# Repository Scope Partition Map

Status: current primary-scope authority

Machine-readable authority: `data/governance/scope_partition_manifest.json`

Classification authority: `data/governance/artifact_classification_manifest.json`

## Purpose

This map separates mandatory engine truth, optional feature profiles, upstream
dependency material, game-specific reference evidence, governance, history, and
future work. Every repository artifact has exactly one primary partition and may
carry secondary tags for cross-cutting concerns.

## Primary Partitions

| Partition | Current repository meaning |
|---|---|
| `ywe_core` | Mandatory platform-neutral engine contracts and semantics consumed by every conforming implementation. |
| `ywe_extension_profile` | Optional setting-neutral feature-engine or subsystem profile material outside mandatory core. |
| `ash_dependency_material` | Authoritative or deterministically mirrored ASH Cosmological Model and ASH mathematics dependency material. |
| `wrw_reference_profile` | Where Ravens Wait: Eternal Reckoning game, narrative, Ravenfall, Raven Companion, and Twin Wolf reference-profile material. |
| `governance_validation` | Roadmap, policy, validation, tests, schemas for governance, and active conformance controls. |
| `historical_evidence` | Changelog, prior acceptance evidence, source-ingest provenance, deprecated records, and superseded records. |
| `later_release_work` | Explicitly deferred or placeholder work assigned to M1 through M10 or downstream work gated by M10. |

## Exact-One Partition Law

Partition matching uses the same normalized path universe and digest as artifact
classification. Exact path overrides are terminal. All remaining ordered rules
must be non-overlapping, and every path must match exactly one primary partition.

Secondary tags may describe subjects such as `ravenfall`, `phase_17`, `ability`,
or `ash_mirror`; they do not create another primary partition.

## Partition Decision Order

Use current repository function, not directory name alone:

1. Deprecated, superseded, and purely historical artifacts route to
   `historical_evidence`.
2. Explicit placeholders route to `later_release_work` with an owner, debt record,
   and future milestone.
3. Deferred host-adapter work routes to `later_release_work`; retained normative
   boundary contracts require an explicit exception.
4. ASH canonical dependency specifications and synchronized mirrors route to
   `ash_dependency_material`.
5. Repository policy, roadmap, validators, tests, and active conformance controls
   route to `governance_validation`.
6. Artifacts that require WRW, Ravenfall, Nathruun, Floki, Raven Companion, or the
   White and Dark Wolves route to `wrw_reference_profile`.
7. Optional setting-neutral feature engines route to `ywe_extension_profile`.
8. Remaining mandatory platform-neutral engine semantics route to `ywe_core`.

Mixed artifacts require an exact override with a rationale. A WRW-specific fixture
cannot become YWE Core truth merely because it validates a generic schema.

## Major Routing Boundaries

- `core/ash_pattern_engine/canonical/**` is authoritative ASH dependency
  material. `specs/**` is its generated mirror; synchronization is enforced by
  `scripts/sync_ash_specifications.py`.
- `docs/game/**`, `data/game/**`, `lore/**`, and Ravenfall-specific fixtures are
  WRW reference-profile material unless an explicit historical or placeholder
  override applies.
- `modules/**` is generally extension-profile material; companion and reward
  artifacts with required Raven or Twin Wolf semantics receive WRW overrides.
- `data/validation/**`, `scripts/**`, `tests/**`, and `.github/**` are generally
  governance and validation material.
- `examples/**` always has maturity class `example`, but its primary scope follows
  its content.
- `adapters/**` remains deferred through the roadmap platform gate and does not
  authorize platform runtime implementation.

## M1 Exact Overrides

Directory defaults do not replace these path-specific decisions:

| Path or path set | Primary partition | Reason |
| --- | --- | --- |
| `lore/wrw_cosmology/canon_scope.md` | `wrw_reference_profile` | Reviewed normative WRW cosmology scope, no longer placeholder or future work. |
| `lore/wrw_cosmology/source_notes.md` | `wrw_reference_profile` | Reviewed informative WRW source context, no longer placeholder or future work. |
| `data/ash_state/realm_bit_mapping.yaml` | `wrw_reference_profile` | WRW named-realm compatibility mapping over ASH structural coordinates. |
| `data/realm_registry/realms.json` | `wrw_reference_profile` | WRW named-realm registry and explicit coordinate bindings. |
| `docs/master_specification/YWE_MASTER_SPECIFICATION.md` | `wrw_reference_profile` | Informative WRW-backed composite governed by the Core/WRW boundary contract. |
| `docs/architecture/ASH_PATTERN_ARCHETYPE_LIBRARY_CANONICAL.md` | `ash_dependency_material` | Canonical ASH archetype dependency semantics. |
| `data/schemas/ash_dependency_identity_schema.json`, `data/schemas/canonical_term_index_schema.json`, `data/schemas/governance_record_register_schema.json`, `data/schemas/m1_acceptance_evidence_schema.json`, `data/schemas/normative_requirement_register_schema.json`, and `data/schemas/truth_authority_lattice_schema.json` | `governance_validation` | M1 governance and acceptance-contract schemas. |
| `docs/architecture/truth_authority_lattice.md` and `docs/architecture/ywe_core_wrw_scope_contract.md` | `governance_validation` | M1 authority and scope governance contracts. |
| M1 policies under `docs/governance/**`, machine authorities under `data/governance/**`, change notes under `governance/**`, validators under `scripts/**`, and tests under `tests/**` | `governance_validation` | Active M1 governance and validation implementation. |
| `data/governance/m1_acceptance_evidence.json` and `docs/project/M1_CANON_TERMINOLOGY_GOVERNANCE_ACCEPTANCE.md` | `historical_evidence` | Preserved M1 outcome evidence; the evidence schema and validator remain active governance. |

## Non-Destructive Boundary

Partitioning is metadata. It does not relocate files, redefine accepted semantic
contracts, authorize platform code, convert the WRW profile into YWE Core, or make
later milestone work current.

## Update Discipline

Any path addition, removal, rename, or change in primary responsibility must update
the scope manifest and its coverage snapshot in the same change. Changes to mixed
or sensitive paths require a path-specific rationale rather than a broader rule.

## Acceptance Conditions

Scope coverage passes only when:

- every path has exactly one primary partition;
- coverage totals equal the path-universe count;
- every later-release path has a milestone disposition;
- every WRW-specific artifact is excluded from YWE Core;
- ASH mirrors have explicit authority roles;
- platform implementation remains unauthorized through the M10 gate.
