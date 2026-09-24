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
| Reddit | login-walled to probes — check by hand | | | |
| X / Twitter, Instagram, TikTok, LinkedIn, Threads | login-walled to probes — check by hand | | | |

| Domain | |
|---|---|
| pagouro.com | **TAKEN** (registered by someone else; RDAP 200) |
| pagouro.org | FREE |
| pagouro.ai | FREE |
| pagouro.net | FREE |
| pagouroai.com / .org | FREE (`.ai`/`.net` rate-limited on the second pass; re-run) |

## Reading it

- The bare word **`pagouro`** is free everywhere that answers — the plainest handle wins if X and
  Instagram also have it. Check those two by hand first; if either is gone, `pagouro_ai` is free
  on every probed platform and reads as one name across all of them.
- The `.com` is taken. **`pagouro.org`** fits a non-commercial, frozen artefact better than `.ai`
  and costs a tenth as much; `.ai` is the obvious second registration so nobody else takes it.
- The GitHub account `ericrwade` already exists (D-52 resolved); a `pagouro` org on GitHub and a
  `pagouro` org on Hugging Face would hold the repository and the model card under the project's
  own name at F13 — both free today.
- One rule for all of them: whatever handle is chosen, register the same string on every
  platform in one sitting, even the ones that will never be used, so the name cannot be
  impersonated. Findability is the point ("everything should have some presence").

## Not done, on purpose

No account was created and no domain registered. Those are outward-facing and Eric's (D-54
spirit: nothing public without his hand on it). The script exists so the check can be repeated
the day he registers.
