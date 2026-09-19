# Make it yours — how to improve or customise Pagouro

This file rides along on the stick. Pagouro is released finished, with no updates coming, so the
only way it gets better is if someone changes it. This is literally what you do, from a
five-minute tweak to a full rebuild, with the exact files and commands. Everything below was
run at least once by the build itself; where a number appears it was measured, not guessed.

The ladder, cheapest first:

| Rung | What changes | Needs | Time |
|---|---|---|---|
| 1 | What it can look up | a text file | 1 minute |
| 2 | Which model runs | a `.gguf` file | 1 minute |
| 3 | Web search, threads, context | a JSON file / one flag | 5 minutes |
| 4 | Its prompts and tools | Python, the repo | an hour |
| 5 | Its habits (fine-tune) | Python, the repo, a CPU | an afternoon |
| 6 | What it was trained on | the repo, patience or a rented GPU | days |
| 7 | A bigger model | a rented GPU and money | see `docs/JOB_1B.md` |

The repo is `github.com/ericrwade/pagouro` (Apache 2.0 code, CC BY-SA 4.0 weights). Fork it.
Rungs 1–3 need nothing but this stick.

---

## Rung 1 — Give it things to look up (no code)

`pack_search` is the tool the model uses for facts. It searches every `.txt` in `packs/`
(paragraph chunks, BM25 keyword ranking, ~20 ms a query). **Drop a plain-text file into
`packs/` and it is searchable on the next launch.** A 1.5 MB manual indexes in a third of a
second.

- Plain UTF-8 text with blank lines between paragraphs works best (the chunker splits on blank
  lines). PDFs need converting first (`pdftotext`, or archive.org's `_djvu.txt` for scans).
- Add a row to `packs/README.md` saying what it is and why you may redistribute it, if you plan
  to pass the stick on. Pagouro's whole claim is that every byte has a nameable licence; keep
  that true for anything you ship, and feel free to break it for your own private notes.
- The model **quotes** the packs rather than "knowing" them. That is on purpose: retrieval is
  where verbatim text belongs; training is for concepts and voice. So a pack changes what it
  can answer immediately, without any training.
- Remove a pack by deleting the file. `us-army-fm21-76-survival.txt` deliberately lacks the
  plant chapters and the app adds a notice on foraging questions; if you add a foraging guide,
  also remove that notice in the app (`FORAGING_NOTICE`, rung 4) or you will contradict yourself.

## Rung 2 — Swap the model (no code)

The app loads the first of `model/pagouro-q8_0.gguf`, `pagouro-real-q8_0.gguf`,
`pagouro-q4_k_m.gguf`, `pagouro-real-q4_k_m.gguf`, else any `.gguf` in `model/`. Put a different
GGUF there and it runs — including models that are not Pagouro at all (the harness is plain
llama.cpp underneath).

Two things to know before you do:
- The harness prompts (`app/prompts.py`) and the router grammar are what Pagouro was trained
  on. Another model will still work through the same prompts, but the "doesn't bluff" numbers
  on the box are for **this** model only; measure the new one (rung 5, "Measure it") before
  claiming anything.
- Bigger model, slower answers: the 7B teacher model used during the build generated ~12
  tokens/s on the build machine's CPU, against near-instant answers from the stick model. The
  context gauge adapts automatically to whatever context size the model reports.

## Rung 3 — Switches that need no rebuild

- **Web search.** Create `workspace/online.json` with either
  `{"searxng": "https://your-searxng-host"}` or `{"brave_key": "your-key"}`, then type
  `/online` in the app. Only `web_search` calls go out; the conversation itself still never
  leaves the machine. The exit line lists every network call made, so you can check that.
- **Threads.** The app gives llama-server half your cores, capped at 8. To change it, edit the
  `threads = ...` line in `app/pagouro_app.py` (rung 4) — or use `PAGOURO-BASIC.bat`, the plain
  llama-cli launcher, where `-t N`, `-c N` (context) and `--temp` are ordinary flags you can edit
  in Notepad.
- **Long-term memory.** `/remember <text>` keeps a dated line in `workspace/memory/`; that
  folder, your notes and every STONE transcript are searched beside the packs in later
  sessions and come back labelled as your own words. `/forget` deletes the remembered file.
  Nothing from a SAND session is kept. (`docs/LEARNING_FROM_THE_OWNER.md` explains the two
  deeper levels — adapters trained on your log, continual pretraining — and their guardrails.)
- **Saving chats / letting tools write.** `/stone` writes the chat to `workspace/transcripts/`;
  `/act` lets `write_note` save into `workspace/notes/`. Both default off. Nothing outside
  `workspace/` is ever written by any tool, and that boundary is enforced in code, not by
  the prompt.

## Rung 4 — Change what it says and what it can do (Python, no training)

Clone the repo. The app is one file plus two helpers, standard library only:

- `app/pagouro_app.py` — the harness: context gauge, the three switches, the tool loop.
- `app/prompts.py` — the exact system and router prompts. **They are also in the training
  data**, so if you change a prompt materially, the model is being asked in a dialect it never
  learned; small wording changes are fine, a new tool name is not (see rung 5).
- `app/packsearch.py` — BM25 over the packs. An embedding index is the obvious upgrade; the
  interface (`Packs(root).search(query, k)`) stays the same.

**Add a tool** (the pattern every existing tool follows):

```python
def tool_word_count(text: str, app) -> str:          # takes the argument string, returns text
    return f"{len(text.split())} words"

TOOLS["word_count"] = (tool_word_count, "count the words in a text", False)   # False = does not write
```

Then add `word_count` to `TOOL_NAMES` in `app/prompts.py` and to the router prompt's list. The
GBNF grammar is built from `TOOLS` automatically, so the model can only ever name a real tool.
Run it straight from source while you iterate:

```
python app/pagouro_app.py          # from the repo root: uses tools/llamacpp/llama-server.exe and data/gguf_real/
```

Rebuild the exe when done: `python scripts/package_release.py` (PyInstaller; produces
`release/Pagouro/` with a fresh `MANIFEST.md`). Hard rules the build kept and asks you to keep:
one tool call per turn, tools never get a shell, writes stay inside `workspace/`, and the exit
line must list every file written and every network call, truthfully.

## Rung 5 — Teach it habits: fine-tune on the CPU (an afternoon)

The model learned its manners (say "I have no record of that", call `calc` for arithmetic,
answer from a tool result instead of from memory) from ~5,000 short conversations in `sft/`.
To change a habit, add conversations and re-run the last stages of the pipeline.

**Data format** (`sft/*.jsonl`, one conversation per line; roles system/user/tool/assistant;
loss is taken on assistant turns only):

```json
{"kind": "router", "messages": [
  {"role": "system", "content": "<the ROUTER_PROMPT string from app/prompts.py, verbatim>"},
  {"role": "user", "content": "How many words is this: the quick brown fox"},
  {"role": "assistant", "content": "{\"tool\":\"word_count\",\"arguments\":\"the quick brown fox\"}"}]}
{"kind": "tool_answer", "messages": [
  {"role": "system", "content": "<SYSTEM_PROMPT with the date filled in>"},
  {"role": "user", "content": "How many words is this: the quick brown fox"},
  {"role": "tool", "content": "word_count: 4 words"},
  {"role": "assistant", "content": "Four words."}]}
```

Put your file next to the others and add one line to `load_examples()` in
`scripts/train_sft.py`. Balance matters more than volume: for every "call the tool" example
give it a "this needs no tool" example, or it learns to always call something (that mistake is
in the build log). Then:

```
SKIP_CORPUS=1 START_STAGE=6 THREADS=8 SFT_STEPS=3000 bash scripts/master_pipeline.sh
```

Stage 6 fine-tunes from `checkpoints/real_anneal.pt` (the pretrained weights, before any
manners), stage 7 exports and quantises the GGUF and checks it reproduces the checkpoint's
output, stage 8 runs the frozen evals, stage 9 the offline audit, stage 10 packages, stage 11
copies to the stick if one is plugged in (it refuses while the app is running from it). Steps:
~1 epoch per (conversations ÷ 4); 3–4 epochs is what the build used. Measured on the build
machine at `THREADS=8`: 2,000 SFT steps in 44 minutes.

**Measure it.** Never ship a habit change without the numbers:

```
python evals/run_eval.py --model data/gguf_real/pagouro-real-q8_0.gguf --label mine --tokens 140
python evals/run_tooluse.py --model data/gguf_real/pagouro-real-q8_0.gguf --label mine
```

Four columns come out: answered-real, bluff rate, deflection, tool routing. Publish bluff rate
**beside** answered-real, always — a model that says nothing never bluffs. The wording rule
in `docs/DECISIONS.md` D-50 applies to anything you call Pagouro: "doesn't bluff, measured",
never "won't hallucinate".

## Rung 6 — Change what it was trained on (days, or a rented GPU)

The corpus is a recipe, not a download: `corpus.json` lists every source, licence, size and
hash, and `scripts/` fetches and cleans each one. To add a source:

1. Find its licence line. No nameable licence → it does not go in. NC and ND licences → out
   (the weights are CC BY-SA and could not carry them). Published or collected before
   2022-01-01, dated on the row (the "before generative AI" claim, D-34).
2. Fetch + ledger it with the tool that fits: `scripts/fetch_gutenberg.py` (Gutenberg, per-
   edition public-domain basis required), `scripts/fetch_archive_text.py` + `scripts/ledger_add_text.py`
   (archive.org OCR text, with the cleaning stats written on the row), `scripts/fetch_data.py`
   (Hugging Face datasets; refuses anything without a licence field).
3. Decide where it goes: the pretrain backbone (`PRETRAIN_MIX` in `scripts/build_mixture.py`)
   or the anneal (the last 10% of training, where domain flavour lives). Small special-interest
   texts go on the "shelf" (row `slice` = `shelf (D-58): anneal-only flavor`): they are
   paragraph-sampled into the anneal, capped per work so nothing dominates.
4. `python scripts/build_mixture.py` (or `--anneal-only` for a shelf-only change), tokenize,
   and run the pipeline from stage 3 or 4: `RESUME_PRETRAIN=1` continues a checkpoint;
   without it stage 4 starts from random weights (and deletes the old checkpoint — read the
   comment at the top of `scripts/master_pipeline.sh` first).

Costs, measured: this CPU trains ~960 tokens/s (a 2B-token run is weeks); a rented A40 did
38,000–62,000 tokens/s (`docs/RUNPOD_JOB.md`, ~$0.50/h, the 126M "Flash" model cost ~$7 for
2B tokens); two L4s in DDP did 60,000 tokens/s aggregate.

## Rung 7 — A bigger model

`docs/JOB_1B.md` is the full plan for the 1B model on 8×H100 (budget $1,500–2,500 from
measured throughput), including the data volume, the WSD schedule, the 8k-context decay, and
the delete-the-pod checklist. `scripts/runpod/` has the bundle, setup, shakedown and flash
scripts that were actually run.

---

## What you are agreeing to when you change it

- **Licences.** Code Apache 2.0; weights CC BY-SA 4.0, so a fine-tuned or retrained Pagouro
  you distribute is also CC BY-SA 4.0 with attribution. Your packs and your SFT data are yours.
- **The ledger rule.** If you keep the name Pagouro, keep every training byte on `corpus.json`
  with a licence you can name. One unlicensed source and the claim on the box is false.
- **The privacy claim.** `docs/THREAT_MODEL.md` says exactly what "offline" does and does not
  protect. Do not let a change (a new tool, an update check, telemetry) quietly widen the
  network surface; the exit line and `evals/offline_audit.py` are there to catch it.
- **Numbers, not adjectives.** Whatever you build, run the evals and print both numbers.

## Checking a stick someone gave you

`python verify_manifest.py` in the release folder checks every file's hash against
`MANIFEST.md` (and the signature, when a release is signed). A modified Pagouro is welcome;
a modified Pagouro pretending to be the original is what the manifest exists to catch.
