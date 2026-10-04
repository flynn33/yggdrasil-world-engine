"""Actual immutable recovery execution under the adopted N2 contract [YWE-REQ-0041]."""

from __future__ import annotations

from dataclasses import replace

from . import normalization_values as nv
from . import recovery_values as rv
from . import state_values as sv
from .diagnostics_values import DiagnosticsCompletionReceipt, RecoveryAdmissionReceipt
from .fallback_registry import FallbackRegistry
from .state_model import StateModel


_SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")
_VALUE_RULES = (
    "ASH-STATE-STRUCTURE-001", "ASH-ADMISSIBILITY-CLASSIFICATION-001",
    "ASH-STATE-VALIDITY-001", "ASH-CODEWORD-STRUCTURE-001", "ASH-RECOVERY-ACTION-001",
)
_FALLBACK_RULES = ("ASH-STATE-VALIDITY-001", "ASH-RECOVERY-ACTION-001", "ASH-FALLBACK-SELECTION-001")
_BOUNDARY_RULES = ("ASH-STATE-GENERAL-001", "ASH-RECOVERY-ACTION-001")
_STEP_LITERALS = {
    "NORMALIZE_PLAN": "resolve-normalization", "NORMALIZE_XOR": "normalize",
    "CORRECTION_RESOLVE": "resolve-correction", "CORRECTION_XOR": "correct",
    "CANDIDATE_APPLICABILITY": "evaluate-applicability", "FALLBACK_SELECT": "select-fallback",
    "CANDIDATE_VALIDATION": "evaluate-additional-validation", "POST_ASSESSMENT": "validate-recovery",
    "HANDOFF": "handoff", "NO_ACTION": "no-action",
}


def _apply_codeword(before, codeword):
    return sv.AshState(tuple(a ^ b for a, b in zip(before.bits, codeword.bits)))


def _port(port, method, field):
    try:
        present = callable(getattr(port, method))
    except Exception:
        present = False
    if not present:
        raise rv.RecoveryContractError("RECOVERY_PORT_INVALID", field)


class ReferenceNormalizationResolutionProvider:
    """Resolve an actual current-model N1 proof with explicit provider provenance."""

    def __init__(self, state_model, source_binding):
        if type(state_model) is not StateModel or type(source_binding) is not rv.EvidenceSourceBinding:
            raise rv.RecoveryContractError("RECOVERY_PORT_INVALID", "normalization_resolver")
        self._model = state_model
        self._source = source_binding

    def resolve(self, origin, *, operation_context, policy_binding):
        diagnosis = self._model.diagnosis_from_assessment(origin)
        if type(diagnosis) is not sv.StateDiagnosis:
            raise rv.RecoveryContractError("RECOVERY_PLAN_INVALID", "origin_assessment", validation=diagnosis)
        operation = operation_context.operation_reference
        observation = rv.NormalizationResolutionObservation(
            availability="READY", operation_reference=operation,
            origin_assessment_reference=origin.assessment_binding.assessment_reference,
            source_binding=self._source, reason="Current StateModel supplied the complete normalization proof.",
        )
        plan = self._model.plan_normalization(
            diagnosis, plan_reference=operation + ":normalization-plan",
            evidence_reference=operation + ":normalization-evidence", policy_binding=policy_binding,
        )
        validation = self._model.validate_normalization_plan(plan)
        return rv.NormalizationPreparation(
            status="READY", original_diagnosis=diagnosis, policy_binding=policy_binding,
            plan=plan, plan_validation=validation, planning_error=None, resolution_observation=observation,
        )


class RecoveryEngine:
    """Own one reference operation at a time through explicit collaborators."""

    def __init__(self, state_model, registry, diagnostics, normalization_resolver,
                 correction_provider, condition_evaluator, post_facts_provider):
        if type(state_model) is not StateModel:
            raise rv.RecoveryContractError("RECOVERY_INPUT_INVALID", "origin_assessment")
        if type(registry) is not FallbackRegistry:
            raise rv.RecoveryContractError("RECOVERY_INPUT_INVALID", "registry")
        for method in ("recovery_capture", "assessment_capture", "complete_assessment"):
            _port(diagnostics, method, "capture")
        for port, method, field in (
            (normalization_resolver, "resolve", "normalization_resolver"),
            (correction_provider, "resolve", "correction_provider"),
            (condition_evaluator, "evaluate", "condition_evaluator"),
            (post_facts_provider, "provide", "post_facts_provider"),
        ):
            _port(port, method, field)
        self._model = state_model
        self._registry = registry
        self._diagnostics = diagnostics
        self._normalization = normalization_resolver
        self._correction = correction_provider
        self._conditions = condition_evaluator
        self._post_facts = post_facts_provider
        self._source = rv.RecoverySourceBinding(
            canonical_binding=state_model.canonical_binding,
            contract_pins=tuple(rv.SourcePin(path, digest) for path, digest in rv.RECOVERY_CONTRACT_PIN_FIELDS),
        )

    def recover(self, origin, *, operation_context):
        validation = self._model.validate_assessment(origin)
        if type(operation_context) is not rv.RecoveryOperationContext:
            raise rv.RecoveryContractError("RECOVERY_INPUT_INVALID", "operation_context")
        rv.RecoveryOperationContext.__post_init__(operation_context)
        if (operation_context.origin_assessment_reference != origin.assessment_binding.assessment_reference or
                operation_context.context_observation.context != origin.system_context):
            raise rv.RecoveryContractError("RECOVERY_BINDING_MISMATCH", "operation_context")
        operation = _RecoveryOperation(self, origin, validation, operation_context)
        return operation.run()


class _Abort(Exception):
    def __init__(self, detail):
        self.detail = detail


class _RecoveryOperation:
    def __init__(self, engine, origin, validation, context):
        self.engine, self.origin, self.validation, self.context = engine, origin, validation, context
        self.steps, self.posts, self.attempts, self.actions, self.emissions = [], [], [], [], []
        self.candidate = self.directive = self.normalization = self.correction = None
        self.registry_binding = self.registry_snapshot = self.registry_validation = self.authorization = None
        self.scope = None
        self.denial = validation.status == "VERIFIED" and origin.system_state_class == "SAFE_HALT"
        self.previous = self.root = self.severity = None
        if validation.status == "VERIFIED":
            self.previous = origin.emitted_diagnostics[-1].diagnostic_reference
            self.root = origin.assessment_binding.diagnosis_reference
            self.severity = max((record.envelope.severity for record in origin.emitted_diagnostics), key=_SEVERITIES.index)

    def _packet(self, kind, detail=None, completion=None):
        return kind(
            operation_context=self.context, origin_assessment=self.origin, origin_validation=self.validation,
            source_binding=self.engine._source, registry_binding=self.registry_binding,
            route_authorization=self.authorization, steps=tuple(self.steps), post_assessments=tuple(self.posts),
            policy_attempts=tuple(self.attempts), action_decisions=tuple(self.actions),
            emitted_diagnostics=tuple(self.emissions), candidate_state=self.candidate,
            directive=self.directive, failure_detail=detail, normalization_preparation=self.normalization,
            correction_observation=self.correction, registry_snapshot=self.registry_snapshot,
            registry_validation=self.registry_validation, completion_observation=completion,
        )

    def _failure(self, code, field, reason, *, submitted=None, attempted=None, status=None):
        return rv.RecoveryFailureDetail(
            failure_code=code, field_name=field, submitted_evidence=submitted,
            attempted_diagnostic=attempted, capture_status=status, pending_directive=self.directive,
            reason=reason, completion_failure_code=None, unconfirmed_completion_observation=None,
        )

    def _abort(self, code, field, reason, **kwargs):
        raise _Abort(self._failure(code, field, reason, **kwargs))

    def _emit(self, record, *, decision=False):
        try:
            receipt = self.scope.append(record)
        except Exception:
            receipt = None
        status = (receipt.status if type(receipt) is sv.CaptureReceipt and
                  receipt.diagnostic_reference == record.diagnostic_reference else "NOT_CONFIRMED")
        if status != "CONFIRMED":
            self._abort("STEP_CAPTURE" + ("_REJECTED" if status == "REJECTED" else "_UNCONFIRMED"),
                "capture.append", "The actual recovery record was not confirmed.",
                attempted=record, status="REJECTED" if status == "REJECTED" else "NOT_CONFIRMED")
        self.emissions.append(record)
        self.previous = record.diagnostic_reference

    def _record(self, reference, payload, kind, *, fallback=False, disposition="PENDING", denial=False):
        rules = _FALLBACK_RULES if fallback else _VALUE_RULES
        if type(payload) is rv.RecoveryActionDecision:
            rules = payload.diagnostic.rule_ids
        if denial:
            envelope = sv.DiagnosticEnvelope(
                "STATE_VALIDITY", "CRITICAL", "DETECTION", "BLOCKED", self.origin.subject_reference,
                None, reference, _BOUNDARY_RULES, "Recovery request denied at an observed safe-halt boundary.",
                ("This is a separate reference denial audit; no mode or session effect was performed.",),
            )
        else:
            envelope = sv.DiagnosticEnvelope(
                "FALLBACK" if fallback else "RECOVERY", self.severity,
                "ESCALATION" if disposition == "ESCALATED" else "RECOVERY", disposition,
                self.origin.subject_reference, self.previous, self.root, rules,
                "Actual immutable recovery observation.",
                ("Actual values and explicit evidence are retained; session effects are not performed.",),
            )
        return rv.RecoveryRecord(reference, envelope, kind, payload)

    def _step(self, action, reason, *, status="COMPLETED", before=None, codeword=None,
              after=None, policy=None, predicate=None, post=None, fallback=False):
        index = len(self.steps)
        if index >= 768:
            self._abort("RESOURCE_LIMIT", "action_decisions", "The admitted step bound was reached.")
        reference = self.context.operation_reference + f":step:{index:03d}"
        step = rv.RecoveryStepEvidence(index, action, status, before, codeword, after,
            policy, predicate, post, reference, reason)
        self.steps.append(step)
        self._emit(self._record(reference, step, "ACTION_VALUE_COMPUTED", fallback=fallback))
        return step

    def _action_reference(self):
        return self.context.operation_reference + f":action:{len(self.actions):03d}"

    def _decision(self, action, outcome, reason, indices=(), *, policy=None, post=None,
                  candidate=None, candidate_context=None, fallback=False, disposition=None, summary=False):
        if len(self.actions) >= 35:
            self._abort("RESOURCE_LIMIT", "action_decisions", "The admitted action bound was reached.")
        reference = self._action_reference()
        if summary:
            local_steps = tuple(rv.RecoveryStep("fallback-summary", "COMPLETED",
                "The completed policy attempt is retained with its detailed evidence.") for _ in self.attempts)
        else:
            local_steps = tuple(rv.RecoveryStep(
                "validate-fallback" if fallback and self.steps[i].action == "POST_ASSESSMENT" else
                _STEP_LITERALS[self.steps[i].action], self.steps[i].status, self.steps[i].reason,
            ) for i in indices)
        rules = _BOUNDARY_RULES if action in ("NO_ACTION", "HANDOFF") else _FALLBACK_RULES if fallback else _VALUE_RULES
        diagnostic = rv.RecoveryDiagnostic(
            recovery_category=self.origin.recovery_category, original_state_class=self.origin.system_state_class,
            original_diagnostic=self.origin.state_validity_diagnostic, steps=local_steps, outcome=outcome,
            corrected_state=candidate, fallback_policy_id=policy, reason=reason, rule_ids=rules,
        )
        decision = rv.RecoveryActionDecision(reference, action, diagnostic, tuple(indices), post,
            candidate_context, self.directive if action == "HANDOFF" else None)
        self.actions.append(decision)
        if disposition is None:
            disposition = ("RESOLVED" if outcome in ("RECOVERED", "RECOVERED_VIA_FALLBACK", "NOT_APPLICABLE")
                           else "ESCALATED" if action == "HANDOFF" else "BLOCKED")
        record_reference = self.context.operation_reference + ":denied" if self.denial else reference
        self._emit(self._record(record_reference, decision, "OPERATION_DECISION", fallback=fallback,
            disposition=disposition, denial=self.denial), decision=True)
        return decision

    def _registry(self):
        registry = self.engine._registry
        self.registry_snapshot = registry.snapshot
        self.registry_binding = self.registry_snapshot.source_binding
        self.registry_validation = registry.validate_for_model(self.engine._model)
        if self.registry_validation.status != "VERIFIED":
            self._abort("REGISTRY_BINDING_REJECTED", "registry_validation",
                "The complete registry binding or candidate certification was rejected.", submitted=self.registry_validation)

    def _admit(self):
        try:
            capture = self.engine._diagnostics.recovery_capture()
            method = capture.begin_denial if self.denial else capture.begin
            result = method(self.origin, operation_reference=self.context.operation_reference)
        except Exception:
            result = None
        scope = receipt = None
        if type(result) is tuple and len(result) == 2:
            scope, receipt = result
        matching = (type(receipt) is RecoveryAdmissionReceipt and
            receipt.operation_reference == self.context.operation_reference and
            receipt.origin_assessment_reference == self.origin.assessment_binding.assessment_reference and
            receipt.origin_diagnostic_references == tuple(v.diagnostic_reference for v in self.origin.emitted_diagnostics))
        reserved = (matching and receipt.reserved_events == (1 if self.denial else 768) and
                    receipt.reserved_bytes == (270336 if self.denial else 31588352))
        if reserved and receipt.status == "CONFIRMED" and scope is not None:
            try:
                _port(scope, "append", "capture.append")
                _port(scope, "finish", "capture.finish")
            except rv.RecoveryContractError:
                matching = False
            else:
                self.scope = scope
                return
        status = "REJECTED" if matching and receipt.status == "REJECTED" else "NOT_CONFIRMED"
        self._abort("CAPTURE_ADMISSION_REJECTED" if status == "REJECTED" else "CAPTURE_ADMISSION_UNCONFIRMED",
            "capture.admission", "Recovery admission was not confirmed before collaborator or value effects.", status=status)

    def _finish(self, result):
        try:
            receipt = self.scope.finish(result)
        except Exception:
            receipt = None
        exact = type(receipt) is DiagnosticsCompletionReceipt
        matching = exact and receipt.operation_reference == self.context.operation_reference
        if matching and receipt.status == "COMPLETE":
            return replace(result, completion_observation=receipt)
        code = "COMPLETION_REJECTED" if matching and receipt.status == "INCOMPLETE" else "COMPLETION_UNCONFIRMED"
        detail = result.failure_detail if type(result) is rv.RecoveryFailure else self._failure(
            code, "capture.finish", "The actual result did not receive a matching complete observation.",
            submitted=receipt if matching else None,
        )
        detail = replace(detail, completion_failure_code=code,
            unconfirmed_completion_observation=receipt if exact and not matching else None)
        fields = {field: getattr(result, field) for field in (
            "operation_context", "origin_assessment", "origin_validation", "source_binding", "registry_binding",
            "route_authorization", "steps", "post_assessments", "policy_attempts", "action_decisions",
            "emitted_diagnostics", "candidate_state", "directive", "normalization_preparation",
            "correction_observation", "registry_snapshot", "registry_validation",
        )}
        return rv.RecoveryFailure(**fields, failure_detail=detail, completion_observation=receipt if matching else None)

    def _handoff(self, action, trigger, reason, *, request_origin="SOURCE_RECOVERABILITY",
                 evidence=(), policy=False, fallback=False):
        self.directive = rv.RecoveryDirective(
            requested_action=action, trigger=trigger,
            origin_assessment_reference=self.origin.assessment_binding.assessment_reference,
            causing_decision_reference=self._action_reference(), evidence_references=tuple(evidence) or
            (self.context.context_observation.observation_reference,), reason=reason,
            request_origin=request_origin, policy_binding=rv.RecoverySafetyPolicyBinding(**dict(rv.RECOVERY_POLICY_BINDING_FIELDS)) if policy else None,
        )
        self._decision("HANDOFF", "ESCALATE_TO_CONTAINMENT" if action == "ENTER_CONTAINMENT" else "NOT_APPLICABLE",
            reason, fallback=fallback, candidate=self.candidate,
            disposition="BLOCKED" if self.denial else "ESCALATED")
        return self._packet(rv.RecoveryHandoff)

    def _post(self, candidate, action_reference, *, fallback=False, policy=None):
        ordinal = len(self.posts)
        if ordinal >= 33:
            self._abort("RESOURCE_LIMIT", "post_assessment", "The admitted child-assessment bound was reached.")
        stem = self.context.operation_reference + f":post:{ordinal:03d}"
        context = sv.DiagnosticContext(stem + ":assessment", stem + ":input", stem + ":detection", stem + ":classification")
        try:
            facts = self.engine._post_facts.provide(candidate, origin=self.origin,
                action_reference=action_reference, diagnostic_context=context, operation_context=self.context)
        except Exception:
            facts = None
        if type(facts) is rv.UnavailablePostAssessmentFacts:
            if facts.operation_reference != self.context.operation_reference or facts.candidate_state_reference != candidate:
                self._abort("COLLABORATOR_FAILED", "post_facts_provider", "The unavailable observation had a mismatched binding.", submitted=facts)
            self._abort("POST_EVIDENCE_UNAVAILABLE", "post_assessment", "Fresh postassessment facts are explicitly unavailable.", submitted=facts)
        if type(facts) is not rv.PostAssessmentFacts or facts.diagnostic_context != context:
            self._abort("COLLABORATOR_FAILED", "post_facts_provider", "The provider did not supply the exact fresh assessment context.",
                submitted=facts if type(facts) is rv.PostAssessmentFacts else None)
        profile = self.engine._model.profile_binding
        canonical = self.engine._model.canonical_binding
        for name in sv.PREDICATE_NAMES:
            binding = getattr(facts.classification_evidence, name).binding
            if (binding.assessment_reference != context.assessment_reference or binding.diagnosis_reference != context.detection_reference or
                    binding.subject_reference != "ash_state_" + candidate.signature or binding.profile_id != profile.profile_id or
                    binding.profile_source_sha256 != profile.source_binding.source_sha256 or
                    binding.ash_dependency_id != canonical.dependency_id or binding.ash_aggregate_sha256 != canonical.aggregate_sha256):
                self._abort("COLLABORATOR_FAILED", "post_assessment.classification_evidence",
                    "The supplied predicate binding does not describe this fresh candidate assessment.", submitted=facts)
        link = rv.PostAssessmentLink(self.context.operation_reference, action_reference, self.root)
        try:
            capture = self.engine._diagnostics.assessment_capture(relation=link)
            child = StateModel(profile, canonical, capture)
            assessed = child.assess(candidate, context=facts.context_observation.context,
                classification_evidence=facts.classification_evidence, diagnostic_context=context)
        except Exception:
            self._abort("COLLABORATOR_FAILED", "post_assessment", "Actual child assessment could not produce an owned result.", submitted=facts)
        if not any(type(assessed) is kind for kind in (sv.StateAssessment, sv.ClassificationEvidenceFailure, sv.DiagnosticCaptureFailure)):
            self._abort("INTERNAL_INVARIANT_FAILURE", "post_assessment", "The actual model returned an inadmissible child type.")
        try:
            receipt = self.engine._diagnostics.complete_assessment(assessed)
        except Exception:
            receipt = None
        completion_confirmed = (type(receipt) is DiagnosticsCompletionReceipt and
            receipt.operation_reference == context.assessment_reference and receipt.status == "COMPLETE")
        complete = type(assessed) is sv.StateAssessment and completion_confirmed
        capture_status = ("COMPLETE" if completion_confirmed and type(assessed) is not sv.DiagnosticCaptureFailure else "REJECTED" if
            (type(assessed) is sv.DiagnosticCaptureFailure and assessed.capture_status == "REJECTED") or
            (type(receipt) is DiagnosticsCompletionReceipt and receipt.operation_reference == context.assessment_reference and receipt.status == "INCOMPLETE")
            else "NOT_CONFIRMED")
        linked = rv.LinkedPostAssessment(link, candidate, facts.context_observation, assessed, capture_status)
        self.posts.append(linked)
        if not complete:
            code = ("POST_ASSESSMENT_FAILED" if type(assessed) is sv.ClassificationEvidenceFailure else
                    "POST_CAPTURE_REJECTED" if capture_status == "REJECTED" else "POST_CAPTURE_UNCONFIRMED")
            self._abort(code, "post_assessment", "Actual child assessment or its completion was not confirmed.", submitted=facts,
                status=None if capture_status == "COMPLETE" else "REJECTED" if capture_status == "REJECTED" else "NOT_CONFIRMED")
        validation = self.engine._model.validate_assessment(assessed)
        if validation.status != "VERIFIED" or assessed.parsed_state != candidate:
            self._abort("INTERNAL_INVARIANT_FAILURE", "post_assessment", "The actual child result failed current-model validation.", submitted=validation)
        self.severity = max((self.severity, assessed.emitted_diagnostics[-1].envelope.severity), key=_SEVERITIES.index)
        self._step("POST_ASSESSMENT", "The actual complete fresh contextual postassessment is retained.",
            before=candidate, after=candidate, policy=policy, post=context.assessment_reference, fallback=fallback)
        return linked

    def _post_boundary(self, post, *, fallback=False):
        classification = post.assessment.system_state_class
        if classification in ("CONTAINED", "SAFE_HALT"):
            return self._handoff("REMAIN_CONTAINED" if classification == "CONTAINED" else "REMAIN_SAFE_HALT",
                rv.ExistingModeBoundary(classification, post.assessment.assessment_binding.assessment_reference),
                "The fresh postassessment reports an existing lifecycle boundary.",
                request_origin="OBSERVED_EXISTING_MODE", evidence=(post.context_observation.observation_reference,), fallback=fallback)
        return None

    def _normalize(self):
        start = len(self.steps)
        policy = nv.NormalizationPolicyBinding(**dict(nv.NORMALIZATION_POLICY_BINDING_FIELDS))
        try:
            preparation = self.engine._normalization.resolve(self.origin, operation_context=self.context, policy_binding=policy)
        except Exception:
            preparation = None
        if type(preparation) is not rv.NormalizationPreparation:
            self._abort("COLLABORATOR_FAILED", "normalization_resolver", "Normalization resolution returned no owned observation.")
        self.normalization = preparation
        observation = preparation.resolution_observation
        diagnosis = self.engine._model.diagnosis_from_assessment(self.origin)
        if (preparation.original_diagnosis != diagnosis or preparation.policy_binding != policy or
                observation.operation_reference != self.context.operation_reference or
                observation.origin_assessment_reference != self.origin.assessment_binding.assessment_reference):
            self._abort("COLLABORATOR_FAILED", "normalization_preparation", "Normalization resolution does not bind this exact origin and operation.", submitted=preparation)
        if preparation.status == "UNAVAILABLE" and observation.availability == "UNAVAILABLE":
            self._step("NORMALIZE_PLAN", "Normalization resolution is explicitly unavailable.", status="BLOCKED")
            self._decision("NORMALIZE", "BLOCKED", "The explicit normalization resolution is unavailable.", range(start, len(self.steps)))
            return self._handoff("ENTER_CONTAINMENT", "OPERATOR_REQUEST", "NORMALIZATION_PATH_NOT_COMPUTABLE",
                request_origin="POLICY", evidence=(observation.source_binding.evidence_reference,), policy=True)
        if preparation.status != "READY" or observation.availability != "READY" or type(preparation.plan) is not nv.NormalizationPlan:
            self._abort("COLLABORATOR_FAILED", "normalization_preparation", "The resolver did not supply a complete ready proof.", submitted=preparation)
        actual_validation = self.engine._model.validate_normalization_plan(preparation.plan)
        self.normalization = replace(preparation, plan_validation=actual_validation)
        plan = preparation.plan
        if actual_validation.validation_status != "VALIDATED" or actual_validation.origin_validation_status != "VERIFIED" or plan.decision != "PLAN_READY":
            self._abort("COLLABORATOR_FAILED", "normalization_preparation.plan_validation", "The supplied normalization proof was rejected at use.", submitted=self.normalization)
        self._step("NORMALIZE_PLAN", "The complete current-model normalization proof was resolved.")
        self.candidate = self.origin.parsed_state
        for codeword in plan.codeword_chain:
            before = self.candidate
            self.candidate = _apply_codeword(before, codeword)
            self._step("NORMALIZE_XOR", "Actual full-vector normalization XOR was computed.", before=before, codeword=codeword, after=self.candidate)
        post = self._post(self.candidate, self._action_reference())
        stable = post.assessment.system_state_class == "STABLE" and post.assessment.state_validity_diagnostic.is_valid and self.candidate == plan.selected_target
        decision = self._decision("NORMALIZE", "RECOVERED" if stable else "RECOVERY_FAILED",
            "The actual normalization target received its complete postassessment.", range(start, len(self.steps)),
            candidate=self.candidate, post=post.assessment.assessment_binding.assessment_reference,
            candidate_context=post.assessment.system_context)
        boundary = self._post_boundary(post)
        if boundary is not None:
            return boundary
        if stable:
            return self._packet(rv.RecoveredValue)
        return self._fallback(decision, post)

    def _correct(self):
        start = len(self.steps)
        try:
            correction = self.engine._correction.resolve(self.origin, operation_context=self.context)
        except Exception:
            correction = None
        if type(correction) is not rv.KnownCorrection and type(correction) is not rv.UnavailableCorrection:
            self._abort("COLLABORATOR_FAILED", "correction_provider", "The correction provider returned no exact owned observation.")
        if (correction.original_assessment_reference != self.origin.assessment_binding.assessment_reference or
                correction.classification_evidence_reference != self.origin.classification_evidence.correction_path_is_known.binding.evidence_reference):
            self._abort("COLLABORATOR_FAILED", "correction_observation.submitted", "The correction provider observation does not bind the original known-path fact.")
        validation = self.engine._model.validate_known_correction(correction, origin=self.origin) if type(correction) is rv.KnownCorrection else None
        self.correction = rv.CorrectionObservation(correction, validation)
        ready = validation is not None and validation.status == "VERIFIED"
        self._step("CORRECTION_RESOLVE", "The supplied correction observation and actual validation are retained.",
            status="COMPLETED" if ready else "BLOCKED")
        if not ready:
            decision = self._decision("CORRECT", "BLOCKED", "The supplied known correction cannot be applied.", range(start, len(self.steps)))
            return self._fallback(decision, None)
        self.candidate = self.origin.parsed_state
        for codeword in correction.chain:
            before = self.candidate
            self.candidate = _apply_codeword(before, codeword)
            self._step("CORRECTION_XOR", "Actual supplied full-vector codeword XOR was computed.", before=before, codeword=codeword, after=self.candidate)
        post = self._post(self.candidate, self._action_reference())
        stable = post.assessment.system_state_class == "STABLE" and post.assessment.state_validity_diagnostic.is_valid and self.candidate == correction.expected_target
        decision = self._decision("CORRECT", "RECOVERED" if stable else "RECOVERY_FAILED",
            "The actual supplied correction received a complete fresh postassessment.", range(start, len(self.steps)),
            candidate=self.candidate, post=post.assessment.assessment_binding.assessment_reference,
            candidate_context=post.assessment.system_context)
        boundary = self._post_boundary(post)
        if boundary is not None:
            return boundary
        return self._packet(rv.RecoveredValue) if stable else self._fallback(decision, post)

    def _predicate(self, condition, entry, phase):
        try:
            observation = self.engine._conditions.evaluate(condition, origin=self.origin, entry=entry,
                phase=phase, operation_context=self.context)
        except Exception:
            observation = None
        binding = self.registry_binding
        if type(observation) is not rv.PredicateObservation:
            self._abort("COLLABORATOR_FAILED", "condition_evaluator", "The condition evaluator returned no owned observation.")
        if (observation.condition != condition or observation.operation_reference != self.context.operation_reference or
                observation.origin_assessment_reference != self.origin.assessment_binding.assessment_reference or
                observation.registry_id != binding.registry_id or observation.registry_source_sha256 != binding.source_binding.source_sha256 or
                observation.policy_id != entry.policy_id or observation.phase != phase or
                observation.candidate_state_reference != entry.candidate_state_reference):
            self._abort("COLLABORATOR_FAILED", "predicate_observation", "The predicate observation has a mismatched condition, candidate or source binding.", submitted=observation)
        self._step("CANDIDATE_APPLICABILITY" if phase == "APPLICABILITY" else "CANDIDATE_VALIDATION",
            "The actual bound condition observation is retained.",
            status="FAILED" if observation.status == "UNAVAILABLE" else "COMPLETED",
            policy=entry.policy_id, predicate=observation, fallback=True)
        if observation.status == "UNAVAILABLE":
            self._abort("COLLABORATOR_FAILED", "predicate_observation", "The condition is explicitly unavailable and cannot be treated as false.", submitted=observation)
        return observation

    def _fallback(self, failed_action=None, failed_post=None):
        if self.registry_validation is None:
            self._registry()
        route = ("DIRECT_DEGRADED" if failed_action is None else "AFTER_CORRECTION_FAILURE" if
                 failed_action.action == "CORRECT" else "AFTER_NORMALIZATION_FAILURE")
        fact = (self.origin.classification_evidence.fallback_is_available if failed_action is None else
                self.origin.classification_evidence.correction_path_is_known if route == "AFTER_CORRECTION_FAILURE" else None)
        self.authorization = rv.FallbackRouteAuthorization(
            route=route, original_system_state_class=self.origin.system_state_class,
            origin_assessment_reference=self.origin.assessment_binding.assessment_reference,
            failed_action_decision_reference=None if failed_action is None else failed_action.action_reference,
            failed_outcome=None if failed_action is None else failed_action.diagnostic.outcome,
            rule_ids=("ASH-RECOVERY-ACTION-001", "ASH-FALLBACK-SELECTION-001"),
            origin_predicate_evidence_reference=None if fact is None else fact.binding.evidence_reference,
        )
        if type(self.registry_snapshot) is rv.UnavailableFallbackRegistry:
            return self._fallback_exhausted("The registry is explicitly unavailable.")
        entries = self.engine._registry.ordered_entries()
        inventory, ranges = [], {}
        for entry in entries:
            start = len(self.steps)
            observations = []
            for condition in entry.applicability_conditions:
                observations.append(self._predicate(condition, entry, "APPLICABILITY"))
                if observations[-1].status == "FALSE":
                    break
            remaining = entry.applicability_conditions[len(observations):]
            applicability = rv.EntryApplicability(entry.policy_id, tuple(observations), remaining)
            inventory.append(applicability)
            ranges[entry.policy_id] = tuple(range(start, len(self.steps)))
            if observations and observations[-1].status == "FALSE":
                decision = self._decision("FALLBACK_CANDIDATE", "BLOCKED", "This registry entry is ineligible under its actual applicability observations.",
                    ranges[entry.policy_id], policy=entry.policy_id, fallback=True, disposition="PENDING")
                self.attempts.append(rv.PolicyAttempt(entry.policy_id, tuple(observations), remaining,
                    (), entry.validation_requirements, None, decision.action_reference, "INELIGIBLE"))
        kwargs = dict(applicability=tuple(inventory))
        if failed_action is None:
            candidates = self.engine._registry.get_candidates(self.origin, **kwargs)
        elif route == "AFTER_CORRECTION_FAILURE":
            candidates = self.engine._registry.get_candidates_after_correction_failure(self.origin,
                failed_action=failed_action, authorization=self.authorization, failed_post_assessment=failed_post, **kwargs)
        else:
            candidates = self.engine._registry.get_candidates_after_normalization_failure(self.origin,
                failed_action=failed_action, failed_post_assessment=failed_post, authorization=self.authorization, **kwargs)
        for entry in candidates:
            applicability = next(item for item in inventory if item.policy_id == entry.policy_id)
            start = len(self.steps)
            before = self.candidate if self.candidate is not None else self.origin.parsed_state
            self.candidate = entry.candidate_state_reference
            self._step("FALLBACK_SELECT", "The actual eligible canonical registry target was selected.",
                before=before, after=self.candidate, policy=entry.policy_id, fallback=True)
            post = self._post(self.candidate, self._action_reference(), fallback=True, policy=entry.policy_id)
            observations = []
            stable = post.assessment.system_state_class == "STABLE" and post.assessment.state_validity_diagnostic.is_valid
            if stable:
                for condition in entry.validation_requirements:
                    observations.append(self._predicate(condition, entry, "ADDITIONAL_VALIDATION"))
                    if observations[-1].status == "FALSE":
                        break
            recovered = stable and all(item.status == "TRUE" for item in observations)
            indices = ranges[entry.policy_id] + tuple(range(start, len(self.steps)))
            decision = self._decision("FALLBACK_CANDIDATE", "RECOVERED_VIA_FALLBACK" if recovered else "RECOVERY_FAILED",
                "The actual candidate postassessment and additional validation are retained.", indices,
                policy=entry.policy_id, post=post.assessment.assessment_binding.assessment_reference,
                candidate=self.candidate, candidate_context=post.assessment.system_context, fallback=True)
            lifecycle = post.assessment.system_state_class in ("CONTAINED", "SAFE_HALT")
            self.attempts.append(rv.PolicyAttempt(entry.policy_id, applicability.observations, applicability.unconsulted_conditions,
                tuple(observations), entry.validation_requirements[len(observations):],
                post.assessment.assessment_binding.assessment_reference, decision.action_reference,
                "LIFECYCLE_BOUNDARY" if lifecycle else "RECOVERED" if recovered else "VALIDATION_FAILED"))
            boundary = self._post_boundary(post, fallback=True)
            if boundary is not None:
                return boundary
            if recovered:
                self._summary("RECOVERED_VIA_FALLBACK", "The selected registry target passed complete actual validation.", policy=entry.policy_id)
                return self._packet(rv.RecoveredFallbackValue)
            if entry.escalation_on_failure == "ESCALATE_TO_CONTAINMENT":
                return self._fallback_exhausted("The failed candidate's entry directs containment.")
        return self._fallback_exhausted("No registry candidate passed complete actual fallback validation.")

    def _summary(self, outcome, reason, *, policy=None):
        indices = tuple(sorted({index for decision in self.actions if decision.action == "FALLBACK_CANDIDATE"
                                for index in decision.step_indices}))
        return self._decision("FALLBACK_SUMMARY", outcome, reason, indices, policy=policy,
            candidate=self.candidate, fallback=True, summary=True)

    def _fallback_exhausted(self, reason):
        self._summary("BLOCKED", reason)
        return self._handoff("ENTER_CONTAINMENT", "FALLBACK_FAILURE", reason, fallback=True,
            evidence=(self.registry_binding.source_binding.evidence_reference,))

    def run(self):
        try:
            if self.validation.status != "VERIFIED":
                self._abort("ORIGIN_REJECTED", "origin_validation", "The complete current-model origin verification was rejected.", submitted=self.validation)
            classification = self.origin.system_state_class
            if classification == "DEGRADED" and self.context.propagation_evidence.status == "SAFE":
                self._registry()
            self._admit()
            if classification == "STABLE":
                self.candidate = self.origin.parsed_state
                self._decision("NO_ACTION", "NOT_APPLICABLE", "The verified original is already stable.", candidate=self.candidate)
                result = self._packet(rv.RecoveryNoAction)
            elif classification in ("CONTAINED", "SAFE_HALT"):
                result = self._handoff("REMAIN_CONTAINED" if classification == "CONTAINED" else "REMAIN_SAFE_HALT",
                    rv.ExistingModeBoundary(classification, self.origin.assessment_binding.assessment_reference),
                    "The original assessment reports an existing lifecycle boundary.", request_origin="OBSERVED_EXISTING_MODE")
            elif classification == "FAILED":
                authority = self.context.external_authority_evidence
                result = self._handoff("ENTER_SAFE_HALT" if authority.status == "UNREACHABLE" else "REQUEST_EXTERNAL_AUTHORITY",
                    "ESCALATION_FROM_FAILED" if authority.status == "UNREACHABLE" else rv.ExternalEscalationRequired(authority.status),
                    "The explicit failed-state authority observation determines the requested handoff.",
                    evidence=(authority.source_binding.evidence_reference,))
            elif self.context.propagation_evidence.status != "SAFE":
                evidence = self.context.propagation_evidence
                missing = evidence.status == "UNAVAILABLE"
                result = self._handoff("ENTER_CONTAINMENT", "OPERATOR_REQUEST" if missing else "PROPAGATION_RISK",
                    "Propagation safety is explicitly unavailable." if missing else "Propagation risk is explicitly reported.",
                    request_origin="POLICY" if missing else "SOURCE_RECOVERABILITY",
                    evidence=(evidence.source_binding.evidence_reference,), policy=missing)
            elif classification == "UNSTABLE":
                result = self._normalize()
            elif classification == "CORRECTABLE":
                result = self._correct()
            else:
                result = self._fallback()
        except _Abort as exc:
            result = self._packet(rv.RecoveryFailure, exc.detail)
        except rv.RecoveryContractError as exc:
            result = self._packet(rv.RecoveryFailure, self._failure("INTERNAL_INVARIANT_FAILURE", exc.field_name,
                "An owned contract rejected the actual operation observation.", submitted=exc.validation))
        return self._finish(result) if self.scope is not None else result
