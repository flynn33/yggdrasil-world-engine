# M3 reviewed source baseline compatibility

Status: active bounded M3 source compatibility contract, adopted October 4, 2026 before dependent implementation. Owner and partition: ywe_core. Requirement: [YWE-REQ-0043]. Decision: ADR-0032. Reviewed against accepted N2 implementation c78ee7e451e5d35b2f615369433291007e7ee261 and publication checkpoint e5fbce354fc0ba7eda4c88682b4deabe5f29de6e. This contract adopts only the reviewed local source extension, complete source bindings and reference Diagnostics source provenance. The exact source patch and dependent compatibility implementation are applied; independent complete acceptance remains pending in this checkpoint. Full N3 session/lifecycle behavior and M3 completion remain outside this adoption.

The exact seven-rule source patch was independently reviewed as N3_LOCAL_CANONICAL_EXTENSION.proposed.patch; its fixed provenance is recorded below and the complete trigger/vector correspondence is embedded in this contract. Its existing two TRIGGER 001 meanings are unchanged; the exact nine-trigger map assigns seven additional IDs. The local canonical directory is the declared source authority. The generated `specs` mirror is regenerated through its existing owner. No external ASH repository mutation or authority adoption is implied.

## Review provenance

The reviewed external source compatibility contract SHA256 is 0e58a9347ba54675e7363ba3224e18d19466f73a745dcc7d80632d951426845a; adoption evidence index 409c328658ce75bb1fcefa563c681a763d8c73a6c0dc1cf29e3d076013a1281a; exact source-only package index bdcb65a97a3dcd0807b2116f1027a95ec9561048e3bcd7290081657a5eee4a8a; source patch 468979ca339a75cd7ee78b67937f2913a90f945d3eb14a0249b2373253ba51b8; source vectors 14cbe2949ef974ae720874218c5b8fdc9c0d5aebc0178c6c19b0218b8e1142dd. These fingerprints identify reviewed proposal bytes, not a completed implementation or a future Git revision.

## Exact finite source inventory

[YWE-REQ-0043] Source identity MUST use one complete reviewed baseline. The appended JSON inventory is normative for this adoption. It contains exactly two named baselines: `LEGACY_C78` and `N3_LIFECYCLE`. Each has an exact nine-field canonical vector, exactly seven ordered recovery contract pins, and exactly eight ordered Diagnostics source kind/hash rows. The dependency ID and serialized field counts stay unchanged. Names are recognition results, never caller-selected truth flags.

`LEGACY_C78` is bound to immutable source commit `c78ee7e451e5d35b2f615369433291007e7ee261`. `N3_LIFECYCLE` source bytes have reviewed aggregate `76d59926ce9676b7584c6cdd555f50f56fceda075fa3fc8b37167fd2be43f7c9`; their containing implementation commit is obtained and verified by host assembly after atomic source adoption. No self-referential future commit or guessed source revision is embedded.

All source math remains the existing F2^9/C16 baseline. The N1 normalization policy and N2 safety policy remain bound to their unchanged actual bytes. Old milestone evidence/source packet examples remain historical facts and are not rewritten to show new source provenance.

## Core values and exact APIs

`state_values.CANONICAL_BINDING_FIELDS` remains a documented legacy alias. Add immutable `CANONICAL_BINDING_BASELINES` containing the two `(baseline_name, complete_fields_tuple)` rows and `CURRENT_CANONICAL_BINDING_FIELDS` selecting N3_LIFECYCLE. The underlying tuple entries are exact immutable built-in strings.

`CanonicalAshBinding` keeps its exact existing nine-field constructor and to_record shape. It accepts exactly one complete known vector. Before comparing tuples, require the exact owned class where an object is supplied and exact built-in strings for all nine leaves. Unknown vectors, old aggregate/new taxonomy, new aggregate/old taxonomy, subclass values, hooks and malformed scalar types refuse with existing CANONICAL_BINDING_INVALID. Structural scalar refusal names its field. An incorrect dependency names dependency_id; an unknown aggregate names aggregate_sha256. A recognized aggregate selects its one complete vector, and any differing leaf names the first differing field in the existing nine-field order. No independent allowed-hash enum is an accepted identity.

Add these pure functions to state_values:

```python
canonical_source_baseline(binding: CanonicalAshBinding) -> str
canonical_diagnostic_pin_fields(binding: CanonicalAshBinding) -> tuple[tuple[str, str], ...]
```

The first validates the exact complete owned binding and returns only LEGACY_C78 or N3_LIFECYCLE. The second returns exactly eight ordered `(source_kind, sha256)` rows from the matching whole vector. Neither reads files/Git, evaluates a profile, or authenticates an assembly. Unknown/reflected-invalid objects fail before string/equality hooks. The derived baseline is not added to raw packet records.

`recovery_values.RECOVERY_CONTRACT_PIN_FIELDS` remains a legacy alias. Add immutable `RECOVERY_SOURCE_BASELINES` containing corresponding named canonical and recovery tuples. Add:

```python
recovery_contract_pin_fields(binding: state_values.CanonicalAshBinding) -> tuple[tuple[str, str], ...]
```

`RecoverySourceBinding(canonical_binding, contract_pins)` keeps its exact two-field signature and record. It validates exactly the seven ordered pins paired with that canonical nine-field vector, including exact nested owned SourcePin/scalar guards before equality. A known canonical vector and independently known but differently paired pin vector is rejected. RecoveryEngine obtains its seven pins through the pure matching helper for its actual StateModel.

StateModel's original assessment and proof comparisons continue to require its actual complete source binding and full profile. Registry revalidation requires exact current model and certification source/profile truth. A rejected comparison may retain a legacy submitted object plus current-model new object; that is valid mismatch evidence. Successful/VERIFIED roles must agree. No comparison changes to partial hash membership.

Explicit reference factories select CURRENT_CANONICAL_BINDING_FIELDS after source adoption; existing callers that construct the full legacy binding remain supported. An older assessment is never relabelled as a current assessment. Future N3 lifecycle admission must require N3_LIFECYCLE before any N3 reservation, capture, provider, mode or publication effect. This source contract supplies the recognition guard but does not implement/adopt those effects.

## Fixed earlier rule ownership

The generic DiagnosticEnvelope rule set grows from 8 to 17 precisely reviewed IDs. Keep ASSESSMENT_RULE_IDS at six, NORMALIZATION_RULE_IDS at seven and N2_RULE_IDS at eight immutable. Enforce the six-ID boundary on standalone StateValidityDiagnostic as well as assessment packet/emission paths. Keep seven/eight guards on standalone owning records, confirmed prefixes and attempted capture records. Generic envelope acceptance cannot admit a lifecycle ID into an earlier packet owner. No new DiagnosticKind, RecoveryOutcome or codeword is introduced.

## Exact Diagnostics provenance input

[YWE-REQ-0043] Collector configuration MUST validate the finite snapshot mapping before storage or clock effects. Both ReferenceDevelopmentDiagnostics and ReferenceReleaseDiagnostics preserve their four positional arguments and add one optional keyword:

```python
ReferenceDevelopmentDiagnostics(identity, profile, store, clock,
    *, canonical_source_snapshots: tuple[diagnostics_values.SourcePin, ...] | None = None)
ReferenceReleaseDiagnostics(identity, profile, store, clock,
    *, canonical_source_snapshots: tuple[diagnostics_values.SourcePin, ...] | None = None)
```

No new value class or service is required. The keyword is API-only configuration; it is not persisted directly and introduces no serialized header/field. When present it is an exact tuple of 0..2 exact owned SourcePin objects, ordered legacy then current when both are present. Every entry has source_kind=ASH_AGGREGATE, one of the two reviewed aggregate hashes and exact 40-lowercase-hex revision. Re-run each owned SourcePin constructor's scalar checks before comparing or selecting it. Duplicate aggregate, unknown aggregate, wrong order/type, malformed revision, or a current entry with absent or different identity.source_revision is DIAGNOSTICS_CONFIG_INVALID/ORIGINAL_SOURCE before store.verify, clock.read or any write. The legacy entry's revision must be exact c78. Empty configuration permits no source-certified capture. Existing unknown implementation identity admission refusal remains mandatory even if a caller supplies a legacy entry.

When the keyword is None, retain a truthful legacy-only direct-constructor default: if identity.source_revision is nonnull, configure exactly `SourcePin('ASH_AGGREGATE', c78, legacy_aggregate)`; if it is null, configure no source snapshot. The default does not enable N3_LIFECYCLE and does not claim that the caller's implementation revision contains legacy source bytes. The immutable c78 association was independently verified before adoption. This preserves the direct legacy constructor call shape and unknown-source refusal. A known raw identity/configuration from an in-memory test is still declared assembly input, not newly authenticated host storage/source evidence.

Host assembly is the owner that actually verifies source bytes and snapshots. Pure Core constructor validation does not prove that a caller ran host verification. Neither SourcePin shape nor a raw source_verified boolean confers that proof; no such boolean is added.

`diagnostics._source_support(binding)` validates/recognizes the actual whole canonical binding, finds exactly its configured aggregate SourcePin, and builds all eight source rows from canonical_diagnostic_pin_fields(binding), using that selected snapshot revision for every row. A missing mapping is DIAGNOSTICS_ORIGIN_UNAVAILABLE/ORIGINAL_SOURCE before alias/support persistence. It must not read the current global legacy alias, use identity.source_revision for every baseline, or substitute a different vector. Source aliases include aggregate and remain distinct. SafeSourceEvidence keeps exactly its existing eight pins and closed fields; its pure digest check recognizes either complete ordered 8-digest vector. Revision formatting remains structural; actual containing-tree proof belongs to assembly. A snapshot may honestly contain both independently verified source nodes and a source-mismatch comparison referencing both.

## Actual host verification before storage

[YWE-REQ-0043] Host assembly MUST verify actual containing-source revisions before protected storage creation. `assemble_reference_diagnostics(root, *, release=False, parent=...)` retains its existing signature and becomes dual-aware by default. Before WindowsProtectedStore creation or any collector/store/clock effect it must:

1. Verify selected module/root ownership and active repository baseline using the existing governed VERSION/truth owner.
2. Enumerate actual 32 canonical files excluding the informative README; apply the established UTF8/BOM/LF normalization; verify exact reviewed relative paths, individual digests, current descriptor and aggregate against one complete known source baseline. Do not trust a caller-selected hash list or mirror.
3. Resolve actual Git HEAD and verify the corresponding 32 source blobs at that exact commit match the selected current canonical bytes. If source edits are uncommitted or the containing tree does not match, refuse before storage; never label new bytes with legacy HEAD. Other implementation dirtiness remains accurately reported by existing SourceProvenance.
4. Read all legacy 32 blobs and descriptor at exact c78, independently verify all expected hashes and aggregate. Missing history/blob or mismatched materialization is a configuration/source failure; no current-file fallback, online download or silent downgrade.
5. If current source is N3_LIFECYCLE, pass two aggregate SourcePins in exact legacy/current order: `(legacy_aggregate,c78)` and `(new_aggregate,verified_HEAD)`. If current source is LEGACY_C78, pass only `(legacy_aggregate,c78)`. These source revisions are distinct from current implementation identity where appropriate. Current snapshot bytes and legacy snapshot bytes are verified separately.

Core performs no filesystem/Git operations. The real Windows protected storage mechanism, privacy limitations and receipt/purge semantics are unchanged. The source extension alone does not assert native/product acceptance.

## Schema and existing fixture compatibility

Use complete-vector oneOf branches for CanonicalAshBinding and exactly paired CanonicalAshBinding/contract_pins branches for RecoverySourceBinding. SafeSourceEvidence uses complete ordered 8-digest branches. Standalone SourcePin may accept the reviewed hash appropriate to its source_kind; that single fact does not certify a whole source identity. RegistrySourceBinding's single aggregate may recognize either reviewed aggregate while runtime validates it against the full model. Existing closed fields, owner requirement annotations, numeric/string/collection bounds, old6/7/8 rule subsets and headers remain unchanged.

Do not globally force every nested source role to one version: a valid REJECTED mismatch must retain the submitted and current facts. Verified/successful model-owned roles still agree. Schema matching does not prove profile mathematics, current model equality, actual source verification, collector acknowledgments, native safety or mode effects.

All 734 existing fixture entries and original authored bytes remain unchanged. The actual external in-memory schema audit ran the complete registered fixture pipeline:734 results,250 expected rejects,zero errors. Exactly one old rejected row reaches a changed source definition: m3.recovery.reject.missing-known-path-evidence-link at examples/core_state_recovery/recovery_rejections.example.json /3, targeting KnownCorrection. Its entire singleton witness remains JSON_SCHEMA_REQUIRED at the root instance pointer and /required schema pointer, with missing_properties=[classification_evidence_reference]. Its nested canonical source node is valid. No registered negative directly targets one of the three changed source nodes. The evidence is N3_LEGACY_FIXTURE_WITNESS_AUDIT.json; this execution establishes schema/catalog compatibility, not new runtime compatibility.

`instance_witnesses` recursively flattens context leaves and `evaluate_fixtures` compares the complete signature set; matching intended requirement alone is insufficient. A valid old source node in an unrelated rejected case must not gain branch errors; any future true source-node negative with changed signatures needs an explicitly reviewed representation/migration, never weakened expected errors. The exact proposed paired-pin branches own both prefixItems and items:false within the same branch; moving that items:false outside the branch rejects otherwise valid pins under Draft 2020-12. Preserve that assertion placement and re-run the full pipeline after live implementation. Add new current positives and exact mixed-vector rejects after adoption. Existing unknown-reference denial/requirement ownership remains active.

Primary source pin tests compare legacy expectations to actual immutable c78 blobs and current expectations to actual current source. Preserve old independent mathematical oracles and fixture data. Recheck current manifest/mirror, historical M1/M2 evidence and all existing area suites. The active recovery contract's stale62/75 description is corrected to the already adopted67 structures/78 enum families; historical Project_Record counts remain untouched.

## Bounded verification and activation

Source-only adoption, exact two-file patch, mirror/descriptor regeneration and dual-vector implementation are one governed compatibility increment. The embedded immutable registry inventory avoids creating an unregistered machine artifact; implementation constants and schemas are independently checked against it. No new taxonomy/profile baseline can be silently added later.

Required checks include the 16 executable atomic cases, all 734 legacy fixture expectations unchanged, both actual host source snapshots, direct legacy constructor default/unknown refusal, wrong current revision/configuration before zero storage/clock calls, source-role mismatch retention, fixed6/7/8 rejection of every lifecycle ID, and new/legacy current-model foreign-source refusal. Future N3 effects remain unavailable until their own reviewed contract/implementation passes the source admission guard and lifecycle tests. M3 remains incomplete.

## Embedded exact source-vector inventory

The embedded JSON inventory is normative and was independently verified against the frozen two-file patch and all 32 legacy Git blobs. No proposed current source commit is fabricated. Only actual host assembly may supply its containing verified revision.

<!-- EXACT_SOURCE_COMPATIBILITY_INVENTORY -->
```json
{
  "contract_id": "YWE-M3-REVIEWED-SOURCE-COMPATIBILITY-001",
  "inventory_version": "1.0.0",
  "legacy_commit": "c78ee7e451e5d35b2f615369433291007e7ee261",
  "baseline_order": [
    "LEGACY_C78",
    "N3_LIFECYCLE"
  ],
  "canonical_field_order": [
    "dependency_id",
    "aggregate_sha256",
    "state_space_sha256",
    "codeword_source_sha256",
    "validity_source_sha256",
    "classification_source_sha256",
    "recovery_source_sha256",
    "diagnostic_source_sha256",
    "taxonomy_source_sha256"
  ],
  "vectors": [
    {
      "baseline": "LEGACY_C78",
      "canonical_binding": {
        "dependency_id": "ash_cosmological_model.f2_9.canonical",
        "aggregate_sha256": "0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb",
        "state_space_sha256": "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e",
        "codeword_source_sha256": "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c",
        "validity_source_sha256": "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e",
        "classification_source_sha256": "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff",
        "recovery_source_sha256": "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd",
        "diagnostic_source_sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7",
        "taxonomy_source_sha256": "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"
      },
      "recovery_contract_pins": [
        {
          "path": "interfaces/contracts/recovery-engine-contract.md",
          "sha256": "27ffacc6218812b280ed236bf9052ee825e903498365d735bf57ee9cb338955b"
        },
        {
          "path": "interfaces/contracts/diagnostics-module-contract.md",
          "sha256": "88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37"
        },
        {
          "path": "registries/fallback-policy-registry.md",
          "sha256": "b108d6c4127da9ea375899e97c34048ded4ea3a7cb624ef24f18bfda5f8deaaa"
        },
        {
          "path": "algorithms/recovery-fallback-semantics.pseudo.md",
          "sha256": "0fb8a0750acae0fb263cd842e186ff35881f77b8e498a8f11f159a5d2db270b7"
        },
        {
          "path": "algorithms/containment-safe-failure-semantics.pseudo.md",
          "sha256": "83f1a19c1a0f375e02f2044c238786514d64b122ab6ab5a8bda6e6fa307c8256"
        },
        {
          "path": "interfaces/diagnostic-schema.md",
          "sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"
        },
        {
          "path": "interfaces/rule-id-taxonomy.md",
          "sha256": "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"
        }
      ],
      "diagnostic_pin_fields": [
        {
          "source_kind": "ASH_AGGREGATE",
          "sha256": "0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb"
        },
        {
          "source_kind": "ASH_STATE_SPACE",
          "sha256": "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e"
        },
        {
          "source_kind": "ASH_CODEWORDS",
          "sha256": "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c"
        },
        {
          "source_kind": "ASH_VALIDITY",
          "sha256": "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e"
        },
        {
          "source_kind": "ASH_CLASSIFICATION",
          "sha256": "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff"
        },
        {
          "source_kind": "ASH_RECOVERY",
          "sha256": "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd"
        },
        {
          "source_kind": "ASH_DIAGNOSTIC_SCHEMA",
          "sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"
        },
        {
          "source_kind": "ASH_TAXONOMY",
          "sha256": "f5ccaf3063dfe3df749f42dbe4659449a1874a6074e1d8d28ab4cad4a462f892"
        }
      ],
      "source_snapshot_revision": "c78ee7e451e5d35b2f615369433291007e7ee261",
      "revision_owner": "PINNED_LEGACY_GIT_SNAPSHOT"
    },
    {
      "baseline": "N3_LIFECYCLE",
      "canonical_binding": {
        "dependency_id": "ash_cosmological_model.f2_9.canonical",
        "aggregate_sha256": "76d59926ce9676b7584c6cdd555f50f56fceda075fa3fc8b37167fd2be43f7c9",
        "state_space_sha256": "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e",
        "codeword_source_sha256": "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c",
        "validity_source_sha256": "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e",
        "classification_source_sha256": "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff",
        "recovery_source_sha256": "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd",
        "diagnostic_source_sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7",
        "taxonomy_source_sha256": "150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250"
      },
      "recovery_contract_pins": [
        {
          "path": "interfaces/contracts/recovery-engine-contract.md",
          "sha256": "27ffacc6218812b280ed236bf9052ee825e903498365d735bf57ee9cb338955b"
        },
        {
          "path": "interfaces/contracts/diagnostics-module-contract.md",
          "sha256": "88b8d682fa826f128787e6154151c68b32d677239e17ddf4344a084461554a37"
        },
        {
          "path": "registries/fallback-policy-registry.md",
          "sha256": "b108d6c4127da9ea375899e97c34048ded4ea3a7cb624ef24f18bfda5f8deaaa"
        },
        {
          "path": "algorithms/recovery-fallback-semantics.pseudo.md",
          "sha256": "0fb8a0750acae0fb263cd842e186ff35881f77b8e498a8f11f159a5d2db270b7"
        },
        {
          "path": "algorithms/containment-safe-failure-semantics.pseudo.md",
          "sha256": "df957dc5c82c2fd0b51e43c6783d8cbb2e3ce565420a765abffd244cdcea98b2"
        },
        {
          "path": "interfaces/diagnostic-schema.md",
          "sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"
        },
        {
          "path": "interfaces/rule-id-taxonomy.md",
          "sha256": "150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250"
        }
      ],
      "diagnostic_pin_fields": [
        {
          "source_kind": "ASH_AGGREGATE",
          "sha256": "76d59926ce9676b7584c6cdd555f50f56fceda075fa3fc8b37167fd2be43f7c9"
        },
        {
          "source_kind": "ASH_STATE_SPACE",
          "sha256": "68435e731c3663a69c9ec3a596d022d0d937b2f0faa537a2827040bb7f89221e"
        },
        {
          "source_kind": "ASH_CODEWORDS",
          "sha256": "8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c"
        },
        {
          "source_kind": "ASH_VALIDITY",
          "sha256": "20d3f3cac028b916524a21bb1fb91afe5bb118eee549c376720ce6049d50a74e"
        },
        {
          "source_kind": "ASH_CLASSIFICATION",
          "sha256": "806ee1e731d6bddec9326150eb645af90b90d08b3256c81436fa272acf7238ff"
        },
        {
          "source_kind": "ASH_RECOVERY",
          "sha256": "cd520d8a9d65c70878dfafe29db8dbee5dcbcbe1e9d2a6b24ef6a6b2e5cf11fd"
        },
        {
          "source_kind": "ASH_DIAGNOSTIC_SCHEMA",
          "sha256": "825de7cfdd8598e940dbbcea73cdd78d2db1ba43df9beaee5e51ebdc0d92f8c7"
        },
        {
          "source_kind": "ASH_TAXONOMY",
          "sha256": "150b45d4c75aa053a8d5276d980b359b0ae768c85ae28896680296920402f250"
        }
      ],
      "source_snapshot_revision": null,
      "revision_owner": "HOST_VERIFIED_CURRENT_GIT_HEAD"
    }
  ],
  "fixed_rule_subsets": {
    "ASSESSMENT_RULE_IDS": [
      "ASH-STATE-STRUCTURE-001",
      "ASH-STATE-VALIDITY-001",
      "ASH-STATE-GENERAL-001",
      "ASH-ADMISSIBILITY-CLASSIFICATION-001",
      "ASH-CLASSIFICATION-MAPPING-001",
      "ASH-RECOVERY-ACTION-001"
    ],
    "NORMALIZATION_RULE_IDS": [
      "ASH-STATE-STRUCTURE-001",
      "ASH-STATE-VALIDITY-001",
      "ASH-STATE-GENERAL-001",
      "ASH-ADMISSIBILITY-CLASSIFICATION-001",
      "ASH-CLASSIFICATION-MAPPING-001",
      "ASH-RECOVERY-ACTION-001",
      "ASH-CODEWORD-STRUCTURE-001"
    ],
    "N2_RULE_IDS": [
      "ASH-STATE-STRUCTURE-001",
      "ASH-STATE-VALIDITY-001",
      "ASH-STATE-GENERAL-001",
      "ASH-ADMISSIBILITY-CLASSIFICATION-001",
      "ASH-CLASSIFICATION-MAPPING-001",
      "ASH-RECOVERY-ACTION-001",
      "ASH-CODEWORD-STRUCTURE-001",
      "ASH-FALLBACK-SELECTION-001"
    ],
    "generic_RULE_IDS": [
      "ASH-STATE-STRUCTURE-001",
      "ASH-STATE-VALIDITY-001",
      "ASH-STATE-GENERAL-001",
      "ASH-ADMISSIBILITY-CLASSIFICATION-001",
      "ASH-CLASSIFICATION-MAPPING-001",
      "ASH-RECOVERY-ACTION-001",
      "ASH-CODEWORD-STRUCTURE-001",
      "ASH-FALLBACK-SELECTION-001",
      "ASH-CONTAINMENT-TRIGGER-001",
      "ASH-CONTAINMENT-TRIGGER-002",
      "ASH-CONTAINMENT-TRIGGER-003",
      "ASH-CONTAINMENT-TRIGGER-004",
      "ASH-HALT-TRIGGER-001",
      "ASH-HALT-TRIGGER-002",
      "ASH-HALT-TRIGGER-003",
      "ASH-HALT-TRIGGER-004",
      "ASH-HALT-TRIGGER-005"
    ]
  },
  "trigger_rule_mapping": {
    "CONTAINMENT": {
      "FALLBACK_FAILURE": "ASH-CONTAINMENT-TRIGGER-001",
      "PROPAGATION_RISK": "ASH-CONTAINMENT-TRIGGER-002",
      "OPERATOR_REQUEST": "ASH-CONTAINMENT-TRIGGER-003",
      "RECOVERY_VALIDATION_FAILURE": "ASH-CONTAINMENT-TRIGGER-004"
    },
    "SAFE_HALT": {
      "CONTAINMENT_BREACH": "ASH-HALT-TRIGGER-001",
      "ESCALATION_FROM_FAILED": "ASH-HALT-TRIGGER-002",
      "OPERATOR_HALT_REQUEST": "ASH-HALT-TRIGGER-003",
      "POLICY_HALT_REQUEST": "ASH-HALT-TRIGGER-004",
      "UNRESOLVABLE_BLOCKED_RECOVERY": "ASH-HALT-TRIGGER-005"
    }
  },
  "collector_configuration": {
    "keyword": "canonical_source_snapshots",
    "owned_value_type": "diagnostics_values.SourcePin",
    "source_kind": "ASH_AGGREGATE",
    "min_items": 0,
    "max_items": 2,
    "order": [
      "LEGACY_C78",
      "N3_LIFECYCLE"
    ],
    "null_default_known_identity": "LEGACY_C78_AT_PINNED_C78",
    "null_default_unknown_identity": "EMPTY_NO_SOURCE_ADMISSION",
    "current_revision_rule": "EXACT_NON_NULL_IMPLEMENTATION_IDENTITY_REVISION_VERIFIED_AT_HEAD_BY_HOST",
    "configuration_error_code": "DIAGNOSTICS_CONFIG_INVALID",
    "configuration_error_field": "ORIGINAL_SOURCE",
    "missing_source_error_code": "DIAGNOSTICS_ORIGIN_UNAVAILABLE",
    "missing_source_error_field": "ORIGINAL_SOURCE"
  },
  "serialized_shape_counts": {
    "CanonicalAshBinding": 9,
    "RecoverySourceBinding": 2,
    "RecoverySourceBinding.contract_pins": 7,
    "SafeSourceEvidence.verified_pins": 8
  },
  "legacy_fixture_compatibility": {
    "fixtures": 734,
    "rejects": 250,
    "affected_legacy_reject_rows": [
      {
        "fixture_id": "m3.recovery.reject.missing-known-path-evidence-link",
        "path": "examples/core_state_recovery/recovery_rejections.example.json",
        "instance_pointer": "/3",
        "schema_id": "https://ywe.local/schemas/m3_recovery_value_schema.json#/$defs/KnownCorrection",
        "expected_errors": [
          {
            "error_id": "JSON_SCHEMA_REQUIRED",
            "instance_pointer": "",
            "schema_pointer": "/required",
            "missing_properties": [
              "classification_evidence_reference"
            ]
          }
        ],
        "reached_source_defs": [
          "https://ywe.local/schemas/m3_state_assessment_schema.json#/$defs/CanonicalAshBinding"
        ]
      }
    ],
    "external_proposed_registry_errors": []
  },
  "excluded_adoption": [
    "N3_LIFECYCLE_EFFECTS",
    "NEW_PROFILE_MATH",
    "NATIVE_PRODUCT_ACCEPTANCE"
  ]
}
```
