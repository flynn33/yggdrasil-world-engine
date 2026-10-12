"""Pure complete deterministic reference plans [YWE-REQ-0049]."""
import hashlib

from . import planner_emitter_values as p
from . import state_values as s
from . import generation_values as g
from .realm_transition import RealmEncoder, TransitionRegistry
from .topology import ReferenceTopologyGenerator
from .axioms import ReferenceAxiomEvaluator
from .state_model import StateModel

_OWNER = object()


def record_reference(operation, ordinal=0):
    p._ref(operation, maximum=160)
    return "pe:"+hashlib.sha256(operation.encode("ascii")).hexdigest()+":"+str(ordinal)


class ReferenceGenerationPlanner:
    __slots__ = ("_model", "_binding", "_encoder", "_registry", "_topology", "_axioms", "_cookie")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("ReferenceGenerationPlanner is final")

    def __init__(self, model, binding, encoder, registry, topology, axioms):
        p._exact(model, StateModel, "model")
        p._exact(binding, p.PlannerEmitterBinding, "binding")
        p._exact(encoder, RealmEncoder, "encoder")
        p._exact(registry, TransitionRegistry, "registry")
        p._exact(topology, ReferenceTopologyGenerator, "topology")
        p._exact(axioms, ReferenceAxiomEvaluator, "axioms")
        self._model, self._binding, self._encoder, self._registry, self._topology, self._axioms = model, binding, encoder, registry, topology, axioms
        self._cookie = (_OWNER, self, model, binding, encoder, registry, topology, axioms)
        ReferenceGenerationPlanner.configuration(self)

    def configuration(self):
        p._exact(self, ReferenceGenerationPlanner, "planner")
        cookie = self._cookie
        if (type(cookie) is not tuple or len(cookie) != 8 or cookie[0] is not _OWNER or cookie[1] is not self or
                any(actual is not expected for actual, expected in zip(cookie[2:],
                    (self._model, self._binding, self._encoder, self._registry, self._topology, self._axioms)))):
            p._fail("planner", "VALUE_CORRUPT")
        p.revalidate_value(self._binding)
        binding = self._binding
        canonical,profile=p._model_bindings(self._model)
        if binding.canonical_binding != canonical or binding.profile_binding != profile:
            p._fail("binding", "SOURCE_UNRECOGNIZED")
        for cls, owner in ((RealmEncoder,self._encoder), (TransitionRegistry,self._registry)):
            actual = cls.configuration(owner)
            if actual.canonical_binding != binding.canonical_binding or actual.profile_binding != binding.profile_binding:
                p._fail("binding", "SOURCE_UNRECOGNIZED")
        for cls, owner in ((ReferenceTopologyGenerator,self._topology),(ReferenceAxiomEvaluator,self._axioms)):
            source, profile, _ = cls.configuration(owner)
            if source.canonical_binding != binding.canonical_binding or profile != binding.profile_binding:
                p._fail("binding", "SOURCE_UNRECOGNIZED")
        return binding

    def validate_owned_result(self, result):
        if type(self) is not ReferenceGenerationPlanner:
            return False
        try:
            binding = ReferenceGenerationPlanner.configuration(self)
            return (p._result_is_owned(result,self,(p.PlannerResult,p.PlannerFailure)) and result.binding == binding)
        except (p.PlannerEmitterContractError, s.StateContractError, g.GenerationContractError, ValueError, AttributeError):
            return False

    def plan(self, request):
        binding = ReferenceGenerationPlanner.configuration(self)
        p._exact(request, p.PlannerRequest, "request")
        p.revalidate_value(request)
        if p.raw_business_size(request) > p.RAW_BUSINESS_LIMIT:
            p._fail("raw_business_packet", "RAW_BUSINESS_LIMIT")
        refused = _request_failure(self, request, binding)
        if refused is not None:
            return _failure(self,request,binding,*refused)
        plan_reference=request.operation_reference+":plan"
        destination=request.chain.last_candidate
        assignments=tuple(p.RoleAssignment(plan_reference+":assignment:"+node.path_token,node.node_id,node.path_token,
                          "role:"+node.branch_kind,node.branch_kind.upper(),destination,node.ordinal,
                          request.inputs.role_profile_id) for node in request.topology.nodes)
        warnings=p._warnings(request.axioms.axiom_diagnostic)
        refs=(request.source_encoding.operation_reference,request.chain.operation_reference,
              request.destination_encoding.operation_reference,request.topology.request.request_reference,
              request.axioms.request.request_reference)
        metadata=p.PlanMetadata(request.operation_reference,request.inputs.profile_id,
                request.origin_diagnosis.assessment_binding.diagnosis_reference,
                request.final_origin_diagnosis.assessment_binding.diagnosis_reference,
                refs[1],refs[3],refs[4],request.inputs.role_profile_id,request.inputs.naming_policy_id,
                request.inputs.subject_policy_id,request.inputs.artifact_policy_id,request.inputs.normalization_mode,
                "ABSTRACT_NO_EXTERNAL_EFFECTS")
        artifacts=[]
        if request.inputs.emission_choice == "REFERENCE_MANIFEST_PAGES":
            pages=(len(assignments)+31)//32
            for index in range(pages):
                rows=tuple(p.ManifestRow(node,assignment) for node,assignment in
                           zip(request.topology.nodes[index*32:(index+1)*32],assignments[index*32:(index+1)*32]))
                document=p.ReferenceManifestDocument("YWE_REFERENCE_MANIFEST",plan_reference,request.inputs.project_name,
                         index,pages,request.origin_diagnosis.parsed_state.signature,destination.signature,
                         request.source_encoding.identity,request.destination_encoding.identity,request.axioms.request.subject,
                         request.axioms.axiom_diagnostic,warnings,request.inputs,binding.canonical_binding.aggregate_sha256,
                         binding.policy_binding,refs,rows)
                content=p.canonical_bytes(document)
                if len(content)>32768:
                    return _failure(self,request,binding,"TARGET_CONSTRAINT_UNSATISFIED","plan.artifacts")
                present=tuple(row.assignment.role_reference for row in rows)
                roles=tuple(role for role in ("role:root","role:continuation","role:positive","role:negative") if role in present)
                artifacts.append(p.ArtifactDescription(plan_reference+":artifact:"+f"{index:03d}",
                    plan_reference+":manifest:"+f"{index:03d}","REFERENCE_MANIFEST",
                    "ywe-"+request.inputs.project_name+"-manifest-"+f"{index:03d}"+".json",index,roles,document,
                    "UTF8_ASCII_JSON_SORTED_COMPACT_NO_NEWLINE",hashlib.sha256(content).hexdigest(),len(content),
                    request.inputs.artifact_policy_id))
        constraints=request.target_constraints
        if (len(artifacts)>constraints.max_artifacts or any(row.content_byte_count>constraints.max_document_bytes for row in artifacts) or
                sum(row.content_byte_count for row in artifacts)>constraints.max_total_document_bytes):
            return _failure(self,request,binding,"TARGET_CONSTRAINT_UNSATISFIED","request.target_constraints")
        plan=p.ReferenceGenerationPlan(plan_reference,binding,request.origin_diagnosis.parsed_state,
             request.source_encoding.identity,request.destination_encoding.identity,request.source_encoding.identity,
             request.destination_encoding.identity,request.topology.nodes,assignments,request.axioms.request.subject,
             request.axioms.axiom_diagnostic,tuple(artifacts),warnings,constraints,request.inputs,metadata)
        payload=p.PlanDiagnostic(request.operation_reference,plan_reference,"COMPLETE",len(assignments),len(artifacts),warnings,None,None)
        result=p.PlannerResult(request,binding,plan,(_record(request,payload,False),))
        return p._seal_result(result,self)


def _request_failure(owner,request,binding):
    for field,origin in (("request.origin",request.origin_diagnosis),("request.final_origin",request.final_origin_diagnosis)):
        validation=StateModel.validate_diagnosis(owner._model,origin)
        if validation.status != "VERIFIED": return "ORIGIN_REJECTED",field
        if origin.parsed_state is None: return "ORIGIN_UNPARSED",field
        if not origin.state_validity_diagnostic.is_valid: return "SOURCE_NOT_NORMALIZED",field
    if request.inputs.profile_id != binding.profile_binding.profile_id: return "DEPENDENCY_MISMATCH","request.inputs"
    dependencies=((RealmEncoder,owner._encoder,request.source_encoding,"request.source_encoding"),
                  (TransitionRegistry,owner._registry,request.chain,"request.chain"),
                  (RealmEncoder,owner._encoder,request.destination_encoding,"request.destination_encoding"),
                  (ReferenceTopologyGenerator,owner._topology,request.topology,"request.topology"),
                  (ReferenceAxiomEvaluator,owner._axioms,request.axioms,"request.axioms"))
    for cls, producer, result, field in dependencies:
        if not cls.validate_owned_result(producer,result): return "DEPENDENCY_FOREIGN",field
    if request.chain.selections != request.inputs.transition_sequence: return "DEPENDENCY_MISMATCH","request.chain"
    if request.source_encoding.origin != request.origin_diagnosis or request.chain.origin != request.origin_diagnosis:
        return "DEPENDENCY_MISMATCH","request.source_encoding"
    destination=request.chain.last_candidate
    if request.final_origin_diagnosis.parsed_state != destination: return "FINAL_DIAGNOSIS_MISMATCH","request.final_origin"
    if (request.destination_encoding.origin != request.final_origin_diagnosis or
            request.topology.request.origin_diagnosis != request.final_origin_diagnosis or
            request.axioms.request.origin_diagnosis != request.final_origin_diagnosis):
        return "DEPENDENCY_MISMATCH","request.destination_encoding"
    if request.topology.request.seed_token != request.inputs.seed_token or request.topology.request.depth != request.inputs.topology_depth:
        return "DEPENDENCY_MISMATCH","request.topology"
    refs=(request.operation_reference,request.origin_diagnosis.assessment_binding.diagnosis_reference,
          request.final_origin_diagnosis.assessment_binding.diagnosis_reference,request.source_encoding.operation_reference,
          request.chain.operation_reference,request.destination_encoding.operation_reference,
          request.topology.request.request_reference,request.axioms.request.request_reference)
    if len(set(refs)) != len(refs): return "REFERENCE_COLLISION","request.reference_set"
    return None


def _record(request,payload,failed):
    root=request.final_origin_diagnosis.emitted_diagnostics[0]
    severity=max((root.envelope.severity,"ERROR" if failed else "WARNING" if payload.warnings else "INFO"),key=p.SEVERITIES.index)
    envelope=p.PlannerEmitterEnvelope("GENERATION_PLAN",severity,"PROCESSING","BLOCKED" if failed else "RESOLVED",
             root.envelope.subject_reference,root.diagnostic_reference,root.envelope.chain_root_reference,
             ("ASH-GENERATION-PLAN-001","ASH-GENERATION-BOUNDARY-001"),
             "Complete deterministic plan constructed." if not failed else "Deterministic plan construction refused.",
             ("Planning produced no target effects.","Every materialized document must retain this complete plan meaning."))
    return p.PlannerEmitterRecord(record_reference(request.operation_reference),envelope,payload)


def _failure(owner,request,binding,code,field):
    validation=StateModel.validate_diagnosis(owner._model,request.final_origin_diagnosis)
    reference=record_reference(request.operation_reference)
    if validation.status=="VERIFIED" and request.final_origin_diagnosis.parsed_state is not None:
        payload=p.PlanDiagnostic(request.operation_reference,None,"REFUSED",0,0,(),code,field)
        records,pending=(_record(request,payload,True),),None
    else:
        records=()
        pending=p.PendingPlannerEmitterDiagnostic(reference,"GENERATION_PLAN","PLAN_BUILD",code,"NO_VERIFIED_ORIGIN")
    return p._seal_result(p.PlannerFailure(request,binding,code,field,records,pending),owner)
