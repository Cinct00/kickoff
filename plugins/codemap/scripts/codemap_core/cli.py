"""Command-line entry: `codemap <command> [args]`."""
from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

from . import VERSION
from .queries import Q, QueryError
from .store import Store
from .util import default_db_path, est_tokens, find_repo_root

COMMANDS_HELP = """commands (cheapest first — reach for these before grep or reading whole files):
  overview                     repo at a glance: languages, dirs, entry points, central files, packages (~250 tokens)
  map [--budget N] [--focus X] ranked signatures across the repo within a token budget (default 1024)
  tree [PATH] [--depth N]      directory summary with file counts and token sizes
  files PATTERN                list files by glob or substring
  find TERMS [--kind K]        search symbol names/signatures (camelCase and snake_case aware)
  def NAME                     where NAME is defined + signature, doc, base/sub classes
  outline PATH                 every symbol in a file with line ranges — instead of reading the file
  show SYMBOL|PATH:A-B         print exactly one symbol's source (or a line range)
  refs NAME                    who uses NAME, grouped by file with enclosing function
  callers NAME / callees SYM   call-graph style views
  deps PATH [--depth N]        what a file uses / what uses it
  impact PATH|SYMBOL           transitive dependents + tests to run before changing it
  tests PATH|SYMBOL            just the tests likely affected
  hierarchy TYPE               base classes and subclasses
  packages [NAME]              declared dependencies and where they are imported
  cycles                       import cycles
  sql "SELECT …" / schema      raw read-only SQL over the index
  index [--full]               build/update the index (queries also update it lazily)
  status / savings             index freshness; tokens saved so far
  mcp                          run as a single-tool MCP server over stdio
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="codemap", description="Token-efficient code map.", epilog=COMMANDS_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help="repository root (default: git root of the current directory)")
    ap.add_argument("--db", help="index database path (default: user cache)")
    ap.add_argument("--no-refresh", action="store_true", help="query the index as-is without checking for changes")
    ap.add_argument("--version", action="version", version=f"codemap {VERSION}")
    sub = ap.add_subparsers(dest="cmd")

    def add(name, *aliases, **kw):
        return sub.add_parser(name, aliases=list(aliases), **kw)

    p = add("index"); p.add_argument("--full", action="store_true"); p.add_argument("--quiet", action="store_true")
    add("overview", "ov")
    add("status")
    add("savings")
    add("schema")
    p = add("map"); p.add_argument("--budget", type=int, default=1024); p.add_argument("--focus", action="append", default=[])
    p.add_argument("--include-focus", action="store_true")
    p = add("tree"); p.add_argument("path", nargs="?", default=""); p.add_argument("--depth", type=int, default=2)
    p = add("files", "ls"); p.add_argument("pattern"); p.add_argument("--limit", type=int, default=50)
    p = add("find", "search"); p.add_argument("query", nargs="+"); p.add_argument("--kind"); p.add_argument("--path")
    p.add_argument("--limit", type=int, default=20)
    p = add("def", "define"); p.add_argument("name"); p.add_argument("--limit", type=int, default=10)
    p = add("outline", "ol"); p.add_argument("path"); p.add_argument("--no-doc", action="store_true")
    p = add("show", "cat"); p.add_argument("target"); p.add_argument("--context", "-C", type=int, default=0)
    p.add_argument("--max-lines", type=int, default=250); p.add_argument("-n", "--numbers", action="store_true")
    p = add("refs", "references"); p.add_argument("name"); p.add_argument("--limit", type=int, default=25)
    p = add("callers"); p.add_argument("name"); p.add_argument("--limit", type=int, default=30)
    p = add("callees"); p.add_argument("target"); p.add_argument("--limit", type=int, default=30)
    p = add("deps"); p.add_argument("path"); p.add_argument("--depth", type=int, default=1); p.add_argument("--limit", type=int, default=25)
    p = add("impact"); p.add_argument("target"); p.add_argument("--depth", type=int, default=2); p.add_argument("--limit", type=int, default=30)
    p = add("tests"); p.add_argument("target"); p.add_argument("--depth", type=int, default=2)
    p = add("hierarchy", "types"); p.add_argument("name")
    p = add("packages", "pkgs"); p.add_argument("name", nargs="?"); p.add_argument("--limit", type=int, default=40)
    p = add("cycles"); p.add_argument("--limit", type=int, default=10)
    p = add("sql"); p.add_argument("query"); p.add_argument("--limit", type=int, default=100)
    add("mcp")
    return ap


ALIASES = {"ov": "overview", "ls": "files", "search": "find", "define": "def", "ol": "outline", "cat": "show",
           "references": "refs", "types": "hierarchy", "pkgs": "packages"}
NO_LOG = {"index", "status", "savings", "schema", "sql", "mcp"}


def open_for(args) -> Store:
    root = Path(args.repo).resolve() if args.repo else find_repo_root(Path(os.environ.get("CODEMAP_REPO") or os.getcwd()))
    db = Path(args.db) if args.db else default_db_path(root)
    return Store(root, db)


def dispatch(args, out=sys.stdout, err=sys.stderr) -> int:
    cmd = ALIASES.get(args.cmd, args.cmd)
    if cmd is None:
        build_parser().print_help(out)
        return 0
    if cmd == "mcp":
        from .mcp import serve
        return serve(args)
    store = open_for(args)
    try:
        if cmd == "index":
            if args.full:
                store.db.execute("DELETE FROM files")
                for t in ("symbols", "symbols_fts", "bases", "idents", "imports", "edges", "deps"):
                    store.db.execute(f"DELETE FROM {t}")
            prog = None if args.quiet else (lambda i, n: print(f"  indexing {i}/{n}…", file=err, flush=True))
            st = store.refresh(lazy=False, force_ranks=True, progress=prog)
            if not args.quiet:
                print(f"indexed {st['files']} files (+{st['added']} new, {st['updated']} parsed, -{st['deleted']}) "
                      f"in {st['seconds']}s → {store.db_path}", file=out)
            return 0
        if not args.no_refresh and os.environ.get("CODEMAP_REFRESH", "1") != "0":
            first = store.meta("last_refresh") is None
            if first:
                print("codemap: building index for this repo (first run)…", file=err, flush=True)
            store.refresh(lazy=not first)
        q = Q(store)
        kw = {k: v for k, v in vars(args).items() if k not in ("cmd", "repo", "db", "no_refresh")}
        if cmd == "def":
            text, avoided = q.define(**kw)
        elif cmd == "find":
            kw["query"] = " ".join(kw["query"])
            text, avoided = q.find(**kw)
        elif cmd == "outline":
            kw["doc"] = not kw.pop("no_doc")
            text, avoided = q.outline(**kw)
        else:
            text, avoided = getattr(q, cmd)(**kw)
        print(text, file=out)
        if cmd not in NO_LOG:
            store.log_usage(cmd, est_tokens(text), avoided)
        return 0
    except QueryError as e:
        print(f"codemap: {e}", file=err)
        return 2
    finally:
        store.db.close()


def run_line(line: str, out, err) -> int:
    """Run a command line (as used by the MCP tool)."""
    try:
        argv = shlex.split(line)
    except ValueError as e:
        print(f"codemap: cannot parse command: {e}", file=err)
        return 2
    if argv and argv[0] == "codemap":
        argv = argv[1:]
    if argv and argv[0] == "mcp":
        print("codemap: 'mcp' is not available from inside the MCP tool", file=err)
        return 2
    try:
        args = build_parser().parse_args(argv)
    except SystemExit:
        print("codemap: invalid arguments. " + COMMANDS_HELP, file=err)
        return 2
    return dispatch(args, out, err)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        return 130
