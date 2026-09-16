# Pagouro session log

Newest entry at the top. Append one per session, at the end, before finishing.

```
## YYYY-MM-DD — <one-line headline>
**Model:** <which Claude model ran the session>
**Goal:** <what we set out to do>
**Did:** <what actually got built or decided>
**Verified:** <what was actually run and what it output — not what "should" work>
**Open / next:** <the single next action, specific enough to start cold>
```

---

## 2026-09-16 (later) — Design session: direction locked
**Model:** Opus 5 (1M context)
**Goal:** Read the design transcript and the brief, then sharpen the project's direction with Eric.
**Did:**
- Read `My_Claude_Conversation.txt` (238 lines) and `PAGOURO_BRIEF.md` in full.
- Analysed Eric's live OpenRouter catalogue to answer why so many non-frontier models exist:
  443 entries, 52 publishers, but 35 dated snapshots, 18 aliases and 94 batch/free variants.
  OpenAI alone is 96 entries across 59 name stems. Conclusion: catalogues are inflated by
  versioning; the base-model layer is ~15-20 funded labs and everything else is derivative.
- Locked D-6 through D-17 and wrote `docs/THREAT_MODEL.md`.
- Added a precedence notice to the brief and fixed `CLAUDE.md` so DECISIONS outranks it.
**Key shifts this session:**
- Size 300M -> ~1B, ceiling set by the product promise (CPU speed, stick size), not the budget.
- Tokenizer vocab must be under 65,536, for embedding budget and uint16 storage.
- Corpus built on Dolma / FineWeb-Edu / The Stack instead of raw scraping. Shrinks milestone 2.
- Reasoning and domain come from different stages; do not load the pretrain mix with domain text.
- Domain corpus is the liberty/economics canon (mostly public domain), not the forum.
- "Speak freely" = the HUMAN speaks freely. Privacy, not model register. Threat model written.
- Bitcoin anchor promoted from ceremony to requirement: it is what makes third-party mirrors
  verifiable, which is the redistribution use case Eric cares about.
**Verified:** Catalogue analysis run against the live API. Preflight green apart from the
known no-credit-cap warning.
**BLOCKING next:** O-7, whether hosted-API teacher output is licensed for training use. It gates
the whole SFT synthetic-data stage and the provenance claim rests on it.
**Open / next:** Settle the tokenizer (O-9), then milestone 1. Eric to ask his publisher (O-8)
with the narrow framing in D-15.

## 2026-09-16 — Project home established, scaffolding built
**Model:** Opus 5 (1M context)
**Goal:** Make `PAGOURO_BUILD` a place any future session can enter and be productive in
immediately. Establish GitHub and OpenRouter readiness.
**Did:**
- Wrote `CLAUDE.md` (auto-loading operating rules), `START_HERE.md` (session opener),
  `docs/SETUP_GITHUB.md`, `docs/SETUP_OPENROUTER.md`, `docs/DECISIONS.md`, this log,
  `docs/00_ORIENTATION.md` (stub), `.gitignore`, `.env.example`, `scripts/preflight.sh`.
- Surveyed the machine: git 2.54 present but no identity set, no SSH keys, no `gh`, no
  OpenRouter key, Python 3.11.15, Node 24.16.0.
- Installed GitHub CLI 2.101.0 via winget. Not yet authenticated.
  Caution for future sessions: the install runs slowly in the background. An early `command -v gh`
  returned nothing and a second concurrent winget call hung on the first one's lock, which looked
  like a failed install. Wait for the task notification before concluding.
- Verified OpenRouter API facts against live docs rather than memory.
- Added a persistent memory entry so "Pagouro / Paguro / our LLM project" routes here.
**Verified:** Ran `scripts/preflight.sh` end to end. It correctly reported every gap.
**Did NOT do:** Read `PAGOURO_BRIEF.md` — Eric explicitly deferred it. No repo created; the
GitHub account question (O-1) is unresolved.
**Late in session:** Eric supplied `API_KEYS_FOR_PAGOURO.txt`. My masking script had an else-branch
that printed unmatched lines raw, so 59 of the 73 key chars leaked into the transcript. Key was moved
into `.env` without further exposure, `.gitignore` hardened against `API_KEYS*` patterns, and the key
verified live. It is free-tier with no credits and no credit cap. Lesson appended to global CLAUDE.md.
**Resolved same session:** Eric rotated the key into `.env` and removed the plaintext file. Wrote
`scripts/smoke.py` and verified a real completion end to end on two free models. Fixed an f-string
bug in `preflight.sh` that crashed the key-status reporter on its first live run.
**Later:** Eric removed his work email, settling the GitHub account as `ericrwade` (D-5); git
identity set to the noreply address. Locked `deepseek/deepseek-v4.1-flash` as default (D-4). Eric
then found he had used the wrong one of his two OpenRouter accounts and swapped the key; verified
the new one is a different, funded account with a working DeepSeek call. Fixed a bug in
`scripts/smoke.py` where argparse captured the model default before `.env` was loaded, so the
configured default was silently ignored.
**Open / next:** Eric sets a per-key credit cap and revokes the two keys on his other OpenRouter
account. Then READ THE BRIEF together and fill `docs/00_ORIENTATION.md`.
