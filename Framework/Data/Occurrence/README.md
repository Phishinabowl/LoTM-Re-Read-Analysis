# Occurrence Conformance Data

This directory contains the portable V31 occurrence and recurrence fixture corpus.

- `valid-registry.yaml` exercises repeated world-time coordinates, subjective ordering, nested recurrence, branching, reset and exit transitions, carryover, and a permitted causal cycle.
- `expectations.json` defines deterministic cross-runtime query results.
- `invalid-cases.json` defines mutations that both runtimes must reject, including a child branch that falsely names one of its own occurrences as its fork point.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
