from __future__ import annotations

import copy
import dataclasses
import json
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.ash_pattern_engine import realm_transition_values as v, state_values as s
from core.ash_pattern_engine.state_model import StateModel
from tests.test_m3_realm_transition_values import ROOT, assembly, diagnosis


def schema_registry():
    registry = Registry(retrieve=lambda uri: (_ for _ in ()).throw(AssertionError('Unexpected remote schema: ' + uri)))
    for name in ('m3_state_assessment_schema.json', 'm3_reference_diagnostic_bundle_schema.json', 'm3_realm_transition_schema.json'):
        source = json.loads((ROOT / 'data/schemas' / name).read_text(encoding='utf-8'))
        registry = registry.with_resource(source['$id'], Resource.from_contents(source))
    return registry


class RealmTransitionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'data/schemas/m3_realm_transition_schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, registry=schema_registry())

    def test_actual_success_failure_values_and_all17_inventory_shapes(self):
        model, encoder, registry = assembly(restricted=True)
        origin = diagnosis(model)
        encode = encoder.encode(origin, operation_reference='schema:encode')
        resolve = registry.resolve(origin, operation_reference='schema:resolve')
        apply = registry.apply(origin, v.TransitionSelection('IDENTIFIER', 'ash_codeword_01', None), operation_reference='schema:apply')
        unavailable = registry.apply(origin, v.TransitionSelection('IDENTIFIER', 'ash_codeword_00', None), operation_reference='schema:unavailable')
        missing = registry.apply(origin, v.TransitionSelection('IDENTIFIER', 'unknown', None), operation_reference='schema:unknown')
        gate = encode.constructed_records[0].payload
        receipt = v.RealmTransitionCaptureReceipt('schema:encode', 'NOT_CONFIRMED', encode, (), None, None, None, 'MODULE_RESERVATION_REFUSED')
        values = [encode.binding.contract_pins[0], encode.binding, apply.selected_definition,
                  resolve.catalog, apply.selection, encode.origin_validation, encode.identity, gate,
                  resolve.availability[0], apply.constructed_records[1].payload,
                  apply.constructed_records[-1].payload, apply.constructed_records[-1],
                  encode, resolve, apply, unavailable, receipt, missing]
        seen = set()
        for value in values:
            with self.subTest(type=type(value).__name__):
                self.validator.validate(value.to_record())
                seen.add(type(value).__name__)
        inventory = json.loads((ROOT / 'docs/design-planning/m3/realm-transition/REALM_TRANSITION_API_INVENTORY.json').read_text(encoding='utf-8'))
        self.assertEqual(seen, {row['name'] for row in inventory['types']})

    def test_closed_phase_rule_order_catalog_policy_selector_and_binding_rejections(self):
        model, encoder, registry = assembly()
        result = registry.apply(diagnosis(model), v.TransitionSelection('IDENTIFIER', 'ash_codeword_01', None), operation_reference='schema:apply').to_record()
        mutations = []
        def mutate(change):
            packet = copy.deepcopy(result)
            change(packet)
            mutations.append(packet)
        mutate(lambda packet: packet.update(extra='closed'))
        mutate(lambda packet: packet['constructed_records'][1]['emission']['envelope'].update(stage='RECOVERY'))
        mutate(lambda packet: packet['constructed_records'][1]['emission']['envelope'].update(rule_ids=['ASH-STATE-GENERAL']))
        mutate(lambda packet: packet['constructed_records'][1].update(payload=packet['constructed_records'][0]['payload']))
        mutate(lambda packet: packet['constructed_records'].reverse())
        mutate(lambda packet: packet['selection'].update(codeword=packet['candidate']))
        mutate(lambda packet: packet['binding']['contract_pins'].reverse())
        mutate(lambda packet: packet['binding'].update(policy_source_sha256='0' * 64))
        mutate(lambda packet: packet['binding']['canonical_binding'].update(aggregate_sha256=s.CURRENT_CANONICAL_BINDING_FIELDS[1][1]))
        mutate(lambda packet: packet['origin_validation'].update(failure_code='DIAGNOSIS_MISMATCH'))
        for index, packet in enumerate(mutations):
            with self.subTest(index=index):
                self.assertFalse(self.validator.is_valid(packet))
        catalog = registry.resolve(diagnosis(model), operation_reference='schema:catalog').catalog.to_record()
        for change in (lambda packet: packet['definitions'].reverse(),
                       lambda packet: packet['definitions'][0].update(applicability_mask='0' + '1' * 511),
                       lambda packet: packet['definitions'][0].update(display_name='Changed compiled policy')):
            mutated = copy.deepcopy(catalog)
            change(mutated)
            self.assertFalse(self.validator.is_valid(mutated))

    def test_shared_rejected_validation_keeps_actual_immutable_fields(self):
        model, encoder, _ = assembly()
        actual = diagnosis(model)
        foreign = dataclasses.replace(actual, source_binding=s.CanonicalAshBinding(**dict(s.CURRENT_CANONICAL_BINDING_FIELDS)))
        validation = StateModel.validate_diagnosis(model, foreign)
        self.validator.validate(validation.to_record())
        bad = validation.to_record()
        bad['failed_field'] = 'arbitrary.path'
        self.assertFalse(self.validator.is_valid(bad))
        malformed = encoder.encode(diagnosis(model, 'bad'), operation_reference='schema:malformed')
        self.validator.validate(malformed.to_record())

    def test_authored_case_wrappers_close_metadata_and_select_definitions_separately(self):
        model, encoder, _ = assembly()
        value = encoder.encode(diagnosis(model), operation_reference='wrapper:encode').to_record()
        case = {'case_id': 'wrapper:positive', 'schema_definition': 'RealmEncodingResult', 'value': value}
        positive = {'schema_ref': 'data/schemas/m3_realm_transition_schema.json',
                    'artifact_type': 'ywe_realm_transition_format_cases', 'artifact_version': '1.0.0',
                    'evidence_scope': 'AUTHORED_WIRE_FORMAT_ONLY_NO_PERSISTENCE_OR_LIVE_EFFECT_CLAIM',
                    'cases': [case]}
        wrapper = Draft202012Validator({'$ref': self.schema['$id'] + '#/$defs/RealmTransitionCaseCatalog'}, registry=schema_registry())
        wrapper.validate(positive)
        self.assertFalse(self.validator.is_valid(positive))
        # Authored format metadata is distinct from the separately selected value check.
        format_only = copy.deepcopy(positive)
        format_only['cases'][0]['value'] = {'intentionally': 'unchecked by wrapper'}
        wrapper.validate(format_only)
        for change in (lambda p: p.update(extra='closed'), lambda p: p.update(evidence_scope='RUNTIME_VERIFIED'),
                       lambda p: p['cases'][0].update(schema_definition='UnknownDefinition'), lambda p: p.update(cases=[])):
            mutated = copy.deepcopy(positive)
            change(mutated)
            self.assertFalse(wrapper.is_valid(mutated))
        rejected = {**positive, 'artifact_type': 'ywe_realm_transition_rejection_cases',
                    'evidence_scope': 'AUTHORED_REJECTION_CONTROL_ONLY_NO_RUNTIME_EFFECT_CLAIM',
                    'cases': [{**case, 'expected_keyword': 'additionalProperties', 'expected_path': []}]}
        reject_wrapper = Draft202012Validator({'$ref': self.schema['$id'] + '#/$defs/RealmTransitionRejectionCatalog'}, registry=schema_registry())
        reject_wrapper.validate(rejected)
        width_rejection = copy.deepcopy(rejected)
        width_rejection['cases'][0].update(schema_definition='TransitionDefinition',
                expected_keyword='minLength', expected_path=['applicability_mask'])
        reject_wrapper.validate(width_rejection)
        for change in (lambda p: p['cases'][0].update(expected_keyword='invented_keyword'),
                       lambda p: p['cases'][0].update(expected_path=[-1]),
                       lambda p: p['cases'][0].update(expected_path=['x' * 257])):
            mutated = copy.deepcopy(rejected)
            change(mutated)
            self.assertFalse(reject_wrapper.is_valid(mutated))


if __name__ == '__main__':
    unittest.main()
