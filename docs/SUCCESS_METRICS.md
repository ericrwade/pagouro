# Success metrics — written down before launch, so the goalposts cannot move

The origin conversation (line 226) ranked what would count as success by how hard each signal is
to fake, and said to write the targets down before release and publish the results either way.
This is that document. It is filled in with targets now and with measurements after release;
nothing here is edited after the fact, only appended.

**Status: DRAFT (2026-09-18, unattended window 3).** Targets are proposals for Eric to confirm
before the public flip (ledger F13). Numbers are for the first 90 days after release.

## Tier 1 — hard to fake (these are the ones that matter)

| # | Signal | Target (90 days) | How it is measured | Result |
|---|---|---|---|---|
| 1 | Independent reruns of the bluff test | **3** people post their own run of `evals/` against Pagouro or another model, with numbers | GitHub issues/PRs, or posts that link the eval files | |
| 2 | A pack shipped by someone else | **1** third-party pack (a `.txt` with a licence row) | a PR or a fork with a `packs/` addition | |
| 3 | Citations of the ledger or the eval | **2** references to `corpus.json` or `evals/` in someone else's writing | search + inbound links | |
| 4 | A fork that changes the model or the harness | **1** substantive fork (not a mirror) | GitHub forks with commits ahead | |

## Tier 2 — visible, gameable (track, don't lead)

| # | Signal | Target | Result |
|---|---|---|---|
| 5 | GitHub stars | 100 | |
| 6 | Downloads of the release archive | 500 | |
| 7 | Hugging Face model downloads | 1,000 | |

## Tier 3 — the metric tied to the day job

| # | Signal | Target | Result |
|---|---|---|---|
| 8 | Newsletter lift attributable to the build series | measurable: subscriber delta in the series weeks vs the 8 weeks before | |

## What is published regardless of outcome
- The frozen eval sets and every result file, including the ones that embarrass the model.
- The bluff rate AND the answered-real rate, always together (D-27, D-50).
- The measured costs: rental hours and dollars (D-55 onward), the Arweave/Ordinal fees (E5).
- This table, filled in at 90 days, in the same repository, even if every row is zero.

## What does not count
- Anything the author can produce alone: stars from friends, self-forks, press the author wrote.
- "Interest" without an artifact: a thread saying it looks cool is not a rerun of the test.
