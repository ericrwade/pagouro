# Where to rent the 1B's GPUs — RunPod, io.net, vast.ai

*Written 2026-09-21 (O-31, Eric's question: "is there an advantage to RunPod or is it trivial to
consider io.net / vast.ai?"). Prices and product facts are as read on that date from the sources
named; the decision rule at the end is the part that should not change.*

## The question, restated

The 1B run is one job: **8×H100 on one host with NVLink, for 3–5 days, with ~200 GB of data on a
disk next to the cards, and a checkpoint copied home every few hours.** Everything that matters
about a provider is how well it does *that one job*. Price is the fourth thing on the list.

## What "ready to go on RunPod" actually means

Nothing in the training code is RunPod-specific. What is:

| Piece | RunPod state | Cost to redo elsewhere |
|---|---|---|
| Driving the provider without a key in the transcript | RunPod MCP plugin in this session (create/stop/delete/billing) | io.net: web UI + a VMaaS/CaaS API exists (not tried); vast.ai: a CLI. A day either way, or Eric clicks. |
| Bundle → copy up → run → copy home (`scripts/runpod/*.sh`) | written, used on 5 pods | edit the copy commands; an hour |
| Data next to the cards | RunPod network volume, 500 GB plan (`docs/JOB_1B.md`) | io.net docs say nothing about persistent volumes; vast.ai instance disk lives and dies with the instance |
| **Proof**: tokens/s measured, checkpoint+resume proven by killing a run, 2-GPU DDP rehearsed, billing watched to the cent | done (D-54/D-55, JOB_1B prereq 2) | **must be repeated** — this is the real head start |
| The delete-the-pod discipline every guardrail hangs on | `list-pods` empty, every window | same discipline, different verb |

So "switch" costs about a day of plumbing plus **~$30 of proof** — cheap. What it does not buy back
is a lost multi-day run; that is where the choice actually lives.

## The three, as found on 2026-09-21

| | RunPod | io.net | vast.ai |
|---|---|---|---|
| H100 SXM, per GPU-hour, on demand | **$3.49 secure / $2.69 community** (JOB_1B, getdeploying) | **$2.10–3.50** (io.net's own page); "$2.19 from" in their guide | **$1.73** (getdeploying; host-set, varies) |
| 8×H100 as one NVLink host | yes (SXM, secure or community) | "multi-GPU H100 SXM clusters include NVLink 4.0" — **not stated** whether an 8-GPU single host is a turnkey option; self-serve **bare metal was discontinued 2025-10-01** (their docs), leaving Ray/Kubernetes clusters, containers and VMs | yes — hosts list whole 8× machines; many are individuals' or small DCs' hardware |
| Who owns the machine | RunPod datacenters (secure) or vetted partners (community) | a marketplace of GPU suppliers, paid in IO/USDC | a marketplace of hosts, individuals to datacenters |
| Billing | per second while running; stop/delete when done | **prepaid for a chosen duration (hourly/daily/weekly/monthly), "Pay & Deploy" up front**, extendable; docs do not say what happens to the disk at expiry | per second; on-demand (fixed) or interruptible (bid; stopped by a higher bid) |
| Persistent storage | network volumes (~$35/month for 500 GB) | **not documented** | instance disk only; "save work frequently, use cloud storage" is their own advice |
| Payment rails | card | **IO coin (no fee), USDC on Solana/Aptos (2% + 0.25% reservation fee), card** | card, crypto |
| Uptime / SLA | none published for community; secure is DC-hosted | none found; "Proof of Time-Lock" attests the GPUs were not shared during the rental | none; interruptible instances are killed by design |
| API | yes (used) | VMaaS / CaaS APIs exist | CLI + API |

Sources: io.net pricing guide and docs (`io.net/p/h100-gpu-cloud-…`, `io.net/docs/guides/payment/*`,
`…/clouds/deploy-vm-on-demand.md`, `…/clouds/deploy-bare-metal-cluster.md`); getdeploying.com H100
table (updated 2026-09-21); vast.ai docs (`docs.vast.ai/guides/reference/faq/rental-types`); RunPod
figures from `docs/JOB_1B.md` and this window's billing.

## What each is for

- **RunPod** — the safe run: one host, DC-hosted, volume next to it, per-second billing, proven
  chain. Cost of the 1B at secure price ≈ $2,000–2,500 of compute; community ≈ $1,600–1,900.
- **io.net** — the story: paid in USDC on Solana, decentralised supply, and it puts the project
  inside Eric's day job. Price roughly community-RunPod. Open questions its docs do not answer:
  an 8×H100 *single host* for self-serve; persistent storage for 200 GB; what happens to the disk
  when a prepaid duration ends (prepayment is the wrong shape for a job whose length is uncertain —
  extend early or lose the machine). Node churn on a multi-day job is the risk, not price.
- **vast.ai** — cheapest, most variable. Good for shakedowns and single-card jobs; the weakest
  choice for a four-day eight-card job because the host is a stranger's machine and the disk is
  the instance's. Interruptible pricing is irrelevant here (a killed pretrain is a killed pretrain).

## The rule (unchanged from O-31)

A provider carries the 1B only after it has passed, **on that provider**, the same two tests
RunPod passed:

1. **Shakedown, ~$1–3:** one GPU, bundle up, 300 steps, checkpoint, kill, resume, tokens/s, copy
   home, delete. `scripts/runpod/shakedown.sh` is the script; only the copy verbs change.
2. **Rehearsal, ~$25:** the 8×H100 host for one hour under `torchrun`, aggregate tokens/s,
   checkpoint on the volume (or wherever the data lives), resume, and — the part that matters
   on a marketplace — a deliberate stop/extend cycle to learn what the disk does.

Pass both and the 1B runs there, with checkpoints home every six hours regardless. Fail either
and RunPod stays, ~$30 spent, and there is still a paragraph for the write-up.

**The marketing rule:** the io.net story is told only if the run *finishes* there. "Trained on
decentralised GPUs, paid in USDC, hash anchored to Bitcoin, mirrored on Arweave" is a coherent
sentence; "…and then we finished on RunPod" is worse than no sentence.

## What Eric does, what the session does

- Eric: open an io.net account, fund it (~$30 covers both tests; USDC if the story is the point),
  and say "shakedown io.net" on the status issue. Same for vast.ai if curious (~$5).
- Session: run the shakedown, post the numbers (tokens/s, resume proven, what the disk did),
  then the rehearsal, then a one-line verdict here and in DECISIONS.md.
