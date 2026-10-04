#!/usr/bin/env python3
"""Validate explicit fixture bindings and resolve schema references offline."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from check_machine_readable_artifacts import UniqueKeyLoader, repository_files

CONTRACT_CATALOG = "data/validation/contract_catalog.json"
FIXTURE_CATALOG = "data/validation/fixture_catalog.json"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
DESCRIPTOR_SCHEMAS = {
    "https://ywe.local/schemas/pattern_registry_descriptor_schema.json": "pattern",
    "https://ywe.local/schemas/module_capability_descriptor_schema.json": "module",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_instance(path: Path):
    if path.suffix.lower() == ".json":
        return load_json(path)
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Unsupported fixture format: {path.suffix!r}")
    document = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=UniqueKeyLoader)
    # JSON Schema evaluates JSON values; YAML-only values have no contract here.
    json.dumps(document, allow_nan=False)
    pending = [document]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise ValueError("YAML fixture mapping keys must be strings")
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif type(value) not in {type(None), bool, int, float, str}:
            raise ValueError(f"Unsupported YAML fixture value: {type(value).__name__}")
    return document


def repository_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Expected a nonempty repository-relative POSIX path")
    path = Path(relative)
    if path.is_absolute() or path.drive or ".." in path.parts or ":" in relative:
        raise ValueError(f"Path escapes the repository: {relative!r}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes the repository: {relative!r}")
    return resolved


def json_pointer(document, pointer: str):
    """Resolve RFC 6901 pointers; the empty pointer selects the document root."""
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError(f"Invalid JSON Pointer: {pointer!r}")
    current = document
    for encoded in pointer.split("/")[1:]:
        if re.search(r"~(?![01])", encoded):
            raise ValueError(f"Invalid JSON Pointer escape: {pointer!r}")
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            index = int(token)
            if index >= len(current):
                raise ValueError(f"Unresolved JSON Pointer: {pointer!r}")
            current = current[index]
        else:
            raise ValueError(f"Unresolved JSON Pointer: {pointer!r}")
    return current


def pointer_from_parts(parts) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def leaf_errors(error):
    if error.context:
        for child in error.context:
            yield from leaf_errors(child)
    else:
        yield error


def error_signature(error) -> dict[str, object]:
    signature = {
        "error_id": "JSON_SCHEMA_" + str(error.validator).upper(),
        "instance_pointer": pointer_from_parts(error.absolute_path),
        "schema_pointer": pointer_from_parts(error.absolute_schema_path),
    }
    if error.validator == "required" and isinstance(error.instance, dict):
        signature["missing_properties"] = sorted(
            name for name in error.validator_value if name not in error.instance
        )
    return signature


def signature_key(signature: dict) -> str:
    return json.dumps(signature, sort_keys=True, separators=(",", ":"))


def deny_retrieval(uri: str):
    raise NoSuchResource(ref=uri)


def schema_references(resource: Resource, base: str):
    """Visit actual subschemas, excluding reference-like strings in annotations."""
    identifier = resource.id()
    if identifier:
        base = urljoin(base, identifier)
    contents = resource.contents
    if isinstance(contents, dict):
        for keyword in ("$ref", "$dynamicRef"):
            if keyword in contents:
                yield base, contents[keyword]
    for child in resource.subresources():
        yield from schema_references(child, base)


def schema_nodes(resource: Resource):
    yield resource.contents
    for child in resource.subresources():
        yield from schema_nodes(child)


def resource_identities(resource: Resource, base: str):
    identifier = resource.id()
    if identifier:
        base = urljoin(base, identifier)
        yield base
    for child in resource.subresources():
        yield from resource_identities(child, base)


def resource_anchors(resource: Resource, base: str):
    if resource.id():
        base = urljoin(base, resource.id())
    if isinstance(resource.contents, dict):
        for keyword in ("$anchor", "$dynamicAnchor"):
            if keyword in resource.contents:
                yield base, resource.contents[keyword]
    for child in resource.subresources():
        yield from resource_anchors(child, base)


def is_schema_pointer(document, pointer: str) -> bool:
    """Recognize schema locations, including booleans, by keyword and path."""
    json_pointer(document, pointer)  # Reject unresolved or malformed pointers first.
    tokens = [token.replace("~1", "/").replace("~0", "~") for token in pointer.split("/")[1:]]
    mapping_keywords = {"$defs", "definitions", "properties", "patternProperties", "dependentSchemas"}
    sequence_keywords = {"allOf", "anyOf", "oneOf", "prefixItems"}
    single_keywords = {
        "additionalProperties", "unevaluatedProperties", "propertyNames", "contains",
        "items", "unevaluatedItems", "not", "if", "then", "else", "contentSchema",
    }
    current = document
    position = 0
    while position < len(tokens):
        if not isinstance(current, dict):
            return False
        keyword = tokens[position]
        position += 1
        if keyword in single_keywords:
            current = current[keyword]
        elif keyword in mapping_keywords or keyword in sequence_keywords:
            if position == len(tokens):
                return False
            member = tokens[position]
            position += 1
            current = current[keyword][int(member) if keyword in sequence_keywords else member]
        else:
            return False
    return isinstance(current, (dict, bool))


def resolve_schema_target(registry: Registry, reference: str, base: str = ""):
    resolved = registry.resolver(base).lookup(reference)
    absolute = base + reference if reference.startswith("#") else urljoin(base, reference)
    uri, fragment = urldefrag(absolute)
    resource = registry[uri]
    fragment = unquote(fragment)
    if not fragment or fragment.startswith("/"):
        if not is_schema_pointer(resource.contents, fragment):
            raise ValueError("Target does not resolve to a schema location")
    elif not isinstance(resolved.contents, dict) or not any(
        resolved.contents is node for node in schema_nodes(resource)
    ):
        raise ValueError("Target does not resolve to a schema anchor")
    return resolved


def load_registry(root: Path) -> tuple[Registry, list[str]]:
    catalog = load_json(repository_path(root, CONTRACT_CATALOG))
    entries = catalog["schemas"]
    errors = []
    resources = []
    seen_ids = set()
    seen_paths = set()
    declared = set()
    for path in repository_files(root):
        if path.suffix.lower() == ".json":
            document = load_json(path)
            if isinstance(document, dict) and "$schema" in document:
                declared.add(path.relative_to(root).as_posix())
    for entry in entries:
        identifier, relative = entry["schema_id"], entry["path"]
        if identifier in seen_ids or relative in seen_paths:
            errors.append(f"Duplicate schema catalog entry: {identifier!r} at {relative}")
        seen_ids.add(identifier)
        seen_paths.add(relative)
        try:
            document = load_json(repository_path(root, relative))
            if document.get("$id") != identifier:
                errors.append(f"Schema catalog identifier mismatch: {relative}")
            if document.get("$schema") != DIALECT:
                errors.append(f"Unsupported schema dialect: {relative}")
            Draft202012Validator.check_schema(document)
            resources.append((identifier, Resource.from_contents(document)))
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            errors.append(f"Invalid schema catalog resource {relative}: {exc}")
        except Exception as exc:
            errors.append(f"Invalid schema declaration {relative}: {exc}")
    if seen_paths != declared:
        errors.append(
            f"Schema catalog coverage differs: missing={sorted(declared - seen_paths)}; "
            f"extra={sorted(seen_paths - declared)}"
        )
    resource_ids = set()
    anchors = set()
    for identifier, resource in resources:
        for effective_id in resource_identities(resource, ""):
            if effective_id in resource_ids:
                errors.append(f"Duplicate effective schema resource identifier: {effective_id!r}")
            resource_ids.add(effective_id)
        for anchor in resource_anchors(resource, ""):
            if anchor in anchors:
                errors.append(f"Duplicate schema anchor: {anchor!r}")
            anchors.add(anchor)
    if errors:
        return Registry(retrieve=deny_retrieval), errors
    registry = Registry(retrieve=deny_retrieval).with_resources(resources).crawl()
    for identifier, resource in resources:
        for base, reference in schema_references(resource, ""):
            try:
                resolve_schema_target(registry, reference, base)
            except Exception as exc:
                errors.append(f"Unresolved offline schema reference in {identifier}: {reference!r}: {exc}")
    return registry, errors


def evaluate_fixtures(root: Path, registry: Registry, fixtures: list[dict]):
    errors = []
    results = []
    seen_ids = set()
    seen_bindings = set()
    for fixture in fixtures:
        fixture_id = fixture["fixture_id"]
        binding = (fixture["path"], fixture["instance_pointer"], fixture["schema_id"])
        if fixture_id in seen_ids or binding in seen_bindings:
            errors.append(f"Duplicate fixture ID or binding: {fixture_id}")
        seen_ids.add(fixture_id)
        seen_bindings.add(binding)
        try:
            # Resolve even when the instance is empty or the validator would skip it.
            target = resolve_schema_target(registry, fixture["schema_id"])
            instance = json_pointer(
                load_instance(repository_path(root, fixture["path"])), fixture["instance_pointer"]
            )
            validator = Draft202012Validator(
                {"$ref": fixture["schema_id"]}, registry=registry
            )
            witnessed = {
                signature_key(error_signature(leaf))
                for error in validator.iter_errors(instance)
                for leaf in leaf_errors(error)
            }
            grammar = DESCRIPTOR_SCHEMAS.get(fixture["schema_id"])
            if grammar:
                if target.contents.get("x-ywe-descriptor-grammar") != grammar:
                    raise ValueError("Descriptor schema differs from its registered grammar")
                if not witnessed:
                    from check_yaml_descriptor_contracts import descriptor_semantic_errors

                    witnessed.update(signature_key(error) for error in descriptor_semantic_errors(instance, grammar, root))
            expected = {signature_key(error) for error in fixture["expected_errors"]}
            result = "reject" if witnessed else "accept"
            if result != fixture["expected_result"] or witnessed != expected:
                errors.append(
                    f"Fixture {fixture_id}: expected {fixture['expected_result']} {sorted(expected)}; "
                    f"observed {result} {sorted(witnessed)}"
                )
            else:
                results.append({"fixture_id": fixture_id, "path": fixture["path"], "result": result})
        except Exception as exc:
            errors.append(f"Fixture {fixture_id}: unable to validate offline: {exc}")
    return errors, results


def validation_errors(root: Path) -> tuple[list[str], list[dict]]:
    try:
        registry, errors = load_registry(root)
        if errors:
            return errors, []
        catalogs = (
            (CONTRACT_CATALOG, "https://ywe.local/schemas/contract_catalog_schema.json"),
            (FIXTURE_CATALOG, "https://ywe.local/schemas/fixture_catalog_schema.json"),
        )
        for relative, schema_id in catalogs:
            validator = Draft202012Validator({"$ref": schema_id}, registry=registry)
            errors.extend(f"{relative}: {error.message}" for error in validator.iter_errors(load_json(root / relative)))
        if errors:
            return errors, []
        catalog = load_json(root / FIXTURE_CATALOG)
        return evaluate_fixtures(root, registry, catalog["fixtures"])
    except Exception as exc:
        return [f"Unable to load fixture/schema catalogs: {exc}"], []


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors, results = validation_errors(root)
    if errors:
        print("Fixture catalog check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    rejected = sum(result["result"] == "reject" for result in results)
    print(f"Fixture catalog check passed ({len(results)} bindings; {rejected} intended rejections; offline references resolved).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
