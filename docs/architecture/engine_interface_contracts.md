# Engine Interface Contracts

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: Forsetti-compatible interface baseline

## Purpose

This document defines the shared runtime contract every future YWE module must satisfy inside Forsetti.

## Shared Contract

Every YWE runtime module must be representable as a Forsetti module with:
- a manifest using schema version `1.0`
- a module descriptor
- a start and stop lifecycle
- public service or event contracts exposed through framework-approved channels only

## Required Manifest Fields

- `schemaVersion`
- `moduleID`
- `displayName`
- `moduleVersion`
- `moduleType`
- `supportedPlatforms`
- `minForsettiVersion`
- `entryPoint`

## YWE Module Type Policy

- core engines map to Forsetti `service` modules
- feature modules map to Forsetti `service` modules
- any future presentation surface maps to a Forsetti `ui` module only in a platform branch
- host bridges may map to Forsetti `app` modules or host-layer integrations outside this branch

## Communication Policy

Allowed channels:
- Forsetti service container
- Forsetti event bus
- Forsetti logger
- overlay router only for explicitly authorized UI-capable modules

Forbidden channels:
- direct module-to-module calls as an integration requirement
- self-messaging as control flow
- reserved `forsetti.internal.*` namespace usage
- requesting `ui_theme_mask`

## Branch Implementation Rule

This repository stores manifest templates beside the runtime design folders:
- `core/*/forsetti_module_manifest.template.json`
- `modules/*/forsetti_module_manifest.template.json`

Those files are planning artifacts for later Forsetti implementation work; they are not claims that the Windows host code already exists here.
