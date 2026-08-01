# Stable Identity Reconciliation Contract

`Project_Config/reconciliation.yaml` schema version 4 is the domain-neutral project-instance audit registry for stable IDs that have been redirected, merged, split, retired, or reclassified. Target types come from selected schema packs and must have exactly one installed provider from taxonomy, resources, sources, entities, or a future registry. The root, `resolution`, record, target, and audit mappings are closed shapes; unknown fields and duplicate YAML keys are errors.

## Record Semantics

Each record has a stable `id`, typed source ID, source-existence state, controlled operation and reason, lifecycle status, audit metadata, and zero or more typed destinations. Source labels use an explicit privacy mode:

- `snapshot` requires `source_label` and preserves the historical display label.
- `redacted` forbids `source_label` and records that a sensitive label was intentionally removed.
- `omitted` forbids `source_label` when no historical label needs preserving.

Operation and reason must form an allowed pair supplied by the selected schema pack. `redirect` and `merge` require one same-type destination. `split` requires at least two same-type destinations. `retire` requires none. `reclassify` requires exactly one destination of a different target type; no other operation may cross types.

`source_state: present` requires the source to remain in its provider and is valid only for redirect-style compatibility records. An active `retire` record requires `source_state: tombstone`; retirement cannot leave the supposedly retired identity current. `source_state: tombstone` requires the source to be absent and reserves that historical identity against reuse. A tombstoned stable ID must not also remain a provider alias. Consumers resolve stable IDs through reconciliation before ordinary alias lookup rather than allowing two mechanisms to claim the same historical key.

`active` records participate in resolution. `superseded` records retain audit history and must lead through `superseded_by_id` to an active record for the same source. `reversed` records are inert history and require the source to be present again.

## Branch-Aware Resolution

An active source may have only one record. Active destination chains must end at current provider records or explicit retirements and must be acyclic. Resolution is iterative and returns `canonical`, `redirected`, `ambiguous`, or `retired` with:

- deduplicated `canonical_targets` for convenience;
- flattened `reconciliation_ids` for compatibility and summary display;
- ordered `branches`, each retaining its own terminal outcome, canonical target if any, and complete reconciliation path.

Any split produces multiple branches and therefore remains ambiguous even if all branches converge on one current target or all branches retire. A resolver never chooses one split branch silently.

The `resolution` mapping requires four positive integer budgets:

- `max_branches` caps terminal branches produced by one resolution;
- `max_records` caps records accepted from one registry;
- `max_targets_per_record` caps direct fan-out from one reconciliation record;
- `max_resolution_steps` caps iterative traversal work for one resolution request.

The loader or resolver raises an explicit limit error before exceeding a bound. These project-owned budgets prevent valid-looking but hostile record sets, split chains, and deep traversals from consuming unbounded resources while preserving every result below the configured limits.

## Audit Modes

Every record declares `audit.mode`:

- `repository-history` derives actor, time, and approval from version control; those explicit fields must be absent. An optional stable `migration_id` may group related changes.
- `explicit` requires a strict timezone-bearing RFC 3339 `recorded_at` and a non-empty `actor_ref`; `approval_ref` and stable `migration_id` are optional. Timestamps require uppercase `T` and `Z`, valid calendar/time values, and UTC offsets no larger than 14 hours.

Audit references identify external or project-owned records without forcing personal information into this registry. Reconciliation records remain provenance-addressable as `reconciliation-record` so evidence for a merge, retirement, or other decision can live in the provenance service.

## Provider Boundary

Providers expose a stable `provider_id`, current stable-record maps, and alias-key maps for the target types they own. Reconciliation targets include only stable identity-bearing records. Relationship rows, bindings, evidence locators, aliases, filesystem placements, graph nodes, and other nested operational records are not redirect targets merely because some are provenance-addressable. Provider types and `reconciliation.target-type` values must close exactly.

## Read Versus Mutation

`Tools/reconciliation_config.py` and `Tools/Reconciliation-Config.ps1` are behaviorally paired read-only loaders and resolvers. They cache current, historical, and active indexes but do not rename files, move folders, rewrite YAML references, modify aliases, update graph IDs, or delete records. Those changes require the planned migration service with preview, validation, rollback information, and an explicit commit boundary.

Portable conformance fixtures live in `Framework/Data/Reconciliation/` and `Framework/Data/Strict-Yaml/`. They exercise strict UTF-8 decoding, canonical mapping-key and scalar ingestion, forbidden YAML composition features, closed record shapes, timestamp parity, byte/parser and record/fan-out/branch/traversal bounds, historical policy, and deep iterative resolution. Run `python Tools/test_reconciliation.py` or `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Reconciliation.ps1` to verify Python, PowerShell 7, or Windows PowerShell 5.1 behavior.
