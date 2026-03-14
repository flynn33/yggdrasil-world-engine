# Repository Implementation Mapping

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: authored Forsetti-aware repository mapping baseline

## Repository To Runtime Mapping

- `core/*`: planned first-party Forsetti service modules for truth ownership
- `modules/*`: planned Forsetti service modules for downstream manifestations
- `data/*`: canonical assets and schemas consumed by runtime services
- `lore/*`: reference material for canon and authoring
- `adapters/*`: downstream host-bridge specifications, not truth-owning runtime layers on main
- `docs/*`: architecture, governance, compliance, and handoff references

## Manifest Mapping

This branch stores planning manifests beside the runtime folders:
- `core/*/forsetti_module_manifest.template.json`
- `modules/*/forsetti_module_manifest.template.json`

Concrete Forsetti implementation branches may relocate those manifests into the resource layout their host build expects.

## Entry Point Mapping

Each runtime folder now defines a planned Forsetti entry point name in `engine_interface.json`. Those names are design targets for later implementation, not claims that executable module code already exists here.

## Adapter Mapping

Unity, Unreal, and Godot remain downstream execution connectors. In a Forsetti implementation they belong in host-specific app or bridge layers that consume YWE truth through public contracts.
