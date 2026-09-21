# O-22 — Giving the backbone a pre-2022 basis (D-34), route and cost

Written 2026-09-18 after D-60 found that the backbone rows carry no date basis. D-34 is locked;
this is how it gets satisfied, source by source, with what was measured tonight.

| Source (today) | Date basis today | Route | Cost |
|---|---|---|---|
| FineWeb-Edu (`sample-10BT`, 2 rows, 203M tokens) | **DONE 2026-09-19**: both slices re-fetched with `--date-field dump` (rows `fineweb-edu-big-pre2022`, `fineweb-edu-sample-10BT-pre2022`; dumps 2013-20 / 2017-26 / 2020-05). The filter skipped 44,480 + 5,560 post-2021 documents — the old slices were ~23% past the cutoff, not 'almost certainly pre-2019'. Old rows superseded, mixture points at the new files. | Re-fetch with `fetch_data.py --date-field dump` (keeps `CC-MAIN-2021-*` and earlier; histogram of dumps goes on the row). Measured tonight on 9,000 rows across 6 of the sample's 14 shards: dumps 2013–2021 ≈ 90%, 2024 ≈ 10%, and the shards are ordered by dump, so our first-N-docs fetches were almost certainly all pre-2019 — "almost certainly" is not a basis, hence the re-fetch. For the 1B volume use the per-dump configs of the full dataset (`CC-MAIN-2013-20` … `CC-MAIN-2021-49`) instead of the sample. | bandwidth + a few hours; $0 |
| Wikipedia (`wikimedia/wikipedia` 20231101.en, 96M tokens) | **DONE 2026-09-19**: row `wikipedia-en-20211220` — 86,385 articles / 100M tokens sampled from 5,007 random streams of the `enwiki-20211220` multistream dump via HTTP range requests (no 20 GB download; `scripts/fetch_wikipedia_dump.py`); last-revision years 2012–2021, 87% in 2021. Old row superseded; mixture points at the new file. | archive.org mirrors the Wikimedia dumps: **`enwiki-20211220`** (and 20211201, 20211101…) exist. Fetch `pages-articles-multistream.xml.bz2` (~19 GB), extract with WikiExtractor, ledger with the dump name as the basis. Every revision in it predates 2021-12-20. | ~19 GB download, ~2 h extraction; $0 |
| The Stack v1 (4 rows, 160M tokens) | **DONE 2026-09-21 (D-62b): replaced by five `code-dated-*` rows — 95 permissively licensed repositories at their default branch's last commit before 2022-01-01, licence file classified per repo, 240.7M tokens; the Stack rows are SUPERSEDED.** Earlier: D-62 (Eric, 2026-09-19): (a) kept with the caveat on the rows and the box; (b) replace with a dated code source ≤ 2021-12-31 before the 1B volume. Was: none; collected 2015-01 → 2022-03 | No per-file date in v1. Options: (a) keep, with the row stating "collected ≤ 2022-03-31, up to three months past the cutoff, per-file dates unavailable" and the box saying so; (b) replace with a code source that carries commit dates and filter ≤ 2021-12-31 (candidates to verify: `codeparrot/github-code` — BigQuery snapshot date to confirm; The Stack v2 has no dates either). Recommendation: (a) for Flash-scale work, decide (b) before the 1B volume. | (a) $0; (b) a day |
| Stack Exchange (`stackexchange-preferences`, 17M tokens) | none | Rows carry no date in that derived dataset; the underlying Stack Exchange data dump has `CreationDate`. Route: fetch from the archive.org SE dump (CC BY-SA), filter posts ≤ 2021-12-31. Or drop: it is 5% of the backbone. | half a day, or $0 to drop |
| Canon, shelf, specs (52 rows) | on every row | done | — |
| bitcointalk | none, and 2026 posts | EXCLUDED (D-60) | — |
| Synthetic rows (2) | synthetic, labelled | outside the claim by construction | — |

**Order:** FineWeb re-fetch (cheap, biggest share) → Wikipedia 2021-12-20 → decide The Stack →
Stack Exchange. All of it before `build_mixture.py` runs for the 1B volume (`docs/JOB_1B.md`
prerequisite 5). Until every backbone row carries `published_before_generative_ai: true` with a
stated basis, no public text claims pre-2022 for the corpus as a whole.

**What the Flash and 59M models are:** trained on backbone text with no recorded date basis.
They are measurement models, not the product; their rows and the build log say so.
