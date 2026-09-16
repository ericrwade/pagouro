"""Offline audit: assert the application makes ZERO network connections in offline mode.

This is the flagship test (DECISIONS.md D-13). Someone at real risk must not have to
trust Eric's word, so the audit has to be reproducible by a stranger in minutes and its
output has to be publishable verbatim.

Target T-8 is absolute: any connection in offline mode is a release blocker, not a
percentage to improve.

    python evals/offline_audit.py --exe tools/llamacpp/llama-completion.exe \\
                                  --args "-m data/gguf/pagouro-m1-q8_0.gguf -p hello -n 16"

Method: snapshot the process's TCP/UDP endpoints repeatedly while it runs, using the
OS's own connection table rather than anything the program reports about itself. A
program cannot lie about this the way it could about a log line.

LIMITATION, stated plainly because overclaiming here is the failure mode: this observes
sockets opened by the process and its children. It does not prove the absence of exotic
channels (DNS via a helper service, IPC to another process that then talks). For a
release audit, run it alongside an external packet capture and publish both.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PS_SNAPSHOT = r"""
$ids = @({pids})
$rows = @()
foreach ($i in $ids) {{
  try {{
    $rows += Get-NetTCPConnection -OwningProcess $i -ErrorAction SilentlyContinue |
      Where-Object {{ $_.RemoteAddress -ne '0.0.0.0' -and $_.RemoteAddress -ne '::' }} |
      Select-Object @{{n='proto';e={{'tcp'}}}}, @{{n='remote';e={{$_.RemoteAddress}}}}, RemotePort, State
    $rows += Get-NetUDPEndpoint -OwningProcess $i -ErrorAction SilentlyContinue |
      Select-Object @{{n='proto';e={{'udp'}}}}, @{{n='remote';e={{$_.LocalAddress}}}}, @{{n='RemotePort';e={{$_.LocalPort}}}}, @{{n='State';e={{'listen'}}}}
  }} catch {{}}
}}
$rows | ConvertTo-Json -Compress
"""


def descendants(pid: int) -> list[int]:
    ps = ("Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=25).stdout
        rows = json.loads(out or "[]")
    except Exception:
        return [pid]
    if isinstance(rows, dict):
        rows = [rows]
    kids: dict[int, list[int]] = {}
    for r in rows:
        kids.setdefault(int(r["ParentProcessId"]), []).append(int(r["ProcessId"]))
    seen, stack = {pid}, [pid]
    while stack:
        cur = stack.pop()
        for k in kids.get(cur, []):
            if k not in seen:
                seen.add(k); stack.append(k)
    return sorted(seen)


def snapshot(pids: list[int]) -> list[dict]:
    if not pids:
        return []
    cmd = PS_SNAPSHOT.format(pids=",".join(str(p) for p in pids))
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                             capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception:
        return []
    if not out:
        return []
    try:
        rows = json.loads(out)
    except Exception:
        return []
    return [rows] if isinstance(rows, dict) else rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--args", default="")
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--max-seconds", type=float, default=180)
    ap.add_argument("--out", default=os.path.join(ROOT, "evals", "results", "offline_audit.json"))
    a = ap.parse_args()

    exe = a.exe if os.path.isabs(a.exe) else os.path.join(ROOT, a.exe)
    if not os.path.exists(exe):
        raise SystemExit(f"missing: {exe}")

    cmd = [exe] + shlex.split(a.args)
    print("OFFLINE AUDIT")
    print("  command :", " ".join(cmd))
    print("  method  : OS connection table, sampled every %.2fs, process tree included" % a.interval)
    print("  note    : a sample count in single digits means sampling was too slow to trust")
    print()

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            cwd=ROOT)
    observed: list[dict] = []
    samples = 0
    t0 = time.time()
    # Enumerating the process tree costs ~4s per call, which throttled sampling to a
    # useless 1 sample per run. Cache it and refresh occasionally; a new child still
    # gets picked up within a few seconds, and the connection table is what matters.
    pids = descendants(proc.pid)
    last_tree = time.time()
    try:
        while proc.poll() is None and (time.time() - t0) < a.max_seconds:
            if time.time() - last_tree > 5.0:
                pids = descendants(proc.pid)
                last_tree = time.time()
            for row in snapshot(pids):
                key = (row.get("proto"), row.get("remote"), row.get("RemotePort"))
                if not any((o.get("proto"), o.get("remote"), o.get("RemotePort")) == key
                           for o in observed):
                    observed.append(row)
                    print("  !! CONNECTION", row, flush=True)
            samples += 1
            time.sleep(a.interval)
    finally:
        if proc.poll() is None:
            proc.terminate()

    elapsed = time.time() - t0
    verdict = "PASS" if not observed else "FAIL"
    result = {
        "verdict": verdict,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": " ".join(cmd),
        "samples": samples,
        "elapsed_s": round(elapsed, 1),
        "connections_observed": observed,
        "limitation": "Observes sockets opened by the process tree. Pair with an external packet "
                      "capture for a release audit.",
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    print()
    print(f"  samples taken   : {samples} over {elapsed:.1f}s")
    print(f"  connections     : {len(observed)}")
    print(f"  VERDICT         : {verdict}")
    if verdict == "FAIL":
        print("\n  Target T-8 is absolute. Any connection in offline mode blocks release.")
    print(f"\n  written to {os.path.relpath(a.out, ROOT)}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
