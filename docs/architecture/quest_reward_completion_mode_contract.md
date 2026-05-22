# Quest Reward Completion Mode Contract

Completion mode is the player-facing and system-facing classification of how a
quest was resolved.

## Required fields

```text
mode_id
quest_ref
chosen_action
is_morality_grade
truth_scope
```

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
