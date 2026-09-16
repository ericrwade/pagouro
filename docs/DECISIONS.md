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
| O-7 | Is teacher output from a hosted API licensed for training use? | **all synthetic data (SFT stage)** | Open weights being MIT does not mean API output carries the same permission. OpenRouter's terms and the upstream provider's terms are both in the path. Resolve in writing before generating a single synthetic example. The whole provenance claim rests on it. |
| O-8 | Publisher permission for Eric's book | its inclusion | Ask narrow: training corpus plus Q&A derivation, with ledger attribution. NOT verbatim retrieval redistribution. See D-15. |
| O-9 | Which small-vocab tokenizer | milestone 1 config | Custom BPE with tool tokens, or an existing permissive one under 65,536. See D-7. |
| O-10 | Which three chains, and the disclosure text | release | Merit-based pick, full holdings disclosure, published cost comparison. Cap at three. See D-14. |
| O-11 | Does training on CC BY-SA content oblige share-alike weights? | weight licence choice | Wikipedia and Stack Exchange are both CC BY-SA and together are ~30% of the proposed mix. Legally unsettled; most open models ignore it. Pagouro cannot, because provenance is the product. Needs a stated position before release, ideally before the full run. |
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
