# Entity Conformance Data

This directory contains the vocabulary-neutral entity-registry corpus used by the paired conformance runners.

`base/registry.json` is a complete schema-4 fixture composed against the independent taxonomy and source fixtures. It covers conceptual entities, category membership, active and deferred lifecycle, ambiguous human aliases, canonical/inverse and symmetric relationship types, lineage basis roles, continuity-bound incarnations, applicability bindings, incarnation relationships, entity- and incarnation-subject identity phases, phase bindings, ordered phase relationships, reconciliation targets, and provenance targets.

`expectations.json` defines exact positive counts, invalid service-query counts, structured malformed mutations, and generated scale size. Runners copy and mutate the base registry only in uniquely named operating-system temporary directories, then remove those directories before exit.

The fixture intentionally uses neutral IDs such as `alpha-concept`, `subject-alpha`, and `primary-continuity`. Project-specific category names, characters, adaptations, and labels are not framework conformance vocabulary.
