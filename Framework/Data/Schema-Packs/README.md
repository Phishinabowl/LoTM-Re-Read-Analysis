# Schema-Pack Conformance Data

This directory owns the shared synthetic corpus for schema-pack composition. The base project is intentionally independent of the LoTM pack catalog so both runtimes validate the contract rather than merely accepting current project data.

- `base/` provides a valid schema-3 three-pack composition with dependency ordering, capability lifecycle and activation, multiple capability providers, cross-pack controlled-value hierarchy, typed occurrence semantic declarations, one used state profile plus kind mapping, and one dormant reusable profile.
- `expectations.json` defines exact positive assertions, 56 structured malformed mutations, and the common scale size used by both runners. State-profile cases reject unsupported dimension requirements, profiles without a usable availability dimension, and missing or unknown mappings. Dormant reusable profiles remain legal for core-only and optional-pack composition. The paired suites also prove that delimiter-colliding stable IDs remain two distinct typed incompatibility records.

The runners copy `base/` into an isolated operating-system temporary directory before applying each mutation. Repository fixtures are never modified, and temporary data is removed after every run.
