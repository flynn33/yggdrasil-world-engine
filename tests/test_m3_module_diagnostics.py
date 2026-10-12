"""Actual module capture under declared portable ports; native tests are explicit."""
from copy import copy, deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.ash_pattern_engine import diagnostics as d, diagnostics_values as dv
from core.ash_pattern_engine import diagnostic_module_values as m, diagnostic_module_capture as capture
from core.ash_pattern_engine import generation_values as g, realm_transition_values as rt, state_values as s
from core.ash_pattern_engine.realm_transition import RealmEncoder, TransitionRegistry
from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
from core.ash_pattern_engine.state_model import StateModel
from tests.test_m3_reference_diagnostics import ControlledClock, ControlledProjectionStore
from tests import test_m3_reference_diagnostics as reference_tests
from tests.test_m3_realm_transition_values import assembly as pure_assembly, diagnosis
from tests.test_m3_axioms import subject

ROOT = Path(__file__).resolve().parents[1]


class ModuleStore(ControlledProjectionStore):
    def __init__(self):
        super().__init__()
        self.unknown_kind = self.unknown_sequence = None
        self.block_kind = None
        self.entered, self.release = threading.Event(), threading.Event()
        self.callback = None
        self.published = None

    def commit_supporting(self, sequence, kind, alias, raw):
        self.calls.append(('commit_supporting', (sequence, kind, alias, raw)))
        if self.callback is not None:
            callback, self.callback = self.callback, None
            callback()
        if kind == self.block_kind:
            self.entered.set()
            if not self.release.wait(5):
                raise AssertionError('controlled thread did not release')
        return dv.StorageReceipt(sequence, 'UNKNOWN' if kind == self.unknown_kind else 'COMMITTED',
                                 'STORAGE_COMMIT_UNCONFIRMED' if kind == self.unknown_kind else None)

    def commit_event(self, sequence, raw):
        self.calls.append(('commit_event', (sequence, raw)))
        return dv.StorageReceipt(sequence, 'UNKNOWN' if sequence == self.unknown_sequence else 'COMMITTED',
                                 'STORAGE_COMMIT_UNCONFIRMED' if sequence == self.unknown_sequence else None)

    def write_pair(self, alias, raw, markdown, manifest, *, last_included_sequence):
        self.published = raw, markdown, manifest
        parts = tuple(dv.PartReceipt(kind, name, 'WRITTEN', len(data), hashlib.sha256(data).hexdigest(), None)
            for kind, name, data in (('JSON', 'diagnostics.json', raw), ('MARKDOWN', 'diagnostics.md', markdown), ('MANIFEST', 'manifest.json', manifest)))
        return dv.StorePairReceipt(alias, parts, last_included_sequence)


def assembly(*, store=None, release=False):
    seed, encoder, registry = pure_assembly()
    identity = reference_tests.CanonicalSourceCompatibilityTests().identity()
    if release:
        identity = replace(identity, implementation_id='REFERENCE_RELEASE_DIAGNOSTICS', profile_id='REFERENCE_RELEASE')
    profile = dv.DiagnosticsProfile(identity.profile_id, identity.implementation_id, 'ref:000003', not release)
    store, clock = ModuleStore() if store is None else store, ControlledClock()
    cls = d.ReferenceReleaseDiagnostics if release else d.ReferenceDevelopmentDiagnostics
    diagnostics = cls(identity, profile, store, clock, canonical_source_snapshots=(dv.SourcePin('ASH_AGGREGATE',
        identity.source_revision, dict(s.MODULE_CANONICAL_BINDING_FIELDS)['aggregate_sha256']),))
    model = StateModel(seed.profile_binding, seed.canonical_binding, diagnostics.assessment_capture())
    binding = encoder.configuration()
    definitions = tuple(rt.TransitionDefinition(f'ash_codeword_{i:02d}', f'ASH codeword {i:02d}',
        'Apply the complete canonical nine-coordinate XOR codeword.', s.AshState(bits), '1'*512)
        for i, bits in enumerate(s.CANONICAL_CODEWORDS))
    owners = (RealmEncoder(model, binding), TransitionRegistry(model, rt.TransitionCatalog(binding, definitions)),
              ReferenceTopologyGenerator(model, g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)),
              ReferenceAxiomEvaluator(model, g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)))
    origin = diagnosis(model)
    completion = diagnostics.complete_assessment(origin)
    assert completion.status == 'COMPLETE'
    return diagnostics, model, owners, origin, store, clock


def result_for(owner, origin, reference, *, depth=6):
    if type(owner) is RealmEncoder:
        return owner.encode(origin, operation_reference=reference)
    if type(owner) is TransitionRegistry:
        return owner.resolve(origin, operation_reference=reference)
    if type(owner) is ReferenceTopologyGenerator:
        return owner.generate(g.TopologyRequest(reference, origin, depth, 'caller-seed-token'))
    return owner.evaluate(g.AxiomRequest(reference, origin, subject(origin, (False, True, True, True, True))))


def start(diagnostics, owner, result):
    kind, _, _ = capture._configuration(owner)
    reference, origin, _ = capture._facts(result)
    context = m.ModuleCaptureContext(reference, kind, type(owner).configuration(owner), origin, result, ())
    return diagnostics.module_capture(owner, context)


def execute(diagnostics, owner, result):
    admission = start(diagnostics, owner, result)
    confirmed, attempted, completion, final = [], None, None, None
    if admission.scope is not None:
        if admission.status == 'ADMITTED':
            for record in capture._facts(result)[2]:
                observed = admission.scope.append(record)
                if observed.status != 'CONFIRMED':
                    attempted = record
                    break
                confirmed.append(capture._emission(record).diagnostic_reference)
        completion = admission.scope.finish(result)
        final = admission.scope.observe_final(result, completion)
        diagnostics.audit_module_return(admission.scope, boundary='RETURN')
    status = 'CONFIRMED' if final is not None and final.status == 'CONFIRMED' and final.coverage == 'COMPLETE_SPECIFIED_SAFE_GRAPH' else 'NOT_CONFIRMED'
    return m.ModuleCaptureReceipt(capture._facts(result)[0], status, result, tuple(confirmed), attempted,
        completion, final, None if status == 'CONFIRMED' else admission.failure_code or 'MODULE_CAPTURE_UNCONFIRMED'), admission


def runtime_capture_controls():
    """Five public wire types and an actual failed captured prefix, under declared ports."""
    diagnostics, model, owners, origin, store, clock = assembly()
    registration = diagnostics.register_module_producer(owners[0])
    result = result_for(owners[0], origin, 'module:fixture:complete')
    context = m.ModuleCaptureContext(result.operation_reference, 'REALM_ENCODER', owners[0].configuration(), origin, result, ())
    receipt, admission = execute(diagnostics, owners[0], result)
    audit = diagnostics.audit_module_return(admission.scope, boundary='RETURN')
    cases = [{'case_id': 'actual-' + type(value).__name__, 'type_name': type(value).__name__, 'value': value.to_record()}
             for value in (registration, context, receipt, receipt.final_observation, audit)]
    diagnostics, model, owners, origin, store, clock = assembly()
    diagnostics.register_module_producer(owners[0]); store.unknown_sequence = 2
    failure, _ = execute(diagnostics, owners[0], result_for(owners[0], origin, 'module:fixture:prefix'))
    cases.append({'case_id': 'actual-unknown-event-prefix', 'type_name': 'ModuleCaptureReceipt', 'value': failure.to_record()})
    return dict(artifact_type='ywe_module_capture_runtime_controls', artifact_version='1.0.0', requirement_id='YWE-REQ-0048',
        provenance=dict(execution='tests.test_m3_module_diagnostics.runtime_capture_controls',
            clock='ControlledClock deterministic port; no actual native time observation.',
            storage='ModuleStore declared COMMITTED and selected UNKNOWN port responses; actual collector execution.',
            source_identity='Declared synthetic aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa containing revision with exact M3_MODULES vector; no host source verification.',
            evidence_scope='Portable reference semantic production and actual collector capture/first-finish/final-observer execution. Format fixtures do not qualify native protection, crash or power-loss behavior.'), cases=cases)


class ModuleCaptureTests(unittest.TestCase):
    def test_effectful_whole_future_raw_refusal_precedes_scope_claim_and_target_call(self):
        from tests.test_m3_artifact_emitter import ready
        from core.ash_pattern_engine.memory_document_target import MemoryDocumentTarget
        runtime, run = ready()
        runner, _, _, _, _, target, ports = runtime
        collector = ports[2]
        before = dict(collector._aliases)
        with patch.object(capture, '_anticipated_emitter_raw_size', return_value=2097153), patch.object(MemoryDocumentTarget, 'materialize', wraps=MemoryDocumentTarget.materialize) as action:
            actual = runner.emit(run.last_observation, target, operation_reference='raw:refusal')
        self.assertEqual(action.call_count, 0)
        self.assertEqual(target.snapshot().revision, 0)
        self.assertEqual(collector._aliases, before)
        self.assertIsNone(actual.completion)
        self.assertEqual(actual.result.actual_effects, False)

    def test_source4_first_response_readback_checks_body_before_io_and_preserves_old_replay(self):
        from tests.test_m3_core_orchestration import current_assembly
        _, model, collector, store, clock = current_assembly()
        origin = diagnosis(model, candidate='000000000', reference='readback:origin')
        response = collector.complete_assessment(origin)
        before = len(store.calls), clock.value, dict(collector._aliases)
        self.assertIs(collector.complete_assessment(copy(origin)), response)
        self.assertEqual((len(store.calls), clock.value, dict(collector._aliases)), before)
        changed = copy(origin)
        object.__setattr__(changed, 'emitted_diagnostics', (replace(origin.emitted_diagnostics[0],
            envelope=replace(origin.emitted_diagnostics[0].envelope, summary='A different legal diagnostic body.')),))
        with self.assertRaises(dv.DiagnosticsContractError):
            collector.complete_assessment(changed)
        self.assertEqual((len(store.calls), clock.value, dict(collector._aliases)), before)
        old_collector, old_model, owners, old_origin, old_store, old_clock = assembly()
        rejected = old_collector.complete_assessment(old_origin)
        self.assertEqual((rejected.status, rejected.failure_code), ('INCOMPLETE', 'DIAGNOSTICS_REPLAY_REFUSED'))

    def test_original_scope_context_authentication_refuses_foreign_copy_and_hostile_reflection(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        owner = owners[0]
        self.assertEqual(diagnostics.register_module_producer(owner).status, 'REGISTERED')
        result = result_for(owner, origin, 'scope:original')
        context = m.ModuleCaptureContext('scope:original', 'REALM_ENCODER', type(owner).configuration(owner), origin, result, ())
        admitted = diagnostics.module_capture(owner, context)
        scope = admitted.scope
        method = capture.ModuleCaptureScope.validate_issued_for_context
        self.assertTrue(method(scope, diagnostics, owner, context))
        before = len(store.calls), clock.value, dict(diagnostics._aliases)
        for inputs in ((copy(scope), diagnostics, owner, context), (scope, copy(diagnostics), owner, context),
                       (scope, diagnostics, copy(owner), context), (scope, diagnostics, owner, copy(context))):
            self.assertFalse(method(*inputs))
        duplicate = copy(context)
        scope._context = duplicate
        try:
            self.assertFalse(method(scope, diagnostics, owner, duplicate))
            self.assertFalse(method(scope, diagnostics, owner, context))
        finally:
            scope._context = context
        self.assertTrue(method(scope, diagnostics, owner, context))
        hooks = []
        class Hostile:
            def __eq__(self, other):
                hooks.append('eq'); raise AssertionError('unowned equality')
            def __getitem__(self, key):
                hooks.append('getitem'); raise AssertionError('unowned indexing')
            def get(self, key):
                hooks.append('get'); raise AssertionError('unowned mapping')
        class HostileKey:
            def __hash__(self):
                return hash('REALM_ENCODER')
            def __eq__(self, other):
                hooks.append('key-eq'); raise AssertionError('unowned mapping key equality')
        digest, registered = scope._context_hash, scope._service.registered
        try:
            scope._context_hash = Hostile()
            self.assertFalse(method(scope, diagnostics, owner, context))
            scope._context_hash = digest
            scope._service.registered = Hostile()
            self.assertFalse(method(scope, diagnostics, owner, context))
            scope._service.registered = {HostileKey(): registered['REALM_ENCODER']}
            self.assertFalse(method(scope, diagnostics, owner, context))
        finally:
            scope._context_hash, scope._service.registered = digest, registered
        self.assertEqual(hooks, [])
        self.assertEqual((len(store.calls), clock.value, dict(diagnostics._aliases)), before)
        for record in result.constructed_records:
            self.assertEqual(scope.append(record).status, 'CONFIRMED')
        response = scope.finish(result)
        self.assertTrue(method(scope, diagnostics, owner, context))
        self.assertIs(scope.finish(result), response)

    @unittest.skipUnless(os.name == 'nt', 'Actual adopted protected storage and paired-file verification are Windows-specific')
    def test_actual_windows_protected_four_producer_max_graph_and_paired_files(self):
        from scripts.reference_diagnostics_host import assemble_reference_diagnostics
        diagnostics = assemble_reference_diagnostics(ROOT)
        self.addCleanup(diagnostics.store.close)
        seed, encoder, registry = pure_assembly()
        model = StateModel(seed.profile_binding, seed.canonical_binding, diagnostics.assessment_capture())
        definitions = tuple(rt.TransitionDefinition(f'ash_codeword_{i:02d}', f'ASH codeword {i:02d}',
            'Apply the complete canonical nine-coordinate XOR codeword.', s.AshState(bits), '1'*512)
            for i,bits in enumerate(s.CANONICAL_CODEWORDS))
        owners = (RealmEncoder(model, encoder.configuration()), TransitionRegistry(model, rt.TransitionCatalog(encoder.configuration(), definitions)),
            ReferenceTopologyGenerator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)), ReferenceAxiomEvaluator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS)))
        origin = diagnosis(model, reference='native:module:origin')
        self.assertEqual('COMPLETE', diagnostics.complete_assessment(origin).status)
        for index, owner in enumerate(owners):
            self.assertEqual('REGISTERED', diagnostics.register_module_producer(owner).status)
            receipt, _ = execute(diagnostics,owner,result_for(owner,origin,'native:module:'+str(index)))
            self.assertEqual('CONFIRMED',receipt.status)
            self.assertEqual('COMPLETE',receipt.completion.status)
            self.assertEqual((2,17,1,5)[index],len(receipt.confirmed_records))
        snapshot = diagnostics.snapshot(bundle_reference='native:module:bundle')
        self.assertEqual(46,sum(row.kind=='TOPOLOGY_PAGE' for row in snapshot.supporting_evidence.module_evidence))
        pages = [row.payload.to_record() for row in snapshot.supporting_evidence.module_evidence if row.kind=='TOPOLOGY_PAGE']
        self.assertEqual(729,sum(len(page['nodes']) for page in pages))
        checks = [row.payload.to_record() for row in snapshot.supporting_evidence.module_evidence if row.kind=='AXIOM_CHECK']
        self.assertEqual(5,len(checks));self.assertTrue(checks[-1]['passed']);self.assertFalse(checks[-1]['overall_pass'])
        wrappers = snapshot.supporting_evidence.module_evidence
        self.assertEqual(len(wrappers),len({row.evidence_reference for row in wrappers}))
        self.assertEqual(4,len(diagnostics._canonical_source_snapshots))
        self.assertEqual(tuple(dict(fields)['aggregate_sha256'] for _, fields in s.CANONICAL_BINDING_BASELINES),
            tuple(pin.sha256 for pin in diagnostics._canonical_source_snapshots))
        self.assertEqual(dv.HISTORICAL_MODULE_SOURCE_REVISION, diagnostics._canonical_source_snapshots[2].revision)
        self.assertIn(diagnostics.identity.source_provenance.status,('VERIFIED_CLEAN','VERIFIED_DIRTY'))
        exported = diagnostics.export_pair(snapshot)
        self.assertIs(type(exported),dv.ExportReceipt)
        raw=(diagnostics.store.root/'diagnostics.json').read_bytes()
        markdown=(diagnostics.store.root/'diagnostics.md').read_bytes()
        manifest=json.loads((diagnostics.store.root/'manifest.json').read_bytes())
        self.assertEqual(snapshot.to_record(),json.loads(raw))
        self.assertEqual(json.loads(raw),json.loads(markdown.split(b'```json\n',1)[1].rsplit(b'\n```',1)[0]))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),manifest['json_sha256'])
        self.assertEqual(hashlib.sha256(markdown).hexdigest(),manifest['markdown_sha256'])
        self.assertEqual('EXACT_EMBEDDED_SNAPSHOT',manifest['parity'])
        Draft202012Validator(json.loads((ROOT/'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text())).validate(json.loads(raw))

    @unittest.skipUnless(os.name == 'nt', 'Actual adopted protected storage and paired-file verification are Windows-specific')
    def test_actual_windows_protected_depth5_emitter_complete_receipt_leaf_graph(self):
        from scripts.reference_diagnostics_host import assemble_reference_diagnostics
        from tests import test_m3_generation_runner as runner_tests
        from tests.test_m3_core_orchestration import H4
        from tests.test_m3_core_values import core_binding
        from tests.test_m3_realm_transition_values import profile_from
        diagnostics = assemble_reference_diagnostics(ROOT)
        self.addCleanup(diagnostics.store.close)
        profile = profile_from(H4, 'native:core:h4')
        core = core_binding(profile=profile)
        model = StateModel(profile, core.canonical_binding, diagnostics.assessment_capture())
        def actual_assembly(**kwargs):
            return core, model, diagnostics, diagnostics.store, diagnostics.clock
        with patch.object(runner_tests, 'current_assembly', side_effect=actual_assembly):
            runner, inputs, origin, facts, constraints, target, ports = runner_tests.runtime_assembly(depth=5)
        run = runner.run(inputs, origin, facts, constraints, operation_reference='native:full:run')
        self.assertEqual(run.status, 'READY')
        actual = runner.emit(run.last_observation, target, operation_reference='native:full:emit')
        self.assertEqual((actual.status, actual.completion.status, actual.final_observation.status), ('CONFIRMED', 'COMPLETE', 'CONFIRMED'))
        self.assertEqual((len(actual.result.outcomes), len(actual.confirmed_records), target.snapshot().revision), (8, 17, 8))
        snapshot = diagnostics.snapshot(bundle_reference='native:full:bundle')
        wrappers = {node.evidence_reference: node for node in snapshot.supporting_evidence.module_evidence}
        operations = [node.payload.to_record() for node in wrappers.values() if node.kind == 'PRODUCER_OPERATION' and node.payload.producer == 'ARTIFACT_EMITTER']
        self.assertEqual(len(operations), 1)
        operation = operations[0]
        self.assertEqual(len(operation['output_references']), 1)
        self.assertEqual(wrappers[operation['output_references'][0]].kind, 'GENERATION_PLAN')
        receipt_roots = []
        records_by_diagnostic = {node.payload.diagnostic_reference: node for node in wrappers.values() if node.kind == 'PRODUCER_RECORD'}
        events_by_diagnostic = {event.diagnostic_reference: event for event in snapshot.events if event.diagnostic_reference is not None}
        for reference in operation['constructed_record_references']:
            node = records_by_diagnostic[reference]
            record = node.payload.to_record()
            self.assertEqual(events_by_diagnostic[reference].context.proof_evidence_reference, node.evidence_reference)
            if record['value_reference'] in wrappers and wrappers[record['value_reference']].kind == 'EMISSION_OUTPUT':
                self.assertEqual(record['value_reference'], record['payload_reference'])
                receipt_roots.append(record['value_reference'])
        self.assertEqual(len(set(receipt_roots)), 8)
        for reference in receipt_roots:
            self.assertEqual(wrappers[reference].payload.actual_status, 'SUCCEEDED')
        exported = diagnostics.export_pair(snapshot)
        self.assertIs(type(exported), dv.ExportReceipt)
        raw = (diagnostics.store.root/'diagnostics.json').read_bytes()
        markdown = (diagnostics.store.root/'diagnostics.md').read_bytes()
        manifest = json.loads((diagnostics.store.root/'manifest.json').read_bytes())
        self.assertEqual(snapshot.to_record(), json.loads(raw))
        self.assertEqual(json.loads(raw), json.loads(markdown.split(b'```json\n', 1)[1].rsplit(b'\n```', 1)[0]))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['json_sha256'])
        self.assertEqual(hashlib.sha256(markdown).hexdigest(), manifest['markdown_sha256'])
        self.assertEqual('EXACT_EMBEDDED_SNAPSHOT', manifest['parity'])
        Draft202012Validator(json.loads((ROOT/'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text())).validate(json.loads(raw))

    def test_concurrent_first_registration_has_one_live_registry_without_io(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        barrier = threading.Barrier(3)
        results = []
        before = len(store.calls), clock.value, dict(diagnostics._aliases)
        def register(owner):
            barrier.wait()
            results.append(diagnostics.register_module_producer(owner))
        threads = [threading.Thread(target=register, args=(owner,)) for owner in owners[:2]]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(5); self.assertFalse(thread.is_alive())
        self.assertEqual(('REGISTERED', 'REGISTERED'), tuple(row.status for row in results))
        self.assertEqual({'REALM_ENCODER', 'TRANSITION_REGISTRY'}, set(diagnostics._module_capture_service.registered))
        self.assertEqual(before, (len(store.calls), clock.value, dict(diagnostics._aliases)))

    def test_actual_four_producers_complete_all_records_pages_and_exact_bindings(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        for index, owner in enumerate(owners):
            before = len(store.calls), clock.value, len(diagnostics._aliases)
            registered = diagnostics.register_module_producer(owner)
            self.assertEqual('REGISTERED', registered.status)
            self.assertEqual(before, (len(store.calls), clock.value, len(diagnostics._aliases)))
            result = result_for(owner, origin, f'module:complete:{index}')
            receipt, admission = execute(diagnostics, owner, result)
            self.assertEqual('CONFIRMED', receipt.status, receipt)
            self.assertEqual('COMPLETE', receipt.completion.status)
            self.assertEqual(len(capture._facts(result)[2]), len(receipt.confirmed_records))
            self.assertIs(receipt.completion, admission.scope.finish(result))
            self.assertIs(receipt.final_observation, admission.scope.observe_final(result, receipt.completion))
            self.assertLessEqual(len(m.raw_business_bytes(receipt)), m.RAW_LIMIT)
        snapshot = diagnostics.snapshot(bundle_reference='module:complete:bundle')
        wrappers = snapshot.supporting_evidence.module_evidence
        self.assertEqual(len(wrappers), len({row.evidence_reference for row in wrappers}))
        self.assertEqual(46, sum(row.kind == 'TOPOLOGY_PAGE' for row in wrappers))
        pages = [row.payload.to_record() for row in wrappers if row.kind == 'TOPOLOGY_PAGE']
        self.assertEqual(729, sum(len(row['nodes']) for row in pages))
        self.assertEqual('r222222', pages[-1]['nodes'][-1]['path'])
        checks = [row.payload.to_record() for row in wrappers if row.kind == 'AXIOM_CHECK']
        self.assertEqual(5, len(checks))
        self.assertTrue(checks[-1]['passed']); self.assertFalse(checks[-1]['overall_pass'])
        schema = json.loads((ROOT/'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text())
        Draft202012Validator(schema).validate(snapshot.to_record())
        self.assertNotIn('caller-seed-token', json.dumps(snapshot.to_record()))
        self.assertEqual({'GENERATION_PLANNER', 'ARTIFACT_EMITTER'},
            {row.source for row in snapshot.coverage if row.source in m.PRODUCERS and row.status == 'EXCLUDED'})

    def test_registration_and_foreign_result_origin_capacity_refuse_without_io(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        owner = owners[0]
        self.assertEqual('REGISTERED', diagnostics.register_module_producer(owner).status)
        result = result_for(owner, origin, 'module:refusals')
        before = len(store.calls), clock.value, dict(diagnostics._aliases)
        self.assertEqual('MODULE_PRODUCER_DUPLICATE', diagnostics.register_module_producer(owner).failure_code)
        self.assertEqual('REJECTED', start(diagnostics, owner, copy(result)).status)
        other, _, other_owners, other_origin, _, _ = assembly()
        foreign = result_for(other_owners[0], other_origin, 'module:foreign')
        self.assertEqual('REJECTED', start(diagnostics, owner, foreign).status)
        self.assertEqual(before, (len(store.calls), clock.value, dict(diagnostics._aliases)))
        diagnostics._used = 33554432
        self.assertEqual('MODULE_RESERVATION_REFUSED', start(diagnostics, owner, result).failure_code)
        self.assertEqual(before, (len(store.calls), clock.value, dict(diagnostics._aliases)))

    def test_copied_generation_owner_and_reflected_self_reset_refuse_without_io(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        before = len(store.calls), clock.value, dict(diagnostics._aliases)
        for owner in owners[2:]:
            for candidate in (copy(owner), deepcopy(owner,{id(model):model})):
                object.__setattr__(candidate,'_self_identity',candidate)
                self.assertEqual('REJECTED',diagnostics.register_module_producer(candidate).status)
        self.assertEqual(before,(len(store.calls),clock.value,dict(diagnostics._aliases)))

    def test_partial_unknown_event_retains_actual_result_first_finish_and_export(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        diagnostics.register_module_producer(owners[0])
        store.unknown_sequence = 2
        result = result_for(owners[0], origin, 'module:partial')
        receipt, admission = execute(diagnostics, owners[0], result)
        self.assertIs(result, receipt.result)
        self.assertEqual(1, len(receipt.confirmed_records))
        self.assertEqual('INCOMPLETE', receipt.completion.status)
        self.assertEqual('PARTIAL', diagnostics.health().coverage_status)
        snapshot = diagnostics.snapshot(bundle_reference='module:partial:bundle')
        self.assertEqual((0,1,2), tuple(event.local_sequence for event in snapshot.events))
        self.assertEqual(1, snapshot.health.last_confirmed_sequence)
        diagnostics.export_pair(snapshot)
        raw, markdown, _ = store.published
        self.assertEqual(json.loads(raw), json.loads(markdown.split(b'```json\n',1)[1].rsplit(b'\n```',1)[0]))

    def test_unknown_support_is_retained_and_no_false_final_ack(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        diagnostics.register_module_producer(owners[0])
        store.unknown_kind = 'PRODUCER_RECORD'
        result = result_for(owners[0], origin, 'module:unknown-support')
        receipt, admission = execute(diagnostics, owners[0], result)
        self.assertEqual('INCOMPLETE', receipt.completion.status)
        self.assertNotEqual('CONFIRMED', receipt.status)
        snapshot = diagnostics.snapshot(bundle_reference='module:unknown-support:bundle')
        self.assertTrue(any(row.kind == 'PRODUCER_RECORD' for row in snapshot.supporting_evidence.module_evidence))
        self.assertTrue(any(kind == 'PRODUCER_RECORD' for kind, alias in diagnostics._unconfirmed_support))
        self.assertEqual('UNCERTAIN', snapshot.health.storage_state)

    def test_unconfirmed_admission_retains_real_scope_and_once_cleanup(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        diagnostics.register_module_producer(owners[0]); store.unknown_kind = 'PRODUCER_SOURCE'
        result = result_for(owners[0], origin, 'module:admission-unknown')
        receipt, admission = execute(diagnostics, owners[0], result)
        self.assertEqual('NOT_CONFIRMED', admission.status)
        self.assertIsNotNone(admission.scope)
        self.assertEqual('INCOMPLETE', receipt.completion.status)
        self.assertIs(receipt.completion, admission.scope.finish(result))

    def test_omission_audit_is_once_after_return_including_missing_final(self):
        for missing in ('records', 'finish', 'final'):
            diagnostics, model, owners, origin, store, clock = assembly()
            diagnostics.register_module_producer(owners[0])
            result = result_for(owners[0], origin, 'module:omit:' + missing)
            scope = start(diagnostics, owners[0], result).scope
            if missing != 'records':
                for record in result.constructed_records:
                    self.assertEqual('CONFIRMED', scope.append(record).status)
            if missing == 'final':
                self.assertEqual('COMPLETE', scope.finish(result).status)
            self.assertIsNone(diagnostics.health().last_failure_code)
            first = diagnostics.audit_module_return(scope, boundary='RETURN')
            count = len(diagnostics._meta)
            second = diagnostics.audit_module_return(scope, boundary='SHUTDOWN')
            self.assertEqual('MISSING', first.status)
            self.assertEqual('FIRST_COMPLETION' if missing == 'finish' else 'REQUIRED_CAPTURE_STEP', first.missing_kind)
            self.assertEqual('ALREADY_OBSERVED', second.status)
            self.assertEqual(count, len(diagnostics._meta))

    def test_concurrent_first_finish_and_final_observer_are_single_actual_operations(self):
        for phase in ('finish', 'final'):
            diagnostics, model, owners, origin, store, clock = assembly()
            diagnostics.register_module_producer(owners[0])
            result = result_for(owners[0], origin, 'module:concurrent:' + phase)
            scope = start(diagnostics, owners[0], result).scope
            for record in result.constructed_records:
                self.assertEqual('CONFIRMED', scope.append(record).status)
            completion = scope.finish(result) if phase == 'final' else None
            store.block_kind = 'PRODUCER_OPERATION' if phase == 'finish' else 'PRODUCER_FINAL_OBSERVATION'
            outcomes = []
            method = (lambda: scope.finish(result)) if phase == 'finish' else (lambda: scope.observe_final(result, completion))
            thread = threading.Thread(target=lambda: outcomes.append(method()))
            thread.start(); self.assertTrue(store.entered.wait(5))
            try:
                with self.assertRaises(dv.DiagnosticsContractError) as error:
                    method()
                self.assertEqual('DIAGNOSTICS_RESERVATION_REFUSED', error.exception.code)
            finally:
                store.release.set(); thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(1, len(outcomes)); self.assertIs(outcomes[0], method())
            self.assertEqual(1, sum(name == 'commit_supporting' and args[1] == store.block_kind for name, args in store.calls))

    def test_concurrent_append_rechecks_order_after_actual_pre_io_scheduling(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        diagnostics.register_module_producer(owners[0])
        result = result_for(owners[0], origin, 'module:concurrent:append')
        scope = start(diagnostics, owners[0], result).scope
        barrier, first_complete = threading.Barrier(2), threading.Event()
        original_io = d._ReferenceDiagnostics._session_io
        outcomes = {}
        def scheduled_io(owner):
            if threading.current_thread().name in ('append:first', 'append:second'):
                barrier.wait(timeout=5)
                if threading.current_thread().name == 'append:second':
                    if not first_complete.wait(5):
                        raise AssertionError('first actual append did not complete')
            return original_io(owner)
        def append(name):
            try:
                outcomes[name] = scope.append(result.constructed_records[0])
            finally:
                if name == 'first':
                    first_complete.set()
        with patch.object(d._ReferenceDiagnostics,'_session_io',scheduled_io):
            threads = [threading.Thread(target=append,args=(name,),name='append:'+name) for name in ('first','second')]
            for thread in threads:thread.start()
            for thread in threads:thread.join(5);self.assertFalse(thread.is_alive())
        self.assertEqual('CONFIRMED',outcomes['first'].status)
        self.assertEqual('REJECTED',outcomes['second'].status)
        self.assertEqual(1,len(scope._native.indices))
        self.assertEqual(1,sum(event.source=='REALM_ENCODER' for event in diagnostics._events))

    def test_copied_foreign_scope_and_service_hooks_do_not_execute(self):
        diagnostics, model, owners, origin, store, clock = assembly()
        diagnostics.register_module_producer(owners[0])
        result = result_for(owners[0], origin, 'module:foreign-scope')
        scope = start(diagnostics, owners[0], result).scope
        entered = []
        class Hostile:
            def __getattr__(self, name):
                entered.append(name)
                raise AssertionError('unowned scope callback')
        malformed = object.__new__(capture.ModuleCaptureScope)
        malformed._service = Hostile()
        malformed._native = scope._native
        malformed._self_identity = malformed
        for candidate in (copy(scope), malformed):
            for method in (capture.ModuleCaptureScope.append, capture.ModuleCaptureScope.finish):
                with self.assertRaises(m.ModuleContractError):
                    method(candidate, result.constructed_records[0] if method is capture.ModuleCaptureScope.append else result)
        self.assertEqual([], entered)
        diagnostics._modules = lambda: entered.append('collector-instance-hook')
        self.assertEqual('MODULE_PRODUCER_DUPLICATE', diagnostics.register_module_producer(owners[0]).failure_code)
        self.assertEqual([], entered)

    def test_release_keeps_exact_semantics_and_ordered_capture(self):
        diagnostics, model, owners, origin, store, clock = assembly(release=True)
        for index, owner in enumerate(owners):
            self.assertEqual('REGISTERED', diagnostics.register_module_producer(owner).status)
            result = result_for(owner, origin, 'module:release:' + str(index), depth=1)
            receipt, _ = execute(diagnostics, owner, result)
            self.assertEqual('CONFIRMED', receipt.status)


class ModuleValueAndSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schemas = [json.loads(path.read_text()) for path in (ROOT/'data/schemas').glob('*.json')]
        cls.registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas if '$id' in schema)
        cls.capture_schema = json.loads((ROOT/'data/schemas/m3_module_capture_schema.json').read_text())
        cls.bundle_schema = json.loads((ROOT/'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text())

    def test_actual_five_wire_controls_and_partial_prefix_validate(self):
        catalog = runtime_capture_controls()
        Draft202012Validator(self.capture_schema, registry=self.registry).validate(catalog)
        self.assertEqual(5, len({case['type_name'] for case in catalog['cases']}))
        partial = catalog['cases'][-1]['value']
        self.assertEqual('INCOMPLETE', partial['completion']['status'])
        self.assertEqual(1, len(partial['confirmed_records']))
        for case in catalog['cases']:
            schema = {'$ref': self.capture_schema['$id']+'#/$defs/'+case['type_name']}
            bad = dict(case['value']); bad['unknown_field'] = 'untrusted'
            self.assertFalse(Draft202012Validator(schema, registry=self.registry).is_valid(bad))

    def test_hostile_metaclass_in_context_dependencies_and_nested_bindings_has_no_hooks(self):
        entered = []
        class Meta(type):
            def __eq__(self, other):
                entered.append('eq');return False
            def __hash__(self):
                entered.append('hash');return type.__hash__(self)
        class Hostile(metaclass=Meta):
            def __str__(self):
                entered.append('str');raise AssertionError('unowned conversion')
        diagnostics, model, owners, origin, store, clock = assembly()
        diagnostics.register_module_producer(owners[0])
        result = result_for(owners[0],origin,'module:hostile:context')
        binding = owners[0].configuration()
        before = len(store.calls),clock.value,dict(diagnostics._aliases)
        with self.assertRaises(m.ModuleContractError):
            m.ModuleCaptureContext(result.operation_reference,'REALM_ENCODER',binding,origin,Hostile(),())
        with self.assertRaises(m.ModuleContractError):
            m.ModuleCaptureContext(result.operation_reference,'REALM_ENCODER',binding,origin,result,(Hostile(),))
        context = m.ModuleCaptureContext(result.operation_reference,'REALM_ENCODER',binding,origin,result,())
        corrupt = copy(context)
        object.__setattr__(corrupt,'dependency_results',(Hostile(),))
        self.assertEqual('REJECTED',diagnostics.module_capture(owners[0],corrupt).status)
        corrupt = copy(context);bad_binding=copy(binding)
        object.__setattr__(bad_binding,'profile_binding',Hostile())
        object.__setattr__(corrupt,'source_binding',bad_binding)
        self.assertEqual('REJECTED',diagnostics.module_capture(owners[0],corrupt).status)
        with self.assertRaises(dv.DiagnosticsContractError):
            d._ReferenceDiagnostics._modules(Hostile())
        self.assertEqual([],entered)
        self.assertEqual(before,(len(store.calls),clock.value,dict(diagnostics._aliases)))

    def test_all17_exact_wrapper_schema_branches_and_runtime_kind_mapping(self):
        leaves = json.loads((ROOT/'docs/design-planning/m3/module-diagnostics/SAFE_MAXIMUM_LEAVES.json').read_text())
        schema = self.bundle_schema['$defs']['SafeModuleEvidence']
        self.assertEqual(17, len(leaves))
        def immutable(value):
            if type(value) is list:
                return tuple(immutable(child) for child in value)
            if type(value) is dict:
                return {name: immutable(child) for name, child in value.items()}
            return value
        for index, (kind, maximum) in enumerate(leaves.items()):
            Draft202012Validator(schema).validate(maximum)
            body = immutable(maximum['payload'])
            if kind == 'PRODUCER_RECORD':
                body['actual_pure_target_diagnostic'] = None
            value = m.SafeModuleEvidence(kind, f'ref:{index+1:06d}', m.SAFE_CLASSES[kind](**body))
            Draft202012Validator(schema).validate(value.to_record())
            bad = dict(value.to_record()); bad['kind'] = 'UNOWNED'
            self.assertFalse(Draft202012Validator(schema).is_valid(bad))
            with self.assertRaises(m.ModuleContractError):
                m.SafeModuleEvidence('UNOWNED', value.evidence_reference, value.payload)
        self.assertEqual(m.KIND_QUOTAS, dv.MODULE_KIND_QUOTAS)

    def test_closed_completion_upper_rederived_from_actual_schema(self):
        defs = self.bundle_schema['$defs']
        encoded = lambda value: json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('ascii')
        def maximum(node):
            if '$ref' in node:
                return maximum(defs[node['$ref'].split('/')[-1]])
            if 'const' in node:
                return node['const']
            if 'enum' in node:
                return max(node['enum'], key=lambda value: len(encoded(value)))
            if 'anyOf' in node:
                return max((maximum(child) for child in node['anyOf']), key=lambda value: len(encoded(value)))
            kind = node['type']
            if kind == 'object':
                return {name: maximum(child) for name, child in node['properties'].items()}
            if kind == 'array':
                return [maximum(node['items']) for _ in range(node['maxItems'])]
            if kind == 'integer':
                return max((node.get('minimum', 0), node['maximum']), key=lambda value: len(encoded(value)))
            if kind == 'string':
                return '\U0001ffff'*node['maxLength']
            return False if kind == 'boolean' else None
        row = maximum(defs['DiagnosticsCompletionReceipt'])
        self.assertEqual(capture.MAX_COMPLETION_WIRE_BYTES, len(encoded(row)))
        self.assertEqual((768,32,16,8), (len(row['confirmed_event_indices']),len(row['health']['missing_sources']),
            len(row['health']['retention_boundaries']),len(row['health']['counter_states'])))

    def test_inline_target_requires_existing_owned_logically_coherent_validity(self):
        leaf = json.loads((ROOT/'docs/design-planning/m3/module-diagnostics/SAFE_MAXIMUM_LEAVES.json').read_text())['PRODUCER_RECORD']['payload']
        def freeze(value):
            return tuple(freeze(child) for child in value) if type(value) is list else {name:freeze(child) for name,child in value.items()} if type(value) is dict else value
        with self.assertRaises(m.ModuleContractError):
            m.SafeProducerRecord(**freeze(leaf))


if __name__ == '__main__':
    unittest.main()
