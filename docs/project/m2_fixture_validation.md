# M2 Fixture Validation

Status: active incremental M2 conformance tooling; milestone acceptance remains outstanding.

The schema catalog at `data/validation/contract_catalog.json` lists every declared
JSON Schema document, including preserved design candidates. Inclusion provides
offline resolution and does not promote a candidate to accepted engine authority.
The catalog MUST cover every declared schema exactly once, match each file's
absolute identifier, and resolve all schema references locally. [YWE-REQ-0019]

The fixture catalog at `data/validation/fixture_catalog.json` MUST select an exact
schema identifier, optional schema fragment, and RFC 6901 instance pointer for
each case. [YWE-REQ-0020] The empty pointer selects the document root; `/` selects an empty
property name. Separate catalog entries preserve closed existing packet shapes.

Each fixture MUST match its recorded result and complete set of rejection error
identifiers, instance pointers, and schema pointers. A failed fixture MUST NOT
remove its example from the schema debt inventory. [YWE-REQ-0020]

Error identifiers use `JSON_SCHEMA_` followed by the assertion keyword in
uppercase. For example, `JSON_SCHEMA_MINITEMS` at `/source_refs` identifies an
empty provenance collection rejected by the targeted `minItems` assertion.
For `required` errors, `missing_properties` records the exact absent members so
a different omission at the same assertion cannot satisfy the case.
Union errors are flattened to their leaf assertion witnesses and compared as an
unordered set; library message wording and first-error ordering are not the
acceptance contract. Expected rejections require at least one witness.

`scripts/check_fixture_catalog.py` builds a local `referencing.Registry` from
the explicit schema catalog. Its retrieval callback rejects unknown resources.
It visits actual subschemas, including unused branches and dynamic references,
so an unreachable remote reference cannot evade the offline check. Schema and
instance file paths stay within the repository. Fragment targets must select an
actual schema rather than descriptive metadata.

The dialect remains JSON Schema 2020-12. `format` remains an annotation under
this profile; this increment does not establish new date/time parser semantics.
Recovery, replay, and migration categories are reserved for future executable
coverage. The current cases exercise structural positive, boundary, and reject
behavior and do not certify runtime recovery, replay, or migration algorithms.

Run the focused check with `python scripts/check_fixture_catalog.py .`. The
blocking `m2_fixture_catalog` check is also registered in
`data/validation/repository_checks.json` and runs through
`bash scripts/run_checks.sh`. The machine-readable artifact check independently
uses successful catalog results when computing remaining example-binding debt.
Examples with historical inline schema labels retain their existing debt
treatment; those labels alone do not establish executed instance conformance.

This is an incremental catalog. Remaining descriptive examples, incompatible
historical packets, full lifecycle fixtures, and the roadmap-derived M2
acceptance gate and report still need completion. An empty binding-debt list
alone would not satisfy every M2 deliverable.

## YAML Module Capability Manifests

The fixture loader accepts JSON and YAML (`.yaml` or `.yml`) instances. YAML
mappings MUST have unique string keys, and YAML values MUST be representable as
JSON without changing scalar types. [YWE-REQ-0022] Duplicate keys, dates, binary
values, sets, non-finite numbers, custom tags, and circular aliases are rejected
at this boundary. Quoted strings remain strings; unquoted Boolean and numeric
values retain their parsed types. Schema documents and catalogs remain JSON.

`data/schemas/module_capability_manifest_schema.json` expresses the declared
structural rules in `data/module_capability/module_capability_manifest_schema.yaml`.
Module manifests MUST satisfy its sixteen root required fields, declared field
types and enums, and the rule requiring at least one non-delegable responsibility
for `foundational_truth` or `structural_runtime_truth` authority. [YWE-REQ-0022]
The ten applied manifests and two embedded source examples are bound to this
schema. Boundary cases preserve open objects, optional nested fields, empty
strings, and empty lists wherever the source declares no tighter restriction.

This schema does not implement the source's registry-wide uniqueness, dependency
graph, or prose truth-boundary rules. Their semantic conformance remains open;
structural acceptance is not module lifecycle acceptance. The descriptive YAML
source and existing applied manifests remain unchanged.

## Phase 12 Representation Correction

The earlier schema migration inferred strings for four plural/list-bearing
fields without consulting their existing instances. The generator is preserved
in commit `468f473` in `.github/workflows/m2-schema-migration.yml`: its decoded
payload SHA-256 is
`0e5534fdcb6e6063ad832b5032f0236f5bc756fc22f1f76633ed7da39afdb6f1`.
`convert_descriptor` passes field names without values to `infer_field`, whose
default result is a nonempty string. Commit
`5b30dd50533d00b4c0852d45df3dfac61b3a4147` applied those inferred constraints.

The corrected `truth_scope_summary`, `visibility_conditions`,
`resolution_mode_options`, and `expected_consequence_classes` fields MUST accept
the formerly permitted nonempty strings and nonempty arrays of nonempty strings.
[YWE-REQ-0021] The last field appears in both quest candidate and chain-seed
schemas. Required-field lists remain authoritative. In particular,
`quest_title_policy` was required before the migration; its absent definition
and missing example value remain outstanding rather than receiving an invented
default. The conservative array boundary preserves the prior nonempty-value
constraint; existing array-valued examples are populated, and the quest contract
forbids quests without expected consequence classes. Empty arrays receive an
explicit rejection case rather than an unverified empty-value interpretation.
This correction adds no uniqueness, visibility combination, or title-generation
rule.

The catalog includes the existing content batch and two lore fragments as
positive instances, plus exact field targets that retain legacy strings and
reject empty strings, empty arrays, numeric/empty array items, nulls, and objects.
