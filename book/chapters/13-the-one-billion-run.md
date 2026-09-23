# Chapter 13 — The one-billion run

*Licence: all rights reserved (story strand, D-64).*

*STORY chapter, draft 1 (2026-09-23, written while the run was at step 58,000 of 95,104),
edited from `BUILD_LOG.md` Days 12–14. The last section is left open for the decay phase and
the numbers it produces; every number here is from the file the footnote names.*

---

The message that started it was short. Eric had asked, from the road, what was left before the
big model could be shown to the world, and the list had two items that were his: whether the
model could be trained at four thousand tokens of context and stretched to eight thousand at
the end (cheaper by a fifth, and the way the larger labs do it), and whether to begin. He
answered both in one line — "consider it approved," and "start on runpod, I will add money to
it right now" — and two decisions that had been open since the first week were closed at 21:58
UTC on the twenty-first of September.[^launch]

We had wanted, honestly, to run it somewhere else. io.net is a decentralised GPU market, paid
in stablecoin, squarely in the world Eric works in, and a better story. Reading its
documentation on the day, three things a marketplace should not be carrying under a four-day
eight-card job could not be found: whether eight H100s come as one machine, where two hundred
gigabytes of data would live, and what happens to the disk when a prepaid rental runs out.
Eric's answer is the project's method in a sentence, so it goes here in his words: "I would
have liked to use it, but not at the expense of the job." The analysis is in the repository,
and the rule it ends in applies to every provider — a dollar's shakedown and an hour's rehearsal
before it is allowed to carry the run.[^providers]

## The corpus, first

You cannot start a hundred-billion-token run with half a billion tokens on the disk. The
evening was spent on a builder that takes a plan — a list of shards, each with a source, a date
basis and a size — fetches each one, tokenizes it, appends it to one long file and writes a
table of hashes, one per shard, beside it. Eighty-three FineWeb-Edu crawls chosen by name, every
one dated 2021 or earlier, so that nothing has to be filtered out afterwards. The whole of
Stack Exchange with its per-row dates. The dated code three times over, because there is so
little of it. And, in the plan as written that night, the whole English Wikipedia as it stood
on the twentieth of December 2021.

It ran on a thirty-two-core machine with no GPU at ninety-six cents an hour, in Iceland, writing
to a five-hundred-gigabyte network disk. The first real shard measured 1.12 billion tokens in
286 seconds, fetched and tokenized, and every shard after landed within twenty percent of that.
By one in the morning the disk held thirty-seven billion tokens for about three dollars. The
machine was in Iceland and not beside the H100s because the H100 datacentres have no CPU
machines to rent, and building the data on a three-and-a-half-dollar card for fifteen hours
would have cost more than one copy of the finished file between countries.[^volume]

Wikipedia did not make it. The fetcher sampled the dump one HTTP range request per hundred
articles — two seconds each, fine for the hundred-million-token slice on the desk, days for the
whole thing. A local parser was written and tested against the full download, which had in fact
finished by then, and it would have worked. Eric's answer arrived first: "if there is a way we
can build this without using Wikipedia, I would be perfectly fine with that." So it is out. The
trade is written down where the ledger can be checked against it: Wikipedia was four or five
percent of the plan and its densest source of plain facts, so the model may answer a little
less, and the calibration set will say how much. What was gained was a corpus ready that
morning, and one fewer share-alike licence in the backbone.[^wiki]

At 06:44 UTC the file held **99,724,809,408 tokens** — 199 gigabytes, the byte count checked
against the shard table, eighty-nine shards each with its own hash and one hash over the whole.
Eight hours and forty-six minutes on the cheap machine: about eight dollars and fifty cents for
the corpus. The mixture, measured rather than planned, was FineWeb-Edu 91.6 percent, Stack
Exchange 7.7, code 0.7.

## Looking for eight cards

Meanwhile the session had been asking the rental company's catalogue, every half hour since the
launch message, for eight H100s on one machine. Seventeen of nineteen answers said *Out*, on
both of the company's clouds, at every CUDA version, in every datacentre. Eric widened the
permission to faster cards, and the arithmetic went into the plan: B200s cost about the same
money for the run because they do more than twice the work per hour, and would have finished in
a day and a third; H200s are H100 speed at a thirty-percent premium and go last; sixteen cards
would halve the days at the same dollars but need two machines talking over the network, and the
cluster catalogue showed no sixteen of anything. He had also seen an analysis saying RTX 4090s
"can almost keep up with H100s if you can find enough of them," which is true per dollar and
false per calendar: a 4090 does about a sixth of an H100's work, has twenty-four gigabytes where
the optimiser alone wants sixteen, has no fast link to its neighbours, and the company caps a
machine at eight of them. Eighteen days, or fifty cards across six machines, which is a
distributed-systems project and not a rental.[^cards]

Twice the catalogue showed eight H100s *Low* on the cheaper "community" cloud, at $21.52 an
hour for the set — the one price at which the run fit inside the money Eric had loaded. The
first time they were gone by the next check. The second time, at 07:03 on the twenty-second,
the session tried to create the machine three times inside two minutes, with three different
disk sizes, and was told each time that there were no longer any instances available. The
explanation was in the catalogue's own entry, once it was read rather than trusted: community
H100 hosts allow **one card per machine**. The stock probe was multiplying a single-card host's
price by eight and reporting it as a machine with eight. Every *Low at 8* the watch had seen
overnight had been that phantom.

Eight H100s on one machine existed only on the secure cloud, and at 07:24 the secure cloud had
them: Montreal, eight H100 SXM with the fast link between every pair, 224 cores, two terabytes
of memory, three hundred gigabytes of disk, **$27.92 an hour**. The projection at that price —
a hundred billion tokens at 25, 30 or 35 percent of the cards' theoretical peak — was $2,440,
$2,030 or $1,740. Every case was over the $1,500 cap. The session created the machine anyway
and posted the arithmetic, because the rehearsal that would decide the run costs one hour, and
a run of this shape can be stopped at any checkpoint and still yield a finished model.

## An hour of plumbing

The corpus was in Iceland and the cards were in Montreal. A single copy stream between them ran
at sixteen megabytes a second — three and a half hours for the file, at twenty-eight dollars an
hour of idle cards. Sixteen streams in parallel, each fetching one sixteenth of the file by byte
range over its own connection, ran at about 175 megabytes a second — and eleven of the sixteen
survived, because the source machine's SSH daemon drops simultaneous logins past a limit. A
second script hashed each sixteenth on both sides and re-fetched the ones that differed; on
the third pass all sixteen matched, and the hash of the whole file came out the same as it had
in Iceland.[^pull]

The rehearsal measured what the plan had guessed. The model has **968,968,192 parameters**;
the plan's feed-forward width had been a round number, and the rehearsal used the one the
architecture's own rule gives. A micro-batch of eight sequences ran out of the eighty
gigabytes on each card; four sequences of 4,096 tokens, accumulated eight times across eight
cards, gave **1,048,576 tokens a step**. Plain: 318,660 tokens a second, 23.4 percent of peak.
With the compiler on: about 444,000 a second, 32.6 percent, 2.36 seconds a step.[^rehearsal]
That number set the run: 95,104 steps for 99.7 billion tokens, two thousand steps of warm-up,
a constant learning rate to step 85,593, then the decay at eight thousand tokens of context on
the anneal mixture, a checkpoint of 11.6 gigabytes every five hundred steps.

**The run started at 08:48 UTC on the twenty-second.** The projection was about $1,800 against
$1,440 remaining, and the post to Eric said so, with the two ways out: an early decay from any
stable checkpoint at about $1,100 spent — fifty-nine billion tokens, a finished model inside the
cap — or a top-up of about five hundred dollars for the whole hundred billion. The decision was
his, and he had about thirty hours to make it.

## Forty minutes in

The disk read one hundred percent full.

The slow single-stream copy from an hour earlier had survived its kill. The command that was
supposed to stop it — a pattern-kill run through a one-line remote shell — had matched the
remote shell's own command line, killed the shell, and never reached the copy. It had happened
three times overnight without anyone noticing, and the surviving copy had written 104 gigabytes
into a file that had since been deleted, so the space was held and the file appeared in no
listing. It was found through the process table, killed by its number, and the space came back
— minutes before the next checkpoint save would have failed on a full disk and taken the run
down with it. The lesson is now in the rules the session reads at the start of every session:
find the process number first, kill the number, and after killing any copy check the disk,
because a deleted file that is still open is still on the disk.[^nearmiss] By 09:33 the
step-500 checkpoint was home and opened on the desk, the Icelandic machine was turned off, and
its disk was kept as the backup copy of the corpus for thirty-five dollars a month.

## The part that would be easy to leave out

From about noon UTC until 23:35 that day the session was paused — the half-hourly checks it
had scheduled for itself queued up instead of firing — so the three o'clock and nine o'clock
checkpoint copies did not happen, and the report that a quarter of the money was spent went
out late. The run did not notice. It is built not to: the checkpoint every five hundred steps
is on the machine's own disk, the log is a file, and when the watch came back it found the run
at step 23,300, loss 2.38, validation perplexity 10.7 from 342 at step 100, 460,000 tokens a
second unchanged since the first hour, exactly where the arithmetic said it would be. The
post at 23:40 carried the numbers and the admission in the same paragraph, because the rule for
the build log is that it records the parts that did not work, especially the session's own.

At twenty past three the next morning Eric's answer came through: "I added $500 to RunPod, go
for the full 100B." Cap two thousand, the full 95,104 steps, the early-decay rule retired.[^topup]

Fifteen minutes later, something the decay phase would have needed and which was wrong on the
machine. The code bundle carries no anneal data, and the anneal folder that had been copied up
at launch was the September 16 build — the one that still contained the forum sample the ledger
had thrown out on the ninth, in Chapter 10. It was rebuilt from the current ledger — thirty-one
shelf works at the one-third cap, the canon, no forum text — tokenized to 12.3 million tokens,
the forum line count checked to be zero, and put in place many hours before phase two would
ask for it.[^anneal] Had nobody looked, the model's last nine thousand steps would have been
trained partly on text the ledger says is not in it, and nothing would have flagged it. This is
the same lesson as the scan and the ablation: decode what you are about to train on, and look.

## Thirty hours of a flat line

Then the watch, which is the least dramatic and most important record in this chapter. Every
thirty minutes: the list of rented machines (one), the last step line, the last validation, the
time on the checkpoint file, the utilisation of two cards, the free disk. Every six hours a
checkpoint copied home and opened, each replacing the last. Every ten thousand steps a note to
Eric. The bill read from the account, not estimated, at every quarter of the cap.

Step 30,000 at 03:54 on the twenty-third. Step 40,000 at 10:24, $740 posted, the cards between
46 and 61 degrees drawing 690 watts each, no restarts, no hardware errors. Step 47,500 at 14:54 —
halfway — $866 posted, slightly ahead of the budget curve. Step 53,800 at 18:54, $978 posted,
half the cap.[^watch] Validation perplexity, read from the run's own record: 90 at step 500,
19 at 2,500, 12.3 by 8,500, under ten for the first time at step 29,000, and a low of **9.2 at
step 38,500**, which step 53,000 tied. Between those it moved in a band from about 9.5 to 11.
That band is not a problem; it is what this schedule looks like. The learning rate is held
constant through the stable phase, the model wanders at the bottom of a valley it cannot settle
into, and the decay — the last ten percent of the steps, at a shrinking rate — is where it
settles and where the last and largest drop comes from. Chapter 10 has the version of that drop
that went wrong. This time the decay data has been checked.

Three of the session's numbers were wrong in this stretch and were corrected on the same
issue, under the originals. The launch-day timeline said phase one would end at ten in the
morning of the twenty-fourth; the actual step clock, 2.26 seconds and the compile overhead not
in the estimate, says three in the afternoon. The half-cap post projected $1,915 because it
counted the decay hours twice; the corrected figure ten minutes later was **about $1,805 in
all**, some two hundred dollars inside the cap. And two evening posts called 9.7 and 9.2 "new
lows" when 9.2 had been reached fifteen thousand steps earlier — the watch was reading the last
few lines of the log and had forgotten the file. The build log for that day says so, and this
chapter was checked against the JSON record rather than the posts.

While the cards worked the desk did what cost nothing: the fine-tuning seeds and the four
skills went up to the machine so the finish could start the moment the run printed its last
line; the export was checked to need only two libraries; the near-miss became a line in the
rules. And this chapter was drafted, to here, at step 58,000.

## The decay

*(To be written when the run ends: the switch to eight thousand tokens of context at step
85,593, the held-out anneal loss through the decay, the final validation number, the two
fine-tuning mixes and which one shipped, the bill read from the account after the machine was
deleted, and the first answer the one-billion model gave.)*

---

[^launch]: `docs/DECISIONS.md` D-81 (4k→8k) and D-82 (the launch); `BUILD_LOG.md` Day 12, night.
[^providers]: `docs/GPU_PROVIDERS.md`; the io.net finding is recorded under D-82.
[^volume]: `scripts/build_volume.py`, `plans/volume_1b.json`; the shard table with per-shard SHA-256 is the build's `meta.json`; issue #2 comments of 2026-09-22 05:38Z and 06:45Z. Whole-file SHA-256 `4a60a5ff…` in D-85.
[^wiki]: D-84. The desk's 100M-token Wikipedia slice stays in the ledger and out of the 1B mixture; the `--local` parser stays in `scripts/fetch_wikipedia_dump.py`.
[^cards]: `docs/JOB_1B.md`, the card table and the sixteen-card note; `BUILD_LOG.md` Day 12, night; the phantom is recorded under D-85.
[^pull]: `scripts/runpod/pull_parallel.sh` and `pull_verify_chunks.sh`; issue #2 comment 07:32Z.
[^rehearsal]: D-85; the rehearsal log lines are quoted in the 08:48Z comment on issue #2. The steady rate over the run, 460,000 tokens a second (33.6% MFU), is in `/workspace/runs/pagouro-1b.jsonl`, copied home with the run.
[^nearmiss]: issue #2 comment 2026-09-22 09:23Z; the rule is the last line under LESSONS in the global `CLAUDE.md`.
[^topup]: D-82 amendment and D-85; Eric's message 2026-09-23 03:2xZ (chat), posted to issue #2 at 03:25Z.
[^anneal]: issue #2 comment 2026-09-23 03:27Z; `data/tokenized_anneal_1b/meta.json` on the desk (12,325,693 train tokens, 31 works).
[^watch]: issue #2 comments 2026-09-23 03:54Z, 10:24Z, 14:54Z, 18:54Z and 18:55Z; billing figures are the RunPod billing API's posted totals at those times. The validation series is `pagouro-1b.jsonl` (116 readings to step 58,000).
