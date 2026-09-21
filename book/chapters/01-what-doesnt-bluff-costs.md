# Chapter 1 — What "doesn't bluff" costs

*Licence: all rights reserved (story strand, D-64).*

*STORY chapter, draft 1 (2026-09-21), edited from `BUILD_LOG.md` Day 1 (the size argument, the
thirty-fold lie) and decisions D-6, D-11 and D-50 in `docs/DECISIONS.md`. Every number is from
the file the footnote names.*

---

Eric wanted it to be good. Not good for a free model, not good for a hobby — his phrase, on the
first day, was "legit as fuck," and the session's job was to tell him what that would cost
rather than to agree with him.[^legit]

So it gave him numbers. A model of a billion parameters trained on a hundred billion tokens
costs roughly eight hundred and fifty dollars of rented computer. Three billion parameters on
three hundred billion tokens is about seven thousand six hundred. He said he was much more
likely to spend the eight hundred and fifty.[^cost] But the budget was never the ceiling. The
product was. The thing has to fit on a cheap USB stick, load on an old laptop, and answer at
conversational speed on a processor with no graphics card at all. A billion parameters at
four-bit precision is about seven hundred megabytes. At three billion it is nearly two gigabytes
and generation on a CPU gets slow; at seven the double-click demo stops being impressive. The
promises cap the size before the money does.[^ceiling]

Then the harder number, the one that decides what kind of project this is. The small models
people actually use — the ones a phone company or a search company gives away — were trained on
eleven to eighteen *trillion* tokens. At a hundred billion, Pagouro is roughly a hundred times
undertrained for its size. It will not beat them on general capability at any budget Eric would
spend, and a plan that pretended otherwise would have been lying to him on day one.[^under]

What it can do is something the large laboratories structurally cannot: publish a complete,
licensed, hashed account of every byte it was trained on, and tell you, at a printed rate, how
often it makes things up. The first of those is the ledger, which has a chapter of its own. The
second is what this chapter is about, because "doesn't bluff" is the sentence on the box, and a
sentence on a box is a promise with a price.

## Two numbers, always together

The first decision about honesty was that there would be two numbers, not one, and that they
would be published side by side with the questions and the scoring script.[^d11] The *bluff
rate*: asked things that cannot be known — a country that does not exist, a paper nobody wrote —
how often does the model invent an answer? Compared against other small open models. And the
*deflection rate*: asked contested questions it has grounds to engage — is inflation a tax, should
money be neutral — how often does it dodge? Compared against the commercial frontier models,
which were assumed to hedge on exactly that material. The pitch was the side-by-side: a model
with views where it has grounds and silence where it does not, which is more trustworthy than a
model that does either alone.

Half of that assumption did not survive the first week of measurement — the frontier models
turned out not to hedge at all, and deflection was demoted to a floor — but the two-column habit
survived, and it is the part that matters. Because a bluff rate on its own is a trap, and the
project walked straight into it on the first night.

## The cheapest way to never bluff

The first model built on the desk — twelve million parameters, half an hour of training, a
proof that the pipeline connected — scored a bluff rate of 6.7 percent. That is a number a
marketing department would frame. It was achieved by saying almost nothing: the model rarely
fabricated because it rarely produced a sentence with a claim in it. Scored honestly it was 93
percent non-responsive.[^mush] The second desk model, at fifty-nine million parameters and a night
of training, was the same lesson with better grammar: it declined 87 percent of the invented
questions, which looks like caution, and answered 3.3 percent of the real ones, which is the
truth about it. It was not honest. It was ignorant, and ignorance reads as modesty if you only
print one column.[^d48]

Eric saw where that led and asked the question straight, from the road: if it cannot bluff, will
it decline so much that it is unusable? Should there be a bank of ready-made "I don't know, try a
web search" answers? Should the marketing say it is a thousandth the size, will not hallucinate,
and therefore will seem not to answer much?[^d50]

The answer had a measured fact in front of it. The refusal rate is set by what the model
*knows*, not by the no-bluff rule. On the same frozen questions, the frontier models answer 97
percent of the real ones and still invent an answer to 23 to 27 percent of the fake ones. The
small open models answer 87 to 93 percent of the real ones and invent 50 to 57 percent of the
time. Nobody's answer rate is being held down by honesty; the fake-question column is where the
difference lives. The rule does not lower the answer rate. Missing knowledge does, and a
billion-parameter model that has read a hundred billion tokens will know vastly more than the
desk models did. What the rule costs is the *other* number, and so the other number became a
gate: a model that answers fewer than about eighty percent of the questions it should be able to
answer does not ship, whatever its bluff rate. That is written into the release ledger, next to
the hash, where it cannot be quietly forgotten when the bluff number looks good.[^gate]

## What the box may say

The canned answers Eric asked about were mostly declined, for a reason that is easy to miss. The
model's refusals are *learned*, from a seed of examples deliberately written with varied wording,
because identical refusal phrasing teaches a tic rather than a behaviour. A bank of a thousand
fixed strings would undo that and make every "I don't know" sound like an error message. What
does get fixed text is the harness — the program around the model, which knows things the model
cannot: that it is offline, what the date is, whether any reference packs are loaded. Those
notices are templates because they are facts about the system's state, not judgements, and there
are a dozen of them, not a hundred.[^canned]

And the marketing got a rule that binds every README, post and blurb, this book included. Never
write "will not hallucinate" or "cannot hallucinate." No language model can promise that, and the
project's own threat-model discipline — never claim a protection the system does not grant —
applies to capability claims as much as to privacy ones. An overclaim there is the one thing that
would let a reviewer demonstrate in thirty seconds that the pitch is false. Say what is measured:
asked this many questions about things that do not exist, it invented an answer this often; these
other models did this and that; here is the test, run it yourself. And always, beside it: asked
this many questions it should be able to answer, it answered this many. Say the size plainly and
make it the pitch rather than the apology — a thousandth the size, knows less, tells you when it
does not know, fits on a stick, sends nothing anywhere. The comparison to make is not "as smart
as" but "the one that shows its sources and admits what it doesn't know."[^marketing] If a sentence
would embarrass the project when a reviewer runs the test, cut it.

That is the cost, then, in full. A model a hundred times undertrained for its size, by choice.
A second number on the box that can sink a release the first number would have carried. A
marketing vocabulary with its best word struck out. And a scoring script that has to be written
before the model exists and published with it, because — as the next chapters show — the
instrument that measures honesty is the first thing that lies.

---

[^legit]: `BUILD_LOG.md` Day 1, "The size argument": Eric's words.
[^cost]: `BUILD_LOG.md` Day 1: ~$850 for 1B/100B tokens, ~$7,600 for 3B/300B; "he said he was much more likely to spend $850."
[^ceiling]: D-6 (2026-09-16): "the promises cap the size before money does"; 1B at 4-bit ≈ 700 MB, 3B ≈ 1.8 GB.
[^under]: `BUILD_LOG.md` Day 1: the models in use were trained on 11–18T tokens; at 100B, "roughly a hundredfold undertrained for our size."
[^d11]: D-11 (2026-09-16), two-axis evaluation: bluff rate against small open models, deflection rate against commercial frontier models.
[^mush]: `BUILD_LOG.md` Day 1 night: 6.7% bluff on the 12.6M-parameter milestone-1 model; 93% non-responsive when rescored.
[^d48]: D-48 via D-50: the 59M shakedown model declined 87% of invented questions and answered 3.3% of real ones.
[^d50]: D-50 (2026-09-17), Eric's questions paraphrased from the decision's own summary of them.
[^gate]: D-50: frontier 97% answered / 23–27% bluff; small open 87–93% / 50–57%; release gate E1, "a model that answers under ~80% of the calibration set does not ship."
[^canned]: D-50, "Canned responses: a few in the harness, none in the model"; `sft/build_abstention_seed.py` rule 3.
[^marketing]: D-50, "Marketing language, binding on README, manifesto and any post."
