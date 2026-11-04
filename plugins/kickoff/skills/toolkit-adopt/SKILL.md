---
name: toolkit-adopt
description: "Brings the AI toolkit into another repository so kickoff, the judgment skills and the right Anthropic, GitHub and partner plugins work there for every collaborator and in GitHub Copilot (CLI, cloud agent, VS Code) as well as Claude Code. Inventories the repo's existing AI setup, picks what fits the stack, writes the config, and lists gaps. Use when the user says 'set up the toolkit here', 'add my skills to this repo', 'make Copilot use kickoff in this project', or opens a repo with no AI configuration."
---

# Toolkit adopt

Goal: after this runs, anyone opening the repository in Claude Code or GitHub Copilot gets kickoff, the relevant judgment skills and the right procedure plugins, without per-person setup. Choose the minimum that fits the project; a lean setup gets used, a sprawling one gets ignored.

## 1. Inventory what the repo already has

Read before writing. Look for:

- Instructions: `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.cursorrules`, `GEMINI.md`.
- Skills and agents: `.claude/skills/`, `.github/skills/`, `.agents/skills/`, `.claude/agents/`, `.github/agents/`.
- Hooks and settings: `.claude/settings.json`, `.github/hooks/*.json`, `.github/copilot/settings.json`.
- An earlier adoption: `.github/ai-toolkit/lock.json`.
- The stack: languages, frameworks, test runner, CI, deploy target, whether there is a UI, data work, docs work.

Note conflicts (an existing skill with the same name as a toolkit one, contradictory instructions) and keep the project's version unless the user says otherwise.

## 2. Choose the set

First decide **where** things live. Copilot (CLI, cloud agent, VS Code) and Claude Code now load skills, agents, hooks and MCP servers from the user level (`~/.copilot/…`, `~/.claude/…`) across every repo on a device, so personal tooling belongs there (`toolkit.py install`), not in each repository. Put things in the repo only when collaborators or the Copilot cloud agent need them, and prefer `--mode plugins` (a few lines of settings) over vendoring copies, which go stale and, for skills, shadow the user-level versions. If the repo already has vendored copies, run `toolkit.py doctor --repo . --fix` to remove duplicates of what is installed at user level.

Default to the `dev` bundle: `kickoff`, `codemap`, `engineering-craft`, `thinking-tools`, `doc-coauthor`. Add `communication-and-leadership` for teams that write a lot of docs and proposals.

Then pick upstream plugins from the catalog (`kickoff/references/catalog.tsv`) that match the stack. Typical picks:

| Project signal | Plugins |
|---|---|
| Any code repo | `feature-dev`, `pr-review-toolkit`, `code-review` (all `@claude-plugins-official`) |
| Security-sensitive, auth, payments | `security-guidance@claude-plugins-official` |
| Web UI | `frontend-design`, `modern-web-guidance` (`@claude-plugins-official`) |
| Legacy code, migrations | `code-modernization@claude-plugins-official` |
| Data / analytics | `data@knowledge-work-plugins` |
| Copilot-heavy team | search `awesome-copilot` and `copilot-plugins` rows in the catalog for the stack (e.g. `dotnet`, `java-development`, `azure-skills`) |

Search the catalog for the project's stack keywords as well; there is often a stack-specific plugin nobody has installed. Present the chosen set in one short list with a reason per item, and get the user's yes before writing.

## 3. Write the configuration

**If the toolkit checkout is available** (`$AI_TOOLKIT_HOME`, `~/.config/ai-toolkit/home`, or `~/.ai-toolkit`), run its CLI from the target repo root:

```bash
python3 "$AI_TOOLKIT_HOME/scripts/toolkit.py" adopt . --bundle dev \
  --upstream feature-dev@claude-plugins-official --upstream pr-review-toolkit@claude-plugins-official
```

Add `--mode vendor` when the repo must work without plugin support (VS Code without agent plugins, Codex, Cursor) or must not depend on GitHub at runtime; that copies the skills into `.claude/skills/` and agents into `.claude/agents/` instead. Use `--dry-run` first if the repo already has AI config.

**Without the toolkit checkout**, write the same files by hand:

1. `.claude/settings.json` and `.github/copilot/settings.json` (merge into existing JSON; Copilot CLI *and* Copilot cloud agent read the second one):

   ```json
   {
     "extraKnownMarketplaces": {
       "ai-toolkit": { "source": { "source": "github", "repo": "Cinct00/ai-toolkit" } },
       "claude-plugins-official": { "source": { "source": "github", "repo": "anthropics/claude-plugins-official" } }
     },
     "enabledPlugins": {
       "kickoff@ai-toolkit": true,
       "engineering-craft@ai-toolkit": true,
       "feature-dev@claude-plugins-official": true
     }
   }
   ```

2. `AGENTS.md`: add a short block, delimited by `<!-- ai-toolkit:begin -->` / `<!-- ai-toolkit:end -->`, telling agents to start substantial tasks with the `kickoff` skill and to put project-specific harvested skills in `.claude/skills/`. Copilot, Codex, Cursor and Gemini read `AGENTS.md`.
3. `CLAUDE.md`: if missing, create it containing `@AGENTS.md`; if present, make sure it imports `AGENTS.md`.
4. `.github/ai-toolkit/gaps.md`: the gaps ledger (table header `| Date | Task | Gap | Resolution |`).

## 4. Fill project-specific gaps

With the set installed, look for what the project needs that nothing covers: its build/test commands, deployment steps, house conventions, a domain glossary. Capture them the harvest way (load `harvest`): project-specific skills in `.claude/skills/`, rules that must always hold as hooks, and anything reusable across projects in the toolkit. Then run the `claude-code-setup` automation recommender if it is installed for repo-specific hook and MCP suggestions.

## 5. Report

List what was written (paths), which plugins are enabled, and the gaps logged. Remind the user to review and commit the changes in that repository; never commit or push there without their yes.
