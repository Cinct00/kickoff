# local-first

Local-first lookups: a PreToolUse hook that stops MCP, WebFetch and curl/gh calls from fetching remote code or docs that already exist on disk (local clones, installed dependencies, mapped docs folders) and points the agent at the local paths instead. Zero tokens unless it redirects.

Part of [ai-toolkit](../../README.md).

## What it does

Agents often reach for a remote MCP server or a web fetch (GitHub file contents, code search, Context7 or DeepWiki docs, `raw.githubusercontent.com`, `docs.rs`, `npmjs.com`…) even when the same content already sits on disk. A remote call costs a round trip, often returns a large payload, and can describe a different version than the one the project actually uses. Before every MCP tool, `WebFetch`, `WebSearch` and network-looking `Bash` call, the hook works out what the call would fetch and looks for a local copy:

| The call fetches | Checked locally |
|---|---|
| A file or tree in `owner/repo` (GitHub MCP `get_file_contents`/`get_repository_tree`, `github.com/.../blob/...`, `raw.githubusercontent.com`, `api.github.com/repos/.../contents`, `gh api repos/.../contents/...`, DeepWiki `repoName`) | Clones whose `.git/config` remote is `owner/repo`, found under the scan roots. The current project always counts. |
| A code search scoped with `repo:owner/name` | The same clones (search them with Grep or codemap) |
| Library docs (Context7 `libraryName` or `/owner/project` ids, `npmjs.com/package/x`, `pypi.org/project/x`, `docs.rs/x`, `pkg.go.dev/x`) | `node_modules/x`, `.venv/lib/python*/site-packages/x`, `vendor/x`, the Cargo registry, the Go module cache, a clone of the library's repo, and your docs map |
| A docs URL or a docs/web search mentioning a mapped name | Your docs map (see below) |

When it finds a local copy, the hook **denies the first remote call** and gives the agent the local paths. If the local copy doesn't answer the question (for example, it needs a newer version), the agent repeats the identical call and it goes through. Calls with no local copy pass silently, so the hook costs no tokens. Calls that write (create, update, push…) or that fetch things with no local equivalent (issues, PRs, CI runs, commits, chat) are never touched.

## Modes

| Mode | Behaviour |
|---|---|
| `once` (default) | Redirect the first call per target in a session; a repeat is allowed |
| `strict` | Always deny a remote call that has a local copy. The agent must update the local copy (`git pull`) or you must relax the mode. |
| `off` | Disabled |

Set the mode with `AI_TOOLKIT_LOCAL_FIRST=once|strict|off`, or with `"mode"` in a config file.

## Configuration

All optional. User level: `~/.config/ai-toolkit/local-first.json` (honours `$XDG_CONFIG_HOME`).

```json
{
  "mode": "once",
  "roots": ["~/src", {"path": "~/work", "depth": 4}],
  "docs": {
    "terraform": "~/docs/terraform",
    "https://docs.python.org/3/": "~/docs/python-3.12"
  },
  "ignore_tools": ["mcp__notion__.*"]
}
```

- `roots`: where to look for clones, in addition to `~/src`, `~/code`, `~/projects`, `~/repos`, `~/dev`, `~/git`, `~/work`, `~/workspace`, `~/ghq`, `~/go/src`, `~/source/repos` and the directories next to the current project. `AI_TOOLKIT_LOCAL_ROOTS` (path-separator list) adds more. The clone index is cached for 10 minutes in `~/.cache/ai-toolkit/`.
- `docs`: keys are either a library or topic name (matched against library arguments and as a whole word in docs/web search queries) or a URL prefix (the rest of the URL is mapped onto the folder).
- `ignore_tools`: regexes of tool names to leave alone.

Project level: `<repo>/.ai-toolkit/local-first.json` may set `mode`, `ignore_tools`, and `docs` entries with paths **inside the repository** (for example `"docs": {"our-sdk": "docs/sdk"}`). A repository can't add scan roots or point the hook outside itself, because its contents are untrusted.

## Security notes

- The hook never runs `git` or any repository code. It reads `.git/config` and `.git/HEAD` as plain text, skips symlinked directories while scanning, and only suggests paths that resolve inside the clone, package or docs folder they belong to.
- It only ever denies a call, never allows one. Your permission rules still decide whether the agent may read the suggested local paths.
- It fails open: any error lets the call through.

## Platforms

- **Claude Code**: `PreToolUse` with matcher `mcp__.*|WebFetch|WebSearch|Bash` (`hooks/hooks.json`).
- **GitHub Copilot**: `preToolUse` (`hooks/copilot-hooks.json`). Copilot runs it for every tool, so the script exits immediately for local tools. The Copilot hook output format follows the Copilot CLI docs but hasn't been exercised in a live Copilot session yet (same caveat as the toolkit's other Copilot hooks; see `docs/platforms.md`).
- **Codex, Cursor, Gemini CLI**: the toolkit installs no hooks there. The behaviour can't be enforced, only asked for in `AGENTS.md`.

<!-- BEGIN GENERATED:install -->
## Install

Claude Code:

```
/plugin marketplace add Cinct00/ai-toolkit
/plugin install local-first@kickoff
```

GitHub Copilot CLI:

```bash
copilot plugin marketplace add Cinct00/ai-toolkit
copilot plugin install local-first@kickoff
```

Any other Agent Skills client: copy or link `skills/*` into `~/.agents/skills/` (or run `python3 scripts/toolkit.py install --target skills` from the toolkit).

## Contents

Hooks: Claude Code PreToolUse (`hooks/hooks.json`); Copilot preToolUse (`hooks/copilot-hooks.json`).
<!-- END GENERATED:install -->
