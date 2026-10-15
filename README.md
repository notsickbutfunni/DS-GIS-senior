# Geospatial Data Scientist Roadmap
### 34-week path from GIS/DS generalist → Geospatial Data Scientist (GeoAI / computer vision)

Goal: go from raw pixels (satellite scenes, traffic-camera video) to maps, measurements and forecasts that a city or a mapping company would act on, and build evidence for the decisions this work requires: evaluating a model so the number survives a new city, turning a camera's pixels into metres on a map and proving the speeds are right, and keeping a pipeline healthy when a camera moves or the season changes.

Two flagship projects:
- **Urban-growth layer from satellite imagery** (Module 4): building footprints, roads and change polygons on a time-slider map.
- **Camera-to-map traffic system** (Modules 5–6, joined in the capstone): detect → track → georeference → speeds → segment state → forecast.

**Time budget:** 10–12.5 hrs/week: Mon–Thu 2 h, Sat 4–5 h build, Fri buffer, Sun 30-min review. Modules 0–1 can compress if you know GIS, Module 3 if you know rasters. **Modules 4–8 are the core (both flagships). Don't compress them.**

Full plan: [docs/roadmap.md](docs/roadmap.md) · Results: [numbers.md](numbers.md) · Interview stories: [stories.md](stories.md)

---

## Progress

| # | Module | Weeks | Status | Deliverable |
|---|---|---|---|---|
| 0 | [Environment & Mental Model](m00_environment/) | 1 | 🟡 In progress (4/5) | Docker stack + PostGIS/OpenSearch parity check |
| 1 | [Spatial Indexing & Core Stack](m01_spatial_indexing/) | 2–4 | ⬜ Not started | Demand heatmap + nearest-driver benchmark |
| 2 | [Spatial Statistics & Spatial ML](m02_spatial_stats/) | 4–6 | ⬜ Not started | Spatial-modelling report: random vs blocked CV |
| 3 | [Raster Data & Remote Sensing](m03_remote_sensing/) | 7–8 | ⬜ Not started | Sentinel-2 pipeline: composites → indices per H3 cell |
| 4 | [Deep Learning for Satellite Imagery ⭐](m04_imagery_dl/) | 9–12 | ⬜ Not started | Urban-growth layer: footprints + roads + change |
| 5 | [Video CV: Detect, Track, Count ⭐](m05_video_cv/) | 13–15 | ⬜ Not started | Counting service by class, lane and direction |
| 6 | [Pixels to Map: Camera Geometry & Speed ⭐](m06_camera_geometry/) | 16–17 | ⬜ Not started | Georeferenced tracks + speeds validated on BrnoCompSpeed |
| 7 | [Trajectories & Traffic Flow](m07_trajectories/) | 18–20 | ⬜ Not started | Trajectory toolkit + study-area dashboard |
| 8 | [Spatio-Temporal Analytics & Forecasting](m08_forecasting/) | 21–23 | ⬜ Not started | Traffic-state API with 30-min forecasts |
| 9 | [Capstone: Camera-to-Map Traffic System](m09_capstone/) | 24–29 | ⬜ Not started | Deployed demo + design doc |
| 10 | [Interview Readiness](m10_interviews/) | 30–34 | ⬜ Not started | Recorded derivations, capstone walkthrough, mocks |

⬜ Not started · 🟡 In progress · ✅ Done · ⭐ Flagship modules

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

Never commit API keys, datasets or raw video. Check each camera feed's terms of use before recording it.

## Quickstart

```bash
make setup   # uv sync: create .venv and install dependencies
make up      # start PostGIS, OpenSearch, Redis, MinIO
make data    # download the Overture places extract into data/
make lab     # open Jupyter
```

Copy `.env.example` to `.env` before `make up`. On Windows, use Git Bash with `make` installed (e.g. `winget install GnuWin32.Make`), or run the commands in the [Makefile](Makefile) directly.
