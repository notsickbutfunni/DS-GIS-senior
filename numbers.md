# Numbers

Every metric produced in this repo. One row per measurement; never overwrite old rows, add new ones.
Get the hash with `git rev-parse --short HEAD` and commit before measuring.

| Date | Module | Metric | Value | Setup / notes | Git hash |
|---|---|---|---|---|---|
| 2026-10-14 | 0 | Detour index (road ÷ straight), Botanical Garden pair, Almaty | 2.05 | 2520 m drive vs 1230 m haversine; OSMnx drive graph, 3 km around (43.22, 76.90), 1650 nodes; day3.ipynb | 3121df3 (notebook uncommitted) |
| 2026-10-14 | 0 | Web Mercator (EPSG:3857) distance error at 43.2°N, Almaty | +37.16% | Mega Alma-Ata to Dostyk Plaza, vs pyproj Geod; UTM 43N −0.01%, haversine −0.16%; day2.ipynb | 3121df3 |
| 2026-10-15 | 0 | Docker sandbox idle RAM, 5 services | 2.86 GiB (37% of 7.7 GiB Docker VM) | OpenSearch 2.40 GiB with 2g heap, Dashboards 279 MiB, PostGIS 103 MiB, MinIO 69 MiB, Redis 15 MiB; docker stats --no-stream at idle | 36d25ba |
