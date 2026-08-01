# Framework Data

This directory contains portable machine-readable data required by framework runtime contracts.

`unicode-lookup-16.0.0.json` pins canonical normalization and full default case-folding data for deterministic semantic lookup keys. Consumers must load it through `Tools/lookup_key_config.py` or `Tools/Lookup-Key-Config.ps1`; do not depend on the host runtime's Unicode version.

The current table was generated from the Unicode Character Database 16.0.0 exposed by CPython 3.14.5. Its mapping counts and behavior are independently validated by both loaders; replacing it is a reviewed data migration rather than an automatic runtime refresh.

`lookup-key-regression-vectors.json` preserves portable equivalent/distinct conformance cases, including Unicode formatting characters that culture-aware string comparers may ignore. Parity checks must normalize both sides and compare the results ordinally.

`Reconciliation/` contains the portable stable-identity reconciliation corpus: one valid schema-v2 registry, expected branch-aware resolutions, and malformed policy fixtures. The paired conformance tools also generate and remove a deep-chain fixture at runtime so iterative behavior is tested without storing thousands of repetitive records.
