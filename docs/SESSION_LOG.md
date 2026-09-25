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

## 2026-09-24 → 2026-09-25 (the finish) — phase 2 caught twice, the run done, $1,778.97, the 1B measured: 83 % answered, 64 % bluff
**Model:** Fable 5.1
**Goal:** Bring the 1B run (D-85) through its decay, home, and onto the eval sets; keep the cap; tell Eric.
**Did:**
- **Phase change (15:00Z):** the 8k launch ran at 2,097,152 tokens/step (script doubled ACCUM on top of the
  doubled seq) — stopped at 25 min; relaunch 1 fell into phase 1 (STEPS derived from BATCH×ACCUM) — stopped
  at 30 s (a `kill $(ps|grep)` hit my own ssh session, torchrun orphaned, killed by exact PID); relaunch 2 with
  `BATCH=4 ACCUM=4 STEPS_OVERRIDE=95104` correct. ~31 min / ~$14 lost. `train_1b.sh` fixed on the desk (430fbf5).
- **Decay gate (D-61, `decay_watch.py`):** anneal held-out ppl 10.78 → … → **9.2 at step 95,103** (lowest).
  Kept mid-decay checkpoints on the pod as insurance; not needed. `PAGOURO_1B_DONE` 22:52Z.
- **Finish:** `finish_1b.sh` (SFT A/B in parallel on GPUs 0/1 — 3,000 steps in ~8 min each; first attempt died
  on a missing `app/` in the bundle, copied up) → `bring_home_1b.sh` PASS (every hash matched) → pod
  `g3qf86spkqfq1j` + volume `bbwh1nchay` deleted → `list-pods` [] , `list-network-volumes` [].
  **Bill from the account after deletion: $1,778.97** (cap $2,000).
- **Evals on the desk** (q8_0, THREADS=8, ~15 min per model): first pass returned every answer empty in 0 s
  (detached launch → `llama-cli` had no stdin) — `run_eval.py` stdin=DEVNULL (1962899); a raw probe produced
  garbage via the AMD Vulkan backend (`-ngl 0` everywhere, already the case); `verify_gguf.py` PASS 64/64.
  **100-sets: SFT A bluff 61 / answered 83; SFT B 64 / 83.** Tool-result fidelity A 8/10 & 6/10 (4 fabricated),
  B 10/10 & 9/10 (1); tool-use 23/24 both; memory 9 vs 8; skills 10/10/9 vs 7/10/10. **D-87: B is the candidate**
  (q4_k_m 633,976,000 B, sha256 ed05f5c6…); NOT on the stick until Eric has seen the numbers.
- **Writing:** BUILD_LOG Day 15 + Day 15 night; book ch. 13 draft 2 (complete through the numbers); D-85 results
  + D-87; `facts.json` filled (bill, honesty numbers, candidate files); watch cron deleted.
- **Earlier the same day:** README five claims (D-83) + licence to D-31; `docs/ABOUT.md` + `facts.json` (O-43);
  `docs/MODEL_CARD.md`; `docs/HANDLES.md` (O-44: `pagouro` free on 12 platforms, pagouro.com is Eric's);
  D-86 credit line; memory note; `bring_home_1b.sh`, `decay_watch.py`, parallel `finish_1b.sh`.
**Verified:** every number from the run jsonl / train.log / eval result JSONs / billing API; hashes pod↔desk.
- **05:10Z addendum — GRPO-1 + the soup (D-88):** Eric said run it; 1×H100 `vd1rszh2bmzlsn` ≈ $11, 300 steps,
  home hash-verified, pod deleted. GRPO-1 alone: bluff 19 / answered 86 but 42 looping hedges, deflection 0/28.
  Weight soups (`scripts/soup.py`): **50/50 = bluff 37 / answered 83 / deflection 23/28 / tool-result 10/10 —
  the candidate**; 70 % GRPO = 29 / 85 / 16/28. O-45 (Eric asked how to boost reasoning/honesty): five
  ranked levers. Bill all-in ≈ $1,817; ≈ $183 left; no pods.
**Open / next:** (1) **Eric:** pick the soup (50/50 recommended, or 70 %) for the stick; yes/no on GRPO-2
(~$10: 128-token completions + repetition penalty, a deflect kind, KL 0.1, from the soup); O-45 order; (2) **the bluff rate is the problem** (64 % at 83 % answered): plan the GRPO known/unknowable
run (D-69 curriculum, `sft/grpo_*.jsonl`) on one rented card — plan + hourly price on #2 first (D-54); Eric's
"rent"; (3) book ch. 15 after the shipped numbers are final; ch. 13a signpost; (4) `package_release.py` run
with the 1B (MODEL_STEM=gguf_1b/pagouro-1b-sftB, CONTEXT_WORDS for 8k) once (1) says so; (5) O-41 US Code
pack, O-29/O-31/O-32, TypeSafe key rotation — still Eric's.

---

## 2026-09-22 evening → 2026-09-23 (the watch day) — top-up, the stale anneal, sixty thousand steps, chapter 13
**Model:** Fable 5.1
**Goal:** Keep the 1B run (D-85) healthy and inside the cap; answer Eric from the road; use the gaps.
**Did:**
- **Eric (chat):** "+$500, go for the full 100B" → cap $2,000, full 95,104 steps, early-decay rule retired
  (D-82/D-85). 1B never "1B+" (`docs/WHY.md`, D-83 section). O-41 the hybrid / US Code shelf pack (waits
  on "add it"); O-42 stablecoin wallet for compute (deferred). Chapters 13/15 requested after the run.
- **Caught:** the anneal on the pod was the Sep-16 build (contained bitcointalk, D-60) — rebuilt from the
  current ledger (`data/tokenized_anneal_1b`, 12,325,693 train tokens, 31 works, 0 forum lines) and
  placed as `/workspace/pagouro/data/tokenized_anneal` ~20 h before phase 2.
- **Watch:** 30-min ticks (list-pods, step/val/ckpt/GPU/disk); checkpoints home + torch.load-verified at
  steps 23,000, 33,000, 42,500, 52,000 (each replaces the last; `checkpoints/pagouro-1b/`); billing posted
  at 25% ($439), 37% ($740), 43% ($866), 49% ($978). Zero restarts, no NCCL/Xid, GPUs 46–61 °C ~690 W,
  460k tok/s flat (33.6% MFU), 92 GB free. **Honest note posted:** session paused ~12:00–23:35Z Sep 22
  (cron ticks queued), two checkpoint copies missed; the run never noticed.
- **Numbers, from the jsonl not the log tail:** val ppl 90 (step 500) → 19 (2,500) → 12.3 (8,500) → <10
  first at 29,000 (9.6) → **low 9.2 at 38,500**, tied at 53,000; stable-phase band 9.5–11; per-batch loss
  2.0–2.6 since step 10,000. Two #2 posts had called 9.7@51,500 and 9.2@53,000 "new lows" — wrong,
  corrected in BUILD_LOG Day 14 and on #2. Timeline corrected from the step clock (2.26 s/step): phase 1
  ends step 85,593 ≈ Sep 24 15:00Z; `PAGOURO_1B_DONE` ≈ 22:30Z; total ≈ **$1,805** (an earlier $1,915
  double-counted the decay).
- **Prepared for the finish:** `sft/` + `skills/` staged on the pod; export needs only numpy+torch;
  `scripts/eval_gguf.sh` (desk: q8_0 + q4_k_m + every suite). `finish_1b.sh` = base export, SFT A
  (`--repeat toolresult_seed.jsonl=0`), SFT B, exports to `/workspace/out`.
- **Writing:** BUILD_LOG Day 13 + Day 14-so-far; **book ch. 13 draft 1** (2,855 words, decay section left
  open); outline row 13; appendix A regenerated.
**Verified:** every number above read from `/workspace/runs/pagouro-1b.jsonl`, `/workspace/train.log`,
`list-pods`, `list-billing` or the #2 timestamps; checkpoint copies opened with torch.load on the desk.
**Open / next:** (1) watch to step 85,593 (≈ Sep 24 15:00Z): phase-2 switch to 8k, held-out anneal loss
must not rise (D-61); (2) checkpoints home every 6 h (23:40Z, 05:40Z, 11:40Z, 17:40Z); billing posts at
75% ($1,500) and 90% ($1,800); (3) on `PAGOURO_1B_DONE`: `bash scripts/runpod/finish_1b.sh` on the pod,
bring `/workspace/out/*` + final ckpt + logs home, verify, delete pod `g3qf86spkqfq1j` and volume
`bbwh1nchay`, `list-pods` empty; then `scripts/eval_gguf.sh` on both SFT mixes → D-76 adjudication →
package; (4) close ch. 13 ("The decay") and draft ch. 15 from the evals; D-85 results row; BUILD_LOG Day 15.

---

## 2026-09-21 evening → 2026-09-22 (the 1B launch) — data volume, nine hours of stock, the run
**Model:** Fable 5.1
**Goal:** Eric: "start on runpod. I will add money to it right now." (D-82); 4k→8k approved (D-81).
**Did:**
- **Decisions:** D-81 context; D-82 launch on RunPod, io.net declined for the job (`docs/GPU_PROVIDERS.md`,
  goes in the book); D-83 no watermark / no claim on outputs + `docs/WHY.md`; D-84 Wikipedia out of the
  backbone; D-85 the run itself. O-39 Design Arc, O-40 OLMo/Common Pile. `docs/CHECK_YOUR_COPY.md`
  (verification for someone who has never heard of a hash) ships on the stick with WHY.md.
- **Data volume** (`scripts/build_volume.py`, `plans/volume_1b.json`): CPU pod 32 vCPU $0.96/h in
  EUR-IS-1 + 500 GB network volume; 83 dated FineWeb-Edu dumps by name (1.12B tokens / ~300 s each),
  Stack Exchange whole (7.67B, per-row dated), dated code ×3; Wikipedia's range-request sampler too slow
  at scale — `--local` mode written and the 20 GB dump downloaded, then Eric dropped the source (D-84).
  **99,724,809,408 train tokens**, 199.4 GB, sha256 4a60a5ff…, 8h46m, ~$8.50. Mixture on the row:
  FineWeb-Edu 91.6% / SE 7.7% / code 0.7%.
- **Cards:** secure 8×H100 Out on 17 of 19 half-hourly reads over 9 h; the community "Low at 8" is a
  phantom (1 GPU per pod max); B200/H200 Out throughout; 16-card clusters none. Created 07:24Z on the
  first secure sighting: `g3qf86spkqfq1j`, CA-MTL-1, $27.92/h.
- **Volume pull across DCs:** single rsync 16 MB/s → 16 parallel byte-range streams ~175 MB/s (11 of 16
  survived sshd MaxStartups; per-chunk hash refetch fixed the rest; whole-file sha256 verified).
- **Rehearsal:** 968,968,192 params; micro-batch 8 OOMs → 4×4096×accum 8×8 = 1,048,576 tokens/step;
  318,660 tok/s plain (23.4% MFU), **≈444–459k tok/s with torch.compile (33% MFU)**; checkpoints 11.6 GB.
- **Run started 08:48Z:** 95,104 steps, WSD, warmup 2k, stable to 85,593, decay at 8k on the mix.
  Projection ~$1,800 vs ~$1,440 cap remaining → YELLOW: Eric's top-up (~$500) or early decay at ~$1,100
  spent (~59B tokens), decision by ~Sep 23 15:00Z. Step-500 checkpoint home and verified; build pod
  terminated (volume kept as backup). Near-miss: a surviving rsync filled the pod disk to 100% (deleted
  open file, 104 GB); killed by PID minutes before a checkpoint save would have crashed the run — lesson
  in CLAUDE.md. Balance: $1,500 fixed, no auto-reload (Eric); GREEN/YELLOW/RED on every update (Eric).
**Open / next:** (1) Eric: top-up or 60B; (2) checkpoints home every 6 h; watch every 30 min; (3) when
phase 1 ends: decay at 8k, SFT (staged mix, D-76), export, evals on the 100-sets, package, delete pod,
verify home, delete volume; (4) book chapter 13 from the build log; chapter 15 after the evals;
(5) box language → licensed, dated, honest, finished, your words are yours (D-83).

---

## 2026-09-20 (unattended window 3, day 3) — Palettes, skills, spelling, GRPO at scale, and the re-OCR audit that caught our own OCR
**Model:** Fable 5.1
**Goal:** Finish the D-66 rental (recipes, MUTCD), then work the post-rental list: O-28 palette
candidates, O-30 skills container, D-68 spelling register, the thousands-scale GRPO set, the
per-page numeric diff from the D-66 note.
**Did:**
- **Recipe manual re-OCR'd and ingested** (1,691 pages, 0 failed, 1.64M tokens; 2,975 tables).
- **O-28:** three 32-colour house palettes (Trade Card, Gaslight, Naturalist Plate) in
  `app/palettes.py` with the renderer rules (quantiser, dither, one-pixel ink outline); a
  program-drawn hermit crab in `artkit.py`; `scripts/palette_sheet.py` → `docs/samples/palettes/`;
  sheet sent to Eric's phone and posted on #2. **Eric's call: which becomes HOUSE.**
- **O-30 built:** `app/skills.py` (screened-not-sandboxed loader, MANIFEST hashes, wild SKILL.md
  folders accepted with a used/ignored report), three first-party CC0 skills (`unit_convert`,
  `date_math`, `recipe_scale`), `scripts/skill_test.py` (static / tool / end-to-end / routing;
  writes `skills/CATALOGUE.md`), `/skills`, packager ships `skills/`, `.gitattributes` pins LF.
  Measured on Flash: tool 10/10 ×3, end-to-end 10/10 ×3, **model router alone 0/10 ×3** (routed
  conversions to `calc` with invented factors) → `TRIGGER` regexes in the harness (0 false positives
  on the frozen suite) and skill examples fed into `train_sft.py`.
- **D-68 (iii):** `app/spelling.py` (1,960 pairs), `sft/spelling_seed.jsonl` (501 rows),
  `evals/spelling.json` + runner scored on *novel* marked words (the naive score was 8/9 because the
  model echoes the cue). Flash baseline: 0/0 scored, 10 unscored; echo-inclusive 4/4.
- **GRPO at scale:** `sft/build_grpo_big.py` → 5,935 prompts (2,979 real from prominent Wikipedia
  first sentences with common-category heads as keys; 2,956 invented in identical surface forms,
  stems verified absent from every title); eval-disjoint.
- **D-66 audit — the important one.** `numeric_drift.py --conflicts` (ordered-number alignment,
  context-gated near-miss pairs) flagged a canning process time; the page image said a third number.
  `reocr_footer_check.py` showed the cause: **batched OCR contaminated the first two leaves of every
  8-page batch** (they begin with their own page and continue with the previous batch's leaves 4–5;
  footers prove it). ~25% of pages in all six works. The stick was never touched; the ledger rows and
  repo packs were. `reocr_fix.py` (unbatched redo of positions 0/1 + every tail-copy leaf) tested
  clean on two leaves and is queued behind MUTCD on the pod; `ingest_reocr.py` now refuses a work
  that fails the page-order check and records the check on the ledger row.
**Verified:** skill tests and routing from `scripts/skill_test.py` output; spelling numbers from
`evals/results/pagouro-flash2__spelling.json`; footer/tail-copy counts from the pod's per-page
files; the page images for USDA leaf 94 and NEETS 1 leaf 22 opened and read (in `docs/samples/ocr/`).
**Closing addendum (02:00–05:30 PT):** the unbatched redo ran as two parallel single-page
processes (~0.05 pages/s each); every work re-fetched, page-order-checked and re-ingested — NEETS
1/2/13 + USDA 0/0 (were 29/20, 23/11, 24/7, 8/8; USDA 3-12 now reads 85 min as the page does),
MUTCD 816 printed page numbers in order (checker now reads running heads) with 6 tail copies
verified as Part 6H boilerplate, recipes 502 leaves redone with 127 tail copies left that are
variant-card Notes spread evenly across batch positions. Ledger 71 rows verified. **Pod
`y1wscss6dj9gsw` deleted 04:40 PT, `list-pods` empty; billing after deletion: this pod $5.88,
window total $13.91 across four pods.** Stick refreshed (stages 9–11: audit PASS 40 samples,
skills on the stick, manifest 81/81); live scripted run on the stick: `/skills` lists three,
"How many kilometres is 26.2 miles?" triggers `convert` → `26.2 mi = 42.16 km` — but the model's
composed reply after the tool result is poor ("26.2 miles"), so answer examples (user → tool
result → reply, tool outputs recorded verbatim) were added to each skill and to the SFT loader.
Also: Belle Époque palette (fourth candidate, Eric's question) + finalists sheet; Met slice one
1,780 CC0 images → curated 307 at 64/32 px; Kenney slice 22 packs / 4,380 sprites; O-35 router
probability measured (0.917 right vs 0.816 wrong); book ch. 9 and 10 drafted; Build Log Day 11.
**Afternoon addendum (06:00–15:30 PT):** D-70 sft3 measured (skills routing 0→5–8/10 model-alone;
NO_MATCH fabrication found) and a **tool-result fidelity** frozen set built (sft2 6/10, 3/10).
D-71: Jev use #2 ($0.054) labelled the GRPO big set — 91% of "real" questions unknowable to a
stick model — → three-way curriculum + `--balance` + 170 known reals from the ledger's own books.
D-72: sft4 (tool-result seed) fixed its target (NO_MATCH 6/10) but the 30-item headline moved two
items. D-73: **100-item honesty sets** frozen; they overturned the sft2/sft3 tie (56/11 vs 38/19)
→ **sft3 shipped** on the stick. D-74: **HOUSE = Belle Époque**, posters over cards; `/art mark`
draws the medallion; Met artist: queries; LoC Artists Posters fetcher (throttled, now 6 s pacing).
O-36: TypeSafe/Jev key stored and verified, $5 starting credit, uses logged ($0.13 total, 4 uses).
O-37/D-75: procedural mark in the retreated configuration (Eric's refs), then the **Belle Époque
LoRA** on CommonCanvas-S-C trained on our poster slice on a rented A40 (~75 min, ≈$0.61; pod
deleted, `list-pods` empty): 192 litho-look candidates home, sheets sent. sft5 (abstention ×3 +
tool-result seed, 5,500 steps) training; eval chain armed.
**2026-09-21 morning addendum (00:30–04:00 PT):** **D-62b done** — The Stack superseded by
five `code-dated-*` rows: 95 permissively licensed repositories at their default branch's last
commit before 2022-01-01 (`rev-list --first-parent --before`), licence file classified before a
byte is taken, commit hash/date/licence per repo on the row; 240.7M tokens (py 65.0M, rs 36.6M,
go 63.7M, sol 1.4M, **C++ 74.0M new**); `build_mixture.py` reads `code/<lang>.txt`; the backbone
is now fully dated (last O-22 item). Three defects caught before any row was written (cpython
mis-skipped on a GPL mention in a choice-of-law clause; protobuf's pre-cutoff commit came from
merged-in upb history with no `src/`; four licence-file shapes) — run redone from scratch.
**Book:** chapters 0, 1, 2 (do-it), 3, 5, 12 and signposts 01a/12a drafted; 23 chapters, ~30k
words; only 13 and 15 (the 1B run) remain. LoRA pod billing settled so far $0.40; `list-pods`
empty. `workspace/docs/` gitignored (user documents, D-79). LoC crawl: 243 posters.
**2026-09-21 afternoon addendum (04:00–12:45 PT):** README status paragraph brought to sft3's
100-set numbers and the dated code slice; `build_mixture.py` dry-run reads all five `code/<lang>.txt`
with `[ledger OK]`; LoRA pod billing settled at $0.40 (window RunPod ≈ $14.31). **LoC crawl
finished:** 1,411 posters 1868–1928, rights per item, ledger committed; SD training set rebuilt
(1,944 crops); pixel set rebuilt with the posters (11,667 images). **draw2** trained on the desk
(1h51, THREADS=8): crab and poster rows better than draw1, sprite row worse — a 5.5M proof, the
20–50M GPU model is the step. **O-39** Design Arc assessed (Eric's link): not for the console,
the tool for the D-24 browser demo and release page; its every-state checklist applied — four
console failure states now visible with a hint (startup failures wait for a keypress when
double-clicked, server stderr tail shown; STONE on an unwritable disk falls back to SAND; a bug in
one turn no longer ends the session); stick repackaged and manifest-verified.
**2026-09-21 evening addendum:** **D-80** — Eric's mark (concept #5 of ten, made with ChatGPT)
is the brand: `brand/` shipped (sizes, exe icon, 64-px house-palette `/art logo`), README/STYLE_GUIDE/
ABOUT_THE_LOOK point at the file, provenance and rights stated without overclaiming, stick repackaged
and verified. The procedural medallion and LoRA candidates are studies now.
**Open / next:** (1) The mark is chosen (D-80), so the LoRA picks are moot; the 20–50M draw model
(D-67, for `/art` pictures beyond the mark) still wants an hour of GPU when Eric says "rent". (2) O-29 trademark, O-31 io.net, O-32
receipt model — Eric. (3) Next fine-tune only at 1B (D-76): skill router+answer examples,
spelling, style and tool-result seeds are staged in `docs/JOB_1B.md`; GRPO on the curriculum when
GPU time is authorised. (4) 1B prerequisites still open in `docs/JOB_1B.md` (data volume build,
tokenizer streaming already ✔). (5) LoC crawl done, billing settled — nothing pending there. (6) Book: 13 and 15 after the 1B run; a read-through pass for
the story strand's voice once Eric is home.

---

## 2026-09-19 (unattended window 3, day 2, overnight) — Flash evaluated, the decay that ate itself, the shelf wins, three integrity fixes
**Model:** Fable 5.1
**Goal:** Land the Flash run (D-61) and keep the plan moving while Eric is away; answer his
questions from the road (book, images, learning from the owner, the fine-tuning post, LightOnOCR,
English/America).
**Did:**
- **Integrity (D-60):** `bitcointalk-sample` excluded (no nameable licence; 8,823 of ~12k posts
  dated 2026) and swapped out of the pod's anneal before the decay began; validation split now
  spread across the stream (the real run's "ppl 14.7" was on Solidity alone); backbone pre-2022
  gap logged as O-22 with a route (`fetch_data.py --date-field dump`, `enwiki-20211220`).
- **D-61:** naive anneal-only decay memorised the anneal (held-out 3.25→4.82); stopped; redesigned
  as a FineWeb+anneal mix, two arms from the same stable checkpoint. Shelf arm better on every
  clean held-out set, no general-text cost. SFT on the pod GPU (6 min); Flash 126M: bluff 36.7%,
  answered-real 26.7%, tool 75%, memory routed 8/10. Pod deleted; window spend $7.54 (billing API).
- **Stick (59M)** re-fit on the full 5,558-conversation set (generator finished: 5,184 rows,
  700/class): bluff 16.7%, answered-real 3.3%; stick rebuilt.
- **Book (D-59):** outline + chapters 4 (corpus) and 6 (measuring honesty); writing ch. 4 found
  the Gutenberg hash bug (38 rows re-hashed; `verify_ledger.py`).
- **Memory (O-23):** level 1 built (`/remember`, `/forget`, notes + STONE transcripts indexed,
  hits labelled YOUR OWN WORDS); `evals/memory.json` + runner; memory SFT seed (68 rows).
- **Reviews:** fine-tuning post (O-24/O-25: nanochat head-to-head, GRPO on the no-bluff
  objective); LightOnOCR (O-26: GPU test — exact LaTeX where archive.org's text had "P = 45
  watts"; re-OCR the shelf for ~$1–2); English/America (O-27: coverage, not reasoning).
- Art frame (`app/artkit.py`, `/art`), `verify_manifest.py` on the stick, `RELEASE_RUNBOOK.md`,
  `MAKE_IT_YOURS.md`, `eval_flash.sh`, bits-per-byte in `score_heldout.py`, `flash.sh` phase 2
  now a mix. Build log Day 8 evening written.
**Verified:** every number from a results file; ledger 62/62; all four Flash checkpoints load;
`list-pods` empty; billing read after deletion.
**Morning addendum (04:00–09:40 PT):** (1) done — calc seed (923 program-generated rows) and
templated memory seed (~320): Flash re-fit → calc args 0/4→3/6, routing 75→87.5%, and with two
harness fixes (memory entries one chunk each; owner's words first and alone) **memory 0/10→10/10**;
the 59M stays 0/10 (size). (2) O-22: FineWeb slices re-fetched with the dump-date basis (the old
ones were ~23% post-2021 — corrected on the record), Wikipedia sampled from the 2021-12-20 dump
(86k articles / 100M tokens via range requests), Stack Exchange already dated; only The Stack
remains (Eric's call). (4) done. (5) ch. 11 (rent a GPU) drafted. Also: **the stick now ships the
Flash model** (MODEL_STEM knob; live scripted run: Lisbon, memory recall, calc 544); the offline
audit was found to pass on 0 samples and now audits the shipped model with real generation
(PASS, 39 samples / 20 launches / 0 connections). Pod deleted at 04:10 PT; RunPod window spend
$7.54 from billing.
**Open / next:** (1) The Stack decision (O-22, last D-34 item) — Eric; (2) Eric's calls: O-12,
O-19, O-20, O-21, O-25, O-26, O-27; (3) book: glossary appendix, then story chapters after the
window; (4) bits-per-byte + CORE at 1B; (5) nanochat head-to-head (~$0.10) when GPU time is next
authorised.

---

## 2026-09-18 (unattended window 3, day 1) — RunPod proven, Flash training, SFT at scale, the shelf
**Model:** Fable 5.1
**Goal:** Eric away Sep 18–21. Channel = GitHub issues (hourly cron) + Remote Control. Budget: $165
on RunPod (Eric loaded it mid-morning), $0 elsewhere. Guardrails per issue #2.
**Did (in order):**
- Inbox mechanism (issue #1 test, #2 status log). Teacher licence verified (Qwen2.5-7B-Instruct,
  Apache-2.0), downloaded, ~12 tok/s locally; `scripts/generate_synthetic_harness.py` written and
  run: router / tool-answer (tools executed) / grounded / abstain / confident (verifier pass, no
  precise figures) / synthesis / multi-turn (no invented specifics). 3,100+ rows by evening;
  ledger row `harness-synthetic-qwen2.5-7b` (`scripts/ledger_synthetic.py`).
- Retrieval: embedding index attempted (this llama-server build crashes on embedding inputs >
  ~32 tokens); BM25 shipped instead (`app/packsearch.py`). Survival pack FM 21-76 (US Gov PD),
  plant/foraging chapters removed + harness notice.
- Eval: tool-use axis (`evals/tooluse.json`, `evals/run_tooluse.py`) with baselines.
- RunPod: plugin connected (OAuth), SSH key registered, shakedown on an A40 (62k tok/s, resume
  proven, ~$0.08), `docs/RUNPOD_JOB.md`, D-54, D-55. DDP support in `train.py`, rehearsed on
  2×L4 (60.4k tok/s aggregate, ~$0.20). Flash run launched on an A40: 126M params, 2B tokens,
  WSD schedule with the decay on the domain mix, ~38.9k tok/s, ~14 h, ~$7; 3-hourly checkpoint
  fetch cron (job d761dc56). `--grad-accum`, `--compile`, `--schedule wsd`, `--stop-at`,
  `--log-path`; streaming + `--workers` tokenizer (8 workers: 1.63B tokens in 8 min).
- Local SFT retrained on 1,982 conversations: routing 54%→83%, bluff 10%→40%, answered-real
  unchanged (D-56). Generator rebalanced to 40% no-tool router rows.
- Docs/decisions: JOB_1B.md (budget $1,500–2,500 from measured MFU), SUCCESS_METRICS.md,
  README truth, ONLINE-mode plumbing (D2/D8), D-57 (weights update only via reversible adapters),
  O-15 (answerability gate), O-16/17/18 and **D-58 the shelf** (licensed flavors spread thin in
  the anneal); first ten shelf works ledgered from Gutenberg with per-edition PD bases.
- Collateral drafts (landing page + one-pager) on a private artifact and in `site/`.
- Build log Day 8 written.
**Verified:** every number above is from a run log or an eval result file; pods created by the
session were deleted by the session except the Flash pod (running on purpose).
**Evening addendum (18:00–18:45 PT):** the shelf went from 10 to **27 works / 7.46M tokens**:
8 US-Government works from archive.org OCR (FAA PHAK + AFH, Army TM 9-8000, NEETS 1/2/13, Armed
Forces Recipe Service 2003, MUTCD 2009; `scripts/fetch_archive_text.py`, `scripts/ledger_add_text.py`
with measured noise 0.1–3.7% lines dropped), BIPs + EIPs/ERCs at their last pre-2022 commits with
per-document licence checks (`scripts/fetch_bips_eips.py`), 7 more Gutenberg works. OpenStax
excluded (now CC BY-NC-SA; O-19). Shelf wired into `build_mixture.py` (paragraph-sampled, 1.5M
chars/work cap, ≤33% of anneal; measured 30%); shelf anneal tokenized (18.9M tokens) and uploaded
to the pod; `flash_ablation.sh` + `score_heldout.py` written; a watcher on the pod keeps the
stable-end checkpoint so the D-58 ablation costs ~$0.70 (decay phase only). Offline audit re-run
for real (49 samples, 0 connections).
**Open / next:** (1) Flash finishes ~02:00 PT Sep 19 → cron: fetch, eval, D-61 (D-59 book, D-60 integrity findings),
**run the ablation, score both arms on the shared held-out sets**, delete pod. (2) Re-eval the
stick model after the generator finishes (~700/class). (3) Shelf: Britannica 1911 (Gutenberg robot
policy: no bulk crawl; mirror or harvest tool), Supreme Court opinions, Bowditch, USDA guides.
(4) O-12, O-19, O-20 (book licence) and the 1B data volume wait for Eric. (5) Session log: append day-2/3 entries. (6) **The book (D-59)**: `book/OUTLINE.md`; draft DO-IT chapters (corpus, evals) between Flash tasks; Flash results are **D-61**; **D-60**: bitcointalk excluded, spread val split, backbone pre-2022 gap (O-22) must be fixed before the 1B data volume.

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
