# Schema-Pack Conformance Data

This directory owns the shared synthetic corpus for schema-pack composition. The base project is intentionally independent of the LoTM pack catalog so both runtimes validate the contract rather than merely accepting current project data.

- `base/` provides a valid schema-3 three-pack composition with dependency ordering, capability lifecycle and activation, multiple capability providers, cross-pack controlled-value hierarchy, and typed occurrence semantic declarations.
- `expectations.json` defines exact positive assertions, 52 structured malformed mutations, and the common scale size used by both runners. The paired suites also prove that delimiter-colliding stable IDs remain two distinct typed incompatibility records.

The runners copy `base/` into an isolated operating-system temporary directory before applying each mutation. Repository fixtures are never modified, and temporary data is removed after every run.
