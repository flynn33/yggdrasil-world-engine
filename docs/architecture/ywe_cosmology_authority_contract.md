# YWE Cosmology Authority Contract

Status: `required_repository_alignment_contract`  
Version: `0.1.0`  
Scope: `Yggdrasil World Engine repository authority stack`

## Purpose

This contract defines the authority hierarchy for the Yggdrasil World Engine repository and prevents drift between the game layer, the engine layer, the ASH Cosmological Model, and the ASH Pattern System component.

## Canonical hierarchy

```text
Where Ravens Wait: Eternal Reckoning
  = game / narrative layer

Yggdrasil World Engine
  = agnostic game engine

ASH Cosmological Model
  = upstream foundation for YWE and its systems

ASH Pattern System
  = YWE component for pattern integrity, diagnostics, recovery, containment,
    conformance, code resilience, and update/patch stability
```

## Authority ownership

### ASH Cosmological Model owns

```text
nine planes of existence
axioms A1-A6
existence potential Φ
pattern vectors
branching choice realization
leaf branch realities
wolf attractor logic
bloodline resonance meaning
Shadow / Void / Divine Core cosmological roles
mortal / celestial relationship
```

### Yggdrasil World Engine owns

```text
engine-agnostic contracts
runtime systems
worldstate deltas
location mutation
branch reality resolution
quest, NPC, lore, artifact, creature, myth, prophecy, ability, faction, perception systems
host adapter boundaries
```

### ASH Pattern System owns inside YWE

```text
pattern integrity
diagnostics
recovery
containment
safe failure handling
conformance
update resilience
patch stability
regression detection
```

### Where Ravens Wait: Eternal Reckoning owns

```text
player-facing narrative
specific game story
specific quests
specific scenes
specific characters
specific location content
specific prose/dialogue
```

## Required interpretation rule

YWE systems must interpret and manifest the ASH Cosmological Model. The ASH Pattern System component may validate, diagnose, recover, stabilize, and protect those systems, but it does not replace or supersede the cosmological model.

## Forbidden interpretations

```text
ASH Pattern System is the topmost authority.
ASH Pattern System owns the cosmology.
YWE owns the ASH Cosmological Model.
Where Ravens Wait is the engine.
Yggdrasil World Engine is only the game title.
Feature engines may redefine the cosmology.
Platform runtimes may author truth.
```

## Required cross-reference

Repository architecture, master specification, module contract, validation, and conformance documents should reference this contract when explaining authority, generation, diagnostics, resilience, or stability.
