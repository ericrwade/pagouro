# Skills for a one-billion-parameter model — the container, the port, the catalogue (O-30)

*Spec 2026-09-19; built 2026-09-20.* What exists: `app/skills.py` (the loader), `skills/` with three
first-party skills (`unit_convert`, `date_math`, `recipe_scale`), `scripts/skill_test.py` (the
offline test; writes `skills/CATALOGUE.md`), `/skills` in the app, and `skills/` on the stick.

**Measured on the Flash stick model (126M, 2026-09-20), ten eval prompts per skill:** tool eval
10/10 for all three; end-to-end through the harness 10/10 for all three; **the model's router
alone 0/10 for all three.** The router has never seen the tool names, and a clause in the prompt
does not teach a 126M model a new name — it routed every conversion to `calc` with an *invented
factor* ("26.2*35000" for miles to kilometres): the bluff in tool form. Two consequences, both
built: (1) a skill's tool may carry a `TRIGGER` regex, and the harness routes on it before asking
the model (the same philosophy as `refine_args`: the harness compensates for the model, visibly);
(2) every skill's `examples.jsonl` is loaded by `train_sft.py`, so the next router fine-tune learns
the names, and the catalogue reports both numbers so the difference stays visible.

**Screened, not sandboxed.** Python cannot sandbox Python. The loader refuses a tool whose source
mentions `subprocess`, `socket`, `urllib`, `http.`, `requests`, `ctypes`, `os.system`, `os.popen`,
`shutil.rmtree`, `eval(`, `exec(`, `__import__` or `importlib`, prints why, and hash-lists every
file against the skill's `MANIFEST` (mismatch = loads, marked MODIFIED). The rest is reading the
code, which is short by construction. Say that plainly wherever skills are described.

## What a skill is here

A big model follows a page of prose. A 1B model follows a router grammar and a two-line
prompt; everything reliable is the harness. So a Pagouro skill is the *decomposed* form:

| part | what it is | who uses it |
|---|---|---|
| `tools/*.py` | one Python function per tool, `def run(argument: str, app) -> str`, with a one-line `DESCRIPTION` | the harness runs it in the sandbox: no shell, no network unless ONLINE, writes only inside `workspace/` |
| `packs/*.txt` | reference text | `pack_search`, indexed at launch |
| `examples.jsonl` | ~10 router examples (`user` → `{"tool": …, "arguments": …}`) and 2–3 answer examples | the router's fine-tune, and the skill's own eval |
| `SKILL.md` | the standard frontmatter (`name`, `description` — short — `license`, `author`, `ported_by`, `source`) and optional prose | the app reads the frontmatter; the prose is for people |
| `eval.jsonl` | ten prompts with the expected tool/argument or answer key | `pagouro skill test` |
| `MANIFEST` | hashes of every file in the folder | listed with the skill at launch |

**Compatibility with the standard SKILL.md folder** (as Claude and others read it): the app
accepts a plain SKILL.md folder as it exists in the wild — `scripts/` become tools if they
expose `run()`, `resources/*.txt` become packs, the description feeds the router — and prints,
for each such skill, which parts it could use and which it ignored. Honest, and often enough.

## The port (the contributor's half-hour)

1. Take a skill written for a larger model. Read it once.
2. Separate what it *does* (deterministic: a conversion, a lookup, a template) from what it
   *says* (prose reasoning). The first becomes `tools/`; reference material becomes `packs/`;
   the second is dropped — write one honest line in SKILL.md about what was lost.
3. Write ten router examples and ten eval prompts. Keep them disjoint from each other and from
   Pagouro's frozen suite (`pagouro skill test` checks).
4. Run `pagouro skill test <folder>` offline: it prints routing accuracy, argument correctness,
   and answer-key hits on the skill's own eval, on the model on the stick.
5. Fill in `license` (the original's; it must be nameable — same rule as the corpus), `author`,
   `ported_by`, `source`. Open the pull request with the test output pasted in. A PR without
   the number is not a PR.

## Credit and the mark

- Every catalogue row names the original author and the porter; `ported_by` is shown in the
  app when skills are listed. A `CONTRIBUTORS.md` in the catalogue accumulates names.
- **"Runs on Pagouro"** — the hermit-crab mark under the O-29 policy — may be used on any skill
  whose eval passes on the current stick model. The compatibility mark is the Solana-style
  signal applied to capabilities.
- Money, if ever: tip-jar-funded micro-bounties on the wanted list. Eric's call, later.

## The catalogue

`skills/` in the repo: one folder per skill, a `CATALOGUE.md` table generated from the
folders (name, what it does, licence, author, porter, eval score, hash). Install = copy a
folder onto the stick; the app lists installed skills with their hashes at launch. No store, no
network, no ratings: a stick that never phones home cannot have a marketplace, and a folder of
audited functions is the honest version of one.

## Wanted (first twenty, ranked by how well they decompose at 1B)

1. Unit conversion (length, mass, volume, temperature, data) — pure table + arithmetic.
2. Date arithmetic (days between, add N days, weekday of a date).
3. Cooking conversions and scaling (cups/grams, halve or double a recipe) — pairs with the recipe pack.
4. Percentages and tips (already partly in `calc`; make it a skill with its own eval).
5. Checklists from a pack (packing list, pre-flight, canning steps) — retrieval + template.
6. Citation formatter (APA/MLA from fields) — template.
7. Word/character/reading-time counter.
8. Regex tester / explain-this-pattern — deterministic.
9. Roman numerals, number words, ordinal dates.
10. Tax/tip/split-the-bill calculator.
11. Timezone conversion (offline table, no DST guessing beyond the table's date).
12. Morse / NATO phonetic / hex-binary conversions.
13. A "define from the packs" skill: dictionary-style answers from a CC0 glossary pack.
14. Fuel economy / trip cost (pairs with the driver-manual thread).
15. Pressure-canning time lookup by altitude (from the USDA pack).
16. Ohm's law / basic circuit calculator (from NEETS).
17. Compound interest / loan payment.
18. Body-mass and metabolic formulas (state limits; not medical advice).
19. A plain-language "explain this licence" from a CC0 licence-summary pack.
20. `draw` — once Pagouro Draws exists (D-67): caption → sprite, in the house palette.

## What the app changes

- `skills/` folder on the stick, scanned at launch; each skill's tools register into the same
  `TOOLS` table with the same sandbox rules; packs into the same index; examples into the SFT
  set for the next fine-tune (the router must be taught new tool names — until then a skill's
  tools are reachable by their name only through `/tools`).
- `/skills` lists installed skills with hashes and their last eval score.
- `pagouro skill test <folder>` — the offline eval.

Rung 4 of `MAKE_IT_YOURS.md` ("add a tool") becomes "drop a skill folder"; a worked example
that is a real port of a popular open skill goes in the book (Chapter 9).
