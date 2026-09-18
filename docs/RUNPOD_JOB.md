# Running Pagouro on a rented GPU (RunPod)

The origin conversation's rule, now with a mechanism: **develop on the EVO-X2, rent one GPU for
the real runs, never spend without Eric's say-so** (D-54). This is the exact sequence the
session uses, so a person can repeat it or check it.

## One-time
- RunPod account funded by Eric; the balance is the hard cap.
- Claude Code plugin `runpod@runpod` connected (OAuth). No API key stored.
- An SSH key generated on this machine (`~/.ssh/id_ed25519_runpod`) and its **public** half
  registered on the account (`update-ssh-keys`). Pods created with `startSsh` accept it.

## Every run
1. **Bundle.** `bash scripts/runpod/make_bundle.sh` → `build/bundle/pagouro-bundle.tar.gz`
   (+ `.sha256`). Contains code, tokenizer, tokenized data. Never checkpoints, corpus, `.env`.
2. **Price first.** `list-gpu-types` (secure cloud, product POD) → state the hourly price on the
   status issue before creating anything. Stock changes by the minute; the first two choices on
   2026-09-18 (RTX 4090, RTX A5000) were gone by the time the create call landed; the A40 at
   $0.49/h was not.
3. **Create the pod** (`create-pod`): official image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`,
   `ports: ["22/tcp"]`, `startSsh: true`, 40 GB container disk. For a run whose checkpoint must
   outlive the pod, create a network volume first (`create-network-volume`, same data center) and
   mount it at `/workspace`.
4. **Wait for `ssh.direct`** in `get-pod` (the proxy endpoint `ssh.runpod.io` needs a PTY and
   cannot carry `scp`). Then everything is plain SSH from Git Bash:
   ```
   ssh -i /tmp/rpkey -p <port> root@<ip> '<command>'
   scp -i /tmp/rpkey -P <port> build/bundle/pagouro-bundle.tar.gz root@<ip>:/workspace/
   ```
   (The key is copied to `/tmp/rpkey` because OpenSSH mis-parses the space in `Eric Wade`.)
5. **Setup:** `bash /workspace/on_pod_setup.sh` — verifies the bundle hash, extracts, installs
   `numpy tokenizers gguf`, prints GPU/torch/bf16 facts.
6. **Run:** `bash /workspace/shakedown.sh` (300 steps + resume proof + tokens/s) or
   `bash /workspace/flash.sh` (the ~150M Baby tier on FineWeb-Edu the pod fetches itself).
   Long runs are launched detached (`setsid … < /dev/null &`) and polled in separate calls.
7. **Bring the results home:** `scp` the checkpoint and `runs/*.jsonl` back; verify the
   checkpoint loads locally; commit the logs.
8. **Terminate** (`delete-pod`) as soon as the artifacts are verified here. A pod left running is
   the one failure mode that costs real money for nothing; `list-pods` must be empty at the end
   of every session.

## What each run is for
| Run | Config | Purpose | Budget |
|---|---|---|---|
| shakedown | 59M, 300 steps, bf16 | prove the bundle end to end; measure tokens/s | < $1 |
| flash | ~150M, ~3B tokens | first model with real knowledge; price the 1B run from measured throughput | ~$50 |
| 1B (D-6) | ~1B, ~100B tokens, WSD schedule, 8k context | the product | ~$1,500 secure H100; needs Eric's "launch" |

## Measured (append as runs happen)
- 2026-09-18 shakedown, A40 $0.49/h: 62,000 tok/s (59M, bf16, data on GPU), ~15% MFU, resume proven, ~9 min pod life. See D-55.
