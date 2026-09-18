# GitHub setup

> **2026-09-17: the account question below is RESOLVED (D-5).** The account is `ericrwade`, the
> work email was removed, and git identity uses `266440753+ericrwade@users.noreply.github.com`.
> The section is kept as history. Repo strategy lives in `docs/ORIGIN_LEDGER.md` section F:
> private repo through the messy milestones, public + archived at release.

Status as of 2026-09-16.

## The account question — ~~UNRESOLVED, blocks repo creation~~ resolved, see above

Eric has two GitHub accounts. Both exist, both have zero public repos.

| Account | Created | Account ID | Email |
|---|---|---|---|
| `ericrwade` | 2026-03-08 | 266440753 | work email — Eric does not want this one |
| `ericrwade-commits` | 2026-03-15 | 268446754 | personal email |

The `-commits` suffix exists because GitHub auto-suggested it when `ericrwade` was already
taken by Eric's own earlier account.

**In-progress migration.** Eric wants the clean name `ericrwade` on his personal email. That
requires freeing the personal email from `-commits` first, since GitHub enforces one email per
account. He added a new email to `-commits` and made it primary, but deletion of the old one is
blocked by "you must set a password first" — `-commits` was created via social login (Google or
Apple) and has no password. The unblock is: set a password via
<https://github.com/password_reset>, then the delete control activates.

**Until this resolves, do not create the repo.** Creating it under the wrong account means
transferring it later, which breaks clone URLs and any CI wiring.

Ask Eric which account to use at the start of the first build session. If he wants to move
forward before the migration finishes, `-commits` is the safe choice — it is already on his
personal email and can be renamed later at Settings, Account, Change username (GitHub sets up
redirects, though local remotes still need updating).

## Machine state

| Item | State |
|---|---|
| git | 2.54.0.windows.1 installed |
| git global user.name | **not set** |
| git global user.email | **not set** |
| GitHub CLI (`gh`) | 2.101.0, installed 2026-09-16 via winget (`GitHub.cli`) |
| `gh auth` | **not logged in** |
| SSH keys (`~/.ssh`) | none |
| Repo | not created |

## Setup sequence, once the account is chosen

1. **Set the git identity.** Use GitHub's noreply address to keep the real email out of commit
   history. Find it at Settings, Emails, "Keep my email addresses private".

```bash
git config --global user.name "Eric Wade"
git config --global user.email "<id>+<username>@users.noreply.github.com"
```

2. **Authenticate the CLI.** This is interactive and opens a browser, so Eric runs it himself
   in the session with a `!` prefix:

```
! gh auth login --hostname github.com --git-protocol https --web
```

HTTPS + the CLI's credential helper avoids needing SSH keys at all. Choose SSH only if Eric
prefers it, in which case generate a key with `ssh-keygen -t ed25519` and add it via
`gh ssh-key add`.

3. **Initialize and create.** Repo name follows the brief; `pagouro` is the working assumption.

```bash
cd "C:\Users\Eric Wade\PAGOURO_BUILD"
git init -b main
git add .
git commit -m "Pagouro scaffold: operating docs, env template, preflight"
gh repo create pagouro --private --source=. --remote=origin --push
```

**Private by default.** Make it public only on Eric's explicit say-so.

4. **Confirm `.env` is absent from the first commit** before pushing:

```bash
git status --porcelain && git ls-files | grep -i env
```

Only `.env.example` should appear.

## Standing rules

- Commit and push only when Eric asks, per the global rules.
- Never force-push a shared branch.
- If a secret ever lands in a commit, rotating the key at OpenRouter is the fix. Rewriting
  history does not un-leak it.
