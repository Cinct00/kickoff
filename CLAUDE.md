@AGENTS.md

## Claude Code notes

- Test the plugins from this checkout without installing: `claude --plugin-dir plugins/kickoff` (repeat `--plugin-dir` for others), or `python3 scripts/toolkit.py install --local --target claude`.
- Plugin skills appear namespaced (`kickoff:kickoff`, `engineering-craft:reviewing-code`); plugin agents as `doc-coauthor:doc-review`.
