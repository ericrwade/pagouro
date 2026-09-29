# Pagouro 1.0 — release notes (draft; links and hashes filled at F10)

**A one-billion-parameter language model on a USB stick, built from scratch on a licensed, dated corpus, that says when it does not know.** Eric Wade, with Claude (Anthropic).

## The two numbers
On the frozen 100-item honesty sets (written before the model existed; `evals/`): it invents an answer to **13 %** of unanswerable questions and answers **82 %** of real questions correctly (small open models: 50–57 % / 87–93 %; frontier models: 23–27 % / 97 %). The test ships in this repository — run it on anything.

## What is in the zip
`Pagouro-1.0-win64.zip` — the folder that goes on a stick: `pagouro.exe` (the harness), `llama-server.exe`, the model (`pagouro-q8_0.gguf`, 1,102,230,720 bytes, SHA-256 `9336cce0…`; `pagouro-q4_k_m.gguf` beside it), the reference packs, skills, `agents/` (use it from Hermes / OpenClaw / IronClaw), the corpus ledger, the eval results, `MANIFEST.md` with every file's hash, `VERIFY.bat` (no Python needed), `ABOUT.md`, `facts.json`, `THREAT_MODEL.md`.

- Zip SHA-256: `96debc3eef9ae95a1582d2b7940d227f0735ae01a2ba024bea6f2d3318b688b7`
- Manifest SHA-256: `02a618fc07bdfdc84b40eefe28cbf6080dfba856dee7eef2c8164223abd90f71` · signature `MANIFEST.md.minisig` (public key: `RWQe8tvI6RCE2uMbuILC9/rEr6bNZdcOA+WC7dHtObLE94ovGk8xuFlG`)
- Bitcoin timestamp (OpenTimestamps): `968959` (`MANIFEST.md.ots`)
- Weights and ledger on Hugging Face: `HF_LINK` · permanent copy on Arweave: `6XjlZGVYmp1mDjfcwHRPpr8qe8xOpLHCAMDoB5WXGBk`

## On Arweave (permanent; uploaded 2026-09-29 via Turbo, 22.3 credits ≈ $109 for the lot)

| file | link |
|---|---|
| `MANIFEST_v1.0.md` | `https://arweave.net/RVpjbcNsXcsIJgStjWvLp5pSFuUu_gqew9ONiB4NNdk` |
| `MANIFEST_v1.0.md.minisig` | `https://arweave.net/Z-UZLzRPcuqYaHsYflabNPNchIU9gTdjRA1x6-UjNvY` |
| `MANIFEST_v1.0.md.ots` | `https://arweave.net/xzEhG3Fw_L4jkkXt0fuaLAeEKGx_Ky5opiK9MCwfBr0` |
| `Pagouro-1.0-win64.zip` | `https://arweave.net/6XjlZGVYmp1mDjfcwHRPpr8qe8xOpLHCAMDoB5WXGBk` |
| `Pagouro-1.0-win64.zip.sha256` | `https://arweave.net/Uv_1bzvvdnTB7psvJckA8YpqH4cQ4aNPNmqsUGQosuM` |
| `facts.json` | `https://arweave.net/TKHvGhAZej_dprU6VxqYSvFy8TxN-N_h-jb-Q25_JEI` |
| `pagouro.pub` | `https://arweave.net/T07Aeq2tQYOmmFaVQNzIa_aBI48CwcoIbMPfbxKretU` |

Each file's bytes were fetched back from a gateway and hashed against the originals (the six small files from `arweave.net`; the zip from `turbo-gateway.com` on upload day — `arweave.net` serves large bundles after indexing).

## Requirements
Any 64-bit Windows machine, CPU only, no internet, no account. First start from a USB stick can take a minute; on an Intel N100 laptop the first answer took 10–20 s. Windows SmartScreen: *More info → Run anyway* (the exe is not code-signed; the manifest, signature and timestamp are what vouch for it — `docs/CHECK_YOUR_COPY.md`).

## Licences
Weights CC BY-SA 4.0 · code Apache 2.0 · corpus rows as listed in `corpus.json`. No watermark; no claim on outputs.

## If it is useful
This was built by one person and cost about $1,900 in rented compute. It is finished and free. If it is useful to you: fork it, or send a small sponsorship toward what it cost — https://github.com/sponsors/ericrwade.

## Finished
One release, frozen. No updates, no support, no telemetry, no roadmap. Fork it — the recipe is complete: `docs/`, `BUILD_LOG.md`, the book (`book/`).
