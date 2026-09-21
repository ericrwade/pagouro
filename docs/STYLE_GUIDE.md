# Pagouro style guide

*This file ships beside the executable. It says how Pagouro looks and how it writes, and why. The
look and the voice are fixed in this version (D-74, D-78). Want it to look or sound like something
else? Fork it — the repository and the weights are free to fork, and `docs/MAKE_IT_YOURS.md` is
the manual.*

## The look: Belle Époque, posters over cards

Everything Pagouro draws — the mark, `/art`, the drawing model's output — uses one palette and one
set of rules, taken from the Paris lithographic poster of 1890–1910 (Chéret, Mucha, Steinlen,
Grasset, Toulouse-Lautrec, Bonnard): flat planes of colour, one heavy warm-black contour,
hand-lettered titles, the medallion and the cartouche. "Modernised" is what 64 pixels does to it.

**The palette — 32 colours, eight ramps of four, dark to light** (`app/palettes.py`, `belleepoque`):

| ramp | hex | role |
|---|---|---|
| warm black | `#1a1410 #332822 #55443a #7a6656` | the contour; never pure black |
| poster cream | `#b8a888 #d9c9a6 #efe3c6 #faf3df` | the paper; the lightest is the ground |
| chrome yellow | `#8a5f0c #c48f16 #eab826 #f8dd6a` | Chéret's yellow |
| vermilion | `#6e1c14 #a9301f #d9502c #f08a5a` | the poster red |
| Prussian blue | `#0e2a44 #174a72 #2d6fa0 #7fb0d4` | the poster blue |
| sage | `#3a4a34 #5f7452 #8fa27e #c3ceae` | Mucha's green |
| dusty rose | `#7a3c4a #a8606e #cf8e98 #ecc3c6` | Mucha's pink |
| gold ochre | `#7a5a1e #a8823a #cfa95e #e8cf94` | outlines and lettering in gold |

**Rules the renderer enforces:** every pixel is one of the 32 (nearest-colour, weighted RGB;
ordered dither allowed); a one-pixel contour in the darkest warm black around every figure; 32 or
64 px; the ground is poster cream, not white. Sunburst behind a medallion: alternate wedges of the
two lightest creams. Lettering: the 3×5 pixel face in `app/mark.py`, cream on a coloured band.

**The mark:** a hermit crab *retreated into its shell* — the shell is the mass, only the folded
claws and the eyes on their stalks show at the mouth, one antenna out; a spiral with a spire, a
cast shadow, inside a round cream medallion with a sunburst and a lettered band. Never a crab
walking with its body out; never a snail.

**The corpus behind the look:** public-domain and CC0 prints only — the Met Open Access poster
masters and trade cards, the Library of Congress Artists Posters collection, Kenney's CC0 sprite
packs — every image in a ledger with its licence and hash (`data/images/*/ledger.jsonl`). The
style model (D-75) is a LoRA on CommonCanvas-S-C (CC-BY-SA-4.0 weights, trained on CC-BY/BY-SA
images). Pagouro's own outputs are CC0.

## The voice

- **It says when it has no record.** "I have no record of that" is a complete answer, never a
  failure. It does not say "I don't hallucinate"; it says what its bluff rate is, next to what it
  answers correctly (D-50).
- **Eras are BC and AD.** Never BCE / CE. Written "753 BC", "AD 476", "the 3rd century AD". The
  harness rewrites the notation in the model's answers (`app/house_style.py`); the training seed
  teaches it (`sft/style_seed.jsonl`). This is a convention, not a claim about anything.
- **Celestial events are dated as observed on Earth.** For anything outside the solar system we
  know when the light arrived, not when the event happened, so: "SN 1987A was observed on Earth
  on 23 February 1987; the explosion itself was roughly 168,000 years earlier, a figure that
  depends on the distance estimate." Inside the solar system, where light-time is minutes to
  hours, the ordinary date is fine and the light-time may be mentioned.
- **Spelling follows the person.** Colour if they wrote colour, color if they wrote color (D-68).
  Within one answer, one register.
- **Numbers come from tools, and are shown with their source.** A calculation from `calc`, a
  conversion from `convert`, a roll from `roll` — each result line is the tool's, and provenance
  (bytes, hashes, formulas) is printed for the person, not fed back to the model.
- **It quotes its packs; it does not paraphrase them into facts.** Retrieval is where verbatim text
  belongs; training is for concepts and voice.

## Why does everything look like this?

Because a look is a promise. The palette is the same 32 colours everywhere, the contour is the same
weight, and the crab is always in its shell — so a Pagouro-made image is recognisable across every
fork, stick and profile picture that keeps the name. See `ABOUT_THE_LOOK.md` for what the Belle
Époque was and why it fits a machine that never phones home.

Want it to look like something else? Fork it. Three other palettes are in `app/palettes.py`
(Trade Card, Gaslight, Naturalist Plate), the rules are a hundred lines, and the corpus tools take
any CC0 source. Keep the name only with the look (O-29).
