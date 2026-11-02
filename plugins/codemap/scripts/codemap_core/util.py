"""Shared helpers: repo discovery, file listing, language detection, token estimates."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

LANG_BY_EXT = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".go": "go",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala",
    ".cs": "csharp",
    ".rs": "rust",
    ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp", ".hxx": "cpp",
    ".php": "php", ".rb": "ruby", ".swift": "swift",
    ".md": "markdown", ".mdx": "markdown",
}
CODE_LANGS = {l for l in LANG_BY_EXT.values() if l != "markdown"}

# Paths that are generated, vendored or otherwise noise for navigation.
SKIP_DIR_PARTS = {
    "node_modules", ".git", ".hg", ".svn", "vendor", "dist", "build", "out", "target", "bin", "obj",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache", ".next", ".nuxt",
    "coverage", ".gradle", ".idea", ".vscode", "Pods", "DerivedData", ".terraform", "site-packages",
}
SKIP_SUFFIXES = (
    ".min.js", ".min.css", ".map", ".lock", "-lock.json", ".lock.json", ".pb.go", "_pb2.py", ".g.cs",
    ".designer.cs", ".generated.ts", ".d.ts.map",
)
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf", ".zip", ".gz", ".tgz", ".bz2", ".xz",
    ".7z", ".jar", ".war", ".class", ".so", ".dll", ".dylib", ".exe", ".o", ".a", ".pyc", ".woff", ".woff2",
    ".ttf", ".otf", ".eot", ".mp3", ".mp4", ".mov", ".avi", ".wav", ".db", ".sqlite", ".bin", ".pkl", ".npy",
    ".parquet", ".onnx", ".pt", ".h5", ".psd", ".sketch", ".fig",
}
MAX_FILE_BYTES = int(os.environ.get("CODEMAP_MAX_FILE_BYTES", 1_000_000))

TEST_RE = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs|testing)/|(^|/)[^/]*[._-][Tt]ests?/|(^|/)[^/]*[a-z]Tests/"
    r"|(^|/)test_[^/]+\.py$|_test\.(py|go)$|\.(test|spec)\.[jt]sx?$"
    r"|(Test|Tests|Spec|IT)\.(java|kt|cs|scala)$|_spec\.rb$|Tests?\.swift$",
)


def est_tokens(text_or_len) -> int:
    """Rough token estimate (~4 chars per token for code and English)."""
    n = text_or_len if isinstance(text_or_len, int) else len(text_or_len)
    return (n + 3) // 4


def fmt_tokens(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def is_test_path(path: str) -> bool:
    return bool(TEST_RE.search(path))


def lang_of(path: str) -> str | None:
    p = path.lower()
    for ext, lang in LANG_BY_EXT.items():
        if p.endswith(ext):
            return lang
    return None


def git(args: list[str], cwd: Path) -> str | None:
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return proc.stdout if proc.returncode == 0 else None


def find_repo_root(start: Path) -> Path:
    out = git(["rev-parse", "--show-toplevel"], start)
    if out and out.strip():
        return Path(out.strip()).resolve()
    return start.resolve()


def cache_dir() -> Path:
    if os.environ.get("CODEMAP_CACHE"):
        base = Path(os.environ["CODEMAP_CACHE"])
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "ai-toolkit" / "codemap"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ai-toolkit" / "codemap"
    base.mkdir(parents=True, exist_ok=True)
    return base


def default_db_path(root: Path) -> Path:
    if os.environ.get("CODEMAP_DB"):
        return Path(os.environ["CODEMAP_DB"])
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", root.name)[:40] or "repo"
    digest = hashlib.sha1(str(root).encode()).hexdigest()[:10]
    return cache_dir() / f"{slug}-{digest}.db"


def _skip(path: str) -> bool:
    parts = path.split("/")
    if any(p in SKIP_DIR_PARTS for p in parts[:-1]):
        return True
    low = path.lower()
    if low.endswith(SKIP_SUFFIXES):
        return True
    dot = low.rfind(".")
    return dot != -1 and low[dot:] in BINARY_EXTS


def list_files(root: Path) -> list[str]:
    """Repo-relative POSIX paths of files worth indexing (respects .gitignore when in git)."""
    out = git(["ls-files", "-z", "--cached", "--others", "--exclude-standard"], root)
    if out is not None:
        paths = [p for p in out.split("\0") if p]
    else:
        paths = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS and not d.startswith(".")]
            rel = os.path.relpath(dirpath, root)
            for f in filenames:
                paths.append(f if rel == "." else f"{rel}/{f}".replace(os.sep, "/"))
    seen = set()
    result = []
    for p in paths:
        p = p.replace("\\", "/")
        if p in seen or _skip(p):
            continue
        seen.add(p)
        result.append(p)
    return sorted(result)


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8000]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "surrogatepass")).hexdigest()


def split_words(name: str) -> str:
    """'getUserById' / 'get_user_by_id' -> 'get user by id' (for search)."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return re.sub(r"[_\-.:$]+", " ", s).lower().strip()
