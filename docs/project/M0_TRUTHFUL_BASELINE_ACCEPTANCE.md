# M0 Truthful Baseline Acceptance

## Baseline

Base ref: `origin/main`
Base SHA: `fdf78bed7699f19975649ac0e570fdba360e451d`
Merge base: `fdf78bed7699f19975649ac0e570fdba360e451d`
Working branch: `governance/m0-truthful-baseline-closure`
Repository baseline version: `2.0.23`
Publication state: `unreleased`
Tags at HEAD: none.

## Authority and Phase Alignment

| Result | Value |
|---|---|
| Authority stack | PASS |
| Phase 8-9 anchors present | PASS |
| Protected Phase 9 paths changed | NO |
| Platform code added | NO |

## M0 Deliverables

| Deliverable | Result | Evidence |
|---|---|---|
| m0-d1 — Canonical roadmap and machine-readable milestone status agree | PASS | `data/governance/specification_roadmap.json`, `docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md` |
| m0-d2 — Maturity vocabulary separates acceptance, conformance, and release status | PASS | `docs/project/artifact_classification_policy.md`, `data/governance/repository_truth_manifest.json` |
| m0-d3 — VERSION is canonical and publication policy is explicit | PASS | `VERSION`, `data/governance/release_publication_policy.json` |
| m0-d4 — Phase, source, placeholder, deviation, license, and owner records are correct | PASS | `data/governance/repository_truth_manifest.json`, `SOURCE_AVAILABILITY_MANIFEST.md`, `missing_source_documents.md` |
| m0-d5 — Every tracked artifact has exactly one maturity class | PASS | `data/governance/artifact_classification_manifest.json` |
| m0-d6 — Every tracked artifact has exactly one scope partition | PASS | `data/governance/scope_partition_manifest.json` |
| m0-d7 — Platform implementation gate remains closed through M10 | PASS | `data/governance/specification_roadmap.json`, `data/governance/release_publication_policy.json` |

## M0 Exit Criteria

| Exit criterion | Result | Evidence |
|---|---|---|
| m0-e1 — No active release, status, license, scope, source, or authority conflict remains | PASS | `data/governance/repository_truth_manifest.json`, `data/governance/release_publication_policy.json`, `data/governance/scope_partition_manifest.json` |
| m0-e2 — Every active public promise is assigned or formally excluded | PASS | `data/governance/public_promise_register.json` |
| m0-e3 — Every current quality exception is registered in the ratcheted inventory | PASS | `data/validation/repository_quality_debt_inventory.json` |

## Coverage Counts

Tracked paths: 986
Classified paths: 986
Unclassified paths: 0
Multiply classified paths: 0
Normative: 722
Informative: 41
Example: 160
Historical: 10
Deprecated: 1
Superseded: 6
Placeholder: 46
Reviewed public surfaces: 65
Public promises: 33
Assigned: 30
Excluded: 3
Unresolved: 0
Debt records: 81
Open debt: 70
Accepted exceptions: 1
Resolved debt: 10

Scope partition coverage:

| Partition | Paths |
|---|---:|
| `ash_dependency_material` | 77 |
| `governance_validation` | 316 |
| `historical_evidence` | 17 |
| `later_release_work` | 61 |
| `wrw_reference_profile` | 242 |
| `ywe_core` | 165 |
| `ywe_extension_profile` | 108 |

Promise source evidence:

- Register: `data/governance/public_promise_register.json`
- Reviewed-surface aggregate: `c1030061ede3b41ada2da1d91ece9f5f2799c24279e215c4c12eba4d73f4d50d`

Debt assignment coverage:

| Milestone | Records |
|---|---:|
| M0 | 11 |
| M1 | 10 |
| M2 | 2 |
| M3 | 15 |
| M4 | 12 |
| M5 | 16 |
| M6 | 5 |
| M7 | 1 |
| M8 | 1 |
| M9 | 7 |
| M10 | 1 |

## Gate Results

| Gate | Result | Evidence |
|---|---|---|
| 9.3 No pre-generated branch tree | PASS | `scripts/check_branch_reality_guardrail.py` |
| 9.4 Correct pattern-system role | PASS | `scripts/check_authority_stack.py` |
| 9.5 Axioms and Phi integrated | PASS | `scripts/check_phase_9_schema_semantics.py` |
| 9.6 Pattern vectors integrated | PASS | `scripts/check_phase_9_schema_semantics.py` |
| 9.7 Non-destructive diff | PASS | `scripts/check_non_destructive_diff.py`, `data/governance/m0_acceptance_evidence.json` |
| 9.8 Existing checks still pass | PASS | `data/validation/repository_checks.json` |

## Validation Results

### local context

Executed at: `2026-07-19T15:05:10Z`

| Check ID | Command | Exit | Result | Summary hash |
|---|---|---:|---|---|
| `roadmap_governance` | `["{python}", "scripts/check_specification_roadmap.py", "{root}"]` | 0 | PASS | `8ed056f8398d22abfdf24ecf596bd6889366f2843bf15b30bd11fc14cb79d05c` |
| `machine_readable_artifacts` | `["{python}", "scripts/check_machine_readable_artifacts.py", "{root}"]` | 0 | PASS | `768d18d58ae33e3ca259c3d58ac80c232bfbc15991f7ce1a27cec252c6fb2116` |
| `validation_unit_tests` | `["{python}", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]` | 0 | PASS | `86117a46f04d4fbab8ae798d9ba11346acb65b4847b27a570100d2e2c64b4e1e` |
| `architecture_structure` | `["{python}", "scripts/validate_architecture.py", "{root}"]` | 0 | PASS | `23e8c91b57ab78b905b54099b6089fe8ce6c5a129167d8413c66698b0493e062` |
| `governance_contracts` | `["{python}", "scripts/check_governance_contracts.py", "{root}"]` | 0 | PASS | `ab5816b674dd6e092ea25abf06bf298caf82a0ff59bd6ebde41aa7075818f225` |
| `m0_truthful_baseline` | `["{python}", "scripts/check_m0_truthful_baseline.py", "{root}"]` | 0 | PASS | `f5f7ea49f30b3ef246c8f90746a3bc4d83c6d565bd85e109568a1e7a11583b6e` |
| `legacy_schema_contracts` | `["{python}", "scripts/validate_schemas.py", "{root}"]` | 0 | PASS | `d37fed5520aba587c9484b7cfe9766f2d31ee5ac98ef40784b33aedf24ad6f90` |
| `ash_compliance` | `["{python}", "scripts/validate_ash_compliance.py", "{root}"]` | 0 | PASS | `100ee89ad025931b1e8b7169b795baa8f2ad15d1f6d3701a6809b24dc515f971` |
| `ash_semantic_integrity` | `["{python}", ".github/scripts/semantic_integrity_check.py", "{root}"]` | 0 | PASS | `732e9b0d56e0fe704d20674007bc0521e4d99d683d455b28a99a27ace6a41b75` |
| `ash_math_integrity` | `["{python}", ".github/scripts/math_integrity_check.py", "{root}"]` | 0 | PASS | `2b86deea7f3c8968e7d5883a7970ca50065511d6916120a0fae24e62abb9895d` |
| `ash_downstream_conformance` | `["{python}", ".github/scripts/downstream_conformance_check.py", "{root}"]` | 0 | PASS | `6953f54cb57c2fdaddf3c9009266c1a2810ef589d68cfb7b7da4e16ea1e02418` |
| `package_acceptance` | `["{python}", ".github/scripts/ywe_package_acceptance_check.py", "{root}"]` | 0 | PASS | `6404be95c27f6301c63f6aad8401223e7a5d8f5507fc60e63108c74eac7b8d54` |
| `required_authority_contracts` | `["{python}", "scripts/check_required_contracts.py", "{root}"]` | 0 | PASS | `8b6eebec4be3558e6a5df21c8f5c140a3b5747abe1867d25eea370c1f105cc6c` |
| `phase_8_9_required_artifacts` | `["{python}", "scripts/check_phase_8_9_required_artifacts.py", "{root}"]` | 0 | PASS | `290f14cbfd3ed806a2d0118ac29a9fcb53f94853bfbd5c5decff8965424625a9` |
| `authority_stack` | `["{python}", "scripts/check_authority_stack.py", "--config", "data/validation/repository_drift_guardrail_rules.json", "{root}"]` | 0 | PASS | `b8b23cf66a630095172257468627a91de4e6ba595c850540d9924b9941247662` |
| `branch_reality` | `["{python}", "scripts/check_branch_reality_guardrail.py", "{root}"]` | 0 | PASS | `3b1a9e9d4b4c4c7c695fad8bc6962489f46d08cbc2d712796e706013d46125d1` |
| `phase_9_schema_semantics` | `["{python}", "scripts/check_phase_9_schema_semantics.py", "{root}"]` | 0 | PASS | `0b302e6263d43d22e1efde99c30c95240618dc263f1448dcbf336bcd6ac1630e` |
| `phase_8_9_package_boundary` | `["{python}", "scripts/check_phase_8_9_package_boundary.py", "{root}"]` | 0 | PASS | `25a2be9598de73dc99d5a9e912f315c1142352a1bcfdfbbed151839d9a3fd5ee` |
| `player_runtime_state` | `["{python}", "scripts/check_player_runtime_state.py", "{root}"]` | 0 | PASS | `9ddea79d1169159924b11ac07a3622eef8e112b02c8c50c59a4740bf7b641933` |
| `worldstate_location_mutation` | `["{python}", "scripts/check_worldstate_location_mutation.py", "{root}"]` | 0 | PASS | `c03e3dd6748c0f936add2779afbae4e0e123f283e5e8d48cb95b5025f7448b76` |
| `quest_npc_lore` | `["{python}", "scripts/check_quest_npc_lore_generation.py", "{root}"]` | 0 | PASS | `70780466bd60e120c044210a709e1ec71304d587375511fb4f4b156886fc5f0a` |
| `source_truth_alignment` | `["{python}", "scripts/check_source_truth_alignment.py", "{root}"]` | 0 | PASS | `4fd58660e01c3817c5bc75f37c06257cebe958760bf3588b21d6db4fd5c08c03` |
| `ability_power_engine` | `["{python}", "scripts/check_ability_power_engine.py", "{root}"]` | 0 | PASS | `3822d5e220479df4b534c7968bbea721d70805f2dcd492c6c11bc93c1b5d90c1` |
| `phase_15a_companion_reward` | `["{python}", "scripts/check_phase_15a_companion_reward_foundation.py", "{root}"]` | 0 | PASS | `62f20c603f9dc485187ad22f9a9fae38e6892d8d499df7916cb1655e58f07918` |
| `phase_16_17_recovery` | `["{python}", "scripts/check_phase_16_17_recovery.py", "{root}"]` | 0 | PASS | `861fbffc2f6c6b7866816d8a4ecbe4feece324d17a342629f0a6212267960081` |
| `platform_agnosticism` | `["{python}", "scripts/check_platform_agnosticism.py", "{root}"]` | 0 | PASS | `0240c7695aa2c26392cd1a415bda2a27b17f9be4106f5a6aa7c896c1591a81f2` |
| `repository_attribution_policy` | `["{python}", "scripts/check_repository_attribution_policy.py", "{root}"]` | 0 | PASS | `fe77bd3706c833f5b52bf2d981a5d55c426276cc0fe9f2975c4c2e3ad97848b9` |

### pull_request context

Executed at: `2026-07-19T15:07:44Z`

| Check ID | Command | Exit | Result | Summary hash |
|---|---|---:|---|---|
| `roadmap_governance` | `["{python}", "scripts/check_specification_roadmap.py", "{root}"]` | 0 | PASS | `8ed056f8398d22abfdf24ecf596bd6889366f2843bf15b30bd11fc14cb79d05c` |
| `machine_readable_artifacts` | `["{python}", "scripts/check_machine_readable_artifacts.py", "{root}"]` | 0 | PASS | `768d18d58ae33e3ca259c3d58ac80c232bfbc15991f7ce1a27cec252c6fb2116` |
| `validation_unit_tests` | `["{python}", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]` | 0 | PASS | `86117a46f04d4fbab8ae798d9ba11346acb65b4847b27a570100d2e2c64b4e1e` |
| `architecture_structure` | `["{python}", "scripts/validate_architecture.py", "{root}"]` | 0 | PASS | `23e8c91b57ab78b905b54099b6089fe8ce6c5a129167d8413c66698b0493e062` |
| `governance_contracts` | `["{python}", "scripts/check_governance_contracts.py", "{root}"]` | 0 | PASS | `ab5816b674dd6e092ea25abf06bf298caf82a0ff59bd6ebde41aa7075818f225` |
| `m0_truthful_baseline` | `["{python}", "scripts/check_m0_truthful_baseline.py", "{root}"]` | 0 | PASS | `f5f7ea49f30b3ef246c8f90746a3bc4d83c6d565bd85e109568a1e7a11583b6e` |
| `legacy_schema_contracts` | `["{python}", "scripts/validate_schemas.py", "{root}"]` | 0 | PASS | `d37fed5520aba587c9484b7cfe9766f2d31ee5ac98ef40784b33aedf24ad6f90` |
| `ash_compliance` | `["{python}", "scripts/validate_ash_compliance.py", "{root}"]` | 0 | PASS | `100ee89ad025931b1e8b7169b795baa8f2ad15d1f6d3701a6809b24dc515f971` |
| `ash_semantic_integrity` | `["{python}", ".github/scripts/semantic_integrity_check.py", "{root}"]` | 0 | PASS | `732e9b0d56e0fe704d20674007bc0521e4d99d683d455b28a99a27ace6a41b75` |
| `ash_math_integrity` | `["{python}", ".github/scripts/math_integrity_check.py", "{root}"]` | 0 | PASS | `2b86deea7f3c8968e7d5883a7970ca50065511d6916120a0fae24e62abb9895d` |
| `ash_downstream_conformance` | `["{python}", ".github/scripts/downstream_conformance_check.py", "{root}"]` | 0 | PASS | `6953f54cb57c2fdaddf3c9009266c1a2810ef589d68cfb7b7da4e16ea1e02418` |
| `package_acceptance` | `["{python}", ".github/scripts/ywe_package_acceptance_check.py", "{root}"]` | 0 | PASS | `6404be95c27f6301c63f6aad8401223e7a5d8f5507fc60e63108c74eac7b8d54` |
| `required_authority_contracts` | `["{python}", "scripts/check_required_contracts.py", "{root}"]` | 0 | PASS | `8b6eebec4be3558e6a5df21c8f5c140a3b5747abe1867d25eea370c1f105cc6c` |
| `phase_8_9_required_artifacts` | `["{python}", "scripts/check_phase_8_9_required_artifacts.py", "{root}"]` | 0 | PASS | `290f14cbfd3ed806a2d0118ac29a9fcb53f94853bfbd5c5decff8965424625a9` |
| `authority_stack` | `["{python}", "scripts/check_authority_stack.py", "--config", "data/validation/repository_drift_guardrail_rules.json", "{root}"]` | 0 | PASS | `b8b23cf66a630095172257468627a91de4e6ba595c850540d9924b9941247662` |
| `branch_reality` | `["{python}", "scripts/check_branch_reality_guardrail.py", "{root}"]` | 0 | PASS | `3b1a9e9d4b4c4c7c695fad8bc6962489f46d08cbc2d712796e706013d46125d1` |
| `phase_9_schema_semantics` | `["{python}", "scripts/check_phase_9_schema_semantics.py", "{root}"]` | 0 | PASS | `0b302e6263d43d22e1efde99c30c95240618dc263f1448dcbf336bcd6ac1630e` |
| `phase_8_9_package_boundary` | `["{python}", "scripts/check_phase_8_9_package_boundary.py", "{root}"]` | 0 | PASS | `25a2be9598de73dc99d5a9e912f315c1142352a1bcfdfbbed151839d9a3fd5ee` |
| `player_runtime_state` | `["{python}", "scripts/check_player_runtime_state.py", "{root}"]` | 0 | PASS | `9ddea79d1169159924b11ac07a3622eef8e112b02c8c50c59a4740bf7b641933` |
| `worldstate_location_mutation` | `["{python}", "scripts/check_worldstate_location_mutation.py", "{root}"]` | 0 | PASS | `c03e3dd6748c0f936add2779afbae4e0e123f283e5e8d48cb95b5025f7448b76` |
| `quest_npc_lore` | `["{python}", "scripts/check_quest_npc_lore_generation.py", "{root}"]` | 0 | PASS | `70780466bd60e120c044210a709e1ec71304d587375511fb4f4b156886fc5f0a` |
| `source_truth_alignment` | `["{python}", "scripts/check_source_truth_alignment.py", "{root}"]` | 0 | PASS | `4fd58660e01c3817c5bc75f37c06257cebe958760bf3588b21d6db4fd5c08c03` |
| `ability_power_engine` | `["{python}", "scripts/check_ability_power_engine.py", "{root}"]` | 0 | PASS | `3822d5e220479df4b534c7968bbea721d70805f2dcd492c6c11bc93c1b5d90c1` |
| `phase_15a_companion_reward` | `["{python}", "scripts/check_phase_15a_companion_reward_foundation.py", "{root}"]` | 0 | PASS | `62f20c603f9dc485187ad22f9a9fae38e6892d8d499df7916cb1655e58f07918` |
| `phase_16_17_recovery` | `["{python}", "scripts/check_phase_16_17_recovery.py", "{root}"]` | 0 | PASS | `861fbffc2f6c6b7866816d8a4ecbe4feece324d17a342629f0a6212267960081` |
| `platform_agnosticism` | `["{python}", "scripts/check_platform_agnosticism.py", "{root}"]` | 0 | PASS | `0240c7695aa2c26392cd1a415bda2a27b17f9be4106f5a6aa7c896c1591a81f2` |
| `repository_attribution_policy` | `["{python}", "scripts/check_repository_attribution_policy.py", "{root}"]` | 0 | PASS | `fe77bd3706c833f5b52bf2d981a5d55c426276cc0fe9f2975c4c2e3ad97848b9` |
| `non_destructive_diff` | `["{python}", "scripts/check_non_destructive_diff.py", "--base", "{base}", "--head", "HEAD", "{root}"]` | 0 | PASS | `72482d1fabb64206aabda62180085ccf86bdfca187f2c2873f5e3b478a239672` |

## Diff Review

- Base ref: `origin/main`
- Files created: 18
- Files patched: 36
- Files deleted: 0
- Files renamed: 0
- Diff stat: `54 files changed, 14402 insertions(+), 263 deletions(-)`
- Implementation tree hash: `da6dcaeeeee5e6b1328bb134c1e06c196c59801c242711786ae197b1e068af26`
- Diff hash: `095feea8ccac4fec23ff66af403317ca5b662d566fcae40720795e44898f1fb1`
- Protected Phase 9 path diff: empty.

Change-budget ledger:

| Path | Original | Added | Deleted | Percentage | Ceiling | Result |
|---|---:|---:|---:|---:|---:|---|
| `CONTRIBUTING.md` | 42 | 7 | 7 | 33.33% | 35.00% | PASS |
| `README.md` | 514 | 16 | 16 | 6.23% | 10.00% | PASS |
| `SOURCE_AVAILABILITY_MANIFEST.md` | 59 | 14 | 0 | 23.73% | 35.00% | PASS |
| `adapters/godot/README.md` | 17 | 3 | 0 | 17.65% | 30.00% | PASS |
| `adapters/unity/README.md` | 17 | 3 | 0 | 17.65% | 30.00% | PASS |
| `adapters/unreal/README.md` | 17 | 3 | 0 | 17.65% | 30.00% | PASS |
| `docs/architecture/forsetti_module_manifest_conventions.md` | 64 | 5 | 5 | 15.62% | 30.00% | PASS |
| `docs/governance/README.md` | 40 | 9 | 0 | 22.50% | 40.00% | PASS |
| `docs/project/source_inventory.md` | 60 | 19 | 6 | 41.67% | 50.00% | PASS |
| `guide.md` | 81 | 11 | 8 | 23.46% | 35.00% | PASS |
| `missing_source_documents.md` | 104 | 20 | 20 | 38.46% | 40.00% | PASS |

## Acceptance Judgment

- M0: ACCEPTED
- Roadmap transition recorded: M0 complete; M1 in progress
- Publication state: unreleased
- Platform work authorized: false
- Open M0 blockers: none

## Deferred Work

M1-M10 implementation remains outside this acceptance record. Platform work is unauthorized until M10 acceptance.

| Milestone | Status | Boundary |
|---|---|---|
| M1 | deferred | M1 implementation is not claimed by M0 acceptance. |
| M2 | deferred | M2 implementation is not claimed by M0 acceptance. |
| M3 | deferred | M3 implementation is not claimed by M0 acceptance. |
| M4 | deferred | M4 implementation is not claimed by M0 acceptance. |
| M5 | deferred | M5 implementation is not claimed by M0 acceptance. |
| M6 | deferred | M6 implementation is not claimed by M0 acceptance. |
| M7 | deferred | M7 implementation is not claimed by M0 acceptance. |
| M8 | deferred | M8 implementation is not claimed by M0 acceptance. |
| M9 | deferred | M9 implementation is not claimed by M0 acceptance. |
| M10 | deferred | M10 implementation is not claimed by M0 acceptance. |
