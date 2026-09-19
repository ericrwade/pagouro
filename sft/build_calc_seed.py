"""Program-generated SFT seed for the calc tool (O-18; D-61 found calc arguments wrong 4/4).

The Flash model routed word problems to calc but wrote the wrong expression: "640, knock 15
percent off" -> "640 * 0.15"; "seconds in 3 and a half hours" -> "3 * 100". Its SFT data had
only "What is 17 times 23?" -> "17*23". This seed teaches the TRANSLATION, with the expression
correct by construction (the script evaluates it), across the patterns people actually ask:
unit price x quantity, percent off/on, powers, unit conversions, splits, number words, tips,
averages, differences, compound phrasing. Router rows (question -> {"tool":"calc","arguments":
expr}) and tool_answer rows (question + "calc: expr = value" -> one-sentence answer).

Disjoint from evals/tooluse.json by construction: every generated prompt is checked against the
eval prompts and expected values before writing.

    python sft/build_calc_seed.py      -> sft/calc_seed.jsonl
"""

from __future__ import annotations

import io
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from prompts import ROUTER_PROMPT, SYSTEM_PROMPT  # noqa: E402

rng = random.Random(61)

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else "-" + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " and " + words(n % 100))
    return words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + words(n % 1000))


def fmt(v: float) -> str:
    return str(int(v)) if abs(v - round(v)) < 1e-9 else f"{v:.4f}".rstrip("0").rstrip(".")


ITEMS = ["notebooks", "tickets", "coffees", "bricks", "chairs", "candles", "bus fares", "plants", "books", "bolts"]
UNITS_TIME = [("hours", 3600), ("minutes", 60), ("days", 86400)]


def gen() -> list[tuple[str, str, str]]:
    """(question, expression, answer sentence template with {v})."""
    out = []
    for _ in range(90):
        q, p = rng.randint(2, 40), round(rng.uniform(0.5, 60), 2)
        item = rng.choice(ITEMS)
        out.append((rng.choice([f"If I buy {q} {item} at {p} each, what's the total?",
                                f"{q} {item} at {p} apiece -- how much altogether?",
                                f"What do {q} {item} cost at {p} each?"]),
                    f"{q}*{p}", f"{q} {item} at {p} each come to {{v}}."))
    for _ in range(80):
        a, pct = rng.choice([40, 60, 80, 120, 150, 200, 240, 360, 480, 640, 750, 900, 1200, 2500]), rng.choice([5, 10, 12, 15, 20, 25, 30, 33, 40, 50, 75])
        out.append((rng.choice([f"Take {a}, knock {pct} percent off it, what's left?",
                                f"What is {a} minus {pct}%?", f"{pct}% off {a} leaves how much?",
                                f"A {a} dollar coat is {pct} percent off. What do I pay?"]),
                    f"{a}*(1-{pct}/100)", f"{pct}% off {a} leaves {{v}}."))
        out.append((rng.choice([f"What is {pct} percent of {a}?", f"{pct}% of {a} is what?",
                                f"Add {pct} percent to {a}."]),
                    f"{a}*{pct}/100" if rng.random() < 0.6 else f"{a}*(1+{pct}/100)", "{v}."))
    for _ in range(50):
        b, e = rng.randint(2, 12), rng.randint(2, 12)
        out.append((rng.choice([f"What's {b} raised to the {e}th?", f"What is {b} to the power of {e}?",
                                f"{b}^{e}?", f"Compute {b} to the {e}."]),
                    f"{b}**{e}", f"{b} to the power of {e} is {{v}}."))
    for _ in range(60):
        n = rng.choice([1.5, 2, 2.5, 3, 3.5, 4, 6, 7.25, 8, 12])
        unit, secs = rng.choice(UNITS_TIME)
        target = rng.choice(["seconds", "minutes"]) if unit != "minutes" else "seconds"
        factor = secs if target == "seconds" else secs // 60
        n_txt = {1.5: "1 and a half", 2.5: "2 and a half", 3.5: "3 and a half", 7.25: "7 and a quarter"}.get(n, fmt(n))
        out.append((rng.choice([f"How many {target} are in {n_txt} {unit}?", f"{n_txt} {unit} is how many {target}?"]),
                    f"{fmt(n)}*{factor}", f"{n_txt} {unit} is {{v}} {target}."))
    for _ in range(50):
        total, ways = rng.choice([24, 36, 48, 60, 75, 96, 100, 120, 150, 180, 250, 300, 420, 1000]), rng.randint(2, 8)
        out.append((rng.choice([f"Split a {total} dollar bill {words(ways)} ways.", f"Divide {total} by {ways}.",
                                f"{total} shared equally among {ways} people is how much each?"]),
                    f"{total}/{ways}", f"{total} split {ways} ways is {{v}} each."))
    for _ in range(60):
        a, b = rng.randint(100, 2000), rng.randint(10, 999)
        op = rng.choice(["minus", "plus", "times"])
        sym = {"minus": "-", "plus": "+", "times": "*"}[op]
        if rng.random() < 0.5:
            out.append((f"{words(a).capitalize()} {op} {words(b)}?", f"{a}{sym}{b}", f"{a} {op} {b} is {{v}}."))
        else:
            out.append((rng.choice([f"What is {a} {op} {b}?", f"{a} {op} {b} equals?"]), f"{a}{sym}{b}", f"{a} {op} {b} is {{v}}."))
    for _ in range(40):
        bill, tip = rng.choice([18.5, 24, 31.2, 42, 56.75, 63, 88, 120]), rng.choice([10, 15, 18, 20, 25])
        out.append((rng.choice([f"What's a {tip}% tip on {bill}?", f"Bill is {bill}, tip {tip} percent -- how much is the tip?"]),
                    f"{bill}*{tip}/100", f"A {tip}% tip on {bill} is {{v}}."))
        out.append((f"Bill is {bill} with a {tip}% tip. Total?", f"{bill}*(1+{tip}/100)", "The total with tip is {v}."))
    for _ in range(40):
        xs = [rng.randint(10, 99) for _ in range(rng.randint(3, 5))]
        out.append((rng.choice([f"Average of {', '.join(map(str, xs))}?", f"What's the mean of {' and '.join(map(str, xs))}?"]),
                    f"({'+'.join(map(str, xs))})/{len(xs)}", "The average is {v}."))
    for _ in range(40):
        km = rng.choice([5, 10, 21.1, 42.2, 100, 250]); mi = rng.choice([3, 26.2, 50, 100])
        out.append((f"How many miles is {fmt(km)} kilometres?", f"{fmt(km)}*0.621371", f"{fmt(km)} km is about {{v}} miles."))
        out.append((f"Convert {fmt(mi)} miles to kilometres.", f"{fmt(mi)}*1.609344", f"{fmt(mi)} miles is about {{v}} km."))
        c = rng.choice([-10, 0, 12, 20, 25, 37, 100]); f = rng.choice([0, 32, 68, 98.6, 212])
        out.append((f"What is {c} Celsius in Fahrenheit?", f"{c}*9/5+32", f"{c} °C is {{v}} °F."))
        out.append((f"{fmt(f)} Fahrenheit in Celsius?", f"({fmt(f)}-32)*5/9", f"{fmt(f)} °F is {{v}} °C."))
    return out


def safe_eval(expr: str) -> float:
    import ast
    import operator as op
    ops = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg}

    def ev(n):
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.BinOp):
            return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return ops[type(n.op)](ev(n.operand))
        raise ValueError(expr)
    return ev(ast.parse(expr, mode="eval").body)


def main() -> int:
    ev = json.load(io.open(os.path.join(ROOT, "evals", "tooluse.json"), encoding="utf-8"))["items"]
    eval_prompts = {it["prompt"].lower() for it in ev}
    eval_values = {round(float(it["expect_value"]), 4) for it in ev if it.get("expect_value") is not None}
    rows, skipped = [], 0
    seen = set()
    for q, expr, tmpl in gen():
        v = safe_eval(expr)
        if q.lower() in eval_prompts or round(v, 4) in eval_values or q in seen:
            skipped += 1
            continue
        seen.add(q)
        rows.append({"kind": "calc_router", "synthetic": True, "messages": [
            {"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": q},
            {"role": "assistant", "content": json.dumps({"tool": "calc", "arguments": expr}, separators=(",", ":"))}]})
        if rng.random() < 0.7:
            date = f"2027-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
            rows.append({"kind": "calc_answer", "synthetic": True, "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(date=date)}, {"role": "user", "content": q},
                {"role": "tool", "content": f"calc: {expr} = {fmt(v)}"},
                {"role": "assistant", "content": tmpl.format(v=fmt(v))}]})
    rng.shuffle(rows)
    out = os.path.join(ROOT, "sft", "calc_seed.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"wrote {out}: {len(rows)} rows {kinds}; skipped {skipped} (eval overlap / duplicates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
