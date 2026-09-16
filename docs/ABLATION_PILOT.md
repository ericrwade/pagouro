# M4 ablation pilot — method, and a flaw in it

Run 2026-09-16. **This is a methodology pilot. The finding is worthless and the method is the
deliverable.** At ~12.6M parameters on ~6M tokens, no result about corpus composition means
anything. What was being tested is whether the comparison machinery is sound before M4 spends real
money on runs where the answer would count.

It is not sound yet. That is the useful outcome.

## What was run

Two arms, identical in every respect but one.

| Held constant | Value |
|---|---|
| Model | 12.6M params, dim 384, 6 layers, 6 heads, 2 KV heads |
| Steps / tokens | 1,200 steps, ~4.9M tokens |
| Seed | 1337, both arms |
| Learning-rate schedule | identical cosine, identical warmup |
| **Tokenizer** | **one shared tokenizer**, trained on a combined sample of both corpora |
| Total corpus size | identical to within 1% |

| Varied | Arm A | Arm B |
|---|---|---|
| Corpus | 100% FineWeb-Edu | 85% FineWeb-Edu + 15% code |

The shared tokenizer matters more than it looks. Training a separate tokenizer per arm would change
where token boundaries fall, and perplexity computed over different tokenizations is not comparable
at all. That confound was anticipated and controlled.

Arm B **substitutes** code for web text rather than adding it, so B does not get more data. It gets
different data in place of some. Otherwise the comparison would measure corpus size, not
composition.

## The flaw: the two arms have different validation sets

`tokenize_corpus.py` holds out a validation slice **from the corpus it is given**. So arm A's
validation set is web text and arm B's contains code.

The two validation perplexities are therefore **not comparable**. B is being scored on a different
distribution than A, and any difference between them confounds "did code help the model reason"
with "is code easier or harder to predict than prose." The second effect is almost certainly larger
than the first, which means the headline number the pilot produces is meaningless in a way that
would look entirely publishable.

This is precisely the class of error the pilot existed to find, and it would have been invisible in
a chart. Two curves, both descending, one slightly lower, and a confident caption.

## What M4 must do instead

1. **One shared, held-out validation set for every arm**, drawn from a source used by *none* of the
   training arms. A third slice of FineWeb-Edu not present in either corpus is the obvious choice.
   Every arm is then scored on identical text.
2. **Lead with the downstream evaluations, not perplexity.** The frozen suite is already shared
   across models by construction, which sidesteps the whole problem. Perplexity becomes a secondary
   sanity check rather than the headline.
3. **Add a standard reasoning benchmark** so the claim connects to numbers outside this project.
4. **Run each arm at more than one seed.** At small scale, seed variance can easily exceed the
   effect being measured, and a single pair of runs cannot tell the two apart.
5. **Pre-register the comparison** the way `TARGETS.md` pre-registers the suite: state what counts
   as a real difference before seeing any curve.

## Other limitations, recorded

- **The code slice is Rosetta Code** (GFDL, ungated, streams without authentication). Chosen because
  every permissively licensed code corpus checked was either gated behind a licence agreement (the
  whole BigCode family, see D-28) or built on a loading script the current `datasets` library no
  longer supports. GFDL is share-alike, so it falls under O-11 and is **not a candidate for the real
  corpus**. Pilot only.
- Rosetta Code is curated task solutions across many languages. That is not representative of the
  code a real corpus slice would contain, and it is unusually dense in short, complete programs.
- 1,200 steps is far short of convergence. Both arms are still improving when the run ends.

## What the pilot did prove

The harness itself works. Two arms ran isolated, with separate checkpoints and separate logs, one
shared tokenizer, matched token budgets and a fixed seed, all driven by a single reproducible
script. That plumbing is now in place and tested, which was the point.

It also surfaced a bug worth recording: the first attempt at giving each arm its own log file
silently failed to patch one of two references, so both arms would have appended to the same file.
The curves would have interleaved into a single log and the comparison would have been nonsense that
looked fine. Caught by reading the file back rather than trusting the edit had applied.

## Numbers

Recorded for completeness. **Do not cite these.** See the flaw above: the arms were scored on
different validation sets, so the comparison is invalid by construction.

*(Filled in when both arms complete; see `runs/ablation_a_web.jsonl` and `runs/ablation_b_code.jsonl`
for the raw curves.)*
