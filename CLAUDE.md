# PAGOURO — project operating rules

This file auto-loads whenever a session touches `C:\Users\Eric Wade\PAGOURO_BUILD`.
It is the standing contract for this project. Keep it short; detail lives in `docs/`.

## What "Pagouro" means

When Eric says **Pagouro**, **Paguro**, **the LLM project**, or **our LLM project**, he means
this folder and the work described in `PAGOURO_BRIEF.md`. Both spellings refer to the same
thing — the folder spelling `PAGOURO` is the one to use in writing, code, and repo names
until Eric says otherwise.

## Start of every session — in this order

1. Read `START_HERE.md` (this folder). It is the session-open checklist.
2. Read `docs/DECISIONS.md`. **This is the highest authority.** Do not re-litigate anything
   marked LOCKED.
3. Read `PAGOURO_BRIEF.md`, the origin document. It governs everything `DECISIONS.md` does not
   address. Where the two conflict, **`DECISIONS.md` wins** — it carries later decisions made with
   Eric directly. The brief carries a precedence notice listing what is superseded.
4. Read `docs/THREAT_MODEL.md`. It is binding on every privacy claim in the README and the UI.
5. Read the last entry in `docs/SESSION_LOG.md` to pick up where we left off.
6. Run `scripts/preflight.sh` to confirm keys and tooling are live.

## Hard rules

- **Secrets never enter the transcript.** The OpenRouter key lives in `.env` (gitignored) or a
  user env var. Do not `cat .env`, do not echo the key, do not paste it into a file that gets
  committed. Verify a key by *using* it, not by printing it.
- **Never commit `.env`.** Check `git status` before every commit. `.gitignore` covers it, but
  check anyway.
- **Cost is real.** Every OpenRouter call spends Eric's money. Before any loop, batch, or
  eval run, state the model, the request count, and the rough cost. Default to the cheapest
  model that can do the job; escalate deliberately.
- **`DECISIONS.md` governs.** Where it and the brief conflict, `DECISIONS.md` wins. Never revert a
  locked decision to match the older brief.
- **Never claim privacy protection `THREAT_MODEL.md` does not grant.** People in genuinely risky
  situations may rely on this. An overclaim is a safety failure, not a documentation error.
- **Provenance is the product.** No byte enters the corpus without a nameable license and a ledger
  row. When rights are unclear the answer is no. The entire differentiator is that the claim holds
  up under inspection, and one unlicensed source destroys it.
- **Log decisions as they happen**, in `docs/DECISIONS.md`, not at the end of the session.
- **Append to `BUILD_LOG.md` at the end of every session.** It is the narrative story of the build,
  written for readers rather than for sessions, and Eric may self-publish it. Append only, oldest
  first, never revise an earlier entry. **Keep the mistakes in, especially your own** — a build log
  that records only the parts that worked is marketing, and this project's whole pitch is that its
  claims survive inspection. Numbers must be measured, not remembered.

## Inherited rules from the global CLAUDE.md that bite hardest here

- Don't stop and ask permission for in-scope work. Build it, flag concerns in the report.
- Keep the permission allowlist current. If a routine command prompts Eric, add its pattern to
  `~/.claude/settings.json` in the same turn.
- `cd` does **not** reset between Bash calls. Use `git -C <repo>` or an explicit `cd` for every
  git command, and check the hash printed back.
- Verify on the case that actually exercises the change, and say which case was checked.
