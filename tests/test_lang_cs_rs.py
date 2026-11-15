"""C# and Rust structural parsers and resolution. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

os.environ.setdefault("CODEMAP_BACKGROUND", "0")  # no detached re-index processes during tests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "codemap" / "scripts"))

from codemap_core.cli import run_line  # noqa: E402
from codemap_core.extract import extract  # noqa: E402

CS = r'''
using System;
using System.Collections.Generic;

namespace Acme.Orders;

/// <summary>An order placed by a <see cref="Customer"/>.</summary>
[Serializable]
public sealed partial class Order : EntityBase, IComparable<Order>
{
    public const int MaxLines = 100;
    private readonly Dictionary<string, object> _meta = new Dictionary<string, object>(), _extra = new();
    public static readonly string A = "a", B = @"b""{";

    public Guid Id { get; init; } = Guid.NewGuid();
    public decimal Total => Lines.Sum(l => l.Price);
    public string this[int index] => _items[index];
    public event EventHandler? Changed;
    public event EventHandler Saved { add { } remove { } }

    public Order(Guid id) : base(id) { Id = id; }
    ~Order() { }

    public int CompareTo(Order? other) => Total.CompareTo(other?.Total);
    void IDisposable.Dispose() { }
    public T Map<T>(Func<Order, T> f) where T : class, new() { return f(this); }
    public static Order operator +(Order a, Order b) => a;
    partial void OnSaved();
    public (int Count, decimal Sum) Stats() { var s = $"{{x}} {(Total > 0 ? "}" : "{")}"; return (1, 2m); }
    private string Raw() => """ { not a block """;

#if NET8_0
    public void OnlyNet8() { }
#else
    public void OnlyOld() { }
#endif

    public delegate void OrderHandler(Order o);
    public record Line(string Sku, decimal Price);
    public ref struct Cursor { public int Pos; }
}

public interface IOrderRepository
{
    Order? Find(Guid id);
    IAsyncEnumerable<Order> AllAsync();
    int Count { get; }
}

public enum Status { Open, Closed }
'''

RS = r'''
//! Crate docs.
use crate::store::{Store, kinds::{Kind, Other as O}};
use super::helpers;

/// Parses things.
#[derive(Debug, Clone)]
pub struct Parser<'a> { input: &'a str }

pub struct Unit;
pub struct Pair(pub u32, pub u32);

pub enum Token { Word(String), Num(i64) }

pub trait Visitor: Send + Sync {
    type Output;
    const LIMIT: usize;
    fn visit(&mut self, t: &Token) -> Self::Output;
    fn done(&self) -> bool { true }
}

impl<'a> Parser<'a> {
    pub const fn new(input: &'a str) -> Self { Parser { input } }
    pub async fn parse(&self) -> Vec<Token> {
        fn helper(c: char) -> bool { c == '{' }
        let s = r#"fn fake() { "#;
        /* outer /* nested } */ */
        vec![]
    }
}

impl<T: Clone> Visitor for Wrapper<T> where T: Send {
    type Output = ();
    const LIMIT: usize = 3;
    fn visit(&mut self, _t: &Token) {}
}

pub(crate) type Result<T> = std::result::Result<T, Error>;
pub static mut COUNTER: u32 = 0;
pub const MAX: usize = 10;

macro_rules! make_fn { ($n:ident) => { fn $n() {} }; }
make_fn!(generated);

pub mod inner { pub fn f() {} }
mod external;
unsafe extern "C" fn callback(x: i32) -> i32 { x }

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn it_works() {}
}
'''


def names(facts, kind=None):
    return {(s.kind, s.qualname) for s in facts.symbols if kind is None or s.kind == kind}


class CSharpParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = extract(textwrap.dedent(CS), "csharp")
        cls.q = {s.qualname: s for s in cls.f.symbols}

    def test_members(self):
        n = names(self.f)
        for expected in [("namespace", "Acme.Orders"), ("class", "Acme.Orders.Order"), ("const", "Acme.Orders.Order.MaxLines"),
                         ("field", "Acme.Orders.Order._meta"), ("field", "Acme.Orders.Order._extra"),
                         ("field", "Acme.Orders.Order.A"), ("field", "Acme.Orders.Order.B"),
                         ("property", "Acme.Orders.Order.Id"), ("property", "Acme.Orders.Order.Total"),
                         ("indexer", "Acme.Orders.Order.this"), ("field", "Acme.Orders.Order.Changed"),
                         ("event", "Acme.Orders.Order.Saved"), ("method", "Acme.Orders.Order.Order"),
                         ("method", "Acme.Orders.Order.CompareTo"), ("method", "Acme.Orders.Order.Dispose"),
                         ("method", "Acme.Orders.Order.Map"), ("method", "Acme.Orders.Order.OnSaved"),
                         ("method", "Acme.Orders.Order.Stats"), ("method", "Acme.Orders.Order.Raw"),
                         ("delegate", "Acme.Orders.Order.OrderHandler"), ("record", "Acme.Orders.Order.Line"),
                         ("struct", "Acme.Orders.Order.Cursor"), ("interface", "Acme.Orders.IOrderRepository"),
                         ("method", "Acme.Orders.IOrderRepository.Find"), ("method", "Acme.Orders.IOrderRepository.AllAsync"),
                         ("property", "Acme.Orders.IOrderRepository.Count"), ("enum", "Acme.Orders.Status")]:
            self.assertIn(expected, n)

    def test_no_phantoms(self):
        n = {q for _, q in names(self.f)}
        self.assertNotIn("Acme.Orders.Order.object", n, "generic initializer must not split into declarators")
        self.assertNotIn("Acme.Orders.Order.OnlyOld", n, "only the first #if branch is kept")
        self.assertIn("Acme.Orders.Order.OnlyNet8", n)

    def test_extents_docs_bases(self):
        order = self.q["Acme.Orders.Order"]
        self.assertEqual(order.bases, ["EntityBase", "IComparable"])
        self.assertEqual(order.doc, "An order placed by a Customer.")
        self.assertGreater(order.end_line, self.q["Acme.Orders.Order.Cursor"].line)
        self.assertTrue(self.q["Acme.Orders.Order.Stats"].signature.startswith("public (int Count, decimal Sum) Stats()"))
        self.assertTrue(self.q["Acme.Orders.Order.Map"].signature.endswith("where T : class, new()"))
        self.assertEqual(self.f.package, "Acme.Orders")


class RustParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = extract(textwrap.dedent(RS), "rust")
        cls.q = {s.qualname: s for s in cls.f.symbols if s.kind != "impl"}
        cls.impl = {s.qualname: s for s in cls.f.symbols if s.kind == "impl"}

    def test_items(self):
        n = names(self.f)
        for expected in [("struct", "Parser"), ("struct", "Unit"), ("struct", "Pair"), ("enum", "Token"),
                         ("trait", "Visitor"), ("type", "Visitor.Output"), ("const", "Visitor.LIMIT"),
                         ("method", "Visitor.visit"), ("method", "Visitor.done"), ("impl", "Parser"),
                         ("method", "Parser.new"), ("method", "Parser.parse"), ("function", "Parser.parse.helper"),
                         ("impl", "Wrapper"), ("method", "Wrapper.visit"), ("type", "Result"), ("const", "COUNTER"),
                         ("const", "MAX"), ("macro", "make_fn"), ("module", "inner"), ("function", "inner.f"),
                         ("module", "external"), ("function", "callback"), ("module", "tests"), ("function", "tests.it_works")]:
            self.assertIn(expected, n)

    def test_no_phantoms(self):
        n = {q for _, q in names(self.f)}
        self.assertNotIn("fake", " ".join(n), "fn inside a raw string is not a definition")
        self.assertFalse(any(q.endswith("$n") or q == "generated" for q in n), "macro templates/invocations are opaque")

    def test_bases_docs_imports(self):
        self.assertEqual(self.impl["Wrapper"].bases, ["Visitor"])
        self.assertEqual(self.q["Visitor"].bases, ["Send", "Sync"])
        self.assertEqual(self.q["Parser"].doc, "Parses things.")
        raws = [(i.raw, i.level) for i in self.f.imports]
        self.assertIn(("crate::store::Store", 0), raws)
        self.assertIn(("crate::store::kinds::Kind", 0), raws)
        self.assertIn(("crate::store::kinds::Other", 0), raws)
        self.assertIn(("super", 1), raws, "`use super::*` inside `mod tests` is the file itself")
        self.assertIn(("external", 0), raws, "`mod external;` declares a file module")


class ResolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="codemap-csrs-"))
        r = cls.repo = cls.tmp / "repo"
        files = {
            "App/App.csproj": '<Project><ItemGroup><Using Include="Acme.Shared" /></ItemGroup></Project>',
            "App/GlobalUsings.cs": "global using Acme.Util;",
            "App/Orders/Order.cs": "namespace Acme.Orders;\npublic class Order { public Money Price; public Clock C; public Ident Key; }",
            "App/Orders/Money.cs": "namespace Acme.Orders;\npublic record Money(decimal Amount);",
            "App/Orders/Unused.cs": "namespace Acme.Orders;\npublic class Unused {}",
            "App/Util/Clock.cs": "namespace Acme.Util;\npublic class Clock {}",
            "App/Shared/Ident.cs": "namespace Acme.Shared;\npublic struct Ident {}",
            "App/Billing/Invoice.cs": "using Acme.Orders;\nnamespace Acme.Billing;\npublic class Invoice { Order o; }",
            "Cargo.toml": '[package]\nname = "tool"\n[[bin]]\nname = "tool"\npath = "crates/core/main.rs"\n',
            "crates/core/main.rs": "mod flags;\nuse crate::flags::defs::Mode;\nfn main() {}",
            "crates/core/flags/mod.rs": "pub mod defs;",
            "crates/core/flags/defs.rs": "pub enum Mode { A }\n#[cfg(test)]\nmod tests { use super::Mode; }",
        }
        for rel, body in files.items():
            p = r / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=r, check=True)
        os.environ["CODEMAP_CACHE"] = str(cls.tmp / "cache")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def deps(self, path):
        out, err = io.StringIO(), io.StringIO()
        run_line(f"--repo {self.repo} deps {path}", out, err)
        return out.getvalue().split("used by")[0]

    def test_csharp_scope(self):
        d = self.deps("App/Orders/Order.cs")
        self.assertIn("App/Orders/Money.cs", d, "same namespace, no using needed")
        self.assertIn("App/Util/Clock.cs", d, "global using in GlobalUsings.cs")
        self.assertIn("App/Shared/Ident.cs", d, "<Using Include> in the .csproj")
        self.assertNotIn("Unused.cs", d, "only files defining a type actually used")
        inv = self.deps("App/Billing/Invoice.cs")
        self.assertIn("App/Orders/Order.cs", inv)
        self.assertNotIn("Money.cs", inv)

    def test_rust_modules(self):
        self.assertIn("crates/core/flags/defs.rs", self.deps("crates/core/main.rs"), "crate root found at crates/core")
        self.assertIn("crates/core/flags/mod.rs", self.deps("crates/core/main.rs"), "`mod flags;`")


if __name__ == "__main__":
    unittest.main()
