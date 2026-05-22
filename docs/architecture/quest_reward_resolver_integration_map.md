# Quest Reward Resolver Integration Map

## Reads from

```text
QuestManifest
QuestResolutionPayload
PlayerRuntimeState
LeafBranchRealityState
WorldstateDeltaHistory
LocationStateRecord
TwinWolfState
AbilityState
PlaneAttunementState
LineageResonanceState
PerceptionState
MythPressureState
ProphecyPressureState
NPC/Faction state
Artifact/Creature eligibility state
ASH Pattern System diagnostic envelopes
```

## Writes to

```text
QuestRewardResolutionPacket
ConsequenceResolutionPacket
PlayerStateUpdatePacket
WorldstateDeltaPacket
LocationMutationCandidate
LocationBranchOverlay
WolfStateUpdatePacket
AbilityStateUpdatePacket
FutureGenerationBiasUpdate
MythSeedCandidate
ProphecyPressureUpdate
NPCRelationshipDelta
FactionStateDelta
ArtifactEligibilityDelta
CreatureEligibilityDelta
DiagnosticNoOp
```

## Depends on accepted upstream phases

```text
Phase 8–9: branch reality foundation
Phase 10: player runtime state
Phase 11: worldstate and location mutation
Phase 12: quest/NPC/lore generation
Phase 14: ability/power engine
```
