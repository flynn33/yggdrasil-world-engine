# Realm Engine

The Realm Engine manages the nine fixed cosmological states and player resonance with those realms.

## Purpose

Realms are fixed cosmological states. Players do not move the realms -- players change resonance with realms. The Realm Engine manages realm definitions, attunement tracking, realm shift conditions, and thin veil locations.

## Canonical Realms

| Realm | Meaning |
|-------|---------|
| Divine Core | Origin of gravity and reality |
| Celestial | Order, creation |
| Causal | Law, fate |
| Mental | Cognition |
| Astral | Energetic patterns |
| Etheric | Life force |
| Physical | Material world |
| Shadow | Hidden truths |
| Void | Dissolution |

## Realm Travel Rules

- Players start in the **Physical Realm**
- Travel to other realms requires: `Realm Attunement >= Threshold` AND `Thin Veil Location`
- Players always have access to the Physical Realm
- Players may activate realm-aligned abilities while remaining in the Physical Realm

## Dependencies

- Cosmology Engine (realm definitions)

## Files

- `realm_schema.json` -- Data schema for realm state
- `engine_interface.json` -- Interface definition for implementations
- `../../data/realm/realm_mechanics_rules.yaml` -- Canonical realm-law rules for boundaries, attunement, and transitions
