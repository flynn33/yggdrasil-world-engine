# Quest Reward Resolver Contract

## Purpose

The Quest Reward Resolver is the YWE system that converts quest completion into
structured consequence. It is not a loot dispenser and not an XP-only reward
system.

A quest result may change player state, branch reality, shared world truth,
location state, wolf companion state, plane/realm attunement, lineage resonance,
ability pressure, perception, myth, prophecy, NPC relationships, faction state,
artifact eligibility, creature eligibility, and future generation bias.

## Authority

The resolver operates inside YWE and is grounded in the ASH Model of the Universe.
It may use ASH Pattern System diagnostics and conformance envelopes, but the ASH
Pattern System remains a YWE stability/resilience component, not the topmost
cosmology.

## Inputs

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
NPC/Faction context
Artifact/Creature eligibility context
```

## Outputs

```text
QuestRewardResolutionPacket
ConsequenceResolutionPacket
RewardDeltaBundle
PlayerStateUpdatePacket
WorldstateDeltaPacket or DiagnosticNoOp
LocationMutationCandidate
LocationBranchOverlay update
WolfStateUpdatePacket
AbilityStateUpdatePacket
FutureGenerationBiasUpdate
MythSeedCandidate
ProphecyPressureUpdate
NPCRelationshipDelta
FactionStateDelta
ArtifactEligibilityDelta
CreatureEligibilityDelta
```

## Invariant

```text
No meaningful quest resolution may silently vanish. It must emit structured
consequence or an explicit DiagnosticNoOp.
```
