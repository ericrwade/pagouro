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

## 2026-09-17/18 — Freeze recovery, first real build end to end, the app on the stick, GitHub
**Model:** Fable 5.1
**Goal:** Find where the overnight build was when the PC hard-froze; resume it; then, on Eric's
instruction, build the agent/tool harness for the stick during a six-hour unattended window.
**Did:**
- Diagnosed the freeze (last log step 6140, checkpoint 5999 intact; cause unknown; box also
  bugchecked 0x139 on 09-15). Backed up the checkpoint, added atomic saves, `RESUME_PRETRAIN=1`,
  `START_STAGE=N`, `THREADS=N` to the pipeline. Resumed at 12 threads (faster than 16). D-47.
- Pretrain 9000 steps (best ppl 14.7), anneal (114 -> 84.7), SFT, export, quantize, eval, package,
  USB. Two bugs on the tail: `verify_gguf.py` lacked `-no-cnv` (false FAIL); `train_sft.py`
  never shifted targets (every earlier SFT checkpoint incl. M1 was an echo model). D-48.
- Launcher fixes (`-st` single-turn removed, q8, context shift). D-49 gauge, D-50 no-bluff UX and
  marketing language, D-51/D-52 agent in v1.0 as MVP framework, O-12 proposal, O-14 (The Law).
- `docs/ORIGIN_LEDGER.md`: every commitment from the design conversation with status; wired into
  CLAUDE.md/START_HERE. `docs/ORIGIN.md` public story; transcript gitignored (private).
- GitHub: private repo `ericrwade/pagouro` created and pushed; `gh auth setup-git` for credentials.
- Overnight: `app/pagouro_app.py` (harness over llama-server: gauge, SAND/STONE, READ-ONLY/CAN
  ACT, GBNF-constrained tool router, 5 tools, packs, argument recovery, truthful exit line),
  `app/prompts.py`, `sft/build_harness_seed.py` (134 conversations), multi-message
  `train_sft.py`, packager builds `pagouro.exe`. Retrained SFT (306 convs), rebuilt the stick. D-53.
**Verified:** Resume: step 6000 loss 3.963 vs 3.965 pre-freeze. GGUF fidelity 102/102. Offline
audit PASS. App run from `D:\Pagouro` with a scripted conversation: correct tool routing for
calc/time/pack_search/write_note, refusal in READ-ONLY, write after `/act` with the exact note
text, STONE transcript from the toggle onward, gauge drops shown, exit line lists written files.
Router held-out 12/16. Frozen suite: bluff 10%, answered-real 6.7% (a 59M hedger, as expected).
User-space memtest 9 GB x3 clean; no newer BIOS than 1.12; newer AMD GPU driver available.
**Open / next:** Eric's reaction to the stick. Then: (1) memtest86 from USB + GPU driver update
while nothing trains; (2) decide O-12 (8k) and the WSD anneal schedule for the 1B run; (3) SFT
needs thousands, not hundreds: teacher-synthesised tool trajectories (D-30 open weights);
(4) `pack_search` needs an embedding index; (5) O-14 on *The Law*; (6) ONLINE mode + BYO key.

## 2026-09-16 (unattended window 2) — Canon built, frontier deflection tested, tutor working
**Model:** Sonnet 5 (session started on Opus per Eric's direct instruction, ran the bulk on Sonnet)
**Goal:** Work docs/OVERNIGHT2.md top to bottom under its guardrails. Eric raised the OpenRouter
budget to $10 and authorised Fable/Opus escalation if needed (not used -- stayed on Sonnet).
**Guardrails held:** $2.7452 spent of $10 authorised, no other spending, nothing irreversible, no
new licence agreements, committed continuously (30 commits this window), miner off then restarted.

**Task 1 DONE -- the domain canon is built.** 13 public-domain works fetched via
scripts/fetch_gutenberg.py (Gutendex was unreachable from this network; fell back to
gutenberg.org's own search pages). Every ledger row states a specific PD basis -- author or
translator death date, or Gutenberg's own per-edition statement -- never "it was on Gutenberg"
alone. Locke, Smith x2, Bastiat x2, Mill x2, Ricardo, Tocqueville x2, Federalist Papers (verified
all 85 essays present), Henry George, and the Communist Manifesto (Marx's actual Capital has no
English edition on Gutenberg, only Modern Greek -- substituted per D-11 symmetry). 26,563,352
tokens total in corpus.json across 15 sources. Zero trademark residue, verified by grep.

**Task 2 DONE -- frontier deflection tested, and it settled D-27 for real.** Added an OpenRouter
backend to evals/run_eval.py (--api, --budget with a hard pre-call cap, verified to actually block
a call once over budget). Ran the full frozen suite against openai/gpt-6-astra.
  FIRST RESULT (WRONG): bluff 93.3% -- worse than every open model. Read the raw responses before
  believing it: "I don't recognize Verdania as a real-world nation" (correct abstention) scored
  FABRICATE. CAUSE: the model writes a Unicode right single quote (U+2019); every marker string
  used a straight ASCII apostrophe. Local GGUF results were unaffected (llama.cpp uses straight
  quotes) -- meaning this bug was correlated with PROVIDER, not honesty.
  FIXED result: bluff 23.3% (best of any model tested), calibration 96.7%, deflection 0.0% (engaged
  27/27 scoreable items). D-27 amended directly: frontier models do NOT deflect either. Deflection
  is not a differentiator over any tested model class, full stop.
  evals/rescore.py re-applies a scorer fix to every saved raw response with ZERO new API calls.
  Also expanded ABSTENTION_MARKERS with real phrasings this run exposed, and documented one
  residual known limitation (confident false-premise corrections with no hedge word).
  Claude Opus 5 SECOND DATA POINT LANDED before close: bluff 26.7%, calibration 96.7%,
  deflection 0.0% (16/28 scoreable, 12/28 API_ERROR even at a 2000-token budget -- its reasoning
  is heavier than gpt-6-astra's). TWO frontier labs now agree: both markedly beat every open model
  on bluff, both deflect on ZERO contested items. D-27 and BASELINES.md updated with both.

**Task 3 DONE -- the tutor works end to end.** 50 hand-written item-bank entries across 5 topics,
every `source` field validated against corpus.json by tutor/validate_items.py (a build error, not
a warning, if any item cites an uncleared source). tutor/tutor.py: spaced repetition (SM-2), a
model grades free-text answers against a fixed reference, SAND/STONE-honoring progress (D-19).
TWO real bugs found and fixed while getting a working transcript:
  (a) console encoding crash on cp1252 -- fixed by reconfiguring stdout to UTF-8 in both tutor.py
      and run_eval.py.
  (b) grading silently returned the ASCII-art loading banner as the model's "answer" on every
      call, with no crash and no error. Root cause found by diffing raw output byte-for-byte:
      llama-cli TRUNCATES its own console echo of long prompts and appends the literal text
      "(truncated)" -- it does not truncate what's sent to the model. A first fix attempt (CRLF/LF
      normalization) was real but did not address this and the bug persisted identically --
      itself a lesson (a plausible fix that doesn't change the failure diagnosed the wrong cause).
      Real fix: when "(truncated)" appears, everything after its last occurrence is the real answer.
  Also documented, not hidden: the 0.5B grading model itself made a real grading mistake (scored an
  off-topic answer CORRECT). Pagouro's own grading accuracy will need its own eval before being
  trusted as the tutor's grader.

**Task 4 DONE -- SFT seeds expanded 60 -> 99** (50 abstain / 49 confident), now inside the 80-150
target. Overlap guard checked against BOTH the frozen evals (clean) and, this time, internally
against the existing 60 items -- caught one genuine near-duplicate and swapped it.

**Corpus consistency verified at close:** all 15 sources have both public_domain_basis (or a
licence) and published_before_generative_ai. No gaps.

**Open / next:** M3 proper (stream the real corpus mixture per docs/CORPUS_PLAN.md), and the
browser-local demo (D-24) once a real Pagouro checkpoint exists. A third frontier model (e.g.
Google) would strengthen n=2 to n=3 but nothing is gated on it.

---

## 2026-09-16 (unattended window) — M2 baselined, corpus planned, SFT seeded
**Model:** Opus 5 (1M context). NOTE: the plan says run this on Sonnet; Eric started it on Opus.
**Goal:** Work docs/OVERNIGHT.md top to bottom under its guardrails.
**Guardrails held:** no money spent, nothing irreversible, ~2.5 GB downloaded of a 5 GB budget,
committed after every task, stopped at blockers rather than improvising.

**Task 1 DONE - baselines (M2 acceptance now met).** Three Apache-2.0 instruct models scored on
the frozen suite via their own chat templates, idle machine:
  Qwen2.5-0.5B  bluff 56.7% | calib 86.7% | deflect 32.1%
  Qwen2.5-1.5B  bluff 53.3% | calib 90.0% | deflect  7.1%
  SmolLM2-1.7B  bluff 50.0% | calib 93.3% | deflect  3.6%
Premise confirmed: they fabricate on ~half of unanswerable questions while answering 87-93% of
answerable ones. Scale barely helps. Wrote evals/BASELINES.md.

**Task 2 DONE (design only) - docs/CORPUS_PLAN.md.** Every licence checked at source.
  CLEAR: FineWeb-Edu, Dolma (both ODC-By).
  BLOCKED: all BigCode/The Stack (gated, needs Eric to accept terms - D-28);
           codeparrot/github-code-clean (Apache but built on a loading script the current
           datasets library dropped); Project Gutenberg (no mirror declares a licence).
  O-11 now concrete: Wikipedia CC BY-SA 3.0+GFDL, Stack Exchange CC BY-SA 4.0, ~30% of the mix.

**Task 3 DONE - sft/abstention_seed.jsonl, 60 hand-written examples (30/30 balanced).**
Short of the 80-150 asked for; these are genuinely hand-written and the script makes expansion
cheap. The overlap guard FAILED on first build with 5 collisions against the frozen evals, one
exact. Training on the test would have invalidated every published number. All five replaced.

**Task 4 DONE - ablation pilot.** Arm A (web) best val 5.1360 / ppl 170.0. Arm B (+15% code)
5.2916 / ppl 198.7. The comparison is INVALID and that is the deliverable: two confounds found.
(1) Each arm was scored on a validation set held out from its own corpus, so B sat a harder exam.
Anticipated and written down before the numbers arrived. (2) NOT anticipated: corpora matched on
characters, not tokens; code tokenizes denser (3.587 vs 3.804 chars/token) so B drew from a pool 6%
larger. Both would have survived into a published chart reading "code hurts small models".
D-29 now binds M4: shared held-out set, downstream evals leading, multiple seeds, token-matched
arms, pre-registered difference threshold.

**Corrections made:**
- score_bluff rewritten after Qwen-0.5B answered "capital of Verdania" with "Verdania itself" and
  scored HEDGE. All models re-run after the fix.
- train.py --log patch silently missed one reference; both ablation arms would have written to one
  file. Caught by reading the file back.
- T-5 demoted to a floor (D-27) with a dated amendment in TARGETS.md. Not edited in place.

**Open / next:** Eric decides O-11 (may change the mixture, so it precedes M3), D-28 (The Stack
terms), O-7, O-9, O-8. Then finish the ablation write-up and start M3.

## 2026-09-16 (evening) — MILESTONE 1 COMPLETE
**Model:** Opus 5 (1M context)
**Goal:** Execute milestone 1: end-to-end pipeline at toy scale in a fresh git repo.
**Did:** Environment detection, Python 3.12 + venv + PyTorch 2.14 CPU, own Llama-style
transformer, 8,192-vocab BPE with chat and tool tokens, FineWeb-Edu slice with ledger row,
uint16 tokenization, training with checkpoint/resume/logging, own GGUF exporter, verifier,
quantization, README. Three commits.
**Results:** 12.6M params, 24.5M-token corpus, 2,200 steps, val perplexity ~8,800 -> 133.7.
GGUF 63.2 MB f32 / 17.0 MB Q8_0. Generation 2,868 tok/s on CPU.
**Verified, not assumed:**
- GGUF export faithful: PyTorch and llama.cpp decoded identically, 94/94 characters.
- Resume: killed at step 2100, resumed, loss continued at 4.80.
- Chat template round-trips, embedded in the GGUF.
- Tokenizer round-trips including unicode.
**Findings:** (1) This EVO-X2 has 31.6 GB RAM, not the large unified pool the brief assumed.
(2) The box was MINING at 99% CPU; training measured 30x slow and looked like a broken
toolchain. Eric flagged it. (3) 2 TB external drive not attached. (4) ROCm absent, Vulkan
present. (5) llama.cpp's converter moved; we own the export now.
**Open / next:** M2, freeze the eval suite. Blocking elsewhere: O-7 teacher licence,
O-9 tokenizer for the real run, O-11 share-alike weights question.

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
