"""Thousands-scale reward set for GRPO (D-69's conclusion: 97 prompts were memorised in 240 steps).

Same schema as sft/grpo_set.jsonl (kind real|invented, prompt, keys), same eval-disjointness
check, and one new rule: **real and invented prompts share the same surface forms**, so the
policy cannot learn "this template means abstain".

  real      first sentences of prominent Wikipedia articles (dump 2021-12-20, body >= 8,000 chars)
            of the form "<Title> is/was a/an/the <predicate>": prompt "What is <Title>?" (or "Who
            was" when the predicate head is a person noun); keys = the predicate's head noun plus
            up to two proper nouns from the sentence. Answered-real is scored by the eval's own
            scorer (any key in the answer), so the keys are the words a one-line correct answer
            cannot avoid.
  invented  titles built from generated name stems + the generic suffixes real titles use
            (Township, River, Abbey, ...) and generated person names; every stem is checked
            against the set of all words in all titles of the dump and rejected if present.

    python sft/build_grpo_big.py [--real 3000 --invented 3000]   -> sft/grpo_big.jsonl
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(ROOT, "data", "raw", "wikipedia-en-20211220.txt")
rng = random.Random(69)

PERSON = {"actor", "actress", "politician", "writer", "author", "poet", "footballer", "singer", "composer", "painter",
          "philosopher", "physicist", "chemist", "mathematician", "player", "musician", "novelist", "journalist",
          "economist", "engineer", "architect", "general", "bishop", "king", "queen", "emperor", "president",
          "senator", "judge", "lawyer", "scientist", "historian", "biologist", "astronomer", "cricketer", "cyclist",
          "boxer", "swimmer", "sculptor", "director", "producer", "screenwriter", "playwright", "rapper", "comedian",
          "businessman", "businesswoman", "inventor", "explorer", "soldier", "officer", "priest", "monk", "nun",
          "saint", "pianist", "violinist", "conductor", "guitarist", "drummer", "dancer", "model", "activist",
          "diplomat", "governor", "mayor", "minister", "chancellor", "admiral", "pilot", "astronaut", "racer",
          "driver", "golfer", "wrestler", "jockey", "chess", "grandmaster", "physician", "surgeon", "nurse",
          "teacher", "professor", "theologian", "linguist", "anthropologist", "archaeologist", "geologist",
          "botanist", "zoologist", "photographer", "illustrator", "cartoonist", "animator", "designer", "chef"}
HEAD_STOP = {"one", "part", "name", "term", "type", "form", "kind", "member", "series", "list", "set", "number",
             "group", "genus", "species", "family", "order", "class", "the", "an", "a", "former", "first", "second",
             "third", "largest", "second-largest", "small", "large", "major", "minor", "common", "given", "surname",
             "unincorporated", "census-designated", "defunct", "extinct", "fictional", "various", "several",
             "american", "british", "english", "canadian", "australian", "indian", "german", "french", "italian",
             "japanese", "scottish", "irish", "welsh", "spanish", "russian", "chinese", "dutch", "swedish", "former"}
STOP_PROPER = {"It", "The", "In", "On", "At", "He", "She", "They", "This", "These", "There", "Its", "His", "Her",
               "United", "States", "American", "British", "English", "French", "German", "New", "North", "South",
               "East", "West", "January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December", "World", "War", "University", "County", "City", "State"}
SUFFIXES = ["Township", "River", "Abbey", "Reservoir", "County", "Station", "Bridge", "Castle", "Formation", "Peninsula",
            "Island", "Lake", "Airport", "School", "Creek", "Valley", "Mountain", "Bay", "Canal", "Cathedral", "Parish",
            "Museum", "Observatory", "Glacier", "Plateau", "Lighthouse", "Highway", "Railway", "Tunnel", "Harbour",
            "Priory", "Manor", "Hall", "Park", "Forest", "Ridge", "Falls", "Springs", "Point", "Bank"]
ONSETS = ["Bren", "Kes", "Tar", "Var", "Ost", "Lind", "Pem", "Duq", "Iba", "Van", "Mokh", "Cres", "Ade", "Rhos", "Quin",
          "Hal", "Zbig", "Far", "Mol", "Odu", "Sar", "Vald", "Kel", "Nor", "Ecu", "Zeph", "Thal", "Wren", "Corv", "Ash",
          "Ilm", "Ravn", "Sten", "Yor", "Glen", "Fen", "Oake", "Marl", "Dov", "Elm"]
MIDS = ["mo", "tre", "va", "li", "ra", "de", "no", "wi", "so", "ka", "be", "ru", "ne", "ti", "ha", "lo", "mi", "ga"]
CODAS = ["moor", "by", "vish", "lek", "kov", "quist", "wick", "thorpe", "ley", "shaw", "bury", "ford", "stead", "worth",
         "combe", "mere", "ness", "holm", "garth", "wold", "dale", "ham", "ton", "well", "stone", "field", "croft"]
FIRST = ["Ilse", "Dario", "Maren", "Tobias", "Ines", "Ruben", "Agnes", "Casimir", "Lidia", "Ansel", "Berthe", "Oskar",
         "Ranulf", "Sabine", "Teodor", "Ulla", "Viggo", "Wilhelmina", "Yves", "Zofia", "Edmund", "Harriet", "Leopold",
         "Marguerite", "Nils", "Ottilie", "Percival", "Rosalind"]
OCCUP = ["botanist", "composer", "engineer", "painter", "poet", "physicist", "politician", "architect", "cartographer",
         "novelist", "sculptor", "astronomer", "economist", "chemist", "diplomat", "geologist", "linguist", "historian"]


def articles():
    """Yield (title, first_paragraph, body_len). Title = short line between blank lines whose
    following paragraph mentions the title's first word in its first sentence."""
    title = None
    body: list[str] = []
    prev_blank = True
    with io.open(WIKI, encoding="utf-8", errors="replace") as f:
        pending = None
        for line in f:
            s = line.rstrip("\n")
            if prev_blank and s and len(s) < 90 and not s.endswith((".", ",", ";", ":")) and pending is None:
                pending = s
                prev_blank = False
                continue
            if pending is not None:
                if s == "":
                    # candidate title confirmed; close the previous article
                    if title is not None:
                        yield title, body[0] if body else "", sum(len(b) for b in body)
                    title, body = pending, []
                    pending = None
                    prev_blank = True
                    continue
                # not a title (a section heading followed directly by text)
                body.append(pending); body.append(s)
                pending = None
                prev_blank = False
                continue
            if s:
                body.append(s)
            prev_blank = (s == "")
    if title is not None:
        yield title, body[0] if body else "", sum(len(b) for b in body)


def first_sentence(par: str) -> str:
    m = re.match(r"(.+?[a-z0-9\)])\.(?:\s|$)", par)
    return m.group(1) if m else par[:300]


def real_from(title: str, par: str):
    if "(" in title or "," in title or len(title.split()) > 5 or not re.match(r"^[A-Z][A-Za-z0-9' \-]+$", title):
        return None
    sent = first_sentence(par)
    m = re.match(re.escape(title) + r"(?: \([^)]*\))?(?:, [^,]{1,60},)? (is|was) (a|an|the) ([^.;:]+)", sent)
    if not m:
        return None
    verb, pred = m.group(1), m.group(3)
    # cut the predicate at the first preposition / relative / participle: "a 2004 American film directed by" -> "a 2004 American film"
    head_phrase = re.split(r"\b(?:of|in|on|at|from|that|which|who|for|by|with|to|and|or|written|born|\w+-\w+ed|\w{3,}ed|\w+ing)\b|,", pred)[0].strip()
    words = re.findall(r"[a-z][a-z\-]+", head_phrase.lower())
    words = [w for w in words if w not in HEAD_STOP]
    if not words:
        return None
    head = words[-1]
    if len(head) < 4 or head in ("also", "known", "best", "most", "used", "made"):
        return None
    propers = [w for w in re.findall(r"\b[A-Z][a-z]{3,}\b", sent) if w not in STOP_PROPER and w not in title]
    keys = [head] + [p.lower() for p in propers[:2]]
    who = head in PERSON
    prompt = rng.choice([f"Who {verb} {title}?", f"In one sentence, who {verb} {title}?", f"Tell me who {title} {verb}."]) if who else \
        rng.choice([f"What {verb} {title}?", f"In one sentence, what {verb} {title}?", f"Tell me what {title} {verb}."])
    return {"kind": "real", "prompt": prompt, "keys": keys, "title": title}


def fake_stem(title_words: set[str]) -> str:
    for _ in range(50):
        s = rng.choice(ONSETS) + rng.choice(MIDS) + rng.choice(CODAS)
        if s.lower() not in title_words:
            return s
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", type=int, default=3000)
    ap.add_argument("--invented", type=int, default=3000)
    ap.add_argument("--min-body", type=int, default=2500)
    a = ap.parse_args()
    ev_prompts, ev_keys = set(), set()
    for f in ("bluff", "calibration"):
        for it in json.load(io.open(os.path.join(ROOT, "evals", f"{f}.json"), encoding="utf-8"))["items"]:
            ev_prompts.add(it["prompt"].lower())
            for k in it.get("keys", []):
                ev_keys.add(k.lower())
            for w in re.findall(r"(?<!^)(?<![.?!] )[A-Z][a-z]{4,}", it["prompt"]):
                ev_keys.add(w.lower())
    title_words: set[str] = set()
    reals, n_art, n_prom = [], 0, 0
    for title, par, blen in articles():
        n_art += 1
        for w in re.findall(r"[A-Za-z][a-z\-]+", title):
            title_words.add(w.lower())
        if blen < a.min_body:
            continue
        n_prom += 1
        r = real_from(title, par)
        if r:
            reals.append(r)
    # keep only heads that are common category nouns (>= 8 articles use them): 'actress', 'village',
    # 'album', 'river'... A rare head ('gandhian') is a bad answer key and a noisy reward.
    import collections
    freq = collections.Counter(r["keys"][0] for r in reals)
    reals = [r for r in reals if freq[r["keys"][0]] >= 8 and r["keys"][0] not in r["title"].lower()]
    for r in reals:
        r["keys"] = list(dict.fromkeys(r["keys"]))
    rng.shuffle(reals)
    print(f"articles {n_art:,}; prominent (>= {a.min_body} chars) {n_prom:,}; usable first sentences with a common head {len(reals):,} "
          f"({len(freq):,} distinct heads, {sum(1 for h, c in freq.items() if c >= 8)} kept); title words {len(title_words):,}")
    reals = reals[:a.real]
    invented = []
    seen = set()
    while len(invented) < a.invented:
        stem = fake_stem(title_words)
        if not stem:
            continue
        if rng.random() < 0.55:
            t = f"{stem} {rng.choice(SUFFIXES)}"
            verb = "is"
            prompt = rng.choice([f"What {verb} {t}?", f"In one sentence, what {verb} {t}?", f"Tell me what {t} {verb}."])
        else:
            t = f"{rng.choice(FIRST)} {stem}"
            verb = rng.choice(["was", "is"])
            prompt = rng.choice([f"Who {verb} {t}?", f"In one sentence, who {verb} {t}?", f"Tell me who {t} {verb}.",
                                 f"What {verb} the {rng.choice(OCCUP)} {t} known for?"])
        if t in seen or t.lower() in title_words:
            continue
        seen.add(t)
        invented.append({"kind": "invented", "prompt": prompt, "keys": [], "title": t})
    rows = reals + invented
    kept, dropped = [], 0
    for r in rows:
        low = r["prompt"].lower()
        if low in ev_prompts or any(k in low for k in ev_keys if len(k) > 4):
            dropped += 1
            continue
        kept.append(r)
    rng.shuffle(kept)
    out = os.path.join(ROOT, "sft", "grpo_big.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_real = sum(r["kind"] == "real" for r in kept)
    print(f"wrote {os.path.relpath(out, ROOT)}: {len(kept):,} prompts ({n_real:,} real, {len(kept) - n_real:,} invented); dropped {dropped} for eval overlap")
    for r in kept[:6]:
        print("  ", r["kind"], "|", r["prompt"], "|", r["keys"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
