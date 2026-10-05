from __future__ import annotations

import dataclasses
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.ash_pattern_engine import diagnostics as core
from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from core.ash_pattern_engine.recovery import RecoveryEngine
from scripts.reference_diagnostics_host import assemble_reference_diagnostics, WindowsProtectedStore
from scripts import reference_diagnostics_host as host
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

    def test_actual_host_captures_current_and_legacy_source_graphs_in_one_pair(self):
        owner = self.create()
        actual_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True).stdout.strip()
        revision, snapshots = host._verified_canonical_source_snapshots(ROOT)
        self.assertEqual(actual_head, revision)
        self.assertEqual(actual_head, owner.identity.source_revision)
        text = (ROOT / "docs/architecture/m3_source_compatibility_contract.md").read_text(encoding="utf-8")
        inventory = json.loads(text.split("<!-- EXACT_SOURCE_COMPATIBILITY_INVENTORY -->", 1)[1].split("```json", 1)[1].split("```", 1)[0])
        expected = {}
        for vector, source_revision in zip(inventory["vectors"], (inventory["legacy_commit"], actual_head)):
            binding = sv.CanonicalAshBinding(**vector["canonical_binding"])
            model = StateModel(fixtures.profile(), binding, owner.assessment_capture())
            result = model.diagnose(fixtures.ash(0),
                diagnostic_context=fixtures.context("diagnosis:source:" + vector["baseline"]))
            self.assertEqual("COMPLETE", owner.complete_assessment(result).status)
            expected[binding.aggregate_sha256] = (source_revision,
                tuple((pin["source_kind"], pin["sha256"]) for pin in vector["diagnostic_pin_fields"]))
        self.assertEqual(tuple(("ASH_AGGREGATE", expected[digest][0], digest) for digest in expected),
            tuple((pin.source_kind, pin.revision, pin.sha256) for pin in snapshots))
        self.assertEqual(2, len(snapshots))
        self.assertNotEqual(inventory["legacy_commit"], actual_head)
        snapshot = owner.snapshot(bundle_reference="bundle:actual:both-sources")
        nodes = snapshot.supporting_evidence.source_evidence
        self.assertEqual(2, len(nodes))
        self.assertEqual(set(expected), {node.verified_pins[0].sha256 for node in nodes})
        for node in nodes:
            source_revision, pins = expected[node.verified_pins[0].sha256]
            self.assertEqual(pins, tuple((pin.source_kind, pin.sha256) for pin in node.verified_pins))
            self.assertEqual({source_revision}, {pin.revision for pin in node.verified_pins})
        pair = owner.export_pair(snapshot)
        self.assertIs(type(pair), dv.ExportReceipt)
        self.assertEqual("COMPLETE", pair.status)
        raw = (owner.store.root / "diagnostics.json").read_bytes()
        markdown = (owner.store.root / "diagnostics.md").read_bytes()
        embedded = markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0]
        self.assertEqual(snapshot.to_record(), json.loads(raw))
        self.assertEqual(json.loads(raw), json.loads(embedded))

    def test_native_parent_with_delete_child_grant_refused(self):
        native = host._WinSecurity()
        self.addCleanup(native.close)
        # Real ACL controls on fresh empty fixtures; no volume-letter assumption
        # or modification of an existing parent. Store integration is separate.
        cases = (("trusted", "", None), ("create-only", "(A;;0x4;;;BU)", None),
            ("delete-child", "(A;;0x40;;;BU)", "STORAGE_PARENT_UNTRUSTED"),
            ("write-dac", "(A;;0x40000;;;BU)", "STORAGE_PARENT_UNTRUSTED"),
            ("write-owner", "(A;;0x80000;;;BU)", "STORAGE_PARENT_UNTRUSTED"),
            ("generic-all", "(A;;GA;;;BU)", "STORAGE_PARENT_UNTRUSTED"))
        with tempfile.TemporaryDirectory(prefix="ywe-native-acl-") as directory:
            fixture_root = Path(directory).resolve()
            for name, grant, failure in cases:
                with self.subTest(grant=name):
                    path = (fixture_root / name).resolve()
                    self.assertEqual(fixture_root, path.parent)
                    descriptor, handle = wintypes.LPVOID(), None
                    sddl = f"O:{native.sid}D:P(A;OICI;FA;;;{native.sid})(A;OICI;FA;;;SY)" + grant
                    native.check(native.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                        sddl, 1, ctypes.byref(descriptor), None))
                    try:
                        attributes = host._SecurityAttributes(ctypes.sizeof(host._SecurityAttributes), descriptor, False)
                        native.check(native.k.CreateDirectoryW(str(path), ctypes.byref(attributes)))
                        handle = native.open_directory(path)
                        native.identity(handle, directory=True)
                        if failure is None:
                            native.security(handle, private=False)
                        else:
                            with self.assertRaises(dv.DiagnosticsContractError) as observed:
                                native.security(handle, private=False)
                            self.assertEqual(failure, observed.exception.code)
                    finally:
                        if handle is not None:
                            native.k.CloseHandle(handle)
                        native.k.LocalFree(descriptor)
                        if path.exists():
                            path.rmdir()

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


class ControlledProjectionStore:
    """Declared port responses for portable Core controls, not native storage proof."""
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def operation(*args):
            self.calls.append((name, args))
            if name == "verify":
                return dv.StorageVerification("VERIFIED", True, True, True,
                    ("EFFECTIVE_USER", "SYSTEM"), True, True, True, None)
            return dv.StorageReceipt(args[0], "COMMITTED", None)
        return operation


class CanonicalSourceCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (ROOT / "docs/architecture/m3_source_compatibility_contract.md").read_text(encoding="utf-8")
        cls.inventory = json.loads(text.split("<!-- EXACT_SOURCE_COMPATIBILITY_INVENTORY -->", 1)[1].split("```json", 1)[1].split("```", 1)[0])
        cls.legacy, cls.current = cls.inventory["vectors"]

    def identity(self, revision="a" * 40):
        provenance = dv.SourceProvenance("UNKNOWN" if revision is None else "VERIFIED_CLEAN", revision, (),
            "SOURCE_NOT_VERIFIED" if revision is None else None)
        unavailable = tuple(dv.MissingCoverage(name, "UNAVAILABLE", "NOT_MEASURED")
            for name in ("ENVIRONMENT_OS", "ARCHITECTURE", "HOST_CLASS"))
        environment = dv.DiagnosticsEnvironment("UNKNOWN", (3, 12, 0), "UNKNOWN", "UNKNOWN", unavailable)
        return dv.DiagnosticsIdentity("2.0.23", "REFERENCE_DEVELOPMENT_DIAGNOSTICS", "REFERENCE_DEVELOPMENT",
            "ref:000001", revision, provenance, "ref:000002", environment)

    def pins(self):
        return (dv.SourcePin("ASH_AGGREGATE", dv.LEGACY_SOURCE_REVISION, self.legacy["canonical_binding"]["aggregate_sha256"]),
            dv.SourcePin("ASH_AGGREGATE", "a" * 40, self.current["canonical_binding"]["aggregate_sha256"]))

    def owner(self, snapshots=None, revision="a" * 40):
        store, clock = ControlledProjectionStore(), ControlledClock()
        profile = dv.DiagnosticsProfile("REFERENCE_DEVELOPMENT", "REFERENCE_DEVELOPMENT_DIAGNOSTICS", "ref:000003", True)
        owner = core.ReferenceDevelopmentDiagnostics(self.identity(revision), profile, store, clock,
            canonical_source_snapshots=snapshots)
        return owner, store, clock

    def test_complete_vectors_project_distinct_actual_configured_source_revisions(self):
        owner, store, _ = self.owner(self.pins())
        for vector, revision in ((self.legacy, dv.LEGACY_SOURCE_REVISION), (self.current, "a" * 40)):
            binding = sv.CanonicalAshBinding(**vector["canonical_binding"])
            reference = owner._source_support(binding)
            node = owner._support["CANONICAL_SOURCE"][reference]
            expected = tuple((row["source_kind"], row["sha256"]) for row in vector["diagnostic_pin_fields"])
            self.assertEqual(expected, tuple((pin.source_kind, pin.sha256) for pin in node.verified_pins))
            self.assertEqual({revision}, {pin.revision for pin in node.verified_pins})
        self.assertEqual(2, len(owner._support["CANONICAL_SOURCE"]))
        self.assertEqual(2, sum(name == "commit_supporting" for name, _ in store.calls))

    def test_direct_legacy_default_does_not_stamp_implementation_revision_or_enable_current(self):
        owner, store, _ = self.owner()
        reference = owner._source_support(sv.CanonicalAshBinding(**self.legacy["canonical_binding"]))
        self.assertEqual({dv.LEGACY_SOURCE_REVISION}, {p.revision for p in owner._support["CANONICAL_SOURCE"][reference].verified_pins})
        aliases, calls = dict(owner._aliases), len(store.calls)
        with self.assertRaises(dv.DiagnosticsContractError) as observed:
            owner._source_support(sv.CanonicalAshBinding(**self.current["canonical_binding"]))
        self.assertEqual(("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE"), (observed.exception.code, observed.exception.failed_field))
        self.assertEqual(aliases, owner._aliases)
        self.assertEqual(calls, len(store.calls))

    def test_invalid_configuration_refuses_before_store_clock_or_write(self):
        legacy, current = self.pins()
        malformed = object.__new__(dv.SourcePin)
        object.__setattr__(malformed, "source_kind", "ASH_AGGREGATE")
        object.__setattr__(malformed, "revision", "bad")
        object.__setattr__(malformed, "sha256", current.sha256)
        cases = ([legacy], (current, legacy), (legacy, legacy), (legacy, current, current),
            (dv.SourcePin("ASH_AGGREGATE", "a" * 40, "f" * 64),),
            (dv.SourcePin("ASH_AGGREGATE", "a" * 40, legacy.sha256),),
            (dataclasses.replace(current, revision="b" * 40),),
            (dv.SourcePin("ASH_TAXONOMY", "a" * 40, current.sha256),), (malformed,))
        profile = dv.DiagnosticsProfile("REFERENCE_DEVELOPMENT", "REFERENCE_DEVELOPMENT_DIAGNOSTICS", "ref:000003", True)
        for snapshots in cases:
            with self.subTest(snapshots_type=type(snapshots).__name__):
                store, clock = ControlledProjectionStore(), ControlledClock()
                with self.assertRaises(dv.DiagnosticsContractError) as observed:
                    core.ReferenceDevelopmentDiagnostics(self.identity(), profile, store, clock, canonical_source_snapshots=snapshots)
                self.assertEqual(("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE"), (observed.exception.code, observed.exception.failed_field))
                self.assertEqual([], store.calls)
                self.assertEqual(100, clock.value)

    def test_reflected_hostile_source_scalars_and_unowned_iterables_invoke_no_hooks(self):
        calls = []
        class Hostile(str):
            def __eq__(self, other):
                calls.append("equality")
                return True
            def __hash__(self):
                calls.append("hash")
                return 0
        def iterable():
            calls.append("iteration")
            yield self.pins()[0]
        invalid = [iterable()]
        for field in ("source_kind", "revision", "sha256"):
            pin = dataclasses.replace(self.pins()[0])
            object.__setattr__(pin, field, Hostile(getattr(pin, field)))
            invalid.append((pin,))
        for snapshots in invalid:
            with self.assertRaises(dv.DiagnosticsContractError):
                self.owner(snapshots)
        self.assertEqual([], calls)

    def test_empty_mapping_and_unknown_identity_cannot_admit_source_certified_capture(self):
        for snapshots, revision in (((), "a" * 40), (self.pins()[:1], None), (None, None)):
            owner, store, clock = self.owner(snapshots, revision)
            before = (len(store.calls), clock.value, dict(owner._aliases))
            with self.assertRaises(dv.DiagnosticsContractError) as observed:
                owner.assessment_capture().begin("assessment:no-source")
            self.assertEqual(("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE"), (observed.exception.code, observed.exception.failed_field))
            self.assertEqual(before, (len(store.calls), clock.value, dict(owner._aliases)))
        with self.assertRaises(dv.DiagnosticsContractError):
            self.owner(self.pins()[1:], None)

    def test_source_nodes_recheck_nested_scalars_and_reject_mixed_complete_vectors(self):
        vectors = []
        for row in (self.legacy, self.current):
            pins = tuple(dv.SourcePin(item["source_kind"], "a" * 40, item["sha256"]) for item in row["diagnostic_pin_fields"])
            dv.SafeSourceEvidence("ref:000001", pins, None)
            vectors.append(pins)
        for mixed in (vectors[0][:-1] + vectors[1][-1:], vectors[1][:-1] + vectors[0][-1:], tuple(reversed(vectors[0]))):
            with self.assertRaises(dv.DiagnosticsContractError):
                dv.SafeSourceEvidence("ref:000001", mixed, None)
        pin = dataclasses.replace(vectors[0][0]); object.__setattr__(pin, "revision", "bad")
        with self.assertRaises(dv.DiagnosticsContractError):
            dv.SafeSourceEvidence("ref:000001", (pin,) + vectors[0][1:], None)

    def test_committed_legacy_snapshot_and_dirty_or_extra_source_refusal(self):
        with tempfile.TemporaryDirectory(prefix="ywe-source-history-") as directory:
            root = Path(directory) / "repo"
            subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(ROOT), str(root)], check=True, capture_output=True)
            subprocess.run(["git", "checkout", "--quiet", "--detach", dv.LEGACY_SOURCE_REVISION], cwd=root, check=True, capture_output=True)
            revision, snapshots = host._verified_canonical_source_snapshots(root)
            self.assertEqual(dv.LEGACY_SOURCE_REVISION, revision)
            self.assertEqual(self.pins()[:1], snapshots)
            taxonomy = root / "core/ash_pattern_engine/canonical/interfaces/rule-id-taxonomy.md"
            original = taxonomy.read_bytes()
            taxonomy.write_bytes(original + b"\nUncommitted source change\n")
            with self.assertRaises(dv.DiagnosticsContractError):
                host._verified_canonical_source_snapshots(root)
            taxonomy.write_bytes(original)
            (taxonomy.parent / "unexpected-source.md").write_text("Not a registered canonical source\n", encoding="utf-8")
            with self.assertRaises(dv.DiagnosticsContractError):
                host._verified_canonical_source_snapshots(root)


if __name__ == "__main__":
    unittest.main()
