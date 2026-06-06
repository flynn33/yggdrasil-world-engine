# Vertical Slice Acceptance Contract

Defines how a YWE vertical slice is accepted at the agnostic design layer.

## Acceptance principle

A vertical slice is accepted when it demonstrates a complete consequence loop across player choice, branch reality, player state, worldstate, location state, companion behavior, ability use, content signals, and future generation bias.

## Required evidence

- At least one trace for every declared completion mode.
- Choice-to-consequence linkage.
- Quest Reward Resolver reference.
- WorldstateDeltaPacket or DiagnosticNoOp references.
- Location mutation or justified no-op.
- Wolf companion trace.
- Ability/combat trace where required.
- NPC/faction/lore/myth/prophecy signals where applicable.
- FutureGenerationBiasUpdate reference or justified no-op.

## Forbidden acceptance shortcuts

- Accepting a slice based only on quest-complete flags.
- Accepting a static location model.
- Accepting static branch-map shortcuts as the primary model.
- Accepting platform-specific runtime details as proof of engine design.
