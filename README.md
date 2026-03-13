# Yggdrasil World Engine (YWE)

Yggdrasil World Engine is a cosmology-driven narrative simulation engine built to turn ASH-derived symbolic state into quests, consequence, myth, prophecy, and perception-safe multiplayer narrative divergence.

It is designed as a code-agnostic, engine-agnostic system architecture operating inside the Forsetti Framework.

## Why YWE Exists

YWE exists to transform symbolic state into living narrative pressure without collapsing into a generic procedural RPG generator. Its purpose is to preserve canonical cosmology while creating consequence, myth, prophecy, perception divergence, and future narrative possibility from ASH-detected patterns.

## Core Design Law

~~~text
ASH State -> Pattern Detection -> Narrative Interpretation -> Quest Manifestation
~~~

All meaningful procedural content must derive from ASH Pattern Detection. No independent random generator may own meaningful content generation.

## Engine-First Architecture

YWE separates universal truth engines from downstream manifestation systems.

- Core truth engines: cosmology, realm, ASH pattern, narrative, and perception.
- Feature modules: quest, myth, prophecy, artifact, and creature systems that consume core truth.
- Shared data: schemas, registries, and archetypes that define canonical structures.
- Lore and docs: canonical reference material, contracts, governance, and handoff guidance.

## Forsetti Relationship

YWE exists inside the Forsetti Framework. Forsetti governs activation; YWE governs truth. External hosts negotiate execution, but they do not own canonical cosmology, player identity doctrine, myth, prophecy, or perception truth.

## Forsetti Compliance Profile

This branch stays code-agnostic, but it is now structured so a later Forsetti implementation can bind to it cleanly:

- core and feature runtime systems are planned as manifest-driven Forsetti service modules
- runtime communication is expected to flow through Forsetti context surfaces such as the service container and event bus
- compatibility and entitlement checks gate activation; they do not redefine YWE truth
- no YWE module may request the framework-reserved `ui_theme_mask` capability
- future UI or host-bridge modules belong in platform-specific implementation branches, not in the truth-owning core of this repository

## Supported External Environments

Adapter scaffolding is provided for Unity, Unreal, and Godot as downstream execution connectors. These adapters expose environment capabilities and realization paths without redefining YWE logic.

## Truth Engines vs. Execution Connectors

Core engines and data domains are authoritative for YWE truth. Adapters remain downstream bridges that realize outputs in host environments. They may instantiate content, but they may not redefine fixed realms, wolf doctrine, player-origin rules, myth systems, or prophecy systems.

## GitHub Automation

This repository includes GitHub automation for:

- version tracking through `VERSION`
- changelog maintenance in `CHANGELOG.md`
- wiki synchronization from selected docs
- Forsetti compliance checks on pushes and pull requests
