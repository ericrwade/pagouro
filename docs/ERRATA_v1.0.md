# Errata — Pagouro 1.0

*Found 2026-09-29 by the first "stranger check": a clean Linux machine (a GitHub-hosted runner,
`.github/workflows/stranger-check.yml`) downloaded the public release and walked the whole trust
chain; the passing run, with every hash and merkle root in the log, is
https://github.com/ericrwade/pagouro/actions/runs/36581718458. The shipped bytes are not changed — that would change the manifest, its signature, its
timestamp and the Arweave copy, and the hashes match everywhere they are promised. These are the
rough edges, with the way round each.*

| # | What | Way round |
|---|---|---|
| E1 | `verify_manifest.py` on the stick looks for the public key as `minisign.pub`; the stick ships it as `pagouro.pub`. Every one of the 115 file hashes checks, but **if `minisign` is installed** the script then reports `SIGNATURE FAILED: minisign.pub: No such file or directory` and the verdict says NOT match. Without `minisign` installed (every Windows machine we tested) the script says "hashes checked only" and passes, which is why this was not caught. | Check the signature directly: `minisign -Vm MANIFEST.md -p pagouro.pub` (or `-P RWQe8tvI6RCE2uMbuILC9/rEr6bNZdcOA+WC7dHtObLE94ovGk8xuFlG`, the key as printed in the README). Or copy `pagouro.pub` to `minisign.pub` beside it and run the script again. `VERIFY.bat` is unaffected (hashes only). |
| E2 | `CHECK_YOUR_COPY.md` on the stick gives the command as `minisign -Vm MANIFEST.md -p minisign.pub`. | Read `pagouro.pub` for `minisign.pub`. |
| E3 | The release zip was written by Windows PowerShell 5.1 `Compress-Archive`, which stores paths with backslashes. Windows extracts it correctly. On Linux, Info-ZIP `unzip` converts the separators and prints a warning (exit code 1). macOS Archive Utility and Python's `zipfile` may extract files with literal backslashes in their names. | On macOS/Linux extract with `unzip` (Info-ZIP) or `7z x`. The zip's SHA-256 (`96debc3e…`) is unaffected and is the one to check. |
| E4 | The app's banner reads `PAGOURO  0.1.0 (MVP framework)`; the release is 1.0. The string is `APP_VERSION` in `app/pagouro_app.py`, never bumped. The version of a copy is the manifest hash (`02a618fc…`), not the banner. | Ignore the banner; check the manifest. |

The verifier in the repository (`scripts/verify_manifest.py`) accepts either key filename from this
commit on; the stick's copy stays as signed.
