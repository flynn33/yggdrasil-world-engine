# Yggdrasil World Engine Agnostic Specification Roadmap

Status: active development authority
Repository baseline: `v2.0.23`
Machine-readable milestone and status authority: `data/governance/specification_roadmap.json`

Publication status: no GitHub Release objects or YWE Agnostic Specification
releases have been published. Existing `v2.0.x` Git tags, including historical
annotations that use release wording, identify repository baselines only.

## Purpose

This roadmap governs completion of the platform-neutral Yggdrasil World Engine
specification. It records what the repository has already established, what
remains incomplete, the dependency order for future work, and the evidence
required before any subsystem or release may be called complete.

Historical phase acceptance is preserved as provenance. It does not by itself
mean that a subsystem is normatively complete, schema-complete,
conformance-tested, or release-ready.

Platform products remain deferred until M10 is accepted. A platform-neutral
reference oracle and a mock adapter are specification conformance artifacts;
they are not platform products.

## Status vocabulary

| Status | Meaning |
|---|---|
| `complete` | All milestone exit criteria and evidence are satisfied |
| `in_progress` | The milestone is the active repository program |
| `planned` | Scope is approved but work has not reached its exit gate |
| `blocked` | A recorded dependency or decision prevents progress |
| `deferred` | Work is intentionally prohibited or postponed |

Every subsystem is measured on five independent dimensions:

1. Historical phase gate accepted.
2. Normative artifact complete.
3. Executable schema complete.
4. Conformance tested.
5. Release-ready.

### Milestone dashboard

| Milestone | Indicator | Status | Dependencies | Program outcome |
|---|---|---|---|---|
| M0 | 🟢 | `complete` | None | One truthful repository baseline |
| M1 | 🟢 | `complete` | M0 | Normalized canon, terminology, and governance |
| M2 | 🟡 | `in_progress` | M1 | Executable contracts, schemas, and fixtures |
| M3 | ⚪ | `planned` | M2 | Complete deterministic core semantics |
| M4 | ⚪ | `planned` | M3 | Persistence, branching, and multiplayer protocols |
| M5 | ⚪ | `planned` | M3, M4 | Complete content-generation engines |
| M6 | ⚪ | `planned` | M4, M5 | Complete abilities, companions, rewards, and prior phases |
| M7 | ⚪ | `planned` | M6 | Combat and encounter foundation |
| M8 | ⚪ | `planned` | M5, M7 | Environment, world, and society profiles |
| M9 | ⚪ | `planned` | M3, M4, M5, M6, M7, M8 | Whole-system conformance and agnosticism proof |
| M10 | ⚪ | `planned` | M9 | Specification freeze, publication, and platform authorization |

Indicators: 🟢 complete, 🟡 in progress, ⚪ planned, 🔴 blocked, and ⏸️ deferred.

## Repository assessment

The repository contains a substantial architecture and conformance corpus, but
the agnostic specification is not yet release-ready. The current repository
suite preserves useful authority and phase guardrails, while the rebuilt check
catalog introduces real JSON Schema meta-validation, YAML validation, roadmap
governance, version synchronization, platform-boundary enforcement, unit tests,
and an explicit quality-debt ratchet.

### Subsystem maturity matrix

The machine-readable matrix records the next governing milestone, responsible
role, repository-local evidence, and open work for every row. Status values are
`complete`, `partial`, `not_started`, `not_applicable`, `deferred`, and
`not_ready`.

| Subsystem | Phase gate | Normative | Schema | Conformance | Release | Next |
|---|---|---|---|---|---|---|
| Authority and engine-game boundaries | `not_applicable` | `complete` | `complete` | `complete` | `complete` | M1 |
| ASH algebra and reference oracle | `complete` | `complete` | `partial` | `complete` | `not_ready` | M3 |
| Cosmology realms and branch reality | `complete` | `partial` | `partial` | `partial` | `not_ready` | M4 |
| Player runtime origin and progression | `complete` | `partial` | `partial` | `partial` | `not_ready` | M4 |
| Perception worldstate and location | `complete` | `partial` | `partial` | `partial` | `not_ready` | M4 |
| Quest NPC and lore generation | `complete` | `partial` | `partial` | `partial` | `not_ready` | M5 |
| Artifact and creature engines | `not_applicable` | `partial` | `not_started` | `partial` | `not_ready` | M5 |
| Myth and prophecy engines | `partial` | `not_started` | `not_started` | `partial` | `not_ready` | M5 |
| Ability and power system | `complete` | `partial` | `partial` | `partial` | `not_ready` | M6 |
| Companion and reward resolution | `partial` | `partial` | `partial` | `partial` | `not_ready` | M6 |
| Combat and encounter system | `not_started` | `not_started` | `not_started` | `not_started` | `not_ready` | M7 |
| Persistence replay migration and multiplayer | `not_applicable` | `not_started` | `not_started` | `not_started` | `not_ready` | M4 |
| Environment manifests and society profiles | `not_applicable` | `not_started` | `not_started` | `not_started` | `not_ready` | M8 |
| Authoring and generic adapter protocol | `not_applicable` | `partial` | `not_started` | `partial` | `not_ready` | M9 |
| Schema conformance and publication governance | `partial` | `partial` | `partial` | `partial` | `not_ready` | M10 |

### Completed or verified foundations

| Area | Current maturity | Completed work |
|---|---|---|
| Authority hierarchy | Strong foundation | ASH foundation, YWE engine, component, and game-layer responsibilities are documented |
| Engine and game separation | Strong foundation | Agnostic contracts and downstream product responsibilities are separated |
| ASH algebra | Verified subset | Nine-bit state space, fixed codewords, XOR behavior, orbit properties, and exhaustive transition checks |
| Cosmology and realm model | Substantial | Realm mechanics, boundaries, transitions, branch concepts, and pattern archetypes |
| Player, worldstate, quest, NPC, and lore foundations | Historical gates accepted | Phase 9 through Phase 12 contracts, examples, and guardrails |
| Twin Wolf canon | Guarded | Complementary non-moral model and recoverable coherence loss |
| Ability foundation | Historical gate accepted | Phase 14 contracts, schemas, examples, and source-provenance guardrails |
| Companion and reward foundation | Partial | Phase 15A packets and routing foundation |
| Ravenfall reference slice | Demonstrated | Phase 16/17 cross-system traces and current structural guardrails |
| Artifact and creature design | Substantial | Detailed eligibility, generation, manifestation, persistence, and consequence rules |
| Repository governance | Operational | Contribution policy, authority guards, attribution guards, workflows, and baseline history |

### Material work remaining

| Area | Current maturity | Remaining work |
|---|---|---|
| Repository truth | M1 authority closure accepted | Maintain M0 and M1 truth controls while M2 builds executable contracts, schemas, and fixtures |
| Schema system | Incomplete | Complete identifiers, convert descriptive records, bind fixtures, validate instances, and eliminate tracked debt |
| ASH reference oracle | Partial | Context classification, recovery, fallback, containment, safe halt, topology, axioms, and emitter traceability |
| Core engine semantics | Partial | Deterministic algorithms, failure modes, persistence, interfaces, and complete conformance |
| Player origin and perception persistence | Placeholder-backed | Replace placeholders with normative state and lifecycle contracts |
| Persistence and multiplayer | Protocol absent | Snapshots, event log, migration, replay, authority, synchronization, conflicts, and branch merge |
| Myth and prophecy | Partial | Emergence, activation, deflection, fulfillment, expiry, propagation, and bounded feedback |
| Companion Engine | Deferred phase | Complete Phase 13 lifecycle, presence, autonomy, recovery, persistence, and multiplayer rules |
| Reward resolution | Foundation only | Transactional application, atomicity, rollback, replay, and conformance |
| Combat and encounters | Not started | Complete Phase 18 normative package |
| Environment manifests | Prose only | Region, site, threshold, terrain-plan, and encounter-field contracts |
| Society engines | Mostly absent | Faction, civilization, economy, religion, and politics profiles |
| Whole-system conformance | Incomplete | Requirements traceability, semantic fixtures, property tests, replay, independent evaluation, and neutral setting |

## Program principles

- The machine-readable roadmap is the milestone and status authority.
- The check catalog is the sole executable validation registry.
- Existing phase checks remain active as legacy structural evidence until their
  semantics are replaced by M2 and later conformance checks.
- Known debt must be explicitly inventoried and may not grow silently.
- A milestone may be marked complete only when every exit criterion has
  repository-local evidence.
- WRW and Ravenfall are reference-profile evidence, not YWE Core truth.
- Normative Core may not require a rendering engine, operating-system API,
  product framework, or platform-specific runtime.
- Platform product work begins only after M10 acceptance.

## M0 — Establish one truthful baseline

Status: `complete`
Dependencies: none
Indicative effort: 1–2 weeks
Owner role: Repository governance maintainers

Acceptance evidence: `data/governance/m0_acceptance_evidence.json` and
`docs/project/M0_TRUTHFUL_BASELINE_ACCEPTANCE.md`

Deliverables:

- Canonical roadmap and machine-readable milestone status.
- Status vocabulary separating historical acceptance, normative completion,
  schema completion, conformance, and release readiness.
- One synchronized repository baseline version source and explicit publication process.
- Correct phase, source, placeholder, deviation, license, and ownership records.
- Classify artifacts as normative, informative, example, historical,
  deprecated, superseded, or placeholder.
- Divide YWE Core, extension profiles, ASH dependency material, the WRW
  reference profile, and later-release work.
- Keep the platform implementation gate closed through M10.

Exit criteria:

- No conflicting release, status, licensing, scope, or authority claims.
- Every public product promise is assigned to a milestone or formally excluded.
- Every current quality exception is registered in a ratcheted debt inventory.

## M1 — Normalize canon terminology and governance

Status: `complete`
Dependencies: M0
Indicative effort: 2–3 weeks
Owner role: Canon and governance maintainers

Acceptance evidence: `data/governance/m1_acceptance_evidence.json` and
`docs/project/M1_CANON_TERMINOLOGY_GOVERNANCE_ACCEPTANCE.md`

Deliverables:

- Normative keyword policy and stable requirement identifiers.
- Architecture-decision, change-proposal, risk, deviation, and question
  registers.
- Resolve immutable ontology versus mutable worldstate.
- Distinguish realm bit position, structural coordinate, ordinal, and
  presentation order.
- Resolve symbolic-grammar ownership and pin the ASH dependency identity.
- Normalize companion resonance terminology and migration aliases.
- Distinguish append-only history from reversible state effects.
- Formal truth and authority lattice.
- Separate normative YWE Core from WRW-specific content.
- One authoritative source or generated mirror for ASH specifications.

Exit criteria:

- No contradictory normative invariant statement remains.
- Every material decision has a durable rationale.
- Every concept has one canonical glossary definition.

## M2 — Build the canonical contract and schema foundation

Status: `in_progress`
Dependencies: M1
Indicative effort: 4–6 weeks
Owner role: Contract and schema maintainers

Deliverables:

- One JSON Schema 2020-12 profile, URI namespace, catalog, and offline resolver.
- Convert descriptive schema-named records into schemas or rename them by
  their actual role.
- Common identifier, reference, version, time, ordering, request, result,
  event, provenance, diagnostic, error, transaction, compensation,
  idempotency, retry, extension, and deprecation contracts.
- YAML structural schemas.
- Explicit fixture catalog mapping schema, instance pointer, expected result,
  and expected requirement or error identifiers.
- Positive, boundary, reject, recovery, replay, and migration fixtures.
- Meta-schema, instance, reference, identifier, dependency, negative,
  property, and mutation validation.

Exit criteria:

- Every normative schema passes its meta-schema.
- Every reference resolves without a network dependency.
- Every normative fixture is bound to a schema.
- Every reject fixture fails for its intended requirement.
- The schema-quality debt inventory is empty.

## M3 — Complete core deterministic semantics and the reference oracle

Status: `planned`
Dependencies: M2
Indicative effort: 5–7 weeks
Owner role: Core semantics maintainers

Deliverables:

- Final Cosmology, Realm, ASH Pattern, Narrative, Perception, and orchestration
  contracts.
- Context-aware state classification and complete diagnostics.
- Recovery, normalization, fallback selection, containment, and safe-halt
  state machines.
- Topology generation, role assignment, axiom evaluation, complete generation
  planning, and artifact-emitter traceability.
- Deterministic seed, selection, tie-break, numeric, canonical serialization,
  bias merge, decay, normalization, and conflict semantics.
- Standard platform-neutral module lifecycle and interface contract.
- Complete core failure, no-op, diagnostic, and resource-bound behavior.

Exit criteria:

- All 28 canonical invariants have executable tests.
- All five conformance categories pass.
- All states and transitions have exhaustive reference coverage.
- Identical input produces byte-stable canonical output.
- No core placeholder remains.

## M4 — Complete state persistence branching and multiplayer

Status: `planned`
Dependencies: M3
Indicative effort: 4–6 weeks
Owner role: State and synchronization maintainers

Deliverables:

- Final branch-reality and player-runtime-state schemas.
- Player origin, creation, progression, identity, bloodline, attunement,
  companion resonance, memory, and ability-state rules.
- Snapshot, event-log, save, load, replay, rollback, compensation, retry,
  idempotency, and migration protocols.
- Shared, branch, realm, local, player, and perception truth synchronization.
- Multiplayer authority, ordering, conflict detection, deterministic
  resolution, reconciliation, and branch merge.

Exit criteria:

- Save/load and migration preserve normative truth.
- Replaying the event log reproduces the same state.
- Repeated packets cannot duplicate consequences.
- Concurrent-order vectors resolve deterministically.
- Perception cannot mutate shared truth.

## M5 — Finish narrative and content generation engines

Status: `planned`
Dependencies: M3 and M4
Indicative effort: 6–8 weeks
Owner role: Content-system maintainers

Deliverables:

- Final Quest, NPC, Lore, Artifact, Creature, Myth, and Prophecy packages.
- Complete creation, activation, progress, correction, rejection, recovery,
  persistence, completion, failure, and archival lifecycles.
- Artifact binding, transfer, transformation, loss, destruction, residue, and
  consequence semantics.
- Creature intent, ecology, recurrence, death, persistence, and consequence
  semantics.
- Myth emergence, variation, propagation, correction, and bounded social
  distribution.
- Prophecy creation, weighting, activation, fulfillment, deflection,
  transmutation, breaking, and expiry.
- Setting-neutral content fixtures.

Exit criteria:

- Generation context through plan, manifest, consequence or no-op, and future
  bias works end to end.
- Myth cannot silently rewrite fact.
- Prophecy cannot become a deterministic script.
- No placeholder remains in a declared release content module.

## M6 — Close ability companion reward and vertical slice phases

Status: `planned`
Dependencies: M4 and M5
Indicative effort: 5–7 weeks
Owner role: Player-system maintainers

Deliverables:

- Canonical Ability and Power ownership, interface, lifecycle, and capability
  declaration.
- Complete Phase 13 Companion Engine registration, recruitment, presence,
  autonomy, action, dismissal, incapacity, coherence loss, recovery,
  persistence, replay, and multiplayer behavior.
- Transactional Quest Reward Resolver with atomicity, rollback, idempotency,
  provenance, and diagnostics.
- Cross-system ability, companion, artifact, creature, quest, player, and
  worldstate integration.
- Reconciled Phase 16 status and durable Phase 17 acceptance report.
- Neutral scenario coverage alongside Ravenfall.

Exit criteria:

- Every feature engine has exactly one authoritative interface and capability
  declaration.
- Phases 13, 15, 16, and 17 have complete acceptance evidence.
- Ravenfall and the neutral scenario pass the same normative contracts.

## M7 — Build the combat and encounter system foundation

Status: `planned`
Dependencies: M6
Indicative effort: 5–7 weeks
Owner role: Encounter-system maintainers

Deliverables:

- Encounter definition, eligibility, composition, participants, lifecycle,
  timing, ordering, and deterministic seed rules.
- Action, target, cost, resource, effect, resistance, status, interruption,
  outcome, and recovery contracts.
- Combat, threat, social, environmental, ritual, and diagnostic/no-op profiles.
- Nonlethal, retreat, negotiation, surrender, interruption, and failure paths.
- Ability, companion, artifact, creature, quest, location, myth, prophecy,
  future-bias, and worldstate integration.
- Atomic persistence, replay, rollback, multiplayer, validation, and
  conformance evidence.

Exit criteria:

- A complete encounter input-to-persistence trace passes deterministic replay.
- Every result has a consequence packet or diagnostic no-op.
- No rendering, device, library, or platform assumption enters normative
  encounter contracts.

## M8 — Complete environment world and society profiles

Status: `planned`
Dependencies: M5 and M7
Indicative effort: 6–10 weeks
Owner role: World-system profile maintainers

Deliverables:

- World region, realm site, threshold, and encounter field manifests.
- Temporary narrative environment and terrain-plan lifecycle.
- Faction Engine built on existing topology contracts.
- Civilization, Economy, Religion, and Politics extension profiles.
- Claims, legitimacy, succession, resources, exchange, institutions, belief,
  diplomacy, cultural memory, and conflict models.
- Cross-scale integration with quests, lore, encounters, myths, worldstate,
  and future generation.

Exit criteria:

- Every public engine promise is conformant or formally excluded.
- Cross-module dependency cycles are resolved.
- No world-scale engine creates an independent source of canonical truth.

## M9 — Prove agnosticism and whole-system conformance

Status: `planned`
Dependencies: M3, M4, M5, M6, M7, and M8
Indicative effort: 4–6 weeks
Owner role: Conformance maintainers

Deliverables:

- One consolidated validation entry point and stable check catalog.
- Complete requirement-to-contract-to-schema-to-fixture-to-validator-to-report
  traceability.
- Unit, exhaustive, property, reject, fuzz, model, replay, and mutation tests.
- Authoring and content-package provenance, override, audit, trust, security,
  resource, cancellation, and backpressure contracts.
- Generic materialization request/result, capability negotiation, and mock
  adapter.
- WRW/Ravenfall and an unrelated neutral setting profile.
- Portable repository-local evidence, complexity budgets, security review,
  and independent evaluation.

Exit criteria:

- Every normative MUST requirement maps to a passing test or intended
  rejection.
- All positive fixtures pass and all reject fixtures fail for the intended
  requirement.
- Two independent evaluators reproduce the same normative results.

## M10 — Freeze and release the agnostic specification

Status: `planned`
Dependencies: M9
Indicative effort: 2–4 weeks
Owner role: Specification release authority

Deliverables:

- Frozen normative corpus with checksums.
- Final specification manifest, glossary, schema registry, and conformance kit.
- Platform-neutral reference oracle.
- Clean-room implementation, migration, compatibility, and deprecation guides.
- Independent architecture, mathematics, data, security, multiplayer, and
  implementability reviews.
- Resolved risk and deviation registers.
- Final acceptance report and platform-program authorization checklist.

Exit criteria:

- No priority-zero or priority-one issue remains.
- No normative artifact is draft, placeholder, or status-conflicted.
- All acceptance checks run from a clean offline clone.
- Independent review confirms that implementation requires no invented core
  behavior.
- Platform work is explicitly authorized only after this gate passes.

## Dependency order

The milestone dependency path is:

`M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10`

Preparatory work may proceed in parallel, but no milestone can pass before all
dependencies in the machine-readable roadmap are complete. M9 converges every
mandatory subsystem before M10.

The serial sum of milestone estimates is 44–66 work weeks. This is a scope
estimate, not a calendar promise; approved preparatory work may overlap without
bypassing milestone gates.

## Definition of done for a subsystem

A subsystem is complete only when it has:

1. Normative responsibility and authority boundary.
2. Complete lifecycle and state-transition model.
3. Formal inputs, outputs, events, and dependencies.
4. Deterministic algorithm or pseudocode.
5. Failure, recovery, diagnostic, and no-op behavior.
6. Formal schemas and registry entries.
7. Valid, boundary, reject, recovery, replay, and migration fixtures.
8. Semantic validators plus negative and property tests.
9. Cross-module requirement traceability.
10. Conformance report and explicit acceptance record.
11. Synchronized version, changelog, catalog, and source inventory.
12. No unresolved placeholder in accepted scope.

## Release acceptance measures

- One authoritative artifact for every normative concern.
- Every normative schema is meta-schema valid and resolves offline.
- Every positive fixture passes.
- Every reject fixture fails for its intended requirement.
- All ASH invariants and conformance categories pass.
- Canonical output and replay are byte-stable.
- Exactly one authoritative interface exists per engine.
- Every normative MUST requirement has validation evidence.
- The frozen normative corpus contains no placeholder.
- WRW and an unrelated neutral profile pass the same conformance suite.
- Evidence reproduces from a clean offline clone.
- Normative Core contains no platform product dependency.

## Principal risks and controls

| Risk | Control |
|---|---|
| Structural checks mistaken for specification completion | Separate maturity dimensions and add semantic gates |
| Existing debt hidden by permissive validation | Ratcheted machine-readable debt inventory |
| Overfitting to Ravenfall | Require an unrelated neutral setting profile |
| Authority and version drift | Canonical roadmap, status manifest, and synchronized version sources |
| Duplicate interface ownership | Interface registry and dependency validation |
| Unbounded promised scope | Core and extension classification during M0 |
| Platform leakage | Platform boundary check and M10 authorization gate |
| Nondeterministic implementations | Canonical serialization, golden vectors, replay, and independent evaluation |

## Platform authorization rule

Unity, Unreal, Godot, desktop, mobile, service, and other platform product
programs may begin only after M10 is complete and the machine-readable platform
gate is changed from `deferred` to `authorized` in the same accepted release.
