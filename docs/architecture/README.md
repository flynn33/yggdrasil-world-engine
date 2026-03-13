# architecture Documentation Index

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: active architecture index

## Purpose
Introduces the canonical architecture documents that define YWE truth, system boundaries, and downstream consumption rules.

## Active ASH Authority

Use these files together as the active ASH symbolic grammar authority:

- `ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md`
- `ash_downstream_contract.md`
- `COMPATIBILITY_MATRIX_NOTES.md`
- `../data/pattern_archetypes/ash_pattern_registry_schema.yaml`

The older `ASH_PATTERN_ARCHETYPE_LIBRARY_V0_2.md` path is retained only as a deprecated compatibility redirect. Historical context belongs in `docs/history/`.

## Other Core Architecture References

This folder also contains:

- engine interface and Forsetti contract surfaces
- module design contracts
- canonical dependency and invariant guardrails
- specialized notes that explain how symbolic grammar becomes downstream runtime behavior

## Inputs
- canonical YWE cosmology and design law
- normalized ASH authority documents
- Forsetti governance alignment rules

## Outputs
- architecture-safe design references
- navigation for future design and implementation work
- boundary guidance for downstream modules and adapters

## Dependencies
- repository structure
- canonical data domains
- governance documentation

## Invariants
- all meaningful generation must remain ASH-derived
- fixed cosmology must remain locked
- perception must not rewrite shared-world truth
- Forsetti governs activation; YWE governs truth
