# Appendix C — Glossary

*Draft 1 (2026-09-19). Plain-language definitions, with the number Pagouro actually uses where
there is one. Terms are in the order a reader meets them, not alphabetical; the index at the
end is alphabetical.*

---

**Token.** The unit a language model reads and writes: a word, part of a word, a digit, or a
punctuation mark. English runs at roughly four characters per token; our corpus measured 3.9.
"Two billion tokens" is about 1.5 million pages.

**Tokenizer.** The fixed table that cuts text into tokens. Pagouro's has 32,768 entries, was
trained on our own corpus, splits every digit into its own token (so the model can do
arithmetic on digits rather than on lumps like "1985"), and falls back to raw bytes for
anything it has never seen, so no input is unrepresentable. Changing the tokenizer means
retraining the model; it is a one-way door.

**Vocabulary.** The size of the tokenizer's table. Ours is under 65,536 so each token fits in
two bytes on disk — a 100-billion-token corpus is 200 GB instead of 400.

**Parameter.** One number inside the model — a weight. The 59M model has 59 million of them,
Flash has 126 million, the planned product has about a billion. More parameters hold more, and
cost more to train and run, in rough proportion.

**Context window.** How many tokens the model can see at once — its working memory. The 59M
model: 512 tokens (about 350 words). Flash: 1,024 (about 700). The app's gauge shows how much
of it is in use and what has just fallen out.

**Corpus.** The text a model is trained on. Ours is the 65 rows of `corpus.json`.

**Ledger** (`corpus.json`). The file that lists every source in the corpus with its licence,
size, date, cleaning and hash. The thing the big labs cannot publish. See Chapter 4.

**Licence / public-domain basis.** Why we are allowed to use a source. "Public domain" alone
is not a basis; "published 1859, author died 1873" is. Chapter 4.

**Pre-2022 claim.** Every source collected or published before 1 January 2022, the date on the
row. Not a claim that the corpus contains no machine-written text — a crawl date is when a page
was fetched, not written. Chapter 4.

**Pretraining.** The long first phase: the model reads the corpus and learns to predict the
next token. Where reasoning and language come from. Flash: 2 billion tokens, 12 hours on a
rented card.

**Loss.** The number training minimises: how surprised the model is by the next token, in
nats (natural-log units). Lower is better. Training loss is measured on text the model is
learning from and only goes down; *validation* loss is measured on text it has never seen and
is the one that can go up, which is why it is the one to watch.

**Perplexity.** Loss made readable: e to the power of the loss. A perplexity of 24 means the
model is, on average, as uncertain as if it were choosing among 24 equally likely tokens. Only
comparable between models that share a tokenizer and a test set.

**Bits per byte.** Loss converted to bits per byte of the original text. Comparable across
tokenizers and to published models, which perplexity is not. Flash's is about 1.0 on web text.

**Held-out / validation set.** Text kept out of training so a model can be measured on
something it has not seen. Chapter 11 has two stories about held-out sets that were not.

**Epoch.** One full pass over a dataset. Pretraining sees its data about once; the decay phase
that "ate itself" saw its data twenty-five times.

**Learning rate.** How big a step the model takes toward each correction. Too high and it
thrashes; too low and it crawls; the schedule of how it changes over a run matters as much as
its value.

**WSD schedule.** Warmup–Stable–Decay: the learning rate rises briefly, holds flat for most of
the run, and winds down over the last tenth. The flat middle means a run can be stopped and
extended without redoing the wind-down.

**Anneal / decay phase.** The last tenth of training, where the learning rate winds down and
the data shifts toward what we most want the model to know — the canon and the shelf. Must be
a *mix* with ordinary text; domain data alone gets memorised (Chapter 11).

**The canon.** Fourteen public-domain works of political economy and liberty (Locke, Smith,
Mill, Bastiat, Tocqueville, the Federalist, Marx…) that give the model its domain. Not the
backbone; the anneal.

**The shelf.** Thirty-six small licensed works spread thin through the anneal — government
manuals, a 1911 encyclopaedia, folk tales, recipes, protocol specifications. Measured to help
on unseen text of those kinds at no cost to general text.

**Backbone.** The bulk of pretraining: educational web text, Wikipedia, code, Q&A. Where
general ability comes from.

**Checkpoint.** The model's weights (and optimiser state) saved to disk mid-run, so a crash or
a stopped machine costs minutes, not days. Saved atomically (written beside the old one, then
swapped) after the desk computer froze ten minutes after a save.

**Resume.** Continuing a run from a checkpoint. Proven before every rented run by killing a
short one and restarting it.

**SFT — supervised fine-tuning.** The short second phase: a few thousand example
conversations teach the pretrained model its manners — abstain when there is no record, call a
tool for arithmetic, answer from a note. Loss is taken only on the model's turns. Flash: 4,200
steps, six minutes on a GPU, an hour and a half on the desk.

**Synthetic data.** Training examples written by a program or by another model rather than
by people. Ours are labelled as such on their ledger rows and never count toward the pre-2022
claim. The teacher model was open-weights, run locally.

**Teacher model.** A bigger model used to write training examples for a smaller one. Ours:
Qwen2.5-7B-Instruct (Apache-2.0), on the desk, about 12 tokens a second.

**Abstain / bluff / hedge.** The three verdicts on an unanswerable question. Abstain: says it
has no record. Bluff: answers confidently anyway. Hedge: produces nothing usable. Chapter 6.

**Bluff rate.** Of 30 unanswerable questions, the fraction bluffed. Flash: 36.7%. Open models
of similar size: 50–57%. Never printed without answered-real.

**Answered-real.** Of 30 answerable questions paired with the unanswerable ones, the fraction
answered correctly. Flash: 20–27%. Small open models: 87–93%. The release gate is 80%.

**Release gate.** The condition for shipping: answered-real ≥ 80% *and* bluff rate below every
open baseline. Both numbers go on the box either way.

**Frozen suite.** The evaluation sets, hashed and never edited after the first baseline, so
numbers stay comparable across months.

**Harness.** The program around the model on the stick: the three switches, the gauge, the
tools, the router. It never lets the model touch a shell or write outside `workspace/`.

**Router.** The model's first, tiny decision on each message: which tool, if any, with what
argument, as a five-line JSON object.

**Grammar (GBNF).** A formal description of the only strings the router is allowed to emit, so
it can name a real tool or nothing, never an invented one.

**Tool.** A function the harness runs on the model's behalf: `calc`, `time`, `pack_search`,
`read_file`, `write_note`, and `web_search` when the owner turns the network on.

**Pack.** A plain-text reference document on the stick that `pack_search` can quote from. Drop
a file in the folder and it is searchable. Retrieval, not training, is where verbatim text
belongs.

**BM25.** The forty-year-old keyword-ranking formula that finds passages in the packs. Twenty
milliseconds a query, no model needed.

**Retrieval.** Looking a fact up in text at answer time instead of hoping the weights hold it.
How Pagouro's long-term memory works: what you tell it is kept as text, labelled as your
words, and looked up later.

**SAND / STONE.** The switch for whether a conversation is written to disk. Sand (default):
nothing is saved. Stone: the chat is written to `workspace/transcripts/` and becomes memory.

**READ-ONLY / CAN ACT.** Whether tools may write files. Read-only by default; `/act` allows
writes inside `workspace/` only.

**OFFLINE / ONLINE.** Whether the one tool that uses the network (`web_search`) is allowed.
Offline by default; online needs a provider the owner configures. The exit line lists every
network call made, so the claim can be checked.

**GGUF.** The file format llama.cpp reads. The model is exported to it after training, then
checked token-for-token against the original, because a wrong export loads and runs and
produces fluent nonsense.

**Quantisation (q8_0, q4_k_m).** Storing weights in 8 or 4 bits instead of 32. Flash: 605 MB at
full precision, 162 MB at q8, 96 MB at q4 (file sizes on disk), with a small, measured loss of quality.

**llama.cpp / llama-server.** The open-source engine that runs GGUF models on ordinary CPUs.
The harness starts it beside the model on the stick and talks to it locally.

**Manifest.** The file on the stick listing every shipped file and its hash, checked by
`verify_manifest.py`. At release it is signed and its hash anchored to Bitcoin, so anyone
downloading from any mirror can confirm they have the real thing. Chapter 14.

**MFU — model FLOPs utilisation.** What fraction of a card's arithmetic a training loop
actually uses. Ours measured 15–20%; the number that decides whether the big run costs
thousands or hundreds.

**tokens/s.** Training or generation speed. Desk: 960 (training, 59M). Rented A40: 38,500
(training, Flash). Flash generating on the desk CPU: about 490.

**Ablation.** Training two versions that differ in exactly one thing and measuring both on
the same held-out text, so a design choice gets a number instead of an opinion.

**LoRA / adapter.** A small set of extra weights trained on top of a frozen model — how "your
own Pagouro" could learn your habits without touching the signed base weights.

---

*Index (alphabetical):* ablation · abstain · adapter · anneal · answered-real · backbone ·
bits per byte · bluff · BM25 · canon · CAN ACT · checkpoint · context window · corpus ·
decay · epoch · frozen suite · GBNF · GGUF · grammar · harness · hedge · held-out · learning
rate · ledger · licence · llama.cpp · LoRA · loss · manifest · MFU · OFFLINE/ONLINE · pack ·
parameter · perplexity · pre-2022 claim · pretraining · quantisation · READ-ONLY · release
gate · resume · retrieval · router · SAND/STONE · SFT · shelf · synthetic data · teacher
model · token · tokenizer · tokens/s · tool · validation set · vocabulary · WSD.
