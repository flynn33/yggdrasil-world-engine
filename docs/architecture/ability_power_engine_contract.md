# Ability / Power Engine Contract

## Purpose

The Ability / Power Engine defines how abilities emerge, unlock, stabilize, transform, decohere, and affect play within the Yggdrasil World Engine.

Abilities are consequence-born manifestations of the player's path. They are not generic skill-tree purchases.

## Authority

```text
ASH Model of the Universe
  -> foundation for simulation ontology and consequence logic
Yggdrasil World Engine
  -> agnostic engine framework
ASH Pattern System
  -> component for diagnostics, recovery, containment, conformance, and patch/update stability
Where Ravens Wait: Eternal Reckoning
  -> game/narrative layer implementation
```

## Required inputs

```text
PlayerRuntimeState
PlayerAgentState
LeafBranchRealityState
PlaneAttunementState
LineageResonanceState
TwinWolfState
WorldstateDeltaPacket history
LocationStateRecord
Quest / NPC / Lore generation context
ArtifactBinding refs
Myth / Prophecy refs
ASP DiagnosticEnvelope refs
```

## Outputs

```text
AbilityState
AbilityUnlockPressure
AbilityManifest
AbilityStateUpdatePacket
AbilityConsequencePacket
AbilityUseContext
FutureGenerationBiasUpdate refs
```

## Invariants

```text
abilities_emerge_from_consequence
abilities_require_source_provenance
meaningful_ability_use_requires_consequence_handling
wolf_linked_abilities_do_not_encode_morality
wolves_are_companions_not_power_meters_only
wolf_decoherence_is_temporary
```
