# Vertical Slice Issue Classification Contract

Phase 17 issues are classified so design drift can be triaged without destructive rewrites.

## Issue severities

- `blocking`: prevents Phase 17 acceptance.
- `major`: must be corrected before Phase 18.
- `minor`: should be tracked but does not block acceptance.
- `observation`: useful note with no required fix.

## Issue classes

- `missing_trace`
- `broken_consequence_chain`
- `wolf_canon_violation`
- `truth_scope_violation`
- `platform_specific_leak`
- `schema_gap`
- `source_of_truth_drift`
- `non_destructive_policy_violation`
