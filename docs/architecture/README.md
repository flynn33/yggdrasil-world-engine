# Architecture Documentation

## Engine-First Architecture

The Yggdrasil World Engine is organized as an engine-first architecture. The ASH Cosmological Model defines the upstream foundation for YWE and its systems; YWE interprets and manifests that foundation through code-agnostic engine contracts. The ASH Pattern System is a YWE component that protects diagnostics, pattern integrity, recovery, containment, resilience, conformance, and update/patch stability.

Required first-read authority contracts:

- `ywe_cosmology_authority_contract.md` -- Current game/engine/foundation/component authority stack.
- `ash_pattern_system_component_contract.md` -- ASH Pattern System role inside YWE.
- `ash_upstream_authority_contract.md` -- Historical packet-spine authority contract, preserved as superseded component evidence where necessary.

Phase 9 runtime-cosmology foundation contracts:

- `runtime_cosmology_foundation_contract.md` -- Phase 9 foundation flow for base world ontology, branch events, diagnostics, and manifestation boundaries.
- `base_world_ontology_contract.md` -- Nine-plane substrate rules; planes are base ontology, not generated branch realities.
- `leaf_branch_reality_contract.md` -- Runtime-generated player branch reality rules and divergence boundaries.
- `branch_event_contract.md` -- Meaningful player-choice event contract for branch creation and bias updates.
- `existential_gameplay_kernel_contract.md` -- A1-A6 diagnostics and existence potential evaluation.
- `pattern_vector_runtime_contract.md` -- Runtime semantics for H, K, D, S, and L pattern vector components.

Phase 10 player-state contract:

- `player_runtime_state_v1.md` -- Canonical player-specific runtime state, runtime-state deltas, branch context references, and generation-context boundary rules.

Phase 11 worldstate and location mutation contract:

- `worldstate_location_mutation_v1.md` -- Canonical persistent consequence, scoped location mutation, worldstate commit records, diagnostic no-ops, and future-generation bias boundary rules.

The current controlling authority chain is:

```text
ASH Cosmological Model
  -> Yggdrasil World Engine
    -> ASH Pattern System component and YWE runtime systems
      -> YWE feature engines
        -> platform-specific runtime implementations
```

Earlier language that treated ASH Pattern System as the topmost authority is
superseded by `ywe_cosmology_authority_contract.md`.

Historical acceptance-marker note: earlier docs said "ASH defines upstream mathematical and generative authority." That marker is retained here only as superseded legacy wording for validator compatibility; current authority is defined by the ASH Cosmological Model foundation and the ASH Pattern System component role above.

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
- `ywe_cosmology_authority_contract.md` -- Current authority stack contract for the game layer, YWE, ASH Cosmological Model, and ASH Pattern System component
- `ash_pattern_system_component_contract.md` -- Component contract for ASH Pattern System diagnostics, recovery, containment, conformance, resilience, and patch/update stability
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

All modules consume ASH Cosmological Model-derived meaning through YWE
contracts and may use ASH Pattern System diagnostics, codeword traces,
generation plans, and YWE interpretation packets for stability. The dependency
flow is:

```
ASH Cosmological Model
  -> Yggdrasil World Engine
    -> ASH Pattern System component and core runtime services
      -> Feature manifestation services
        -> host adapters
```

No reverse dependencies. No circular dependencies.

Host adapters materialize approved manifests but do not author symbolic truth.

Phase 9 branch-reality dependency flow:

```text
ASH Cosmological Model
  -> YWE Runtime Cosmology Contracts
    -> Branch Reality Resolver
      -> Feature Engines

ASH Pattern System Component
  -> diagnostics, conformance, recovery, and containment support
```

Phase 10 player-runtime dependency flow:

```text
Leaf Branch Reality
  -> Player Runtime State
    -> YWEGenerationContextPacket.player_runtime_state_ref
      -> ASH-governed generation
```

Phase 11 worldstate-location dependency flow:

```text
Player Runtime State
  -> WorldstateDeltaPacket
    -> LocationMutationState
      -> FutureGenerationBiasUpdate
        -> YWEGenerationContextPacket
```
