#!/usr/bin/env python3
"""Session-start hook: tell the agent the toolkit is here and how to use it.

Works for Claude Code (--format claude) and GitHub Copilot CLI / cloud agent
(--format copilot). Never fails the session: any error prints an empty result.
"""
import json
import os
import sys
from pathlib import Path


def toolkit_home():
    env = os.environ.get("KICKOFF_HOME")
    if env and Path(env, "toolkit.json").is_file():
        return env
    marker = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kickoff" / "home"
    try:
        p = marker.read_text(encoding="utf-8").strip()
        if p and Path(p, "toolkit.json").is_file():
            return p
    except OSError:
        pass
    default = Path.home() / ".kickoff"
    return str(default) if (default / "toolkit.json").is_file() else None


def open_gaps(cwd: Path) -> int:
    for f in (cwd / ".github" / "kickoff" / "gaps.md", cwd / "catalog" / "gaps.md"):
        try:
            return sum(1 for line in f.read_text(encoding="utf-8").splitlines()
                       if line.startswith("|") and line.rstrip().rstrip("|").strip().endswith("open"))
        except OSError:
            continue
    return 0


def build_context() -> str:
    parts = [
        "The Kickoff toolkit is installed (skills: kickoff, harvest, toolkit-adopt, codemap, plus judgment skills such as "
        "understanding-the-problem, debugging-systematically, reviewing-code, writing-clearly).",
        "For any substantial task, load the `kickoff` skill first: it prefers this repo's and your own skills, "
        "agents and prompts, falls back to Kickoff's generic ones and the catalog, and ends with `harvest`.",
    ]
    home = toolkit_home()
    if home:
        parts.append(f"Toolkit checkout: {home} (write cross-project skills/agents/hooks there during harvest).")
    gaps = open_gaps(Path.cwd())
    if gaps:
        parts.append(f"{gaps} open toolkit gap(s) are logged in this repo's gaps ledger; harvest can close them.")
    if home:
        refresh_inventory(Path(home))
        nudge = doctor_nudge(Path(home))
        if nudge:
            parts.append(nudge)
    return " ".join(parts)


def refresh_inventory(home: Path) -> None:
    """Keep ~/.config/kickoff/local-inventory.tsv (local skills/agents/hooks/MCP + vet verdicts) at most a day old.
    Runs detached so the session never waits for it."""
    import subprocess
    import time
    inv = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kickoff" / "local-inventory.tsv"
    try:
        if inv.exists() and time.time() - inv.stat().st_mtime < 86400:
            return
        kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "cwd": os.getcwd()}
        if os.name == "nt":
            kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen([sys.executable, str(home / "scripts" / "toolkit.py"), "discover"], **kwargs)
    except Exception:
        pass


def doctor_nudge(home: Path) -> str:
    """At most once a day, run a quick device health check and surface one line if something is off."""
    import subprocess
    import time
    stamp = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kickoff" / "last-doctor"
    try:
        if stamp.exists() and time.time() - stamp.stat().st_mtime < 86400:
            return ""
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        out = subprocess.run([sys.executable, str(home / "scripts" / "toolkit.py"), "doctor", "--quick", "--summary"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        return out
    except Exception:
        return ""


def main() -> None:
    fmt = "claude"
    if "--format" in sys.argv:
        fmt = sys.argv[sys.argv.index("--format") + 1]
    try:
        sys.stdin.read() if not sys.stdin.isatty() else None
    except Exception:
        pass
    try:
        ctx = build_context()
    except Exception:
        print("{}")
        return
    if fmt == "copilot":
        print(json.dumps({"additionalContext": ctx}))
    else:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))


if __name__ == "__main__":
    main()
