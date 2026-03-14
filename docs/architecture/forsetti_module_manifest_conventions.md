# Forsetti Module Manifest Conventions

Date: 2026-03-13
Project: Yggdrasil World Engine
Status: authored manifest convention baseline

## Purpose

This document explains how the code-agnostic YWE branch stores Forsetti-ready manifest templates without pretending the Windows host implementation already exists here.

## Template Locations

- `core/*/forsetti_module_manifest.template.json`
- `modules/*/forsetti_module_manifest.template.json`

## Naming Rules

- module IDs use reverse-domain naming under `com.ywe.*`
- core truth services use `com.ywe.core.*`
- feature manifestation services use `com.ywe.module.*`
- entry point names use PascalCase and end with `Module`

## Required Fields

- `schemaVersion`
- `moduleID`
- `displayName`
- `moduleVersion`
- `moduleType`
- `supportedPlatforms`
- `minForsettiVersion`
- `entryPoint`

## Template Defaults In This Branch

- schema version `1.0`
- planning module version `0.1.0`
- planning minimum Forsetti version `0.1.0`
- empty capability requests until a platform branch chooses concrete bindings
- `null` entitlement product IDs unless a host later gates the module

## Reserved Capability Rule

No YWE manifest template may request `ui_theme_mask`.
