# Provenance Registry Contract

## Ownership

`Project_Config/provenance.yaml` schema version 2 is the sole project-instance store for factual assertions and claim-supersession chains. Subject registries expose stable target records; they do not carry their own assertion collections. Evidence sources, locator media, coverage, position semantics, and authority profiles remain owned by the source registry. Observation and effective timing use the shared domain-neutral contract in `temporal-model.md`.

`Tools/provenance_config.py` and `Tools/Provenance-Config.ps1` are behaviorally paired loaders. They load only after source, entity, and reconciliation registries and compose those registries through typed provenance-target APIs. A controlled subject type without an installed provider, or a subject ID absent from its provider, is invalid.

## Assertions

Every assertion has a globally stable ID and `claim_key`, one controlled subject type and stable subject ID, one controlled claim namespace, an asserted-value snapshot, a controlled assertion status, optional observation and effective windows, and one or more evidence links. An optional dotted/indexed field path must resolve against the normalized target record. Repeated claim keys must retain one subject, namespace, and field-path shape while allowing corroborating or conflicting values.

Each evidence link references one canonical source and one or more globally stable point or range locators. Locators explicitly select a medium and evidence mode allowed by that source. Their positions must satisfy the medium schema and structural validator, remain within the source work and release-object scope, and remain inside matching declared coverage when coverage exists. Verified and inferred assertions require supporting evidence. Disputed assertions require both supporting and contradicting evidence.

## Supersession And Authority

Claim supersession relates a newer claim to an older shape-compatible claim through a scope that targets the older claim. Relationship types come from the selected schema packs, referenced continuities and claims must exist, and the supersession graph must remain acyclic.

Claim evaluation delegates every supporting locator to the source registry's authority profile. The provenance service then compares each assertion's best evidence rank and reports one winner, a corroborating tie, a conflict among equally authoritative values, or an incomparable result across comparison groups. Source priority therefore remains source-owned while assertion grouping remains provenance-owned.

## Extension Boundary

New registries become provenance-addressable by exposing normalized target lookup and contributing their subject types through schema packs. They must not copy locator, evidence, claim, or supersession fields into their own schemas. The stable load order is project and packs, foundational registries, sources, entities or other subject providers, reconciliation, then provenance.
