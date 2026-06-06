# Ravenfall Gate Location Mutation Plan

Status: `phase_16_recovery`

## Mutation phases

```text
ravenfall_gate.unawakened
ravenfall_gate.oath_discovered
ravenfall_gate.oath_revealed
ravenfall_gate.oath_concealed
ravenfall_gate.oath_bound
ravenfall_gate.oath_studied_unresolved
ravenfall_gate.oath_weaponized
ravenfall_gate.threshold_awakened
ravenfall_gate.shadow_contained
ravenfall_gate.mythic_site
ravenfall_gate.prophecy_charged
```

## Required mutation inputs

```text
player choice
branch event
player runtime state
wolf companion state
ability use context
worldstate delta packet
quest reward resolution packet
future generation bias update
```

## Rule

Every meaningful mutation must have a `WorldstateDeltaPacket` or `DiagnosticNoOp`.
