"""Wiki publication refuses malformed mappings and preserves manual content."""
import importlib.util
import contextlib
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "prepare_wiki", Path(__file__).resolve().parents[1] / "scripts/github/prepare_wiki.py"
)
wiki = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wiki)


class WikiPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source"
        self.target = Path(self.temp.name) / "wiki"
        self.source.mkdir()
        self.target.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Jim Daley")
        self.run_git("config", "user.email", "94642455+flynn33@users.noreply.github.com")
        self.run_git("config", "core.autocrlf", "false")
        (self.source / ".github").mkdir()
        (self.source / "docs").mkdir()
        (self.source / "README.md").write_text("# Home\n\nCommitted source.\n", encoding="utf-8")
        (self.source / "docs/Roadmap.md").write_text("# Roadmap\n\nM3 is active.\n", encoding="utf-8")
        (self.target / "_Sidebar.md").write_bytes(b"## Manual navigation\r\n\r\n- [[Home]]\r\n")
        self.config = {"pages": [
            {"source": "README.md", "destination": "Home.md"},
            {"source": "docs/Roadmap.md", "destination": "Specification-Roadmap.md"}
        ]}
        self.commit_config()

    def run_git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], stderr=subprocess.STDOUT).decode().strip()

    def commit_config(self):
        (self.source / ".github/wiki-sync.json").write_text(json.dumps(self.config), encoding="utf-8")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "Update wiki test source")
        self.revision = self.run_git("rev-parse", "HEAD")

    def prepare(self, verify=False):
        return wiki.prepare(self.source, self.target, self.revision, ".github/wiki-sync.json", verify=verify)

    def test_missing_source_refuses_before_any_page_write(self):
        self.config["pages"].append({"source": "missing.md", "destination": "Missing.md"})
        self.commit_config()
        original = (self.target / "_Sidebar.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "Source is missing"):
            self.prepare()
        self.assertFalse((self.target / "Home.md").exists())
        self.assertEqual((self.target / "_Sidebar.md").read_bytes(), original)

    def test_duplicate_destination_is_case_insensitively_refused(self):
        self.config["pages"].append({"source": "README.md", "destination": "home.md"})
        self.commit_config()
        with self.assertRaisesRegex(ValueError, "Duplicate wiki destination"):
            self.prepare()
        self.assertFalse((self.target / "Home.md").exists())

    def test_source_and_destination_traversal_are_refused(self):
        original = dict(self.config["pages"][0])
        for field, bad in (("source", "../README.md"), ("destination", "../Escaped.md"),
                           ("source", "/README.md"), ("destination", "sub/Page.md"),
                           ("source", "docs\\Roadmap.md")):
            with self.subTest(field=field, path=bad):
                self.config["pages"][0] = dict(original, **{field: bad})
                self.commit_config()
                with self.assertRaises(ValueError):
                    self.prepare()
        self.assertFalse((self.target.parent / "Escaped.md").exists())
        self.assertFalse((self.target / "Home.md").exists())

    def test_links_are_pinned_with_correct_source_relative_paths(self):
        (self.source / "LICENSE").write_text("Terms.\n", encoding="utf-8")
        text = ('# Roadmap\n\n[License](../LICENSE#terms) [Directory](../docs/) '
                '[External](https://example.com/a) [Section](#local)\n'
                '[ref]: ../README.md "Readme"\n'
                '![Image](../LICENSE "caption")\n'
                '`[literal](../LICENSE)`\n'
                '```markdown\n[example](../missing.md)\n```\n')
        (self.source / "docs/Roadmap.md").write_text(text, encoding="utf-8")
        self.commit_config()
        self.prepare()
        result = (self.target / "Specification-Roadmap.md").read_text(encoding="utf-8")
        base = f"https://github.com/flynn33/yggdrasil-world-engine/blob/{self.revision}/"
        self.assertIn(f"[License]({base}LICENSE#terms)", result)
        self.assertIn(f"[ref]: {base}README.md \"Readme\"", result)
        self.assertIn(f'![Image]({base}LICENSE "caption")', result)
        self.assertIn(f"/tree/{self.revision}/docs", result)
        self.assertIn("[External](https://example.com/a) [Section](#local)", result)
        self.assertIn("`[literal](../LICENSE)`", result)
        self.assertIn("[example](../missing.md)", result)

    def test_escaping_link_refuses_before_writes(self):
        (self.source / "README.md").write_text("[Escape](../outside.md)\n", encoding="utf-8")
        self.commit_config()
        with self.assertRaisesRegex(ValueError, "Link escapes repository"):
            self.prepare()
        self.assertFalse((self.target / "Home.md").exists())

    def test_manual_pages_sidebar_and_idempotence_are_preserved(self):
        manual = b"# Owner manual\r\n\r\nOwner-maintained diagrams.\r\n"
        (self.target / "Manual.md").write_bytes(manual)
        original_sidebar = (self.target / "_Sidebar.md").read_bytes()
        first = self.prepare()
        self.assertEqual((self.target / "Manual.md").read_bytes(), manual)
        sidebar = (self.target / "_Sidebar.md").read_bytes()
        self.assertTrue(sidebar.startswith(original_sidebar))
        self.assertEqual(sidebar.count(b"[[Specification Roadmap]]"), 1)
        second = self.prepare()
        self.assertEqual(second["changed_paths"], [])
        self.assertEqual(first["generated_sha256"], second["generated_sha256"])
        self.assertEqual(first["preserved_unmapped_sha256"], second["preserved_unmapped_sha256"])
        self.assertEqual(self.prepare(verify=True)["changed_paths"], [])

    def test_uncommitted_sources_do_not_replace_pinned_source(self):
        (self.source / "README.md").write_text("# Dirty replacement\n", encoding="utf-8")
        self.prepare()
        self.assertIn("Committed source.", (self.target / "Home.md").read_text())
        self.assertNotIn("Dirty replacement", (self.target / "Home.md").read_text())

    def test_verify_detects_changed_generated_bytes_without_rewriting(self):
        self.prepare()
        page = self.target / "Home.md"
        page.write_text("Changed wiki output.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from pinned sources"):
            self.prepare(verify=True)
        self.assertEqual(page.read_text(), "Changed wiki output.\n")

    def test_missing_composite_source_is_not_partially_published(self):
        self.config["pages"].append({"source": "README.md", "sources": ["README.md", "gone.md"],
            "destination": "Composite.md", "kind": "composite", "title": "Composite"})
        self.commit_config()
        with self.assertRaisesRegex(ValueError, "Source is missing"):
            self.prepare()
        self.assertFalse((self.target / "Composite.md").exists())
        self.assertFalse((self.target / "Home.md").exists())

    def test_wiki_target_inside_source_repo_is_refused(self):
        inside = self.source / "wiki"
        inside.mkdir()
        (inside / "_Sidebar.md").write_text("- [[Home]]\n")
        with self.assertRaisesRegex(ValueError, "outside the source repository"):
            wiki.prepare(self.source, inside, self.revision, ".github/wiki-sync.json")

    def test_source_subdirectory_cannot_hide_product_directory_boundary(self):
        inside = self.source / "wiki"
        inside.mkdir()
        (inside / "_Sidebar.md").write_text("- [[Home]]\n")
        with self.assertRaisesRegex(ValueError, "repository top-level"):
            wiki.prepare(self.source / "docs", inside, self.revision, ".github/wiki-sync.json")

    def test_git_replacement_cannot_rewrite_pinned_source_identity(self):
        original_revision = self.revision
        (self.source / "README.md").write_text("# Replacement source\n", encoding="utf-8")
        self.commit_config()
        self.run_git("replace", original_revision, self.revision)
        self.revision = original_revision
        self.prepare()
        self.assertIn("Committed source.", (self.target / "Home.md").read_text())
        self.assertNotIn("Replacement source", (self.target / "Home.md").read_text())

    def test_invalid_cli_report_paths_refuse_before_wiki_mutation(self):
        existing = Path(self.temp.name) / "existing-report.json"
        existing.write_text("Preserved evidence.\n", encoding="utf-8")
        before = {path.name: path.read_bytes() for path in self.target.iterdir()}
        for report in (existing, self.target / "new-report.json",
                       Path(self.temp.name) / "missing-parent" / "report.json"):
            with self.subTest(report=report):
                arguments = ["prepare_wiki.py", "prepare", "--source-root", str(self.source),
                    "--wiki-root", str(self.target), "--source-revision", self.revision,
                    "--report", str(report)]
                with patch("sys.argv", arguments), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(wiki.main(), 2)
                self.assertEqual({path.name: path.read_bytes() for path in self.target.iterdir()}, before)
        self.assertEqual(existing.read_text(), "Preserved evidence.\n")

    def test_workflow_owner_authentication_refuses_another_account(self):
        text = (Path(__file__).resolve().parents[1] / ".github/workflows/wiki-sync.yml").read_text()
        code = next(line.strip()[len("python -c '"):-1] for line in text.splitlines()
                    if line.strip().startswith("python -c 'import json,os,sys,urllib.request;"))
        for login in ("another-account", "flynn33"):
            with self.subTest(login=login), patch.dict(os.environ, {"WIKI_OWNER_TOKEN": "synthetic-fixture-token"}), \
                    patch("urllib.request.urlopen", return_value=io.StringIO(json.dumps({"login": login}))):
                with self.assertRaises(SystemExit) as result:
                    exec(compile(code, "workflow-owner-authentication", "exec"), {})
                if login == "flynn33":
                    self.assertEqual(result.exception.code, 0)
                else:
                    self.assertEqual(result.exception.code, "Wiki publication requires the flynn33 account")

    def test_workflow_missing_owner_token_refuses_before_git(self):
        git_bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        bash = str(git_bash) if git_bash.is_file() else shutil.which("bash")
        if not bash:
            self.skipTest("Bash is unavailable for the hosted-script refusal probe")
        text = (Path(__file__).resolve().parents[1] / ".github/workflows/wiki-sync.yml").read_text()
        after = text.split("          set -euo pipefail\n", 1)[1]
        block = after.split("\n      - name: Preserve publication reports", 1)[0]
        script = "set -euo pipefail\ngit() { echo UNEXPECTED_GIT_CALL; exit 70; }\n" + \
            "\n".join(line[10:] if line.startswith("          ") else line for line in block.splitlines())
        environment = os.environ.copy()
        environment["WIKI_OWNER_TOKEN"] = ""
        result = subprocess.run([bash, "-c", script], env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Owner wiki credential is not configured", result.stdout)
        self.assertNotIn("UNEXPECTED_GIT_CALL", result.stdout)


if __name__ == "__main__":
    unittest.main()
