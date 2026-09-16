# Environment report — primary dev box

Detected 2026-09-16, milestone 1 step 1. Re-run detection if hardware changes.

## The machine

This **is** the EVO-X2 described in the brief. Confirmed by name, not assumed.

| Item | Value |
|---|---|
| Manufacturer / model | GMKtec NucBox_EVO-X2 |
| CPU | AMD Ryzen AI Max+ 395 with Radeon 8060S ("Strix Halo") |
| Cores / threads | 16 / 32 |
| **RAM** | **31.6 GB** |
| GPU | AMD Radeon 8060S (integrated, unified memory) |
| GPU driver | 32.0.12078.30 |
| OS | Windows 11 Pro, build 26200 |

## ⚠ Finding 1 — RAM is 32 GB, not the large unified pool the brief assumed

`PAGOURO_BRIEF.md` §4 describes "large unified memory" and says model size is never the bottleneck,
compute is. It also, correctly, said to verify installed RAM at start. **This unit has 31.6 GB
total**, shared between CPU and integrated GPU. The EVO-X2 ships in configurations up to 128 GB;
this is not one of those.

What this changes:

- The "unified memory means model size is never the bottleneck" reasoning **does not apply here**.
  32 GB shared is a real constraint.
- It does not threaten the plan. The chosen target is ~1B parameters (D-6), and the big run is
  rented anyway (D-6, M6). Local work is toy-scale and small-run scale.
- It does affect milestone 5, the ~300M local sanity run, and the ablation study at M4. Both need a
  memory budget calculated rather than assumed. Plan for it; do not discover it mid-run.
- Worth asking Eric whether the unit is upgradeable. Strix Halo memory is usually soldered LPDDR5X,
  in which case 32 GB is permanent and M4/M5 batch sizes must be sized to it.

## Storage

| Device | Size | Free | Notes |
|---|---|---|---|
| YMTC PC411-2TB-B (NVMe, internal) | 1,908 GB | **1,329 GB** | The only internal drive |
| USB 2.0 Flash Disk (D:) | 1 GB | 0.2 GB | A small stick, not the project drive |

**Finding 2 — the 2 TB external USB drive is not attached.** Only a 1 GB flash disk is present.
The brief's storage plan (archives and raw corpus on the external, tokenized data on internal NVMe)
needs that drive connected before milestone 3.

**Finding 3 — the second M.2 slot appears free**, as the brief predicted. One physical NVMe is
present. With 1.33 TB free internally there is no urgency, but D-8 (build on Dolma / FineWeb-Edu /
The Stack) means bulk downloads land here, and 100B tokens at 16-bit is roughly 200 GB tokenized
plus the raw sources. Comfortable for now; worth planning before M3.

## Software

| Tool | State |
|---|---|
| Python | **None installed.** The only interpreter on PATH belongs to another tool's virtualenv (hermes-agent, 3.11.15) and must not be used for this project. `python3.exe` in WindowsApps is the Microsoft Store stub. No `py` launcher. |
| PyTorch | Not installed |
| ROCm / HIP | **Not installed.** `HIP_PATH` unset, no ROCm directory. |
| Vulkan | **Present.** `vulkan-1.dll` and `vulkaninfo` both available; the GPU enumerates correctly. |
| git | 2.54.0.windows.1 |
| cmake | Not installed |
| MSVC compiler | Not on PATH |

**Finding 4 — Vulkan works, which is what inference needs.** llama.cpp's Vulkan build is the
portability story for the shipped application (brief §5), and the runtime plus a correctly
enumerating GPU are already here. The distribution plan is not at risk.

**Finding 5 — ROCm is absent and its viability on this chip under Windows is unverified.** The
brief flagged this as experimental and said to propose rather than decide. Nothing about milestone 1
depends on it: the brief explicitly says to proceed on CPU if GPU training is unavailable, and a
10–20M parameter toy model trains on 16 cores in minutes.

The real decision, for milestone 4 and 5 rather than now, is between three paths:

1. **CPU on Windows.** Certain to work, slowest. Adequate for toy scale.
2. **ROCm on Windows.** Least friction if it works; support for this chip needs verifying against
   AMD's current matrix rather than assumed.
3. **Linux or WSL2 with ROCm.** Historically the smoothest ROCm path, at the cost of a boot
   environment or a WSL setup.

Do not rabbit-hole on this during milestone 1. Record the question, finish the pipeline on CPU,
and decide with measurements from the small runs.

## What was installed during this milestone

- Python 3.12 (user scope), because no usable interpreter existed.

## Open questions this raises for Eric

1. Is the 32 GB upgradeable, or is it soldered? Changes the local training ceiling permanently.
2. Where is the 2 TB external drive? Needed before milestone 3.
3. Mining: see Finding 6. Confirmed, measured, and it is worse than the brief implies.

---

## ⚠ Finding 6 — this box was mining, and it invalidated the first benchmarks

Discovered mid-milestone when CPU training measured absurdly slow. `midstate.exe` (Midstate /
MDS, in the user's `midstate\bin` folder) was running with **2,519,748 accumulated CPU-seconds**,
about 29 days of CPU time, holding the machine at **99% load**.

The brief predicted exactly this: "training and mining cannot share the machine." Worth recording
how badly, because the failure looked like a broken toolchain rather than a busy one.

| Condition | ms/step | tokens/sec |
|---|---|---|
| Miner running | 29,131 | 141 |
| Miner stopped | 951 | **4,308** |

**A 30x difference.** Before stopping it I had already begun diagnosing PyTorch threading and
matmul kernels, because 141 tok/s looks exactly like a misconfigured build. Raw matmul measured
192 GFLOP/s even under load, which was the clue that the hardware was fine and something else was
eating it.

**Rule for this project:** confirm the machine is idle before recording any timing number, and say
so in the writeup. Published tokens-per-second figures are a headline metric (brief section 9) and
a contaminated one is worse than none.

**Stopping and restarting.** The vendor ships `STOP-MINING.bat` and `START-MINING.bat` in the
`midstate` folder. The stop script could not kill the process from a non-interactive shell
("Input redirection is not supported"), so a forced process stop did it. Restart mining with
`START-MINING.bat` whenever the box is not training.

## Measured baseline (idle machine, 2026-09-16)

| Measurement | Value |
|---|---|
| Raw fp32 matmul, 2048x2048 | 192 GFLOP/s |
| Raw fp32 matmul, 1024x1024 | 28.5 GFLOP/s (small matrices are overhead-bound) |
| Training, 12.6M params, batch 16 x 256 | 951 ms/step, ~4,300 tok/s |
| PyTorch threads / interop | 16 / 16, on 32 logical CPUs |
| PyTorch build | 2.14.0+cpu, MKL and MKLDNN available |

At ~4,300 tok/s, CPU training moves roughly 15M tokens per hour. Fine for milestone 1 and for the
ablation study's small runs, and it confirms the plan's shape: develop here, rent for anything
real.
