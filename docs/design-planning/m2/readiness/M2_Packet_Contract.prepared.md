# M2 Packet Object and Serialization Contract — Review Draft

**Status:** Proposed bounded contract; not adopted, issued, or implemented.  
**Review ID:** YWE-M2-PRF-20260918  
**Source baseline:** v2.0.23 at `2db1230f638cd065d791c05f1adb7b4b51505c57`.  
**Source register:** `source-register.json`.  
**Purpose:** Turn an established behavioral model into enforceable serialization contracts without redesigning the engine through JSON.

## 1. Scope and authority

This draft does not reopen M0 or invalidate accepted M1 evidence. It responds to defects demonstrated in the current M2 packet artifact and preserves the owner's agnostic, object-oriented, modular, reference-only requirements. The proposed type/constructor rules below are not represented as already approved decisions. Existing product names and compatibility aliases are retained unless a separate accepted migration changes them. [S01-S03, S07-S10]

No native runtime, product framework, source repository, or external runtime package is introduced. Python probes are verification tooling only. Their repository-planning location is governed by `../../decisions/2026-09-19-planning-location.md`; they are not application source. This draft is not the human/machine System Realization Contract set required for dependent implementation.

## 2. Nine local records, not thirty new aggregates

| Existing record | Object role for review | Responsibility / invariant owner | Serialization consequence | Status |
|---|---|---|---|---|
| `AshState` | Immutable finite-state value | State representation boundary within `StateModel`; construction should protect the nine-coordinate invariant | One declared representation; no coercion hidden in schema validation | Existing name and finite domain; stronger construction proposed |
| `CanonicalCodeword` | Immutable validated transformation value | Codeword membership boundary using the pinned 16-element set | Validate actual membership, never trust a claimed membership flag | Existing record and membership rule; construction contract proposed |
| `CosmicPatternSnapshot` | Immutable observation/planning snapshot | Snapshot-producing behavior, not the transport serializer | Preserve current signature, identity, provenance, and plan-nullability distinctions | Owner/lifecycle finalization required |
| `DiagnosticEnvelope` | Diagnostic value/transport record | Existing diagnostics contracts and producing domain behavior | Typed severity/stage/disposition/rule references only after source reconciliation | Affected source decision unresolved |
| `GenerationPlan` | Inspectable plan value | `GenerationPlanner` owns planning; `ArtifactEmitter` owns materialization | Complete self-contained plan; no hidden callbacks or side effects | Materialization boundary source-established [S06] |
| `SourceASHRefs` | Provenance relationship record | Producing operation/assessment owns evidence; a reference container cannot create truth | Specify reference identity, resolution, and allowed embedded data explicitly | Wire/reference policy unresolved |
| `SystemManifestExchange` | Transport between an interpretation and an allowed feature engine | Existing allowed-feature routing; no new truth authority | Encode actual Boolean assertions, not Boolean-schema metadata | Role source-established; wire flags unresolved |
| `AshStateSnapshot` | State observation record | State snapshot producer | Keep distinction from the larger cosmic snapshot until an accepted consolidation exists | Existing name preserved; relationship must be finalized |
| `CanonicalCodewordTrace` | Ordered transformation evidence | Transform/trace-producing behavior | Sequence order and legal codeword membership must be checked | Existing trace role; final representation required |

The other 21 records already delegate through `schema_ref`. Their required fields and owning domain contracts remain with those targets. This work does not invent Player, Quest, World, NPC, or Myth aggregate contracts by copying their packet descriptions. The full routing inventory is in `M2_Readiness_Review.md`. [S02]

## 3. AshState behavioral draft

The following proposal deliberately keeps the existing `AshState` name. It does not silently rename it `PatternState`, reassign plane labels, or make wire objects into domain aggregates.

**Identity and invariants.** An AshState represents one ordered nine-coordinate vector over the binary domain. Equality is equality of all nine coordinate values in order. Its value is immutable once constructed. No realm label, ordinal, codeword-membership claim, operational-stability class, or recovery disposition is inferred merely from successful representation parsing. The pinned source separately defines classification behavior; this proposal does not replace it. [S02-S03, S05]

**Proposed construction boundary.** A named factory or constructor validates the declared input representation before returning a value. An invalid candidate returns a structured failure instead of constructing a partially valid public object. Fractional numbers must not be silently truncated and Boolean/string inputs must not be silently converted to coordinates. These stricter admission rules are proposed corrections: the current Python helper calls `int(...)`, so equivalence to existing behavior is not claimed. Ordinary JSON numeric equivalence, such as a parsed numeric 1 versus lexical `1.0`, requires an explicit wire/canonicalization decision rather than a claim that JSON Schema alone controls lexical spelling. [S03]

**Behavior.** Reading a signature or creating a transformed value must not mutate the source value. A legal transformation consumes a validated canonical codeword and yields the coordinate-wise XOR result as a new valid value. The constructor must not perform corrective movement while pretending only to decode a wire representation.

**Normalization limitation.** Distinguish representation decoding from semantic normalization/correction. The latter is disputed between the recovered analysis and current project-local contract and remains outside this construction draft. No recovery categories or normative normalization rules are changed here. [S01, S05]

**Wire decision still needed.** The descriptor calls `bits` a full nine-bit vector; the implementation uses tuples internally and nine-character signatures for several snapshot fields. Do not choose one representation for every occurrence without a field-specific mapping. The schema can enforce an approved representation but cannot substitute for immutable object construction or invariant ownership.

## 4. CanonicalCodeword behavioral draft

**Identity.** Preserve the pinned 16-member codeword set and its established ordering. The current source supplies exact vectors; a new mathematical basis, parity-only approximation, shortened vector, or reordered index convention is not part of this work. [S03]

**Proposed construction.** Validate both nine-coordinate representation and actual membership in the pinned set. Return a valid immutable value or an explicit failure. A client-provided `membership` string, flag, or assessment is never sufficient evidence of membership. The current descriptor's `must_be_member_of_canonical_C` text states an obligation, not an approved literal wire value. [S02-S03]

**Behavior.** Applying the value through the existing transformation boundary creates a new AshState; it does not mutate arbitrary aggregates. Representation checks are not a substitute for the transformation's source/target relation or its diagnostic obligations. No side effect or framework lookup is part of value construction.

**Wire decision still needed.** The stand-alone record describes `bits`, while traces contain an ordered codeword sequence rendered as signatures in the inspected helper. Specify how each field serializes before issuing schemas. Do not add a mandatory discriminator or new public URI namespace by assumption.

## 5. Conversion rules proposed for the eventual M2 change

1. Keep a descriptive catalog separate from the schemas that validate instances. Preserve the existing catalog's consumers until their migration is reviewed; a filename change is not a semantic conversion.
2. Give each accepted schema an explicit catalog identity and offline resolution route under the project's selected URI policy. That policy has not been selected in this draft.
3. Express literal values as typed assertions (`const`/`enum` as appropriate), not prose or Boolean subschema values mistaken for data constants.
4. Bind each fixture to an exact schema and instance pointer. There is no assumption that one root tagged union already exists or that all 30 records share a discriminator.
5. Preserve accepted M1 aliases as lossless compatibility behavior. Equality of alias/canonical references requires a semantic validator when structural validation cannot establish it.
6. Keep object construction, codeword membership, cross-record identity, reference resolution, provenance integrity, and side effects as separate validation obligations. Schema success must not mint a domain-admission receipt.
7. Reduce the registered debt only after the associated behavior, schemas, fixtures, and repository checks pass. Do not reclassify the problem away to obtain a zero count.

## 6. Proposed acceptance matrix

Review labels below are local draft labels, not new entries in the normative requirement register.

| Review case | Intended evidence after contract approval | Present status |
|---|---|---|
| C01 — Valid AshState construction | All 512 nine-bit vectors construct; values remain immutable | Not executed against a revised implementation |
| C02 — Representation rejection | Wrong width, missing data, nonbinary values, and unsupported representations reject at the construction boundary | Root schema counterexamples reproduced; proposed constructor not implemented |
| C03 — Codeword membership | Exactly the pinned 16 vectors admit as codewords; other well-formed states reject as codewords | Required future evidence, not claimed passed |
| C04 — Transformation | Legal XOR result, original unchanged, trace retains order | Required future evidence |
| C05 — Wrong root/record target | Null/scalars and unrelated records reject under their bound object schema | Baseline root accepts all 16 probes |
| C06 — Boolean intent | Forbidden truth authority remains false; planning-before-materialization holds | Direct-lift counterexamples reproduced |
| C07 — Reference/alias consistency | Offline resolution, explicit embedded/reference alternatives, lossless aliases | Contract decision and tests pending |
| C08 — Planner/emitter boundary | Planning has no side effects; emitter receives complete plan | Existing contract retained; no new execution result |
| C09 — Diagnostics/recovery | Enumerations and transitions agree with approved source binding | Held pending source reconciliation |
| C10 — Regression/debt | Full repository suite passes; relevant debt closure has evidence | Suite unavailable in current environment |

## 7. Change boundary and exit

The eventual edit set should contain only the accepted local record contracts/schemas, shared primitives actually needed by them, fixture/catalog entries, focused validation tests, and synchronized debt/source records. It must not alter unrelated feature schemas, M0/M1 evidence, the ASH mathematical baseline, platform gates, or upstream repositories.

This draft is ready for source/owner review, not for implementation issuance. Next substantive work is to settle the two value-object construction/wire decisions above, complete their source mapping, and then produce the smallest conformant schema slice. Broader unresolved diagnostics and framework issues should not become a reason to restart the project or redesign all modules.

## Planning-location update — September 19, 2026

The historical two-value questions in sections 3–4 were advanced into the tested candidate at `../ash-values/Ash_Value_Contract.candidate.md`. That candidate is not an approved engine contract. The approved storage location is now `docs/design-planning/`, with publication still pending.
