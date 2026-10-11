"""Closed immutable strict realm/transition values [YWE-REQ-0046]."""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import re

from . import state_values as state

RAW_BUSINESS_LIMIT = 1_048_576
TEN_BYTE_LIMIT = 8192
PHASES = ("VALID_SOURCE", "IDENTITY", "SELECTION", "APPLICABILITY", "TRANSFORMATION")
BUSINESS_FAILURES = ("STATE_NOT_VALID", "PROFILE_UNAVAILABLE", "TRANSITION_UNKNOWN",
                     "CODEWORD_NOT_CANONICAL", "TRANSITION_NOT_APPLICABLE")
ERROR_CODES = ("REALM_TRANSITION_VALUE_INVALID", "REALM_TRANSITION_CATALOG_INVALID",
               "REALM_TRANSITION_SELECTION_INVALID", "REALM_TRANSITION_ORIGIN_REJECTED",
               "REALM_TRANSITION_RAW_PACKET_LIMIT")
ERROR_FIELDS = ("state_model", "diagnostics", "realm_transition_binding", "transition_catalog",
                "transition_selection", "origin_diagnosis", "operation_reference",
                "producer_result", "capture_scope", "raw_business_packet")
POLICY_IDENTITIES = (
    ("docs/design-planning/m3/realm-transition/REALM_TRANSITION_STANDARD_POLICY.json",
     "6df6e573a27612e513a673ac54d89338fc72bce19c77357ddb3c9f80501f6149"),
    ("docs/design-planning/m3/realm-transition/REALM_TRANSITION_RESTRICTED_TEST_POLICY.json",
     "608730096b94094a0f247011946c5e7093b82d8713b5c1122e57a5a15a6aee4d"),
)
SOURCE_PINS = (
    ("REALM_ENCODER_CONTRACT", "b3fa0deb71ae136c712f402f2b8159b7448ef8756a884369931ab7098bc83fbb"),
    ("REALM_IDENTITY", "43f274d9c8c1b7269938bf8661c42e91cf020d215683cb6dfa4b340ff975cad5"),
    ("TRANSITION_REGISTRY_CONTRACT", "f123b02c3390253cba5f50a04e9c69e9c20771c6dc7cff5bcdc7a3c85aa6471f"),
    ("TRANSITION_SYSTEM", "26c456f60fbb5c847714c4a9a49cf8d11ac48ef0a7d0c127da53bd893dd527c2"),
    ("TRANSFORMATION", "80623862ac8dfe72bdecea670f15f4f339c0096da1f63b9058a73458eeedd88e"),
    ("CODEWORDS", "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c"),
    ("ASH_STATE_SPACE", "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e"),
    ("STATE_ADMISSIBILITY", "5d9231331849a6359a8d8e537d0434ee78787bb14efe5da03f60e68ba3c1978e"),
    ("DIAGNOSTIC_SCHEMA", "1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa"),
    ("RULE_TAXONOMY", "7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196"),
    ("DIAGNOSTICS_MODULE_CONTRACT", "6bd5dc891960cbd9fcdc878de6b46b715912df43ccd1a2affc9793176776376b"),
)
SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")
PHASE_RULES = {
    "IDENTITY": ("ASH-STATE-IDENTITY-001",),
    "SELECTION": ("ASH-CODEWORD-SELECTION-001", "ASH-CODEWORD-STRUCTURE-001"),
    "APPLICABILITY": ("ASH-CODEWORD-APPLICABILITY-001",),
    "TRANSFORMATION": ("ASH-CODEWORD-TRANSFORMATION-001",),
}


class RealmTransitionContractError(ValueError):
    def __init__(self, code, field_name):
        if type(code) is not str or code not in ERROR_CODES:
            raise ValueError("invalid realm/transition error code")
        if type(field_name) is not str or field_name not in ERROR_FIELDS:
            raise ValueError("invalid realm/transition error field")
        self.code, self.field_name = code, field_name
        super().__init__(f"{code}: {field_name}")


def _fail(field="producer_result", code="REALM_TRANSITION_VALUE_INVALID"):
    raise RealmTransitionContractError(code, field)


def _exact(value, classes, field="producer_result"):
    allowed = classes if type(classes) is tuple else (classes,)
    if not any(type(value) is cls for cls in allowed):
        _fail(field)


def _text(value, *, maximum=512, pattern=None, field="producer_result"):
    if (type(value) is not str or not 1 <= len(value) <= maximum or
            any(0xD800 <= ord(char) <= 0xDFFF for char in value)):
        _fail(field)
    if pattern is not None and re.fullmatch(pattern, value, re.ASCII) is None:
        _fail(field)


def _ref(value, field="producer_result"):
    _text(value, maximum=256, pattern=r"[A-Za-z0-9][A-Za-z0-9._:/-]*", field=field)
    if value in ("NONE", "SELF"):
        _fail(field)


def _choice(value, domain, field="producer_result"):
    if type(value) is not str or value not in domain:
        _fail(field)


def _tuple(value, low, high, normalize, field="producer_result"):
    if type(value) is not tuple and not (normalize and type(value) is list):
        _fail(field)
    if not low <= len(value) <= high:
        _fail(field)
    return tuple(value)


def _equal(actual, expected, field="producer_result"):
    if actual != expected:
        _fail(field)


def record_reference(operation_reference, ordinal):
    _ref(operation_reference, "operation_reference")
    return "rt:" + hashlib.sha256(operation_reference.encode("utf-8")).hexdigest() + ":" + str(ordinal)


class _WireValue:
    __slots__ = ()

    def __post_init__(self):
        _walk(self, set(), normalize=True)

    def to_record(self):
        return json.loads(canonical_bytes(self))

    def canonical_bytes(self):
        return canonical_bytes(self)


class _Result(_WireValue):
    __slots__ = ("_issuer", "_cookie", "_self_identity")


@dataclass(frozen=True, slots=True)
class RealmTransitionSourcePin(_WireValue):
    source_id: str
    source_sha256: str


@dataclass(frozen=True, slots=True)
class RealmTransitionBinding(_WireValue):
    canonical_binding: state.CanonicalAshBinding
    profile_binding: state.ProfileBinding
    contract_pins: tuple[RealmTransitionSourcePin, ...]
    policy_source_reference: str
    policy_source_sha256: str
    policy_evidence_reference: str


@dataclass(frozen=True, slots=True)
class TransitionDefinition(_WireValue):
    transition_id: str
    display_name: str
    description: str
    codeword: state.AshState
    applicability_mask: str


@dataclass(frozen=True, slots=True)
class TransitionCatalog(_WireValue):
    binding: RealmTransitionBinding
    definitions: tuple[TransitionDefinition, ...]


@dataclass(frozen=True, slots=True)
class TransitionSelection(_WireValue):
    selection_kind: str
    transition_id: str | None
    codeword: state.AshState | None


@dataclass(frozen=True, slots=True)
class RealmIdentity(_WireValue):
    state_signature: str
    vertex_id: str
    realm_id: str
    orbit_id: str


@dataclass(frozen=True, slots=True)
class RealmTransitionGate(_WireValue):
    origin_assessment_reference: str
    verification_status: str
    admissibility_status: str
    is_valid: bool


@dataclass(frozen=True, slots=True)
class TransitionApplicabilityObservation(_WireValue):
    transition_id: str
    codeword: state.AshState
    source_state: state.AshState
    is_applicable: bool
    reason_code: str


@dataclass(frozen=True, slots=True)
class TransitionSelectionObservation(_WireValue):
    selection: TransitionSelection
    transition_id: str | None
    codeword: state.AshState | None
    status: str
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class TransitionTransformationObservation(_WireValue):
    transition_id: str
    codeword: state.AshState
    source_state: state.AshState
    candidate: state.AshState
    target_diagnosis: state.StateValidityDiagnostic


@dataclass(frozen=True, slots=True)
class RealmTransitionRecord(_WireValue):
    record_reference: str
    phase: str
    emission: state.DiagnosticEmission
    payload: object


@dataclass(frozen=True, slots=True)
class RealmEncodingResult(_Result):
    operation_reference: str
    binding: RealmTransitionBinding
    origin: state.StateDiagnosis
    origin_validation: state.DiagnosisValidation
    identity: RealmIdentity
    constructed_records: tuple[RealmTransitionRecord, ...]


@dataclass(frozen=True, slots=True)
class TransitionResolutionResult(_Result):
    operation_reference: str
    binding: RealmTransitionBinding
    origin: state.StateDiagnosis
    origin_validation: state.DiagnosisValidation
    catalog: TransitionCatalog
    availability: tuple[TransitionApplicabilityObservation, ...]
    constructed_records: tuple[RealmTransitionRecord, ...]


@dataclass(frozen=True, slots=True)
class TransitionApplicationResult(_Result):
    operation_reference: str
    binding: RealmTransitionBinding
    origin: state.StateDiagnosis
    origin_validation: state.DiagnosisValidation
    selection: TransitionSelection
    selected_definition: TransitionDefinition
    candidate: state.AshState
    target_diagnosis: state.StateValidityDiagnostic
    constructed_records: tuple[RealmTransitionRecord, ...]


@dataclass(frozen=True, slots=True)
class RealmTransitionFailure(_Result):
    operation_reference: str
    binding: RealmTransitionBinding
    origin: state.StateDiagnosis
    origin_validation: state.DiagnosisValidation
    action: str
    failed_phase: str
    failure_code: str
    selection: TransitionSelection | None
    selected_definition: TransitionDefinition | None
    constructed_records: tuple[RealmTransitionRecord, ...]


@dataclass(frozen=True, slots=True)
class RealmTransitionCaptureReceipt(_WireValue):
    operation_reference: str
    status: str
    result: RealmEncodingResult | TransitionResolutionResult | TransitionApplicationResult | RealmTransitionFailure
    confirmed_records: tuple[str, ...]
    attempted_record: RealmTransitionRecord | None
    completion: object | None
    final_observation: object | None
    failure_code: str | None


RESULT_TYPES = (RealmEncodingResult, TransitionResolutionResult, TransitionApplicationResult, RealmTransitionFailure)
OWNED_TYPES = (RealmTransitionSourcePin, RealmTransitionBinding, TransitionDefinition, TransitionCatalog,
               TransitionSelection, RealmIdentity, RealmTransitionGate, TransitionApplicabilityObservation,
               TransitionSelectionObservation, TransitionTransformationObservation, RealmTransitionRecord,
               *RESULT_TYPES, RealmTransitionCaptureReceipt)
STATE_TYPES = (state.AshState, state.CanonicalAshBinding, state.ProfileSourceBinding, state.ValidityProfile,
               state.UnavailableValidityProfileEvidence, state.AvailableProfileBinding,
               state.UnavailableProfileBinding, state.AssessmentBinding, state.CoordinateObservation,
               state.InputEvidence, state.RejectedCandidateEvidence, state.OrbitInfo,
               state.StateValidityDiagnostic, state.DiagnosticEnvelope, state.DiagnosticEmission,
               state.StateDiagnosis, state.DiagnosisValidation)


def _local(value, normalize):
    kind = type(value)
    if kind is RealmTransitionSourcePin:
        _choice(value.source_id, tuple(name for name, _ in SOURCE_PINS))
        _text(value.source_sha256, maximum=64, pattern=r"[0-9a-f]{64}")
    elif kind is RealmTransitionBinding:
        _exact(value.canonical_binding, state.CanonicalAshBinding, "realm_transition_binding")
        _equal(tuple(getattr(value.canonical_binding, name) for name, _ in state.MODULE_CANONICAL_BINDING_FIELDS),
               tuple(digest for _, digest in state.MODULE_CANONICAL_BINDING_FIELDS), "realm_transition_binding")
        _exact(value.profile_binding, (state.AvailableProfileBinding, state.UnavailableProfileBinding), "realm_transition_binding")
        if type(value.profile_binding) is state.UnavailableProfileBinding:
            _text(value.profile_binding.evidence.reason, field="realm_transition_binding")
        pins = _tuple(value.contract_pins, 11, 11, normalize, "realm_transition_binding")
        for pin in pins:
            _exact(pin, RealmTransitionSourcePin, "realm_transition_binding")
        _equal(tuple((pin.source_id, pin.source_sha256) for pin in pins), SOURCE_PINS, "realm_transition_binding")
        _equal((value.policy_source_reference, value.policy_source_sha256) in POLICY_IDENTITIES, True, "realm_transition_binding")
        _ref(value.policy_evidence_reference, "realm_transition_binding")
        if normalize:
            object.__setattr__(value, "contract_pins", pins)
    elif kind is TransitionDefinition:
        _text(value.transition_id, maximum=256, pattern=r"ash_codeword_(?:0[0-9]|1[0-5])")
        _text(value.display_name)
        _text(value.description)
        _exact(value.codeword, state.AshState)
        _text(value.applicability_mask, maximum=512, pattern=r"[01]{512}")
    elif kind is TransitionCatalog:
        _exact(value.binding, RealmTransitionBinding, "transition_catalog")
        definitions = _tuple(value.definitions, 16, 16, normalize, "transition_catalog")
        restricted = value.binding.policy_source_sha256 == POLICY_IDENTITIES[1][1]
        for index, definition in enumerate(definitions):
            _exact(definition, TransitionDefinition, "transition_catalog")
            expected = (f"ash_codeword_{index:02d}", f"ASH codeword {index:02d}",
                        "Apply the complete canonical nine-coordinate XOR codeword.",
                        state.CANONICAL_CODEWORDS[index], "1" + "0" * 511 if restricted and index == 0 else "1" * 512)
            _equal((definition.transition_id, definition.display_name, definition.description,
                    definition.codeword.bits, definition.applicability_mask), expected, "transition_catalog")
        if normalize:
            object.__setattr__(value, "definitions", definitions)
    elif kind is TransitionSelection:
        _choice(value.selection_kind, ("IDENTIFIER", "CODEWORD"), "transition_selection")
        if value.selection_kind == "IDENTIFIER":
            _ref(value.transition_id, "transition_selection")
            _equal(value.codeword, None, "transition_selection")
        else:
            _exact(value.codeword, state.AshState, "transition_selection")
            _equal(value.transition_id, None, "transition_selection")
    elif kind is RealmIdentity:
        _text(value.state_signature, maximum=9, pattern=r"[01]{9}")
        _equal(value.vertex_id, "ash_state_" + value.state_signature)
        _equal(value.realm_id, value.vertex_id)
        _text(value.orbit_id, maximum=9, pattern=r"[01]{9}")
        orbit = tuple("".join(str(int(bit) ^ code[index]) for index, bit in enumerate(value.state_signature))
                      for code in state.CANONICAL_CODEWORDS)
        _equal(value.orbit_id, min(orbit))
    elif kind is RealmTransitionGate:
        _ref(value.origin_assessment_reference)
        _equal(value.verification_status, "VERIFIED")
        _choice(value.admissibility_status, ("VALID", "TRANSFORMATION_COMPATIBLE", "TRANSFORMATION_INCOMPATIBLE", "UNCLASSIFIED"))
        _exact(value.is_valid, bool)
        _equal(value.is_valid, value.admissibility_status == "VALID")
    elif kind is TransitionApplicabilityObservation:
        _text(value.transition_id, maximum=256, pattern=r"ash_codeword_(?:0[0-9]|1[0-5])")
        _exact(value.codeword, state.AshState)
        _exact(value.source_state, state.AshState)
        _exact(value.is_applicable, bool)
        _equal(value.codeword.bits, state.CANONICAL_CODEWORDS[int(value.transition_id[-2:])])
        _equal(value.reason_code, "SOURCE_ALLOWED" if value.is_applicable else "SOURCE_NOT_ALLOWED")
    elif kind is TransitionSelectionObservation:
        _exact(value.selection, TransitionSelection)
        _choice(value.status, ("SELECTED", "REFUSED"))
        if value.status == "SELECTED":
            _text(value.transition_id, maximum=256, pattern=r"ash_codeword_(?:0[0-9]|1[0-5])")
            _exact(value.codeword, state.AshState)
            _equal(value.codeword.bits, state.CANONICAL_CODEWORDS[int(value.transition_id[-2:])])
            _equal(value.failure_code, None)
            _equal(value.transition_id if value.selection.selection_kind == "IDENTIFIER" else value.codeword,
                   value.selection.transition_id if value.selection.selection_kind == "IDENTIFIER" else value.selection.codeword)
        else:
            _equal(value.transition_id, None)
            _equal(value.codeword, None)
            expected = "TRANSITION_UNKNOWN" if value.selection.selection_kind == "IDENTIFIER" else "CODEWORD_NOT_CANONICAL"
            _equal(value.failure_code, expected)
            if value.selection.selection_kind == "IDENTIFIER":
                if value.selection.transition_id in tuple(f"ash_codeword_{i:02d}" for i in range(16)):
                    _fail()
            elif value.selection.codeword.bits in state.CANONICAL_CODEWORDS:
                _fail()
    elif kind is TransitionTransformationObservation:
        _text(value.transition_id, maximum=256, pattern=r"ash_codeword_(?:0[0-9]|1[0-5])")
        for item in (value.codeword, value.source_state, value.candidate):
            _exact(item, state.AshState)
        _equal(value.codeword.bits, state.CANONICAL_CODEWORDS[int(value.transition_id[-2:])])
        _equal(value.candidate.bits, tuple(bit ^ code for bit, code in zip(value.source_state.bits, value.codeword.bits)))
        _exact(value.target_diagnosis, state.StateValidityDiagnostic)
        _equal(value.target_diagnosis.input_state, value.candidate)
    elif kind is RealmTransitionRecord:
        _ref(value.record_reference)
        _choice(value.phase, PHASES)
        _exact(value.emission, state.DiagnosticEmission)
        _equal(value.record_reference, value.emission.diagnostic_reference)
        payload_type = {"VALID_SOURCE": RealmTransitionGate, "IDENTITY": RealmIdentity,
                        "SELECTION": TransitionSelectionObservation,
                        "APPLICABILITY": TransitionApplicabilityObservation,
                        "TRANSFORMATION": TransitionTransformationObservation}[value.phase]
        _exact(value.payload, payload_type)
        envelope = value.emission.envelope
        _equal(envelope.stage, "PROCESSING")
        _choice(envelope.diagnostic_kind, ("REALM_ENCODING", "TRANSITION"))
        _equal(envelope.diagnostic_kind, "REALM_ENCODING" if value.phase == "IDENTITY" else "TRANSITION" if value.phase != "VALID_SOURCE" else envelope.diagnostic_kind)
        rules = (("ASH-STATE-VALIDITY-001",) if envelope.diagnostic_kind == "REALM_ENCODING" else
                 ("ASH-STATE-VALIDITY-001", "ASH-CODEWORD-REGISTRY-001")) if value.phase == "VALID_SOURCE" else PHASE_RULES[value.phase]
        _equal(envelope.rule_ids, rules)
        _equal(len(envelope.notes), 1)
        for text in (envelope.summary, *envelope.notes):
            _text(text)
            if any(char in text for char in ("\r", "\n", "\v", "\f", "\x1c", "\x1d", "\x1e", "\u0085", "\u2028", "\u2029")):
                _fail()
        if len(json.dumps(_shared_record(value.emission.envelope), separators=(",", ":"), ensure_ascii=True).encode("ascii")) > TEN_BYTE_LIMIT:
            _fail("raw_business_packet", "REALM_TRANSITION_RAW_PACKET_LIMIT")
    elif any(kind is cls for cls in RESULT_TYPES):
        _result_local(value, normalize)
    elif kind is RealmTransitionCaptureReceipt:
        from .diagnostics_values import DiagnosticsCompletionReceipt, enum_values
        from .diagnostic_module_values import ModuleFinalObservationReceipt, FAILURES
        _ref(value.operation_reference, "operation_reference")
        _choice(value.status, ("CONFIRMED", "REJECTED", "NOT_CONFIRMED"))
        _exact(value.result, RESULT_TYPES)
        _equal(value.operation_reference, value.result.operation_reference)
        refs = _tuple(value.confirmed_records, 0, 17, normalize)
        _equal(refs, tuple(record.record_reference for record in value.result.constructed_records[:len(refs)]))
        if value.attempted_record is not None:
            _exact(value.attempted_record, RealmTransitionRecord)
            _equal(value.attempted_record, value.result.constructed_records[len(refs)])
        if value.failure_code is not None:
            _choice(value.failure_code, (*FAILURES, *enum_values("DiagnosticsFailure")))
        if value.completion is not None:
            _exact(value.completion, DiagnosticsCompletionReceipt)
        if value.final_observation is not None:
            _exact(value.final_observation, ModuleFinalObservationReceipt)
        if value.status == "CONFIRMED":
            _equal(len(refs), len(value.result.constructed_records))
            _equal(value.attempted_record, None)
            _equal(value.failure_code, None)
            if value.completion is None or value.final_observation is None:
                _fail()
            _equal(value.completion.status, "COMPLETE")
            _equal(value.final_observation.status, "CONFIRMED")
            _equal(value.completion.operation_reference, value.operation_reference)
            _equal(value.final_observation.operation_reference, value.operation_reference)
        if normalize:
            object.__setattr__(value, "confirmed_records", refs)


def _result_local(value, normalize):
    _ref(value.operation_reference, "operation_reference")
    _exact(value.binding, RealmTransitionBinding)
    _exact(value.origin, state.StateDiagnosis)
    _exact(value.origin_validation, state.DiagnosisValidation)
    validation = value.origin_validation
    _equal(validation.status, "VERIFIED")
    _equal(validation.submitted_diagnosis, value.origin)
    _equal(validation.current_source_binding, value.binding.canonical_binding)
    _equal(validation.current_profile_binding, value.binding.profile_binding)
    records = _tuple(value.constructed_records, 1, 17, normalize)
    for ordinal, record in enumerate(records):
        _exact(record, RealmTransitionRecord)
        _equal(record.record_reference, record_reference(value.operation_reference, ordinal))
        envelope, root = record.emission.envelope, value.origin.emitted_diagnostics[0].envelope
        _equal(envelope.subject_reference, root.subject_reference)
        _equal(envelope.chain_root_reference, root.chain_root_reference)
        _equal(envelope.parent_diagnostic_reference, value.origin.emitted_diagnostics[0].diagnostic_reference if ordinal == 0 else records[ordinal - 1].record_reference)
        previous = root.severity if ordinal == 0 else records[ordinal - 1].emission.envelope.severity
        if SEVERITIES.index(envelope.severity) < SEVERITIES.index(previous):
            _fail()
    first = records[0]
    _equal(first.phase, "VALID_SOURCE")
    _equal(first.payload, RealmTransitionGate(value.origin.assessment_binding.assessment_reference, "VERIFIED",
                                            value.origin.state_validity_diagnostic.admissibility_status,
                                            value.origin.state_validity_diagnostic.is_valid))
    kind = type(value)
    if kind is RealmEncodingResult:
        _exact(value.identity, RealmIdentity)
        _equal(value.origin.parsed_state.signature, value.identity.state_signature)
        _equal(tuple(r.phase for r in records), ("VALID_SOURCE", "IDENTITY"))
        _equal(records[-1].payload, value.identity)
    elif kind is TransitionResolutionResult:
        _exact(value.catalog, TransitionCatalog)
        _equal(value.catalog.binding, value.binding)
        availability = _tuple(value.availability, 16, 16, normalize)
        _equal(tuple(r.phase for r in records), ("VALID_SOURCE",) + ("APPLICABILITY",) * 16)
        _equal(tuple(r.payload for r in records[1:]), availability)
        for definition, observed in zip(value.catalog.definitions, availability):
            expected = TransitionApplicabilityObservation(definition.transition_id, definition.codeword,
                         value.origin.parsed_state, definition.applicability_mask[int(value.origin.parsed_state.signature, 2)] == "1",
                         "SOURCE_ALLOWED" if definition.applicability_mask[int(value.origin.parsed_state.signature, 2)] == "1" else "SOURCE_NOT_ALLOWED")
            _equal(observed, expected)
        if normalize:
            object.__setattr__(value, "availability", availability)
    elif kind is TransitionApplicationResult:
        _exact(value.selection, TransitionSelection)
        _exact(value.selected_definition, TransitionDefinition)
        _exact(value.candidate, state.AshState)
        _exact(value.target_diagnosis, state.StateValidityDiagnostic)
        _equal(tuple(r.phase for r in records), ("VALID_SOURCE", "SELECTION", "APPLICABILITY", "TRANSFORMATION"))
        _equal(records[1].payload, TransitionSelectionObservation(value.selection, value.selected_definition.transition_id,
                                                                 value.selected_definition.codeword, "SELECTED", None))
        _equal(records[2].payload.is_applicable, True)
        _equal(records[3].payload, TransitionTransformationObservation(value.selected_definition.transition_id,
               value.selected_definition.codeword, value.origin.parsed_state, value.candidate, value.target_diagnosis))
        from .state_model import StateModel
        pure = StateModel(value.binding.profile_binding, value.binding.canonical_binding, None)
        _equal(value.target_diagnosis, StateModel.inspect_state(pure, value.candidate))
    else:
        _choice(value.action, ("ENCODE", "RESOLVE", "APPLY"))
        _choice(value.failure_code, BUSINESS_FAILURES)
        _choice(value.failed_phase, ("VALID_SOURCE", "SELECTION", "APPLICABILITY"))
        _equal(records[-1].phase, value.failed_phase)
        _equal(records[-1].emission.envelope.disposition, "BLOCKED")
        if value.selected_definition is not None:
            _exact(value.selected_definition, TransitionDefinition)
        if value.selection is not None:
            _exact(value.selection, TransitionSelection)
        if value.failed_phase == "VALID_SOURCE":
            _equal(len(records), 1)
            _equal(value.selected_definition, None)
            expected = "PROFILE_UNAVAILABLE" if type(value.binding.profile_binding) is state.UnavailableProfileBinding else "STATE_NOT_VALID"
            _equal(value.failure_code, expected)
            _equal(first.payload.is_valid, False)
        elif value.failed_phase == "SELECTION":
            _equal(tuple(r.phase for r in records), ("VALID_SOURCE", "SELECTION"))
            _equal(value.action, "APPLY")
            _equal(records[-1].payload.status, "REFUSED")
            _equal(records[-1].payload.failure_code, value.failure_code)
            _equal(records[-1].payload.selection, value.selection)
            _equal(value.selected_definition, None)
        else:
            _equal(tuple(r.phase for r in records), ("VALID_SOURCE", "SELECTION", "APPLICABILITY"))
            _equal(value.action, "APPLY")
            _equal(value.failure_code, "TRANSITION_NOT_APPLICABLE")
            _equal(records[-1].payload.is_applicable, False)
    if kind is not RealmTransitionFailure or value.failed_phase != "VALID_SOURCE":
        _equal(first.payload.is_valid, True)
    if normalize:
        object.__setattr__(value, "constructed_records", records)


def _shared_record(value):
    # Clean field copies cannot carry instance serializer/helper overrides.
    def copy(item):
        kind = type(item)
        if item is None or any(kind is scalar for scalar in (str, int, bool)):
            return item
        if kind is tuple:
            return tuple(copy(child) for child in item)
        if kind is frozenset:
            return frozenset(copy(child) for child in item)
        owned = object.__new__(kind)
        for field in fields(kind):
            object.__setattr__(owned, field.name, copy(getattr(item, field.name)))
        return owned
    owned = copy(value)
    return type(owned).to_record(owned)


def _walk(value, ancestors, *, normalize=False, depth=0):
    kind = type(value)
    if value is None or kind is bool:
        return
    if kind is str:
        # Existing N1 observations may retain an invalid UTF-8 input preview.
        # New module prose is separately scalar-checked by its owning fields.
        if len(value) > 512:
            _fail()
        return
    if kind is int:
        if abs(value).bit_length() > 64:
            _fail()
        return
    if depth > 20 or id(value) in ancestors:
        _fail()
    is_local = any(kind is cls for cls in OWNED_TYPES)
    is_state = any(kind is cls for cls in STATE_TYPES)
    is_receipt = any(kind is cls for cls in _receipt_types())
    if not is_local and not is_state and not is_receipt and not any(kind is container for container in (tuple, frozenset)) and not (normalize and kind is list):
        _fail()
    ancestors.add(id(value))
    try:
        if any(kind is container for container in (tuple, frozenset, list)):
            if len(value) > 512:
                _fail()
            for item in value:
                _walk(item, ancestors, normalize=normalize, depth=depth + 1)
        else:
            for field in fields(kind):
                try:
                    child = object.__getattribute__(value, field.name)
                except AttributeError:
                    _fail()
                _walk(child, ancestors, normalize=normalize, depth=depth + 1)
            if is_local:
                _local(value, normalize)
            elif is_receipt:
                for field in fields(kind):
                    if type(getattr(value, field.name)) is list:
                        _fail()
                kind.__post_init__(value)
            elif kind is state.DiagnosisValidation:
                state.DiagnosisValidation.__post_init__(value)
            elif kind is state.StateDiagnosis:
                # The shared public validator owns complete diagnosis coherence.
                from .state_model import StateModel
                model = StateModel(value.profile_binding, value.source_binding, None)
                StateModel.validate_diagnosis(model, value)
            else:
                immutable = {state.AshState: ("bits",), state.InputEvidence: ("coordinate_observations",),
                             state.StateValidityDiagnostic: ("rule_ids", "notes"),
                             state.DiagnosticEnvelope: ("rule_ids", "notes")}
                for name in immutable.get(kind, ()):
                    if type(getattr(value, name)) is not tuple:
                        _fail()
                if kind is state.ValidityProfile and type(value.recognized_valid_states) is not frozenset:
                    _fail()
                kind.__post_init__(value)
    finally:
        ancestors.remove(id(value))


def revalidate_value(value):
    _walk(value, set())


def _record(value):
    kind = type(value)
    if value is None or any(kind is scalar for scalar in (str, int, bool)):
        return value
    if kind is tuple:
        return [_record(item) for item in value]
    if any(kind is cls for cls in (*STATE_TYPES, *_receipt_types())):
        return _shared_record(value)
    return {field.name: _record(getattr(value, field.name)) for field in fields(kind)}


def _receipt_types():
    from . import diagnostics_values as diagnostics
    from .diagnostic_module_values import ModuleFinalObservationReceipt
    return (diagnostics.DiagnosticsCompletionReceipt, diagnostics.DiagnosticsHealth,
            diagnostics.MissingCoverage, diagnostics.RetentionBoundary,
            diagnostics.DiagnosticCounterState, ModuleFinalObservationReceipt)


def canonical_bytes(value, *, limit=RAW_BUSINESS_LIMIT):
    revalidate_value(value)
    if type(limit) is not int or not 1 <= limit <= RAW_BUSINESS_LIMIT:
        _fail("raw_business_packet")
    chunks, size = [], 0
    for text in json.JSONEncoder(ensure_ascii=True, separators=(",", ":"), allow_nan=False).iterencode(_record(value)):
        chunk = text.encode("ascii")
        size += len(chunk)
        if size > limit:
            _fail("raw_business_packet", "REALM_TRANSITION_RAW_PACKET_LIMIT")
        chunks.append(chunk)
    return b"".join(chunks)


def raw_business_size(value, *, limit=RAW_BUSINESS_LIMIT):
    try:
        return len(canonical_bytes(value, limit=limit))
    except RealmTransitionContractError as exc:
        if exc.code == "REALM_TRANSITION_RAW_PACKET_LIMIT":
            return limit + 1
        raise
