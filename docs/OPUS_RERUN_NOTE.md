# Claude Opus 5 frontier eval — in progress, pick up here

Started 2026-09-16, session 2, still running in the background when this session closed out.

## What happened

Two attempts:

1. First attempt, `--tokens 500`: completed all three sets, but Opus 5's reasoning consumed the
   entire token budget on most items. 27 of 28 deflection items and 8 of 30 calibration items came
   back `content: null` (`finish_reason: length`), correctly scored `API_ERROR` and excluded from
   the percentages rather than silently miscounted -- but that left almost no usable deflection
   data for this model.
2. Second attempt, `--tokens 2000`, `--budget 4.00`: launched to get real signal on all three sets.
   Still running when this session ended. Spend at handoff: **$2.7452 total on the OpenRouter key**
   for the whole session (both `gpt-6-astra` and both `claude-opus-5` attempts combined), well
   inside the $10 authorized for this window.

## To resume

```bash
bash scripts/preflight.sh                              # confirm the run isn't still live, check spend
ls evals/results/frontier-claude-opus-5*                # did it finish and write files?
python evals/run_eval.py --report                       # see it in the comparison table if so
```

If it finished: read the results, add the row to `evals/BASELINES.md` next to `gpt-6-astra`, and
delete this file.

If it's gone (process died, terminal closed) with no result files: it needs re-running. Consider
whether 2000 tokens was enough -- check the raw `API_ERROR` count in whatever partial data exists
first, since reasoning-heavy models may need more, or a lower reasoning-effort setting if
OpenRouter's payload supports one for this model, rather than simply raising the ceiling again.

## Why this shouldn't block anything else

`gpt-6-astra` already gives a real, verified, single frontier data point that directly answers
D-27's open question: frontier models do not deflect either (0.0%), and this one's bluff rate
(23.3%, corrected) is the best in the comparison table. A second frontier model strengthens n=1 to
n=2, which matters, but nothing in the project is gated on it.
