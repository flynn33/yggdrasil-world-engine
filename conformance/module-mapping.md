# Module Mapping

YWE maps `core/ash_pattern_engine/` to the ASH StateModel, TransitionRegistry,
Diagnostics, GenerationPlanner, and ArtifactEmitter contracts. Downstream YWE
engines consume `CosmicPatternSnapshot` and may only interpret ASH-derived
state, orbit, transition, diagnostic, and plan records.

Package rebuild surfaces map as follows:

- `core/narrative_engine/` owns character creation/progression, NPC synthesis,
  worldstate delta routing, and lore archive generation contracts.
- `modules/quest_engine/` owns `QuestChainManifest`, `StageManifest`,
  `CompletionModeSet`, and `QuestResolutionPayload`.
- `modules/creature_engine/` owns `CreatureManifest`, `EncounterPlan`, and
  `BehaviorPressureVector`.
- `modules/artifact_engine/` owns `ArtifactManifest`, `UseConsequenceRoute`,
  and `MythSeedCandidate`.
- `modules/myth_engine/` owns `MythRecord`, `MythLine`, and
  `SocialDistributionDelta`.
- `modules/prophecy_engine/` owns `ProphecyRecord`, `OmenCluster`, and
  `RuntimeBiasEffect`.
- `core/perception_engine/` owns `PerceptionStateRecord`, `OverlayManifest`,
  and `VisibilityRules`.
- `data/faction_topology/` owns `FactionDelta`, `ClaimRecord`,
  `ReformCurrent`, and `SuccessionTrack`.
- `core/realm_engine/` owns realm transition eligibility and
  `RealmTransitionResolution`.

All listed systems require `CosmicPatternSnapshot`, `DiagnosticEnvelope`, and
`GenerationPlan` provenance for meaningful generation or materialization.
