from __future__ import annotations

import collections
import copy
import dataclasses
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest import mock

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.ash_pattern_engine import normalization_values as nv
from core.ash_pattern_engine import normalization
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'core/ash_pattern_engine/canonical'
AGGREGATE = '0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb'
CODEWORD_PIN = '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c'
POLICY_PIN = '804eec92cf52b465b7aaf0cb5f139f581ac2899d13203a8c4cfe9f4d7579c383'
# Fingerprint of seven expectation columns in the independently reviewed 2,048 rows.
# It binds source-derived expectations, not any production execution claim.
REVIEWED_ROWS_PIN = '8dcaa3e70a3e5cf19539be76c15c6e7c9e7ed3357b1877004516cbcbe9e239cc'
SOURCE_FIELDS = {
    'state_space_sha256': 'core/ash-state-space.pseudo.md',
    'codeword_source_sha256': 'core/codeword-set.pseudo.md',
    'validity_source_sha256': 'core/state-validity-diagnostics.pseudo.md',
    'classification_source_sha256': 'core/system-state-classification.pseudo.md',
    'recovery_source_sha256': 'core/recoverability-semantics.pseudo.md',
    'diagnostic_source_sha256': 'interfaces/diagnostic-schema.md',
    'taxonomy_source_sha256': 'interfaces/rule-id-taxonomy.md',
}
DIAGNOSIS_RULES = ('ASH-STATE-STRUCTURE-001', 'ASH-ADMISSIBILITY-CLASSIFICATION-001',
                   'ASH-STATE-VALIDITY-001')
CODEWORD_RULE = 'ASH-CODEWORD-STRUCTURE-001'
SEMANTIC_FIELDS = ('input_state', 'admissibility_status', 'transformation_compatibility',
                   'normalization_status', 'recoverability_relevance', 'is_valid', 'orbit_info')
ROWS = {
    'VALID': ('COMPATIBLE', 'ALREADY_VALID', 'NO_RECOVERY_NEEDED', True),
    'TRANSFORMATION_COMPATIBLE': ('COMPATIBLE', 'NORMALIZABLE', 'RECOVERY_APPLICABLE', False),
    'TRANSFORMATION_INCOMPATIBLE': ('INCOMPATIBLE', 'NOT_NORMALIZABLE', 'NOT_RECOVERABLE', False),
    'UNCLASSIFIED': ('UNKNOWN', 'BLOCKED', 'CONTAINMENT_NEEDED', False),
}
IMPACT = {'VALID': ('INFO', 'RESOLVED'), 'TRANSFORMATION_COMPATIBLE': ('WARNING', 'PENDING'),
          'TRANSFORMATION_INCOMPATIBLE': ('ERROR', 'BLOCKED'), 'UNCLASSIFIED': ('ERROR', 'BLOCKED')}
SEVERITY = {'INFO': 0, 'WARNING': 1, 'ERROR': 2, 'CRITICAL': 3}
PLAN_FIELDS = ('plan_reference', 'evidence_reference', 'policy_binding', 'original_diagnosis',
               'decision', 'eligible_targets_complete', 'eligible_targets', 'selected_target',
               'codeword_chain', 'reason_code')
VALIDATION_FIELDS = ('plan', 'original_diagnosis', 'canonical_binding', 'profile_binding',
                     'origin_validation_status', 'validation_status', 'failure_code', 'field_name',
                     'expected_decision', 'recomputed_eligible_targets', 'recomputed_target',
                     'recomputed_codeword_chain')
COMMON_FIELDS = ('outcome', 'operation_binding', 'plan', 'plan_validation', 'original_diagnosis',
                 'actual_state', 'steps', 'post_validity_diagnostic', 'normalized_state',
                 'inherited_diagnostics', 'emitted_diagnostics')


def normalized_hash(path):
    data = path.read_bytes().decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def generator_codewords():
    """Parse four source generators; compute closure with integer XOR independently."""
    text = (CANONICAL / 'core/codeword-set.pseudo.md').read_text(encoding='utf-8')
    generators = re.findall(r'^g([1-4]) = \(([01](?:, [01]){8})\)$', text, re.M)
    if [index for index, _ in generators] != ['1', '2', '3', '4']:
        raise AssertionError('The pinned independent generator block is incomplete')
    closure = {0}
    for _, digits in generators:
        generator = int(digits.replace(', ', ''), 2)
        closure |= {member ^ generator for member in tuple(closure)}
    enumeration = re.findall(r'^\s*(\d+)\s+\(([01](?:, [01]){8})\)\s+[048]\s*$', text, re.M)
    if [int(index) for index, _ in enumeration] != list(range(16)):
        raise AssertionError('The source enumeration is not all sixteen numbered rows')
    if closure != {int(digits.replace(', ', ''), 2) for _, digits in enumeration}:
        raise AssertionError('Independent generator closure disagrees with source enumeration')
    return tuple(sorted(closure))


def wrw_signatures():
    text = (ROOT / 'data/ash_state/realm_bit_mapping.yaml').read_text(encoding='utf-8')
    result = tuple(sorted(re.findall(r'^    state_identity: "([01]{9})"$', text, re.M)))
    if len(result) != 9 or len(set(result)) != 9:
        raise AssertionError('The explicit WRW mapping must retain nine distinct anchors')
    return result


def declared_profiles():
    return {
        'wrw_reference_profile': wrw_signatures(),
        'ywe.validation.neutral-origin.v1': ('000000000',),
        'ywe.validation.empty-known-set.v1': (),
        'ywe.validation.multi-target-same-orbit.v1': ('000000000', '000011110', '001100110'),
    }


def expected_case(signature, recognized, codewords):
    original = int(signature, 2)
    orbit = {original ^ word for word in codewords}
    targets = tuple(sorted(state for state in recognized if int(state, 2) in orbit))
    if signature in recognized:
        status, outcome, target, chain = 'VALID', 'ALREADY_VALID', signature, ()
    elif targets:
        status, outcome, target = 'TRANSFORMATION_COMPATIBLE', 'NORMALIZED', targets[0]
        chain = (format(original ^ int(target, 2), '09b'),)
    else:
        status, outcome, target, chain = 'TRANSFORMATION_INCOMPATIBLE', 'NOT_NORMALIZABLE', None, ()
    return status, outcome, targets, target, chain, format(min(orbit), '09b')


def canonical_record():
    return {'dependency_id': 'ash_cosmological_model.f2_9.canonical', 'aggregate_sha256': AGGREGATE,
            **{field: normalized_hash(CANONICAL / path) for field, path in SOURCE_FIELDS.items()}}


def source_record(profile_id, signatures):
    reference = 'data/ash_state/realm_bit_mapping.yaml' if profile_id == 'wrw_reference_profile' else 'tests/test_m3_normalization.py:' + profile_id
    digest = normalized_hash(ROOT / reference) if profile_id == 'wrw_reference_profile' else hashlib.sha256(
        json.dumps(list(signatures), separators=(',', ':')).encode('ascii')).hexdigest()
    return {'source_reference': reference, 'source_sha256': digest,
            'evidence_reference': profile_id + ':declared_source'}


def ash(signature):
    return sv.AshState(tuple(int(bit) for bit in signature))


def profile_binding(profile_id='wrw_reference_profile', signatures=None, source=None):
    signatures = wrw_signatures() if signatures is None else tuple(signatures)
    source = sv.ProfileSourceBinding(**source_record(profile_id, signatures)) if source is None else source
    return sv.AvailableProfileBinding(sv.ValidityProfile(profile_id, source, [ash(s) for s in signatures]))


def diagnostic_context(reference):
    return sv.DiagnosticContext(reference, reference + ':input', reference + ':detection', reference + ':classification')


def operation_context(reference='n1:operation'):
    return nv.NormalizationContext(reference, reference + ':computation', reference + ':post')


def policy_binding():
    return nv.NormalizationPolicyBinding('YWE-NORMALIZE-LEXICOGRAPHIC-001', '1.0.0',
                                         'docs/architecture/m3_normalization_policy.md', POLICY_PIN)


def authored_wire_packets():
    """Author wire evidence with dictionaries and the source generator oracle only.

    This function deliberately never calls a production value constructor, model,
    plan, computation, capture or serializer. Its packets describe declared cases.
    """
    words = generator_codewords()
    source = canonical_record()
    policy = {'policy_id': 'YWE-NORMALIZE-LEXICOGRAPHIC-001', 'policy_version': '1.0.0',
              'source_reference': 'docs/architecture/m3_normalization_policy.md', 'source_sha256': POLICY_PIN}
    plan_header = {'schema_ref': 'data/schemas/m3_normalization_plan_schema.json',
                   'artifact_type': 'ywe_state_normalization_plan', 'artifact_version': '1.0.0'}
    result_header = {'schema_ref': 'data/schemas/m3_state_normalization_schema.json',
                     'artifact_type': 'ywe_state_normalization', 'artifact_version': '1.0.0'}
    notes = ['Independent source-derived value evidence; no operational recovery is asserted.']
    def state(signature):
        return None if signature is None else {'state_space': 'F2^9', 'bits': [int(bit) for bit in signature]}
    def profile(profile_id, recognized, unavailable=False):
        record = {'availability': 'UNAVAILABLE' if unavailable else 'AVAILABLE',
                  'profile_id': profile_id, 'source_binding': source_record(profile_id, recognized)}
        if unavailable:
            record.update(reason_code='PROFILE_DATA_UNAVAILABLE', reason='Declared authoritative profile unavailable.')
        else:
            record['recognized_valid_signatures'] = list(recognized)
        return record
    def diagnostic(signature, recognized, rejected=None, unavailable=False):
        if rejected is not None:
            input_state = {'candidate_kind': 'REJECTED', 'input_evidence': copy.deepcopy(rejected)}
            status, orbit = 'UNCLASSIFIED', None
        elif unavailable:
            input_state, status, orbit = state(signature)['bits'], 'UNCLASSIFIED', None
        else:
            status, _, targets, _, _, orbit_id = expected_case(signature, recognized, words)
            input_state = state(signature)['bits']
            orbit = {'orbit_id': orbit_id, 'member_count': 16, 'contains_known_valid_state': bool(targets)}
        compatibility, normal, relevance, valid = ROWS[status]
        return {'input_state': input_state, 'admissibility_status': status,
                'transformation_compatibility': compatibility, 'normalization_status': normal,
                'recoverability_relevance': relevance, 'is_valid': valid, 'orbit_info': orbit,
                'rule_ids': list(DIAGNOSIS_RULES), 'notes': list(notes)}
    def diagnosis(name, signature, profile_id, recognized, unavailable=False):
        reference = 'n1_authored:' + name
        raw = 'bad' if signature is None else signature
        evidence = {'original_input_reference': reference + ':input', 'representation_kind': 'SIGNATURE',
                    'observed_length': len(raw), 'length_unit': 'CHARACTERS', 'preview': raw,
                    'preview_encoding': 'TEXT', 'truncated': False, 'coordinate_observations': [],
                    'failure_code': 'INPUT_SIGNATURE_INVALID' if signature is None else None}
        diag = diagnostic(signature, recognized, evidence if signature is None else None, unavailable)
        severity, disposition = IMPACT[diag['admissibility_status']]
        detection = {'diagnostic_reference': reference + ':detection', 'envelope': {
            'diagnostic_kind': 'STATE_VALIDITY', 'severity': severity, 'stage': 'DETECTION',
            'disposition': disposition, 'subject_reference': reference + ':input' if signature is None else 'ash_state_' + signature,
            'parent_diagnostic_reference': None, 'chain_root_reference': reference + ':detection',
            'rule_ids': list(DIAGNOSIS_RULES), 'summary': 'Independently authored complete original diagnosis.', 'notes': list(notes)}}
        return {'schema_ref': 'data/schemas/m3_state_assessment_schema.json', 'artifact_type': 'ywe_state_assessment',
                'artifact_version': '1.0.0', 'outcome': 'diagnosis', 'assessment_binding': {
                    'assessment_reference': reference, 'original_input_reference': reference + ':input',
                    'diagnosis_reference': reference + ':detection'},
                'source_binding': copy.deepcopy(source), 'profile_binding': profile(profile_id, recognized, unavailable),
                'input_evidence': evidence, 'parsed_state': state(signature), 'state_validity_diagnostic': diag,
                'emitted_diagnostics': [detection]}
    def plan(name, signature, profile_id, recognized, unavailable=False):
        original = diagnosis(name, signature, profile_id, recognized, unavailable)
        if signature is None or unavailable:
            decision, targets, target, chain = 'BLOCKED', (), None, ()
            reason = 'NORMALIZATION_INPUT_REJECTED' if signature is None else 'NORMALIZATION_PROFILE_UNAVAILABLE'
        else:
            _, outcome, targets, target, chain, _ = expected_case(signature, recognized, words)
            decision = 'PLAN_READY' if outcome == 'NORMALIZED' else outcome
            reason = {'PLAN_READY': 'NORMALIZATION_PLAN_READY', 'ALREADY_VALID': 'NORMALIZATION_ALREADY_VALID',
                      'NOT_NORMALIZABLE': 'NORMALIZATION_NO_TARGET'}[decision]
        return {**plan_header, 'plan_reference': 'n1_authored:' + name + ':plan',
                'evidence_reference': 'n1_authored:' + name + ':proof', 'policy_binding': copy.deepcopy(policy),
                'original_diagnosis': original, 'decision': decision, 'eligible_targets_complete': decision != 'BLOCKED',
                'eligible_targets': [state(s) for s in targets], 'selected_target': state(target),
                'codeword_chain': [state(s) for s in chain], 'reason_code': reason}
    def validation(submitted, expected=None, code=None, field=None, origin='VERIFIED', current_profile=None):
        expected = submitted if expected is None else expected
        evaluated = origin == 'VERIFIED'
        return {'plan': copy.deepcopy(submitted), 'original_diagnosis': copy.deepcopy(submitted['original_diagnosis']),
                'canonical_binding': copy.deepcopy(source),
                'profile_binding': copy.deepcopy(submitted['original_diagnosis']['profile_binding'] if current_profile is None else current_profile),
                'origin_validation_status': origin, 'validation_status': 'VALIDATED' if code is None else 'REJECTED',
                'failure_code': code, 'field_name': field, 'expected_decision': expected['decision'] if evaluated else None,
                'recomputed_eligible_targets': copy.deepcopy(expected['eligible_targets']) if evaluated and expected['decision'] != 'BLOCKED' else None,
                'recomputed_target': copy.deepcopy(expected['selected_target']) if evaluated else None,
                'recomputed_codeword_chain': copy.deepcopy(expected['codeword_chain']) if evaluated and expected['decision'] != 'BLOCKED' else None}
    def record(submitted, context, phase, semantic, step, disposition):
        original = submitted['original_diagnosis']
        inherited = original['emitted_diagnostics'][0]
        severity = max((inherited['envelope']['severity'], IMPACT[semantic['admissibility_status']][0]), key=SEVERITY.__getitem__)
        parent = inherited['diagnostic_reference'] if phase == 'COMPUTATION' else context['computation_reference']
        reference = context['computation_reference'] if phase == 'COMPUTATION' else context['post_validation_reference']
        return {'emission': {'diagnostic_reference': reference, 'envelope': {
                    'diagnostic_kind': 'STATE_VALIDITY', 'severity': severity, 'stage': 'RECOVERY',
                    'disposition': disposition, 'subject_reference': inherited['envelope']['subject_reference'],
                    'parent_diagnostic_reference': parent, 'chain_root_reference': inherited['diagnostic_reference'],
                    'rule_ids': list(DIAGNOSIS_RULES) + ([] if submitted['decision'] == 'BLOCKED' else [CODEWORD_RULE]),
                    'summary': 'Independently authored ' + phase + ' value evidence.', 'notes': copy.deepcopy(semantic['notes'])}},
                'phase': phase, 'state_validity_diagnostic': copy.deepcopy(semantic), 'step': copy.deepcopy(step)}
    def result(submitted):
        reference = submitted['plan_reference'] + ':operation'
        context = {'operation_reference': reference, 'computation_reference': reference + ':computation',
                   'post_validation_reference': reference + ':post'}
        original = submitted['original_diagnosis']
        actual = copy.deepcopy(original['parsed_state'])
        steps, post, normalized = [], None, None
        if submitted['decision'] == 'PLAN_READY':
            actual = copy.deepcopy(submitted['selected_target'])
            steps = [{'step_index': 0, 'input_state': copy.deepcopy(original['parsed_state']),
                      'codeword': copy.deepcopy(submitted['codeword_chain'][0]), 'actual_state': copy.deepcopy(actual)}]
        success = submitted['decision'] in ('PLAN_READY', 'ALREADY_VALID')
        step = steps[0] if steps else None
        computation = record(submitted, context, 'COMPUTATION', original['state_validity_diagnostic'], step,
                             'PENDING' if success else 'BLOCKED')
        emissions = [computation]
        if success:
            signature = ''.join(str(bit) for bit in actual['bits'])
            post = diagnostic(signature, original['profile_binding']['recognized_valid_signatures'])
            emissions.append(record(submitted, context, 'POST_VALIDATION', post, step, 'RESOLVED'))
            normalized = copy.deepcopy(actual)
        packet = {**result_header, 'outcome': 'NORMALIZED' if submitted['decision'] == 'PLAN_READY' else submitted['decision'],
                  'operation_binding': context, 'plan': copy.deepcopy(submitted), 'plan_validation': validation(submitted),
                  'original_diagnosis': copy.deepcopy(original), 'actual_state': actual, 'steps': steps,
                  'post_validity_diagnostic': post, 'normalized_state': normalized,
                  'inherited_diagnostics': copy.deepcopy(original['emitted_diagnostics']), 'emitted_diagnostics': emissions}
        if not success:
            field = 'original_diagnosis.parsed_state' if submitted['reason_code'] == 'NORMALIZATION_INPUT_REJECTED' else 'original_diagnosis.profile_binding' if submitted['decision'] == 'BLOCKED' else 'selected_target'
            packet.update(failure_kind='semantic', failure_code=submitted['reason_code'], failed_field=field)
        return packet
    profiles = declared_profiles()
    plans = [plan('ready', '100011110', 'wrw_reference_profile', profiles['wrw_reference_profile']),
             plan('identity', '100000000', 'wrw_reference_profile', profiles['wrw_reference_profile']),
             plan('empty', '000000000', 'ywe.validation.empty-known-set.v1', ()),
             plan('rejected', None, 'wrw_reference_profile', profiles['wrw_reference_profile']),
             plan('unavailable', '100011110', 'n1_authored:unavailable', (), True),
             plan('multi-identity', '001100110', 'ywe.validation.multi-target-same-orbit.v1', profiles['ywe.validation.multi-target-same-orbit.v1'])]
    packets = copy.deepcopy(plans) + [result(p) for p in plans]
    success = result(plans[0])
    for stage in (0, 1):
        for status in ('REJECTED', 'NOT_CONFIRMED'):
            packet = copy.deepcopy(success)
            packet.update(outcome='FAILURE', failure_kind='diagnostic_capture',
                          failure_code='DIAGNOSTIC_CAPTURE_REJECTED' if status == 'REJECTED' else 'DIAGNOSTIC_CAPTURE_UNCONFIRMED',
                          failed_field='normalization_capture', capture_status=status,
                          normalized_state=None, attempted_diagnostic=copy.deepcopy(success['emitted_diagnostics'][stage]))
            packet['emitted_diagnostics'] = packet['emitted_diagnostics'][:stage]
            if stage == 0: packet['post_validity_diagnostic'] = None
            packets.append(packet)
    begin_failure = copy.deepcopy(packets[-3])
    begin_failure.update(actual_state=copy.deepcopy(plans[0]['original_diagnosis']['parsed_state']), steps=[],
                         post_validity_diagnostic=None, emitted_diagnostics=[])
    begin_failure['attempted_diagnostic'] = record(plans[0], begin_failure['operation_binding'], 'COMPUTATION',
        plans[0]['original_diagnosis']['state_validity_diagnostic'], None, 'BLOCKED')
    packets.append(begin_failure)
    foreign = plan('foreign-origin', '000000000', 'ywe.validation.neutral-origin.v1', ('000000000',))
    early = result(foreign)
    early.update(outcome='FAILURE', failure_kind='plan_validation', failure_code='NORMALIZATION_BINDING_MISMATCH',
                 failed_field='original_diagnosis.profile_binding', steps=[], post_validity_diagnostic=None,
                 normalized_state=None, inherited_diagnostics=[], emitted_diagnostics=[])
    early['plan_validation'] = validation(foreign, code='NORMALIZATION_BINDING_MISMATCH',
        field='original_diagnosis.profile_binding', origin='REJECTED',
        current_profile=profile('wrw_reference_profile', profiles['wrw_reference_profile']))
    packets.append(early)
    wrong_proof = copy.deepcopy(plans[0])
    wrong_proof['codeword_chain'] = [state('001100110')]
    late = copy.deepcopy(success)
    late.update(outcome='FAILURE', failure_kind='plan_validation', failure_code='NORMALIZATION_CODEWORD_MISMATCH',
                failed_field='codeword_chain', plan=wrong_proof, actual_state=copy.deepcopy(wrong_proof['original_diagnosis']['parsed_state']),
                steps=[], post_validity_diagnostic=None, normalized_state=None)
    late['plan_validation'] = validation(wrong_proof, plans[0], 'NORMALIZATION_CODEWORD_MISMATCH', 'codeword_chain')
    late['emitted_diagnostics'] = [record(wrong_proof, late['operation_binding'], 'COMPUTATION',
                                         wrong_proof['original_diagnosis']['state_validity_diagnostic'], None, 'BLOCKED')]
    packets.append(late)
    post_failure = copy.deepcopy(success)
    post_failure.update(outcome='FAILURE', failure_kind='post_validation',
                        failure_code='NORMALIZATION_POST_VALIDATION_FAILED', failed_field='post_validity_diagnostic', normalized_state=None)
    post_failure['post_validity_diagnostic'].update(admissibility_status='TRANSFORMATION_COMPATIBLE',
        transformation_compatibility='COMPATIBLE', normalization_status='NORMALIZABLE',
        recoverability_relevance='RECOVERY_APPLICABLE', is_valid=False)
    post_failure['emitted_diagnostics'][1] = record(plans[0], post_failure['operation_binding'], 'POST_VALIDATION',
        post_failure['post_validity_diagnostic'], post_failure['steps'][0], 'BLOCKED')
    packets.append(post_failure)
    return packets


class CaptureDouble:
    """Observe actual append attempts separately from externally stored and confirmed records."""
    def __init__(self, mode='confirm', stage=0):
        self.mode, self.stage = mode, stage
        self.begins, self.attempts, self.stored = [], [], []

    def begin(self, reference, *, original_diagnosis):
        self.begins.append((reference, original_diagnosis))
        if self.mode == 'begin-throw':
            raise RuntimeError('Private collector detail must not enter a packet')
        if self.mode == 'begin-none': return None
        if self.mode == 'begin-object': return object()
        if self.mode == 'begin-noncallable': return type('MalformedScope', (), {'append': 42})()
        return self

    def append(self, record):
        index = len(self.attempts)
        self.attempts.append(record)
        ref = record.emission.diagnostic_reference
        if index == self.stage:
            if self.mode == 'reject': return sv.CaptureReceipt(ref, 'REJECTED')
            if self.mode == 'throw-before': raise RuntimeError('Private pre-append detail')
            if self.mode == 'missing': return None
            if self.mode == 'wrong-reference': return sv.CaptureReceipt(ref + ':other', 'CONFIRMED')
            if self.mode == 'unconfirmed': return sv.CaptureReceipt(ref, 'NOT_CONFIRMED')
            if self.mode == 'throw-after':
                self.stored.append(record)
                raise RuntimeError('Private post-append detail')
        self.stored.append(record)
        return sv.CaptureReceipt(ref, 'CONFIRMED')


class Hostile:
    calls = []
    def _fail(self, name):
        self.calls.append(name)
        raise AssertionError('Untrusted hook executed: ' + name)
    def __str__(self): return self._fail('str')
    def __repr__(self): return self._fail('repr')
    def __iter__(self): return self._fail('iter')
    def __len__(self): return self._fail('len')
    def __eq__(self, other): return self._fail('eq')
    def __hash__(self): return self._fail('hash')
    def __bool__(self): return self._fail('bool')


class HostileMeta(type):
    calls = []
    def __eq__(cls, other):
        cls.calls.append('metaclass-eq')
        raise AssertionError('Untrusted metaclass equality')
    def __hash__(cls):
        cls.calls.append('metaclass-hash')
        raise AssertionError('Untrusted metaclass hash')


class HostileType(metaclass=HostileMeta):
    pass


class NormalizationTestCase(unittest.TestCase):
    def model(self, profile=None, capture=None):
        return StateModel(profile_binding() if profile is None else profile,
                          sv.CanonicalAshBinding(**canonical_record()), RecordingDiagnosticCapture(),
                          normalization_capture=capture)

    def diagnose(self, model, signature='100011110', reference='n1:assessment'):
        result = model.diagnose(signature, diagnostic_context=diagnostic_context(reference))
        self.assertIs(type(result), sv.StateDiagnosis)
        return result

    def plan(self, model, diagnosis=None, reference='n1:plan'):
        diagnosis = self.diagnose(model) if diagnosis is None else diagnosis
        return model.plan_normalization(diagnosis, plan_reference=reference,
                                       evidence_reference=reference + ':evidence', policy_binding=policy_binding())

    def assert_contract_error(self, operation, code, field=None):
        with self.assertRaises(nv.NormalizationContractError) as caught:
            operation()
        self.assertEqual(code, caught.exception.code)
        if field is not None:
            self.assertEqual(field, caught.exception.field_name)
        self.assertEqual((), caught.exception.emitted_diagnostics)
        return caught.exception

    def assert_origin_witness(self, validation, diagnosis, status, plan):
        self.assertIs(type(validation), nv.NormalizationPlanValidation)
        self.assertEqual(diagnosis, validation.original_diagnosis)
        self.assertEqual(plan, validation.plan)
        self.assertEqual(status, validation.origin_validation_status)
        self.assertEqual('REJECTED', validation.validation_status)
        for field in ('expected_decision', 'recomputed_eligible_targets', 'recomputed_target', 'recomputed_codeword_chain'):
            self.assertIsNone(getattr(validation, field))

    def assert_chain(self, result, expected_new):
        self.assertEqual(result.original_diagnosis, result.plan.original_diagnosis)
        self.assertEqual(result.plan, result.plan_validation.plan)
        self.assertEqual(result.original_diagnosis, result.plan_validation.original_diagnosis)
        self.assertEqual(result.original_diagnosis.emitted_diagnostics, result.inherited_diagnostics)
        self.assertEqual(expected_new, len(result.emitted_diagnostics))
        previous = result.original_diagnosis.emitted_diagnostics[0]
        for index, record in enumerate(result.emitted_diagnostics):
            self.assertIs(type(record), nv.NormalizationDiagnosticRecord)
            envelope = record.emission.envelope
            self.assertEqual('STATE_VALIDITY', envelope.diagnostic_kind)
            self.assertEqual('RECOVERY', envelope.stage)
            self.assertEqual(previous.diagnostic_reference, envelope.parent_diagnostic_reference)
            self.assertEqual(result.original_diagnosis.assessment_binding.diagnosis_reference, envelope.chain_root_reference)
            self.assertEqual(previous.envelope.subject_reference, envelope.subject_reference)
            self.assertGreaterEqual(SEVERITY[envelope.severity], SEVERITY[previous.envelope.severity])
            self.assertEqual('COMPUTATION' if index == 0 else 'POST_VALIDATION', record.phase)
            previous = record.emission
        record = result.to_record()
        self.assertTrue({'system_context', 'system_state_class', 'recovery_category', 'committed_state', 'RECOVERED'}.isdisjoint(record))


class IndependentNormalizationTests(NormalizationTestCase):
    def test_source_generators_policy_and_reviewed_2048_fingerprint(self):
        self.assertEqual(CODEWORD_PIN, normalized_hash(CANONICAL / 'core/codeword-set.pseudo.md'))
        self.assertEqual(POLICY_PIN, normalized_hash(ROOT / 'docs/architecture/m3_normalization_policy.md'))
        words = generator_codewords()
        self.assertEqual(16, len(words))
        rows = []
        for profile_id, recognized in declared_profiles().items():
            for vertex in range(512):
                signature = format(vertex, '09b')
                status, outcome, targets, target, chain, _ = expected_case(signature, recognized, words)
                rows.append([profile_id, signature, status, list(targets), outcome, target, list(chain)])
        self.assertEqual(2048, len(rows))
        self.assertEqual(REVIEWED_ROWS_PIN, hashlib.sha256(json.dumps(rows, separators=(',', ':'), ensure_ascii=True).encode('ascii')).hexdigest())

    def test_all_2048_plans_validations_and_actual_applications(self):
        words = generator_codewords()
        counts = {}
        for profile_id, recognized in declared_profiles().items():
            model = self.model(profile_binding(profile_id, recognized), normalization.RecordingNormalizationCapture())
            outcomes = collections.Counter()
            for vertex in range(512):
                signature = format(vertex, '09b')
                with self.subTest(profile=profile_id, state=signature):
                    status, outcome, targets, target, chain, orbit_id = expected_case(signature, recognized, words)
                    diagnosis = self.diagnose(model, signature, profile_id + ':' + signature)
                    before = copy.deepcopy(diagnosis.to_record())
                    self.assertEqual(status, diagnosis.state_validity_diagnostic.admissibility_status)
                    self.assertEqual(orbit_id, diagnosis.state_validity_diagnostic.orbit_info.orbit_id)
                    plan = self.plan(model, diagnosis, profile_id + ':' + signature + ':plan')
                    self.assertEqual('PLAN_READY' if outcome == 'NORMALIZED' else outcome, plan.decision)
                    self.assertIs(True, plan.eligible_targets_complete)
                    self.assertEqual(targets, tuple(state.signature for state in plan.eligible_targets))
                    self.assertEqual(target, None if plan.selected_target is None else plan.selected_target.signature)
                    self.assertEqual(chain, tuple(state.signature for state in plan.codeword_chain))
                    validation = model.validate_normalization_plan(plan)
                    self.assertEqual('VERIFIED', validation.origin_validation_status)
                    self.assertEqual('VALIDATED', validation.validation_status)
                    self.assertEqual(targets, tuple(state.signature for state in validation.recomputed_eligible_targets))
                    self.assertEqual(plan, validation.plan)
                    result = model.apply_normalization(plan, normalization_context=operation_context(profile_id + ':' + signature + ':operation'))
                    outcomes[result.outcome] += 1
                    self.assertEqual(outcome, result.outcome)
                    self.assertEqual(before, diagnosis.to_record())
                    if outcome == 'NOT_NORMALIZABLE':
                        self.assertIs(type(result), nv.NormalizationFailure)
                        self.assertEqual('semantic', result.failure_kind)
                        self.assertEqual('NORMALIZATION_NO_TARGET', result.failure_code)
                        self.assertEqual(ash(signature), result.actual_state)
                        self.assertEqual((), result.steps)
                        self.assertIsNone(result.normalized_state)
                        self.assertIsNone(result.post_validity_diagnostic)
                        self.assert_chain(result, 1)
                    else:
                        self.assertIs(type(result), nv.NormalizationResult)
                        self.assertEqual(ash(target), result.actual_state)
                        self.assertEqual(ash(target), result.normalized_state)
                        self.assertEqual('VALID', result.post_validity_diagnostic.admissibility_status)
                        self.assertEqual(len(chain), len(result.steps))
                        if chain:
                            step = result.steps[0]
                            self.assertEqual(0, step.step_index)
                            self.assertEqual(ash(signature), step.input_state)
                            self.assertEqual(ash(chain[0]), step.codeword)
                            self.assertEqual(ash(target), step.actual_state)
                        self.assert_chain(result, 2)
            counts[profile_id] = [outcomes['ALREADY_VALID'], outcomes['NORMALIZED'], outcomes['NOT_NORMALIZABLE']]
        self.assertEqual([[9, 135, 368], [1, 15, 496], [0, 0, 512], [3, 13, 496]], list(counts.values()))

    def test_identity_first_retains_every_target_including_all_sixteen(self):
        recognized = tuple(format(word, '09b') for word in generator_codewords())
        model = self.model(profile_binding('n1:all16', recognized), normalization.RecordingNormalizationCapture())
        for signature in recognized:
            plan = self.plan(model, self.diagnose(model, signature, 'n1:all16:' + signature), 'n1:all16:' + signature + ':plan')
            self.assertEqual(recognized, tuple(state.signature for state in plan.eligible_targets))
            self.assertEqual(ash(signature), plan.selected_target)
            self.assertEqual((), plan.codeword_chain)
            result = model.apply_normalization(plan, normalization_context=operation_context('n1:all16:' + signature + ':operation'))
            self.assertEqual('ALREADY_VALID', result.outcome)
            self.assertEqual((), result.steps)
            self.assertEqual(ash(signature), result.normalized_state)

    def test_pure_planning_and_validation_work_without_capture_then_apply_refuses(self):
        model = self.model()
        plan = self.plan(model)
        validation = model.validate_normalization_plan(plan)
        self.assertEqual('VALIDATED', validation.validation_status)
        error = self.assert_contract_error(lambda: model.apply_normalization(plan, normalization_context=operation_context()),
                                           'NORMALIZATION_CONFIG_INVALID', 'normalization_capture')
        self.assertEqual(plan, error.submitted_plan)
        self.assert_origin_witness(error.validation, plan.original_diagnosis, 'NOT_EVALUATED', plan)

    def test_unavailable_and_rejected_branches_preserve_full_original_diagnosis(self):
        source = sv.ProfileSourceBinding('tests/test_m3_normalization.py:unavailable', '0' * 64, 'n1:unavailable:evidence')
        unavailable = sv.UnavailableProfileBinding(sv.UnavailableValidityProfileEvidence(
            'n1:unavailable', source, 'PROFILE_DATA_UNAVAILABLE', 'Authoritative profile unavailable.'))
        for profile, candidate, failure in [(unavailable, '100011110', 'NORMALIZATION_PROFILE_UNAVAILABLE'),
                                             (profile_binding(), 'bad', 'NORMALIZATION_INPUT_REJECTED')]:
            with self.subTest(failure=failure):
                model = self.model(profile, normalization.RecordingNormalizationCapture())
                diagnosis = self.diagnose(model, candidate)
                before = diagnosis.to_record()
                plan = self.plan(model, diagnosis)
                self.assertEqual('BLOCKED', plan.decision)
                self.assertIs(False, plan.eligible_targets_complete)
                self.assertEqual((), plan.eligible_targets)
                validation = model.validate_normalization_plan(plan)
                self.assertIsNone(validation.recomputed_eligible_targets)
                self.assertEqual('VERIFIED', validation.origin_validation_status)
                result = model.apply_normalization(plan, normalization_context=operation_context())
                self.assertEqual('BLOCKED', result.outcome)
                self.assertEqual(failure, result.failure_code)
                self.assertEqual(diagnosis.parsed_state, result.actual_state)
                self.assertEqual(before, result.original_diagnosis.to_record())
                self.assertEqual((), result.steps)
                self.assert_chain(result, 1)


class NormalizationProvenanceTests(NormalizationTestCase):
    def test_real_foreign_profile_planning_refusal_has_rejected_origin_without_plan(self):
        collector = CaptureDouble()
        foreign = self.model(profile_binding('ywe.validation.neutral-origin.v1', ('000000000',)))
        diagnosis = self.diagnose(foreign, '000000000', 'n1:foreign')
        model = self.model(capture=collector)
        error = self.assert_contract_error(lambda: self.plan(model, diagnosis), 'NORMALIZATION_PLAN_INVALID',
                                           'original_diagnosis.profile_binding')
        self.assertIsNone(error.submitted_plan)
        self.assert_origin_witness(error.validation, diagnosis, 'REJECTED', None)
        self.assertEqual('NORMALIZATION_BINDING_MISMATCH', error.validation.failure_code)
        self.assertEqual(model.canonical_binding, error.validation.canonical_binding)
        self.assertEqual(model.profile_binding, error.validation.profile_binding)
        self.assertNotEqual(diagnosis.profile_binding, error.validation.profile_binding)
        self.assertEqual([], collector.begins)
        self.assertEqual([], collector.attempts)

    def test_same_profile_id_and_source_hash_with_substituted_known_set_is_rejected(self):
        collector = CaptureDouble()
        original_profile = profile_binding()
        altered = profile_binding(original_profile.profile_id, ('100000000',), source=original_profile.source_binding)
        original_model = self.model(original_profile)
        plan = self.plan(original_model)
        other_model = self.model(altered, collector)
        witness = other_model.validate_normalization_plan(plan)
        self.assert_origin_witness(witness, plan.original_diagnosis, 'REJECTED', plan)
        self.assertEqual('NORMALIZATION_BINDING_MISMATCH', witness.failure_code)
        self.assertEqual('original_diagnosis.profile_binding', witness.field_name)
        with mock.patch.object(normalization._NormalizationOperations, '_apply_codeword') as apply:
            result = other_model.apply_normalization(plan, normalization_context=operation_context())
        apply.assert_not_called()
        self.assertEqual('plan_validation', result.failure_kind)
        self.assertEqual((), result.inherited_diagnostics)
        self.assertEqual((), result.emitted_diagnostics)
        self.assertEqual(plan.original_diagnosis, result.original_diagnosis)
        self.assertEqual(ash('100011110'), result.actual_state)
        self.assertEqual([], collector.begins)

    def test_all_nine_source_pin_substitutions_refuse_without_capture(self):
        for field in canonical_record():
            with self.subTest(field=field):
                collector = CaptureDouble()
                model = self.model(capture=collector)
                diagnosis = self.diagnose(model)
                bad_binding = sv.CanonicalAshBinding(**canonical_record())
                object.__setattr__(bad_binding, field, 'foreign.dependency' if field == 'dependency_id' else '0' * 64)
                bad_diagnosis = dataclasses.replace(diagnosis, source_binding=bad_binding)
                error = self.assert_contract_error(lambda: self.plan(model, bad_diagnosis), 'NORMALIZATION_PLAN_INVALID',
                                                   'original_diagnosis.source_binding')
                self.assert_origin_witness(error.validation, bad_diagnosis, 'REJECTED', None)
                self.assertEqual('NORMALIZATION_BINDING_MISMATCH', error.validation.failure_code)
                self.assertEqual([], collector.begins)

    def test_forged_validity_row_and_orbit_are_recomputed_before_capture(self):
        for corruption in ('valid-row', 'orbit-id'):
            with self.subTest(corruption=corruption):
                collector = CaptureDouble()
                model = self.model(capture=collector)
                diagnosis = self.diagnose(model)
                diagnostic = diagnosis.state_validity_diagnostic
                if corruption == 'valid-row':
                    altered = dataclasses.replace(diagnostic, admissibility_status='VALID',
                        transformation_compatibility='COMPATIBLE', normalization_status='ALREADY_VALID',
                        recoverability_relevance='NO_RECOVERY_NEEDED', is_valid=True)
                    emission = dataclasses.replace(diagnosis.emitted_diagnostics[0], envelope=dataclasses.replace(
                        diagnosis.emitted_diagnostics[0].envelope, severity='INFO', disposition='RESOLVED'))
                else:
                    altered = dataclasses.replace(diagnostic, orbit_info=sv.OrbitInfo('000000000', 16, True))
                    emission = diagnosis.emitted_diagnostics[0]
                bad = dataclasses.replace(diagnosis, state_validity_diagnostic=altered, emitted_diagnostics=(emission,))
                error = self.assert_contract_error(lambda: self.plan(model, bad), 'NORMALIZATION_PLAN_INVALID',
                                                   'original_diagnosis.state_validity_diagnostic')
                self.assert_origin_witness(error.validation, bad, 'REJECTED', None)
                self.assertEqual('NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH', error.validation.failure_code)
                self.assertEqual([], collector.begins)

    def test_origin_requires_rule_coverage_and_coherent_impact_and_notes(self):
        model = self.model()
        diagnosis = self.diagnose(model)
        envelope = diagnosis.emitted_diagnostics[0].envelope
        cases = [
            ('rule-coverage', dataclasses.replace(diagnosis, state_validity_diagnostic=dataclasses.replace(
                diagnosis.state_validity_diagnostic, rule_ids=(DIAGNOSIS_RULES[0], DIAGNOSIS_RULES[2]))),
             'original_diagnosis.state_validity_diagnostic'),
        ]
        for name, changes in [('severity', {'severity': 'ERROR'}), ('disposition', {'disposition': 'BLOCKED'}),
                               ('rules', {'rule_ids': (DIAGNOSIS_RULES[0],)}), ('notes', {'notes': ('Other evidence.',)})]:
            cases.append((name, dataclasses.replace(diagnosis, emitted_diagnostics=(dataclasses.replace(
                diagnosis.emitted_diagnostics[0], envelope=dataclasses.replace(envelope, **changes)),)),
                'original_diagnosis.emitted_diagnostics'))
        for name, bad, field in cases:
            with self.subTest(case=name):
                error = self.assert_contract_error(lambda: self.plan(model, bad), 'NORMALIZATION_PLAN_INVALID', field)
                self.assertEqual('NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH', error.validation.failure_code)

    def test_owned_explanatory_text_is_preserved_without_template_equality(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        diagnosis = self.diagnose(model)
        notes = ('Independent bounded explanation; the seven semantic fields remain authoritative.',)
        diagnostic = dataclasses.replace(diagnosis.state_validity_diagnostic, notes=notes)
        envelope = dataclasses.replace(diagnosis.emitted_diagnostics[0].envelope, notes=notes,
                                       summary='Independent producer wording for this complete diagnosis.')
        diagnosis = dataclasses.replace(diagnosis, state_validity_diagnostic=diagnostic,
                                        emitted_diagnostics=(dataclasses.replace(diagnosis.emitted_diagnostics[0], envelope=envelope),))
        plan = self.plan(model, diagnosis)
        self.assertEqual('VALIDATED', model.validate_normalization_plan(plan).validation_status)
        result = model.apply_normalization(plan, normalization_context=operation_context())
        self.assertEqual('NORMALIZED', result.outcome)
        self.assertEqual(notes, result.original_diagnosis.state_validity_diagnostic.notes)
        self.assertEqual(envelope.summary, result.inherited_diagnostics[0].envelope.summary)

    def test_omitted_targets_wrong_choice_and_wrong_canonical_proof_are_retained(self):
        recognized = declared_profiles()['ywe.validation.multi-target-same-orbit.v1']
        for corruption, code, field in [('targets', 'NORMALIZATION_TARGET_SET_MISMATCH', 'eligible_targets'),
                                         ('selection', 'NORMALIZATION_SELECTION_MISMATCH', 'selected_target'),
                                         ('proof', 'NORMALIZATION_CODEWORD_MISMATCH', 'codeword_chain')]:
            with self.subTest(corruption=corruption):
                collector = CaptureDouble()
                model = self.model(profile_binding('n1:multi', recognized), collector)
                diagnosis = self.diagnose(model, '111100000')
                plan = self.plan(model, diagnosis)
                if corruption == 'targets':
                    bad = dataclasses.replace(plan, eligible_targets=plan.eligible_targets[:1])
                elif corruption == 'selection':
                    bad = dataclasses.replace(plan, selected_target=plan.eligible_targets[-1])
                else:
                    bad = dataclasses.replace(plan, codeword_chain=(ash('000011110'),))
                witness = model.validate_normalization_plan(bad)
                self.assertEqual('VERIFIED', witness.origin_validation_status)
                self.assertEqual('REJECTED', witness.validation_status)
                self.assertEqual(code, witness.failure_code)
                self.assertEqual(field, witness.field_name)
                self.assertEqual(plan.eligible_targets, witness.recomputed_eligible_targets)
                self.assertEqual(plan.selected_target, witness.recomputed_target)
                self.assertEqual(plan.codeword_chain, witness.recomputed_codeword_chain)
                with mock.patch.object(normalization._NormalizationOperations, '_apply_codeword') as apply:
                    result = model.apply_normalization(bad, normalization_context=operation_context())
                apply.assert_not_called()
                self.assertEqual(bad, result.plan)
                self.assertEqual(code, result.failure_code)
                self.assertEqual('plan_validation', result.failure_kind)
                self.assertEqual((), result.steps)
                self.assertIsNone(result.normalized_state)
                self.assert_chain(result, 1)
                self.assertEqual(1, len(collector.attempts))

    def test_apply_revalidates_after_prior_successful_validation(self):
        collector = CaptureDouble()
        model = self.model(capture=collector)
        plan = self.plan(model)
        self.assertEqual('VALIDATED', model.validate_normalization_plan(plan).validation_status)
        # Deliberate hostile bypass of a frozen value; a prior witness is not use-time authority.
        object.__setattr__(plan, 'codeword_chain', (ash('001100110'),))
        with mock.patch.object(normalization._NormalizationOperations, '_apply_codeword') as apply:
            result = model.apply_normalization(plan, normalization_context=operation_context())
        apply.assert_not_called()
        self.assertEqual('NORMALIZATION_CODEWORD_MISMATCH', result.failure_code)
        self.assertEqual('REJECTED', result.plan_validation.validation_status)
        self.assertEqual((), result.steps)
        self.assert_chain(result, 1)

    def test_preplanning_policy_and_reference_errors_are_unevaluated(self):
        model = self.model()
        diagnosis = self.diagnose(model)
        for field, kwargs, code in [('policy_binding', {'policy_binding': None}, 'NORMALIZATION_POLICY_INVALID'),
                                    ('plan_reference', {'plan_reference': 'bad\n'}, 'NORMALIZATION_PLAN_INVALID'),
                                    ('evidence_reference', {'evidence_reference': 'SELF'}, 'NORMALIZATION_PLAN_INVALID')]:
            with self.subTest(field=field):
                inputs = dict(plan_reference='n1:plan', evidence_reference='n1:evidence', policy_binding=policy_binding())
                inputs.update(kwargs)
                error = self.assert_contract_error(lambda: model.plan_normalization(diagnosis, **inputs), code, field)
                self.assert_origin_witness(error.validation, diagnosis, 'NOT_EVALUATED', None)
                self.assertEqual(code, error.validation.failure_code)


class NormalizationCaptureTests(NormalizationTestCase):
    def test_all_begin_failures_are_before_xor_and_retain_complete_blocked_record(self):
        for mode in ('begin-throw', 'begin-none', 'begin-object', 'begin-noncallable'):
            with self.subTest(mode=mode):
                collector = CaptureDouble(mode)
                model = self.model(capture=collector)
                plan = self.plan(model)
                with mock.patch.object(normalization._NormalizationOperations, '_apply_codeword') as apply:
                    result = model.apply_normalization(plan, normalization_context=operation_context())
                apply.assert_not_called()
                self.assertIs(type(result), nv.NormalizationCaptureFailure)
                self.assertEqual('NOT_CONFIRMED', result.capture_status)
                self.assertEqual('DIAGNOSTIC_CAPTURE_UNCONFIRMED', result.failure_code)
                self.assertEqual(ash('100011110'), result.actual_state)
                self.assertEqual((), result.steps)
                self.assertIsNone(result.normalized_state)
                self.assertIsNone(result.post_validity_diagnostic)
                self.assertEqual((), result.emitted_diagnostics)
                self.assertEqual(plan.original_diagnosis.emitted_diagnostics, result.inherited_diagnostics)
                attempted = result.attempted_diagnostic
                self.assertEqual('COMPUTATION', attempted.phase)
                self.assertIsNone(attempted.step)
                self.assertEqual('BLOCKED', attempted.emission.envelope.disposition)
                self.assertEqual(plan.original_diagnosis.state_validity_diagnostic, attempted.state_validity_diagnostic)
                self.assertEqual([], collector.attempts)
                self.assertNotIn('Private collector detail', json.dumps(result.to_record()))

    def test_each_append_failure_preserves_actual_result_and_only_confirmed_prefix(self):
        for stage in (0, 1):
            for mode in ('reject', 'throw-before', 'throw-after', 'missing', 'wrong-reference', 'unconfirmed'):
                with self.subTest(stage=stage, mode=mode):
                    collector = CaptureDouble(mode, stage)
                    model = self.model(capture=collector)
                    plan = self.plan(model)
                    result = model.apply_normalization(plan, normalization_context=operation_context())
                    self.assertIs(type(result), nv.NormalizationCaptureFailure)
                    status = 'REJECTED' if mode == 'reject' else 'NOT_CONFIRMED'
                    self.assertEqual(status, result.capture_status)
                    self.assertEqual('DIAGNOSTIC_CAPTURE_REJECTED' if mode == 'reject' else 'DIAGNOSTIC_CAPTURE_UNCONFIRMED', result.failure_code)
                    self.assertEqual(ash('100000000'), result.actual_state)
                    self.assertEqual(1, len(result.steps))
                    self.assertEqual(ash('000011110'), result.steps[0].codeword)
                    self.assertIsNone(result.normalized_state)
                    self.assertEqual(stage, len(result.emitted_diagnostics))
                    self.assertEqual(tuple(collector.attempts[:stage]), result.emitted_diagnostics)
                    self.assertEqual(collector.attempts[stage], result.attempted_diagnostic)
                    self.assertEqual(stage + 1, len(collector.attempts))
                    self.assertEqual('COMPUTATION' if stage == 0 else 'POST_VALIDATION', result.attempted_diagnostic.phase)
                    self.assertEqual(stage + (mode == 'throw-after'), len(collector.stored))
                    if stage == 0: self.assertIsNone(result.post_validity_diagnostic)
                    else: self.assertEqual('VALID', result.post_validity_diagnostic.admissibility_status)
                    self.assertNotIn('Private', json.dumps(result.to_record()))

    def test_computation_is_acknowledged_before_actual_post_diagnosis(self):
        collector = CaptureDouble()
        model = self.model(capture=collector)
        plan = self.plan(model)
        diagnose = model._diagnose
        observations = []
        def inspect(decoded):
            observations.append((decoded.state, tuple(record.phase for record in collector.stored)))
            return diagnose(decoded)
        with mock.patch.object(model, '_diagnose', side_effect=inspect):
            result = model.apply_normalization(plan, normalization_context=operation_context())
        self.assertEqual([(ash('100011110'), ()), (ash('100000000'), ('COMPUTATION',))], observations)
        self.assertEqual('NORMALIZED', result.outcome)
        self.assertEqual(['COMPUTATION', 'POST_VALIDATION'], [record.phase for record in collector.stored])
        self.assertEqual(1, len(collector.begins))

    def test_post_validation_failure_retains_actual_step_and_both_acknowledgements(self):
        collector = CaptureDouble()
        model = self.model(capture=collector)
        plan = self.plan(model)
        diagnose = model._diagnose
        def wrong_post(decoded):
            diagnostic = diagnose(decoded)
            if decoded.state == ash('100000000'):
                return dataclasses.replace(diagnostic, admissibility_status='TRANSFORMATION_COMPATIBLE',
                    transformation_compatibility='COMPATIBLE', normalization_status='NORMALIZABLE',
                    recoverability_relevance='RECOVERY_APPLICABLE', is_valid=False)
            return diagnostic
        with mock.patch.object(model, '_diagnose', side_effect=wrong_post):
            result = model.apply_normalization(plan, normalization_context=operation_context())
        self.assertIs(type(result), nv.NormalizationFailure)
        self.assertEqual('post_validation', result.failure_kind)
        self.assertEqual('NORMALIZATION_POST_VALIDATION_FAILED', result.failure_code)
        self.assertEqual(ash('100000000'), result.actual_state)
        self.assertEqual(1, len(result.steps))
        self.assertIsNone(result.normalized_state)
        self.assertEqual('TRANSFORMATION_COMPATIBLE', result.post_validity_diagnostic.admissibility_status)
        self.assert_chain(result, 2)

    def test_reference_recording_scope_is_per_operation_and_guards_order_and_replay(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        plan = self.plan(model)
        result = model.apply_normalization(plan, normalization_context=operation_context())
        capture = normalization.RecordingNormalizationCapture()
        first = capture.begin('n1:first', original_diagnosis=plan.original_diagnosis)
        second = capture.begin('n1:second', original_diagnosis=plan.original_diagnosis)
        computation, post = result.emitted_diagnostics
        self.assertEqual('REJECTED', first.append(post).status)
        self.assertEqual('CONFIRMED', first.append(computation).status)
        self.assertEqual('REJECTED', first.append(computation).status)
        self.assertEqual('CONFIRMED', second.append(computation).status)
        self.assertEqual('CONFIRMED', first.append(post).status)
        self.assertEqual('REJECTED', first.append(post).status)
        self.assertEqual('CONFIRMED', second.append(post).status)

    def test_reference_scope_cannot_append_post_after_a_real_semantic_refusal(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        refusal = model.apply_normalization(self.plan(model, self.diagnose(model, '000000000')),
                                            normalization_context=operation_context())
        original = refusal.original_diagnosis
        previous = refusal.emitted_diagnostics[0].emission
        post = nv.NormalizationDiagnosticRecord(sv.DiagnosticEmission('n1:operation:post', sv.DiagnosticEnvelope(
            'STATE_VALIDITY', previous.envelope.severity, 'RECOVERY', 'BLOCKED', original.subject_reference,
            previous.diagnostic_reference, original.assessment_binding.diagnosis_reference, DIAGNOSIS_RULES,
            'This post follows a blocked refusal and cannot be appended.', original.state_validity_diagnostic.notes)),
            'POST_VALIDATION', original.state_validity_diagnostic, None)
        scope = normalization.RecordingNormalizationCapture().begin('n1:scope', original_diagnosis=original)
        self.assertEqual('CONFIRMED', scope.append(refusal.emitted_diagnostics[0]).status)
        self.assertEqual(1, len(scope._records))
        self.assertEqual('REJECTED', scope.append(post).status)
        self.assertEqual(1, len(scope._records))
        self.assertEqual([refusal.emitted_diagnostics[0]], scope._records)

    def test_reference_scope_rejects_resolved_computation_and_pending_post(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        result = model.apply_normalization(self.plan(model), normalization_context=operation_context())
        computation, post = result.emitted_diagnostics
        scope = normalization.RecordingNormalizationCapture().begin('n1:scope', original_diagnosis=result.original_diagnosis)
        resolved = dataclasses.replace(computation, emission=dataclasses.replace(computation.emission,
            envelope=dataclasses.replace(computation.emission.envelope, disposition='RESOLVED')))
        self.assertEqual('REJECTED', scope.append(resolved).status)
        self.assertEqual([], scope._records)
        self.assertEqual('CONFIRMED', scope.append(computation).status)
        pending = dataclasses.replace(post, emission=dataclasses.replace(post.emission,
            envelope=dataclasses.replace(post.emission.envelope, disposition='PENDING')))
        self.assertEqual('REJECTED', scope.append(pending).status)
        self.assertEqual([computation], scope._records)
        self.assertEqual('CONFIRMED', scope.append(post).status)


class NormalizationValueTests(NormalizationTestCase):
    def test_exact_owned_constructor_fields_and_fixed_capture_discriminators(self):
        expected = {
            nv.NormalizationPolicyBinding: ('policy_id', 'policy_version', 'source_reference', 'source_sha256'),
            nv.NormalizationPlan: PLAN_FIELDS, nv.NormalizationPlanValidation: VALIDATION_FIELDS,
            nv.NormalizationContext: ('operation_reference', 'computation_reference', 'post_validation_reference'),
            nv.NormalizationStep: ('step_index', 'input_state', 'codeword', 'actual_state'),
            nv.NormalizationDiagnosticRecord: ('emission', 'phase', 'state_validity_diagnostic', 'step'),
            nv.NormalizationResult: COMMON_FIELDS,
            nv.NormalizationFailure: COMMON_FIELDS + ('failure_kind', 'failure_code', 'failed_field'),
            nv.NormalizationCaptureFailure: COMMON_FIELDS[1:] + ('failure_code', 'failed_field', 'capture_status', 'attempted_diagnostic'),
        }
        for cls, fields in expected.items():
            with self.subTest(cls=cls.__name__):
                self.assertEqual(fields, tuple(field.name for field in dataclasses.fields(cls)))
        self.assertEqual('FAILURE', nv.NormalizationCaptureFailure.outcome)
        self.assertEqual('diagnostic_capture', nv.NormalizationCaptureFailure.failure_kind)
        self.assertEqual(4, len(nv.CONTRACT_CODES))
        self.assertEqual(62, len(nv.FIELD_NAMES))
        self.assertTrue({'decision', 'plan_validation'}.issubset(nv.FIELD_NAMES))

    def test_policy_rejects_every_substituted_pin_with_exact_field(self):
        kwargs = dict(policy_id='YWE-NORMALIZE-LEXICOGRAPHIC-001', policy_version='1.0.0',
                      source_reference='docs/architecture/m3_normalization_policy.md', source_sha256=POLICY_PIN)
        for field in kwargs:
            with self.subTest(field=field):
                altered = dict(kwargs)
                altered[field] = '0' * 64 if field == 'source_sha256' else 'other'
                self.assert_contract_error(lambda: nv.NormalizationPolicyBinding(**altered),
                                           'NORMALIZATION_POLICY_INVALID', 'policy_binding.' + field)
        self.assertEqual(kwargs, dict(nv.NORMALIZATION_POLICY_BINDING_FIELDS))

    def test_reference_bounds_reserved_tokens_and_permitted_operation_aliases(self):
        for good in ('a', 'a' * 256, 'n1:ref/path-0.1'):
            context = nv.NormalizationContext(good, good + ':c' if len(good) < 250 else 'c', 'p')
            self.assertEqual(good, context.operation_reference)
        for bad in ('', 'a' * 257, 'NONE', 'SELF', 'bad\n', 'é', 'a b', 'x\x00'):
            with self.subTest(reference=bad):
                self.assert_contract_error(lambda: nv.NormalizationContext(bad, 'n1:comp', 'n1:post'),
                                           'NORMALIZATION_CONTEXT_INVALID', 'operation_reference')
        self.assert_contract_error(lambda: nv.NormalizationContext('n1:op', 'n1:same', 'n1:same'),
                                   'NORMALIZATION_CONTEXT_INVALID', 'normalization_context')
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        plan = self.plan(model)
        root = plan.original_diagnosis.assessment_binding.diagnosis_reference
        for operation in ('n1:c', 'n1:p', root):
            result = model.apply_normalization(plan, normalization_context=nv.NormalizationContext(operation, 'n1:c', 'n1:p'))
            self.assertEqual('NORMALIZED', result.outcome)
        for field in ('computation_reference', 'post_validation_reference'):
            kwargs = dict(operation_reference='n1:op', computation_reference='n1:c', post_validation_reference='n1:p')
            kwargs[field] = root
            self.assert_contract_error(lambda: model.apply_normalization(plan, normalization_context=nv.NormalizationContext(**kwargs)),
                                       'NORMALIZATION_CONTEXT_INVALID', field)

    def test_plan_bounds_sorted_unique_copied_arrays_and_fresh_record_containers(self):
        model = self.model()
        original = self.plan(model)
        targets, chain = list(original.eligible_targets), list(original.codeword_chain)
        plan = dataclasses.replace(original, eligible_targets=targets, codeword_chain=chain)
        targets.clear(); chain.clear()
        self.assertEqual(original, plan)
        self.assertIs(type(plan.eligible_targets), tuple)
        self.assertIs(type(plan.codeword_chain), tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError): plan.decision = 'BLOCKED'
        wire = plan.to_record()
        wire['eligible_targets'][0]['bits'][0] = 0
        wire['original_diagnosis']['parsed_state']['bits'][0] = 0
        wire['codeword_chain'].clear()
        self.assertEqual(original, plan)
        self.assertEqual(1, len(plan.to_record()['codeword_chain']))
        invalid = [({'eligible_targets': list(original.eligible_targets) * 17}, 'eligible_targets'),
                   ({'eligible_targets': list(original.eligible_targets) * 2}, 'eligible_targets'),
                   ({'eligible_targets': [ash('100000000'), ash('000000000')]}, 'eligible_targets'),
                   ({'eligible_targets': set(original.eligible_targets)}, 'eligible_targets'),
                   ({'eligible_targets': [object()]}, 'eligible_targets'),
                   ({'codeword_chain': list(original.codeword_chain) * 2}, 'codeword_chain'),
                   ({'codeword_chain': [ash('000000001')]}, 'codeword_chain'),
                   ({'eligible_targets_complete': 1}, 'eligible_targets_complete'),
                   ({'decision': 'RECOVERED'}, 'decision'),
                   ({'reason_code': 'NORMALIZATION_NO_TARGET'}, 'reason_code')]
        for changes, field in invalid:
            with self.subTest(field=field, kind=type(next(iter(changes.values()))).__name__):
                self.assert_contract_error(lambda: dataclasses.replace(original, **changes), 'NORMALIZATION_PLAN_INVALID', field)

    def test_structurally_owned_wrong_identity_target_is_rejected_by_math_owner(self):
        recognized = declared_profiles()['ywe.validation.multi-target-same-orbit.v1']
        model = self.model(profile_binding('n1:identity', recognized), normalization.RecordingNormalizationCapture())
        plan = self.plan(model, self.diagnose(model, recognized[-1]))
        bad = dataclasses.replace(plan, selected_target=ash(recognized[0]))
        witness = model.validate_normalization_plan(bad)
        self.assertEqual('NORMALIZATION_SELECTION_MISMATCH', witness.failure_code)
        self.assertEqual(ash(recognized[-1]), witness.recomputed_target)
        result = model.apply_normalization(bad, normalization_context=operation_context())
        self.assertEqual('FAILURE', result.outcome)
        self.assertEqual((), result.steps)
        self.assertIsNone(result.normalized_state)

    def test_step_owns_exact_index_canonical_member_and_actual_xor(self):
        state, code, actual = ash('100011110'), ash('000011110'), ash('100000000')
        step = nv.NormalizationStep(0, state, code, actual)
        self.assertEqual(actual.to_record(), step.to_record()['actual_state'])
        for index in (True, False, 0.0, 1, -1):
            self.assert_contract_error(lambda: nv.NormalizationStep(index, state, code, actual),
                                       'NORMALIZATION_PLAN_INVALID', 'step_index')
        self.assert_contract_error(lambda: nv.NormalizationStep(0, state, ash('000000001'), actual),
                                   'NORMALIZATION_PLAN_INVALID', 'codeword')
        self.assert_contract_error(lambda: nv.NormalizationStep(0, state, code, state),
                                   'NORMALIZATION_PLAN_INVALID', 'actual_state')

    def test_untrusted_conversion_metaclass_and_sequence_hooks_never_execute(self):
        Hostile.calls.clear(); HostileMeta.calls.clear()
        model = self.model()
        plan = self.plan(model)
        for bad in (Hostile(), HostileType()):
            for field in ('eligible_targets', 'codeword_chain', 'selected_target', 'decision', 'original_diagnosis'):
                with self.subTest(field=field, bad_type=type(bad).__name__):
                    self.assert_contract_error(lambda: dataclasses.replace(plan, **{field: bad}), 'NORMALIZATION_PLAN_INVALID', field)
            self.assert_contract_error(lambda: model.plan_normalization(bad, plan_reference='n1:p', evidence_reference='n1:e',
                policy_binding=policy_binding()), 'NORMALIZATION_PLAN_INVALID', 'original_diagnosis')
            self.assert_contract_error(lambda: model.validate_normalization_plan(bad), 'NORMALIZATION_PLAN_INVALID', 'plan')
            self.assert_contract_error(lambda: model.apply_normalization(plan, normalization_context=bad),
                                       'NORMALIZATION_CONTEXT_INVALID', 'normalization_context')
        self.assertEqual([], Hostile.calls)
        self.assertEqual([], HostileMeta.calls)
        class StringSubclass(str): pass
        class ListSubclass(list):
            def __iter__(self): raise AssertionError('Subclass iteration executed')
            def __len__(self): raise AssertionError('Subclass length executed')
        self.assert_contract_error(lambda: dataclasses.replace(plan, decision=StringSubclass('PLAN_READY')),
                                   'NORMALIZATION_PLAN_INVALID', 'decision')
        self.assert_contract_error(lambda: dataclasses.replace(plan, eligible_targets=ListSubclass(plan.eligible_targets)),
                                   'NORMALIZATION_PLAN_INVALID', 'eligible_targets')

    def test_validation_origin_nullability_and_conditional_error_ownership(self):
        model = self.model()
        plan = self.plan(model)
        good = model.validate_normalization_plan(plan)
        for changes in ({'plan': None}, {'original_diagnosis': self.diagnose(model, '100000000', 'n1:other')},
                        {'recomputed_eligible_targets': ()}, {'failure_code': 'NORMALIZATION_CODEWORD_MISMATCH'}):
            with self.assertRaises(nv.NormalizationContractError): dataclasses.replace(good, **changes)
        foreign_model = self.model(profile_binding('n1:foreign-origin', ('000000000',)))
        foreign_diagnosis = self.diagnose(foreign_model, '000000000', 'n1:foreign-origin')
        origin = nv.NormalizationPlanValidation(None, foreign_diagnosis, model.canonical_binding,
            model.profile_binding, 'REJECTED', 'REJECTED', 'NORMALIZATION_BINDING_MISMATCH',
            'original_diagnosis.profile_binding', None, None, None, None)
        error = nv.NormalizationContractError('NORMALIZATION_PLAN_INVALID', origin.field_name, validation=origin)
        self.assertIsNone(error.submitted_plan)
        self.assertEqual(origin, error.validation)
        for kwargs in ({'code': 'NORMALIZATION_CONFIG_INVALID', 'field_name': origin.field_name, 'validation': origin},
                       {'code': 'NORMALIZATION_PLAN_INVALID', 'field_name': 'decision', 'validation': origin},
                       {'code': 'NORMALIZATION_PLAN_INVALID', 'field_name': origin.field_name, 'submitted_plan': plan, 'validation': origin},
                       {'code': 'invented', 'field_name': 'plan'},
                       {'code': 'NORMALIZATION_PLAN_INVALID', 'field_name': 'untrusted.descendant'}):
            with self.assertRaises(ValueError) as caught: nv.NormalizationContractError(**kwargs)
            self.assertIs(type(caught.exception), ValueError)
        with self.assertRaises(nv.NormalizationContractError):
            dataclasses.replace(origin, recomputed_eligible_targets=())
        with self.assertRaises(nv.NormalizationContractError):
            dataclasses.replace(origin, field_name='selected_target')

    def test_named_binding_rejection_requires_an_actual_difference_in_that_binding(self):
        model = self.model()
        diagnosis = self.diagnose(model)
        for field in ('original_diagnosis.source_binding', 'original_diagnosis.profile_binding'):
            with self.subTest(field=field):
                self.assert_contract_error(lambda: nv.NormalizationPlanValidation(None, diagnosis,
                    model.canonical_binding, model.profile_binding, 'REJECTED', 'REJECTED',
                    'NORMALIZATION_BINDING_MISMATCH', field, None, None, None, None),
                    'NORMALIZATION_PLAN_INVALID', 'origin_validation_status')
        foreign = self.model(profile_binding('n1:foreign-origin', ('000000000',)))
        original = self.diagnose(foreign, '000000000')
        # The profile differs; naming the matching canonical source is still false evidence.
        self.assert_contract_error(lambda: nv.NormalizationPlanValidation(None, original,
            model.canonical_binding, model.profile_binding, 'REJECTED', 'REJECTED',
            'NORMALIZATION_BINDING_MISMATCH', 'original_diagnosis.source_binding', None, None, None, None),
            'NORMALIZATION_PLAN_INVALID', 'origin_validation_status')

    def test_result_constructors_retain_owned_arrays_and_refuse_false_success(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        result = model.apply_normalization(self.plan(model), normalization_context=operation_context())
        steps, inherited, emitted = list(result.steps), list(result.inherited_diagnostics), list(result.emitted_diagnostics)
        owned = dataclasses.replace(result, steps=steps, inherited_diagnostics=inherited, emitted_diagnostics=emitted)
        steps.clear(); inherited.clear(); emitted.clear()
        self.assertEqual(result, owned)
        for changes in ({'normalized_state': None}, {'steps': ()}, {'emitted_diagnostics': result.emitted_diagnostics[:1]},
                        {'inherited_diagnostics': ()}, {'post_validity_diagnostic': None}, {'actual_state': ash('000000000')}):
            with self.assertRaises(nv.NormalizationContractError): dataclasses.replace(result, **changes)
        wire = owned.to_record()
        wire['steps'][0]['actual_state']['bits'][0] = 0
        wire['plan_validation']['plan']['eligible_targets'].clear()
        wire['emitted_diagnostics'][0]['emission']['envelope']['notes'].clear()
        self.assertEqual(result, owned)

    def test_semantic_and_proof_refusals_cannot_become_capture_post_prefixes(self):
        for kind in ('semantic', 'proof'):
            with self.subTest(kind=kind):
                model = self.model(capture=normalization.RecordingNormalizationCapture())
                plan = self.plan(model, self.diagnose(model, '000000000' if kind == 'semantic' else '100011110'))
                if kind == 'proof': plan = dataclasses.replace(plan, codeword_chain=(ash('001100110'),))
                refusal = model.apply_normalization(plan, normalization_context=operation_context())
                self.assertEqual(1, len(refusal.emitted_diagnostics))
                original = refusal.original_diagnosis
                previous = refusal.emitted_diagnostics[0].emission
                post = nv.NormalizationDiagnosticRecord(sv.DiagnosticEmission('n1:operation:post', sv.DiagnosticEnvelope(
                    'STATE_VALIDITY', previous.envelope.severity, 'RECOVERY', 'BLOCKED', original.subject_reference,
                    previous.diagnostic_reference, original.assessment_binding.diagnosis_reference,
                    DIAGNOSIS_RULES, 'Fabricated post after a refusal must be rejected.', original.state_validity_diagnostic.notes)),
                    'POST_VALIDATION', original.state_validity_diagnostic, None)
                common = {field: getattr(refusal, field) for field in COMMON_FIELDS[1:]}
                common['post_validity_diagnostic'] = original.state_validity_diagnostic
                self.assert_contract_error(lambda: nv.NormalizationCaptureFailure(**common,
                    failure_code='DIAGNOSTIC_CAPTURE_UNCONFIRMED', failed_field='normalization_capture',
                    capture_status='NOT_CONFIRMED', attempted_diagnostic=post), 'NORMALIZATION_PLAN_INVALID', 'emitted_diagnostics')

    def test_seventh_rule_is_allowed_for_operations_and_rejected_in_assessment_packets(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        diagnosis = self.diagnose(model)
        diagnostic = dataclasses.replace(diagnosis.state_validity_diagnostic, rule_ids=DIAGNOSIS_RULES + (CODEWORD_RULE,))
        with self.assertRaises(sv.StateContractError) as caught:
            dataclasses.replace(diagnosis, state_validity_diagnostic=diagnostic)
        self.assertEqual(('DIAGNOSTIC_ROW_INVALID', 'state_validity_diagnostic.rule_ids'), (caught.exception.code, caught.exception.field_name))
        envelope = dataclasses.replace(diagnosis.emitted_diagnostics[0].envelope, rule_ids=DIAGNOSIS_RULES + (CODEWORD_RULE,))
        emission = dataclasses.replace(diagnosis.emitted_diagnostics[0], envelope=envelope)
        with self.assertRaises(sv.StateContractError) as caught:
            dataclasses.replace(diagnosis, emitted_diagnostics=(emission,))
        self.assertEqual(('DIAGNOSTIC_ENVELOPE_INVALID', 'emitted_diagnostics'), (caught.exception.code, caught.exception.field_name))
        common = {field.name: getattr(diagnosis, field.name) for field in dataclasses.fields(diagnosis)}
        common['emitted_diagnostics'] = ()
        with self.assertRaises(sv.StateContractError) as caught:
            sv.DiagnosticCaptureFailure(**common, failure_code='DIAGNOSTIC_CAPTURE_UNCONFIRMED', capture_status='NOT_CONFIRMED',
                attempted_diagnostic=emission, system_context=None, classification_evidence=None)
        self.assertEqual(('DIAGNOSTIC_ENVELOPE_INVALID', 'emitted_diagnostics'), (caught.exception.code, caught.exception.field_name))
        result = model.apply_normalization(self.plan(model, diagnosis), normalization_context=operation_context())
        self.assertIn(CODEWORD_RULE, result.emitted_diagnostics[0].emission.envelope.rule_ids)
        self.assertNotIn(CODEWORD_RULE, result.emitted_diagnostics[0].state_validity_diagnostic.rule_ids)

    def test_recovery_rule_cannot_broaden_any_normalization_record_boundary(self):
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        result = model.apply_normalization(self.plan(model), normalization_context=operation_context())
        record = result.emitted_diagnostics[0]
        envelope = dataclasses.replace(record.emission.envelope,
            rule_ids=record.emission.envelope.rule_ids + ('ASH-FALLBACK-SELECTION-001',))
        emission = dataclasses.replace(record.emission, envelope=envelope)
        self.assert_contract_error(lambda: dataclasses.replace(record, emission=emission),
            'NORMALIZATION_PLAN_INVALID', 'emission.envelope.rule_ids')
        substituted = copy.deepcopy(record)
        object.__setattr__(substituted, 'emission', emission)
        self.assert_contract_error(lambda: dataclasses.replace(result,
            emitted_diagnostics=(substituted, result.emitted_diagnostics[1])),
            'NORMALIZATION_PLAN_INVALID', 'emission.envelope.rule_ids')
        rejected_model = self.model(capture=CaptureDouble('reject', 0))
        rejected = rejected_model.apply_normalization(self.plan(rejected_model),
            normalization_context=operation_context())
        self.assert_contract_error(lambda: dataclasses.replace(rejected,
            attempted_diagnostic=substituted), 'NORMALIZATION_PLAN_INVALID',
            'emission.envelope.rule_ids')

    def test_actual_computation_is_pending_and_post_disposition_matches_observed_outcome(self):
        for signature in ('100000000', '100011110'):
            with self.subTest(signature=signature):
                model = self.model(capture=normalization.RecordingNormalizationCapture())
                plan = self.plan(model, self.diagnose(model, signature))
                result = model.apply_normalization(plan, normalization_context=operation_context())
                computation, post = result.emitted_diagnostics
                blocked_computation = dataclasses.replace(computation, emission=dataclasses.replace(computation.emission,
                    envelope=dataclasses.replace(computation.emission.envelope, disposition='BLOCKED')))
                self.assert_contract_error(lambda: dataclasses.replace(result, emitted_diagnostics=(blocked_computation, post)),
                                           'NORMALIZATION_PLAN_INVALID', 'emitted_diagnostics')
                pending_post = dataclasses.replace(post, emission=dataclasses.replace(post.emission,
                    envelope=dataclasses.replace(post.emission.envelope, disposition='PENDING')))
                self.assert_contract_error(lambda: dataclasses.replace(result, emitted_diagnostics=(computation, pending_post)),
                                           'NORMALIZATION_PLAN_INVALID', 'emission.envelope')
        model = self.model(capture=normalization.RecordingNormalizationCapture())
        plan = self.plan(model)
        diagnose = model._diagnose
        def wrong_post(decoded):
            result = diagnose(decoded)
            return dataclasses.replace(result, admissibility_status='TRANSFORMATION_COMPATIBLE',
                transformation_compatibility='COMPATIBLE', normalization_status='NORMALIZABLE',
                recoverability_relevance='RECOVERY_APPLICABLE', is_valid=False) if decoded.state == ash('100000000') else result
        with mock.patch.object(model, '_diagnose', side_effect=wrong_post):
            failure = model.apply_normalization(plan, normalization_context=operation_context())
        computation, post = failure.emitted_diagnostics
        resolved_post = dataclasses.replace(post, emission=dataclasses.replace(post.emission,
            envelope=dataclasses.replace(post.emission.envelope, disposition='RESOLVED')))
        self.assert_contract_error(lambda: dataclasses.replace(failure, emitted_diagnostics=(computation, resolved_post)),
                                   'NORMALIZATION_PLAN_INVALID', 'emission.envelope')


class NormalizationWireTests(NormalizationTestCase):
    @classmethod
    def setUpClass(cls):
        cls.retrievals = []
        def deny(uri):
            cls.retrievals.append(uri)
            raise AssertionError('N1 schemas must resolve locally: ' + uri)
        schemas = [json.loads((ROOT / 'data/schemas' / name).read_text(encoding='utf-8')) for name in (
            'm3_state_assessment_schema.json', 'm3_normalization_plan_schema.json', 'm3_state_normalization_schema.json')]
        for schema in schemas: Draft202012Validator.check_schema(schema)
        registry = Registry(retrieve=deny).with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas)
        cls.validators = {schema['$id'].rsplit('/', 1)[1]: Draft202012Validator(schema, registry=registry) for schema in schemas}
        cls.authored = json.loads((ROOT / 'examples/core_state_normalization/normalization_cases.example.json').read_text(encoding='utf-8'))

    def validator_for(self, packet):
        return self.validators[packet['schema_ref'].rsplit('/', 1)[1]]

    def assert_wire_valid(self, packet, validator=None):
        validator = self.validator_for(packet) if validator is None else validator
        errors = list(validator.iter_errors(packet))
        self.assertEqual([], errors, '\n'.join(error.message for error in errors))
        self.assertEqual([], self.retrievals)

    def assert_wire_rejected(self, packet, keyword, path, validator=None):
        validator = self.validator_for(packet) if validator is None else validator
        errors = list(validator.iter_errors(packet))
        self.assertTrue(errors, 'An intended structural rejection escaped')
        def witnesses(error):
            result = {(error.validator, tuple(error.absolute_path))}
            for child in error.context: result |= witnesses(child)
            return result
        observed = set().union(*(witnesses(error) for error in errors))
        self.assertIn((keyword, path), observed)
        self.assertEqual([], self.retrievals)

    def test_twenty_authored_packets_match_independent_author_and_validate_offline(self):
        self.assertEqual(authored_wire_packets(), self.authored)
        self.assertEqual(20, len(self.authored))
        self.assertEqual(6, sum(p['artifact_type'] == 'ywe_state_normalization_plan' for p in self.authored))
        outcomes = set()
        for index, packet in enumerate(self.authored):
            with self.subTest(pointer='/' + str(index)):
                self.assert_wire_valid(packet)
                if 'outcome' in packet: outcomes.add((packet['outcome'], packet.get('failure_kind')))
        self.assertEqual({('ALREADY_VALID', None), ('NORMALIZED', None), ('NOT_NORMALIZABLE', 'semantic'),
            ('BLOCKED', 'semantic'), ('FAILURE', 'diagnostic_capture'), ('FAILURE', 'plan_validation'),
            ('FAILURE', 'post_validation')}, outcomes)

    def test_actual_plans_and_results_cover_all_outcomes_and_capture_boundaries(self):
        actual_packets = []
        for signature in ('100000000', '100011110', '000000000', 'bad'):
            model = self.model(capture=normalization.RecordingNormalizationCapture())
            plan = self.plan(model, self.diagnose(model, signature))
            actual_packets.extend([plan.to_record(), model.apply_normalization(plan, normalization_context=operation_context()).to_record()])
        source = sv.ProfileSourceBinding('tests/test_m3_normalization.py:unavailable', '0' * 64, 'n1:unavailable:evidence')
        profile = sv.UnavailableProfileBinding(sv.UnavailableValidityProfileEvidence('n1:unavailable', source,
            'PROFILE_DATA_UNAVAILABLE', 'No authoritative profile data is available.'))
        model = self.model(profile, normalization.RecordingNormalizationCapture())
        plan = self.plan(model)
        actual_packets.extend([plan.to_record(), model.apply_normalization(plan, normalization_context=operation_context()).to_record()])
        for mode in ('begin-throw', 'begin-none', 'begin-object', 'begin-noncallable', 'reject', 'throw-before',
                     'throw-after', 'missing', 'wrong-reference', 'unconfirmed'):
            for stage in ((0,) if mode.startswith('begin-') else (0, 1)):
                model = self.model(capture=CaptureDouble(mode, stage))
                actual_packets.append(model.apply_normalization(self.plan(model), normalization_context=operation_context()).to_record())
        original = self.model(profile_binding('n1:foreign', ('000000000',)), normalization.RecordingNormalizationCapture())
        plan = self.plan(original, self.diagnose(original, '000000000'))
        current = self.model(capture=normalization.RecordingNormalizationCapture())
        actual_packets.append(current.apply_normalization(plan, normalization_context=operation_context()).to_record())
        plan = self.plan(current)
        bad = dataclasses.replace(plan, codeword_chain=(ash('001100110'),))
        actual_packets.append(current.apply_normalization(bad, normalization_context=operation_context()).to_record())
        diagnose = current._diagnose
        def wrong_post(decoded):
            diagnostic = diagnose(decoded)
            return dataclasses.replace(diagnostic, admissibility_status='TRANSFORMATION_COMPATIBLE',
                transformation_compatibility='COMPATIBLE', normalization_status='NORMALIZABLE',
                recoverability_relevance='RECOVERY_APPLICABLE', is_valid=False) if decoded.state == ash('100000000') else diagnostic
        with mock.patch.object(current, '_diagnose', side_effect=wrong_post):
            actual_packets.append(current.apply_normalization(plan, normalization_context=operation_context()).to_record())
        rejected_post = self.model(capture=CaptureDouble('reject', 1))
        rejected_plan = self.plan(rejected_post)
        with mock.patch.object(rejected_post, '_diagnose', side_effect=wrong_post):
            actual_packets.append(rejected_post.apply_normalization(rejected_plan, normalization_context=operation_context()).to_record())
        self.assertEqual(30, len(actual_packets))
        for index, packet in enumerate(actual_packets):
            with self.subTest(actual_packet=index): self.assert_wire_valid(packet)

    def test_plan_structural_mutations_have_exact_owned_keyword_and_path(self):
        base = self.authored[0]
        validator = self.validator_for(base)
        mutations = [('unknown-field', lambda p: p.update(unknown=True), 'additionalProperties', ())]
        for field in ('schema_ref', 'artifact_type', 'artifact_version') + PLAN_FIELDS:
            mutations.append(('missing-' + field, lambda p, field=field: p.pop(field), 'required', ()))
        mutations.extend([
            ('wrong-header', lambda p: p.update(artifact_type='ywe_state_normalization'), 'const', ('artifact_type',)),
            ('boolean-completeness', lambda p: p.update(eligible_targets_complete=1), 'type', ('eligible_targets_complete',)),
            ('seventeen-targets', lambda p: p.update(eligible_targets=p['eligible_targets'] * 17), 'maxItems', ('eligible_targets',)),
            ('duplicate-target', lambda p: p['eligible_targets'].append(copy.deepcopy(p['eligible_targets'][0])), 'uniqueItems', ('eligible_targets',)),
            ('two-codewords', lambda p: p['codeword_chain'].append(copy.deepcopy(p['codeword_chain'][0])), 'maxItems', ('codeword_chain',)),
            ('noncanonical-codeword', lambda p: p['codeword_chain'][0].update(bits=[0] * 8 + [1]), 'enum', ('codeword_chain', 0, 'bits')),
            ('codeword-bool-bit', lambda p: p['codeword_chain'][0]['bits'].__setitem__(0, True), 'type', ('codeword_chain', 0, 'bits', 0)),
            ('target-short-width', lambda p: p['selected_target']['bits'].pop(), 'minItems', ('selected_target', 'bits')),
            ('unknown-decision', lambda p: p.update(decision='RECOVERED'), 'enum', ('decision',)),
            ('missing-ready-target', lambda p: p.update(selected_target=None), 'type', ('selected_target',)),
            ('policy-pin', lambda p: p['policy_binding'].update(source_sha256='0' * 64), 'const', ('policy_binding', 'source_sha256')),
            ('ready-empty-chain', lambda p: p.update(codeword_chain=[]), 'minItems', ('codeword_chain',)),
            ('new-codeword-rule-in-original', lambda p: p['original_diagnosis']['state_validity_diagnostic']['rule_ids'].append(CODEWORD_RULE),
             'enum', ('original_diagnosis', 'state_validity_diagnostic', 'rule_ids', 3)),
        ])
        for name, mutate, keyword, path in mutations:
            with self.subTest(case=name):
                altered = copy.deepcopy(base); mutate(altered)
                self.assert_wire_rejected(altered, keyword, path, validator)

    def test_result_structural_mutations_have_exact_owned_keyword_and_path(self):
        base, capture, early = self.authored[6], self.authored[15], self.authored[17]
        validator = self.validator_for(base)
        mutations = [('unknown-field', base, lambda p: p.update(unknown=True), 'additionalProperties', ()),
                     ('fake-system-class', base, lambda p: p.update(system_state_class='STABLE'), 'additionalProperties', ())]
        for field in ('schema_ref', 'artifact_type', 'artifact_version') + COMMON_FIELDS:
            mutations.append(('missing-' + field, base, lambda p, field=field: p.pop(field), 'required', ()))
        for field in VALIDATION_FIELDS:
            mutations.append(('missing-validation-' + field, base, lambda p, field=field: p['plan_validation'].pop(field),
                              'required', ('plan_validation',)))
        for field in SEMANTIC_FIELDS + ('rule_ids', 'notes'):
            mutations.append(('missing-post-' + field, base, lambda p, field=field: p['post_validity_diagnostic'].pop(field),
                              'required', ('post_validity_diagnostic',)))
        mutations.extend([
            ('wire-validation-plan-null', base, lambda p: p['plan_validation'].update(plan=None), 'type', ('plan_validation', 'plan')),
            ('valid-post-false', base, lambda p: p['post_validity_diagnostic'].update(is_valid=False), 'const', ('post_validity_diagnostic', 'is_valid')),
            ('zero-success-records', base, lambda p: p.update(emitted_diagnostics=[]), 'minItems', ('emitted_diagnostics',)),
            ('extra-success-record', base, lambda p: p['emitted_diagnostics'].append(copy.deepcopy(p['emitted_diagnostics'][1])), 'maxItems', ('emitted_diagnostics',)),
            ('lost-normalized-result', base, lambda p: p.update(normalized_state=None), 'type', ('normalized_state',)),
            ('fraction-step-index', base, lambda p: p['steps'][0].update(step_index=0.5), 'const', ('steps', 0, 'step_index')),
            ('bool-step-index', base, lambda p: p['steps'][0].update(step_index=False), 'const', ('steps', 0, 'step_index')),
            ('wrong-phase', base, lambda p: p['emitted_diagnostics'][0].update(phase='POST_VALIDATION'), 'const', ('emitted_diagnostics', 0, 'phase')),
            ('stage-regresses', base, lambda p: p['emitted_diagnostics'][1]['emission']['envelope'].update(stage='DETECTION'), 'const', ('emitted_diagnostics', 1, 'emission', 'envelope', 'stage')),
            ('fake-rule', base, lambda p: p['emitted_diagnostics'][0]['emission']['envelope'].update(rule_ids=['ASH-NORMALIZATION-POLICY-001']),
             'enum', ('emitted_diagnostics', 0, 'emission', 'envelope', 'rule_ids', 0)),
            ('early-origin-fakes-target-evaluation', early, lambda p: p['plan_validation'].update(recomputed_eligible_targets=[]),
             'type', ('plan_validation', 'recomputed_eligible_targets')),
            ('early-origin-fakes-inherited-ack', early, lambda p: p.update(inherited_diagnostics=copy.deepcopy(p['original_diagnosis']['emitted_diagnostics'])),
             'maxItems', ('inherited_diagnostics',)),
            ('capture-claims-confirmed', capture, lambda p: p.update(capture_status='CONFIRMED'), 'enum', ('capture_status',)),
            ('capture-status-code-pair', capture, lambda p: p.update(capture_status='REJECTED'), 'const', ('failure_code',)),
            ('capture-loses-full-attempt', capture, lambda p: p.pop('attempted_diagnostic'), 'required', ()),
            ('capture-publishes-normalized', capture, lambda p: p.update(normalized_state=copy.deepcopy(p['actual_state'])), 'type', ('normalized_state',)),
            ('post-attempt-loses-confirmed-prefix', capture, lambda p: p.update(emitted_diagnostics=[]), 'minItems', ('emitted_diagnostics',)),
            ('capture-fakes-original-rule', capture, lambda p: p['inherited_diagnostics'][0]['envelope']['rule_ids'].append(CODEWORD_RULE),
             'enum', ('inherited_diagnostics', 0, 'envelope', 'rule_ids', 3)),
        ])
        for name, original, mutate, keyword, path in mutations:
            with self.subTest(case=name):
                altered = copy.deepcopy(original); mutate(altered)
                self.assert_wire_rejected(altered, keyword, path, validator)

    def test_all_ten_summary_separators_and_bounds_are_enforced_with_positive_controls(self):
        base = self.authored[6]
        path = ('emitted_diagnostics', 0, 'emission', 'envelope', 'summary')
        for separator in ('\r', '\n', '\v', '\f', '\x1c', '\x1d', '\x1e', '\u0085', '\u2028', '\u2029'):
            with self.subTest(separator=ord(separator)):
                altered = copy.deepcopy(base)
                altered['emitted_diagnostics'][0]['emission']['envelope']['summary'] = 'a' + separator + 'b'
                self.assert_wire_rejected(altered, 'not', path)
        for summary in ('', 's' * 513):
            altered = copy.deepcopy(base)
            altered['emitted_diagnostics'][0]['emission']['envelope']['summary'] = summary
            self.assert_wire_rejected(altered, 'minLength' if not summary else 'maxLength', path)
        for summary in ('a b', 'a\tb', 's' * 512):
            altered = copy.deepcopy(base)
            altered['emitted_diagnostics'][0]['emission']['envelope']['summary'] = summary
            self.assert_wire_valid(altered)

    def test_semantic_blocked_and_proof_refusals_cannot_structurally_acquire_post_attempt(self):
        actual_post = self.authored[15]['attempted_diagnostic']
        for index in (8, 9, 10, 18):
            with self.subTest(original_pointer='/' + str(index)):
                altered = copy.deepcopy(self.authored[index])
                altered.update(outcome='FAILURE', failure_kind='diagnostic_capture',
                    failure_code='DIAGNOSTIC_CAPTURE_UNCONFIRMED', failed_field='normalization_capture',
                    capture_status='NOT_CONFIRMED', post_validity_diagnostic=copy.deepcopy(altered['original_diagnosis']['state_validity_diagnostic']),
                    attempted_diagnostic=copy.deepcopy(actual_post))
                self.assert_wire_rejected(altered, 'const', ('emitted_diagnostics', 0, 'emission', 'envelope', 'disposition'))

    def test_wire_computation_and_post_dispositions_match_the_declared_phase(self):
        for index in (6, 7):
            with self.subTest(pointer='/' + str(index)):
                altered = copy.deepcopy(self.authored[index])
                altered['emitted_diagnostics'][0]['emission']['envelope']['disposition'] = 'BLOCKED'
                self.assert_wire_rejected(altered, 'const', ('emitted_diagnostics', 0, 'emission', 'envelope', 'disposition'))
                altered = copy.deepcopy(self.authored[index])
                altered['emitted_diagnostics'][1]['emission']['envelope']['disposition'] = 'PENDING'
                self.assert_wire_rejected(altered, 'const', ('emitted_diagnostics', 1, 'emission', 'envelope', 'disposition'))
        altered = copy.deepcopy(self.authored[19])
        altered['emitted_diagnostics'][1]['emission']['envelope']['disposition'] = 'RESOLVED'
        self.assert_wire_rejected(altered, 'const', ('emitted_diagnostics', 1, 'emission', 'envelope', 'disposition'))

    def test_capture_post_requires_complete_disposition_with_blocked_nonvalid_control(self):
        path = ('attempted_diagnostic', 'emission', 'envelope', 'disposition')
        for disposition in ('PENDING', 'ESCALATED', 'TERMINAL'):
            with self.subTest(disposition=disposition):
                altered = copy.deepcopy(self.authored[15])
                altered['attempted_diagnostic']['emission']['envelope']['disposition'] = disposition
                self.assert_wire_rejected(altered, 'enum', path)
        failing_post = copy.deepcopy(self.authored[19])
        failing_post.update(failure_kind='diagnostic_capture', failure_code='DIAGNOSTIC_CAPTURE_REJECTED',
                            failed_field='normalization_capture', capture_status='REJECTED')
        failing_post['attempted_diagnostic'] = failing_post['emitted_diagnostics'].pop()
        self.assert_wire_valid(failing_post)
        failing_post['attempted_diagnostic']['emission']['envelope']['disposition'] = 'RESOLVED'
        self.assert_wire_rejected(failing_post, 'const', path)


if __name__ == '__main__':
    unittest.main()
