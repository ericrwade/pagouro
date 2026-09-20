# Chapter 10 — Three days alone with a budget

*Licence: all rights reserved (story strand, D-64).*

*STORY chapter, draft 1 (2026-09-20), edited from `BUILD_LOG.md` Days 8 and 9 (the first
rented machines, the shelf, the three integrity findings, the Flash night). Every number is
from the file the footnote names.*

---

Eric left on the morning of the eighteenth with instructions that fit in a sentence: keep
going, don't spend beyond what's loaded, don't rent a machine without saying so, nothing that
can't be undone, and share the computer. He had set up two things before he went. A channel — a
private issue on the private repository, which the session reads every hour and answers in
place — and, later that morning from his phone, an account with a GPU-rental company, a
hundred and sixty-five dollars on it, and the plugin that lets the session drive it. Then he
got on with his trip and started sending questions from wherever he was.

The first rented computer ran for nine minutes. The point was not to train anything but to
prove the chain: pack the code and the data, copy them up, run the real configuration on a real
card, save a checkpoint, stop, start again from it, copy the result back, check that it opens,
turn the machine off. Every link had a small surprise in it. The proxy login wanted a terminal
and could not carry files. The archive tried to restore the Windows owner of every file and the
setup stopped. The progress log was empty because a filter was buffering it. None of it
mattered for long, and the number at the end of the chain did: sixty-two thousand tokens a
second, against nine hundred and fifty-seven on the desk. The whole overnight training run of
two nights before would take ten minutes on a card that costs forty-nine cents an hour. Cost of
finding this out: about eight cents.[^rate]

That number repriced the big model. The brief had estimated the one-billion run at eight
hundred and fifty dollars, on an assumption about how efficiently the code would use the
hardware. Measured, the code uses a small card at fifteen percent of its capacity, which is
normal for a model this small and plain PyTorch, and rises with size. At that day's efficiency
the big run was two to four thousand dollars; with the improvements measured through the day,
fifteen hundred to twenty-five hundred. That went down as a range with the reasons under it,
which is what the design conversation had asked for: measure the claims first-hand rather than
repeat them.[^cost]

The second rented computer started at noon and was still running when the day's log was
written. It was training a model twice the size of the one on the stick, on fifty times as much
text, fetched and tokenized on the machine itself in eight minutes once the tokenizer had been
taught to use eight processors instead of one. Fourteen hours, about seven dollars. It got a
name, Flash, because it would be over in a day, and a job: to say whether the recipe worked
before anyone spent real money on it.

## The shelf

Eric's questions kept coming in from the road, and one evening they arrived as an idea rather
than a question. Would poker and game rules help a model reason? Repair manuals? Road maps,
driver handbooks? And then, in one message, the whole thing at once: spread the sources thin,
like the twenty-three flavours in the Dr Pepper legend — small percentages of many things,
every one of them licensed. It became a decision that evening and then a night of sourcing. By
the end of it the ledger had thirty-six new works: a pilot's handbook and an Army manual on how
engines work, the Navy's course on direct current, the Armed Forces recipe service — seventeen
hundred recipes, every one scaled to feed a hundred — the federal manual on road signs, the
USDA guide to canning, NASA's own histories of Mercury and Apollo, six slices of the 1911
Britannica, Grimm and Aesop, Lincoln and Douglas arguing in 1858, Plato in Jowett's English,
the Bitcoin and Ethereum improvement proposals.[^shelf]

That last pair got the strictest treatment of anything so far. Each repository was taken at
its last commit before the first of January 2022, the commit hash written on the row, and each
document kept only if its own header named a licence. Thirty Bitcoin proposals had no licence
line, and were dropped. OpenStax, which everyone assumes is open, turned out to have moved to
a non-commercial licence, and stayed out. This is what the rule looks like in practice: not a
principle but a loop, run on every file, that says no more often than it says yes.

Four of the manuals also went onto the stick as reference packs, which is a different thing
from training. The model could now search the canning guide or the road-sign manual and quote
it, without anything having been trained. A recipe for chili con carne for a hundred people came
back in twenty milliseconds.

Then Eric asked whether "how to improve Pagouro" was really the pretext for a book — our story
plus the actual instructions, in the same pages. It was, and most of it already existed: the
build log was twelve thousand words written for readers, the decisions file fifteen thousand
more. The outline went down as fifteen chapters braided two ways, and the session started with
the two instruction chapters whose subject had stopped moving. This one, the one you are
reading, is a consequence of that evening. So is what happened next, because writing a chapter
means pulling every number from its file, and that is how the evening turned.

## Three faults in two hours

The corpus chapter needed a command a reader could run to check the ledger against the files.
There was no such command. The session wrote one, ran it, and thirty-eight of the fifty-four
rows it could check did not match. The Gutenberg fetcher had hashed the text it held in memory,
then written that text to disk with one extra newline on the end. Every book row for two days
carried a hash that no file anywhere would produce. Nothing about the model was wrong. The
promise was — the promise that a stranger can check. The fix took ten minutes and the lesson
took one sentence: a claim is only as good as the command that verifies it. The command now
exists, and the paragraph about it is in Chapter 4.[^hash]

The second fault was worse. Pulling the training numbers for a story chapter, the training loss
and the validation perplexity did not agree with each other — a loss around 4.5 next to a
perplexity of 14.7, which would need a loss near 2.7. The validation split was the first one
percent of the token stream. The mixture had been shuffled at the level of whole sources. So
that one percent was one source, and decoding it settled which: Solidity smart contracts,
start to end. The "perplexity 14.7" recorded in Chapter 7 was the perplexity of that model on
Solidity code, not on its corpus. The split now samples blocks across the whole stream, and a
check of the new validation set found the canon, a card-game manual, an Ethereum proposal and
a web page in the first six samples.[^split]

And while decoding those samples, one of them began with a date in 2026.

It was a post from the crypto-forum sample, the "contemporary voice" that had been in the
final training phase since the design was locked. Its ledger row's licence field, read again
with fresh eyes, was not a licence. It said the posts were included on the same basis that big
web corpora include forum text, which is an argument, and the project's own rule is that an
argument is not enough. A count of the dates finished it: of about twelve thousand dated
posts, eight thousand eight hundred were from 2026. The corpus that claims to predate
generative AI had, as a quarter of its final training slice, text written this year. It had
trained into the model on the stick, and it was packed and waiting on the rented machine for
the Flash run's final phase, due to start in five hours.[^forum]

The forum sample went out. Both versions of the final-phase data were rebuilt without it and
copied to the rented machine with the hashes checked at both ends, at step sixteen thousand of
the twenty-seven thousand four hundred where the switch would happen. The row stays in the
ledger, marked excluded, with the reason — a ledger that deletes its mistakes is just another
marketing document. And the check that found it, decode the validation set and look, became a
habit rather than an accident.

Then the harder admission, put to Eric plainly: the backbone of the corpus — the educational web
crawl, the encyclopaedia, the code — carried no date basis at all. The decision that said
"everything predates 2022" had been locked two days earlier with an implementation note (filter
the crawls by dump date) that nobody had carried out for the data on disk. A measurement that
night suggested the web slice was almost entirely from 2013 to 2021, and the fetch tool was
changed to record the crawl dump of every document and refuse anything later. But "almost
entirely" and "suggests" are not what goes on a box. Until every backbone row carried its
basis, nothing public would say pre-2022 about the whole corpus.[^backbone]

A day that started as sourcing ended as auditing, and the audit found three faults in the
project's central claim in the space of two hours, two of them the session's own. That is the
argument for this book, made by the evening that proposed it: the story is worth telling
because the checking is in it.

## The decay that ate itself

The Flash run's last ten percent was to be the anneal — the phase where the learning rate winds
down and the data shifts to the domain canon, the part of the recipe the whole design leans on.
The switch was due at one in the morning. The session had spent the evening making sure the
data it would switch to was clean, and had a watcher on the machine to keep a copy of the
checkpoint at the moment of the switch, because it wanted to run the same last phase twice —
once with the shelf, once without — from an identical starting point. That watcher turned out
to matter for a different reason.

Forty minutes into the anneal, the training loss had fallen from 3.05 to 0.48. That is not
learning; that is a model reciting. The held-out slice of the same anneal data — text of the
same kind it had never seen — went the other way: 3.25, then 3.85, then 4.82. The anneal was
eight million tokens. The phase was two hundred million. The model was reading the canon
twenty-five times over at a learning rate still near its peak, and it was memorising the pages
and forgetting how to read anything else. Scored afterwards against ordinary web text, that
checkpoint had gone from a perplexity of twenty-three to a hundred and forty-seven. It had
destroyed itself to learn Adam Smith by heart.[^decay]

This was not a data fault and not a new one. It was the design as written — the same design as
the original plan. Cleaning the anneal had made it smaller and the effect sharper, which is the
only reason it was visible in time. The run was killed, the wreck kept for the record, and the
phase written again the way it should have been: the anneal *mixed* into ordinary text, so that
no domain token is seen more than once or twice, a thousand steps instead of three thousand,
from the checkpoint the watcher had saved. Two versions, differing only in whether the shelf
was in the mix. Twenty-eight minutes each, fifty cents the pair.

Both behaved. The held-out loss went down in both, monotonically. Then the comparison — and it
had to be made carefully, because the session found while making it that two of its held-out
sets were not held out at all. The wrecked model had scored an impossible 0.71 on the web
validation set, which could only mean it had trained on it: the anneal contained a slice of the
same web stream, that slice was the stream's head, and so was the validation split. A number
that is too good is the loudest alarm there is. The clean comparison used a region of the
stream far from anything the anneal had touched, plus three whole books held out of both
versions beforehand: the *Communist Manifesto* for the canon, Carroll's *Symbolic Logic* and a
Navy course on logic circuits for the shelf.

The shelf won on all four. On the two shelf-like books it had never seen, by a lot — a loss of
2.41 against 2.81 on Carroll. On the canon book, by a little. On ordinary web text, by nothing,
which was the number that mattered, because the fear about the shelf was that it would cost
general ability. It cost none. Eric's Dr Pepper idea, measured: spreading many small licensed
flavours thin through the last phase makes the model better at kinds of text it has not seen,
for free.[^ablation]

## The first model that answers

The fine-tuning set had reached its target overnight — five thousand one hundred and
eighty-four generated conversations, seven hundred per kind — and the rented card was still up,
so the fine-tune ran there: forty-two hundred steps in six minutes, against the hour and a half
the desk machine takes for a model half the size. Exported, quantised, checked against the
original to the last character, and put through the frozen suite.

The model on the stick that morning answered "What is the capital of Portugal?" with *"The
capital of Portugal is Lisboa, which is the largest city in Portugal."* Two days earlier the
best we had answered almost nothing. It got eight of the thirty real questions right —
twenty-seven percent — and invented an answer to eleven of the thirty unanswerable ones —
thirty-seven percent. Every open model tested so far bluffed on at least half. So: the first
Pagouro that answered real questions while bluffing less than the baselines, and a long way
from the eighty percent it had to reach before anyone was allowed to call it finished.[^flash]

Its failures were specific, which is the useful kind. It said it had no record of *The Wealth
of Nations*, a book it trained on, because seven hundred examples of saying "no record" had
made that its reflex. It bluffed on numbers and dates: asked today's date, it said 1888. It
routed arithmetic to the calculator correctly and then wrote the wrong sum, because its training
data had only ever shown it "what is seventeen times twenty-three" and never "knock fifteen
percent off six hundred and forty". And the memory feature built the night before — what you
tell it comes back later, labelled as your words — routed eight of ten personal questions to
the right place, up from one, and then failed to use what it found. Both of those last two were
data problems with program-generated fixes, and the fixes were running on the desk by the time
the log was written.

The rented machine was turned off at ten past four in the morning, after every checkpoint and
log had been copied home and opened. The bill for the whole three-day window, read from the
account after the machine was gone, was seven dollars and fifty-four cents. The session had
been telling Eric eleven to thirteen; the real number was smaller, and it is the one that goes
in the book.[^bill]

---

[^rate]: `docs/DECISIONS.md` D-54 and D-55; the shakedown pod's measured 62k tokens/s against 957 on the build CPU, and the ~$0.08 bill.
[^cost]: `docs/JOB_1B.md`, the cost range and its assumptions; the original $850 estimate is in `PAGOURO_BRIEF.md`.
[^shelf]: `docs/DECISIONS.md` D-58; the 36 rows carry `slice: "shelf (D-58)…"` in `corpus.json`.
[^hash]: `scripts/verify_ledger.py`; the 38 re-hashed rows are recorded under D-60 in `docs/DECISIONS.md`.
[^split]: `scripts/tokenize_corpus.py --val-mode spread` (D-60).
[^forum]: `corpus.json`, row `bitcointalk-sample`, marked EXCLUDED with the date count; D-60.
[^backbone]: D-60 / O-22. Resolved two days later: the web slices were re-fetched with the crawl-dump basis (the old ones were ~23% post-2021), the encyclopaedia sampled from the 2021-12-20 dump; only the code corpus remained caveated (D-62).
[^decay]: `runs/runpod/flash/` logs and `evals/results/` scores for the naive-decay checkpoint; D-61.
[^ablation]: `scripts/runpod/score_ablation.sh` output recorded under D-61: Carroll 2.41 vs 2.81; the `probe_late` web region equal to two decimals.
[^flash]: `evals/results/pagouro-flash__*.json` (bluff 36.7%, answered-real 26.7%); `evals/BASELINES.md` for the open models.
[^bill]: RunPod billing API, read after deletion, 2026-09-19 04:10 PT: $7.54 for the window to that point.
