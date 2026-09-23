# MAKE YOUR OWN AI — working outline

*A book: the story of building Pagouro, with the actual instructions to build or change your
own, in the same pages.* Eric's proposal, 2026-09-18 (D-59). This file is the working spine;
chapter drafts go in `book/chapters/` as they are written. Nothing here is final prose.

## The premise, in one paragraph

One person, one desk computer, one rented GPU, and a rule that every training byte has a
licence you can name. The AI that came out is small, honest about what it doesn't know, and
lives on a USB stick. This book is what happened, in order, mistakes included, and every few
chapters it stops and says: here is exactly how you do this part yourself. The reader can
finish it as a story, or follow it as a manual and end up with their own model.

## Shape: two braided strands

- **STORY chapters** — edited from `BUILD_LOG.md` (already narrative, Days 0–8, ~12k words)
  and `docs/SESSION_LOG.md`, with the origin conversation summarised only as `docs/ORIGIN.md`
  allows (the transcript itself stays private, D-52). Eric's own messages may be quoted; the
  session's reasoning is paraphrased.
- **DO-IT chapters** — the instruction docs, rewritten for a reader who is not us:
  `docs/MAKE_IT_YOURS.md` (the ladder), `docs/CORPUS_PLAN.md` + `corpus.json` (the recipe),
  `docs/RUNPOD_JOB.md` + `docs/JOB_1B.md` (renting a GPU), `evals/BASELINES.md` +
  `docs/SUCCESS_METRICS.md` (measuring honesty), `docs/THREAT_MODEL.md` (what "private" means),
  `docs/RELEASE_RUNBOOK.md` (shipping a frozen artifact).

Rule carried over from the build log: **numbers are measured, not remembered; mistakes stay in.**
The book's credibility is the same as the model's — it survives inspection.

## Chapter map (draft 1)

| # | Title (working) | Strand | Source material | Status |
|---|---|---|---|---|
| 0 | The stick | story | `docs/ORIGIN.md`; BUILD_LOG Day 0, Day 1 setup | draft 1 (`chapters/00-…`, 2026-09-21) |
| 1 | What "doesn't bluff" costs | story | D-6, D-11, D-50, BUILD_LOG Day 1 (the size argument) | draft 1 (`chapters/01-…`, 2026-09-21) |
| 2 | **Do it: a model in an afternoon** (tokenizer → 59M on CPU) | do-it | `scripts/train.py`, MAKE_IT_YOURS rung 5–6, BUILD_LOG Day 1 numbers | draft 1 (`chapters/02-…`, 2026-09-21) |
| 3 | The ledger, or why the big labs can't publish this file | story | D-8/D-9, D-32, D-34, D-60/D-62, O-22, BUILD_LOG Days 1–2 | draft 1 (`chapters/03-…`, 2026-09-21) |
| 4 | **Do it: build a corpus you can defend** | do-it | `corpus.json`, fetch tools, licence rules, the shelf (D-58) | draft 1 (`chapters/04-…`) |
| 5 | The test that caught itself | story | BUILD_LOG Day 1 night, Day 2, Day 4 (the apostrophe) | draft 1 (`chapters/05-…`, 2026-09-21) |
| 6 | **Do it: measure honesty** (bluff / calibration / deflection / tool-use) | do-it | `evals/`, BASELINES.md, SUCCESS_METRICS.md | draft 1 (`chapters/06-…`) |
| 7 | The machine stopped | story | BUILD_LOG Day 6 (freeze, checkpoints, resume) | draft 1 (`chapters/07-…`; later corrections as footnotes) |
| 8 | An app on a stick | story | BUILD_LOG Day 7 (gauge, three switches, tools, the dropped turn) | draft 1 (`chapters/08-…`, 2026-09-19) |
| 9 | **Do it: make it yours** (packs, model swap, skills, fine-tune) | do-it | MAKE_IT_YOURS rungs 1–7, SKILLS.md, the skills numbers | draft 1 (`chapters/09-…`) |
| 10 | Three days alone with a budget | story | BUILD_LOG Days 8–9 (RunPod, Flash, the shelf, the ablation, the decay that ate itself) | draft 1 (`chapters/10-…`) |
| 11 | **Do it: rent a GPU without getting hurt** | do-it | RUNPOD_JOB.md, JOB_1B.md, D-54/D-55/D-61 | draft 1 (`chapters/11-…`) |
| 12 | What "private" means, exactly | story+do-it | THREAT_MODEL.md, the offline audit, D-19 | draft 1 (`chapters/12-…`, 2026-09-21) |
| 13 | The one-billion run | story | BUILD_LOG Days 12-14 (the launch, the phantom Low, the full disk, the pause, the watch); last section open for the decay | draft 1 (`chapters/13-...`, 2026-09-23, run at step 58,000) |
| 14 | **Do it: ship a finished thing** (manifest, signature, anchor, archive) | do-it | RELEASE_RUNBOOK.md | drafted (doc) |
| 15 | What it can and cannot do, with the numbers on the box | story | final evals, D-50 wording, `docs/WHY.md` (O-40/D-83: licensed, dated, honest, finished, your words are yours) | future |
| A | Appendix: every decision (D-1…) in one table | reference | DECISIONS.md | generate |
| B | Appendix: the ledger, printed | reference | corpus.json | generate |
| C | Appendix: glossary (token, anneal, WSD, quantise, GBNF, BM25…) | reference | — | to write |

## Reader

Someone curious and stubborn with a computer, not a researcher. Assume they can install
Python and copy a command; assume nothing else. Every DO-IT chapter ends with "what you should
see" (a number or an output line) so they know it worked.

## Rights and rules for the book itself

- Story text: Eric's, first person plural where the build was shared. The session's messages
  are paraphrased, not presented as a co-author's prose. Eric's quoted messages are his words.
- The origin transcript is never quoted at length (D-52). `docs/ORIGIN.md` is the ceiling.
- Every number traces to a log or eval file in the repo (cite the file in a footnote).
- Licence for the book (**D-64, Eric 2026-09-19**): STORY chapters and signposts all rights
  reserved; DO-IT chapters and generated appendices CC BY-SA 4.0. Each chapter file says which at
  the top. Price in dollars if sold (F17), tip jar either way.
- **Signposts** (Eric): short connective passages between chapters — "this is where we tested
  whether adding X, Y and Z would change the output, so we tested it" — so the reader always knows
  where they are. Draft 1 written 2026-09-20 as `chapters/NNa-signpost-*.md` (sorted after chapter
  NN by `build.py`): 04a the canon and the shelf; 06a the tests of the tests; 07a what the
  checkpoint bought; 08a the harness is the product; 10a the audit habit and the scan. 01a the promise,
  priced; 12a the claim and the check (both 2026-09-21). Still to write once its chapter exists:
  after 13 (the 1B run).
- Marketing wording rule D-50 applies to the cover and the blurb.

## Process from here

- The build log stays the source of truth and keeps being appended per session (`CLAUDE.md`).
  Chapter drafts are downstream of it, never the other way round.
- Write DO-IT chapters as their subject stabilises (corpus and evals now; GPU after the 1B run).
- `book/chapters/NN-slug.md`, one file per chapter; `book/build.py` later concatenates to a
  single Markdown / EPUB / PDF (pandoc).
- Word budget: ~60–80k. Story ≈ 35k (the build log edited, plus the window and the 1B run);
  DO-IT ≈ 30k; appendices generated.
