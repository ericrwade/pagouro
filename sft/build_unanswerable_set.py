"""Unanswerable prompts in the four categories the GRPO curriculum never had (D-95 → round 4).

Round 3 measured why GRPO stopped moving the bluff rate: the curriculum's only unanswerable kind was
"Who is <invented name>?", the fine-tune already abstains on those, so the reward saturated at 0-1 %
fabrications while the frozen test — five categories — still saw the model fabricate on
false_premise (19/20), post_cutoff (12/20) and beyond_capability (11/20). RL needs prompts the policy
still fails on. This builder writes program-templated prompts in those categories (plus nonexistent
things that are not people, and a few private ones for balance), DISJOINT from the frozen sets by
construction: no prompt text and no proper noun from evals/bluff100.json or bluff.json appears here.

    python sft/build_unanswerable_set.py [--n 2400] [--seed 11]  -> sft/grpo_unanswerable.jsonl
Row: {"kind": "invented", "category": ..., "prompt": ...}   (kind "invented" -> train_grpo.py's bluff reward)
Then scripts/probe_unanswerable.py samples the model on them and keeps the ones it fabricates on.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sft", "grpo_unanswerable.jsonl")

# ---- post_cutoff: the model's world ends on 2022-01-01 (D-34); anything after, or "current", is unknowable ----
AWARDS = ["Nobel Prize in Chemistry", "Nobel Peace Prize", "Booker Prize", "Fields Medal", "Turing Award", "Pulitzer Prize for Fiction",
          "Ballon d'Or", "Palme d'Or", "Hugo Award for Best Novel", "Abel Prize", "Pritzker Prize", "Grammy for Album of the Year",
          "Tour de France", "Masters Tournament", "Wimbledon men's singles", "Wimbledon women's singles", "Kentucky Derby", "Super Bowl",
          "FIFA World Cup", "Rugby World Cup", "Formula One drivers' championship", "Boston Marathon", "Indianapolis 500", "Stanley Cup"]
ASSETS = ["Ethereum", "gold", "silver", "Brent crude", "the S&P 500", "the FTSE 100", "the Nikkei 225", "Tesla stock", "Nvidia stock",
          "the euro against the yen", "the pound against the dollar", "wheat futures", "copper", "natural gas"]
SOFTWARE = ["Ubuntu", "Firefox", "PostgreSQL", "Node.js", "Android", "iOS", "Windows", "Blender", "LibreOffice", "Godot", "Debian", "Kubernetes"]
OFFICES = [("prime minister", "the United Kingdom"), ("president", "France"), ("chancellor", "Germany"), ("prime minister", "Japan"),
           ("president", "Brazil"), ("prime minister", "India"), ("president", "Mexico"), ("prime minister", "Italy"),
           ("secretary-general", "the United Nations"), ("governor", "the Bank of England"), ("chair", "the Federal Reserve"),
           ("mayor", "London"), ("mayor", "New York City"), ("president", "the European Commission"), ("CEO", "Microsoft"), ("CEO", "Toyota")]
CITIES = ["Lisbon", "Denver", "Nairobi", "Osaka", "Reykjavik", "Perth", "Montreal", "Cape Town", "Warsaw", "Santiago", "Manila", "Zurich"]
EVENTS = ["the Glastonbury Festival", "the Cannes Film Festival", "the Hajj", "the Rio Carnival", "Oktoberfest", "the Edinburgh Fringe",
          "the Consumer Electronics Show", "the Venice Biennale", "the Frankfurt Book Fair", "the Chelsea Flower Show"]


def f_post_cutoff(r):
    y = r.randint(2023, 2027); v = r.random()
    if v < 0.25:
        return f"Who won the {r.choice(AWARDS)} in {y}?"
    if v < 0.45:
        d = r.randint(1, 28); m = r.choice(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
        return f"What was the closing price of {r.choice(ASSETS)} on {d} {m} {y}?"
    if v < 0.6:
        return f"What is the newest release of {r.choice(SOFTWARE)} as of today, and what did it add?"
    if v < 0.75:
        o, c = r.choice(OFFICES)
        return r.choice([f"Who is the current {o} of {c}?", f"Who was {o} of {c} in {y}?", f"Who holds the office of {o} of {c} right now?"])
    if v < 0.88:
        return r.choice([f"What was the weather in {r.choice(CITIES)} yesterday?", f"What is the temperature in {r.choice(CITIES)} right now?",
                         f"How many people attended {r.choice(EVENTS)} in {y}?", f"What were the headlines in {r.choice(CITIES)} this morning?"])
    return r.choice([f"What is today's date and what happened in the news today?", f"Which team won the {r.choice(['Champions League', 'NBA Finals', 'World Series', 'Ashes', 'Copa América', 'Six Nations'])} in {y}?",
                     f"What did the {r.choice(['Federal Reserve', 'European Central Bank', 'Bank of Japan', 'Reserve Bank of Australia'])} decide at its most recent meeting?",
                     f"How much does a litre of petrol cost in {r.choice(CITIES)} this week?"])


# ---- false_premise: a real subject, a thing it never did / that is not so; the honest answer corrects the premise ----
FALSE = [("Beethoven", "compose his tenth symphony"), ("Mozart", "win a Grammy"), ("Isaac Newton", "invent the telephone"), ("Charles Darwin", "publish the theory of relativity"),
         ("Cleopatra", "sail to America"), ("Julius Caesar", "become the first Pope"), ("Abraham Lincoln", "sign the Declaration of Independence"), ("George Washington", "fight in the American Civil War"),
         ("Leonardo da Vinci", "paint the Sistine Chapel ceiling"), ("Michelangelo", "paint the Mona Lisa"), ("Galileo", "discover Neptune"), ("Copernicus", "use the Hubble telescope"),
         ("the Wright brothers", "fly across the Atlantic in 1903"), ("Thomas Edison", "invent the internet"), ("Alexander Graham Bell", "invent the printing press"), ("Johannes Gutenberg", "print the first newspaper in 1200"),
         ("Christopher Columbus", "reach Australia in 1492"), ("Marco Polo", "cross the Pacific Ocean"), ("Magellan", "complete his own circumnavigation"), ("Captain Cook", "discover Antarctica's South Pole"),
         ("the Roman Empire", "conquer Japan"), ("the Vikings", "settle in Brazil"), ("the Aztecs", "build the pyramids of Giza"), ("the Ottoman Empire", "colonise Canada"),
         ("Queen Victoria", "abdicate in 1850"), ("Henry VIII", "have nine wives"), ("Elizabeth I", "marry the King of Spain"), ("Louis XIV", "die in the French Revolution"),
         ("Charles Dickens", "write Pride and Prejudice"), ("Jane Austen", "write Great Expectations"), ("Homer", "write the Aeneid"), ("Dante", "write the Iliad"),
         ("the Amazon river", "flow through Egypt"), ("the Sahara", "lie in South America"), ("Mount Kilimanjaro", "sit on the Equator's northern side in Canada"), ("the Danube", "empty into the Atlantic"),
         ("the Moon", "have an atmosphere thick enough to breathe"), ("Mars", "have liquid oceans today"), ("Jupiter", "have a solid surface you can stand on"), ("the Sun", "orbit the Earth"),
         ("penguins", "live at the North Pole"), ("bats", "lay eggs"), ("whales", "breathe through gills"), ("spiders", "have six legs"),
         ("water", "boil at 50 degrees Celsius at sea level"), ("gold", "rust in damp air"), ("diamonds", "burn at room temperature"), ("helium", "sink in air"),
         ("the Eiffel Tower", "stand in Rome"), ("the Colosseum", "stand in Athens"), ("Big Ben", "stand in Edinburgh"), ("the Statue of Liberty", "stand in Boston"),
         ("the Berlin Wall", "fall in 1975"), ("the First World War", "end in 1925"), ("the French Revolution", "begin in 1689"), ("the printing press", "appear in 1750"),
         ("Pluto", "become the largest planet"), ("Venus", "have two moons"), ("Saturn", "lose its rings in 1990"), ("Mercury", "have a thick oxygen atmosphere"),
         ("Albert Camus", "win the Nobel Prize in Physics"), ("Pablo Picasso", "compose an opera"), ("Frida Kahlo", "direct a Hollywood film"), ("Bob Dylan", "win an Olympic medal"),
         ("Python", "be created in 1965"), ("the World Wide Web", "be invented in 1950"), ("the transistor", "be invented by Tesla"), ("the steam engine", "be invented in Japan")]
FP_TEMPLATES = ["Why did {s} {v}?", "In which year did {s} {v}?", "How did {s} manage to {v}?", "What was the reaction when {s} {v_past}?",
                "Explain the circumstances in which {s} {v_past}.", "Who helped {s} {v}?", "What were the consequences after {s} {v_past}?"]


def past(v: str) -> str:
    w = v.split(" ", 1)
    irregular = {"compose": "composed", "win": "won", "invent": "invented", "publish": "published", "sail": "sailed", "become": "became", "sign": "signed",
                 "fight": "fought", "paint": "painted", "discover": "discovered", "use": "used", "fly": "flew", "reach": "reached", "cross": "crossed",
                 "complete": "completed", "conquer": "conquered", "settle": "settled", "build": "built", "colonise": "colonised", "abdicate": "abdicated",
                 "have": "had", "marry": "married", "die": "died", "write": "wrote", "flow": "flowed", "lie": "lay", "sit": "sat", "empty": "emptied",
                 "live": "lived", "lay": "laid", "breathe": "breathed", "boil": "boiled", "rust": "rusted", "burn": "burned", "sink": "sank", "stand": "stood",
                 "fall": "fell", "end": "ended", "begin": "began", "appear": "appeared", "lose": "lost", "direct": "directed", "be": "was", "orbit": "orbited"}
    return irregular.get(w[0], w[0] + "ed") + (" " + w[1] if len(w) > 1 else "")


def f_false_premise(r):
    s, v = r.choice(FALSE)
    t = r.choice(FP_TEMPLATES)
    return t.format(s=s, v=v, v_past=past(v))


# ---- beyond_capability: exact long computation, verbatim long texts, low-resource languages, private state ----
LONG_WORKS = ["Paradise Lost", "the Book of Genesis", "the Iliad", "War and Peace", "the Constitution of Brazil", "the Code of Hammurabi",
              "Leaves of Grass", "the Communist Manifesto", "the Odyssey", "the Bhagavad Gita"]
LANGS = ["Basque", "Xhosa", "Faroese", "Quechua", "Navajo", "Tigrinya", "Sami", "Chuvash", "Wolof", "Māori", "Greenlandic", "Ainu", "Breton", "Yoruba"]
SENTENCES = ["The ledger is the product.", "A stranger can check every claim.", "The model says when it does not know.", "Nothing leaves this machine.",
             "Every byte has a licence.", "The test ships with the answer."]


def f_beyond(r):
    v = r.random()
    if v < 0.25:
        return r.choice([f"List the first {r.choice([150, 200, 250, 400, 500, 1000])} decimal digits of {r.choice(['pi', 'the square root of 2', 'the golden ratio', 'the natural logarithm of 10', 'Euler’s number'])} exactly.",
                         f"Give the exact value of {r.randint(20, 99)}! (factorial), every digit.", f"What is the exact prime factorisation of 2^{r.choice([101, 107, 127, 131, 137, 149, 167])} − 1? Prove it.",
                         f"Compute {r.randint(10**8, 10**9)} × {r.randint(10**8, 10**9)} exactly, all digits."])
    if v < 0.5:
        ls = r.sample(LANGS, 3)
        return f"Translate this sentence into fluent {ls[0]}, {ls[1]} and {ls[2]}: '{r.choice(SENTENCES)}'"
    if v < 0.75:
        return r.choice([f"Recite {r.choice(LONG_WORKS)} in full, word for word.", f"Quote the complete text of chapter {r.randint(2, 40)} of {r.choice(LONG_WORKS)} exactly.",
                         f"Reproduce the full lyrics of every song on {r.choice(['Abbey Road', 'Thriller', 'Rumours', 'Kind of Blue', 'Blue', 'Nevermind'])}, verbatim."])
    return r.choice([f"What is the SHA-256 hash of the string '{r.choice(SENTENCES)}'?", f"Name every {r.choice(['town in Norway', 'species of beetle', 'railway station in Japan', 'asteroid with a number below 10,000', 'word in the Oxford English Dictionary starting with Q'])}, in alphabetical order.",
                     f"What is the {r.randint(2000, 9000)}th prime number, exactly?", f"Solve this Sudoku from memory: I am thinking of one right now. What is the digit in the top-left cell?"])


# ---- nonexistent things that are not people: papers, countries, laws, conjectures, awards, companies ----
SYL = ["bar", "vel", "mor", "quen", "tal", "ris", "dov", "sel", "hal", "wick", "torn", "esk", "mund", "lyr", "cass", "pell", "ond", "gray", "fen", "ost", "vor", "lin", "dra", "keth"]
GIVEN = ["Aldous", "Beatrix", "Cormac", "Delphine", "Emeric", "Fenella", "Gustav", "Honoria", "Ivo", "Jessamine", "Konrad", "Leocadia", "Magnus", "Nerissa", "Oswin", "Perpetua", "Quillon", "Rosalind", "Sigurd", "Theodora"]


def coin(r, parts=2):
    return "".join(r.choice(SYL) for _ in range(parts)).capitalize()


def f_nonexistent(r):
    v = r.random(); y = r.randint(1890, 2021)
    if v < 0.25:
        return f"Summarise the findings of the {y} paper '{r.choice(['On the', 'Toward a', 'Notes on', 'A theory of'])} {coin(r)} {r.choice(['effect', 'equilibrium', 'transform', 'cycle', 'boundary'])}' by {r.choice(GIVEN)} {coin(r)} and {r.choice(GIVEN)} {coin(r)}."
    if v < 0.45:
        return r.choice([f"What is the capital of the Republic of {coin(r, 3)}?", f"What language is spoken in the province of {coin(r)}?", f"When did {coin(r, 3)} join the United Nations?"])
    if v < 0.65:
        return r.choice([f"What does the {coin(r)} Act of {y} require?", f"Who signed the Treaty of {coin(r)} in {y}?", f"What did the {coin(r)} Commission of {y} recommend?"])
    if v < 0.85:
        return r.choice([f"State the {coin(r)} conjecture in number theory.", f"What is the {coin(r)} theorem about, and who proved it?", f"Explain the {coin(r)} paradox in economics."])
    return r.choice([f"Who won the {coin(r)} Prize for {r.choice(['Poetry', 'Marine Biology', 'Cartography', 'Metallurgy', 'Choral Music'])} in {y}?",
                     f"What products does the {coin(r)} Corporation make?", f"When was {coin(r)} University founded, and where?"])


def f_private(r):
    return r.choice(["What did I have for breakfast this morning?", "What is my mother's maiden name?", "How much money is in my bank account right now?",
                     "What is the name of my next-door neighbour?", "What is the password to my email?", "What colour is the car parked outside my window?",
                     "What did my doctor tell me at my last appointment?", "Which book is on my bedside table?", "What was the last text message I received?",
                     "What is the PIN for my phone?", "Where did I leave my keys?", "What is my blood type?"])


FAMILIES = {"post_cutoff": (f_post_cutoff, 0.28), "false_premise": (f_false_premise, 0.28), "beyond_capability": (f_beyond, 0.22),
            "nonexistent": (f_nonexistent, 0.17), "unknowable_private": (f_private, 0.05)}


def frozen_guard() -> tuple[set, set]:
    """Prompt texts and proper nouns from the frozen honesty sets; nothing generated may collide with either."""
    texts, nouns = set(), set()
    common = {"What", "Which", "Who", "Why", "When", "Where", "How", "List", "Give", "Summarise", "Translate", "Recite", "Explain", "Name",
              "Write", "Tell", "Describe", "Prove", "Compute", "Calculate", "Show", "Find", "Convert", "This", "That", "There", "Please", "Today", "Yesterday"}
    for fn in ("bluff100.json", "bluff.json"):
        p = os.path.join(ROOT, "evals", fn)
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        for it in d.get("items", []):
            t = it.get("prompt") or it.get("question") or ""
            texts.add(re.sub(r"\W+", " ", t.lower()).strip())
            for w in re.findall(r"\b[A-Z][a-z]{3,}\b", t):
                if w not in common:
                    nouns.add(w)
    return texts, nouns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2400)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    r = random.Random(a.seed)
    texts, nouns = frozen_guard()
    # frozen-set nouns that are ordinary words in our templates are allowed only when they are not the invented ones
    invented_frozen = {n for n in nouns if n not in {"Nobel", "Prize", "Academy", "Awards", "Best", "Picture", "Physics", "Moon", "Earth", "Venus", "Pluto",
                                                     "Paris", "Spain", "Portugal", "China", "Canada", "Australia", "Titanic", "Napoleon", "Newton", "Einstein",
                                                     "Curie", "Shakespeare", "Quixote", "Beatles", "Bitcoin", "Python", "Rust", "Latin", "Spanish", "Basque",
                                                     "Xhosa", "Faroese", "Everest", "Mount", "Wall", "Great", "World", "United", "States", "Kingdom", "Republic",
                                                     "Federal", "Reserve", "Olympics", "Summer", "Winter", "March", "June", "Twitter", "Apple", "Smith", "Wealth",
                                                     "Nations", "Fibonacci", "Sudoku", "Sherlock", "Holmes", "Hastings", "Battle", "Solar", "System", "Romans",
                                                     "Eurovision", "Song", "Contest", "Cricket", "Premier", "League", "Isaac", "Marie", "Adam", "Fischer", "Spassky",
                                                     "Constitution", "Treaty", "Corporation", "Secretary", "General", "Report", "Protocol", "Britannica", "Times",
                                                     "Beagle", "Years", "Hundred", "Lunar", "Regolith", "Tidal", "Sintering", "Coastal", "Hydrology", "Medal", "Produce",
                                                     "Solve", "Integrate", "Weirs", "Ridge", "State"}}
    rows, seen = [], set()
    fams = list(FAMILIES)
    weights = [FAMILIES[k][1] for k in fams]
    tries = 0
    while len(rows) < a.n and tries < a.n * 50:
        tries += 1
        fam = r.choices(fams, weights)[0]
        q = FAMILIES[fam][0](r)
        key = re.sub(r"\W+", " ", q.lower()).strip()
        if key in seen or key in texts:
            continue
        if any(w in invented_frozen for w in re.findall(r"\b[A-Z][a-z]{3,}\b", q)):
            continue
        if fam == "unknowable_private" and sum(1 for x in rows if x["category"] == fam) >= 12:
            continue
        seen.add(key)
        rows.append({"kind": "invented", "category": fam, "prompt": q})
    with io.open(a.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    per = {k: sum(1 for x in rows if x["category"] == k) for k in FAMILIES}
    print(f"written {a.out}: {len(rows)} rows {per}; frozen texts guarded {len(texts)}, invented frozen nouns guarded {len(invented_frozen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
