# YWE Core and WRW Reference-Profile Scope Contract

Status: canonical M1 scope contract
Version: 1.0.0
Requirement: `YWE-REQ-0015`

## Purpose

This contract separates universal Yggdrasil World Engine requirements from
Where Ravens Wait: Eternal Reckoning content. It prevents a game-specific rule,
name, story, or fixture from becoming a mandatory engine behavior merely
because both scopes are represented in the same repository or document.

## Normativity Is Scope-Bound

A WRW-specific rule MUST NOT become normative YWE Core truth.
[YWE-REQ-0015]

`normative` means binding within an artifact's declared scope. It does not mean
universal across every repository partition.

- A normative **YWE Core** rule binds every conforming YWE implementation.
- A normative **WRW reference-profile** rule binds the WRW profile and products
  that declare conformance to that profile.
- An informative or example artifact may demonstrate either scope but creates
  no requirement by itself.
- A mixed document must route each claim to a controlling scope authority. Its
  physical path does not grant universal authority.

## YWE Core

YWE Core owns mandatory, setting-neutral, platform-neutral semantics and
contracts, including:

- truth-scope and authority-boundary rules;
- immutable base-ontology and mutable-worldstate distinctions;
- deterministic state, delta, branch, provenance, diagnostic, and
  interpretation contracts;
- engine interfaces and extension points that do not require WRW identities;
- conformance behavior and rejection conditions; and
- downstream host boundaries.

A Core contract may expose generic capabilities for paired resonance,
companions, narrative profiles, locations, factions, myths, prophecies, or
endgames. It must not require the White Wolf, Dark Wolf, Floki, Nathruun,
Ravenfall, Lucifer, Odin, a specific quest, a specific location, or a specific
WRW ending to exercise those capabilities.

## WRW Reference Profile

The WRW reference profile owns game- and narrative-specific material,
including:

- named characters, companions, factions, locations, scenes, quests, and
  dialogue;
- the WRW creation narrative and its reveal order;
- White Wolf and Dark Wolf narrative identity and manifestation canon;
- Nathruun, Floki Hrafen Vilgerson, Ravenfall, the Seventh Gate, and the
  profile's Divine Core endgame; and
- profile-specific presentation, balance, content, and campaign rules.

The profile may specialize Core extension points and demonstrate conformance.
It cannot redefine ASH mathematics, weaken Core invariants, author
platform-specific truth, or make a WRW identity mandatory for a neutral YWE
implementation.

## Dependency Direction

```text
ASH Cosmological Model
  -> YWE Core
    -> optional YWE extension profiles
      -> WRW reference profile
        -> post-M10 downstream WRW products and host materialization
```

Dependencies flow downward. Evidence and defect reports may flow upward, but a
lower layer cannot override the meaning owned by a higher layer.

## Routing Rules

1. A setting-neutral requirement needed by every conforming implementation
   routes to `ywe_core`.
2. An optional setting-neutral subsystem routes to `ywe_extension_profile`.
3. A claim that requires a WRW proper noun, unique story event, profile-only
   cosmology narration, or game-specific outcome routes to
   `wrw_reference_profile`.
4. A WRW fixture validating a Core schema remains WRW evidence; the schema and
   invariant remain Core.
5. A mixed artifact must label its normative reach and link to the controlling
   source for each scope.
6. A summary or example cannot promote its content into Core.
7. Platform realization remains downstream and cannot author Core or WRW
   truth.

## Compatibility Rule

Existing WRW-shaped fields may remain as compatibility surfaces when removing
them would break consumers. Their documentation must identify the canonical
neutral term, the scope of the legacy field, conflict behavior, and the
migration target. Compatibility does not make the legacy name universal Core
vocabulary.

## Acceptance Conditions

The boundary is satisfied when:

- every normative claim has an unambiguous scope;
- Core can be implemented and tested without WRW-specific identities;
- WRW can specialize Core without overriding it;
- mixed documents carry an explicit routing notice;
- compatibility aliases do not create duplicate state; and
- host materialization remains non-authoritative.
