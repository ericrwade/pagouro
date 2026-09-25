# Pagouro for agents

Skills that teach an agent framework to use Pagouro as its local, offline model. They follow the
**agentskills.io** `SKILL.md` format, which Hermes Agent (Nous Research), OpenClaw and Venice's
skill runtime all read; IronClaw (NEAR AI) uses WASM tools instead, so it takes the connection
settings from `pagouro-connect` and needs no skill file.

| folder | what it teaches |
|---|---|
| `pagouro-connect/` | start `pagouro.exe --serve`, point the agent at `http://127.0.0.1:8484/v1` (model `pagouro`), the defaults the endpoint enforces, and what the model is good and bad at — with the measured numbers |
| `pagouro-long-document/` | interview the user → build a fixed outline of questions → read a long document in chunks a 1B can hold → keep going until every chunk × question is done → write up. Pagouro finds and quotes; the agent judges. Runner: `scripts/chunk_review.py`; worked example: the book |

## Install

Hermes Agent: copy a folder into `~/.hermes/skills/pagouro/<folder>/`; it appears as `/pagouro-connect`
and `/pagouro-long-document`. OpenClaw: into the workspace skills directory. Or hand the agent the
`SKILL.md` as context; it is plain text.

## The one rule

Everything here keeps Pagouro's promise: the endpoint binds to 127.0.0.1, decodes greedily (measured:
sampling costs honesty), and the harness — not the client — owns the system prompt. An agent gets the
whole product through the endpoint, not the bare weights, unless it asks for `pagouro-raw` on purpose.
