#!/usr/bin/env python3
"""Token benchmark: codemap queries vs the usual grep-and-read workflow.

    python3 tests/bench_codemap.py path/to/repo:SymbolName [more:Symbols ...]
    python3 tests/bench_codemap.py --review path/to/repo:BASE..HEAD [...]

For each task it measures the tokens an agent would put into its context:

  locate-and-understand a symbol
    baseline: `git grep -n -w SYMBOL` (first 250 lines, like a capped Grep tool)
              + read the defining file + read the 2 files that use it most
    codemap:  def SYMBOL + refs SYMBOL + show SYMBOL
  orient in the repo (once per repo)
    baseline: `git ls-files` + README + the 3 most central files, read in full
    codemap:  overview + map --budget 1024

Tokens are estimated at 4 characters per token for both sides.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins" / "codemap" / "scripts"))
from codemap_core.cli import run_line  # noqa: E402
from codemap_core.util import est_tokens  # noqa: E402


def cm(repo: Path, line: str) -> str:
    out, err = io.StringIO(), io.StringIO()
    run_line(f"--repo {repo} --no-refresh {line}", out, err)
    return out.getvalue()


def read(repo: Path, rel: str) -> str:
    """Text of a file as an agent would read it; binary files (images, archives) count as nothing."""
    try:
        data = (repo / rel).read_bytes()
    except OSError:
        return ""
    if b"\0" in data[:8000]:
        return ""
    return data.decode("utf-8", errors="replace")


def baseline_symbol(repo: Path, name: str, def_file: str) -> int:
    grep = subprocess.run(["git", "grep", "-n", "-w", name], cwd=repo, capture_output=True, text=True).stdout
    lines = grep.splitlines()[:250]
    cost = est_tokens("\n".join(lines))
    cost += est_tokens(read(repo, def_file))
    users = Counter(l.split(":", 1)[0] for l in grep.splitlines() if not l.startswith(def_file + ":"))
    for f, _ in users.most_common(2):
        cost += est_tokens(read(repo, f))
    return cost


def review_bench(specs: list) -> int:
    """`--review repo:BASE..HEAD …`: AI-review pack vs full patch + changed files."""
    import json as _json
    print("| Repo | Range | Files | Baseline (patch + changed files) | Review pack (budget 8k) | Saved | Analysis time |")
    print("|---|---|---:|---:|---:|---:|---:|")
    for spec in specs:
        path, _, rng = spec.rpartition(":")
        repo = Path(path).resolve()
        base, _, head = rng.partition("..")
        cm(repo, "index --quiet")
        t0 = time.time()
        a = _json.loads(cm(repo, f"review --base {base} --head {head or 'HEAD'} --format json"))
        secs = round(time.time() - t0, 1)
        pack = cm(repo, f"review --base {base} --head {head or 'HEAD'} --format context --budget 8000")
        patch = subprocess.run(["git", "diff", base, head or "HEAD"], cwd=repo, capture_output=True, text=True).stdout
        files = sum(est_tokens(read(repo, f["path"])) for f in a["files"] if f["status"] != "D")
        base_t = est_tokens(patch) + files
        print(f"| {repo.name} | `{rng}` | {len(a['files'])} | {base_t:,} | {est_tokens(pack):,} | "
              f"{100 * (1 - est_tokens(pack) / max(base_t, 1)):.0f}% | {secs}s |")
    return 0


def main(argv: list) -> int:
    if not argv:
        print(__doc__)
        return 1
    if argv[0] == "--review":
        return review_bench(argv[1:])
    tasks: dict = {}
    for spec in argv:
        path, _, sym = spec.rpartition(":")
        tasks.setdefault(Path(path).resolve(), []).append(sym)
    rows, orient = [], []
    for repo, syms in tasks.items():
        t0 = time.time()
        cm(repo, "index --full --quiet")
        index_secs = round(time.time() - t0, 1)
        ov, mp = cm(repo, "overview"), cm(repo, "map --budget 1024")
        files = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True).stdout
        readme = next((read(repo, r) for r in ("README.md", "readme.md", "README.rst", "README") if (repo / r).exists()), "")
        line = next((l for l in ov.splitlines() if l.startswith("central files: ")), "")
        central = line[len("central files: "):].split(", ")[:3] if line else []
        base_orient = est_tokens(files) + est_tokens(readme) + sum(est_tokens(read(repo, c)) for c in central)
        orient.append((repo.name, base_orient, est_tokens(ov) + est_tokens(mp), index_secs))
        for s in syms:
            d = cm(repo, f"def {s}")
            first = d.splitlines()[0] if d.strip() else ""
            def_file = first.split(":", 1)[0] if ":" in first else ""
            base = baseline_symbol(repo, s, def_file)
            ours = est_tokens(d) + est_tokens(cm(repo, f"refs {s}")) + est_tokens(cm(repo, f"show {s}"))
            rows.append((repo.name, s, base, ours))

    print("| Repo | Orientation: baseline | codemap | Saved | Full index |")
    print("|---|---:|---:|---:|---:|")
    for name, b, o, secs in orient:
        print(f"| {name} | {b:,} | {o:,} | {100 * (1 - o / b):.0f}% | {secs}s |")
    print()
    print("| Repo | Symbol | Locate+understand: baseline | codemap | Saved |")
    print("|---|---|---:|---:|---:|")
    tb = to = 0
    for name, s, b, o in rows:
        tb += b
        to += o
        print(f"| {name} | `{s}` | {b:,} | {o:,} | {100 * (1 - o / max(b, 1)):.0f}% |")
    print(f"| **total** | | **{tb:,}** | **{to:,}** | **{100 * (1 - to / max(tb, 1)):.0f}%** |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
