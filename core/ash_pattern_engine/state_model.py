"""Profile-bound ASH reference assessment, not an operational recovery engine.

Owned by YWE-REQ-0039. The canonical source and the adopted M3 assessment
contract define the mathematics, branch order and bounded representation policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DecimalException
import hashlib
import json
import math
from types import MappingProxyType

from . import state_values as values


_RECOVERY = MappingProxyType({
    "STABLE": "NO_ACTION", "UNSTABLE": "NORMALIZE_STATE",
    "CORRECTABLE": "APPLY_CORRECTION", "DEGRADED": "FALLBACK_REQUIRED",
    "CONTAINED": "CONTAINMENT_REQUIRED", "FAILED": "ESCALATION_REQUIRED",
    "SAFE_HALT": "TERMINAL_NO_RECOVERY",
})
_IMPACT = MappingProxyType({
    "STABLE": ("INFO", "RESOLVED"), "UNSTABLE": ("WARNING", "PENDING"),
    "CORRECTABLE": ("ERROR", "PENDING"), "DEGRADED": ("ERROR", "PENDING"),
    "FAILED": ("ERROR", "BLOCKED"), "CONTAINED": ("CRITICAL", "PENDING"),
    "SAFE_HALT": ("CRITICAL", "TERMINAL"),
})
_ROWS = MappingProxyType({
    "VALID": ("COMPATIBLE", "ALREADY_VALID", "NO_RECOVERY_NEEDED", True),
    "TRANSFORMATION_COMPATIBLE": ("COMPATIBLE", "NORMALIZABLE", "RECOVERY_APPLICABLE", False),
    "TRANSFORMATION_INCOMPATIBLE": ("INCOMPATIBLE", "NOT_NORMALIZABLE", "NOT_RECOVERABLE", False),
    "UNCLASSIFIED": ("UNKNOWN", "BLOCKED", "CONTAINMENT_NEEDED", False),
})
_DIAGNOSIS_RULES = (
    "ASH-STATE-STRUCTURE-001", "ASH-ADMISSIBILITY-CLASSIFICATION-001",
    "ASH-STATE-VALIDITY-001",
)
_SEMANTIC_FIELDS = (
    "input_state", "admissibility_status", "transformation_compatibility",
    "normalization_status", "recoverability_relevance", "is_valid", "orbit_info",
)


@dataclass(frozen=True)
class DecodedInput:
    state: values.AshState | None
    input_evidence: values.InputEvidence


class _DecodeIssue(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class StateInputCodec:
    """Decode only bounded, exact representations; preserve rejected observations."""

    MAX_BYTES = 4096
    MAX_DEPTH = 32
    MAX_TOKEN = 128
    MAX_KEYS = 64

    def decode(self, candidate, *, original_input_reference, legacy_whitespace=False):
        values.InputEvidence.validate_reference(original_input_reference)
        if type(legacy_whitespace) is not bool:
            raise values.StateContractError("CONTEXT_INVALID", "legacy_whitespace")
        try:
            state = self._decode(candidate, legacy_whitespace=legacy_whitespace)
        except _DecodeIssue as exc:
            return DecodedInput(None, self._observe(candidate, original_input_reference, exc.code))
        return DecodedInput(state, self._observe(candidate, original_input_reference, None))

    def _decode(self, candidate, *, legacy_whitespace):
        raw = False
        if type(candidate) is values.AshState:
            return candidate
        if type(candidate) is bytes:
            if len(candidate) > self.MAX_BYTES:
                raise _DecodeIssue("INPUT_SIZE_LIMIT")
            try:
                text = candidate.decode("utf-8", errors="strict")
            except UnicodeError:
                raise _DecodeIssue("INPUT_UTF8_INVALID") from None
            self._scan_json(text)
            try:
                candidate = json.loads(
                    text, parse_float=self._decimal, parse_int=self._integer,
                    parse_constant=self._nonfinite, object_pairs_hook=self._object,
                )
            except _DecodeIssue:
                raise
            except (ValueError, RecursionError, DecimalException, OverflowError):
                raise _DecodeIssue("INPUT_JSON_INVALID") from None
            raw = True
        if type(candidate) is str:
            if len(candidate) > self.MAX_BYTES:
                raise _DecodeIssue("INPUT_SIZE_LIMIT")
            try:
                size = len(candidate.encode("utf-8", errors="strict"))
            except UnicodeError:
                raise _DecodeIssue("INPUT_UTF8_INVALID") from None
            if size > self.MAX_BYTES:
                raise _DecodeIssue("INPUT_SIZE_LIMIT")
            signature = candidate.strip() if legacy_whitespace else candidate
            if len(signature) != 9 or any(ch not in "01" for ch in signature):
                raise _DecodeIssue("INPUT_SIGNATURE_INVALID")
            return values.AshState(tuple(0 if ch == "0" else 1 for ch in signature))
        if type(candidate) is dict:
            if len(candidate) > self.MAX_KEYS:
                raise _DecodeIssue("INPUT_RECORD_SIZE_LIMIT")
            if any(type(key) is not str for key in candidate):
                raise _DecodeIssue("INPUT_RECORD_KEY_INVALID")
            if "state_space" not in candidate or "bits" not in candidate:
                raise _DecodeIssue("INPUT_RECORD_INVALID")
            if type(candidate["state_space"]) is not str or candidate["state_space"] != "F2^9":
                raise _DecodeIssue("INPUT_STATE_SPACE_INVALID")
            candidate = candidate["bits"]
        if type(candidate) is not list and type(candidate) is not tuple:
            raise _DecodeIssue("INPUT_KIND_UNSUPPORTED")
        if len(candidate) != 9:
            raise _DecodeIssue("STATE_WIDTH")
        bits = []
        for coordinate in candidate:
            kind = type(coordinate)
            if kind is int:
                if coordinate not in (0, 1):
                    raise _DecodeIssue("STATE_COORDINATE_VALUE")
            elif kind is float:
                if not math.isfinite(coordinate) or coordinate not in (0.0, 1.0):
                    raise _DecodeIssue("STATE_COORDINATE_VALUE")
            elif raw and kind is Decimal:
                if not coordinate.is_finite() or coordinate not in (Decimal(0), Decimal(1)):
                    raise _DecodeIssue("STATE_COORDINATE_VALUE")
            else:
                raise _DecodeIssue("STATE_COORDINATE_TYPE")
            bits.append(0 if coordinate == 0 else 1)
        return values.AshState(tuple(bits))

    def _scan_json(self, text):
        # Pre-scan does not parse recursively and ignores brackets/numbers in strings.
        depth = 0
        quoted = escaped = False
        index = 0
        while index < len(text):
            char = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                index += 1
                continue
            if char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > self.MAX_DEPTH:
                    raise _DecodeIssue("INPUT_DEPTH_LIMIT")
            elif char in "]}":
                depth -= 1
            elif char in "-0123456789":
                start = index
                while index < len(text) and text[index] in "+-0123456789.eE":
                    index += 1
                if index - start > self.MAX_TOKEN:
                    raise _DecodeIssue("INPUT_TOKEN_LIMIT")
                continue
            index += 1

    @staticmethod
    def _decimal(token):
        try:
            return Decimal(token)
        except (ValueError, DecimalException, OverflowError):
            raise _DecodeIssue("INPUT_NUMERIC_TOKEN_INVALID") from None

    @staticmethod
    def _integer(token):
        try:
            return int(token)
        except (ValueError, OverflowError):
            raise _DecodeIssue("INPUT_NUMERIC_TOKEN_INVALID") from None

    @staticmethod
    def _nonfinite(_token):
        raise _DecodeIssue("INPUT_JSON_NONFINITE")

    @staticmethod
    def _object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise _DecodeIssue("INPUT_JSON_DUPLICATE_KEY")
            result[key] = value
        return result

    def _observe(self, candidate, reference, failure):
        kind, length, unit, preview, encoding, truncated = (
            "UNSUPPORTED", None, "UNKNOWN", None, "TEXT", False
        )
        coordinates = ()
        if type(candidate) is bytes:
            kind, length, unit = "RAW_JSON", len(candidate), "BYTES"
            preview, encoding, truncated = candidate[:32].hex(), "HEX", length > 32
        elif type(candidate) is str:
            kind, length, unit = "SIGNATURE", len(candidate), "CHARACTERS"
            preview, truncated = candidate[:64], length > 64
        elif type(candidate) is list or type(candidate) is tuple or type(candidate) is values.AshState:
            sequence = candidate.bits if type(candidate) is values.AshState else candidate
            kind, length, unit = "BIT_SEQUENCE", len(sequence), "ELEMENTS"
            coordinates = self._coordinates(sequence)
            truncated = length > 9
        elif type(candidate) is dict:
            kind, length, unit = "STATE_RECORD", len(candidate), "KEYS"
            # Do not look up owned keys until all bounded keys have safe exact types.
            if length <= self.MAX_KEYS and all(type(key) is str for key in candidate):
                sequence = candidate.get("bits")
                if type(sequence) is list or type(sequence) is tuple:
                    coordinates = self._coordinates(sequence)
                    truncated = len(sequence) > 9
            else:
                truncated = True
        return values.InputEvidence(
            original_input_reference=reference, representation_kind=kind,
            observed_length=length, length_unit=unit, preview=preview,
            preview_encoding=encoding, truncated=truncated,
            coordinate_observations=coordinates, failure_code=failure,
        )

    @staticmethod
    def _coordinates(sequence):
        observations = []
        for index in range(min(len(sequence), 9)):
            value = sequence[index]
            kind = type(value)
            fields = {"index": index}
            if kind is int:
                if value in (0, 1):
                    fields.update(scalar_kind="INTEGER_BIT", value=value)
                else:
                    fields.update(scalar_kind="INTEGER_OTHER", sign=(value > 0) - (value < 0), bit_length=value.bit_length())
            elif kind is float:
                if math.isfinite(value):
                    fields.update(scalar_kind="FINITE_FLOAT", value=value.hex())
                else:
                    token = "NAN" if math.isnan(value) else "POSITIVE_INFINITY" if value > 0 else "NEGATIVE_INFINITY"
                    fields.update(scalar_kind="NONFINITE_FLOAT", value=token)
            elif kind is str:
                fields.update(scalar_kind="STRING", value=value[:64], total_length=len(value), truncated=len(value) > 64)
            else:
                fields.update(scalar_kind="UNSUPPORTED")
            observations.append(values.CoordinateObservation(**fields))
        return tuple(observations)


class RecordingDiagnosticCapture:
    """Explicit reference collaborator with fresh, bounded storage per assessment."""

    def begin(self, assessment_reference):
        return _RecordingAssessmentCapture(assessment_reference)


class _RecordingAssessmentCapture:
    def __init__(self, assessment_reference):
        self.assessment_reference = assessment_reference
        self._records = []

    def append(self, emission):
        if type(emission) is not values.DiagnosticEmission:
            raise values.StateContractError("DIAGNOSTIC_ENVELOPE_INVALID", "emission")
        envelope = emission.envelope
        valid = len(self._records) < 2
        if not self._records:
            valid = valid and envelope.stage == "DETECTION" and envelope.parent_diagnostic_reference is None and envelope.chain_root_reference == emission.diagnostic_reference
        else:
            first = self._records[0]
            valid = valid and envelope.stage == "CLASSIFICATION" and envelope.parent_diagnostic_reference == first.diagnostic_reference and envelope.chain_root_reference == first.diagnostic_reference and envelope.subject_reference == first.envelope.subject_reference and emission.diagnostic_reference != first.diagnostic_reference
        if not valid:
            return values.CaptureReceipt(emission.diagnostic_reference, "REJECTED")
        self._records.append(emission)
        return values.CaptureReceipt(emission.diagnostic_reference, "CONFIRMED")


class StateModel:
    """Own diagnosis, assessment and normalization reference value operations."""

    def __init__(self, profile_binding, canonical_binding, diagnostic_capture, *, normalization_capture=None):
        if type(profile_binding) is not values.AvailableProfileBinding and type(profile_binding) is not values.UnavailableProfileBinding:
            raise values.StateContractError("PROFILE_BINDING_INVALID", "profile_binding")
        if type(canonical_binding) is not values.CanonicalAshBinding:
            raise values.StateContractError("CANONICAL_BINDING_INVALID", "canonical_binding")
        values.canonical_source_baseline(canonical_binding)
        self._profile_binding = profile_binding
        self._canonical_binding = canonical_binding
        self._capture = diagnostic_capture
        self._normalization_capture = normalization_capture
        self._codec = StateInputCodec()

    @property
    def profile_binding(self):
        return self._profile_binding

    @property
    def canonical_binding(self):
        return self._canonical_binding

    def diagnose(self, candidate, *, diagnostic_context):
        return self._run(candidate, diagnostic_context, None, None)

    def _normalization_operations(self):
        from .normalization import _NormalizationOperations

        return _NormalizationOperations(
            self.profile_binding, self.canonical_binding,
            lambda state, evidence: self._diagnose(DecodedInput(state, evidence)),
            self._normalization_capture,
        )

    def plan_normalization(self, diagnosis, *, plan_reference, evidence_reference, policy_binding):
        return self._normalization_operations().plan(
            diagnosis, plan_reference=plan_reference, evidence_reference=evidence_reference,
            policy_binding=policy_binding,
        )

    def validate_normalization_plan(self, plan):
        return self._normalization_operations().validate(plan)

    def apply_normalization(self, plan, *, normalization_context):
        return self._normalization_operations().apply(plan, normalization_context=normalization_context)

    @staticmethod
    def _classify(status, context, evidence):
        if context.is_in_safe_halt:
            return "SAFE_HALT", (), None
        if context.is_in_containment:
            return "CONTAINED", (), None
        if status == "VALID":
            return "STABLE", (), None
        if status == "TRANSFORMATION_COMPATIBLE":
            field = "correction_path_is_known"
            fact = evidence.correction_path_is_known
            if type(fact) is not values.EvaluatedPredicate:
                return None, (field,), field
            return ("CORRECTABLE" if fact.value else "UNSTABLE"), (field,), None
        if status == "TRANSFORMATION_INCOMPATIBLE":
            field = "fallback_is_available"
            fact = evidence.fallback_is_available
            if type(fact) is not values.EvaluatedPredicate:
                return None, (field,), field
            return ("DEGRADED" if fact.value else "FAILED"), (field,), None
        return "DEGRADED", (), None

    def validate_assessment(self, submitted):
        """Compare a complete reported assessment without decoding or capture."""
        from . import recovery_values as rv

        if type(submitted) is not values.StateAssessment:
            raise rv.RecoveryContractError("RECOVERY_INPUT_INVALID", "origin_assessment")
        expected = classification = category = consulted = None

        def witness(code=None, field=None):
            return rv.AssessmentValidation(
                status="VERIFIED" if code is None else "REJECTED",
                submitted_assessment=submitted, current_source_binding=self.canonical_binding,
                current_profile_binding=self.profile_binding, expected_diagnostic=expected,
                expected_system_state_class=classification, expected_recovery_category=category,
                expected_consulted_predicates=consulted, failure_code=code, field_name=field,
            )

        if type(submitted.source_binding) is not values.CanonicalAshBinding:
            return witness("SOURCE_BINDING_MISMATCH", "origin_assessment.source_binding")
        if (type(submitted.profile_binding) is not values.AvailableProfileBinding and
                type(submitted.profile_binding) is not values.UnavailableProfileBinding):
            return witness("PROFILE_BINDING_MISMATCH", "origin_assessment.profile_binding")
        try:
            values.CanonicalAshBinding.__post_init__(submitted.source_binding)
        except values.StateContractError:
            return witness("SOURCE_BINDING_MISMATCH", "origin_assessment.source_binding")
        try:
            binding = submitted.profile_binding
            type(binding).__post_init__(binding)
            profile = binding.profile if type(binding) is values.AvailableProfileBinding else binding.evidence
            values._require_type(profile.source_binding, values.ProfileSourceBinding,
                                 "PROFILE_BINDING_INVALID", "source_binding")
            values.ProfileSourceBinding.__post_init__(profile.source_binding)
            if type(binding) is values.AvailableProfileBinding:
                states = profile.recognized_valid_states
                values._require_type(states, frozenset, "PROFILE_BINDING_INVALID", "recognized_valid_states")
                if len(states) > 512:
                    raise values.StateContractError("PROFILE_SIZE_LIMIT", "recognized_valid_states")
                for state in states:
                    values._require_type(state, values.AshState, "PROFILE_BINDING_INVALID", "recognized_valid_states")
                    values.AshState.__post_init__(state)
            type(profile).__post_init__(profile)
        except values.StateContractError:
            return witness("PROFILE_BINDING_MISMATCH", "origin_assessment.profile_binding")
        if submitted.source_binding != self.canonical_binding:
            return witness("SOURCE_BINDING_MISMATCH", "origin_assessment.source_binding")
        if submitted.profile_binding != self.profile_binding:
            return witness("PROFILE_BINDING_MISMATCH", "origin_assessment.profile_binding")
        try:
            for field, kind in (
                ("assessment_binding", values.AssessmentBinding),
                ("input_evidence", values.InputEvidence),
                ("system_context", values.SystemContext),
                ("classification_evidence", values.ClassificationEvidence),
                ("state_validity_diagnostic", values.StateValidityDiagnostic),
            ):
                values._require_type(getattr(submitted, field), kind, "DIAGNOSTIC_ROW_INVALID", field)
            values.AssessmentBinding.__post_init__(submitted.assessment_binding)
            values.InputEvidence.__post_init__(submitted.input_evidence)
            for coordinate in submitted.input_evidence.coordinate_observations:
                values.CoordinateObservation.__post_init__(coordinate)
            if submitted.parsed_state is not None:
                values._require_type(submitted.parsed_state, values.AshState, "DIAGNOSTIC_ROW_INVALID", "parsed_state")
                values.AshState.__post_init__(submitted.parsed_state)
            values.SystemContext.__post_init__(submitted.system_context)
            values.ClassificationEvidence.__post_init__(submitted.classification_evidence)
        except values.StateContractError as exc:
            field = exc.field_name.split(".", 1)[0]
            if field == "system_context" or exc.code == "CONTEXT_INVALID":
                field = "origin_assessment.system_context"
            elif field == "parsed_state":
                field = "origin_assessment.parsed_state"
            else:
                field = "origin_assessment.input_evidence"
            return witness("INPUT_BINDING_MISMATCH", field)

        if submitted.assessment_binding.original_input_reference != submitted.input_evidence.original_input_reference:
            return witness("INPUT_BINDING_MISMATCH", "origin_assessment.input_evidence")
        if (type(submitted.emitted_diagnostics) is not tuple or len(submitted.emitted_diagnostics) != 2 or
                any(type(emission) is not values.DiagnosticEmission for emission in submitted.emitted_diagnostics)):
            return witness("CLASSIFICATION_ENVELOPE_MISMATCH", "origin_assessment")

        expected = self._diagnose(DecodedInput(submitted.parsed_state, submitted.input_evidence))
        observed = submitted.state_validity_diagnostic
        for field in _SEMANTIC_FIELDS:
            actual = getattr(observed, field)
            try:
                if field == "input_state":
                    values._require_type(actual, (values.AshState, values.RejectedCandidateEvidence),
                                         "DIAGNOSTIC_ROW_INVALID", field)
                    type(actual).__post_init__(actual)
                    if type(actual) is values.RejectedCandidateEvidence:
                        values.InputEvidence.__post_init__(actual.input_evidence)
                        for coordinate in actual.input_evidence.coordinate_observations:
                            values.CoordinateObservation.__post_init__(coordinate)
                elif field == "orbit_info":
                    if actual is not None:
                        values._require_type(actual, values.OrbitInfo, "DIAGNOSTIC_ROW_INVALID", field)
                        values.OrbitInfo.__post_init__(actual)
                else:
                    values._require_type(actual, bool if field == "is_valid" else str,
                                         "DIAGNOSTIC_ROW_INVALID", field)
            except values.StateContractError:
                return witness("DIAGNOSIS_MISMATCH", "origin_assessment.state_validity_diagnostic." + field)
            if actual != getattr(expected, field):
                return witness("DIAGNOSIS_MISMATCH", "origin_assessment.state_validity_diagnostic." + field)
        if type(observed.rule_ids) is not tuple or any(type(rule) is not str for rule in observed.rule_ids):
            return witness("DIAGNOSIS_MISMATCH", "origin_assessment.state_validity_diagnostic.rule_ids")
        if observed.rule_ids != _DIAGNOSIS_RULES:
            return witness("DIAGNOSIS_MISMATCH", "origin_assessment.state_validity_diagnostic.rule_ids")
        try:
            values.StateValidityDiagnostic.__post_init__(observed)
        except values.StateContractError:
            return witness("DIAGNOSIS_MISMATCH", "origin_assessment.state_validity_diagnostic.notes")
        subject = submitted.subject_reference
        root = submitted.assessment_binding.diagnosis_reference
        for index, emission in enumerate(submitted.emitted_diagnostics):
            prefix = f"origin_assessment.emitted_diagnostics[{index}]"
            if type(emission.diagnostic_reference) is not str:
                return witness("CLASSIFICATION_ENVELOPE_MISMATCH", prefix + ".diagnostic_reference")
            if type(emission.envelope) is not values.DiagnosticEnvelope:
                return witness("CLASSIFICATION_ENVELOPE_MISMATCH", prefix + ".envelope")
            for field in ("diagnostic_kind", "stage", "severity", "disposition", "subject_reference", "chain_root_reference"):
                if type(getattr(emission.envelope, field)) is not str:
                    return witness("CLASSIFICATION_ENVELOPE_MISMATCH", prefix + ".envelope." + field)
            parent = emission.envelope.parent_diagnostic_reference
            if parent is not None and type(parent) is not str:
                return witness("CLASSIFICATION_ENVELOPE_MISMATCH", prefix + ".envelope.parent_diagnostic_reference")
        if submitted.emitted_diagnostics[0].diagnostic_reference != root:
            return witness("CLASSIFICATION_ENVELOPE_MISMATCH", "origin_assessment.emitted_diagnostics[0].diagnostic_reference")
        if submitted.emitted_diagnostics[1].diagnostic_reference == root:
            return witness("CLASSIFICATION_ENVELOPE_MISMATCH", "origin_assessment.emitted_diagnostics[1].diagnostic_reference")
        diagnostic_context = values.DiagnosticContext(
            submitted.assessment_binding.assessment_reference,
            submitted.assessment_binding.original_input_reference,
            submitted.assessment_binding.diagnosis_reference,
            submitted.emitted_diagnostics[1].diagnostic_reference,
        )
        for name in values.PREDICATE_NAMES:
            fact = getattr(submitted.classification_evidence, name)
            prefix = "origin_assessment.classification_evidence." + name
            try:
                type(fact).__post_init__(fact)
                values.PredicateBinding.__post_init__(fact.binding)
            except values.StateContractError:
                return witness("PREDICATE_BINDING_MISMATCH", prefix + ".binding.evidence_reference")
            if not self._matches(fact.binding, diagnostic_context, subject):
                expected_binding = (
                    ("assessment_reference", diagnostic_context.assessment_reference),
                    ("diagnosis_reference", diagnostic_context.detection_reference),
                    ("subject_reference", subject),
                    ("profile_id", self.profile_binding.profile_id),
                    ("profile_source_sha256", self.profile_binding.source_binding.source_sha256),
                    ("ash_dependency_id", self.canonical_binding.dependency_id),
                    ("ash_aggregate_sha256", self.canonical_binding.aggregate_sha256),
                )
                field = next(field for field, value in expected_binding if getattr(fact.binding, field) != value)
                return witness("PREDICATE_BINDING_MISMATCH", prefix + ".binding." + field)
        classification, consulted, missing = self._classify(
            expected.admissibility_status, submitted.system_context, submitted.classification_evidence,
        )
        if missing is not None:
            return witness("PREDICATE_NOT_EVALUATED", "origin_assessment.classification_evidence." + missing + ".evaluation")
        category = _RECOVERY[classification]
        for field, value in (("system_state_class", classification), ("recovery_category", category),
                             ("consulted_predicates", consulted)):
            actual = getattr(submitted, field)
            if (type(actual) is not (tuple if field == "consulted_predicates" else str) or
                    field == "consulted_predicates" and any(type(item) is not str for item in actual)):
                return witness("CLASSIFICATION_MISMATCH", "origin_assessment." + field)
            if actual != value:
                return witness("CLASSIFICATION_MISMATCH", "origin_assessment." + field)
        status = expected.admissibility_status
        detection_impact = (("INFO", "RESOLVED") if status == "VALID" else
                            ("WARNING", "PENDING") if status == "TRANSFORMATION_COMPATIBLE" else
                            ("ERROR", "BLOCKED"))
        for index, emission in enumerate(submitted.emitted_diagnostics):
            prefix = f"origin_assessment.emitted_diagnostics[{index}]"
            envelope = emission.envelope
            try:
                values.DiagnosticEmission.__post_init__(emission)
                values.DiagnosticEnvelope.__post_init__(envelope)
            except values.StateContractError:
                return witness("CLASSIFICATION_ENVELOPE_MISMATCH", prefix + ".envelope.summary")
            severity, disposition = detection_impact if index == 0 else _IMPACT[classification]
            fields = (
                ("diagnostic_kind", "STATE_VALIDITY"),
                ("stage", "DETECTION" if index == 0 else "CLASSIFICATION"),
                ("severity", severity), ("disposition", disposition),
                ("subject_reference", subject),
                ("parent_diagnostic_reference", None if index == 0 else diagnostic_context.detection_reference),
                ("chain_root_reference", diagnostic_context.detection_reference),
                ("rule_ids", _DIAGNOSIS_RULES if index == 0 else
                 ("ASH-CLASSIFICATION-MAPPING-001", "ASH-RECOVERY-ACTION-001")),
            )
            for field, value in fields:
                if getattr(envelope, field) != value:
                    return witness("CLASSIFICATION_ENVELOPE_MISMATCH", prefix + ".envelope." + field)
            if index == 0 and envelope.notes != observed.notes:
                return witness("DIAGNOSIS_MISMATCH", prefix + ".envelope.notes")
        try:
            values.StateAssessment.__post_init__(submitted)
        except values.StateContractError:
            return witness("INPUT_BINDING_MISMATCH", "origin_assessment.input_evidence")
        return witness()

    def diagnosis_from_assessment(self, submitted):
        validation = self.validate_assessment(submitted)
        if validation.status != "VERIFIED":
            return validation
        return values.StateDiagnosis(
            assessment_binding=submitted.assessment_binding, source_binding=submitted.source_binding,
            profile_binding=submitted.profile_binding, input_evidence=submitted.input_evidence,
            parsed_state=submitted.parsed_state, state_validity_diagnostic=submitted.state_validity_diagnostic,
            emitted_diagnostics=(submitted.emitted_diagnostics[0],),
        )

    def inspect_state(self, state):
        if type(state) is not values.AshState:
            raise values.StateContractError("STATE_COORDINATE_TYPE", "state")
        values.AshState.__post_init__(state)
        observation = values.InputEvidence(
            original_input_reference="inspection:state", representation_kind="BIT_SEQUENCE",
            observed_length=9, length_unit="ELEMENTS", preview=None, preview_encoding="TEXT",
            truncated=False, coordinate_observations=tuple(
                values.CoordinateObservation(index=index, scalar_kind="INTEGER_BIT", value=bit)
                for index, bit in enumerate(state.bits)
            ), failure_code=None,
        )
        return self._diagnose(DecodedInput(state, observation))

    def validate_known_correction(self, submitted, *, origin):
        from . import recovery_values as rv

        if type(submitted) is not rv.KnownCorrection:
            raise rv.RecoveryContractError("RECOVERY_PLAN_INVALID", "correction_observation.submitted")
        validation = self.validate_assessment(origin)
        target = diagnostic = None

        def witness(code=None, field=None):
            return rv.CorrectionValidation(
                status="VERIFIED" if code is None else "REJECTED", submitted_correction=submitted,
                origin_validation=validation, current_source_binding=self.canonical_binding,
                current_profile_binding=self.profile_binding, computed_target=target,
                target_diagnostic=diagnostic, failure_code=code, field_name=field,
            )

        if validation.status != "VERIFIED" or origin.parsed_state is None:
            return witness("ORIGIN_MISMATCH", "origin_assessment")
        rv.KnownCorrection.__post_init__(submitted)
        rv.EvidenceSourceBinding.__post_init__(submitted.source_binding)
        try:
            values.CanonicalAshBinding.__post_init__(submitted.canonical_binding)
        except values.StateContractError:
            return witness("SOURCE_BINDING_MISMATCH", "source_binding")
        if submitted.canonical_binding != self.canonical_binding:
            return witness("SOURCE_BINDING_MISMATCH", "source_binding")
        if (submitted.profile_id != self.profile_binding.profile_id or
                submitted.profile_source_sha256 != self.profile_binding.source_binding.source_sha256):
            return witness("PROFILE_BINDING_MISMATCH", "profile_binding")
        if (submitted.original_assessment_reference != origin.assessment_binding.assessment_reference or
                submitted.classification_evidence_reference !=
                origin.classification_evidence.correction_path_is_known.binding.evidence_reference):
            return witness("ORIGIN_MISMATCH", "origin_assessment")
        target = origin.parsed_state
        for index, codeword in enumerate(submitted.chain):
            try:
                values.AshState.__post_init__(codeword)
            except values.StateContractError:
                return witness("CHAIN_MEMBER_INVALID", f"chain[{index}]")
            if codeword.bits not in values.CANONICAL_CODEWORDS:
                return witness("CHAIN_MEMBER_INVALID", f"chain[{index}]")
            target = values.AshState(tuple(a ^ b for a, b in zip(target.bits, codeword.bits)))
        diagnostic = self.inspect_state(target)
        try:
            values.AshState.__post_init__(submitted.expected_target)
        except values.StateContractError:
            raise rv.RecoveryContractError("RECOVERY_PLAN_INVALID", "candidate_state") from None
        if target != submitted.expected_target:
            return witness("CHAIN_TARGET_MISMATCH", "candidate_state")
        if not diagnostic.is_valid:
            return witness("TARGET_NOT_VALID", "candidate_state")
        return witness()

    def assess(self, candidate, *, context, classification_evidence, diagnostic_context):
        if type(context) is not values.SystemContext:
            raise values.StateContractError("CONTEXT_INVALID", "context")
        if type(classification_evidence) is not values.ClassificationEvidence:
            raise values.StateContractError("PREDICATE_EVIDENCE_INVALID", "classification_evidence")
        return self._run(candidate, diagnostic_context, context, classification_evidence)

    def _run(self, candidate, diagnostic_context, context, evidence):
        if type(diagnostic_context) is not values.DiagnosticContext:
            raise values.StateContractError("DIAGNOSTIC_CONTEXT_INVALID", "diagnostic_context")
        decoded = self._codec.decode(candidate, original_input_reference=diagnostic_context.original_input_reference)
        diagnostic = self._diagnose(decoded)
        common = dict(
            assessment_binding=values.AssessmentBinding(
                diagnostic_context.assessment_reference,
                diagnostic_context.original_input_reference,
                diagnostic_context.detection_reference,
            ),
            source_binding=self.canonical_binding, profile_binding=self.profile_binding,
            input_evidence=decoded.input_evidence, parsed_state=decoded.state,
            state_validity_diagnostic=diagnostic, emitted_diagnostics=(),
        )
        status = diagnostic.admissibility_status
        severity, disposition = (
            ("INFO", "RESOLVED") if status == "VALID" else
            ("WARNING", "PENDING") if status == "TRANSFORMATION_COMPATIBLE" else
            ("ERROR", "BLOCKED")
        )
        subject = f"ash_state_{decoded.state.signature}" if decoded.state is not None else diagnostic_context.original_input_reference
        detection = values.DiagnosticEmission(
            diagnostic_context.detection_reference,
            values.DiagnosticEnvelope(
                diagnostic_kind="STATE_VALIDITY", severity=severity, stage="DETECTION",
                disposition=disposition, subject_reference=subject,
                parent_diagnostic_reference=None,
                chain_root_reference=diagnostic_context.detection_reference,
                rule_ids=diagnostic.rule_ids, summary=f"ASH state diagnosis: {status}",
                notes=diagnostic.notes,
            ),
        )
        scope, receipt = self._append(None, diagnostic_context.assessment_reference, detection)
        if receipt != "CONFIRMED":
            return self._capture_failure(common, detection, receipt, context, evidence)
        common["emitted_diagnostics"] = (detection,)
        if context is None:
            return values.StateDiagnosis(**common)
        for name in ("correction_path_is_known", "fallback_is_available"):
            fact = getattr(evidence, name)
            if not self._matches(fact.binding, diagnostic_context, subject):
                return values.ClassificationEvidenceFailure(
                    **common, failure_code="PREDICATE_BINDING_MISMATCH", failed_predicate=name,
                    system_context=context, classification_evidence=evidence,
                )
        classification, consulted, missing = self._classify(status, context, evidence)
        if missing is not None:
            return self._predicate_failure(common, missing, context, evidence)
        recovery = _RECOVERY[classification]
        severity, disposition = _IMPACT[classification]
        classified = values.DiagnosticEmission(
            diagnostic_context.classification_reference,
            values.DiagnosticEnvelope(
                diagnostic_kind="STATE_VALIDITY", severity=severity, stage="CLASSIFICATION",
                disposition=disposition, subject_reference=subject,
                parent_diagnostic_reference=diagnostic_context.detection_reference,
                chain_root_reference=diagnostic_context.detection_reference,
                rule_ids=("ASH-CLASSIFICATION-MAPPING-001", "ASH-RECOVERY-ACTION-001"),
                summary=f"ASH contextual classification: {classification}; category: {recovery}",
                notes=("Classification describes the supplied context and bound evidence; no recovery or lifecycle operation was executed.",),
            ),
        )
        scope, receipt = self._append(scope, diagnostic_context.assessment_reference, classified)
        if receipt != "CONFIRMED":
            return self._capture_failure(common, classified, receipt, context, evidence)
        common["emitted_diagnostics"] = (detection, classified)
        return values.StateAssessment(
            **common, system_context=context, classification_evidence=evidence,
            system_state_class=classification, recovery_category=recovery,
            consulted_predicates=consulted,
        )

    def _diagnose(self, decoded):
        state = decoded.state
        notes = []
        orbit_info = None
        if state is None:
            status = "UNCLASSIFIED"
            input_state = values.RejectedCandidateEvidence(decoded.input_evidence)
            notes.append(f"Candidate representation rejected: {decoded.input_evidence.failure_code}.")
        elif type(self.profile_binding) is values.UnavailableProfileBinding:
            status = "UNCLASSIFIED"
            input_state = state
            notes.append("Authoritative validity-profile data is unavailable; orbit membership was not inferred.")
        else:
            input_state = state
            members = self._orbit(state)
            recognized = self.profile_binding.profile.recognized_valid_states
            contains = any(values.AshState(tuple(int(bit) for bit in signature)) in recognized for signature in members)
            status = "VALID" if state in recognized else "TRANSFORMATION_COMPATIBLE" if contains else "TRANSFORMATION_INCOMPATIBLE"
            orbit_info = values.OrbitInfo(members[0], 16, contains)
            notes.append("Admissibility uses the explicitly bound profile and fixed canonical sixteen-codeword relation.")
        compatibility, normalization, relevance, is_valid = _ROWS[status]
        if status == "UNCLASSIFIED":
            notes.append("Transformation compatibility is unknown and normalization is blocked.")
        elif status == "TRANSFORMATION_INCOMPATIBLE":
            notes.append("No known-valid profile state is reachable by canonical codeword normalization.")
        return values.StateValidityDiagnostic(
            input_state=input_state, admissibility_status=status,
            transformation_compatibility=compatibility, normalization_status=normalization,
            recoverability_relevance=relevance, is_valid=is_valid, orbit_info=orbit_info,
            rule_ids=_DIAGNOSIS_RULES, notes=tuple(notes),
        )

    @staticmethod
    def _orbit(state):
        return tuple(sorted("".join(str(bit ^ code[index]) for index, bit in enumerate(state.bits)) for code in values.CANONICAL_CODEWORDS))

    def _matches(self, binding, context, subject):
        profile = self.profile_binding.profile if type(self.profile_binding) is values.AvailableProfileBinding else self.profile_binding.evidence
        return (
            binding.assessment_reference == context.assessment_reference and
            binding.diagnosis_reference == context.detection_reference and
            binding.subject_reference == subject and binding.profile_id == profile.profile_id and
            binding.profile_source_sha256 == profile.source_binding.source_sha256 and
            binding.ash_dependency_id == self.canonical_binding.dependency_id and
            binding.ash_aggregate_sha256 == self.canonical_binding.aggregate_sha256
        )

    def _append(self, scope, reference, emission):
        try:
            if scope is None:
                scope = self._capture.begin(reference)
            receipt = scope.append(emission)
        except Exception:
            return scope, "NOT_CONFIRMED"
        if type(receipt) is not values.CaptureReceipt or receipt.diagnostic_reference != emission.diagnostic_reference:
            return scope, "NOT_CONFIRMED"
        return scope, receipt.status

    @staticmethod
    def _capture_failure(common, attempted, receipt, context, evidence):
        return values.DiagnosticCaptureFailure(
            **common, failure_code="DIAGNOSTIC_CAPTURE_REJECTED" if receipt == "REJECTED" else "DIAGNOSTIC_CAPTURE_UNCONFIRMED",
            capture_status="REJECTED" if receipt == "REJECTED" else "NOT_CONFIRMED",
            attempted_diagnostic=attempted, system_context=context, classification_evidence=evidence,
        )

    @staticmethod
    def _predicate_failure(common, name, context, evidence):
        return values.ClassificationEvidenceFailure(
            **common, failure_code="PREDICATE_NOT_EVALUATED", failed_predicate=name,
            system_context=context, classification_evidence=evidence,
        )


def wrw_profile_binding():
    """Explicit immutable WRW reference projection, independent of public views."""
    source = values.ProfileSourceBinding(
        "data/ash_state/realm_bit_mapping.yaml",
        "751879429b53534de04033d500722e87bd35f8994c7aefdc67631bb7f3783455",
        "wrw_reference_profile:source_binding",
    )
    return values.AvailableProfileBinding(values.ValidityProfile(
        "wrw_reference_profile", source,
        tuple(values.AshState(tuple(1 if coordinate == anchor else 0 for coordinate in range(9))) for anchor in range(9)),
    ))


def legacy_diagnosis(candidate):
    """Bounded deterministic references and explicit diagnosis-only compatibility."""
    codec = StateInputCodec()
    decoded = codec.decode(candidate, original_input_reference="legacy:input", legacy_whitespace=True)
    observed = decoded.state.to_record() if decoded.state is not None else decoded.input_evidence.to_record()
    digest = hashlib.sha256(json.dumps(observed, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()
    context = values.DiagnosticContext(
        f"legacy:assessment:{digest}", f"legacy:bounded-input:{digest}",
        f"legacy:detection:{digest}", f"legacy:classification:{digest}",
    )
    # Whitespace compatibility is decoded once; no unknown provenance is certified.
    model = StateModel(wrw_profile_binding(), values.CanonicalAshBinding(**dict(values.CURRENT_CANONICAL_BINDING_FIELDS)), RecordingDiagnosticCapture())
    result = model.diagnose(decoded.state if decoded.state is not None else candidate, diagnostic_context=context)
    if type(result) is not values.StateDiagnosis:
        raise values.StateContractError("DIAGNOSTIC_CAPTURE_UNCONFIRMED", "legacy_diagnosis")
    flattened = result.emitted_diagnostics[0].envelope.to_record()
    flattened["parent_diagnostic_reference"] = "NONE"
    flattened.update(result.state_validity_diagnostic.to_record())
    return flattened
