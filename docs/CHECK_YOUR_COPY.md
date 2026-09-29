# Is this the real Pagouro? How to check your copy

*For someone who has never heard of a hash. Ships on the stick beside the program; the commands
are the same ones the release runbook uses (F8–F10). Written 2026-09-22.*

You have a folder called `Pagouro`, from a download, a mirror, or a USB stick someone handed you.
Before you type anything into it that matters, you can check — in about two minutes, without
trusting anyone, including us — that it is byte-for-byte the thing we released. Here is what the
check is, why it works, and how to do it.

## The idea in one paragraph

A **hash** is a fingerprint for a file: a short string of letters and digits that a standard
formula computes from the file's bytes. Change one byte anywhere in the file and the fingerprint
changes completely; keep the bytes the same and anyone, on any computer, gets the same
fingerprint. So if we publish the fingerprints of our files, you can compute the fingerprints of
yours and compare. A match means your copy is our copy. That is the whole trick. Two more steps
make it hard to fake: we **sign** the list of fingerprints so you know *we* published it, and we
put the list's own fingerprint on the **Bitcoin blockchain**, so anyone can prove *when* it
existed and that it has not been changed since.

## Step 1 — the fingerprints match (two minutes)

In the `Pagouro` folder there is a file called `MANIFEST.md`. It lists every file in the release
with its fingerprint (the formula is SHA-256; the fingerprint is 64 characters). Next to it is a
small program, `verify_manifest.py`, that fingerprints every file in the folder and compares.

Open a terminal in the folder and run:

```
python verify_manifest.py
```

You should see, at the end: **`VERDICT: every listed file matches the manifest`**.

If you would rather not run our program to check our files — a fair instinct — fingerprint a
file yourself with a tool that comes with your operating system and compare it by eye to the
line in `MANIFEST.md`:

- Windows (PowerShell): `Get-FileHash model\pagouro-1b-q4_k_m.gguf`
- Windows (Command Prompt): `certutil -hashfile model\pagouro-1b-q4_k_m.gguf SHA256`
- macOS: `shasum -a 256 model/pagouro-1b-q4_k_m.gguf`
- Linux: `sha256sum model/pagouro-1b-q4_k_m.gguf`

**What this proves:** the bytes in your folder are the bytes listed in the manifest.
**What it does not prove:** that the manifest itself is ours. Anyone could write a manifest for
a tampered build. That is step 2.

## Step 2 — the manifest is really ours (one minute)

The manifest is **signed**. A signature is made with a private key only we hold and checked with
a public key everyone can see. The public key is a single line printed in three places you can
compare against each other: `README.md` and `MANIFESTO.txt` in this folder, and the project's
release page. Next to the manifest is `MANIFEST.md.minisig`, the signature.

Check it with the small free tool `minisign` (a few hundred kilobytes, from
https://jedisct1.github.io/minisign/):

```
minisign -Vm MANIFEST.md -p pagouro.pub
```

You should see **`Signature and comment signature verified`**.

**What this proves:** whoever holds the private key signed exactly this manifest. Combined
with step 1, your files are the ones that key-holder released.
**What it does not prove:** that the key is ours rather than an impostor's. For that, compare
the public key line with a copy you got from somewhere else — the release page, a friend's
stick, the anchor in step 3. A matching manifest under the wrong key is a matching forgery.

## Step 3 — it existed when we say, unchanged (optional, one minute)

We took the fingerprint of the signed manifest and recorded it on the Bitcoin blockchain
through a free service called OpenTimestamps. The blockchain is a public ledger that thousands
of computers keep identical copies of and that nobody can quietly edit, so this is a timestamp
that cannot be moved: it proves the manifest — and therefore every file it lists — existed in
this exact form at that date. Next to the manifest is `MANIFEST.md.ots`, the proof.

```
pip install opentimestamps-client
ots verify MANIFEST.md.ots
```

You should see **`Success! Bitcoin block <number> attests existence as of <date>`**. The block
number and date are also printed in `README.md`; they should match.

**What this proves:** this manifest is the one that existed on that date, not one edited last
week. It also lets someone who found Pagouro on an unknown mirror, years from now, confirm they
have the original release.
**What it does not prove:** who made it (that is the signature) or that it is any good (that is
the ledger, the tests and the code — all in the folder, all readable).

## If something does not match

Stop and do not use that copy. A mismatch means a file was changed, added, or damaged after we
released it — by a mirror, by an accident, or by someone who wanted it changed. Get another copy
from a different source and check again. There is no situation in which "close enough" is fine;
the whole point of a fingerprint is that it is exact.

## Why we bother

Almost nobody will run these commands, and that is fine. The point is that anyone *can*, and
that the answer is arithmetic rather than trust. Pagouro's claims — every byte licensed and
dated, honesty measured, nothing leaves the machine, no watermark on your words — are all
claims about a specific set of bytes. The fingerprints are what tie the claims to the bytes in
your hand. Without them, "this is Pagouro" would just be our word.
