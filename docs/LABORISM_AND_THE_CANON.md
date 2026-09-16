# American Laborism, and what it means for the corpus

Written 2026-09-16 from *America vs. Americans* (Eric Wade, 2024), then **substantially corrected
the same day** after Eric read the first version. The error and the correction are both kept,
because this project does not quietly revise its own record.

---

## ⚠ First: I got this wrong, and how

My first pass counted words. Hayek, Mises, Rothbard and Friedman appeared zero times across 449,000
characters; Marx appeared sixty times; the chapter titles said capitalism had failed. I concluded
the book argued *against* the classical liberal tradition and proposed rebuilding the domain corpus
around Marx, Veblen and Proudhon.

That was wrong, and the method was the problem. **Sixty mentions of Marx were sixty rejections of
Marx.** Frequency told me what the book discusses, not where it stands, and I treated the first as
evidence of the second. A chapter titled *Marxism Fails Because Some People Do Have Capital* should
have been enough on its own.

Eric's correction, in his words:

> *"What I thought I was saying is that capitalism has failed — some people. The book says if
> capitalism is working for you, then pay your taxes and we will leave you alone. That is 180
> degrees from collectivism."*

Had this shipped, the model would have been trained on the wrong half of the argument and would
have sounded nothing like its author.

## What American Laborism actually is

| Element | Position |
|---|---|
| Capitalism | Has failed **some people**, not everyone. Not rejected. |
| If it works for you | Pay your taxes, and the state leaves you alone |
| Assistance | **In kind, never cash.** Hungry, get food. |
| Conditions | Federal assistance requires a **work** criterion **and** an **advancement** (education) criterion |
| Relation to Marxism | Explicitly rejected. Some people do hold capital, and that is fine. |
| Relation to collectivism | "180 degrees from it" |

The load-bearing idea: a floor under people, delivered in kind and conditioned on work and
advancement, sitting on top of an otherwise intact property-and-markets order. Eric's own summary of
where Ayn Rand would land on it: *"She'd likely hate American Laborism but it keeps people from
starving."*

## The corpus: D-10 stands

Eric, directly: *"Smith, Bastiat, Mises, Hayek, Rothbard — the Austrian and classical liberal canon
— that is perfect for ownership, currency, philosophy. Throw John Locke in there. Ayn Rand."*

So the original specification was right and my proposed replacement was not. **D-10 stands; D-37 is
superseded by D-38.**

Confirmed for the domain slice, all public domain:

- **Smith**, *The Wealth of Nations* and *Theory of Moral Sentiments*
- **Locke**, *Second Treatise* — explicitly added by Eric, and the source of the property argument
- **Bastiat**, *The Law*, *Economic Sophisms*
- **Mill**, **Hume**, **Ricardo**, **Tocqueville**
- **The Austrians** where openly licensed. Mises Institute publishes much of Mises and Rothbard
  under Creative Commons; verify per work rather than assuming the whole catalogue.
- **Founding documents**, the Federalist Papers, the Constitution

### The Ayn Rand problem, which is a real constraint

Rand died in 1982 and her major works are firmly in copyright. *Atlas Shrugged* (1957) and *The
Fountainhead* (1943) will not enter the public domain for decades. They cannot be in this corpus and
no amount of wanting changes that.

**One exception, and it is a good one:** *Anthem* (1938) is public domain in the United States
because its copyright was not renewed. It is on Project Gutenberg. It is short, and it is the purest
statement of the individualist case she ever wrote.

So: *Anthem* goes in. The rest is a licensed work like any other, and the same rule that excludes
Eric's own book excludes hers.

## Laborism's blockchain mechanisms

Eric's answer to O-15, which is more specific than the word count suggested. Four distinct roles:

1. **A tokenized federal balance sheet backing the currency.** American federal net worth —
   bitcoin, gold, diamonds, real estate — tokenized so that assets back the dollar.
2. **Asymmetric transparency.** All federal business on a chain, so *citizens can see what the
   government does, while the government cannot see what citizens do.* Requires zero-knowledge
   proofs, trusted execution, or fully homomorphic encryption.
3. **Bespoke AI training**, distributed, "in a Braintrust kind of way."
4. **Expenditure tracking**, to reduce scams, graft, corruption and theft by making federal spending
   auditable by anyone.

### Point 2 is the one worth noticing

*Citizens can see the government; the government cannot see citizens.*

That is Pagouro's own threat model stated at the scale of a state. The model runs on your machine
and your questions never leave it, while the weights, the corpus ledger and the release hash are
public and checkable by anyone. Transparency pointed at the powerful, privacy pointed at the
individual.

The book and the artifact are arguing the same thing in different registers. That is a genuinely
strong line for the release writing, and it was not designed — it fell out of both being built on
the same instinct.

## For the SFT set

These positions get stated in fresh language, never quoted:

- Capitalism failing *some* people is not capitalism failing.
- In-kind assistance over cash transfers, and why the distinction matters.
- Work and advancement conditions as the mechanism that distinguishes this from a welfare state.
- Why this is not Marxism: some people hold capital, and that is not the problem to solve.
- Asymmetric transparency as a design principle for institutions.
- Assets backing currency, and what tokenization does and does not solve.

## Still open

Whether *Anthem* alone is worth including for Rand, or whether her absence should simply be noted in
the ledger as a copyright constraint. Eric's call, low stakes either way.
