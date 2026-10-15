# Module 0: Environment & Mental Model

**Status:** 🟡 In progress (4/5)
**Deliverable:** Docker stack + PostGIS/OpenSearch parity check
**Plan:** [docs/roadmap.md](../docs/roadmap.md)

## Goal
To set the env and understanding the introduction for next journey. 

## What I built
Right now - the environment where everything gonna run and build. 
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

## Trade-offs considered
Worth keeping? Copy to [stories.md](../stories.md).

## What I'd do next
