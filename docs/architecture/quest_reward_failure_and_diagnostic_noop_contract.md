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

`QuestRewardResolutionPacket.resolution_status` must use only those schema enum
values. A rejected reward candidate never emits a `rejected_due_to_*` status.
It emits `rejected`, and the specific cause is stored separately in
`QuestRewardRejectionReason.reason_code`.

| `QuestRewardRejectionReason.reason_code` | Use |
| --- | --- |
| `missing_provenance` | Required source reference or trace evidence is absent. |
| `invalid_truth_scope` | The reward tries to write through the wrong truth layer. |
| `random_reward_table_primary_model` | Random reward tables are being treated as the primary model. |
| `wolf_morality_language` | Wolf reward text frames the Twin Wolf system as moral grading. |
| `ability_without_source_ref` | Ability pressure lacks required source provenance. |
| `quest_without_consequence` | Quest completion has neither consequence delta nor DiagnosticNoOp. |
| `unsafe_destructive_patch` | The candidate would rewrite or delete protected state. |
| `unknown` | The resolver rejected the candidate but no narrower code applies. |

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
