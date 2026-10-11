"""Actual N3 collector controls [YWE-REQ-0044].

Portable port responses are declared synthetic; the protected-file test uses
the actual Windows store. Neither fixture establishes physical crash behavior.
"""
from __future__ import annotations

import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import threading
import unittest
from unittest import mock

from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import diagnostic_session_values as safe
from core.ash_pattern_engine import session_values as v
from core.ash_pattern_engine import recovery_values as rv
from core.ash_pattern_engine import state_values as sv
from tests.test_m3_session_lifecycle import (assembly, contain_command, halt_command,
    resolve_command, recover_command, authority, request, EvaluatedFacts)
from tests.test_m3_reference_diagnostics import ControlledProjectionStore
from tests import test_m3_recovery as n2
from scripts.reference_diagnostics_host import assemble_reference_diagnostics

ROOT = Path(__file__).resolve().parents[1]


class CallbackStore(ControlledProjectionStore):
    def __init__(self):
        super().__init__()
        self.callback = None
        self.callback_method = "commit_event"
        self.unknown_kind = None
        self.unknown_event_sequence = None

    def __getattr__(self, name):
        original = super().__getattr__(name)
        def operation(*args):
            result = original(*args)
            if name == self.callback_method and self.callback is not None:
                callback, self.callback = self.callback, None
                callback()
            if name == "commit_supporting" and args[1] == self.unknown_kind:
                return dv.StorageReceipt(args[0], "UNKNOWN", "STORAGE_COMMIT_UNCONFIRMED")
            if name == "commit_event" and args[0] == self.unknown_event_sequence:
                return dv.StorageReceipt(args[0], "UNKNOWN", "STORAGE_COMMIT_UNCONFIRMED")
            return result
        return operation


def runtime_bundle_controls():
    """Reproducible real collector outputs with declared synthetic port inputs."""
    cases = []
    values = assembly()
    session, diagnostics = values[2], values[4]
    session.execute(contain_command(session))
    session.execute(resolve_command(session))
    session.execute(contain_command(session, "n3:contain-again"))
    session.execute(halt_command(session))
    session.execute(object())
    session.execute(object())
    cases.append(dict(case_id="complete-contained-resolution-later-containment-halt-denials",
        operation_scope="Actual containment, direct resolution, later containment, first halt and two terminal denials.",
        snapshot=diagnostics.snapshot(bundle_reference="n3:fixture:complete").to_record()))
    store = CallbackStore()
    values = assembly(store=store)
    store.unknown_event_sequence = 3
    values[2].execute(recover_command(values[2], values[7]))
    cases.append(dict(case_id="partial-fresh-origin-one-confirmed-one-unknown",
        operation_scope="Actual fresh origin first record confirmed; second write returns UNKNOWN; first finish is INCOMPLETE; no N2.",
        snapshot=values[4].snapshot(bundle_reference="n3:fixture:partial").to_record()))
    values = assembly(provider=n2.PostFacts(n2.profile(), mode="UNAVAILABLE"))
    values[2].execute(recover_command(values[2], values[7]))
    cases.append(dict(case_id="unavailable-origin-facts-no-child-no-n2",
        operation_scope="Actual declared unavailable origin facts, bounded inline failure projection and no assessment/N2 records.",
        snapshot=values[4].snapshot(bundle_reference="n3:fixture:unavailable").to_record()))
    return dict(artifact_type="ywe_session_diagnostic_runtime_controls", artifact_version="1.0.0",
        requirement_id="YWE-REQ-0044",
        provenance=dict(execution="tests.test_m3_session_diagnostics.runtime_bundle_controls",
            clock="tests.test_m3_reference_diagnostics.ControlledClock",
            storage="ControlledProjectionStore with explicitly declared UNKNOWN response control",
            source_identity="Explicit synthetic configured aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa revision; no host verification claim.",
            evidence_scope="Actual reference collector execution under synthetic ports; no native protection, physical crash, authority or power-loss qualification."),
        cases=cases)


class SessionCollectorTests(unittest.TestCase):
    def admitted(self, *, store=None):
        values = assembly(store=store)
        owner, session = values[1], values[2]
        op = owner._admit(contain_command(session))
        owner._begin_scope(op)
        return values, op

    def test_registration_pins_actual_initial_graph_without_holding_n3_scope(self):
        values = assembly()
        diagnostics, receipt = values[4], values[-1]
        self.assertEqual("CONFIRMED", receipt.status)
        self.assertEqual(0, diagnostics.health().active_reservations)
        self.assertEqual(1, len(diagnostics._support["SESSION_BINDING"]))
        self.assertEqual(0, len(diagnostics._support["SESSION_HISTORY"]))

    def test_containment_pair_uses_actual_parent_four_slots_and_actual_context(self):
        values = assembly()
        result = values[2].execute(contain_command(values[2]))
        diagnostics = values[4]
        scope = diagnostics._lifecycle_scopes[result.request.request.request_reference]
        child = diagnostics._scopes[result.actual_post_assessment.assessment_binding.assessment_reference]
        self.assertEqual("COMPLETE", result.completion_observation.status)
        self.assertEqual(scope.storage_reference, child.budget_parent)
        self.assertEqual(0, scope.remaining_events)
        self.assertTrue(result.actual_post_assessment.system_context.is_in_containment)
        self.assertEqual(4, len(scope.indices) + len(child.indices))
        self.assertEqual(0, diagnostics.health().active_reservations)

    def test_resolution_control_has_no_ten_and_freezes_previous_episode(self):
        values = assembly()
        session, diagnostics = values[2], values[4]
        contained = session.execute(contain_command(session))
        old = contained.confirmed_lifecycle_records[-1]
        resolved = session.execute(resolve_command(session))
        control = next(event for event in diagnostics._events if event.message_template == "CONTAINMENT_RESOLUTION_RECORDED")
        self.assertIsNone(control.envelope)
        self.assertIsNone(control.diagnostic_reference)
        self.assertEqual("COMPLETED", control.outcome)
        self.assertIsNotNone(control.context.resolution_evidence_reference)
        later = session.execute(contain_command(session, "n3:contain-again"))
        bridge = later.confirmed_lifecycle_records[0]
        self.assertEqual(resolved.actual_post_assessment.emitted_diagnostics[-1].diagnostic_reference, bridge.envelope.parent_diagnostic_reference)
        self.assertNotEqual(old.diagnostic_reference, bridge.envelope.parent_diagnostic_reference)
        self.assertEqual("COMPLETE", later.completion_observation.status)

    def test_n2_and_lifecycle_preserve_distinct_scopes_with_same_public_reference(self):
        values = assembly()
        result = values[2].execute(recover_command(values[2], values[7]))
        diagnostics = values[4]
        n2 = diagnostics._scopes["n3:recover"]
        n3 = diagnostics._lifecycle_scopes["n3:recover"]
        self.assertIsNot(n2, n3)
        self.assertEqual(n2.reference, n3.reference)
        self.assertEqual(result.recovery_result.completion_observation, n2.completion_response)
        self.assertEqual(result.completion_observation, n3.completion_response)
        self.assertEqual("COMPLETED", result.status)

    def test_foreign_or_copied_gate_is_refused_before_io(self):
        values, op = self.admitted()
        other = assembly()
        before = len(other[5].calls)
        with self.assertRaises(v.SessionContractError):
            copy.copy(op.gate)
        copied = object.__new__(v.SessionExecutionGate)
        for name in v.SessionExecutionGate.__slots__:
            setattr(copied, name, getattr(op.gate, name))
        for gate in (op.gate, copied):
            with self.assertRaises(dv.DiagnosticsContractError):
                other[4].recovery_capture(execution_gate=gate)
            with self.assertRaises(dv.DiagnosticsContractError):
                other[4].assessment_capture(execution_gate=gate)
        self.assertEqual(before, len(other[5].calls))
        with self.assertRaises(dv.DiagnosticsContractError):
            values[4].lifecycle_capture(other[1]._handle, execution_gate=op.gate)

    def test_scope_clock_rechecks_gate_after_actual_callback(self):
        values, op = self.admitted()
        clock = values[6]
        original = clock.read
        def read():
            observed = original()
            v._set_capture_disposition(values[1], op.gate, "SEALED")
            return observed
        clock.read = read
        with self.assertRaises(dv.DiagnosticsContractError):
            op.scope.observe_clock()
        self.assertEqual(0, len(op.scope.scope.indices))

    def test_callback_physical_event_after_seal_is_retained_without_ack(self):
        store = CallbackStore()
        values, op = self.admitted(store=store)
        owner, diagnostics = values[1], values[4]
        cause = v.SessionCauseObservation("n3:contain:cause", "n3:contain", op.lease.before.snapshot_reference,
            "AUTHORITY_REQUEST", "OPERATOR_REQUEST", None, op.command.authority_observation, ())
        op.cause = cause
        record = owner._bridge(op, "ESCALATE_TO_CONTAINMENT")
        store.callback = lambda: v._set_capture_disposition(owner, op.gate, "SEALED")
        receipt = op.scope.append(record)
        self.assertNotEqual("CONFIRMED", receipt.status)
        self.assertNotIn(record.diagnostic_reference, diagnostics._acks)
        self.assertTrue(op.scope.scope.late_indices)
        self.assertTrue(any(event.event_id == diagnostics._aliases[record.diagnostic_reference] for event in diagnostics._events))

    def test_terminal_capture_refuses_io_depth_without_waiting_or_extending_chain(self):
        values = assembly()
        diagnostics, session = values[4], values[2]
        diagnostics._io_depth = 1
        calls = len(values[5].calls)
        halted = session.execute(halt_command(session))
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertTrue(halted.session_effects_performed)
        self.assertIsNotNone(halted.pending_lifecycle_record)
        self.assertEqual(calls, len(values[5].calls))
        diagnostics._io_depth = 0

    def test_support_callback_halt_preserves_outer_charge_and_stops_next_projection(self):
        from core.ash_pattern_engine.session import _Refusal
        store = CallbackStore()
        values = assembly(store=store)
        owner, session, diagnostics = values[1], values[2], values[4]
        op = owner._admit(contain_command(session))
        observed = []
        store.callback_method = "commit_supporting"
        def halt_during_support():
            scope = diagnostics._charging_scope
            observed.append((scope, scope.remaining_bytes))
            halted = session.execute(halt_command(session, "n3:callback-halt"))
            observed.append((diagnostics._charging_scope, halted))
        store.callback = halt_during_support
        first_call = len(store.calls)
        with self.assertRaises(_Refusal) as refused:
            owner._begin_scope(op)
        self.assertEqual("SESSION_CAPTURE_FAILED", refused.exception.code)
        scope, budget_before = observed[0]
        self.assertIs(scope, observed[1][0])
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertIsNotNone(observed[1][1].pending_lifecycle_record)
        writes = [args for method, args in store.calls[first_call:] if method == "commit_supporting"]
        self.assertEqual(1, len(writes))
        self.assertEqual(budget_before - len(writes[0][-1]), scope.remaining_bytes)
        self.assertEqual(scope.reserved_supporting_bytes - len(writes[0][-1]), scope.remaining_supporting_bytes)
        self.assertNotIn("SESSION_AUTHORITY", {args[1] for args in writes})
        self.assertNotIn("SESSION_REQUEST", {args[1] for args in writes})
        self.assertIsNone(diagnostics._charging_scope)
        self.assertIs(op.scope.scope, scope)
        self.assertNotIn("n3:contain", diagnostics._session_state(owner._handle).observed)

    def test_terminal_capture_does_not_wait_for_other_thread_collector_lock(self):
        values = assembly()
        acquired, release = threading.Event(), threading.Event()
        def hold():
            with values[4]._lock:
                acquired.set()
                release.wait(5)
        worker = threading.Thread(target=hold)
        worker.start()
        self.assertTrue(acquired.wait(2))
        try:
            halted = values[2].execute(halt_command(values[2]))
            self.assertEqual("SAFE_HALT", values[2].read().mode)
            self.assertIsNotNone(halted.pending_lifecycle_record)
        finally:
            release.set(); worker.join(2)
        self.assertFalse(worker.is_alive())

    def test_once_final_sidecar_and_history_index_are_immutable(self):
        values = assembly()
        session, diagnostics = values[2], values[4]
        result = session.execute(halt_command(session))
        state = diagnostics._session_state(values[1]._handle)
        self.assertEqual("CONFIRMED", state.freeze_receipt.status)
        before = {kind: {alias: node.to_record() for alias, node in rows.items()} for kind, rows in diagnostics._support.items()}
        refused = diagnostics.observe_session_result(values[1]._handle, result)
        self.assertNotEqual("CONFIRMED", refused.status)
        refused = diagnostics.freeze_terminal(values[1]._handle, session.history(), result.publication)
        self.assertNotEqual("CONFIRMED", refused.status)
        self.assertEqual(before, {kind: {alias: node.to_record() for alias, node in rows.items()} for kind, rows in diagnostics._support.items()})
        pages = tuple(diagnostics._support["SESSION_HISTORY_PAGE"].values())
        indexed = {(item.kind, item.evidence_reference) for page in pages for item in page.supporting_references}
        self.assertIn(("SESSION_HISTORY", next(iter(diagnostics._support["SESSION_HISTORY"]))), indexed)
        self.assertFalse(any(kind == "SESSION_HISTORY_PAGE" for kind, alias in indexed))

    def test_terminal_denials_are_separate_roots_and_never_rewrite_index(self):
        values = assembly()
        session, diagnostics = values[2], values[4]
        session.execute(halt_command(session))
        index = tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY_PAGE"].values())
        for ordinal in range(1, 17):
            denied = session.execute(object())
            self.assertEqual(ordinal, denied.denial_ordinal)
            self.assertEqual("CONFIRMED", denied.capture_status)
            self.assertEqual("COMPLETE", denied.completion_observation.status)
            self.assertIsNone(denied.attempted_record.envelope.parent_diagnostic_reference)
        overflow = session.execute(object())
        self.assertIsNone(overflow.denial_ordinal)
        self.assertEqual(16, len(diagnostics._support["SESSION_DENIED"]))
        self.assertEqual(index, tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY_PAGE"].values()))

    def test_unknown_supporting_write_cannot_be_reported_complete(self):
        store = CallbackStore()
        values = assembly(store=store)
        store.unknown_kind = "SESSION_COMMAND"
        result = values[2].execute(contain_command(values[2]))
        self.assertEqual("COMPLETE", result.completion_observation.status)
        self.assertEqual("AUDIT_BLOCKED", values[2].read().admission_status)
        state = values[4]._session_state(values[1]._handle)
        self.assertTrue(state.pinned_support & values[4]._unconfirmed_support.keys())
        self.assertEqual(0, len(values[4]._support["SESSION_COMMAND"]))

    def test_current_session_pin_preserves_actual_native_files_on_purge(self):
        if os.name != "nt":
            self.skipTest("Actual adopted protected storage is Windows-specific")
        actual = assemble_reference_diagnostics(ROOT)
        self.addCleanup(actual.store.close)
        values = assembly(store=actual.store)
        result = values[2].execute(contain_command(values[2]))
        self.assertEqual("COMPLETE", result.completion_observation.status)
        from tests import test_m3_recovery as n2
        unrelated = n2.assessment(values[3], n2.ash(0), reference="n3:unpinned", known=False, fallback=False)
        self.assertEqual("COMPLETE", values[4].complete_assessment(unrelated).status)
        before = {path.name: path.read_bytes() for path in actual.store.root.glob("*.json")}
        receipt = values[4].purge_completed(through_sequence=1000)
        self.assertEqual("COMPLETED", receipt.status)
        after = {path.name: path.read_bytes() for path in actual.store.root.glob("*.json")}
        # Health is refreshed by purge; selected event/support files are fixed.
        selected_sequences = set(range(6))
        selected_aliases = values[4]._session_state(values[1]._handle).pinned_support
        selected = {name: raw for name, raw in before.items() if name.startswith("support-") and
            any(name == "support-" + kind + "-" + alias[4:] + ".json" for kind, alias in selected_aliases) or name.startswith("event-") and
            any(str(sequence).zfill(20) in name for sequence in selected_sequences)}
        self.assertTrue(selected)
        self.assertTrue(any(name.startswith("support-") for name in selected))
        self.assertEqual(selected, {name: after[name] for name in selected})

    def test_unknown_final_support_root_survives_actual_unrelated_purge(self):
        if os.name != "nt":
            self.skipTest("Actual adopted protected storage is Windows-specific")
        actual = assemble_reference_diagnostics(ROOT)
        self.addCleanup(actual.store.close)
        class UnknownFinalStore:
            enabled = False
            def __getattr__(self, name):
                return getattr(actual.store, name)
            def commit_supporting(self, sequence, kind, alias, payload):
                observed = actual.store.commit_supporting(sequence, kind, alias, payload)
                if self.enabled and kind == "SESSION_COMMAND":
                    return dv.StorageReceipt(sequence, "UNKNOWN", "STORAGE_COMMIT_UNCONFIRMED")
                return observed
        store = UnknownFinalStore()
        values = assembly(store=store)
        diagnostics = values[4]
        unrelated = n2.assessment(values[3], n2.ash(0), reference="n3:unrelated-purge")
        self.assertEqual("COMPLETE", diagnostics.complete_assessment(unrelated).status)
        unrelated_indices = tuple(diagnostics._scopes[unrelated.assessment_binding.assessment_reference].indices)
        store.enabled = True
        values[2].execute(contain_command(values[2]))
        key = next(key for key in diagnostics._unconfirmed_support if key[0] == "SESSION_COMMAND")
        path = actual.store.root / ("support-" + key[0] + "-" + key[1][4:] + ".json")
        retained_bytes = path.read_bytes()
        receipt = diagnostics.purge_completed(through_sequence=1000)
        self.assertEqual("COMPLETED", receipt.status)
        self.assertTrue(set(unrelated_indices).isdisjoint(event.local_sequence for event in diagnostics._events))
        self.assertIn(key, diagnostics._session_state(values[1]._handle).pinned_support)
        self.assertIn(key, diagnostics._unconfirmed_support)
        self.assertEqual(retained_bytes, path.read_bytes())
        self.assertEqual("PARTIAL", diagnostics.health().coverage_status)

    def test_actual_protected_pair_contains_all_new_support_kinds_with_exact_parity(self):
        if os.name != "nt":
            self.skipTest("Actual adopted protected storage is Windows-specific")
        actual = assemble_reference_diagnostics(ROOT)
        self.addCleanup(actual.store.close)
        values = assembly(store=actual.store)
        session, diagnostics = values[2], values[4]
        self.assertEqual("COMPLETED", session.execute(recover_command(session, values[7])).status)
        submitted = request(session, "n3:denied-authority", "REQUEST_CONTAINMENT")
        sentinel = "session-untrusted-prose-must-not-persist"
        submitted = replace(submitted, reason=sentinel)
        denied = v.SessionContainmentRequest(submitted, "OPERATOR_REQUEST", authority(submitted, status="DENIED"), (), None)
        self.assertEqual("REFUSED", session.execute(denied).status)
        self.assertEqual("COMPLETED", session.execute(contain_command(session)).status)
        self.assertEqual("COMPLETED", session.execute(resolve_command(session)).status)
        self.assertEqual("COMPLETED", session.execute(halt_command(session)).status)
        session.execute(object())
        snapshot = diagnostics.snapshot(bundle_reference="n3:actual-pair")
        for name, _kind, _cls, _maximum in dv.SESSION_SUPPORT_FIELDS:
            self.assertTrue(getattr(snapshot.supporting_evidence, name), name)
        pair = diagnostics.export_pair(snapshot)
        self.assertIs(type(pair), dv.ExportReceipt)
        raw = (actual.store.root / "diagnostics.json").read_bytes()
        markdown = (actual.store.root / "diagnostics.md").read_bytes()
        embedded = markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0]
        self.assertEqual(raw, embedded)
        self.assertEqual(snapshot.to_record(), json.loads(raw))
        self.assertNotIn(sentinel.encode("ascii"), raw + markdown)
        self.assertEqual(("JSON", "MARKDOWN", "MANIFEST"), tuple(part.part for part in pair.parts))

    def test_interrupted_returns_keep_separate_final_audit_without_extending_frozen_index(self):
        for during_post in (False, True):
            with self.subTest(during_post=during_post):
                class Provider(EvaluatedFacts):
                    def provide(self, *args, **kwargs):
                        result = super().provide(*args, **kwargs)
                        post = ":origin:assessment" not in kwargs["diagnostic_context"].assessment_reference
                        if post == during_post:
                            self.halt = self.session.execute(halt_command(self.session, "n3:callback-halt"))
                            self.index = tuple(node.to_record() for node in self.diagnostics._support["SESSION_HISTORY_PAGE"].values())
                        return result
                provider = Provider()
                values = assembly(30 if during_post else 0, provider=provider)
                provider.session, provider.diagnostics = values[2], values[4]
                result = values[2].execute(recover_command(values[2], values[7]))
                self.assertEqual("SESSION_EXECUTION_CANCELLED", result.failure_detail.failure_code)
                self.assertFalse(result.session_effects_performed)
                self.assertEqual("SAFE_HALT", values[2].read().mode)
                diagnostics = values[4]
                self.assertEqual(provider.index, tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY_PAGE"].values()))
                state = diagnostics._session_state(values[1]._handle)
                self.assertIn("n3:recover", state.observed)
                sidecar = next(node for node in diagnostics._support["SESSION_COMMAND"].values()
                    if node.request_evidence_reference == diagnostics._projection(state).key("SESSION_REQUEST", result.request))
                self.assertEqual("FAILED", sidecar.operation_status)
                self.assertEqual("PARTIAL", sidecar.projection_coverage)
                self.assertEqual(0, diagnostics.health().active_reservations)
                if during_post:
                    self.assertIs(type(result.recovery_result), rv.RecoveryFailure)
                    self.assertTrue(diagnostics._scopes["n3:recover"].finished)
                    self.assertIsNotNone(result.recovery_result.completion_observation)

    def test_actual_protected_pair_retains_interrupted_audit_outside_frozen_index(self):
        if os.name != "nt":
            self.skipTest("Actual adopted protected storage is Windows-specific")
        for during_post in (False, True):
            with self.subTest(during_post=during_post):
                actual = assemble_reference_diagnostics(ROOT)
                self.addCleanup(actual.store.close)
                class Provider(EvaluatedFacts):
                    def provide(self, *args, **kwargs):
                        observed = super().provide(*args, **kwargs)
                        post = ":origin:assessment" not in kwargs["diagnostic_context"].assessment_reference
                        if post == during_post:
                            self.session.execute(halt_command(self.session, "n3:callback-halt"))
                            self.index = tuple(node.to_record() for node in self.diagnostics._support["SESSION_HISTORY_PAGE"].values())
                        return observed
                provider = Provider()
                values = assembly(30 if during_post else 0, provider=provider, store=actual.store)
                provider.session, provider.diagnostics = values[2], values[4]
                result = values[2].execute(recover_command(values[2], values[7]))
                diagnostics = values[4]
                state = diagnostics._session_state(values[1]._handle)
                sidecar = next(node for node in diagnostics._support["SESSION_COMMAND"].values()
                    if node.request_evidence_reference == diagnostics._projection(state).key("SESSION_REQUEST", result.request))
                self.assertEqual("SESSION_EXECUTION_CANCELLED", result.failure_detail.failure_code)
                self.assertEqual("PARTIAL", sidecar.projection_coverage)
                self.assertEqual(provider.index, tuple(node.to_record() for node in diagnostics._support["SESSION_HISTORY_PAGE"].values()))
                self.assertNotIn(sidecar.evidence_reference, json.dumps(provider.index))
                snapshot = diagnostics.snapshot(bundle_reference="n3:interrupted-pair")
                pair = diagnostics.export_pair(snapshot)
                self.assertIs(type(pair), dv.ExportReceipt)
                raw = (actual.store.root / "diagnostics.json").read_bytes()
                markdown = (actual.store.root / "diagnostics.md").read_bytes()
                embedded = markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0]
                self.assertEqual(raw, embedded)
                self.assertEqual(snapshot.to_record(), json.loads(raw))
                self.assertIn(sidecar.evidence_reference.encode("ascii"), raw)
                self.assertEqual(0, diagnostics.health().active_reservations)

    def test_unavailable_post_facts_inline_projection_keeps_exact_declared_facts(self):
        values = assembly()
        diagnostics, state = values[4], values[4]._session_state(values[1]._handle)
        submitted = contain_command(values[2])
        source = submitted.authority_observation.source_binding
        facts = rv.UnavailablePostAssessmentFacts("n3:unavailable", submitted.request.expected_snapshot.current_state,
            source, "Untrusted private reason is not retained.")
        failure = v.SessionFailureDetail("SESSION_COLLABORATOR_FAILED", "origin_assessment", facts, None, None, None, None, None, "Actual facts are unavailable.")
        admitted = v.SessionAdmission("REJECTED", submitted.request, submitted.request.expected_snapshot, None,
            "SESSION_COLLABORATOR_FAILED", "origin_assessment", "Unavailable observation.")
        context = values[1]._context(submitted.request, submitted.request.expected_snapshot)
        result = v.SessionOperationResult(submitted, "REFUSED", submitted.request.expected_snapshot, submitted.request.expected_snapshot,
            False, admitted, context, None, None, None, None, None, None, (), (), None, None, None, failure, None, None)
        receipt = diagnostics.observe_session_result(values[1]._handle, result)
        self.assertEqual("CONFIRMED", receipt.status)
        leaf = next(iter(diagnostics._support["SESSION_FAILURE"].values()))
        self.assertIsNone(leaf.primary_evidence_reference)
        self.assertEqual(facts.candidate_state_reference.signature, leaf.unavailable_post_assessment_facts.candidate_state)
        self.assertEqual(diagnostics._aliases[source.evidence_reference], leaf.unavailable_post_assessment_facts.source_binding.evidence_reference)
        self.assertNotIn("Untrusted private reason", json.dumps(leaf.to_record()))

    def test_new_safe_nodes_and_full_actual_bundle_obey_closed_schema(self):
        import jsonschema
        values = assembly()
        session, diagnostics = values[2], values[4]
        session.execute(contain_command(session))
        session.execute(resolve_command(session))
        session.execute(halt_command(session))
        schema = json.loads((ROOT / "data/schemas/m3_reference_diagnostic_bundle_schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        snapshot = diagnostics.snapshot(bundle_reference="n3:test:snapshot")
        jsonschema.Draft202012Validator(schema).validate(snapshot.to_record())
        record = snapshot.to_record()
        record["supporting_evidence"]["session_commands"][0]["invented"] = True
        self.assertTrue(tuple(jsonschema.Draft202012Validator(schema).iter_errors(record)))

    def test_registered_runtime_controls_reproduce_exact_safe_bundles(self):
        import jsonschema
        actual = runtime_bundle_controls()
        declared = json.loads((ROOT / "examples/core_session_diagnostics/session_diagnostic_bundle_cases.example.json").read_text(encoding="utf-8"))
        self.assertEqual(declared, actual)
        schema = json.loads((ROOT / "data/schemas/m3_reference_diagnostic_bundle_schema.json").read_text(encoding="utf-8"))
        for case in actual["cases"]:
            with self.subTest(case=case["case_id"]):
                jsonschema.Draft202012Validator(schema).validate(case["snapshot"])

    def test_real_n2_admission_survives_callback_cutover_and_finishes_once(self):
        store = CallbackStore()
        values = assembly(store=store)
        diagnostics, session = values[4], values[2]
        issued = []
        store.callback_method = "commit_health"
        def at_health():
            scope = diagnostics._scopes.get("n3:recover")
            if scope is None:
                store.callback = at_health
                return
            issued.append(scope)
            session.execute(halt_command(session, "n3:callback-halt"))
        store.callback = at_health
        result = session.execute(recover_command(session, values[7]))
        self.assertEqual("SAFE_HALT", session.read().mode)
        self.assertEqual(1, len(issued))
        scope = issued[0]
        self.assertIs(scope, diagnostics._scopes["n3:recover"])
        self.assertTrue(scope.finished)
        self.assertIsNotNone(scope.completion_response)
        self.assertEqual("INCOMPLETE", scope.completion_response.status)
        self.assertEqual(scope.completion_response, result.recovery_result.completion_observation)
        self.assertFalse(scope.indices)

    def test_partial_fresh_child_keeps_actual_prefix_uncertain_root_and_once_final_failure(self):
        for prefix in (0, 1):
            with self.subTest(prefix=prefix):
                store = CallbackStore()
                values = assembly(store=store)
                owner, session, diagnostics = values[1], values[2], values[4]
                store.unknown_event_sequence = 2 + prefix
                result = session.execute(recover_command(session, values[7]))
                self.assertIs(type(result.origin_assessment), sv.DiagnosticCaptureFailure)
                self.assertEqual(prefix, len(result.origin_assessment.emitted_diagnostics))
                self.assertEqual("INCOMPLETE", result.origin_completion_observation.status)
                self.assertIsNone(result.recovery_result)
                self.assertIsNone(result.completion_observation)
                self.assertFalse(result.session_effects_performed)
                state = diagnostics._session_state(owner._handle)
                reference = result.origin_assessment.assessment_binding.assessment_reference
                self.assertIn(reference, state.pinned_scopes)
                child = diagnostics._scopes[reference]
                self.assertIsNotNone(child.completed_hash)
                self.assertEqual(result.origin_completion_observation, child.completion_response)
                self.assertIn(store.unknown_event_sequence, diagnostics._unconfirmed_events)
                self.assertEqual(1, len(diagnostics._support["SESSION_COMMAND"]))
                projected = next(iter(diagnostics._support["SESSION_COMMAND"].values()))
                self.assertEqual("PARTIAL", projected.projection_coverage)
                self.assertEqual("INCOMPLETE", projected.origin_completion_observation.status)
                self.assertEqual(prefix, len(projected.origin_completion_observation.confirmed_event_indices))
                self.assertEqual("AUDIT_BLOCKED", session.read().admission_status)
                self.assertEqual(0, diagnostics.health().active_reservations)

    def test_no_child_provider_failure_has_actual_zero_event_failure_sidecar(self):
        provider = n2.PostFacts(n2.profile(), mode="UNAVAILABLE")
        values = assembly(provider=provider)
        diagnostics, session = values[4], values[2]
        events = tuple(diagnostics._events)
        result = session.execute(recover_command(session, values[7]))
        self.assertIsNone(result.origin_assessment)
        self.assertIsNone(result.origin_completion_observation)
        self.assertIsNone(result.recovery_result)
        self.assertIsNone(result.completion_observation)
        self.assertEqual(events, tuple(diagnostics._events))
        self.assertEqual(1, len(diagnostics._support["SESSION_COMMAND"]))
        failure = next(iter(diagnostics._support["SESSION_FAILURE"].values()))
        self.assertIsNotNone(failure.unavailable_post_assessment_facts)
        self.assertEqual(0, diagnostics.health().active_reservations)

    def test_native_recovery_scope_identity_proof_does_not_accept_copy_or_other_collector(self):
        from core.ash_pattern_engine.diagnostics import _is_issued_recovery_scope
        values = assembly()
        result = values[2].execute(recover_command(values[2], values[7]))
        diagnostics = values[4]
        scope = diagnostics._scopes[result.recovery_result.operation_context.operation_reference]
        self.assertTrue(_is_issued_recovery_scope(scope, diagnostics, scope.execution_gate, scope.reference))
        self.assertFalse(_is_issued_recovery_scope(copy.copy(scope), diagnostics, scope.execution_gate, scope.reference))
        self.assertFalse(_is_issued_recovery_scope(scope, assembly()[4], scope.execution_gate, scope.reference))
        self.assertFalse(_is_issued_recovery_scope(scope, diagnostics, scope.execution_gate, "n3:foreign"))
        self.assertFalse(_is_issued_recovery_scope(scope, diagnostics, None, scope.reference))

    def test_actual_post_mode_boundary_keeps_distinct_origin_and_post_references(self):
        class BoundaryFacts(EvaluatedFacts):
            def __init__(self, mode):
                super().__init__()
                self.mode = mode

            def provide(self, *args, **kwargs):
                facts = super().provide(*args, **kwargs)
                return replace(facts, context_observation=replace(facts.context_observation,
                    context=sv.SystemContext(self.mode == "SAFE_HALT", self.mode == "CONTAINED")))

        for mode in ("CONTAINED", "SAFE_HALT"):
            with self.subTest(mode=mode):
                values = assembly(30, provider=BoundaryFacts(mode))
                engine, diagnostics, origin = values[0], values[4], values[7]
                operation = n2.operation(origin, "n3:actual-boundary:" + mode)
                result = engine.recover(origin, operation_context=operation)
                self.assertIs(type(result), rv.RecoveryHandoff)
                self.assertEqual("COMPLETE", result.completion_observation.status)
                self.assertEqual(mode, result.post_assessments[-1].assessment.system_state_class)
                projected = next(node for node in diagnostics._support["RECOVERY_SAFETY"].values()
                    if node.operation_reference == diagnostics._aliases[operation.operation_reference])
                self.assertNotEqual(projected.origin_assessment_reference,
                                    projected.directive.trigger.assessment_reference)
                self.assertEqual(diagnostics._aliases[result.post_assessments[-1].assessment.assessment_binding.assessment_reference],
                                 projected.directive.trigger.assessment_reference)

    def test_same_collector_foreign_mode_assessment_cannot_supply_operation_boundary(self):
        values = assembly(30, provider=EvaluatedFacts(failed_post=True))
        engine, model, diagnostics, origin = values[0], values[3], values[4], values[7]
        foreign = n2.assessment(model, n2.ash(0), reference="n3:foreign-boundary", contained=True)
        self.assertEqual("COMPLETE", diagnostics.complete_assessment(foreign).status)
        def foreign_boundary(operation, post, *, fallback=False):
            return operation._handoff("REMAIN_CONTAINED",
                rv.ExistingModeBoundary("CONTAINED", foreign.assessment_binding.assessment_reference),
                "Declared foreign boundary control.", request_origin="OBSERVED_EXISTING_MODE", fallback=fallback)
        with mock.patch("core.ash_pattern_engine.recovery._RecoveryOperation._post_boundary", foreign_boundary):
            result = engine.recover(origin, operation_context=n2.operation(origin, "n3:foreign-boundary-operation"))
        self.assertIs(type(result), rv.RecoveryFailure)
        self.assertEqual("COMPLETION_REJECTED", result.failure_detail.failure_code)
        self.assertEqual("DIAGNOSTICS_ORIGIN_MISMATCH", result.completion_observation.failure_code)
        self.assertEqual("INCOMPLETE", result.completion_observation.status)
        self.assertEqual("COMPLETE", result.post_assessments[-1].capture_status)

    def test_global_alias_reservation_authentically_refuses_later_n2(self):
        values = assembly()
        diagnostics = values[4]
        # Existing genuine N2 reserves5931aliases. Actual retained session
        # aliases consume headroom; no promise that a second run can fit.
        for index in range(220):
            diagnostics._alias("n3:retained:" + str(index))
        command = recover_command(values[2], values[7])
        result = values[2].execute(command)
        self.assertIs(type(result.recovery_result), rv.RecoveryFailure)
        self.assertNotIn(command.request.request_reference, diagnostics._scopes)
        self.assertIsNone(result.recovery_result.completion_observation)
        self.assertEqual("SESSION_N2_COMPLETION_UNCONFIRMED", result.failure_detail.failure_code)


if __name__ == "__main__":
    unittest.main()
