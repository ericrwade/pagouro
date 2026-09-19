# Chapter 4 — Do it: a corpus you can defend

*Licence: CC BY-SA 4.0 (instruction strand / generated appendix, D-64).*

*DO-IT chapter, draft 1 (2026-09-18). Every number here comes from `corpus.json` or a script in
the repo on that date; footnotes name the file.*

---

There is a file in the Pagouro repository called `corpus.json`. It is 62 rows long.[^1] Each
row is one source of training text and says where it came from, who holds the rights, what
licence or public-domain basis lets us use it, when it was published, how many tokens it
contributed, what we did to clean it, and the SHA-256 of the bytes that actually went into the
model. Add the rows up and you get 493 million tokens. Remove any one of them and the model you
would train is a different model, and the file tells you exactly which.

The big labs cannot publish this file. Not "choose not to" — cannot. Their models were trained
on crawls of the open web, on books whose provenance is a court case, on data from other models.
There is no row they could write for most of it. That is the whole reason a one-person project
on a desk computer has anything to say to them: the ledger is not a feature of Pagouro, it is
the thing the rest of Pagouro is built around.

This chapter is how you make one. It is less work than it sounds, and the work is front-loaded:
every source costs you ten minutes of reading a licence page before it costs you any bandwidth.

## The rule

One sentence, and it is the only sentence that matters:

> No byte enters the corpus without a licence you can name, written on a row, before the
> download starts.

Three consequences fall out of it, and we hit all three.

**"Unclear" means no.** Not "probably fine", not "everyone uses it". When we could not find a
licence line for a translation of Bastiat's *The Law* (the only Gutenberg edition is a 2007
translation under an unspecified Creative Commons variant), it stayed out, and the book we
wanted was replaced by one we could name.[^2] When OpenStax turned out to have moved its
textbooks to a NonCommercial licence, out.[^3] The temptation to argue is real — "CC licences
are irrevocable, the old edition was CC BY" — and the argument may even be right. It is still
an argument, not a licence line, and a stranger checking your ledger should not have to
adjudicate arguments.

**NonCommercial and NoDerivatives are out**, whatever you think of your own intentions. A model
is a derivative of its training data in every sense that matters to a licence, and you cannot
promise what someone will do with your weights after you release them. If your weights are
going to be CC BY-SA (ours are), every input has to be at least that free.

**Every row needs a basis, not a vibe.** "Public domain" is not a basis. "Published 1859, author
died 1873, life+70 expired 1944, Project Gutenberg #34901 marked public domain in the USA" is a
basis. "US Government work, 17 U.S.C. §105, archive.org item carries the Public Domain Mark, no
copyright notice in the text (checked)" is a basis. The difference is that the second kind can
be wrong in a way someone can point at.

## What a row looks like

Here is one, lightly trimmed, for a manual that went on the shelf last night:[^4]

```json
{
  "slug": "usgov-faa-phak",
  "name": "Pilot's Handbook of Aeronautical Knowledge (FAA-H-8083-25A)",
  "source": "archive.org OCR text",
  "author": "US Federal Aviation Administration",
  "url": "https://archive.org/details/PilotsHandbookOfAeronauticalKnowledge",
  "license": "Public domain (US Government work, 17 U.S.C. 105)",
  "public_domain_basis": "Work of the US Federal Aviation Administration (Flight Standards Service); archive.org item carries the Public Domain Mark; FAA publications are US Government works",
  "first_published": "2008",
  "published_before_generative_ai": true,
  "retrieved_utc": "2026-09-19T00:18:41+00:00",
  "characters": 1565066,
  "estimated_tokens": 419501,
  "cleaning": "homoglyph map + drop lines >5% non-ASCII + whitespace",
  "cleaning_detail": {"lines_dropped_non_ascii": 421, "lines_kept": 69604},
  "sha256_processed": "938636b7700e…",
  "file": "data/raw/usgov/faa-phak.txt",
  "slice": "shelf (D-58): anneal-only flavor"
}
```

Read it as a stranger would. Where did this come from? A named archive.org item. May we use it?
Named statute, and the archive's own rights mark. When? 2008 — before 2022, which matters in a
moment. How much of the model is it? 419,501 tokens, under a tenth of a percent. What did you
do to it? Dropped 421 lines of OCR garbage out of 70,025, and said so. Is this the exact text?
Here is its hash; the file is in the repo's data folder; check.

The `slice` field is the one people miss. It says *where in training* the source goes — the
pretraining backbone, the anneal (the last tenth of training, where flavour lives), or, for
this one, the "shelf" of small licensed works that get spread thin through the anneal. We will
come to why that matters in Chapter 6; for the ledger it is enough that the row says it.

## The "before generative AI" line

One field above deserves its own paragraph: `published_before_generative_ai: true`. Every row
in the ledger is dated, and every date is before 1 January 2022.[^5]

The reason is not nostalgia. After 2022, an unknown and growing fraction of the text on the
internet was written by language models. Train on it and you are training on your
predecessors' habits, including their bluffs, and nobody can tell you how much. The frontier
labs cannot make the pre-2022 claim; they trained on the post-2022 web. We can, because the
corpus is small enough to date by hand.

Be precise about what the claim is. It is: *every source was collected or published before
2022-01-01, and the date is on the row.* It is not: *the corpus contains no machine-generated
text.* A 2021 crawl date is when a page was fetched, not written, and we say so on the box.
Overstating this would be exactly the kind of unearned claim the rest of the project refuses
to make.

For sources that live in version control this claim can be made airtight instead of merely
honest: take the repository at its last commit before the cutoff and write the commit hash on
the row. Our Bitcoin and Ethereum improvement proposals were taken that way — commits from
25 and 30 December 2021, hashes on the rows — so the "before 2022" claim for them is a fact
about a git object, not about our diligence.[^6]

## Where to get text you can name

In rough order of how much we got from each.

**Curated open datasets** (most of the tokens). FineWeb-Edu is a filtered educational slice of
the web under ODC-By; Wikipedia is CC BY-SA; The Stack is source code with per-file licence
metadata and an opt-out registry; Stack Exchange is CC BY-SA. Between them these are 450 of our
493 million tokens.[^7] The rule for this tier: use a dataset whose curators already did the
licence work and *published* it, and record their licence statement on your row. Do not
assemble your own web crawl; you will not be able to write the rows.

**Project Gutenberg** (the canon and most of the shelf). Public-domain books, one row each,
with a per-edition basis — not "it is on Gutenberg" but *which* translation, *when* the
translator died. The one wrinkle: the Project Gutenberg *trademark* is restricted even though
the text is free, so the fetch script strips their header and footer and drops any line naming
the trademark, and the row records how many bytes that was.[^8] Gutenberg asks not to be
crawled in bulk; fetch books one at a time, slowly, and use a mirror if you want hundreds.

**US Government works** (the technical shelf). Anything written by a federal employee in the
course of their job has no copyright in the United States. Field manuals, flight handbooks,
the Navy's electronics course, the Army's recipe service, the traffic-sign manual, NASA's own
histories. Archive.org holds scans with OCR text, often with a Public Domain Mark on the item;
NTRS holds NASA's. Two cautions: contractor-written government publications are a grey area
(we took the two NASA histories because they were printed by the Government Printing Office
before 1989 with no copyright notice, which is public domain on its own terms, and said so on
the row); and OCR text needs cleaning and the cleaning needs stating.[^9]

**Open specifications.** Standards bodies and protocol communities often require a permissive
licence per document (the Bitcoin proposals require a licence header; the Ethereum ones require
a CC0 waiver sentence). Check *each document*, not the repository: 30 of 153 BIPs had no
licence header and were dropped.[^6]

**Your own generated data**, if you use a teacher model, is a source too, and it needs a row
like any other: which model, under what licence (ours was Apache 2.0 open weights, run
locally), how the outputs were filtered, how many survived. The row for our synthetic
tool-use conversations says all of that and marks them synthetic, because a reader deciding
whether to trust the "before 2022" claim needs to know these were written in 2026 by a
machine, on purpose, and never counted toward that claim.[^10]

## The tools, and what they refuse to do

Three scripts wrote the 62 rows, and the useful thing about each is what it will not let you
do.

`scripts/fetch_data.py` pulls a Hugging Face dataset and writes its row. It reads the
dataset's licence field first and **refuses to download anything without one.** That single
refusal is most of the ledger discipline; the rest is habit.

`scripts/fetch_gutenberg.py` takes an ebook number and requires `--pd-basis` and
`--published` on the command line. It refuses any publication year of 2022 or later, strips
the Gutenberg boilerplate, counts the trademark mentions it removed, hashes the result, and
writes the row. If you cannot fill in the basis, you cannot run the command, which is the
point.

`scripts/ledger_add_text.py` is for text you fetched some other way (archive.org OCR, a
specification dump). It cleans — maps Cyrillic look-alike letters that OCR produces back to
Latin, drops lines that are more than 5% non-ASCII, collapses whitespace — and **writes the
cleaning statistics onto the row**, so "we cleaned it" is a number, not an adjective. It
requires the same licence, basis, author, year and URL fields.

None of them lets you write a row by hand, and you should resist doing so. A hand-written row
is exactly as trustworthy as a hand-written hash.

## What you should see

After your first three sources — say one Gutenberg book, one government manual, one Hugging
Face dataset — `corpus.json` has three rows, each with a hash, and `data/raw/` has three
files. Then run the one check that makes the ledger worth anything:

```
python scripts/verify_ledger.py
```

It hashes every file and compares it to its row. What you should see is every row matching and
the line `VERDICT: the ledger matches the files`.

What we saw, the first time we ran it, was 38 of 54 rows *not* matching.[^11]

This was the evening of the eighteenth of September, sixty-two rows in, while writing this
chapter. The Gutenberg fetcher hashed the text it held in memory and then wrote that text to
disk with one extra newline at the end. Every book row for two days had carried a hash that no
file on earth would produce. Nothing about the model was wrong; the ledger's promise was — the
promise that a stranger can check. Nobody had run the check, because the check did not exist
as a command; it existed as a belief that the script was fine.

The fix took ten minutes: hash the file as written, re-hash the 38 rows from disk, write the
check as a script, and put this paragraph here. That order is the lesson. If a claim matters,
the thing that verifies it has to be a command someone runs, not a sentence someone trusts —
including you, including us. The ledger is only as good as `verify_ledger.py`, and it was only
that good starting on day eight.

Then look at your smallest source and ask whether you could explain its row to someone
hostile in one breath. If not, delete it. There will be another one.

---

[^1]: `corpus.json`, 62 rows on 2026-09-18: 36 shelf works, 14 domain-canon works, 8 backbone
datasets, 3 synthetic/derived rows, 1 retrieval-only pack. Token total 492,942,750 as summed
from `estimated_tokens`.
[^2]: `docs/DECISIONS.md` O-14; the substitute was *Economic Sophisms* in the Stirling
translation, translator d. 1891.
[^3]: `docs/DECISIONS.md` D-58 shelf log, 2026-09-18, citing OpenStax's licensing help page.
[^4]: `corpus.json` row `usgov-faa-phak`; hash abbreviated.
[^5]: `docs/DECISIONS.md` D-34, locked 2026-09-16.
[^6]: `scripts/fetch_bips_eips.py`; rows `specs-bips-2021` (commit `ae747e2b…`, 123 of 153
documents kept) and `specs-eips-2021` (commit `1ed32a1f…`, 355 of 406 kept).
[^7]: Rows `fineweb-edu-sample-10BT` (179M), `wikipedia-20231101.en` (96M), the four
`the-stack-*` rows (160M), `stackexchange-preferences` (17M).
[^8]: `docs/DECISIONS.md` D-32, quoting Project Gutenberg's permissions page.
[^9]: Rows `usgov-nasa-sp4201`, `usgov-nasa-sp4205` (basis: GPO, 1966/1979, no notice);
cleaning stats on every `usgov-*` row, 0.1–3.7% of lines dropped.
[^10]: Row `harness-synthetic-qwen2.5-7b`, written by `scripts/ledger_synthetic.py`.
[^11]: `scripts/verify_ledger.py`, first run 2026-09-18 evening: 16 match, 38 mismatch (all
`gutenberg-*` rows plus one stale synthetic row), 8 large files skipped; after the fix, 62 of 62.
The fetcher fix and the re-hash are in the same commit as this chapter draft.
