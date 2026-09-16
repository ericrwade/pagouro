# OpenRouter setup

## CURRENT STATE (2026-09-16)

Eric has **two OpenRouter accounts**. The key in `.env` now belongs to the one he intends to use.
An earlier session used a key from the *other* account by mistake; that key was replaced.

| Item | State |
|---|---|
| Key in `.env` | correct account, 73 chars, verified live |
| Account tier | `is_free_tier: false` — a funded account, not the free tier |
| Default model | `deepseek/deepseek-v4.1-flash`, resolved from `OPENROUTER_DEFAULT_MODEL` |
| End-to-end call | **working** — billed $0.000023 on a test completion |
| Catalog | 443 models, 20 of them `:free` |
| Credit cap on key | **none set** |

### Still open for Eric

1. **Set a per-key credit cap** at <https://openrouter.ai/keys>. The key is uncapped.
2. **Revoke the keys on the other account.** Two keys were created there during setup, and one of
   them was partially printed into a session transcript. Neither is in use now. Killing them closes
   the exposure permanently.

### Do not trust the usage counters

`GET /api/v1/key` reported `$0.0000` usage at the same moment paid calls were succeeding and being
billed. The counters lag. Never conclude from them that spending is not happening. The `is_free_tier`
flag does appear reliable: it read `true` on the free account and `false` on the funded one.

### Smoke test

```bash
python scripts/smoke.py                              # uses the .env default model
python scripts/smoke.py --list-free                  # current free slugs
python scripts/smoke.py --model <slug> --prompt "hi"
```

It prints the reply, token counts, cost, and serving provider, and never prints the key.

Free models vary wildly. `nvidia/nemotron-3.5-lightning:free` emitted its chain of thought into the
reply field on a trivial prompt; `nex-agi/nex-n2.5-mini:free` answered correctly in 5 tokens. Test a
slug before relying on it.

## What I need from Eric

Exactly one thing: **an API key, placed in a file — never pasted into chat.**

1. Create/sign in at <https://openrouter.ai>.
2. Add credits at <https://openrouter.ai/credits>. Start small; $10 lifetime spend also raises
   the free-tier daily cap from 50 to 1000 requests, which is a useful side effect.
3. Create a key at <https://openrouter.ai/keys>.
   - **Set a credit limit on the key.** This is the single most important setting. A key with a
     $20 cap cannot drain the account if a loop misbehaves.
   - Name it `pagouro-dev` so it can be revoked independently later.
4. Put it in this project's `.env`:

```bash
cd "C:\Users\Eric Wade\PAGOURO_BUILD"
cp .env.example .env
# then edit .env and paste the key after OPENROUTER_API_KEY=
```

`.env` is gitignored. Do not paste the key into the chat window — anything in the transcript
is stored, and I will never need to see the literal string to use it.

Then tell me it's in place and I'll verify with `scripts/preflight.sh`, which calls the key-status
endpoint and reports the credit limit without printing the secret.

## Decisions Eric still owns

| Question | Why it matters | Default if unanswered |
|---|---|---|
| Which models? | Cost varies ~100x across the catalog | Pick per task after reading the brief |
| Logging / privacy | Some cheap providers train on prompts | Review <https://openrouter.ai/settings/privacy> before first real run |
| Zero-data-retention only? | Restricts the model pool, raises cost | Off unless the brief requires it |

If the brief involves anything confidential, set the privacy policy **before** the first call.
Provider routing is per-request but the account default is what protects you from mistakes.

## Technical reference

**Base URL:** `https://openrouter.ai/api/v1`
**Endpoint:** `POST /chat/completions` — OpenAI-compatible, so the `openai` SDK works unchanged.

Headers:

| Header | Required | Purpose |
|---|---|---|
| `Authorization: Bearer $OPENROUTER_API_KEY` | yes | auth |
| `Content-Type: application/json` | yes | for raw HTTP calls |
| `HTTP-Referer` | no | app attribution on OpenRouter's leaderboards |
| `X-OpenRouter-Title` | no | app name on those leaderboards |

Using the OpenAI Python SDK:

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
resp = client.chat.completions.create(
    model="anthropic/claude-sonnet-5",
    messages=[{"role": "user", "content": "ping"}],
)
```

**Key status:** `GET https://openrouter.ai/api/v1/key` returns `limit`, `limit_remaining`,
`usage`, `usage_daily`/`weekly`/`monthly`, and `is_free_tier`. This is how preflight verifies the
key is live and how we watch spend. It never returns the key itself.

**Model catalog:** `GET /api/v1/models`, or browse <https://openrouter.ai/models>. Model slugs
look like `anthropic/claude-sonnet-5`, `openai/gpt-...`, `meta-llama/...`. Slugs ending in
`:free` are free but rate-limited.

**Rate limits:**

| Tier | Limit |
|---|---|
| `:free` models, under $10 lifetime spend | 20 req/min, 50 req/day |
| `:free` models, $10+ lifetime spend | 20 req/min, 1000 req/day |
| Paid models | No platform cap; upstream providers may throttle |

On a 429, retry with exponential backoff and honor any `Retry-After` header.

## Cost discipline

Before any batch, eval, or loop, state the model, the request count, and the estimated cost in
the session. Default to the cheapest model that clears the bar. Escalate on purpose, not by habit.
