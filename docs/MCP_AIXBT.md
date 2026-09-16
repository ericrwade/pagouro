# aixbt MCP — crypto intelligence

Filed 2026-09-16 because Eric has access and expects the project may raise crypto questions.
**Not currently wired into any session.** This doc is what a future session needs to turn it on.

Docs: <https://docs.aixbt.tech/developers/mcp>

## Verified working, 2026-09-16

I probed the server directly over HTTP with no credentials and no client config.

| Check | Result |
|---|---|
| Endpoint | `https://api.aixbt.tech/mcp` |
| Transport | streamable HTTP |
| Server identity | `aixbt` v1.0.0, MCP protocol 2024-11-05 |
| Tools exposed | 12 |
| Public call without a key | **worked** — `list_topics` returned 25 live topics |

The server describes itself as read-only crypto intelligence over Projects, Topics, Intel,
Reports, and community Clusters. Every tool is annotated `readOnlyHint: true`.

## The 12 tools

| Tool | What it does | Needs a key |
|---|---|---|
| `list_topics` | current crypto topic landscape | no |
| `get_topic` | one topic with recent context | no |
| `get_topic_series` | attention history for a topic | yes |
| `list_projects` | find tracked projects by chain, ticker, category, address | yes |
| `get_project` | one project with recent intel and related projects | yes |
| `get_project_series` | attention history for a project | yes |
| `list_intel` | search recent crypto developments | yes |
| `get_intel` | one development with sources and context | yes |
| `get_report` | a published aixbt report with sources | yes, plus `topic-reports` entitlement |
| `get_vocabulary` | current valid filter values | yes |
| `list_clusters` | audience communities driving attention | yes |
| `me` | the current credential's entitlements, limits, history window | yes |

Only MCP discovery, `list_topics` and `get_topic` are public. Everything else needs OAuth or an
account-backed API key.

## To enable it

1. Create a key at <https://aixbt.tech/profile#developer-access>.
2. Put it in `.env` as `AIXBT_API_KEY=...`. Never inline it into a config file that gets committed.
3. Add the server. The vendor's config shape:

```json
{
  "mcpServers": {
    "aixbt": {
      "type": "streamable-http",
      "url": "https://api.aixbt.tech/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

In Claude Code, prefer `claude mcp add` over hand-editing, and keep the key out of any file under
version control.

## Why it is not enabled yet

Wiring in an MCP server puts all 12 tool schemas into every session's context whether or not crypto
comes up. Those schemas are large; `list_projects` alone carries a long input and output schema.
Enable it when the brief shows crypto is actually in scope, not before.

`run `curl` against the endpoint as above for a one-off question — the public tools need no setup
at all.

## Unknown

Pricing and rate limits are not stated in the docs. Call `me` once a key exists; it reports the
credential's limits. Establish that before any loop that calls this server repeatedly.
