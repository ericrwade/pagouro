# Why does the world need another AI — least of all a small one?

*The case for Pagouro, in plain words. Written 2026-09-22 (O-40, D-83); it is the source for the
README's first paragraph, the manifesto, and the book's opening. Every claim here is one the
artefact can be checked against; the rule (D-50, THREAT_MODEL) is that a sentence which would
embarrass the project when a reviewer runs the test gets cut.*

## The short answer

You do not need it for what it knows. It is roughly a thousandth the size of the models you
already use, trained on a hundredth of their data, and it will lose to them on every capability
test — Chapter 1 of the book says so in numbers. You need it, if you need it at all, for what it
can *promise*, and for the fact that the promises can be checked by a stranger.

## Four claims nobody bigger makes together

**Licensed.** Every byte it was trained on has a licence you can name and a row in a public
ledger with a hash. Not "an open dataset" — an open licence on a crawl says nothing about the
pages inside it — but a source, a licence, and a reason, per row. When the rights were unclear,
the answer was no, and the ledger records what was removed and why.

**Dated.** Everything it read was written or collected before 1 January 2022, before generative
AI arrived, and the date basis is on every row. The claim is precise: not "no machine-written
text" (a crawl date is when a page was fetched), but *this is the last corpus anyone will build
that could make the claim at all*.

**Honest, measured.** The headline number on the box is how often it invents an answer to a
question that has none, on a test that was written and frozen before the model existed, with
the answered-real rate always printed beside it — because a model that says nothing would score
perfectly on the first number alone. The test ships; run it yourself; run it on the big models
too. It will not say "does not hallucinate," because no model can promise that.

**Finished.** It is released once, frozen, signed, its hash anchored to Bitcoin, mirrored where
nobody has to pay for it again. No account, no update check, no telemetry, nothing you type
leaves the machine — and a seven-row table says exactly what "private" means and where it
stops. A maintained project drifts; a frozen one can be verified from an unknown mirror on a
hostile network by anyone with the manifest.

Each of these is a discipline, not a budget. That is why a one-person project can hold all four
and a well-funded lab holds none of them together: at web scale the first two cannot be claimed,
the third is not what benchmarks measure, and the fourth is the opposite of how a lab works.

## And one more: your words are yours

Some assistants mark what they write for you — a statistical watermark in the word choices, or
terms that limit what you may do with the text. Whether that is right or wrong is not the point
here; it is binary. Either your writing carries a mark you did not put there, or it does not.

Pagouro does not, and the claim has three checkable parts:

1. **There is no watermark.** The program that produces every word is on the stick and in the
   repository. Read it. There is no marking code because there is none.
2. **There cannot be one later.** The release is frozen and signed. A fork could add a watermark
   — that is what forks are for — but then it is not Pagouro: its manifest will not match, and
   the manifest is the only thing that makes something Pagouro.
3. **We claim no rights in what it writes for you.** The project asserts none over its outputs.
   What it writes is yours to use for anything. (We do not claim its output is free of *anyone's*
   rights: a language model can reproduce a sentence it read, and only you can check what you
   publish. When it quotes the packs on the stick, it tells you the source.)

That is the same property as privacy, seen from the other side: the thing that helps you think
neither watches what you say nor signs what you write.

## Who it is for

Someone who wants an assistant that admits what it does not know rather than one that knows
everything. Someone who needs their questions to stay on their own machine, and needs to be
able to verify that rather than trust it. Someone who wants to see the whole recipe — every
source, every decision, every mistake — and change it. And anyone who wants to know whether
one person, one desk computer and a rented card can build a model that keeps promises, because
the book of how it was done ships with it.

## Where this sits among the others

AI2's OLMo releases weights, data, code and checkpoints in full; it is the standard for open
research models and it is far more capable than this one. EleutherAI's Common Pile and its
Comma models are the closest relatives: trained only on openly licensed text. Pagouro is not a
competitor to either. It is smaller, dated, measured for honesty first, frozen, and built for a
person to carry — and it borrows gratefully from both where their sources meet its rules.
