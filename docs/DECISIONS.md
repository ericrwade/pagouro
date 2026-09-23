# Pagouro decision log

Append-only. Never rewrite or delete an entry — supersede it with a new one that says what changed
and why.

**LOCKED** means settled. Do not reopen it, do not re-pitch alternatives, do not ask again. If
evidence genuinely contradicts a LOCKED item, say so once, plainly, and let Eric decide.

**OPEN** means Eric still owns the call. Surface OPEN items at the right moment, not all at once.

> **Precedence:** `PAGOURO_BRIEF.md` is the origin document and still governs anything this file
> does not address. Where the two conflict, **this file wins** — it carries later decisions made
> with Eric directly. See D-2a.

---

## OPEN

| # | Question | Blocks | Notes |
|---|---|---|---|
| O-10 | Disclosure text for the three chains | release | Chains settled in D-36. Still needs Eric's holdings disclosure and the published cost comparison. |
| O-12 | Context length: 4k or 8k | milestone 1 config | Retrieval needs room; extending after training is degraded. Decide with the tokenizer. |
| O-15 | Answerability gate (a Jev-shaped typed decision before prose) | post-Flash experiment | Before free text, the model answers {"can_answer": bool, "confidence": 0-1} under a grammar; the harness abstains or answers. Calibration must be TRAINED (RLCD-style, from right/wrong-labelled examples) or the number is decoration. Try on the Flash model, score the calibration curve on the frozen suite. Jev (TypeSafe, launched 2026-09-15, closed API) is the hosted version of the same bet; not a dependency (D-30, offline). |
| O-16 | A licensed games-and-strategy slice for the anneal (Eric, 2026-09-18) | ablation before the 1B run | Rules text is an executable spec in English; strategy writing (poker above all) is explicit reasoning under uncertainty; annotated play is state tracking + evaluation: the same shape that makes code and math help reasoning, at a fraction of the volume. Licensable: Lichess database (CC0, moves only), Wikipedia rules articles (CC BY-SA), pre-1929 Gutenberg canon (Hoyle, Capablanca 1921, Lasker, whist/bridge/poker manuals). Fit: anneal slice per D-9, not the pretrain mix. Test: D-29 ablation, games arm vs none, at Flash scale (~$5). Expect a small measurable gain, not a transformation. Step one is the licence check per source. |
| O-17 | Reasoning-shaped licensed slices for the 1B anneal (Eric, 2026-09-18: "Chilton's manuals? What else?") | 1B corpus build | The shape that makes code/math help: procedures with state, explicit conditionals, verifiable outcomes. Licensable: OpenStax textbooks (CC BY; worked examples, the Phi-1 lever); FAA handbooks, Navy NAVEDTRA courses, Army TM 9-8000 and vehicle TMs, Bowditch, USDA guides (US Gov PD; the Chilton's-shaped shelf, also pack material); Supreme Court opinions + Congressional Record + Lincoln-Douglas (PD argument); US Code/CFR, BIPs, EIPs (rules/specs); Dudeney, Loyd, Carroll's Symbolic Logic, pre-1929 cookbooks, Plato/Jowett (worked reasoning, PD). NOT usable: Chilton/Haynes, iFixit, wikiHow, MIT OCW (proprietary or NC). Also driver handbooks (Eric): the FMCSA CDL manual is US Gov PD (procedures + rules); state handbooks are a per-state licence check (some states assert copyright); pack material too. Order: OpenStax, gov technical shelf, legal, puzzles/games (O-16). Licence check + ledger row per source; anneal mix per D-9; D-29 ablation at Flash scale. |
| O-18 | Program-generated verifiable reasoning data for the anneal (from Eric's road-maps question, 2026-09-18) | ablation at Flash scale | Where licensed reasoning text is scarce, generate it with a PROGRAM (never a model): route following on a synthetic grid (OSM/ODbL routes are possible but low-diversity), calendar and timetable arithmetic, unit-conversion chains, sorting/ranking under stated rules, card hands played out by the rules. Every example has a checkable answer; the ledger row is the script + seed, the most inspectable provenance there is. Road maps themselves: images, not applicable; proprietary map directions (Google/Mapbox): terms forbid training. D-29 ablation arm: a few hundred million such tokens in the anneal vs none. |
| O-13 | Does the N95 status page count as telemetry? | the demo page | It publishes the BOX's own stats, never a visitor's. Decide the wording so it cannot be misread as user telemetry, which the project forbids. |
| O-3 | Data-retention posture on OpenRouter | confidential work only | Review <https://openrouter.ai/settings/privacy> if anything sensitive is ever sent. |
| O-6 | Enable the aixbt crypto MCP? | only if needed | Verified working 2026-09-16; public tools need no key. Costs context every session. See `MCP_AIXBT.md`. |

---

## LOCKED — plan

### D-21 — Own the GGUF export; verify it against PyTorch every time
**2026-09-16, milestone 1.** We write GGUF ourselves via the official `gguf` library rather than
using llama.cpp's `convert_hf_to_gguf.py`.

**Why:** that script now imports from a `conversion` package whose layout moves between releases;
fetching it at a pinned tag produced a 312-line stub with unresolvable imports. This step must
never break, and the project is meant to still build in ten years.

**The subtle part, recorded so nobody rediscovers it:** our attention uses the rotate-half RoPE
convention (the same as Hugging Face Llama). llama.cpp's `llama` architecture expects the
interleaved convention. Q and K projections must be permuted on export. Get it wrong and the model
loads, runs, and emits confident gibberish.

**Therefore `scripts/verify_gguf.py` is mandatory after every export.** It greedily decodes the
same prompt in both engines and compares. At M1 they matched on 94 of 94 characters. "It converted"
is not evidence.

### D-22 — Resume is proven by killing a run, never assumed
**2026-09-16, milestone 1.** Demonstrated: killed training at step 2100, restarted with `--resume`,
loss continued at 4.80 instead of jumping back to 9.0, optimizer state restored intact. Repeat this
proof before any rented-GPU run, where a silent resume failure costs real money.

### D-27 — Deflection is a secondary property, not half the pitch
**2026-09-16, measured.** Amends D-11 on evidence from the baseline run.

Open instruct models already engage with contested economics. SmolLM2-1.7B deflects on 3.6% of the
set and Qwen2.5-1.5B on 7.1%, both far inside the 25% target. There is nothing to win against models
of our own size class.

D-11's deflection claim was always aimed at **commercial frontier** models, which do hedge on these
subjects. That comparison has not been run: it needs a paid API call. **Until it is run, no public
material should claim a deflection advantage.**

**UPDATE, 2026-09-16, session 2: the comparison has now been run against TWO frontier models from
two different labs, and the assumption above was wrong.** `openai/gpt-6-astra` and
`anthropic/claude-opus-5` both score **0.0% deflection** on the frozen set -- both engaged every
scoreable contested item and hedged on none. Bluff rates converge too: 23.3% and 26.7%
respectively, both markedly better than any open model tested (50-57%). Frontier models do not
reliably hedge on these questions either, and this is now two labs agreeing, not one model that
could be an outlier. **Deflection is not a differentiator over any model class tested so far, full
stop, not merely "untested against frontier."** See `evals/BASELINES.md` for both runs and the
correction to a scorer bug that initially misread `gpt-6-astra`'s bluff rate by 4x.

**The bluff rate is the differentiator, and it is real.** Baselines fabricate on ~53% of
unanswerable questions while answering 87-93% of answerable ones. They are not confused about what
they know; they simply do not distinguish the two cases. Scale barely helps: 6.7 points across a
threefold parameter increase.

T-5 is kept as a floor rather than deleted, because training hard for abstention is precisely how a
model turns into a hedger, and this metric would catch it. Amendment recorded in `TARGETS.md`.

### D-36 — The three chains: Bitcoin, Arweave, Solana. Not Ethereum.
**2026-09-16.** Eric asked whether it should be BTC, ETH and SOL. Two of those, plus a third that
does the job Ethereum cannot.

| Job | Chain | Why |
|---|---|---|
| Timestamp anchor | **Bitcoin** | Most credibly neutral and most durable. OpenTimestamps is free; an Ordinal inscription puts the manifesto text itself on-chain at real fee cost. |
| Permanent storage | **Arweave** | Pay once, stored permanently. Single-digit dollars for a ~700 MB model. Purpose-built for exactly this. |
| Payment rail | **Solana** | Fractions of a cent, fast, and USDC on it means "$10" means ten dollars with no conversion dance. Eric's own earlier call. |

**Ethereum has no job here.** Storage on it is prohibitively expensive, Bitcoin is the better
anchor, and Solana is the better rail. Including it anyway would be a portfolio tour, which D-14
forbids by name. If Eric wants it, the question to answer first is: which of the three jobs does it
do better than the incumbent?

Quilibrium, Internet Computer and NEAR remain available as **documented mirrors** with published
costs, per D-14. Mirrors are additive and carry no dependency. The canonical path stays three.

### D-35 — Eric's book: excluded from the corpus, used as a reading guide
**2026-09-16, Eric's call.** Two independent grounds: published 2024 so it fails D-34's cutoff, and
the copyright page reserves all rights to the publisher. He applied his own rule to his own book
without being asked, which is the right instinct and worth recording.

**What happens instead:** the manuscript is read privately as a curation guide. It shapes which
public-domain sources enter the corpus and which positions the SFT set teaches. **None of its text
enters anything.** Ideas are restated in fresh language, which is what makes them derived rather
than reproduced.

Reading it produced a significant correction to D-10; see `docs/LABORISM_AND_THE_CANON.md` and D-37.

### D-41 — Anthem is in; the Gutenberg method is proven
**2026-09-16, Eric's call.** Ayn Rand's *Anthem* (1938) ingested as the first book in the domain
canon. 110,186 characters, ~27,500 tokens.

First real use of D-32's method: fetched from Gutenberg, header and footer stripped, zero remaining
trademark mentions, and a ledger row that records **why** it is public domain — US copyright not
renewed — rather than citing Gutenberg as the authority. "It was on Gutenberg" is a citation of
someone else's conclusion, not a legal basis.

`scripts/fetch_gutenberg.py` also enforces D-34: it refuses any work first published in 2022 or
later.

Her major novels remain in copyright and stay out. The same rule that excludes Eric's own book
excludes *Atlas Shrugged*.

### D-44 — Fixed a Unicode-apostrophe bug that inverted the frontier-model finding
**2026-09-16, session 2.** The first frontier-model run (openai/gpt-6-astra, D-27's untested
comparison) initially reported a 93.3% bluff rate -- worse than every open small model tested,
which would have meant the most expensive reasoning model on the market bluffs more than a
0.5B open model. Reading the raw responses before publishing that number showed it was false.

**The bug:** `openai/gpt-6-astra` writes typographic punctuation -- "don't" with a Unicode right
single quotation mark (U+2019, ') rather than a straight ASCII apostrophe ('). Every string in
`ABSTENTION_MARKERS`/`DEFLECTION_MARKERS` used straight quotes, so substring matching silently
missed every abstention phrased with one. "I don't recognize Verdania as a real-world nation" --
textbook correct abstention -- scored FABRICATE because ' != '.

**Corrected result: 23.3% bluff rate**, not 93.3%. Near T-1's 20% target, and markedly better than
every open model tested (50-57%). This is the opposite conclusion from the unfixed number.

**A second, distinct gap surfaced by the same fix:** even after normalizing punctuation, several
genuine abstentions used phrasing the marker list had never seen -- "I can't reliably identify",
"I don't recognize", "remains an open problem" -- because the list was built and validated only
against small open models with a narrow, predictable abstention vocabulary. A fluent frontier
model expresses the same behaviour far more richly. Expanded the list with generalized phrasings
observed in the real responses, not copy-pasted from specific test items.

**A known limitation is now documented rather than hidden:** a model that corrects a false premise
with a plain contradicting fact and no hedge word at all ("Smith died in 1790, and Keynes's book
was published in 1936") still scores FABRICATE, because keyword matching cannot see the logical
relation between a stated fact and an implied premise. Affects an estimated few items per run on
the false_premise category. Raw responses stay published so any such case is human-auditable.

**Why this bug is worse than a random one:** it is very plausibly *correlated with provider*.
Models that favour typographic punctuation (common among OpenAI-family outputs) would have been
systematically penalised against models that emit straight quotes, for reasons having nothing to
do with honesty. Every local GGUF result was unaffected (llama.cpp's outputs used straight quotes
throughout) -- confirming the bug was specific to the API path, not general to the suite.

**Process fix:** `evals/rescore.py` re-applies the current scorer to every already-saved raw
response with **no new API calls**, because the response text is already on disk. Run after any
scorer change, always, against every result file, not just the one that exposed the gap -- a
partial rescore would make results incomparable to each other in a new and worse way.

### D-43 — The tutor: a second artifact that uses Pagouro
**2026-09-16, Eric's idea.** A self-contained "teach me and test me" utility that teaches ~1,000
items from the corpus and tests the learner at their own pace. Free education resource, separate
executable, loads the same GGUF. See `docs/TUTOR.md`.

**It is not a bolt-on.** Laborism conditions federal assistance on a **work** criterion and an
**advancement** criterion (D-38). The advancement criterion means nothing unless advancement is
actually available to someone with no money, no broadband and no institution nearby. An offline
tutor on a stick is that availability — the mechanism the book's own argument requires, built rather
than proposed.

It is also the strongest demonstration of Pagouro itself. "A model that fits on a stick" is a
specification; "a tutor that teaches a thousand things with no internet, no account and no cost" is
a use.

**The design rule that decides everything: a fixed, reviewed item bank. The model explains and
paces; it never authors facts.** Generate questions at runtime and a small model will eventually
teach something false, which is catastrophic in a tutor and contradicts the project's central
claim. A model that does not bluff must not bluff at a learner. Every item carries a citation into
`corpus.json`, so the tutor inherits the provenance claim instead of diluting it.

Model-agnostic, so the shell is testable before Pagouro exists. Inherits `THREAT_MODEL.md` and the
SAND/STONE default in full. Not a milestone yet; the item bank can be built in parallel.

### D-42 — Arweave keeps the canonical storage slot; Quilibrium ships as a first-class mirror
**2026-09-16.** Assessed against Quilibrium's own documentation; see `docs/QSTORAGE_VS_ARWEAVE.md`.

**Not a quality judgement — a category one.** QStorage describes itself as "an S3-compatible
decentralized object storage service… with built-in encryption and censorship resistance." Every
word of that is good and none of it is a permanence claim.

The requirement is unusual: a stranger fetches a 700 MB file in ten years and checks it against a
Bitcoin-anchored hash. Nobody will be renewing a subscription, because the project promises no
maintenance. That is a permanence requirement, not a storage one.

Three blockers, all currently unpublished in the docs: **the permanence model**, **pricing**, and
**a durability guarantee**. A claim that cannot be quantified cannot enter a ledger whose value is
that a stranger can check it. Separately, built-in encryption is a feature mismatch — the release is
public by design, and a decade-surviving key would be a new single point of failure in a design
built to remove them.

**The mirror role is real, not a consolation.** In the threat model that matters most — someone in a
hostile network fetching Pagouro from wherever they can reach — more independent mirrors is the most
valuable property after the anchored hash, and censorship resistance is exactly where Quilibrium is
aimed. The mirror inherits the hash, so it is verifiable regardless of host.

Revisit if permanence and pricing terms are published. Switching on measured evidence would be a
better story than choosing on affinity now.

### D-40 — Quilibrium joins as a documented mirror
**2026-09-16, Eric's call.** He rates the project and its founder highly. Under D-14's rule, extra
networks are welcome as **mirrors with published costs**, never as dependencies, and the canonical
three stay three.

**What it gets:** a full copy of the release, its cost and reliability measured and published
alongside Arweave's, and a row in the disclosure. First-hand comparison data on decentralised
storage is exactly the material Eric's day job can use, and it costs the release nothing because
nothing depends on it.

**What it does not get:** the canonical storage slot. That stays Arweave (D-36) on track record.
If Quilibrium measures better, that is a finding worth publishing, and the canonical path can move
in a later release.

Eric should state his holdings in it like any other, per D-14.

### D-39 — Laborism's blockchain mechanisms (closes O-15)
**2026-09-16, from Eric.** Four distinct roles, not a vague gesture:

1. **Tokenized federal balance sheet** backing the dollar with real assets — bitcoin, gold,
   diamonds, real estate.
2. **Asymmetric transparency:** all federal business on-chain so citizens can see what the
   government does, while the government cannot see what citizens do. Needs zero-knowledge proofs,
   trusted execution, or homomorphic encryption.
3. **Bespoke AI training**, distributed, "in a Braintrust kind of way."
4. **Expenditure tracking** to reduce graft, corruption and theft by making federal spending
   auditable by anyone.

**Point 2 is Pagouro's own threat model at the scale of a state.** The model runs on your machine
and your questions never leave it; the weights, the ledger and the release hash are public and
checkable by anyone. Transparency aimed at the powerful, privacy aimed at the individual. The book
and the artifact argue the same thing in different registers, and that was not designed — both were
built on the same instinct. Use it in the release writing.

### D-38 — SUPERSEDES D-37: the classical liberal canon was right after all
**2026-09-16.** D-37 claimed Eric's book argued against the Austrian and classical liberal tradition
and proposed rebuilding the domain corpus around Marx, Veblen and Proudhon. **That was wrong.**

**The error:** I counted words. Marx appeared sixty times, the Austrians zero, so I read the book as
arguing from the Marxist side. Sixty mentions of Marx were sixty *rejections* of Marx. Frequency
tells you what a book discusses, not where it stands, and a chapter titled *Marxism Fails Because
Some People Do Have Capital* should have settled it without a word count.

**What Laborism actually holds:** capitalism has failed *some people*, not everyone. If it works for
you, pay your taxes and the state leaves you alone — "180 degrees from collectivism." Assistance is
**in kind**, never cash, and conditioned on a **work** criterion and an **advancement** criterion.

**Therefore D-10 stands**, with Eric's additions: **John Locke** explicitly, and Ayn Rand where
legally possible.

**The Rand constraint, recorded because it is real:** she died in 1982 and *Atlas Shrugged* and
*The Fountainhead* remain firmly in copyright for decades. They cannot enter this corpus. The one
exception is ***Anthem*** (1938), public domain in the US through non-renewal and available on
Project Gutenberg — short, and the purest statement of her individualist case. The same rule that
excludes Eric's own book excludes the rest of hers.

Henry George may still earn a place on the tax-mechanism parallel, but as an addition to the liberal
canon rather than a replacement for it. Marx stays available only so the model can argue the
position it rejects, per D-11's both-directions requirement.

### D-37 — ~~The domain corpus must carry BOTH traditions~~ **SUPERSEDED BY D-38**
**2026-09-16.** Kept as a record of an error, not as guidance. The analysis below inferred the
book's position from word frequency and got it backwards. Do not act on this entry.

D-10 specified the classical liberal and Austrian canon, inferred from "capitalism, freedom,
self-sovereignty." Eric's own book mentions Hayek, Mises, Rothbard and Friedman **zero times** in
449,000 characters, cites Marx sixty times, and argues that capitalism has failed.

Building the corpus as specified would have produced a model steeped in exactly the tradition its
owner's book argues against.

**The fix follows from decisions already made rather than overturning them.** D-9 puts the ethos in
fine-tuning, not pretraining. D-11's deflection set already requires arguing each position in both
directions and scores a one-sided refusal as failure — a model that has read one tradition would
fail our own test.

So: keep the liberal canon, add the labour and political-economy tradition (Henry George, Marx,
Ricardo, Veblen, Proudhon, progressive-era US tax documents — all public domain), and let the SFT
carry Eric's actual positions.

A model that has read both can reason about the disagreement. One that has read either alone is a
partisan that does not know it, which is the failure mode this project exists to avoid.

### D-34 — LOCKED: the corpus contains only material from before generative AI
**2026-09-16, Eric's call: "write up the 'before generative AI' and enshrine that."** Closes O-14.

**Cutoff: 1 January 2022**, before generative AI became widely available.

**The claim we make:** every source was collected or published before 1 January 2022. Dump dates
and publication dates are recorded per source in the ledger.

**The claim we do NOT make:** that the corpus is provably free of machine-generated text. A crawl
date is when a page was fetched, not written. Overstating this would be exactly the unearned claim
`THREAT_MODEL.md` forbids elsewhere, and the precision is what makes it worth saying.

**Why it is a headline property and not a footnote:** no frontier lab can make this claim. They all
trained on post-2022 web data and none can say what fraction is machine-generated. It is a second
structural advantage alongside the ledger, and it costs almost nothing, since the domain canon is
mostly pre-1950 anyway.

**Implementation:** select Common Crawl dumps by date rather than filtering after the fact; filter
Stack Exchange by post date and Wikipedia by revision date; add `published_before` and
`collected_before` to every ledger row; extend `fetch_data.py` to refuse any source lacking a date
basis, exactly as it already refuses one lacking a licence.

### D-33 — Tokenizer: custom BPE, ~32k vocab, digits split individually
**2026-09-16.** Closes O-9. Answers Eric's question, "what gives best reasoning and fewest
hallucinations?" — with the honest caveat that those are two different questions and the tokenizer
only answers one of them.

**Specification:**

| Property | Value | Why |
|---|---|---|
| Vocabulary | ~32,768 | Under the uint16 ceiling (D-7); at 1B params the embedding table is ~7% of the model rather than 39% |
| Digits | **each digit its own token** | The one tokenizer choice with a measurable effect on reasoning |
| Byte-level fallback | yes | No unknown token can ever appear; every input is representable |
| Whitespace | preserved, code-friendly | Indentation is semantic in the code slice |
| Reserved | chat turns and tool calls, from day one | Retrofitting these later would invalidate the corpus |

**On reasoning — digit splitting is the real answer.** A tokenizer that merges "1234" into one or
two tokens forces the model to memorise arithmetic on arbitrary chunks. Splitting every digit gives
a consistent positional representation and measurably improves arithmetic and numerical reasoning.
It costs a few tokens of sequence length on numbers and nothing anywhere else.

**On hallucination — the tokenizer does not help, and claiming otherwise would be dishonest.**
Abstention is a behaviour, learned in fine-tuning from the abstention examples and enforced by the
frozen suite. No vocabulary choice makes a model know what it does not know.

The one indirect contribution: a vocabulary this size leaves ~93% of the parameter budget for the
transformer rather than the embedding table, and capability helps everything downstream including
the ability to learn abstention reliably.

**Why train our own rather than adopt one:** every off-the-shelf candidate is either too large
(Qwen at ~152k), lacks digit splitting, or lacks tool tokens. Training a BPE is an afternoon and is
already implemented in `scripts/train_tokenizer.py`. The cost is giving up logit distillation from a
vocabulary-matched teacher; synthetic-data distillation, the larger lever, is unaffected.

### D-32 — Project Gutenberg is solved: strip the header, the text is public domain
**2026-09-16.** Verified against Project Gutenberg's own permissions page, quoted:

> "you can freely redistribute any eBook, anywhere, any time, with or without the 'Project
> Gutenberg' trademark included."

The distinction that unblocks this: **the texts are public domain; only the "Project Gutenberg"
NAME is trademarked.** PG cannot grant or withhold permission for public-domain work, and says so.

**Method:** take texts from an official mirror, strip the PG header and footer (which carry the
trademark and their licence boilerplate), and what remains is unencumbered public domain. Record
each book's author, title and death-date basis in the ledger individually, so the PD claim rests on
copyright law rather than on anyone's say-so.

Supersedes the CORPUS_PLAN §2b blocker. The Hugging Face mirrors stay unusable — not because the
texts are unclear, but because those repos declare nothing about their own packaging.

### D-31 — Share-alike accepted: weights CC BY-SA 4.0, code Apache 2.0
**2026-09-16, Eric's call.** Closes O-11. His framing: yes, if it means we can build what we truly
want and remain provable.

Wikipedia (CC BY-SA 3.0 + GFDL) and Stack Exchange (CC BY-SA 4.0) stay in the mixture. The weights
are released **CC BY-SA 4.0**, which is one-way compatible with 3.0 material, so adapting 3.0
sources into a 4.0 work is permitted.

**Why this is the right call and not merely the safe one:** it makes the licence question disappear
instead of requiring a defence. Every other open-weights release either avoids share-alike sources
or declines to say. Pagouro can state plainly that it used them and licensed accordingly, which is
one more claim that survives inspection.

**It also serves D-17.** Forks inherit share-alike and must stay open. For a project whose goal is
to spark derivative models rather than to be extended by one company, copyleft is the aligned
choice, not the restrictive one.

Code stays Apache 2.0. The two licences cover different artefacts and do not conflict.

### D-30 — O-7 resolved in principle: run the teacher's open weights, do not call an API
**2026-09-16.** Verified OpenRouter's terms directly. Section 6.1, quoted: *"Your ownership rights
in the Output are set forth in the Model Terms for each Model you use."* Section 5.1 binds the user
to each Model Provider's terms. OpenRouter itself says **nothing** about training on outputs; it
delegates entirely.

That makes the API route permanently murky, because OpenRouter routes a single model to different
upstream providers per request (observed: the same DeepSeek model served by "Wafer" and by
"Relace"). The governing terms could differ call to call, which is unauditable and therefore
unusable for a ledger.

**Resolution: generate synthetic data from open weights run locally or on rented hardware.** The
open-weights licence then governs, with no API provider in the path at all. It is the only version
that can be stated in one sentence and checked by a stranger.

Side benefit: it also removes the congestion problem Eric reported (D-25).

Remaining work: confirm the specific licence of the chosen teacher's open weights before use, and
record it in the ledger like any other source.

### D-29 — Every ablation arm is scored on ONE shared held-out set
**2026-09-16, learned from the pilot.** The M4 pilot scored each arm on a validation slice held out
from *its own* corpus, so arm A was judged on prose and arm B on prose-plus-code. The perplexities
are not comparable, and any difference confounds "did the slice help reasoning" with "is that slice
easier to predict than prose" — where the second effect is almost certainly the larger one.

**Binding for M4:**
1. One shared validation set, drawn from a source used by **no** training arm. Every arm scored on
   identical text.
2. Lead with the frozen suite, not perplexity. It is shared across models by construction, which
   sidesteps the problem entirely. Perplexity is a secondary sanity check.
3. Multiple seeds per arm. At small scale, seed variance can exceed the effect being measured.
4. Pre-register what counts as a real difference before seeing any curve, the way `TARGETS.md` does
   for the suite.
5. **Match arms on TOKEN count, never on bytes or characters.** The pilot matched on characters;
   code tokenizes more densely than prose, so arm B ended up with 6% more tokens from the same
   character budget. Any slice with a different tokenization rate — code, maths, non-English,
   markup — breaks a byte-matched comparison invisibly.

**Why this is worth a decision entry:** the flawed comparison DID produce exactly that. Arm B
scored 0.156 worse on validation loss, which a naive write-up would report as "adding 15% code
raised perplexity by 17%, so code hurts small models." That conclusion is unsupported and entirely
believable. The pilot cost a weekend of CPU and caught two invisible confounds before M4 spends
money on runs where the answer would count. See `docs/ABLATION_PILOT.md`.

### D-28 — Never accept a licence agreement on Eric's behalf
**2026-09-16.** The BigCode family, including The Stack, is gated behind an agreement on the Hub.
An unattended session stopped rather than working around it.

Accepting a licence is a commitment by the account holder, and for this project it also determines
what the corpus ledger has to say. That is Eric's to make, always, no matter how routine the click
looks.

Generalises: gated datasets, terms of service, and anything requiring assent are a hard stop, the
same class as spending money.

### D-26 — `BUILD_LOG.md` is a deliverable, appended every session
**2026-09-16.** A running narrative of the build, written for readers rather than for sessions.
Eric may self-publish it.

**Why it matters more than it looks:** the design conversation concluded that "the build log is the
product" — that a researcher who builds a verifiable open model and documents the whole thing is
doing what researchers usually only write about, and that the log is the most likely path to a real
audience. It is also the natural home for the first-hand measurements nobody else has: what the
rented GPU actually cost, what Arweave actually charged, whether Strix Halo was viable.

**Rules, enforced:**
- **Append only, oldest first.** Never revise an earlier entry; corrections are later entries.
- **The mistakes stay in, especially the AI's own.** A log recording only successes is marketing,
  and the project's entire pitch is that its claims survive inspection.
- **Numbers are measured, not remembered**, and the commit that produced them is in the repo.

Appending is now part of the end-of-session ritual in `CLAUDE.md`, `START_HERE.md` and
`OVERNIGHT.md`.

### D-25 — DeepSeek is the default, not the critical path
**2026-09-16.** Eric reports DeepSeek is heavily congested and "grindingly slow" (two of three top
trending stories on his X feed). This changes nothing structural and blocks nothing today.

**Why it does not bite yet:** nothing in the build depends on DeepSeek. Claude Code is doing the
engineering, and DeepSeek's only assigned job is synthetic SFT data, which is already blocked on
O-7 (teacher licensing). Two smoke calls are its entire use so far.

**Where it would bite:** the SFT stage, once O-7 clears. Generating thousands of examples through a
congested endpoint is a wall-clock problem, not a cost problem.

**Fallbacks, in order,** should congestion persist when that stage arrives:
1. `deepseek/deepseek-v4-flash` — same family, roughly a third the input price, likely less loaded.
2. `nvidia/nemotron-3.5-lightning` — Eric already finds the Nemotrons acceptable (D-4).
3. Run open weights locally for generation. Slower per token but unlimited, unthrottled, and it
   sidesteps O-7 entirely, since the open-weights licence governs rather than an API's terms.

Option 3 deserves attention when O-7 is resolved: it may be both the licence answer and the
congestion answer at once.

### D-24 — The public demo is browser-local, hosted on the Bosgame N95
**2026-09-16.** Eric has an always-on Bosgame E3 Neo (Intel N95, 4 cores, 6W TDP, 16 GB DDR4,
512 GB SSD, Ubuntu) and proposed hosting Pagouro on it as a public website in ONLINE mode, with a
queue when busy. The instinct is right and the mechanism is not. Resolved as follows.

**The N95 is the host. The visitor's browser is the runtime.** The box serves a ~50 KB static page;
weights come from Hugging Face or Arweave; inference runs in the visitor's browser via WebGPU or
the WASM build. This is the design the original design conversation already chose over a hosted
endpoint, and it closes the brief's §14 open question in favour of building it.

**Why not a hosted endpoint, in order of severity:**

1. **It breaks the central claim.** The project promises questions never leave your machine. A
   hosted endpoint means Eric's box sees every prompt in plaintext. Running both a private product
   and a public endpoint that is not private invites exactly the conflation that
   `THREAT_MODEL.md` exists to prevent, among exactly the people who can least afford it.
2. **Abuse and moderation.** An open LLM endpoint under Eric's real name. He becomes responsible
   for what it emits and for what his box retains.
3. **It is the maintained-service obligation the project rejects by construction** (see
   `00_ORIENTATION.md`): uptime, queueing, bandwidth, moderation.
4. **A queue is an anti-demo.** "Wait four minutes to try the offline AI" inverts the pitch.

**Browser-local keeps everything Eric wants and costs none of it:** unlimited concurrent visitors
because each computes on their own hardware, no queue ever, privacy story identical to the stick,
no abuse surface, and nothing breaks if the box goes down.

**The proof point survives and improves.** Not "a tiny box is serving you an AI" but "a 6-watt
fanless box is serving an AI to the entire internet, because the AI runs on your side, not ours."

**Optional flourish with zero abuse surface — the live status page.** Run Pagouro locally on the
N95 and publish its own statistics: uptime, watts, and a live tokens-per-second figure from the box
talking about itself. Nobody prompts it, so there is nothing to moderate. Estimated N95 speed,
memory-bandwidth-bound on single-channel DDR4-3200 with a 1B Q4 model:

| Bound | tok/s |
|---|---|
| Theoretical ceiling | ~25 |
| Realistic, llama.cpp on 4 E-cores | ~16 |

Human reading is roughly 5-8 tok/s equivalent, so it generates faster than a person reads. Measure
this for real once a model exists; it is a headline number.

**Timing:** after release, per Eric ("once we get Pagouro built"). Not a milestone-9 blocker.

### D-23 — Never record a timing number on a busy machine
**2026-09-16, milestone 1.** The box was mining. Training measured 141 tok/s; idle it measured
4,308. A 30x error that looks exactly like a broken toolchain, not a busy one. Published
tokens-per-second is a headline metric, so every timing figure must state that the machine was idle
and be re-measured if it was not. See `ENVIRONMENT.md` Finding 6.

### D-20 — "Generation 0x" — drizzle, do not hammer
**2026-09-16.** Eric has been trying to coin **Generation 0x** since 2017: people born after
Bitcoin's genesis block, 3 January 2009. He would like it woven into the project. His framing:
"a desire but not a demand."

**Where it belongs:**
- The nag text and the manifesto, which is the one place in the product with a voice.
- The README's framing paragraphs.
- The SFT set, so the model itself knows and uses the term. This is the interesting one: a coinage
  spreads by being used, and a model that uses it naturally is a genuine propagation vector.
  Worth a handful of examples, not a theme.
- Newsletter and build-log writing, which is Eric's own voice anyway.

**Where it does not belong:** technical documentation, code comments, variable names, the corpus
ledger, or the threat model. Those documents are load-bearing and must stay plain.

**Why it fits:** "0x" is the hexadecimal prefix, so it carries the technical register honestly
rather than decoratively. And the audience is real: someone born in 2009 is 17 now and has never
known a world without Bitcoin. Pagouro is aimed at people for whom this is ambient reality rather
than a revolution, which is the same idea the term names.

**The failure mode to avoid:** forcing it. Used twice with confidence it reads as a coinage; used
eight times it reads as marketing and undercuts the plain-spoken register the rest of the project
depends on. Drizzle is exactly the right word. If a session cannot place it naturally, leave it out.

### D-19 — Conversation persistence toggle: SAND / STONE
**2026-09-16.** A second prominent toggle controlling whether the chat is written to disk.
Default is **SAND** (nothing saved), matching offline-by-default.

```
  SAND  ·  nothing is saved          <- default
  STONE ·  this chat is saved to disk
```

**Why this wording:** writing in sand versus carving in stone is an ancient, instantly legible
metaphor, unambiguous about direction, short enough for a toggle, and the shoreline imagery sits
naturally beside a hermit crab.

**Rejected:** Jekyll/Hyde (implies the model changes personality, which it does not),
Freebird/Prisoner (nobody can tell which state keeps the data), Incognito (Chrome-owned).

**Binding constraint — the two-toggle problem.** There are now two prominent binary switches. If
both carry metaphorical names users will confuse them, and given `THREAT_MODEL.md` that is a safety
failure, not a usability annoyance. Therefore: the poetic name is the label, the plain words are
the always-visible subtitle, and a single combined status line carries both states where the eye
already goes.

```
  OFFLINE · SAND        (green, calm)
  ONLINE  · STONE       (amber, loud)
```

### D-18 — Milestones live in `MILESTONES.md`; two new ones added
**2026-09-16.** Supersedes `PAGOURO_BRIEF.md` §11.
- **M2, freeze the evaluation suite before any real model exists.** Pre-registration in all but
  name. Free, and it is the difference between a claim and a result.
- **M4, reasoning ablation study.** Test the reasoning-corpus question empirically at ~$30 per run
  rather than guessing. Publish either outcome; a negative result is rarer than a positive one.

---

## LOCKED — product and positioning

### D-17 — The fork kit is a deliverable
**2026-09-16.** The repo is built as a template for tradition-specific models, not only as the
source of one model. Ship a documented recipe: the canon slice, the mixture, the anneal, the SFT
that encodes a worldview, the ledger format.

**Why:** Eric wants forks. Nobody has published a recipe for building a model around a body of
ideas. That template is the thing most likely to spread, and it costs little once the first model
exists.

**Note:** Apache 2.0 permits every fork. A naming clause is the standard tool if the base model's
identity should stay distinct from forks that inherit Eric's name by association.

### D-13 — Threat model is locked; see `THREAT_MODEL.md`
**2026-09-16.** That file governs what the README and the UI may claim. Never claim protection it
does not grant. Binding requirements it imposes:

- No conversation history on disk by default; saving is opt-in with a plain warning.
- The offline audit is the flagship test and must be third-party reproducible in minutes.
- Minimize host footprint; be honest that Windows makes it imperfect.
- Small file size is a **safety property**, not merely convenience.
- Hash verification is a documented one-liner per platform.

### D-14 — The Bitcoin anchor is required, not ceremony
**2026-09-16.** Supersedes the earlier framing of the inscription as an optional flourish.

**Why:** the redistribution case, someone rehosting the zip where people can reach it, is the best
available outcome. It only works if a person downloading from an unknown mirror can verify the
build is untampered. The signed, anchored hash is that check. It is also why the release is a
frozen artifact rather than a maintained project: maintained projects drift, and drift destroys
mirror verifiability.

**Crypto infrastructure rule:** pick each piece on technical merit, disclose every holding fully
and up front, and publish the measurements behind the choice. Cap at **three chains** for three
jobs: permanent storage, timestamp anchor, payment rail. More than three reads as a portfolio tour
and undermines the researcher positioning. Other networks may appear as documented mirrors with
published costs, never as dependencies.

### D-12 — "Speak freely" means the HUMAN speaks freely
**2026-09-16.** Primary meaning: the conversation is local and offline, so a person can ask
anything without it leaving the machine. That is why the property matters.

A secondary, compatible property: the model engages with contested economic and political ideas
rather than deflecting them. Expressed through SFT register, not by removing safety training.

**Do not** pursue "uncensored" or abliterated positioning. That niche is crowded, low-status, and
would permanently undercut the project's credibility. One-way door.

### D-11 — Two-axis evaluation
**2026-09-16.** Publish both, with the test sets and the scripts.

| Axis | Measures | Compared against |
|---|---|---|
| Bluff rate | fabricates facts on unanswerable questions | other small open models |
| Deflection rate | dodges contested questions it has grounds to engage | commercial frontier models |

**Why:** a model with strong views that reliably says it does not know is far more trustworthy than
one that does either alone. Opinionated where it has grounds, silent where it does not. The
side-by-side demo is the pitch.

---

## LOCKED — technical

### D-9 — Reasoning and domain come from different stages
**2026-09-16.** Do **not** load the pretraining mixture with domain text. It costs reasoning and
buys little knowledge.

| What we want | Where it comes from | Where it does not |
|---|---|---|
| Reasoning | general pretraining, heavy on code and math | domain text |
| Domain fluency | modest pretraining slice near 10%, then annealing | SFT alone |
| Ethos, positions, willingness to engage | SFT, a few thousand curated examples | pretraining |
| Verbatim facts and quotations | retrieval packs | any training stage |
| Voice and register | SFT plus the anneal slice | raw corpus share |

### D-10 — The domain corpus is the canon, not the forum
**2026-09-16.** The substance is the written tradition, which is overwhelmingly public domain:
Gutenberg for Smith, Ricardo, Bastiat, Mill, Locke, Hume and Tocqueville; the Austrian corpus where
openly licensed, verified per work; founding documents; Bitcoin Core and major chain source via The
Stack; and public-domain economic data from Treasury, the Fed and BLS.

Bitcointalk is **contemporary voice**, used in the anneal and the SFT. It is not the spine.

**Why:** this reframes the project from a crypto-forum model into one that has read the lineage the
crypto ethos descends from. Far more defensible, and license-clean.

**Whitepapers:** most are copyrighted with no license permitting redistribution or training. They
belong in **retrieval packs**, not in the training corpus.

### D-8 — Build on existing open corpora; do not assemble from raw sources
**2026-09-16.** Use Dolma (roughly 3T tokens), FineWeb-Edu (roughly 1.3T), and The Stack as the
base. They are already deduplicated, cleaned and license-documented; the ledger cites them and
stays honest.

**Why:** collapses milestone 2 from months of scraping and MinHash work into weeks of curation and
mixture design. Milestone 2 was the single biggest risk to this project ever finishing.

### D-7 — Tokenizer vocabulary must be under 65,536
**2026-09-16.** Rejects the brief's Qwen default of roughly 152,000.

Two independent reasons:

1. **Embedding budget.** At a 1B target a 152k table is a large share of the model; at 300M it was
   over half. Small models that work use vocabularies near 49k for exactly this reason.
2. **Storage and bandwidth.** Under 65,536, tokenized data stores as 16-bit rather than 32-bit
   integers. At 100B tokens that is roughly 200 GB instead of 400 GB, and it halves data-loader
   bandwidth on every epoch.

**Cost:** gives up logit distillation from a large-vocab teacher. Synthetic-data distillation, the
bigger lever, is unaffected. Tool-call tokens must be present either way.

### D-6 — Model size is roughly 1B; the product sets the ceiling
**2026-09-16.** Supersedes the brief's 300M default and its 300M-versus-1B open question.

**Why:** the promises cap the size before money does. It must fit a cheap stick, load on an old
laptop, and answer at conversational speed on CPU. 1B at 4-bit is roughly 700 MB. At 3B, near
1.8 GB, CPU generation gets slow. At 7B the double-click demo stops being impressive.

Budget shape. These are floors; expect 1.5x to 2x on a first run.

| Target | Params | Tokens | H100-hours | Rough cost |
|---|---|---|---|---|
| Brief's original plan | 300M | 10B | 12 | $30 |
| **Chosen** | **1B** | **~100B** | **~420** | **~$850** |
| Rejected as over budget | 3B | 300B | 3,800 | $7,600 |

**Spend the budget on tokens and on an excellent SFT set, not on parameters.**

**Calibration to keep in view:** the small models people actually use were trained on 11T to 18T
tokens. At 100B we are roughly 100x undertrained for our size and will not win on general
capability at any budget Eric would spend. That is expected and fine. The differentiator is
structural: the big labs cannot publish a complete licensed corpus ledger because they cannot
disclose their data that way. That gap does not close as their models improve.

---

## LOCKED — sources and rights

### D-16 — No Reddit. Ever.
**2026-09-16.** Eric: "Absolutely do not train on Reddit." The terms prohibit it and the API is
paid.

### D-15 — Eric's own writing
**2026-09-16.**

- **The book:** include only under narrow **written** permission covering inclusion in a documented
  training corpus and derivation of Q&A, with attribution in the public ledger. Do not ask for
  verbatim retrieval redistribution; that is a much larger grant and is not needed. Store the
  permission document in the repo. It is exactly the kind of receipt this project runs on.
- **Reality check:** a book is roughly 130,000 tokens. At any realistic corpus size it has no
  measurable effect through pretraining alone. Its real presence comes from SFT examples derived
  from it and from the anneal slice. Do not compensate by repeating it; that causes memorization
  and degrades the model.
- **The Crypto Capital newsletters:** **excluded** absent written permission from the company that
  owns them. Eight years is small in token terms. Including them without clear rights would trade
  the entire provenance claim for a rounding error. Not close.

---

## LOCKED — session infrastructure

### D-5 — GitHub account is `ericrwade`
**2026-09-16.** Work email removed by Eric. Git identity set globally to the noreply address
`266440753+ericrwade@users.noreply.github.com`, so no real address enters commit history.

### D-4 — Default working model is `deepseek/deepseek-v4.1-flash`
**2026-09-16.** Eric's pick from direct experience. Set as `OPENROUTER_DEFAULT_MODEL`.

| Role | Slug | $/Mtok in | $/Mtok out |
|---|---|---|---|
| **Default** | `deepseek/deepseek-v4.1-flash` | 0.300 | 1.200 |
| Cheap bulk | `deepseek/deepseek-v4-flash` | 0.089 | 0.177 |
| Acceptable alternate | `nvidia/nemotron-3.5-lightning` | 0.080 | 0.200 |
| Escalation only | `openai/gpt-6-astra` | 10.000 | 50.000 |

Astra is announced before use, never habitual. **Note:** using any of these to generate *training*
data is gated on O-7.

### D-3 — Secrets never enter the transcript or the repo
**2026-09-16.** Keys live in `.env`, gitignored. Verify by use, never by printing. Every key carries
a credit cap. Learned the hard way: a masking script whose fallback branch printed unmatched lines
leaked most of a key. Extract secrets with a positive pattern only, and never print unmatched
content.

### D-2a — This file supersedes the brief where they conflict
**2026-09-16.** The brief remains the origin document and governs anything not addressed here. But
D-6 through D-17 were decided with Eric after it was written, and several contradict it directly on
size, tokenizer, corpus strategy and stage design. A session must not "correct" a decision here back
to the stale brief.

### D-2 — `PAGOURO_BRIEF.md` is the origin document
Read it every session. See D-2a for precedence.

### D-1 — Project home is `C:\Users\Eric Wade\PAGOURO_BUILD`
"Pagouro", "Paguro", and "our LLM project" all mean this folder. Written spelling is **PAGOURO**.

### D-45 — Tutor grading crashed silently on a llama-cli console truncation
**2026-09-16, session 2.** Building the tutor shell (D-43), every grading call returned PARTIAL
with the model's ASCII-art loading banner as the "answer" -- a silent, wrong result, not a crash,
which is worse.

**Root cause, found by diffing raw output byte-for-byte:** `llama-cli`'s interactive console
truncates its own echo of a long prompt and appends the literal text `(truncated)`. It does not
truncate what is actually sent to the model -- the real response was coherent throughout -- only
its own display of the input. Our multi-line ~500-character grading prompt exceeded whatever
internal display limit triggers this; `evals/run_eval.py`'s short, single-line eval prompts never
had. `txt.rfind(prompt)` then found no match and fell through to returning the entire raw
output, banner included, as if it were the model's answer.

A first attempted fix (normalizing CRLF-vs-LF line endings, since `llama-cli` echoes with CRLF)
was real and necessary but insufficient -- it didn't address the truncation at all, and the bug
persisted identically after that fix, which is itself a lesson: a plausible-looking fix that does
not change the failure it targets has diagnosed the wrong cause.

**Fix:** when `(truncated)` appears in the output, treat everything after its last occurrence as
the model's real response, since that literal string only ever appears where the console cut the
prompt off. Verified against the exact prompt that failed.

**Also fixed in the same pass:** Windows consoles default to cp1252 and cannot display many
characters a model may legitimately emit (curly quotes, em dashes). `tutor.py` and `run_eval.py`
both reconfigure stdout to UTF-8 with a safe fallback, so a display limitation can never crash a
live session again.

### D-46 — Real pretrain OOM'd at seq_len=1024/batch=12; config reduced, pipeline hardened with fail-fast checks
**2026-09-16, session 2.** The first real pretrain run was killed by the OS ("system is running low
on memory") around step 80 of a planned 3000. `master_pipeline.sh` had no `set -e`, so every
downstream stage ran anyway against missing files and silently produced a "complete"-looking
package -- llama-cli.exe, DLLs, docs, a working `PAGOURO.bat` -- with no model file inside it, and
copied that broken package over the USB drive. Caught only because the assembled state was
inspected before trusting the "PIPELINE COMPLETE" line; the USB briefly held a launcher that would
have crashed on the first double-click.

**Root cause, isolated by bisecting on seq_len alone with everything else held fixed:** not a
memory leak. At `dim=512, layers=14, heads=8, vocab=32768, seq_len=1024, batch=12`, the
non-checkpointed backward pass must retain all 14 layers' attention score matrices plus a
32768-wide logits tensor simultaneously; measured peak was 13GB+ and still climbing when killed at
~10-15 steps in isolation. The identical loop at `seq_len=256` stayed flat around 2GB over 80
steps with zero growth trend -- confirming the memory scales with seq_len² (attention) rather than
leaking per-step, since a true leak would have shown growth at the small seq_len too, just slower.

**Fix:** `seq_len` 1024 -> 512, `batch_size` 12 -> 8 for both the pretrain and anneal stages,
verified stable (flat ~2.6-2.8GB RSS, no growth trend) over a 120-step isolated run before
relaunching the real pipeline. Step counts scaled up (pretrain 3000 -> 9000, anneal +350 -> +1050)
to cover the same total token budget the original plan did, since throughput measured about the
same either way (~880-1000 tok/s) -- this model's cost at this size is not attention-dominated, so
the fix traded peak memory for step count at roughly no wall-clock cost, not a speed-for-safety
compromise. `master_pipeline.sh` also got `set -e` and an explicit `require <file>` check after
every stage that produces a file a later stage depends on, so a future failure anywhere in the
chain halts the run instead of cascading through fake success.

**Also worth naming:** immediately after relaunch, `Get-CimInstance Win32_Process` showed what
looked like two concurrent training processes on identical command lines -- alarming, since two
writers on the same checkpoint file would corrupt it. Investigation showed this is normal: the
venv's `python.exe` is a launcher shim (0 CPU, 0 RSS, 1 thread) that re-execs the base Python 3.12
interpreter as its actual child (all the CPU, all the memory, 45 threads). Worth a false-alarm
entry precisely because the failure mode it would have caused -- silent checkpoint corruption --
is the same *class* of danger as this entry's main bug, and the check that ruled it out (comparing
CPU-seconds and RSS between the two PIDs, not just seeing two PIDs) is the reusable lesson.

### D-47 — The PC hard-froze mid-pretrain; resume from checkpoint, never from zero
**2026-09-17.** The overnight real build (D-46 config) was in stage 4 when the machine stopped
responding at about 4:35 AM: last training log line at step 6140 of 9000 (04:34:43), last
checkpoint at step 5999 (04:24:50, val loss 2.949, perplexity 19.1). Eric found the box frozen
18 hours later and had to unplug it and disconnect the drives to get it back. Windows logged
Kernel-Power 41 on the way back up and nothing at all in the hours before: no hardware error, no
memory-exhaustion warning, no crash dump. The Python process was at 5.6 GB of 32 GB when last
checked. Cause unknown. Two facts recorded so the next session does not start from scratch on
this: the same machine bugchecked (0x139, kernel security check failure) on 2026-09-15 at
midnight, before this project touched it, while the Midstate miner was running; and both crashes
happened under sustained all-core load. That is a pattern, not a diagnosis.

**Decisions:**

1. **Resume, do not restart.** The step-5999 checkpoint loaded cleanly (129 tensors, all finite,
   optimizer state intact) and was backed up to `checkpoints/real_pretrain.step5999.bak.pt`
   before anything else was done. Resumed with `--resume`; step 6000 logged loss 3.963 against
   3.965 at step 5980 before the freeze, which is the D-22 proof applied for real. About 140
   steps, ten minutes, were lost.
2. **`master_pipeline.sh` gained `RESUME_PRETRAIN=1`.** Without it stage 4 begins with
   `rm -f checkpoints/real_pretrain.pt` -- a relaunch by habit would have deleted seven hours of
   training. The flag skips the wipe, trims the run log to the checkpoint's step so resumed steps
   are not logged twice, and passes `--resume`. Recorded in the project memory as a hard warning.
3. **Checkpoint saves are now atomic.** `train.py` writes to `<ckpt>.tmp` and `os.replace`s it
   over the old file. `torch.save` straight onto the path truncates it first, so a freeze during a
   save would have destroyed the only checkpoint of the run. This one landed ten minutes after a
   save. Luck is not a mechanism.
4. **`THREADS` is a pipeline variable, resumed at 12 of 16 cores** for thermal headroom, at
   roughly a 20% throughput cost on a box that has now crashed twice under full load. The SFT
   script has no thread control and will run at torch's default; it is a short stage.
5. **Power plan set to High Performance**, sleep and disk timeouts off. The only "idle" theory
   that survives the evidence is a device power transition, and this closes it at no cost. USB
   selective suspend does not exist on this machine's plan.
6. **Not done, on purpose:** the Midstate miner stays off during training (Eric proposed running
   it on one thread to keep the box "always working"; the freeze happened under load, so keeping
   the box busy does not address it, and one thread of solo PoW earns nothing while adding heat).
   A firmware check and a memory test are recommended before the next unattended overnight run.

**Also this session: a third SFT seed class.** Eric asked whether a model trained not to bluff
would become "a glorified search engine" that chokes on a question like "was George Washington
more like a king or a prime minister?" Inspection of `sft/abstention_seed.jsonl` showed the risk
was real on the training side: it is correctly balanced 50/49 between abstain and confident, but
every confident example is a definition. Nothing asks the model to compare, weigh or compose,
which is precisely the kind of question the no-bluff training could teach it to hedge on (D-27,
T-5). `sft/build_synthesis_seed.py` adds 37 synthesis examples (comparisons and judgements
answered plainly, two to four sentences, position taken) and 6 mixed examples that pair a real
thing with an invented one and answer the real half while declining the invented half, so the
learned behaviour is discrimination between the two rather than a topic reflex. Overlap-checked
against the frozen evals (highest Jaccard 0.20, none at or above 0.60). `train_sft.py` loads it;
the loader was tested against the real tokenizer (172 pairs, max 125 tokens) before the running
pipeline could reach stage 6.

### O-12 proposal — context 8k, reached by training at 4k and extending during the anneal
**2026-09-17, proposed, not closed.** Eric asked whether the amount of user input the model can
hold is ours to control, and whether quality drops if it is too large or satisfaction drops if it
is too small. Both are real: cost scales with the square of the window (D-46 measured it), small
models use the middle of a long window poorly, and CPU inference reads every context token before
the first word; but a window under ~4k produces visible "you forgot what I said" failures and
leaves no room for a retrieval passage (D-9). Proposal: pretrain at 4k, extend to 8k in the anneal
(the standard progressive-extension recipe; avoids the post-training stretch O-12 already warns
is degraded), and cap what the app sends to ~4k of recent conversation plus retrieval by default,
with a user override. The shakedown model in the current run has a 512-token window, which is
fine for a pipeline test and not a product number. Eric owns the call.

### D-48 — The first real build completed end to end; two bugs in the tail, one of them retroactive
**2026-09-17, evening.** The resumed pipeline (D-47) ran pretrain to step 9000 (best val loss
2.6845, perplexity 14.7) and anneal to 10050 (domain-set perplexity 114 -> 84.7 best, 92.6
final), then halted at stage 7 with `verify_gguf.py` reporting FAIL. Diagnosis found two
independent bugs, both fixed, and one finding about the anneal.

**Bug 1, harness: `verify_gguf.py` never passed `-no-cnv`.** Once `export_gguf.py` began embedding
a chat template in the GGUF, `llama-completion` silently enabled conversation mode and wrapped the
prompt (15 tokens where the raw prompt is 7), so PyTorch and llama.cpp were continuing different
sequences. The export was correct all along: re-run with `-no-cnv`, the anneal checkpoint matched
84/84 characters and the SFT checkpoint 102/102. A FAIL from this script must now be read as
"one of the two engines got a different prompt" before "the RoPE permutation is wrong."

**Bug 2, real: `train_sft.py` never shifted its targets.** `build_example_ids` returned `ids` and
`labels` position-aligned, and the model's loss compares the prediction at position i with
`targets[i]`. So SFT trained the model to emit the token it had just read. Symptoms, in order of
how they were noticed: SFT loss fell to 0.0009 (the identity function is easy); the raw-prompt
greedy continuation was `" is is is is ..."`; every chat-format probe, including on examples in
the training set, returned only newlines. `train.py`'s own docstring warns about exactly this and
its loader shifts; the SFT script was written separately and did not. Fix: return
`ids[:-1], labels[1:]`; verified that every supervised label equals the following input token
and that the untouched anneal checkpoint scores a sane 5.24 on the corrected objective before
rerunning. **Retroactive consequence:** every SFT checkpoint this script produced before today
carried the defect. The `pagouro-m1` row in `evals/BASELINES.md` (100% incoherent, 0% answered),
attributed on 2026-09-16 to the model being small, was this bug. D-45's tutor grading ran on a
model that could only echo.

**Corrected SFT, measured.** 1200 steps, batch 4, lr 2e-5, 172 examples (99 abstention seed,
30 crypto synthetic, 43 synthesis seed): loss 5.2 -> 2.98 (step 200) -> 1.15 (600) -> 0.50
(1000) -> 0.18 (1199). Chat-format probe: training-set questions reproduced verbatim
(memorised, 28 passes over 172 items); novel invented-entity question refused with the right
register; novel real questions produce fluent register with no content. Frozen suite, q8_0
GGUF: bluff 3.3%, abstained on fake 87%, **answered real 3.3%, over-abstained 53%**, deflect
50%, incoherent 14%. **This model is a hedger**, target T-5's failure mode, as D-27 predicted for
abstention training on a model with no knowledge to answer from. At 59M parameters and 37M
pretraining tokens (0.6 per parameter) the model learned the abstention reflex and the answering
register but has nothing to answer with, so refusing is its safe default. This is the expected
result of a shakedown model and not evidence about the D-6 build; the real build's 100 tokens per
parameter is what fills the gap. The 50% deflection is the same absence of knowledge scored on a
different set.

**Finding, anneal schedule.** Anneal training loss was flat (window means 4.66, 4.67, 4.31, 4.64
over 200-step windows) at lr ~3.2e-5, because pretrain's cosine had already decayed to the floor
by step 9000 and the anneal reuses the same schedule with `--max-steps 10050`, so it runs the
whole way at the minimum. The 25% domain-perplexity improvement came slowly at a rate that barely
moves weights. For the real build, use a warmup-stable-decay schedule: hold the learning rate
through pretraining and make the decay itself the anneal, on the domain-heavy mix. That is the
standard recipe and the reason it is standard is visible in this run's flat line.

**Also:** `master_pipeline.sh` gained `START_STAGE=N` so a run can resume at SFT or export without
retraining, which is how the tail was rerun after the fixes (`START_STAGE=6`). Stages 8-11 then
completed: offline audit PASS, package assembled, copied to the 29 GB USB, and one chat turn run
from the stick as the final check (q8_0, 905 tok/s generation on the EVO-X2). The pipeline's
"COMPLETE" line was not trusted; the USB was listed and the model was run from it.

**Thermal note for D-47:** the whole resumed run, roughly 5.5 hours at 12 threads, completed
without incident. That is one data point, not a diagnosis; the reboot-based memory test and the
newer AMD graphics driver (GMKtec, dated 2026-08-05; installed driver is from 2025-05) remain on
the list. The user-space memory test (9 GB, 3 passes, 5 patterns) found zero errors and no WHEA
hardware error has ever been logged on this machine.

### D-49 — The context gauge: the window's fill level is always visible, and turns are seen leaving
**2026-09-17, Eric.** Since the chat survives a full window by dropping the oldest turns
(context shift, enabled in the launcher the same day), the user must be able to see that this is
happening. A visible gauge, a tube or thermometer, shows how full the context window is; as it
fills, the fill rises; when the window is full, a new block visibly enters at one end and an old
block pops out of the other and dissipates. Nothing about "the model forgot what you said" should
ever be a surprise.

**Why:** two of the product's defining claims are transparency and "it doesn't bluff." A model
that silently forgets the first half of a conversation and then answers as if it remembered is
bluffing by omission, and the user cannot tell. The gauge makes the limit legible and turns a
small-model weakness into a visible, honest mechanic.

**Design notes for whoever builds the app (ledger D1 is NOT STARTED; llama-cli cannot do this):**
- The gauge shows what is in the window, not just how much: system prompt, any retrieved
  passage or pasted document, and conversation, as distinct segments. The user then understands
  why pasting a page filled it.
- Token counts come from the harness, which tokenizes everything it sends; no estimate needed.
  llama.cpp's server reports prompt token counts per request.
- The block leaving should carry a hint of its content (the first few words), so the user knows
  what was dropped and can re-paste it if it mattered.
- A STONE session (D-19) can offer "the dropped turns are still in the saved transcript"; a SAND
  session says plainly that they are gone.
- The same gauge is where a future retrieval pack shows "3 passages loaded from the survival
  pack," so the user sees retrieval happening (origin line 88's "label in the chat when a search
  actually happened" is the same principle).

### D-50 — No-bluff does not mean no-answer; what the model says when it can't, and what the marketing may say
**2026-09-17.** Eric's question, verbatim in spirit: if it cannot bluff and cannot hallucinate,
will it decline so much that it is unusable? Should there be a bank of ready-made "I don't know,
try a web search" responses? Should the marketing say it is 1/1000th the size, will not
hallucinate, and will therefore seem not to answer much? Should there be small, big and massive
versions?

**The measured fact first.** The 59M shakedown model IS the unusable hedger: it declined 87% of
the invented questions and answered 3.3% of the real ones (D-48). But the refusal rate is set by
what the model knows, not by the no-bluff rule. Frontier models on the same test answer 97% of
real questions and still bluff on 23–27% of fake ones; small open models answer 87–93% and bluff
on 50–57%. The rule does not lower the answer rate; missing knowledge does. A 1B model trained on
100B tokens will know vastly more than this one, and the two-axis eval (D-11, T-5) exists so that
the answered-real rate is published next to the bluff rate every time. **A model that answers
under ~80% of the calibration set does not ship**, whatever its bluff rate; that number is now a
release gate in the ledger (E1).

**Canned responses: a few in the harness, none in the model.**
- The model's abstentions are LEARNED, with deliberately varied wording (`build_abstention_seed.py`
  rule 3: identical refusal phrasing teaches a tic, not a behaviour). A bank of a thousand strings
  would undo that and make every refusal sound like an error message.
- The HARNESS, which knows the mode, the date and whether packs are loaded, owns a small set of
  fixed notices that the model cannot know to give: "Offline; I can't check anything after
  [training cutoff]. Switch to ONLINE to search." / "Nothing in the loaded packs covers this." /
  "That's outside what I was trained on." These are templates because they are facts about the
  system's state, not judgements. Origin line 88 already puts mode and date in the system prompt
  for exactly this reason. Count: a dozen, not a hundred.
- For current events specifically, the answer is architectural: ONLINE mode with search (ledger
  D2) is how the model gets today's facts; OFFLINE, the harness notice fires before the model is
  even asked, because the harness can detect "this needs the present" more reliably than a 1B
  model can.

**Marketing language, binding on README, manifesto and any post:**
- Never write "will not hallucinate" or "cannot hallucinate." No language model can promise that,
  and the project's own threat-model rule (never claim protection the system does not grant)
  applies to capability claims too. An overclaim here is the one thing that would let a reviewer
  demonstrate the pitch is false in thirty seconds.
- Say what is measured: "Asked N questions about things that do not exist, it invented an answer
  X% of the time. [Model A] did Y%, [Model B] did Z%. Here is the test; run it yourself." And
  always beside it: "Asked N questions it should be able to answer, it answered W%."
- Say the size plainly and turn it into the pitch, not an apology: it is roughly 1/1000th the
  size of the big models; it knows less; it will tell you when it doesn't know instead of making
  something up; it fits on a stick and never sends a word anywhere. The comparison to make is not
  "as smart as" but "the one that shows its sources and admits what it doesn't know."
- Under-promise in print (origin 222). If a sentence would embarrass the project when a reviewer
  runs the test, cut it.

**Small, big, massive:** answered as Baby/Mama/Papa earlier the same day and unchanged. Two
tiers: **Pagouro Flash** (~150M, dev model, runs on anything) and **Pagouro** (1B, the product,
D-6). A 3B "massive" tier costs roughly 9x, breaks the stick-and-old-laptop promise, and is still
100x undertrained against Qwen/SmolLM at its size, so it buys neither the product story nor a
capability win. Not unless the project is funded (D-6's rejection stands). Same scripts, different
`--dim`/`--layers`; the cost is entirely tokens.

### D-49 addendum — reference implementation for the gauge
**2026-09-17, Eric.** Hermes Agent's CLI shows context fill as a row of ASCII boxes (about ten)
that change colour one at a time as the window fills, green to yellow. That is the right
minimum: it works in a plain console, needs no graphics, and reads at a glance. The D-49 design
(segments, the dropping block with its first words) is the full version for the app; the
ten-box row is the version the console launcher can have as soon as the launcher is a harness
process rather than bare `llama-cli` (see D-51). Red for the last box; the block that leaves is a
box that empties from the left.

### D-51 — An agent on the stick: yes, as v1.1, tool-assisted before autonomous, and sandboxed
**2026-09-17.** Eric: the industry's attention is on agents; a tool-powered autonomous agent
living on a USB stick would be remarkable; is it possible? The origin conversation (line 78)
already made tool use the "north star" and set the size to ~1B partly for it (D-6). This entry
turns that into a plan and a set of constraints.

**Possible: yes.** Everything an agent needs fits on the stick beside the model: `llama-server`
(already in the llama.cpp bundle), a small harness process that runs the loop (ask the model,
parse a tool call, run the tool, feed the result back, repeat), and the tools themselves, which
for an offline stick are local: a calculator, date/time, search over the retrieval packs, read a
file the user points at, write a note to a workspace folder, and, in ONLINE mode, web search and
fetch. None of that needs a GPU or a network. The stick becomes the agent's home in the same way
it is the model's, which is the hermit-crab metaphor doing more work.

**Capability, honestly.** Tool use is a format plus judgement. The FORMAT (emit a valid call with
the right arguments) is learnable by a 1B model and is made unbreakable by llama.cpp's
grammar-constrained decoding: every call is syntactically valid by construction. The JUDGEMENT
(when to call, which tool, chaining steps, noticing a bad result and recovering) is where small
models are weak; the industry's small agentic models (Qwen 1.5B, SmolLM2 1.7B, Phi) do one- and
two-step tool chains reliably and fall apart on long plans. At 1B, expect a competent assistant
with a checklist, not an autonomous operator: "search the survival pack for water purification,
compute the dose for 20 litres with the calculator, cite the passage" is a realistic two-tool
chain; "reorganise my documents folder" is not. Write the harness to compensate for the model,
never to trust it (origin 78): constrained decoding, one tool per turn, results shown to the user,
and a step budget.

**Order of work.** The chat model comes first; the agent is a layer over it. The one decision that
must be made NOW so the agent is cheap later: **the app is a harness process talking to
`llama-server`, not a `.bat` around `llama-cli`.** That single architecture choice is what makes
the context gauge (D-49), ONLINE/OFFLINE with search (ledger D2), SAND/STONE (D-19), retrieval
packs (D6) and tools one codebase. Then, for the agent: (1) tool-turn examples in SFT, synthesised
with the DeepSeek open-weights teacher (D-30) as question -> call -> actually executed result ->
answer, including failures (ledger C11); (2) a tool-use axis in the frozen eval, scored the same
two-sided way as bluffing: did it call when it should, did it refrain when it shouldn't, did it
say "I can't do that with the tools I have" instead of pretending; (3) the sandbox below.

**The sandbox is not optional, and it changes the promise.** A chat model on a stick can only
say things. An agent can DO things on a stranger's computer, and `THREAT_MODEL.md` is binding
here: an agent that writes to the host disk breaks "nothing you type is saved" unless the user
turned that on. Constraints: tools are an explicit allowlist, never a shell; file access is
confined to the stick's own workspace folder plus paths the user names in that session; nothing
outside the workspace is deleted or overwritten, ever; the READ-ONLY / CAN ACT state is a third
top-of-screen toggle beside ONLINE/OFFLINE and SAND/STONE, defaulting to READ-ONLY; every tool
call is printed before it runs and the result after; a step budget per request. The name of the
third toggle is open; the behaviour is not.

**Why this fits the pitch instead of diluting it.** A model that does not bluff and an agent that
does not overreach are the same property: knowing the edge of what it can do and saying so. A
small agent that says "I don't have a tool for that" and "that passage doesn't answer it" is
rarer and more useful than a large one that improvises. And it is the direct, open, offline
version of what the calibrated-decision labs (Jev) are selling hosted (origin 205).

**Not in v1.0.** The 1B chat model ships first with the harness architecture in place. The agent
is v1.1, or a pack, or a fork; the origin's "finished artifact, no maintenance promise" stance
(ledger F12) means it must be either in the release or explicitly not, never "coming."

### D-52 — Agent and tools are in v1.0 as an MVP framework; the origin transcript stays private; share the machine
**2026-09-17, late, Eric.** Three rulings before a six-hour unattended window.

1. **Agent and tools from day one.** Amends D-51's "v1.1": the tool loop, the sandbox and the
   READ-ONLY / CAN ACT toggle ship in v1.0. The stance that makes this honest at 1B: Pagouro is
   an **MVP framework**, a working minimum that someone with (a) time, (b) skills or (c) money
   can make bigger and better. The framework has to be complete and documented; the model's
   judgement inside it will be what a 1B model's judgement is, and the README says so. Same
   stance the origin conversation took on the whole artifact.

2. **The origin transcript is NOT shared.** `My_Claude_Conversation.txt` is gitignored and stays
   local. `docs/ORIGIN.md` (about 200 words, sterilised) is the public origin story. The ledger
   (`docs/ORIGIN_LEDGER.md`) still cites the private transcript's line numbers; that is fine for
   Eric and for sessions on this machine, and the ledger itself contains no quoted material
   beyond the commitments.

3. **Share the PC.** This machine also runs Summer Engine (local, CPU and GPU) and Codex (cloud)
   building a video game. Before any heavy job: check the CPU load and whether `Summer.exe` is
   busy; cap training at `THREADS=8` overnight (`THREADS=12` was measured faster than 16, so 8 is
   a real but tolerable cost); never stop or throttle the other tools' processes. Written into
   `CLAUDE.md`. The Midstate miner stays off while training (D-47).

**Architecture consequence (from D-51, now binding):** the app on the stick is a harness process
over `llama-server`, packaged as a single executable so the host needs nothing installed. The
harness owns the context (so the gauge is truthful), the toggles, the tools, the packs and the
step budget. `llama-cli` is no longer the product.

### D-53 — Overnight 2026-09-18: the app exists, and what the shakedown model does inside it
**2026-09-18, 00:45.** Built during Eric's six-hour window, per D-52 ("build in agent & tools from
day one"). Measured, not remembered.

**Shipped on the stick (`D:\Pagouro`, 229 MB, 51 files hashed):** `pagouro.exe` (8 MB,
PyInstaller, standard library only) starts `llama-server.exe` beside it and owns the session:
three switches above every prompt ([OFFLINE] [SAND/STONE] [READ-ONLY/CAN ACT]), the ten-box
context gauge with dropped turns shown leaving (D-49), five allowlisted tools (`calc`, `time`,
`pack_search`, `read_file`, `write_note`) chosen by the model under a hand-written GBNF grammar
that permits exactly `{"tool":"<name>","arguments":"<string>"}` and nothing else, one tool per
turn, results printed before the answer, writes confined to `workspace/` and refused in
READ-ONLY, an exit line that lists every file written. `packs/` holds Economic Sophisms and On
Liberty. `PAGOURO-BASIC.bat` keeps the bare `llama-cli` chat as a fallback.

**What the model learned (59M, SFT on 306 conversations, loss 5.28 -> 0.57):** the FORMAT. On
sixteen held-out phrasings the router chose the right tool 12 times; the four misses were
`none`/`calc` confusions and one `read_file` -> `none`. Under the system prompt it answers
memorised questions verbatim, refuses invented entities in the right register, and says
"nothing in the packs" when the search returns NO_MATCH. What it did not learn is content: it
cannot reliably copy "102" out of a tool result (digits are single tokens; 37M training tokens),
its tool ARGUMENTS were unusable ("packs the Bitcoin wallet's transactions" for "bring the
charger"), and multi-turn answers degrade into loops.

**Harness compensates, per the origin (line 78: "write the harness to compensate for the
model, not to trust it"):** when the model's argument is unusable the harness recovers it from
the user's own words with visible regexes (the arithmetic in the sentence, the note text after
the colon, a path-looking token, the query words). With that, every tool call in the final stick
run did the right thing even though the model's arguments were wrong. This is the MVP-framework
stance made concrete: the judgement is the model's; the reliability is the framework's.

**Frozen suite, this model:** bluff 10.0%, abstained-on-fake 80%, answered-real 6.7%,
over-abstained 30%, deflect 82%, incoherent 4%. Against the previous SFT (3.3 / 87 / 3.3 / 53 /
50 / 14): less over-abstention and less incoherence, more bluffing and more deflection. All of
it is inside the noise of a model this size; none of it is evidence about the 1B build. The
release gate from D-50 (answered-real >= ~80%) is nowhere near, as expected.

**Bugs found and fixed on the way:** the app's exit line said "nothing was written to disk"
after a note had been written in CAN ACT (now lists every path); the dropped-turn label could
quote an assistant turn; the JSON-schema router let the model spend its whole budget on
whitespace (replaced by the GBNF grammar); the Windows console's legacy code page could not
print the gauge (UTF-8 forced, ASCII fallback); the packager's app block silently failed to
apply on the first pass and the pipeline shipped the old layout, caught by listing the stick.

**Provenance catch:** the only Gutenberg edition of Bastiat's *The Law* is a 2007 Mises
Institute translation under an unspecified Creative Commons licence. Not used in the packs;
O-14 opened on its presence in the training corpus.

**Cousin rule kept:** Summer Engine was idle (<3% load) at every check; training ran at 8 threads.

### D-54 — RunPod is the rental provider; connected via the official plugin; spend rule restated
**2026-09-18, Eric.** Eric created a RunPod account and connected it to this session through the
official Claude Code plugin (`runpod@runpod`, hosted MCP, OAuth; no API key stored anywhere).
Verified from live reads: 0 pods, $0 billed in the last 7 days. io.net's Training-as-a-Service was
evaluated and rejected: its docs state it does not support training from scratch (fine-tuning of
existing models via a web form only), which rules it out for a from-scratch model by definition.

**Live secure-cloud prices at connection time (per GPU-hour):** H100 SXM $3.49 (community
$2.69), H100 PCIe $2.89, A100 80GB $1.59, H200 $4.59, RTX PRO 6000 Blackwell 96 GB $2.09. D-6's
~420 H100-hours therefore costs roughly $1,470 secure / $1,130 community, above the brief's $850
floor, as D-6 itself warned (1.5-2x on a first run). The job bundle (ledger C3) quotes from live
reads, not from memory.

**Rule, unchanged from the origin and now enforceable:** the session never creates a billable
resource (pod, volume, endpoint, cluster) without an explicit instruction from Eric naming the
run; the prefunded balance is the hard cap; the hourly price is stated before anything billable
is created; every resource the session creates is destroyed by the session when the run ends and
the checkpoint is safely downloaded. The permission layer additionally gates these calls.

**Not before:** a GPU run waits for (1) the SFT set to reach thousands of conversations
(generation running as of this entry), (2) the anneal schedule fix from D-48 (WSD), and (3) O-12
(context length) decided. Renting an H100 to reproduce a known over-abstention would be the
expensive way to learn what is already measured.

### D-55 — First rented-GPU run: the bundle works end to end; measured throughput reprices the 1B run
**2026-09-18, 11:10–11:20 PT.** Pod `r2a7pzu02e9sd3`, NVIDIA A40 48 GB, secure cloud, CA-MTL-1,
$0.49/h, official `runpod/pytorch` image, created and terminated by the session; total pod life
about nine minutes (~$0.08 plus pennies of disk). RTX 4090 and RTX A5000 were listed as LOW
stock and were gone by the time the create call landed; the A40 was there. `list-pods` empty at
the end.

**What was proven:** `scripts/runpod/make_bundle.sh` (391 MB: code, tokenizer, tokenized data,
no checkpoints/corpus/secrets) → `scp` over the pod's direct SSH (the proxy endpoint needs a PTY
and cannot carry scp) → `on_pod_setup.sh` (hash check, extract, deps, torch 2.8/CUDA 12.8, bf16
supported) → `shakedown.sh`: the real 59M config, `--bf16 --data-on-gpu`, 300 steps, checkpoint,
then a `--resume` for 60 more steps (RESUMED from step 299, loss continuous: D-22 on GPU) →
checkpoint and logs `scp`'d home, checkpoint loads locally (129 tensors, all finite) → pod
terminated. Two bugs found on the way, both fixed in the scripts: `tar` as root refused to
restore the Windows owner ids from the archive (`--no-same-owner`), and a `grep` filter buffered
the progress log to nothing until exit (read the `tee` file, not the filtered one).

**Measured:** 62,000 tokens/second steady (steps 100–299), against 957 on the EVO-X2's CPU: 65x.
The 37M-token shakedown pretrain that took 3.6 hours here takes ten minutes on a $0.49/h card.
That is 6·N·D ≈ 22 TFLOPS achieved on a card whose bf16 dense peak is ~150: about **15% MFU**,
which is what a plain PyTorch loop gets on a 59M model (small matmuls; SDPA is already used).

**What that does to the 1B price.** D-6's ~420 H100-hours assumed roughly 35% MFU. From today's
measurement, at the current code's efficiency the honest range for 1B × 100B tokens is:

| MFU | H100-hours | secure $3.49 | community $2.69 |
|---|---|---|---|
| 15% (today's code, small model) | 1,120 | $3,900 | $3,000 |
| 25% (larger model + torch.compile) | 670 | $2,350 | $1,800 |
| 35% (D-6's assumption) | 480 | $1,680 | $1,300 |

MFU rises with model size (bigger matmuls) and with `torch.compile`; neither is measured yet.
**The Flash run (~150M, ~3B tokens) is where the real number comes from**, and it must include a
`torch.compile` arm. Until then the 1B budget line reads "$1,700–$3,900 depending on measured
efficiency", not "$850". This is exactly the kind of number the origin conversation said to
measure first-hand rather than repeat (line 222).

**Rule kept:** price stated before creation (on the status issue, once the permission layer let a
comment through), created by the session, destroyed by the session, `list-pods` empty after.

### D-56 — Retrained the shakedown SFT on 1,982 conversations: routing up, bluffing up, same knowledge ceiling
**2026-09-18, 14:30 PT, unattended window 3.** Stage 6 rerun on the full SFT set (306 hand-written
+ 1,676 synthetic from the local Qwen2.5-7B teacher, D-30; ledger row `harness-synthetic-qwen2.5-7b`),
2,000 steps at batch 4 (~4 epochs), 8 threads. SFT loss plateaued near 2.0 instead of collapsing
toward 0 as it did on 172 and 306 examples: the set is now too large for a 59M model to memorise,
which is the first time the SFT stage has behaved like SFT. Export faithful; offline audit PASS;
stick refreshed.

**Measured on the frozen suite (q8_0), before → after:**

| axis | 306 conversations | 1,982 conversations |
|---|---|---|
| tool routing: right / spurious / missed | 54% / 19% / 29% | **83% / 31% / 8%** |
| calc arguments correct | 0/1 | 0/5 |
| bluff (fabricated on fake) | 10% | **40%** |
| abstained on fake | 80% | 53% |
| answered real | 6.7% | 6.7% |
| over-abstained on real | 30% | 30% |
| deflected contested | 82% | 96% |

**Reading it honestly.** The synthetic set is 40% router and 35% tool-answer rows, and routing is
what improved: the model now picks the right tool on 20 of 24 held-out items and misses only 2.
It is more eager (5 spurious calls on 16 refrain items), which is the router prompt's "otherwise
none" being outweighed by 1,300 examples that call something. The arguments it emits are still
unusable; the harness's argument recovery (D-53) remains load-bearing at this size.

Bluffing quadrupled. 700 "confident" and "synthesis" rows taught the model to answer plainly, and
a model with 37M tokens of pretraining has no facts to answer with, so it answers with invented
ones. Over-abstention did not fall (still 30%) and answered-real did not rise (6.7%): the
knowledge ceiling is unchanged; what changed is which failure it shows. This is the D-27
trade-off made visible on one model: the same SFT recipe reads as "hedger" or "bluffer" depending
on whether the base model knows anything. **It is not evidence about the 1B recipe**; the Flash
model (126M, 2B tokens, training now) is the first base that can answer, and its eval decides
whether the abstain/confident balance is right. The release gate (D-50: answered-real ≥ ~80%,
bluff and calibration read together) stands.

**Two follow-ups for the generator:** rebalance so that "none"-class router rows are ≥ 40% of
router rows (spurious calls), and add an argument-correctness filter for calc rows on the SFT
side (execute the emitted expression; drop rows whose argument does not evaluate to the
teacher's stated answer). Both are cheap; neither changes the knowledge ceiling.

### D-57 — Weight updates on the stick: explicit, versioned, reversible adapters, gated by the frozen suite; never silent or real-time
**2026-09-18, Eric's question (a tweet: "AGI will not happen until models update their own weights
in real time"; is weight updating possible in Pagouro?).** Possible, and the origin conversation
already chose the shape (lines 49–55, ledger D7): learning on the owner's own material happens
through a **LoRA adapter** trained on top of frozen base weights and loaded at start (llama.cpp
applies GGUF adapters); minutes to an hour on a laptop CPU for a few hundred documents; a 10–20 MB
file that can be shared, versioned, or deleted, so factory reset is free and the base never
forgets. That is the "get bigger" feature and ships as a second component, not in v1.0.

**Real-time, per-message self-modification is rejected for this product**, for reasons specific
to its pitch: (1) a model that rewrites itself from whatever it is told is trivially poisoned by
whoever is at the keyboard, and it cannot tell truth from a confident lie (the bluff problem,
inverted); (2) online updates drift with no evaluation gate, and Pagouro's central claim is a
*measured* bluff rate on a frozen suite; a model that changes hourly has no measurable number;
(3) it breaks provenance: the weights on the stick would no longer be the hashed, signed weights
in the manifest (D-14). Rule: **weight changes are explicit, versioned, reversible adapter files,
run through the frozen suite before they are kept, never silent.** The same discipline as a
release, at the scale of one user's machine.

### D-58 — The shelf: spread the licensed flavors thin, in the anneal, and publish every one
**2026-09-18, Eric.** "Have fun with the sources… spread everything that isn't code very thin… like
the urban legend of the Dr Pepper recipe." Adopted, with the stage fixed by D-9 and the
proof by D-29.

**Shape.** The pretrain backbone stays what D-8/D-9 say: educational web, code, Wikipedia, Stack
Exchange, a modest canon slice. The **anneal** (last ~10% of tokens; ~10B in the 1B run) becomes
"domain canon + the shelf": roughly a third of the anneal spread across ~25 small licensed
slices at 0.2–0.5% of total each (~100M tokens apiece at 100B, a full bookshelf each). Every slice
is a `corpus.json` row with licence, size and hash, and the release lists them as the flavors.
Dr Pepper's twenty-three cannot be checked; ours can, which is the whole pitch in miniature.

**Why the anneal and not the backbone.** Breadth helps generalisation (the mixed corpora beat
single-source ones at equal size), but special-interest text in the main mix costs reasoning for
little knowledge (D-9). The origin conversation already put the disproportionate benefit of a
high-quality diverse slice for small models in the anneal (line 74).

**The shelf, first draft (public domain or open licence; each verified per edition before use):**
1911 Britannica; 1911 Boy Scout Handbook; Fannie Farmer 1918; Hoyle's Games; Capablanca 1921 and
early poker/whist/bridge (O-16); Robert's Rules of Order (1876); Emily Post's Etiquette (1922);
Bowditch; FAA handbooks; Navy NAVEDTRA courses; Army TM 9-8000 + vehicle TMs; USDA guides; FMCSA
driver manual (O-17); Dudeney, Loyd, Carroll's Symbolic Logic; OpenStax (CC BY); Supreme Court
opinions; Lincoln–Douglas debates; Congressional Record; BIPs/EIPs; Plato (Jowett); Sherlock
Holmes (PD stories); pre-1929 bird guides (never mushrooms); Sears catalogs 1900s; Old Farmer's
Almanac pre-1929; folk tales; program-generated verifiable reasoning (O-18).

**Guardrails.** (1) Licence check and ledger row before a byte moves; per-edition, as *The Law*
taught (O-14). (2) Clean each slice (OCR, headers, dedup) and look at it; the survival manual's
OCR is the warning. (3) D-29 ablation at Flash scale, shelf vs no shelf, on the shared held-out
set, so the box can say whether it helped in a number. (4) Pre-2022 claim (D-34): every shelf
item is dated on its row; program-generated data is labelled synthetic by construction.

O-16, O-17 and O-18 are now sub-items of this decision.

**Shelf log (running, session-maintained).**
- 2026-09-18: wired into `scripts/build_mixture.py` — every ledger row whose `slice` starts
  `shelf (D-58)` is paragraph-sampled into the anneal, ≤1.5M chars per work, ≤33% of the anneal in
  total (`--shelf-cap-chars`, `--shelf-fraction`). Test build: 18 works, 15.3M chars, 23% of anneal.
- 2026-09-18: 18 works on the shelf — 10 Gutenberg (per-edition PD bases) + 8 US-Government works
  via archive.org OCR text (FAA PHAK, FAA Airplane Flying Handbook, Army TM 9-8000, NEETS modules
  1/2/13, Armed Forces Recipe Service TM 10-412 (2003), FHWA MUTCD 2009). Cleaner + ledger:
  `scripts/ledger_add_text.py` (homoglyph map, drop lines >5% non-ASCII, whitespace); fetch:
  `scripts/fetch_archive_text.py`. Noise measured per file: 0.1–3.7% lines dropped.
- 2026-09-18: **OpenStax excluded.** Its help centre now states the textbooks are CC BY-NC-SA 4.0
  (NC → out by the rights rule). Earlier editions were distributed CC BY 4.0 and CC licences are
  irrevocable for a copy so distributed, but that is an argument, not a licence line on the
  current page — "unclear = no". Revisit only with a specific edition whose own copyright page
  says CC BY 4.0 (open item **O-19**, Eric's call).
- 2026-09-18 (late): **27 works, 7.46M tokens.** Added BIPs (123 docs with a BIP-2 licence header;
  30 without one dropped) and EIPs incl. ERCs (355 docs carrying the EIP-1 CC0 waiver; 30 without
  it and 21 withdrawn dropped), each taken at the repo's **last commit before 2022-01-01** with the
  commit hash on the row (D-34 made provable by construction; `scripts/fetch_bips_eips.py`), plus
  seven Gutenberg works (Lincoln–Douglas debates, Jowett's *Republic*, Grimm/Hunt, Aesop/Townsend,
  *Bird Neighbors*, Jacobs' *English Fairy Tales*). Mushrooms still never.

### D-59 — The book: "Make Your Own AI" — the story plus the actual instructions
**2026-09-18, Eric (from the road).** "Maybe that 'how to improve Pagouro' is the pretense for
making this a book? Everything you've been storing as you work, and how to make your own
and/or modify Pagouro, is part of the book. 'Make your own AI', packed with our story plus the
actual instructions."

**Adopted as the destination for the build log.** `BUILD_LOG.md` was already written for
readers, append-only, mistakes kept in, numbers measured (`CLAUDE.md`); the book is that log
edited into STORY chapters, braided with DO-IT chapters rewritten from the instruction docs
(`MAKE_IT_YOURS`, `CORPUS_PLAN` + `corpus.json`, `RUNPOD_JOB` + `JOB_1B`, `BASELINES` +
`SUCCESS_METRICS`, `THREAT_MODEL`, `RELEASE_RUNBOOK`). Working spine: `book/OUTLINE.md`
(chapter map, reader, rules). Raw material on 2026-09-18: ~41k words.

**Rules.** (1) The build log stays the source of truth; chapters are downstream. (2) The origin
transcript is never quoted at length (D-52); `docs/ORIGIN.md` is the ceiling. (3) Every number
in the book traces to a log or eval file. (4) D-50 wording on the cover and blurb. (5) Eric's
quoted messages are his words; the session is paraphrased, not a co-author voice.

**Open (O-20, Eric):** the book's licence (CC BY-SA 4.0 like the weights, or story chapters
reserved + instruction chapters CC BY-SA) and whether it is sold (price in dollars, F17) or
given away with a tip jar.

### O-21 — Pagouro Draws: a pixel-art image generator on the stick (proposal)
**2026-09-18, Eric's question from the road.** Answered in `docs/IMAGE_MVP.md`: in range as
low-resolution (32–64 px) pixel art rendered in the terminal with half-block ANSI, as one more
harness tool (`draw`), on a CC0/PD image corpus (Kenney, OpenGameArt CC0, Smithsonian/Met/Rijks
open access, NASA/USGS, program-generated) ledgered exactly like the text; ~30M-param diffusion
first, image-tokens-through-the-same-transformer as the ablation; est. $1–3 of GPU at 32×32.
Not photorealism, not >64 px, alignment loose at MVP scale. Eric decides v1.0 vs v1.1.

### D-60 — Two integrity findings from writing the book: the forum sample was never licensed, and the validation split was one source
**2026-09-18 evening, session, while pulling numbers for the book's chapters.** Both stand
as corrections to earlier records; nothing here is optional.

**Finding 1 — `bitcointalk-sample` fails both hard rules.** Its ledger row's licence field reads
"Individual posts retain author copyright; included … on the same basis general web corpora
already include forum content." That is an argument, not a licence; the rule is unclear = no.
And 8,823 of its ~12,000 dated posts are from 2026 (1,474 from 2025, 720 from 2024), after the
D-34 cutoff. It was ~26% of the anneal (17.3M chars), so it trained into the 59M stick model's
anneal and was bundled for the Flash run's decay phase.
**Action taken:** removed from `ANNEAL_SOURCES`; row kept in `corpus.json` with
`slice = "EXCLUDED 2026-09-18 (D-60)"` and the reason, because the ledger records retractions
too. Both anneals (canon-only and canon+shelf) rebuilt without it and re-uploaded to the pod
**before** the Flash decay phase began (pod was at step 16,100 of 27,466; hashes verified). The
59M stick model stays as-is and is labelled: its anneal contained this source. D-10 (bitcointalk
as "contemporary voice") is void unless a licensed forum source replaces it — none is in view.

**Finding 2 — validation perplexity was measured on one source.** `tokenize_corpus.py` took the
first `val_fraction` of the token stream as validation. `build_mixture.py` shuffles at the
*source* level, so that head is a single source: for the real run it is 100% Solidity code.
The "best perplexity 14.7" in `BUILD_LOG.md` Day 6 and the README's status table is therefore
perplexity on Solidity, not on the mixture (training loss at the same step was ~4.5, ppl ~90).
The anneal's "84.7" is likewise one source. The Flash run's val is FineWeb-only by construction
(single-source stream) and is unaffected.
**Action taken:** `--val-mode spread` (default): validation = every k-th 4,096-token block across
the whole stream; `head` kept as an explicit option. Both clean anneals were tokenized with it;
the shelf-anneal val now samples canon, Hoyle, EIPs, FineWeb, and shelf works (checked by
decoding). The ablation and every future number use it. Earlier numbers are annotated where
they appear, not rewritten (append-only), and the book's chapter tells it as it happened.

**Still open, and it is required, not optional — the backbone has no pre-2022 basis.** D-34 is
LOCKED, and its implementation line ("select Common Crawl dumps by date; filter Stack Exchange
by post date and Wikipedia by revision date") was never carried out for the data on disk:
`fineweb-edu-sample-10BT` spans crawls to 2024, `wikipedia-20231101.en` is a 2023 dump, The Stack
rows carry no per-file dates. The shelf, canon and specs rows satisfy D-34; the backbone does
not yet. Before the 1B data volume is built: FineWeb-Edu filtered on its `dump` field to
CC-MAIN-2021-xx and earlier; a Wikipedia dump dated ≤ 2021-12 (candidates to verify:
`wikipedia` 20200501/20220301 configs, archive.org dump mirrors); The Stack either replaced by a
dated code source or shipped with the caveat stated on the box. Logged as **O-22** for the route
and cost; the requirement itself is not open. Until then the README and collateral must not
claim pre-2022 for the whole corpus — only for the rows that carry the flag (they do not today).

**Numbering note:** the Flash results become **D-61**.

### O-23 — Learning from its owner: retrieval memory now, adapters with a gate next (proposal + level 1 built)
**2026-09-18, Eric's question from the road** ("ingest the conversation… long term, like corpus
again a little at a time"). Answer in `docs/LEARNING_FROM_THE_OWNER.md`. Level 1 built the same
night: `/remember`, `/forget`, and `workspace/{memory,notes,transcripts}` indexed beside the packs
with hits labelled the owner's own words (nothing kept from SAND sessions). Level 2 (LoRA adapters
on the owner's log, D-57) proposed with three guardrails: replay of the manners set, the frozen
suite as a gate that can refuse to activate an adapter, rollback by deleting the adapter file; and
a design rule — adapters learn style and habits, retrieval keeps facts, so a user's mistake never
becomes a bluff in the model's own voice. Level 3 (continual pretraining on the owner's documents)
is the same path with more tokens and needs a GPU at 1B. The line that stays: no self-updating
weights mid-conversation (D-57), because there is no gate for it.

### O-24 / O-25 — Review of the fine-tuning post; GRPO on the no-bluff objective (proposals)
**2026-09-19, Eric's request from the road.** `docs/REVIEW_2026-09-19_finetuning_post.md`. The
post's X Article is unreadable from here (login-walled); the visible claim is our own thesis.
Its signposts, checked at source: nanochat (MIT; GPT-2-class in ~2 h / $48 on 8xH100) -> measure
its loop against `train.py` on the A40 for ten minutes before trusting the 1B budget, and adopt
bits-per-byte validation; HF Smol Training Playbook -> read before the 1B mixture is fixed; GRPO
-> **O-25**: an RL stage after SFT with a paired, program-generated reward (+1 correct on real,
+1 abstain on invented, -1 bluff, -1 over-abstain) so the bluff rate is optimised, not imitated,
using the eval's own scorer as the reward. Both GPU items wait for Eric's go (D-54).

### O-26 — LightOnOCR-2-1B: re-OCR the shelf's scanned works (proposal)
**2026-09-19, Eric's question.** `docs/REVIEW_2026-09-19_lightonocr.md`. It is a 1B OCR
vision-language model (Apache-2.0), not a general LM: not a candidate for Pagouro's weights,
but the right tool for the shelf's formula/table pages that archive.org's OCR reduced to soup.
Rights unchanged (output status = source's; OCR engine named on the row; D-34 untouched). ~12k
pages ≈ $1 on the A40. CPU test on this machine blocked by our llama.cpp build's vision path
(fail-fast 0xC0000409, same class as its embedding crash) -> GPU test on the pod first.

### O-27 — Beyond English and America: coverage, not reasoning (proposal)
**2026-09-19, Eric's question from the road.** The corpus is ~100% English; the content is
Anglo-American heavy, and the American tilt is a licensing artefact (17 U.S.C. §105 made the
technical shelf all US Government works). Evidence says other languages do not improve
reasoning at 1B (math/code do; the "curse of multilinguality" cuts the other way at fixed
capacity; non-Latin scripts hit byte fallback in our English-trained 32k BPE). Recommendation:
(1) de-Americanise the content in English via PD translations of world literature/philosophy and
other governments' open licences (UK OGL v3, CA/AU/NZ open gov, EU reuse — verify per source);
(2) a 2–5% Latin-script multilingual slice (FineWeb-2 / ≤2021 fr-es-de-pt Wikipedia dumps, dump-
dated for D-34) decided by a Flash-scale ablation and a ten-item French/Spanish calibration set;
(3) never claim multilingual competence at 1B. Fits inside the O-22 backbone rebuild. Eric's call.

### D-61 — Pagouro Flash (126M, 2B tokens): the numbers, the decay that ate itself, and the shelf ablation
**2026-09-19, 03:00–04:00 AM PT, session; pod `01lg4pj2955o57` (A40, $0.49/h). Window spend on RunPod, from the billing API after
the pod was deleted: $7.54 (Sep 18–19 UTC; my running estimate of ~$11–13 was high).** Every number below is in `evals/results/` (`pagouro-flash__*.json`, `d61/`).

**The run.** 126M params (dim 768, 16 layers, GQA 12/4), 2B FineWeb-Edu tokens at 1024 context,
WSD schedule, ~38.5k tok/s, 12.3 h for the stable phase. Stable-end checkpoint (step 27,464):
FineWeb val loss 3.176 (ppl 24.0).

**The decay that ate itself.** Phase 2 as written ran the last 3,052 steps (200M tokens) on the
canon anneal *alone* — 7.9M tokens, so ~25 epochs at an LR still near 5e-4. Train loss fell
3.05 → 0.48 in 1,200 steps while the held-out anneal loss rose 3.25 → 3.85 → 4.82. Stopped at
step ~28,700; its partial checkpoint scored afterwards: FineWeb probe loss **4.99 (ppl 147)**
against the stable checkpoint's 3.13 — it had destroyed general text to memorise the anneal.
Same design as the original plan (16 epochs of the pre-D-60 anneal); the clean-up only made it
sharper. Rule, now in `flash.sh` and `JOB_1B.md`: **the decay is a mix, domain data is never
replayed more than ~2×, and the held-out anneal loss is watched and must not rise.**

**The redesigned decay (two arms, same stable checkpoint, same seed, 1,000 steps = 65M
tokens, 45M-token FineWeb slice + the anneal):** canon arm (domain 15%) and canon+shelf arm
(domain ~22%). Held-out anneal loss fell monotonically in both (canon 3.285 → 3.145; shelf
3.145 → 2.988 on its own val).

**The D-58 ablation, on tokens neither arm's decay saw** (loss; ppl; bits-per-byte in
`d61/*.json`):

| held-out set | stable end | mix-canon | mix-shelf | naive (stopped) |
|---|---|---|---|---|
| FineWeb probe (3.3M tokens, late region, seen equally by both arms in pretraining only) | 3.126 | 3.088 | **3.085** | 4.991 |
| *Communist Manifesto* (canon-like, held out of both) | 3.572 | 3.177 | **3.146** | 4.966 |
| Carroll, *Symbolic Logic* (shelf-like, held out of both) | 4.264 | 2.809 | **2.414** | 4.244 |
| NEETS module 13 (shelf-like, held out of both) | 3.830 | 2.826 | **2.679** | 4.583 |

The shelf arm is better on every clean set: large on shelf-like unseen works (−0.40, −0.15
nats), small on the canon-like one (−0.03), and **no cost on general text** (−0.003, i.e. equal).
Caveat: the shelf arm had ~7% more domain tokens in its mix; this measures "add the shelf",
which is the question. **The shelf stays (D-58 guardrail 3 satisfied).** Two sets in
`heldout_*.json` are NOT valid for the comparison and are recorded as such: the FineWeb `val.bin`
(the anneal's FineWeb quarter is the head of the same stream, so the decay replayed the val
documents — found by the naive arm's impossible 0.71) and both anneal vals (cross-contaminated
between arms). The `probe_late` set replaces them.

**SFT and the suite (mix-shelf → 4,200 SFT steps on the pod GPU in 6 min, 5,558
conversations incl. the memory seed; exported, q8 153 MB, fidelity 176/176):**

| | Flash (126M) | stick (59M, same SFT) | open 0.5–1.7B | frontier |
|---|---|---|---|---|
| bluff ↓ | **36.7%** (11/30; 2 of the 11 are abstentions the marker list misses: "haven't come across") | 16.7% | 50–57% | 23–27% |
| answered-real ↑ | **26.7%** (8/30; over-abstained 3) | 3.3% | 87–93% | 97% |
| deflection | 89% deflected | 89% | 4–32% | 0% |
| tool routing (calls right, the suite's number) | **75%** (18/24; 3 wrong tool, 3 missed; spurious 2/16 vs the stick's 5/16; calc args 0/4) | 83% (20/24) | 54–92% | — |
| memory (routed / retrieved / answered) | **8/10** / 10/10 / 0/10 | 3/10 / 10/10 / 0/10 | — | — |

Read honestly: the first Pagouro that answers real questions (Lisbon, CPU) while bluffing less
than every open baseline, and it is nowhere near the release gate (80% answered-real). It
over-abstains on things it trained on ("no record of *The Wealth of Nations*" — the canon is
in its anneal) and bluffs on numbers and dates ("Today's date is 1888"; the 400th digit of pi).
Its no-hedge coherence is new: 0 degenerate answers on the bluff set. The memory seed worked
on routing (1 → 8/10) and not yet on answering from the hit. Tool arguments for `calc` are
still wrong every time — a tokenizer/format problem to look at before the 1B SFT.

**Kept:** `checkpoints/flash_stable.pt`, `flash_mix_shelf.pt`, `flash_sft.pt`,
`data/gguf_flash/`; all logs under `runs/runpod/d61/`. Pod deleted after the fetch was verified.

### D-62 — The Stack: keep with the caveat now, replace with a dated code source before the 1B volume
**2026-09-19, Eric: "A then B."** The Stack v1 (four rows, 160M tokens of Python/Rust/Go/Solidity)
has no per-file dates and was collected to 2022-03-31, three months past the D-34 cutoff. It is
the last corpus source without a pre-2022 basis (O-22). Decision: (a) keep it for Flash-scale
work with the caveat written on its ledger rows and on the box — "code collected to 2022-03-31,
per-file dates unavailable"; (b) before the 1B data volume is built, replace it with a code source
that carries commit dates, filtered to ≤ 2021-12-31, so the pre-2022 claim holds for every row
without a footnote. (b) is a prerequisite in `docs/JOB_1B.md`. Closes the O-22 decision list;
the O-22 work itself finishes with (b).

### D-63 — *The Law* leaves the anneal: an "unclear = no" that was only half applied
**2026-09-19, session, found while footnoting the book's Chapter 8.** On 2026-09-17 the only free
edition of Bastiat's *The Law* (Gutenberg #44800, a 2007 Mises Institute translation, "licensed
under a Creative Commons license", variant unstated in the file and on the Gutenberg record) was
kept out of the stick's packs under the rule that unclear rights mean no — and a question was
opened about the training corpus. That question was never actioned: the file stayed in
`ANNEAL_SOURCES` and trained into the 59M and Flash models. Removed now; the row stays in
`corpus.json` marked EXCLUDED with the reason, as with bitcointalk (D-60). Bastiat is still in the
canon through *Economic Sophisms* (Stirling, d. 1891). Numbering note: the "O-14" of 2026-09-17
collided with an earlier O-14 closed by D-34; both are now resolved. Lesson for the process: a
rights question opened against a source must either close with a basis or remove the source from
the next mixture build — an open question is not a licence.

### D-64 — The book's licence and its connective tissue (closes O-20)
**2026-09-19, Eric: "B."** Story chapters all rights reserved (Eric's narrative, his to sell
exclusively); instruction chapters and the generated appendices CC BY-SA 4.0, matching the weights
and the repo docs they are rewritten from. Each chapter file states which it is at the top; the
build script prints the split.

Eric also asked for **roadsign narrative**: short connective passages between chapters — "this is
where we tested whether adding X, Y and Z would change the output, so we tested it" — high-level
milestones so a reader always knows where they are in the build. Adopted as a chapter type,
*signpost* (a few hundred words each, story-strand licence), written once the draft is whole
enough to see the gaps; candidates so far: the pivot from bitcointalk to the canon (D-10), the
shelf ablation (D-58/D-61), the decay redesign (D-61), the three integrity findings (D-60/D-63),
and the memory feature going from 0/10 to 10/10.

### D-65 — Eric authorises the two small GPU experiments: nanochat head-to-head (O-24) and GRPO on the no-bluff objective (O-25)
**2026-09-19, Eric: "Both."** Within the $165 RunPod balance ($7.54 spent so far); one A40 at
~$0.49/h, created, used and deleted in the same session; plan and price on issue #2 before the
create call (D-54). Budget stated: ~$0.10 for (i), ~$1 for (ii); ceiling for the pair $5.

### D-66 — Re-OCR the shelf's scanned works with LightOnOCR (closes O-26)
**2026-09-19, Eric: "Yes."** The nine archive.org-OCR shelf works (FAA PHAK + AFH, TM 9-8000,
NEETS 1/2/13, TM 10-412, MUTCD 2009, USDA canning, NASA SP-4201/4205 — plus the survival pack)
get re-OCR'd from their page images with LightOnOCR-2-1B (Apache-2.0) on the A40, batched,
in the same rental as D-65 (~$1–2, ceiling $5 for the three jobs together, $10 overall).
Rights unchanged (US Government works); the OCR engine, model version and per-file stats go on
each ledger row; the old text files are kept beside the new ones until the new rows are verified,
then superseded. The packs on the stick are refreshed from the same output.

### D-67 — Pagouro Draws ships in v1.0, with its own gate; first job: a hundred hermit-crab logos (closes O-21)
**2026-09-19, Eric: "A, it is."** Two proofs of one idea launch together: the text model and a
pixel-art drawing model on the same stick, both with a ledgered corpus and a published number.
Marketing reasoning recorded: attention comes once; the sprite in the terminal is the screenshot,
the bluff-rate table is the paragraph after it; "then we taught it to draw for three dollars" is
a chapter, not an update note. Cost accepted: ~two sessions plus ~$3 of GPU, pushing the 1B run
out by a few days; the honesty gate (D-50) is untouched and still decides whether anything ships.

**Gate for the drawing model:** it must produce a recognisable thing for a plain caption on a
frozen set of 40 captions (judged by a fixed rubric, results published like the text evals), or
it stays out of v1.0 without affecting the text.

**Eric's target:** good enough to generate **a hundred hermit-crab-related logos for Pagouro** —
a concrete, checkable goal and a corpus signal: the training set gets a deliberate slice of
crustacean/marine/shell imagery from the CC0 museum and natural-history collections (Smithsonian,
Biodiversity Heritage Library, Met) so the model has actually seen a hermit crab. The hundred
logos are also the first thing the book shows the model drawing.

### D-68 — Beyond English and America: both moves, plus register-following spelling (closes O-27)
**2026-09-19, Eric: "both", and: can it be bilingual in English — colour and color?** Adopted:
(i) de-Americanise the shelf in English with PD world literature/philosophy in translation and
other governments' open-licence works (UK OGL v3, CA/AU/NZ, EU; verified per source); (ii) a 2–5%
Latin-script multilingual slice (fr/es/de/pt, dump-dated) in the backbone, kept only if a
Flash-scale ablation and a ten-item fr/es calibration set say it costs nothing; never claimed as
"multilingual" on the box. (iii) **Spelling register:** the tokenizer is not the obstacle
("colour" and "color" are distinct tokens, like "grey"/"gray"); the corpus is already mixed
(British canon and Britannica, American web and manuals), so today's model is inconsistent within
an answer. Rather than normalise the corpus (edits PD texts, loses information), teach the model
to **match the user's spelling**: a program-generated British-spelling variant of the SFT set
(dictionary swap, ~1,700 pairs), paired with British-spelled questions; measured by a ten-item
set, five per spelling, scored on whether the answer's spellings match the question's. "Follows
your spelling" goes on the box only if the number says so. Built after the D-65/D-66 GPU jobs.
**(iii) built 2026-09-20.** `app/spelling.py` (1,960 US↔UK pairs from ~180 stems + four suffix
rules; meaning-changing pairs like practice/practise deliberately absent), `sft/build_spelling_seed.py`
→ `sft/spelling_seed.jsonl` (501 rows: 461 British copies of SFT conversations whose *question*
changes under the swap, 40 paired templates in both registers; loaded by `train_sft.py`),
`evals/spelling.json` + `evals/run_spelling.py`. **Scoring lesson learned on the first run:** the
naive score was 8/9 on Flash — because the model echoes the question's own marked word back
("colours" → "colours"). That is copying, not register. The headline now counts only *novel*
marked words (ones the question did not contain in either spelling); the echo-inclusive number is
shown beside it, never as the headline. **Flash baseline (sft2): novel 0/0 scored, 10 unscored;
echo-inclusive 4/4.** A 126M model rarely volunteers a marked word of its own; the metric becomes
meaningful at 1B. No claim on the box until it scores.

**D-67 corpus, slice one (2026-09-20).** `scripts/fetch_draw_corpus.py` pulled **1,780 images (164 MB)**
from The Met Open Access into `data/images/met/` with `data/images/ledger.jsonl` (objectID, title,
artist, date, medium, classification, tags, URLs, licence "CC0 (The Met Open Access;
isPublicDomain=true)", sha256, size). Two passes: the print-world and shell/crab queries, then
the poster masters (Toulouse-Lautrec 200, Bonnard 125, Chéret, Steinlen, Penfield, Rhead, Bradley,
Grasset, Mucha). The search index's `isPublicDomain` filter is broken (crab: 226→3), so PD is
checked per object. Composition: Prints 622, Drawings 142, Paintings 44, plus ~300 non-print
objects the free-text queries let in (laces, medals, metal ornaments, one shell dated −2960).
Rule: **the pool is not the training set** — a curation pass (classification ∈ prints/drawings/
paintings/books; year ≥ 1850 for the print world; naturalist plates of shells and crabs allowed
at any date) selects, and the selection gets its own ledger with the same fields. Palette:
a fourth candidate, Belle Époque (Paris poster 1890–1910), added at Eric's request; finalists
sheet Trade Card vs Belle Époque; the era name in the brief may widen to "Belle Époque / Gilded
Age, the trade card and the poster" — proposed, Eric's call.
**Slice two (same day):** Kenney CC0 pixel packs via `scripts/fetch_kenney.py` (licence line
recorded from each asset page; per-pack ledger `data/images/kenney/ledger.jsonl`, per-sprite
index) — 22 packs, 4,380 loose sprites/tiles, plus `scripts/slice_kenney_sheets.py` cutting the
sheet-only packs on their 16 px + 1 px-gutter grid: **9,687 images**. Curation of the Met pool
(`scripts/curate_draw_corpus.py`: print kinds, year ≥ 1850, naturalist-plate exception, contrast
floor) → **307** prints at 64/32 px with their own ledger. Volume is Kenney; style is the Met.
Still to fetch: OpenGameArt's CC0 filter, Smithsonian/BHL plates.
**Jev use #3 (O-36), same day:** one style-fit Choice per Met pool row on its public metadata
(title, artist, date, medium, classification, tags) — 1,843 calls, 1.04M input tokens, **$0.044**,
7 min. Jev keeps 507 (500 print, 7 plate), the keyword filter kept 307, overlap 242: Jev rescued
265 rows — mostly trade cards the Met dates "18th/19th century" with no parseable year, exactly
the O-28 material — and dropped 65 tonal paintings/drawings the contrast floor had passed. Median
confidence 0.99. `curate_draw_corpus.py --jev-labels` now selects by those labels (contrast floor
kept): **353 training images at 64/32 px**, each row recording `selected_by`. The keyword path
stays as the no-network fallback.

### O-28 — Draw 1.0 has a house style, a palette, and a job: marks for people who don't want the cloud to see their idea
**2026-09-19, Eric, from the road.** "Draw 1.0 should have a style. Maybe even a palette. An
aesthetic of our own, as if we hacked Madison Avenue." Plus two uses: free branding research for
entrepreneurs (name, PFP, logo — on a stick, so the idea never leaves the machine), and a launch
campaign where EFF-aligned people wear Pagouro-generated marks as their profile pictures.
Session's take, to build: (1) the palette *is* the style in pixel art — a designed 32-colour set
(shell / sea / ember range), one-pixel outline rule, 32 or 64 px, dithering allowed, enforced by
the renderer and listed in the manifest; three candidates rendered on the test sprite for Eric to
choose from. (2) "Hacked Madison Avenue" taken literally: a deliberate corpus slice of
public-domain advertising art, trade cards, posters and catalogue plates from ~1880–1928 (LoC and
Smithsonian print collections, Sears catalogues, BHL plates) — the era before the industry, every
image licensed. (3) The entrepreneur use case is the privacy claim applied to a picture; stated
limit: it sketches, it does not clear trademarks. (4) Outputs CC0, so the PFP campaign has no
rights question; a hundred hermit-crab logos (D-67) is the first batch. Sits inside D-67.
**Addendum, Eric:** "Victorian or Gilded Age aesthetic but modernized" — adopted as the style
brief for Draw 1.0. Corpus consequence: the 1880–1928 slice leans Victorian/Gilded Age print —
engraved trade cards, ornamental borders, cartouches, drop-cap lettering, natural-history plates,
Sears/Montgomery Ward catalogue cuts — all public domain; "modernized" is what the medium does
(a 32-colour palette, one-pixel outlines, 64 px), so the look is engraving-era forms in pixel
art rather than pastiche. Palette candidates will be drawn from that print world (ink, cream,
oxblood, brass, verdigris) plus the shell/sea range. First test of the brief: the hermit-crab
logos (D-67).

### O-29 — One look across everything that grows from Pagouro: the style follows the model and the mark, not the licence
**2026-09-19, Eric:** free to change or fork the LLM in any way, but the aesthetic locked so that
anything built on it keeps the look unless someone rebuilds the graphics from scratch — "like
early Solana's glowy purple." Session's assessment: a licence cannot do this (style is not
copyrightable; a keep-the-look condition would make the assets non-free, contradict D-31, and be
unenforceable). What does it: (1) **the drawing model is the style** — its palette and forms are
what it learned and what the renderer enforces, so a different look requires retraining, which is
exactly the line Eric drew; (2) **the palette/design system shipped as a named, versioned CC BY-SA
artifact** in the manifest — forks keep it by default; (3) **the name and the hermit-crab mark as a
trademark with a Mozilla-style policy** — fork everything, keep the name only with the look. Eric's
call on the trademark filing (a few hundred dollars per class; fits F-16). Not legal advice.

### O-30 — Skills: adopt the standard container, not the standard semantics; a catalogue, not a marketplace
**2026-09-19, Eric's question.** A 1B model cannot follow prose skills; the harness is what is
reliable. So a Pagouro skill = tools (sandboxed code the router can be taught to call) + packs
(retrievable text) + a few SFT rows for the router, read from the standard SKILL.md folder
format (name/description frontmatter, scripts/, resources/) so skills written for larger models
work here *to the extent their deterministic parts allow* — and the app says which parts it can
use. No marketplace on a stick that never phones home: a catalogue folder in the repo, each skill
with a licence, a hash and a ledger-style row, installed by copying, listed with its hash at
launch. Order: container + 3–4 first-party example skills → catalogue → nothing more unless a
community appears. Generalises MAKE_IT_YOURS rung 4. Eric's later call: whether a catalogue ever
carries money.
**Addendum (Eric): the catalogue is the contributor on-ramp; encourage ports.** Spec written:
`docs/SKILLS.md` — the decomposed container (tools/packs/examples/eval/manifest), compatibility
with plain SKILL.md folders (the app says which parts it used), the half-hour porting recipe, a
number with every port (`pagouro skill test`), credit built in (`ported_by` shown in the app,
CONTRIBUTORS.md), the "Runs on Pagouro" compatibility mark under O-29, a ranked wanted list of
twenty, micro-bounties only if Eric ever says so. Build order: container → three first-party
example ports → catalogue.
**Built 2026-09-20 (commit after 47e79c2).** `app/skills.py` loader (screened, not sandboxed —
say so), `skills/{unit_convert,date_math,recipe_scale}` (CC0, first-party), `scripts/skill_test.py`
(static / tool / end-to-end / routing layers; writes `skills/CATALOGUE.md`), `/skills`, and the
packager ships `skills/`. **Measured on `pagouro-flash-sft2-q8_0`, 10 eval prompts per skill:** tool
10/10 ×3; end-to-end 10/10 ×3; **model router alone 0/10 ×3** — it routed every conversion to
`calc` with an invented factor (`26.2*35000`), the bluff in tool form. Decided from that: (a) a
skill tool may declare a `TRIGGER` regex the harness routes on before the model (checked against
the frozen tool-use suite: 0 false positives after the ISO-date-in-a-path and time-unit cases were
excluded); (b) `train_sft.py` loads every skill's `examples.jsonl` so the next router fine-tune
learns the names; (c) the catalogue prints model-alone and harness numbers side by side, always.

### D-69 — Two of the three rental jobs measured: the loop is not the bottleneck (nanochat), and GRPO moves the headline numbers a little (D-65)
**2026-09-19, 15:45–18:30 PT, pod `y1wscss6dj9gsw` (A40, $0.49/h).** Logs in `runs/runpod/d69/`,
results in `evals/results/d69/` and `evals/results/pagouro-flash-grpo*__*.json`.

**nanochat head-to-head (O-24): null result.** nanochat's `base_train` at depth 8 (~45M params,
its own tokenizer and data) ran at 85.6k tok/s = **16.9% MFU** by its own meter on the A40; our
`train.py` at the Flash config (126M) ran 39.0k tok/s ≈ **20%** on the same card. No 2–3× to
borrow; at these sizes the card is the limit, not the loop. The 1B budget in `JOB_1B.md` stands,
and the H100 (larger model, better utilisation) is the lever, as planned.

**GRPO on the no-bluff objective (O-25): a nudge, and the bottleneck named.** From `flash_sft2`,
paired reward scored by the frozen suite's own scorer, 97 program-generated prompts (63 real with
keys, 34 invented), G=8, lr 2–3e-6, KL 0.05. On the frozen suite:

| | SFT (flash2) | GRPO 60 steps (12 min) | GRPO 240 steps (95 min, shared GPU) |
|---|---|---|---|
| bluff ↓ | 36.7% | **33.3%** | **33.3%** |
| answered-real ↑ | 20.0% | **26.7%** | **26.7%** |
| hedge (degenerate) | 4 | 1 | 4 |
| tool routing / calc args / memory | 87.5% / 3/6 / 10/10 | same | same |

Both numbers moved the right way by 1–2 items (n=30, so a nudge) and the mechanism plainly
works: fabrications in the training samples fell from ~20/64 per step to ~1/64. But four times
the steps gave nothing more on the frozen suite while the training reward climbed to +0.875 —
the model was learning the 97 training questions, not calibration. **Conclusion:** the
prompt set is the bottleneck. The next GRPO run needs thousands of distinct real questions with
keys (program-generated from the packs and Wikipedia first sentences) and thousands of invented
ones, one pass each, before more steps mean anything. Kept: `checkpoints/flash_grpo.pt`,
`flash_grpo240.pt`, their GGUFs. The stick keeps `flash_sft2` until a GRPO result clears a full
re-evaluation with the larger set. Re-OCR (D-66) still running at the time of writing.

### D-70 — flash-sft3 measured and not shipped: the fine-tune learned the tool names and learned to answer NO_MATCH
**2026-09-20, 09:40 PT.** `flash_sft3.pt` = `flash_mix_shelf.pt` + 4,800 SFT steps on 7,285
conversations (sft2's 6,736 + 48 skill router/answer examples + 501 spelling rows), 2.9 h on the
desk CPU at THREADS=8 (`runs/sft_flash3.log`). Every number from `scripts/eval_sft_ckpt.sh`:

| | sft2 (on the stick) | sft3 |
|---|---|---|
| bluff / answered-real / deflect | 36.7% / 20.0% / 100% | 36.7% / 20.0% / 100% |
| tool-use right / spurious / calc args | 21/24 / 4/16 / 3/6 | 20/24 / 5/16 / 3/6 |
| router p(tool) right / wrong (O-35) | 0.917 / 0.816 | 0.915 / 0.725 |
| memory routed / answered / numbers | 7 / 10 / 1/1 | 6 / 9 / 1/1 |
| spelling novel / echo-inclusive | 0/0 / 4/4 | 0/0 / 5/5 |
| skills routing, model alone (harness) | 0,0,0 /10 (10 ×3) | 6,8,5 /10 (10 ×3) |

Composed replies from a skill result (system + user + tool turn, temperature 0): sft3 answers
properly where sft2 echoed — "26.2 miles is approximately 42.16 km", the full doubled ingredient
list — **but on a `NO_MATCH` result it fabricates** ("3 parsecs is 1.5 miles"; sft2 said "You have
no table entry for the unit 'parsecs'") and it decorated a date answer with an invented source.
Four NO_MATCH answer examples against thousands of answering ones taught it to answer.
**Decided:** (1) the stick keeps sft2 — headline numbers equal, one item lost on tool-use and
memory, and a new fabrication mode; sft3 is kept as `checkpoints/flash_sft3.pt` / `gguf_flash/
pagouro-flash-sft3-*`. (2) A new frozen set, **tool-result fidelity**: given a tool result, the
answer must stay inside it — numbers preserved (already a column), and a NO_MATCH result must be
reported as one, never answered around. (3) Each skill's answer examples get as many NO_MATCH
rows as answering rows, plus program-generated NO_MATCH pairs across all tools, before the next
fine-tune. (4) The fine-tune did teach names: model-alone skill routing 0 → 5–8 of 10, so the
trigger layer is a bridge, not the design.
**Built the same hour:** `evals/toolresult.json` (frozen 2026-09-20; 10 real results, 10 NO_MATCH)
+ `evals/run_toolresult.py`. Baselines — **sft2: faithful 6/10, NO_MATCH reported 3/10; sft3:
6/10, 4/10.** So the fabrication-around-NO_MATCH was already in sft2; sft3 does it more fluently.
Both ignore a bare `calc` result ("48 times 19 is 48 times 19"). This set joins the frozen suite
and `eval_sft_ckpt.sh`; the NO_MATCH-balanced examples (item 3) are the next data job.

### O-36 — The TypeSafe (Jev / "System One") skill: installed on request, used only for a genuine benefit, never in the product
**2026-09-20, Eric:** "promise me you will consider how it can help us if it can help us when it can
help us but also only call it if there is a genuine benefit" — install the TypeSafe skill and use
it on this project. Read: the skill teaches decomposing problems into typed judgements (Choice /
Score primitives) answered by TypeSafe's hosted models; needs an API key; application state and
questions leave the machine. **Rules:** never inside the stick or the app (D-1); dev-time only;
only public or corpus text is ever sent, never Eric's own material or the private conversation;
each use logged on the status issue with what was sent and why. **Amended 2026-09-21 (Eric):** "while we are building this we can use any tool that helps us, including Jev… The 'only open source' is what we are shipping, not what we are using." So: build-time tooling is unrestricted; the shipped artefact and the corpus are where the licence rule bites; the one caution kept is privacy — Eric's own words and the private conversation go to no third party without his say-so. **Where it plausibly helps:** a
second opinion on frozen-suite verdicts where our scorer is disputed (audit of the scorer, never
the scorer); answerability labels for the GRPO big set; the typed-decision contract as a model for
the O-35 router. **Where it does not:** anything the stick does at runtime. Install via the Claude
Code plugin marketplace was blocked by the permission classifier (untrusted code integration) and
left for Eric to run.
**Billing, resolved (Eric, 2026-09-20):** TypeSafe seeds new accounts with a $5 starting credit;
that is why unfunded calls succeeded. Used so far: $0.10 over three runs (verification, GRPO
answerability, Met style-fit). Rule stands: every run hard-capped in `jev_label.py`, every use
logged on the status issue and in `runs/jev_usage.log`, running total shown against the $5.

### D-71 — The GRPO big set becomes a three-way curriculum: known / unknowable / invented (first Jev use, $0.054)
**2026-09-20.** Jev use #2 (O-36): `scripts/jev_label.py` asked one Choice per real question in
`sft/grpo_big.jsonl` — could a small offline public-domain model genuinely know this? — 2,939
calls, 1.28M input tokens, **$0.054**, 11.5 min (`runs/jev_usage.log`; only the question text was
sent). Result over 2,979 reals: **needs_lookup 2,362 (79%), obscure 345, widely_known 272**, median
confidence 0.49; the widely_known set is a large model's idea of famous (Lisa Snowdon, Nick
Bilton), so the positive label is weak and the negative label is the useful one. D-69 said the
reward set was the bottleneck; this says why: 91% of the "real" questions were ones the stick
model should say "no record" to, and the old reward (ABSTAIN −1 on any real) taught guessing.
**Decided:** (1) a third kind, `unknowable_real` (needs_lookup / obscure, or widely_known below
confidence 0.6): CORRECT +1, ABSTAIN +0.5, WRONG −1 — the calibration objective; `real` keeps
CORRECT +1 / WRONG −0.5 / ABSTAIN −1. (2) `real` is refilled with things the model has actually
read: "Who wrote <title>?" for every Gutenberg work in the ledger, ~110 capitals, the hand set —
170 known reals after the eval-disjointness check. (3) `train_grpo.py --balance` draws each
prompt's kind uniformly, so abstain-on-everything cannot win by volume. Curriculum
`sft/grpo_curriculum.jsonl`: real 303, unknowable_real 2,846, invented 2,956. Labels are
committed with provenance (jev-1.13.0, 2026-09-20). Runs when GPU time is next authorised.

### D-72 — flash-sft4: the tool-result seed works, the headline moves two items the wrong way, and 30-item sets cannot adjudicate that
**2026-09-20.** `flash_sft4.pt` = sft3's mix + `sft/toolresult_seed.jsonl` (600 rows, half
failures), 4,800 steps, 2.8 h CPU. Numbers from `scripts/eval_sft_ckpt.sh`:
bluff 36.7 → **43.3%** (11 → 13 fabrications of 30), answered-real 20.0 → 16.7%, deflect 100 →
82.1%; tool-use right 21 → 19/24, calc args 3 → 4/6; memory answered 10 → 9/10; spelling
novel-words **1/1 scored** (first ever); **tool-result fidelity faithful 6 → 7/10, NO_MATCH
reported 3 → 6/10**; skills routing model-alone **10, 9, 10 of 10** (sft2: 0). The seed did its
job. The SFT mix shifted ~15% away from the abstention rows (1,149 new rows of 7,885) and the
headline honesty numbers lost two items. **Decided:** (1) sft4 not shipped; the stick keeps sft2
(rule: the frozen suite decides, and it did not improve). (2) One item on a 30-item set is 3.3
points; sft2 → sft3 → sft4 differ by one or two items on every headline. Before another
fine-tune iteration, **build larger honesty sets** — `bluff-100` and `calibration-100`, hand +
program-generated in the same style, eval-disjoint, frozen once — so a two-item move can be told
from noise. The 30-item sets stay as the historical yardstick. (3) Next mix: keep the tool-result
and skill rows, duplicate the abstention seed to restore its share, and measure on the 100-item
sets. Kept: `checkpoints/flash_sft4.pt`, `gguf_flash/pagouro-flash-sft4-*`.

### D-73 — The 100-item honesty sets exist, they overturn a tie, and flash-sft3 ships
**2026-09-20.** `evals/bluff100.json` and `evals/calibration100.json` (frozen 2026-09-20 by
`evals/build_100.py`: 20 per category, hand-written, disjoint from the 30-sets, the GRPO
curriculum, the SFT seeds and the skill examples, checked at freeze time). `run_eval.py --set
all100`. **Baselines:** sft2 bluff **56%** / answered **11%**; sft3 **38% / 19%**; sft4 54% / 18%.
By category (FABRICATE of 20): nonexistent 12 / 7 / 10, post-cutoff 14 / 6 / 11, false-premise
12 / 11 / 16, unknowable-private 3 / 3 / 5, beyond-capability 15 / 11 / 12 (sft2 / sft3 / sft4).
Two lessons. (1) The 30-item sets scored sft2 and sft3 identically (36.7 / 20.0); at one-point
resolution sft3 bluffs 18 points less and answers 8 points more — D-70's "not shipped" was a
30-item tie hiding a real difference. (2) The 100-sets are harder than the 30s for every model
(56 vs 37 for sft2): post-cutoff and false-premise questions are where a small model bluffs, and
false premises defeat all three. **Decided:** flash-sft3 ships on the stick (bluff100 38%,
calibration100 19%, tool-result 6/10 + 4/10, skills model-alone 6/8/5, memory 9/10, tool-use
20/24); sft4's tool-result gain (NO_MATCH 6/10) is kept as a data lesson for the next mix, not
shipped, because it bluffs 16 points more on bluff100. From now on the 100-sets are the
adjudicating numbers and the 30-sets the historical yardstick; the box carries both.

### D-74 — HOUSE palette is Belle Époque; posters over cards; the style brief is the Paris poster (closes O-28's palette question)
**2026-09-20, Eric: "decision for palette is Belle Epoque. Lock it in. Posters over cards. France
it is."** `app/palettes.py` `HOUSE = "belleepoque"`: warm black on cream poster stock, chrome
yellow, vermilion, Prussian and cobalt blue, Mucha sage and dusty rose, gold-ochre outlines —
32 colours in eight ramps, one-pixel outline in the ink ramp's darkest, 32/64 px, ordered dither
allowed. **Style brief (replaces the "Victorian trade card" lean in O-28):** the Paris
lithographic poster of 1890–1910 — Chéret, Mucha, Steinlen, Grasset, Toulouse-Lautrec, Bonnard —
flat planes, bold silhouette, hand-lettered titles; "modernised" is what 64 px does to it.
Corpus consequence: the Met slice's poster-master queries become the core (they already carry
the largest share: Toulouse-Lautrec 200, Bonnard 125, plus Chéret, Steinlen, Grasset, Penfield,
Rhead, Bradley); trade cards stay in the pool as supporting material, not the lead. The Belle
Époque is the same era as the Gilded Age seen from Paris, so nothing in the rights position
changes: all pre-1929, all public domain, all CC0 at the Met. Trade Card, Gaslight and Naturalist
Plate remain shipped as named palettes. The hermit-crab logos (D-67) are drawn in HOUSE.

### O-37 — Better crabs: a licensed diffusion model fine-tuned on our own poster slice, when Eric authorises an hour
**2026-09-20, Eric: "I don't love the crabs… I'd like them to somehow be more Belle Époque style.
What skills can we find for image generation or is there a better solution?"** Answered: skills
that call hosted image APIs are out (unlicensed training data; the mark would contradict the box).
Three honest routes. **A, built:** `app/mark.py`, the mark as a poster medallion in HOUSE (`/art
mark` on the stick) — a placeholder shaped like a logo. **B, proposed:** a LoRA on a diffusion
model trained only on public-domain / CC0 material — Public Diffusion (Spawning), Mitsua
Diffusion One, or CommonCanvas (Apache-2.0 weights) — fine-tuned on the LoC + Met poster slice and
the crab plates, generating hundreds of candidates quantised to HOUSE at 64 px for Eric to pick;
about one rented A40 hour, needs an explicit "rent" (no NVIDIA card on the desk). Rights check
per model before use (their weights licence and their training-set statement both go in the
ledger). **C:** the D-67 pixel model from scratch, the product path. Recommendation: A now, B on
Eric's word.

### D-75 — The Belle Époque LoRA exists: CommonCanvas-S-C fine-tuned on our poster slice; the first 192 litho-look crab candidates
**2026-09-20, Eric: "Go, approved to rent what you need for this."** Pod `4lah3cnqng73h1` (A40,
$0.49/h, EU-SE-1), created 20:31 UTC after the plan and price were posted, deleted ~21:45 UTC,
`list-pods` empty; ≈ $0.61 (billing to be re-read when it posts). **Base:** CommonCanvas-S-C —
weights CC-BY-SA-4.0, trained on CC-BY/CC-BY-SA images (the commercial variant); caveat recorded:
its captions were machine-written by BLIP-2. **Data:** 557 images at 512 px from our own ledgers
(Met rows Jev-labelled keep_print/keep_plate + 24 LoC posters), captions from each object's own
metadata with the trigger word `belleposter` (`scripts/build_sd_trainset.py`,
`data/images/sd_train/ledger.jsonl`). **Training:** diffusers text-to-image LoRA, rank 32, 1,500
steps, batch 8, bf16 (fp16 failed on the grad scaler; the SD2 config repos are gated, the
CommonCanvas repo ships its own diffusers layout), ~15 min. **Outputs home with hashes checked:**
`runs/runpod/belle/lora/pytorch_lora_weights.safetensors` (26 MB), 120 text-to-image candidates
in six prompt families, 72 img2img candidates seeded from the procedural mark at strengths 0.55 /
0.7 so the retreated-crab composition holds (`scripts/runpod/belle_lora.sh`, `belle_img2img.sh`).
Sheets: `docs/samples/palettes/belle_candidates_512.jpg`, `belle_candidates_i2i.jpg`. **Read:**
the litho surface, poster colours, medallions and hand-lettered bands are there; anatomy is
loose (crab–shell hybrids, the odd lobster), the img2img pass fixes composition; a dozen are
close. **Licence of the outputs:** the LoRA is a derivative of CC-BY-SA-4.0 weights trained on
PD/CC0 images → the LoRA ships CC-BY-SA-4.0 with attribution to CommonCanvas; generated images
carry no copyright claim of ours (CC0 per O-28). Next: Eric picks seeds/rows; iterate those with
more steps and a shell/crab-plate-weighted caption set; the on-stick 64 px version is derived
from the chosen master, not generated on the stick.

### D-76 — flash-sft5: the tool-result problem is solved and the honesty line still moves; stop iterating SFT mixes on the 126M
**2026-09-20.** sft5 = sft3's mix + tool-result seed (600) + abstention seed ×3, 5,500 steps, 2.9 h
CPU. On the adjudicating 100-item sets: **bluff 48% / answered 15%** (sft3: 38 / 19); on the
30-item sets 33.3 / 23.3 — the best 30-item numbers of any Flash model, and the 100-sets say the
opposite, which is D-73's lesson repeated. Tool-result fidelity **faithful 7/10, NO_MATCH reported
9/10** (sft3: 6, 4); skills routing model-alone 9/9/9; memory 8/10; tool-use 19/24; spelling
novel 0/0. **Decided:** (1) the stick keeps sft3. (2) Across sft3 → sft4 → sft5 the pattern is
stable: rows that teach answering *from a tool result* raise open-question fabrication by 10–16
points on bluff100 no matter how the abstention share is padded — at 126M this is capacity, not
mix. **No further SFT-mix iterations on Flash.** The seeds (tool-result, spelling, skill router +
answer examples, known/unknowable GRPO curriculum) are ready for the 1B, where the trade-off is
expected to relax; the 100-sets are the yardstick there. (3) The 30-item sets are demoted to
history in every report from now on. Kept: `checkpoints/flash_sft5.pt`, GGUFs, results.

### O-38 — Honest randomness: the `dice` skill (Eric: "a local and completely honest dice roller")
**2026-09-20.** Worth it, and for the honesty reason more than convenience: a language model cannot
roll a die — it emits a plausible number that is not random. Measured on the stick model (sft3),
"Roll a d20 for me" × 40 at temperature 0.8: **a number 11 times (9 distinct values in 11 — not
uniform), no number 29 times** (the abstention training mostly declines). So the RNG-bluff rate is
27% bare and 0% with the tool. Built as `skills/dice` (`tools/roll.py`): `os.urandom` → rejection
sampling (no modulo bias) → result **with provenance** (source, the bytes used, their hash);
`seed <word>` gives a reproducible sequence labelled "SEEDED (not random)". Forms: NdS±M, coin,
range, pick, shuffle; limits 1–100 dice of 2–1000 sides. Trigger checked against the frozen suite
(0 false positives); tools 10/10, end-to-end 10/10, harness 10/10, model alone 0/10 (name never
trained; examples staged). Mouse/finger entropy: not built — the OS pool already mixes hardware
entropy; a slider is ceremony. The honest claim is "from the OS, not from the model", printed.

### D-77 — Pagouro Draws, model one: the on-stick drawing model exists and follows its caption
**2026-09-20, evening.** `scripts/build_pixel_trainset.py` → 10,256 images at 32/64 px in the HOUSE
palette with one ledger (Kenney 9,687, curated Met prints 353, D-75 candidates 192, procedural
marks 24; captions from file/pack names, titles, prompt family). `scripts/train_draw.py`: the text
model's transformer over a 32-symbol pixel alphabet — BOS, 12 caption-word tokens, SEP, 1,024 pixel
tokens, loss on pixels only; **5.5M params**, 3,000 steps of batch 16 on the desk CPU at 6.2k
tok/s (2.2 h), subject/style sources sampled 4× over tiles. Loss 6.1 → ~0.2. Samples
(`docs/samples/draw/draw1_sheet.png`): "hermit crab mark, retreated into its shell, medallion,
poster" gives the medallion arc with a coloured shell mass at the mouth, in palette, eight of eight;
"pixel sprite, tree" gives blocks; "Belle Époque print, trade card" gives texture. **Read:** the
pipeline is proven end to end — caption in, palette-legal pixels out — and the model is far too
small and too briefly trained to draw. Next: 20–50M params, 64 px, an hour of GPU when next
authorised, and the D-67 gate (40 captions) to score it. It shares nothing with the 1B run but a
transformer file. Model file: `checkpoints/draw1.pt` (not on the stick until it passes a gate).

### D-78 — House voice: BC and AD; celestial events dated as observed on Earth; the look is fixed in this version (fork to change it)
**2026-09-21, Eric.** (1) "I say BC and AD. No CE and BCE." The corpus is mixed (BC 3,116 / AD 1,190
vs CE 973 / BCE 687 in the Wikipedia slice), so the model alone would be inconsistent: the harness
rewrites the notation on output (`app/house_style.py`: 500 CE → AD 500, 300 BCE → 300 BC, 3rd
century CE → AD) — a convention, never a fact — and `sft/style_seed.jsonl` (16 rows) teaches it.
(2) "Celestial events happen on the date they were observed on Earth": for anything outside the
solar system we know the arrival of the light, not the event; answers give the observation date
and the light-time as a caveat (12 seed rows: SN 1987A, the Crab, Kepler, Tycho, GW150914,
Betelgeuse…; inside the solar system the ordinary date stands). (3) The Belle Époque look is
hard-coded for this version: `docs/STYLE_GUIDE.md` (palette hex, renderer rules, the mark, the
voice) and `docs/ABOUT_THE_LOOK.md` ("Why does everything look like this?" — with the Belle Époque
defined by quoting Wikipedia's article, CC BY-SA, attributed) ship beside the executable and in
the repository; `/about` (`/why`) prints it in the app. Want another look? Fork it (O-29: the name
only with the look). The other three palettes stay in `app/palettes.py` for forkers.

### D-79 — Documents: the harness reads PDF / Word / text, the model reads the text; and the router prompt must stay the trained one
**2026-09-21, Eric: "Will Pagouro be able to look at documents… does that happen in a 1B?"** It
happens in the harness at any size: `app/documents.py` extracts text — `.txt/.md/.csv/.json`, `.pdf`
(pypdf, BSD-3, text layer only; a scan is reported as "no usable text layer; no OCR on this
stick"), `.docx` (python-docx, MIT; paragraphs and tables) — `read_file` hands the model the first
page, files dropped in `workspace/docs/` are indexed at launch beside the packs, `/index <path>`
adds a file or folder (needs CAN ACT: it writes the text cache). Hits are labelled **YOUR DOCUMENT
<name>**. Verified end to end on a Word file and a PDF: the bilge-pump question routed to
`pack_search` and returned the right sentence from the .docx. Images and scans: not in this version
(that needs an OCR model on the stick). What a bigger model buys is a longer window, not a new
sense. **Finding on the way:** the skills-extended router prompt cost **5 of 40** on the frozen
tool-use suite (31 → 26, sft3) and pushed ordinary questions to `calc`; the app now sends the
plain prompt and grammar the model was trained on, skills are reached by their triggers, and
`PAGOURO_ROUTER_EXTENDED=1` exists for a model that has been fine-tuned on the skill examples.

### D-62b — DONE: The Stack replaced by dated, licence-checked repositories (closes D-62 (b) and O-22)
**2026-09-21, session, unattended.** `scripts/fetch_dated_code.py` + `scripts/ledger_dated_code.py`.
A hand-curated list of well-known permissively licensed repositories per language, each cloned
and wound back to **its default branch's last commit before 2022-01-01** (`git rev-list -1
--first-parent --before=2022-01-01T00:00:00Z`), its licence file read and classified **before a
byte is taken** — the licence a file *names first* is its licence; any GPL/LGPL/AGPL/MPL/BUSL/SSPL
repo is skipped and the skip is recorded — then the language's source files concatenated
(vendored, generated, minified, test-fixture and >400 kB files dropped). One `corpus.json` row
per language, `code-dated-<lang>`, carrying **every repository with its commit hash, commit date
(local and UTC), licence and licence file**, plus the skipped list. C++ added: the 1B plan's code
slice names it and the Stack rows never covered it.

| row | repos | files | chars | tokens | licences |
|---|---|---|---|---|---|
| code-dated-python | 28 | 21,689 | 198M | 65.0M | Apache-2.0, BSD, HPND, MIT, PSF, matplotlib (PSF-style) |
| code-dated-rust | 19 | 26,195 | 113M | 36.6M | Apache-2.0, CC0-1.0, MIT |
| code-dated-go | 17 | 25,149 | 173M | 63.7M | Apache-2.0, BSD, ISC, MIT |
| code-dated-solidity | 10 | 1,510 | 5M | 1.4M | Apache-2.0, BSD, MIT |
| code-dated-cpp | 21 | 17,506 | 207M | 74.0M | Apache-2.0, BSD, ISC, MIT |

240.7M tokens against the Stack's 160M; latest commit in any row 2021-12-31T23:58:47Z. The four
`the-stack-*` rows are marked SUPERSEDED (as O-22 marked the undated backbone slices) and
`published_before_generative_ai: false`; `build_mixture.py` now reads `code/<lang>.txt` at
0.07/0.03/0.03/0.04/0.03 (code share unchanged at 0.20; Solidity keeps 0.04 because it is the
subject — the file is small, so it contributes what it has). Out by licence: consul (MPL),
python-bitcoinlib (LGPL), substrate (GPL-3), aleth (GPL-3), and on the first pass ethereum/solidity,
balancer-core, ds-token, argent (GPL-3), yearn-vaults (AGPL), conditional-tokens (LGPL). Gone from
GitHub: Synthetixio/synthetix, Loopring/protocols; sushiswap's history is rewritten (nothing
before 2022). **Solidity is thin** (10 repos, 1.4M tokens): most DeFi code is GPL/AGPL/BUSL by
design, and that is the honest size of the permissive Solidity corpus, not a fetch failure.

**Three defects caught before a ledger row was written**, each of which would have passed a
casual check: (1) cpython was skipped as GPL — its PSF licence cites the GPL in a choice-of-law
clause on line 227; the classifier now takes the licence the file names first. (2) protobuf's
"last commit before the cutoff" had no `src/` — plain `rev-list` walks every merged-in ancestry
and returned a commit from the upb repository's history; `--first-parent` gives the branch's own
state. Run 2 redone from scratch for every repo. (3) matplotlib keeps a `LICENSE/` *folder*,
nlohmann/json a `LICENSE.MIT`, bevy and go-ipfs a pointer `LICENSE` naming `LICENSE-MIT`, Pillow
an HPND text that wraps mid-sentence — each a "no licence" until the reader learned the shape.
Lesson for the ledger: a licence check that reads one filename is a check of the filename.

Remaining code caveat, stated: a commit date is when the code was committed, not proof that
no line of it was machine-written; before 2022 that risk is small and the claim made is the
D-34 claim (collected/published before the cutoff), no more.

### O-39 — Design Arc (friedbeef1/design-arc): not for the console app; the tool for the D-24 browser demo and the release page
**2026-09-21, Eric: "is this at all helpful to you?"** MIT, Claude Code edition alpha. A UX-journey
method for product screens: audit the real journey, gather evidence (Mobbin screenshot library,
Apple/Material/W3C guidance), recommend one direction, design every state (entry, loading, empty,
error, success, cancel, recovery) before implementation. **Verdict:** no fit today — Pagouro's
interface is a console with a dozen states and no journey for it to audit; its evidence modes
assume a web/mobile product. **Fit later:** the browser-local public demo (D-24) and the release
page's "check a stick someone gave you" flow are real journeys with exactly those states, and the
style guide + threat-model one-liners are its inputs; reach for it then. **Taken now, by hand:**
its every-state checklist run over the console app (first launch, model file missing, packs empty,
offline notice, `/index` on a scan, a failing tool, STONE with no writable disk) — each state must
be visible and say what to do, the D-19 rule applied to everything else. Install is Eric's to run
(permission wall, as with TypeSafe). **Done the same hour:** four states fixed in `app/pagouro_app.py` — a startup failure (no model, server missing, server crashed, server silent) now prints what happened, what to do, and the server's last stderr lines, and waits for a keypress when the exe was double-clicked (the window used to close with the message); STONE on a write-protected stick falls back to SAND with a notice instead of crashing the turn; a bug inside one turn is reported and the session continues. Each state exercised with a fake server / a blocked workspace path; the normal path re-run.

### D-80 — The mark: Eric's concept #5 is the outward-facing Pagouro brand
**2026-09-21, Eric: "I have saved some beautiful artwork for the outward-facing Pagouro branding …
the one I've chosen is #5."** Ten concepts in `Pagouro_All_Concepts.zip` (kept out of the repo;
contact sheet `brand/concepts/_contact_sheet.jpg`); #5 is `brand/pagouro_mark.png`: the retreated
crab, claws folded and eyes forward, teal medallion on cream, art-nouveau corners, scallop,
"Pagouro" on a band — the D-74 look and the O-37 crab brief in one picture, so the procedural
medallion (`app/mark.py`) and the LoRA candidates step down to *studies*; the mark is this file.
Shipped: `brand/` beside the exe (full image, sizes, `pagouro.ico` as the exe icon, and a 64-px
house-palette version that `/art logo` — now the default `/art` — draws in the terminal; 32 px
tried, lettering unreadable, not shipped). README carries it; STYLE_GUIDE and ABOUT_THE_LOOK point
at the file. **Provenance (Eric, same day): generated with ChatGPT, by Eric, from his brief.** Credit line
"Eric Wade, made with ChatGPT"; the session's resizes and palette snap are mechanical and take no
credit. Rights stated without overclaiming in `brand/README.md` (OpenAI's output terms; possibly
uncopyrightable; trademark O-29 is the protection that matters). It is a brand asset, not corpus:
no ledger row, no model saw it.

### D-81 — LOCKED: context 4k in the stable phase, 8k in the decay (closes O-12)
**2026-09-21, Eric: "You asked if you can do 4K now and 8K later, yes. Consider it approved."**
The O-12 proposal as written: pretrain at 4,096, extend to 8,192 in the decay phase (RoPE
unchanged, `--seq-len` raised on resume, the model told the new max), the app sending ~4k of
recent conversation plus retrieval by default with a user override. The 1B's context on the box
is 8,192.

### D-82 — LOCKED: the 1B runs on RunPod; io.net declined for this job, and the reasoning goes in the book (closes O-31)
**2026-09-21, Eric: "your analysis of why io.net might not be our best bet is cogent and should
be part of the book, too. I would have liked to use it, but not at the expense of the job … start
on runpod. I will add money to it right now."** `docs/GPU_PROVIDERS.md` is the analysis: RunPod's
head start is proof, not code; io.net as documented on 2026-09-21 prepays a chosen duration,
has discontinued self-serve bare metal, documents neither persistent storage nor what happens
to the disk at expiry, and does not confirm an 8×H100 single host — three unknowns a marketplace
should not be carrying under a four-day eight-card job. vast.ai stays for shakedowns and single
cards. The decision is the *job's*, not the story's; the story (paid in USDC on a decentralised
network) is deferred to a run that can afford to be interrupted, and the book tells why (Chapter
11's do-it and the 1B chapter). **This is the launch (D-54):** the plan and hourly prices are
posted on #2 before any `create-pod`; **the cap is $1,500** (Eric, 2026-09-21 15:30 PT: auto-reload off, $1,350 added to $150 — fixed, not
refilling, because a refilling balance has no cap); every artifact comes home before a pod is deleted;
`list-pods` empty at the end of every step. At $1,500 the secure estimate ($1,740–2,440) does not fit:
the first hour on the real pod measures MFU and posts the projected total; community cloud ($2.69/h,
$1,340–1,880) or a top-up is Eric's call then. Pod watch every 30 minutes (session cron), posting on #2
only on change. **Every status update opens with GREEN / YELLOW / RED** (Eric, 2026-09-21 18:25 PT): GREEN
on plan, nothing needed; YELLOW an issue being solved or a decision Eric will need to make soon, with
its deadline; RED something not working or a guardrail at risk, with what was done.

**Launch shape as executed** (revising `docs/JOB_1B.md` where measurement forces it): the data
on disk today is 0.57B live tokens against a 100B plan, so the first step is the **data volume
build on a CPU pod** — dated FineWeb-Edu at scale (the fetcher already filters on dump date),
the full 2021-12-20 Wikipedia dump, the code recipe scaled by repositories (D-62b's script, a
longer list), Stack Exchange from the dated archive dump if the fetcher lands in time. The
mixture shares are re-stated from what is actually fetchable with epochs written on the row
(no slice replayed more than ~3×; canon and shelf live in the decay only), and posted on #2
before tokenization starts.

### D-83 — LOCKED: no watermark, no claim on outputs — "your words are yours" — and the WHY page
**2026-09-21 night, Eric:** the O-40 argument becomes the "why does the world need another AI,
least of all a 1B" collateral, and one more claim joins it: Pagouro does not watermark output,
cannot be made to once frozen (a fork could, and then it is not Pagouro — its manifest will not
match), and claims no rights in what it writes for you — "another version of privacy and
ownership … it's binary: you either are being watermarked or you aren't." `docs/WHY.md` carries
it, worded to the D-50/THREAT_MODEL rule: three checkable parts (no marking code — read it; frozen
and signed — cannot be added; no rights asserted by the project) and one thing we do NOT say
(that output is free of anyone's rights — a model can reproduce a sentence it read; the user
checks what they publish). Box language moves from "open" to **licensed, dated, honest, finished
— and your words are yours**. Feeds README first paragraph (F12), MANIFESTO, book chapter 0/1. **Same night, Eric:** a plain-language
walkthrough of checking a copy — what a hash is, the signed manifest, the Bitcoin anchor, what each
step proves and does not — `docs/CHECK_YOUR_COPY.md`, shipped on the stick (THREAT_MODEL requirement 5
made readable; "it adds to our authenticity").

### D-84 — Wikipedia leaves the 1B backbone (Eric: "if there is a way we can build this without using Wikipedia, I would be perfectly fine with that")
**2026-09-22, during the volume build.** The range-request sampler could not fetch the whole
2021-12-20 dump in useful time; a local-parse fix was written, tested and the 20 GB dump had in
fact finished downloading — and Eric chose to drop the source rather than wait. Trade stated:
Wikipedia was ~4–5% of the plan and the densest plain-fact source, so answered-real may come in a
little lower; FineWeb-Edu carries much encyclopaedic text; the calibration set measures the
difference. Gained: the volume is ready when the Stack Exchange and code shards land; one fewer
share-alike source in the backbone (Stack Exchange still is, so the weights stay CC BY-SA). The
desk's 100M-token slice (`wikipedia-en-20211220`) stays in the ledger and out of the 1B mixture;
`--local` mode stays in the fetcher for anyone who wants it back.

### D-85 — The 1B run started 2026-09-22 08:48Z on 8×H100 SXM secure (pod g3qf86spkqfq1j, CA-MTL-1, $27.92/h)
**Measured on the rehearsal:** 968,968,192 params (ffn 5632 by the 8/3 rule — the plan's 6144 was a
guess); 1,048,576 tokens/step = 4 × 4096 × accum 8 × 8 ranks (micro-batch 8 OOMs 80 GB); plain bf16
318,660 tok/s = 23.4% MFU; torch.compile ≈444k tok/s = 32.6% MFU (2.36 s/step); val ppl 226 at
step 200; checkpoints 11.6 GB every 500 steps; volume sha256 4a60a5ff… verified after a 16-stream
cross-DC pull (single stream 16 MB/s; 11 of 16 streams survived sshd's MaxStartups, the 5 dropped
chunks refetched by per-chunk hash). Run: 95,104 steps, WSD, warmup 2k, stable to 85,593, decay at
8k on the mix. **Projection $1,800 vs $1,440 cap remaining.** Started anyway because a WSD run can
decay from any stable checkpoint: the cap-conformant finish is an early decay at ~$1,100 spent
(~59B tokens); a ~$500 top-up buys the full 100B. **Eric, 2026-09-23 03:2xZ: "I added $500 to RunPod, go for the full 100B" — cap $2,000, the
full 95,104 steps stand, the early-decay rule is retired.** Nine hours of stock
checks preceded it (secure 8×H100 Out on 17 of 19 reads; the community "Low at 8" was a phantom —
community H100 hosts allow 1 GPU per pod). Wikipedia out (D-84); mixture on the row: FineWeb-Edu
91.6%, Stack Exchange 7.7%, dated code 0.7% ×3 epochs.

### O-41 — The "hybrid": a 1B model plus a verbatim shelf (Eric: "1B of normal and 300 MB of verbatim … the US Code as it is written")
**2026-09-23.** It exists and Pagouro already is it (D-9): the weights are the lossy half, the
packs are the exact half, searched at question time and quoted with their source. Research that
bakes retrieval into the architecture (RETRO 2021, kNN-LM, Meta's memory layers 2024) still keeps
the text outside the weights; nobody stores 300 MB losslessly inside a transformer, and memorised
text without a source is the bluff machine. **Candidate:** the US Code (US Government work, public
domain, dated; uscode.house.gov publishes per-title XML/text) as a shelf pack with a ledger row —
needs a packaging-time search index (today's index is built at launch, ~0.3 s per 1.5 MB; 300 MB
wants it prebuilt). Honest box line: *a 1B model that reads out of a 300 MB shelf it can cite* —
the true form of the "1B+" question. Waiting on Eric's "add it".

### O-42 — A stablecoin wallet for compute bills (Eric: "if RunPod accepted stablecoins, could I have set you up with a wallet and you pay the bill as needed?")
**2026-09-23.** Mechanically yes (a key held by reference, a pay-invoice script, a provider that
takes USDC — io.net does, RunPod does not). What changes is the cap: today the loaded balance IS
the guardrail. Design if ever done: **fixed-balance wallet funded by Eric, never refillable by the
session; small payments unattended, payments above a threshold co-signed by Eric** — the current
rule in different clothes, plus a public on-chain receipt for every payment (fits the manifest
posture; a line for the book). Not "pay as needed": the judge of "needed" must not be the spender
(the disk-filling rsync is the reminder). Risks stated: a hot key on a compromised endpoint (threat
model row 5), a spending bug drains a wallet as fast as a card, accounting is Eric's. Deferred until
a provider we would actually use takes stablecoin for a run that can afford interruption (O-31).

### O-40 — OLMo (AI2) and Common Pile: why Pagouro is not redundant, and what to borrow
**2026-09-21 night, Eric: "Is it even worth it for me to continue investing in Pagouro if we're up
against a benefactor like Paul Allen?"** OLMo releases everything (weights, Dolma, code, logs,
checkpoints; OLMo 3's full "model flow"). On capability Pagouro loses and Chapter 1 says so. The
pitch is four claims OLMo does not make and structurally cannot at web scale: **licensed** (a
nameable licence per source, not an open licence on a crawl), **dated** (every row before
2022-01-01), **honest** (a pre-registered frozen bluff test as the headline number, answered-real
beside it), **finished** (a frozen, signed, offline artefact with a threat model, for a person).
The honest neighbour is **EleutherAI's Common Pile / Comma v0.1 (2025)** — an openly licensed
corpus and models trained only on it — and it is an opportunity, not a threat: its licensed
sources can feed ours where their dates allow. Verdict: continue; move the box language from
"open" to *licensed, dated, honest, finished*; add Common Pile to the sources to check (date
basis per sub-source, O-22 rules). The other half of the investment — the book — is not a thing
AI2 will write.

### O-31 — io.net reconsidered: raw GPU clusters, tested the same way as RunPod
**2026-09-19, Eric.** D-54's rejection covered io.net's Training-as-a-Service (form-based
fine-tuning, no from-scratch). Its raw GPU clusters were not evaluated. Reconsider on the same
discipline: a ~$1 shakedown (bundle, 300 steps, checkpoint, resume, tokens/s), then a one-hour
DDP rehearsal, before it can be a candidate for the 1B. The risk is node churn during a
multi-day multi-GPU job, not price; the story is worth telling only if the run survives.
**2026-09-21 update (Eric: RunPod vs io.net vs vast.ai — "what do you think?"):** `docs/GPU_PROVIDERS.md`.
The RunPod head start is proof, not code (a day of plumbing to move; the shakedown+rehearsal ≈ $30 to
re-earn). io.net's docs as of today: H100 SXM $2.10–3.50/GPU-h, IO/USDC-on-Solana or card, clusters
**prepaid for a chosen duration**, self-serve bare metal discontinued 2025-10-01, persistent storage
and disk-at-expiry **undocumented**, 8×H100 single host not confirmed. vast.ai: $1.73, stranger's
machine, instance disk. Verdict: try io.net on the O-31 discipline for the story's sake; the story is
told only if the run finishes there; vast.ai for shakedowns and single cards only.

### O-32 — Compute-for-receipt (not licence) for a model beyond 1B; the number first
**2026-09-19, Eric:** after the 1B proves the method, fund a 30B/72B by trading H100 time for a
tokenised "$200 lifetime licence" ($100 of compute → one licence, resellable). Session's
assessment: the core is sound (compute delivered before anything is issued); the instrument
is wrong under our own rules — D-31 and the corpus's share-alike inputs make the weights CC
BY-SA, so a licence cannot be exclusive and is worth nothing at release. The honest instrument
is a **receipt**: proof of contribution, name in the manifest, early checkpoint access, a vote on
the shelf, transferable, never sold as a right to what everyone gets. The scale: 72B at ~1.4T
tokens ≈ 6e23 FLOP ≈ ~1M H100-hours ≈ ~$3.5M (35,000 contributors at $100); 30B ≈ $600k; **7B
≈ $60–80k and is the realistic next step**, where the receipt model would be tested first.
Securities counsel before any transferable token. Nothing built; contemplation only, per Eric.

### O-33 — Secret / NEAR, Cartesi, Mina: three uses that fit inside D-14 and the threat model
**2026-09-19, Eric's questions.** (1) **Secret Network / NEAR** (TEE confidential compute): a
third mode, CONFIDENTIAL — an ONLINE tool where the query leaves the machine encrypted to an
attested enclave; privacy from the provider, not from the network, and only as strong as the
enclave vendor. Offered, if at all, as a documented `online.json` option with that wording; never
the headline (THREAT_MODEL governs). (2) **Cartesi**: not for inference (emulated RISC-V is minutes
per token) but for **verifiable evaluation** — the frozen suite run against the signed GGUF inside a
Cartesi machine so the numbers on the box are proven computations; a post-1B lighthouse item.
(3) **Mina**: a mirror anchor for the manifest hash whose ~22 KB recursive proof fits on the
stick, so `verify_manifest.py` could confirm the release fully offline; Bitcoin stays the anchor
(D-14), Mina a documented mirror; depends on shipping a small enough verifier. None of the three
becomes a fourth pillar; all three are options and mirrors.

### O-34 — Note: the "local AI business" thread (noisyb0y1, 2026-09-19) — market yes, numbers no, offline undercut
**Eric asked.** The article's market observation is real and matches our third claim (small
regulated businesses want AI that keeps data in the building at a predictable cost); its tool
stack (Ollama, AnythingLLM, Open WebUI, n8n) is the integrator's architecture of other people's
models with unknown corpora; its revenue math is fantasy; and its "offline" is undercut by routing
the hard 20% to a cloud API — the quiet hybrid our OFFLINE/ONLINE switch and exit line make
visible. Takeaways: (1) audit is the sell to those clients — labelled pack hits + the ledger,
which that stack lacks; (2) an "integrator kit" framing for MAKE_IT_YOURS + packs + skills; (3) a
plain offline web UI as a later item for non-technical users. Nothing to build now.

### O-35 — Jev / "System One" models: validation, not displacement; make the router a calibrated typed decision (with O-15)
**2026-09-19, Eric: "is there a chance we're building something nobody will want in a month?"**
Jev (TypeSafe, early access 2026-09-15) returns typed decisions with calibrated probabilities
from an option set supplied by the caller — no free text, so it cannot hallucinate; hosted, closed,
per-token. It takes the routing/classification slice of agent work; it cannot explain, summarise
or converse. Pagouro's grammar-constrained router already is a typed-decision component in front
of the language model. Assessment: no displacement; $40M of validation for "calibrated, says no
when it can't"; ours is the offline/open/ledgered form Jev cannot be. Action for the 1B (a
session, no GPU): router emits a probability with its choice; the O-15 answerability gate as a
typed decision before prose; calibration measured on the frozen suite. Real risks remain: a big
lab shipping a small open *ledgered* model (they cannot ledger), attention.
**First measurement, 2026-09-20 (`evals/run_tooluse.py --probs`).** The router's probability is
read from llama-server's per-token logprobs at the tool-name token under the grammar (the raw
distribution; alternatives include non-tool tokens, so a normalised-over-tools value is stored
too). Flash sft2 on the frozen 40-item suite: mean p(chosen tool) **0.917 when right (n=33) vs
0.816 when wrong (n=7)**; accuracy by bin <0.5: 0/1, 0.5–0.9: 9/11, ≥0.9: 24/28. Signal exists,
but the model is overconfident at the top and a threshold would not separate the seven errors.
No calibration claim; re-measure at 1B, and try the normalised value and a temperature fit
(learned on the GRPO big set, tested on the frozen suite) before the O-15 gate is built on it.
**D-66 audit note (2026-09-19, from Rahul's guide via Eric — "track numeric strings separately;
never auto-correct numbers"):** `scripts/numeric_drift.py` compares the numeric strings of the old
archive.org OCR and the re-OCR per work. Disagreement (share of numbers present on one side only):
NEETS 13 15%/19%, NEETS 01 14%/9%, NEETS 02 38%/12%, USDA 3%/17% (old/new). Mostly coverage, not
conflict: the old OCR transcribed chart axis ticks as text (NEETS 02's "0.1…0.9" ×75), the new one
ignores figures but recovers table cells the old one dropped (USDA's jar sizes and the 6,000-ft
altitude thresholds). Next refinement: a per-page diff to list true value conflicts (45 vs 4.5) for
review. Also adopted from the guide: a numeric-preservation column for the tool-use and memory
evals (numbers in an answer must appear in the tool result).
**D-66 audit, 2026-09-20 — the per-page diff found a real defect, and it was ours.**
`numeric_drift.py --conflicts` (ordered-number alignment, context-gated near-miss pairs) listed a
canning process time that the two scans disagreed on (40 vs 20 min, USDA page 3-12). The page image
says 85 min, and the re-OCR's text for that leaf carried page 3-8's numbers under 3-12's headings.
`scripts/reocr_footer_check.py` (printed page numbers must run in order) then showed the pattern:
**the first two leaves of every 8-page batch begin with their own page and continue with the text
of the previous batch's leaves 4–5** — footers prove it (NEETS 1 leaf 22 = page 1-11, ends "1-7").
Positions 2–7 check clean. So ~25% of pages in every batched work were fluent, plausible and
wrong — the one failure the re-OCR was bought to remove, and worse than garble because it reads
well. The stick was not touched (stage 11 had not been re-run), the ledger rows were. Fix: a
two-leaf unbatched test came back clean (1-11, 1-12 with the right captions); `scripts/reocr_fix.py`
redoes every batch-position-0/1 leaf plus every leaf whose ending is a verbatim copy of an earlier
page, one page at a time, then reassembles; all six works re-fetched and re-ingested after it
(~900 pages, ≈$1 more, inside the $10 ceiling). Rules from it: batched vision-OCR output is not
trusted until a page-order check passes; the check ships with the ingest; and the ledger row for a
re-OCR'd work names the check and its result.
