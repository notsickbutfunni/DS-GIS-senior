"""PostGIS vs OpenSearch parity check: restaurants within 2 km of a point.

For each centre (random restaurants, fixed seed) it runs three queries:
  pg_spheroid  ST_DWithin(geog, centre, 2000)         PostGIS default: WGS84 spheroid
  pg_sphere    ST_DWithin(geog, centre, 2000, false)  PostGIS on a sphere
  opensearch   geo_distance 2000m                     arc distance on a sphere
and compares the sets of ids. Strict parity is pg_spheroid == opensearch.
A mismatch counts as explained when pg_sphere == opensearch for it and it lies
within a few metres of the 2 km boundary: then the only difference is the Earth model.

Needs both stores loaded first: uv run python m00_environment/scripts/load_places.py
Run: uv run python m00_environment/scripts/parity_check.py [--centres 50] [--radius 2000]
"""

import argparse
import os
import statistics
import time

import pandas as pd
import psycopg
from load_places import FLAT, INDEX, ROOT, load_env
from opensearchpy import OpenSearch

OUT = ROOT / "data" / "processed" / "parity_mismatches.csv"
BAND_M = 10  # a mismatch further than this from the radius is not an Earth-model effect

PG_WITHIN = """
    SELECT id FROM places
    WHERE is_restaurant
      AND ST_DWithin(geog, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography,
                     %(radius)s, %(spheroid)s)
"""

PG_DETAILS = """
    WITH c AS (SELECT ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography AS g)
    SELECT p.id, p.name, p.category,
           ST_Distance(p.geog, c.g, true)        AS dist_spheroid_m,
           ST_Distance(p.geog, c.g, false)       AS dist_sphere_m,
           degrees(ST_Azimuth(c.g, p.geog))      AS bearing_deg
    FROM places p, c
    WHERE p.id = ANY(%(ids)s)
"""


def os_within(client: OpenSearch, lat: float, lon: float, radius: float) -> tuple[set[str], int]:
    body = {
        "size": 10000,  # max result window; a 2 km circle holds far fewer restaurants
        "_source": False,  # only ids are needed
        "track_total_hits": True,
        "query": {
            "bool": {
                "filter": [  # filter context: no scoring, cacheable
                    {"term": {"is_restaurant": True}},
                    {"geo_distance": {"distance": f"{radius}m", "location": {"lat": lat, "lon": lon}}},
                ]
            }
        },
    }
    res = client.search(index=INDEX, body=body)
    assert res["hits"]["total"]["value"] < 10000, "result window too small"
    return {h["_id"] for h in res["hits"]["hits"]}, res["took"]


def pg_within(cur, lat: float, lon: float, radius: float, spheroid: bool) -> set[str]:
    cur.execute(PG_WITHIN, {"lat": lat, "lon": lon, "radius": radius, "spheroid": spheroid})
    return {r[0] for r in cur.fetchall()}


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, (time.perf_counter() - t0) * 1000


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--centres", type=int, default=50)
    ap.add_argument("--radius", type=float, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    load_env(ROOT / ".env")
    flat = pd.read_parquet(FLAT)
    centres = flat[flat.is_restaurant].sample(args.centres, random_state=args.seed)

    client = OpenSearch(hosts=[{"host": os.getenv("OPENSEARCH_HOST", "localhost"), "port": 9200}], timeout=60)
    conn = psycopg.connect(
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        autocommit=True,
    )
    cur = conn.cursor()

    # The GIST index must be used, otherwise the PostGIS timing is a full table scan
    first = centres.iloc[0]
    cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + PG_WITHIN,
                {"lat": first.lat, "lon": first.lon, "radius": args.radius, "spheroid": True})
    plan = "\n".join(r[0] for r in cur.fetchall())
    uses_index = "places_geog_gix" in plan
    print(f"PostGIS plan uses GIST index: {uses_index}")

    # Warm-up so the first timing does not include cold caches and connection setup
    pg_within(cur, first.lat, first.lon, args.radius, True)
    os_within(client, first.lat, first.lon, args.radius)

    t_pg, t_pg_sphere, t_os, t_os_took, hits = [], [], [], [], []
    rows, sphere_mism = [], 0
    for c in centres.itertuples():
        pg, ms = timed(pg_within, cur, c.lat, c.lon, args.radius, True)
        t_pg.append(ms)
        pg_s, ms = timed(pg_within, cur, c.lat, c.lon, args.radius, False)
        t_pg_sphere.append(ms)
        (os_ids, took), ms = timed(os_within, client, c.lat, c.lon, args.radius)
        t_os.append(ms)
        t_os_took.append(took)
        hits.append(len(pg))
        sphere_mism += len(pg_s ^ os_ids)  # the key proof: same Earth model, same answer

        only_pg, only_os = pg - os_ids, os_ids - pg
        if not (only_pg or only_os):
            continue
        cur.execute(PG_DETAILS, {"lat": c.lat, "lon": c.lon, "ids": list(only_pg | only_os)})
        for pid, name, cat, d_sph, d_sphere, bearing in cur.fetchall():
            in_os = pid in os_ids
            rows.append({
                "centre_id": c.id, "centre_lat": c.lat, "centre_lon": c.lon,
                "id": pid, "name": name, "category": cat,
                "only_in": "opensearch" if in_os else "postgis",
                "dist_spheroid_m": round(d_sph, 3),
                "dist_sphere_m": round(d_sphere, 3),
                "spheroid_minus_sphere_m": round(d_sph - d_sphere, 3),
                "bearing_deg": round(bearing, 1),
                # explained: on the sphere PostGIS agrees with OpenSearch, and it sits at the boundary
                "explained": (pid in pg_s) == in_os and abs(d_sph - args.radius) <= BAND_M,
            })

    mism = pd.DataFrame(rows)
    sphere_parity = sphere_mism == 0
    conn.close()

    med = statistics.median
    print(f"\nCentres: {args.centres} random restaurants (seed {args.seed}), radius {args.radius:.0f} m")
    print(f"Restaurants per circle: median {med(hits):.0f}, min {min(hits)}, max {max(hits)}, "
          f"total pairs checked {sum(hits)}")
    print("\nQuery timings, median over centres (client wall clock):")
    print(f"  PostGIS ST_DWithin spheroid  {med(t_pg):6.2f} ms")
    print(f"  PostGIS ST_DWithin sphere    {med(t_pg_sphere):6.2f} ms")
    print(f"  OpenSearch geo_distance      {med(t_os):6.2f} ms  (server 'took' {med(t_os_took):.0f} ms)")

    print(f"\nStrict parity (spheroid vs OpenSearch): {len(mism)} mismatches")
    if len(mism):
        OUT.parent.mkdir(parents=True, exist_ok=True)
        mism.to_csv(OUT, index=False)
        cols = ["only_in", "dist_spheroid_m", "dist_sphere_m", "spheroid_minus_sphere_m", "bearing_deg", "explained"]
        print(mism.sort_values("dist_spheroid_m")[["name", *cols]].to_string(index=False))
        print(f"Saved to {OUT.relative_to(ROOT)}")
        print(f"  only in PostGIS:    {(mism.only_in == 'postgis').sum()}")
        print(f"  only in OpenSearch: {(mism.only_in == 'opensearch').sum()}")
        print(f"  furthest from {args.radius:.0f} m: {(mism.dist_spheroid_m - args.radius).abs().max():.2f} m")
    print(f"Sphere parity (ST_DWithin use_spheroid=false vs OpenSearch): {sphere_mism} mismatches")

    strict = mism.empty
    explained = strict or (sphere_parity and bool(mism.explained.all()))
    print()
    if strict:
        print("PASS: strict parity, the two stores return identical sets.")
    elif explained:
        print("PASS (explained): every mismatch is a boundary point that flips because PostGIS uses the "
              "WGS84 spheroid and OpenSearch a sphere. With use_spheroid=false the sets are identical.")
    else:
        print("FAIL: some mismatches are not explained by the Earth model. Check the rows with explained=False.")
    raise SystemExit(0 if explained and uses_index else 1)


if __name__ == "__main__":
    main()
