"""Actual neutral baseline and declared access predicate behavior."""
import unittest
import json
from pathlib import Path
from unittest.mock import patch
from core import core_values as v
from core.cosmology_engine.cosmology import CosmologyEngine
from core.realm_engine.realm import RealmEngine
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture
from core.ash_pattern_engine import state_values as s
from tests.test_m3_core_values import core_binding
from tests.test_m3_realm_transition_values import profile_from, diagnosis


def pure_model(*, realms=()):
    binding = core_binding(profile=profile_from(('000000000',)),realms=realms)
    return binding,StateModel(binding.profile_binding,binding.canonical_binding,RecordingDiagnosticCapture())


class CoreCosmologyRealmTests(unittest.TestCase):
    def test_actual_diagnosis_nine_ordered_coordinates_no_instance_validation_hooks(self):
        binding,model = pure_model()
        actual = diagnosis(model,'000000000')
        owner = CosmologyEngine(binding,model)
        with patch.object(model,'validate_diagnosis',side_effect=AssertionError('instance hook')), patch.object(model,'_diagnose',side_effect=AssertionError('private override')):
            result = owner.initialize_cosmos(actual,operation_reference='cosmos')
        self.assertEqual(result.status,'COMPLETED')
        self.assertIs(result.value.baseline,actual)
        self.assertEqual(result.value.structural_coordinates,tuple('b'+str(i) for i in range(9)))
        self.assertEqual(owner.get_profile_realm_definitions(),())
        self.assertTrue(owner.validate_owned_result(result))
        tc = diagnosis(model,s.CANONICAL_CODEWORDS[1],'tc')
        self.assertEqual(owner.initialize_cosmos(tc,operation_reference='tc:cosmos').status,'REFUSED')

    def test_explicit64_realm_mapping_sorted_never_ordinal_or_name_defaults(self):
        rows = tuple(v.ProfileRealmDefinition('realm'+f'{i:02d}',i%9,None,'Physical',0,False,()) for i in reversed(range(64)))
        binding,model = pure_model(realms=rows)
        owner = CosmologyEngine(binding,model)
        self.assertEqual([row.realm_id for row in owner.get_profile_realm_definitions()],['realm'+f'{i:02d}' for i in range(64)])
        self.assertEqual(owner.get_profile_realm_definitions()[6].coordinate,6)
        with self.assertRaises(v.CoreContractError):
            pure_model(realms=(*rows,v.ProfileRealmDefinition('extra',0,None,'Extra',0,False,())))

    def test_attunement_equality_veil_missing_and_false_all_predicates_retained(self):
        realms=(v.ProfileRealmDefinition('source',6,None,'Source',0,False,('source',)),
                v.ProfileRealmDefinition('target',2,None,'Target',500000,True,('source',)))
        owner = RealmEngine(pure_model(realms=realms)[0])
        def access(weight,veil):
            facts=() if weight is None else (v.AttunementFact('target',weight,veil,('attunement:fact',)),)
            return owner.evaluate_access(v.RealmAccessRequest('request','source','target','location',facts))
        equal=access(500000,'TRUE')
        self.assertEqual((equal.status,equal.value.eligible),('COMPLETED',True))
        self.assertEqual([row.field for row in equal.value.evaluated_rules],['source_realm_id','target_realm_id','allowed_origins','attunement_q6','thin_veil'])
        self.assertEqual(access(499999,'TRUE').status,'REFUSED')
        self.assertEqual(access(500001,'FALSE').status,'REFUSED')
        self.assertEqual(access(500000,'UNAVAILABLE').status,'PENDING')
        self.assertEqual(access(None,'UNAVAILABLE').status,'PENDING')
        proposed=owner.propose_shift(equal.value,proposal_ref='shift')
        self.assertEqual((proposed.effect_status,proposed.value.before_realm_id,proposed.value.target_realm_id),('PROPOSED_ONLY','source','target'))
        self.assertEqual(v.canonical_bytes(proposed),v.canonical_bytes(owner.propose_shift(equal.value,proposal_ref='shift')))
        denied=owner.evaluate_access(v.RealmAccessRequest('unknown','source','Physical','location',()))
        self.assertEqual((denied.status,denied.value.eligible),('REFUSED',False))

    def test_original_wrw_metadata_requires_exact_coordinates_and_explicit_eligibility(self):
        root=Path(__file__).resolve().parents[1]
        raw=(root/'data/realm_registry/realms.json').read_bytes()
        metadata=json.loads(raw)
        definitions=tuple(v.ProfileRealmDefinition(row['realm_id'],row['coordinate_index'],None,row['presentation_label'],
            500000,True,('physical',)) for row in metadata['coordinate_bindings'])
        actual=CosmologyEngine._compile_profile_realms(raw,definitions)
        self.assertEqual(next(row.coordinate for row in actual if row.realm_id=='physical'),6)
        self.assertTrue(all(row.threshold_q6==500000 and row.veil_required for row in actual))
        metadata['coordinate_bindings'][6]['coordinate_index']=0
        with self.assertRaises(v.CoreContractError):
            CosmologyEngine._compile_profile_realms(json.dumps(metadata).encode('utf-8'),definitions)
        with self.assertRaises(v.CoreContractError):
            CosmologyEngine._compile_profile_realms(raw,())


if __name__=='__main__':
    unittest.main()
