# Product Runtime Boundary Contract

## Purpose

This contract separates the agnostic YWE repository from future platform-specific product/runtime repositories.

Scope note: the named game layer below is an informative cross-scope routing
example only. It does not establish YWE Core behavior; authority remains with
`docs/architecture/ywe_core_wrw_scope_contract.md`.

## Authority Chain

```text
ASH Model of the Universe
  -> Yggdrasil World Engine agnostic logic
    -> Where Ravens Wait: Eternal Reckoning game layer
      -> native macOS runtime implementation
```

## YWE Repository Owns

```text
agnostic engine contracts
system logic
rule models
schemas
validation specs
example manifests
feature-engine relationships
consequence packet definitions
generation and interpretation boundaries
platform adapter contracts
```

## Product Runtime Repository Owns

```text
Swift implementation
Metal rendering
SwiftUI / AppKit presentation
GameController input integration
macOS persistence implementation
audio playback implementation
platform asset pipeline
platform build and distribution
performance optimization
```

## Materialization Rule

A platform runtime may materialize YWE outputs. It must not author symbolic truth, redefine ASH Model cosmology, redefine ASH Pattern System math, or invent untracked gameplay consequences.

## Completion Standard

The agnostic YWE repository is platform-ready only when a product runtime team can implement materialization without inventing missing core systems.
