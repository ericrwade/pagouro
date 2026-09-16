# Proposal: restrict the corpus to text written before generative AI

Eric's idea, 2026-09-16. **Not yet decided — O-14.** This is the case for and against.

## The idea

Include only material published before large language models were widely available, so the corpus
is human-written with high confidence. A practical cutoff is **1 January 2022**, before ChatGPT's
launch made generated text common on the open web.

## Why it is stronger than it first sounds

**It is a claim nobody else makes, and it is checkable.** Every frontier lab trained on web data
scraped after 2022 and none of them can say what fraction is machine-generated, because nobody
knows. "Every token in this model predates generative AI" is a sentence no large lab can write. It
sits alongside the provenance ledger as a second structural advantage rather than a marketing line.

**It addresses a real and documented problem.** Training on model output degrades models — the
effect is well studied and known as model collapse. Post-2022 web corpora are contaminated to an
unknown and growing degree. Avoiding it entirely is a defensible engineering decision, not just a
philosophical one.

**It costs us almost nothing.** The domain corpus under D-10 is the classical liberal canon, most of
it written before 1950. The founding documents are eighteenth century. Public-domain works are by
definition old. The cutoff removes essentially none of what Pagouro is actually about.

**It is implementable.** FineWeb and Dolma are built from Common Crawl snapshots that carry dump
dates, so pre-2022 crawls can be selected rather than filtered heuristically. That makes the claim
auditable: we can name the exact dumps.

**It fits the hermit-crab framing.** A finished artifact, anchored in time, dug up later. A corpus
with a hard date boundary is the same idea one layer down.

## What it costs

- **No recent technical material.** Post-2022 code, recent protocol developments, anything about the
  current AI era. For a model whose subject is money and liberty, this matters less than it would
  for a general assistant, but it is a real loss.
- **A smaller corpus.** Pre-2022 Common Crawl is still enormous, far beyond our 100B token target,
  so this is not binding at our scale.
- **Verification is imperfect.** A crawl date is when a page was *fetched*, not written, and some
  pre-2022 pages were later edited. The honest claim is "collected before generative AI was
  widespread," not "provably written by humans." **Overstating this would be exactly the kind of
  unearned claim the threat model forbids elsewhere.**
- **Stack Exchange and Wikipedia need date filtering** by post or revision date, which is possible
  but adds pipeline work.

## Recommendation

**Adopt it, and state it precisely.**

The claim to make: *every source in this corpus was collected or published before 1 January 2022,
prior to the widespread availability of generative AI. Dump dates and publication dates are listed
per source in the ledger.*

The claim **not** to make: that the corpus is provably free of machine-generated text. It is not,
and cannot be. A small amount of pre-2022 generated text exists.

This is the same discipline as `THREAT_MODEL.md`: state exactly what is true, and let the precision
of the claim be the thing that impresses.

## If adopted

1. Add `published_before` and `collected_before` fields to every `corpus.json` row.
2. Select Common Crawl dumps by date rather than filtering after the fact.
3. Filter Stack Exchange by post date and Wikipedia by revision date.
4. Extend the licence gate in `fetch_data.py` to refuse any source without a date basis, exactly as
   it already refuses sources without a licence.
5. Put the cutoff in the README's first section. It is a headline property, not a footnote.
