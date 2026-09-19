# Chapter 11 — Do it: rent a GPU without getting hurt

*Licence: CC BY-SA 4.0 (instruction strand / generated appendix, D-64).*

*DO-IT chapter, draft 1 (2026-09-19). Numbers from `docs/RUNPOD_JOB.md`, `docs/DECISIONS.md`
D-54/D-55/D-61, the RunPod billing API, and the run logs under `runs/runpod/`; footnotes name
the file.*

---

The desk computer trains the 59-million-parameter model at about 960 tokens a second. The
126-million-parameter model that is on the stick as this chapter is written took two billion
tokens. On the desk that would be twenty-four days even at the small model's speed, and the
bigger model is slower per token. On a rented card it was fourteen hours, and the
whole three-day window in which it was trained, evaluated twice, ablated, and fine-tuned cost
**$7.54** — read from the provider's billing page after the machine was deleted, not
estimated.[^1]

So renting is not optional for anything past a toy, and it is also the only place in this
project where a mistake costs money instead of time. This chapter is the sequence we use, and
each rule in it was paid for once.

## The rules before the commands

1. **The balance is the cap.** Load a fixed amount; never enable auto-top-up. The account can
   then lose at most what is on it. Ours was $165 for the window and $7.54 of it went.[^1]
2. **Price out loud before creating anything.** Write the hourly price and the plan somewhere
   a second person can read — for us, the status issue — *then* create the machine. Stock
   changes by the minute: the first two cards we chose were gone before the create call
   landed; the third, an A40 at $0.49 an hour, was there.[^2]
3. **Nothing lives on the rented machine.** Code and data go up in a bundle with a hash; every
   checkpoint and log comes home and is *opened* (loaded, its tensors counted, checked for
   NaNs) before the machine is deleted. If it did not come home, it did not happen.
4. **Delete it, then prove it.** `list-pods` must be empty at the end of every session. A
   machine left running is the one failure that costs real money for nothing.[^2]
5. **Two people can stop it.** The session works unattended, but the owner can see every pod
   and every dollar from a phone, and the plan for anything new goes on the issue first so it
   can be vetoed.

## The sequence

**Bundle.** `bash scripts/runpod/make_bundle.sh` packs the code, the tokenizer and the
tokenized data into one tarball with a SHA-256 beside it. Never checkpoints, never the raw
corpus, never `.env`.[^3]

**Create.** Through the provider's tool: the official PyTorch image, SSH enabled, a container
disk of 40 GB, a network volume mounted at `/workspace` if the checkpoint must outlive the
machine. Then wait for the *direct* SSH endpoint — the proxy one wants a terminal and cannot
carry files.[^3]

**Set up.** `bash on_pod_setup.sh` verifies the bundle's hash, extracts it, installs three
packages, and prints the GPU, the PyTorch version, and whether bf16 works. Every one of those
lines is there because its absence once cost twenty minutes: the tarball tried to restore
Windows file owners and stopped; the proxy login could not scp; a `pip` refused to install
without a flag; `pkill -f` on the run's own name killed the launcher.[^4]

**Shake it down before you trust it.** Three hundred steps of the real configuration, a
checkpoint, a kill, a resume, tokens-per-second — nine minutes, about eight cents. The point
is the *resume*: if a silent resume failure is going to cost you a fourteen-hour run, you want
to find it in a nine-minute one.[^2]

**Run detached, poll from outside.** `setsid bash flash.sh > log 2>&1 < /dev/null &`, then
read the log in separate calls. Never hold a terminal open on a rented machine for hours.

**Watch the *held-out* number, not the training loss.** This one is D-61, and it is the most
expensive lesson in the chapter, so it gets its own section.

**Bring it home, open it, delete the machine, read the bill.**

## The decay that ate itself

The training recipe ends with a "decay": the learning rate winds down over the last tenth of
the steps while the data shifts toward the domain we care about. As written, that last phase
ran on the domain data *alone* — eight million tokens — for a phase two hundred million tokens
long. Twenty-five passes over the same pages, at a learning rate still near its peak.

The training loss did what memorising does: 3.05 to 0.48 in twelve hundred steps. The loss
on held-out text of the same kind did the opposite: 3.25, 3.85, 4.82. Scored afterwards
against ordinary web text, that checkpoint had gone from a perplexity of 23 to 147. It had
destroyed itself to learn *The Wealth of Nations* by heart.[^5]

It was caught forty minutes in because the held-out loss is printed every 250 steps and
someone was reading it. The phase was stopped, the checkpoint from the start of the decay —
kept by a watcher precisely because we wanted to run the decay twice — was used to run it
again as a *mix*: the domain data blended into ordinary text so that no domain token is seen
more than once or twice. The held-out loss then fell, monotonically, and the model that came
out is the one on the stick. Twenty-eight minutes and fifty cents for the redo, against
fourteen hours if the whole run had needed repeating.

The rule that came out is now in the training script and the plan for the big model: **the
decay is a mix; domain data is never replayed more than about twice; the held-out loss is
watched and must not rise.**[^5] The general form of the rule is older and cheaper: any
number that only goes down is not telling you anything. Print one that can go up.

## A number that is too good is an alarm

While comparing the two decay runs, one of the held-out sets scored an impossible 0.71 for
the wrecked checkpoint — a model that had just proved it could not read web text. It could only
mean the "held-out" set was in the training data. It was: the domain mix carries a slice of the
same web stream, and that slice and the validation split are both the *head* of the stream.
Two of the six scoring sets were thrown out on the spot and replaced with a region of the
stream nothing had touched.[^5] The comparison that survived (the shelf helped on every clean
set at no cost to general text) is only worth stating because of what was thrown out.

## What it costs, measured

| | card | tokens/s | what it was for | cost |
|---|---|---|---|---|
| shakedown | A40 | 62,000 (59M) | bundle, resume, throughput | ~$0.08 |
| DDP rehearsal | 2×L4 | 60,400 aggregate | multi-GPU before it matters | ~$0.20 |
| Flash stable phase | A40 | 38,500 (126M) | 2B tokens, 12.3 h | ~$6 |
| two decay arms + scoring | A40 | — | the ablation | ~$0.50 |
| SFT | A40 | 4,200 steps in 6 min | the manners | ~$0.05 |
| **window total, from billing** | | | | **$7.54** |

The 1B model is priced from these numbers, not from hope: at the measured 15–20% hardware
utilisation, 500–700 H100-hours, $1,500–2,500.[^6] The next thing to measure is whether a
better training loop halves that (a ten-minute head-to-head against a public reference loop,
about ten cents), because the utilisation number is the only one in the table that is ours to
improve.

## What you should see

After a shakedown: a checkpoint on your disk that loads; a `RESUMED from step N` line in the
log with the loss continuing rather than restarting; a tokens-per-second figure; `list-pods`
empty; a billing line under a dollar. If any of those five is missing, you are not ready to
rent for fourteen hours.

---

[^1]: RunPod billing API, `list-billing` for 2026-09-18/19 after the last pod was deleted:
$7.54 total; D-61.
[^2]: `docs/DECISIONS.md` D-55; `docs/RUNPOD_JOB.md` "Every run".
[^3]: `scripts/runpod/make_bundle.sh`, `on_pod_setup.sh`; `docs/RUNPOD_JOB.md`.
[^4]: `BUILD_LOG.md` Day 8.
[^5]: `docs/DECISIONS.md` D-61; `evals/results/d61/`; `scripts/runpod/flash_decay_mix.sh`;
`docs/JOB_1B.md` schedule row.
[^6]: `docs/JOB_1B.md` "Cost, from measurement".
