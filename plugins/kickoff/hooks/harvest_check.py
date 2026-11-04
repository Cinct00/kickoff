#!/usr/bin/env python3
"""Stop hook (Claude Code): nudge once when a kickoff route ran without a harvest.

Kickoff's rule is "never skip the harvest step". This checks it mechanically:
if the transcript has a `Route:` line from kickoff and no `Harvest` block after
it, block the stop once with a reminder. It never blocks twice for the same
route, never blocks when the agent is already continuing from a stop hook, and
fails open on any error. Disable with AI_TOOLKIT_HARVEST_CHECK=0.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROUTE_RE = re.compile(r"^\s*\**Route:\**\s+.+→", re.M)
HARVEST_RE = re.compile(r"^\s*\**Harvest\b", re.M)


def assistant_texts(transcript: Path):
    with transcript.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            content = (entry.get("message") or {}).get("content")
            if isinstance(content, str):
                yield content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        yield block.get("text", "")


def main() -> None:
    if os.environ.get("AI_TOOLKIT_HARVEST_CHECK", "1") == "0":
        return
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    transcript = Path(data.get("transcript_path") or "")
    if not transcript.is_file():
        return

    last_route, harvested_after = None, False
    for text in assistant_texts(transcript):
        routes = ROUTE_RE.findall(text)
        if routes:
            last_route, harvested_after = routes[-1].strip(), False
            tail = text[text.rfind(routes[-1]) :]
            harvested_after = bool(HARVEST_RE.search(tail))
        elif last_route and HARVEST_RE.search(text):
            harvested_after = True
    if not last_route or harvested_after:
        return

    key = hashlib.sha1(f"{data.get('session_id')}|{last_route}".encode()).hexdigest()[:16]
    state = Path(tempfile.gettempdir()) / "ai-toolkit-harvest-check"
    state.mkdir(exist_ok=True)
    marker = state / key
    if marker.exists():
        return
    marker.touch()
    print(json.dumps({
        "decision": "block",
        "reason": "Kickoff stated a route but no harvest has run. If the task is finished, load the `harvest` "
                  "skill and end with the Harvest block (or one line: 'Harvest: nothing reusable this session'). "
                  "If you are waiting on the user, just end your turn again; this reminder will not repeat for this route.",
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
