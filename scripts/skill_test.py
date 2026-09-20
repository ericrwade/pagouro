"""`pagouro skill test` (O-30): the offline check a skill folder must pass before it goes in the
catalogue. Three layers, each printed with a number:

  1. static   frontmatter complete (name, description, license, author, source); tools screened
              and importable; examples.jsonl and eval.jsonl parse; eval prompts disjoint from the
              examples and from the frozen tool-use suite (evals/tooluse.json); MANIFEST matches
              (or --write-manifest writes it).
  2. tools    every eval row's tool is run with the row's argument; the output must contain
              `expect`. This is the deterministic half: no model involved.
  3. routing  with --model, every eval prompt goes through the router (the app's grammar + the
              skill-extended prompt) on the stick model; reports tool-choice accuracy. Argument
              correctness is reported too (exact match after whitespace/case folding) but a
              wrong argument with the right tool is the harness's job to recover (refine_args).

    python scripts/skill_test.py skills/unit_convert [--model gguf_flash/pagouro-flash-sft2.gguf] [--write-manifest]
    python scripts/skill_test.py --all [--catalogue]      # every folder under skills/; --catalogue rewrites skills/CATALOGUE.md
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
import skills as S  # noqa: E402

REQUIRED_META = ("name", "description", "license", "author", "source")


def rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in io.open(path, encoding="utf-8") if l.strip()]


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def test_folder(folder: str, model: str | None, write_manifest: bool, threads: int) -> dict:
    rep: dict = {"folder": os.path.relpath(folder, ROOT).replace("\\", "/"), "problems": []}
    sk = S.load_skill(folder, set(["calc", "time", "pack_search", "read_file", "write_note", "web_search"]))
    if sk is None:
        rep["problems"].append("no SKILL.md"); return rep
    rep["name"] = sk.meta.get("name", sk.key)
    for k in REQUIRED_META:
        if not sk.meta.get(k):
            rep["problems"].append(f"SKILL.md frontmatter missing '{k}'")
    if sk.meta.get("license", "").lower() in ("", "unknown", "?", "none"):
        rep["problems"].append("licence must be nameable (same rule as the corpus)")
    for n in sk.notes:
        if n.startswith("refused"):
            rep["problems"].append(n)
    ex = rows(os.path.join(folder, "examples.jsonl"))
    ev = rows(os.path.join(folder, "eval.jsonl"))
    if len(ex) < 10:
        rep["problems"].append(f"examples.jsonl has {len(ex)} rows; want >= 10")
    if len(ev) < 10:
        rep["problems"].append(f"eval.jsonl has {len(ev)} rows; want >= 10")
    ex_prompts = {norm(r.get("user", "")) for r in ex}
    frozen = set()
    fz = os.path.join(ROOT, "evals", "tooluse.json")
    if os.path.exists(fz):
        frozen = {norm(it["prompt"]) for it in json.load(io.open(fz, encoding="utf-8"))["items"]}
    for r in ev:
        p = norm(r.get("prompt", ""))
        if p in ex_prompts:
            rep["problems"].append(f"eval {r.get('id')} duplicates an examples.jsonl row")
        if p in frozen:
            rep["problems"].append(f"eval {r.get('id')} duplicates a frozen tool-use suite prompt")
        if r.get("tool") not in sk.tools and r.get("tool") not in ("none", "calc", "time", "pack_search"):
            rep["problems"].append(f"eval {r.get('id')} names tool '{r.get('tool')}' which this skill does not provide")
    # layer 2: tools
    hits, fails = 0, []
    for r in ev:
        t = r.get("tool")
        if t not in sk.tools:
            continue
        fn = sk.tools[t][0]
        try:
            out = fn(r.get("argument", ""), None)
        except Exception as e:  # noqa: BLE001
            out = f"tool error: {e}"
        if r.get("expect", "") in out:
            hits += 1
        else:
            fails.append((r.get("id"), r.get("argument"), out[:90], r.get("expect")))
    n_tool_rows = sum(1 for r in ev if r.get("tool") in sk.tools)
    rep["tools"] = {"hits": hits, "of": n_tool_rows, "fails": fails}
    # layer 2b: end to end without a model — the trigger picks the tool and the tool gets the WHOLE prompt
    e_hits, e_fails, triggered = 0, [], 0
    for r in ev:
        trig = next((n for n, p in S.TRIGGERS.items() if n in sk.tools and p.search(r["prompt"])), None)
        if trig is None:
            e_fails.append((r.get("id"), "no trigger fired (needs the model's routing)", "", r.get("expect")))
            continue
        triggered += 1
        if trig != r.get("tool"):
            e_fails.append((r.get("id"), f"trigger chose {trig}", "", r.get("tool"))); continue
        try:
            out = sk.tools[trig][0](r["prompt"], None)
        except Exception as e:  # noqa: BLE001
            out = f"tool error: {e}"
        if r.get("expect", "") in out:
            e_hits += 1
        else:
            e_fails.append((r.get("id"), r["prompt"], out[:90], r.get("expect")))
    rep["e2e"] = {"hits": e_hits, "of": len(ev), "triggered": triggered, "fails": e_fails}
    # manifest
    man = S.read_manifest(folder)
    if write_manifest:
        with io.open(os.path.join(folder, "MANIFEST"), "w", encoding="utf-8", newline="\n") as f:
            for rel, h in sorted(sk.hashes.items()):
                f.write(f"{h}  {rel}\n")
        rep["manifest"] = "written"
    elif not man:
        rep["problems"].append("no MANIFEST (run with --write-manifest)")
    elif sk.modified:
        rep["problems"].append("MANIFEST mismatch: " + ", ".join(sk.modified))
    else:
        rep["manifest"] = "ok"
    # layer 3: routing
    if model:
        rep["routing"] = route_eval(sk, ev, model, threads)
    return rep


def route_eval(sk: S.Skill, ev: list[dict], model: str, threads: int) -> dict:
    """Route each eval prompt through the stick model with the skill's tools in grammar + prompt."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_tooluse", os.path.join(ROOT, "evals", "run_tooluse.py"))
    rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)  # type: ignore[union-attr]
    from prompts import ROUTER_PROMPT
    app_mod = rt._app
    tools = [t for t in app_mod.OFFLINE_TOOLS] + list(sk.tools)
    grammar = app_mod.router_grammar(tools)
    names = "/".join(sk.tools)
    clauses = "; ".join(f"{n} for {d}" for n, (_, d, _) in sk.tools.items())
    prompt = ROUTER_PROMPT.replace('"arguments": string}', f'"arguments": string}} (also: {names})') + f" Use {clauses}."
    srv = rt.Server(model, threads)
    try:
        right_tool, right_arg, harness_ok, log = 0, 0, 0, []
        for r in ev:
            body = {"messages": [{"role": "system", "content": prompt}, {"role": "user", "content": r["prompt"]}],
                    "temperature": 0, "max_tokens": 96, "grammar": grammar}
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{srv.port}/v1/chat/completions",
                                         data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
            raw = json.loads(urllib.request.urlopen(req, timeout=180).read())["choices"][0]["message"]["content"]
            try:
                d = json.loads(raw)
            except Exception:
                d = {}
            got_t, got_a = str(d.get("tool", "?")), str(d.get("arguments", ""))
            ok_t = got_t == r.get("tool")
            ok_a = ok_t and norm(got_a) == norm(r.get("argument", ""))
            right_tool += ok_t; right_arg += ok_a
            trig = next((n for n, p in S.TRIGGERS.items() if n in sk.tools and p.search(r["prompt"])), None)
            harness_ok += (trig or got_t) == r.get("tool")       # what the app actually does: trigger first, then model
            log.append({"id": r.get("id"), "want": r.get("tool"), "got": got_t, "arg": got_a[:60], "ok": ok_t, "trigger": trig})
        return {"tool_acc": right_tool, "arg_exact": right_arg, "harness_acc": harness_ok, "of": len(ev),
                "model": os.path.basename(model), "log": log}
    finally:
        srv.stop()


def catalogue(reports: list[dict]) -> str:
    lines = ["# Skills catalogue", "",
             "Generated by `scripts/skill_test.py --all --catalogue`. Install = copy the folder onto the stick's `skills/`.",
             "Every row: what it does, the licence (nameable, or it is not listed), who wrote it, who ported it,",
             "the offline tool-eval score (deterministic), the end-to-end score with the skill's own triggers and no model,",
             "the routing score on the named stick model when measured (model alone, and the harness: trigger first, then model),",
             "and the MANIFEST state. \"Runs on Pagouro\" (O-29) may be used by any skill whose eval passes on the current stick model.", "",
             "| skill | does | licence | author | ported by | tool eval | end-to-end (triggers) | routing | manifest |", "|---|---|---|---|---|---|---|---|---|"]
    for r in reports:
        folder = os.path.join(ROOT, r["folder"])
        sk = S.load_skill(folder, set())
        m = sk.meta if sk else {}
        t = r.get("tools", {})
        rt = r.get("routing")
        rt_s = f"model {rt['tool_acc']}/{rt['of']}, harness {rt['harness_acc']}/{rt['of']} ({rt['model']})" if rt else "not measured"
        e = r.get("e2e", {})
        lines.append(f"| `{r.get('name')}` | {m.get('description', '')} | {m.get('license', '?')} | {m.get('author', '?')} | "
                     f"{m.get('ported_by', '')} | {t.get('hits', 0)}/{t.get('of', 0)} | {e.get('hits', 0)}/{e.get('of', 0)} | {rt_s} | {r.get('manifest', 'missing')} |")
    lines += ["", "## Wanted", "", "See `docs/SKILLS.md` for the ranked list of twenty; take one, port it, run this script, open a PR with the output pasted in."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--write-manifest", action="store_true")
    ap.add_argument("--catalogue", action="store_true")
    a = ap.parse_args()
    folders = sorted(d for d in glob.glob(os.path.join(ROOT, "skills", "*")) if os.path.isdir(d)) if a.all else [os.path.abspath(a.folder)]
    reports = []
    for f in folders:
        r = test_folder(f, a.model, a.write_manifest, a.threads)
        reports.append(r)
        t = r.get("tools", {})
        e = r.get("e2e", {})
        print(f"{r.get('name', r['folder'])}: tools {t.get('hits', 0)}/{t.get('of', 0)}; end-to-end via triggers {e.get('hits', 0)}/{e.get('of', 0)}"
              + (f"; model routing alone {r['routing']['tool_acc']}/{r['routing']['of']}, harness (trigger then model) {r['routing']['harness_acc']}/{r['routing']['of']}" if r.get("routing") else "")
              + f"; manifest {r.get('manifest', 'missing')}; problems {len(r['problems'])}")
        for p in r["problems"]:
            print("   ! " + p)
        for fl in t.get("fails", []):
            print(f"   x {fl[0]} arg={fl[1]!r} got={fl[2]!r} want={fl[3]!r}")
        for fl in e.get("fails", []):
            print(f"   e {fl[0]} {fl[1][:50]!r} got={fl[2]!r} want={fl[3]!r}")
        for row in (r.get("routing") or {}).get("log", []):
            if not row["ok"]:
                print(f"   ~ {row['id']} routed to {row['got']} (want {row['want']}) arg={row['arg']!r}")
    if a.catalogue:
        io.open(os.path.join(ROOT, "skills", "CATALOGUE.md"), "w", encoding="utf-8", newline="\n").write(catalogue(reports))
        print("skills/CATALOGUE.md written")
    io.open(os.path.join(ROOT, "skills", "last_test.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(reports, indent=1) + "\n")
    return 0 if all(not r["problems"] and r.get("tools", {}).get("hits") == r.get("tools", {}).get("of") for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
