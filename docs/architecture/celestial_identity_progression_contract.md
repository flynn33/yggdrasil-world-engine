# Celestial Identity Progression Contract

## Purpose

This contract defines how the player's deeper celestial identity is represented and revealed over time.

## Core invariant

```text
The player begins with veiled celestial identity.
Celestial identity is revealed through play, not selected up front.
```

## Identity layers

```text
mortal_identity
  -> the player's lived incarnation

celestial_identity
  -> deeper pattern, initially veiled

primordial_or_architectural_identity
  -> optional late/endgame pattern layer, if applicable
```

## Reveal states

Allowed states:

```text
veiled
suspected
fragmented
named_fragment
partial_revelation
coherent_revelation
integrated
```

Initial state:

```text
veiled
```

## Reveal evidence

Identity progression requires evidence such as:

```text
branch_event_refs
player_action_trace_refs
bloodline_resonance_refs
wolf_resonance_event_refs
plane_attunement_threshold_refs
myth_participation_refs
prophecy_pressure_refs
artifact_binding_refs
location_threshold_refs
axiom_diagnostic_refs
```

## Forbidden

```text
full_celestial_identity_at_character_creation
class_selection_as_celestial_identity
identity_reveal_without_provenance
identity_reveal_without_player_history
platform_adapter_authored_identity
```

## Relationship to celestial name generation

The celestial name generator may support identity flavor, seed values, epithets, or eventual reveal text.

It does not override the cosmological identity progression contract.

## Relationship to Player Runtime State

The Player Runtime State must reference CelestialIdentityState, not embed all celestial identity logic directly.
