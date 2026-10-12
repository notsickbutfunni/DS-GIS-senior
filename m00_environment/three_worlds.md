# Three worlds of geo search

A geo search system can be split into three worlds:

- **Index world:** what we know about places and how we store them so they can be found fast.
- **Query world:** what the user meant when they typed something messy.
- **Ranking world:** which of the found places should come first, and whether to show our answer at all.

## One query, three worlds

What happens when someone types "мега" in a ride app:

| World | The question it answers | Example with "мега" |
| :--- | :--- | :--- |
| **Index** | How are places stored so they can be found quickly? | The places database, with names in Russian, Kazakh and Latin script, coordinates, and spatial and text indexes (H3, PostGIS, OpenSearch). |
| **Query** | What did the user actually mean? | Fixing typos and switching between scripts ("mega" → "Мега"), and working out that it's a mall and not a word. All of this has to happen within ~50 ms per keystroke. |
| **Ranking** | Out of the matches found, which should come first? | Mega Alma-Ata vs Mega Park: ordered by distance, popularity and past rides. Also decides whether to show our answer at all or fall back to Google/HERE. |

## Sorting the requirements

The three headline decisions from the roadmap intro, then the core requirement behind each of Modules 1–8.

| # | Requirement | World | Module |
| :--- | :--- | :--- | :--- |
| H1 | Turn ~200M noisy ride sessions into unbiased ranking labels | Ranking | 5 |
| H2 | Keep query understanding under a 50 ms keystroke budget | Query | 3–4 |
| H3 | Decide per query: trust our own index or fall back to Google/HERE | **Ranking + Index** | 7–8 |
| 1 | Find nearby places/drivers fast: spatial index (H3, BallTree) vs. a real routing call | Index | 1 |
| 2 | Cross-script analyzers and BM25 + distance-decay retrieval in OpenSearch | **Index + Ranking** | 2 |
| 3 | Clean typos, transliterate between scripts, parse addresses and landmarks | **Query + Index** | 3 |
| 4 | Distil LLM labels into a fast intent classifier (fastText / MiniLM / GBM) | Query | 4 |
| 5 | Correct position bias in click logs (IPS) to get trustworthy labels | Ranking | 5 |
| 6 | Two-stage retrieval-then-rank with GBDT learning to rank | Ranking | 6 |
| 7 | Offline replay harness and segmented error analysis | Cross-cutting (all three) | 7 |
| 8 | Switchback / geo-cluster A/B tests and the fallback confidence model | Ranking (+ Index for fallback) | 8 |

## Rows that span two worlds

- **H3, the fallback gate.** The decision is made after ranking, so it lives in the ranking world. But what it is really judging is whether our index has the right place at all, so it is also an index-world question. A low-confidence answer usually means missing or wrong data, not a bad ranker.
- **Module 2, retrieval.** BM25 + distance decay is already a first, rough ranking. And retrieval decides what the ranker can ever see: a place that isn't retrieved can't be ranked first.
- **Module 3, cross-script matching.** The same normalisation (lowercasing, transliteration, Kazakh/Russian letter variants) must run both when places are indexed and when the query arrives. If the two sides normalise differently, nothing matches.
- **Module 7, evaluation.** It measures all three worlds. Each failure it finds is traced back to the world (and module) that caused it.

## What this shows

- **Ranking** appears in 7 of 11 rows (counting the evaluation row). That is where most of the job lives, which matches the roadmap's advice not to rush Modules 5–9.
- **Index** is the foundation (Modules 1–2), but it keeps coming back through the fallback gate and data quality.
- **Query** is narrow but has the hardest constraint: latency.