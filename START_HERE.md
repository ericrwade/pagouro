# START HERE — Pagouro session opener

**Read this first, every session. Two minutes, and it prevents the expensive mistakes.**

Last updated: 2026-09-16

---

## 1. What Pagouro is

A ~1B parameter language model, trained from scratch on a fully open and fully documented corpus,
that fits on a USB stick and runs offline on any machine. Its defining features are that it
**does not bluff**, that **every training byte is licensed and hashed**, and that **the person
using it can ask anything without it leaving their machine**.

It is a finished artifact, released as-is, signed and hash-anchored to Bitcoin, with no maintenance
promise. It is also a template: the repo is meant to be forked into models built around other
traditions.

Greek *págouros*, hermit crab: carries a home it can leave. The *ouro* nods to ouroboros: needs
nothing from outside.

## 2. Read these, in this order

| Order | File | Why |
|---|---|---|
| 1 | `docs/DECISIONS.md` | **Highest authority.** LOCKED items are settled; do not reopen them. |
| 2 | `PAGOURO_BRIEF.md` | Origin document. Governs what DECISIONS does not. Carries a precedence notice. |
| 3 | `docs/THREAT_MODEL.md` | Binding on every privacy claim in the README and UI. |
| 4 | `docs/SESSION_LOG.md` (last entry) | Where the previous session stopped. |
| 5 | `CLAUDE.md` | Standing rules. Auto-loads, but skim it. |
| 6 | `docs/ORIGIN_LEDGER.md` | Every commitment from the design conversation, with status. Section F is the release order — walk it before any GitHub/HF/Arweave/anchoring step. |

Where the brief and `DECISIONS.md` disagree, **DECISIONS wins**. Never revert a locked decision to
match the older brief.

## 3. Run preflight

```bash
bash scripts/preflight.sh
```

Checks git identity, GitHub auth, the OpenRouter key, runtimes, and whether `.env` ever got tracked.
Fix anything it flags before starting work.

## 4. Current state

```
STATUS AS OF 2026-09-16 (end of unattended window 2)
  Milestones:     M1 complete (pipeline). M2 complete (evals frozen + baselined,
                  now including one real frontier model). M4 pilot done.
  Repo:           30+ commits, local only. NOT pushed - no remote created yet.
  Corpus:         15 sources, 26.6M tokens. Domain canon built (D-38): Locke,
                  Smith, Bastiat, Mill, Ricardo, Tocqueville, Federalist Papers,
                  Henry George, Communist Manifesto, Anthem. Every row has a
                  stated public-domain basis and a pre-2022 date (D-34).
  BASELINES:      TWO frontier models tested, both labs agree. gpt-6-astra:
                  bluff 23.3%, deflect 0.0%. claude-opus-5: bluff 26.7%,
                  deflect 0.0%. Both crush open models (50-57% bluff) and
                  neither hedges on ANY contested item. D-27 settled for real.
  Tutor (D-43):   working end to end against a baseline GGUF. Two real bugs
                  found and fixed (console encoding; llama-cli truncates its
                  own prompt echo on long prompts). Grading model's own
                  accuracy is a known open gap, documented in docs/TUTOR.md.
  OpenRouter:     ~$2.75 spent this window of $10 authorised.

  RESOLVED SINCE LAST STATUS: O-7 (D-30, run open weights locally, never API),
  O-11 (D-31, share-alike accepted, weights CC BY-SA 4.0), D-28 (Eric accepted
  The Stack's terms, HF_TOKEN in .env), O-9 (D-33, custom ~32k BPE, digits
  split individually), O-8 (book excluded, D-35), O-14 (D-34, pre-2022 cutoff
  locked), O-10 (D-36, Bitcoin/Arweave/Solana, Quilibrium as mirror).

  NEEDS ERIC:
    O-15 was closed (D-39) but the blockchain mechanisms it describes are
    design ideas, not built -- nothing blocks on them yet.
    O-16 (Anthem: done, D-41) -- no longer open.
    (nothing left blocking from this window)

  Next action:    start M3 proper -- stream the real corpus per
                  docs/CORPUS_PLAN.md instead of the toy FineWeb-Edu slice
                  from M1. Optionally a 3rd frontier model (e.g. Google) for
                  n=3, though n=2 already agrees closely.
```

## 5. The things most likely to go wrong

1. **Reverting a locked decision to match the brief.** The brief predates a long design session.
2. **Claiming privacy the threat model does not grant.** People at real risk may rely on this.
3. **Letting a source in without a nameable license.** Provenance is the entire differentiator.
4. **Generating synthetic training data before O-7 is answered.** Same reason.
5. **Treating milestone 2 as a phase rather than the project.** It is where this dies. D-8 exists
   to shrink it; respect that.

## 6. End-of-session ritual

1. Append an entry to `docs/SESSION_LOG.md` (template at the top of that file).
2. Append a narrative entry to `BUILD_LOG.md` — the story, for readers. Mistakes included.
3. Update the status block in section 4 above.
4. Add any new settled choices to `docs/DECISIONS.md`, with the reasoning.
5. Commit and push if a repo exists. Confirm `.env` is not in the diff.
