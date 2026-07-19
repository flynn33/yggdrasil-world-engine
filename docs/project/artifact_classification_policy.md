# Repository Artifact Classification Policy

Status: current M0 classification authority

Machine-readable authority: `data/governance/artifact_classification_manifest.json`

Scope authority: `data/governance/scope_partition_manifest.json`

## Purpose

This policy assigns one current maturity class to every repository artifact without
renaming, relocating, or rewriting the artifact. Classification describes the
artifact's current repository role. It does not erase its origin phase or imply
release readiness.

## Maturity Classes

| Class | Current repository meaning |
|---|---|
| `normative` | Defines a current requirement, contract, schema, rule, policy, validator, or acceptance authority. |
| `informative` | Explains, indexes, maps, or summarizes without creating a new requirement. |
| `example` | Provides a positive, boundary, rejection, recovery, replay, migration, or reference-profile fixture. |
| `historical` | Preserves chronology, prior acceptance evidence, change history, or immutable provenance. |
| `deprecated` | Remains for compatibility but is explicitly discouraged and has a migration target. |
| `superseded` | Has been replaced by a named current authority and remains only for provenance. |
| `placeholder` | Explicitly declares incomplete content and is routed to a future milestone. |

An artifact has exactly one primary class. In particular, an artifact cannot be
both `normative` and `placeholder`, and historical origin does not automatically
make a currently enforced contract `historical`.

## Repository Path Universe

The classification universe uses normalized, repository-relative POSIX paths.
Path comparison is case-sensitive and uses ordinal sorting.

For committed validation, the universe is `git ls-files -z`. For local validation,
nonignored untracked files are added to the tracked set so that new governance
artifacts cannot escape classification before their first commit. Ignored files
and generated local environments are excluded.

The manifest records the exact path count and a SHA-256 digest of the sorted,
NUL-delimited path set. Any path-set drift requires a manifest review and update.

## Deterministic Matching Law

Classification is resolved in this order:

1. Normalize and validate the repository-relative path.
2. Apply an exact path override, when present. Overrides are terminal.
3. Otherwise evaluate ordered path rules.
4. Require exactly one matching class rule.
5. Reject zero matches, multiple matches, duplicate overrides, nonexistent
   override paths, invalid paths, or coverage-count disagreement.

Rule priority controls deterministic evaluation order; it does not silently
resolve overlapping matches. Overlap is an error and must be removed with a
narrow exclusion or exact override.

## Required Conditional Metadata

- `placeholder` requires `owner_role`, `future_milestone`, and `debt_ref`.
- `deprecated` requires `migration_ref`.
- `superseded` requires `superseded_by`.
- synchronized mirrors require `mirror_of` and an explicit synchronization check.
- later-release normative boundary contracts require a documented exception and
  milestone disposition.

The `origin_phase` field may preserve provenance but cannot substitute for the
current class.

## Placeholder Authority

At the M0 baseline, 46 tracked artifacts explicitly declare placeholder status.
The machine-readable manifest is the sole current exact list. The 14-item and
21-item lists preserved in older source-ingest documents are provenance subsets,
not current maturity inventories.

Current human indexes report the manifest count and link to the machine authority.
They must not independently reconstruct the placeholder set.

## Mirror and Authority Roles

The ASH dependency material under `core/ash_pattern_engine/canonical/` and
`specs/` includes synchronized representations. Classification alone does not
decide which copy is canonical. Each sensitive mirror records an authority role,
its counterpart when one exists, and the synchronization evidence used to detect
drift.

## Update Discipline

Any change that adds, removes, renames, promotes, deprecates, or supersedes an
artifact must update the classification manifest in the same change. A placeholder
promotion must also update its debt record and the current human inventory summary.

No broad document rewrite, source-history deletion, or semantic contract change is
authorized merely to simplify classification.

## Acceptance Conditions

Classification coverage passes only when:

- the effective path universe equals the manifest snapshot;
- every path has exactly one primary class;
- all conditional metadata is complete;
- coverage totals equal the path count;
- the placeholder count agrees with the debt inventory and current human indexes;
- no current normative artifact is disguised as historical, superseded, or
  placeholder content.
