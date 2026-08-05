# Occurrence Conformance Data

This directory contains the portable V31-V39 occurrence, recurrence, cardinality, policy, and subject-state fixture corpus.

- `valid-registry.yaml` exercises exact, minimum, maximum, ranged, unknown, complete, representative, unmaterialized, exact-zero, and signed-64-bit cardinality claims alongside repeated world-time coordinates, coherent multi-axis bindings, recurrence policy, state acquisition, carryover, and permitted causal cycles.
- `expectations.json` contributes deterministic cross-runtime query and evaluation results, including cardinalities ordered by stable ID, explainable indeterminate evaluation, controlled civil-range failures, conflict traces, and contributor lineage.
- `invalid-cases.json` defines 87 mutations that every runtime must reject, including malformed cardinality bounds, coverage/list combinations, cross-recurrence representatives, semantic duplicates, numeric overflow, and the earlier occurrence, policy, state, and lifecycle failures.

The paired conformance tools report 72 query/evaluation assertions and add a generated 128-record cardinality probe. They also introduce synthetic typed owning-pattern and external-pattern effects, global and same-target incompatibility, idempotent, accumulating, and invalid repetition, contributor diagnostics, and conflict-wide authorization blocking through pack declarations alone.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
