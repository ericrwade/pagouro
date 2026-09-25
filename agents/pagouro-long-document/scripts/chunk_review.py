"""Run a long document through Pagouro in chunks a 1B can hold, against a fixed outline of questions,
until every chunk x question is done. Resumable. Standard library only. (O-48; the skill in ../SKILL.md)

The division of labour that makes this work: the 1B FINDS AND QUOTES — for each chunk and each outline
question it returns the passage's own sentences, verbatim, or NO_MATCH. It never summarises freely (its
tool-result fidelity measured 10/10; its free generation is where a 1B bluffs). Every quote is checked
against the chunk text; a quote that is not in the passage is marked INVENTED and dropped from the report.
The agent that runs this (Hermes, OpenClaw, a person) does the interviewing, the outline, and the synthesis.

    python chunk_review.py --doc BOOK.md --outline outline.json --out review.md
        [--endpoint http://127.0.0.1:8484/v1] [--chunk-words 900] [--state review.state.json] [--limit N]

outline.json: [{"id": "q1", "question": "What does the author say the model must never claim?"}, ...]
state file: every (chunk, question) result, written after each call, so a stopped run continues where it was.
review.md: per question, the verified quotes with chunk references; then a coverage table.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.request

PROMPT = ("Below is part {i} of {n} of a document called \"{doc}\".\n\n"
          "PASSAGE:\n{chunk}\n\n"
          "QUESTION: {q}\n\n"
          "Copy, word for word, the sentences from the PASSAGE that answer the question. Quote only what is "
          "there; do not add anything. If the passage does not address the question, reply exactly: NO_MATCH")


def chunks_of(text: str, max_words: int) -> list[tuple[str, str]]:
    """Split on headings and blank lines; pack paragraphs up to max_words; keep the nearest heading as a label."""
    out, buf, words, label = [], [], 0, "start"
    for para in re.split(r"\n\s*\n", text):
        p = para.strip()
        if not p:
            continue
        if re.match(r"^#{1,6}\s", p):
            label = p.lstrip("# ").strip()[:60]
        w = len(p.split())
        if w > max_words:                              # one giant paragraph: hard-split by sentences
            sents, cur, cw = re.split(r"(?<=[.!?])\s+", p), [], 0
            for s_ in sents:
                if cw + len(s_.split()) > max_words and cur:
                    out.append((label, " ".join(cur))); cur, cw = [], 0
                cur.append(s_); cw += len(s_.split())
            if cur:
                out.append((label, " ".join(cur)))
            continue
        if words + w > max_words and buf:
            out.append((label, "\n\n".join(buf))); buf, words = [], 0
        buf.append(p); words += w
    if buf:
        out.append((label, "\n\n".join(buf)))
    return out


def ask(endpoint: str, content: str, max_tokens: int) -> str:
    body = {"model": "pagouro", "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens,
            "pagouro_tools": False}          # a passage-review turn: no router, no pack search, just the passage
    req = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"].strip()


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def verify(answer: str, chunk: str) -> tuple[list[str], list[str]]:
    """Split the answer into sentences; keep those found verbatim (normalised) in the chunk."""
    if answer.upper().startswith("NO_MATCH") or "no_match" in answer.lower()[:40]:
        return [], []
    hay = norm(chunk)
    ok, bad = [], []
    for s_ in re.split(r"(?<=[.!?])\s+|\n+", answer):
        s_ = s_.strip().strip('"“”')
        if len(s_.split()) < 4:
            continue
        (ok if norm(s_) in hay else bad).append(s_)
    return ok, bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--outline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8484/v1")
    ap.add_argument("--chunk-words", type=int, default=900)
    ap.add_argument("--max-tokens", type=int, default=220)
    ap.add_argument("--state", default=None)
    ap.add_argument("--limit", type=int, default=0, help="stop after N calls this run (0 = until done)")
    a = ap.parse_args()
    doc = io.open(a.doc, encoding="utf-8", errors="replace").read()
    outline = json.load(io.open(a.outline, encoding="utf-8"))
    state_path = a.state or a.out + ".state.json"
    state = json.load(io.open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {}
    parts = chunks_of(doc, a.chunk_words)
    total = len(parts) * len(outline)
    done_before = len(state)
    print(f"{os.path.basename(a.doc)}: {len(parts)} chunks x {len(outline)} questions = {total} calls; {done_before} done already", flush=True)
    calls, t0 = 0, time.time()
    for ci, (label, chunk) in enumerate(parts):
        for q in outline:
            key = f"{ci}:{q['id']}"
            if key in state:
                continue
            if a.limit and calls >= a.limit:
                break
            content = PROMPT.format(i=ci + 1, n=len(parts), doc=os.path.basename(a.doc), chunk=chunk, q=q["question"])
            try:
                ans = ask(a.endpoint, content, a.max_tokens)
            except Exception as e:  # noqa: BLE001
                print(f"  chunk {ci+1} {q['id']}: endpoint error {type(e).__name__}: {str(e)[:80]} — stopping; rerun to resume", flush=True)
                break
            ok, bad = verify(ans, chunk)
            state[key] = {"chunk": ci, "label": label, "q": q["id"], "quotes": ok, "invented": bad, "raw": ans[:600]}
            io.open(state_path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False, indent=1))
            calls += 1
            print(f"  [{len(state)}/{total}] chunk {ci+1} ({label[:30]}) {q['id']}: {len(ok)} quote(s)"
                  + (f", {len(bad)} not in passage" if bad else "") + ("" if ok or bad else ", no match"), flush=True)
        else:
            continue
        break
    # the report, from the state: every verified quote under its question, with the chunk it came from
    lines = [f"# Review of {os.path.basename(a.doc)}", "",
             f"*{len(parts)} chunks of ≤ {a.chunk_words} words; {len(state)} of {total} chunk×question calls done; "
             f"quotes are verbatim from the text (checked); Pagouro 1B found them, a person or a larger model reads them.*", ""]
    for q in outline:
        hits = [v for k, v in state.items() if v["q"] == q["id"] and v["quotes"]]
        lines += [f"## {q['id']} — {q['question']}", ""]
        if not hits:
            lines += ["*No passage answered this yet.*", ""]
        for v in sorted(hits, key=lambda v: v["chunk"]):
            for s_ in v["quotes"]:
                lines.append(f"- “{s_}” — chunk {v['chunk']+1}, *{v['label']}*")
        lines.append("")
    inv = sum(len(v["invented"]) for v in state.values())
    lines += ["## Coverage", "", "| question | chunks with a quote | chunks with no match | not-in-passage lines dropped |", "|---|---|---|---|"]
    for q in outline:
        vs = [v for v in state.values() if v["q"] == q["id"]]
        lines.append(f"| {q['id']} | {sum(1 for v in vs if v['quotes'])} | {sum(1 for v in vs if not v['quotes'])} | {sum(len(v['invented']) for v in vs)} |")
    lines += ["", f"*{inv} sentence(s) the model offered were not in their passage and were dropped — that is the bluff rate of this run, visible.*"]
    io.open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    left = total - len(state)
    print(f"written {a.out}; {len(state)}/{total} done, {left} left; {calls} calls in {time.time()-t0:.0f}s"
          + ("" if not left else " — run again to continue"), flush=True)
    return 0 if not left else 2


if __name__ == "__main__":
    sys.exit(main())
