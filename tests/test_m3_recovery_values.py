"""Independent source/contract controls for N2 values and pure registry."""
from copy import copy
from dataclasses import FrozenInstanceError, replace
import hashlib
import inspect
from pathlib import Path
import unittest
from unittest import mock

from core.ash_pattern_engine import recovery_values as r
from core.ash_pattern_engine import state_values as s
from core.ash_pattern_engine.fallback_registry import FallbackRegistry
from core.ash_pattern_engine.state_model import RecordingDiagnosticCapture, StateModel
from tests.test_m3_state_model import canonical_record, diagnostic_context, evidence, profile_binding


ROOT = Path(__file__).resolve().parents[1]
ZERO = s.AshState((0,) * 9)
G1 = s.AshState((1, 1, 1, 1, 0, 0, 0, 0, 0))
NONMEMBER = s.AshState((1,) * 9)


def source(reference="declared:test"):
    return r.EvidenceSourceBinding(reference, "a" * 64, reference + ":evidence")


def assembly():
    profile = profile_binding("recovery_values_test", ("000000000",))
    capture = RecordingDiagnosticCapture()
    return StateModel(profile, s.CanonicalAshBinding(**canonical_record()), capture), capture


def assess(model, candidate, reference, *, correction=None, fallback=None, context=None):
    dc = diagnostic_context(reference)
    subject = "ash_state_" + candidate.signature
    facts = evidence(model.profile_binding, dc, subject, correction, fallback)
    return model.assess(candidate, context=context or s.SystemContext(False, False),
                        classification_evidence=facts, diagnostic_context=dc)


def registry_binding(model):
    return r.RegistrySourceBinding("declared:registry", source("declared:registry"),
        model.profile_binding.profile_id, model.profile_binding.source_binding.source_sha256,
        model.canonical_binding.dependency_id, model.canonical_binding.aggregate_sha256)


def entry_and_cert(model, policy="FALLBACK-TEST-001", rank=0, conditions=(), *, context=None):
    entry = r.FallbackPolicyEntry(policy, conditions, ZERO, rank, (), "TRY_NEXT", ("Declared test policy.",))
    assessment = assess(model, ZERO, "certificate:" + policy, context=context)
    observation = r.ContextObservation(assessment.system_context, "declared:owner", "declared:context", source())
    return entry, r.CandidateCertification(policy, observation, assessment)


def observation(model, entry, condition, status="TRUE", *, reference="operation:test"):
    return r.PredicateObservation(status, condition, reference, "origin:degraded",
        "declared:registry", "a" * 64, entry.policy_id, "APPLICABILITY",
        entry.candidate_state_reference, source("provider:test"), "Declared predicate observation.")


def no_action_packet(model):
    origin = assess(model, ZERO, "origin:stable")
    context = r.RecoveryOperationContext("operation:test", "origin:stable",
        r.ContextObservation(origin.system_context, "owner:test", "context:test", source()),
        r.PropagationEvidence("SAFE", "operation:test", "origin:stable", source(), "Explicit safe propagation."),
        r.ExternalAuthorityEvidence("UNAVAILABLE", "operation:test", "origin:stable", source(), "No authority observation."))
    diagnostic = r.RecoveryDiagnostic("NO_ACTION", "STABLE", origin.state_validity_diagnostic, (),
        "NOT_APPLICABLE", None, None, "Verified stable origin needs no action.", ("ASH-RECOVERY-ACTION-001",))
    decision = r.RecoveryActionDecision("decision:no_action", "NO_ACTION", diagnostic, (), None, None, None)
    envelope = s.DiagnosticEnvelope("RECOVERY", "INFO", "RECOVERY", "RESOLVED", origin.subject_reference,
        origin.emitted_diagnostics[-1].diagnostic_reference, origin.assessment_binding.diagnosis_reference,
        diagnostic.rule_ids, "No recovery action required.", ("The candidate is unchanged.",))
    record = r.RecoveryRecord("operation:test:decision", envelope, "OPERATION_DECISION", decision)
    binding = r.RecoverySourceBinding(model.canonical_binding, tuple(r.SourcePin(*pin) for pin in r.RECOVERY_CONTRACT_PIN_FIELDS))
    return r.RecoveryNoAction(context, origin, model.validate_assessment(origin), binding, None, None,
        (), (), (), (decision,), (record,), ZERO, None, None, None, None, None, None, None)


class RecoveryValueTests(unittest.TestCase):
    def setUp(self):
        self.model, self.capture = assembly()

    def test_actual_reviewed_contract_and_policy_pins(self):
        canonical = ROOT / "core/ash_pattern_engine/canonical"
        for path, expected in r.RECOVERY_CONTRACT_PIN_FIELDS:
            text = (canonical / path).read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), expected)
        policy = (ROOT / "docs/architecture/m3_recovery_safety_policy.md").read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        self.assertEqual(hashlib.sha256(policy.encode()).hexdigest(), r.RECOVERY_POLICY_BINDING_FIELDS[-1][1])

    def test_packet_headers_are_not_constructor_arguments(self):
        expected = {"operation_context", "origin_assessment", "origin_validation", "source_binding", "registry_binding", "route_authorization", "steps", "post_assessments", "policy_attempts", "action_decisions", "emitted_diagnostics", "candidate_state", "directive", "failure_detail", "normalization_preparation", "correction_observation", "registry_snapshot", "registry_validation", "completion_observation"}
        for cls in (r.RecoveryNoAction, r.RecoveredValue, r.RecoveredFallbackValue, r.RecoveryHandoff, r.RecoveryFailure):
            self.assertEqual(set(inspect.signature(cls).parameters), expected)

    def test_no_action_packet_has_exact_headers_and_one_unchanged_acknowledged_decision(self):
        packet = no_action_packet(self.model)
        wire = packet.to_record()
        self.assertEqual(len(wire), 25)
        self.assertEqual((wire["outcome"], wire["execution_scope"], wire["session_effects_performed"]),
            ("NO_ACTION", "CORE_REFERENCE_IMMUTABLE_VALUE", False))
        for changes in ({"action_decisions": packet.action_decisions * 2}, {"emitted_diagnostics": ()},
                        {"candidate_state": G1}, {"registry_snapshot": r.UnavailableFallbackRegistry(registry_binding(self.model), "Unavailable.")}):
            with self.subTest(changes=changes), self.assertRaises(r.RecoveryContractError):
                replace(packet, **changes)

    def test_confirmed_main_chain_cannot_change_subject_root_parent_or_severity_floor(self):
        packet = no_action_packet(self.model)
        record = packet.emitted_diagnostics[0]
        for changes in ({"subject_reference": "other:subject"}, {"chain_root_reference": "other:root"},
                        {"parent_diagnostic_reference": "other:parent"}):
            altered = replace(record, envelope=replace(record.envelope, **changes))
            with self.subTest(changes=changes), self.assertRaises(r.RecoveryContractError):
                replace(packet, emitted_diagnostics=(altered,))
        step = r.RecoveryStepEvidence(0, "NO_ACTION", "COMPLETED", None, None, None, None, None, None,
            "operation:test:step:0", "Declared observation before the final decision.")
        first = r.RecoveryRecord(step.diagnostic_reference,
            replace(record.envelope, severity="ERROR", disposition="PENDING"), "ACTION_VALUE_COMPUTED", step)
        second = replace(record, envelope=replace(record.envelope, parent_diagnostic_reference=first.diagnostic_reference))
        detail = r.RecoveryFailureDetail("COLLABORATOR_FAILED", "post_assessment", None, None, None, None, "Controlled failure.", None, None)
        fields = {name: getattr(packet, name) for name in inspect.signature(r.RecoveryFailure).parameters}
        fields.update(steps=(step,), emitted_diagnostics=(first, second), failure_detail=detail)
        with self.assertRaises(r.RecoveryContractError) as raised:
            r.RecoveryFailure(**fields)
        self.assertEqual(raised.exception.field_name, "emitted_diagnostics")

    def test_post_child_complete_semantics_retains_failed_completion_observation(self):
        child = assess(self.model, ZERO, "post:child")
        link = r.PostAssessmentLink("operation:test", "action:test", "origin:detection")
        observation = r.ContextObservation(child.system_context, "owner:test", "post:context", source())
        for status in ("COMPLETE", "REJECTED", "NOT_CONFIRMED"):
            with self.subTest(status=status):
                linked = r.LinkedPostAssessment(link, ZERO, observation, child, status)
                self.assertEqual((linked.assessment, linked.capture_status), (child, status))
        with self.assertRaises(r.RecoveryContractError):
            r.LinkedPostAssessment(link, G1, observation, child, "REJECTED")

    def test_recovered_values_cannot_discard_consulted_normalization_or_known_correction_proof(self):
        from tests.test_m3_recovery import RecoveryIntegrationTests, known_correction, operation
        fixture = RecoveryIntegrationTests()
        fixture.setUp()
        _, origin, engine, *_ = fixture.fixture()
        normalized = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(normalized.outcome, "RECOVERED_VALUE")
        with self.assertRaises(r.RecoveryContractError) as raised:
            replace(normalized, normalization_preparation=None)
        self.assertEqual(raised.exception.field_name, "normalization_preparation")
        _, origin, engine, _, _, provider, *_ = fixture.fixture(known=True)
        provider.result = known_correction(origin, (fixture.g1,), 0)
        corrected = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(corrected.outcome, "RECOVERED_VALUE")
        with self.assertRaises(r.RecoveryContractError) as raised:
            replace(corrected, correction_observation=None)
        self.assertEqual(raised.exception.field_name, "correction_observation")

    def test_after_correction_fallback_keeps_actual_unavailable_observation(self):
        from tests.test_m3_recovery import RecoveryIntegrationTests, ash, operation
        fixture = RecoveryIntegrationTests()
        fixture.setUp()
        entry = r.FallbackPolicyEntry("FALLBACK-TEST-001", (), ash(0), 0, (), "TRY_NEXT", ("Declared test policy.",))
        _, origin, engine, *_ = fixture.fixture(known=True, entries=(entry,))
        recovered = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(recovered.outcome, "RECOVERED_FALLBACK_VALUE")
        self.assertEqual(recovered.route_authorization.route, "AFTER_CORRECTION_FAILURE")
        self.assertIs(type(recovered.correction_observation.submitted), r.UnavailableCorrection)
        with self.assertRaises(r.RecoveryContractError) as raised:
            replace(recovered, correction_observation=None)
        self.assertEqual(raised.exception.field_name, "correction_observation")

    def test_known_correction_declared_nonmember_is_retained_then_purely_rejected(self):
        origin = assess(self.model, G1, "origin:correction", correction=True)
        supplied = r.KnownCorrection("correction:test", origin.assessment_binding.assessment_reference,
            source(), self.model.profile_binding.profile_id,
            self.model.profile_binding.source_binding.source_sha256, [NONMEMBER], ZERO,
            "Declared invalid member control.", origin.classification_evidence.correction_path_is_known.binding.evidence_reference,
            self.model.canonical_binding)
        self.assertEqual(supplied.chain, (NONMEMBER,))
        result = self.model.validate_known_correction(supplied, origin=origin)
        self.assertEqual((result.status, result.failure_code, result.field_name), ("REJECTED", "CHAIN_MEMBER_INVALID", "chain[0]"))
        self.assertEqual(result.submitted_correction, supplied)

    def test_known_chain_is_copied_and_bounded(self):
        origin = assess(self.model, G1, "origin:correction", correction=True)
        chain = [G1]
        supplied = r.KnownCorrection("correction:test", "origin:correction", source(), self.model.profile_binding.profile_id,
            self.model.profile_binding.source_binding.source_sha256, chain, ZERO, "Full supplied chain.",
            origin.classification_evidence.correction_path_is_known.binding.evidence_reference, self.model.canonical_binding)
        chain.clear()
        self.assertEqual(supplied.chain, (G1,))
        self.assertEqual(self.model.validate_known_correction(supplied, origin=origin).status, "VERIFIED")
        with self.assertRaises(r.RecoveryContractError):
            replace(supplied, chain=(G1,) * 17)
        with self.assertRaises(FrozenInstanceError):
            supplied.reason = "mutation"

    def test_actual_step_xor_requires_full_codeword_and_exact_result(self):
        step = r.RecoveryStepEvidence(0, "CORRECTION_XOR", "COMPLETED", G1, G1, ZERO, None, None, None, "step:0", "Actual XOR control.")
        self.assertEqual(step.after_state.bits, (0,) * 9)
        for change in ({"after_state": NONMEMBER}, {"codeword": NONMEMBER}, {"step_index": False}, {"step_index": 768}, {"status": "FAILED"}):
            with self.subTest(change=change), self.assertRaises(r.RecoveryContractError):
                replace(step, **change)

    def test_operation_evidence_cannot_name_another_origin(self):
        context = r.ContextObservation(s.SystemContext(False, False), "owner:test", "context:test", source())
        propagation = r.PropagationEvidence("SAFE", "operation:test", "origin:test", source(), "Explicit safety observation.")
        authority = r.ExternalAuthorityEvidence("UNAVAILABLE", "operation:test", "other:origin", source(), "Not observed.")
        with self.assertRaises(r.RecoveryContractError) as raised:
            r.RecoveryOperationContext("operation:test", "origin:test", context, propagation, authority)
        self.assertEqual(raised.exception.field_name, "operation_context")

    def test_source_pin_order_hash_and_cardinality_are_exact(self):
        pins = [r.SourcePin(*row) for row in r.RECOVERY_CONTRACT_PIN_FIELDS]
        accepted = r.RecoverySourceBinding(self.model.canonical_binding, pins)
        pins.reverse()
        self.assertEqual(accepted.contract_pins[0].path, "interfaces/contracts/recovery-engine-contract.md")
        for altered in (pins, accepted.contract_pins[:-1], (replace(accepted.contract_pins[0], sha256="b" * 64), *accepted.contract_pins[1:])):
            with self.assertRaises(r.RecoveryContractError):
                r.RecoverySourceBinding(self.model.canonical_binding, altered)

    def test_policy_request_is_typed_and_never_actual_mode_entry(self):
        policy = r.RecoverySafetyPolicyBinding(**dict(r.RECOVERY_POLICY_BINDING_FIELDS))
        directive = r.RecoveryDirective("ENTER_CONTAINMENT", "OPERATOR_REQUEST", "origin:test", "action:test", ("resolution:test",),
            "Typed policy request.", "POLICY", policy)
        self.assertEqual(directive.to_record()["actual_mode_status"], "NOT_ENTERED_BY_N2")
        for changes in ({"request_origin": "SOURCE_RECOVERABILITY"}, {"policy_binding": None}, {"trigger": "UNREACHABLE"}):
            with self.subTest(changes=changes), self.assertRaises(r.RecoveryContractError):
                replace(directive, **changes)

    def test_secondary_completion_detail_does_not_replace_primary_failure(self):
        detail = r.RecoveryFailureDetail("POST_EVIDENCE_UNAVAILABLE", "post_assessment", None, None, None, None,
            "Original missing evidence.", None, None)
        retained = replace(detail, completion_failure_code="COMPLETION_UNCONFIRMED")
        self.assertEqual((retained.failure_code, retained.reason), ("POST_EVIDENCE_UNAVAILABLE", "Original missing evidence."))
        self.assertEqual(len(retained.to_record()), 9)
        with self.assertRaises(r.RecoveryContractError):
            replace(detail, completion_failure_code="OTHER_FAILURE")

    def test_exact_type_guards_do_not_run_metaclass_equality_or_object_hooks(self):
        calls = []
        class HostileMeta(type):
            def __eq__(cls, other):
                calls.append("metaclass")
                return True
        class Hostile(metaclass=HostileMeta):
            def __getattribute__(self, name):
                calls.append("attribute")
                raise AssertionError("untrusted attribute hook")
        for invoke in (lambda: r.ContextObservation(Hostile(), "owner", "observation", source()),
                       lambda: r.RecoveryContractError("RECOVERY_PLAN_INVALID", "origin_assessment", validation=Hostile())):
            with self.assertRaises((r.RecoveryContractError, ValueError)):
                invoke()
        self.assertEqual(calls, [])


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.model, self.capture = assembly()
        self.origin = assess(self.model, NONMEMBER, "origin:degraded", fallback=True)

    def registry(self, entries_and_certifications):
        rows = tuple(entries_and_certifications)
        snapshot = r.AvailableFallbackRegistry(registry_binding(self.model), tuple(e for e, _ in rows), tuple(c for _, c in rows))
        return FallbackRegistry(snapshot, state_model=self.model)

    def test_available_empty_is_distinct_from_unavailable(self):
        empty = self.registry(())
        unavailable = FallbackRegistry(r.UnavailableFallbackRegistry(registry_binding(self.model), "Source explicitly unavailable."), state_model=self.model)
        self.assertEqual(empty.get_candidates(self.origin, applicability=()), ())
        self.assertEqual(unavailable.get_candidates(self.origin, applicability=()), ())
        self.assertEqual((empty.snapshot.availability, unavailable.snapshot.availability), ("AVAILABLE", "UNAVAILABLE"))

    def test_rank_then_ascii_id_order_includes_negative_rank(self):
        registry = self.registry((entry_and_cert(self.model, "FALLBACK-Z-001", 0), entry_and_cert(self.model, "FALLBACK-B-001", -2), entry_and_cert(self.model, "FALLBACK-A-001", 0)))
        self.assertEqual(tuple(e.policy_id for e in registry.ordered_entries()), ("FALLBACK-B-001", "FALLBACK-A-001", "FALLBACK-Z-001"))
        rows = tuple(r.EntryApplicability(e.policy_id, (), ()) for e in registry.ordered_entries())
        self.assertEqual(registry.get_candidates(self.origin, applicability=rows), registry.ordered_entries())

    def test_nonstable_source_certification_refuses_with_full_witness(self):
        entry, cert = entry_and_cert(self.model, context=s.SystemContext(False, True))
        snapshot = r.AvailableFallbackRegistry(registry_binding(self.model), (entry,), (cert,))
        with self.assertRaises(r.RecoveryContractError) as raised:
            FallbackRegistry(snapshot, state_model=self.model)
        witness = raised.exception.validation
        self.assertEqual(witness.failure_code, "CERTIFICATION_NOT_STABLE")
        self.assertEqual(witness.submitted_snapshot, snapshot)
        self.assertEqual(witness.candidate_validations[0].submitted_certification, cert)

    def test_invalid_target_is_not_repaired_or_replaced(self):
        entry, cert = entry_and_cert(self.model)
        snapshot = r.AvailableFallbackRegistry(registry_binding(self.model), (replace(entry, candidate_state_reference=G1),), (cert,))
        with self.assertRaises(r.RecoveryContractError) as raised:
            FallbackRegistry(snapshot, state_model=self.model)
        self.assertEqual(raised.exception.validation.failure_code, "TARGET_NOT_VALID")
        self.assertEqual(raised.exception.validation.candidate_validations[0].target_diagnostic.input_state, G1)

    def test_same_profile_id_hash_different_full_set_rejected_at_use(self):
        registry = self.registry((entry_and_cert(self.model),))
        profile = self.model.profile_binding.profile
        different = s.AvailableProfileBinding(replace(profile, recognized_valid_states=(ZERO, G1)))
        other = StateModel(different, self.model.canonical_binding, RecordingDiagnosticCapture())
        witness = registry.validate_for_model(other)
        self.assertEqual(witness.failure_code, "REGISTRY_PROFILE_MISMATCH")
        self.assertEqual(witness.current_profile_binding, different)
        self.assertEqual(witness.candidate_validations, ())

    def test_registry_source_structural_guards_precede_constructor_and_use_time_equality(self):
        touched = []
        class Hook:
            def __eq__(self, other):
                touched.append("equality")
                return True
            def __getattr__(self, name):
                touched.append("attribute")
                raise AssertionError("Foreign source attribute hook ran")
        valid = self.registry(())
        binding = valid.snapshot.source_binding

        def forged(value, **changes):
            result = copy(value)
            for name, child in changes.items():
                object.__setattr__(result, name, child)
            return result

        cases = [
            (forged(binding, ash_aggregate_sha256=Hook()), "REGISTRY_SOURCE_MISMATCH", "registry.source_binding"),
            (forged(binding, profile_source_sha256=Hook()), "REGISTRY_PROFILE_MISMATCH", "profile_binding"),
            (forged(binding, profile_id=Hook()), "REGISTRY_PROFILE_MISMATCH", "profile_binding"),
            (Hook(), "REGISTRY_SOURCE_MISMATCH", "registry.source_binding"),
            (forged(binding, source_binding=Hook()), "REGISTRY_SOURCE_MISMATCH", "registry.source_binding"),
        ]
        for leaf in ("source_reference", "source_sha256", "evidence_reference"):
            cases.append((forged(binding, source_binding=forged(binding.source_binding, **{leaf: Hook()})),
                          "REGISTRY_SOURCE_MISMATCH", "registry.source_binding"))
        with mock.patch.object(self.capture, "begin", wraps=self.capture.begin) as opened:
            for submitted_binding, code, field in cases:
                with self.subTest(code=code, field=field):
                    submitted = forged(valid.snapshot, source_binding=submitted_binding)
                    with self.assertRaises(r.RecoveryContractError) as raised:
                        FallbackRegistry(submitted, state_model=self.model)
                    witness = raised.exception.validation
                    self.assertIs(type(witness), r.RegistryValidation)
                    self.assertEqual((witness.status, witness.failure_code, witness.field_name),
                                     ("REJECTED", code, field))
                    self.assertIs(witness.submitted_snapshot, submitted)
                    at_use = forged(valid, _snapshot=submitted).validate_for_model(self.model)
                    self.assertEqual((at_use.status, at_use.failure_code, at_use.field_name),
                                     ("REJECTED", code, field))
                    self.assertIs(at_use.submitted_snapshot, submitted)
                    self.assertEqual(at_use.candidate_validations, ())
                    self.assertEqual(touched, [])
        opened.assert_not_called()

    def test_applicability_requires_whole_declared_prefix_and_stops_at_false(self):
        conditions = (r.ConditionReference("condition:a", source("condition:a")), r.ConditionReference("condition:b", source("condition:b")))
        registry = self.registry((entry_and_cert(self.model, conditions=conditions),))
        entry = registry.ordered_entries()[0]
        false = observation(self.model, entry, conditions[0], "FALSE")
        accepted = r.EntryApplicability(entry.policy_id, (false,), conditions[1:])
        self.assertEqual(registry.get_candidates(self.origin, applicability=(accepted,)), ())
        for row in (replace(accepted, unconsulted_conditions=()),
                    replace(accepted, observations=(replace(false, status="TRUE"),)),
                    replace(accepted, observations=(false, observation(self.model, entry, conditions[1])), unconsulted_conditions=())):
            with self.subTest(row=row), self.assertRaises(r.RecoveryContractError):
                registry.get_candidates(self.origin, applicability=(row,))

    def test_predicate_origin_registry_candidate_and_operation_bindings_fail_closed(self):
        condition = r.ConditionReference("condition:a", source())
        registry = self.registry((entry_and_cert(self.model, conditions=(condition,)),))
        entry = registry.ordered_entries()[0]
        true = observation(self.model, entry, condition)
        for changes in ({"origin_assessment_reference": "other:origin"}, {"registry_id": "other:registry"}, {"registry_source_sha256": "b" * 64}, {"candidate_state_reference": G1}, {"status": "UNAVAILABLE"}):
            row = r.EntryApplicability(entry.policy_id, (replace(true, **changes),), ())
            with self.subTest(changes=changes), self.assertRaises(r.RecoveryContractError):
                registry.get_candidates(self.origin, applicability=(row,))

    def test_registry_direct_precondition_is_degraded_only_and_never_captures(self):
        registry = self.registry((entry_and_cert(self.model),))
        stable = assess(self.model, ZERO, "origin:stable")
        rows = (r.EntryApplicability("FALLBACK-TEST-001", (), ()),)
        with self.assertRaises(r.RecoveryContractError):
            registry.get_candidates(stable, applicability=rows)
        with mock.patch.object(self.capture, "begin", wraps=self.capture.begin) as opened:
            registry.get_candidates(self.origin, applicability=rows)
        opened.assert_not_called()

    def test_integer_and_policy_id_boundaries_are_owned(self):
        entry, _ = entry_and_cert(self.model)
        for rank in (False, -(1 << 63) - 1, 1 << 63, 1.0):
            with self.subTest(rank=rank), self.assertRaises(r.RecoveryContractError):
                replace(entry, ordering_rank=rank)
        for policy in ("FALLBACK-TEST-000", "FALLBACK-test-001", "FALLBACK-TEST-1000"):
            with self.subTest(policy=policy), self.assertRaises(r.RecoveryContractError):
                replace(entry, policy_id=policy)

    def test_snapshot_certification_inventory_duplicates_and_order(self):
        a = entry_and_cert(self.model, "FALLBACK-A-001")
        b = entry_and_cert(self.model, "FALLBACK-B-001")
        binding = registry_binding(self.model)
        for entries, certs in (((a[0], a[0]), (a[1], a[1])), ((a[0], b[0]), (b[1], a[1])), ((a[0],), ())):
            with self.assertRaises(r.RecoveryContractError):
                r.AvailableFallbackRegistry(binding, entries, certs)


if __name__ == "__main__":
    unittest.main()
