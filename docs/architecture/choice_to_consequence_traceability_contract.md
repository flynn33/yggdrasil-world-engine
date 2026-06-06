# Choice-to-Consequence Traceability Contract

A vertical-slice choice is accepted only if it traces to consequence.

## Required chain

```text
choice
  -> branch_event
  -> quest_reward_resolution
  -> consequence_resolution
  -> player_state_update
  -> worldstate_delta or diagnostic_noop
  -> location_mutation or location_noop
  -> future_generation_bias
```

## Design rule

No meaningful choice ends at dialogue, reward text, or a quest-complete flag.
