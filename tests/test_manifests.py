"""Unit tests for codemap's dependency-manifest parsing. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "codemap" / "scripts"))

from codemap_core.manifests import is_manifest, norm_pkg, parse_manifest, parse_manifest_text, tomllib  # noqa: E402


def deps(path, text):
    return {(eco, name, ver, scope) for eco, name, ver, scope in parse_manifest_text(path, text)}


class ManifestTest(unittest.TestCase):
    def test_is_manifest(self):
        for p in ("package.json", "a/b/pyproject.toml", "go.mod", "requirements-dev.txt", "src/App.csproj",
                  "Directory.Packages.props", "build.gradle.kts", "Gemfile"):
            self.assertTrue(is_manifest(p), p)
        for p in ("package-lock.json", "README.md", "requirements.md", "src/app.py"):
            self.assertFalse(is_manifest(p), p)

    def test_package_json_scopes(self):
        got = deps("web/package.json", '{"dependencies": {"react": "^18.3.1"}, "devDependencies": {"vitest": "1.6.0"}}')
        self.assertEqual(got, {("npm", "react", "^18.3.1", "prod"), ("npm", "vitest", "1.6.0", "dev")})

    def test_requirements_txt(self):
        text = "# comment\n-r base.txt\nrequests==2.31.0\nuvicorn[standard]>=0.30 ; python_version>'3.8'\n\nflask\n"
        got = deps("requirements.txt", text)
        self.assertEqual(got, {("pypi", "requests", "==2.31.0", "prod"), ("pypi", "uvicorn", ">=0.30", "prod"),
                               ("pypi", "flask", "", "prod")})
        self.assertEqual({d[3] for d in deps("requirements-test.txt", "pytest\n")}, {"dev"})

    @unittest.skipUnless(tomllib, "tomllib needs Python 3.11+")
    def test_pyproject_and_cargo(self):
        py = ('[project]\ndependencies = ["httpx>=0.27"]\n[project.optional-dependencies]\ndocs = ["mkdocs"]\n'
              '[tool.poetry.dependencies]\npython = "^3.11"\nrich = {version = "13.7"}\n')
        self.assertEqual(deps("pyproject.toml", py), {("pypi", "httpx", ">=0.27", "prod"), ("pypi", "mkdocs", "", "docs"),
                                                       ("pypi", "rich", "13.7", "prod")})
        cargo = '[dependencies]\nserde = { version = "1.0", features = ["derive"] }\n[dev-dependencies]\ninsta = "1.39"\n'
        self.assertEqual(deps("Cargo.toml", cargo), {("cargo", "serde", "1.0", "prod"), ("cargo", "insta", "1.39", "dev")})

    def test_go_mod(self):
        text = "module x\n\nrequire (\n\tgithub.com/spf13/cobra v1.8.1\n\tgolang.org/x/sys v0.21.0 // indirect\n)\n"
        self.assertEqual(deps("go.mod", text), {("go", "github.com/spf13/cobra", "v1.8.1", "prod"),
                                                ("go", "golang.org/x/sys", "v0.21.0", "indirect")})

    def test_nuget_maven_gradle_gem_composer(self):
        self.assertIn(("nuget", "Newtonsoft.Json", "13.0.3", "prod"),
                      deps("App.csproj", '<PackageReference Include="Newtonsoft.Json" Version="13.0.3" />'))
        pom = ("<dependency><groupId>junit</groupId><artifactId>junit</artifactId><version>4.13</version>"
               "<scope>test</scope></dependency>")
        self.assertEqual(deps("pom.xml", pom), {("maven", "junit:junit", "4.13", "test")})
        self.assertEqual(deps("build.gradle", "implementation 'com.google.guava:guava:33.0.0-jre'\n"),
                         {("maven", "com.google.guava:guava", "33.0.0-jre", "implementation")})
        self.assertEqual(deps("Gemfile", "gem 'rails', '7.1.3'\n"), {("gem", "rails", "7.1.3", "prod")})
        self.assertEqual(deps("composer.json", '{"require-dev": {"phpunit/phpunit": "^10"}}'),
                         {("composer", "phpunit/phpunit", "^10", "dev")})

    def test_malformed_input_never_raises(self):
        self.assertEqual(parse_manifest_text("package.json", "{not json"), [])
        self.assertEqual(parse_manifest_text("composer.json", "[]"), [])
        self.assertEqual(parse_manifest_text("unknown.cfg", "anything"), [])

    def test_parse_manifest_reads_from_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "requirements.txt").write_text("attrs==23.2.0\n")
            self.assertEqual(parse_manifest(Path(tmp), "requirements.txt"), [("pypi", "attrs", "==23.2.0", "prod")])
            self.assertEqual(parse_manifest(Path(tmp), "missing/package.json"), [])

    def test_norm_pkg(self):
        self.assertEqual(norm_pkg("Python_Dateutil"), "python-dateutil")
        self.assertEqual(norm_pkg("zope.interface"), "zope-interface")


if __name__ == "__main__":
    unittest.main()
