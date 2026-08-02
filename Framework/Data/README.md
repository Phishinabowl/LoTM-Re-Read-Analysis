# Framework Data

This directory contains portable machine-readable data required by framework runtime contracts.

`../testing_methodology.md` defines when these conformance families run, how new defects become permanent vectors, how coverage is retained across versions, and how their results are recorded. This file describes the fixture contents rather than redefining that lifecycle.

`unicode-lookup-16.0.0.json` pins canonical normalization and full default case-folding data for deterministic semantic lookup keys. Consumers must load it through `Tools/Runtime/Python/knowledge_framework/lookup_key_config.py` or `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; do not depend on the host runtime's Unicode version.

The current table was generated from the Unicode Character Database 16.0.0 exposed by CPython 3.14.5. Its mapping counts and behavior are independently validated by both loaders; replacing it is a reviewed data migration rather than an automatic runtime refresh.

`lookup-key-regression-vectors.json` preserves portable equivalent/distinct conformance cases, including Unicode formatting characters that culture-aware string comparers may ignore. Parity checks must normalize both sides and compare the results ordinally.

`Strict-Yaml/` contains the portable mapping-key corpus for the shared configuration-ingestion boundary. Its valid fixture proves quoted ambiguous words and numerals remain textual keys. Malformed fixtures cover Boolean, integer, empty, uppercase, case-colliding, Unicode, punctuation-shaped, complex, and duplicate keys before runtime-native dictionary behavior can diverge.

`Reconciliation/` contains the portable stable-identity reconciliation corpus: one valid schema-v4 registry, expected branch-aware resolutions, branch/traversal-limit cases, and malformed canonical-YAML, scalar, timestamp, shape, resource-budget, and policy fixtures. The paired conformance tools combine it with `Strict-Yaml/`, generate malformed-byte, BOM, Unicode byte-budget, and deep-chain probes at runtime, then remove them so ingestion and iterative behavior are tested without storing large or binary fixtures.

`Temporal/` contains the portable domain-neutral temporal corpus. Schema-2 fixtures exercise open and explicitly unknown bounds, inclusive and exclusive handoffs, mixed precision, complete-unit queries, partial intersections, certainty-specific outcomes, microsecond normalization, timezone and calendar extremes, and malformed input. Expected match/overlap vectors keep Python, PowerShell 7, and Windows PowerShell 5.1 behavior aligned.

`Chronology/` contains the portable domain-neutral chronology corpus. Its valid schema-1 fixture covers negative and five-digit years, era-local direction, ordinary and relative integer axes, descending counters, chronology spans, transitive exact equivalence and order, incomparable coordinate systems, and explicit relations. Malformed fixtures reject forbidden zero, missing eras, duplicate era ordinals, contradictory or duplicate exact order claims, isolated and combined exact order cycles, equivalence-chain conflicts, same-system mappings, missing or cyclic relative anchors, reversed spans, and unknown narrative targets.

`Occurrence/` contains the portable V31-V37 occurrence, recurrence-policy, and subject-state corpus. Its schema-4 fixture covers concrete phases, civil and coordinate schedules, scoped defaults and execution overrides, subject-qualified conditions, priority and resolution groups, pack-defined outcome and rule/effect compatibility, target scope, repetition policy, global and same-target effect conflicts, duplicate nested-component rejection, resolved contributor lineage, explainable indeterminate context, and deterministic evaluation while retaining lifecycle, state acquisition, carryover, repeated-coordinate, nested-loop, branch, transition-profile, and cyclic-causality coverage. Sixty-seven permanent and synthetic extension assertions plus 67 mutation cases run identically in Python, PowerShell 7, and Windows PowerShell 5.1.
