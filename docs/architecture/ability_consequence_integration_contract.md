# Ability Consequence Integration Contract

Ability use can change the world, branch, player state, location state, NPC relationships, myth pressure, prophecy pressure, or future generation bias.

## Required consequence classification

Meaningful ability use must emit at least one:

```text
AbilityConsequencePacket
WorldstateDeltaPacket
DiagnosticNoOp
PlayerStateUpdatePacket
FutureGenerationBiasUpdate
LocationMutationCandidate
QuestProgressSignal
NPCRelationshipChange
MythSeedCandidate
ProphecyPressureUpdate
WolfCoherenceEvent
```

## Forbidden

```text
significant ability use with no record
location mutation without provenance
branch mutation without branch context
wolf decoherence without recovery path
```
