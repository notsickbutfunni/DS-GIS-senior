# Geo Search Senior Data Scientist Roadmap
### 6–12 month path from GIS/DS generalist → Senior DS, Geo Search

Goal: build evidence for the decisions this role requires: turning noisy ride sessions into unbiased ranking labels, keeping query understanding under a 50ms keystroke budget, and deciding per query whether to trust your own index or fall back to an external provider.

**Time budget:** 10–15 hrs/week. Modules 0–2 can compress if you know GIS. **Modules 5–8 are the core. Don't compress them.**

Full plan: [docs/roadmap.md](docs/roadmap.md) · Results: [numbers.md](numbers.md) · Interview stories: [stories.md](stories.md)

---

## Progress

| # | Module | Weeks | Status | Deliverable |
|---|---|---|---|---|
| 0 | [Environment & Mental Model](m00_environment/) | 1 | 🟡 Pre-starting | Docker stack + PostGIS/OpenSearch parity check |
| 1 | [Spatial Indexing](m01_spatial_indexing/) | 2–4 | ⬜ Not started | Nearest-driver strategy benchmark |
| 2 | [OpenSearch for Geo](m02_opensearch/) | 4–6 | ⬜ Not started | Cross-script autocomplete engine |
| 3 | [Query Understanding](m03_query_understanding/) | 6–9 | ⬜ Not started | Query understanding microservice |
| 4 | [LLM Distillation](m04_distillation/) | 9–11 | ⬜ Not started | Intent classifier at 10ms p99 |
| 5 | [Unbiased Ranking Labels ⭐](m05_labels/) | 11–15 | ⬜ Not started | IPS-corrected label pipeline |
| 6 | [Learning to Rank](m06_ltr/) | 15–19 | ⬜ Not started | Two-stage geo LTR service |
| 7 | [Offline Replay & Error Analysis](m07_replay/) | 19–22 | ⬜ Not started | Replay harness + segmented report |
| 8 | [Experimentation & Fallback](m08_experiments/) | 22–25 | ⬜ Not started | Switchback simulator + confidence model |
| 9 | [Capstone](m09_capstone/) | 25–30+ | ⬜ Not started | Deployed demo + design doc |
| 10 | [Interview Readiness](m10_interviews/) | 30–34 | ⬜ Not started | Recorded walkthrough + mock interviews |

⬜ Not started · 🟡 In progress · ✅ Done

---

## Repo Layout

```
README.md          overview + progress (portfolio front page)
docs/roadmap.md    full module plan
numbers.md         every metric produced, with date and git hash
stories.md         trade-off stories for interviews
src/geosearch/     shared code: distance, H3 helpers, metrics, simulator
mXX_*/             one folder per module: README.md (report), notebooks/, scripts/
data/, models/     gitignored; filled by `make data`
```

## Quickstart

```bash
make setup   # uv sync: create .venv and install dependencies
make up      # start PostGIS, OpenSearch, Redis, MinIO
make data    # download the Overture places extract into data/
make lab     # open Jupyter
```

Copy `.env.example` to `.env` before `make up`. On Windows, use Git Bash with `make` installed (e.g. `winget install GnuWin32.Make`), or run the commands in the [Makefile](Makefile) directly.
