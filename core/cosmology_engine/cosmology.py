"""Neutral nine-coordinate structure over an explicit, validated ASH baseline."""
from .. import core_values as cv
from ..ash_pattern_engine.state_model import StateModel
import json


class CosmologyEngine(cv._ConfiguredOwner):
    __slots__ = ('_model',)
    CORE_OWNER = 'COSMOLOGY'

    def __init__(self, binding, state_model):
        cv._initialize_owner(self, binding, CosmologyEngine)
        self._model = cv._validate_model(state_model, binding)

    def configuration(self):
        binding = cv._owner_configuration(self, CosmologyEngine)
        cv._validate_model(self._model, binding)
        return binding

    def validate_owned_result(self, result):
        try:
            return cv._validate_result(self, result, CosmologyEngine.configuration(self))
        except cv.CoreContractError:
            return False

    def initialize_cosmos(self, baseline, *, operation_reference):
        binding = CosmologyEngine.configuration(self)
        cv._text(operation_reference, 'ID', 'operation_reference')
        if type(baseline) is not cv.state.StateDiagnosis:
            cv._fail('baseline')
        cv._peer_guard(baseline, set())
        validation = StateModel.validate_diagnosis(self._model, baseline)
        if validation.status != 'VERIFIED' or baseline.parsed_state is None or baseline.state_validity_diagnostic.admissibility_status != 'VALID':
            return cv._operation_result(self, CosmologyEngine, operation_reference, None, 'BINDING',
                status='REFUSED', code='CORE_BINDING_MISMATCH' if validation.status != 'VERIFIED' else 'CORE_CAPABILITY_UNAVAILABLE',
                field='baseline', evidence=(baseline.assessment_binding.assessment_reference,))
        value = cv.CosmicState(binding, baseline, tuple('b'+str(index) for index in range(9)))
        return cv._operation_result(self, CosmologyEngine, operation_reference, value, 'BINDING',
            evidence=(baseline.assessment_binding.assessment_reference,),
            explanation='The supplied valid diagnosis defines the neutral baseline; coordinates are b0 through b8.')

    def get_profile_realm_definitions(self):
        return tuple(sorted(CosmologyEngine.configuration(self).profile_realms, key=lambda row: row.realm_id))

    @staticmethod
    def _compile_profile_realms(raw,definitions):
        """Match explicit eligibility facts to original metadata, with no defaults."""
        if type(raw) is not bytes or len(raw)>cv.MAX_RAW_CORE_BYTES or type(definitions) is not tuple:
            cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
        for row in definitions:
            if type(row) is not cv.ProfileRealmDefinition:
                cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
            cv.revalidate_value(row)
        try:
            metadata=json.loads(raw.decode('utf-8'))
        except (UnicodeError,json.JSONDecodeError):
            cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
        if type(metadata) is not dict or type(metadata.get('coordinate_bindings')) is not list or type(metadata.get('realms')) is not list:
            cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
        mappings=metadata['coordinate_bindings']
        if len(mappings)!=9 or len(definitions)!=9:
            cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
        indices,ids=set(),set()
        declared={row.realm_id:row for row in definitions}
        if len(declared)!=9:
            cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
        for row in mappings:
            if type(row) is not dict or type(row.get('coordinate_index')) is not int or not 0<=row['coordinate_index']<9 or type(row.get('realm_id')) is not str:
                cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
            index,identifier=row['coordinate_index'],row['realm_id']
            if index in indices or identifier in ids or identifier not in declared or type(row.get('ordinal')) is not int or row['ordinal']!=index+1:
                cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
            actual=declared[identifier]
            if actual.coordinate!=index or actual.display_name!=row.get('presentation_label'):
                cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
            indices.add(index);ids.add(identifier)
        if any(type(identifier) is not str for identifier in metadata['realms']) or len(metadata['realms'])!=9 or set(metadata['realms'])!=ids:
            cv._fail('profile_realms','CORE_PROFILE_CONFLICT')
        if any(origin not in ids for row in definitions for origin in row.allowed_origins):
            cv._fail('allowed_origins','CORE_UNKNOWN_REFERENCE')
        return tuple(sorted(definitions,key=lambda row:row.realm_id))
