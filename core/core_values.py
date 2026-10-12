"""Immutable neutral Core values and closed serialization (YWE-REQ-0051)."""
from __future__ import annotations
from dataclasses import dataclass, fields
import hashlib
import importlib
import json
import re
from .ash_pattern_engine import state_values as state
from .ash_pattern_engine import realm_transition_values as rt
from .ash_pattern_engine import normalization_values as nv

Q6 = 1_000_000
MAX_RAW_CORE_BYTES = 1_048_576
MAX_DIAGNOSTIC_BYTES = 8_192
CORE_POLICY_ID = 'ywe_core_reference_q6_v1'
CORE_POLICY_SHA256 = '74dfa3b318cd38296c0b86ad9ff5c14e8fb1d7aed5ff1c02274baa4bbd871e91'

class CoreContractError(ValueError):
    def __init__(self, code, field_name):
        if type(code) is not str or type(field_name) is not str or not 1 <= len(field_name) <= 128:
            raise ValueError('Invalid Core contract error fields')
        if code not in DOMAINS['CORE_FAILURE']:
            raise ValueError('Invalid Core contract error code')
        self.code, self.field_name = code, field_name
        super().__init__(code + ': ' + field_name)

def _fail(field='value', code='CORE_VALUE_INVALID'):
    raise CoreContractError(code, field)

def _one_of(kind, classes):
    return any(kind is item for item in classes)

class _WireValue:
    __slots__ = ()
    def __post_init__(self):
        _walk(self, set(), normalize=True)
    def to_record(self):
        return json.loads(canonical_bytes(self))
    def canonical_bytes(self):
        return canonical_bytes(self)

class _IssuedValue(_WireValue):
    __slots__ = ('_core_result_cookie',)

CANONICAL_FIELDS = (('dependency_id', 'ash_cosmological_model.f2_9.canonical'), ('aggregate_sha256', '2371f71e570b4e193f5fc3e3e210816b06640204582dbb17046f78ae1d5efcc8'), ('state_space_sha256', '68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e'), ('codeword_source_sha256', '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c'), ('validity_source_sha256', '20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e'), ('classification_source_sha256', '806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff'), ('recovery_source_sha256', 'cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd'), ('diagnostic_source_sha256', '1b0f05c94e8136c536f5bcf156e2299782476e77c1e648db93dcea2c70e1f5fa'), ('taxonomy_source_sha256', '7eb9e39ac860439e674c3596d5e1cd705915d4de4a98a674786117919caa1196'))
DOMAINS = {'COORDINATE': ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8'], 'CODEWORD_ID': ['ash_codeword_00', 'ash_codeword_01', 'ash_codeword_02', 'ash_codeword_03', 'ash_codeword_04', 'ash_codeword_05', 'ash_codeword_06', 'ash_codeword_07', 'ash_codeword_08', 'ash_codeword_09', 'ash_codeword_10', 'ash_codeword_11', 'ash_codeword_12', 'ash_codeword_13', 'ash_codeword_14', 'ash_codeword_15'], 'FAMILY': ['character', 'quest', 'region', 'faction', 'transformation', 'event', 'cluster'], 'TRUTH_TIER': ['OBJECTIVE_SHARED', 'OBJECTIVE_BRANCH', 'OBJECTIVE_PLAYER', 'DERIVED_INTERPRETATION'], 'CORE_STATUS': ['COMPLETED', 'REFUSED', 'PENDING', 'NO_OP'], 'CORE_EFFECT': ['NONE', 'PROPOSED_ONLY', 'KNOWN_COMPLETE', 'KNOWN_PARTIAL', 'UNKNOWN'], 'CORE_OWNER': ['COSMOLOGY', 'REALM', 'ASH_FACADE', 'NARRATIVE', 'PERCEPTION', 'DETERMINISTIC_POLICY', 'ORCHESTRATION'], 'CORE_RULE': ['BINDING', 'PROVENANCE', 'REALM_ACCESS', 'PATTERN_PROJECTION', 'ARCHETYPE_SCORE', 'RELATION_CONFLICT', 'CLUSTER_BASIS', 'TRUTH_PRECEDENCE', 'VISIBILITY', 'NORMALIZATION', 'SELECTION', 'BIAS_MERGE', 'BIAS_DECAY', 'EXISTENCE', 'CAPABILITY', 'RESOURCE_LIMIT', 'LIFECYCLE', 'STAGE_GATE'], 'ARCHETYPE_ROLE': ['DOMINANT', 'SECONDARY', 'SUPPRESSED', 'INELIGIBLE'], 'LIFECYCLE_PHASE': ['STOPPED', 'STARTING', 'ACTIVE', 'STOPPING', 'FAILED'], 'LIFECYCLE_COMPLETION': ['COMPLETED', 'REFUSED', 'PENDING', 'INTERRUPTED'], 'PROPHECY_STATUS': ['DORMANT', 'ACTIVE', 'FULFILLED', 'BROKEN'], 'OBSERVED_BOOL': ['TRUE', 'FALSE', 'UNAVAILABLE'], 'CLUSTER_STABILITY': ['STABLE', 'CYCLICAL', 'THRESHOLD_BASED', 'UNSTABLE'], 'RELATION': ['CONTRADICTION', 'FRICTION', 'COMPATIBILITY', 'NEUTRAL'], 'LIFECYCLE_ACTION': ['START', 'STOP'], 'CORE_FAILURE': ['CORE_VALUE_INVALID', 'CORE_BINDING_MISMATCH', 'CORE_PROFILE_CONFLICT', 'CORE_PROVENANCE_MISSING', 'CORE_UNKNOWN_REFERENCE', 'CORE_FACT_CONFLICT', 'CORE_CAPABILITY_UNAVAILABLE', 'CORE_RESOURCE_LIMIT', 'CORE_LIFECYCLE_REJECTED', 'CORE_STAGE_REVOKED', 'CORE_NO_POSITIVE_WEIGHT', 'CORE_SELECTION_EXHAUSTED', 'CORE_EPOCH_REVERSED', 'CORE_NUMERIC_OVERFLOW'], 'CORE_FIELD': ['accepted_draw', 'accepted_risk_refs', 'access', 'action', 'activated', 'activated_clusters', 'actual_codeword_trace', 'actual_effect_status', 'admitted_generation', 'affinity_refs', 'after', 'allowed_origins', 'allowed_tension_pairs', 'archetype_context', 'archetype_id', 'archetypes', 'attractor', 'attunement_q6', 'authority_tier', 'base_score_q6', 'baseline', 'before', 'before_realm_id', 'before_ref', 'binding', 'binding_sha256', 'canonical_binding', 'closed', 'cluster_id', 'cluster_scores', 'clusters', 'codeword_ids', 'coefficient_c', 'coefficient_h', 'coefficient_p', 'coefficient_s', 'coexistence_allowed', 'compatible_with', 'compressibility_q6', 'condition_fact_refs', 'condition_refs', 'context', 'context_ref', 'context_sha256', 'contradiction_refs', 'contradiction_risk_ref', 'contradicts', 'contribution_q6', 'coordinate', 'cosmic_pattern_snapshot_ref', 'cosmology', 'counters_used', 'dark_q6', 'declared_subject', 'deflection_routes', 'destination_identity', 'destination_interpretation_ref', 'destination_signature', 'diagnostic_ref', 'diagnostics', 'display_name', 'domain', 'dominant', 'downstream_affinities', 'effect_id', 'effect_status', 'eligible', 'entity_ref', 'entity_refs', 'entropy_q6', 'evaluated_rules', 'evaluation_ref', 'evaluation_sha256', 'event_id', 'events', 'evidence_ref', 'evidence_refs', 'evidence_status', 'explanation', 'fact_id', 'fact_refs', 'facts', 'failure_code', 'family', 'field', 'final_score_q6', 'first_id', 'fixed_script', 'friction_with', 'generation', 'generation_plan_ref', 'generation_run', 'hidden_entities', 'higher_order_pairs', 'inflight', 'inputs', 'interpretation_ref', 'interpretation_tags', 'lawful_basis_refs', 'ledger_used', 'location_ref', 'logical_epoch', 'manifestation_hint_refs', 'matched', 'member_ids', 'membership_mask', 'module_id', 'myth_refs', 'narrative', 'normalization', 'normalization_completion', 'normalization_result', 'normalization_step', 'normalized_origin', 'normalized_origin_completion', 'objective_effects', 'observations', 'observed_symbol_refs', 'operation_reference', 'option_id', 'options', 'origin', 'original_signature', 'overlay_ref', 'owner', 'pattern', 'pattern_id', 'perception', 'perception_request', 'persistence_q6', 'phase', 'plan', 'player_phase', 'player_phase_bias', 'policy_id', 'policy_sha256', 'potential_q6', 'pressure_tags', 'primary_source', 'priority', 'profile_binding', 'profile_realms', 'prophecy_id', 'prophecy_refs', 'proposal_ref', 'proposed', 'provenance', 'qualifying_members', 'realm_access', 'realm_bias', 'realm_id', 'realm_pressure', 'realm_request', 'realm_shift', 'reasons', 'recurrence_count', 'recurrence_refs', 'registry_id', 'registry_ref', 'registry_sha256', 'relation', 'relationship_source', 'relationships', 'request', 'request_ref', 'requested_domain', 'result_ref', 'route_id', 'rule', 'rule_id', 'rules', 'satisfied_basis_refs', 'scope_ref', 'score_delta_q6', 'score_q6', 'scores', 'second_id', 'secondary', 'seed_token', 'selected_id', 'selected_role', 'shadow_tags', 'snapshot_ref', 'snapshot_sha256', 'source_ash_refs', 'source_identity', 'source_realm_id', 'source_ref', 'source_sha256', 'source_signature', 'stability', 'stability_bonus_q6', 'state_id', 'state_ref', 'state_signature', 'status', 'strength_q6', 'structural_coordinates', 'subject_ref', 'support_penalty_q6', 'suppressed_by', 'suppressed_id', 'symbol_ref', 'symbolic_tags', 'symmetry_q6', 'tags', 'target_constraints', 'target_domain', 'target_id', 'target_realm_id', 'target_reference', 'term', 'terms', 'thin_veil', 'threshold_q6', 'total_q6', 'transmutation_routes', 'truth', 'truth_input', 'truth_sha256', 'truth_tags', 'value', 'value_token', 'veil_required', 'visible', 'visible_entities', 'weight', 'weight_q6', 'weights', 'white_q6', 'wolf_bias', 'wolf_pressure']}
FIELD_DOMAINS = {'CoreBinding': {'canonical_binding': 'CanonicalAshBinding', 'profile_binding': 'ProfileBinding', 'policy_id': 'ID', 'policy_sha256': 'HASH', 'profile_realms': 'ProfileRealmDefinition[0..64]'}, 'ProfileRealmDefinition': {'realm_id': 'ID', 'coordinate': '0..8', 'state_signature': 'SIGNATURE?', 'display_name': 'TEXT', 'threshold_q6': 'Q6', 'veil_required': 'bool', 'allowed_origins': 'ID[0..64]'}, 'CosmicState': {'binding': 'CoreBinding', 'baseline': 'StateDiagnosis', 'structural_coordinates': 'COORDINATE[9]'}, 'CoreProvenance': {'cosmic_pattern_snapshot_ref': 'REF', 'diagnostic_ref': 'REF', 'generation_plan_ref': 'REF', 'source_ash_refs': 'REF[1..65]'}, 'DeclaredTruthFact': {'fact_id': 'ID', 'authority_tier': 'TRUTH_TIER', 'scope_ref': 'REF', 'subject_ref': 'REF', 'value_token': 'TEXT', 'evidence_refs': 'REF[1..65]'}, 'TruthInputSnapshot': {'snapshot_ref': 'REF', 'scope_ref': 'REF', 'facts': 'DeclaredTruthFact[0..256]', 'entity_refs': 'REF[0..256]', 'evidence_status': 'DECLARED_INPUT'}, 'AttunementFact': {'realm_id': 'ID', 'attunement_q6': 'Q6', 'thin_veil': 'OBSERVED_BOOL', 'evidence_refs': 'REF[1..65]'}, 'RealmAccessRequest': {'request_ref': 'REF', 'source_realm_id': 'ID', 'target_realm_id': 'ID', 'location_ref': 'REF', 'facts': 'AttunementFact[0..64]'}, 'RealmAccessResult': {'request': 'RealmAccessRequest', 'eligible': 'bool?', 'evaluated_rules': 'CoreDiagnostic[1..32]'}, 'RealmShiftProposal': {'proposal_ref': 'REF', 'access': 'RealmAccessResult', 'before_realm_id': 'ID', 'target_realm_id': 'ID', 'effect_status': 'PROPOSED_ONLY'}, 'PatternProjectionRule': {'pattern_id': 'ID', 'membership_mask': 'MASK512', 'codeword_ids': 'CODEWORD_ID[0..16]', 'strength_q6': 'Q6', 'tags': 'ID[0..64]', 'evidence_refs': 'REF[1..65]'}, 'PatternObservation': {'pattern_id': 'ID', 'matched': 'bool', 'strength_q6': 'Q6', 'actual_codeword_trace': 'CODEWORD_ID[0..5]', 'evidence_refs': 'REF[1..65]'}, 'CosmicPatternSnapshot': {'snapshot_ref': 'REF', 'binding': 'CoreBinding', 'original_signature': 'SIGNATURE?', 'source_signature': 'SIGNATURE', 'source_identity': 'RealmIdentity', 'destination_signature': 'SIGNATURE', 'destination_identity': 'RealmIdentity', 'normalization_step': 'NormalizationStep?', 'observations': 'PatternObservation[0..64]', 'actual_codeword_trace': 'CODEWORD_ID[0..5]', 'provenance': 'CoreProvenance'}, 'ArchetypeRecord': {'archetype_id': 'ID', 'family': 'FAMILY', 'symbolic_tags': 'ID[0..64]', 'truth_tags': 'ID[0..64]', 'shadow_tags': 'ID[0..64]', 'realm_bias': 'ID[0..64]', 'wolf_bias': 'WolfBias?', 'player_phase_bias': 'ID[0..64]', 'compatible_with': 'ID[0..64]', 'friction_with': 'ID[0..64]', 'contradicts': 'ID[0..64]', 'downstream_affinities': 'ArchetypeAffinity[0..6]', 'manifestation_hint_refs': 'REF[0..64]', 'evidence_refs': 'REF[1..65]'}, 'ArchetypeContext': {'context_ref': 'REF', 'symbolic_tags': 'ID[0..64]', 'truth_tags': 'ID[0..64]', 'shadow_tags': 'ID[0..64]', 'realm_pressure': 'WeightedOption[0..64]', 'wolf_pressure': 'WolfPressure?', 'player_phase': 'ID?', 'recurrence_refs': 'REF[0..64]', 'myth_refs': 'REF[0..64]', 'prophecy_refs': 'REF[0..64]', 'requested_domain': 'ID?', 'allowed_tension_pairs': 'ID[0..256]', 'higher_order_pairs': 'ID[0..256]', 'satisfied_basis_refs': 'REF[0..16]', 'accepted_risk_refs': 'REF[0..16]'}, 'ArchetypeScore': {'archetype_id': 'ID', 'score_q6': 'SIGNED63', 'selected_role': 'ARCHETYPE_ROLE', 'suppressed_by': 'ID?', 'reasons': 'ID[0..32]'}, 'ArchetypeEvaluation': {'evaluation_ref': 'REF', 'snapshot_ref': 'REF', 'snapshot_sha256': 'HASH', 'context_ref': 'REF', 'context_sha256': 'HASH', 'registry_ref': 'REF', 'registry_sha256': 'HASH', 'scores': 'ArchetypeScore[0..64]', 'relationships': 'RelationObservation[0..256]', 'cluster_scores': 'ClusterScore[0..16]', 'dominant': 'ID[0..64]', 'secondary': 'ID[0..64]', 'activated_clusters': 'ID[0..16]'}, 'NarrativeInterpretation': {'interpretation_ref': 'REF', 'evaluation_ref': 'REF', 'evaluation_sha256': 'HASH', 'scope_ref': 'REF', 'fact_refs': 'REF[0..256]', 'pressure_tags': 'ID[0..64]', 'contradiction_refs': 'REF[0..256]', 'provenance': 'CoreProvenance'}, 'PerceptionRule': {'rule_id': 'ID', 'priority': 'SIGNED32', 'subject_ref': 'REF', 'entity_ref': 'REF', 'condition_fact_refs': 'REF[0..64]', 'visible': 'bool', 'interpretation_tags': 'ID[0..64]'}, 'PerceptionRequest': {'request_ref': 'REF', 'subject_ref': 'REF', 'truth': 'TruthInputSnapshot', 'rules': 'PerceptionRule[0..256]', 'provenance': 'CoreProvenance'}, 'PerceptionOverlay': {'overlay_ref': 'REF', 'request': 'PerceptionRequest', 'truth_sha256': 'HASH', 'evaluated_rules': 'CoreDiagnostic[0..256]', 'visible_entities': 'REF[0..256]', 'hidden_entities': 'REF[0..256]', 'tags': 'ID[0..64]', 'contradiction_refs': 'REF[0..256]', 'objective_effects': 'NONE'}, 'WeightedOption': {'option_id': 'ID', 'weight': '0..1000000'}, 'WeightedAllocation': {'options': 'WeightedOption[0..64]', 'total_q6': '0..1000000'}, 'SelectionRequest': {'domain': 'ID', 'binding_sha256': 'HASH', 'context_sha256': 'HASH', 'seed_token': 'SEED', 'options': 'WeightedOption[0..64]'}, 'SelectionResult': {'request': 'SelectionRequest', 'selected_id': 'ID?', 'counters_used': '0..16', 'accepted_draw': 'UINT64?'}, 'BiasTerm': {'event_id': 'ID', 'domain': 'ID', 'target_id': 'ID', 'contribution_q6': 'SIGNED_Q6', 'evidence_refs': 'REF[1..65]'}, 'BiasState': {'state_ref': 'REF', 'logical_epoch': 'UINT64', 'events': 'BiasEvent[0..512]', 'weights': 'WeightedOption[0..64]'}, 'BiasUpdateResult': {'before': 'BiasState', 'proposed': 'BiasState', 'effect_status': 'PROPOSED_ONLY'}, 'ExistentialMetricInputs': {'context_ref': 'REF', 'compressibility_q6': 'Q6', 'symmetry_q6': 'Q6', 'persistence_q6': 'Q6', 'entropy_q6': 'Q6', 'coefficient_c': 'Q6', 'coefficient_s': 'Q6', 'coefficient_p': 'Q6', 'coefficient_h': 'Q6', 'evidence_refs': 'REF[1..65]'}, 'ExistenceMeasure': {'inputs': 'ExistentialMetricInputs', 'potential_q6': 'SIGNED63'}, 'CoreDiagnostic': {'diagnostic_ref': 'REF', 'owner': 'CORE_OWNER', 'rule': 'CORE_RULE', 'status': 'CORE_STATUS', 'failure_code': 'CORE_FAILURE?', 'field': 'CORE_FIELD?', 'evidence_refs': 'REF[0..65]', 'explanation': 'TEXT'}, 'CoreResult': {'operation_reference': 'ID', 'binding': 'CoreBinding', 'status': 'CORE_STATUS', 'value': 'CORE_OUTPUT?', 'diagnostics': 'CoreDiagnostic[1..32]', 'effect_status': 'CORE_EFFECT'}, 'ModuleStatus': {'module_id': 'CORE_OWNER', 'generation': 'UINT64', 'phase': 'LIFECYCLE_PHASE', 'closed': 'bool', 'inflight': '0..8', 'ledger_used': '0..64'}, 'ModuleCompletion': {'request_ref': 'REF', 'admitted_generation': 'UINT64', 'status': 'LIFECYCLE_COMPLETION', 'result_ref': 'REF?', 'actual_effect_status': 'CORE_EFFECT'}, 'ProphecyRoute': {'route_id': 'ID', 'condition_refs': 'REF[1..64]', 'destination_interpretation_ref': 'REF'}, 'ProphecyAttractor': {'target_domain': 'ID', 'target_reference': 'REF', 'weight_q6': 'Q6'}, 'ProphecyRecord': {'prophecy_id': 'ID', 'provenance': 'CoreProvenance', 'attractor': 'ProphecyAttractor', 'fixed_script': 'FALSE', 'deflection_routes': 'ProphecyRoute[0..16]', 'transmutation_routes': 'ProphecyRoute[0..16]', 'status': 'PROPHECY_STATUS', 'condition_refs': 'REF[1..64]'}, 'OmenCluster': {'cluster_id': 'ID', 'prophecy_refs': 'REF[2..16]', 'observed_symbol_refs': 'REF[1..64]', 'provenance': 'CoreProvenance'}, 'RuntimeBiasEffect': {'effect_id': 'ID', 'before_ref': 'REF', 'term': 'BiasTerm', 'effect_status': 'PROPOSED_ONLY', 'provenance': 'CoreProvenance'}, 'RecurringSymbolState': {'state_id': 'ID', 'symbol_ref': 'REF', 'recurrence_count': 'UINT64', 'logical_epoch': 'UINT64', 'provenance': 'CoreProvenance'}, 'RegistrySource': {'source_ref': 'REF', 'source_sha256': 'HASH', 'evidence_ref': 'REF'}, 'WolfPressure': {'white_q6': 'Q6', 'dark_q6': 'Q6', 'evidence_refs': 'REF[1..65]'}, 'WolfBias': {'white_q6': 'SIGNED_Q6', 'dark_q6': 'SIGNED_Q6'}, 'ArchetypeAffinity': {'domain': 'ID', 'affinity_refs': 'REF[0..64]'}, 'ClusterRecord': {'cluster_id': 'ID', 'member_ids': 'ID[2..16]', 'lawful_basis_refs': 'REF[1..16]', 'stability': 'CLUSTER_STABILITY', 'contradiction_risk_ref': 'REF'}, 'ArchetypeRegistry': {'registry_id': 'ID', 'primary_source': 'RegistrySource', 'relationship_source': 'RegistrySource', 'archetypes': 'ArchetypeRecord[0..64]', 'clusters': 'ClusterRecord[0..16]'}, 'RelationObservation': {'first_id': 'ID', 'second_id': 'ID', 'relation': 'RELATION', 'score_delta_q6': 'SIGNED_Q6', 'coexistence_allowed': 'bool', 'suppressed_id': 'ID?'}, 'ClusterScore': {'cluster_id': 'ID', 'qualifying_members': 'ID[0..16]', 'base_score_q6': 'SIGNED63', 'stability_bonus_q6': 'SIGNED_Q6', 'support_penalty_q6': 'SIGNED_Q6', 'final_score_q6': 'SIGNED63', 'activated': 'bool', 'reasons': 'ID[0..32]'}, 'BiasEvent': {'event_id': 'ID', 'terms': 'BiasTerm[1..64]', 'evidence_refs': 'REF[1..65]'}, 'ModuleLifecycleReceipt': {'operation_reference': 'ID', 'action': 'LIFECYCLE_ACTION', 'before': 'ModuleStatus', 'after': 'ModuleStatus', 'status': 'LIFECYCLE_COMPLETION', 'failure_code': 'CORE_FAILURE?'}, 'CoreOrchestrationRequest': {'operation_reference': 'ID', 'inputs': 'GenerationInputs', 'origin': 'StateDiagnosis', 'normalization': 'CoreNormalizationRequest?', 'declared_subject': 'AxiomSubject', 'target_constraints': 'TargetConstraints', 'realm_request': 'RealmAccessRequest?', 'archetype_context': 'ArchetypeContext?', 'truth_input': 'TruthInputSnapshot?', 'perception_request': 'PerceptionRequest?'}, 'CoreOrchestrationResult': {'request': 'CoreOrchestrationRequest', 'binding': 'CoreBinding', 'normalization_result': 'NormalizationPacket?', 'normalization_completion': 'DiagnosticsCompletionReceipt?', 'normalized_origin': 'StateDiagnosis?', 'normalized_origin_completion': 'DiagnosticsCompletionReceipt?', 'generation_run': 'GenerationRunReceipt?', 'cosmology': 'CoreResult?', 'realm_access': 'CoreResult?', 'realm_shift': 'CoreResult?', 'pattern': 'CoreResult?', 'archetypes': 'CoreResult?', 'narrative': 'CoreResult?', 'perception': 'CoreResult?', 'status': 'CORE_STATUS', 'diagnostics': 'CoreDiagnostic[1..32]'}, 'CoreNormalizationRequest': {'plan': 'NormalizationPlan', 'context': 'NormalizationContext'}}
UNIQUE_FIELDS = {'CoreBinding': [], 'ProfileRealmDefinition': [], 'CosmicState': [], 'CoreProvenance': [], 'DeclaredTruthFact': [], 'TruthInputSnapshot': [], 'AttunementFact': [], 'RealmAccessRequest': [], 'RealmAccessResult': [], 'RealmShiftProposal': [], 'PatternProjectionRule': [], 'PatternObservation': [], 'CosmicPatternSnapshot': [], 'ArchetypeRecord': [], 'ArchetypeContext': [], 'ArchetypeScore': [], 'ArchetypeEvaluation': [], 'NarrativeInterpretation': [], 'PerceptionRule': [], 'PerceptionRequest': [], 'PerceptionOverlay': [], 'WeightedOption': [], 'WeightedAllocation': [], 'SelectionRequest': [], 'SelectionResult': [], 'BiasTerm': [], 'BiasState': [], 'BiasUpdateResult': [], 'ExistentialMetricInputs': [], 'ExistenceMeasure': [], 'CoreDiagnostic': [], 'CoreResult': [], 'ModuleStatus': [], 'ModuleCompletion': [], 'ProphecyRoute': [], 'ProphecyAttractor': [], 'ProphecyRecord': [], 'OmenCluster': [], 'RuntimeBiasEffect': [], 'RecurringSymbolState': [], 'RegistrySource': [], 'WolfPressure': [], 'WolfBias': [], 'ArchetypeAffinity': [], 'ClusterRecord': [], 'ArchetypeRegistry': [], 'RelationObservation': [], 'ClusterScore': [], 'BiasEvent': [], 'ModuleLifecycleReceipt': [], 'CoreOrchestrationRequest': [], 'CoreOrchestrationResult': [], 'CoreNormalizationRequest': []}

@dataclass(frozen=True, slots=True)
class CoreBinding(_WireValue):
    canonical_binding: object
    profile_binding: object
    policy_id: str
    policy_sha256: str
    profile_realms: object

@dataclass(frozen=True, slots=True)
class ProfileRealmDefinition(_WireValue):
    realm_id: str
    coordinate: int
    state_signature: object
    display_name: str
    threshold_q6: int
    veil_required: bool
    allowed_origins: object

@dataclass(frozen=True, slots=True)
class CosmicState(_WireValue):
    binding: object
    baseline: object
    structural_coordinates: object

@dataclass(frozen=True, slots=True)
class CoreProvenance(_WireValue):
    cosmic_pattern_snapshot_ref: str
    diagnostic_ref: str
    generation_plan_ref: str
    source_ash_refs: object

@dataclass(frozen=True, slots=True)
class DeclaredTruthFact(_WireValue):
    fact_id: str
    authority_tier: str
    scope_ref: str
    subject_ref: str
    value_token: str
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class TruthInputSnapshot(_WireValue):
    snapshot_ref: str
    scope_ref: str
    facts: object
    entity_refs: object
    evidence_status: object

@dataclass(frozen=True, slots=True)
class AttunementFact(_WireValue):
    realm_id: str
    attunement_q6: int
    thin_veil: str
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class RealmAccessRequest(_WireValue):
    request_ref: str
    source_realm_id: str
    target_realm_id: str
    location_ref: str
    facts: object

@dataclass(frozen=True, slots=True)
class RealmAccessResult(_WireValue):
    request: object
    eligible: object
    evaluated_rules: object

@dataclass(frozen=True, slots=True)
class RealmShiftProposal(_WireValue):
    proposal_ref: str
    access: object
    before_realm_id: str
    target_realm_id: str
    effect_status: object

@dataclass(frozen=True, slots=True)
class PatternProjectionRule(_WireValue):
    pattern_id: str
    membership_mask: str
    codeword_ids: object
    strength_q6: int
    tags: object
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class PatternObservation(_WireValue):
    pattern_id: str
    matched: bool
    strength_q6: int
    actual_codeword_trace: object
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class CosmicPatternSnapshot(_WireValue):
    snapshot_ref: str
    binding: object
    original_signature: object
    source_signature: str
    source_identity: object
    destination_signature: str
    destination_identity: object
    normalization_step: object
    observations: object
    actual_codeword_trace: object
    provenance: object

@dataclass(frozen=True, slots=True)
class ArchetypeRecord(_WireValue):
    archetype_id: str
    family: str
    symbolic_tags: object
    truth_tags: object
    shadow_tags: object
    realm_bias: object
    wolf_bias: object
    player_phase_bias: object
    compatible_with: object
    friction_with: object
    contradicts: object
    downstream_affinities: object
    manifestation_hint_refs: object
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class ArchetypeContext(_WireValue):
    context_ref: str
    symbolic_tags: object
    truth_tags: object
    shadow_tags: object
    realm_pressure: object
    wolf_pressure: object
    player_phase: object
    recurrence_refs: object
    myth_refs: object
    prophecy_refs: object
    requested_domain: object
    allowed_tension_pairs: object
    higher_order_pairs: object
    satisfied_basis_refs: object
    accepted_risk_refs: object

@dataclass(frozen=True, slots=True)
class ArchetypeScore(_WireValue):
    archetype_id: str
    score_q6: int
    selected_role: str
    suppressed_by: object
    reasons: object

@dataclass(frozen=True, slots=True)
class ArchetypeEvaluation(_IssuedValue):
    evaluation_ref: str
    snapshot_ref: str
    snapshot_sha256: str
    context_ref: str
    context_sha256: str
    registry_ref: str
    registry_sha256: str
    scores: object
    relationships: object
    cluster_scores: object
    dominant: object
    secondary: object
    activated_clusters: object

@dataclass(frozen=True, slots=True)
class NarrativeInterpretation(_WireValue):
    interpretation_ref: str
    evaluation_ref: str
    evaluation_sha256: str
    scope_ref: str
    fact_refs: object
    pressure_tags: object
    contradiction_refs: object
    provenance: object

@dataclass(frozen=True, slots=True)
class PerceptionRule(_WireValue):
    rule_id: str
    priority: int
    subject_ref: str
    entity_ref: str
    condition_fact_refs: object
    visible: bool
    interpretation_tags: object

@dataclass(frozen=True, slots=True)
class PerceptionRequest(_WireValue):
    request_ref: str
    subject_ref: str
    truth: object
    rules: object
    provenance: object

@dataclass(frozen=True, slots=True)
class PerceptionOverlay(_WireValue):
    overlay_ref: str
    request: object
    truth_sha256: str
    evaluated_rules: object
    visible_entities: object
    hidden_entities: object
    tags: object
    contradiction_refs: object
    objective_effects: object

@dataclass(frozen=True, slots=True)
class WeightedOption(_WireValue):
    option_id: str
    weight: int

@dataclass(frozen=True, slots=True)
class WeightedAllocation(_WireValue):
    options: object
    total_q6: int

@dataclass(frozen=True, slots=True)
class SelectionRequest(_WireValue):
    domain: str
    binding_sha256: str
    context_sha256: str
    seed_token: str
    options: object

@dataclass(frozen=True, slots=True)
class SelectionResult(_WireValue):
    request: object
    selected_id: object
    counters_used: int
    accepted_draw: object

@dataclass(frozen=True, slots=True)
class BiasTerm(_WireValue):
    event_id: str
    domain: str
    target_id: str
    contribution_q6: int
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class BiasState(_WireValue):
    state_ref: str
    logical_epoch: int
    events: object
    weights: object

@dataclass(frozen=True, slots=True)
class BiasUpdateResult(_WireValue):
    before: object
    proposed: object
    effect_status: object

@dataclass(frozen=True, slots=True)
class ExistentialMetricInputs(_WireValue):
    context_ref: str
    compressibility_q6: int
    symmetry_q6: int
    persistence_q6: int
    entropy_q6: int
    coefficient_c: int
    coefficient_s: int
    coefficient_p: int
    coefficient_h: int
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class ExistenceMeasure(_WireValue):
    inputs: object
    potential_q6: int

@dataclass(frozen=True, slots=True)
class CoreDiagnostic(_WireValue):
    diagnostic_ref: str
    owner: str
    rule: str
    status: str
    failure_code: object
    field: object
    evidence_refs: object
    explanation: str

@dataclass(frozen=True, slots=True)
class CoreResult(_IssuedValue):
    operation_reference: str
    binding: object
    status: str
    value: object
    diagnostics: object
    effect_status: str

@dataclass(frozen=True, slots=True)
class ModuleStatus(_WireValue):
    module_id: str
    generation: int
    phase: str
    closed: bool
    inflight: int
    ledger_used: int

@dataclass(frozen=True, slots=True)
class ModuleCompletion(_WireValue):
    request_ref: str
    admitted_generation: int
    status: str
    result_ref: object
    actual_effect_status: str

@dataclass(frozen=True, slots=True)
class ProphecyRoute(_WireValue):
    route_id: str
    condition_refs: object
    destination_interpretation_ref: str

@dataclass(frozen=True, slots=True)
class ProphecyAttractor(_WireValue):
    target_domain: str
    target_reference: str
    weight_q6: int

@dataclass(frozen=True, slots=True)
class ProphecyRecord(_WireValue):
    prophecy_id: str
    provenance: object
    attractor: object
    fixed_script: bool
    deflection_routes: object
    transmutation_routes: object
    status: str
    condition_refs: object

@dataclass(frozen=True, slots=True)
class OmenCluster(_WireValue):
    cluster_id: str
    prophecy_refs: object
    observed_symbol_refs: object
    provenance: object

@dataclass(frozen=True, slots=True)
class RuntimeBiasEffect(_WireValue):
    effect_id: str
    before_ref: str
    term: object
    effect_status: object
    provenance: object

@dataclass(frozen=True, slots=True)
class RecurringSymbolState(_WireValue):
    state_id: str
    symbol_ref: str
    recurrence_count: int
    logical_epoch: int
    provenance: object

@dataclass(frozen=True, slots=True)
class RegistrySource(_WireValue):
    source_ref: str
    source_sha256: str
    evidence_ref: str

@dataclass(frozen=True, slots=True)
class WolfPressure(_WireValue):
    white_q6: int
    dark_q6: int
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class WolfBias(_WireValue):
    white_q6: int
    dark_q6: int

@dataclass(frozen=True, slots=True)
class ArchetypeAffinity(_WireValue):
    domain: str
    affinity_refs: object

@dataclass(frozen=True, slots=True)
class ClusterRecord(_WireValue):
    cluster_id: str
    member_ids: object
    lawful_basis_refs: object
    stability: str
    contradiction_risk_ref: str

@dataclass(frozen=True, slots=True)
class ArchetypeRegistry(_WireValue):
    registry_id: str
    primary_source: object
    relationship_source: object
    archetypes: object
    clusters: object

@dataclass(frozen=True, slots=True)
class RelationObservation(_WireValue):
    first_id: str
    second_id: str
    relation: str
    score_delta_q6: int
    coexistence_allowed: bool
    suppressed_id: object

@dataclass(frozen=True, slots=True)
class ClusterScore(_WireValue):
    cluster_id: str
    qualifying_members: object
    base_score_q6: int
    stability_bonus_q6: int
    support_penalty_q6: int
    final_score_q6: int
    activated: bool
    reasons: object

@dataclass(frozen=True, slots=True)
class BiasEvent(_WireValue):
    event_id: str
    terms: object
    evidence_refs: object

@dataclass(frozen=True, slots=True)
class ModuleLifecycleReceipt(_WireValue):
    operation_reference: str
    action: str
    before: object
    after: object
    status: str
    failure_code: object

@dataclass(frozen=True, slots=True)
class CoreOrchestrationRequest(_WireValue):
    operation_reference: str
    inputs: object
    origin: object
    normalization: object
    declared_subject: object
    target_constraints: object
    realm_request: object
    archetype_context: object
    truth_input: object
    perception_request: object

@dataclass(frozen=True, slots=True)
class CoreOrchestrationResult(_IssuedValue):
    request: object
    binding: object
    normalization_result: object
    normalization_completion: object
    normalized_origin: object
    normalized_origin_completion: object
    generation_run: object
    cosmology: object
    realm_access: object
    realm_shift: object
    pattern: object
    archetypes: object
    narrative: object
    perception: object
    status: str
    diagnostics: object

@dataclass(frozen=True, slots=True)
class CoreNormalizationRequest(_WireValue):
    plan: object
    context: object

WIRE_TYPES = (CoreBinding, ProfileRealmDefinition, CosmicState, CoreProvenance, DeclaredTruthFact, TruthInputSnapshot, AttunementFact, RealmAccessRequest, RealmAccessResult, RealmShiftProposal, PatternProjectionRule, PatternObservation, CosmicPatternSnapshot, ArchetypeRecord, ArchetypeContext, ArchetypeScore, ArchetypeEvaluation, NarrativeInterpretation, PerceptionRule, PerceptionRequest, PerceptionOverlay, WeightedOption, WeightedAllocation, SelectionRequest, SelectionResult, BiasTerm, BiasState, BiasUpdateResult, ExistentialMetricInputs, ExistenceMeasure, CoreDiagnostic, CoreResult, ModuleStatus, ModuleCompletion, ProphecyRoute, ProphecyAttractor, ProphecyRecord, OmenCluster, RuntimeBiasEffect, RecurringSymbolState, RegistrySource, WolfPressure, WolfBias, ArchetypeAffinity, ClusterRecord, ArchetypeRegistry, RelationObservation, ClusterScore, BiasEvent, ModuleLifecycleReceipt, CoreOrchestrationRequest, CoreOrchestrationResult, CoreNormalizationRequest,)
OUTPUT_TYPES = (ProfileRealmDefinition, CosmicState, CoreProvenance, DeclaredTruthFact, TruthInputSnapshot, AttunementFact, RealmAccessRequest, RealmAccessResult, RealmShiftProposal, PatternProjectionRule, PatternObservation, CosmicPatternSnapshot, ArchetypeRecord, ArchetypeContext, ArchetypeScore, ArchetypeEvaluation, NarrativeInterpretation, PerceptionRule, PerceptionRequest, PerceptionOverlay, WeightedOption, WeightedAllocation, SelectionRequest, SelectionResult, BiasTerm, BiasState, BiasUpdateResult, ExistentialMetricInputs, ExistenceMeasure, ModuleStatus, ModuleCompletion, ProphecyRoute, ProphecyAttractor, ProphecyRecord, OmenCluster, RuntimeBiasEffect, RecurringSymbolState, RegistrySource, WolfPressure, WolfBias, ArchetypeAffinity, ClusterRecord, ArchetypeRegistry, RelationObservation, ClusterScore, BiasEvent, ModuleLifecycleReceipt, CoreOrchestrationRequest,)


def _peer_types():
    from .ash_pattern_engine import generation_values as gen
    from .ash_pattern_engine import diagnostics_values as dv
    from .ash_pattern_engine import diagnostic_module_values as mv
    base = tuple(rt.STATE_TYPES) + tuple(rt.OWNED_TYPES) + tuple(gen.WIRE_TYPES)
    normalization = (nv.NormalizationPolicyBinding, nv.NormalizationPlan, nv.NormalizationPlanValidation,
                     nv.NormalizationContext, nv.NormalizationStep, nv.NormalizationDiagnosticRecord,
                     nv.NormalizationResult, nv.NormalizationFailure, nv.NormalizationCaptureFailure)
    receipts = (dv.DiagnosticsCompletionReceipt, dv.DiagnosticsHealth, dv.MissingCoverage,
                dv.RetentionBoundary, dv.DiagnosticCounterState,mv.ModuleFinalObservationReceipt,
                mv.ModuleReturnAuditObservation)
    try:
        pe = importlib.import_module('.ash_pattern_engine.planner_emitter_values', __package__)
    except ModuleNotFoundError as error:
        if error.name != __package__ + '.ash_pattern_engine.planner_emitter_values':
            raise
        pe = None
    pe_types = () if pe is None else tuple(pe.WIRE_TYPES)
    return base + normalization + receipts + pe_types


def _peer_guard(value, active, depth=0):
    kind = type(value)
    if value is None or _one_of(kind, (str, bool, int)):
        if kind is int and abs(value).bit_length() > 64:
            _fail()
        return
    if depth > 48 or id(value) in active:
        _fail()
    if not _one_of(kind, _peer_types() + (tuple, frozenset)):
        _fail()
    active.add(id(value))
    try:
        if _one_of(kind, (tuple, frozenset)):
            if len(value) > 1024:
                _fail()
            for child in value:
                _peer_guard(child, active, depth + 1)
        else:
            for field in fields(kind):
                _peer_guard(object.__getattribute__(value, field.name), active, depth + 1)
    finally:
        active.remove(id(value))


def _peer_record(value):
    _peer_guard(value, set())
    kind = type(value)
    if _one_of(kind, rt.STATE_TYPES + rt.OWNED_TYPES):
        return json.loads(rt.canonical_bytes(value))
    from .ash_pattern_engine import generation_values as gen
    if _one_of(kind, gen.WIRE_TYPES):
        return json.loads(gen.canonical_bytes(value))
    try:
        pe = importlib.import_module('.ash_pattern_engine.planner_emitter_values', __package__)
    except ModuleNotFoundError as error:
        if error.name != __package__ + '.ash_pattern_engine.planner_emitter_values':
            raise
        pe = None
    if pe is not None and _one_of(kind, pe.WIRE_TYPES):
        return json.loads(pe.canonical_bytes(value))
    from .ash_pattern_engine import session_values
    return session_values.raw_business_record(value)


def _text(value, domain, field):
    maximum = {'ID': 128, 'REF': 256, 'TEXT': 512, 'SEED': 128}.get(domain, 512)
    if type(value) is not str or not 1 <= len(value) <= maximum:
        _fail(field)
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        _fail(field)
    if domain in ('ID', 'REF') and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', value) is None:
        _fail(field)
    if domain == 'HASH' and re.fullmatch(r'[a-f0-9]{64}', value) is None:
        _fail(field)
    if domain == 'SIGNATURE' and re.fullmatch(r'[01]{9}', value) is None:
        _fail(field)
    if domain == 'MASK512' and re.fullmatch(r'[01]{512}', value) is None:
        _fail(field)


def _field(value, domain, field, normalize, active):
    if domain.endswith('?'):
        if value is None:
            return value
        domain = domain[:-1]
    match = re.fullmatch(r'([A-Za-z_]+)\[(\d+)(?:\.\.(\d+))?\]', domain)
    if match:
        low, high = int(match[2]), int(match[3] or match[2])
        allowed = (tuple, list) if normalize else (tuple,)
        if not _one_of(type(value), allowed) or not low <= len(value) <= high:
            _fail(field)
        result = tuple(_field(item, match[1], field, normalize, active) for item in value)
        return result
    if domain in ('ID', 'REF', 'TEXT', 'SEED', 'HASH', 'SIGNATURE', 'MASK512'):
        _text(value, domain, field)
        return value
    ranges = {'Q6': (0, Q6), 'SIGNED_Q6': (-Q6, Q6), 'SIGNED63': (-(1 << 63), (1 << 63) - 1),
              'SIGNED32': (-(1 << 31), (1 << 31) - 1), 'UINT64': (0, (1 << 64) - 1)}
    match = re.fullmatch(r'(\d+)\.\.(\d+)', domain)
    if match:
        ranges[domain] = int(match[1]), int(match[2])
    if domain in ranges:
        if type(value) is not int or not ranges[domain][0] <= value <= ranges[domain][1]:
            _fail(field)
        return value
    if domain == 'bool' or domain == 'FALSE':
        if type(value) is not bool or (domain == 'FALSE' and value):
            _fail(field)
        return value
    if domain in DOMAINS:
        if type(value) is not str or value not in DOMAINS[domain]:
            _fail(field)
        return value
    if domain in ('DECLARED_INPUT', 'PROPOSED_ONLY', 'NONE'):
        if type(value) is not str or value != domain:
            _fail(field)
        return value
    expected = {'CanonicalAshBinding': (state.CanonicalAshBinding,),
                'ProfileBinding': (state.AvailableProfileBinding, state.UnavailableProfileBinding),
                'StateDiagnosis': (state.StateDiagnosis,), 'RealmIdentity': (rt.RealmIdentity,),
                'NormalizationStep': (nv.NormalizationStep,), 'NormalizationPlan': (nv.NormalizationPlan,),
                'NormalizationContext': (nv.NormalizationContext,),
                'NormalizationPacket': (nv.NormalizationResult, nv.NormalizationFailure, nv.NormalizationCaptureFailure),
                'CORE_OUTPUT': OUTPUT_TYPES}
    if domain in FIELD_DOMAINS:
        expected[domain] = (globals()[domain],)
    if domain not in expected:
        found = tuple(cls for cls in _peer_types() if cls.__name__ == domain)
        if not found:
            _fail(field)
        expected[domain] = found
    if not _one_of(type(value), expected[domain]):
        _fail(field)
    _walk(value, active, normalize=normalize)
    return value


def _coherent(value):
    kind = type(value)
    if kind is CoreBinding:
        if tuple((name, getattr(value.canonical_binding, name)) for name, expected in CANONICAL_FIELDS) != CANONICAL_FIELDS:
            _fail('canonical_binding', 'CORE_BINDING_MISMATCH')
        if value.policy_id != CORE_POLICY_ID or value.policy_sha256 != CORE_POLICY_SHA256:
            _fail('policy_sha256', 'CORE_BINDING_MISMATCH')
        if type(value.profile_binding) is not state.AvailableProfileBinding:
            _fail('profile_binding', 'CORE_CAPABILITY_UNAVAILABLE')
        ids = tuple(row.realm_id for row in value.profile_realms)
        if len(set(ids)) != len(ids):
            _fail('profile_realms', 'CORE_PROFILE_CONFLICT')
        if any(origin not in ids for row in value.profile_realms for origin in row.allowed_origins):
            _fail('allowed_origins', 'CORE_UNKNOWN_REFERENCE')
    elif kind is CosmicState:
        if value.structural_coordinates != tuple('b' + str(index) for index in range(9)):
            _fail('structural_coordinates')
    elif kind is WeightedAllocation:
        if sum(option.weight for option in value.options) != value.total_q6 or value.total_q6 not in (0, Q6):
            _fail('total_q6')
    elif kind is SelectionResult:
        if (value.selected_id is None) != (value.accepted_draw is None):
            _fail('accepted_draw')
        if value.selected_id is not None and value.selected_id not in tuple(row.option_id for row in value.request.options):
            _fail('selected_id')
    elif kind is BiasUpdateResult:
        if value.proposed.logical_epoch < value.before.logical_epoch:
            _fail('logical_epoch', 'CORE_EPOCH_REVERSED')
    elif kind is RealmShiftProposal:
        if value.access.eligible is not True or value.before_realm_id != value.access.request.source_realm_id or value.target_realm_id != value.access.request.target_realm_id:
            _fail('access')
    elif kind is PatternObservation:
        if not value.matched and value.strength_q6 != 0:
            _fail('strength_q6')
    elif kind is CosmicPatternSnapshot:
        if value.source_signature != value.source_identity.state_signature or value.destination_signature != value.destination_identity.state_signature:
            _fail('destination_identity')
        if len({row.pattern_id for row in value.observations}) != len(value.observations):
            _fail('observations')
        if any(row.actual_codeword_trace != value.actual_codeword_trace for row in value.observations):
            _fail('actual_codeword_trace')
    elif kind is ArchetypeEvaluation:
        if set(value.dominant) & set(value.secondary):
            _fail('secondary')
    elif kind is PerceptionOverlay:
        if set(value.visible_entities) & set(value.hidden_entities) or set(value.visible_entities) | set(value.hidden_entities) != set(value.request.truth.entity_refs):
            _fail('visible_entities')
        if value.truth_sha256 != _wire_digest(value.request.truth):
            _fail('truth_sha256')
    elif kind is BiasEvent:
        keys = tuple((row.domain, row.target_id) for row in value.terms)
        if len(set(keys)) != len(keys) or any(row.event_id != value.event_id for row in value.terms):
            _fail('terms')
    elif kind is ClusterRecord:
        if len(set(value.member_ids)) != len(value.member_ids):
            _fail('member_ids')
    elif kind is OmenCluster:
        if len(set(value.prophecy_refs)) != len(value.prophecy_refs):
            _fail('prophecy_refs')
    elif kind is ModuleStatus:
        if value.inflight > value.ledger_used or (value.phase in ('STOPPING', 'FAILED') and not value.closed):
            _fail('inflight')
    for cls, attr, key in ((RealmAccessRequest, 'facts', 'realm_id'), (CoreBinding, 'profile_realms', 'realm_id'),
                          (SelectionRequest, 'options', 'option_id'), (WeightedAllocation, 'options', 'option_id'),
                          (BiasState, 'weights', 'option_id'), (ArchetypeRegistry, 'archetypes', 'archetype_id'),
                          (ArchetypeRegistry, 'clusters', 'cluster_id'), (PerceptionRequest, 'rules', 'rule_id')):
        if kind is cls:
            identifiers = tuple(getattr(row, key) for row in getattr(value, attr))
            if len(set(identifiers)) != len(identifiers):
                _fail(attr)
    if kind is CoreDiagnostic:
        record = {name: _record(object.__getattribute__(value, name)) for name in FIELD_DOMAINS['CoreDiagnostic']}
        if len(json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('ascii')) > MAX_DIAGNOSTIC_BYTES:
            _fail('diagnostics', 'CORE_RESOURCE_LIMIT')


def _walk(value, active, *, normalize=False):
    kind = type(value)
    if not _one_of(kind, WIRE_TYPES):
        _peer_record(value)
        return
    if id(value) in active or len(active) > 48:
        _fail()
    active.add(id(value))
    try:
        for name, domain in FIELD_DOMAINS[kind.__name__].items():
            try:
                actual = object.__getattribute__(value, name)
            except AttributeError:
                _fail(name)
            checked = _field(actual, domain, name, normalize, active)
            if normalize and checked is not actual:
                object.__setattr__(value, name, checked)
        for name in UNIQUE_FIELDS[kind.__name__]:
            sequence = object.__getattribute__(value, name)
            records = tuple(json.dumps(_record(item), sort_keys=True, separators=(',', ':'), ensure_ascii=True) for item in sequence)
            if len(set(records)) != len(records):
                _fail(name)
        _coherent(value)
    finally:
        active.remove(id(value))


def revalidate_value(value):
    if not _one_of(type(value), WIRE_TYPES):
        _fail()
    _walk(value, set())


def _record(value):
    kind = type(value)
    if value is None or _one_of(kind, (str, int, bool)):
        return value
    if kind is tuple:
        return [_record(item) for item in value]
    if _one_of(kind, WIRE_TYPES):
        return {name: _record(object.__getattribute__(value, name)) for name in FIELD_DOMAINS[kind.__name__]}
    return _peer_record(value)


def _chunks(value):
    yield from json.JSONEncoder(ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).iterencode(_record(value))


def _wire_digest(value):
    digest = hashlib.sha256()
    for chunk in _chunks(value):
        digest.update(chunk.encode('ascii'))
    return digest.hexdigest()


def canonical_bytes(value, *, limit=MAX_RAW_CORE_BYTES):
    revalidate_value(value)
    if type(limit) is not int or not 1 <= limit <= MAX_RAW_CORE_BYTES:
        _fail('value')
    result, size = [], 0
    for text in _chunks(value):
        chunk = text.encode('ascii')
        size += len(chunk)
        if size > limit:
            _fail('value', 'CORE_RESOURCE_LIMIT')
        result.append(chunk)
    return b''.join(result)


def raw_business_size(value, *, limit=MAX_RAW_CORE_BYTES):
    try:
        return len(canonical_bytes(value, limit=limit))
    except CoreContractError as error:
        if error.code == 'CORE_RESOURCE_LIMIT':
            return limit + 1
        raise


@dataclass(frozen=True, slots=True)
class _ResultCookie:
    issuer: object
    original: object
    wire_sha256: str


def _issue_result(owner, result):
    if not _one_of(type(result), (CoreResult, CoreOrchestrationResult)):
        _fail()
    revalidate_value(result)
    object.__setattr__(result, '_core_result_cookie', _ResultCookie(owner, result, _wire_digest(result)))
    return result


def _validate_result(owner, result, binding):
    if not _one_of(type(result), (CoreResult, CoreOrchestrationResult)):
        return False
    try:
        cookie = object.__getattribute__(result, '_core_result_cookie')
        if (type(cookie) is not _ResultCookie or cookie.issuer is not owner or cookie.original is not result or
                type(cookie.wire_sha256) is not str):
            return False
        revalidate_value(result)
        return _wire_digest(result.binding) == _wire_digest(binding) and cookie.wire_sha256 == _wire_digest(result)
    except (CoreContractError, AttributeError, ValueError):
        return False


@dataclass(frozen=True, slots=True)
class _OwnerCookie:
    original: object
    owner_class: object
    binding_sha256: str


class _ConfiguredOwner:
    __slots__ = ('_core_binding', '_core_owner_cookie', '_core_lifecycle')


def _initialize_owner(owner, binding, owner_class):
    if type(owner) is not owner_class or type(binding) is not CoreBinding:
        _fail('binding')
    revalidate_value(binding)
    object.__setattr__(owner, '_core_binding', binding)
    object.__setattr__(owner, '_core_owner_cookie', _OwnerCookie(owner, owner_class, _wire_digest(binding)))
    object.__setattr__(owner, '_core_lifecycle', None)


def _owner_configuration(owner, owner_class):
    if type(owner) is not owner_class:
        _fail('owner')
    try:
        cookie = object.__getattribute__(owner, '_core_owner_cookie')
        binding = object.__getattribute__(owner, '_core_binding')
    except AttributeError:
        _fail('binding')
    if (type(cookie) is not _OwnerCookie or cookie.original is not owner or cookie.owner_class is not owner_class or
            type(cookie.binding_sha256) is not str or type(binding) is not CoreBinding):
        _fail('owner')
    revalidate_value(binding)
    if cookie.binding_sha256 != _wire_digest(binding):
        _fail('binding', 'CORE_BINDING_MISMATCH')
    return binding


def _operation_result(owner, owner_class, reference, value, rule, *, status='COMPLETED',
                      code=None, field=None, effect='NONE', evidence=(), explanation='Core operation evaluated.'):
    binding = _owner_configuration(owner, owner_class)
    diagnostic = CoreDiagnostic(reference + ':diagnostic', owner_class.CORE_OWNER, rule,
                                status, code, field, tuple(evidence), explanation)
    return _issue_result(owner, CoreResult(reference, binding, status, value, (diagnostic,), effect))


def _validate_model(state_model, binding):
    from .ash_pattern_engine.state_model import StateModel
    if type(state_model) is not StateModel:
        _fail('binding', 'CORE_BINDING_MISMATCH')
    canonical = StateModel.canonical_binding.fget(state_model)
    profile = StateModel.profile_binding.fget(state_model)
    if type(canonical) is not state.CanonicalAshBinding or type(profile) is not state.AvailableProfileBinding:
        _fail('binding', 'CORE_BINDING_MISMATCH')
    _peer_guard(canonical, set())
    _peer_guard(profile, set())
    if _wire_digest(canonical) != _wire_digest(binding.canonical_binding) or _wire_digest(profile) != _wire_digest(binding.profile_binding):
        _fail('binding', 'CORE_BINDING_MISMATCH')
    return state_model
