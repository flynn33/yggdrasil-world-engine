# Prophecy Engine -- Module Description

## Responsibility

Generate and track prophecies that act as future narrative attractors. Prophecies adjust the probability weights of cosmic patterns, making certain events more likely to manifest.

## Inputs

- `PatternNode[]` from ASH Pattern Engine
- `PlayerState` including bloodline resonance and attunement
- `MythRecord[]` from Myth Engine (repeated participation tracking)

## Outputs

- `Prophecy` -- generated prophecy with conditions and status
- Pattern weight adjustments fed back to ASH Pattern Engine
- Prophecy activation events

## Rules

1. Prophecies are probability weights, not fixed scripts.
2. Prophecy generation derives from ASH patterns.
3. Prophecies influence future pattern emergence through weight adjustment.
4. Prophecy activation is triggered by matching cosmic conditions.

## Prophecy Schema

```json
{
  "prophecy_id": "PR_0082",
  "condition": "shadow_gate_pattern",
  "status": "dormant"
}
```

Status values: `dormant`, `active`, `fulfilled`, `broken`
