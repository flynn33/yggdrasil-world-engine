#!/usr/bin/env python3
"""Validate repository JSON, YAML, JSON Schema declarations, and tracked debt."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
    from jsonschema.validators import validator_for
except ImportError:
    print("Missing validation dependencies. Install scripts/requirements.txt.")
    raise SystemExit(1)

DEBT_PATH = "data/validation/schema_quality_baseline.json"
SCHEMA_KEYWORDS = {
    "type",
    "properties",
    "items",
    "allOf",
    "anyOf",
    "oneOf",
    "not",
    "if",
    "$defs",
    "enum",
    "const",
    "required",
    "additionalProperties",
    "patternProperties",
}


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def repository_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode == 0:
        names = [name for name in result.stdout.decode("utf-8").split("\0") if name]
        return sorted(root / name for name in names if (root / name).is_file())
    return sorted(path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts)


def walk_refs(value, pointer=""):
    if isinstance(value, dict):
        for key, item in value.items():
            next_pointer = f"{pointer}/{key}"
            if key == "$ref" and isinstance(item, str):
                yield next_pointer, item
            yield from walk_refs(item, next_pointer)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_refs(item, f"{pointer}/{index}")


def resolve_json_pointer(document, ref: str) -> bool:
    if ref == "#":
        return True
    if not ref.startswith("#/"):
        return False
    current = document
    for token in ref[2:].split("/"):
        token = unquote(token).replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return False
    return True


def quality_debt(
    schema_documents: dict[str, dict], json_documents: dict[str, object] | None = None
) -> dict[str, list[str]]:
    json_documents = json_documents or schema_documents
    return {
        "declared_schema_missing_id": sorted(
            path for path, document in schema_documents.items() if "$id" not in document
        ),
        "annotation_only_schema_documents": sorted(
            path for path, document in schema_documents.items() if not SCHEMA_KEYWORDS.intersection(document)
        ),
        "schema_named_json_without_schema_declaration": sorted(
            path
            for path, document in json_documents.items()
            if path != DEBT_PATH
            and "schema" in Path(path).stem.lower()
            and not (isinstance(document, dict) and "$schema" in document)
        ),
        "unbound_json_examples": sorted(
            path
            for path, document in json_documents.items()
            if path.startswith("examples/")
            and not (
                isinstance(document, dict)
                and any(key in document for key in ("$schema", "schema_ref", "schema_id"))
            )
        ),
    }


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    json_count = 0
    yaml_count = 0
    json_documents: dict[str, object] = {}
    schema_documents: dict[str, dict] = {}
    schema_ids: dict[str, list[str]] = defaultdict(list)

    for path in repository_files(root):
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        if suffix == ".json":
            json_count += 1
            try:
                document = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
                continue
            json_documents[rel] = document
            if isinstance(document, dict) and "$schema" in document:
                schema_documents[rel] = document
                if isinstance(document.get("$id"), str):
                    schema_ids[document["$id"]].append(rel)
                try:
                    validator_for(document).check_schema(document)
                except Exception as exc:
                    errors.append(f"{rel}: invalid JSON Schema declaration: {exc}")
                for pointer, ref in walk_refs(document):
                    if ref.startswith("#") and not resolve_json_pointer(document, ref):
                        errors.append(f"{rel}{pointer}: unresolved local reference {ref!r}")
        elif suffix in {".yaml", ".yml"}:
            yaml_count += 1
            try:
                yaml.load(path.read_text(encoding="utf-8-sig"), Loader=UniqueKeyLoader)
            except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
                errors.append(f"{rel}: invalid YAML: {exc}")

    for schema_id, paths in sorted(schema_ids.items()):
        if len(paths) > 1:
            errors.append(f"Duplicate schema identifier {schema_id!r}: {paths}")

    try:
        baseline = json.loads((root / DEBT_PATH).read_text(encoding="utf-8-sig"))
        expected_debt = baseline["known_debt"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"Unable to load schema quality baseline: {exc}")
        expected_debt = {}
    actual_debt = quality_debt(schema_documents, json_documents)
    for debt_kind, actual in actual_debt.items():
        expected = sorted(expected_debt.get(debt_kind, []))
        if actual != expected:
            added = sorted(set(actual) - set(expected))
            resolved = sorted(set(expected) - set(actual))
            if added:
                errors.append(f"Unregistered {debt_kind}: {added}")
            if resolved:
                errors.append(f"Resolved {debt_kind} must be removed from the baseline: {resolved}")

    if errors:
        print("Machine-readable artifact check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"Machine-readable artifact check passed ({json_count} JSON, {yaml_count} YAML, "
        f"{len(schema_documents)} declared schemas, {len(schema_ids)} unique schema identifiers)."
    )
    print(
        "Tracked M2 schema debt: "
        f"{len(actual_debt['declared_schema_missing_id'])} declarations without $id; "
        f"{len(actual_debt['annotation_only_schema_documents'])} annotation-only declarations; "
        f"{len(actual_debt['schema_named_json_without_schema_declaration'])} schema-named JSON artifacts "
        f"without a declaration; {len(actual_debt['unbound_json_examples'])} unbound JSON examples."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
