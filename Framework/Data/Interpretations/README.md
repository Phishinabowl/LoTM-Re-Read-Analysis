# Structural Interpretation Fixtures

This corpus owns schema-1 structural-interpretation conformance. The base registry uses synthetic records and provider IDs; it is not LoTM project data.

The paired suite verifies typed target reuse, deferred provenance-claim validation, local relation canonicalization and cycle rejection, compatible/competing/mutually-exclusive decisions, provenance targets, malformed structures, and structured-summary parity.

`composed-registry.json` is consumed by the hosting conformance suite after it loads the real chronology, occurrence, and hosted-identity fixtures. It keeps mutually exclusive occurrence orderings unresolved while also resolving a chronology context and host carrier through their actual providers. The surrounding composed assertions retain recurrence cardinality, branch lifecycle, backward causality, participant-relative chronology, belief and capability progression, and nested-host reachability in one loaded probe.
