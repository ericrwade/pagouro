# Appendix A — Every decision, in one table

*Generated from `docs/DECISIONS.md` by `book/build_appendix_a.py`; 101 decisions, 36 open items with their own heading or table row (items raised inline — O-14, O-19, O-20, O-22, O-25 — live in the decisions that raised them). The file itself carries the reasoning; this is the map.*

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
| D-65 | 2026-09-19 | Eric authorises the two small GPU experiments: nanochat head-to-head (O-24) and GRPO on the no-bluff objective (O-25) |
| D-66 | 2026-09-19 | Re-OCR the shelf's scanned works with LightOnOCR (closes O-26) |
| D-67 | 2026-09-19 | Pagouro Draws ships in v1.0, with its own gate; first job: a hundred hermit-crab logos (closes O-21) |
| D-68 | 2026-09-19 | Beyond English and America: both moves, plus register-following spelling (closes O-27) |
| D-69 | 2026-09-19 | Two of the three rental jobs measured: the loop is not the bottleneck (nanochat), and GRPO moves the headline numbers a little (D-65) |
| D-70 | 2026-09-20 | flash-sft3 measured and not shipped: the fine-tune learned the tool names and learned to answer NO_MATCH |
| D-71 | 2026-09-20 | The GRPO big set becomes a three-way curriculum: known / unknowable / invented (first Jev use, $0.054) |
| D-72 | 2026-09-20 | flash-sft4: the tool-result seed works, the headline moves two items the wrong way, and 30-item sets cannot adjudicate that |
| D-73 | 2026-09-20 | The 100-item honesty sets exist, they overturn a tie, and flash-sft3 ships |
| D-74 | 2026-09-20 | HOUSE palette is Belle Époque; posters over cards; the style brief is the Paris poster (closes O-28's palette question) |
| D-75 | 2026-09-20 | The Belle Époque LoRA exists: CommonCanvas-S-C fine-tuned on our poster slice; the first 192 litho-look crab candidates |
| D-76 | 2026-09-20 | flash-sft5: the tool-result problem is solved and the honesty line still moves; stop iterating SFT mixes on the 126M |
| D-77 | 2026-09-20 | Pagouro Draws, model one: the on-stick drawing model exists and follows its caption |
| D-78 | 2026-09-21 | House voice: BC and AD; celestial events dated as observed on Earth; the look is fixed in this version (fork to change it) |
| D-79 | 2026-09-21 | Documents: the harness reads PDF / Word / text, the model reads the text; and the router prompt must stay the trained one |
| D-80 | 2026-09-21 | The mark: Eric's concept #5 is the outward-facing Pagouro brand |
| D-81 | 2026-09-21 | LOCKED: context 4k in the stable phase, 8k in the decay (closes O-12) **(locked)** |
| D-82 | 2026-09-21 | LOCKED: the 1B runs on RunPod; io.net declined for this job, and the reasoning goes in the book (closes O-31) **(locked)** |
| D-83 | 2026-09-21 | LOCKED: no watermark, no claim on outputs — "your words are yours" — and the WHY page **(locked)** |
| D-84 | 2026-09-22 | Wikipedia leaves the 1B backbone (Eric: "if there is a way we can build this without using Wikipedia, I would be perfectly fine with that") |
| D-85 |  | The 1B run started 2026-09-22 08:48Z on 8×H100 SXM secure (pod g3qf86spkqfq1j, CA-MTL-1, $27.92/h) |
| D-86 | 2026-09-24 | Credit line: "Eric Wade, with Claude (Anthropic)" |
| D-87 | 2026-09-25 | SFT B is the 1B candidate; the next lever is the GRPO known/unknowable curriculum on a rented card |
| D-88 | 2026-09-25 | GRPO-1 on the 1B, and the soup: the candidate is 50 % SFT B + 50 % GRPO-1 (bluff 37 / answered 83), Eric to confirm |
| D-89 |  | Eric's three calls on the 1B (2026-09-25, chat): the 70 % soup goes on the stick; GRPO-2 yes; O-45 order = self-knowledge, verified reasoning + careful mode, argue-a-side seed |
| D-90 |  | Eric, 2026-09-25 08:03Z, going to sleep: "You have my permission to spend $100 on runpod to keep this moving forward" (≈ 5 h) |
| D-91 | 2026-09-25 | The GRPO models' "hedges" were greedy-decoding loops; a repetition penalty on FREE answers fixes them; GRPO-3 + penalty = bluff 17 / answered 82; Eric to choose the stick model |
| D-92 |  | Eric, 2026-09-25 (chat): "Do GRPO-3" — GRPO-3 with the decode split ships on the stick |
| D-93 | 2026-09-25 | The multi-turn bug, its cause, and the shipped decode: greedy, no penalty, payload cap, loop trim → GRPO-3 = bluff 22 / answered 81, clean in conversation |
| D-94 |  | The marketing message (Eric, 2026-09-25): a proof that it can be done and be useful; the niche of 100 % documented and self-contained; not competing with frontier or open-weights models |
| D-95 | 2026-09-25 | Research round 2: the reasoning seed works (18 → 94 of 320) and does not ship; soups do not rescue it; GRPO-3 stays |
| D-96 | 2026-09-26 | Round 4 ships as a soup: 60 % GRPO-3 + 40 % GRPO-C′ — bluff 13 / answered 83; the freeze |
| D-97 |  | Autonomous RunPod budget while Eric sleeps: $20 (2026-09-28) |
| D-98 | 2026-09-29 | Pagouro BE: the Belle Époque image model is a sibling release, funded by the RunPod balance |
| D-99 | 2026-09-29 | Pagouro BE round 1 read: the fine-tune draws the subject, the lettering is glyph salad, the judge is lenient; round 2 plan |
| D-100 | 2026-09-29 | Pagouro BE: round 3 is the shipping candidate; f16 ships because q8_0 draws blanks; the box numbers |
| D-101 | 2026-10-01 | The whole book is CC BY-SA 4.0; the story strand's reservation (D-64) is lifted |

## Open items (Eric's calls, or waiting on a measurement)

| # | Item | Status |
|---|---|---|
| O-3 | Data-retention posture on OpenRouter | open |
| O-6 | Enable the aixbt crypto MCP? | open |
| O-10 | Disclosure text for the three chains | open |
| O-12 | Context length: 4k or 8k | closed by D-81 |
| O-13 | Does the N95 status page count as telemetry? | open |
| O-15 | Answerability gate (a Jev-shaped typed decision before prose) | closed by D-39 |
| O-16 | A licensed games-and-strategy slice for the anneal (Eric, 2026-09-18) | open |
| O-17 | Reasoning-shaped licensed slices for the 1B anneal (Eric, 2026-09-18: "Chilton's manuals? What else?") | open |
| O-18 | Program-generated verifiable reasoning data for the anneal (from Eric's road-maps question, 2026-09-18) | open |
| O-21 | Pagouro Draws: a pixel-art image generator on the stick (proposal) | closed by D-67 |
| O-23 | Learning from its owner: retrieval memory now, adapters with a gate next (proposal + level 1 built) | open |
| O-24 | Review of the fine-tuning post; GRPO on the no-bluff objective (proposals) | open |
| O-26 | LightOnOCR-2-1B: re-OCR the shelf's scanned works (proposal) | closed by D-66 |
| O-27 | Beyond English and America: coverage, not reasoning (proposal) | closed by D-68 |
| O-28 | Draw 1.0 has a house style, a palette, and a job: marks for people who don't want the cloud to see their idea | closed by D-74 |
| O-29 | One look across everything that grows from Pagouro: the style follows the model and the mark, not the licence | open |
| O-30 | Skills: adopt the standard container, not the standard semantics; a catalogue, not a marketplace | open |
| O-31 | io.net reconsidered: raw GPU clusters, tested the same way as RunPod | closed by D-82 |
| O-32 | Compute-for-receipt (not licence) for a model beyond 1B; the number first | open |
| O-33 | Secret / NEAR, Cartesi, Mina: three uses that fit inside D-14 and the threat model | open |
| O-34 | Note: the "local AI business" thread (noisyb0y1, 2026-09-19) — market yes, numbers no, offline undercut | open |
| O-35 | Jev / "System One" models: validation, not displacement; make the router a calibrated typed decision (with O-15) | open |
| O-36 | The TypeSafe (Jev / "System One") skill: installed on request, used only for a genuine benefit, never in the product | open |
| O-37 | Better crabs: a licensed diffusion model fine-tuned on our own poster slice, when Eric authorises an hour | open |
| O-38 | Honest randomness: the `dice` skill (Eric: "a local and completely honest dice roller") | open |
| O-39 | Design Arc (friedbeef1/design-arc): not for the console app; the tool for the D-24 browser demo and the release page | open |
| O-40 | OLMo (AI2) and Common Pile: why Pagouro is not redundant, and what to borrow | open |
| O-41 | The "hybrid": a 1B model plus a verbatim shelf (Eric: "1B of normal and 300 MB of verbatim … the US Code as it is written") | open |
| O-42 | A stablecoin wallet for compute bills (Eric: "if RunPod accepted stablecoins, could I have set you up with a wallet and you pay the bill as needed?") | open |
| O-43 | The About page: a key-facts table and a FAQ (Eric: "is there anything in that list we hadn't thought of?") | open |
| O-44 | Handles and domains (Eric: "everything should have some presence. Needs to be findable") | open |
| O-45 | Boosting reasoning, honesty and "over-delivering" in the 1B (Eric: "if you can think of a way to boost that, I want to hear about it") | open |
| O-46 | "Someone could 70B this" / a token raise for a 30B–100B: what it would cost and what the Pagouro of it would be (Eric, 2026-09-25) | open |
| O-47 | Contrastive Language Models (Kwok et al., 2026, "CLM") as a router, later (Eric: "CLM instead of LLM. Any help to us?") | open |
| O-48 | Pagouro as a local model for agent frameworks (Eric: "will I be able to access Pagouro in Hermes Agent … can we package some starter skills") | open |
| O-49 | First outside review (Grok, expert mode, 2026-10-01) and what changed because of it | open |
