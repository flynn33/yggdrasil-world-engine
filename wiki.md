# Yggdrasil World Engine -- Extended Reference

> Built on the [Forsetti Framework v0.1.0](https://github.com/flynn33/Forsetti-Framework)

This document is the comprehensive reference for contributors, integrators, reviewers, and repository automation working with the Yggdrasil World Engine.

---

## About the Forsetti Framework

The Yggdrasil World Engine is built on the [Forsetti Framework](https://github.com/flynn33/Forsetti-Framework) -- an architecture governance framework that enforces module contracts, runtime policy, and structural integrity. Named after Forseti, the Norse god of justice and reconciliation, the framework provides a consistent way to discover, validate, activate, and govern feature modules while keeping architecture boundaries strict and enforceable.

For the concise integration rules, see [`guide.md`](guide.md).

---

## 1. Cosmology Deep Dive

### Primordial State

Before existence, there was Primordial Darkness. Consciousness gathered within that darkness until dark matter compacted into the first conscious singularity: the Dark Star.

### Creation Event

The Dark Star creates gravity, increasing gravity creates time, Void forms as containment, and the Dark Star collapses into the first light: the Divine Core. The collapse stabilizes the nine fixed realms or planes and transforms contained consciousness into the first Architects. The first wolves emerge with that creation event to preserve balance against decoherence and Void.

### The Nine Realms

The universe stabilizes into nine fixed cosmological states. In YWE canon, planes and realms are the same ontology category, with `realm` as the preferred repo term. These are not locations -- they are layered states of being separated by liminal space and symbolically understood through ASH cosmology and Yggdrasil. The nine realms are: Divine Core, Celestial, Causal, Mental, Astral, Etheric, Physical, Shadow, and Void.

---

## 2. Player Model

Players begin as mortals who have forgotten their celestial heritage. Identity emerges through gameplay, not character creation. The engine generates personal backstory over time based on quests completed, realm attunement, wolf alignment, bloodline resonance, mythic encounters, and prophecy activation.

---

## 3. Twin Wolf Companion and Alignment Model

White Wolf and Dark Wolf are paired symbiotic companions of consciousness, not morality markers. Every conscious being carries both. Both can increase simultaneously, a single quest may award both alignments, and the healthiest path is balance rather than domination of one wolf over the other. Alignment is accumulation-only -- it can never decrease.

---

## 4. Realm Attunement and Travel

Players gain realm attunement through realm-aligned quests. A realm becomes accessible when attunement meets the threshold AND the player is at a thin veil location. Players always have access to the Physical Realm.

---

## 5. Perception Layer

The world does not change. Player perception changes. Two players at the same location may see entirely different things based on their cosmic state. This is critical for multiplayer compatibility.

---

## 6. Quest Generation

Quests derive from ASH cosmic patterns, not random templates. Every quest supports multiple completion paths, each with different consequences. The quest generation flow is: ASH state -> pattern detection -> player interpretation -> quest manifestation.

---

## 7. Myth Formation

Significant events become mythology. Different factions may produce different versions of the same myth. Myths influence books, songs, cult beliefs, shrine inscriptions, future quests, and world rumors.

---

## 8. Prophecy System

Prophecies are probability weights that make related cosmic patterns more likely to emerge. They are influenced by bloodline resonance, realm attunement, myth participation, and cosmic imbalances.

---

## 9. Wolf Manifestation

White Wolf and Dark Wolf cannot die permanently and appear during cosmic events as visible companions of consciousness. They can guide players, assist in combat, trigger prophecies, and appear in dreams. If they lose coherence in manifestation, they may withdraw temporarily and later return. They are never enemies and must never be framed as rival moral sides.

---

## 10. Terrain Generation

YWE generates only temporary narrative environments (vision realms, celestial trials, shadow labyrinths, ancestral memories). Persistent world geography is created by developers in the host engine, not by YWE.

---

## 11. Engine Interface Pattern

Every core engine and expansion module defines its interface in a JSON file (`engine_interface.json` or `*_engine_interface.json`). The interface specifies:
- Purpose and responsibility
- Layer placement
- Dependencies (what it reads from)
- Methods (what it does)
- Events published and subscribed
- Invariants (what must never be violated)

---

## 12. Module Communication

Modules communicate through events, not direct references. The event bus pattern ensures loose coupling. Published events include: pattern_detected, quest_completed, myth_formed, realm_shift_completed, prophecy_activated, etc.

---

## 13. Data Schema Reference

All data schemas are in the `data/` directory:
- `player_schema.json` -- Player state
- `realm_registry/realms.json` -- Nine canonical realms
- `realm/realm_mechanics_rules.yaml` -- Canonical realm-law rules for boundaries, attunement, manifestation, and transitions
- `realm/realm_boundary_profiles.yaml` -- Canonical boundary profile catalog for lawful threshold behavior
- `realm/realm_transition_examples.yaml` -- Canonical lawful/unlawful transition examples for shift/contact behavior
- `module_capability/module_capability_manifest_schema.yaml` -- Canonical module capability, delegation, and suppression governance schema
- `module_capability/manifests/*.yaml` -- Applied canonical capability declarations for the current YWE core engines and feature modules
- `faction_topology/faction_topology_state_schema.yaml` -- Canonical faction-topology state schema (claims, legitimacy, reform, schism, succession)
- `pattern_archetypes/pattern_schema.json` -- Pattern nodes
- `quest_archetypes/quest_seed_schema.json` -- Quest seeds
- `myth_archetypes/myth_schema.json` -- Myth records
- `bloodline_registry/bloodline_schema.json` -- Bloodlines
- `perception/perception_overlay_rules.yaml` -- Canonical perception overlay rules and truth-boundary constraints
- `modules/prophecy_engine/prophecy_schema.json` -- Prophecies

---

## 14. Validation and Quality Gates

Every change must pass:
1. `scripts/validate_architecture.py` -- directory structure and dependency checks
2. `scripts/validate_schemas.py` -- JSON schema plus canonical YAML/doc artifact validation
3. `scripts/validate_ash_compliance.py` -- ASH cosmological compliance
4. `bash scripts/run_checks.sh` on POSIX shells -- authoritative local suite for architecture, schemas, ASH compliance, conformance, package acceptance, Phase 10-12 guardrails, source-truth alignment, and Phase 14 ability-power checks
5. `scripts/run_checks.ps1` on Windows PowerShell where available -- core validation wrapper; verify parity before treating it as a full replacement for the Bash suite

CI workflows block merges on any failure.

---

## 15. Governance Files

| File | Purpose |
|------|---------|
| `guide.md` | Concise Forsetti integration rules |
| `developer-guide.md` | Extended guide for engine implementors |
| `wiki.md` | This file -- comprehensive reference |
| `docs/master_specification/YWE_MASTER_SPECIFICATION.md` | Foundational engine-first design and cosmology baseline |
| `YWE_REPOSITORY_BOOTSTRAP_PROMPT.md` | Repository bootstrap and structure baseline paired with the master spec |
| `missing_source_documents.md` | Canonical artifact inventory and placeholder-backed tracking |
| `docs/architecture/authored_override_and_tooling_notes.md` | Authored override authority and tooling safety guardrails |
| `docs/architecture/realm_truth_boundary_contract.md` | Boundary contract separating realm truth from interpretive layers |
| `yggdrasil-instructions.json` | Machine-readable architecture rules |
| `agentic-coding-policy.json` | Machine-readable contributor automation constraints |
| `docs/ash_compliance/` | ASH compliance rules and checklist |

---

## 16. Pre-PR Checklist

- [ ] No engine-specific code on main
- [ ] All JSON schemas valid
- [ ] ASH compliance checklist satisfied
- [ ] Layer dependencies respected
- [ ] Engine interfaces defined before implementation
- [ ] Validation scripts pass
- [ ] No independent random generators for meaningful content
