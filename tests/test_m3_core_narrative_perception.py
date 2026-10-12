"""Exact scoring, relationship, cluster and immutable truth view controls."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from core import core_values as v
from core.narrative_engine.narrative import NarrativeEngine
from core.perception_engine.perception import PerceptionEngine
from core.ash_pattern_engine import realm_transition_values as rt
from core.ash_pattern_engine.realm_transition import RealmEncoder
from tests.test_m3_core_cosmology_realm import pure_model
from tests.test_m3_realm_transition_values import diagnosis


def snapshot(binding,model):
    rb=rt.RealmTransitionBinding(binding.canonical_binding,binding.profile_binding,
        tuple(rt.RealmTransitionSourcePin(*row) for row in rt.GENERATION_SOURCE_PINS),*rt.POLICY_IDENTITIES[0],'policy:evidence')
    origin=diagnosis(model,'000000000')
    identity=RealmEncoder(model,rb).encode(origin,operation_reference='source').identity
    provenance=v.CoreProvenance('snapshot','dx','plan',('ash',))
    return v.CosmicPatternSnapshot('snapshot',binding,None,'000000000',identity,'000000000',identity,None,(),(),provenance)


def archetype(identifier,*,symbolic=(),truth=(),shadow=(),wolf=None,compatible=(),friction=(),contradicts=(),realm=(),phase=(),evidence=('fact',),affinities=()):
    return v.ArchetypeRecord(identifier,'character',symbolic,truth,shadow,realm,wolf,phase,compatible,friction,contradicts,affinities,(),evidence)


def context(*,symbolic=(),truth=(),shadow=(),wolf=None,realm=(),phase=None,recurrence=(),myth=(),prophecy=(),domain=None,tension=(),higher=(),basis=(),risk=()):
    return v.ArchetypeContext('context',symbolic,truth,shadow,realm,wolf,phase,recurrence,myth,prophecy,domain,tension,higher,basis,risk)


def registry(records,clusters=()):
    source=v.RegistrySource('primary','0'*64,'source:evidence')
    return v.ArchetypeRegistry('registry',source,v.RegistrySource('matrix','1'*64,'matrix:evidence'),records,clusters)


class CoreNarrativePerceptionTests(unittest.TestCase):
    def setUp(self):
        self.binding,self.model=pure_model()
        self.snapshot=snapshot(self.binding,self.model)
        self.owner=NarrativeEngine(self.binding)

    def test_all_features_once_exact_rounding_declared_reference_match_and_shallow_penalty(self):
        row=archetype('a',symbolic=('s',),truth=('t',),shadow=('h',),wolf=v.WolfBias(400000,200000),realm=('realm',),phase=('phase',),evidence=('rec','myth','prophecy'))
        ctx=context(symbolic=('s','s'),truth=('t',),shadow=('h',),wolf=v.WolfPressure(500000,500000,('wolf',)),realm=(v.WeightedOption('realm',1000000),),phase='phase',recurrence=('rec',),myth=('myth',),prophecy=('prophecy',),domain='quest')
        result=self.owner.evaluate_archetypes(self.snapshot,ctx,registry((row,)))
        # 1M+800k+600k+350k+60k+250k+150k+100k+100k-200k.
        self.assertEqual(result.value.scores[0].score_q6,3210000)
        self.assertEqual(result.value.dominant,('a',))
        self.assertEqual(len(result.value.scores[0].reasons),10)
        self.assertTrue(self.owner.validate_owned_result(result))

    def test_secondary_and_dominant_exact_equality_and_one_tick_neighbors(self):
        ctx=context(symbolic=('s',),truth=('t',),wolf=v.WolfPressure(1000000,0,('wolf',)),realm=(v.WeightedOption('r',3),))
        rows=(archetype('sminus',truth=('t',),wolf=v.WolfBias(-5,0)),archetype('sequal',truth=('t',)),archetype('splus',truth=('t',),wolf=v.WolfBias(5,0)),
              archetype('dminus',symbolic=('s',),wolf=v.WolfBias(999995,0)),archetype('dequal',symbolic=('s',),wolf=v.WolfBias(1000000,0)),archetype('dplus',symbolic=('s',),wolf=v.WolfBias(1000000,0),realm=('r',)))
        result=self.owner.evaluate_archetypes(self.snapshot,ctx,registry(rows)).value
        values={row.archetype_id:(row.score_q6,row.selected_role) for row in result.scores}
        self.assertEqual(values,{'sminus':(799999,'INELIGIBLE'),'sequal':(800000,'SECONDARY'),'splus':(800001,'SECONDARY'),
            'dminus':(1199999,'SECONDARY'),'dequal':(1200000,'DOMINANT'),'dplus':(1200001,'DOMINANT')})

    def test_pair_precedence_ascii_suppression_unambiguous_explicit_pair_and_complete_records(self):
        rows=(archetype('a:b',symbolic=('s',),compatible=('c',),friction=('c',),contradicts=('c',)),archetype('c',symbolic=('s',)))
        first=self.owner.evaluate_archetypes(self.snapshot,context(symbolic=('s',)),registry(rows)).value
        pair=first.relationships[0]
        self.assertEqual((pair.relation,pair.score_delta_q6,pair.suppressed_id),('CONTRADICTION',-1000000,'c'))
        token='pair:'+hashlib.sha256(json.dumps(['a:b','c'],separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
        allowed=self.owner.evaluate_archetypes(self.snapshot,context(symbolic=('s',),higher=(token,)),registry(rows)).value
        self.assertTrue(allowed.relationships[0].coexistence_allowed)
        self.assertIsNone(allowed.relationships[0].suppressed_id)
        other='pair:'+hashlib.sha256(json.dumps(['a','b:c'],separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
        self.assertNotEqual(token,other)
        unlisted=self.owner.evaluate_archetypes(self.snapshot,context(symbolic=('s',),higher=(other,)),registry(rows)).value
        self.assertFalse(unlisted.relationships[0].coexistence_allowed)
        reverse=registry(rows[::-1])
        self.assertEqual(allowed.relationships,self.owner.evaluate_archetypes(self.snapshot,context(symbolic=('s',),higher=(token,)),reverse).value.relationships)

    def test_cluster_strict_members_activation_equality_neighbors_and_unsupported_basis(self):
        ctx=context(symbolic=('s',),truth=('t',),wolf=v.WolfPressure(1000000,0,('wolf',)),basis=('basis',),risk=('risk',))
        cluster=v.ClusterRecord('cluster',('a','b'),('basis',),'STABLE','risk')
        for wolf,expected in ((499995,False),(500000,True),(500005,True)):
            rows=(archetype('a',symbolic=('s',)),archetype('b',truth=('t',),wolf=v.WolfBias(wolf,0)))
            actual=self.owner.evaluate_archetypes(self.snapshot,ctx,registry(rows,(cluster,))).value.cluster_scores[0]
            self.assertEqual(actual.final_score_q6,2100000+(wolf-500000)//5)
            self.assertEqual(actual.activated,expected)
        equal_member=self.owner.evaluate_archetypes(self.snapshot,ctx,registry((archetype('a',truth=('t',)),archetype('b',truth=('t',))),(cluster,))).value.cluster_scores[0]
        self.assertEqual(equal_member.qualifying_members,())
        unsupported=self.owner.evaluate_archetypes(self.snapshot,context(symbolic=('s',),truth=('t',)),registry((archetype('a',symbolic=('s',)),archetype('b',symbolic=('s',))),(cluster,))).value.cluster_scores[0]
        self.assertEqual((unsupported.support_penalty_q6,unsupported.activated),(-500000,False))

    def test_original_evaluation_provenance_and_declared_truth_conflict_scope(self):
        result=self.owner.evaluate_archetypes(self.snapshot,context(symbolic=('s',)),registry((archetype('a',symbolic=('s',)),)))
        fact=v.DeclaredTruthFact('fact','OBJECTIVE_SHARED','scope','subject','actual',('evidence',))
        lower=v.DeclaredTruthFact('fact','DERIVED_INTERPRETATION','scope','subject','belief',('belief',))
        truth=v.TruthInputSnapshot('truth','scope',(lower,fact,fact),('entity',),'DECLARED_INPUT')
        interpreted=self.owner.interpret(result.value,truth,interpretation_ref='interpretation')
        self.assertEqual(interpreted.value.provenance,self.snapshot.provenance)
        self.assertEqual(interpreted.value.contradiction_refs,('fact',))
        alternative=v.DeclaredTruthFact('fact','DERIVED_INTERPRETATION','scope','subject','otherBelief',('belief',))
        deduped=self.owner.read_memory_view(v.TruthInputSnapshot('derived','scope',(lower,alternative,lower),(),'DECLARED_INPUT'))
        self.assertEqual(len(deduped),2)
        self.assertEqual(self.owner.interpret(copy.copy(result.value),truth,interpretation_ref='copied').status,'REFUSED')
        conflicting=v.DeclaredTruthFact('fact','OBJECTIVE_SHARED','scope','subject','other',('evidence',))
        with self.assertRaises(v.CoreContractError):
            self.owner.read_memory_view(v.TruthInputSnapshot('bad','scope',(fact,conflicting),(),'DECLARED_INPUT'))
        separate=v.DeclaredTruthFact('fact','OBJECTIVE_SHARED','otherScope','subject','other',('evidence',))
        self.assertEqual(len(self.owner.read_memory_view(v.TruthInputSnapshot('separate','scope',(fact,separate),(),'DECLARED_INPUT'))),2)

    def test_two_subject_views_priority_all_rules_and_unchanged_objective_truth(self):
        owner=PerceptionEngine(self.binding)
        facts=(v.DeclaredTruthFact('f','OBJECTIVE_SHARED','scope','subjectA','false',('evidence',)),)
        truth=v.TruthInputSnapshot('truth','scope',facts,('entityA','entityB'),'DECLARED_INPUT')
        provenance=self.snapshot.provenance
        rules=(v.PerceptionRule('lower',0,'subjectA','entityA',('f',),True,('lowerTag',)),v.PerceptionRule('first',1,'subjectA','entityA',('f',),False,('hiddenTag',)))
        actual=owner.compose_overlay(v.PerceptionRequest('view','subjectA',truth,rules,provenance))
        self.assertEqual((actual.value.visible_entities,actual.value.hidden_entities,actual.value.tags),(('entityB',),('entityA',),('hiddenTag',)))
        self.assertEqual(len(actual.value.evaluated_rules),2)
        second=owner.compose_overlay(v.PerceptionRequest('viewB','subjectB',truth,rules,provenance))
        self.assertEqual(second.value.visible_entities,('entityA','entityB'))
        self.assertEqual(actual.value.truth_sha256,second.value.truth_sha256)
        self.assertIs(actual.value.request.truth,truth)
        bad=v.PerceptionRule('bad',2,'subjectA','missing',(),False,())
        self.assertEqual(owner.compose_overlay(v.PerceptionRequest('bad','subjectA',truth,(bad,),provenance)).diagnostics[0].failure_code,'CORE_UNKNOWN_REFERENCE')

    def test_compile_actual_primary_families_exact_decimal_lexemes_and_matrix_disagreement(self):
        root=Path(__file__).resolve().parents[1]
        names=('data/pattern_archetypes/character_archetypes.yaml','data/quest_archetypes/quest_archetypes.yaml',
            'data/pattern_archetypes/region_archetypes.yaml','data/pattern_archetypes/faction_archetypes.yaml',
            'data/pattern_archetypes/transformation_archetypes.yaml','data/pattern_archetypes/event_archetypes.yaml',
            'data/pattern_archetypes/pattern_clusters.yaml')
        sources=tuple((name,(root/name).read_bytes()) for name in names)
        matrix_name='data/pattern_archetypes/compatibility_matrix.yaml'
        matrix=(matrix_name,(root/matrix_name).read_bytes())
        actual=NarrativeEngine._compile_registry(sources,matrix,registry_id='compiled:wrw',evidence_ref='source:evidence')
        self.assertEqual((len(actual.archetypes),len(actual.clusters)),(47,5))
        seeker=next(row for row in actual.archetypes if row.archetype_id=='char_seeker')
        self.assertEqual((seeker.wolf_bias.white_q6,seeker.wolf_bias.dark_q6),(400000,200000))
        self.assertEqual(actual.relationship_source.source_sha256,hashlib.sha256(matrix[1]).hexdigest())
        bad=(matrix_name,matrix[1].replace(b'compatible: [char_weaver, char_harbinger, char_exile]',b'compatible: [char_weaver]',1))
        with self.assertRaises(v.CoreContractError):
            NarrativeEngine._compile_registry(sources,bad,registry_id='conflict',evidence_ref='source:evidence')
        precise=(sources[0][0],sources[0][1].replace(b'white: 0.4',b'white: 0.4000001',1))
        with self.assertRaises(v.CoreContractError):
            NarrativeEngine._compile_registry((precise,*sources[1:]),matrix,registry_id='precise',evidence_ref='source:evidence')
        # Complete47-row format is legal; its1081pair operation refuses the fixed256 budget.
        refused=self.owner.evaluate_archetypes(self.snapshot,context(),actual)
        self.assertEqual(refused.diagnostics[0].failure_code,'CORE_RESOURCE_LIMIT')


if __name__=='__main__':
    unittest.main()
