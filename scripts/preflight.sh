#!/usr/bin/env bash
# Pagouro preflight. Run at the start of every session.
# Reports readiness of git, GitHub CLI, OpenRouter, and runtimes.
# NEVER prints the API key.

cd "$(dirname "$0")/.." || exit 1

ok(){   printf '  [ OK ]  %s\n' "$1"; }
warn(){ printf '  [WARN]  %s\n' "$1"; }
bad(){  printf '  [FAIL]  %s\n' "$1"; }

echo "=============================================="
echo " PAGOURO PREFLIGHT   $(date '+%Y-%m-%d %H:%M')"
echo "=============================================="

echo
echo "-- git --"
if command -v git >/dev/null 2>&1; then
  ok "git $(git --version | awk '{print $3}')"
  GN=$(git config --global user.name  || true)
  GE=$(git config --global user.email || true)
  [ -n "$GN" ] && ok "user.name  = $GN"  || bad "user.name not set  -> git config --global user.name \"Eric Wade\""
  [ -n "$GE" ] && ok "user.email = $GE"  || bad "user.email not set -> use the GitHub noreply address"
else
  bad "git not found"
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ok "repo present, HEAD $(git rev-parse --short HEAD 2>/dev/null || echo '(no commits)')"
  if [ -n "$(git status --porcelain)" ]; then
    warn "working tree dirty:"; git status --porcelain | sed 's/^/          /'
  else
    ok "working tree clean"
  fi
  if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    bad ".env IS TRACKED BY GIT -- rotate the key and untrack it now"
  fi
else
  warn "not a git repo yet -- see docs/SETUP_GITHUB.md"
fi

echo
echo "-- GitHub CLI --"
# A freshly installed gh is not on the PATH of an already-open shell, so fall back
# to the standard Windows install location before declaring it missing.
GH=""
if command -v gh >/dev/null 2>&1; then
  GH="gh"
elif [ -x "/c/Program Files/GitHub CLI/gh.exe" ]; then
  GH="/c/Program Files/GitHub CLI/gh.exe"
  warn "gh found at its install path but NOT on this shell's PATH (restart the terminal)"
fi

if [ -n "$GH" ]; then
  ok "gh $("$GH" --version 2>/dev/null | head -1 | awk '{print $3}')"
  if "$GH" auth status >/dev/null 2>&1; then
    ok "authenticated as $("$GH" api user --jq .login 2>/dev/null || echo '?')"
  else
    warn "gh not authenticated -> run:  ! gh auth login --hostname github.com --git-protocol https --web"
  fi
else
  warn "gh not installed -> winget install --id GitHub.cli -e"
fi

echo
echo "-- OpenRouter --"
if [ -f .env ]; then
  ok ".env present"
  # shellcheck disable=SC1091
  set -a; . ./.env 2>/dev/null; set +a
else
  warn ".env missing -> cp .env.example .env  and add the key"
fi

KEY="${OPENROUTER_API_KEY:-}"
if [ -z "$KEY" ]; then
  bad "OPENROUTER_API_KEY not set -- see docs/SETUP_OPENROUTER.md"
else
  ok "key present (${#KEY} chars, not shown)"
  RESP=$(curl -s -m 20 -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/key 2>/dev/null)
  if [ -z "$RESP" ]; then
    bad "no response from OpenRouter -- network?"
  else
    echo "$RESP" | python -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print("  [FAIL]  unparseable response from OpenRouter"); sys.exit()
if "error" in d:
    err = d["error"]
    msg = err.get("message", err) if isinstance(err, dict) else err
    print("  [FAIL]  key rejected:", msg); sys.exit()
d = d.get("data", d)
lim  = d.get("limit")
rem  = d.get("limit_remaining")
use  = d.get("usage")
free = d.get("is_free_tier")
print("  [ OK ]  key is live")
lim_s = "uncapped" if lim is None else "$%.2f" % lim
print("          limit          : " + lim_s)
if rem is not None:  print("          remaining      : $%.2f" % rem)
if use is not None:  print("          usage to date  : $%.4f" % use)
print("          free tier      : %s" % free)
for k, lab in (("usage_daily","today"),("usage_weekly","this week"),("usage_monthly","this month")):
    v = d.get(k)
    if v is not None: print("          spend %-10s: $%.4f" % (lab, v))
if lim is None:
    print("  [WARN]  this key has NO credit cap. Set one at https://openrouter.ai/keys")
'
  fi
fi

echo
echo "-- runtimes --"
command -v python >/dev/null 2>&1 && ok "python $(python --version 2>&1 | awk '{print $2}')" || warn "python not found"
command -v node   >/dev/null 2>&1 && ok "node $(node --version)"                            || warn "node not found"

echo
echo "-- project docs --"
for f in PAGOURO_BRIEF.md START_HERE.md CLAUDE.md docs/DECISIONS.md docs/SESSION_LOG.md; do
  [ -f "$f" ] && ok "$f" || warn "$f missing"
done

echo
echo "=============================================="
echo " Next: read START_HERE.md, then PAGOURO_BRIEF.md"
echo "=============================================="
