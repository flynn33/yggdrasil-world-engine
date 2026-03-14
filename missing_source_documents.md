# Missing Source Documents

This inventory tracks canonical artifact promotion status and known missing
source-backed artifacts that still require canonical merge.

## Canonical Promoted Artifacts

| Artifact | Status | Notes |
|---|---|---|
| `data/perception/perception_overlay_rules.yaml` | Canonical | Promoted with validation and truth-boundary checks |
| `data/realm/realm_mechanics_rules.yaml` | Canonical | Promoted with validation for attunement, boundaries, bleed, and shift law |

## Placeholder-Backed / Pending Canonical Artifacts

- `data/faction_topology/faction_topology_state_schema.yaml` — pending canonical merge in this repository snapshot
- `docs/architecture/realm_truth_boundary_contract.md` — recommended companion artifact (not yet present)
- `data/realm/realm_transition_examples.yaml` — recommended companion artifact (not yet present)
- `data/realm/realm_boundary_profiles.yaml` — recommended companion artifact (not yet present)

## Update Discipline

When promoting a canonical artifact in this repository:

1. Merge the artifact into canonical path.
2. Update this inventory in the same change set.
3. Update validation scripts in the same change set.
4. Run `bash scripts/run_checks.sh` before completion.
