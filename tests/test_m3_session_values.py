"""Closed N3 values, raw publication bounds and local capability guards.

These tests use real StateModel evidence and explicitly synthetic authority,
clock and capture responses. They establish representation, not host authority.
"""
from __future__ import annotations

import copy
from dataclasses import fields, replace, FrozenInstanceError
import hashlib
import json
from pathlib import Path
import unittest

from core.ash_pattern_engine import session_values as v
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine import recovery_values as rv
from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import normalization_values as nv
from core.ash_pattern_engine.normalization import RecordingNormalizationCapture
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from core.ash_pattern_engine.recovery import RecoveryEngine
from core.ash_pattern_engine.session import ReferenceSessionLifecycle
from core.ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics
from tests import test_m3_recovery as n2
from tests import test_m3_reference_diagnostics as reference


ROOT = Path(__file__).resolve().parents[1]


def values_fixture():
    source = sv.CanonicalAshBinding(**dict(dict(sv.CANONICAL_BINDING_BASELINES)["N3_LIFECYCLE"]))
    profile = n2.profile()
    model = StateModel(profile, source, RecordingDiagnosticCapture())
    origin = n2.assessment(model, n2.ash(0), reference="n3:value:initial")
    recovery = rv.RecoverySourceBinding(source, tuple(rv.SourcePin(path, digest)
        for path, digest in rv.recovery_contract_pin_fields(source)))
    policy = v.SessionPolicyBinding(**dict(v.SESSION_POLICY_BINDING_FIELDS))
    binding = v.SessionBinding("n3:value:binding", "n3:value:session", source, recovery,
        profile, policy, origin.assessment_binding.assessment_reference)
    snapshot = v.SessionSnapshot("n3:value:snapshot:0", binding, 0, n2.ash(0), "NORMAL",
        False, "OPEN", None, None, False, None,
        origin.assessment_binding.assessment_reference, "STABLE")
    return model, origin, binding, snapshot


def request(snapshot, action="REQUEST_CONTAINMENT", reference="n3:value:command"):
    return v.SessionRequest(reference, snapshot.binding.session_reference, snapshot,
        action, "Explicit synthetic value request.")


def authority(submitted):
    return v.SessionAuthorityObservation(submitted.request_reference,
        submitted.expected_snapshot.snapshot_reference, "AUTHORIZED", "OPERATOR",
        n2.evidence_source("n3:value:authority"), "n3:value:authority:observation",
        "Synthetic authority; this record does not authenticate it.")


def refused_result(command, origin=None, primary=None):
    submitted = command.request
    before = submitted.expected_snapshot
    failure = v.SessionFailureDetail("SESSION_ORIGIN_REJECTED", "origin_assessment",
        primary, None, None, None, None, None, "Actual structural refusal evidence.")
    admission = v.SessionAdmission("REJECTED", submitted, before, None,
        "SESSION_ORIGIN_REJECTED", "origin_assessment", "No effect admitted.")
    observed = v.SessionContextObservation("n3:value:context", before,
        submitted.request_reference, before.current_state, True, False, False)
    return v.SessionOperationResult(command, "REFUSED", before, before, False,
        admission, observed, command.authority_observation, None, origin, None,
        None, None, (), (), None, None, None, failure, None, None)


class SessionValueTests(unittest.TestCase):
    def setUp(self):
        self.model, self.origin, self.binding, self.snapshot = values_fixture()

    def assertRefuses(self, callback, code=None):
        with self.assertRaises(v.SessionContractError) as caught:
            callback()
        if code is not None:
            self.assertEqual(caught.exception.failure_code, code)
        self.assertIn(caught.exception.field_name, v.SESSION_FIELD_PATHS)
        return caught.exception

    def command(self, snapshot=None):
        submitted = request(self.snapshot if snapshot is None else snapshot)
        return v.SessionContainmentRequest(submitted, "OPERATOR_REQUEST",
            authority(submitted), (), None)

    def test_every_adopted_wire_value_has_exact_inventory_fields(self):
        inventory = json.loads((ROOT / "docs/design-planning/m3/session-lifecycle/BUSINESS_API_INVENTORY.json").read_text())
        self.assertEqual(len(inventory["types"]), 38)
        api_only = {"SessionContractError", "SessionExecutionGate", "SessionRetentionHandle", "SessionStageGrant"}
        for name, names in inventory["types"].items():
            with self.subTest(value=name):
                kind = getattr(v, name)
                if name not in api_only:
                    expected = list(names) + (['module_history'] if name == 'SessionHistory' else [])
                    self.assertEqual([field.name for field in fields(kind)], expected)
        self.assertEqual(len(v._SESSION_TYPES), 34)

    def test_policy_pin_is_actual_normalized_adopted_file(self):
        policy = (ROOT / "docs/architecture/m3_session_lifecycle_policy.md").read_text(encoding="utf-8-sig")
        digest = hashlib.sha256(policy.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()
        self.assertEqual(self.binding.policy_binding.source_sha256, digest)
        for field in fields(v.SessionPolicyBinding):
            with self.subTest(field=field.name):
                replacement = "f" * 64 if field.name == "source_sha256" else "unapproved"
                self.assertRefuses(lambda: replace(self.binding.policy_binding, **{field.name: replacement}))

    def test_n3_binding_rejects_all_earlier_complete_vectors(self):
        for baseline, vector in sv.CANONICAL_BINDING_BASELINES:
            if baseline == "N3_LIFECYCLE":
                continue
            old = sv.CanonicalAshBinding(**dict(vector))
            paired = rv.RecoverySourceBinding(old, tuple(rv.SourcePin(path, digest)
                for path, digest in rv.recovery_contract_pin_fields(old)))
            with self.subTest(baseline=baseline):
                self.assertRefuses(lambda: replace(self.binding, canonical_binding=old,
                    recovery_binding=paired), "SESSION_SOURCE_REJECTED")

    def test_revalidation_catches_each_mutated_full_source_field(self):
        for field in fields(sv.CanonicalAshBinding):
            damaged = copy.deepcopy(self.binding)
            object.__setattr__(damaged.canonical_binding, field.name,
                "unrecognized" if field.name == "dependency_id" else "f" * 64)
            with self.subTest(field=field.name):
                self.assertRefuses(lambda: v.revalidate_value(damaged))

    def test_snapshot_truth_and_generation_are_exact(self):
        failed = replace(self.snapshot, observed_system_state_class="FAILED")
        running = v.SessionContextObservation("n3:value:failed-context", failed,
            "n3:value:failed-command", failed.current_state, True, False, False)
        self.assertTrue(running.is_running)
        contained = replace(self.snapshot, mode="CONTAINED", containment_reference="n3:value:containment",
            observed_system_state_class="CONTAINED")
        self.assertTrue(v.SessionContextObservation("n3:value:contained-context", contained,
            "n3:value:contained-command", contained.current_state, True, True, False).is_running)
        for patch in ({"generation": True}, {"generation": -1}, {"generation": 1 << 64},
                      {"current_assessment_reference": None}, {"terminal_latched": True},
                      {"mode": "CONTAINED"}, {"observed_system_state_class": "SAFE_HALT"}):
            with self.subTest(patch=patch):
                self.assertRefuses(lambda: replace(self.snapshot, **patch))
        maximum = replace(self.snapshot, generation=v.MAX_GENERATION)
        self.assertEqual(maximum.generation, (1 << 64) - 1)

    def test_terminal_snapshot_drops_live_origin_and_context_is_truthful(self):
        terminal = replace(self.snapshot, snapshot_reference="n3:value:terminal", mode="SAFE_HALT",
            terminal_latched=True, admission_status="TERMINAL", halt_reference="n3:value:halt",
            current_assessment_reference=None, observed_system_state_class=None)
        observed = v.SessionContextObservation("n3:value:terminal-context", terminal,
            "n3:value:halt-command", terminal.current_state, False, False, True)
        self.assertFalse(observed.is_running)
        self.assertRefuses(lambda: replace(observed, is_running=True))
        self.assertRefuses(lambda: replace(terminal, current_assessment_reference="n3:value:old-origin",
            observed_system_state_class="SAFE_HALT"))

    def test_command_reference_and_reason_bounds(self):
        submitted = request(self.snapshot)
        self.assertEqual(len(replace(submitted, request_reference="a" * 160).request_reference), 160)
        self.assertEqual(len(replace(submitted, reason="🚀" * 512).reason), 512)
        for patch in ({"request_reference": "a" * 161}, {"request_reference": "NONE"},
                      {"request_reference": "SELF"}, {"request_reference": "é"},
                      {"request_reference": "a\nb"}, {"reason": "x" * 513},
                      {"reason": ""}, {"reason": "x\0y"}):
            with self.subTest(patch=patch):
                self.assertRefuses(lambda: replace(submitted, **patch))

    def test_nested_evidence_must_match_the_primary_full_snapshot_reference(self):
        command = self.command()
        for patch in ({"request_reference": "n3:value:another"},
                      {"expected_snapshot_reference": "n3:value:another-snapshot"}):
            mismatched = replace(command.authority_observation, **patch)
            self.assertRefuses(lambda: replace(command, authority_observation=mismatched),
                "SESSION_EVIDENCE_MISMATCH")
        boundary = v.SessionBoundaryObservation(command.request.request_reference,
            self.snapshot.snapshot_reference, "PROPAGATION_RISK", "SATISFIED",
            n2.evidence_source(), "n3:value:boundary", "Synthetic boundary.")
        mutable = [boundary]
        sealed = replace(command, boundary_observations=mutable)
        mutable.clear()
        self.assertEqual(sealed.boundary_observations, (boundary,))
        with self.assertRaises(FrozenInstanceError):
            sealed.trigger = "FALLBACK_FAILURE"
        self.assertRefuses(lambda: replace(command, boundary_observations=(boundary, boundary)))

    def test_lease_preserves_before_generation_state_and_revision(self):
        submitted = request(self.snapshot)
        active = replace(self.snapshot, snapshot_reference="n3:value:active",
            active_operation_reference=submitted.request_reference)
        lease = v.SessionOperationLease("n3:value:lease", submitted, self.snapshot, "CONTAIN", active)
        v.revalidate_value(lease)
        for patch in ({"generation": 1}, {"current_state": n2.ash(1)},
                      {"current_assessment_reference": "n3:value:stale-origin"},
                      {"active_operation_reference": "n3:value:other-operation"}):
            self.assertRefuses(lambda: replace(lease, active_snapshot=replace(active, **patch)),
                "SESSION_EVIDENCE_MISMATCH")

    def test_direct_risk_cause_requires_actual_matching_satisfied_boundary(self):
        submitted = request(self.snapshot)
        boundary = v.SessionBoundaryObservation(submitted.request_reference,
            self.snapshot.snapshot_reference, "PROPAGATION_RISK", "SATISFIED",
            n2.evidence_source(), "n3:value:direct-risk", "Synthetic observed boundary.")
        cause = v.SessionCauseObservation("n3:value:direct-risk:cause",
            submitted.request_reference, self.snapshot.snapshot_reference,
            "PROPAGATION_RISK_BOUNDARY", "PROPAGATION_RISK", None, None, (boundary,))
        v.revalidate_value(cause)
        self.assertEqual(cause.to_record()["boundary_observations"], [boundary.to_record()])
        for patch in ({"trigger": "OPERATOR_REQUEST"}, {"boundary_observations": ()},
                {"boundary_observations": (replace(boundary, status="NOT_SATISFIED"),)},
                {"boundary_observations": (replace(boundary, request_reference="n3:value:foreign"),)},
                {"boundary_observations": (replace(boundary, expected_snapshot_reference="n3:value:stale"),)},
                {"authority_observation": authority(submitted)},
                {"recovery_operation_reference": "n3:value:unobserved-n2"}):
            with self.subTest(patch=patch):
                self.assertRefuses(lambda: replace(cause, **patch))

    def test_authority_request_cause_requires_observed_authority(self):
        submitted = request(self.snapshot)
        cause = v.SessionCauseObservation("n3:value:authority:cause",
            submitted.request_reference, self.snapshot.snapshot_reference,
            "AUTHORITY_REQUEST", "OPERATOR_REQUEST", None, authority(submitted), ())
        self.assertRefuses(lambda: replace(cause, authority_observation=None))

    def test_publication_retains_actual_commit_truth(self):
        after = replace(self.snapshot, snapshot_reference="n3:value:after", generation=1,
            mode="CONTAINED", containment_reference="n3:value:containment",
            current_assessment_reference=None, observed_system_state_class=None)
        publication = v.SessionPublication("n3:value:publication", "n3:value:command",
            "n3:value:lease", self.snapshot, after, "COMMITTED", True, self.snapshot.current_state,
            "CONTAINED", "n3:value:cause", None, None, "Actual atomic mutation.")
        self.assertTrue(publication.session_effects_performed)
        self.assertRefuses(lambda: replace(publication, session_effects_performed=False))
        self.assertRefuses(lambda: replace(publication, after=replace(after, generation=2)))
        unconfirmed = replace(publication, status="UNCONFIRMED", session_effects_performed=None,
            failure_code="SESSION_PUBLICATION_UNCONFIRMED")
        self.assertIsNone(unconfirmed.session_effects_performed)

    def test_trigger_rule_mapping_and_clock_truth(self):
        clock = dv.ClockObservation("2026-10-11T00:00:00.000000Z", 1, None, None)
        for trigger, rule in v.CONTAINMENT_RULES.items():
            payload = v.ContainmentDiagnostic(trigger, self.origin.state_validity_diagnostic,
                "CONTAINED", v.RESTRICTED_OPERATIONS, clock, True, "PENDING", (rule,), ("Actual payload.",))
            self.assertEqual(payload.rule_ids, (rule,))
            wrong = next(other for other in v.CONTAINMENT_RULES.values() if other != rule)
            self.assertRefuses(lambda: replace(payload, rule_ids=(wrong,)))
            self.assertRefuses(lambda: replace(payload, containment_time=dv.ClockObservation(
                None, None, "CLOCK_UNAVAILABLE", "CLOCK_UNAVAILABLE")))

    def test_unconfirmed_wrong_reference_completion_is_retained(self):
        actual = v.SessionLifecycleCompletion("n3:value:wrong-first-return", "COMPLETE", (), None)
        failure = v.SessionFailureDetail("SESSION_CAPTURE_FAILED", "capture.finish", None,
            "NOT_CONFIRMED", None, None, "CAPTURE_COMPLETION_UNCONFIRMED", actual,
            "The actual first return had a different operation reference.")
        self.assertIs(failure.unconfirmed_completion_observation, actual)
        self.assertEqual(failure.to_record()["unconfirmed_completion_observation"]["status"], "COMPLETE")
        self.assertRefuses(lambda: replace(failure, completion_failure_code=None))

    def test_corrected_origin_union_preserves_actual_partial_and_zero_emission_outputs(self):
        ctx = n2.context("n3:value:partial")
        unrelated = n2.context("n3:value:unrelated")
        mismatched = n2.classification_facts(self.model.profile_binding, unrelated, n2.ash(0),
            canonical=self.model.canonical_binding)
        partial = self.model.assess(n2.ash(0), context=sv.SystemContext(False, False),
            classification_evidence=mismatched, diagnostic_context=ctx)
        self.assertIs(type(partial), sv.ClassificationEvidenceFailure)
        self.assertEqual(len(partial.emitted_diagnostics), 1)
        class RejectingCapture:
            def begin(self, reference):
                return self
            def append(self, emission):
                return sv.CaptureReceipt(emission.diagnostic_reference, "REJECTED")
        rejected_model = StateModel(self.model.profile_binding, self.model.canonical_binding, RejectingCapture())
        uncaptured = n2.assessment(rejected_model, n2.ash(0), reference="n3:value:uncaptured")
        self.assertIs(type(uncaptured), sv.DiagnosticCaptureFailure)
        self.assertEqual(uncaptured.emitted_diagnostics, ())
        for child in (self.origin, partial, uncaptured):
            with self.subTest(child=type(child).__name__):
                result = refused_result(self.command(), origin=child)
                self.assertEqual(result.to_record()["origin_assessment"], child.to_record())
                self.assertIs(result.origin_assessment, child)

    def test_unavailable_fresh_facts_retains_all_four_owned_fields(self):
        unavailable = rv.UnavailablePostAssessmentFacts("n3:value:command", n2.ash(0),
            n2.evidence_source("n3:value:post-facts"), "Provider unavailable before fresh assessment.")
        result = refused_result(self.command(), primary=unavailable)
        self.assertIs(result.failure_detail.primary_evidence, unavailable)
        self.assertEqual(result.to_record()["failure_detail"]["primary_evidence"], unavailable.to_record())
        self.assertEqual(set(unavailable.to_record()),
            {"operation_reference", "candidate_state_reference", "source_binding", "reason"})

    def test_api_only_capabilities_and_grants_have_no_wire_or_public_issuance(self):
        self.assertRefuses(lambda: v.SessionExecutionGate(), "SESSION_LEASE_REJECTED")
        self.assertRefuses(lambda: v.SessionRetentionHandle(), "SESSION_RETENTION_FAILED")
        forged = object.__new__(v.SessionExecutionGate)
        self.assertFalse(v._is_issued_gate(forged))
        self.assertRefuses(lambda: forged.stage_grant("REGISTRY_READ"), "SESSION_LEASE_REJECTED")
        grant = v.SessionStageGrant(0, "REGISTRY_READ", "CANCELLED", "n3:value:lease", 0)
        self.assertFalse(hasattr(grant, "to_record"))
        self.assertRefuses(lambda: v.raw_business_record(grant))

    def test_issued_gate_seal_read_is_independent_nonblocking_and_copies_are_not_issued(self):
        # This exact owner is unbound to an engine. Issuing a local token alone
        # grants no owner membership or semantic stage authority.
        identity = reference.CanonicalSourceCompatibilityTests().identity()
        diagnostics = ReferenceDevelopmentDiagnostics(identity,
            dv.DiagnosticsProfile("REFERENCE_DEVELOPMENT", "REFERENCE_DEVELOPMENT_DIAGNOSTICS", "ref:000003", True),
            reference.ControlledProjectionStore(), reference.ControlledClock(),
            canonical_source_snapshots=(dv.SourcePin("ASH_AGGREGATE", identity.source_revision,
                self.model.canonical_binding.aggregate_sha256),))
        owner = ReferenceSessionLifecycle(self.model, diagnostics, self.binding.policy_binding)
        submitted = request(self.snapshot)
        active = replace(self.snapshot, snapshot_reference="n3:value:gate-active",
            active_operation_reference=submitted.request_reference)
        lease = v.SessionOperationLease("n3:value:gate-lease", submitted, self.snapshot, "CONTAIN", active)
        gate = v._issue_gate(owner, lease, collector=diagnostics)
        self.assertTrue(v._is_issued_gate(gate))
        self.assertTrue(v._gate_is_issued_by(gate, owner))
        self.assertTrue(v._gate_matches_collector(gate, diagnostics))
        matching = v._issue_retention_handle(diagnostics, self.binding.session_reference)
        foreign_session = v._issue_retention_handle(diagnostics, "n3:value:another-session")
        self.assertTrue(v._gate_matches_collector(gate, diagnostics, matching))
        self.assertFalse(v._gate_matches_collector(gate, diagnostics, foreign_session))
        self.assertFalse(v._gate_matches_collector(gate, object(), matching))
        self.assertRefuses(lambda: gate.stage_grant("REGISTRY_READ"), "SESSION_LEASE_REJECTED")
        self.assertEqual(gate.capture_disposition(), "SEALED")
        v._set_capture_disposition(owner, gate, "ACTIVE")
        self.assertEqual(gate.capture_disposition(), "ACTIVE")
        gate._capture_lock.acquire()
        try:
            self.assertEqual(gate.capture_disposition(), "UNAVAILABLE")
        finally:
            gate._capture_lock.release()
        copied = object.__new__(v.SessionExecutionGate)
        for name in v.SessionExecutionGate.__slots__:
            setattr(copied, name, getattr(gate, name))
        self.assertFalse(v._is_issued_gate(copied))
        self.assertEqual(copied.capture_disposition(), "UNAVAILABLE")
        self.assertRefuses(lambda: v._set_capture_disposition(object(), gate, "SEALED"), "SESSION_LEASE_REJECTED")
        v._set_capture_disposition(owner, gate, "SEALED")
        self.assertEqual(gate.capture_disposition(), "SEALED")

    def test_guarded_serializer_matches_real_source_owned_records(self):
        objects = [self.binding.profile_binding, self.origin, self.origin.input_evidence,
            self.origin.state_validity_diagnostic, self.origin.classification_evidence,
            self.binding.recovery_binding, n2.evidence_source(),
            dv.ClockObservation(None, 5, "CLOCK_UNAVAILABLE", None)]
        for value in objects:
            with self.subTest(value=type(value).__name__):
                expected = value.to_record()
                self.assertEqual(v.raw_business_record(value), expected)
                self.assertEqual(v.raw_business_size(value), len(json.dumps(expected,
                    ensure_ascii=True, separators=(",", ":")).encode("ascii")))

    def test_guarded_serializer_preserves_actual_n2_and_n1_packets(self):
        codeword = n2.source_codewords()[1][1]
        for integer, capture in ((0, n2.ControlledDiagnostics()),
                (codeword, n2.ControlledDiagnostics()), (0, n2.ControlledDiagnostics(admission="REJECTED"))):
            model = StateModel(self.binding.profile_binding, self.binding.canonical_binding, RecordingDiagnosticCapture())
            origin = n2.assessment(model, n2.ash(integer), reference="n3:value:parity:" + str(integer))
            engine = RecoveryEngine(model, n2.registry(model), capture, n2.NormalizationResolver(model),
                n2.CorrectionProvider(), n2.Conditions(), n2.PostFacts(model.profile_binding))
            actual = engine.recover(origin, operation_context=n2.operation(origin))
            with self.subTest(packet=type(actual).__name__):
                self.assertEqual(v.raw_business_record(actual), actual.to_record())
        diagnosis = self.model.diagnosis_from_assessment(self.origin)
        plan = self.model.plan_normalization(diagnosis, plan_reference="n3:value:n1-plan",
            evidence_reference="n3:value:n1-proof", policy_binding=n2.normalization_policy())
        validation = self.model.validate_normalization_plan(plan)
        for value in (diagnosis, plan, validation):
            self.assertEqual(v.raw_business_record(value), value.to_record())
        context = nv.NormalizationContext("n3:value:n1-operation", "n3:value:n1-computation",
            "n3:value:n1-post-validation")
        class RefusingNormalizationCapture:
            def begin(self, reference, *, original_diagnosis):
                return self
            def append(self, record):
                return sv.CaptureReceipt(record.emission.diagnostic_reference, "REJECTED")
        rejected_model = StateModel(self.binding.profile_binding, self.binding.canonical_binding,
            RecordingDiagnosticCapture(), normalization_capture=RefusingNormalizationCapture())
        missing_capture = rejected_model.apply_normalization(plan, normalization_context=context)
        self.assertIs(type(missing_capture), nv.NormalizationCaptureFailure)
        successful_model = StateModel(self.binding.profile_binding, self.binding.canonical_binding,
            RecordingDiagnosticCapture(), normalization_capture=RecordingNormalizationCapture())
        successful = successful_model.apply_normalization(plan, normalization_context=context)
        self.assertIs(type(successful), nv.NormalizationResult)
        for value in (missing_capture, successful):
            self.assertEqual(v.raw_business_record(value), value.to_record())

    def test_exact_raw_limit_and_unicode_encoding(self):
        raw = {"astral": "🚀" * 512}
        expected = json.dumps(raw, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        self.assertEqual(v.raw_business_bytes(raw), expected)
        self.assertEqual(v.raw_business_size(raw, limit=len(expected)), len(expected))
        self.assertEqual(v.raw_business_size(raw, limit=len(expected) - 1), len(expected))
        self.assertRefuses(lambda: v.raw_business_bytes(raw, limit=len(expected) - 1),
            "SESSION_RAW_BUSINESS_LIMIT")
        self.assertRefuses(lambda: v.raw_business_record(raw, limit=len(expected) - 1),
            "SESSION_RAW_BUSINESS_LIMIT")
        for invalid in (float("nan"), {"x": object()}, {1: "bad key"}):
            self.assertRefuses(lambda: v.raw_business_size(invalid))

    def test_raw_overflow_refuses_full_32_mib_packet_without_truncation(self):
        # Exactly quotes plus the string reach the publication bound. A one-byte
        # larger string must return only the sentinel and refuse complete bytes.
        at_limit = ["x" * (v.MAX_RAW_BUSINESS_BYTES - 4)]
        self.assertEqual(v.raw_business_size(at_limit), v.MAX_RAW_BUSINESS_BYTES)
        self.assertEqual(len(v.raw_business_bytes(at_limit)), v.MAX_RAW_BUSINESS_BYTES)
        at_limit[0] += "x"
        self.assertEqual(v.raw_business_size(at_limit), v.MAX_RAW_BUSINESS_BYTES + 1)
        self.assertRefuses(lambda: v.raw_business_bytes(at_limit), "SESSION_RAW_BUSINESS_LIMIT")

    def test_cycles_and_unowned_hooks_are_refused_before_invocation(self):
        calls = []
        class CallerObject:
            def to_record(self):
                calls.append("to_record")
                raise AssertionError("Unknown serializer invoked")
            def __eq__(self, other):
                calls.append("equality")
                raise AssertionError("Unknown equality invoked")
        self.assertRefuses(lambda: v.raw_business_size({"caller": CallerObject()}))
        damaged = copy.deepcopy(self.snapshot)
        object.__setattr__(damaged, "current_state", CallerObject())
        self.assertRefuses(lambda: v.revalidate_value(damaged))
        self.assertRefuses(lambda: v.raw_business_size({"owned_child": damaged}))
        self.assertRefuses(lambda: v.raw_business_size(["x" * 64, CallerObject()], limit=1))
        self.assertEqual(calls, [])
        recursive = []
        recursive.append(recursive)
        self.assertRefuses(lambda: v.raw_business_size(recursive))
        cyclic = copy.deepcopy(self.snapshot)
        object.__setattr__(cyclic.binding, "profile_binding", cyclic)
        self.assertRefuses(lambda: v.revalidate_value(cyclic))


if __name__ == "__main__":
    unittest.main()
