"""Declared realm eligibility and immutable proposals, without world commits."""
from .. import core_values as cv


class RealmEngine(cv._ConfiguredOwner):
    __slots__ = ()
    CORE_OWNER = 'REALM'

    def __init__(self, binding):
        cv._initialize_owner(self, binding, RealmEngine)

    def configuration(self):
        return cv._owner_configuration(self, RealmEngine)

    def validate_owned_result(self, result):
        try:
            return cv._validate_result(self, result, RealmEngine.configuration(self))
        except cv.CoreContractError:
            return False

    def evaluate_access(self, request):
        binding = RealmEngine.configuration(self)
        if type(request) is not cv.RealmAccessRequest:
            cv._fail('request')
        cv.revalidate_value(request)
        # Core result operations have local IDs; upstream refs remain in the value.
        reference = 'access:' + cv._wire_digest(request)
        realms = {row.realm_id: row for row in binding.profile_realms}
        observations = []
        outcomes = []

        def observe(field, condition, evidence=()):
            status = 'COMPLETED' if condition is True else 'REFUSED' if condition is False else 'PENDING'
            code = None if condition is True else 'CORE_PROVENANCE_MISSING' if condition is None else 'CORE_CAPABILITY_UNAVAILABLE'
            outcomes.append(condition)
            observations.append(cv.CoreDiagnostic(reference+':'+str(len(observations)), self.CORE_OWNER,
                'REALM_ACCESS', status, code, field, evidence, 'Declared realm predicate: '+field+'.'))

        observe('source_realm_id', request.source_realm_id in realms)
        observe('target_realm_id', request.target_realm_id in realms)
        if any(fact.realm_id not in realms for fact in request.facts):
            observe('facts', False)
        target = realms.get(request.target_realm_id)
        fact = next((row for row in request.facts if row.realm_id == request.target_realm_id), None)
        if target is not None:
            observe('allowed_origins', request.source_realm_id in target.allowed_origins)
            observe('attunement_q6', None if fact is None else fact.attunement_q6 >= target.threshold_q6,
                    () if fact is None else fact.evidence_refs)
            observe('thin_veil', True if not target.veil_required else None if fact is None or fact.thin_veil == 'UNAVAILABLE' else fact.thin_veil == 'TRUE',
                    () if fact is None else fact.evidence_refs)
        eligible = False if False in outcomes else None if None in outcomes else True
        value = cv.RealmAccessResult(request, eligible, tuple(observations))
        status = 'COMPLETED' if eligible is True else 'REFUSED' if eligible is False else 'PENDING'
        return cv._issue_result(self, cv.CoreResult(reference, binding, status, value, tuple(observations), 'NONE'))

    def propose_shift(self, access, *, proposal_ref):
        RealmEngine.configuration(self)
        cv._text(proposal_ref, 'ID', 'proposal_ref')
        if type(access) is not cv.RealmAccessResult:
            cv._fail('access')
        cv.revalidate_value(access)
        actual = RealmEngine.evaluate_access(self, access.request)
        if cv.canonical_bytes(actual.value) != cv.canonical_bytes(access) or access.eligible is not True:
            return cv._operation_result(self, RealmEngine, proposal_ref, access, 'REALM_ACCESS',
                status='PENDING' if actual.status == 'PENDING' else 'REFUSED', code='CORE_PROVENANCE_MISSING', field='access')
        value = cv.RealmShiftProposal(proposal_ref, access, access.request.source_realm_id,
                                     access.request.target_realm_id, 'PROPOSED_ONLY')
        return cv._operation_result(self, RealmEngine, proposal_ref, value, 'REALM_ACCESS', effect='PROPOSED_ONLY',
                                    evidence=(access.request.request_ref,))
