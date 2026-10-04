"""Authored N2 format controls, independent of recovery producer output."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ID = "https://ywe.local/schemas/m3_recovery_value_schema.json"
REGISTRY_ID = "https://ywe.local/schemas/m3_fallback_registry_schema.json"
SCHEMA_NAMES = (
    "m3_state_assessment_schema.json", "m3_normalization_plan_schema.json",
    "m3_state_normalization_schema.json", "m3_reference_diagnostic_bundle_schema.json",
    "m3_recovery_value_schema.json", "m3_fallback_registry_schema.json",
)
SOURCE_PATHS = (
    "interfaces/contracts/recovery-engine-contract.md", "interfaces/contracts/diagnostics-module-contract.md",
    "registries/fallback-policy-registry.md", "algorithms/recovery-fallback-semantics.pseudo.md",
    "algorithms/containment-safe-failure-semantics.pseudo.md", "interfaces/diagnostic-schema.md",
    "interfaces/rule-id-taxonomy.md",
)


def deny_retrieval(uri):
    raise NoSuchResource(ref=uri)


def schemas():
    resources = {}
    registry = Registry(retrieve=deny_retrieval)
    for name in SCHEMA_NAMES:
        document = json.loads((ROOT / "data/schemas" / name).read_text(encoding="utf-8"))
        resources[document["$id"]] = document
        registry = registry.with_resource(document["$id"], Resource.from_contents(document))
    return resources, registry


def owned_source(reference="declared:format:test"):
    return {"source_reference": reference, "source_sha256": "a" * 64, "evidence_reference": reference + ":evidence"}


def assessments():
    return json.loads((ROOT / "examples/core_state_assessment/state_assessment_cases.example.json").read_text(encoding="utf-8"))


def contract_binding(origin):
    pins = []
    for path in SOURCE_PATHS:
        text = (ROOT / "core/ash_pattern_engine/canonical" / path).read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        pins.append({"path": path, "sha256": hashlib.sha256(text.encode()).hexdigest()})
    return {"canonical_binding": deepcopy(origin["source_binding"]), "contract_pins": pins}


def comparison(origin, *, status="VERIFIED"):
    return {"status": status, "submitted_assessment": deepcopy(origin),
            "current_source_binding": deepcopy(origin["source_binding"]), "current_profile_binding": deepcopy(origin["profile_binding"]),
            "expected_diagnostic": deepcopy(origin["state_validity_diagnostic"]) if status == "VERIFIED" else None,
            "expected_system_state_class": origin["system_state_class"] if status == "VERIFIED" else None,
            "expected_recovery_category": origin["recovery_category"] if status == "VERIFIED" else None,
            "expected_consulted_predicates": list(origin["consulted_predicates"]) if status == "VERIFIED" else None,
            "failure_code": None if status == "VERIFIED" else "DIAGNOSIS_MISMATCH", "field_name": None if status == "VERIFIED" else "origin_assessment.state_validity_diagnostic.is_valid"}


def operation(origin):
    origin_ref = origin["assessment_binding"]["assessment_reference"]
    observation = {"context": deepcopy(origin["system_context"]), "owner_reference": "declared:context:owner",
                   "observation_reference": "declared:context", "source_binding": owned_source()}
    def evidence(status):
        return {"status": status, "operation_reference": "operation:authored", "origin_assessment_reference": origin_ref,
                "source_binding": owned_source(), "reason": "Explicit authored observation."}
    return {"operation_reference": "operation:authored", "origin_assessment_reference": origin_ref,
            "context_observation": observation, "propagation_evidence": evidence("SAFE"), "external_authority_evidence": evidence("UNAVAILABLE")}


def decision(origin, *, action="NO_ACTION", outcome="NOT_APPLICABLE", target=None, directive=None, post=None, policy=None):
    canonical = {"recovery_category": origin["recovery_category"], "original_state_class": origin["system_state_class"],
                 "original_diagnostic": deepcopy(origin["state_validity_diagnostic"]), "steps": [], "outcome": outcome,
                 "corrected_state": deepcopy(target), "fallback_policy_id": policy, "reason": "Authored completed action decision.",
                 "rule_ids": ["ASH-RECOVERY-ACTION-001"]}
    return {"action_reference": "action:authored", "action": action, "diagnostic": canonical, "step_indices": [],
            "post_assessment_reference": post, "candidate_context": deepcopy(origin["system_context"]) if post else None,
            "directive": deepcopy(directive)}


def record(origin, action):
    return {"diagnostic_reference": "operation:authored:decision", "record_kind": "OPERATION_DECISION", "payload": deepcopy(action),
            "envelope": {"diagnostic_kind": "RECOVERY", "severity": "INFO", "stage": "RECOVERY", "disposition": "RESOLVED",
                "subject_reference": "ash_state_100000000", "parent_diagnostic_reference": origin["emitted_diagnostics"][-1]["diagnostic_reference"],
                "chain_root_reference": origin["assessment_binding"]["diagnosis_reference"], "rule_ids": ["ASH-RECOVERY-ACTION-001"],
                "summary": "Authored completed decision.", "notes": ["No session or mode effect is asserted."]}}


def packet(origin=None):
    original = deepcopy(origin or assessments()[5])
    action = decision(original)
    return {"schema_ref": "data/schemas/m3_recovery_value_schema.json", "artifact_type": "ywe_recovery_value", "artifact_version": "1.0.0",
            "outcome": "NO_ACTION", "execution_scope": "CORE_REFERENCE_IMMUTABLE_VALUE", "operation_context": operation(original),
            "origin_assessment": original, "origin_validation": comparison(original), "source_binding": contract_binding(original),
            "registry_binding": None, "route_authorization": None, "steps": [], "post_assessments": [], "policy_attempts": [],
            "action_decisions": [action], "emitted_diagnostics": [record(original, action)], "candidate_state": deepcopy(original["parsed_state"]),
            "directive": None, "failure_detail": None, "session_effects_performed": False, "normalization_preparation": None,
            "correction_observation": None, "registry_snapshot": None, "registry_validation": None, "completion_observation": None}


def registry_snapshot(origin=None, *, availability="AVAILABLE"):
    original = origin or assessments()[5]
    profile = original["profile_binding"]
    binding = {"registry_id": "declared:registry", "source_binding": owned_source(), "profile_id": profile["profile_id"],
               "profile_source_sha256": profile["source_binding"]["source_sha256"], "ash_dependency_id": original["source_binding"]["dependency_id"],
               "ash_aggregate_sha256": original["source_binding"]["aggregate_sha256"], "source_verification": "DECLARED_NOT_AUTHENTICATED"}
    result = {"schema_ref": "data/schemas/m3_fallback_registry_schema.json", "artifact_type": "ywe_fallback_registry", "artifact_version": "1.0.0", "availability": availability, "source_binding": binding}
    if availability == "AVAILABLE": result.update(entries=[], candidate_certifications=[])
    else: result["reason"] = "The declared registry source is unavailable."
    return result


def leaves(error):
    if error.context:
        for child in error.context:
            yield from leaves(child)
    else:
        yield error


class RecoverySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.registry = schemas()

    def validator(self, name=None, *, registry=False):
        uri = REGISTRY_ID if registry else RECOVERY_ID
        target = self.documents[uri] if name is None else {"$ref": uri + "#/$defs/" + name}
        return Draft202012Validator(target, registry=self.registry)

    def accept(self, document, name=None, *, registry=False):
        errors = list(self.validator(name, registry=registry).iter_errors(document))
        self.assertEqual(errors, [], [e.message for e in errors][:5])

    def reject(self, original, mutation, keyword, path, name=None, *, registry=False):
        self.accept(original, name, registry=registry)
        altered = deepcopy(original)
        mutation(altered)
        errors = [leaf for error in self.validator(name, registry=registry).iter_errors(altered) for leaf in leaves(error)]
        self.assertTrue(any(e.validator == keyword and tuple(e.absolute_path) == path for e in errors),
                        [(e.validator, list(e.absolute_path), e.message) for e in errors][:15])

    def test_metaschemas_owned_annotation_and_all_adopted_type_mappings(self):
        text = (ROOT / "docs/architecture/m3_recovery_contract.md").read_text(encoding="utf-8")
        adopted = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
        self.assertEqual(len(adopted["types"]), 49)
        self.assertTrue(set(adopted["types"]).issubset(self.documents[RECOVERY_ID]["$defs"]))
        for uri in (RECOVERY_ID, REGISTRY_ID):
            Draft202012Validator.check_schema(self.documents[uri])
            self.assertEqual(self.documents[uri]["x-ywe-requirement-id"], "YWE-REQ-0041")

    def test_every_declared_reference_resolves_without_network(self):
        def walk(node, base):
            if isinstance(node, dict):
                if "$ref" in node:
                    self.registry.resolver(base).lookup(node["$ref"])
                for value in node.values(): walk(value, base)
            elif isinstance(node, list):
                for value in node: walk(value, base)
        for uri, document in self.documents.items(): walk(document, uri)
        with self.assertRaises(Exception):
            self.registry.resolver(RECOVERY_ID).lookup("https://unregistered.invalid/schema")

    def test_authored_no_action_packet_exact_25_fields_and_header_refusals(self):
        p = packet()
        self.assertEqual(len(p), 25)
        self.accept(p)
        for name, value in (("session_effects_performed", True), ("execution_scope", "NATIVE_RUNTIME"), ("artifact_type", "canonical_recovery")):
            self.reject(p, lambda x, n=name, v=value: x.update({n: v}), "const", (name,))
        self.reject(p, lambda x: x.update(extra=True), "additionalProperties", ())
        self.reject(p, lambda x: x.pop("completion_observation"), "required", ())

    def test_no_action_cannot_include_recovery_steps_or_duplicate_decisions(self):
        p = packet()
        self.reject(p, lambda x: x["action_decisions"].append(deepcopy(x["action_decisions"][0])), "maxItems", ("action_decisions",))
        step = {"step_index": 0, "action": "NO_ACTION", "status": "COMPLETED", "before_state": None, "codeword": None,
                "after_state": None, "policy_id": None, "predicate_observation": None, "post_assessment_reference": None,
                "diagnostic_reference": "step:unexpected", "reason": "A typed but forbidden recovery observation."}
        self.reject(p, lambda x: x["steps"].append(step), "maxItems", ("steps",))

    def test_available_empty_and_unavailable_distinct_closed_roots(self):
        for status in ("AVAILABLE", "UNAVAILABLE"):
            self.accept(registry_snapshot(availability=status), registry=True)
        self.reject(registry_snapshot(), lambda x: x.pop("candidate_certifications"), "required", (), registry=True)
        self.reject(registry_snapshot(), lambda x: x.update(reason="Conflated unavailable branch."), "additionalProperties", (), registry=True)

    def test_available_entry_and_certification_cardinality_is_exact(self):
        p = registry_snapshot()
        child = assessments()[5]
        p["entries"] = [{"policy_id": "FALLBACK-TEST-001", "applicability_conditions": [], "candidate_state_reference": child["parsed_state"],
                         "ordering_rank": 0, "validation_requirements": [], "escalation_on_failure": "TRY_NEXT", "notes": ["Declared test entry."]}]
        p["candidate_certifications"] = [{"policy_id": "FALLBACK-TEST-001", "context_observation": operation(child)["context_observation"], "source_assessment": child}]
        self.reject(p, lambda x: x.update(candidate_certifications=[]), "minItems", ("candidate_certifications",), registry=True)

    def test_registry_entry_signed_rank_and_named_nested_bounds(self):
        target = assessments()[5]["parsed_state"]
        entry = {"policy_id": "FALLBACK-TEST-001", "applicability_conditions": [], "candidate_state_reference": target,
                 "ordering_rank": -(1 << 63), "validation_requirements": [], "escalation_on_failure": "TRY_NEXT", "notes": ["Declared policy."]}
        self.accept(entry, "FallbackPolicyEntry", registry=True)
        for rank in (True, -(1 << 63) - 1, 1 << 63):
            keyword = "type" if rank is True else "minimum" if rank < 0 else "maximum"
            self.reject(entry, lambda x, v=rank: x.update(ordering_rank=v), keyword, ("ordering_rank",), "FallbackPolicyEntry", registry=True)
        self.reject(entry, lambda x: x.update(policy_id="FALLBACK-TEST-000"), "pattern", ("policy_id",), "FallbackPolicyEntry", registry=True)
        condition = {"condition_id": "condition:test", "source_binding": owned_source()}
        self.reject(entry, lambda x: x.update(applicability_conditions=[condition] * 9), "maxItems", ("applicability_conditions",), "FallbackPolicyEntry", registry=True)

    def test_declared_correction_nonmember_is_structural_but_xor_requires_member(self):
        origin = assessments()[7]
        known = {"correction_reference": "correction:declared", "original_assessment_reference": origin["assessment_binding"]["assessment_reference"],
                 "source_binding": owned_source(), "profile_id": origin["profile_binding"]["profile_id"],
                 "profile_source_sha256": origin["profile_binding"]["source_binding"]["source_sha256"], "chain": [{"state_space": "F2^9", "bits": [1] * 9}],
                 "expected_target": origin["parsed_state"], "reason": "Declared nonmember is retained for pure proof rejection.",
                 "classification_evidence_reference": "predicate:known", "canonical_binding": origin["source_binding"], "provider_source_verification": "DECLARED_NOT_AUTHENTICATED"}
        self.accept(known, "KnownCorrection")
        self.reject(known, lambda x: x.update(chain=[{"state_space": "F2^9", "bits": [1] * 9}] * 17), "maxItems", ("chain",), "KnownCorrection")
        step = {"step_index": 0, "action": "CORRECTION_XOR", "status": "COMPLETED", "before_state": {"state_space": "F2^9", "bits": [1] * 9},
                "codeword": {"state_space": "F2^9", "bits": [0] * 9}, "after_state": {"state_space": "F2^9", "bits": [1] * 9}, "policy_id": None, "predicate_observation": None,
                "post_assessment_reference": None, "diagnostic_reference": "step:xor", "reason": "Actual step representation."}
        self.reject(step, lambda x: x.update(codeword={"state_space": "F2^9", "bits": [1] * 9}), "enum", ("codeword", "bits"), "RecoveryStepEvidence")
        self.reject(step, lambda x: x.update(step_index=False), "type", ("step_index",), "RecoveryStepEvidence")

    def test_route_preserves_original_class_category_and_blocks_normalization_relabelling(self):
        authorization = {"route": "AFTER_NORMALIZATION_FAILURE", "original_system_state_class": "UNSTABLE",
                         "origin_assessment_reference": "origin:unstable", "failed_action_decision_reference": "action:normalize",
                         "failed_outcome": "RECOVERY_FAILED", "rule_ids": ["ASH-RECOVERY-ACTION-001", "ASH-FALLBACK-SELECTION-001"],
                         "origin_predicate_evidence_reference": None, "active_recovery_category": "FALLBACK_REQUIRED"}
        self.reject(authorization, lambda x: x.update(failed_outcome="BLOCKED"), "const", ("failed_outcome",), "FallbackRouteAuthorization")
        canonical = decision(assessments()[7], action="CORRECT", outcome="BLOCKED")["diagnostic"]
        self.reject(canonical, lambda x: x.update(recovery_category="FALLBACK_REQUIRED"), "const", ("recovery_category",), "RecoveryDiagnostic")

    def test_actual_recovered_packets_keep_their_source_required_proof_on_wire(self):
        from tests.test_m3_recovery import RecoveryIntegrationTests, known_correction, operation
        fixture = RecoveryIntegrationTests()
        fixture.setUp()
        _, origin, engine, *_ = fixture.fixture()
        normalized = engine.recover(origin, operation_context=operation(origin)).to_record()
        self.assertEqual(normalized["outcome"], "RECOVERED_VALUE")
        self.reject(normalized, lambda x: x.update(normalization_preparation=None), "type", ("normalization_preparation",))
        _, origin, engine, _, _, provider, *_ = fixture.fixture(known=True)
        provider.result = known_correction(origin, (fixture.g1,), 0)
        corrected = engine.recover(origin, operation_context=operation(origin)).to_record()
        self.assertEqual(corrected["outcome"], "RECOVERED_VALUE")
        self.reject(corrected, lambda x: x.update(correction_observation=None), "type", ("correction_observation",))

    def test_authorized_fallback_keeps_actual_unavailable_correction_evidence(self):
        from core.ash_pattern_engine import recovery_values as r
        from tests.test_m3_recovery import RecoveryIntegrationTests, ash, operation
        fixture = RecoveryIntegrationTests()
        fixture.setUp()
        entry = r.FallbackPolicyEntry("FALLBACK-TEST-001", (), ash(0), 0, (), "TRY_NEXT", ("Declared test policy.",))
        _, origin, engine, *_ = fixture.fixture(known=True, entries=(entry,))
        result = engine.recover(origin, operation_context=operation(origin)).to_record()
        self.assertEqual(result["outcome"], "RECOVERED_FALLBACK_VALUE")
        self.reject(result, lambda x: x.update(correction_observation=None), "type", ("correction_observation",))

    def test_child_completion_failures_keep_complete_assessment_without_success(self):
        child = assessments()[5]
        linked = {"link": {"parent_operation_reference": "operation:authored", "parent_action_reference": "action:authored", "originating_chain_root_reference": "origin:detection"},
                  "candidate_state": child["parsed_state"], "context_observation": operation(child)["context_observation"], "assessment": child, "capture_status": "REJECTED"}
        self.accept(linked, "LinkedPostAssessment")
        linked["capture_status"] = "NOT_CONFIRMED"
        self.accept(linked, "LinkedPostAssessment")
        captured = deepcopy(linked)
        captured["assessment"] = assessments()[17]
        self.reject(captured, lambda x: x.update(capture_status="COMPLETE"), "enum", ("capture_status",), "LinkedPostAssessment")

    def test_recovery_rule_scope_and_ten_field_shape_remain_closed(self):
        envelope = packet()["emitted_diagnostics"][0]["envelope"]
        self.assertEqual(len(envelope), 10)
        for rule in ("ASH-CONTAINMENT-TRIGGER-001", "ASH-HALT-TRIGGER-001", "ASH-META-GENERAL-001"):
            self.reject(envelope, lambda x, r=rule: x.update(rule_ids=[r]), "enum", ("rule_ids", 0), "RecoveryEnvelope")
        for separator in ("\r", "\n", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            self.reject(envelope, lambda x, s=separator: x.update(summary="first" + s + "second"), "not", ("summary",), "RecoveryEnvelope")

    def test_branch_failure_retains_primary_and_secondary_completion_fields(self):
        p = packet()
        p.update(outcome="FAILURE", origin_validation=comparison(p["origin_assessment"], status="REJECTED"), action_decisions=[], emitted_diagnostics=[], candidate_state=None)
        p["failure_detail"] = {"failure_code": "ORIGIN_REJECTED", "field_name": "origin_validation", "submitted_evidence": p["origin_validation"],
            "attempted_diagnostic": None, "capture_status": None, "pending_directive": None, "reason": "Actual pure comparison refused origin.",
            "completion_failure_code": None, "unconfirmed_completion_observation": None}
        self.accept(p)
        self.reject(p, lambda x: x["failure_detail"].pop("completion_failure_code"), "required", ("failure_detail",))
        self.reject(p, lambda x: x["failure_detail"].update(failure_code="UNKNOWN_FAILURE"), "enum", ("failure_detail", "failure_code"))
        self.reject(p, lambda x: x["failure_detail"].update(field_name="arbitrary.path"), "enum", ("failure_detail", "field_name"))

    def test_independently_authored_tracked_roots_cover_all_five_outcomes(self):
        directory = ROOT / "examples/core_state_recovery"
        recovery = json.loads((directory / "recovery_cases.example.json").read_text(encoding="utf-8"))
        snapshots = json.loads((directory / "fallback_registry_cases.example.json").read_text(encoding="utf-8"))
        self.assertEqual({p["outcome"] for p in recovery},
                         {"NO_ACTION", "RECOVERED_VALUE", "RECOVERED_FALLBACK_VALUE", "HANDOFF_REQUIRED", "FAILURE"})
        for index, p in enumerate(recovery):
            with self.subTest(recovery=index): self.accept(p)
        for index, p in enumerate(snapshots):
            with self.subTest(registry=index): self.accept(p, registry=True)


if __name__ == "__main__":
    unittest.main()
