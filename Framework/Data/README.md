# Framework Data

This directory contains portable machine-readable data required by framework runtime contracts.

`unicode-lookup-16.0.0.json` pins canonical normalization and full default case-folding data for deterministic semantic lookup keys. Consumers must load it through `Tools/lookup_key_config.py` or `Tools/Lookup-Key-Config.ps1`; do not depend on the host runtime's Unicode version.

The current table was generated from the Unicode Character Database 16.0.0 exposed by CPython 3.14.5. Its mapping counts and behavior are independently validated by both loaders; replacing it is a reviewed data migration rather than an automatic runtime refresh.

`lookup-key-regression-vectors.json` preserves portable equivalent/distinct conformance cases, including Unicode formatting characters that culture-aware string comparers may ignore. Parity checks must normalize both sides and compare the results ordinally.

`Strict-Yaml/` contains the portable mapping-key corpus for the shared configuration-ingestion boundary. Its valid fixture proves quoted ambiguous words and numerals remain textual keys. Malformed fixtures cover Boolean, integer, empty, uppercase, case-colliding, Unicode, punctuation-shaped, complex, and duplicate keys before runtime-native dictionary behavior can diverge.

`Reconciliation/` contains the portable stable-identity reconciliation corpus: one valid schema-v4 registry, expected branch-aware resolutions, branch/traversal-limit cases, and malformed canonical-YAML, scalar, timestamp, shape, resource-budget, and policy fixtures. The paired conformance tools combine it with `Strict-Yaml/`, generate malformed-byte, BOM, Unicode byte-budget, and deep-chain probes at runtime, then remove them so ingestion and iterative behavior are tested without storing large or binary fixtures.

`Temporal/` contains the portable domain-neutral temporal corpus. Valid windows exercise open and closed bounds, inclusive and exclusive handoffs, mixed precision, timezone normalization, uncertain bounds, and explicitly unknown timing. Malformed fixtures and expected match/overlap vectors keep Python, PowerShell 7, and Windows PowerShell 5.1 behavior aligned.
