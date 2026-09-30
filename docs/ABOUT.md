# About Pagouro

*Draft 3, 2026-09-26 (O-43; key facts from the measured files, D-96). The source for the public "About" page and the model card. The
structure follows a conventional About-page recipe Eric sent from the road (one-sentence value
proposition, what it does, what makes it different, who it is for, who made it, how it works,
a machine-readable key-facts table, FAQ), rewritten for a finished artefact rather than a
company: where the recipe assumes a sales team, this page says plainly that there is none.
Every claim here is bound by D-50 (never "does not hallucinate"; bluff rate beside answered-real)
and `docs/THREAT_MODEL.md`. Values marked TBD are filled at release from measured files.*

## Pagouro in one sentence

Pagouro is an offline language model on a USB stick, built from scratch on a licensed, dated
corpus, that tells you when it does not know — for anyone who wants an assistant whose promises
they can check rather than trust.

## What Pagouro does

### Answers, or says it cannot
A one-billion-parameter model answers questions and writes text on your machine. When a question
has no answer it can stand behind, it says so; how often it invents one instead is the first
number on the box, measured on a frozen test that ships with it.

### Reads your documents and cites them
A shelf of reference packs — public-domain and licensed books, manuals, your own files — is
searched at question time. When the answer comes from the shelf, it says which work and where.

### Remembers what you tell it, on your machine
Things you tell it come back later, labelled as your own words. The memory is a file on the
stick; nothing about you leaves the computer.

### Checks itself when you ask it to
`/careful` re-asks each question five times and only stands behind an answer when the answers
agree; when they don't, it tells you and calls the answer a guess. A small model's honest
confidence signal, built from its own consistency.

### Runs small tools
Five sandboxed tools (calculator, dates, units, dice, recipe scaling) that the model routes to
rather than guessing at arithmetic. You can add your own; the recipe is in the repository.

### Has a sibling that draws
Pagouro BE, released the same day, draws Belle Époque posters from a sentence, on CPU, offline, from the
same kind of stick — a fine-tune of a Creative-Commons-only base on 3,043 ledgered public-domain posters,
with its own frozen gate and its own honest numbers (it draws the asked subject 85 times in 100 by a person's
count, and adds unreadable lettering to most pictures). Text stays here; pictures live there.

### Ships with its recipe
The corpus ledger, the training code, every decision and every mistake (the book) are on the
stick and in the repository. You can rebuild it, or fork it into a model around your own texts.

## What makes Pagouro different

The four promises below are each a discipline rather than a budget, which is why a one-person
project can hold all of them and larger releases hold none of them together. `docs/WHY.md` is
the long form.

### Licensed, row by row
Every training byte has a licence you can name and a row in `corpus.json` with a hash. OLMo
(AI2) and the Common Pile / Comma models (EleutherAI) publish their data too; Pagouro is the
smaller relative that also records, per row, what was *removed* and why.

### Dated before 2022
Everything it read was written or collected before 1 January 2022, with the date basis on every
row. Few releases state a training cut-off at all; none we know of states it per row, and a
crawl-scale corpus cannot.

### Honesty measured first
The headline number is the rate at which it invents answers to unanswerable questions, printed
beside the rate at which it answers real ones — because a model that says nothing would score
perfectly on the first alone. The test ships; run it on any model.

### Finished
Released once, frozen, signed, hash-anchored, mirrored. No account, no update check, no
telemetry. A maintained product drifts; a frozen one can be verified by a stranger on a hostile
network (`docs/CHECK_YOUR_COPY.md`).

### Your words are yours
No watermark in its output — the program that writes every word is on the stick, read it — and
the project claims no rights in what it writes for you. Some assistants do one or both.

## Who Pagouro is for

- People who need their questions to stay on their own machine, and need to verify that rather
  than trust it — journalists, lawyers, clinicians, anyone whose questions are someone else's
  risk.
- Writers and researchers who want a reader for their own shelf of documents that cites its
  source.
- Teachers and students who want a model small enough to understand end to end, with its whole
  recipe.
- People without reliable internet, or who do not want an account.
- Anyone who wants to fork a model around their own tradition's texts and keep the licence
  claim intact.

## Who made it

One person and one model. Eric Wade set the rules, chose every source, made every decision that
is marked as his in `docs/DECISIONS.md`, and paid for the cards. The engineering, writing and
measuring were done by Claude (Anthropic) in sessions Eric directed, mostly while he was
travelling and reading the reports on his phone. The public origin story is `docs/ORIGIN.md`;
the build log is the unedited daily record; the book *Make Your Own AI* is the story with the
numbers. The credit line is Eric's (D-86): **Eric Wade, with Claude (Anthropic)**. In his words: "This is a personal project which has been built as free and open-source software and has no connection to myself after launch, nor to my employer at any time." *(Founder links and
handles: `docs/HANDLES.md`, F12 at release.)*

## Disclosures

What it cost: $1,778.97 for the 1B training run and about $1,915 all-in with the research rounds
that followed it (every figure read from the RunPod account after each pod was deleted, and
listed by day in `BUILD_LOG.md`); the domain; a USB stick. No grant, no sponsor, no investor.
There is no token and there will not be one: a coin would give the project a reason to keep
promising things after it is finished, which is the opposite of the promise it makes. Money can be
given to it — a GitHub Sponsors link toward what the compute cost — but nothing can be bought from it. Eric has mined bitcoin and uses crypto and blockchain as often as he can; he does not itemise his holdings. The model was built by one
person and one AI model; the AI's company had no say in it and did not pay for it.

## How Pagouro works — what to expect

There is no team, no support channel, no response time and no roadmap. That is the point, not
an apology: the artefact is finished, and the only promise is that it will keep being exactly
what it was when its hash was anchored. The repository accepts issues and reads them; it
promises nothing about answering. If you want it changed, fork it — the recipe is complete.

## Key facts

| Field | Value |
|---|---|
| Name | Pagouro |
| Type | Offline language model and application on a USB stick |
| Parameters | 968,968,192 (counted by the training script; the file never grows) |
| Architecture | Decoder-only transformer, 20 layers, dim 2048, 16 heads / 4 KV heads, context 8,192 tokens |
| Training data | 99,724,809,408 tokens; FineWeb-Edu 91.6 %, Stack Exchange 7.7 %, dated code 0.7 % (×3); anneal on a licensed shelf |
| Date basis | Every row written or collected before 2022-01-01; basis stated per row |
| Corpus ledger | `corpus.json` — source, licence, date basis, tokens, SHA-256 per row |
| Weights licence | CC BY-SA 4.0 (D-31; share-alike sources are in the corpus and it says so) |
| Code licence | Apache 2.0 |
| Book licence | Story chapters all rights reserved; do-it chapters CC BY-SA 4.0 (D-64) |
| Tokenizer | 32,768-entry BPE, trained on the licensed corpus |
| Trained on | 8× NVIDIA H100 SXM, rented (RunPod, Montreal), 2026-09-22 → 09-24; bill $1,778.97 read from the account after the pod was deleted |
| Honesty score | Bluff rate 13 % on the 100-item unanswerable set; answered-real 82 % on the 100-item real set (D-96; measured at the shipped decode, `evals/results/pagouro-1b-soup-g3-cp-4-trim2__*`) |
| File on the stick | `model/pagouro-q8_0.gguf`, 1,102,230,720 bytes, SHA-256 `9336cce0647dc5a0a7346163fa45d97ec18fd9a73cb3048ebd810643f7585c05` (the app runs this one; `pagouro-q4_k_m.gguf`, 633,976,000 bytes, ships beside it and measures 16 % / 78 % — the smaller file, not the measured model) |
| Requirements | Any 64-bit Windows/Linux/macOS machine; runs on CPU; no internet, no account |
| Price | Free. Tip jar. |
| Maintenance | None. Frozen at release; verify with `docs/CHECK_YOUR_COPY.md` |
| Telemetry | None. See `docs/THREAT_MODEL.md` for what "private" does and does not cover |
| Release | 2026-09-29, v1.0 — https://github.com/ericrwade/pagouro/releases/tag/v1.0; manifest signed and timestamped on Bitcoin block 968959; Arweave copy https://arweave.net/6XjlZGVYmp1mDjfcwHRPpr8qe8xOpLHCAMDoB5WXGBk |
| Relatives | OLMo (AI2), Common Pile / Comma (EleutherAI) — larger, open; Pagouro borrows from both where their sources meet its rules |
| Sibling | Pagouro BE 1.0 — the Belle Époque poster image model, same rules, same key: https://github.com/ericrwade/pagouro-be · https://huggingface.co/Pagouro/pagouro-be-1.0 |
| Made by | Eric Wade, with Claude (Anthropic) |
| Repository | https://github.com/ericrwade/pagouro (public; frozen at tag `v1.0`; issues open for receipts) |
| Mirror | https://pagouro.qstorage.quilibrium.com/ — Quilibrium QStorage: the link page, the signing key and every receipt (manifest, signature, timestamp proof, facts) for both models |

*The same table ships as `facts.json` on the stick and in the model card, so that a program —
or another model — describing Pagouro has one source to read.*

## Frequently asked questions

### Is it as good as ChatGPT / Claude / Gemini?
No. It is about a thousandth the size and trained on a hundredth of the data, and it loses on
every capability test. It is for the promises above, not for capability.

### Can it make images, or read them?
No. It is a text model: text in, text out. No images, audio, video, camera, microphone, file
browser or web. Asked for a picture it may claim it can — that is the bluff the box measures, not a
feature. The project's artwork was made by people and other tools.

### Does it hallucinate?
Yes; every language model does. What Pagouro does is measure how often, on a frozen test, and
print the number beside how often it answers real questions correctly. It never claims not to.

### Can it reason — word problems, multi-step arithmetic?
Barely, today. On a program-checked held-out set of school word problems (`evals/reasoning_heldout.jsonl`,
eight kinds, exact keys, 320 problems) the shipped model solved 11 without tools; it answers in one
line and does not work anything out. Plain arithmetic goes to the calculator tool instead, which is exact. The
set, the checker and the training recipe for the next round ship in the repository, so the number
can be re-measured on any later build.

### Is "1B" really one billion, or "1B+"?
968,968,192 weights, counted. Nothing at run time makes it more. The shelf it reads from adds
knowledge to its answers, not weight to the model; the box says 1B.

### Why not use Wikipedia?
It was in the plan and it was dropped during the build (D-84): the fetcher was too slow at
scale and Eric chose to build without it. The trade — a little less plain-fact coverage — is
recorded, and measured on the calibration set.

### Can I check that my copy is genuine?
Yes, without being technical: `docs/CHECK_YOUR_COPY.md` walks through it. The manifest's hash is
anchored where it cannot be altered; your copy either matches it or it is not Pagouro.

### Does it watermark or claim what it writes for me?
No and no. The code that produces every word is on the stick. The project asserts no rights in
its outputs. It cannot promise the output is free of anyone else's rights — a model can repeat a
sentence it read — and when it quotes the shelf it names the source.

### Why did a one-person project rent GPUs instead of a cheaper market?
Because the job comes first: the decentralised markets could not answer, on the day, where two
hundred gigabytes would live or whether eight cards came as one machine (`docs/GPU_PROVIDERS.md`).
The analysis is in the book.

### Why bother, when OLMo exists?
OLMo is the standard for open research models and is far more capable. It does not claim a
per-row licence, a pre-2022 date basis, honesty as its first number, or a frozen release — and
those four together are what Pagouro is.

### Can I make it about my own texts?
Yes. `docs/MAKE_IT_YOURS.md` has seven rungs, from dropping files on the shelf to a full retrain
on your own ledger, and the book's do-it chapters walk each one.
