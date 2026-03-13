# ASH Compliance Checklist
## Operational validation checklist for future YWE design files

Date: 2026-03-13  
Project: Yggdrasil World Engine  
Status: agnostic validation artifact

---

# 1. Purpose

This checklist is used to validate whether a new YWE design artifact remains aligned with:

- locked YWE canon
- ASH-first generation law
- established engine/module boundaries
- consequence persistence rules
- myth / prophecy / perception distinctions
- Forsetti-aligned governance language

This file is not a coding checklist.
It is a **design-truth validation checklist**.

---

# 2. Why this file is next

The current design stack already has broad system coverage, and the continuation brief explicitly identifies **`ash_compliance_checklist.md`** as the next missing operational artifact after the glossary. Its role is to validate future files against locked canon and ASH-first generation rules before drift sets in. fileciteturn2file0

That makes this the right follow-up to the glossary: the glossary stabilizes terminology, and this checklist stabilizes design judgment. The brief also keeps scope centered on agnostic design truth, module boundaries, canonical domains, and guardrails rather than activation policy or implementation mechanics. fileciteturn2file1

---

# 3. How to use this checklist

Use this checklist whenever a new YWE file is proposed, including:

- a new rules file
- a schema expansion
- a notes file that introduces new assumptions
- a repo mapping refinement
- a future specialized subsystem spec
- a rewrite of an existing file

## Review sequence

1. Identify what kind of file is being reviewed.
2. Determine which truth layer it belongs to.
3. Run the universal compliance questions.
4. Run the layer-specific compliance questions.
5. Record any failures by severity.
6. Apply repair guidance.
7. Re-check before accepting the file into the design stack.

---

# 4. Severity classes

## Pass
The file is aligned and may proceed.

## Soft fail
The file is repairable without changing the intended subsystem.

## Hard fail
The file breaks canon, architecture, or generation law and must be reworked before use.

## Scope fail
The file may not be wrong, but it belongs to the wrong design layer, module, or ownership domain.

---

# 5. Universal compliance questions

Every future YWE design file should be tested against these questions.

## 5.1 Canon compliance

- Does the file preserve the fixed cosmology?
- Does it preserve the nine fixed realms?
- Does it preserve Divine Core primacy?
- Does it preserve the White Wolf / Dark Wolf as primordial informational forces?
- Does it avoid turning the wolves into morality tokens or killable bosses?
- Does it preserve mortal-origin players with identity revealed through play?
- Does it avoid turning bloodline or prophecy into hard destiny lock?

## 5.2 Generation-law compliance

- Does all meaningful generation still derive from ASH pattern detection?
- Does the file avoid introducing an independent meaning generator?
- Does it avoid random filler-first content logic?
- Does it preserve interpretation multiplicity rather than single-solution flattening?
- Does it keep symbolic pressure ahead of generic task churn?

## 5.3 Consequence compliance

- Does the file preserve persistent consequence?
- Does it avoid reset-to-neutral design?
- Does it produce meaningful residue in memory, relationships, myth, prophecy, perception, faction state, or site state?
- Does it avoid important outcomes that disappear without downstream effect?

## 5.4 Distinction compliance

- Does it keep worldstate, myth, prophecy, and perception distinct?
- Does it avoid treating myth as raw fact by default?
- Does it avoid treating prophecy as a retrospective record?
- Does it avoid letting perception rewrite shared-world truth?

## 5.5 Architecture compliance

- Does the file respect upstream truth priority?
- Does it avoid giving a specialized module ownership over higher-order truth?
- Does it keep module ownership clean rather than fuzzy?
- Does it belong in the layer where it has been placed?

## 5.6 Forsetti-language compliance

- Does it preserve the rule that Forsetti governs activation while YWE governs truth?
- Does it avoid granting external execution environments ownership of YWE truth?
- Does it avoid drifting into activation/governance policy when the artifact should stay agnostic-design only?

---

# 6. Truth-layer classification check

Before judging a file, classify it correctly.

## Foundational canon layer
Examples:
- cosmology truth
- realm ontology
- non-negotiable wolf rules

## Structural runtime layer
Examples:
- archetype registries
- pattern grammar
- interface contracts
- shared schemas

## Emergent state layer
Examples:
- runtime flow
- quest manifestation
- worldstate deltas
- NPC relationship changes

## Interpretive layer
Examples:
- myth emergence
- prophecy activation
- perception overlays
- rumor, doctrine, and omen logic

### Validation question
Is the file making claims appropriate to its truth layer?

#### Soft fail examples
- a notes file casually redefining canon
- a quest template inventing new realm law
- a perception rule implying hard world rewrite

#### Hard fail examples
- a creature spec defining cosmology
- an adapter file declaring what bloodlines mean
- a myth file changing realm ontology

---

# 7. Canon lock checklist

A file hard-fails if it violates any of the following.

## Cosmology locks

- Primordial Darkness remains pre-creation background.
- White Wolf and Dark Wolf predate realms, gods, matter, and time.
- Creation begins with Divine Core ignition.
- Divine Core remains cosmological origin, not ordinary zone content.

## Realm locks

- There are nine fixed realms.
- Realms are fixed cosmological states.
- Players change resonance, not realm structure.
- Physical Realm access is always retained.
- Realm shift requires attunement plus thin veil / place-of-power conditions.

## Player-model locks

- Players begin as mortals with veiled celestial memory.
- Identity is revealed through play.
- Bloodline influences eligibility and salience, not fixed destiny.

## Wolf-system locks

- White Wolf and Dark Wolf are not morality tracks.
- Alignment only accumulates.
- Both wolves may increase from the same quest depending on interpretation.
- Wolves cannot be permanently killed.

## Terrain locks

- Persistent geography is developer-authored.
- YWE may generate temporary narrative environments only.
- Temporary spaces may leave residue but must not silently become persistent geography.

These locks are repeatedly preserved in the current continuation brief and guardrail work. fileciteturn2file7 fileciteturn2file8

---

# 8. ASH-first generation checklist

A future file passes this section only if all meaningful outputs remain downstream of:

**ASH State → Pattern Detection → Narrative Interpretation → Manifestation / Consequence / Future Pressure**

## Required checks

- Does the file name its ASH or pattern dependency explicitly or implicitly?
- Does it treat symbolic grammar as upstream rather than optional flavor?
- Does it avoid free-floating procgen logic?
- Does it preserve compatibility logic rather than brute-force combinatorics?
- Does it keep content meaning-bearing rather than merely content-bearing?

## Common soft fails

- file uses symbolic labels decoratively but not structurally
- file generates content from location tags alone
- file uses random selection with no pattern pressure weighting

## Common hard fails

- “standalone random quest generator”
- “artifact rarity table that decides lore importance by itself”
- “creature/ecology system that invents meaningful threats without pattern input”

The current stack repeatedly defines pattern-origin generation as non-negotiable. fileciteturn2file8 fileciteturn2file10

---

# 9. Identity-through-play checklist

Use this section for any file touching players, bloodlines, oaths, quests, mythic status, or prophecy relevance.

## Required checks

- Does the file preserve mortal-origin framing?
- Does it preserve progressive revelation instead of frontloaded certainty?
- Does it create pressure, burden, or consequence rather than only reward?
- Does it allow multiple plausible identity directions?
- Does it avoid class-like premature totalization of the player?
- Does it preserve choice-shaped becoming?

## Soft fail examples

- “lineage unlock gives too much certainty too early”
- “prophecy strongly implies a role but still leaves interpretation”

## Hard fail examples

- “the player is permanently assigned as the lost heir at start”
- “bloodline equals mandatory role”
- “prophecy guarantees one fixed end-state”

---

# 10. Consequence persistence checklist

Use this section for quest, runtime, NPC, faction, worldstate, myth, prophecy, and perception files.

## Required checks

- Does the file define what changes after meaningful events?
- Are those changes scoped and typed clearly?
- Do consequences persist into future selection pressure?
- Does the file preserve memory, residue, legitimacy, relationship, or world-condition continuity?
- Does it avoid cosmetic-only branching?

## Good signs

- memory updates
- faction response changes
- myth seeds or prophecy weights
- NPC trust or stance shifts
- site activation or residue
- world condition or legitimacy changes

## Failure signs

- reward-only resolution
- no future state effects
- “quest complete” with no memory spine
- big event with no myth/prophecy/perception aftermath

The brief’s quality bar explicitly prefers residue over reset and consequence over cosmetic branching. fileciteturn2file10

---

# 11. Myth / prophecy / perception distinction checklist

This is one of the most important review sections.

## Myth checks

- Is myth retrospective?
- Does myth interpret consequence rather than replace it?
- Can competing versions exist?
- Does myth affect legitimacy, behavior, rumor, doctrine, or expectation?

## Prophecy checks

- Is prophecy prospective?
- Is prophecy modeled as attractor pressure rather than fixed script?
- Does prophecy require convergence rather than isolated declaration?
- Can misreading exist without collapsing the system?

## Perception checks

- Does perception change interpretation, visibility, or salience rather than canonical world fact?
- Does it preserve multiplayer-safe shared-world stability?
- Does it avoid silently becoming geography rewrite?

## Hard-fail examples

- myth treated as official fact automatically
- prophecy treated as guaranteed fate
- perception overlay rewriting permanent map state
- one combined “lore pressure” system with no distinction between myth and prophecy

The current brief and guardrails explicitly preserve these distinctions. fileciteturn2file8 fileciteturn2file10

---

# 12. Module-boundary checklist

Use this whenever a file introduces responsibilities, ownership, or cross-system interactions.

## Questions

- Does the file sit in the correct conceptual owner?
- Is it assigning cosmology truth only to cosmology-level artifacts?
- Is it assigning manifestation logic to the right module?
- Is it assigning interpretive social logic to myth/prophecy/perception rather than to quest templates?
- Does it accidentally make one subsystem the hidden owner of everything?

## Scope-fail examples

- quest file owning realm ontology
- adapter file owning prophecy law
- myth file owning worldstate source truth
- perception file deciding bloodline truth

## Good signs

- upstream truth stays upstream
- downstream systems consume but do not rewrite their providers
- ownership language is explicit
- outputs are clear and bounded

---

# 13. External-environment boundary checklist

Use this for repo, adapter, governance, or environment-facing files.

## Required checks

- Does the file preserve that YWE governs truth?
- Does it preserve that external environments only realize outputs where appropriate?
- Does it avoid granting Unity / Unreal / Godot authority over canon, pattern law, myth law, prophecy law, or bloodline truth?
- Does it keep adapter/integration language downstream?

## Hard-fail examples

- “Unreal owns the prophecy engine”
- “Unity decides realm legality”
- “external runtime generates meaningful lore without YWE truth systems”

The clarified Forsetti framing keeps activation/governance separate from truth ownership. fileciteturn2file5

---

# 14. Layer-specific mini-checklists

## For archetype or registry files

- Are terms canonical and stable?
- Are compatibility rules explicit?
- Are symbols structural rather than decorative?
- Do new archetypes fit the existing grammar rather than bypass it?

## For quest files

- Are chains pressure-bearing rather than task-only?
- Is there choice, interpretation, recontextualization, and cost?
- Are NPC, faction, site, and consequence interactions present?

## For NPC files

- Are NPCs pattern-bearers rather than flat dispensers?
- Do major NPCs have truth function, shadow risk, and relationship dynamics?
- Is distributed truth preserved?

## For worldstate files

- Are deltas typed, scoped, persistent, and canon-safe?
- Does the file avoid direct geography rewrite?
- Does it propagate into myth/prophecy/perception appropriately?

## For myth files

- Do myths emerge from consequence?
- Are competing versions possible?
- Does social spread matter?

## For prophecy files

- Is prophecy future-pressure, not script?
- Are omens, misreading, convergence, and fulfillment aftermath present?

## For perception files

- Is experience downstream of truth?
- Is shared-world stability preserved?
- Are overlays and variants handled without world rewrite?

## For artifact / creature future files

- Do they remain downstream of ASH meaning and narrative context?
- Do they avoid becoming independent loot/ecology generators?
- Do they integrate with myth, prophecy, or perception only where justified?

The brief specifically calls out artifact rules, creature rules, faction topology, perception overlays, and realm mechanics as likely next specialized specs after glossary/checklist. fileciteturn2file0

---

# 15. Repair guidance

## If a file soft-fails

Preferred repairs:

- clarify the owner module
- add explicit upstream dependency language
- reduce certainty
- increase interpretive multiplicity
- add consequence outputs
- split truth, interpretation, and manifestation into separate sections
- remove accidental governance/activation detail from agnostic files

## If a file hard-fails

Preferred repairs:

- remove cosmology drift
- restore fixed-realm ontology
- restore ASH-first generation dependency
- remove destiny lock
- restore myth/prophecy/perception distinctions
- move the file to the proper owner layer if the idea is valid but misplaced
- reject the artifact entirely if the premise itself breaks YWE invariants

---

# 16. Fast rejection triggers

Reject or fully rework any new file if it does any of the following:

- invents new canonical realms casually
- lets players permanently kill a wolf
- converts wolf alignment into morality
- makes bloodline equal fixed fate
- makes prophecy equal script
- makes myth equal raw history by default
- makes perception rewrite the world map
- creates permanent geography by runtime generation without explicit exception
- creates meaningful content with no ASH / pattern basis
- hands YWE truth ownership to an external runtime

---

# 17. Review record template

Use this template when reviewing a future file.

```markdown
## Compliance Review Record

**File under review:**
**Reviewer:**
**Date:**
**Truth layer:**
**Primary owning module/domain:**

### Universal result
- Canon compliance:
- Generation-law compliance:
- Consequence compliance:
- Distinction compliance:
- Architecture compliance:
- Forsetti-language compliance:

### Severity
- Pass / Soft fail / Hard fail / Scope fail

### Problems found
- 
- 
- 

### Required repairs
- 
- 
- 

### Final judgment
- 
```

---

# 18. Final rule

When a future design choice is unclear, prefer the option that better preserves:

- fixed cosmology
- fixed realm ontology
- ASH-first meaning generation
- identity-through-play
- consequence persistence
- myth / prophecy / perception distinction
- shared-world stability
- clean module boundaries
- YWE truth ownership inside the Forsetti-aligned framing

If a design choice weakens those, it should not pass.

---

# 19. Final conclusion

The glossary makes the language precise.
This checklist makes the standards operational.

That combination is what keeps YWE from drifting from a strong design stack into a pile of individually interesting but incompatible subsystems.
