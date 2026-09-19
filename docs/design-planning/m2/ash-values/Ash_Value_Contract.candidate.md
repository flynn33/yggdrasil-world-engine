# AshState and CanonicalCodeword — Object and Wire Contract

**Candidate ID:** YWE-ASH-VALUES-20260918-1  
**Status:** Tested design candidate. Not adopted as repository authority or issued for product implementation.  
**Product baseline:** YWE v2.0.23, commit `2db1230f638cd065d791c05f1adb7b4b51505c57`.  
**Replaces in the prepared review:** The open two-value-object construction and wire questions in sections 3–4 of `M2_Packet_Contract.prepared.md`. It does not replace any approved product contract.  
**Sources:** `source-register.json`. Results: `Verification_Report.md` and `evidence/`.

## 1. What this accomplishes

A state is an ordered pattern of nine binary values. A codeword is one of the sixteen specific patterns permitted as a transformation operand. This contract defines how those two values are constructed, distinguished, exchanged, and checked.

The product's existing type and transformation specifications establish the finite values and XOR operation [N01–N03]. This candidate supplies explicit object-construction and JSON representation choices where the packet description does not supply executable rules [S02–S03]. Those choices are proposals, not retrospectively claimed approvals.

Successful construction means **well-formed represented value**, not operational stability, permission to mutate the world, successful recovery, or accepted domain consequences. Every one of the 512 binary vectors may be represented without deciding any disputed admissibility policy.

## 2. Scope and boundaries

This is a value-boundary experiment, not the M3 reference oracle or an implementation of the complete StateModel. It does not implement classification, semantic normalization, correction, fallback, containment, safe halt, diagnostics envelopes, generation plans, or game objects. The existing normalization disagreement remains outside this work.

ASH Model, APS, and Aeostara remain reference specifications, not runtime dependencies. The experiment introduces no native framework or platform product. Python exists only under `verification/` as a disposable executable check of this candidate; it is not proposed application source.

The 30-record parent packet document is unchanged. Its remaining seven local records and 21 delegated records keep their existing ownership and outstanding obligations. No milestone, accepted M0/M1 evidence, source pin, product version, or schema-debt entry is changed.

## 3. Source-established facts and explicit design choices

| Concern | Source-established baseline | Candidate decision |
|---|---|---|
| State value | Nine ordered coordinates over F2; 512 represented states [N02] | Guard construction; preserve coordinate order and immutable value ownership |
| Codeword value | Exactly the enumerated sixteen vectors, fixed at the baseline [N01] | Validate actual membership on every untrusted construction path |
| Transformation | Coordinate-wise XOR; deterministic, pure, identity and involution [N03] | `AshState.transformedBy(codeword)` returns a new value |
| JSON `bits` | Described as a full nine-bit vector, without executable representation rules [S02] | An array of nine numeric values exactly equal to 0 or 1 |
| Snapshot/trace fields | The inspected helper emits nine-character signatures [S03] | Preserve string representation in those fields; use an explicitly named codec |
| `membership` | Required by the descriptive standalone record, but its prose is an obligation, not a wire literal [S02] | Retain the field as Boolean `true`; recompute membership from `bits` regardless of the assertion |
| Numeric spellings | JSON Schema integer means a number with no fractional part [N06] | Read exact numeric 0/1 spellings, including `1.0`, `1e0`, and `-0`; write integer tokens `0` and `1` |
| Additional members | No closed standalone value-record policy is established [S02] | Close these two narrow record shapes; do not silently ignore extra members |
| JSON text safety | Not established for these records | Reject duplicate keys, invalid UTF-8/JSON, and non-JSON constants; preserve decimal precision before value checks |
| Schema identity | Production namespace decision remains unrecovered | Use a review-local URN only; no production namespace adoption |

These choices are recorded individually in `candidate-decisions.json`, with rationale, alternatives, and reopening conditions. Testing evaluates the choices; it does not approve them.

## 4. Object responsibilities

### AshState

**Role:** Immutable value object representing one element of the nine-coordinate state space.

**Invariants:** Exactly nine binary coordinates in the established order `b0` through `b8`. No plane label, operational status, or codeword restriction is added. Both possible values of the ninth state coordinate remain valid representations.

**Equality:** Two AshState values are equal exactly when every corresponding coordinate is equal. Equality is not object identity, an orbit comparison, or equality to a codeword type.

**Construction:** A named factory validates the entire candidate before publishing the value. Failure returns a local typed failure and no usable state. Construction does not repair, classify, obtain policy permission, mutate an aggregate, or read a service registry.

**Ownership:** The value owns its coordinates. It does not retain a caller-mutable array. Accessors expose a read-only view or a copy. Changing an input or returned serialization array cannot change the original value.

**Behavior:** `signature()` encodes coordinates in the same order. `transformedBy(CanonicalCodeword)` applies the source-defined XOR operation and produces a new AshState value. The source object is unchanged, including for the zero codeword. This does not authorize persistence or world mutation.

### CanonicalCodeword

**Role:** A distinct immutable value object representing an actual member of the pinned canonical set.

**Invariants:** The same nine-coordinate representation plus exact membership in the fixed enumeration. Checking only length, even parity, weight, or ninth coordinate is insufficient. The set is not a user-supplied runtime policy.

**Construction:** Validate representation and actual membership before publication. A client assertion such as `membership: true` cannot make a nonmember valid. Failure publishes no codeword.

**Equality:** Two codewords are equal exactly when their coordinate values match. A same-bits AshState is not implicitly interchangeable with a CanonicalCodeword. Explicit checked construction is required.

**Ordinal:** Preserve the source's enumeration indices 0–15 if an index is needed. This candidate does not add a required ordinal field to a wire record.

**Ownership and effects:** The value is immutable and does not own a world aggregate or mutation authority. Its signature is derived, not separately editable.

### JsonValueCodec

**Role:** A boundary adapter between the specified wire shapes and the two objects. It does not own mathematical truth, state admission, recovery, or domain changes.

Separate entry points handle state records, codeword records, state signatures, codeword signatures, and ordered sequences. A decoder does not guess among representations, strip signature characters, pad a short value, truncate a long value, turn a Boolean into a bit, or drop unsupported fields.

A future native implementation can use appropriate language-native result/error mechanisms. The Python experiment uses explicit exceptions captured by the verifier; that exception mechanism is not a normative platform requirement.

## 5. Exact field-level wire mapping

| Existing field or value | Candidate encoding | Decoder/check |
|---|---|---|
| Standalone `AshState.state_space` | Exact string `F2^9` | Required literal |
| Standalone `AshState.bits` | JSON array, exactly nine numeric 0/1 values | `AshStateRecord` → guarded AshState construction |
| Standalone `CanonicalCodeword.state_space` | Exact string `F2^9` | Required literal |
| Standalone `CanonicalCodeword.bits` | Same array shape, restricted to the sixteen exact vectors | `CanonicalCodewordRecord` → checked codeword construction |
| Standalone `CanonicalCodeword.membership` | Boolean `true` | Required redundant assertion; never substitutes for actual membership |
| Existing snapshot `normalized_state` | String of exactly nine ASCII `0`/`1` characters | `StateSignature`; no semantic normalization is performed by decoding |
| Existing `state_identity.state_signature` | Same signature string | `StateSignature`; vertex/orbit/alias consistency remains separate |
| Each existing `active_codeword_sequence` item | One permitted nine-character codeword signature | `CodewordSignature` |
| The `active_codeword_sequence` container | Ordered array; empty array and repeated codewords preserved | `CanonicalCodewordSequence`; no sorting or deduplication |
| Existing helper transition `codeword` / `result_state` | Codeword signature / state signature respectively | Value checks only; full trace consistency is deferred |

`bits` is not a signature string. A signature is not an array. These are deliberately distinct field encodings for the same underlying values, rather than a permissive union in every field.

The sequence definition does not establish a global unbounded-processing entitlement. Product resource limits and cancellation remain the enclosing operation's responsibility; no arbitrary sequence limit is invented here.

### Examples

State record:

```json
{"state_space":"F2^9","bits":[0,0,0,0,0,0,0,0,1]}
```

This is a valid state representation but not a valid codeword.

Codeword record:

```json
{"state_space":"F2^9","bits":[0,0,0,0,1,1,1,1,0],"membership":true}
```

The same codeword as a sequence item is `"000011110"`. The `membership` member is generated from checked construction. It is not a permission or authority token.

### Consumer-selected type is mandatory

The root of the experimental schema recognizes either standalone record. It cannot know which type a consumer expected. For example, a record without `membership` might be a valid AshState but is not a valid CanonicalCodeword record.

Every real consumer must bind the appropriate `$defs` target or decoder. A passing root-union check is not sufficient for a codeword-only input. Fixtures explicitly demonstrate this distinction. No new discriminator is silently added to legacy messages.

## 6. Numeric and text rules

At the JSON boundary, the accepted numeric values are exactly zero and one. Numeric `1`, `1.0`, and `1e0` have the same value. Negative zero maps to zero. Boolean `true`, string `"1"`, null, and numbers with nonzero fractional parts do not qualify.

This is exact-value interpretation, not truncation or truthiness coercion. An input such as `1.00000000000000000001` must not become accepted merely because a binary floating-point parser rounds it to `1`. The raw-text reader must preserve enough precision to decide whether the original number is exactly zero or one. Equivalent exact-token validation is an acceptable native implementation technique.

The experimental raw reader uses Decimal and adapts the validator's integer type check for exact integral Decimal values. This implements the existing JSON Schema meaning of integer; it introduces no custom schema keyword. Pre-parsed numbers cannot recover information a previous parser already lost, so the raw-input guarantee requires the precision-preserving parse path.

Duplicate keys are rejected before constructing a dictionary-backed record. Invalid UTF-8, malformed JSON, NaN, and Infinity are rejected. Whitespace around a JSON document is permitted; extra whitespace inside a signature string is not.

The experiment has a 16,384-byte input budget as a verification-tool safety limit only. That number is not proposed as the engine's universal packet limit.

## 7. Canonical output for these two records only

After successful construction, the writer emits UTF-8 without a BOM, indentation, spaces, trailing newline, or optional members. Coordinate numbers are the integer tokens `0` and `1`.

Member order is fixed:

- AshState: `state_space`, `bits`.
- CanonicalCodeword: `state_space`, `bits`, `membership`.

Readers accept member order and document-whitespace variations; writers produce the single form above. This is a narrow candidate encoding convention, not adoption of a whole-engine canonical JSON standard. Equal represented values yield equal emitted bytes under this convention.

## 8. Construction and transformation pseudocode

```text
AshState.tryCreate(candidateCoordinates):
    require exactly nine binary coordinate values
    copy into privately owned immutable value storage
    return Success(AshState)
    on failure return Failure(local construction diagnostic), with no state

CanonicalCodeword.tryCreate(candidateCoordinates):
    validate the same coordinate representation
    require actual membership in the pinned sixteen-value set
    return Success(CanonicalCodeword)
    on failure return Failure(local construction diagnostic), with no codeword

JsonValueCodec.readState(record):
    require object, required fields, exact state-space label
    require bits array of exactly nine numeric values equal to zero or one
    require no extra fields
    map exact numeric values into binary coordinates
    return AshState.tryCreate(coordinates)

JsonValueCodec.readCodeword(record):
    require object, required fields, exact state-space label
    require bits array of exactly nine numeric values equal to zero or one
    require actual pinned-set membership
    require membership is Boolean true and no extra fields
    return CanonicalCodeword.tryCreate(coordinates)

AshState.transformedBy(codeword):
    require a successfully constructed CanonicalCodeword
    for each coordinate i from 0 through 8:
        result[i] = this[i] XOR codeword[i]
    return a new AshState(result)
    leave source and codeword unchanged
```

There is no callback to the planner, policy lookup, world mutation, or recovery operation in this slice.

## 9. Error and validation boundaries

Local experimental errors identify representation type, required fields, state-space label, array width, bit value, actual codeword membership, membership assertion, unknown fields, signature, sequence, JSON syntax, or duplicate key. They are not newly issued `YWE-REQ` or `ASH-*` rule identifiers and do not claim to satisfy the engine DiagnosticEnvelope contract.

The fixture catalog binds each case to its exact schema target and instance pointer. Rejection fixtures name the intended schema keyword and instance location, and the expected model error. The checker verifies the intended error exists; it does not depend on a library's first-error ordering.

All schema references resolve within one review-local resource. Unknown external references fail locally without fetching a network resource. The JSON Schema dialect implementation is supplied by the recorded test installation.

## 10. Verification completed and limitations

See `Verification_Report.md` for all observed results. The candidate was exercised over all 512 represented states, all 512 codeword candidates, every one of the 8,192 state/codeword combinations, exact-decimal and malformed text cases, mutation faults, and repeated runs.

This is not independent reviewer approval, whole-system semantic conformance, runtime integration, a repository regression result, M2 acceptance, or debt closure. The old packet artifact and old helper remain unchanged.

The `membership` encoding, closed records, exact numeric reading, text-safety rules, writer convention, and immutable construction discipline are now explicit tested proposals rather than unanswered questions. They remain candidates until incorporated through the applicable project decision and implementation process.

## 11. Next eligible action

Perform one bounded compatibility review of these exact wire choices against existing packet consumers and fixtures, then record the resulting accept/change decision. That review must pay particular attention to required membership, closed records, numeric parsing, and exact schema-target binding. It does not authorize a parent-catalog rewrite, source upgrade, or automatic migration.

Before product edits, the outstanding method/realization binding, source mapping, actual checkout inspection, and full pre-change repository validation remain required. Hold only work affected by those prerequisites; preserve all independent specification progress.
