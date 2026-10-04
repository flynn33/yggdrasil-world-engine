"""Owned N1 reference normalization behavior and scoped capture [YWE-REQ-0040]."""

from __future__ import annotations

import re

from . import normalization_values as nv
from . import state_values as sv


_ORIGIN_RULES = (
    "ASH-STATE-STRUCTURE-001", "ASH-ADMISSIBILITY-CLASSIFICATION-001",
    "ASH-STATE-VALIDITY-001",
)
_COMPUTATION_RULES = _ORIGIN_RULES + ("ASH-CODEWORD-STRUCTURE-001",)
_SEMANTIC_FIELDS = (
    "input_state", "admissibility_status", "transformation_compatibility",
    "normalization_status", "recoverability_relevance", "is_valid", "orbit_info",
)
_SEVERITY = ("INFO", "WARNING", "ERROR", "CRITICAL")


def _diagnostic_impact(diagnostic):
    status = diagnostic.admissibility_status
    if status == "VALID":
        return "INFO", "RESOLVED"
    if status == "TRANSFORMATION_COMPATIBLE":
        return "WARNING", "PENDING"
    return "ERROR", "BLOCKED"


class RecordingNormalizationCapture:
    """Explicit reference adapter; each begin owns a separate bounded scope."""

    def begin(self, operation_reference, *, original_diagnosis):
        if type(original_diagnosis) is not sv.StateDiagnosis:
            raise nv.NormalizationContractError("NORMALIZATION_PLAN_INVALID", "original_diagnosis")
        return _RecordingNormalizationScope(operation_reference, original_diagnosis)


class _RecordingNormalizationScope:
    def __init__(self, operation_reference, original_diagnosis):
        self.operation_reference = operation_reference
        self._origin = original_diagnosis.emitted_diagnostics[0]
        self._records = []

    def append(self, record):
        if type(record) is not nv.NormalizationDiagnosticRecord:
            raise nv.NormalizationContractError("NORMALIZATION_PLAN_INVALID", "emission")
        emission = record.emission
        envelope = emission.envelope
        previous = self._origin if not self._records else self._records[-1].emission
        valid = (
            len(self._records) < 2 and
            record.phase == ("COMPUTATION" if not self._records else "POST_VALIDATION") and
            (envelope.disposition in ("PENDING", "BLOCKED") if not self._records else
             previous.envelope.disposition == "PENDING" and envelope.disposition in ("RESOLVED", "BLOCKED")) and
            envelope.parent_diagnostic_reference == previous.diagnostic_reference and
            envelope.chain_root_reference == self._origin.diagnostic_reference and
            envelope.subject_reference == self._origin.envelope.subject_reference and
            emission.diagnostic_reference != self._origin.diagnostic_reference and
            emission.diagnostic_reference != previous.diagnostic_reference and
            _SEVERITY.index(envelope.severity) >= _SEVERITY.index(previous.envelope.severity)
        )
        if not valid:
            return sv.CaptureReceipt(emission.diagnostic_reference, "REJECTED")
        self._records.append(record)
        return sv.CaptureReceipt(emission.diagnostic_reference, "CONFIRMED")


class _NormalizationOperations:
    """StateModel's private owner with immutable bindings and narrow collaborators."""

    def __init__(self, profile_binding, canonical_binding, diagnose_candidate, capture):
        self._profile = profile_binding
        self._canonical = canonical_binding
        self._diagnose_candidate = diagnose_candidate
        self._capture = capture

    def _witness(self, plan, diagnosis, origin, code=None, field=None, *, expected=None):
        decision, targets, target, chain = (None, None, None, None) if expected is None else expected[:4]
        return nv.NormalizationPlanValidation(
            plan=plan, original_diagnosis=diagnosis,
            canonical_binding=self._canonical, profile_binding=self._profile,
            origin_validation_status=origin,
            validation_status="VALIDATED" if code is None else "REJECTED",
            failure_code=code, field_name=field, expected_decision=decision,
            recomputed_eligible_targets=targets, recomputed_target=target,
            recomputed_codeword_chain=chain,
        )

    def _precondition(self, code, field, *, plan=None, diagnosis=None):
        if plan is not None:
            diagnosis = plan.original_diagnosis
        witness = None
        if type(diagnosis) is sv.StateDiagnosis:
            witness = self._witness(plan, diagnosis, "NOT_EVALUATED", code, field)
        raise nv.NormalizationContractError(code, field, submitted_plan=plan, validation=witness)

    def _reference(self, value, field, *, diagnosis=None):
        if (type(value) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}", value) is None
                or value in ("NONE", "SELF")):
            self._precondition("NORMALIZATION_PLAN_INVALID", field, diagnosis=diagnosis)

    def _policy(self, binding, *, plan=None, diagnosis=None):
        if type(binding) is not nv.NormalizationPolicyBinding:
            self._precondition("NORMALIZATION_POLICY_INVALID", "policy_binding", plan=plan, diagnosis=diagnosis)
        for field, expected in nv.NORMALIZATION_POLICY_BINDING_FIELDS:
            actual = getattr(binding, field)
            if type(actual) is not str or actual != expected:
                self._precondition("NORMALIZATION_POLICY_INVALID", "policy_binding." + field,
                                   plan=plan, diagnosis=diagnosis)

    def _origin_issue(self, diagnosis):
        if diagnosis.source_binding != self._canonical:
            return "NORMALIZATION_BINDING_MISMATCH", "original_diagnosis.source_binding"
        if diagnosis.profile_binding != self._profile:
            return "NORMALIZATION_BINDING_MISMATCH", "original_diagnosis.profile_binding"
        try:
            sv.StateDiagnosis.__post_init__(diagnosis)
        except sv.StateContractError as exc:
            owner = exc.field_name.split(".", 1)[0]
            if owner not in ("assessment_binding", "input_evidence", "parsed_state",
                             "state_validity_diagnostic", "emitted_diagnostics"):
                owner = "state_validity_diagnostic"
            return "NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH", "original_diagnosis." + owner
        diagnostic = diagnosis.state_validity_diagnostic
        expected = self._diagnose_candidate(diagnosis.parsed_state, diagnosis.input_evidence)
        if (any(getattr(diagnostic, field) != getattr(expected, field) for field in _SEMANTIC_FIELDS)
                or diagnostic.rule_ids != _ORIGIN_RULES):
            return "NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH", "original_diagnosis.state_validity_diagnostic"
        emission = diagnosis.emitted_diagnostics[0]
        envelope = emission.envelope
        severity, disposition = _diagnostic_impact(diagnostic)
        if (envelope.diagnostic_kind != "STATE_VALIDITY" or envelope.stage != "DETECTION"
                or emission.diagnostic_reference != diagnosis.assessment_binding.diagnosis_reference
                or envelope.chain_root_reference != emission.diagnostic_reference
                or envelope.parent_diagnostic_reference is not None
                or envelope.subject_reference != diagnosis.subject_reference
                or envelope.severity != severity or envelope.disposition != disposition
                or envelope.rule_ids != diagnostic.rule_ids or envelope.notes != diagnostic.notes):
            return "NORMALIZATION_ORIGINAL_DIAGNOSIS_MISMATCH", "original_diagnosis.emitted_diagnostics"
        return None

    @staticmethod
    def _apply_codeword(state, codeword):
        return sv.AshState(tuple(bit ^ code for bit, code in zip(state.bits, codeword.bits)))

    def _derive(self, diagnosis):
        state = diagnosis.parsed_state
        if state is None:
            return "BLOCKED", None, None, None, "NORMALIZATION_INPUT_REJECTED"
        if type(self._profile) is sv.UnavailableProfileBinding:
            return "BLOCKED", None, None, None, "NORMALIZATION_PROFILE_UNAVAILABLE"
        recognized = self._profile.profile.recognized_valid_states
        orbit = frozenset(sv.AshState(tuple(bit ^ code[index] for index, bit in enumerate(state.bits)))
                          for code in sv.CANONICAL_CODEWORDS)
        targets = tuple(sorted(recognized.intersection(orbit), key=lambda target: target.signature))
        if state in recognized:
            return "ALREADY_VALID", targets, state, (), "NORMALIZATION_ALREADY_VALID"
        if not targets:
            return "NOT_NORMALIZABLE", (), None, (), "NORMALIZATION_NO_TARGET"
        target = targets[0]
        codeword = sv.AshState(tuple(bit ^ target.bits[index] for index, bit in enumerate(state.bits)))
        return "PLAN_READY", targets, target, (codeword,), "NORMALIZATION_PLAN_READY"

    def plan(self, diagnosis, *, plan_reference, evidence_reference, policy_binding):
        if type(diagnosis) is not sv.StateDiagnosis:
            self._precondition("NORMALIZATION_PLAN_INVALID", "original_diagnosis")
        self._reference(plan_reference, "plan_reference", diagnosis=diagnosis)
        self._reference(evidence_reference, "evidence_reference", diagnosis=diagnosis)
        self._policy(policy_binding, diagnosis=diagnosis)
        issue = self._origin_issue(diagnosis)
        if issue is not None:
            witness = self._witness(None, diagnosis, "REJECTED", *issue)
            raise nv.NormalizationContractError("NORMALIZATION_PLAN_INVALID", issue[1], validation=witness)
        decision, targets, target, chain, reason = self._derive(diagnosis)
        return nv.NormalizationPlan(
            plan_reference=plan_reference, evidence_reference=evidence_reference,
            policy_binding=policy_binding, original_diagnosis=diagnosis, decision=decision,
            eligible_targets_complete=targets is not None, eligible_targets=() if targets is None else targets,
            selected_target=target, codeword_chain=() if chain is None else chain, reason_code=reason,
        )

    def validate(self, plan):
        if type(plan) is not nv.NormalizationPlan:
            self._precondition("NORMALIZATION_PLAN_INVALID", "plan")
        self._policy(plan.policy_binding, plan=plan)
        diagnosis = plan.original_diagnosis
        issue = self._origin_issue(diagnosis)
        if issue is not None:
            return self._witness(plan, diagnosis, "REJECTED", *issue)
        expected = self._derive(diagnosis)
        decision, targets, target, chain, reason = expected
        issue = None
        if plan.eligible_targets_complete != (targets is not None):
            issue = "NORMALIZATION_TARGET_SET_MISMATCH", "eligible_targets_complete"
        elif plan.eligible_targets != (() if targets is None else targets):
            issue = "NORMALIZATION_TARGET_SET_MISMATCH", "eligible_targets"
        elif plan.decision != decision:
            issue = "NORMALIZATION_SELECTION_MISMATCH", "decision"
        elif plan.reason_code != reason:
            issue = "NORMALIZATION_SELECTION_MISMATCH", "reason_code"
        elif plan.selected_target != target:
            issue = "NORMALIZATION_SELECTION_MISMATCH", "selected_target"
        elif plan.codeword_chain != (() if chain is None else chain):
            issue = "NORMALIZATION_CODEWORD_MISMATCH", "codeword_chain"
        return self._witness(plan, diagnosis, "VERIFIED", *(issue or (None, None)), expected=expected)

    def _record(self, plan, context, phase, diagnostic, step, disposition, summary, *, previous=None):
        origin = plan.original_diagnosis.emitted_diagnostics[0]
        severity = max((origin.envelope.severity, _diagnostic_impact(diagnostic)[0]), key=_SEVERITY.index)
        if previous is not None:
            severity = max((severity, previous.emission.envelope.severity), key=_SEVERITY.index)
        reference = context.computation_reference if phase == "COMPUTATION" else context.post_validation_reference
        parent = origin.diagnostic_reference if previous is None else previous.emission.diagnostic_reference
        return nv.NormalizationDiagnosticRecord(
            emission=sv.DiagnosticEmission(reference, sv.DiagnosticEnvelope(
                diagnostic_kind="STATE_VALIDITY", severity=severity, stage="RECOVERY",
                disposition=disposition, subject_reference=origin.envelope.subject_reference,
                parent_diagnostic_reference=parent, chain_root_reference=origin.diagnostic_reference,
                rule_ids=_ORIGIN_RULES if plan.decision == "BLOCKED" else _COMPUTATION_RULES,
                summary=summary, notes=diagnostic.notes,
            )), phase=phase, state_validity_diagnostic=diagnostic, step=step,
        )

    @staticmethod
    def _append(scope, record):
        try:
            receipt = scope.append(record)
        except Exception:
            return "NOT_CONFIRMED"
        if type(receipt) is not sv.CaptureReceipt or receipt.diagnostic_reference != record.emission.diagnostic_reference:
            return "NOT_CONFIRMED"
        return receipt.status

    @staticmethod
    def _capture_failure(common, attempted, status):
        return nv.NormalizationCaptureFailure(
            **common, failure_code="DIAGNOSTIC_CAPTURE_REJECTED" if status == "REJECTED" else "DIAGNOSTIC_CAPTURE_UNCONFIRMED",
            failed_field="normalization_capture", capture_status=status, attempted_diagnostic=attempted,
        )

    def apply(self, plan, *, normalization_context):
        if type(plan) is not nv.NormalizationPlan:
            self._precondition("NORMALIZATION_PLAN_INVALID", "plan")
        if type(normalization_context) is not nv.NormalizationContext:
            self._precondition("NORMALIZATION_CONTEXT_INVALID", "normalization_context", plan=plan)
        context = normalization_context
        root = plan.original_diagnosis.assessment_binding.diagnosis_reference
        for field in ("computation_reference", "post_validation_reference"):
            if getattr(context, field) == root:
                self._precondition("NORMALIZATION_CONTEXT_INVALID", field, plan=plan)
        try:
            begin = None if self._capture is None else getattr(self._capture, "begin", None)
        except Exception:
            begin = None
        if not callable(begin):
            self._precondition("NORMALIZATION_CONFIG_INVALID", "normalization_capture", plan=plan)
        validation = self.validate(plan)
        diagnosis = plan.original_diagnosis
        common = dict(
            operation_binding=context, plan=plan, plan_validation=validation,
            original_diagnosis=diagnosis, actual_state=diagnosis.parsed_state, steps=(),
            post_validity_diagnostic=None, normalized_state=None,
            inherited_diagnostics=(), emitted_diagnostics=(),
        )
        if validation.origin_validation_status != "VERIFIED":
            return nv.NormalizationFailure(
                **common, outcome="FAILURE", failure_kind="plan_validation",
                failure_code=validation.failure_code, failed_field=validation.field_name,
            )
        common["inherited_diagnostics"] = diagnosis.emitted_diagnostics
        blocked = self._record(plan, context, "COMPUTATION", diagnosis.state_validity_diagnostic,
                               None, "BLOCKED", "ASH normalization attempt blocked before value computation.")
        try:
            scope = begin(context.operation_reference, original_diagnosis=diagnosis)
            if scope is None or not callable(getattr(scope, "append", None)):
                return self._capture_failure(common, blocked, "NOT_CONFIRMED")
        except Exception:
            return self._capture_failure(common, blocked, "NOT_CONFIRMED")
        if validation.validation_status == "REJECTED" or plan.decision in ("NOT_NORMALIZABLE", "BLOCKED"):
            status = self._append(scope, blocked)
            if status != "CONFIRMED":
                return self._capture_failure(common, blocked, status)
            common["emitted_diagnostics"] = (blocked,)
            if validation.validation_status == "REJECTED":
                return nv.NormalizationFailure(
                    **common, outcome="FAILURE", failure_kind="plan_validation",
                    failure_code=validation.failure_code, failed_field=validation.field_name,
                )
            field = ("original_diagnosis.parsed_state" if plan.reason_code == "NORMALIZATION_INPUT_REJECTED" else
                     "original_diagnosis.profile_binding" if plan.reason_code == "NORMALIZATION_PROFILE_UNAVAILABLE" else
                     "selected_target")
            return nv.NormalizationFailure(**common, outcome=plan.decision, failure_kind="semantic",
                                           failure_code=plan.reason_code, failed_field=field)
        step = None
        actual = diagnosis.parsed_state
        if plan.decision == "PLAN_READY":
            actual = self._apply_codeword(actual, plan.codeword_chain[0])
            step = nv.NormalizationStep(0, diagnosis.parsed_state, plan.codeword_chain[0], actual)
            common["steps"] = (step,)
        common["actual_state"] = actual
        computation = self._record(plan, context, "COMPUTATION", diagnosis.state_validity_diagnostic,
                                   step, "PENDING", "ASH normalization value computation completed; validation is pending.")
        status = self._append(scope, computation)
        if status != "CONFIRMED":
            return self._capture_failure(common, computation, status)
        common["emitted_diagnostics"] = (computation,)
        post = self._diagnose_candidate(actual, diagnosis.input_evidence)
        common["post_validity_diagnostic"] = post
        succeeded = post.is_valid and post.input_state == actual and actual == plan.selected_target
        post_record = self._record(
            plan, context, "POST_VALIDATION", post, step, "RESOLVED" if succeeded else "BLOCKED",
            "ASH normalization actual result validated." if succeeded else "ASH normalization actual result failed validation.",
            previous=computation,
        )
        status = self._append(scope, post_record)
        if status != "CONFIRMED":
            return self._capture_failure(common, post_record, status)
        common["emitted_diagnostics"] = (computation, post_record)
        if not succeeded:
            return nv.NormalizationFailure(
                **common, outcome="FAILURE", failure_kind="post_validation",
                failure_code="NORMALIZATION_POST_VALIDATION_FAILED", failed_field="post_validity_diagnostic",
            )
        common["normalized_state"] = actual
        return nv.NormalizationResult(**common, outcome="ALREADY_VALID" if plan.decision == "ALREADY_VALID" else "NORMALIZED")
