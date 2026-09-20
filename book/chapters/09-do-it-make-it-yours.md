# Chapter 9 — Do it: make it yours

*Licence: CC BY-SA 4.0 (instruction strand, D-64).*

*DO-IT chapter, draft 1 (2026-09-20). The ladder is `docs/MAKE_IT_YOURS.md`, which rides on the
stick; this chapter is the ladder with the reasons attached and one rung worked end to end, with
the numbers it produced on the day. Footnotes name the file each number comes from.*

---

Pagouro ships finished. There is no update server, no telemetry, no "new version available".
That is a feature — it is the whole privacy claim — and it has a cost: the only way the thing on
your stick gets better is if *you* change it. So this chapter is literally what you do, from a
one-minute tweak to a full rebuild, cheapest first. Every rung below was climbed at least once
by the build itself. Where a number appears, it was measured.

| Rung | What changes | Needs | Time |
|---|---|---|---|
| 1 | What it can look up | a text file | 1 minute |
| 2 | Which model runs | a `.gguf` file | 1 minute |
| 3 | Web search, threads, context | a JSON file / one flag | 5 minutes |
| 4 | What it can *do* — a skill | a folder with a Python file | half an hour |
| 5 | Its habits (fine-tune) | Python, the repo, a CPU | an afternoon |
| 6 | What it was trained on | the repo, patience or a rented GPU | days |
| 7 | A bigger model | a rented GPU and money | Chapter 11 |

The first three rungs need nothing but the stick. The rest need the repository, which is the
same code that built the stick.

## Rung 1 — Give it things to look up

The model does not *know* facts; it looks them up. The `pack_search` tool searches every
`.txt` in `packs/`, paragraph by paragraph, by keyword ranking, in about twenty milliseconds.
Drop a plain-text file into `packs/` and it is searchable on the next launch. A 1.5-megabyte
manual indexes in a third of a second.[^packs]

That division of labour is deliberate and it is the most important thing in this chapter.
Retrieval is where verbatim text belongs; training is for concepts and voice. A model this size
cannot memorise a canning table and should not try — it would get the altitude thresholds wrong
and say them confidently. It *can* find the table and read the number out. So if you want
Pagouro to answer questions about your field, your town or your family recipes, the first move
is never training. It is a text file.

Two rules ride along. Keep blank lines between paragraphs (that is what the chunker splits on).
And if you intend to pass the stick to anyone else, write one line in `packs/README.md` saying
what the file is and why you may redistribute it. Pagouro's whole claim is that every byte has
a nameable licence. Keep that true for anything you ship; break it freely for your own notes.

## Rung 2 — Swap the model

The app loads whatever `.gguf` it finds in `model/`. Put a different one there — a bigger
Pagouro, or a model that is not Pagouro at all — and it runs, because the harness is plain
llama.cpp underneath. Two cautions. The prompts and the router grammar are what *this* model was
trained on; another model will work through them, but the honesty numbers on the box belong to
the model they were measured on, so measure the new one (Chapter 6) before claiming anything.
And a bigger model is a slower one: the seven-billion-parameter teacher used during the build
managed about twelve tokens a second on the build machine's CPU, against near-instant answers
from the stick model.[^teacher]

## Rung 3 — Switches

`/online` allows one tool, web search, through a provider you name in `workspace/online.json`;
nothing else leaves the machine, and the conversation never does. Threads and context size are
flags on the launcher. None of these need a rebuild, and all of them are printed in the status
line so you can see what is on.

## Rung 4 — A skill, worked end to end

This is the rung the rest of the chapter is about, because it is the one where a stranger can
add a *capability* in half an hour and prove it works, and because the day it was built it
produced a number that changed the design.

A skill is a folder. That is the whole container:

```
skills/unit_convert/
  SKILL.md          name, description, licence, author, source (and prose for people)
  tools/convert.py  one function: run(argument, app) -> str
  packs/units.txt   reference text, indexed like any other pack
  examples.jsonl    ten examples of a user saying it and the tool call that should follow
  eval.jsonl        ten test prompts with the expected tool, argument and answer
  MANIFEST          a hash of every file above
```

The Python file is short by construction — one function, one table, no reasoning:

```python
DESCRIPTION = "convert a quantity between units, e.g. '12 km to miles' or '350 F to C'"

def run(argument, app=None):
    ...parse "<number> <unit> to <unit>", look both units up in a table, multiply...
    return "12 km = 7.456 mi"
```

Anything it cannot do, it refuses with a line that starts `NO_MATCH`, so the model has nothing
to bluff with. Ask it for parsecs and it says it has no table entry for parsecs.

The test is one command: `python scripts/skill_test.py skills/unit_convert`. It checks the
folder is complete and the licence is named; runs every eval row through the tool and checks
the answer; and, given the model on the stick, asks the model's router to choose the tool for
each prompt. On the day, three first-party skills — unit conversion, date arithmetic, recipe
scaling — scored like this on the 126-million-parameter Flash model:[^skills]

| skill | tool alone | model's router alone | harness |
|---|---|---|---|
| unit_convert | 10/10 | **0/10** | 10/10 |
| date_math | 10/10 | **0/10** | 10/10 |
| recipe_scale | 10/10 | **0/10** | 10/10 |

The middle column is the number that mattered. Told in its prompt that a tool called `convert`
existed, the model never once chose it. It sent every conversion to the calculator, with a
conversion factor it made up: `26.2*35000` for miles to kilometres.[^bluff] That is the bluff in
tool form — a confident wrong number with an arithmetic tool's authority behind it — and it is
exactly the failure the project exists to remove. A model this size does not learn a new name
from a sentence in its prompt. It learns names from training.

So the harness got two things, and the table got its third column. First, a skill's tool may
declare a `TRIGGER`, a plain regular expression; when the user's message matches, the harness
routes to the tool before the model is asked. The triggers were checked against the frozen
tool-use test — forty prompts that belong to other tools — and adjusted until none of them
fired there: an ISO date inside a file path no longer looks like a date question, and time units
were left to the calculator.[^triggers] Second, every skill's `examples.jsonl` is now part of
the fine-tuning set, so the next model learns the names properly and the middle column should
rise. Until it does, the catalogue prints both numbers, side by side, always.

One more honesty note, because it is the kind that gets skipped. The loader *screens* a tool's
source — a file that mentions the shell, the network, `eval` or `exec` is refused with the reason
printed — and it hash-lists every file against the manifest. It does not *sandbox* anything;
Python cannot sandbox Python from inside. The protection is the screen, the hashes, and the fact
that a tool is one short function you can read. Say that plainly wherever you describe skills.
"Sandboxed" is a word that gets people hurt.

### The port

The half-hour, for a skill written for a larger model:

1. Read it once. Separate what it *does* — a conversion, a lookup, a template — from what it
   *says*. The first becomes `tools/`; reference material becomes `packs/`; the prose reasoning is
   dropped, with one honest line in `SKILL.md` about what was lost.
2. Write ten examples and ten test prompts. Keep them apart from each other and from Pagouro's
   frozen tests; the test script checks.
3. Run the test. Paste its output into the pull request. A PR without the number is not a PR.
4. Fill in the licence — the original's, and it must be nameable, the same rule as the corpus —
   the author, and yourself as porter. Both names go in the catalogue and in the app's `/skills`
   listing.

## Rung 5 — Habits

Fine-tuning on the CPU is an afternoon and it changes *habits*, not knowledge: how the model
routes, whether it says "I have no record of that", the spelling register it answers in. The
recipe is in Chapter 6's terms — build the examples, run `train_sft.py`, re-run the frozen
suite, and keep the model only if the numbers moved the way you meant. For the Flash model the
fine-tune ran on a rented card in six minutes, and the whole frozen suite — six test sets — runs
on the build machine's CPU in a little over a minute.[^sft]

## Rung 6 and 7 — The corpus and the size

Changing what the model was trained on means changing the ledger first and the data second;
Chapter 4 is that discipline. Changing the size means renting a machine; Chapter 11 is how to do
that without getting hurt. Neither is a weekend.

## What you are agreeing to when you change it

The code is Apache 2.0; the weights and the packs are CC BY-SA 4.0; the corpus rows each carry
their own licence. You may do anything with them that those licences allow, including selling a
stick. What you may not do is *claim the numbers*. The numbers on the box were measured on one
model, one corpus and one harness; the moment you change any of the three, re-measure or say
nothing. That is not a licence term. It is the only thing that makes a box worth reading.

---

[^packs]: `docs/MAKE_IT_YOURS.md`, rung 1; timing measured on the build machine at launch.
[^teacher]: `BUILD_LOG.md` Day 3, the DeepSeek 7B teacher on the build CPU.
[^skills]: `skills/CATALOGUE.md`, generated by `scripts/skill_test.py --all --model data/gguf_flash/pagouro-flash-sft2-q8_0.gguf` on 2026-09-20; per-item log in `skills/last_test.json` (not committed).
[^bluff]: `scripts/skill_test.py` routing log for `uc-01`, "How many kilometres is 26.2 miles?": routed to `calc` with argument `26.2*35000`. The rest of the column is the same shape.
[^triggers]: `evals/tooluse.json` (40 items, frozen); the two false positives found and removed were an ISO date inside a path (`/home/eric/journal/2026-09-18.md`) and "How many seconds are in 3 and a half hours?", which belongs to `calc`.
[^sft]: `docs/DECISIONS.md` D-61 (SFT on the A40, 6 min); `evals/results/pagouro-flash2__*.json` `elapsed_s` sum to 72.8 s on 2026-09-20 (bluff 22.9, calibration 22.6, deflection 20.7, tool-use 3.0, memory 2.0, spelling 1.6).
