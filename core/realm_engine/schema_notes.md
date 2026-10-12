# RealmEngine: M3 reference schema and interface contract

[YWE-REQ-0051] Decision ADR-0043. The normative behavior is defined in [the Core domain contract](../../docs/design-planning/m3/m3_core_domain_contract.md) and [its exact API inventory](../../docs/design-planning/m3/core-domain/CORE_API_INVENTORY.json).

RealmEngine evaluates the declared source/target realm request, attunement, veil and origin predicates. Each evaluated condition remains in the result. Missing facts are PENDING; false eligibility is REFUSED. A successful shift is an immutable RealmShiftProposal with effect_status PROPOSED_ONLY.

The exact class-owned public operations are configuration, evaluate_access, propose_shift and validate_owned_result. Constructors validate immutable configuration/dependencies without hooks or activation. New records use the closed m3_core_domain_schema.json. Existing M2 engine-interface/metadata schemas and accepted fixture bodies remain backward compatible authored formats; wire validation does not confer runtime issuance or committed-world proof.

A proposal does not mutate WorldstateDelta, attunement or a host/world commit. Neutral Core supplies no automatic Physical starting realm. Profile realm IDs and display names are distinct from lossless nine-bit ASH identity. Whole Core packets are limited to1MiB, CoreDiagnostic to8,192bytes and operation diagnostics to32. Domain-specific array maxima remain subject to whole-packet preflight. Refusal retains the actual evaluated prefix; no silent healing, clipping or fabricated ACK occurs. Integer q6 arithmetic, ASCII ties, explicit seeds/logical epochs and fresh compact serialization are fixed by the central policy.

The platform-neutral CoreModuleLifecycle binds an exact configured owner. It limits each operation to64 grants/children,8 simultaneous tickets and64 lifetime ledger entries. Stop latches before cleanup or callbacks; an actually granted late outcome remains interrupted audit and cannot authorize the following ordinary stage. Forsetti owns later host discovery, entitlement and activation. Optional profile names, symbols and content cannot rewrite ASH or Core truth.

This contract finalizes the M3 interface; it does not claim runtime acceptance. Acceptance requires the complete28-invariant/five-category executable judgment, per-module failure/no-op/resource proofs and clean unfiltered validation. M4 persistent world/branch/player acceptance and M5 content activation remain separately owned roadmap work.
