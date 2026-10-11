"""Closed module capture values and safe projections [YWE-REQ-0048]."""
from __future__ import annotations

from dataclasses import dataclass, fields, make_dataclass
import hashlib
import json
import re

from . import state_values as sv

PRODUCERS = ("REALM_ENCODER", "TRANSITION_REGISTRY", "TOPOLOGY_GENERATOR",
             "AXIOM_EVALUATOR", "GENERATION_PLANNER", "ARTIFACT_EMITTER")
FAILURES = ("MODULE_PRODUCER_FOREIGN", "MODULE_PRODUCER_DUPLICATE",
    "MODULE_PRODUCER_BINDING_MISMATCH", "MODULE_PRODUCER_UNSUPPORTED",
    "MODULE_CONTEXT_REJECTED", "MODULE_ORIGIN_REJECTED", "MODULE_RESULT_REJECTED",
    "MODULE_RESERVATION_REFUSED", "MODULE_RAW_PACKET_LIMIT", "MODULE_CAPTURE_REJECTED",
    "MODULE_CAPTURE_UNCONFIRMED", "MODULE_COMPLETION_MISSING", "MODULE_COMPLETION_REJECTED",
    "MODULE_FINAL_OBSERVATION_REJECTED", "MODULE_REQUIRED_RECORD_MISSING",
    "MODULE_SCOPE_FOREIGN", "MODULE_REPLAY_REFUSED")
COVERAGE = ("COMPLETE_SPECIFIED_SAFE_GRAPH", "PARTIAL", "STORAGE_UNCERTAIN")
RAW_LIMIT = 1_048_576


class ModuleContractError(ValueError):
    def __init__(self, code, field="module_value"):
        if type(code) is not str or code not in FAILURES:
            raise ValueError("invalid module error code")
        self.code, self.field_name = code, field
        super().__init__(code + ": " + field)


def _fail(code="MODULE_CONTEXT_REJECTED", field="module_value"):
    raise ModuleContractError(code, field)


def _choice(value, domain):
    if type(value) is not str or value not in domain:
        _fail()


def _ref(value):
    try:
        sv.InputEvidence.validate_reference(value)
    except (sv.StateContractError, TypeError):
        _fail()


def _is(value, classes):
    return any(type(value) is cls for cls in classes)


def pure_record(value):
    """Serialize only exact owned public module values, without instance hooks."""
    from . import realm_transition_values as rt
    from . import generation_values as gen
    if _is(value, rt.OWNED_TYPES):
        rt.revalidate_value(value)
        return json.loads(rt.canonical_bytes(value))
    if _is(value, gen.WIRE_TYPES):
        gen.revalidate_value(value)
        return json.loads(gen.canonical_bytes(value))
    _fail("MODULE_RESULT_REJECTED")


def pure_bytes(value):
    from . import realm_transition_values as rt
    from . import generation_values as gen
    if _is(value, rt.OWNED_TYPES):
        return rt.canonical_bytes(value)
    if _is(value, gen.WIRE_TYPES):
        return gen.canonical_bytes(value)
    _fail("MODULE_RESULT_REJECTED")


def _record(value):
    from . import diagnostics_values as dv
    kind = type(value)
    if value is None or _is(value, (str, int, bool)):
        return value
    if kind is tuple:
        return [_record(child) for child in value]
    if _is(value, WIRE_TYPES):
        _validate(value)
        return {f.name: _record(object.__getattribute__(value, f.name)) for f in fields(kind)}
    if _is(value, (sv.StateDiagnosis, sv.AvailableProfileBinding, sv.UnavailableProfileBinding)):
        kind.__post_init__(value)
        return kind.to_record(value)
    if _is(value, dv.VALUE_TYPES):
        kind.__post_init__(value)
        return kind.to_record(value)
    return pure_record(value)


def raw_business_bytes(value, *, limit=RAW_LIMIT):
    if type(limit) is not int or not 0 < limit <= RAW_LIMIT:
        _fail("MODULE_RAW_PACKET_LIMIT")
    record = _record(value)
    result = bytearray()
    for part in json.JSONEncoder(ensure_ascii=True, allow_nan=False, separators=(",", ":")).iterencode(record):
        result.extend(part.encode("ascii"))
        if len(result) > limit:
            _fail("MODULE_RAW_PACKET_LIMIT")
    return bytes(result)


def raw_business_size(value, *, limit=RAW_LIMIT):
    try:
        return len(raw_business_bytes(value, limit=limit))
    except ModuleContractError as error:
        if error.code == "MODULE_RAW_PACKET_LIMIT":
            return limit + 1
        raise


class _Wire:
    __slots__ = ()

    def __post_init__(self):
        _validate(self)

    def to_record(self):
        return json.loads(raw_business_bytes(self))


@dataclass(frozen=True, slots=True)
class ModuleProducerRegistrationReceipt(_Wire):
    producer: str | None
    status: str
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class ModuleCaptureContext(_Wire):
    operation_reference: str
    producer: str
    source_binding: object
    origin_diagnosis: sv.StateDiagnosis
    prepared_value: object
    dependency_results: tuple = ()


@dataclass(frozen=True, slots=True)
class ModuleCaptureAdmission:
    operation_reference: str
    status: str
    scope: object | None
    failure_code: str | None

    def __post_init__(self):
        _ref(self.operation_reference)
        _choice(self.status, ("ADMITTED", "REJECTED", "NOT_CONFIRMED"))
        if self.failure_code is not None:
            _choice(self.failure_code, FAILURES)
        if self.status == "ADMITTED" and (self.scope is None or self.failure_code is not None):
            _fail()


@dataclass(frozen=True, slots=True)
class ModuleCaptureReceipt(_Wire):
    operation_reference: str
    status: str
    result: object
    confirmed_records: tuple
    attempted_record: object | None
    completion: object | None
    final_observation: object | None
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class ModuleFinalObservationReceipt(_Wire):
    operation_reference: str
    status: str
    supporting_reference: str | None
    coverage: str
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class ModuleReturnAuditObservation(_Wire):
    operation_reference: str
    status: str
    missing_kind: str
    meta_sequence: int | None
    coverage: str
    failure_code: str | None


WIRE_TYPES = (ModuleProducerRegistrationReceipt, ModuleCaptureContext, ModuleCaptureReceipt,
              ModuleFinalObservationReceipt, ModuleReturnAuditObservation)


def _validate(value):
    from . import diagnostics_values as dv
    kind = type(value)
    if not _is(value, WIRE_TYPES):
        _fail()
    if kind is ModuleProducerRegistrationReceipt:
        if value.producer is not None:
            _choice(value.producer, PRODUCERS)
        _choice(value.status, ("REGISTERED", "REJECTED"))
    else:
        _ref(value.operation_reference)
    if getattr(value, "failure_code", None) is not None:
        _choice(value.failure_code, FAILURES)
    if kind is ModuleCaptureContext:
        _choice(value.producer, PRODUCERS)
        if type(value.origin_diagnosis) is not sv.StateDiagnosis:
            _fail("MODULE_ORIGIN_REJECTED")
        sv.StateDiagnosis.__post_init__(value.origin_diagnosis)
        from . import realm_transition_values as rt
        from . import generation_values as gen
        if type(value.source_binding) is not rt.RealmTransitionBinding and not (
            type(value.source_binding) is tuple and len(value.source_binding) == 3 and
            type(value.source_binding[0]) is gen.TopologyAxiomSourceBinding and
            _is(value.source_binding[1], (sv.AvailableProfileBinding, sv.UnavailableProfileBinding)) and
            type(value.source_binding[2]) is gen.TopologyAxiomPolicyBinding):
            _fail('MODULE_PRODUCER_BINDING_MISMATCH')
        _record(value.source_binding)
        pure_record(value.prepared_value)
        result = value.prepared_value
        if _is(result, rt.RESULT_TYPES):
            expected = 'REALM_ENCODER' if type(result) is rt.RealmEncodingResult or type(result) is rt.RealmTransitionFailure and result.action == 'ENCODE' else 'TRANSITION_REGISTRY'
            if value.producer != expected or type(value.source_binding) is not rt.RealmTransitionBinding or value.source_binding != result.binding or value.operation_reference != result.operation_reference or value.origin_diagnosis != result.origin:
                _fail('MODULE_CONTEXT_REJECTED')
        elif _is(result, gen.PACKET_TYPES):
            expected = 'TOPOLOGY_GENERATOR' if _is(result, (gen.TopologyResult, gen.TopologyFailure)) else 'AXIOM_EVALUATOR'
            if value.producer != expected or type(value.source_binding) is not tuple or value.source_binding != (result.source_binding, result.request.origin_diagnosis.profile_binding, result.policy_binding) or value.operation_reference != result.request.request_reference or value.origin_diagnosis != result.request.origin_diagnosis:
                _fail('MODULE_CONTEXT_REJECTED')
        else:
            _fail('MODULE_RESULT_REJECTED')
        if type(value.dependency_results) is not tuple or len(value.dependency_results) > 6:
            _fail()
        for dependency in value.dependency_results:
            pure_record(dependency)
    elif kind is ModuleCaptureReceipt:
        _choice(value.status, ("CONFIRMED", "REJECTED", "NOT_CONFIRMED"))
        pure_record(value.result)
        from . import realm_transition_values as rt
        from . import generation_values as gen
        reference = value.result.operation_reference if _is(value.result, rt.RESULT_TYPES) else value.result.request.request_reference if _is(value.result, gen.PACKET_TYPES) else None
        if reference != value.operation_reference:
            _fail('MODULE_CONTEXT_REJECTED')
        if type(value.confirmed_records) is not tuple or len(value.confirmed_records) > 65:
            _fail()
        for reference in value.confirmed_records:
            _ref(reference)
        if value.attempted_record is not None:
            pure_record(value.attempted_record)
        if value.completion is not None:
            if type(value.completion) is not dv.DiagnosticsCompletionReceipt:
                _fail()
            dv.DiagnosticsCompletionReceipt.__post_init__(value.completion)
            if value.completion.operation_reference != value.operation_reference:
                _fail('MODULE_CONTEXT_REJECTED')
        if value.final_observation is not None:
            if type(value.final_observation) is not ModuleFinalObservationReceipt:
                _fail()
            _validate(value.final_observation)
            if value.final_observation.operation_reference != value.operation_reference:
                _fail('MODULE_CONTEXT_REJECTED')
    elif kind is ModuleFinalObservationReceipt:
        _choice(value.status, ("CONFIRMED", "REJECTED", "NOT_CONFIRMED"))
        _choice(value.coverage, COVERAGE)
        if value.supporting_reference is not None and (type(value.supporting_reference) is not str or re.fullmatch(r"ref:[0-9]{6}", value.supporting_reference) is None):
            _fail()
    elif kind is ModuleReturnAuditObservation:
        _choice(value.status, ("COMPLETE", "MISSING", "ALREADY_OBSERVED", "NOT_CONFIRMED"))
        _choice(value.missing_kind, ("NONE", "REQUIRED_SEMANTIC_RECORD", "REQUIRED_CAPTURE_STEP", "FIRST_COMPLETION"))
        _choice(value.coverage, COVERAGE)
        if value.meta_sequence is not None and (type(value.meta_sequence) is not int or not 0 <= value.meta_sequence < 1 << 64):
            _fail()


def revalidate_value(value):
    _validate(value)
    return value

SAFE_SCHEMAS = {'PRODUCER_CONTEXT': {'type': 'object',
                      'additionalProperties': False,
                      'required': ['operation_reference',
                                   'producer',
                                   'origin_assessment_reference',
                                   'origin_diagnostic_reference',
                                   'origin_completion_reference',
                                   'root_reference',
                                   'predecessor_reference',
                                   'source_reference',
                                   'profile_reference',
                                   'dependency_operation_references',
                                   'binding_status',
                                   'capture_assurance'],
                      'properties': {'operation_reference': {'type': 'string',
                                                             'pattern': '^ref:[0-9]{6}$',
                                                             'maxLength': 10},
                                     'producer': {'type': 'string',
                                                  'enum': ['REALM_ENCODER',
                                                           'TRANSITION_REGISTRY',
                                                           'TOPOLOGY_GENERATOR',
                                                           'AXIOM_EVALUATOR',
                                                           'GENERATION_PLANNER',
                                                           'ARTIFACT_EMITTER']},
                                     'origin_assessment_reference': {'type': 'string',
                                                                     'pattern': '^ref:[0-9]{6}$',
                                                                     'maxLength': 10},
                                     'origin_diagnostic_reference': {'type': 'string',
                                                                     'pattern': '^ref:[0-9]{6}$',
                                                                     'maxLength': 10},
                                     'origin_completion_reference': {'type': 'string',
                                                                     'pattern': '^ref:[0-9]{6}$',
                                                                     'maxLength': 10},
                                     'root_reference': {'type': 'string',
                                                        'pattern': '^ref:[0-9]{6}$',
                                                        'maxLength': 10},
                                     'predecessor_reference': {'type': 'string',
                                                               'pattern': '^ref:[0-9]{6}$',
                                                               'maxLength': 10},
                                     'source_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                     'profile_reference': {'type': 'string',
                                                           'pattern': '^ref:[0-9]{6}$',
                                                           'maxLength': 10},
                                     'dependency_operation_references': {'type': 'array',
                                                                         'items': {'type': 'string',
                                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                                   'maxLength': 10},
                                                                         'maxItems': 6},
                                     'binding_status': {'type': 'string',
                                                        'enum': ['FULL_CURRENT_BINDINGS_MATCH',
                                                                 'SUBMITTED_BINDINGS_REJECTED']},
                                     'capture_assurance': {'type': 'string',
                                                           'enum': ['ACTUAL_COMPLETED_ORIGIN',
                                                                    'UNAVAILABLE_OR_FOREIGN_ORIGIN']}}},
 'PRODUCER_SOURCE': {'type': 'object',
                     'additionalProperties': False,
                     'required': ['canonical_evidence_reference',
                                  'profile_evidence_reference',
                                  'contract_pins',
                                  'diagnostics_contract_sha256',
                                  'diagnostic_schema_sha256',
                                  'taxonomy_sha256',
                                  'source_baseline',
                                  'source_assurance',
                                  'module_policy_references'],
                     'properties': {'canonical_evidence_reference': {'type': 'string',
                                                                     'pattern': '^ref:[0-9]{6}$',
                                                                     'maxLength': 10},
                                    'profile_evidence_reference': {'type': 'string',
                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                   'maxLength': 10},
                                    'contract_pins': {'type': 'array',
                                                      'items': {'type': 'object',
                                                                'additionalProperties': False,
                                                                'required': ['path_reference', 'sha256'],
                                                                'properties': {'path_reference': {'type': 'string',
                                                                                                  'pattern': '^ref:[0-9]{6}$',
                                                                                                  'maxLength': 10},
                                                                               'sha256': {'type': 'string',
                                                                                          'pattern': '^[0-9a-f]{64}$',
                                                                                          'maxLength': 64}}},
                                                      'maxItems': 11},
                                    'diagnostics_contract_sha256': {'type': 'string',
                                                                    'pattern': '^[0-9a-f]{64}$',
                                                                    'maxLength': 64},
                                    'diagnostic_schema_sha256': {'type': 'string',
                                                                 'pattern': '^[0-9a-f]{64}$',
                                                                 'maxLength': 64},
                                    'taxonomy_sha256': {'type': 'string',
                                                        'pattern': '^[0-9a-f]{64}$',
                                                        'maxLength': 64},
                                    'source_baseline': {'type': 'string',
                                                        'enum': ['M3_MODULES'],
                                                        'const': 'M3_MODULES'},
                                    'source_assurance': {'type': 'string',
                                                         'enum': ['HOST_VERIFIED_COMPLETE_VECTOR',
                                                                  'RECOGNIZED_COMPLETE_VECTOR']},
                                    'module_policy_references': {'type': 'array',
                                                                 'items': {'type': 'string',
                                                                           'pattern': '^ref:[0-9]{6}$',
                                                                           'maxLength': 10},
                                                                 'maxItems': 4}}},
 'PRODUCER_OPERATION': {'type': 'object',
                        'additionalProperties': False,
                        'required': ['context_reference',
                                     'producer',
                                     'semantic_status',
                                     'constructed_record_references',
                                     'attempted_event_indices',
                                     'confirmed_event_indices',
                                     'pending_record_references',
                                     'output_references',
                                     'completion_observation_reference',
                                     'capture_status',
                                     'failure_code'],
                        'properties': {'context_reference': {'type': 'string',
                                                             'pattern': '^ref:[0-9]{6}$',
                                                             'maxLength': 10},
                                       'producer': {'type': 'string',
                                                    'enum': ['REALM_ENCODER',
                                                             'TRANSITION_REGISTRY',
                                                             'TOPOLOGY_GENERATOR',
                                                             'AXIOM_EVALUATOR',
                                                             'GENERATION_PLANNER',
                                                             'ARTIFACT_EMITTER']},
                                       'semantic_status': {'type': 'string',
                                                           'enum': ['COMPLETE_SEMANTICS',
                                                                    'REJECTED_INPUT',
                                                                    'CONSTRUCTED_PREFIX_ONLY']},
                                       'constructed_record_references': {'type': 'array',
                                                                         'items': {'type': 'string',
                                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                                   'maxLength': 10},
                                                                         'maxItems': 65},
                                       'attempted_event_indices': {'type': 'array',
                                                                   'items': {'type': 'integer',
                                                                             'minimum': 0,
                                                                             'maximum': 18446744073709551615},
                                                                   'maxItems': 65},
                                       'confirmed_event_indices': {'type': 'array',
                                                                   'items': {'type': 'integer',
                                                                             'minimum': 0,
                                                                             'maximum': 18446744073709551615},
                                                                   'maxItems': 65},
                                       'pending_record_references': {'type': 'array',
                                                                     'items': {'type': 'string',
                                                                               'pattern': '^ref:[0-9]{6}$',
                                                                               'maxLength': 10},
                                                                     'maxItems': 65},
                                       'output_references': {'type': 'array',
                                                             'items': {'type': 'string',
                                                                       'pattern': '^ref:[0-9]{6}$',
                                                                       'maxLength': 10},
                                                             'maxItems': 6},
                                       'completion_observation_reference': {'anyOf': [{'type': 'string',
                                                                                       'pattern': '^ref:[0-9]{6}$',
                                                                                       'maxLength': 10},
                                                                                      {'type': 'null'}]},
                                       'capture_status': {'type': 'string',
                                                          'enum': ['COMPLETE',
                                                                   'INCOMPLETE',
                                                                   'NOT_CONFIRMED']},
                                       'failure_code': {'anyOf': [{'type': 'string',
                                                                   'enum': ['MODULE_ORIGIN_UNAVAILABLE',
                                                                            'MODULE_REQUIRED_RECORD_MISSING',
                                                                            'MODULE_CAPTURE_UNCONFIRMED',
                                                                            'MODULE_RAW_PACKET_LIMIT',
                                                                            'MODULE_PLAN_POLICY_UNAVAILABLE']},
                                                                  {'type': 'null'}]}}},
 'PRODUCER_FINAL_OBSERVATION': {'type': 'object',
                                'additionalProperties': False,
                                'required': ['operation_reference',
                                             'tentative_operation_reference',
                                             'actual_result_reference',
                                             'completion_observation_reference',
                                             'first_finish_status',
                                             'semantic_status',
                                             'capture_status',
                                             'failure_code'],
                                'properties': {'operation_reference': {'type': 'string',
                                                                       'pattern': '^ref:[0-9]{6}$',
                                                                       'maxLength': 10},
                                               'tentative_operation_reference': {'type': 'string',
                                                                                 'pattern': '^ref:[0-9]{6}$',
                                                                                 'maxLength': 10},
                                               'actual_result_reference': {'type': 'string',
                                                                           'pattern': '^ref:[0-9]{6}$',
                                                                           'maxLength': 10},
                                               'completion_observation_reference': {'type': 'string',
                                                                                    'pattern': '^ref:[0-9]{6}$',
                                                                                    'maxLength': 10},
                                               'first_finish_status': {'type': 'string',
                                                                       'enum': ['COMPLETE',
                                                                                'INCOMPLETE',
                                                                                'NOT_CONFIRMED']},
                                               'semantic_status': {'type': 'string',
                                                                   'enum': ['COMPLETE_SEMANTICS',
                                                                            'REJECTED_INPUT',
                                                                            'CONSTRUCTED_PREFIX_ONLY']},
                                               'capture_status': {'type': 'string',
                                                                  'enum': ['COMPLETE',
                                                                           'INCOMPLETE',
                                                                           'NOT_CONFIRMED']},
                                               'failure_code': {'anyOf': [{'type': 'string',
                                                                           'enum': ['MODULE_ORIGIN_UNAVAILABLE',
                                                                                    'MODULE_REQUIRED_RECORD_MISSING',
                                                                                    'MODULE_CAPTURE_UNCONFIRMED',
                                                                                    'MODULE_RAW_PACKET_LIMIT',
                                                                                    'MODULE_PLAN_POLICY_UNAVAILABLE']},
                                                                          {'type': 'null'}]}}},
 'PRODUCER_RECORD': {'type': 'object',
                     'additionalProperties': False,
                     'required': ['context_reference',
                                  'diagnostic_reference',
                                  'payload_reference',
                                  'producer',
                                  'record_index',
                                  'current_impact',
                                  'phase',
                                  'result',
                                  'input_state',
                                  'output_state',
                                  'codeword',
                                  'is_applicable',
                                  'verification_status',
                                  'admissibility_status',
                                  'selection_kind',
                                  'selected_definition_reference',
                                  'value_reference',
                                  'actual_pure_target_diagnostic',
                                  'omitted_fields'],
                     'properties': {'context_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                    'diagnostic_reference': {'type': 'string',
                                                             'pattern': '^ref:[0-9]{6}$',
                                                             'maxLength': 10},
                                    'payload_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                    'producer': {'type': 'string',
                                                 'enum': ['REALM_ENCODER',
                                                          'TRANSITION_REGISTRY',
                                                          'TOPOLOGY_GENERATOR',
                                                          'AXIOM_EVALUATOR',
                                                          'GENERATION_PLANNER',
                                                          'ARTIFACT_EMITTER']},
                                    'record_index': {'type': 'integer', 'minimum': 0, 'maximum': 64},
                                    'current_impact': {'type': 'string',
                                                       'enum': ['INFO', 'WARNING', 'ERROR', 'CRITICAL']},
                                    'phase': {'type': 'string',
                                              'enum': ['INPUT_VALIDATION',
                                                       'IDENTITY_ENCODING',
                                                       'DEFINITION_APPLICABILITY',
                                                       'SELECTED_MEMBERSHIP',
                                                       'SELECTED_APPLICABILITY',
                                                       'FULL_VECTOR_TRANSFORMATION',
                                                       'TOPOLOGY_EXPANSION',
                                                       'AXIOM_CHECK',
                                                       'INPUT_REFUSAL',
                                                       'PLAN_BUILD',
                                                       'ARTIFACT_DISPATCH',
                                                       'ARTIFACT_RECEIPT',
                                                       'OPERATION_SUMMARY']},
                                    'result': {'type': 'string',
                                               'enum': ['SUCCEEDED',
                                                        'REFUSED',
                                                        'INAPPLICABLE',
                                                        'FAILED',
                                                        'UNCONFIRMED']},
                                    'input_state': {'anyOf': [{'type': 'string',
                                                               'pattern': '^[01]{9}$',
                                                               'maxLength': 9},
                                                              {'type': 'null'}]},
                                    'output_state': {'anyOf': [{'type': 'string',
                                                                'pattern': '^[01]{9}$',
                                                                'maxLength': 9},
                                                               {'type': 'null'}]},
                                    'codeword': {'anyOf': [{'type': 'string',
                                                            'pattern': '^[01]{9}$',
                                                            'maxLength': 9},
                                                           {'type': 'null'}]},
                                    'is_applicable': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
                                    'verification_status': {'anyOf': [{'type': 'string',
                                                                       'enum': ['VERIFIED', 'REJECTED']},
                                                                      {'type': 'null'}]},
                                    'admissibility_status': {'anyOf': [{'type': 'string',
                                                                        'enum': ['VALID',
                                                                                 'TRANSFORMATION_COMPATIBLE',
                                                                                 'TRANSFORMATION_INCOMPATIBLE',
                                                                                 'UNCLASSIFIED']},
                                                                       {'type': 'null'}]},
                                    'selection_kind': {'anyOf': [{'type': 'string',
                                                                  'enum': ['TRANSITION_ID', 'CODEWORD']},
                                                                 {'type': 'null'}]},
                                    'selected_definition_reference': {'anyOf': [{'type': 'string',
                                                                                 'pattern': '^ref:[0-9]{6}$',
                                                                                 'maxLength': 10},
                                                                                {'type': 'null'}]},
                                    'value_reference': {'anyOf': [{'type': 'string',
                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                   'maxLength': 10},
                                                                  {'type': 'null'}]},
                                    'actual_pure_target_diagnostic': {'anyOf': [{'type': 'object',
                                                                                 'additionalProperties': False,
                                                                                 'required': ['input_state',
                                                                                              'admissibility_status',
                                                                                              'transformation_compatibility',
                                                                                              'normalization_status',
                                                                                              'recoverability_relevance',
                                                                                              'is_valid',
                                                                                              'orbit_info',
                                                                                              'rule_ids',
                                                                                              'notes'],
                                                                                 'properties': {'input_state': {'type': 'object',
                                                                                                                'additionalProperties': False,
                                                                                                                'required': ['kind',
                                                                                                                             'state',
                                                                                                                             'input_reference',
                                                                                                                             'failure_code'],
                                                                                                                'properties': {'kind': {'type': 'string',
                                                                                                                                        'enum': ['ASH_STATE',
                                                                                                                                                 'REJECTED']},
                                                                                                                               'state': {'anyOf': [{'type': 'string',
                                                                                                                                                    'pattern': '^[01]{9}$',
                                                                                                                                                    'minLength': 9,
                                                                                                                                                    'maxLength': 9},
                                                                                                                                                   {'type': 'null'}]},
                                                                                                                               'input_reference': {'type': 'string',
                                                                                                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                                                                                                   'minLength': 10,
                                                                                                                                                   'maxLength': 10},
                                                                                                                               'failure_code': {'anyOf': [{'type': 'string',
                                                                                                                                                           'enum': ['INPUT_DEPTH_LIMIT',
                                                                                                                                                                    'INPUT_JSON_DUPLICATE_KEY',
                                                                                                                                                                    'INPUT_JSON_INVALID',
                                                                                                                                                                    'INPUT_JSON_NONFINITE',
                                                                                                                                                                    'INPUT_KIND_UNSUPPORTED',
                                                                                                                                                                    'INPUT_NUMERIC_TOKEN_INVALID',
                                                                                                                                                                    'INPUT_RECORD_INVALID',
                                                                                                                                                                    'INPUT_RECORD_KEY_INVALID',
                                                                                                                                                                    'INPUT_RECORD_SIZE_LIMIT',
                                                                                                                                                                    'INPUT_SIGNATURE_INVALID',
                                                                                                                                                                    'INPUT_SIZE_LIMIT',
                                                                                                                                                                    'INPUT_STATE_SPACE_INVALID',
                                                                                                                                                                    'INPUT_TOKEN_LIMIT',
                                                                                                                                                                    'INPUT_UTF8_INVALID',
                                                                                                                                                                    'STATE_COORDINATE_TYPE',
                                                                                                                                                                    'STATE_COORDINATE_VALUE',
                                                                                                                                                                    'STATE_WIDTH']},
                                                                                                                                                          {'type': 'null'}]}}},
                                                                                                'admissibility_status': {'type': 'string',
                                                                                                                         'enum': ['VALID',
                                                                                                                                  'TRANSFORMATION_COMPATIBLE',
                                                                                                                                  'TRANSFORMATION_INCOMPATIBLE',
                                                                                                                                  'UNCLASSIFIED']},
                                                                                                'transformation_compatibility': {'type': 'string',
                                                                                                                                 'enum': ['COMPATIBLE',
                                                                                                                                          'INCOMPATIBLE',
                                                                                                                                          'UNKNOWN']},
                                                                                                'normalization_status': {'type': 'string',
                                                                                                                         'enum': ['ALREADY_VALID',
                                                                                                                                  'NORMALIZABLE',
                                                                                                                                  'NOT_NORMALIZABLE',
                                                                                                                                  'BLOCKED']},
                                                                                                'recoverability_relevance': {'type': 'string',
                                                                                                                             'enum': ['NO_RECOVERY_NEEDED',
                                                                                                                                      'RECOVERY_APPLICABLE',
                                                                                                                                      'NOT_RECOVERABLE',
                                                                                                                                      'CONTAINMENT_NEEDED']},
                                                                                                'is_valid': {'type': 'boolean'},
                                                                                                'orbit_info': {'anyOf': [{'type': 'object',
                                                                                                                          'additionalProperties': False,
                                                                                                                          'required': ['orbit_id',
                                                                                                                                       'member_count',
                                                                                                                                       'contains_known_valid_state'],
                                                                                                                          'properties': {'orbit_id': {'type': 'string',
                                                                                                                                                      'pattern': '^[01]{9}$',
                                                                                                                                                      'minLength': 9,
                                                                                                                                                      'maxLength': 9},
                                                                                                                                         'member_count': {'const': 16},
                                                                                                                                         'contains_known_valid_state': {'type': 'boolean'}}},
                                                                                                                         {'type': 'null'}]},
                                                                                                'rule_ids': {'type': 'array',
                                                                                                             'items': {'type': 'string',
                                                                                                                       'enum': ['ASH-ADMISSIBILITY-CLASSIFICATION-001',
                                                                                                                                'ASH-CLASSIFICATION-MAPPING-001',
                                                                                                                                'ASH-RECOVERY-ACTION-001',
                                                                                                                                'ASH-STATE-GENERAL-001',
                                                                                                                                'ASH-STATE-STRUCTURE-001',
                                                                                                                                'ASH-STATE-VALIDITY-001']},
                                                                                                             'maxItems': 5},
                                                                                                'notes': {'type': 'array',
                                                                                                          'items': {'type': 'string',
                                                                                                                    'enum': ['Reference '
                                                                                                                             'diagnostic '
                                                                                                                             'session '
                                                                                                                             'opened; '
                                                                                                                             'capture '
                                                                                                                             'is '
                                                                                                                             'limited '
                                                                                                                             'to '
                                                                                                                             'the '
                                                                                                                             'declared '
                                                                                                                             'producers.',
                                                                                                                             'Reference '
                                                                                                                             'diagnostic '
                                                                                                                             'session '
                                                                                                                             'closed; '
                                                                                                                             'retained '
                                                                                                                             'evidence '
                                                                                                                             'and '
                                                                                                                             'coverage '
                                                                                                                             'limitations '
                                                                                                                             'remain '
                                                                                                                             'explicit.',
                                                                                                                             'The '
                                                                                                                             'exact '
                                                                                                                             'previously '
                                                                                                                             'confirmed '
                                                                                                                             'origin '
                                                                                                                             'was '
                                                                                                                             'attached '
                                                                                                                             'by '
                                                                                                                             'this '
                                                                                                                             'collector; '
                                                                                                                             'no '
                                                                                                                             'origin '
                                                                                                                             'record '
                                                                                                                             'was '
                                                                                                                             'emitted '
                                                                                                                             'again.',
                                                                                                                             'State '
                                                                                                                             'validity '
                                                                                                                             'was '
                                                                                                                             'diagnosed '
                                                                                                                             'under '
                                                                                                                             'the '
                                                                                                                             'explicit '
                                                                                                                             'complete '
                                                                                                                             'source '
                                                                                                                             'and '
                                                                                                                             'profile '
                                                                                                                             'bindings.',
                                                                                                                             'Contextual '
                                                                                                                             'classification '
                                                                                                                             'evaluated '
                                                                                                                             'only '
                                                                                                                             'the '
                                                                                                                             'recorded '
                                                                                                                             'context '
                                                                                                                             'and '
                                                                                                                             'consulted '
                                                                                                                             'predicates.',
                                                                                                                             'Actual '
                                                                                                                             'full-vector '
                                                                                                                             'normalization '
                                                                                                                             'completed; '
                                                                                                                             'post-validation '
                                                                                                                             'acknowledgment '
                                                                                                                             'is '
                                                                                                                             'pending.',
                                                                                                                             'Actual '
                                                                                                                             'post-operation '
                                                                                                                             'state '
                                                                                                                             'was '
                                                                                                                             'diagnosed '
                                                                                                                             'and '
                                                                                                                             'classified '
                                                                                                                             'in '
                                                                                                                             'its '
                                                                                                                             'separately '
                                                                                                                             'linked '
                                                                                                                             'assessment '
                                                                                                                             'chain.',
                                                                                                                             'The '
                                                                                                                             'consulted '
                                                                                                                             'predicate '
                                                                                                                             'or '
                                                                                                                             'value '
                                                                                                                             'step '
                                                                                                                             'completed '
                                                                                                                             'with '
                                                                                                                             'the '
                                                                                                                             'structured '
                                                                                                                             'outcome '
                                                                                                                             'shown '
                                                                                                                             'in '
                                                                                                                             'this '
                                                                                                                             'record.',
                                                                                                                             'Recovery '
                                                                                                                             'was '
                                                                                                                             'refused '
                                                                                                                             'before '
                                                                                                                             'unapproved '
                                                                                                                             'effects; '
                                                                                                                             'the '
                                                                                                                             'original '
                                                                                                                             'submitted '
                                                                                                                             'evidence '
                                                                                                                             'remains '
                                                                                                                             'retained.',
                                                                                                                             'Only '
                                                                                                                             'a '
                                                                                                                             'typed '
                                                                                                                             'containment '
                                                                                                                             'or '
                                                                                                                             'halt '
                                                                                                                             'request '
                                                                                                                             'was '
                                                                                                                             'produced; '
                                                                                                                             'no '
                                                                                                                             'runtime '
                                                                                                                             'mode '
                                                                                                                             'entry '
                                                                                                                             'is '
                                                                                                                             'claimed.',
                                                                                                                             'A '
                                                                                                                             'required '
                                                                                                                             'diagnostic '
                                                                                                                             'invariant '
                                                                                                                             'failed; '
                                                                                                                             'the '
                                                                                                                             'related '
                                                                                                                             'operation '
                                                                                                                             'or '
                                                                                                                             'record '
                                                                                                                             'was '
                                                                                                                             'not '
                                                                                                                             'silently '
                                                                                                                             'accepted.',
                                                                                                                             'Capture '
                                                                                                                             'did '
                                                                                                                             'not '
                                                                                                                             'acknowledge '
                                                                                                                             'this '
                                                                                                                             'attempted '
                                                                                                                             'record; '
                                                                                                                             'its '
                                                                                                                             'external '
                                                                                                                             'persistence '
                                                                                                                             'remains '
                                                                                                                             'unconfirmed.',
                                                                                                                             'A '
                                                                                                                             'whole '
                                                                                                                             'declared '
                                                                                                                             'retention '
                                                                                                                             'range '
                                                                                                                             'became '
                                                                                                                             'unavailable; '
                                                                                                                             'counts '
                                                                                                                             'and '
                                                                                                                             'boundary '
                                                                                                                             'evidence '
                                                                                                                             'are '
                                                                                                                             'retained.',
                                                                                                                             'The '
                                                                                                                             'JSON '
                                                                                                                             'and '
                                                                                                                             'Markdown '
                                                                                                                             'parts '
                                                                                                                             'and '
                                                                                                                             'manifest '
                                                                                                                             'completed '
                                                                                                                             'for '
                                                                                                                             'one '
                                                                                                                             'verified '
                                                                                                                             'sanitized '
                                                                                                                             'snapshot.',
                                                                                                                             'The '
                                                                                                                             'paired '
                                                                                                                             'diagnostic '
                                                                                                                             'export '
                                                                                                                             'did '
                                                                                                                             'not '
                                                                                                                             'complete; '
                                                                                                                             'retained '
                                                                                                                             'part '
                                                                                                                             'status '
                                                                                                                             'and '
                                                                                                                             'failure '
                                                                                                                             'evidence '
                                                                                                                             'are '
                                                                                                                             'explicit.',
                                                                                                                             'Untrusted '
                                                                                                                             'producer '
                                                                                                                             'prose, '
                                                                                                                             'previews, '
                                                                                                                             'paths '
                                                                                                                             'and '
                                                                                                                             'exception '
                                                                                                                             'material '
                                                                                                                             'were '
                                                                                                                             'omitted '
                                                                                                                             'before '
                                                                                                                             'persistence.']},
                                                                                                          'maxItems': 8}}},
                                                                                {'type': 'null'}]},
                                    'omitted_fields': {'type': 'string',
                                                       'enum': ['CALLER_EXPLANATION_AND_IDENTIFIERS'],
                                                       'const': 'CALLER_EXPLANATION_AND_IDENTIFIERS'}}},
 'REALM_IDENTITY': {'type': 'object',
                    'additionalProperties': False,
                    'required': ['state_signature', 'vertex_id', 'realm_id', 'orbit_id', 'identity_policy'],
                    'properties': {'state_signature': {'type': 'string',
                                                       'pattern': '^[01]{9}$',
                                                       'maxLength': 9},
                                   'vertex_id': {'type': 'string',
                                                 'pattern': '^ash_state_[01]{9}$',
                                                 'maxLength': 19},
                                   'realm_id': {'type': 'string',
                                                'pattern': '^ash_state_[01]{9}$',
                                                'maxLength': 19},
                                   'orbit_id': {'type': 'string', 'pattern': '^[01]{9}$', 'maxLength': 9},
                                   'identity_policy': {'type': 'string',
                                                       'enum': ['FULL_VECTOR_VERTEX_LOSSLESS_ALIAS'],
                                                       'const': 'FULL_VECTOR_VERTEX_LOSSLESS_ALIAS'}}},
 'TRANSITION_REGISTRY': {'type': 'object',
                         'additionalProperties': False,
                         'required': ['registry_reference',
                                      'source_reference',
                                      'policy_reference',
                                      'definitions',
                                      'policy_status',
                                      'ordering'],
                         'properties': {'registry_reference': {'type': 'string',
                                                               'pattern': '^ref:[0-9]{6}$',
                                                               'maxLength': 10},
                                        'source_reference': {'type': 'string',
                                                             'pattern': '^ref:[0-9]{6}$',
                                                             'maxLength': 10},
                                        'policy_reference': {'type': 'string',
                                                             'pattern': '^ref:[0-9]{6}$',
                                                             'maxLength': 10},
                                        'definitions': {'type': 'array',
                                                        'items': {'type': 'string',
                                                                  'pattern': '^ref:[0-9]{6}$',
                                                                  'maxLength': 10},
                                                        'maxItems': 16},
                                        'policy_status': {'type': 'string',
                                                          'enum': ['DECLARED_REFERENCE_POLICY',
                                                                   'REJECTED_FOREIGN_POLICY']},
                                        'ordering': {'type': 'string',
                                                     'enum': ['CANONICAL_C16_ORDER'],
                                                     'const': 'CANONICAL_C16_ORDER'}}},
 'TRANSITION_DEFINITION': {'type': 'object',
                           'additionalProperties': False,
                           'required': ['definition_reference',
                                        'registry_reference',
                                        'transition_reference',
                                        'codeword',
                                        'catalog_index',
                                        'applicability_mask',
                                        'policy_reference',
                                        'omitted_fields'],
                           'properties': {'definition_reference': {'type': 'string',
                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                   'maxLength': 10},
                                          'registry_reference': {'type': 'string',
                                                                 'pattern': '^ref:[0-9]{6}$',
                                                                 'maxLength': 10},
                                          'transition_reference': {'type': 'string',
                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                   'maxLength': 10},
                                          'codeword': {'type': 'string',
                                                       'pattern': '^[01]{9}$',
                                                       'maxLength': 9},
                                          'catalog_index': {'type': 'integer', 'minimum': 0, 'maximum': 15},
                                          'applicability_mask': {'type': 'string',
                                                                 'pattern': '^[01]{512}$',
                                                                 'minLength': 512,
                                                                 'maxLength': 512},
                                          'policy_reference': {'type': 'string',
                                                               'pattern': '^ref:[0-9]{6}$',
                                                               'maxLength': 10},
                                          'omitted_fields': {'type': 'string',
                                                             'enum': ['DECLARED_DEFINITION_LABELS'],
                                                             'const': 'DECLARED_DEFINITION_LABELS'}}},
 'TOPOLOGY': {'type': 'object',
              'additionalProperties': False,
              'required': ['topology_reference',
                           'context_reference',
                           'input_state',
                           'seed_reference',
                           'seed_policy',
                           'depth',
                           'leaf_count',
                           'visited_count',
                           'pages',
                           'node_id_policy',
                           'frontier_policy',
                           'rules'],
              'properties': {'topology_reference': {'type': 'string',
                                                    'pattern': '^ref:[0-9]{6}$',
                                                    'maxLength': 10},
                             'context_reference': {'type': 'string',
                                                   'pattern': '^ref:[0-9]{6}$',
                                                   'maxLength': 10},
                             'input_state': {'type': 'string', 'pattern': '^[01]{9}$', 'maxLength': 9},
                             'seed_reference': {'type': 'string',
                                                'pattern': '^ref:[0-9]{6}$',
                                                'maxLength': 10},
                             'seed_policy': {'type': 'string',
                                             'enum': ['ASCII_TOKEN_1_TO_32'],
                                             'const': 'ASCII_TOKEN_1_TO_32'},
                             'depth': {'type': 'integer', 'minimum': 0, 'maximum': 6},
                             'leaf_count': {'type': 'integer', 'minimum': 0, 'maximum': 729},
                             'visited_count': {'type': 'integer', 'minimum': 0, 'maximum': 1093},
                             'pages': {'type': 'array',
                                       'items': {'type': 'string',
                                                 'pattern': '^ref:[0-9]{6}$',
                                                 'maxLength': 10},
                                       'maxItems': 46},
                             'node_id_policy': {'type': 'string',
                                                'enum': ['TOPOLOGY_SEED_BASE3_PATH'],
                                                'const': 'TOPOLOGY_SEED_BASE3_PATH'},
                             'frontier_policy': {'type': 'string',
                                                 'enum': ['FINAL_FRONTIER_ONLY_BASE3_ORDER'],
                                                 'const': 'FINAL_FRONTIER_ONLY_BASE3_ORDER'},
                             'rules': {'type': 'array',
                                       'items': {'type': 'string',
                                                 'enum': ['ASH-TOPOLOGY-ADMISSION-001',
                                                          'ASH-TOPOLOGY-STRUCTURE-001',
                                                          'ASH-TOPOLOGY-EXPANSION-001',
                                                          'ASH-TOPOLOGY-ORDER-001',
                                                          'ASH-TOPOLOGY-LINEAGE-001']},
                                       'maxItems': 5}}},
 'TOPOLOGY_PAGE': {'type': 'object',
                   'additionalProperties': False,
                   'required': ['topology_reference', 'page_index', 'nodes'],
                   'properties': {'topology_reference': {'type': 'string',
                                                         'pattern': '^ref:[0-9]{6}$',
                                                         'maxLength': 10},
                                  'page_index': {'type': 'integer', 'minimum': 0, 'maximum': 45},
                                  'nodes': {'type': 'array',
                                            'items': {'type': 'object',
                                                      'additionalProperties': False,
                                                      'required': ['path',
                                                                   'parent_path',
                                                                   'kind',
                                                                   'depth',
                                                                   'frontier_ordinal'],
                                                      'properties': {'path': {'type': 'string',
                                                                              'pattern': '^r[012]{0,6}$',
                                                                              'maxLength': 7},
                                                                     'parent_path': {'anyOf': [{'type': 'string',
                                                                                                'pattern': '^r[012]{0,6}$',
                                                                                                'maxLength': 7},
                                                                                               {'type': 'null'}]},
                                                                     'kind': {'type': 'string',
                                                                              'enum': ['ROOT',
                                                                                       'CONTINUATION',
                                                                                       'POSITIVE',
                                                                                       'NEGATIVE']},
                                                                     'depth': {'type': 'integer',
                                                                               'minimum': 0,
                                                                               'maximum': 6},
                                                                     'frontier_ordinal': {'type': 'integer',
                                                                                          'minimum': 0,
                                                                                          'maximum': 728}}},
                                            'maxItems': 16}}},
 'AXIOM_SUBJECT': {'type': 'object',
                   'additionalProperties': False,
                   'required': ['subject_reference',
                                'state',
                                'relation_count',
                                'scale_count',
                                'raw_measure',
                                'compressed_measure',
                                'erasure_cost',
                                'self_reference_capable',
                                'self_model_available',
                                'source_kind',
                                'source_reference',
                                'method_id_reference',
                                'method_revision_reference',
                                'origin_diagnosis_reference'],
                   'properties': {'subject_reference': {'type': 'string',
                                                        'pattern': '^ref:[0-9]{6}$',
                                                        'maxLength': 10},
                                  'state': {'type': 'string', 'pattern': '^[01]{9}$', 'maxLength': 9},
                                  'relation_count': {'type': 'integer',
                                                     'minimum': 0,
                                                     'maximum': 9223372036854775807},
                                  'scale_count': {'type': 'integer',
                                                  'minimum': 0,
                                                  'maximum': 9223372036854775807},
                                  'raw_measure': {'type': 'object',
                                                  'additionalProperties': False,
                                                  'required': ['ticks', 'unit', 'ticks_per_unit'],
                                                  'properties': {'ticks': {'type': 'integer',
                                                                           'minimum': 0,
                                                                           'maximum': 9223372036854775807},
                                                                 'unit': {'type': 'string',
                                                                          'enum': ['STRUCTURE_TICK',
                                                                                   'ERASURE_TICK']},
                                                                 'ticks_per_unit': {'type': 'integer',
                                                                                    'minimum': 1,
                                                                                    'maximum': 1000000000}}},
                                  'compressed_measure': {'type': 'object',
                                                         'additionalProperties': False,
                                                         'required': ['ticks', 'unit', 'ticks_per_unit'],
                                                         'properties': {'ticks': {'type': 'integer',
                                                                                  'minimum': 0,
                                                                                  'maximum': 9223372036854775807},
                                                                        'unit': {'type': 'string',
                                                                                 'enum': ['STRUCTURE_TICK',
                                                                                          'ERASURE_TICK']},
                                                                        'ticks_per_unit': {'type': 'integer',
                                                                                           'minimum': 1,
                                                                                           'maximum': 1000000000}}},
                                  'erasure_cost': {'type': 'object',
                                                   'additionalProperties': False,
                                                   'required': ['ticks', 'unit', 'ticks_per_unit'],
                                                   'properties': {'ticks': {'type': 'integer',
                                                                            'minimum': 0,
                                                                            'maximum': 9223372036854775807},
                                                                  'unit': {'type': 'string',
                                                                           'enum': ['STRUCTURE_TICK',
                                                                                    'ERASURE_TICK']},
                                                                  'ticks_per_unit': {'type': 'integer',
                                                                                     'minimum': 1,
                                                                                     'maximum': 1000000000}}},
                                  'self_reference_capable': {'type': 'boolean'},
                                  'self_model_available': {'type': 'boolean'},
                                  'source_kind': {'type': 'string',
                                                  'enum': ['DECLARED_REFERENCE_INPUT'],
                                                  'const': 'DECLARED_REFERENCE_INPUT'},
                                  'source_reference': {'type': 'string',
                                                       'pattern': '^ref:[0-9]{6}$',
                                                       'maxLength': 10},
                                  'method_id_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                  'method_revision_reference': {'type': 'string',
                                                                'pattern': '^ref:[0-9]{6}$',
                                                                'maxLength': 10},
                                  'origin_diagnosis_reference': {'type': 'string',
                                                                 'pattern': '^ref:[0-9]{6}$',
                                                                 'maxLength': 10}}},
 'AXIOM_CHECK': {'type': 'object',
                 'additionalProperties': False,
                 'required': ['subject_reference',
                              'axiom_id',
                              'passed',
                              'current_impact',
                              'operator',
                              'operand_names',
                              'overall_pass',
                              'explanation_code'],
                 'properties': {'subject_reference': {'type': 'string',
                                                      'pattern': '^ref:[0-9]{6}$',
                                                      'maxLength': 10},
                                'axiom_id': {'type': 'string',
                                             'enum': ['A1_RELATIONAL_EXISTENCE',
                                                      'A2_STRUCTURAL_COMPRESSIBILITY',
                                                      'A3_MULTI_SCALE_PERSISTENCE',
                                                      'A4_ENERGETIC_COST_OF_ERASURE',
                                                      'A5_SELF_REFERENCE_FOR_CONSCIOUSNESS']},
                                'passed': {'type': 'boolean'},
                                'current_impact': {'type': 'string', 'enum': ['INFO', 'WARNING']},
                                'operator': {'type': 'string',
                                             'enum': ['GREATER_THAN_ZERO',
                                                      'LESS_THAN_SAME_QUANTUM',
                                                      'GREATER_THAN_ONE',
                                                      'BOOLEAN_CONJUNCTION']},
                                'operand_names': {'type': 'array',
                                                  'items': {'type': 'string',
                                                            'enum': ['RELATION_COUNT',
                                                                     'COMPRESSED_MEASURE',
                                                                     'RAW_MEASURE',
                                                                     'SCALE_COUNT',
                                                                     'ERASURE_COST',
                                                                     'SELF_REFERENCE_CAPABLE',
                                                                     'SELF_MODEL_AVAILABLE']},
                                                  'maxItems': 2},
                                'overall_pass': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
                                'explanation_code': {'type': 'string',
                                                     'enum': ['CHECK_PASSED',
                                                              'CHECK_FAILED',
                                                              'SUBJECT_UNITS_REJECTED',
                                                              'SUBJECT_STATE_REJECTED']}}},
 'GENERATION_PLAN': {'type': 'object',
                     'additionalProperties': False,
                     'required': ['plan_reference',
                                  'context_reference',
                                  'normalized_state',
                                  'source_identity_state',
                                  'destination_identity_state',
                                  'topology_reference',
                                  'axiom_operation_reference',
                                  'role_pages',
                                  'artifact_pages',
                                  'target_constraints_reference',
                                  'profile_reference',
                                  'naming_policy_reference',
                                  'role_policy_reference',
                                  'subject_policy_reference',
                                  'artifact_policy_reference',
                                  'warnings',
                                  'metadata_references',
                                  'boundary'],
                     'properties': {'plan_reference': {'type': 'string',
                                                       'pattern': '^ref:[0-9]{6}$',
                                                       'maxLength': 10},
                                    'context_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                    'normalized_state': {'type': 'string',
                                                         'pattern': '^[01]{9}$',
                                                         'maxLength': 9},
                                    'source_identity_state': {'type': 'string',
                                                              'pattern': '^[01]{9}$',
                                                              'maxLength': 9},
                                    'destination_identity_state': {'type': 'string',
                                                                   'pattern': '^[01]{9}$',
                                                                   'maxLength': 9},
                                    'topology_reference': {'type': 'string',
                                                           'pattern': '^ref:[0-9]{6}$',
                                                           'maxLength': 10},
                                    'axiom_operation_reference': {'type': 'string',
                                                                  'pattern': '^ref:[0-9]{6}$',
                                                                  'maxLength': 10},
                                    'role_pages': {'type': 'array',
                                                   'items': {'type': 'string',
                                                             'pattern': '^ref:[0-9]{6}$',
                                                             'maxLength': 10},
                                                   'maxItems': 46},
                                    'artifact_pages': {'type': 'array',
                                                       'items': {'type': 'string',
                                                                 'pattern': '^ref:[0-9]{6}$',
                                                                 'maxLength': 10},
                                                       'maxItems': 2},
                                    'target_constraints_reference': {'type': 'string',
                                                                     'pattern': '^ref:[0-9]{6}$',
                                                                     'maxLength': 10},
                                    'profile_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                    'naming_policy_reference': {'type': 'string',
                                                                'pattern': '^ref:[0-9]{6}$',
                                                                'maxLength': 10},
                                    'role_policy_reference': {'type': 'string',
                                                              'pattern': '^ref:[0-9]{6}$',
                                                              'maxLength': 10},
                                    'subject_policy_reference': {'type': 'string',
                                                                 'pattern': '^ref:[0-9]{6}$',
                                                                 'maxLength': 10},
                                    'artifact_policy_reference': {'type': 'string',
                                                                  'pattern': '^ref:[0-9]{6}$',
                                                                  'maxLength': 10},
                                    'warnings': {'type': 'array',
                                                 'items': {'type': 'string',
                                                           'enum': ['AXIOM_CHECK_FAILED',
                                                                    'TARGET_CONSTRAINT_UNSATISFIED',
                                                                    'DECLARED_POLICY_LIMIT']},
                                                 'maxItems': 5},
                                    'metadata_references': {'type': 'array',
                                                            'items': {'type': 'string',
                                                                      'pattern': '^ref:[0-9]{6}$',
                                                                      'maxLength': 10},
                                                            'maxItems': 16},
                                    'boundary': {'type': 'string',
                                                 'enum': ['ABSTRACT_NO_EXTERNAL_EFFECTS'],
                                                 'const': 'ABSTRACT_NO_EXTERNAL_EFFECTS'}}},
 'ROLE_PAGE': {'type': 'object',
               'additionalProperties': False,
               'required': ['plan_reference', 'page_index', 'assignments'],
               'properties': {'plan_reference': {'type': 'string',
                                                 'pattern': '^ref:[0-9]{6}$',
                                                 'maxLength': 10},
                              'page_index': {'type': 'integer', 'minimum': 0, 'maximum': 45},
                              'assignments': {'type': 'array',
                                              'items': {'type': 'object',
                                                        'additionalProperties': False,
                                                        'required': ['node_path',
                                                                     'role_reference',
                                                                     'assignment_reference',
                                                                     'policy_reference'],
                                                        'properties': {'node_path': {'type': 'string',
                                                                                     'pattern': '^r[012]{0,6}$',
                                                                                     'maxLength': 7},
                                                                       'role_reference': {'type': 'string',
                                                                                          'pattern': '^ref:[0-9]{6}$',
                                                                                          'maxLength': 10},
                                                                       'assignment_reference': {'type': 'string',
                                                                                                'pattern': '^ref:[0-9]{6}$',
                                                                                                'maxLength': 10},
                                                                       'policy_reference': {'type': 'string',
                                                                                            'pattern': '^ref:[0-9]{6}$',
                                                                                            'maxLength': 10}}},
                                              'maxItems': 16}}},
 'ARTIFACT_PAGE': {'type': 'object',
                   'additionalProperties': False,
                   'required': ['plan_reference', 'page_index', 'artifacts'],
                   'properties': {'plan_reference': {'type': 'string',
                                                     'pattern': '^ref:[0-9]{6}$',
                                                     'maxLength': 10},
                                  'page_index': {'type': 'integer', 'minimum': 0, 'maximum': 1},
                                  'artifacts': {'type': 'array',
                                                'items': {'type': 'object',
                                                          'additionalProperties': False,
                                                          'required': ['artifact_reference',
                                                                       'plan_element_reference',
                                                                       'kind',
                                                                       'name_reference',
                                                                       'role_references',
                                                                       'content_reference',
                                                                       'content_sha256',
                                                                       'content_byte_count',
                                                                       'semantic_policy_reference'],
                                                          'properties': {'artifact_reference': {'type': 'string',
                                                                                                'pattern': '^ref:[0-9]{6}$',
                                                                                                'maxLength': 10},
                                                                         'plan_element_reference': {'type': 'string',
                                                                                                    'pattern': '^ref:[0-9]{6}$',
                                                                                                    'maxLength': 10},
                                                                         'kind': {'type': 'string',
                                                                                  'enum': ['REFERENCE_DOCUMENT',
                                                                                           'REFERENCE_MANIFEST']},
                                                                         'name_reference': {'type': 'string',
                                                                                            'pattern': '^ref:[0-9]{6}$',
                                                                                            'maxLength': 10},
                                                                         'role_references': {'type': 'array',
                                                                                             'items': {'type': 'string',
                                                                                                       'pattern': '^ref:[0-9]{6}$',
                                                                                                       'maxLength': 10},
                                                                                             'maxItems': 16},
                                                                         'content_reference': {'type': 'string',
                                                                                               'pattern': '^ref:[0-9]{6}$',
                                                                                               'maxLength': 10},
                                                                         'content_sha256': {'type': 'string',
                                                                                            'pattern': '^[0-9a-f]{64}$',
                                                                                            'maxLength': 64},
                                                                         'content_byte_count': {'type': 'integer',
                                                                                                'minimum': 0,
                                                                                                'maximum': 32768},
                                                                         'semantic_policy_reference': {'type': 'string',
                                                                                                       'pattern': '^ref:[0-9]{6}$',
                                                                                                       'maxLength': 10}}},
                                                'maxItems': 16}}},
 'TARGET_CONSTRAINTS': {'type': 'object',
                        'additionalProperties': False,
                        'required': ['target_reference',
                                     'configuration_reference',
                                     'constraints',
                                     'target_kind',
                                     'policy_reference'],
                        'properties': {'target_reference': {'type': 'string',
                                                            'pattern': '^ref:[0-9]{6}$',
                                                            'maxLength': 10},
                                       'configuration_reference': {'type': 'string',
                                                                   'pattern': '^ref:[0-9]{6}$',
                                                                   'maxLength': 10},
                                       'constraints': {'type': 'array',
                                                       'items': {'type': 'object',
                                                                 'additionalProperties': False,
                                                                 'required': ['constraint_reference',
                                                                              'constraint_kind',
                                                                              'status',
                                                                              'value_reference',
                                                                              'limit_value',
                                                                              'unit'],
                                                                 'properties': {'constraint_reference': {'type': 'string',
                                                                                                         'pattern': '^ref:[0-9]{6}$',
                                                                                                         'maxLength': 10},
                                                                                'constraint_kind': {'type': 'string',
                                                                                                    'enum': ['DECLARED_PLATFORM',
                                                                                                             'DECLARED_RUNTIME',
                                                                                                             'DECLARED_CAPABILITY',
                                                                                                             'DECLARED_LIMIT']},
                                                                                'status': {'type': 'string',
                                                                                           'enum': ['SATISFIED',
                                                                                                    'UNSATISFIED',
                                                                                                    'UNAVAILABLE']},
                                                                                'value_reference': {'anyOf': [{'type': 'string',
                                                                                                               'pattern': '^ref:[0-9]{6}$',
                                                                                                               'maxLength': 10},
                                                                                                              {'type': 'null'}]},
                                                                                'limit_value': {'anyOf': [{'type': 'integer',
                                                                                                           'minimum': 0,
                                                                                                           'maximum': 18446744073709551615},
                                                                                                          {'type': 'null'}]},
                                                                                'unit': {'type': 'string',
                                                                                         'enum': ['NOT_APPLICABLE',
                                                                                                  'COUNT',
                                                                                                  'BYTES']}}},
                                                       'maxItems': 16},
                                       'target_kind': {'type': 'string',
                                                       'enum': ['REFERENCE_DOCUMENT_TARGET',
                                                                'REFERENCE_MANIFEST_TARGET']},
                                       'policy_reference': {'type': 'string',
                                                            'pattern': '^ref:[0-9]{6}$',
                                                            'maxLength': 10}}},
 'EMISSION_OUTPUT': {'type': 'object',
                     'additionalProperties': False,
                     'required': ['plan_reference',
                                  'artifact_reference',
                                  'dispatch_reference',
                                  'receipt_reference',
                                  'target_reference',
                                  'actual_status',
                                  'actual_effects',
                                  'expected_sha256',
                                  'observed_sha256',
                                  'expected_byte_count',
                                  'observed_byte_count',
                                  'materialization_policy_reference',
                                  'failure_code'],
                     'properties': {'plan_reference': {'type': 'string',
                                                       'pattern': '^ref:[0-9]{6}$',
                                                       'maxLength': 10},
                                    'artifact_reference': {'type': 'string',
                                                           'pattern': '^ref:[0-9]{6}$',
                                                           'maxLength': 10},
                                    'dispatch_reference': {'type': 'string',
                                                           'pattern': '^ref:[0-9]{6}$',
                                                           'maxLength': 10},
                                    'receipt_reference': {'type': 'string',
                                                          'pattern': '^ref:[0-9]{6}$',
                                                          'maxLength': 10},
                                    'target_reference': {'type': 'string',
                                                         'pattern': '^ref:[0-9]{6}$',
                                                         'maxLength': 10},
                                    'actual_status': {'type': 'string',
                                                      'enum': ['SUCCEEDED',
                                                               'FAILED',
                                                               'UNKNOWN',
                                                               'NO_EFFECT']},
                                    'actual_effects': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
                                    'expected_sha256': {'type': 'string',
                                                        'pattern': '^[0-9a-f]{64}$',
                                                        'maxLength': 64},
                                    'observed_sha256': {'anyOf': [{'type': 'string',
                                                                   'pattern': '^[0-9a-f]{64}$',
                                                                   'maxLength': 64},
                                                                  {'type': 'null'}]},
                                    'expected_byte_count': {'type': 'integer',
                                                            'minimum': 0,
                                                            'maximum': 32768},
                                    'observed_byte_count': {'anyOf': [{'type': 'integer',
                                                                       'minimum': 0,
                                                                       'maximum': 32768},
                                                                      {'type': 'null'}]},
                                    'materialization_policy_reference': {'type': 'string',
                                                                         'pattern': '^ref:[0-9]{6}$',
                                                                         'maxLength': 10},
                                    'failure_code': {'anyOf': [{'type': 'string',
                                                                'enum': ['EMITTER_EFFECT_UNCONFIRMED',
                                                                         'EMITTER_TARGET_UNAVAILABLE',
                                                                         'EMITTER_PLAN_INCOMPLETE',
                                                                         'EMITTER_FIDELITY_FAILED']},
                                                               {'type': 'null'}]}}}}

KIND_QUOTAS = {'PRODUCER_CONTEXT': 64,
 'PRODUCER_SOURCE': 16,
 'PRODUCER_OPERATION': 64,
 'PRODUCER_FINAL_OBSERVATION': 64,
 'PRODUCER_RECORD': 256,
 'REALM_IDENTITY': 64,
 'TRANSITION_REGISTRY': 16,
 'TRANSITION_DEFINITION': 256,
 'TOPOLOGY': 64,
 'TOPOLOGY_PAGE': 512,
 'AXIOM_SUBJECT': 64,
 'AXIOM_CHECK': 320,
 'GENERATION_PLAN': 64,
 'ROLE_PAGE': 512,
 'ARTIFACT_PAGE': 128,
 'TARGET_CONSTRAINTS': 64,
 'EMISSION_OUTPUT': 256}

PRODUCER_MAPPING = {'REALM_ENCODER': {'kind': 'REALM_ENCODING',
                   'max_records': 2,
                   'rules': ['ASH-STATE-VALIDITY-001', 'ASH-STATE-IDENTITY-001'],
                   'raw_cap': 1048576},
 'TRANSITION_REGISTRY': {'kind': 'TRANSITION',
                         'max_records': 17,
                         'apply_max_records': 4,
                         'rules': ['ASH-STATE-VALIDITY-001',
                                   'ASH-CODEWORD-STRUCTURE-001',
                                   'ASH-CODEWORD-REGISTRY-001',
                                   'ASH-CODEWORD-SELECTION-001',
                                   'ASH-CODEWORD-APPLICABILITY-001',
                                   'ASH-CODEWORD-TRANSFORMATION-001'],
                         'raw_cap': 1048576},
 'TOPOLOGY_GENERATOR': {'kind': 'TOPOLOGY',
                        'max_records': 1,
                        'rules': ['ASH-TOPOLOGY-ADMISSION-001',
                                  'ASH-TOPOLOGY-STRUCTURE-001',
                                  'ASH-TOPOLOGY-EXPANSION-001',
                                  'ASH-TOPOLOGY-ORDER-001',
                                  'ASH-TOPOLOGY-LINEAGE-001'],
                        'raw_cap': 1048576},
 'AXIOM_EVALUATOR': {'kind': 'AXIOM',
                     'max_records': 5,
                     'input_refusal_max_records': 1,
                     'rules': ['ASH-AXIOM-SUBJECT-001',
                               'ASH-AXIOM-RELATION-001',
                               'ASH-AXIOM-COMPRESSION-001',
                               'ASH-AXIOM-SCALE-001',
                               'ASH-AXIOM-ERASURE-001',
                               'ASH-AXIOM-SELFREFERENCE-001',
                               'ASH-AXIOM-CONJUNCTION-001'],
                     'raw_cap': 1048576},
 'GENERATION_PLANNER': {'kind': 'GENERATION_PLAN',
                        'max_records': 1,
                        'rules': ['ASH-GENERATION-PLAN-001', 'ASH-GENERATION-BOUNDARY-001'],
                        'raw_cap': 2097152},
 'ARTIFACT_EMITTER': {'kind': 'ARTIFACT_EMISSION',
                      'max_records': 65,
                      'rules': ['ASH-GENERATION-TRACEABILITY-001',
                                'ASH-GENERATION-EMISSION-001',
                                'ASH-GENERATION-PLANFIDELITY-001'],
                      'raw_cap': 2097152}}

WHOLE_RESERVATIONS = {'REALM_ENCODER': {'bytes': 524288, 'supporting_bytes': 131072, 'aliases': 320},
 'TRANSITION_REGISTRY': {'bytes': 2097152, 'supporting_bytes': 262144, 'aliases': 1024},
 'TOPOLOGY_GENERATOR': {'bytes': 2097152, 'supporting_bytes': 524288, 'aliases': 512},
 'AXIOM_EVALUATOR': {'bytes': 1048576, 'supporting_bytes': 262144, 'aliases': 512},
 'GENERATION_PLANNER': {'bytes': 4194304, 'supporting_bytes': 1048576, 'aliases': 4096},
 'ARTIFACT_EMITTER': {'bytes': 8388608, 'supporting_bytes': 1048576, 'aliases': 5120}}

OPERATION_KIND_COUNTS = {'REALM_ENCODER': {'PRODUCER_CONTEXT': 1,
                   'PRODUCER_SOURCE': 1,
                   'PRODUCER_OPERATION': 1,
                   'PRODUCER_FINAL_OBSERVATION': 1,
                   'PRODUCER_RECORD': 2,
                   'REALM_IDENTITY': 1},
 'TRANSITION_REGISTRY': {'PRODUCER_CONTEXT': 1,
                         'PRODUCER_SOURCE': 1,
                         'PRODUCER_OPERATION': 1,
                         'PRODUCER_FINAL_OBSERVATION': 1,
                         'PRODUCER_RECORD': 17,
                         'TRANSITION_REGISTRY': 1,
                         'TRANSITION_DEFINITION': 16},
 'TOPOLOGY_GENERATOR': {'PRODUCER_CONTEXT': 1,
                        'PRODUCER_SOURCE': 1,
                        'PRODUCER_OPERATION': 1,
                        'PRODUCER_FINAL_OBSERVATION': 1,
                        'PRODUCER_RECORD': 1,
                        'TOPOLOGY': 1,
                        'TOPOLOGY_PAGE': 46},
 'AXIOM_EVALUATOR': {'PRODUCER_CONTEXT': 1,
                     'PRODUCER_SOURCE': 1,
                     'PRODUCER_OPERATION': 1,
                     'PRODUCER_FINAL_OBSERVATION': 1,
                     'PRODUCER_RECORD': 5,
                     'AXIOM_SUBJECT': 1,
                     'AXIOM_CHECK': 5},
 'GENERATION_PLANNER': {'PRODUCER_CONTEXT': 1,
                        'PRODUCER_SOURCE': 1,
                        'PRODUCER_OPERATION': 1,
                        'PRODUCER_FINAL_OBSERVATION': 1,
                        'PRODUCER_RECORD': 1,
                        'REALM_IDENTITY': 2,
                        'TOPOLOGY': 1,
                        'TOPOLOGY_PAGE': 46,
                        'AXIOM_SUBJECT': 1,
                        'AXIOM_CHECK': 5,
                        'GENERATION_PLAN': 1,
                        'ROLE_PAGE': 46,
                        'ARTIFACT_PAGE': 2,
                        'TARGET_CONSTRAINTS': 1},
 'ARTIFACT_EMITTER': {'PRODUCER_CONTEXT': 1,
                      'PRODUCER_SOURCE': 1,
                      'PRODUCER_OPERATION': 1,
                      'PRODUCER_FINAL_OBSERVATION': 1,
                      'PRODUCER_RECORD': 65,
                      'REALM_IDENTITY': 2,
                      'TOPOLOGY': 1,
                      'TOPOLOGY_PAGE': 46,
                      'AXIOM_SUBJECT': 1,
                      'AXIOM_CHECK': 5,
                      'GENERATION_PLAN': 1,
                      'ROLE_PAGE': 46,
                      'ARTIFACT_PAGE': 2,
                      'TARGET_CONSTRAINTS': 1,
                      'EMISSION_OUTPUT': 32}}


@dataclass(frozen=True, slots=True)
class _SafeObject:
    members: tuple


def _safe_validate(value, schema, *, normalize=False):
    from . import diagnostics_values as dv
    if 'anyOf' in schema:
        for branch in schema['anyOf']:
            try:
                return _safe_validate(value, branch, normalize=normalize)
            except ModuleContractError:
                pass
        _fail('MODULE_CAPTURE_REJECTED')
    kind = schema.get('type')
    if kind == 'null':
        if value is not None:
            _fail('MODULE_CAPTURE_REJECTED')
    elif kind == 'string':
        if type(value) is not str or not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 512):
            _fail('MODULE_CAPTURE_REJECTED')
        if 'pattern' in schema and re.fullmatch(schema['pattern'], value, re.ASCII) is None:
            _fail('MODULE_CAPTURE_REJECTED')
    elif kind == 'integer':
        if type(value) is not int or not schema.get('minimum', 0) <= value <= schema.get('maximum', (1 << 64)-1):
            _fail('MODULE_CAPTURE_REJECTED')
    elif kind == 'boolean':
        if type(value) is not bool:
            _fail('MODULE_CAPTURE_REJECTED')
    elif kind == 'array':
        if type(value) is not tuple or not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', 1024):
            _fail('MODULE_CAPTURE_REJECTED')
        value = tuple(_safe_validate(child, schema['items'], normalize=normalize) for child in value)
    elif kind == 'object':
        target_validity = tuple(schema['properties']) == tuple(field.name for field in fields(dv.SafeStateValidity))
        if target_validity:
            if type(value) is not dv.SafeStateValidity:
                _fail('MODULE_CAPTURE_REJECTED')
            dv.SafeStateValidity.__post_init__(value)
            return value
        if type(value) is _SafeObject:
            members = value.members
            if type(members) is not tuple or any(type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str for pair in members):
                _fail('MODULE_CAPTURE_REJECTED')
            values = dict(members)
            if len(values) != len(members):
                _fail('MODULE_CAPTURE_REJECTED')
        elif normalize and type(value) is dict and all(type(key) is str for key in value):
            values = value
        else:
            _fail('MODULE_CAPTURE_REJECTED')
        if set(values) != set(schema['properties']):
            _fail('MODULE_CAPTURE_REJECTED')
        value = _SafeObject(tuple((name, _safe_validate(values[name], child, normalize=normalize)) for name, child in schema['properties'].items()))
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        _fail('MODULE_CAPTURE_REJECTED')
    if 'enum' in schema and (type(value) is not str or value not in schema['enum']):
        _fail('MODULE_CAPTURE_REJECTED')
    return value


def _safe_record(value):
    from . import diagnostics_values as dv
    if value is None or _is(value, (str, int, bool)):
        return value
    if type(value) is tuple:
        return [_safe_record(child) for child in value]
    if type(value) is _SafeObject:
        return {name: _safe_record(child) for name, child in value.members}
    if type(value) is dv.SafeStateValidity:
        dv.SafeStateValidity.__post_init__(value)
        return dv.SafeStateValidity.to_record(value)
    if _is(value, SAFE_TYPES):
        value.__class__.__post_init__(value)
        return {f.name: _safe_record(object.__getattribute__(value, f.name)) for f in fields(type(value))}
    _fail('MODULE_CAPTURE_REJECTED')


class _SafeValue:
    __slots__ = ()

    def __post_init__(self):
        if not _is(self, SAFE_TYPES):
            _fail('MODULE_CAPTURE_REJECTED')
        schema = SAFE_SCHEMAS[TYPE_KINDS[type(self)]]
        for field in fields(type(self)):
            value = object.__getattribute__(self, field.name)
            object.__setattr__(self, field.name, _safe_validate(value, schema['properties'][field.name], normalize=True))

    def to_record(self):
        return _safe_record(self)


SAFE_CLASSES = {}
for _kind, _schema in SAFE_SCHEMAS.items():
    _name = 'Safe' + ''.join(part.title() for part in _kind.split('_'))
    _cls = make_dataclass(_name, [(name, object) for name in _schema['properties']],
        bases=(_SafeValue,), frozen=True, slots=True, namespace={'__module__': __name__})
    SAFE_CLASSES[_kind] = _cls
    globals()[_name] = _cls
TYPE_KINDS = {cls: kind for kind, cls in SAFE_CLASSES.items()}
SAFE_TYPES = tuple(SAFE_CLASSES.values())


@dataclass(frozen=True, slots=True)
class SafeModuleEvidence:
    kind: str
    evidence_reference: str
    payload: object

    def __post_init__(self):
        _choice(self.kind, tuple(SAFE_CLASSES))
        if type(self.evidence_reference) is not str or re.fullmatch(r'ref:[0-9]{6}', self.evidence_reference, re.ASCII) is None:
            _fail('MODULE_CAPTURE_REJECTED')
        if type(self.payload) is not SAFE_CLASSES[self.kind]:
            _fail('MODULE_CAPTURE_REJECTED')
        SAFE_CLASSES[self.kind].__post_init__(self.payload)

    def to_record(self):
        SafeModuleEvidence.__post_init__(self)
        return {'kind': self.kind, 'evidence_reference': self.evidence_reference, 'payload': _safe_record(self.payload)}
