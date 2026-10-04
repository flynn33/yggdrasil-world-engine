from __future__ import annotations

import collections
import copy
import dataclasses
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import unittest
from unittest import mock

from jsonschema import Draft202012Validator
from referencing import Registry

from core.ash_pattern_engine import ash_canonical as legacy
from core.ash_pattern_engine.state_model import RecordingDiagnosticCapture, StateInputCodec, StateModel
from core.ash_pattern_engine import state_values as values


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'core/ash_pattern_engine/canonical'
DEPENDENCY = 'ash_cosmological_model.f2_9.canonical'
AGGREGATE = '0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb'
SOURCE_FIELDS = {
    'state_space_sha256': 'core/ash-state-space.pseudo.md',
    'codeword_source_sha256': 'core/codeword-set.pseudo.md',
    'validity_source_sha256': 'core/state-validity-diagnostics.pseudo.md',
    'classification_source_sha256': 'core/system-state-classification.pseudo.md',
    'recovery_source_sha256': 'core/recoverability-semantics.pseudo.md',
    'diagnostic_source_sha256': 'interfaces/diagnostic-schema.md',
    'taxonomy_source_sha256': 'interfaces/rule-id-taxonomy.md',
}
VALIDITY_FIELDS = {
    'input_state', 'admissibility_status', 'transformation_compatibility',
    'normalization_status', 'recoverability_relevance', 'is_valid', 'orbit_info', 'rule_ids', 'notes',
}
ENVELOPE_FIELDS = {
    'diagnostic_kind', 'severity', 'stage', 'disposition', 'subject_reference',
    'parent_diagnostic_reference', 'chain_root_reference', 'rule_ids', 'summary', 'notes',
}
ROWS = {
    'VALID': ('COMPATIBLE', 'ALREADY_VALID', 'NO_RECOVERY_NEEDED', True),
    'TRANSFORMATION_COMPATIBLE': ('COMPATIBLE', 'NORMALIZABLE', 'RECOVERY_APPLICABLE', False),
    'TRANSFORMATION_INCOMPATIBLE': ('INCOMPATIBLE', 'NOT_NORMALIZABLE', 'NOT_RECOVERABLE', False),
    'UNCLASSIFIED': ('UNKNOWN', 'BLOCKED', 'CONTAINMENT_NEEDED', False),
}
CATEGORIES = {
    'STABLE': 'NO_ACTION', 'UNSTABLE': 'NORMALIZE_STATE', 'CORRECTABLE': 'APPLY_CORRECTION',
    'DEGRADED': 'FALLBACK_REQUIRED', 'CONTAINED': 'CONTAINMENT_REQUIRED',
    'FAILED': 'ESCALATION_REQUIRED', 'SAFE_HALT': 'TERMINAL_NO_RECOVERY',
}
# Direct transcription of the pinned classifier's four rows in HTKF order.
CLASS_MATRIX = {
    'VALID': ['STABLE'] * 4 + ['CONTAINED'] * 4 + ['SAFE_HALT'] * 8,
    'TRANSFORMATION_COMPATIBLE': ['UNSTABLE', 'UNSTABLE', 'CORRECTABLE', 'CORRECTABLE']
                                + ['CONTAINED'] * 4 + ['SAFE_HALT'] * 8,
    'TRANSFORMATION_INCOMPATIBLE': ['FAILED', 'DEGRADED', 'FAILED', 'DEGRADED']
                                  + ['CONTAINED'] * 4 + ['SAFE_HALT'] * 8,
    'UNCLASSIFIED': ['DEGRADED'] * 4 + ['CONTAINED'] * 4 + ['SAFE_HALT'] * 8,
}


def normalized_hash(path: Path) -> str:
    text = path.read_bytes().decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def independently_read_codewords() -> tuple[int, ...]:
    text = (CANONICAL / 'core/codeword-set.pseudo.md').read_text(encoding='utf-8')
    rows = re.findall(r'^\s*(\d+)\s+\(([01](?:, [01]){8})\)\s+[048]\s*$', text, re.M)
    if [int(index) for index, _ in rows] != list(range(16)):
        raise AssertionError('Pinned codeword enumeration is not the complete ordered C16')
    return tuple(int(bits.replace(', ', ''), 2) for _, bits in rows)


def wrw_signatures() -> tuple[str, ...]:
    text = (ROOT / 'data/ash_state/realm_bit_mapping.yaml').read_text(encoding='utf-8')
    signatures = tuple(re.findall(r'^    state_identity: "([01]{9})"$', text, re.M))
    if len(signatures) != 9 or len(set(signatures)) != 9:
        raise AssertionError('Explicit WRW projection does not contain nine distinct anchors')
    return signatures


def canonical_record() -> dict[str, str]:
    return {'dependency_id': DEPENDENCY, 'aggregate_sha256': AGGREGATE,
            **{field: normalized_hash(CANONICAL / path) for field, path in SOURCE_FIELDS.items()}}


def source_binding(profile_id: str, signatures: tuple[str, ...]):
    if profile_id == 'wrw_reference_profile':
        reference = 'data/ash_state/realm_bit_mapping.yaml'
        digest = normalized_hash(ROOT / reference)
    else:
        reference = 'tests/test_m3_state_model.py:' + profile_id
        digest = hashlib.sha256(json.dumps(sorted(signatures), separators=(',', ':')).encode()).hexdigest()
    return values.ProfileSourceBinding(source_reference=reference, source_sha256=digest,
                                       evidence_reference=profile_id + ':declared_source')


def profile_binding(profile_id='wrw_reference_profile', signatures=None):
    signatures = wrw_signatures() if signatures is None else tuple(signatures)
    source = source_binding(profile_id, signatures)
    profile = values.ValidityProfile(profile_id=profile_id, source_binding=source,
                                    recognized_valid_states=[values.AshState(tuple(map(int, s))) for s in signatures])
    return values.AvailableProfileBinding(profile=profile)


def diagnostic_context(reference='m3_test:assessment'):
    return values.DiagnosticContext(assessment_reference=reference,
                                    original_input_reference=reference + ':input',
                                    detection_reference=reference + ':detection',
                                    classification_reference=reference + ':classification')


def predicate_binding(profile, context, subject, predicate):
    record = profile.to_record()
    return values.PredicateBinding(
        assessment_reference=context.assessment_reference, diagnosis_reference=context.detection_reference,
        subject_reference=subject, profile_id=record['profile_id'],
        profile_source_sha256=record['source_binding']['source_sha256'],
        ash_dependency_id=DEPENDENCY, ash_aggregate_sha256=AGGREGATE,
        evidence_reference=context.assessment_reference + ':' + predicate + ':fixture_fact',
    )


def evidence(profile, context, subject, correction=None, fallback=None):
    facts = []
    for name, value in [('correction_path_is_known', correction), ('fallback_is_available', fallback)]:
        binding = predicate_binding(profile, context, subject, name)
        facts.append(values.NotEvaluatedPredicate(binding=binding, reason='Not evaluated by this explicit fixture.')
                     if value is None else values.EvaluatedPredicate(binding=binding, value=value))
    return values.ClassificationEvidence(correction_path_is_known=facts[0], fallback_is_available=facts[1])


class CaptureDouble:
    """A real append/ack boundary with deliberately injected uncertainty."""

    def __init__(self, failure_at=None, mode='confirmed'):
        self.failure_at, self.mode = failure_at, mode
        self.begins = []
        self.calls = []
        self.stored = []

    def begin(self, assessment_reference):
        self.begins.append(assessment_reference)
        return self

    def append(self, emission):
        self.calls.append(emission)
        ref = emission.diagnostic_reference
        if len(self.calls) == self.failure_at:
            if self.mode == 'reject':
                return values.CaptureReceipt(diagnostic_reference=ref, status='REJECTED')
            if self.mode == 'throw_before':
                raise RuntimeError('collector private detail must not enter output')
            if self.mode == 'append_then_throw':
                self.stored.append(emission)
                raise RuntimeError('collector private detail must not enter output')
            if self.mode == 'wrong_reference':
                self.stored.append(emission)
                return values.CaptureReceipt(diagnostic_reference=ref + ':wrong', status='CONFIRMED')
            if self.mode == 'wrong_rejected_reference':
                return values.CaptureReceipt(diagnostic_reference=ref + ':wrong', status='REJECTED')
            if self.mode == 'malformed_receipt':
                self.stored.append(emission)
                return {'diagnostic_reference': ref, 'status': 'CONFIRMED'}
            if self.mode == 'not_confirmed':
                self.stored.append(emission)
                return values.CaptureReceipt(diagnostic_reference=ref, status='NOT_CONFIRMED')
        self.stored.append(emission)
        return values.CaptureReceipt(diagnostic_reference=ref, status='CONFIRMED')


class HostileValue:
    def __init__(self):
        self.calls = []

    def _fail(self, operation):
        self.calls.append(operation)
        raise AssertionError('Untrusted conversion hook executed: ' + operation)

    def __int__(self): return self._fail('int')
    def __float__(self): return self._fail('float')
    def __str__(self): return self._fail('str')
    def __repr__(self): return self._fail('repr')
    def __iter__(self): return self._fail('iter')
    def __len__(self): return self._fail('len')
    def __eq__(self, other): return self._fail('eq')
    def __hash__(self): return self._fail('hash')


class HostileInt(int):
    calls = []

    def __int__(self):
        self.calls.append('int')
        raise AssertionError('int subclass converted')

    def __eq__(self, other):
        self.calls.append('eq')
        raise AssertionError('int subclass compared')

    def __repr__(self):
        self.calls.append('repr')
        raise AssertionError('int subclass represented')


class HostileMetaclass(type):
    calls = []

    def __eq__(cls, other):
        HostileMetaclass.calls.append('metaclass equality')
        raise AssertionError('Unsupported type compared through its metaclass')


class HostileMetaValue(metaclass=HostileMetaclass):
    pass


class HostileMetaSequence(list, metaclass=HostileMetaclass):
    pass


class ModelTestCase(unittest.TestCase):
    def make_model(self, profile=None, capture=None):
        profile = profile if profile is not None else profile_binding()
        capture = capture if capture is not None else CaptureDouble()
        return StateModel(profile_binding=profile, canonical_binding=values.CanonicalAshBinding(**canonical_record()),
                          diagnostic_capture=capture)

    def assert_code(self, code, callable, *args, **kwargs):
        with self.assertRaises(values.StateContractError) as caught:
            callable(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)
        return caught.exception

    def decode(self, candidate, **kwargs):
        return StateInputCodec().decode(candidate, original_input_reference='m3_test:input', **kwargs)

    def assert_rejected(self, candidate, code, **kwargs):
        result = self.decode(candidate, **kwargs)
        self.assertIsNone(result.state)
        record = result.input_evidence.to_record()
        self.assertEqual(code, record['failure_code'])
        self.assertEqual('m3_test:input', record['original_input_reference'])
        self.assertLessEqual(len(record['coordinate_observations']), 9)
        self.assertLessEqual(len(record['preview'] or ''), 64)
        json.dumps(record, allow_nan=False, ensure_ascii=True).encode('utf-8')
        return record

    def assert_diagnosis(self, packet, expected_status):
        self.assertEqual('data/schemas/m3_state_assessment_schema.json', packet['schema_ref'])
        self.assertEqual('ywe_state_assessment', packet['artifact_type'])
        self.assertEqual('1.0.0', packet['artifact_version'])
        diagnostic = packet['state_validity_diagnostic']
        self.assertEqual(VALIDITY_FIELDS, set(diagnostic))
        compatibility, normalization, relevance, is_valid = ROWS[expected_status]
        self.assertEqual(expected_status, diagnostic['admissibility_status'])
        self.assertEqual(compatibility, diagnostic['transformation_compatibility'])
        self.assertEqual(normalization, diagnostic['normalization_status'])
        self.assertEqual(relevance, diagnostic['recoverability_relevance'])
        self.assertIs(is_valid, diagnostic['is_valid'])
        self.assertTrue(diagnostic['rule_ids'])
        self.assertTrue(diagnostic['notes'])
        return diagnostic

    def assert_chain(self, packet, count):
        emissions = packet['emitted_diagnostics']
        self.assertEqual(count, len(emissions))
        previous = None
        root = packet['assessment_binding']['diagnosis_reference']
        for index, emission in enumerate(emissions):
            envelope = emission['envelope']
            self.assertEqual(ENVELOPE_FIELDS, set(envelope))
            self.assertEqual('STATE_VALIDITY', envelope['diagnostic_kind'])
            self.assertEqual('DETECTION' if index == 0 else 'CLASSIFICATION', envelope['stage'])
            self.assertEqual(previous, envelope['parent_diagnostic_reference'])
            self.assertEqual(root, envelope['chain_root_reference'])
            self.assertTrue(envelope['summary'])
            self.assertNotIn('\n', envelope['summary'])
            self.assertTrue(envelope['notes'])
            self.assertLessEqual(len(envelope['notes']), 8)
            self.assertLessEqual(len(envelope['rule_ids']), 5)
            for rule in envelope['rule_ids']:
                self.assertRegex(rule, r'^ASH-(?:STATE|CODEWORD|ADMISSIBILITY|CLASSIFICATION|RECOVERY|FALLBACK|CONTAINMENT|HALT)-[A-Z]+-\d{3}$')
            previous = emission['diagnostic_reference']


class StateConstructionTests(ModelTestCase):
    def test_constructor_owns_bits_and_returns_fresh_wire_containers(self):
        original = [1] + [0] * 8
        state = values.AshState(bits=original)
        original[0] = 0
        self.assertEqual('100000000', state.signature)
        self.assertEqual((1,) + (0,) * 8, state.bits)
        record = state.to_record()
        record['bits'][0] = 0
        self.assertEqual(1, state.to_record()['bits'][0])
        with self.assertRaises((dataclasses.FrozenInstanceError, AttributeError)):
            state.bits = (0,) * 9

    def test_constructor_rejects_width_value_and_coercible_types(self):
        for width in [0, 8, 10]:
            with self.subTest(width=width):
                self.assert_code('STATE_WIDTH', values.AshState, bits=[0] * width)
        for bit, code in [(2, 'STATE_COORDINATE_VALUE'), (-1, 'STATE_COORDINATE_VALUE'),
                          (True, 'STATE_COORDINATE_TYPE'), (1.0, 'STATE_COORDINATE_TYPE'),
                          ('1', 'STATE_COORDINATE_TYPE')]:
            with self.subTest(bit=bit):
                self.assert_code(code, values.AshState, bits=[bit] + [0] * 8)

    def test_constructor_rejects_hostile_integer_subclass_without_hooks(self):
        HostileInt.calls.clear()
        self.assert_code('STATE_COORDINATE_TYPE', values.AshState, bits=[HostileInt(1)] + [0] * 8)
        self.assertEqual([], HostileInt.calls)

    def test_constructor_rejects_unsupported_coordinate_without_conversion(self):
        hostile = HostileValue()
        self.assert_code('STATE_COORDINATE_TYPE', values.AshState, bits=[hostile] + [0] * 8)
        self.assertEqual([], hostile.calls)

    def test_constructor_rejects_hostile_metaclass_without_type_equality_hooks(self):
        HostileMetaclass.calls.clear()
        self.assert_code('STATE_COORDINATE_TYPE', values.AshState, bits=[HostileMetaValue()] + [0] * 8)
        self.assert_code('STATE_COORDINATE_TYPE', values.AshState, bits=HostileMetaSequence([0] * 9))
        self.assertEqual([], HostileMetaclass.calls)

    def test_each_canonical_binding_field_requires_the_exact_fixed_pin(self):
        original = canonical_record()
        self.assertEqual(original, values.CanonicalAshBinding(**original).to_record())
        for field in original:
            altered = dict(original)
            altered[field] = DEPENDENCY + '.wrong' if field == 'dependency_id' else '0' * 64
            with self.subTest(field=field):
                self.assert_code('CANONICAL_BINDING_INVALID', values.CanonicalAshBinding, **altered)

    def test_source_manifest_and_independently_hashed_pins_match(self):
        identity = json.loads((ROOT / 'data/governance/ash_dependency_identity.json').read_text(encoding='utf-8'))
        self.assertEqual(DEPENDENCY, identity['dependency_id'])
        self.assertEqual(32, len(identity['files']))
        records = []
        for item in sorted(identity['files'], key=lambda item: item['relative_path']):
            observed = normalized_hash(CANONICAL / item['relative_path'])
            self.assertEqual(item['sha256'], observed)
            records.append(item['relative_path'].encode() + b'\0' + observed.encode() + b'\n')
        self.assertEqual(AGGREGATE, hashlib.sha256(b''.join(records)).hexdigest())

    def test_context_requires_exact_booleans(self):
        for field in ['is_in_safe_halt', 'is_in_containment']:
            for value in [0, 1, 'false', None]:
                args = dict(is_in_safe_halt=False, is_in_containment=False)
                args[field] = value
                with self.subTest(field=field, value=value):
                    self.assert_code('CONTEXT_INVALID', values.SystemContext, **args)

    def test_diagnostic_references_have_explicit_distinct_finite_bounds(self):
        for length in [1, 256]:
            context = values.DiagnosticContext(assessment_reference='a' * length,
                        original_input_reference='b' * length, detection_reference='c' * length,
                        classification_reference='d' * length)
            self.assertEqual('c' * length, context.detection_reference)
        base = diagnostic_context().to_record()
        for field in base:
            for wrong in ['', 'a' * 257, '_bad', 'contains space', 'é', None]:
                args = dict(base); args[field] = wrong
                with self.subTest(field=field, wrong=wrong):
                    self.assert_code('DIAGNOSTIC_CONTEXT_INVALID', values.DiagnosticContext, **args)
        for wrong in ['NONE', 'SELF', base['detection_reference']]:
            args = dict(base); args['classification_reference'] = wrong
            self.assert_code('DIAGNOSTIC_CONTEXT_INVALID', values.DiagnosticContext, **args)

    def test_profile_copies_caller_collection_and_distinguishes_duplicate_size(self):
        source = source_binding('m3_test:owned', ('100000000',))
        originals = [values.AshState([1] + [0] * 8)]
        profile = values.ValidityProfile(profile_id='m3_test:owned', source_binding=source,
                                        recognized_valid_states=originals)
        originals.clear()
        self.assertEqual(['100000000'], profile.to_record()['recognized_valid_signatures'])
        state = values.AshState([0] * 9)
        self.assert_code('PROFILE_STATE_DUPLICATE', values.ValidityProfile, profile_id='m3_test:duplicates',
                         source_binding=source, recognized_valid_states=[state, state])
        all_states = [values.AshState(tuple(map(int, format(x, '09b')))) for x in range(512)]
        accepted = values.ValidityProfile(profile_id='m3_test:all', source_binding=source,
                                         recognized_valid_states=all_states)
        self.assertEqual(512, len(accepted.to_record()['recognized_valid_signatures']))
        self.assert_code('PROFILE_SIZE_LIMIT', values.ValidityProfile, profile_id='m3_test:overflow',
                         source_binding=source, recognized_valid_states=all_states + [state])


class CandidateCodecTests(ModelTestCase):
    def test_exact_ash_state_candidate_preserves_the_owned_value(self):
        state = values.AshState([1] + [0] * 8)
        decoded = self.decode(state)
        self.assertEqual(state, decoded.state)
        self.assertEqual([1] + [0] * 8, decoded.state.to_record()['bits'])
        self.assertIsNone(decoded.input_evidence.to_record()['failure_code'])
        packet = self.make_model().diagnose(state, diagnostic_context=diagnostic_context()).to_record()
        self.assert_diagnosis(packet, 'VALID')

    def test_parsed_integral_float_is_a_codec_rule_not_a_constructor_rule(self):
        decoded = self.decode([1.0, -0.0] + [0.0] * 7)
        self.assertEqual('100000000', decoded.state.signature)
        self.assertTrue(all(type(bit) is int for bit in decoded.state.bits))
        self.assert_code('STATE_COORDINATE_TYPE', values.AshState, bits=[1.0] + [0] * 8)

    def test_fraction_boolean_and_quoted_coordinate_do_not_coerce(self):
        for candidate, code in [(0.9, 'STATE_COORDINATE_VALUE'), (True, 'STATE_COORDINATE_TYPE'),
                                ('1', 'STATE_COORDINATE_TYPE')]:
            with self.subTest(candidate=candidate):
                self.assert_rejected([candidate] + [0] * 8, code)

    def test_nonfinite_coordinates_have_json_safe_typed_observations(self):
        for number, token in [(math.nan, 'NAN'), (math.inf, 'POSITIVE_INFINITY'),
                              (-math.inf, 'NEGATIVE_INFINITY')]:
            with self.subTest(token=token):
                record = self.assert_rejected([number] + [0] * 8, 'STATE_COORDINATE_VALUE')
                observation = record['coordinate_observations'][0]
                self.assertEqual('NONFINITE_FLOAT', observation['scalar_kind'])
                self.assertEqual(token, observation['value'])

    def test_signature_is_ascii_and_whitespace_is_an_explicit_legacy_adapter(self):
        self.assertEqual('100000000', self.decode('100000000').state.signature)
        self.assert_rejected('١٠٠٠٠٠٠٠٠', 'INPUT_SIGNATURE_INVALID')
        self.assert_rejected(' 100000000 ', 'INPUT_SIGNATURE_INVALID')
        self.assertEqual('100000000', self.decode(' \t100000000\r\n', legacy_whitespace=True).state.signature)

    def test_hostile_value_and_generator_are_not_iterated_converted_or_represented(self):
        hostile = HostileValue()
        self.assert_rejected(hostile, 'INPUT_KIND_UNSUPPORTED')
        self.assertEqual([], hostile.calls)
        self.assert_rejected([hostile] + [0] * 8, 'STATE_COORDINATE_TYPE')
        self.assertEqual([], hostile.calls)
        visited = []
        def bits():
            visited.append('iterated')
            yield from [0] * 9
        self.assert_rejected(bits(), 'INPUT_KIND_UNSUPPORTED')
        self.assertEqual([], visited)

    def test_hostile_metaclass_cannot_escape_candidate_or_observation_type_guards(self):
        HostileMetaclass.calls.clear()
        unsupported = HostileMetaValue()
        self.assert_rejected(unsupported, 'INPUT_KIND_UNSUPPORTED')
        self.assert_rejected(HostileMetaSequence([0] * 9), 'INPUT_KIND_UNSUPPORTED')
        record = self.assert_rejected([unsupported] + [0] * 8, 'STATE_COORDINATE_TYPE')
        self.assertEqual({'index': 0, 'scalar_kind': 'UNSUPPORTED'}, record['coordinate_observations'][0])
        self.assert_rejected({'state_space': 'F2^9', 'bits': HostileMetaSequence([0] * 9)}, 'INPUT_KIND_UNSUPPORTED')
        self.assertEqual([], HostileMetaclass.calls)

    def test_invalid_reference_rejects_before_candidate_or_observation_hooks(self):
        hostile = HostileValue()
        self.assert_code('DIAGNOSTIC_ROW_INVALID', StateInputCodec().decode, hostile,
                         original_input_reference='invalid reference')
        self.assertEqual([], hostile.calls)

    def test_container_and_scalar_subclasses_cannot_execute_hooks(self):
        visited = []
        class BadList(list):
            def __len__(self): visited.append('len'); raise AssertionError('bad list len')
            def __iter__(self): visited.append('iter'); raise AssertionError('bad list iter')
        class BadStr(str):
            def strip(self): visited.append('strip'); raise AssertionError('bad str strip')
            def encode(self, *args, **kwargs): visited.append('encode'); raise AssertionError('bad str encode')
        class BadDict(dict):
            def keys(self): visited.append('keys'); raise AssertionError('bad dict keys')
            def get(self, *args): visited.append('get'); raise AssertionError('bad dict get')
        for candidate in [BadList([0] * 9), BadStr('000000000'), BadDict(bits=[0] * 9)]:
            self.assert_rejected(candidate, 'INPUT_KIND_UNSUPPORTED')
        HostileInt.calls.clear()
        self.assert_rejected([HostileInt(1)] + [0] * 8, 'STATE_COORDINATE_TYPE')
        self.assertEqual([], visited)
        self.assertEqual([], HostileInt.calls)

    def test_raw_decimal_precision_precedes_binary_float_and_integer_conversion(self):
        self.assert_rejected(b'[1.00000000000000000001,0,0,0,0,0,0,0,0]', 'STATE_COORDINATE_VALUE')
        self.assertEqual('100000000', self.decode(b'[1.000,0,0,0,0,0,0,0,0]').state.signature)
        self.assertEqual('000000000', self.decode(b'[-0.0,0,0,0,0,0,0,0,0]').state.signature)
        self.assertEqual(1.0, json.loads('[1.00000000000000000001]')[0])

    def test_raw_duplicate_keys_nonfinite_invalid_utf8_and_syntax_are_bounded_rejections(self):
        self.assert_rejected(b'{"state_space":"F2^9","bits":[0,0,0,0,0,0,0,0,0],"bits":[1,0,0,0,0,0,0,0,0]}', 'INPUT_JSON_DUPLICATE_KEY')
        for token in [b'NaN', b'Infinity', b'-Infinity']:
            self.assert_rejected(b'[' + token + b',0,0,0,0,0,0,0,0]', 'INPUT_JSON_NONFINITE')
        self.assert_rejected(b'\xff', 'INPUT_UTF8_INVALID')
        self.assert_rejected(b'[', 'INPUT_JSON_INVALID')

    def test_raw_4096_byte_boundary_precedes_parse_or_legacy_strip(self):
        payload = b'[1,0,0,0,0,0,0,0,0]'
        exact = payload + b' ' * (4096 - len(payload))
        self.assertEqual('100000000', self.decode(exact).state.signature)
        self.assert_rejected(exact + b' ', 'INPUT_SIZE_LIMIT')
        exact_signature = ' ' * (4096 - 9) + '100000000'
        self.assertEqual('100000000', self.decode(exact_signature, legacy_whitespace=True).state.signature)
        self.assert_rejected(exact_signature + ' ', 'INPUT_SIZE_LIMIT', legacy_whitespace=True)
        self.assert_rejected('é' * 2049, 'INPUT_SIZE_LIMIT')

    def test_raw_numeric_token_128_boundary_and_huge_exponent_failure(self):
        def array(token): return b'[' + token + b',0,0,0,0,0,0,0,0]'
        exact = b'1.' + b'0' * 126
        self.assertEqual(128, len(exact))
        self.assertEqual('100000000', self.decode(array(exact)).state.signature)
        self.assert_rejected(array(exact + b'0'), 'INPUT_TOKEN_LIMIT')
        self.assert_rejected(array(b'1e' + b'9' * 100), 'INPUT_NUMERIC_TOKEN_INVALID')

    def test_raw_nesting_32_boundary_respects_strings_and_escapes(self):
        def nested(depth):
            # root record counts one level; ignored metadata supplies remaining levels.
            metadata = '[' * (depth - 1) + '0' + ']' * (depth - 1)
            return ('{"state_space":"F2^9","bits":[1,0,0,0,0,0,0,0,0],"metadata":' + metadata + '}').encode()
        self.assertEqual('100000000', self.decode(nested(32)).state.signature)
        self.assert_rejected(nested(33), 'INPUT_DEPTH_LIMIT')
        quoted = json.dumps({'state_space': 'F2^9', 'bits': [1] + [0] * 8,
                             'metadata': '[[[["escaped"\\]]]]' * 40}).encode()
        self.assertEqual('100000000', self.decode(quoted).state.signature)

    def test_direct_record_64_key_boundary_does_not_traverse_metadata(self):
        hostile = HostileValue()
        record = {'state_space': 'F2^9', 'bits': [1] + [0] * 8,
                  **{f'metadata{i}': hostile for i in range(62)}}
        self.assertEqual(64, len(record))
        self.assertEqual('100000000', self.decode(record).state.signature)
        record['metadata_overflow'] = hostile
        self.assert_rejected(record, 'INPUT_RECORD_SIZE_LIMIT')
        self.assertEqual([], hostile.calls)

    def test_nonstring_record_key_is_rejected_before_collision_lookup(self):
        calls = []
        class Key:
            armed = False
            def __hash__(self):
                if self.armed: calls.append('hash'); raise AssertionError('key hash called')
                return hash('bits')
            def __eq__(self, other):
                if self.armed: calls.append('eq'); raise AssertionError('key comparison called')
                return False
        key = Key()
        candidate = {key: [0] * 9, 'state_space': 'F2^9'}
        key.armed = True
        self.assert_rejected(candidate, 'INPUT_RECORD_KEY_INVALID')
        self.assertEqual([], calls)

    def test_capture_preview_observations_and_surrogates_are_bounded_and_json_safe(self):
        for length in [64, 65]:
            record = self.assert_rejected(['x' * length] + [0] * 8, 'STATE_COORDINATE_TYPE')
            observation = record['coordinate_observations'][0]
            self.assertEqual('STRING', observation['scalar_kind'])
            self.assertEqual('x' * min(length, 64), observation['value'])
            self.assertIs(length > 64, observation['truncated'])
        record = self.assert_rejected(br'["\ud800",0,0,0,0,0,0,0,0]', 'STATE_COORDINATE_TYPE')
        json.dumps(record, ensure_ascii=True, allow_nan=False).encode('utf-8')
        self.assert_rejected('\ud800', 'INPUT_UTF8_INVALID')
        for length in [8, 10]:
            record = self.assert_rejected([0] * length, 'STATE_WIDTH')
            self.assertLessEqual(len(record['coordinate_observations']), 9)

    def test_raw_parser_recursion_error_is_retained_as_stable_candidate_rejection(self):
        # Injection at the stdlib parser boundary proves the unhappy path, without
        # relying on a platform recursion limit or weakening the explicit depth limit.
        with mock.patch('json.loads', side_effect=RecursionError('private parser detail')):
            record = self.assert_rejected(b'[0,0,0,0,0,0,0,0,0]', 'INPUT_JSON_INVALID')
        self.assertNotIn('private parser detail', json.dumps(record))


class StateDiagnosisAndClassificationTests(ModelTestCase):
    def test_all_1536_profile_vertices_match_independent_integer_orbit_expectations(self):
        codewords = independently_read_codewords()
        profiles = [('wrw_reference_profile', wrw_signatures()),
                    ('ywe.validation.neutral-origin.v1', ('000000000',)),
                    ('ywe.validation.empty-known-set.v1', ())]
        observed_counts = {}
        for profile_id, signatures in profiles:
            binding = profile_binding(profile_id, signatures)
            known = {int(signature, 2) for signature in signatures}
            model = self.make_model(binding)
            counts = collections.Counter()
            for vertex in range(512):
                signature = format(vertex, '09b')
                orbit = sorted(vertex ^ word for word in codewords)
                expected = ('VALID' if vertex in known else 'TRANSFORMATION_COMPATIBLE'
                            if any(member in known for member in orbit) else 'TRANSFORMATION_INCOMPATIBLE')
                with self.subTest(profile=profile_id, state=signature):
                    context = diagnostic_context(profile_id + ':' + signature)
                    result = model.diagnose(list(map(int, signature)), diagnostic_context=context)
                    packet = result.to_record()
                    self.assertEqual('diagnosis', packet['outcome'])
                    self.assertNotIn('system_state_class', packet)
                    self.assertNotIn('recovery_category', packet)
                    diagnostic = self.assert_diagnosis(packet, expected)
                    self.assertEqual(list(map(int, signature)), diagnostic['input_state'])
                    self.assertEqual({'orbit_id': format(orbit[0], '09b'), 'member_count': 16,
                                      'contains_known_valid_state': any(member in known for member in orbit)},
                                     diagnostic['orbit_info'])
                    self.assertEqual(signature, ''.join(map(str, packet['parsed_state']['bits'])))
                    self.assert_chain(packet, 1)
                    counts[expected] += 1
            observed_counts[profile_id] = dict(counts)
        self.assertEqual({'VALID': 9, 'TRANSFORMATION_COMPATIBLE': 135, 'TRANSFORMATION_INCOMPATIBLE': 368},
                         observed_counts['wrw_reference_profile'])
        self.assertEqual({'VALID': 1, 'TRANSFORMATION_COMPATIBLE': 15, 'TRANSFORMATION_INCOMPATIBLE': 496},
                         observed_counts['ywe.validation.neutral-origin.v1'])
        self.assertEqual({'TRANSFORMATION_INCOMPATIBLE': 512}, observed_counts['ywe.validation.empty-known-set.v1'])

    def test_all_64_source_classification_cases_and_consulted_predicate_traces(self):
        binding = profile_binding()
        candidates = {'VALID': '100000000', 'TRANSFORMATION_COMPATIBLE': '100011110',
                      'TRANSFORMATION_INCOMPATIBLE': '000000000', 'UNCLASSIFIED': '00000000'}
        counts = collections.Counter()
        for status, candidate in candidates.items():
            for flag_index, flags in enumerate(itertools.product((False, True), repeat=4)):
                halt, containment, correction, fallback = flags
                reference = 'm3_matrix:' + status + ':' + str(flag_index)
                dc = diagnostic_context(reference)
                subject = dc.original_input_reference if status == 'UNCLASSIFIED' else 'ash_state_' + candidate
                supplied = evidence(binding, dc, subject, correction=correction, fallback=fallback)
                with self.subTest(status=status, flags=flags):
                    packet = self.make_model(binding).assess(candidate,
                        context=values.SystemContext(is_in_safe_halt=halt, is_in_containment=containment),
                        classification_evidence=supplied, diagnostic_context=dc).to_record()
                    expected = CLASS_MATRIX[status][flag_index]
                    self.assertEqual('assessment', packet['outcome'])
                    self.assertEqual(expected, packet['system_state_class'])
                    self.assertEqual(CATEGORIES[expected], packet['recovery_category'])
                    consulted = ([] if halt or containment else ['correction_path_is_known']
                                 if status == 'TRANSFORMATION_COMPATIBLE' else ['fallback_is_available']
                                 if status == 'TRANSFORMATION_INCOMPATIBLE' else [])
                    self.assertEqual(consulted, packet['consulted_predicates'])
                    self.assert_diagnosis(packet, status)
                    self.assert_chain(packet, 2)
                    self.assertEqual('CLASSIFICATION', packet['emitted_diagnostics'][1]['envelope']['stage'])
                    counts[expected] += 1
        self.assertEqual({'SAFE_HALT': 32, 'CONTAINED': 16, 'STABLE': 4, 'CORRECTABLE': 2,
                          'UNSTABLE': 2, 'DEGRADED': 6, 'FAILED': 2}, dict(counts))

    def test_empty_available_profile_and_unavailable_profile_are_distinct(self):
        empty = profile_binding('m3_test:empty', ())
        unavailable = values.UnavailableProfileBinding(evidence=values.UnavailableValidityProfileEvidence(
            profile_id='m3_test:unavailable', source_binding=source_binding('m3_test:unavailable', ()),
            reason_code='PROFILE_DATA_UNAVAILABLE', reason='Authoritative evaluation data unavailable in this fixture.'))
        for binding, expected in [(empty, 'TRANSFORMATION_INCOMPATIBLE'), (unavailable, 'UNCLASSIFIED')]:
            dc = diagnostic_context('m3_test:' + binding.to_record()['profile_id'])
            packet = self.make_model(binding).diagnose('000000000', diagnostic_context=dc).to_record()
            diagnostic = self.assert_diagnosis(packet, expected)
            self.assertEqual([0] * 9, diagnostic['input_state'])
            self.assertEqual({'state_space': 'F2^9', 'bits': [0] * 9}, packet['parsed_state'])
            if binding is unavailable:
                self.assertIsNone(diagnostic['orbit_info'])
                assessment = self.make_model(binding).assess('000000000',
                    context=values.SystemContext(False, False),
                    classification_evidence=evidence(binding, dc, 'ash_state_000000000'), diagnostic_context=dc).to_record()
                self.assertEqual('DEGRADED', assessment['system_state_class'])
                self.assertEqual([], assessment['consulted_predicates'])

    def test_malformed_candidate_has_complete_tagged_diagnosis_and_no_fake_vertex(self):
        dc = diagnostic_context('m3_test:malformed')
        packet = self.make_model().diagnose([0.9] + [0] * 8, diagnostic_context=dc).to_record()
        diagnostic = self.assert_diagnosis(packet, 'UNCLASSIFIED')
        self.assertIsNone(packet['parsed_state'])
        self.assertIsNone(diagnostic['orbit_info'])
        self.assertEqual('REJECTED', diagnostic['input_state']['candidate_kind'])
        self.assertEqual(packet['input_evidence'], diagnostic['input_state']['input_evidence'])
        self.assertEqual(dc.original_input_reference, packet['emitted_diagnostics'][0]['envelope']['subject_reference'])
        self.assertNotIn('vertex_id', diagnostic['input_state'])
        self.assertNotIn('bits', diagnostic['input_state'])

    def test_structural_configuration_failure_precedes_candidate_and_capture(self):
        capture = CaptureDouble()
        self.assert_code('PROFILE_BINDING_INVALID', StateModel, profile_binding=None,
                         canonical_binding=values.CanonicalAshBinding(**canonical_record()), diagnostic_capture=capture)
        self.assertEqual([], capture.begins)
        hostile = HostileValue()
        model = self.make_model(capture=capture)
        self.assert_code('DIAGNOSTIC_CONTEXT_INVALID', model.diagnose, hostile, diagnostic_context=None)
        dc = diagnostic_context()
        self.assert_code('CONTEXT_INVALID', model.assess, hostile, context=None,
                         classification_evidence=evidence(profile_binding(), dc, dc.original_input_reference), diagnostic_context=dc)
        self.assert_code('PREDICATE_EVIDENCE_INVALID', model.assess, hostile, context=values.SystemContext(False, False),
                         classification_evidence=None, diagnostic_context=dc)
        self.assertEqual([], hostile.calls)
        self.assertEqual([], capture.calls)

    def test_consulted_not_evaluated_fact_retains_acknowledged_detection(self):
        binding = profile_binding()
        for candidate, predicate in [('100011110', 'correction_path_is_known'), ('000000000', 'fallback_is_available')]:
            dc = diagnostic_context('m3_test:missing:' + candidate)
            capture = CaptureDouble()
            packet = self.make_model(binding, capture).assess(candidate, context=values.SystemContext(False, False),
                classification_evidence=evidence(binding, dc, 'ash_state_' + candidate), diagnostic_context=dc).to_record()
            self.assertEqual('failure', packet['outcome'])
            self.assertEqual('classification_evidence', packet['failure_kind'])
            self.assertEqual('PREDICATE_NOT_EVALUATED', packet['failure_code'])
            self.assertEqual(predicate, packet['failed_predicate'])
            self.assertEqual(1, len(capture.calls))
            self.assert_chain(packet, 1)
            self.assertNotIn('system_state_class', packet)
            self.assertNotIn('recovery_category', packet)
            self.assert_diagnosis(packet, 'TRANSFORMATION_COMPATIBLE' if candidate[0] == '1' else 'TRANSFORMATION_INCOMPATIBLE')

    def test_unconsulted_not_evaluated_facts_preserve_halt_containment_stable_default(self):
        binding = profile_binding()
        for candidate, halt, contained, expected in [('100000000', False, False, 'STABLE'),
                ('100011110', False, True, 'CONTAINED'), ('100011110', True, True, 'SAFE_HALT'),
                ('00000000', False, False, 'DEGRADED')]:
            dc = diagnostic_context('m3_test:unconsulted:' + expected)
            subject = dc.original_input_reference if len(candidate) != 9 else 'ash_state_' + candidate
            packet = self.make_model(binding).assess(candidate, context=values.SystemContext(halt, contained),
                classification_evidence=evidence(binding, dc, subject), diagnostic_context=dc).to_record()
            self.assertEqual(expected, packet['system_state_class'])
            self.assertEqual([], packet['consulted_predicates'])
            for fact in packet['classification_evidence'].values():
                self.assertEqual('NOT_EVALUATED', fact['evaluation'])
                self.assertNotIn('value', fact)

    def test_each_predicate_binding_mismatch_is_a_retaining_post_detection_failure(self):
        profile = profile_binding()
        dc = diagnostic_context('m3_test:mismatch')
        good_binding = predicate_binding(profile, dc, 'ash_state_100011110', 'correction_path_is_known')
        for field, wrong in [('assessment_reference', 'm3_test:other_assessment'),
                             ('diagnosis_reference', 'm3_test:other_diagnosis'),
                             ('subject_reference', 'ash_state_100000000'), ('profile_id', 'm3_test:other_profile'),
                             ('profile_source_sha256', '0' * 64), ('ash_dependency_id', DEPENDENCY + '.other'),
                             ('ash_aggregate_sha256', '0' * 64)]:
            with self.subTest(field=field):
                altered = good_binding.to_record(); altered[field] = wrong
                facts = values.ClassificationEvidence(
                    correction_path_is_known=values.EvaluatedPredicate(binding=values.PredicateBinding(**altered), value=True),
                    fallback_is_available=evidence(profile, dc, 'ash_state_100011110').fallback_is_available)
                packet = self.make_model(profile).assess('100011110', context=values.SystemContext(False, False),
                    classification_evidence=facts, diagnostic_context=dc).to_record()
                self.assertEqual('classification_evidence', packet['failure_kind'])
                self.assertEqual('PREDICATE_BINDING_MISMATCH', packet['failure_code'])
                self.assertEqual('correction_path_is_known', packet['failed_predicate'])
                self.assert_chain(packet, 1)
                self.assertNotIn('system_state_class', packet)

    def test_mismatched_unconsulted_fact_is_not_accepted_as_bound_evidence(self):
        profile = profile_binding(); dc = diagnostic_context('m3_test:unconsulted_mismatch')
        good = evidence(profile, dc, 'ash_state_100000000')
        bad = good.fallback_is_available.binding.to_record(); bad['profile_id'] = 'm3_test:other'
        facts = values.ClassificationEvidence(correction_path_is_known=good.correction_path_is_known,
                fallback_is_available=values.NotEvaluatedPredicate(binding=values.PredicateBinding(**bad), reason='Irrelevant but must be bound.'))
        packet = self.make_model(profile).assess('100000000', context=values.SystemContext(False, False),
                    classification_evidence=facts, diagnostic_context=dc).to_record()
        self.assertEqual('PREDICATE_BINDING_MISMATCH', packet['failure_code'])
        self.assert_chain(packet, 1)

    def test_result_records_are_fresh_and_candidate_mutation_cannot_change_retained_state(self):
        original = [1] + [0] * 8
        result = self.make_model().diagnose(original, diagnostic_context=diagnostic_context())
        before = result.to_record()
        original[0] = 0
        self.assertEqual(before, result.to_record())
        changed = result.to_record()
        changed['parsed_state']['bits'][0] = 0
        changed['state_validity_diagnostic']['notes'].clear()
        changed['emitted_diagnostics'][0]['envelope']['notes'].clear()
        self.assertEqual(before, result.to_record())

    def test_incoherent_semantic_diagnostic_rows_fail_at_the_value_owner(self):
        state = values.AshState([1] + [0] * 8)
        original = dict(input_state=state, admissibility_status='VALID', transformation_compatibility='COMPATIBLE',
                        normalization_status='ALREADY_VALID', recoverability_relevance='NO_RECOVERY_NEEDED', is_valid=True,
                        orbit_info=values.OrbitInfo('000101100', 16, True),
                        rule_ids=['ASH-STATE-VALIDITY-001'], notes=['Complete coherent source row.'])
        for field, wrong in [('admissibility_status', 'TRANSFORMATION_INCOMPATIBLE'),
                ('transformation_compatibility', 'UNKNOWN'), ('normalization_status', 'BLOCKED'),
                ('recoverability_relevance', 'FALLBACK_NEEDED'), ('is_valid', False)]:
            altered = dict(original); altered[field] = wrong
            with self.subTest(field=field):
                self.assert_code('DIAGNOSTIC_ROW_INVALID', values.StateValidityDiagnostic, **altered)


class DiagnosticCaptureTests(ModelTestCase):
    def assess_with(self, capture, reference='m3_test:capture'):
        binding = profile_binding(); dc = diagnostic_context(reference)
        return self.make_model(binding, capture).assess('100000000', context=values.SystemContext(False, False),
                classification_evidence=evidence(binding, dc, 'ash_state_100000000'), diagnostic_context=dc)

    def test_success_is_two_immediately_acknowledged_records_not_duplicate_detection(self):
        capture = CaptureDouble()
        result = self.assess_with(capture)
        packet = result.to_record()
        self.assertEqual('assessment', packet['outcome'])
        self.assertEqual(['m3_test:capture'], capture.begins)
        self.assertEqual(2, len(capture.calls))
        self.assertEqual([emission.to_record() for emission in capture.stored], packet['emitted_diagnostics'])
        self.assert_chain(packet, 2)

    def test_begin_throw_retains_complete_detection_and_never_attempts_append(self):
        class BeginFailure(CaptureDouble):
            def begin(self, assessment_reference):
                self.begins.append(assessment_reference)
                raise RuntimeError('private begin detail')
        capture = BeginFailure()
        packet = self.assess_with(capture).to_record()
        self.assertEqual('diagnostic_capture', packet['failure_kind'])
        self.assertEqual('NOT_CONFIRMED', packet['capture_status'])
        self.assertEqual('DIAGNOSTIC_CAPTURE_UNCONFIRMED', packet['failure_code'])
        self.assertEqual([], packet['emitted_diagnostics'])
        self.assertEqual([], capture.calls)
        self.assertEqual([], capture.stored)
        self.assertEqual('DETECTION', packet['attempted_diagnostic']['envelope']['stage'])
        self.assertEqual(ENVELOPE_FIELDS, set(packet['attempted_diagnostic']['envelope']))
        self.assert_diagnosis(packet, 'VALID')
        self.assertNotIn('private begin detail', json.dumps(packet))

    def test_real_recording_capture_has_fresh_scopes_and_rejects_bad_order_without_append(self):
        producer = CaptureDouble()
        self.assess_with(producer)
        detection, classification = producer.calls
        real = RecordingDiagnosticCapture()
        scope = real.begin('m3_test:capture')
        self.assertEqual('REJECTED', scope.append(classification).status)
        self.assertEqual('CONFIRMED', scope.append(detection).status)
        wrong_parent = dataclasses.replace(classification,
            envelope=dataclasses.replace(classification.envelope, parent_diagnostic_reference='m3_test:wrong_parent'))
        self.assertEqual('REJECTED', scope.append(wrong_parent).status)
        self.assertEqual('CONFIRMED', scope.append(classification).status)
        self.assertEqual('REJECTED', scope.append(classification).status)
        fresh = real.begin('m3_test:capture')
        self.assertEqual('CONFIRMED', fresh.append(detection).status)
        self.assertEqual('CONFIRMED', fresh.append(classification).status)

    def test_real_recording_capture_does_not_accumulate_between_actual_model_calls(self):
        real = RecordingDiagnosticCapture()
        profile = profile_binding(); model = self.make_model(profile, real)
        first = None
        for invocation in range(3):
            dc = diagnostic_context('m3_test:real:' + str(invocation))
            packet = model.assess('100000000', context=values.SystemContext(False, False),
                classification_evidence=evidence(profile, dc, 'ash_state_100000000'), diagnostic_context=dc).to_record()
            self.assertEqual('assessment', packet['outcome'])
            self.assert_chain(packet, 2)
            self.assertEqual(dc.detection_reference, packet['emitted_diagnostics'][0]['diagnostic_reference'])
            if first is None: first = packet
            else: self.assertNotEqual(first['assessment_binding'], packet['assessment_binding'])

    def test_throw_before_or_after_append_never_certifies_the_attempt(self):
        for stage_index in [1, 2]:
            for mode in ['throw_before', 'append_then_throw']:
                with self.subTest(stage_index=stage_index, mode=mode):
                    capture = CaptureDouble(failure_at=stage_index, mode=mode)
                    packet = self.assess_with(capture).to_record()
                    self.assertEqual('failure', packet['outcome'])
                    self.assertEqual('diagnostic_capture', packet['failure_kind'])
                    self.assertEqual('DIAGNOSTIC_CAPTURE_UNCONFIRMED', packet['failure_code'])
                    self.assertEqual('NOT_CONFIRMED', packet['capture_status'])
                    self.assertEqual(stage_index, len(capture.calls))
                    self.assertEqual(capture.calls[-1].to_record(), packet['attempted_diagnostic'])
                    self.assertEqual([item.to_record() for item in capture.calls[:stage_index - 1]], packet['emitted_diagnostics'])
                    self.assert_chain(packet, stage_index - 1)
                    self.assertNotIn('system_state_class', packet)
                    self.assertNotIn('recovery_category', packet)
                    self.assertEqual(stage_index if mode == 'append_then_throw' else stage_index - 1, len(capture.stored))
                    self.assert_diagnosis(packet, 'VALID')
                    self.assertNotIn('collector private detail', json.dumps(packet))

    def test_valid_rejected_receipt_guarantees_no_append_and_preserves_prior_prefix(self):
        for stage_index in [1, 2]:
            capture = CaptureDouble(failure_at=stage_index, mode='reject')
            packet = self.assess_with(capture).to_record()
            self.assertEqual('REJECTED', packet['capture_status'])
            self.assertEqual('DIAGNOSTIC_CAPTURE_REJECTED', packet['failure_code'])
            self.assertEqual(stage_index - 1, len(capture.stored))
            self.assertEqual([item.to_record() for item in capture.stored], packet['emitted_diagnostics'])
            self.assertEqual(capture.calls[-1].to_record(), packet['attempted_diagnostic'])
            self.assert_chain(packet, stage_index - 1)

    def test_invalid_missing_and_wrong_reference_receipts_are_unconfirmed(self):
        for stage_index in [1, 2]:
            for mode in ['malformed_receipt', 'wrong_reference', 'wrong_rejected_reference', 'not_confirmed']:
                with self.subTest(stage_index=stage_index, mode=mode):
                    capture = CaptureDouble(failure_at=stage_index, mode=mode)
                    packet = self.assess_with(capture).to_record()
                    self.assertEqual('NOT_CONFIRMED', packet['capture_status'])
                    self.assertEqual('DIAGNOSTIC_CAPTURE_UNCONFIRMED', packet['failure_code'])
                    self.assertEqual(stage_index - 1, len(packet['emitted_diagnostics']))
                    self.assertEqual(capture.calls[-1].to_record(), packet['attempted_diagnostic'])
                    self.assertNotIn('system_state_class', packet)

    def test_diagnosis_only_capture_failure_has_no_fabricated_context_or_evidence(self):
        capture = CaptureDouble(failure_at=1, mode='append_then_throw')
        packet = self.make_model(capture=capture).diagnose('100000000', diagnostic_context=diagnostic_context()).to_record()
        self.assertIsNone(packet['system_context'])
        self.assertIsNone(packet['classification_evidence'])
        self.assertEqual([], packet['emitted_diagnostics'])
        self.assertEqual('DETECTION', packet['attempted_diagnostic']['envelope']['stage'])
        self.assertNotIn('system_state_class', packet)

    def test_detected_nonconformance_rejects_append_and_preserves_complete_attempt(self):
        class RejectNonconformance(CaptureDouble):
            def append(self, emission):
                self.calls.append(emission)
                return values.CaptureReceipt(diagnostic_reference=emission.diagnostic_reference, status='REJECTED')
        capture = RejectNonconformance()
        packet = self.assess_with(capture).to_record()
        self.assertEqual('REJECTED', packet['capture_status'])
        self.assertEqual([], capture.stored)
        self.assertEqual(capture.calls[0].to_record(), packet['attempted_diagnostic'])
        self.assertEqual(ENVELOPE_FIELDS, set(packet['attempted_diagnostic']['envelope']))
        self.assert_diagnosis(packet, 'VALID')


class DiagnosticValueBoundaryTests(ModelTestCase):
    def envelope_arguments(self):
        return dict(diagnostic_kind='STATE_VALIDITY', severity='INFO', stage='DETECTION', disposition='RESOLVED',
                    subject_reference='ash_state_100000000', parent_diagnostic_reference=None,
                    chain_root_reference='m3_test:detection', rule_ids=['ASH-STATE-VALIDITY-001'],
                    summary='Complete bounded source diagnosis.', notes=['Owned explanatory observation.'])

    def test_envelope_summary_and_note_limits_at_exact_boundaries(self):
        args = self.envelope_arguments(); args['summary'] = 's' * 512; args['notes'] = ['n' * 512] * 8
        record = values.DiagnosticEnvelope(**args).to_record()
        self.assertEqual(512, len(record['summary']))
        self.assertEqual(8, len(record['notes']))
        for summary in ('a b', 'a\tb'):
            accepted = self.envelope_arguments(); accepted['summary'] = summary
            self.assertEqual(summary, values.DiagnosticEnvelope(**accepted).summary)
        for field, wrong in [('summary', ''), ('summary', 's' * 513), ('summary', 'a\nb'),
                ('summary', 'a\rb'), ('summary', 'a\vb'), ('summary', 'a\fb'),
                ('summary', 'a\x1cb'), ('summary', 'a\x1db'), ('summary', 'a\x1eb'),
                ('summary', 'a\u0085b'), ('summary', 'a\u2028b'),
                ('summary', 'a\u2029b'), ('notes', []), ('notes', ['']), ('notes', ['n' * 513]), ('notes', ['n'] * 9)]:
            altered = self.envelope_arguments(); altered[field] = wrong
            with self.subTest(field=field, wrong_kind=type(wrong).__name__):
                error = self.assert_code('DIAGNOSTIC_ENVELOPE_INVALID', values.DiagnosticEnvelope, **altered)
                self.assertEqual(field, error.field_name)

    def test_envelope_rule_count_format_and_explicit_uppercase_enums(self):
        five = ['ASH-STATE-STRUCTURE-001', 'ASH-ADMISSIBILITY-CLASSIFICATION-001', 'ASH-STATE-VALIDITY-001',
                'ASH-CLASSIFICATION-MAPPING-001', 'ASH-RECOVERY-ACTION-001']
        args = self.envelope_arguments(); args['rule_ids'] = five
        self.assertEqual(five, values.DiagnosticEnvelope(**args).to_record()['rule_ids'])
        for field, wrong in [('rule_ids', []), ('rule_ids', ['not-a-rule']),
                ('rule_ids', five + ['ASH-STATE-GENERAL-001']), ('severity', 'info'), ('severity', 1),
                ('stage', 'detection'), ('disposition', 'resolved'), ('diagnostic_kind', 'state_validity')]:
            altered = self.envelope_arguments(); altered[field] = wrong
            with self.subTest(field=field):
                self.assert_code('DIAGNOSTIC_ENVELOPE_INVALID', values.DiagnosticEnvelope, **altered)

    def test_envelope_constructor_owns_rule_and_note_arrays(self):
        args = self.envelope_arguments()
        envelope = values.DiagnosticEnvelope(**args)
        args['rule_ids'].clear(); args['notes'].clear()
        record = envelope.to_record()
        self.assertEqual(['ASH-STATE-VALIDITY-001'], record['rule_ids'])
        self.assertTrue(record['notes'])
        record['notes'].clear()
        self.assertTrue(envelope.to_record()['notes'])

    def test_evaluated_predicate_rejects_integer_truthiness(self):
        profile = profile_binding(); dc = diagnostic_context()
        binding = predicate_binding(profile, dc, 'ash_state_100000000', 'correction_path_is_known')
        for wrong in [0, 1, 'true', None]:
            self.assert_code('PREDICATE_EVIDENCE_INVALID', values.EvaluatedPredicate, binding=binding, value=wrong)

    def test_profile_identifier_bounds_and_unavailable_reason_are_owned(self):
        source = source_binding('m3_test:source', ())
        for length in [1, 256]:
            profile = values.ValidityProfile(profile_id='p' * length, source_binding=source, recognized_valid_states=[])
            self.assertEqual('p' * length, profile.to_record()['profile_id'])
        for wrong in ['', 'p' * 257, 'profile id', 'é']:
            self.assert_code('PROFILE_BINDING_INVALID', values.ValidityProfile,
                             profile_id=wrong, source_binding=source, recognized_valid_states=[])
        args = dict(profile_id='m3_test:unavailable', source_binding=source,
                    reason_code='PROFILE_DATA_UNAVAILABLE', reason='r' * 512)
        self.assertEqual(512, len(values.UnavailableValidityProfileEvidence(**args).to_record()['reason']))
        for wrong in ['', 'r' * 513]:
            altered = dict(args); altered['reason'] = wrong
            self.assert_code('PROFILE_BINDING_INVALID', values.UnavailableValidityProfileEvidence, **altered)

    def test_classified_rows_require_complete_and_matching_orbit_evidence(self):
        for status in ['VALID', 'TRANSFORMATION_COMPATIBLE', 'TRANSFORMATION_INCOMPATIBLE']:
            compatibility, normalization, relevance, is_valid = ROWS[status]
            contains = status != 'TRANSFORMATION_INCOMPATIBLE'
            args = dict(input_state=values.AshState([1] + [0] * 8), admissibility_status=status,
                transformation_compatibility=compatibility, normalization_status=normalization,
                recoverability_relevance=relevance, is_valid=is_valid,
                orbit_info=values.OrbitInfo('000101100', 16, contains),
                rule_ids=['ASH-STATE-VALIDITY-001'], notes=['Explicit complete orbit observation.'])
            self.assertEqual(contains, values.StateValidityDiagnostic(**args).to_record()['orbit_info']['contains_known_valid_state'])
            for wrong in [None, values.OrbitInfo('000101100', 16, not contains)]:
                altered = dict(args); altered['orbit_info'] = wrong
                with self.subTest(status=status, missing=wrong is None):
                    self.assert_code('DIAGNOSTIC_ROW_INVALID', values.StateValidityDiagnostic, **altered)

    def test_available_profile_cannot_construct_unknown_diagnosis_for_well_formed_state(self):
        available = profile_binding()
        unavailable = values.UnavailableProfileBinding(values.UnavailableValidityProfileEvidence(
            profile_id=available.profile_id, source_binding=available.source_binding,
            reason_code='PROFILE_DATA_UNAVAILABLE', reason='Authoritative source unavailable in this fixture.'))
        result = self.make_model(unavailable).diagnose('100000000', diagnostic_context=diagnostic_context())
        self.assertEqual('UNCLASSIFIED', result.state_validity_diagnostic.admissibility_status)
        self.assertEqual('100000000', result.parsed_state.signature)
        failure = self.assert_code('DIAGNOSTIC_ROW_INVALID', dataclasses.replace, result, profile_binding=available)
        self.assertEqual('profile_binding', failure.field_name)

    def test_mismatch_failure_constructor_requires_the_named_fact_to_be_mismatched(self):
        profile = profile_binding(); dc = diagnostic_context('m3_test:failure_honesty')
        matching = evidence(profile, dc, 'ash_state_100011110', True, False)
        bad_binding = dataclasses.replace(matching.correction_path_is_known.binding, profile_id='m3_test:wrong_profile')
        mismatched = values.ClassificationEvidence(
            values.EvaluatedPredicate(bad_binding, True), matching.fallback_is_available)
        result = self.make_model(profile).assess('100011110', context=values.SystemContext(False, False),
            classification_evidence=mismatched, diagnostic_context=dc)
        self.assertEqual('PREDICATE_BINDING_MISMATCH', result.failure_code)
        self.assertEqual('correction_path_is_known', result.failed_predicate)
        self.assertEqual('m3_test:wrong_profile', result.classification_evidence.correction_path_is_known.binding.profile_id)
        self.assert_chain(result.to_record(), 1)
        for changed in [dict(classification_evidence=matching), dict(failed_predicate='fallback_is_available')]:
            with self.subTest(changed=next(iter(changed))):
                failure = self.assert_code('PREDICATE_EVIDENCE_INVALID', dataclasses.replace, result, **changed)
                self.assertEqual('failed_predicate', failure.field_name)

    def test_input_evidence_constructor_owns_representation_units_and_previews(self):
        common = dict(original_input_reference='m3_test:input', truncated=False,
                      coordinate_observations=[], failure_code=None)
        examples = [
            dict(representation_kind='RAW_JSON', observed_length=4096, length_unit='BYTES', preview='5b5d', preview_encoding='HEX'),
            dict(representation_kind='SIGNATURE', observed_length=9, length_unit='CHARACTERS', preview='100000000', preview_encoding='TEXT'),
            dict(representation_kind='BIT_SEQUENCE', observed_length=9, length_unit='ELEMENTS', preview=None, preview_encoding='TEXT'),
            dict(representation_kind='STATE_RECORD', observed_length=64, length_unit='KEYS', preview=None, preview_encoding='TEXT'),
            dict(representation_kind='UNSUPPORTED', observed_length=None, length_unit='UNKNOWN', preview=None,
                 preview_encoding='TEXT', failure_code='INPUT_KIND_UNSUPPORTED'),
        ]
        for example in examples:
            args = {**common, **example}
            self.assertEqual(example['representation_kind'], values.InputEvidence(**args).representation_kind)
            invalid = [('length_unit', 'KEYS' if example['length_unit'] != 'KEYS' else 'BYTES')]
            if example['representation_kind'] in ('RAW_JSON', 'SIGNATURE'):
                invalid.extend([('preview', None), ('observed_length', None),
                    ('preview_encoding', 'TEXT' if example['preview_encoding'] == 'HEX' else 'HEX'),
                    ('coordinate_observations', [values.CoordinateObservation(0, 'INTEGER_BIT', value=0)])])
            elif example['representation_kind'] == 'UNSUPPORTED':
                invalid.extend([('failure_code', None), ('failure_code', 'STATE_WIDTH'), ('observed_length', 0)])
            else:
                invalid.extend([('preview', 'unowned preview'), ('preview_encoding', 'HEX'), ('observed_length', None)])
            for field, wrong in invalid:
                altered = dict(args); altered[field] = wrong
                with self.subTest(kind=example['representation_kind'], field=field):
                    self.assert_code('DIAGNOSTIC_ROW_INVALID', values.InputEvidence, **altered)

    def test_input_evidence_acceptance_bounds_cannot_certify_oversized_representation(self):
        common = dict(original_input_reference='m3_test:input', preview_encoding='TEXT', truncated=True,
                      coordinate_observations=[], failure_code=None)
        cases = [
            ('RAW_JSON', 'BYTES', 4096, 4097, '', 'HEX'),
            ('SIGNATURE', 'CHARACTERS', 4096, 4097, '1' * 64, 'TEXT'),
            ('BIT_SEQUENCE', 'ELEMENTS', 9, 8, None, 'TEXT'),
            ('STATE_RECORD', 'KEYS', 64, 65, None, 'TEXT'),
        ]
        for kind, unit, boundary, overflow, preview, encoding in cases:
            args = {**common, 'representation_kind': kind, 'length_unit': unit,
                    'observed_length': boundary, 'preview': preview, 'preview_encoding': encoding}
            self.assertEqual(boundary, values.InputEvidence(**args).observed_length)
            altered = {**args, 'observed_length': overflow}
            with self.subTest(kind=kind):
                failure = self.assert_code('DIAGNOSTIC_ROW_INVALID', values.InputEvidence, **altered)
                self.assertEqual('observed_length', failure.field_name)
        args = {**common, 'representation_kind': 'STATE_RECORD', 'length_unit': 'KEYS',
                'observed_length': 1, 'preview': None}
        self.assert_code('DIAGNOSTIC_ROW_INVALID', values.InputEvidence, **args)

    def test_model_configuration_rejects_hostile_metaclass_without_equality_hooks(self):
        hostile = HostileMetaValue(); capture = CaptureDouble()
        profile = profile_binding(); canonical = values.CanonicalAshBinding(**canonical_record())
        HostileMetaclass.calls.clear()
        self.assert_code('PROFILE_BINDING_INVALID', StateModel, profile_binding=hostile,
                         canonical_binding=canonical, diagnostic_capture=capture)
        self.assert_code('CANONICAL_BINDING_INVALID', StateModel, profile_binding=profile,
                         canonical_binding=hostile, diagnostic_capture=capture)
        model = self.make_model(profile, capture); dc = diagnostic_context()
        self.assert_code('DIAGNOSTIC_CONTEXT_INVALID', model.diagnose, '100000000', diagnostic_context=hostile)
        self.assert_code('CONTEXT_INVALID', model.assess, '100000000', context=hostile,
                         classification_evidence=evidence(profile, dc, 'ash_state_100000000'), diagnostic_context=dc)
        self.assert_code('PREDICATE_EVIDENCE_INVALID', model.assess, '100000000', context=values.SystemContext(False, False),
                         classification_evidence=hostile, diagnostic_context=dc)
        self.assertEqual([], HostileMetaclass.calls)
        self.assertEqual([], capture.begins)


class StateAssessmentWireSchemaTests(ModelTestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'data/schemas/m3_state_assessment_schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.retrievals = []
        def deny(uri):
            cls.retrievals.append(uri)
            raise AssertionError('Wire validation must resolve locally: ' + uri)
        cls.validator = Draft202012Validator(cls.schema, registry=Registry(retrieve=deny))
        cls.authored = json.loads((ROOT / 'examples/core_state_assessment/state_assessment_cases.example.json').read_text(encoding='utf-8'))

    def assert_wire_valid(self, packet):
        errors = list(self.validator.iter_errors(packet))
        self.assertEqual([], errors, '\n'.join(error.message for error in errors))
        self.assertEqual([], self.retrievals)

    def assert_wire_rejected(self, packet, keyword, instance_path):
        errors = list(self.validator.iter_errors(packet))
        self.assertTrue(errors, 'Intended structural rejection escaped')
        def witnesses(error):
            return {(error.validator, tuple(error.absolute_path))} | set().union(
                *(witnesses(child) for child in error.context))
        observed = set().union(*(witnesses(error) for error in errors))
        self.assertIn((keyword, instance_path), observed)
        self.assertEqual([], self.retrievals)

    def test_all_20_independently_authored_packets_validate_offline(self):
        self.assertEqual(20, len(self.authored))
        outcomes = collections.Counter()
        for index, packet in enumerate(self.authored):
            with self.subTest(index=index):
                self.assert_wire_valid(packet)
                outcomes[(packet['outcome'], packet.get('failure_kind'))] += 1
        self.assertEqual({('diagnosis', None), ('assessment', None), ('failure', 'classification_evidence'),
                          ('failure', 'diagnostic_capture')}, set(outcomes))

    def test_all_68_authored_structural_mutations_fail_for_owned_keywords(self):
        base = self.authored[0]
        assessment = next(p for p in self.authored if p.get('system_state_class') == 'CORRECTABLE')
        failure = next(p for p in self.authored if p.get('capture_status') == 'NOT_CONFIRMED'
                       and p['attempted_diagnostic']['envelope']['stage'] == 'CLASSIFICATION')
        common = ['schema_ref', 'artifact_type', 'artifact_version', 'outcome', 'assessment_binding',
                  'source_binding', 'profile_binding', 'input_evidence', 'parsed_state',
                  'state_validity_diagnostic', 'emitted_diagnostics']
        mutations = [
            ('unknown-root-field', base, lambda p: p.update(unknown=True), 'unevaluatedProperties', ()),
            ('diagnosis-invents-class', base, lambda p: p.update(system_state_class='STABLE'), 'unevaluatedProperties', ()),
        ]
        for field in common:
            mutations.append(('missing-' + field, base, lambda p, field=field: p.pop(field), 'required', ()))
        for field in sorted(VALIDITY_FIELDS):
            mutations.append(('missing-validity-' + field, base,
                lambda p, field=field: p['state_validity_diagnostic'].pop(field), 'required', ('state_validity_diagnostic',)))
        for field in sorted(ENVELOPE_FIELDS):
            mutations.append(('missing-envelope-' + field, base,
                lambda p, field=field: p['emitted_diagnostics'][0]['envelope'].pop(field), 'required', ('emitted_diagnostics', 0, 'envelope')))
        mutations.extend([
            ('bit-boolean', base, lambda p: p['parsed_state']['bits'].__setitem__(0, True), 'type', ('parsed_state', 'bits', 0)),
            ('bit-fraction', base, lambda p: p['parsed_state']['bits'].__setitem__(0, 0.9), 'type', ('parsed_state', 'bits', 0)),
            ('bit-quoted', base, lambda p: p['parsed_state']['bits'].__setitem__(0, '1'), 'type', ('parsed_state', 'bits', 0)),
            ('bit-width-eight', base, lambda p: p['parsed_state']['bits'].pop(), 'minItems', ('parsed_state', 'bits')),
            ('valid-row-false-summary', base, lambda p: p['state_validity_diagnostic'].update(is_valid=False), 'const', ('state_validity_diagnostic', 'is_valid')),
            ('wrong-normalization-row', base, lambda p: p['state_validity_diagnostic'].update(normalization_status='BLOCKED'), 'const', ('state_validity_diagnostic', 'normalization_status')),
            ('numeric-severity-m2-shape', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(severity=1), 'enum', ('emitted_diagnostics', 0, 'envelope', 'severity')),
            ('lowercase-severity-other-format', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(severity='info'), 'enum', ('emitted_diagnostics', 0, 'envelope', 'severity')),
            ('zero-emissions-for-diagnosis', base, lambda p: p.update(emitted_diagnostics=[]), 'minItems', ('emitted_diagnostics',)),
            ('summary-empty', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary=''), 'minLength', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-newline', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\nline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-carriage-return', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\rline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-vertical-tab', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\vline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-form-feed', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\fline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-file-separator', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\x1cline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-group-separator', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\x1dline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-record-separator', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\x1eline2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-next-line', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\u0085line2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-line-separator', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\u2028line2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-paragraph-separator', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='line1\u2029line2'), 'not', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('summary-overflow', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(summary='a' * 513), 'maxLength', ('emitted_diagnostics', 0, 'envelope', 'summary')),
            ('notes-empty', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(notes=[]), 'minItems', ('emitted_diagnostics', 0, 'envelope', 'notes')),
            ('notes-overflow', base, lambda p: p['emitted_diagnostics'][0]['envelope'].update(notes=['a'] * 9), 'maxItems', ('emitted_diagnostics', 0, 'envelope', 'notes')),
            ('preview-overflow', base, lambda p: p['input_evidence'].update(preview='x' * 65), 'maxLength', ('input_evidence', 'preview')),
            ('class-category-mismatch', assessment, lambda p: p.update(recovery_category='NO_ACTION'), 'const', ('recovery_category',)),
            ('class-needs-consulted-fact', assessment,
                lambda p: p['classification_evidence']['correction_path_is_known'].update(value=False), 'const', ('classification_evidence', 'correction_path_is_known', 'value')),
            ('class-wrong-context', assessment, lambda p: p['system_context'].update(is_in_safe_halt=True), 'const', ('system_context', 'is_in_safe_halt')),
            ('context-not-boolean', assessment, lambda p: p['system_context'].update(is_in_containment=0), 'type', ('system_context', 'is_in_containment')),
            ('assessment-one-emission', assessment, lambda p: p['emitted_diagnostics'].pop(), 'minItems', ('emitted_diagnostics',)),
            ('assessment-wrong-stage', assessment,
                lambda p: p['emitted_diagnostics'][1]['envelope'].update(stage='DETECTION'), 'const', ('emitted_diagnostics', 1, 'envelope', 'stage')),
            ('wrong-consulted-trace', assessment, lambda p: p.update(consulted_predicates=['fallback_is_available']), 'const', ('consulted_predicates',)),
            ('failure-invents-class', failure, lambda p: p.update(system_state_class='STABLE'), 'unevaluatedProperties', ()),
            ('failure-claims-confirmed', failure, lambda p: p.update(capture_status='CONFIRMED'), 'enum', ('capture_status',)),
            ('failure-code-status-mismatch', failure, lambda p: p.update(capture_status='REJECTED'), 'const', ('failure_code',)),
            ('failure-loses-attempt', failure, lambda p: p.pop('attempted_diagnostic'), 'required', ()),
            ('failure-prefix-too-long', failure,
                lambda p: p['emitted_diagnostics'].append(copy.deepcopy(p['attempted_diagnostic'])), 'maxItems', ('emitted_diagnostics',)),
        ])
        self.assertEqual(68, len(mutations))
        for summary in ('a b', 'a\tb', 's' * 512):
            accepted = copy.deepcopy(base)
            accepted['emitted_diagnostics'][0]['envelope']['summary'] = summary
            self.assert_wire_valid(accepted)
        for name, original, mutate, keyword, instance_path in mutations:
            with self.subTest(case=name):
                altered = copy.deepcopy(original); mutate(altered)
                self.assert_wire_rejected(altered, keyword, instance_path)

    def test_newline_and_trailing_control_cannot_escape_identifier_hash_or_signature(self):
        for suffix in ['\n', '\r', '\t', '\x00']:
            for path in [('assessment_binding', 'assessment_reference'),
                         ('profile_binding', 'profile_id'),
                         ('profile_binding', 'source_binding', 'source_sha256'),
                         ('state_validity_diagnostic', 'orbit_info', 'orbit_id')]:
                altered = copy.deepcopy(self.authored[0]); parent = altered
                for key in path[:-1]: parent = parent[key]
                parent[path[-1]] += suffix
                with self.subTest(path=path, suffix=ord(suffix)):
                    self.assertTrue(list(self.validator.iter_errors(altered)))

    def test_actual_producer_packets_validate_for_diagnosis_assessment_and_failure_classes(self):
        profile = profile_binding()
        for candidate in ['100000000', '100011110', '000000000', [0.9] + [0] * 8,
                          {'state_space': 'F2^9', 'bits': [1] + [0] * 8, 'metadata': HostileValue()}]:
            packet = self.make_model(profile).diagnose(candidate, diagnostic_context=diagnostic_context()).to_record()
            self.assert_wire_valid(packet)
        for status, candidate in [('VALID', '100000000'), ('TRANSFORMATION_COMPATIBLE', '100011110'),
                                  ('TRANSFORMATION_INCOMPATIBLE', '000000000'), ('UNCLASSIFIED', '00000000')]:
            for index, (halt, contained, correction, fallback) in enumerate(itertools.product((False, True), repeat=4)):
                dc = diagnostic_context('m3_wire_actual:' + status + ':' + str(index))
                subject = dc.original_input_reference if status == 'UNCLASSIFIED' else 'ash_state_' + candidate
                packet = self.make_model(profile).assess(candidate, context=values.SystemContext(halt, contained),
                    classification_evidence=evidence(profile, dc, subject, correction, fallback), diagnostic_context=dc).to_record()
                self.assert_wire_valid(packet)
        for candidate in ['100011110', '000000000']:
            dc = diagnostic_context('m3_wire_actual:missing:' + candidate)
            facts = evidence(profile, dc, 'ash_state_' + candidate)
            packet = self.make_model(profile).assess(candidate, context=values.SystemContext(False, False),
                    classification_evidence=facts, diagnostic_context=dc).to_record()
            self.assertEqual('classification_evidence', packet['failure_kind'])
            self.assert_wire_valid(packet)
        dc = diagnostic_context('m3_wire_actual:mismatch')
        facts = evidence(profile, dc, 'ash_state_100011110', True)
        binding = facts.correction_path_is_known.binding.to_record(); binding['profile_id'] = 'm3_test:wrong'
        mismatch = values.ClassificationEvidence(
            correction_path_is_known=values.EvaluatedPredicate(values.PredicateBinding(**binding), True),
            fallback_is_available=facts.fallback_is_available)
        self.assert_wire_valid(self.make_model(profile).assess('100011110', context=values.SystemContext(False, False),
                               classification_evidence=mismatch, diagnostic_context=dc).to_record())
        for stage_index, mode in itertools.product([1, 2], ['reject', 'throw_before', 'append_then_throw', 'wrong_reference']):
            capture = CaptureDouble(failure_at=stage_index, mode=mode)
            dc = diagnostic_context('m3_wire_actual:capture:' + str(stage_index) + ':' + mode)
            packet = self.make_model(profile, capture).assess('100000000', context=values.SystemContext(False, False),
                classification_evidence=evidence(profile, dc, 'ash_state_100000000'), diagnostic_context=dc).to_record()
            self.assertEqual('diagnostic_capture', packet['failure_kind'])
            self.assert_wire_valid(packet)
        for number in [0.9, math.nan, math.inf, -math.inf]:
            packet = self.make_model(profile).diagnose([number] + [0] * 8, diagnostic_context=diagnostic_context()).to_record()
            self.assert_wire_valid(packet)

    def test_partial_string_prefix_constructor_and_wire_share_the_64_character_limit(self):
        result = self.make_model().diagnose(['string'] + [0] * 8, diagnostic_context=diagnostic_context())
        for prefix, total_length in [('short', 6), ('x' * 64, 65)]:
            observation = values.CoordinateObservation(index=0, scalar_kind='STRING', value=prefix,
                                                      total_length=total_length, truncated=True)
            input_evidence = dataclasses.replace(result.input_evidence, coordinate_observations=[observation])
            diagnostic = dataclasses.replace(result.state_validity_diagnostic,
                                            input_state=values.RejectedCandidateEvidence(input_evidence))
            owned_packet = dataclasses.replace(result, input_evidence=input_evidence, state_validity_diagnostic=diagnostic)
            wire = owned_packet.to_record()
            self.assertEqual({'index': 0, 'scalar_kind': 'STRING', 'value': prefix,
                              'total_length': total_length, 'truncated': True},
                             wire['input_evidence']['coordinate_observations'][0])
            with self.subTest(prefix_length=len(prefix)):
                self.assert_wire_valid(wire)
        self.assert_code('DIAGNOSTIC_ROW_INVALID', values.CoordinateObservation, index=0,
                         scalar_kind='STRING', value='x' * 65, total_length=66, truncated=True)
        too_long = copy.deepcopy(wire)
        too_long['input_evidence']['coordinate_observations'][0].update(value='x' * 65, total_length=66)
        self.assert_wire_rejected(too_long, 'maxLength', ('input_evidence', 'coordinate_observations', 0, 'value'))


class LegacyDiagnosisMigrationTests(ModelTestCase):
    def assert_legacy_diagnosis_only(self, diagnostic, expected_status):
        self.assertTrue(VALIDITY_FIELDS <= diagnostic.keys())
        self.assertTrue(ENVELOPE_FIELDS <= diagnostic.keys())
        self.assertEqual(expected_status, diagnostic['admissibility_status'])
        self.assertNotIn('system_state_class', diagnostic)
        self.assertNotIn('recovery_category', diagnostic)
        self.assertNotEqual('SELF', diagnostic['chain_root_reference'])
        self.assertEqual('NONE', diagnostic['parent_diagnostic_reference'])
        self.assertEqual('DETECTION', diagnostic['stage'])
        self.assertTrue(diagnostic['notes'])
        for note in diagnostic['notes']:
            self.assertNotIn('System state:', note)
        self.assertNotIn('containment entered', json.dumps(diagnostic).lower())
        self.assertNotIn('safe halt entered', json.dumps(diagnostic).lower())

    def test_direct_diagnosis_all_four_rows_have_complete_diagnosis_only_scope(self):
        for candidate, status in [('100000000', 'VALID'), ('100011110', 'TRANSFORMATION_COMPATIBLE'),
                                  ('000000000', 'TRANSFORMATION_INCOMPATIBLE'), ([0.9] + [0] * 8, 'UNCLASSIFIED')]:
            with self.subTest(status=status):
                self.assert_legacy_diagnosis_only(legacy.diagnose_state(candidate), status)

    def test_snapshot_and_planner_consumers_preserve_diagnosis_only_fields_and_aliases(self):
        for signature, status in [('100000000', 'VALID'), ('100011110', 'TRANSFORMATION_COMPATIBLE'),
                                  ('000000000', 'TRANSFORMATION_INCOMPATIBLE')]:
            snapshot = legacy.build_cosmic_pattern_snapshot(signature)
            self.assert_legacy_diagnosis_only(snapshot['diagnostic'], status)
            self.assertEqual(snapshot['diagnostic'], snapshot['diagnostic_ref'])
            self.assertEqual(snapshot['state_identity'], snapshot['realm_identity'])
            plan = legacy.plan_generation('m3_migration', signature)
            for diagnostic in [plan['diagnostic_ref'], plan['axiom_diagnostic'],
                               plan['cosmic_pattern_snapshot_ref']['diagnostic_ref']]:
                self.assert_legacy_diagnosis_only(diagnostic, status)
            self.assertEqual(plan['source_state_identity'], plan['source_realm'])
            self.assertEqual(plan['destination_state_identity'], plan['destination_realm'])

    def test_public_mutable_anchor_view_cannot_change_legacy_profile_authority(self):
        before = [legacy.diagnose_state(format(vertex, '09b')) for vertex in range(512)]
        original = dict(legacy.YWE_REALM_STATE_ANCHORS)
        try:
            legacy.YWE_REALM_STATE_ANCHORS.clear()
            legacy.YWE_REALM_STATE_ANCHORS['invented'] = (0,) * 9
            after = [legacy.diagnose_state(format(vertex, '09b')) for vertex in range(512)]
            self.assertEqual(before, after)
        finally:
            legacy.YWE_REALM_STATE_ANCHORS.clear()
            legacy.YWE_REALM_STATE_ANCHORS.update(original)

    def test_all_512_identities_and_8192_codeword_transforms_preserve_full_vector_algebra(self):
        codewords = independently_read_codewords()
        identities = []
        for vertex in range(512):
            signature = format(vertex, '09b')
            orbit = sorted(vertex ^ word for word in codewords)
            expected = {'state_signature': signature, 'vertex_id': 'ash_state_' + signature,
                        'realm_id': 'ash_state_' + signature, 'orbit_id': format(orbit[0], '09b')}
            self.assertEqual(expected, legacy.encode_state_identity(signature))
            self.assertEqual(expected, legacy.encode_realm_identity(signature))
            identities.append(expected['vertex_id'])
            for word in codewords:
                codeword = format(word, '09b')
                transformed = legacy.transform_state(signature, codeword)
                self.assertEqual(format(vertex ^ word, '09b'), transformed.signature)
                restored = legacy.transform_state(transformed.bits, codeword)
                self.assertEqual(signature, restored.signature)
        self.assertEqual(512, len(set(identities)))
        self.assertEqual(16, len(codewords))
        self.assertEqual(set(codewords), {a ^ b for a in codewords for b in codewords})


if __name__ == '__main__':
    unittest.main()
