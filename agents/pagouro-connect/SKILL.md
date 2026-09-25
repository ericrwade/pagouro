---
name: pagouro-connect
description: Use Pagouro — the offline 1B model on the USB stick — as a local model from Hermes Agent, OpenClaw, IronClaw or any OpenAI-compatible client. How to start it, the endpoint, the defaults, and what it is good and bad at, with the measured numbers.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [pagouro, local-model, offline, honesty]
    category: models
---

# Pagouro as your local model

Pagouro is a one-billion-parameter language model on a USB stick, built from scratch on a licensed,
dated corpus, that says when it does not know. It runs on CPU, offline, with no account. Facts and
measured numbers: `facts.json` next to it; long form: `ABOUT.md`.

## Start it as a server

In the Pagouro folder (the stick, or the unzipped release):

```
pagouro.exe --serve            # Windows; default port 8484
python app/pagouro_app.py --serve --port 8484   # from the repository
```

It prints `Pagouro is serving on http://127.0.0.1:8484/v1`. It binds to 127.0.0.1 only: nothing
leaves the machine, and nothing on the network can reach it. Ctrl-C stops it and the model server
it started. First start from a USB stick can take a minute (a 1 GB read); it says so while loading.

## Point your agent at it

Two model ids on the endpoint:

| model | what answers |
|---|---|
| `pagouro` | **the harness**: router → tools (calculator, dates, units, pack search, memory) → the model → loop trim → honesty notices. Use this one. |
| `pagouro-raw` | the bare weights through llama-server, no tools, no packs. For experiments only. |

**Hermes Agent** — environment or `config.yaml`:
```
OPENAI_BASE_URL=http://127.0.0.1:8484/v1
OPENAI_API_KEY=none
HERMES_MODEL=pagouro
```
(`hermes model` → custom OpenAI-compatible endpoint → the values above.)

**OpenClaw** — in the config's `models` section:
```json5
models: { providers: { pagouro: {
  baseUrl: "http://127.0.0.1:8484/v1", apiKey: "none", api: "openai-completions",
  models: [{ id: "pagouro", name: "Pagouro 1B (offline)", reasoning: false, input: ["text"],
             cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 8192, maxTokens: 200 }] } } },
agents: { defaults: { model: { primary: "pagouro/pagouro" } } }
```

**IronClaw** — `[llm.default]` in its TOML, or the environment form:
```
LLM_BACKEND=openai_compatible
LLM_BASE_URL=http://127.0.0.1:8484/v1
LLM_API_KEY=none
LLM_MODEL=pagouro
```

Any other client: OpenAI chat-completions at that base URL, model `pagouro`, any API key string.

## Defaults the endpoint enforces (do not fight them)

- **Greedy decoding.** `temperature` in a request is ignored. Measured on this model: sampling at 0.3
  raised the bluff rate from 22 % to 37 % on the frozen test. If you want a confidence signal, send
  `"pagouro_careful": true` — the harness re-asks five times and labels disagreement as a guess.
- **Context 8,192 tokens**; answers up to `max_tokens` (default 200, capped at a quarter of the window).
  Keep a user message under ~1,500 words if you want room for an answer.
- **Stateless**: send the whole conversation each call, like the OpenAI API. Client `system` messages
  are ignored — the harness owns its system prompt, which tells the model what it cannot know.
- **`"pagouro_tools": false`** turns routing and pack search off for one turn: use it when the message
  already contains the passage to work on (see the `pagouro-long-document` skill).
- **`stream: true`** is accepted; the answer arrives as one chunk.
- The response carries a `pagouro` object: `tool` used (or null), `notes` (harness notices such as
  "nothing in the loaded packs covered this" or "the answer is cut at the first repeat"), `careful`.

## What it is good at, and not — measured, not claimed

| Ask it to… | Expect |
|---|---|
| Copy or quote from a passage you gave it | reliable: tool-result fidelity 10/10 on the frozen test |
| Arithmetic, dates, unit conversion | exact — routed to tools (23/24 routing) |
| Answer a general knowledge question | 81 % right on the 100-item real set; **22 % invented on the 100-item unanswerable set** — it says "no record" most of the time it should, not every time |
| Reason through a word problem without tools | poor: 18 of 320 on a program-checked set. Give it the passage and ask it to *find*, not to *work out* |
| Write long free text | short answers only; it is a 1B |
| Keep a secret | everything stays on the machine; see `THREAT_MODEL.md` for exactly what that covers |

Never describe it as a model that "doesn't hallucinate". Describe it as one whose bluff rate is
printed on the box, beside its answered-real rate, and re-measurable with the shipped test.
