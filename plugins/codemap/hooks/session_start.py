#!/usr/bin/env python3
"""Session-start hook: keep the codemap index warm and tell the agent it exists.

Starts a detached background `codemap index` (cheap when nothing changed) and
returns ~60 tokens of context. Never blocks or fails the session.
Usage: session_start.py --format claude|copilot. Disable with CODEMAP_HOOK=0.
"""
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def emit(fmt: str, ctx: str) -> None:
    if fmt == "copilot":
        print(json.dumps({"additionalContext": ctx} if ctx else {}))
    elif ctx:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))


def main() -> None:
    fmt = sys.argv[sys.argv.index("--format") + 1] if "--format" in sys.argv else "claude"
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except Exception:
        pass
    if os.environ.get("CODEMAP_HOOK", "1") == "0":
        emit(fmt, "")
        return
    sys.path.insert(0, str(SCRIPTS))
    from codemap_core.util import default_db_path, find_repo_root  # noqa: E402

    root = find_repo_root(Path.cwd())
    if not (root / ".git").exists():
        emit(fmt, "")
        return
    db = default_db_path(root)
    stats = None
    if db.exists():
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1)
            files = con.execute("SELECT COUNT(*) FROM files WHERE lang IS NOT NULL").fetchone()[0]
            syms = con.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            last = float((con.execute("SELECT value FROM meta WHERE key='last_refresh'").fetchone() or [0])[0])
            con.close()
            stats = (files, syms, last)
        except Exception:
            stats = None
    if stats is None or time.time() - stats[2] > 60:
        try:
            kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "cwd": str(root)}
            if os.name == "nt":
                kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen([sys.executable, str(SCRIPTS / "codemap.py"), "--repo", str(root), "index", "--quiet"], **kwargs)
        except Exception:
            pass
    how = "the `codemap` tool or `codemap <cmd>`"
    if stats:
        ctx = (f"codemap index for this repo: {stats[0]} files, {stats[1]} symbols. Navigate with {how} "
               "(overview, map, find, def, outline, show, refs, callers, impact) before grepping or reading whole files.")
    else:
        ctx = (f"codemap is indexing this repo in the background. Navigate with {how} "
               "(overview, map, find, def, outline, show, refs, impact) before grepping or reading whole files.")
    emit(fmt, ctx)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("{}")
