# Contributing to Yggdrasil World Engine

Thank you for your interest in contributing to the Yggdrasil World Engine.

## Contributor License Agreement (CLA)

All contributors must agree to the Contributor License Agreement before any contribution can be merged. By submitting a pull request, you agree to the terms outlined in [CLA.md](CLA.md).

## Branch Model

- **main**: The sealed, code-agnostic specification. Contains contracts, schemas, documentation, and governance. No engine-specific code.
- **Engine branches** (e.g., `unity`, `unreal`, `godot`): Engine-specific implementations. These do not merge with `main`.

## How to Contribute

### Specification Changes (main branch)

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make your changes following the Forsetti Framework principles (see `guide.md`).
4. Ensure all validation scripts pass: `bash scripts/run_checks.sh`
5. Open a pull request against `main`.

### Engine Implementations (engine branches)

1. Fork the repository.
2. Create a feature branch from the appropriate engine branch.
3. Implement against the contracts defined in `core/*/engine_interface.json`.
4. Use native engine idioms (C# for Unity, C++ for Unreal, GDScript for Godot).
5. Open a pull request against the engine branch.

## Rules

- Do not invent systems outside the master specification.
- Do not alter cosmology rules or ASH compliance invariants.
- All procedural systems must derive from ASH Pattern Detection.
- Follow the Forsetti Framework principles documented in `guide.md`.
- Run validation scripts before submitting any pull request.

## Code of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md). GitHub Discussions are subject to automated moderation for racist, vulgar, profane, threatening, or harassing content.
