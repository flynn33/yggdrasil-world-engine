"""Original bounded leases, immutable cutover receipts and concurrent cancellation."""
import copy
import threading
import unittest
from dataclasses import replace
from core import core_values as v
from core.deterministic_policy import DeterministicPolicy
from core.module_lifecycle import CoreModuleLifecycle, CoreExecutionGate, ModuleTicket
from tests.test_m3_core_values import core_binding
from tests.test_m3_module_diagnostics import assembly


class CoreLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.owner = DeterministicPolicy(core_binding())
        self.lifecycle = CoreModuleLifecycle(self.owner)

    def test_start_stop_exact_replay_snapshot_count_and_no_restart(self):
        first = self.lifecycle.start('start',expected_generation=0)
        self.assertEqual((first.before.generation,first.after.generation,first.after.ledger_used),(0,1,1))
        self.assertIs(self.lifecycle.start('start',expected_generation=0),first)
        stopped = self.lifecycle.stop('stop',expected_generation=1)
        self.assertEqual((stopped.after.generation,stopped.after.phase,stopped.after.ledger_used),(2,'STOPPED',2))
        self.assertIs(self.lifecycle.stop('stop',expected_generation=1),stopped)
        self.assertEqual(self.lifecycle.start('restart',expected_generation=2).status,'REFUSED')
        self.assertIs(self.lifecycle.start('start',expected_generation=0),first)
        self.assertEqual(self.lifecycle.status().phase,'STOPPED')

    def test_failed_start_closed_generation_and_original_lifecycle_identity(self):
        replica = copy.copy(self.lifecycle)
        replica._self = replica
        with self.assertRaises(v.CoreContractError):
            replica.status()
        object.__setattr__(self.owner._core_binding, 'profile_realms',
            (v.ProfileRealmDefinition('named',0,None,'Name',0,False,()),))
        failed = self.lifecycle.start('failed',expected_generation=0)
        self.assertEqual((failed.status,failed.after.generation,failed.after.phase,failed.after.closed),('REFUSED',1,'FAILED',True))
        self.assertIs(self.lifecycle.start('failed',expected_generation=0),failed)
        self.assertEqual(self.lifecycle.start('again',expected_generation=1).status,'REFUSED')

    def test_ledger_shutdown_slot_and_max8_inflight_no_eviction(self):
        self.lifecycle.start('start',expected_generation=0)
        for index in range(62):
            actual = self.owner.normalize((v.WeightedOption('option'+str(index),1),))
            ticket = self.lifecycle.admit(actual.operation_reference,expected_generation=1,operation_bindings=())
            self.assertIs(type(ticket),ModuleTicket)
            self.assertEqual(self.lifecycle.complete(ticket,actual).status,'COMPLETED')
            self.assertIs(self.lifecycle.complete(ticket,actual),ticket._completed)
        self.assertEqual(self.lifecycle.status().ledger_used,63)
        self.assertEqual(self.lifecycle.admit('overflow',expected_generation=1,operation_bindings=()).status,'REFUSED')
        stopped = self.lifecycle.stop('stop',expected_generation=1)
        self.assertEqual(stopped.after.ledger_used,64)
        self.assertIs(self.lifecycle.stop('stop',expected_generation=1),stopped)
        owner = DeterministicPolicy(core_binding())
        other = CoreModuleLifecycle(owner)
        other.start('start',expected_generation=0)
        for index in range(8):
            self.assertIs(type(other.admit('work'+str(index),expected_generation=1,operation_bindings=())),ModuleTicket)
        self.assertEqual(other.admit('ninth',expected_generation=1,operation_bindings=()).status,'REFUSED')
        self.assertEqual(other.status().inflight,8)

    def test_original_child_operation_stage_caps_token_busy_and_copy_refusal(self):
        diagnostics = assembly()[0]
        self.lifecycle.start('start',expected_generation=0)
        ticket = self.lifecycle.admit('work',expected_generation=1,operation_bindings=(('work:child',('COSMOLOGY',)),))
        original = self.lifecycle.execution_gate(ticket,diagnostics)
        child = CoreExecutionGate.for_operation(original,'work:child','COSMOLOGY')
        self.assertTrue(CoreExecutionGate.validate_issued_for_collector(child,diagnostics,'work:child'))
        self.assertFalse(CoreExecutionGate.validate_issued_for_collector(child,diagnostics,'work:other'))
        with self.assertRaises(v.CoreContractError):
            copy.copy(child)
        forged = object.__new__(CoreExecutionGate)
        for name in CoreExecutionGate.__slots__:
            object.__setattr__(forged,name,object.__getattribute__(child,name))
        self.assertFalse(CoreExecutionGate.validate_issued_for_collector(forged,diagnostics,'work:child'))
        with self.assertRaises(v.CoreContractError):
            CoreExecutionGate.for_operation(child,'work:child','COSMOLOGY')
        with self.assertRaises(v.CoreContractError):
            CoreExecutionGate.for_operation(original,'work:child:invented','COSMOLOGY')
        with self.assertRaises(v.CoreContractError):
            child.stage_grant('NARRATIVE')
        for index in range(64):
            grant = child.stage_grant('COSMOLOGY')
            self.assertEqual((grant.status,grant.grant_sequence),('GRANTED',index+1))
        self.assertEqual(child.stage_grant('COSMOLOGY').status,'UNAVAILABLE')
        child._token_lock.acquire()
        try:
            self.assertEqual(child.capture_disposition(),'UNAVAILABLE')
            stopped = self.lifecycle.stop('stop',expected_generation=1)
            self.assertEqual(stopped.status,'PENDING')
            self.assertEqual(child.capture_disposition(),'SEALED')
        finally:
            child._token_lock.release()
        self.assertEqual(child.stage_grant('COSMOLOGY').status,'CANCELLED')

    def test_concurrent_stop_returns_before_blocked_granted_body_and_preserves_late_value(self):
        diagnostics = assembly()[0]
        options = (v.WeightedOption('late',1),)
        reference = self.owner.normalize(options).operation_reference
        self.lifecycle.start('start',expected_generation=0)
        ticket = self.lifecycle.admit(reference,expected_generation=1,operation_bindings=((reference,('COSMOLOGY',)),))
        gate = self.lifecycle.execution_gate(ticket,diagnostics)
        entered, release = threading.Event(), threading.Event()
        observations, errors = [], []
        def work():
            try:
                observations.append(gate.stage_grant('COSMOLOGY'))
                entered.set()
                if not release.wait(5):
                    raise AssertionError('release was not signaled')
                actual = self.owner.normalize(options)
                observations.extend((actual,gate.stage_grant('COSMOLOGY'),self.lifecycle.complete(ticket,actual)))
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=work)
        thread.start()
        try:
            self.assertTrue(entered.wait(5))
            stopped = self.lifecycle.stop('stop',expected_generation=1)
            self.assertEqual((stopped.status,stopped.after.phase),('PENDING','STOPPING'))
            self.assertTrue(thread.is_alive())
            self.assertEqual(gate.capture_disposition(),'SEALED')
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors,[])
        self.assertEqual((observations[0].status,observations[2].status,observations[3].status),('GRANTED','CANCELLED','INTERRUPTED'))
        self.assertTrue(self.owner.validate_owned_result(observations[1]))
        self.assertEqual((self.lifecycle.status().phase,self.lifecycle.status().generation),('STOPPED',2))
        self.assertIs(self.lifecycle.stop('stop',expected_generation=1),stopped)
        self.assertEqual(stopped.after.phase,'STOPPING')

    def test_wrong_or_copied_result_cannot_borrow_cached_completion(self):
        self.lifecycle.start('start',expected_generation=0)
        actual=self.owner.normalize((v.WeightedOption('actual',1),))
        ticket=self.lifecycle.admit(actual.operation_reference,expected_generation=1,operation_bindings=())
        first=self.lifecycle.complete(ticket,actual)
        self.assertEqual(first.status,'COMPLETED')
        for wrong in (copy.copy(actual),self.owner.normalize((v.WeightedOption('other',1),)),object()):
            refused=self.lifecycle.complete(ticket,wrong)
            self.assertEqual((refused.status,refused.result_ref),('REFUSED',None))
        self.assertIs(self.lifecycle.complete(ticket,actual),first)

    def test_hostile_reflected_gate_and_lifecycle_metadata_never_enters_caller_hooks(self):
        calls=[]
        class Meta(type):
            def __eq__(cls,other):calls.append('type-equality');return False
            def __hash__(cls):calls.append('type-hash');return 0
        class Hostile(metaclass=Meta):
            def __getattribute__(self,name):calls.append('get:'+name);raise AttributeError(name)
            def __eq__(self,other):calls.append('equality');return False
            def __hash__(self):calls.append('hash');return 0
            def __bool__(self):calls.append('bool');return False
            def __str__(self):calls.append('str');return 'hostile'
        diagnostics=assembly()[0]
        self.lifecycle.start('start',expected_generation=0)
        ticket=self.lifecycle.admit('work',expected_generation=1,operation_bindings=(('work',('COSMOLOGY',)),))
        gate=self.lifecycle.execution_gate(ticket,diagnostics)
        cookie=gate._cookie
        # Both substituted immutable cookies and corrupted original fields refuse.
        for field in ('binding','reference','generation','stages','collector','ticket','lifecycle'):
            original=getattr(cookie,field)
            for substituted in (True,False):
                if substituted:
                    gate._cookie=replace(cookie,**{field:Hostile()})
                else:
                    object.__setattr__(cookie,field,Hostile())
                try:
                    self.assertFalse(CoreExecutionGate.validate_issued_for_collector(gate,diagnostics,'work'))
                    with self.assertRaises(v.CoreContractError):gate.configuration()
                finally:
                    object.__setattr__(cookie,field,original)
                    gate._cookie=cookie
        for field in ('_sealed','_token_lock'):
            original=getattr(gate,field)
            object.__setattr__(gate,field,Hostile())
            try:self.assertEqual(gate.capture_disposition(),'UNAVAILABLE')
            finally:object.__setattr__(gate,field,original)
        for field in ('_sequence','_children','_bindings','_gates','_completed','_generation','_reference'):
            original=getattr(ticket,field)
            setattr(ticket,field,Hostile())
            try:
                self.assertFalse(CoreExecutionGate.validate_issued_for_collector(gate,diagnostics,'work'))
                self.assertEqual(gate.capture_disposition(),'UNAVAILABLE')
                with self.assertRaises(v.CoreContractError):gate.stage_grant('COSMOLOGY')
                with self.assertRaises(v.CoreContractError):CoreExecutionGate.for_operation(gate,'work','COSMOLOGY')
            finally:setattr(ticket,field,original)
        original=ticket._sealed
        ticket._sealed=Hostile()
        try:self.assertEqual(gate.capture_disposition(),'UNAVAILABLE')
        finally:ticket._sealed=original
        original_owner,original_type=self.lifecycle._owner,self.lifecycle._owner_type
        self.lifecycle._owner,self.lifecycle._owner_type=Hostile(),Hostile
        try:
            with self.assertRaises(v.CoreContractError):self.lifecycle.status()
        finally:self.lifecycle._owner,self.lifecycle._owner_type=original_owner,original_type
        for invalid in (Hostile(),object.__new__(CoreExecutionGate)):
            self.assertFalse(CoreExecutionGate.validate_issued_for_collector(invalid,diagnostics,'work'))
            self.assertEqual(CoreExecutionGate.capture_disposition(invalid),'UNAVAILABLE')
            with self.assertRaises(v.CoreContractError):CoreExecutionGate.configuration(invalid)
        self.assertEqual(calls,[])
        self.assertEqual(gate.capture_disposition(),'ACTIVE')
        self.assertEqual(gate.stage_grant('COSMOLOGY').status,'GRANTED')

    def test_shutdown_seals_a_completed_tickets_original_and_child_tokens(self):
        diagnostics=assembly()[0]
        self.lifecycle.start('start',expected_generation=0)
        actual=self.owner.normalize((v.WeightedOption('actual',1),))
        ticket=self.lifecycle.admit(actual.operation_reference,expected_generation=1,
            operation_bindings=((actual.operation_reference+':child',('COSMOLOGY',)),))
        original=self.lifecycle.execution_gate(ticket,diagnostics)
        child=CoreExecutionGate.for_operation(original,actual.operation_reference+':child','COSMOLOGY')
        self.assertEqual(self.lifecycle.complete(ticket,actual).status,'COMPLETED')
        self.assertEqual(self.lifecycle.status().inflight,0)
        self.assertEqual(child.capture_disposition(),'SEALED')
        self.assertEqual(self.lifecycle.stop('stop',expected_generation=1).status,'COMPLETED')
        for gate in (original,child):
            self.assertEqual(gate.capture_disposition(),'SEALED')
        self.assertEqual(child.stage_grant('COSMOLOGY').status,'CANCELLED')

    def test_reflected_legitimate_collector_or_registered_scope_does_not_change_issuance(self):
        original,foreign=assembly()[0],assembly()[0]
        self.lifecycle.start('start',expected_generation=0)
        ticket=self.lifecycle.admit('work',expected_generation=1,
            operation_bindings=(('work:one',('COSMOLOGY',)),('work:two',('COSMOLOGY',))))
        gate=self.lifecycle.execution_gate(ticket,original)
        child=CoreExecutionGate.for_operation(gate,'work:one','COSMOLOGY')
        for field,value,collector,reference in (('collector',foreign,foreign,'work:one'),
                                               ('reference','work:two',original,'work:two')):
            before=getattr(child._cookie,field)
            object.__setattr__(child._cookie,field,value)
            try:
                self.assertFalse(CoreExecutionGate.validate_issued_for_collector(child,collector,reference))
                self.assertEqual(child.capture_disposition(),'UNAVAILABLE')
                with self.assertRaises(v.CoreContractError):child.stage_grant('COSMOLOGY')
            finally:object.__setattr__(child._cookie,field,before)
        self.assertTrue(CoreExecutionGate.validate_issued_for_collector(child,original,'work:one'))
        old_cookie,old_metadata=child._cookie,child._issued_metadata
        rebuilt=replace(old_cookie,collector=foreign,reference='work:two')
        child._cookie=child._issued_cookie=rebuilt
        child._issued_metadata=(rebuilt.original,rebuilt.lifecycle,rebuilt.ticket,rebuilt.collector,rebuilt.reference,
            rebuilt.generation,rebuilt.stages,rebuilt.binding,rebuilt.binding_sha256,rebuilt.parent)
        try:
            self.assertFalse(CoreExecutionGate.validate_issued_for_collector(child,foreign,'work:two'))
            self.assertEqual(child.capture_disposition(),'UNAVAILABLE')
            with self.assertRaises(v.CoreContractError):child.configuration()
            with self.assertRaises(v.CoreContractError):child.stage_grant('COSMOLOGY')
        finally:
            child._cookie=child._issued_cookie=old_cookie
            child._issued_metadata=old_metadata
        self.assertTrue(CoreExecutionGate.validate_issued_for_collector(child,original,'work:one'))

    def test_copied_gate_and_ticket_rebound_self_metadata_have_no_original_issuance_membership(self):
        diagnostics=assembly()[0]
        self.lifecycle.start('start',expected_generation=0)
        ticket=self.lifecycle.admit('work',expected_generation=1,operation_bindings=(('work:child',('COSMOLOGY',)),))
        original=self.lifecycle.execution_gate(ticket,diagnostics)
        child=CoreExecutionGate.for_operation(original,'work:child','COSMOLOGY')
        clone=object.__new__(CoreExecutionGate)
        for name in CoreExecutionGate.__slots__:object.__setattr__(clone,name,object.__getattribute__(child,name))
        cookie=replace(child._cookie,original=clone)
        clone._cookie=clone._issued_cookie=cookie
        clone._issued_metadata=(clone,*child._issued_metadata[1:])
        self.assertFalse(CoreExecutionGate.validate_issued_for_collector(clone,diagnostics,'work:child'))
        self.assertEqual(clone.capture_disposition(),'UNAVAILABLE')
        with self.assertRaises(v.CoreContractError):clone.stage_grant('COSMOLOGY')
        ticket_clone=object.__new__(ModuleTicket)
        for name in ModuleTicket.__slots__:object.__setattr__(ticket_clone,name,object.__getattribute__(ticket,name))
        ticket_clone._original=ticket_clone
        ticket_clone._gates=[clone]
        cookie=replace(cookie,ticket=ticket_clone)
        clone._cookie=clone._issued_cookie=cookie
        clone._issued_metadata=(clone,cookie.lifecycle,ticket_clone,*child._issued_metadata[3:])
        self.assertFalse(CoreExecutionGate.validate_issued_for_collector(clone,diagnostics,'work:child'))
        before=self.lifecycle.status()
        with self.assertRaises(v.CoreContractError):self.lifecycle.complete(ticket_clone,self.owner.normalize((v.WeightedOption('x',1),)))
        self.assertEqual(before,self.lifecycle.status())
        self.assertTrue(CoreExecutionGate.validate_issued_for_collector(child,diagnostics,'work:child'))

    def test_copied_lifecycle_ticket_gate_and_private_ledgers_cannot_replace_owner_backlink(self):
        diagnostics=assembly()[0]
        self.lifecycle.start('start',expected_generation=0)
        ticket=self.lifecycle.admit('work',expected_generation=1,operation_bindings=(('work:child',('COSMOLOGY',)),))
        original=self.lifecycle.execution_gate(ticket,diagnostics)
        child=CoreExecutionGate.for_operation(original,'work:child','COSMOLOGY')
        lifecycle_clone=copy.copy(self.lifecycle)
        lifecycle_clone._self=lifecycle_clone
        lifecycle_clone._ledger=dict(self.lifecycle._ledger)
        ticket_clone=object.__new__(ModuleTicket)
        for name in ModuleTicket.__slots__:object.__setattr__(ticket_clone,name,object.__getattribute__(ticket,name))
        ticket_clone._original=ticket_clone
        ticket_clone._lifecycle=lifecycle_clone
        gate_clone=object.__new__(CoreExecutionGate)
        for name in CoreExecutionGate.__slots__:object.__setattr__(gate_clone,name,object.__getattribute__(child,name))
        cookie=replace(child._cookie,original=gate_clone,lifecycle=lifecycle_clone,ticket=ticket_clone)
        gate_clone._cookie=gate_clone._issued_cookie=cookie
        metadata=(gate_clone,lifecycle_clone,ticket_clone,cookie.collector,cookie.reference,cookie.generation,
            cookie.stages,cookie.binding,cookie.binding_sha256,cookie.parent)
        gate_clone._issued_metadata=metadata
        ticket_clone._gates=[(gate_clone,cookie,metadata)]
        lifecycle_clone._ledger['work']=(self.lifecycle._ledger['work'][0],ticket_clone)
        self.assertIs(self.owner._core_lifecycle,self.lifecycle)
        self.assertFalse(CoreExecutionGate.validate_issued_for_collector(gate_clone,diagnostics,'work:child'))
        self.assertEqual(gate_clone.capture_disposition(),'UNAVAILABLE')
        with self.assertRaises(v.CoreContractError):gate_clone.stage_grant('COSMOLOGY')
        self.assertTrue(CoreExecutionGate.validate_issued_for_collector(child,diagnostics,'work:child'))


if __name__ == '__main__':
    unittest.main()
