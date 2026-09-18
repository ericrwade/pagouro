"""Tool-use axis of the frozen suite (evals/tooluse.json).

Unlike the other three sets this one runs through llama-server, because the
routing decision is made under the app's GBNF grammar (app/pagouro_app.py), and the
score must measure the model the way the app uses it. Results land in
evals/results/<label>__tooluse.json in the same shape as the other sets, so
`python evals/run_eval.py --report` shows all four columns.

    python evals/run_tooluse.py --model data/gguf_real/pagouro-real-q8_0.gguf --label pagouro-real
"""

from __future__ import annotations

import argparse
import io
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(ROOT, "evals")
RESULTS_DIR = os.path.join(EVAL_DIR, "results")
sys.path.insert(0, os.path.join(ROOT, "app"))
from prompts import ROUTER_PROMPT  # noqa: E402

# Import the grammar from the app without starting it (module has no side effects
# beyond console setup).
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("pagouro_app", os.path.join(ROOT, "app", "pagouro_app.py"))
_app = importlib.util.module_from_spec(_spec)
_saved_argv, sys.argv = sys.argv, [sys.argv[0]]
_spec.loader.exec_module(_app)
sys.argv = _saved_argv
ROUTER_GRAMMAR = _app.ROUTER_GRAMMAR


def safe_calc(expr: str):
    import ast, operator
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
           ast.USub: operator.neg, ast.UAdd: operator.pos}
    try:
        tree = ast.parse(expr.replace("^", "**").replace(",", ""), mode="eval")
    except SyntaxError:
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.operand))
        raise ValueError
    try:
        return ev(tree)
    except Exception:
        return None


class Server:
    def __init__(self, model: str, threads: int):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        exe = os.path.join(ROOT, "tools", "llamacpp", "llama-server.exe")
        self.proc = subprocess.Popen([exe, "-m", model, "--port", str(self.port), "-ngl", "0", "-t", str(threads),
                                      "--log-disable", "--no-webui"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(240):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2)
                return
            except Exception:
                time.sleep(0.5)
        raise SystemExit("llama-server did not start")

    def route(self, prompt: str) -> str:
        body = {"messages": [{"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": prompt}],
                "temperature": 0, "max_tokens": 96, "grammar": ROUTER_GRAMMAR}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]

    def stop(self):
        try:
            self.proc.terminate()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()

    with io.open(os.path.join(EVAL_DIR, "tooluse.json"), encoding="utf-8") as f:
        spec = json.load(f)
    items = spec["items"]
    print(f"\n=== tooluse: {len(items)} items -> {a.label} ===", flush=True)
    srv = Server(a.model, a.threads)
    out, counts = [], {}
    arg_ok = arg_total = 0
    t0 = time.time()
    try:
        for i, it in enumerate(items, 1):
            raw = srv.route(it["prompt"])
            try:
                d = json.loads(raw)
                tool, arg = str(d.get("tool", "none")), str(d.get("arguments", ""))
            except Exception:
                tool, arg = "none", ""
            exp = it["expect"]
            if exp == "none":
                verdict = "REFRAIN_RIGHT" if tool == "none" else "SPURIOUS"
            elif tool == "none":
                verdict = "MISSED"
            elif tool == exp:
                verdict = "CALL_RIGHT"
            else:
                verdict = "CALL_WRONG"
            argv = None
            if exp == "calc" and tool == "calc":
                arg_total += 1
                v = safe_calc(arg)
                argv = v is not None and abs(float(v) - float(it["expect_value"])) < 1e-6
                arg_ok += bool(argv)
            counts[verdict] = counts.get(verdict, 0) + 1
            out.append({**it, "response": raw, "tool": tool, "arguments": arg, "verdict": verdict, "arg_ok": argv})
            print(f"  [{i:3d}/{len(items)}] {it['id']:<10} {verdict:<14} {tool:<12} {arg[:40]}", flush=True)
    finally:
        srv.stop()
    result = {
        "set": "tooluse", "model_label": a.label, "model_file": os.path.basename(a.model),
        "n_items": len(items), "counts": counts, "arg_ok": arg_ok, "arg_total": arg_total,
        "elapsed_s": round(time.time() - t0, 1), "suite_version": spec["version"], "suite_frozen": spec["frozen"],
        "mode": "router-grammar", "items": out,
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, f"{a.label}__tooluse.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    n_call = sum(1 for it in items if it["expect"] != "none")
    n_none = len(items) - n_call
    print(f"  -> right {counts.get('CALL_RIGHT', 0)}/{n_call} calls, wrong-tool {counts.get('CALL_WRONG', 0)}, "
          f"missed {counts.get('MISSED', 0)}, spurious {counts.get('SPURIOUS', 0)}/{n_none}, "
          f"calc args ok {arg_ok}/{arg_total}   saved {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
