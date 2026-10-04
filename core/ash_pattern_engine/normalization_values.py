"""Immutable N1 normalization records [YWE-REQ-0040].

The adopted contract is docs/architecture/m3_normalization_contract.md.
Complete origin/target mathematics and capture observation belong to StateModel;
these values own bounded construction and coherent retained record snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import ClassVar

from . import state_values as values


NORMALIZATION_POLICY_BINDING_FIELDS = (
    ("policy_id", "YWE-NORMALIZE-LEXICOGRAPHIC-001"),
    ("policy_version", "1.0.0"),
    ("source_reference", "docs/architecture/m3_normalization_policy.md"),
    ("source_sha256", "804eec92cf52b465b7aaf0cb5f139f581ac2899d13203a8c4cfe9f4d7579c383"),
)
CONTRACT_CODES = frozenset((
    "NORMALIZATION_CONFIG_INVALID", "NORMALIZATION_CONTEXT_INVALID",
    "NORMALIZATION_POLICY_INVALID", "NORMALIZATION_PLAN_INVALID",
))
ORIGIN_CODES = frozenset((
    "NORMALIZATION_BINDING_MISMATCH", "NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH",
))
PLAN_VALIDATION_CODES = ORIGIN_CODES | frozenset((
    "NORMALIZATION_TARGET_SET_MISMATCH", "NORMALIZATION_SELECTION_MISMATCH",
    "NORMALIZATION_CODEWORD_MISMATCH",
))
FAILURE_CODES = PLAN_VALIDATION_CODES | frozenset((
    "NORMALIZATION_INPUT_REJECTED", "NORMALIZATION_PROFILE_UNAVAILABLE",
    "NORMALIZATION_NO_TARGET", "NORMALIZATION_POST_VALIDATION_FAILED",
    "DIAGNOSTIC_CAPTURE_REJECTED", "DIAGNOSTIC_CAPTURE_UNCONFIRMED",
))
FIELD_NAMES = frozenset((
    "normalization_capture", "normalization_context", "policy_binding", "plan",
    "plan_validation", "plan_reference", "evidence_reference", "decision",
    "original_diagnosis", "original_diagnosis.source_binding",
    "original_diagnosis.profile_binding", "original_diagnosis.assessment_binding",
    "original_diagnosis.input_evidence", "original_diagnosis.parsed_state",
    "original_diagnosis.state_validity_diagnostic", "original_diagnosis.emitted_diagnostics",
    "eligible_targets_complete", "eligible_targets", "selected_target", "codeword_chain",
    "reason_code", "step_index", "input_state", "codeword", "actual_state", "phase",
    "emission", "emission.envelope", "emission.envelope.rule_ids",
    "emission.diagnostic_reference", "operation_reference", "computation_reference",
    "post_validation_reference", "inherited_diagnostics", "emitted_diagnostics", "steps",
    "post_validity_diagnostic", "normalized_state", "origin_validation_status",
    "validation_status", "failure_code", "field_name", "expected_decision",
    "recomputed_eligible_targets", "recomputed_target", "recomputed_codeword_chain",
    "policy_binding.policy_id", "policy_binding.policy_version", "policy_binding.source_reference",
    "policy_binding.source_sha256", "canonical_binding", "profile_binding",
    "state_validity_diagnostic", "step", "outcome", "operation_binding", "failure_kind",
    "failed_field", "capture_status", "attempted_diagnostic", "submitted_plan", "validation",
))
_BINDING_FIELDS = frozenset(("original_diagnosis.source_binding", "original_diagnosis.profile_binding"))
_ORIGINAL_FIELDS = frozenset((
    "original_diagnosis.assessment_binding", "original_diagnosis.input_evidence",
    "original_diagnosis.parsed_state", "original_diagnosis.state_validity_diagnostic",
    "original_diagnosis.emitted_diagnostics",
))
_DECISIONS = ("ALREADY_VALID", "PLAN_READY", "NOT_NORMALIZABLE", "BLOCKED")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}\Z")
_SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")


class NormalizationContractError(ValueError):
    """A bounded precondition failure, retaining an owned comparison if present."""

    def __init__(self, code, field_name, *, submitted_plan=None, validation=None):
        invalid = "invalid NormalizationContractError construction"
        if type(code) is not str or code not in CONTRACT_CODES:
            raise ValueError(invalid)
        if type(field_name) is not str or field_name not in FIELD_NAMES:
            raise ValueError(invalid)
        if submitted_plan is not None and type(submitted_plan) is not NormalizationPlan:
            raise ValueError(invalid)
        if validation is not None:
            if type(validation) is not NormalizationPlanValidation:
                raise ValueError(invalid)
            if validation.plan != submitted_plan or validation.field_name != field_name:
                raise ValueError(invalid)
            if validation.origin_validation_status == "NOT_EVALUATED":
                if validation.failure_code != code:
                    raise ValueError(invalid)
            elif not (code == "NORMALIZATION_PLAN_INVALID" and submitted_plan is None
                      and validation.origin_validation_status == "REJECTED"
                      and validation.failure_code in ORIGIN_CODES):
                raise ValueError(invalid)
        self.code = code
        self.field_name = field_name
        self.submitted_plan = submitted_plan
        self.validation = validation
        self.emitted_diagnostics = ()
        super().__init__(f"{code}: {field_name}")


def _exact(value, expected, field, code="NORMALIZATION_PLAN_INVALID"):
    allowed = expected if type(expected) is tuple else (expected,)
    if not any(type(value) is kind for kind in allowed):
        raise NormalizationContractError(code, field)


def _choice(value, choices, field, code="NORMALIZATION_PLAN_INVALID"):
    if type(value) is not str or value not in choices:
        raise NormalizationContractError(code, field)


def _reference(value, field, code="NORMALIZATION_PLAN_INVALID"):
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None or value in ("NONE", "SELF"):
        raise NormalizationContractError(code, field)


def _sequence(value, member_type, field, maximum, *, codewords=False, sorted_unique=False):
    _exact(value, (list, tuple), field)
    if len(value) > maximum:
        raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", field)
    for member in value:
        _exact(member, member_type, field)
        if codewords and member.bits not in values.CANONICAL_CODEWORDS:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", field)
    result = tuple(value)
    if sorted_unique:
        signatures = tuple(member.signature for member in result)
        if signatures != tuple(sorted(set(signatures))):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", field)
    return result


def _optional_state(value, field):
    if value is not None:
        _exact(value, values.AshState, field)


def _state_record(value):
    return None if value is None else value.to_record()


@dataclass(frozen=True, slots=True)
class NormalizationPolicyBinding:
    policy_id: str
    policy_version: str
    source_reference: str
    source_sha256: str

    def __post_init__(self):
        for field, expected in NORMALIZATION_POLICY_BINDING_FIELDS:
            value = getattr(self, field)
            if type(value) is not str or value != expected:
                raise NormalizationContractError("NORMALIZATION_POLICY_INVALID", "policy_binding." + field)

    def to_record(self):
        return {field: getattr(self, field) for field, _ in NORMALIZATION_POLICY_BINDING_FIELDS}


@dataclass(frozen=True, slots=True)
class NormalizationPlan:
    plan_reference: str
    evidence_reference: str
    policy_binding: NormalizationPolicyBinding
    original_diagnosis: values.StateDiagnosis
    decision: str
    eligible_targets_complete: bool
    eligible_targets: tuple[values.AshState, ...]
    selected_target: values.AshState | None
    codeword_chain: tuple[values.AshState, ...]
    reason_code: str
    schema_ref: ClassVar[str] = "data/schemas/m3_normalization_plan_schema.json"
    artifact_type: ClassVar[str] = "ywe_state_normalization_plan"
    artifact_version: ClassVar[str] = "1.0.0"

    def __post_init__(self):
        _reference(self.plan_reference, "plan_reference")
        _reference(self.evidence_reference, "evidence_reference")
        _exact(self.policy_binding, NormalizationPolicyBinding, "policy_binding")
        _exact(self.original_diagnosis, values.StateDiagnosis, "original_diagnosis")
        _choice(self.decision, _DECISIONS, "decision")
        _exact(self.eligible_targets_complete, bool, "eligible_targets_complete")
        targets = _sequence(self.eligible_targets, values.AshState, "eligible_targets", 16, sorted_unique=True)
        chain = _sequence(self.codeword_chain, values.AshState, "codeword_chain", 1, codewords=True)
        object.__setattr__(self, "eligible_targets", targets)
        object.__setattr__(self, "codeword_chain", chain)
        _optional_state(self.selected_target, "selected_target")
        status = self.original_diagnosis.state_validity_diagnostic.admissibility_status
        if self.decision == "BLOCKED":
            if self.eligible_targets_complete or targets or chain or self.selected_target is not None or status != "UNCLASSIFIED":
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "decision")
            expected = ("NORMALIZATION_INPUT_REJECTED" if self.original_diagnosis.parsed_state is None
                        else "NORMALIZATION_PROFILE_UNAVAILABLE")
        elif self.decision == "NOT_NORMALIZABLE":
            if not self.eligible_targets_complete or targets or chain or self.selected_target is not None or status != "TRANSFORMATION_INCOMPATIBLE":
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "decision")
            expected = "NORMALIZATION_NO_TARGET"
        else:
            expected_status = "VALID" if self.decision == "ALREADY_VALID" else "TRANSFORMATION_COMPATIBLE"
            if (not self.eligible_targets_complete or not targets or self.selected_target is None
                    or len(chain) != (0 if self.decision == "ALREADY_VALID" else 1) or status != expected_status):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "decision")
            expected = "NORMALIZATION_ALREADY_VALID" if self.decision == "ALREADY_VALID" else "NORMALIZATION_PLAN_READY"
        _choice(self.reason_code, (expected,), "reason_code")

    def to_record(self):
        return {"schema_ref": self.schema_ref, "artifact_type": self.artifact_type,
                "artifact_version": self.artifact_version, "plan_reference": self.plan_reference,
                "evidence_reference": self.evidence_reference, "policy_binding": self.policy_binding.to_record(),
                "original_diagnosis": self.original_diagnosis.to_record(), "decision": self.decision,
                "eligible_targets_complete": self.eligible_targets_complete,
                "eligible_targets": [state.to_record() for state in self.eligible_targets],
                "selected_target": _state_record(self.selected_target),
                "codeword_chain": [state.to_record() for state in self.codeword_chain],
                "reason_code": self.reason_code}


@dataclass(frozen=True, slots=True)
class NormalizationPlanValidation:
    plan: NormalizationPlan | None
    original_diagnosis: values.StateDiagnosis
    canonical_binding: values.CanonicalAshBinding
    profile_binding: values.ProfileBinding
    origin_validation_status: str
    validation_status: str
    failure_code: str | None
    field_name: str | None
    expected_decision: str | None
    recomputed_eligible_targets: tuple[values.AshState, ...] | None
    recomputed_target: values.AshState | None
    recomputed_codeword_chain: tuple[values.AshState, ...] | None

    def __post_init__(self):
        if self.plan is not None:
            _exact(self.plan, NormalizationPlan, "plan")
        _exact(self.original_diagnosis, values.StateDiagnosis, "original_diagnosis")
        if self.plan is not None and self.original_diagnosis != self.plan.original_diagnosis:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "original_diagnosis")
        _exact(self.canonical_binding, values.CanonicalAshBinding, "canonical_binding")
        _exact(self.profile_binding, (values.AvailableProfileBinding, values.UnavailableProfileBinding), "profile_binding")
        _choice(self.origin_validation_status, ("NOT_EVALUATED", "REJECTED", "VERIFIED"), "origin_validation_status")
        _choice(self.validation_status, ("VALIDATED", "REJECTED"), "validation_status")
        if self.validation_status == "VALIDATED":
            if self.failure_code is not None or self.field_name is not None:
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "failure_code")
        else:
            _choice(self.field_name, FIELD_NAMES, "field_name")
        if self.origin_validation_status != "VERIFIED":
            if (self.validation_status != "REJECTED" or any(value is not None for value in
                    (self.expected_decision, self.recomputed_eligible_targets, self.recomputed_target,
                     self.recomputed_codeword_chain))):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "origin_validation_status")
            codes = CONTRACT_CODES if self.origin_validation_status == "NOT_EVALUATED" else ORIGIN_CODES
            _choice(self.failure_code, codes, "failure_code")
            if self.origin_validation_status == "REJECTED":
                fields = _BINDING_FIELDS if self.failure_code == "NORMALIZATION_BINDING_MISMATCH" else _ORIGINAL_FIELDS
                _choice(self.field_name, fields, "field_name")
                if self.failure_code == "NORMALIZATION_BINDING_MISMATCH":
                    submitted, current = ((self.original_diagnosis.source_binding, self.canonical_binding)
                                          if self.field_name == "original_diagnosis.source_binding"
                                          else (self.original_diagnosis.profile_binding, self.profile_binding))
                    if submitted == current:
                        raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "origin_validation_status")
            return
        if self.plan is None:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "plan")
        if (self.canonical_binding != self.original_diagnosis.source_binding
                or self.profile_binding != self.original_diagnosis.profile_binding):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "origin_validation_status")
        _choice(self.expected_decision, _DECISIONS, "expected_decision")
        if self.recomputed_eligible_targets is not None:
            object.__setattr__(self, "recomputed_eligible_targets", _sequence(
                self.recomputed_eligible_targets, values.AshState, "recomputed_eligible_targets", 16, sorted_unique=True))
        if self.recomputed_codeword_chain is not None:
            object.__setattr__(self, "recomputed_codeword_chain", _sequence(
                self.recomputed_codeword_chain, values.AshState, "recomputed_codeword_chain", 1, codewords=True))
        _optional_state(self.recomputed_target, "recomputed_target")
        if self.expected_decision == "BLOCKED":
            if any(value is not None for value in (self.recomputed_eligible_targets, self.recomputed_target,
                                                   self.recomputed_codeword_chain)):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "expected_decision")
        elif self.expected_decision == "NOT_NORMALIZABLE":
            if self.recomputed_eligible_targets != () or self.recomputed_target is not None or self.recomputed_codeword_chain != ():
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "expected_decision")
        elif (not self.recomputed_eligible_targets or self.recomputed_target is None
              or self.recomputed_codeword_chain is None
              or len(self.recomputed_codeword_chain) != (0 if self.expected_decision == "ALREADY_VALID" else 1)):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "expected_decision")
        if self.validation_status == "REJECTED":
            _choice(self.failure_code, PLAN_VALIDATION_CODES - ORIGIN_CODES, "failure_code")
        else:
            actual = (self.plan.decision, self.plan.eligible_targets, self.plan.selected_target, self.plan.codeword_chain)
            expected = (self.expected_decision, self.recomputed_eligible_targets,
                        self.recomputed_target, self.recomputed_codeword_chain)
            if self.expected_decision == "BLOCKED":
                expected = ("BLOCKED", (), None, ())
            if actual != expected:
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "plan_validation")

    def to_record(self):
        return {"plan": None if self.plan is None else self.plan.to_record(),
                "original_diagnosis": self.original_diagnosis.to_record(),
                "canonical_binding": self.canonical_binding.to_record(),
                "profile_binding": self.profile_binding.to_record(),
                "origin_validation_status": self.origin_validation_status,
                "validation_status": self.validation_status, "failure_code": self.failure_code,
                "field_name": self.field_name, "expected_decision": self.expected_decision,
                "recomputed_eligible_targets": None if self.recomputed_eligible_targets is None else
                    [state.to_record() for state in self.recomputed_eligible_targets],
                "recomputed_target": _state_record(self.recomputed_target),
                "recomputed_codeword_chain": None if self.recomputed_codeword_chain is None else
                    [state.to_record() for state in self.recomputed_codeword_chain]}


@dataclass(frozen=True, slots=True)
class NormalizationContext:
    operation_reference: str
    computation_reference: str
    post_validation_reference: str

    def __post_init__(self):
        for field in ("operation_reference", "computation_reference", "post_validation_reference"):
            _reference(getattr(self, field), field, "NORMALIZATION_CONTEXT_INVALID")
        if self.computation_reference == self.post_validation_reference:
            raise NormalizationContractError("NORMALIZATION_CONTEXT_INVALID", "normalization_context")

    def to_record(self):
        return {"operation_reference": self.operation_reference,
                "computation_reference": self.computation_reference,
                "post_validation_reference": self.post_validation_reference}


@dataclass(frozen=True, slots=True)
class NormalizationStep:
    step_index: int
    input_state: values.AshState
    codeword: values.AshState
    actual_state: values.AshState

    def __post_init__(self):
        if type(self.step_index) is not int or self.step_index != 0:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "step_index")
        for field in ("input_state", "codeword", "actual_state"):
            _exact(getattr(self, field), values.AshState, field)
        if self.codeword.bits not in values.CANONICAL_CODEWORDS:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "codeword")
        if tuple(a ^ b for a, b in zip(self.input_state.bits, self.codeword.bits)) != self.actual_state.bits:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "actual_state")

    def to_record(self):
        return {"step_index": self.step_index, "input_state": self.input_state.to_record(),
                "codeword": self.codeword.to_record(), "actual_state": self.actual_state.to_record()}


@dataclass(frozen=True, slots=True)
class NormalizationDiagnosticRecord:
    emission: values.DiagnosticEmission
    phase: str
    state_validity_diagnostic: values.StateValidityDiagnostic
    step: NormalizationStep | None

    def __post_init__(self):
        _exact(self.emission, values.DiagnosticEmission, "emission")
        _choice(self.phase, ("COMPUTATION", "POST_VALIDATION"), "phase")
        _exact(self.state_validity_diagnostic, values.StateValidityDiagnostic, "state_validity_diagnostic")
        if any(rule not in values.ASSESSMENT_RULE_IDS for rule in self.state_validity_diagnostic.rule_ids):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "state_validity_diagnostic")
        envelope = self.emission.envelope
        if envelope.diagnostic_kind != "STATE_VALIDITY" or envelope.stage != "RECOVERY":
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emission.envelope")
        if self.step is not None:
            _exact(self.step, NormalizationStep, "step")
            expected = self.step.input_state if self.phase == "COMPUTATION" else self.step.actual_state
            if self.state_validity_diagnostic.input_state != expected:
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "state_validity_diagnostic")

    def to_record(self):
        return {"emission": self.emission.to_record(), "phase": self.phase,
                "state_validity_diagnostic": self.state_validity_diagnostic.to_record(),
                "step": None if self.step is None else self.step.to_record()}


class _NormalizationPacket:
    __slots__ = ()
    schema_ref: ClassVar[str] = "data/schemas/m3_state_normalization_schema.json"
    artifact_type: ClassVar[str] = "ywe_state_normalization"
    artifact_version: ClassVar[str] = "1.0.0"

    def _validate_common(self):
        _exact(self.operation_binding, NormalizationContext, "operation_binding")
        _exact(self.plan, NormalizationPlan, "plan")
        _exact(self.plan_validation, NormalizationPlanValidation, "plan_validation")
        _exact(self.original_diagnosis, values.StateDiagnosis, "original_diagnosis")
        if (self.plan_validation.plan != self.plan or self.original_diagnosis != self.plan.original_diagnosis
                or self.plan_validation.original_diagnosis != self.original_diagnosis):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "plan_validation")
        root = self.original_diagnosis.assessment_binding.diagnosis_reference
        if root in (self.operation_binding.computation_reference, self.operation_binding.post_validation_reference):
            raise NormalizationContractError("NORMALIZATION_CONTEXT_INVALID", "normalization_context")
        _optional_state(self.actual_state, "actual_state")
        _optional_state(self.normalized_state, "normalized_state")
        if self.post_validity_diagnostic is not None:
            _exact(self.post_validity_diagnostic, values.StateValidityDiagnostic, "post_validity_diagnostic")
            if (self.actual_state is None or self.post_validity_diagnostic.input_state != self.actual_state
                    or any(rule not in values.ASSESSMENT_RULE_IDS for rule in self.post_validity_diagnostic.rule_ids)):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "post_validity_diagnostic")
        for field, member, maximum in (("steps", NormalizationStep, 1),
                                       ("inherited_diagnostics", values.DiagnosticEmission, 1),
                                       ("emitted_diagnostics", NormalizationDiagnosticRecord, 2)):
            object.__setattr__(self, field, _sequence(getattr(self, field), member, field, maximum))
        if self.steps:
            step = self.steps[0]
            if (step.input_state != self.original_diagnosis.parsed_state or step.actual_state != self.actual_state
                    or self.plan.codeword_chain != (step.codeword,)):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "steps")
        elif self.actual_state != self.original_diagnosis.parsed_state:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "actual_state")
        if self.normalized_state is not None and self.normalized_state != self.actual_state:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "normalized_state")
        if self.plan_validation.origin_validation_status == "VERIFIED":
            if self.inherited_diagnostics != self.original_diagnosis.emitted_diagnostics:
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "inherited_diagnostics")
        elif self.inherited_diagnostics or self.emitted_diagnostics or self.steps or self.post_validity_diagnostic is not None:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "inherited_diagnostics")
        for index, record in enumerate(self.emitted_diagnostics):
            self._validate_record(record, index)

    def _validate_record(self, record, index):
        _exact(record, NormalizationDiagnosticRecord, "emitted_diagnostics")
        if not self.inherited_diagnostics:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "inherited_diagnostics")
        envelope = record.emission.envelope
        root = self.original_diagnosis.assessment_binding.diagnosis_reference
        context = self.operation_binding
        reference = context.computation_reference if index == 0 else context.post_validation_reference
        parent = root if index == 0 else context.computation_reference
        phase = "COMPUTATION" if index == 0 else "POST_VALIDATION"
        if (record.phase != phase or record.emission.diagnostic_reference != reference
                or envelope.chain_root_reference != root or envelope.parent_diagnostic_reference != parent
                or envelope.subject_reference != self.original_diagnosis.subject_reference):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emitted_diagnostics")
        previous = (self.inherited_diagnostics[0].envelope if index == 0
                    else self.emitted_diagnostics[0].emission.envelope)
        if index == 1 and previous.disposition != "PENDING":
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emitted_diagnostics")
        if _SEVERITIES.index(envelope.severity) < _SEVERITIES.index(previous.severity):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emission.envelope")
        expected_diagnostic = (self.original_diagnosis.state_validity_diagnostic if index == 0
                               else self.post_validity_diagnostic)
        if record.state_validity_diagnostic != expected_diagnostic or record.step != (self.steps[0] if self.steps else None):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emitted_diagnostics")
        if index == 1:
            succeeded = (self.post_validity_diagnostic.admissibility_status == "VALID"
                         and self.actual_state == self.plan.selected_target)
            if envelope.disposition != ("RESOLVED" if succeeded else "BLOCKED"):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emission.envelope")

    def _common_record(self):
        return {"schema_ref": self.schema_ref, "artifact_type": self.artifact_type,
                "artifact_version": self.artifact_version, "outcome": self.outcome,
                "operation_binding": self.operation_binding.to_record(), "plan": self.plan.to_record(),
                "plan_validation": self.plan_validation.to_record(),
                "original_diagnosis": self.original_diagnosis.to_record(),
                "actual_state": _state_record(self.actual_state), "steps": [step.to_record() for step in self.steps],
                "post_validity_diagnostic": None if self.post_validity_diagnostic is None else self.post_validity_diagnostic.to_record(),
                "normalized_state": _state_record(self.normalized_state),
                "inherited_diagnostics": [entry.to_record() for entry in self.inherited_diagnostics],
                "emitted_diagnostics": [entry.to_record() for entry in self.emitted_diagnostics]}


@dataclass(frozen=True, slots=True)
class NormalizationResult(_NormalizationPacket):
    outcome: str
    operation_binding: NormalizationContext
    plan: NormalizationPlan
    plan_validation: NormalizationPlanValidation
    original_diagnosis: values.StateDiagnosis
    actual_state: values.AshState | None
    steps: tuple[NormalizationStep, ...]
    post_validity_diagnostic: values.StateValidityDiagnostic | None
    normalized_state: values.AshState | None
    inherited_diagnostics: tuple[values.DiagnosticEmission, ...]
    emitted_diagnostics: tuple[NormalizationDiagnosticRecord, ...]

    def __post_init__(self):
        self._validate_common()
        _choice(self.outcome, ("ALREADY_VALID", "NORMALIZED"), "outcome")
        decision = "ALREADY_VALID" if self.outcome == "ALREADY_VALID" else "PLAN_READY"
        if (self.plan_validation.validation_status != "VALIDATED" or self.plan.decision != decision
                or self.actual_state is None or self.actual_state != self.plan.selected_target
                or self.normalized_state != self.actual_state
                or len(self.steps) != (0 if self.outcome == "ALREADY_VALID" else 1)
                or self.post_validity_diagnostic is None
                or self.post_validity_diagnostic.admissibility_status != "VALID"
                or len(self.emitted_diagnostics) != 2):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "outcome")

    def to_record(self):
        return self._common_record()


@dataclass(frozen=True, slots=True)
class NormalizationFailure(_NormalizationPacket):
    outcome: str
    operation_binding: NormalizationContext
    plan: NormalizationPlan
    plan_validation: NormalizationPlanValidation
    original_diagnosis: values.StateDiagnosis
    actual_state: values.AshState | None
    steps: tuple[NormalizationStep, ...]
    post_validity_diagnostic: values.StateValidityDiagnostic | None
    normalized_state: values.AshState | None
    inherited_diagnostics: tuple[values.DiagnosticEmission, ...]
    emitted_diagnostics: tuple[NormalizationDiagnosticRecord, ...]
    failure_kind: str
    failure_code: str
    failed_field: str

    def __post_init__(self):
        self._validate_common()
        _choice(self.failed_field, FIELD_NAMES, "failed_field")
        _choice(self.failure_kind, ("semantic", "plan_validation", "post_validation"), "failure_kind")
        _choice(self.failure_code, FAILURE_CODES, "failure_code")
        if self.normalized_state is not None:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "normalized_state")
        if self.failure_kind == "semantic":
            _choice(self.outcome, ("NOT_NORMALIZABLE", "BLOCKED"), "outcome")
            if (self.plan.decision != self.outcome or self.failure_code != self.plan.reason_code
                    or self.plan_validation.validation_status != "VALIDATED"
                    or self.steps or self.post_validity_diagnostic is not None or len(self.emitted_diagnostics) != 1):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "failure_code")
        elif self.failure_kind == "plan_validation":
            _choice(self.outcome, ("FAILURE",), "outcome")
            _choice(self.failure_code, PLAN_VALIDATION_CODES, "failure_code")
            expected_count = 1 if self.plan_validation.origin_validation_status == "VERIFIED" else 0
            if (self.plan_validation.validation_status != "REJECTED"
                    or self.failure_code != self.plan_validation.failure_code
                    or self.failed_field != self.plan_validation.field_name
                    or self.steps or self.post_validity_diagnostic is not None
                    or len(self.emitted_diagnostics) != expected_count):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "plan_validation")
        else:
            _choice(self.outcome, ("FAILURE",), "outcome")
            _choice(self.failure_code, ("NORMALIZATION_POST_VALIDATION_FAILED",), "failure_code")
            if (self.plan_validation.validation_status != "VALIDATED"
                    or self.plan.decision not in ("ALREADY_VALID", "PLAN_READY")
                    or self.post_validity_diagnostic is None or len(self.emitted_diagnostics) != 2
                    or len(self.steps) != (0 if self.plan.decision == "ALREADY_VALID" else 1)
                    or (self.post_validity_diagnostic.admissibility_status == "VALID"
                        and self.actual_state == self.plan.selected_target)):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "post_validity_diagnostic")
        if self.failure_kind != "post_validation" and self.emitted_diagnostics:
            if self.emitted_diagnostics[0].emission.envelope.disposition != "BLOCKED":
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emission.envelope")

    def to_record(self):
        return {**self._common_record(), "failure_kind": self.failure_kind,
                "failure_code": self.failure_code, "failed_field": self.failed_field}


@dataclass(frozen=True, slots=True)
class NormalizationCaptureFailure(_NormalizationPacket):
    operation_binding: NormalizationContext
    plan: NormalizationPlan
    plan_validation: NormalizationPlanValidation
    original_diagnosis: values.StateDiagnosis
    actual_state: values.AshState | None
    steps: tuple[NormalizationStep, ...]
    post_validity_diagnostic: values.StateValidityDiagnostic | None
    normalized_state: values.AshState | None
    inherited_diagnostics: tuple[values.DiagnosticEmission, ...]
    emitted_diagnostics: tuple[NormalizationDiagnosticRecord, ...]
    failure_code: str
    failed_field: str
    capture_status: str
    attempted_diagnostic: NormalizationDiagnosticRecord
    outcome: ClassVar[str] = "FAILURE"
    failure_kind: ClassVar[str] = "diagnostic_capture"

    def __post_init__(self):
        self._validate_common()
        _choice(self.failed_field, FIELD_NAMES, "failed_field")
        _choice(self.capture_status, ("REJECTED", "NOT_CONFIRMED"), "capture_status")
        expected_code = "DIAGNOSTIC_CAPTURE_REJECTED" if self.capture_status == "REJECTED" else "DIAGNOSTIC_CAPTURE_UNCONFIRMED"
        _choice(self.failure_code, (expected_code,), "failure_code")
        if (self.plan_validation.origin_validation_status != "VERIFIED" or self.normalized_state is not None
                or len(self.emitted_diagnostics) > 1):
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "capture_status")
        self._validate_record(self.attempted_diagnostic, len(self.emitted_diagnostics))
        if not self.emitted_diagnostics and self.post_validity_diagnostic is not None:
            raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "post_validity_diagnostic")
        if self.emitted_diagnostics:
            if (self.plan_validation.validation_status != "VALIDATED"
                    or self.plan.decision not in ("ALREADY_VALID", "PLAN_READY")
                    or len(self.steps) != (0 if self.plan.decision == "ALREADY_VALID" else 1)):
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emitted_diagnostics")
        else:
            disposition = self.attempted_diagnostic.emission.envelope.disposition
            if disposition == "PENDING":
                if (self.plan_validation.validation_status != "VALIDATED"
                        or self.plan.decision not in ("ALREADY_VALID", "PLAN_READY")
                        or len(self.steps) != (0 if self.plan.decision == "ALREADY_VALID" else 1)):
                    raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "steps")
            elif disposition != "BLOCKED" or self.steps:
                raise NormalizationContractError("NORMALIZATION_PLAN_INVALID", "attempted_diagnostic")

    def to_record(self):
        return {**self._common_record(), "failure_kind": self.failure_kind,
                "failure_code": self.failure_code, "failed_field": self.failed_field,
                "capture_status": self.capture_status,
                "attempted_diagnostic": self.attempted_diagnostic.to_record()}
