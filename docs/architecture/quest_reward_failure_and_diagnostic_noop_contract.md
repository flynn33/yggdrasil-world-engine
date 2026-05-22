# Quest Reward Failure and DiagnosticNoOp Contract

Quest resolution can fail, partially resolve, or produce no meaningful system
change.

## Resolver outcomes

```text
resolved_with_consequence
resolved_with_partial_consequence
resolved_as_branch_only
resolved_as_perception_only
resolved_as_diagnostic_noop
rejected_due_to_missing_provenance
rejected_due_to_invalid_truth_scope
rejected_due_to_forbidden_morality_wolf_language
```

## DiagnosticNoOp requirements

```text
noop_id
quest_ref
reason
validated_context
systems_checked
diagnostic_refs
```

A DiagnosticNoOp is not a silent failure. It is an explicit system record.
