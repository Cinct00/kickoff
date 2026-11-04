#!/usr/bin/env bash
# Set up ai-toolkit on this device (macOS / Linux / WSL / Git Bash).
#
#   curl -fsSL https://raw.githubusercontent.com/gimarais/ai-toolkit/main/install.sh | bash
#   ./install.sh --dry-run            # any toolkit.py install options pass through
#
# Clones (or updates) the toolkit into $AI_TOOLKIT_HOME (default ~/.ai-toolkit),
# then runs `toolkit.py install`.
set -euo pipefail

REPO="${AI_TOOLKIT_REPO:-https://github.com/gimarais/ai-toolkit.git}"
HOME_DIR="${AI_TOOLKIT_HOME:-$HOME/.ai-toolkit}"

command -v git >/dev/null 2>&1 || { echo "error: git is required" >&2; exit 1; }
PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "error: Python 3.9+ is required" >&2; exit 1; }

# If run from inside a checkout, use it in place.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/toolkit.json" ]; then
  HOME_DIR="$SCRIPT_DIR"
elif [ -d "$HOME_DIR/.git" ]; then
  git -C "$HOME_DIR" pull --ff-only
else
  git clone "$REPO" "$HOME_DIR"
fi

exec "$PY" "$HOME_DIR/scripts/toolkit.py" install "$@"
