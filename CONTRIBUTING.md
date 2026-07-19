# Contributing to Yggdrasil World Engine

Thank you for your interest in contributing to the Yggdrasil World Engine.

## Contributor License Agreement (CLA)

All contributors must agree to the Contributor License Agreement before any contribution can be merged. By submitting a pull request, you agree to the terms outlined in [CLA.md](CLA.md).

## Repository and Branch Model

- **All branches in this repository**: Agnostic specification work only. A branch name never activates platform implementation mode.
- **Downstream platform repositories**: Concrete Unity, Unreal, Godot, or other product implementations may begin only after M10 acceptance and explicit platform authorization.

## How to Contribute

### Specification Changes (main branch)

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make your changes following the Forsetti Framework principles (see `guide.md`).
4. Ensure all validation scripts pass: `bash scripts/run_checks.sh`
5. Open a pull request against `main`.

### Engine Implementations (separate downstream repositories after M10)

1. Use a separately authorized downstream platform repository.
2. Create a feature branch in that downstream repository.
3. Implement against the contracts defined in `core/*/engine_interface.json`.
4. Use native engine idioms (C# for Unity, C++ for Unreal, GDScript for Godot).
5. Open a pull request against that downstream repository.

## Rules

- Do not invent systems outside the master specification.
- Do not alter cosmology rules or ASH compliance invariants.
- All procedural systems must derive from ASH Pattern Detection.
- Follow the Forsetti Framework principles documented in `guide.md`.
- Run validation scripts before submitting any pull request.

## Code of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).
