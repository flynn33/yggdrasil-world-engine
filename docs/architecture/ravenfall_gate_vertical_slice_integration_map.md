# Ravenfall Gate Vertical Slice Integration Map

Status: `phase_16_recovery`

## Purpose

This map shows how the Ravenfall Gate slice touches existing YWE systems.

## Required integration points

| System | Phase | Ravenfall Gate Use |
|---|---:|---|
| Base world / branch reality | 9 | Creates leaf-branch-specific outcomes for Reveal, Conceal, Bind, Study, Weaponize. |
| Player runtime state | 10 | Reads player branch history, plane attunement, bloodline/lineage resonance, wolf companion state, ability pressure. |
| Worldstate and location mutation | 11 | Updates Ravenfall Gate location phase and truth-scope scoped deltas. |
| Quest/NPC/lore generation | 12 | Generates quest candidate, NPC witnesses/keepers, and lore fragments from axiom pressure. |
| Twin Wolf Companion Engine | 13 | Physical wolf companions participate in exploration, visions, quest assistance, and combat. |
| Ability / Power Engine | 14 | Tests Oath-Sight, Grave-Anchor, Twin Threshold Step, Blood-Echo Hearing, and Causal Thread Mark. |
| Quest Reward Resolver | 15 | Converts completion modes into structured consequence bundles and future generation bias. |

## Slice output

The slice should emit example manifests and trace records proving that each system contributes a consistent piece of the player-facing experience.
