# Pagouro 1.0 — release notes (draft; links and hashes filled at F10)

**A one-billion-parameter language model on a USB stick, built from scratch on a licensed, dated corpus, that says when it does not know.** Eric Wade, with Claude (Anthropic).

## The two numbers
On the frozen 100-item honesty sets (written before the model existed; `evals/`): it invents an answer to **13 %** of unanswerable questions and answers **82 %** of real questions correctly (small open models: 50–57 % / 87–93 %; frontier models: 23–27 % / 97 %). The test ships in this repository — run it on anything.

## What is in the zip
`Pagouro-1.0-win64.zip` — the folder that goes on a stick: `pagouro.exe` (the harness), `llama-server.exe`, the model (`pagouro-q8_0.gguf`, 1,102,230,720 bytes, SHA-256 `9336cce0…`; `pagouro-q4_k_m.gguf` beside it), the reference packs, skills, `agents/` (use it from Hermes / OpenClaw / IronClaw), the corpus ledger, the eval results, `MANIFEST.md` with every file's hash, `VERIFY.bat` (no Python needed), `ABOUT.md`, `facts.json`, `THREAT_MODEL.md`.

- Zip SHA-256: `ZIP_SHA256`
- Manifest SHA-256: `02a618fc07bdfdc84b40eefe28cbf6080dfba856dee7eef2c8164223abd90f71` · signature `MANIFEST.md.minisig` (public key: `RWQe8tvI6RCE2uMbuILC9/rEr6bNZdcOA+WC7dHtObLE94ovGk8xuFlG`)
- Bitcoin timestamp (OpenTimestamps): `OTS_BLOCK` (`MANIFEST.md.ots`)
- Weights and ledger on Hugging Face: `HF_LINK` · permanent copy on Arweave: `ARWEAVE_TXID`

## Requirements
Any 64-bit Windows machine, CPU only, no internet, no account. First start from a USB stick can take a minute; on an Intel N100 laptop the first answer took 10–20 s. Windows SmartScreen: *More info → Run anyway* (the exe is not code-signed; the manifest, signature and timestamp are what vouch for it — `docs/CHECK_YOUR_COPY.md`).

## Licences
Weights CC BY-SA 4.0 · code Apache 2.0 · corpus rows as listed in `corpus.json`. No watermark; no claim on outputs.

## Finished
One release, frozen. No updates, no support, no telemetry, no roadmap. Fork it — the recipe is complete: `docs/`, `BUILD_LOG.md`, the book (`book/`).
