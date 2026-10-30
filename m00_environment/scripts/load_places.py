"""Load the flattened Overture places into PostGIS and OpenSearch.

PostGIS: geography(Point, 4326) column + GIST index.
OpenSearch: geo_point mapping, loaded with helpers.bulk.
Both read the same parquet file, so any later difference comes from the distance math.

Run from anywhere:
    uv run python m00_environment/scripts/load_places.py                    # both stores
    uv run python m00_environment/scripts/load_places.py --only opensearch  # just one
"""

import argparse
import os
import time
from pathlib import Path

import pandas as pd
import psycopg
from opensearchpy import OpenSearch, helpers

ROOT = Path(__file__).resolve().parents[2]  # repo root
FLAT = ROOT / "data" / "processed" / "places_flat.parquet"
COLUMNS = ["id", "name", "category", "is_restaurant", "confidence", "lon", "lat"]
INDEX = "places"


def load_env(path: Path) -> None:
    """Read KEY=VALUE lines from .env into os.environ (no python-dotenv needed)."""
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def expected_counts(df: pd.DataFrame) -> tuple[int, int, int]:
    """(total, restaurants, no category) straight from the parquet file."""
    return len(df), int(df.is_restaurant.sum()), int(df.category.isna().sum())


def check(store: str, got: tuple[int, int, int], expected: tuple[int, int, int]) -> bool:
    print(f"{store}: {got[0]} | {got[1]} | {got[2]} (total | restaurants | no category)")
    if got == expected:
        print(f"Verification PASSED: {store} matches the parquet file.")
        return True
    print(f"Verification FAILED: expected {expected}, got {got}.")
    return False


# --------------------------------------------------------------------------- PostGIS


def load_postgis(df: pd.DataFrame) -> bool:
    print("\n=== PostGIS ===")
    db_name = os.environ["POSTGRES_DB"]
    db_user = os.environ["POSTGRES_USER"]
    print(f"Connecting to database '{db_name}' as '{db_user}'...")
    t0 = time.perf_counter()

    # One transaction: if anything fails, nothing is left half-loaded
    with psycopg.connect(
        dbname=db_name,
        user=db_user,
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    ) as conn, conn.cursor() as cur:
        print("Creating table 'places'...")
        cur.execute("""
            DROP TABLE IF EXISTS places;
            CREATE TABLE places (
              id text PRIMARY KEY, name text, category text,
              is_restaurant boolean, confidence double precision,
              lon double precision, lat double precision
            );
        """)

        print("Bulk-loading rows with COPY...")
        # pandas marks missing values as NaN, which COPY would store as the
        # text 'nan', so turn them into None (NULL).
        with cur.copy(f"COPY places ({', '.join(COLUMNS)}) FROM STDIN") as copy:
            for row in df.itertuples(index=False):
                copy.write_row([None if pd.isna(v) else v for v in row])

        print("Building geography column and GIST index...")
        # Geography column (lon first!), then the index, then planner stats
        cur.execute("""
            ALTER TABLE places ADD COLUMN geog geography(Point, 4326);
            UPDATE places SET geog = ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography;
            CREATE INDEX places_geog_gix ON places USING GIST (geog);
            ANALYZE places;
        """)

        cur.execute("""
            SELECT count(*),
                   count(*) FILTER (WHERE is_restaurant),
                   count(*) FILTER (WHERE category IS NULL)
            FROM places;
        """)
        got = cur.fetchone()

    print(f"Loaded in {time.perf_counter() - t0:.1f} s")
    return check("PostGIS", tuple(got), expected_counts(df))


# ------------------------------------------------------------------------ OpenSearch

MAPPING = {
    # One node in the sandbox, so replicas would never be assigned (status yellow)
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "dynamic": "strict",  # a typo in a field name fails loudly instead of adding a field
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "text"},
            "category": {"type": "keyword"},
            "is_restaurant": {"type": "boolean"},
            "confidence": {"type": "double"},
            "location": {"type": "geo_point"},
        },
    },
}


def to_actions(df: pd.DataFrame):
    """One bulk action per place. Casts numpy types to plain Python for the JSON body."""
    for r in df.itertuples(index=False):
        yield {
            "_index": INDEX,
            "_id": r.id,  # same id as PostGIS, so the parity check can compare id sets
            "_source": {
                "id": r.id,
                "name": None if pd.isna(r.name) else r.name,
                "category": None if pd.isna(r.category) else r.category,
                "is_restaurant": bool(r.is_restaurant),
                "confidence": float(r.confidence),
                # Object form avoids the [lon, lat] vs "lat,lon" order trap
                "location": {"lat": float(r.lat), "lon": float(r.lon)},
            },
        }


def load_opensearch(df: pd.DataFrame) -> bool:
    print("\n=== OpenSearch ===")
    host = os.getenv("OPENSEARCH_HOST", "localhost")
    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    client = OpenSearch(hosts=[{"host": host, "port": port}], timeout=60)
    print(f"Connected to OpenSearch {client.info()['version']['number']} at {host}:{port}")
    t0 = time.perf_counter()

    print(f"Recreating index '{INDEX}' with geo_point mapping...")
    client.indices.delete(index=INDEX, ignore_unavailable=True)
    client.indices.create(index=INDEX, body=MAPPING)

    print("Bulk-loading documents...")
    ok, errors = helpers.bulk(client, to_actions(df), chunk_size=5000, raise_on_error=False)
    if errors:
        print(f"{len(errors)} documents failed, first one: {errors[0]}")

    # Without a refresh, freshly indexed documents are not visible to search yet
    client.indices.refresh(index=INDEX)
    print(f"Indexed {ok} documents in {time.perf_counter() - t0:.1f} s")

    def count(query: dict | None = None) -> int:
        body = {"query": query} if query else None
        return client.count(index=INDEX, body=body)["count"]

    got = (
        count(),
        count({"term": {"is_restaurant": True}}),
        count({"bool": {"must_not": {"exists": {"field": "category"}}}}),
    )
    return check("OpenSearch", got, expected_counts(df)) and not errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=["postgis", "opensearch"], help="load just one store")
    args = parser.parse_args()

    load_env(ROOT / ".env")  # the same .env that docker compose uses
    print(f"Reading {FLAT.relative_to(ROOT)}...")
    df = pd.read_parquet(FLAT)[COLUMNS]  # fixed column order, same as the COPY list

    passed = True
    if args.only in (None, "postgis"):
        passed &= load_postgis(df)
    if args.only in (None, "opensearch"):
        passed &= load_opensearch(df)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
