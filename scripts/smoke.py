#!/usr/bin/env python
"""Pagouro OpenRouter smoke test.

One chat completion, reporting tokens and cost. Never prints the API key.

  python scripts/smoke.py                                  # default free model
  python scripts/smoke.py --model anthropic/claude-sonnet-5 --prompt "hi"
  python scripts/smoke.py --list-free                      # show free slugs
"""
import argparse, io, json, os, sys, urllib.request, urllib.error

BASE = "https://openrouter.ai/api/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    """Read .env without exporting secrets anywhere visible."""
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in io.open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        sys.exit("OPENROUTER_API_KEY not set. See docs/SETUP_OPENROUTER.md")
    return key


def call(url, key, payload=None):
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    title = os.environ.get("OPENROUTER_APP_TITLE")
    if title:
        req.add_header("X-OpenRouter-Title", title)
    ref = os.environ.get("OPENROUTER_APP_URL")
    if ref:
        req.add_header("HTTP-Referer", ref)
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:600]
        sys.exit("HTTP %s from OpenRouter:\n%s" % (e.code, body))
    except urllib.error.URLError as e:
        sys.exit("network error: %s" % e.reason)


def main():
    ap = argparse.ArgumentParser()
    # NOTE: --model has NO argparse default. The default lives in .env as
    # OPENROUTER_DEFAULT_MODEL and can only be read AFTER load_env() runs, so it is
    # resolved below. Setting it here would capture the value before .env is loaded.
    ap.add_argument("--model", default=None)
    ap.add_argument("--prompt", default="Reply with exactly: pong")
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--list-free", action="store_true")
    a = ap.parse_args()

    key = load_env()

    if not a.model:
        a.model = (os.environ.get("OPENROUTER_DEFAULT_MODEL") or "").strip()
    if not a.model:
        sys.exit("No model given and OPENROUTER_DEFAULT_MODEL is unset in .env. "
                 "Pass --model, or set the default. See docs/DECISIONS.md D-4.")

    if a.list_free:
        models = call(BASE + "/models", key).get("data", [])
        free = sorted(m["id"] for m in models if m.get("id", "").endswith(":free"))
        print("%d free slugs of %d total:" % (len(free), len(models)))
        for m in free:
            print("  " + m)
        return

    print("model  : %s" % a.model)
    print("prompt : %s" % a.prompt)
    resp = call(BASE + "/chat/completions", key, {
        "model": a.model,
        "messages": [{"role": "user", "content": a.prompt}],
        "max_tokens": a.max_tokens,
    })

    if "error" in resp:
        sys.exit("API error: %s" % resp["error"])

    choices = resp.get("choices") or []
    text = choices[0].get("message", {}).get("content", "") if choices else "<no choices>"
    print("reply  : %s" % (text or "<empty>").strip())

    u = resp.get("usage") or {}
    print("tokens : prompt %s, completion %s, total %s"
          % (u.get("prompt_tokens", "?"), u.get("completion_tokens", "?"), u.get("total_tokens", "?")))
    cost = u.get("cost")
    if cost is not None:
        print("cost   : $%.6f" % cost)
    served = resp.get("provider")
    if served:
        print("served : %s" % served)


if __name__ == "__main__":
    main()
