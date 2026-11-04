"""Regression tests for codemap. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

os.environ.setdefault("CODEMAP_BACKGROUND", "0")  # no detached re-index processes during tests

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins" / "codemap" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from codemap_core.cli import run_line  # noqa: E402
from codemap_core.mcp import handle  # noqa: E402
from codemap_core.util import est_tokens  # noqa: E402

FIXTURE = {
    "pkg/__init__.py": "",
    "pkg/models.py": '''
        """Domain models."""
        MAX_USERS = 100

        class Base:
            pass

        class User(Base):
            """A registered user."""
            def __init__(self, name: str):
                self.name = name

            def display_name(self) -> str:
                return self.name.title()
        ''',
    "pkg/service.py": '''
        from .models import User, MAX_USERS

        class UserService:
            def get_user(self, name: str) -> User:
                user = User(name)
                return user

            def count(self) -> int:
                return MAX_USERS
        ''',
    "tests/test_service.py": '''
        from pkg.service import UserService

        def test_get_user():
            assert UserService().get_user("a").display_name() == "A"
        ''',
    "web/tsconfig.json": '{ // comment\n "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["src/*"] }, }, }',
    "web/src/api/client.ts": '''
        import { formatUser } from "@/util/format";
        import axios from "axios";

        export interface ApiUser { id: number; name: string }

        export class ApiClient {
          constructor(private base: string) {}

          async fetchUser(id: number): Promise<ApiUser> {
            const res = await axios.get(`${this.base}/users/${id}`);
            return formatUser(res.data);
          }

          reset = (): void => {
            this.base = "";
          };
        }
        ''',
    "web/src/util/format.ts": '''
        // Turns raw payloads into users.
        export function formatUser(raw: any): any {
          return { id: raw.id, name: String(raw.name) };
        }

        export const shout = (s: string) => s.toUpperCase();
        ''',
    "go.mod": "module example.com/demo\n\ngo 1.22\n\nrequire github.com/spf13/pflag v1.0.5\n",
    "cmd/app/main.go": '''
        package main

        import (
          "fmt"
          "example.com/demo/internal/store"
        )

        func main() {
          s := store.New()
          fmt.Println(s.Get("k"))
        }
        ''',
    "internal/store/store.go": '''
        package store

        // Store keeps values in memory.
        type Store struct {
          data map[string]string
        }

        func New() *Store { return &Store{data: map[string]string{}} }

        func (s *Store) Get(k string) string {
          return s.data[k]
        }
        ''',
    "java/com/acme/Greeter.java": '''
        package com.acme;

        import com.acme.util.Strings;

        /** Greets people. */
        public class Greeter implements Speaker {
            private final String prefix;

            public Greeter(String prefix) { this.prefix = prefix; }

            @Override
            public String greet(String who) {
                Runnable r = new Runnable() { public void run() {} };
                return Strings.join(prefix, who);
            }
        }
        ''',
    "java/com/acme/util/Strings.java": '''
        package com.acme.util;

        public final class Strings {
            public static String join(String a, String b) { return a + " " + b; }
        }
        ''',
    "cs/Billing/Invoice.cs": '''
        using System;
        using Acme.Billing.Rules;

        namespace Acme.Billing
        {
            /// <summary>An invoice for a <see cref="Customer"/>.</summary>
            public class Invoice : IPayable
            {
                public decimal Total { get; set; }

                public decimal Due(DateTime now)
                {
                    return TaxRules.Apply(Total);
                }
            }
        }
        ''',
    "cs/Billing/Rules/TaxRules.cs": '''
        namespace Acme.Billing.Rules;

        public static class TaxRules
        {
            public static decimal Apply(decimal amount) => amount * 1.2m;
        }
        ''',
    "rs/Cargo.toml": '[package]\nname = "demo-core"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1"\n',
    "rs/src/lib.rs": '''
        pub mod parser;

        use crate::parser::Parser;

        pub struct Engine { parser: Parser }

        impl Engine {
            pub fn run(&self, input: &str) -> usize {
                self.parser.parse(input)
            }
        }
        ''',
    "rs/src/parser.rs": '''
        pub struct Parser;

        impl Parser {
            pub fn parse(&self, input: &str) -> usize { input.len() }
        }
        ''',
    "README.md": "# Demo\n\nSee [service](pkg/service.py).\n\n## Usage\n\nRun it.\n",
    "requirements.txt": "requests>=2\nPyYAML==6.0\n",
}


def write_fixture(root: Path) -> None:
    for rel, body in FIXTURE.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")


class CodemapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="codemap-test-"))
        cls.repo = cls.tmp / "repo"
        cls.repo.mkdir()
        write_fixture(cls.repo)
        subprocess.run(["git", "init", "-q"], cwd=cls.repo, check=True)
        os.environ["CODEMAP_CACHE"] = str(cls.tmp / "cache")
        cls.cm("index --quiet")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def cm(cls, line: str) -> str:
        out, err = io.StringIO(), io.StringIO()
        rc = run_line(f"--repo {cls.repo} {line}", out, err)
        if rc not in (0, None):
            raise AssertionError(f"codemap {line} -> rc {rc}: {err.getvalue()}")
        return out.getvalue()

    # ---------------------------------------------------------------- extraction
    def test_python_symbols_and_docs(self):
        out = self.cm("outline pkg/models.py")
        self.assertIn("class User(Base)", out)
        self.assertIn("def display_name(self) -> str", out)
        self.assertIn("A registered user.", out)
        self.assertIn("MAX_USERS = 100", out)

    def test_typescript_class_members(self):
        out = self.cm("outline web/src/api/client.ts")
        self.assertIn("export interface ApiUser", out)
        self.assertIn("export class ApiClient", out)
        self.assertIn("fetchUser(id: number): Promise<ApiUser>", out)
        self.assertIn("reset = (): void", out)

    def test_go_receiver_methods(self):
        out = self.cm("def Get")
        self.assertIn("internal/store/store.go", out)
        self.assertIn("Store.Get", out)
        self.assertIn("Store keeps values in memory", self.cm("def Store"))

    def test_java_anonymous_class_is_not_a_method(self):
        out = self.cm("outline java/com/acme/Greeter.java")
        self.assertIn("public String greet(String who)", out)
        self.assertNotIn("Runnable()", out.split("greet")[0])
        self.assertNotIn(" Runnable(", out)

    def test_csharp_namespace_members_and_doc(self):
        out = self.cm("outline cs/Billing/Invoice.cs")
        self.assertIn("public class Invoice : IPayable", out)
        self.assertIn("public decimal Due(DateTime now)", out)
        self.assertIn("An invoice for a Customer.", out)

    def test_rust_impl_methods(self):
        out = self.cm("outline rs/src/lib.rs")
        self.assertIn("impl Engine", out)
        self.assertIn("pub fn run(&self, input: &str) -> usize", out)

    def test_markdown_headings(self):
        out = self.cm("outline README.md")
        self.assertIn("# Demo", out)
        self.assertIn("## Usage", out)

    # ---------------------------------------------------------------- resolution
    def test_import_resolution_per_language(self):
        self.assertIn("pkg/models.py", self.cm("deps pkg/service.py"))
        self.assertIn("web/src/util/format.ts", self.cm("deps web/src/api/client.ts"))  # tsconfig alias
        self.assertIn("internal/store/store.go", self.cm("deps cmd/app/main.go"))  # go module path
        self.assertIn("java/com/acme/util/Strings.java", self.cm("deps java/com/acme/Greeter.java"))
        self.assertIn("cs/Billing/Rules/TaxRules.cs", self.cm("deps cs/Billing/Invoice.cs"))  # namespace
        self.assertIn("rs/src/parser.rs", self.cm("deps rs/src/lib.rs"))  # mod + crate::

    def test_external_packages(self):
        out = self.cm("deps web/src/api/client.ts")
        self.assertIn("axios", out)
        pk = self.cm("packages")
        self.assertIn("requests", pk)
        self.assertIn("pyyaml", pk.lower())
        self.assertIn("serde", pk)

    # ---------------------------------------------------------------- queries
    def test_find_ranks_exact_type_first(self):
        out = self.cm("find user service")
        self.assertTrue(out.splitlines()[1].strip().endswith("class UserService"), out)

    def test_refs_are_import_aware(self):
        out = self.cm("refs User")
        self.assertIn("pkg/service.py", out)
        self.assertIn("in UserService.get_user", out)

    def test_callers_and_impact(self):
        self.assertIn("UserService.get_user", self.cm("callers User"))
        imp = self.cm("impact pkg/models.py")
        self.assertIn("pkg/service.py", imp)
        self.assertIn("tests/test_service.py", imp)

    def test_hierarchy(self):
        self.assertIn("User", self.cm("hierarchy Base"))

    def test_show_prints_exact_symbol(self):
        out = self.cm("show UserService.count")
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("pkg/service.py:"))
        self.assertIn("def count(self) -> int:", lines[1])
        self.assertIn("return MAX_USERS", out)
        self.assertNotIn("get_user", out)

    def test_map_respects_budget(self):
        for budget in (60, 200, 800):
            out = self.cm(f"map --budget {budget}")
            self.assertLessEqual(est_tokens(out.strip()), budget, out)

    def test_overview_is_small(self):
        self.assertLess(est_tokens(self.cm("overview")), 400)

    def test_sql_is_read_only(self):
        self.assertIn("path", self.cm('sql "SELECT path FROM files LIMIT 1"'))
        out, err = io.StringIO(), io.StringIO()
        rc = run_line(f'--repo {self.repo} sql "DELETE FROM files"', out, err)
        self.assertEqual(rc, 2)

    def test_savings_logged(self):
        self.cm("outline pkg/models.py")
        self.assertIn("avoided", self.cm("savings"))

    # ---------------------------------------------------------------- freshness
    def test_incremental_update_and_delete(self):
        p = self.repo / "pkg" / "extra.py"
        p.write_text("from .models import User\n\ndef make_admin(u: User) -> User:\n    return u\n", encoding="utf-8")
        try:
            time.sleep(3.1)  # lazy refresh is throttled to one per 3 s
            self.assertIn("def make_admin", self.cm("find make_admin"))
            self.assertIn("pkg/extra.py", self.cm("refs User"))
        finally:
            p.unlink()
        time.sleep(3.1)
        self.assertIn("no symbols match", self.cm("find make_admin"))  # deleted file dropped from the index

    # ---------------------------------------------------------------- MCP
    def test_mcp_protocol(self):
        init = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(init["result"]["serverInfo"]["name"], "codemap")
        tools = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual([t["name"] for t in tools], ["codemap"])
        self.assertLess(len(json.dumps(tools)), 1200, "tool schema should stay small")
        res = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                      "params": {"name": "codemap", "arguments": {"cmd": f"--repo {self.repo} def UserService"}}})
        self.assertFalse(res["result"]["isError"])
        self.assertIn("class UserService", res["result"]["content"][0]["text"])
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_mcp_stdio_server(self):
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "codemap", "arguments": {"cmd": "overview"}}}]
        proc = subprocess.run([sys.executable, str(SCRIPTS / "codemap.py"), "mcp"], cwd=self.repo,
                              input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True,
                              timeout=60, env={**os.environ})
        replies = [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]
        self.assertEqual([r["id"] for r in replies], [1, 2])
        self.assertIn("code:", replies[1]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
