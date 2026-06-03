# Companion Presence Model Contract

## Purpose

Define how companion presence is represented in YWE runtime logic.

## Core Law

```text
Raven = constant witness / persistent companion.
Wolves = conditional threshold presences.
```

## Companion Presence Classes

| Class | Runtime Rule | Examples |
|---|---|---|
| `persistent_player_bound_companion` | Always attached to player runtime state | Raven Companion |
| `conditional_manifestation_companion` | Appears only when criteria are met | White Wolf, Dark Wolf |

## Persistent Companion Axis

The Raven Companion is always with the player at the runtime-state level.

The Raven Companion may be:

```text
visible
perched nearby
airborne
offscreen
noninteractive for presentation
temporarily separated by explicit story-state
```

But the Raven Companion is not absent from player runtime state unless an explicit story-state marks the exception.

## Conditional Companion Axis

The White Wolf and Dark Wolf are conditional companion manifestations. Their presence must be justified by a manifestable trigger and duration.

Valid trigger sources include:

```text
quest requirement
branch event threshold
location threshold state
wolf resonance condition
myth pressure
prophecy pressure
combat/encounter pressure
ability unlock or use state
dream or vision sequence
```

## Forbidden Interpretations

```text
Raven as generic pet
Raven as optional cosmetic familiar
Wolves as default party members
Wolves as morality meters
Wolves as good/evil UI choices
Wolves as permanently losable pets
```
