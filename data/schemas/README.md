# schemas Data Domain

Date: 2026-05-10
Project: Yggdrasil World Engine
Status: source-truth schema index

## Purpose
Documents the shared schema contracts used by YWE systems to consume
ASH-derived state, diagnostics, codeword traces, generation plans, and
downstream interpretation packets.

Current authority clarification: ASH Model of the Universe is the mathematical
and ontological foundation for YWE and its systems. ASH Pattern System is a YWE
component for pattern integrity, diagnostics, recovery, containment,
conformance, code resilience, update safety, and patch stability. Earlier
shorthand that described ASH as upstream mathematical and generative authority
should be read as referring to the ASH Model of the Universe, not ASH Pattern
System as an upstream authority.

## Upstream Generation Packet Spine

Meaningful generation uses this packet spine:

```text
YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestHandoff
  -> QuestChainManifest / NPCManifest / CodexRecord / MythRecord
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> LocationMutationState or LocationMutationDelta
  -> FutureGenerationBiasUpdate
```

## Core Files

Rows without an inline deferred marker remain active within their accepted
phase boundary. The active Phase 8-9 schema boundary is the base world ontology,
leaf branch reality, branch event, branch generation context, pattern vector,
existence potential, axiom diagnostic packet, plane pressure state, and future
generation bias update foundation.

| File | Role |
|---|---|
| `ash_generation_packet_schema.json` | Shared ASH/YWE packet index and provenance spine |
| `ash_upstream_generation_envelope_schema.json` | ASH provenance envelope for meaningful generated output |
| `ywe_generation_context_packet_schema.json` | Player, realm, perception, and worldstate context submitted into ASH-governed generation |
| `ywe_interpretation_packet_schema.json` | YWE interpretation of ASH-derived output for feature-engine handoff |
| `player_action_trace_schema.json` | Phase 10 player action trace records that provide provenance for meaningful player-state updates |
| `player_runtime_state_schema.json` | Phase 10 player runtime state spine for branch, identity, resonance, memory, world links, and ASH Pattern System resilience references |
| `player_agent_state_schema.json` | Phase 10 branch-bound player agency state |
| `celestial_identity_state_schema.json` | Phase 10 veiled celestial identity and reveal-through-play evidence state |
| `plane_attunement_state_schema.json` | Phase 10 dynamic plane attunement pressure state |
| `bloodline_resonance_state_schema.json` | Phase 10 dynamic bloodline resonance pressure state |
| `wolf_resonance_summary_schema.json` | Phase 10 wolf resonance summary; not a morality meter |
| `player_memory_record_schema.json` | Phase 10 player memory record references |
| `player_branch_history_schema.json` | Phase 10 player branch history references |
| `player_progression_signal_schema.json` | Phase 10 progression signal references |
| `player_state_update_packet_schema.json` | Phase 10 controlled player-state mutation packet |
| `player_state_snapshot_schema.json` | Phase 10 player-state snapshot reference contract |
| `exploration_frontier_request_schema.json` | Frontier, threshold, thin-veil, and unresolved-node generation requests |
| `worldstate_delta_packet_schema.json` | Phase 11 meaningful consequence packet with truth scope, consequence classification, provenance, and delta/no-op validation |
| `diagnostic_noop_schema.json` | Phase 11 explicit no-op record for evaluated events with no persistent consequence |
| `location_state_record_schema.json` | Phase 11 persistent location state record |
| `location_mutation_rule_schema.json` | Phase 11 location mutation trigger, context, effect, provenance, and fallback rule |
| `location_branch_overlay_schema.json` | Phase 11 player-specific leaf branch location overlay |
| `location_resolution_context_schema.json` | Phase 11 resolver input context spanning player, branch, location, cosmology, and diagnostics |
| `future_generation_bias_update_schema.json` | Phase 11 consequence-derived eligibility and weighting bias for later generation context |
| `truth_scope_schema.json` | Phase 11 allowed truth scopes |
| `consequence_classification_schema.json` | Phase 11 allowed consequence classes |
| `worldstate_resolution_result_schema.json` | Phase 11 resolution result packet for delta/no-op and secondary updates |
| `location_access_state_schema.json` | Phase 11 access state for gates, paths, thresholds, routes, and related location surfaces |
| `location_content_eligibility_schema.json` | Phase 11 downstream content eligibility record without content materialization |
| `location_mutation_history_schema.json` | Phase 11 append-only mutation history |
| `worldstate_location_mutation_schema.json` | Earlier Phase 11-adjacent packet-spine schema retained for compatibility and historical validation |
| `quest_npc_lore_generation_schema.json` | Phase 12 quest chains, NPC manifests, NPC memory deltas, lore records, myth records, and social distribution deltas |
| `quest_generation_context_schema.json` | Phase 12 context packet for quest generation from axiom pressure, branch reality, player state, location state, and worldstate consequences |
| `npc_generation_context_schema.json` | Phase 12 context packet for NPC generation from branch, relation, location, pattern, and self-reference context |
| `lore_generation_context_schema.json` | Phase 12 context packet for lore generation from pattern trace, source events, truth scope, and visibility rules |
| `generated_lore_fragment_schema.json` | Phase 12 generated lore fragment contract with pattern trace, source context, truth scope, visibility, and provenance |
| `content_generation_provenance_schema.json` | Phase 12 shared provenance spine for generated content candidates |
| `content_generation_candidate_schema.json` | Phase 12 generic candidate handoff contract for quest, NPC, and lore outputs |
| `content_manifest_handoff_schema.json` | Phase 12 downstream handoff contract for generated content manifests |
| `quest_npc_lore_linkage_schema.json` | Phase 12 linkage contract connecting quests, NPC candidates, lore fragments, and shared provenance |
| `engine_authority_stack_schema.json` | Source-truth authority stack contract for ASH Model, YWE, ASH Pattern System component, and game layer |
| `engine_cosmology_framework_schema.json` | Engine cosmology framework contract for structural layers and extensible implementation lore |
| `ash_pattern_system_component_role_schema.json` | ASH Pattern System component-role schema for diagnostics, recovery, containment, conformance, resilience, update safety, and patch stability |
| `twin_wolf_companion_state_schema.json` | Twin Wolf companion canon schema for complementary non-moral embodied companions, quest/combat assistance, and decoherence return |
| `dual_variable_alignment_state_schema.json` | Non-moral dual-variable alignment schema where both variables may grow from the same event |
| `lineage_resonance_state_schema.json` | Simulation-level lineage resonance schema for ancestry, inheritance, faction legacy, and related thematic skins |
| `ability_state_schema.json` | Phase 14 ability state record for latent, pressured, eligible, unlocked, transformed, decohered, or sealed abilities |
| `ability_unlock_pressure_schema.json` | Phase 14 unlock pressure record derived from branch, worldstate, lineage, plane, wolf, artifact, myth, and prophecy sources |
| `ability_source_ref_schema.json` | Phase 14 source provenance reference for ability eligibility and manifestation |
| `ability_manifest_schema.json` | Phase 14 ability manifest contract for use modes, source refs, and consequence policy refs |
| `ability_manifestation_rule_schema.json` | Phase 14 manifestation rule contract for state-bound ability expression |
| `ability_progression_event_schema.json` | Phase 14 ability progression event record |
| `ability_use_context_schema.json` | Phase 14 combat, quest, exploration, perception, social, ritual, recovery, and threshold-use context |
| `ability_consequence_packet_schema.json` | Phase 14 AbilityConsequencePacket for meaningful use outcomes |
| `ability_combat_role_schema.json` | Phase 14 combat role mapping for ability surfaces |
| `ability_quest_application_schema.json` | Phase 14 quest application mapping for ability use |
| `ability_wolf_synergy_schema.json` | Phase 14 wolf synergy record preserving companion presence and non-morality constraints |
| `ability_decoherence_state_schema.json` | Phase 14 temporary decoherence and recovery condition record |
| `ability_branch_influence_schema.json` | Phase 14 leaf-branch influence record |
| `ability_plane_attunement_link_schema.json` | Phase 14 plane attunement link record |
| `ability_lineage_resonance_link_schema.json` | Phase 14 lineage resonance link record |
| `ability_artifact_binding_link_schema.json` | Phase 14 artifact binding link record |
| `ability_myth_prophecy_link_schema.json` | Phase 14 myth and prophecy link record |
| `ability_permission_gate_schema.json` | Phase 14 permission gate result record |
| `ability_cooldown_and_recovery_schema.json` | Phase 14 cooldown, containment, and recovery reference record |
| `ability_risk_profile_schema.json` | Phase 14 risk profile record |
| `ability_catalog_entry_schema.json` | Phase 14 catalog entry for supported use modes and source categories |
| `ability_state_update_packet_schema.json` | Phase 14 AbilityStateUpdatePacket for downstream state mutation handoff |
| `ability_loadout_state_schema.json` | Phase 14 player ability loadout state record |

## Required Provenance

Every meaningful manifest must preserve:

- `source_ash_refs`
- `diagnostic_ref`
- `generation_plan_ref`
- `requested_manifest_kind`
- `worldstate_delta_policy`

## Invariants
- all meaningful generation must remain ASH-derived
- player actions influence future generation context; they do not mutate ASH math
- host adapters materialize approved manifests but do not author truth
- engine structural ontology remains stable while narrative skins remain extensible
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
