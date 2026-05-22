# Quest Reward NPC and Faction Integration Contract

Quest rewards may update NPC relationships and faction state.

## NPC effects

```text
trust_delta
witness_status
keeper_status
rival_status
mentor_status
relationship_memory
quest_followup_eligibility
```

## Faction effects

```text
standing_delta
claim_delta
public_attention
covert_attention
legitimacy_pressure
schism_pressure
reform_pressure
retaliation_pressure
alliance_pressure
```

## Boundary

A faction claim is not automatically shared-world truth. It must be labeled as a
claim unless supported by worldstate evidence.
