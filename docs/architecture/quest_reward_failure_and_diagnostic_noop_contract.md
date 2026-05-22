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
rejected
```

Rejected resolutions keep `QuestRewardResolutionPacket.resolution_status` set to
`rejected`. The specific rejection cause is carried by
`QuestRewardRejectionReason.reason_code`.

```text
missing_provenance
invalid_truth_scope
random_reward_table_primary_model
wolf_morality_language
ability_without_source_ref
quest_without_consequence
unsafe_destructive_patch
unknown
```

## DiagnosticNoOp requirements

DiagnosticNoOp records use the canonical `ywe.diagnostic_noop.v1` shape:

```text
schema_id
version
noop_id
reason
source_context
evaluation
```

A DiagnosticNoOp is not a silent failure. It is an explicit system record.

Quest-specific resolver linkage is represented separately by
`QuestRewardDiagnosticNoOpLink`.

```text
link_id
quest_ref
diagnostic_noop_ref
reason
systems_checked
```
