---
name: pagouro-long-document
description: Review a long document with Pagouro (offline 1B) in chunks it can hold, against an outline you build by interviewing the user first, and keep working until every chunk has been read for every question. Pagouro finds and quotes; you judge and write up. Worked example — the book Make Your Own AI.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [pagouro, long-document, review, chunking, offline]
    category: research
---

# Long-document review with Pagouro

**When to use:** the user has a long text (a book, a report, a contract, a transcript) and wants it
read against *their* questions, on their own machine, with nothing sent anywhere. Pagouro can hold
about 1,500 words at a time, so the document is read in chunks; you are the one who decides what to
look for and what the findings mean.

**The rule that makes it work:** Pagouro's job is to **find and quote**. For every chunk and every
question it returns the passage's own sentences or `NO_MATCH`; every quote is checked against the
chunk and anything not actually in the passage is dropped and counted. It is never asked to summarise
or judge — that is where a 1B invents. You (the agent) do the interview, the outline, and the write-up.

Requires the `pagouro-connect` skill's endpoint: `pagouro.exe --serve` running at
`http://127.0.0.1:8484/v1`.

## Steps

### 1. Interview the user (5–8 questions, one at a time)
Ask, and write the answers down:
1. What is this document, and why are they reading it now?
2. What decision or piece of writing will the review feed?
3. What do *they* think the three most important things in it are? (Their words become questions.)
4. What would they be embarrassed to have missed?
5. Anything to ignore (front matter, appendices, a chapter they already know)?
6. How do they want the result: quotes with references, a memo, a table, a list of contradictions?
7. How long can it run? (≈ 3–4 s per chunk × question on a laptop CPU: a 60,000-word book with 6
   questions is ~70 chunks × 6 = ~420 calls ≈ 25 minutes.)

### 2. Build the outline — the fixed set of questions every chunk is read against
Turn the answers into 4–8 **findable** questions: things a passage either says or does not. Good:
"What does the author say the model must never claim?" Bad: "Is the argument convincing?" (a
judgement — yours, later). Save as `outline.json`:
```json
[
  {"id": "q1", "question": "What does the author say the model must never claim?"},
  {"id": "q2", "question": "Where does the text give a measured number for the bluff rate?"}
]
```
Show the outline to the user and get a yes before spending their time.

### 3. Run it, and keep running until done
```
python scripts/chunk_review.py --doc THE_DOCUMENT.md --outline outline.json --out review.md
```
- Prints progress per chunk × question; writes `review.md.state.json` after every call.
- If it stops (machine off, endpoint down, `--limit N` reached), **run the same command again**: it
  continues from the state file. Exit code 2 means "not finished yet"; 0 means every chunk × question
  is done. Loop on it until 0.
- `--chunk-words 900` is the default; drop to 600 for dense text, raise to 1,200 for prose.
- Documents in PDF/Word: convert to text first (Pagouro's own `documents.py` extractor, or `pandoc`).

### 4. Read `review.md` and write the deliverable the user asked for
`review.md` has, per question, the verified quotes with chunk numbers and the nearest heading, then a
coverage table and the count of sentences the model offered that were *not* in the passage (its bluff
rate on this run — show the user that number). Now do the part only you can: group, compare, find
the contradictions, write the memo. Cite chunks so the user can check any line against the text.

### 5. Tell the user what was and was not read
Chunks with `NO_MATCH` for every question are listed in the coverage table; if a whole section came
back empty, say so — it either does not address their questions or needs a different question.

## Worked example — the book *Make Your Own AI*

Document: `book/MAKE_YOUR_OWN_AI.md` (ships in the Pagouro repository). A user who is thinking of
building their own model. Interview answers → outline:
```json
[
  {"id": "promises", "question": "What promises does the author say the finished model makes to a stranger?"},
  {"id": "numbers",  "question": "Which measured numbers (cost, tokens, bluff rate, answered-real) does this passage state?"},
  {"id": "mistakes", "question": "What mistake does the author admit to in this passage, and what did it cost?"},
  {"id": "rules",    "question": "What rule or decision does the passage say must never be reversed?"},
  {"id": "howto",    "question": "What concrete step could a reader repeat from this passage (a command, a file, a setting)?"}
]
```
Run: `python scripts/chunk_review.py --doc book/MAKE_YOUR_OWN_AI.md --outline examples/book_outline.json --out book_review.md`
Deliverable: a two-page memo for the user — the four promises in the author's words, the cost table
with chunk references, the five most expensive mistakes, and the list of steps the reader can repeat —
every line traceable to a quote in `book_review.md`.

## Limits, stated
- A 1B on a chunk misses things a large model would catch; coverage is honest, recall is not perfect.
  The state file lets you add a question later and run only the new one.
- It reads chunks independently: a fact split across a chunk boundary can be missed. Overlap is not
  built in; if a question needs continuity, lower `--chunk-words` and ask a narrower question.
- Nothing leaves the machine. If you route the *write-up* through a cloud model, that is your choice
  and the user should be told; the review itself stayed local.
