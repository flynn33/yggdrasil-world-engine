"""Closed immutable topology/axiom reference values [YWE-REQ-0047]."""
from __future__ import annotations

from dataclasses import dataclass, fields
import json
import math
import re
from typing import ClassVar

from . import state_values as state

RAW_BUSINESS_LIMIT = 1_048_576
TEN_BYTE_LIMIT = 8192
INT63_MAX = 9_223_372_036_854_775_807
POLICY_FIELDS = ("YWE-TOPOLOGY-AXIOM-REFERENCE-001", "1.0.0",
                 "ab645a078e9aaee04e3eb01ac1ced01de986340d8f0242057eb3e4567196c7ae")
ERROR_CODES = ("GENERATION_INPUT_INVALID", "GENERATION_POLICY_MISMATCH",
               "GENERATION_SOURCE_UNSUPPORTED", "GENERATION_COMPOSITION_INVALID",
               "GENERATION_RAW_BYTE_LIMIT")
TOPOLOGY_FAILURES = ("ORIGIN_REJECTED", "ORIGIN_UNPARSED", "PROFILE_UNAVAILABLE",
                    "STATE_NOT_NORMALIZED", "DEPTH_RANGE_EXCEEDED", "REFERENCE_COLLISION",
                    "SOURCE_UNSUPPORTED", "VALIDATION_UNAVAILABLE")
AXIOM_FAILURES = ("ORIGIN_REJECTED", "ORIGIN_UNPARSED", "PROFILE_UNAVAILABLE",
                 "SUBJECT_STATE_MISMATCH", "SUBJECT_ORIGIN_MISMATCH", "SUBJECT_UNIT_MISMATCH",
                 "REFERENCE_COLLISION", "SOURCE_UNSUPPORTED", "VALIDATION_UNAVAILABLE")
FAILURE_FIELDS = ("request.origin_diagnosis", "request.depth", "request.subject.state",
                  "request.subject.provenance.origin_diagnosis_reference",
                  "request.subject.raw_measure.unit", "request.subject.compressed_measure.unit",
                  "request.subject.erasure_cost.unit", "request.subject.compressed_measure.ticks_per_unit",
                  "request.reference_set", "model.canonical_binding", "model.validation")
PENDING_REQUIREMENTS = {"SOURCE_UNSUPPORTED": "CURRENT_SOURCE",
                        "VALIDATION_UNAVAILABLE": "VALIDATION_RESULT",
                        "ORIGIN_REJECTED": "VERIFIED_ORIGIN",
                        "REFERENCE_COLLISION": "DISTINCT_REFERENCES"}
TOPOLOGY_RULES = ("ASH-TOPOLOGY-STRUCTURE-001", "ASH-TOPOLOGY-EXPANSION-001",
                  "ASH-TOPOLOGY-ORDER-001", "ASH-TOPOLOGY-LINEAGE-001")
TOPOLOGY_ADMISSION = ("ASH-TOPOLOGY-ADMISSION-001",)
AXIOM_RULES = (("ASH-AXIOM-RELATION-001",), ("ASH-AXIOM-COMPRESSION-001",),
               ("ASH-AXIOM-SCALE-001",), ("ASH-AXIOM-ERASURE-001",),
               ("ASH-AXIOM-SELFREFERENCE-001", "ASH-AXIOM-CONJUNCTION-001"))
AXIOM_ADMISSION = ("ASH-AXIOM-SUBJECT-001",)
AXIOM_FIELDS = ("a1_relational_existence", "a2_structural_compressibility",
                "a3_multi_scale_persistence", "a4_energetic_cost_of_erasure",
                "a5_self_reference_for_consciousness")
OPERATORS = ("GT_ZERO", "LT", "GT_ONE", "GT_ZERO", "BOTH_TRUE")
OPERANDS = (("relation_count",), ("compressed_measure", "raw_measure"),
            ("scale_count",), ("erasure_cost",),
            ("self_reference_capable", "self_model_available"))
SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")


class GenerationContractError(ValueError):
    def __init__(self, code, field_name):
        if type(code) is not str or code not in ERROR_CODES:
            raise ValueError("invalid generation error code")
        if type(field_name) is not str or re.fullmatch(r"[A-Za-z0-9_.\[\]]{1,128}", field_name) is None:
            raise ValueError("invalid generation error field")
        self.code, self.field_name = code, field_name
        super().__init__(f"{code}: {field_name}")


def _fail(field="value", code="GENERATION_INPUT_INVALID"):
    raise GenerationContractError(code, field)


def _exact(value, kinds, field):
    allowed = kinds if type(kinds) is tuple else (kinds,)
    if not _type_is_one_of(type(value), allowed):
        _fail(field)


def _type_is_one_of(kind, allowed):
    return any(kind is candidate for candidate in allowed)


def _int(value, low, high, field):
    if type(value) is not int or not low <= value <= high:
        _fail(field)


def _text(value, field, *, maximum=512, pattern=None):
    if (type(value) is not str or not 1 <= len(value) <= maximum or
            any(0xD800 <= ord(char) <= 0xDFFF for char in value)):
        _fail(field)
    if pattern is not None and re.fullmatch(pattern, value, re.ASCII) is None:
        _fail(field)


def _ref(value, field, maximum=256):
    _text(value, field, maximum=maximum, pattern=r"[A-Za-z0-9][A-Za-z0-9._:/-]*")
    if value in ("NONE", "SELF"):
        _fail(field)


def _choice(value, choices, field):
    if type(value) is not str or value not in choices:
        _fail(field)


def _equal(actual, expected, field):
    if actual != expected:
        _fail(field)


def _tuple(value, field, low, high, normalize):
    if type(value) is not tuple and not (normalize and type(value) is list):
        _fail(field)
    if not low <= len(value) <= high:
        _fail(field)
    return tuple(value)


def bool_text(value):
    return "true" if value else "false"


def topology_notes(depth, frontier, visited):
    return ("Input is VALID and ALREADY_VALID under the current complete profile.",
            "Ternary child order is continuation, positive, negative.",
            f"Final frontier has {frontier} nodes at depth {depth}.",
            f"Constructed {visited} nodes across all levels.",
            "Lineage is encoded by the explicit seed and base-three path.")


def topology_refusal_notes(code):
    return (f"Reason: {code}.", "No topology nodes were constructed.",
            "Complete normalized origin and supported depth 0..6 are required.")


def axiom_passes(subject):
    return (subject.relation_count > 0,
            subject.compressed_measure.ticks < subject.raw_measure.ticks,
            subject.scale_count > 1, subject.erasure_cost.ticks > 0,
            subject.self_reference_capable and subject.self_model_available)


def axiom_explanation(axiom_id, subject):
    index = int(axiom_id[1]) - 1
    passed = bool_text(axiom_passes(subject)[index])
    if index == 0:
        return f"A1: relation_count={subject.relation_count}; requires relation_count>0; component_pass={passed}."
    if index == 1:
        return (f"A2: compressed_measure={subject.compressed_measure.ticks} STRUCTURE_TICK, "
                f"raw_measure={subject.raw_measure.ticks} STRUCTURE_TICK, "
                f"ticks_per_unit={subject.raw_measure.ticks_per_unit}; requires compressed<raw; component_pass={passed}.")
    if index == 2:
        return f"A3: scale_count={subject.scale_count}; requires scale_count>1; component_pass={passed}."
    if index == 3:
        return (f"A4: erasure_cost={subject.erasure_cost.ticks} ERASURE_TICK, "
                f"ticks_per_unit={subject.erasure_cost.ticks_per_unit}; requires cost>0; component_pass={passed}.")
    return (f"A5: self_reference_capable={bool_text(subject.self_reference_capable)}, "
            f"self_model_available={bool_text(subject.self_model_available)}; requires both true; "
            f"component_pass={passed}; overall_pass={bool_text(all(axiom_passes(subject)))}.")


def refusal_explanation(code, field):
    return f"Axiom input refusal: {code}; field={field}."


def pending_reason(kind, code, missing):
    return f"Canonical {kind} production unavailable: {code}; missing={','.join(missing)}."


class _WireValue:
    __slots__ = ()

    def __post_init__(self):
        _walk(self, set(), normalize=True)

    def to_record(self):
        return json.loads(canonical_bytes(self))

    def canonical_bytes(self):
        return canonical_bytes(self)


class _Packet(_WireValue):
    __slots__ = ("_issuer", "_cookie", "_self_identity")
    schema_version: ClassVar[str] = "1.0.0"


def _local(value, normalize):
    name = type(value).__name__
    for field in fields(type(value)):
        try:
            item = object.__getattribute__(value, field.name)
        except AttributeError:
            _fail(field.name)
        domain = FIELD_DOMAINS[name][field.name]
        _field(item, domain, field.name, normalize)
        if domain.startswith("tuple") and type(item) is list:
            object.__setattr__(value, field.name, tuple(item))


def _field(value, domain, field, normalize):
    if domain.endswith("|null"):
        if value is None:
            return
        domain = domain[:-5]
    if domain.startswith("literal "):
        _exact(value, str, field)
        _equal(value, domain[8:], field)
    elif domain == "exact bool":
        _exact(value, bool, field)
    elif domain == "Signed64":
        _int(value, -INT63_MAX-1, INT63_MAX, field)
    elif domain == "NonNegativeInt63":
        _int(value, 0, INT63_MAX, field)
    elif domain.startswith("integer"):
        low, high = domain[7:].split("..")
        _int(value, int(low), int(high), field)
    elif domain.startswith("Reference"):
        _ref(value, field, int(domain[9:]))
    elif domain.startswith("Identifier"):
        _text(value, field, maximum=int(domain[10:]), pattern=r"[A-Za-z0-9][A-Za-z0-9._-]*")
    elif domain == "Text512":
        _text(value, field)
    elif domain == "FailureField":
        _choice(value, FAILURE_FIELDS, field)
    elif domain == "TopologyFailureCode":
        _choice(value, TOPOLOGY_FAILURES, field)
    elif domain == "AxiomFailureCode":
        _choice(value, AXIOM_FAILURES, field)
    elif domain.startswith("enum "):
        _choice(value, domain[5:].split("|"), field)
    elif domain.startswith("ASCII "):
        _text(value, field, maximum=32 if "32" in domain else 7, pattern=domain[6:])
    elif domain.startswith("ASCII1.."):
        _text(value, field, maximum=int(domain[8:]), pattern=r"[\x21-\x7e]+")
    elif domain.startswith("tuple"):
        match = re.match(r"tuple(?: exactly(\d+)|(\d+)\.\.(\d+))", domain)
        if match is None:
            _fail(field)
        low = high = int(match[1]) if match[1] else None
        if low is None:
            low, high = int(match[2]), int(match[3])
        sequence = _tuple(value, field, low, high, normalize)
        if domain.startswith("tuple exactly7 of exact tuple"):
            for pair in sequence:
                _exact(pair, tuple, field)
                if len(pair) != 2:
                    _fail(field)
                _text(pair[0], field, maximum=256, pattern=r"[\x21-\x7e]+")
                _text(pair[1], field, maximum=64, pattern=r"[0-9a-f]{64}")
        elif "Text512" in domain:
            for item in sequence:
                _text(item, field)
        elif "AxiomOperandName" in domain:
            for item in sequence:
                _choice(item, tuple(x for row in OPERANDS for x in row), field)
        elif "unique of" in domain:
            for item in sequence:
                _choice(item, tuple(PENDING_REQUIREMENTS.values()), field)
            if len(set(sequence)) != len(sequence):
                _fail(field)
        elif "rule IDs" in domain:
            for item in sequence:
                _choice(item, TOPOLOGY_RULES + TOPOLOGY_ADMISSION + AXIOM_ADMISSION + tuple(x for row in AXIOM_RULES for x in row), field)
            if len(set(sequence)) != len(sequence):
                _fail(field)
        else:
            child = "TopologyNode" if "TopologyNode" in domain else "GenerationDiagnosticRecord"
            for item in sequence:
                _exact(item, globals()[child], field)
    else:
        allowed = []
        for child in domain.replace(" after source adoption", "").split("|"):
            cls = globals().get(child, getattr(state, child, None))
            if cls is None:
                _fail(field)
            allowed.append(cls)
        _exact(value, tuple(allowed), field)


_SHARED_NAMES = ("AshState", "CanonicalAshBinding", "ProfileSourceBinding", "ValidityProfile",
                 "UnavailableValidityProfileEvidence", "AvailableProfileBinding", "UnavailableProfileBinding",
                 "AssessmentBinding", "CoordinateObservation", "InputEvidence", "RejectedCandidateEvidence",
                 "OrbitInfo", "StateValidityDiagnostic", "DiagnosticEnvelope", "DiagnosticEmission",
                 "StateDiagnosis", "DiagnosisValidation")


def _walk(value, active, *, normalize=False):
    kind = type(value)
    if value is None or kind is bool:
        return
    if kind is str:
        # Source-owned malformed input previews preserve their exact observation.
        # TA-authored text is independently scalar-checked by its own field guard.
        if len(value) > 65536:
            _fail("value")
        return
    if kind is int:
        if int.bit_length(value) > 64:
            _fail("value")
        return
    if kind is float:
        # CoordinateObservation owns any retained finite numeric observation.
        if not math.isfinite(value):
            _fail("value")
        return
    identity = id(value)
    if identity in active or len(active) >= 64:
        _fail("value")
    own = _type_is_one_of(kind, WIRE_TYPES)
    shared = any(kind is getattr(state, name, None) for name in _SHARED_NAMES)
    if kind is not tuple and kind is not frozenset and not own and not shared:
        _fail("value")
    active.add(identity)
    try:
        if kind is tuple or kind is frozenset:
            if len(value) > (512 if kind is frozenset else 1024):
                _fail("value")
            for child in value:
                if kind is frozenset:
                    _exact(child, state.AshState, "recognized_valid_states")
                _walk(child, active)
        else:
            if own:
                _local(value, normalize)
            for field in fields(kind):
                _walk(object.__getattribute__(value, field.name), active)
            if own:
                _coherent(value)
            else:
                kind.__post_init__(value)
    except (AttributeError, TypeError, RecursionError):
        _fail("value")
    finally:
        active.remove(identity)


def revalidate_value(value):
    _walk(value, set())
    return value


def _record(value):
    kind = type(value)
    if value is None or _type_is_one_of(kind, (str, int, bool, float)):
        return value
    if kind is tuple:
        return [_record(child) for child in value]
    if kind is frozenset:
        return [_record(child) for child in sorted(value, key=lambda entry: entry.bits)]
    if _type_is_one_of(kind, WIRE_TYPES):
        record = {field.name: _record(object.__getattribute__(value, field.name)) for field in fields(kind)}
        if _type_is_one_of(kind, PACKET_TYPES):
            record.update(schema_version="1.0.0", packet_kind=PACKET_KINDS[kind])
        return record
    if any(kind is getattr(state, name, None) for name in _SHARED_NAMES):
        return kind.to_record(value)
    _fail("value")


def _tokens(value, limit):
    revalidate_value(value)
    total = 0
    for token in json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                                  allow_nan=False).iterencode(_record(value)):
        chunk = token.encode("ascii")
        total += len(chunk)
        if total > limit:
            _fail("raw_business_packet", "GENERATION_RAW_BYTE_LIMIT")
        yield chunk


def canonical_bytes(value):
    return b"".join(_tokens(value, RAW_BUSINESS_LIMIT))


def raw_business_size(value, limit=RAW_BUSINESS_LIMIT):
    _int(limit, 1, RAW_BUSINESS_LIMIT, "limit")
    try:
        return sum(len(chunk) for chunk in _tokens(value, limit))
    except GenerationContractError as error:
        if error.code == "GENERATION_RAW_BYTE_LIMIT":
            return limit + 1
        raise


def source_binding_for(binding):
    revalidate_value(binding)
    for row in SOURCE_BASELINES:
        if state.CanonicalAshBinding.to_record(binding) == row[1]:
            return TopologyAxiomSourceBinding(binding, row[2])
    _fail("model.canonical_binding", "GENERATION_SOURCE_UNSUPPORTED")


def _normalized(origin):
    diagnostic = origin.state_validity_diagnostic
    return diagnostic.admissibility_status == "VALID" and diagnostic.is_valid and diagnostic.normalization_status == "ALREADY_VALID"


def derived_references(request):
    if type(request) is TopologyRequest:
        return (request.request_reference + ":diagnostic:topology",)
    return tuple(request.request_reference + f":diagnostic:A{i}" for i in range(1, 6)) + (request.request_reference + ":diagnostic:axiom-input",)


def admission_failure(request, source, validation):
    if source.canonical_binding.aggregate_sha256 not in CURRENT_PRODUCER_AGGREGATES:
        return "SOURCE_UNSUPPORTED", "model.canonical_binding"
    if validation is None:
        return "VALIDATION_UNAVAILABLE", "model.validation"
    if validation.status != "VERIFIED":
        return "ORIGIN_REJECTED", "request.origin_diagnosis"
    origin = request.origin_diagnosis
    refs = derived_references(request)
    if origin.emitted_diagnostics[0].diagnostic_reference in refs or len(set(refs)) != len(refs):
        return "REFERENCE_COLLISION", "request.reference_set"
    if type(validation.current_profile_binding) is state.UnavailableProfileBinding:
        return "PROFILE_UNAVAILABLE", "request.origin_diagnosis"
    if origin.parsed_state is None:
        return "ORIGIN_UNPARSED", "request.origin_diagnosis"
    if type(request) is TopologyRequest:
        if not _normalized(origin):
            return "STATE_NOT_NORMALIZED", "request.origin_diagnosis"
        if not 0 <= request.depth <= 6:
            return "DEPTH_RANGE_EXCEEDED", "request.depth"
    else:
        subject = request.subject
        if subject.state != origin.parsed_state:
            return "SUBJECT_STATE_MISMATCH", "request.subject.state"
        if subject.provenance.origin_diagnosis_reference != origin.emitted_diagnostics[0].diagnostic_reference:
            return "SUBJECT_ORIGIN_MISMATCH", "request.subject.provenance.origin_diagnosis_reference"
        for field in ("raw_measure", "compressed_measure"):
            if getattr(subject, field).unit != "STRUCTURE_TICK":
                return "SUBJECT_UNIT_MISMATCH", f"request.subject.{field}.unit"
        if subject.compressed_measure.ticks_per_unit != subject.raw_measure.ticks_per_unit:
            return "SUBJECT_UNIT_MISMATCH", "request.subject.compressed_measure.ticks_per_unit"
        if subject.erasure_cost.unit != "ERASURE_TICK":
            return "SUBJECT_UNIT_MISMATCH", "request.subject.erasure_cost.unit"
    return None


def _coherent(value):
    name = type(value).__name__
    if name == "TopologyAxiomPolicyBinding":
        _equal(tuple(getattr(value, f.name) for f in fields(type(value))), POLICY_FIELDS, "policy_binding")
    elif name == "TopologyAxiomSourceBinding":
        row = next((row for row in SOURCE_BASELINES if state.CanonicalAshBinding.to_record(value.canonical_binding) == row[1]), None)
        if row is None:
            _fail("canonical_binding")
        _equal(value.contract_pins, row[2], "contract_pins")
    elif name == "TopologyNode":
        match = re.fullmatch(r"topology:([A-Za-z0-9_-]{1,32}):(r[012]{0,6})", value.node_id, re.ASCII)
        if match is None:
            _fail("node_id")
        seed, path = match.groups()
        depth = len(path) - 1
        _equal((value.path_token, value.depth, value.ordinal), (path, depth, int(path[1:], 3) if depth else 0), "path_token")
        _equal(value.parent_id, None if depth == 0 else f"topology:{seed}:{path[:-1]}", "parent_id")
        _equal(value.branch_kind, "root" if depth == 0 else ("continuation", "positive", "negative")[int(path[-1])], "branch_kind")
    elif name == "TopologyDiagnostic":
        if value.outcome == "COMPLETE":
            if value.input_state is None or value.topology_reference is None or value.failure_code is not None:
                _fail("outcome")
            _int(value.depth, 0, 6, "depth")
            _equal(value.topology_reference, value.request_reference + ":topology", "topology_reference")
            _equal(value.frontier_count, 3**value.depth, "frontier_count")
            _equal(value.visited_node_count, sum(3**k for k in range(value.depth + 1)), "visited_node_count")
            _equal(value.notes, topology_notes(value.depth, value.frontier_count, value.visited_node_count), "notes")
        else:
            if value.topology_reference is not None or value.frontier_count is not None or value.failure_code is None or value.visited_node_count != 0:
                _fail("outcome")
            _equal(value.notes, topology_refusal_notes(value.failure_code), "notes")
    elif name == "AxiomCheckDiagnostic":
        index = int(value.axiom_id[1]) - 1
        passes = axiom_passes(value.subject)
        _equal((value.passed, value.current_impact, value.operator, value.operand_names, value.overall_pass),
               (passes[index], "INFO" if passes[index] else "WARNING", OPERATORS[index], OPERANDS[index], all(passes) if index == 4 else None), "passed")
        _equal(value.explanation, axiom_explanation(value.axiom_id, value.subject), "explanation")
    elif name == "AxiomInputDiagnostic":
        _equal(value.explanation, refusal_explanation(value.failure_code, value.failed_field), "explanation")
    elif name == "AxiomDiagnostic":
        _equal(value.overall_pass, all(getattr(value, name) for name in AXIOM_FIELDS), "overall_pass")
    elif name == "PendingGenerationDiagnostic":
        _equal(value.missing_requirements, (PENDING_REQUIREMENTS[value.failure_code],), "missing_requirements")
        _equal(value.intended_rule_ids, TOPOLOGY_ADMISSION if value.intended_kind == "TOPOLOGY" else AXIOM_ADMISSION, "intended_rule_ids")
        _equal(value.reason, pending_reason(value.intended_kind, value.failure_code, value.missing_requirements), "reason")
    elif name == "GenerationDiagnosticRecord":
        _coherent_record(value)
    elif _type_is_one_of(type(value), PACKET_TYPES):
        _coherent_packet(value)


def _coherent_record(value):
    payload, envelope = value.payload, value.envelope
    if type(payload) is TopologyDiagnostic:
        complete = payload.outcome == "COMPLETE"
        _equal((envelope.diagnostic_kind, envelope.stage, envelope.disposition, envelope.rule_ids, envelope.summary, envelope.notes),
               ("TOPOLOGY", "PROCESSING", "RESOLVED" if complete else "BLOCKED", TOPOLOGY_RULES if complete else TOPOLOGY_ADMISSION,
                "Topology expansion completed." if complete else "Topology request rejected.", payload.notes), "envelope")
        _equal(value.diagnostic_reference, payload.request_reference + ":diagnostic:topology", "diagnostic_reference")
    elif type(payload) is AxiomInputDiagnostic:
        _equal((envelope.diagnostic_kind, envelope.stage, envelope.disposition, envelope.rule_ids, envelope.summary, envelope.notes),
               ("AXIOM", "PROCESSING", "BLOCKED", AXIOM_ADMISSION, "Axiom subject rejected.",
                (payload.explanation, "No axiom components were evaluated.", "Measurements and subject provenance are declared reference input.")), "envelope")
        _equal(value.diagnostic_reference, payload.request_reference + ":diagnostic:axiom-input", "diagnostic_reference")
    else:
        index = int(payload.axiom_id[1]) - 1
        word = "passed" if payload.passed else "failed"
        summary = (f"{payload.axiom_id} axiom check {word}." if index < 4 else
                   f"A5 component {word}; overall {'passed' if payload.overall_pass else 'failed'}.")
        disposition_pass = payload.overall_pass if index == 4 else payload.passed
        _equal((envelope.diagnostic_kind, envelope.stage, envelope.disposition, envelope.rule_ids, envelope.summary, envelope.notes),
               ("AXIOM", "PROCESSING", "RESOLVED" if disposition_pass else "BLOCKED", AXIOM_RULES[index], summary,
                (payload.explanation, "Measurements and subject provenance are declared reference input.")), "envelope")
    if len(json.dumps(state.DiagnosticEnvelope.to_record(envelope), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")) > TEN_BYTE_LIMIT:
        _fail("envelope", "GENERATION_RAW_BYTE_LIMIT")


def _coherent_packet(value):
    origin = value.request.origin_diagnosis
    validation = value.origin_validation
    if validation is not None:
        _equal(validation.submitted_diagnosis, origin, "origin_validation")
        _equal(validation.current_source_binding, value.source_binding.canonical_binding, "source_binding")
    failure = admission_failure(value.request, value.source_binding, validation)
    if _type_is_one_of(type(value), (TopologyFailure, AxiomEvaluationFailure)):
        _equal(failure, (value.failure_code, value.failed_field), "failure_code")
        if value.failure_code in ("SOURCE_UNSUPPORTED", "VALIDATION_UNAVAILABLE") and validation is not None:
            _fail("origin_validation")
        if value.failure_code in PENDING_REQUIREMENTS:
            _equal(value.produced_diagnostics, (), "produced_diagnostics")
            if value.pending_diagnostic is None:
                _fail("pending_diagnostic")
            kind = "TOPOLOGY" if type(value) is TopologyFailure else "AXIOM"
            ref = value.request.request_reference + (":diagnostic:topology" if kind == "TOPOLOGY" else ":diagnostic:axiom-input")
            _equal((value.pending_diagnostic.diagnostic_reference, value.pending_diagnostic.intended_kind, value.pending_diagnostic.failure_code), (ref, kind, value.failure_code), "pending_diagnostic")
            return
        if value.pending_diagnostic is not None or len(value.produced_diagnostics) != 1:
            _fail("produced_diagnostics")
        payload = value.produced_diagnostics[0].payload
        if type(value) is TopologyFailure:
            _exact(payload, TopologyDiagnostic, "payload")
            _equal((payload.request_reference, payload.input_state, payload.seed_token, payload.depth, payload.failure_code),
                   (value.request.request_reference, origin.parsed_state, value.request.seed_token, value.request.depth, value.failure_code), "payload")
        else:
            _exact(payload, AxiomInputDiagnostic, "payload")
            _equal((payload.request_reference, payload.subject, payload.failure_code, payload.failed_field),
                   (value.request.request_reference, value.request.subject, value.failure_code, value.failed_field), "payload")
    else:
        if failure is not None:
            _fail("origin_validation")
        if type(value) is TopologyResult:
            request = value.request
            _equal(value.topology_reference, request.request_reference + ":topology", "topology_reference")
            _equal(value.input_state, origin.parsed_state, "input_state")
            _equal(len(value.nodes), 3**request.depth, "nodes")
            _equal(value.visited_node_count, sum(3**k for k in range(request.depth + 1)), "visited_node_count")
            for ordinal, node in enumerate(value.nodes):
                _equal((node.depth, node.ordinal, node.node_id), (request.depth, ordinal, f"topology:{request.seed_token}:{node.path_token}"), "nodes")
            payload = value.produced_diagnostics[0].payload
            _exact(payload, TopologyDiagnostic, "payload")
            _equal((payload.outcome, payload.request_reference, payload.topology_reference, payload.input_state, payload.seed_token, payload.depth, payload.frontier_count, payload.visited_node_count),
                   ("COMPLETE", request.request_reference, value.topology_reference, value.input_state, request.seed_token, request.depth, len(value.nodes), value.visited_node_count), "payload")
        else:
            subject = value.request.subject
            _equal(value.evaluation_reference, value.request.request_reference + ":axioms", "evaluation_reference")
            _equal(tuple(getattr(value.axiom_diagnostic, name) for name in AXIOM_FIELDS), axiom_passes(subject), "axiom_diagnostic")
            _equal(value.axiom_diagnostic.notes, tuple(axiom_explanation(f"A{i}", subject) for i in range(1, 6)), "notes")
            for index, record in enumerate(value.produced_diagnostics):
                _exact(record.payload, AxiomCheckDiagnostic, "payload")
                _equal((record.diagnostic_reference, record.payload.axiom_id, record.payload.subject),
                       (value.request.request_reference + f":diagnostic:A{index+1}", f"A{index+1}", subject), "produced_diagnostics")
    previous = origin.emitted_diagnostics[0]
    severity = previous.envelope.severity
    for record in value.produced_diagnostics:
        impact = record.payload.current_impact if type(record.payload) is AxiomCheckDiagnostic else "INFO" if type(value) is TopologyResult else "ERROR"
        severity = max((severity, impact), key=SEVERITIES.index)
        _equal((record.envelope.subject_reference, record.envelope.chain_root_reference, record.envelope.parent_diagnostic_reference, record.envelope.severity),
               (previous.envelope.subject_reference, origin.emitted_diagnostics[0].diagnostic_reference, previous.diagnostic_reference, severity), "envelope")
        previous = record


MODULES_AGGREGATE = 'f431a5056601adaf1959fdf0252f0750e5b388177b5e29f168a0ea1375e82400'
GENERATION_AGGREGATE = '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8'
CURRENT_PRODUCER_AGGREGATES = (MODULES_AGGREGATE, GENERATION_AGGREGATE)

SOURCE_BASELINES = (('LEGACY_C78',
  {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
   'aggregate_sha256': '0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb',
   'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
   'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
   'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
   'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
   'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
   'diagnostic_source_sha256': '825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7',
   'taxonomy_source_sha256': 'f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892'},
  (('interfaces/contracts/topology-generator-contract.md',
    'a408b335ecacff01e38113bcd6cc6089142e40219d521e7081e87406fac11147'),
   ('interfaces/contracts/axiom-evaluator-contract.md',
    'dc2edf80d2ded0b89b31df15416e24c13139988ab6fd38adaa6195921a692faf'),
   ('algorithms/topology-expansion.pseudo.md',
    '1b6ab5d3d13b678c67f185f2f91a60d0dae7a976dcbb6df2b169efa6d15c9a3d'),
   ('algorithms/axiom-evaluation.pseudo.md',
    '0f205842840399aaf08932e20cde34761874a3296b260f139dc6a04df0e707ba'),
   ('interfaces/diagnostic-schema.md', '825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7'),
   ('interfaces/rule-id-taxonomy.md', 'f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892'),
   ('interfaces/contracts/diagnostics-module-contract.md',
    '88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37'))),
 ('N3_LIFECYCLE',
  {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
   'aggregate_sha256': '76d59926ce9676b7584c6cdd555f50f56fceda075fa3fc8b37167fd2be43f7c9',
   'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
   'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
   'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
   'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
   'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
   'diagnostic_source_sha256': '825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7',
   'taxonomy_source_sha256': '150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250'},
  (('interfaces/contracts/topology-generator-contract.md',
    'a408b335ecacff01e38113bcd6cc6089142e40219d521e7081e87406fac11147'),
   ('interfaces/contracts/axiom-evaluator-contract.md',
    'dc2edf80d2ded0b89b31df15416e24c13139988ab6fd38adaa6195921a692faf'),
   ('algorithms/topology-expansion.pseudo.md',
    '1b6ab5d3d13b678c67f185f2f91a60d0dae7a976dcbb6df2b169efa6d15c9a3d'),
   ('algorithms/axiom-evaluation.pseudo.md',
    '0f205842840399aaf08932e20cde34761874a3296b260f139dc6a04df0e707ba'),
   ('interfaces/diagnostic-schema.md', '825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7'),
   ('interfaces/rule-id-taxonomy.md', '150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250'),
   ('interfaces/contracts/diagnostics-module-contract.md',
    '88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37'))),
 ('M3_MODULES',
  {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
   'aggregate_sha256': 'f431a5056601adaf1959fdf0252f0750e5b388177b5e29f168a0ea1375e82400',
   'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
   'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
   'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
   'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
   'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
   'diagnostic_source_sha256': '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa',
   'taxonomy_source_sha256': '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'},
  (('interfaces/contracts/topology-generator-contract.md',
    'a408b335ecacff01e38113bcd6cc6089142e40219d521e7081e87406fac11147'),
   ('interfaces/contracts/axiom-evaluator-contract.md',
    'dc2edf80d2ded0b89b31df15416e24c13139988ab6fd38adaa6195921a692faf'),
   ('algorithms/topology-expansion.pseudo.md',
    '1b6ab5d3d13b678c67f185f2f91a60d0dae7a976dcbb6df2b169efa6d15c9a3d'),
   ('algorithms/axiom-evaluation.pseudo.md',
    '0f205842840399aaf08932e20cde34761874a3296b260f139dc6a04df0e707ba'),
   ('interfaces/diagnostic-schema.md', '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa'),
   ('interfaces/rule-id-taxonomy.md', '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'),
   ('interfaces/contracts/diagnostics-module-contract.md',
    '6bd5dc891960cbd9fcdc878de6b46b715912df43ccd1a2affc9793176776376b'))))

SOURCE_BASELINES += (('M3_GENERATION',
 {'dependency_id': 'ash_cosmological_model.f2_9.canonical',
  'aggregate_sha256': '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8',
  'state_space_sha256': '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e',
  'codeword_source_sha256': '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c',
  'validity_source_sha256': '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e',
  'classification_source_sha256': '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff',
  'recovery_source_sha256': 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd',
  'diagnostic_source_sha256': '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa',
  'taxonomy_source_sha256': '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'},
 (('interfaces/contracts/topology-generator-contract.md',
   'a408b335ecacff01e38113bcd6cc6089142e40219d521e7081e87406fac11147'),
  ('interfaces/contracts/axiom-evaluator-contract.md',
   'dc2edf80d2ded0b89b31df15416e24c13139988ab6fd38adaa6195921a692faf'),
  ('algorithms/topology-expansion.pseudo.md',
   '1b6ab5d3d13b678c67f185f2f91a60d0dae7a976dcbb6df2b169efa6d15c9a3d'),
  ('algorithms/axiom-evaluation.pseudo.md',
   '0f205842840399aaf08932e20cde34761874a3296b260f139dc6a04df0e707ba'),
  ('interfaces/diagnostic-schema.md', '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa'),
  ('interfaces/rule-id-taxonomy.md', '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'),
  ('interfaces/contracts/diagnostics-module-contract.md',
   '5ba322a2376bb325e5d58d9341938535ee8d69ff0fc286b3969dfdb77bd8c225'))),)

FIELD_DOMAINS = {'TopologyAxiomPolicyBinding': {'policy_id': 'literal YWE-TOPOLOGY-AXIOM-REFERENCE-001',
                                'policy_version': 'literal 1.0.0',
                                'policy_sha256': 'literal '
                                                 'ab645a078e9aaee04e3eb01ac1ced01de986340d8f0242057eb3e4567196c7ae'},
 'TopologyAxiomSourceBinding': {'canonical_binding': 'CanonicalAshBinding',
                                'contract_pins': 'tuple exactly7 of exact tuple(path: ASCII1..256, sha256: '
                                                 'lowercasehex64)'},
 'TopologyRequest': {'request_reference': 'Reference160',
                     'origin_diagnosis': 'StateDiagnosis',
                     'depth': 'Signed64',
                     'seed_token': 'ASCII [A-Za-z0-9_-]{1,32}'},
 'TopologyNode': {'node_id': 'ASCII1..49',
                  'parent_id': 'ASCII1..48|null',
                  'depth': 'integer0..6',
                  'ordinal': 'integer0..728',
                  'branch_kind': 'enum root|continuation|positive|negative',
                  'path_token': 'ASCII r[012]{0,6}'},
 'TopologyDiagnostic': {'request_reference': 'Reference160',
                        'topology_reference': 'Reference256|null',
                        'input_state': 'AshState|null',
                        'seed_token': 'ASCII [A-Za-z0-9_-]{1,32}',
                        'depth': 'Signed64',
                        'frontier_count': 'integer1..729|null',
                        'visited_node_count': 'integer0..1093',
                        'outcome': 'enum COMPLETE|REJECTED',
                        'failure_code': 'TopologyFailureCode|null',
                        'notes': 'tuple1..8 of Text512'},
 'AxiomSubjectProvenance': {'source_kind': 'literal DECLARED_REFERENCE_INPUT',
                            'source_reference': 'Reference160',
                            'method_id': 'Identifier64',
                            'method_revision': 'Identifier32',
                            'origin_diagnosis_reference': 'Reference256'},
 'AxiomMeasure': {'ticks': 'NonNegativeInt63',
                  'unit': 'enum STRUCTURE_TICK|ERASURE_TICK',
                  'ticks_per_unit': 'integer1..1000000000'},
 'AxiomSubject': {'subject_reference': 'Reference160',
                  'state': 'AshState',
                  'relation_count': 'NonNegativeInt63',
                  'raw_measure': 'AxiomMeasure',
                  'compressed_measure': 'AxiomMeasure',
                  'scale_count': 'NonNegativeInt63',
                  'erasure_cost': 'AxiomMeasure',
                  'self_reference_capable': 'exact bool',
                  'self_model_available': 'exact bool',
                  'provenance': 'AxiomSubjectProvenance'},
 'AxiomRequest': {'request_reference': 'Reference160', 'origin_diagnosis': 'StateDiagnosis', 'subject': 'AxiomSubject'},
 'AxiomCheckDiagnostic': {'axiom_id': 'enum A1|A2|A3|A4|A5',
                          'subject': 'AxiomSubject',
                          'passed': 'exact bool',
                          'current_impact': 'enum INFO|WARNING',
                          'operator': 'enum GT_ZERO|LT|GT_ONE|BOTH_TRUE',
                          'operand_names': 'tuple1..2 of AxiomOperandName',
                          'overall_pass': 'exact bool|null',
                          'explanation': 'Text512'},
 'AxiomInputDiagnostic': {'request_reference': 'Reference160',
                          'subject': 'AxiomSubject',
                          'failure_code': 'AxiomFailureCode',
                          'failed_field': 'FailureField',
                          'explanation': 'Text512'},
 'GenerationDiagnosticRecord': {'diagnostic_reference': 'Reference256',
                                'envelope': 'DiagnosticEnvelope after source adoption',
                                'payload': 'TopologyDiagnostic|AxiomCheckDiagnostic|AxiomInputDiagnostic'},
 'PendingGenerationDiagnostic': {'diagnostic_reference': 'Reference256',
                                 'intended_kind': 'enum TOPOLOGY|AXIOM',
                                 'intended_rule_ids': 'tuple1..5 of source-adopted topology/axiom exact rule IDs',
                                 'failure_code': 'enum '
                                                 'ORIGIN_REJECTED|REFERENCE_COLLISION|SOURCE_UNSUPPORTED|VALIDATION_UNAVAILABLE',
                                 'missing_requirements': 'tuple1..4 unique of '
                                                         'CURRENT_SOURCE|VERIFIED_ORIGIN|VALIDATION_RESULT|DISTINCT_REFERENCES',
                                 'reason': 'Text512'},
 'TopologyResult': {'topology_reference': 'Reference256',
                    'request': 'TopologyRequest',
                    'policy_binding': 'TopologyAxiomPolicyBinding',
                    'source_binding': 'TopologyAxiomSourceBinding',
                    'origin_validation': 'DiagnosisValidation',
                    'input_state': 'AshState',
                    'nodes': 'tuple1..729 of TopologyNode',
                    'visited_node_count': 'integer1..1093',
                    'produced_diagnostics': 'tuple exactly1 GenerationDiagnosticRecord'},
 'TopologyFailure': {'request': 'TopologyRequest',
                     'policy_binding': 'TopologyAxiomPolicyBinding',
                     'source_binding': 'TopologyAxiomSourceBinding',
                     'origin_validation': 'DiagnosisValidation|null',
                     'failure_code': 'TopologyFailureCode',
                     'failed_field': 'FailureField',
                     'produced_diagnostics': 'tuple0..1 GenerationDiagnosticRecord',
                     'pending_diagnostic': 'PendingGenerationDiagnostic|null'},
 'AxiomDiagnostic': {'a1_relational_existence': 'exact bool',
                     'a2_structural_compressibility': 'exact bool',
                     'a3_multi_scale_persistence': 'exact bool',
                     'a4_energetic_cost_of_erasure': 'exact bool',
                     'a5_self_reference_for_consciousness': 'exact bool',
                     'overall_pass': 'exact bool',
                     'notes': 'tuple exactly5 Text512'},
 'AxiomEvaluationResult': {'evaluation_reference': 'Reference256',
                           'request': 'AxiomRequest',
                           'policy_binding': 'TopologyAxiomPolicyBinding',
                           'source_binding': 'TopologyAxiomSourceBinding',
                           'origin_validation': 'DiagnosisValidation',
                           'axiom_diagnostic': 'AxiomDiagnostic',
                           'produced_diagnostics': 'tuple exactly5 GenerationDiagnosticRecord'},
 'AxiomEvaluationFailure': {'request': 'AxiomRequest',
                            'policy_binding': 'TopologyAxiomPolicyBinding',
                            'source_binding': 'TopologyAxiomSourceBinding',
                            'origin_validation': 'DiagnosisValidation|null',
                            'failure_code': 'AxiomFailureCode',
                            'failed_field': 'FailureField',
                            'produced_diagnostics': 'tuple0..1 GenerationDiagnosticRecord',
                            'pending_diagnostic': 'PendingGenerationDiagnostic|null'}}


@dataclass(frozen=True, slots=True)
class TopologyAxiomPolicyBinding(_WireValue):
    policy_id: str
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class TopologyAxiomSourceBinding(_WireValue):
    canonical_binding: state.CanonicalAshBinding
    contract_pins: tuple


@dataclass(frozen=True, slots=True)
class TopologyRequest(_WireValue):
    request_reference: str
    origin_diagnosis: state.StateDiagnosis
    depth: int
    seed_token: str = "F"


@dataclass(frozen=True, slots=True)
class TopologyNode(_WireValue):
    node_id: str
    parent_id: object
    depth: int
    ordinal: int
    branch_kind: str
    path_token: str


@dataclass(frozen=True, slots=True)
class TopologyDiagnostic(_WireValue):
    request_reference: str
    topology_reference: object
    input_state: object
    seed_token: str
    depth: int
    frontier_count: int
    visited_node_count: int
    outcome: str
    failure_code: object
    notes: tuple


@dataclass(frozen=True, slots=True)
class AxiomSubjectProvenance(_WireValue):
    source_kind: str
    source_reference: str
    method_id: str
    method_revision: str
    origin_diagnosis_reference: str


@dataclass(frozen=True, slots=True)
class AxiomMeasure(_WireValue):
    ticks: int
    unit: str
    ticks_per_unit: int


@dataclass(frozen=True, slots=True)
class AxiomSubject(_WireValue):
    subject_reference: str
    state: state.AshState
    relation_count: int
    raw_measure: AxiomMeasure
    compressed_measure: AxiomMeasure
    scale_count: int
    erasure_cost: AxiomMeasure
    self_reference_capable: bool
    self_model_available: bool
    provenance: AxiomSubjectProvenance


@dataclass(frozen=True, slots=True)
class AxiomRequest(_WireValue):
    request_reference: str
    origin_diagnosis: state.StateDiagnosis
    subject: AxiomSubject


@dataclass(frozen=True, slots=True)
class AxiomCheckDiagnostic(_WireValue):
    axiom_id: str
    subject: AxiomSubject
    passed: bool
    current_impact: str
    operator: str
    operand_names: tuple
    overall_pass: object
    explanation: str


@dataclass(frozen=True, slots=True)
class AxiomInputDiagnostic(_WireValue):
    request_reference: str
    subject: AxiomSubject
    failure_code: str
    failed_field: str
    explanation: str


@dataclass(frozen=True, slots=True)
class GenerationDiagnosticRecord(_WireValue):
    diagnostic_reference: str
    envelope: state.DiagnosticEnvelope
    payload: object


@dataclass(frozen=True, slots=True)
class PendingGenerationDiagnostic(_WireValue):
    diagnostic_reference: str
    intended_kind: str
    intended_rule_ids: tuple
    failure_code: str
    missing_requirements: tuple
    reason: str


@dataclass(frozen=True, slots=True)
class TopologyResult(_Packet):
    packet_kind: ClassVar[str] = "topology_result"
    topology_reference: str
    request: TopologyRequest
    policy_binding: TopologyAxiomPolicyBinding
    source_binding: TopologyAxiomSourceBinding
    origin_validation: state.DiagnosisValidation
    input_state: state.AshState
    nodes: tuple
    visited_node_count: int
    produced_diagnostics: tuple


@dataclass(frozen=True, slots=True)
class TopologyFailure(_Packet):
    packet_kind: ClassVar[str] = "topology_failure"
    request: TopologyRequest
    policy_binding: TopologyAxiomPolicyBinding
    source_binding: TopologyAxiomSourceBinding
    origin_validation: object
    failure_code: str
    failed_field: str
    produced_diagnostics: tuple
    pending_diagnostic: object


@dataclass(frozen=True, slots=True)
class AxiomDiagnostic(_WireValue):
    a1_relational_existence: bool
    a2_structural_compressibility: bool
    a3_multi_scale_persistence: bool
    a4_energetic_cost_of_erasure: bool
    a5_self_reference_for_consciousness: bool
    overall_pass: bool
    notes: tuple


@dataclass(frozen=True, slots=True)
class AxiomEvaluationResult(_Packet):
    packet_kind: ClassVar[str] = "axiom_evaluation_result"
    evaluation_reference: str
    request: AxiomRequest
    policy_binding: TopologyAxiomPolicyBinding
    source_binding: TopologyAxiomSourceBinding
    origin_validation: state.DiagnosisValidation
    axiom_diagnostic: AxiomDiagnostic
    produced_diagnostics: tuple


@dataclass(frozen=True, slots=True)
class AxiomEvaluationFailure(_Packet):
    packet_kind: ClassVar[str] = "axiom_evaluation_failure"
    request: AxiomRequest
    policy_binding: TopologyAxiomPolicyBinding
    source_binding: TopologyAxiomSourceBinding
    origin_validation: object
    failure_code: str
    failed_field: str
    produced_diagnostics: tuple
    pending_diagnostic: object

WIRE_TYPES = (TopologyAxiomPolicyBinding, TopologyAxiomSourceBinding, TopologyRequest, TopologyNode, TopologyDiagnostic, AxiomSubjectProvenance, AxiomMeasure, AxiomSubject, AxiomRequest, AxiomCheckDiagnostic, AxiomInputDiagnostic, GenerationDiagnosticRecord, PendingGenerationDiagnostic, TopologyResult, TopologyFailure, AxiomDiagnostic, AxiomEvaluationResult, AxiomEvaluationFailure,)

PACKET_TYPES = (TopologyResult, TopologyFailure, AxiomEvaluationResult, AxiomEvaluationFailure,)

PACKET_KINDS = {TopologyResult: 'topology_result', TopologyFailure: 'topology_failure', AxiomEvaluationResult: 'axiom_evaluation_result', AxiomEvaluationFailure: 'axiom_evaluation_failure'}


def _model_configuration(model, policy):
    from .state_model import StateModel

    if type(model) is not StateModel:
        _fail("model", "GENERATION_COMPOSITION_INVALID")
    _exact(policy, TopologyAxiomPolicyBinding, "policy_binding")
    revalidate_value(policy)
    source = StateModel.canonical_binding.fget(model)
    profile = StateModel.profile_binding.fget(model)
    _exact(source, state.CanonicalAshBinding, "model.canonical_binding")
    _exact(profile, (state.AvailableProfileBinding, state.UnavailableProfileBinding), "model.profile_binding")
    revalidate_value(profile)
    return source_binding_for(source), profile, policy


_PRODUCER_COOKIE_MARKER = object()


@dataclass(frozen=True, slots=True)
class _OwnedProducerCookie:
    marker: object
    owner: object
    model: object
    policy: object


def _issue_producer_cookie(owner, model, policy):
    return _OwnedProducerCookie(_PRODUCER_COOKIE_MARKER, owner, model, policy)


def _owned_configuration(owner, expected_class):
    if type(owner) is not expected_class:
        _fail("producer", "GENERATION_COMPOSITION_INVALID")
    try:
        cookie = object.__getattribute__(owner, "_cookie")
        model = object.__getattribute__(owner, "_model")
        policy = object.__getattribute__(owner, "_policy")
        if (object.__getattribute__(owner, "_self_identity") is not owner or
                type(cookie) is not _OwnedProducerCookie or
                cookie.marker is not _PRODUCER_COOKIE_MARKER or cookie.owner is not owner or
                cookie.model is not model or cookie.policy is not policy):
            _fail("producer", "GENERATION_COMPOSITION_INVALID")
    except AttributeError:
        _fail("producer", "GENERATION_COMPOSITION_INVALID")
    return _model_configuration(model, policy)


def _validate_origin(model, request, configuration):
    from .state_model import StateModel

    if configuration[0].canonical_binding.aggregate_sha256 not in CURRENT_PRODUCER_AGGREGATES:
        return None
    try:
        witness = StateModel.validate_diagnosis(model, request.origin_diagnosis)
    except state.StateContractError:
        raise
    except Exception:
        return None
    if type(witness) is not getattr(state, "DiagnosisValidation", None):
        return None
    try:
        revalidate_value(witness)
        if (witness.submitted_diagnosis != request.origin_diagnosis or
                witness.current_source_binding != configuration[0].canonical_binding or
                witness.current_profile_binding != configuration[1]):
            return None
    except (GenerationContractError, state.StateContractError):
        return None
    return witness


@dataclass(frozen=True, slots=True)
class _OwnedResultCookie:
    issuer: object
    owner_token: object
    result: object


def _seal(result, owner, cookie):
    canonical_bytes(result)
    object.__setattr__(result, "_issuer", owner)
    object.__setattr__(result, "_cookie", _OwnedResultCookie(owner, cookie, result))
    object.__setattr__(result, "_self_identity", result)
    return result


def _validate_seal(result, owner, cookie, kinds, configuration):
    if not _type_is_one_of(type(result), kinds):
        return False
    try:
        seal = object.__getattribute__(result, "_cookie")
        if (object.__getattribute__(result, "_issuer") is not owner or
                type(seal) is not _OwnedResultCookie or seal.issuer is not owner or
                seal.owner_token is not cookie or seal.result is not result or
                object.__getattribute__(result, "_self_identity") is not result):
            return False
        canonical_bytes(result)
        if result.source_binding != configuration[0] or result.policy_binding != configuration[2]:
            return False
        validation = result.origin_validation
        if validation is not None and validation.current_profile_binding != configuration[1]:
            return False
        current = _validate_origin(owner._model, result.request, configuration)
        if current != validation:
            return False
    except (AttributeError, GenerationContractError, state.StateContractError):
        return False
    return True


def _failure(request, configuration, validation, code, field):
    source, _, policy = configuration
    topo = type(request) is TopologyRequest
    kind = "TOPOLOGY" if topo else "AXIOM"
    reference = request.request_reference + (":diagnostic:topology" if topo else ":diagnostic:axiom-input")
    if code in PENDING_REQUIREMENTS:
        missing = (PENDING_REQUIREMENTS[code],)
        pending = PendingGenerationDiagnostic(reference, kind, TOPOLOGY_ADMISSION if topo else AXIOM_ADMISSION,
                                              code, missing, pending_reason(kind, code, missing))
        records = ()
    else:
        pending = None
        if topo:
            payload = TopologyDiagnostic(request.request_reference, None, request.origin_diagnosis.parsed_state,
                                         request.seed_token, request.depth, None, 0, "REJECTED", code,
                                         topology_refusal_notes(code))
            summary, notes, rules = "Topology request rejected.", payload.notes, TOPOLOGY_ADMISSION
        else:
            payload = AxiomInputDiagnostic(request.request_reference, request.subject, code, field,
                                           refusal_explanation(code, field))
            summary, notes, rules = ("Axiom subject rejected.",
                                     (payload.explanation, "No axiom components were evaluated.",
                                      "Measurements and subject provenance are declared reference input."), AXIOM_ADMISSION)
        origin = request.origin_diagnosis.emitted_diagnostics[0]
        severity = max((origin.envelope.severity, "ERROR"), key=SEVERITIES.index)
        envelope = state.DiagnosticEnvelope(kind, severity, "PROCESSING", "BLOCKED", origin.envelope.subject_reference,
                                             origin.diagnostic_reference, origin.diagnostic_reference, rules, summary, notes)
        records = (GenerationDiagnosticRecord(reference, envelope, payload),)
    cls = TopologyFailure if topo else AxiomEvaluationFailure
    return cls(request, policy, source, validation, code, field, records, pending)


def wire_schema(value):
    _exact(value, WIRE_TYPES, "value")
    revalidate_value(value)
    source = None
    if type(value) is TopologyAxiomSourceBinding:
        source = value.canonical_binding
    elif _type_is_one_of(type(value), PACKET_TYPES):
        source = value.source_binding.canonical_binding
    elif type(value) is TopologyRequest or type(value) is AxiomRequest:
        source = value.origin_diagnosis.source_binding
    if source is not None and state.canonical_source_baseline(source) == "M3_GENERATION":
        return "https://ywe.local/schemas/m3_generation_topology_axiom_schema.json"
    return "https://ywe.local/schemas/m3_topology_axiom_schema.json"
