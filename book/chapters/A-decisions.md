# Appendix A — Every decision, in one table

*Generated from `docs/DECISIONS.md` by `book/build_appendix_a.py`; 64 decisions, 14 open items with their own heading or table row (items raised inline — O-14, O-19, O-20, O-22, O-25 — live in the decisions that raised them). The file itself carries the reasoning; this is the map.*

## Decisions

| # | Date | Decision |
|---|---|---|
| D-1 |  | Project home is `C:\Users\Eric Wade\PAGOURO_BUILD` |
| D-2 |  | `PAGOURO_BRIEF.md` is the origin document |
| D-3 | 2026-09-16 | Secrets never enter the transcript or the repo |
| D-4 | 2026-09-16 | Default working model is `deepseek/deepseek-v4.1-flash` |
| D-5 | 2026-09-16 | GitHub account is `ericrwade` |
| D-6 | 2026-09-16 | Model size is roughly 1B; the product sets the ceiling |
| D-7 | 2026-09-16 | Tokenizer vocabulary must be under 65,536 |
| D-8 | 2026-09-16 | Build on existing open corpora; do not assemble from raw sources |
| D-9 | 2026-09-16 | Reasoning and domain come from different stages |
| D-10 | 2026-09-16 | The domain corpus is the canon, not the forum |
| D-11 | 2026-09-16 | Two-axis evaluation |
| D-12 | 2026-09-16 | "Speak freely" means the HUMAN speaks freely |
| D-13 | 2026-09-16 | Threat model is locked; see `THREAT_MODEL.md` **(locked)** |
| D-14 | 2026-09-16 | The Bitcoin anchor is required, not ceremony |
| D-15 | 2026-09-16 | Eric's own writing |
| D-16 | 2026-09-16 | No Reddit. Ever. |
| D-17 | 2026-09-16 | The fork kit is a deliverable |
| D-18 | 2026-09-16 | Milestones live in `MILESTONES.md`; two new ones added |
| D-19 | 2026-09-16 | Conversation persistence toggle: SAND / STONE |
| D-20 | 2026-09-16 | "Generation 0x" — drizzle, do not hammer |
| D-21 | 2026-09-16 | Own the GGUF export; verify it against PyTorch every time |
| D-22 | 2026-09-16 | Resume is proven by killing a run, never assumed |
| D-23 | 2026-09-16 | Never record a timing number on a busy machine |
| D-24 | 2026-09-16 | The public demo is browser-local, hosted on the Bosgame N95 |
| D-25 | 2026-09-16 | DeepSeek is the default, not the critical path |
| D-26 | 2026-09-16 | `BUILD_LOG.md` is a deliverable, appended every session |
| D-27 | 2026-09-16 | Deflection is a secondary property, not half the pitch |
| D-28 | 2026-09-16 | Never accept a licence agreement on Eric's behalf |
| D-29 | 2026-09-16 | Every ablation arm is scored on ONE shared held-out set |
| D-30 | 2026-09-16 | O-7 resolved in principle: run the teacher's open weights, do not call an API |
| D-31 | 2026-09-16 | Share-alike accepted: weights CC BY-SA 4.0, code Apache 2.0 |
| D-32 | 2026-09-16 | Project Gutenberg is solved: strip the header, the text is public domain |
| D-33 | 2026-09-16 | Tokenizer: custom BPE, ~32k vocab, digits split individually |
| D-34 | 2026-09-16 | LOCKED: the corpus contains only material from before generative AI **(locked)** |
| D-35 | 2026-09-16 | Eric's book: excluded from the corpus, used as a reading guide |
| D-36 | 2026-09-16 | The three chains: Bitcoin, Arweave, Solana. Not Ethereum. |
| D-37 | 2026-09-16 | ~~The domain corpus must carry BOTH traditions~~ **SUPERSEDED BY D-38** |
| D-38 | 2026-09-16 | SUPERSEDES D-37: the classical liberal canon was right after all |
| D-39 | 2026-09-16 | Laborism's blockchain mechanisms (closes O-15) |
| D-40 | 2026-09-16 | Quilibrium joins as a documented mirror |
| D-41 | 2026-09-16 | Anthem is in; the Gutenberg method is proven |
| D-42 | 2026-09-16 | Arweave keeps the canonical storage slot; Quilibrium ships as a first-class mirror |
| D-43 | 2026-09-16 | The tutor: a second artifact that uses Pagouro |
| D-44 | 2026-09-16 | Fixed a Unicode-apostrophe bug that inverted the frontier-model finding |
| D-45 | 2026-09-16 | Tutor grading crashed silently on a llama-cli console truncation |
| D-46 | 2026-09-16 | Real pretrain OOM'd at seq_len=1024/batch=12; config reduced, pipeline hardened with fail-fast checks |
| D-47 | 2026-09-17 | The PC hard-froze mid-pretrain; resume from checkpoint, never from zero |
| D-48 | 2026-09-17 | The first real build completed end to end; two bugs in the tail, one of them retroactive |
| D-49 | 2026-09-17 | The context gauge: the window's fill level is always visible, and turns are seen leaving |
| D-50 | 2026-09-17 | No-bluff does not mean no-answer; what the model says when it can't, and what the marketing may say |
| D-51 | 2026-09-17 | An agent on the stick: yes, as v1.1, tool-assisted before autonomous, and sandboxed |
| D-52 | 2026-09-17 | Agent and tools are in v1.0 as an MVP framework; the origin transcript stays private; share the machine |
| D-53 | 2026-09-18 | Overnight 2026-09-18: the app exists, and what the shakedown model does inside it |
| D-54 | 2026-09-18 | RunPod is the rental provider; connected via the official plugin; spend rule restated |
| D-55 | 2026-09-18 | First rented-GPU run: the bundle works end to end; measured throughput reprices the 1B run |
| D-56 | 2026-09-18 | Retrained the shakedown SFT on 1,982 conversations: routing up, bluffing up, same knowledge ceiling |
| D-57 | 2026-09-18 | Weight updates on the stick: explicit, versioned, reversible adapters, gated by the frozen suite; never silent or real-time |
| D-58 | 2026-09-18 | The shelf: spread the licensed flavors thin, in the anneal, and publish every one |
| D-59 | 2026-09-18 | The book: "Make Your Own AI" — the story plus the actual instructions |
| D-60 | 2026-09-18 | Two integrity findings from writing the book: the forum sample was never licensed, and the validation split was one source |
| D-61 | 2026-09-19 | Pagouro Flash (126M, 2B tokens): the numbers, the decay that ate itself, and the shelf ablation |
| D-62 | 2026-09-19 | The Stack: keep with the caveat now, replace with a dated code source before the 1B volume |
| D-63 | 2026-09-19 | *The Law* leaves the anneal: an "unclear = no" that was only half applied |
| D-64 | 2026-09-19 | The book's licence and its connective tissue (closes O-20) |

## Open items (Eric's calls, or waiting on a measurement)

| # | Item | Status |
|---|---|---|
| O-3 | Data-retention posture on OpenRouter | open |
| O-6 | Enable the aixbt crypto MCP? | open |
| O-10 | Disclosure text for the three chains | open |
| O-12 | Context length: 4k or 8k | open |
| O-13 | Does the N95 status page count as telemetry? | open |
| O-15 | Answerability gate (a Jev-shaped typed decision before prose) | closed by D-39 |
| O-16 | A licensed games-and-strategy slice for the anneal (Eric, 2026-09-18) | open |
| O-17 | Reasoning-shaped licensed slices for the 1B anneal (Eric, 2026-09-18: "Chilton's manuals? What else?") | open |
| O-18 | Program-generated verifiable reasoning data for the anneal (from Eric's road-maps question, 2026-09-18) | open |
| O-21 | Pagouro Draws: a pixel-art image generator on the stick (proposal) | open |
| O-23 | Learning from its owner: retrieval memory now, adapters with a gate next (proposal + level 1 built) | open |
| O-24 | Review of the fine-tuning post; GRPO on the no-bluff objective (proposals) | open |
| O-26 | LightOnOCR-2-1B: re-OCR the shelf's scanned works (proposal) | open |
| O-27 | Beyond English and America: coverage, not reasoning (proposal) | open |
