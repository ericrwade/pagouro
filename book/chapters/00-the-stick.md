# Chapter 0 — The stick

*Licence: all rights reserved (story strand, D-64).*

*STORY chapter, draft 1 (2026-09-21), from `docs/ORIGIN.md` — the public account of the design
conversation, which is the ceiling on what this chapter may say about it (D-52) — and
`BUILD_LOG.md` Day 0 and Day 1. Every number is from the file the footnote names.*

---

The object this book is about fits in a pocket and costs less than lunch. It is a USB stick
with a program on it, and if you plug it into a computer with no internet connection and
double-click, a small artificial intelligence starts up, tells you it is offline, and waits for a
question. It answers at the speed of conversation on a processor with no graphics card. It
shows you where its answers come from. When it does not know, it says so — not always, and the
rate at which it fails to is printed on the box. Nothing you type leaves the machine.

None of that is remarkable on its own. Small models exist; offline runners exist; "I don't
know" is a sentence. What is unusual is the set of claims that go with it and the way they are
made. Every byte the model was trained on has a licence somebody can name and a row in a public
ledger, with a hash. All of it was written or collected before generative AI arrived, and the
date is on every row. The honesty claim is a measurement with a frozen test behind it, published
beside the score of the models you already use. The privacy claim is a seven-row table that says
where it stops. And the whole thing — model, program, data recipe, tests, decisions, and every
mistake made on the way — is in one repository, released once, as a finished thing, with no
promise to maintain it and an explicit invitation to take it and make it bigger.[^origin]

That is the pitch, and it is the reason the project is worth a book: not that a one-person
model can compete with the large ones, because it cannot and the first chapter says so in
numbers, but that it can make promises the large ones structurally cannot make, and keep them
in a way you can check.

## Where it came from

It began as a question Eric put to an earlier AI session over two days, before there was a
repository: could one person, with no graphics card, build a language model from scratch and
run it as a plain executable on a Windows machine? The first version of the idea was narrow —
a small model trained on a cryptocurrency forum, steeped in the things he had spent years
writing about. Talking it through turned it into something else: a standalone, fully
documented framework for a model that lives on a stick, runs offline anywhere, and needs
nothing from outside.[^origin] Three commitments came out of that conversation and have not
moved since. Every byte licensed and ledgered. Trained to say it does not know, with the claim
measured rather than asserted. Nothing the user types leaves the machine.

The conversation produced a document — the brief — and the brief is what the build session was
handed on the first morning. Eric asked it not to read the brief yet. That turned out to matter:
the scaffolding for the work — a folder that means something when you say its name, a decision
log that outranks every other document, a session log, a check that the keys and tools are
actually live — was designed around how the work would run and not around what the work was,
and the two stayed usefully separate.[^scaffold] The decision log is the reason this book can be
precise: eighty-odd numbered decisions, each with its date and its reason, and nothing marked
locked is re-argued later without a new number.

The name came out of the same conversation. *Págouros* is Greek for hermit crab: an animal that
carries a home it did not build and moves to a bigger one when it outgrows the first. The *ouro*
in the middle is an accident of spelling that points at the ouroboros, the snake eating its own
tail — a closed loop that needs nothing from outside. Both describe the product, and the crab
turned up later on the label, drawn in the manner of a French poster from the 1890s, for
reasons that get a chapter of their own.[^name]

## What this book is

Two braided strands. The *story* chapters are what happened, in order, edited from the build
log that was written at the end of every working day with the rule that numbers are measured,
not remembered, and that mistakes stay in — including the session's own, of which there were
two before a line of model code existed.[^mistakes] The *do-it* chapters stop the story every
few chapters and say: here is exactly how you do this part yourself, with the commands that
actually ran and the number you should see when it works. You can read the book as an account
and skip the do-it chapters. Or you can follow it as a manual and finish with your own stick.

Either way, the standard the book holds itself to is the one the model is held to. Its claims
should survive inspection. Where a number appears there is a footnote naming the file it came
from, and the files are in the repository. If you find one that does not match, the book is
wrong, and the ledger — the subject of Chapter 3 — is the place to start looking for how.

---

[^origin]: `docs/ORIGIN.md`, the public account of the design conversation; the transcript itself is private (D-52) and this chapter does not draw on it beyond that document.
[^scaffold]: `BUILD_LOG.md` Day 1, "Setting up": "He asked me not to read the brief yet."
[^name]: `BUILD_LOG.md` Day 0; `docs/ORIGIN.md`; the Belle Époque house style is D-74 and `docs/ABOUT_THE_LOOK.md`.
[^mistakes]: `BUILD_LOG.md` Day 1, "The first mistake was mine" and "The other mistake was also mine": a masking script that printed 59 of a 73-character key, and an install declared failed that had succeeded.
