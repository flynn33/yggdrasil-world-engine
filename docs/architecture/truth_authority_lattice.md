# Truth and Authority Lattice

Status: canonical M1 authority contract
Version: 1.0.0
Machine-readable authority: `data/governance/truth_authority_lattice.json`
Schema: `data/schemas/truth_authority_lattice_schema.json`
Requirements: `YWE-REQ-0009`, `YWE-REQ-0010`, `YWE-REQ-0014`,
`YWE-REQ-0015`, `YWE-REQ-0016`

## Purpose

This contract defines who may author each kind of truth, how lower scopes may
derive from higher scopes, and which records may change at runtime. Authority
is a partial order: a lower layer may specialize, interpret, or materialize an
upstream decision only within its declared scope.

## Lattice Nodes

| Node | Kind | Owns | Cannot do |
|---|---|---|---|
| `ash_cosmological_model` | Source authority | Cosmological and mathematical foundation, ontology meaning, axioms, existence potential, pattern-vector and symbolic-grammar meaning, branching foundations | Be redefined by YWE, WRW, a feature engine, or a host |
| `ywe_core` | Normative authority | Setting-neutral engine contracts, truth scopes, state and delta rules, deterministic interpretation, provenance, diagnostics, and extension boundaries | Redefine ASH or require WRW-specific identities as universal behavior |
| `ywe_extension_profile` | Optional normative authority | Setting-neutral optional capability contracts | Weaken Core or become mandatory without an explicit Core revision |
| `wrw_reference_profile` | Profile authority | WRW canon, named content, campaign rules, and profile specializations | Override ASH or Core, or universalize WRW story content |
| `shared_worldstate` | Objective state | Committed facts shared by the governing world context | Rewrite ontology, contracts, profile canon, or localize itself silently |
| `branch_local_state` | Objective scoped state | Committed facts within one leaf branch | Escape its branch scope or override shared truth without an accepted transition |
| `player_local_state` | Objective scoped state | Committed facts local to one player | Escape its player scope or override branch/shared truth |
| `perception_social_interpretation` | Derived interpretation | Perception, myth, prophecy pressure, and faction claims | Author objective state by interpretation alone |
| `host_materialization` | Derived realization | Rendering, input, storage, networking, and execution of approved state | Author ASH, Core, WRW, or committed runtime truth |
| `forsetti_lifecycle_governance` | Orthogonal lifecycle governance | Activation, module lifecycle, and external execution negotiation | Acquire or override truth ownership |

The ASH Pattern System is a YWE component for pattern integrity, diagnostics,
recovery, containment, conformance, resilience, and update safety. It protects
the authority chain; it is not a separate layer above the ASH Cosmological
Model and does not own symbolic meaning.

Forsetti lifecycle governance is orthogonal to the truth-authority order. It
may govern whether and how a module is activated without changing what that
module's authoritative contracts mean.

Relationship arrows use `source_node -> target_node`. `constrains` means the
source bounds the target; `specializes` means the target is a scoped
specialization of the source; `records_within` means the target records state
under source contracts; `projects_to` derives a non-objective view;
`materializes` realizes approved state; and `governs_activation` applies only
Forsetti lifecycle control.

## Symbolic-Grammar Ownership

The ASH Cosmological Model owns canonical symbolic meaning and the archetypal
grammar from which YWE interpretation begins. YWE owns deterministic contracts
that consume that grammar and route it into engine state and manifestations.
The ASH Pattern System component validates and stabilizes those operations.
WRW specializes the grammar into game content. No downstream subsystem may
create an independent symbolic-grammar authority.

## Truth Scopes

| Truth scope | Mutability | Governing authority | Lawful change or derivation |
|---|---|---|---|
| `base_world_ontology` | Immutable at runtime | ASH Cosmological Model, consumed by YWE Core | Governance-controlled dependency revision only; never a player or worldstate delta |
| `ywe_normative_contract` | Immutable at runtime | YWE Core | Reviewed governance change with durable rationale |
| `extension_profile_contract` | Immutable at runtime | YWE extension profile | Reviewed extension-profile change that remains subordinate to ASH and Core |
| `wrw_reference_canon` | Immutable at runtime | WRW reference profile | Reviewed profile canon change that remains subordinate to ASH and Core |
| `shared_worldstate` | Mutable scoped state | `shared_worldstate` under YWE Core contracts | Accepted append-only worldstate delta with provenance |
| `leaf_branch_state` | Mutable scoped state | `branch_local_state` under YWE Core contracts | Accepted branch event and append-only delta within one leaf branch |
| `player_state` | Mutable scoped state | `player_local_state` under YWE Core contracts | Accepted player-state update packet and provenance |
| `player_perception` | Derived observer view | `perception_social_interpretation` | Recomputed overlay from authoritative state; cannot itself mutate objective state |
| `mythic_interpretation` | Derived social interpretation | `perception_social_interpretation` | Evidence-linked interpretation; not raw history |
| `prophetic_pressure` | Derived future pressure | `perception_social_interpretation` | Weighted attractor; not a guaranteed script |
| `faction_claim` | Derived actor claim | `perception_social_interpretation` | Claim with source and visibility; not objective truth by assertion |
| `host_materialization` | Derived presentation | `host_materialization` | Presentation only; cannot author source truth |
| `diagnostic_noop` | Append-only evaluation record | YWE Core and ASH Pattern System component contracts | Records evaluated non-mutation with diagnostic provenance |

## Lattice Laws

A lower truth-authority layer MUST NOT overwrite a higher layer's constraints.
[YWE-REQ-0014]

1. Higher-precedence authority constrains lower-precedence specialization.
2. Lower-precedence evidence may reveal a defect but cannot silently rewrite a
   higher-precedence contract.
3. Immutable ontology defines what can exist; mutable worldstate records what
   is currently true within an authorized scope.
4. Event history is append-only. A reversible current-state effect is changed
   by a later compensating delta, never by erasing the earlier event.
5. Perception, myth, prophecy, faction claims, and host presentation are
   derived views. None becomes objective worldstate without an accepted state
   transition under the governing contract.
6. A branch-local or player-local fact cannot escape its scope by omission of a
   scope label.
7. WRW evidence may validate Core behavior but cannot define universal Core
   truth.

## ASH Dependency Pin and Mirror

The repository-local ASH dependency pin is
`data/governance/ash_dependency_identity.json`. Its authoritative source tree
is `core/ash_pattern_engine/canonical/`; the identity artifact owns the
aggregate digest and exact pinned identity.

`specs/` is the generated compatibility mirror. The canonical source's
`README.md` is source-local routing metadata and is excluded from mirror
correspondence. All other canonical relative paths must have exact normalized
UTF-8/LF text equivalence with their mirror files. A UTF-8 BOM or CRLF/CR input
is normalized before comparison; raw-byte identity is not the contract. Mirror
content cannot override its source.
`scripts/sync_ash_specifications.py` is the synchronization authority; a source
change and generated mirror update form one reviewed change.

The machine synchronization mode is `normalized_utf8_lf_relative_paths`.
`core/ash_pattern_engine/canonical` MUST be the authoritative ASH
specification source, and `specs` MUST remain its deterministically synchronized
generated mirror. [YWE-REQ-0016]

## Conflict Resolution

Resolve a conflict by identifying both authority layer and truth scope:

1. Reject a lower-layer attempt to override a higher-layer owner.
2. Reject an interpretive view presented as objective state.
3. Reject an objective state mutation without its required packet and
   provenance.
4. Preserve compatibility aliases only when they resolve to one canonical
   value and conflicts fail closed.
5. Route non-normative summaries to their controlling source instead of
   treating document prominence as authority.

## Normative Machine Form

`data/governance/truth_authority_lattice.json` is the exact machine-readable
form of the layer order, truth scopes, derivation edges, routing boundary, and
ASH source/mirror relationship. Human prose may explain that artifact but may
not contradict it.
