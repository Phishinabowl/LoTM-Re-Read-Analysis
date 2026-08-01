# Stable Identity Reconciliation Contract

`Project_Config/reconciliation.yaml` schema version 1 is the project-instance audit registry for stable IDs that have been redirected, merged, split, or retired. It is domain-neutral. Target types are supplied by selected schema packs and must have exactly one installed provider from taxonomy, resource, source, entity, or a future registry.

## Record Semantics

Each record has its own stable `id`, a typed source ID, a snapshot `source_label`, an operation, typed destinations, a controlled reason, and lifecycle status. `source_state: present` requires the source to remain in its provider; `source_state: tombstone` requires it to be absent. The tombstone and reconciliation record reserve historical identity and prevent silent ID reuse.

- `redirect` and `merge` require exactly one same-type destination.
- `split` requires at least two same-type destinations and always resolves as ambiguous.
- `retire` requires no destination and resolves as retired.
- `active` records participate in resolution.
- `superseded` records remain audit history and must lead through `superseded_by_id` to an active record for the same source.
- `reversed` records remain inert audit history and require the source to be present again.

An active source may have only one record. Active destination chains must end at current provider records, may pass through tombstones, and must be acyclic. Resolution preserves every traversed reconciliation ID. It returns `canonical`, `redirected`, `ambiguous`, or `retired`; it never selects one branch of a split.

## Provider Boundary

Reconciliation providers expose only stable identity-bearing records. Relationship rows, bindings, evidence locators, aliases, filesystem placements, graph nodes, and other nested operational records are not redirect targets merely because they are provenance-addressable. Provider types and `reconciliation.target-type` values must match exactly so a pack cannot advertise a target without an implementation.

The current providers cover content types, categories, resource kinds/types, source work and release identities, evidence sources, and entity/incarnation/phase identities. All operations preserve target type. Reclassifying a record across types is a migration concern and must not be disguised as a redirect.

## Read Versus Mutation

`Tools/reconciliation_config.py` and `Tools/Reconciliation-Config.ps1` are behaviorally paired read-only loaders and resolvers. They explain current identity; they do not rename files, move folders, rewrite YAML references, modify aliases, update graph IDs, or delete records. Those changes require the separately planned migration service with preview, validation, rollback information, and an explicit commit boundary.

Reconciliation records are provenance-addressable as `reconciliation-record`, allowing evidence for a mistaken duplicate, merge, or retirement without embedding assertions in this registry.
