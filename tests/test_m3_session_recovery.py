"""N3 engine composition and callback controls [YWE-REQ-0044].

Portable controls use explicitly synthetic clock/store/provider responses.
Native retention and full lifecycle integration have separate witnesses.
"""
from __future__ import annotations

import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import core.ash_pattern_engine as public
from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import recovery_values as rv
from core.ash_pattern_engine import session_values as values
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics
from core.ash_pattern_engine.recovery import RecoveryEngine, _SessionEngineServices
from core.ash_pattern_engine.session import ReferenceSessionLifecycle
from core.ash_pattern_engine.state_model import StateModel
from scripts import reference_diagnostics_host as host
from tests import test_m3_recovery as n2
from tests import test_m3_reference_diagnostics as diagnostic_fixture
from tests import test_m3_session_lifecycle as lifecycle_fixture


ROOT = Path(__file__).resolve().parents[1]


def unopened_composition(diagnostics=None):
    """Actual owners; no session registration or lifecycle effects in this helper."""
    binding = sv.CanonicalAshBinding(**dict(dict(sv.CANONICAL_BINDING_BASELINES)["N3_LIFECYCLE"]))
    if diagnostics is None:
        identity = diagnostic_fixture.CanonicalSourceCompatibilityTests().identity()
        profile = dv.DiagnosticsProfile("REFERENCE_DEVELOPMENT", "REFERENCE_DEVELOPMENT_DIAGNOSTICS", "ref:000003", True)
        diagnostics = ReferenceDevelopmentDiagnostics(identity, profile,
            diagnostic_fixture.ControlledProjectionStore(), diagnostic_fixture.ControlledClock(),
            canonical_source_snapshots=(dv.SourcePin("ASH_AGGREGATE", identity.source_revision, binding.aggregate_sha256),))
    model = StateModel(n2.profile(), binding, diagnostics.assessment_capture())
    owner = ReferenceSessionLifecycle(model, diagnostics,
        values.SessionPolicyBinding(**dict(values.SESSION_POLICY_BINDING_FIELDS)))
    registry = n2.registry(model)
    collaborators = (model, registry, diagnostics, n2.NormalizationResolver(model),
                     n2.CorrectionProvider(), n2.Conditions(), n2.PostFacts(model.profile_binding))
    engine = RecoveryEngine(*collaborators, lifecycle_owner=owner)
    return engine, owner, collaborators


class SessionCompositionTests(unittest.TestCase):
    def test_inventory_public_types_export_the_owned_classes(self):
        inventory = json.loads((ROOT / "docs/design-planning/m3/session-lifecycle/BUSINESS_API_INVENTORY.json").read_text())
        for name in inventory["types"]:
            with self.subTest(name=name):
                self.assertIn(name, public.__all__)
                self.assertIs(getattr(values, name), getattr(public, name))
        self.assertEqual(len(public.__all__), len(set(public.__all__)))

    def test_legacy_engine_session_calls_refuse_before_callback_and_recovery_remains_actual(self):
        _, origin, engine, diagnostics, *_ = n2.RecoveryIntegrationTests().fixture(original=0)
        before = tuple(diagnostics.calls)
        for call in (lambda: engine.open_session(origin, session_binding=None),
                     lambda: engine.read_session(None), lambda: engine.execute_session(None, None),
                     lambda: engine.read_session_history(None)):
            with self.assertRaises(values.SessionContractError) as observed:
                call()
            self.assertEqual(("SESSION_INPUT_INVALID", "collaborator"),
                             (observed.exception.failure_code, observed.exception.field_name))
        self.assertEqual(before, tuple(diagnostics.calls))
        result = engine.recover(origin, operation_context=n2.operation(origin))
        self.assertEqual("NO_ACTION", result.outcome)
        self.assertEqual("COMPLETE", result.completion_observation.status)
        self.assertEqual(1, len(diagnostics.finish_inputs))

    def test_service_copy_and_blank_are_not_issued_and_refuse_closed(self):
        engine, _, _ = unopened_composition()
        issued = engine._session_services
        self.assertTrue(issued.is_issued(issued))
        for unissued in (copy.copy(issued), object.__new__(_SessionEngineServices)):
            with self.subTest(kind="copy" if hasattr(unissued, "_engine") else "blank"):
                self.assertFalse(unissued.is_issued(unissued))
                with self.assertRaises(values.SessionContractError) as observed:
                    unissued.read_session(None)
                self.assertEqual("SESSION_INPUT_INVALID", observed.exception.failure_code)

    def test_owner_can_be_composed_only_once_and_against_its_actual_model_and_collector(self):
        engine, owner, collaborators = unopened_composition()
        before = tuple(collaborators[2].store.calls)
        with self.assertRaises(values.SessionContractError) as observed:
            RecoveryEngine(*collaborators, lifecycle_owner=owner)
        self.assertEqual("SESSION_OPERATION_DUPLICATE", observed.exception.failure_code)
        other_engine, other_owner, other = unopened_composition()
        with self.assertRaises(values.SessionContractError) as observed:
            other_owner._bind_engine(engine._session_services, other[0], other[2])
        self.assertEqual("SESSION_INPUT_INVALID", observed.exception.failure_code)
        self.assertTrue(other_engine._session_services.is_issued(other_engine._session_services))
        self.assertEqual(before, tuple(collaborators[2].store.calls))

    def test_unissued_gate_refuses_before_any_recovery_port(self):
        _, origin, engine, diagnostics, resolver, correction, conditions, provider = n2.RecoveryIntegrationTests().fixture(original=0)
        before = tuple(diagnostics.calls)
        for gate in (object(), object.__new__(values.SessionExecutionGate)):
            with self.assertRaises(rv.RecoveryContractError) as observed:
                engine.recover(origin, operation_context=n2.operation(origin), execution_gate=gate)
            self.assertEqual(("RECOVERY_INPUT_INVALID", "execution_gate"),
                             (observed.exception.code, observed.exception.field_name))
        self.assertEqual(before, tuple(diagnostics.calls))
        self.assertEqual(([], [], [], []), (resolver.calls, correction.calls, conditions.calls, provider.calls))


class SessionHostPolicyTests(unittest.TestCase):
    def test_actual_adopted_policy_matches_containing_committed_bytes(self):
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        host._verified_session_policy(ROOT, revision)

    def test_normalization_accepts_bom_and_crlf_but_refuses_changed_or_uncommitted_policy(self):
        relative = dict(values.SESSION_POLICY_BINDING_FIELDS)["source_path"]
        committed = subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=ROOT)
        with tempfile.TemporaryDirectory(prefix="ywe-session-policy-") as directory:
            root = Path(directory)
            policy = root / relative
            policy.parent.mkdir(parents=True)
            policy.write_bytes(b"\xef\xbb\xbf" + committed.replace(b"\n", b"\r\n"))
            with mock.patch.object(host.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, committed)):
                host._verified_session_policy(root, "0" * 40)
                policy.write_bytes(committed + b"Changed policy.\n")
                with self.assertRaises(dv.DiagnosticsContractError) as observed:
                    host._verified_session_policy(root, "0" * 40)
                self.assertEqual("DIAGNOSTICS_CONFIG_INVALID", observed.exception.code)
                policy.write_bytes(committed)
            with mock.patch.object(host.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, committed + b"x")):
                with self.assertRaises(dv.DiagnosticsContractError):
                    host._verified_session_policy(root, "0" * 40)

    @unittest.skipUnless(os.name == "nt", "The adopted protected reference host is Windows-specific")
    def test_actual_verified_windows_host_captures_current_session_and_paired_export(self):
        import jsonschema
        diagnostics = host.assemble_reference_diagnostics(ROOT)
        self.addCleanup(diagnostics.store.close)
        engine, owner, collaborators = unopened_composition(diagnostics)
        model = collaborators[0]
        origin = n2.assessment(model, n2.ash(0), reference="n3:host:initial")
        self.assertEqual("COMPLETE", diagnostics.complete_assessment(origin).status)
        source = model.canonical_binding
        binding = values.SessionBinding("n3:host:binding", "n3:host:session", source,
            rv.RecoverySourceBinding(source, tuple(rv.SourcePin(path, digest) for path, digest in
                rv.recovery_contract_pin_fields(source))), model.profile_binding,
            values.SessionPolicyBinding(**dict(values.SESSION_POLICY_BINDING_FIELDS)),
            origin.assessment_binding.assessment_reference)
        session, retained = engine.open_session(origin, session_binding=binding)
        self.assertEqual("CONFIRMED", retained.status)
        for build in (lifecycle_fixture.contain_command, lifecycle_fixture.resolve_command,
                      lifecycle_fixture.halt_command):
            self.assertEqual("COMPLETED", session.execute(build(session)).status)
        denial = session.execute(object())
        self.assertEqual("NOT_INSPECTED_AT_TERMINAL", denial.request_observation)
        self.assertTrue(session.history().frozen)
        self.assertEqual("SAFE_HALT", session.read().mode)
        snapshot = diagnostics.snapshot(bundle_reference="n3:host:bundle")
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        self.assertEqual(revision, snapshot.identity.source_revision)
        schema = json.loads((ROOT / "data/schemas/m3_reference_diagnostic_bundle_schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(snapshot.to_record())
        exported = diagnostics.export_pair(snapshot)
        self.assertEqual("COMPLETE", exported.status)
        wire = json.loads((diagnostics.store.root / "diagnostics.json").read_bytes())
        markdown = (diagnostics.store.root / "diagnostics.md").read_bytes()
        embedded = json.loads(markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0])
        self.assertEqual(snapshot.to_record(), wire)
        self.assertEqual(wire, embedded)
        self.assertTrue(wire["supporting_evidence"]["session_commands"])
        self.assertTrue(wire["supporting_evidence"]["session_denials"])
        self.assertEqual(0, diagnostics.health().active_reservations)


class FreshOriginIntegrationTests(unittest.TestCase):
    def test_unavailable_provider_retains_actual_fact_without_child_or_n2(self):
        class Provider(n2.PostFacts):
            def provide(self, *args, **kwargs):
                self.actual = super().provide(*args, **kwargs)
                return self.actual
        provider = Provider(n2.profile(), mode="UNAVAILABLE")
        _, _, session, _, diagnostics, store, _, origin, *_ = lifecycle_fixture.assembly(provider=provider)
        before = len([call for call in store.calls if call[0] == "commit_event"])
        with mock.patch.object(diagnostics, "recovery_capture", wraps=diagnostics.recovery_capture) as capture:
            result = session.execute(lifecycle_fixture.recover_command(session, origin))
        self.assertFalse(result.session_effects_performed)
        self.assertEqual("SESSION_ORIGIN_REJECTED", result.failure_detail.failure_code)
        self.assertIs(provider.actual, result.failure_detail.primary_evidence)
        self.assertIsNone(result.origin_assessment)
        self.assertIsNone(result.recovery_result)
        self.assertIsNone(result.origin_completion_observation)
        self.assertEqual(before, len([call for call in store.calls if call[0] == "commit_event"]))
        capture.assert_not_called()
        self.assertEqual(1, len(provider.calls))
        self.assertEqual("n3:recover:origin:assessment", provider.calls[0][2].assessment_reference)

    def test_wrong_provider_context_binding_or_exception_never_reaches_n2(self):
        cases = (("BAD_BINDING", False, "SESSION_EVIDENCE_MISMATCH", "origin_assessment"),
                 (None, True, "SESSION_EVIDENCE_MISMATCH", "operation_context.context_observation"),
                 ("THROW", False, "SESSION_COLLABORATOR_FAILED", "collaborator"))
        for mode, contained, code, field in cases:
            with self.subTest(mode=mode, contained=contained):
                provider = n2.PostFacts(n2.profile(), mode=mode, contained=contained)
                _, _, session, _, diagnostics, store, _, origin, *_ = lifecycle_fixture.assembly(provider=provider)
                before = tuple(store.calls)
                with mock.patch.object(diagnostics, "recovery_capture", wraps=diagnostics.recovery_capture) as capture:
                    result = session.execute(lifecycle_fixture.recover_command(session, origin))
                self.assertEqual((code, field), (result.failure_detail.failure_code, result.failure_detail.field_name))
                self.assertFalse(result.session_effects_performed)
                self.assertIsNone(result.recovery_result)
                self.assertIsNone(result.origin_assessment)
                self.assertIsNone(result.origin_completion_observation)
                self.assertEqual([call for call in before if call[0] == "commit_event"],
                                 [call for call in store.calls if call[0] == "commit_event"])
                final_commands = [call for call in store.calls[len(before):]
                                  if call[0] == "commit_supporting" and
                                  call[1][1] == "SESSION_COMMAND"]
                self.assertEqual(1, len(final_commands))
                capture.assert_not_called()

    def test_actual_child_capture_failure_preserves_zero_or_one_confirmed_prefix_and_completes_once(self):
        class Store(diagnostic_fixture.ControlledProjectionStore):
            failure_event = None
            def commit_event(self, sequence, payload):
                prior = len([call for call in self.calls if call[0] == "commit_event"])
                if prior == self.failure_event:
                    self.calls.append(("commit_event", (sequence, payload)))
                    return dv.StorageReceipt(sequence, "REJECTED", "STORAGE_COMMIT_REJECTED")
                return self.__getattr__("commit_event")(sequence, payload)
        for prefix in (0, 1):
            with self.subTest(prefix=prefix):
                store = Store()
                _, _, session, _, diagnostics, _, _, origin, *_ = lifecycle_fixture.assembly(store=store)
                store.failure_event = len([call for call in store.calls if call[0] == "commit_event"]) + prefix
                with mock.patch.object(diagnostics, "complete_assessment", wraps=diagnostics.complete_assessment) as complete, \
                     mock.patch.object(diagnostics, "recovery_capture", wraps=diagnostics.recovery_capture) as capture:
                    result = session.execute(lifecycle_fixture.recover_command(session, origin))
                self.assertIs(type(result.origin_assessment), sv.DiagnosticCaptureFailure)
                self.assertEqual(prefix, len(result.origin_assessment.emitted_diagnostics))
                self.assertIsNotNone(result.origin_assessment.attempted_diagnostic)
                self.assertEqual("INCOMPLETE", result.origin_completion_observation.status)
                self.assertFalse(result.session_effects_performed)
                self.assertIsNone(result.recovery_result)
                complete.assert_called_once_with(result.origin_assessment)
                capture.assert_not_called()


class RecoveryCancellationIntegrationTests(unittest.TestCase):
    def test_wrong_reference_admission_receipts_still_finish_the_actual_issued_scope_once(self):
        for field, wrong in (("operation_reference", "n3:foreign:operation"),
                             ("origin_assessment_reference", "n3:foreign:assessment"),
                             ("origin_diagnostic_references", ("n3:foreign:detect", "n3:foreign:classify"))):
            with self.subTest(field=field):
                _, _, session, _, diagnostics, _, _, origin, *_ = lifecycle_fixture.assembly()
                actual_capture = diagnostics.recovery_capture
                observations = {}
                def capture(**kwargs):
                    adapter = actual_capture(**kwargs)
                    actual_begin = adapter.begin
                    def begin(*args, **parameters):
                        scope, receipt = actual_begin(*args, **parameters)
                        self.assertIsNotNone(scope)
                        scope.finish = mock.Mock(wraps=scope.finish)
                        observations["scope"] = scope
                        return scope, replace(receipt, **{field: wrong})
                    adapter.begin = begin
                    return adapter
                with mock.patch.object(diagnostics, "recovery_capture", side_effect=capture):
                    result = session.execute(lifecycle_fixture.recover_command(session, origin))
                packet = result.recovery_result
                self.assertIs(type(packet), rv.RecoveryFailure)
                self.assertEqual("CAPTURE_ADMISSION_UNCONFIRMED", packet.failure_detail.failure_code)
                self.assertFalse(result.session_effects_performed)
                self.assertEqual((), packet.steps)
                self.assertEqual((), packet.emitted_diagnostics)
                observations["scope"].finish.assert_called_once()
                self.assertTrue(observations["scope"].finished)
                self.assertEqual([], [scope for scope in diagnostics._scopes.values() if not scope.finished])

    def test_gated_admission_with_denial_reservation_cleans_up_without_ordinary_work(self):
        _, _, session, _, diagnostics, _, _, origin, *_ = lifecycle_fixture.assembly()
        actual_capture = diagnostics.recovery_capture
        observations = {}
        def capture(**kwargs):
            adapter = actual_capture(**kwargs)
            actual_begin = adapter.begin
            def begin(*args, **parameters):
                scope, receipt = actual_begin(*args, **parameters)
                self.assertIsNotNone(scope)
                scope.finish = mock.Mock(wraps=scope.finish)
                observations["scope"] = scope
                return scope, replace(receipt, reserved_events=1, reserved_bytes=270336)
            adapter.begin = begin
            return adapter
        with mock.patch.object(diagnostics, "recovery_capture", side_effect=capture):
            result = session.execute(lifecycle_fixture.recover_command(session, origin))
        packet = result.recovery_result
        self.assertIs(type(packet), rv.RecoveryFailure)
        self.assertEqual("CAPTURE_ADMISSION_UNCONFIRMED", packet.failure_detail.failure_code)
        self.assertFalse(result.session_effects_performed)
        self.assertEqual((), packet.steps)
        self.assertEqual((), packet.emitted_diagnostics)
        observations["scope"].finish.assert_called_once()

    def test_halt_returned_from_each_n2_provider_stops_following_work_and_finishes_actual_scope_once(self):
        for stage in ("NORMALIZATION_PROVIDER", "CORRECTION_PROVIDER", "CONDITION_PROVIDER", "POST_FACTS_PROVIDER"):
            with self.subTest(stage=stage):
                entries, _ = n2.entries_for()
                provider = lifecycle_fixture.EvaluatedFacts(
                    known=stage == "CORRECTION_PROVIDER", fallback=stage == "CONDITION_PROVIDER")
                integer = 1 if stage == "CONDITION_PROVIDER" else n2.source_codewords()[0][0]
                engine, _, session, _, diagnostics, _, _, origin, *_ = lifecycle_fixture.assembly(integer,
                    provider=provider, initial_known=stage == "CORRECTION_PROVIDER",
                    initial_fallback=stage == "CONDITION_PROVIDER",
                    registry_entries=entries if stage == "CONDITION_PROVIDER" else (),
                    correction_provider=lifecycle_fixture.ActualCorrection())
                observations = {}
                if stage == "NORMALIZATION_PROVIDER":
                    collaborator, method = engine._normalization, "resolve"
                elif stage == "CORRECTION_PROVIDER":
                    collaborator, method = engine._correction, "resolve"
                elif stage == "CONDITION_PROVIDER":
                    collaborator, method = engine._conditions, "evaluate"
                else:
                    collaborator, method = engine._post_facts, "provide"
                actual_provider = getattr(collaborator, method)
                def provider_return(*args, **kwargs):
                    actual = actual_provider(*args, **kwargs)
                    if stage != "POST_FACTS_PROVIDER" or ":origin:assessment" not in kwargs["diagnostic_context"].assessment_reference:
                        observations["halt"] = session.execute(lifecycle_fixture.halt_command(session, "n3:stage:halt"))
                        observations["frozen"] = session.history()
                    return actual
                actual_capture = diagnostics.recovery_capture
                def capture(**kwargs):
                    adapter = actual_capture(**kwargs)
                    actual_begin = adapter.begin
                    def begin(*args, **parameters):
                        scope, receipt = actual_begin(*args, **parameters)
                        self.assertIsNotNone(scope)
                        scope.finish = mock.Mock(wraps=scope.finish)
                        observations["scope"] = scope
                        return scope, receipt
                    adapter.begin = begin
                    return adapter
                with mock.patch.object(collaborator, method, side_effect=provider_return) as callback, \
                     mock.patch.object(diagnostics, "recovery_capture", side_effect=capture):
                    result = session.execute(lifecycle_fixture.recover_command(session, origin))
                packet = result.recovery_result
                self.assertIs(type(packet), rv.RecoveryFailure)
                self.assertEqual("SESSION_EXECUTION_CANCELLED", packet.failure_detail.failure_code)
                self.assertFalse(result.session_effects_performed)
                self.assertTrue(observations["halt"].session_effects_performed)
                self.assertEqual("SAFE_HALT", session.read().mode)
                observations["scope"].finish.assert_called_once()
                self.assertEqual(observations["frozen"].confirmed_lifecycle_records, session.history().confirmed_lifecycle_records)
                self.assertEqual(observations["frozen"].terminal_snapshot, session.history().terminal_snapshot)
                self.assertEqual(2 if stage == "POST_FACTS_PROVIDER" else 1, callback.call_count)
                if stage == "POST_FACTS_PROVIDER":
                    self.assertTrue(packet.steps)
                    self.assertEqual((), packet.post_assessments)
                else:
                    self.assertEqual((), packet.steps)
                self.assertFalse(any(step.action in ("CORRECTION_XOR", "FALLBACK_SELECT") for step in packet.steps))

    def test_reentrant_halt_during_fresh_provider_revokes_before_child_capture_and_keeps_frozen_membership(self):
        class Provider(n2.PostFacts):
            def provide(self, *args, **kwargs):
                self.halt = self.session.execute(lifecycle_fixture.halt_command(self.session, "n3:provider:halt"))
                self.sealed = self.session.history()
                return super().provide(*args, **kwargs)
        provider = Provider(n2.profile())
        _, _, session, _, diagnostics, _, _, origin, *_ = lifecycle_fixture.assembly(provider=provider)
        provider.session = session
        with mock.patch.object(diagnostics, "recovery_capture", wraps=diagnostics.recovery_capture) as capture:
            result = session.execute(lifecycle_fixture.recover_command(session, origin))
        self.assertTrue(provider.halt.session_effects_performed)
        self.assertTrue(session.read().terminal_latched)
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertEqual("SESSION_EXECUTION_CANCELLED", result.failure_detail.failure_code)
        self.assertFalse(result.session_effects_performed)
        self.assertIsNone(result.recovery_result)
        self.assertEqual(provider.sealed.confirmed_lifecycle_records, session.history().confirmed_lifecycle_records)
        self.assertEqual(provider.sealed.terminal_snapshot, session.history().terminal_snapshot)
        capture.assert_not_called()

    def test_scope_returned_before_halt_is_finished_once_even_with_unconfirmed_admission(self):
        for unconfirmed in (False, True):
            with self.subTest(unconfirmed=unconfirmed):
                _, _, session, _, diagnostics, _, _, origin, *_ = lifecycle_fixture.assembly()
                actual_capture = diagnostics.recovery_capture
                observations = {}
                def capture(**kwargs):
                    adapter = actual_capture(**kwargs)
                    actual_begin = adapter.begin
                    def begin(*args, **parameters):
                        scope, receipt = actual_begin(*args, **parameters)
                        self.assertIsNotNone(scope)
                        scope.finish = mock.Mock(wraps=scope.finish)
                        observations["scope"] = scope
                        observations["halt"] = session.execute(lifecycle_fixture.halt_command(session, "n3:admission:halt"))
                        if unconfirmed:
                            receipt = replace(receipt, status="NOT_CONFIRMED", reserved_events=0,
                                reserved_bytes=0, failure_code="DIAGNOSTICS_REPLAY_REFUSED")
                        return scope, receipt
                    adapter.begin = begin
                    return adapter
                with mock.patch.object(diagnostics, "recovery_capture", side_effect=capture):
                    result = session.execute(lifecycle_fixture.recover_command(session, origin))
                packet = result.recovery_result
                self.assertIs(type(packet), rv.RecoveryFailure)
                self.assertEqual("SESSION_EXECUTION_CANCELLED", packet.failure_detail.failure_code)
                self.assertTrue(observations["halt"].session_effects_performed)
                self.assertTrue(session.read().terminal_latched)
                self.assertFalse(result.session_effects_performed)
                observations["scope"].finish.assert_called_once()
                self.assertEqual((), packet.steps)
                self.assertEqual((), packet.emitted_diagnostics)


if __name__ == "__main__":
    unittest.main()
