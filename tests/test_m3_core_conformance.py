"""Actual repeated foundational outputs and audited source mapping, without nested execution."""
import itertools
import ast
import json
from pathlib import Path
import sys
import unittest

from core.ash_pattern_engine import generation_values as g
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.state_model import StateModel
from core.ash_pattern_engine.normalization import RecordingNormalizationCapture
from core.ash_pattern_engine.realm_transition import RealmEncoder
from core.ash_pattern_engine.topology import ReferenceTopologyGenerator
from tests import test_m3_state_model as state_fixtures
from tests import test_m3_recovery as recovery_fixtures
from tests.test_m3_normalization import NormalizationTestCase,operation_context
from tests.test_m3_realm_transition_values import assembly,diagnosis
from tests.test_m3_topology import module_model,diagnosis as topology_diagnosis

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import check_m3_acceptance as acceptance
from run_validation_unit_tests import MAPPING_PATH


def wire(value):
    return json.dumps(value.to_record(),ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')


class CoreConformanceTests(unittest.TestCase):
    def test_repeated_actual_normalization_all_outcomes_have_identical_complete_wire(self):
        fixture=NormalizationTestCase()
        for signature,expected in (('100000000','ALREADY_VALID'),('100011110','NORMALIZED'),
                                   ('000000000','NOT_NORMALIZABLE'),('bad','BLOCKED')):
            packets=[]
            for repeat in range(2):
                model=fixture.model(capture=RecordingNormalizationCapture())
                origin=fixture.diagnose(model,signature,'repeat:origin')
                plan=fixture.plan(model,origin,'repeat:plan')
                actual=StateModel.apply_normalization(model,plan,normalization_context=operation_context('repeat:operation'))
                self.assertEqual(actual.outcome,expected)
                self.assertEqual(origin.to_record(),actual.original_diagnosis.to_record())
                packets.append(wire(actual))
            self.assertEqual(packets[0],packets[1])

    def test_repeated64_context_classifications_and_all_valid_wrw_encodings_are_byte_equal(self):
        fixture=state_fixtures.ModelTestCase()
        binding=state_fixtures.profile_binding()
        candidates={'VALID':'100000000','TRANSFORMATION_COMPATIBLE':'100011110',
                    'TRANSFORMATION_INCOMPATIBLE':'000000000','UNCLASSIFIED':'00000000'}
        for status,candidate in candidates.items():
            for index,flags in enumerate(itertools.product((False,True),repeat=4)):
                halt,contained,correction,fallback=flags
                context=state_fixtures.diagnostic_context('repeat:class:'+status+':'+str(index))
                subject=context.original_input_reference if status=='UNCLASSIFIED' else 'ash_state_'+candidate
                evidence=state_fixtures.evidence(binding,context,subject,correction=correction,fallback=fallback)
                packets=[]
                for repeat in range(2):
                    actual=StateModel.assess(fixture.make_model(binding),candidate,
                        context=sv.SystemContext(is_in_safe_halt=halt,is_in_containment=contained),
                        classification_evidence=evidence,diagnostic_context=context)
                    self.assertEqual(actual.system_state_class,state_fixtures.CLASS_MATRIX[status][index])
                    packets.append(wire(actual))
                self.assertEqual(packets[0],packets[1])
        model,encoder,_registry=assembly()
        for bit in range(9):
            origin=diagnosis(model,f'{1<<bit:09b}','repeat:encode:'+str(bit))
            first=RealmEncoder.encode(encoder,origin,operation_reference='repeat:encoding')
            second=RealmEncoder.encode(encoder,origin,operation_reference='repeat:encoding')
            self.assertTrue(RealmEncoder.validate_owned_result(encoder,first))
            self.assertTrue(RealmEncoder.validate_owned_result(encoder,second))
            self.assertEqual(first.identity.realm_id,'ash_state_'+origin.parsed_state.signature)
            self.assertEqual(wire(first),wire(second))

    def test_every_topology_depth_repeated_structure_lineage_and_complete_bytes(self):
        model=module_model()
        origin=topology_diagnosis(model)
        owner=ReferenceTopologyGenerator(model,g.TopologyAxiomPolicyBinding(*g.POLICY_FIELDS))
        for depth in range(7):
            request=g.TopologyRequest('repeat:topology',origin,depth,'explicit-seed')
            first=ReferenceTopologyGenerator.generate(owner,request)
            second=ReferenceTopologyGenerator.generate(owner,request)
            self.assertEqual(len(first.nodes),3**depth)
            self.assertEqual(first.nodes,second.nodes)
            self.assertEqual(wire(first),wire(second))
            self.assertTrue(ReferenceTopologyGenerator.validate_owned_result(owner,first))

    def test_repeated_actual_seven_recovery_categories_have_identical_complete_diagnostics(self):
        fixture=recovery_fixtures.RecoveryIntegrationTests()
        fixture.setUp()
        cases=(('STABLE',0,False,False,False,False),('UNSTABLE',fixture.g1,False,False,False,False),
            ('CORRECTABLE',fixture.g1,True,False,False,False),('DEGRADED',1,False,True,False,False),
            ('CONTAINED',0,False,False,False,True),('FAILED',1,False,False,False,False),
            ('SAFE_HALT',0,False,False,True,False))
        for expected,integer,known,fallback,halt,contained in cases:
            packets=[]
            for repeat in range(2):
                model,origin,engine,*_ports=fixture.fixture(original=integer,known=known,fallback=fallback,halt=halt,contained=contained)
                actual=engine.recover(origin,operation_context=recovery_fixtures.operation(origin))
                self.assertEqual(origin.system_state_class,expected)
                self.assertEqual(actual.completion_observation.status,'COMPLETE')
                self.assertFalse(actual.session_effects_performed)
                fixture.assert_chain(actual)
                packets.append(wire(actual))
            self.assertEqual(packets[0],packets[1])

    def test_issued_core_owner_paths_have_real_bodies_and_no_runtime_placeholder(self):
        paths=('core/core_values.py','core/deterministic_policy.py','core/module_lifecycle.py','core/orchestration.py',
            'core/cosmology_engine/cosmology.py','core/realm_engine/realm.py','core/ash_pattern_engine/core_facade.py',
            'core/narrative_engine/narrative.py','core/perception_engine/perception.py')
        for relative in paths:
            source=(ROOT/relative).read_text(encoding='utf-8')
            tree=ast.parse(source,filename=relative)
            methods=[node for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
            self.assertTrue(methods,relative)
            for method in methods:
                substantive=[node for node in method.body if not (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and type(node.value.value) is str)]
                self.assertTrue(substantive,relative+':'+method.name)
                self.assertFalse(len(substantive)==1 and isinstance(substantive[0],ast.Pass),relative+':'+method.name)
                self.assertFalse(any(isinstance(node,ast.Constant) and node.value is Ellipsis for node in ast.walk(method)),relative+':'+method.name)
                self.assertFalse(any(isinstance(node,ast.Name) and node.id=='NotImplementedError' for node in ast.walk(method)),relative+':'+method.name)

    def test_audited_definition_selectors_bind_exact_original_bodies_without_executing_them(self):
        mapping=json.loads((ROOT/MAPPING_PATH).read_text(encoding='utf-8'))
        canonical=acceptance.canonical_definitions(ROOT)
        self.assertEqual(len(mapping['required_invariants']),28)
        self.assertEqual(mapping['category_sizes'],{'1':9,'2':5,'3':5,'4':4,'5':5})
        for actual,expected in zip(mapping['required_invariants'],canonical):
            for name,value in expected.items():self.assertEqual(actual[name],value)
            self.assertEqual(acceptance.mapped_source_errors(ROOT,actual),[])
        for field,definitions in acceptance.expected_obligations(ROOT).items():
            self.assertEqual(len(mapping[field]),len(definitions))
            for actual,expected in zip(mapping[field],definitions):
                for name,value in expected.items():self.assertEqual(actual[name],value)
                self.assertEqual(acceptance.mapped_source_errors(ROOT,actual),[])


if __name__=='__main__':unittest.main()
