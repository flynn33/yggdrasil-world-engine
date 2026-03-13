# quest archetypes Data Domain

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical ASH quest-family domain

## Purpose
Explains why `data/quest_archetypes` remains a separate repository domain while still participating in the normalized ASH symbolic grammar.

## Canonical contents

This domain stores:

- `quest_archetypes.yaml` as the quest-family ASH registry
- `quest_seed_schema.json` as the downstream quest seed reference

The shared ASH schema still lives in `data/pattern_archetypes/ash_pattern_registry_schema.yaml`.

## Relationship to ASH authority

`quest_archetypes.yaml` is part of the ASH family registry set even though it is stored outside `data/pattern_archetypes/`.

That split remains intentional:

- `data/pattern_archetypes/*` holds the broader symbolic grammar hub
- `data/quest_archetypes/*` keeps quest-shaped ASH data beside quest seed structures

## Inputs
- canonical ASH prose authority
- shared registry schema
- narrative and quest design contracts

## Outputs
- quest-family symbolic pressure records
- quest-shaped ASH inputs for downstream generation

## Dependencies
- ASH pattern detection
- narrative interpretation
- quest engine downstream contracts

## Invariants
- all meaningful generation must remain ASH-derived
- quest archetypes must stay part of the centralized ASH authority chain
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
