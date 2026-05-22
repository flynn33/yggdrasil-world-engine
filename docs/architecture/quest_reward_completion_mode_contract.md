# Quest Reward Completion Mode Contract

Completion mode is the player-facing and system-facing classification of how a
quest was resolved.

## Schema-aligned fields

The authoritative Phase 15 shape is
`data/schemas/quest_completion_mode_schema.json`. Completion-mode records use
`mode_id`; they do not emit `completion_mode_id` or `resolution_intent`.

## Required fields

| Field | Schema rule |
| --- | --- |
| `mode_id` | Stable completion-mode identifier. |
| `quest_ref` | Quest or quest-manifest reference. |
| `chosen_action` | Player action that selected the mode. |
| `is_morality_grade` | Must be `false`. |
| `truth_scope` | One of the schema truth-scope enum values. |

## Optional fields

```text
mode_label
available_actions
consequence_profile
```

## Ravenfall Gate baseline modes

```text
reveal_oath
conceal_oath
bind_oath
study_oath
weaponize_oath
```

## Important rule

Completion modes are not moral grades. A completion mode describes the pattern of
resolution and its consequence-routing implications.

For example, `conceal_oath` may involve the Dark Wolf because concealment,
endurance, and transformation are Dark Wolf domains. It does not mean the player
made a moral choice or that either wolf is a moral pole.
