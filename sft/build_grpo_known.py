"""Known-real questions for the GRPO curriculum (D-71): things the model has actually read.

  * "Who wrote <title>?" for every Gutenberg work in the ledger (the name field holds "Title — Author");
    keys = the author's surname(s). The model trained on these books.
  * Capitals of ~80 well-known countries, and the hand-written FACTS/AUTHORS/CAPITALS from build_grpo_set.py.

Merged with sft/grpo_big_curriculum.jsonl into sft/grpo_curriculum.jsonl; eval-disjoint by the same
check as build_grpo_set.py.

    python sft/build_grpo_known.py   -> sft/grpo_curriculum.jsonl (+ counts by kind)
"""

from __future__ import annotations

import io
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sft"))
rng = random.Random(71)

MORE_CAPITALS = [("Germany", "Berlin"), ("Italy", "Rome"), ("Spain", "Madrid"), ("Portugal", "Lisbon"), ("Netherlands", "Amsterdam"),
                 ("Belgium", "Brussels"), ("Switzerland", "Bern"), ("Russia", "Moscow"), ("China", "Beijing"), ("India", "New Delhi"),
                 ("Pakistan", "Islamabad"), ("Bangladesh", "Dhaka"), ("Indonesia", "Jakarta"), ("Philippines", "Manila"),
                 ("South Korea", "Seoul"), ("North Korea", "Pyongyang"), ("Saudi Arabia", "Riyadh"), ("Israel", "Jerusalem"),
                 ("Syria", "Damascus"), ("Lebanon", "Beirut"), ("Jordan", "Amman"), ("Ethiopia", "Addis Ababa"), ("South Africa", "Pretoria"),
                 ("Tanzania", "Dodoma"), ("Uganda", "Kampala"), ("Senegal", "Dakar"), ("Algeria", "Algiers"), ("Tunisia", "Tunis"),
                 ("Libya", "Tripoli"), ("Sudan", "Khartoum"), ("Brazil", "Brasília"), ("Venezuela", "Caracas"), ("Ecuador", "Quito"),
                 ("Bolivia", "La Paz"), ("Uruguay", "Montevideo"), ("Paraguay", "Asunción"), ("Jamaica", "Kingston"), ("Haiti", "Port-au-Prince"),
                 ("Iceland", "Reykjavík"), ("Czech Republic", "Prague"), ("Slovakia", "Bratislava"), ("Romania", "Bucharest"),
                 ("Bulgaria", "Sofia"), ("Serbia", "Belgrade"), ("Croatia", "Zagreb"), ("Ukraine", "Kyiv"), ("Belarus", "Minsk"),
                 ("Lithuania", "Vilnius"), ("Latvia", "Riga"), ("Estonia", "Tallinn"), ("Georgia", "Tbilisi"), ("Armenia", "Yerevan"),
                 ("Azerbaijan", "Baku"), ("Kazakhstan", "Astana"), ("Uzbekistan", "Tashkent"), ("Afghanistan", "Kabul"), ("Mongolia", "Ulaanbaatar"),
                 ("Malaysia", "Kuala Lumpur"), ("Singapore", "Singapore"), ("New Zealand", "Wellington"), ("Fiji", "Suva"), ("Cambodia", "Phnom Penh"),
                 ("Laos", "Vientiane"), ("Myanmar", "Naypyidaw"), ("Sri Lanka", "Colombo"), ("Zimbabwe", "Harare"), ("Zambia", "Lusaka"),
                 ("Angola", "Luanda"), ("Mozambique", "Maputo"), ("Madagascar", "Antananarivo"), ("Somalia", "Mogadishu"), ("Yemen", "Sanaa"),
                 ("Oman", "Muscat"), ("Qatar", "Doha"), ("Kuwait", "Kuwait City"), ("Bahrain", "Manama"), ("Cyprus", "Nicosia"), ("Malta", "Valletta")]


def main() -> int:
    import build_grpo_set as B
    ev_prompts, ev_keys = set(), set()
    for f in ("bluff", "calibration"):
        for it in json.load(io.open(os.path.join(ROOT, "evals", f"{f}.json"), encoding="utf-8"))["items"]:
            ev_prompts.add(it["prompt"].lower())
            for k in it.get("keys", []):
                ev_keys.add(k.lower())
            for w in re.findall(r"(?<!^)(?<![.?!] )[A-Z][a-z]{4,}", it["prompt"]):
                if w not in B.STOP:
                    ev_keys.add(w.lower())
    known = []
    led = json.load(io.open(os.path.join(ROOT, "corpus.json"), encoding="utf-8"))["sources"]
    for s in led:
        if "gutenberg" not in (s.get("slug", "") + s.get("url", "")).lower():
            continue
        if "EXCLUDED" in str(s.get("slice", "")) or "SUPERSEDED" in str(s.get("slice", "")):
            continue
        name = s.get("name", "")
        if " — " not in name and " - " not in name:
            continue
        title, author = re.split(r" — | - ", name, 1)
        surnames = [w for w in re.findall(r"[A-Z][a-zé]+", author) if len(w) > 2 and w not in ("The", "Von", "Van", "And")]
        if not surnames:
            continue
        keys = [surnames[-1].lower()] + ([surnames[0].lower()] if len(surnames) > 1 else [])
        q = rng.choice([f"Who wrote '{title.strip()}'?", f"Who is the author of {title.strip()}?", f"Who was the author of '{title.strip()}'?"])
        known.append({"kind": "real", "prompt": q, "keys": keys, "source": "ledger:gutenberg"})
    for c, cap in B.CAPITALS + MORE_CAPITALS:
        known.append({"kind": "real", "prompt": rng.choice([f"What is the capital of {c}?", f"Name the capital city of {c}.", f"{c}'s capital is which city?"]),
                      "keys": [cap.lower()], "source": "capitals"})
    for title, auth in B.AUTHORS:
        keys = [x.lower() for x in (auth if isinstance(auth, list) else [auth])]
        known.append({"kind": "real", "prompt": f"Who wrote {title}?", "keys": keys, "source": "hand"})
    for q, keys in B.FACTS:
        known.append({"kind": "real", "prompt": q, "keys": [k.lower() for k in keys], "source": "hand"})
    kept, dropped, seen = [], 0, set()
    for r in known:
        low = r["prompt"].lower()
        if low in ev_prompts or any(k in low for k in ev_keys if len(k) > 4) or low in seen:
            dropped += 1; continue
        seen.add(low); kept.append(r)
    big = [json.loads(l) for l in io.open(os.path.join(ROOT, "sft", "grpo_big_curriculum.jsonl"), encoding="utf-8") if l.strip()]
    allrows = kept + big
    rng.shuffle(allrows)
    out = os.path.join(ROOT, "sft", "grpo_curriculum.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in allrows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"known reals {len(kept)} (dropped {dropped} for eval overlap); curriculum {len(allrows)} rows: {dict(Counter(r['kind'] for r in allrows))} -> {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
