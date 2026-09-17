"""Pagouro Teaches -- a self-contained "teach me and test me" tutor.

Model-agnostic: works against any GGUF via llama.cpp, so it is testable today
against a baseline model, before Pagouro itself is trained. See docs/TUTOR.md.

THE RULE THAT DEFINES THIS TOOL: the model explains and paces; it never
authors facts. Every question and reference answer comes from a fixed,
reviewed item bank (tutor/items/*.jsonl), each item traceable to a source in
corpus.json. The model's only job is to (a) grade a free-text answer against
the reference, in the learner's own words, and (b) restate the explanation
conversationally if asked. It is NEVER asked to generate a new question or
invent a fact. A tutor that bluffs at a learner would contradict the entire
project's central claim.

Spaced repetition: a simple SM-2-family scheduler. Deliberately boring --
well-understood, works fully offline, needs no training.

Progress: local file only, honoring Pagouro's SAND/STONE default (D-19).
Nothing is written unless the learner explicitly enables STONE mode.

Usage:
    python tutor/tutor.py --model path/to/model.gguf
    python tutor/tutor.py --model path/to/model.gguf --stone   # save progress
    python tutor/tutor.py --model path/to/model.gguf --topic money-and-economics
"""

from __future__ import annotations

import argparse
import datetime
import glob
import io
import sys

# Windows consoles default to cp1252, which cannot display many characters a
# model can legitimately emit (curly quotes, em dashes, non-Latin scripts).
# Reconfigure stdout to UTF-8 with a safe fallback so a display limitation
# never crashes a live tutoring session.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS_DIR = os.path.join(ROOT, "tutor", "items")
PROGRESS_FILE = os.path.join(ROOT, "tutor", "progress.json")   # only written in --stone mode
LLAMA_CHAT = os.path.join(ROOT, "tools", "llamacpp", "llama-cli.exe")
ANSI = re.compile("\x1b\\[[0-9;]*m")

# --------------------------------------------------------------------------
# Item bank loading
# --------------------------------------------------------------------------

def load_items(topic: str | None = None) -> list[dict]:
    items = []
    for fp in sorted(glob.glob(os.path.join(ITEMS_DIR, "*.jsonl"))):
        with io.open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if topic and item.get("topic") != topic:
                    continue
                items.append(item)
    return items


# --------------------------------------------------------------------------
# Spaced repetition -- a minimal SM-2-family scheduler. `progress[item_id]`
# holds {ease, interval_days, due, reps}. New items are due immediately.
# --------------------------------------------------------------------------

DEFAULT_EASE = 2.5

def new_progress_entry() -> dict:
    return {"ease": DEFAULT_EASE, "interval_days": 0, "reps": 0,
            "due": datetime.date.today().isoformat()}


def schedule_next(entry: dict, quality: int) -> dict:
    """quality: 0 (wrong) to 5 (perfect). Standard SM-2 update."""
    entry = dict(entry)
    if quality < 3:
        entry["reps"] = 0
        entry["interval_days"] = 1
    else:
        entry["reps"] += 1
        if entry["reps"] == 1:
            entry["interval_days"] = 1
        elif entry["reps"] == 2:
            entry["interval_days"] = 6
        else:
            entry["interval_days"] = round(entry["interval_days"] * entry["ease"])
        entry["ease"] = max(1.3, entry["ease"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    due = datetime.date.today() + datetime.timedelta(days=entry["interval_days"])
    entry["due"] = due.isoformat()
    return entry


def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        with io.open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress: dict) -> None:
    with io.open(PROGRESS_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(progress, f, indent=2)
        f.write("\n")


# --------------------------------------------------------------------------
# The model's ONE job: grade a free-text answer against the reference.
# It never sees a raw item.question with an open invitation to answer it
# itself -- the prompt below only ever asks it to COMPARE two texts.
# --------------------------------------------------------------------------

GRADE_PROMPT = """You are grading a student's answer against a reference answer.
Do not add outside facts. Judge only whether the student's answer captures the
same key idea as the reference, even if worded differently.

Reference answer: {reference}

Student's answer: {student}

Reply with exactly one line: CORRECT, PARTIAL, or WRONG, followed by a dash and
one short sentence of feedback. Example: "PARTIAL - you have the mechanism right but missed the direction of the effect." """


def grade_with_model(model: str, reference: str, student: str, timeout: int = 60) -> tuple[str, str]:
    if not student.strip():
        return "WRONG", "no answer given"
    prompt = GRADE_PROMPT.format(reference=reference, student=student)
    cmd = [LLAMA_CHAT, "-m", model, "-p", prompt, "-st", "-n", "80",
          "--temp", "0", "--top-k", "1", "--seed", "1", "--no-warmup", "-ngl", "0"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "PARTIAL", "grading timed out; counted as partial credit"
    txt = ANSI.sub("", res.stdout or "")
    txt_norm = txt.replace("\r\n", "\n").replace("\r", "\n")
    # THE REAL BUG, found by diffing byte-for-byte against a raw capture: llama-cli's
    # interactive console TRUNCATES its own echo of a long prompt and appends the
    # literal text "(truncated)" -- it does NOT truncate what is actually sent to the
    # model (the response that follows is coherent and on-topic). Our first fix
    # (normalizing CRLF/LF) was correct but insufficient, because prompt.rfind() can
    # never match a prompt that was cut off mid-sentence on the console's side.
    # run_eval.py's short, single-line eval prompts never hit this; this multi-line
    # ~500-char grading prompt does. When present, "(truncated)" is a reliable anchor:
    # the model's actual generated text starts immediately after it.
    if "(truncated)" in txt_norm:
        i = txt_norm.rfind("(truncated)")
        cont = txt_norm[i + len("(truncated)"):].strip()
    else:
        prompt_norm = prompt.replace("\r\n", "\n").replace("\r", "\n")
        i = txt_norm.rfind(prompt_norm)
        cont = (txt_norm[i + len(prompt_norm):] if i >= 0 else txt_norm).strip()
    cont = re.split(r"\n\s*\[end of text\]|\nllama_perf|\nExiting", cont)[0].strip()

    m = re.match(r"^(CORRECT|PARTIAL|WRONG)\b\s*-?\s*(.*)", cont, re.I)
    if m:
        return m.group(1).upper(), m.group(2).strip() or "(no feedback given)"
    return "PARTIAL", f"(model reply did not follow the expected format: {cont[:120]!r})"


QUALITY_MAP = {"CORRECT": 5, "PARTIAL": 3, "WRONG": 0}


# --------------------------------------------------------------------------
# CLI loop
# --------------------------------------------------------------------------

def session(model: str, topic: str | None, stone: bool, max_items: int, non_interactive_answers=None):
    items = load_items(topic)
    if not items:
        print(f"no items found" + (f" for topic '{topic}'" if topic else ""))
        return

    progress = load_progress() if stone else {}
    today = datetime.date.today().isoformat()

    # Due items first (by due date, earliest first), then never-seen items.
    def sort_key(it):
        p = progress.get(it["id"])
        if p is None:
            return (0, it["id"])            # never seen -> highest priority
        return (1 if p["due"] <= today else 2, p["due"])

    items.sort(key=sort_key)
    items = items[:max_items]

    print(f"Pagouro Teaches -- {len(items)} item(s) this session"
         + (f", topic={topic}" if topic else "")
         + (", STONE mode (progress saved)" if stone else ", SAND mode (nothing saved)"))
    print("Type your answer, or 'source' to see the citation, or 'skip' to move on.\n")

    results = []
    for idx, item in enumerate(items):
        print(f"[{idx+1}/{len(items)}] ({item['topic']}, difficulty {item['difficulty']})")
        print(f"  Q: {item['question']}")

        if non_interactive_answers is not None:
            answer = non_interactive_answers[idx] if idx < len(non_interactive_answers) else ""
            print(f"  A: {answer}")
        else:
            answer = input("  > ").strip()

        if answer.lower() == "source":
            print(f"  Source: {item['source']}" +
                 (f" ({item['source_locator']})" if item.get("source_locator") else ""))
            if non_interactive_answers is None:
                answer = input("  > ").strip()

        if answer.lower() == "skip":
            print("  (skipped)\n")
            continue

        verdict, feedback = grade_with_model(model, item["reference_answer"], answer)
        print(f"  Verdict: {verdict} -- {feedback}")
        print(f"  Reference: {item['reference_answer']}")
        print(f"  Why: {item['explanation']}")
        print(f"  Source: {item['source']}" +
             (f" ({item['source_locator']})" if item.get("source_locator") else ""))
        print()

        results.append({"id": item["id"], "verdict": verdict})
        if stone:
            entry = progress.get(item["id"], new_progress_entry())
            progress[item["id"]] = schedule_next(entry, QUALITY_MAP.get(verdict, 3))

    if stone:
        save_progress(progress)
        print(f"progress saved to {os.path.relpath(PROGRESS_FILE, ROOT)}")
    else:
        print("SAND mode: nothing was saved. Nothing about this session persists.")

    n = len(results)
    if n:
        correct = sum(1 for r in results if r["verdict"] == "CORRECT")
        print(f"\n{correct}/{n} correct this session.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="path to a .gguf model, any model")
    ap.add_argument("--topic", default=None)
    ap.add_argument("--stone", action="store_true", help="save progress to disk (default: SAND, nothing saved)")
    ap.add_argument("--max-items", type=int, default=10)
    a = ap.parse_args()

    if not os.path.exists(a.model):
        raise SystemExit(f"missing model: {a.model}")
    if not os.path.exists(LLAMA_CHAT):
        raise SystemExit(f"missing llama-cli: {LLAMA_CHAT}")

    session(a.model, a.topic, a.stone, a.max_items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
