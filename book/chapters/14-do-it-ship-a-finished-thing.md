# Chapter 14 — Do it: ship a finished thing

*Licence: CC BY-SA 4.0 (do-it strand, D-64).*

*DO-IT chapter, draft 1 (2026-09-29), written from what was actually done on 27–29 September
rather than from the plan in `docs/RELEASE_RUNBOOK.md` — the plan is in the repository too, and the
places where the two differ are the point of this chapter.*

---

A finished thing is one a stranger can check without trusting you, ten years from now, on a
machine you have never seen. That sentence turns into six mechanical steps, in an order that
matters, each of which produces a receipt. This chapter is the six steps as we ran them, with the
commands, the costs, and the three places we got it wrong first.

## 1. Freeze, and hash everything

Nothing below makes sense until the bytes stop changing. Our freeze is a decision in the log
(D-96: "no further training; the numbers on the box are these"), and the packaging script that
follows it writes `MANIFEST.md`: one row per file — path, SHA-256, size — for every file that will
be on the stick, a hundred and fifteen of them.

```
python scripts/package_release.py      # via master_pipeline.sh stage 10
```

The manifest is the product's spine. Everything after this step signs it, timestamps it, or
copies it; nothing after this step may change a shipped byte, because the manifest would no longer
describe the folder. We changed shipped bytes twice after signing — a public key that had to be
regenerated, a README paragraph — and each time the sequence restarted from here. Budget for that.

A verifier ships beside the manifest. Ours is two: `verify_manifest.py` for anyone with Python,
and `VERIFY.bat` with a PowerShell script for a fresh Windows machine that has nothing. The second
exists because the first fresh-stick test, on an Intel N100 laptop, found no Python installed.
The test that finds the gap is worth more than the gap.

## 2. Sign the manifest

A signature says *the person who holds this key produced this manifest*. We used minisign: small,
audited, no web of trust, one public key line short enough to compare by eye.

```
minisign -G -p pagouro.pub -s ~/.ssh/pagouro.key            # once, offline; passphrase in the password manager
minisign -Sm MANIFEST.md -s ~/.ssh/pagouro.key -t "Pagouro release 1.0"
minisign -Vm MANIFEST.md -P RWQe8tvI6RCE2uMbuILC9/rEr6bNZdcOA+WC7dHtObLE94ovGk8xuFlG
```

The secret key never enters the repository, the stick, or a chat; the public key goes into all
three, and into the README so it can be compared against the one on the release page. Our first
key pair was thrown away after its passphrase was mistyped at creation — a hyphen for an
underscore, twice, identically. Write the passphrase down before you type it, and sign something
disposable immediately to prove you can.

## 3. Timestamp the manifest on Bitcoin

A signature proves who; a timestamp proves when — that this exact manifest existed before a
given moment, in a ledger nobody can quietly edit. OpenTimestamps does this for free: public
calendar servers aggregate hashes into a Bitcoin transaction they pay for, and hand back a proof
that anyone can check against the chain.

```
pip install opentimestamps-client
ots stamp MANIFEST.md          # -> MANIFEST.md.ots, pending
ots upgrade MANIFEST.md.ots    # hours later, once a block includes it
ots info MANIFEST.md.ots       # BitcoinBlockHeaderAttestation(968959)
```

Ours attests to block 968959. Two things to know. The client did not run on our Windows Python
(its Bitcoin library wants a system OpenSSL), so both commands ran on a rented Linux box at six
cents an hour; the whole exercise cost seventy-three cents, mostly because the box idled while a
safety check on our side was down. And `ots verify` wants a Bitcoin node; without one, `ots info`
shows the block height and the merkle root, and any block explorer confirms the rest. The proof
file ships beside the manifest.

## 4. Put the bytes somewhere permanent

This is the step that is easy to promise and expensive to keep. The manifest's hash lives on
Bitcoin forever; the 1.76 GB it describes has to live somewhere too, and "on GitHub" is a promise
about a company. Arweave is a pay-once permanent store. The honest number, on the day: 22.3 AR-
equivalent credits for the zip, about a hundred and nine dollars including the small files — ten
times the per-gigabyte figure we had written down a week earlier from stale sources. We paid it,
because the alternative was to reword the promise, and the promise was the product.

```
npx @ardrive/turbo-sdk upload-file --wallet-file <keyfile.json> --file-path Pagouro-1.0-win64.zip
```

Then fetch every file back from a gateway and hash it. The six small files matched from
`arweave.net` within minutes; the zip took longer to be served, and was checked from the
uploader's own gateway first. The transaction IDs go into the release notes beside the SHA-256s.
Two mistakes here: the CLI flag is `--file-path`, not `--file` (one wasted run, no credits lost),
and the wallet app's own upsell — a "vault" for sixty-eight AR — appeared as a signature request
that looked, for a minute, like something we had triggered. Decline anything you did not type.

## 5. Publish, in three places, the same hash everywhere

- **Hugging Face** — `Pagouro/pagouro-1.0`: both GGUFs, the corpus ledger, the eval results, the
  manifest, its signature, its timestamp proof, the public key, and the model card as the README.
  The upload client verifies each large file's SHA-256 against the store; check it anyway. The
  repository is created private and flipped with everything else.
- **Arweave** — step 4.
- **GitHub Release** `v1.0` — the zip, its `.sha256`, the manifest, signature, proof, and public key
  as assets, with the release notes carrying every hash and every link. Created as a draft on the
  private repository; publishing it is part of the last step.

A front page went up before the flip — `pagouro.com`, one static file on GitHub Pages, no scripts,
no analytics — showing the two numbers, the four promises, the manifest hash, the signing key and
the block height, with the download links reading "at release" until they exist. DNS at the
registrar: four A records to GitHub's addresses and a `www` CNAME; the certificate took a re-save
of the domain to start provisioning. Free, and HTTPS.

## 6. The one-way door

Before it: scan the whole history for anything that must not be public. Ours found no key, no
`.env`, no private conversation, no checkpoint in any commit — only a template and a few small
provenance ledgers, tracked on purpose. Then, in this order: publish the Hugging Face repository,
publish the GitHub release, flip the repository public, archive it (read-only, forkable), and
change the front page's links from "at release" to the links. After the archive, the repository
cannot be edited without un-archiving it in public view, which is the point: the thing is done.

## What we did not do

No code signing of the executable (it costs money and would change bytes before the manifest;
the manifest, signature and timestamp are the trust chain, and Windows SmartScreen's "Run anyway"
is documented instead). No Ordinal inscription (the OpenTimestamps proof satisfies the anchor
requirement; an inscription is ceremony). No Quilibrium mirror yet (a second copy is welcome; the
canonical permanent copy is Arweave, on track record — D-42).

## The receipts, in one place

| What | Where |
|---|---|
| Manifest | `MANIFEST.md`, SHA-256 `02a618fc…`, 115 files |
| Signature | `MANIFEST.md.minisig`; public key `RWQe8tvI…` in `pagouro.pub` |
| Timestamp | `MANIFEST.md.ots`, Bitcoin block 968959 |
| Release zip | `Pagouro-1.0-win64.zip`, SHA-256 `96debc3e…` |
| Arweave | zip tx `6XjlZGVYmp1mDjfcwHRPpr8qe8xOpLHCAMDoB5WXGBk`; small files listed in the release notes |
| Weights | Hugging Face `Pagouro/pagouro-1.0` |
| Front page | https://pagouro.com |

Every row is a thing a stranger can fetch and check. That is what finished means.
