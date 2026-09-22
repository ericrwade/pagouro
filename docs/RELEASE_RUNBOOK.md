# Release runbook — section F of the origin ledger, in order

Written 2026-09-18 during the unattended window so the release, when it comes, is a checklist
and not a scramble. Every step here is reversible right up to F13 (public flip + archive) and
F9 (the anchor), which are the two one-way doors. **Nothing in this file has been run.** Status
lives in `docs/ORIGIN_LEDGER.md` section F; update the row when you do the step.

Order matters (`CLAUDE.md` step 7: out-of-order release steps get redone): the weights must be
final before the manifest, the manifest before the signature, the signature before the anchor,
the anchor before anything is published, publication before the public flip.

## F8 — Freeze, hash, sign

1. Freeze: the final GGUF is the one that passed the release gate (D-50: answered-real ≥ 80%,
   bluff rate below every open baseline, all four eval columns in `evals/results/`). Copy the
   eval JSONs into `release/Pagouro/docs/evals/` so the box carries its own numbers.
2. Build: `python scripts/package_release.py` writes `release/Pagouro/` with `MANIFEST.md`
   (SHA-256 + bytes of every file), `MANIFESTO.txt`, `README.md`, and `verify_manifest.py`.
3. Check it on a clean machine or a fresh USB stick: `python verify_manifest.py` in the folder
   (`docs/CHECK_YOUR_COPY.md` is the plain-language walkthrough of steps 3, 4 and the anchor; it ships on the stick)
   must print `VERDICT: every listed file matches the manifest`.
4. Signing key ceremony (Eric, once, offline):
   - `minisign -G -p minisign.pub -s pagouro.key` (minisign is small, audited, no web of trust;
     GPG is the fallback if a reviewer insists). Passphrase in the password manager; the secret
     key never enters the repo, the stick, or a chat.
   - Sign: `minisign -Sm release/Pagouro/MANIFEST.md -s pagouro.key -t "Pagouro release 1.0"`
     → `MANIFEST.md.minisig`. Copy `minisign.pub` into the release folder and paste the public
     key line into `README.md` and `MANIFESTO.txt` (people compare it by eye).
   - `verify_manifest.py` now also checks the signature when `minisign` is on PATH.
5. Zip: `Pagouro-1.0-win64.zip` of the folder. Record its SHA-256; it goes next to every
   download link (F10) and into the GitHub Release notes.

## F9 — Timestamp and anchor (D-14: required, not ceremony)

1. OpenTimestamps first, free: `pip install opentimestamps-client`,
   `ots stamp release/Pagouro/MANIFEST.md` → `MANIFEST.md.ots`. Wait for a Bitcoin confirmation
   (hours), then `ots upgrade MANIFEST.md.ots` and `ots verify MANIFEST.md.ots` prints the block
   height. Ship the `.ots` beside the manifest. Anyone can verify against a Bitcoin node or a
   public calendar.
2. Optional Ordinal inscription of the manifest text (a few KB): dedicated wallet, fresh
   address, low-fee day; measure the fee first and log it in `docs/QSTORAGE_VS_ARWEAVE.md`'s
   companion table (E5). Skip it if the fee is silly; the OTS proof already satisfies D-14.
3. Record block height, txid (if inscribed) and the manifest hash in `README.md`,
   `docs/ORIGIN_LEDGER.md` F9, and the GitHub Release notes. After this the manifest is frozen:
   any change to a shipped byte means a new release, not a patch.

## F10 — Publish (three places, same hash everywhere)

1. Hugging Face: `pagouro/pagouro-1.0` (weights CC BY-SA 4.0, D-31) with the GGUF, `corpus.json`,
   the eval JSONs, `MANIFEST.md`, `.minisig`, `.ots`, and a model card that repeats the two
   numbers (answered-real, bluff rate) and the pre-2022 claim exactly as D-34 words it.
2. Arweave: the zip (+ manifest, signature, ots). Cost measured at upload time and logged (E5).
   Quilibrium mirror per D-40/D-42 if the tooling still works that day; it is additive.
3. GitHub Release on `ericrwade/pagouro`: tag `v1.0`, the zip, the SHA-256 in the notes, the
   Arweave and HF links, the OTS block height. This is "the link" Eric emails.

## F11 — Windows friction

- Unsigned exe: document SmartScreen "More info → Run anyway" with a screenshot in the README.
- Code signing is optional and costs money; if done, sign `pagouro.exe` **before** F8 step 2,
  because signing changes the bytes and therefore the manifest.

## F12 — README stance

The repo README's first paragraph becomes the stick README's: finished artifact, released
as-is, no updates or support promised, fork it. Keep the status table's measured numbers; delete
"milestone N of 9" language. Keep D-50's wording rule: never "won't hallucinate"; bluff rate
beside answered-real, always.

## F13 — The one-way door

1. Final `git status` clean; `.env`, `My_Claude_Conversation.txt`, `API_KEYS*`, `data/`,
   `checkpoints/`, `release/` all absent from history (re-run the history scan from F2).
2. Flip the repo public.
3. Archive it (Settings → Archive): read-only, forkable. Software Heritage picks it up on its
   own; `https://archive.softwareheritage.org/save/` accepts a manual save request too.
4. pagouro.com → 301 to the GitHub Release (F14). DNSSEC and WHOIS privacy already on.

## What is deliberately NOT here

- No auto-update, no telemetry, no "check for a new version" (threat model + D-14 drift rule).
- No token gate, no encrypted weights (F7, rejected in origin).
- No fourth chain (D-14: storage, anchor, payment; three jobs, three chains).
