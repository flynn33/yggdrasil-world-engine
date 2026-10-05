from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.ash_pattern_engine import normalization, normalization_values as nv
from core.ash_pattern_engine import diagnostics_values as dv, recovery_values as rv
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.state_model import RecordingDiagnosticCapture, StateModel
from tests import test_m3_normalization as n1
from tests import test_m3_state_model as assessment


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'docs/architecture/m3_source_compatibility_contract.md'


def reviewed_inventory():
    match = re.search(r'<!-- EXACT_SOURCE_COMPATIBILITY_INVENTORY -->\s*```json\s*(.*?)```',
                      CONTRACT.read_text(encoding='utf-8'), re.S)
    if match is None:
        raise AssertionError('The adopted exact inventory is missing')
    return json.loads(match.group(1))


def binding_schema():
    schema = json.loads((ROOT / 'data/schemas/m3_state_assessment_schema.json').read_text(encoding='utf-8'))
    registry = Registry().with_resource(schema['$id'], Resource.from_contents(schema))
    return Draft202012Validator({'$ref': schema['$id'] + '#/$defs/CanonicalAshBinding'}, registry=registry)


class CountingCapture:
    def __init__(self):
        self.begins = []

    def begin(self, reference, **kwargs):
        self.begins.append(reference)
        raise AssertionError('A pure or rejected source operation invoked capture')


class EqualityHook(str):
    calls = []

    def __eq__(self, other):
        self.calls.append('eq')
        raise AssertionError('An unowned scalar equality hook executed')

    def __hash__(self):
        self.calls.append('hash')
        raise AssertionError('An unowned scalar hash hook executed')


class SourceCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.inventory = reviewed_inventory()
        self.vectors = self.inventory['vectors']
        self.profile = assessment.profile_binding()

    def model(self, vector, capture=None, normalization_capture=None):
        return StateModel(self.profile, sv.CanonicalAshBinding(**vector['canonical_binding']),
                          RecordingDiagnosticCapture() if capture is None else capture,
                          normalization_capture=normalization_capture)

    def assess(self, model, reference):
        context = assessment.diagnostic_context(reference)
        facts = []
        for name in ('correction_path_is_known', 'fallback_is_available'):
            binding = sv.PredicateBinding(
                context.assessment_reference, context.detection_reference, 'ash_state_100000000',
                self.profile.profile_id, self.profile.source_binding.source_sha256,
                model.canonical_binding.dependency_id, model.canonical_binding.aggregate_sha256,
                reference + ':' + name + ':fixture_fact')
            facts.append(sv.NotEvaluatedPredicate(binding, 'Not needed for a valid state.'))
        return model.assess('100000000', context=sv.SystemContext(False, False),
                            classification_evidence=sv.ClassificationEvidence(*facts),
                            diagnostic_context=context)

    def test_two_complete_vectors_preserve_constructor_and_wire_fields(self):
        fields = tuple(self.inventory['canonical_field_order'])
        self.assertEqual(tuple(inspect.signature(sv.CanonicalAshBinding).parameters), fields)
        self.assertEqual(tuple(field.name for field in dataclasses.fields(sv.CanonicalAshBinding)), fields)
        validator = binding_schema()
        for vector in self.vectors:
            with self.subTest(baseline=vector['baseline']):
                binding = sv.CanonicalAshBinding(**vector['canonical_binding'])
                self.assertEqual(binding.to_record(), vector['canonical_binding'])
                self.assertEqual(tuple(binding.to_record()), fields)
                self.assertEqual(sv.canonical_source_baseline(binding), vector['baseline'])
                expected = tuple((pin['source_kind'], pin['sha256']) for pin in vector['diagnostic_pin_fields'])
                self.assertEqual(sv.canonical_diagnostic_pin_fields(binding), expected)
                self.assertEqual(list(validator.iter_errors(binding.to_record())), [])
        self.assertEqual(sv.CANONICAL_BINDING_FIELDS, tuple(self.vectors[0]['canonical_binding'].items()))
        self.assertEqual(sv.CURRENT_CANONICAL_BINDING_FIELDS, tuple(self.vectors[1]['canonical_binding'].items()))

    def test_aggregate_and_taxonomy_are_paired_in_constructor_and_schema(self):
        validator = binding_schema()
        for aggregate_owner in self.vectors:
            for taxonomy_owner in self.vectors:
                record = dict(aggregate_owner['canonical_binding'])
                record['taxonomy_source_sha256'] = taxonomy_owner['canonical_binding']['taxonomy_source_sha256']
                paired = aggregate_owner['baseline'] == taxonomy_owner['baseline']
                with self.subTest(aggregate=aggregate_owner['baseline'], taxonomy=taxonomy_owner['baseline']):
                    self.assertEqual(validator.is_valid(record), paired)
                    if paired:
                        sv.CanonicalAshBinding(**record)
                    else:
                        with self.assertRaises(sv.StateContractError) as caught:
                            sv.CanonicalAshBinding(**record)
                        self.assertEqual((caught.exception.code, caught.exception.field_name),
                                         ('CANONICAL_BINDING_INVALID', 'taxonomy_source_sha256'))

    def test_independently_authored_sixteen_atomic_values_match_constructor_acceptance(self):
        cases = json.loads((ROOT / 'examples/core_source_compatibility/source_vector_cases.example.json').read_text(
            encoding='utf-8'))
        self.assertEqual(sum(len(controls) for controls in cases.values()), 16)
        self.assertEqual(sum(control['accepted'] for controls in cases.values() for control in controls), 6)
        for domain, controls in cases.items():
            for control in controls:
                record = control['input']
                with self.subTest(case=control['case_id']):
                    try:
                        if domain == 'canonical':
                            value = sv.CanonicalAshBinding(**record)
                        elif domain == 'recovery':
                            value = rv.RecoverySourceBinding(sv.CanonicalAshBinding(**record['canonical_binding']),
                                tuple(rv.SourcePin(**pin) for pin in record['contract_pins']))
                        else:
                            self.assertEqual(domain, 'source_graph')
                            value = dv.SafeSourceEvidence(record['evidence_reference'],
                                tuple(dv.SourcePin(**pin) for pin in record['verified_pins']),
                                record['external_source_reference'])
                    except (sv.StateContractError, rv.RecoveryContractError, dv.DiagnosticsContractError):
                        self.assertFalse(control['accepted'])
                    else:
                        self.assertTrue(control['accepted'])
                        self.assertEqual(value.to_record(), record)

    def test_all_scalars_are_owned_before_any_vector_equality(self):
        for vector in self.vectors:
            for field in self.inventory['canonical_field_order']:
                for bad in (None, [], EqualityHook(vector['canonical_binding'][field])):
                    EqualityHook.calls.clear()
                    record = dict(vector['canonical_binding'])
                    record[field] = bad
                    with self.subTest(baseline=vector['baseline'], field=field, kind=type(bad).__name__):
                        with self.assertRaises(sv.StateContractError) as caught:
                            sv.CanonicalAshBinding(**record)
                        self.assertEqual(caught.exception.field_name, field)
                        self.assertEqual(EqualityHook.calls, [])
        record = dict(self.vectors[0]['canonical_binding'])
        record['dependency_id'] = 'unknown.dependency'
        record['taxonomy_source_sha256'] = EqualityHook(record['taxonomy_source_sha256'])
        EqualityHook.calls.clear()
        with self.assertRaises(sv.StateContractError) as caught:
            sv.CanonicalAshBinding(**record)
        self.assertEqual(caught.exception.field_name, 'taxonomy_source_sha256')
        self.assertEqual(EqualityHook.calls, [])

    def test_helpers_and_model_reject_subclasses_missing_fields_and_reflected_mixes(self):
        class ForeignBinding(sv.CanonicalAshBinding):
            pass
        valid = sv.CanonicalAshBinding(**self.vectors[0]['canonical_binding'])
        foreign = object.__new__(ForeignBinding)
        for field in self.inventory['canonical_field_order']:
            object.__setattr__(foreign, field, getattr(valid, field))
        missing = object.__new__(sv.CanonicalAshBinding)
        reflected = dataclasses.replace(valid)
        object.__setattr__(reflected, 'taxonomy_source_sha256',
                           self.vectors[1]['canonical_binding']['taxonomy_source_sha256'])
        capture = CountingCapture()
        for bad in (foreign, missing, reflected):
            for helper in (sv.canonical_source_baseline, sv.canonical_diagnostic_pin_fields):
                with self.subTest(helper=helper.__name__, kind=type(bad).__name__):
                    with self.assertRaises(sv.StateContractError):
                        helper(bad)
            with self.assertRaises(sv.StateContractError):
                StateModel(self.profile, bad, capture)
        self.assertEqual(capture.begins, [])

    def test_unknown_dependency_aggregate_and_first_changed_leaf_are_bounded(self):
        for vector in self.vectors:
            for field in self.inventory['canonical_field_order']:
                record = dict(vector['canonical_binding'])
                record[field] = 'unknown.dependency' if field == 'dependency_id' else '0' * 64
                with self.subTest(baseline=vector['baseline'], field=field):
                    with self.assertRaises(sv.StateContractError) as caught:
                        sv.CanonicalAshBinding(**record)
                    self.assertEqual(caught.exception.field_name, field)

    def test_assessment_validation_keeps_both_complete_roles_without_capture(self):
        origins = [self.assess(self.model(vector), 'source_compat:assessment:' + str(index))
                   for index, vector in enumerate(self.vectors)]
        for current_index, vector in enumerate(self.vectors):
            capture = CountingCapture()
            model = self.model(vector, capture)
            for origin_index, origin in enumerate(origins):
                with self.subTest(current=current_index, submitted=origin_index):
                    witness = model.validate_assessment(origin)
                    self.assertIs(witness.submitted_assessment, origin)
                    self.assertIs(witness.current_source_binding, model.canonical_binding)
                    if current_index == origin_index:
                        self.assertEqual(witness.status, 'VERIFIED')
                        self.assertEqual(witness.expected_system_state_class, 'STABLE')
                    else:
                        self.assertEqual((witness.status, witness.failure_code, witness.field_name),
                                         ('REJECTED', 'SOURCE_BINDING_MISMATCH', 'origin_assessment.source_binding'))
                        self.assertIsNone(witness.expected_diagnostic)
                    self.assertEqual(capture.begins, [])

    def test_generic_lifecycle_ids_do_not_widen_state_or_normalization_owners(self):
        added = tuple('ASH-CONTAINMENT-TRIGGER-' + str(i).zfill(3) for i in range(1, 5)) + tuple(
            'ASH-HALT-TRIGGER-' + str(i).zfill(3) for i in range(1, 6))
        self.assertEqual(len(sv.RULE_IDS), 17)
        self.assertEqual(len(sv.ASSESSMENT_RULE_IDS), 6)
        self.assertEqual(len(nv.NORMALIZATION_RULE_IDS), 7)
        diagnostic = self.model(self.vectors[1]).diagnose(
            '100000000', diagnostic_context=assessment.diagnostic_context('source_compat:rule')).state_validity_diagnostic
        for rule in added:
            envelope = sv.DiagnosticEnvelope('STATE_VALIDITY', 'WARNING', 'RECOVERY', 'PENDING',
                                              'ash_state_100000000', 'source_compat:root', 'source_compat:root',
                                              (rule,), 'Generic source taxonomy control.',
                                              ('Owned by the generic envelope taxonomy.',))
            emission = sv.DiagnosticEmission('source_compat:child', envelope)
            with self.subTest(rule=rule):
                with self.assertRaises(sv.StateContractError) as caught:
                    dataclasses.replace(diagnostic, rule_ids=(rule,))
                self.assertEqual(caught.exception.field_name, 'rule_ids')
                with self.assertRaises(nv.NormalizationContractError) as caught:
                    nv.NormalizationDiagnosticRecord(emission, 'COMPUTATION', diagnostic, None)
                self.assertEqual(caught.exception.field_name, 'emission.envelope.rule_ids')

    def test_actual_normalization_preserves_each_source_and_rejects_foreign_origin(self):
        plans = []
        for index, vector in enumerate(self.vectors):
            model = self.model(vector, normalization_capture=normalization.RecordingNormalizationCapture())
            diagnosis = model.diagnose('100011110', diagnostic_context=assessment.diagnostic_context(
                'source_compat:normalization:' + str(index)))
            plan = model.plan_normalization(diagnosis, plan_reference='source_compat:plan:' + str(index),
                                             evidence_reference='source_compat:evidence:' + str(index),
                                             policy_binding=n1.policy_binding())
            plans.append(plan)
            result = model.apply_normalization(plan, normalization_context=n1.operation_context(
                'source_compat:operation:' + str(index)))
            self.assertEqual(result.outcome, 'NORMALIZED')
            self.assertEqual(result.actual_state.signature, '100000000')
            self.assertTrue(result.post_validity_diagnostic.is_valid)
            self.assertEqual(result.original_diagnosis.source_binding.to_record(), vector['canonical_binding'])
            self.assertEqual(result.plan_validation.canonical_binding.to_record(), vector['canonical_binding'])
            self.assertEqual(len(result.emitted_diagnostics), 2)
        for index, vector in enumerate(self.vectors):
            capture = CountingCapture()
            model = self.model(vector, capture, capture)
            witness = model.validate_normalization_plan(plans[1 - index])
            self.assertEqual(witness.validation_status, 'REJECTED')
            self.assertEqual(witness.field_name, 'original_diagnosis.source_binding')
            self.assertEqual(witness.origin_validation_status, 'REJECTED')
            self.assertEqual(capture.begins, [])


if __name__ == '__main__':
    unittest.main()
