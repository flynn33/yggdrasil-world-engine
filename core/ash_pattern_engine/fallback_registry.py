"""Pure, immutable-snapshot fallback selection [YWE-REQ-0041]."""
from __future__ import annotations

from . import recovery_values as values
from . import state_values as state
from .state_model import StateModel


class FallbackRegistry:
    """Validate declared known-good targets; select only observed applicability."""

    __slots__ = ("_snapshot", "_state_model", "_profile_binding", "_canonical_binding")

    def __init__(self, snapshot, *, state_model):
        values._exact(snapshot, (values.AvailableFallbackRegistry, values.UnavailableFallbackRegistry), "registry")
        values._exact(state_model, StateModel, "registry")
        self._snapshot = snapshot
        self._state_model = state_model
        self._profile_binding = state_model.profile_binding
        self._canonical_binding = state_model.canonical_binding
        validation = self.validate_for_model(state_model)
        if validation.status != "VERIFIED":
            raise values.RecoveryContractError("RECOVERY_BINDING_MISMATCH", validation.field_name, validation=validation)

    @property
    def snapshot(self):
        return self._snapshot

    @property
    def profile_binding(self):
        return self._profile_binding

    @property
    def canonical_binding(self):
        return self._canonical_binding

    def ordered_entries(self):
        if type(self.snapshot) is values.UnavailableFallbackRegistry:
            return ()
        return tuple(sorted(self.snapshot.entries, key=lambda entry: (entry.ordering_rank, entry.policy_id)))

    def validate_for_model(self, current_model):
        """Reinspect complete bindings, current mathematics and certifications."""
        values._exact(current_model, StateModel, "registry_validation")
        validations = []

        def witness(code=None, field=None, policy=None):
            return values.RegistryValidation(
                status="VERIFIED" if code is None else "REJECTED",
                submitted_snapshot=self.snapshot,
                current_source_binding=current_model.canonical_binding,
                current_profile_binding=current_model.profile_binding,
                candidate_validations=tuple(validations), failure_code=code,
                failed_policy_id=policy, field_name=field,
            )

        binding = self.snapshot.source_binding
        try:
            values._exact(binding, values.RegistrySourceBinding, "registry.source_binding")
            values.RegistrySourceBinding.__post_init__(binding)
            values.EvidenceSourceBinding.__post_init__(binding.source_binding)
        except values.RecoveryContractError as error:
            if error.field_name == "profile_binding":
                return witness("REGISTRY_PROFILE_MISMATCH", "profile_binding")
            return witness("REGISTRY_SOURCE_MISMATCH", "registry.source_binding")
        if (self.canonical_binding != current_model.canonical_binding or
                binding.ash_dependency_id != current_model.canonical_binding.dependency_id or
                binding.ash_aggregate_sha256 != current_model.canonical_binding.aggregate_sha256):
            return witness("REGISTRY_SOURCE_MISMATCH", "registry.source_binding")
        if (self.profile_binding != current_model.profile_binding or
                binding.profile_id != current_model.profile_binding.profile_id or
                binding.profile_source_sha256 != current_model.profile_binding.source_binding.source_sha256):
            return witness("REGISTRY_PROFILE_MISMATCH", "profile_binding")
        if type(self.snapshot) is values.UnavailableFallbackRegistry:
            return witness()
        if tuple(e.policy_id for e in self.snapshot.entries) != tuple(c.policy_id for c in self.snapshot.candidate_certifications):
            return witness("CERTIFICATION_INVENTORY_MISMATCH", "registry.candidate_certifications")
        for index, (entry, certification) in enumerate(zip(self.snapshot.entries, self.snapshot.candidate_certifications)):
            comparison = current_model.validate_assessment(certification.source_assessment)
            try:
                diagnostic = current_model.inspect_state(entry.candidate_state_reference)
            except state.StateContractError:
                diagnostic = None
            validations.append(values.RegistryTargetValidation(entry.policy_id, certification, comparison, diagnostic))
            if diagnostic is None or not diagnostic.is_valid:
                return witness("TARGET_NOT_VALID", f"registry.entries[{index}]", entry.policy_id)
            if (comparison.status != "VERIFIED" or certification.source_assessment.parsed_state != entry.candidate_state_reference or
                    certification.source_assessment.system_state_class != "STABLE" or
                    certification.context_observation.context != certification.source_assessment.system_context):
                return witness("CERTIFICATION_NOT_STABLE", f"registry.candidate_certifications[{index}]", entry.policy_id)
        return witness()

    def _origin(self, origin, classification):
        values._exact(origin, state.StateAssessment, "origin_assessment")
        comparison = self._state_model.validate_assessment(origin)
        if comparison.status != "VERIFIED":
            raise values.RecoveryContractError("RECOVERY_BINDING_MISMATCH", comparison.field_name, validation=comparison)
        if origin.system_state_class != classification:
            raise values.RecoveryContractError("RECOVERY_PLAN_INVALID", "origin_assessment")
        registry = self.validate_for_model(self._state_model)
        if registry.status != "VERIFIED":
            raise values.RecoveryContractError("RECOVERY_BINDING_MISMATCH", registry.field_name, validation=registry)

    def _select(self, origin, applicability):
        values._exact(applicability, tuple, "applicability")
        if len(applicability) > 32:
            values._fail("applicability")
        for observed in applicability:
            values._exact(observed, values.EntryApplicability, "applicability")
        ordered = self.ordered_entries()
        if tuple(observed.policy_id for observed in applicability) != tuple(entry.policy_id for entry in ordered):
            values._fail("applicability", "RECOVERY_BINDING_MISMATCH")
        candidates = []
        operation = None
        for entry, observed in zip(ordered, applicability):
            prefix = tuple(v.condition for v in observed.observations)
            expected = entry.applicability_conditions
            if prefix != expected[:len(prefix)] or observed.unconsulted_conditions != expected[len(prefix):]:
                values._fail("applicability", "RECOVERY_BINDING_MISMATCH")
            stopped = False
            for observation in observed.observations:
                if stopped:
                    values._fail("applicability")
                if (observation.origin_assessment_reference != origin.assessment_binding.assessment_reference or
                        observation.registry_id != self.snapshot.source_binding.registry_id or
                        observation.registry_source_sha256 != self.snapshot.source_binding.source_binding.source_sha256 or
                        observation.candidate_state_reference != entry.candidate_state_reference):
                    values._fail("predicate_observation", "RECOVERY_BINDING_MISMATCH")
                if operation is None:
                    operation = observation.operation_reference
                elif observation.operation_reference != operation:
                    values._fail("predicate_observation", "RECOVERY_BINDING_MISMATCH")
                if observation.status == "UNAVAILABLE":
                    values._fail("predicate_observation", "RECOVERY_PORT_INVALID")
                stopped = observation.status == "FALSE"
            if not stopped and observed.unconsulted_conditions:
                values._fail("applicability", "RECOVERY_PORT_INVALID")
            if not stopped:
                candidates.append(entry)
        return tuple(candidates)

    def get_candidates(self, origin, *, applicability):
        self._origin(origin, "DEGRADED")
        return self._select(origin, applicability)

    def _after_failure(self, origin, failed_action, authorization, failed_post_assessment, route):
        classification = "CORRECTABLE" if route == "AFTER_CORRECTION_FAILURE" else "UNSTABLE"
        self._origin(origin, classification)
        values._exact(failed_action, values.RecoveryActionDecision, "action_decisions")
        values._exact(authorization, values.FallbackRouteAuthorization, "route_authorization")
        action = "CORRECT" if classification == "CORRECTABLE" else "NORMALIZE"
        diagnostic = failed_action.diagnostic
        if (failed_action.action != action or authorization.route != route or
                authorization.origin_assessment_reference != origin.assessment_binding.assessment_reference or
                authorization.original_system_state_class != origin.system_state_class or
                authorization.failed_action_decision_reference != failed_action.action_reference or
                authorization.failed_outcome != diagnostic.outcome or
                diagnostic.original_state_class != origin.system_state_class or
                diagnostic.recovery_category != origin.recovery_category or
                diagnostic.original_diagnostic != origin.state_validity_diagnostic):
            values._fail("route_authorization", "RECOVERY_BINDING_MISMATCH")
        if classification == "CORRECTABLE" and authorization.origin_predicate_evidence_reference != origin.classification_evidence.correction_path_is_known.binding.evidence_reference:
            values._fail("route_authorization", "RECOVERY_BINDING_MISMATCH")
        if diagnostic.outcome == "BLOCKED":
            if classification != "CORRECTABLE" or failed_post_assessment is not None or failed_action.post_assessment_reference is not None:
                values._fail("post_assessment")
            return
        if diagnostic.outcome != "RECOVERY_FAILED":
            values._fail("route_authorization")
        values._exact(failed_post_assessment, values.LinkedPostAssessment, "post_assessment")
        post = failed_post_assessment
        if (post.capture_status != "COMPLETE" or type(post.assessment) is not state.StateAssessment or
                post.link.parent_action_reference != failed_action.action_reference or
                post.link.originating_chain_root_reference != origin.assessment_binding.diagnosis_reference or
                post.assessment.assessment_binding.assessment_reference != failed_action.post_assessment_reference or
                post.candidate_state != diagnostic.corrected_state or
                post.context_observation.context != failed_action.candidate_context):
            values._fail("post_assessment", "RECOVERY_BINDING_MISMATCH")
        comparison = self._state_model.validate_assessment(post.assessment)
        if comparison.status != "VERIFIED":
            raise values.RecoveryContractError("RECOVERY_BINDING_MISMATCH", comparison.field_name, validation=comparison)
        if post.assessment.system_state_class in ("CONTAINED", "SAFE_HALT"):
            values._fail("post_assessment.system_context", "RECOVERY_PLAN_INVALID")

    def get_candidates_after_correction_failure(self, origin, *, failed_action, authorization, applicability, failed_post_assessment=None):
        self._after_failure(origin, failed_action, authorization, failed_post_assessment, "AFTER_CORRECTION_FAILURE")
        return self._select(origin, applicability)

    def get_candidates_after_normalization_failure(self, origin, *, failed_action, failed_post_assessment, authorization, applicability):
        self._after_failure(origin, failed_action, authorization, failed_post_assessment, "AFTER_NORMALIZATION_FAILURE")
        return self._select(origin, applicability)
