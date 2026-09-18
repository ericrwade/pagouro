"""Generate SFT conversations at scale from a LOCAL open-weights teacher (D-30).

Teacher: Qwen/Qwen2.5-7B-Instruct-GGUF (Apache-2.0), run by llama-server on this
machine. No API is ever called. Every row records its generator; the source gets a
ledger row like any other (scripts/ledger_synthetic.py at the end of the run).

Classes (same shapes as sft/build_harness_seed.py, so the model sees one dialect):
  router      teacher writes varied user messages per tool category, with the
              argument; the label is by construction.
  tool_answer the tool is EXECUTED (calc for real, pack_search over the real packs,
              time from a random clock, read_file on a teacher-written file,
              write_note simulated); the teacher then writes the answer FROM the
              result, including NO_MATCH and REFUSED cases.
  grounded    a short original passage, one answerable and one unanswerable
              question, "the passage doesn't say" for the second.
  abstain     invented entities -> refusal in varied wording.
  confident   real general-knowledge questions -> plain 2-4 sentence answers.
  synthesis   "is X more like Y or Z" comparisons answered with a position.
  multi_turn  2-3 exchanges where the follow-up depends on the first answer.

Validation before a row is kept: JSON shape, length caps, calc answers must contain
the computed number, no overlap with the frozen evals (Jaccard >= 0.6 on prompt
words), no duplicate user message across all SFT files. Runs are resumable: the
output is appended per row and counts are read back at start.

    python scripts/generate_synthetic_harness.py --per-class 400 --threads 8
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import random
import re
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from prompts import ROUTER_PROMPT, TOOL_NAMES, router_json, system_prompt  # noqa: E402
from packsearch import Packs  # noqa: E402

OUT = os.path.join(ROOT, "sft", "synthetic_harness.jsonl")
LOG = os.path.join(ROOT, "runs", "synthetic_harness.log")
TEACHER = os.path.join(ROOT, "tools", "teacher", "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf")
SOURCE = "qwen2.5-7b-instruct-q4_k_m (Apache-2.0, run locally via llama-server)"

TOPICS = ["cooking", "travel", "personal finance", "gardening", "home repair", "history", "geography",
          "chemistry", "astronomy", "music", "sports", "law", "medicine basics", "economics", "software",
          "cars", "weather", "pets", "parenting", "fitness", "photography", "sailing", "farming",
          "carpentry", "bicycles", "chess", "languages", "philosophy", "architecture", "elections",
          "banking", "insurance", "taxes", "shipping", "trains", "aviation", "mining", "textiles",
          "printing", "libraries", "museums", "hiking", "camping", "first aid", "water purification",
          "bread baking", "coffee", "tea", "wine", "cheese", "beekeeping", "poultry", "fishing",
          "knots", "maps", "compasses", "radio", "electricity", "plumbing", "roofing", "bitcoin",
          "central banks", "constitutions", "parliaments", "monarchy", "republics", "trade", "tariffs"]


# --------------------------------------------------------------------------
# teacher
# --------------------------------------------------------------------------
class Teacher:
    def __init__(self, model: str, threads: int):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        exe = os.path.join(ROOT, "tools", "llamacpp", "llama-server.exe")
        self.proc = subprocess.Popen([exe, "-m", model, "--port", str(self.port), "-ngl", "0", "-t", str(threads),
                                      "-c", "4096", "--log-disable", "--no-webui"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(240):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("teacher did not start")
        self.tokens_out = 0

    def json(self, prompt: str, max_tokens: int = 700, temperature: float = 0.85, schema: dict | None = None) -> dict | None:
        body = {"messages": [{"role": "system", "content": "You write training data for a small offline assistant. Output only JSON."},
                             {"role": "user", "content": prompt}],
                "temperature": temperature, "max_tokens": max_tokens}
        if schema is not None:
            body["json_schema"] = schema        # the server turns it into a grammar: the shape cannot drift
        else:
            body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=900).read())
        except Exception as e:
            log(f"teacher error: {e}")
            return None
        self.tokens_out += d.get("usage", {}).get("completion_tokens", 0)
        try:
            return json.loads(d["choices"][0]["message"]["content"])
        except Exception:
            return None

    def verify(self, question: str, answer: str) -> bool:
        """Second pass at temperature 0: is the answer factually correct and does it
        take a position? A 7B teacher states wrong facts confidently now and then
        ("Roquefort has the highest fat content", smoke test 2026-09-18); a
        no-bluff model must not be trained on those."""
        d = self.json("Question: " + question + chr(10) + "Answer: " + answer + chr(10) + chr(10) +
                      "Is the answer factually correct, free of invented specifics, and does it commit to a position rather than hedge? "
                      'Output JSON: {"correct": true or false, "issue": string}', max_tokens=120, temperature=0.0,
                      schema={"type": "object", "properties": {"correct": {"type": "boolean"}, "issue": {"type": "string"}},
                              "required": ["correct", "issue"]})
        return bool(d and d.get("correct") is True)

    def stop(self):
        try:
            self.proc.terminate()
        except Exception:
            pass


def items_schema(props: dict, key: str = "items") -> dict:
    return {"type": "object", "properties": {key: {"type": "array", "items": {
        "type": "object", "properties": props, "required": list(props)}}}, "required": [key]}

STR = {"type": "string"}


def log(msg: str):
    line = f"{dt.datetime.now().strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# --------------------------------------------------------------------------
# validation helpers
# --------------------------------------------------------------------------
def norm_words(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", s.lower()))


def load_eval_prompts() -> list[set[str]]:
    out = []
    for name in ("bluff.json", "calibration.json", "deflection.json", "tooluse.json"):
        p = os.path.join(ROOT, "evals", name)
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as f:
                out += [norm_words(i["prompt"]) for i in json.load(f)["items"]]
    return out


def overlaps_eval(text: str, evals: list[set[str]]) -> bool:
    q = norm_words(text)
    if not q:
        return False
    for e in evals:
        if e and len(q & e) / len(q | e) >= 0.6:
            return True
    return False


def existing_user_messages() -> set[str]:
    seen = set()
    for fn in os.listdir(os.path.join(ROOT, "sft")):
        if not fn.endswith(".jsonl"):
            continue
        for line in io.open(os.path.join(ROOT, "sft", fn), encoding="utf-8"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            msgs = d.get("messages") or [{"role": "user", "content": d.get("question", "")}]
            for m in msgs:
                if m["role"] == "user":
                    seen.add(" ".join(m["content"].lower().split())[:200])
    return seen


def safe_calc(expr: str):
    """Evaluate with the same rules as the app's calc tool."""
    import ast, operator
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
           ast.USub: operator.neg, ast.UAdd: operator.pos}
    try:
        tree = ast.parse(expr.replace("^", "**"), mode="eval")
    except SyntaxError:
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 64:
                raise ValueError
            return ops[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.operand))
        raise ValueError
    try:
        v = ev(tree)
    except Exception:
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, float):
        v = round(v, 4)
    return v


def fmt_num(v) -> str:
    return str(v)


# --------------------------------------------------------------------------
# generators. Each returns a list of {"kind", "messages"} rows.
# --------------------------------------------------------------------------
def gen_router(t: Teacher, rng: random.Random, packs: Packs) -> list[dict]:
    rows = []
    spec = {
        "calc": ("needs arithmetic to answer (percentages, unit conversions with a given factor, totals, averages, powers). Give the exact arithmetic expression using only numbers and + - * / ( ) ** %.", "expression"),
        "time": ("asks for the current date, time, day of the week, or year, in different phrasings.", None),
        "pack_search": ("asks what a classic economics or liberty text says about a topic (Mill's On Liberty, Bastiat's Economic Sophisms, Adam Smith, Locke), or asks to search the reference packs. Give a 2-5 word search query.", "query"),
        "read_file": ("asks the assistant to read, open, summarise or check a specific text file, naming a path (Windows or Unix style, or workspace/notes/...). Give the path.", "path"),
        "write_note": ("asks the assistant to save, note, remember or jot down a specific short piece of text. Give the exact note text.", "note"),
        "none": ("is an ordinary question or remark that needs NO tool: a definition, an opinion, a comparison, a greeting, a question about something that may not exist, a request for a short explanation, or a question about the assistant itself.", None),
    }
    for tool, (desc, argkey) in spec.items():
        topic = rng.choice(TOPICS)
        argline = f' "{argkey}": string,' if argkey else ""
        props = {"message": STR}
        if argkey:
            props[argkey] = STR
        d = t.json(f"Write 8 different short messages a user might type that each {desc} Vary the wording, length and register; some casual, some formal; roughly half about {topic}. "
                   f'Output JSON: {{"items": [{{"message": string,{argline} }}]}}', schema=items_schema(props))
        if not d:
            continue
        for it in d.get("items", []):
            if not isinstance(it, dict):
                continue
            msg = str(it.get("message", "")).strip()
            if not msg:
                continue
            arg = str(it.get(argkey, "")).strip() if argkey else ""
            if argkey and len(arg) < 2:
                continue                      # a tool call with no argument is not a training example
            if tool == "calc":
                if safe_calc(arg) is None:
                    continue
            rows.append({"kind": "router", "messages": [
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": msg},
                {"role": "assistant", "content": router_json(tool, arg)}],
                "_tool": tool, "_arg": arg})
    return rows


def gen_tool_answers(t: Teacher, rng: random.Random, packs: Packs, router_rows: list[dict]) -> list[dict]:
    rows = []
    for r in router_rows:
        tool, arg, msg = r["_tool"], r["_arg"], r["messages"][1]["content"]
        if tool == "none":
            continue
        # EXECUTE the tool, for real where possible
        if tool == "calc":
            v = safe_calc(arg)
            if v is None:
                continue
            result = f"calc: {arg} = {fmt_num(v)}"
            must_contain = fmt_num(v)
        elif tool == "time":
            when = dt.datetime(2026, 1, 1) + dt.timedelta(minutes=rng.randrange(0, 1400 * 1440))
            result = "time: local date and time: " + when.strftime("%A %Y-%m-%d %H:%M")
            must_contain = None
        elif tool == "pack_search":
            hits = packs.search(arg, k=1)
            result = ("pack_search: " + f"[{hits[0][0]}] {hits[0][1][:600]}") if hits else "pack_search: NO_MATCH: nothing in the loaded packs covers this."
            must_contain = None
        elif tool == "read_file":
            if rng.random() < 0.25:
                result = f"read_file: could not read: [Errno 2] No such file or directory: '{arg}'"
            elif rng.random() < 0.15:
                result = f"read_file: REFUSED: {arg} is outside the workspace and you did not name it in this message."
            else:
                fd = t.json(f'Write the plausible contents (60-140 words, plain text, no markdown) of a text file at path "{arg}" that the user asked about with: "{msg}". Output JSON: {{"content": string}}', max_tokens=300)
                content = (fd or {}).get("content", "").strip()
                if not content:
                    continue
                result = f"read_file: [{os.path.basename(arg)}, first {len(content)} chars]\n{content}"
            must_contain = None
        elif tool == "write_note":
            if rng.random() < 0.3:
                result = "write_note: REFUSED: READ-ONLY mode. Type /act to allow writing to the workspace."
            else:
                stamp = (dt.datetime(2026, 1, 1) + dt.timedelta(minutes=rng.randrange(0, 1400 * 1440))).strftime("%Y%m%d-%H%M%S")
                result = f"write_note: wrote workspace\\notes\\{stamp}.txt"
            must_contain = None
        else:
            continue
        d = t.json(
            "You are writing the assistant's reply in a training example. The assistant is a small offline model. "
            f"The user said: \"{msg}\". A tool then returned this line:\n{result}\n\n"
            "Write the assistant's reply: 1-3 sentences, answer FROM the tool line, do not add facts the line does not contain, "
            "state numbers exactly as given, and if the line says NO_MATCH / REFUSED / could not read, say so plainly and suggest the obvious next step "
            "(paste the text; type /act; check the path). Never mention 'the tool line' or 'tool' explicitly. "
            'Output JSON: {"reply": string}', max_tokens=220, temperature=0.6)
        reply = (d or {}).get("reply", "").strip()
        if not reply or len(reply) > 600:
            continue
        if must_contain and must_contain not in reply.replace(",", ""):
            continue
        rows.append({"kind": "tool_answer", "messages": [
            {"role": "system", "content": system_prompt(rand_date(rng))},
            {"role": "user", "content": msg},
            {"role": "tool", "content": result},
            {"role": "assistant", "content": reply}]})
    return rows


def rand_date(rng: random.Random) -> str:
    return (dt.date(2026, 1, 1) + dt.timedelta(days=rng.randrange(0, 1400))).isoformat()


def gen_grounded(t: Teacher, rng: random.Random) -> list[dict]:
    rows = []
    topic = rng.choice(TOPICS)
    d = t.json(f"Write 3 items about {topic}. Each item: an original factual-sounding passage of 50-90 words (invented but plausible details are fine: names, numbers, rules), "
               "one question that the passage answers, its answer in 1-2 sentences drawn only from the passage, "
               "and one question on the same subject that the passage does NOT answer. "
               'Output JSON: {"items":[{"passage":string,"q_yes":string,"a_yes":string,"q_no":string}]}', max_tokens=900,
               schema=items_schema({"passage": STR, "q_yes": STR, "a_yes": STR, "q_no": STR}))
    if not d:
        return rows
    frames = ["Using only the passage below, answer: {q}\n\nPassage: {p}",
              "{q}\n\nAnswer from this text only:\n{p}",
              "Here is a passage:\n{p}\n\nQuestion: {q}"]
    no_answers = ["The passage doesn't say.", "That isn't in the passage.", "The text doesn't cover that.",
                  "Nothing in the passage answers that.", "The passage gives no information on that."]
    for it in d.get("items", []):
        if not isinstance(it, dict):
            continue
        p, qy, ay, qn = (str(it.get(k, "")).strip() for k in ("passage", "q_yes", "a_yes", "q_no"))
        if not (p and qy and ay and qn) or len(p) > 900:
            continue
        rows.append({"kind": "grounded", "messages": [
            {"role": "system", "content": system_prompt(rand_date(rng))},
            {"role": "user", "content": rng.choice(frames).format(q=qy, p=p)},
            {"role": "assistant", "content": ay}]})
        tail = rng.choice([" It covers " + p.split(".")[0].strip().lower()[:80] + ", not that.", "", "", " If you have another source, paste it in."])
        rows.append({"kind": "grounded", "messages": [
            {"role": "system", "content": system_prompt(rand_date(rng))},
            {"role": "user", "content": rng.choice(frames).format(q=qn, p=p)},
            {"role": "assistant", "content": rng.choice(no_answers) + tail}]})
    return rows


def gen_abstain_confident(t: Teacher, rng: random.Random) -> list[dict]:
    rows = []
    topic = rng.choice(TOPICS)
    d = t.json(f"Create 4 questions about INVENTED things related to {topic} that sound real but do not exist (a made-up prize, commission, book and author, theorem, law, company, treaty or person), "
               "and for each a refusal reply of 1-2 sentences that says the assistant has no record of it and will not invent details, in DIFFERENT wording each time (no two replies may start the same way), optionally inviting the user to paste a source. "
               'Output JSON: {"items":[{"question":string,"refusal":string}]}', max_tokens=700,
               schema=items_schema({"question": STR, "refusal": STR}))
    for it in (d or {}).get("items", []):
        if not isinstance(it, dict):
            continue
        q, a = str(it.get("question", "")).strip(), str(it.get("refusal", "")).strip()
        if q and a and len(a) < 400:
            rows.append({"kind": "abstain", "messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]})
    d = t.json(f"Write 4 ordinary general-knowledge questions about {topic} that a well-read person can answer without looking anything up, "
               "each with a plain, correct answer of 2-4 sentences that takes a clear position and avoids hedging. Prefer well-established qualitative facts; do NOT rely on precise figures, dates or statistics unless they are universally known. "
               'Output JSON: {"items":[{"question":string,"answer":string}]}', max_tokens=800, temperature=0.7,
               schema=items_schema({"question": STR, "answer": STR}))
    for it in (d or {}).get("items", []):
        if not isinstance(it, dict):
            continue
        q, a = str(it.get("question", "")).strip(), str(it.get("answer", "")).strip()
        if q and a and len(a) < 700 and len(re.findall(r"\d+(?:[.,]\d+)?", a)) < 2 and t.verify(q, a):
            rows.append({"kind": "confident", "messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]})
    return rows


def gen_synthesis(t: Teacher, rng: random.Random) -> list[dict]:
    rows = []
    topic = rng.choice(TOPICS)
    d = t.json(f"Write 4 comparison questions of the form 'Is X more like Y or more like Z?' or 'Was X closer to Y or Z?' about {topic} or history/economics/politics, "
               "where X, Y and Z are real, well-known things, and answer each in 2-4 sentences that COMMIT to a position and give the deciding reason. 'Neither, and here is why' is allowed as a position; hedging is not. "
               'Output JSON: {"items":[{"question":string,"answer":string}]}', max_tokens=900, temperature=0.8,
               schema=items_schema({"question": STR, "answer": STR}))
    for it in (d or {}).get("items", []):
        if not isinstance(it, dict):
            continue
        q, a = str(it.get("question", "")).strip(), str(it.get("answer", "")).strip()
        if q and a and len(a) < 700 and t.verify(q, a):
            rows.append({"kind": "synthesis", "messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]})
    return rows


def gen_multi_turn(t: Teacher, rng: random.Random) -> list[dict]:
    rows = []
    topic = rng.choice(TOPICS)
    props = {"u1": STR, "a1": STR, "u2": STR, "a2": STR, "u3": STR, "a3": STR}
    d = t.json(f"Write 2 short dialogues about {topic} between a user and a small offline assistant named Pagouro. Each dialogue has three user turns u1, u2, u3 and the assistant's replies a1, a2, a3; "
               "u2 and u3 must depend on the previous reply (a pronoun, 'that', 'the second one', 'give me an example'). "
               "Assistant replies are 1-3 sentences, plain; if the user asks about something that cannot be known offline (today's news, a live price) the assistant says it cannot know that here. "
               'Output JSON: {"dialogues":[{"u1":string,"a1":string,"u2":string,"a2":string,"u3":string,"a3":string}]}', max_tokens=900,
               schema=items_schema(props, key="dialogues"))
    for dl in (d or {}).get("dialogues", []):
        if not isinstance(dl, dict):
            continue
        msgs = [{"role": "system", "content": system_prompt(rand_date(rng))}]
        ok = True
        for i in (1, 2, 3):
            u, a = str(dl.get(f"u{i}", "")).strip(), str(dl.get(f"a{i}", "")).strip()
            if not u or not a or len(a) > 600:
                ok = False
                break
            msgs += [{"role": "user", "content": u}, {"role": "assistant", "content": a}]
        if ok:
            rows.append({"kind": "multi_turn", "messages": msgs})
    return rows


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=400, help="target rows per class")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--model", default=TEACHER)
    ap.add_argument("--hours", type=float, default=0, help="stop after this many hours (0 = when targets are met)")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    rng = random.Random()
    evals = load_eval_prompts()
    seen = existing_user_messages()
    counts: dict[str, int] = {}
    if os.path.exists(OUT):
        for line in io.open(OUT, encoding="utf-8"):
            try:
                counts[json.loads(line)["kind"]] = counts.get(json.loads(line)["kind"], 0) + 1
            except Exception:
                pass
    log(f"start: existing {counts}, {len(seen)} known user messages, {len(evals)} eval prompts")

    packs = Packs(os.path.join(ROOT, "packs"))
    t = Teacher(a.model, a.threads)
    log(f"teacher up on port {t.port} ({a.threads} threads)")
    t0 = time.time()
    kinds = ["router", "tool_answer", "grounded", "abstain", "confident", "synthesis", "multi_turn"]
    kept_total = dropped = 0
    empty_streak: dict[str, int] = {}
    try:
        while True:
            if a.hours and (time.time() - t0) / 3600 > a.hours:
                log("time budget reached")
                break
            need = [k for k in kinds if counts.get(k, 0) < a.per_class and empty_streak.get(k, 0) < 6]
            if not need:
                log("targets met")
                break
            batch: list[dict] = []
            if "router" in need or "tool_answer" in need:
                r = gen_router(t, rng, packs)
                if "router" in need:
                    batch += r
                if "tool_answer" in need:
                    batch += gen_tool_answers(t, rng, packs, r)
            if "grounded" in need:
                batch += gen_grounded(t, rng)
            if "abstain" in need or "confident" in need:
                batch += [x for x in gen_abstain_confident(t, rng) if x["kind"] in need]
            if "synthesis" in need:
                batch += gen_synthesis(t, rng)
            if "multi_turn" in need:
                batch += gen_multi_turn(t, rng)
            kept = 0
            with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
                for row in batch:
                    users = [m["content"] for m in row["messages"] if m["role"] == "user"]
                    key = " ".join(users[0].lower().split())[:200] if users else ""
                    if not key or key in seen or any(overlaps_eval(u, evals) for u in users):
                        dropped += 1
                        continue
                    if sum(len(m["content"]) for m in row["messages"]) > 2200:
                        dropped += 1
                        continue
                    seen.add(key)
                    out = {"kind": row["kind"], "source": SOURCE, "messages": row["messages"]}
                    f.write(json.dumps(out, ensure_ascii=False) + "\n")
                    counts[row["kind"]] = counts.get(row["kind"], 0) + 1
                    kept += 1
            kept_total += kept
            for k in need:
                empty_streak[k] = 0 if any(r["kind"] == k for r in batch) else empty_streak.get(k, 0) + 1
            el = (time.time() - t0) / 3600
            log(f"+{kept} kept ({dropped} dropped total) -> {counts} | {t.tokens_out} teacher tokens, {t.tokens_out / max(1, time.time() - t0):.1f} tok/s, {el:.2f} h")
    finally:
        t.stop()
    log(f"done: {kept_total} rows this run, totals {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
