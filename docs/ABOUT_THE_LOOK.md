# Why does everything look like this?

*Ships beside the executable and on the project site. Short answer: because Pagouro has one look,
on purpose, and it comes from a particular place and time.*

## What the Belle Époque was

> "The Belle Époque (French for 'Beautiful Era') was a period of French and European history that
> began after the end of the Franco-Prussian War in 1871 and continued until the outbreak of World
> War I in 1914."
>
> "Art Nouveau is the most popularly recognised art movement to emerge from the period. This
> largely decorative style … characterised by its curvilinear forms, and nature-inspired motifs
> became prominent from the mid-1890s."
>
> — Wikipedia, *Belle Époque*, retrieved 2026-09-21; text licensed CC BY-SA 4.0
> (https://en.wikipedia.org/wiki/Belle_%C3%89poque).

It is the era of the Paris lithographic poster: Jules Chéret's chrome-yellow dancers on the
kiosks, Steinlen's black cat, Mucha's cartouches and whiplash borders, Toulouse-Lautrec's
Aristide Bruant in a red scarf. Advertising was being invented, and for about twenty years it was
art — flat colour laid on stone, one heavy contour, lettering drawn by hand, printed in the
thousands and pasted on walls. Everything from that print world published before 1929 is in the
public domain, which is how Pagouro can be trained on it and how you can use what it makes.

## Why it fits this machine

Pagouro is a small assistant that lives on a USB stick and never phones home. Its look had to be
one that a stick-sized model could actually produce, that could be *owned* rather than borrowed,
and that meant something. Pixel art was the honest ceiling of the model; a fixed 32-colour palette
is how pixel art becomes a style; and the Belle Époque poster was the print world whose whole
point was a bold, legible image made cheaply and put in front of everyone — which is the point of
this project too.

There is a second reason. The poster artists worked before the advertising industry, for printers
and cabarets and bicycle makers, and their pictures belong to everyone now. A machine that runs
on your own desk and keeps your words to yourself borrows their look rather than a corporation's.

## What "the look" is, exactly

Thirty-two colours in eight ramps (warm black, poster cream, chrome yellow, vermilion, Prussian
blue, sage, dusty rose, gold ochre); one-pixel warm-black contours; 32 or 64 pixels; the hermit
crab retreated into its shell in a cream medallion with a sunburst and a lettered band. The full
rules and the hex values are in `STYLE_GUIDE.md` beside this file.

## Want it to look like something else?

Fork it. The code is Apache 2.0, the weights and the packs are CC BY-SA 4.0, and the palettes are a
hundred lines in `app/palettes.py` — three alternatives are already there. The one thing that does
not travel with a new look is the name and the mark (see `docs/DECISIONS.md`, O-29): keep the
name only with the look.

## Credits

The images the style was learned from are listed, with their licences and hashes, in the image
ledgers of the repository (`data/images/*/ledger.jsonl`): The Metropolitan Museum of Art Open
Access (CC0), the Library of Congress Artists Posters collection (public domain, no known
restrictions), and Kenney (CC0). The style model is a LoRA on CommonCanvas-S-C (Creative Commons
Attribution-ShareAlike 4.0; CommonCanvas by Gokaslan et al., trained on CC-BY and CC-BY-SA
images). Pagouro's own drawings are released CC0.
