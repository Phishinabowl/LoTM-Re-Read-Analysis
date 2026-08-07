# Effective-Schema Conformance Data

`expected-summary.json` pins the reviewed structural summary of the LoTM effective schema without
turning a full generated export into canonical project configuration. The paired conformance suites
verify the complete contract shape, deterministic serialization, capability states, diagnostics,
ordering, synthetic ambiguity and deprecation cases, malformed failure classification, and scale.

Update this summary only when a reviewed canonical registry change intentionally changes the
effective composition. Runtime parity compares complete generated documents separately.
