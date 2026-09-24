# Handles and domains — availability as probed 2026-09-24 02:50Z (O-44)

*Read-only probes by `scripts/check_handles.py` (public lookups only; nothing registered, no
logins). Verified against controls the same minute: `google`/`allenai` returned TAKEN on every
probe that says FREE below. Availability changes by the hour; re-run before registering.*

| Platform | `pagouro` | `pagouro_ai` | `pagouroai` | `pagouro-ai` |
|---|---|---|---|---|
| GitHub | FREE | FREE | FREE | FREE |
| Hugging Face (user + org namespace) | FREE | FREE | FREE | FREE |
| Bluesky (`.bsky.social`) | FREE | FREE | FREE | FREE |
| Mastodon (`mastodon.social`) | FREE | FREE | FREE | FREE |
| YouTube `@handle` | FREE | FREE | FREE | FREE |
| PyPI | FREE | FREE | FREE | FREE |
| npm | FREE | FREE | FREE | FREE |
| X / Twitter | **FREE** (Eric, by hand, 2026-09-24) | | | |
| Instagram | **FREE** (Eric, by hand, 2026-09-24) | | | |
| TikTok | **FREE** (Eric, by hand, 2026-09-24) | | | |
| Reddit | **FREE** (Eric, by hand, 2026-09-24) | | | |
| LinkedIn, Threads | login-walled to probes — check by hand (URLs below) | | | |

| Domain | |
|---|---|
| pagouro.com | **ERIC'S** — bought before the build, WHOIS privacy + DNSSEC on (ORIGIN_LEDGER F14). The first draft of this table said "taken by someone else" from the RDAP hit alone; Eric corrected it. |
| pagouro.org | FREE |
| pagouro.ai | FREE |
| pagouro.net | FREE |
| pagouroai.com / .org | FREE (`.ai`/`.net` rate-limited on the second pass; re-run) |

## Reading it

- **The bare word `pagouro` is free on every platform checked** — eight by probe, four by Eric's
  hand (X, Instagram, TikTok, Reddit). That is the handle; `pagouro_ai` is not needed.
- The `.com` is already Eric's (F14: it redirects to the release). `.org` and `.ai` are free and
  cheap defensive registrations so nobody else can trade on the name; not required.
- **X: `x.com/pagouro` is available** (Eric checked by hand, 2026-09-24).
- The GitHub account `ericrwade` already exists (D-52 resolved); a `pagouro` org on GitHub and a
  `pagouro` org on Hugging Face would hold the repository and the model card under the project's
  own name at F13 — both free today.
- One rule for all of them: whatever handle is chosen, register the same string on every
  platform in one sitting, even the ones that will never be used, so the name cannot be
  impersonated. Findability is the point ("everything should have some presence").

## Checking the login-walled ones without an account

Open the URL in any browser; no login is needed to see whether a name exists:

- Instagram: `https://www.instagram.com/pagouro/` — free if it says "Sorry, this page isn't available."
- TikTok: `https://www.tiktok.com/@pagouro` — free if it says "Couldn't find this account."
- Reddit user: `https://www.reddit.com/user/pagouro` — free if "Sorry, nobody on Reddit goes by that name."
- Reddit community: `https://www.reddit.com/r/pagouro` — free if "there aren't any communities on Reddit with that name."
- Threads: `https://www.threads.net/@pagouro`; LinkedIn: `https://www.linkedin.com/company/pagouro`.

(Probes cannot do this: these sites return the same page for every name and fill it in
afterwards with script.)

## Not done, on purpose

No account was created and no domain registered. Those are outward-facing and Eric's (D-54
spirit: nothing public without his hand on it). The script exists so the check can be repeated
the day he registers.
