# Occurrence Conformance Data

This directory contains the portable V31-V38 occurrence, recurrence, policy, and subject-state fixture corpus.

- `valid-registry.yaml` exercises repeated world-time coordinates, coherent multi-axis bindings, subjective ordering, reusable recurrence patterns and concrete executions, non-overlapping phases, typed schedules including leap-day and maximum civil anchors, lifecycle, nested recurrence, explicit branch topology, every core transition profile, pack-scoped outcome and effect compatibility, duplicate cross-rule effect contributions, scoped defaults and overrides, deterministic selection and conflict traces, state acquisition, state-referencing carryover, and a permitted causal cycle.
- `expectations.json` defines 53 permanent deterministic cross-runtime query and evaluation results, including explainable indeterminate evaluation, leap-day projection, controlled civil-range failures, same-target effect conflicts, and resolved-effect contributor lineage.
- `invalid-cases.json` defines 67 mutations that every runtime must reject, including the earlier adversarial failures plus malformed phases, civil and coordinate schedules, applicability, subject-qualified conditions, ordinal predicates, overrides, incompatible outcomes, semantically duplicate rules or nested rule components whose record IDs differ, foreign-pattern predicates/effects, and incompatible rule/effect semantics.

The paired conformance tools add in-memory extension assertions. They introduce synthetic typed owning-pattern and external-pattern effects, global and same-target incompatibility, idempotent, accumulating, and invalid repetition, contributor diagnostics, and conflict-wide authorization blocking through pack declarations alone. The combined reported total remains 67 assertions.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
