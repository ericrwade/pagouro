# Tutor item bank — schema

One item is one JSON object, one line in a `.jsonl` file under `tutor/items/`.

```json
{
  "id": "money-003",
  "topic": "money-and-economics",
  "question": "What does it mean for a currency to be inflated?",
  "reference_answer": "Its purchasing power falls, usually because the supply of money grows faster than the supply of goods and services it can buy.",
  "explanation": "Inflation is a ratio problem, not a moral one: more units of currency chasing the same real output means each unit buys less. The rate matters as much as the direction -- a little inflation is normal, a lot is corrosive.",
  "difficulty": 1,
  "source": "gutenberg-the-wealth-of-nations",
  "source_locator": "Book I, Chapter V",
  "distractors": [
    "Prices always go up over time regardless of the money supply.",
    "It only happens when a government intentionally prints money to pay debts."
  ]
}
```

## Field rules

| Field | Required | Rule |
|---|---|---|
| `id` | yes | `topic-NNN`, stable forever once assigned. Never reused. |
| `topic` | yes | one of the five slice names in `docs/TUTOR.md` |
| `question` | yes | plain text, one question |
| `reference_answer` | yes | the grading target. Short, factual, checkable. |
| `explanation` | yes | the *why*, shown after grading regardless of the learner's answer |
| `difficulty` | yes | 1 (foundational) to 3 (applies the idea to a new case) |
| `source` | yes | **must be a `slug` that exists in `corpus.json`**. The loader refuses to start on a violation. |
| `source_locator` | no | chapter/book/section, whatever helps a human find the passage |
| `distractors` | no | wrong answers for future multiple-choice mode; not used by the free-text grader |

## The rule this schema enforces

**Every item is traceable to a source that already cleared the corpus ledger's licence gate.**
The tutor does not introduce a second, looser standard of provenance — it inherits the same one.
An item bank entry with no `source`, or a `source` that is not in `corpus.json`, is a build error,
not a warning.

## Why explanation is separate from reference_answer

`reference_answer` is what the grader checks against — short and exact enough to match against a
free-text response. `explanation` is what a human actually learns from — the mechanism, not just
the fact. A tutor that only confirms right/wrong teaches test-taking. One that explains teaches the
idea. Both are shown after every attempt, regardless of whether the learner got it right.
