# Compatibility Matrix Notes

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: canonical interpretation notes

## Purpose

This document explains how `data/pattern_archetypes/compatibility_matrix.yaml`
should be read and maintained.

The compatibility matrix is a **derived reference**, not an independent source
of symbolic truth. Canonical meaning still lives in:

- `docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md`
- `data/pattern_archetypes/ash_pattern_registry_schema.yaml`
- the family-specific ASH registry files

## Relationship semantics

The matrix exposes three canonical relationship types:

- `compatible`: the paired pressures reinforce each other and can be co-selected
  without special justification
- `friction`: the paired pressures can coexist, but they should generate visible
  tension, cost, instability, or split interpretation
- `contradiction`: the paired pressures should not be combined casually and
  require an explicit higher-order design basis

The precedence order is:

```text
contradiction -> friction -> compatibility -> neutral
```

If a pair appears in multiple categories during maintenance, the stronger
category wins.

## Derivation rules

The matrix should be maintained by normalizing relationship fields already
present in the family registries:

- `compatible_with`
- `friction_with`
- `contradicts`

This means the matrix should not add novel symbolic meaning on its own.
Its job is to give downstream systems and maintainers a fast consolidated view
of relationship pressure.

## Intended downstream use

Downstream systems may use the matrix to:

- score lawful co-selection
- escalate friction when a narrative or social tension is desired
- reject accidental contradiction during content assembly
- inform cluster candidacy and symbolic coherence checks

Downstream systems must not use the matrix to:

- invent new archetype meaning
- flatten archetypes into generic tags
- override the canonical family registries
- convert friction or contradiction into random difficulty modifiers with no
  symbolic interpretation

## Relationship handling guidance

Compatibility should usually:

- increase co-selection likelihood
- strengthen cluster candidacy
- reinforce lawful manifestation hints

Friction should usually:

- remain visible in quest cost, myth retelling, prophecy ambiguity, or social
  consequence
- increase interpretive tension rather than silently cancel selection

Contradiction should usually:

- block casual pairing
- require explicit authored or generated justification
- remain legible if intentionally allowed

## Maintenance note

When family registries change, the matrix must be updated in the same commit.

If a future implementation adds automation for regenerating the matrix, that
automation should still treat the family registries as the primary authority.

## Invariants

- all meaningful generation must remain ASH-derived
- compatibility must remain symbolic rather than purely tactical
- friction must be a designed tension, not random noise
- contradiction must remain explicit and legible
- the matrix must not become a second authority separate from the canonical ASH
  registries
