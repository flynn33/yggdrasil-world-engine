"""Actual reference lifecycle controls under YWE-REQ-0044.

Injected time/storage responses are synthetic. These tests exercise the real
collector and owner; they do not qualify native Windows storage or authority.
"""
from __future__ import annotations

import copy
from dataclasses import fields, replace
import json
import threading
import unittest
from unittest import mock

from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine import recovery_values as rv
from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import session_values as v
from core.ash_pattern_engine import session as session_domain
from core.ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics
from core.ash_pattern_engine.recovery import RecoveryEngine
from core.ash_pattern_engine.session import ReferenceSessionLifecycle
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from tests import test_m3_recovery as n2
from tests import test_m3_reference_diagnostics as diagnostics_fixture
from tests.test_m3_reference_diagnostics import ControlledClock, ControlledProjectionStore


def current_source():
    return sv.CanonicalAshBinding(**dict(dict(sv.CANONICAL_BINDING_BASELINES)["N3_LIFECYCLE"]))


def current_policy():
    return v.SessionPolicyBinding(**dict(v.SESSION_POLICY_BINDING_FIELDS))


def assembly(integer=0, *, store=None, clock=None, provider=None, initial_known=False, initial_fallback=False,
             registry_entries=(), correction_provider=None, normalization_mode="READY", conditions=None):
    """Real portable collector with explicitly declared synthetic host responses."""
    source, profile = current_source(), n2.profile()
    store = ControlledProjectionStore() if store is None else store
    clock = ControlledClock() if clock is None else clock
    identity = diagnostics_fixture.CanonicalSourceCompatibilityTests().identity()
    diagnostics_profile = dv.DiagnosticsProfile("REFERENCE_DEVELOPMENT", "REFERENCE_DEVELOPMENT_DIAGNOSTICS", "ref:000003", True)
    diagnostics = ReferenceDevelopmentDiagnostics(identity, diagnostics_profile, store, clock,
        canonical_source_snapshots=(dv.SourcePin("ASH_AGGREGATE", identity.source_revision, source.aggregate_sha256),))
    model = StateModel(profile, source, diagnostics.assessment_capture())
    origin = n2.assessment(model, n2.ash(integer), reference="n3:initial", known=initial_known, fallback=initial_fallback)
    completed = diagnostics.complete_assessment(origin)
    if completed.status != "COMPLETE":
        raise AssertionError("Actual initial assessment was not completed")
    policy = current_policy()
    owner = ReferenceSessionLifecycle(model, diagnostics, policy)
    registry = n2.registry(model, registry_entries)
    for certification in registry.snapshot.candidate_certifications:
        if diagnostics.complete_assessment(certification.source_assessment).status != "COMPLETE":
            raise AssertionError("Actual registry certification assessment was not completed")
    provider = n2.PostFacts(profile) if provider is None else provider
    engine = RecoveryEngine(model, registry, diagnostics, n2.NormalizationResolver(model, normalization_mode),
        n2.CorrectionProvider() if correction_provider is None else correction_provider,
        n2.Conditions() if conditions is None else conditions, provider, lifecycle_owner=owner)
    recovery = rv.RecoverySourceBinding(source, tuple(rv.SourcePin(path, digest) for path, digest in
        rv.recovery_contract_pin_fields(source)))
    binding = v.SessionBinding("n3:binding", "n3:session", source, recovery, profile, policy,
                              origin.assessment_binding.assessment_reference)
    session, receipt = engine.open_session(origin, session_binding=binding)
    return engine, owner, session, model, diagnostics, store, clock, origin, binding, receipt


def request(session, reference, action):
    snapshot = session.read()
    return v.SessionRequest(reference, snapshot.binding.session_reference, snapshot, action,
                            "Explicit controlled lifecycle request.")


def authority(submitted, origin="OPERATOR", status="AUTHORIZED"):
    return v.SessionAuthorityObservation(submitted.request_reference,
        submitted.expected_snapshot.snapshot_reference, status, origin, n2.evidence_source("n3:authority"),
        submitted.request_reference + ":authority", "Declared reference authority observation.")


def boundary(submitted, condition, status="SATISFIED"):
    return v.SessionBoundaryObservation(submitted.request_reference,
        submitted.expected_snapshot.snapshot_reference, condition, status, n2.evidence_source("n3:boundary"),
        submitted.request_reference + ":boundary:" + condition, "Declared actual boundary observation.")


def halt_command(session, reference="n3:halt", *, policy=False):
    submitted = request(session, reference, "REQUEST_HALT")
    return v.SessionHaltRequest(submitted, "POLICY_HALT_REQUEST" if policy else "OPERATOR_HALT_REQUEST",
                               authority(submitted, "POLICY" if policy else "OPERATOR"), (), None)


def contain_command(session, reference="n3:contain"):
    submitted = request(session, reference, "REQUEST_CONTAINMENT")
    return v.SessionContainmentRequest(submitted, "OPERATOR_REQUEST", authority(submitted), (), None)


def resolve_command(session, reference="n3:resolve", target=0, *, policy=False):
    submitted = request(session, reference, "RESOLVE_CONTAINMENT")
    propagation = rv.PropagationEvidence("SAFE", reference,
        submitted.expected_snapshot.current_assessment_reference, n2.evidence_source("n3:propagation"),
        "Actual current containment reference is explicitly SAFE.")
    return v.SessionResolutionRequest(submitted, "POLICY_DRIVEN" if policy else "OPERATOR_INTERVENTION",
        "REPLACE_STATE", n2.ash(target), authority(submitted, "POLICY" if policy else "OPERATOR"), propagation,
        (boundary(submitted, "CONTAINMENT_CLEAR"),), None)


def recover_command(session, origin, reference="n3:recover", *, propagation="SAFE", external="REACHABLE"):
    submitted = request(session, reference, "RECOVER")
    fresh = reference + ":origin:assessment"
    context = rv.RecoveryOperationContext(reference, fresh,
        rv.ContextObservation(sv.SystemContext(False, False), "n3:owner", reference + ":owner-context",
                              n2.evidence_source("n3:context")),
        rv.PropagationEvidence(propagation, reference, fresh, n2.evidence_source("n3:propagation"),
                               "Actual propagation observation for the new origin."),
        rv.ExternalAuthorityEvidence(external, reference, fresh, n2.evidence_source("n3:external"),
                                    "Actual external-authority availability for the new origin."))
    return v.SessionRecoveryRequest(submitted, origin, context)


class EvaluatedFacts(n2.PostFacts):
    """Declared full fresh predicate facts, with optional actual post-mode fault."""
    def __init__(self, *, known=False, fallback=False, failed_post=False, post_halted=False):
        super().__init__(n2.profile())
        self.known, self.fallback, self.failed_post = known, fallback, failed_post
        self.post_halted = post_halted

    def provide(self, candidate, *, origin, action_reference, diagnostic_context, operation_context):
        self.calls.append((candidate, action_reference, diagnostic_context))
        facts = n2.classification_facts(self.binding, diagnostic_context, candidate,
            self.known, self.fallback, canonical=origin.source_binding)
        is_post = ":origin:assessment" not in diagnostic_context.assessment_reference
        contained, halted = self.failed_post and is_post, self.post_halted and is_post
        return rv.PostAssessmentFacts(diagnostic_context, rv.ContextObservation(sv.SystemContext(halted, contained),
            "n3:declared-provider", action_reference + ":context", n2.evidence_source("n3:declared-provider")), facts)


class ActualCorrection:
    def resolve(self, origin, *, operation_context):
        return n2.known_correction(origin, (30,), 0)


class ResolutionTargetTests(unittest.TestCase):
    def model(self, states=(0,)):
        capture = RecordingDiagnosticCapture()
        capture.begin = mock.Mock(wraps=capture.begin)
        return StateModel(n2.profile(states), current_source(), capture), capture

    def test_pure_current_target_math_exhausts_all_512_states_without_capture(self):
        model, capture = self.model()
        for integer in range(512):
            target = n2.ash(integer)
            result = model.validate_resolution_target(target, prospective_context=sv.SystemContext(False, False))
            self.assertEqual("VERIFIED" if integer == 0 else "REJECTED", result.status)
            self.assertEqual(target, result.target_diagnostic.input_state)
            self.assertEqual(current_source(), result.current_source_binding)
            self.assertEqual("STABLE" if integer == 0 else None, result.expected_system_state_class)
            self.assertEqual("NO_ACTION" if integer == 0 else None, result.expected_recovery_category)
        capture.begin.assert_not_called()

    def test_prospective_context_and_hostile_target_are_refused_without_hooks(self):
        model, capture = self.model()
        calls = []
        class Hostile:
            def __eq__(self, other): calls.append("equality"); return True
            def __repr__(self): calls.append("repr"); return "hostile"
            def to_record(self): calls.append("record"); return {}
        for target, context in ((Hostile(), sv.SystemContext(False, False)),
                                (n2.ash(0), sv.SystemContext(False, True)),
                                (n2.ash(0), sv.SystemContext(True, False)),
                                (n2.ash(0), Hostile())):
            with self.assertRaises(v.SessionContractError):
                model.validate_resolution_target(target, prospective_context=context)
        self.assertEqual([], calls)
        capture.begin.assert_not_called()


class SessionRawGuardTests(unittest.TestCase):
    def operation(self):
        _, owner, session, _, _, store, _, origin, *_ = assembly()
        # This guard unit uses the actual OPEN association but does not enter a
        # lifecycle scope or claim a capture reservation acknowledgment.
        with owner._lock:
            command = contain_command(session)
            op = owner._admit(command)
        return owner, op, store

    def test_closed_raw_guard_uses_no_shared_capture_or_store_and_has_no_guessed_allowance(self):
        owner, op, store = self.operation()
        calls = tuple(store.calls)
        owner._raw_preflight(op)
        self.assertEqual(calls, tuple(store.calls))
        self.assertEqual(0, owner._snapshot.generation)
        self.assertEqual("NORMAL", owner._snapshot.mode)
        self.assertIsNone(op.publication)

    def test_size_overflow_sentinel_rejects_before_publication(self):
        owner, op, store = self.operation()
        calls = tuple(store.calls)
        with mock.patch.object(v, "raw_business_size", return_value=v.MAX_RAW_BUSINESS_BYTES + 1):
            with self.assertRaises(session_domain._Refusal) as observed:
                owner._raw_preflight(op)
        self.assertEqual("SESSION_RAW_BUSINESS_LIMIT", observed.exception.code)
        self.assertEqual("CANDIDATE_RESULT", op.raw_phase)
        self.assertFalse(op.effects)
        self.assertIsNone(op.publication)
        self.assertEqual(calls, tuple(store.calls))

    def test_terminal_history_counts_all_five_possible_trace_repetitions(self):
        owner, op, _ = self.operation()
        current = owner._prospective_result_record(op, owner._result(op))
        history = v.raw_business_record(owner._history_value(extra=owner._result(op)))
        marker = {"sizing_only_marker": "x" * 4096}
        base = owner._anticipated_terminal_record(history, [{}], current)
        larger = owner._anticipated_terminal_record(history, [{}, marker], current)
        measure = lambda value: len(json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False))
        self.assertEqual(5 * (measure(marker) + 1), measure(larger) - measure(base))
        self.assertEqual(measure(larger), session_domain._sizing_size(larger, measure(larger)))
        self.assertEqual(measure(larger), session_domain._sizing_size(larger, measure(larger) - 1))


class SessionLifecycleTests(unittest.TestCase):
    def test_partial_child_failure_remains_primary_when_actual_attachment_throws(self):
        _, owner, session, _, diagnostics, store, _, origin, *_ = assembly()
        actual_event = store.commit_event
        store.commit_event = lambda sequence, payload: (dv.StorageReceipt(sequence, "REJECTED", "STORAGE_COMMIT_REJECTED")
            if sequence == 2 else actual_event(sequence, payload))
        with mock.patch.object(diagnostics, "attach_result", side_effect=RuntimeError("declared attachment transport fault")), \
                mock.patch.object(diagnostics, "recovery_capture", wraps=diagnostics.recovery_capture) as n2_capture:
            result = session.execute(recover_command(session, origin))
            n2_capture.assert_not_called()
        self.assertIsInstance(result.origin_assessment, sv.DiagnosticCaptureFailure)
        self.assertEqual("INCOMPLETE", result.origin_completion_observation.status)
        self.assertEqual("SESSION_ORIGIN_REJECTED", result.failure_detail.failure_code)
        self.assertEqual("ATTACH", owner._last_retention.phase)
        self.assertEqual("NOT_CONFIRMED", owner._last_retention.status)
        self.assertIsNone(result.recovery_result)
        self.assertFalse(result.session_effects_performed)

    def test_unowned_command_metaclass_and_body_hooks_never_run_at_owner_boundary(self):
        _, _, session, _, _, store, *_ = assembly()
        calls = []
        class HostileMeta(type):
            def __eq__(cls, other): calls.append("metaclass equality"); raise AssertionError("unowned metaclass hook")
        class Hostile(metaclass=HostileMeta):
            def __repr__(self): calls.append("repr"); raise AssertionError("unowned body hook")
            def to_record(self): calls.append("record"); raise AssertionError("unowned body hook")
        before = tuple(store.calls)
        with self.assertRaises(v.SessionContractError):
            session.execute(Hostile())
        self.assertEqual([], calls)
        self.assertEqual(before, tuple(store.calls))
        session.execute(halt_command(session))
        terminal = session.execute(Hostile())
        self.assertEqual("NOT_INSPECTED_AT_TERMINAL", terminal.request_observation)
        self.assertEqual([], calls)

    def test_complete_nonentry_handoffs_observe_no_effects_and_preserve_current_accepted_origin(self):
        cases = (("REQUEST_EXTERNAL_AUTHORITY", 1, EvaluatedFacts()),
                 ("REMAIN_CONTAINED", 30, EvaluatedFacts(failed_post=True)),
                 ("REMAIN_SAFE_HALT", 30, EvaluatedFacts(post_halted=True)))
        for requested, integer, provider in cases:
            with self.subTest(requested=requested):
                _, owner, session, _, _, _, _, origin, *_ = assembly(integer, provider=provider)
                result = session.execute(recover_command(session, origin))
                self.assertEqual("COMPLETED", result.status)
                self.assertFalse(result.session_effects_performed)
                self.assertEqual(requested, result.recovery_result.directive.requested_action)
                self.assertEqual("COMPLETE", result.recovery_result.completion_observation.status)
                self.assertIs(origin, owner._accepted)
                self.assertEqual(origin.assessment_binding.assessment_reference, session.read().current_assessment_reference)
                self.assertEqual(("NORMAL", 0, "OPEN"),
                    (session.read().mode, session.read().generation, session.read().admission_status))
                self.assertEqual("N2_RESULT", result.cause.kind)
                self.assertIsNone(result.cause.trigger)
                self.assertEqual("NOT_APPLICABLE", result.confirmed_lifecycle_records[0].payload.outcome)
                self.assertIsNone(result.publication)

    def test_actual_complete_failed_post_and_new_bound_validation_boundary_enter_containment(self):
        _, _, session, _, _, _, _, origin, *_ = assembly(30, provider=EvaluatedFacts(failed_post=True))
        recovered = session.execute(recover_command(session, origin))
        self.assertEqual("COMPLETED", recovered.status)
        self.assertEqual("CONTAINED", recovered.recovery_result.post_assessments[-1].assessment.system_state_class)
        self.assertEqual("OPEN", session.read().admission_status)
        submitted = request(session, "n3:validation-boundary", "REQUEST_CONTAINMENT")
        command = v.SessionContainmentRequest(submitted, "RECOVERY_VALIDATION_FAILURE", None,
            (boundary(submitted, "RECOVERY_VALIDATION_FAILURE"),), recovered.recovery_result.operation_context.operation_reference)
        result = session.execute(command)
        self.assertEqual("COMPLETED", result.status)
        self.assertTrue(result.session_effects_performed)
        self.assertEqual("RECOVERY_VALIDATION_BOUNDARY", result.cause.kind)
        self.assertEqual("CONTAINED", session.read().mode)
        self.assertEqual(("ASH-CONTAINMENT-TRIGGER-004",), result.confirmed_lifecycle_records[-1].payload.rule_ids)
        self.assertEqual("CONTAINED", result.actual_post_assessment.system_state_class)

    def test_actual_fresh_failed_unreachable_handoff_latches_halt_with_actual_evidence(self):
        _, _, session, _, _, _, _, origin, *_ = assembly(1, provider=EvaluatedFacts())
        result = session.execute(recover_command(session, origin, external="UNREACHABLE"))
        self.assertEqual("COMPLETED", result.status)
        self.assertTrue(result.session_effects_performed)
        self.assertEqual("FAILED", result.origin_assessment.system_state_class)
        self.assertEqual("COMPLETE", result.recovery_result.completion_observation.status)
        self.assertEqual("ESCALATION_FROM_FAILED", result.cause.trigger)
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertEqual(("ASH-HALT-TRIGGER-002",), result.confirmed_lifecycle_records[-1].payload.rule_ids)

    def test_actual_finalization_keeps_ordinary_lease_exclusive_through_once_observer(self):
        _, _, session, _, diagnostics, _, _, origin, *_ = assembly()
        original_observe = diagnostics.observe_session_result
        seen = []
        def observe(handle, result, **kwargs):
            seen.append(session.read())
            competing = session.execute(recover_command(session, origin, "n3:observer-competing"))
            seen.append(competing)
            return original_observe(handle, result, **kwargs)
        with mock.patch.object(diagnostics, "observe_session_result", side_effect=observe) as observer:
            result = session.execute(recover_command(session, origin))
            self.assertEqual(1, observer.call_count)
        self.assertEqual("COMPLETED", result.status)
        self.assertEqual(result.request.request.request_reference, seen[0].active_operation_reference)
        self.assertEqual("SESSION_OPERATION_IN_PROGRESS", seen[1].failure_detail.failure_code)
        self.assertEqual(1, len(session.history().command_results))
        self.assertIsNone(session.read().active_operation_reference)
        self.assertIsNot(result.after, session.read())
        self.assertEqual(result.after.generation, session.read().generation)
        self.assertEqual(result.after.current_state, session.read().current_state)

    def test_controlled_source_change_after_clock_refuses_next_append_and_cas(self):
        _, owner, session, model, diagnostics, _, _, _, *_ = assembly()
        canonical = model.canonical_binding
        actual_clock = owner._clock
        def change_source(op):
            observed = actual_clock(op)
            # Privileged source-owner fault injection, outside the facade API.
            model._canonical_binding = n2.canonical_binding()
            return observed
        with mock.patch.object(owner, "_clock", side_effect=change_source), \
                mock.patch.object(diagnostics, "_session_append", wraps=diagnostics._session_append) as append:
            result = session.execute(contain_command(session))
            append.assert_not_called()
        model._canonical_binding = canonical
        self.assertEqual("SESSION_SOURCE_REJECTED", result.failure_detail.failure_code)
        self.assertFalse(result.session_effects_performed)
        self.assertEqual(("NORMAL", 0), (session.read().mode, session.read().generation))
        self.assertTrue(session.execute(halt_command(session)).session_effects_performed)

    def test_initial_rule_subset_and_classification_mutations_refuse_before_registration(self):
        engine, _, _, _, diagnostics, _, _, origin, binding, _ = assembly()
        cases = []
        for index in (0, 1):
            emissions = list(origin.emitted_diagnostics)
            altered = n2.reflectively_forged(emissions[index].envelope, rule_ids=emissions[index].envelope.rule_ids[:-1])
            emissions[index] = n2.reflectively_forged(emissions[index], envelope=altered)
            cases.append(n2.reflectively_forged(origin, emitted_diagnostics=tuple(emissions)))
        cases.append(n2.reflectively_forged(origin, system_state_class="FAILED", recovery_category="ESCALATION_REQUIRED"))
        with mock.patch.object(diagnostics, "register_session", wraps=diagnostics.register_session) as register:
            for submitted in cases:
                with self.assertRaises(v.SessionContractError) as observed:
                    engine.open_session(submitted, session_binding=binding)
                self.assertEqual("SESSION_ORIGIN_REJECTED", observed.exception.failure_code)
            register.assert_not_called()

    def test_actual_normalization_correction_and_fallback_candidates_publish_only_complete_valid_post(self):
        cases = (("normalize", 30, dict(provider=EvaluatedFacts())),
            ("correct", 30, dict(provider=EvaluatedFacts(known=True), initial_known=True,
                                correction_provider=ActualCorrection())),
            ("fallback", 1, dict(provider=EvaluatedFacts(fallback=True), initial_fallback=True,
                                 registry_entries=n2.entries_for()[0])))
        for name, integer, configuration in cases:
            with self.subTest(route=name):
                _, _, session, _, _, _, _, origin, *_ = assembly(integer, **configuration)
                result = session.execute(recover_command(session, origin, "n3:actual:" + name))
                self.assertEqual("COMPLETED", result.status)
                self.assertEqual("COMPLETE", result.recovery_result.completion_observation.status)
                self.assertTrue(result.session_effects_performed)
                self.assertEqual(("NORMAL", 1, n2.ash(0), "OPEN"),
                    (session.read().mode, session.read().generation, session.read().current_state, session.read().admission_status))
                self.assertEqual("STABLE", result.actual_post_assessment.system_state_class)
                self.assertTrue(result.actual_post_assessment.state_validity_diagnostic.is_valid)
                self.assertEqual("N2_RESULT", result.cause.kind)
                self.assertIsNone(result.cause.trigger)
                self.assertEqual(result.recovery_result.operation_context.operation_reference, result.cause.recovery_operation_reference)

    def test_actual_fallback_failure_risk_and_policy_handoffs_enter_containment_with_source_rule(self):
        cases = (("FALLBACK_FAILURE", 1, "SAFE", dict(provider=EvaluatedFacts(fallback=True), initial_fallback=True)),
                 ("PROPAGATION_RISK", 30, "RISK", dict(provider=EvaluatedFacts())),
                 ("OPERATOR_REQUEST", 30, "UNAVAILABLE", dict(provider=EvaluatedFacts())))
        for trigger, integer, propagation, configuration in cases:
            with self.subTest(trigger=trigger):
                _, _, session, *_rest = assembly(integer, **configuration)
                origin = _rest[4]
                result = session.execute(recover_command(session, origin, "n3:handoff:" + trigger, propagation=propagation))
                self.assertEqual("COMPLETED", result.status)
                self.assertIsInstance(result.recovery_result, rv.RecoveryHandoff)
                self.assertEqual(trigger, result.recovery_result.directive.trigger)
                self.assertEqual("COMPLETE", result.recovery_result.completion_observation.status)
                self.assertEqual("N2_HANDOFF", result.cause.kind)
                self.assertTrue(result.session_effects_performed)
                self.assertEqual("CONTAINED", session.read().mode)
                self.assertEqual((session_domain._CONTAINMENT_RULES[trigger],), result.confirmed_lifecycle_records[-1].payload.rule_ids)
                self.assertEqual("CONTAINED", result.actual_post_assessment.system_state_class)

    def test_direct_risk_boundary_needs_no_invented_authority_or_n2_handoff(self):
        _, _, session, *_ = assembly()
        submitted = request(session, "n3:direct-risk", "REQUEST_CONTAINMENT")
        command = v.SessionContainmentRequest(submitted, "PROPAGATION_RISK", None,
            (boundary(submitted, "PROPAGATION_RISK"),), None)
        result = session.execute(command)
        self.assertEqual("COMPLETED", result.status)
        self.assertTrue(result.session_effects_performed)
        self.assertEqual("PROPAGATION_RISK_BOUNDARY", result.cause.kind)
        self.assertIsNone(result.cause.authority_observation)
        self.assertIsNone(result.cause.recovery_operation_reference)
        self.assertEqual("CONTAINED", result.after.mode)
        self.assertEqual("ASH-CONTAINMENT-TRIGGER-002", result.confirmed_lifecycle_records[-1].payload.rule_ids[0])

    def test_failed_allocated_capture_admission_finishes_once_blocks_ordinary_and_still_halts(self):
        _, _, session, _, diagnostics, store, _, _, *_ = assembly()
        actual_commit = store.commit_supporting
        store.commit_supporting = lambda sequence, *args: dv.StorageReceipt(sequence, "REJECTED", "STORAGE_COMMIT_UNCONFIRMED")
        with mock.patch.object(diagnostics, "_session_finish", wraps=diagnostics._session_finish) as finish:
            result = session.execute(contain_command(session))
            self.assertEqual(1, finish.call_count)
        self.assertFalse(result.session_effects_performed)
        self.assertEqual("SESSION_CAPTURE_FAILED", result.failure_detail.failure_code)
        self.assertEqual("INCOMPLETE", result.completion_observation.status)
        self.assertEqual(("NORMAL", 0, "AUDIT_BLOCKED"),
            (session.read().mode, session.read().generation, session.read().admission_status))
        store.commit_supporting = actual_commit
        blocked = session.execute(contain_command(session, "n3:after-capture-failure"))
        self.assertEqual("SESSION_AUDIT_BLOCKED", blocked.failure_detail.failure_code)
        self.assertTrue(session.execute(halt_command(session)).session_effects_performed)
        self.assertTrue(session.read().terminal_latched)

    def test_capture_failure_after_known_containment_commit_keeps_actual_mode_and_true_effects(self):
        _, _, session, _, diagnostics, store, _, _, *_ = assembly()
        actual_event = store.commit_event
        store.commit_event = lambda sequence, payload: (dv.StorageReceipt(sequence, "UNKNOWN", "STORAGE_COMMIT_UNCONFIRMED")
            if sequence == 3 else actual_event(sequence, payload))
        with mock.patch.object(diagnostics, "_session_finish", wraps=diagnostics._session_finish) as finish:
            result = session.execute(contain_command(session))
            self.assertEqual(1, finish.call_count)
        self.assertEqual("UNCONFIRMED", result.status)
        self.assertTrue(result.session_effects_performed)
        self.assertEqual("COMMITTED", result.publication.status)
        self.assertEqual(("CONTAINED", 1, "AUDIT_BLOCKED"),
            (session.read().mode, session.read().generation, session.read().admission_status))
        self.assertEqual(1, len(result.confirmed_lifecycle_records))
        self.assertEqual(2, len(result.attempted_lifecycle_records))

    def test_first_wrong_reference_finish_preserves_clock_failure_and_actual_observation(self):
        _, owner, session, _, diagnostics, _, clock, _, *_ = assembly()
        actual_clock = owner._clock
        def unavailable_after_admission(op):
            clock.mode = "UNAVAILABLE"
            return actual_clock(op)
        actual_finish = diagnostics._session_finish
        observed = []
        def wrong_reference(wrapper, result):
            response = actual_finish(wrapper, result)
            returned = replace(response, operation_reference="n3:actual-wrong-return")
            observed.append(returned)
            return returned
        with mock.patch.object(owner, "_clock", side_effect=unavailable_after_admission), \
                mock.patch.object(diagnostics, "_session_finish", side_effect=wrong_reference) as finish:
            result = session.execute(contain_command(session))
            self.assertEqual(1, finish.call_count)
        self.assertEqual("SESSION_CAPTURE_FAILED", result.failure_detail.failure_code)
        self.assertEqual("clock", result.failure_detail.field_name)
        self.assertIs(observed[0], result.completion_observation)
        self.assertIs(observed[0], result.failure_detail.unconfirmed_completion_observation)
        self.assertFalse(result.session_effects_performed)
        self.assertEqual("AUDIT_BLOCKED", session.read().admission_status)

    def test_later_final_observer_failure_preserves_completed_body_known_effects_and_failed_receipt(self):
        _, owner, session, _, diagnostics, store, _, _, *_ = assembly()
        actual_commit = store.commit_supporting
        store.commit_supporting = lambda sequence, kind, alias, payload: (dv.StorageReceipt(sequence, "UNKNOWN", "STORAGE_COMMIT_UNCONFIRMED")
            if kind == "SESSION_COMMAND" else actual_commit(sequence, kind, alias, payload))
        with mock.patch.object(diagnostics, "observe_session_result", wraps=diagnostics.observe_session_result) as observer:
            result = session.execute(contain_command(session))
            self.assertEqual(1, observer.call_count)
        self.assertEqual("COMPLETED", result.status)
        self.assertTrue(result.session_effects_performed)
        self.assertIsNone(result.failure_detail)
        self.assertIs(result, observer.call_args.args[1])
        self.assertIs(result, session.history().command_results[-1])
        self.assertEqual("AUDIT_BLOCKED", session.read().admission_status)
        self.assertNotEqual("CONFIRMED", owner._last_retention.status)
        self.assertEqual("FINAL_RESULT", owner._last_retention.phase)
        self.assertNotEqual("COMPLETE_DECLARED_REFERENCE_SCOPE", diagnostics.health().coverage_status)

    def test_mandatory_halt_raw_overflow_keeps_terminal_truth_and_pending_without_shortened_chain(self):
        _, _, session, *_ = assembly()
        actual_size = v.raw_business_size
        def oversize(value, **kwargs):
            if type(value) is v.LifecycleRecord and type(value.payload) is v.SafeHaltDiagnostic:
                return v.MAX_RAW_BUSINESS_BYTES + 1
            return actual_size(value, **kwargs)
        with mock.patch.object(v, "raw_business_size", side_effect=oversize):
            result = session.execute(halt_command(session))
        self.assertIsInstance(result, v.SessionRawBusinessFailure)
        self.assertEqual("TERMINAL_CHAIN", result.phase)
        self.assertTrue(result.session_effects_performed)
        self.assertEqual("SAFE_HALT", result.after.mode)
        history = session.history()
        self.assertTrue(history.frozen)
        self.assertEqual("RAW_BUSINESS_LIMIT", history.pending_lifecycle_records[-1].reason_code)
        self.assertEqual((), history.confirmed_lifecycle_records)

    def test_every_complete_source_and_policy_field_and_recovery_pin_rejects_before_registration(self):
        engine, _, _, _, diagnostics, store, _, origin, binding, _ = assembly()
        invalid = []
        for field in fields(binding.canonical_binding):
            changed = "unknown.canonical" if field.name == "dependency_id" else "f" * 64
            canonical = n2.reflectively_forged(binding.canonical_binding, **{field.name: changed})
            invalid.append(n2.reflectively_forged(binding, canonical_binding=canonical))
        for index, pin in enumerate(binding.recovery_binding.contract_pins):
            for change in ({"path": "interfaces/unknown-contract.md"}, {"sha256": "f" * 64}):
                pins = list(binding.recovery_binding.contract_pins)
                pins[index] = n2.reflectively_forged(pin, **change)
                recovery = n2.reflectively_forged(binding.recovery_binding, contract_pins=tuple(pins))
                invalid.append(n2.reflectively_forged(binding, recovery_binding=recovery))
        invalid.append(n2.reflectively_forged(binding, recovery_binding=n2.reflectively_forged(
            binding.recovery_binding, contract_pins=tuple(reversed(binding.recovery_binding.contract_pins)))))
        for field in fields(binding.policy_binding):
            original = getattr(binding.policy_binding, field.name)
            changed = "f" * 64 if "sha256" in field.name else original + ":changed"
            invalid.append(n2.reflectively_forged(binding, policy_binding=n2.reflectively_forged(
                binding.policy_binding, **{field.name: changed})))
        invalid.append(n2.reflectively_forged(binding, profile_binding=n2.profile(profile_id="n3:foreign-profile")))
        calls = tuple(store.calls)
        with mock.patch.object(diagnostics, "register_session", wraps=diagnostics.register_session) as register:
            for index, submitted in enumerate(invalid):
                with self.subTest(index=index):
                    with self.assertRaises(v.SessionContractError) as observed:
                        engine.open_session(origin, session_binding=submitted)
                    self.assertNotEqual("SESSION_BUDGET_EXCEEDED", observed.exception.failure_code)
            register.assert_not_called()
        self.assertEqual(calls, tuple(store.calls))

    def test_full_expected_snapshot_changes_are_stale_without_capture_or_state_effect(self):
        changes = (dict(snapshot_reference="n3:other-snapshot"), dict(generation=1),
                   dict(current_state=n2.ash(30)), dict(recovery_attempted=True),
                   dict(active_operation_reference="n3:other-active"))
        for change in changes:
            with self.subTest(change=change):
                _, _, session, _, diagnostics, _, _, _, _, _ = assembly()
                command = contain_command(session)
                expected = replace(command.request.expected_snapshot, **change)
                submitted = replace(command.request, expected_snapshot=expected)
                command = replace(command, request=submitted, authority_observation=authority(submitted))
                with mock.patch.object(diagnostics, "lifecycle_capture", wraps=diagnostics.lifecycle_capture) as capture:
                    result = session.execute(command)
                    capture.assert_not_called()
                self.assertEqual("SESSION_STATE_STALE", result.failure_detail.failure_code)
                self.assertFalse(result.session_effects_performed)
                self.assertEqual((0, "NORMAL", n2.ash(0)),
                    (session.read().generation, session.read().mode, session.read().current_state))

    def test_old_same_state_assessment_after_cycle_and_foreign_samecollector_packet_are_refused(self):
        _, _, session, model, diagnostics, _, _, original, *_ = assembly()
        foreign = n2.assessment(model, n2.ash(0), reference="n3:foreign-valid")
        self.assertEqual("COMPLETE", diagnostics.complete_assessment(foreign).status)
        refused = session.execute(replace(recover_command(session, original, "n3:foreign-origin"), origin_assessment=foreign))
        self.assertEqual("SESSION_ORIGIN_FOREIGN", refused.failure_detail.failure_code)
        self.assertTrue(session.execute(contain_command(session)).session_effects_performed)
        self.assertTrue(session.execute(resolve_command(session)).session_effects_performed)
        self.assertEqual((2, n2.ash(0)), (session.read().generation, session.read().current_state))
        stale = session.execute(recover_command(session, original, "n3:old-origin"))
        self.assertEqual("SESSION_ORIGIN_FOREIGN", stale.failure_detail.failure_code)
        self.assertFalse(stale.session_effects_performed)
        self.assertEqual(2, session.read().generation)

    def test_last_unsigned_generation_is_reserved_for_actual_first_halt_without_wrap(self):
        _, owner, session, _, _, _, _, origin, *_ = assembly()
        # Controlled private boundary injection avoids 2**64 real publications.
        with owner._lock:
            owner._snapshot = replace(owner._snapshot, generation=2**64 - 2)
            owner._accepted_generation = owner._snapshot.generation
        refused = session.execute(recover_command(session, origin))
        self.assertEqual("SESSION_GENERATION_EXHAUSTED", refused.failure_detail.failure_code)
        self.assertFalse(refused.session_effects_performed)
        halted = session.execute(halt_command(session))
        self.assertTrue(halted.session_effects_performed)
        self.assertEqual(2**64 - 1, session.read().generation)
        self.assertEqual("SAFE_HALT", session.read().mode)
        session.execute(object())
        self.assertEqual(2**64 - 1, session.read().generation)

    def test_all_five_halt_triggers_require_actual_evidence_and_keep_exact_rule(self):
        cases = (("OPERATOR_HALT_REQUEST", False, 0), ("POLICY_HALT_REQUEST", False, 0),
                 ("ESCALATION_FROM_FAILED", False, 1), ("UNRESOLVABLE_BLOCKED_RECOVERY", False, 0),
                 ("CONTAINMENT_BREACH", True, 0))
        for trigger, contained, integer in cases:
            with self.subTest(trigger=trigger):
                _, _, session, *_ = assembly(integer)
                if contained:
                    self.assertEqual("COMPLETED", session.execute(contain_command(session)).status)
                submitted = request(session, "n3:trigger:" + trigger, "REQUEST_HALT")
                auth = authority(submitted, "POLICY" if trigger == "POLICY_HALT_REQUEST" else "OPERATOR")
                boundaries = ((boundary(submitted, "CONTAINMENT_BREACH"),) if contained else
                    (boundary(submitted, "RECOVERY_NO_PATH"), boundary(submitted, "CONTAINMENT_UNAVAILABLE"))
                    if trigger == "UNRESOLVABLE_BLOCKED_RECOVERY" else ())
                if trigger in ("CONTAINMENT_BREACH", "UNRESOLVABLE_BLOCKED_RECOVERY"):
                    auth = None
                result = session.execute(v.SessionHaltRequest(submitted, trigger, auth, boundaries, None))
                self.assertEqual("COMPLETED", result.status)
                self.assertTrue(result.session_effects_performed)
                payload = result.confirmed_lifecycle_records[-1].payload
                self.assertEqual(trigger, payload.trigger)
                self.assertEqual((session_domain._HALT_RULES[trigger],), payload.rule_ids)
                self.assertEqual("SAFE_HALT", session.read().mode)

    def test_policy_resolution_and_halt_resolution_do_not_invent_breach(self):
        for action in ("REPLACE_STATE", "HALT"):
            with self.subTest(action=action):
                _, _, session, *_ = assembly()
                session.execute(contain_command(session))
                command = resolve_command(session, policy=True)
                if action == "HALT":
                    command = replace(command, route="ESCALATE_TO_SAFE_HALT", resolution_action="HALT", target_state=None,
                                      boundary_observations=(), propagation_evidence=None)
                result = session.execute(command)
                self.assertEqual("COMPLETED", result.status)
                self.assertTrue(result.session_effects_performed)
                self.assertEqual("POLICY_HALT_REQUEST" if action == "HALT" else "OPERATOR_REQUEST", result.cause.trigger)
                self.assertEqual("SAFE_HALT" if action == "HALT" else "NORMAL", session.read().mode)

    def test_resolution_rejects_invalid_target_or_unbound_or_unavailable_guard_without_cas(self):
        for failure in ("target", "authority", "clear", "propagation", "stale-propagation"):
            with self.subTest(failure=failure):
                _, _, session, *_ = assembly()
                session.execute(contain_command(session))
                command = resolve_command(session)
                if failure == "target": command = replace(command, target_state=n2.ash(1))
                elif failure == "authority": command = replace(command, authority_observation=replace(command.authority_observation,status="UNAVAILABLE"))
                elif failure == "clear": command = replace(command, boundary_observations=(replace(command.boundary_observations[0],status="UNAVAILABLE"),))
                elif failure == "propagation": command = replace(command, propagation_evidence=replace(command.propagation_evidence,status="UNAVAILABLE"))
                else: command = replace(command, propagation_evidence=replace(command.propagation_evidence,origin_assessment_reference="n3:old-assessment"))
                result = session.execute(command)
                self.assertFalse(result.session_effects_performed)
                self.assertIsNotNone(result.failure_detail)
                self.assertEqual(("CONTAINED", 1), (session.read().mode, session.read().generation))

    def test_preterminal_compact_refusals_preserve_all_sixteen_terminal_audit_slots(self):
        _, _, session, _, _, store, _, origin, *_ = assembly()
        before_calls = tuple(store.calls)
        for ordinal in range(16):
            submitted = request(session, "n3:wrong-mode:" + str(ordinal), "RESOLVE_CONTAINMENT")
            command = v.SessionResolutionRequest(submitted, "OPERATOR_INTERVENTION", "REPLACE_STATE",
                n2.ash(0), authority(submitted), rv.PropagationEvidence("SAFE", submitted.request_reference,
                    origin.assessment_binding.assessment_reference, n2.evidence_source("n3:wrong-mode"),
                    "The current mode is checked before this observation."),
                (boundary(submitted, "CONTAINMENT_CLEAR"),), None)
            denied = session.execute(command)
            self.assertEqual("SESSION_MODE_FORBIDDEN", denied.reason_code)
            self.assertIsNone(denied.denial_ordinal)
            self.assertIsNone(denied.audit_reference)
            self.assertIsNone(denied.attempted_record)
        self.assertEqual(before_calls, tuple(store.calls))
        self.assertEqual((), session.history().command_results)
        session.execute(halt_command(session))
        for ordinal in range(1, 17):
            denied = session.execute(object())
            self.assertEqual(ordinal, denied.denial_ordinal)
            self.assertIsNotNone(denied.audit_reference)
        self.assertIsNone(session.execute(object()).denial_ordinal)

    def test_eligible_stale_recovery_refusals_spend_two_slots_replay_without_new_effects(self):
        _, _, session, _, _, store, _, origin, *_ = assembly()
        results = []
        commands = []
        for ordinal in range(2):
            command = recover_command(session, origin, "n3:stale-recovery:" + str(ordinal))
            stale = replace(command.request.expected_snapshot, snapshot_reference="n3:stale:" + str(ordinal))
            command = replace(command, request=replace(command.request, expected_snapshot=stale))
            results.append(session.execute(command))
            commands.append(command)
            self.assertEqual("SESSION_STATE_STALE", results[-1].failure_detail.failure_code)
            self.assertFalse(results[-1].session_effects_performed)
        self.assertEqual(2, len(session.history().command_results))
        calls = tuple(store.calls)
        replay = session.execute(commands[0])
        self.assertIsInstance(replay, v.SessionReplayObservation)
        self.assertIs(results[0], replay.original_result)
        self.assertEqual(calls, tuple(store.calls))
        exhausted = session.execute(recover_command(session, origin, "n3:third-recovery"))
        self.assertEqual("SESSION_BUDGET_EXCEEDED", exhausted.reason_code)
        self.assertIsNone(exhausted.denial_ordinal)
        self.assertEqual(2, len(session.history().command_results))
        self.assertEqual(0, session.read().generation)
        self.assertTrue(session.execute(halt_command(session)).session_effects_performed)

    def test_authority_refusals_spend_fifteen_modes_without_spending_first_halt_reserve(self):
        _, _, session, *_ = assembly()
        for ordinal in range(15):
            command = contain_command(session, "n3:denied-authority:" + str(ordinal))
            command = replace(command, authority_observation=replace(command.authority_observation, status="DENIED"))
            result = session.execute(command)
            self.assertEqual("SESSION_AUTHORITY_DENIED", result.failure_detail.failure_code)
            self.assertFalse(result.session_effects_performed)
        self.assertEqual(15, len(session.history().command_results))
        exhausted = session.execute(contain_command(session, "n3:sixteenth-mode"))
        self.assertEqual("SESSION_BUDGET_EXCEEDED", exhausted.reason_code)
        halted = session.execute(halt_command(session))
        self.assertTrue(halted.session_effects_performed)
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertEqual(16, len(session.history().command_results))

    def test_conflicting_duplicate_and_foreign_session_do_not_rewrite_existing_ledger(self):
        _, _, session, *_ = assembly()
        command = contain_command(session)
        command = replace(command, authority_observation=replace(command.authority_observation, status="DENIED"))
        original = session.execute(command)
        history = session.history()
        conflicting = replace(command, request=replace(command.request, reason="Another bounded command body."))
        result = session.execute(conflicting)
        self.assertEqual("SESSION_OPERATION_DUPLICATE", result.failure_detail.failure_code)
        foreign = contain_command(session, "n3:foreign")
        foreign_binding = replace(foreign.request.expected_snapshot.binding, session_reference="n3:other-session")
        foreign_snapshot = replace(foreign.request.expected_snapshot, binding=foreign_binding)
        foreign = replace(foreign, request=replace(foreign.request, session_reference="n3:other-session",
                                                expected_snapshot=foreign_snapshot))
        refused = session.execute(foreign)
        self.assertEqual("SESSION_ORIGIN_FOREIGN", refused.failure_detail.failure_code)
        self.assertEqual(history, session.history())
        self.assertIs(original, session.execute(command).original_result)

    def test_two_fresh_no_action_children_keep_historical_main_origin_and_exact_quota(self):
        _, _, session, _, diagnostics, store, _, origin, *_ = assembly()
        main = session.history().main_assessment
        first = session.execute(recover_command(session, origin, "n3:first-no-action"))
        self.assertEqual("COMPLETED", first.status)
        self.assertIsNone(first.failure_detail)
        self.assertIsInstance(first.recovery_result, rv.RecoveryNoAction)
        self.assertEqual("COMPLETE", first.origin_completion_observation.status)
        self.assertEqual("n3:first-no-action:origin:assessment", first.origin_assessment.assessment_binding.assessment_reference)
        self.assertFalse(first.session_effects_performed)
        self.assertEqual(0, session.read().generation)
        second = session.execute(recover_command(session, origin, "n3:second-no-action"))
        self.assertIsInstance(second.recovery_result, rv.RecoveryNoAction)
        self.assertIs(main, session.history().main_assessment)
        self.assertEqual(2, len(session.history().child_links))
        self.assertEqual(2, len(session.history().recovery_results))
        events = len(diagnostics.snapshot(bundle_reference="n3:quota:bundle").events)
        calls = tuple(store.calls)
        replay = session.execute(first.request)
        self.assertIs(first, replay.original_result)
        self.assertEqual(calls, tuple(store.calls))
        self.assertEqual(events, len(diagnostics.snapshot(bundle_reference="n3:quota:bundle").events))
        denied = session.execute(recover_command(session, origin, "n3:third-no-action"))
        self.assertEqual("SESSION_BUDGET_EXCEEDED", denied.reason_code)
        self.assertIsNone(denied.denial_ordinal)

    def test_initial_failed_class_is_running_normal(self):
        _, _, session, _, _, _, _, origin, _, receipt = assembly(1)
        self.assertEqual("FAILED", origin.system_state_class)
        self.assertEqual(("NORMAL", False, "FAILED"), (session.read().mode, session.read().terminal_latched,
                                                      session.read().observed_system_state_class))
        self.assertEqual("CONFIRMED", receipt.status)

    def test_malformed_parsed_origin_rejects_before_any_new_registration_effect(self):
        engine, _, _, model, diagnostics, store, _, _, binding, _ = assembly()
        malformed = n2.assessment(model, (0,) * 8, reference="n3:malformed", known=False, fallback=False)
        diagnostics.complete_assessment(malformed)
        self.assertIsNone(malformed.parsed_state)
        before = len(store.calls)
        with self.assertRaises(v.SessionContractError) as observed:
            engine.open_session(malformed, session_binding=replace(binding,
                initial_assessment_reference=malformed.assessment_binding.assessment_reference))
        self.assertEqual("SESSION_ORIGIN_REJECTED", observed.exception.failure_code)
        self.assertEqual(before, len(store.calls))

    def test_exact_facade_copy_does_not_copy_engine_issuance(self):
        engine, _, session, *_ = assembly()
        with self.assertRaises(v.SessionContractError):
            engine.read_session(copy.copy(session))

    def test_authorized_containment_has_legal_bridge_actual_pair_and_release_identity(self):
        _, _, session, _, diagnostics, *_ = assembly()
        before = session.read()
        result = session.execute(contain_command(session))
        self.assertTrue(result.session_effects_performed)
        self.assertEqual("COMMITTED", result.publication.status)
        self.assertEqual(["RECOVERY", "ESCALATION"], [r.envelope.stage for r in result.confirmed_lifecycle_records])
        self.assertEqual((), result.confirmed_lifecycle_records[0].payload.steps)
        self.assertEqual("CONTAINED", result.actual_post_assessment.system_state_class)
        self.assertEqual(sv.SystemContext(False, True), result.actual_post_assessment.system_context)
        self.assertEqual("COMPLETE", result.actual_post_completion_observation.status)
        self.assertEqual(before.generation + 1, session.read().generation)
        self.assertEqual("CONTAINED", session.read().mode)
        self.assertEqual("OPEN", session.read().admission_status)
        self.assertIsNone(session.read().active_operation_reference)
        self.assertNotEqual(result.after.snapshot_reference, session.read().snapshot_reference)
        self.assertEqual(result.after.generation, session.read().generation)
        self.assertEqual(6, len(diagnostics.snapshot(bundle_reference="n3:controlled:bundle").events))

    def test_authorized_resolution_uses_pure_proof_actual_normal_pair_and_new_root(self):
        _, _, session, *_ = assembly()
        entered = session.execute(contain_command(session))
        resolved = session.execute(resolve_command(session))
        self.assertTrue(resolved.session_effects_performed)
        self.assertEqual("VERIFIED", resolved.resolution_observation.target_validation.status)
        self.assertEqual(sv.SystemContext(False, False), resolved.resolution_observation.target_validation.prospective_context)
        self.assertEqual("STABLE", resolved.actual_post_assessment.system_state_class)
        self.assertEqual("NORMAL", session.read().mode)
        self.assertIsNone(session.read().containment_reference)
        halted = session.execute(halt_command(session))
        self.assertEqual(resolved.actual_post_assessment.assessment_binding.diagnosis_reference,
                         halted.confirmed_lifecycle_records[0].envelope.chain_root_reference)
        self.assertEqual(entered.confirmed_lifecycle_records[-1], session.history().confirmed_lifecycle_records[1])

    def test_clock_failure_cannot_prevent_authorized_first_halt_or_inspect_later_body(self):
        _, _, session, _, _, _, clock, *_ = assembly()
        command = halt_command(session)
        clock.mode = "UNAVAILABLE"
        result = session.execute(command)
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertTrue(session.read().terminal_latched)
        self.assertTrue(result.session_effects_performed)
        self.assertIsNotNone(result.pending_lifecycle_record)
        calls = []
        class Hostile:
            def __getattribute__(self, name): calls.append(name); raise AssertionError("body inspected")
        for ordinal in range(1, 18):
            denied = session.execute(Hostile())
            self.assertEqual("NOT_INSPECTED_AT_TERMINAL", denied.request_observation)
            self.assertIsNone(denied.request_reference)
            self.assertEqual(ordinal if ordinal <= 16 else None, denied.denial_ordinal)
        self.assertEqual([], calls)

    def test_halt_closure_exactly_matches_final_record_and_source_rule(self):
        _, _, session, *_ = assembly()
        result = session.execute(halt_command(session))
        record = result.confirmed_lifecycle_records[-1]
        closure = record.payload.full_diagnostic_chain[-1]
        self.assertEqual(record.diagnostic_reference, closure.terminal_emission.diagnostic_reference)
        self.assertEqual(record.envelope, closure.terminal_emission.envelope)
        self.assertEqual("ASH-HALT-TRIGGER-003", record.payload.rule_ids[0])
        self.assertEqual("TERMINAL", record.envelope.disposition)
        self.assertTrue(session.history().frozen)
        self.assertIs(session.read(), session.history().terminal_snapshot)

    def test_terminal_gate_precedes_replay_and_frozen_history_does_not_grow(self):
        _, _, session, *_ = assembly()
        command = halt_command(session)
        session.execute(command)
        history = session.history()
        replay = session.execute(command)
        self.assertIs(type(replay), v.SessionDeniedAttempt)
        self.assertEqual(history, session.history())

    def test_stale_full_snapshot_does_not_become_current_after_release(self):
        _, _, session, *_ = assembly()
        entered = session.execute(contain_command(session))
        command = resolve_command(session)
        old = replace(command.request, expected_snapshot=entered.after)
        result = session.execute(replace(command, request=old,
            authority_observation=replace(command.authority_observation, expected_snapshot_reference=old.expected_snapshot.snapshot_reference),
            boundary_observations=tuple(replace(item, expected_snapshot_reference=old.expected_snapshot.snapshot_reference)
                                       for item in command.boundary_observations)))
        self.assertFalse(result.session_effects_performed)
        self.assertEqual("SESSION_STATE_STALE", result.failure_detail.failure_code)
        self.assertEqual("CONTAINED", session.read().mode)

    def test_concurrent_provider_halt_revokes_following_work_and_keeps_frozen_index(self):
        for block_post in (False, True):
            with self.subTest(block_post=block_post):
                entered, release, halt_returned = threading.Event(), threading.Event(), threading.Event()
                results, errors, scopes = {}, [], []
                class Provider(EvaluatedFacts):
                    def provide(self, *args, **kwargs):
                        actual = super().provide(*args, **kwargs)
                        is_post = ":origin:assessment" not in kwargs["diagnostic_context"].assessment_reference
                        if is_post == block_post:
                            entered.set()
                            if not release.wait(10):
                                raise AssertionError("The concurrent halt did not release its provider control.")
                        return actual
                provider = Provider()
                engine, _, session, _, diagnostics, store, _, origin, *_ = assembly(30, provider=provider)
                command = recover_command(session, origin, "n3:concurrent-recover")
                actual_capture = diagnostics.recovery_capture
                def capture(**kwargs):
                    adapter = actual_capture(**kwargs)
                    actual_begin = adapter.begin
                    def begin(*args, **parameters):
                        scope, receipt = actual_begin(*args, **parameters)
                        self.assertIsNotNone(scope)
                        scope.finish = mock.Mock(wraps=scope.finish)
                        scopes.append(scope)
                        return scope, receipt
                    adapter.begin = begin
                    return adapter
                def recover():
                    try:
                        results["recovery"] = session.execute(command)
                    except BaseException as error:
                        errors.append(error)
                def halt():
                    try:
                        results["halt"] = session.execute(halt_command(session, "n3:concurrent-halt"))
                    except BaseException as error:
                        errors.append(error)
                    finally:
                        halt_returned.set()
                recovery_thread = threading.Thread(target=recover, daemon=True)
                halt_thread = threading.Thread(target=halt, daemon=True)
                with mock.patch.object(diagnostics, "recovery_capture", side_effect=capture), \
                     mock.patch.object(diagnostics, "complete_assessment", wraps=diagnostics.complete_assessment) as complete, \
                     mock.patch.object(engine._normalization, "resolve", wraps=engine._normalization.resolve) as normalize, \
                     mock.patch.object(engine._correction, "resolve", wraps=engine._correction.resolve) as correct, \
                     mock.patch.object(engine._conditions, "evaluate", wraps=engine._conditions.evaluate) as condition:
                    recovery_thread.start()
                    try:
                        self.assertTrue(entered.wait(5), "Actual recovery did not reach the controlled provider.")
                        self.assertTrue(recovery_thread.is_alive())
                        self.assertEqual(1 if block_post else 0, len(scopes))
                        halt_thread.start()
                        self.assertTrue(halt_returned.wait(5), "Authorized halt waited for the blocked provider.")
                        self.assertEqual([], errors)
                        halted = results["halt"]
                        self.assertTrue(halted.session_effects_performed)
                        self.assertEqual("COMMITTED", halted.publication.status)
                        self.assertEqual("SAFE_HALT", session.read().mode)
                        self.assertTrue(session.read().terminal_latched)
                        self.assertFalse(release.is_set())
                        self.assertTrue(recovery_thread.is_alive())
                        frozen_history = session.history()
                        frozen_index = tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY_PAGE"].values())
                        frozen_nodes = tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY"].values())
                        if block_post:
                            # The real N2 reservation may refuse halt capture; the
                            # semantic latch still returned before cleanup.
                            self.assertIsNotNone(halted.pending_lifecycle_record)
                            self.assertEqual((), frozen_index)
                        else:
                            self.assertTrue(frozen_index)
                        calls_at_halt = (len(provider.calls), complete.call_count, normalize.call_count,
                                         correct.call_count, condition.call_count)
                        events_at_halt = tuple(call for call in store.calls if call[0] == "commit_event")
                    finally:
                        release.set()
                        recovery_thread.join(5)
                        if halt_thread.ident is not None:
                            halt_thread.join(5)
                    self.assertFalse(recovery_thread.is_alive(), "Recovery cleanup did not finish.")
                    self.assertFalse(halt_thread.is_alive(), "Halt did not finish.")
                    self.assertEqual([], errors)
                    result = results["recovery"]
                    self.assertEqual("SESSION_EXECUTION_CANCELLED", result.failure_detail.failure_code)
                    self.assertFalse(result.session_effects_performed)
                    self.assertIsNone(result.publication)
                    self.assertEqual(calls_at_halt, (len(provider.calls), complete.call_count, normalize.call_count,
                                                   correct.call_count, condition.call_count))
                    self.assertEqual(events_at_halt, tuple(call for call in store.calls if call[0] == "commit_event"))
                    self.assertEqual(frozen_index, tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY_PAGE"].values()))
                    self.assertEqual(frozen_nodes, tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY"].values()))
                    self.assertEqual(frozen_history, session.history())
                    self.assertEqual(0, diagnostics.health().active_reservations)
                    if block_post:
                        self.assertIs(type(result.recovery_result), rv.RecoveryFailure)
                        self.assertEqual((), result.recovery_result.post_assessments)
                        self.assertTrue(result.recovery_result.steps)
                        self.assertIsNotNone(result.recovery_result.completion_observation)
                        scopes[0].finish.assert_called_once()
                    else:
                        self.assertIsNone(result.recovery_result)
                        self.assertIsNone(result.origin_assessment)
                        self.assertEqual([], scopes)


if __name__ == "__main__":
    unittest.main()
