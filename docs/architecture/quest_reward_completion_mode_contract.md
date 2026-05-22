# Quest Reward Completion Mode Contract

Completion mode is the player-facing and system-facing classification of how a
quest was resolved.

## Required fields

```text
completion_mode_id
quest_ref
chosen_action
available_actions
player_action_trace_ref
branch_event_ref
truth_scope
resolution_intent
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
