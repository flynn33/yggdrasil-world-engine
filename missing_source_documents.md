# Missing Source Documents

This inventory tracks canonical artifact promotion status and known missing
source-backed artifacts that still require canonical merge.

## Canonical Promoted Artifacts

| Artifact | Status | Notes |
|---|---|---|
| `data/perception/perception_overlay_rules.yaml` | Canonical | Promoted with validation and truth-boundary checks |
| `data/realm/realm_mechanics_rules.yaml` | Canonical | Promoted with validation for attunement, boundaries, bleed, and shift law |
| `data/faction_topology/faction_topology_state_schema.yaml` | Canonical | Promoted as the canonical faction topology state schema |
| `data/realm/realm_boundary_profiles.yaml` | Canonical | Promoted as boundary profile support artifact for realm mechanics |
| `data/realm/realm_transition_examples.yaml` | Canonical | Promoted as lawful/unlawful transition guidance support artifact |
| `docs/architecture/authored_override_and_tooling_notes.md` | Canonical | Promoted as authored-control and tooling boundary authority |
| `docs/architecture/realm_truth_boundary_contract.md` | Canonical | Promoted as boundary contract separating truth and interpretive layers |

## Placeholder-Backed / Pending Canonical Artifacts

- None currently tracked in this repository snapshot.

### Support Pass Status (2026-03-13)

- `FOUND` `data/faction_topology/faction_topology_state_schema.yaml`
- `FOUND` `docs/architecture/realm_truth_boundary_contract.md`
- `FOUND` `data/realm/realm_transition_examples.yaml`
- `FOUND` `data/realm/realm_boundary_profiles.yaml`

## Update Discipline

When promoting a canonical artifact in this repository:

1. Merge the artifact into canonical path.
2. Update this inventory in the same change set.
3. Update validation scripts in the same change set.
4. Run `bash scripts/run_checks.sh` before completion.
