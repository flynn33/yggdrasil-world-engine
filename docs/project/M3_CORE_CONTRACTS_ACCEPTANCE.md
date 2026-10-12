# M3 Core contracts acceptance

M3: ACCEPTED

Tested implementation: `504e297737fa0a79ab19d6edd63f9fcbc5c139e7`.
Normalized source-state digest: `b539e35aa4abfeb11f1c2f76ec94431520109a77ffae3368c02a269c6ecc5b8c` (1428 source files; only the six fixed evidence paths are excluded).
Executable obligation mapping SHA256: `326b1ae1e087229fa8445558d2269384c007b9189b7834f451ebfd749cc8ac39`.

The actual unfiltered clean offline local repository run passes 37 checks with zero blocking failures and zero advisories. Ordinary unittest discovery executes 1393 cases: 0 failures, 0 errors, 0 skips, 0 expected failures and 0 unexpected successes.
The parent process retains the complete combined stdout/stderr transcript. The child receipt records actual case callbacks, discovered order, original method-body entry, source/body hashes before and after, and the unchanged obligation mapping. Both report clean before/after state and file-only Git protocols. Acceptance consumes this execution without rerunning exhaustive cases.

The record in `data/governance/m3_acceptance_evidence.json` binds four exact byte archives under `data/governance/evidence/m3/`. Its first accepted introduction is a direct child of the tested implementation and changes only the six fixed evidence paths. Historical verification checks the Git source digest, file modes, archive hashes, immutable history and the tested evaluator’s reproduced complete judgment.

The accepted reference scope includes the neutral Cosmology, Realm, ASH, Narrative, Perception and orchestration modules; exact integer deterministic policies; bounded logical lifecycle; source4 chain/planner/emitter; and current-source four-pure Session. The materialization target is explicit bounded memory documents. World-state persistence, branching, multiplayer and downstream platform realization retain their later roadmap gates.

## Canonical invariant judgments

| Invariant | Judgment |
|---|---|
| INV-STATE-001 | PASS |
| INV-STATE-002 | PASS |
| INV-STATE-003 | PASS |
| INV-CODEWORD-001 | PASS |
| INV-CODEWORD-002 | PASS |
| INV-CODEWORD-003 | PASS |
| INV-CODEWORD-004 | PASS |
| INV-ADMISSIBILITY-001 | PASS |
| INV-ADMISSIBILITY-002 | PASS |
| INV-REALM-001 | PASS |
| INV-REALM-002 | PASS |
| INV-TRANS-001 | PASS |
| INV-TRANS-002 | PASS |
| INV-TOPO-001 | PASS |
| INV-AXIOM-001 | PASS |
| INV-RECOVERY-001 | PASS |
| INV-RECOVERY-002 | PASS |
| INV-RECOVERY-003 | PASS |
| INV-RECOVERY-004 | PASS |
| INV-RECOVERY-005 | PASS |
| INV-PLAN-001 | PASS |
| INV-PLAN-002 | PASS |
| INV-BOUNDARY-001 | PASS |
| INV-BOUNDARY-002 | PASS |
| INV-DIAG-001 | PASS |
| INV-DIAG-002 | PASS |
| INV-DIAG-003 | PASS |
| INV-DIAG-004 | PASS |

## Conformance categories

| Category | Judgment |
|---|---|
| 1 | PASS |
| 2 | PASS |
| 3 | PASS |
| 4 | PASS |
| 5 | PASS |

## Canonical module contracts

| Obligation | Judgment | Required behavior |
|---|---|---|
| M3-MODULE-ARTIFACT-EMITTER-CONTRACT | PASS | ArtifactEmitter Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-AXIOM-EVALUATOR-CONTRACT | PASS | AxiomEvaluator Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-DIAGNOSTICS-MODULE-CONTRACT | PASS | Diagnostics Module Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-GENERATION-PLANNER-CONTRACT | PASS | GenerationPlanner Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-REALM-ENCODER-CONTRACT | PASS | RealmEncoder Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-RECOVERY-ENGINE-CONTRACT | PASS | RecoveryEngine Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-STATE-MODEL-CONTRACT | PASS | StateModel Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-TOPOLOGY-GENERATOR-CONTRACT | PASS | TopologyGenerator Contract — implementation contract (Canonical Baseline) |
| M3-MODULE-TRANSITION-REGISTRY-CONTRACT | PASS | TransitionRegistry Contract — implementation contract (Canonical Baseline) |

## Roadmap deliverables

| Obligation | Judgment | Required behavior |
|---|---|---|
| M3-D1 | PASS | Final Cosmology, Realm, ASH Pattern, Narrative, Perception, and orchestration contracts. |
| M3-D2 | PASS | Context-aware state classification and complete diagnostics. |
| M3-D3 | PASS | Recovery, normalization, fallback selection, containment, and safe-halt state machines. |
| M3-D4 | PASS | Topology generation, role assignment, axiom evaluation, complete generation planning, and artifact-emitter traceability. |
| M3-D5 | PASS | Deterministic seed, selection, tie-break, numeric, canonical serialization, bias merge, decay, normalization, and conflict semantics. |
| M3-D6 | PASS | Standard platform-neutral module lifecycle and interface contract. |
| M3-D7 | PASS | Complete core failure, no-op, diagnostic, and resource-bound behavior. |

## Roadmap exit criteria

| Obligation | Judgment | Required behavior |
|---|---|---|
| M3-C1 | PASS | All 28 canonical invariants have executable tests. |
| M3-C2 | PASS | All five conformance categories pass. |
| M3-C3 | PASS | All states and transitions have exhaustive reference coverage. |
| M3-C4 | PASS | Identical input produces byte-stable canonical output. |
| M3-C5 | PASS | No core placeholder remains. |

## Scope boundaries

All accepted M3 Core obligations pass. The following exact files remain formally assigned to M4 and excluded from the M3 Core acceptance scope:
- `core/narrative_engine/player_origin_arc_rules.yaml` — `M4`, debt `QD-PH-d6f260b2a191`.
- `core/perception_engine/perception_layer_persistence_schema.json` — `M4`, debt `QD-PH-8a1b553f2965`.

The actual eight-document execution and protected diagnostic export are covered by the mapped source-bound tests. Depth-six capacity refusal retains its complete API evidence and makes no target effects. These observations do not certify physical power-loss durability or a downstream platform product.

M4 remains planned. After publishing completed M3, development pauses for the owner’s explicit go-ahead before any M4 work.
