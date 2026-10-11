"""Authored N3 closed wire controls independent of lifecycle execution."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


ROOT = Path(__file__).resolve().parents[1]
SESSION_ID = "https://ywe.local/schemas/m3_session_lifecycle_schema.json"
EXAMPLE = ROOT / "examples/core_session_lifecycle/session_cases.example.json"
REJECTIONS = ROOT / "examples/core_session_lifecycle/session_rejections.example.json"
INVENTORY = ROOT / "docs/design-planning/m3/session-lifecycle/BUSINESS_API_INVENTORY.json"


def deny_retrieval(uri):
    raise NoSuchResource(ref=uri)


def schemas():
    documents = {}
    registry = Registry(retrieve=deny_retrieval)
    for path in (ROOT / "data/schemas").glob("m3_*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        documents[document["$id"]] = document
        registry = registry.with_resource(document["$id"], Resource.from_contents(document))
    return documents, registry


class SessionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.registry = schemas()
        cls.document = cls.documents[SESSION_ID]
        cls.catalog = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        cls.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in cls.catalog["cases"]}

    def validator(self, definition):
        return Draft202012Validator({"$ref": SESSION_ID + "#/$defs/" + definition}, registry=self.registry)

    def assertRejected(self, definition, value, path=None, keyword=None):
        errors = list(self.validator(definition).iter_errors(value))
        self.assertTrue(errors, (definition, value))
        if path is not None or keyword is not None:
            def descend(error):
                yield error
                for child in error.context:
                    yield from descend(child)
            leaves = [child for error in errors for child in descend(error)]
            matched = [error for error in leaves if
                (path is None or list(error.absolute_path) == path) and
                (keyword is None or error.validator == keyword)]
            self.assertTrue(matched, [(list(error.absolute_path), error.validator) for error in leaves])

    def specimen(self, case_id):
        return deepcopy(self.cases[case_id]["value"])

    def test_metaschema_and_all_refs_resolve_from_only_local_resources(self):
        Draft202012Validator.check_schema(self.document)
        def walk(value):
            if type(value) is dict:
                if "$ref" in value:
                    self.registry.resolver(SESSION_ID).lookup(value["$ref"])
                for child in value.values():
                    walk(child)
            elif type(value) is list:
                for child in value:
                    walk(child)
        walk(self.document)

    def test_all_38_adopted_types_are_explicit_closed_or_api_only(self):
        api_only = {"SessionContractError", "SessionExecutionGate", "SessionRetentionHandle", "SessionStageGrant"}
        self.assertEqual(len(self.inventory["types"]), 38)
        for name, fields in self.inventory["types"].items():
            definition = self.document["$defs"][name]
            with self.subTest(value=name):
                if name in api_only:
                    self.assertEqual(definition["not"], {})
                    for attempted in ({}, None, {"construction": "caller"}):
                        self.assertRejected(name, attempted)
                else:
                    self.assertEqual(definition["required"], list(fields))
                    self.assertEqual(list(definition["properties"]), list(fields))
                    self.assertIs(definition["additionalProperties"], False)

    def test_46_authored_cases_cover_all_34_wire_types_and_all_triggers(self):
        self.assertEqual(len(self.cases), 46)
        api_only = {"SessionContractError", "SessionExecutionGate", "SessionRetentionHandle", "SessionStageGrant"}
        self.assertEqual({case["schema_definition"] for case in self.cases.values()},
                         set(self.inventory["types"]) - api_only)
        for case in self.cases.values():
            with self.subTest(case=case["case_id"]):
                errors = list(self.validator(case["schema_definition"]).iter_errors(case["value"]))
                self.assertEqual([(list(error.absolute_path), error.validator) for error in errors], [])
        source = self.documents["https://ywe.local/schemas/m3_recovery_value_schema.json"]
        for domain, name in (("CanonicalContainmentTrigger", "ContainmentDiagnostic"),
                             ("CanonicalSafeHaltTrigger", "SafeHaltDiagnostic")):
            self.assertEqual({case["value"]["trigger"] for case in self.cases.values()
                              if case["schema_definition"] == name},
                             set(source["$defs"][domain]["enum"]))

    def test_catalog_wrapper_validates_without_a_lifecycle_execution_claim(self):
        errors = list(self.validator("SessionLifecycleCaseCatalog").iter_errors(self.catalog))
        self.assertEqual([(list(error.absolute_path), error.validator) for error in errors], [])

    def test_authored_rejection_catalog_validates_wrapper_and_every_declared_refusal(self):
        catalog = json.loads(REJECTIONS.read_text(encoding="utf-8"))
        self.validator("SessionLifecycleRejectionCatalog").validate(catalog)
        self.assertEqual(len(catalog["cases"]), 122)
        self.assertEqual(len({case["case_id"] for case in catalog["cases"]}), len(catalog["cases"]))
        for case in catalog["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertRejected(case["schema_definition"], case["value"],
                                    case["expected_path"], case["expected_keyword"])

    def test_unknown_and_missing_fields_refuse_every_authored_wire_type(self):
        for case in self.cases.values():
            name, original = case["schema_definition"], case["value"]
            unknown = deepcopy(original)
            unknown["caller_extension"] = True
            with self.subTest(case=case["case_id"], mutation="unknown"):
                self.assertRejected(name, unknown, [], "additionalProperties")
            missing = deepcopy(original)
            del missing[next(iter(self.document["$defs"][name]["properties"]))]
            with self.subTest(case=case["case_id"], mutation="required"):
                self.assertRejected(name, missing, [], "required")

    def test_current_full_vector_and_exact_policy_reject_each_mutated_field(self):
        for binding, case_id in (("canonical_binding", "SessionBinding"), ("policy_binding", "SessionBinding")):
            original = self.specimen(case_id)
            for field in original[binding]:
                altered = deepcopy(original)
                altered[binding][field] = "unapproved" if not field.endswith("sha256") else "f" * 64
                with self.subTest(binding=binding, field=field):
                    self.assertRejected("SessionBinding", altered, [binding, field], "const")
        paired = self.specimen("SessionBinding")
        paired["recovery_binding"]["canonical_binding"]["aggregate_sha256"] = "f" * 64
        self.assertRejected("SessionBinding", paired,
            ["recovery_binding", "canonical_binding", "aggregate_sha256"], "const")

    def test_reused_predicate_schema_accepts_exact_legacy_and_current_aggregates(self):
        schema_id = "https://ywe.local/schemas/m3_state_assessment_schema.json"
        validator = Draft202012Validator({"$ref": schema_id + "#/$defs/PredicateBinding"}, registry=self.registry)
        current = self.specimen("SessionOperationResult:complete-child")["origin_assessment"]
        predicate = current["classification_evidence"]["correction_path_is_known"]["binding"]
        validator.validate(predicate)
        legacy_packets = json.loads((ROOT / "examples/core_state_assessment/state_assessment_cases.example.json").read_text())
        legacy = next(packet for packet in legacy_packets if packet["outcome"] == "assessment")
        validator.validate(legacy["classification_evidence"]["correction_path_is_known"]["binding"])
        unknown = deepcopy(predicate)
        unknown["ash_aggregate_sha256"] = "f" * 64
        errors = list(validator.iter_errors(unknown))
        self.assertEqual([(list(error.path), error.validator) for error in errors],
                         [(["ash_aggregate_sha256"], "enum")])

    def test_snapshot_terminal_truth_scalar_limits_and_reference_domain(self):
        for field, replacement, keyword in (("generation", True, "type"),
                ("generation", 1 << 64, "maximum"), ("generation", -1, "minimum"),
                ("snapshot_reference", "SELF", "not"), ("snapshot_reference", "a\nb", "not"),
                ("snapshot_reference", "é", "pattern")):
            altered = self.specimen("SessionSnapshot")
            altered[field] = replacement
            self.assertRejected("SessionSnapshot", altered, [field], keyword)
        altered = self.specimen("SessionDeniedAttempt")["frozen_snapshot"]
        altered["current_assessment_reference"] = "authored:stale"
        self.assertRejected("SessionSnapshot", altered, ["current_assessment_reference"], "type")
        altered = self.specimen("SessionSnapshot")
        altered["current_assessment_reference"] = None
        self.assertRejected("SessionSnapshot", altered, ["observed_system_state_class"], "type")

    def test_request_tags_resolution_route_and_target_proof(self):
        for name in ("SessionRecoveryRequest", "SessionContainmentRequest", "SessionResolutionRequest", "SessionHaltRequest"):
            altered = self.specimen(name)
            altered["request"]["action"] = "REQUEST_HALT" if name != "SessionHaltRequest" else "RECOVER"
            self.assertRejected(name, altered, ["request", "action"], "const")
        altered = self.specimen("SessionResolutionRequest")
        altered["route"] = "ESCALATE_TO_SAFE_HALT"
        self.assertRejected("SessionResolutionRequest", altered, ["route"], "enum")
        altered = self.specimen("ResolutionTargetValidation")
        altered["prospective_context"]["is_in_containment"] = True
        self.assertRejected("ResolutionTargetValidation", altered,
            ["prospective_context", "is_in_containment"], "const")
        altered = self.specimen("ResolutionTargetValidation")
        altered["target_diagnostic"]["is_valid"] = False
        self.assertRejected("ResolutionTargetValidation", altered, ["target_diagnostic", "is_valid"], "const")

    def test_each_trigger_requires_exact_rule_and_measured_clock(self):
        for case in self.cases.values():
            name = case["schema_definition"]
            if name not in ("ContainmentDiagnostic", "SafeHaltDiagnostic"):
                continue
            changed = deepcopy(case["value"])
            changed["rule_ids"] = ["ASH-CONTAINMENT-TRIGGER-001" if name == "SafeHaltDiagnostic"
                                    else "ASH-HALT-TRIGGER-001"]
            with self.subTest(case=case["case_id"], mutation="trigger-map"):
                self.assertRejected(name, changed, ["rule_ids"], "const")
            clock = "halt_time" if name == "SafeHaltDiagnostic" else "containment_time"
            changed = deepcopy(case["value"])
            changed[clock] = {"observed_utc": None, "monotonic_nanoseconds": None,
                              "utc_reason": "CLOCK_UNAVAILABLE", "monotonic_reason": "CLOCK_UNAVAILABLE"}
            with self.subTest(case=case["case_id"], mutation="clock"):
                self.assertRejected(name, changed, [clock, "monotonic_nanoseconds"], "type")

    def test_exact_ten_fields_stage_and_rule_producer_domains(self):
        record = self.specimen("LifecycleRecord")
        self.assertEqual(len(record["envelope"]), 10)
        record["envelope"]["stage"] = "RECOVERY"
        self.assertRejected("LifecycleRecord", record, ["envelope", "stage"], "const")
        record = self.specimen("LifecycleRecord")
        record["envelope"]["rule_ids"] = ["invented:rule"]
        self.assertRejected("LifecycleRecord", record, ["envelope", "rule_ids", 0], "enum")
        recovery = self.documents["https://ywe.local/schemas/m3_recovery_value_schema.json"]
        assessment = self.documents["https://ywe.local/schemas/m3_state_assessment_schema.json"]
        self.assertEqual(len(recovery["$defs"]["N2RuleID"]["enum"]), 8)
        self.assertEqual(len(assessment["$defs"]["RuleIDs"]["items"]["enum"]), 6)
        self.assertEqual(len(self.document["$defs"]["DiagnosticEnvelope"]["properties"]["rule_ids"]["items"]["enum"]), 17)

    def test_amended_evidence_union_stays_closed_and_preserves_zero_emission_capture(self):
        cases = [self.specimen("SessionOperationResult:" + suffix) for suffix in
                 ("complete-child", "partial-child", "zero-emission-child", "unavailable-fresh-facts")]
        self.assertEqual(cases[2]["origin_assessment"]["emitted_diagnostics"], [])
        self.assertIsNotNone(cases[2]["origin_assessment"]["attempted_diagnostic"])
        for value in cases:
            errors = list(self.validator("SessionExecuteReturn").iter_errors(value))
            self.assertEqual([(list(error.absolute_path), error.validator) for error in errors], [])
        changed = deepcopy(cases[3])
        changed["failure_detail"]["primary_evidence"]["invented_source"] = "caller"
        self.assertRejected("SessionOperationResult", changed)

    def test_actual_owner_containment_resolution_halt_denial_and_history_wire(self):
        from tests import test_m3_session_lifecycle as lifecycle
        _, _, session, *_ = lifecycle.assembly()
        for build in (lifecycle.contain_command, lifecycle.resolve_command, lifecycle.halt_command):
            actual = session.execute(build(session))
            self.assertEqual(actual.status, "COMPLETED")
            self.validator("SessionExecuteReturn").validate(actual.to_record())
        denial = session.execute(object())
        self.assertEqual(denial.request_observation, "NOT_INSPECTED_AT_TERMINAL")
        self.validator("SessionExecuteReturn").validate(denial.to_record())
        history = session.history()
        self.assertTrue(history.frozen)
        self.validator("SessionHistory").validate(history.to_record())

    def test_actual_owner_direct_risk_boundary_wire_has_no_invented_authority(self):
        from tests import test_m3_session_lifecycle as lifecycle
        from core.ash_pattern_engine import session_values as values
        _, _, session, *_ = lifecycle.assembly()
        submitted = lifecycle.request(session, "n3:wire:direct-risk", "REQUEST_CONTAINMENT")
        boundary = lifecycle.boundary(submitted, "PROPAGATION_RISK")
        command = values.SessionContainmentRequest(submitted, "PROPAGATION_RISK", None, (boundary,), None)
        actual = session.execute(command)
        self.assertEqual(actual.status, "COMPLETED")
        self.assertEqual(actual.cause.kind, "PROPAGATION_RISK_BOUNDARY")
        self.assertIsNone(actual.cause.authority_observation)
        self.assertIsNone(actual.cause.recovery_operation_reference)
        self.validator("SessionExecuteReturn").validate(actual.to_record())


if __name__ == "__main__":
    unittest.main()
