# Forsetti Governance Alignment

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: framework-aligned governance baseline

## Purpose

This document defines how YWE stays compatible with the attached Forsetti Framework - Windows branch while remaining code-agnostic on main.

## Forsetti Rules That Bind YWE

- runtime features must be expressed as modules
- discovery, validation, activation, and deactivation are manifest-driven
- activation requires compatibility approval and host-defined entitlement approval when applicable
- modules communicate through framework-mediated channels, not direct calls
- service modules may run concurrently
- only one UI module may be active at a time
- `ui_theme_mask` is reserved for framework use
- `forsetti.internal.*` is a reserved event namespace
- framework integrations must use public APIs only

## YWE Runtime Mapping

- `core/*` are planned first-party Forsetti service modules that own truth domains
- `modules/*` are planned Forsetti service modules that consume core truth and emit manifestations
- `adapters/*` are downstream bridge specifications; they do not become truth-owning modules in this branch
- `data/*`, `lore/*`, and `docs/*` are assets and references, not runtime modules

## Governance Split

- Forsetti governs activation, compatibility, entitlement, and host lifecycle
- YWE governs cosmology, realm truth, ASH pattern law, narrative truth, myth, prophecy, and perception rules
- host environments may realize YWE outputs but may not redefine YWE truth

## Branch Boundary

- this repository does not vendor Forsetti implementation files
- this repository remains MIT-licensed even though the attached Forsetti framework is proprietary
- compliance here means architectural compatibility, not code inclusion
- platform-specific Forsetti host code belongs in later implementation branches or companion repositories

## Required Outcome

Any future Forsetti implementation of YWE should be able to:
- register YWE runtime modules through manifests
- activate them through Forsetti lifecycle rules
- communicate through the Forsetti context, service container, and event bus
- preserve the rule that Forsetti governs activation while YWE governs truth
