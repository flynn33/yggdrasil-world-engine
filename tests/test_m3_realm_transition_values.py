from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
from pathlib import Path
import unittest

from core.ash_pattern_engine import realm_transition_values as v
from core.ash_pattern_engine import state_values as s
from core.ash_pattern_engine.realm_transition import RealmEncoder, TransitionRegistry
from core.ash_pattern_engine.state_model import RecordingDiagnosticCapture, StateModel, wrw_profile_binding

ROOT = Path(__file__).resolve().parents[1]


def assembly(*, restricted=False, profile=None):
    profile = wrw_profile_binding() if profile is None else profile
    binding = v.RealmTransitionBinding(s.CanonicalAshBinding(**dict(s.MODULE_CANONICAL_BINDING_FIELDS)), profile,
            [v.RealmTransitionSourcePin(*pin) for pin in v.SOURCE_PINS], *v.POLICY_IDENTITIES[int(restricted)], 'test:policy')
    definitions = [v.TransitionDefinition(f'ash_codeword_{index:02d}', f'ASH codeword {index:02d}',
                   'Apply the complete canonical nine-coordinate XOR codeword.', s.AshState(bits),
                   '1' + '0' * 511 if restricted and index == 0 else '1' * 512)
                   for index, bits in enumerate(s.CANONICAL_CODEWORDS)]
    catalog = v.TransitionCatalog(binding, definitions)
    model = StateModel(profile, binding.canonical_binding, RecordingDiagnosticCapture())
    return model, RealmEncoder(model, binding), TransitionRegistry(model, catalog)


def diagnosis(model, candidate='100000000', reference='test:origin'):
    return model.diagnose(candidate, diagnostic_context=s.DiagnosticContext(reference, reference + ':input',
                          reference + ':detection', reference + ':classification'))


def profile_from(signatures, reference='test:profile'):
    signatures = tuple(signatures)
    digest = hashlib.sha256(json.dumps(sorted(signatures), separators=(',', ':')).encode()).hexdigest()
    return s.AvailableProfileBinding(s.ValidityProfile(reference, s.ProfileSourceBinding(reference, digest,
                    reference + ':evidence'), tuple(s.AshState(tuple(map(int, signature))) for signature in signatures)))


class RealmTransitionValueTests(unittest.TestCase):
    def test_exact_inventory_field_order_and_shared_failure_domains(self):
        inventory = json.loads((ROOT / 'docs/design-planning/m3/realm-transition/REALM_TRANSITION_API_INVENTORY.json').read_text(encoding='utf-8'))
        for row in inventory['types']:
            cls = getattr(s if row['name'] == 'DiagnosisValidation' else v, row['name'])
            self.assertEqual(tuple(f.name for f in dataclasses.fields(cls)), tuple(row['fields']))
        self.assertEqual(s.DIAGNOSIS_FAILURE_CODES, tuple(inventory['enums']['DiagnosisFailure']))
        self.assertEqual(s.DIAGNOSIS_FAILURE_FIELDS, tuple(inventory['enums']['DiagnosisFailureField']))
        self.assertEqual(v.SOURCE_PINS, tuple((row['source_id'], row['source_sha256']) for row in inventory['source_contract_pin_values']))

    def test_compiled_catalog_and_policy_bytes_are_exact(self):
        for restricted in (False, True):
            model, encoder, registry = assembly(restricted=restricted)
            binding = encoder.configuration()
            raw = (ROOT / binding.policy_source_reference).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest(), binding.policy_source_sha256)
            authored = json.loads(raw)['definitions']
            for expected, actual in zip(authored, registry._catalog.definitions):
                self.assertEqual(actual.transition_id, expected['transition_id'])
                self.assertEqual(actual.display_name, expected['display_name'])
                self.assertEqual(actual.description, expected['description'])
                self.assertEqual(actual.codeword.signature, expected['codeword'])
                self.assertEqual(actual.applicability_mask, expected['applicability_mask'])

    def test_catalog_reorder_replacement_mask_and_mixed_pin_rejected(self):
        model, encoder, registry = assembly()
        binding, catalog = encoder.configuration(), registry._catalog
        for definitions in (catalog.definitions[::-1], catalog.definitions[:-1],
                (dataclasses.replace(catalog.definitions[0], applicability_mask='0' + '1' * 511), *catalog.definitions[1:]),
                (dataclasses.replace(catalog.definitions[0], display_name='Replacement'), *catalog.definitions[1:]),
                (dataclasses.replace(catalog.definitions[0], codeword=catalog.definitions[1].codeword), *catalog.definitions[1:])):
            with self.assertRaises(v.RealmTransitionContractError):
                v.TransitionCatalog(binding, definitions)
        with self.assertRaises(v.RealmTransitionContractError):
            dataclasses.replace(binding, contract_pins=(dataclasses.replace(binding.contract_pins[0], source_sha256='0' * 64), *binding.contract_pins[1:]))
        with self.assertRaises(v.RealmTransitionContractError):
            dataclasses.replace(binding, canonical_binding=s.CanonicalAshBinding(**dict(s.CURRENT_CANONICAL_BINDING_FIELDS)))
        with self.assertRaises(v.RealmTransitionContractError):
            dataclasses.replace(binding, policy_source_sha256='0' * 64)

    def test_selectors_are_closed_and_do_not_coerce(self):
        cases = [('IDENTIFIER', 0, None), ('IDENTIFIER', 'NONE', None), ('CODEWORD', None, [0] * 9),
                 ('CODEWORD', 'ash_codeword_00', s.AshState((0,) * 9)), ('UNKNOWN', None, None)]
        for case in cases:
            with self.assertRaises(v.RealmTransitionContractError):
                v.TransitionSelection(*case)
        with self.assertRaises(v.RealmTransitionContractError):
            v.TransitionDefinition('ash_codeword_00', '\ud800', 'description', s.AshState((0,) * 9), '1' * 512)

    def test_immutable_collections_serializers_and_corruption(self):
        model, encoder, registry = assembly()
        actual = encoder.encode(diagnosis(model), operation_reference='test:encode')
        plain = actual.to_record()
        plain['constructed_records'].clear()
        self.assertEqual(len(actual.constructed_records), 2)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            actual.identity = None
        reflected = copy.copy(actual)
        object.__setattr__(reflected, 'constructed_records', list(actual.constructed_records))
        with self.assertRaises(v.RealmTransitionContractError):
            v.canonical_bytes(reflected)
        self.assertFalse(encoder.validate_owned_result(reflected))
        cyclic = copy.copy(actual)
        object.__setattr__(cyclic, 'origin', cyclic)
        with self.assertRaises(v.RealmTransitionContractError):
            v.canonical_bytes(cyclic)
        for invalid_note in ('\ud800', 'Untrusted\nsecond line'):
            record = actual.constructed_records[0]
            emission = dataclasses.replace(record.emission, envelope=dataclasses.replace(record.emission.envelope, notes=(invalid_note,)))
            with self.assertRaises(v.RealmTransitionContractError):
                dataclasses.replace(record, emission=emission)

    def test_whole_compact_guard_exact_boundary_and_no_truncation(self):
        model, encoder, registry = assembly()
        result = registry.resolve(diagnosis(model), operation_reference='test:resolve')
        exact = len(v.canonical_bytes(result))
        self.assertEqual(v.raw_business_size(result, limit=exact), exact)
        self.assertEqual(v.raw_business_size(result, limit=exact - 1), exact)
        with self.assertRaises(v.RealmTransitionContractError) as caught:
            v.canonical_bytes(result, limit=exact - 1)
        self.assertEqual(caught.exception.code, 'REALM_TRANSITION_RAW_PACKET_LIMIT')
        self.assertEqual(v.RAW_BUSINESS_LIMIT, 1_048_576)

    def test_unissued_results_copies_and_producer_copies_refuse_authority(self):
        model, encoder, registry = assembly()
        original = encoder.encode(diagnosis(model), operation_reference='test:encode')
        self.assertTrue(RealmEncoder.validate_owned_result(encoder, original))
        self.assertFalse(RealmEncoder.validate_owned_result(encoder, copy.copy(original)))
        copied = copy.copy(original)
        object.__setattr__(copied, '_self_identity', copied)
        self.assertFalse(RealmEncoder.validate_owned_result(encoder, copied))
        self.assertFalse(RealmEncoder.validate_owned_result(encoder, dataclasses.replace(original)))
        self.assertFalse(RealmEncoder.validate_owned_result(copy.copy(encoder), original))
        other = RealmEncoder(model, encoder.configuration())
        self.assertFalse(RealmEncoder.validate_owned_result(other, original))
        with self.assertRaises(v.RealmTransitionContractError):
            RealmEncoder.configuration(copy.copy(encoder))
        copied_owner = copy.copy(encoder)
        copied_owner._self_identity = copied_owner
        with self.assertRaises(v.RealmTransitionContractError):
            RealmEncoder.configuration(copied_owner)


if __name__ == '__main__':
    unittest.main()
