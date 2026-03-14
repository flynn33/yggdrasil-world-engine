# Module Capability Data

Contains canonical capability-declaration artifacts that describe how YWE
modules participate in Forsetti-governed activation without transferring YWE
truth ownership to external environments.

## Module Capability Manifest Schema

See `module_capability_manifest_schema.yaml` for the canonical schema covering:

- module classification, authority class, activation state, and dependency order
- provides, requires, consumes, and emits capability/state surfaces
- non-delegable versus delegable-compatible responsibilities
- suppression conditions and compatible external capability hooks
- validation rules preserving the split where Forsetti governs lifecycle and YWE keeps truth ownership

## Applied Capability Manifests

See `manifests/*.yaml` for the canonical applied capability declarations for the
current core engines and feature modules. These YAML manifests:

- align with the schema in `module_capability_manifest_schema.yaml`
- declare module authority, dependency order, and activation posture
- define module-specific provides/requires/consumes/emits surfaces
- separate non-delegable YWE truth ownership from delegable-compatible realization support
- remain canonical YWE governance data, distinct from the host-facing Forsetti template JSON files kept beside runtime folders
