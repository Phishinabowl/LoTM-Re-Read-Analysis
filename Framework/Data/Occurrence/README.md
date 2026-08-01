# Occurrence Conformance Data

This directory contains the portable V31-V34 occurrence, recurrence, policy, and subject-state fixture corpus.

- `valid-registry.yaml` exercises repeated world-time coordinates, coherent multi-axis bindings, subjective ordering, reusable recurrence patterns and concrete executions, non-overlapping phases, typed schedules, lifecycle, nested recurrence, explicit branch topology, every core transition profile, pack-scoped outcome compatibility, scoped defaults and overrides, deterministic selection and conflict traces, state acquisition, state-referencing carryover, and a permitted causal cycle.
- `expectations.json` defines 43 deterministic cross-runtime query and evaluation results.
- `invalid-cases.json` defines 60 mutations that every runtime must reject, including the earlier adversarial failures plus malformed phases, civil and coordinate schedules, applicability, subject-qualified conditions, ordinal predicates, overrides, and incompatible outcomes.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
