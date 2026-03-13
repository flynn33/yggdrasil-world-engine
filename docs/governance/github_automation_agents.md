# GitHub Automation Agents

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: automation baseline

## Purpose

This document describes the GitHub automation added to this repository for release governance and Forsetti compliance enforcement.

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
