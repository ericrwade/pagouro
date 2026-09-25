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
        rp = os.environ.get("REPEAT_PENALTY", "1.0")   # D-91: the shipped decode's repetition penalty; measure with it
        self.proc = subprocess.Popen([exe, "-m", model, "--port", str(self.port), "-ngl", "0", "-t", str(threads),
                                      "--repeat-penalty", rp, "--log-disable", "--no-webui"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(240):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2)
                return
            except Exception:
                time.sleep(0.5)
        raise SystemExit("llama-server did not start")

    def route(self, prompt: str, probs: bool = False):
        """The router's JSON; with probs=True also (json, p_tool) where p_tool is the model's probability
        of the tool-name token it chose (O-35: the router emits a probability with its decision)."""
        body = {"messages": [{"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": prompt}],
                "temperature": 0, "max_tokens": 96, "grammar": ROUTER_GRAMMAR}
        if probs:
            body.update({"logprobs": True, "top_logprobs": 8})
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
        ch = json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]
        if not probs:
            return ch["message"]["content"]
        return ch["message"]["content"], tool_prob(ch)

    def stop(self):
        try:
            self.proc.terminate()
        except Exception:
            pass


TOOL_TOKENS = ("none", "calc", "time", "pack", "read", "write", "web")


def tool_prob(choice: dict):
    """Probability of the chosen tool-name token: the first generated token whose text begins one of
    the tool names, i.e. the token right after '{"tool":"'. Also the runner-up tool and its probability.
    Returns (p_chosen, p_normalised_over_tool_alternatives, runner_up, p_runner_up) or None."""
    import math
    toks = (choice.get("logprobs") or {}).get("content") or []
    seen = ""
    for t in toks:
        if seen.endswith('"tool":"') or seen.endswith('"tool": "'):
            p = math.exp(t["logprob"])
            alts = {}
            for a in t.get("top_logprobs", []):
                name = a["token"].strip()
                if any(name.startswith(x) for x in TOOL_TOKENS):
                    alts[name] = max(alts.get(name, 0.0), math.exp(a["logprob"]))
            alts[t["token"].strip()] = max(alts.get(t["token"].strip(), 0.0), p)
            z = sum(alts.values()) or 1.0
            others = sorted(((n, v) for n, v in alts.items() if n != t["token"].strip()), key=lambda x: -x[1])
            ru, pru = (others[0] if others else ("", 0.0))
            return round(p, 4), round(p / z, 4), ru, round(pru, 4)
        seen += t["token"]
    return None



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--probs", action="store_true", help="O-35: record the router's probability for its tool choice and report calibration")
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
            pinfo = None
            if a.probs:
                raw, pinfo = srv.route(it["prompt"], probs=True)
            else:
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
            row = {**it, "response": raw, "tool": tool, "arguments": arg, "verdict": verdict, "arg_ok": argv}
            if pinfo:
                row.update({"p_tool": pinfo[0], "p_tool_norm": pinfo[1], "runner_up": pinfo[2], "p_runner_up": pinfo[3]})
            out.append(row)
            ptxt = f"  p={pinfo[0]:.2f} (next {pinfo[2]} {pinfo[3]:.2f})" if pinfo else ""
            print(f"  [{i:3d}/{len(items)}] {it['id']:<10} {verdict:<14} {tool:<12} {arg[:40]}{ptxt}", flush=True)
    finally:
        srv.stop()
    result = {
        "set": "tooluse", "model_label": a.label, "model_file": os.path.basename(a.model),
        "n_items": len(items), "counts": counts, "arg_ok": arg_ok, "arg_total": arg_total,
        "elapsed_s": round(time.time() - t0, 1), "suite_version": spec["version"], "suite_frozen": spec["frozen"],
        "mode": "router-grammar", "items": out,
    }
    if a.probs:
        right = [r["p_tool"] for r in out if r.get("p_tool") is not None and r["verdict"] in ("CALL_RIGHT", "REFRAIN_RIGHT")]
        wrong = [r["p_tool"] for r in out if r.get("p_tool") is not None and r["verdict"] not in ("CALL_RIGHT", "REFRAIN_RIGHT")]
        bins = {"<0.5": [0, 0], "0.5-0.9": [0, 0], ">=0.9": [0, 0]}
        for r in out:
            pr = r.get("p_tool")
            if pr is None:
                continue
            b = "<0.5" if pr < 0.5 else "0.5-0.9" if pr < 0.9 else ">=0.9"
            bins[b][1] += 1
            bins[b][0] += r["verdict"] in ("CALL_RIGHT", "REFRAIN_RIGHT")
        result["calibration"] = {"mean_p_when_right": round(sum(right) / max(1, len(right)), 3), "n_right": len(right),
                                 "mean_p_when_wrong": round(sum(wrong) / max(1, len(wrong)), 3), "n_wrong": len(wrong),
                                 "bins_right_of_n": {k: f"{v[0]}/{v[1]}" for k, v in bins.items()},
                                 "note": "p_tool = model probability of the chosen tool-name token under the router grammar (O-35)"}
        c = result["calibration"]
        print(f"  calibration: mean p right {c['mean_p_when_right']} (n={c['n_right']}), wrong {c['mean_p_when_wrong']} (n={c['n_wrong']}); "
              f"accuracy by bin {c['bins_right_of_n']}")
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
