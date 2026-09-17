# Unattended window 2 — build and test

Written 2026-09-16 for a second ~24 hour window. Read `START_HERE.md` and `docs/DECISIONS.md` first.

**Run this on Sonnet.** `/model sonnet`. Eric is on a $20 plan and none of these tasks need Opus.
The design thinking is done and written down; that is what `DECISIONS.md` is for.

## Guardrails

Same as window 1, with one change: **OpenRouter spending is now authorised, with a cap.**

1. **OpenRouter budget: $5.00 maximum for the whole window.** The account holds $50. Check spend
   with `bash scripts/preflight.sh` before and after each task and record it. Stop at $5 even if a
   task is unfinished, and write down where it stopped.
2. **No other spending.** No GPU rental, no purchases, no subscriptions.
3. **No API output becomes training data.** D-30 is absolute: synthetic training data comes from
   open weights run locally, never from an API. Using an API to *evaluate* is fine; using it to
   *generate corpus or SFT content for Pagouro* is not.
4. **Nothing irreversible.** No force-push, no history rewriting, no deleting data, no BIOS, no
   touching the 2 TB drive.
5. **No accepting licence agreements** on Eric's behalf (D-28). He has already accepted The Stack's;
   anything new is a stop.
6. **No LOCKED decision changes.** Propose in `DECISIONS.md`, do not act.
7. **Downloads under 10 GB total.**
8. **Commit continuously.** Append to `BUILD_LOG.md` as you go, not only at the end.
9. **Miner off while benchmarking, back on when the machine goes idle.**
10. **When blocked, write down why and move to the next task.**

---

## Task 1 — Build the canon (highest value, fully unblocked)

`scripts/fetch_gutenberg.py` works and *Anthem* proved it. Now build the domain corpus per D-10 and
D-38.

Ingest, each with its own ledger row stating the public-domain basis:

- **Locke**, *Second Treatise of Government* — Eric named it explicitly
- **Smith**, *The Wealth of Nations*, and *Theory of Moral Sentiments*
- **Bastiat**, *The Law*, *Economic Sophisms*
- **Mill**, *On Liberty*, *Principles of Political Economy*
- **Ricardo**, *Principles of Political Economy and Taxation*
- **Hume**, the economic essays
- **Tocqueville**, *Democracy in America*
- **The Federalist Papers**, the Constitution, the Declaration
- **Marx**, *Capital* vol. 1 — so the model can argue the position it rejects (D-11 symmetry)
- **Henry George**, *Progress and Poverty* — the tax-mechanism parallel

Then: verify every row has `public_domain_basis` and `published_before_generative_ai`. Report total
tokens and the per-author breakdown.

**Watch for:** works whose *translation* is still in copyright, which is a live risk for Marx and
Tocqueville. Prefer a translation published before 1929, and record which one. When unclear, skip it
and write down why.

## Task 2 — The frontier deflection test (uses OpenRouter; settles an open claim)

D-27 demoted the deflection target because open models already engage, and noted the claim was
always aimed at **commercial frontier** models — a comparison never run, because window 1 could not
spend.

Run it now. This is the highest-value use of the budget.

1. Extend `evals/run_eval.py` with an OpenRouter backend (`--api <model-slug>`), reusing the same
   frozen sets and the same deterministic scorers. Store raw responses as always.
2. Score the **deflection set** against 2–3 frontier models. Report spend per model.
3. Score the **bluff set** too if budget allows. Frontier bluff rates would strengthen or weaken
   T-1's framing and nobody has published that comparison either.
4. Write the results into `evals/BASELINES.md` and amend `TARGETS.md` if T-5 needs revisiting again.

**Budget note:** 88 items at a few hundred tokens each is cents on DeepSeek and roughly a dollar on
the expensive models. Start cheap, confirm the harness, then spend.

**If frontier models do NOT deflect meaningfully, say so plainly.** That would kill the deflection
claim entirely rather than demote it, and D-27 should be superseded accordingly. A dead claim
honestly reported is worth more than a live one that does not survive checking.

## Task 3 — The tutor shell (Eric's new request; see `docs/TUTOR.md`)

Build the utility, model-agnostic, testable today against any GGUF.

1. Item bank schema: question, reference answer, explanation, difficulty, and a `source` field
   pointing into `corpus.json`. **Every item traceable.**
2. Seed ~50 items drawn from *Anthem* and whatever Task 1 lands. Fifty good ones, not a thousand
   mediocre.
3. A spaced-repetition scheduler over the bank. Plain, offline, no training needed.
4. A CLI shell: ask, accept a free-text answer, have the model grade it against the reference,
   allow "show me the source" on any item, allow the learner to challenge a grade.
5. Progress in a local file, honouring SAND/STONE (D-19). Default is nothing written.
6. Test it end to end against a baseline GGUF and record a transcript.

**The rule that defines this:** the model explains and paces; it never authors facts. A tutor that
bluffs at a learner would contradict the entire project.

## Task 4 — Expand the SFT set, if time remains

`sft/abstention_seed.jsonl` has 60 examples against a target of 80–150 abstention plus matched
confident. Expand toward it, hand-written, and **run the overlap guard every time.** It caught five
collisions on the first build and will catch more.

---

## End of window

1. `docs/SESSION_LOG.md` entry.
2. `BUILD_LOG.md` narrative entry, mistakes included.
3. Update the status block in `START_HERE.md`.
4. **Report total OpenRouter spend**, per task.
5. Clean, committed tree. Restart the miner.
