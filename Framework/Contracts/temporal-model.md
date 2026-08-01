# Temporal Model Contract

## Ownership

Temporal windows are a domain-neutral framework primitive. `Framework/Packs/core/pack.yaml` owns the `temporal.window-kind`, `temporal.precision`, and `temporal.certainty` vocabularies. `Tools/temporal_config.py` and `Tools/Temporal-Config.ps1` are the behaviorally paired parser and comparison kernel. Source, provenance, entity, and future domain registries may consume this kernel; no consuming registry may redefine its own window shape or comparison semantics.

## Window Shape

A temporal window is either `interval` or `unknown`.

- An `unknown` window has no bounds. It records that timing exists conceptually but is not known.
- An `interval` has at least one `start` or `end` bound. Omitting `start` creates an open-start interval; omitting `end` creates an open-end interval.
- Every bound contains exactly `value`, `precision`, `certainty`, and `inclusive`.
- `precision` is `year`, `month`, `date`, or `datetime`. Values must match that precision. Datetimes are strict timezone-bearing RFC 3339 values and are normalized to UTC for comparison.
- `certainty` is `exact`, `approximate`, `announced`, or `uncertain`. Certainty belongs to each bound so one interval may preserve different evidence quality at its start and end.
- `inclusive` controls whether the represented precision unit is included. An inclusive coarse start begins at the start of its year, month, or date; an exclusive coarse start begins after that whole unit. An inclusive coarse end includes the whole unit; an exclusive coarse end stops before it.

Reversed and empty intervals are invalid. Closed mappings reject unknown fields. A missing window is unbounded and is not equivalent to an explicit `unknown` window.

## Outcomes

Point matching returns `unbounded`, `effective`, `indeterminate`, `unknown`, or no match. Window comparison returns `overlap`, `disjoint`, `indeterminate`, or `unknown`.

- Exact known bounds produce deterministic effective/overlap results.
- A non-exact bound produces `indeterminate`; consumers must not silently promote it to an exact winner.
- An explicit unknown window produces `unknown`.
- Conservative uniqueness checks treat `unknown` and `indeterminate` as potentially overlapping; only `disjoint` proves separation.

Applicability and precedence services may report unknown or indeterminate temporal candidates, but those candidates cannot win a time-specific decision as if their bounds were exact.

## Conformance

`Framework/Data/Temporal/` is the permanent cross-runtime corpus. It covers closed and open intervals, exclusive handoffs, mixed precision, UTC normalization, uncertainty, unknown timing, and malformed shapes or values. Run `python Tools/test_temporal.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Temporal.ps1` after changing temporal vocabulary, parsing, comparison, source applicability, or provenance timing.
