# Geo Search Senior Data Scientist Roadmap
### A production-oriented, 6–12 month path from GIS/DS generalist → Senior DS, Geo Search

This roadmap is built around one assumption: the interview panel doesn't want someone who "knows GeoPandas." They want someone who has already made the architectural decisions this role requires — how to turn 200M noisy ride sessions into unbiased ranking labels, how to keep a query-understanding model under a 50ms keystroke budget, and how to decide, per query, whether to trust your own index or fall back to Google/HERE. Every module below is built to produce evidence of exactly that.

**Time budget assumption:** 10–15 hrs/week. Modules 1–4 are foundational and can compress if you already know GIS. Modules 5–9 are where the job actually lives — do not rush them.

---

## Module 0 — Environment & Mental Model (Week 1)

**Theoretical Foundation**
- The "three worlds" of geo search: (1) the **index world** — how places/POIs are stored and made searchable, (2) the **query world** — how a noisy human keystroke becomes a structured intent, (3) the **ranking world** — how you order candidates once retrieved. Almost every module maps to one of these three.
- Coordinate reference systems: WGS84 (EPSG:4326, lat/lon, what GPS gives you) vs. Web Mercator (EPSG:3857, what you render) vs. local projected CRS (for true distance/area math). Never compute distance in raw lat/lon degrees.
- Great-circle distance (Haversine, Vincenty) vs. projected Euclidean distance vs. **road-network distance/ETA** — and why ranking on Haversine alone fails badly in cities with rivers, highways, or one-way systems (a classic "why is the nearest driver 8 minutes away" bug).

**Concrete Tech Stack**
- Python env: `conda`/`uv`, `geopandas`, `shapely>=2.0`, `pyproj`, `h3`, `s2sphere`, `osmnx`, `folium`/`kepler.gl`, `duckdb` + `duckdb-spatial` (fast local geo SQL, no server needed).
- Docker Compose stack you'll reuse for the whole roadmap: `postgres+postgis`, `opensearch` + `opensearch-dashboards`, `redis` (for hot geo cache), `minio` (S3-compatible for Overture/OSM extracts).

**Hands-on Production Project**
- Stand up the full local stack via `docker-compose.yml`. Load an Overture Maps `places` extract for one city into PostGIS **and** OpenSearch simultaneously. Write a script that queries both for "restaurants within 2km of point X" and asserts result parity. This becomes your dev sandbox for every later module.

---

## Module 1 — Spatial Indexing & the Geospatial Core Stack (Weeks 2–4)

**Theoretical Foundation**
- Why lat/lon pairs are a bad index key: no locality, expensive range queries, can't do "nearby" cheaply on a B-tree.
- Space-filling curves & hierarchical grids: **Geohash** (base-32, quadtree, has the "edge/boundary" problem where nearby points hash very differently), **S2** (Google, spherical hierarchical, Hilbert-curve-based cells, true spherical geometry, used by MongoDB/Cloud Spanner), **Uber H3** (hexagonal, uniform adjacency — no "corner" neighbor ambiguity like a square grid has, 16 resolutions, designed explicitly for ride-hailing supply/demand indexing — this is Uber's own paper, know it cold).
- R-trees / R*-trees (bounding-box hierarchical index — what PostGIS `GIST` indexes and Shapely's `STRtree` actually use under the hood) vs. grid indexes: R-trees are better for irregular polygons, grids are better for uniform density aggregation (surge pricing, ETA heatmaps).
- KD-trees and Ball-trees for exact/approximate nearest-neighbor (`sklearn.neighbors.BallTree` with haversine metric) vs. approximate NN (HNSW/FAISS) for embedding-based candidate generation later.

**Concrete Tech Stack & Libraries**
- **H3**: `h3.latlng_to_cell`, `h3.cell_to_latlng`, `h3.grid_disk` (k-ring), `h3.grid_ring`, `h3.cell_to_boundary`, `h3.compact_cells`/`uncompact_cells`, `h3.cell_to_parent`/`cell_to_children` (resolution hierarchy), `h3.grid_distance`. Know how to pick resolution (res 7 ≈ 5.16 km² avg hex, res 9 ≈ 0.1 km² — map resolution choice to "neighborhood-level demand" vs. "street-level ETA").
- **S2**: `s2sphere.CellId.from_lat_lng`, `S2RegionCoverer` for polygon-to-cell covering (used for geofencing service areas).
- **PostGIS/SpatiaLite**: `ST_DWithin`, `ST_Intersects`, `ST_Contains`, `ST_Buffer`, `ST_Distance` (spheroid vs. planar), `ST_ClusterDBSCAN`, `GIST` index, `KNN <->` operator for nearest-neighbor search.
- **GeoPandas/Shapely**: `gpd.sjoin`/`sjoin_nearest`, `shapely.STRtree`, `unary_union`, `.buffer()`, `.simplify()` (Douglas-Peucker, critical for reducing polygon complexity before serving).
- **PySAL**: `esda.Moran` (spatial autocorrelation — you'll use this in Module 5 to detect systematic geographic bias in labels), `libpysal.weights` (spatial weight matrices, KNN/Queen/Rook contiguity).
- **OSMnx**: `ox.graph_from_place`, `ox.distance.nearest_nodes`, `ox.shortest_path` (networkx Dijkstra/A* under the hood) — your free substitute for a commercial road-network/ETA engine.

**Hands-on Production Project**
"Demand-Supply Heatmap & Nearest-Driver Engine" — Ingest NYC TLC trip data, bucket pickups into H3 res-8 cells, build a rolling 15-min demand surface. Separately build a driver-simulation layer and implement three "nearest driver" strategies: (a) Haversine + BallTree, (b) H3 `grid_disk` expanding-ring search, (c) OSMnx road-network shortest-path ETA. Benchmark latency and accuracy of all three at increasing driver density — this is the exact trade-off analysis a Geo Search interviewer will probe ("when do you use a spatial index vs. a real routing call?").

**Open Datasets:** NYC TLC Trip Record Data (pickup/dropoff lat-lon), Overture Maps `places` + `divisions` themes, OpenStreetMap extracts (Geofabrik), Porto Taxi Trajectory dataset (ECML/PKDD 2015, GPS traces).

---

## Module 2 — Search Engine Internals: OpenSearch/Elasticsearch for Geo (Weeks 4–6)

**Theoretical Foundation**
- Inverted index fundamentals: terms → postings lists, TF-IDF and **BM25** scoring (know the formula and its `k1`/`b` parameters — you will be asked to explain why BM25 beats raw TF-IDF for short place-name queries).
- Geo field types: `geo_point` (lat/lon, indexed via a **geohash-based prefix tree / BKD-tree** in Lucene) vs. `geo_shape` (for polygons — service areas, neighborhoods, admin boundaries).
- Compound scoring: `function_score` query, combining text relevance with a **distance decay function** (`gauss`/`exp`/`linear` decay) — this is literally how you blend "textual match" with "how close is it" before any ML ranker touches the results.
- Custom analyzers for place-name search: `edge_ngram` tokenizer (for prefix/autocomplete), `ICU analyzer`/`icu_folding` (for cross-script normalization — Arabic diacritics, Cyrillic, CJK), `phonetic` token filter (Soundex/Metaphone/Beider-Morse — critical for transliterated names like "Al-Qahira" vs "Cairo" vs "القاهرة").
- Fuzzy matching: Damerau-Levenshtein edit distance, `fuzziness: AUTO`, and why naive edit-distance fuzziness breaks for short strings (a 1-character typo on a 4-letter place name changes meaning entirely) — you need length-aware fuzziness tuning.

**Concrete Tech Stack**
- `opensearch-py` client, index mapping design (`geo_point`, `geo_shape`, `search_as_you_type` field type, `completion` suggester with fuzzy support).
- Custom analyzer chain: `char_filter` (strip diacritics) → `tokenizer` (`edge_ngram`, min_gram 2 max_gram 15) → `token_filter` (`icu_folding`, `asciifolding`, synonym filter for common abbreviations "St." → "Street").
- `geo_distance` query/sort, `geo_bounding_box`, `function_score` with `gauss` decay on `geo_point`.
- Relevance tuning workflow: **Ranking Evaluation API** (`_rank_eval`) to score query sets against a judgment list — this is your offline harness precursor for Module 7.

**Hands-on Production Project**
"Cross-Script Place Autocomplete Engine" — Build an OpenSearch index of ~500K POIs (Overture Places, multi-country) with a custom analyzer pipeline supporting Latin + Arabic + Arabizi (Arabic written in Latin letters, e.g. "ma3adi" for "المعادي"/Maadi). Implement a `function_score` query blending BM25 text relevance with a distance-decay geo signal, tuned via `_rank_eval` against a judgment list you hand-label. Deliverable: p50/p95 query latency report + relevance report (NDCG@5) before/after custom analyzer tuning.

**Open Datasets:** Overture Maps Places (multilingual names field is ideal for this), GeoNames (alternate names table — literally built for cross-script/transliteration testing), Arabizi transliteration corpora (e.g., research corpora from CALIMA/MADAMIRA/Arabic-Arabizi parallel datasets).

---

## Module 3 — Query Understanding: Cleaning, Typos, Cross-Script Matching (Weeks 6–9)

**Theoretical Foundation**
- Query understanding pipeline as a cascade: normalization → language/script detection → tokenization → intent classification (place-name search vs. category search vs. address) → entity extraction (street, city, landmark, house number) → transliteration/translation.
- Typo tolerance beyond edit distance: **keyboard-adjacency-aware** edit costs (a "typo" swapping adjacent QWERTY keys should cost less than a random substitution), phonetic algorithms (Soundex, Double Metaphone, and for Arabic specifically, **Buckwalter transliteration** as a canonical intermediate representation).
- Cross-script matching as a retrieval problem, not just a string-matching one: transliteration is many-to-many (one Arabic name → multiple valid Latin spellings), so exact matching fails — you need either (a) a canonicalization/normalization layer, or (b) an embedding-based fuzzy match.
- Address parsing as sequence labeling (BIO tagging: house_number, street, city, postal_code) — this is a **NER problem**, not a regex problem, in messy/informal-address markets.

**Concrete Tech Stack**
- `rapidfuzz` (fast Levenshtein/Jaro-Winkler, `process.extract` for top-k fuzzy candidates), `jellyfish` (Soundex, Metaphone, NYSIIS), `python-Levenshtein`.
- `polyglot`/`langdetect`/`fasttext` `lid.176` model for language identification per query.
- `pyicu` / `unicodedata` normalization (NFKD/NFKC) for diacritic stripping.
- Transliteration: `camel-tools` (CAMeL Lab's Arabic NLP toolkit — Buckwalter transliteration, Arabic normalization, dialect ID — this is the field-standard library, know its `CharMapper`, `dediac_ar`, `normalize_alef_ar`).
- Address parsing: `libpostal` (the open-source global address parser trained on OpenAddresses/OSM — this is what most industry geocoders bootstrap from) via `pypostal` bindings; alternatively fine-tune a lightweight token-classification model (`bert-base-multilingual-cased` fine-tuned as a BIO tagger via `transformers` `AutoModelForTokenClassification`).
- Query rewriting: synonym/abbreviation dictionaries, learned query-to-query embedding similarity (build with `sentence-transformers`, e.g. `paraphrase-multilingual-MiniLM-L12-v2`) for "did you mean" and query expansion.

**Hands-on Production Project**
"Query Understanding Microservice" — FastAPI service that takes a raw keystroke-level query string and outputs: detected language/script, normalized/transliterated form, parsed address components (BIO tags), and top-5 fuzzy-matched canonical place candidates with confidence scores. Test set: deliberately noisy queries (typos, mixed Arabic/Arabizi/English, missing diacritics, informal landmarks like "next to the blue mosque"). Report precision@1 and MRR against a hand-labeled gold set, broken out by script/language — this per-segment error breakdown is exactly the "error analysis" muscle the JD calls out.

**Open Datasets:** OpenAddresses, libpostal's training corpus (OSM + OpenAddresses), GeoNames alternate-names, CoNLL-style NER sets adapted for address entities, QALB (Qatar Arabic Learners' Corpus, for Arabic typo/correction patterns), synthetic Arabizi generation (rule-based, you'll build a small generator — this itself is a good interview talking point on synthetic data for low-resource cross-script problems).

---

## Module 4 — LLM Distillation Under Strict Latency Budgets (Weeks 9–11)

**Theoretical Foundation**
- The core tension the JD names explicitly: LLMs give you high-quality *offline* labels/judgments but are far too slow (100ms–2s+) for the **<50ms keystroke-path** online serving budget. The pattern is always: **LLM as offline teacher/labeler → small fast model as online student.**
- Knowledge distillation theory: soft-label matching via KL divergence between teacher and student output distributions (temperature-scaled softmax), combined with a hard-label cross-entropy term — the classic Hinton et al. distillation loss: `L = α·CE(y_true, student) + (1-α)·T²·KL(softmax(teacher/T), softmax(student/T))`.
- Model compression paths: **architecture distillation** (BERT → DistilBERT/TinyBERT/MiniLM-style smaller transformer), **task-specific distillation** (LLM zero/few-shot labels → simple classifier: FastText/logistic regression/small MLP on embeddings, or gradient-boosted trees on engineered features), and **quantization** (FP32 → INT8 via `onnxruntime` quantization, post-training or quantization-aware).
- Latency budget accounting: for a 50ms keystroke path you typically can't even afford a transformer forward pass on CPU at scale — the realistic pattern is precomputed embeddings (via an offline transformer) + an online **approximate nearest-neighbor lookup** (FAISS/HNSW) or a tiny (few-KB) FastText/n-gram model, not a live transformer call.

**Concrete Tech Stack**
- Teacher labeling: batch offline calls to a large LLM (via Anthropic/OpenAI API or a self-hosted open model) with structured-output prompting to produce query→intent, query→canonical-place, or relevance judgments at scale — log everything to a labeled dataset.
- Student models: `fasttext` (subword n-gram embeddings, near-instant CPU inference, genuinely used in production autocomplete systems), `sentence-transformers` distillation utilities, `transformers.Trainer` with a custom `DistillationTrainer` (override `compute_loss` for the KD loss above), TinyBERT/MiniLM checkpoints as distillation targets.
- Serving-side compression: `onnx`/`onnxruntime` (`onnxruntime.quantization.quantize_dynamic`), `optimum` (HuggingFace's ONNX/quantization toolkit), benchmark with `onnxruntime`'s CPU execution provider under realistic QPS.
- ANN for embedding-based candidate generation: `faiss` (`IndexHNSWFlat`, `IndexIVFPQ` for compressed vectors at scale), or `hnswlib` directly for a lighter dependency footprint.

**Hands-on Production Project**
"Distilled Query-Intent Classifier at 10ms p99" — Use an LLM to label 20–50K real/synthetic queries with intent classes (address / POI-name / category / landmark-relative) and extracted entities. Train three student candidates: (1) FastText classifier, (2) distilled MiniLM via KD loss, (3) GBM on hand-engineered + embedding features. Quantize the transformer student to INT8 via ONNX. Load-test all three with `locust`/`wrk` for p50/p95/p99 latency on CPU, and report the accuracy-vs-latency Pareto frontier — explicitly recommend which one ships to the <50ms keystroke path and which is reserved for slower downstream re-ranking. This accuracy/latency trade-off table is the single most senior-signal artifact in this whole roadmap.

**Open Datasets:** MS MARCO / Amazon ESCI query sets adapted for intent-labeling practice, your own Module 3 query corpus re-used, CLINC150 or Banking77 as generic intent-classification distillation practice sets before you apply the technique to geo queries.

---

## Module 5 — Data Engineering & Labeling: From Logs to Trustworthy Ranking Labels (Weeks 11–15)

**This is the module the JD weights heaviest ("build the label pipeline... correcting position bias & presentation effects") — treat it as the centerpiece of your portfolio.**

**Theoretical Foundation**
- The core problem: a click or a completed ride is **not** a ground-truth relevance label. It's confounded by (a) **position bias** (top results get clicked more regardless of relevance — examine hypothesis: `P(click) = P(examine|position) × P(relevance|query,doc)`), (b) **presentation bias** (bold text, photo thumbnails, "verified" badges change click-through independent of true relevance), (c) **selection bias** (you only observe outcomes for items you chose to show).
- Click models: **Position-Based Model (PBM)** and **Cascade Model** (user examines results top-to-bottom, stops at first click) and **Dynamic Bayesian Network (DBN)** model — know how each factorizes examination probability from relevance probability, and when cascade assumptions break for map/grid UIs (geo search results are often shown on a map, not a list — classic list-based cascade assumptions don't hold, and you need a 2D/spatial examination model instead).
- Bias correction techniques: **Inverse Propensity Scoring (IPS)** — reweight each observed click by `1/P(examine|position)` to get an unbiased relevance estimate; **counterfactual learning-to-rank** (Joachims et al.) trains directly on IPS-weighted pairs; **result randomization / intervention harvesting** (periodically inject randomized result order to directly measure position-effect propensities — the RandTop-n / RandPair method) is how you *estimate* the propensity curve in the first place rather than assuming one.
- Implicit signal hierarchy for ride-hailing specifically: impression → tap/click → address confirmed → ride requested → ride completed → (optionally) rating. Each transition is a different "relevance signal" with different noise; a completed ride is a much stronger positive label than a tap, but it's rarer and slower to arrive (label latency vs. label quality trade-off — discuss this explicitly with interviewers).
- Negative sampling strategy: naive "everything not clicked is negative" is wrong at scale (most non-clicks are just unexamined) — use examined-but-not-clicked as hard negatives, and random/popularity-based sampling for easy negatives, mirroring the two-negative-type approach used in industrial LTR/retrieval systems (cf. how DPR/ANCE style retrieval training samples negatives).

**Concrete Tech Stack**
- Pipeline orchestration: `Apache Airflow` or `Dagster` DAGs (session reconstruction job → propensity estimation job → label materialization job → feature-store write).
- Session reconstruction: `pandas`/`polars` or `PySpark` for large-scale session windowing (group raw event logs into sessions by user_id + time-gap threshold), sessionization logic with `pyspark.sql.Window`.
- Feature store pattern: `Feast` (open-source feature store) to serve consistent point-in-time-correct features to both training and serving — critical to avoid **training/serving skew**, which you should be ready to discuss as a named failure mode.
- Bias diagnostics: implement PBM examination-probability estimation from a randomized-interleaving experiment (simulate this since you won't have live traffic — inject synthetic position randomization into your NYC TLC-derived "sessions"), plot click-through-rate by position to visually demonstrate position bias, then show the corrected vs. uncorrected label distributions.
- Data quality: `great_expectations` for label-pipeline data contracts (schema, null-rate, distribution drift checks on the labels themselves).

**Hands-on Production Project**
"Unbiased Ranking-Label Pipeline from Synthetic Ride Sessions" — Simulate a realistic session log from NYC TLC data + a synthetic search-results-shown log (impressions with position, simulated clicks with an injected position-bias function you control so you have ground truth to validate against). Build an Airflow DAG: raw events → sessionization → **IPS-based label correction** → feature-store-ready training table. Deliverable: a report showing (a) the raw click-position curve, (b) your recovered propensity curve from randomized-position experiments, (c) NDCG of a ranker trained on naive labels vs. IPS-corrected labels, measured against your known ground-truth relevance (since it's synthetic, you can prove correction actually helps — this is the single most compelling proof-of-competence artifact for this role).

**Open Datasets:** NYC TLC Trip Data (base sessions), Yandex Personalized Web Search Click Log (a real, large, industrial-scale click-log dataset with position info — the closest public analogue to what you'd get internally), Microsoft's `MSLR-WEB10K`/`WEB30K` (pre-built LTR feature+label sets for practicing the correction techniques before applying to your own pipeline), Criteo's counterfactual/off-policy datasets if available for IPS practice.

---

## Module 6 — Learning to Rank & Geo Relevance (Weeks 15–19)

**Theoretical Foundation**
- LTR problem framing: **pointwise** (regression/classification on individual relevance) vs. **pairwise** (learn to order pairs correctly — RankNet-style) vs. **listwise** (optimize a ranking metric directly over the whole result list — LambdaMART/LambdaRank, ListNet, YetiRank).
- **LambdaMART** deep-dive: it's gradient-boosted trees where the gradient ("lambda") for each pair is the RankNet pairwise gradient *scaled* by the change in NDCG if that pair were swapped (`|ΔNDCG|`) — this is why LambdaMART directly optimizes a ranking metric despite using a pairwise loss under the hood. Be able to derive/explain this on a whiteboard.
- Evaluation metrics and their failure modes: **NDCG@k** (handles graded relevance, position-discounted — know the DCG formula `Σ (2^rel_i - 1)/log2(i+1)` and why the `2^rel-1` gain function matters for highly-relevant items), **MRR** (only cares about the first relevant result — good for navigational/single-answer queries like "take me to my exact address"), **Hit@k**/**Recall@k** (candidate-generation-stage metric, before fine ranking).
- Two-stage retrieval-then-rank architecture (matches how virtually every large-scale search/rec system is built): cheap **candidate generation** (geo radius filter + BM25/ANN) narrows millions of POIs to ~100–1000, then an **expensive ranker** (GBDT or learned model) reorders the top candidates using rich features.
- Spatial + behavioral feature engineering for the ranker: distance-decay features (multiple bandwidths), H3-cell historical demand/popularity, time-of-day/day-of-week seasonality, query-place text-match scores (BM25 score as a *feature*, not just a filter), user-specific history (frequent destinations, home/work inferred locations), real-time supply signals (driver density nearby), POI quality signals (completeness of address, verification status).
- Position/exploration trade-off at serving time: pure exploitation (always show gbdt's top-1) starves the label pipeline of exploration data — tie this back to Module 5 by discussing epsilon-greedy or Thompson-sampling-style controlled exploration in the serving layer.

**Concrete Tech Stack**
- `LightGBM`: `objective='lambdarank'` and `objective='rank_xendcg'`, `label_gain`, `group` parameter for query grouping, `lgb.train` with `eval_metric='ndcg'`.
- `XGBoost`: `objective='rank:pairwise'`, `'rank:ndcg'`, `'rank:map'`, `DMatrix` with `set_group()`.
- `CatBoost`: `YetiRank`/`YetiRankPairwise` loss (CatBoost's listwise objective, often strong out-of-the-box), native categorical feature handling (useful for city/country/POI-category features without manual encoding).
- Feature engineering: `featuretools` or hand-rolled feature pipelines joined against your Module 5 feature store; SHAP (`shap.TreeExplainer`) for ranker feature-importance and per-query explainability (you will be asked "why did result X rank above Y" in an interview — be ready to answer with SHAP).
- Two-stage serving stub: candidate generation via OpenSearch (Module 2) + FAISS (Module 4) → feature join → LightGBM `predict()` re-rank, wrapped in a FastAPI endpoint with a p99 latency budget you explicitly measure.

**Hands-on Production Project**
"End-to-End Geo LTR System" — Using your Module 5 labeled sessions, engineer 25–40 ranking features (spatial, textual, behavioral, temporal). Train and compare LightGBM `lambdarank`, XGBoost `rank:pairwise`, and CatBoost `YetiRank` on the same feature set; report NDCG@5, NDCG@10, MRR, and Hit@3 for each. Run a SHAP analysis to explain the top-3 features driving ranking decisions. Wire the trained model into a FastAPI two-stage retrieval-then-rank service (candidate gen from Module 2's OpenSearch index → GBDT re-rank) with measured end-to-end p50/p95 latency.

**Open Datasets:** `MSLR-WEB10K`/`WEB30K` (canonical public LTR benchmark — do a first pass here before your own data to sanity-check your LightGBM/XGBoost/CatBoost pipeline against known baselines), Amazon **ESCI** (Shopping Queries Dataset — real e-commerce search-relevance judgments, structurally very close to a geo-search relevance-judgment set), your own Module 5 synthetic-session output, Yelp Open Dataset (business attributes + reviews, good source of "POI quality" features).

---

## Module 7 — Evaluation: Offline Replay Harness & Error Analysis (Weeks 19–22)

**Theoretical Foundation**
- **Offline replay evaluation**: instead of only computing NDCG on a static labeled test set, replay *recorded real sessions* through your new model and check whether it would have surfaced the place the user actually completed a ride to (counterfactual scoring). This directly mirrors the JD's "offline replay harness scoring recorded sessions against real rides."
- Counterfactual evaluation caveat: replaying a new ranker against logs collected under an *old* ranker's policy is itself subject to the same position/selection bias as Module 5 — you generally need **off-policy evaluation** techniques (IPS-weighted replay, or a doubly-robust estimator) to get an unbiased estimate of a new policy's performance from old logs, not naive replay.
- Error analysis taxonomy for search/ranking systems: **retrieval failures** (correct answer never made it into the candidate set — a Recall@k problem, fixed by better candidate generation/indexing) vs. **ranking failures** (correct answer was retrieved but ranked too low — a ranker/feature problem) vs. **query-understanding failures** (query was mis-parsed/mis-transliterated before search even ran) vs. **label-noise-induced failures**. Always slice failures this way before proposing a fix — this diagnostic discipline is a strong senior-level signal.
- Segmented evaluation: never report a single aggregate metric. Slice by geography (market maturity — the JD explicitly cares about "countries where maps are wrong/missing"), query language/script, query length, new vs. returning user, time-of-day. A model that's +5% NDCG overall but -10% in your lowest-map-quality markets is a regression, not a win, for this role specifically.

**Concrete Tech Stack**
- Build a `ReplayHarness` class: given a historical session (query, shown-results, ground-truth completed-ride place) and a candidate new model, recompute rankings and score NDCG/MRR/Hit@k "as if" the new model had served that session — implemented in `pandas`/`polars` with vectorized batch scoring for speed.
- Off-policy evaluation: implement IPS-weighted and self-normalized IPS (SNIPS) estimators; optionally a simple doubly-robust estimator combining a direct-reward model with IPS correction.
- Error taxonomy tooling: automatic classification of each failed session into retrieval/ranking/query-understanding buckets via rule-based diagnostics (was gold item in candidate set at all? at what raw rank pre-model?).
- Dashboarding: `streamlit` or `Plotly Dash` app for slicing error rate and NDCG by market/language/segment — build this as a reusable internal tool, not a one-off notebook, and say so explicitly in your portfolio write-up.

**Hands-on Production Project**
"Replay Harness + Segmented Error Analysis Report" — Build the `ReplayHarness` over your Module 6 model and Module 5 session data. Compute off-policy-corrected performance estimates (IPS/SNIPS) vs. naive replay, and quantify how much naive replay over/understates true performance. Produce a segmented error-analysis report (by simulated "market maturity" tier and by query script/language from Module 3) identifying the top 3 failure categories per segment, each with a proposed fix mapped back to a specific earlier module (e.g., "Arabizi query failures are query-understanding failures → revisit Module 3 transliteration coverage").

**Open Datasets:** Continue using your accumulated synthetic pipeline (this module is inherently about *your own system's* logs); for off-policy-evaluation method validation specifically, the Criteo/Open Bandit Pipeline (OBP) datasets are purpose-built public benchmarks for testing IPS/SNIPS/doubly-robust estimators before trusting them on your own data.

---

## Module 8 — Online Experimentation & Confidence/Fallback Modeling (Weeks 22–25)

**Theoretical Foundation**
- A/B testing fundamentals for spatial features specifically: **network/spatial interference** — ride-hailing experiments violate the standard SUTVA (Stable Unit Treatment Value Assumption) because treating drivers/riders in one geographic cell affects supply available to neighboring cells. Standard user-level randomization can be badly biased; you need **geo-based (switchback or cluster) randomization** — randomize treatment by H3 cell or by city, rotate treatment over time windows (switchback design), and this is a very well-known ride-hailing-specific experimentation pattern worth naming explicitly in an interview.
- Statistical power and sample-ratio-mismatch (SRM) checks — an SRM alert is often the *first* sign that a geo-randomized experiment is broken (e.g., routing logic accidentally correlated with the randomization key).
- Sequential testing / always-valid p-values (mSPRT, group-sequential designs) for shipping decisions faster than a fixed-horizon test would allow, relevant for a "keep models healthy post-launch" cadence.
- **Confidence modeling for fallback logic** — this is a distinct, JD-named responsibility: train a secondary model whose job is *not* "what's the best result" but "should I trust my own top result at all, or fall back to an external provider?" Frame it as calibration + out-of-distribution detection: (a) **probability calibration** of your ranker's top-score (Platt scaling / isotonic regression via `sklearn.calibration.CalibratedClassifierCV`) so a "0.9 confidence" genuinely means ~90% of such cases are correct, (b) an auxiliary "coverage" classifier trained on meta-features (candidate-set size, top-score margin over 2nd place, map data completeness in that H3 cell, query-understanding confidence from Module 4) predicting P(top result is correct) directly, (c) threshold selection via precision-recall trade-off curve — you're choosing an operating point that trades "own-answer coverage" against "own-answer error rate," which is a business decision you should be able to frame in cost terms (cost of wrong own-answer vs. cost/latency of external-provider fallback call).

**Concrete Tech Stack**
- Experiment design: geo-cluster/switchback randomization implemented over your H3 grid from Module 1; power analysis via `statsmodels.stats.power`.
- SRM detection: chi-square goodness-of-fit test on treatment/control allocation counts.
- Calibration: `sklearn.calibration.calibration_curve`, `CalibratedClassifierCV` (`method='isotonic'` vs `'sigmoid'`), reliability diagrams.
- Fallback classifier: a small LightGBM/logistic-regression binary classifier on meta-features producing P(trust own top result); evaluate via **precision-recall curve** and **ROC-AUC**, and explicitly select an operating threshold tied to a stated cost ratio.
- Sequential testing: `mSPRT` reference implementations or a from-scratch implementation to demonstrate you understand the mechanics, not just the library call.

**Hands-on Production Project**
"Switchback Experiment Simulator + Fallback Confidence Model" — (1) Simulate a switchback/geo-cluster A/B test over your H3 grid comparing Module 6's baseline ranker vs. an improved variant, including a deliberately injected spatial-interference effect, and show how naive user-level randomization would have mis-measured the effect versus correctly-designed switchback randomization. (2) Train the fallback-confidence classifier described above on your Module 7 error-taxonomy output (label = "was own top-1 actually correct") and produce the precision-recall operating-point analysis with a stated cost-ratio justification for your chosen threshold.

**Open Datasets:** No single "ride-hailing experiment" public dataset exists at this granularity — this module is necessarily simulation-heavy; ground the simulation parameters (effect sizes, spatial-spillover magnitude) in published ride-hailing experimentation literature (Lyft/Uber/DiDi engineering blogs on switchback testing are the standard references — read them, cite the design pattern, build your own simulator rather than searching for a dataset that doesn't exist).

---

## Module 9 — Capstone: Integrated Geo Search System (Weeks 25–30, flex to week 36+ for the 12-month track)

**Goal:** stitch Modules 1–8 into one coherent, demo-able, architecturally-documented system — this is what actually goes on your resume/portfolio site and what you walk an interviewer through live.

**Architecture to build and diagram (system-design style, know every arrow):**
```
[Client keystroke]
   → Query Understanding svc (Module 3/4: normalize, transliterate, intent-classify — <50ms)
   → Candidate Generation (Module 1/2: H3 geo-filter + OpenSearch BM25/geo_distance + FAISS ANN)
   → Feature Join (Module 5/6: feature-store lookup — spatial, behavioral, textual, real-time supply)
   → LTR Re-rank (Module 6: LightGBM/CatBoost, p95 budget measured)
   → Confidence/Fallback Gate (Module 8: serve own top-k vs. call external provider)
   → Response
        ⇣ (async)
   Logging → Session reconstruction → Label pipeline (Module 5) → Replay harness (Module 7)
        → Offline eval → Switchback online experiment (Module 8) → Model registry → redeploy
```
- Write this up as a formal design doc (problem statement, requirements incl. latency/SLA budgets per stage, alternatives considered and rejected, metrics for success) — this document *is* the interview artifact; many senior interviews are structured around walking through exactly this kind of doc.
- Add basic MLOps: model registry (`MLflow`), a `Makefile`/CI pipeline that retrains and validates against a minimum-NDCG gate before "deployment," and a monitoring stub for **feature drift** (`evidently` or hand-rolled PSI/KL-divergence checks on key spatial/behavioral features) — ties directly to "keep models healthy post-launch as data and cities shift."
- Deploy at least the query-understanding + candidate-gen + rank path as a live, load-tested API (containerized, `docker`, optionally a minimal `k8s` manifest) with a public demo (even a small map UI via `folium`/a lightweight React+Mapbox frontend) — a working demo link is disproportionately persuasive versus a notebook.

**Open Datasets for the capstone:** combine everything above — Overture Maps (index), NYC TLC + your synthetic session generator (behavior/labels), MSLR/ESCI (LTR sanity baseline), GeoNames + CAMeL Tools corpora (cross-script). Pick 2–3 real cities with genuinely poor OSM/Overture coverage (rural India, parts of Sub-Saharan Africa, or informal-settlement areas are well-documented as low-map-quality regions) to make your "developing markets" story concrete and specific rather than generic — the JD explicitly names this.

---

## Module 10 — Interview & System-Design Readiness (Weeks 30–34, ongoing)

**Theoretical Foundation / Practice**
- Rehearse explaining, from memory and on a whiteboard: (1) the IPS position-bias correction derivation, (2) the LambdaMART gradient intuition, (3) NDCG vs. MRR vs. Hit@k — when each is the *wrong* metric to optimize, (4) switchback experimentation for spatial interference, (5) the distillation loss and why <50ms rules out a live transformer call.
- Practice **live system design** for prompts like: "Design geo search for a country where 40% of addresses aren't in any map provider," "Design the confidence model deciding own-answer vs. fallback," "Design an evaluation harness that wouldn't have missed a regression only visible in low-connectivity markets." Time-box yourself to 35–40 minutes each, out loud.
- Mock case-study walkthroughs of your Module 9 capstone doc with a peer or on video — optimize for "what trade-off did you consider and reject, and why," since that's what distinguishes senior from mid-level answers.

**Hands-on Production Project**
Record yourself presenting the Module 9 architecture doc end-to-end in under 15 minutes, then do 3+ mock system-design interviews (peers, Pramp-style platforms, or self-recorded) on the prompts above, and revise the capstone write-up based on the gaps that surface.

---

## Consolidated Open Dataset Reference

| Dataset | Use For |
|---|---|
| NYC TLC Trip Record Data | Sessions, demand surfaces, ETA/routing baselines |
| Overture Maps (`places`, `divisions`, `transportation`) | POI index, multilingual names, road network |
| OpenStreetMap extracts (Geofabrik) | Road graphs (OSMnx), low-map-quality region case studies |
| GeoNames (incl. alternate names table) | Cross-script/transliteration testing, gazetteer |
| OpenAddresses | Address parsing training data (libpostal-style) |
| Porto Taxi Trajectories (ECML/PKDD 2015) | GPS trajectory / trip-pattern analysis |
| MSLR-WEB10K / WEB30K | Canonical LTR benchmark, sanity-check LambdaMART/XGBoost/CatBoost pipeline |
| Amazon ESCI (Shopping Queries Dataset) | Real relevance-judgment structure, transferable to geo |
| Yandex Personalized Web Search Click Log | Real click-log with position info, for click-model/IPS practice |
| Yelp Open Dataset | POI quality/attribute features |
| CAMeL Tools corpora / QALB | Arabic NLP, dediacritization, typo/correction patterns |
| Criteo / Open Bandit Pipeline (OBP) | Off-policy evaluation (IPS/SNIPS/doubly-robust) benchmarking |
| CLINC150 / Banking77 | Generic intent-classification distillation practice before geo-specific application |

---

## Candidate Readiness Checklist — Senior DS, Geo Search

**Spatial fundamentals**
- [ ] Can explain H3 vs. S2 vs. Geohash trade-offs and justify a resolution choice for a specific use case (surge heatmap vs. street-level nearest-driver)
- [ ] Can write `ST_DWithin`/`ST_Intersects` PostGIS queries and equivalent OpenSearch `geo_distance`/`function_score` queries from memory
- [ ] Understands why road-network ETA ≠ Haversine distance, and when each is acceptable

**Query understanding**
- [ ] Built and can demo a cross-script (e.g., Arabic/Arabizi/Latin) fuzzy place-matching pipeline
- [ ] Can explain the LLM-teacher → distilled-student pattern and defend a specific student architecture choice against a <50ms budget with measured p99 numbers
- [ ] Has hands-on experience with `libpostal`/CAMeL Tools or equivalent, not just theoretical knowledge

**Labeling & bias**
- [ ] Can derive the position-bias examination-probability model and explain IPS correction on a whiteboard
- [ ] Has built (even synthetically) a pipeline that measurably improves NDCG by correcting biased labels vs. naive labels — with numbers to show
- [ ] Understands cascade vs. PBM vs. DBN click models and their assumption failures for map/grid UIs

**Ranking**
- [ ] Has trained LTR models in LightGBM (`lambdarank`), XGBoost (`rank:pairwise`), and CatBoost (`YetiRank`) and can compare their objectives precisely
- [ ] Can explain the LambdaMART `|ΔNDCG|`-scaled gradient intuition
- [ ] Has built a real two-stage candidate-generation → re-ranking pipeline with measured latency at each stage
- [ ] Can use SHAP to explain individual ranking decisions

**Evaluation & experimentation**
- [ ] Has built a replay/off-policy evaluation harness and can explain why naive replay is biased
- [ ] Can design a switchback/geo-cluster experiment and explain why standard user-randomized A/B tests fail under spatial interference
- [ ] Has built a calibrated confidence/fallback model with an explicit, cost-justified decision threshold
- [ ] Defaults to segmented (per-market, per-language) evaluation, not aggregate metrics alone

**System & production judgment**
- [ ] Can whiteboard the full geo-search architecture end-to-end, including monitoring/retraining loop
- [ ] Has a deployed, load-tested demo (not just notebooks) with real latency numbers
- [ ] Can speak concretely, with named regions/examples, to "search in markets with poor map data" — not generic GIS talking points
- [ ] Has 2–3 stories ready of a trade-off explicitly considered and rejected, with reasoning

---

### How to use this document
Work top to bottom, but treat Modules 5–8 as non-negotiable depth — they are what separates this JD from a generic "GIS + ML" posting. If you're compressing to 6 months, compress Modules 0–2 (assume more prior GIS knowledge) and Module 10 (run it in parallel with Module 9), but do not compress Modules 5, 6, 7, or 8.
