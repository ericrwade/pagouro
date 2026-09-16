# Corpus plan (milestone 3)

Drafted 2026-09-16 during the unattended window. **Design only — no bulk data was downloaded.**

Every licence below was checked against the source's own metadata on the date shown, not recalled.
Where a licence could not be verified, the source is marked BLOCKED and stays out. When rights are
unclear the answer is no; that rule is the entire differentiator (`CLAUDE.md`).

---

## 1. Licence verification, 2026-09-16

| Source | Declared licence | Gated? | Verdict |
|---|---|---|---|
| `HuggingFaceFW/fineweb-edu` | **ODC-By 1.0** | no | **CLEAR** |
| `allenai/dolma` | **ODC-By 1.0** | no | **CLEAR** |
| `wikimedia/wikipedia` | **CC BY-SA 3.0 + GFDL** | no | clear, but share-alike — see §3 |
| `HuggingFaceH4/stack-exchange-preferences` | **CC BY-SA 4.0** | no | clear, but share-alike — see §3 |
| `codeparrot/github-code-clean` | **Apache-2.0** | no | **CLEAR** — the code slice |
| `bigcode/the-stack-dedup` | "other" | **yes, auto** | **BLOCKED** — see §2 |
| `bigcode/the-stack-v2` | "other" | **yes, auto** | **BLOCKED** |
| `bigcode/the-stack-smol` | none declared | **yes, auto** | **BLOCKED** |
| `bigcode/starcoderdata` | "other" | **yes, auto** | **BLOCKED** |
| Project Gutenberg (HF mirrors) | none declared on any mirror found | no | **BLOCKED** — see §2 |

A streaming attempt against `the-stack-smol` returned, verbatim:
`DatasetNotFoundError: ... is a gated dataset on the Hub. You must be authenticated to access it.`

## 2. Blockers for Eric

### 2a. The Stack is gated and needs terms accepted

Every BigCode code dataset requires authentication *and* acceptance of a licence agreement on the
Hub. **Accepting a licence agreement is a decision for Eric, not for an unattended session**, so
this stopped here rather than being worked around.

`D-8` and `PAGOURO_BRIEF.md` §6 both name The Stack as the code slice. Two ways forward:

1. **Eric accepts the terms** on the Hub and sets `HF_TOKEN`. Then read the agreement carefully,
   because its opt-out provisions and attribution requirements need a ledger row of their own.
2. **Use `codeparrot/github-code-clean` instead.** Apache-2.0, not gated, filtered to permissive
   licences. Slightly less curated than The Stack, and the licence position is simpler to state,
   which for this project counts for a lot.

Recommendation: option 2 unless Eric wants The Stack specifically. A corpus whose licence story
fits in one sentence is worth more here than marginal data quality.

### 2b. Project Gutenberg has no clean packaged source

Gutenberg *texts* are public domain. That is not the question. The question is whether a given
**packaged copy** is redistributable, and no Hugging Face mirror found declares a licence at all.
Gutenberg's own site also restricts automated bulk downloading of the site itself, separately from
the copyright status of the books.

Do not use an undeclared mirror. Options, in order of cleanliness:

1. Gutenberg's official mirror sites, which exist precisely for bulk access and publish terms.
2. The Gutenberg CD/DVD archive images.
3. Build the slice from a per-book list with each book's PD status recorded individually. Slowest,
   strongest ledger.

This slice is worth the trouble: per D-10, the classical liberal canon is the *spine* of the domain
corpus and almost all of it lives here.

## 3. The share-alike question is now concrete (O-11)

Wikipedia is CC BY-SA 3.0 plus GFDL. Stack Exchange is CC BY-SA 4.0. Both are share-alike, and
together they are roughly 30% of the mixture the brief proposed.

Whether model weights are a derivative work of their training text is genuinely unsettled. Most
open models never address it and are not asked, because they make no provenance claims. Pagouro
will be asked, because it holds up a ledger and invites the question.

**This needs an answer before the full run, not before release**, because the answer may change the
mixture. The three defensible positions are in O-11. What is not defensible is not having thought
about it.

## 4. Proposed mixture

Follows D-9 strictly: **the pretraining mix is optimised for reasoning, not for domain.** Domain
knowledge arrives in the anneal and the ethos arrives in fine-tuning. Loading domain text into
pretraining costs reasoning and buys little.

### Stage 1 — pretraining, ~90% of tokens

| Slice | Source | Share | Licence |
|---|---|---|---|
| Educational web | FineWeb-Edu | 45% | ODC-By |
| General web / books / mixed | Dolma | 20% | ODC-By |
| Code | `codeparrot/github-code-clean` | 15% | Apache-2.0 |
| Encyclopedic | Wikipedia | 10% | CC BY-SA — pending O-11 |
| Expert Q&A | Stack Exchange | 10% | CC BY-SA — pending O-11 |

Code is weighted at 15% rather than the brief's 10% because it is one of only two known
reasoning-boosters and the M4 ablation will test exactly this.

### Stage 2 — anneal, final ~10% of tokens

Where the domain actually lands.

| Slice | Content | Share of anneal |
|---|---|---|
| The canon | Smith, Ricardo, Bastiat, Mill, Locke, Hume, Tocqueville; Austrians where openly licensed | 35% |
| Chain source and protocol docs | Bitcoin Core and major implementations, permissively licensed | 20% |
| Founding and legal documents | Constitution, Federalist Papers, US Code — public domain | 15% |
| Highest-quality educational web | top-scoring FineWeb-Edu | 20% |
| Contemporary voice | bitcointalk, subject to its terms | 10% |

### Stage 3 — SFT

Ethos, abstention, tool use, retrieval discipline. Not a corpus slice. Partly blocked on O-7; the
hand-written portion is not and is being started now.

### Not in training at all

Whitepapers (copyrighted, mostly unlicensed — retrieval pack per D-10), Eric's book (retrieval and
SFT derivation only, pending O-8), the newsletters (excluded absent written permission), Reddit
(never, D-16).

## 5. Storage and streaming

Per `ENVIRONMENT.md` Finding 2: **stream and tokenize on the fly; never land raw corpus on disk.**
Raw FineWeb-Edu and Dolma dwarf their tokenized output, and only the uint16 result is needed.
`scripts/fetch_data.py` already streams.

At 100B tokens the tokenized corpus is ~200 GB against 1,329 GB free. No new storage required.

## 6. What to do next

1. **Eric:** decide The Stack versus `github-code-clean` (§2a).
2. **Eric:** answer O-11 before the full run (§3).
3. **Session:** resolve a clean Gutenberg path (§2b) and write its ledger rows.
4. **Session:** build the mixture sampler, and extend `fetch_data.py`'s licence gate to cover every
   source above so an unlicensed one cannot enter by accident.
