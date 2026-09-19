# Chapter 7 — The machine stopped

*STORY chapter, draft 1 (2026-09-19), edited from `BUILD_LOG.md` Day 6 and Day 6 evening. The
log entries stand as written on their days; where later work corrected a number, the correction
is a footnote here, not a rewrite.*

---

The first real build ran overnight on the desk computer: fifty-nine million parameters, nine
thousand steps, the whole pipeline from corpus to stick for the first time at a size that
might say something. Eric left it running and came back eighteen hours later to a computer
that would not respond to anything. Not a crash with an error on screen; a freeze, the kind
where the only fix is to pull the plug. He disconnected the drives, cut the power, and brought
it back up. Then he asked the obvious question: where were we when it died?

The answer took about twenty minutes to establish and is worth recording in order, because the
order is the method. The training log's last line was step 6,140 of 9,000, written at 4:34 AM.
The last checkpoint was step 5,999, written ten minutes earlier. The previous session's own
last words, at 4:25 AM, were a memory check — 5.6 GB in use of 32 — followed by "still safely
in the normal range, continuing to wait." Windows recorded nothing in the hours before the
freeze. No hardware fault, no out-of-memory warning, no crash dump. Just a note on the way
back up that the system had rebooted without shutting down first. The model had reached a
perplexity of 19, down from 28 at the halfway mark, and was still improving when the lights
went out.[^1]

What survived was the checkpoint. It was loaded and inspected before anything else was
touched: every weight finite, the optimiser's state intact. Then it was copied somewhere safe,
with the copy's hash checked against the original. Only after that did anyone look at how to
continue.

Here is the part that would have been the real loss. The pipeline script that ran the build
begins its training stage by deleting the old checkpoint, because it was written for a fresh
start. Relaunching it by habit — the natural thing to do at three in the afternoon with a
rebooted machine — would have erased seven hours of work in the first second and started over
from nothing, and the log would have looked perfectly normal while it did. The fix was a flag
that tells the script to continue rather than begin, and a line in the project's memory so the
next session knows the trap is there.[^2]

A second thing was found while looking. The training script saved each checkpoint by writing
directly over the previous one. If the freeze had come during a save instead of ten minutes
after, the only copy would have been half-written and useless. Now it writes to a temporary
file and swaps it into place in one step, so the old checkpoint survives until the new one is
complete. This is a standard precaution and it should have been there from the start; it was
not, and the run survived on timing rather than design.

The resume itself is the proof that matters. The rule in this project is that resuming is
demonstrated by doing it, never assumed. The first step after the resume logged a loss of
3.963. The last step before the freeze had logged 3.965. A restart from scratch would have
shown a loss near 10. Roughly 140 steps were lost, about ten minutes of compute.

Why the machine froze is not known, and this book will not pretend otherwise. Two facts are on
the record. This same computer had crashed with a blue screen two days earlier, before this
project ever ran on it, while the cryptocurrency miner it also hosts was running. And both
crashes came after hours of every core working flat out. That is a pattern, not a cause. The
training was resumed on twelve cores instead of sixteen, trading about a fifth of its speed
for some thermal room, and the power settings were changed so nothing can go to sleep mid-run.
A firmware check and a memory test went on the list before the next unattended night.[^3]

## A king or a prime minister

Eric had a question while this was being sorted out that deserves its own section, because it
goes to the heart of what the project is. If the model is trained never to bluff, does it
become a search engine over its own corpus — able to define things, unable to think? He gave
an example: "Was George Washington more like a king or a prime minister?" A model that has
read a few thousand descriptions of each should be able to say "neither, and here's why"
without any document having said it for him. That is the thing training adds that a search
engine cannot.

When the fine-tuning examples were inspected, the worry turned out to be well-founded on the
training side. The set was correctly balanced between "decline the made-up thing" and "answer
the real thing", but every "answer" example was a definition. Nothing asked the model to
compare or judge. A model taught that confidence means "define a term" and anything harder
means "hedge" would fail exactly where Eric feared. Forty-three new examples were written that
afternoon — comparisons and judgements answered plainly, plus a handful that pair a real thing
with an invented one and ask the model to answer the first and decline the second in the same
breath. They were checked for overlap against the frozen test set before being added, because
training on the test is the one way to make every published number a lie.[^4]

## Finished, with two more bugs on the way out

The resumed run reached the end of pretraining a little after seven in the evening: nine
thousand steps, the remaining work done faster on twelve cores than the original run had
managed on sixteen, and a best validation perplexity of 14.7.[^5] The anneal stage took another
seventy minutes. Then the fine-tuning stage ran, and then the pipeline stopped itself, exactly
as it had been built to do the night before: the check that compares the exported model
against the original said the two disagreed.

That check turned out to be wrong, and the model underneath it turned out to be broken, and
those were two different problems. The check was wrong because the export had started carrying
a chat template inside it, and the llama.cpp program the check runs saw the template and
quietly switched into chat mode, wrapping the test prompt before continuing it. The original
model got the bare prompt; the exported one got a dressed-up version. Of course they
disagreed. One flag fixes it, and with the flag the export matches the original character for
character.[^6]

The model was broken for a reason that is embarrassing to write down and is being written
down anyway. The fine-tuning script was training the model to predict the word it had just
read rather than the word that comes next. That is an off-by-one, and it is the single most
classic mistake in this kind of code; the main training script warns about it in its own
opening comment and gets it right. The fine-tuning script was written separately and got it
wrong. The tell was that its reported error had dropped to almost nothing, which looked like
success and was the opposite: copying the previous word is trivially easy to learn, and a
model that has learned it produces the same word forever. Every question, answered with a page
of blank lines.

Worse: this meant the fine-tuned model scored the day before, the one recorded as producing
nothing coherent and blamed on being small, was not small. It was echoing. The earlier entry
stands as written, because that is the rule, and this one corrects it.

With the shift fixed, the fine-tuning stage was rerun in ten minutes, and the numbers said
something honest. The model reproduced its training examples word for word, which is what
happens when a very small model sees a very small set twenty-eight times. Asked about a prize
that does not exist, it declined, in the right voice. Asked about something real that it was
not trained on, it produced sentences that sounded like answers and contained nothing. On the
frozen test, it refused the made-up questions at a rate no baseline touched, and it refused
the real ones too: it answered three percent of the questions it should have answered. The
evaluation harness prints a warning under its own table for exactly this case: a low bluff
rate means nothing on its own. That model did not bluff because it barely said anything. It
had been predicted in the decision log days earlier as the failure mode of abstention training
on a model without knowledge, and there it was, measured. The cure is not less abstention
training; it is a model that has read a hundred times more, which is what the rented-GPU runs
in Chapter 10 are for.

Then the rest ran: the export, the fidelity check (passed), two quantised copies, the offline
audit, the package, the copy to the USB stick. The "pipeline complete" line was not taken at
its word this time either. The stick was listed, and a question was typed into the model
running from it. It answered, correctly, at nine hundred tokens a second. The answer was one it
had memorised, but the chain from a checkpoint on this disk to a running model on a stick in
the front of the machine was proven end to end, with every stage having failed at least once
along the way and been fixed.

The machine stayed up for the whole five and a half hours.

---

[^1]: `runs/real_pretrain.pre-freeze.bak.jsonl`; the freeze is D-47 in `docs/DECISIONS.md`.
[^2]: `scripts/master_pipeline.sh`, `RESUME_PRETRAIN=1`.
[^3]: The user-space memory test came back clean; the firmware was already current; a
bootable memory test and a graphics-driver update were deferred until the machine was idle.
The cause remains unknown as of this draft.
[^4]: `sft/build_synthesis_seed.py`, 43 conversations; D-48.
[^5]: **Corrected later.** Two days after this run, while pulling numbers for Chapter 4, the
validation split turned out to be the first one percent of a source-shuffled stream — a
single source, and for this run that source was Solidity code. The 14.7 is the model's
perplexity on Solidity, not on its corpus; the training loss at the same step implies a
mixture perplexity nearer 90. The split has since been made to sample the whole stream. The
number is left here as it was recorded, with this note, because that is the rule (D-60).
[^6]: `scripts/verify_gguf.py`, `-no-cnv`. The same quirk bit the evaluation script's "raw"
mode and the offline audit two days later — three times is a pattern, and it is now a line in
the project's standing rules.
