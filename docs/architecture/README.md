# Architecture Documentation

## Engine-First Architecture

The Yggdrasil World Engine is organized as an engine-first architecture. ASH defines upstream mathematical and generative authority; YWE interprets and manifests ASH-derived truth through code-agnostic engine contracts. Additional systems are implemented as separate engines/modules.

The controlling authority chain is:

```text
ASH Pattern System
  -> Yggdrasil World Engine
    -> YWE game systems / feature engines
      -> platform-specific runtime implementations
```

The canonical upstream authority contract is
`ash_upstream_authority_contract.md`.

## Repository Baseline Authority

Before applying downstream architecture guidance, keep the original repository
baseline in view:

- `../master_specification/YWE_MASTER_SPECIFICATION.md` -- foundational engine-first design and canonical cosmology baseline
- `../../YWE_REPOSITORY_BOOTSTRAP_PROMPT.md` -- repository structure and scaffolding baseline paired with the master specification

## Core Engines

| Engine | Purpose |
|--------|---------|
| Cosmology Engine | Origin of gravity, reality, and the nine realms |
| Realm Engine | Fixed cosmological state management and player attunement |
| ASH Pattern Engine | ASH-derived state, diagnostics, codeword traces, and generation planning |
| Narrative Engine | Player-specific interpretation, story transformation, and memory |
| Perception Engine | Player perception overlay based on cosmic state |

## Expansion Engines (Modules)

| Module | Purpose |
|--------|---------|
| Quest Engine | Quest generation from cosmic patterns |
| Myth Engine | Myth formation from significant events |
| Prophecy Engine | Future narrative attractors and probability weights |
| Artifact Engine | Artifact generation and management |
| Creature Engine | Creature generation and behavior |

## Future Expansion Engines

The architecture supports additional engines:
- Civilization Engine
- Economy Engine
- Religion Engine
- Faction Engine
- Politics Engine

All expansion engines must consume ASH-derived pattern output through YWE
interpretation contracts. No module may generate meaningful content
independently.

## Control Documents

- `ash_upstream_authority_contract.md` -- Canonical ASH upstream mathematical and generative authority contract for YWE
- `ash_downstream_contract.md` -- Downstream consumption contract subordinate to the upstream authority contract
- `authored_override_and_tooling_notes.md` -- Canonical authored override authority order, allowed/forbidden override categories, and tooling guardrails
- `realm_truth_boundary_contract.md` -- Canonical separation contract for realm truth, perception, myth, prophecy, faction claims, and authored overrides

## Canonical Data Companions

- `../data/perception/perception_overlay_rules.yaml` -- Perception-layer truth-boundary rules
- `../data/realm/realm_mechanics_rules.yaml` -- Realm-law and attunement rules
- `../data/realm/realm_boundary_profiles.yaml` -- Boundary profile catalog for lawful threshold behavior
- `../data/realm/realm_transition_examples.yaml` -- Lawful and unlawful transition examples
- `../data/module_capability/module_capability_manifest_schema.yaml` -- Module capability, delegation, and suppression governance schema
- `../data/module_capability/manifests/*.yaml` -- Applied canonical capability declarations for current YWE engines and modules
- `../data/faction_topology/faction_topology_state_schema.yaml` -- Faction topology state schema

## Dependency Direction

All modules consume ASH-derived state, diagnostics, codeword traces, generation
plans, and YWE interpretation packets. The dependency flow is:

```
ASH Pattern System
  -> Yggdrasil World Engine
    -> Core truth services
      -> Feature manifestation services
        -> host adapters
```

No reverse dependencies. No circular dependencies.

Host adapters materialize approved manifests but do not author symbolic truth.
