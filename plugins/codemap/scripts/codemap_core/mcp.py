"""Minimal MCP server over stdio (JSON-RPC 2.0, newline-delimited), stdlib only.

Exposes ONE tool, `codemap`, that takes a command line. One small schema costs
far fewer context tokens per request than a dozen tool definitions would.
"""
from __future__ import annotations

import io
import json
import sys

from . import VERSION

PROTOCOL = "2025-06-18"
TOOL = {
    "name": "codemap",
    "description": (
        "Query the code map of the current repository instead of grepping or reading whole files. "
        "cmd examples: 'overview', 'map --budget 1500 --focus src/api.py', 'find user session', 'def UserService', "
        "'outline src/auth.py', 'show UserService.login', 'refs get_user', 'callers save', 'deps src/db.py', "
        "'impact src/models/user.py', 'packages', 'sql \"SELECT …\"'. Run 'help' for all commands. "
        "Read-only and limited to this repository: --repo, --db and --out are refused."
    ),
    "annotations": {"readOnlyHint": True, "openWorldHint": False},
    "inputSchema": {
        "type": "object",
        "properties": {"cmd": {"type": "string", "description": "codemap command line, e.g. \"refs UserService\""}},
        "required": ["cmd"],
    },
}
INSTRUCTIONS = ("codemap indexes this repository's symbols, imports and references. Start with 'overview' or "
                "'map', locate with 'find'/'def', read with 'outline'/'show', and check 'impact' before editing.")


def _call(cmd: str) -> tuple[str, bool]:
    from .cli import COMMANDS_HELP, run_line
    if cmd.strip() in ("", "help", "--help", "-h"):
        return COMMANDS_HELP, False
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = run_line(cmd, out, err, restricted=True)
    except Exception as e:  # never crash the server
        return f"codemap error: {type(e).__name__}: {e}", True
    text = out.getvalue().rstrip()
    if err.getvalue().strip():
        msg = "\n".join(l for l in err.getvalue().strip().splitlines() if not l.startswith("  indexing"))
        text = (text + "\n" + msg).strip() if msg else text
    return text or "(no output)", rc not in (0, None)


def handle(msg: dict):
    mid = msg.get("id")
    method = msg.get("method")
    if mid is None:  # notification
        return None
    if method == "initialize":
        requested = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL
        result = {"protocolVersion": requested, "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": "codemap", "version": VERSION}, "instructions": INSTRUCTIONS}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [TOOL]}
    elif method == "tools/call":
        params = msg.get("params") or {}
        if params.get("name") != "codemap":
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {params.get('name')}"}}
        text, is_err = _call(str((params.get("arguments") or {}).get("cmd", "")))
        result = {"content": [{"type": "text", "text": text}], "isError": is_err}
    elif method in ("resources/list", "prompts/list"):
        result = {method.split("/")[0]: []}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def serve(args=None) -> int:
    stdin = sys.stdin
    stdout = sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}) + "\n")
            stdout.flush()
            continue
        batch = msg if isinstance(msg, list) else [msg]
        replies = [r for r in (handle(m) for m in batch if isinstance(m, dict)) if r is not None]
        if replies:
            stdout.write(json.dumps(replies if isinstance(msg, list) else replies[0]) + "\n")
            stdout.flush()
    return 0
