# Occurrence Conformance Data

This directory contains the portable V31-V33 occurrence, recurrence, rule, and subject-state fixture corpus.

- `valid-registry.yaml` exercises repeated world-time coordinates, coherent multi-axis bindings, subjective ordering, reusable recurrence patterns and concrete executions, lifecycle, nested recurrence, explicit branch topology, every core transition profile, typed outcomes and rules, state acquisition, state-referencing carryover, and a permitted causal cycle.
- `expectations.json` defines deterministic cross-runtime query results.
- `invalid-cases.json` defines 47 mutations that every runtime must reject, including the V32 adversarial failures, contradictory primary bindings, reversed/interleaved iterations, invalid lifecycle and transition profiles, malformed rules and state transitions, stale or ungrounded carryover, semantic duplicates, and malformed branch lineage.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
