# Roadmap

Module summaries first, full detail below. The day-by-day schedule, with every reading and checkbox, lives in the interactive plan; this file is the reference version that travels with the code.
 
**Direction:** become a geospatial data scientist who can go from raw pixels (satellite scenes, traffic-camera video) to maps, measurements and forecasts that a city or a mapping company would act on. Two flagship projects: (1) an urban-growth layer from satellite imagery, (2) a camera-to-map traffic system (detect → track → georeference → speeds → segment state → forecast).
 
**Timeline:** 34 weeks, 28 Sep 2026 → 22 May 2027, ~10–12.5 h/week (Mon–Thu 2 h, Sat 4–5 h build, Fri buffer, Sun 30-min review).
 
**Hardware:** Colab/Kaggle for anything that needs >8 GB VRAM (foundation-model fine-tunes, DCRNN); a local RTX 4060 (8 GB) for everything else — 512 px tiles, batch 8, mixed precision.

## Modules
 
**0. Environment & Mental Model (wk 1):** CRS (4326 vs 3857 vs projected); Haversine vs road distance; vector vs raster vs video as three ways of seeing the same city. Docker Compose (PostGIS/Timescale, Redis, MinIO).
→ Load Overture places for your city into PostGIS and DuckDB; assert parity on a 2 km radius query.
 
**1. Spatial Indexing & Core Stack (wk 2–4):** Geohash vs S2 vs H3; R-trees vs grids; BallTree vs ANN. `h3`, PostGIS `ST_DWithin`/KNN, `sjoin_nearest`, OSMnx.
→ NYC 2015 taxi demand on H3 res-8; benchmark BallTree vs H3 ring search vs OSMnx ETA for nearest driver.
 
**2. Spatial Statistics & Spatial ML (wk 4–6):** Moran's I / LISA, point patterns (KDE, Ripley's K), spatial lag/error regression (`spreg`), GWR (`mgwr`), kriging, regionalisation, **spatial cross-validation**.
→ Spatial-modelling report on one city; headline figure = random-vs-blocked CV gap.
 
**3. Raster Data & Remote Sensing (wk 7–8):** Sentinel-2 L2A, SCL cloud masking, composites, spectral indices, COGs, STAC, zonal stats, Earth Engine.
→ STAC → cloud-free monthly composites → NDVI/NDBI/NDWI per H3 cell; 512 px training chips for Module 4.
 
**4. Deep Learning for Satellite & Aerial Imagery ⭐ (wk 9–12):** U-Net segmentation (buildings, roads), cross-city generalisation, MOSAIKS, Prithvi-EO fine-tune, Siamese change detection, tiled inference.
→ **Flagship 1:** vectorised urban-growth layer (footprints + roads + change) with an interactive time-slider map.
 
**5. Video CV: Detect, Track, Count ⭐ (wk 13–15):** YOLO11 fine-tuning, Kalman + ByteTrack/BoT-SORT, HOTA/MOTA, line/zone counting, night/rain robustness, TensorRT.
→ Counting service: per-minute counts by class, lane and direction from traffic-camera video.
 
**6. From Pixels to the Map: Camera Geometry & Speed (wk 16–17):** Pinhole model, homography, ground control points from a basemap, reprojection error, speed from smoothed ground-plane tracks, drift detection.
→ Georeferenced vehicle tracks (WGS84) and speeds validated on BrnoCompSpeed.
 
**7. Trajectories & Traffic Flow (wk 18–20):** MovingPandas, HMM map matching (FMM), fundamental diagram, Edie metrics, turning movements, OD matrices, MFD, SUMO as ground truth, movement-data privacy.
→ `src/geosearch/traj` toolkit + study-area dashboard (segment speeds, TMC, OD, queues).
 
**8. Spatio-Temporal Analytics & Forecasting (wk 21–23):** Rolling-origin backtests, seasonal naive → LightGBM → DCRNN/Graph WaveNet on METR-LA, incident detection, prediction intervals, TimescaleDB, Evidently drift.
→ Segment-state table + forecasting benchmark + traffic-state API with 30-min forecasts.
 
**9. Capstone: Camera-to-Map Traffic System + Urban Layers (wk 24–29):** One system with a design doc, MLflow champion/challenger gates, drift monitoring, MapLibre front end, public demo.
```
RTSP/clip → Video worker (TensorRT detector + ByteTrack + zones + homography)
  → per-minute camera records → segment_state (TimescaleDB) → forecast (5-min job) → incidents
  → API → MapLibre map (live speeds, forecast slider, incidents, camera frames, satellite layers)
  ⇣ batch monthly: STAC → composites → indices → segmentation → change → GeoParquet
  ⇣ async: logs → evaluation → MLflow registry → CI gates → redeploy
```
 
**10. Interview Readiness (wk 30–34):** Five recorded derivations (spatial CV, camera→speed, tracking metrics, fundamental diagram, ST forecasting); timed system-design mocks; <15-min capstone walkthrough.
 
---
 
## Key Datasets
 
| Dataset | Use |
|---|---|
| NYC Open Data 2015 Yellow Taxi (with coordinates), Overture Maps, OSM | Demand surfaces, POI index, road graphs |
| Sentinel-2 L2A via Planetary Computer STAC | Composites, indices, change detection |
| SpaceNet (buildings, roads), LoveDA, xBD / LEVIR-CD | Segmentation and change-detection training |
| UA-DETRAC, AI City Challenge, VisDrone | Detection, tracking, counting |
| BrnoCompSpeed | Speed-estimation ground truth (LiDAR/GPS) |
| pNEUMA, NGSIM, highD, GeoLife | Trajectories, fundamental diagrams, map matching |
| METR-LA, PEMS-BAY | Traffic forecasting benchmarks |
 
---
 
# Full Detail
 
This roadmap is built around one assumption: a GeoAI / transport-analytics interview panel doesn't want someone who "knows GeoPandas and trained a YOLO once." They want someone who has already made the decisions this work requires — how to evaluate a model so the number survives a new city, how to turn a camera's pixels into metres on a map and prove the speeds are right, how to keep a pipeline healthy when a camera moves or a season changes. Every module below is built to produce evidence of exactly that.
 
**Time budget assumption:** 10–12.5 hrs/week. Modules 0–1 are foundational and can compress if you already know GIS. Modules 4–8 are where the job lives — do not rush them.
 
**Repo layout:** `m00_environment/ … m10_interviews/` one folder per module (each with its own README = the module write-up), `src/geosearch/` for reusable code, `docs/roadmap.md` (this file), `numbers.md` (every headline number and where it comes from), `stories.md` (interview stories). `data/` and `.env` are git-ignored; never commit API keys, datasets or raw video, and check each camera feed's terms of use before recording it.
 
---
 
## Module 0 — Environment & Mental Model (Week 1)
 
**Theoretical Foundation**
- Three representations of one city: **vector** (points, lines, polygons: POIs, roads, footprints), **raster** (grids of pixels: satellite bands, elevation, density surfaces) and **video** (rasters over time, in a camera's coordinate frame, not the Earth's). Almost every module is about converting between these three.
- Coordinate reference systems: WGS84 (EPSG:4326, lat/lon, what GPS gives you) vs. Web Mercator (EPSG:3857, what you render) vs. local projected CRS / UTM (for true distance/area math). Never compute distance in raw lat/lon degrees. Pixel coordinates in an image are a fourth frame you will later map onto the first three.
- Great-circle distance (Haversine) vs. projected Euclidean distance vs. **road-network distance/ETA**, and why ranking on straight-line distance fails in cities with rivers, highways and one-way systems.
**Concrete Tech Stack**
- Python env: `uv`/`conda`, `geopandas`, `shapely>=2.0`, `pyproj`, `h3`, `osmnx`, `folium`/`lonboard`, `duckdb` + spatial extension (fast local geo SQL, no server needed).
- Docker Compose stack you'll reuse for the whole roadmap: `postgres` with `postgis` + `timescaledb`, `redis`, `minio` (S3-compatible, for imagery extracts and video clips). GPU: CUDA toolkit + PyTorch on the 4060 once it arrives; Colab until then.
**Hands-on Production Project**
- Stand up the local stack via `docker-compose.yml`. Load an Overture Maps `places` extract for one city into PostGIS **and** DuckDB. Write a script that queries both for "restaurants within 2 km of point X" and asserts result parity. This becomes your dev sandbox for every later module.
---
 
## Module 1 — Spatial Indexing & the Geospatial Core Stack (Weeks 2–4)
 
**Theoretical Foundation**
- Why lat/lon pairs are a bad index key: no locality, expensive range queries, no cheap "nearby" on a B-tree.
- Space-filling curves & hierarchical grids: **Geohash** (base-32, quadtree, boundary problem), **S2** (Google, spherical, Hilbert-curve cells), **Uber H3** (hexagonal, uniform adjacency, 16 resolutions, designed for supply/demand aggregation). H3 cells become the unit of analysis for Modules 2, 3, 7 and 8, so get the resolution intuition right now (res 7 ≈ 5 km², res 8 ≈ 0.7 km², res 9 ≈ 0.1 km²).
- R-trees / R*-trees (what PostGIS `GIST` and Shapely's `STRtree` use) vs. grid indexes: R-trees for irregular polygons, grids for uniform-density aggregation (heatmaps, zonal statistics).
- KD-trees and Ball-trees for exact nearest neighbour (`sklearn.neighbors.BallTree` with haversine metric) vs. approximate NN (HNSW/FAISS) for embedding lookups later.
**Concrete Tech Stack & Libraries**
- **H3**: `latlng_to_cell`, `cell_to_latlng`, `grid_disk`, `grid_ring`, `cell_to_boundary`, `compact_cells`/`uncompact_cells`, `cell_to_parent`/`cell_to_children`, `grid_distance`.
- **PostGIS**: `ST_DWithin`, `ST_Intersects`, `ST_Contains`, `ST_Buffer`, `ST_Distance` (spheroid vs. planar), `ST_ClusterDBSCAN`, `GIST` index, KNN `<->` operator.
- **GeoPandas/Shapely**: `sjoin`/`sjoin_nearest`, `STRtree`, `unary_union`, `.buffer()`, `.simplify()`.
- **PySAL**: `esda.Moran`, `libpysal.weights` (KNN/Queen/Rook) — the entry point to Module 2.
- **OSMnx**: `graph_from_place`, `nearest_nodes`, `shortest_path` — your free road-network engine, reused for map matching in Module 7.
**Hands-on Production Project**
"Demand-Supply Heatmap & Nearest-Driver Engine" — Ingest NYC 2015 Yellow Taxi trips (the NYC Open Data release that still carries pickup/dropoff coordinates; post-2016 TLC Parquet files only have zone IDs), bucket pickups into H3 res-8 cells, build a rolling 15-min demand surface. Build a driver-simulation layer and implement three "nearest driver" strategies: (a) Haversine + BallTree, (b) H3 `grid_disk` expanding-ring search, (c) OSMnx shortest-path ETA. Benchmark latency and accuracy at increasing driver density. The resulting `city_cells` table (demand, POI counts, road density, distance to centre per H3 cell) is the input to Module 2.
 
**Open Datasets:** NYC Open Data 2015 Yellow Taxi (`2yzn-sicd`), Overture Maps `places` + `divisions` + `buildings`, OpenStreetMap extracts (Geofabrik).
 
---
 
## Module 2 — Spatial Statistics & Spatial Machine Learning (Weeks 4–6)
 
**Theoretical Foundation**
- **Spatial dependence vs. spatial heterogeneity**: global autocorrelation (Moran's I, Geary's C) vs. local indicators (LISA, Getis-Ord G*); hot spots with significance, not just a coloured map.
- **Point pattern analysis**: intensity, KDE and bandwidth choice, Ripley's G/K functions against CSR, DBSCAN on points.
- **Spatial regression**: why OLS residuals are autocorrelated on spatial data; spatial lag vs. spatial error models; Lagrange-multiplier specification tests; **geographically weighted regression** (GWR/MGWR) as the "coefficients vary over space" alternative and how to read local-coefficient maps.
- **Geostatistics**: variograms, ordinary kriging vs. IDW, when each is right.
- **Spatial cross-validation**: random K-fold leaks information through spatial autocorrelation and over-states accuracy; blocked, buffered and leave-region-out folds (Roberts et al. 2017); area of applicability. This is the single most interview-relevant idea in the module and it recurs in Modules 4, 5 and 8.
- Support, scale and the **MAUP** — why results change when you change the cell size.
**Concrete Tech Stack**
- `esda` (Moran, Moran_Local, G_Local), `libpysal.weights`, `pointpats`, `spreg` (`OLS`, `ML_Lag`, `ML_Error`, LM tests), `mgwr` (`Sel_BW`, `GWR`, `MGWR`), `PyKrige` / `scikit-gstat`, `spopt` (regionalisation: SKATER, max-p), `spacv` / `scikit-learn` custom splitters for blocked CV, `LightGBM` for the tabular model.
**Hands-on Production Project**
"Spatial Modelling Report for One City" — On Module 1's `city_cells`: point patterns and hot spots of demand; OLS → lag → error → GWR on demand vs. urban-form features with local-coefficient maps; kriging of a sampled variable vs. IDW on held-out points; then a **spatial-CV benchmark**: LightGBM with random vs. blocked vs. leave-district-out folds, with and without spatial lag features. Deliverable: `m02_spatial_stats/README.md` with one figure per section; the random-vs-blocked CV gap is the headline figure. Record a 6-minute explanation of spatial CV and GWR.
 
**Open Datasets:** Your own `city_cells` table (Module 1), Overture Places/Buildings, any open-data sensor or census layer for your city.
 
---
 
## Module 3 — Raster Data & Remote Sensing (Weeks 7–8)
 
**Theoretical Foundation**
- Remote-sensing fundamentals: sensors, spatial/spectral/temporal resolution, radiance vs. reflectance, Level-1C vs. **Level-2A** surface reflectance; Sentinel-2 bands and the **Scene Classification Layer (SCL)**.
- Cloud masking and compositing: SCL-based masks, median vs. best-pixel monthly composites, the cloud-shadow silent error.
- Spectral indices: NDVI, NDBI, NDWI and what each says about an urban surface; per-pixel trends over years as a cheap change signal.
- Cloud-native geo: **COG** internals (tiling, overviews, HTTP range reads), **STAC** catalogues, lazy evaluation with Dask-backed xarray.
- Sensors beyond optical: Sentinel-1 SAR basics, nighttime lights, DEMs; what each adds to urban analysis.
- Zonal statistics as the bridge from raster back to your H3 vector world.
**Concrete Tech Stack**
- `rasterio` (windows, reprojection, writing COGs), `rioxarray`, `xarray` + `dask`, `pystac-client` + `stackstac` / `odc-stac` against the **Microsoft Planetary Computer** STAC API (free, no account for Sentinel-2), `spyndex` for indices, `exactextract` / `rasterstats` for zonal stats, `geemap` + Earth Engine for the same workflow at continental scale.
**Hands-on Production Project**
"Analysis-Ready Sentinel-2 Pipeline for Your City" — STAC search → one year of Sentinel-2 L2A as a lazy stack → SCL cloud masking → monthly composites → NDVI/NDBI/NDWI → `exactextract` zonal stats per H3 cell joined to `city_cells`; a 2–3-year NDVI/NDBI trend notebook answering "where did the city grow?"; the same composite reproduced in Earth Engine to compare effort and limits. Final Saturday: cut 512×512 training chips (Sentinel-2 + a high-resolution source) with building masks from Overture, spatially split train/val/test — the inputs to Module 4.
 
**Open Datasets:** Sentinel-2 L2A (Planetary Computer / Copernicus Data Space), Sentinel-1 GRD, VIIRS nighttime lights, Copernicus DEM, Overture `buildings`.
 
---

## Module 4 — Deep Learning for Satellite & Aerial Imagery (Weeks 9–12) ⭐ Flagship 1
 
**Theoretical Foundation**
- CNN and **semantic segmentation** refresher: U-Net, encoder–decoder, loss functions for imbalanced masks (BCE + Dice, focal), IoU/F1 and boundary F1.
- What is different about geospatial DL: tiling and samplers, CRS-aware datasets, multispectral inputs and per-band normalisation, label noise from OSM/Overture, and the fact that **spatial autocorrelation makes random train/test splits dishonest** (Module 2 again).
- Thin structures: road segmentation, class imbalance, from mask to road graph (skeletonisation) and the APLS metric idea.
- **Cross-city generalisation** as the real test; why a model trained on one city drops on another and how to diagnose it.
- **Foundation models for Earth observation** (Prithvi-EO-2.0, TorchGeo pretrained Sentinel-2 backbones) and the critique of their evaluation; **MOSAIKS** (random convolutional features + ridge) as the cheap strong baseline you must beat.
- **Change detection**: Siamese architectures, bi-temporal datasets (LEVIR-CD, xBD), change F1.
- Inference at scale: tiling with overlap and blending, stitching, throughput on an 8 GB card.
**Concrete Tech Stack**
- `torch`, `torchgeo` (datasets, samplers, pretrained weights), `segmentation_models.pytorch` (U-Net with ResNet-34 encoder as the baseline), `lightning`, `albumentations`, `rasterio` for tiled inference, `shapely`/`geopandas` for vectorisation and polygon simplification, **Open-CD** for change-detection configs, `samgeo` (SAM) for labelling assistance, `mlflow` for experiment tracking, GeoParquet for outputs.
- Training recipe for the 4060: 512 px tiles, batch 8, bf16/fp16 mixed precision, gradient accumulation; Prithvi fine-tune on Colab.
**Hands-on Production Project**
"Urban-Growth Layer for Your City" — (1) Baseline U-Net for buildings on SpaceNet, improved (loss, encoder, TTA), post-processed to polygons and compared with Overture/Microsoft footprints. (2) SpaceNet 3 roads → mask → road graph. (3) Evaluate the buildings model on a city it never saw; diagnose the drop. (4) MOSAIKS baseline for building density per cell. (5) Prithvi-EO-2.0 fine-tune for built-up segmentation vs. the U-Net on identical splits. (6) Siamese change detection trained on LEVIR-CD/xBD, applied to bi-temporal Sentinel-2 composites from Module 3 and validated against the NDBI trend. (7) Evaluation that survives review: spatially blocked test metrics with CIs, per-density strata, boundary F1, calibration. Deliverable: one GeoParquet layer (footprints + roads + change polygons), an interactive map with a time slider, dataset and model cards, `make reproduce` rebuilding the metrics table, and a recorded 10-minute walkthrough.
 
**Open Datasets:** SpaceNet 1/2 (buildings), SpaceNet 3 (roads), LoveDA, LEVIR-CD, xBD / xView2, Microsoft Building Footprints, Overture `buildings`, your Module 3 chips.
 
---
 
## Module 5 — Video Computer Vision: Detect, Track, Count (Weeks 13–15) ⭐ Flagship 2, part 1
 
**Theoretical Foundation**
- Object detection refresher: anchor-based vs. anchor-free, NMS, IoU, mAP@0.5 and mAP@0.5:0.95; the YOLO family and what changed in YOLO11.
- **Fine-tune, don't train from scratch**: 300–500 labelled frames from your target cameras beat 100K generic frames; active learning (mine low-confidence frames, label, retrain, measure gain per frame).
- **Multi-object tracking**: Kalman filter prediction/update, Hungarian association, SORT → ByteTrack (associate low-score boxes too) → BoT-SORT (camera-motion compensation + appearance). Metrics: **HOTA** vs. MOTA vs. IDF1, and why ID switches are invisible in a demo and fatal for counts.
- Counting with lines and zones: per-direction and per-lane logic, double counting, occlusion.
- Robustness: night, rain, glare, low FPS; measuring count accuracy under each.
- Image formation (prep for Module 6): why pixel distance isn't metres.
- Deployment: ONNX/TensorRT export, FP16/INT8, FPS at 1 vs. 4 streams on an 8 GB card.
**Concrete Tech Stack**
- `ultralytics` (YOLO11 train/val/predict/track/export/benchmark), `supervision` (`LineZone`, `PolygonZone`, annotators), `boxmot` or Ultralytics built-in ByteTrack/BoT-SORT, **TrackEval** for HOTA, **CVAT** for labelling, `opencv-python`, `ffmpeg`, TensorRT via Ultralytics export, Parquet/Postgres sink.
**Hands-on Production Project**
"Traffic Counting Service v1" — Collect clips from 2–3 public traffic cameras (check terms of use) plus UA-DETRAC; label 150 frames in CVAT; fine-tune YOLO11s and review night/rain failures; run ByteTrack and BoT-SORT on a labelled UA-DETRAC sequence and score with TrackEval, tuning thresholds on HOTA; per-lane, per-direction counts against manual counts; robustness table (night/rain, 5/10/25 FPS); TensorRT FP16/INT8 benchmarks; drone footage (VisDrone) with tiling for tiny objects; one active-learning round. Deliverable: a service that takes a stream/clip + camera config and emits per-minute counts by class, lane and direction to Parquet/Postgres; a 60-second annotated demo video; `m05_video_cv/README.md`.
 
**Open Datasets:** UA-DETRAC, AI City Challenge (request access in week 13 — approval takes weeks), VisDrone, your own camera clips.
 
---
 
## Module 6 — From Pixels to the Map: Camera Geometry & Speed (Weeks 16–17) ⭐ Flagship 2, part 2
 
**Theoretical Foundation**
- **Camera models**: pinhole, intrinsics, extrinsics, lens distortion; what you can and cannot recover from a single fixed camera.
- **Homography**: plane-to-plane mapping between the image and the road plane; why it works for traffic (vehicles live on a plane) and where it fails (hills, overpasses, tall vehicles' bounding boxes).
- **Ground control points**: 4–6 well-spread GCPs matched between a video frame and a basemap/satellite image (lane markings, crossings); solving the homography; reprojection error as the quality metric.
- Projection chain: bottom-centre of a track → ground plane → UTM → WGS84; smoothing; **speed from smoothed ground-plane positions over ≥1 s windows** (frame-to-frame speeds are noise).
- Validation against ground truth (BrnoCompSpeed: LiDAR/GPS) before trusting any speed from your own cameras.
- **Camera drift**: detecting when the homography stops being valid (camera moved, zoom, wind) and automating the check.
- Drone video (pNEUMA, highD) as the georeferenced-by-construction counterpart.
**Concrete Tech Stack**
- `opencv-python` (`findHomography`, `perspectiveTransform`, calibration), `pyproj` (UTM ↔ WGS84), `numpy`/`scipy` smoothing (Savitzky–Golay / Kalman), `geopandas` → GeoParquet trajectories, a per-camera YAML calibration file, `lonboard`/MapLibre to publish the layer.
**Hands-on Production Project**
"Georeferenced Traffic Layer v1" — Per-camera calibration files with reprojection errors; Module 5 tracks projected to WGS84 and written as GeoParquet trajectories; speed estimation implemented and validated on **BrnoCompSpeed** (tuned window and smoothing, error table against truth); the same applied to your own cameras with sanity checks against speed limits and free-flow conditions; an automated homography-drift check. Deliverable: per-camera, per-minute records (counts + speeds + positions) with coordinates, published as a map layer; `m06_camera_geometry/README.md` with calibration method, errors, validation, limits.
 
**Open Datasets:** BrnoCompSpeed, pNEUMA (EPFL), highD, your own cameras.
 
---
 
## Module 7 — Trajectories & Traffic Flow (Weeks 18–20)
 
**Theoretical Foundation**
- **Trajectories as objects**: TrajectoryCollection, speed/direction, stop detection, splitting, generalisation.
- **Map matching**: HMM map matching (Newson & Krumm) — emission vs. transition probabilities, failure modes; this is where CV meets GIS: your camera tracks only become road-segment observations after map matching.
- **Traffic flow theory**: flow, density, speed; q = k·v; Greenshields and the **fundamental diagram**; Edie's generalised definitions; shockwaves (LWR intuition); the **macroscopic fundamental diagram** (Geroliminis & Daganzo) at city scale.
- Intersection analytics: turning-movement counts from tracks vs. zone-based counts.
- **OD matrices** from trajectories at H3 zones; the identifiability problem; flow maps.
- Simulation as ground truth: SUMO from OSM, exporting trajectories and detector counts to test your estimators.
- Anomalies from trajectories: stops, queues, wrong-way, near-misses (time-to-collision).
- **Privacy and ethics of movement data**: re-identification risk, aggregation thresholds, k-anonymity for OD; write a data policy.
**Concrete Tech Stack**
- `movingpandas`, `scikit-mobility`, **FMM** (Fast Map Matching) on an OSMnx graph, `osmnx`, `sumo` + `traci`, `geopandas`, `h3`, `streamlit` + `lonboard` for the dashboard.
**Hands-on Production Project**
"Trajectory Toolkit + Study-Area Dashboard" — Map-match pNEUMA and GeoLife trajectories with FMM; compute fundamental diagrams from NGSIM US-101 and pNEUMA and compare with camera-derived counts; turning-movement counts at one intersection; OD matrices at H3 zones; reproduce the MFD idea on pNEUMA; SUMO network + simulated day to validate every estimator; anomaly detection with precision on hand-checked cases. Package it as `src/geosearch/traj` (loading, cleaning, map matching, Edie metrics, TMC, OD) with tests on SUMO data. Deliverable: a Streamlit/lonboard dashboard of segment speeds, turning movements, OD flows and queue lengths for one day; `m07_trajectories/README.md` including the privacy policy.
 
**Open Datasets:** pNEUMA, NGSIM (US-101, I-80), GeoLife, highD, SUMO outputs, your Module 6 tracks.
 
---
 
## Module 8 — City-Scale Spatio-Temporal Analytics & Forecasting (Weeks 21–23)
 
**Theoretical Foundation**
- Forecasting fundamentals: decomposition, **baselines (historical average, seasonal naive)** that are hard to beat at 15-minute horizons, rolling-origin backtests, per-horizon evaluation (15/30/60 min).
- Real sensor data: loop detectors, missingness, the sensor graph, daily profiles (METR-LA, PEMS-BAY, PeMS).
- Gradient-boosted forecasting with lag, calendar and neighbour features across all sensors.
- **Spatio-temporal graph neural networks**: message passing, GCN/GAT, over-smoothing; DCRNN's diffusion convolution; Graph WaveNet; reproducing published numbers within tolerance.
- Incident/anomaly detection from speed drops vs. expected profile; false-alarm rate on simulated incidents.
- **Uncertainty**: quantile GBM, conformal prediction, coverage checks.
- Monitoring: input drift (counts, speeds) and error drift; alerts.
- Network-level traffic science: MFD applications (perimeter control), how cities report congestion (TomTom/INRIX-style indices).
**Concrete Tech Stack**
- `statsforecast`/`sktime` for baselines, `lightgbm`, `torch` + **PyTorch Geometric Temporal** / LibCity / DCRNN-PyTorch, `timescaledb` (hypertables, continuous aggregates) + PostGIS, `evidently`, `mlflow`, `fastapi`.
**Hands-on Production Project**
"City Traffic-State Service" — `segment_state` table (camera counts/speeds + trajectories aggregated to road segments and H3 cells per 5 min, in TimescaleDB); forecasting benchmark seasonal naive → LightGBM → DCRNN/Graph WaveNet on METR-LA, then the same pipeline on your own segments with per-segment-class errors; incident detector evaluated on SUMO-injected incidents; prediction intervals with coverage; Evidently drift reports. Deliverable: API + map with current segment speeds, 30-minute forecast and active incidents, refreshed from the database; `make m08-benchmark` rebuilds every table; `m08_forecasting/README.md`; capstone design-doc skeleton.
 
**Open Datasets:** METR-LA, PEMS-BAY, Caltrans PeMS, your `segment_state` table, SUMO.
 
---
 
## Module 9 — Capstone: Camera-to-Map Traffic System + Urban Layers (Weeks 24–29)
 
**Goal:** stitch Modules 2–8 into one coherent, demo-able, documented system — the thing that goes on your portfolio and that you walk an interviewer through live. Scope: 3 cameras, one study area, one city for the satellite layers. A working thin slice beats an ambitious broken system.
 
**Architecture to build and diagram (know every arrow and its budget):**
```
[RTSP stream / replayed clip]
   → Streaming ingest (ffmpeg → frame queue, back-pressure)
   → Video worker (TensorRT FP16 detector + ByteTrack + zones + homography)   (Modules 5/6)
   → per-camera, per-minute records → TimescaleDB
   → segment_state continuous aggregates → forecast job every 5 min → incident detector   (Modules 7/8)
   → FastAPI → MapLibre map (live speeds, forecast slider, incidents, camera frames)
        ⇣ batch, monthly
   STAC → composites → indices → segmentation → change → GeoParquet urban layers   (Modules 3/4)
        ⇣ async
   Logs → evaluation → MLflow champion/challenger → CI gates → redeploy; drift + camera-health monitoring
```
- **Design doc** (problem, requirements incl. latency/throughput budgets per stage, data, models, evaluation, monitoring, risks, alternatives considered and rejected) — v1, external review by 1–2 CV/GIS/transport people, v2.
- **MLOps**: MLflow registry for detector, forecaster and segmenter; CI evaluation gates before promotion; Evidently drift; camera-drift, dark/frozen-camera and data-freshness alerts; Locust load tests and chaos tests (kill a worker, stall the DB, move a camera).
- **Public demo** on a Hugging Face Docker Space or small VM, running recorded clips replayed as streams with a CPU fallback detector — say so in the README. Optional: DeepStream comparison, Kubernetes manifest on `kind`.
- **Reproducibility**: fresh clone + `make reproduce` regenerates every headline number; `numbers.md` is the single source of truth.
- Portfolio: top-level README (2-minute summary, demo link, diagram, 6 headline numbers), three "considered and rejected" trade-off case studies with numbers, a new-city onboarding playbook, résumé bullets, 15-minute recorded walkthrough, tag `v1.0`.
**Open Datasets for the capstone:** everything above — your cameras + UA-DETRAC (video), BrnoCompSpeed (validation), Sentinel-2 + SpaceNet models (satellite layers), METR-LA (forecasting sanity baseline), SUMO (incident ground truth).
 
---
 
## Module 10 — Interview & System-Design Readiness (Weeks 30–34)
 
**Theoretical Foundation / Practice**
- Five derivations, from memory, recorded: (1) spatial cross-validation and leakage, (2) camera geometry → homography → ground-plane tracks → speed with error sources, (3) HOTA vs. MOTA vs. IDF1 and the ByteTrack association, (4) q = k·v, the fundamental diagram, shockwaves and the MFD, (5) spatio-temporal forecasting from baselines to DCRNN with per-horizon evaluation.
- Timed 40-minute **system-design mocks**: "design a city-wide traffic monitoring system from cameras", "produce building footprints and growth maps for a country with little training data", "an evaluation and monitoring plan for a detector/segmenter rolled out to new cities". One structure every time: clarify → requirements & budgets → data → baseline → model → evaluation (spatially honest) → deployment → monitoring. Always name the alternative you rejected, with a number.
- Coding refreshes under time: spatial join, H3 aggregation, haversine, zonal stats, homography with OpenCV, trajectory speed; IoU/NMS, a PyTorch training loop, a Kalman update, a rolling backtest, blocked CV.
- Statistics and ML-breadth refresh, GeoAI vocabulary, company deep dives (mapping, mobility, smart-city, EO analytics).
**Hands-on Production Project**
Capstone walkthrough under 15 minutes; four solo + two peer mocks with written feedback; a story bank of six STAR stories with numbers; a flashcard pass over every module's self-check questions; portfolio final pass (README, demo, design doc, LinkedIn consistent, every link works); applications to 5 roles and outreach to 3 people with the demo; a final honest pass through the readiness checklist.
 
---
 
## Consolidated Open Dataset Reference
 
| Dataset | Use For |
|---|---|
| NYC Open Data 2015 Yellow Taxi (`2yzn-sicd`) | Demand surfaces, nearest-driver benchmarks (has coordinates; post-2016 TLC files don't) |
| Overture Maps (`places`, `buildings`, `divisions`, `transportation`) | POI index, building masks, road network |
| OpenStreetMap extracts (Geofabrik) | Road graphs (OSMnx), map matching, SUMO networks |
| Sentinel-2 L2A (Planetary Computer STAC / Copernicus Data Space) | Composites, indices, change detection, training chips |
| Sentinel-1 GRD, VIIRS nighttime lights, Copernicus DEM | Sensors beyond optical |
| SpaceNet 1/2/3 | Building and road segmentation |
| LoveDA | Cross-city generalisation test |
| LEVIR-CD, xBD / xView2 | Change-detection training |
| Microsoft Building Footprints | Footprint comparison baseline |
| UA-DETRAC | Vehicle detection and tracking with labels (HOTA evaluation) |
| AI City Challenge | Multi-camera tracking, counting, speed (request access early) |
| VisDrone | Drone-view detection, tiny objects |
| BrnoCompSpeed | Speed-estimation ground truth (LiDAR/GPS) |
| pNEUMA (EPFL), highD | Drone-derived trajectories, fundamental diagrams, MFD |
| NGSIM US-101 / I-80 | Vehicle trajectories, fundamental diagrams |
| GeoLife | Map-matching practice |
| METR-LA, PEMS-BAY, Caltrans PeMS | Traffic forecasting benchmarks |
| SUMO (simulated) | Ground truth for estimators and incident detection |
 
---
 
## Candidate Readiness Checklist — Geospatial Data Scientist (GeoAI / CV)
 
**Spatial fundamentals**
- [ ] Can explain H3 vs. S2 vs. Geohash trade-offs and justify a resolution choice for a specific use case
- [ ] Can write `ST_DWithin`/`ST_Intersects`/KNN PostGIS queries from memory and knows when to reach for DuckDB instead
- [ ] Understands why road-network distance ≠ Haversine, and when each is acceptable
**Spatial statistics & evaluation**
- [ ] Can explain spatial dependence vs. heterogeneity and read a LISA map and a GWR coefficient map
- [ ] Can derive on a whiteboard why random K-fold leaks on spatial data and design blocked/buffered/leave-region-out folds
- [ ] Has a measured random-vs-blocked CV gap on real data, with numbers
- [ ] Defaults to per-city, per-density-stratum, per-horizon evaluation, never one aggregate number
**Remote sensing & imagery DL**
- [ ] Has built a STAC → cloud-masked composite → indices → zonal-stats pipeline and can explain SCL masking and COGs
- [ ] Has trained, evaluated (on a city never seen in training) and vectorised a building/road segmentation model
- [ ] Can compare a U-Net, MOSAIKS and a fine-tuned EO foundation model on identical splits and say which to ship and why
- [ ] Has run change detection on real bi-temporal imagery and validated it against an independent signal
**Video CV & geometry**
- [ ] Has fine-tuned a detector on target-camera frames and can quote per-class AP, night/rain degradation and FPS on a given GPU
- [ ] Evaluates trackers with HOTA on labelled clips and can explain why ID switches break counts
- [ ] Can derive pinhole → homography → ground plane → speed, name the error sources and quote a validated speed error on BrnoCompSpeed
- [ ] Has an automated camera-drift check
**Trajectories, flow & forecasting**
- [ ] Can explain HMM map matching and has matched real trajectories to an OSM graph
- [ ] Can derive q = k·v, draw the fundamental diagram and explain the MFD; has computed them from real trajectories
- [ ] Has a forecasting benchmark where seasonal naive, LightGBM and an ST-GNN are compared per horizon, with prediction intervals and coverage
- [ ] Has a written movement-data privacy policy
**System & production judgment**
- [ ] Can whiteboard the full camera-to-map architecture end-to-end, including the batch satellite path and the monitoring/retraining loop, with budgets per stage
- [ ] Has a deployed, load-tested demo (not just notebooks) with real throughput numbers
- [ ] Every headline number reproduces from a clean checkout
- [ ] Has 3 stories of a trade-off explicitly considered and rejected, with numbers
---
 
### How to use this document
Work top to bottom. Modules 0–1 can compress if you already know GIS. Modules 4–8 are the depth that separates a GeoAI data scientist from a generalist — do not compress them. If you are on the 12-month track, flex weeks go after Module 9 (multi-camera tracking, SegFormer, a second city), not before it. Keep `numbers.md` current as you go; Module 10 is built on it.
