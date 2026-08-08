# Validation Run Reporting Contract

**Status:** Accepted Phase 3.1.6 design. Aggregate conformance and compatibility reporting are
implemented and adopted; final closure validation remains pending.

## Purpose

Validation execution strength and validation output verbosity are separate concerns. Selecting a
concise report must never select fewer suites, checks, fixtures, runtimes, assertions, or safety
guards than the corresponding detailed run.

This contract defines the shared reporting boundary for aggregate framework conformance and project
compatibility runs. It supports routine human and agent use without removing the complete semantic
records required by extraction rehearsal, parity comparison, baseline review, or failure diagnosis.

## Reporting Surfaces

Each aggregate runner must expose four complementary surfaces by Phase 3.1.6 closure:

| Surface | Purpose |
| --- | --- |
| Concise human output | Routine interactive progress and final status. |
| Concise structured summary | Stable low-volume automation, CI, and agent consumption. |
| Detailed structured output | Backward-compatible complete runner result for semantic clients. |
| Detailed report export | Complete structured result written to a confined file without requiring the complete document on standard output. |

The established detailed `--json` / `-Json` output remains backward compatible. A new concise
structured switch must use a distinct name. A report export may be combined with concise human or
structured output, but it never changes which validation work executes.

## Concise Document Shape

The concise JSON document uses this top-level order:

```json
{
  "contract": "validation-run-summary",
  "contract_version": 1,
  "runner": "framework-conformance",
  "status": "passed",
  "profile": "baseline",
  "requested_ids": [],
  "selected_count": 0,
  "passed": 0,
  "failed": 0,
  "elapsed_seconds": 0.0,
  "canonical_outputs_unchanged": null,
  "output_kept": null,
  "report_path": null,
  "results": [],
  "failures": []
}
```

Every field is required. A runner uses JSON `null` only where the field does not apply or the value
cannot exist because validation failed before that boundary was established.

## Common Fields

| Field | Meaning |
| --- | --- |
| `contract` | Always `validation-run-summary`. |
| `contract_version` | Concise reporting contract version, initially `1`. |
| `runner` | Stable runner kind: `framework-conformance` or `project-compatibility`. |
| `status` | `passed` only when the complete selected run passed; otherwise `failed`. |
| `profile` | Selected registered profile, `selected` for explicit IDs, or `null` when selection failed before resolution. |
| `requested_ids` | Ordered selected suite or check IDs after registry resolution. |
| `selected_count` | Exact length of `requested_ids`. |
| `passed` | Number of selected IDs that completed successfully. |
| `failed` | Number of failed selected IDs. A pre-execution orchestration failure reports at least one failure even when no result row exists. |
| `elapsed_seconds` | Nonnegative wall-clock duration rounded to three decimal places, or `null` if timing never started. |
| `canonical_outputs_unchanged` | Compatibility protection result; `null` for conformance or when compatibility could not establish it. |
| `output_kept` | Whether scoped diagnostic output remains available; `null` when the runner has no scoped output concept. |
| `report_path` | Repository-relative forward-slash path to a detailed report, or `null`. Absolute machine paths are forbidden. |
| `results` | Ordered concise result rows for completed suite or check attempts. |
| `failures` | Ordered bounded failure rows. |

Elapsed time and a generated retained path are operational metadata. Cross-runtime parity requires
matching field presence, type, nonnegative duration, containment, result order, status, counts, and
semantic fields; it does not require equal elapsed values or equal run-unique path names.

## Result Rows

Every result row contains:

```json
{
  "id": "effective-schema",
  "kind": null,
  "status": "passed"
}
```

`id` is the registered suite or check ID. `kind` is `null` for conformance and the registered check
kind for compatibility. `status` is `passed` or `failed`. Concise rows do not embed child suite
summaries, runtime comparisons, artifact inventories, file hashes, generated documents, or renderer
details; those remain in detailed output.

## Failure Rows And Budgets

Every failure row contains the failed ID when known, a stable failure classification when the runner
can provide one, a normalized excerpt, and `excerpt_truncated`.

The excerpt preserves the beginning of the diagnostic after CRLF normalization. It is limited to 20
lines and 4,096 UTF-8 bytes. Truncation must stop on a valid UTF-8 boundary and set
`excerpt_truncated` to `true`. The complete diagnostic remains in the detailed report and, where the
runner owns scoped artifacts, the retained failure output.

Successful concise output contains no child standard output or standard error. Detailed reports are
not size-limited by this presentation budget.

## Detailed Output Compatibility

The existing runner-specific detailed documents remain authoritative for clients that require their
current nested semantics:

- conformance retains `schema_version`, `profile`, suite counts, and complete ordered suite results
  including child summaries;
- compatibility retains `schema_version`, profile/request state, elapsed time, canonical-output
  protection, scoped-output state, and complete ordered check results.

Adding concise reporting must not rename, remove, reinterpret, or reorder established detailed
fields. The isolated framework extraction rehearsal remains a detailed conformance client because it
compares complete suite summaries across Python, PowerShell 7, and Windows PowerShell 5.1.

## Report Paths And Lifecycle

An explicit report path must resolve to a file beneath the project root. It may replace that exact
file but must not delete its parent, siblings, or unrelated temporary content. Repository-root and
outside-root destinations fail before validation or cleanup begins.

Automatically retained failure reports belong beneath a unique ignored `.tmp/` child owned by that
run. Compatibility may use its existing scoped output root. A successful run removes automatically
owned temporary evidence unless retention was explicitly requested; an explicitly requested report
is user-owned output and remains.

Report JSON uses UTF-8 without a byte-order mark, LF line endings, deterministic property and result
order, and one final newline. It contains no generation timestamp, user profile, machine name, or
unconfined absolute path.

## Command And Consumer Rules

- Python and PowerShell conformance commands must provide equivalent concise/report switches,
  validation, fields, exit behavior, and path safety.
- The canonical compatibility orchestrator uses the same concise contract but remains intentionally
  Python-only because cross-runtime comparison is its responsibility.
- CI and routine agent workflows should consume concise output after adoption.
- Semantic comparison, accepted-baseline review, and extraction rehearsal continue to consume or
  export detailed output.
- Verbosity changes never justify removing a permanent test, weakening a fixture, skipping a runtime,
  or changing a compatibility profile.
