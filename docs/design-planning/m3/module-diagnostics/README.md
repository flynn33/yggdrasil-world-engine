# M3 module contracts and representation controls

The active source, Realm/Transition, topology/axiom and module Diagnostics contracts
are adopted under YWE-REQ-0045–0048 and ADR-0036–0039. Contract adoption precedes
dependent implementation. These inventories define finite values and capture
boundaries; they do not establish runtime, native export or complete M3 acceptance.

| Contract | Exact companion |
|---|---|
| [Three-baseline source compatibility](../../../architecture/m3_module_source_compatibility_contract.md) | [Source inventory](SOURCE_VECTOR_INVENTORY.json) |
| [RealmEncoder and TransitionRegistry](../../../architecture/m3_realm_transition_contract.md) | [API inventory](../realm-transition/REALM_TRANSITION_API_INVENTORY.json), [standard policy](../realm-transition/REALM_TRANSITION_STANDARD_POLICY.json), [restricted test policy](../realm-transition/REALM_TRANSITION_RESTRICTED_TEST_POLICY.json), [test orbit](../realm-transition/CODEWORD_ORBIT_TEST_PROFILE.json) |
| [Bounded topology and five axioms](../../../architecture/m3_topology_axiom_reference_contract.md) | [Policy](../../../architecture/m3_topology_axiom_reference_policy.md), [business/API inventory](../topology-axiom/BUSINESS_API_INVENTORY.json) |
| [Six-producer Diagnostics](../../../architecture/m3_module_diagnostics_capture_contract.md) | [Capture API](CAPTURE_API_INVENTORY.json), [closed safe graph and reservations](PRODUCER_AND_SAFE_GRAPH_INVENTORY.json) |

The source extension changes exactly three repository-owned Diagnostics pages.
The other 29 canonical source files and the existing F2^9/C16 mathematics remain
exact. Source recognition adds M3_MODULES alongside the retained LEGACY_C78 and
N3_LIFECYCLE complete vectors. Actual Git/source/profile/policy verification and
captured origin authentication remain separate implementation obligations.

[Maximum leaf specimens](SAFE_MAXIMUM_LEAVES.json) and the [bound report](BOUND_REPORT.json)
are synthetic representation controls. The frozen external package's actual replay
and a byte-identical fresh-copy replay passed before adoption. Their commands,
hashes, scope and external locations are in [Project Record section 17](../../Project_Record.md#17-adopted-m3-module-contracts-and-bounded-implementation).
[The adoption receipt](ADOPTION_RECEIPT.json) distinguishes frozen reviewed bytes
from the small adoption-state and wording transformations in current copies.
An external proposal receipt does not claim a replay of changed adoption metadata.

| Producer | Records | Structural retained bound | Reserved bytes |
|---|---:|---:|---:|
| RealmEncoder | 2 | 325,787 | 524,288 |
| TransitionRegistry | 17 | 1,056,069 | 2,097,152 |
| TopologyGenerator | 1 | 391,542 | 2,097,152 |
| AxiomEvaluator | 5 | 470,095 | 1,048,576 |
| GenerationPlanner | 1 | 1,303,968 | 4,194,304 |
| ArtifactEmitter | 65 | 4,333,056 | 8,388,608 |

The table represents conservative encoded shapes, not observed producer executions.
The existing 65,536-byte source/profile/origin support allowance must be measured
at runtime and refused if exceeded. Existing collector capacities are unchanged;
the individual bounds do not promise simultaneous worst-case operations.

The first implementation increment covers the four pure producers. Planner and
emitter registration remains refused until their complete business policies and
owned implementations are separately adopted. M3_MODULES is initially ineligible
for N3 lifecycle operations; a coherent current-source lifecycle policy pair and
integration remain required before M3 acceptance. All five M3 exits remain open.

The owner instruction is to finish, verify and publish M3, then pause for explicit
go-ahead before any M4 work. The current reference work does not activate M4 or
platform products.
