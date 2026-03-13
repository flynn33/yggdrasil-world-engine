# pattern archetypes Data Domain

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical ASH domain index

## Purpose
Explains the ASH symbolic grammar assets stored in `data/pattern_archetypes` and how they function as canonical YWE data.

## Canonical contents

This domain now holds:

- the shared ASH registry schema
- character, region, faction, transformation, event, and cluster registries
- the derived compatibility matrix
- archetype evaluation and generation rules
- the base `pattern_schema.json` reference

Quest-family ASH registries remain in `data/quest_archetypes/` by repository design, but they are governed by the same ASH authority stack.

## Authority chain

Use these together:

- `docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md`
- `ash_pattern_registry_schema.yaml`
- `docs/architecture/ash_downstream_contract.md`

## Inputs
- canonical ASH prose authority
- shared schema contract
- locked YWE canon and invariants

## Outputs
- machine-readable symbolic grammar
- relationship and weighting references
- downstream-safe ASH evaluation inputs

## Dependencies
- core ASH pattern detection
- narrative interpretation
- downstream module design contracts

## Invariants
- all meaningful generation must remain ASH-derived
- symbolic grammar must remain centralized rather than cloned downstream
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
