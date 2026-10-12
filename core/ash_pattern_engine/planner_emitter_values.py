"""Closed immutable generation and memory-emission values [YWE-REQ-0049]."""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import math
import re
from threading import Lock

from . import state_values as state
from . import realm_transition_values as rt
from . import generation_values as gen

RAW_BUSINESS_LIMIT = 2_097_152
TEN_BYTE_LIMIT = 8192
SCHEMA_ID = "https://ywe.local/schemas/m3_planner_emitter_schema.json"
GENERATION_AGGREGATE = "2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8"
POLICY_FIELDS = ("YWE-M3-PLANNER-EMITTER-REFERENCE-001", "1.0.0",
                 "3b4666031a79fec97ed98653bf556ed2d6d8ad538639475813dbd3273b6670b6")
SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")


class PlannerEmitterContractError(ValueError):
    def __init__(self, code, field_name):
        if type(code) is not str or code not in ("INPUT_INVALID", "VALUE_CORRUPT", "SOURCE_UNRECOGNIZED", "RAW_BUSINESS_LIMIT"):
            raise ValueError("invalid planner/emitter error code")
        if type(field_name) is not str or re.fullmatch(r"[A-Za-z0-9_.\[\]]{1,160}", field_name, re.ASCII) is None:
            raise ValueError("invalid planner/emitter error field")
        self.code, self.field_name = code, field_name
        super().__init__(f"{code}: {field_name}")


def _fail(field="value", code="INPUT_INVALID"):
    raise PlannerEmitterContractError(code, field)


def _is(value, classes):
    return any(type(value) is cls for cls in classes)


def _exact(value, classes, field="value"):
    if not _is(value, classes if type(classes) is tuple else (classes,)):
        _fail(field)


def _ref(value, field="operation_reference", maximum=256):
    if (type(value) is not str or not 1 <= len(value) <= maximum or value in ("NONE", "SELF") or
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", value, re.ASCII) is None):
        _fail(field)


class _Value:
    __slots__ = ()
    def __post_init__(self):
        revalidate_value(self)
    def to_record(self):
        return json.loads(canonical_bytes(self))
    def canonical_bytes(self):
        return canonical_bytes(self)


class _IssuedResult(_Value):
    __slots__ = ("_issuer", "_cookie", "_self_identity", "_wire_digest")


@dataclass(frozen=True, slots=True)
class PlannerEmitterPolicyBinding(_Value):
    policy_id: str
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class PlannerEmitterBinding(_Value):
    canonical_binding: object
    profile_binding: object
    contract_pins: object
    policy_binding: object


@dataclass(frozen=True, slots=True)
class GenerationInputs(_Value):
    project_name: str
    seed_token: str
    topology_depth: int
    transition_sequence: tuple
    profile_id: str
    normalization_mode: str
    role_profile_id: str
    naming_policy_id: str
    subject_policy_id: str
    artifact_policy_id: str
    target_runtime: str
    emission_choice: str


@dataclass(frozen=True, slots=True)
class TargetConstraints(_Value):
    max_artifacts: int
    max_document_bytes: int
    max_total_document_bytes: int
    allow_declared_axiom_failures: bool
    existing_document_policy: str


@dataclass(frozen=True, slots=True)
class RoleAssignment(_Value):
    assignment_reference: str
    node_reference: str
    node_path: str
    role_reference: str
    role_kind: str
    destination_state: object
    ordinal: int
    role_policy_id: str


@dataclass(frozen=True, slots=True)
class PlanMetadata(_Value):
    request_reference: str
    profile_id: str
    source_diagnosis_reference: str
    destination_diagnosis_reference: str
    chain_operation_reference: str
    topology_operation_reference: str
    axiom_operation_reference: str
    role_profile_id: str
    naming_policy_id: str
    subject_policy_id: str
    artifact_policy_id: str
    normalization_mode: str
    materialization_boundary: str


@dataclass(frozen=True, slots=True)
class ManifestRow(_Value):
    node: object
    assignment: object


@dataclass(frozen=True, slots=True)
class ReferenceManifestDocument(_Value):
    document_kind: str
    plan_reference: str
    project_name: str
    page_index: int
    page_count: int
    source_state: str
    destination_state: str
    source_identity: object
    destination_identity: object
    axiom_subject: object
    axiom_diagnostic: object
    warnings: tuple
    inputs: object
    canonical_aggregate_sha256: str
    policy_binding: object
    dependency_operation_references: tuple
    rows: tuple


@dataclass(frozen=True, slots=True)
class ArtifactDescription(_Value):
    artifact_reference: str
    plan_element_reference: str
    kind: str
    name: str
    page_index: int
    role_references: tuple
    document: object
    serializer_id: str
    content_sha256: str
    content_byte_count: int
    semantic_policy_id: str


@dataclass(frozen=True, slots=True)
class ReferenceGenerationPlan(_Value):
    plan_reference: str
    binding: object
    normalized_state: object
    source_state_identity: object
    destination_state_identity: object
    source_realm: object
    destination_realm: object
    topology_nodes: tuple
    role_assignments: tuple
    axiom_subject: object
    axiom_diagnostic: object
    artifacts: tuple
    warnings: tuple
    target_constraints: object
    inputs: object
    metadata: object


@dataclass(frozen=True, slots=True)
class ChainStep(_Value):
    ordinal: int
    input_state: object
    source_proof_reference: str
    selection: object
    selected_definition: object
    selection_observation: object
    applicability_observation: object
    transformation_observation: object
    record_references: tuple


@dataclass(frozen=True, slots=True)
class ChainRecord(_Value):
    record_reference: str
    phase: str
    emission: object
    payload: object


@dataclass(frozen=True, slots=True)
class ChainDiagnosticEmission(_Value):
    diagnostic_reference: str
    envelope: object


@dataclass(frozen=True, slots=True)
class ChainEnvelope(_Value):
    diagnostic_kind: str
    severity: str
    stage: str
    disposition: str
    subject_reference: object
    parent_diagnostic_reference: object
    chain_root_reference: object
    rule_ids: tuple
    summary: object
    notes: tuple


@dataclass(frozen=True, slots=True)
class TransitionChainResult(_IssuedResult):
    operation_reference: str
    binding: object
    origin: object
    origin_validation: object
    selections: tuple
    steps: tuple
    last_candidate: object
    constructed_records: tuple
    final_target_diagnostic: object
    status: str


@dataclass(frozen=True, slots=True)
class TransitionChainFailure(_IssuedResult):
    operation_reference: str
    binding: object
    origin: object
    origin_validation: object
    selections: tuple
    steps: tuple
    last_candidate: object
    constructed_records: tuple
    failed_index: object
    failed_phase: str
    failure_code: str
    status: str


@dataclass(frozen=True, slots=True)
class PlannerRequest(_Value):
    operation_reference: str
    inputs: object
    origin_diagnosis: object
    final_origin_diagnosis: object
    source_encoding: object
    chain: object
    destination_encoding: object
    topology: object
    axioms: object
    target_constraints: object


@dataclass(frozen=True, slots=True)
class PlanDiagnostic(_Value):
    operation_reference: str
    plan_reference: object
    outcome: str
    assignment_count: int
    artifact_count: int
    warnings: tuple
    failure_code: object
    failed_field: object


@dataclass(frozen=True, slots=True)
class MemoryTargetConfiguration(_Value):
    target_reference: str
    target_runtime: str
    policy_binding: object
    max_documents: object
    max_bytes: object


@dataclass(frozen=True, slots=True)
class MaterializedDocument(_Value):
    artifact_reference: str
    plan_reference: str
    plan_element_reference: str
    name: str
    content_ascii: str
    actual_sha256: str
    actual_byte_count: int
    creation_revision: int


@dataclass(frozen=True, slots=True)
class TargetSnapshot(_Value):
    configuration: object
    revision: int
    documents: tuple
    actual_byte_count: int


@dataclass(frozen=True, slots=True)
class EmissionPreparationReceipt(_Value):
    operation_reference: str
    plan_reference: str
    target_reference: str
    status: str
    preparation_reference: object
    failure_code: object


@dataclass(frozen=True, slots=True)
class EmitterRequest(_Value):
    operation_reference: str
    plan: object
    target_configuration: object
    preparation_reference: str


@dataclass(frozen=True, slots=True)
class MemoryTargetReceipt(_IssuedResult):
    operation_reference: str
    artifact_reference: str
    plan_element_reference: str
    target_reference: str
    actual_status: str
    actual_effects: object
    expected_sha256: str
    observed_sha256: object
    expected_byte_count: int
    observed_byte_count: object
    target_revision_before: object
    target_revision_after: object
    readback_assurance: str
    failure_code: object


@dataclass(frozen=True, slots=True)
class EmissionDispatchDiagnostic(_Value):
    operation_reference: str
    plan_reference: str
    artifact_reference: str
    plan_element_reference: str
    artifact_index: int
    expected_sha256: str
    expected_byte_count: int
    target_reference: str


@dataclass(frozen=True, slots=True)
class EmissionOutcomeDiagnostic(_Value):
    dispatch_reference: str
    actual_receipt: object


@dataclass(frozen=True, slots=True)
class EmissionSummaryDiagnostic(_Value):
    operation_reference: str
    plan_reference: str
    status: str
    requested_artifact_count: int
    attempted_artifact_count: int
    confirmed_artifact_count: int
    actual_effects: object
    failure_code: object


@dataclass(frozen=True, slots=True)
class PlannerEmitterEnvelope(_Value):
    diagnostic_kind: str
    severity: str
    stage: str
    disposition: str
    subject_reference: str
    parent_diagnostic_reference: str
    chain_root_reference: str
    rule_ids: tuple
    summary: str
    notes: tuple


@dataclass(frozen=True, slots=True)
class PlannerEmitterRecord(_Value):
    diagnostic_reference: str
    envelope: object
    payload: object


@dataclass(frozen=True, slots=True)
class PendingPlannerEmitterDiagnostic(_Value):
    diagnostic_reference: str
    intended_kind: str
    intended_phase: str
    failure_code: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class PlannerResult(_IssuedResult):
    request: object
    binding: object
    plan: object
    produced_diagnostics: tuple


@dataclass(frozen=True, slots=True)
class PlannerFailure(_IssuedResult):
    request: object
    binding: object
    failure_code: str
    failed_field: str
    produced_diagnostics: tuple
    pending_diagnostic: object


@dataclass(frozen=True, slots=True)
class EmitterResult(_IssuedResult):
    request: object
    binding: object
    status: str
    actual_effects: object
    outcomes: tuple
    produced_diagnostics: tuple
    pending_summary: object
    failure_code: object


@dataclass(frozen=True, slots=True)
class PlannerEmitterCaptureReceipt(_IssuedResult):
    operation_reference: str
    status: str
    result: object
    confirmed_records: tuple
    attempted_record: object
    completion: object
    final_observation: object
    failure_code: object


@dataclass(frozen=True, slots=True)
class GenerationDependencyCaptureReceipt(_Value):
    operation_reference: str
    status: str
    result: object
    confirmed_records: tuple
    attempted_record: object
    completion: object
    final_observation: object
    failure_code: object


@dataclass(frozen=True, slots=True)
class GenerationRunReceipt(_IssuedResult):
    operation_reference: str
    status: str
    last_stage: str
    last_observation: object
    last_origin_completion: object
    completed_operation_references: tuple


WIRE_TYPES = (PlannerEmitterPolicyBinding, PlannerEmitterBinding, GenerationInputs, TargetConstraints, RoleAssignment, PlanMetadata, ManifestRow, ReferenceManifestDocument, ArtifactDescription, ReferenceGenerationPlan, ChainStep, ChainRecord, ChainDiagnosticEmission, ChainEnvelope, TransitionChainResult, TransitionChainFailure, PlannerRequest, PlanDiagnostic, MemoryTargetConfiguration, MaterializedDocument, TargetSnapshot, EmissionPreparationReceipt, EmitterRequest, MemoryTargetReceipt, EmissionDispatchDiagnostic, EmissionOutcomeDiagnostic, EmissionSummaryDiagnostic, PlannerEmitterEnvelope, PlannerEmitterRecord, PendingPlannerEmitterDiagnostic, PlannerResult, PlannerFailure, EmitterResult, PlannerEmitterCaptureReceipt, GenerationDependencyCaptureReceipt, GenerationRunReceipt,)
RESULT_TYPES = (TransitionChainResult, TransitionChainFailure, PlannerResult, PlannerFailure, MemoryTargetReceipt, EmitterResult, PlannerEmitterCaptureReceipt, GenerationRunReceipt,)

FIELD_SCHEMAS = {'PlannerEmitterPolicyBinding': {'policy_id': {'const': 'YWE-M3-PLANNER-EMITTER-REFERENCE-001'},
                                 'policy_version': {'const': '1.0.0'},
                                 'policy_sha256': {'const': '3b4666031a79fec97ed98653bf556ed2d6d8ad538639475813dbd3273b6670b6'}},
 'PlannerEmitterBinding': {'canonical_binding': {'const': {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
                                                           'aggregate_sha256': '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8',
                                                           'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
                                                           'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
                                                           'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
                                                           'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
                                                           'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
                                                           'diagnostic_source_sha256': '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa',
                                                           'taxonomy_source_sha256': '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'}},
                           'profile_binding': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/ProfileBinding'},
                           'contract_pins': {'const': [{'path': 'interfaces/contracts/generation-planner-contract.md',
                                                        'sha256': '09f2a6c99fa4b39484e5c5497103b3e09d274a6ddfda2c97dc9eba5cfd685708'},
                                                       {'path': 'interfaces/contracts/artifact-emitter-contract.md',
                                                        'sha256': 'cca1c794405f2d85c80f5de2e1efd6a8f1bc395985a39ebf7ebc6daf64b53243'},
                                                       {'path': 'algorithms/generation-planning.pseudo.md',
                                                        'sha256': '88d474a4e25e297ef59f28245bc6a0f4cfa375d4173433240d993639d8e30ec1'},
                                                       {'path': 'interfaces/contracts/realm-encoder-contract.md',
                                                        'sha256': 'b3fa0deb71ae136c712f402f2b8159b7448ef8756a884369931ab7098bc83fbb'},
                                                       {'path': 'interfaces/contracts/transition-registry-contract.md',
                                                        'sha256': '4460f1c6f3dbc5289d29bfdbb1c7b1ca5dabfa60f425be3d9ca485855eb5d903'},
                                                       {'path': 'interfaces/contracts/topology-generator-contract.md',
                                                        'sha256': 'a408b335ecacff01e38113bcd6cc6089142e40219d521e7081e87406fac11147'},
                                                       {'path': 'interfaces/contracts/axiom-evaluator-contract.md',
                                                        'sha256': 'dc2edf80d2ded0b89b31df15416e24c13139988ab6fd38adaa6195921a692faf'},
                                                       {'path': 'core/realm-identity.pseudo.md',
                                                        'sha256': '43f274d9c8c1b7269938bf8661c42e91cf020d215683cb6dfa4b340ff975cad5'},
                                                       {'path': 'interfaces/diagnostic-schema.md',
                                                        'sha256': '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa'},
                                                       {'path': 'interfaces/rule-id-taxonomy.md',
                                                        'sha256': '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'},
                                                       {'path': 'interfaces/contracts/diagnostics-module-contract.md',
                                                        'sha256': '5ba322a2376bb325e5d58d9341938535ee8d69ff0fc286b3969dfdb77bd8c225'}]},
                           'policy_binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterPolicyBinding'}},
 'GenerationInputs': {'project_name': {'type': 'string',
                                       'minLength': 1,
                                       'maxLength': 32,
                                       'pattern': '^[a-z][a-z0-9_-]{0,31}$'},
                      'seed_token': {'type': 'string',
                                     'minLength': 1,
                                     'maxLength': 32,
                                     'pattern': '^[A-Za-z0-9_-]{1,32}$'},
                      'topology_depth': {'type': 'integer', 'minimum': 0, 'maximum': 6},
                      'transition_sequence': {'type': 'array',
                                              'items': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionSelection'},
                                              'minItems': 0,
                                              'maxItems': 4},
                      'profile_id': {'type': 'string',
                                     'minLength': 1,
                                     'maxLength': 160,
                                     'pattern': '^[A-Za-z0-9][A-Za-z0-9._:-]*$'},
                      'normalization_mode': {'const': 'ALREADY_VALID'},
                      'role_profile_id': {'const': 'TERNARY_BRANCH_ROLES_001'},
                      'naming_policy_id': {'const': 'YWE_ASCII_DOCUMENT_NAMES_001'},
                      'subject_policy_id': {'const': 'DECLARED_AXIOM_FACTS_001'},
                      'artifact_policy_id': {'const': 'REFERENCE_MANIFEST_PAGES_001'},
                      'target_runtime': {'const': 'REFERENCE_MEMORY_DOCUMENTS'},
                      'emission_choice': {'type': 'string',
                                          'enum': ['REFERENCE_MANIFEST_PAGES', 'INSPECT_ONLY']}},
 'TargetConstraints': {'max_artifacts': {'type': 'integer', 'minimum': 0, 'maximum': 32},
                       'max_document_bytes': {'type': 'integer', 'minimum': 1, 'maximum': 32768},
                       'max_total_document_bytes': {'type': 'integer', 'minimum': 1, 'maximum': 1048576},
                       'allow_declared_axiom_failures': {'type': 'boolean'},
                       'existing_document_policy': {'const': 'EXACT_BYTES_IDEMPOTENT_OR_REFUSE'}},
 'RoleAssignment': {'assignment_reference': {'type': 'string',
                                             'minLength': 1,
                                             'maxLength': 256,
                                             'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                    'node_reference': {'type': 'string',
                                       'minLength': 1,
                                       'maxLength': 256,
                                       'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                    'node_path': {'type': 'string',
                                  'minLength': 1,
                                  'maxLength': 7,
                                  'pattern': '^r[012]{0,6}$'},
                    'role_reference': {'type': 'string',
                                       'enum': ['role:root',
                                                'role:continuation',
                                                'role:positive',
                                                'role:negative']},
                    'role_kind': {'type': 'string', 'enum': ['ROOT', 'CONTINUATION', 'POSITIVE', 'NEGATIVE']},
                    'destination_state': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/AshState'},
                    'ordinal': {'type': 'integer', 'minimum': 0, 'maximum': 728},
                    'role_policy_id': {'const': 'TERNARY_BRANCH_ROLES_001'}},
 'PlanMetadata': {'request_reference': {'type': 'string',
                                        'minLength': 1,
                                        'maxLength': 160,
                                        'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                  'profile_id': {'type': 'string', 'minLength': 1, 'maxLength': 160},
                  'source_diagnosis_reference': {'type': 'string',
                                                 'minLength': 1,
                                                 'maxLength': 256,
                                                 'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                  'destination_diagnosis_reference': {'type': 'string',
                                                      'minLength': 1,
                                                      'maxLength': 256,
                                                      'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                  'chain_operation_reference': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 256,
                                                'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                  'topology_operation_reference': {'type': 'string',
                                                   'minLength': 1,
                                                   'maxLength': 256,
                                                   'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                  'axiom_operation_reference': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 256,
                                                'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                  'role_profile_id': {'const': 'TERNARY_BRANCH_ROLES_001'},
                  'naming_policy_id': {'const': 'YWE_ASCII_DOCUMENT_NAMES_001'},
                  'subject_policy_id': {'const': 'DECLARED_AXIOM_FACTS_001'},
                  'artifact_policy_id': {'const': 'REFERENCE_MANIFEST_PAGES_001'},
                  'normalization_mode': {'const': 'ALREADY_VALID'},
                  'materialization_boundary': {'const': 'ABSTRACT_NO_EXTERNAL_EFFECTS'}},
 'ManifestRow': {'node': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/TopologyNode'},
                 'assignment': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/RoleAssignment'}},
 'ReferenceManifestDocument': {'document_kind': {'const': 'YWE_REFERENCE_MANIFEST'},
                               'plan_reference': {'type': 'string',
                                                  'minLength': 1,
                                                  'maxLength': 256,
                                                  'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                               'project_name': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 32,
                                                'pattern': '^[a-z][a-z0-9_-]{0,31}$'},
                               'page_index': {'type': 'integer', 'minimum': 0, 'maximum': 22},
                               'page_count': {'type': 'integer', 'minimum': 1, 'maximum': 23},
                               'source_state': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 9,
                                                'pattern': '^[01]{9}$'},
                               'destination_state': {'type': 'string',
                                                     'minLength': 1,
                                                     'maxLength': 9,
                                                     'pattern': '^[01]{9}$'},
                               'source_identity': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmIdentity'},
                               'destination_identity': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmIdentity'},
                               'axiom_subject': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomSubject'},
                               'axiom_diagnostic': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomDiagnostic'},
                               'warnings': {'type': 'array',
                                            'items': {'type': 'string',
                                                      'enum': ['A1_FAILED',
                                                               'A2_FAILED',
                                                               'A3_FAILED',
                                                               'A4_FAILED',
                                                               'A5_FAILED']},
                                            'minItems': 0,
                                            'maxItems': 5},
                               'inputs': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/GenerationInputs'},
                               'canonical_aggregate_sha256': {'const': '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8'},
                               'policy_binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterPolicyBinding'},
                               'dependency_operation_references': {'type': 'array',
                                                                   'items': {'type': 'string',
                                                                             'minLength': 1,
                                                                             'maxLength': 256,
                                                                             'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                                                   'minItems': 5,
                                                                   'maxItems': 5},
                               'rows': {'type': 'array',
                                        'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ManifestRow'},
                                        'minItems': 1,
                                        'maxItems': 32}},
 'ArtifactDescription': {'artifact_reference': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 256,
                                                'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                         'plan_element_reference': {'type': 'string',
                                                    'minLength': 1,
                                                    'maxLength': 256,
                                                    'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                         'kind': {'const': 'REFERENCE_MANIFEST'},
                         'name': {'type': 'string',
                                  'minLength': 1,
                                  'maxLength': 62,
                                  'pattern': '^ywe-[a-z][a-z0-9_-]{0,31}-manifest-[0-9]{3}\\.json$'},
                         'page_index': {'type': 'integer', 'minimum': 0, 'maximum': 22},
                         'role_references': {'type': 'array',
                                             'items': {'type': 'string',
                                                       'enum': ['role:root',
                                                                'role:continuation',
                                                                'role:positive',
                                                                'role:negative']},
                                             'minItems': 1,
                                             'maxItems': 4},
                         'document': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ReferenceManifestDocument'},
                         'serializer_id': {'const': 'UTF8_ASCII_JSON_SORTED_COMPACT_NO_NEWLINE'},
                         'content_sha256': {'type': 'string',
                                            'minLength': 1,
                                            'maxLength': 64,
                                            'pattern': '^[0-9a-f]{64}$'},
                         'content_byte_count': {'type': 'integer', 'minimum': 1, 'maximum': 32768},
                         'semantic_policy_id': {'const': 'REFERENCE_MANIFEST_PAGES_001'}},
 'ReferenceGenerationPlan': {'plan_reference': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 256,
                                                'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                             'binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterBinding'},
                             'normalized_state': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/AshState'},
                             'source_state_identity': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmIdentity'},
                             'destination_state_identity': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmIdentity'},
                             'source_realm': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmIdentity'},
                             'destination_realm': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmIdentity'},
                             'topology_nodes': {'type': 'array',
                                                'items': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/TopologyNode'},
                                                'minItems': 1,
                                                'maxItems': 729},
                             'role_assignments': {'type': 'array',
                                                  'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/RoleAssignment'},
                                                  'minItems': 1,
                                                  'maxItems': 729},
                             'axiom_subject': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomSubject'},
                             'axiom_diagnostic': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomDiagnostic'},
                             'artifacts': {'type': 'array',
                                           'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ArtifactDescription'},
                                           'minItems': 0,
                                           'maxItems': 23},
                             'warnings': {'type': 'array',
                                          'items': {'type': 'string',
                                                    'enum': ['A1_FAILED',
                                                             'A2_FAILED',
                                                             'A3_FAILED',
                                                             'A4_FAILED',
                                                             'A5_FAILED']},
                                          'minItems': 0,
                                          'maxItems': 5},
                             'target_constraints': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/TargetConstraints'},
                             'inputs': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/GenerationInputs'},
                             'metadata': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlanMetadata'}},
 'ChainStep': {'ordinal': {'type': 'integer', 'minimum': 0, 'maximum': 3},
               'input_state': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/AshState'},
               'source_proof_reference': {'type': 'string',
                                          'minLength': 1,
                                          'maxLength': 256,
                                          'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
               'selection': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionSelection'},
               'selected_definition': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionDefinition'},
               'selection_observation': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionSelectionObservation'},
               'applicability_observation': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionApplicabilityObservation'},
               'transformation_observation': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionTransformationObservation'},
               'record_references': {'type': 'array',
                                     'items': {'type': 'string',
                                               'minLength': 1,
                                               'maxLength': 256,
                                               'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                     'minItems': 3,
                                     'maxItems': 3}},
 'ChainRecord': {'record_reference': {'type': 'string',
                                      'minLength': 1,
                                      'maxLength': 256,
                                      'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                 'phase': {'type': 'string',
                           'enum': ['VALID_SOURCE', 'SELECTION', 'APPLICABILITY', 'TRANSFORMATION']},
                 'emission': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainDiagnosticEmission'},
                 'payload': {'oneOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmTransitionGate'},
                                       {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionSelectionObservation'},
                                       {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionApplicabilityObservation'},
                                       {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionTransformationObservation'}]}},
 'ChainDiagnosticEmission': {'diagnostic_reference': {'type': 'string',
                                                      'minLength': 1,
                                                      'maxLength': 256,
                                                      'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                             'envelope': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainEnvelope'}},
 'ChainEnvelope': {'diagnostic_kind': {'const': 'TRANSITION'},
                   'severity': {'type': 'string', 'enum': ['INFO', 'WARNING', 'ERROR', 'CRITICAL']},
                   'stage': {'const': 'PROCESSING'},
                   'disposition': {'type': 'string', 'enum': ['RESOLVED', 'BLOCKED']},
                   'subject_reference': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/Identifier'},
                   'parent_diagnostic_reference': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/Identifier'},
                   'chain_root_reference': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/Identifier'},
                   'rule_ids': {'type': 'array',
                                'items': {'type': 'string',
                                          'enum': ['ASH-STATE-VALIDITY-001',
                                                   'ASH-CODEWORD-STRUCTURE-001',
                                                   'ASH-CODEWORD-REGISTRY-001',
                                                   'ASH-CODEWORD-SELECTION-001',
                                                   'ASH-CODEWORD-APPLICABILITY-001',
                                                   'ASH-CODEWORD-TRANSFORMATION-001']},
                                'minItems': 1,
                                'maxItems': 2},
                   'summary': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/LineText'},
                   'notes': {'type': 'array',
                             'items': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/LineText'},
                             'minItems': 1,
                             'maxItems': 1}},
 'TransitionChainResult': {'operation_reference': {'type': 'string',
                                                   'minLength': 1,
                                                   'maxLength': 160,
                                                   'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                           'binding': {'allOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmTransitionBinding'},
                                                 {'properties': {'canonical_binding': {'const': {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
                                                                                                 'aggregate_sha256': '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8',
                                                                                                 'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
                                                                                                 'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
                                                                                                 'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
                                                                                                 'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
                                                                                                 'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
                                                                                                 'diagnostic_source_sha256': '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa',
                                                                                                 'taxonomy_source_sha256': '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'}}}}]},
                           'origin': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/StateDiagnosis'},
                           'origin_validation': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/DiagnosisValidation'},
                           'selections': {'type': 'array',
                                          'items': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionSelection'},
                                          'minItems': 0,
                                          'maxItems': 4},
                           'steps': {'type': 'array',
                                     'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainStep'},
                                     'minItems': 0,
                                     'maxItems': 4},
                           'last_candidate': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/AshState'},
                                                        {'type': 'null'}]},
                           'constructed_records': {'type': 'array',
                                                   'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainRecord'},
                                                   'minItems': 1,
                                                   'maxItems': 13},
                           'final_target_diagnostic': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/StateValidityDiagnostic'},
                           'status': {'const': 'COMPLETE'}},
 'TransitionChainFailure': {'operation_reference': {'type': 'string',
                                                    'minLength': 1,
                                                    'maxLength': 160,
                                                    'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                            'binding': {'allOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmTransitionBinding'},
                                                  {'properties': {'canonical_binding': {'const': {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
                                                                                                  'aggregate_sha256': '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8',
                                                                                                  'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
                                                                                                  'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
                                                                                                  'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
                                                                                                  'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
                                                                                                  'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
                                                                                                  'diagnostic_source_sha256': '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa',
                                                                                                  'taxonomy_source_sha256': '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'}}}}]},
                            'origin': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/StateDiagnosis'},
                            'origin_validation': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/DiagnosisValidation'},
                            'selections': {'type': 'array',
                                           'items': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionSelection'},
                                           'minItems': 0,
                                           'maxItems': 4},
                            'steps': {'type': 'array',
                                      'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainStep'},
                                      'minItems': 0,
                                      'maxItems': 4},
                            'last_candidate': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/AshState'},
                                                         {'type': 'null'}]},
                            'constructed_records': {'type': 'array',
                                                    'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainRecord'},
                                                    'minItems': 1,
                                                    'maxItems': 13},
                            'failed_index': {'anyOf': [{'type': 'integer', 'minimum': 0, 'maximum': 3},
                                                       {'type': 'null'}]},
                            'failed_phase': {'type': 'string',
                                             'enum': ['VALID_SOURCE',
                                                      'SELECTION',
                                                      'APPLICABILITY',
                                                      'TRANSFORMATION']},
                            'failure_code': {'type': 'string',
                                             'enum': ['PROFILE_UNAVAILABLE',
                                                      'STATE_NOT_VALID',
                                                      'TRANSITION_UNKNOWN',
                                                      'CODEWORD_NOT_CANONICAL',
                                                      'TRANSITION_NOT_APPLICABLE',
                                                      'CHAIN_TARGET_NOT_VALID']},
                            'status': {'const': 'FAILED_PREFIX'}},
 'PlannerRequest': {'operation_reference': {'type': 'string',
                                            'minLength': 1,
                                            'maxLength': 160,
                                            'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                    'inputs': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/GenerationInputs'},
                    'origin_diagnosis': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/StateDiagnosis'},
                    'final_origin_diagnosis': {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/StateDiagnosis'},
                    'source_encoding': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmEncodingResult'},
                    'chain': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/TransitionChainResult'},
                    'destination_encoding': {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmEncodingResult'},
                    'topology': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/TopologyResult'},
                    'axioms': {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomEvaluationResult'},
                    'target_constraints': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/TargetConstraints'}},
 'PlanDiagnostic': {'operation_reference': {'type': 'string',
                                            'minLength': 1,
                                            'maxLength': 160,
                                            'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                    'plan_reference': {'anyOf': [{'type': 'string',
                                                  'minLength': 1,
                                                  'maxLength': 256,
                                                  'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                                 {'type': 'null'}]},
                    'outcome': {'type': 'string', 'enum': ['COMPLETE', 'REFUSED']},
                    'assignment_count': {'type': 'integer', 'minimum': 0, 'maximum': 729},
                    'artifact_count': {'type': 'integer', 'minimum': 0, 'maximum': 23},
                    'warnings': {'type': 'array',
                                 'items': {'type': 'string',
                                           'enum': ['A1_FAILED',
                                                    'A2_FAILED',
                                                    'A3_FAILED',
                                                    'A4_FAILED',
                                                    'A5_FAILED']},
                                 'minItems': 0,
                                 'maxItems': 5},
                    'failure_code': {'anyOf': [{'type': 'string',
                                                'enum': ['SOURCE_UNSUPPORTED',
                                                         'PROFILE_UNAVAILABLE',
                                                         'ORIGIN_REJECTED',
                                                         'ORIGIN_UNPARSED',
                                                         'SOURCE_NOT_NORMALIZED',
                                                         'DEPENDENCY_FOREIGN',
                                                         'DEPENDENCY_MISMATCH',
                                                         'CHAIN_NOT_COMPLETE',
                                                         'FINAL_DIAGNOSIS_MISMATCH',
                                                         'SUBJECT_PROVENANCE_MISMATCH',
                                                         'TARGET_CONSTRAINT_UNSATISFIED',
                                                         'REFERENCE_COLLISION',
                                                         'RAW_BUSINESS_LIMIT']},
                                               {'type': 'null'}]},
                    'failed_field': {'anyOf': [{'type': 'string',
                                                'enum': ['binding',
                                                         'request.origin',
                                                         'request.final_origin',
                                                         'request.inputs',
                                                         'request.source_encoding',
                                                         'request.chain',
                                                         'request.destination_encoding',
                                                         'request.topology',
                                                         'request.axioms',
                                                         'request.target_constraints',
                                                         'request.reference_set',
                                                         'plan',
                                                         'plan.artifacts',
                                                         'plan.axiom_diagnostic',
                                                         'preparation',
                                                         'scope.admission',
                                                         'scope.dispatch',
                                                         'scope.outcome',
                                                         'scope.summary',
                                                         'scope.completion',
                                                         'target',
                                                         'target.readback',
                                                         'raw_business_packet']},
                                               {'type': 'null'}]}},
 'MemoryTargetConfiguration': {'target_reference': {'type': 'string',
                                                    'minLength': 1,
                                                    'maxLength': 256,
                                                    'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                               'target_runtime': {'const': 'REFERENCE_MEMORY_DOCUMENTS'},
                               'policy_binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterPolicyBinding'},
                               'max_documents': {'const': 32},
                               'max_bytes': {'const': 1048576}},
 'MaterializedDocument': {'artifact_reference': {'type': 'string',
                                                 'minLength': 1,
                                                 'maxLength': 256,
                                                 'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                          'plan_reference': {'type': 'string',
                                             'minLength': 1,
                                             'maxLength': 256,
                                             'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                          'plan_element_reference': {'type': 'string',
                                                     'minLength': 1,
                                                     'maxLength': 256,
                                                     'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                          'name': {'type': 'string',
                                   'minLength': 1,
                                   'maxLength': 62,
                                   'pattern': '^ywe-[a-z][a-z0-9_-]{0,31}-manifest-[0-9]{3}\\.json$'},
                          'content_ascii': {'type': 'string',
                                            'minLength': 1,
                                            'maxLength': 32768,
                                            'pattern': '^[\\x20-\\x7e]+$'},
                          'actual_sha256': {'type': 'string',
                                            'minLength': 1,
                                            'maxLength': 64,
                                            'pattern': '^[0-9a-f]{64}$'},
                          'actual_byte_count': {'type': 'integer', 'minimum': 1, 'maximum': 32768},
                          'creation_revision': {'type': 'integer',
                                                'minimum': 1,
                                                'maximum': 18446744073709551615}},
 'TargetSnapshot': {'configuration': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/MemoryTargetConfiguration'},
                    'revision': {'type': 'integer', 'minimum': 0, 'maximum': 18446744073709551615},
                    'documents': {'type': 'array',
                                  'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/MaterializedDocument'},
                                  'minItems': 0,
                                  'maxItems': 32},
                    'actual_byte_count': {'type': 'integer', 'minimum': 0, 'maximum': 1048576}},
 'EmissionPreparationReceipt': {'operation_reference': {'type': 'string',
                                                        'minLength': 1,
                                                        'maxLength': 160,
                                                        'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'plan_reference': {'type': 'string',
                                                   'minLength': 1,
                                                   'maxLength': 256,
                                                   'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'target_reference': {'type': 'string',
                                                     'minLength': 1,
                                                     'maxLength': 256,
                                                     'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'status': {'type': 'string', 'enum': ['ISSUED', 'REJECTED']},
                                'preparation_reference': {'anyOf': [{'type': 'string',
                                                                     'minLength': 1,
                                                                     'maxLength': 256,
                                                                     'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                                                    {'type': 'null'}]},
                                'failure_code': {'anyOf': [{'type': 'string',
                                                            'enum': ['PREPARATION_FOREIGN',
                                                                     'PREPARATION_USED',
                                                                     'PREPARATION_LIMIT',
                                                                     'EMITTER_BUSY',
                                                                     'PLAN_INCOMPLETE',
                                                                     'PLAN_BINDING_MISMATCH',
                                                                     'AXIOM_FAILURE_NOT_AUTHORIZED',
                                                                     'TARGET_CONSTRAINT_UNSATISFIED',
                                                                     'CAPTURE_ADMISSION_UNCONFIRMED',
                                                                     'DISPATCH_UNCONFIRMED',
                                                                     'COMMAND_CANCELLED',
                                                                     'DOCUMENT_CONFLICT',
                                                                     'TARGET_RESOURCE_LIMIT',
                                                                     'TARGET_BUSY',
                                                                     'TARGET_STALE_REVISION',
                                                                     'TARGET_VERSION_EXHAUSTED',
                                                                     'TARGET_RECEIPT_FOREIGN',
                                                                     'TARGET_READBACK_MISMATCH',
                                                                     'TARGET_INTERNAL_FAILURE',
                                                                     'TARGET_EFFECT_UNKNOWN',
                                                                     'OUTCOME_CAPTURE_UNCONFIRMED',
                                                                     'SUMMARY_CAPTURE_UNCONFIRMED',
                                                                     'COMPLETION_UNCONFIRMED',
                                                                     'RAW_BUSINESS_LIMIT']},
                                                           {'type': 'null'}]}},
 'EmitterRequest': {'operation_reference': {'type': 'string',
                                            'minLength': 1,
                                            'maxLength': 160,
                                            'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                    'plan': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ReferenceGenerationPlan'},
                    'target_configuration': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/MemoryTargetConfiguration'},
                    'preparation_reference': {'type': 'string',
                                              'minLength': 1,
                                              'maxLength': 256,
                                              'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'}},
 'MemoryTargetReceipt': {'operation_reference': {'type': 'string',
                                                 'minLength': 1,
                                                 'maxLength': 160,
                                                 'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                         'artifact_reference': {'type': 'string',
                                                'minLength': 1,
                                                'maxLength': 256,
                                                'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                         'plan_element_reference': {'type': 'string',
                                                    'minLength': 1,
                                                    'maxLength': 256,
                                                    'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                         'target_reference': {'type': 'string',
                                              'minLength': 1,
                                              'maxLength': 256,
                                              'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                         'actual_status': {'type': 'string',
                                           'enum': ['SUCCEEDED', 'NO_EFFECT', 'FAILED', 'UNKNOWN']},
                         'actual_effects': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
                         'expected_sha256': {'type': 'string',
                                             'minLength': 1,
                                             'maxLength': 64,
                                             'pattern': '^[0-9a-f]{64}$'},
                         'observed_sha256': {'anyOf': [{'type': 'string',
                                                        'minLength': 1,
                                                        'maxLength': 64,
                                                        'pattern': '^[0-9a-f]{64}$'},
                                                       {'type': 'null'}]},
                         'expected_byte_count': {'type': 'integer', 'minimum': 1, 'maximum': 32768},
                         'observed_byte_count': {'anyOf': [{'type': 'integer',
                                                            'minimum': 0,
                                                            'maximum': 32768},
                                                           {'type': 'null'}]},
                         'target_revision_before': {'anyOf': [{'type': 'integer',
                                                               'minimum': 0,
                                                               'maximum': 18446744073709551615},
                                                              {'type': 'null'}]},
                         'target_revision_after': {'anyOf': [{'type': 'integer',
                                                              'minimum': 0,
                                                              'maximum': 18446744073709551615},
                                                             {'type': 'null'}]},
                         'readback_assurance': {'type': 'string',
                                                'enum': ['OWNED_EXACT_READBACK', 'UNAVAILABLE']},
                         'failure_code': {'anyOf': [{'type': 'string',
                                                     'enum': ['PREPARATION_FOREIGN',
                                                              'PREPARATION_USED',
                                                              'PREPARATION_LIMIT',
                                                              'EMITTER_BUSY',
                                                              'PLAN_INCOMPLETE',
                                                              'PLAN_BINDING_MISMATCH',
                                                              'AXIOM_FAILURE_NOT_AUTHORIZED',
                                                              'TARGET_CONSTRAINT_UNSATISFIED',
                                                              'CAPTURE_ADMISSION_UNCONFIRMED',
                                                              'DISPATCH_UNCONFIRMED',
                                                              'COMMAND_CANCELLED',
                                                              'DOCUMENT_CONFLICT',
                                                              'TARGET_RESOURCE_LIMIT',
                                                              'TARGET_BUSY',
                                                              'TARGET_STALE_REVISION',
                                                              'TARGET_VERSION_EXHAUSTED',
                                                              'TARGET_RECEIPT_FOREIGN',
                                                              'TARGET_READBACK_MISMATCH',
                                                              'TARGET_INTERNAL_FAILURE',
                                                              'TARGET_EFFECT_UNKNOWN',
                                                              'OUTCOME_CAPTURE_UNCONFIRMED',
                                                              'SUMMARY_CAPTURE_UNCONFIRMED',
                                                              'COMPLETION_UNCONFIRMED',
                                                              'RAW_BUSINESS_LIMIT']},
                                                    {'type': 'null'}]}},
 'EmissionDispatchDiagnostic': {'operation_reference': {'type': 'string',
                                                        'minLength': 1,
                                                        'maxLength': 160,
                                                        'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'plan_reference': {'type': 'string',
                                                   'minLength': 1,
                                                   'maxLength': 256,
                                                   'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'artifact_reference': {'type': 'string',
                                                       'minLength': 1,
                                                       'maxLength': 256,
                                                       'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'plan_element_reference': {'type': 'string',
                                                           'minLength': 1,
                                                           'maxLength': 256,
                                                           'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                'artifact_index': {'type': 'integer', 'minimum': 0, 'maximum': 22},
                                'expected_sha256': {'type': 'string',
                                                    'minLength': 1,
                                                    'maxLength': 64,
                                                    'pattern': '^[0-9a-f]{64}$'},
                                'expected_byte_count': {'type': 'integer', 'minimum': 1, 'maximum': 32768},
                                'target_reference': {'type': 'string',
                                                     'minLength': 1,
                                                     'maxLength': 256,
                                                     'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'}},
 'EmissionOutcomeDiagnostic': {'dispatch_reference': {'type': 'string',
                                                      'minLength': 1,
                                                      'maxLength': 256,
                                                      'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                               'actual_receipt': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/MemoryTargetReceipt'}},
 'EmissionSummaryDiagnostic': {'operation_reference': {'type': 'string',
                                                       'minLength': 1,
                                                       'maxLength': 160,
                                                       'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                               'plan_reference': {'type': 'string',
                                                  'minLength': 1,
                                                  'maxLength': 256,
                                                  'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                               'status': {'type': 'string',
                                          'enum': ['SUCCEEDED', 'NO_OP', 'FAILED', 'PARTIAL', 'UNKNOWN']},
                               'requested_artifact_count': {'type': 'integer', 'minimum': 0, 'maximum': 23},
                               'attempted_artifact_count': {'type': 'integer', 'minimum': 0, 'maximum': 23},
                               'confirmed_artifact_count': {'type': 'integer', 'minimum': 0, 'maximum': 23},
                               'actual_effects': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
                               'failure_code': {'anyOf': [{'type': 'string',
                                                           'enum': ['PREPARATION_FOREIGN',
                                                                    'PREPARATION_USED',
                                                                    'PREPARATION_LIMIT',
                                                                    'EMITTER_BUSY',
                                                                    'PLAN_INCOMPLETE',
                                                                    'PLAN_BINDING_MISMATCH',
                                                                    'AXIOM_FAILURE_NOT_AUTHORIZED',
                                                                    'TARGET_CONSTRAINT_UNSATISFIED',
                                                                    'CAPTURE_ADMISSION_UNCONFIRMED',
                                                                    'DISPATCH_UNCONFIRMED',
                                                                    'COMMAND_CANCELLED',
                                                                    'DOCUMENT_CONFLICT',
                                                                    'TARGET_RESOURCE_LIMIT',
                                                                    'TARGET_BUSY',
                                                                    'TARGET_STALE_REVISION',
                                                                    'TARGET_VERSION_EXHAUSTED',
                                                                    'TARGET_RECEIPT_FOREIGN',
                                                                    'TARGET_READBACK_MISMATCH',
                                                                    'TARGET_INTERNAL_FAILURE',
                                                                    'TARGET_EFFECT_UNKNOWN',
                                                                    'OUTCOME_CAPTURE_UNCONFIRMED',
                                                                    'SUMMARY_CAPTURE_UNCONFIRMED',
                                                                    'COMPLETION_UNCONFIRMED',
                                                                    'RAW_BUSINESS_LIMIT']},
                                                          {'type': 'null'}]}},
 'PlannerEmitterEnvelope': {'diagnostic_kind': {'type': 'string',
                                                'enum': ['GENERATION_PLAN', 'ARTIFACT_EMISSION']},
                            'severity': {'type': 'string', 'enum': ['INFO', 'WARNING', 'ERROR', 'CRITICAL']},
                            'stage': {'const': 'PROCESSING'},
                            'disposition': {'type': 'string', 'enum': ['RESOLVED', 'BLOCKED']},
                            'subject_reference': {'type': 'string',
                                                  'minLength': 1,
                                                  'maxLength': 256,
                                                  'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                            'parent_diagnostic_reference': {'type': 'string',
                                                            'minLength': 1,
                                                            'maxLength': 256,
                                                            'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                            'chain_root_reference': {'type': 'string',
                                                     'minLength': 1,
                                                     'maxLength': 256,
                                                     'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                            'rule_ids': {'type': 'array',
                                         'items': {'type': 'string',
                                                   'enum': ['ASH-GENERATION-PLAN-001',
                                                            'ASH-GENERATION-BOUNDARY-001',
                                                            'ASH-GENERATION-TRACEABILITY-001',
                                                            'ASH-GENERATION-EMISSION-001',
                                                            'ASH-GENERATION-PLANFIDELITY-001']},
                                         'minItems': 1,
                                         'maxItems': 3},
                            'summary': {'type': 'string', 'minLength': 1, 'maxLength': 128},
                            'notes': {'type': 'array',
                                      'items': {'type': 'string', 'minLength': 1, 'maxLength': 512},
                                      'minItems': 0,
                                      'maxItems': 4}},
 'PlannerEmitterRecord': {'diagnostic_reference': {'type': 'string',
                                                   'minLength': 1,
                                                   'maxLength': 256,
                                                   'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                          'envelope': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterEnvelope'},
                          'payload': {'oneOf': [{'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlanDiagnostic'},
                                                {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/EmissionDispatchDiagnostic'},
                                                {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/EmissionOutcomeDiagnostic'},
                                                {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/EmissionSummaryDiagnostic'}]}},
 'PendingPlannerEmitterDiagnostic': {'diagnostic_reference': {'type': 'string',
                                                              'minLength': 1,
                                                              'maxLength': 256,
                                                              'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                     'intended_kind': {'type': 'string',
                                                       'enum': ['GENERATION_PLAN', 'ARTIFACT_EMISSION']},
                                     'intended_phase': {'type': 'string',
                                                        'enum': ['PLAN_BUILD',
                                                                 'ARTIFACT_DISPATCH',
                                                                 'ARTIFACT_RECEIPT',
                                                                 'OPERATION_SUMMARY']},
                                     'failure_code': {'type': 'string',
                                                      'enum': ['SOURCE_UNSUPPORTED',
                                                               'PROFILE_UNAVAILABLE',
                                                               'ORIGIN_REJECTED',
                                                               'ORIGIN_UNPARSED',
                                                               'SOURCE_NOT_NORMALIZED',
                                                               'DEPENDENCY_FOREIGN',
                                                               'DEPENDENCY_MISMATCH',
                                                               'CHAIN_NOT_COMPLETE',
                                                               'FINAL_DIAGNOSIS_MISMATCH',
                                                               'SUBJECT_PROVENANCE_MISMATCH',
                                                               'TARGET_CONSTRAINT_UNSATISFIED',
                                                               'REFERENCE_COLLISION',
                                                               'RAW_BUSINESS_LIMIT',
                                                               'PREPARATION_FOREIGN',
                                                               'PREPARATION_USED',
                                                               'PREPARATION_LIMIT',
                                                               'EMITTER_BUSY',
                                                               'PLAN_INCOMPLETE',
                                                               'PLAN_BINDING_MISMATCH',
                                                               'AXIOM_FAILURE_NOT_AUTHORIZED',
                                                               'TARGET_CONSTRAINT_UNSATISFIED',
                                                               'CAPTURE_ADMISSION_UNCONFIRMED',
                                                               'DISPATCH_UNCONFIRMED',
                                                               'COMMAND_CANCELLED',
                                                               'DOCUMENT_CONFLICT',
                                                               'TARGET_RESOURCE_LIMIT',
                                                               'TARGET_BUSY',
                                                               'TARGET_STALE_REVISION',
                                                               'TARGET_VERSION_EXHAUSTED',
                                                               'TARGET_RECEIPT_FOREIGN',
                                                               'TARGET_READBACK_MISMATCH',
                                                               'TARGET_INTERNAL_FAILURE',
                                                               'TARGET_EFFECT_UNKNOWN',
                                                               'OUTCOME_CAPTURE_UNCONFIRMED',
                                                               'SUMMARY_CAPTURE_UNCONFIRMED',
                                                               'COMPLETION_UNCONFIRMED',
                                                               'RAW_BUSINESS_LIMIT']},
                                     'reason_code': {'type': 'string',
                                                     'enum': ['NO_VERIFIED_ORIGIN',
                                                              'CAPTURE_NOT_APPENDABLE',
                                                              'CAPTURE_NOT_CONFIRMED',
                                                              'CAPABILITY_REFUSED']}},
 'PlannerResult': {'request': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerRequest'},
                   'binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterBinding'},
                   'plan': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ReferenceGenerationPlan'},
                   'produced_diagnostics': {'type': 'array',
                                            'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterRecord'},
                                            'minItems': 1,
                                            'maxItems': 1}},
 'PlannerFailure': {'request': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerRequest'},
                    'binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterBinding'},
                    'failure_code': {'type': 'string',
                                     'enum': ['SOURCE_UNSUPPORTED',
                                              'PROFILE_UNAVAILABLE',
                                              'ORIGIN_REJECTED',
                                              'ORIGIN_UNPARSED',
                                              'SOURCE_NOT_NORMALIZED',
                                              'DEPENDENCY_FOREIGN',
                                              'DEPENDENCY_MISMATCH',
                                              'CHAIN_NOT_COMPLETE',
                                              'FINAL_DIAGNOSIS_MISMATCH',
                                              'SUBJECT_PROVENANCE_MISMATCH',
                                              'TARGET_CONSTRAINT_UNSATISFIED',
                                              'REFERENCE_COLLISION',
                                              'RAW_BUSINESS_LIMIT']},
                    'failed_field': {'type': 'string',
                                     'enum': ['binding',
                                              'request.origin',
                                              'request.final_origin',
                                              'request.inputs',
                                              'request.source_encoding',
                                              'request.chain',
                                              'request.destination_encoding',
                                              'request.topology',
                                              'request.axioms',
                                              'request.target_constraints',
                                              'request.reference_set',
                                              'plan',
                                              'plan.artifacts',
                                              'plan.axiom_diagnostic',
                                              'preparation',
                                              'scope.admission',
                                              'scope.dispatch',
                                              'scope.outcome',
                                              'scope.summary',
                                              'scope.completion',
                                              'target',
                                              'target.readback',
                                              'raw_business_packet']},
                    'produced_diagnostics': {'type': 'array',
                                             'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterRecord'},
                                             'minItems': 0,
                                             'maxItems': 1},
                    'pending_diagnostic': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PendingPlannerEmitterDiagnostic'},
                                                     {'type': 'null'}]}},
 'EmitterResult': {'request': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/EmitterRequest'},
                   'binding': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterBinding'},
                   'status': {'type': 'string',
                              'enum': ['SUCCEEDED', 'NO_OP', 'FAILED', 'PARTIAL', 'UNKNOWN']},
                   'actual_effects': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
                   'outcomes': {'type': 'array',
                                'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/MemoryTargetReceipt'},
                                'minItems': 0,
                                'maxItems': 23},
                   'produced_diagnostics': {'type': 'array',
                                            'items': {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterRecord'},
                                            'minItems': 0,
                                            'maxItems': 47},
                   'pending_summary': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PendingPlannerEmitterDiagnostic'},
                                                 {'type': 'null'}]},
                   'failure_code': {'anyOf': [{'type': 'string',
                                               'enum': ['PREPARATION_FOREIGN',
                                                        'PREPARATION_USED',
                                                        'PREPARATION_LIMIT',
                                                        'EMITTER_BUSY',
                                                        'PLAN_INCOMPLETE',
                                                        'PLAN_BINDING_MISMATCH',
                                                        'AXIOM_FAILURE_NOT_AUTHORIZED',
                                                        'TARGET_CONSTRAINT_UNSATISFIED',
                                                        'CAPTURE_ADMISSION_UNCONFIRMED',
                                                        'DISPATCH_UNCONFIRMED',
                                                        'COMMAND_CANCELLED',
                                                        'DOCUMENT_CONFLICT',
                                                        'TARGET_RESOURCE_LIMIT',
                                                        'TARGET_BUSY',
                                                        'TARGET_STALE_REVISION',
                                                        'TARGET_VERSION_EXHAUSTED',
                                                        'TARGET_RECEIPT_FOREIGN',
                                                        'TARGET_READBACK_MISMATCH',
                                                        'TARGET_INTERNAL_FAILURE',
                                                        'TARGET_EFFECT_UNKNOWN',
                                                        'OUTCOME_CAPTURE_UNCONFIRMED',
                                                        'SUMMARY_CAPTURE_UNCONFIRMED',
                                                        'COMPLETION_UNCONFIRMED',
                                                        'RAW_BUSINESS_LIMIT']},
                                              {'type': 'null'}]}},
 'PlannerEmitterCaptureReceipt': {'operation_reference': {'type': 'string',
                                                          'minLength': 1,
                                                          'maxLength': 160,
                                                          'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                  'status': {'type': 'string',
                                             'enum': ['CONFIRMED', 'REJECTED', 'NOT_CONFIRMED']},
                                  'result': {'oneOf': [{'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerResult'},
                                                       {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerFailure'},
                                                       {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/EmitterResult'}]},
                                  'confirmed_records': {'type': 'array',
                                                        'items': {'type': 'string',
                                                                  'minLength': 1,
                                                                  'maxLength': 256,
                                                                  'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                                        'minItems': 0,
                                                        'maxItems': 47},
                                  'attempted_record': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterRecord'},
                                                                 {'type': 'null'}]},
                                  'completion': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_reference_diagnostic_bundle_schema.json#/$defs/DiagnosticsCompletionReceipt'},
                                                           {'type': 'null'}]},
                                  'final_observation': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_module_capture_schema.json#/$defs/ModuleFinalObservationReceipt'},
                                                                  {'type': 'null'}]},
                                  'failure_code': {'anyOf': [{'type': 'string',
                                                              'enum': ['SOURCE_UNSUPPORTED',
                                                                       'PROFILE_UNAVAILABLE',
                                                                       'ORIGIN_REJECTED',
                                                                       'ORIGIN_UNPARSED',
                                                                       'SOURCE_NOT_NORMALIZED',
                                                                       'DEPENDENCY_FOREIGN',
                                                                       'DEPENDENCY_MISMATCH',
                                                                       'CHAIN_NOT_COMPLETE',
                                                                       'FINAL_DIAGNOSIS_MISMATCH',
                                                                       'SUBJECT_PROVENANCE_MISMATCH',
                                                                       'TARGET_CONSTRAINT_UNSATISFIED',
                                                                       'REFERENCE_COLLISION',
                                                                       'RAW_BUSINESS_LIMIT',
                                                                       'PREPARATION_FOREIGN',
                                                                       'PREPARATION_USED',
                                                                       'PREPARATION_LIMIT',
                                                                       'EMITTER_BUSY',
                                                                       'PLAN_INCOMPLETE',
                                                                       'PLAN_BINDING_MISMATCH',
                                                                       'AXIOM_FAILURE_NOT_AUTHORIZED',
                                                                       'CAPTURE_ADMISSION_UNCONFIRMED',
                                                                       'DISPATCH_UNCONFIRMED',
                                                                       'COMMAND_CANCELLED',
                                                                       'DOCUMENT_CONFLICT',
                                                                       'TARGET_RESOURCE_LIMIT',
                                                                       'TARGET_BUSY',
                                                                       'TARGET_STALE_REVISION',
                                                                       'TARGET_VERSION_EXHAUSTED',
                                                                       'TARGET_RECEIPT_FOREIGN',
                                                                       'TARGET_READBACK_MISMATCH',
                                                                       'TARGET_INTERNAL_FAILURE',
                                                                       'TARGET_EFFECT_UNKNOWN',
                                                                       'OUTCOME_CAPTURE_UNCONFIRMED',
                                                                       'SUMMARY_CAPTURE_UNCONFIRMED',
                                                                       'COMPLETION_UNCONFIRMED',
                                                                       'MODULE_PRODUCER_FOREIGN',
                                                                       'MODULE_PRODUCER_DUPLICATE',
                                                                       'MODULE_PRODUCER_BINDING_MISMATCH',
                                                                       'MODULE_PRODUCER_UNSUPPORTED',
                                                                       'MODULE_CONTEXT_REJECTED',
                                                                       'MODULE_ORIGIN_REJECTED',
                                                                       'MODULE_RESULT_REJECTED',
                                                                       'MODULE_RESERVATION_REFUSED',
                                                                       'MODULE_RAW_PACKET_LIMIT',
                                                                       'MODULE_CAPTURE_REJECTED',
                                                                       'MODULE_CAPTURE_UNCONFIRMED',
                                                                       'MODULE_COMPLETION_MISSING',
                                                                       'MODULE_COMPLETION_REJECTED',
                                                                       'MODULE_FINAL_OBSERVATION_REJECTED',
                                                                       'MODULE_REQUIRED_RECORD_MISSING',
                                                                       'MODULE_SCOPE_FOREIGN',
                                                                       'MODULE_REPLAY_REFUSED']},
                                                             {'type': 'null'}]}},
 'GenerationDependencyCaptureReceipt': {'operation_reference': {'type': 'string',
                                                                'minLength': 1,
                                                                'maxLength': 160,
                                                                'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                        'status': {'type': 'string',
                                                   'enum': ['CONFIRMED', 'REJECTED', 'NOT_CONFIRMED']},
                                        'result': {'oneOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmEncodingResult'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionResolutionResult'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/TransitionApplicationResult'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmTransitionFailure'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/TransitionChainResult'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/TransitionChainFailure'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/TopologyResult'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/TopologyFailure'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomEvaluationResult'},
                                                             {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/AxiomEvaluationFailure'}]},
                                        'confirmed_records': {'type': 'array',
                                                              'items': {'type': 'string',
                                                                        'minLength': 1,
                                                                        'maxLength': 256,
                                                                        'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                                              'minItems': 0,
                                                              'maxItems': 17},
                                        'attempted_record': {'anyOf': [{'oneOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_realm_transition_schema.json#/$defs/RealmTransitionRecord'},
                                                                                  {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/ChainRecord'},
                                                                                  {'$ref': 'https://ywe.local/schemas/m3_generation_topology_axiom_schema.json#/$defs/GenerationDiagnosticRecord'}]},
                                                                       {'type': 'null'}]},
                                        'completion': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_reference_diagnostic_bundle_schema.json#/$defs/DiagnosticsCompletionReceipt'},
                                                                 {'type': 'null'}]},
                                        'final_observation': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_module_capture_schema.json#/$defs/ModuleFinalObservationReceipt'},
                                                                        {'type': 'null'}]},
                                        'failure_code': {'anyOf': [{'type': 'string',
                                                                    'enum': ['MODULE_PRODUCER_FOREIGN',
                                                                             'MODULE_PRODUCER_DUPLICATE',
                                                                             'MODULE_PRODUCER_BINDING_MISMATCH',
                                                                             'MODULE_PRODUCER_UNSUPPORTED',
                                                                             'MODULE_CONTEXT_REJECTED',
                                                                             'MODULE_ORIGIN_REJECTED',
                                                                             'MODULE_RESULT_REJECTED',
                                                                             'MODULE_RESERVATION_REFUSED',
                                                                             'MODULE_RAW_PACKET_LIMIT',
                                                                             'MODULE_CAPTURE_REJECTED',
                                                                             'MODULE_CAPTURE_UNCONFIRMED',
                                                                             'MODULE_COMPLETION_MISSING',
                                                                             'MODULE_COMPLETION_REJECTED',
                                                                             'MODULE_FINAL_OBSERVATION_REJECTED',
                                                                             'MODULE_REQUIRED_RECORD_MISSING',
                                                                             'MODULE_SCOPE_FOREIGN',
                                                                             'MODULE_REPLAY_REFUSED']},
                                                                   {'type': 'null'}]}},
 'GenerationRunReceipt': {'operation_reference': {'type': 'string',
                                                  'minLength': 1,
                                                  'maxLength': 128,
                                                  'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                          'status': {'type': 'string', 'enum': ['READY', 'REFUSED', 'NOT_CONFIRMED']},
                          'last_stage': {'type': 'string',
                                         'enum': ['ORIGIN',
                                                  'SOURCE_ENCODING',
                                                  'CHAIN',
                                                  'FINAL_DIAGNOSIS',
                                                  'DESTINATION_ENCODING',
                                                  'TOPOLOGY',
                                                  'AXIOMS',
                                                  'PLANNER']},
                          'last_observation': {'oneOf': [{'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/StateDiagnosis'},
                                                         {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/ClassificationEvidenceFailure'},
                                                         {'$ref': 'https://ywe.local/schemas/m3_generation_state_schema.json#/$defs/DiagnosticCaptureFailure'},
                                                         {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/GenerationDependencyCaptureReceipt'},
                                                         {'$ref': 'https://ywe.local/schemas/m3_planner_emitter_schema.json#/$defs/PlannerEmitterCaptureReceipt'}]},
                          'last_origin_completion': {'anyOf': [{'$ref': 'https://ywe.local/schemas/m3_reference_diagnostic_bundle_schema.json#/$defs/DiagnosticsCompletionReceipt'},
                                                               {'type': 'null'}]},
                          'completed_operation_references': {'type': 'array',
                                                             'items': {'type': 'string',
                                                                       'minLength': 1,
                                                                       'maxLength': 256,
                                                                       'pattern': '^[A-Za-z0-9][A-Za-z0-9._:/-]*$'},
                                                             'minItems': 0,
                                                             'maxItems': 7}}}

WIRE_HEADERS = {'ReferenceManifestDocument': {'schema_version': '1.0.0'},
 'PlannerResult': {'schema_version': '1.0.0', 'packet_kind': 'planner_result'},
 'PlannerFailure': {'schema_version': '1.0.0', 'packet_kind': 'planner_failure'},
 'EmitterResult': {'schema_version': '1.0.0', 'packet_kind': 'emitter_result'},
 'PlannerEmitterCaptureReceipt': {'schema_version': '1.0.0',
                                  'packet_kind': 'planner_emitter_capture_receipt'},
 'GenerationRunReceipt': {'schema_version': '1.0.0', 'packet_kind': 'generation_run_receipt'}}


_EXTERNAL_TYPES_CACHE = None


def _external_types():
    global _EXTERNAL_TYPES_CACHE
    if _EXTERNAL_TYPES_CACHE is not None:
        return _EXTERNAL_TYPES_CACHE
    from . import diagnostics_values as dv
    from . import diagnostic_module_values as mv
    names = ("AshState", "CanonicalAshBinding", "ProfileSourceBinding", "ValidityProfile",
             "UnavailableValidityProfileEvidence", "AvailableProfileBinding", "UnavailableProfileBinding",
             "AssessmentBinding", "CoordinateObservation", "InputEvidence", "RejectedCandidateEvidence",
             "OrbitInfo", "StateValidityDiagnostic", "DiagnosticEnvelope", "DiagnosticEmission",
             "StateDiagnosis", "DiagnosisValidation", "ClassificationEvidenceFailure", "DiagnosticCaptureFailure")
    receipts = (dv.DiagnosticsCompletionReceipt, dv.DiagnosticsHealth, dv.MissingCoverage,
                dv.RetentionBoundary, dv.DiagnosticCounterState, mv.ModuleFinalObservationReceipt)
    _EXTERNAL_TYPES_CACHE = tuple(getattr(state, name) for name in names) + rt.OWNED_TYPES + gen.WIRE_TYPES + receipts
    return _EXTERNAL_TYPES_CACHE


def _resolve(reference):
    name = reference.rsplit("/", 1)[-1]
    if name == "ProfileBinding":
        return (state.AvailableProfileBinding, state.UnavailableProfileBinding)
    for cls in (*WIRE_TYPES, *_external_types()):
        if cls.__name__ == name:
            return (cls,)
    _fail("value", "VALUE_CORRUPT")


def _equal(actual, expected, field="value"):
    if actual != expected:
        _fail(field, "VALUE_CORRUPT")


def _check(value, spec, field):
    if "$ref" in spec:
        reference_name = spec["$ref"].rsplit("/", 1)[-1]
        if reference_name == "Identifier":
            _ref(value, field)
        elif reference_name == "LineText":
            if (type(value) is not str or not 1 <= len(value) <= 512 or
                    any(0xD800 <= ord(char) <= 0xDFFF for char in value) or
                    re.search(r"[\r\n\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]", value)):
                _fail(field)
        else:
            _exact(value, _resolve(spec["$ref"]), field)
    for keyword in ("anyOf", "oneOf"):
        if keyword in spec:
            matches = 0
            for branch in spec[keyword]:
                try:
                    _check(value, branch, field)
                    matches += 1
                except PlannerEmitterContractError:
                    pass
            if matches == 0 or keyword == "oneOf" and matches != 1:
                _fail(field)
    for branch in spec.get("allOf", ()):
        _check(value, branch, field)
    if "properties" in spec:
        for name, child in spec["properties"].items():
            _check(object.__getattribute__(value, name), child, field)
    if "const" in spec:
        target = spec["const"]
        if type(target) is str:
            _exact(value, str, field)
            _equal(value, target, field)
        elif type(target) is dict:
            _exact(value, state.CanonicalAshBinding, field)
            _equal(state.CanonicalAshBinding.to_record(value), target, field)
        elif type(target) is list:
            _exact(value, tuple, field)
            _equal(value, tuple((row["path"], row["sha256"]) for row in target), field)
        else:
            _equal(value, target, field)
    if "enum" in spec:
        _exact(value, str, field)
        if value not in spec["enum"]:
            _fail(field)
    kind = spec.get("type")
    if kind == "null":
        if value is not None:
            _fail(field)
    elif kind == "boolean":
        _exact(value, bool, field)
    elif kind == "integer":
        _exact(value, int, field)
        if not spec.get("minimum", -(1 << 63)) <= value <= spec.get("maximum", (1 << 64)-1):
            _fail(field)
    elif kind == "string":
        _exact(value, str, field)
        if (not spec.get("minLength", 0) <= len(value) <= spec.get("maxLength", 32768) or
                any(0xD800 <= ord(char) <= 0xDFFF for char in value)):
            _fail(field)
        if "pattern" in spec and re.fullmatch(spec["pattern"], value, re.ASCII) is None:
            _fail(field)
    elif kind == "array":
        _exact(value, tuple, field)
        if not spec.get("minItems", 0) <= len(value) <= spec.get("maxItems", 1024):
            _fail(field)
        for child in value:
            _check(child, spec["items"], field)


def _clean(value):
    """Copy known declared fields, removing instance serializer overrides."""
    kind = type(value)
    if value is None or _is(value, (str, int, bool, float)):
        return value
    if kind is tuple:
        return tuple(_clean(child) for child in value)
    if kind is frozenset:
        return frozenset(_clean(child) for child in value)
    result = object.__new__(kind)
    for field in fields(kind):
        object.__setattr__(result, field.name, _clean(object.__getattribute__(value, field.name)))
    return result


def _walk(value, active, seen):
    kind = type(value)
    if value is None or kind is bool:
        return
    if kind is str:
        # Reused malformed N1 previews are observations, not newly authored prose.
        if len(value) > 65536:
            _fail()
        return
    if kind is int:
        if value.bit_length() > 64:
            _fail()
        return
    if kind is float:
        if not math.isfinite(value):
            _fail()
        return
    identity = id(value)
    if identity in active or len(active) > 64:
        _fail("value", "VALUE_CORRUPT")
    own = _is(value, WIRE_TYPES)
    external = not own and _is(value, _external_types())
    if not own and not external and kind is not tuple and kind is not frozenset:
        _fail()
    if identity in seen:
        return
    active.add(identity)
    try:
        if kind is tuple or kind is frozenset:
            if len(value) > 2048:
                _fail()
            for child in value:
                _walk(child, active, seen)
        else:
            for field in fields(kind):
                _walk(object.__getattribute__(value, field.name), active, seen)
            if own:
                for name, spec in FIELD_SCHEMAS[kind.__name__].items():
                    _check(object.__getattribute__(value, name), spec, kind.__name__ + "." + name)
                _coherent(value)
            elif _is(value, rt.OWNED_TYPES):
                rt.revalidate_value(value)
            elif _is(value, gen.WIRE_TYPES):
                gen.revalidate_value(value)
            else:
                clean = _clean(value)
                kind.__post_init__(clean)
                if kind is state.StateDiagnosis:
                    from .state_model import StateModel
                    model = StateModel(clean.profile_binding, clean.source_binding, None)
                    StateModel.validate_diagnosis(model, clean)
        seen.add(identity)
    except (AttributeError, TypeError, RecursionError):
        _fail("value", "VALUE_CORRUPT")
    finally:
        active.remove(identity)


def revalidate_value(value):
    _walk(value, set(), set())
    return value


def _model_bindings(model):
    from .state_model import StateModel
    _exact(model,StateModel,"model")
    canonical=StateModel.canonical_binding.fget(model)
    profile=StateModel.profile_binding.fget(model)
    _exact(canonical,state.CanonicalAshBinding,"model.canonical_binding")
    _exact(profile,(state.AvailableProfileBinding,state.UnavailableProfileBinding),"model.profile_binding")
    revalidate_value(canonical);revalidate_value(profile)
    return canonical,profile


def _record(value):
    kind = type(value)
    if value is None or _is(value, (str, int, bool, float)):
        return value
    if kind is tuple:
        return [_record(child) for child in value]
    if kind is frozenset:
        return [_record(child) for child in sorted(value, key=lambda entry: entry.bits)]
    if _is(value, WIRE_TYPES):
        result = {field.name: _record(object.__getattribute__(value, field.name)) for field in fields(kind)}
        if kind is PlannerEmitterBinding:
            result["contract_pins"] = [{"path": path, "sha256": digest} for path, digest in value.contract_pins]
        result.update(WIRE_HEADERS.get(kind.__name__, {}))
        return result
    if _is(value, rt.OWNED_TYPES):
        return json.loads(rt.canonical_bytes(value))
    if _is(value, gen.WIRE_TYPES):
        return json.loads(gen.canonical_bytes(value))
    clean = _clean(value)
    return kind.to_record(clean)


def _tokens(value, limit):
    _exact(value, WIRE_TYPES)
    _exact(limit, int, "limit")
    if not 1 <= limit <= RAW_BUSINESS_LIMIT:
        _fail("limit")
    revalidate_value(value)
    total = 0
    for token in json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                                  allow_nan=False).iterencode(_record(value)):
        chunk = token.encode("ascii")
        total += len(chunk)
        if total > limit:
            _fail("raw_business_packet", "RAW_BUSINESS_LIMIT")
        yield chunk


def canonical_bytes(value, *, limit=RAW_BUSINESS_LIMIT):
    return b"".join(_tokens(value, limit))


def raw_business_size(value, limit=RAW_BUSINESS_LIMIT):
    try:
        return sum(len(chunk) for chunk in _tokens(value, limit))
    except PlannerEmitterContractError as error:
        if error.code == "RAW_BUSINESS_LIMIT":
            return limit + 1
        raise


def wire_schema(value):
    _exact(value, WIRE_TYPES)
    revalidate_value(value)
    return SCHEMA_ID


def _digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


_RESULT_MARKER = object()


def _seal_result(value, owner):
    _exact(value, RESULT_TYPES)
    digest = _digest(value)
    object.__setattr__(value, "_issuer", owner)
    object.__setattr__(value, "_cookie", (_RESULT_MARKER, owner, value))
    object.__setattr__(value, "_self_identity", value)
    object.__setattr__(value, "_wire_digest", digest)
    return value


def _result_is_owned(value, owner, kinds):
    if not _is(value, kinds):
        return False
    try:
        cookie = object.__getattribute__(value, "_cookie")
        if (type(cookie) is not tuple or len(cookie) != 3 or cookie[0] is not _RESULT_MARKER or
                cookie[1] is not owner or cookie[2] is not value or
                object.__getattribute__(value, "_issuer") is not owner or
                object.__getattribute__(value, "_self_identity") is not value):
            return False
        issued_digest = object.__getattribute__(value, "_wire_digest")
        return type(issued_digest) is str and _digest(value) == issued_digest
    except (PlannerEmitterContractError, state.StateContractError, rt.RealmTransitionContractError,
            gen.GenerationContractError, AttributeError, TypeError, ValueError):
        return False


def _warnings(diagnostic):
    flags = (diagnostic.a1_relational_existence, diagnostic.a2_structural_compressibility,
             diagnostic.a3_multi_scale_persistence, diagnostic.a4_energetic_cost_of_erasure,
             diagnostic.a5_self_reference_for_consciousness)
    return tuple("A" + str(index+1) + "_FAILED" for index, passed in enumerate(flags) if not passed)


def _coherent(value):
    kind = type(value)
    if kind is RoleAssignment:
        role = "root" if value.node_path == "r" else ("continuation", "positive", "negative")[int(value.node_path[-1])]
        _equal((value.role_reference, value.role_kind), ("role:"+role, role.upper()))
        _equal(value.ordinal, int(value.node_path[1:], 3) if len(value.node_path) > 1 else 0)
    elif kind is ChainStep:
        selected = value.selected_definition
        _equal(value.selection_observation, rt.TransitionSelectionObservation(value.selection, selected.transition_id,
               selected.codeword, "SELECTED", None))
        _equal(value.applicability_observation.source_state, value.input_state)
        _equal(value.applicability_observation.transition_id, selected.transition_id)
        _equal(value.applicability_observation.codeword, selected.codeword)
        if not value.applicability_observation.is_applicable:
            _fail("ChainStep.applicability_observation")
        _equal(value.transformation_observation.source_state, value.input_state)
        _equal(value.transformation_observation.transition_id, selected.transition_id)
        _equal(value.transformation_observation.codeword, selected.codeword)
        _equal(len(set(value.record_references)), 3)
    elif kind is ChainRecord:
        _equal(value.record_reference, value.emission.diagnostic_reference)
        expected = {"VALID_SOURCE": rt.RealmTransitionGate, "SELECTION": rt.TransitionSelectionObservation,
                    "APPLICABILITY": rt.TransitionApplicabilityObservation, "TRANSFORMATION": rt.TransitionTransformationObservation}
        _exact(value.payload, expected[value.phase])
        rules = {"VALID_SOURCE": ("ASH-STATE-VALIDITY-001", "ASH-CODEWORD-REGISTRY-001"),
                 "SELECTION": rt.PHASE_RULES["SELECTION"], "APPLICABILITY": rt.PHASE_RULES["APPLICABILITY"],
                 "TRANSFORMATION": ("ASH-CODEWORD-TRANSFORMATION-001", "ASH-STATE-VALIDITY-001")}
        _equal(value.emission.envelope.rule_ids, rules[value.phase])
        failed = (not value.payload.is_valid if value.phase == "VALID_SOURCE" else
                  value.payload.status == "REFUSED" if value.phase == "SELECTION" else
                  not value.payload.is_applicable if value.phase == "APPLICABILITY" else
                  not value.payload.target_diagnosis.is_valid)
        _equal(value.emission.envelope.disposition, "BLOCKED" if failed else "RESOLVED")
    elif kind is ChainEnvelope or kind is PlannerEmitterEnvelope:
        if value.parent_diagnostic_reference == value.chain_root_reference == value.subject_reference:
            _fail("envelope.subject_reference")
        if len(json.dumps(_record(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")) > TEN_BYTE_LIMIT:
            _fail("envelope", "RAW_BUSINESS_LIMIT")
    elif kind is TransitionChainResult or kind is TransitionChainFailure:
        _chain_coherence(value)
    elif kind is ReferenceManifestDocument:
        if value.page_index >= value.page_count:
            _fail("ReferenceManifestDocument.page_index")
        _equal(value.source_state, value.source_identity.state_signature)
        _equal(value.destination_state, value.destination_identity.state_signature)
        _equal(value.axiom_subject.state.signature, value.destination_state)
        _equal(value.warnings, _warnings(value.axiom_diagnostic))
        if len(set(value.dependency_operation_references)) != 5:
            _fail("ReferenceManifestDocument.dependency_operation_references")
        for row in value.rows:
            _equal((row.node.node_id, row.node.path_token, row.node.ordinal),
                   (row.assignment.node_reference, row.assignment.node_path, row.assignment.ordinal))
    elif kind is ArtifactDescription:
        content = canonical_bytes(value.document)
        _equal(value.content_sha256, hashlib.sha256(content).hexdigest())
        _equal(value.content_byte_count, len(content))
        _equal(value.page_index, value.document.page_index)
        _equal(value.name, "ywe-"+value.document.project_name+"-manifest-"+f"{value.page_index:03d}"+".json")
        present = tuple(row.assignment.role_reference for row in value.document.rows)
        _equal(value.role_references, tuple(role for role in ("role:root", "role:continuation", "role:positive", "role:negative") if role in present))
    elif kind is MaterializedDocument:
        content = value.content_ascii.encode("ascii")
        _equal(value.actual_sha256, hashlib.sha256(content).hexdigest())
        _equal(value.actual_byte_count, len(content))
    elif kind is TargetSnapshot:
        _equal(value.documents, tuple(sorted(value.documents, key=lambda row: row.name)))
        _equal(len({row.name for row in value.documents}), len(value.documents))
        _equal(value.actual_byte_count, sum(row.actual_byte_count for row in value.documents))
        if len(value.documents) > value.configuration.max_documents or value.actual_byte_count > value.configuration.max_bytes:
            _fail("TargetSnapshot.documents")
        if any(row.creation_revision > value.revision for row in value.documents):
            _fail("TargetSnapshot.revision")
    elif kind is MemoryTargetReceipt:
        if value.actual_status == "UNKNOWN":
            _equal((value.actual_effects, value.readback_assurance), (None, "UNAVAILABLE"))
        elif value.actual_status == "SUCCEEDED":
            _equal(value.actual_effects, True)
            _equal((value.expected_sha256, value.expected_byte_count), (value.observed_sha256, value.observed_byte_count))
            if value.target_revision_before is None or value.target_revision_after != value.target_revision_before+1:
                _fail("MemoryTargetReceipt.target_revision_after")
        elif value.actual_status == "NO_EFFECT":
            _equal(value.actual_effects, False)
            _equal(value.target_revision_before, value.target_revision_after)
            _equal((value.expected_sha256, value.expected_byte_count), (value.observed_sha256, value.observed_byte_count))
    elif kind is EmissionSummaryDiagnostic:
        if not value.confirmed_artifact_count <= value.attempted_artifact_count <= value.requested_artifact_count:
            _fail("EmissionSummaryDiagnostic.attempted_artifact_count")
    elif kind is ReferenceGenerationPlan:
        _plan_coherence(value)
    elif kind is PlannerResult:
        _equal(value.binding, value.plan.binding)
        _equal(value.plan.inputs, value.request.inputs)
        request, plan = value.request, value.plan
        _equal(plan.plan_reference, request.operation_reference+":plan")
        _equal(plan.normalized_state, request.origin_diagnosis.parsed_state)
        _equal(plan.source_state_identity, request.source_encoding.identity)
        _equal(plan.destination_state_identity, request.destination_encoding.identity)
        _equal(plan.topology_nodes, request.topology.nodes)
        _equal(plan.axiom_subject, request.axioms.request.subject)
        _equal(plan.axiom_diagnostic, request.axioms.axiom_diagnostic)
        _equal(plan.target_constraints, request.target_constraints)
        _equal((plan.metadata.request_reference,plan.metadata.source_diagnosis_reference,
                plan.metadata.destination_diagnosis_reference,plan.metadata.chain_operation_reference,
                plan.metadata.topology_operation_reference,plan.metadata.axiom_operation_reference),
               (request.operation_reference,request.origin_diagnosis.assessment_binding.diagnosis_reference,
                request.final_origin_diagnosis.assessment_binding.diagnosis_reference,request.chain.operation_reference,
                request.topology.request.request_reference,request.axioms.request.request_reference))
        _equal(value.produced_diagnostics[0].payload.outcome, "COMPLETE")
    elif kind is PlannerEmitterRecord:
        plan_record = type(value.payload) is PlanDiagnostic
        _equal(value.envelope.diagnostic_kind, "GENERATION_PLAN" if plan_record else "ARTIFACT_EMISSION")
        _equal(value.envelope.rule_ids, ("ASH-GENERATION-PLAN-001", "ASH-GENERATION-BOUNDARY-001") if plan_record else
               ("ASH-GENERATION-TRACEABILITY-001", "ASH-GENERATION-PLANFIDELITY-001", "ASH-GENERATION-EMISSION-001"))
    elif kind is PlannerFailure:
        if not value.produced_diagnostics and value.pending_diagnostic is None:
            _fail("PlannerFailure.produced_diagnostics")
    elif kind is EmitterResult:
        _emission_coherence(value)
    elif kind is PlannerEmitterCaptureReceipt or kind is GenerationDependencyCaptureReceipt:
        if kind is PlannerEmitterCaptureReceipt:
            reference=value.result.request.operation_reference
            records=value.result.produced_diagnostics
            refs=tuple(record.diagnostic_reference for record in records)
        elif _is(value.result,(TransitionChainResult,TransitionChainFailure)) or _is(value.result,rt.RESULT_TYPES):
            reference=value.result.operation_reference
            refs=tuple(record.record_reference for record in value.result.constructed_records)
        else:
            reference=value.result.request.request_reference
            refs=tuple(record.diagnostic_reference for record in value.result.produced_diagnostics)
        _equal(value.operation_reference,reference)
        _equal(value.confirmed_records,refs[:len(value.confirmed_records)])
        if value.status=="CONFIRMED":
            _equal(value.confirmed_records,refs)
            _equal((value.attempted_record,value.failure_code),(None,None))
            if (value.completion is None or value.completion.status!="COMPLETE" or
                    value.completion.operation_reference!=reference or value.final_observation is None or
                    value.final_observation.status!="CONFIRMED" or value.final_observation.operation_reference!=reference):
                _fail("capture.completion")
    elif kind is GenerationRunReceipt:
        if len(set(value.completed_operation_references)) != len(value.completed_operation_references):
            _fail("GenerationRunReceipt.completed_operation_references")
        if value.status == "READY":
            _equal(value.last_stage, "PLANNER")
            _exact(value.last_observation, PlannerEmitterCaptureReceipt)
            _exact(value.last_observation.result, PlannerResult)
            _equal(value.last_observation.status, "CONFIRMED")
            _equal(value.completed_operation_references,tuple(value.operation_reference+suffix for suffix in
                   (":source",":chain",":final",":destination",":topology",":axioms",":planner")))


def _emission_coherence(value):
    request=value.request
    _equal(value.binding,request.plan.binding)
    _equal(request.target_configuration.policy_binding,value.binding.policy_binding)
    artifacts=request.plan.artifacts
    if len(value.outcomes)>len(artifacts):_fail("EmitterResult.outcomes")
    for artifact,outcome in zip(artifacts,value.outcomes):
        _equal((outcome.operation_reference,outcome.artifact_reference,outcome.plan_element_reference,
                outcome.target_reference,outcome.expected_sha256,outcome.expected_byte_count),
               (request.operation_reference,artifact.artifact_reference,artifact.plan_element_reference,
                request.target_configuration.target_reference,artifact.content_sha256,artifact.content_byte_count))
    expected_effects=True if any(row.actual_effects is True for row in value.outcomes) else None if any(row.actual_effects is None for row in value.outcomes) else False
    _equal(value.actual_effects,expected_effects)
    if value.status=="UNKNOWN" and not any(row.actual_effects is None for row in value.outcomes):
        _fail("EmitterResult.status")
    if value.status=="NO_OP":
        _equal((value.actual_effects,len(value.outcomes),value.failure_code),(False,len(artifacts),None))
        if any(row.actual_status!="NO_EFFECT" for row in value.outcomes):_fail("EmitterResult.status")
    if value.status=="SUCCEEDED":
        _equal((value.actual_effects,len(value.outcomes),value.failure_code),(True,len(artifacts),None))
        if any(row.actual_status not in ("SUCCEEDED","NO_EFFECT") for row in value.outcomes):_fail("EmitterResult.status")
    if value.status=="PARTIAL":_equal(value.actual_effects,True)
    if value.status=="FAILED":_equal(value.actual_effects,False)
    records=value.produced_diagnostics
    if not records:
        if value.pending_summary is None or value.outcomes:_fail("EmitterResult.produced_diagnostics")
        return
    from .generation_planner import record_reference
    root=records[0].envelope
    parent=root.chain_root_reference
    previous_severity=root.severity
    dispatches=0;observations=0;summary=None
    for ordinal,record in enumerate(records):
        env,payload=record.envelope,record.payload
        _equal((env.subject_reference,env.chain_root_reference,env.parent_diagnostic_reference),
               (root.subject_reference,root.chain_root_reference,parent))
        if SEVERITIES.index(env.severity)<SEVERITIES.index(previous_severity):_fail("EmitterResult.produced_diagnostics")
        parent,previous_severity=record.diagnostic_reference,env.severity
        if type(payload) is EmissionDispatchDiagnostic:
            if observations!=dispatches or dispatches>=len(artifacts):_fail("EmitterResult.produced_diagnostics")
            artifact=artifacts[dispatches]
            _equal(record.diagnostic_reference,record_reference(request.operation_reference,2*dispatches))
            _equal((payload.operation_reference,payload.plan_reference,payload.artifact_reference,payload.plan_element_reference,
                    payload.artifact_index,payload.expected_sha256,payload.expected_byte_count,payload.target_reference),
                   (request.operation_reference,request.plan.plan_reference,artifact.artifact_reference,artifact.plan_element_reference,
                    dispatches,artifact.content_sha256,artifact.content_byte_count,request.target_configuration.target_reference))
            dispatches+=1
        elif type(payload) is EmissionOutcomeDiagnostic:
            if dispatches!=observations+1 or observations>=len(value.outcomes):_fail("EmitterResult.produced_diagnostics")
            _equal(record.diagnostic_reference,record_reference(request.operation_reference,2*observations+1))
            _equal(payload.dispatch_reference,record_reference(request.operation_reference,2*observations))
            _equal(payload.actual_receipt,value.outcomes[observations]);observations+=1
        elif type(payload) is EmissionSummaryDiagnostic:
            if ordinal!=len(records)-1 or summary is not None:_fail("EmitterResult.produced_diagnostics")
            summary=payload
            _equal(record.diagnostic_reference,record_reference(request.operation_reference,2*len(artifacts)))
            _equal((payload.operation_reference,payload.plan_reference,payload.requested_artifact_count,
                    payload.attempted_artifact_count,payload.confirmed_artifact_count,payload.actual_effects),
                   (request.operation_reference,request.plan.plan_reference,len(artifacts),len(value.outcomes),
                    sum(row.actual_status in ("SUCCEEDED","NO_EFFECT") for row in value.outcomes),value.actual_effects))
        else:_fail("EmitterResult.produced_diagnostics")
    if observations!=len(value.outcomes) or summary is None:_fail("EmitterResult.produced_diagnostics")


def _chain_coherence(value):
    _equal(value.origin_validation.submitted_diagnosis, value.origin)
    _equal(value.binding.canonical_binding, value.origin.source_binding)
    _equal(value.binding.profile_binding, value.origin.profile_binding)
    records = value.constructed_records
    _equal(records[0].phase, "VALID_SOURCE")
    _equal(records[0].payload, rt.RealmTransitionGate(value.origin.assessment_binding.assessment_reference,
           value.origin_validation.status, value.origin.state_validity_diagnostic.admissibility_status,
           value.origin.state_validity_diagnostic.is_valid))
    current = value.origin.parsed_state
    from .state_model import StateModel
    model = StateModel(value.binding.profile_binding, value.binding.canonical_binding, None)
    root = value.origin.emitted_diagnostics[0]
    previous = root.diagnostic_reference
    severity = root.envelope.severity
    for index, record in enumerate(records):
        _equal(record.record_reference, rt.record_reference(value.operation_reference, index))
        envelope = record.emission.envelope
        _equal((envelope.subject_reference, envelope.chain_root_reference, envelope.parent_diagnostic_reference),
               (root.envelope.subject_reference, root.envelope.chain_root_reference, previous))
        if SEVERITIES.index(envelope.severity) < SEVERITIES.index(severity):
            _fail("TransitionChainResult.constructed_records")
        previous, severity = record.record_reference, envelope.severity
    for index, step in enumerate(value.steps):
        _equal((step.ordinal, step.input_state, step.selection), (index, current, value.selections[index]))
        _equal(step.source_proof_reference, root.diagnostic_reference if index == 0 else value.steps[index-1].record_references[-1])
        _equal(step.record_references, tuple(record.record_reference for record in records[1+3*index:4+3*index]))
        _equal(tuple(record.payload for record in records[1+3*index:4+3*index]),
               (step.selection_observation, step.applicability_observation, step.transformation_observation))
        mask = step.selected_definition.applicability_mask[int(step.input_state.signature, 2)]
        _equal(mask, "1")
        current = step.transformation_observation.candidate
        _equal(step.transformation_observation.target_diagnosis, StateModel.inspect_state(model, current))
        if index < len(value.steps)-1 and not step.transformation_observation.target_diagnosis.is_valid:
            _fail("TransitionChainResult.steps")
    _equal(value.last_candidate, current)
    if type(value) is TransitionChainResult:
        _equal((len(value.steps), len(records)), (len(value.selections), 1+3*len(value.steps)))
        diagnostic = value.steps[-1].transformation_observation.target_diagnosis if value.steps else value.origin.state_validity_diagnostic
        _equal(value.final_target_diagnostic, diagnostic)
        if not diagnostic.is_valid or not records[0].payload.is_valid:
            _fail("TransitionChainResult.final_target_diagnostic")
        if any(not step.transformation_observation.target_diagnosis.is_valid for step in value.steps):
            _fail("TransitionChainResult.steps")
    else:
        if value.failed_phase == "VALID_SOURCE":
            _equal((value.failed_index, len(value.steps), len(records)), (None, 0, 1))
        elif value.failed_phase == "TRANSFORMATION":
            _equal(value.failed_index, len(value.steps)-1)
            _equal(len(records), 1+3*len(value.steps))
            _equal(value.failure_code, "CHAIN_TARGET_NOT_VALID")
            if not value.steps or value.steps[-1].transformation_observation.target_diagnosis.is_valid:
                _fail("TransitionChainFailure.steps")
        else:
            _equal(value.failed_index, len(value.steps))
            _equal(len(records), 1+3*len(value.steps)+(1 if value.failed_phase == "SELECTION" else 2))
        if records[-1].emission.envelope.disposition != "BLOCKED":
            _fail("TransitionChainFailure.constructed_records")


def _plan_coherence(plan):
    _equal(plan.source_realm, plan.source_state_identity)
    _equal(plan.destination_realm, plan.destination_state_identity)
    _equal(plan.normalized_state.signature, plan.source_state_identity.state_signature)
    _equal(len(plan.topology_nodes), 3 ** plan.inputs.topology_depth)
    _equal(len(plan.role_assignments), len(plan.topology_nodes))
    _equal(plan.warnings, _warnings(plan.axiom_diagnostic))
    _equal(plan.axiom_subject.state.signature, plan.destination_state_identity.state_signature)
    _equal(plan.metadata.profile_id,plan.inputs.profile_id)
    for ordinal, (node, assignment) in enumerate(zip(plan.topology_nodes, plan.role_assignments)):
        _equal(node.ordinal,ordinal)
        _equal(node.depth,plan.inputs.topology_depth)
        _equal(node.node_id,"topology:"+plan.inputs.seed_token+":"+node.path_token)
        _equal((node.node_id, node.path_token, node.ordinal), (assignment.node_reference, assignment.node_path, assignment.ordinal))
        _equal(assignment.assignment_reference,plan.plan_reference+":assignment:"+node.path_token)
        _equal(assignment.destination_state.signature, plan.destination_state_identity.state_signature)
    expected_count = 0 if plan.inputs.emission_choice == "INSPECT_ONLY" else (len(plan.topology_nodes)+31)//32
    _equal(len(plan.artifacts), expected_count)
    for index, artifact in enumerate(plan.artifacts):
        _equal((artifact.page_index, artifact.document.page_count, artifact.document.plan_reference),
               (index, expected_count, plan.plan_reference))
        rows = tuple(ManifestRow(node, assignment) for node, assignment in
                     zip(plan.topology_nodes[index*32:(index+1)*32], plan.role_assignments[index*32:(index+1)*32]))
        _equal(artifact.document.rows, rows)
        _equal((artifact.document.source_identity,artifact.document.destination_identity,artifact.document.axiom_subject,
                artifact.document.axiom_diagnostic,artifact.document.warnings,artifact.document.inputs,artifact.document.policy_binding),
               (plan.source_state_identity,plan.destination_state_identity,plan.axiom_subject,plan.axiom_diagnostic,
                plan.warnings,plan.inputs,plan.binding.policy_binding))
        _equal(artifact.artifact_reference, plan.plan_reference+":artifact:"+f"{index:03d}")
        _equal(artifact.plan_element_reference, plan.plan_reference+":manifest:"+f"{index:03d}")
    if (len(plan.artifacts) > plan.target_constraints.max_artifacts or
            any(row.content_byte_count > plan.target_constraints.max_document_bytes for row in plan.artifacts) or
            sum(row.content_byte_count for row in plan.artifacts) > plan.target_constraints.max_total_document_bytes):
        _fail("ReferenceGenerationPlan.artifacts")


_CONTROL_MARKER = object()
_ACTION_MARKER = object()
_LOCK_TYPE = type(Lock())


class IssuedEmitterCaptureControl:
    """API-only original emitter token; no public constructor grants issuance."""
    __slots__ = ("_emitter", "_collector", "_operation", "_prepared", "_slots", "_cookie", "_lock", "_sealed")

    def __new__(cls, *args, **kwargs):
        _fail("emitter_control")

    @staticmethod
    def validate_issued_for_collector(control, collector, operation_reference, *, emitter=None, prepared=None, record_slots=None):
        if type(control) is not IssuedEmitterCaptureControl or type(operation_reference) is not str:
            return False
        try:
            cookie = object.__getattribute__(control, "_cookie")
            issued=(type(cookie) is tuple and len(cookie) == 8 and cookie[0] is _CONTROL_MARKER and
                    cookie[1] is control and cookie[2] is control._emitter and cookie[3] is collector is control._collector and
                    type(control._operation) is str and type(cookie[4]) is str and cookie[4] == operation_reference == control._operation and
                    cookie[5] is control._prepared and cookie[6] is control._slots and type(control._sealed) is bool and
                    type(control._lock) is _LOCK_TYPE and cookie[7] is control._lock)
            if not issued:return False
            if emitter is not None:
                from .artifact_emitter import ReferenceArtifactEmitter
                if type(emitter) is not ReferenceArtifactEmitter or emitter is not control._emitter:return False
            if prepared is not None:
                from .diagnostic_module_values import PreparedEmission
                if type(prepared) is not PreparedEmission or prepared is not control._prepared:return False
            if record_slots is not None:
                if type(record_slots) is not tuple or not 1<=len(record_slots)<=47:return False
                for ref in record_slots:_ref(ref,"record_slots")
                if record_slots!=control._slots:return False
            return True
        except (AttributeError,PlannerEmitterContractError):
            return False

    @staticmethod
    def capture_disposition(control):
        if type(control) is not IssuedEmitterCaptureControl:
            return "UNAVAILABLE"
        try:
            if not IssuedEmitterCaptureControl.validate_issued_for_collector(control, control._collector, control._operation):
                return "UNAVAILABLE"
            if control._sealed:
                return "SEALED"
            if not control._lock.acquire(False):
                return "UNAVAILABLE"
            try:
                return "SEALED" if control._sealed else "ACTIVE"
            finally:
                control._lock.release()
        except AttributeError:
            return "UNAVAILABLE"


def _issue_emitter_control(emitter, collector, operation_reference, prepared, record_slots):
    from .artifact_emitter import ReferenceArtifactEmitter
    from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
    _exact(emitter, ReferenceArtifactEmitter, "emitter")
    _exact(collector, (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics), "collector")
    _ref(operation_reference, maximum=160)
    _exact(record_slots, tuple, "record_slots")
    if not 1 <= len(record_slots) <= 47:
        _fail("record_slots")
    for reference in record_slots:
        _ref(reference, "record_slots")
    control = object.__new__(IssuedEmitterCaptureControl)
    control._emitter, control._collector, control._operation = emitter, collector, operation_reference
    control._prepared, control._slots, control._lock, control._sealed = prepared, record_slots, Lock(), False
    control._cookie = (_CONTROL_MARKER, control, emitter, collector, operation_reference, prepared, record_slots, control._lock)
    return control


def _seal_emitter_control(control):
    _exact(control, IssuedEmitterCaptureControl, "emitter_control")
    control._sealed = True


class EmissionActionLease:
    """API-only single action metadata, validated locally by the exact target."""
    __slots__ = ("_emitter", "_target", "_operation", "_description", "_revision", "_cookie", "_description_digest", "_claim_lock", "_used")

    def __new__(cls, *args, **kwargs):
        _fail("action_lease")


def _issue_action_lease(emitter, target, operation_reference, description, expected_revision):
    from .artifact_emitter import ReferenceArtifactEmitter
    from .memory_document_target import MemoryDocumentTarget
    _exact(emitter, ReferenceArtifactEmitter, "emitter")
    _exact(target, MemoryDocumentTarget, "target")
    _exact(description, ArtifactDescription, "description")
    revalidate_value(description)
    _ref(operation_reference, maximum=160)
    if type(expected_revision) is not int or not 0 <= expected_revision <= (1 << 64)-1:
        _fail("target_revision")
    lease = object.__new__(EmissionActionLease)
    lease._emitter, lease._target, lease._operation = emitter, target, operation_reference
    lease._description, lease._revision = description, expected_revision
    lease._claim_lock,lease._used=Lock(),False
    lease._description_digest = _digest(description)
    lease._cookie = (_ACTION_MARKER, lease, emitter, target, operation_reference, description, expected_revision, lease._description_digest,lease._claim_lock)
    return lease


def _action_lease_facts(lease, target, description):
    if type(lease) is not EmissionActionLease or type(description) is not ArtifactDescription:
        _fail("action_lease")
    try:
        cookie = lease._cookie
        if (type(cookie) is not tuple or len(cookie) != 9 or cookie[0] is not _ACTION_MARKER or cookie[1] is not lease or
                cookie[2] is not lease._emitter or cookie[3] is not target is lease._target or cookie[5] is not description is lease._description or
                type(lease._operation) is not str or type(lease._revision) is not int or
                type(cookie[4]) is not str or type(cookie[6]) is not int or type(cookie[7]) is not str or
                type(lease._description_digest) is not str or type(lease._used) is not bool or cookie[8] is not lease._claim_lock or cookie[7] != lease._description_digest or
                cookie[4] != lease._operation or cookie[6] != lease._revision or _digest(description) != lease._description_digest):
            _fail("action_lease")
        return lease._operation, lease._revision
    except AttributeError:
        _fail("action_lease")


def _claim_action_lease(lease):
    # Local original lease ownership was fully checked before this nonblocking once latch.
    if not lease._claim_lock.acquire(False):
        return False
    try:
        if lease._used:
            return False
        lease._used=True
        return True
    finally:
        lease._claim_lock.release()


@dataclass(frozen=True, slots=True)
class CancellationObservation:
    operation_reference: str
    status: str

    def __post_init__(self):
        _ref(self.operation_reference, maximum=160)
        if type(self.status) is not str or self.status not in ("LATCHED", "ALREADY_FINAL", "UNKNOWN_OPERATION"):
            _fail("cancellation.status")


@dataclass(frozen=True, slots=True)
class OwnerShutdownObservation:
    status: str
    active_operation_count: int
    unused_preparation_count: object

    def __post_init__(self):
        if type(self.status) is not str or self.status not in ("SEALED", "ALREADY_SEALED"):
            _fail("shutdown.status")
        if (type(self.active_operation_count) is not int or not 0 <= self.active_operation_count <= 8 or
                self.unused_preparation_count is not None and
                (type(self.unused_preparation_count) is not int or not 0 <= self.unused_preparation_count <= 64)):
            _fail("shutdown.count")
