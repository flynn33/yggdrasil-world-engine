# Playtest Trace Contract

A playtest trace is an agnostic evidence object used to prove that a planned play path exercises the engine systems.

## Trace is not

- save-game runtime data;
- platform telemetry;
- a scripted cutscene log;
- a QA bug report by itself.

## Trace is

- a structured acceptance artifact;
- a source-of-truth-preserving design proof;
- an evidence chain from choice to consequence.

## Minimum trace fields

- trace id;
- vertical slice id;
- quest id;
- completion mode;
- branch event reference;
- quest reward resolution reference;
- player state references;
- worldstate/location consequence references;
- wolf companion trace reference;
- ability/combat references;
- content signal references;
- future generation bias reference;
- acceptance result.
