# Occurrence Conformance Data

This directory contains the portable V31-V40 occurrence, participation, recurrence, cardinality, policy, and subject-state fixture corpus.

- `valid-registry.yaml` exercises both role-distinct and semantically identical ordered participations by one subject in one concrete occurrence, stable track-entry ordering, distinct chronology-context references, exact, minimum, maximum, ranged, unknown, complete, representative, unmaterialized, exact-zero, and signed-64-bit cardinality claims alongside repeated world-time coordinates, coherent multi-axis bindings, recurrence policy, state acquisition, carryover, and permitted causal cycles.
- `expectations.json` contributes deterministic cross-runtime query and evaluation results, including participation and entry lookup, explicit occurrence-relative ambiguity rejection, cardinalities ordered by stable ID, explainable indeterminate evaluation, controlled civil-range failures, conflict traces, and contributor lineage.
- `invalid-cases.json` defines 102 mutations that every runtime must reject, including malformed participation targets and values, semantically identical participations without a shared ordering track, invalid track-entry ownership or order, ambiguous occurrence-level transition/state consumers, malformed cardinality bounds, coverage/list combinations, cross-recurrence representatives, numeric overflow, and the earlier occurrence, policy, state, and lifecycle failures.

The paired conformance tools report 87 query/evaluation assertions and add generated 128-record cardinality and 128-participation/track-entry probes. They also introduce synthetic typed owning-pattern and external-pattern effects, global and same-target incompatibility, idempotent, accumulating, and invalid repetition, contributor diagnostics, and conflict-wide authorization blocking through pack declarations alone.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
