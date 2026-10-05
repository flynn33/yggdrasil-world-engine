"""Bounded reference Diagnostics composition [YWE-REQ-0042].

All observations and persistence cross explicit injected ports. Core performs no
source discovery, filesystem access, ambient clock lookup or native OS calls.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import re
import threading
from typing import Protocol

from . import diagnostics_values as dv
from . import state_values as sv
from . import normalization_values as nv


def _configured_source_snapshots(identity, snapshots):
    """Validate declared assembly input before any storage or clock effects."""
    revision = identity.source_revision
    if revision is not None and (type(revision) is not str or re.fullmatch(r"[0-9a-f]{40}", revision) is None):
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    if snapshots is None:
        snapshots = () if revision is None else (dv.SourcePin("ASH_AGGREGATE", dv.LEGACY_SOURCE_REVISION,
            dict(sv.CANONICAL_BINDING_FIELDS)["aggregate_sha256"]),)
    if type(snapshots) is not tuple or len(snapshots) > 2:
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    expected = tuple(dict(fields)["aggregate_sha256"] for _, fields in sv.CANONICAL_BINDING_BASELINES)
    indexes, result = [], []
    for pin in snapshots:
        if type(pin) is not dv.SourcePin:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        try:
            dv.SourcePin.__post_init__(pin)
        except (AttributeError, dv.DiagnosticsContractError):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE") from None
        if pin.source_kind != "ASH_AGGREGATE" or pin.sha256 not in expected:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        index = expected.index(pin.sha256)
        if pin.revision != (dv.LEGACY_SOURCE_REVISION if index == 0 else revision) or index == 1 and revision is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        indexes.append(index)
        result.append(dv.SourcePin(pin.source_kind, pin.revision, pin.sha256))
    if indexes != sorted(set(indexes)):
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    return tuple(result)


def _encode(value):
    return json.dumps(value.to_record(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _fingerprint(value):
    return hashlib.sha256(_encode(value)).hexdigest()


class DiagnosticsClockPort(Protocol):
    def read(self) -> dv.ClockObservation: ...


class ProtectedStore(Protocol):
    def verify(self) -> dv.StorageVerification: ...
    def commit_event(self, sequence: int, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_supporting(self, sequence: int, kind: str, evidence_alias: str, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_meta(self, sequence: int, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_incident(self, sequence: int, incident_alias: str, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_health(self, sequence: int | None, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def commit_fallback_health(self, sequence: int | None, redacted_bytes: bytes) -> dv.StorageReceipt: ...
    def write_pair(self, bundle_alias: str, json_bytes: bytes, markdown_bytes: bytes, manifest_bytes: bytes, *, last_included_sequence: int | None): ...
    def purge_bundle(self, bundle_alias: str) -> dv.StorePurgeReceipt: ...
    def purge_capture(self, request: dv.CapturePurgeRequest) -> dv.StoreCapturePurgeReceipt: ...


def _context(**values):
    row = {name: None for name in dv.CONTEXT_FIELDS}
    row.update(values)
    row["unavailable_fields"] = tuple(name.upper() for name, value in row.items() if value is None)
    row["input_failure_code"] = values.get("input_failure_code")
    return dv.SafeStateContext(**row)


def _orbit(value):
    return None if value is None else dv.SafeOrbit(value.orbit_id, value.contains_known_valid_state)


@dataclass(frozen=True, slots=True)
class _Origin:
    assessment_reference: str
    subject_reference: str
    chain_root_reference: str
    last_diagnostic_reference: str
    system_state_class: str | None
    recovery_category: str | None

    @classmethod
    def observed(cls, packet):
        last = packet.emitted_diagnostics[-1]
        return cls(packet.assessment_binding.assessment_reference,
                   last.envelope.subject_reference, last.envelope.chain_root_reference,
                   last.diagnostic_reference, getattr(packet, "system_state_class", None),
                   getattr(packet, "recovery_category", None))


class _CaptureScope:
    def __init__(self, owner, reference, producer, *, relation=None, original=None,
                 reserved_events=2, reserved_bytes=131072, reserved_aliases=64, denial=False):
        self.owner, self.reference, self.producer = owner, reference, producer
        self.relation = relation
        self.original = None if original is None else _Origin.observed(original)
        self.reserved_events, self.reserved_bytes, self.reserved_aliases = reserved_events, reserved_bytes, reserved_aliases
        self.remaining_events, self.remaining_bytes, self.remaining_aliases = reserved_events, reserved_bytes, reserved_aliases
        self.denial, self.finished = denial, False
        self.references, self.indices, self.hashes = [], [], []
        self.attempted_reference, self.attempted_hash, self.attempted_index = None, None, None
        self.failed, self.first_clock, self.last_envelope = None, owner._last_clock, None
        self.child_operations = []
        self.support_keys = set()
        self.purged = False
        self.step_indices = {}
        self.step_policies = {}
        self.remaining_incidents = 32 if producer == "RECOVERY_ENGINE" and not denial else 1
        if relation is not None:
            self.remaining_incidents = 0

    def append(self, record):
        return self.owner._append(self, record)

    def finish(self, result):
        return self.owner._complete(self, result, "RECOVERY_ENGINE")


class _AssessmentCapture:
    def __init__(self, owner, relation):
        self.owner, self.relation = owner, relation

    def begin(self, assessment_reference):
        return self.owner._begin(assessment_reference, "STATE_MODEL", relation=self.relation)


class _NormalizationCapture:
    def __init__(self, owner):
        self.owner = owner

    def begin(self, operation_reference, *, original_diagnosis):
        if type(original_diagnosis) is not sv.StateDiagnosis:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "ORIGINAL_DIAGNOSIS")
        self.owner._attached(original_diagnosis.emitted_diagnostics)
        return self.owner._begin(operation_reference, "NORMALIZATION", original=original_diagnosis)


class _RecoveryCapture:
    def __init__(self, owner):
        self.owner = owner

    def begin(self, origin, *, operation_reference):
        return self.owner._recovery_begin(origin, operation_reference, False)

    def begin_denial(self, origin, *, operation_reference):
        return self.owner._recovery_begin(origin, operation_reference, True)


class _ReferenceDiagnostics:
    _profile_id = None

    def __init__(self, identity, profile, store, clock, *, canonical_source_snapshots=None):
        if type(identity) is not dv.DiagnosticsIdentity or type(profile) is not dv.DiagnosticsProfile:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID")
        snapshots = _configured_source_snapshots(identity, canonical_source_snapshots)
        if identity.profile_id != self._profile_id or profile.profile_id != self._profile_id or identity.implementation_id != profile.implementation_id:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID")
        methods = ("verify", "commit_event", "commit_supporting", "commit_meta", "commit_health",
                   "commit_fallback_health", "write_pair", "purge_bundle", "purge_capture", "commit_incident")
        if any(not callable(getattr(store, method, None)) for method in methods) or not callable(getattr(clock, "read", None)):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID")
        self.identity, self.profile, self.store, self.clock = identity, profile, store, clock
        self._canonical_source_snapshots = snapshots
        self._lock, self._limits = threading.RLock(), dv.DiagnosticLimits()
        verification = store.verify()
        if type(verification) is not dv.StorageVerification or verification.status != "VERIFIED":
            raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
        self._aliases, self._next_alias = {}, 1
        # Assembly aliases are already safe identity values, never raw-key records.
        seeded = (identity.build_id, identity.session_reference, profile.selection_authority,
                  *identity.source_provenance.dirty_path_aliases)
        self._next_alias = max(int(item[4:]) for item in seeded) + 1
        self._events, self._meta, self._incidents, self._scopes, self._acks = [], [], [], {}, {}
        self._support = {kind: {} for kind in dv.enum_values("SupportingKind")}
        self._support_bytes, self._used, self._next_sequence = 0, 0, 0
        self._counts = dict.fromkeys(dv.enum_values("CounterField"), 0)
        self._saturated = set()
        self._redactions, self._retention = {}, []
        self._failure = self._fallback_cause = None
        self._incident_bytes = 0
        self._unconfirmed_incidents = []
        self._first_unavailable = self._last_unavailable = None
        self._storage = self._meta_storage = "PROTECTED_VERIFIED"
        self._producer_completed = set()
        self._issued_snapshots, self._export_slot = {}, None
        self._export_completed = False
        self._export_boundary = None
        self._last_clock = self._start_clock = self._observe_clock(initial=True)
        self._charging_scope = None
        self._persist_health()

    def _increment(self, field, amount=1):
        previous = self._counts[field]
        if previous is None:
            return
        if previous > (1 << 64) - 1 - amount:
            self._counts[field] = (1 << 64) - 1
            self._saturated.add(field)
            self._failure = "DIAGNOSTICS_COUNTER_LIMIT"
        else:
            self._counts[field] = previous + amount

    def _alias(self, reference):
        if type(reference) is not str or not 1 <= len(reference) <= 256 or not reference.isascii():
            raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")
        if reference in self._aliases:
            return self._aliases[reference]
        charged = self._charging_scope
        if charged is not None and charged.relation is not None:
            charged = self._scopes[charged.relation.parent_operation_reference]
        if charged is not None and charged.remaining_aliases <= 0:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
        reserved = sum(scope.remaining_aliases for scope in self._scopes.values() if not scope.finished)
        if charged is None and len(self._aliases) + reserved >= 6144:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
        if len(self._aliases) >= 6144 or self._next_alias > 999999:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
        alias = f"ref:{self._next_alias:06d}"
        self._next_alias += 1
        self._aliases[reference] = alias
        if charged is not None:
            charged.remaining_aliases -= 1
        self._increment("REDACTED_REFERENCES")
        return alias

    def _observe_clock(self, *, initial=False):
        try:
            observed = self.clock.read()
            if type(observed) is not dv.ClockObservation:
                raise ValueError()
        except Exception:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CLOCK_UNAVAILABLE") from None
        value = observed.monotonic_nanoseconds
        if value is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CLOCK_UNAVAILABLE")
        if not initial:
            previous = self._last_clock.monotonic_nanoseconds
            if value < previous:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_CLOCK_REGRESSION")
            if value - self._start_clock.monotonic_nanoseconds > 600000000000:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_DURATION_LIMIT")
            self._last_clock = observed
        return observed

    def _begin(self, reference, producer, *, relation=None, original=None,
               reserved_events=2, reserved_bytes=131072, reserved_aliases=64, denial=False):
        sv.InputEvidence.validate_reference(reference)
        with self._lock:
            if self.identity.source_revision is None or not self._canonical_source_snapshots:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE")
            self._observe_clock()
            if reference in self._scopes:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
            active = tuple(scope for scope in self._scopes.values() if not scope.finished)
            incidents = 32 if producer == "RECOVERY_ENGINE" and not denial else 1
            if relation is not None:
                reserved_events, reserved_bytes, reserved_aliases = 0, 0, 0
                incidents = 0
            if len(self._incidents) + len(self._unconfirmed_incidents) + sum(scope.remaining_incidents for scope in active) + incidents > 32:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if len(active) >= 8 or len(self._events) + sum(scope.remaining_events for scope in active) + reserved_events > 1024:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if self._used + sum(scope.remaining_bytes for scope in active) + reserved_bytes > 33554432:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
            if len(self._aliases) + sum(scope.remaining_aliases for scope in active) + reserved_aliases > 6144:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ALIAS_LIMIT")
            if relation is not None:
                from .recovery_values import PostAssessmentLink
                if type(relation) is not PostAssessmentLink:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                parent = self._scopes.get(relation.parent_operation_reference)
                if parent is None or parent.finished or parent.producer != "RECOVERY_ENGINE":
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                parent.child_operations.append(reference)
                # Children consume their operation's existing whole reservation.
                reserved_events, reserved_bytes, reserved_aliases = 0, 0, 0
            scope = _CaptureScope(self, reference, producer, relation=relation, original=original,
                reserved_events=reserved_events, reserved_bytes=reserved_bytes,
                reserved_aliases=reserved_aliases, denial=denial)
            self._scopes[reference] = scope
            previous_charge = self._charging_scope
            self._charging_scope = scope
            try:
                self._alias(reference)
            finally:
                self._charging_scope = previous_charge
            return scope

    def assessment_capture(self, *, relation=None):
        return _AssessmentCapture(self, relation)

    def normalization_capture(self):
        return _NormalizationCapture(self)

    def recovery_capture(self):
        return _RecoveryCapture(self)

    def _attached(self, emissions):
        for emission in emissions:
            witness = self._acks.get(emission.diagnostic_reference)
            if witness is None:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
            if witness.emission_sha256 != _fingerprint(emission):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        return True

    def _recovery_begin(self, origin, reference, denial):
        if type(origin) is not sv.StateAssessment:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "ORIGINAL_ASSESSMENT")
        sv.InputEvidence.validate_reference(reference)
        if len(reference) > 192:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")
        references = tuple(item.diagnostic_reference for item in origin.emitted_diagnostics)
        with self._lock:
            scope = None
            try:
                self._attached(origin.emitted_diagnostics)
                original_scope = self._scopes.get(origin.assessment_binding.assessment_reference)
                if original_scope is None or not original_scope.finished or original_scope.failed:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE")
                if denial != (origin.system_state_class == "SAFE_HALT" and origin.recovery_category == "TERMINAL_NO_RECOVERY"):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                scope = self._begin(reference, "RECOVERY_ENGINE", original=origin,
                    reserved_events=1 if denial else 768, reserved_bytes=270336 if denial else 31588352,
                    reserved_aliases=64 if denial else 5931, denial=denial)
                self._assessment_support(origin)
                self._persist_health()
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                return scope, dv.RecoveryAdmissionReceipt("CONFIRMED", reference,
                    origin.assessment_binding.assessment_reference, references,
                    scope.reserved_events, scope.reserved_bytes, None)
            except dv.DiagnosticsContractError as error:
                if scope is not None:
                    scope.finished, scope.failed = True, error.code
                self._mark_failure(error.code)
                return None, dv.RecoveryAdmissionReceipt("REJECTED", reference,
                    origin.assessment_binding.assessment_reference, references, 0, 0, error.code)

    def _safe_envelope(self, envelope, template):
        return dv.SafeDiagnosticEnvelope(envelope.diagnostic_kind, envelope.severity,
            envelope.stage, envelope.disposition, self._alias(envelope.subject_reference),
            None if envelope.parent_diagnostic_reference is None else self._alias(envelope.parent_diagnostic_reference),
            self._alias(envelope.chain_root_reference), envelope.rule_ids,
            dv.message_text(template), (dv.message_text("UNTRUSTED_PROSE_OMITTED"),))

    def _validate_chain(self, scope, emission, phase):
        envelope = emission.envelope
        previous = scope.last_envelope
        if emission.diagnostic_reference in self._acks:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED", "CHAIN")
        if envelope.subject_reference != (scope.original.subject_reference if scope.original else envelope.subject_reference):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        if scope.producer == "STATE_MODEL":
            if len(scope.indices) >= 2 or envelope.stage != ("DETECTION" if not scope.indices else "CLASSIFICATION") or any(rule not in sv.ASSESSMENT_RULE_IDS for rule in envelope.rule_ids):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CANONICAL_ENVELOPE")
        elif scope.producer == "NORMALIZATION":
            if len(scope.indices) >= 2 or phase != ("COMPUTATION" if not scope.indices else "POST_VALIDATION"):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "EXPECTED_STEP")
            if not scope.indices:
                if envelope.parent_diagnostic_reference != scope.original.last_diagnostic_reference or envelope.chain_root_reference != scope.original.chain_root_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            elif previous.disposition != "PENDING":
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "EXPECTED_STEP")
        elif scope.denial:
            from . import recovery_values as rv
            if scope.indices or envelope.stage != "DETECTION" or envelope.disposition != "BLOCKED" or envelope.severity != "CRITICAL" or envelope.diagnostic_kind != "STATE_VALIDITY" or envelope.parent_diagnostic_reference is not None or envelope.chain_root_reference != emission.diagnostic_reference or envelope.rule_ids != ("ASH-STATE-GENERAL-001", "ASH-RECOVERY-ACTION-001"):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        else:
            if envelope.diagnostic_kind not in ("RECOVERY", "FALLBACK") or envelope.stage not in ("RECOVERY", "ESCALATION"):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CANONICAL_ENVELOPE")
            if not scope.indices:
                if envelope.parent_diagnostic_reference != scope.original.last_diagnostic_reference or envelope.chain_root_reference != scope.original.chain_root_reference:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        if previous is not None:
            if previous.disposition == "TERMINAL" or previous.stage == "TERMINAL":
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            if envelope.parent_diagnostic_reference != scope.references[-1] or self._alias(envelope.chain_root_reference) != previous.chain_root_reference or self._alias(envelope.subject_reference) != previous.subject_reference:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
            severity = ("INFO", "WARNING", "ERROR", "CRITICAL")
            if severity.index(envelope.severity) < severity.index(previous.severity):
                raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")
        elif scope.producer == "STATE_MODEL" and (envelope.parent_diagnostic_reference is not None or envelope.chain_root_reference != emission.diagnostic_reference):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT", "CHAIN")

    def _append(self, scope, record):
        with self._lock:
            self._charging_scope = scope
            emission = None
            try:
                if scope.finished or scope.failed:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                if scope.producer == "STATE_MODEL":
                    if type(record) is not sv.DiagnosticEmission:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    emission, phase, template, context = record, record.envelope.stage, "DIAGNOSIS_RECORDED" if not scope.indices else "CLASSIFICATION_RECORDED", _context()
                elif scope.producer == "NORMALIZATION":
                    if type(record) is not nv.NormalizationDiagnosticRecord:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    emission, phase = record.emission, record.phase
                    template = "NORMALIZATION_COMPUTED" if phase == "COMPUTATION" else "POST_VALIDATION_RECORDED"
                    context = self._diagnosis_context(record.state_validity_diagnostic)
                    if record.step is not None:
                        context = self._context_update(context, before_state=record.step.input_state.signature,
                            codeword=record.step.codeword.signature, after_state=record.step.actual_state.signature,
                            actual_state=record.step.actual_state.signature, step_index=record.step.step_index)
                else:
                    from . import recovery_values as rv
                    if type(record) is not rv.RecoveryRecord:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                    emission = sv.DiagnosticEmission(record.diagnostic_reference, record.envelope)
                    phase, template = "RECOVERY", "RECOVERY_ACTION_RECORDED"
                    context = self._recovery_context(scope, record.payload)
                    if scope.denial and (record.record_kind != "OPERATION_DECISION" or record.payload.action != "HANDOFF" or record.payload.directive is None or record.payload.directive.requested_action != "REMAIN_SAFE_HALT"):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
                scope.attempted_reference, scope.attempted_hash = emission.diagnostic_reference, _fingerprint(record)
                if len(_encode(record)) > 33554432:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RAW_PACKET_LIMIT")
                self._validate_chain(scope, emission, phase)
                observed = self._observe_clock()
                if self._next_sequence >= 1 << 64:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_SEQUENCE_LIMIT")
                sequence = self._next_sequence
                scope.attempted_index = sequence if sequence <= 1023 else None
                if len(self._events) >= 1024 or len(scope.indices) >= (1 if scope.denial else 768 if scope.producer == "RECOVERY_ENGINE" else 2):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
                safe = self._safe_envelope(emission.envelope, template)
                redactions = (dv.RedactionEntry("SUMMARY", "UNTRUSTED_FREEFORM", 1),
                              dv.RedactionEntry("NOTES", "UNTRUSTED_FREEFORM", len(emission.envelope.notes)))
                relation = None if scope.relation is None else dv.CaptureRelation(
                    self._alias(scope.relation.parent_operation_reference), self._alias(scope.relation.parent_action_reference),
                    self._alias(scope.relation.originating_chain_root_reference))
                event = dv.DiagnosticEvent(self._alias(emission.diagnostic_reference), sequence, observed,
                    scope.producer, "DIAGNOSTIC", template, self.identity.session_reference,
                    self._alias(scope.reference), self._action_alias(record), relation,
                    self._alias(emission.diagnostic_reference), safe, "OBSERVED",
                    observed.monotonic_nanoseconds - scope.first_clock.monotonic_nanoseconds, None,
                    context, None, redactions)
                payload = _encode(event)
                if len(payload) > 32768:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_EVENT_TOO_LARGE")
                if self._used + len(payload) > 33554432:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_BYTE_LIMIT")
                self._commit("commit_event", sequence, payload)
                self._events.append(event)
                self._used += len(payload)
                self._consume_reservation(scope, len(payload), event=True)
                self._next_sequence += 1
                scope.references.append(emission.diagnostic_reference)
                scope.indices.append(sequence)
                scope.hashes.append(_fingerprint(record))
                # Safe envelope retains chain state; raw business record is not retained.
                scope.last_envelope = safe
                self._acks[emission.diagnostic_reference] = dv.PrivateAcknowledgmentWitness(
                    emission.diagnostic_reference, self.identity.build_id, self.identity.session_reference,
                    sequence, _fingerprint(emission))
                for row in redactions:
                    key = (row.field_category, row.reason)
                    self._redactions[key] = self._redactions.get(key, 0) + row.count
                    self._increment("REDACTED_FIELDS", row.count)
                self._increment("ACCEPTED")
                self._increment("RETAINED")
                self._persist_health()
                if self._storage != "PROTECTED_VERIFIED":
                    # Event bytes are retained, but health completion did not ACK.
                    scope.references.pop()
                    scope.indices.pop()
                    scope.hashes.pop()
                    self._acks.pop(emission.diagnostic_reference, None)
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE")
                if scope.producer == "RECOVERY_ENGINE" and hasattr(record.payload, "step_index"):
                    scope.step_indices[record.payload.step_index] = sequence
                    scope.step_policies[record.payload.step_index] = record.payload.policy_id
                return sv.CaptureReceipt(emission.diagnostic_reference, "CONFIRMED")
            except dv.DiagnosticsContractError as error:
                scope.failed = error.code
                self._mark_failure(error.code)
                self._meta_failure(scope, error.code)
                self._persist_health()
                reference = emission.diagnostic_reference if emission else scope.reference
                return sv.CaptureReceipt(reference, "NOT_CONFIRMED" if error.code.startswith("STORAGE") else "REJECTED")
            except Exception:
                scope.failed = "DIAGNOSTICS_COLLECTOR_FAILURE"
                self._mark_failure(scope.failed)
                self._meta_failure(scope, scope.failed)
                return sv.CaptureReceipt(emission.diagnostic_reference if emission else scope.reference, "NOT_CONFIRMED")
            finally:
                self._charging_scope = None

    def _context_update(self, old, **values):
        row = {name: getattr(old, name) for name in dv.CONTEXT_FIELDS}
        row.update(values)
        return _context(**row)

    def _diagnosis_context(self, diagnostic):
        state = diagnostic.input_state
        return _context(input_state=state.signature if type(state) is sv.AshState else None,
            admissibility_status=diagnostic.admissibility_status,
            transformation_compatibility=diagnostic.transformation_compatibility,
            normalization_status=diagnostic.normalization_status,
            recoverability_relevance=diagnostic.recoverability_relevance,
            is_valid=diagnostic.is_valid, orbit_info=_orbit(diagnostic.orbit_info))

    def _action_alias(self, record):
        payload = getattr(record, "payload", None)
        reference = getattr(payload, "action_reference", None)
        return None if reference is None else self._alias(reference)

    def _commit(self, method, sequence, payload, *args):
        try:
            receipt = getattr(self.store, method)(sequence, *args, payload)
        except Exception:
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE") from None
        if type(receipt) is not dv.StorageReceipt or receipt.sequence != sequence or receipt.status != "COMMITTED":
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE")
        return receipt

    def _supporting(self, kind, alias, node):
        encoded = _encode(node)
        existing = self._support[kind].get(alias)
        if self._charging_scope is not None:
            self._charging_scope.support_keys.add((kind, alias))
        if existing is not None:
            if _encode(existing) != encoded:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
            return alias
        maxima = {"PROFILE": 16, "ASSESSMENT": 512, "RECOVERY_DIAGNOSTIC": 64,
            "CANONICAL_SOURCE": 16, "NORMALIZATION_PROOF": 8, "CORRECTION_PROOF": 8,
            "REGISTRY_PROOF": 8, "CONDITION": 512, "PREDICATE_OBSERVATION": 512, "RECOVERY_SAFETY": 8,
            "TARGET_VALIDITY": 264}
        if len(self._support[kind]) >= maxima[kind]:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        if len(encoded) > 32768 or self._support_bytes + len(encoded) > 2097152:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
        sequence = self._next_sequence
        self._commit("commit_supporting", sequence, encoded, kind, alias)
        self._support[kind][alias] = node
        self._support_bytes += len(encoded)
        self._used += len(encoded)
        if self._charging_scope is not None:
            self._consume_reservation(self._charging_scope, len(encoded))
        return alias

    def _consume_reservation(self, scope, byte_count, *, event=False):
        if scope.relation is not None:
            scope = self._scopes[scope.relation.parent_operation_reference]
        if byte_count > scope.remaining_bytes or event and scope.remaining_events <= 0:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RESERVATION_REFUSED")
        scope.remaining_bytes -= byte_count
        if event:
            scope.remaining_events -= 1

    def _source_support(self, binding):
        if self.identity.source_revision is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE")
        try:
            fields = sv.canonical_diagnostic_pin_fields(binding)
        except sv.StateContractError:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE") from None
        snapshot = next((pin for pin in self._canonical_source_snapshots if pin.sha256 == fields[0][1]), None)
        if snapshot is None:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_UNAVAILABLE", "ORIGINAL_SOURCE")
        alias = self._alias("canonical-source:" + fields[0][1])
        pins = tuple(dv.SourcePin(name, snapshot.revision, digest) for name, digest in fields)
        return self._supporting("CANONICAL_SOURCE", alias, dv.SafeSourceEvidence(alias, pins, None))

    def _profile_support(self, binding):
        profile = binding.profile if binding.availability == "AVAILABLE" else binding.evidence
        alias = self._alias("profile-evidence:" + _fingerprint(binding))
        node = dv.SafeProfileEvidence(alias, self._alias(binding.profile_id), binding.availability,
            self._alias(binding.source_binding.source_reference), self._alias(binding.source_binding.source_sha256), self._alias(binding.source_binding.evidence_reference),
            None if binding.availability == "UNAVAILABLE" else tuple(sorted(state.signature for state in profile.recognized_valid_states)),
            "NOT_PROVIDED" if binding.availability == "UNAVAILABLE" else None)
        return self._supporting("PROFILE", alias, node)

    def _safe_validity(self, diagnostic, input_reference):
        state = diagnostic.input_state
        safe_input = dv.SafeInputState("ASH_STATE" if type(state) is sv.AshState else "REJECTED",
            state.signature if type(state) is sv.AshState else None, self._alias(input_reference),
            None if type(state) is sv.AshState else state.input_evidence.failure_code)
        return dv.SafeStateValidity(safe_input, diagnostic.admissibility_status,
            diagnostic.transformation_compatibility, diagnostic.normalization_status,
            diagnostic.recoverability_relevance, diagnostic.is_valid, _orbit(diagnostic.orbit_info),
            diagnostic.rule_ids, (dv.message_text("UNTRUSTED_PROSE_OMITTED"),))

    def _safe_predicate(self, fact):
        binding = fact.binding
        return dv.SafePredicate(fact.evaluation, getattr(fact, "value", None),
            self._alias(binding.assessment_reference), self._alias(binding.diagnosis_reference),
            self._alias(binding.subject_reference), self._alias(binding.profile_id),
            self._alias(binding.profile_source_sha256), self._alias(binding.evidence_reference))

    def _assessment_support(self, packet):
        source = self._source_support(packet.source_binding)
        profile = self._profile_support(packet.profile_binding)
        binding = packet.assessment_binding
        alias = self._alias("assessment-evidence:" + _fingerprint(packet))
        context = getattr(packet, "system_context", None)
        evidence = getattr(packet, "classification_evidence", None)
        node = dv.SafeAssessmentEvidence(alias, self._alias(binding.assessment_reference),
            self._alias(packet.input_evidence.original_input_reference),
            None if packet.parsed_state is None else packet.parsed_state.signature, source, profile,
            self._safe_validity(packet.state_validity_diagnostic, packet.input_evidence.original_input_reference),
            False if context is None else context.is_in_safe_halt,
            False if context is None else context.is_in_containment,
            None if evidence is None else self._safe_predicate(evidence.correction_path_is_known),
            None if evidence is None else self._safe_predicate(evidence.fallback_is_available),
            getattr(packet, "system_state_class", None), getattr(packet, "recovery_category", None),
            tuple(name.upper() for name in getattr(packet, "consulted_predicates", ())),
            tuple(self._safe_envelope(emission.envelope, "DIAGNOSIS_RECORDED" if index == 0 else "CLASSIFICATION_RECORDED")
                  for index, emission in enumerate(packet.emitted_diagnostics)))
        new = alias not in self._support["ASSESSMENT"]
        result = self._supporting("ASSESSMENT", alias, node)
        if new:
            if packet.input_evidence.preview is not None:
                self._redact("INPUT_PREVIEW", 1)
            scalars = sum(observation.scalar_kind != "INTEGER_BIT" for observation in packet.input_evidence.coordinate_observations)
            if scalars:
                self._redact("NON_BIT_SCALAR", scalars)
            self._redact("NOTES", len(packet.state_validity_diagnostic.notes))
        return result

    def _redact(self, category, count):
        key = (category, "UNTRUSTED_FREEFORM")
        self._redactions[key] = self._redactions.get(key, 0) + count
        self._increment("REDACTED_FIELDS", count)

    def _normalization_support(self, packet):
        self._assessment_support(packet.original_diagnosis)
        plan, validation = packet.plan, packet.plan_validation
        source = self._source_support(validation.canonical_binding)
        profile = self._profile_support(validation.profile_binding)
        submitted_profile = self._profile_support(packet.original_diagnosis.profile_binding)
        alias = self._alias("normalization-proof:" + plan.evidence_reference)
        node = dv.SafeNormalizationProof(alias, "READY" if validation.validation_status == "VALIDATED" else "REJECTED",
            self._alias(packet.original_diagnosis.assessment_binding.assessment_reference),
            self._alias(packet.original_diagnosis.emitted_diagnostics[0].diagnostic_reference),
            self._alias(plan.plan_reference), self._alias(plan.policy_binding.policy_id),
            self._alias(packet.original_diagnosis.source_binding.aggregate_sha256), source,
            submitted_profile, profile,
            self._proof_status(validation.origin_validation_status), self._proof_status(validation.validation_status),
            plan.decision, tuple(item.signature for item in plan.eligible_targets),
            None if validation.recomputed_eligible_targets is None else tuple(item.signature for item in validation.recomputed_eligible_targets),
            None if plan.selected_target is None else plan.selected_target.signature,
            None if validation.recomputed_target is None else validation.recomputed_target.signature,
            tuple(item.signature for item in plan.codeword_chain),
            None if validation.recomputed_codeword_chain is None else tuple(item.signature for item in validation.recomputed_codeword_chain),
            self._validation_field(validation.field_name), None if validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
        return self._supporting("NORMALIZATION_PROOF", alias, node)

    @staticmethod
    def _proof_status(status):
        return "VERIFIED" if status in ("VALIDATED", "VERIFIED") else status

    @staticmethod
    def _validation_field(field):
        if field is None:
            return None
        mapping = {"original_diagnosis.source_binding": "ORIGINAL_SOURCE",
            "original_diagnosis.profile_binding": "ORIGINAL_PROFILE", "original_diagnosis": "ORIGINAL_DIAGNOSIS",
            "eligible_targets": "TARGET_SET", "selected_target": "SELECTED_TARGET", "codeword_chain": "CODEWORD_CHAIN"}
        return mapping.get(field, "UNKNOWN_REGISTERED_FIELD")

    def complete_assessment(self, result):
        if not any(type(result) is kind for kind in (sv.StateDiagnosis, sv.StateAssessment, sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure)):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        reference = result.assessment_binding.assessment_reference
        scope = self._scopes.get(reference)
        return self._complete(scope, result, "STATE_MODEL", reference=reference)

    def complete_normalization(self, result):
        if not any(type(result) is kind for kind in (nv.NormalizationResult, nv.NormalizationFailure, nv.NormalizationCaptureFailure)):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        reference = result.operation_binding.operation_reference
        return self._complete(self._scopes.get(reference), result, "NORMALIZATION", reference=reference)

    def _complete(self, scope, result, producer, *, reference=None):
        with self._lock:
            self._charging_scope = scope
            reference = reference or scope.reference
            indices, attempted, failure = (), None, None
            outcome = "COMPLETED"
            try:
                self._observe_clock()
                if scope is None or scope.producer != producer:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISSING")
                indices = tuple(scope.indices)
                attempted = scope.attempted_index if scope.failed else None
                if scope.finished:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_REPLAY_REFUSED")
                if len(_encode(result)) > 33554432:
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_RAW_PACKET_LIMIT")
                records = result.emitted_diagnostics
                if tuple(_fingerprint(record) for record in records) != tuple(scope.hashes):
                    raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if producer == "STATE_MODEL":
                    if type(result) is sv.StateDiagnosis and len(records) != 1 or type(result) is sv.StateAssessment and len(records) != 2:
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    if not records:
                        if type(result) is not sv.DiagnosticCaptureFailure:
                            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    else:
                        self._assessment_support(result)
                    partial = any(type(result) is kind for kind in (sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure))
                elif producer == "NORMALIZATION":
                    if type(result) is nv.NormalizationResult and tuple(record.phase for record in records) != ("COMPUTATION", "POST_VALIDATION"):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
                    self._normalization_support(result)
                    partial = type(result) is nv.NormalizationCaptureFailure
                    outcome = "NORMALIZED" if type(result) is nv.NormalizationResult else "FAILED"
                else:
                    partial, outcome = self._recovery_completion(scope, result)
                if getattr(result, "attempted_diagnostic", None) is not None:
                    if scope.attempted_hash != _fingerprint(result.attempted_diagnostic):
                        raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
                if partial or scope.failed:
                    raise dv.DiagnosticsContractError(scope.failed or "DIAGNOSTICS_REQUIRED_STEP_MISSING")
                if producer == "RECOVERY_ENGINE" and getattr(result, "failure_detail", None) is not None:
                    self._incident_failure(scope, "SOURCE_REPORTED_FAILURE")
                scope.finished = True
                self._producer_completed.add(producer)
                self._persist_health()
                if self._storage != "PROTECTED_VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                self._charging_scope = None
                return dv.DiagnosticsCompletionReceipt(reference, "COMPLETE", outcome, indices,
                    "COMPLETE_DECLARED_REFERENCE_SCOPE", None, None, self.health())
            except dv.DiagnosticsContractError as error:
                failure = error.code
            except Exception:
                failure = "DIAGNOSTICS_COLLECTOR_FAILURE"
            if scope is not None:
                scope.finished, scope.failed = True, scope.failed or failure
                self._meta_failure(scope, failure)
                try:
                    self._incident_failure(scope, "STORAGE_FAILURE" if failure.startswith("STORAGE") else "MISSING_REQUIRED_STEP")
                except dv.DiagnosticsContractError as error:
                    failure = error.code
            self._mark_failure(failure)
            self._persist_health()
            self._charging_scope = None
            return dv.DiagnosticsCompletionReceipt(reference, "INCOMPLETE", "INCOMPLETE", indices,
                "PARTIAL", failure, attempted, self.health())

    def _mark_failure(self, code):
        self._failure = code
        self._increment("REJECTED")
        self._first_unavailable = self._next_sequence if self._first_unavailable is None else self._first_unavailable
        self._last_unavailable = self._next_sequence
        if code.startswith("STORAGE"):
            self._storage = "UNCERTAIN"
            self._counts["LOST"] = None

    def _meta_failure(self, scope, code):
        cause = "COMPLETION_MISSING" if code in ("DIAGNOSTICS_COMPLETION_MISSING", "DIAGNOSTICS_REQUIRED_STEP_MISSING") else "SCHEMA_NONCONFORMANCE"
        self._fallback_cause = cause
        if len(self._meta) >= 16:
            self._increment("META_OVERFLOW")
            self._fallback_health()
            return
        try:
            reference = self._alias("meta:" + str(len(self._meta)))
            envelope = dv.SafeDiagnosticEnvelope("STATE_VALIDITY", "ERROR", "DETECTION", "BLOCKED",
                self._alias(scope.reference), None, reference, ("ASH-STATE-GENERAL-001",),
                dv.message_text("DIAGNOSTIC_NONCONFORMANCE"), (dv.message_text("UNTRUSTED_PROSE_OMITTED"),))
            meta = dv.MetaDiagnosticRecord(reference, len(self._meta), self._last_clock, envelope,
                dv.MetaCause(cause, self._alias(scope.reference), None if scope.attempted_reference is None else self._alias(scope.attempted_reference), None, None))
            self._commit("commit_meta", meta.local_sequence, _encode(meta))
            self._meta.append(meta)
        except Exception:
            self._meta_storage = "UNCERTAIN"
            self._increment("META_OVERFLOW")
            self._fallback_health()

    def _fallback_health(self):
        record = dv.FallbackHealthRecord(self._fallback_cause or "SCHEMA_NONCONFORMANCE", self._storage,
            self._events[-1].local_sequence if self._events else None,
            self._first_unavailable, self._last_unavailable, self._counts["META_OVERFLOW"], self._last_clock)
        try:
            self._commit("commit_fallback_health", None, _encode(record))
        except dv.DiagnosticsContractError:
            self._meta_storage = "UNCERTAIN"

    def _incident_failure(self, scope, safe_failure):
        operation_alias = self._alias(scope.reference)
        if any(operation_alias in incident.affected_operation_references for incident in self._incidents):
            return
        if any(operation_alias in incident.affected_operation_references for incident in self._unconfirmed_incidents):
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
        timeline = tuple(event.event_id for event in self._events
            if event.operation_reference == operation_alias or event.relation is not None and event.relation.parent_operation_reference == operation_alias)
        if not timeline and scope.original is not None:
            origin = self._scopes.get(scope.original.assessment_reference)
            if origin is not None:
                timeline = tuple(event.event_id for event in self._events if event.local_sequence in origin.indices)
        if not timeline:
            timeline = tuple(meta.meta_reference for meta in self._meta
                if meta.cause.related_operation_reference == operation_alias)
        if not timeline:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
        if len(self._incidents) + len(self._unconfirmed_incidents) >= 32:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_INCIDENT_LIMIT")
        alias = self._alias("incident:" + scope.reference)
        trigger = timeline[-1]
        semantic = safe_failure == "SOURCE_REPORTED_FAILURE"
        error = dv.SafeError("RECOVERY" if semantic else "STORAGE" if safe_failure == "STORAGE_FAILURE" else "DIAGNOSTICS",
            safe_failure, (), "STORE" if safe_failure == "STORAGE_FAILURE" else "EXPECTED_STEP", None,
            "CAPTURE_UNCONFIRMED", ("EXCEPTION_TEXT", "STACK", "ABSOLUTE_PATH"))
        incident = dv.DiagnosticIncident(alias, trigger,
            dv.ExpectedBehavior("VALID_RETURN" if semantic else "ACKNOWLEDGED_STEPS", self._alias("docs/architecture/m3_reference_diagnostics_contract.md"), "COMPLETED" if semantic else "CONFIRMED"),
            "FAILED" if semantic else "NOT_CONFIRMED", (operation_alias,), timeline, (), error, (), None,
            (dv.EvidenceFact("CAPTURE_CONFIRMED" if semantic else "CAPTURE_NOT_CONFIRMED", (trigger,)),), (), ("NO_SUPPORTED_CAUSE",), True)
        payload = _encode(incident)
        if len(payload) > 32768 or self._incident_bytes + len(payload) > 1048576:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_INCIDENT_LIMIT")
        charged = scope if scope.relation is None else self._scopes[scope.relation.parent_operation_reference]
        if charged.remaining_incidents <= 0:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_INCIDENT_LIMIT")
        charged.remaining_incidents -= 1
        try:
            sequence = self._events[-1].local_sequence if self._events else self._next_sequence
            self._commit("commit_incident", sequence, payload, alias)
            self._incidents.append(incident)
            self._incident_bytes += len(payload)
            self._used += len(payload)
            if self._charging_scope is not None:
                self._consume_reservation(self._charging_scope, len(payload))
        except dv.DiagnosticsContractError:
            self._unconfirmed_incidents.append(incident)
            self._incident_bytes += len(payload)
            self._used += len(payload)
            if self._charging_scope is not None:
                self._consume_reservation(self._charging_scope, len(payload))
            self._storage = "UNCERTAIN"
            self._failure = "STORAGE_COMMIT_UNCONFIRMED"
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED") from None

    def _coverage(self):
        available = {"DIAGNOSTICS", "PROTECTED_STORAGE", "ENVIRONMENT_OS", "RUNTIME_VERSION", "ARCHITECTURE", "HOST_CLASS", "UTC_CLOCK", "MONOTONIC_CLOCK"} | self._producer_completed
        if self._export_completed:
            available.add("PAIRED_EXPORT")
        environmental_missing = {row.source: row.reason for row in self.identity.environment.unavailable_fields}
        if self._storage != "PROTECTED_VERIFIED":
            environmental_missing["PROTECTED_STORAGE"] = "STORAGE_UNAVAILABLE"
        if self._unconfirmed_incidents or self._failure == "DIAGNOSTICS_INCIDENT_LIMIT":
            environmental_missing["DIAGNOSTICS"] = "LOSS_UNCONFIRMED"
        if self._last_clock.observed_utc is None:
            environmental_missing["UTC_CLOCK"] = self._last_clock.utc_reason
        if self._failure in ("DIAGNOSTICS_CLOCK_UNAVAILABLE", "DIAGNOSTICS_CLOCK_REGRESSION", "DIAGNOSTICS_DURATION_LIMIT"):
            environmental_missing["MONOTONIC_CLOCK"] = {"DIAGNOSTICS_CLOCK_REGRESSION": "CLOCK_REGRESSION",
                "DIAGNOSTICS_DURATION_LIMIT": "DURATION_LIMIT"}.get(self._failure, "CLOCK_UNAVAILABLE")
        available.difference_update(environmental_missing)
        excluded = {"REALM_ENCODER", "TRANSITION_REGISTRY", "TOPOLOGY_GENERATOR", "AXIOM_EVALUATOR", "GENERATION_PLANNER", "ARTIFACT_EMITTER", "NATIVE_RUNTIME", "NATIVE_RELEASE", "PHYSICAL_CRASH"}
        return tuple(dv.MissingCoverage(source, "EXCLUDED" if source in excluded else "AVAILABLE" if source in available else "UNAVAILABLE",
            "EXCLUDED_REFERENCE_SCOPE" if source in excluded else None if source in available else environmental_missing.get(source, "NOT_MEASURED")) for source in dv.enum_values("CoverageSource"))

    def health(self):
        with self._lock:
            coverage = self._coverage()
            active = sum(not scope.finished for scope in self._scopes.values())
            status = "PARTIAL" if active or self._failure else "COMPLETE_DECLARED_REFERENCE_SCOPE"
            counters = tuple(dv.DiagnosticCounterState(field,
                "UNAVAILABLE" if self._counts[field] is None else "SATURATED" if field in self._saturated else "EXACT",
                "STORAGE_UNCONFIRMED" if self._counts[field] is None else "COUNTER_LIMIT" if field in self._saturated else None) for field in dv.enum_values("CounterField"))
            return dv.DiagnosticsHealth(status, self._counts["ACCEPTED"], self._counts["REJECTED"], self._counts["RETAINED"],
                self._counts["EXPIRED"], self._counts["LOST"], self._counts["REDACTED_FIELDS"], self._counts["REDACTED_REFERENCES"],
                self._events[-1].local_sequence if self._events else None, self._first_unavailable, self._last_unavailable,
                active, self._used, self._storage, self._failure, tuple(row for row in coverage if row.status != "AVAILABLE"),
                tuple(self._retention), any(row.coalesced for row in self._retention), self._counts["META_OVERFLOW"], counters, len(self._meta), self._meta_storage, self._fallback_cause)

    def _persist_health(self):
        try:
            self._commit("commit_health", self._events[-1].local_sequence if self._events else None, _encode(self.health()))
        except dv.DiagnosticsContractError:
            self._storage = "UNCERTAIN"
            self._failure = "STORAGE_COMMIT_UNCONFIRMED"
            self._fallback_health()

    def _evidence(self):
        support = self._support
        return dv.SupportingEvidence((), (), (), tuple(support["PROFILE"].values()),
            tuple(support["ASSESSMENT"].values()), tuple(support["RECOVERY_DIAGNOSTIC"].values()),
            tuple(support["CANONICAL_SOURCE"].values()), tuple(support["NORMALIZATION_PROOF"].values()),
            tuple(support["CORRECTION_PROOF"].values()), tuple(support["REGISTRY_PROOF"].values()),
            tuple(support["CONDITION"].values()), tuple(support["PREDICATE_OBSERVATION"].values()),
            tuple(support["RECOVERY_SAFETY"].values()), tuple(support["TARGET_VALIDITY"].values()))

    def snapshot(self, *, bundle_reference):
        sv.InputEvidence.validate_reference(bundle_reference)
        with self._lock:
            try:
                observed = self._observe_clock()
            except dv.DiagnosticsContractError as error:
                self._mark_failure(error.code)
                observed = dv.ClockObservation(None, None, "CLOCK_UNAVAILABLE", "CLOCK_UNAVAILABLE")
            for scope in self._scopes.values():
                if not scope.finished:
                    self._failure = "DIAGNOSTICS_COMPLETION_MISSING"
            self._persist_health()
            bundle_alias = self._alias(bundle_reference)
            aliases = self._counts["REDACTED_REFERENCES"]
            entries = tuple(dv.RedactionEntry(category, reason, count) for (category, reason), count in self._redactions.items())
            if aliases:
                entries += (dv.RedactionEntry("CALLER_REFERENCE", "OPAQUE_REFERENCE_ALIAS", aliases),)
            limitations = tuple(dv.Limitation(code, source) for code, source in (
                ("REFERENCE_IMPLEMENTATION_ONLY", "DIAGNOSTICS"), ("TRUSTED_CAPTURE_CONTRACT", "DIAGNOSTICS"),
                ("NO_REMOTE_ACK_AUTHENTICATION", "DIAGNOSTICS"), ("NATIVE_COMPOSITION_DEFERRED", "NATIVE_RUNTIME"),
                ("NATIVE_RELEASE_DEFERRED", "NATIVE_RELEASE"), ("NO_PHYSICAL_CRASH_PROOF", "PHYSICAL_CRASH"),
                ("NO_POWER_LOSS_DURABILITY_PROOF", "PROTECTED_STORAGE"), ("NO_ENCRYPTION_CLAIM", "PROTECTED_STORAGE"),
                ("NO_SECOND_USER_ACCESS_TEST", "PROTECTED_STORAGE"), ("UNTRUSTED_PROSE_OMITTED", "DIAGNOSTICS")))
            snapshot = dv.DiagnosticSnapshot(bundle_alias, observed.observed_utc, observed.utc_reason,
                self.identity, self.profile, dv.CaptureWindow(self._events[0].local_sequence if self._events else None,
                    self._events[-1].local_sequence if self._events else None, self._start_clock, observed),
                self._coverage(), tuple(self._events), tuple(self._meta), tuple(self._incidents), self._evidence(), self.health(),
                dv.RetentionAccount(self._limits, tuple(self._retention),
                    tuple(self._alias(scope.reference) for scope in self._scopes.values() if not scope.finished),
                    tuple(dict.fromkeys(reference for incident in self._incidents if incident.unresolved
                                        for reference in incident.affected_operation_references)), any(row.coalesced for row in self._retention)),
                dv.RedactionAccount(self._counts["REDACTED_FIELDS"], self._counts["REDACTED_REFERENCES"], entries), limitations)
            self._issued_snapshots[snapshot.bundle_id] = _fingerprint(snapshot)
            return snapshot

    def export_pair(self, snapshot):
        if type(snapshot) is not dv.DiagnosticSnapshot:
            raise dv.DiagnosticsContractError("EXPORT_SNAPSHOT_INVALID")
        with self._lock:
            try:
                if type(snapshot.bundle_id) is not str or self._issued_snapshots.get(snapshot.bundle_id) != _fingerprint(snapshot):
                    raise dv.DiagnosticsContractError("EXPORT_SNAPSHOT_INVALID")
            except Exception:
                raise dv.DiagnosticsContractError("EXPORT_SNAPSHOT_INVALID") from None
            if self._export_slot is not None:
                parts = tuple(dv.PartReceipt(kind, name, "NOT_WRITTEN", None, None, None)
                    for kind, name in (("JSON", "diagnostics.json"), ("MARKDOWN", "diagnostics.md"), ("MANIFEST", "manifest.json")))
                return dv.ExportFailure(snapshot.bundle_id, "EXPORT_SLOT_OCCUPIED", "PUBLICATION", parts, snapshot)
            raw = _encode(snapshot)
            markdown = self._markdown(snapshot, raw)
            if len(raw) > 33554432 or len(markdown) > 50331648:
                raise dv.DiagnosticsContractError("EXPORT_BYTE_LIMIT")
            if json.loads(markdown.split(b"```json\n", 1)[1].rsplit(b"\n```", 1)[0]) != json.loads(raw):
                raise dv.DiagnosticsContractError("EXPORT_PARITY_FAILED")
            manifest = json.dumps({"bundle_id": snapshot.bundle_id, "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                "json_sha256": hashlib.sha256(raw).hexdigest(), "markdown_sha256": hashlib.sha256(markdown).hexdigest(),
                "last_included_sequence": snapshot.capture_window.last_sequence,
                "parity": "EXACT_EMBEDDED_SNAPSHOT"}, sort_keys=True, separators=(",", ":")).encode("ascii")
            try:
                receipt = self.store.write_pair(snapshot.bundle_id, raw, markdown, manifest,
                    last_included_sequence=snapshot.capture_window.last_sequence)
            except Exception:
                receipt = None
            if type(receipt) is dv.StorePairReceipt and receipt.bundle_id == snapshot.bundle_id and receipt.last_included_sequence == snapshot.capture_window.last_sequence:
                expected = (raw, markdown, manifest)
                if all(part.bytes == len(data) and part.sha256 == hashlib.sha256(data).hexdigest() for part, data in zip(receipt.parts, expected)):
                    self._export_slot = snapshot.bundle_id
                    self._export_completed = True
                    self._export_boundary = snapshot.capture_window.last_sequence
                    return dv.ExportReceipt(snapshot.bundle_id, receipt.parts, receipt.last_included_sequence, snapshot)
            if type(receipt) is dv.StorePairFailure and receipt.bundle_id == snapshot.bundle_id:
                self._export_slot = snapshot.bundle_id
                self._export_boundary = snapshot.capture_window.last_sequence
                return dv.ExportFailure(snapshot.bundle_id, receipt.failure_code, receipt.failed_part, receipt.parts, snapshot)
            parts = tuple(dv.PartReceipt(kind, name, "WRITTEN_UNCONFIRMED", None, None, "EXPORT_PUBLICATION_FAILED")
                for kind, name in (("JSON", "diagnostics.json"), ("MARKDOWN", "diagnostics.md"), ("MANIFEST", "manifest.json")))
            self._export_slot = snapshot.bundle_id
            self._export_boundary = snapshot.capture_window.last_sequence
            return dv.ExportFailure(snapshot.bundle_id, "EXPORT_PUBLICATION_FAILED", "PUBLICATION", parts, snapshot)

    @staticmethod
    def _markdown(snapshot, raw):
        identity = snapshot.identity
        lines = ["# Reference Diagnostics", "", f"Bundle `{snapshot.bundle_id}`; product `{identity.product_version}`; implementation `{identity.implementation_id}`.",
            f"Source `{identity.source_revision}`; provenance `{identity.source_provenance.status}`; coverage `{snapshot.health.coverage_status}`.",
            "", "## Coverage", ""]
        for row in snapshot.coverage:
            lines.append(f"- {row.source}: {row.status}" + (f" ({row.reason})" if row.reason else ""))
        lines.extend(("", "## Observed timeline", ""))
        for event in snapshot.events:
            envelope = event.envelope
            classification = "local observation" if envelope is None else f"{envelope.diagnostic_kind}/{envelope.stage}/{envelope.severity}/{envelope.disposition}"
            lines.extend((f"### {event.local_sequence}: {event.event_id}", "",
                f"Producer `{event.source}`; {classification}; outcome `{event.outcome}`.",
                dv.message_text(event.message_template), "",
                "Context: `" + json.dumps(event.context.to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
            if event.error is not None:
                lines.extend(("Observed error: `" + json.dumps(event.error.to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
        lines.extend(("## Incidents", ""))
        for incident in snapshot.incidents:
            lines.extend((f"### {incident.incident_id}", "",
                f"Expected `{incident.expected.invariant}/{incident.expected.expected_outcome}`; observed `{incident.observed_outcome}`; unresolved `{incident.unresolved}`.",
                "Timeline: " + ", ".join(incident.timeline_event_references),
                "Unknown causes: " + ", ".join(incident.unknowns),
                "Retained evidence: `" + json.dumps(incident.to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
        lines.extend(("## Supporting evidence", ""))
        supporting = snapshot.supporting_evidence.to_record()
        for name, rows in supporting.items():
            if type(rows) is list and rows:
                lines.extend((f"### {name} ({len(rows)})", ""))
                lines.extend("- `" + json.dumps(row, sort_keys=True, separators=(",", ":")) + "`" for row in rows)
                lines.append("")
        lines.extend(("## Retention, redaction and health", ""))
        for name in ("retention", "redaction", "health"):
            lines.extend((name + ": `" + json.dumps(getattr(snapshot, name).to_record(), sort_keys=True, separators=(",", ":")) + "`", ""))
        lines.extend(("## Limitations", ""))
        lines.extend(f"- {row.code}: {row.source}" for row in snapshot.limitations)
        lines.extend(("", "## Exact paired snapshot", "", "The following artifact is identical to the paired JSON file.", ""))
        detailed = ("\n".join(lines) + "\n").encode("ascii")
        if len(detailed) > 16777216:
            raise dv.DiagnosticsContractError("EXPORT_BYTE_LIMIT")
        return detailed + b"```json\n" + raw + b"\n```\n"

    def purge_completed(self, *, through_sequence):
        if type(through_sequence) is not int or not 0 <= through_sequence < 1 << 64:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_VALUE_INVALID")
        with self._lock:
            groups = []
            for scope in self._scopes.values():
                if scope.relation is not None or scope.purged or not scope.finished or scope.failed:
                    continue
                group = (scope,) + tuple(self._scopes[reference] for reference in scope.child_operations)
                if any(not member.finished or member.failed for member in group):
                    continue
                indices = tuple(index for member in group for index in member.indices)
                if indices and max(indices) <= through_sequence:
                    aliases = {self._alias(member.reference) for member in group}
                    event_aliases = {event.event_id for event in self._events if event.local_sequence in indices}
                    if any(incident.unresolved and (aliases.intersection(incident.affected_operation_references) or
                            event_aliases.intersection(incident.timeline_event_references))
                            for incident in (*self._incidents, *self._unconfirmed_incidents)):
                        continue
                    groups.append(group)
            retained_before = {event.local_sequence for event in self._events}
            indices = tuple(sorted(index for group in groups for member in group for index in member.indices if index in retained_before))
            if not indices or not callable(getattr(self.store, "purge_capture", None)):
                return dv.RetentionReceipt("REJECTED", (), self.health())
            request = dv.CapturePurgeRequest(indices, ())
            def invalidate_origins(affected):
                self._acks = {reference: witness for reference, witness in self._acks.items()
                    if witness.confirmed_sequence not in affected}
                for scope in self._scopes.values():
                    if affected.intersection(scope.indices):
                        scope.failed = scope.failed or "STORAGE_COMMIT_UNCONFIRMED"
                self._issued_snapshots.clear()
            try:
                observed = self.store.purge_capture(request)
                expected = tuple(dv.CaptureObjectKey("EVENT", index, None, None) for index in indices)
                if type(observed) is not dv.StoreCapturePurgeReceipt or tuple(row.key for row in observed.observations) != expected:
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
            except Exception:
                # A thrown or malformed result cannot establish whether the
                # requested files still exist. Retain their graph roots, but
                # never use the old acknowledgements for a new attachment.
                invalidate_origins(set(indices))
                self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
                self._persist_health()
                return dv.RetentionReceipt("REJECTED", (), self.health())
            removed = {row.key.sequence for row in observed.observations if row.status == "REMOVED"}
            uncertain = {row.key.sequence for row in observed.observations if row.status == "UNCONFIRMED"}
            if uncertain:
                invalidate_origins(uncertain)
            for event in tuple(self._events):
                if event.local_sequence in removed:
                    self._events.remove(event)
                    self._used -= len(_encode(event))
                    self._increment("EXPIRED")
                    self._counts["RETAINED"] -= 1
            self._acks = {reference: witness for reference, witness in self._acks.items() if witness.confirmed_sequence not in removed}
            for group in groups:
                if all(index in removed or index not in retained_before for member in group for index in member.indices):
                    for member in group:
                        member.purged = True
            # Unknown event deletions remain roots. The second request is computed
            # from actual retained evidence, never from intended first-phase removal.
            reachable = set()
            for scope in self._scopes.values():
                if not scope.purged:
                    reachable.update(scope.support_keys)
            def references(value):
                if type(value) is str:
                    yield value
                elif type(value) in (tuple, list):
                    for child in value:
                        yield from references(child)
                elif type(value) is dict:
                    for child in value.values():
                        yield from references(child)
            indexed = {alias: (kind, alias) for kind, nodes in self._support.items() for alias in nodes}
            for event in self._events:
                reachable.update(indexed[alias] for alias in references(event.to_record()) if alias in indexed)
            changed = True
            while changed:
                changed = False
                for kind, alias in tuple(reachable):
                    for reference in references(self._support[kind][alias].to_record()):
                        key = indexed.get(reference)
                        if key is not None and key not in reachable:
                            reachable.add(key)
                            changed = True
            unreachable = tuple(dv.CaptureObjectKey("SUPPORTING", None, kind, alias)
                for kind, alias in sorted(set(indexed.values()) - reachable))
            partial = observed.status != "COMPLETED"
            if unreachable:
                try:
                    support_receipt = self.store.purge_capture(dv.CapturePurgeRequest((), unreachable))
                    if type(support_receipt) is not dv.StoreCapturePurgeReceipt or tuple(row.key for row in support_receipt.observations) != unreachable:
                        raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                    for row in support_receipt.observations:
                        if row.status == "REMOVED":
                            node = self._support[row.key.supporting_kind].pop(row.key.evidence_reference)
                            size = len(_encode(node))
                            self._support_bytes -= size
                            self._used -= size
                    partial = partial or support_receipt.status != "COMPLETED"
                except Exception:
                    partial = True
            boundaries = []
            for index in sorted(removed):
                if boundaries and index == boundaries[-1][1] + 1:
                    boundaries[-1][1] = index
                else:
                    boundaries.append([index, index])
            account = tuple(dv.RetentionBoundary(first, last, last - first + 1, "EXPLICIT_PURGE", False) for first, last in boundaries)
            self._retention.extend(account)
            if len(self._retention) > 16:
                first, last = self._retention[0].first_sequence, self._retention[-1].last_sequence
                self._retention[:] = [dv.RetentionBoundary(first, last, sum(row.record_count for row in self._retention), "EXPLICIT_PURGE", True)]
            if partial:
                self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
            elif self._export_slot is not None and self._export_boundary is not None and self._export_boundary <= through_sequence:
                try:
                    exported = self.store.purge_bundle(self._export_slot)
                    if type(exported) is not dv.StorePurgeReceipt or exported.bundle_id != self._export_slot or exported.status != "COMPLETED":
                        raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED")
                    self._export_slot, self._export_boundary, self._export_completed = None, None, False
                except Exception:
                    partial = True
                    self._mark_failure("STORAGE_COMMIT_UNCONFIRMED")
            self._issued_snapshots.clear()
            self._persist_health()
            return dv.RetentionReceipt("REJECTED" if partial else "COMPLETED", account[:16], self.health())

    def _evidence_source(self, value):
        return dv.SafeEvidenceSourceBinding(self._alias(value.source_reference),
            self._alias(value.source_sha256), self._alias(value.evidence_reference))

    def _condition_support(self, condition):
        alias = self._alias(condition.condition_id)
        return self._supporting("CONDITION", alias,
            dv.SafeConditionEvidence(alias, self._evidence_source(condition.source_binding)))

    def _predicate_support(self, observed):
        condition_alias = self._condition_support(observed.condition)
        alias = self._alias("predicate-observation:" + _fingerprint(observed))
        node = dv.SafePredicateObservationEvidence(alias, observed.status, condition_alias,
            self._evidence_source(observed.condition.source_binding), self._evidence_source(observed.source_binding),
            self._alias(observed.operation_reference), self._alias(observed.origin_assessment_reference),
            self._alias(observed.registry_id), self._alias(observed.registry_source_sha256),
            self._alias(observed.policy_id), observed.phase, observed.candidate_state_reference.signature)
        return self._supporting("PREDICATE_OBSERVATION", alias, node)

    def _directive(self, directive):
        from . import recovery_values as rv
        trigger = directive.trigger
        if type(trigger) is rv.ExternalEscalationRequired:
            trigger = dv.SafeExternalEscalationRequired(trigger.authority_status)
        elif type(trigger) is rv.ExistingModeBoundary:
            trigger = dv.SafeExistingModeBoundary(trigger.observed_system_state_class,
                self._alias(trigger.observed_assessment_reference))
        return dv.SafeRecoveryDirective(directive.requested_action, trigger,
            self._alias(directive.origin_assessment_reference), self._alias(directive.causing_decision_reference),
            tuple(self._alias(reference) for reference in directive.evidence_references), directive.request_origin,
            None if directive.policy_binding is None else dv.SafeRecoverySafetyPolicy())

    @staticmethod
    def _step_kind(action):
        mapping = {"NORMALIZE_PLAN": "NORMALIZE", "NORMALIZE_XOR": "NORMALIZE", "CORRECTION_RESOLVE": "CORRECT",
            "CORRECTION_XOR": "CORRECT", "CANDIDATE_APPLICABILITY": "APPLICABILITY", "FALLBACK_SELECT": "SELECT_FALLBACK",
            "CANDIDATE_VALIDATION": "ADDITIONAL_VALIDATION", "POST_ASSESSMENT": "VALIDATE_RECOVERY", "HANDOFF": "HANDOFF",
            "NORMALIZE": "NORMALIZE", "CORRECT": "CORRECT", "FALLBACK": "SELECT_FALLBACK", "NO_ACTION": "SUMMARY",
            "CANDIDATE_DECISION": "CANDIDATE_DECISION", "SUMMARY": "SUMMARY"}
        return mapping.get(action, "SUMMARY")

    def _recovery_diagnostic_support(self, scope, decision):
        diagnostic = decision.diagnostic
        alias = self._alias(decision.action_reference)
        steps = []
        indices = tuple(scope.step_indices[index] for index in decision.step_indices if index in scope.step_indices)
        if len(indices) > 32:
            groups = {}
            for index in decision.step_indices:
                if index in scope.step_indices:
                    groups.setdefault(scope.step_policies.get(index), []).append(scope.step_indices[index])
            grouped = tuple(tuple(rows) for rows in groups.values())
        else:
            grouped = tuple((index,) for index in indices)
        for index, step in enumerate(diagnostic.steps):
            step_indices = grouped[index] if index < len(grouped) else ()
            if len(step_indices) > 32:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_SUPPORTING_LIMIT")
            steps.append(dv.SafeRecoveryStep(alias, self._step_kind(step.action),
                "COMPLETED" if step.status == "COMPLETED" else "BLOCKED" if step.status == "BLOCKED" else "FAILED",
                None, step_indices, "RECOVERY_ACTION_RECORDED"))
        node = dv.SafeRecoveryDiagnostic(diagnostic.recovery_category, diagnostic.original_state_class,
            self._alias(scope.original.last_diagnostic_reference), tuple(steps), diagnostic.outcome,
            None if diagnostic.corrected_state is None else diagnostic.corrected_state.signature,
            None if diagnostic.fallback_policy_id is None else self._alias(diagnostic.fallback_policy_id),
            dv.message_text("RECOVERY_ACTION_RECORDED"), diagnostic.rule_ids)
        return self._supporting("RECOVERY_DIAGNOSTIC", alias, node)

    def _recovery_context(self, scope, payload):
        from . import recovery_values as rv
        if type(payload) is rv.RecoveryStepEvidence:
            values = dict(step_index=payload.step_index,
                before_state=None if payload.before_state is None else payload.before_state.signature,
                codeword=None if payload.codeword is None else payload.codeword.signature,
                after_state=None if payload.after_state is None else payload.after_state.signature,
                actual_state=None if payload.after_state is None else payload.after_state.signature,
                policy_reference=None if payload.policy_id is None else self._alias(payload.policy_id),
                post_assessment_reference=None if payload.post_assessment_reference is None else self._alias(payload.post_assessment_reference))
            if payload.predicate_observation is not None:
                observed = payload.predicate_observation
                values.update(predicate_name=observed.phase,
                    predicate_value=True if observed.status == "TRUE" else False if observed.status == "FALSE" else None,
                    source_evidence_reference=self._predicate_support(observed))
            return _context(**values)
        if type(payload) is not rv.RecoveryActionDecision:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        return _context(recovery_diagnostic_reference=self._recovery_diagnostic_support(scope, payload),
            system_state_class=payload.diagnostic.original_state_class,
            recovery_category=payload.diagnostic.recovery_category,
            actual_state=None if payload.diagnostic.corrected_state is None else payload.diagnostic.corrected_state.signature,
            policy_reference=None if payload.diagnostic.fallback_policy_id is None else self._alias(payload.diagnostic.fallback_policy_id))

    def _registry_support(self, result):
        snapshot, validation = result.registry_snapshot, result.registry_validation
        if snapshot is None:
            return None
        binding = snapshot.source_binding
        alias = self._alias("registry-proof:" + result.operation_context.operation_reference)
        current_source = self._source_support(validation.current_source_binding)
        current_profile = self._profile_support(validation.current_profile_binding)
        submitted_profile = self._profile_support(result.origin_assessment.profile_binding)
        entries = []
        certifications = {item.policy_id: item for item in getattr(snapshot, "candidate_certifications", ())}
        validations = {item.policy_id: item for item in validation.candidate_validations}
        for index, entry in enumerate(getattr(snapshot, "entries", ())):
            certification = certifications[entry.policy_id]
            self._assessment_support(certification.source_assessment)
            for condition in (*entry.applicability_conditions, *entry.validation_requirements):
                self._condition_support(condition)
            item = validations.get(entry.policy_id)
            entries.append(dv.SafeRegistryEntry(self._alias(entry.policy_id), index, entry.ordering_rank,
                tuple(self._alias(condition.condition_id) for condition in entry.applicability_conditions),
                tuple(self._alias(condition.condition_id) for condition in entry.validation_requirements),
                entry.candidate_state_reference.signature, entry.escalation_on_failure,
                self._alias(certification.source_assessment.assessment_binding.assessment_reference),
                "NOT_EVALUATED" if item is None else item.assessment_validation.status,
                None if item is None or item.target_diagnostic is None else self._target_support(item.target_diagnostic,
                    validation.current_source_binding, validation.current_profile_binding)))
        node = dv.SafeRegistryProof(alias, self._alias(binding.registry_id), snapshot.availability,
            self._alias(binding.source_binding.source_reference), current_source, submitted_profile, current_profile,
            validation.status, tuple(entries), tuple(self._alias(attempt.policy_id) for attempt in result.policy_attempts),
            None if validation.failed_policy_id is None else self._alias(validation.failed_policy_id),
            self._validation_field(validation.field_name), None if validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
        return self._supporting("REGISTRY_PROOF", alias, node)

    def _preparation_support(self, result):
        preparation = result.normalization_preparation
        if preparation is not None:
            diagnosis = preparation.original_diagnosis
            self._assessment_support(diagnosis)
            validation, plan = preparation.plan_validation, preparation.plan
            current = result.origin_validation
            alias = self._alias("normalization-proof:" + result.operation_context.operation_reference)
            node = dv.SafeNormalizationProof(alias, preparation.status,
                self._alias(result.origin_assessment.assessment_binding.assessment_reference),
                self._alias(diagnosis.emitted_diagnostics[0].diagnostic_reference),
                None if plan is None else self._alias(plan.plan_reference), self._alias(preparation.policy_binding.policy_id),
                self._alias(diagnosis.source_binding.aggregate_sha256), self._source_support(current.current_source_binding),
                self._profile_support(diagnosis.profile_binding), self._profile_support(current.current_profile_binding),
                "NOT_EVALUATED" if validation is None else self._proof_status(validation.origin_validation_status),
                "NOT_EVALUATED" if validation is None else self._proof_status(validation.validation_status),
                None if plan is None else plan.decision, None if plan is None else tuple(state.signature for state in plan.eligible_targets),
                None if validation is None or validation.recomputed_eligible_targets is None else tuple(state.signature for state in validation.recomputed_eligible_targets),
                None if plan is None or plan.selected_target is None else plan.selected_target.signature,
                None if validation is None or validation.recomputed_target is None else validation.recomputed_target.signature,
                None if plan is None else tuple(state.signature for state in plan.codeword_chain),
                None if validation is None or validation.recomputed_codeword_chain is None else tuple(state.signature for state in validation.recomputed_codeword_chain),
                None if validation is None else self._validation_field(validation.field_name),
                None if validation is None or validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
            self._supporting("NORMALIZATION_PROOF", alias, node)
        observation = result.correction_observation
        if observation is not None and observation.validation is not None:
            correction, validation = observation.submitted, observation.validation
            alias = self._alias("correction-proof:" + correction.correction_reference)
            node = dv.SafeCorrectionProof(alias, self._alias(correction.correction_reference),
                self._alias(correction.original_assessment_reference), self._alias(correction.source_binding.source_reference),
                self._source_support(validation.current_source_binding), self._profile_support(result.origin_assessment.profile_binding),
                self._profile_support(validation.current_profile_binding), validation.origin_validation.status, validation.status,
                tuple(state.signature for state in correction.chain), correction.expected_target.signature,
                None if validation.computed_target is None else validation.computed_target.signature,
                None if validation.target_diagnostic is None else self._target_support(validation.target_diagnostic,
                    validation.current_source_binding, validation.current_profile_binding),
                self._validation_field(validation.field_name), None if validation.failure_code is None else "SOURCE_REPORTED_FAILURE")
            self._supporting("CORRECTION_PROOF", alias, node)

    def _target_support(self, diagnostic, source_binding, profile_binding):
        if type(diagnostic) is not sv.StateValidityDiagnostic:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        alias = self._alias("target-validity:" + _fingerprint(diagnostic) + ":" + _fingerprint(profile_binding))
        state = diagnostic.input_state
        reference = "ash_state_" + state.signature if type(state) is sv.AshState else state.input_evidence.original_input_reference
        node = dv.SafeTargetValidityEvidence(alias, self._source_support(source_binding),
            self._profile_support(profile_binding), self._safe_validity(diagnostic, reference))
        new = alias not in self._support["TARGET_VALIDITY"]
        result = self._supporting("TARGET_VALIDITY", alias, node)
        if new:
            self._redact("NOTES", len(diagnostic.notes))
        return result

    def _safety_support(self, result):
        context = result.operation_context
        alias = self._alias("safety-evidence:" + context.operation_reference)
        directive = result.directive
        consulted_propagation = result.origin_assessment.system_state_class in ("UNSTABLE", "CORRECTABLE", "DEGRADED")
        consulted_authority = result.origin_assessment.system_state_class == "FAILED"
        node = dv.SafeRecoverySafetyEvidence(alias, self._alias(context.operation_reference),
            self._alias(context.origin_assessment_reference), context.propagation_evidence.status,
            self._evidence_source(context.propagation_evidence.source_binding), consulted_propagation,
            context.external_authority_evidence.status, self._evidence_source(context.external_authority_evidence.source_binding),
            consulted_authority, None if directive is None else self._directive(directive))
        new = alias not in self._support["RECOVERY_SAFETY"]
        result = self._supporting("RECOVERY_SAFETY", alias, node)
        if new:
            self._redact("CAUSAL_TEXT", 2 + (directive is not None))
        return result

    def _recovery_completion(self, scope, result):
        from . import recovery_values as rv
        kinds = (rv.RecoveryNoAction, rv.RecoveredValue, rv.RecoveredFallbackValue, rv.RecoveryHandoff, rv.RecoveryFailure)
        if not any(type(result) is kind for kind in kinds) or result.operation_context.operation_reference != scope.reference:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        if result.origin_assessment.assessment_binding.assessment_reference != scope.original.assessment_reference:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_ORIGIN_MISMATCH")
        self._attached(result.origin_assessment.emitted_diagnostics)
        if scope.denial and (not any(type(result) is kind for kind in (rv.RecoveryHandoff, rv.RecoveryFailure)) or result.steps or result.post_assessments or result.registry_snapshot is not None):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_RECORD_NONCONFORMANT")
        if tuple(post.assessment.assessment_binding.assessment_reference for post in result.post_assessments) != tuple(scope.child_operations):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
        for post in result.post_assessments:
            child = self._scopes.get(post.assessment.assessment_binding.assessment_reference)
            if child is None or not child.finished or child.failed:
                raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
            self._assessment_support(post.assessment)
        recorded_steps = tuple(record.payload for record in result.emitted_diagnostics if record.record_kind == "ACTION_VALUE_COMPUTED")
        if any(step not in result.steps for step in recorded_steps):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        if type(result) is not rv.RecoveryFailure and recorded_steps != result.steps:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_REQUIRED_STEP_MISSING")
        self._preparation_support(result)
        self._registry_support(result)
        self._safety_support(result)
        attempted = None if result.failure_detail is None else result.failure_detail.attempted_diagnostic
        if attempted is not None and scope.attempted_hash != _fingerprint(attempted):
            raise dv.DiagnosticsContractError("DIAGNOSTICS_COMPLETION_MISMATCH")
        mapping = {"NO_ACTION": "NOT_APPLICABLE", "RECOVERED_VALUE": "RECOVERED",
                   "RECOVERED_FALLBACK_VALUE": "RECOVERED_VIA_FALLBACK", "HANDOFF_REQUIRED": "COMPLETED", "FAILURE": "FAILED"}
        return bool(scope.failed), mapping[result.outcome]


class ReferenceDevelopmentDiagnostics(_ReferenceDiagnostics):
    _profile_id = "REFERENCE_DEVELOPMENT"


class ReferenceReleaseDiagnostics(_ReferenceDiagnostics):
    _profile_id = "REFERENCE_RELEASE"
