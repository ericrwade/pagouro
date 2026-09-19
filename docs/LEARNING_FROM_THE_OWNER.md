# Learning from its owner — how Pagouro can take in what you tell it, long term (O-23)

Eric, 2026-09-18: "Once Pagouro and its human have started conversing, is there any way to
ingest that conversation and over time their version of Pagouro integrates their input? Not
the context window — long term, almost like corpus again, a little at a time."

Yes. There are three levels, and the honest engineering answer is: the first is the one that
works well for a small model and it is already on the stick tonight; the second is the real
"their version of Pagouro" and it is safe only with three guardrails; the third is the thing we
already declined (D-57) because nobody can make it safe.

## Level 1 — Memory by retrieval (built, commit 3b6113a)

What the user says is kept as **text**, not as weights, and comes back through the same
`pack_search` tool the reference packs use.

- `/remember <text>` appends a dated line to `workspace/memory/remembered.txt`.
- Notes the model wrote (`write_note`, under CAN ACT) and every STONE transcript are indexed
  too. **Nothing is learned from SAND sessions** — they were never written down, so consent
  is the switch that already exists.
- In any later session, a question that touches those passages brings them back, labelled
  `YOUR OWN WORDS, from remembered.txt` (or from the transcript's filename), and the owner's
  words win near-ties against the packs. "What's my dog's name?" → the line where you told it.
- `/forget` deletes the remembered file; deleting a transcript forgets that session. It is
  all plain text the owner can read, edit, or carry to another stick.

Why this is the right default for a small model: it is exact (it quotes you rather than
paraphrasing you into a weight), it is honest (the label says these are your words, not the
world's facts), it is instant (no training, ~20 ms a query), it is private (the folder never
leaves `workspace/`), and it is reversible by deleting a file. Facts about *you* — names,
preferences, what you decided last month — are precisely the kind of thing retrieval handles
better than training does, at any model size.

What it is not: it does not change how the model *talks* or what it *assumes*. For that you
need level 2.

## Level 2 — Adapters trained on the owner's log (D-57; proposed, not built)

Periodically — a `/learn` command, or overnight — fine-tune a **LoRA adapter** (a small set
of extra matrices, a few megabytes) on the owner's STONE transcripts and remembered lines.
The base weights on the stick never change, so the manifest, the signature and the anchor
stay valid; the adapter is a separate file that is the owner's, like the memory folder.

Cost, measured against what we know: the CPU SFT on the 59M model ran 2,000 steps in 44
minutes at eight threads. A LoRA on the 126M Flash model over a few hundred conversations
is an hour on the desk computer; on the 1B model it is an overnight job on CPU or minutes on
a rented GPU. Every level of this can run on the owner's own machine.

The three guardrails, without which it should not ship:

1. **Replay.** Every learn mixes the owner's conversations with a slice of the original
   manners set (the abstention and tool-use conversations). Otherwise a few dozen chatty
   sessions erase "I have no record of that" — small models forget fast.
2. **The gate.** After every learn, the frozen suite runs. If the bluff rate rises or
   answered-real falls beyond a threshold, the adapter is not activated and the owner is
   told why. Same rule as the release gate (D-50), applied to the owner's own version.
3. **Rollback is a file delete.** Adapters are versioned (`workspace/adapters/2026-09-18.safetensors`);
   `/unlearn` removes the newest. The base is untouched by construction.

And one honesty rule that is not a guardrail but a design choice: level 2 should learn
**style, preferences and habits** — how you like answers, your vocabulary, what you always
ask next — and leave **facts** to level 1. A fact learned into weights becomes
indistinguishable from training knowledge; the model would state what you *told* it with the
same voice it states what the corpus taught it, and if you were wrong, it now bluffs with your
mistake. Retrieved facts keep the label. That division is the whole difference between a
model that adapts to you and one that flatters you.

## Level 3 — Continual pretraining, "corpus again a little at a time"

The owner drops documents (their own writing, manuals they use, their transcripts) into a
folder, and the model continues *pretraining* on them at a low learning rate — the same
anneal-style mechanics as the last 10% of the original run, in small doses.

It is possible and it is the same code path as level 2 with more tokens, but on a CPU the
arithmetic is against it at 1B: the desk machine trained the 59M model at ~960 tokens/s;
the 1B model is roughly fifteen times the work per token, so a million tokens of the owner's
documents is a night, and a real "corpus" is weeks. With a rented GPU it is an hour and a
few dollars. So level 3 is a feature for people with a GPU or patience, and for the same
reasons as level 2 it goes through a LoRA (base untouched, gate, rollback), never into the
base weights.

## The line we do not cross (D-57)

The model does not rewrite its own weights as it talks. That is the "real AGI" version of
the question and the reason we do not do it is not capability — a training step is one
function call — it is that there is no gate. A model that updates itself mid-conversation
cannot be evaluated before the update takes effect, cannot be rolled back to a known state,
and cannot be signed. Everything above is the version of "learns from you" that keeps the
three claims on the box true: it doesn't bluff (the gate), every byte is accounted for (the
owner's data is the owner's, in a folder, labelled), and nothing leaves the machine.

## What to build next, in order

1. Level 1 is done; the stick's README and `MAKE_IT_YOURS.md` get a paragraph (done below).
2. Level 2 on the Flash model as the experiment: a LoRA path in `train_sft.py`, the replay
   mix, the gate as a script (`scripts/gate.py`: run evals, compare to the base's numbers,
   exit 1 if worse), `/learn` and `/unlearn` in the app. One session of work; measured on the
   frozen suite before and after, and the numbers go in the build log either way.
3. Level 3 only after the 1B model exists and only behind the same gate.
