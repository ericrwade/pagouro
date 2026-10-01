# Chapter 8 — An app on a stick

*Licence: CC BY-SA 4.0 (D-101, 2026-10-01; the story strand was all rights reserved under D-64 until then).*

*STORY chapter, draft 1 (2026-09-19), edited from `BUILD_LOG.md` Day 7 with the morning after
(Day 7's app transcript, D-53) and later corrections as footnotes.*

---

Eric went to bed with three instructions. The agent and its tools go in from day one, as a
working minimum that someone with time, skill or money can make bigger. The original design
conversation stays private, with a two-hundred-word public version in its place. And the
computer is shared with a game engine and another coding agent, so play nice. Then: have
something to show in six hours.

What was on the stick at midnight was a bare console program from the llama.cpp project. You
typed, it answered, and if you typed enough the conversation silently fell off the front. What
was on the stick by morning was a small program of this project's own. It starts the model
server beside it, and above every prompt it shows three switches and a bar.

The switches are the ones the design conversation asked for, plus one the agent needs.
**OFFLINE**, which in that build was the only mode and is proven by an audit that watches for
any network call and finds none.[^1] **SAND or STONE**: nothing you type is saved unless you
say so, and when you say so, the transcript starts from that moment, not before. And
**READ-ONLY or CAN ACT**: a tool that writes a file is refused until you allow it, and even
then it may only write inside one folder on the stick. The bar is the model's memory, ten
boxes, green to red. That first model held about three hundred and fifty words.[^2] When it
fills, the oldest exchange is shown leaving, with its first few words, so you know what it no
longer remembers. A small model's limit, made visible instead of hidden.

The tools were five: a calculator, the clock, a search over reference texts kept on the stick,
reading a file you name, and saving a note.[^3] Before each answer the model is asked whether
one is needed. It answers under a grammar, which means the only thing it can physically emit
is a valid choice from that list with a string of arguments. Then the harness runs the tool,
prints what it did and what came back, and the model answers with the result in front of it.

## The honest part

The model that lived on the stick that morning had fifty-nine million parameters and had read
thirty-seven million words. It was taught the format overnight, from three hundred hand-written
conversations, and it learned the format: on sixteen questions it had never seen, it picked
the right tool twelve times. It did not learn the content, because there is no content to
learn at that size. Asked to say what a tool returned, it garbled the digits. Asked to save
"bring the charger," it asked the tool to save something about Bitcoin wallets. Its second
answer in any conversation was worse than its first.

So the harness does what the design conversation said a harness should do, which is
compensate for the model rather than trust it. When the model's argument is unusable, the
program recovers it from the user's own words with a handful of plain, visible rules: the
arithmetic in the sentence, the words after the colon, the thing that looks like a file path.
With that in place, every tool call in the final run from the stick did the right thing, while
the model's own arguments were wrong every time. That is the whole thesis of the project in
one evening: the model's judgement is the model's; the reliability is the framework's, and the
framework is what you are meant to build on.

## The morning after

Eric ran it and pasted the conversation back. The first exchange went well; the second did
not, and the reason was the kind that only a real user finds. He had typed a long, careful
message, and the program — making room in a full memory for the answer — had thrown away the
oldest thing it held, which was the message he had just typed. The bar showed a block leaving;
what it did not show was that the block was the question. The fix was a rule the program now
keeps absolutely: the current turn is never dropped. If there is not room for it, the tool
result is trimmed, then the history, and the answer's length budget shrinks, but the thing the
person just said stays.[^4]

He also wanted the bar to be a thermometer that the program never explained in words, and a
launcher that did not stop for "press any key" between answers. Both done that day. The last
thing he asked was harder: how much can a person type and have the model retain? The honest
answer, then and now, is "what the bar shows", and the bar is the answer to the question rather
than a decoration on it.

## Two bugs that belong here

The program's closing line said "nothing was written to disk" after a note had just been
written. It was fixed to list every file it touched, and the exit line has told the truth
since — including, two days later, the one file a scripted test wrote and the zero network
calls it made.[^5]

And the packaging step silently failed to include the new program at all on its first run, so
the stick was refreshed with the old layout and the pipeline reported success. It was caught by
listing the stick rather than reading the report, which is the same lesson as two nights
before, learned again. The stick is now listed, and its manifest verified, after every rebuild.

## A "probably fine" that stayed out

One more, found by accident while choosing the reference texts. The only free edition of
Bastiat's *The Law* is a 2007 translation published under a licence the file describes only as
"a Creative Commons license," variant unstated. Under this project's rule that unclear rights
mean no, it stayed out of the packs, and a question was opened about its presence in the
training corpus.[^6] A model whose whole pitch is provenance cannot have a "probably fine" in
it.

The game engine was idle every time it was checked. The stick held the app, the model, two
public-domain books, and an empty workspace with a note inside explaining what may be written
there and when.

---

[^1]: The audit itself was later found to be capable of passing on zero samples and was
rebuilt to force real generation for the whole window (Chapter 11's rule about numbers that
only go one way; commit of 2026-09-19). The stick's current audit: 39 samples over 60 s, 0
connections.
[^2]: 512 tokens. The Flash model that replaced it two days later holds 1,024, about 700 words.
[^3]: A sixth, `web_search`, was added the next day for an ONLINE mode the owner has to turn on
and configure; it stays off by default.
[^4]: D-49 and D-53 in `docs/DECISIONS.md`; `app/pagouro_app.py`, `make_room` and
`fit_current_turn`.
[^5]: `BUILD_LOG.md` Day 9; the scripted run from the stick with the Flash model.
[^6]: The question was opened and then not acted on: the book stayed out of the packs but in
the training anneal for two more days, until writing this footnote found it there. It is out
now (D-63). Bastiat remains through *Economic Sophisms* in the Stirling translation (translator
d. 1891), a nameable basis. An open question is not a licence.
