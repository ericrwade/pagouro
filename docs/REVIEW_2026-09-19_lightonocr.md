# Review: LightOnOCR-2-1B — "a powerful 1B": is it useful to us? (O-26)

Eric, 2026-09-19 01:30 PT: https://huggingface.co/lightonai/LightOnOCR-2-1B

## What it is (from the model card, checked)

Not a general language model. A **1B-parameter vision-language OCR model**: a vision encoder plus
a small decoder, trained end to end to turn page images (PDFs, scans) into clean, naturally
ordered text with Markdown, LaTeX for maths and HTML for tables. Apache-2.0. OlmOCR-Bench
83.2 overall, 89.6 on arXiv maths, 85.6 on old scanned maths; 5.71 pages/s on one H100;
"3.3× faster than Chandra OCR, 1.7× faster than OlmOCR". Eleven languages. Its training set is
released (`lightonai/LightOnOCR-mix-0126`, 16.4M pages from the PDFA corpus, Common Crawl
2021-31) with **model-generated labels** ("distillation using a state-of-the-art VLM teacher";
"targets may contain occasional hallucinations") under an "other" licence tied to Common
Crawl's and Digital Corpora's terms.

So "powerful 1B" is true of it *as an OCR engine*. It is evidence for D-6's bet — a
1B-class model can do serious specialised work — but it is not a candidate for Pagouro's
weights, and not a comparison point for Pagouro's claims.

## Where it helps: our OCR problem is real and this is the tool for it

The shelf's technical works (D-58) come from archive.org's own OCR text: 0.1–3.7% of lines
dropped as garbage per file, rotated page headers, and — the part the cleaner cannot fix —
**formulas and tables reduced to soup**. The NEETS page checked tonight (module 1, page 120)
is fractions and worked examples (`I = E/R`, `I = 2 volts / 2 ohms`); the archive.org text of
that page is not usable as a worked example. The recipe cards and the canning process tables
are the same story. A page-level OCR model that emits LaTeX and HTML tables turns those pages
from noise into exactly the reasoning-shaped text the shelf was meant to add (O-17).

The rights position does not change: the OCR engine adds no rights of its own; the output's
status is the source's (US Government works, public domain), and the row states which OCR
produced the text and when. It does not touch D-34 either — archive.org's text was also
machine-made, from the same pre-2022 scans.

**Cost, measured against what is known:** the shelf's OCR'd works are ~12,000 pages. At the
card's 5.7 pages/s on an H100 that is 35 minutes; on the A40 we rent at $0.49/h, call it two
hours and ~$1. Fetching page images from archive.org is the slower part.

## The test tonight, and what blocked it

- Official GGUFs exist (`ggml-org/LightOnOCR-1B-1025-GGUF`: 805 MB model + 437 MB mmproj, Q8)
  and llama.cpp supports the model through its multimodal path (`llama-mtmd-cli`, which our
  shipped build includes).
- Ran it on the NEETS page on this machine, CPU, 4 threads: **the process fail-fasts
  (0xC0000409) in the vision encoder**, at any image size, ~2 s in. That is the same failure
  class we hit on this build's embedding path on 2026-09-18 (crash on inputs over ~32 tokens).
  It is our llama.cpp build (0.4.1-dev, build 11005) on this CPU, not the model.
- Next: run the same page on the pod's GPU with the HF weights during the ablation window
  (the pod is alive anyway; no extra rental), and compare the output with archive.org's text
  for that page. If it is as good as the card says, the shelf re-OCR is a ~$1 job.

## The GPU test (done 02:05 AM PT, on the pod, transformers 5.17, bf16, A40)

`scripts/ocr_page.py` (uses the model's own `LightOnOcrForConditionalGeneration` /
`LightOnOcrProcessor`; the generic auto-classes load it with missing weights and return "no
visible content" — a trap worth recording). Two pages, outputs in `docs/samples/ocr/`:

- **NEETS module 1, page 120 (formulas):** 1,107 chars in 12.9 s. Every equation correct in
  LaTeX (`I = rac{2 	ext{ volts}}{2 	ext{ ohms}}`, `P = 4.5 	ext{ watts}`). The archive.org text
  of the same page (`neets-p120.archive-org.txt`) reads **"P = 45 watts"** where the page says
  4.5, "I = -", "P- HI", "j _ 2 volts" — i.e. the training text we ledgered carries a *wrong
  number*, not just noise. That is the strongest argument for the re-OCR: garbage lines were
  measured and dropped, but a plausible wrong number passes every filter.
- **Armed Forces Recipe Service, page 300 (a recipe card):** 1,724 chars in 19.7 s; the
  nutrition line and the ingredient list come out as proper HTML tables with headers.

Speed with plain transformers, one page at a time, is 13–20 s/page on the A40 — ~50 h for the
~12k shelf pages, so the re-OCR job needs batching or vLLM (the card's 5.7 pages/s is vLLM on an
H100). Plan for ~2 h and ~$1–2 on the A40 with vLLM; verify the rate on 100 pages first.

## Two smaller things it suggests

1. **An offline "read this scan" tool for the stick** (`read_file` for images/PDF pages).
   A 1.2 GB Q8 pair is too big to ship beside the model on a 1 GB stick; it could be an
   optional download the harness detects, like the BYO search provider. Only worth it once the
   llama.cpp vision path works on the shipped build — which is now a known defect to retest
   with each build update.
2. **The book:** a paragraph in the corpus chapter on why OCR quality is a provenance
   question — the cleaning stats on the row are the honest version of "we fixed the scans".

## Verdict

Yes, helpful — as a tool on the corpus, not as a model in the product. Concretely: re-OCR the
shelf's scanned technical works with it on a rented GPU (~$1), write the OCR engine on each
row, and re-measure the cleaning stats; expect the NEETS formulas and the recipe/canning
tables to become usable. The GPU test passed decisively (formulas exact where archive.org's text had a wrong number);
the re-OCR should be scheduled, with vLLM for throughput. Logged as **O-26**.
