# Player State and ASH Pattern System Resilience Contract

## Purpose

This contract defines how Player Runtime State uses the ASH Pattern System component for diagnostics, pattern integrity, recovery, containment, conformance, resilience, and patch/update stability.

## Correct role of ASH Pattern System

The ASH Pattern System is a YWE component. It is not the top-level cosmology.

It provides:

```text
pattern diagnostics
state integrity checks
conformance validation
recovery semantics
containment semantics
safe correction paths
patch/update stability
```

## Player state resilience fields

Player Runtime State should include:

```text
asp_diagnostic_refs
last_valid_snapshot_ref
state_integrity_status
recovery_status
containment_refs
diagnostic_noop_refs
schema_version_history
migration_notes
```

## Update safety

Before accepting a PlayerStateUpdatePacket, the system should be able to check:

```text
schema compatibility
required provenance
branch consistency
identity reveal constraints
wolf non-morality constraints
plane and bloodline dynamic-signal constraints
diagnostic references
```

## Recovery semantics

If player state becomes invalid, the repository should define non-destructive recovery expectations:

```text
normalize_state
reject_update
rollback_to_last_valid_snapshot
contain_invalid_branch_link
emit_diagnostic_noop
flag_for_author_review
```

## Forbidden

```text
silent_state_corruption
state_update_without_diagnostic_path
patch_migration_without_schema_version
feature_engine_direct_mutation
ash_pattern_system_as_top_level_cosmology
```
