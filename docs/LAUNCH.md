# Launch — the one text, and the one recording

*Drafted 2026-09-26 (TO_DONE 6.2, 6.3) under D-94: bare-minimum marketing; a proof that it can be
done and be useful; the niche of 100 % documented and self-contained; no superlatives, no
competitive claims — every sentence checkable (D-50). Numbers are the shipped ones (`facts.json`);
if round 4 changes them, change them here. The links are filled at F10. Eric posts; nothing here
goes out before F13.*

## The text (reused everywhere; trim to the platform, never embellish)

**Title:** Pagouro — a 1B language model on a USB stick, built from scratch on a licensed, dated
corpus, that says when it doesn't know

**Body:**

I built a one-billion-parameter language model from random weights on a corpus where every byte
has a licence you can name and a date before 2022, and put it on a USB stick with everything it
needs. It runs on CPU, offline, with no account. It is about a thousandth the size of the models
you use and loses to them on every capability test. What it has instead is four promises a
stranger can check, and the checks ship with it:

- **Licensed:** every training source is a row in `corpus.json` — licence, date basis, token count,
  hash of the slice — including the rows that were removed and why.
- **Dated:** everything it read was written or collected before 1 January 2022, per row.
- **Honesty measured:** on a frozen 100-question test of unanswerable questions it invents an
  answer **13 %** of the time (small open models: 50–57 %; frontier models: 23–27 % on the same
  test), and it answers **82 %** of a matching set of real questions correctly. Both numbers always
  together, because a model that says nothing would ace the first alone. The test is in the repo;
  run it on anything.
- **Finished:** one release, signed, hash-anchored on Bitcoin, mirrored on Arweave. No updates, no
  telemetry, no watermark, no claim on what it writes for you.

It does small things well (quotes from a passage you give it, routes arithmetic to a calculator,
remembers what you told it, on your machine) and reasons badly (11 of 320 school word problems
without tools — the number is on the box too). The whole build — every decision, every mistake,
$1,778.97 for the run — is in the repository and in a book that ships on the stick.

It's a proof that a model can be fully documented and fully self-contained and still be useful.
If you want a frontier model, use one. If you want to know exactly what you're talking to, this
is the niche, and this is the first thing in it.

Download (zip + SHA-256): `<GitHub Release link>` · Weights: `<Hugging Face link>` · Permanent copy:
`<Arweave txid>` · Verify your copy: `docs/CHECK_YOUR_COPY.md`. Eric Wade, with Claude (Anthropic).

## Per platform

| Where | What changes |
|---|---|
| Show HN | Title as above (≤ 80 chars: "Show HN: Pagouro – a 1B model on a USB stick, licensed, dated, honesty-measured"); body verbatim; answer questions with numbers and file paths, never adjectives |
| r/LocalLLaMA | Same body; add the GGUF sizes (q8_0 1.10 GB, q4_k_m 634 MB) and "runs on any CPU, `-ngl 0`" up front; expect "why not fine-tune Llama" — the answer is the ledger (D-9) |
| X / Bluesky / Mastodon | Three lines: the one-sentence description, the two numbers, the link. The 90-second recording attached |
| Hugging Face (model page) | The model card *is* the post (`docs/MODEL_CARD.md`) |
| Email to friends | The body, plus "run `python verify_manifest.py` in the folder and tell me what it prints" — the first independent receipts (E4) |

## The 90-second recording (6.3) — shot list

Screen only, no voice-over needed; captions are the harness's own text. One take, no cuts.

1. **0:00** File Explorer on the stick: the folder, `PAGOURO.bat`, `MANIFEST.md`. Double-click.
2. **0:05** The loading line ("still loading the model … a USB stick reads slowly the first time" if it
   shows) → the banner. Caption: *no install, no internet, no account.*
3. **0:20** `What is the capital of Portugal?` → Lisbon.
4. **0:28** `Who won the 1972 Dunmoral Medal for Coastal Hydrology?` → "I have no record…" Caption:
   *it says when it doesn't know — 87 times in 100 on the frozen test; the other 13 are on the box.*
5. **0:40** `/careful` then `Who wrote The Wealth of Nations?` → the five re-asks agree → the answer.
   Caption: *its own consistency as a confidence signal.*
6. **0:55** `What is 17 times 23?` → the calc tool line → 391. Caption: *arithmetic goes to a tool.*
7. **1:05** `/exit` → "Nothing was written to disk. No network calls were made."
8. **1:10** A terminal in the same folder: `python verify_manifest.py` → `VERDICT: every listed file
   matches the manifest`. Caption: *the manifest hash is timestamped on Bitcoin — check yours.*
9. **1:25** End card: the mark, the two numbers, the link. *Eric Wade, with Claude (Anthropic).*

What not to show: any prompt the model gets wrong "on camera" is fine to leave in — cutting it would
be the one thing the project must not do. If a take shows a bluff, keep it and caption it.
