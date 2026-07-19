# Glossary Documentation Index

Project: Yggdrasil World Engine
Status: active glossary index
Current baseline: `v2.0.23`

## Purpose

The glossary keeps repository terminology stable across architecture
contracts, schemas, lore documents, validation checks, and wiki pages. It is a
reader-facing routing surface for terms that carry acceptance or retrieval
value.

## Documents

| File | Role |
|---|---|
| `ywe_design_glossary.md` | Sole canonical definition authority for YWE architecture, lore, runtime, and validation terms. |
| `../../data/governance/canonical_term_index.json` | Machine-readable heading, scope, alias, migration, and requirement index without duplicate definition prose. |
| `YWE_Design_Glossary_source.txt` | Source note record retained for provenance review. |

## High-Value Term Families

| Family | Examples |
|---|---|
| Authority stack | ASH Model of the Universe, Yggdrasil World Engine, ASH Pattern System component, Where Ravens Wait |
| ASH math | `F2^9`, codeword, XOR transition, orbit, diagnostic envelope |
| Runtime truth | base ontology, leaf branch reality, player runtime state, worldstate delta |
| Generation | generation context packet, interpretation packet, manifest exchange, future generation bias |
| Lore and perception | Twin Wolf, realm attunement, bloodline resonance, myth variant, perception overlay |
| Ability engine | unlock pressure, ability source provenance, ability state update, ability consequence packet |

## Maintenance Rules

- Preserve exact names used by schemas, scripts, and architecture contracts.
- Keep exactly one glossary H2 heading and one term-index record for each canonical concept.
- Do not collapse player-local perception, NPC/faction claims, myth variants,
  and committed worldstate into one truth layer.
- Prefer current authority terms from `docs/architecture/README.md` and
  `docs/architecture/ywe_cosmology_authority_contract.md`.
- Keep glossary updates synchronized with wiki navigation and validation docs.
