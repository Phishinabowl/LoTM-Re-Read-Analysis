# Occurrence Conformance Data

This directory contains the portable V31-V32 occurrence and recurrence fixture corpus.

- `valid-registry.yaml` exercises repeated world-time coordinates, coherent multi-axis bindings, subjective ordering, nested recurrence, explicit branch topology, every core transition profile, internal and externally supplied carryover payload targets, and a permitted causal cycle.
- `expectations.json` defines deterministic cross-runtime query results.
- `invalid-cases.json` defines mutations that both runtimes must reject, including contradictory primary bindings, backward track transitions, invalid transition profiles, ungrounded carryover, and malformed branch lineage.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
