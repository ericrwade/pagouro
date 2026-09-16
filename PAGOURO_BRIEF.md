# Pagouro — Project Brief for Claude Code

> A small language model, built from scratch, that lives on a USB stick and needs nothing from outside.
> Greek *págouros*: hermit crab. Carries a home it can move out of. The *ouro* is an ouroboros nod: self-sufficient.

**Owner:** Eric (real name on the project; no pseudonymity)
**Status:** pre-build. **PARTLY SUPERSEDED — read `docs/DECISIONS.md` first.**
**Working name of v1.0:** Kindergarten

> ## ⚠ Precedence notice (added 2026-09-16)
>
> This brief is the **origin document**. It still governs everything `docs/DECISIONS.md` does not
> address. But a long design session with Eric on 2026-09-16 changed several decisions here, and
> **`docs/DECISIONS.md` wins wherever the two conflict.**
>
> Sections materially superseded:
>
> | Section | What changed | See |
> |---|---|---|
> | §5 model size | 300M → **~1B**; the product promise sets the ceiling, not the budget | D-6 |
> | §5 tokenizer | Qwen (~152k vocab) → **under 65,536** | D-7 |
> | §6 corpus strategy | assemble from raw sources → **build on Dolma / FineWeb-Edu / The Stack** | D-8 |
> | §6 mixture design | domain-heavy mix → **reasoning-first pretrain; domain via anneal + SFT** | D-9, D-10 |
> | §6 whitepapers | training data → **retrieval packs only** (licensing) | D-10 |
> | §7 synthetic data | assumed available → **gated on teacher-licence question** | O-7 |
> | §9 evaluation | bluff rate → **two axes: bluff rate + deflection rate** | D-11 |
> | §10 anchoring | optional flourish → **required**; it is what makes mirrors verifiable | D-14 |
> | §14 open questions | 300M vs 1B → **closed** (1B) | D-6 |
>
> New material with no section here: `docs/THREAT_MODEL.md` (binding on all privacy claims) and
> the fork-kit deliverable (D-17).
>
> Do **not** "correct" a decision in `DECISIONS.md` back to this document.

---

## 1. What we are building

A ~300M–1B parameter transformer, pretrained from random weights on a fully open, fully documented corpus, fine-tuned to chat and use tools, packaged as a portable Windows application (also runnable on Linux/macOS via llama.cpp) that:

- runs entirely offline by default, on CPU or any GPU via Vulkan;
- has a big, obvious **ONLINE / OFFLINE** toggle at the top of the UI;
- **does not bluff** — reliably says "I don't know" rather than inventing answers, and cites retrieved text when online;
- ships with a **provenance ledger** listing every training source, its license, its token share, and a hash of the processed slice;
- can be extended by users with **packs** (adapters or retrieval indexes) and, for power users, **continued training** locally or on a rented GPU;
- is released fully open (code + weights + data recipe), signed, and hash-anchored to Bitcoin, as a **finished artifact with no maintenance commitment**.

## 2. What we are NOT building

- Not a frontier competitor. Not a general coder. Not a chatbot that knows the news.
- Not a hosted service. No server. No accounts. No telemetry. No update checks.
- No token, no faucet, no on-chain gating, no DRM. (Explored and rejected.)
- No website beyond a domain redirect to the GitHub release. No app stores.
- No Llama-family naming or derivation — this is from scratch and license-clean, and should read that way.

## 3. Non-negotiables (test these; do not "improve" them away)

1. **Offline means zero network calls.** Pull the cable: no observable difference. No favicon fetches, no update pings, nothing.
2. **Online means search + fetch only.** The conversation never leaves the machine; only harness-generated search queries go to the search provider. Bring-your-own-key; document a self-hosted option (SearXNG).
3. **Default is offline.** Every fresh launch starts offline unless the user made a deliberate sticky choice.
4. **The model must abstain when it should.** Unanswerable/out-of-scope/offline-current-events questions get "I can't know that" not a guess. This is the product's defining feature and is measured (see §9).
5. **Every training byte is accounted for.** Nothing enters the corpus without a row in the ledger with a license we can name. No NC, no ND, no unlicensed scrapes.
6. **Open license.** Apache 2.0 for code. Apache 2.0 or CC0 for weights. Attribute CC BY-SA sources in the ledger and README.
7. **Terminology:** "data mixture / data recipe" = training proportions. "Weights" = the model parameter file. Never conflate in docs or UI.
8. **Secrets never enter git.** API keys, wallet material, and the raw corpus stay out from the first commit.

## 4. Environment and hardware

- **Primary dev/training box:** GMKtec EVO-X2 (AMD Ryzen AI Max+ 395 "Strix Halo", integrated Radeon 8060S, large unified memory — verify installed RAM at start). Two M.2 2280 PCIe 4.0 slots; one is free for a second NVMe. Runs Windows; ROCm/HIP support for this chip is experimental and PyTorch on it is rougher than on NVIDIA. **First task on this machine is environment detection**: report what works (ROCm, Vulkan, CPU-only) before assuming anything. A Linux boot or WSL may be the smoother path for training; propose, don't decide.
- **Secondary box:** Ryzen PC with AMD RX 580. Not usable for ROCm training. Use for scraping and data prep.
- **Storage:** 2 TB external USB drive (archives, raw scrape, old checkpoints). Live tokenized data on internal NVMe. Total project footprint target: < 500 GB.
- **Thermals:** the EVO-X2 runs hot under sustained load and is sometimes used for mining. Training and mining cannot share the machine; expect the user to pause mining for runs.
- **Big run:** rented GPU. Preferred vendors: Pearl (PRL) miners' GPU cloud (miners rent cheap because they also earn PRL), RunPod, Lambda, Vast. **Never rent or spend money without explicit confirmation.** Produce a job bundle + one-line launch script; the user launches.

## 5. Architecture decisions

- **Model:** Llama-style decoder-only transformer (RMSNorm, RoPE, SwiGLU, GQA). Default 300M; parameterize so 1B is a config change. If the agentic/tool-use north star holds, expect to run 1B for the full run (cost ~$100–150 on one H100 vs ~$30 for 300M).
- **Tokenizer:** adopt a permissively licensed open tokenizer that already has chat and tool-call tokens (Qwen's is the default candidate; confirm license and that llama.cpp understands its chat template). Rationale: enables logit distillation later and tool turns from day one. Do not train a custom BPE unless this fails.
- **Context length:** train at ≥ 4k; 8k if compute allows. Retrieval needs room.
- **Export:** GGUF via llama.cpp converters. Quantize to Q8 and Q4_K_M for release. Verify the chat template round-trips.
- **Inference:** llama.cpp (Vulkan build for portability; CPU fallback). Grammar-constrained decoding (GBNF / JSON schema) for every tool call.

## 6. Corpus (the "global free wisdom" recipe)

Target ~10B tokens (~40 GB clean). Small models keep improving well past the 20-tokens-per-parameter rule; overtrain.

| Slice | Sources (verify license per source) | Share |
|---|---|---|
| Educational web | FineWeb-Edu (ODC-By) | ~35% |
| Books | Project Gutenberg (public domain), Wikisource | ~20% |
| Encyclopedic | Wikipedia (CC BY-SA), Wikibooks, Wikiversity | ~15% |
| Expert Q&A | Stack Exchange data dump or HF mirror (CC BY-SA 4.0) — all sites | ~15% |
| Code | The Stack (permissive-license subset): Rust, Go, C++, Solidity, Python; plus blockchain repos (dedup — most chains are forks) | ~10% |
| Government / reference | US Code, CFR, congress.gov, NASA, NIH, USDA, Army field manuals (public domain) | ~5% |
| Forum / voice | bitcointalk (check terms before scraping; crawl politely); blockchain whitepapers | small slice within the above |

Rules:
- **Deduplicate** (exact + near-dup MinHash) across the whole corpus. Near-duplicate code actively hurts.
- **License ledger first.** `corpus.json` row per source: name, URL, license, retrieval date, token count, mixture share, cleaning steps, SHA-256 of the processed slice. This file is a headline feature of the release.
- **Anneal:** spend the final ~10% of training on only the highest-quality slice (Gutenberg philosophy/science, top Stack Exchange answers, whitepapers, teacher-written explanations).
- **Prefer existing open datasets over scraping.** Do not scrape GitHub (use The Stack). Do not scrape Reddit. Do not scrape recipe sites (use an open recipe dataset if recipes are wanted).
- **Synthetic data** may come only from permissively licensed open models (Qwen, Mistral, DeepSeek). Not Llama (naming clause). Not commercial APIs (Anthropic/OpenAI terms prohibit training on outputs). Claude Code writes the code; it does not generate training data.

## 7. Training stages

1. **Pretrain** on the mixture above. Checkpoint frequently; every run must be resumable. Log loss to a file the user can glance at.
2. **Anneal** on the high-quality slice (see §6).
3. **SFT** on a curated instruction set (~5–20k examples; quality over volume):
   - mined Q&A (Stack Exchange accepted answers; bitcointalk question → high-merit reply);
   - teacher-synthesized explanations of whitepapers and code;
   - **abstention examples** — unanswerable questions, out-of-scope questions, "what happened yesterday" while offline — answered with honest refusals; balanced with an equal volume of confident-answer examples so it doesn't over-abstain;
   - **tool-use trajectories** — question → tool call → *actually executed* result → answer, including failures and recovery. Ground results by running the tools, never by letting the teacher imagine them;
   - **RAG examples** — "answer only from the provided context; say when it isn't there; cite it."
   Low LR, 1–3 epochs, loss on response tokens only. Full fine-tune (no LoRA needed at this size).
4. **DPO (optional):** good-vs-worse pairs to sharpen judgment and abstention.
5. **Distillation (optional accelerator):** logit distillation from the tokenizer-matched teacher if compute allows.

## 8. The application

**Chat executable** (single folder or single .exe; no Python dependency):
- llama.cpp backend, model auto-detected from the folder.
- **ONLINE / OFFLINE toggle** — top of window, unmissable, color-coded. Offline default. Tooltip states exactly what online sends and to whom.
- System prompt includes current date, mode, and the model's training cutoff so it can say "I can't check that right now."
- When a search happened, the transcript shows it ("searched: …") so users know which answers came from the web.
- **RAG layer:** local packs = folders of documents with a prebuilt index. Retrieve few, tight, reranked passages. Online mode adds web search + fetch (BYO key; SearXNG documented).
- **Tool harness:** small toolset (search, fetch, read local file, calculator, code runner behind a confirm). Grammar-constrained calls. Hard iteration cap. Harness is written to compensate for the model, not to trust it.
- **Nag:** one line at first launch; rare thereafter (≈ every 20th session); never mid-conversation; a quiet permanent "support" link. Full function always — nag, never cripple. "I've paid" is a local flag. Payment address embedded as static data (Solana/USDC address; optional PRL address); the only URL is the GitHub release page. The nag text is the manifesto: nothing leaves this machine, you own this file, here's an address if it was worth $10.
- **Factory reset:** base weights are never modified; deleting adapters restores v1.0.

**Trainer executable** (second component; CPU-first, Vulkan where available):
- **Local tier:** point at a folder → clean → tokenize → train a LoRA adapter overnight → drop-in. Mix a slice of the original corpus back in to limit forgetting.
- **Cloud tier:** export a **job bundle** (base weights, tokenized data, config, launch script) for a rented GPU; result downloads back and drops in. UI must state plainly that this tier sends data to a rented machine. v1 = bundle + script; no cloud orchestration UI.
- **Packs:** adapters (behavioral/stylistic) or retrieval indexes (factual/reference). Rule of thumb: train on things that teach concepts and voice; retrieve things that should be quoted verbatim (statutes, manuals, prices). Survival manuals, legal codes, recipes → retrieval packs. **Exclude wild-plant/mushroom identification**; hard-wall it behind "consult a physical field guide."

**Browser-local version (undecided, later):** the same model running in the visitor's browser via WebGPU/WASM (llama.cpp wasm or WebLLM). Static page on pagouro.com, no backend, same privacy story. Do not build a hosted server version.

## 9. Evaluation (publish all of it)

- **Bluff rate:** a fixed test of unanswerable / unknowable / out-of-scope questions; report % answered with a fabrication vs. honest abstention. Run the same test on 2–3 popular small open models for comparison. Publish the test set and the script.
- **Calibration:** abstention must not exceed a threshold on a matched set of answerable questions.
- **Tool-call validity:** 100% schema-valid calls (grammar guarantees it — verify anyway).
- **Speed:** tokens/sec on CPU-only on an old laptop; time from double-click to first token. These are the numbers hardware reviewers will check.
- **Offline audit:** a script that runs the app under a network monitor and asserts zero connections in offline mode.
- Held-out perplexity per corpus slice, for sanity.

## 10. Release checklist (do in this order)

1. Freeze weights. SHA-256 every file.
2. Write `MANIFEST.md`: hashes, git commit, license, corpus summary, Arweave/HF/GitHub locations, one paragraph on why it's free. Sign it (GPG or minisign).
3. Timestamp the manifest: OpenTimestamps (free) at minimum; optional Ordinal inscription of the manifest text (keep it under a few KB; do it on a low-fee day; dedicated wallet; fresh address).
4. Upload weights to Hugging Face and Arweave. Attach packaged app + GGUF to a **GitHub Release**. Publish SHA-256 next to every download.
5. Windows: ship as .zip (SmartScreen) and document "More info → Run anyway", or code-sign if the user buys a cert.
6. README first paragraph: *finished artifact, released as-is, no updates or support promised; fork it.* Then licenses, then `corpus.json`, then the bluff-rate results.
7. Flip repo public. Then **archive** it. Software Heritage will pick it up.
8. pagouro.com → redirect to the GitHub release. DNSSEC on. WHOIS privacy on.
9. Per-community coupon codes (plain strings, honor system) if the user wants them. No tokens.

## 11. Milestones (each one-shottable; user checks between)

| # | Milestone | Acceptance |
|---|---|---|
| 1 | **Pipeline check** | Tiny model trained on a small public dataset → GGUF → chats in llama.cpp on this machine. One afternoon. |
| 2 | **Data** | Sources fetched, cleaned, deduped, tokenized; `corpus.json` complete with licenses and hashes. Weeks of wall-clock, mostly unattended. |
| 3 | **Small real run** | ~100M model, 1–2B tokens, on the EVO-X2. Sanity-checks the mixture and the annealing. |
| 4 | **Full run** | 300M–1B on ~10B tokens on a rented GPU (user launches). Resumable. Loss curve reported. |
| 5 | **Fine-tune + eval** | SFT (+DPO). Bluff-rate, calibration, tool-validity, speed numbers all produced and reproducible. |
| 6 | **App + trainer** | Chat exe with toggle, RAG, tools, nag. Trainer with local tier and job-bundle export. Offline audit passes. |
| 7 | **Release** | §10 complete. |

## 12. Milestone 1 — the first goal (execute this)

Build the end-to-end pipeline at toy scale on this machine, in a fresh git repo.

1. Detect environment: OS, Python, PyTorch availability, ROCm/HIP vs Vulkan vs CPU, RAM, free disk. Write findings to `ENVIRONMENT.md`. If GPU training is unavailable, proceed on CPU — this milestone must complete regardless.
2. Adopt the chosen open tokenizer (§5). Record its license in `corpus.json`.
3. Download a small permissively licensed public text dataset (e.g., a slice of FineWeb-Edu or Gutenberg; ~50–100M tokens). Add its row to `corpus.json` with license and hash.
4. Implement the Llama-style model (configurable), a training loop with checkpointing/resume and loss logging, and a sampling script.
5. Train a ~10–20M parameter model until loss visibly drops (minutes to an hour). Save a checkpoint.
6. Convert to GGUF. Quantize to Q8. Load it in llama.cpp and hold a short (incoherent is fine) conversation. Verify the chat template round-trips.
7. Write `README.md` (what this is, how to run each step) and `DECISIONS.md` (this brief's decisions, plus anything decided during the milestone).
8. Stop. Report: what worked, what didn't, timings, and what milestone 2 needs from the user (disk, drive, decisions).

## 13. Working agreements for Claude Code

- Git from the first commit. Small commits. Never commit secrets or corpus data (`.gitignore` first).
- Ask before: spending money, renting hardware, scraping any site, downloading > 20 GB, deleting checkpoints, or changing a non-negotiable.
- Check robots.txt and terms before any crawler runs. Crawl politely (rate limits, identify the bot).
- Every long-running process must be resumable and must write progress to a log file.
- On judgment calls (include/exclude a source, licensing ambiguity, 300M vs 1B, abstention threshold): stop and ask. Do not silently decide.
- Log decisions in `DECISIONS.md` with dates. Keep `corpus.json` current at all times.
- Prefer boring, well-supported tools (PyTorch, HF `datasets`/`tokenizers`, llama.cpp). Avoid clever dependencies that will be dead in two years — this project is meant to be dug up.

## 14. Open questions (owner decides; not blockers for milestone 1)

- 300M vs 1B for the full run (decide after milestone 3 timings).
- Accept PRL as payment alongside Solana/USDC? (Address is static data either way.)
- Browser-local WebGPU version: build after release, or never.
- Whether any commercial path is pursued later. The plan above is the FOSS release either way; traction from it is the input to that decision.

---
*Hermit crab: carries a home it can leave. Ouroboros: needs nothing from outside. Both are the product.*
