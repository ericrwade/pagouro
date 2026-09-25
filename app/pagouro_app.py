"""Pagouro -- the harness that lives on the stick.

This process IS the product's application layer (D-51, D-52): it starts llama-server
next to it, owns the conversation, the context gauge, the three toggles, the tools
and the sandbox, and talks to the model over HTTP. llama-cli is no longer the app.

Design rules it enforces (see docs/DECISIONS.md):
  D-19  SAND / STONE   -- nothing is written to disk unless the user flips STONE.
  D-49  context gauge  -- the window's fill is always visible; dropped turns are
                          shown leaving, with their first words, never silently.
  D-50  harness notices -- facts about the system's state (offline, date, no pack
                          coverage) are fixed harness text, not model output.
  D-51  agent + tools  -- one tool per turn, grammar-constrained so every call is
                          valid, results printed, READ-ONLY by default, an explicit
                          allowlist, never a shell, file writes confined to workspace/.
  D-52  MVP framework  -- everything here is meant to be read and extended.

Standard library only, so PyInstaller produces one small executable and the host
machine needs nothing installed.
"""

from __future__ import annotations

import ast
import ctypes
import datetime as dt
import json
import operator
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_ONLINE, ROUTER_PROMPT, ROUTER_PROMPT_ONLINE  # noqa: E402  (shared with the SFT builder)
from packsearch import Packs, words as _pwords  # noqa: E402
import artkit  # noqa: E402  (O-21: terminal pixel-art renderer + PNG; the drawing model is not on this stick yet)
import skills as _skills  # noqa: E402  (O-30: skill folders under skills/ add tools and packs)
import palettes as _palettes  # noqa: E402  (D-74: HOUSE palette, Belle Époque; the crab is drawn in it)
import mark as _mark  # noqa: E402  (the poster-medallion mark, procedural, in HOUSE)
import house_style as _house  # noqa: E402  (D-78: BC/AD on output; the rest is in STYLE_GUIDE.md)
import documents as _docs  # noqa: E402  (D-79: PDF / Word / text documents, extracted by the harness and indexed beside the packs)

APP_VERSION = "0.1.0 (MVP framework)"
MAX_TOKENS_ANSWER = 200          # generation budget per answer (capped to a quarter of the window at runtime)
MAX_TOKENS_ROUTER = 96           # the tool decision is a tiny JSON object
GAUGE_BOXES = 10
TOOL_STEPS_PER_TURN = 1          # D-51: one tool per turn in the MVP

# --------------------------------------------------------------------------
# Paths. When frozen by PyInstaller, everything lives next to the executable.
# --------------------------------------------------------------------------
def base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE = base_dir()
MODEL_DIR = os.path.join(BASE, "model")
PACKS_DIR = os.path.join(BASE, "packs")
WORKSPACE = os.path.join(BASE, "workspace")
SKILLS_DIR = os.path.join(BASE, "skills")
SERVER_EXE = os.path.join(BASE, "llama-server.exe")

# Development fallback: run from the repo against tools/ and data/.
if not os.path.exists(SERVER_EXE):
    SERVER_EXE = os.path.join(BASE, "tools", "llamacpp", "llama-server.exe")
if not os.path.isdir(MODEL_DIR):
    MODEL_DIR = os.path.join(BASE, "data", "gguf_real")


def pick_model() -> str:
    prefs = ["pagouro-q8_0.gguf", "pagouro-real-q8_0.gguf", "pagouro-q4_k_m.gguf", "pagouro-real-q4_k_m.gguf"]
    for p in prefs:
        f = os.path.join(MODEL_DIR, p)
        if os.path.exists(f):
            return f
    for f in sorted(os.listdir(MODEL_DIR)) if os.path.isdir(MODEL_DIR) else []:
        if f.endswith(".gguf"):
            return os.path.join(MODEL_DIR, f)
    fatal(f"no .gguf model found in {MODEL_DIR}",
          "Put the model file back (the release folder has one; a replacement goes in the same place, "
          "docs/MAKE_IT_YOURS.md rung 2), then start again.")


def owns_console() -> bool:
    """True when this process is the only one attached to its console window -- i.e. it was
    double-clicked from Explorer and the window will vanish the moment we exit."""
    if os.name != "nt":
        return False
    try:
        buf = (ctypes.c_uint * 4)()
        return ctypes.windll.kernel32.GetConsoleProcessList(buf, 4) <= 1
    except Exception:  # noqa: BLE001
        return False


def fatal(what: str, do: str, detail: str = "") -> None:
    """Every-state rule (O-39): a failure is visible and says what to do. Waits for a keypress when
    closing the window would take the message with it."""
    print(c(RED, f"\n  Pagouro cannot start: {what}"))
    print("  " + do)
    if detail:
        print(c(DIM, "  " + detail.replace("\n", "\n  ")))
    if owns_console():
        try:
            input("\n  Press Enter to close this window. ")
        except Exception:  # noqa: BLE001
            pass
    raise SystemExit(1)


# --------------------------------------------------------------------------
# Console colour. Windows 10+ supports VT sequences once enabled.
# --------------------------------------------------------------------------
def enable_vt() -> bool:
    if os.name != "nt":
        return True
    try:
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not k.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        return bool(k.SetConsoleMode(h, mode.value | 0x0004))
    except Exception:
        return False

COLOR = enable_vt()


def enable_utf8() -> bool:
    """Windows consoles default to a legacy code page; the gauge glyphs need UTF-8."""
    try:
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        "■□◀⚙→…".encode(sys.stdout.encoding or "ascii")
        return True
    except Exception:
        return False

UTF8 = enable_utf8()
BOX_FULL, BOX_EMPTY, ARROW_OUT, GEAR, ARROW, ELLIPSIS = (
    ("■", "□", "◀", "⚙", "→", "…") if UTF8 else ("#", "-", "<", "*", "->", "..."))

def c(code: str, s: str) -> str:
    return f"\x1b[{code}m{s}\x1b[0m" if COLOR else s

GREEN, YELLOW, RED, DIM, BOLD, CYAN, MAG = "32", "33", "31", "2", "1", "36", "35"


# --------------------------------------------------------------------------
# llama-server lifecycle
# --------------------------------------------------------------------------
def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Server:
    def __init__(self, model: str):
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        threads = max(2, min(8, (os.cpu_count() or 4) // 2))
        # -c 8192: the 1B was trained at 8k (D-81); without it llama-server defaults to 4096. The KV cache
        # for 8k on this model is ~170 MB, fine on CPU. -ngl 0 always: this desk's AMD Vulkan backend
        # emits garbage for the 1B (D-88), and the product promise is "runs on any CPU".
        cmd = [SERVER_EXE, "-m", model, "--port", str(self.port), "--host", "127.0.0.1", "-c", "8192",
               "-ngl", "0", "-t", str(threads), "--log-disable", "--no-webui"]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        if not os.path.exists(SERVER_EXE):
            fatal("the model server program is missing", f"Expected {SERVER_EXE}. Copy the release folder whole; "
                  "if an antivirus quarantined it, restore it (it is llama.cpp, MIT-licensed, hash in MANIFEST.md).")
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                     creationflags=flags)
        self._stderr_tail: list[str] = []
        import threading
        def _drain():                       # keep the last lines only; never block the server on a full pipe
            for raw in iter(self.proc.stderr.readline, b""):
                self._stderr_tail.append(raw.decode("utf-8", "replace").rstrip())
                del self._stderr_tail[:-40]
        threading.Thread(target=_drain, daemon=True).start()
        for _ in range(120):
            try:
                if self.get("/health").get("status") == "ok":
                    break
            except Exception:
                pass
            if self.proc.poll() is not None:
                fatal("the model server stopped while starting",
                      "Usually the model file is damaged or the machine is short of memory. Check the file's hash "
                      "against MANIFEST.md (python verify_manifest.py) and close other programs; then start again.",
                      "\n".join(self._stderr_tail[-8:]))
            time.sleep(0.25)
        else:
            fatal("the model server did not answer within 30 seconds",
                  "A slow disk or a very large model can take longer: start again once; if it repeats, check "
                  "the model file's hash against MANIFEST.md.", "\n".join(self._stderr_tail[-8:]))
        props = self.get("/props")
        self.n_ctx = int(props.get("default_generation_settings", {}).get("n_ctx", 512))

    def get(self, path: str):
        with urllib.request.urlopen(self.url + path, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))

    def post(self, path: str, body: dict, timeout: int = 120):
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.url + path, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def count_tokens(self, text: str) -> int:
        return len(self.post("/tokenize", {"content": text, "add_special": False}).get("tokens", []))

    def chat(self, messages: list[dict], max_tokens: int, grammar: str | None = None,
             temperature: float = 0.3) -> tuple[str, dict]:
        body = {"messages": messages, "max_tokens": max_tokens, "temperature": temperature,
                "cache_prompt": True}
        if grammar is not None:
            body["grammar"] = grammar
            body["temperature"] = 0
        d = self.post("/v1/chat/completions", body)
        return d["choices"][0]["message"]["content"], d.get("usage", {})

    def stop(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


# --------------------------------------------------------------------------
# Tools. An explicit allowlist. Never a shell. (D-51)
# --------------------------------------------------------------------------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}

def tool_calc(expr: str, app) -> str:
    """Arithmetic only: numbers, + - * / // % ** and parentheses."""
    expr = expr.strip().replace("^", "**").replace("x", "*").replace("×", "*").replace("÷", "/")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return f"could not parse '{expr}' as arithmetic"

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 64:
                raise ValueError("exponent too large")
            return _OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("only arithmetic is allowed")
    try:
        v = ev(tree)
    except ZeroDivisionError:
        return "division by zero"
    except Exception as e:
        return f"refused: {e}"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return f"{expr} = {v}"


def tool_time(_arg: str, app) -> str:
    now = dt.datetime.now()
    return now.strftime("local date and time: %A %Y-%m-%d %H:%M (%Z)").strip()


FORAGING = re.compile(r"\b(mushroom|fung(us|i)|toadstool|edible|forag\w*|wild (plant|berr)|berries|poisonous plant|safe to eat)\b", re.I)
FORAGING_NOTICE = ("HARNESS NOTICE: plant and mushroom identification is deliberately not in these packs and is "
                   "not something to trust a language model with. Consult a physical field guide.")


def tool_pack_search(query: str, app) -> str:
    """The origin conversation (line 92) hard-walls foraging and mushroom identification
    behind 'consult a physical field guide'. The survival pack omits those chapters, and
    this notice is fixed harness text (D-50) on any foraging-shaped query, whatever the
    packs return."""
    hits = app.packs.search(query)
    if not hits:
        return "NO_MATCH: nothing in the loaded packs covers this." + (" " + FORAGING_NOTICE if FORAGING.search(query) else "")
    # O-23: if the owner's own words match, they come first and alone (at most two passages). A
    # small model given three mixed hits binds the answer to the wrong one (D-61 memory eval:
    # right shape, wrong hit); the owner's note is also the higher-priority source by design.
    mem = [h for h in hits if h[0].startswith("memory:")]
    if mem:
        hits = mem[:2]
    out = []
    for name, text, _ in hits:
        label = (f"YOUR OWN WORDS, from {name[len('memory:'):]}" if name.startswith("memory:")
                 else f"YOUR DOCUMENT {name[len('doc:'):].removesuffix('.txt')}" if name.startswith("doc:") else name)   # D-79
        out.append(f"[{label}] {text[:700]}")
    res = "\n\n".join(out)
    if FORAGING.search(query) or FORAGING.search(res[:400]):
        res = FORAGING_NOTICE + "\n\n" + res
    return res


def _path_allowed_for_read(path: str, app) -> bool:
    p = os.path.abspath(path)
    if p.startswith(os.path.abspath(WORKSPACE)) or p.startswith(os.path.abspath(PACKS_DIR)):
        return True
    # A path the user typed themselves in this turn is fair to read (D-51).
    return path in app.last_user_text


def tool_read_file(path: str, app) -> str:
    path = path.strip().strip('"').strip("'")
    if not _path_allowed_for_read(path, app):
        return f"REFUSED: {path} is outside the workspace and you did not name it in this message."
    if not os.path.exists(path):
        return f"could not read: no such file {path}"
    text, note = _docs.extract_text(path, max_chars=200_000)
    if not text:
        return f"NO_MATCH: {os.path.basename(path)} — {note}"
    head = text[:4000]
    return f"[{os.path.basename(path)}: {note}; first {len(head)} chars]\n{head}"


def tool_write_note(text: str, app) -> str:
    if not app.can_act:
        return "REFUSED: READ-ONLY mode. Type /act to allow writing to the workspace."
    os.makedirs(os.path.join(WORKSPACE, "notes"), exist_ok=True)
    fn = os.path.join(WORKSPACE, "notes", dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    app.written.append(os.path.relpath(fn, BASE))
    return f"wrote {os.path.relpath(fn, BASE)}"


# ---- ONLINE mode (origin line 88; ledger D2/D8). Search and fetch only; the
# conversation never leaves the machine, only a harness-generated query does.
# Bring-your-own: workspace/online.json holds either {"searxng": "https://host"}
# (self-hosted, no key) or {"brave_key": "..."} (Brave Search API). Nothing in this
# file touches the network unless app.online is True AND a provider is configured,
# so the OFFLINE default is audit-clean by construction.
ONLINE_CONFIG = os.path.join(WORKSPACE, "online.json")


def load_online_config() -> dict:
    try:
        with open(ONLINE_CONFIG, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def tool_web_search(query: str, app) -> str:
    if not app.online:
        return "REFUSED: OFFLINE mode. Type /online to allow search (needs workspace/online.json)."
    cfg = load_online_config()
    q = urllib.parse.quote_plus(query.strip()[:200])
    try:
        if cfg.get("searxng"):
            url = cfg["searxng"].rstrip("/") + f"/search?q={q}&format=json&language=en"
            req = urllib.request.Request(url, headers={"User-Agent": "Pagouro/0.1"})
            d = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
            hits = [(r.get("title", ""), r.get("url", ""), r.get("content", "")) for r in d.get("results", [])[:3]]
        elif cfg.get("brave_key"):
            url = f"https://api.search.brave.com/res/v1/web/search?q={q}&count=3"
            req = urllib.request.Request(url, headers={"Accept": "application/json", "X-Subscription-Token": cfg["brave_key"]})
            d = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
            hits = [(r.get("title", ""), r.get("url", ""), r.get("description", "")) for r in d.get("web", {}).get("results", [])[:3]]
        else:
            return "REFUSED: no search provider configured (workspace/online.json: {\"searxng\": url} or {\"brave_key\": key})."
    except Exception as e:
        return f"search failed: {type(e).__name__}: {str(e)[:120]}"
    app.searches += 1
    if not hits:
        return "NO_MATCH: the search returned nothing."
    return "\n".join(f"[{i + 1}] {t} — {u}\n    {s[:300]}" for i, (t, u, s) in enumerate(hits))


TOOLS = {
    "calc":        (tool_calc,        "arithmetic on an expression, e.g. 17*23 or (3+4)/2", False),
    "time":        (tool_time,        "the local date and time right now", False),
    "pack_search": (tool_pack_search, "search the offline reference packs for a topic", False),
    "read_file":   (tool_read_file,   "read a text file the user named, or one in the workspace", False),
    "write_note":  (tool_write_note,  "save a note to workspace/notes (needs CAN ACT)", True),
    "web_search":  (tool_web_search,  "search the web (needs ONLINE and a configured provider)", False),
}

# GBNF grammar for the tool decision. Written by hand rather than derived from a
# JSON schema because the schema-derived grammar permits arbitrary whitespace
# between tokens, and a small model will happily spend its whole budget on
# newlines. This one allows none: the object is exactly
#   {"tool":"<name>","arguments":"<string>"}
def router_grammar(tools: list[str]) -> str:
    alts = " | ".join('"%s"' % t for t in ["none"] + tools)
    return (r'''
root  ::= "{\"tool\":\"" tool "\",\"arguments\":\"" chars "\"}"
tool  ::= %s
chars ::= ([^"\\\n] | "\\" .){0,200}
'''.strip() % alts) + "\n"


OFFLINE_TOOLS = [t for t in TOOLS if t != "web_search"]
ROUTER_GRAMMAR = router_grammar(OFFLINE_TOOLS)          # the default (offline) grammar; evals use this
ROUTER_RE = re.compile(r'"tool"\s*:\s*"(\w+)"(?:\s*,\s*"arguments"\s*:\s*"((?:[^"\\]|\\.)*)")?')


# --------------------------------------------------------------------------
# The app
# --------------------------------------------------------------------------
class App:
    def __init__(self, server: Server):
        self.srv = server
        self.packs = Packs(PACKS_DIR)            # BM25 unless an index + embedder are present
        # The owner's long-term memory (O-23): notes, /remember lines and STONE transcripts from
        # earlier sessions are searchable beside the packs, labelled as the owner's own words.
        # Nothing is learned from SAND sessions -- they were never written down.
        self.memory_chunks = 0
        for sub in ("memory", "notes", "transcripts"):
            self.memory_chunks += self.packs.add_dir(os.path.join(WORKSPACE, sub), "memory")
        # D-79: documents the owner dropped into workspace/docs/ are extracted (PDF/Word/text) into a
        # text cache and indexed like packs, labelled as documents in search hits.
        self.doc_chunks = 0
        docs_dir, cache = os.path.join(WORKSPACE, "docs"), os.path.join(WORKSPACE, "docs", ".text")
        if os.path.isdir(docs_dir):
            try:
                _docs.index_into(docs_dir, cache)
            except Exception:  # noqa: BLE001
                pass
            self.doc_chunks = self.packs.add_dir(cache, "doc")
        # Skills (O-30): each folder under skills/ may add tools (screened, hash-listed) and packs.
        self.skills = _skills.load_all(SKILLS_DIR, TOOLS, self.packs)
        self.stone = False            # D-19: SAND by default
        self.can_act = False          # D-51: READ-ONLY by default
        self.online = False           # D-1: OFFLINE by default; /online needs workspace/online.json
        self.careful = False          # O-45 #2 (D-89): /careful samples five answers and only stands behind agreement
        self.searches = 0
        self.history: list[dict] = [] # user/assistant/tool turns, oldest first
        self.last_user_text = ""
        self.transcript_path = None
        self.dropped_total = 0
        self.written: list[str] = []   # every path a tool or STONE wrote, for an honest exit line

    # ---- system prompt: the harness tells the model what it cannot know (D-50)
    def system_prompt(self) -> str:
        return (SYSTEM_PROMPT_ONLINE if self.online else SYSTEM_PROMPT).format(date=dt.date.today().isoformat())

    def router_prompt(self) -> str:
        """The frozen router prompt the model was trained on — and nothing else. Measured 2026-09-21
        (D-79): adding one clause per skill tool cost 5 of 40 on the frozen tool-use suite (31 -> 26)
        and pushed ordinary questions to `calc`. Skill tools are reached by their TRIGGER until a
        model has been fine-tuned on the skills' examples; then the model may be told their names
        (set PAGOURO_ROUTER_EXTENDED=1 to try it on such a model)."""
        base = ROUTER_PROMPT_ONLINE if self.online else ROUTER_PROMPT
        if not os.environ.get("PAGOURO_ROUTER_EXTENDED"):
            return base
        extra = [(n, d) for n, (_, d, _) in TOOLS.items() if d.startswith("[") and n in self.available_tools()]
        if not extra:
            return base
        names = "/".join(n for n, _ in extra)
        clauses = "; ".join(f"{n} for {d.split('] ', 1)[-1]}" for n, d in extra)
        return base.replace('"arguments": string}', f'"arguments": string}} (also: {names})') + f" Use {clauses}."

    def available_tools(self) -> list[str]:
        """Tools the model may choose (the router grammar): the app's own set, plus skill tools only
        when the router prompt names them. Skill tools stay callable through their triggers."""
        own = [t for t in TOOLS if not TOOLS[t][1].startswith("[")]
        base = own if not self.online else own + ([] if "web_search" in own else ["web_search"])
        base = [t for t in base if self.online or t != "web_search"]
        if os.environ.get("PAGOURO_ROUTER_EXTENDED"):
            base += [t for t in TOOLS if TOOLS[t][1].startswith("[")]
        return base

    def skill_tools(self) -> list[str]:
        return [t for t in TOOLS if TOOLS[t][1].startswith("[")]

    def messages(self) -> list[dict]:
        return [{"role": "system", "content": self.system_prompt()}] + self.history

    # ---- gauge (D-49)
    def render_for_count(self, msgs: list[dict]) -> str:
        return "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in msgs) + "<|im_start|>assistant\n"

    def used_tokens(self) -> tuple[int, int, int]:
        sys_t = self.srv.count_tokens(self.render_for_count([{"role": "system", "content": self.system_prompt()}]))
        chat_t = self.srv.count_tokens(self.render_for_count(self.history)) if self.history else 0
        return sys_t + chat_t, sys_t, chat_t

    def gauge(self, used: int) -> str:
        n = self.srv.n_ctx
        frac = min(1.0, used / n)
        filled = int(round(frac * GAUGE_BOXES))
        col = GREEN if frac < 0.6 else YELLOW if frac < 0.85 else RED
        boxes = c(col, BOX_FULL * filled) + c(DIM, BOX_EMPTY * (GAUGE_BOXES - filled))
        return f"{boxes} {used}/{n} tokens"

    def status_line(self) -> str:
        used, sys_t, chat_t = self.used_tokens()
        mode = c(GREEN, "OFFLINE") if not self.online else c(YELLOW, "ONLINE")
        persist = c(YELLOW, "STONE") if self.stone else c(GREEN, "SAND")
        act = c(RED, "CAN ACT") if self.can_act else c(GREEN, "READ-ONLY")
        return f"[{mode}] [{persist}] [{act}]  {self.gauge(used)}  " + c(DIM, f"(system {sys_t} · chat {chat_t})")

    # ---- context management: drop oldest, visibly (D-49)
    def _current_turn_start(self) -> int:
        """Index of the last user message. Everything from there on is the CURRENT
        turn (the question and any tool result) and is never dropped."""
        for i in range(len(self.history) - 1, -1, -1):
            if self.history[i]["role"] == "user":
                return i
        return len(self.history)

    def make_room(self, reserve: int):
        """Drop the oldest exchanges until the answer fits. 2026-09-18, Eric's first run:
        a pack search returned ~600 tokens into a 512-token window and this loop
        dropped everything, INCLUDING the question just asked and its search result,
        then the model answered from an empty context. Now the current turn is
        protected, and if it alone does not fit, the tool result is trimmed to the
        room that is left (see fit_current_turn)."""
        while self._current_turn_start() > 0:
            used, _, _ = self.used_tokens()
            if used + reserve <= self.srv.n_ctx:
                return
            drop = [self.history.pop(0)]
            while self.history and self.history[0]["role"] != "user":
                drop.append(self.history.pop(0))
            self.dropped_total += len(drop)
            head = next((m for m in drop if m["role"] == "user"), drop[0])
            first = " ".join(head["content"].split()[:6])
            where = "still in the saved transcript" if self.stone else "gone (SAND mode)"
            print(c(MAG, f"  {ARROW_OUT} {BOX_FULL} dropped oldest turn: \"{first}{ELLIPSIS}\" -- {where}"))
        self.fit_current_turn(reserve)

    def fit_current_turn(self, reserve: int):
        """With only the current turn left, trim the tool result (never the question)
        until question + result + answer fit the window. Says so when it does."""
        trimmed = False
        for _ in range(12):
            used, _, _ = self.used_tokens()
            if used + reserve <= self.srv.n_ctx:
                break
            tool_idx = next((i for i in range(len(self.history) - 1, -1, -1)
                             if self.history[i]["role"] == "tool"), None)
            if tool_idx is None:
                break                       # nothing trimmable; the server will truncate
            over = used + reserve - self.srv.n_ctx
            content = self.history[tool_idx]["content"]
            # ~4 chars per token; cut a little more than the overflow, keep at least a line
            cut = max(80, len(content) - int(over * 4.5) - 40)
            if cut >= len(content):
                cut = max(80, len(content) - 40)
            if cut >= len(content):
                break
            self.history[tool_idx]["content"] = content[:cut].rstrip() + " [trimmed]"
            trimmed = True
        if trimmed:
            print(c(DIM, "  note: the tool result was trimmed to fit the model's window."))

    # ---- persistence (D-19)
    def record(self, role: str, text: str):
        if not self.stone:
            return
        try:
            if self.transcript_path is None:
                os.makedirs(os.path.join(WORKSPACE, "transcripts"), exist_ok=True)
                self.transcript_path = os.path.join(WORKSPACE, "transcripts",
                                                    dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
            with open(self.transcript_path, "a", encoding="utf-8") as f:
                f.write(f"{role}: {text}\n")
        except OSError as e:                # a write-protected stick, a full disk, a read-only folder
            self.stone = False
            self.transcript_path = None
            print(c(YELLOW, f"  STONE could not write to workspace/transcripts/ ({e.strerror or e}). "
                            "Back to SAND: nothing is being saved. Unlock the drive or free space, then /stone again."))
            return
        rel = os.path.relpath(self.transcript_path, BASE)
        if rel not in self.written:
            self.written.append(rel)

    # ---- the tool loop (D-51)
    def route(self, user_text: str) -> tuple[str, str]:
        """Ask the model, under a grammar, whether a tool is needed. Returns (tool, arguments).
        The grammar guarantees a valid object; the model supplies the judgement."""
        for name, pat in _skills.TRIGGERS.items():      # O-30: a skill's own trigger outranks the model
            if name in TOOLS and pat.search(user_text):
                return name, user_text
        router_msgs = [{"role": "system", "content": self.router_prompt()},
                       {"role": "user", "content": user_text}]
        try:
            raw, _ = self.srv.chat(router_msgs, MAX_TOKENS_ROUTER, grammar=router_grammar(self.available_tools()))
        except Exception:
            return "none", ""
        if os.environ.get("PAGOURO_DEBUG"):
            print(c(DIM, f"  router: {raw!r}"))
        try:
            d = json.loads(raw)
            return str(d.get("tool", "none")), str(d.get("arguments", ""))
        except Exception:
            m = ROUTER_RE.search(raw)          # salvage a truncated object
            if m:
                return m.group(1), (m.group(2) or "")
            return "none", ""

    # ---- argument recovery: the harness compensates for the model (origin line 78)
    _WORD_OPS = [(r"\bmultiply\s+([\d\.]+)\s+by\s+([\d\.]+)", r"\1 * \2"),
                 (r"\bdivide\s+([\d\.]+)\s+by\s+([\d\.]+)", r"\1 / \2"),
                 (r"\bsubtract\s+([\d\.]+)\s+from\s+([\d\.]+)", r"\2 - \1"),
                 (r"\badd\s+([\d\.]+)\s+(?:and|to)\s+([\d\.]+)", r"\1 + \2"),
                 (r"\bplus\b", "+"), (r"\bminus\b", "-"), (r"\btimes\b", "*"), (r"\bmultiplied by\b", "*"),
                 (r"\bdivided by\b", "/"), (r"\bover\b", "/"), (r"\bsquared\b", "**2"), (r"\bcubed\b", "**3"),
                 (r"\bto the power of\b", "**"), (r"\bpercent of\b", "/100*"), (r"%\s*of\b", "/100*"),
                 (r"\bx\b", "*"), (r",", "")]

    def refine_args(self, name: str, args: str, user_text: str) -> str:
        """A small model's tool ARGUMENTS are unreliable even when its tool CHOICE is
        right (the shakedown model asked write_note to save "packs the Bitcoin wallet's
        transactions" for "save a note: bring the charger"). When the argument is
        unusable, recover it from the user's own words; when the user's words are
        clearer, prefer them. Every rule here is a plain regex, visible and editable."""
        t = user_text.strip()
        if name == "calc":
            expr = t.lower()
            for pat, rep in self._WORD_OPS:
                expr = re.sub(pat, f" {rep} ", expr)
            cands = re.findall(r"[\d\.\s\+\-\*/\(\)%]+", expr)
            cands = [x.strip() for x in cands if re.search(r"\d", x) and re.search(r"[\+\-\*/%]|\*\*", x)]
            if cands:
                return max(cands, key=len)
            return args
        if name == "write_note":
            m = re.search(r"(?:note|save|write|remember|jot)[^:]*:\s*(.+)$", t, re.I)
            if m:
                return m.group(1).strip().strip('"').strip("'").rstrip(".")
            m = re.search(r"(?:note|remember|jot down)\s+(?:that\s+)?(.+)$", t, re.I)
            return m.group(1).strip().rstrip(".") if m else args
        if name == "read_file":
            m = re.search(r"([A-Za-z]:\\[^\s\"']+|/[^\s\"']+|(?:workspace|packs)[/\\][^\s\"']+|[\w\-]+\.(?:txt|md|json|csv|log))", t)
            return m.group(1).rstrip(".,;") if m else args
        if name == "pack_search":
            if len(re.findall(r"[a-z]{3,}", args.lower())) < 2:
                return " ".join(sorted(_pwords(t))) or args
            return args
        return args

    def run_tool(self, name: str, args: str) -> str | None:
        if name not in TOOLS:
            return None
        fn, _, needs_act = TOOLS[name]
        args = self.refine_args(name, args, self.last_user_text)
        print(c(CYAN, f"  {GEAR} tool {name}({args[:80]})"))
        if needs_act and not self.can_act:
            res = "REFUSED: READ-ONLY mode. Type /act to allow tools that write."
        else:
            try:
                res = fn(args, self)
            except Exception as e:
                res = f"tool error: {e}"
        shown = res if len(res) <= 300 else res[:300] + ELLIPSIS
        print(c(DIM, "  → " + shown.replace("\n", "\n    ")))
        return res

    def turn(self, user_text: str):
        self.last_user_text = user_text
        self.record("user", user_text)
        self.history.append({"role": "user", "content": user_text})

        tool, args = self.route(user_text)
        tool_result = None
        if tool != "none":
            tool_result = self.run_tool(tool, args)
            if tool_result is not None:
                # Convention (O-38): a tool may put a line "--" in its result; what follows is for the
                # person (provenance, raw bytes, hashes) and is shown, but never fed to the model,
                # which would only be confused by it.
                for_model = tool_result.split("\n--\n", 1)[0]
                self.history.append({"role": "tool", "content": f"{tool}: {for_model[:1200]}"})

        budget = min(MAX_TOKENS_ANSWER, max(64, self.srv.n_ctx // 4))
        self.make_room(budget)
        try:
            answer, usage = self.srv.chat(self.messages(), budget)
            if self.careful:
                answer = self.careful_check(answer, budget)
        except urllib.error.HTTPError as e:
            answer = f"(the model server refused the request: {e.code}; try /clear)"
            usage = {}
        answer = _house.apply(answer.strip()) or "(no answer)"   # D-78: eras written BC / AD, a display convention
        self.history.append({"role": "assistant", "content": answer})
        self.record("assistant", answer)
        print(c(BOLD, "pagouro> ") + answer)
        if tool_result and tool_result.startswith("NO_MATCH"):
            print(c(DIM, "  note: nothing in the loaded packs covered this; the answer above is from the model alone."))

    # ---- careful mode (O-45 #2, D-89): agreement across samples as an honest confidence signal
    CAREFUL_SAMPLES = 5
    CAREFUL_AGREE = 3

    @staticmethod
    def _content_words(text: str) -> set:
        stop = {"the", "a", "an", "of", "in", "on", "at", "to", "is", "was", "are", "were", "and", "or", "it",
                "its", "this", "that", "by", "for", "with", "as", "be", "which", "from", "i", "you", "not", "no"}
        return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in stop and len(w) > 1}

    def careful_check(self, answer: str, budget: int) -> str:
        """Ask the same question CAREFUL_SAMPLES more times at sampling temperature and measure how
        many of those answers agree with the greedy one on content words (Jaccard >= 0.5). A model that
        knows something says it the same way every time; a model that is guessing says something
        different each time. Below CAREFUL_AGREE agreements the answer is presented as a guess, in so
        many words. An abstention is left alone: 'I have no record' needs no vote."""
        low = answer.lower()
        if any(m in low for m in ("no record", "don't have any record", "don't have a record", "have no record",
                                  "i don't know", "can't find", "not in my records", "can't make up", "won't make up")):
            return answer
        # Every answer repeats the question's words, so those are stripped before comparing; what is
        # left is the claim itself ("lisbon" vs "porto"). Overlap coefficient, so a short answer and a
        # long one that agree still agree.
        qwords = self._content_words(self.history[-1]["content"]) if self.history else set()
        base = self._content_words(answer) - qwords
        if not base:
            return answer
        agree = 0
        for _ in range(self.CAREFUL_SAMPLES):
            alt, _ = self.srv.chat(self.messages(), budget, temperature=0.7)
            words = self._content_words(alt) - qwords
            ov = len(base & words) / max(1, min(len(base), len(words)))
            if ov >= 0.5:
                agree += 1
        tag = f"careful: {agree} of {self.CAREFUL_SAMPLES} re-asks agreed"
        if agree >= self.CAREFUL_AGREE:
            print(c(DIM, f"  {tag}."))
            return answer
        print(c(YELLOW, f"  {tag} — treating this as a guess."))
        return ("I'm not sure about this one: when I asked myself again, my answers disagreed. "
                "Treat the following as a guess, not a fact: " + answer)

    # ---- commands
    def command(self, line: str) -> bool:
        cmd, _, rest = line.partition(" ")
        cmd = cmd.lower()
        if cmd in ("/exit", "/quit", "/q"):
            return False
        if cmd == "/help":
            print(HELP)
        elif cmd == "/stone":
            self.stone = True
            print(c(YELLOW, "  STONE: this chat will be written to workspace/transcripts/ from now on."))
        elif cmd == "/sand":
            self.stone = False
            print(c(GREEN, "  SAND: nothing further is written to disk."))
        elif cmd == "/act":
            self.can_act = True
            print(c(RED, "  CAN ACT: tools may now write inside workspace/. Nothing outside it, ever."))
        elif cmd == "/readonly":
            self.can_act = False
            print(c(GREEN, "  READ-ONLY: tools that write are refused."))
        elif cmd == "/online":
            cfg = load_online_config()
            if not (cfg.get("searxng") or cfg.get("brave_key")):
                print(c(YELLOW, "  ONLINE needs a provider in workspace/online.json: {\"searxng\": \"https://host\"} or {\"brave_key\": \"...\"}. Still OFFLINE."))
            else:
                self.online = True
                who = "your SearXNG at " + cfg["searxng"] if cfg.get("searxng") else "Brave Search (your key)"
                print(c(YELLOW, f"  ONLINE: web_search allowed via {who}. Only the search query leaves this machine; the chat does not."))
        elif cmd == "/offline":
            self.online = False
            print(c(GREEN, "  OFFLINE: no network calls."))
        elif cmd == "/careful":
            self.careful = not self.careful
            if self.careful:
                print(c(YELLOW, f"  CAREFUL: each answer is re-asked {self.CAREFUL_SAMPLES} times; below {self.CAREFUL_AGREE} agreements it is called a guess. Slower."))
            else:
                print(c(GREEN, "  careful mode off."))
        elif cmd == "/tools":
            for n, (_, desc, needs) in TOOLS.items():
                if n not in self.available_tools():
                    continue
                print(f"  {n:<12} {desc}{'  [needs CAN ACT]' if needs else ''}")
            print(f"  packs loaded: {', '.join(self.packs.names) or 'none'} ({len(self.packs.chunks)} chunks, {self.packs.mode} search)")
        elif cmd == "/clear":
            self.history.clear()
            print("  context cleared.")
        elif cmd == "/status":
            print("  " + self.status_line())
        elif cmd == "/art":
            self.art(rest.strip())
        elif cmd == "/remember":
            self.remember(rest.strip())
        elif cmd == "/index":
            target = rest.strip().strip('"')
            if not target:
                print("  /index <file or folder>: extract PDF / Word / text documents into workspace/docs/.text and search them like packs (needs CAN ACT). Files dropped into workspace/docs/ are indexed at launch.")
            elif not self.can_act:
                print(c(YELLOW, "  READ-ONLY: /act first — /index writes the extracted text into workspace/docs/.text."))
            elif not os.path.exists(target):
                print(c(YELLOW, f"  no such file or folder: {target}"))
            else:
                cache = os.path.join(WORKSPACE, "docs", ".text")
                summary, first = _docs.index_into(target, cache)
                n = self.packs.reindex_dir(cache, "doc") if hasattr(self.packs, "reindex_dir") else self.packs.add_dir(cache, "doc")
                self.doc_chunks = n
                print(c(GREEN, "  " + summary.replace("\n", "\n  ")))
                print(c(DIM, f"  {n} document chunks searchable; ask about it and pack_search will find the paragraph."))
        elif cmd in ("/about", "/why"):
            for name in ("ABOUT_THE_LOOK.md", "STYLE_GUIDE.md"):
                p = os.path.join(BASE, name)
                if os.path.exists(p):
                    print(open(p, encoding="utf-8").read() if name == "ABOUT_THE_LOOK.md" else f"  (the full rules are in {name} beside this program)")
                    break
            else:
                print("  Belle Époque, posters over cards (D-74). Want it to look like something else? Fork it. See docs/STYLE_GUIDE.md in the repository.")
        elif cmd == "/skills":
            if not self.skills:
                print("  no skills installed (drop a folder into skills/; see docs/SKILLS.md)")
            for sk in self.skills:
                print("  " + _skills.describe(sk).replace("\n", "\n  "))
        elif cmd == "/forget":
            self.forget()
        else:
            print("  unknown command; /help")
        return True

    def remember(self, text: str) -> None:
        """O-23 level 1: long-term memory by retrieval. Appends one dated line to
        workspace/memory/remembered.txt and re-indexes, so it comes back through pack_search in
        every later session, labelled as the owner's own words. User-initiated, like /stone, so
        it does not need CAN ACT; the write is listed on the exit line like any other."""
        if not text:
            n = sum(1 for nm in self.packs.names if nm.startswith("memory:"))
            print(f"  memory: {self.memory_chunks} passages from {n} file(s) in workspace/memory, notes, transcripts. "
                  "/remember <text> adds a line; /forget deletes remembered.txt.")
            return
        d = os.path.join(WORKSPACE, "memory")
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, "remembered.txt")
        with open(fn, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"{dt.date.today().isoformat()}: {text}\n\n")
        rel = os.path.relpath(fn, BASE)
        if rel not in self.written:
            self.written.append(rel)
        self.memory_chunks = self.packs.reindex_dir(d, "memory") + sum(
            self.packs.add_dir(os.path.join(WORKSPACE, sub), "memory") for sub in ("notes", "transcripts"))
        print(c(GREEN, f"  remembered (written to {rel}); it will come back through pack_search, as your words."))

    def forget(self) -> None:
        fn = os.path.join(WORKSPACE, "memory", "remembered.txt")
        if os.path.exists(fn):
            os.remove(fn)
            print(c(YELLOW, "  forgot: workspace/memory/remembered.txt deleted. Notes and transcripts are untouched; delete those files yourself."))
        else:
            print("  nothing remembered.")
        self.packs.reindex_dir(os.path.join(WORKSPACE, "memory"), "memory")

    def art(self, arg: str) -> None:
        """O-21 frame, D-74 palette: `/art [seed]` draws a program-generated hermit crab in the HOUSE
        palette (Belle Époque) in the terminal; `/art blob [seed]` the older test sprite; `/art save
        [seed]` also writes workspace/art/crab-<seed>.png (needs CAN ACT). No drawing model on this
        stick yet; this proves the display, the palette and the file path it will use."""
        parts = arg.split()
        if not parts or parts[0] == "logo":                # D-80: the mark itself, Eric's concept #5, in the house palette
            size = 64                                       # 32 px was tried: the lettering turns to mush
            p = os.path.join(BASE, "brand", f"mark_house_{size}.json")
            if not os.path.exists(p):
                p = os.path.join(os.path.dirname(BASE), "brand", f"mark_house_{size}.json")   # dev tree
            if os.path.exists(p):
                d = json.load(open(p, encoding="utf-8"))
                cols = [tuple(c) for c in d["colors"]]
                img = [[cols[i] for i in row] for row in d["pixels"]]
                print(artkit.render_ansi(img) if COLOR else artkit.render_ascii(img))
                print(c(DIM, f"  the Pagouro mark ({size} px, {d['palette']} palette). Full size: brand/pagouro_mark.png beside this program. "
                             "/art crab, /art mark, /art blob draw program-generated pictures."))
                return
            if not parts:
                parts = ["crab"]
        save = bool(parts) and parts[0] == "save"
        blob = bool(parts) and parts[0] == "blob"
        medal = bool(parts) and parts[0] == "mark"
        if parts and parts[0] == "crab":
            parts = parts[1:]
        rest = parts[1:] if (save or blob or medal) else parts
        if rest and rest[0] == "crab":
            rest = rest[1:]
        seed = int(rest[0]) if rest and rest[0].isdigit() else int(time.time()) % 100000
        pal = _palettes.CANDIDATES[_palettes.HOUSE]
        if medal:
            img = _mark.mark(seed, 64)
        elif blob:
            img = pal.quantize(artkit.test_sprite(seed, 32, transparent=(0, 0, 0)), transparent=(0, 0, 0))
        else:
            ramps = list(pal.ramps.values())
            img = pal.quantize(artkit.hermit_crab(seed, 32, shell=ramps[2 + seed % 6], body=ramps[2 + (seed + 3) % 6],
                                                  ink=pal.ink, transparent=(0, 0, 0)), transparent=(0, 0, 0))
        print(artkit.render_ansi(img, transparent=(0, 0, 0)) if COLOR else artkit.render_ascii(img))
        print(c(DIM, f"  {'test sprite' if blob else 'mark' if medal else 'hermit crab'} #{seed} in the {pal.name} palette (HOUSE, D-74): program-generated, "
                     "no drawing model on this stick yet (O-21). /art save <n> writes a PNG into workspace/art (needs CAN ACT)."))
        if save:
            if not self.can_act:
                print(c(YELLOW, "  READ-ONLY: /act first to let this write inside workspace/."))
                return
            d = os.path.join(WORKSPACE, "art")
            os.makedirs(d, exist_ok=True)
            fn = os.path.join(d, f"{'sprite' if blob else 'mark' if medal else 'crab'}-{seed}.png")
            n = artkit.write_png(fn, img)
            rel = os.path.relpath(fn, BASE)
            if rel not in self.written:
                self.written.append(rel)
            print(c(GREEN, f"  wrote {rel} ({n} bytes)"))


HELP = """  commands:
    /stone  /sand      save this chat to disk / stop saving (default: SAND, nothing saved)
    /act    /readonly  allow tools to write inside workspace/ / forbid (default: READ-ONLY)
    /tools             list tools and loaded packs
    /status            show the context gauge
    /careful           toggle: re-ask each question 5 times and call the answer a guess unless 3 agree (slower, honest)
    /art [logo|crab|mark|blob|save] [n]  the Pagouro mark (logo, default), or a program-drawn crab / medallion / old sprite in the house palette (save: PNG, needs CAN ACT)
    /remember <text>   keep a line in workspace/memory for every later session (/remember alone: status; /forget deletes it)
    /skills            list installed skills (skills/<name>/), their licences, tools, and whether they match their MANIFEST
    /about  /why       why everything looks like this (Belle Époque), and where the style guide is
    /index <path>      read a PDF / Word / text document (or a folder of them) into the search index (needs CAN ACT)
    /clear             forget the conversation
    /online /offline   allow web search (needs workspace/online.json) / forbid (default: OFFLINE)
    /exit              quit"""

BANNER = """
  PAGOURO  {ver}
  A small language model that lives on this USB stick.
  Nothing you type leaves this machine. Nothing is saved unless you say /stone.
  The bar shows how full the model's memory is; when it fills, the oldest turn
  is shown leaving. Type /help for commands.
"""


def main() -> int:
    model = pick_model()
    print(c(DIM, f"  starting model server ({os.path.basename(model)}) {ELLIPSIS}"), flush=True)
    srv = Server(model)
    app = App(srv)
    print(BANNER.format(ver=APP_VERSION))
    try:
        while True:
            try:
                print("  " + app.status_line())
                line = input(c(BOLD, "you> ")).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            if line.startswith("/"):
                if not app.command(line):
                    break
                continue
            try:
                app.turn(line)
            except Exception as e:  # noqa: BLE001  -- a bug in one turn is reported, not fatal
                print(c(RED, f"  This turn failed inside the program ({type(e).__name__}: {str(e)[:120]}). "
                             "The conversation continues; if it repeats, please report it with the line you typed."))
    finally:
        srv.stop()
    net = f" {app.searches} web search(es) were sent." if app.searches else " No network calls were made."
    if app.written:
        print("\n  Session ended. Written to disk this session: " + ", ".join(app.written) + net)
    else:
        print("\n  Session ended. Nothing was written to disk." + net)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
