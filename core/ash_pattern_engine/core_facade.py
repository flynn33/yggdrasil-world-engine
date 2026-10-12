"""Lossless ASH-backed pattern projections from an original captured-plan permit."""
from .. import core_values as cv
from .state_model import StateModel


class AshCoreFacade(cv._ConfiguredOwner):
    __slots__ = ('_model',)
    CORE_OWNER = 'ASH_FACADE'

    def __init__(self,binding,state_model):
        cv._initialize_owner(self,binding,AshCoreFacade)
        self._model=cv._validate_model(state_model,binding)

    def configuration(self):
        binding=cv._owner_configuration(self,AshCoreFacade)
        cv._validate_model(self._model,binding)
        return binding

    def validate_owned_result(self,result):
        try:
            return cv._validate_result(self,result,AshCoreFacade.configuration(self))
        except cv.CoreContractError:
            return False

    def project_patterns(self,permit,projection_rules,*,snapshot_ref):
        binding=AshCoreFacade.configuration(self)
        cv._text(snapshot_ref,'ID','snapshot_ref')
        from ..orchestration import CoreOrchestrator
        if not CoreOrchestrator.validate_plan_permit(permit,binding=binding):
            return cv._operation_result(self,AshCoreFacade,snapshot_ref,None,'PROVENANCE',status='REFUSED',
                code='CORE_PROVENANCE_MISSING',field='generation_plan_ref')
        if type(projection_rules) is not tuple or len(projection_rules)>64:
            cv._fail('rules')
        for row in projection_rules:
            if type(row) is not cv.PatternProjectionRule:
                cv._fail('rules')
            cv.revalidate_value(row)
        if len({row.pattern_id for row in projection_rules})!=len(projection_rules):
            cv._fail('pattern_id','CORE_PROFILE_CONFLICT')
        actual=permit.plan_result
        request=actual.request
        source=request.source_encoding.identity
        destination=request.destination_encoding.identity
        validation=StateModel.validate_diagnosis(self._model,request.final_origin_diagnosis)
        if validation.status!='VERIFIED':
            return cv._operation_result(self,AshCoreFacade,snapshot_ref,None,'BINDING',status='REFUSED',code='CORE_BINDING_MISMATCH',field='destination_signature')
        normalization=permit.normalization_result
        step=None if normalization is None or not normalization.steps else normalization.steps[0]
        trace=[]
        if step is not None:
            index=cv.state.CANONICAL_CODEWORDS.index(step.codeword.bits)
            trace.append('ash_codeword_'+f'{index:02d}')
        trace.extend(row.selected_definition.transition_id for row in request.chain.steps)
        trace=tuple(trace)
        observations=[]
        index=int(destination.state_signature,2)
        for row in sorted(projection_rules,key=lambda row:row.pattern_id):
            matched=row.membership_mask[index]=='1' and (not row.codeword_ids or bool(set(row.codeword_ids)&set(trace)))
            observations.append(cv.PatternObservation(row.pattern_id,matched,row.strength_q6 if matched else 0,trace,row.evidence_refs))
        refs=[permit.original_origin.assessment_binding.diagnosis_reference,
              request.origin_diagnosis.assessment_binding.diagnosis_reference,
              request.final_origin_diagnosis.assessment_binding.diagnosis_reference]
        if normalization is not None:
            refs.append(normalization.operation_binding.operation_reference)
        provenance=cv.CoreProvenance(snapshot_ref,request.final_origin_diagnosis.assessment_binding.diagnosis_reference,
            actual.plan.plan_reference,tuple(dict.fromkeys(refs)))
        value=cv.CosmicPatternSnapshot(snapshot_ref,binding,
            permit.original_origin.parsed_state.signature if normalization is not None else None,
            source.state_signature,source,destination.state_signature,destination,step,tuple(observations),trace,provenance)
        return cv._operation_result(self,AshCoreFacade,snapshot_ref,value,'PATTERN_PROJECTION',
            status='COMPLETED' if any(row.matched for row in observations) else 'NO_OP',
            evidence=(actual.plan.plan_reference,),explanation='Destination-mask projections retained the complete actual normalization and transition trace.')
