# YWE Canonical Data Domains

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: authored canonical data-domain baseline

## Purpose

This document defines which folders under `data/` are canonical YWE truth assets and how they participate in a Forsetti-compatible design.

## Data Domains

- `data/realm_registry`: canonical realm list and realm ontology anchors
- `data/realm`: canonical realm-law, boundary-profile, and transition-rule assets
- `data/module_capability`: canonical module capability and delegation-governance schemas
- `data/pattern_archetypes`: symbolic grammar and pattern references
- `data/quest_archetypes`: quest seed and quest structure references
- `data/faction_topology`: faction topology, claim, succession, and relational collective-state schemas
- `data/perception`: canonical perception overlay and truth-boundary rule assets
- `data/myth_archetypes`: myth record structures
- `data/bloodline_registry`: bloodline resonance data
- `data/schemas`: shared payload, persistence, and state contracts
- `data/validation`: guardrail contracts, required artifact manifests, and check specifications for package-scoped acceptance gates

## Runtime Rule

These domains are consumed by runtime modules, but they are not independent Forsetti modules. In a concrete implementation they should ship as assets or shared read-only resources behind public service contracts.

## Governance Rule

Changes to canonical data domains must preserve:
- ASH-first generation
- fixed cosmology
- multiplayer-safe perception divergence
- player runtime state updates through controlled update packets
- Forsetti lifecycle governance without external truth transfer
- the split where Forsetti governs activation and YWE governs truth
