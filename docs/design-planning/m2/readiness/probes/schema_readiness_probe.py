"""Read-only readiness probe for one pinned, retrieved YWE schema artifact.

This is diagnostic tooling, not engine implementation or an acceptance validator.
Exit 2 means the inspected baseline has demonstrated readiness blockers.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry
from referencing.exceptions import NoSuchResource

EXPECTED_BLOB = "1d1891fce3138fd87ce69483b47f9b093094fe71"
EXPECTED_COMMIT = "2db1230f638cd065d791c05f1adb7b4b51505c57"
MAX_SOURCE_BYTES = 1_000_000


def refuse_remote(uri: str) -> Any:
    raise NoSuchResource(ref=uri)


def pointer(parts: Any) -> str:
    return "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in parts)


@dataclass(frozen=True)
class ProbeCase:
    identifier: str
    description: str
    instance: Any


class SchemaReadinessProbe:
    def __init__(self, source: Path) -> None:
        if not source.is_file() or source.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError("Source must be an existing file no larger than 1 MB.")
        self.raw = source.read_bytes()
        self.blob = hashlib.sha1(
            b"blob " + str(len(self.raw)).encode("ascii") + b"\0" + self.raw
        ).hexdigest()
        if self.blob != EXPECTED_BLOB:
            raise ValueError(f"Source hash mismatch: {self.blob}; expected {EXPECTED_BLOB}.")
        self.schema = json.loads(self.raw)
        if not isinstance(self.schema, dict) or not isinstance(self.schema.get("records"), dict):
            raise ValueError("Pinned artifact structure is not recognized.")
        self.registry = Registry(retrieve=refuse_remote)

    def validator(self, schema: dict[str, Any]) -> Draft202012Validator:
        return Draft202012Validator(schema, registry=self.registry)

    def run(self) -> dict[str, Any]:
        Draft202012Validator.check_schema(self.schema)
        root_validator = self.validator(self.schema)
        probes = [
            ProbeCase("ROOT-01", "Null", None),
            ProbeCase("ROOT-02", "Boolean false", False),
            ProbeCase("ROOT-03", "Boolean true", True),
            ProbeCase("ROOT-04", "Integer", 42),
            ProbeCase("ROOT-05", "Non-integral number", 0.5),
            ProbeCase("ROOT-06", "Arbitrary string", "not a packet"),
            ProbeCase("ROOT-07", "Empty array", []),
            ProbeCase("ROOT-08", "Empty object", {}),
            ProbeCase("ROOT-09", "Missing state bits", {"state_space": "F2^9"}),
            ProbeCase("ROOT-10", "Incorrect state space", {"state_space": "F2^8", "bits": [0]*9}),
            ProbeCase("ROOT-11", "Eight coordinates", {"state_space": "F2^9", "bits": [0]*8}),
            ProbeCase("ROOT-12", "Ten coordinates", {"state_space": "F2^9", "bits": [0]*10}),
            ProbeCase("ROOT-13", "Nonbinary coordinate", {"state_space": "F2^9", "bits": [2]+[0]*8}),
            ProbeCase("ROOT-14", "Boolean coordinates", {"state_space": "F2^9", "bits": [True]*9}),
            ProbeCase("ROOT-15", "Missing provenance", {"snapshot_type": "CosmicPatternSnapshot"}),
            ProbeCase("ROOT-16", "Unknown discriminator", {"record_type": "not-a-YWE-type"}),
        ]
        root_results = []
        for case in probes:
            errors = list(root_validator.iter_errors(case.instance))
            root_results.append({
                "id": case.identifier, "description": case.description,
                "instance": case.instance, "accepted_by_advertised_root_schema": not errors,
                "errors": [{"keyword": e.validator, "instance_pointer": pointer(e.path),
                            "schema_pointer": pointer(e.schema_path), "message": e.message} for e in errors],
            })
        record_results = []
        for name, record in self.schema["records"].items():
            try:
                Draft202012Validator.check_schema(record)
            except SchemaError as exc:
                # Library-selected first-error ordering is not a stable diagnostic identity.
                # Gather and sort all top-level meta-schema errors by source pointer.
                meta_validator = Draft202012Validator(
                    Draft202012Validator.META_SCHEMA,
                    format_checker=Draft202012Validator.FORMAT_CHECKER,
                )
                meta_errors = sorted(
                    meta_validator.iter_errors(record),
                    key=lambda e: (pointer(e.path), str(e.validator), e.message),
                )
                chosen = meta_errors[0] if meta_errors else exc
                record_results.append({"record": name, "standalone_meta_valid": False,
                                       "record_pointer": f"/records/{name}",
                                       "error_pointer": pointer(chosen.path), "message": chosen.message})
            else:
                v = self.validator(record)
                record_results.append({"record": name, "standalone_meta_valid": True,
                                       "accepts_null_when_lifted_unchanged": v.is_valid(None)})

        exchange = self.schema["records"]["SystemManifestExchange"]
        example = {key: "probe-only-reference" for key in exchange["required"]}
        v = self.validator(exchange)
        exchange_probes = []
        for label, delta in [
            ("Required keys alone", {}),
            ("Intended false flag provided", {"host_adapter_may_author_truth": False}),
            ("Intended false math-authority flag provided", {"feature_engine_claims_math_authority": False}),
            ("Intended true flag supplied as false", {"planning_precedes_materialization": False}),
            ("Intended true flag supplied as arbitrary text", {"planning_precedes_materialization": "anything"}),
        ]:
            instance = {**example, **delta}
            errors = list(v.iter_errors(instance))
            exchange_probes.append({"description": label, "instance": instance,
                                    "accepted_when_record_lifted_unchanged": not errors,
                                    "messages": [e.message for e in errors]})

        assert all(x["accepted_by_advertised_root_schema"] for x in root_results)
        invalid = [x for x in record_results if not x["standalone_meta_valid"]]
        assert invalid, "Pinned-source expectation failed: investigate rather than assuming known defects."
        assert exchange_probes[0]["accepted_when_record_lifted_unchanged"]
        assert not exchange_probes[1]["accepted_when_record_lifted_unchanged"]
        assert not exchange_probes[2]["accepted_when_record_lifted_unchanged"]
        assert exchange_probes[3]["accepted_when_record_lifted_unchanged"]
        assert exchange_probes[4]["accepted_when_record_lifted_unchanged"]
        return {
            "artifact_type": "ywe_schema_readiness_diagnostic", "status": "BLOCKED",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": {"repository": "flynn33/yggdrasil-world-engine", "commit": EXPECTED_COMMIT,
                       "path": "data/schemas/ash_generation_packet_schema.json", "git_blob_sha1": self.blob,
                       "sha256": hashlib.sha256(self.raw).hexdigest(), "bytes": len(self.raw)},
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "jsonschema": version("jsonschema"), "referencing": version("referencing"),
                            "remote_reference_retrieval": "denied"},
            "summary": {"root_meta_schema_valid": True, "root_probes": len(root_results),
                        "root_probes_accepted": sum(x["accepted_by_advertised_root_schema"] for x in root_results),
                        "descriptive_records": len(record_results), "invalid_if_lifted_as_schema": len(invalid),
                        "valid_meta_records_accepting_null": sum(x.get("accepts_null_when_lifted_unchanged", False) for x in record_results),
                        "exchange_semantics_probes": len(exchange_probes),
                        "source_mutated": False, "repository_suite_run": False,
                        "product_schema_change_applied": False},
            "root_results": root_results, "record_results": record_results, "exchange_probes": exchange_probes,
            "limits": ["One pinned artifact, not the full repository or custom catalog consumers.",
                       "Standalone record evaluation is a counterfactual migration test, not a claim that the baseline dispatches records this way.",
                       "Meta-schema validity does not establish domain conformance.",
                       "No milestone accepted, repository write performed, or source revision upgraded."],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.source.resolve() == args.report.resolve():
        parser.error("Report must not overwrite the source.")
    try:
        result = SchemaReadinessProbe(args.source).run()
        if args.report.exists():
            raise FileExistsError("Refusing to overwrite existing evidence; select a new report path.")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write("\n")
    except (OSError, ValueError, SchemaError, AssertionError) as exc:
        print(f"Probe execution failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result["summary"], indent=2))
    print("Readiness: BLOCKED. Diagnostic observations reproduced; this is not a passing product gate.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
