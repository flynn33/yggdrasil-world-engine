"""Pure valid-state realm identity and finite transition registry [YWE-REQ-0046]."""
from __future__ import annotations

from . import realm_transition_values as values
from . import state_values as state
from .state_model import StateModel

_OWNER_COOKIE = object()
_RESULT_COOKIE = object()


def _configuration(owner, expected):
    cookie = getattr(owner, "_cookie", None) if type(owner) is expected else None
    if (type(owner) is not expected or getattr(owner, "_self_identity", None) is not owner or
            type(cookie) is not tuple or len(cookie) != 2 or cookie[0] is not _OWNER_COOKIE or cookie[1] is not owner):
        values._fail("realm_transition_binding")
    model = owner._model
    if type(model) is not StateModel:
        values._fail("state_model")
    binding = owner._binding
    values.revalidate_value(binding)
    if (binding.canonical_binding != StateModel.canonical_binding.fget(model) or
            binding.profile_binding != StateModel.profile_binding.fget(model)):
        values._fail("realm_transition_binding")
    if expected is TransitionRegistry:
        values.revalidate_value(owner._catalog)
        if owner._catalog.binding != binding:
            values._fail("transition_catalog")
    return binding


def _origin(owner, expected, origin, operation_reference):
    binding = _configuration(owner, expected)
    values._ref(operation_reference, "operation_reference")
    if type(origin) is not state.StateDiagnosis:
        values._fail("origin_diagnosis", "REALM_TRANSITION_ORIGIN_REJECTED")
    validation = StateModel.validate_diagnosis(owner._model, origin)
    if validation.status != "VERIFIED":
        values._fail("origin_diagnosis", "REALM_TRANSITION_ORIGIN_REJECTED")
    return binding, validation


class _Records:
    """Private immediate in-memory construction; no persistence or caller dispatch."""
    __slots__ = ("operation", "origin", "kind", "records")

    def __init__(self, operation, origin, kind):
        self.operation, self.origin, self.kind, self.records = operation, origin, kind, []

    def append(self, phase, payload, *, failed=False):
        ordinal = len(self.records)
        reference = values.record_reference(self.operation, ordinal)
        root = self.origin.emitted_diagnostics[0]
        previous = root.envelope if not self.records else self.records[-1].emission.envelope
        severity = max((previous.severity, "ERROR" if failed else "INFO"), key=values.SEVERITIES.index)
        rules = (("ASH-STATE-VALIDITY-001",) if self.kind == "REALM_ENCODING" else
                 ("ASH-STATE-VALIDITY-001", "ASH-CODEWORD-REGISTRY-001")) if phase == "VALID_SOURCE" else values.PHASE_RULES[phase]
        summaries = {"VALID_SOURCE": "Strict module source validity evaluated.",
                     "IDENTITY": "Full nine-coordinate realm identity encoded.",
                     "SELECTION": "Canonical transition selection evaluated.",
                     "APPLICABILITY": "Declared transition applicability evaluated.",
                     "TRANSFORMATION": "Complete nine-coordinate XOR candidate constructed."}
        notes = {"VALID_SOURCE": "The current complete diagnosis and profile govern valid source admission.",
                 "IDENTITY": "Vertex and realm are equal lossless full-vector aliases; orbit is distinct.",
                 "SELECTION": "Selection uses exact source-order identifiers or a complete canonical codeword.",
                 "APPLICABILITY": "Applicability is the declared mask bit indexed by the complete source signature.",
                 "TRANSFORMATION": "Target diagnosis is retained without normalization or session publication."}
        envelope = state.DiagnosticEnvelope(self.kind, severity, "PROCESSING", "BLOCKED" if failed else "RESOLVED",
                    root.envelope.subject_reference,
                    root.diagnostic_reference if not self.records else self.records[-1].record_reference,
                    root.envelope.chain_root_reference, rules, summaries[phase], (notes[phase],))
        record = values.RealmTransitionRecord(reference, phase, state.DiagnosticEmission(reference, envelope), payload)
        self.records.append(record)


def _gate(origin, builder):
    diagnostic = origin.state_validity_diagnostic
    failed = not diagnostic.is_valid
    builder.append("VALID_SOURCE", values.RealmTransitionGate(origin.assessment_binding.assessment_reference,
                   "VERIFIED", diagnostic.admissibility_status, diagnostic.is_valid), failed=failed)
    return not failed


def _finish(owner, result):
    # First perform the complete pure-result guard, then seal actual production.
    values.canonical_bytes(result)
    object.__setattr__(result, "_issuer", owner)
    object.__setattr__(result, "_cookie", (_RESULT_COOKIE, result))
    object.__setattr__(result, "_self_identity", result)
    return result


def _failure(owner, binding, origin, validation, builder, action, phase, code, selection=None, definition=None):
    return _finish(owner, values.RealmTransitionFailure(builder.operation, binding, origin, validation,
                   action, phase, code, selection, definition, tuple(builder.records)))


def _source_failure(binding):
    return "PROFILE_UNAVAILABLE" if type(binding.profile_binding) is state.UnavailableProfileBinding else "STATE_NOT_VALID"


def _encode(owner, origin, operation_reference):
    binding, validation = _origin(owner, RealmEncoder, origin, operation_reference)
    builder = _Records(operation_reference, origin, "REALM_ENCODING")
    if not _gate(origin, builder):
        return _failure(owner, binding, origin, validation, builder, "ENCODE", "VALID_SOURCE", _source_failure(binding))
    signature = state.AshState.signature.fget(origin.parsed_state)
    identity = values.RealmIdentity(signature, "ash_state_" + signature, "ash_state_" + signature,
                                   origin.state_validity_diagnostic.orbit_info.orbit_id)
    builder.append("IDENTITY", identity)
    return _finish(owner, values.RealmEncodingResult(operation_reference, binding, origin, validation,
                                                   identity, tuple(builder.records)))


def _applicability(definition, source):
    applies = definition.applicability_mask[int(state.AshState.signature.fget(source), 2)] == "1"
    return values.TransitionApplicabilityObservation(definition.transition_id, definition.codeword, source,
               applies, "SOURCE_ALLOWED" if applies else "SOURCE_NOT_ALLOWED")


def _resolve(owner, origin, operation_reference):
    binding, validation = _origin(owner, TransitionRegistry, origin, operation_reference)
    builder = _Records(operation_reference, origin, "TRANSITION")
    if not _gate(origin, builder):
        return _failure(owner, binding, origin, validation, builder, "RESOLVE", "VALID_SOURCE", _source_failure(binding))
    availability = []
    for definition in owner._catalog.definitions:
        observation = _applicability(definition, origin.parsed_state)
        builder.append("APPLICABILITY", observation)
        availability.append(observation)
    return _finish(owner, values.TransitionResolutionResult(operation_reference, binding, origin, validation,
                   owner._catalog, tuple(availability), tuple(builder.records)))


def _apply(owner, origin, selection, operation_reference):
    if type(selection) is not values.TransitionSelection:
        values._fail("transition_selection", "REALM_TRANSITION_SELECTION_INVALID")
    values.revalidate_value(selection)
    binding, validation = _origin(owner, TransitionRegistry, origin, operation_reference)
    builder = _Records(operation_reference, origin, "TRANSITION")
    if not _gate(origin, builder):
        return _failure(owner, binding, origin, validation, builder, "APPLY", "VALID_SOURCE", _source_failure(binding), selection)
    if selection.selection_kind == "IDENTIFIER":
        definition = next((item for item in owner._catalog.definitions if item.transition_id == selection.transition_id), None)
    else:
        definition = next((item for item in owner._catalog.definitions if item.codeword == selection.codeword), None)
    if definition is None:
        code = "TRANSITION_UNKNOWN" if selection.selection_kind == "IDENTIFIER" else "CODEWORD_NOT_CANONICAL"
        builder.append("SELECTION", values.TransitionSelectionObservation(selection, None, None, "REFUSED", code), failed=True)
        return _failure(owner, binding, origin, validation, builder, "APPLY", "SELECTION", code, selection)
    builder.append("SELECTION", values.TransitionSelectionObservation(selection, definition.transition_id,
                   definition.codeword, "SELECTED", None))
    applicability = _applicability(definition, origin.parsed_state)
    builder.append("APPLICABILITY", applicability, failed=not applicability.is_applicable)
    if not applicability.is_applicable:
        return _failure(owner, binding, origin, validation, builder, "APPLY", "APPLICABILITY",
                        "TRANSITION_NOT_APPLICABLE", selection, definition)
    candidate = state.AshState(tuple(bit ^ code for bit, code in zip(origin.parsed_state.bits, definition.codeword.bits)))
    target = StateModel.inspect_state(owner._model, candidate)
    builder.append("TRANSFORMATION", values.TransitionTransformationObservation(definition.transition_id,
                   definition.codeword, origin.parsed_state, candidate, target))
    return _finish(owner, values.TransitionApplicationResult(operation_reference, binding, origin, validation,
                   selection, definition, candidate, target, tuple(builder.records)))


def _validate_owned(owner, expected, result):
    from . import planner_emitter_values as pe
    if type(result) is pe.TransitionChainResult or type(result) is pe.TransitionChainFailure:
        if expected is not TransitionRegistry:
            return False
        try:
            binding = _configuration(owner, expected)
            if not pe._result_is_owned(result, owner, (pe.TransitionChainResult, pe.TransitionChainFailure)) or result.binding != binding:
                return False
            fresh = _chain(owner, result.origin, result.selections, result.operation_reference)
            return pe.canonical_bytes(result) == pe.canonical_bytes(fresh)
        except (pe.PlannerEmitterContractError, values.RealmTransitionContractError,
                state.StateContractError, AttributeError, TypeError, ValueError):
            return False
    if not any(type(result) is kind for kind in values.RESULT_TYPES):
        return False
    cookie = getattr(result, "_cookie", None)
    if (getattr(result, "_issuer", None) is not owner or type(cookie) is not tuple or len(cookie) != 2 or
            cookie[0] is not _RESULT_COOKIE or cookie[1] is not result or
            getattr(result, "_self_identity", None) is not result):
        return False
    try:
        binding = _configuration(owner, expected)
        values.revalidate_value(result)
        if result.binding != binding:
            return False
        kind = type(result)
        action = result.action if kind is values.RealmTransitionFailure else (
                 "ENCODE" if kind is values.RealmEncodingResult else "RESOLVE" if kind is values.TransitionResolutionResult else "APPLY")
        if action == "ENCODE":
            if expected is not RealmEncoder:
                return False
            fresh = _encode(owner, result.origin, result.operation_reference)
        elif action == "RESOLVE":
            if expected is not TransitionRegistry:
                return False
            fresh = _resolve(owner, result.origin, result.operation_reference)
        else:
            if expected is not TransitionRegistry:
                return False
            fresh = _apply(owner, result.origin, result.selection, result.operation_reference)
        return values.canonical_bytes(result) == values.canonical_bytes(fresh)
    except (values.RealmTransitionContractError, state.StateContractError, AttributeError, TypeError, ValueError):
        return False


class RealmEncoder:
    __slots__ = ("_model", "_binding", "_cookie", "_self_identity")

    def __init__(self, state_model, binding):
        if type(state_model) is not StateModel:
            values._fail("state_model")
        if type(binding) is not values.RealmTransitionBinding:
            values._fail("realm_transition_binding")
        self._model, self._binding, self._cookie, self._self_identity = state_model, binding, (_OWNER_COOKIE, self), self
        _configuration(self, RealmEncoder)

    def configuration(self):
        return _configuration(self, RealmEncoder)

    def validate_owned_result(self, result):
        return _validate_owned(self, RealmEncoder, result)

    def encode(self, origin, *, operation_reference):
        return _encode(self, origin, operation_reference)


class TransitionRegistry:
    __slots__ = ("_model", "_binding", "_catalog", "_cookie", "_self_identity")

    def __init__(self, state_model, catalog):
        if type(state_model) is not StateModel:
            values._fail("state_model")
        if type(catalog) is not values.TransitionCatalog:
            values._fail("transition_catalog", "REALM_TRANSITION_CATALOG_INVALID")
        self._model, self._binding, self._catalog = state_model, catalog.binding, catalog
        self._cookie, self._self_identity = (_OWNER_COOKIE, self), self
        _configuration(self, TransitionRegistry)

    def configuration(self):
        return _configuration(self, TransitionRegistry)

    def validate_owned_result(self, result):
        return _validate_owned(self, TransitionRegistry, result)

    def resolve(self, origin, *, operation_reference):
        return _resolve(self, origin, operation_reference)

    def apply(self, origin, selection, *, operation_reference):
        return _apply(self, origin, selection, operation_reference)

    def apply_chain(self, origin, selections, *, operation_reference):
        return _chain(self, origin, selections, operation_reference)


class _ChainRecords:
    __slots__ = ("operation", "origin", "records")

    def __init__(self, operation, origin):
        self.operation, self.origin, self.records = operation, origin, []

    def append(self, phase, payload, *, failed=False):
        from . import planner_emitter_values as pe
        reference = values.record_reference(self.operation, len(self.records))
        root = self.origin.emitted_diagnostics[0]
        previous = root.envelope if not self.records else self.records[-1].emission.envelope
        severity = max((previous.severity, "ERROR" if failed else "INFO"), key=values.SEVERITIES.index)
        rules = (("ASH-STATE-VALIDITY-001", "ASH-CODEWORD-REGISTRY-001") if phase == "VALID_SOURCE" else
                 ("ASH-CODEWORD-TRANSFORMATION-001", "ASH-STATE-VALIDITY-001") if phase == "TRANSFORMATION" else
                 values.PHASE_RULES[phase])
        summaries = {"VALID_SOURCE": "Strict chain source validity evaluated.",
                     "SELECTION": "Canonical chain selection evaluated.",
                     "APPLICABILITY": "Actual candidate applicability evaluated.",
                     "TRANSFORMATION": "Full XOR and strict target validity evaluated."}
        notes = {"VALID_SOURCE": "The current complete diagnosis and profile govern chain admission.",
                 "SELECTION": "Selection uses the exact canonical catalog and requested order.",
                 "APPLICABILITY": "The declared mask is indexed by the actual intermediate candidate.",
                 "TRANSFORMATION": "Only this exact already evaluated VALID proof permits the next step."}
        envelope = pe.ChainEnvelope("TRANSITION", severity, "PROCESSING", "BLOCKED" if failed else "RESOLVED",
                   root.envelope.subject_reference,
                   root.diagnostic_reference if not self.records else self.records[-1].record_reference,
                   root.envelope.chain_root_reference, rules, summaries[phase], (notes[phase],))
        record = pe.ChainRecord(reference, phase, pe.ChainDiagnosticEmission(reference, envelope), payload)
        self.records.append(record)
        return reference


def _chain(owner, origin, selections, operation_reference):
    from . import planner_emitter_values as pe
    pe._ref(operation_reference, maximum=160)
    if type(selections) is not tuple or len(selections) > 4:
        pe._fail("selections")
    for selection in selections:
        values._exact(selection, values.TransitionSelection, "transition_selection")
        values.revalidate_value(selection)
    binding, validation = _origin(owner, TransitionRegistry, origin, operation_reference)
    if state.canonical_source_baseline(binding.canonical_binding) != "M3_GENERATION":
        pe._fail("binding", "SOURCE_UNRECOGNIZED")
    builder = _ChainRecords(operation_reference, origin)
    steps = []
    current = origin.parsed_state

    def failure(index, phase, code):
        result = pe.TransitionChainFailure(operation_reference, binding, origin, validation, selections,
                 tuple(steps), current, tuple(builder.records), index, phase, code, "FAILED_PREFIX")
        return pe._seal_result(result, owner)

    if not _gate(origin, builder):
        return failure(None, "VALID_SOURCE", _source_failure(binding))
    for index, selection in enumerate(selections):
        definition = next((item for item in owner._catalog.definitions if
                           item.transition_id == selection.transition_id), None) if selection.selection_kind == "IDENTIFIER" else next(
                           (item for item in owner._catalog.definitions if item.codeword == selection.codeword), None)
        if definition is None:
            code = "TRANSITION_UNKNOWN" if selection.selection_kind == "IDENTIFIER" else "CODEWORD_NOT_CANONICAL"
            builder.append("SELECTION", values.TransitionSelectionObservation(selection, None, None, "REFUSED", code), failed=True)
            return failure(index, "SELECTION", code)
        observation = values.TransitionSelectionObservation(selection, definition.transition_id, definition.codeword, "SELECTED", None)
        selection_ref = builder.append("SELECTION", observation)
        applicability = _applicability(definition, current)
        applicability_ref = builder.append("APPLICABILITY", applicability, failed=not applicability.is_applicable)
        if not applicability.is_applicable:
            return failure(index, "APPLICABILITY", "TRANSITION_NOT_APPLICABLE")
        before = current
        current = state.AshState(tuple(bit ^ code for bit, code in zip(before.bits, definition.codeword.bits)))
        target = StateModel.inspect_state(owner._model, current)
        transformation = values.TransitionTransformationObservation(definition.transition_id, definition.codeword, before, current, target)
        transformation_ref = builder.append("TRANSFORMATION", transformation, failed=not target.is_valid)
        proof_ref = origin.emitted_diagnostics[0].diagnostic_reference if index == 0 else steps[-1].record_references[-1]
        steps.append(pe.ChainStep(index, before, proof_ref, selection, definition, observation, applicability,
                                 transformation, (selection_ref, applicability_ref, transformation_ref)))
        if not target.is_valid:
            return failure(index, "TRANSFORMATION", "CHAIN_TARGET_NOT_VALID")
    final = steps[-1].transformation_observation.target_diagnosis if steps else origin.state_validity_diagnostic
    result = pe.TransitionChainResult(operation_reference, binding, origin, validation, selections, tuple(steps),
                                    current, tuple(builder.records), final, "COMPLETE")
    return pe._seal_result(result, owner)


class RealmTransitionReferenceRunner:
    """Explicit local capture composition; collector ports are checked before use."""
    __slots__ = ("_encoder", "_registry", "_diagnostics")

    def __init__(self, encoder, registry, diagnostics):
        from .diagnostics import ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics
        from .diagnostic_module_values import ModuleProducerRegistrationReceipt
        if type(encoder) is not RealmEncoder or type(registry) is not TransitionRegistry:
            values._fail("realm_transition_binding")
        if not any(type(diagnostics) is cls for cls in
                   (ReferenceDevelopmentDiagnostics, ReferenceReleaseDiagnostics)):
            values._fail("diagnostics")
        if RealmEncoder.configuration(encoder) != TransitionRegistry.configuration(registry):
            values._fail("realm_transition_binding")
        for producer in (encoder, registry):
            receipt = type(diagnostics).register_module_producer(diagnostics, producer)
            if type(receipt) is not ModuleProducerRegistrationReceipt or receipt.status != "REGISTERED":
                values._fail("diagnostics")
        self._encoder, self._registry, self._diagnostics = encoder, registry, diagnostics

    def run_encode(self, origin, *, operation_reference):
        result = RealmEncoder.encode(self._encoder, origin, operation_reference=operation_reference)
        return _capture(self._diagnostics, self._encoder, result)

    def run_resolve(self, origin, *, operation_reference):
        result = TransitionRegistry.resolve(self._registry, origin, operation_reference=operation_reference)
        return _capture(self._diagnostics, self._registry, result)

    def run_apply(self, origin, selection, *, operation_reference):
        result = TransitionRegistry.apply(self._registry, origin, selection, operation_reference=operation_reference)
        return _capture(self._diagnostics, self._registry, result)


def _capture(diagnostics, owner, result):
    from .diagnostic_module_values import (ModuleCaptureContext, ModuleCaptureAdmission,
                                           ModuleFinalObservationReceipt, ModuleReturnAuditObservation)
    from .diagnostic_module_capture import ModuleCaptureScope
    from .diagnostics_values import DiagnosticsCompletionReceipt

    producer = "REALM_ENCODER" if type(owner) is RealmEncoder else "TRANSITION_REGISTRY"
    owner_class = RealmEncoder if type(owner) is RealmEncoder else TransitionRegistry
    context = ModuleCaptureContext(result.operation_reference, producer, owner_class.configuration(owner),
                                   result.origin, result, ())
    # The public collector admission owns the independently derived combined
    # future-wire preflight and whole reservation before any capture IO.
    admission = type(diagnostics).module_capture(diagnostics, owner, context)
    if type(admission) is not ModuleCaptureAdmission:
        return values.RealmTransitionCaptureReceipt(result.operation_reference, "NOT_CONFIRMED", result,
                   (), None, None, None, "MODULE_CAPTURE_UNCONFIRMED")
    scope = admission.scope if ModuleCaptureScope.validate_issued_for_context(
        admission.scope, diagnostics, owner, context) is True else None
    try:
        ModuleCaptureAdmission.__post_init__(admission)
        matched = admission.operation_reference == result.operation_reference
    except Exception:
        matched = False
    if scope is None:
        receipt = values.RealmTransitionCaptureReceipt(result.operation_reference,
                  "REJECTED" if matched and admission.scope is None and admission.status == "REJECTED" else "NOT_CONFIRMED", result,
                  (), None, None, None, admission.failure_code if matched and admission.scope is None else "MODULE_CAPTURE_UNCONFIRMED")
        values.canonical_bytes(receipt)
        return receipt
    confirmed, attempted, completion, final = [], None, None, None
    failure = admission.failure_code if matched else "MODULE_CAPTURE_UNCONFIRMED"
    status = "CONFIRMED" if matched and admission.status == "ADMITTED" else "NOT_CONFIRMED"
    try:
        if matched and admission.status == "ADMITTED":
            for record in result.constructed_records:
                attempted = record
                try:
                    response = ModuleCaptureScope.append(scope, record)
                except Exception:
                    response = None
                if (type(response) is not state.CaptureReceipt or
                        response.diagnostic_reference != record.record_reference or response.status != "CONFIRMED"):
                    status = "REJECTED" if type(response) is state.CaptureReceipt and response.status == "REJECTED" else "NOT_CONFIRMED"
                    failure = failure or ("MODULE_CAPTURE_REJECTED" if status == "REJECTED" else "MODULE_CAPTURE_UNCONFIRMED")
                    break
                confirmed.append(record.record_reference)
                attempted = None
    finally:
        # An actual issued scope retains its cleanup obligation even after an
        # unconfirmed admission or append. Never retry the first finish call.
        try:
            observed = ModuleCaptureScope.finish(scope, result)
            if type(observed) is DiagnosticsCompletionReceipt:
                completion = observed
                if observed.operation_reference != result.operation_reference or observed.status != "COMPLETE":
                    status = "NOT_CONFIRMED"
                    failure = failure or observed.failure_code or "MODULE_COMPLETION_REJECTED"
            else:
                status, failure = "NOT_CONFIRMED", failure or "MODULE_COMPLETION_MISSING"
        except Exception:
            status, failure = "NOT_CONFIRMED", failure or "MODULE_COMPLETION_MISSING"
        if completion is not None:
            try:
                observed = ModuleCaptureScope.observe_final(scope, result, completion)
                if type(observed) is ModuleFinalObservationReceipt:
                    final = observed
                    if (observed.operation_reference != result.operation_reference or observed.status != "CONFIRMED" or
                            observed.coverage != "COMPLETE_SPECIFIED_SAFE_GRAPH"):
                        status = "NOT_CONFIRMED"
                        failure = failure or observed.failure_code or "MODULE_FINAL_OBSERVATION_REJECTED"
                else:
                    status, failure = "NOT_CONFIRMED", failure or "MODULE_FINAL_OBSERVATION_REJECTED"
            except Exception:
                status, failure = "NOT_CONFIRMED", failure or "MODULE_FINAL_OBSERVATION_REJECTED"
        try:
            audit = type(diagnostics).audit_module_return(diagnostics, scope, boundary="RETURN")
            if type(audit) is not ModuleReturnAuditObservation:
                status, failure = "NOT_CONFIRMED", failure or "MODULE_COMPLETION_MISSING"
            elif audit.status not in ("COMPLETE", "ALREADY_OBSERVED"):
                status, failure = "NOT_CONFIRMED", failure or audit.failure_code or "MODULE_REQUIRED_RECORD_MISSING"
        except Exception:
            status, failure = "NOT_CONFIRMED", failure or "MODULE_COMPLETION_MISSING"
    receipt = values.RealmTransitionCaptureReceipt(result.operation_reference, status, result,
                  tuple(confirmed), attempted, completion, final, failure)
    values.canonical_bytes(receipt)
    return receipt
