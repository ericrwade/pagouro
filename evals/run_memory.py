"""Memory eval (O-23, level 1): does what the owner said in an earlier session come back in a
later one? Three stages per item, three numbers:

  ROUTED     the router chose pack_search for the question (model)
  RETRIEVED  the told line is among the top-3 pack_search hits, labelled as the owner's words
             (retrieval; model-independent, so a low number here is the index's fault)
  ANSWERED   given that tool result, the model's answer contains an accepted key (model)

    python evals/run_memory.py --model data/gguf_real/pagouro-real-q8_0.gguf --label pagouro-real

All ten "told" lines are written into a temporary workspace/memory folder (dated as earlier
sessions), the real packs are loaded beside them, and the questions are asked cold, one at a
time, with no conversation history -- the strictest version of "a later session".
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "app"))
_argv = sys.argv; sys.argv = [_argv[0]]                       # the app parses argv on import
from packsearch import Packs                                    # noqa: E402
from prompts import SYSTEM_PROMPT                               # noqa: E402
sys.path.insert(0, EVAL_DIR)
from run_tooluse import Server                                  # noqa: E402  (router + grammar, same as the app)
sys.argv = _argv

import urllib.error  # noqa: E402
import urllib.request  # noqa: E402


def n_ctx(srv: Server) -> int:
    try:
        props = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{srv.port}/props", timeout=10).read())
        return int(props.get("default_generation_settings", {}).get("n_ctx", 512))
    except Exception:
        return 512


def answer(srv: Server, question: str, tool_result: str, ctx: int, max_tokens: int = 120) -> str:
    # Fit the tool result to the model's window the way the app does (trim the tool result, never
    # the question): ~2.8 chars/token (dates and labels tokenize badly), minus prompt overhead and the answer budget.
    budget_chars = max(300, int((ctx - max_tokens - 140) * 2.8))
    msgs = [{"role": "system", "content": SYSTEM_PROMPT.format(date=dt.date.today().isoformat())},
            {"role": "user", "content": question},
            {"role": "tool", "content": f"pack_search: {tool_result[:budget_chars]}"}]
    body = {"messages": msgs, "temperature": 0, "max_tokens": max_tokens}
    req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"<<HTTP {e.code}: {e.read()[:200]!r}>>"


_NUM = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?(?![\w])")


def numbers_preserved(response: str, sources: str) -> bool | None:
    """D-66 audit column (from Rahul's guide: track numeric strings separately). Every number in the
    answer must appear in the tool result or the question; None when the answer has no numbers."""
    got = {n.replace(",", "") for n in _NUM.findall(response)}
    if not got:
        return None
    have = {n.replace(",", "") for n in _NUM.findall(sources)}
    return got <= have


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    spec = json.load(io.open(os.path.join(EVAL_DIR, "memory.json"), encoding="utf-8"))
    items = spec["items"]

    tmp = tempfile.mkdtemp(prefix="pagouro_mem_")
    mem = os.path.join(tmp, "memory"); os.makedirs(mem)
    with io.open(os.path.join(mem, "remembered.txt"), "w", encoding="utf-8", newline="\n") as f:
        for i, it in enumerate(items):
            day = (dt.date.today() - dt.timedelta(days=30 - i)).isoformat()
            f.write(f"{day}: {it['told']}\n\n")
    packs = Packs(os.path.join(ROOT, "packs"))
    packs.add_dir(mem, "memory")

    print(f"\n=== memory: {len(items)} items -> {a.label} ===", flush=True)
    srv = Server(a.model, a.threads)
    ctx = n_ctx(srv)
    print(f"  model window: {ctx} tokens", flush=True)
    out, c = [], {"ROUTED": 0, "RETRIEVED": 0, "ANSWERED": 0, "NUMERIC_CHECKED": 0, "NUMERIC_PRESERVED": 0}
    t0 = time.time()
    try:
        for i, it in enumerate(items, 1):
            raw = srv.route(it["ask"])
            try:
                routed = json.loads(raw).get("tool") == "pack_search"
            except Exception:
                routed = False
            hits = packs.search(it["ask"], k=3)
            retrieved = any(n.startswith("memory:") and it["told"] in t for n, t, _ in hits)
            mem = [h for h in hits if h[0].startswith("memory:")]      # mirror the app: owner's words first and alone
            if mem:
                hits = mem[:2]
            tool_result = "\n\n".join(
                f"[{'YOUR OWN WORDS, from ' + n[len('memory:'):] if n.startswith('memory:') else n}] {t[:700]}"
                for n, t, _ in hits) or "NO_MATCH"
            resp = answer(srv, it["ask"], tool_result, ctx)
            low = resp.lower()
            answered = any(k.lower() in low for k in it["keys"])
            npres = numbers_preserved(resp, tool_result + " " + it["ask"] + " " + it["told"])
            c["ROUTED"] += routed; c["RETRIEVED"] += retrieved; c["ANSWERED"] += answered
            if npres is not None:
                c["NUMERIC_CHECKED"] += 1; c["NUMERIC_PRESERVED"] += npres
            out.append({**it, "router": raw, "routed": routed, "retrieved": retrieved, "answered": answered,
                        "numbers_preserved": npres, "top_hit": hits[0][0] if hits else None, "response": resp})
            print(f"  [{i:2d}/{len(items)}] {it['id']}  routed={int(routed)} retrieved={int(retrieved)} answered={int(answered)} "
                  f"numbers={'-' if npres is None else int(npres)}  {resp[:60]!r}", flush=True)
    finally:
        srv.stop()
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(items)
    result = {"set": "memory", "model_label": a.label, "model_file": os.path.basename(a.model), "n_items": n,
              "counts": c, "rates": {k: round(v / n, 3) for k, v in c.items()},
              "elapsed_s": round(time.time() - t0, 1), "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "items": out}
    os.makedirs(os.path.join(EVAL_DIR, "results"), exist_ok=True)
    path = os.path.join(EVAL_DIR, "results", f"{a.label}__memory.json")
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"  -> routed {c['ROUTED']}/{n}  retrieved {c['RETRIEVED']}/{n}  answered {c['ANSWERED']}/{n}  "
          f"numbers preserved {c['NUMERIC_PRESERVED']}/{c['NUMERIC_CHECKED']} answers-with-numbers   ({result['elapsed_s']}s)   saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
