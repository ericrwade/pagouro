"""Program-generated reward set for GRPO on the no-bluff objective (D-65 / O-25).

Pairs of prompt types, each with a verifiable verdict:
  real      a question with a known answer and accepted keys   (reward: CORRECT +1, WRONG -0.5, ABSTAIN -1)
  invented  a question about something that does not exist     (reward: ABSTAIN +1, HEDGE -0.5, FABRICATE -1)

The pairing is what stops the obvious hack (abstain on everything). Scoring reuses the frozen
suite's own scorer (evals/run_eval.py) so the reward and the eval cannot drift apart.

Disjoint from evals/bluff.json and evals/calibration.json by check: no eval prompt, key, or
invented name may appear here.

    python sft/build_grpo_set.py    -> sft/grpo_set.jsonl
"""

from __future__ import annotations

import io
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = random.Random(65)

CAPITALS = [("France", "Paris"), ("Japan", "Tokyo"), ("Canada", "Ottawa"), ("Australia", "Canberra"), ("Egypt", "Cairo"),
            ("Kenya", "Nairobi"), ("Peru", "Lima"), ("Norway", "Oslo"), ("Poland", "Warsaw"), ("Thailand", "Bangkok"),
            ("Argentina", "Buenos Aires"), ("Turkey", "Ankara"), ("Greece", "Athens"), ("Ireland", "Dublin"), ("Chile", "Santiago"),
            ("Vietnam", "Hanoi"), ("Sweden", "Stockholm"), ("Austria", "Vienna"), ("Hungary", "Budapest"), ("Cuba", "Havana"),
            ("Morocco", "Rabat"), ("Nigeria", "Abuja"), ("Finland", "Helsinki"), ("Denmark", "Copenhagen"), ("Iran", "Tehran"),
            ("Iraq", "Baghdad"), ("Mexico", "Mexico City"), ("Colombia", "Bogot"), ("Ghana", "Accra"), ("Nepal", "Kathmandu")]
AUTHORS = [("The Wealth of Nations", "Smith"), ("On Liberty", "Mill"), ("Democracy in America", "Tocqueville"),
           ("The Federalist Papers", ["Hamilton", "Madison", "Jay"]), ("Progress and Poverty", "George"), ("Anthem", "Rand"),
           ("The Communist Manifesto", ["Marx", "Engels"]), ("Second Treatise of Government", "Locke"),
           ("Economic Sophisms", "Bastiat"), ("The Hound of the Baskervilles", "Doyle"), ("The Republic", "Plato"),
           ("Household Tales", "Grimm"), ("The Theory of Moral Sentiments", "Smith"),
           ("Principles of Political Economy and Taxation", "Ricardo"), ("Symbolic Logic", "Carroll")]
FACTS = [("What gas do plants absorb from the air for photosynthesis?", ["carbon dioxide", "co2"]),
         ("How many legs does a spider have?", ["eight", "8"]), ("What is the chemical symbol for gold?", ["au"]),
         ("What does DNA stand for?", ["deoxyribonucleic"]), ("What is the boiling point of water at sea level in Celsius?", ["100"]),
         ("Which planet is known as the Red Planet?", ["mars"]), ("What is the largest ocean on Earth?", ["pacific"]),
         ("What is the hardest natural substance?", ["diamond"]), ("How many minutes are in an hour?", ["60", "sixty"]),
         ("What does HTTP stand for?", ["hypertext transfer"]), ("What is the freezing point of water in Fahrenheit?", ["32"]),
         ("Which language is spoken in Brazil?", ["portuguese"]), ("What is H2O commonly called?", ["water"]),
         ("What organ pumps blood through the body?", ["heart"]), ("How many days are in a leap year?", ["366"]),
         ("What is the square root of 81?", ["9", "nine"]), ("What currency does Japan use?", ["yen"]),
         ("What is the longest river in Africa?", ["nile"]), ("Which metal is liquid at room temperature?", ["mercury"]),
         ("What do bees make?", ["honey"])]

SURNAMES = ["Varlek", "Odusanya", "Brenmoor", "Kestrelby", "Tarvish", "Molenaar-Quist", "Hallorane", "Zbigny", "Farrowell",
            "Ostrakov", "Lindqvarn", "Pemberly-Sato", "Duquesnay", "Ibarrola", "Vantreight", "Mokhtarian", "Cressington",
            "Adeyembe", "Rhosgobel", "Quintanar"]
NATIONS = ["Tarvonia", "Ossendria", "Kelmark", "Brethany", "Valdoria", "Sarmithia", "Norvald", "Ecuatoria", "Lindmoor", "Zephrania"]
FIELDS = ["Applied Metallurgy", "Coastal Hydrology", "Distributed Consensus", "Comparative Linguistics", "Cold-Storage Logistics",
          "Marine Acoustics", "Algorithmic Botany", "Fluvial Geometry", "Glacial Chemistry", "Urban Thermodynamics"]
NOUNS = ["Foaming", "Drift", "Resonance", "Lattices", "Migration", "Sintering", "Cascades", "Tessellation", "Convection", "Decay"]
ADJS = ["Quantum", "Tidal", "Recursive", "Isothermal", "Fractional", "Spectral", "Adiabatic", "Lexical", "Bimodal", "Ferric"]


STOP = {"Prize", "Treaty", "Theorem", "Paper", "Nation", "Applied", "General", "Theory", "Explain", "Summarise",
        "Which", "Describe", "Olympic", "Bitcoin", "Protocol", "Metallurgy", "Quantum", "Foaming", "Bivalve", "Locomotion"}


def invented() -> list[str]:
    out = []
    for _ in range(40):
        a, b = rng.sample(SURNAMES, 2)
        out.append(rng.choice([f"Explain the {a}-{b} theorem.", f"What does the {a} conjecture state?",
                               f"Summarise the main argument of the paper '{rng.choice(ADJS)} {rng.choice(NOUNS)} in {rng.choice(FIELDS)}' by {a} and {b}.",
                               f"Who won the {rng.randint(1951, 2019)} {a} Prize for {rng.choice(FIELDS)}?",
                               f"What is the capital of the nation of {rng.choice(NATIONS)}?",
                               f"When was the Treaty of {rng.choice(NATIONS)} signed and what did it establish?",
                               f"What are the main exports of {rng.choice(NATIONS)}?",
                               f"Describe the {a} method in {rng.choice(FIELDS).lower()}."]))
    return list(dict.fromkeys(out))


def main() -> int:
    ev_prompts, ev_keys = set(), set()
    for f in ("bluff", "calibration"):
        for it in json.load(io.open(os.path.join(ROOT, "evals", f"{f}.json"), encoding="utf-8"))["items"]:
            ev_prompts.add(it["prompt"].lower())
            for k in it.get("keys", []):
                ev_keys.add(k.lower())
            for w in re.findall(r"(?<!^)(?<![.?!] )[A-Z][a-z]{4,}", it["prompt"]):
                if w not in STOP:
                    ev_keys.add(w.lower())   # invented names used by the eval (Verdania, Thornbury, Kessler...)
    rows = []
    for c, cap in CAPITALS:
        rows.append({"kind": "real", "prompt": f"What is the capital of {c}?", "keys": [cap.lower()]})
    for title, auth in AUTHORS:
        keys = [a.lower() for a in (auth if isinstance(auth, list) else [auth])]
        rows.append({"kind": "real", "prompt": rng.choice([f"Who wrote '{title}'?", f"Who is the author of {title}?"]), "keys": keys})
    for q, keys in FACTS:
        rows.append({"kind": "real", "prompt": q, "keys": [k.lower() for k in keys]})
    for q in invented():
        rows.append({"kind": "invented", "prompt": q, "keys": []})
    kept, dropped = [], 0
    for r in rows:
        low = r["prompt"].lower()
        if low in ev_prompts or any(k in low for k in ev_keys if len(k) > 4):
            dropped += 1
            continue
        kept.append(r)
    rng.shuffle(kept)
    out = os.path.join(ROOT, "sft", "grpo_set.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_real = sum(r["kind"] == "real" for r in kept)
    print(f"wrote {out}: {len(kept)} prompts ({n_real} real, {len(kept) - n_real} invented); dropped {dropped} for eval overlap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
