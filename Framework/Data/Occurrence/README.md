# Occurrence Conformance Data

This directory contains the portable V31-V36 occurrence, recurrence, policy, and subject-state fixture corpus.

- `valid-registry.yaml` exercises repeated world-time coordinates, coherent multi-axis bindings, subjective ordering, reusable recurrence patterns and concrete executions, non-overlapping phases, typed schedules including leap-day and maximum civil anchors, lifecycle, nested recurrence, explicit branch topology, every core transition profile, pack-scoped outcome and effect compatibility, scoped defaults and overrides, deterministic selection and conflict traces, state acquisition, state-referencing carryover, and a permitted causal cycle.
- `expectations.json` defines 51 permanent deterministic cross-runtime query and evaluation results, including explainable indeterminate evaluation, leap-day projection, controlled civil-range failures, and accumulating pack-declared effect conflicts.
- `invalid-cases.json` defines 67 mutations that every runtime must reject, including the earlier adversarial failures plus malformed phases, civil and coordinate schedules, applicability, subject-qualified conditions, ordinal predicates, overrides, incompatible outcomes, semantically duplicate rules or nested rule components whose record IDs differ, foreign-pattern predicates/effects, and incompatible rule/effect semantics.

The paired conformance tools add three in-memory extension assertions. They introduce synthetic owning-pattern and external-pattern effects plus a new incompatibility pair through pack vocabulary alone, proving those semantics do not depend on hard-coded effect names. The combined reported total is therefore 54 assertions.

The fixture uses the chronology positions in `Framework/Data/Chronology/valid-registry.yaml` and a synthetic `character:protagonist` subject. It is framework conformance data, not LoTM canon.
