# M2 Exact Valid Schema Matches

Generic extension-schema matches are deliberately excluded.

| Fixture | Exact zero-error schema matches |
|---|---|
| `examples/ability_power_engine/invalid_ability_without_source_refs.example.json` | None |
| `examples/ability_power_engine/invalid_generic_xp_unlock.example.json` | None |
| `examples/ability_power_engine/invalid_permanent_wolf_death_cost.example.json` | None |
| `examples/ability_power_engine/invalid_white_good_dark_evil_ability.example.json` | None |
| `examples/phase_11_worldstate_location_mutation/ravenfall_gate/ravenfall_gate_truth_scope_examples.json` | None |
| `examples/phase_12_quest_npc_lore_generation/content_generation_batch/ravenfall_gate_phase_12_content_batch.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/lore_generation/lore_invalid_no_pattern_trace.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/lore_generation/ravenfall_gate_hidden_oath_lore_fragment.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/lore_generation/ravenfall_gate_public_oath_lore_fragment.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/npc_generation/npc_invalid_no_relation.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/npc_generation/ravenfall_gate_keeper_npc_candidate.example.json` | `data/schemas/npc_manifest_candidate_schema.json` @ `/` |
| `examples/phase_12_quest_npc_lore_generation/npc_generation/ravenfall_gate_witness_npc_candidate.example.json` | `data/schemas/npc_manifest_candidate_schema.json` @ `/` |
| `examples/phase_12_quest_npc_lore_generation/quest_generation/axiom_pressure_a1_isolation_to_quest.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/quest_generation/axiom_pressure_a4_erasure_cost_to_quest.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/quest_generation/invalid_generic_random_quest_candidate.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/quest_generation/quest_manifest_candidate_buried_oath_reveal.example.json` | None |
| `examples/phase_12_quest_npc_lore_generation/quest_generation/ravenfall_gate_conceal_oath_quest_generation_context.example.json` | `data/schemas/quest_generation_context_schema.json` @ `/` |
| `examples/phase_12_quest_npc_lore_generation/quest_generation/ravenfall_gate_reveal_oath_quest_generation_context.example.json` | `data/schemas/quest_generation_context_schema.json` @ `/` |
| `examples/player_runtime_state/future_generation_bias_from_player_state.example.json` | None |
| `examples/player_runtime_state/player_runtime_state_delta_branch_event.example.json` | None |
| `examples/player_runtime_state/player_runtime_state_initial.example.json` | None |
| `examples/quest_npc_lore_generation/lore_archive_record_oath_under_gate.example.json` | `data/schemas/lore_archive_record_schema.json` @ `/lore_variants/0`; `data/schemas/lore_archive_record_schema.json` @ `/lore_variants/1`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/myth_record_oath_under_gate.example.json` | `data/schemas/myth_record_schema_expansion.json` @ `/myth_lines/0`; `data/schemas/myth_record_schema_expansion.json` @ `/myth_lines/1`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/myth_seed_candidate_oath_under_gate.example.json` | `data/schemas/myth_record_schema_expansion.json` @ `/`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/npc_manifest_ragna_oathkeeper.example.json` | `data/schemas/npc_manifest_schema.json` @ `/persistence_state`; `data/schemas/npc_manifest_schema.json` @ `/relationship_vector`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/npc_memory_delta_ragna_oath_revealed.example.json` | `data/schemas/npc_manifest_schema.json` @ `/`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/quest_chain_manifest_ravenfall_gate_oath.example.json` | `data/schemas/quest_npc_lore_generation_schema.json` @ `/`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/stage_manifests/0`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/stage_manifests/1` |
| `examples/quest_npc_lore_generation/quest_generation_request_ravenfall_gate.example.json` | `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/quest_resolution_payload_ravenfall_gate_oath_revealed.example.json` | `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/quest_npc_lore_generation/social_distribution_delta_oath_under_gate.example.json` | `data/schemas/myth_record_schema_expansion.json` @ `/`; `data/schemas/quest_npc_lore_generation_schema.json` @ `/` |
| `examples/ravenfall_gate/phase_17/invalid_no_reward_packet_trace.reject.json` | None |
| `examples/ravenfall_gate/phase_17/invalid_permanent_wolf_death.reject.json` | None |
| `examples/ravenfall_gate/phase_17/invalid_platform_runtime_trace.reject.json` | None |
| `examples/ravenfall_gate/phase_17/invalid_static_location_trace.reject.json` | None |
| `examples/ravenfall_gate/phase_17/invalid_wolf_morality_trace.reject.json` | None |
| `examples/worldstate_location_mutation/location_mutation_delta_ravenfall_gate_oath_revealed.example.json` | `data/schemas/worldstate_location_mutation_schema.json` @ `/` |
| `examples/worldstate_location_mutation/location_mutation_state_ravenfall_gate_after.example.json` | `data/schemas/worldstate_location_mutation_schema.json` @ `/` |
| `examples/worldstate_location_mutation/worldstate_delta_ravenfall_gate_oath_revealed.example.json` | `data/schemas/worldstate_location_mutation_schema.json` @ `/` |
| `examples/worldstate_location_mutation/worldstate_mutation_commit_ravenfall_gate.example.json` | `data/schemas/worldstate_location_mutation_schema.json` @ `/` |
