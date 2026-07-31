# Framework Data

This directory contains portable machine-readable data required by framework runtime contracts.

`unicode-lookup-16.0.0.json` pins canonical normalization and full default case-folding data for deterministic semantic lookup keys. Consumers must load it through `Tools/lookup_key_config.py` or `Tools/Lookup-Key-Config.ps1`; do not depend on the host runtime's Unicode version.

The current table was generated from the Unicode Character Database 16.0.0 exposed by CPython 3.14.5. Its mapping counts and behavior are independently validated by both loaders; replacing it is a reviewed data migration rather than an automatic runtime refresh.
