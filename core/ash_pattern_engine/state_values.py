"""Immutable values for the M3 StateModel reference oracle [YWE-REQ-0039].

The adopted contract is docs/architecture/m3_state_assessment_contract.md.
Construction owns representation and record invariants; assessment behavior and
source loading belong to StateModel and its explicit collaborators.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import ClassVar


ASH_STATE_BITS = 9
CANONICAL_CODEWORDS: tuple[tuple[int, ...], ...] = (
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 1, 1, 1, 1, 0),
    (0, 0, 1, 1, 0, 0, 1, 1, 0),
    (0, 0, 1, 1, 1, 1, 0, 0, 0),
    (0, 1, 0, 1, 0, 1, 0, 1, 0),
    (0, 1, 0, 1, 1, 0, 1, 0, 0),
    (0, 1, 1, 0, 0, 1, 1, 0, 0),
    (0, 1, 1, 0, 1, 0, 0, 1, 0),
    (1, 0, 0, 1, 0, 1, 1, 0, 0),
    (1, 0, 0, 1, 1, 0, 0, 1, 0),
    (1, 0, 1, 0, 0, 1, 0, 1, 0),
    (1, 0, 1, 0, 1, 0, 1, 0, 0),
    (1, 1, 0, 0, 0, 0, 1, 1, 0),
    (1, 1, 0, 0, 1, 1, 0, 0, 0),
    (1, 1, 1, 1, 0, 0, 0, 0, 0),
    (1, 1, 1, 1, 1, 1, 1, 1, 0),
)
# Historical alias retained for callers constructing the accepted c78 baseline.
CANONICAL_BINDING_FIELDS: tuple[tuple[str, str], ...] = (
    ("dependency_id", "ash_cosmological_model.f2_9.canonical"),
    ("aggregate_sha256", "0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb"),
    ("state_space_sha256", "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e"),
    ("codeword_source_sha256", "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c"),
    ("validity_source_sha256", "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e"),
    ("classification_source_sha256", "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff"),
    ("recovery_source_sha256", "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd"),
    ("diagnostic_source_sha256", "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"),
    ("taxonomy_source_sha256", "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"),
)
CURRENT_CANONICAL_BINDING_FIELDS: tuple[tuple[str, str], ...] = (
    ("dependency_id", "ash_cosmological_model.f2_9.canonical"),
    ("aggregate_sha256", "76d59926ce9676b7584c6cdd555f50f56fceda075fa3fc8b37167fd2be43f7c9"),
    ("state_space_sha256", "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e"),
    ("codeword_source_sha256", "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c"),
    ("validity_source_sha256", "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e"),
    ("classification_source_sha256", "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff"),
    ("recovery_source_sha256", "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd"),
    ("diagnostic_source_sha256", "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"),
    ("taxonomy_source_sha256", "150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250"),
)
CANONICAL_BINDING_BASELINES: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    ("LEGACY_C78", CANONICAL_BINDING_FIELDS),
    ("N3_LIFECYCLE", CURRENT_CANONICAL_BINDING_FIELDS),
)
DIAGNOSTIC_ROWS: tuple[tuple[str, str, str, str, bool], ...] = (
    ("VALID", "COMPATIBLE", "ALREADY_VALID", "NO_RECOVERY_NEEDED", True),
    ("TRANSFORMATION_COMPATIBLE", "COMPATIBLE", "NORMALIZABLE", "RECOVERY_APPLICABLE", False),
    ("TRANSFORMATION_INCOMPATIBLE", "INCOMPATIBLE", "NOT_NORMALIZABLE", "NOT_RECOVERABLE", False),
    ("UNCLASSIFIED", "UNKNOWN", "BLOCKED", "CONTAINMENT_NEEDED", False),
)
RECOVERY_CATEGORY_PAIRS: tuple[tuple[str, str], ...] = (
    ("STABLE", "NO_ACTION"),
    ("UNSTABLE", "NORMALIZE_STATE"),
    ("CORRECTABLE", "APPLY_CORRECTION"),
    ("DEGRADED", "FALLBACK_REQUIRED"),
    ("CONTAINED", "CONTAINMENT_REQUIRED"),
    ("FAILED", "ESCALATION_REQUIRED"),
    ("SAFE_HALT", "TERMINAL_NO_RECOVERY"),
)
ASSESSMENT_RULE_IDS = frozenset((
    "ASH-STATE-STRUCTURE-001", "ASH-STATE-VALIDITY-001", "ASH-STATE-GENERAL-001",
    "ASH-ADMISSIBILITY-CLASSIFICATION-001", "ASH-CLASSIFICATION-MAPPING-001",
    "ASH-RECOVERY-ACTION-001",
))
RULE_IDS = ASSESSMENT_RULE_IDS | frozenset((
    "ASH-CODEWORD-STRUCTURE-001", "ASH-FALLBACK-SELECTION-001",
    "ASH-CONTAINMENT-TRIGGER-001", "ASH-CONTAINMENT-TRIGGER-002",
    "ASH-CONTAINMENT-TRIGGER-003", "ASH-CONTAINMENT-TRIGGER-004",
    "ASH-HALT-TRIGGER-001", "ASH-HALT-TRIGGER-002", "ASH-HALT-TRIGGER-003",
    "ASH-HALT-TRIGGER-004", "ASH-HALT-TRIGGER-005",
))
INPUT_FAILURE_CODES = frozenset((
    "STATE_WIDTH", "STATE_COORDINATE_TYPE", "STATE_COORDINATE_VALUE",
    "INPUT_KIND_UNSUPPORTED", "INPUT_SIZE_LIMIT", "INPUT_DEPTH_LIMIT", "INPUT_TOKEN_LIMIT",
    "INPUT_UTF8_INVALID", "INPUT_JSON_INVALID", "INPUT_JSON_DUPLICATE_KEY",
    "INPUT_JSON_NONFINITE", "INPUT_NUMERIC_TOKEN_INVALID", "INPUT_SIGNATURE_INVALID",
    "INPUT_RECORD_INVALID", "INPUT_RECORD_SIZE_LIMIT", "INPUT_RECORD_KEY_INVALID",
    "INPUT_STATE_SPACE_INVALID",
))
FAILURE_CODES = INPUT_FAILURE_CODES | frozenset((
    "CANONICAL_BINDING_INVALID", "PROFILE_BINDING_INVALID", "PROFILE_STATE_DUPLICATE",
    "PROFILE_SIZE_LIMIT", "PROFILE_SOURCE_MISMATCH", "CONTEXT_INVALID",
    "DIAGNOSTIC_CONTEXT_INVALID", "PREDICATE_EVIDENCE_INVALID",
    "PREDICATE_BINDING_MISMATCH", "PREDICATE_NOT_EVALUATED", "DIAGNOSTIC_ROW_INVALID",
    "DIAGNOSTIC_ENVELOPE_INVALID", "DIAGNOSTIC_CAPTURE_REJECTED",
    "DIAGNOSTIC_CAPTURE_UNCONFIRMED",
))
PREDICATE_NAMES = ("correction_path_is_known", "fallback_is_available")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SIGNATURE = re.compile(r"[01]{9}\Z")


class StateContractError(ValueError):
    """Bounded structural failure before any diagnostic has been emitted."""

    def __init__(self, code: str, field_name: str) -> None:
        if type(code) is not str or code not in FAILURE_CODES:
            raise ValueError("unknown StateContractError code")
        if type(field_name) is not str or not re.fullmatch(r"[A-Za-z0-9_.\[\]]{1,128}", field_name):
            raise ValueError("invalid StateContractError field name")
        self.code = code
        self.field_name = field_name
        self.emitted_diagnostics: tuple[DiagnosticEmission, ...] = ()
        super().__init__(f"{code}: {field_name}")


def _require_type(value: object, expected: type | tuple[type, ...], code: str, field: str) -> None:
    allowed = expected if type(expected) is tuple else (expected,)
    if not any(type(value) is kind for kind in allowed):
        raise StateContractError(code, field)


def _identifier(value: object, code: str, field: str, *, reference: bool = False) -> None:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise StateContractError(code, field)
    if reference and value in ("NONE", "SELF"):
        raise StateContractError(code, field)


def _choice(value: object, choices: tuple[str, ...] | frozenset[str], code: str, field: str) -> None:
    if type(value) is not str or value not in choices:
        raise StateContractError(code, field)


def _text(value: object, code: str, field: str, *, limit: int = 512, nonempty: bool = True) -> None:
    if type(value) is not str or len(value) > limit or (nonempty and not value.strip()):
        raise StateContractError(code, field)


def _hash(value: object, code: str, field: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise StateContractError(code, field)


def _text_tuple(value: object, code: str, field: str, *, rules: bool = False) -> tuple[str, ...]:
    _require_type(value, (list, tuple), code, field)
    maximum = 5 if rules else 8
    if not 1 <= len(value) <= maximum:
        raise StateContractError(code, field)
    for entry in value:
        if rules:
            _choice(entry, RULE_IDS, code, field)
        else:
            _text(entry, code, field)
    result = tuple(value)
    if rules and len(set(result)) != len(result):
        raise StateContractError(code, field)
    return result


@dataclass(frozen=True, slots=True)
class AshState:
    bits: tuple[int, ...]

    def __post_init__(self) -> None:
        _require_type(self.bits, (tuple, list), "STATE_COORDINATE_TYPE", "bits")
        if len(self.bits) != ASH_STATE_BITS:
            raise StateContractError("STATE_WIDTH", "bits")
        for index, bit in enumerate(self.bits):
            if type(bit) is not int:
                raise StateContractError("STATE_COORDINATE_TYPE", f"bits[{index}]")
            if bit not in (0, 1):
                raise StateContractError("STATE_COORDINATE_VALUE", f"bits[{index}]")
        object.__setattr__(self, "bits", tuple(self.bits))

    @property
    def signature(self) -> str:
        return "".join("1" if bit else "0" for bit in self.bits)

    def to_record(self) -> dict[str, object]:
        return {"state_space": "F2^9", "bits": list(self.bits)}


@dataclass(frozen=True, slots=True)
class CanonicalAshBinding:
    dependency_id: str
    aggregate_sha256: str
    state_space_sha256: str
    codeword_source_sha256: str
    validity_source_sha256: str
    classification_source_sha256: str
    recovery_source_sha256: str
    diagnostic_source_sha256: str
    taxonomy_source_sha256: str

    def __post_init__(self) -> None:
        _canonical_source_fields(self)

    def to_record(self) -> dict[str, str]:
        return {field: getattr(self, field) for field, _ in CANONICAL_BINDING_FIELDS}


def _canonical_source_fields(binding: CanonicalAshBinding) -> tuple[str, tuple[tuple[str, str], ...]]:
    if type(binding) is not CanonicalAshBinding:
        raise StateContractError("CANONICAL_BINDING_INVALID", "canonical_binding")
    actual = []
    for field, _ in CANONICAL_BINDING_FIELDS:
        try:
            value = getattr(binding, field)
        except AttributeError:
            raise StateContractError("CANONICAL_BINDING_INVALID", field) from None
        if type(value) is not str:
            raise StateContractError("CANONICAL_BINDING_INVALID", field)
        actual.append(value)
    if actual[0] != CANONICAL_BINDING_FIELDS[0][1]:
        raise StateContractError("CANONICAL_BINDING_INVALID", "dependency_id")
    for name, fields in CANONICAL_BINDING_BASELINES:
        if actual[1] == fields[1][1]:
            for value, (field, expected) in zip(actual, fields):
                if value != expected:
                    raise StateContractError("CANONICAL_BINDING_INVALID", field)
            return name, fields
    raise StateContractError("CANONICAL_BINDING_INVALID", "aggregate_sha256")


def canonical_source_baseline(binding: CanonicalAshBinding) -> str:
    """Recognize one complete reviewed vector without authenticating its host."""
    return _canonical_source_fields(binding)[0]


def canonical_diagnostic_pin_fields(binding: CanonicalAshBinding) -> tuple[tuple[str, str], ...]:
    """Return the eight ordered source digests belonging to the exact binding."""
    _, fields = _canonical_source_fields(binding)
    names = ("ASH_AGGREGATE", "ASH_STATE_SPACE", "ASH_CODEWORDS", "ASH_VALIDITY",
             "ASH_CLASSIFICATION", "ASH_RECOVERY", "ASH_DIAGNOSTIC_SCHEMA", "ASH_TAXONOMY")
    return tuple((name, digest) for name, (_, digest) in zip(names, fields[1:]))


@dataclass(frozen=True, slots=True)
class ProfileSourceBinding:
    source_reference: str
    source_sha256: str
    evidence_reference: str

    def __post_init__(self) -> None:
        _identifier(self.source_reference, "PROFILE_BINDING_INVALID", "source_reference")
        _hash(self.source_sha256, "PROFILE_BINDING_INVALID", "source_sha256")
        _identifier(self.evidence_reference, "PROFILE_BINDING_INVALID", "evidence_reference", reference=True)

    def to_record(self) -> dict[str, str]:
        return {"source_reference": self.source_reference, "source_sha256": self.source_sha256,
                "evidence_reference": self.evidence_reference}


@dataclass(frozen=True, slots=True)
class ValidityProfile:
    profile_id: str
    source_binding: ProfileSourceBinding
    recognized_valid_states: frozenset[AshState]

    def __post_init__(self) -> None:
        _identifier(self.profile_id, "PROFILE_BINDING_INVALID", "profile_id")
        _require_type(self.source_binding, ProfileSourceBinding, "PROFILE_BINDING_INVALID", "source_binding")
        _require_type(self.recognized_valid_states, (list, tuple, set, frozenset),
                      "PROFILE_BINDING_INVALID", "recognized_valid_states")
        if len(self.recognized_valid_states) > 512:
            raise StateContractError("PROFILE_SIZE_LIMIT", "recognized_valid_states")
        for state in self.recognized_valid_states:
            _require_type(state, AshState, "PROFILE_BINDING_INVALID", "recognized_valid_states")
        owned = frozenset(self.recognized_valid_states)
        if len(owned) != len(self.recognized_valid_states):
            raise StateContractError("PROFILE_STATE_DUPLICATE", "recognized_valid_states")
        object.__setattr__(self, "recognized_valid_states", owned)

    def to_record(self) -> dict[str, object]:
        return {"profile_id": self.profile_id, "source_binding": self.source_binding.to_record(),
                "recognized_valid_signatures": sorted(state.signature for state in self.recognized_valid_states)}


@dataclass(frozen=True, slots=True)
class UnavailableValidityProfileEvidence:
    profile_id: str
    source_binding: ProfileSourceBinding
    reason_code: str
    reason: str

    def __post_init__(self) -> None:
        _identifier(self.profile_id, "PROFILE_BINDING_INVALID", "profile_id")
        _require_type(self.source_binding, ProfileSourceBinding, "PROFILE_BINDING_INVALID", "source_binding")
        _choice(self.reason_code, ("PROFILE_DATA_UNAVAILABLE",), "PROFILE_BINDING_INVALID", "reason_code")
        _text(self.reason, "PROFILE_BINDING_INVALID", "reason")

    def to_record(self) -> dict[str, object]:
        return {"profile_id": self.profile_id, "source_binding": self.source_binding.to_record(),
                "reason_code": self.reason_code, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class AvailableProfileBinding:
    profile: ValidityProfile
    availability: ClassVar[str] = "AVAILABLE"

    def __post_init__(self) -> None:
        _require_type(self.profile, ValidityProfile, "PROFILE_BINDING_INVALID", "profile")

    @property
    def profile_id(self) -> str:
        return self.profile.profile_id

    @property
    def source_binding(self) -> ProfileSourceBinding:
        return self.profile.source_binding

    def to_record(self) -> dict[str, object]:
        return {"availability": self.availability, **self.profile.to_record()}


@dataclass(frozen=True, slots=True)
class UnavailableProfileBinding:
    evidence: UnavailableValidityProfileEvidence
    availability: ClassVar[str] = "UNAVAILABLE"

    def __post_init__(self) -> None:
        _require_type(self.evidence, UnavailableValidityProfileEvidence, "PROFILE_BINDING_INVALID", "evidence")

    @property
    def profile_id(self) -> str:
        return self.evidence.profile_id

    @property
    def source_binding(self) -> ProfileSourceBinding:
        return self.evidence.source_binding

    def to_record(self) -> dict[str, object]:
        return {"availability": self.availability, **self.evidence.to_record()}


ProfileBinding = AvailableProfileBinding | UnavailableProfileBinding


@dataclass(frozen=True, slots=True)
class SystemContext:
    is_in_safe_halt: bool
    is_in_containment: bool

    def __post_init__(self) -> None:
        _require_type(self.is_in_safe_halt, bool, "CONTEXT_INVALID", "is_in_safe_halt")
        _require_type(self.is_in_containment, bool, "CONTEXT_INVALID", "is_in_containment")

    def to_record(self) -> dict[str, bool]:
        return {"is_in_safe_halt": self.is_in_safe_halt, "is_in_containment": self.is_in_containment}


@dataclass(frozen=True, slots=True)
class AssessmentBinding:
    assessment_reference: str
    original_input_reference: str
    diagnosis_reference: str

    def __post_init__(self) -> None:
        for field in ("assessment_reference", "original_input_reference", "diagnosis_reference"):
            _identifier(getattr(self, field), "DIAGNOSTIC_CONTEXT_INVALID", field, reference=True)

    def to_record(self) -> dict[str, str]:
        return {"assessment_reference": self.assessment_reference,
                "original_input_reference": self.original_input_reference,
                "diagnosis_reference": self.diagnosis_reference}


@dataclass(frozen=True, slots=True)
class DiagnosticContext:
    assessment_reference: str
    original_input_reference: str
    detection_reference: str
    classification_reference: str

    def __post_init__(self) -> None:
        for field in ("assessment_reference", "original_input_reference", "detection_reference", "classification_reference"):
            _identifier(getattr(self, field), "DIAGNOSTIC_CONTEXT_INVALID", field, reference=True)
        if self.detection_reference == self.classification_reference:
            raise StateContractError("DIAGNOSTIC_CONTEXT_INVALID", "classification_reference")

    def to_record(self) -> dict[str, str]:
        return {"assessment_reference": self.assessment_reference,
                "original_input_reference": self.original_input_reference,
                "detection_reference": self.detection_reference,
                "classification_reference": self.classification_reference}


@dataclass(frozen=True, slots=True)
class PredicateBinding:
    assessment_reference: str
    diagnosis_reference: str
    subject_reference: str
    profile_id: str
    profile_source_sha256: str
    ash_dependency_id: str
    ash_aggregate_sha256: str
    evidence_reference: str

    def __post_init__(self) -> None:
        for field in ("assessment_reference", "diagnosis_reference", "subject_reference", "profile_id"):
            _identifier(getattr(self, field), "PREDICATE_EVIDENCE_INVALID", field, reference=True)
        _hash(self.profile_source_sha256, "PREDICATE_EVIDENCE_INVALID", "profile_source_sha256")
        _identifier(self.ash_dependency_id, "PREDICATE_EVIDENCE_INVALID", "ash_dependency_id")
        _hash(self.ash_aggregate_sha256, "PREDICATE_EVIDENCE_INVALID", "ash_aggregate_sha256")
        _identifier(self.evidence_reference, "PREDICATE_EVIDENCE_INVALID", "evidence_reference", reference=True)

    def to_record(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in (
            "assessment_reference", "diagnosis_reference", "subject_reference", "profile_id",
            "profile_source_sha256", "ash_dependency_id", "ash_aggregate_sha256", "evidence_reference")}


@dataclass(frozen=True, slots=True)
class EvaluatedPredicate:
    binding: PredicateBinding
    value: bool
    evaluation: ClassVar[str] = "EVALUATED"

    def __post_init__(self) -> None:
        _require_type(self.binding, PredicateBinding, "PREDICATE_EVIDENCE_INVALID", "binding")
        _require_type(self.value, bool, "PREDICATE_EVIDENCE_INVALID", "value")

    def to_record(self) -> dict[str, object]:
        return {"evaluation": self.evaluation, "binding": self.binding.to_record(), "value": self.value}


@dataclass(frozen=True, slots=True)
class NotEvaluatedPredicate:
    binding: PredicateBinding
    reason: str
    evaluation: ClassVar[str] = "NOT_EVALUATED"

    def __post_init__(self) -> None:
        _require_type(self.binding, PredicateBinding, "PREDICATE_EVIDENCE_INVALID", "binding")
        _text(self.reason, "PREDICATE_EVIDENCE_INVALID", "reason")

    def to_record(self) -> dict[str, object]:
        return {"evaluation": self.evaluation, "binding": self.binding.to_record(), "reason": self.reason}


PredicateEvidence = EvaluatedPredicate | NotEvaluatedPredicate


@dataclass(frozen=True, slots=True)
class ClassificationEvidence:
    correction_path_is_known: PredicateEvidence
    fallback_is_available: PredicateEvidence

    def __post_init__(self) -> None:
        for field in PREDICATE_NAMES:
            _require_type(getattr(self, field), (EvaluatedPredicate, NotEvaluatedPredicate),
                          "PREDICATE_EVIDENCE_INVALID", field)

    def to_record(self) -> dict[str, object]:
        return {"correction_path_is_known": self.correction_path_is_known.to_record(),
                "fallback_is_available": self.fallback_is_available.to_record()}


@dataclass(frozen=True, slots=True)
class CoordinateObservation:
    index: int
    scalar_kind: str
    value: int | str | None = None
    sign: int | None = None
    bit_length: int | None = None
    total_length: int | None = None
    truncated: bool | None = None

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ROW_INVALID"
        if type(self.index) is not int or not 0 <= self.index < 9:
            raise StateContractError(code, "index")
        _choice(self.scalar_kind, ("INTEGER_BIT", "INTEGER_OTHER", "FINITE_FLOAT",
                                 "NONFINITE_FLOAT", "STRING", "UNSUPPORTED"), code, "scalar_kind")
        allowed_fields: tuple[str, ...]
        if self.scalar_kind == "INTEGER_BIT":
            if type(self.value) is not int or self.value not in (0, 1):
                raise StateContractError(code, "value")
            allowed_fields = ("value",)
        elif self.scalar_kind == "INTEGER_OTHER":
            if type(self.sign) is not int or self.sign not in (-1, 0, 1):
                raise StateContractError(code, "sign")
            if type(self.bit_length) is not int or self.bit_length < 0:
                raise StateContractError(code, "bit_length")
            if (self.sign == 0) != (self.bit_length == 0):
                raise StateContractError(code, "bit_length")
            allowed_fields = ("sign", "bit_length")
        elif self.scalar_kind == "FINITE_FLOAT":
            _text(self.value, code, "value", limit=64)
            try:
                number = float.fromhex(self.value)
            except (ValueError, OverflowError) as exc:
                raise StateContractError(code, "value") from exc
            if not math.isfinite(number) or number.hex() != self.value:
                raise StateContractError(code, "value")
            allowed_fields = ("value",)
        elif self.scalar_kind == "NONFINITE_FLOAT":
            _choice(self.value, ("NAN", "POSITIVE_INFINITY", "NEGATIVE_INFINITY"), code, "value")
            allowed_fields = ("value",)
        elif self.scalar_kind == "STRING":
            _text(self.value, code, "value", limit=64, nonempty=False)
            if type(self.total_length) is not int or self.total_length < len(self.value):
                raise StateContractError(code, "total_length")
            _require_type(self.truncated, bool, code, "truncated")
            if self.truncated != (self.total_length > len(self.value)):
                raise StateContractError(code, "truncated")
            allowed_fields = ("value", "total_length", "truncated")
        else:
            allowed_fields = ()
        for field in ("value", "sign", "bit_length", "total_length", "truncated"):
            if field not in allowed_fields and getattr(self, field) is not None:
                raise StateContractError(code, field)

    def to_record(self) -> dict[str, object]:
        result: dict[str, object] = {"index": self.index, "scalar_kind": self.scalar_kind}
        for field in ("value", "sign", "bit_length", "total_length", "truncated"):
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        return result


@dataclass(frozen=True, slots=True)
class InputEvidence:
    original_input_reference: str
    representation_kind: str
    observed_length: int | None
    length_unit: str
    preview: str | None
    preview_encoding: str
    truncated: bool
    coordinate_observations: tuple[CoordinateObservation, ...]
    failure_code: str | None

    @staticmethod
    def validate_reference(reference: object) -> None:
        _identifier(reference, "DIAGNOSTIC_ROW_INVALID", "original_input_reference", reference=True)

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ROW_INVALID"
        InputEvidence.validate_reference(self.original_input_reference)
        _choice(self.representation_kind,
                ("RAW_JSON", "SIGNATURE", "BIT_SEQUENCE", "STATE_RECORD", "UNSUPPORTED"), code, "representation_kind")
        if self.observed_length is not None and (type(self.observed_length) is not int or self.observed_length < 0):
            raise StateContractError(code, "observed_length")
        _choice(self.length_unit, ("BYTES", "CHARACTERS", "ELEMENTS", "KEYS", "UNKNOWN"), code, "length_unit")
        if self.preview is not None:
            _text(self.preview, code, "preview", limit=64, nonempty=False)
        _choice(self.preview_encoding, ("TEXT", "HEX"), code, "preview_encoding")
        if self.preview is not None and self.preview_encoding == "HEX":
            if len(self.preview) % 2 or re.fullmatch(r"[0-9a-f]*", self.preview) is None:
                raise StateContractError(code, "preview")
        _require_type(self.truncated, bool, code, "truncated")
        _require_type(self.coordinate_observations, (list, tuple), code, "coordinate_observations")
        if len(self.coordinate_observations) > 9:
            raise StateContractError(code, "coordinate_observations")
        previous = -1
        for observation in self.coordinate_observations:
            _require_type(observation, CoordinateObservation, code, "coordinate_observations")
            if observation.index <= previous:
                raise StateContractError(code, "coordinate_observations")
            previous = observation.index
        object.__setattr__(self, "coordinate_observations", tuple(self.coordinate_observations))
        if self.failure_code is not None:
            _choice(self.failure_code, INPUT_FAILURE_CODES, code, "failure_code")
        expected_unit = {
            "RAW_JSON": "BYTES", "SIGNATURE": "CHARACTERS", "BIT_SEQUENCE": "ELEMENTS",
            "STATE_RECORD": "KEYS", "UNSUPPORTED": "UNKNOWN",
        }[self.representation_kind]
        if self.length_unit != expected_unit:
            raise StateContractError(code, "length_unit")
        if self.representation_kind == "UNSUPPORTED":
            if self.failure_code != "INPUT_KIND_UNSUPPORTED":
                raise StateContractError(code, "failure_code")
            if self.observed_length is not None or self.preview is not None or self.coordinate_observations:
                raise StateContractError(code, "representation_kind")
        elif self.observed_length is None:
            raise StateContractError(code, "observed_length")
        if self.representation_kind == "RAW_JSON":
            if self.preview_encoding != "HEX" or self.preview is None or self.coordinate_observations:
                raise StateContractError(code, "preview")
        elif self.representation_kind == "SIGNATURE":
            if self.preview_encoding != "TEXT" or self.preview is None or self.coordinate_observations:
                raise StateContractError(code, "preview")
        elif self.preview_encoding != "TEXT" or self.preview is not None:
            raise StateContractError(code, "preview")
        if self.failure_code is None:
            if self.representation_kind in ("RAW_JSON", "SIGNATURE") and self.observed_length > 4096:
                raise StateContractError(code, "observed_length")
            if self.representation_kind == "BIT_SEQUENCE" and self.observed_length != 9:
                raise StateContractError(code, "observed_length")
            if self.representation_kind == "STATE_RECORD" and not 2 <= self.observed_length <= 64:
                raise StateContractError(code, "observed_length")

    def to_record(self) -> dict[str, object]:
        return {"original_input_reference": self.original_input_reference,
                "representation_kind": self.representation_kind, "observed_length": self.observed_length,
                "length_unit": self.length_unit, "preview": self.preview, "preview_encoding": self.preview_encoding,
                "truncated": self.truncated,
                "coordinate_observations": [entry.to_record() for entry in self.coordinate_observations],
                "failure_code": self.failure_code}


@dataclass(frozen=True, slots=True)
class RejectedCandidateEvidence:
    input_evidence: InputEvidence
    candidate_kind: ClassVar[str] = "REJECTED"

    def __post_init__(self) -> None:
        _require_type(self.input_evidence, InputEvidence, "DIAGNOSTIC_ROW_INVALID", "input_evidence")
        if self.input_evidence.failure_code is None:
            raise StateContractError("DIAGNOSTIC_ROW_INVALID", "input_evidence.failure_code")

    def to_record(self) -> dict[str, object]:
        return {"candidate_kind": self.candidate_kind, "input_evidence": self.input_evidence.to_record()}


@dataclass(frozen=True, slots=True)
class OrbitInfo:
    orbit_id: str
    member_count: int
    contains_known_valid_state: bool

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ROW_INVALID"
        if type(self.orbit_id) is not str or _SIGNATURE.fullmatch(self.orbit_id) is None:
            raise StateContractError(code, "orbit_id")
        if type(self.member_count) is not int or self.member_count != 16:
            raise StateContractError(code, "member_count")
        _require_type(self.contains_known_valid_state, bool, code, "contains_known_valid_state")

    def to_record(self) -> dict[str, object]:
        return {"orbit_id": self.orbit_id, "member_count": self.member_count,
                "contains_known_valid_state": self.contains_known_valid_state}


@dataclass(frozen=True, slots=True)
class StateValidityDiagnostic:
    input_state: AshState | RejectedCandidateEvidence
    admissibility_status: str
    transformation_compatibility: str
    normalization_status: str
    recoverability_relevance: str
    is_valid: bool
    orbit_info: OrbitInfo | None
    rule_ids: tuple[str, ...]
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ROW_INVALID"
        _require_type(self.input_state, (AshState, RejectedCandidateEvidence), code, "input_state")
        for field in ("admissibility_status", "transformation_compatibility", "normalization_status", "recoverability_relevance"):
            _require_type(getattr(self, field), str, code, field)
        _require_type(self.is_valid, bool, code, "is_valid")
        row = (self.admissibility_status, self.transformation_compatibility,
               self.normalization_status, self.recoverability_relevance, self.is_valid)
        if row not in DIAGNOSTIC_ROWS:
            raise StateContractError(code, "admissibility_status")
        if self.orbit_info is not None:
            _require_type(self.orbit_info, OrbitInfo, code, "orbit_info")
        if type(self.input_state) is RejectedCandidateEvidence:
            if self.admissibility_status != "UNCLASSIFIED" or self.orbit_info is not None:
                raise StateContractError(code, "input_state")
        if self.admissibility_status == "UNCLASSIFIED" and self.orbit_info is not None:
            raise StateContractError(code, "orbit_info")
        if self.admissibility_status != "UNCLASSIFIED":
            if self.orbit_info is None:
                raise StateContractError(code, "orbit_info")
            expected_contains = self.admissibility_status in ("VALID", "TRANSFORMATION_COMPATIBLE")
            if self.orbit_info.contains_known_valid_state != expected_contains:
                raise StateContractError(code, "orbit_info.contains_known_valid_state")
        rules = _text_tuple(self.rule_ids, code, "rule_ids", rules=True)
        if any(rule not in ASSESSMENT_RULE_IDS for rule in rules):
            raise StateContractError(code, "rule_ids")
        object.__setattr__(self, "rule_ids", rules)
        object.__setattr__(self, "notes", _text_tuple(self.notes, code, "notes"))

    def to_record(self) -> dict[str, object]:
        input_state = (list(self.input_state.bits) if type(self.input_state) is AshState
                       else self.input_state.to_record())
        return {"input_state": input_state, "admissibility_status": self.admissibility_status,
                "transformation_compatibility": self.transformation_compatibility,
                "normalization_status": self.normalization_status,
                "recoverability_relevance": self.recoverability_relevance, "is_valid": self.is_valid,
                "orbit_info": None if self.orbit_info is None else self.orbit_info.to_record(),
                "rule_ids": list(self.rule_ids), "notes": list(self.notes)}


@dataclass(frozen=True, slots=True)
class DiagnosticEnvelope:
    diagnostic_kind: str
    severity: str
    stage: str
    disposition: str
    subject_reference: str
    parent_diagnostic_reference: str | None
    chain_root_reference: str
    rule_ids: tuple[str, ...]
    summary: str
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ENVELOPE_INVALID"
        _choice(self.diagnostic_kind, ("STATE_VALIDITY", "RECOVERY", "FALLBACK", "CONTAINMENT", "SAFE_HALT"), code, "diagnostic_kind")
        _choice(self.severity, ("INFO", "WARNING", "ERROR", "CRITICAL"), code, "severity")
        _choice(self.stage, ("DETECTION", "CLASSIFICATION", "RECOVERY", "ESCALATION", "TERMINAL"), code, "stage")
        _choice(self.disposition, ("RESOLVED", "PENDING", "BLOCKED", "ESCALATED", "TERMINAL"), code, "disposition")
        _identifier(self.subject_reference, code, "subject_reference", reference=True)
        if self.parent_diagnostic_reference is not None:
            _identifier(self.parent_diagnostic_reference, code, "parent_diagnostic_reference", reference=True)
        if (self.stage == "DETECTION") != (self.parent_diagnostic_reference is None):
            raise StateContractError(code, "parent_diagnostic_reference")
        _identifier(self.chain_root_reference, code, "chain_root_reference", reference=True)
        object.__setattr__(self, "rule_ids", _text_tuple(self.rule_ids, code, "rule_ids", rules=True))
        _text(self.summary, code, "summary")
        if any(char in self.summary for char in ("\r", "\n", "\v", "\f", "\x1c", "\x1d", "\x1e", "\u0085", "\u2028", "\u2029")):
            raise StateContractError(code, "summary")
        object.__setattr__(self, "notes", _text_tuple(self.notes, code, "notes"))

    def to_record(self) -> dict[str, object]:
        return {"diagnostic_kind": self.diagnostic_kind, "severity": self.severity, "stage": self.stage,
                "disposition": self.disposition, "subject_reference": self.subject_reference,
                "parent_diagnostic_reference": self.parent_diagnostic_reference,
                "chain_root_reference": self.chain_root_reference, "rule_ids": list(self.rule_ids),
                "summary": self.summary, "notes": list(self.notes)}


@dataclass(frozen=True, slots=True)
class DiagnosticEmission:
    diagnostic_reference: str
    envelope: DiagnosticEnvelope

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ENVELOPE_INVALID"
        _identifier(self.diagnostic_reference, code, "diagnostic_reference", reference=True)
        _require_type(self.envelope, DiagnosticEnvelope, code, "envelope")
        if self.envelope.stage == "DETECTION":
            if self.envelope.chain_root_reference != self.diagnostic_reference:
                raise StateContractError(code, "envelope.chain_root_reference")
        elif self.diagnostic_reference in (self.envelope.parent_diagnostic_reference, self.envelope.chain_root_reference):
            raise StateContractError(code, "diagnostic_reference")

    def to_record(self) -> dict[str, object]:
        return {"diagnostic_reference": self.diagnostic_reference, "envelope": self.envelope.to_record()}


@dataclass(frozen=True, slots=True)
class CaptureReceipt:
    diagnostic_reference: str
    status: str

    def __post_init__(self) -> None:
        _identifier(self.diagnostic_reference, "DIAGNOSTIC_ENVELOPE_INVALID", "diagnostic_reference", reference=True)
        _choice(self.status, ("CONFIRMED", "REJECTED", "NOT_CONFIRMED"),
                "DIAGNOSTIC_ENVELOPE_INVALID", "status")

    def to_record(self) -> dict[str, str]:
        return {"diagnostic_reference": self.diagnostic_reference, "status": self.status}


@dataclass(frozen=True, slots=True)
class _StatePacket:
    assessment_binding: AssessmentBinding
    source_binding: CanonicalAshBinding
    profile_binding: ProfileBinding
    input_evidence: InputEvidence
    parsed_state: AshState | None
    state_validity_diagnostic: StateValidityDiagnostic
    emitted_diagnostics: tuple[DiagnosticEmission, ...]
    schema_ref: ClassVar[str] = "data/schemas/m3_state_assessment_schema.json"
    artifact_type: ClassVar[str] = "ywe_state_assessment"
    artifact_version: ClassVar[str] = "1.0.0"
    outcome: ClassVar[str]

    def __post_init__(self) -> None:
        code = "DIAGNOSTIC_ROW_INVALID"
        _require_type(self.assessment_binding, AssessmentBinding, code, "assessment_binding")
        _require_type(self.source_binding, CanonicalAshBinding, code, "source_binding")
        _require_type(self.profile_binding, (AvailableProfileBinding, UnavailableProfileBinding), code, "profile_binding")
        _require_type(self.input_evidence, InputEvidence, code, "input_evidence")
        if self.parsed_state is not None:
            _require_type(self.parsed_state, AshState, code, "parsed_state")
        _require_type(self.state_validity_diagnostic, StateValidityDiagnostic, code, "state_validity_diagnostic")
        if self.assessment_binding.original_input_reference != self.input_evidence.original_input_reference:
            raise StateContractError(code, "input_evidence.original_input_reference")
        diagnostic = self.state_validity_diagnostic
        if any(rule not in ASSESSMENT_RULE_IDS for rule in diagnostic.rule_ids):
            raise StateContractError(code, "state_validity_diagnostic.rule_ids")
        if self.parsed_state is None:
            if (self.input_evidence.failure_code is None or type(diagnostic.input_state) is not RejectedCandidateEvidence
                    or diagnostic.input_state.input_evidence != self.input_evidence):
                raise StateContractError(code, "parsed_state")
        elif (self.input_evidence.failure_code is not None or type(diagnostic.input_state) is not AshState
              or diagnostic.input_state != self.parsed_state):
            raise StateContractError(code, "parsed_state")
        if type(self.profile_binding) is UnavailableProfileBinding and diagnostic.admissibility_status != "UNCLASSIFIED":
            raise StateContractError(code, "profile_binding")
        if (type(self.profile_binding) is AvailableProfileBinding and self.parsed_state is not None
                and diagnostic.admissibility_status == "UNCLASSIFIED"):
            raise StateContractError(code, "profile_binding")
        _require_type(self.emitted_diagnostics, (list, tuple), code, "emitted_diagnostics")
        if len(self.emitted_diagnostics) > 2:
            raise StateContractError(code, "emitted_diagnostics")
        for emission in self.emitted_diagnostics:
            _require_type(emission, DiagnosticEmission, code, "emitted_diagnostics")
        object.__setattr__(self, "emitted_diagnostics", tuple(self.emitted_diagnostics))
        for index, emission in enumerate(self.emitted_diagnostics):
            self._validate_emission(emission, index)

    @property
    def subject_reference(self) -> str:
        if self.parsed_state is None:
            return self.input_evidence.original_input_reference
        return "ash_state_" + self.parsed_state.signature

    def _validate_emission(self, emission: DiagnosticEmission, index: int) -> None:
        code = "DIAGNOSTIC_ENVELOPE_INVALID"
        envelope = emission.envelope
        if any(rule not in ASSESSMENT_RULE_IDS for rule in envelope.rule_ids):
            raise StateContractError(code, "emitted_diagnostics")
        if envelope.diagnostic_kind != "STATE_VALIDITY" or envelope.subject_reference != self.subject_reference:
            raise StateContractError(code, "emitted_diagnostics")
        root = self.assessment_binding.diagnosis_reference
        if envelope.chain_root_reference != root:
            raise StateContractError(code, "emitted_diagnostics")
        if index == 0:
            if (emission.diagnostic_reference != root or envelope.stage != "DETECTION"
                    or envelope.parent_diagnostic_reference is not None):
                raise StateContractError(code, "emitted_diagnostics")
        elif envelope.stage != "CLASSIFICATION" or envelope.parent_diagnostic_reference != root:
            raise StateContractError(code, "emitted_diagnostics")

    def _common_record(self) -> dict[str, object]:
        return {"schema_ref": self.schema_ref, "artifact_type": self.artifact_type,
                "artifact_version": self.artifact_version, "outcome": self.outcome,
                "assessment_binding": self.assessment_binding.to_record(),
                "source_binding": self.source_binding.to_record(), "profile_binding": self.profile_binding.to_record(),
                "input_evidence": self.input_evidence.to_record(),
                "parsed_state": None if self.parsed_state is None else self.parsed_state.to_record(),
                "state_validity_diagnostic": self.state_validity_diagnostic.to_record(),
                "emitted_diagnostics": [entry.to_record() for entry in self.emitted_diagnostics]}

    def _contextual_values(self, context: SystemContext, evidence: ClassificationEvidence) -> None:
        _require_type(context, SystemContext, "CONTEXT_INVALID", "system_context")
        _require_type(evidence, ClassificationEvidence, "PREDICATE_EVIDENCE_INVALID", "classification_evidence")

    def _predicate_binding_matches(self, binding: PredicateBinding) -> bool:
        expected = (self.assessment_binding.assessment_reference, self.assessment_binding.diagnosis_reference,
                    self.subject_reference, self.profile_binding.profile_id,
                    self.profile_binding.source_binding.source_sha256,
                    self.source_binding.dependency_id, self.source_binding.aggregate_sha256)
        actual = (binding.assessment_reference, binding.diagnosis_reference, binding.subject_reference,
                  binding.profile_id, binding.profile_source_sha256, binding.ash_dependency_id,
                  binding.ash_aggregate_sha256)
        return actual == expected

    def _validate_predicate_bindings(self, evidence: ClassificationEvidence) -> None:
        for field in PREDICATE_NAMES:
            if not self._predicate_binding_matches(getattr(evidence, field).binding):
                raise StateContractError("PREDICATE_BINDING_MISMATCH", field)


@dataclass(frozen=True, slots=True)
class StateDiagnosis(_StatePacket):
    outcome: ClassVar[str] = "diagnosis"

    def __post_init__(self) -> None:
        _StatePacket.__post_init__(self)
        if len(self.emitted_diagnostics) != 1:
            raise StateContractError("DIAGNOSTIC_ENVELOPE_INVALID", "emitted_diagnostics")

    def to_record(self) -> dict[str, object]:
        return self._common_record()


@dataclass(frozen=True, slots=True)
class StateAssessment(_StatePacket):
    system_context: SystemContext
    classification_evidence: ClassificationEvidence
    system_state_class: str
    recovery_category: str
    consulted_predicates: tuple[str, ...]
    outcome: ClassVar[str] = "assessment"

    def __post_init__(self) -> None:
        _StatePacket.__post_init__(self)
        self._contextual_values(self.system_context, self.classification_evidence)
        self._validate_predicate_bindings(self.classification_evidence)
        _require_type(self.system_state_class, str, "DIAGNOSTIC_ROW_INVALID", "system_state_class")
        _require_type(self.recovery_category, str, "DIAGNOSTIC_ROW_INVALID", "recovery_category")
        if (self.system_state_class, self.recovery_category) not in RECOVERY_CATEGORY_PAIRS:
            raise StateContractError("DIAGNOSTIC_ROW_INVALID", "recovery_category")
        _require_type(self.consulted_predicates, (list, tuple), "PREDICATE_EVIDENCE_INVALID", "consulted_predicates")
        if len(self.consulted_predicates) > 1:
            raise StateContractError("PREDICATE_EVIDENCE_INVALID", "consulted_predicates")
        for field in self.consulted_predicates:
            _choice(field, PREDICATE_NAMES, "PREDICATE_EVIDENCE_INVALID", "consulted_predicates")
            _require_type(getattr(self.classification_evidence, field), EvaluatedPredicate,
                          "PREDICATE_NOT_EVALUATED", field)
        object.__setattr__(self, "consulted_predicates", tuple(self.consulted_predicates))
        if len(self.emitted_diagnostics) != 2:
            raise StateContractError("DIAGNOSTIC_ENVELOPE_INVALID", "emitted_diagnostics")

    def to_record(self) -> dict[str, object]:
        return {**self._common_record(), "system_context": self.system_context.to_record(),
                "classification_evidence": self.classification_evidence.to_record(),
                "system_state_class": self.system_state_class, "recovery_category": self.recovery_category,
                "consulted_predicates": list(self.consulted_predicates)}


@dataclass(frozen=True, slots=True)
class ClassificationEvidenceFailure(_StatePacket):
    failure_code: str
    failed_predicate: str
    system_context: SystemContext
    classification_evidence: ClassificationEvidence
    outcome: ClassVar[str] = "failure"
    failure_kind: ClassVar[str] = "classification_evidence"

    def __post_init__(self) -> None:
        _StatePacket.__post_init__(self)
        _choice(self.failure_code, ("PREDICATE_BINDING_MISMATCH", "PREDICATE_NOT_EVALUATED"),
                "PREDICATE_EVIDENCE_INVALID", "failure_code")
        _choice(self.failed_predicate, PREDICATE_NAMES, "PREDICATE_EVIDENCE_INVALID", "failed_predicate")
        self._contextual_values(self.system_context, self.classification_evidence)
        if self.failure_code == "PREDICATE_NOT_EVALUATED":
            self._validate_predicate_bindings(self.classification_evidence)
            _require_type(getattr(self.classification_evidence, self.failed_predicate), NotEvaluatedPredicate,
                          "PREDICATE_EVIDENCE_INVALID", "failed_predicate")
        elif self._predicate_binding_matches(getattr(self.classification_evidence, self.failed_predicate).binding):
            raise StateContractError("PREDICATE_EVIDENCE_INVALID", "failed_predicate")
        if len(self.emitted_diagnostics) != 1:
            raise StateContractError("DIAGNOSTIC_ENVELOPE_INVALID", "emitted_diagnostics")

    def to_record(self) -> dict[str, object]:
        return {**self._common_record(), "failure_kind": self.failure_kind,
                "failure_code": self.failure_code, "failed_predicate": self.failed_predicate,
                "system_context": self.system_context.to_record(),
                "classification_evidence": self.classification_evidence.to_record()}


@dataclass(frozen=True, slots=True)
class DiagnosticCaptureFailure(_StatePacket):
    failure_code: str
    capture_status: str
    attempted_diagnostic: DiagnosticEmission
    system_context: SystemContext | None
    classification_evidence: ClassificationEvidence | None
    outcome: ClassVar[str] = "failure"
    failure_kind: ClassVar[str] = "diagnostic_capture"

    def __post_init__(self) -> None:
        _StatePacket.__post_init__(self)
        code = "DIAGNOSTIC_ENVELOPE_INVALID"
        _choice(self.failure_code, ("DIAGNOSTIC_CAPTURE_REJECTED", "DIAGNOSTIC_CAPTURE_UNCONFIRMED"), code, "failure_code")
        _choice(self.capture_status, ("REJECTED", "NOT_CONFIRMED"), code, "capture_status")
        if (self.failure_code == "DIAGNOSTIC_CAPTURE_REJECTED") != (self.capture_status == "REJECTED"):
            raise StateContractError(code, "capture_status")
        _require_type(self.attempted_diagnostic, DiagnosticEmission, code, "attempted_diagnostic")
        if (self.system_context is None) != (self.classification_evidence is None):
            raise StateContractError(code, "system_context")
        if self.system_context is not None:
            self._contextual_values(self.system_context, self.classification_evidence)
        if len(self.emitted_diagnostics) > 1:
            raise StateContractError(code, "emitted_diagnostics")
        self._validate_emission(self.attempted_diagnostic, len(self.emitted_diagnostics))
        if len(self.emitted_diagnostics) == 1 and self.system_context is None:
            raise StateContractError(code, "system_context")

    def to_record(self) -> dict[str, object]:
        return {**self._common_record(), "failure_kind": self.failure_kind,
                "failure_code": self.failure_code, "capture_status": self.capture_status,
                "attempted_diagnostic": self.attempted_diagnostic.to_record(),
                "system_context": None if self.system_context is None else self.system_context.to_record(),
                "classification_evidence": (None if self.classification_evidence is None
                                            else self.classification_evidence.to_record())}
