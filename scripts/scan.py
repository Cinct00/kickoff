"""Local discovery and security vetting of agent customisations (stdlib only).

discover: finds the skills, agents, prompts, instructions, hooks and MCP servers already on this machine
          (Copilot, Claude Code, Agent Skills, Codex, Gemini) and in a repository, so kickoff can route to
          what the user already has before reaching for the catalog.
vet:      static security scan of a plugin, skill, agent or config before it is trusted. It cannot prove
          anything safe; it catches the known-bad patterns (pipe-to-shell, permission bypass flags, prompt
          injection, hidden Unicode, unpinned MCP servers, base-URL hijacks) so a human looks first.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

MAX_BYTES = 512_000
MAX_FILES = 4000
TEXT_EXT = {".md", ".json", ".jsonc", ".toml", ".yaml", ".yml", ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".py",
            ".js", ".mjs", ".cjs", ".ts", ".rb", ".txt", ".mdc", ""}
SKIP_NAMES = {"README.md", "CHANGELOG.md", "LICENSE", "LICENSE.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "docs", "test", "tests"}

# (severity, id, regex, applies-to, explanation). applies-to: "md" (instructions an agent reads), "shell" (shell
# scripts and the hook / MCP / settings configs that run commands), "code" (Python/JS/TS/Ruby), "run" (shell or
# code), "all".
HIDDEN = "[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff]|[\U000e0000-\U000e007f]"
RULES = [
    ("high", "pipe-to-shell", r"(curl|wget|iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b|\|\s*iex\b",
     "shell", "downloads and runs code in one step"),
    ("high", "decode-and-run", r"base64\s+(-d|--decode)[^\n]*\|\s*(ba|z)?sh|exec\s*\(\s*(base64|codecs|zlib)\.|FromBase64String[^\n]*(iex|Invoke-Expression)",
     "run", "runs obfuscated code"),
    ("high", "reverse-shell", r"/dev/tcp/|\bnc\b[^\n]*\s-e\s|bash\s+-i\s+>&|socat\b[^\n]*exec:", "run", "opens a remote shell"),
    ("high", "permission-bypass", r"--dangerously-skip-permissions|--yolo\b|--allow-all-tools|\bbypassPermissions\b|approval[_-]policy\s*=\s*\"?never",
     "all", "turns off the agent's permission prompts"),
    ("high", "base-url-hijack", r"\b(ANTHROPIC|OPENAI|AZURE_OPENAI|GITHUB_COPILOT)_[A-Z_]*BASE_URL\b\s*[\"']?\s*[:=]",
     "shell", "redirects model traffic (and API keys) to another server"),
    ("high", "prompt-injection", r"ignore (all |any )?(previous|prior|above|earlier) (instructions|rules)|disregard (the |all |your )?(previous |prior )?(instructions|system prompt)"
     r"|do not (tell|inform) the user|(run|execute|send|upload|delete|install|commit|push|proceed|do (this|it))\b[^.\n]{0,40}\bwithout (asking|telling|informing) the user"
     r"|you are now (in )?(developer|dan|jailbreak)",
     "md", "instructions that try to override the user or hide actions from them"),
    ("high", "hidden-unicode", HIDDEN, "all", "invisible or bidirectional characters can hide instructions"),
    ("high", "plain-http-mcp", r"\"(url|serverUrl)\"\s*:\s*\"http://(?!localhost|127\.0\.0\.1|\[::1\])", "shell", "MCP traffic without TLS"),
    ("medium", "secret-access", r"~/\.ssh|\bid_rsa\b|\bid_ed25519\b|\.aws/credentials|~/\.netrc|gh\s+auth\s+token|security find-generic-password",
     "shell", "reads credential files"),
    ("medium", "secret-access", r"(read|cat|open|send|upload|copy)\b[^.\n]{0,40}(~/\.ssh|\bid_rsa\b|\.aws/credentials|~/\.netrc|\.env\b)", "md",
     "tells the agent to read credential files"),
    ("medium", "unpinned-mcp", r"\"(npx|bunx|uvx)\"\s*,\s*\"args\"\s*:\s*\[\s*(?:\"-y\"\s*,\s*)?\"(?!@?[\w./-]+@\d)(?!-)[@\w./-]+\"|\"docker\"[^\]]*\"[\w./-]+(:latest)?\"\s*\]",
     "shell", "MCP server runs whatever version the registry serves next (pin a version or digest)"),
    ("medium", "network-in-hook", r"\b(curl|wget|Invoke-WebRequest|Invoke-RestMethod)\b", "shell", "hook or script talks to the network"),
    ("medium", "network-in-hook", r"^\s*(import (requests|httpx|urllib\.request|http\.client|socket)|from (requests|httpx|urllib\.request|http\.client) import)|\bfetch\(|require\(['\"](https?|axios|node-fetch)['\"]\)",
     "code", "hook or script talks to the network"),
    ("medium", "dynamic-exec", r"\beval\s+[\"$`]|Invoke-Expression", "shell", "builds and runs shell strings at runtime"),
    ("medium", "dynamic-exec", r"(?<![\w.])(eval|exec)\(|os\.system\(|subprocess\.[a-z_]+\([^\n]*shell\s*=\s*True|\bnew Function\(|require\(['\"]child_process['\"]\)",
     "code", "builds and runs code or shell strings at runtime"),
    ("medium", "destructive", r"\brm\s+-[a-z]*r[a-z]*f?\s+[\"']?(\$|~|/(?!tmp))|Remove-Item[^\n]*-Recurse[^\n]*-Force|\bmkfs\b|\bdd\s+if=", "shell", "deletes broadly"),
    ("medium", "broad-tools", r"allowed-tools\s*:[^\n]*\b(Bash|Shell)\b(?!\()|Bash\(\*\)", "all", "grants unrestricted shell"),
]
COMPILED = [(sev, rid, re.compile(rx, (re.I | re.M) if rid not in ("hidden-unicode", "base-url-hijack") else re.M), scope, why)
            for sev, rid, rx, scope, why in RULES]
# A flagged phrase on a line that is clearly warning about it, or quoting it as an example, is downgraded.
DEFENSIVE = re.compile(r"\b(never|don'?t|do not|avoid|refuse|reject|detect|flag|warn|example|e\.g\.|such as|untrusted|injection|"
                       r"attack|malicious|treat .{0,30} as data|is data|not instructions)\b", re.I)
SHELL_EXT = {".sh", ".bash", ".zsh", ".ps1", ".psm1"}
CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".rb"}


def _kinds(p: Path) -> set:
    n, suf = p.name.lower(), p.suffix.lower()
    kinds = set()
    if suf in SHELL_EXT or suf in (".json", ".jsonc", ".toml") and (
            "hook" in str(p).lower() or "mcp" in n or "settings" in n or n == "config.toml"):
        kinds |= {"shell", "run"}
    if suf in CODE_EXT:
        kinds |= {"code", "run"}
    if suf in (".md", ".mdc", ".txt") and p.name not in SKIP_NAMES:
        kinds.add("md")
    return kinds | {"all"}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        links = [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d not in links]
        for f in links + filenames:  # symlinked directories are reported, never followed
            n += 1
            if n > MAX_FILES:
                return
            yield Path(dirpath) / f


def vet_path(root: Path) -> list[dict]:
    """Findings for every file under root: [{severity, rule, file, line, why, excerpt}]."""
    root = Path(root)
    base = root if root.is_dir() else root.parent
    findings = []
    for p in iter_files(root):
        rel = str(p.relative_to(base)) if p != base else p.name
        if p.is_symlink():
            try:
                p.resolve().relative_to(base.resolve())
            except (ValueError, OSError):
                findings.append({"severity": "high", "rule": "symlink-escape", "file": rel, "line": 0,
                                 "why": "symlink points outside the plugin", "excerpt": os.readlink(p)})
            continue
        if p.name in SKIP_NAMES or p.suffix.lower() not in TEXT_EXT:
            if p.suffix.lower() in (".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".jar", ".node"):
                findings.append({"severity": "medium", "rule": "binary", "file": rel, "line": 0,
                                 "why": "ships a compiled binary that cannot be reviewed", "excerpt": ""})
            continue
        try:
            if p.stat().st_size > MAX_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        kinds = _kinds(p)
        lines = text.splitlines()
        done = set()
        for sev, rid, rx, scope, why in COMPILED:
            if scope not in kinds or rid in done:
                continue
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                src = lines[line - 1] if line <= len(lines) else ""
                level, reason = sev, why
                if rid in ("prompt-injection", "permission-bypass") and DEFENSIVE.search(src):
                    level, reason = "medium", why + " (mentioned in what looks like a warning or example; confirm)"
                excerpt = repr(m.group(0)) if rid == "hidden-unicode" else src.strip()[:140]
                findings.append({"severity": level, "rule": rid, "file": rel, "line": line, "why": reason, "excerpt": excerpt})
                done.add(rid)  # one finding per rule per file keeps reports readable
                break
    order = {"high": 0, "medium": 1}
    return sorted(findings, key=lambda f: (order[f["severity"]], f["file"], f["line"]))


def verdict(findings: list[dict]) -> str:
    if any(f["severity"] == "high" for f in findings):
        return "block"
    return "review" if findings else "ok"


# --------------------------------------------------------------------------- discover

def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v and not line.startswith((" ", "\t")):
                out[k.strip()] = v.strip().strip("\"'")
    return out


def _desc(p: Path) -> str:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")[:6000]
    except OSError:
        return ""
    d = _frontmatter(text).get("description", "")
    if not d:
        body = re.sub(r"^---.*?---", "", text, flags=re.S)
        d = next((l.strip("# ").strip() for l in body.splitlines() if l.strip()), "")
    return re.sub(r"\s+", " ", d)[:160]


def _json(p: Path) -> dict:
    try:
        data = json.loads(re.sub(r"^\s*//.*$", "", p.read_text(encoding="utf-8", errors="replace"), flags=re.M))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def locations(home: Path, repo: Path | None) -> list[tuple[str, str, Path]]:
    """(scope, client, path) roots to scan."""
    env = os.environ
    copilot = Path(env.get("COPILOT_HOME", home / ".copilot"))
    claude = Path(env.get("CLAUDE_CONFIG_DIR", home / ".claude"))
    locs = [("user", "copilot", copilot), ("user", "claude", claude), ("user", "agent-skills", home / ".agents"),
            ("user", "codex", home / ".codex"), ("user", "gemini", home / ".gemini")]
    if os.name == "nt" and env.get("APPDATA"):
        locs.append(("user", "vscode", Path(env["APPDATA"]) / "Code" / "User"))
    else:
        for vs in (home / ".config" / "Code" / "User", home / "Library" / "Application Support" / "Code" / "User"):
            locs.append(("user", "vscode", vs))
    if repo:
        locs += [("project", "copilot", repo / ".github"), ("project", "claude", repo / ".claude"),
                 ("project", "agent-skills", repo / ".agents"), ("project", "vscode", repo / ".vscode"),
                 ("project", "any", repo)]
    return [l for l in locs if l[2].exists()]


def discover(home: Path, repo: Path | None, toolkit_root: Path | None = None, with_vet: bool = True) -> list[dict]:
    items, seen = [], set()

    def add(kind, name, scope, client, path: Path, desc="", vet_target: Path | None = None):
        key = (kind, str(path))
        if key in seen:
            return
        seen.add(key)
        own = False
        try:
            own = bool(toolkit_root) and path.resolve().is_relative_to(toolkit_root.resolve())  # type: ignore[attr-defined]
        except (OSError, AttributeError, ValueError):
            own = False
        item = {"kind": kind, "name": name, "scope": scope, "client": client, "path": str(path),
                "description": desc, "source": "kickoff" if own else "local"}
        if with_vet and vet_target is not None and not own:
            item["verdict"] = verdict(vet_path(vet_target))
        items.append(item)

    for scope, client, root in locations(home, repo):
        shallow = client == "any"  # the repo root itself: only top-level instruction files and MCP config
        if shallow:
            for f in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules"):
                if (root / f).is_file():
                    add("instructions", f, scope, client, root / f, _desc(root / f), root / f)
            for f in (".mcp.json",):
                if (root / f).is_file():
                    for name in (_json(root / f).get("mcpServers") or {}):
                        add("mcp", name, scope, client, root / f, "", root / f)
            continue
        # skills (also inside installed plugins: any SKILL.md below the root, bounded)
        for i, sk in enumerate(root.rglob("SKILL.md")):
            if i > 2000:
                break
            if any(part in SKIP_DIRS for part in sk.parts):
                continue
            add("skill", _frontmatter(sk.read_text(encoding="utf-8", errors="replace")[:4000]).get("name") or sk.parent.name,
                scope, client, sk.parent, _desc(sk), sk.parent)
        for pattern, kind in (("agents/*.md", "agent"), ("chatmodes/*.chatmode.md", "agent"), ("prompts/*.prompt.md", "prompt"),
                              ("commands/*.md", "command"), ("instructions/*.instructions.md", "instructions"),
                              ("copilot-instructions.md", "instructions"), ("AGENTS.md", "instructions"), ("CLAUDE.md", "instructions"),
                              ("GEMINI.md", "instructions"), ("rules/*.mdc", "instructions")):
            for f in root.glob(pattern):
                name = f.name
                for suf in (".agent.md", ".chatmode.md", ".prompt.md", ".instructions.md", ".md", ".mdc"):
                    if name.endswith(suf):
                        name = name[: -len(suf)]
                        break
                add(kind, name, scope, client, f, _desc(f), f)
        # hooks: Copilot hook files, Claude settings hooks, plugin hooks.json
        for hf in list(root.glob("hooks/*.json")) + [root / "settings.json", root / "settings.local.json"]:
            if hf.is_file():
                for event in (_json(hf).get("hooks") or {}):
                    add("hook", f"{event}", scope, client, hf, f"{hf.name}", hf)
        # MCP servers
        for mf in (root / "mcp-config.json", root / "mcp.json", root / ".mcp.json", root / "settings.json", root / "config.toml"):
            if not mf.is_file():
                continue
            if mf.suffix == ".toml":
                for name in re.findall(r"^\[mcp_servers\.([\w.-]+)\]", mf.read_text(encoding="utf-8", errors="replace"), re.M):
                    add("mcp", name, scope, client, mf, "codex config.toml", mf)
                continue
            data = _json(mf)
            for name in (data.get("mcpServers") or data.get("servers") or {}):
                add("mcp", name, scope, client, mf, mf.name, mf)
        # installed plugins (Claude Code cache, Copilot installs): one entry per plugin manifest
        for i, pm in enumerate(list(root.rglob(".claude-plugin/plugin.json")) + list(root.rglob("plugin.json"))):
            if i > 500:
                break
            pdir = pm.parent.parent if pm.parent.name == ".claude-plugin" else pm.parent
            if any(part in SKIP_DIRS for part in pm.parts) or pdir == root:
                continue
            data = _json(pm)
            if data.get("name"):
                add("plugin", data["name"], scope, client, pdir, str(data.get("description", ""))[:160], pdir)
    # Precedence order, as kickoff routes: this repo's own tools, then the user's (work/domain), then Kickoff's.
    tier = lambda x: 0 if x["scope"] == "project" else 1 if x["source"] == "local" else 2
    order = {"skill": 0, "agent": 1, "prompt": 2, "command": 3, "instructions": 4, "mcp": 5, "hook": 6, "plugin": 7}
    return sorted(items, key=lambda x: (tier(x), order.get(x["kind"], 9), x["client"], x["name"]))


def to_tsv(items: list[dict]) -> str:
    head = "# kind\tname\tscope\tclient\tsource\tverdict\tpath\tdescription\n"
    rows = ["\t".join([i["kind"], i["name"], i["scope"], i["client"], i["source"], i.get("verdict", "-"), i["path"],
                       i["description"].replace("\t", " ")]) for i in items]
    return head + "\n".join(rows) + ("\n" if rows else "")
