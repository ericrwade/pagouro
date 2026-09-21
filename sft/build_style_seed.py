"""House-voice seed (D-78): eras written BC / AD, and celestial events dated as observed on Earth.
Hand-written pairs; the celestial ones carry the light-time caveat in the answer. The first rule is
also enforced on output by app/house_style.py; this seed teaches the model to write it that way in
the first place, and the second rule can only be taught.

    python sft/build_style_seed.py   -> sft/style_seed.jsonl
"""

from __future__ import annotations

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ERAS = [
    ("When was Rome founded, traditionally?", "Tradition puts the founding of Rome in 753 BC."),
    ("When did the Western Roman Empire fall?", "The conventional date is AD 476, when Romulus Augustulus was deposed."),
    ("When did Julius Caesar die?", "Julius Caesar was assassinated on the Ides of March, 15 March 44 BC."),
    ("When was the Battle of Hastings?", "The Battle of Hastings was fought in AD 1066."),
    ("When did Alexander the Great die?", "Alexander the Great died in 323 BC, in Babylon."),
    ("In which century did the Vikings first raid Lindisfarne?", "In the 8th century AD — the raid on Lindisfarne is dated to AD 793."),
    ("When was the Great Pyramid of Giza built?", "In the 26th century BC, during the reign of Khufu — roughly 2560 BC."),
    ("When did Augustus become the first Roman emperor?", "In 27 BC, when the Senate granted Octavian the title Augustus."),
    ("When did the Han dynasty begin?", "The Han dynasty began in 206 BC."),
    ("When was the Magna Carta sealed?", "In AD 1215, at Runnymede."),
    ("Which came first, the Parthenon or the Colosseum?", "The Parthenon, completed in 432 BC; the Colosseum was finished in AD 80."),
    ("When did Hannibal cross the Alps?", "In 218 BC, at the start of the Second Punic War."),
    ("What year did Constantine legalise Christianity?", "The Edict of Milan was issued in AD 313."),
    ("How long ago was 500 BC?", "About 2,500 years ago — there is no year zero, so from 500 BC to AD 2026 is 2,525 years."),
    ("Write the date of the Battle of Marathon.", "490 BC."),
    ("Is it BC or BCE?", "Pagouro writes BC and AD — 490 BC, AD 1066. Same years, one convention."),
]
CELESTIAL = [
    ("When did supernova SN 1987A explode?", "It was observed on Earth on 23 February 1987. The star was about 168,000 light-years away, so the explosion itself happened roughly 168,000 years before that — a figure that depends on the distance estimate. We date such events by when their light reached us."),
    ("When was the Crab Nebula supernova?", "It was observed on Earth in AD 1054, recorded by Chinese astronomers. The Crab Nebula is about 6,500 light-years away, so the explosion happened around 6,500 years before the light arrived."),
    ("When did Kepler's supernova happen?", "Kepler's supernova was observed on Earth in October AD 1604. It lies about 20,000 light-years away, so the event itself was roughly 20,000 years earlier; we date it by the observation."),
    ("When did Tycho's supernova occur?", "It was observed on Earth in November AD 1572. At a distance of roughly 8,000–10,000 light-years, the explosion happened that many years before the light reached us."),
    ("When was the first gravitational wave detected?", "GW150914 was observed on Earth on 14 September 2015. The merger of the two black holes happened about 1.3 billion years earlier; the date is the observation date."),
    ("When did the star Betelgeuse dim dramatically?", "The Great Dimming was observed on Earth from late 2019 to early 2020. Betelgeuse is about 550 light-years away, so what we watched had happened around AD 1470."),
    ("When did the gamma-ray burst GRB 221009A happen?", "It was observed on Earth on 9 October 2022. Its source was about 2.4 billion light-years away, so the burst itself predates the observation by that long; we date it by the detection."),
    ("When did the light from the Andromeda Galaxy that we see tonight leave it?", "About 2.5 million years ago. Anything we observe in Andromeda tonight is dated by tonight's observation on Earth, and the event itself is 2.5 million years old."),
    ("Was the 1006 supernova the brightest ever seen?", "SN 1006, observed on Earth in AD 1006, is thought to be the brightest recorded; it was about 7,200 light-years away, so the explosion was some 7,200 years before the observation."),
    ("When did the Sun's last big solar flare hit?", "For the Sun the light-time is only about 8 minutes, so the ordinary date is fine: the Carrington flare was observed on Earth on 1 September 1859, and the storm followed within a day."),
    ("When did the Chelyabinsk meteor explode?", "On 15 February 2013, over Chelyabinsk, Russia — inside the solar system the light-time is negligible, so the observed date is the event date."),
    ("How do we date events in other galaxies?", "By the date they are observed on Earth. The light took thousands to billions of years to arrive, so the event itself happened that long before; we can only estimate that gap from the distance. Pagouro states both: the observation date, and the light-time as a caveat."),
]


def main() -> int:
    out = os.path.join(ROOT, "sft", "style_seed.jsonl")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for q, a in ERAS:
            f.write(json.dumps({"kind": "style-era", "question": q, "answer": a}, ensure_ascii=False) + "\n")
        for q, a in CELESTIAL:
            f.write(json.dumps({"kind": "style-celestial", "question": q, "answer": a}, ensure_ascii=False) + "\n")
    print(f"wrote {os.path.relpath(out, ROOT)}: {len(ERAS)} era rows, {len(CELESTIAL)} celestial rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
