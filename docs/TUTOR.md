# The tutor: "teach me and test me"

Eric's idea, 2026-09-16. A separate self-contained utility that **uses** Pagouro to teach roughly a
thousand pieces of information from the corpus, then tests the learner at their own pace. A free
education resource.

**Not part of Pagouro.** A second artifact that depends on it.

## Why this is not a bolt-on

American Laborism conditions federal assistance on two criteria: a **work** criterion and an
**advancement** criterion (D-38). The advancement criterion only means anything if advancement is
actually available to someone with no money, no broadband and no institution nearby.

An offline tutor on a USB stick is that availability. It is the mechanism the book's own argument
requires, built rather than proposed. Eric's book has a chapter on remaking the education system;
this is the smallest working piece of it.

That also makes it the strongest possible demonstration of Pagouro itself. "A model that fits on a
stick" is a specification. "A tutor that teaches a thousand things with no internet, no account and
no cost" is a use.

## Shape

| Property | Decision |
|---|---|
| Relationship to Pagouro | separate executable, loads the same GGUF |
| Model dependency | **model-agnostic**. Any GGUF, so it is testable before Pagouro exists |
| Network | none, ever. Inherits `THREAT_MODEL.md` in full |
| Progress data | local file, and the SAND/STONE choice (D-19) applies to it too |
| Content | derived from the corpus, shipped as a curated item bank, not improvised at runtime |
| Licence | same as Pagouro |

## The design question that decides everything

**Does the model generate the questions, or does it teach from a fixed item bank?**

Generate at runtime and a small model will eventually teach something false, which is catastrophic
for a tutor and directly contradicts the project's central claim. A model that does not bluff must
not bluff at a learner.

So: **a fixed, reviewed item bank of ~1,000 items, each traceable to a corpus source.** The model's
job is explanation, dialogue and adaptive pacing, not authorship of facts. Every item carries a
citation into the ledger, which means the tutor inherits the provenance claim rather than diluting
it.

The model does what models are good at — rephrasing, answering "why", noticing a confused answer,
adjusting difficulty — while the truth of what is taught rests on reviewed text.

## Mechanics

- **Spaced repetition** over the item bank, with per-item scheduling. Well-understood, works
  offline, no training required.
- **Free-text answers graded by the model** against a reference, with the learner able to challenge
  a grade and see the source. Multiple choice is easier and teaches recognition instead of recall.
- **"Show me the source"** on any item, since every item has one. This is the tutor's version of not
  bluffing.
- **Pacing by the learner**, not by a streak or a timer. No engagement mechanics.

## Known limitation, observed in the first working session

Built and tested end to end against `Qwen2.5-0.5B-Instruct` (`tutor/tutor.py`, transcript in
`tutor/sample_transcript.txt`). The grading pipeline itself works, but the **grading model's
judgment** does not yet meet the bar: in that test, given a question about the difference between
public and private keys, a student answer that was actually about blockchain (wrong topic
entirely) was graded CORRECT by the 0.5B grader.

This is not a harness bug -- the reference answer, the student's actual answer, and the prompt
asking the model to compare them were all passed through correctly. It is a capability gap in a
0.5B model used as a grader. **Before Pagouro itself is used as the tutor's grader, its grading
accuracy needs its own small evaluation set** (known-correct and known-wrong sample answers per
item, checked against what the grader actually outputs), the same discipline as the frozen eval
suite, rather than assuming grading fidelity comes for free with model size.

## The 1,000 items

Drawn from the corpus, weighted toward what a person actually benefits from knowing:

| Slice | Share | Examples |
|---|---|---|
| Money and economics | 30% | what inflation is, what a central bank does, supply and demand |
| Property, law and rights | 20% | Locke on property, the Constitution, what a contract is |
| Practical numeracy and finance | 20% | compound interest, reading a loan, percentages |
| The liberty canon | 15% | Smith, Bastiat, Mill, Rand's *Anthem* |
| Technology and crypto | 15% | what a hash is, what a blockchain is, key custody |

Every item: a question, a reference answer, an explanation, a difficulty, and a `source` field
pointing into `corpus.json`.

## Status

Idea recorded. Not a milestone yet — it depends on a trained Pagouro. But the item bank is
corpus-derived and can be built in parallel with everything else, and the tutor shell can be built
and tested against any GGUF today.

Named later. "Pagouro Teaches" is a placeholder, not a decision.
