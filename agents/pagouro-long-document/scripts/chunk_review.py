"""Run a long document through Pagouro in pieces a 1B can hold, against a fixed outline of questions,
until every piece x question is done. Resumable. Standard library only. (O-48; the skill in ../SKILL.md)

How a piece reaches the model: as a pack_search hit, the exact shape it was fine-tuned on (question ->
tool result -> answer from it; tool-result fidelity measured 10/10). The first attempt pasted 900-word
chunks into the question and asked for verbatim copies; that is off the model's training and it
confabulated (2026-09-25, 0 of 10 usable). Pieces are ~600 characters, the size the D-93 payload
measurements showed it can read without losing the question.

How an answer is checked: GROUNDING -- the share of the answer's content words that occur in the piece.
An answer below the floor (default 0.6) is marked UNGROUNDED and kept out of the report but counted, so
the run's own bluff rate is visible. "No match" phrasings count as no match, not as invention.

    python chunk_review.py --doc BOOK.md --outline outline.json --out review.md
        [--wave idea|outline|bulk] [--segment-words 5000] [--overlap 0.5]
        [--endpoint http://127.0.0.1:8484/v1] [--chunk-chars 600] [--ground 0.6] [--state review.state.json] [--limit N]

Waves and scales (Eric, 2026-09-26): the document is read in WAVES -- `idea` (one piece per segment, one
question: what is this about), `outline` (three pieces per segment against the outline), `bulk` (every piece).
Segments are sliding windows that OVERLAP LIKE FISH SCALES: --segment-words 5000 --overlap 0.34 turns a
100,000-word manuscript into 30 segments of 5,000 words (not 20), each sharing a third of its text with the next, so a
fact that sits on a boundary is read in the context of both neighbours. Pieces (~600 chars, what the 1B
holds) are cut inside each segment; a piece in an overlap zone is asked once per segment it belongs to.

outline.json: [{"id": "q1", "question": "What does the author say the model must never claim?"}, ...]
state file: every (piece, question) result, written after each call, so a stopped run continues where it was.
review.md: per question, the grounded findings with piece references; then a coverage table.
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

STOP = {"the", "a", "an", "of", "in", "on", "at", "to", "is", "was", "are", "were", "and", "or", "it", "its", "this",
        "that", "by", "for", "with", "as", "be", "which", "from", "i", "you", "not", "no", "he", "she", "they", "we",
        "his", "her", "their", "our", "has", "have", "had", "but", "if", "so", "than", "then", "there", "here", "what",
        "who", "when", "where", "how", "does", "do", "did", "says", "say", "said", "passage", "author", "text", "about"}
NO_MATCH = re.compile(r"no[_ ]match|no information|does not (cover|address|mention|say|give|state)|doesn't (cover|address|mention|say|give|state)|"
                      r"not (in|covered|mentioned|addressed|stated) (in )?(the |this )?(passage|text|search)|isn't in (the |this )?(passage|text)|"
                      r"nothing (in|about)|no record|isn't about|is not about|can't find|cannot find|gives no |give no |"
                      r"passage (gives|says|has|contains|mentions|covers) no", re.I)


def judge(ans: str, piece: str, floor: float) -> tuple[str, float]:
    nomatch = bool(NO_MATCH.search(ans[:200]))
    g = 0.0 if nomatch else grounding(ans, piece)
    return ("NO_MATCH" if nomatch else ("GROUNDED" if g >= floor else "UNGROUNDED")), g


def pieces_of(text: str, max_chars: int) -> list[tuple[str, str]]:
    """Split on headings and blank lines; pack paragraphs (and sentences of long paragraphs) up to max_chars;
    keep the nearest heading as a label."""
    out, buf, size, label = [], [], 0, "start"

    def flush():
        nonlocal buf, size
        if buf:
            out.append((label, " ".join(buf)))
        buf, size = [], 0

    for para in re.split(r"\n\s*\n", text):
        p = re.sub(r"\s+", " ", para).strip()
        if not p:
            continue
        if re.match(r"^#{1,6}\s", p):
            flush(); label = p.lstrip("# ").strip()[:60]; continue
        units = [p] if len(p) <= max_chars else re.split(r"(?<=[.!?])\s+", p)
        for u in units:
            if size + len(u) + 1 > max_chars and buf:
                flush()
            buf.append(u); size += len(u) + 1
    flush()
    return out


def segments_of(text: str, seg_words: int, overlap: float) -> list[tuple[int, str]]:
    """Sliding windows of seg_words words, stepping by seg_words * (1 - overlap): the fish scales."""
    words = text.split()
    if seg_words <= 0 or len(words) <= seg_words:
        return [(0, text)]
    step = max(1, int(seg_words * (1.0 - overlap)))
    out, start = [], 0
    while start < len(words):
        out.append((start, " ".join(words[start:start + seg_words])))
        if start + seg_words >= len(words):
            break
        start += step
    return out


def ask(endpoint: str, question: str, passage: str, max_tokens: int) -> tuple[str, list[str]]:
    body = {"model": "pagouro", "messages": [{"role": "user", "content": question}], "max_tokens": max_tokens,
            "pagouro_passage": passage}
    req = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"].strip(), d.get("pagouro", {}).get("notes", [])


def content_words(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP and len(w) > 2}


def grounding(answer: str, piece: str) -> float:
    aw = content_words(answer)
    if not aw:
        return 0.0
    pw = content_words(piece)
    return len(aw & pw) / len(aw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--outline", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8484/v1")
    ap.add_argument("--chunk-chars", type=int, default=600)
    ap.add_argument("--ground", type=float, default=0.6, help="grounding floor: share of answer content words found in the piece")
    ap.add_argument("--max-tokens", type=int, default=120)
    ap.add_argument("--state", default=None)
    ap.add_argument("--limit", type=int, default=0, help="stop after N calls this run (0 = until done)")
    ap.add_argument("--rejudge", action="store_true", help="recompute every saved verdict from the saved answers (no model calls), then rewrite the report")
    ap.add_argument("--wave", choices=["idea", "outline", "bulk"], default="bulk", help="idea: 1 piece/segment, one question; outline: 3 pieces/segment; bulk: every piece")
    ap.add_argument("--segment-words", type=int, default=0, help="segment length in words; 0 = auto: the document in ~30 windows, clamped to 1,500-8,000 words")
    ap.add_argument("--overlap", type=float, default=0.5, help="share of each segment shared with the next (fish scales)")
    a = ap.parse_args()
    doc = io.open(a.doc, encoding="utf-8", errors="replace").read()
    outline = json.load(io.open(a.outline, encoding="utf-8"))
    state_path = a.state or a.out + ".state.json"
    state = json.load(io.open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {}
    name = os.path.basename(a.doc)
    if a.segment_words <= 0:                     # auto: ~30 windows over the document, whatever its length
        a.segment_words = max(1500, min(8000, len(doc.split()) // 30 * 2))
    segs = segments_of(doc, a.segment_words, a.overlap)
    parts = []                                   # (label, piece) with the label carrying the segment number
    for si, (w0, seg) in enumerate(segs):
        ps = pieces_of(seg, a.chunk_chars)
        if a.wave == "idea":
            ps = ps[:1]
        elif a.wave == "outline" and len(ps) > 3:
            ps = [ps[0], ps[len(ps) // 2], ps[-1]]
        for label, piece in ps:
            parts.append((f"seg {si+1} · {label}", piece))
    if a.wave == "idea":
        outline = [{"id": "idea", "question": "In one or two sentences, what is this passage about, and what does it claim?"}]
    total = len(parts) * len(outline)
    print(f"{name}: {len(segs)} segments of <= {a.segment_words} words (overlap {a.overlap:.0%}), wave '{a.wave}': "
          f"{len(parts)} pieces of <= {a.chunk_chars} chars x {len(outline)} questions = {total} calls; {len(state)} done already", flush=True)
    if a.rejudge:
        for k, v in state.items():
            if not k.startswith(a.wave + ":") or v["piece"] >= len(parts):
                continue
            v["verdict"], g = judge(v["answer"], parts[v["piece"]][1], a.ground); v["grounding"] = round(g, 2)
        io.open(state_path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False, indent=1))
        print(f"rejudged {len(state)} saved answers", flush=True)
    calls, t0, stopped = 0, time.time(), False
    for ci, (label, piece) in enumerate(parts):
        for q in outline:
            key = f"{a.wave}:{ci}:{q['id']}"
            if key in state:
                continue
            if a.limit and calls >= a.limit:
                stopped = True; break
            try:
                ans, notes = ask(a.endpoint, q["question"], f"[{name} part {ci+1} of {len(parts)}] {piece}", a.max_tokens)
            except Exception as e:  # noqa: BLE001
                print(f"  piece {ci+1} {q['id']}: endpoint error {type(e).__name__}: {str(e)[:80]} -- stopping; rerun to resume", flush=True)
                stopped = True; break
            verdict, g = judge(ans, piece, a.ground)
            nomatch = verdict == "NO_MATCH"
            state[key] = {"wave": a.wave, "piece": ci, "label": label, "q": q["id"], "verdict": verdict, "grounding": round(g, 2),
                          "answer": ans[:800], "notes": notes}
            io.open(state_path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False, indent=1))
            calls += 1
            print(f"  [{len(state)}/{total}] piece {ci+1} ({label[:28]}) {q['id']}: {verdict}" + (f" {g:.2f}" if not nomatch else ""), flush=True)
        if stopped:
            break
    # the report, from the state
    state = {k: v for k, v in state.items() if k.startswith(a.wave + ":")}
    lines = [f"# Review of {name} — wave '{a.wave}'", "",
             f"*{len(segs)} segments of <= {a.segment_words} words overlapping {a.overlap:.0%}; {len(parts)} pieces of <= {a.chunk_chars} characters; "
             f"{len(state)} of {total} piece x question calls done. "
             f"Findings are Pagouro 1B's answers from each piece, kept only when at least {int(a.ground*100)} % of their content "
             f"words occur in that piece; a person or a larger model reads them and checks the piece.*", ""]
    for q in outline:
        hits = sorted((v for v in state.values() if v["q"] == q["id"] and v["verdict"] == "GROUNDED"), key=lambda v: v["piece"])
        lines += [f"## {q['id']} -- {q['question']}", ""]
        if not hits:
            lines += ["*No piece answered this yet.*", ""]
        for v in hits:
            lines.append(f"- {v['answer'].strip()}  \n  -- piece {v['piece']+1}, *{v['label']}* (grounding {v['grounding']:.2f})")
        lines.append("")
    lines += ["## Coverage", "", "| question | grounded | no match | ungrounded (dropped) |", "|---|---|---|---|"]
    ung = 0
    for q in outline:
        vs = [v for v in state.values() if v["q"] == q["id"]]
        c = {k: sum(1 for v in vs if v["verdict"] == k) for k in ("GROUNDED", "NO_MATCH", "UNGROUNDED")}
        ung += c["UNGROUNDED"]
        lines.append(f"| {q['id']} | {c['GROUNDED']} | {c['NO_MATCH']} | {c['UNGROUNDED']} |")
    lines += ["", f"*{ung} answer(s) were not grounded in their piece and were dropped -- that is the bluff rate of this run, visible. "
                  f"Pieces with 'no match' for every question were read and did not address the questions.*"]
    io.open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    left = total - len(state)
    print(f"written {a.out} (wave {a.wave}); {len(state)}/{total} done, {left} left; {calls} calls in {time.time()-t0:.0f}s"
          + ("" if not left else " -- run again to continue"), flush=True)
    return 0 if not left else 2


if __name__ == "__main__":
    sys.exit(main())
