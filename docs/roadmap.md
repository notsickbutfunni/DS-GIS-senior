# Roadmap

Module summaries first, full detail below. The day-by-day schedule, with every reading and checkbox, lives in the interactive plan; this file is the reference version that travels with the code.
 
**Direction:** GIS analytics and travel-demand modelling as the foundation; machine learning and deep learning applied to traffic (forecasting, calibration, causal evaluation, counts from video); one platform capstone; interview preparation aimed at big-tech loops.
 
**Timeline:** 57 weeks, 28 Sep 2026 → 27 Oct 2027, three sessions a week (Tue/Wed/Thu; Theory/Lab 2 h, Build 4–5 h), ≈415 h in total. Modules 0–2 are unchanged from the earlier plan.
 
**Hardware:** Colab/Kaggle for anything that needs >8 GB VRAM (foundation-model fine-tunes, DCRNN); a local RTX 4060 (8 GB) for everything else — 512 px tiles, batch 8, mixed precision.

**Two parallel habits from Module 3:** two algorithm problems a week (NeetCode), and one real department task per module done through the Visum–Python bridge.

## Modules
 
**0. Environment & Mental Model (wk 1):** CRS (4326 vs 3857 vs projected); Haversine vs road distance; vector vs raster vs video as three ways of seeing the same city. Docker Compose (PostGIS/Timescale, Redis, MinIO).
→ Load Overture places for your city into PostGIS and DuckDB; assert parity on a 2 km radius query.
 
**1. Spatial Indexing & Core Stack (wk 2–6, 08 Oct 2026 → 04 Nov 2026):** Geohash vs S2 vs H3; R-trees vs grids; BallTree vs ANN; PostGIS `ST_DWithin`/KNN; `sjoin_nearest`; OSMnx.  
→ NYC 2015 taxi demand on H3 res-8; nearest-driver benchmark (BallTree vs H3 rings vs road ETA); the `city_cells` table.
 
**2. Spatial Statistics & Spatial ML (wk 6–10, 05 Nov 2026 → 03 Dec 2026):** Moran's I / LISA, point patterns, spatial lag/error regression, GWR, kriging, regionalisation, **spatial cross-validation**.  
→ Spatial-modelling report on one city; headline figure = random-vs-blocked CV gap.

**3. Transport Data Foundations & GIS Analytics ⭐ (wk 11–15, 08 Dec 2026 → 06 Jan 2027):** Counts and factoring (AADT), FCD and HMM map matching, GTFS and accessibility (r5py), travel survey expansion, mobile-data OD, a **Visum ↔ Python bridge** under tests.  
→ A transport data warehouse for one study area + department dashboard v0.

**4. Travel Demand Modelling × ML ⭐ (wk 15–21, 07 Jan 2027 → 17 Feb 2027):** Four-step structure; random utility, MNL and nested logit (Biogeme); logit vs GBM vs neural with **elasticities**; gravity models and assignment (AequilibraE/Visum); **OD estimation with synthetic truth**; ActivitySim; validation discipline; scenario sensitivity (SALib).  
→ Mode-choice comparison table, OD-estimation error-vs-information figure, a reproducible change shipped to the production Visum model.

**5. Trajectories & Traffic Flow (wk 21–26, 18 Feb 2027 → 24 Mar 2027):** MovingPandas, FMM map matching, fundamental diagram and Edie metrics, turning movements, OD from trajectories, MFD, SUMO as ground truth, movement-data privacy.  
→ `src/mobilitylab/traj` toolkit + study-area dashboard.

**6. Spatio-Temporal Forecasting ⭐ (wk 26–31, 25 Mar 2027 → 28 Apr 2027):** Rolling-origin backtests; seasonal naive → LightGBM → DCRNN on METR-LA and on your own segments; incident detection; prediction intervals; TimescaleDB; Evidently drift.  
→ Segment-state table, forecasting benchmark per horizon, traffic-state API.

**7. Simulation × ML ⭐ (wk 31–36, 29 Apr 2027 → 02 Jun 2027):** SUMO twin calibrated with Optuna; Sobol sensitivity; surrogate for scenario screening; **DiD / synthetic control / CausalImpact** on real interventions; switchback experiments under interference; RL signal control vs max-pressure.  
→ Calibrated twin, surrogate, two causal evaluations, intervention-evaluation playbook, scenario studio v1.

**8. Video CV for Traffic Counts (wk 36–39, 03 Jun 2027 → 24 Jun 2027):** YOLO11 + ByteTrack + supervision zones; HOTA evaluation; homography to the ground plane; turning-movement counts; camera health; optional fine-tuning.  
→ Counting service feeding the warehouse and the model's calibration targets.

**9. Capstone: City Traffic Analytics Platform (wk 40–49, 29 Jun 2027 → 31 Aug 2027):** Ingest → warehouse → link state → forecasts & incidents → calibrated twin → scenario studio → map/API; MLflow gates; drift and sensor-health monitoring; chaos tests; public demo on a synthetic twin; Visum integration; design doc v2.  
→ Deployed demo, design doc, three trade-off case studies, new-city playbook, recorded walkthrough, v1.0.

**10. Interview Readiness (big-tech DS/ML) (wk 49–57, 01 Sep 2027 → 27 Oct 2027):** Five recorded derivations (spatial/temporal CV, discrete choice & OD, map matching & flow, ST forecasting, experimentation & causal); design mocks (ETA, marketplace demand, cross-city rollout); timed algorithm and SQL sets; stats and ML breadth; story bank.  
→ Four solo + two peer mocks, cheat-sheets, applications sent.

```
Counts · FCD · GTFS · survey · mobile OD · cameras
  → warehouse (DuckDB/PostGIS + Timescale, pandera contracts, H3 + zone ids)
  → link state (map-matched speeds, counts, incidents) → forecasts per horizon
  → Visum model ⇄ Python bridge ⇄ SUMO twin (calibrated) → surrogate → scenario studio
  → causal evaluation of interventions (DiD / synthetic control)
  → API + MapLibre map + GeoPackage exports for planners
  ⇣ async: MLflow registry → CI gates → drift & sensor-health monitoring → retrain
```

---
 
## Key Datasets

| Dataset | Use |
|---|---|
| Your department's counts, FCD, mobile OD, GTFS/AVL, survey, Visum model | Everything from Module 3 on (with a synthetic twin of each table in the public repo) |
| NYC Open Data 2015 Yellow Taxi, Overture Maps, OSM | Modules 0–2 |
| Swissmetro (Biogeme examples) | Discrete-choice practice before your own survey |
| pNEUMA, NGSIM, highD, GeoLife | Trajectories, fundamental diagrams, map matching |
| METR-LA, PEMS-BAY, Caltrans PeMS | Forecasting benchmarks |
| SUMO (OSM Web Wizard + your OD) | Calibration, surrogates, RL, synthetic truth for OD estimation and causal methods |
| UA-DETRAC, VisDrone, your cameras | Video counts |

---

# Full Detail

## Module 0 — Environment & Mental Model (Weeks 1–2, 29 Sep 2026 → 07 Oct 2026)

**Why this module**  
Every later module runs on this sandbox. CRS and distance mistakes silently corrupt ranking features for months.

**You finish with:** docker-compose sandbox, a distance notebook, and a PostGIS ↔ OpenSearch parity test.

**Sessions**
1. *Lab* — **Kick-off: repo, environment, the three worlds.** Set up your DS-GIS-senior repo (folders, uv environment, .gitignore); write a one-page map of the job into index / query / ranking worlds.
2. *Theory* — **CRS and distance, done right.** Watch why maps distort; read Geocompx ch. 6 and the pyproj gotchas; compute one distance several ways and quantify the Web Mercator error at your latitude.
3. *Lab* — **Road network vs straight line.** Read DeepETA; with OSMnx build a drive graph and find a pair of points whose route is 1.5–3× the straight line.
4. *Lab* — **Docker sandbox up.** docker-compose.yml with PostGIS, OpenSearch (+ Dashboards), Redis and MinIO; verify every service.
5. *Build* — **Build: PostGIS ↔ OpenSearch parity check.** Load Overture places for your city into PostGIS and OpenSearch; assert that 'restaurants within 2 km of X' returns the same set from both.

**Read:** [Geocomputation with Python, ch. 1: Geographic data in Python](https://py.geocompx.org/01-spatial-data) · [Geocomputation with Python, ch. 6: Reprojecting geographic data](https://py.geocompx.org/06-reproj) · [Movable Type: distance, bearing & more between lat/lon points](https://www.movable-type.co.uk/scripts/latlong.html) · [Uber: DeepETA, how Uber predicts arrival times](https://www.uber.com/us/en/blog/deepeta-how-uber-predicts-arrival-times/) · [Overture: Places guide](https://docs.overturemaps.org/guides/places/) · [Overture workshop: Exploring & accessing data](https://labs.overturemaps.org/workshop/2-accessing-data.html) · [PostGIS workshop: Spatial indexing](https://postgis.net/workshops/postgis-intro/indexing.html) · [DuckDB: Introducing the spatial extension](https://duckdb.org/2023/04/28/spatial)

**Watch:** [Vox: Why all world maps are wrong](https://www.youtube.com/watch?v=kIID5FDi2JQ)

**Look at:** [uv (Python package & project manager)](https://docs.astral.sh/uv/) · [pyproj Gotchas/FAQ (axis order, always_xy)](https://pyproj4.github.io/pyproj/stable/gotchas.html) · [OSMnx: Getting started](https://osmnx.readthedocs.io/en/stable/getting-started.html) · [OSMnx: User reference](https://osmnx.readthedocs.io/en/stable/user-reference.html) · [OpenSearch: Installing with Docker](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/docker/) · [OpenSearch: Disabling the Security plugin](https://docs.opensearch.org/latest/security/configuration/disable-enable-security/) · [Overture: Python client (overturemaps CLI)](https://docs.overturemaps.org/getting-data/overturemaps-py/) · [Overture Explorer (map viewer)](https://explore.overturemaps.org/) · [OpenSearch: Geodistance query](https://docs.opensearch.org/latest/query-dsl/geo-and-xy/geodistance/) · [DuckDB: Spatial functions](https://duckdb.org/docs/current/core_extensions/spatial/functions)

**Recommendations**
- Your DS-GIS-senior repo is public, which is good for the portfolio, but never commit API keys (.env) or datasets. GitHub rejects files over 100 MB, so keep data in a gitignored data/ folder with download scripts.
- Use the same two cities for all 34 weeks (e.g. Almaty + Cairo). Comparable numbers across modules make a much stronger portfolio than new data each time.
- Keep numbers.md from day one: every latency, NDCG and recall figure with the date and git hash.
- Don't over-engineer infra. Single-node OpenSearch with security off is fine locally; just never expose the port.
- If Docker strains your laptop, run PostGIS + OpenSearch only and use DuckDB spatial for heavy local SQL.

**Self-check before moving on**
- [ ] Why is Euclidean distance in EPSG:3857 wrong for ranking, and by how much at your city's latitude?
- [ ] When is haversine good enough, and when do you need road-network ETA?
- [ ] What does always_xy=True fix, and what bug does it prevent?
- [ ] Why can PostGIS and OpenSearch disagree on a 2 km radius?

---

## Module 1 — Spatial Indexing & the Geospatial Core Stack (Weeks 2–6, 08 Oct 2026 → 04 Nov 2026)

**Why this module**  
Spatial indexing is the foundation of the index world, and the first trade-off question you'll get: spatial index or a real routing call?

**You finish with:** Demand heatmap, nearest-driver benchmark (3 strategies × 4 driver densities) and a trade-off write-up.

**Sessions**
1. *Theory* — **Why lat/lon is a bad key; geohash by hand.** Read the proximity-search deep dive; implement geohash yourself and demonstrate the cell-edge problem.
2. *Theory* — **H3 deep read.** Read Uber's H3 post and the H3 overview; watch the hexagons video; answer 'why hexagons for ride-hailing?' in 60 seconds.
3. *Lab* — **H3 hands-on.** Practise the h3-py v4 API, build a resolution cheat sheet for your city, map a k-ring.
4. *Theory* — **S2 and the Hilbert curve.** Watch 3Blue1Brown on Hilbert curves; read the S2 cell docs; cover one polygon with S2 and with H3 and compare.
5. *Build* — **Build: demand surface from real trips.** Pull one week of 2015 NYC taxi trips with coordinates; bucket pickups into H3 res 8; compute a rolling 15-minute demand surface.
6. *Theory* — **R-trees and database spatial indexes.** Read the PostGIS indexing and KNN chapters, skim Guttman's R-tree paper, EXPLAIN ANALYZE a radius query with and without GIST.
7. *Lab* — **Geography vs geometry; spatial joins.** Compare spheroid and planar distance in PostGIS; benchmark sjoin, sjoin_nearest and STRtree on 1M points.
8. *Lab* — **Ball trees and spatial autocorrelation.** Haversine BallTree for nearest neighbours; Moran's I on your demand surface.
9. *Lab* — **Driver simulator + two index strategies.** Simulate drivers around demand; nearest-driver via (a) haversine BallTree and (b) H3 expanding-ring search.
10. *Build* — **Build: road-network ETA + benchmark.** Add strategy (c), OSMnx travel-time routing; benchmark latency and accuracy of all three at 100 to 50k drivers.
11. *Write-up* — **Write-up: index vs routing call.** Module 1 README: when a spatial index is enough, when to pay for routing, and the hybrid you'd ship.
12. *Review* — **Review: proximity system-design drill.** Self-check questions out loud; whiteboard nearest-drivers at 10k QPS; watch a proximity-service design and note what it misses.

**Read:** [Hello Interview: Proximity search deep dive](https://www.hellointerview.com/learn/system-design/deep-dives/proximity-search) · [Wikipedia: Geohash](https://en.wikipedia.org/wiki/Geohash) · [Uber: H3, Uber's Hexagonal Hierarchical Spatial Index](https://www.uber.com/us/en/blog/h3/) · [H3 docs: Overview of the H3 system](https://h3geo.org/docs/core-library/overview/) · [S2 Geometry: S2 cell hierarchy](https://s2geometry.io/devguide/s2cell_hierarchy.html) · [C. Perone: Google's S2, geometry on the sphere, cells and Hilbert curve](https://blog.christianperone.com/2015/08/googles-s2-geometry-on-the-sphere-cells-and-hilbert-curve/) · [PostGIS workshop: Spatial indexing](https://postgis.net/workshops/postgis-intro/indexing.html) · [PostGIS workshop: Nearest-neighbour searching (<->)](https://postgis.net/workshops/postgis-intro/knn.html) · [PostGIS workshop: Geography type](https://postgis.net/workshops/postgis-intro/geography.html) · [Guttman: R-trees, a dynamic index structure for spatial searching (tech report)](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1983/ERL-m-83-64.pdf) · [scikit-learn: Nearest neighbors user guide](https://scikit-learn.org/stable/modules/neighbors.html) · [GDS book: Global spatial autocorrelation (Moran's I)](https://geographicdata.science/book/notebooks/06_spatial_autocorrelation.html) · [Geographic Data Science with Python (Rey, Arribas-Bel, Wolf)](https://geographicdata.science/book/) · [Boeing: OSMnx paper](https://arxiv.org/abs/1611.01890) · [ByteByteGo: Proximity service](https://bytebytego.com/guides/proximity-service/)


**Watch:** [CGP Grey: Hexagons are the Bestagons](https://www.youtube.com/watch?v=thOifuHs6eY) · [Hexagonify the World: theory & applications of Uber H3](https://www.youtube.com/watch?v=1Ocw_oaw_a8) · [3Blue1Brown: Hilbert's Curve, is infinite math useful?](https://www.youtube.com/watch?v=3s7h2MHQtxc) · [Design a Proximity Service (Yelp): QuadTree / GeoHash](https://www.youtube.com/watch?v=kzRb1KPhrjs)


**Look at:** [h3-py: API quick reference (v4)](https://uber.github.io/h3-py/api_quick.html) · [H3: Cell statistics across resolutions](https://h3geo.org/docs/core-library/restable/) · [H3: Migrating from 3.x (old to new function names)](https://h3geo.org/docs/library/migrating-3.x/) · [s2sphere quickstart (Python S2)](https://s2sphere.readthedocs.io/en/latest/quickstart.html) · [NYC Open Data: 2015 Yellow Taxi Trip Data (has pickup lat/lon)](https://data.cityofnewyork.us/Transportation/2015-Yellow-Taxi-Trip-Data/2yzn-sicd) · [NYC TLC Trip Record Data (Parquet)](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) · [Porto taxi trajectories, ECML/PKDD 2015 (UCI)](https://archive.ics.uci.edu/dataset/339/taxi+service+trajectory+prediction+challenge+ecml+pkdd+2015) · [GeoPandas: Merging data (spatial joins)](https://geopandas.org/en/stable/docs/user_guide/mergingdata.html) · [GeoPandas: sjoin_nearest](https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin_nearest.html) · [scikit-learn: BallTree](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.BallTree.html) · [PySAL esda: Moran](https://pysal.org/esda/generated/esda.Moran.html) · [OSMnx: User reference](https://osmnx.readthedocs.io/en/stable/user-reference.html) · [kepler.gl](https://kepler.gl/) · [DuckDB: Spatial functions](https://duckdb.org/docs/current/core_extensions/spatial/functions)

**Recommendations**
- Data trap: TLC Parquet files since July 2016 carry taxi-zone IDs only. Use NYC Open Data's 2015 trips (coordinates) or the Porto trajectories, so you don't lose a Saturday discovering this.
- Aggregate in DuckDB or Polars; bring only aggregated data into pandas/GeoPandas.
- BallTree with haversine wants radians in [lat, lon] order, the most common nearest-neighbour bug.
- Report p95 (not averages), with warm caches and fixed hardware. Interviewers will ask how you measured.
- S2: learn the concepts and when to use it. Don't sink time into its C++ internals.

**Self-check before moving on**
- [ ] Pick H3, S2 or geohash for (a) a surge heatmap, (b) geofencing a service area, (c) nearest driver. Justify each.
- [ ] Why does an H3 ring search need a final exact re-rank?
- [ ] R-tree vs grid index: which for irregular admin polygons, which for demand aggregation, and why?
- [ ] When do you call a routing engine instead of haversine, and how do you keep that within budget?
- [ ] What does Moran's I tell you, and why should a ranking person care?

---

## Module 2 — Spatial Statistics & Spatial Machine Learning (Weeks 6–10, 05 Nov 2026 → 03 Dec 2026)

**Why this module**  
Spatial data breaks ordinary statistics: nearby things are correlated, so naive models overfit and naive cross-validation lies. This module gives you the toolkit a geospatial data scientist is expected to own.

**You finish with:** A spatial-modelling report on one city: point patterns, hot spots, spatial regression vs GWR, kriging, and an honest spatial-CV comparison.

**Sessions**
1. *Theory* — **Spatial dependence and heterogeneity.** Anselin's week-1 lecture + GDS book LISA chapter: global vs local autocorrelation, dependence vs heterogeneity.
2. *Theory* — **Point pattern analysis.** GDS point-pattern chapter: intensity, KDE bandwidths, Ripley's G/K, DBSCAN on points.
3. *Build* — **Build: an urban dataset for spatial modelling.** Assemble an H3-cell table for your city: demand, POI counts/mix, building density, road density, distance to centre; explore with maps and correlations.
4. *Theory* — **Spatial regression: lag and error models.** GDS regression chapter + spreg model specs; fit OLS, test residuals, then fit lag and error models.
5. *Lab* — **Geographically weighted regression.** mgwr: choose a bandwidth, fit GWR and MGWR, map local coefficients and local R².
6. *Lab* — **Interpolation: IDW vs kriging.** Fit a variogram, krige a surface (e.g. average pickup wait or a sampled sensor variable), compare with IDW using held-out points.
7. *Theory* — **Spatial cross-validation: why random folds lie.** Roberts et al. 2017 + the GeoAI spatial-CV chapter; design blocked and buffered folds for your city.
8. *Build* — **Build: spatial-CV benchmark.** Random forest / LightGBM on city_cells with random vs blocked vs leave-district-out CV; add spatial features and lag features; report the gap.
9. *Lab* — **Spatial feature engineering.** Neighbourhood features (lags, k-ring aggregates, distance decays), spatial encodings, and when they leak.
10. *Lab* — **Clustering regions and uncertainty.** Regionalisation (spatially constrained clustering) of city cells; bootstrap uncertainty on hot spots.
11. *Theory* — **Reading week: what GeoAI practitioners argue about.** Pebesma & Bivand on support and scale (MAUP); Anselin on spatial heterogeneity; write 5 interview-ready explanations.
12. *Write-up* — **Write-up: the spatial modelling report.** m02/README: data, point patterns, regression comparison, GWR maps, kriging, the CV gap, and what you'd do differently.
13. *Build* — **Build: portfolio polish + drill.** Turn the report into a 3-minute read with one figure per section; record a 6-minute explanation of spatial CV and GWR.

**Read:** [GDS book: Point pattern analysis](https://geographicdata.science/book/notebooks/08_point_pattern_analysis.html) · [GDS book: Local spatial autocorrelation (LISA)](https://geographicdata.science/book/notebooks/07_local_autocorrelation.html) · [GDS book: Spatial regression](https://geographicdata.science/book/notebooks/11_regression.html) · [Spatial Data Science book: Point pattern analysis chapter](https://r-spatial.org/book/11-PointPattern.html) · [Pebesma & Bivand: Spatial Data Science (free online)](https://r-spatial.org/book/) · [Oshan et al.: mgwr, multiscale geographically weighted regression](https://www.mdpi.com/2220-9964/8/6/269) · [Roberts et al.: Cross-validation strategies for structured data (Ecography 2017)](https://www.wsl.ch/lud/biodiversity_events/papers/Roberts_et_al-2017-Ecography.pdf) · [Meyer & Pebesma: Predicting into unknown space? Area of applicability](https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.13650) · [Spatial cross-validation for GeoAI (handbook chapter)](https://www.acsu.buffalo.edu/~yhu42/papers/2023_GeoAIHandbook_SpatialCV.pdf) · [Anselin: An Introduction to Spatial Data Science with GeoDa (free)](https://lanselin.github.io/introbook_vol1/) · [Geocomputation with Python, ch. 5: Raster-vector interactions](https://py.geocompx.org/05-raster-vector)

**Watch:** [Luc Anselin: Introduction to Spatial Data Science (lecture playlist)](https://www.youtube.com/playlist?list=PLzREt6r1NenmFyTw8v2JZpEE4PZGNi5Ht)

**Look at:** [Geographic Data Science with Python: table of contents](https://geographicdata.science/book/notebooks/00_toc.html) · [spreg: Spatial model specifications](https://pysal.org/spreg/notebooks/7_spatial_models.html) · [spreg: Specification tests (LM tests)](https://pysal.org/spreg/notebooks/9_specification_tests.html) · [mgwr: GWR and MGWR example notebook](https://pysal.org/notebooks/model/mgwr/GWR_MGWR_example.html) · [PyKrige: ordinary kriging example](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/examples/00_ordinary.html) · [SciKit-GStat: variogram and kriging reference](https://scikit-gstat.readthedocs.io/en/latest/reference/kriging.html) · [spacv: spatial cross-validation in Python](https://github.com/SamComber/spacv) · [spatial-kfold (PyPI)](https://pypi.org/project/spatial-kfold/) · [PySAL esda: Moran](https://pysal.org/esda/generated/esda.Moran.html) · [h3-py: API quick reference (v4)](https://uber.github.io/h3-py/api_quick.html) · [Overture: Buildings guide](https://docs.overturemaps.org/guides/buildings/) · [NYC Open Data: 2015 Yellow Taxi Trip Data (has pickup lat/lon)](https://data.cityofnewyork.us/Transportation/2015-Yellow-Taxi-Trip-Data/2yzn-sicd)

**Recommendations**
- Keep using your two cities. Spatial stats on data you already know (Module 1's demand surface, Overture POIs) teaches more than new toy datasets.
- Watch one Anselin lecture before each theory day; he explains the intuition better than any blog.
- Spatial cross-validation is the single most interview-relevant idea here. Make the random-vs-blocked CV plot your headline figure.
- Don't drown in econometrics. Lag vs error vs GWR is enough; you can learn Durbin models when a job needs them.

**Self-check before moving on**
- [ ] Why does random K-fold overestimate the accuracy of a spatial model? Show it with your own numbers.
- [ ] Spatial lag vs spatial error: what process does each assume, and which test tells them apart?
- [ ] When would you use GWR instead of a global model with spatial features?
- [ ] What does the kriging variance tell you that IDW cannot?
- [ ] What is the area of applicability of a model, and how would you compute it?

---
 
## Module 3 — Transport Data Foundations & GIS Analytics (Weeks 11–15, 08 Dec 2026 → 06 Jan 2027)

**Why this module**  
Your department sits on counts, detectors, floating-car data, mobile-operator data, GTFS, a travel survey and a Visum model. Most of the value in year one comes from being the person who can turn all of that into clean, joined, spatially indexed tables and honest descriptive analytics, and who can move data in and out of Visum from Python without clicking.

**You finish with:** A documented transport data warehouse for one study area (DuckDB/PostGIS + Timescale): counts with QA flags, map-matched FCD speeds per link, GTFS service metrics, survey tables, and a Visum ↔ Python bridge with tests.

**Sessions**
1. *Theory* — **The transport data landscape.** Inventory what your department has: counts, detectors, FCD, mobile data, GTFS/AVL, survey, model outputs. FHWA Traffic Monitoring Guide ch. 1–3 for how counts are collected and factored.
2. *Lab* — **Counts and detectors: loading and QA.** Load permanent and short counts into DuckDB/Timescale; build QA flags (stuck sensors, impossible volumes, gaps) with pandera schemas.
3. *Lab* — **Factoring and AADT.** Compute seasonal, day-of-week and hourly factors from permanent stations and apply them to short counts; quantify the error with hold-out stations.
4. *Theory* — **Floating-car data: what it is and isn't.** Anita Graser's movement-data series + Newson & Krumm. Sampling rates, fleet bias, GPS error, and why raw FCD speeds are not link speeds until matched.
5. *Build* — **Build: map-matched FCD speeds per link.** FMM on your OSM/Visum network: match a day of FCD, derive per-link, per-15-minute speeds with sample counts, and compare with detector speeds where both exist.
6. *Lab* — **Visum ↔ Python bridge, part 1: reading.** Open your Visum model from Python through COM; pull nodes, links, zones, connectors and a demand matrix into GeoPandas/numpy.
7. *Lab* — **Visum ↔ Python bridge, part 2: writing and procedures.** Write attributes back (e.g. observed counts onto links), run a procedure sequence from Python, read results; wrap in tests on a small example network.
8. *Theory* — **Public transport data: GTFS.** GTFS reference + gtfs_kit: routes, trips, stop_times, frequencies, calendars. Service metrics: headways, span, stop-level frequency, route geometries.
9. *Lab* — **Accessibility with r5py.** Travel-time matrices from GTFS + OSM with r5py; cumulative-opportunity and gravity accessibility to jobs per zone; the accessibility book ch. 1–4.
10. *Build* — **Build: the warehouse and the first analytics report.** Assemble counts, link speeds, GTFS metrics, accessibility and zone data into one documented warehouse; produce a descriptive analytics report for the study area.
11. *Lab* — **Household travel survey: cleaning and expansion.** Load the survey; weights/expansion, trip rates by purpose and household type, mode shares; validate against counts and GTFS ridership.
12. *Lab* — **Mobile-operator and other big-data sources.** Aggregated mobile data as OD evidence: what it measures, zone-level aggregation, privacy constraints, scaling to population; compare with survey OD at district level.
13. *Write-up* — **Write-up: data foundations.** m03/README: inventory, warehouse schema, QA approach, matching results, Visum bridge, accessibility, survey validation, open issues.
14. *Build* — **Build: department-ready dashboard v0.** A Streamlit/lonboard dashboard over the warehouse: link speeds by time of day, counts and trends, transit frequency, accessibility; export of any view to GeoPackage.

**Read:** [FHWA Traffic Monitoring Guide](https://www.fhwa.dot.gov/policyinformation/tmguide/) · [Pereira & Herszenhut: Introduction to Urban Accessibility (free book)](https://ipeagit.github.io/intro_access_book/) · [TFResource: the Travel Forecasting Resource (TRB)](https://tfresource.org/) · [Newson & Krumm: Hidden Markov map matching (2009)](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/map-matching-ACM-GIS-camera-ready.pdf) · [Anita Graser: Movement data in GIS (series)](https://anitagraser.com/movement-data-in-gis/)

**Watch:** [PTV: Deep dive into the Scripting Hub and the Visum Python API (talk)](https://www.ptvgroup.com/de/10_ptv_mobility_aws26_deep_dive_scripting_hub_visum_python-api_vogel_ehlert_snethlage)

**Look at:** [PTV Visum 2025 online help (full manual)](https://cgi.ptvgroup.com/vision-help/VISUM_2025_ENG/) · [PTV Visum: Python as additional script language](https://cgi.ptvgroup.com/vision-help/VISUM_2024_ENG/Content/2_Mit_Skripten_arbeiten/2_14_Python%20als%20zus%C3%A4tzliche%20Skriptsprache.htm) · [pandera: dataframe validation](https://pandera.readthedocs.io/) · [Polars user guide](https://docs.pola.rs/) · [GTFS Schedule reference](https://gtfs.org/documentation/schedule/reference/) · [gtfs_kit: GTFS analysis in Python](https://github.com/mrcagney/gtfs_kit) · [r5py: travel-time matrices and accessibility with R5](https://r5py.readthedocs.io/) · [Fast Map Matching (FMM) documentation](https://cyang-kth.github.io/fmm/) · [Map matching with OSM data (FMM tutorial)](https://github.com/cyang-kth/osm_mapmatching) · [MovingPandas documentation](https://movingpandas.org/) · [Timescale: geospatial time series with PostGIS](https://docs.timescale.com/use-timescale/latest/extensions/postgis/) · [DuckDB: Spatial functions](https://duckdb.org/docs/current/core_extensions/spatial/functions) · [h3-py: API quick reference (v4)](https://uber.github.io/h3-py/api_quick.html)

**Recommendations**
- Use real department data wherever you can, with permission, and keep a synthetic twin of every table in the repo so the public portfolio shows the method without the data.
- Build the Visum bridge early (read network, links, zones, matrices into GeoPandas; write attributes back) and put it under tests. It will save you hundreds of hours over the next year.
- Start the algorithms habit now: two NeetCode problems a week, 30 minutes each, on non-session days if you have them or at the start of a Tuesday. It compounds toward the big-tech move.
- Every dataset gets a one-page data card: source, coverage, known biases (FCD is biased toward certain fleets; counts are biased toward arterials), refresh cadence.

**Self-check before moving on**
- [ ] What are the main biases of floating-car data and of permanent count stations, and how would each distort a congestion index?
- [ ] How do you factor a 48-hour count into an AADT, and what can go wrong?
- [ ] Explain HMM map matching in two minutes, including emission and transition probabilities.
- [ ] What is the difference between cumulative and gravity accessibility measures, and when does each mislead?
- [ ] How does Visum store a demand matrix and how do you read it into numpy without the GUI?

---

## Module 4 — Travel Demand Modelling × Machine Learning (Weeks 15–21, 07 Jan 2027 → 17 Feb 2027)

**Why this module**  
Demand modelling is your department's core product and the part of transport data science that big-tech mobility teams secretly need (demand forecasting, ETA, pricing all sit on top of it). Knowing the four-step and activity-based structure, estimating choice models properly, and then showing exactly where ML beats or loses to logit is a rare combination.

**You finish with:** A mode-choice study (logit vs GBM vs neural, with elasticities), an OD-estimation experiment with known truth, an open assignment pipeline, and a note on where ML belongs inside the department's Visum workflow.

**Sessions**
1. *Theory* — **The four-step model and where it breaks.** TFResource and NCHRP 716 on model structure: generation, distribution, mode choice, assignment; feedback; the known failure modes.
2. *Theory* — **Random utility and the logit family.** Train ch. 2–3 (and MIT 1.201 notes): random utility, MNL derivation, IIA, nested logit; value of time from coefficients.
3. *Lab* — **Estimating a mode-choice model with Biogeme.** Swissmetro tutorial, then your survey: MNL with level-of-service from your skims; segment by purpose; goodness of fit, t-stats, VoT.
4. *Lab* — **Nested logit and segmentation.** Add nests (motorised/non-motorised, car/transit) and household segments; likelihood-ratio tests; which structure the data supports.
5. *Build* — **Build: logit vs GBM vs neural for mode choice.** Same choice table, three families; proper out-of-sample evaluation (by household, not by trip); log-loss, accuracy, calibration, and elasticities from each.
6. *Theory* — **Trip generation and distribution.** Trip rates vs regression vs GBM for generation; gravity and destination-choice models for distribution; calibration to survey trip-length distributions.
7. *Lab* — **Skims and assignment with AequilibraE.** Build the open network, compute skims, run user-equilibrium assignment; compare assigned volumes with Visum's on the same OD.
8. *Theory* — **Assignment theory.** Wardrop's principles, BPR volume-delay, Frank–Wolfe, stochastic assignment; why assignment is a fixed point and what that means for calibration.
9. *Lab* — **OD estimation: the problem.** Matrix estimation from counts: under-determination, priors, entropy/least-squares formulations, GEH. Visum's TFlowFuzzy and what it assumes.
10. *Build* — **Build: OD estimation with counts + FCD.** Estimate OD from counts with and without FCD-derived route shares and partial OD; evaluate against synthetic truth; then run on real data in Visum.
11. *Theory* — **Activity-based models.** ActivitySim component overview: tours, scheduling, mode choice at tour and trip level; what ABMs buy you and what they cost.
12. *Lab* — **Population synthesis and ML inside the pipeline.** Where ML helps: synthetic populations, imputing missing survey attributes, learned destination choice, speeding up skims; where it harms: non-monotone responses to policy.
13. *Lab* — **Validation and calibration discipline.** Validation hierarchy: screenlines, GEH, trip-length distributions, mode shares, transit boardings; calibration vs over-fitting; documenting adjustments.
14. *Lab* — **Scenario analysis the ML way.** Scenarios as experiments: run the model over a design of scenarios; emulate outputs with a surrogate; sensitivity of KPIs to inputs with SALib.
15. *Theory* — **Reading: demand forecasting at mobility companies.** Uber's forecasting introduction and the H3 post reread with demand in mind: how a marketplace frames demand, metrics, granularity, and how that differs from a planning model.
16. *Write-up* — **Write-up: demand × ML.** m04/README: model structure, choice-model comparison with elasticities, OD estimation findings, assignment agreement, ABM position, ML-in-the-pipeline map.
17. *Build* — **Build: ship something at work.** Take one finding (better mode-choice segmentation, an OD-estimation improvement, a validation report) into the real Visum model via your Python bridge; document before/after.
18. *Build* — **Build: review + recorded explanation.** Record a 10-minute explanation of discrete choice vs ML for mode choice and of OD estimation's identifiability; fix the two weakest parts of the module; merge.

**Read:** [TFResource: the Travel Forecasting Resource (TRB)](https://tfresource.org/) · [NCHRP Report 716: Travel Demand Forecasting, Parameters and Techniques](https://www.trb.org/Publications/Blurbs/167055.aspx) · [MIT OCW 1.201J: Transportation Systems Analysis, Demand & Economics](https://ocw.mit.edu/courses/1-201j-transportation-systems-analysis-demand-and-economics-fall-2008/) · [Kenneth Train: Discrete Choice Methods with Simulation (free online)](https://eml.berkeley.edu/books/choice2.html) · [Wang, Mo & Zhao: Deep neural networks for choice analysis](https://arxiv.org/abs/1812.04528)

**Look at:** [Biogeme documentation (EPFL)](https://biogeme.epfl.ch/sphinx/index.html) · [xlogit: fast multinomial and mixed logit in Python](https://xlogit.readthedocs.io/) · [AequilibraE: open-source transport modelling in Python](https://www.aequilibrae.com/) · [ActivitySim documentation](https://activitysim.github.io/activitysim/) · [PTV Visum 2025 online help (full manual)](https://cgi.ptvgroup.com/vision-help/VISUM_2025_ENG/) · [PTV Visum: Python as additional script language](https://cgi.ptvgroup.com/vision-help/VISUM_2024_ENG/Content/2_Mit_Skripten_arbeiten/2_14_Python%20als%20zus%C3%A4tzliche%20Skriptsprache.htm) · [Optuna tutorial](https://optuna.readthedocs.io/en/stable/tutorial/index.html) · [PySAL esda: Moran](https://pysal.org/esda/generated/esda.Moran.html)

**Recommendations**
- Estimate the logit model first and make it good (nests, segmentation, value of time that makes sense). Only then let a GBM compete; most ML-beats-logit papers compare against a bad logit.
- Report elasticities and value of time from every model, including the GBM and the neural one. If you can't get them, you don't have a demand model, you have a classifier.
- For OD estimation, build the truth yourself (synthetic OD → assignment → counts) before touching real counts. You will learn how non-identifiable the problem is.
- Use Visum for assignment at work and AequilibraE at home; keep the same zone system so results are comparable.

**Self-check before moving on**
- [ ] Derive the multinomial logit choice probability from random utility with Gumbel errors; state the IIA property and when it fails.
- [ ] How do you compute a direct and cross elasticity from an estimated logit model? From a GBM?
- [ ] Why is OD matrix estimation from link counts under-determined, and what do priors, FCD and GEH statistics each contribute?
- [ ] User equilibrium vs system optimum: define both; what does Frank–Wolfe iterate on?
- [ ] Name three places in a four-step pipeline where ML helps and one where it actively harms.

---

## Module 5 — Trajectories & Traffic Flow (Weeks 21–26, 18 Feb 2027 → 24 Mar 2027)

**Why this module**  
Trajectories are the raw material of modern traffic analysis: floating cars, drones, and later cameras all produce them. This module gives you the theory (traffic flow, fundamental diagrams, the MFD) and the tooling (MovingPandas, map matching, SUMO as ground truth) to turn them into the quantities your department reports and your models consume.

**You finish with:** A trajectory toolkit (MovingPandas + map matching), fundamental diagrams from pNEUMA/NGSIM, turning-movement counts and an OD matrix for your study area.

**Sessions**
1. *Theory* — **Trajectories as objects.** MovingPandas tutorials 1–3: TrajectoryCollection, speed/direction, stops, splitting, generalisation.
2. *Theory* — **Map matching theory.** Newson & Krumm: HMM map matching; emission vs transition probabilities; failure modes.
3. *Lab* — **Map matching in practice.** FMM on an OSMnx graph: match pNEUMA and GeoLife trajectories; measure matched fraction and sanity-check.
4. *Theory* — **Traffic flow theory.** Flow, density, speed; Greenshields and the fundamental diagram; shockwaves (LWR) intuition.
5. *Build* — **Build: fundamental diagrams from real trajectories.** NGSIM US-101 and pNEUMA: compute flow, density and speed on segments and plot the fundamental diagram; compare with detector and FCD-derived values from Module 3.
6. *Lab* — **Turning movements and intersection analytics.** From tracks to turning-movement counts at an intersection; compare with zone-based counts.
7. *Lab* — **OD matrices and flows.** scikit-mobility: OD matrices from trajectories at H3 zones; flow maps; the identifiability problem.
8. *Theory* — **Macroscopic fundamental diagram.** Geroliminis & Daganzo: the city-wide MFD; reproduce the idea on pNEUMA.
9. *Lab* — **Simulation as ground truth.** SUMO: build a small network from OSM, simulate a day, export trajectories and detector counts; test your estimators.
10. *Build* — **Build: trajectory toolkit package.** Package src/mobilitylab/traj: loading, cleaning, map matching, Edie metrics, turning movements, OD; tests on SUMO data.
11. *Lab* — **Anomalies and events in trajectories.** Stops, queues, wrong-way, near-misses (TTC) from trajectories; precision on hand-checked cases.
12. *Lab* — **Privacy and ethics of movement data.** Re-identification risk, aggregation thresholds, k-anonymity for OD; write your data policy.
13. *Theory* — **Reading: how cities use this.** Traffic-engineering practice: signal timing inputs, level of service, what planners ask for.
14. *Write-up* — **Write-up: trajectories and flow.** m07/README: toolkit, fundamental diagrams, TMC, OD, MFD, simulation validation, privacy policy.
15. *Build* — **Build: study-area dashboard.** A Streamlit/lonboard dashboard: segment speeds, turning movements, OD flows, queue lengths for one day.

**Read:** [Anita Graser: MovingPandas hands-on tutorials](https://anitagraser.com/2019/09/11/movement-data-in-gis-24-movingpandas-hands-on-tutorials/) · [Anita Graser: Movement data in GIS (series)](https://anitagraser.com/movement-data-in-gis/) · [Newson & Krumm: Hidden Markov map matching (2009)](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/map-matching-ACM-GIS-camera-ready.pdf) · [FHWA: Traffic Flow Theory monograph (revised)](https://rosap.ntl.bts.gov/view/dot/35775) · [Traffic Flow Theory (chapter, Springer open PDF)](https://link.springer.com/content/pdf/10.1007/978-3-319-69231-9_3.pdf) · [Geroliminis & Daganzo: Existence of urban-scale macroscopic fundamental diagrams](https://escholarship.org/uc/item/2rq792j1)

**Look at:** [MovingPandas documentation](https://movingpandas.org/) · [scikit-mobility documentation](https://scikit-mobility.github.io/scikit-mobility/) · [Fast Map Matching (FMM) documentation](https://cyang-kth.github.io/fmm/) · [Map matching with OSM data (FMM tutorial)](https://github.com/cyang-kth/osm_mapmatching) · [NGSIM vehicle trajectories (US-101, I-80)](https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj) · [pNEUMA: drone trajectories over Athens (EPFL open data)](https://open-traffic.epfl.ch/) · [SUMO: tutorials](https://github.com/eclipse-sumo/sumo/blob/main/docs/web/docs/Tutorials/index.md) · [SUMO: interfacing TraCI from Python](https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html) · [GeoLife GPS trajectories (Microsoft Research)](https://www.microsoft.com/en-us/research/publication/geolife-gps-trajectory-dataset-user-guide/) · [OSMnx: User reference](https://osmnx.readthedocs.io/en/stable/user-reference.html) · [h3-py: API quick reference (v4)](https://uber.github.io/h3-py/api_quick.html)

**Recommendations**
- Learn MovingPandas properly; it's the standard Python trajectory library and Anita Graser's tutorials are the best way in.
- Map matching is where GIS and CV meet: FCD and camera tracks become road-segment observations only after it.
- Use SUMO to make synthetic ground truth when you need to test an estimator; it's free and realistic enough.
- Think in traffic-engineering units from the start: veh/h, veh/km, km/h, and the fundamental diagram tying them together.

**Self-check before moving on**
- [ ] Explain the fundamental diagram and what the capacity point means.
- [ ] How does HMM map matching trade off emission and transition probabilities?
- [ ] How do you estimate an OD matrix from partial observations, and what's unidentifiable?
- [ ] Why does a macroscopic fundamental diagram exist for a whole city, and when does it break?
- [ ] What are the privacy risks of trajectory data, and how do you mitigate them?

---

## Module 6 — City-Scale Spatio-Temporal Analytics & Forecasting (Weeks 26–31, 25 Mar 2027 → 28 Apr 2027)

**Why this module**  
Short-term prediction is where transport data science meets production ML: a segment-level traffic state, honest baselines, gradient boosting, then spatio-temporal graph networks, all evaluated per horizon with uncertainty. It is also the single most common 'ML system design' question at mobility companies.

**You finish with:** A segment-level traffic state table, an incident detector, and a forecasting benchmark (seasonal naive → GBM → DCRNN) on METR-LA plus your own data.

**Sessions**
1. *Theory* — **Forecasting fundamentals.** FPP3 chapters on decomposition, baselines, evaluation; set up rolling-origin backtests.
2. *Lab* — **Real sensor data: METR-LA and PeMS.** Load METR-LA/PEMS-BAY; missingness, sensor graph, daily profiles; the PeMS tutorial on aggregation.
3. *Lab* — **Segment-level state from your own data.** Aggregate detector counts, map-matched FCD speeds and trajectories to road segments and H3 cells per 5 minutes; store in TimescaleDB.
4. *Lab* — **Gradient-boosted forecasting.** LightGBM with lag, calendar and neighbour features for all sensors; per-horizon errors vs baselines.
5. *Build* — **Build: DCRNN / Graph WaveNet benchmark.** Train DCRNN (and one more ST-GNN via LibCity or PGT) on METR-LA on the 4060; reproduce published numbers within tolerance.
6. *Lab* — **Apply forecasting to your segments.** Same pipeline on your segment_state table; small-data realities; per-segment-class errors.
7. *Lab* — **Incident and anomaly detection.** Detect incidents from speed drops vs expected profile; evaluate false-alarm rate on SUMO-injected incidents.
8. *Theory* — **Graph ML foundations.** CS224W lectures 4–7: message passing, GCN/GAT, over-smoothing; relate to DCRNN's diffusion convolution.
9. *Lab* — **Uncertainty and evaluation discipline.** Prediction intervals (quantile GBM, conformal), coverage checks, and horizon-wise reporting standards.
10. *Build* — **Build: city traffic-state service.** API + map: current segment speeds, 30-minute forecast, active incidents; refreshed from the database.
11. *Lab* — **Monitoring and drift.** Evidently reports on input drift (counts, FCD speeds) and model error drift; alerts.
12. *Theory* — **Reading: network-level traffic science.** MFD applications (perimeter control), and how cities report congestion (TomTom/INRIX-style indices).
13. *Write-up* — **Write-up: analytics and forecasting.** m08/README: data model, benchmark table, incident detection, uncertainty, monitoring, KPIs.
14. *Lab* — **Reproducibility pass.** make m08-benchmark rebuilds every table; seeds pinned; MLflow runs tagged.
15. *Build* — **Build: capstone design kickoff.** Merge m08; write the capstone design-doc skeleton: the city traffic analytics platform (warehouse → state → forecasts → twin → scenarios → map).

**Read:** [Hyndman & Athanasopoulos: Forecasting, Principles and Practice (free)](https://otexts.com/fpp3/) · [Li et al.: DCRNN, data-driven traffic forecasting](https://arxiv.org/abs/1707.01926) · [Caltrans PeMS tutorial (loop-detector data)](https://people.eecs.berkeley.edu/~varaiya/papers_ps.dir/PeMSTutorial.pdf) · [Geroliminis & Daganzo: Existence of urban-scale macroscopic fundamental diagrams](https://escholarship.org/uc/item/2rq792j1) · [Uber: Forecasting at Uber, an introduction](https://www.uber.com/blog/forecasting-introduction/)

**Watch:** [Stanford CS224W: Machine Learning with Graphs (videos)](http://snap.stanford.edu/class/cs224w-2021/)

**Look at:** [DCRNN in PyTorch](https://github.com/chnsh/DCRNN_PyTorch) · [PyTorch Geometric Temporal: datasets](https://pytorch-geometric-temporal.readthedocs.io/en/latest/modules/dataset.html) · [PyTorch Geometric Temporal: introduction](https://pytorch-geometric-temporal.readthedocs.io/en/latest/notes/introduction.html) · [LibCity: urban spatio-temporal prediction library](https://github.com/LibCity/Bigscity-LibCity) · [STG4Traffic: survey & benchmark of ST-GNNs for traffic](https://github.com/trainingl/STG4Traffic) · [Timescale: geospatial time series with PostGIS](https://docs.timescale.com/use-timescale/latest/extensions/postgis/) · [lonboard: fast geospatial visualisation in Jupyter](https://developmentseed.org/lonboard/latest/) · [h3-py: API quick reference (v4)](https://uber.github.io/h3-py/api_quick.html) · [PySAL esda: Moran](https://pysal.org/esda/generated/esda.Moran.html) · [Evidently (drift reports & tests)](https://github.com/evidentlyai/evidently)

**Recommendations**
- Baselines first: historical average and seasonal naive are hard to beat at 15-minute horizons. Report them next to every neural model.
- Use METR-LA/PEMS-BAY to validate your forecasting code, then apply the same pipeline to your own segment data.
- Evaluate per horizon (15/30/60 min) and per segment class; an average over horizons hides the interesting failures.
- Spatial autocorrelation of residuals (Moran's I, Module 1) is your model-diagnostics tool here too.

**Self-check before moving on**
- [ ] Why do seasonal-naive baselines beat many neural models on short horizons?
- [ ] What does the graph in DCRNN encode, and how is the adjacency built?
- [ ] How would you detect an incident from speed and flow with a low false-alarm rate?
- [ ] How do you backtest a forecaster without leakage?
- [ ] Which drift would you monitor on a deployed traffic model and why?

---

## Module 7 — Simulation × ML: Calibration, Causal Evaluation & Signal Control (Weeks 31–36, 29 Apr 2027 → 02 Jun 2027)

**Why this module**  
A transport model is a simulator, and the modern way to work with simulators is ML: calibrate them with Bayesian optimisation, replace slow runs with surrogates, and treat real-world interventions as experiments to be evaluated causally. Add a taste of reinforcement learning for signals and you cover the questions a department and a mobility company both ask: 'what happens if', 'did it work', and 'can it run itself'.

**You finish with:** A calibrated SUMO twin of your study area with a documented calibration method, a surrogate model for scenario screening, two causal before/after evaluations of real interventions, and an RL signal-control experiment benchmarked against max-pressure.

**Sessions**
1. *Theory* — **Simulation as a scientific instrument.** Microscopic vs mesoscopic vs macroscopic; what SUMO and Visum each represent; calibration vs validation; stochasticity and seeds.
2. *Lab* — **A SUMO twin of the study area.** OSM Web Wizard, then replace random demand with your OD (Module 4) and detectors at your real count locations; run a morning peak.
3. *Lab* — **Calibration with Optuna.** Objective = weighted GEH on counts + speed error on FCD links; Optuna TPE over car-following and demand-scaling parameters; seeds handled properly.
4. *Theory* — **Sensitivity analysis.** Morris screening and Sobol indices with SALib; which parameters matter for which KPI; use it to prune the calibration space.
5. *Build* — **Build: surrogate for scenario screening.** Train a surrogate (GBM or GP) from simulation runs to predict KPIs from scenario inputs; validate on held-out runs; use it to screen 1,000 scenarios in seconds.
6. *Theory* — **Causal inference for transport interventions.** Facure ch. 1–3 and the DiD chapter: potential outcomes, confounding, parallel trends; why before/after without controls is not evidence.
7. *Lab* — **Difference-in-differences on real data.** Pick an intervention (new bus lane, signal retiming, speed limit) with pre/post data from the warehouse; choose controls; test pre-trends; estimate the effect with intervals.
8. *Lab* — **Synthetic control and CausalImpact.** When you have one treated corridor and many candidates: synthetic control; Bayesian structural time series on the warehouse time series.
9. *Build* — **Build: intervention-evaluation playbook.** Package the evaluation as src/mobilitylab/causal: panel building, pre-trend tests, DiD, synthetic control, reporting; apply it to a second intervention; write the department playbook.
10. *Theory* — **Experimentation in marketplaces.** DoorDash and Lyft posts + the switchback paper: interference, SUTVA violations, switchback and cluster designs, variance, and Kohavi's trustworthiness checks (SRM, guardrails).
11. *Lab* — **Switchback simulator on the twin.** Use the SUMO twin as the world: implement a treatment (e.g. signal plan), simulate user-level vs switchback randomisation, measure bias and variance of each estimator.
12. *Theory* — **RL for signal control: concepts.** MDP framing of a junction; state (queues, pressure), action (phase), reward (delay, pressure); max-pressure as the baseline that is hard to beat; RESCO benchmark.
13. *Lab* — **RL agent vs max-pressure.** Train a DQN/PPO agent with sumo-rl on the junction (then a small arterial); evaluate on unseen demand; compare with fixed-time and max-pressure.
14. *Write-up* — **Write-up: simulation × ML.** m07/README: calibration method and trade-offs, sensitivity, surrogate, two causal evaluations, switchback experiment, RL results and honest conclusions.
15. *Build* — **Build: scenario studio v1.** Combine the twin, the surrogate and the evaluation package into a small app: define a scenario, screen with the surrogate, confirm with simulation, export a Visum-compatible result; demo to the department.

**Read:** [Facure: Causal Inference for the Brave and True (free book)](https://matheusfacure.github.io/python-causality-handbook/landing-page.html) · [Bojinov, Simchi-Levi & Zhao: Design and analysis of switchback experiments](https://arxiv.org/abs/2009.00148) · [DoorDash: Switchback tests and randomized experimentation under network effects](https://careersatdoordash.com/blog/switchback-tests-and-randomized-experimentation-under-network-effects-at-doordash/) · [Lyft: Experimentation in a ridesharing marketplace](https://eng.lyft.com/experimentation-in-a-ridesharing-marketplace-b39db027a66e) · [Kohavi, Tang & Xu: Trustworthy Online Controlled Experiments (book site)](https://experimentguide.com/)

**Look at:** [SUMO: OSM Web Wizard tutorial](https://sumo.dlr.de/docs/Tutorials/OSMWebWizard.html) · [SUMO: TraCI for traffic lights tutorial](https://sumo.dlr.de/docs/Tutorials/TraCI4Traffic_Lights.html) · [SUMO: interfacing TraCI from Python](https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html) · [Optuna tutorial](https://optuna.readthedocs.io/en/stable/tutorial/index.html) · [SALib: sensitivity analysis in Python](https://salib.readthedocs.io/) · [DoWhy documentation](https://www.pywhy.org/dowhy/) · [tfcausalimpact: Bayesian structural time series for before/after studies](https://github.com/WillianFuks/tfcausalimpact) · [sumo-rl: reinforcement-learning environments for signal control](https://github.com/LucasAlegre/sumo-rl) · [RESCO: benchmark for RL traffic signal control](https://github.com/Pi-Star-Lab/RESCO) · [PTV Visum: Python as additional script language](https://cgi.ptvgroup.com/vision-help/VISUM_2024_ENG/Content/2_Mit_Skripten_arbeiten/2_14_Python%20als%20zus%C3%A4tzliche%20Skriptsprache.htm)

**Recommendations**
- Calibrate against several observations at once (counts, speeds, travel times) and report the trade-off; a model matched to counts alone will lie about speeds.
- Before/after studies are where departments most often fool themselves. Always have a control (unaffected corridors), test for parallel pre-trends, and report the effect with an interval.
- RL signal control is a one-week taste, not a research project: the goal is to be able to explain why it rarely beats a well-tuned max-pressure baseline in practice.
- The experimentation readings are for the big-tech move: marketplace interference, switchbacks and trustworthy A/B tests are standard interview material at mobility companies.

**Self-check before moving on**
- [ ] What is the difference between calibration and validation of a simulation, and how do you avoid calibrating to noise?
- [ ] Explain Sobol indices to a traffic engineer in one minute.
- [ ] Set up a difference-in-differences for a new bus lane: units, periods, controls, assumptions, threats.
- [ ] Why do user-level A/B tests fail in a two-sided marketplace, and what does a switchback design change?
- [ ] What state, action and reward would you give an RL signal controller, and what goes wrong with each choice?

---

## Module 8 — Video CV for Traffic Counts (Weeks 36–39, 03 Jun 2027 → 24 Jun 2027)

**Why this module**  
Cameras are the cheapest new sensor a department can add, and pretrained detectors are good enough that counts, turning movements and classification from video are a two-week project rather than a research programme. You keep enough computer vision to build and evaluate a counting pipeline and to feed its output into the warehouse and the model.

**You finish with:** A counting pipeline (YOLO + ByteTrack + zones) evaluated with HOTA and against manual counts, a ground-plane homography for one camera, turning-movement counts for one junction, and counts flowing into the warehouse as a sensor type.

**Sessions**
1. *Theory* — **Detection and tracking in one afternoon.** Ultralytics YOLO11 on a traffic clip; ByteTrack via the track mode; the Kalman-filter picture; what the tracker IDs mean for counting.
2. *Lab* — **Counting with lines and zones.** supervision LineZone and PolygonZone for per-direction and per-lane counts; compare with a manual 10-minute count.
3. *Lab* — **Labelling and tracker evaluation.** Label 150 frames (boxes + IDs) in CVAT on a short clip; TrackEval HOTA/MOTA/IDF1 for ByteTrack vs BoT-SORT; tune thresholds.
4. *Build* — **Build: counting service.** A service that takes a clip or stream + camera config and writes per-minute counts by class, lane and direction; robustness test at night and at 5/10/25 FPS; TensorRT or ONNX export for speed.
5. *Theory* — **Image to ground plane.** Nayar on image formation and homography; four to six ground control points from a basemap; reprojection error; where homographies fail.
6. *Lab* — **Tracks to the map and turning movements.** Project track points to the ground plane and to WGS84; define approach and exit zones; turning-movement counts for one junction versus a manual TMC.
7. *Lab* — **Fine-tuning when needed.** Mine low-confidence frames from your cameras; label 100; fine-tune YOLO11s; measure the gain per labelled frame and on the night subset.
8. *Lab* — **Drone and aerial video.** pNEUMA-style drone views: tiny objects, tiling, nadir geometry; how drone trajectories complement fixed cameras.
9. *Write-up* — **Write-up: video counts.** m08/README: pipeline, evaluation (HOTA, count error), robustness, homography and TMC, fine-tuning decision, integration with the warehouse, limits and camera terms of use.
10. *Build* — **Build: camera counts into the model.** Feed one week of camera counts into the validation report (Module 4) and the calibration targets (Module 7); 60-second annotated demo video; merge.

**Read:** [Zhang et al.: ByteTrack, associating every detection box](https://arxiv.org/abs/2110.06864) · [Bzarg: How a Kalman filter works, in pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/) · [LearnOpenCV: homography examples (Python)](https://learnopencv.com/homography-examples-using-opencv-python-c/)

**Watch:** [Shree Nayar: First Principles of Computer Vision (lecture series)](https://www.youtube.com/watch?v=1EJ84QqkxWc)

**Look at:** [Ultralytics: Python usage (train, predict, val)](https://docs.ultralytics.com/usage/python) · [Ultralytics: multi-object tracking (ByteTrack, BoT-SORT)](https://docs.ultralytics.com/modes/track) · [Ultralytics: model export (ONNX, TensorRT)](https://docs.ultralytics.com/modes/export) · [supervision (Roboflow) docs](https://supervision.roboflow.com/) · [supervision: LineZone counting](https://supervision.roboflow.com/detection/tools/line_zone/) · [supervision: count objects in a zone](https://supervision.roboflow.com/latest/how_to/count_in_zone/) · [TrackEval: HOTA and other MOT metrics](https://github.com/JonathonLuiten/TrackEval) · [UA-DETRAC vehicle detection & tracking benchmark](https://www.sciencedirect.com/science/article/abs/pii/S1077314220300035) · [OpenCV: camera calibration tutorial](https://docs.opencv.org/4.13.0/dc/dbb/tutorial_py_calibration.html) · [OpenCV: features + homography tutorial](https://docs.opencv.org/4.13.0/d7/dff/tutorial_feature_homography.html) · [CVAT annotation tool](https://github.com/cvat-ai/cvat) · [pNEUMA: drone trajectories over Athens (EPFL open data)](https://open-traffic.epfl.ch/)

**Recommendations**
- Use pretrained YOLO11 and only fine-tune if your cameras' failure cases demand it; 150 labelled frames is usually enough.
- Evaluate tracking with HOTA on a labelled clip and counts against a manual count; demo videos hide ID switches.
- Treat the camera as another station in the warehouse: same schema, same QA flags, plus a camera-health check.
- If you buy the RTX 4060, this is where it pays; otherwise Colab handles clips fine.

**Self-check before moving on**
- [ ] Why does a missed detection on one frame rarely break a count, while an ID switch does?
- [ ] What does HOTA measure that MOTA doesn't?
- [ ] How many ground control points does a homography need and why should they come from a basemap?
- [ ] What are the three biggest sources of count error at night and how would you measure them?

---

## Module 9 — Capstone: City Traffic Analytics Platform (Weeks 40–49, 29 Jun 2027 → 31 Aug 2027)

**Why this module**  
Everything so far becomes one system a city department could run and a big-tech interviewer can be walked through: observed data in, calibrated model and forecasts in the middle, scenario evaluation and monitoring out, with a design doc, an MLOps loop and a public demo on synthetic data. It is the artefact for both of your next two steps.

**You finish with:** A deployed demo (synthetic twin city), design doc v2, MLOps loop (registry, gates, drift, data-quality alerts), the Visum integration path, three trade-off case studies, a new-city playbook and a recorded walkthrough.

**Sessions**
1. *Theory* — **Architecture and budgets.** Draw the platform: ingest (counts, FCD, GTFS, cameras) → warehouse → link state → forecasts & incidents → model/twin → scenario studio → map and API; batch and streaming paths; retraining loop. Budgets on every arrow.
2. *Lab* — **Ingestion pipelines.** Airflow (or Dagster) DAGs for counts, FCD, GTFS; pandera contracts at every boundary; back-fill and idempotency.
3. *Lab* — **Link-state and forecasting services.** segment_state continuous aggregates; forecast job every 5–15 minutes; incident detector; FastAPI endpoints with contract tests.
4. *Lab* — **Camera workers.** Module 8 counting service as a managed worker with camera-health monitoring; recorded clips replayed as streams for the demo.
5. *Build* — **Build: platform thin slice.** Everything wired end to end on the synthetic twin: ingest → state → forecast → map. One command up, one command down, seeded data.
6. *Lab* — **Map front end.** MapLibre page: link speeds now and forecast slider, incidents, cameras with latest frame, accessibility and scenario layers; export buttons.
7. *Lab* — **Scenario studio integrated.** Module 7's twin, surrogate and evaluation package behind the API; scenario definitions stored; results as map layers and Visum exports.
8. *Lab* — **Model registry and CI gates.** MLflow champion/challenger for forecaster, mode-choice model and calibrated twin parameters; CI runs evaluation gates before promotion.
9. *Lab* — **Monitoring and failure modes.** Evidently drift on inputs and errors; data-freshness and sensor-health alerts; camera drift; forecast-error drift; a runbook per alert.
10. *Build* — **Build: load and chaos tests.** Locust on the API; kill a worker, stall the database, feed a frozen camera, poison a count feed; record user-visible impact and recovery time.
11. *Lab* — **Deploy the public demo.** Slim demo on a Hugging Face Docker Space or small VM: synthetic twin, replayed clips, CPU-only detector; clearly labelled as synthetic.
12. *Lab* — **New-city playbook.** Document and test the steps to onboard a new study area: data inventory, zone system, network export from Visum, calibration budget, camera setup, validation.
13. *Write-up* — **Design doc v1.** Full doc: problem, users (department and city), requirements with budgets, architecture, data, models, evaluation, monitoring, risks, alternatives rejected, rollout.
14. *Lab* — **Reproducibility audit.** Fresh clone, make reproduce; every headline number regenerates or has an explanation; seeds pinned; data versions recorded.
15. *Build* — **Build: trade-off case studies.** Three 'considered and rejected' studies with numbers: e.g. GBM vs ST-GNN for forecasting, Visum-only vs twin for scenarios, user-level vs switchback evaluation.
16. *Lab* — **Diagram and document polish.** Consistent diagrams, naming and budgets; a glossary for non-ML readers in the department; accessibility of figures.
17. *Lab* — **Portfolio README.** Top-level README: 2-minute summary, demo link, diagram, six headline numbers, module reports, how to reproduce, how to onboard a city.
18. *Lab* — **Ask for review.** Send the design doc to two reviewers (one transport, one ML/software); mark unclear sentences yourself first.
19. *Write-up* — **Address feedback.** Triage review comments into must-fix, should-fix, won't-fix with reasons; update doc and numbers.
20. *Build* — **Build: recorded walkthrough v1.** 15-minute walkthrough of the platform and design doc; watch back; list five improvements.
21. *Lab* — **Optional: Kubernetes or catch-up.** kind cluster with Deployments, Services and probes for API and one worker; or clear the backlog.
22. *Lab* — **Visum integration polish.** The bridge as a documented package: install, read/write, procedures, result import; example notebooks the department can run.
23. *Write-up* — **Design doc v2.** Fold in walkthrough and review improvements; final proofread; version and freeze.
24. *Lab* — **Résumé, LinkedIn and the internal case.** Five résumé bullets with numbers; a LinkedIn post with the demo; a one-page internal note proposing the platform as a department tool.
25. *Build* — **Build: freeze v1.0.** Tag v1.0 with release notes; archive numbers; plan the remaining weeks.
26. *Lab* — **Buffer: fix what broke.** Reserved for whatever the walkthrough, reviewers or the demo exposed.
27. *Lab* — **Buffer: extension or blog post.** Either one extension (multi-junction RL, transit forecasting, a second city) or a public write-up of the platform.
28. *Build* — **Build: final capstone review.** Dry-run the 15-minute presentation to a peer; collect questions; fix the doc; merge everything.

**Read:** [Malte Ubl: Design docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) · [Eugene Yan: How to write design docs for ML systems](https://eugeneyan.com/writing/ml-design-docs/) · [Sculley et al.: Hidden technical debt in ML systems](https://proceedings.neurips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf) · [Zinkevich: Rules of Machine Learning (PDF)](https://martin.zinkevich.org/rules_of_ml/rules_of_ml.pdf) · [Chip Huyen: Designing ML Systems (book resources)](https://github.com/chiphuyen/dmls-book)

**Watch:** [Eugene Yan: System design for recommendations and search (talk)](https://www.youtube.com/watch?v=lh9CNRDqKBk)

**Look at:** [MLflow: Model registry tutorial](https://mlflow.org/docs/latest/ml/model-registry/tutorial) · [MLflow: Model registry workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow) · [Evidently (drift reports & tests)](https://github.com/evidentlyai/evidently) · [Hugging Face: Docker Spaces](https://huggingface.co/docs/hub/spaces-sdks-docker) · [MapLibre GL JS docs](https://maplibre.org/maplibre-gl-js/docs/) · [Timescale: geospatial time series with PostGIS](https://docs.timescale.com/use-timescale/latest/extensions/postgis/) · [lonboard: fast geospatial visualisation in Jupyter](https://developmentseed.org/lonboard/latest/) · [Locust: your first load test](https://docs.locust.io/en/stable/quickstart.html) · [FastAPI: Tutorial / user guide](https://fastapi.tiangolo.com/tutorial/) · [Airflow 101: building your first workflow](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html) · [PTV Visum: Python as additional script language](https://cgi.ptvgroup.com/vision-help/VISUM_2024_ENG/Content/2_Mit_Skripten_arbeiten/2_14_Python%20als%20zus%C3%A4tzliche%20Skriptsprache.htm)

**Recommendations**
- Scope: one study area, the sensors you have, a synthetic twin for the public demo. A thin slice that runs beats a wide system that doesn't.
- Every headline number reproduces from a clean checkout. numbers.md is the single source of truth and the design doc quotes it.
- Build the Visum integration as a first-class path, not an afterthought: that is what makes it useful at work in year one.
- Write the design doc as if a staff engineer at a mobility company will read it. Budgets on every arrow, alternatives rejected with numbers.

**Self-check before moving on**
- [ ] Draw the architecture and state the latency, freshness and cost budget on every arrow.
- [ ] Which three failure modes would you detect first in production, and how?
- [ ] What is in your CI gate before a forecaster or a calibrated model is promoted?
- [ ] Give the three trade-offs you considered and rejected, each with a number.

---

## Module 10 — Interview Readiness: Big-Tech DS/ML with a Transport Edge (Weeks 49–57, 01 Sep 2027 → 27 Oct 2027)

**Why this module**  
The move to a big-tech mobility, maps or marketplace team is decided in four rounds: coding, SQL/statistics, ML system design and behavioural. Your transport depth is the differentiator; this module makes sure the generic rounds don't filter you out before anyone sees it.

**You finish with:** Five recorded derivations, a <15-minute capstone walkthrough, four solo and two peer mocks, 60+ algorithm problems and 40+ SQL questions logged, an experimentation cheat-sheet, a story bank, and a reviewed readiness checklist.

**Sessions**
1. *Review* — **Derivation 1: spatial and temporal cross-validation.** From memory: why random folds lie on spatial and time-series data, blocked/buffered and rolling-origin designs, area of applicability; record it.
2. *Review* — **Derivation 2: discrete choice and OD estimation.** Logit from random utility, IIA, nested logit, elasticities; OD estimation as an under-determined inverse problem and what information fixes it.
3. *Review* — **Derivation 3: map matching, trajectories and flow.** HMM map matching; Edie's definitions; q = k·v; fundamental diagram and MFD; what detectors, FCD and cameras each measure.
4. *Review* — **Derivation 4: spatio-temporal forecasting.** Baselines, GBM with lags and neighbours, DCRNN's diffusion convolution, per-horizon evaluation, backtesting, prediction intervals.
5. *Mock* — **Mock #1: design ETA prediction for a ride-hailing app.** 40-minute timed design, out loud and recorded; use DeepETA as the reference answer afterwards; rewrite as a one-page outline.
6. *Review* — **Derivation 5: experimentation and causal evaluation.** A/B basics, power, SRM, guardrails; interference and switchbacks; DiD and synthetic control; when each applies.
7. *Review* — **Capstone walkthrough under 15 minutes.** Present the design doc end to end; hard stop at 15 minutes; record.
8. *Lab* — **Coding set 1: arrays, hashing, two pointers, sliding window.** Timed NeetCode set: six problems in 2 hours, talking aloud; log results.
9. *Lab* — **Coding set 2: trees, graphs, BFS/DFS, shortest paths.** Timed set with a transport flavour: shortest path, connected components, topological sort, grid BFS.
10. *Mock* — **Mock #2: design demand forecasting and dispatch signals for a marketplace.** 40-minute design: H3-cell demand forecasts feeding dispatch/pricing; evaluation under interference.
11. *Lab* — **SQL set 1.** StrataScratch: twelve medium questions, window functions, sessionisation, cohort tables.
12. *Lab* — **Statistics refresh.** Estimation and CIs, bootstrap, hypothesis tests and power, regression diagnostics, calibration, Bayesian basics; twenty questions aloud.
13. *Theory* — **ML breadth refresh.** Huyen's interview book: your two weakest areas; twenty questions aloud; implement a training loop and a Kalman update from memory.
14. *Write-up* — **Fix the gaps.** Turn mock and recording weaknesses into fixes; rehearse the fixed parts.
15. *Mock* — **Peer mock #1.** Live ML/system-design mock with a peer or platform; capture written feedback.
16. *Lab* — **Coding set 3: dynamic programming, intervals, heaps.** Timed set; log.
17. *Lab* — **SQL set 2 + data-modelling questions.** Twelve more questions; design a star schema for trips, sessions and sensors; explain partitioning and indexing choices.
18. *Theory* — **Company deep dive.** Target teams (maps, ETA, marketplace, logistics, smart-city at large companies and strong regional players): their engineering posts and products; five sharp questions each.
19. *Review* — **Rapid-fire self-check.** Every self-check question from Modules 0–9 as flashcards; mark misses.
20. *Lab* — **Weak-area deep dive.** Re-study misses; re-run one notebook behind a weak answer.
21. *Mock* — **Mock #3: evaluate and roll out a model across cities.** 40-minute design: evaluation and monitoring plan for a forecaster or choice model rolled out to new cities; spatial CV, drift, gates.
22. *Write-up* — **Portfolio final pass.** README, demo, design doc, LinkedIn consistent; every link works; numbers match; résumé tailored per target team.
23. *Mock* — **Peer mock #2.** Second live mock, different interviewer; revise the capstone write-up where it exposed gaps.
24. *Theory* — **Applications and outreach.** Apply to five roles; message three people in the field with the demo; prepare a 30-second pitch and a 3-minute transport story.
25. *Mock* — **Final mock + readiness checklist.** One last full mock; then an honest pass through the readiness checklist; plan the next quarter (keep the algorithms habit, pick one extension).

**Read:** [Chip Huyen: Introduction to Machine Learning Interviews (free book)](https://huyenchip.com/ml-interviews-book/) · [Exponent: ML system design interview guide](https://www.tryexponent.com/blog/machine-learning-system-design-interview-guide) · [alirezadir: ML system design template](https://github.com/alirezadir/machine-learning-interviews/blob/main/src/MLSD/ml-system-design.md) · [Kohavi, Tang & Xu: Trustworthy Online Controlled Experiments (book site)](https://experimentguide.com/) · [Uber: DeepETA, how Uber predicts arrival times](https://www.uber.com/us/en/blog/deepeta-how-uber-predicts-arrival-times/) · [Hello Interview: Proximity search deep dive](https://www.hellointerview.com/learn/system-design/deep-dives/proximity-search) · [Hyndman & Athanasopoulos: Forecasting, Principles and Practice (free)](https://otexts.com/fpp3/) · [Roberts et al.: Cross-validation strategies for structured data (Ecography 2017)](https://www.wsl.ch/lud/biodiversity_events/papers/Roberts_et_al-2017-Ecography.pdf)

**Watch:** [Mock interview: Design a ranking model (Meta ML engineer)](https://www.youtube.com/watch?v=7_E4wnZGJKo) · [interviewing.io: YouTube recommendation system design mock (replay)](https://interviewing.io/mocks/google-system-design-youtube-recommendation-system)

**Look at:** [NeetCode roadmap (algorithms practice)](https://neetcode.io/roadmap) · [StrataScratch: SQL and data-science interview questions](https://www.stratascratch.com/) · [Evidently (drift reports & tests)](https://github.com/evidentlyai/evidently)

**Recommendations**
- One structure for every design question: clarify → requirements and budgets → data → baseline → model → evaluation (spatially and temporally honest) → deployment → monitoring. Always name the rejected alternative with a number.
- Algorithms are a habit, not a module: if you kept two problems a week since Module 3 you have ~90 done; this module adds timed sets, not first contact.
- Lead with transport stories in behavioural rounds: the OD-identifiability experiment, the causal evaluation that overturned a claim, the calibration trade-off.
- Record everything and watch at 1.5×. You will fix more in one watch-back than in three rehearsals.

**Self-check before moving on**
- [ ] Can you derive logit, explain IIA and compute an elasticity on a whiteboard in five minutes?
- [ ] Can you design an ETA or demand-forecasting system with budgets, baselines and a monitoring plan in 40 minutes?
- [ ] Can you explain switchback experiments and SRM checks to a product manager?
- [ ] Can you solve a medium graph or two-pointer problem in 25 minutes while talking?
- [ ] Do all six STAR stories end in a number?

---

## Candidate Readiness Checklist — Transport Data Scientist / Mobility ML

**Spatial & data foundations**
- [ ] Can justify an H3 resolution and a CRS for a given analysis; writes PostGIS/DuckDB spatial SQL from memory
- [ ] Can explain the biases of counts, FCD and mobile data and how each distorts a congestion or demand estimate
- [ ] Has a tested Visum ↔ Python bridge and has shipped a reproducible change to a production model through it

**Spatial statistics & evaluation**
- [ ] Can derive on a whiteboard why random K-fold leaks on spatial and temporal data; has a measured random-vs-blocked gap
- [ ] Reads a LISA map and a GWR coefficient map correctly; knows MAUP
- [ ] Defaults to per-horizon, per-segment-class, per-district evaluation with intervals

**Demand modelling**
- [ ] Derives MNL from random utility, explains IIA, estimates nested logit, computes elasticities and value of time
- [ ] Has compared logit, GBM and a neural choice model on prediction *and* economic sensibility
- [ ] Can explain why OD estimation from counts is under-determined and show numerically what FCD or partial OD adds
- [ ] States Wardrop's principles and what Frank–Wolfe iterates on; has matched Visum and AequilibraE assignments within a GEH tolerance

**Traffic flow, forecasting & simulation**
- [ ] Explains HMM map matching; derives q = k·v and the fundamental diagram; has computed an MFD from real trajectories
- [ ] Has a forecasting benchmark where seasonal naive, LightGBM and an ST-GNN are compared per horizon with coverage of prediction intervals
- [ ] Has calibrated a simulator against several observation types with a stated trade-off, and knows which parameters matter (Sobol)
- [ ] Can set up a DiD or synthetic-control evaluation of an intervention, test pre-trends and report an interval

**Experimentation & production (big-tech rounds)**
- [ ] Explains interference, switchback designs, SRM and guardrail metrics to a PM
- [ ] Can design an ETA or demand-forecasting system in 40 minutes with budgets, baselines, evaluation and monitoring
- [ ] Solves medium algorithm problems in 25 minutes aloud; handles window-function SQL and a star-schema design question
- [ ] Has a deployed demo, a design doc with rejected alternatives and numbers, and six STAR stories that end in a number

---

### How to use this document
Work top to bottom. Modules 3, 4, 6 and 7 are the ones that pay off at work in year one and in interviews later; protect them. Module 8 can shrink to its first four sessions if time is short. Keep `docs/numbers.md` current from Module 3; the capstone and the interview module are built on it. Start the algorithms habit in Module 3, not in Module 10.