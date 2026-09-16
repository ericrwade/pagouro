# Pagouro milestones

Supersedes `PAGOURO_BRIEF.md` §11. Each milestone is one-shottable; Eric checks between them.

Two additions to the brief's list, both cheap and both protecting the expensive work: **M2**
freezes the evaluation suite before any training exists, and **M4** tests the reasoning-corpus
question empirically instead of guessing.

| # | Milestone | Acceptance | Cost / time |
|---|---|---|---|
| 1 | Pipeline check | Tiny model trained on a small public set, converted to GGUF, chats in llama.cpp on this machine. `ENVIRONMENT.md` written. | one afternoon, $0 |
| 2 | **Eval suite frozen** | Test sets and scripts written, committed, and hashed **before any real model exists**. | one day, $0 |
| 3 | Corpus assembly | Dolma / FineWeb-Edu / The Stack curated and mixed; canon slice built; `corpus.json` complete with licenses and hashes. | weeks, $0 |
| 4 | **Reasoning ablation study** | 2–4 small models, identical but for one corpus slice, scored on the M2 evals. Result published either way. | a weekend, ~$60–120 |
| 5 | Small real run | ~300M on 1–2B tokens. Sanity-checks mixture, annealing, checkpoint/resume. | days, ~$30 |
| 6 | Full run | ~1B on ~100B tokens on a rented GPU. Eric launches. Resumable. Loss curve published. | ~420 H100-hrs, ~$850 |
| 7 | SFT + eval | SFT (+ optional DPO). All M2 evals run and reproducible. | days, small |
| 8 | App + trainer | Chat exe with both toggles, RAG, tools, nag. Trainer with local tier and job-bundle export. Offline audit passes. | weeks, $0 |
| 9 | Release | `PAGOURO_BRIEF.md` §10 checklist complete. | days, tens of dollars |

---

## M2 — Freeze the evaluation suite (new)

**Do this before any model worth measuring exists.** It costs nothing and it is the difference
between a claim and a result.

If the bluff-rate test is written after seeing the model, it will be shaped by what the model
happens to do well, and everyone reading it will know that. Writing it first, committing it, and
hashing it is pre-registration in all but name. It is exactly the "receipts over claims" posture
the project is built on, and almost no small-model release does it.

Deliverables:

- **Bluff-rate set** — unanswerable, unknowable and out-of-scope questions, with a scoring rubric
  distinguishing fabrication from honest abstention.
- **Calibration set** — answerable questions of matched difficulty, so over-abstention is caught.
  A model that always says "I don't know" must score badly.
- **Deflection set** — contested questions it has grounds to engage, per D-11.
- **Speed harness** — tokens/sec on CPU, and time from double-click to first token.
- **Offline audit script** — asserts zero network connections in offline mode; must be runnable by
  a third party in minutes (D-13).
- **Targets written down in advance.** What counts as success, committed before the numbers exist,
  so the goalposts cannot move.

Acceptance: all of the above committed and hashed, plus a baseline run of the bluff and deflection
sets against 2–3 existing small open models, so there is a comparison point that predates Pagouro.

## M4 — Reasoning ablation study (new)

**The question:** code and math are the known reasoning-boosters. Is there an unexplored slice
that also helps? Eric's candidates, sorted by the mechanism that makes code and math work
(explicit structure, long-range dependency, verifiability):

| Slice | Why it might work | Licensing |
|---|---|---|
| **Court opinions, with dissents** | Densest explicit argumentation in the public domain. Dissents give the same facts reasoned to the opposite conclusion. Doubles as domain material: property, contracts, ownership. | Not copyrightable in the US |
| **Accident investigations** (NTSB and similar) | Abductive reasoning under uncertainty: facts, hypotheses, rejected hypotheses, probable cause. | US government, public domain |
| **Formal proof libraries** (Lean mathlib and similar) | Machine-checked reasoning; the most verifiable text that exists. | Permissive, verify per library |
| **Music notation** (ABC / MusicXML / kern) | Genuine long-range structure and rule systems that can be checked. Transfer to language reasoning is **unproven**. | Verify per corpus |
| **Procedures with causal failure analysis** | Repair manuals, lab protocols, field manuals. The strong form of Eric's baking-versus-cooking instinct. | Army field manuals are public domain |

Rejected at this stage: anthropology (descriptive, fails verifiability); scholastic theology
(genuinely formal argument structure, but a small corpus and a credibility cost this project cannot
spare early).

**Method:** train 2–4 models at ~300M on ~10B tokens, identical in every respect except one swapped
slice, holding total token count constant so the comparison is clean. Score on the M2 evals plus
standard reasoning benchmarks. One run is the control.

**Cost:** roughly $30 per run, so $60–120 for the study. Compare against $850 for the real run and
the study is cheap insurance as well as a result.

**Publish either outcome.** A negative result is rarer than a positive one and fits the project's
posture perfectly. Nobody publishes clean corpus ablations at this scale: the labs will not
disclose their data, and hobbyists lack the ledger. Pagouro will have both.

**Caveat to state plainly in the writeup:** findings at 300M on 10B tokens may not hold at 1B on
100B tokens, let alone at frontier scale. Claim what was measured, not more.
