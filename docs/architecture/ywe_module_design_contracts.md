# YWE Module Design Contracts

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: Forsetti-compatible module baseline

## Core Truth Services

- `com.ywe.core.cosmology-engine`: planned `service` module for cosmology canon and realm ontology anchors.
- `com.ywe.core.realm-engine`: planned `service` module for attunement and lawful realm access.
- `com.ywe.core.ash-pattern-engine`: planned `service` module for ASH-derived pattern detection.
- `com.ywe.core.narrative-engine`: planned `service` module for interpretation, quest pressure, and consequence routing.
- `com.ywe.core.perception-engine`: planned `service` module for multiplayer-safe divergence without rewriting shared truth.

## Feature Manifestation Services

- `com.ywe.module.quest-engine`: planned `service` module for quest chains and quest state transitions.
- `com.ywe.module.myth-engine`: planned `service` module for myth seeds, myth records, and faction versions.
- `com.ywe.module.prophecy-engine`: planned `service` module for prophecy weighting and activation pressure.
- `com.ywe.module.artifact-engine`: planned `service` module for artifact manifestations.
- `com.ywe.module.creature-engine`: planned `service` module for creature manifestations.

## Adapter Position

- Unity, Unreal, and Godot remain downstream execution connectors.
- In a Forsetti implementation, they belong in platform-specific host or app layers.
- They must never become sources of canonical YWE truth.

## Shared Rules

- modules activate through Forsetti lifecycle rules
- modules communicate through framework-mediated channels only
- direct runtime dependencies remain one-way
- peer awareness may exist through events, not direct ownership inversion
- truth-sensitive responsibilities must be declared as non-delegable even when realization support is delegable-compatible
- suppression conditions may defer activation but may not transfer YWE truth ownership to adapters or external environments
- truth modules never request framework-reserved `ui_theme_mask`
