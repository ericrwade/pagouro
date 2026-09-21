"""Skills for the stick (O-30, docs/SKILLS.md). Standard library only.

A skill is a folder under `skills/`:

    SKILL.md          frontmatter: name, description, license, author, ported_by, source  (+ prose for people)
    tools/*.py        one tool per file: DESCRIPTION (one line), NEEDS_ACT (bool, default False),
                      optional TRIGGER (a regex: when the user's message matches, the harness routes
                      to this tool deterministically, passing the whole message - the 126M router has
                      never seen the tool's name, and a prompt clause does not teach it; the
                      examples.jsonl in the next fine-tune does), def run(argument: str, app) -> str
    packs/*.txt       reference text, indexed beside the stick's own packs
    examples.jsonl    router examples ({"user": ..., "tool": ..., "arguments": ...}) for the next fine-tune
    eval.jsonl        the skill's own test: {"prompt", "tool", "argument", "expect"} rows (see scripts/skill_test.py)
    MANIFEST          "<sha256>  <relative path>" per file, written by scripts/skill_test.py --write-manifest

What the loader enforces, and what it does not:
  * Tool modules are SCREENED, not sandboxed: a module whose source mentions subprocess, socket,
    urllib, http, requests, ctypes, os.system, os.popen, shutil.rmtree, eval( or exec( is refused
    at load with the reason printed. Python cannot be sandboxed from inside Python; the honest
    protection is the hash list, the screen, and reading the code (it is short by construction).
  * Tool names must not collide with the app's own tools or another skill's; a collision is refused.
  * A tool result may contain a line "--": everything after it is shown to the person (provenance,
    raw bytes, hashes) but never sent to the model, which a small model cannot use and is confused by.
  * Every loaded file's hash is compared with MANIFEST when one exists; a mismatch is printed and
    the skill still loads (the owner may be editing it) but is marked MODIFIED in /skills.
  * A plain SKILL.md folder from the wild (no tools/, scripts/ instead, resources/ instead of
    packs/) is accepted: scripts/*.py that expose run() become tools, resources/*.txt become
    packs, and the loader prints which parts it used and which it ignored.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import re

TRIGGERS: dict[str, "re.Pattern[str]"] = {}   # tool name -> regex; the harness routes on a match before asking the model

FORBIDDEN = ("subprocess", "socket", "urllib", "http.", "requests", "ctypes", "os.system", "os.popen",
             "shutil.rmtree", "eval(", "exec(", "__import__", "importlib")


class Skill:
    def __init__(self, folder: str):
        self.folder = folder
        self.key = os.path.basename(folder)
        self.meta: dict[str, str] = {}
        self.tools: dict[str, tuple] = {}     # name -> (fn, description, needs_act)
        self.packs_dir: str | None = None
        self.notes: list[str] = []            # what was used / ignored / refused
        self.hashes: dict[str, str] = {}
        self.modified: list[str] = []
        self.eval_score: str = "untested"


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if _:
                meta[k.strip().lower()] = v.strip().strip('"').strip("'")
    return meta


def file_hashes(folder: str) -> dict[str, str]:
    out = {}
    for dp, _, fns in os.walk(folder):
        for fn in fns:
            if fn == "MANIFEST" or fn.endswith(".pyc") or "__pycache__" in dp:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, folder).replace("\\", "/")
            out[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def read_manifest(folder: str) -> dict[str, str]:
    p = os.path.join(folder, "MANIFEST")
    if not os.path.exists(p):
        return {}
    out = {}
    for line in io.open(p, encoding="utf-8"):
        parts = line.split(None, 1)
        if len(parts) == 2:
            out[parts[1].strip()] = parts[0]
    return out


def screen(src: str) -> str | None:
    """Return the first forbidden token found in a tool's source, or None."""
    for tok in FORBIDDEN:
        if tok in src:
            return tok
    return None


def load_tool_module(path: str):
    spec = importlib.util.spec_from_file_location("skill_tool_" + hashlib.md5(path.encode()).hexdigest()[:8], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def load_skill(folder: str, taken: set[str]) -> Skill | None:
    sk = Skill(folder)
    md = os.path.join(folder, "SKILL.md")
    if not os.path.exists(md):
        return None
    sk.meta = parse_frontmatter(io.open(md, encoding="utf-8").read())
    if not sk.meta.get("name"):
        sk.meta["name"] = sk.key
    # tools/ (ours) or scripts/ (the wild SKILL.md convention)
    tools_dir = next((d for d in (os.path.join(folder, "tools"), os.path.join(folder, "scripts")) if os.path.isdir(d)), None)
    if tools_dir:
        for fn in sorted(os.listdir(tools_dir)):
            if not fn.endswith(".py") or fn.startswith("_"):
                continue
            p = os.path.join(tools_dir, fn)
            src = io.open(p, encoding="utf-8", errors="replace").read()
            bad = screen(src)
            if bad:
                sk.notes.append(f"refused tools/{fn}: source mentions '{bad}'")
                continue
            try:
                mod = load_tool_module(p)
            except Exception as e:  # noqa: BLE001
                sk.notes.append(f"refused tools/{fn}: import failed ({e})")
                continue
            if not callable(getattr(mod, "run", None)):
                sk.notes.append(f"ignored tools/{fn}: no run(argument, app)")
                continue
            name = fn[:-3]
            if name in taken or name in sk.tools:
                sk.notes.append(f"refused tools/{fn}: tool name '{name}' already taken")
                continue
            desc = str(getattr(mod, "DESCRIPTION", "")).strip() or f"{sk.meta['name']}: {name}"
            sk.tools[name] = (mod.run, desc, bool(getattr(mod, "NEEDS_ACT", False)))
            trig = getattr(mod, "TRIGGER", None)
            if trig:
                try:
                    TRIGGERS[name] = re.compile(trig, re.I)
                except re.error as e:
                    sk.notes.append(f"tools/{fn}: TRIGGER regex invalid ({e}); model routing only")
            taken.add(name)
    else:
        sk.notes.append("no tools/ or scripts/ folder: nothing callable; description and packs only")
    packs_dir = next((d for d in (os.path.join(folder, "packs"), os.path.join(folder, "resources")) if os.path.isdir(d)), None)
    if packs_dir:
        n = len([f for f in os.listdir(packs_dir) if f.endswith(".txt")])
        if n:
            sk.packs_dir = packs_dir
        else:
            sk.notes.append(f"ignored {os.path.basename(packs_dir)}/: no .txt files (only .txt is indexed)")
    for fn in os.listdir(folder):
        if fn.endswith(".md") and fn != "SKILL.md":
            sk.notes.append(f"ignored {fn}: prose for people, not for the model")
    sk.hashes = file_hashes(folder)
    man = read_manifest(folder)
    if man:
        sk.modified = sorted(set(k for k in sk.hashes if man.get(k) != sk.hashes[k]) | set(k for k in man if k not in sk.hashes))
    else:
        sk.notes.append("no MANIFEST (run scripts/skill_test.py --write-manifest)")
    return sk


def load_all(skills_root: str, app_tools: dict, packs=None) -> list[Skill]:
    """Register every skill's tools into `app_tools` (same table, same sandbox rules) and its
    packs into `packs` (if given). Returns the loaded skills, for /skills."""
    if not os.path.isdir(skills_root):
        return []
    taken = set(app_tools.keys())
    scores = {}
    try:   # scripts/skill_test.py leaves its last report beside the skills; /skills shows it
        import json
        for r in json.load(io.open(os.path.join(skills_root, "last_test.json"), encoding="utf-8")):
            t, rt = r.get("tools", {}), r.get("routing")
            scores[os.path.basename(r["folder"])] = (f"tools {t.get('hits', 0)}/{t.get('of', 0)}"
                                                     + (f", routing {rt['tool_acc']}/{rt['of']} on {rt['model']}" if rt else ""))
    except Exception:  # noqa: BLE001
        pass
    out = []
    for name in sorted(os.listdir(skills_root)):
        folder = os.path.join(skills_root, name)
        if not os.path.isdir(folder):
            continue
        sk = load_skill(folder, taken)
        if sk is None:
            continue
        sk.eval_score = scores.get(sk.key, "untested")
        for tname, (fn, desc, needs) in sk.tools.items():
            app_tools[tname] = (fn, f"[{sk.meta['name']}] {desc}", needs)
        if sk.packs_dir and packs is not None:
            try:
                packs.add_dir(sk.packs_dir, f"skill:{sk.key}")
            except Exception as e:  # noqa: BLE001
                sk.notes.append(f"packs not indexed: {e}")
        out.append(sk)
    return out


def describe(sk: Skill) -> str:
    m = sk.meta
    head = f"{m.get('name', sk.key):<16} {m.get('description', '')[:60]}"
    who = " / ".join(x for x in (m.get("author", ""), ("ported by " + m["ported_by"]) if m.get("ported_by") else "") if x)
    lines = [head,
             f"    licence {m.get('license', '?')}; {who or 'no author named'}; tools: {', '.join(sk.tools) or 'none'}"
             f"; packs: {'yes' if sk.packs_dir else 'no'}; eval: {sk.eval_score}"
             + (f"; MODIFIED since MANIFEST: {', '.join(sk.modified)}" if sk.modified else "")]
    for n in sk.notes:
        lines.append("    note: " + n)
    return "\n".join(lines)
