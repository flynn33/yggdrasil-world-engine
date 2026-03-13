# GitHub Automation Agents

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: expanded automation governance baseline

## Purpose

This document describes the GitHub automation added to this repository for release governance, design validation, and Forsetti-aligned repository enforcement.

## Release Governance Agent

The release-governance workflow is responsible for:
- maintaining `VERSION`
- prepending entries to `CHANGELOG.md`
- syncing selected repository docs into the GitHub wiki when the wiki is available

Versioning policy:
- `BREAKING CHANGE` or `!:` bumps major
- `feat:` bumps minor
- all other pushed commits bump patch
- `[skip version]` or `[skip release]` disables the automatic bump for that push

## Forsetti Compliance Agent

The compliance workflow validates that pushed changes still respect the repository's Forsetti alignment rules.

It checks:
- required governance and architecture docs still exist
- every core and feature runtime folder still has a Forsetti manifest template
- manifest templates keep required fields and do not request `ui_theme_mask`
- core runtime dependencies do not point at feature modules
- feature runtime dependencies point only at core runtime modules
- adapter capability profiles preserve their non-truth-owning host-bridge role

## Wiki Sync Behavior

The wiki sync step updates a curated set of wiki pages from repository sources. If the GitHub wiki is not enabled, the sync step exits cleanly without failing the workflow.

## Source Completeness Agent

The source-completeness workflow refreshes `docs/handoff/missing_source_documents.md` from the tracked placeholder inventory in `SOURCE_AVAILABILITY_MANIFEST.md`.

It:
- preserves the manually authored context in the report
- regenerates the `Still Placeholder-Backed` section from repository truth
- auto-commits the refreshed inventory on `main` when the placeholder set changes

## Schema Integrity Agent

The schema-integrity workflow validates canonical JSON contracts across `data/` with extra focus on `data/schemas/`.

It checks:
- file naming conventions for shared schema files
- required fields in player, prophecy, myth, pattern, quest, bloodline, and realm records
- placeholder expansion schema structure
- cross-file dependency references for shared schema expansions

## Module Contract Coverage Agent

The module-contract-coverage workflow validates that each planned runtime folder still carries the full documentation and contract scaffold expected for a code-agnostic design branch.

It checks:
- required core and feature runtime directories are present
- every runtime folder includes `README.md`, `module_description.md`, `schema_notes.md`, `engine_interface.json`, and `forsetti_module_manifest.template.json`
- special rule and schema companion files remain present where required
- contract markdown files preserve core sections such as Purpose, Inputs, Outputs, Dependencies, and Invariants

## Docs Link And Glossary Agent

The docs-link-and-glossary workflow validates repository documentation hygiene.

It checks:
- internal markdown links resolve
- sandbox-only handoff links do not remain in repository docs
- wiki sync mappings reference real source files and unique destination pages
- the design glossary still contains required canonical terms

## Architecture Drift Agent

The architecture-drift workflow guards against design changes landing without their companion documentation updates.

It requires related documentation updates when:
- runtime interface contracts or manifest templates change
- canonical schemas or realm registry files change
- core and feature rule files change
- adapter capability profiles change

## Canonical Truth Boundary Agent

The canonical-truth-boundary workflow enforces the split between YWE truth ownership and downstream host realization.

It checks:
- governance and architecture docs preserve the rule that Forsetti governs activation while YWE governs truth
- adapter profiles remain non-truth-owning downstream execution connectors
- adapter docs continue to describe host work as realization rather than canon authorship

## Release Readiness Agent

The release-readiness workflow is a final gate for tagged or manually requested release checks.

It verifies:
- version and changelog state are coherent
- the missing source inventory is current
- wiki sync configuration is intact
- the repository passes the Forsetti, schema, module, docs, and truth-boundary checks

## Operating Notes

- workflow-authored commits use `github-actions[bot]`
- automation commits that should not cause release bumps include `[skip version]`
- validation agents fail fast when design structure drifts; they do not invent or rewrite canon on their own
