# Temporal Model Contract

## Ownership

Temporal windows and precision-aware temporal queries are domain-neutral framework primitives. `Framework/Packs/core/pack.yaml` owns the `temporal.window-kind`, `temporal.bound-kind`, `temporal.precision`, and `temporal.certainty` vocabularies. `Tools/temporal_config.py` and `Tools/Temporal-Config.ps1` are the behaviorally paired parser and comparison kernel. Source, provenance, entity, and future domain registries may consume this kernel; no consuming registry may redefine its own window shape, timestamp resolution, or comparison semantics.

## Canonical Time Values

Calendar values use the proleptic Gregorian calendar in the inclusive year range `0001` through `9999`. Datetimes are uppercase-`T`, timezone-bearing RFC 3339 strings with no more than six fractional digits. The unknown-local-offset form `-00:00` is not an absolute comparable timestamp and is rejected by this profile rather than normalized to UTC. A timestamp's UTC-normalized value must remain inside the supported calendar range. Six digits establish one portable microsecond ceiling across Python and PowerShell; runtimes must not silently retain, round, or truncate finer input.

`year`, `month`, and `date` values represent their complete calendar unit. Internal upper bounds stop at the final portable microsecond of that unit, including the maximum year, month, and date.

## Window Shape

A temporal window is either `interval` or `unknown`.

- An `unknown` window has no bounds. It records that the complete timing is unknown.
- An `interval` has at least one `start` or `end` bound.
- Omitting `start` or `end` creates a genuinely open, unbounded side. This differs from declaring that bound with `kind: unknown`, which records that a boundary exists but its value is unknown.
- A known bound contains exactly `kind: known`, `value`, `precision`, `certainty`, and `inclusive`.
- An unknown bound contains exactly `kind: unknown`.
- Known-bound `precision` is `year`, `month`, `date`, or `datetime`; its value must match that precision.
- Known-bound `certainty` is `exact`, `announced`, `approximate`, or `uncertain`. Certainty belongs to each bound so one interval may preserve different evidence quality at its start and end.
- `inclusive` controls whether the represented precision unit is included. An inclusive coarse start begins at the start of its unit; an exclusive coarse start begins after the whole unit. An inclusive coarse end includes the whole unit; an exclusive coarse end stops before it.

Reversed and empty intervals are invalid when known bounds prove them invalid. This includes an exclusive lower bound at the maximum representable instant and an exclusive upper bound at the minimum representable instant, even when the opposite side is open. Closed mappings reject unknown fields. A missing window is unbounded and is not equivalent to an explicit unknown window or unknown bound.

## Query Semantics

An effective-time query accepts an ISO year, month, date, RFC 3339 datetime, or runtime datetime object. Year, month, and date queries represent their complete unit; a date never silently means midnight. Datetime queries represent one instant.

A query wholly contained by exact known bounds is `effective`. A query wholly outside bounds is no match. A coarse query that only partially intersects an exact window is `indeterminate-partial`.

## Outcomes

Point/range matching returns `unbounded`, `effective`, `indeterminate-partial`, `indeterminate-announced`, `indeterminate-approximate`, `indeterminate-uncertain`, `unknown`, or no match. Window comparison returns `overlap`, `disjoint`, one of the certainty-specific indeterminate outcomes, or `unknown`.

- Exact known bounds produce deterministic effective, overlap, disjoint, or partial-intersection results.
- Non-exact bounds preserve the strongest uncertainty reason instead of collapsing every case into one label. The conservative order is `uncertain`, `approximate`, then `announced`.
- An explicit unknown window or a relevant unknown bound produces `unknown`.
- Known exact bounds may still prove a query or another window disjoint even when the opposite side is unknown.
- Conservative uniqueness checks treat every unknown or indeterminate result as potentially overlapping; only `disjoint` proves separation.

Applicability and precedence services retain the detailed temporal result but classify every `unknown` or `indeterminate-*` candidate as non-winning indeterminate scope state.

## Conformance

`Framework/Data/Temporal/` schema 2 is the permanent cross-runtime corpus. It covers open and unknown bounds, exclusive handoffs, mixed precision, precision-aware queries, partial intersections, all certainty outcomes, microsecond resolution, UTC normalization, minimum/maximum calendar safety, and malformed shapes or values. Run `python Tools/test_temporal.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Temporal.ps1` after changing temporal vocabulary, strict timestamps, parsing, comparison, source applicability, or provenance timing. Add `--json` or `-Json` for matching structured summary fields.
