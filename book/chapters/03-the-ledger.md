# Chapter 3 — The ledger, or why the big labs can't publish this file

*Licence: CC BY-SA 4.0 (D-101, 2026-10-01; the story strand was all rights reserved under D-64 until then).*

*STORY chapter, draft 1 (2026-09-21), edited from `BUILD_LOG.md` Day 1 ("the project finds its
actual subject") and Day 2, and from decisions D-8, D-9, D-10, D-32, D-34, D-60, D-62 and O-22 in
`docs/DECISIONS.md`. Every number is from the file the footnote names.*

---

There is a file in the repository called `corpus.json`. It is not large — seventy-one entries
as of this morning — and it is the least glamorous thing in the project and the reason the
project exists.[^rows] Each entry is one source of training text: what it is, where it came
from, what licence it carries and on what basis, when it was retrieved, how many characters and
tokens it contributed, and a hash of the exact bytes that went into the mixture. Anyone can open
the file. Anyone with the same sources can rebuild the same bytes and check the hash. That is
the whole idea, and it took about a day to go from "obviously we should do that" to
understanding what it costs.

The obvious version was the first afternoon's. Build on the big open corpora — the educational
web crawl, the encyclopaedia, the code archive — because they are already deduplicated, cleaned
and documented, and assembling a corpus from raw sources is months of scraping that a one-person
project will never finish.[^d8] Cite them. Done. The decision was right and it is still the
backbone, but "documented" turned out to mean something narrower than "defensible", and finding
the gap is most of this chapter.

## What the subject was

Before the ledger meant anything we had to know what the model was *for*. Eric's early framing
was a bespoke model steeped in his own subject — money, property, debt, ownership, the things he
had spent years thinking and writing about — on the reasoning that he could not compete on
scale, so he would compete on being *his*. The first instinct was the obvious one: the forum
where that culture actually talks. A sample of a crypto forum went into the plan as "contemporary
voice."

The correction that shaped everything came from how training actually works. Reasoning and
subject knowledge come from different stages. A model learns to think from general text, code
and mathematics; it learns a domain from a modest slice plus a concentrated pass at the end; it
learns its *positions* from a few thousand curated examples at the very end; and it should not
learn specific documents at all — a book is about a hundred and thirty thousand tokens, which is
nothing against a corpus of billions, and repeating it until it sticks makes the model worse,
not better informed. Specific documents go in a retrieval index where they can be quoted
exactly.[^d9]

Once you see it that way the forum stops being the spine. If the subject is money, property and
liberty, the substance is a written tradition, and the tradition is almost entirely out of
copyright: Smith, Ricardo, Bastiat, Mill, Locke, Hume, Tocqueville, the founding documents, and
the source code of the chains themselves, which is open by construction. A model that has read
the lineage the crypto ethos descends from is a more interesting thing than a model that has
read the forum, and — this is the part that made it a decision rather than a preference — it is
licence-clean.[^d10] The forum was demoted to flavour. Later it was removed altogether, and the
reason it was removed is the point of the ledger.

## Three kinds of "we checked"

The Gutenberg books were the easy case and even they had a wrinkle. The texts are public domain;
the Project Gutenberg *name* is a trademark, and their files carry a licence about the name. For
a while that looked like a blocker. It is not: their own permissions page says you may freely
redistribute any eBook with or without their trademark, and the resolution is to strip the
header and footer that carry the boilerplate and record, for every book, the author's death date
that makes the text public domain — so the claim rests on copyright law and not on anyone's
say-so.[^d32] Thirty-seven of the seventy-one rows are books handled that way.

The big corpora were the hard case, and the hardness was invisible at first. Each comes with a
licence for the *collection*: an open-data licence on the web crawl, share-alike on the
encyclopaedia and the Q&A site, and, on the code archive, a licence that is really a list of
files whose authors have asked to be left out. We accepted share-alike deliberately — it means
the model's weights themselves are released under a share-alike licence, which Eric said yes to
on the grounds that it let us build what we actually wanted and stay provable.[^d31] What none of
the collection licences told us was *when* anything was written.

That mattered because of a second rule, set a day after the ledger, that turned out to be the
one people react to. The corpus contains only material from before generative AI: nothing
collected or published after the first of January 2022.[^d34] The claim is precise on purpose.
It is not "there is no machine-written text in here" — a crawl date is when a page was fetched,
not when it was written, and pretending otherwise would be exactly the unearned promise the
project refuses to make elsewhere. It is: every source has a date basis, and the basis is on the
row. No frontier lab can say that about its training data, and for a corpus that is mostly
nineteenth-century books it costs almost nothing.

Except that it had not actually been done. Two days later, pulling numbers for this book, the
session found that the backbone rows — the ones we had cited on the first afternoon — had no
date basis at all. The educational web slice spanned crawls up to 2024. The encyclopaedia was a
dump from November 2023. The code archive had no per-file dates and had been collected to March
2022, three months past the line.[^d60] The rule was written on the wall and the data on the disk
did not meet it. The fix was mechanical but not small: re-fetch the web slice from crawls dated
2013 to 2021 only, re-fetch the encyclopaedia from the last dump of 2021, and mark the old rows
superseded rather than deleting them — the ledger records retractions too.[^o22] When the dated
web slice was compared with the undated one at the same position in the stream, about
twenty-three percent of the undated documents were from after the cutoff. Nearly a quarter of
what the first two models had read for "general English" was from the years the rule exists to
exclude.[^o22]

The forum sample was the third kind. Its ledger row had a licence field that read, in effect,
"forum posts are in every web corpus, so this is fine." That is an argument, not a licence, and
the project's rule is that unclear rights mean no. Worse, 8,823 of its roughly twelve thousand
dated posts were from 2026 — the year the model was being built — and it was about a quarter of
the anneal, the concentrated pass at the end where the domain flavour goes.[^d60] It had trained
into the first stick model. It was removed the evening it was found, the anneal was rebuilt and
re-uploaded to a rented machine that was mid-run, and the row stays in the file marked
EXCLUDED with the reason. The next day the same rule caught a translation of Bastiat whose
Creative Commons variant nobody had written down; it left the same way.[^d63]

## Why they can't publish this file

None of this is clever. It is a spreadsheet with a hash column, kept honestly. The reason no
large lab publishes one is not that they lack the engineering. It is that the file would have to
say what the rows above say — here is a source, here is its licence, here is its date — for
every source, and for the corpora the big models are trained on the honest entries would read
"unknown", "contested" and "after 2022, fraction machine-written: not measurable". A ledger you
cannot fill in is worse than no ledger, because it shows the shape of what is missing. Ours can
be filled in because the model is small and the subject is old, and that is the trade the
project makes: it gives up scale to be able to answer the question "what did you train this on?"
with a file instead of a paragraph.

The code archive was the last row without a date, and it was replaced this morning, which is
how the chapter can end where the ledger is rather than where it was. Instead of an archive
whose collection date was the only date, the code slice is now a list of named repositories,
each cloned and wound back to its last commit before the first of January 2022, each licence
file read and classified before a byte was taken, the commit hash on the row. A repository
whose licence file we could not classify was skipped and counted. The cost was a script and a
morning.[^d62] The previous rows are marked superseded, and say which two models were trained
on them.

If you follow the *do-it* chapter after this one you will build the same file for your own
corpus. It will be shorter than ours and it will have the same columns, and the column that will
give you the most trouble is the date.

---

[^rows]: `corpus.json`, 71 rows on 2026-09-21 before the code rows were added: 37 Gutenberg works, 2 marked EXCLUDED, 14 marked SUPERSEDED.
[^d8]: `docs/DECISIONS.md` D-8 (2026-09-16): build on existing open corpora; assembling from raw sources was "the single biggest risk to this project ever finishing."
[^d9]: D-9, the stage table; the 130,000-token figure for a book is from `BUILD_LOG.md` Day 1.
[^d10]: D-10: the canon, not the forum.
[^d32]: D-32, quoting Project Gutenberg's permissions page: "you can freely redistribute any eBook, anywhere, any time, with or without the 'Project Gutenberg' trademark included."
[^d31]: D-31: weights CC BY-SA 4.0, code Apache 2.0.
[^d34]: D-34 (LOCKED 2026-09-16): cutoff 1 January 2022; the claim made and the claim not made are both quoted from the decision.
[^d60]: D-60 (2026-09-18): the forum sample's licence field and its dates (8,823 of ~12,000 dated posts from 2026; ~26% of the anneal, 17.3M characters); the backbone's missing date basis.
[^o22]: `docs/O22_PRE2022_BACKBONE.md` and the superseded rows in `corpus.json`: the undated FineWeb-Edu slice held ~44,480 post-2021 documents among ~194,000 at the same stream position (~23%); Wikipedia re-fetched from the 2021-12-20 dump.
[^d63]: D-63 (2026-09-19): *The Law*, Gutenberg #44800, a 2007 translation with an unstated Creative Commons variant, removed from the anneal.
[^d62]: D-62 and D-62b; `scripts/fetch_dated_code.py` and the `code-dated-*` rows, each carrying its repository list with commit hash, commit date and licence file. The measured totals are on those rows and in Appendix B.
