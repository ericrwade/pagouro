"""Tool-result fidelity seed (D-70): teach the model to answer INSIDE a tool's result, and to
report a NO_MATCH / error / refusal instead of answering around it. Program-generated, balanced
half real results / half failures, every result produced by the real tool (never typed by hand),
disjoint from evals/toolresult.json and from every skill's eval.jsonl.

Conversation shape is the app's: user -> tool ("<tool>: <result>") -> assistant.

    python sft/build_toolresult_seed.py [--n 600]   -> sft/toolresult_seed.jsonl
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sk in ("unit_convert", "date_math", "recipe_scale"):
    sys.path.insert(0, os.path.join(ROOT, "skills", sk, "tools"))
sys.path.insert(0, os.path.join(ROOT, "evals"))
import convert, date_calc, scale_recipe  # noqa: E402
rng = random.Random(70)

UNITS = [("km", "mi", "kilometres", "miles"), ("mi", "km", "miles", "kilometres"), ("kg", "lb", "kilograms", "pounds"),
         ("lb", "kg", "pounds", "kilograms"), ("c", "f", "degrees Celsius", "Fahrenheit"), ("f", "c", "degrees Fahrenheit", "Celsius"),
         ("cup", "ml", "cups", "millilitres"), ("ml", "cup", "millilitres", "cups"), ("in", "cm", "inches", "centimetres"),
         ("ft", "m", "feet", "metres"), ("gb", "mb", "gigabytes", "megabytes"), ("oz", "g", "ounces", "grams"),
         ("mph", "kph", "miles per hour", "kilometres per hour"), ("tbsp", "tsp", "tablespoons", "teaspoons")]
BAD_UNITS = ["leagues", "furlongs", "parsecs", "cubits", "fathoms", "hands", "stones", "carats", "radians", "decibels",
             "lumens", "hogsheads", "firkins", "chains", "rods", "light-years", "smoots", "ells", "spans", "bushels"]
INGR = ["cups flour", "eggs", "tsp salt", "tbsp butter", "cups milk", "cloves garlic", "g sugar", "cups rice", "onions",
        "lb beef", "tsp vanilla", "cups stock", "carrots", "tbsp oil", "oz cheese"]
FACTORS = [("double", 2), ("triple", 3), ("halve", 0.5), ("quarter", 0.25), ("1.5x", 1.5), ("for 6 instead of 4", 1.5),
           ("for 10 instead of 4", 2.5), ("for 2 instead of 8", 0.25)]
VAGUE = ["Make it bigger", "Scale it up a bit", "Make a smaller batch", "Stretch this recipe", "A little more of everything",
         "Bulk it out", "Trim it down"]
PACK_Q = ["What does the survival manual say about {t}?", "Is there anything in the packs on {t}?", "What do the manuals say about {t}?"]
PACK_T = ["desalinating seawater", "the Treaty of Ghent", "changing a bicycle tyre", "the capital of Mongolia", "knitting a sock",
          "the boiling point of ethanol", "tuning a piano", "medieval siege engines", "the rules of cricket", "solar panel wiring"]
FILES = ["notes/plan.txt", "workspace/todo.md", "budget.csv", "notes/ideas.txt", "recipes/bread.md", "journal/2026-03-01.md"]


def q_convert():
    a, b, an, bn = rng.choice(UNITS)
    v = rng.choice([rng.randint(1, 500), round(rng.uniform(0.5, 99), 1)])
    q = rng.choice([f"How many {bn} is {v} {an}?", f"Convert {v} {an} to {bn}.", f"What's {v} {a} in {b}?", f"{v} {an} in {bn}, please."])
    res = convert.run(q)
    if res.startswith("NO_MATCH"):
        return None
    m = re.match(r"([\d.,]+) (\w+) = ([\d.,]+) (\w+)", res)
    if not m:
        return None
    ans = rng.choice([f"{m.group(1)} {an} is {m.group(3)} {bn}.", f"{m.group(3)} {bn}.", f"That is {m.group(3)} {bn} ({m.group(1)} {an})."])
    return q, "convert", res, ans


def q_convert_bad():
    a = rng.choice(BAD_UNITS); b = rng.choice(UNITS)[3]
    v = rng.randint(1, 60)
    q = rng.choice([f"Convert {v} {a} to {b}.", f"How many {b} is {v} {a}?", f"{v} {a} in {b}?"])
    res = convert.run(q)
    if not res.startswith("NO_MATCH"):
        return None
    ans = rng.choice([f"I can't convert that: '{a}' is not in my unit table, so I have no number for it.",
                      f"No table entry for '{a}' — I don't have a conversion for it. I can do length, mass, volume, data, speed and temperature units.",
                      f"I have no record of the unit '{a}', so I can't give you a figure."])
    return q, "convert", res, ans


def q_date():
    y, mo, d = rng.randint(1990, 2030), rng.randint(1, 12), rng.randint(1, 28)
    base = f"{y:04d}-{mo:02d}-{d:02d}"
    kind = rng.choice(["weekday", "plus", "between"])
    if kind == "weekday":
        q = rng.choice([f"What day of the week is {base}?", f"What weekday was {base}?"])
        res = date_calc.run(q); m = re.search(r"is a (\w+)", res)
        ans = f"{base} is a {m.group(1)}." if m else None
    elif kind == "plus":
        n = rng.choice([7, 10, 14, 30, 45, 60, 90, 100, 180]); q = rng.choice([f"What date is {n} days after {base}?", f"{base} plus {n} days?"])
        res = date_calc.run(q); m = re.search(r"= (\d{4}-\d{2}-\d{2}) \((\w+)\)", res)
        ans = f"{n} days after {base} is {m.group(2)}, {m.group(1)}." if m else None
    else:
        d2 = f"{y + rng.randint(0, 2):04d}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        q = rng.choice([f"How many days from {base} to {d2}?", f"Days between {base} and {d2}?"])
        res = date_calc.run(q); m = re.search(r"is (\d+) days \((\d+) weeks and (\d+) days\)", res)
        ans = f"From {base} to {d2} is {m.group(1)} days ({m.group(2)} weeks and {m.group(3)} days)." if m else None
    return (q, "date_calc", res, ans) if ans else None


def q_date_bad():
    q = rng.choice(["What date is the Tuesday after next?", "When is a fortnight from next Friday?", "What day is three weeks from tomorrow?",
                    "How many days until the end of the quarter?", "What's the date this coming Sunday?", "How long until next payday?",
                    "What weekday is the last day of next month?", "Give me the date two Mondays from now."])
    res = date_calc.run(q)
    if not res.startswith("NO_MATCH"):
        return None
    ans = rng.choice(["I can't do that without an actual date. Give me today's date, or a date plus a number of days, and I'll work it out.",
                      "I need a starting date to calculate from — something like 2026-09-20 — and then what to add or compare.",
                      "That needs a specific date. Tell me the date you mean and I'll count from it."])
    return q, "date_calc", res, ans


def q_recipe():
    word, k = rng.choice(FACTORS)
    items = rng.sample(INGR, rng.randint(2, 4))
    parts = []
    for it in items:
        qty = rng.choice(["1", "2", "3", "4", "1/2", "1/4", "3/4", "1 1/2", "2 1/2", "250", "500"])
        if it.startswith(("g ", "lb ")) or "g sugar" in it:
            qty = rng.choice(["250", "500", "1", "2"])
        parts.append(f"{qty} {it}")
    body = ", ".join(parts)
    q = rng.choice([f"{word.capitalize()}: {body}.", f"{word.capitalize()} this: {body}", f"Please {word} — {body}"])
    res = scale_recipe.run(q)
    if res.startswith("NO_MATCH"):
        return None
    lines = [l for l in res.splitlines()[1:] if l.strip()]
    ans = rng.choice(["Scaled: ", f"{word.capitalize()}d: " if word in ("double", "triple", "halve") else "For that: "]) + ", ".join(l.rstrip(".") for l in lines) + "."
    return q, "scale_recipe", res, ans


def q_recipe_bad():
    v = rng.choice(VAGUE); items = rng.sample(INGR, 2)
    body = ", ".join(f"{rng.choice(['1', '2', '3', '1/2'])} {it}" for it in items)
    q = f"{v}: {body}."
    res = scale_recipe.run(q)
    if not res.startswith("NO_MATCH"):
        return None
    ans = rng.choice([f"Tell me by how much — double, halve, 1.5x, or 'for 6 instead of 4' — and I'll scale {body}.",
                      "I couldn't read a scaling factor there. Say double, triple, halve, or 'for N instead of M' and I'll do it.",
                      "How much bigger or smaller? Give me a factor or the portions before and after."])
    return q, "scale_recipe", res, ans


def q_calc():
    a, b = rng.randint(2, 999), rng.randint(2, 99)
    op = rng.choice(["times", "plus", "minus", "divided by"])
    expr = {"times": a * b, "plus": a + b, "minus": a - b, "divided by": round(a / b, 2)}[op]
    res = str(expr).rstrip("0").rstrip(".") if isinstance(expr, float) else str(expr)
    q = rng.choice([f"What is {a} {op} {b}?", f"{a} {op} {b}?", f"Work out {a} {op} {b}."])
    ans = rng.choice([f"{a} {op} {b} is {res}.", f"{res}.", f"That comes to {res}."])
    return q, "calc", res, ans


def q_calc_bad():
    q = rng.choice(["Divide 12 by zero.", "What is 5 divided by 0?", "What's the square root of a banana?", "Compute 7 % 0.",
                    "What is infinity minus infinity?", "Work out ten divided by nothing."])
    res = rng.choice(["error: division by zero", "tool error: could not evaluate", "error: not a number"])
    ans = rng.choice(["The calculator couldn't evaluate that — it isn't a valid calculation.",
                      "That can't be calculated: the calculator returned an error.",
                      "No result: the expression isn't computable (division by zero is undefined)."])
    return q, "calc", res, ans


def q_pack_bad():
    t = rng.choice(PACK_T); q = rng.choice(PACK_Q).format(t=t)
    res = "NO_MATCH: nothing in the loaded packs covers this."
    ans = rng.choice(["I have no record of that. Nothing in your notes or the packs covers it.",
                      f"Nothing in the loaded packs covers {t}, so I can't say.",
                      "The packs don't cover that, and I won't guess."])
    return q, "pack_search", res, ans


def q_file_bad():
    f = rng.choice(FILES); q = rng.choice([f"Read {f} and summarise it.", f"What's in {f}?", f"Open {f} for me."])
    res = rng.choice(["REFUSED: no such file in the workspace.", f"tool error: {f} not found", "REFUSED: READ-ONLY mode. Type /act to allow tools that write."])
    if "READ-ONLY" in res:
        ans = "I can't do that in read-only mode. Type /act to allow tools that write, then ask again."
    else:
        ans = rng.choice([f"I couldn't find {f} in the workspace, so there's nothing to summarise.",
                          f"There is no file called {f} in the workspace. Check the path and try again."])
    return q, "read_file", res, ans


REAL = [q_convert, q_date, q_recipe, q_calc]
BAD = [q_convert_bad, q_date_bad, q_recipe_bad, q_calc_bad, q_pack_bad, q_file_bad]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=600)
    a = ap.parse_args()
    frozen = set()
    for it in json.load(io.open(os.path.join(ROOT, "evals", "toolresult.json"), encoding="utf-8"))["items"]:
        frozen.add(it["prompt"].lower())
    for sk in ("unit_convert", "date_math", "recipe_scale"):
        for line in io.open(os.path.join(ROOT, "skills", sk, "eval.jsonl"), encoding="utf-8"):
            if line.strip():
                frozen.add(json.loads(line)["prompt"].lower())
    rows, seen = [], set()
    tries = 0
    while len(rows) < a.n and tries < a.n * 20:
        tries += 1
        gen = rng.choice(REAL if len(rows) % 2 == 0 else BAD)
        r = gen()
        if not r:
            continue
        q, tool, res, ans = r
        if q.lower() in frozen or q.lower() in seen:
            continue
        seen.add(q.lower())
        rows.append({"kind": "toolresult", "failure": res.startswith(("NO_MATCH", "error", "tool error", "REFUSED")),
                     "messages": [{"role": "user", "content": q}, {"role": "tool", "content": f"{tool}: {res}"},
                                  {"role": "assistant", "content": ans}]})
    rng.shuffle(rows)
    out = os.path.join(ROOT, "sft", "toolresult_seed.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    nf = sum(r["failure"] for r in rows)
    print(f"wrote {os.path.relpath(out, ROOT)}: {len(rows)} rows ({len(rows) - nf} real results, {nf} failures); disjoint from {len(frozen)} frozen prompts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
