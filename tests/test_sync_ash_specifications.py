from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sync_ash_specifications as sync


def write_bytes(root: Path, relative_path: str, value: bytes) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class AshSpecificationSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        write_bytes(self.root, "VERSION", b"2.0.23\n")
        write_bytes(
            self.root,
            "core/ash_pattern_engine/canonical/README.md",
            b"source documentation only\n",
        )
        write_bytes(
            self.root,
            "core/ash_pattern_engine/canonical/core/alpha.md",
            b"\xef\xbb\xbfalpha\r\nbeta\r",
        )
        write_bytes(
            self.root,
            "core/ash_pattern_engine/canonical/interfaces/zeta.md",
            b"zeta without final newline",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @property
    def source_root(self) -> Path:
        return self.root / sync.SOURCE_ROOT

    @property
    def mirror_root(self) -> Path:
        return self.root / sync.MIRROR_ROOT

    @property
    def manifest_path(self) -> Path:
        return self.root / sync.MANIFEST_PATH

    def test_write_creates_normalized_mirror_and_manifest_without_touching_source(self):
        source_before = tree_bytes(self.source_root)

        manifest = sync.write_synchronized_state(self.root)

        self.assertEqual(source_before, tree_bytes(self.source_root))
        self.assertEqual(b"alpha\nbeta\n", (self.mirror_root / "core/alpha.md").read_bytes())
        self.assertEqual(
            b"zeta without final newline",
            (self.mirror_root / "interfaces/zeta.md").read_bytes(),
        )
        self.assertFalse((self.mirror_root / "README.md").exists())
        self.assertEqual(["core/alpha.md", "interfaces/zeta.md"], [
            item["relative_path"] for item in manifest["files"]
        ])
        self.assertEqual(sync.TEXT_NORMALIZATION, manifest["text_normalization"])
        self.assertEqual(sync.AGGREGATE_ALGORITHM, manifest["aggregate_algorithm"])
        self.assertEqual(sync.CANONICAL_PROFILE, manifest["canonical_profile"])
        self.assertEqual(manifest, load_json(self.manifest_path))
        self.assertEqual(([], manifest), sync.synchronization_errors(self.root))

    def test_check_reports_missing_stale_and_extra_mirror_paths(self):
        sync.write_synchronized_state(self.root)
        (self.mirror_root / "core/alpha.md").unlink()
        write_bytes(self.root, "specs/interfaces/zeta.md", b"stale\n")
        write_bytes(self.root, "specs/extra.md", b"unexpected\n")

        errors, _manifest = sync.synchronization_errors(self.root)

        self.assertTrue(any("missing mirror path: specs/core/alpha.md" in error for error in errors))
        self.assertTrue(any("stale mirror path: specs/interfaces/zeta.md" in error for error in errors))
        self.assertTrue(any("extra mirror path: specs/extra.md" in error for error in errors))

    def test_write_rejects_extra_mirror_paths_before_any_output_changes(self):
        sync.write_synchronized_state(self.root)
        write_bytes(self.root, "specs/core/alpha.md", b"stale\n")
        write_bytes(self.root, "specs/extra.md", b"unexpected\n")
        before = tree_bytes(self.root)

        with self.assertRaises(sync.SynchronizationError) as raised:
            sync.write_synchronized_state(self.root)

        self.assertTrue(any("extra mirror path" in error for error in raised.exception.errors))
        self.assertEqual(before, tree_bytes(self.root))

    def test_check_compares_normalized_utf8_and_lf_content(self):
        expected = sync.write_synchronized_state(self.root)
        write_bytes(
            self.root,
            "specs/core/alpha.md",
            b"\xef\xbb\xbfalpha\r\nbeta\r\n",
        )

        self.assertEqual(([], expected), sync.synchronization_errors(self.root))

    def test_write_repairs_missing_stale_mirrors_and_manifest(self):
        sync.write_synchronized_state(self.root)
        (self.mirror_root / "core/alpha.md").unlink()
        write_bytes(self.root, "specs/interfaces/zeta.md", b"stale\n")
        changed_manifest = load_json(self.manifest_path)
        changed_manifest["aggregate_sha256"] = "0" * 64
        self.manifest_path.write_text(
            json.dumps(changed_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        expected = sync.write_synchronized_state(self.root)

        self.assertEqual(([], expected), sync.synchronization_errors(self.root))
        self.assertEqual(b"alpha\nbeta\n", (self.mirror_root / "core/alpha.md").read_bytes())
        self.assertEqual(
            b"zeta without final newline",
            (self.mirror_root / "interfaces/zeta.md").read_bytes(),
        )

    def test_manifest_drift_and_extra_fields_are_rejected(self):
        sync.write_synchronized_state(self.root)
        manifest = load_json(self.manifest_path)
        manifest["unexpected"] = True
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        errors, _expected = sync.synchronization_errors(self.root)

        self.assertTrue(any("manifest is stale" in error and "extra" in error for error in errors))

    def test_invalid_source_utf8_fails_before_outputs_are_changed(self):
        sync.write_synchronized_state(self.root)
        write_bytes(
            self.root,
            "core/ash_pattern_engine/canonical/core/alpha.md",
            b"\xffinvalid",
        )
        before = tree_bytes(self.root)

        with self.assertRaises(sync.SynchronizationError) as raised:
            sync.write_synchronized_state(self.root)

        self.assertTrue(any("not strict UTF-8" in error for error in raised.exception.errors))
        self.assertEqual(before, tree_bytes(self.root))

    def test_write_reports_mirror_file_directory_collision(self):
        collision = self.mirror_root / "core/alpha.md"
        collision.mkdir(parents=True)
        source_before = tree_bytes(self.source_root)

        with self.assertRaises(sync.SynchronizationError) as raised:
            sync.write_synchronized_state(self.root)

        self.assertTrue(
            any("unable to write synchronized ASH outputs" in error for error in raised.exception.errors)
        )
        self.assertEqual(source_before, tree_bytes(self.source_root))

    def test_canonical_readme_is_excluded_but_mirror_readme_is_extra(self):
        sync.write_synchronized_state(self.root)
        write_bytes(self.root, "specs/README.md", b"not generated\n")

        errors, _manifest = sync.synchronization_errors(self.root)

        self.assertTrue(any("extra mirror path: specs/README.md" in error for error in errors))
        with self.assertRaises(sync.SynchronizationError):
            sync.write_synchronized_state(self.root)

    def test_aggregate_is_order_independent_and_matches_declared_payload(self):
        files = [
            {"relative_path": "z.md", "sha256": "f" * 64},
            {"relative_path": "a.md", "sha256": "0" * 64},
        ]
        payload = b"a.md\0" + b"0" * 64 + b"\n" + b"z.md\0" + b"f" * 64 + b"\n"
        expected = hashlib.sha256(payload).hexdigest()

        self.assertEqual(expected, sync.aggregate_sha256(files))
        self.assertEqual(expected, sync.aggregate_sha256(reversed(files)))

    def test_cli_check_and_write_support_explicit_root(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            write_result = sync.main(["--write", "--root", str(self.root)])
            check_result = sync.main(["--check", "--root", str(self.root)])

        self.assertEqual(0, write_result)
        self.assertEqual(0, check_result)
        self.assertEqual("", stderr.getvalue())
        self.assertIn("WROTE: synchronized 2 ASH specification files", stdout.getvalue())
        self.assertIn("PASS: synchronized 2 ASH specification files", stdout.getvalue())


class LiveAshDependencyIdentityTests(unittest.TestCase):
    def test_live_manifest_is_exact_and_schema_valid(self):
        schema = load_json(ROOT / sync.SCHEMA_PATH)
        manifest = load_json(ROOT / sync.MANIFEST_PATH)
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(manifest),
            key=lambda error: list(error.absolute_path),
        )
        self.assertEqual([], [error.message for error in errors])
        self.assertEqual(sync.expected_manifest(ROOT), manifest)

    def test_live_source_and_mirror_sets_are_complete_and_synchronized(self):
        errors, manifest = sync.synchronization_errors(ROOT)
        self.assertEqual([], errors)
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertEqual(32, len(manifest["files"]))
        self.assertIn(
            "registries/fallback-policy-registry.md",
            [item["relative_path"] for item in manifest["files"]],
        )

    def test_realm_identity_mirror_preserves_vertex_alias_contract(self):
        canonical = (ROOT / sync.SOURCE_ROOT / "core/realm-identity.pseudo.md").read_bytes()
        mirror = (ROOT / sync.MIRROR_ROOT / "core/realm-identity.pseudo.md").read_bytes()
        canonical_normalized = sync.normalized_utf8_data(canonical, "canonical realm identity")
        mirror_normalized = sync.normalized_utf8_data(mirror, "mirrored realm identity")

        self.assertEqual(canonical_normalized, mirror_normalized)
        text = canonical_normalized.decode("utf-8")
        for required in ("StateIdentity", "vertex_id", "RealmIdentity", "realm_id", "512"):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
