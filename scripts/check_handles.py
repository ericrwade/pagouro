"""Read-only handle availability probe (O-44): does a name look free on each platform that
answers a public request? It creates nothing and logs in nowhere. Platforms that hide profile
pages behind a login or block automated fetches (X, Instagram, TikTok, LinkedIn) are reported
as CHECK BY HAND rather than guessed.

    python scripts/check_handles.py pagouro pagouro_ai pagouroai pagouro-ai

Verdicts: FREE (a profile lookup returned not-found), TAKEN (a profile exists), ? (unclear
response), CHECK BY HAND (the platform does not answer probes). Domains use RDAP, the
registries' own lookup protocol: a 404 there means unregistered.
"""
from __future__ import annotations

import json
import socket
import sys
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (handle-availability check; one request per name)"}


def get(url: str, timeout: int = 15):
    """Return (status, body_head) without raising; None status on network failure."""
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(4000)
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError):
        return None, b""


def by_status(url, free_codes=(404,), taken_codes=(200,)):
    st, _ = get(url)
    if st is None:
        return "?"
    if st in free_codes:
        return "FREE"
    if st in taken_codes:
        return "TAKEN"
    return f"? ({st})"


def github(name):
    return by_status(f"https://api.github.com/users/{name}")


def huggingface(name):
    st, _ = get(f"https://huggingface.co/api/users/{name}/overview")
    if st == 200:
        return "TAKEN"
    if st == 404:
        # orgs live in the same namespace
        st2, _ = get(f"https://huggingface.co/api/organizations/{name}/overview")
        return "TAKEN (org)" if st2 == 200 else ("FREE" if st2 == 404 else f"? ({st2})")
    return "?" if st is None else f"? ({st})"


def bluesky(name):
    st, body = get(f"https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle?handle={name}.bsky.social")
    if st == 200:
        return "TAKEN"
    if st == 400 or st == 404:
        return "FREE"
    return "?" if st is None else f"? ({st})"


def reddit(name):
    st, body = get(f"https://www.reddit.com/user/{name}/about.json")
    if st == 404:
        return "FREE"
    if st == 200:
        return "TAKEN"
    return "CHECK BY HAND" if st in (403, 429) else ("?" if st is None else f"? ({st})")


def youtube(name):
    return by_status(f"https://www.youtube.com/@{name}")


def pypi(name):
    return by_status(f"https://pypi.org/pypi/{name}/json")


def npm(name):
    return by_status(f"https://registry.npmjs.org/{name}")


def mastodon_social(name):
    return by_status(f"https://mastodon.social/api/v1/accounts/lookup?acct={name}")


def domain(fqdn):
    st, _ = get(f"https://rdap.org/domain/{fqdn}")
    if st == 404:
        return "FREE"
    if st == 200:
        return "TAKEN"
    return "?" if st is None else f"? ({st})"


PLATFORMS = [
    ("GitHub", github),
    ("Hugging Face", huggingface),
    ("Bluesky (.bsky.social)", bluesky),
    ("Mastodon (mastodon.social)", mastodon_social),
    ("Reddit", reddit),
    ("YouTube @handle", youtube),
    ("PyPI", pypi),
    ("npm", npm),
]
BY_HAND = ["X / Twitter", "Instagram", "TikTok", "LinkedIn", "Threads"]
TLDS = ["com", "org", "ai", "net"]


def main(names):
    for name in names:
        print(f"\n== {name} ==")
        for label, fn in PLATFORMS:
            print(f"  {label:28s} {fn(name)}")
        base = name.replace("_", "").replace("-", "")
        for tld in TLDS:
            print(f"  {'domain ' + base + '.' + tld:28s} {domain(base + '.' + tld)}")
        print(f"  {'; '.join(BY_HAND):28s} CHECK BY HAND (login-walled)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["pagouro", "pagouro_ai", "pagouroai"]))
