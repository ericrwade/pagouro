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
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompts import SYSTEM_PROMPT, ROUTER_PROMPT  # noqa: E402  (shared with the SFT builder)

APP_VERSION = "0.1.0 (MVP framework)"
MAX_TOKENS_ANSWER = 200          # generation budget per answer
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
    raise SystemExit(f"no .gguf model found in {MODEL_DIR}")


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
        cmd = [SERVER_EXE, "-m", model, "--port", str(self.port), "--host", "127.0.0.1",
               "-ngl", "0", "-t", str(threads), "--log-disable", "--no-webui"]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     creationflags=flags)
        for _ in range(120):
            try:
                if self.get("/health").get("status") == "ok":
                    break
            except Exception:
                pass
            if self.proc.poll() is not None:
                raise SystemExit("llama-server exited during startup")
            time.sleep(0.25)
        else:
            raise SystemExit("llama-server did not become ready")
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


class Packs:
    """Keyword search over plain-text packs. Deliberately simple: chunk by paragraph,
    score by overlap of query words, return the best few. A real build swaps this for
    an embedding index; the interface stays the same."""

    def __init__(self, root: str):
        self.chunks: list[tuple[str, str]] = []   # (source name, text)
        self.names: list[str] = []
        if not os.path.isdir(root):
            return
        for fn in sorted(os.listdir(root)):
            if not fn.lower().endswith(".txt"):
                continue
            self.names.append(fn)
            with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as f:
                text = f.read()
            buf = []
            for para in re.split(r"\n\s*\n", text):
                para = " ".join(para.split())
                if not para:
                    continue
                buf.append(para)
                if sum(len(p) for p in buf) >= 600:
                    self.chunks.append((fn, " ".join(buf)))
                    buf = []
            if buf:
                self.chunks.append((fn, " ".join(buf)))

    @staticmethod
    def words(s: str) -> set[str]:
        return {w for w in re.findall(r"[a-z]{3,}", s.lower())
                if w not in {"the", "and", "that", "with", "for", "this", "what", "which", "from", "are", "was", "were", "have", "has", "not", "but", "his", "her", "its", "they", "them", "there", "their", "than", "then", "into", "upon", "about", "does", "did", "how", "why", "who", "can", "all", "any", "one", "two"}}

    def search(self, query: str, k: int = 3) -> list[tuple[str, str, float]]:
        q = self.words(query)
        if not q or not self.chunks:
            return []
        scored = []
        for name, text in self.chunks:
            w = self.words(text)
            if not w:
                continue
            overlap = len(q & w)
            if overlap:
                scored.append((overlap / (len(q) ** 0.5) / (len(w) ** 0.25), name, text))
        scored.sort(reverse=True)
        return [(n, t, s) for s, n, t in scored[:k]]


def tool_pack_search(query: str, app) -> str:
    hits = app.packs.search(query)
    if not hits:
        return "NO_MATCH: nothing in the loaded packs covers this."
    out = []
    for name, text, _ in hits:
        out.append(f"[{name}] {text[:700]}")
    return "\n\n".join(out)


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
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read(4000)
    except OSError as e:
        return f"could not read: {e}"
    return f"[{os.path.basename(path)}, first {len(text)} chars]\n{text}"


def tool_write_note(text: str, app) -> str:
    if not app.can_act:
        return "REFUSED: READ-ONLY mode. Type /act to allow writing to the workspace."
    os.makedirs(os.path.join(WORKSPACE, "notes"), exist_ok=True)
    fn = os.path.join(WORKSPACE, "notes", dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    app.written.append(os.path.relpath(fn, BASE))
    return f"wrote {os.path.relpath(fn, BASE)}"


TOOLS = {
    "calc":        (tool_calc,        "arithmetic on an expression, e.g. 17*23 or (3+4)/2", False),
    "time":        (tool_time,        "the local date and time right now", False),
    "pack_search": (tool_pack_search, "search the offline reference packs for a topic", False),
    "read_file":   (tool_read_file,   "read a text file the user named, or one in the workspace", False),
    "write_note":  (tool_write_note,  "save a note to workspace/notes (needs CAN ACT)", True),
}

# GBNF grammar for the tool decision. Written by hand rather than derived from a
# JSON schema because the schema-derived grammar permits arbitrary whitespace
# between tokens, and a small model will happily spend its whole budget on
# newlines. This one allows none: the object is exactly
#   {"tool":"<name>","arguments":"<string>"}
_ROUTER_TOOLS = " | ".join('"%s"' % t for t in ["none"] + list(TOOLS.keys()))
ROUTER_GRAMMAR = r'''
root  ::= "{\"tool\":\"" tool "\",\"arguments\":\"" chars "\"}"
tool  ::= %s
chars ::= ([^"\\\n] | "\\" .){0,200}
'''.strip() % _ROUTER_TOOLS + "\n"
ROUTER_RE = re.compile(r'"tool"\s*:\s*"(\w+)"(?:\s*,\s*"arguments"\s*:\s*"((?:[^"\\]|\\.)*)")?')


# --------------------------------------------------------------------------
# The app
# --------------------------------------------------------------------------
class App:
    def __init__(self, server: Server):
        self.srv = server
        self.packs = Packs(PACKS_DIR)
        self.stone = False            # D-19: SAND by default
        self.can_act = False          # D-51: READ-ONLY by default
        self.online = False           # D-1: OFFLINE; online mode is not built in this version
        self.history: list[dict] = [] # user/assistant/tool turns, oldest first
        self.last_user_text = ""
        self.transcript_path = None
        self.dropped_total = 0
        self.written: list[str] = []   # every path a tool or STONE wrote, for an honest exit line

    # ---- system prompt: the harness tells the model what it cannot know (D-50)
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(date=dt.date.today().isoformat())

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
    def make_room(self, reserve: int):
        while self.history:
            used, _, _ = self.used_tokens()
            if used + reserve <= self.srv.n_ctx:
                return
            # drop the oldest exchange: a user turn and everything up to the next user turn
            drop = [self.history.pop(0)]
            while self.history and self.history[0]["role"] != "user":
                drop.append(self.history.pop(0))
            self.dropped_total += len(drop)
            head = next((m for m in drop if m["role"] == "user"), drop[0])
            first = " ".join(head["content"].split()[:6])
            where = "still in the saved transcript" if self.stone else "gone (SAND mode)"
            print(c(MAG, f"  {ARROW_OUT} {BOX_FULL} dropped oldest turn: \"{first}{ELLIPSIS}\" -- {where}"))

    # ---- persistence (D-19)
    def record(self, role: str, text: str):
        if not self.stone:
            return
        if self.transcript_path is None:
            os.makedirs(os.path.join(WORKSPACE, "transcripts"), exist_ok=True)
            self.transcript_path = os.path.join(WORKSPACE, "transcripts",
                                                dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
        with open(self.transcript_path, "a", encoding="utf-8") as f:
            f.write(f"{role}: {text}\n")
        rel = os.path.relpath(self.transcript_path, BASE)
        if rel not in self.written:
            self.written.append(rel)

    # ---- the tool loop (D-51)
    def route(self, user_text: str) -> tuple[str, str]:
        """Ask the model, under a grammar, whether a tool is needed. Returns (tool, arguments).
        The grammar guarantees a valid object; the model supplies the judgement."""
        router_msgs = [{"role": "system", "content": ROUTER_PROMPT},
                       {"role": "user", "content": user_text}]
        try:
            raw, _ = self.srv.chat(router_msgs, MAX_TOKENS_ROUTER, grammar=ROUTER_GRAMMAR)
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
                return " ".join(Packs.words(t)) or args
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
                self.history.append({"role": "tool", "content": f"{tool}: {tool_result[:1200]}"})

        self.make_room(MAX_TOKENS_ANSWER)
        try:
            answer, usage = self.srv.chat(self.messages(), MAX_TOKENS_ANSWER)
        except urllib.error.HTTPError as e:
            answer = f"(the model server refused the request: {e.code}; try /clear)"
            usage = {}
        answer = answer.strip() or "(no answer)"
        self.history.append({"role": "assistant", "content": answer})
        self.record("assistant", answer)
        print(c(BOLD, "pagouro> ") + answer)
        if tool_result and tool_result.startswith("NO_MATCH"):
            print(c(DIM, "  note: nothing in the loaded packs covered this; the answer above is from the model alone."))

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
            print(c(YELLOW, "  ONLINE mode is not built in this version. This build makes no network calls at all."))
        elif cmd == "/tools":
            for n, (_, desc, needs) in TOOLS.items():
                print(f"  {n:<12} {desc}{'  [needs CAN ACT]' if needs else ''}")
            print(f"  packs loaded: {', '.join(self.packs.names) or 'none'} ({len(self.packs.chunks)} chunks)")
        elif cmd == "/clear":
            self.history.clear()
            print("  context cleared.")
        elif cmd == "/status":
            print("  " + self.status_line())
        else:
            print("  unknown command; /help")
        return True


HELP = """  commands:
    /stone  /sand      save this chat to disk / stop saving (default: SAND, nothing saved)
    /act    /readonly  allow tools to write inside workspace/ / forbid (default: READ-ONLY)
    /tools             list tools and loaded packs
    /status            show the context gauge
    /clear             forget the conversation
    /online            (not built in this version)
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
            app.turn(line)
    finally:
        srv.stop()
    if app.written:
        print("\n  Session ended. Written to disk this session: " + ", ".join(app.written))
    else:
        print("\n  Session ended. Nothing was written to disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
