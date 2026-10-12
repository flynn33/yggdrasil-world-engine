"""Current Session data and bounded capture compatibility [YWE-REQ-0050]."""
import copy
from dataclasses import fields, replace
import inspect
import json
from pathlib import Path
import unittest
import threading
import hashlib
import os
from unittest import mock

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.ash_pattern_engine import session_values as v
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine import diagnostic_session_values as safe
from tests import test_m3_session_lifecycle as lifecycle
from tests.test_m3_session_values import values_fixture, request, authority, refused_result

ROOT = Path(__file__).resolve().parents[1]


class CurrentRetentionContextTests(unittest.TestCase):
    def current_policy(self):
        return v.SessionPolicyBinding(**dict(v.MODULE_SESSION_POLICY_BINDING_FIELDS))

    def receipt(self, count, **context):
        return v.SessionRetentionReceipt('session:retention', 'CONFIRMED', 'PIN',
            'COMPLETE_SPECIFIED_SAFE_GRAPH', 0, 0, count, None, **context)

    def test_historical_and_current_constructor_bounds_and_wire_fields(self):
        old = self.receipt(2544)
        current = self.receipt(2663, policy_binding=self.current_policy())
        for count, context in ((2545, {}), (2664, {'policy_binding': self.current_policy()})):
            with self.subTest(count=count), self.assertRaises(v.SessionContractError):
                self.receipt(count, **context)
        self.assertEqual(len(fields(old)), 8)
        signature = inspect.signature(v.SessionRetentionReceipt)
        self.assertEqual(signature.parameters['policy_binding'].kind,
            inspect.Parameter.KEYWORD_ONLY)
        expected = {'session_reference': 'session:retention', 'status': 'CONFIRMED',
            'phase': 'PIN', 'coverage': 'COMPLETE_SPECIFIED_SAFE_GRAPH',
            'confirmed_record_count': 0, 'unknown_storage_record_count': 0,
            'pinned_supporting_count': 2544, 'failure_code': None}
        self.assertEqual(old.to_record(), expected)
        self.assertEqual(v.raw_business_bytes(old), json.dumps(expected,
            ensure_ascii=True, separators=(',', ':')).encode())
        schemas = [json.loads(path.read_text()) for path in (ROOT/'data/schemas').glob('*.json')]
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema))
            for schema in schemas if '$id' in schema and '$schema' in schema)
        for receipt in (old, current):
            schema = json.loads((ROOT/v.wire_schema(receipt)).read_text())
            selected = {'$schema': schema['$schema'], '$ref': schema['$id']+'#/$defs/SessionRetentionReceipt'}
            self.assertEqual(list(Draft202012Validator(selected, registry=registry).iter_errors(receipt.to_record())), [])

    def test_copy_revalidation_replace_and_enclosing_historical_refusal(self):
        policy = self.current_policy()
        current = self.receipt(2663, policy_binding=policy)
        for item in (copy.copy(current), copy.deepcopy(current), replace(current, policy_binding=policy)):
            v.revalidate_value(item)
            self.assertEqual(item.to_record(), current.to_record())
            self.assertEqual(v.wire_schema(item), 'data/schemas/m3_current_source_session_schema.json')
        with self.assertRaises(v.SessionContractError):
            replace(current)
        _, _, _, snapshot = values_fixture()
        submitted = request(snapshot)
        command = v.SessionContainmentRequest(submitted, 'OPERATOR_REQUEST', authority(submitted), (), None)
        result = refused_result(command, primary=current)
        with self.assertRaises(v.SessionContractError):
            v.revalidate_value(result)
        with self.assertRaises(v.SessionContractError):
            result.to_record()

    def test_context_corruption_and_hostile_types_call_no_hooks(self):
        hooks = []
        class Meta(type):
            def __eq__(self, other):
                hooks.append('eq')
                return False
            def __hash__(self):
                hooks.append('hash')
                return type.__hash__(self)
        class Hostile(metaclass=Meta):
            def __str__(self):
                hooks.append('str')
                return 'hostile'
        for context in (Hostile(), v.SessionPolicyBinding(**dict(v.SESSION_POLICY_BINDING_FIELDS))):
            with self.assertRaises(v.SessionContractError):
                self.receipt(2663, policy_binding=context)
        current = self.receipt(2663, policy_binding=self.current_policy())
        object.__setattr__(current._construction_policy, 'policy_version', Hostile())
        with self.assertRaises(v.SessionContractError):
            v.revalidate_value(current)
        with self.assertRaises(v.SessionContractError):
            v.raw_business_bytes(Hostile())
        self.assertEqual(hooks, [])


class CurrentLifecycleProjectionTests(unittest.TestCase):
    def test_current_source_containment_resolution_halt_uses_current_graph(self):
        for baseline in ('M3_MODULES', 'M3_GENERATION'):
            with self.subTest(baseline=baseline):
                source = sv.CanonicalAshBinding(**dict(dict(sv.CANONICAL_BINDING_BASELINES)[baseline]))
                policy = v.SessionPolicyBinding(**dict(v.MODULE_SESSION_POLICY_BINDING_FIELDS))
                with mock.patch.object(lifecycle, 'current_source', return_value=source), mock.patch.object(lifecycle, 'current_policy', return_value=policy):
                    values = lifecycle.assembly()
                session, diagnostics, opened = values[2], values[4], values[-1]
                self.assertEqual(opened.status, 'CONFIRMED')
                for command in (lifecycle.contain_command, lifecycle.resolve_command, lifecycle.halt_command):
                    actual = session.execute(command(session))
                    self.assertEqual(actual.status, 'COMPLETED')
                    self.assertEqual(actual.completion_observation.status, 'COMPLETE')
                snapshot = diagnostics.snapshot(bundle_reference='current:session:graph')
                evidence = snapshot.supporting_evidence
                self.assertEqual(evidence.session_bindings, ())
                self.assertTrue(evidence.session_current_bindings)
                self.assertTrue(all(type(node) is safe.SafeCurrentSessionBindingEvidence for node in evidence.session_current_bindings))
                self.assertEqual(len(evidence.session_current_histories), 1)
                self.assertTrue(evidence.session_current_history_pages)
                self.assertEqual(evidence.session_histories, ())
                self.assertEqual(values[0].read_session_history(session).terminal_snapshot.mode, 'SAFE_HALT')


def module_assembly(baseline='M3_GENERATION', **kwargs):
    from core.ash_pattern_engine.session import ReferenceSessionLifecycle
    from core.ash_pattern_engine.realm_transition import RealmEncoder, TransitionRegistry
    from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
    from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
    from core.ash_pattern_engine import realm_transition_values as rt, generation_values as gen
    source = sv.CanonicalAshBinding(**dict(dict(sv.CANONICAL_BINDING_BASELINES)[baseline]))
    policy = v.SessionPolicyBinding(**dict(v.MODULE_SESSION_POLICY_BINDING_FIELDS))
    def owner(model, collector, bound):
        pins = rt.GENERATION_SOURCE_PINS if baseline == 'M3_GENERATION' else rt.SOURCE_PINS
        binding = rt.RealmTransitionBinding(source, model.profile_binding,
            tuple(rt.RealmTransitionSourcePin(*pair) for pair in pins), *rt.POLICY_IDENTITIES[0], 'module:policy')
        definitions = tuple(rt.TransitionDefinition(f'ash_codeword_{index:02d}', f'ASH codeword {index:02d}',
            'Apply the complete canonical nine-coordinate XOR codeword.', sv.AshState(bits), '1'*512)
            for index, bits in enumerate(sv.CANONICAL_CODEWORDS))
        owners = (RealmEncoder(model, binding), TransitionRegistry(model, rt.TransitionCatalog(binding, definitions)),
            ReferenceTopologyGenerator(model, gen.TopologyAxiomPolicyBinding(*gen.POLICY_FIELDS)),
            ReferenceAxiomEvaluator(model, gen.TopologyAxiomPolicyBinding(*gen.POLICY_FIELDS)))
        return ReferenceSessionLifecycle(model, collector, bound, module_owners=owners)
    with mock.patch.object(lifecycle, 'current_source', return_value=source), mock.patch.object(lifecycle, 'current_policy', return_value=policy), mock.patch.object(lifecycle, 'ReferenceSessionLifecycle', side_effect=owner):
        return lifecycle.assembly(**kwargs)


def module_command(session, producer='REALM_ENCODER', operation='ENCODE_REALM', reference='session:encode', arguments=None):
    if arguments is None:
        arguments = v.RealmEncodingArguments()
    before = session.read()
    prefix = reference + ':module:origin'
    return v.SessionModuleCommand(reference, before.binding.session_reference, before, producer, operation,
        'CAPTURE_CURRENT_DIAGNOSIS', sv.DiagnosticContext(prefix+':assessment', prefix+':input', prefix+':detection', prefix+':classification'),
        arguments, ())


class CurrentModuleIntegrationTests(unittest.TestCase):
    def test_session_cookie_and_gate_collector_rebinding_cannot_transfer_original_issuance(self):
        first, second = module_assembly(), module_assembly()
        owner, session, collector = first[1], first[2], first[4]
        command = module_command(session)
        before = session.read()
        active = owner._new_snapshot(active_operation_reference=command.request_reference)
        lease = v.SessionModuleLease(command.request_reference+':lease', command, before, active, 'MODULE', before.generation)
        gate = owner._gate(lease)
        metadata = (gate._collector, gate._cookie.collector)
        before_calls = len(first[5].calls), len(second[5].calls)
        self.assertTrue(v.SessionExecutionGate.validate_module_capture(gate, collector, command.request_reference, command.producer))
        try:
            object.__setattr__(gate, '_collector', second[4])
            object.__setattr__(gate._cookie, 'collector', second[4])
            self.assertFalse(v.SessionExecutionGate.validate_module_capture(gate, second[4], command.request_reference, command.producer))
            self.assertEqual(gate.capture_disposition(), 'UNAVAILABLE')
        finally:
            object.__setattr__(gate, '_collector', metadata[0])
            object.__setattr__(gate._cookie, 'collector', metadata[1])
        self.assertTrue(v.SessionExecutionGate.validate_module_capture(gate, collector, command.request_reference, command.producer))
        self.assertEqual((len(first[5].calls), len(second[5].calls)), before_calls)

    def test_halt_after_actual_module_append_ack_preserves_prefix_and_once_late_cleanup(self):
        from core.ash_pattern_engine.diagnostic_module_capture import ModuleCaptureScope
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        original = ModuleCaptureScope.append
        receipts = []
        def halted_after_ack(scope, record):
            response = original(scope, record)
            receipts.append(response)
            self.assertEqual(response.status, 'CONFIRMED')
            session.execute(lifecycle.halt_command(session))
            return response
        with mock.patch.object(ModuleCaptureScope, 'append', side_effect=halted_after_ack), mock.patch.object(ModuleCaptureScope, 'finish', wraps=ModuleCaptureScope.finish) as finish:
            actual = engine.execute_session_module(session, module_command(session))
        self.assertEqual(finish.call_count, 1)
        self.assertEqual(actual.result.failure_code, 'SESSION_EXECUTION_CANCELLED')
        self.assertEqual(actual.result.module_capture.confirmed_records, (receipts[0].diagnostic_reference,))
        self.assertEqual(len(actual.result.module_capture.completion.confirmed_event_indices), 1)
        self.assertEqual(actual.result.module_capture.completion.status, 'INCOMPLETE')
        journal = engine.read_session_module_history(session)
        self.assertEqual((journal.frozen, journal.pending_cutover.phase), (True, 'CAPTURING'))
        snapshot = diagnostics.snapshot(bundle_reference='after-ack:cutover')
        self.assertEqual((len(snapshot.supporting_evidence.session_module_links), len(snapshot.supporting_evidence.session_module_cutovers)), (1, 1))
        selected = {record['diagnostic_reference'] for page in snapshot.supporting_evidence.session_current_history_pages for record in page.to_record()['record_references']}
        event = next(event for event in snapshot.events if event.diagnostic_reference == diagnostics._alias(receipts[0].diagnostic_reference))
        self.assertIn(event.diagnostic_reference, selected)

    def test_foreign_same_collector_scope_is_untouched_and_original_wrong_receipt_cleans_once(self):
        from core.ash_pattern_engine import diagnostic_module_values as module
        from core.ash_pattern_engine.diagnostic_module_capture import ModuleCaptureScope
        from core.ash_pattern_engine.diagnostics import ReferenceDevelopmentDiagnostics
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        encoder = owner._module_owners['REALM_ENCODER']
        context = sv.DiagnosticContext('foreign:origin', 'foreign:input', 'foreign:detection', 'foreign:classification')
        origin = model.diagnose(session.read().current_state, diagnostic_context=context)
        self.assertEqual(diagnostics.complete_assessment(origin).status, 'COMPLETE')
        result = type(encoder).encode(encoder, origin, operation_reference='foreign:operation')
        foreign_context = module.ModuleCaptureContext('foreign:operation', 'REALM_ENCODER', type(encoder).configuration(encoder), origin, result, ())
        foreign = diagnostics.module_capture(encoder, foreign_context).scope
        with mock.patch.object(ReferenceDevelopmentDiagnostics, 'module_capture', return_value=module.ModuleCaptureAdmission('session:encode', 'ADMITTED', foreign, None)):
            refused = engine.execute_session_module(session, module_command(session))
        self.assertEqual(refused.result.failure_code, 'SESSION_CAPTURE_FAILED')
        self.assertFalse(foreign._native.finished)
        self.assertIsNone(foreign._native.failed)
        self.assertIsNone(foreign._native.completion_response)
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        begin = ReferenceDevelopmentDiagnostics.module_capture
        issued = []
        def wrong_receipt(collector, producer, context, **kwargs):
            actual = begin(collector, producer, context, **kwargs)
            issued.append(actual.scope)
            return module.ModuleCaptureAdmission('wrong:receipt', 'NOT_CONFIRMED', actual.scope, 'MODULE_CAPTURE_UNCONFIRMED')
        with mock.patch.object(ReferenceDevelopmentDiagnostics, 'module_capture', side_effect=wrong_receipt), mock.patch.object(ModuleCaptureScope, 'finish', wraps=ModuleCaptureScope.finish) as finish:
            refused = engine.execute_session_module(session, module_command(session))
        self.assertEqual(finish.call_count, 1)
        self.assertTrue(issued[0]._native.finished)
        self.assertEqual(refused.result.module_capture.completion.status, 'INCOMPLETE')

    def test_held_module_token_cannot_block_mandatory_halt_or_reactivate_after_release(self):
        from core.ash_pattern_engine.realm_transition import RealmEncoder
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        entered, release = threading.Event(), threading.Event()
        original = RealmEncoder.encode
        values, errors = [], []
        def blocked(producer, origin, *, operation_reference):
            entered.set()
            if not release.wait(5):
                raise AssertionError('release missing')
            return original(producer, origin, operation_reference=operation_reference)
        def execute():
            try:
                values.append(engine.execute_session_module(session, module_command(session)))
            except BaseException as error:
                errors.append(error)
        with mock.patch.object(RealmEncoder, 'encode', side_effect=blocked):
            thread = threading.Thread(target=execute); thread.start()
            try:
                self.assertTrue(entered.wait(5))
                gate = owner._active.gate
                gate._capture_lock.acquire()
                try:
                    self.assertEqual(gate.capture_disposition(), 'UNAVAILABLE')
                    halted = session.execute(lifecycle.halt_command(session))
                    self.assertTrue(session.read().terminal_latched)
                finally:
                    gate._capture_lock.release()
                self.assertEqual(gate.capture_disposition(), 'SEALED')
            finally:
                release.set(); thread.join(5)
        self.assertEqual(errors, [])
        self.assertFalse(thread.is_alive())
        self.assertEqual(values[0].result.failure_code, 'SESSION_EXECUTION_CANCELLED')

    def validate_wire(self, actual):
        documents = [json.loads(path.read_text()) for path in (ROOT/'data/schemas').glob('*.json')]
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in documents if '$id' in schema and '$schema' in schema)
        selected = next(schema for schema in documents if schema.get('$id') == 'https://ywe.local/schemas/m3_current_source_session_schema.json')
        Draft202012Validator({'$ref': selected['$id']+'#/$defs/'+type(actual).__name__}, registry=registry).validate(actual.to_record())

    def test_four_owned_producers_keep_session_state_and_complete_actual_journal(self):
        from core.ash_pattern_engine import generation_values as gen
        for baseline in ('M3_MODULES', 'M3_GENERATION'):
            with self.subTest(baseline=baseline):
                engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly(baseline)
                commands = [module_command(session)]
                actual = engine.execute_session_module(session, commands[0])
                self.validate_wire(actual)
                for producer, operation, args, reference in (
                    ('TRANSITION_REGISTRY', 'RESOLVE_TRANSITIONS', v.TransitionResolutionArguments(), 'session:resolve-module'),
                    ('TOPOLOGY_GENERATOR', 'GENERATE_TOPOLOGY', v.TopologyArguments('seed', 1), 'session:topology'),
                    ('AXIOM_EVALUATOR', 'EVALUATE_AXIOMS', None, 'session:axioms')):
                    if args is None:
                        args = v.AxiomArguments(gen.AxiomSubject('declared:subject', session.read().current_state, 0,
                            gen.AxiomMeasure(1, 'STRUCTURE_TICK', 100), gen.AxiomMeasure(0, 'STRUCTURE_TICK', 100),
                            2, gen.AxiomMeasure(1, 'ERASURE_TICK', 10), True, True,
                            gen.AxiomSubjectProvenance('DECLARED_REFERENCE_INPUT', 'declared:source', 'test-method', '1', reference+':module:origin:detection')))
                    actual = engine.execute_session_module(session, module_command(session, producer, operation, reference, args))
                    self.assertEqual((actual.result.status, actual.result.failure_code), ('COMPLETED', None))
                    self.assertEqual(actual.control_observation.status, 'CONFIRMED')
                    self.validate_wire(actual)
                self.assertEqual((session.read().generation, session.read().current_state, session.read().admission_status), (0, initial.parsed_state, 'OPEN'))
                self.assertEqual(len(engine.read_session_module_history(session).results), 4)

    def test_actual_explicit_fresh_origin_module_capture_replay_and_halt(self):
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        submitted = module_command(session)
        actual = engine.execute_session_module(session, submitted)
        self.assertEqual((actual.result.status, actual.result.failure_code), ('COMPLETED', None))
        self.assertEqual((actual.result.origin_completion.status, actual.result.module_capture.completion.status,
            actual.control_observation.status), ('COMPLETE', 'COMPLETE', 'CONFIRMED'))
        self.assertEqual(actual.result.origin_diagnosis.parsed_state, initial.parsed_state)
        self.assertIs(owner._accepted, initial)
        self.assertEqual((session.read().generation, session.read().current_state), (0, initial.parsed_state))
        count = len(store.calls)
        replay = engine.execute_session_module(session, submitted)
        self.assertIs(replay.original_result, actual)
        self.assertEqual(len(store.calls), count)
        halted = session.execute(lifecycle.halt_command(session))
        self.assertEqual((halted.status, halted.completion_observation.status), ('COMPLETED', 'COMPLETE'))
        history = engine.read_session_module_history(session)
        self.assertEqual((history.frozen, len(history.results)), (True, 1))
        evidence = diagnostics.snapshot(bundle_reference='session:module:graph').supporting_evidence
        self.assertEqual((len(evidence.session_module_links), len(evidence.session_module_histories)), (1, 1))

    def test_stale_same_state_cycle_refuses_before_new_diagnosis_or_pure_work(self):
        from core.ash_pattern_engine.realm_transition import RealmEncoder
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        submitted = module_command(session)
        for command in (lifecycle.contain_command, lifecycle.resolve_command):
            actual = session.execute(command(session))
            self.assertEqual(actual.status, 'COMPLETED')
        count = len(store.calls)
        with mock.patch.object(RealmEncoder, 'encode', wraps=RealmEncoder.encode) as encode:
            actual = engine.execute_session_module(session, submitted)
        self.assertEqual((actual.result.status, actual.result.failure_code), ('REFUSED', 'SESSION_STATE_STALE'))
        self.assertEqual(encode.call_count, 0)
        self.assertEqual(len(store.calls), count)
        self.assertEqual((session.read().current_state, session.read().generation), (initial.parsed_state, 2))

    def test_uncertain_fresh_origin_finishes_actual_scope_and_prevents_computation(self):
        from core.ash_pattern_engine.realm_transition import RealmEncoder
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        def uncertain(sequence, raw):
            from core.ash_pattern_engine import diagnostics_values as dv
            return dv.StorageReceipt(sequence, 'UNKNOWN', 'STORAGE_COMMIT_UNCONFIRMED')
        with mock.patch.object(store, 'commit_event', side_effect=uncertain), mock.patch.object(RealmEncoder, 'encode', wraps=RealmEncoder.encode) as encode:
            actual = engine.execute_session_module(session, module_command(session))
        self.assertEqual(encode.call_count, 0)
        self.assertEqual((actual.result.status, actual.result.failure_code, actual.result.origin_completion.status),
            ('FAILED', 'SESSION_ORIGIN_REJECTED', 'INCOMPLETE'))
        self.assertEqual(session.read().admission_status, 'AUDIT_BLOCKED')
        self.assertIsNotNone(actual.result.origin_diagnosis)

    def test_concurrent_halt_seals_granted_pure_work_and_keeps_late_link_outside_frozen_journal(self):
        from core.ash_pattern_engine.realm_transition import RealmEncoder
        engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly()
        entered, release = threading.Event(), threading.Event()
        original = RealmEncoder.encode
        values, errors = [], []
        def blocked(producer, origin, *, operation_reference):
            entered.set()
            if not release.wait(5):
                raise AssertionError('the controlled halt did not release computation')
            return original(producer, origin, operation_reference=operation_reference)
        def execute():
            try:
                values.append(engine.execute_session_module(session, module_command(session)))
            except BaseException as error:
                errors.append(error)
        with mock.patch.object(RealmEncoder, 'encode', side_effect=blocked):
            thread = threading.Thread(target=execute)
            thread.start()
            try:
                self.assertTrue(entered.wait(5))
                halted = session.execute(lifecycle.halt_command(session))
                self.assertTrue(session.read().terminal_latched)
                journal = engine.read_session_module_history(session)
                frozen = journal.to_record()
                count = len(diagnostics.snapshot(bundle_reference='cutover:before').events)
            finally:
                release.set(); thread.join(5)
        self.assertEqual(errors, [])
        self.assertFalse(thread.is_alive())
        actual = values[0]
        self.assertEqual((actual.result.status, actual.result.failure_code), ('UNCONFIRMED', 'SESSION_EXECUTION_CANCELLED'))
        self.assertIsNotNone(actual.result.actual_pure_result)
        self.assertIsNone(actual.result.module_capture)
        self.assertEqual(engine.read_session_module_history(session).to_record(), frozen)
        self.assertEqual(len(diagnostics.snapshot(bundle_reference='cutover:after').events), count)
        self.assertEqual((journal.pending_cutover.phase, journal.frozen), ('COMPUTING', True))
        self.assertEqual(len(diagnostics.snapshot(bundle_reference='cutover:links').supporting_evidence.session_module_links), 1)

    def test_current_source_recovery_no_action_and_terminal_hostile_precedence(self):
        for baseline in ('M3_MODULES', 'M3_GENERATION'):
            engine, owner, session, model, diagnostics, store, clock, initial, binding, opened = module_assembly(baseline)
            actual = session.execute(lifecycle.recover_command(session, initial))
            self.assertEqual((actual.status, actual.recovery_result.completion_observation.status), ('COMPLETED', 'COMPLETE'))
            session.execute(lifecycle.halt_command(session))
            class Hostile:
                def __getattribute__(self, key):
                    raise AssertionError('terminal module request body was inspected')
            denied = engine.execute_session_module(session, Hostile())
            self.assertEqual(denied.reason_code, 'SESSION_TERMINAL')

    @unittest.skipUnless(os.name == 'nt', 'Actual adopted protected storage and paired-file verification are Windows-specific')
    def test_actual_windows_current_module_journal_and_terminal_index_export(self):
        from scripts.reference_diagnostics_host import assemble_reference_diagnostics
        diagnostics = assemble_reference_diagnostics(ROOT)
        self.addCleanup(diagnostics.store.close)
        with mock.patch.object(lifecycle, 'ReferenceDevelopmentDiagnostics', return_value=diagnostics):
            engine, owner, session, model, actual_collector, _, _, initial, binding, opened = module_assembly()
        self.assertIs(actual_collector, diagnostics)
        actual = engine.execute_session_module(session, module_command(session))
        self.assertEqual((actual.result.status, actual.control_observation.status), ('COMPLETED', 'CONFIRMED'))
        for command in (lifecycle.contain_command, lifecycle.resolve_command, lifecycle.halt_command):
            self.assertEqual(session.execute(command(session)).status, 'COMPLETED')
        snapshot = diagnostics.snapshot(bundle_reference='native:current:journal')
        self.assertEqual((len(snapshot.supporting_evidence.session_module_links), len(snapshot.supporting_evidence.session_module_histories)), (1, 1))
        diagnostics.export_pair(snapshot)
        raw = (diagnostics.store.root/'diagnostics.json').read_bytes()
        markdown = (diagnostics.store.root/'diagnostics.md').read_bytes()
        manifest = json.loads((diagnostics.store.root/'manifest.json').read_bytes())
        self.assertEqual(snapshot.to_record(), json.loads(raw))
        self.assertEqual(json.loads(raw), json.loads(markdown.split(b'```json\n', 1)[1].rsplit(b'\n```', 1)[0]))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['json_sha256'])
        self.assertEqual(hashlib.sha256(markdown).hexdigest(), manifest['markdown_sha256'])
        Draft202012Validator(json.loads((ROOT/'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text())).validate(json.loads(raw))


if __name__ == '__main__':
    unittest.main()
