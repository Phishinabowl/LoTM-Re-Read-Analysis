# Schema-Pack Conformance Data

This directory owns the shared synthetic corpus for schema-pack composition. The base project is intentionally independent of the LoTM pack catalog so both runtimes validate the contract rather than merely accepting current project data.

- `base/` provides a valid three-pack composition with dependency ordering, capability lifecycle and activation, multiple capability providers, cross-pack controlled-value hierarchy, and occurrence semantic declarations.
- `expectations.json` defines exact positive assertions, structured malformed mutations, and the common scale size used by both runners.

The runners copy `base/` into an isolated operating-system temporary directory before applying each mutation. Repository fixtures are never modified, and temporary data is removed after every run.
