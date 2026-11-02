# Toolkit gaps

The toolkit-wide ledger. Projects that adopted the toolkit keep their own in `.github/ai-toolkit/gaps.md`.

Kickoff appends here when a task had no good route, or a tool fell short. Harvest closes a gap by
building a skill, agent or hook, or by installing an existing plugin from the catalog.

| Date | Task | Gap | Resolution |
|---|---|---|---|
| 2026-11-02 | codemap precision for C-family edge cases | regex extraction misses some constructs (macro-generated functions, JS regex literals, TS class properties typed with function types) | open: optional tree-sitter backend when the wheels are installed |
| 2026-11-02 | VS Code verification | VS Code docs were unreachable from the build environment; user-level skills/agents/MCP and agent-plugin marketplaces assumed from shared conventions | open: confirm on first VS Code use and record in docs/platforms.md |
| 2026-11-02 | Copilot CLI verification | formats follow GitHub's docs and marketplaces; the Copilot CLI itself was not available to test | open |
