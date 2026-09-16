# Overnight / unattended work plan

Written 2026-09-16 for a ~24 hour window with Eric away from the machine. A session picking this
up should read `START_HERE.md` and `docs/DECISIONS.md` first, then work this list top to bottom.

## Hard guardrails — these are not negotiable while unattended

1. **Spend no money. Zero.** No paid API calls, no GPU rental, no purchases, no subscriptions.
   The OpenRouter key is currently **uncapped**, so this rule is the only thing standing between a
   loop and a bill. Nothing on this list requires a paid call.
2. **Nothing irreversible.** No force-push, no history rewriting, no deleting checkpoints or data,
   no formatting anything, no BIOS changes, no touching the 2 TB drive.
3. **No LOCKED decision changes.** If work suggests one is wrong, write the argument into
   `DECISIONS.md` as a proposal for Eric and carry on. Do not act on it.
4. **Downloads under 5 GB total.** The brief's limit is 20 GB with permission; unattended, use 5.
5. **Commit continuously**, small and described, so every hour is reviewable and any of it can be
   dropped.
6. **The miner stays off while benchmarking** (D-23), and gets turned back on if the machine is
   left idle for long stretches. Restart script is in the `midstate` folder.
7. **When blocked, stop that task and move to the next.** Do not improvise around a guardrail.

## Task 1 — Baseline the frozen eval suite (highest value, completes M2)

M2's acceptance requires comparison models scored on the identical suite. Without baselines the
bluff-rate claim has no reference point and T-1 and T-5 cannot be evaluated at all.

1. Download 3 small instruct GGUFs from Hugging Face, roughly 0.5B, 1B and 3B, Q4 or Q8. Prefer
   permissively licensed families. Note each one's licence in the results.
2. Run all three sets against each: `python evals/run_eval.py --model <f> --label <name>`.
3. `python evals/run_eval.py --report` and commit the results.
4. Write `evals/BASELINES.md`: the table, each model's licence and quantisation, and an honest read
   of whether T-1's 20% target is ambitious or soft against what the baselines actually score.

**Watch for:** the scorers were tuned against an incoherent model. Real instruct models will expose
new failure modes in the pattern matching. When a verdict looks wrong, read the stored response,
fix the matcher, re-run everything, and note the change. The suite is frozen against *silent* edits,
not against improvement — but a scorer change means re-running every model, no exceptions.

## Task 2 — Corpus design for M3 (no bulk downloads)

Design work only. Do not pull hundreds of gigabytes unattended.

1. For each planned source, verify the licence from the source itself, not from memory: FineWeb-Edu,
   Dolma, The Stack, Project Gutenberg, Wikipedia, Stack Exchange, and the public-domain canon in
   D-10. Record findings with URLs.
2. Draft the full mixture as a table with proportions and token counts, following D-9's stage
   separation. Reasoning-first pretraining, domain via anneal, ethos via SFT.
3. Write `docs/CORPUS_PLAN.md` with the mixture, the per-source ledger rows, and the streaming
   plan from ENVIRONMENT.md Finding 2.
4. Flag anything whose licence cannot be verified. When rights are unclear the answer is no.

## Task 3 — Hand-written SFT abstention seeds (unblocked by O-7)

The abstention behaviour is the product. The synthetic portion is blocked on the teacher-licence
question, but **hand-written examples need no teacher** and are the highest-quality part anyway.

1. Write 80–150 examples in `sft/abstention_seed.jsonl`: an unanswerable question and a good
   refusal that explains *why* it cannot be known, without inventing anything.
2. Write a matching number of confident-answer examples. D-9 and T-3 exist because abstention
   training without this produces a model that refuses everything.
3. Vary the refusal wording heavily. Identical phrasing teaches a tic, not a behaviour.
4. **Do not draw from the frozen eval sets.** Training on the test is the one mistake that would
   invalidate every published number. Keep the topics disjoint and say so in the file header.

## Task 4 — Ablation pilot, only if tasks 1–3 are done

Shake out M4's methodology cheaply before it costs anything.

1. Two ~15M models on equal token budgets: one on FineWeb-Edu alone, one with a code slice swapped
   in for ~15% of the tokens. Everything else identical, same seed.
2. Score both on the frozen suite plus held-out perplexity.
3. Write up the *method*, not the finding. At 15M parameters the result carries no weight; what
   matters is that the comparison machinery works and the confounds are controlled.

## End of window

Write a session entry in `docs/SESSION_LOG.md` covering what was done, what was verified, what
failed, and the single next action. Update the status block in `START_HERE.md`. Leave the working
tree clean and committed.

If the machine will sit idle afterwards, restart the miner.

## The prompt to start this

> Work `docs/OVERNIGHT.md` top to bottom under its guardrails. Spend no money, change nothing
> irreversible, commit continuously. When a task blocks, write down why and move to the next one.
> Leave a session log entry at the end.
