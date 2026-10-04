from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
import unittest

from core.ash_pattern_engine import diagnostics as core
from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from core.ash_pattern_engine.recovery import RecoveryEngine
from scripts.reference_diagnostics_host import assemble_reference_diagnostics, WindowsProtectedStore
from tests import test_m3_recovery as fixtures

ROOT = Path(__file__).resolve().parents[1]


class ControlledClock:
    """Explicit deterministic observation port, not native time evidence."""
    def __init__(self):
        self.value = 100
        self.mode = None

    def read(self):
        if self.mode == "THROW":
            raise RuntimeError("untrusted clock sentinel must never be logged")
        if self.mode == "UNAVAILABLE":
            return dv.ClockObservation(None, None, "CLOCK_UNAVAILABLE", "CLOCK_UNAVAILABLE")
        if self.mode == "REGRESS":
            value = 0
        else:
            value = self.value
            self.value += 1
        return dv.ClockObservation("2026-10-04T12:00:00.000000Z", value, None, None)


class FaultStore:
    """Fault wrapper around an actual verified backend; no protection flags."""
    def __init__(self, actual):
        self.actual = actual
        self.calls = []
        self.failure = None
        self.mode = "REJECTED"

    def __getattr__(self, name):
        original = getattr(self.actual, name)
        def operation(*args, **kwargs):
            self.calls.append((name, args))
            if self.failure == name:
                sequence = args[0] if args else None
                if self.mode == "THROW":
                    raise RuntimeError("private storage path/token sentinel")
                if self.mode == "WRONG_SEQUENCE":
                    return dv.StorageReceipt(None, "COMMITTED", None)
                return dv.StorageReceipt(sequence, "UNKNOWN" if self.mode == "UNKNOWN" else "REJECTED",
                                         "STORAGE_COMMIT_UNCONFIRMED")
            return original(*args, **kwargs)
        return operation


class PartialPurgeStore(FaultStore):
    def __init__(self, actual):
        super().__init__(actual)
        self.partial_once = True

    def purge_capture(self, request):
        self.calls.append(("purge_capture", (request,)))
        if request.event_sequences and self.partial_once:
            self.partial_once = False
            first = self.actual.purge_capture(dv.CapturePurgeRequest(request.event_sequences[:1], ()))
            remaining = tuple(dv.CaptureRemovalObservation(dv.CaptureObjectKey("EVENT", sequence, None, None),
                "NOT_REMOVED", 0, "STORAGE_COMMIT_REJECTED") for sequence in request.event_sequences[1:])
            return dv.StoreCapturePurgeReceipt("PARTIAL", first.observations + remaining, "STORAGE_COMMIT_UNCONFIRMED")
        return self.actual.purge_capture(request)


class LostPurgeReceiptStore(FaultStore):
    def __init__(self, actual, outcome):
        super().__init__(actual)
        self.outcome = outcome

    def purge_capture(self, request):
        self.calls.append(("purge_capture", (request,)))
        actual = self.actual.purge_capture(request)
        if self.outcome == "THROW":
            raise RuntimeError("deletion completed before transport failure")
        if self.outcome == "MALFORMED":
            return None
        return dv.StoreCapturePurgeReceipt("REJECTED", tuple(
            dv.CaptureRemovalObservation(row.key, "UNCONFIRMED", None, "STORAGE_COMMIT_UNCONFIRMED")
            for row in actual.observations), "STORAGE_COMMIT_UNCONFIRMED")


@unittest.skipUnless(os.name == "nt", "Actual adopted protected storage is Windows-specific")
class ReferenceDiagnosticsTests(unittest.TestCase):
    def create(self):
        owner = assemble_reference_diagnostics(ROOT)
        self.addCleanup(owner.store.close)
        return owner

    def model(self, owner):
        return StateModel(fixtures.profile(), fixtures.canonical_binding(), owner.assessment_capture(),
                          normalization_capture=owner.normalization_capture())

    def diagnosis(self, owner, reference="diagnosis:a", candidate=None):
        model = self.model(owner)
        return model.diagnose(fixtures.ash(0) if candidate is None else candidate,
                              diagnostic_context=fixtures.context(reference))

    def wrapped(self):
        original = self.create()
        store = FaultStore(original.store)
        clock = ControlledClock()
        owner = core.ReferenceDevelopmentDiagnostics(original.identity, original.profile, store, clock)
        return owner, store, clock

    def test_actual_protected_store_and_complete_pair(self):
        owner = self.create()
        result = self.diagnosis(owner)
        self.assertEqual(owner.complete_assessment(result).status, "COMPLETE")
        self.assertEqual(owner.store.verify().status, "VERIFIED")
        snapshot = owner.snapshot(bundle_reference="bundle:actual")
        pair = owner.export_pair(snapshot)
        self.assertIs(type(pair), dv.ExportReceipt)
        protected = owner.store.root
        raw = (protected / "diagnostics.json").read_bytes()
        markdown = (protected / "diagnostics.md").read_bytes()
        embedded = markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0]
        self.assertEqual(json.loads(raw), json.loads(embedded))
        self.assertEqual(json.loads(raw), snapshot.to_record())
        self.assertTrue(list(protected.glob("support-PROFILE-*.json")))
        self.assertTrue(list(protected.glob("support-ASSESSMENT-*.json")))
        self.assertEqual(pair.parts[-1].part, "MANIFEST")
        self.assertFalse(any(item.source == "NATIVE_RELEASE" and item.status == "AVAILABLE" for item in snapshot.coverage))

    def test_native_parent_with_delete_child_grant_refused(self):
        with self.assertRaises(dv.DiagnosticsContractError) as observed:
            WindowsProtectedStore(Path("C:/"))
        self.assertEqual(observed.exception.code, "STORAGE_PARENT_UNTRUSTED")

    def test_nested_parent_is_not_silently_trusted(self):
        with self.assertRaises(dv.DiagnosticsContractError):
            WindowsProtectedStore(ROOT)

    def test_no_capture_completion_is_visible(self):
        owner = self.create()
        self.diagnosis(owner)
        snapshot = owner.snapshot(bundle_reference="bundle:missing")
        self.assertEqual(snapshot.health.coverage_status, "PARTIAL")
        self.assertEqual(snapshot.health.last_failure_code, "DIAGNOSTICS_COMPLETION_MISSING")

    def test_actual_completion_cannot_be_replayed(self):
        owner = self.create()
        result = self.diagnosis(owner)
        self.assertEqual(owner.complete_assessment(result).status, "COMPLETE")
        second = owner.complete_assessment(result)
        self.assertEqual(second.status, "INCOMPLETE")
        self.assertEqual(second.failure_code, "DIAGNOSTICS_REPLAY_REFUSED")

    def test_changed_emission_cannot_claim_acknowledgement(self):
        owner = self.create()
        result = self.diagnosis(owner)
        changed = dataclasses.replace(result.emitted_diagnostics[0],
            envelope=dataclasses.replace(result.emitted_diagnostics[0].envelope, summary="changed owned bounded prose"))
        altered = dataclasses.replace(result, emitted_diagnostics=(changed,))
        observed = owner.complete_assessment(altered)
        self.assertEqual(observed.status, "INCOMPLETE")
        self.assertEqual(observed.failure_code, "DIAGNOSTICS_COMPLETION_MISMATCH")

    def test_failed_predicate_binding_is_retained_without_classification_claim(self):
        owner = self.create()
        model = self.model(owner)
        context = fixtures.context("assessment:foreign-fact")
        candidate = fixtures.ash(1)
        evidence = fixtures.classification_facts(model.profile_binding, context, candidate)
        changed = dataclasses.replace(evidence.correction_path_is_known,
            binding=dataclasses.replace(evidence.correction_path_is_known.binding, assessment_reference="assessment:other"))
        evidence = dataclasses.replace(evidence, correction_path_is_known=changed)
        result = model.assess(candidate, context=sv.SystemContext(False, False),
            classification_evidence=evidence, diagnostic_context=context)
        self.assertIs(type(result), sv.ClassificationEvidenceFailure)
        self.assertEqual(owner.complete_assessment(result).status, "INCOMPLETE")
        safe = owner.snapshot(bundle_reference="bundle:foreign-fact").supporting_evidence.assessments[0]
        self.assertIsNone(safe.system_state_class)
        self.assertNotEqual(safe.correction_path_is_known.assessment_reference, safe.assessment_reference)
        self.assertEqual(len(safe.emissions), 1)

    def test_untrusted_refs_preview_summary_and_notes_never_persist(self):
        owner = self.create()
        marker = "secret_TOKEN_910023"
        result = self.diagnosis(owner, reference="diagnosis:" + marker, candidate=marker)
        self.assertEqual(owner.complete_assessment(result).status, "COMPLETE")
        snapshot = owner.snapshot(bundle_reference="bundle:" + marker)
        self.assertEqual(owner.export_pair(snapshot).status, "COMPLETE")
        for file in owner.store.root.iterdir():
            self.assertNotIn(marker.encode(), file.read_bytes(), file.name)
        self.assertEqual(snapshot.supporting_evidence.assessments[0].state_validity_diagnostic.input_state.kind, "REJECTED")
        self.assertGreater(snapshot.redaction.field_count, 0)
        self.assertGreater(snapshot.redaction.reference_count, 0)

    def test_event_commit_failure_retains_actual_capture_failure(self):
        for mode in ("REJECTED", "UNKNOWN", "THROW", "WRONG_SEQUENCE"):
            with self.subTest(mode=mode):
                owner, store, _ = self.wrapped()
                store.failure, store.mode = "commit_event", mode
                result = self.diagnosis(owner)
                self.assertIs(type(result), sv.DiagnosticCaptureFailure)
                self.assertEqual(result.emitted_diagnostics, ())
                self.assertIsNotNone(result.attempted_diagnostic)
                receipt = owner.complete_assessment(result)
                self.assertEqual(receipt.status, "INCOMPLETE")
                self.assertEqual(owner.health().coverage_status, "PARTIAL")

    def test_support_commit_failure_prevents_complete_observation(self):
        owner, store, _ = self.wrapped()
        result = self.diagnosis(owner)
        store.failure = "commit_supporting"
        receipt = owner.complete_assessment(result)
        self.assertEqual(receipt.status, "INCOMPLETE")
        self.assertEqual(receipt.failure_code, "STORAGE_COMMIT_UNCONFIRMED")
        self.assertEqual(len(owner.snapshot(bundle_reference="bundle:partial").events), 1)
        self.assertTrue(list(store.actual.root.glob("incident-*.json")))
        incident = owner.snapshot(bundle_reference="bundle:incident").incidents[0]
        self.assertEqual(incident.observed_outcome, "NOT_CONFIRMED")
        self.assertTrue(incident.unresolved)
        self.assertEqual(owner.purge_completed(through_sequence=0).status, "REJECTED")

    def test_incident_commit_failure_is_retained_as_unknown_coverage(self):
        owner, store, _ = self.wrapped()
        result = self.diagnosis(owner)
        # Actual missing completion followed by a changed submitted fingerprint.
        altered = dataclasses.replace(result, emitted_diagnostics=(dataclasses.replace(result.emitted_diagnostics[0],
            envelope=dataclasses.replace(result.emitted_diagnostics[0].envelope, summary="changed")),))
        store.failure = "commit_incident"
        self.assertEqual(owner.complete_assessment(altered).status, "INCOMPLETE")
        self.assertEqual(len(owner._unconfirmed_incidents), 1)
        snapshot = owner.snapshot(bundle_reference="bundle:incident-unknown")
        self.assertEqual(snapshot.incidents, ())
        self.assertTrue(any(row.source == "DIAGNOSTICS" and row.status == "UNAVAILABLE" for row in snapshot.coverage))

    def test_health_failure_prevents_event_ack(self):
        owner, store, _ = self.wrapped()
        store.failure = "commit_health"
        result = self.diagnosis(owner)
        self.assertIs(type(result), sv.DiagnosticCaptureFailure)
        self.assertEqual(result.emitted_diagnostics, ())
        self.assertEqual(len(owner._acks), 0)
        self.assertEqual(len(owner._events), 1)  # actual file retained, acknowledgement absent

    def test_clock_unavailable_regression_and_duration_refuse_before_capture(self):
        for mode in ("UNAVAILABLE", "REGRESS", "THROW", "DURATION"):
            with self.subTest(mode=mode):
                owner, _, clock = self.wrapped()
                clock.mode = mode
                if mode == "DURATION":
                    clock.value = 600000000101
                result = self.diagnosis(owner)
                self.assertIs(type(result), sv.DiagnosticCaptureFailure)
                self.assertEqual(len(owner._events), 0)

    def test_source_clock_is_an_explicit_port(self):
        owner, _, clock = self.wrapped()
        result = self.diagnosis(owner)
        self.assertEqual(owner.complete_assessment(result).status, "COMPLETE")
        snapshot = owner.snapshot(bundle_reference="bundle:deterministic")
        self.assertEqual(snapshot.generated_at_utc, "2026-10-04T12:00:00.000000Z")
        self.assertLess(snapshot.events[0].clock.monotonic_nanoseconds, snapshot.capture_window.end.monotonic_nanoseconds)

    def test_independent_meta_pool_and_nonrecursive_fallback(self):
        owner, store, _ = self.wrapped()
        store.failure = "commit_event"
        result = self.diagnosis(owner)
        self.assertEqual(owner.health().meta_record_count, 1)
        self.assertTrue(any(name == "commit_meta" for name, _ in store.calls))
        store.failure = "commit_meta"
        owner.complete_assessment(result)
        self.assertTrue(any(name == "commit_fallback_health" for name, _ in store.calls))
        self.assertLessEqual(len([name for name, _ in store.calls if name == "commit_meta"]), 2)

    def test_uint64_counter_never_wraps(self):
        owner = self.create()
        owner._counts["REJECTED"] = (1 << 64) - 1
        owner._increment("REJECTED")
        health = owner.health()
        self.assertEqual(health.rejected_count, (1 << 64) - 1)
        self.assertEqual(next(row for row in health.counter_states if row.field == "REJECTED").status, "SATURATED")

    def test_reserved_operation_refuses_before_effects(self):
        owner = self.create()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(0))
        owner.complete_assessment(origin)
        owner._used = 2_000_000
        scope, receipt = owner.recovery_capture().begin(origin, operation_reference="operation:quota")
        self.assertIsNone(scope)
        self.assertEqual(receipt.status, "REJECTED")
        self.assertEqual(receipt.reserved_events, 0)
        self.assertEqual(receipt.failure_code, "DIAGNOSTICS_RESERVATION_REFUSED")

    def test_incident_pool_reservation_refuses_recovery_before_provider_effects(self):
        owner, _, _ = self.wrapped()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(fixtures.source_codewords()[0][0]),
                                     reference="origin:before-incident-capacity", known=True)
        self.assertEqual(owner.complete_assessment(origin).status, "COMPLETE")
        for index in range(32):
            actual = self.diagnosis(owner, "incident-capacity:" + str(index))
            changed = dataclasses.replace(actual, emitted_diagnostics=(dataclasses.replace(actual.emitted_diagnostics[0],
                envelope=dataclasses.replace(actual.emitted_diagnostics[0].envelope, summary="changed owned summary")),))
            self.assertEqual(owner.complete_assessment(changed).status, "INCOMPLETE")
        self.assertEqual(len(owner._incidents), 32)
        self.assertEqual(len(list(owner.store.actual.root.glob("incident-*.json"))), 32)
        certificate_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        provider = fixtures.CorrectionProvider(throw=True)
        engine = RecoveryEngine(model, fixtures.registry(certificate_model), owner,
            fixtures.NormalizationResolver(model), provider, fixtures.Conditions(), fixtures.PostFacts(model.profile_binding))
        result = engine.recover(origin, operation_context=fixtures.operation(origin))
        self.assertEqual(result.outcome, "FAILURE")
        self.assertEqual(provider.calls, [])
        self.assertIsNone(result.completion_observation)
        self.assertFalse(any(scope.producer == "RECOVERY_ENGINE" for scope in owner._scopes.values()))
        self.assertEqual(owner.health().last_failure_code, "DIAGNOSTICS_RESERVATION_REFUSED")

    def test_recovery_admission_health_commit_failure_retires_scope_before_provider(self):
        owner, store, _ = self.wrapped()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(fixtures.source_codewords()[0][0]), known=True)
        self.assertEqual(owner.complete_assessment(origin).status, "COMPLETE")
        certificate_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        provider = fixtures.CorrectionProvider(throw=True)
        engine = RecoveryEngine(model, fixtures.registry(certificate_model), owner,
            fixtures.NormalizationResolver(model), provider, fixtures.Conditions(), fixtures.PostFacts(model.profile_binding))
        store.failure = "commit_health"
        result = engine.recover(origin, operation_context=fixtures.operation(origin))
        self.assertEqual(result.outcome, "FAILURE")
        self.assertEqual(provider.calls, [])
        self.assertIsNone(result.completion_observation)
        retired = [scope for scope in owner._scopes.values() if scope.producer == "RECOVERY_ENGINE"]
        self.assertEqual(len(retired), 1)
        self.assertTrue(retired[0].finished)
        self.assertEqual(retired[0].failed, "STORAGE_COMMIT_UNCONFIRMED")
        self.assertEqual(retired[0].indices, [])
        self.assertEqual(owner.health().active_reservations, 0)

    def test_semantic_recovery_failure_requires_confirmed_incident_before_completion(self):
        owner, store, _ = self.wrapped()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(fixtures.source_codewords()[0][0]), known=True)
        self.assertEqual(owner.complete_assessment(origin).status, "COMPLETE")
        certificate_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        provider = fixtures.CorrectionProvider(throw=True)
        engine = RecoveryEngine(model, fixtures.registry(certificate_model), owner,
            fixtures.NormalizationResolver(model), provider, fixtures.Conditions(), fixtures.PostFacts(model.profile_binding))
        store.failure = "commit_incident"
        result = engine.recover(origin, operation_context=fixtures.operation(origin))
        self.assertEqual(result.outcome, "FAILURE")
        self.assertEqual(result.failure_detail.failure_code, "COLLABORATOR_FAILED")
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(result.completion_observation.status, "INCOMPLETE")
        self.assertEqual(result.completion_observation.failure_code, "STORAGE_COMMIT_UNCONFIRMED")
        self.assertEqual(len(owner._unconfirmed_incidents), 1)
        self.assertGreater(owner._incident_bytes, 0)
        self.assertEqual(owner._incidents, [])
        self.assertEqual(len([name for name, _ in store.calls if name == "commit_incident"]), 1)
        self.assertEqual(owner.purge_completed(through_sequence=1).status, "REJECTED")
        self.assertEqual(len(list(store.actual.root.glob("event-*.json"))), 2)

    def test_before_first_event_incident_pins_origin_without_mislabeling_or_overflow(self):
        owner, store, _ = self.wrapped()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(fixtures.source_codewords()[0][0]), known=True)
        self.assertEqual(owner.complete_assessment(origin).status, "COMPLETE")
        certificate_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        engine = RecoveryEngine(model, fixtures.registry(certificate_model), owner,
            fixtures.NormalizationResolver(model), fixtures.CorrectionProvider(throw=True), fixtures.Conditions(), fixtures.PostFacts(model.profile_binding))
        result = engine.recover(origin, operation_context=fixtures.operation(origin))
        self.assertEqual(result.completion_observation.status, "COMPLETE")
        self.assertEqual(result.emitted_diagnostics, ())
        incident = owner._incidents[0]
        self.assertEqual(incident.affected_operation_references, (owner._aliases[result.operation_context.operation_reference],))
        self.assertEqual(set(incident.timeline_event_references), {event.event_id for event in owner._events})
        self.assertEqual(owner.purge_completed(through_sequence=1).status, "REJECTED")
        self.assertEqual(len(list(store.actual.root.glob("event-*.json"))), 2)
        for index in range(31):
            actual = self.diagnosis(owner, "incident-pin-limit:" + str(index))
            changed = dataclasses.replace(actual, emitted_diagnostics=(dataclasses.replace(actual.emitted_diagnostics[0],
                envelope=dataclasses.replace(actual.emitted_diagnostics[0].envelope, summary="changed owned summary")),))
            self.assertEqual(owner.complete_assessment(changed).status, "INCOMPLETE")
        snapshot = owner.snapshot(bundle_reference="bundle:32-pinned-incidents")
        self.assertEqual(len(snapshot.incidents), 32)
        self.assertEqual(len(snapshot.retention.incident_pinned_operation_references), 32)
        self.assertEqual(len(list(store.actual.root.glob("incident-*.json"))), 32)

    def test_actual_rank_tie_order_preserved_with_source_inventory_order(self):
        owner = self.create()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(1), fallback=True)
        owner.complete_assessment(origin)
        entries, values = fixtures.entries_for((0, 1, 1))
        cert_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        engine = RecoveryEngine(model, fixtures.registry(cert_model, entries), owner,
            fixtures.NormalizationResolver(model), fixtures.CorrectionProvider(), fixtures.Conditions(values), fixtures.PostFacts(model.profile_binding))
        result = engine.recover(origin, operation_context=fixtures.operation(origin))
        self.assertEqual(result.outcome, "RECOVERED_FALLBACK_VALUE")
        proof = owner.snapshot(bundle_reference="bundle:order").supporting_evidence.registry_proofs[0]
        self.assertEqual(tuple(entry.input_order_index for entry in proof.entries), (0, 1, 2))
        self.assertEqual(tuple(entry.policy_reference for entry in proof.entries),
                         tuple(owner._aliases[entry.policy_id] for entry in entries))
        self.assertEqual(proof.evaluated_policy_references,
                         tuple(owner._aliases[attempt.policy_id] for attempt in result.policy_attempts))
        self.assertNotEqual(proof.evaluated_policy_references, tuple(entry.policy_reference for entry in proof.entries[:2]))
        targets = {node.evidence_reference: node for node in owner.snapshot(bundle_reference="bundle:targets").supporting_evidence.target_validity}
        self.assertTrue(targets)
        for entry in proof.entries:
            self.assertIn(entry.target_diagnostic_reference, targets)
            target = targets[entry.target_diagnostic_reference]
            self.assertEqual(target.state_validity_diagnostic.input_state.state, entry.candidate_state)
            self.assertEqual(target.state_validity_diagnostic.admissibility_status, "VALID")
        self.assertTrue(list(owner.store.root.glob("support-TARGET_VALIDITY-*.json")))

    def test_maximum_actual_transaction_fits_pre_effect_reservation(self):
        from core.ash_pattern_engine import recovery_values as rv
        owner = self.create()
        model = self.model(owner)
        origin = fixtures.assessment(model, fixtures.ash(fixtures.source_codewords()[0][0]), known=True)
        owner.complete_assessment(origin)
        entries, observations = [], {}
        for index in range(32, 0, -1):
            policy = f"FALLBACK-STATE-{index:03d}"
            applicability = tuple(rv.ConditionReference(policy + ":app:" + str(n), fixtures.evidence_source()) for n in range(8))
            validation = tuple(rv.ConditionReference(policy + ":validation:" + str(n), fixtures.evidence_source()) for n in range(8))
            for condition in applicability + validation:
                observations[condition.condition_id] = "TRUE"
            if index != 32:
                observations[validation[-1].condition_id] = "FALSE"
            entries.append(rv.FallbackPolicyEntry(policy, applicability, fixtures.ash(0), index, validation,
                "TRY_NEXT", ("Maximum bounded actual transaction.",)))
        cert_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        conditions = fixtures.Conditions(observations)
        engine = RecoveryEngine(model, fixtures.registry(cert_model, entries), owner,
            fixtures.NormalizationResolver(model), fixtures.CorrectionProvider(), conditions, fixtures.PostFacts(model.profile_binding))
        result = engine.recover(origin, operation_context=fixtures.operation(origin))
        self.assertEqual(result.outcome, "RECOVERED_FALLBACK_VALUE")
        self.assertEqual(len(conditions.calls), 512)
        snapshot = owner.snapshot(bundle_reference="bundle:maximum")
        self.assertEqual(len(snapshot.supporting_evidence.predicate_observations), 512)
        self.assertEqual(len(snapshot.supporting_evidence.conditions), 512)
        self.assertLessEqual(len(snapshot.events), 770)  # inherited origin2 + admitted768
        self.assertLessEqual(snapshot.health.used_bytes, 31588352)
        self.assertEqual(result.completion_observation.status, "COMPLETE")

    def test_whole_completed_purge_uses_actual_native_deletion(self):
        owner = self.create()
        result = self.diagnosis(owner)
        owner.complete_assessment(result)
        observed = owner.purge_completed(through_sequence=0)
        self.assertEqual(observed.status, "COMPLETED")
        self.assertEqual(owner.health().retained_count, 0)
        self.assertEqual(owner.health().expired_count, 1)
        self.assertFalse(list(owner.store.root.glob("event-*.json")))
        self.assertFalse(list(owner.store.root.glob("support-*.json")))
        self.assertFalse(owner._acks)

    def test_purge_never_removes_shared_retained_profile(self):
        owner = self.create()
        first = self.diagnosis(owner, "diagnosis:first")
        second = self.diagnosis(owner, "diagnosis:second")
        owner.complete_assessment(first)
        owner.complete_assessment(second)
        self.assertEqual(owner.purge_completed(through_sequence=0).status, "COMPLETED")
        snapshot = owner.snapshot(bundle_reference="bundle:retained")
        self.assertEqual(len(snapshot.events), 1)
        self.assertEqual(len(snapshot.supporting_evidence.profiles), 1)
        self.assertTrue(list(owner.store.root.glob("support-PROFILE-*.json")))

    def test_partial_event_purge_keeps_all_dependencies_then_retry_can_finish(self):
        original = self.create()
        store = PartialPurgeStore(original.store)
        owner = core.ReferenceDevelopmentDiagnostics(original.identity, original.profile, store, ControlledClock())
        model = self.model(owner)
        result = fixtures.assessment(model, fixtures.ash(0))
        self.assertEqual(owner.complete_assessment(result).status, "COMPLETE")
        first = owner.purge_completed(through_sequence=1)
        self.assertEqual(first.status, "REJECTED")
        self.assertEqual(owner.health().retained_count, 1)
        self.assertEqual(owner.health().expired_count, 1)
        self.assertTrue(list(original.store.root.glob("support-PROFILE-*.json")))
        self.assertEqual(len([name for name, _ in store.calls if name == "purge_capture"]), 1)
        second = owner.purge_completed(through_sequence=1)
        self.assertEqual(second.status, "COMPLETED")
        self.assertEqual(owner.health().retained_count, 0)
        self.assertFalse(list(original.store.root.glob("support-*.json")))

    def test_unknown_purge_invalidates_origin_acknowledgements_and_keeps_graph_roots(self):
        for outcome in ("UNCONFIRMED", "MALFORMED", "THROW"):
            with self.subTest(outcome=outcome):
                original = self.create()
                store = LostPurgeReceiptStore(original.store, outcome)
                owner = core.ReferenceDevelopmentDiagnostics(original.identity, original.profile, store, ControlledClock())
                model = self.model(owner)
                origin = fixtures.assessment(model, fixtures.ash(0))
                self.assertEqual(owner.complete_assessment(origin).status, "COMPLETE")
                snapshot = owner.snapshot(bundle_reference="bundle:before-unknown-purge")
                self.assertEqual(owner.purge_completed(through_sequence=1).status, "REJECTED")
                self.assertFalse(list(original.store.root.glob("event-*.json")))
                self.assertEqual(owner.health().retained_count, 2)
                self.assertTrue(list(original.store.root.glob("support-PROFILE-*.json")))
                self.assertFalse(owner._acks)
                scope, receipt = owner.recovery_capture().begin(origin, operation_reference="recovery:after-unknown-purge")
                self.assertIsNone(scope)
                self.assertEqual(receipt.status, "REJECTED")
                self.assertEqual(receipt.failure_code, "DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                self.assertEqual(len(owner._events), 2)
                self.assertEqual(len([name for name, _ in store.calls if name == "purge_capture"]), 1)
                with self.assertRaises(dv.DiagnosticsContractError):
                    owner.export_pair(snapshot)

    def test_complete_purge_explicitly_releases_export_slot(self):
        owner = self.create()
        result = self.diagnosis(owner)
        owner.complete_assessment(result)
        self.assertEqual(owner.export_pair(owner.snapshot(bundle_reference="bundle:first")).status, "COMPLETE")
        self.assertEqual(owner.purge_completed(through_sequence=0).status, "COMPLETED")
        self.assertFalse((owner.store.root / "manifest.json").exists())
        self.assertEqual(owner.export_pair(owner.snapshot(bundle_reference="bundle:next")).status, "COMPLETE")

    def test_capture_purge_controls_reject_combined_or_empty_request(self):
        key = dv.CaptureObjectKey("SUPPORTING", None, "PROFILE", "ref:000001")
        for sequences, keys in (((), ()), ((0,), (key,))):
            with self.assertRaises(dv.DiagnosticsContractError):
                dv.CapturePurgeRequest(sequences, keys)

    def test_actual_unconfirmed_atomic_file_is_accounted_and_cannot_claim_purge(self):
        owner = self.create()
        store = owner.store
        actual_security = store._native.security
        def reject_file_confirmation(handle, *, private):
            try:
                store._native.identity(handle, directory=False)
            except dv.DiagnosticsContractError:
                return actual_security(handle, private=private)
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE")
        store._native.security = reject_file_confirmation
        try:
            pair = store.write_pair("ref:000999", b"{}", b"markdown", b"{}", last_included_sequence=None)
        finally:
            store._native.security = actual_security
        self.assertEqual(pair.status, "INCOMPLETE")
        self.assertTrue((store.root / "diagnostics.json").exists())
        self.assertNotIn("diagnostics.json", store._files)
        self.assertEqual(store._unconfirmed_files["diagnostics.json"], 2)
        receipt = store.purge_bundle("ref:000999")
        self.assertEqual(receipt.status, "REJECTED")
        self.assertEqual(receipt.removed_parts, 0)
        self.assertEqual(receipt.failure_code, "STORAGE_COMMIT_UNCONFIRMED")
        self.assertEqual(store._pair, "ref:000999")
        self.assertTrue((store.root / "diagnostics.json").exists())
        next_pair = store.write_pair("ref:001000", b"{}", b"markdown", b"{}", last_included_sequence=None)
        self.assertEqual(next_pair.failure_code, "EXPORT_SLOT_OCCUPIED")

    def test_export_cannot_reuse_occupied_slot(self):
        owner = self.create()
        result = self.diagnosis(owner)
        owner.complete_assessment(result)
        snapshot = owner.snapshot(bundle_reference="bundle:first")
        self.assertEqual(owner.export_pair(snapshot).status, "COMPLETE")
        second = owner.snapshot(bundle_reference="bundle:second")
        observed = owner.export_pair(second)
        self.assertEqual(observed.status, "INCOMPLETE")
        self.assertEqual(observed.failure_code, "EXPORT_SLOT_OCCUPIED")

    def test_partial_pair_retains_complete_snapshot_and_exact_known_parts(self):
        owner, store, _ = self.wrapped()
        result = self.diagnosis(owner)
        owner.complete_assessment(result)
        snapshot = owner.snapshot(bundle_reference="bundle:partial-pair")
        def partial(alias, json_bytes, markdown_bytes, manifest_bytes, *, last_included_sequence):
            import hashlib
            store.actual._write("diagnostics.json", json_bytes, cap=33554432)
            parts = (dv.PartReceipt("JSON", "diagnostics.json", "CONFIRMED", len(json_bytes), hashlib.sha256(json_bytes).hexdigest(), None),
                dv.PartReceipt("MARKDOWN", "diagnostics.md", "WRITTEN_UNCONFIRMED", None, None, "EXPORT_MARKDOWN_FAILED"),
                dv.PartReceipt("MANIFEST", "manifest.json", "NOT_WRITTEN", None, None, None))
            return dv.StorePairFailure(alias, parts, last_included_sequence, "MARKDOWN", "EXPORT_MARKDOWN_FAILED")
        store.write_pair = partial
        observed = owner.export_pair(snapshot)
        self.assertIs(type(observed), dv.ExportFailure)
        self.assertEqual(observed.snapshot, snapshot)
        self.assertEqual(tuple(part.status for part in observed.parts), ("CONFIRMED", "WRITTEN_UNCONFIRMED", "NOT_WRITTEN"))
        self.assertFalse(any(row.source == "PAIRED_EXPORT" and row.status == "AVAILABLE" for row in owner.snapshot(bundle_reference="bundle:after-partial").coverage))

    def test_forged_safe_snapshot_never_reaches_store(self):
        owner, store, _ = self.wrapped()
        result = self.diagnosis(owner)
        owner.complete_assessment(result)
        snapshot = owner.snapshot(bundle_reference="bundle:owned")
        altered = dataclasses.replace(snapshot, bundle_id="ref:999999")
        with self.assertRaises(dv.DiagnosticsContractError) as observed:
            owner.export_pair(altered)
        self.assertEqual(observed.exception.code, "EXPORT_SNAPSHOT_INVALID")
        self.assertFalse(any(name == "write_pair" for name, _ in store.calls))

    def test_owned_public_boundaries_do_not_invoke_hostile_metaclass_equality(self):
        observed = []
        class HostileMeta(type):
            def __eq__(cls, other):
                observed.append("equality")
                raise AssertionError("unowned metaclass equality")
        class Hostile(metaclass=HostileMeta):
            def __str__(self):
                observed.append("string")
                raise AssertionError("unowned conversion")
        owner = self.create()
        for method in (owner.complete_assessment, owner.complete_normalization, owner.export_pair):
            with self.assertRaises(dv.DiagnosticsContractError):
                method(Hostile())
        with self.assertRaises(dv.DiagnosticsContractError):
            dv.SafeInputState("REJECTED", None, Hostile(), "INPUT_SIGNATURE_INVALID")
        self.assertEqual(observed, [])


class DiagnosticValueTests(unittest.TestCase):
    def test_exact_builtin_clock_timestamp_and_counter_types(self):
        for timestamp in ("2026-10-04T00:00:00.0000000Z", "2026-02-30T00:00:00.000000Z", "2026-10-04T00:00:60.000000Z"):
            with self.assertRaises(dv.DiagnosticsContractError):
                dv.ClockObservation(timestamp, 0, None, None)
        with self.assertRaises(dv.DiagnosticsContractError):
            dv.ClockObservation("2026-10-04T00:00:00.000000Z", True, None, None)

    def test_canonical_source_constructor_requires_all_eight_actual_pins(self):
        names = ("ASH_AGGREGATE", "ASH_STATE_SPACE", "ASH_CODEWORDS", "ASH_VALIDITY", "ASH_CLASSIFICATION", "ASH_RECOVERY", "ASH_DIAGNOSTIC_SCHEMA", "ASH_TAXONOMY")
        pins = tuple(dv.SourcePin(name, "0" * 40, digest) for name, (_, digest) in zip(names, sv.CANONICAL_BINDING_FIELDS[1:]))
        dv.SafeSourceEvidence("ref:000001", pins, None)
        wrong = dataclasses.replace(pins[-1], sha256="f" * 64)
        with self.assertRaises(dv.DiagnosticsContractError):
            dv.SafeSourceEvidence("ref:000001", pins[:-1] + (wrong,), None)

    def test_static_values_have_closed_exact_constructors(self):
        self.assertEqual(len(dv.VALUE_TYPES), 67)
        self.assertEqual(len(dv.ENUMS), 78)
        with self.assertRaises(dv.DiagnosticsContractError):
            dv.StorageReceipt(None, "COMMITTED", "STORAGE_COMMIT_UNCONFIRMED")
        with self.assertRaises(dv.DiagnosticsContractError):
            dv.CaptureRemovalObservation(dv.CaptureObjectKey("EVENT", 0, None, None), "REMOVED", None, None)


if __name__ == "__main__":
    unittest.main()
