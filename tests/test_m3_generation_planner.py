"""Pure complete plan math, declared facts and independently expected artifacts."""
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from core.ash_pattern_engine import planner_emitter_values as p, generation_values as g, state_values as s
from core.ash_pattern_engine.generation_planner import ReferenceGenerationPlanner
from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
from core.ash_pattern_engine.axioms import ReferenceAxiomEvaluator
from core.ash_pattern_engine.state_model import StateModel
from tests.test_m3_transition_chain import assembly, select
from tests.test_m3_realm_transition_values import diagnosis
from tests.test_m3_axioms import subject


def planner_assembly(*, depth=0, flags=(True,)*5, choice='REFERENCE_MANIFEST_PAGES', profile=None):
    model,encoder,registry=assembly(profile=profile)
    topology=ReferenceTopologyGenerator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
    axioms=ReferenceAxiomEvaluator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
    pins=p.FIELD_SCHEMAS['PlannerEmitterBinding']['contract_pins']['const']
    binding=p.PlannerEmitterBinding(model.canonical_binding,model.profile_binding,
            tuple((row['path'],row['sha256']) for row in pins),p.PlannerEmitterPolicyBinding(*p.POLICY_FIELDS))
    planner=ReferenceGenerationPlanner(model,binding,encoder,registry,topology,axioms)
    origin=diagnosis(model,'000000000','plan:initial')
    final=diagnosis(model,'000000000','plan:final')
    sequence=(select(1),select(1))
    inputs=p.GenerationInputs('test_project','seed',depth,sequence,model.profile_binding.profile_id,'ALREADY_VALID',
           'TERNARY_BRANCH_ROLES_001','YWE_ASCII_DOCUMENT_NAMES_001','DECLARED_AXIOM_FACTS_001',
           'REFERENCE_MANIFEST_PAGES_001','REFERENCE_MEMORY_DOCUMENTS',choice)
    source=encoder.encode(origin,operation_reference='plan:source')
    chain=registry.apply_chain(origin,sequence,operation_reference='plan:chain')
    destination=encoder.encode(final,operation_reference='plan:destination')
    top=topology.generate(g.TopologyRequest('plan:topology',final,depth,'seed'))
    ax=axioms.evaluate(g.AxiomRequest('plan:axioms',final,subject(final,flags)))
    constraints=p.TargetConstraints(32,32768,1048576,False,'EXACT_BYTES_IDEMPOTENT_OR_REFUSE')
    request=p.PlannerRequest('plan:operation',inputs,origin,final,source,chain,destination,top,ax,constraints)
    return planner,request,(model,encoder,registry,topology,axioms)


class GenerationPlannerTests(unittest.TestCase):
    def test_identical_immutable_request_repeats_plan_and_document_canonical_bytes(self):
        from tests.test_m3_realm_transition_values import profile_from
        profile=profile_from(('000000000','000011110','001100110','001111000'),'planner:repeat:h4')
        planner,request,_=planner_assembly(depth=2,profile=profile)
        first=ReferenceGenerationPlanner.plan(planner,request)
        second=ReferenceGenerationPlanner.plan(planner,request)
        self.assertTrue(planner.validate_owned_result(first))
        self.assertTrue(planner.validate_owned_result(second))
        self.assertEqual(p.canonical_bytes(first),p.canonical_bytes(second))
        self.assertEqual(tuple(p.canonical_bytes(row.document) for row in first.plan.artifacts),
                         tuple(p.canonical_bytes(row.document) for row in second.plan.artifacts))

    def test_every_depth_role_path_pages_names_full_payload_and_exact_ascii_bytes(self):
        for depth in range(7):
            planner,request,_=planner_assembly(depth=depth)
            result=planner.plan(request)
            self.assertIs(type(result),p.PlannerResult)
            plan=result.plan
            self.assertEqual(3**depth,len(plan.role_assignments))
            self.assertEqual((3**depth+31)//32,len(plan.artifacts))
            self.assertEqual(plan.source_state_identity,plan.source_realm)
            self.assertEqual(plan.destination_state_identity,plan.destination_realm)
            for ordinal,assignment in enumerate(plan.role_assignments):
                n=ordinal; digits=''
                for _ in range(depth): digits=str(n%3)+digits;n//=3
                path='r'+digits
                role='ROOT' if not digits else ('CONTINUATION','POSITIVE','NEGATIVE')[int(digits[-1])]
                self.assertEqual((path,role,ordinal), (assignment.node_path,assignment.role_kind,assignment.ordinal))
                self.assertEqual('plan:operation:plan:assignment:'+path,assignment.assignment_reference)
            for index,artifact in enumerate(plan.artifacts):
                self.assertEqual(f'ywe-test_project-manifest-{index:03d}.json',artifact.name)
                expected=json.dumps(artifact.document.to_record(),sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii')
                self.assertEqual(hashlib.sha256(expected).hexdigest(),artifact.content_sha256)
                self.assertEqual(len(expected),artifact.content_byte_count)
                self.assertFalse(expected.endswith(b'\n'))
                self.assertEqual(tuple(plan.topology_nodes[index*32:(index+1)*32]),tuple(row.node for row in artifact.document.rows))
            self.assertTrue(planner.validate_owned_result(result))

    def test_false_axiom_warning_combinations_and_explicit_inspect_only_preserve_declared_values(self):
        from itertools import product
        for flags in product((False,True),repeat=5):
            planner,request,_=planner_assembly(flags=flags,choice='INSPECT_ONLY')
            result=planner.plan(request)
            self.assertIs(type(result),p.PlannerResult)
            self.assertEqual(tuple('A'+str(i+1)+'_FAILED' for i,passed in enumerate(flags) if not passed),result.plan.warnings)
            self.assertIs(result.plan.axiom_subject,request.axioms.request.subject)
            self.assertEqual((),result.plan.artifacts)
            self.assertFalse(result.plan.target_constraints.allow_declared_axiom_failures)

    def test_constraints_refuse_complete_prefix_without_shortening_or_default_substitution(self):
        planner,request,_=planner_assembly(depth=1)
        for constraints in (replace(request.target_constraints,max_artifacts=0),
                            replace(request.target_constraints,max_document_bytes=1),
                            replace(request.target_constraints,max_total_document_bytes=1)):
            result=planner.plan(replace(request,target_constraints=constraints))
            self.assertIs(type(result),p.PlannerFailure)
            self.assertEqual('TARGET_CONSTRAINT_UNSATISFIED',result.failure_code)
            self.assertEqual(request.topology.nodes,result.request.topology.nodes)
            self.assertEqual('REFERENCE_MANIFEST_PAGES',result.request.inputs.emission_choice)
            self.assertEqual(1,len(result.produced_diagnostics))

    def test_no_io_instance_overrides_and_original_owner_result_seals(self):
        planner,request,owners=planner_assembly()
        model,encoder,registry,topology,axioms=owners
        called=[]
        model.validate_diagnosis=lambda *_:called.append('validate')
        model.inspect_state=lambda *_:called.append('inspect')
        model._orbit=lambda *_:called.append('orbit')
        with patch('builtins.open',side_effect=AssertionError('unexpected IO')):
            result=ReferenceGenerationPlanner.plan(planner,request)
        self.assertEqual([],called)
        self.assertTrue(ReferenceGenerationPlanner.validate_owned_result(planner,result))
        for copier in (copy.copy,lambda owner:copy.deepcopy(owner,{id(model):model})):
            copied=copier(planner)
            with self.assertRaises(p.PlannerEmitterContractError): ReferenceGenerationPlanner.plan(copied,request)
        copied=copy.copy(result)
        object.__setattr__(copied,'_self_identity',copied)
        self.assertFalse(planner.validate_owned_result(copied))
        object.__setattr__(result.plan.metadata,'profile_id','foreign')
        self.assertFalse(planner.validate_owned_result(result))

    def test_foreign_dependency_and_mismatched_full_final_origin_refuse(self):
        planner,request,_=planner_assembly()
        copied=copy.copy(request.chain)
        object.__setattr__(copied,'_self_identity',copied)
        result=planner.plan(replace(request,chain=copied))
        self.assertIs(type(result),p.PlannerFailure)
        self.assertEqual(('DEPENDENCY_FOREIGN','request.chain'),(result.failure_code,result.failed_field))
        result=planner.plan(replace(request,final_origin_diagnosis=request.origin_diagnosis))
        self.assertIs(type(result),p.PlannerFailure)
        self.assertEqual('DEPENDENCY_MISMATCH',result.failure_code)


if __name__=='__main__': unittest.main()
