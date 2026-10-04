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
acceptance evidence still need completion. An empty binding-debt list
alone would not satisfy every M2 deliverable.

## M2 Readiness Evaluation

`python scripts/check_m2_acceptance.py . --output <external-report.json>`
evaluates the roadmap's six exit criteria and eight deliverables. It MUST retain
an exact ordered mapping of those obligations and return a failing readiness
result while any obligation is failed or unverified. [YWE-REQ-0023]
The normal suite runs only `--check-definition`; that passing check verifies the
mapping and does not accept M2. Method-specific validation coverage and durable
milestone acceptance evidence still have unverified evaluators.

The evaluator enumerates every JSON/YAML path classified as an example, including
examples outside `examples/`. Historical inline labels provide no executed binding.
Registered case bundles require each case's exact pointer; a document-root binding
cannot cover their cases. Normative YAML needs accepted structural bindings; an
expected rejection cannot certify its conformance. Historical artifacts keep their
recorded classification and do not become active examples through this evaluation.

`python scripts/validate_repository.py --offline --report <external-report.json>`
records executed checks, return codes, context, check-catalog hash, tool versions,
revision, and checkout state before and after execution. Full acceptance evidence
MUST use every applicable check in the local context, an unfiltered selection, a
clean matching revision and catalog, and entirely passing results. [YWE-REQ-0023]
Pass that report with `--repository-report` when evaluating readiness. Reports
saved inside the checkout cannot manufacture clean evidence: their newly created
or modified paths are included in the recorded state.

The offline option denies remote Git protocols during the checks. Schema resolution
independently denies unknown resources through the fixture checker. Dependencies
must be prepared before execution. These controls do not attest that the host's
network interfaces were disabled. A passing normal suite alone remains insufficient
for the unimplemented domain and lifecycle obligations.

## Historical Representation and Preview Bindings

The historical PlayerRuntimeState provenance, authority boundary, and update policy,
and PlayerRuntimeStateDelta changed-field members MUST accept nonempty legacy
strings or open objects while preserving their existing required members and array
constraints. [YWE-REQ-0024] The original examples contain objects; the migration's
generic string inference rejected those representations. The newer reference-based
`player_runtime_state_schema.json` retains its separate contract.

`contract_example_descriptor_schema.json` gives three historical explanatory
formats explicit structural roles: a Phase 10 future-bias preview, a truth-scope
example collection, and quest axiom-pressure previews. Their bindings MUST certify
only those descriptor formats and MUST NOT imply canonical runtime or complete
domain semantic acceptance. [YWE-REQ-0025] Empty values and open properties remain
available where the source does not declare tighter constraints; the observed
missing A4 player reference remains optional for that preview format.

Forty-four additional original examples now have explicit full-root bindings to
their uniquely matching existing contracts. Each was validated in full before
registration. The catalogs retain schema IDs and pointers instead of implementing
a runtime label-guessing resolver. Exact negative witnesses and boundaries cover
the four compatible historical fields and three preview formats.

## YAML Pattern Archetype Records

`pattern_archetype_registry_schema.json` executes the structural contract in
`data/pattern_archetypes/ash_pattern_registry_schema.yaml`. Record bindings MUST
enforce its explicit required fields, types, enums, nested required members, and
cluster member minimum without turning descriptive hints into assertions.
[YWE-REQ-0026] Open fields, unspecified empty-value boundaries, and optional
registry members remain available. The schema belongs to the YWE extension
profile; it does not change the pinned upstream ASH dependency identity.

The catalog binds 47 records in seven original family registries, two seed
records, the seed registry, seven whole family documents, and 45 positive/boundary/reject cases. These bindings
exercise the selected records and seed format. They do not validate the source
descriptor's entire root or certify reference resolution, relationship coherence,
lawful combinations, or generation behavior.

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


## YAML Descriptor Grammars

The pattern registry and module capability descriptor roots have distinct,
explicit YWE-owned format grammars. Descriptors MUST satisfy their grammar
before semantic checks resolve required-field names, enum/record references,
duplicate enum values and inheritance cycles. Hints MUST remain annotations.
[YWE-REQ-0027] This is a conservative new descriptor-format policy, rather than
an assertion that a historical runtime parser implemented these checks.

`check_yaml_descriptor_contracts.py` executes both unchanged YAML source roots
and registered positive, boundary and reject cases. The fixture catalog dispatches
semantic checks only for the two exact descriptor schema root IDs. Semantic
witnesses identify their actual owned `x-ywe-semantic-rules` annotation; they do
not invent JSON Schema keywords or dispatch from arbitrary metadata.

## Ability and Phase 12 Negative Descriptions

The existing ability owner check requires `not_morality_system=true` and
`temporary=true`. The corresponding schema properties MUST retain those constants.
[YWE-REQ-0028] The two false-valued cases now receive the specific constant errors.

Historical ability and Phase 12 negative files describe candidates or scenarios.
Their accepted format bindings MUST remain separate from executed subject or
mutation rejection. [YWE-REQ-0028] Missing source references, missing NPC relation,
missing lore pattern trace and generic quest description are exercised on explicit
accepted controls. The XP-only source, wolf-death and morality cases use selected
assertion projections. Those projections certify only source admissibility,
temporary decoherence or the morality invariant; they do not implement an unlock,
cost or leveling algorithm. The unchanged quest candidate lacking its required
`quest_title_policy` is bound as an exact intended full-root rejection rather than
receiving an invented title policy.

## Source-bound Rejection Scenarios

The separate scenario catalog records the original description's normalized
SHA-256 digest, exact selected source values, owning assertions, validation scope,
and either a direct subject, explicit mutations of an accepted control, or
lexical subjects against owning forbidden terms. Every scenario MUST validate its
source bindings and match the complete expected witness set. Mutation controls
MUST be accepted before mutation. Description-format acceptance MUST NOT establish
intended rejection, and collection cases MUST each have an executed witness.
[YWE-REQ-0029]

The checker rejects changed descriptions, changed owning assertions, unaccepted
controls, mismatched subjects, wrong expected reasons and unrelated error sets.
Every executed schema keyword has its exact owning file, pointer and value
binding. Missing-required-member witnesses also bind each exact required-list
member; a different missing field under the same array cannot stand in for the
intended reason. Every selected member binding must be exercised by a missing-field
error, independently of its possible use as a source literal. Scalar
replacement values bind an exact source literal, or the strictly Boolean inverse
of their executed constant at the same target. Unrelated strings and numeric
substitutes for Boolean values cannot witness the intended scenario.

Local projection keywords also have explicit mappings to their source rules.
These mappings establish mechanical source linkage, rather than executing a
prose rule or domain algorithm. Bound executable keywords must be exercised or
used as explicit projection sources. Lexical cases bind the exact owning term
list they execute.

Hashes normalize UTF-8 line endings so the same source binding works in Windows
and Linux checkouts. Original negative files remain unchanged. The M2 readiness
evaluator counts their exact description units independently from schema-format
coverage. Assertion projections and lexical matches retain their declared limited
scope; neither establishes complete runtime or lifecycle conformance.


## Protected Phase 9 Representation Correction

The original Phase 9 diagnostics, existence-potential and branch-event examples
predate the descriptor migration. The migration inferred string constraints for
five diagnostic arrays, two potential-value objects, numeric `phi_value`, notes,
and branch decision-context/actions. Its generator passed field names without
instance values to the generic string inference, as recorded above.

The correction MUST preserve original descriptive values and migration proofs,
retain accepted legacy nonempty strings, and admit the observed typed containers
or number through exact declared assertion transitions. The proof validator MUST
reconstruct the immutable original migration and reject undeclared edits or
unreviewed baseline stages. [YWE-REQ-0030] Original source and migration commits,
whole-property before/after values, exact value hashes and the requirement ID
are recorded separately from the original migration records.

This preserves the original potential formula and legacy example shapes. It does
not implement potential computation or a cosmology oracle. Open containers and
unspecified array cardinality remain open; no new enum, range, uniqueness or
nested required-field rule is inferred from the example values. Permanent proof
validation also applies when the current diff contains no protected target edit.

The 51 Phase9 field cases retain original string acceptance, exercise the observed
containers/numeric representation, preserve open-container boundaries, and reject
wrong types or empty legacy strings. The four original full roots are independently
bound to their complete schemas. The legacy `QD-001` subledger is resolved after
all four debt categories became empty and all 505 catalog bindings passed with
offline references; strict M2 coverage and acceptance obligations remain open.
