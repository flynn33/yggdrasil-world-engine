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
        consulted = ()
        if context.is_in_safe_halt:
            classification = "SAFE_HALT"
        elif context.is_in_containment:
            classification = "CONTAINED"
        elif status == "VALID":
            classification = "STABLE"
        elif status == "TRANSFORMATION_COMPATIBLE":
            consulted = ("correction_path_is_known",)
            fact = evidence.correction_path_is_known
            if type(fact) is not values.EvaluatedPredicate:
                return self._predicate_failure(common, consulted[0], context, evidence)
            classification = "CORRECTABLE" if fact.value else "UNSTABLE"
        elif status == "TRANSFORMATION_INCOMPATIBLE":
            consulted = ("fallback_is_available",)
            fact = evidence.fallback_is_available
            if type(fact) is not values.EvaluatedPredicate:
                return self._predicate_failure(common, consulted[0], context, evidence)
            classification = "DEGRADED" if fact.value else "FAILED"
        else:
            classification = "DEGRADED"
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
    model = StateModel(wrw_profile_binding(), values.CanonicalAshBinding(**dict(values.CANONICAL_BINDING_FIELDS)), RecordingDiagnosticCapture())
    result = model.diagnose(decoded.state if decoded.state is not None else candidate, diagnostic_context=context)
    if type(result) is not values.StateDiagnosis:
        raise values.StateContractError("DIAGNOSTIC_CAPTURE_UNCONFIRMED", "legacy_diagnosis")
    flattened = result.emitted_diagnostics[0].envelope.to_record()
    flattened["parent_diagnostic_reference"] = "NONE"
    flattened.update(result.state_validity_diagnostic.to_record())
    return flattened
