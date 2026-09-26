# Pagouro — from today to "100 % done"

*Compiled 2026-09-25 (Eric: "everything that needs to happen for us to put this to bed"). One line per task,
in the order it has to happen. Dates are targets, not promises; a task with a date depends on the one above
it finishing. Costs are what a task spends beyond the RunPod balance already on the account (≈ $150 on
2026-09-25). "Who" is who has to act: **Eric** = only Eric can (money, accounts, signatures, public flips);
**Claude** = done in session, Eric reads the report. The authority for any conflict is `docs/DECISIONS.md`;
the release order is `docs/ORIGIN_LEDGER.md` section F and `docs/RELEASE_RUNBOOK.md`. Update this file as
rows close; it is the one page to open when asking "what is left?".*

## 0. Where we are (2026-09-25, 12:00 PT)

| Done | Evidence |
|---|---|
| 1B model trained from scratch on the licensed, dated corpus (99.7 B tokens, $1,778.97) | D-85; `data/out_1b/`, `runs/pagouro-1b.jsonl` |
| Post-trained (SFT + four GRPO rounds, the last a 60/40 soup), decode settled, on the stick | D-87 → D-96; stick manifest 112/112, sha `81d6ebb3…` |
| Numbers on the box: **bluff 13 % / answered-real 83 %**, multi-turn clean (D-96) | `evals/results/pagouro-1b-soup-g3-cp-4__*`, `facts.json` |
| App (harness, tools, packs, memory, `/careful`), docs, threat model, corpus ledger, book ch. 0–13 draft 1 | repo `ericrwade/pagouro` (private) |
| Handles checked (`pagouro` free everywhere probed), pagouro.com Eric's | `docs/HANDLES.md` |

## 1. Finish the model (this week)

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 1.1 | ~~Sep 25~~ DONE | Research round 2 (pod `e333vfwcjuo4ej`, $8.66, deleted): SFT-v3 + GRPO-5 home and hash-verified | $8.66 | Claude |
| 1.2 | ~~Sep 25~~ DONE | Round 2 measured (D-95): SFT-v3 43/77, GRPO-5 49/84, reasoning 18 → 93–94 of 320, soups 28/81 and 37/81 — **does not ship** | $0 | Claude |
| 1.3 | ~~Sep 26~~ DONE | Shipped model = GRPO-3 (22 / 81), unchanged; stick current; facts / card / ABOUT agree (D-95) | $0 | Claude |
| 1.4 | ~~Sep 26~~ DONE | Rounds 3 and 4 (D-95, D-96): round 3 ≈ $11.8, no ship (reward saturated); round 4 ≈ $13.3 — GRPO-3 on its own failures, blended 60/40 → **bluff 13 / answered 83**, ships | $25.1 | Claude |
| 1.5 | ~~Sep 26~~ DONE | Freeze written into D-96: no further training; the numbers on the box are 13 / 83 | $0 | Claude (Eric can veto) |

**Hard checkpoint — Sep 27, ~11:30 AM PT (18:30Z; Eric, 2026-09-25): the build PC is shut down and travels to Las Vegas, then
restarts.** Before it: no pod running (`list-pods` []), stick current, everything committed and pushed, session log +
memory written for a cold restart. No card session starts after Sep 26 evening PT until the machine is back; long desk jobs end by Sep 27 09:00 PT.

## 2. Prove it on the box (release gate, D-50)

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 2.1 | ~~Sep 26~~ DONE (re-checked for D-96) | **Release gate (D-50) for the shipped soup:** answered-real **83 %** (≥ 80 ✓); bluff **13 %** — below every open baseline (50–57 %) ✓, below the frontier figures in `evals/BASELINES.md` ✓, and under the stretch target T-1 (≤ 20 %) ✓; all nine suites present as `evals/results/pagouro-1b-soup-g3-cp-4__*` (+ multi-turn 0 fails, held-out reasoning 11/320 recorded); offline audit **PASS** (`evals/results/offline_audit_pagouro-1b-grpo3.json`, shipped as `docs/offline_audit.json`). Re-check only if round 4 changes the model | $0 | Claude |
| 2.2 | ~~Sep 26~~ DONE (Eric) | Fresh-stick test on an Intel N100 laptop (800 MHz, 16 GB, W11): start ≈ 1 min, first answer 10–20 s, a George Washington question answered OK but with a repeated "I can look for more info" tail (→ trim tightened, D-97 pending); **`verify_manifest.py` could not run — no Python on a fresh PC** (→ `VERIFY.bat` + `verify_manifest.ps1`, PowerShell only, added to the package); **a MacBook could not read the stick** (the stick is FAT32, which a Mac reads natively → most likely the port/adapter or the mount; try another port; FAT32 or exFAT both fine, 5.1). Stick must be re-packaged with these when it is back in the build PC | $0 | Eric tested; Claude fixed |
| 2.3 | ~~Sep 27~~ DONE | E3 as measured by Eric on the N100 laptop: ≈ 1 min to start from the stick, 10–20 s to the first answer (in the README) | $0 | Eric |
| 2.4 | Sep 27 | Independent rerun of the bluff test by someone who is not us (a friend, one hour) — the first "receipt over claim" (E4) | $0 | **Eric** finds the person |

## 3. Words on the box (F12, D-94)

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 3.1 | Sep 26 | Eric picks the README first paragraph (candidates A / B / C in `docs/ORIGIN_LEDGER.md` F12) and the box line | $0 | **Eric** |
| 3.2 | ~~Sep 26~~ DONE (except the first paragraph, 3.1) | README final pass: the five claims, the two numbers, SmartScreen note (F11), "finished, as-is, fork it" stance; stick README = repo README first paragraph | $0 | Claude |
| 3.3 | ~~Sep 27~~ DONE (release-day fields only remain: date, anchor, links) | Model card final (`docs/MODEL_CARD.md`), ABOUT final, `facts.json` final — every TBD gone except the release-day fields (date, anchor, links) | $0 | Claude |
| 3.4 | Sep 27 | Founder byline and links on ABOUT/README (name only, one-line employer disclaimer, no home address — F16) | $0 | **Eric** writes the disclaimer line |
| 3.5 | ~~Sep 27~~ DRAFTED in `docs/ABOUT.md` § Disclosures — **Eric's holdings sentence is the one bracket left** | Disclosures paragraph (E7): what it cost, what Eric holds, "no token, on purpose, because…" | $0 | Claude drafts, **Eric** approves |

## 4. Book — *Make Your Own AI* (ships with the release, not after)

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 4.1 | ~~Sep 26~~ DONE | Ch. 13 closes on the decay, the finish and the SFT numbers (draft 2, 3,955 words); the GRPO arc and the frozen 22 / 81 belong to ch. 15 (4.3), not here | $0 | Claude |
| 4.2 | Sep 27 | Ch. 14 *Do it: ship a finished thing* from the runbook, written as done rather than planned (after 5.x below) | $0 | Claude |
| 4.3 | ~~Sep 27~~ DRAFTED (draft 1, D-88 → D-96) | Ch. 15 *What it can and cannot do, with the numbers on the box* | $0 | Claude |
| 4.4 | Sep 28 | Appendices A (decisions) and B (ledger) regenerated; C (glossary) written | $0 | Claude |
| 4.5 | Sep 28 | Build the book (`book/build.py`) → one `.md` + PDF/EPUB; licence split per D-64 (story chapters all rights reserved, do-it chapters CC BY-SA) | $0 | Claude |
| 4.6 | Sep 29 | Eric reads it once, start to finish, and marks anything he would not put his name to | $0 | **Eric** (an evening) |
| 4.7 | Sep 30 | Corrections; the book goes on the stick and in the repo; optional later: print-on-demand / Kindle (a separate, post-release decision) | $0 (POD later ≈ $0 to list) | Claude / **Eric** |

## 5. Freeze, sign, anchor, publish (F8 → F13 — **in this order, no skipping**)

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 5.1 | Sep 30 | **F8 build:** `package_release.py` on the frozen model → `release/Pagouro/`, `MANIFEST.md`, `verify_manifest.py` + `VERIFY.bat`/`.ps1`; PASS on a fresh stick formatted FAT32 or exFAT (both readable on Windows, macOS, Linux; Eric's Mac could not mount the FAT32 stick on 2026-09-26 — port/adapter suspected, retest at 2.2) | $0 | Claude |
| 5.2 | Sep 30 | **F8 sign — key ceremony:** `minisign -G` offline, passphrase in the password manager, secret key never in repo/stick/chat; sign `MANIFEST.md`; paste the public key into README + MANIFESTO | $0 | **Eric** (10 min, once) |
| 5.3 | Sep 30 | Zip `Pagouro-1.0-win64.zip`; record its SHA-256 | $0 | Claude |
| 5.4 | Sep 30 | **F9 anchor:** `ots stamp MANIFEST.md`; wait for a Bitcoin confirmation; `ots upgrade`/`verify`; ship the `.ots` | $0 | Claude (Eric's machine or session) |
| 5.5 | Oct 1 | F9 optional Ordinal inscription of the manifest text: measure the fee first; skip if silly (D-14 is satisfied by OTS) | ≈ $5–30 if done | **Eric** decides + funds the dedicated wallet |
| 5.6 | Oct 1 | **F16/F17 wallet:** a dedicated project wallet (Solana/USDC address for the box) — created on Eric's hardware, address only into the repo | $0 | **Eric** |
| 5.7 | Oct 1 | **F10 Hugging Face:** create `pagouro` org/user, repo `pagouro/pagouro-1.0`: GGUFs, `corpus.json`, eval JSONs, manifest, `.minisig`, `.ots`, model card | $0 | **Eric** creates the account (5 min); Claude uploads (`HF_TOKEN` in `.env`) |
| 5.8 | Oct 1 | **F10 Arweave:** upload the zip + manifest + signature + ots via Turbo (turbo.ar.io credits, card or crypto) or a native AR wallet; verify the bytes back from a second gateway by hash; log the measured cost (E5) | ≈ $8–15 at $6–8/GB for a ~1.2 GB zip (+ ~$5 if the q4 file goes up separately) | **Eric** tops up ~$15 of Turbo credits; Claude uploads |
| 5.9 | Oct 1 | **F10 GitHub Release** `v1.0`: zip, SHA-256, HF + Arweave links, OTS block height. This is "the link" | $0 | Claude drafts, **Eric** publishes |
| 5.10 | Oct 1 | F17 tip jar: GitHub Sponsors or Ko-fi link + the wallet address in README; price in dollars ("what a card-hour costs") | $0 | **Eric** (accounts) |
| 5.11 | Oct 2 | **F13 history scan:** `.env`, `My_Claude_Conversation.txt`, `API_KEYS*`, `data/`, `checkpoints/`, `release/` never in history; final `git status` clean | $0 | Claude |
| 5.12 | Oct 2 | **F13 flip PUBLIC, then ARCHIVE** (read-only, forkable); Software Heritage save request | $0 | **Eric** (the one-way door) |
| 5.13a | ~~Oct 1~~ DRAFTED (`docs/site/index.html`; four placeholders filled at F9/F10) | **The front page** `docs/site/index.html` — one static page: the two numbers, the four promises, the manifest hash, links to the GitHub Release / HF / Arweave. Lives in the repo; hosted wherever DNS points | $0 | Claude |
| 5.13b | Oct 1 | **QStorage (Quilibrium) as the front door + mirror** (Eric, 2026-09-25): upload the page (and the release zip as a D-40 mirror) to a public bucket via QConsole; get the CNAME; **test HTTPS on `pagouro.com`** — if the bucket cannot serve a certificate for the domain, the site stays a 301 (5.13c) and QStorage stays a mirror; cost measured and published (E5). Keys go in `.env` as `QSTORAGE_ACCESS_KEY` / `QSTORAGE_SECRET_KEY` / `QSTORAGE_ENDPOINT` / `QSTORAGE_BUCKET` | QStorage plan (Eric's account; cost to be read from it) | **Eric** (account, DNS at Wix); Claude (upload, TLS test) |
| 5.13c | Oct 2 | **F14 DNS at Wix:** `pagouro.com` → CNAME to the QStorage site if 5.13b passed, else 301 forwarding to the GitHub Release. DNSSEC + WHOIS privacy already on. Either way the GitHub Release stays the canonical link; the site is a front door, never a dependency | $0 (domain already paid) | **Eric** (Wix DNS, 10 min) |
| 5.14 | Oct 2 | Book PDF/EPUB attached to the Release and on the stick (from 4.7) | $0 | Claude |

## 6. Presence — bare minimum (D-94: "everything should have some presence; needs to be findable")

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 6.1 | Oct 2 | Register `pagouro` where it is free: X, Instagram, TikTok, Reddit (Eric checked), Bluesky, Mastodon, YouTube; HF is 5.7; same avatar (the mark, `brand/pagouro_mark.png`) and the one-sentence bio everywhere; link = the GitHub Release | $0 | **Eric** (accounts are his; ~1 h) |
| 6.2 | ~~Oct 2~~ DRAFTED (`docs/LAUNCH.md`; links at F10) | Launch post, one text reused: the two numbers, the four promises, the link. Places: Show HN, r/LocalLLaMA, X, Bluesky/Mastodon, Hugging Face post | $0 | Claude drafts; **Eric** posts |
| 6.3 | Oct 2 (shot list DRAFTED in `docs/LAUNCH.md`) | A 60–90 s screen recording: double-click → first answer → an abstention → `/careful` → `verify_manifest.py` PASS. Goes on YouTube/TikTok/X | $0 | **Eric** records; Claude scripts it |
| 6.4 | Oct 3 | `docs/HANDLES.md` updated with what was registered; success metrics baseline written (stars, downloads, forks, independent reruns — E6) | $0 | Claude |
| 6.5 | ongoing | Read issues; answer nothing that promises a change (ABOUT: "no team, no roadmap"); reruns of the bluff test by others get linked from a `docs/RECEIPTS.md` | $0 | **Eric** reads; Claude drafts replies if asked |

## 7. Housekeeping before the lights go off

| # | Date | Task | Cost | Who |
|---|---|---|---|---|
| 7.1 | Oct 2 | Rotate/revoke the keys that touched the build: TypeSafe (`TYPESAFE_API_KEY`), OpenRouter, HF token after upload; RunPod: confirm `list-pods` [] and auto-reload OFF; leave the balance or withdraw | $0 | **Eric** |
| 7.2 | Oct 2 | Local archive: `data/out_1b/`, checkpoints, eval results, the release zip, the book — one copy on the stick, one on a second drive, hashes in `MANIFEST.md` | $0 (a spare drive if none) | **Eric** |
| 7.3 | Oct 3 | Final BUILD_LOG entry ("Day N — released") and SESSION_LOG close-out; memory note marked RELEASED | $0 | Claude |
| 7.4 | Oct 3 | `docs/ORIGIN_LEDGER.md`: every F-row DONE with its evidence; every O-item either closed or marked "post-release, not a blocker" | $0 | Claude |

## 8. Explicitly *not* on the list (decided, do not re-open)

- A maintained product, updates, telemetry, a roadmap (ABOUT, THREAT_MODEL, D-14).
- A web *app*, accounts, app stores; a token; encrypted or gated weights (origin F7, G). (A one-page static front door is now in 5.13a–c; it is not a dependency.)
- Bigger models (7B/30B/70B, O-46), the US Code shelf (O-41), the CLM judge (O-47), io.net (O-31): all
  **post-release** ideas with their own decisions; none blocks "done".
- Round 3+ of research beyond 1.4: the freeze (1.5) ends it.

## Cost summary

| Item | Amount |
|---|---|
| Already spent (RunPod, all runs) | ≈ $1,850 |
| Left to spend to be done | round 2 ≈ $10 (+ optional round 3 ≈ $10–15) · Arweave ≈ $8–15 · optional inscription ≈ $5–30 · everything else $0 |
| Eric's hands-on time | ≈ 6–8 hours total across 2.2, 3.1, 4.6, 5.2, 5.6–5.13, 6.1–6.3, 7.1–7.2 |
| Earliest realistic "100 % done" | **Oct 3, 2026**, if the round-2 result is in by Sep 26 and Eric's items land on the dates above |
