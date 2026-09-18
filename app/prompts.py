"""The exact prompt strings the harness sends to the model.

They live in one place because the SFT data (sft/build_harness_seed.py) trains the
model on these strings verbatim. If the app and the training data drift apart, the
model is being asked questions in a dialect it never learned.
"""

TOOL_NAMES = ["calc", "time", "pack_search", "read_file", "write_note"]

SYSTEM_PROMPT = (
    "You are Pagouro, a small offline assistant. Mode: OFFLINE. Today is {date}. "
    "You cannot browse or check anything after your training. If you do not know, say so. "
    "Tools available: " + ", ".join(TOOL_NAMES) + "."
)

ROUTER_PROMPT = (
    "Decide if a tool is needed for the user's message. Reply with JSON: "
    '{"tool": one of none/calc/time/pack_search/read_file/write_note, "arguments": string}. '
    "Use calc for arithmetic, time for the current date or time, pack_search for facts "
    "that might be in the reference packs, read_file for a file the user named, "
    "write_note to save something. Otherwise none."
)


def system_prompt(date_iso: str) -> str:
    return SYSTEM_PROMPT.format(date=date_iso)


def router_json(tool: str, arguments: str) -> str:
    """The one canonical serialisation: no spaces, key order fixed. Matches the GBNF
    grammar in pagouro_app.py, so what the model is trained to emit is exactly what
    the grammar permits."""
    import json
    return '{"tool":"%s","arguments":%s}' % (tool, json.dumps(arguments, ensure_ascii=False))
