# Yggdrasil World Engine -- Extended Reference

> Built on the [Forsetti Framework v0.1.0](https://github.com/flynn33/Forsetti-Framework)

This document is the comprehensive reference for contributors, integrators, and AI agents working with the Yggdrasil World Engine.

---

## About the Forsetti Framework

The Yggdrasil World Engine is built on the [Forsetti Framework](https://github.com/flynn33/Forsetti-Framework) -- an architecture governance framework that enforces module contracts, runtime policy, and structural integrity. Named after Forseti, the Norse god of justice and reconciliation, the framework provides a consistent way to discover, validate, activate, and govern feature modules while keeping architecture boundaries strict and enforceable.

For the concise integration rules, see [`guide.md`](guide.md).

---

## 1. Cosmology Deep Dive

### Primordial State

Before existence, there was Primordial Darkness. Two cosmic informational forces existed within it: the White Wolf (illumination, revelation, knowledge) and the Dark Wolf (hiddenness, fear, concealment). These forces predate time, matter, realms, gods, and civilizations.

### Creation Event

The Divine Core ignites, gravity emerges, information compresses, and realm layers form. Realms are created through compression of cosmic data around the Divine Core.

### The Nine Realms

The universe stabilizes into nine fixed cosmological states. These are not locations -- they are states of being that players resonate with. The nine realms are: Divine Core, Celestial, Causal, Mental, Astral, Etheric, Physical, Shadow, and Void.

---

## 2. Player Model

Players begin as mortals who have forgotten their celestial heritage. Identity emerges through gameplay, not character creation. The engine generates personal backstory over time based on quests completed, realm attunement, wolf alignment, bloodline resonance, mythic encounters, and prophecy activation.

---

## 3. Alignment System

White Wolf and Dark Wolf are informational forces, not morality. Both can increase simultaneously. A single quest may award both alignments. Alignment is accumulation-only -- it can never decrease.

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

White Wolf and Dark Wolf cannot be killed, exist outside the realm system, and appear during cosmic events. They can guide players, assist in combat, trigger prophecies, and appear in dreams. If defeated in combat, they dematerialize and rematerialize later. They are never enemies.

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
2. `scripts/validate_schemas.py` -- JSON schema validation
3. `scripts/validate_ash_compliance.py` -- ASH cosmological compliance
4. `scripts/run_checks.sh` -- all of the above

CI workflows block merges on any failure.

---

## 15. Governance Files

| File | Purpose |
|------|---------|
| `guide.md` | Concise Forsetti integration rules |
| `developer-guide.md` | Extended guide for engine implementors |
| `wiki.md` | This file -- comprehensive reference |
| `missing_source_documents.md` | Canonical artifact inventory and placeholder-backed tracking |
| `docs/architecture/authored_override_and_tooling_notes.md` | Authored override authority and tooling safety guardrails |
| `docs/architecture/realm_truth_boundary_contract.md` | Boundary contract separating realm truth from interpretive layers |
| `yggdrasil-instructions.json` | Machine-readable architecture rules |
| `agentic-coding-policy.json` | Machine-readable AI agent constraints |
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
