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

## ⚠ Finding 1 — CORRECTED: 64 GB installed, 32 GB carved out for the iGPU

**Superseded reading below.** The first pass reported "this unit has 31.6 GB" and guessed the
memory was soldered at that size. Eric knew it had 64 GB, which prompted a proper look.

| Measurement | Value |
|---|---|
| Physically installed | **64.0 GB** (8 x 8 GB Micron LPDDR5X-8533, eight channels) |
| Visible to Windows | 31.6 GB |
| Difference | **32.4 GB** |
| `HardwareInformation.qwMemorySize` | **32.0 GB** |

The iGPU has a **32 GB UMA frame-buffer carve-out**, set in BIOS. Nothing is broken and no memory
is missing. (`Win32_VideoController.AdapterRAM` reports 4 GB, but that is a legacy 32-bit field
that saturates; the registry value is the true one.)

**This is a real decision, not a defect, and it cuts both ways.**

- Training on **CPU**, as milestone 1 did, the 32 GB is pure waste. Dropping the carve-out to
  8 or 16 GB would hand the CPU 48-56 GB.
- Training on the **GPU**, 32 GB of unified VRAM is a serious asset and would allow far larger
  local runs than any discrete consumer card.

**Recommendation: change nothing yet.** The backend question (CPU / ROCm-Windows / ROCm-Linux) is
still open, and the setting is reversible in minutes. Decide it once ROCm has actually been tested.
Milestone 1 and the M4 ablation runs fit comfortably in 31.6 GB either way.

The BIOS setting lives under Advanced, AMD CBS, NBIO, GFX Configuration, UMA Frame Buffer Size on
this class of machine.

---

## (superseded) Original Finding 1 — RAM is 32 GB, not the large unified pool the brief assumed

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

**Finding 2 — RESOLVED: no additional storage is needed, and no drive should be bought.**

The 2 TB external is not attached and Eric has it earmarked for an Ubuntu machine. He asked whether
to buy a USB4 drive instead. The answer is no, on two independent grounds.

**Capacity is already sufficient.** At the real target (1B params, ~100B tokens, D-6):

| Item | Size |
|---|---|
| Tokenized corpus, uint16 | 200 GB |
| Three 1B checkpoints (4 GB weights + 8 GB AdamW moments each) | 36 GB |
| Working and scratch space | 50 GB |
| **Total needed** | **286 GB** |
| Internal NVMe free | 1,329 GB |
| Headroom | 1,043 GB |

**Disk bandwidth is irrelevant to training.** The loader reads a flat uint16 array at a trickle:

| Scenario | Throughput | Disk read |
|---|---|---|
| This CPU (measured) | 4,400 tok/s | 0.01 MB/s |
| Rented H100, 1B model | ~100,000 tok/s | 0.20 MB/s |
| 8x H100 | ~800,000 tok/s | 1.60 MB/s |

Even USB 2.0 manages ~35 MB/s, twenty times the most demanding case. The brief's own note that the
storage bottleneck was overstated is correct, and D-7's uint16 choice halves this again.

**If more space is ever wanted**, the second M.2 slot is free. An internal NVMe is cheaper per GB
than USB4, permanently faster, and needs no cable. Keep the 2 TB USB for the Ubuntu machine.

**Architecture note for milestone 3:** stream sources and tokenize on the fly rather than landing
raw corpus on disk. Raw FineWeb-Edu and Dolma dwarf their tokenized output; we only need the
uint16 result. `scripts/fetch_data.py` already streams.

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

1. ~~Is the 32 GB upgradeable?~~ **Answered.** 64 GB installed, 32 GB is an iGPU carve-out set in
   BIOS. Revisit the setting once the training backend is decided, not before.
2. ~~Where is the 2 TB external drive?~~ **Answered.** Not needed. Internal NVMe has 1,043 GB of
   headroom over the real requirement, and disk bandwidth does not affect training.
3. **Ubuntu is probably on the wrong machine.** Eric plans to turn the older PC into an Ubuntu box.
   That PC has an RX 580, which the brief already rules out for ROCm, so Ubuntu there does nothing
   for training. If the goal is a working ROCm stack, Ubuntu belongs on the **EVO-X2** as a dual
   boot, since Linux is historically the smoother ROCm path. Worth deciding together with the
   backend question rather than separately.
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
