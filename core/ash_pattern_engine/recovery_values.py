"""Owned N2 recovery values [YWE-REQ-0041] and reviewed source pairs [YWE-REQ-0043]."""

from __future__ import annotations

from dataclasses import dataclass, fields
import re
from typing import ClassVar, Literal

from . import state_values as state
from . import normalization_values as normalization
from .diagnostics_values import DiagnosticsCompletionReceipt

CONTRACT_CODES = frozenset(("RECOVERY_INPUT_INVALID", "RECOVERY_BINDING_MISMATCH", "RECOVERY_PLAN_INVALID", "RECOVERY_PORT_INVALID"))
ASSESSMENT_FAILURE_CODES = frozenset(("SOURCE_BINDING_MISMATCH", "PROFILE_BINDING_MISMATCH", "INPUT_BINDING_MISMATCH", "DIAGNOSIS_MISMATCH", "PREDICATE_BINDING_MISMATCH", "PREDICATE_NOT_EVALUATED", "CLASSIFICATION_MISMATCH", "CLASSIFICATION_ENVELOPE_MISMATCH"))
CORRECTION_FAILURE_CODES = frozenset(("SOURCE_BINDING_MISMATCH", "PROFILE_BINDING_MISMATCH", "ORIGIN_MISMATCH", "CHAIN_MEMBER_INVALID", "CHAIN_TARGET_MISMATCH", "TARGET_NOT_VALID"))
REGISTRY_FAILURE_CODES = frozenset(("REGISTRY_SOURCE_MISMATCH", "REGISTRY_PROFILE_MISMATCH", "CERTIFICATION_INVENTORY_MISMATCH", "TARGET_NOT_VALID", "CERTIFICATION_NOT_STABLE"))
FAILURE_CODES = frozenset(("ORIGIN_REJECTED", "CAPTURE_ADMISSION_REJECTED", "CAPTURE_ADMISSION_UNCONFIRMED", "STEP_CAPTURE_REJECTED", "STEP_CAPTURE_UNCONFIRMED", "POST_EVIDENCE_UNAVAILABLE", "POST_ASSESSMENT_FAILED", "POST_CAPTURE_REJECTED", "POST_CAPTURE_UNCONFIRMED", "COLLABORATOR_FAILED", "RESOURCE_LIMIT", "INTERNAL_INVARIANT_FAILURE", "REGISTRY_BINDING_REJECTED", "COMPLETION_REJECTED", "COMPLETION_UNCONFIRMED"))
COMPLETION_FAILURE_CODES = frozenset(("COMPLETION_REJECTED", "COMPLETION_UNCONFIRMED"))
N2_RULE_IDS = frozenset((*state.ASSESSMENT_RULE_IDS, "ASH-CODEWORD-STRUCTURE-001", "ASH-FALLBACK-SELECTION-001"))
STEP_ACTIONS = ("NORMALIZE_PLAN", "NORMALIZE_XOR", "CORRECTION_RESOLVE", "CORRECTION_XOR", "CANDIDATE_APPLICABILITY", "FALLBACK_SELECT", "CANDIDATE_VALIDATION", "POST_ASSESSMENT", "HANDOFF", "NO_ACTION")
CANONICAL_STEP_ACTIONS = ("normalize", "correct", "validate-recovery", "select-fallback", "validate-fallback", "resolve-normalization", "resolve-correction", "evaluate-applicability", "evaluate-additional-validation", "handoff", "no-action", "fallback-summary")
ACTION_NAMES = ("NORMALIZE", "CORRECT", "FALLBACK_CANDIDATE", "FALLBACK_SUMMARY", "NO_ACTION", "HANDOFF")
RECOVERY_OUTCOMES = ("RECOVERED", "RECOVERED_VIA_FALLBACK", "BLOCKED", "RECOVERY_FAILED", "ESCALATE_TO_CONTAINMENT", "NOT_APPLICABLE")
STATUSES = ("COMPLETED", "BLOCKED", "FAILED")
CONTAINMENT_TRIGGERS = ("FALLBACK_FAILURE", "PROPAGATION_RISK", "OPERATOR_REQUEST", "RECOVERY_VALIDATION_FAILURE")
HALT_TRIGGERS = ("ESCALATION_FROM_FAILED", "CONTAINMENT_BREACH", "OPERATOR_HALT_REQUEST", "POLICY_HALT_REQUEST", "UNRESOLVABLE_BLOCKED_RECOVERY")
CanonicalContainmentTrigger = Literal["FALLBACK_FAILURE", "PROPAGATION_RISK", "OPERATOR_REQUEST", "RECOVERY_VALIDATION_FAILURE"]
CanonicalSafeHaltTrigger = Literal["ESCALATION_FROM_FAILED", "CONTAINMENT_BREACH", "OPERATOR_HALT_REQUEST", "POLICY_HALT_REQUEST", "UNRESOLVABLE_BLOCKED_RECOVERY"]
CanonicalCodeword = state.AshState
SystemStateClass = Literal["STABLE", "UNSTABLE", "CORRECTABLE", "DEGRADED", "CONTAINED", "FAILED", "SAFE_HALT"]
RecoveryCategory = Literal["NO_ACTION", "NORMALIZE_STATE", "APPLY_CORRECTION", "FALLBACK_REQUIRED", "CONTAINMENT_REQUIRED", "ESCALATION_REQUIRED", "TERMINAL_NO_RECOVERY"]
N2RuleID = str
RECOVERY_CONTRACT_PIN_FIELDS = (
    ("interfaces/contracts/recovery-engine-contract.md", "27ffacc6218812b280ed236bf9052ee825e903498365d735bf57ee9cb338955b"),
    ("interfaces/contracts/diagnostics-module-contract.md", "88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37"),
    ("registries/fallback-policy-registry.md", "b108d6c4127da9ea375899e97c34048ded4ea3a7cb624ef24f18bfda5f8deaaa"),
    ("algorithms/recovery-fallback-semantics.pseudo.md", "0fb8a0750acae0fb263cd842e186ff35881f77b8e498a8f11f159a5d2db270b7"),
    ("algorithms/containment-safe-failure-semantics.pseudo.md", "83f1a19c1a0f375e02f2044c238786514d64b122ab6ab5a8bda6e6fa307c8256"),
    ("interfaces/diagnostic-schema.md", "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"),
    ("interfaces/rule-id-taxonomy.md", "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"),
)
RECOVERY_SOURCE_BASELINES = (
    ("LEGACY_C78", state.CANONICAL_BINDING_FIELDS, RECOVERY_CONTRACT_PIN_FIELDS),
    ("N3_LIFECYCLE", state.CURRENT_CANONICAL_BINDING_FIELDS, (
        *RECOVERY_CONTRACT_PIN_FIELDS[:4],
        ("algorithms/containment-safe-failure-semantics.pseudo.md", "df957dc5c82c2fd0b51e43c6783d8cbb2e3ce565420a765abffd244cdcea98b2"),
        RECOVERY_CONTRACT_PIN_FIELDS[5],
        ("interfaces/rule-id-taxonomy.md", "150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250"),
    )),
)
RECOVERY_POLICY_BINDING_FIELDS = (
    ("policy_id", "YWE-RECOVERY-SAFETY-001"), ("policy_version", "1.0.0"),
    ("source_path", "docs/architecture/m3_recovery_safety_policy.md"),
    ("source_sha256", "00fcee810c5cd445dd0baaaf98c754000347489001e21588eb03afdd1e1ebb95"),
)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_POLICY = re.compile(r"FALLBACK-[A-Z][A-Z0-9]{0,31}-(?!000)[0-9]{3}\Z")
FIELD_NAMES = frozenset((
    "origin_assessment", "origin_validation", "source_binding", "profile_binding", "registry", "registry.source_binding", "registry.entries", "operation_context", "operation_context.context_observation", "operation_context.propagation_evidence", "operation_context.external_authority_evidence", "normalization_preparation", "normalization_preparation.plan", "normalization_preparation.plan_validation", "correction_observation", "correction_observation.submitted", "correction_observation.validation", "route_authorization", "applicability", "predicate_observation", "post_assessment", "post_assessment.classification_evidence", "post_assessment.system_context", "capture", "capture.admission", "capture.append", "capture.finish", "directive", "candidate_state", "action_decisions", "emitted_diagnostics", "registry.candidate_certifications", "registry_validation", "normalization_preparation.resolution_observation", "normalization_resolver", "correction_provider", "condition_evaluator", "post_facts_provider",
))
_ASSESSMENT_PATHS = (
    "source_binding", "profile_binding", "input_evidence", "parsed_state", "system_context", "system_state_class", "recovery_category", "consulted_predicates",
    *("state_validity_diagnostic." + n for n in ("input_state", "admissibility_status", "transformation_compatibility", "normalization_status", "recoverability_relevance", "is_valid", "orbit_info", "rule_ids", "notes")),
    *("assessment_binding." + n for n in ("assessment_reference", "original_input_reference", "diagnosis_reference")),
    *("classification_evidence." + p + "." + n for p in state.PREDICATE_NAMES for n in ("evaluation", "value", "reason", "binding.assessment_reference", "binding.diagnosis_reference", "binding.subject_reference", "binding.profile_id", "binding.profile_source_sha256", "binding.ash_dependency_id", "binding.ash_aggregate_sha256", "binding.evidence_reference")),
    *(f"emitted_diagnostics[{i}]." + n for i in range(2) for n in ("diagnostic_reference", "envelope.diagnostic_kind", "envelope.severity", "envelope.stage", "envelope.disposition", "envelope.subject_reference", "envelope.parent_diagnostic_reference", "envelope.chain_root_reference", "envelope.rule_ids", "envelope.summary", "envelope.notes")),
)
FIELD_NAMES |= frozenset("origin_assessment." + n for n in _ASSESSMENT_PATHS)
FIELD_NAMES |= frozenset(f"chain[{i}]" for i in range(16))
FIELD_NAMES |= frozenset(f"{prefix}[{i}]" for prefix, size in (("entries", 32), ("registry.entries", 32), ("registry.candidate_certifications", 32), ("steps", 768), ("post_assessments", 33), ("action_decisions", 35)) for i in range(size))
FIELD_NAMES |= frozenset(f"entries[{i}].{phase}[{j}]" for i in range(32) for phase in ("applicability_conditions", "validation_requirements") for j in range(8))
RecoveryFieldPath = str


class RecoveryContractError(ValueError):
    """A closed pre-effect structural/configuration refusal."""
    def __init__(self, code, field_name, *, validation=None):
        if type(code) is not str or code not in CONTRACT_CODES or type(field_name) is not str or field_name not in FIELD_NAMES:
            raise ValueError("invalid RecoveryContractError construction")
        if validation is not None:
            if not any(type(validation) is kind for kind in (AssessmentValidation, RegistryValidation, CorrectionValidation)) or validation.status != "REJECTED" or validation.field_name != field_name:
                raise ValueError("invalid RecoveryContractError validation")
        self.code, self.field_name, self.validation = code, field_name, validation
        self.emitted_diagnostics = ()
        super().__init__(f"{code}: {field_name}")


def _fail(field, code="RECOVERY_INPUT_INVALID"):
    raise RecoveryContractError(code, field)


def _exact(value, kinds, field):
    allowed = kinds if type(kinds) is tuple else (kinds,)
    if not any(type(value) is kind for kind in allowed):
        _fail(field)


def _reference(value, field, maximum=256):
    if type(value) is not str or len(value) > maximum or _IDENTIFIER.fullmatch(value) is None or value in ("NONE", "SELF"):
        _fail(field)


def _choice(value, choices, field):
    if type(value) is not str or value not in choices:
        _fail(field)


def _hash(value, field):
    if type(value) is not str or _HASH.fullmatch(value) is None:
        _fail(field)


def _policy(value, field):
    if type(value) is not str or _POLICY.fullmatch(value) is None:
        _fail(field)


def _text(value, field):
    if type(value) is not str or not value.strip() or len(value) > 512:
        _fail(field)


def _integer(value, low, high, field):
    if type(value) is not int or not low <= value <= high:
        _fail(field)


def _sequence(value, check, field, maximum, minimum=0):
    _exact(value, (list, tuple), field)
    if not minimum <= len(value) <= maximum:
        _fail(field)
    for member in value:
        check(member, field)
    return tuple(value)


def _optional(value, kind, field):
    if value is not None:
        _exact(value, kind, field)


def _record(value):
    if value is None or any(type(value) is kind for kind in (str, int, bool)):
        return value
    if type(value) is tuple:
        return [_record(v) for v in value]
    return value.to_record()


class _Record:
    _headers: ClassVar[tuple[tuple[str, object], ...]] = ()
    def to_record(self):
        return {**dict(self._headers), **{f.name: _record(getattr(self, f.name)) for f in fields(self)}}


@dataclass(frozen=True, slots=True)
class SourcePin(_Record):
    path: str
    sha256: str
    def __post_init__(self):
        _reference(self.path, "source_binding")
        _hash(self.sha256, "source_binding")


def recovery_contract_pin_fields(binding: state.CanonicalAshBinding) -> tuple[tuple[str, str], ...]:
    """Select the whole reviewed recovery vector for an exact canonical binding."""
    _exact(binding, state.CanonicalAshBinding, "source_binding")
    try:
        baseline = state.canonical_source_baseline(binding)
    except state.StateContractError:
        _fail("source_binding", "RECOVERY_BINDING_MISMATCH")
    for name, _canonical_fields, pins in RECOVERY_SOURCE_BASELINES:
        if baseline == name:
            return pins
    _fail("source_binding", "RECOVERY_BINDING_MISMATCH")


@dataclass(frozen=True, slots=True)
class RecoverySourceBinding(_Record):
    canonical_binding: state.CanonicalAshBinding
    contract_pins: tuple[SourcePin, ...]
    def __post_init__(self):
        expected = recovery_contract_pin_fields(self.canonical_binding)
        pins = _sequence(self.contract_pins, lambda v, f: _exact(v, SourcePin, f), "source_binding", 7, 7)
        for pin in pins:
            try:
                SourcePin.__post_init__(pin)
            except AttributeError:
                _fail("source_binding", "RECOVERY_BINDING_MISMATCH")
        if tuple((p.path, p.sha256) for p in pins) != expected:
            _fail("source_binding", "RECOVERY_BINDING_MISMATCH")
        object.__setattr__(self, "contract_pins", pins)


@dataclass(frozen=True, slots=True)
class EvidenceSourceBinding(_Record):
    source_reference: str
    source_sha256: str
    evidence_reference: str
    def __post_init__(self):
        _reference(self.source_reference, "source_binding")
        _hash(self.source_sha256, "source_binding")
        _reference(self.evidence_reference, "source_binding")


@dataclass(frozen=True, slots=True)
class ContextObservation(_Record):
    context: state.SystemContext
    owner_reference: str
    observation_reference: str
    source_binding: EvidenceSourceBinding
    def __post_init__(self):
        _exact(self.context, state.SystemContext, "operation_context.context_observation")
        _reference(self.owner_reference, "operation_context.context_observation")
        _reference(self.observation_reference, "operation_context.context_observation")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")


@dataclass(frozen=True, slots=True)
class PropagationEvidence(_Record):
    status: str
    operation_reference: str
    origin_assessment_reference: str
    source_binding: EvidenceSourceBinding
    reason: str
    def __post_init__(self):
        _choice(self.status, ("SAFE", "RISK", "UNAVAILABLE"), "operation_context.propagation_evidence")
        _reference(self.operation_reference, "operation_context", 192)
        _reference(self.origin_assessment_reference, "origin_assessment")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _text(self.reason, "operation_context.propagation_evidence")


@dataclass(frozen=True, slots=True)
class ExternalAuthorityEvidence(_Record):
    status: str
    operation_reference: str
    origin_assessment_reference: str
    source_binding: EvidenceSourceBinding
    reason: str
    def __post_init__(self):
        _choice(self.status, ("REACHABLE", "UNREACHABLE", "UNAVAILABLE"), "operation_context.external_authority_evidence")
        _reference(self.operation_reference, "operation_context", 192)
        _reference(self.origin_assessment_reference, "origin_assessment")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _text(self.reason, "operation_context.external_authority_evidence")


@dataclass(frozen=True, slots=True)
class RecoveryOperationContext(_Record):
    operation_reference: str
    origin_assessment_reference: str
    context_observation: ContextObservation
    propagation_evidence: PropagationEvidence
    external_authority_evidence: ExternalAuthorityEvidence
    def __post_init__(self):
        _reference(self.operation_reference, "operation_context", 192)
        _reference(self.origin_assessment_reference, "origin_assessment")
        for name, kind in (("context_observation", ContextObservation), ("propagation_evidence", PropagationEvidence), ("external_authority_evidence", ExternalAuthorityEvidence)):
            _exact(getattr(self, name), kind, "operation_context." + name)
        for evidence in (self.propagation_evidence, self.external_authority_evidence):
            if (evidence.operation_reference, evidence.origin_assessment_reference) != (self.operation_reference, self.origin_assessment_reference):
                _fail("operation_context", "RECOVERY_BINDING_MISMATCH")


@dataclass(frozen=True, slots=True)
class AssessmentValidation(_Record):
    status: str
    submitted_assessment: state.StateAssessment
    current_source_binding: state.CanonicalAshBinding
    current_profile_binding: state.ProfileBinding
    expected_diagnostic: state.StateValidityDiagnostic | None
    expected_system_state_class: str | None
    expected_recovery_category: str | None
    expected_consulted_predicates: tuple[str, ...] | None
    failure_code: str | None
    field_name: str | None
    def __post_init__(self):
        _choice(self.status, ("VERIFIED", "REJECTED"), "origin_validation")
        _exact(self.submitted_assessment, state.StateAssessment, "origin_assessment")
        _exact(self.current_source_binding, state.CanonicalAshBinding, "source_binding")
        _exact(self.current_profile_binding, (state.AvailableProfileBinding, state.UnavailableProfileBinding), "profile_binding")
        _optional(self.expected_diagnostic, state.StateValidityDiagnostic, "origin_validation")
        if self.expected_system_state_class is not None:
            _choice(self.expected_system_state_class, tuple(x for x, _ in state.RECOVERY_CATEGORY_PAIRS), "origin_validation")
        if self.expected_recovery_category is not None:
            _choice(self.expected_recovery_category, tuple(x for _, x in state.RECOVERY_CATEGORY_PAIRS), "origin_validation")
        if self.expected_consulted_predicates is not None:
            p = _sequence(self.expected_consulted_predicates, lambda v, f: _choice(v, state.PREDICATE_NAMES, f), "origin_validation", 1)
            object.__setattr__(self, "expected_consulted_predicates", p)
        if self.status == "VERIFIED":
            if self.failure_code is not None or self.field_name is not None or any(x is None for x in (self.expected_diagnostic, self.expected_system_state_class, self.expected_recovery_category, self.expected_consulted_predicates)):
                _fail("origin_validation")
            if (self.expected_system_state_class, self.expected_recovery_category) not in state.RECOVERY_CATEGORY_PAIRS:
                _fail("origin_validation")
        else:
            _choice(self.failure_code, ASSESSMENT_FAILURE_CODES, "origin_validation")
            _choice(self.field_name, FIELD_NAMES, "origin_validation")


@dataclass(frozen=True, slots=True)
class KnownCorrection(_Record):
    correction_reference: str
    original_assessment_reference: str
    source_binding: EvidenceSourceBinding
    profile_id: str
    profile_source_sha256: str
    chain: tuple[state.AshState, ...]
    expected_target: state.AshState
    reason: str
    classification_evidence_reference: str
    canonical_binding: state.CanonicalAshBinding
    provider_source_verification: ClassVar[str] = "DECLARED_NOT_AUTHENTICATED"
    _headers = (("provider_source_verification", "DECLARED_NOT_AUTHENTICATED"),)
    def __post_init__(self):
        for v in (self.correction_reference, self.original_assessment_reference, self.profile_id, self.classification_evidence_reference):
            _reference(v, "correction_observation.submitted")
        _hash(self.profile_source_sha256, "correction_observation.submitted")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _exact(self.canonical_binding, state.CanonicalAshBinding, "source_binding")
        object.__setattr__(self, "chain", _sequence(self.chain, lambda v, f: _exact(v, state.AshState, f), "correction_observation.submitted", 16))
        _exact(self.expected_target, state.AshState, "candidate_state")
        _text(self.reason, "correction_observation.submitted")


@dataclass(frozen=True, slots=True)
class UnavailableCorrection(_Record):
    original_assessment_reference: str
    source_binding: EvidenceSourceBinding
    reason: str
    classification_evidence_reference: str
    provider_source_verification: ClassVar[str] = "DECLARED_NOT_AUTHENTICATED"
    _headers = (("provider_source_verification", "DECLARED_NOT_AUTHENTICATED"),)
    def __post_init__(self):
        _reference(self.original_assessment_reference, "origin_assessment")
        _reference(self.classification_evidence_reference, "correction_observation.submitted")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _text(self.reason, "correction_observation.submitted")


@dataclass(frozen=True, slots=True)
class CorrectionValidation(_Record):
    status: str
    submitted_correction: KnownCorrection
    origin_validation: AssessmentValidation
    current_source_binding: state.CanonicalAshBinding
    current_profile_binding: state.ProfileBinding
    computed_target: state.AshState | None
    target_diagnostic: state.StateValidityDiagnostic | None
    failure_code: str | None
    field_name: str | None
    def __post_init__(self):
        _choice(self.status, ("VERIFIED", "REJECTED"), "correction_observation.validation")
        _exact(self.submitted_correction, KnownCorrection, "correction_observation.submitted")
        _exact(self.origin_validation, AssessmentValidation, "origin_validation")
        _exact(self.current_source_binding, state.CanonicalAshBinding, "source_binding")
        _exact(self.current_profile_binding, (state.AvailableProfileBinding, state.UnavailableProfileBinding), "profile_binding")
        _optional(self.computed_target, state.AshState, "candidate_state")
        _optional(self.target_diagnostic, state.StateValidityDiagnostic, "correction_observation.validation")
        if (self.current_source_binding, self.current_profile_binding) != (self.origin_validation.current_source_binding, self.origin_validation.current_profile_binding):
            _fail("correction_observation.validation")
        if self.status == "VERIFIED":
            if self.failure_code is not None or self.field_name is not None or self.origin_validation.status != "VERIFIED" or self.computed_target is None or self.target_diagnostic is None or not self.target_diagnostic.is_valid or self.target_diagnostic.input_state != self.computed_target:
                _fail("correction_observation.validation")
        else:
            _choice(self.failure_code, CORRECTION_FAILURE_CODES, "correction_observation.validation")
            _choice(self.field_name, FIELD_NAMES, "correction_observation.validation")
            if self.origin_validation.status == "REJECTED" and (self.failure_code != "ORIGIN_MISMATCH" or self.computed_target is not None or self.target_diagnostic is not None):
                _fail("correction_observation.validation")


@dataclass(frozen=True, slots=True)
class ConditionReference(_Record):
    condition_id: str
    source_binding: EvidenceSourceBinding
    def __post_init__(self):
        _reference(self.condition_id, "applicability", 128)
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")


@dataclass(frozen=True, slots=True)
class FallbackPolicyEntry(_Record):
    policy_id: str
    applicability_conditions: tuple[ConditionReference, ...]
    candidate_state_reference: state.AshState
    ordering_rank: int
    validation_requirements: tuple[ConditionReference, ...]
    escalation_on_failure: str
    notes: tuple[str, ...]
    def __post_init__(self):
        _policy(self.policy_id, "registry.entries")
        _exact(self.candidate_state_reference, state.AshState, "candidate_state")
        _integer(self.ordering_rank, -(1 << 63), (1 << 63) - 1, "registry.entries")
        _choice(self.escalation_on_failure, ("TRY_NEXT", "ESCALATE_TO_CONTAINMENT"), "registry.entries")
        for name in ("applicability_conditions", "validation_requirements"):
            object.__setattr__(self, name, _sequence(getattr(self, name), lambda v, f: _exact(v, ConditionReference, f), "registry.entries", 8))
        object.__setattr__(self, "notes", _sequence(self.notes, _text, "registry.entries", 8, 1))


@dataclass(frozen=True, slots=True)
class RegistrySourceBinding(_Record):
    registry_id: str
    source_binding: EvidenceSourceBinding
    profile_id: str
    profile_source_sha256: str
    ash_dependency_id: str
    ash_aggregate_sha256: str
    source_verification: ClassVar[str] = "DECLARED_NOT_AUTHENTICATED"
    _headers = (("source_verification", "DECLARED_NOT_AUTHENTICATED"),)
    def __post_init__(self):
        _reference(self.registry_id, "registry.source_binding", 128)
        _reference(self.profile_id, "profile_binding")
        _hash(self.profile_source_sha256, "profile_binding")
        _exact(self.source_binding, EvidenceSourceBinding, "registry.source_binding")
        if (type(self.ash_dependency_id) is not str or
                self.ash_dependency_id != state.CANONICAL_BINDING_FIELDS[0][1] or
                type(self.ash_aggregate_sha256) is not str or
                self.ash_aggregate_sha256 not in tuple(dict(canonical)["aggregate_sha256"]
                                                     for _name, canonical, _pins in RECOVERY_SOURCE_BASELINES)):
            _fail("registry.source_binding", "RECOVERY_BINDING_MISMATCH")


@dataclass(frozen=True, slots=True)
class CandidateCertification(_Record):
    policy_id: str
    context_observation: ContextObservation
    source_assessment: state.StateAssessment
    def __post_init__(self):
        _policy(self.policy_id, "registry.candidate_certifications")
        _exact(self.context_observation, ContextObservation, "operation_context.context_observation")
        _exact(self.source_assessment, state.StateAssessment, "origin_assessment")
        if self.context_observation.context != self.source_assessment.system_context:
            _fail("registry.candidate_certifications", "RECOVERY_BINDING_MISMATCH")


_REGISTRY_HEADERS = (("schema_ref", "data/schemas/m3_fallback_registry_schema.json"), ("artifact_type", "ywe_fallback_registry"), ("artifact_version", "1.0.0"))
@dataclass(frozen=True, slots=True)
class AvailableFallbackRegistry(_Record):
    source_binding: RegistrySourceBinding
    entries: tuple[FallbackPolicyEntry, ...]
    candidate_certifications: tuple[CandidateCertification, ...]
    schema_ref: ClassVar[str] = _REGISTRY_HEADERS[0][1]
    artifact_type: ClassVar[str] = _REGISTRY_HEADERS[1][1]
    artifact_version: ClassVar[str] = "1.0.0"
    availability: ClassVar[str] = "AVAILABLE"
    _headers = (*_REGISTRY_HEADERS, ("availability", "AVAILABLE"))
    def __post_init__(self):
        _exact(self.source_binding, RegistrySourceBinding, "registry.source_binding")
        entries = _sequence(self.entries, lambda v, f: _exact(v, FallbackPolicyEntry, f), "registry.entries", 32)
        certs = _sequence(self.candidate_certifications, lambda v, f: _exact(v, CandidateCertification, f), "registry.candidate_certifications", 32)
        ids = tuple(e.policy_id for e in entries)
        if len(set(ids)) != len(ids) or ids != tuple(c.policy_id for c in certs):
            _fail("registry.candidate_certifications")
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "candidate_certifications", certs)


@dataclass(frozen=True, slots=True)
class UnavailableFallbackRegistry(_Record):
    source_binding: RegistrySourceBinding
    reason: str
    schema_ref: ClassVar[str] = _REGISTRY_HEADERS[0][1]
    artifact_type: ClassVar[str] = _REGISTRY_HEADERS[1][1]
    artifact_version: ClassVar[str] = "1.0.0"
    availability: ClassVar[str] = "UNAVAILABLE"
    _headers = (*_REGISTRY_HEADERS, ("availability", "UNAVAILABLE"))
    def __post_init__(self):
        _exact(self.source_binding, RegistrySourceBinding, "registry.source_binding")
        _text(self.reason, "registry")


@dataclass(frozen=True, slots=True)
class RegistryTargetValidation(_Record):
    policy_id: str
    submitted_certification: CandidateCertification
    assessment_validation: AssessmentValidation
    target_diagnostic: state.StateValidityDiagnostic | None
    def __post_init__(self):
        _policy(self.policy_id, "registry.candidate_certifications")
        _exact(self.submitted_certification, CandidateCertification, "registry.candidate_certifications")
        _exact(self.assessment_validation, AssessmentValidation, "registry_validation")
        _optional(self.target_diagnostic, state.StateValidityDiagnostic, "registry_validation")
        if self.policy_id != self.submitted_certification.policy_id or self.assessment_validation.submitted_assessment != self.submitted_certification.source_assessment:
            _fail("registry_validation")


@dataclass(frozen=True, slots=True)
class RegistryValidation(_Record):
    status: str
    submitted_snapshot: AvailableFallbackRegistry | UnavailableFallbackRegistry
    current_source_binding: state.CanonicalAshBinding
    current_profile_binding: state.ProfileBinding
    candidate_validations: tuple[RegistryTargetValidation, ...]
    failure_code: str | None
    failed_policy_id: str | None
    field_name: str | None
    def __post_init__(self):
        _choice(self.status, ("VERIFIED", "REJECTED"), "registry_validation")
        _exact(self.submitted_snapshot, (AvailableFallbackRegistry, UnavailableFallbackRegistry), "registry")
        _exact(self.current_source_binding, state.CanonicalAshBinding, "source_binding")
        _exact(self.current_profile_binding, (state.AvailableProfileBinding, state.UnavailableProfileBinding), "profile_binding")
        vals = _sequence(self.candidate_validations, lambda v, f: _exact(v, RegistryTargetValidation, f), "registry_validation", 32)
        expected = self.submitted_snapshot.candidate_certifications if type(self.submitted_snapshot) is AvailableFallbackRegistry else ()
        if tuple(v.submitted_certification for v in vals) != expected[:len(vals)]:
            _fail("registry_validation")
        if any((v.assessment_validation.current_source_binding, v.assessment_validation.current_profile_binding) != (self.current_source_binding, self.current_profile_binding) for v in vals):
            _fail("registry_validation")
        object.__setattr__(self, "candidate_validations", vals)
        if self.status == "VERIFIED":
            if self.failure_code is not None or self.failed_policy_id is not None or self.field_name is not None or len(vals) != len(expected) or any(v.assessment_validation.status != "VERIFIED" or v.target_diagnostic is None or not v.target_diagnostic.is_valid or v.submitted_certification.source_assessment.system_state_class != "STABLE" for v in vals):
                _fail("registry_validation")
        else:
            _choice(self.failure_code, REGISTRY_FAILURE_CODES, "registry_validation")
            _choice(self.field_name, FIELD_NAMES, "registry_validation")
            if self.failed_policy_id is not None:
                _policy(self.failed_policy_id, "registry_validation")


@dataclass(frozen=True, slots=True)
class FallbackRouteAuthorization(_Record):
    route: str
    original_system_state_class: str
    origin_assessment_reference: str
    failed_action_decision_reference: str | None
    failed_outcome: str | None
    rule_ids: tuple[str, ...]
    origin_predicate_evidence_reference: str | None
    active_recovery_category: ClassVar[str] = "FALLBACK_REQUIRED"
    _headers = (("active_recovery_category", "FALLBACK_REQUIRED"),)
    def __post_init__(self):
        pairs = {"DIRECT_DEGRADED": "DEGRADED", "AFTER_CORRECTION_FAILURE": "CORRECTABLE", "AFTER_NORMALIZATION_FAILURE": "UNSTABLE"}
        _choice(self.route, tuple(pairs), "route_authorization")
        if type(self.original_system_state_class) is not str or self.original_system_state_class != pairs[self.route]:
            _fail("route_authorization")
        _reference(self.origin_assessment_reference, "origin_assessment")
        rules = _sequence(self.rule_ids, lambda v, f: _choice(v, N2_RULE_IDS, f), "route_authorization", 2, 2)
        if rules != ("ASH-RECOVERY-ACTION-001", "ASH-FALLBACK-SELECTION-001"):
            _fail("route_authorization")
        object.__setattr__(self, "rule_ids", rules)
        if self.origin_predicate_evidence_reference is not None:
            _reference(self.origin_predicate_evidence_reference, "route_authorization")
        if self.route == "DIRECT_DEGRADED":
            if self.failed_action_decision_reference is not None or self.failed_outcome is not None:
                _fail("route_authorization")
        else:
            _reference(self.failed_action_decision_reference, "route_authorization")
            _choice(self.failed_outcome, ("RECOVERY_FAILED",) if self.route == "AFTER_NORMALIZATION_FAILURE" else ("BLOCKED", "RECOVERY_FAILED"), "route_authorization")
            if self.route == "AFTER_CORRECTION_FAILURE":
                _reference(self.origin_predicate_evidence_reference, "route_authorization")


@dataclass(frozen=True, slots=True)
class PredicateObservation(_Record):
    status: str
    condition: ConditionReference
    operation_reference: str
    origin_assessment_reference: str
    registry_id: str
    registry_source_sha256: str
    policy_id: str
    phase: str
    candidate_state_reference: state.AshState
    source_binding: EvidenceSourceBinding
    reason: str
    def __post_init__(self):
        _choice(self.status, ("TRUE", "FALSE", "UNAVAILABLE"), "predicate_observation")
        _exact(self.condition, ConditionReference, "predicate_observation")
        _reference(self.operation_reference, "operation_context", 192)
        _reference(self.origin_assessment_reference, "origin_assessment")
        _reference(self.registry_id, "registry.source_binding", 128)
        _hash(self.registry_source_sha256, "registry.source_binding")
        _policy(self.policy_id, "predicate_observation")
        _choice(self.phase, ("APPLICABILITY", "ADDITIONAL_VALIDATION"), "predicate_observation")
        _exact(self.candidate_state_reference, state.AshState, "candidate_state")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _text(self.reason, "predicate_observation")


@dataclass(frozen=True, slots=True)
class EntryApplicability(_Record):
    policy_id: str
    observations: tuple[PredicateObservation, ...]
    unconsulted_conditions: tuple[ConditionReference, ...]
    def __post_init__(self):
        _policy(self.policy_id, "applicability")
        observations = _sequence(self.observations, lambda v, f: _exact(v, PredicateObservation, f), "applicability", 8)
        rest = _sequence(self.unconsulted_conditions, lambda v, f: _exact(v, ConditionReference, f), "applicability", 8)
        if len(observations) + len(rest) > 8 or any(v.policy_id != self.policy_id or v.phase != "APPLICABILITY" for v in observations):
            _fail("applicability")
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "unconsulted_conditions", rest)


@dataclass(frozen=True, slots=True)
class PostAssessmentFacts(_Record):
    diagnostic_context: state.DiagnosticContext
    context_observation: ContextObservation
    classification_evidence: state.ClassificationEvidence
    def __post_init__(self):
        _exact(self.diagnostic_context, state.DiagnosticContext, "post_assessment")
        _exact(self.context_observation, ContextObservation, "post_assessment.system_context")
        _exact(self.classification_evidence, state.ClassificationEvidence, "post_assessment.classification_evidence")


@dataclass(frozen=True, slots=True)
class UnavailablePostAssessmentFacts(_Record):
    operation_reference: str
    candidate_state_reference: state.AshState
    source_binding: EvidenceSourceBinding
    reason: str
    def __post_init__(self):
        _reference(self.operation_reference, "operation_context", 192)
        _exact(self.candidate_state_reference, state.AshState, "candidate_state")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _text(self.reason, "post_assessment")


@dataclass(frozen=True, slots=True)
class PostAssessmentLink(_Record):
    parent_operation_reference: str
    parent_action_reference: str
    originating_chain_root_reference: str
    def __post_init__(self):
        _reference(self.parent_operation_reference, "operation_context", 192)
        _reference(self.parent_action_reference, "action_decisions")
        _reference(self.originating_chain_root_reference, "origin_assessment")


@dataclass(frozen=True, slots=True)
class LinkedPostAssessment(_Record):
    link: PostAssessmentLink
    candidate_state: state.AshState
    context_observation: ContextObservation
    assessment: state.StateAssessment | state.ClassificationEvidenceFailure | state.DiagnosticCaptureFailure
    capture_status: str
    def __post_init__(self):
        _exact(self.link, PostAssessmentLink, "post_assessment")
        _exact(self.candidate_state, state.AshState, "candidate_state")
        _exact(self.context_observation, ContextObservation, "post_assessment.system_context")
        _exact(self.assessment, (state.StateAssessment, state.ClassificationEvidenceFailure, state.DiagnosticCaptureFailure), "post_assessment")
        _choice(self.capture_status, ("COMPLETE", "REJECTED", "NOT_CONFIRMED"), "post_assessment")
        if self.assessment.parsed_state != self.candidate_state or self.assessment.system_context != self.context_observation.context:
            _fail("post_assessment", "RECOVERY_BINDING_MISMATCH")
        if type(self.assessment) is state.DiagnosticCaptureFailure and self.capture_status == "COMPLETE":
            _fail("post_assessment")


@dataclass(frozen=True, slots=True)
class NormalizationResolutionObservation(_Record):
    availability: str
    operation_reference: str
    origin_assessment_reference: str
    source_binding: EvidenceSourceBinding
    reason: str
    def __post_init__(self):
        _choice(self.availability, ("READY", "UNAVAILABLE"), "normalization_preparation.resolution_observation")
        _reference(self.operation_reference, "operation_context", 192)
        _reference(self.origin_assessment_reference, "origin_assessment")
        _exact(self.source_binding, EvidenceSourceBinding, "source_binding")
        _text(self.reason, "normalization_preparation.resolution_observation")


@dataclass(frozen=True, slots=True)
class NormalizationErrorObservation(_Record):
    code: str
    field_name: str
    plan_validation: normalization.NormalizationPlanValidation | None
    reason: str
    def __post_init__(self):
        _choice(self.code, normalization.CONTRACT_CODES, "normalization_preparation")
        _choice(self.field_name, normalization.FIELD_NAMES, "normalization_preparation")
        _optional(self.plan_validation, normalization.NormalizationPlanValidation, "normalization_preparation.plan_validation")
        if type(self.reason) is not str or self.reason != "NORMALIZATION_PLANNING_REFUSED":
            _fail("normalization_preparation")


@dataclass(frozen=True, slots=True)
class NormalizationPreparation(_Record):
    status: str
    original_diagnosis: state.StateDiagnosis
    policy_binding: normalization.NormalizationPolicyBinding
    plan: normalization.NormalizationPlan | None
    plan_validation: normalization.NormalizationPlanValidation | None
    planning_error: NormalizationErrorObservation | None
    resolution_observation: NormalizationResolutionObservation
    def __post_init__(self):
        _choice(self.status, ("READY", "UNAVAILABLE", "REJECTED"), "normalization_preparation")
        _exact(self.original_diagnosis, state.StateDiagnosis, "normalization_preparation")
        _exact(self.policy_binding, normalization.NormalizationPolicyBinding, "normalization_preparation")
        _optional(self.plan, normalization.NormalizationPlan, "normalization_preparation.plan")
        _optional(self.plan_validation, normalization.NormalizationPlanValidation, "normalization_preparation.plan_validation")
        _optional(self.planning_error, NormalizationErrorObservation, "normalization_preparation")
        _exact(self.resolution_observation, NormalizationResolutionObservation, "normalization_preparation.resolution_observation")
        if self.plan is not None and (self.plan.original_diagnosis != self.original_diagnosis or self.plan.policy_binding != self.policy_binding):
            _fail("normalization_preparation.plan")
        if self.plan_validation is not None and (self.plan_validation.plan != self.plan or self.plan_validation.original_diagnosis != self.original_diagnosis):
            _fail("normalization_preparation.plan_validation")
        if self.status == "READY":
            if self.plan is None or self.plan_validation is None or self.plan_validation.validation_status != "VALIDATED" or self.planning_error is not None or self.resolution_observation.availability != "READY":
                _fail("normalization_preparation")
        elif self.status == "UNAVAILABLE":
            if self.plan is not None or self.plan_validation is not None or self.planning_error is not None or self.resolution_observation.availability != "UNAVAILABLE":
                _fail("normalization_preparation")
        elif self.planning_error is None and (self.plan_validation is None or self.plan_validation.validation_status != "REJECTED"):
            _fail("normalization_preparation")


@dataclass(frozen=True, slots=True)
class CorrectionObservation(_Record):
    submitted: KnownCorrection | UnavailableCorrection
    validation: CorrectionValidation | None
    def __post_init__(self):
        _exact(self.submitted, (KnownCorrection, UnavailableCorrection), "correction_observation.submitted")
        _optional(self.validation, CorrectionValidation, "correction_observation.validation")
        if type(self.submitted) is UnavailableCorrection and self.validation is not None:
            _fail("correction_observation.validation")
        if self.validation is not None and self.validation.submitted_correction != self.submitted:
            _fail("correction_observation.validation")


@dataclass(frozen=True, slots=True)
class RecoverySafetyPolicyBinding(_Record):
    policy_id: str
    policy_version: str
    source_path: str
    source_sha256: str
    def __post_init__(self):
        if any(type(getattr(self, n)) is not str or getattr(self, n) != value for n, value in RECOVERY_POLICY_BINDING_FIELDS):
            _fail("directive", "RECOVERY_BINDING_MISMATCH")


@dataclass(frozen=True, slots=True)
class ExternalEscalationRequired(_Record):
    authority_status: str
    trigger_domain: ClassVar[str] = "YWE_RECOVERABILITY_CATEGORY"
    recovery_category: ClassVar[str] = "ESCALATION_REQUIRED"
    _headers = (("trigger_domain", "YWE_RECOVERABILITY_CATEGORY"), ("recovery_category", "ESCALATION_REQUIRED"))
    def __post_init__(self):
        _choice(self.authority_status, ("REACHABLE", "UNREACHABLE", "UNAVAILABLE"), "directive")


@dataclass(frozen=True, slots=True)
class ExistingModeBoundary(_Record):
    observed_system_state_class: str
    observed_assessment_reference: str
    trigger_domain: ClassVar[str] = "YWE_OBSERVED_MODE_BOUNDARY"
    _headers = (("trigger_domain", "YWE_OBSERVED_MODE_BOUNDARY"),)
    def __post_init__(self):
        _choice(self.observed_system_state_class, ("CONTAINED", "SAFE_HALT"), "directive")
        _reference(self.observed_assessment_reference, "directive")


@dataclass(frozen=True, slots=True)
class RecoveryDirective(_Record):
    requested_action: str
    trigger: str | ExternalEscalationRequired | ExistingModeBoundary
    origin_assessment_reference: str
    causing_decision_reference: str
    evidence_references: tuple[str, ...]
    reason: str
    request_origin: str
    policy_binding: RecoverySafetyPolicyBinding | None
    actual_mode_status: ClassVar[str] = "NOT_ENTERED_BY_N2"
    _headers = (("actual_mode_status", "NOT_ENTERED_BY_N2"),)
    def __post_init__(self):
        _choice(self.requested_action, ("ENTER_CONTAINMENT", "REQUEST_EXTERNAL_AUTHORITY", "ENTER_SAFE_HALT", "REMAIN_CONTAINED", "REMAIN_SAFE_HALT"), "directive")
        _reference(self.origin_assessment_reference, "directive")
        _reference(self.causing_decision_reference, "directive")
        refs = _sequence(self.evidence_references, _reference, "directive", 8, 1)
        if len(set(refs)) != len(refs):
            _fail("directive")
        object.__setattr__(self, "evidence_references", refs)
        _text(self.reason, "directive")
        _choice(self.request_origin, ("POLICY", "SOURCE_RECOVERABILITY", "OBSERVED_EXISTING_MODE"), "directive")
        _optional(self.policy_binding, RecoverySafetyPolicyBinding, "directive")
        if self.requested_action == "ENTER_CONTAINMENT":
            _choice(self.trigger, CONTAINMENT_TRIGGERS, "directive")
        elif self.requested_action == "ENTER_SAFE_HALT":
            _choice(self.trigger, HALT_TRIGGERS, "directive")
        elif self.requested_action == "REQUEST_EXTERNAL_AUTHORITY":
            _exact(self.trigger, ExternalEscalationRequired, "directive")
        else:
            _exact(self.trigger, ExistingModeBoundary, "directive")
            wanted = "CONTAINED" if self.requested_action == "REMAIN_CONTAINED" else "SAFE_HALT"
            if self.trigger.observed_system_state_class != wanted or self.request_origin != "OBSERVED_EXISTING_MODE":
                _fail("directive")
        if (self.request_origin == "POLICY") != (self.policy_binding is not None):
            _fail("directive")
        if type(self.trigger) is str and self.trigger == "OPERATOR_REQUEST" and self.request_origin != "POLICY":
            _fail("directive")


@dataclass(frozen=True, slots=True)
class RecoveryStepEvidence(_Record):
    step_index: int
    action: str
    status: str
    before_state: state.AshState | None
    codeword: state.AshState | None
    after_state: state.AshState | None
    policy_id: str | None
    predicate_observation: PredicateObservation | None
    post_assessment_reference: str | None
    diagnostic_reference: str
    reason: str
    def __post_init__(self):
        _integer(self.step_index, 0, 767, "action_decisions")
        _choice(self.action, STEP_ACTIONS, "action_decisions")
        _choice(self.status, STATUSES, "action_decisions")
        for v in (self.before_state, self.codeword, self.after_state):
            _optional(v, state.AshState, "candidate_state")
        if self.policy_id is not None:
            _policy(self.policy_id, "action_decisions")
        _optional(self.predicate_observation, PredicateObservation, "predicate_observation")
        if self.post_assessment_reference is not None:
            _reference(self.post_assessment_reference, "post_assessment")
        _reference(self.diagnostic_reference, "emitted_diagnostics")
        _text(self.reason, "action_decisions")
        if self.action in ("NORMALIZE_XOR", "CORRECTION_XOR"):
            if any(v is None for v in (self.before_state, self.codeword, self.after_state)) or self.codeword.bits not in state.CANONICAL_CODEWORDS or tuple(a ^ b for a, b in zip(self.before_state.bits, self.codeword.bits)) != self.after_state.bits or self.status != "COMPLETED":
                _fail("candidate_state", "RECOVERY_PLAN_INVALID")
        elif self.codeword is not None:
            _fail("candidate_state")
        if self.action in ("CANDIDATE_APPLICABILITY", "CANDIDATE_VALIDATION"):
            expected = "APPLICABILITY" if self.action == "CANDIDATE_APPLICABILITY" else "ADDITIONAL_VALIDATION"
            if self.predicate_observation is None or self.predicate_observation.phase != expected or self.policy_id != self.predicate_observation.policy_id:
                _fail("predicate_observation")
        elif self.predicate_observation is not None:
            _fail("predicate_observation")
        if (self.action == "POST_ASSESSMENT") != (self.post_assessment_reference is not None):
            _fail("post_assessment")


@dataclass(frozen=True, slots=True)
class RecoveryStep(_Record):
    action: str
    status: str
    reason: str
    def __post_init__(self):
        _choice(self.action, CANONICAL_STEP_ACTIONS, "action_decisions")
        _choice(self.status, STATUSES, "action_decisions")
        _text(self.reason, "action_decisions")


@dataclass(frozen=True, slots=True)
class RecoveryDiagnostic(_Record):
    recovery_category: str
    original_state_class: str
    original_diagnostic: state.StateValidityDiagnostic
    steps: tuple[RecoveryStep, ...]
    outcome: str
    corrected_state: state.AshState | None
    fallback_policy_id: str | None
    reason: str
    rule_ids: tuple[str, ...]
    def __post_init__(self):
        if type(self.original_state_class) is not str or type(self.recovery_category) is not str or (self.original_state_class, self.recovery_category) not in state.RECOVERY_CATEGORY_PAIRS:
            _fail("action_decisions")
        _exact(self.original_diagnostic, state.StateValidityDiagnostic, "action_decisions")
        if any(r not in state.ASSESSMENT_RULE_IDS for r in self.original_diagnostic.rule_ids):
            _fail("action_decisions")
        object.__setattr__(self, "steps", _sequence(self.steps, lambda v, f: _exact(v, RecoveryStep, f), "action_decisions", 32))
        _choice(self.outcome, RECOVERY_OUTCOMES, "action_decisions")
        _optional(self.corrected_state, state.AshState, "candidate_state")
        if self.fallback_policy_id is not None:
            _policy(self.fallback_policy_id, "action_decisions")
        _text(self.reason, "action_decisions")
        rules = _sequence(self.rule_ids, lambda v, f: _choice(v, N2_RULE_IDS, f), "action_decisions", 5, 1)
        if len(set(rules)) != len(rules):
            _fail("action_decisions")
        object.__setattr__(self, "rule_ids", rules)
        if self.outcome in ("RECOVERED", "RECOVERED_VIA_FALLBACK") and self.corrected_state is None:
            _fail("candidate_state")
        if self.outcome == "RECOVERED_VIA_FALLBACK" and self.fallback_policy_id is None:
            _fail("action_decisions")


@dataclass(frozen=True, slots=True)
class RecoveryActionDecision(_Record):
    action_reference: str
    action: str
    diagnostic: RecoveryDiagnostic
    step_indices: tuple[int, ...]
    post_assessment_reference: str | None
    candidate_context: state.SystemContext | None
    directive: RecoveryDirective | None
    def __post_init__(self):
        _reference(self.action_reference, "action_decisions")
        _choice(self.action, ACTION_NAMES, "action_decisions")
        _exact(self.diagnostic, RecoveryDiagnostic, "action_decisions")
        indices = _sequence(self.step_indices, lambda v, f: _integer(v, 0, 767, f), "action_decisions", 768)
        if indices != tuple(sorted(set(indices))):
            _fail("action_decisions")
        object.__setattr__(self, "step_indices", indices)
        if self.post_assessment_reference is not None:
            _reference(self.post_assessment_reference, "post_assessment")
        _optional(self.candidate_context, state.SystemContext, "post_assessment.system_context")
        _optional(self.directive, RecoveryDirective, "directive")
        if self.action == "HANDOFF":
            if self.directive is None or self.directive.causing_decision_reference != self.action_reference:
                _fail("directive")
        elif self.directive is not None:
            _fail("directive")


@dataclass(frozen=True, slots=True)
class RecoveryRecord(_Record):
    diagnostic_reference: str
    envelope: state.DiagnosticEnvelope
    record_kind: str
    payload: RecoveryStepEvidence | RecoveryActionDecision
    def __post_init__(self):
        _reference(self.diagnostic_reference, "emitted_diagnostics")
        _exact(self.envelope, state.DiagnosticEnvelope, "emitted_diagnostics")
        try:
            state.DiagnosticEnvelope.__post_init__(self.envelope)
        except state.StateContractError:
            _fail("emitted_diagnostics")
        _choice(self.record_kind, ("ACTION_VALUE_COMPUTED", "OPERATION_DECISION"), "emitted_diagnostics")
        kind = RecoveryStepEvidence if self.record_kind == "ACTION_VALUE_COMPUTED" else RecoveryActionDecision
        _exact(self.payload, kind, "emitted_diagnostics")
        if any(r not in N2_RULE_IDS for r in self.envelope.rule_ids):
            _fail("emitted_diagnostics")
        if self.envelope.stage == "DETECTION":
            if self.record_kind != "OPERATION_DECISION" or self.payload.action != "HANDOFF" or self.payload.diagnostic.original_state_class != "SAFE_HALT" or self.payload.diagnostic.outcome != "NOT_APPLICABLE" or self.payload.directive.requested_action != "REMAIN_SAFE_HALT" or self.envelope.diagnostic_kind != "STATE_VALIDITY" or self.envelope.severity != "CRITICAL" or self.envelope.disposition != "BLOCKED" or self.envelope.chain_root_reference != self.diagnostic_reference or self.envelope.rule_ids != ("ASH-STATE-GENERAL-001", "ASH-RECOVERY-ACTION-001"):
                _fail("emitted_diagnostics")
        elif self.envelope.diagnostic_kind not in ("RECOVERY", "FALLBACK") or self.envelope.stage not in ("RECOVERY", "ESCALATION") or self.envelope.disposition == "TERMINAL":
            _fail("emitted_diagnostics")
        if self.diagnostic_reference in (self.envelope.parent_diagnostic_reference, self.envelope.chain_root_reference) and self.envelope.stage != "DETECTION":
            _fail("emitted_diagnostics")
        if self.record_kind == "ACTION_VALUE_COMPUTED" and self.payload.diagnostic_reference != self.diagnostic_reference:
            _fail("emitted_diagnostics")


@dataclass(frozen=True, slots=True)
class PolicyAttempt(_Record):
    policy_id: str
    applicability_observations: tuple[PredicateObservation, ...]
    unconsulted_applicability: tuple[ConditionReference, ...]
    validation_observations: tuple[PredicateObservation, ...]
    unconsulted_validation: tuple[ConditionReference, ...]
    post_assessment_reference: str | None
    decision_reference: str
    result: str
    def __post_init__(self):
        _policy(self.policy_id, "action_decisions")
        for name, phase in (("applicability_observations", "APPLICABILITY"), ("validation_observations", "ADDITIONAL_VALIDATION")):
            observations = _sequence(getattr(self, name), lambda v, f: _exact(v, PredicateObservation, f), "predicate_observation", 8)
            if any(v.policy_id != self.policy_id or v.phase != phase for v in observations):
                _fail("predicate_observation")
            object.__setattr__(self, name, observations)
        for name in ("unconsulted_applicability", "unconsulted_validation"):
            object.__setattr__(self, name, _sequence(getattr(self, name), lambda v, f: _exact(v, ConditionReference, f), "applicability", 8))
        if len(self.applicability_observations) + len(self.unconsulted_applicability) > 8 or len(self.validation_observations) + len(self.unconsulted_validation) > 8:
            _fail("applicability")
        if self.post_assessment_reference is not None:
            _reference(self.post_assessment_reference, "post_assessment")
        _reference(self.decision_reference, "action_decisions")
        _choice(self.result, ("INELIGIBLE", "RECOVERED", "VALIDATION_FAILED", "UNAVAILABLE", "LIFECYCLE_BOUNDARY"), "action_decisions")


@dataclass(frozen=True, slots=True)
class RecoveryFailureDetail(_Record):
    failure_code: str
    field_name: str
    submitted_evidence: AssessmentValidation | RegistryValidation | CorrectionValidation | NormalizationPreparation | PostAssessmentFacts | UnavailablePostAssessmentFacts | PredicateObservation | DiagnosticsCompletionReceipt | None
    attempted_diagnostic: RecoveryRecord | None
    capture_status: str | None
    pending_directive: RecoveryDirective | None
    reason: str
    completion_failure_code: str | None
    unconfirmed_completion_observation: DiagnosticsCompletionReceipt | None
    def __post_init__(self):
        _choice(self.failure_code, FAILURE_CODES, "capture")
        _choice(self.field_name, FIELD_NAMES, "capture")
        _optional(self.submitted_evidence, (AssessmentValidation, RegistryValidation, CorrectionValidation, NormalizationPreparation, PostAssessmentFacts, UnavailablePostAssessmentFacts, PredicateObservation, DiagnosticsCompletionReceipt), "capture")
        _optional(self.attempted_diagnostic, RecoveryRecord, "capture.append")
        if self.attempted_diagnostic is not None:
            RecoveryRecord.__post_init__(self.attempted_diagnostic)
        if self.capture_status is not None:
            _choice(self.capture_status, ("REJECTED", "NOT_CONFIRMED"), "capture.append")
        _optional(self.pending_directive, RecoveryDirective, "directive")
        _text(self.reason, "capture")
        if self.completion_failure_code is not None:
            _choice(self.completion_failure_code, COMPLETION_FAILURE_CODES, "capture.finish")
        _optional(self.unconfirmed_completion_observation, DiagnosticsCompletionReceipt, "capture.finish")
        if self.unconfirmed_completion_observation is not None and self.completion_failure_code != "COMPLETION_UNCONFIRMED":
            _fail("capture.finish")


@dataclass(frozen=True, slots=True)
class RecoveryPacketCommon(_Record):
    operation_context: RecoveryOperationContext
    origin_assessment: state.StateAssessment
    origin_validation: AssessmentValidation
    source_binding: RecoverySourceBinding
    registry_binding: RegistrySourceBinding | None
    route_authorization: FallbackRouteAuthorization | None
    steps: tuple[RecoveryStepEvidence, ...]
    post_assessments: tuple[LinkedPostAssessment, ...]
    policy_attempts: tuple[PolicyAttempt, ...]
    action_decisions: tuple[RecoveryActionDecision, ...]
    emitted_diagnostics: tuple[RecoveryRecord, ...]
    candidate_state: state.AshState | None
    directive: RecoveryDirective | None
    failure_detail: RecoveryFailureDetail | None
    normalization_preparation: NormalizationPreparation | None
    correction_observation: CorrectionObservation | None
    registry_snapshot: AvailableFallbackRegistry | UnavailableFallbackRegistry | None
    registry_validation: RegistryValidation | None
    completion_observation: DiagnosticsCompletionReceipt | None
    schema_ref: ClassVar[str] = "data/schemas/m3_recovery_value_schema.json"
    artifact_type: ClassVar[str] = "ywe_recovery_value"
    artifact_version: ClassVar[str] = "1.0.0"
    execution_scope: ClassVar[str] = "CORE_REFERENCE_IMMUTABLE_VALUE"
    session_effects_performed: ClassVar[bool] = False
    outcome: ClassVar[str]
    def __post_init__(self):
        if type(self) is RecoveryPacketCommon:
            _fail("capture")
        _exact(self.operation_context, RecoveryOperationContext, "operation_context")
        _exact(self.origin_assessment, state.StateAssessment, "origin_assessment")
        _exact(self.origin_validation, AssessmentValidation, "origin_validation")
        _exact(self.source_binding, RecoverySourceBinding, "source_binding")
        RecoverySourceBinding.__post_init__(self.source_binding)
        if self.origin_validation.submitted_assessment != self.origin_assessment or self.operation_context.origin_assessment_reference != self.origin_assessment.assessment_binding.assessment_reference or self.operation_context.context_observation.context != self.origin_assessment.system_context or self.source_binding.canonical_binding != self.origin_validation.current_source_binding:
            _fail("origin_validation", "RECOVERY_BINDING_MISMATCH")
        for name, kind, maximum in (("steps", RecoveryStepEvidence, 768), ("post_assessments", LinkedPostAssessment, 33), ("policy_attempts", PolicyAttempt, 32), ("action_decisions", RecoveryActionDecision, 35), ("emitted_diagnostics", RecoveryRecord, 768)):
            field = "action_decisions" if name in ("steps", "policy_attempts") else ("post_assessment" if name == "post_assessments" else name)
            object.__setattr__(self, name, _sequence(getattr(self, name), lambda v, f, k=kind: _exact(v, k, f), field, maximum))
        for record in self.emitted_diagnostics:
            RecoveryRecord.__post_init__(record)
        if tuple(s.step_index for s in self.steps) != tuple(range(len(self.steps))):
            _fail("action_decisions")
        for name, kinds in (("registry_binding", RegistrySourceBinding), ("route_authorization", FallbackRouteAuthorization), ("candidate_state", state.AshState), ("directive", RecoveryDirective), ("failure_detail", RecoveryFailureDetail), ("normalization_preparation", NormalizationPreparation), ("correction_observation", CorrectionObservation), ("registry_snapshot", (AvailableFallbackRegistry, UnavailableFallbackRegistry)), ("registry_validation", RegistryValidation), ("completion_observation", DiagnosticsCompletionReceipt)):
            field = {"failure_detail": "capture", "completion_observation": "capture.finish", "registry_binding": "registry.source_binding", "registry_snapshot": "registry"}.get(name, name)
            _optional(getattr(self, name), kinds, field)
        if self.failure_detail is not None:
            RecoveryFailureDetail.__post_init__(self.failure_detail)
        if any(a.diagnostic.original_state_class != self.origin_assessment.system_state_class or a.diagnostic.recovery_category != self.origin_assessment.recovery_category or a.diagnostic.original_diagnostic != self.origin_assessment.state_validity_diagnostic or any(i >= len(self.steps) for i in a.step_indices) for a in self.action_decisions):
            _fail("action_decisions")
        ids = [r.diagnostic_reference for r in self.emitted_diagnostics]
        if len(set(ids)) != len(ids):
            _fail("emitted_diagnostics")
        if any(r.payload not in (self.steps if r.record_kind == "ACTION_VALUE_COMPUTED" else self.action_decisions) for r in self.emitted_diagnostics):
            _fail("emitted_diagnostics")
        denial = self.origin_assessment.system_state_class == "SAFE_HALT"
        if denial:
            if len(self.emitted_diagnostics) > 1 or any(r.envelope.stage != "DETECTION" or r.envelope.subject_reference != self.origin_assessment.subject_reference for r in self.emitted_diagnostics):
                _fail("emitted_diagnostics")
        elif self.emitted_diagnostics:
            if not self.origin_assessment.emitted_diagnostics:
                _fail("emitted_diagnostics")
            previous = self.origin_assessment.emitted_diagnostics[-1].diagnostic_reference
            floor = self.origin_assessment.emitted_diagnostics[-1].envelope.severity
            severity_order = ("INFO", "WARNING", "ERROR", "CRITICAL")
            for record in self.emitted_diagnostics:
                envelope = record.envelope
                if envelope.stage == "DETECTION" or envelope.subject_reference != self.origin_assessment.subject_reference or envelope.chain_root_reference != self.origin_assessment.assessment_binding.diagnosis_reference or envelope.parent_diagnostic_reference != previous or severity_order.index(envelope.severity) < severity_order.index(floor):
                    _fail("emitted_diagnostics")
                previous, floor = record.diagnostic_reference, envelope.severity
        if self.outcome != "FAILURE" and (len(self.emitted_diagnostics) != len(self.steps) + len(self.action_decisions) or any(not any(record.payload == value for record in self.emitted_diagnostics) for value in (*self.steps, *self.action_decisions))):
            _fail("emitted_diagnostics")
        if (self.registry_snapshot is None) != (self.registry_validation is None) or (self.registry_snapshot is None) != (self.registry_binding is None):
            _fail("registry_validation")
        if self.registry_snapshot is not None and (self.registry_binding != self.registry_snapshot.source_binding or self.registry_validation.submitted_snapshot != self.registry_snapshot or self.registry_validation.current_source_binding != self.source_binding.canonical_binding or self.registry_validation.current_profile_binding != self.origin_validation.current_profile_binding):
            _fail("registry_validation", "RECOVERY_BINDING_MISMATCH")
        if self.route_authorization is not None and (self.route_authorization.original_system_state_class != self.origin_assessment.system_state_class or self.route_authorization.origin_assessment_reference != self.origin_assessment.assessment_binding.assessment_reference):
            _fail("route_authorization")
        if self.route_authorization is not None:
            if self.route_authorization.route == "AFTER_CORRECTION_FAILURE" and self.correction_observation is None:
                _fail("correction_observation")
            if self.route_authorization.route == "AFTER_NORMALIZATION_FAILURE" and (self.normalization_preparation is None or self.normalization_preparation.status != "READY"):
                _fail("normalization_preparation")
        for p in self.post_assessments:
            if p.link.parent_operation_reference != self.operation_context.operation_reference or p.link.originating_chain_root_reference != self.origin_assessment.assessment_binding.diagnosis_reference:
                _fail("post_assessment", "RECOVERY_BINDING_MISMATCH")
        if self.completion_observation is not None and self.completion_observation.operation_reference != self.operation_context.operation_reference:
            _fail("capture.finish", "RECOVERY_BINDING_MISMATCH")
        if self.outcome == "FAILURE":
            if self.failure_detail is None:
                _fail("capture")
            if self.failure_detail.pending_directive != self.directive:
                _fail("directive")
            if self.failure_detail.failure_code == "ORIGIN_REJECTED" and (self.origin_validation.status != "REJECTED" or any((self.steps, self.post_assessments, self.action_decisions, self.emitted_diagnostics)) or self.directive is not None or self.registry_snapshot is not None):
                _fail("origin_validation")
        elif self.origin_validation.status != "VERIFIED" or self.failure_detail is not None:
            _fail("origin_validation")
        if self.outcome == "HANDOFF_REQUIRED":
            if self.directive is None or not any(a.directive == self.directive for a in self.action_decisions):
                _fail("directive")
        elif self.outcome != "FAILURE" and self.directive is not None:
            _fail("directive")
        if self.outcome == "NO_ACTION":
            if self.origin_assessment.system_state_class != "STABLE" or self.candidate_state != self.origin_assessment.parsed_state or len(self.action_decisions) != 1 or self.action_decisions[0].action != "NO_ACTION" or self.action_decisions[0].diagnostic.outcome != "NOT_APPLICABLE" or any((self.steps, self.post_assessments, self.policy_attempts)) or any(value is not None for value in (self.normalization_preparation, self.correction_observation, self.registry_snapshot, self.route_authorization)):
                _fail("candidate_state")
        if self.outcome in ("RECOVERED_VALUE", "RECOVERED_FALLBACK_VALUE"):
            if self.candidate_state is None or not any(type(p.assessment) is state.StateAssessment and p.capture_status == "COMPLETE" and p.candidate_state == self.candidate_state and p.assessment.system_state_class == "STABLE" and p.assessment.state_validity_diagnostic.is_valid and p.assessment.profile_binding == self.origin_validation.current_profile_binding and p.assessment.source_binding == self.source_binding.canonical_binding for p in self.post_assessments):
                _fail("post_assessment")
            expected = "RECOVERED" if self.outcome == "RECOVERED_VALUE" else "RECOVERED_VIA_FALLBACK"
            decisions = [a for a in self.action_decisions if a.diagnostic.outcome == expected and a.diagnostic.corrected_state == self.candidate_state]
            if not decisions or not any(r.record_kind == "OPERATION_DECISION" and r.payload in decisions for r in self.emitted_diagnostics):
                _fail("emitted_diagnostics")
            if not any(any(p.link.parent_action_reference == a.action_reference and p.assessment.assessment_binding.assessment_reference == a.post_assessment_reference and p.candidate_state == self.candidate_state and p.capture_status == "COMPLETE" and type(p.assessment) is state.StateAssessment and p.assessment.system_state_class == "STABLE" and p.context_observation.context == a.candidate_context for p in self.post_assessments) for a in decisions):
                _fail("post_assessment", "RECOVERY_BINDING_MISMATCH")
            if self.outcome == "RECOVERED_VALUE" and self.origin_assessment.system_state_class not in ("UNSTABLE", "CORRECTABLE"):
                _fail("origin_assessment")
            if self.outcome == "RECOVERED_VALUE":
                if self.origin_assessment.system_state_class == "UNSTABLE":
                    if self.normalization_preparation is None or self.normalization_preparation.status != "READY" or not any(a.action == "NORMALIZE" for a in decisions):
                        _fail("normalization_preparation")
                elif self.correction_observation is None or type(self.correction_observation.submitted) is not KnownCorrection or self.correction_observation.validation is None or self.correction_observation.validation.status != "VERIFIED" or not any(a.action == "CORRECT" for a in decisions):
                    _fail("correction_observation")
            if self.outcome == "RECOVERED_FALLBACK_VALUE" and (self.registry_snapshot is None or self.registry_validation.status != "VERIFIED" or self.route_authorization is None):
                _fail("registry_validation")
        if self.completion_observation is not None and self.completion_observation.status == "INCOMPLETE" and (self.outcome != "FAILURE" or self.failure_detail.completion_failure_code != "COMPLETION_REJECTED"):
            _fail("capture.finish")

    def to_record(self):
        return {"schema_ref": self.schema_ref, "artifact_type": self.artifact_type, "artifact_version": self.artifact_version, "outcome": self.outcome, "execution_scope": self.execution_scope,
                **{f.name: _record(getattr(self, f.name)) for f in fields(self)}, "session_effects_performed": self.session_effects_performed}


@dataclass(frozen=True, slots=True)
class RecoveryNoAction(RecoveryPacketCommon):
    outcome: ClassVar[str] = "NO_ACTION"


@dataclass(frozen=True, slots=True)
class RecoveredValue(RecoveryPacketCommon):
    outcome: ClassVar[str] = "RECOVERED_VALUE"


@dataclass(frozen=True, slots=True)
class RecoveredFallbackValue(RecoveryPacketCommon):
    outcome: ClassVar[str] = "RECOVERED_FALLBACK_VALUE"


@dataclass(frozen=True, slots=True)
class RecoveryHandoff(RecoveryPacketCommon):
    outcome: ClassVar[str] = "HANDOFF_REQUIRED"


@dataclass(frozen=True, slots=True)
class RecoveryFailure(RecoveryPacketCommon):
    outcome: ClassVar[str] = "FAILURE"


RecoveryValuePacket = RecoveryNoAction | RecoveredValue | RecoveredFallbackValue | RecoveryHandoff | RecoveryFailure
