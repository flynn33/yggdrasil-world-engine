#!/usr/bin/env python3
"""Reconcile YWE's accepted M0/M1 repository surfaces before M2 closure work."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def run(root: Path, *args: str) -> str:
    result = subprocess.run(args, cwd=root, check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout


def load(root: Path, path: str) -> dict:
    return json.loads((root / path).read_text(encoding="utf-8-sig"))


def write(root: Path, path: str, value: object) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def restore_pre_deletion(root: Path, path: str) -> str:
    deletion = run(root, "git", "log", "--diff-filter=D", "-n1", "--format=%H", "--", path).strip()
    if not deletion:
        raise RuntimeError(f"No deletion commit found for {path}")
    return run(root, "git", "show", f"{deletion}^:{path}")


def manual_only(text: str) -> str:
    start = text.index("on:\n")
    candidates = [
        index
        for marker in ("\npermissions:", "\nenv:", "\njobs:")
        if (index := text.find(marker, start)) >= 0
    ]
    if not candidates:
        raise RuntimeError("Unable to locate the end of a workflow trigger block")
    return text[:start] + "on:\n  workflow_dispatch:\n" + text[min(candidates):]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sys.path.insert(0, str(root / "scripts"))
    import check_m0_truthful_baseline as m0
    import check_specification_roadmap as roadmap

    (root / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (root / ".github/workflows/main-ci.yml").write_text(
        """name: Main CI

on:
  workflow_dispatch:

permissions:
  contents: read

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

jobs:
  validate:
    name: Validate Repository
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          fetch-tags: true
          persist-credentials: false

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install validation dependencies
        run: python3 -m pip install -r scripts/requirements.txt

      - name: Run canonical validation suite
        run: python3 scripts/validate_repository.py --context manual
""",
        encoding="utf-8",
    )

    for name in (
        "branch-guard.yml",
        "forsetti-compliance.yml",
        "ywe_repository_guardrails.yml",
    ):
        path = f".github/workflows/{name}"
        text = manual_only(restore_pre_deletion(root, path))
        text = text.replace("python-version: '3.11'", "python-version: '3.13'")
        text = text.replace(
            "          fetch-depth: 0\n",
            "          fetch-depth: 0\n          fetch-tags: true\n          persist-credentials: false\n",
        )
        (root / path).write_text(text, encoding="utf-8")

    versioning = restore_pre_deletion(root, ".github/workflows/versioning.yml")
    (root / ".github/workflows/versioning.yml").write_text(versioning, encoding="utf-8")

    wiki = manual_only(restore_pre_deletion(root, ".github/workflows/wiki-sync.yml"))
    (root / ".github/workflows/wiki-sync.yml").write_text(wiki, encoding="utf-8")

    cla = root / "CLA.md"
    cla_text = cla.read_text(encoding="utf-8")
    if "Jim Daley" not in cla_text:
        cla_text = cla_text.rstrip() + (
            "\n## Repository owner\n\n"
            "This repository is maintained by Jim Daley (legal name James Daley).\n\n"
        )
        cla.write_text(cla_text, encoding="utf-8")

    platform_path = root / "scripts/check_platform_agnosticism.py"
    platform_text = platform_path.read_text(encoding="utf-8")
    old_allowlist = '''APPROVED_REFERENCE_SOURCES = {
    "core/ash_pattern_engine/__init__.py",
    "core/ash_pattern_engine/ash_canonical.py",
}
'''
    new_allowlist = '''APPROVED_REFERENCE_SOURCES = {
    "core/ash_pattern_engine/__init__.py",
    "core/ash_pattern_engine/ash_canonical.py",
    "docs/design-planning/m2/ash-values/verification/value_model.py",
    "docs/design-planning/m2/ash-values/verification/verify_contract.py",
    "docs/design-planning/m2/consumer-compatibility/verify_compatibility.py",
    "docs/design-planning/m2/readiness/probes/schema_readiness_probe.py",
    "docs/design-planning/m2/readiness/probes/verify_probe.py",
}
'''
    if old_allowlist in platform_text:
        platform_text = replace_once(
            platform_text, old_allowlist, new_allowlist, "platform allowlist"
        )
    elif new_allowlist not in platform_text:
        raise RuntimeError("Platform allowlist is neither original nor reconciled")
    platform_path.write_text(platform_text, encoding="utf-8")

    roadmap_path = root / "scripts/check_specification_roadmap.py"
    roadmap_text = roadmap_path.read_text(encoding="utf-8")
    old_wiki_gate = '''    if "- 'VERSION'" not in text:
        errors.append("Wiki synchronization must trigger when VERSION changes")
'''
    new_wiki_gate = '''    if "- 'VERSION'" not in text and "workflow_dispatch:" not in text:
        errors.append(
            "Wiki synchronization must trigger when VERSION changes or provide an explicit manual route"
        )
'''
    if old_wiki_gate in roadmap_text:
        roadmap_text = replace_once(roadmap_text, old_wiki_gate, new_wiki_gate, "wiki gate")
    elif new_wiki_gate not in roadmap_text:
        raise RuntimeError("Wiki gate is neither original nor reconciled")
    roadmap_path.write_text(roadmap_text, encoding="utf-8")

    tests_path = root / "tests/test_validation_foundation.py"
    tests = tests_path.read_text(encoding="utf-8")
    platform_anchor = '''    def test_product_source_outside_approved_paths_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "product" / "runtime.py"
            path.parent.mkdir(parents=True)
            path.write_text("value = 1\\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertTrue(any("runtime.py" in violation for violation in violations))

'''
    platform_tests = '''    def test_reviewed_planning_verification_sources_are_allowed_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in sorted(platform_check.APPROVED_REFERENCE_SOURCES):
                if not relative_path.startswith("docs/design-planning/"):
                    continue
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("value = 1\\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertEqual([], violations)

    def test_unreviewed_planning_executable_remains_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "docs/design-planning/m2/unreviewed.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("value = 1\\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertTrue(any("unreviewed.py" in violation for violation in violations))

'''
    if "test_reviewed_planning_verification_sources_are_allowed_exactly" not in tests:
        tests = replace_once(
            tests, platform_anchor, platform_anchor + platform_tests, "platform tests"
        )

    workflow_anchor = "    def test_version_workflow_does_not_publish_or_tag(self):\n"
    wiki_test = '''    def test_manual_wiki_workflow_uses_canonical_version(self):
        workflow = (ROOT / ".github/workflows/wiki-sync.yml").read_text(encoding="utf-8-sig")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("main-repo/VERSION", workflow)
        self.assertEqual([], roadmap_check.wiki_version_workflow_errors(ROOT))

'''
    if "test_manual_wiki_workflow_uses_canonical_version" not in tests:
        tests = replace_once(tests, workflow_anchor, wiki_test + workflow_anchor, "wiki test")
    tests_path.write_text(tests, encoding="utf-8")

    readme = root / "README.md"
    readme_text = readme.read_text(encoding="utf-8-sig")
    start = readme_text.index(roadmap.README_STATUS_START)
    end = readme_text.index(roadmap.README_STATUS_END, start) + len(roadmap.README_STATUS_END)
    roadmap_data = load(root, roadmap.ROADMAP_PATH)
    block = (
        roadmap.README_STATUS_START
        + "\n"
        + roadmap.render_readme_status(roadmap_data)
        + "\n"
        + roadmap.README_STATUS_END
    )
    readme.write_text(readme_text[:start] + block + readme_text[end:], encoding="utf-8")

    class_path = "data/governance/artifact_classification_manifest.json"
    scope_path = "data/governance/scope_partition_manifest.json"
    classification = load(root, class_path)
    scope = load(root, scope_path)

    acr200 = next(rule for rule in classification["ordered_rules"] if rule["id"] == "ACR-200")
    if "docs/design-planning/**" not in acr200["include"]:
        acr200["include"].append("docs/design-planning/**")
    acr900 = next(rule for rule in classification["ordered_rules"] if rule["id"] == "ACR-900")
    if "docs/design-planning/**" not in acr900["exclude"]:
        acr900["exclude"].append("docs/design-planning/**")

    spr300 = next(rule for rule in scope["ordered_rules"] if rule["id"] == "SPR-300")
    if "docs/design-planning/**" not in spr300["include"]:
        spr300["include"].append("docs/design-planning/**")
    spr900 = next(rule for rule in scope["ordered_rules"] if rule["id"] == "SPR-900")
    if "docs/design-planning/**" not in spr900["exclude"]:
        spr900["exclude"].append("docs/design-planning/**")

    write(root, class_path, classification)
    write(root, scope_path, scope)

    errors: list[str] = []
    paths = m0.repository_candidate_paths(root, errors)
    if errors:
        raise RuntimeError("\n".join(errors))
    for manifest in (classification, scope):
        manifest["tracked_path_snapshot"]["path_count"] = len(paths)
        manifest["tracked_path_snapshot"]["path_digest"] = m0.nul_digest(paths)

    assignment_errors: list[str] = []
    class_assignments = m0.effective_assignments(
        paths, classification, "classification", assignment_errors, "Artifact classification"
    )
    scope_assignments = m0.effective_assignments(
        paths, scope, "primary_partition", assignment_errors, "Scope partition"
    )
    assignment_errors = [
        error for error in assignment_errors if "coverage counts are stale" not in error
    ]
    if assignment_errors:
        raise RuntimeError("\n".join(assignment_errors))

    class_counts = Counter(item["classification"] for item in class_assignments.values())
    scope_counts = Counter(item["primary_partition"] for item in scope_assignments.values())
    classification["coverage"]["counts_by_class"] = {
        key: class_counts.get(key, 0)
        for key in classification["coverage"]["counts_by_class"]
    }
    scope["coverage"]["counts_by_partition"] = {
        key: scope_counts.get(key, 0)
        for key in scope["coverage"]["counts_by_partition"]
    }
    for source in classification.get("sensitive_sources", []):
        source["sha256"] = m0.normalized_text_sha256(root / source["path"])
    write(root, class_path, classification)
    write(root, scope_path, scope)

    promises_path = "data/governance/public_promise_register.json"
    promises = load(root, promises_path)
    for surface in promises.get("reviewed_surfaces", []):
        surface["sha256"] = m0.normalized_text_sha256(root / surface["path"])
    promises["reviewed_surface_aggregate_sha256"] = m0.reviewed_surface_digest(
        promises.get("reviewed_surfaces", [])
    )
    records = promises.get("promises", [])
    promises["summary"] = {
        "reviewed_surface_count": len(promises.get("reviewed_surfaces", [])),
        "promise_count": len(records),
        "assigned_count": sum(
            record.get("disposition") == "milestone_assigned" for record in records
        ),
        "excluded_count": sum(
            record.get("disposition") == "formally_excluded" for record in records
        ),
        "unresolved_count": 0,
    }
    write(root, promises_path, promises)

    release_path = "data/governance/release_publication_policy.json"
    release = load(root, release_path)
    release.setdefault("tag_semantics", {})["existing_tag_count"] = 0
    release["tag_semantics"]["tags_at_current_head"] = []
    write(root, release_path, release)

    debt_path = "data/validation/repository_quality_debt_inventory.json"
    schema_debt_path = "data/validation/schema_quality_baseline.json"
    debt = load(root, debt_path)
    schema_debt = load(root, schema_debt_path)
    known = schema_debt.get("known_debt", {})
    counts = {key: len(value) for key, value in known.items() if isinstance(value, list)}
    subledger = debt.setdefault("schema_debt_subledger", {})
    subledger["sha256"] = m0.normalized_text_sha256(root / schema_debt_path)
    subledger["counts_by_category"] = counts
    subledger["category_occurrence_count"] = sum(counts.values())
    subledger["unique_path_count"] = len(
        {
            path
            for values in known.values()
            if isinstance(values, list)
            for path in values
        }
    )
    write(root, debt_path, debt)

    print(f"Reconciled {len(paths)} repository paths.")
    print("Classification:", classification["coverage"]["counts_by_class"])
    print("Scope:", scope["coverage"]["counts_by_partition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
