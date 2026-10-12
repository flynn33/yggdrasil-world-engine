# Realm registry: neutral Core and profile boundary

[YWE-REQ-0051] Decision ADR-0043. Core structural coordinates are exactly b0 through b8; a profile may declare zero to64 realm expressions. A display name or ontology P-number is not a lossless nine-bit state identity. WRW realms.json explicitly binds b0=Divine Core through b8=Void and b6=Physical. The ontology's P1=Physical belongs to another ordered domain. The adapter uses explicit coordinate bindings and refuses unknown/conflicting mappings.

ProfileRealmDefinition fixes the realm ID, coordinate, optional full signature, threshold, veil requirement and allowed-origin facts. RealmEngine.evaluate_access retains every actual declared predicate. RealmEngine.propose_shift returns only PROPOSED_ONLY and cannot commit world/attunement/host state. Neutral Core has no default Physical access; a profile may explicitly define its starting realm.

The original M2 metadata and accepted fixture bodies remain valid. The exact compiler, integer policy, lifecycle and resource rules are in docs/design-planning/m3/m3_core_domain_contract.md and core-domain/CORE_PROFILE_ADAPTER_POLICY.json. Proper names/lore are optional profile expressions. Actual M4 persistent transitions and M5 content remain separate obligations.
