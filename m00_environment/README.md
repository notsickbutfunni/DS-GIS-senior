# Module 0: Environment & Mental Model

**Status:** ✅ Done (5/5), finished 2026-10-30
**Deliverable:** Docker stack + PostGIS/OpenSearch parity check
**Plan:** [docs/roadmap.md](../docs/roadmap.md)

## Goal
To set the env and understanding the introduction for next journey. 

## What I built
The environment where everything gonna run and build.

| Day | What | Where |
|---|---|---|
| 1 | Repo layout, uv environment, the three-worlds map | [three_worlds.md](three_worlds.md) |
| 2 | One distance four ways: haversine, Geod, EPSG:3857, UTM | [notebooks/day2.ipynb](notebooks/day2.ipynb) |
| 3 | Road route vs straight line, detour index 2.05 | [notebooks/day3.ipynb](notebooks/day3.ipynb), [detour_map.html](detour_map.html) |
| 4 | Docker sandbox: 5 healthy containers | [docker-compose.yml](../docker-compose.yml), [Makefile](../Makefile) |
| 5 | Overture places → PostGIS + OpenSearch, 2 km parity check | [notebooks/day5.ipynb](notebooks/day5.ipynb), [scripts/load_places.py](scripts/load_places.py), [scripts/parity_check.py](scripts/parity_check.py) |

## Results

I have chose the Almaty and Cairo.
Numbers go here and in [numbers.md](../numbers.md).

| Metric | Value | Notes |
|---|---|---|
|Almaty|76.74, 43.03, 77.16, 43.40|the bbox of my home city|
|Cairo|31.10,29.95,31.45,30.15|the bbox of multilingual market City|

### Docker sandbox (day 4)

All 5 containers `healthy` after `docker compose up -d`. Memory from `docker stats --no-stream` at idle; the Docker VM limit is 7.7 GiB (half of 16 GB RAM).

| Service | Image | Port | Health check | Check result | RAM (idle) | % of limit |
|---|---|---|---|---|---|---|
| PostGIS | `postgis/postgis:16-3.4` | 5432 | `pg_isready` | PostGIS 3.4.3 | 102.5 MiB | 1.3% |
| OpenSearch | `opensearchproject/opensearch:2` | 9200 | `curl _cluster/health` | green, 1 node | 2.40 GiB | 31.2% |
| OpenSearch Dashboards | `opensearchproject/opensearch-dashboards:2` | 5601 | `curl /api/status` | UI up | 278.9 MiB | 3.5% |
| Redis | `redis:7` | 6379 | `redis-cli ping` | PONG | 14.9 MiB | 0.2% |
| MinIO | `cgr.dev/chainguard/minio` | 9000 / 9001 | `mc ready local` | console up on :9001 | 68.8 MiB | 0.9% |
| **Total** | | | | | **2.86 GiB** | **37.1%** |

OpenSearch takes 84% of the stack's memory, almost all of it the 2 GB JVM heap (`-Xms2g -Xmx2g`). Watch it when the 500K-POI index arrives in Module 2.

### PostGIS ↔ OpenSearch parity check (day 5)

**Result: PASS (explained).** 17 of 10,533 restaurant–centre pairs disagree, every one within 4.6 m of the 2 km boundary. With `ST_DWithin(..., use_spheroid => false)` PostGIS returns exactly the same sets as OpenSearch (0 mismatches).

**Data.** Overture places for the Almaty bbox (`make data`), flattened in day5.ipynb to `data/processed/places_flat.parquet`: 24,312 points, 1,663 restaurants (`'restaurant'` anywhere in `taxonomy.hierarchy`). [load_places.py](scripts/load_places.py) loads the same file into PostGIS (`geography(Point, 4326)` + GIST index) and OpenSearch (`geo_point`, `helpers.bulk`), so any difference comes from the distance math.

**Setup.** 50 random restaurants as centres (seed 42), radius 2,000 m, restaurants only. Restaurants per circle: median 165 (min 2, max 550). The PostGIS plan uses the GIST index.

| Query | Median time | Notes |
|---|---|---|
| PostGIS `ST_DWithin` spheroid (default) | 4.14 ms | client wall clock |
| PostGIS `ST_DWithin` sphere | 3.04 ms | ~25% faster than spheroid |
| OpenSearch `geo_distance` 2000m | 56.33 ms | server `took` 9 ms; the rest is HTTP + JSON through Docker on Windows |

| Comparison | Mismatches |
|---|---|
| PostGIS spheroid vs OpenSearch (strict) | 17 (6 only in PostGIS, 11 only in OpenSearch) |
| PostGIS sphere vs OpenSearch | **0** |

**Why they disagree.** PostGIS `geography` measures on the WGS84 spheroid by default; OpenSearch uses arc distance on a sphere of mean radius 6,371,008.8 m. At 43.2°N the spheroid is flatter north–south (meridian radius 6,365 km) and rounder east–west (prime-vertical radius 6,388 km) than that sphere, so a 2 km distance comes out about **−1.8 m north–south** and **+5.4 m east–west** on the spheroid. The mismatches follow exactly this pattern:

- **Only in PostGIS (6):** bearings near 0° or 180° (north/south). The spheroid says 1,999.1–1,999.8 m (inside); the sphere says 2,000.6–2,001.4 m (outside).
- **Only in OpenSearch (11):** bearings mostly 65–95° or 250–280° (east/west), plus one diagonal at 143° with the smallest gap (+0.8 m). The spheroid says 2,000.6–2,004.6 m (outside); the sphere says under 2,000 m (inside).

Full list: `data/processed/parity_mismatches.csv` (gitignored). Rerun with `uv run python m00_environment/scripts/parity_check.py`; it exits 0 only if the plan uses the index and every mismatch is explained.

## Trade-offs considered
Worth keeping? Copy to [stories.md](../stories.md).

- **Which Earth model counts as the truth for a radius filter.** A few metres at the 2 km edge never matter to a user, but they do break a test that expects two stores to agree. Options: accept the spheroid default and tolerate boundary flips; switch PostGIS to the sphere so both stores agree exactly; or compare with a small tolerance band. I kept the spheroid as the reference (it is the more accurate one) and made the test prove the cause instead: same sets on the sphere, and every flip within 10 m of the boundary. Written up in [stories.md](../stories.md).
- **OpenSearch latency.** 9 ms on the server vs 56 ms at the client: most of the cost is the round trip, not the geo filter. Module 1's latency benchmark should report both.

## What I'd do next
- Module 1 builds on this sandbox: H3/S2/geohash, the nearest-driver benchmark and `city_cells`.
- Load Cairo the same way and rerun the parity check. At 30°N the spheroid offsets differ, so the mismatch pattern should shift. (`make data` writes to `data/raw/places.parquet`, so give Cairo its own output file first.)
