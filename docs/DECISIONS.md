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
