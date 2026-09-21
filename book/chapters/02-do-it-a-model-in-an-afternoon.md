# Chapter 2 — Do it: a model in an afternoon

*Licence: CC BY-SA 4.0 (instruction strand, D-64).*

*DO-IT chapter, draft 1 (2026-09-21). This is milestone 1 of the build, done again for you: the
whole pipeline at toy scale on one CPU, so that every later chapter is a change to something
that already works. The commands are the ones in `scripts/`; the numbers are from
`docs/SESSION_LOG.md` (2026-09-16) and `BUILD_LOG.md` Day 1, measured on a sixteen-core desktop
with no usable GPU. Footnotes name the file each number comes from.*

---

Nothing in this chapter produces a model worth talking to. The one it produces is twelve
million parameters, trained for half an hour, and when it was asked what a hermit crab is it
said: *"Like this time, the day of the time, he might have taken up of the day."*[^crab] That is
the correct result. What you are building is not a model; it is a *pipeline* — text in one end,
a file that any computer can run out of the other — and the point of building it small first
is that every piece is cheap to get wrong and cheap to fix. The real model, a hundred times
bigger, went through exactly these steps with exactly these scripts. Only the numbers changed.

You need: Python 3.12, about two gigabytes of disk, the repository, and an afternoon. No
graphics card. If you have one, ignore it for now.

## 0. The machine, and the thing that ate thirty of it

Before the first timing number, make sure nothing else is using the computer. This is not
housekeeping advice; it is the first bug the build hit. Training measured 141 tokens a second on
a chip that should have managed thousands, and the session spent an hour diagnosing the
numerical libraries before Eric mentioned that the box might be mining cryptocurrency. It was,
at 99 percent of the CPU, and had been for twenty-nine days. With the miner stopped the same
run did 4,308 tokens a second — thirty times faster, with no other change.[^miner] The failure
looked exactly like a broken toolchain. So: open the task manager, look at what is running, and
write down in your notes that the machine was idle when you took a number. A published speed
from a busy machine is worse than none.

```
python -m venv .venv
.venv\Scripts\activate            # on Windows; source .venv/bin/activate elsewhere
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install numpy tokenizers datasets huggingface-hub tqdm gguf
```

**What you should see:** `python -c "import torch; print(torch.__version__)"` prints a
version and no error.

## 1. Text you are allowed to use

Every byte that goes into a model in this book has a row in `corpus.json` saying what it is and
what licence it carries. The fetch script writes that row for you and refuses sources it cannot
name a licence for. For the afternoon model, take twenty thousand documents from FineWeb-Edu,
an open-licensed (ODC-By) crawl of educational web pages, which is also the largest slice of the
real corpus — so the path is the real one at toy scale.[^fetch]

```
python scripts/fetch_data.py --docs 20000
```

**What you should see:** a file `data/raw/fineweb-edu-sample-10BT.txt` of roughly 95 million
characters, and a new row at the end of `corpus.json` with a `sha256_processed` field.[^chars]
Open the row. It has the dataset name, the licence, the retrieval date and the hash. That row
is the difference between this project and most of the models you have used, and you just made
your first one.

## 2. A vocabulary

A model does not read letters; it reads *tokens*, pieces of text a few characters long, and the
list of pieces is the tokenizer. It is chosen once and it is a one-way door — change it later and
every tokenized byte on disk is invalid — so the build has an opinion about it, and the opinion
is in Chapter 3. For the afternoon, a vocabulary of 8,192 pieces is plenty:

```
python scripts/train_tokenizer.py --vocab-size 8192
```

**What you should see:** `data/tokenizer/tokenizer.json` and a `tokenizer_config.json` beside
it. The config carries a chat template — the markers that separate your turn from the model's —
and the vocabulary has tool-call tokens reserved from day one, because retrofitting those later
would mean re-tokenizing everything.[^tok] Check it round-trips: encode a sentence with an accent
or an emoji, decode it, and compare. The build's own check did that, including Unicode, before
going on.

## 3. Text to numbers

```
python scripts/tokenize_corpus.py
```

This turns the text file into two binary files of 16-bit integers, `data/tokenized/train.bin`
and `val.bin`, and a `meta.json` describing them. Sixteen-bit is deliberate: a vocabulary under
65,536 lets every token be stored in two bytes instead of four, which at the real corpus size is
the difference between two hundred gigabytes and four hundred.[^u16]

**What you should see** in `meta.json`: about 24.4 million training tokens, about 3.9 characters
per token.[^meta] If characters-per-token is near 1, the tokenizer did not train; if it is above 6,
you pointed it at the wrong file.

## 4. Train

The model is the project's own code: a small Llama-style transformer, deliberately matching
Llama's layout exactly, because the whole distribution story depends on a file that the standard
runner, llama.cpp, can load.[^llama] The defaults in `scripts/train.py` are the afternoon model.

```
python scripts/train.py --max-steps 2200
```

Watch the log. Every two hundred steps it evaluates on the held-out split and prints a
perplexity — roughly, how surprised the model is by text it has not seen, where lower is better.
It starts near the size of the vocabulary and should fall monotonically.

**What you should see:** about 12.6 million parameters reported at the start; 2,200 steps in
about thirty-one minutes on an idle sixteen-core CPU; validation perplexity falling from
roughly 8,800 to about 134, with no step where it jumps back up.[^train]

There is a trap under this step worth knowing about even though the script already avoids it.
The training target must be shifted one position — the model predicts the *next* token. Get that
wrong and position *t* can see token *t* in its own input; the loss collapses below the
theoretical floor and the run looks superb while learning nothing. The build checked the correct
behaviour numerically, 9.06 against a theoretical 9.01, rather than assuming it, and the first
fine-tuning script in this project nonetheless made the mistake anyway — which is a story for
Chapter 7.[^shift]

### Prove it can resume

Before you ever rent a machine by the hour, prove that a killed run restarts where it stopped,
because a silent resume failure on a rented GPU costs real money. Stop the training with Ctrl-C
somewhere past step 2,000, then:

```
python scripts/train.py --max-steps 2200 --resume
```

**What you should see:** the loss continues from where it was — the build's run was at 4.80
when killed at step 2,100 and resumed at 4.80 — not back at 9.[^resume] If it restarts at 9, the
checkpoint is not being loaded, and you have just saved yourself a rented hour.

## 5. Export, and the door that only opens one way

```
python scripts/export_gguf.py
python scripts/verify_gguf.py
```

The first command writes `data/gguf/pagouro-m1-f32.gguf`, the format llama.cpp reads. The
second is the one that matters. Exporting has a subtlety that produces silent, confident garbage
when you get it wrong: the project's attention code uses one convention for rotary position
embeddings and llama.cpp's Llama architecture expects the other, so the query and key weights
have to be permuted on the way out. If you get that wrong, the model loads. It runs. It emits
fluent nonsense. "It converted" is not evidence. The verifier greedily decodes the same prompt
through PyTorch and through llama.cpp and compares them character by character.[^export]

**What you should see:** `94/94 characters match`, or the equivalent for your prompt. Anything
less is a broken export, however good the text looks.

Then make it small:

```
tools\llamacpp\llama-quantize.exe data\gguf\pagouro-m1-f32.gguf data\gguf\pagouro-m1-q8_0.gguf Q8_0
```

**What you should see:** a 63-megabyte file becomes a 17-megabyte one.[^size] Eight-bit
quantisation costs almost nothing in quality at any size this book deals with; four-bit, which
the shipped model uses, is the trade the final chapters measure.

## 6. Talk to it

```
tools\llamacpp\llama-cli.exe -m data\gguf\pagouro-m1-q8_0.gguf -p "A hermit crab is" -n 40 -no-cnv
```

**What you should see:** grammatical English that repeats itself and means nothing, produced at
a couple of thousand tokens a second — the build measured 2,868 on this CPU.[^speed] Read it once
for the pleasure of having made it, and do not read anything into it. A twelve-million-parameter
model trained on twenty-four million tokens knows the shape of English sentences and nothing
else. The `-no-cnv` flag is load-bearing: once a GGUF carries a chat template, recent llama.cpp
builds start a conversation by default, and a raw continuation is what you want to look at
here.[^nocnv]

## What you have

A text file with a licence row. A tokenizer. A binary corpus. A checkpoint that resumes. A
`.gguf` that was verified, not assumed, to be the same model. And, if you wrote the numbers
down, a page of measurements from an idle machine that you can compare against the next run.
Everything from here is scale and care: more text (Chapter 4), a test written before the model
you want to measure (Chapter 6), a bigger transformer on a rented card (Chapter 11), and the
harness that makes a file into something a person can use (Chapter 8). None of those steps
introduces a new kind of thing. They are these six, larger.

---

[^crab]: `BUILD_LOG.md` Day 1, evening: the milestone-1 model's answer, quoted verbatim.
[^miner]: `BUILD_LOG.md` Day 1, "The thirty-fold lie": 141 tokens/s with the miner running (29,131 ms/step), 4,308 with it stopped (951 ms/step); `midstate.exe` at 2,519,748 s of CPU time. Rule D-23.
[^fetch]: `scripts/fetch_data.py` docstring; the ODC-By licence is recorded on the row it writes.
[^chars]: `data/tokenized/meta.json`: `source_chars` 95,340,108 for the 20,000-document slice.
[^tok]: `scripts/train_tokenizer.py`: the chat template and reserved tool tokens are written into `tokenizer_config.json`; D-33 for the real run's 32,768-piece vocabulary with digits split.
[^u16]: `BUILD_LOG.md` Day 1, "Then I read the transcript"; D-7.
[^meta]: `data/tokenized/meta.json`: `train_tokens` 24,417,484, `chars_per_token` 3.885, `vocab_size` 8192, `dtype` uint16.
[^llama]: `BUILD_LOG.md` Day 1, "The transformer"; D-21 (own the GGUF export; verify it every time).
[^train]: `docs/SESSION_LOG.md` 2026-09-16: 12.6M parameters, 2,200 steps, val perplexity ~8,800 → 133.7; `BUILD_LOG.md` Day 1: thirty-one minutes, 9 million tokens seen.
[^shift]: `BUILD_LOG.md` Day 1, "Training, and the trap underneath it": 9.06 measured against 9.01 theoretical; D-48 for the fine-tuning script that shipped without the shift.
[^resume]: `docs/SESSION_LOG.md` 2026-09-16: "killed at step 2100, resumed, loss continued at 4.80"; D-22.
[^export]: `BUILD_LOG.md` Day 1, "The one-way door"; `scripts/verify_gguf.py`; 94/94 characters.
[^size]: `docs/SESSION_LOG.md` 2026-09-16: GGUF 63.2 MB f32, 17.0 MB Q8_0.
[^speed]: `docs/SESSION_LOG.md` 2026-09-16: generation 2,868 tokens/s on the CPU.
[^nocnv]: `scripts/verify_gguf.py`, the comment on `-no-cnv`; the pipeline halted on exactly this flag once (`scripts/master_pipeline.sh`, note on START_STAGE).
