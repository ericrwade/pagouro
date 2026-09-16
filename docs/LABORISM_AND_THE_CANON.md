# Eric's book, and a correction to the domain corpus

Written 2026-09-16 after reading *America vs. Americans: How Capitalism Has Failed a Capitalist
Nation and What We Can Do about It* (Eric Wade, 2024, 282 pages).

## Status of the book itself

**Excluded from the corpus**, on two independent grounds, both Eric's call:

1. Published 2024, so it fails the pre-generative-AI cutoff (D-34). He applied his own rule to his
   own book, which is the correct instinct and worth recording.
2. The copyright page reserves all rights to the publisher.

It is used here only as a **reading guide**: a private document that shapes what goes into the
corpus, without any of its text entering it.

## ⚠ The correction: the corpus was pointed at the wrong tradition

D-10 specified the domain corpus as the classical liberal and Austrian canon — Smith, Bastiat,
Mill, Locke, Hume, Tocqueville, the Austrians. That was inferred from "capitalism, freedom,
self-sovereignty, gold, fiat, debt, ownership," and it was **a reasonable inference that turns out
to be wrong about this author.**

Word counts across the book's 449,000 characters:

| Term | Count |
|---|---|
| labor | 747 |
| Laborism | 424 |
| tax | 384 |
| capitalism / capitalist | 125 |
| Marx | 60 |
| Marxism | 39 |
| blockchain | 34 |
| Smith | 9 |
| **Hayek, Mises, Rothbard, Friedman** | **0 each** |

Not one mention of the Austrian school in an entire book about economic systems. Marx appears sixty
times — engaged with and rejected, but engaged with seriously. Smith nine times.

The thesis, in Eric's own words from the preface:

> *"American Laborism isn't just a replacement for capitalism. It's an upgrade. Every human has the
> right to live a life of dignity… I've made a great living under capitalism… but it has failed
> us."*

Chapter titles make the position explicit: *Capitalism Failed Because Not Everyone Has Capital*;
*Marxism Fails Because Some People Do Have Capital*; *Why Labor Is Better — for Everyone — Than
Capital*.

**Had we built the corpus as specified, we would have produced a model steeped in exactly the
tradition its owner's own book argues against.** It would have answered questions about capital and
labor like a Mises Institute pamphlet, and Eric would have found it alien.

## The fix, which is better than either single tradition

**Include both traditions. Let the SFT carry the position.**

This is not a compromise; it follows directly from two decisions already made.

- **D-9** already says the ethos belongs in fine-tuning, not pretraining. Pretraining supplies
  breadth and reasoning; a few thousand curated examples supply the view. The corpus was never
  supposed to be the argument.
- **D-11's deflection set** already requires the model to argue each contested position in *both*
  directions, scoring a refusal to argue either side as failure. A model that has read only one
  tradition cannot do that. It would fail our own test.

A model that has read both Mises and Marx can reason about the disagreement. One that has read
either alone is a partisan, and a partisan that does not know it is exactly the failure mode this
project exists to avoid.

## Revised domain corpus

Keep everything in D-10, and add the tradition the book actually argues within. All public domain.

| Addition | Why | Status |
|---|---|---|
| **Henry George, *Progress and Poverty*** (1879) | Poverty amid progress, addressed through a tax system. The closest historical parallel to Laborism's structure that exists. | PD |
| **Marx, *Capital* and the earlier writings** | Engaged with sixty times. The model must know the argument it is rejecting. | PD |
| **Ricardo**, on the labour theory of value | The origin of the labour-value line both traditions descend from | PD |
| **Veblen**, *The Theory of the Leisure Class* | Institutional critique of capital ownership | PD |
| **Proudhon**, *What Is Property?* | Property as a contested question rather than an axiom | PD |
| **Smith**, *Wealth of Nations* | Already planned; Eric cites him and the labour chapters matter | PD |
| Progressive-era US economic and tax documents | Laborism is fundamentally a tax proposal | PD, US government |

And retain the liberal and Austrian material already specified, wherever it is openly licensed.
The point is coverage of the argument, not endorsement of a side.

## Laborism's own concepts, for the SFT set

These come from the book and belong in fine-tuning, written fresh rather than quoted:

- Capitalism fails because capital ownership is not universal, not because capital is wrong.
- Marxism fails from the opposite direction: some people do hold capital, and that is not fixable
  by abolition.
- Labour as the universal human input, and therefore the fairer basis for a system.
- Laborism expressed as a tax mechanism rather than an ownership seizure.
- Its application across education, defence procurement, healthcare, and foreign affairs.
- A blockchain role, mentioned thirty-four times, which needs Eric's clarification before anything
  is written about it.

**None of this is quoted.** The SFT examples state the positions in fresh language, which is what
makes them derived ideas rather than reproduced text.

## Open question for Eric

The book uses "blockchain" thirty-four times. Whether Laborism's mechanism actually depends on a
chain, and how, is not something to infer from word counts. Worth ten minutes of his time before
any SFT example touches it.
