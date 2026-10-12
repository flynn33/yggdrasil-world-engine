"""Actual bounded pure compound chains with independent intermediate-state expectations."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import unittest

from core.ash_pattern_engine import planner_emitter_values as p, realm_transition_values as rt, state_values as s
from core.ash_pattern_engine.realm_transition import RealmEncoder, TransitionRegistry
from core.ash_pattern_engine.state_model import StateModel, RecordingDiagnosticCapture, wrw_profile_binding
from tests.test_m3_realm_transition_values import profile_from, diagnosis


def assembly(*, profile=None, restricted=False):
    if profile is None:
        profile = profile_from(tuple(f'{index:09b}' for index in range(512)), 'generation:all512')
    canonical = s.CanonicalAshBinding(**dict(s.GENERATION_CANONICAL_BINDING_FIELDS))
    binding = rt.RealmTransitionBinding(canonical, profile, tuple(rt.RealmTransitionSourcePin(*pin) for pin in rt.GENERATION_SOURCE_PINS),
              *rt.POLICY_IDENTITIES[int(restricted)], 'generation:policy')
    definitions = tuple(rt.TransitionDefinition(f'ash_codeword_{i:02d}', f'ASH codeword {i:02d}',
                  'Apply the complete canonical nine-coordinate XOR codeword.', s.AshState(bits),
                  '1'+'0'*511 if restricted and i == 0 else '1'*512) for i,bits in enumerate(s.CANONICAL_CODEWORDS))
    model = StateModel(profile, canonical, RecordingDiagnosticCapture())
    return model, RealmEncoder(model,binding), TransitionRegistry(model, rt.TransitionCatalog(binding,definitions))


def select(index):
    return rt.TransitionSelection('IDENTIFIER', f'ash_codeword_{index:02d}', None)


class TransitionChainTests(unittest.TestCase):
    def test_all_lengths_retain_actual_immediate_records_and_prior_proof(self):
        model, _, registry = assembly()
        origin = diagnosis(model, '000000000', 'chain:origin')
        for length in range(5):
            selections = tuple(select(index+1) for index in range(length))
            result = registry.apply_chain(origin,selections,operation_reference=f'chain:length{length}')
            self.assertIs(type(result),p.TransitionChainResult)
            self.assertEqual(1+3*length,len(result.constructed_records))
            current = (0,)*9
            for index, step in enumerate(result.steps):
                self.assertEqual(current,step.input_state.bits)
                current = tuple(bit^code for bit,code in zip(current,s.CANONICAL_CODEWORDS[index+1]))
                self.assertEqual(current,step.transformation_observation.candidate.bits)
                self.assertTrue(step.transformation_observation.target_diagnosis.is_valid)
                expected_proof = origin.emitted_diagnostics[0].diagnostic_reference if index==0 else result.steps[index-1].record_references[2]
                self.assertEqual(expected_proof,step.source_proof_reference)
            self.assertEqual(current,result.last_candidate.bits)
            self.assertTrue(TransitionRegistry.validate_owned_result(registry,result))
            self.assertEqual('PROCESSING',result.constructed_records[-1].emission.envelope.stage)
            self.assertEqual(origin.emitted_diagnostics[0].envelope.subject_reference,result.constructed_records[-1].emission.envelope.subject_reference)
            result.to_record()

    def test_nonzero_h4_four_step_reversal_and_full_math(self):
        c1,c2 = s.CANONICAL_CODEWORDS[1:3]
        h4 = ((0,)*9,c1,c2,tuple(a^b for a,b in zip(c1,c2)))
        profile = profile_from(tuple(''.join(map(str,bits)) for bits in h4),'generation:H4')
        model,_,registry=assembly(profile=profile)
        result=registry.apply_chain(diagnosis(model,'000000000','h4:origin'),tuple(select(i) for i in (1,1,2,2)),operation_reference='h4:chain')
        self.assertEqual((c1,(0,)*9,c2,(0,)*9),tuple(step.transformation_observation.candidate.bits for step in result.steps))
        self.assertEqual('COMPLETE',result.status)
        self.assertEqual(13,len(result.constructed_records))

    def test_actual_intermediate_mask_refusal_stops_before_transform(self):
        model,_,registry=assembly(restricted=True)
        result=registry.apply_chain(diagnosis(model,'000000000'),(select(1),select(0),select(1)),operation_reference='chain:mask')
        self.assertIs(type(result),p.TransitionChainFailure)
        self.assertEqual((1,'APPLICABILITY','TRANSITION_NOT_APPLICABLE'),(result.failed_index,result.failed_phase,result.failure_code))
        self.assertEqual((1,6),(len(result.steps),len(result.constructed_records)))
        self.assertEqual(s.CANONICAL_CODEWORDS[1],result.last_candidate.bits)
        self.assertFalse(result.constructed_records[-1].payload.is_applicable)

    def test_unknown_noncanonical_and_computed_tc_keep_exact_prefix_single_apply_unchanged(self):
        model,_,registry=assembly()
        origin=diagnosis(model,'000000000')
        for selector,code in ((rt.TransitionSelection('IDENTIFIER','unknown',None),'TRANSITION_UNKNOWN'),
                              (rt.TransitionSelection('CODEWORD',None,s.AshState((1,0,0,0,0,0,0,0,0))),'CODEWORD_NOT_CANONICAL')):
            result=registry.apply_chain(origin,(select(1),selector,select(2)),operation_reference='chain:unknown:'+code)
            self.assertEqual((1,5,1,code),(len(result.steps),len(result.constructed_records),result.failed_index,result.failure_code))
        model,_,registry=assembly(profile=wrw_profile_binding())
        origin=diagnosis(model,'100000000')
        single=registry.apply(origin,select(1),operation_reference='chain:oldsingle')
        chain=registry.apply_chain(origin,(select(1),select(1)),operation_reference='chain:tc')
        self.assertIs(type(single),rt.TransitionApplicationResult)
        self.assertEqual('TRANSFORMATION_COMPATIBLE',single.target_diagnosis.admissibility_status)
        self.assertEqual(single.candidate,chain.last_candidate)
        self.assertEqual((1,4,0,'CHAIN_TARGET_NOT_VALID'),(len(chain.steps),len(chain.constructed_records),chain.failed_index,chain.failure_code))

    def test_invalid_actual_source_and_empty_identity_have_one_gate_without_new_diagnosis(self):
        model,_,registry=assembly(profile=wrw_profile_binding())
        origin=diagnosis(model,'000000000')
        result=registry.apply_chain(origin,(),operation_reference='chain:invalid')
        self.assertIs(type(result),p.TransitionChainFailure)
        self.assertEqual(('VALID_SOURCE',1,()),(result.failed_phase,len(result.constructed_records),result.steps))
        model,_,registry=assembly()
        origin=diagnosis(model,'000000000')
        result=registry.apply_chain(origin,(),operation_reference='chain:empty')
        self.assertIs(result.origin,origin)
        self.assertIs(result.final_target_diagnostic,origin.state_validity_diagnostic)
        self.assertEqual((),result.steps)

    def test_full_source_pair_copy_mutation_and_zero_hostile_type_hooks(self):
        model,_,registry=assembly()
        origin=diagnosis(model,'000000000')
        result=registry.apply_chain(origin,(select(1),),operation_reference='chain:sealed')
        copied=copy.copy(result)
        object.__setattr__(copied,'_self_identity',copied)
        self.assertFalse(registry.validate_owned_result(copied))
        object.__setattr__(result.steps[0],'source_proof_reference','wrong:proof')
        self.assertFalse(registry.validate_owned_result(result))
        with self.assertRaises(p.PlannerEmitterContractError): p.canonical_bytes(result)
        hooks=[]
        class Meta(type):
            def __eq__(cls,other): hooks.append('eq');return False
            def __hash__(cls): hooks.append('hash');return 1
        class Hostile(metaclass=Meta):
            def __str__(self): hooks.append('str');return 'hostile'
            def __eq__(self,other): hooks.append('value_eq');return False
            def __ne__(self,other): hooks.append('value_ne');return True
        reflected=registry.apply_chain(origin,(select(1),),operation_reference='chain:hostile:binding')
        object.__setattr__(reflected,'binding',Hostile())
        self.assertFalse(registry.validate_owned_result(reflected))
        for call in (lambda:p.canonical_bytes(Hostile()),lambda:p.GenerationInputs(Hostile(),'seed',0,(),'p','ALREADY_VALID','TERNARY_BRANCH_ROLES_001','YWE_ASCII_DOCUMENT_NAMES_001','DECLARED_AXIOM_FACTS_001','REFERENCE_MANIFEST_PAGES_001','REFERENCE_MEMORY_DOCUMENTS','INSPECT_ONLY')):
            with self.assertRaises(p.PlannerEmitterContractError): call()
        self.assertEqual([],hooks)

    def test_schema_exact_binding_and_original_branch_compatibility(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry,Resource
        root=Path(__file__).resolve().parents[1]
        resources=[]
        for path in (root/'data/schemas').glob('*.json'):
            raw=json.loads(path.read_text(encoding='utf-8'))
            if '$id' in raw: resources.append((raw['$id'],Resource.from_contents(raw)))
        schema=json.loads((root/'data/schemas/m3_planner_emitter_schema.json').read_text())
        model,_,registry=assembly()
        origin=diagnosis(model,'000000000')
        result=registry.apply_chain(origin,(select(1),select(1)),operation_reference='chain:schema')
        selected={'$ref':schema['$id']+'#/$defs/TransitionChainResult'}
        Draft202012Validator(selected,registry=Registry().with_resources(resources)).validate(result.to_record())
        pins=list(registry.configuration().contract_pins)
        pins[2]=replace(pins[2],source_sha256=rt.SOURCE_PINS[2][1])
        with self.assertRaises(rt.RealmTransitionContractError): replace(registry.configuration(),contract_pins=tuple(pins))
        from tests.test_m3_realm_transition_values import assembly as old_assembly
        old_model,_,old_registry=old_assembly()
        old_origin=diagnosis(old_model)
        with self.assertRaises(p.PlannerEmitterContractError): old_registry.apply_chain(old_origin,(),operation_reference='chain:historical')


if __name__ == '__main__': unittest.main()
