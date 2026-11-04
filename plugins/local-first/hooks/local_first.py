#!/usr/bin/env python3
"""PreToolUse hook: look locally before querying remote code or documentation.

Before an MCP tool, WebFetch or a curl/gh command fetches a file, a code search
or library docs from a remote source, this checks whether the same content is
already on disk:

- a local clone of the GitHub repo (found by scanning the configured roots and
  reading each `.git/config` remote URL as text; git itself is never run),
- an installed dependency (node_modules, Python site-packages, the Cargo
  registry, the Go module cache, vendor/),
- a docs folder you mapped in the config (by library name or URL prefix).

When it finds one, the first remote call for that target is denied with the
local paths to use instead. The default mode is "once": repeating the identical
call afterwards goes through, so a stale or incomplete local copy never traps
the agent. "strict" denies every time a local copy exists; "off" disables it.
Calls with no local equivalent pass silently, so the hook adds no tokens.

Config (all optional, JSON), merged in this order:
  ~/.config/kickoff/local-first.json      user level ($XDG_CONFIG_HOME honoured)
  <project>/.kickoff/local-first.json      project level (only "mode", "docs"
                                              inside the project, and "ignore_tools")
  {
    "mode": "once" | "strict" | "off",
    "roots": ["~/src", {"path": "~/work", "depth": 4}],
    "docs": {"terraform": "~/docs/terraform",
             "https://docs.python.org/3/": "~/docs/python-3"},
    "ignore_tools": ["mcp__slack__.*"]
  }
Environment: KICKOFF_LOCAL_FIRST=once|strict|off overrides the mode;
KICKOFF_LOCAL_ROOTS (os.pathsep-separated) adds roots.

Usage: local_first.py --format claude|copilot (hook JSON on stdin). Fails open.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

INDEX_TTL = 600            # seconds before the clone index is rebuilt
MAX_DIRS = 20000           # cap on directories visited per index build
MAX_SUGGESTIONS = 3
DEFAULT_ROOTS = ["~/src", "~/code", "~/projects", "~/repos", "~/dev", "~/git", "~/work",
                 "~/workspace", "~/ghq", "~/go/src", "~/source/repos"]
SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "target", "build", "dist", ".cache",
             ".tox", ".mypy_cache", ".gradle", "vendor", "Library", "AppData"}

# Tools that are already local (or are this toolkit's own local index) are never inspected.
LOCAL_TOOLS = re.compile(r"^(Read|Grep|Glob|Edit|Write|MultiEdit|NotebookEdit|LS|Task|Agent|TodoWrite|Skill|"
                         r"view|edit|create|str_replace|glob|grep|read|write|ls)$|codemap", re.I)
# Tool-name words (split on _ - . and a trailing "s" dropped) for calls with no local equivalent:
# issues, PRs, CI, history, people, chat. Those pass untouched, as does anything that writes.
NO_LOCAL_EQUIVALENT = {"issue", "pull", "pr", "comment", "review", "release", "workflow", "action", "job", "run",
                       "check", "deploy", "commit", "branche", "branch", "tag", "notification", "discussion", "gist",
                       "secret", "alert", "label", "milestone", "collaborator", "user", "team", "member", "star",
                       "slack", "message", "channel", "email", "mail", "calendar", "event", "ticket"}
WRITE_VERBS = {"create", "update", "delete", "remove", "push", "merge", "add", "write", "put", "post", "edit", "set",
               "close", "reopen", "assign", "dismiss", "approve", "submit", "upload", "send", "fork", "rename",
               "move", "trigger", "cancel", "rerun"}
URL_RE = re.compile(r"https?://[^\s'\"<>()`]+")
GH_API_RE = re.compile(r"\bgh\s+api\s+(?:-\S+\s+\S+\s+)*['\"]?/?repos/([\w.-]+)/([\w.-]+)/contents/([^\s'\"?]*)")
REPO_QUALIFIER_RE = re.compile(r"\brepo:([\w.-]+)/([\w.-]+)")
FETCH_CMD_RE = re.compile(r"\b(curl|wget|gh\s+api|http|xh|Invoke-WebRequest|iwr)\b")


# --------------------------------------------------------------------------- config

def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kickoff"


def cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "kickoff"


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def find_project_root(cwd: Path) -> Path:
    for d in (cwd, *cwd.parents):
        if (d / ".git").exists():
            return d
    return cwd


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def load_config(project: Path) -> dict:
    user = read_json(config_home() / "local-first.json")
    proj = read_json(project / ".kickoff" / "local-first.json")
    cfg = {"mode": user.get("mode", "once"), "roots": list(user.get("roots") or []),
           "docs": {}, "ignore_tools": list(user.get("ignore_tools") or [])}
    for key, val in (user.get("docs") or {}).items():
        if isinstance(val, str):
            cfg["docs"][key] = Path(os.path.expanduser(val))
    # A repository's own config is untrusted: it may tune the mode, ignore tools and map docs
    # that live inside the repository, but it cannot add scan roots or point outside itself.
    if proj.get("mode") in ("once", "strict", "off"):
        cfg["mode"] = proj["mode"]
    cfg["ignore_tools"] += [t for t in (proj.get("ignore_tools") or []) if isinstance(t, str)]
    for key, val in (proj.get("docs") or {}).items():
        if isinstance(val, str) and not os.path.isabs(os.path.expanduser(val)):
            p = project / val
            if within(p, project):
                cfg["docs"][key] = p
    env_mode = os.environ.get("KICKOFF_LOCAL_FIRST", "").strip().lower()
    if env_mode in ("once", "strict", "off", "0", "1"):
        cfg["mode"] = {"0": "off", "1": "once"}.get(env_mode, env_mode)
    return cfg


def scan_roots(cfg: dict, project: Path) -> list[tuple[Path, int]]:
    roots: list[tuple[Path, int]] = []
    extra = [r for r in os.environ.get("KICKOFF_LOCAL_ROOTS", "").split(os.pathsep) if r]
    for r in extra + cfg["roots"] + DEFAULT_ROOTS:
        path, depth = (r.get("path"), int(r.get("depth", 3))) if isinstance(r, dict) else (r, 3)
        if path:
            roots.append((Path(os.path.expanduser(path)), depth))
    roots.append((project.parent, 1))  # sibling checkouts next to the current project
    seen, out = set(), []
    for path, depth in roots:
        key = str(path)
        if key not in seen and path.is_dir():
            seen.add(key)
            out.append((path, depth))
    return out


# --------------------------------------------------------------------------- local clones

def git_dir(repo: Path) -> Path | None:
    dot = repo / ".git"
    if dot.is_dir():
        return dot
    if dot.is_file():  # worktree or submodule: "gitdir: <path>"
        try:
            line = dot.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if line.startswith("gitdir:"):
            gd = Path(line[7:].strip())
            return gd if gd.is_absolute() else (repo / gd).resolve()
    return None


def config_dir(gd: Path) -> Path:
    common = gd / "commondir"
    if common.is_file():
        try:
            c = Path(common.read_text(encoding="utf-8").strip())
            return c if c.is_absolute() else (gd / c).resolve()
        except OSError:
            pass
    return gd


def remote_slugs(repo: Path) -> list[str]:
    """owner/name for every remote URL, read from .git/config as plain text."""
    gd = git_dir(repo)
    if not gd:
        return []
    try:
        text = (config_dir(gd) / "config").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    slugs = []
    for url in re.findall(r"^\s*url\s*=\s*(\S+)", text, re.M):
        path = re.sub(r"^[\w+.-]+://[^/]+/", "", url)        # scheme://host/
        path = re.sub(r"^[^/@:]+@[^:/]+:", "", path)          # git@host:
        parts = [p for p in path.rstrip("/").split("/") if p]
        if len(parts) >= 2:
            name = parts[-1][:-4] if parts[-1].endswith(".git") else parts[-1]
            slugs.append(f"{parts[-2]}/{name}".lower())
    return slugs


def head_branch(repo: Path) -> str:
    gd = git_dir(repo)
    try:
        head = (gd / "HEAD").read_text(encoding="utf-8").strip() if gd else ""
    except OSError:
        return ""
    return head[len("ref: refs/heads/"):] if head.startswith("ref: refs/heads/") else head[:12]


def build_index(roots: list[tuple[Path, int]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    visited = 0
    for root, depth in roots:
        stack = [(root, 0)]
        while stack and visited < MAX_DIRS:
            d, level = stack.pop()
            visited += 1
            if (d / ".git").exists():
                for slug in remote_slugs(d):
                    index.setdefault(slug, [])
                    if str(d) not in index[slug]:
                        index[slug].append(str(d))
                continue  # do not descend into a repository
            if level >= depth:
                continue
            try:
                children = [c for c in d.iterdir()
                            if c.is_dir() and not c.is_symlink() and not c.name.startswith(".") and c.name not in SKIP_DIRS]
            except OSError:
                continue
            stack.extend((c, level + 1) for c in children)
    return index


def clone_index(cfg: dict, project: Path) -> dict[str, list[str]]:
    roots = scan_roots(cfg, project)
    key = hashlib.sha1(json.dumps([(str(p), d) for p, d in roots]).encode()).hexdigest()[:12]
    cache = cache_home() / f"local-first-index-{key}.json"
    data = read_json(cache)
    if data.get("built", 0) + INDEX_TTL > time.time() and isinstance(data.get("repos"), dict):
        index = data["repos"]
    else:
        index = build_index(roots)
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache.with_suffix(".tmp")
            tmp.write_text(json.dumps({"built": time.time(), "repos": index}), encoding="utf-8")
            tmp.replace(cache)
        except OSError:
            pass
    for slug in remote_slugs(project):  # the current project is always fresh
        index.setdefault(slug, [])
        if str(project) not in index[slug]:
            index[slug].insert(0, str(project))
    return index


# --------------------------------------------------------------------------- what is being fetched

def parse_github_url(url: str) -> dict | None:
    u = urlparse(url)
    host = (u.hostname or "").lower()
    parts = [unquote(p) for p in u.path.split("/") if p]
    if host in ("github.com", "www.github.com") and len(parts) >= 2:
        t = {"repo": f"{parts[0]}/{parts[1].removesuffix('.git')}".lower()}
        if len(parts) >= 4 and parts[2] in ("blob", "tree", "raw", "blame"):
            t["ref"], t["path"] = parts[3], "/".join(parts[4:])
        elif len(parts) > 2:
            return None  # issues, pulls, actions…: nothing local
        return t
    if host == "raw.githubusercontent.com" and len(parts) >= 4:
        return {"repo": f"{parts[0]}/{parts[1]}".lower(), "ref": parts[2], "path": "/".join(parts[3:])}
    if host == "api.github.com" and len(parts) >= 4 and parts[0] == "repos" and parts[3] == "contents":
        return {"repo": f"{parts[1]}/{parts[2]}".lower(), "path": "/".join(parts[4:])}
    return None


def package_from_url(url: str) -> str | None:
    u = urlparse(url)
    host = (u.hostname or "").lower()
    parts = [p for p in u.path.split("/") if p]
    if host.endswith("npmjs.com") and len(parts) >= 2 and parts[0] == "package":
        return "/".join(parts[1:3]) if parts[1].startswith("@") else parts[1]
    if host.endswith("pypi.org") and len(parts) >= 2 and parts[0] == "project":
        return parts[1]
    if host == "docs.rs" and parts:
        return parts[1] if parts[0] == "crate" and len(parts) > 1 else parts[0]
    if host == "crates.io" and len(parts) >= 2 and parts[0] == "crates":
        return parts[1]
    if host == "pkg.go.dev" and parts:
        return "/".join(parts).split("@")[0]
    return None


def flatten_strings(obj, out: list[str], depth: int = 0) -> list[str]:
    if depth > 4:
        return out
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            flatten_strings(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:50]:
            flatten_strings(v, out, depth + 1)
    return out


def targets_from_urls(urls: list[str]) -> list[dict]:
    targets = []
    for url in urls[:10]:
        url = url.rstrip(".,;")
        gh = parse_github_url(url)
        if gh:
            targets.append(gh)
            continue
        pkg = package_from_url(url)
        if pkg:
            targets.append({"library": pkg})
        targets.append({"url": url})
    return targets


def extract_targets(tool: str, args: dict) -> list[dict]:
    """Normalise a tool call into the things it would fetch: repo files, repo searches, libraries, URLs."""
    if tool in ("Bash", "bash", "shell", "powershell"):
        cmd = str(args.get("command") or args.get("cmd") or "")
        if not FETCH_CMD_RE.search(cmd):
            return []
        targets = [{"repo": f"{o}/{r}".lower(), "path": p} for o, r, p in GH_API_RE.findall(cmd)]
        return targets + targets_from_urls(URL_RE.findall(cmd))
    if tool in ("WebFetch", "web_fetch", "fetch"):
        return targets_from_urls([str(args.get("url") or "")])
    if tool in ("WebSearch", "web_search"):
        return [{"words": str(args.get("query") or "")}]  # only mapped docs can answer a free-text search

    name = tool.lower()
    words = {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in re.split(r"[^a-z0-9]+", name) if w}
    if words & WRITE_VERBS or words & NO_LOCAL_EQUIVALENT:
        return []
    targets: list[dict] = []
    owner, repo = args.get("owner"), args.get("repo") or args.get("repository") or args.get("repoName")
    if isinstance(repo, str) and "/" in repo.strip("/") and not owner:
        owner, repo = repo.strip("/").split("/")[:2]
    if isinstance(owner, str) and isinstance(repo, str) and owner and repo:
        t = {"repo": f"{owner}/{repo}".lower()}
        path = args.get("path") or args.get("file_path") or args.get("filePath")
        if isinstance(path, str):
            t["path"] = path.strip("/")
        ref = args.get("ref") or args.get("branch") or args.get("sha")
        if isinstance(ref, str):
            t["ref"] = ref
        targets.append(t)
    strings = flatten_strings(args, [])
    for s in strings:
        for o, r in REPO_QUALIFIER_RE.findall(s):
            targets.append({"repo": f"{o}/{r}".lower(), "search": True})
    for key in ("context7CompatibleLibraryID", "libraryId", "library_id"):
        lib = args.get(key)
        if isinstance(lib, str) and lib.count("/") >= 2:  # Context7 ids look like /owner/project[/version]
            o, r = lib.strip("/").split("/")[:2]
            targets.append({"repo": f"{o}/{r}".lower(), "docs": True})
            targets.append({"library": r})
    for key in ("libraryName", "library", "package", "packageName", "crate", "module"):
        lib = args.get(key)
        if isinstance(lib, str) and lib.strip():
            targets.append({"library": lib.strip()})
    targets += targets_from_urls([u for s in strings for u in URL_RE.findall(s)])
    if re.search(r"doc|wiki|librar|search|ask|query|lookup|resolve", name):
        targets.append({"words": " ".join(strings)[:4000]})
    return targets


# --------------------------------------------------------------------------- local resolution

def installed_package(project: Path, name: str) -> list[Path]:
    found: list[Path] = []
    lower = name.lower()
    py = re.sub(r"[-.]+", "_", lower)
    for base in (project, *list(project.parents)[:2]):
        nm = base / "node_modules" / name
        if nm.is_dir():
            found.append(nm)
        for venv in (".venv", "venv", "env"):
            for sp in (base / venv).glob("lib/python*/site-packages"):
                for cand in (sp / py, sp / lower):
                    if cand.is_dir():
                        found.append(cand)
                found += sorted(sp.glob(f"{py}-*.dist-info"))[:1]
            sp_win = base / venv / "Lib" / "site-packages" / py
            if sp_win.is_dir():
                found.append(sp_win)
        vend = base / "vendor" / name
        if vend.is_dir():
            found.append(vend)
        if found:
            break
    home = Path.home()
    for src in (home / ".cargo" / "registry" / "src").glob("*"):
        found += sorted(src.glob(f"{lower}-[0-9]*"), reverse=True)[:1]
    if "/" in name:
        gomod = home / "go" / "pkg" / "mod"
        found += sorted(gomod.glob(f"{name.lower()}@*"), reverse=True)[:1]
    return [p for i, p in enumerate(found) if p not in found[:i]]


def resolve(target: dict, index: dict[str, list[str]], cfg: dict, project: Path) -> list[tuple[str, str]]:
    """Return (local path, why) pairs that can stand in for the remote target."""
    hits: list[tuple[str, str]] = []
    if "repo" in target:
        for clone in index.get(target["repo"], []):
            root = Path(clone)
            branch = head_branch(root)
            on = f", on {branch}" if branch else ""
            path = target.get("path")
            if path:
                local = root / path
                if within(local, root) and local.exists():
                    hits.append((str(local), f"local clone of {target['repo']}{on}"))
                # A path the clone lacks means the local copy cannot answer: let the call through.
            else:
                what = "search it with Grep or codemap" if target.get("search") else "read it there"
                hits.append((str(root), f"local clone of {target['repo']}{on}; {what}"))
    if "library" in target:
        name = target["library"]
        if name in cfg["docs"] and cfg["docs"][name].exists():
            hits.append((str(cfg["docs"][name]), f"mapped docs for {name}"))
        for p in installed_package(project, name):
            hits.append((str(p), f"installed copy of {name} (source and README match the version you use)"))
    if "url" in target:
        for prefix, local in cfg["docs"].items():
            if prefix.startswith(("http://", "https://")) and target["url"].startswith(prefix):
                rest = unquote(target["url"][len(prefix):].split("#")[0].split("?")[0])
                cand = local / rest if rest else local
                if within(cand, local) and cand.exists():
                    hits.append((str(cand), f"local mirror of {prefix}"))
                elif local.exists():
                    hits.append((str(local), f"local mirror of {prefix}"))
    if "words" in target:
        text = target["words"].lower()
        for key, local in cfg["docs"].items():
            if not key.startswith(("http://", "https://")) and re.search(rf"(?<![\w-]){re.escape(key.lower())}(?![\w-])", text) \
                    and local.exists():
                hits.append((str(local), f"mapped docs for {key}"))
    return hits


# --------------------------------------------------------------------------- decision

def already_redirected(session: str, key: str) -> bool:
    """True if this target was redirected before in this session (then let it through)."""
    uid = os.getuid() if hasattr(os, "getuid") else "u"
    state = Path(tempfile.gettempdir()) / f"kickoff-local-first-{uid}"
    marker = state / hashlib.sha1(f"{session}|{key}".encode()).hexdigest()[:20]
    if marker.exists():
        return True
    try:
        state.mkdir(mode=0o700, exist_ok=True)
        marker.touch()
    except OSError:
        pass
    return False


def emit(fmt: str, reason: str | None) -> None:
    if fmt == "copilot":
        print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason} if reason else {}))
    elif reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))


def decide(data: dict) -> str | None:
    tool = str(data.get("tool_name") or data.get("toolName") or "")
    if not tool or LOCAL_TOOLS.search(tool):
        return None
    args = data.get("tool_input", data.get("toolArgs")) or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {"command": args}
    if not isinstance(args, dict):
        return None
    targets = extract_targets(tool, args)
    if not targets:
        return None

    project = find_project_root(Path(data.get("cwd") or os.getcwd()))
    cfg = load_config(project)
    if cfg["mode"] == "off" or any(re.search(p, tool) for p in cfg["ignore_tools"]):
        return None
    index = clone_index(cfg, project) if any("repo" in t for t in targets) else {}
    hits: list[tuple[str, str]] = []
    for t in targets:
        for h in resolve(t, index, cfg, project):
            if h[0] not in [x[0] for x in hits]:
                hits.append(h)
    if not hits:
        return None

    call_key = tool + json.dumps(args, sort_keys=True, default=str)
    session = str(data.get("session_id") or data.get("sessionId") or os.getppid())
    if cfg["mode"] != "strict" and already_redirected(session, call_key):
        return None
    lines = [f"local-first: `{tool}` would fetch something that is already on this machine. Use the local copy first:"]
    lines += [f"- {path}  ({why})" for path, why in hits[:MAX_SUGGESTIONS]]
    if cfg["mode"] == "strict":
        lines.append("Remote lookups with a local equivalent are blocked (strict mode). If the local copy is stale, "
                     "update it (e.g. `git -C <clone> pull`), or ask the user to set KICKOFF_LOCAL_FIRST=once.")
    else:
        lines.append("Read or Grep these (or use codemap on a clone). If they don't answer the question, for example "
                     "because you need a different version than the local copy, repeat the same call and it will be allowed.")
    return "\n".join(lines)


def main() -> None:
    fmt = sys.argv[sys.argv.index("--format") + 1] if "--format" in sys.argv else "claude"
    try:
        data = json.loads(sys.stdin.read() or "{}")
        reason = decide(data) if isinstance(data, dict) else None
    except Exception:
        reason = None
    emit(fmt, reason)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("{}" if "copilot" in sys.argv else "")
