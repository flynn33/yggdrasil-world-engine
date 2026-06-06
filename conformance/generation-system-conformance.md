# Generation System Conformance

Date: 2026-05-09

## Authority Boundary

Current authority clarification, 2026-05-16: this conformance file is preserved
as ASH Pattern System component stability and generation-packet evidence. The
ASH Cosmological Model is the upstream foundation for YWE and its systems. The
ASH Pattern System is a YWE component for state consistency, diagnostics,
recovery, containment, conformance, generation-plan consistency, and
update/patch stability. YWE is the downstream domain interpretation layer.
Adapters and host implementations may materialize emitted plans, but they must
not author ASH truth or YWE domain truth.

ASH is also the upstream generative authority for meaningful YWE generation.
YWE consumes ASH-derived state, diagnostics, codeword traces, and generation
plans, then interprets lawful pattern output into world, quest, NPC, creature,
artifact, myth, prophecy, perception, faction, progression, wolf, and ability
manifests.

Forsetti is not the active authority for ASH/ASP math, YWE cosmology truth,
codewords, diagnostics, generation semantics, or conformance acceptance.

## Shared Packet Spine

Shared packet contracts are defined in:

- `docs/architecture/ash_upstream_authority_contract.md`
- `core/ash_pattern_engine/pattern_engine_schema.json`
- `core/narrative_engine/ash_runtime_generation_flow.yaml`
- `data/schemas/ash_generation_packet_schema.json`
- `data/validation/ash_generation_gate_contract.json`
- `data/validation/ash_upstream_authority_gate_contract.json`

The upstream generation spine is:

```text
RuntimeGenerationTrigger
  -> YWEGenerationContextPacket
  -> ASHUpstreamGenerationEnvelope
  -> YWEInterpretationPacket
  -> SystemManifestExchange
  -> HostAdapterMaterializationRequest
  -> MaterializationResult
  -> ResolutionPayload
  -> WorldstateDeltaPacket or DiagnosticNoOp
  -> FutureGenerationBiasUpdate
```

Every meaningful generator consumes or cites:

- `CosmicPatternSnapshot`
- `DiagnosticEnvelope`
- `GenerationPlan`
- `SourceASHRefs`
- `YWEGenerationContextPacket`
- `ASHUpstreamGenerationEnvelope`
- `YWEInterpretationPacket`

Every meaningful resolution emits:

- `WorldstateDeltaPacket`, or
- explicit `DiagnosticNoOp`

Player action and exploration inputs may influence `YWEGenerationContextPacket`
and `FutureGenerationBiasUpdate`. They must not mutate ASH math.

## System Coverage Matrix

| System | Contract paths | Required output records |
| --- | --- | --- |
| Character creation and progression | `core/narrative_engine/character_creation_progression_interface.json`, `core/narrative_engine/character_creation_progression_rules.yaml`, `data/schemas/character_progression_schema.json` | `CharacterSeedManifest`, `IdentityPressureVector`, `ProgressionDelta`, `PlayerStateDelta` |
| Quest generation | `modules/quest_engine/quest_engine_interface.json`, `data/quest_archetypes/quest_chain_manifest_schema.json` | `QuestChainManifest`, `StageManifest`, `CompletionModeSet`, `QuestResolutionPayload` |
| Creature creation | `modules/creature_engine/creature_engine_interface.json`, `data/schemas/creature_manifest_schema.json` | `CreatureManifest`, `EncounterPlan`, `BehaviorPressureVector` |
| Artifact materialization | `modules/artifact_engine/artifact_engine_interface.json`, `data/schemas/artifact_manifest_schema.json` | `ArtifactManifest`, `UseConsequenceRoute`, `MythSeedCandidate` |
| NPC synthesis | `core/narrative_engine/engine_interface.json`, `data/schemas/npc_manifest_schema.json` | `NPCManifest`, `RelationshipVector`, `TruthFunction`, `PersistenceState` |
| Worldstate deltas | `core/narrative_engine/engine_interface.json`, `core/narrative_engine/worldstate_delta_rules.yaml`, `data/schemas/worldstate_delta_packet_schema.json` | `WorldstateDeltaPacket`, `FutureGenerationBiasUpdate`, `DiagnosticNoOp` |
| Myth emergence | `modules/myth_engine/myth_engine_interface.json`, `data/schemas/myth_record_schema_expansion.json` | `MythRecord`, `MythLine`, `SocialDistributionDelta` |
| Prophecy activation | `modules/prophecy_engine/prophecy_engine_interface.json`, `data/schemas/prophecy_schema_expansion.json` | `ProphecyRecord`, `OmenCluster`, `RuntimeBiasEffect` |
| Perception overlays | `core/perception_engine/engine_interface.json`, `core/perception_engine/perception_schema.json`, `data/schemas/perception_layer_persistence_schema.json` | `PerceptionStateRecord`, `OverlayManifest`, `VisibilityRules` |
| Faction topology | `data/faction_topology/faction_topology_state_schema.yaml` | `FactionDelta`, `ClaimRecord`, `ReformCurrent`, `SuccessionTrack` |
| Lore archive generation | `core/narrative_engine/lore_archive_generation_rules.yaml`, `data/schemas/lore_archive_record_schema.json` | `LoreArchiveRecord`, `LoreRecordVariant`, `VisibilityScope` |
| Realm mechanics and transitions | `core/realm_engine/engine_interface.json`, `data/schemas/realm_transition_resolution_schema.json`, `data/realm/realm_mechanics_rules.yaml`, `data/realm/realm_boundary_profiles.yaml` | `RealmTransitionResolution`, `WorldstateDeltaPacket`, `DiagnosticNoOp` |

## Adapter Materialization Boundary

Unity, Unreal, and Godot adapter documents now state that adapters may
materialize or instantiate only from emitted `GenerationPlan` outputs. Adapter
surfaces must preserve `CosmicPatternSnapshot`, `DiagnosticEnvelope`, and
`generation_plan_ref` provenance and must not author ASH state, codewords,
diagnostics, cosmology, myths, prophecies, character meaning, or YWE domain
truth.

Host adapters materialize approved manifests but do not author symbolic truth.

## Validation

Blocking package acceptance is implemented in:

`.github/scripts/ywe_package_acceptance_check.py`

The script implements the 14 required package test families and is called by
both local validation runners.
