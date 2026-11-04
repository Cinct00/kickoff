"""Read declared dependencies from package manifests (no third-party parsers)."""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = None

MANIFEST_NAMES = {"package.json", "pyproject.toml", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
                  "build.gradle.kts", "Gemfile", "composer.json", "Pipfile", "setup.cfg"}


def is_manifest(path: str) -> bool:
    base = posixpath.basename(path)
    return (base in MANIFEST_NAMES or (base.startswith("requirements") and base.endswith(".txt"))
            or base.endswith((".csproj", ".fsproj", ".vbproj")) or base == "Directory.Packages.props")


def _req_name(spec: str) -> tuple[str, str]:
    spec = spec.split(";")[0].strip()
    m = re.match(r"^([A-Za-z0-9_.\-\[\]]+)\s*(.*)$", spec)
    if not m:
        return "", ""
    return re.sub(r"\[.*\]", "", m.group(1)), m.group(2).strip()


def parse_manifest(root: Path, path: str) -> list:
    """Return [(ecosystem, name, version, scope)] for a manifest on disk."""
    try:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return parse_manifest_text(path, text)


def parse_manifest_text(path: str, text: str) -> list:
    """Return [(ecosystem, name, version, scope)] for manifest content (e.g. from `git show`)."""
    base = posixpath.basename(path)
    out = []
    try:
        if base == "package.json":
            data = json.loads(text)
            for scope, label in (("dependencies", "prod"), ("devDependencies", "dev"), ("peerDependencies", "peer"),
                                 ("optionalDependencies", "optional")):
                for n, v in (data.get(scope) or {}).items():
                    out.append(("npm", n, str(v), label))
        elif base.startswith("requirements") and base.endswith(".txt"):
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    n, v = _req_name(line)
                    if n:
                        out.append(("pypi", n, v, "dev" if "dev" in base or "test" in base else "prod"))
        elif base == "pyproject.toml" and tomllib:
            data = tomllib.loads(text)
            for spec in (data.get("project") or {}).get("dependencies") or []:
                n, v = _req_name(spec)
                out.append(("pypi", n, v, "prod"))
            for grp, specs in ((data.get("project") or {}).get("optional-dependencies") or {}).items():
                for spec in specs:
                    n, v = _req_name(spec)
                    out.append(("pypi", n, v, grp))
            poetry = (data.get("tool") or {}).get("poetry") or {}
            for n, v in (poetry.get("dependencies") or {}).items():
                if n.lower() != "python":
                    out.append(("pypi", n, str(v if not isinstance(v, dict) else v.get("version", "")), "prod"))
            for grp, g in (poetry.get("group") or {}).items():
                for n, v in (g.get("dependencies") or {}).items():
                    out.append(("pypi", n, str(v if not isinstance(v, dict) else v.get("version", "")), grp))
        elif base == "go.mod":
            for m in re.finditer(r"^\s*(?:require\s+)?([\w.\-/]+\.[\w.\-/]+)\s+(v[\w.\-+]+)(\s*//\s*indirect)?", text, re.M):
                out.append(("go", m.group(1), m.group(2), "indirect" if m.group(3) else "prod"))
        elif base == "Cargo.toml" and tomllib:
            data = tomllib.loads(text)
            for scope in ("dependencies", "dev-dependencies", "build-dependencies"):
                for n, v in (data.get(scope) or {}).items():
                    out.append(("cargo", n, str(v if not isinstance(v, dict) else v.get("version", "")), scope.split("-")[0] if "-" in scope else "prod"))
        elif base.endswith((".csproj", ".fsproj", ".vbproj")) or base == "Directory.Packages.props":
            for m in re.finditer(r'<Package(?:Reference|Version)\s+Include="([^"]+)"(?:\s+Version="([^"]*)")?', text):
                out.append(("nuget", m.group(1), m.group(2) or "", "prod"))
        elif base == "pom.xml":
            for m in re.finditer(r"<dependency>(.*?)</dependency>", text, re.S):
                g = re.search(r"<groupId>([^<]+)</groupId>", m.group(1))
                a = re.search(r"<artifactId>([^<]+)</artifactId>", m.group(1))
                v = re.search(r"<version>([^<]+)</version>", m.group(1))
                s = re.search(r"<scope>([^<]+)</scope>", m.group(1))
                if a:
                    out.append(("maven", f"{g.group(1)}:{a.group(1)}" if g else a.group(1), v.group(1) if v else "", s.group(1) if s else "prod"))
        elif base.startswith("build.gradle"):
            for m in re.finditer(r"^\s*(\w+)\s*\(?\s*['\"]([\w.\-]+):([\w.\-]+)(?::([^'\"]+))?['\"]", text, re.M):
                out.append(("maven", f"{m.group(2)}:{m.group(3)}", m.group(4) or "", m.group(1)))
        elif base == "Gemfile":
            for m in re.finditer(r"^\s*gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?", text, re.M):
                out.append(("gem", m.group(1), m.group(2) or "", "prod"))
        elif base == "composer.json":
            data = json.loads(text)
            for scope in ("require", "require-dev"):
                for n, v in (data.get(scope) or {}).items():
                    out.append(("composer", n, str(v), "dev" if scope.endswith("dev") else "prod"))
    except (ValueError, KeyError, TypeError, AttributeError):
        return out
    return [o for o in out if o[1]]


PY_IMPORT_ALIASES = {
    "yaml": "pyyaml", "PIL": "pillow", "cv2": "opencv-python", "sklearn": "scikit-learn", "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil", "jwt": "pyjwt", "dotenv": "python-dotenv", "magic": "python-magic",
    "Crypto": "pycryptodome", "OpenSSL": "pyopenssl", "attr": "attrs", "google": "google-*", "docx": "python-docx",
}


def norm_pkg(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()
