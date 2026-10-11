from __future__ import annotations

from collections import Counter
import copy
import dataclasses
import hashlib
import json
import os
import re
import unittest
from unittest import mock

from core.ash_pattern_engine import realm_transition_values as v, state_values as s
from core.ash_pattern_engine.realm_transition import RealmEncoder, TransitionRegistry, RealmTransitionReferenceRunner
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from tests.test_m3_realm_transition_values import ROOT, assembly, diagnosis, profile_from


def independent_codes():
    text = (ROOT / 'core/ash_pattern_engine/canonical/core/codeword-set.pseudo.md').read_text(encoding='utf-8')
    rows = re.findall(r'^\s*(\d+)\s+\(([01](?:, [01]){8})\)\s+[048]\s*$', text, re.M)
    if tuple(int(index) for index, _ in rows) != tuple(range(16)):
        raise AssertionError('Missing source-order canonical C16')
    return tuple(int(bits.replace(', ', ''), 2) for _, bits in rows)


class SharedDiagnosisValidationTests(unittest.TestCase):
    def test_complete_2048_state_profile_math_and_current_binding(self):
        codes = independent_codes()
        wrw = tuple(1 << index for index in range(9))
        profiles = [('wrw', wrw), ('neutral', (0,)), ('empty', ()), ('orbit', codes)]
        for label, recognized in profiles:
            profile = profile_from(tuple(f'{n:09b}' for n in recognized), 'validation:' + label)
            model, _, _ = assembly(profile=profile)
            counts = Counter()
            for number in range(512):
                observed = diagnosis(model, f'{number:09b}', f'validation:{label}:{number}')
                receipt = StateModel.validate_diagnosis(model, observed)
                expected = 'VALID' if number in recognized else 'TRANSFORMATION_COMPATIBLE' if any(number ^ code in recognized for code in codes) else 'TRANSFORMATION_INCOMPATIBLE'
                self.assertEqual(receipt.status, 'VERIFIED')
                self.assertEqual(receipt.derived_diagnostic.admissibility_status, expected)
                self.assertEqual(receipt.derived_diagnostic.orbit_info.orbit_id, f'{min(number ^ code for code in codes):09b}')
                self.assertEqual(receipt.derived_diagnostic, observed.state_validity_diagnostic)
                self.assertIs(receipt.submitted_diagnosis, observed)
                counts[expected] += 1
            if label == 'wrw':
                self.assertEqual(counts, {'VALID': 9, 'TRANSFORMATION_COMPATIBLE': 135, 'TRANSFORMATION_INCOMPATIBLE': 368})

    def test_source_profile_input_math_and_envelope_refusals(self):
        model, _, _ = assembly()
        original = diagnosis(model)
        foreign = dataclasses.replace(original, source_binding=s.CanonicalAshBinding(**dict(s.CURRENT_CANONICAL_BINDING_FIELDS)))
        receipt = StateModel.validate_diagnosis(model, foreign)
        self.assertEqual((receipt.status, receipt.failure_code), ('REJECTED', 'SOURCE_BINDING_MISMATCH'))
        changed_profile = dataclasses.replace(original, profile_binding=profile_from(('100000000',), 'foreign:profile'))
        self.assertEqual(StateModel.validate_diagnosis(model, changed_profile).failure_code, 'PROFILE_BINDING_MISMATCH')
        changed_input = dataclasses.replace(original, input_evidence=dataclasses.replace(original.input_evidence, preview='010000000'))
        self.assertEqual(StateModel.validate_diagnosis(model, changed_input).failure_code, 'INPUT_BINDING_MISMATCH')
        raw = diagnosis(model, b'[1,0,0,0,0,0,0,0,0]')
        changed_raw = dataclasses.replace(raw, input_evidence=dataclasses.replace(raw.input_evidence,
                        preview=b'[0,1,0,0,0,0,0,0,0]'.hex()))
        self.assertEqual(StateModel.validate_diagnosis(model, changed_raw).failure_code, 'INPUT_BINDING_MISMATCH')
        wrong_notes = dataclasses.replace(original, state_validity_diagnostic=dataclasses.replace(original.state_validity_diagnostic, notes=('Forged but structurally valid explanation.',)))
        self.assertEqual(StateModel.validate_diagnosis(model, wrong_notes).failure_code, 'DIAGNOSIS_MISMATCH')
        wrong_orbit = dataclasses.replace(original, state_validity_diagnostic=dataclasses.replace(original.state_validity_diagnostic,
                    orbit_info=dataclasses.replace(original.state_validity_diagnostic.orbit_info, orbit_id='000000000')))
        self.assertEqual(StateModel.validate_diagnosis(model, wrong_orbit).failure_code, 'DIAGNOSIS_MISMATCH')
        first = original.emitted_diagnostics[0]
        wrong_impact = dataclasses.replace(original, emitted_diagnostics=(dataclasses.replace(first, envelope=dataclasses.replace(first.envelope, severity='CRITICAL')),))
        self.assertEqual(StateModel.validate_diagnosis(model, wrong_impact).failure_code, 'DIAGNOSIS_ENVELOPE_MISMATCH')

    def test_structural_mutation_cycles_subclasses_and_instance_hooks(self):
        model, encoder, registry = assembly()
        original = diagnosis(model)
        entered = []
        def forbidden(*args, **kwargs):
            entered.append(True)
            raise AssertionError('Injected callback entered pure operation')
        model.validate_diagnosis = forbidden
        model._diagnose = forbidden
        model._orbit = forbidden
        model.inspect_state = forbidden
        model._codec = forbidden
        with self.assertRaises(AttributeError):
            object.__setattr__(original, '_common_record', forbidden)
        receipt = StateModel.validate_diagnosis(model, copy.copy(original))
        self.assertEqual(receipt.status, 'VERIFIED')
        self.assertEqual(receipt.to_record()['status'], 'VERIFIED')
        encoded = RealmEncoder.encode(encoder, original, operation_reference='pure:encode')
        transformed = TransitionRegistry.apply(registry, original, v.TransitionSelection('IDENTIFIER', 'ash_codeword_01', None), operation_reference='pure:apply')
        self.assertTrue(RealmEncoder.validate_owned_result(encoder, encoded))
        self.assertTrue(TransitionRegistry.validate_owned_result(registry, transformed))
        self.assertEqual(entered, [])
        reflected = copy.copy(original)
        object.__setattr__(reflected, 'emitted_diagnostics', list(original.emitted_diagnostics))
        with self.assertRaises(s.StateContractError):
            StateModel.validate_diagnosis(model, reflected)
        cyclic = copy.copy(original)
        object.__setattr__(cyclic, 'parsed_state', cyclic)
        with self.assertRaises(s.StateContractError):
            StateModel.validate_diagnosis(model, cyclic)
        class ForeignDiagnosis(s.StateDiagnosis):
            pass
        with self.assertRaises(s.StateContractError):
            StateModel.validate_diagnosis(model, ForeignDiagnosis(*(getattr(original, field.name) for field in dataclasses.fields(original))))
        self.assertEqual(entered, [])

    def test_unavailable_malformed_and_truncated_observations_keep_truth(self):
        model, _, _ = assembly()
        for candidate in ('bad', [True] * 9, b'[0,0,0,0,0,0,0,0,0]' + b' ' * 80):
            original = diagnosis(model, candidate)
            receipt = StateModel.validate_diagnosis(model, original)
            self.assertEqual(receipt.status, 'VERIFIED')
            self.assertEqual(receipt.submitted_diagnosis.input_evidence, original.input_evidence)
        unavailable = s.UnavailableProfileBinding(s.UnavailableValidityProfileEvidence('unavailable',
                s.ProfileSourceBinding('test:unavailable', '0' * 64, 'test:unavailable:source'),
                'PROFILE_DATA_UNAVAILABLE', 'Explicit fixture absence.'))
        unavailable_model, encoder, _ = assembly(profile=unavailable)
        original = diagnosis(unavailable_model)
        receipt = StateModel.validate_diagnosis(unavailable_model, original)
        self.assertEqual(receipt.status, 'VERIFIED')
        self.assertEqual(receipt.derived_diagnostic.admissibility_status, 'UNCLASSIFIED')
        failure = encoder.encode(original, operation_reference='unavailable:encode')
        self.assertEqual(failure.failure_code, 'PROFILE_UNAVAILABLE')
        self.assertEqual(len(failure.constructed_records), 1)


class StrictRealmTransitionTests(unittest.TestCase):
    def test_unowned_metaclass_hooks_do_not_run_at_values_or_runner_boundary(self):
        _, encoder, registry = assembly()
        entered = []

        class HostileMeta(type):
            def __eq__(cls, other):
                entered.append('metaclass equality')
                return False

            def __hash__(cls):
                entered.append('metaclass hash')
                return 1

        class Hostile(metaclass=HostileMeta):
            def __getattribute__(self, name):
                entered.append('instance attribute ' + name)
                raise AssertionError('Unowned collaborator hook entered')

        hostile = Hostile()
        nested = copy.copy(encoder.configuration())
        object.__setattr__(nested, 'profile_binding', hostile)
        for boundary in (v.revalidate_value, v.canonical_bytes, v.raw_business_size,
                         lambda value: RealmTransitionReferenceRunner(encoder, registry, value)):
            for submitted in (hostile, nested):
                with self.subTest(boundary=boundary, nested=submitted is nested):
                    with self.assertRaises(v.RealmTransitionContractError) as rejected:
                        boundary(submitted)
                    self.assertEqual(rejected.exception.code, 'REALM_TRANSITION_VALUE_INVALID')
                    self.assertEqual(entered, [])

    def test_all512_encoder_gate_injective_full_identity_and_no_normalization(self):
        model, encoder, _ = assembly()
        counts, identities = Counter(), set()
        codes = independent_codes()
        for number in range(512):
            origin = diagnosis(model, f'{number:09b}', f'encode:origin:{number}')
            result = encoder.encode(origin, operation_reference=f'encode:{number}')
            counts[type(result).__name__] += 1
            self.assertIs(result.origin, origin)
            if type(result) is v.RealmEncodingResult:
                self.assertEqual(result.identity.vertex_id, f'ash_state_{number:09b}')
                self.assertEqual(result.identity.realm_id, result.identity.vertex_id)
                self.assertEqual(result.identity.orbit_id, f'{min(number ^ code for code in codes):09b}')
                identities.add(result.identity.vertex_id)
                self.assertEqual(tuple(record.phase for record in result.constructed_records), ('VALID_SOURCE', 'IDENTITY'))
            else:
                self.assertEqual(result.failure_code, 'STATE_NOT_VALID')
                self.assertEqual(len(result.constructed_records), 1)
                self.assertEqual(result.constructed_records[0].emission.envelope.disposition, 'BLOCKED')
        self.assertEqual(counts, {'RealmEncodingResult': 9, 'RealmTransitionFailure': 503})
        self.assertEqual(len(identities), 9)

    def test_actual_WRW_144_pairs_preserve9valid_135TC_and_target_strict_refusal(self):
        model, encoder, registry = assembly()
        codes, counts = independent_codes(), Counter()
        for source in (1 << index for index in range(9)):
            origin = diagnosis(model, f'{source:09b}', f'wrw:origin:{source}')
            for index, code in enumerate(codes):
                result = registry.apply(origin, v.TransitionSelection('IDENTIFIER', f'ash_codeword_{index:02d}', None), operation_reference=f'wrw:apply:{source}:{index}')
                self.assertEqual(int(result.candidate.signature, 2), source ^ code)
                counts[result.target_diagnosis.admissibility_status] += 1
                self.assertEqual(tuple(record.phase for record in result.constructed_records), v.PHASES[:1] + ('SELECTION', 'APPLICABILITY', 'TRANSFORMATION'))
                self.assertEqual(len(result.origin.emitted_diagnostics), 1)
                if result.target_diagnosis.admissibility_status != 'VALID':
                    destination = diagnosis(model, result.candidate, f'wrw:destination:{source}:{index}')
                    refused = encoder.encode(destination, operation_reference=f'wrw:strict-target:{source}:{index}')
                    self.assertEqual(refused.failure_code, 'STATE_NOT_VALID')
        self.assertEqual(counts, {'VALID': 9, 'TRANSFORMATION_COMPATIBLE': 135})

    def test_independent_whole_coset_256_pairs_ID_codeword_parity_and_involution(self):
        codes = independent_codes()
        model, encoder, registry = assembly(profile=profile_from(tuple(f'{code:09b}' for code in codes), 'coset:profile'))
        for source in codes:
            origin = diagnosis(model, f'{source:09b}', f'coset:origin:{source}')
            for index, code in enumerate(codes):
                by_id = registry.apply(origin, v.TransitionSelection('IDENTIFIER', f'ash_codeword_{index:02d}', None), operation_reference=f'coset:ID:{source}:{index}')
                by_word = registry.apply(origin, v.TransitionSelection('CODEWORD', None, s.AshState(tuple(map(int, f'{code:09b}')))), operation_reference=f'coset:word:{source}:{index}')
                self.assertEqual(by_id.candidate, by_word.candidate)
                self.assertEqual(by_id.target_diagnosis.admissibility_status, 'VALID')
                target = diagnosis(model, by_id.candidate, f'coset:target:{source}:{index}')
                again = registry.apply(target, v.TransitionSelection('IDENTIFIER', f'ash_codeword_{index:02d}', None), operation_reference=f'coset:back:{source}:{index}')
                self.assertEqual(again.candidate, origin.parsed_state)
                self.assertEqual(encoder.encode(target, operation_reference=f'coset:identity:{source}:{index}').identity.realm_id, 'ash_state_' + by_id.candidate.signature)

    def test_actual_all512_times16_apply_under32_complete_cosets_repeats_entire_wire(self):
        codes = independent_codes()
        self.assertEqual(16, len(set(codes)))
        # The expected partition comes from source C16 and integer XOR, never
        # from registry output, diagnosis orbit metadata or application results.
        remaining = set(range(512))
        cosets = []
        while remaining:
            representative = min(remaining)
            members = tuple(sorted(representative ^ code for code in codes))
            self.assertEqual(16, len(set(members)))
            self.assertTrue(set(members) <= remaining)
            cosets.append((representative, members))
            remaining.difference_update(members)
        self.assertEqual(32, len(cosets))
        self.assertEqual(list(range(512)), sorted(member for _, members in cosets for member in members))
        covered = set()
        for representative, members in cosets:
            model, _, registry = assembly(profile=profile_from(
                tuple(f'{number:09b}' for number in members), f'exhaustive:coset:{representative}'))
            for source in members:
                origin = diagnosis(model, f'{source:09b}', f'exhaustive:origin:{source}')
                self.assertEqual('VALID', origin.state_validity_diagnostic.admissibility_status)
                for index, code in enumerate(codes):
                    with self.subTest(source=source, codeword=index):
                        selection = v.TransitionSelection('IDENTIFIER', f'ash_codeword_{index:02d}', None)
                        operation = f'exhaustive:apply:{source}:{index}'
                        first = registry.apply(origin, selection, operation_reference=operation)
                        repeated = registry.apply(origin, selection, operation_reference=operation)
                        self.assertIs(type(first), v.TransitionApplicationResult)
                        self.assertIs(type(repeated), v.TransitionApplicationResult)
                        self.assertEqual(f'{source ^ code:09b}', first.candidate.signature)
                        self.assertEqual(f'{code:09b}', first.selected_definition.codeword.signature)
                        self.assertEqual('VALID', first.target_diagnosis.admissibility_status)
                        self.assertEqual(('VALID_SOURCE', 'SELECTION', 'APPLICABILITY', 'TRANSFORMATION'),
                                         tuple(record.phase for record in first.constructed_records))
                        self.assertTrue(TransitionRegistry.validate_owned_result(registry, first))
                        self.assertEqual(v.canonical_bytes(first), v.canonical_bytes(repeated))
                        self.assertNotIn((source, index), covered)
                        covered.add((source, index))
        self.assertEqual({(source, index) for source in range(512) for index in range(16)}, covered)

    def test_all512_full_mask_positions_have16actual_observations(self):
        # Each explicitly bound singleton profile makes the full source independently VALID.
        for number in range(512):
            signature = f'{number:09b}'
            model, _, registry = assembly(restricted=True, profile=profile_from((signature,), f'mask:profile:{number}'))
            result = registry.resolve(diagnosis(model, signature, f'mask:origin:{number}'), operation_reference=f'mask:resolve:{number}')
            self.assertEqual(len(result.availability), 16)
            self.assertEqual(len(result.constructed_records), 17)
            for index, observation in enumerate(result.availability):
                expected = number == 0 if index == 0 else True
                self.assertEqual(observation.is_applicable, expected)
                self.assertEqual(observation.reason_code, 'SOURCE_ALLOWED' if expected else 'SOURCE_NOT_ALLOWED')
                self.assertEqual(result.constructed_records[index + 1].emission.envelope.disposition, 'RESOLVED')

    def test_unknown_noncanonical_and_restricted_refusals_preserve_exact_prefix(self):
        model, encoder, registry = assembly(restricted=True)
        origin = diagnosis(model)
        cases = [(v.TransitionSelection('IDENTIFIER', 'well_formed_unknown', None), 'TRANSITION_UNKNOWN', 2),
                 (v.TransitionSelection('CODEWORD', None, s.AshState((1,) + (0,) * 8)), 'CODEWORD_NOT_CANONICAL', 2),
                 (v.TransitionSelection('IDENTIFIER', 'ash_codeword_00', None), 'TRANSITION_NOT_APPLICABLE', 3)]
        for selection, code, length in cases:
            result = registry.apply(origin, selection, operation_reference='refused:' + code)
            self.assertEqual(result.failure_code, code)
            self.assertEqual(len(result.constructed_records), length)
            self.assertEqual(result.constructed_records[-1].emission.envelope.disposition, 'BLOCKED')
            self.assertEqual(result.constructed_records[-1].emission.envelope.severity, 'ERROR')
            for ordinal, record in enumerate(result.constructed_records):
                self.assertEqual(record.emission.envelope.subject_reference, origin.emitted_diagnostics[0].envelope.subject_reference)
                self.assertEqual(record.emission.envelope.chain_root_reference, origin.assessment_binding.diagnosis_reference)
                self.assertEqual(record.record_reference, 'rt:' + hashlib.sha256(result.operation_reference.encode()).hexdigest() + ':' + str(ordinal))

    def test_origin_foreign_primitive_old_owner_vector_refuse_before_records(self):
        model, encoder, registry = assembly()
        old_model = StateModel(model.profile_binding, s.CanonicalAshBinding(**dict(s.CURRENT_CANONICAL_BINDING_FIELDS)), RecordingDiagnosticCapture())
        for origin in (None, diagnosis(old_model), dataclasses.replace(diagnosis(model), state_validity_diagnostic=dataclasses.replace(diagnosis(model).state_validity_diagnostic, notes=('Forged explanation.',)))):
            with self.assertRaises((v.RealmTransitionContractError, s.StateContractError)):
                encoder.encode(origin, operation_reference='refused:origin')
        with self.assertRaises(v.RealmTransitionContractError):
            RealmEncoder(old_model, encoder.configuration())

    def test_real_malformed_input_observations_include_invalid_utf8_and_nonfinite(self):
        model, encoder, registry = assembly()
        for index, candidate in enumerate(('\ud800', b'\xff', '1' * 4097, [float('nan')] + [0] * 8,
                                           [2] + [0] * 8, [True] + [0] * 8)):
            origin = diagnosis(model, candidate, f'malformed:origin:{index}')
            self.assertIsNone(origin.parsed_state)
            result = encoder.encode(origin, operation_reference=f'malformed:encode:{index}')
            self.assertEqual(result.failure_code, 'STATE_NOT_VALID')
            self.assertEqual(result.origin.input_evidence, origin.input_evidence)
            self.assertEqual(len(result.constructed_records), 1)
            self.assertEqual(json.loads(result.canonical_bytes())['origin']['input_evidence'], origin.input_evidence.to_record())


@unittest.skipUnless(os.name == 'nt', 'Actual protected backend is Windows-specific')
class RealmTransitionCaptureTests(unittest.TestCase):
    def create(self, *, fault_at=None, fault_mode=None, observer_fault=False):
        from core.ash_pattern_engine import diagnostics as diagnostics, diagnostics_values as dv
        from scripts.reference_diagnostics_host import assemble_reference_diagnostics, _verified_canonical_source_snapshots
        from tests.test_m3_reference_diagnostics import ControlledClock, FaultStore
        actual = assemble_reference_diagnostics(ROOT)
        self.addCleanup(actual.store.close)

        class ModuleFaultStore(FaultStore):
            def __init__(self, backend):
                super().__init__(backend)
                self.armed, self.module_appends = False, 0

            def __getattr__(self, name):
                operation = getattr(self.actual, name)
                def invoke(*args, **kwargs):
                    self.calls.append((name, args))
                    fail = False
                    if self.armed and name == 'commit_event':
                        self.module_appends += 1
                        fail = self.module_appends == fault_at
                    if self.armed and observer_fault and name == 'commit_supporting' and args[1] == 'PRODUCER_FINAL_OBSERVATION':
                        fail = True
                    if fail:
                        if fault_mode == 'THROW':
                            raise RuntimeError('Untrusted fault text must not enter a record')
                        if fault_mode == 'UNKNOWN':
                            response = operation(*args, **kwargs)
                            return dv.StorageReceipt(response.sequence, 'UNKNOWN', 'STORAGE_COMMIT_UNCONFIRMED')
                        sequence = args[0]
                        return dv.StorageReceipt(sequence, 'REJECTED', 'STORAGE_COMMIT_REJECTED')
                    return operation(*args, **kwargs)
                return invoke

        store = ModuleFaultStore(actual.store)
        _revision, snapshots = _verified_canonical_source_snapshots(ROOT)
        owner = diagnostics.ReferenceDevelopmentDiagnostics(actual.identity, actual.profile, store, ControlledClock(),
                                                           canonical_source_snapshots=snapshots)
        _, old_encoder, old_registry = assembly()
        model = StateModel(old_encoder.configuration().profile_binding, old_encoder.configuration().canonical_binding, owner.assessment_capture())
        encoder = RealmEncoder(model, old_encoder.configuration())
        registry = TransitionRegistry(model, old_registry._catalog)
        origin = diagnosis(model, reference='captured:origin')
        completion = owner.complete_assessment(origin)
        self.assertEqual(completion.status, 'COMPLETE', completion.failure_code)
        runner = RealmTransitionReferenceRunner(encoder, registry, owner)
        store.armed = True
        return owner, store, model, runner, origin

    def test_native_complete2_17_4_capture_and_actual_paired_safe_export(self):
        from core.ash_pattern_engine import diagnostics_values as dv
        from tests.test_m3_realm_transition_schemas import schema_registry
        from jsonschema import Draft202012Validator
        owner, store, model, runner, origin = self.create()
        results = (runner.run_encode(origin, operation_reference='captured:encode'),
                   runner.run_resolve(origin, operation_reference='captured:resolve'),
                   runner.run_apply(origin, v.TransitionSelection('IDENTIFIER', 'ash_codeword_01', None), operation_reference='captured:apply'))
        for receipt, count in zip(results, (2, 17, 4)):
            self.assertEqual(receipt.status, 'CONFIRMED')
            self.assertIsNone(receipt.failure_code)
            self.assertEqual(len(receipt.confirmed_records), count)
            self.assertEqual(receipt.completion.status, 'COMPLETE')
            self.assertEqual(receipt.final_observation.coverage, 'COMPLETE_SPECIFIED_SAFE_GRAPH')
            self.assertEqual(len(receipt.result.origin.emitted_diagnostics), 1)
            Draft202012Validator({'$ref': 'https://ywe.local/schemas/m3_realm_transition_schema.json#/$defs/RealmTransitionCaptureReceipt'}, registry=schema_registry()).validate(receipt.to_record())
        self.assertEqual(results[-1].result.target_diagnosis.admissibility_status, 'TRANSFORMATION_COMPATIBLE')
        snapshot = owner.snapshot(bundle_reference='captured:pair')
        schema = json.loads((ROOT / 'data/schemas/m3_reference_diagnostic_bundle_schema.json').read_text(encoding='utf-8'))
        Draft202012Validator(schema).validate(snapshot.to_record())
        pair = owner.export_pair(snapshot)
        self.assertIs(type(pair), dv.ExportReceipt)
        raw = (store.actual.root / 'diagnostics.json').read_bytes()
        markdown = (store.actual.root / 'diagnostics.md').read_bytes()
        embedded = markdown.split(b'```json\n', 1)[1].rsplit(b'\n```', 1)[0]
        self.assertEqual(json.loads(raw), json.loads(embedded))
        self.assertEqual(json.loads(raw), snapshot.to_record())
        self.assertNotIn(b'test:policy', raw)

    def test_authentic_immutable_origin_copy_API_only_and_duplicate_refusals_before_IO(self):
        owner, store, model, runner, origin = self.create()
        actual = runner.run_encode(copy.copy(origin), operation_reference='captured:copy')
        self.assertEqual(actual.status, 'CONFIRMED')
        retained = actual.canonical_bytes()
        before = len(store.calls)
        replay = runner.run_encode(origin, operation_reference='captured:copy')
        self.assertEqual(replay.status, 'REJECTED')
        self.assertEqual(replay.failure_code, 'MODULE_RESERVATION_REFUSED')
        self.assertIsNone(replay.completion)
        self.assertEqual(len(store.calls), before)
        self.assertEqual(actual.canonical_bytes(), retained)
        api_model = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture())
        api_only = diagnosis(api_model, reference='uncaptured:origin')
        refusal = runner.run_encode(api_only, operation_reference='uncaptured:encode')
        self.assertEqual(refusal.failure_code, 'MODULE_ORIGIN_REJECTED')
        self.assertEqual(len(store.calls), before)
        self.assertIs(type(refusal.result), v.RealmEncodingResult)
        self.assertEqual(refusal.confirmed_records, ())

    def test_actual_append_failures_preserve_prefix_attempt_and_once_cleanup(self):
        from core.ash_pattern_engine.diagnostic_module_capture import ModuleCaptureScope
        original_finish = ModuleCaptureScope.finish
        for position in (1, 2):
            for mode in ('REJECTED', 'UNKNOWN', 'THROW'):
                with self.subTest(position=position, mode=mode):
                    owner, store, model, runner, origin = self.create(fault_at=position, fault_mode=mode)
                    calls = []
                    def finish(scope, result):
                        calls.append(result)
                        return original_finish(scope, result)
                    with mock.patch.object(ModuleCaptureScope, 'finish', finish):
                        receipt = runner.run_encode(origin, operation_reference='fault:encode')
                    self.assertNotEqual(receipt.status, 'CONFIRMED')
                    self.assertEqual(len(receipt.confirmed_records), position - 1)
                    self.assertEqual(receipt.attempted_record, receipt.result.constructed_records[position - 1])
                    self.assertEqual(store.module_appends, position)
                    self.assertEqual(calls, [receipt.result])
                    self.assertEqual(receipt.completion.status, 'INCOMPLETE')
                    self.assertIsNotNone(receipt.final_observation)
                    self.assertEqual(len(receipt.result.constructed_records), 2)
                    self.assertEqual(receipt.result.identity.vertex_id, 'ash_state_100000000')
                    if mode == 'UNKNOWN':
                        sequence = [args[0] for name, args in store.calls if name == 'commit_event'][-1]
                        self.assertEqual(sequence, position)
                        self.assertTrue((store.actual.root / f'event-{sequence:020d}.json').exists())
                        self.assertNotEqual(receipt.final_observation.coverage, 'COMPLETE_SPECIFIED_SAFE_GRAPH')

    def test_later_observer_refusal_preserves_first_complete_and_pure_result(self):
        owner, store, model, runner, origin = self.create(observer_fault=True, fault_mode='UNKNOWN')
        receipt = runner.run_encode(origin, operation_reference='observer:encode')
        self.assertEqual(receipt.status, 'NOT_CONFIRMED')
        self.assertEqual(receipt.completion.status, 'COMPLETE')
        self.assertEqual(len(receipt.confirmed_records), 2)
        self.assertEqual(receipt.final_observation.status, 'NOT_CONFIRMED')
        self.assertEqual(receipt.final_observation.coverage, 'STORAGE_UNCERTAIN')
        self.assertEqual(receipt.result.identity.vertex_id, 'ash_state_100000000')
        first, packet = receipt.completion, receipt.result.canonical_bytes()
        snapshot = owner.snapshot(bundle_reference='observer:snapshot')
        self.assertEqual(receipt.completion, first)
        self.assertEqual(receipt.result.canonical_bytes(), packet)
        self.assertNotEqual(snapshot.health.coverage_status, 'COMPLETE_DECLARED_REFERENCE_SCOPE')

    def test_lost_finish_response_has_no_fabricated_completion_or_retry(self):
        from core.ash_pattern_engine.diagnostic_module_capture import ModuleCaptureScope
        owner, store, model, runner, origin = self.create()
        original_finish, calls = ModuleCaptureScope.finish, []
        def lost_response(scope, result):
            calls.append(original_finish(scope, result))
            raise RuntimeError('Response lost after actual first finish')
        with mock.patch.object(ModuleCaptureScope, 'finish', lost_response):
            receipt = runner.run_encode(origin, operation_reference='finish:lost')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].status, 'COMPLETE')
        self.assertIsNone(receipt.completion)
        self.assertIsNone(receipt.final_observation)
        self.assertEqual(receipt.status, 'NOT_CONFIRMED')
        self.assertEqual(receipt.failure_code, 'MODULE_COMPLETION_MISSING')
        self.assertEqual(len(receipt.confirmed_records), 2)


if __name__ == '__main__':
    unittest.main()
