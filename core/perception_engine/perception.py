"""Declared truth views preserve their exact objective input graph."""
from .. import core_values as cv


_TIER_ORDER = {'OBJECTIVE_SHARED':0, 'OBJECTIVE_BRANCH':1, 'OBJECTIVE_PLAYER':2, 'DERIVED_INTERPRETATION':3}


def _truth_facts(truth):
    if type(truth) is not cv.TruthInputSnapshot:
        cv._fail('truth_input')
    cv.revalidate_value(truth)
    seen, result = {}, []
    for fact in truth.facts:
        key = fact.scope_ref, fact.subject_ref, fact.fact_id, fact.authority_tier
        digest = cv._wire_digest(fact)
        prior = seen.get(key)
        if prior is not None:
            if digest in prior:
                continue
            if fact.authority_tier != 'DERIVED_INTERPRETATION':
                cv._fail('facts', 'CORE_FACT_CONFLICT')
        seen.setdefault(key,set()).add(digest)
        result.append(fact)
    return tuple(sorted(result, key=lambda fact:(fact.scope_ref,fact.subject_ref,fact.fact_id,
        _TIER_ORDER[fact.authority_tier],fact.value_token,cv._wire_digest(fact))))


def _contradictions(facts):
    values = {}
    for fact in facts:
        key = fact.scope_ref, fact.subject_ref, fact.fact_id
        values.setdefault(key,set()).add(fact.value_token)
    return tuple(sorted({key[2] for key,tokens in values.items() if len(tokens)>1}))


class PerceptionEngine(cv._ConfiguredOwner):
    __slots__ = ()
    CORE_OWNER = 'PERCEPTION'

    def __init__(self, binding):
        cv._initialize_owner(self, binding, PerceptionEngine)

    def configuration(self):
        return cv._owner_configuration(self, PerceptionEngine)

    def validate_owned_result(self, result):
        try:
            return cv._validate_result(self, result, PerceptionEngine.configuration(self))
        except cv.CoreContractError:
            return False

    def compose_overlay(self, request):
        PerceptionEngine.configuration(self)
        if type(request) is not cv.PerceptionRequest:
            cv._fail('request')
        cv.revalidate_value(request)
        reference = 'perception:' + cv._wire_digest(request)
        try:
            facts = _truth_facts(request.truth)
            entities = tuple(sorted(set(request.truth.entity_refs)))
            if len(entities) != len(request.truth.entity_refs):
                cv._fail('entity_refs', 'CORE_FACT_CONFLICT')
            for rule in request.rules:
                if rule.entity_ref not in entities:
                    cv._fail('entity_ref', 'CORE_UNKNOWN_REFERENCE')
                known = {fact.fact_id for fact in facts if fact.scope_ref == request.truth.scope_ref and fact.subject_ref == rule.subject_ref}
                if any(condition not in known for condition in rule.condition_fact_refs):
                    cv._fail('condition_fact_refs', 'CORE_UNKNOWN_REFERENCE')
        except cv.CoreContractError as error:
            return cv._operation_result(self, PerceptionEngine, reference, None, 'TRUTH_PRECEDENCE',
                status='REFUSED', code=error.code, field=error.field_name, evidence=(request.truth.snapshot_ref,))
        observations, visible, hidden, tags = [], [], [], set()
        for entity in entities:
            selected = None
            rows = sorted((row for row in request.rules if row.entity_ref == entity), key=lambda row:(-row.priority,row.rule_id))
            for rule in rows:
                matches = rule.subject_ref == request.subject_ref
                observations.append(cv.CoreDiagnostic(reference+':rule:'+str(len(observations)), self.CORE_OWNER,
                    'VISIBILITY', 'COMPLETED' if matches else 'NO_OP', None, 'rule_id',
                    (request.truth.snapshot_ref,rule.rule_id),
                    'Rule subject and declared fact presence matched.' if matches else 'The rule subject did not match the requested view.'))
                if selected is None and matches:
                    selected = rule
            is_visible = selected.visible if selected is not None else True
            (visible if is_visible else hidden).append(entity)
            if selected is not None:
                tags.update(selected.interpretation_tags)
        if len(tags)>64:
            return cv._operation_result(self, PerceptionEngine, reference, None, 'RESOURCE_LIMIT',
                status='REFUSED',code='CORE_RESOURCE_LIMIT',field='tags',evidence=(request.truth.snapshot_ref,))
        overlay = cv.PerceptionOverlay(reference+':overlay',request,cv._wire_digest(request.truth),tuple(observations),
            tuple(visible),tuple(hidden),tuple(sorted(tags)),_contradictions(facts),'NONE')
        return cv._operation_result(self, PerceptionEngine, reference, overlay, 'VISIBILITY',
            status='COMPLETED' if entities else 'NO_OP', evidence=(request.truth.snapshot_ref,),
            explanation='Subject-specific visibility preserved the complete declared truth graph and entity partition.')
