"""British / American spelling register (D-68). Standard library only.

    to_british(text), to_american(text)  - dictionary swap, case-preserving, word-boundary only
    register(text) -> (n_british, n_american) - how many register-marked words a text contains

Built from ~180 stems plus four suffix rules (-or/-our, -er/-re, -ize/-ise, -yze/-yse) with the
words the rules must NOT touch listed explicitly (seize, size, prize, capsize, meter-the-device
is left alone, etc.). Words that differ in meaning rather than spelling (practice/practise,
program/programme, draft/draught, check/cheque, story/storey) are deliberately absent: a swap
there would change the sense, and the aim is register, not translation.
"""

from __future__ import annotations

import re

# American -> British, the irregular pairs (the suffix rules below cover the regular ones)
PAIRS = {
    "gray": "grey", "tire": "tyre", "tires": "tyres", "curb": "kerb", "mold": "mould", "molds": "moulds", "moldy": "mouldy",
    "plow": "plough", "plows": "ploughs", "pajamas": "pyjamas", "skeptic": "sceptic", "skeptical": "sceptical",
    "skepticism": "scepticism", "aluminum": "aluminium", "airplane": "aeroplane", "airplanes": "aeroplanes",
    "math": "maths", "sulfur": "sulphur", "sulfate": "sulphate", "pediatric": "paediatric", "anemia": "anaemia",
    "anemic": "anaemic", "estrogen": "oestrogen", "fetus": "foetus", "esophagus": "oesophagus",
    "encyclopedia": "encyclopaedia", "archeology": "archaeology", "archeological": "archaeological",
    "enroll": "enrol", "enrollment": "enrolment", "fulfill": "fulfil", "fulfillment": "fulfilment",
    "skillful": "skilful", "willful": "wilful", "distill": "distil", "instill": "instil", "artifact": "artefact",
    "artifacts": "artefacts", "ax": "axe", "mustache": "moustache", "licorice": "liquorice", "mom": "mum",
    "cozy": "cosy", "yogurt": "yoghurt", "judgment": "judgement", "acknowledgment": "acknowledgement",
    "omelet": "omelette", "jewelry": "jewellery", "pretense": "pretence", "defense": "defence",
    "defenses": "defences", "offense": "offence", "offenses": "offences",
    "license": "licence", "licenses": "licences", "catalog": "catalogue", "catalogs": "catalogues",
    "dialog": "dialogue", "dialogs": "dialogues", "analog": "analogue", "epilog": "epilogue", "prolog": "prologue",
    "traveling": "travelling", "traveled": "travelled", "traveler": "traveller", "travelers": "travellers",
    "canceling": "cancelling", "canceled": "cancelled", "modeling": "modelling", "modeled": "modelled",
    "labeling": "labelling", "labeled": "labelled", "fueling": "fuelling", "fueled": "fuelled",
    "jeweler": "jeweller", "counselor": "counsellor", "counselors": "counsellors", "marvelous": "marvellous",
    "signaling": "signalling", "signaled": "signalled", "totaling": "totalling", "totaled": "totalled",
    "leveling": "levelling", "leveled": "levelled", "quarreling": "quarrelling", "quarreled": "quarrelled",
    "dueling": "duelling", "channeling": "channelling", "channeled": "channelled", "marveled": "marvelled",
    "woolen": "woollen", "aging": "ageing", "tidbit": "titbit", "draftsman": "draughtsman",
    "specialty": "speciality", "specialties": "specialities", "cesium": "caesium", "diarrhea": "diarrhoea",
    "hemoglobin": "haemoglobin", "hemorrhage": "haemorrhage", "leukemia": "leukaemia", "maneuver": "manoeuvre",
    "maneuvers": "manoeuvres", "pretenses": "pretences", "donut": "doughnut",
    "donuts": "doughnuts", "favorite": "favourite", "favorites": "favourites", "coloring": "colouring",
    "colored": "coloured", "colorful": "colourful", "colors": "colours", "honors": "honours", "honored": "honoured",
    "honorable": "honourable", "flavors": "flavours", "flavored": "flavoured", "neighbors": "neighbours",
    "neighborhood": "neighbourhood", "neighborhoods": "neighbourhoods", "behaviors": "behaviours",
    "behavioral": "behavioural", "labors": "labours", "labored": "laboured", "harbors": "harbours",
    "humors": "humours", "armored": "armoured", "armory": "armoury", "savory": "savoury", "vapors": "vapours",
    "rumors": "rumours", "odors": "odours", "centers": "centres", "centered": "centred", "meters": "metres",
    "liters": "litres", "theaters": "theatres", "fibers": "fibres", "kilometers": "kilometres",
    "millimeters": "millimetres", "centimeters": "centimetres", "kilometer": "kilometre", "millimeter": "millimetre",
    "centimeter": "centimetre",
}
OR_OUR = ["color", "honor", "flavor", "labor", "neighbor", "humor", "behavior", "favor", "harbor", "armor",
          "vapor", "rumor", "savor", "odor", "valor", "vigor", "rigor", "splendor", "tumor", "candor", "clamor",
          "endeavor", "fervor", "parlor", "demeanor", "ardor"]
ER_RE = ["center", "meter", "liter", "theater", "fiber", "caliber", "saber", "somber", "specter", "luster",
         "scepter", "sepulcher", "goiter", "louver", "miter", "reconnoiter"]
IZE_KEEP = {"size", "seize", "prize", "capsize", "resize", "downsize", "oversize", "supersize", "sizes", "prizes",
            "seized", "seizes", "seizing", "capsized", "maize", "assize", "baize"}
# -ize words the rule converts (stems). Anything not listed is left alone, so the rule cannot invent words.
IZE = ["agon", "apolog", "apostroph", "atom", "author", "bapt", "brutal", "burglar", "cannibal", "capital", "carbon",
       "categor", "central", "character", "civil", "colon", "commercial", "computer", "critic", "crystal", "custom",
       "decentral", "demon", "digit", "dogmat", "dramat", "econom", "empath", "emphas", "energ", "epitom", "equal",
       "eulog", "familiar", "fantas", "fertil", "fictional", "final", "formal", "fossil", "galvan", "general",
       "global", "harmon", "hospital", "human", "hybrid", "hypnot", "ideal", "idol", "immortal", "immun",
       "individual", "industrial", "initial", "internal", "ion", "italic", "jeopard", "legal", "legitim", "liberal",
       "lion", "local", "magnet", "marginal", "martyr", "material", "maxim", "mechan", "memor", "memorial", "mesmer",
       "metabol", "mineral", "minim", "mobil", "modern", "monetar", "monopol", "moral", "motor", "mytholog",
       "narcot", "nasal", "national", "natural", "nebul", "neutral", "normal", "notar", "optim", "organ", "ostrac",
       "oxid", "pasteur", "patron", "penal", "personal", "philosoph", "pixel", "plagiar", "plural", "polar",
       "polymer", "popular", "pressur", "prior", "priorit", "privat", "professional", "proselyt", "public", "pulver",
       "quant", "radical", "random", "rational", "real", "recogn", "regular", "revolution", "romantic", "sanit",
       "satir", "scandal", "scrutin", "secular", "sensitiv", "serial", "sexual", "slogan", "social", "sodom",
       "solemn", "special", "stabil", "standard", "steril", "stigmat", "styl", "subsid", "summar", "symbol",
       "sympath", "synchron", "synthes", "tantal", "tempor", "terror", "theor", "token", "tranquil", "traumat",
       "trivial", "tyrann", "union", "urban", "util", "vandal", "vapor", "verbal", "victim", "visual", "vital",
       "vocal", "vulgar", "weapon", "western"]
YZE = ["anal", "paral", "catal", "electrol", "dial", "hydrol", "psychoanal", "breathal"]


def _build() -> dict[str, str]:
    us2uk = dict(PAIRS)
    for s in OR_OUR:
        for suf in ("", "s", "ed", "ing", "ful", "less", "able", "ite", "ites"):
            us2uk[s + suf] = s[:-2] + "our" + suf
    for s in ER_RE:
        base = s[:-2]
        us2uk[s] = base + "re"
        us2uk[s + "s"] = base + "res"
        us2uk[s + "ed"] = base + "red"
    for s in IZE:
        for suf, uk in (("ize", "ise"), ("izes", "ises"), ("ized", "ised"), ("izing", "ising"), ("ization", "isation"),
                        ("izations", "isations"), ("izer", "iser"), ("izers", "isers"), ("izable", "isable")):
            us2uk[s + suf] = s + uk
    for s in YZE:
        for suf, uk in (("yze", "yse"), ("yzes", "yses"), ("yzed", "ysed"), ("yzing", "ysing"), ("yzer", "yser")):
            us2uk[s + suf] = s + uk
    for w in IZE_KEEP:
        us2uk.pop(w, None)
    return us2uk


US2UK = _build()
UK2US = {v: k for k, v in US2UK.items()}
_WORD = re.compile(r"[A-Za-z]+")


def _case_like(src: str, out: str) -> str:
    if src.isupper():
        return out.upper()
    if src[:1].isupper():
        return out[:1].upper() + out[1:]
    return out


def _swap(text: str, table: dict[str, str]) -> str:
    def one(m: re.Match) -> str:
        w = m.group(0)
        t = table.get(w.lower())
        return _case_like(w, t) if t else w
    return _WORD.sub(one, text)


def to_british(text: str) -> str:
    return _swap(text, US2UK)


def to_american(text: str) -> str:
    return _swap(text, UK2US)


def register(text: str) -> tuple[int, int]:
    """(british_count, american_count) of register-marked words in the text."""
    uk = us = 0
    for w in _WORD.findall(text):
        lw = w.lower()
        if lw in UK2US:
            uk += 1
        elif lw in US2UK:
            us += 1
    return uk, us


if __name__ == "__main__":
    import sys
    print(len(US2UK), "pairs")
    print(to_british(sys.argv[1] if len(sys.argv) > 1 else "The color of the center is gray; we organized the catalog and analyzed the labor."))
