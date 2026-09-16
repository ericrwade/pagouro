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
STATUS AS OF 2026-09-16
  Phase:          design locked, build NOT started
  Brief:          read; partly superseded (see its precedence notice)
  Repo:           not created yet — will live under github.com/ericrwade, private first
  GitHub:         gh 2.101.0 authenticated as ericrwade; git identity on noreply address
  OpenRouter:     correct account, funded, DeepSeek v4.1-flash verified working
  Target:         ~1B params, ~100B tokens, ~$850 on rented H100s (likely Pearl/PRL)

  BLOCKING:       O-7 — is hosted-API teacher output licensed for training use?
                  Blocks the entire synthetic-data / SFT stage. Resolve in writing.

  Next action:    Milestone 1 (pipeline check) — see brief §12, adjusted by D-6/D-7.
                  Tokenizer choice (O-9) must be settled before a config is written.
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
2. Update the status block in section 4 above.
3. Add any new settled choices to `docs/DECISIONS.md`, with the reasoning.
4. Commit and push if a repo exists. Confirm `.env` is not in the diff.
