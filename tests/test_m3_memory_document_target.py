"""Actual owned target commits/readbacks under explicit test-issued action leases."""
import copy
from dataclasses import replace
import hashlib
import unittest

from core.ash_pattern_engine import planner_emitter_values as p, state_values as s
from core.ash_pattern_engine.artifact_emitter import ReferenceArtifactEmitter
from core.ash_pattern_engine.memory_document_target import MemoryDocumentTarget, UINT64_MAX
from tests.test_m3_generation_planner import planner_assembly
from tests.test_m3_realm_transition_values import profile_from
from tests.test_m3_module_diagnostics import assembly as collector_assembly


def target_assembly():
    c1,c2=s.CANONICAL_CODEWORDS[1:3]
    signatures=tuple(''.join(map(str,bits)) for bits in ((0,)*9,c1,c2,tuple(a^b for a,b in zip(c1,c2))))
    planner,request,owners=planner_assembly(profile=profile_from(signatures,'target:H4'))
    plan=planner.plan(request).plan
    collector,*_=collector_assembly()
    target=MemoryDocumentTarget(p.MemoryTargetConfiguration('target:memory','REFERENCE_MEMORY_DOCUMENTS',
                                plan.binding.policy_binding,32,1048576))
    emitter=ReferenceArtifactEmitter(owners[0],plan.binding,collector,target)
    return target,emitter,plan,planner,request


def test_lease(target,emitter,artifact,operation='target:operation',revision=None):
    revision=target.snapshot().revision if revision is None else revision
    return p._issue_action_lease(emitter,target,operation,artifact,revision)


class MemoryDocumentTargetTests(unittest.TestCase):
    def test_reflected_target_state_locks_and_document_children_reject_before_hooks(self):
        target,emitter,plan,_,_=target_assembly()
        artifact=plan.artifacts[0]
        target.materialize(test_lease(target,emitter,artifact),artifact)
        hooks=[]
        class Hostile:
            def __bool__(self):hooks.append('bool');return False
            def __eq__(self,other):hooks.append('eq');return False
            def __iter__(self):hooks.append('iter');return iter(())
            def acquire(self,*args):hooks.append('acquire');return False
            def __str__(self):hooks.append('str');return 'foreign'
        original_snapshot=target.snapshot()
        for field in ('_lock','_lease_lock','_revision','_documents','_leases','_active_leases'):
            original=getattr(target,field)
            setattr(target,field,Hostile())
            try:
                with self.assertRaises(p.PlannerEmitterContractError):target.snapshot()
            finally:setattr(target,field,original)
        document=next(iter(target._documents.values()))
        original=document.actual_byte_count
        object.__setattr__(document,'actual_byte_count',Hostile())
        try:
            with self.assertRaises(p.PlannerEmitterContractError):target.snapshot()
        finally:object.__setattr__(document,'actual_byte_count',original)
        self.assertEqual(hooks,[])
        self.assertEqual(target.snapshot(),original_snapshot)

    def test_actual_atomic_commit_ascii_readback_idempotence_and_single_use(self):
        target,emitter,plan,_,_=target_assembly()
        artifact=plan.artifacts[0]
        lease=test_lease(target,emitter,artifact)
        receipt=target.materialize(lease,artifact)
        self.assertEqual(('SUCCEEDED',True,0,1,'OWNED_EXACT_READBACK'),
            (receipt.actual_status,receipt.actual_effects,receipt.target_revision_before,receipt.target_revision_after,receipt.readback_assurance))
        snapshot=target.snapshot()
        self.assertEqual(1,snapshot.revision)
        raw=p.canonical_bytes(artifact.document)
        self.assertEqual(raw.decode('ascii'),snapshot.documents[0].content_ascii)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),snapshot.documents[0].actual_sha256)
        self.assertEqual(len(raw),snapshot.actual_byte_count)
        repeated=target.materialize(test_lease(target,emitter,artifact,'target:repeat'),artifact)
        self.assertEqual(('NO_EFFECT',False,1,1),(repeated.actual_status,repeated.actual_effects,repeated.target_revision_before,repeated.target_revision_after))
        reused=target.materialize(lease,artifact)
        self.assertEqual(('FAILED','TARGET_RESOURCE_LIMIT'),(reused.actual_status,reused.failure_code))
        self.assertEqual(snapshot,target.snapshot())

    def test_conflict_preserves_actual_existing_hash_bytes_and_revision(self):
        target,emitter,plan,planner,request=target_assembly()
        first=plan.artifacts[0]
        target.materialize(test_lease(target,emitter,first),first)
        changed=planner.plan(replace(request,operation_reference='other:operation')).plan.artifacts[0]
        result=target.materialize(test_lease(target,emitter,changed,'target:conflict'),changed)
        self.assertEqual(('FAILED',False,'DOCUMENT_CONFLICT'),(result.actual_status,result.actual_effects,result.failure_code))
        self.assertEqual(first.content_sha256,result.observed_sha256)
        self.assertEqual((1,1),(result.target_revision_before,result.target_revision_after))
        self.assertEqual(first.document.plan_reference,target.snapshot().documents[0].plan_reference)

    def test_version_exhaustion_before_mutation_and_existing_no_op_at_max(self):
        target,emitter,plan,_,_=target_assembly()
        artifact=plan.artifacts[0]
        # Controlled internal fixture sets the actual boundary, without a public version-reset API.
        target._revision=UINT64_MAX
        result=target.materialize(test_lease(target,emitter,artifact),artifact)
        self.assertEqual(('FAILED',False,'TARGET_VERSION_EXHAUSTED'),(result.actual_status,result.actual_effects,result.failure_code))
        self.assertEqual((),target.snapshot().documents)
        target._revision=0
        target.materialize(test_lease(target,emitter,artifact,'target:first'),artifact)
        target._revision=UINT64_MAX
        result=target.materialize(test_lease(target,emitter,artifact,'target:noeffect'),artifact)
        self.assertEqual(('NO_EFFECT',False,UINT64_MAX),(result.actual_status,result.actual_effects,result.target_revision_after))

    def test_busy_stale_copy_mutation_and_original_target_refuse_without_effect(self):
        target,emitter,plan,_,_=target_assembly()
        artifact=plan.artifacts[0]
        lease=test_lease(target,emitter,artifact)
        with self.assertRaises(p.PlannerEmitterContractError): copy.copy(lease)
        copied=object.__new__(p.EmissionActionLease)
        for name in p.EmissionActionLease.__slots__:
            object.__setattr__(copied,name,object.__getattribute__(lease,name))
        with self.assertRaises(p.PlannerEmitterContractError): target.materialize(copied,artifact)
        copytarget=copy.copy(target)
        with self.assertRaises(p.PlannerEmitterContractError): copytarget.materialize(lease,artifact)
        target._lock.acquire()
        try: result=target.materialize(lease,artifact)
        finally: target._lock.release()
        self.assertEqual(('FAILED',False,'TARGET_BUSY'),(result.actual_status,result.actual_effects,result.failure_code))
        self.assertEqual('TARGET_RESOURCE_LIMIT',target.materialize(lease,artifact).failure_code)
        stale=target.materialize(test_lease(target,emitter,artifact,'target:stale',revision=1),artifact)
        self.assertEqual(('FAILED',False,'TARGET_STALE_REVISION'),(stale.actual_status,stale.actual_effects,stale.failure_code))
        self.assertEqual((),target.snapshot().documents)
        fresh=test_lease(target,emitter,artifact,'target:corrupt')
        object.__setattr__(fresh,'_revision',1)
        with self.assertRaises(p.PlannerEmitterContractError): target.materialize(fresh,artifact)

    def test_metadata_lock_busy_still_consumes_the_original_action_once(self):
        target,emitter,plan,_,_=target_assembly()
        artifact=plan.artifacts[0]
        lease=test_lease(target,emitter,artifact,'target:metadata-busy')
        target._lease_lock.acquire()
        try:refused=target.materialize(lease,artifact)
        finally:target._lease_lock.release()
        self.assertEqual((refused.actual_status,refused.actual_effects,refused.failure_code),('FAILED',False,'TARGET_BUSY'))
        reused=target.materialize(lease,artifact)
        self.assertEqual((reused.actual_status,reused.actual_effects,reused.failure_code),('FAILED',False,'TARGET_RESOURCE_LIMIT'))
        self.assertEqual(target.snapshot().documents,())

    def test_document_count_capacity_has_no_eviction_or_overwrite(self):
        target,emitter,_,planner,request=target_assembly()
        for index in range(32):
            inputs=replace(request.inputs,project_name='project'+str(index))
            plan=planner.plan(replace(request,operation_reference='capacity:plan'+str(index),inputs=inputs)).plan
            artifact=plan.artifacts[0]
            receipt=target.materialize(test_lease(target,emitter,artifact,'capacity:emit'+str(index)),artifact)
            self.assertEqual('SUCCEEDED',receipt.actual_status)
        before=target.snapshot()
        plan=planner.plan(replace(request,operation_reference='capacity:extra',inputs=replace(request.inputs,project_name='extra'))).plan
        artifact=plan.artifacts[0]
        result=target.materialize(test_lease(target,emitter,artifact,'capacity:refuse'),artifact)
        self.assertEqual(('FAILED',False,'TARGET_RESOURCE_LIMIT'),(result.actual_status,result.actual_effects,result.failure_code))
        self.assertEqual(before,target.snapshot())
        self.assertEqual(32,len(before.documents))


if __name__=='__main__': unittest.main()
