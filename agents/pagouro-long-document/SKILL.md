---
name: pagouro-long-document
description: Review a long document with Pagouro (offline 1B) in chunks it can hold, against an outline you build by interviewing the user first, and keep working until every chunk has been read for every question. Pagouro finds and points; you read, judge and write up. Worked example — the book Make Your Own AI.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [pagouro, long-document, review, chunking, offline]
    category: research
---

# Long-document review with Pagouro

**When to use:** the user has a long text (a book, a report, a contract, a transcript) and wants it
read against *their* questions, on their own machine, with nothing sent anywhere. Pagouro reads
about 600 characters at a time, so the document is read in pieces; you are the one who decides what to
look for and what the findings mean.

**The rule that makes it work:** Pagouro's job is to **find and point**. Each piece of the document
(~600 characters — the size this model reads without losing the question) reaches it the way it was
trained to read evidence, as a search hit, with one question. Its answer is kept only if at least 60 %
of its content words occur in that piece (*grounded*); the rest are dropped and counted, so the run's
own bluff rate is printed. It is never asked to summarise the whole or to judge — that is where a 1B
invents. You (the agent) do the interview, the outline, the reading of the pieces it points to, and the
write-up. Measured on chapter 5 of the book (2026-09-25): 105 calls in 212 s; 28 grounded, 65 no
match, 12 ungrounded.

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
7. How long can it run? (≈ 2 s per piece × question on a desktop CPU, more on a laptop: a 35,000-word
   book with 5 questions is ~380 pieces × 5 = ~1,900 calls ≈ 1 hour. It resumes, so it can run in parts.)

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

### 3. Read in waves, over scales
The document is cut into **segments that overlap like fish scales**: by default each segment shares
half its text with the next, so every passage is read inside two segments and nothing that sits on a
boundary is read out of context; the segment length is set from the document (about thirty windows,
1,500–8,000 words). Raise `--overlap` to 0.75 to have every passage read in four segments — the
cost scales with it, and the continuity is the point, so spend it where the text is dense. Inside each segment the model reads ~600-character pieces. Three waves, each
its own run and its own state:
1. `--wave idea` — one piece per segment, one question ("what is this about, what does it claim"): the
   gist of the whole in ~30 calls. Read it; sharpen the outline with the user.
2. `--wave outline` — three pieces per segment (start, middle, end) against the outline: a map of where
   each question is answered, in ~90 × questions calls.
3. `--wave bulk` — every piece against the outline, until done.
Each wave's findings are grouped by segment, so a fact seen in two overlapping segments shows up twice
with two neighbours — that is the continuity, not a duplicate.

### 4. Run it, and keep running until done
```
python scripts/chunk_review.py --doc THE_DOCUMENT.md --outline outline.json --out review.md --wave idea
python scripts/chunk_review.py --doc THE_DOCUMENT.md --outline outline.json --out review.md --wave outline
python scripts/chunk_review.py --doc THE_DOCUMENT.md --outline outline.json --out review.md --wave bulk
```
(`--overlap 0.5` and an automatic segment length are the defaults; one state file holds all three waves.)
- Prints progress per piece × question; writes `review.md.state.json` after every call.
- If it stops (machine off, endpoint down, `--limit N` reached), **run the same command again**: it
  continues from the state file. Exit code 2 means "not finished yet"; 0 means every piece × question
  is done. Loop on it until 0.
- `--chunk-chars 600` is the default. Do not raise it much: at ~1,200 characters this model starts
  continuing the passage instead of answering (measured, D-93). `--ground 0.6` is the grounding floor.
- Documents in PDF/Word: convert to text first (Pagouro's own `documents.py` extractor, or `pandoc`).

### 5. Read `review.md` and write the deliverable the user asked for
`review.md` has, per question, the grounded findings with piece numbers and the nearest heading, then a
coverage table and the count of answers that were *not* grounded in their piece (its bluff rate on this
run — show the user that number). A finding is a pointer in the model's words, not a quotation: open
the piece it names and read the text before you use it. Now do the part only you can: group, compare,
find the contradictions, write the memo. Cite pieces so the user can check any line against the text.

### 6. Tell the user what was and was not read
Pieces with "no match" for every question are counted in the coverage table; if a whole section came
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
(the result of that exact run is in `examples/book_review.md`, produced by Pagouro 1B on 2026-09-25)
Deliverable: a two-page memo for the user — the four promises in the author's words, the cost table
with chunk references, the five most expensive mistakes, and the list of steps the reader can repeat —
every line traceable to a piece named in `book_review.md`.

## Limits, stated
- A 1B on a chunk misses things a large model would catch; coverage is honest, recall is not perfect.
  The state file lets you add a question later and run only the new one.
- It reads pieces independently: a fact split across a boundary can be missed. Overlap is not built
  in; if a question needs continuity, ask a narrower question.
- Nothing leaves the machine. If you route the *write-up* through a cloud model, that is your choice
  and the user should be told; the review itself stayed local.
