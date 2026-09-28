# Origin ledger — every commitment from the design conversation, and where it stands

Source: `My_Claude_Conversation.txt` (Sept 14–16, 2026), the conversation in which Pagouro was
designed. This file turns it into something a session can CHECK rather than reread. One row per
commitment, with a status and the evidence. Update the status column when something changes;
never delete a row — a commitment that was dropped gets SUPERSEDED with the D-number that
dropped it, so the reasoning travels with it.

**Precedence:** `docs/DECISIONS.md` outranks this file (it carries later decisions made with
Eric). This file outranks nothing; it is a checklist. When a row here conflicts with a LOCKED
decision, the decision wins and the row must say so.

**Status key:** `DONE` · `PARTIAL` · `NOT STARTED` · `SUPERSEDED (D-n)` · `REJECTED IN ORIGIN`
(considered and rejected in the conversation itself; listed so nobody re-pitches it).

Last full walk: 2026-09-18 (overnight build of the app).

---

## A. The artifact

| # | Commitment (origin line) | Status | Evidence / gap |
|---|---|---|---|
| A1 | A Llama-style transformer, from scratch, exported to GGUF, runnable in llama.cpp / LM Studio / Ollama (13) | DONE | `pagouro/model.py`, `scripts/export_gguf.py`, fidelity check 102/102 (D-21, D-48) |
| A2 | Portable folder on a $10 USB stick: model + engine, double-click, chat, no install (47) | DONE at shakedown scale | `D:\Pagouro`: `PAGOURO.bat` runs `pagouro.exe` (the harness, D-51/52) over `llama-server`. Multi-turn, gauge, toggles, tools. `PAGOURO-BASIC.bat` is the bare `llama-cli` fallback |
| A3 | Runs at conversational speed on CPU alone (47) | DONE | 905 tok/s generation on the EVO-X2 for the 59M model; NOT yet measured for a 1B model on a ten-year-old laptop (see E3) |
| A4 | Size: 300M, later "aim ~1B if agentic is a priority" (74, 78) | SUPERSEDED (D-6) | 1B locked; the product's stick/laptop promise sets the ceiling, not the budget |
| A5 | Context window of at least 4–8k so retrieval has room (84) | NOT STARTED | Shakedown model is 512. O-12 open; proposal logged 2026-09-17 (8k via anneal-stage extension) |
| A6 | Tokenizer with tool-call tokens and a chat template with tool turns from day one (78) | PARTIAL | Special tokens present; tool turns now in SFT (`harness_seed.jsonl`: 28 tool-answer + 12 multi-turn with tool turns). The harness uses a `tool` role, not `<\|tool_call\|>` yet |
| A7 | Adopt the teacher's tokenizer if logit distillation is wanted (74) | SUPERSEDED (D-7, D-33) | Custom 32k BPE; logit distillation given up deliberately; synthetic-data distillation kept |
| A8 | Quantize to Q8 and Q4_K_M for release (brief §5) | DONE | Both produced and packaged. Launcher now defaults to Q8 for the small model |

## B. The corpus and its ledger

| # | Commitment | Status | Evidence / gap |
|---|---|---|---|
| B1 | General-English backbone (FineWeb-Edu) so the model is not brittle (35, 74) | DONE | In the pretrain mixture (`scripts/build_mixture.py`, `corpus.json`) |
| B2 | Do not scrape GitHub; use The Stack (37) | DONE | The Stack slices (Python, Rust, Go, Solidity) in `data/raw/` |
| B3 | No Reddit, ever (55) | DONE | D-16 |
| B4 | "Hoover up global free wisdom": Gutenberg, Wikipedia, Stack Exchange, arXiv/PMC, US gov, The Stack; bitcointalk becomes a slice (147) | PARTIAL | Gutenberg canon (D-38), Wikipedia, Stack Exchange, FineWeb-Edu, The Stack, bitcointalk present. arXiv/PMC and US-government sources NOT yet ingested |
| B5 | Mixture spine was 40% bitcointalk (74) → domain is the canon, not the forum | SUPERSEDED (D-9, D-10) | Reasoning from general pretraining; domain via anneal + SFT; bitcointalk is "contemporary voice" only |
| B6 | Anneal the last ~10% on the highest-quality slice (74) | DONE, with a finding | Stage 5 runs. D-48: it ran at the LR floor and barely moved; real build needs a WSD schedule |
| B7 | `corpus.json`: one row per source — name, URL, license, token count, share, cleaning, hash (159) | DONE | 24 rows with slug, license, public-domain basis, retrieval date, characters, tokens, cleaning, sha256. "Share of mixture" per row: CHECK it is present for every row before release |
| B8 | Per-source license ledger from day one; skip NC/ND; honor CC BY-SA (147, 163) | DONE | D-31: weights CC BY-SA 4.0, code Apache 2.0; license texts in `licenses/` |
| B9 | Deduplication is mandatory (23) | PARTIAL | Built on already-deduplicated corpora (D-8); no cross-source dedup run of our own. Acceptable for D-8's reasoning; say so in the release notes |
| B10 | Whitepapers are retrieval material, not training data (D-10, origin 84) | DONE as policy | No whitepapers in corpus. No retrieval packs built yet (see D6) |

## C. Training stages

| # | Commitment | Status | Evidence / gap |
|---|---|---|---|
| C1 | Milestone 1: end-to-end pipeline in an afternoon (31) | DONE | M1 2026-09-16; real shakedown build 2026-09-17 |
| C2 | Every long process resumable, progress in a human-readable file (31) | DONE | `--resume`, jsonl logs; resume proven by killing (D-22) and by a real freeze (D-47) |
| C3 | Rent, don't buy; develop on the EVO-X2, one H100 for the final run; produce a job bundle, Eric launches (13, 55, brief) | PARTIAL | RunPod connected (D-54); bundle + on-pod scripts proven on an A40 (D-55, 62k tok/s); `docs/RUNPOD_JOB.md` is the operator sequence. Flash run in progress. The 1B run still needs Eric's 'launch' and the WSD/O-12 decisions |
| C4 | Pearl miners' GPU cloud as a rental option; PRL acceptance maybe (98) | NOT STARTED | Logged in brief; not investigated |
| C5 | SFT: a few thousand curated Q/A pairs; loss on response tokens only; 1–3 epochs; lr 10–50× lower than pretrain (27) | PARTIAL | 306 conversations (99 abstention, 30 crypto, 43 synthesis, 134 harness), not thousands. Multi-message, template-exact, shift fixed (D-48). ~16 epochs at 1200 steps; fine for a shakedown |
| C6 | Abstention examples balanced with confident-answer examples so it does not over-abstain (155) | PARTIAL | 50/49 balanced seed + 43 synthesis examples. The shakedown model still over-abstains (53%); that is the knowledge gap at 59M, not the balance (D-48) |
| C7 | SFT includes "answer only from the provided context, and say when it isn't there" (84) | DONE (seed) | 24 grounded examples in `sft/build_harness_seed.py`, half answerable from the passage, half "the passage doesn't say" |
| C8 | Multi-turn conversation in SFT (implied by "double-click, chat") | DONE (seed) | `train_sft.py` takes any message list; 12 multi-turn seeds; 50% of single-turn seeds get the system prompt |
| C9 | Synthetic data from a permissively licensed teacher; Claude/commercial APIs never generate training data (43, 230) | DONE as policy, PARTIAL in data | D-30: run DeepSeek's open weights locally rather than an API. 30 crypto items exist |
| C10 | Optional DPO on good-vs-worse pairs (27) | NOT STARTED | Later |
| C11 | Tool-use trajectories synthesized with a teacher; grammar-constrained decoding in the harness (78) | PARTIAL | Harness: GBNF-constrained router, one tool per turn, argument recovery. SFT: 70 hand-written router examples (held-out accuracy 12/16 at 59M). Teacher-synthesised trajectories NOT yet |

## D. The application

| # | Commitment | Status | Evidence / gap |
|---|---|---|---|
| D1 | Big, obvious ONLINE / OFFLINE control at the top; offline = zero network calls, the default (86–88); plus the context gauge (D-49) | PARTIAL | The harness shows [OFFLINE] [SAND/STONE] [READ-ONLY/CAN ACT] and the ten-box gauge above every prompt; dropped turns shown with first words. Offline audit passes. ONLINE mode not built (`/online` says so) |
| D2 | Online mode = search and fetch only; conversation never leaves; label in chat when a search happened; mode + date in the system prompt (88) | PARTIAL | `web_search` tool, `/online` (needs `workspace/online.json` with a SearXNG URL or Brave key), grammar/prompts switch per mode, calls printed, exit line counts network calls. Tested against a local stub. No page fetch yet; the 59M model never routes to it |
| D3 | SAND / STONE persistence toggle, SAND default (D-19) | DONE | `/stone` writes `workspace/transcripts/<ts>.txt` from that point; `/sand` stops; exit line lists every file written |
| D4 | Nagware, not crippleware: one line at first launch, ~every 20th session, never mid-conversation; "I've paid" is a local flag; embedded address, no URL but the GitHub release (134) | NOT STARTED | Manifesto text exists (`MANIFESTO.txt`); no nag logic, no address |
| D5 | Retrieval-augmented answers for staleness; the harness searches and pastes paragraphs in (84) | NOT STARTED | — |
| D6 | Retrieval PACKS on the stick: US Code, field manuals, "Where There Is No Doctor", FAO/CDC; foraging/mushroom ID hard-walled out; open recipe dataset only (84, 92) | PARTIAL | `packs/`: Economic Sophisms, On Liberty, **FM 21-76 Survival (US Gov PD, plant/foraging chapters removed + harness notice on foraging queries)**. BM25 search. Not yet: US Code, CDC. *Where There Is No Doctor* is CC BY-NC-SA (Hesperian): NC, so it stays OUT under the rights rule; FAO is mostly NC too |
| D7 | "Get bigger": LoRA adapters on frozen base, factory reset for free; local trainer + cloud job bundle (51, 55) | NOT STARTED | Second real component; post-release or never |
| D8 | Bring-your-own-key search with a self-hosted option, frozen so online mode outlives Eric (126) | DONE (plumbing) | SearXNG (self-hosted, no key) or Brave (key) in `workspace/online.json`; file is gitignored |
| D9 | Browser-local WebGPU version on pagouro.com; no hosted version (197) | NOT STARTED | D-24 places the demo on the Bosgame N95, browser-local. After release, or never |

## E. The pie, the evals, and the receipts

| # | Commitment | Status | Evidence / gap |
|---|---|---|---|
| E1 | "It doesn't bluff": published bluff rate on unanswerable questions vs popular small models; publish the test (155) | DONE (harness), PENDING (model) | `evals/` frozen (M2), `BASELINES.md` with open and frontier baselines. The real model's number does not exist yet. **Release gate (D-50): answered-real under ~80% does not ship, whatever the bluff rate** |
| E2 | Read bluff and calibration together; never publish a bluff rate alone (155, harness warning) | DONE as rule | The harness prints the warning; D-27, T-5 |
| E3 | Tokens/second on a ten-year-old laptop; time from double-click to first answer (155) | NOT STARTED | Needs the 1B model and an old laptop |
| E4 | Receipts over claims: publish eval sets, scripts, loss curves, ledger, inscription ID, Arweave TX (222) | PARTIAL | Evals, scripts, loss logs (`runs/*.jsonl`), ledger all in repo. Nothing anchored or uploaded |
| E5 | Measure the crypto claims first-hand: Arweave cost, Ordinal cost weekday vs weekend, PRL vs RunPod, Strix Halo viability (222) | PARTIAL | Strix Halo: ENVIRONMENT.md. Arweave vs Quilibrium: `QSTORAGE_VS_ARWEAVE.md`, D-42. Ordinal and rental costs unmeasured |
| E6 | Success metrics written down before launch: stars/downloads (track, don't lead), forks, independent reruns of the bluff test, packs shipped, citations, newsletter lift (226) | DRAFTED | `docs/SUCCESS_METRICS.md` (2026-09-18): tiered by how hard each is to fake, 90-day targets proposed, filled in after release regardless of outcome. Eric confirms targets before F13 |
| E7 | The build log is the product; under-promise in print; disclose holdings and costs; no token, on purpose, say why early (222) | DONE (log), PARTIAL (disclosures) | `BUILD_LOG.md` is a deliverable (D-26). Holdings disclosure is O-10 |

## F. Release, GitHub, and anchoring — the part that must happen in ORDER

The origin (108, 114, 126, 138) and brief §10 agree on the sequence. A step done out of order
is a step to redo: the manifest must contain the final hashes, and the anchor must contain the
manifest, so nothing can be anchored until the weights are frozen.

| # | Commitment | Status | Evidence / gap |
|---|---|---|---|
| F1 | Code in a git repo from milestone 1; Claude Code works better with history (108) | DONE | Pushed to `github.com/ericrwade/pagouro` 2026-09-17 (48 commits). Git uses `gh` for credentials (`gh auth setup-git`) |
| F2 | Keep API keys, wallet material, and the corpus out of git from the first commit (108) | DONE | `.gitignore` covers `.env`, `API_KEYS*`, data, checkpoints, `release/`. History scanned 2026-09-17: no key strings, no key files ever tracked |
| F3 | Work PRIVATE through the messy milestones; flip public when there is something coherent to read (108) | DONE (private) | Repo is PRIVATE. Public flip is release step F13 and comes after F8–F12 |
| F4 | Account: `ericrwade`, git identity on the noreply address (D-5) | DONE | `SETUP_GITHUB.md`'s "unresolved" section is stale; D-5 resolved it |
| F5 | Weights to Hugging Face, not to GitHub (108, 114) | NOT STARTED | Release step |
| F6 | Bytes on Arweave (with Quilibrium as a documented mirror, D-40/D-42); only the manifest hash on Bitcoin (17, 114) | NOT STARTED | Release step; costs measured first (E5) |
| F7 | Ungated weights; a key SIGNS, never gates (19, 104) | DONE as policy | Every token-gate and encrypted-weights idea was REJECTED IN ORIGIN (70, 104) |
| F8 | Freeze weights → hash every file → write and sign `MANIFEST.md` (hashes, git commit, license, corpus summary, locations, why it's free) (114, brief §10.1–2) | PARTIAL | `package_release.py` writes a MANIFEST.md with hashes for the stick. Signing key made 2026-09-27 (minisign, Eric, offline; public key `RWQTLswb…` in `pagouro.pub`) `verify_manifest.py` (stdlib, no network) now ships beside the manifest and was tested on the built stick (54/54) and on a tampered copy (fails, exit 1); the whole F8-F13 sequence is written out in `docs/RELEASE_RUNBOOK.md` (2026-09-18). Signing key ceremony is Eric's |
| F9 | Timestamp the manifest: OpenTimestamps at minimum; optional Ordinal inscription of the manifest text, few KB, low-fee day, dedicated wallet, fresh address (114, 118) | NOT STARTED | D-14: the Bitcoin anchor is required, not ceremony |
| F10 | Then publish: Hugging Face + Arweave + a **GitHub Release** with the packaged app, GGUF, and SHA-256 next to every download (114, 126) | NOT STARTED (card drafted) | The GitHub Release is "the link" Eric emails; no website, no app stores. Model card draft: `docs/MODEL_CARD.md` (2026-09-24, TBDs filled at release from `facts.json`) |
| F11 | Windows: ship a .zip; document SmartScreen "More info → Run anyway", or code-sign (126) | NOT STARTED | — |
| F12 | README first paragraph: finished artifact, released as-is, no updates or support promised, fork it (124, 126) | DONE (2026-09-27: Eric chose A; disclaimer and holdings in his words in README/ABOUT) | README now carries the five claims (licensed, dated, honest-measured, finished, your words are yours; D-83) with `docs/WHY.md` and `docs/CHECK_YOUR_COPY.md`; three candidate first paragraphs drafted 2026-09-25 under D-94 (the message: a proof that it can be done and be useful; the niche of documented and self-contained; no competitive claims, no superlatives): **A** (README) — 'built to prove one thing: that an AI can be fully documented and fully self-contained and still be useful … not trying to be the smartest model you can run; trying to be the only one whose promises a stranger can check'; **B** — 'not a competitor … it exists because none of them can say what this one can'; **C** (box) — 'a proof, in the form of a product … if you want a frontier model, use one; if you want to know exactly what you're talking to, this is the niche, and this is the first thing in it.' Full text in the session transcript of 2026-09-25 and to be pasted into the README at F12; Eric picks. Copy note (2026-09-18, Eric's pointer to Robbie Tilton's Compositor): lead with the three-word promise, *free, open source, always yours*, plus the one word an editor doesn't need and a model does: *offline* |
| F13 | Flip repo public, then ARCHIVE it (read-only, forkable); Software Heritage picks it up (126, 138) | NOT STARTED | Last step |
| F14 | pagouro.com → redirect to the GitHub release; DNSSEC on; WHOIS privacy on (189–193) | PARTIAL | Domain bought, private + DNSSEC chosen. No redirect target yet |
| F15 | Licenses: Apache 2.0 / MIT for code; weights at least as open; publish the data recipe so someone could rebuild it (114, 163) | DONE | D-31 (code Apache 2.0, weights CC BY-SA 4.0); `corpus.json` is the recipe |
| F16 | Real name on it; compartmentalize: dedicated project wallet, WHOIS privacy, no home address, one-line employer disclaimer (122) | PARTIAL | Name: yes. Wallet, disclaimer: not yet |
| F17 | Payment: Solana/USDC address embedded; GitHub Sponsors or Ko-fi for cards; price in dollars (64, 68, 138) | NOT STARTED | Needs a dedicated wallet first (F16) |

## G. Considered and rejected in the origin — do not re-pitch

| Idea | Where | Why it was rejected |
|---|---|---|
| Blockchain-enforced single install / token-gated weights | 62–70, 104 | The check runs on the buyer's machine; gate services, never the artifact |
| Inscribing the weights themselves on Bitcoin or Ethereum | 17 | Half a bitcoin to several in fees; anchor the hash, store the bytes elsewhere |
| Scraping GitHub, Reddit, recipe sites | 37, 55, 92 | Terms of service; use The Stack, skip Reddit, open recipe datasets |
| Community token airdrop, token faucet | 100 | Rejected as traction plays |
| A hosted "online version" Eric operates | 197 | Makes him an operator with plaintext and uptime; the browser-local page is the one to build |
| Building Pearl into the product | 96 | Coattails, not partnership: rent from its miners, maybe accept PRL |
| Pseudonymity | 120–122 | Not dangerous work; a signed release from a real person is more trustworthy |
| Encrypted-weights paid tier | 104 | The one path where money means limiting who can use it |
| Building Jev / TypeSafe into the product | 205 | Validates the pie; hosted, closed, early-access — the mirror image of a crab on a stick |
| fossLLM / camelid names | 165–169 | Fossil collision; camelid reads as a Llama derivative |

## H. Standing rules from the origin that apply every session

- Claude Code does the building; the design conversation and the docs do the arguing (234).
- Milestones, each one-shottable, with minutes of Eric between them (31). Never a single run.
- Never rent or spend money without explicit confirmation (brief §3).
- "Wise" comes from the SFT set; the base model is a poster-simulator until then (23).
- Retrieval beats training for anything that should be quoted verbatim (84, 92).
- Under-promise in print; the build log records the mistakes (222, D-26).
- "Weights" means the model file. Mixture proportions are the "data recipe" (151).
