# CI Testing Modernization Contracts

**Status:** Accepted Phase 1.3 design, confirmed by the maintainer on 2026-10-03, based on published Phase 1.2
`7d02499`. No catalog, supervisor, selector, XML adapter, or hosted pipeline is implemented by this
document. Examples are design fixtures, not current invocation recipes or measured results.

The [modernization plan](ci-testing-modernization-plan.md) owns delivery and acceptance gates.
The [coverage ledger](ci-testing-coverage-ledger.md) owns coverage mapping and migration gaps.
Existing [validation reporting](../Framework/Contracts/validation-run-reporting.md),
[conformance membership](Conformance/suites.json), and
[compatibility membership](Compatibility/compatibility.json) remain authoritative and unchanged.
This contract specifies an additional repository-owned orchestration boundary.

## 1. Ownership And Authoritative Locations

| Location | Authority |
| --- | --- |
| `Tools/ci-testing-modernization-plan.md` | Phase scope, review gates and closure pointers. |
| `Tools/ci-testing-coverage-ledger.md` | Stable family/scenario ownership, consumer edges, coverage gaps and retirement evidence pointers. |
| This document, Decision Record section | Accepted design rationale, affected contracts, review outcome and superseding decisions. |
| `Tools/CI/Data/policy-validators.json` | Proposed schema 1: repository-owned policy validator registration. |
| `Tools/CI/Data/implementation-tests.json` | Proposed schema 1: pytest/Pester implementation groups. |
| `Tools/CI/Data/execution-profiles.json` | Proposed schema 1: ordered layer references, obligations and execution policy. |
| `Tools/CI/Data/coverage-metadata.json` | Proposed schema 1: impact/dependency/deadline/adapter metadata for externally owned units and shared infrastructure. |
| `Tools/Conformance/suites.json` | Existing schema 1: paired semantic suite paths, order, profiles and discovery. |
| `Tools/Compatibility/compatibility.json` | Existing schema 2: project check kinds, runtime inventory, order and profiles. |
| `.tmp/ci/<run-id>/` | Proposed ignored local execution evidence, generated and owned by one run. |
| `Framework/platform_evolution.md` | Confirmed platform/CI integration milestones and exact implementation/evidence pointers when adopted. |
| `Framework/testing_methodology.md`, `Tools/TOOLING_REFERENCE.md` | Cumulative obligations and actual implemented APIs/recipes; updated when behavior is adopted. |

The decision record stays in this document rather than creating another design authority. Each
subphase records its baseline, actual checks, result and next checkpoint in the plan; detailed
execution evidence lives in the run directory or hosted artifacts, with stable links from the plan
and ledger. A generated report is never a semantic baseline or authored-content source of truth.
Do not create framework version history claiming an implementation from this documentation pass.

One Python supervisor owns planning, selection and aggregate results. PowerShell domain behavior,
Pester execution and paired conformance remain independently implemented. A convenience PowerShell
launcher may forward typed arguments; it must not introduce another selector or result model.
Execution is sequential initially. Hosted YAML supplies runtime/setup, event provenance and
publication; it does not register tests, reinterpret policies or select membership by path filters.

## 2. Catalog Shapes And Membership

All new catalog roots require `schema_version: 1`. Their root keys are:

| Catalog | Required root keys |
| --- | --- |
| Policy | `schema_version`, `validators`, `discovery` |
| Implementation | `schema_version`, `groups`, `discovery` |
| Profiles | `schema_version`, `runtime_order`, `profiles` |
| Coverage metadata | `schema_version`, `external_units`, `comparisons`, `dependencies`, `full_selection_paths`, `non_impact_paths` |

Unknown keys, unsupported versions, duplicate JSON object keys, missing required fields, wrong
types (including booleans accepted as integers), empty required arrays and duplicate identities
are invalid. Required values cannot be silently defaulted from host YAML. New fields need a reviewed
contract revision and validator regression; incompatible changes increment schema/contract versions.
Catalogs are UTF-8 JSON with deterministic formatting. IDs match `[a-z0-9]+(?:-[a-z0-9]+)*`.

Policy/group records require `id`, `description`, `order`, `adapter`, `runtimes`, `os`, `entry`,
`arguments`, `fixtures`, `impact_paths`, `depends_on`, `deadline_seconds`, `result_contract`,
`empty_policy`, `allowed_skips`. `order` is a unique nonnegative integer within its catalog.
`deadline_seconds` is a positive integer defining the entire unit lifetime. Phase 1.4 supplies
measured values before executable adoption; unresolved budgets make a catalog non-executable.

`entry` is a nonempty explicit ordered file list: one script for an owned validator, explicit test
files for pytest/Pester groups. Files cannot belong to multiple native groups. `arguments` is a
string array passed as process arguments, never an evaluated shell string. Runtime, executable,
root/scope/output arguments are adapter-owned typed inputs, not arbitrary string interpolation.
Catalog paths and arguments cannot inject another runtime, change the output owner or weaken a
required profile. Adapter names are a fixed supported enum, not arbitrary import/function names.

Proposed adapters: `ruff`, `powershell-format`, `work-annotations`, `actionlint`, `change-policy`,
`pytest`, `pester`, `conformance`, `compatibility`, `parity`. Each has a separately tested argument,
result and artifact contract. External adapters refer to existing IDs/entry points. Policy
registration approves actual validator code; a filename discovered on disk is not that approval.

`fixtures` lists current repository-relative files/directories consumed by the unit. `impact_paths`
lists repository-relative glob patterns. `depends_on` lists exact unit identities needed for
execution success, not impact edges. Impact propagation belongs in metadata `dependencies`.
An empty impact list means impact is unbounded, causing full selection; it never means no impact.
`empty_policy` is `fail` except for an explicitly reviewed policy validator that records
`allow-no-applicable-files`; native test collection cannot opt out of empty-collection failure.
`allowed_skips` is an explicit list of stable native identities, reason and decision reference;
it defaults to an explicit empty list, not an unrestricted skip allowance.

Runtime/OS arrays must be nonempty, unique and compatible with the adapter: pytest uses Python;
Pester uses the declared PowerShell variants; 5.1 requires Windows. OS IDs are `windows`, `linux`,
`macos`. `result_contract` is a supported adapter contract ID, not a free-form version claim.
An allowed-skip record requires `identity`, `reason`, `decision`, `review_checkpoint`; an unknown,
stale or mismatched identity fails validation. Acceptance is reviewed at the nominated checkpoint,
not silently extended by a green run.

Discovery records require `directory`, `pattern`, `exclude`. Each exclusion has an exact path,
reason and decision reference, and must still match discovery. Planned native locations are
`Tools/Tests/Python/` (`test_*.py`) and `Tools/Tests/PowerShell/` (`*.Tests.ps1`), organized by owning
component. Helpers/data use separate paths. They do not enter existing conformance discovery.
Discovery rejects unregistered files, stale exclusions, multiply owned files and registered missing
files. pytest/Pester collection must be limited to approved files; discovery does not auto-enroll.

### External Metadata And Profile References

Logical unit IDs are `policy/<id>`, `implementation/<id>`, `conformance/<suite-id>`,
`compatibility/<check-id>`, and `parity/<id>`. An expanded execution ID appends `::<runtime>`.
Compatibility and parity use `::referee`: one Python orchestrator/comparison with recorded
participating runtime IDs, not three fictitious implementations. Native runtime IDs are `python`, `powershell7`,
`powershell51`; profile `runtime_order` is explicit and unique. OS restrictions cannot remove a
required runtime from a gating profile: an unavailable Windows 5.1 obligation is blocked/failing,
or must be assigned to another declared shard.

External metadata records require `unit`, `fixtures`, `impact_paths`, `deadline_seconds`,
`depends_on`, `result_contract`. Membership and entry paths still come from the owning registries.
Missing impact mapping falls back to full; missing execution/deadline/adapter metadata is a planning
error. Existing compatibility timeouts remain inner call limits; outer deadlines add supervision.

Metadata `comparisons` explicitly registers parity units; it requires the same external metadata
fields plus `id`, `description`, `order`, `source_reference`, `runtimes`, `normalization`.
Its `unit` must equal `parity/<id>` and comparison order values must be unique.
`source_reference` names one owning registry/profile or exact ID set with the same exclusive rule
as profile references. The fixed parity adapter consumes complete source results for each declared
runtime; missing/failed sources block comparison, while source execution failures already fail
the gate. It does not rerun domain semantics or replace them with Python. `normalization` names
an approved tested rule set. Metadata owns comparison membership; YAML cannot create a comparison.

Impact dependency records require `source`, `consumers`, `reason`; source is an exact unit identity
or registered shared path rule, consumers are exact logical unit IDs. Full-selection path records
require `pattern`, `reason`. Non-impact path records require `pattern`, `reason`, `decision`.
Unknown edges, cycles and conflicting non-impact/impact declarations fail catalog validation.

Profile records require `id`, `description`, `references`, `always_run`, `selection`,
`execution_policy`, `budget`, `required_reviews`. References require `owner`, `profile`, `ids`,
`runtimes`, `blocking`; exactly one of `profile` or `ids` is non-null. Owner-profile expansion reads
its source registry, preserving that order. Exact IDs are an explicit diagnostic or supplemental
obligation, not a copied replacement for the source profile. Duplicate expanded references are
invalid rather than quietly deduplicated. Dependencies must exist, be acyclic and lie in the
profile closure. `always_run` names expanded obligations within that closure, including mandatory
catalog/supervisor/selector regressions. It cannot reference a missing unit.

Selection is `full` or `affected`; initial PR/main/release gates remain full. Profiles describe
capabilities, not GitHub/ADO events; Phase 1.5 binds events. A PR profile can reference compatibility
`pull-request` plus the separate distribution-boundary check without changing legacy membership.
Render/expensive obligations require an explicit profile reference. Full fallback expands the
requested profile only. It cannot silently add full-release or remove lifecycle closure obligations.

Execution policy requires `continue_independent: true`, `parallelism: 1`, canonical guard policy and
owned environment policy. Budget requires total, termination, cleanup and finalization seconds;
the reserved budgets must leave a positive launch window. Phase 1.4 chooses actual numbers.
`required_reviews` lists retained methodology families and acceptance evidence references. Automated
results show pending human review; only explicit reviewed evidence can satisfy those obligations.

Only conformance/compatibility references accept an owning `profile`, since those registries define
profiles. Policy, implementation and parity references use explicit approved IDs; execution-profiles
is their membership authority. `blocking` is a boolean attached to the reference; it cannot weaken
an already required owner/methodology obligation. Profile `budget` keys are `total_seconds`,
`termination_seconds`, `cleanup_seconds`, `finalization_seconds`. Execution policy keys are
`continue_independent`, `parallelism`, `canonical_guard`, `environment`; the latter two name
supported policy IDs. Required-review records use `family`, `blocking`, `evidence` (null if pending).

Deterministic order is profile reference order, owning registry/catalog order, then declared runtime
order. Stable topological sorting moves prerequisites before consumers, using that expanded order
as its tie-break. The recorded plan order is immutable; completion timing cannot reorder results.
Execution dependencies use logical IDs and require all declared variants of their prerequisite.
Parity source references also imply those prerequisites. Select the entire comparison runtime set
when any source is affected; a partial runtime sample cannot prove full parity.

### Illustrative External Metadata Record

The numeric deadline below is an example for schema review, not an adopted timeout.

```json
{
  "unit": "conformance/strict-ingestion",
  "fixtures": ["Framework/Data/Strict-Yaml"],
  "impact_paths": ["Framework/Data/Strict-Yaml/**"],
  "deadline_seconds": 120,
  "depends_on": [],
  "result_contract": "legacy-conformance-detailed-v1"
}
```

Changes to shared ingestion/runtime code additionally propagate through metadata dependencies/full
selection paths. This single illustrative fixture edge is not sufficient for narrow selection.

## 3. Scope, Snapshot And Conservative Selection

Policy scope and test impact are separate outputs of one scope resolver. Every actual changed
path gets a policy disposition: validated, deleted-integrity-checked, reviewed-not-applicable or
blocked. Applicable composed validation uses required context, not just changed-file syntax.
No test selection decision exempts a changed file from its repository policy obligation.

| Explicit scope mode | Comparison and executed content |
| --- | --- |
| `committed` | Required base/source refs resolved to object IDs; complete merge-base-to-source diff. Execute immutable source snapshot; dirty local state is rejected. |
| `local-staged` | HEAD versus index; execute an isolated index snapshot. Working-tree edits do not enter execution. |
| `local-worktree` | HEAD versus combined staged/unstaged tracked changes plus nonignored untracked files; execute a captured worktree snapshot, including deletions. |
| `hosted-pr` | Target/source tips and merge base identify source changes; record separately the actual checkout/merge commit executed. |
| `hosted-commit` | Explicit comparison base and executed source commit. No invented parent/base when history is missing. |
| `full` | No affected filtering; execute captured commit/worktree and validate the complete eligible policy surface. Record absence of a comparison explicitly. |

Scope mode is required; do not silently combine staged, unstaged and committed changes. Snapshot
capture failure or detected drift blocks execution. A full fallback may repair missing comparison
evidence only when the executed snapshot itself is known and coherent; validate the full eligible
policy surface and record lost deletion/history precision. It cannot repair missing/unreadable
checkout, invalid catalogs, unsafe paths or an unidentified executed commit.

Git reads use argument arrays and NUL-delimited status/path output with rename/copy detection.
Preserve additions, modifications, deletions, both rename paths, and copy source/destination.
Resolve the merge base against actual target/source refs, not a shallow single-commit change list.
Record base tip, source tip, merge base, executed commit and checkout kind (`source`, `merge`,
`local-snapshot`). A merge checkout's source-impact list is not described as a merge-tree diff.
If target changes or merge execution cannot be bounded by complete metadata, select full.
Missing history triggers bounded fetch by the host adapter or recorded full fallback, never empty
success. Unsupported Git statuses similarly trigger full selection if the snapshot remains safe.

Paths are repository-relative forward-slash strings without absolute/drive/UNC prefixes, `..`, NUL
or root destinations. Decode Git paths without whitespace splitting; preserve case, spaces,
Unicode and exact identity. Do not apply lookup-key semantic normalization to file paths. Match
case-sensitively by repository spelling; ambiguous case collisions on Windows block snapshot use.
On-disk resolution must remain under the owned root after symlink/reparse checks. Reject escaping
links in catalogs, snapshots and output targets. Gitlink/submodule impact is unbounded until an
explicit supported policy exists. Unrepresentable path data cannot become a no-impact decision.

Glob grammar is literal segments, `*` and `?` within one segment, and whole-segment `**` matching
zero or more segments. No shell expansion, bracket syntax, negation or regex. Literal registered
files must exist; impact patterns may describe deleted/renamed paths, so a nonmatching pattern is
not automatically a stale exclusion. Dependency edges must cover the actual current implemented
data/module/consumer paths; future storage plans do not justify them.

Selection precedence:

1. Validate catalogs/profile, runtime obligations and coherent snapshot; errors fail planning.
2. Expand requested profile, prerequisites and always-run meta-regressions.
3. Full mode, a shared-infrastructure match, unknown impact, incomplete mapping, unsupported change
   status or indeterminate comparison selects the complete profile with explicit fallback reasons.
4. Otherwise match both old/new paths, propagate transitive impact to fixed point, add execution
   prerequisites and always-run obligations, then retain plan order.
5. A path is non-impact only through an exact reviewed metadata rule with reason and decision
   reference, no impact/dependency conflict, and independent policy disposition. No blanket docs
   rule: schemas, contracts, fixtures and policy documents may affect behavior.

The explain-only selection plan records the full candidate universe, selected/unselected IDs,
every changed path and its disposition/reasons, dependency expansion, fallback and provenance.
Explain-only never launches tests, installs dependencies or writes canonical outputs. It may write
an explicitly requested owned plan artifact. `no-impact` requires zero selected execution units,
complete approved path dispositions, no required reviews and no always-run obligations; otherwise
zero selection is an error. Routine gating profiles with mandatory meta-regressions cannot take
that shortcut. Explicit diagnostic subsets remain labeled diagnostic and cannot satisfy full gates.

## 4. Execution States, Safety And Exit Behavior

Each selected expanded ID has exactly one result row, including units never launched. Unselected
units live in selection metadata; they are not native skips or attempted tests. A unit progresses
`planned` to `running` to one terminal state; blocked/skipped may terminate before launching.
Before catalog expansion fails, plan/results may be empty but a run-level error is required.

| Terminal unit state | Meaning |
| --- | --- |
| `passed` | Successful process, valid complete expected result and satisfied case/coverage obligations. |
| `failed` | Completed assertion, semantic comparison or repository policy failure. |
| `error` | Launch/preflight/discovery/collection/adapter/parse/result/report contract failure. |
| `timed-out` | Unit deadline exceeded; owned child tree termination attempted and recorded. |
| `cancelled` | Active child interrupted, or planned unit not launched after cancellation. |
| `blocked` | Missing prerequisite/runtime, unsafe shared state, canonical mutation or exhausted run launch budget prevents attempt. |
| `skipped` | Explicit approved optional unit exclusion with reason/decision; never a substitute for a missing required runtime. |

Within native groups, expected skips must match registered identities/reasons. Unexpected skips,
all-skipped required collection, strict XPASS, unauthorized xfail or zero collection produce an
error or coverage failure even when the native exit code is zero. Approved exclusions remain
visible and cannot be described as tested coverage. Native counts and supervisor-unit counts are
separate. Collection/internal/usage errors are not assertion failures.

Preflight verifies exact dependency versions/paths and required runtime/OS. Bootstrap is a separate
explicit action; execution does not install or silently substitute. A missing runtime blocks its
units while independent available units continue. Failure of an execution prerequisite blocks its
dependents; failure of an impact-related unit does not automatically block consumers.
Policy assertion failures still permit independent evidence. Failed catalog/snapshot validation
cannot safely authorize launching anything.

Every child has an owned cwd, temporary destination, explicit environment allowlist/overrides,
stdout/stderr capture and process-tree ownership. Total unit deadlines include descendants,
startup, parsing and artifact verification; existing inner timeouts remain in force. Stop only
owned children using tested Windows Job Objects/POSIX process groups. Unproven child containment
is a preflight error for units needing it. The run budget stops new launches early enough to reserve
termination, cleanup and finalization. Later budget-blocked units remain visible and fail a gate.

Canonical guard checks include inventoried authored pages, templates, Relationship Seeds,
configuration and configured canonical outputs. Resolve the existing paths before launch; do not
design a future layout. Record changed/additional/deleted paths and hashes before/after protected
operations. Ignore only explicitly owned generated destinations. Guard setup/read failure blocks
mutating units. Canonical mutation stops further generation/consumers sharing that state; independent
read-only evidence can continue only with proven isolation. Never automatically restore user content.

Failure classification is an enum: `assertion`, `policy`, `parity`, `catalog`, `scope`,
`prerequisite`, `launch`, `collection`, `result-contract`, `timeout`, `cancellation`, `budget`,
`canonical-mutation`, `cleanup`, `report`, `publication`. Preserve original child exit/message
and full diagnostics, while reporting the supervisor classification separately.

| Aggregate exit | Required behavior |
| --- | --- |
| `0` | All blocking selected obligations passed (or explicitly permitted exclusions), reports/cleanup/guards succeeded, required review evidence is present. Also valid explain-only/no-impact outcomes under their distinct states. |
| `1` | Completed run has blocking test/policy/coverage/prerequisite/canonical/cleanup/report failures or budget-blocked units. |
| `2` | Invocation, catalog, profile, scope/snapshot or planning failure prevents valid execution. |
| `130` | Cancellation requested; preserve independent earlier failures and partial evidence. |

Run status is `passed`, `passed-with-findings`, `failed`, `cancelled`, `planned`, or `no-impact`.
`passed-with-findings` may exit 0 only for explicitly observational shadow references; report their
failures prominently and mark equivalence/readiness unsatisfied. A required observation gate must
evaluate that evidence before adoption. Blocking policy cannot be changed at invocation time or
in YAML to hide failures. Cancellation takes exit precedence over an already recorded assertion
failure; planning error takes precedence before execution; all causes remain in diagnostics.

Unit rows do not change a child's actual outcome because a later run-level report/cleanup fails.
Those are run-level failures that force nonzero aggregate exit. A successful publication cannot
overwrite saved supervisor failure. Hosted publication failure also makes the hosted outcome fail,
even if local execution passed; keep both statuses and artifact digests in publication evidence.

## 5. Supervisor JSON And Evidence Contract

New top-level contract: `ci-execution-report`, `contract_version: 1`. It does not replace or add
fields to legacy detailed JSON or `validation-run-summary` v1. Mandatory top-level fields in order:
`contract`, `contract_version`, `run_id`, `mode`, `profile`, `status`, `exit_code`, `complete`,
`provenance`, `selection`, `runtime_inventory`, `budget`, `counts`, `results`, `reviews`,
`failures`, `canonical_guard`, `cleanup`, `artifacts`. Use null only for explicitly inapplicable or
not-established data; no omitted required fields. Unknown versions/keys/duplicate IDs are invalid.
`mode` is `execute` or `explain`; `run_id` is an opaque unique safe directory identifier, excluded
from semantic equality and test identity. Timings are finite nonnegative seconds; exit codes are
integers. Results cannot contain a running/planned state in a finalized execution report.

| Record | Required content |
| --- | --- |
| Provenance | Scope mode, base/source/merge-base/executed IDs, checkout kind, dirty/snapshot identity, catalog/profile digests, host kind and run URL when hosted. No credentials or personal machine/profile names. |
| Selection | Full ordered candidate IDs, selected IDs, unselected rows/reasons, change records/dispositions, requested mode, applied full/affected mode, fallback boolean/reasons. |
| Runtime inventory | Runtime ID, verified version, repository/owned-relative executable reference or sanitized system-tool label, dependency names/versions and preflight status. |
| Budget | Run/termination/cleanup/finalization limits, elapsed seconds, exhausted state; measurements use monotonic clocks. |
| Counts | Candidate/selected/unselected and every terminal unit-state count; separate native case counts by group, with unknown counts represented as null. |
| Results | Plan-ordered expanded ID, owner/layer/runtime/participating runtimes, blocking flag, status/classification, child exit, duration, deadline, attempts, native counts, reasons, diagnostics and artifact references. |
| Reviews | Stable family, required/observational flag, pending/accepted/failed status, decision/evidence references; no synthetic automated pass. |
| Failures | Run/unit identity, classification, bounded excerpt, truncation flag and full diagnostic artifact; preserve multiple failures and cause relationships. |
| Canonical guard | Applicable state, before/after fingerprints, unchanged true/false/null and changed paths; null cannot satisfy a required guard. |
| Cleanup | Owned destinations, removed/retained/failed state, retention reason and termination verification. |
| Artifacts | Unique relative path, media type, producer, required flag, byte length, SHA-256, complete/partial state. No artifact outside the run owner. |

`selected_count = len(selected_ids) = len(results)` once a plan is established; terminal state counts
sum to selected. Unselected rows account for the remaining candidate universe. All selected units
must be terminal at normal finalization, including blocked/cancelled. `complete` means an intact
finalized record, not all tests passed. An interrupted event journal remains partial. Explain-only
uses status `planned`, selected plan metadata and empty execution results; executed count invariants
apply only to execution mode. Native count aggregation never adds custom suite assertion estimates.

### Illustrative Terminal Result Row

This example shows a timed-out custom suite. It records one supervisor unit and no invented native
assertion count. The corresponding custom XML case appears below. Values are illustrative.

```json
{
  "id": "conformance/strict-ingestion::powershell51",
  "owner": "conformance",
  "layer": "language-neutral-conformance",
  "runtime": "powershell51",
  "participating_runtimes": ["powershell51"],
  "blocking": true,
  "status": "timed-out",
  "classification": "timeout",
  "child_exit_code": null,
  "elapsed_seconds": 120.0,
  "deadline_seconds": 120,
  "attempts": 1,
  "native_counts": null,
  "reasons": ["Full baseline profile selected"],
  "diagnostics": {
    "excerpt": "Unit deadline exceeded",
    "excerpt_truncated": false,
    "stdout": "units/conformance-strict-ingestion-powershell51/stdout.txt",
    "stderr": "units/conformance-strict-ingestion-powershell51/stderr.txt",
    "termination": "owned-tree-terminated"
  },
  "artifacts": ["diagnostics/strict-ingestion.txt"]
}
```

Artifact references are relative to the run directory and must resolve in its artifact manifest.
Unknown child exit after termination stays null; it cannot be replaced by a fabricated assertion
exit. A prerequisite-blocked unit has zero attempts, null child exit and native counts, zero unit
execution duration, and its exact failed prerequisite IDs in reasons. A native result uses
`native_counts` fields `collected`, `passed`, `failed`, `errors`, `skipped`, `xfail`, `xpass`,
`unreported`; values are nonnegative integers or null when unknowable. Counts must be reconciled
against the native format's actual semantics, not forced into a guessed case inventory.

Execution adapters verify exit code AND detailed results AND required artifact availability. Zero
exit plus malformed/missing JSON/XML, mismatched selected inventory, unexpected duplicate results or
wrong counts is `result-contract` error. Capture stdout/stderr independently so either stream can
explain a failure. Human excerpts retain the existing 20-line/4096-byte UTF-8 budget; full output
is retained within measured artifact limits. If capture limits are reached, preserve truncation
metadata and emit an evidence-limit failure rather than claiming complete diagnostics.

Incremental `events.jsonl` records plan/run/unit transitions with sequence numbers; it can recover
partial evidence after supervisor failure without inventing final status. Write each completed
unit record atomically, then generate projections from those same records. Final JSON, Markdown,
XML and manifest use UTF-8 without BOM, LF/final newline and atomic replacement within the run.
Finalization failure exits nonzero and leaves the journal/available records; failure to write any
artifact must still produce stderr and nonzero exit. A hard OS/host kill may prevent finalization
or publication; report that boundary honestly on recovery.

Default success output is concise status/counts/duration and evidence location. Failures add bounded
diagnostics and links. Successful run evidence remains until explicit retention cleanup governed by
Phase 1.4; do not delete reports before host upload. Automatic fixtures/process scratch are cleaned,
while failure evidence is retained. User-requested diagnostic destinations remain owned by the user.
The supervisor default stays under `.tmp/ci/`; an alternate ignored run parent must be explicitly
registered and root-confined. Reject existing foreign run directories, canonical targets, root/
outside paths, link escapes, stale XML from another run and deleting parent/sibling directories.

Legacy runners remain callable directly with current detailed/concise/report behavior. Supervisor
adapters save their complete legacy reports as separate artifacts and interpret without rewriting
them. Extraction continues copying its current portable subset and consuming full detailed reports.
Any dependency/test layout changes must prove isolated extraction before adoption. Parity validates
full selected inventory, runtime completeness, typed semantic decisions/errors and allowed
serialization rules; only declared timing/run-path/generated timestamp fields may be normalized.
Never normalize away IDs, visibility, semantic ordering, file hashes or failures.

## 6. Markdown, XML And Hosted Publication

Markdown is the common front door locally and on both hosts: overall result and execution commit,
profile/scope/fallback, selected/unselected/blocked coverage, durations, retained review, safety and
cleanup, all failures with bounded excerpts, and complete artifact/Test-tab links. Counts distinguish
units from native cases. Escape Markdown/XML-sensitive diagnostics; do not truncate the failure
inventory just because excerpts are bounded. Report links are platform projections of local
relative artifacts. YAML cannot supply a different Markdown interpretation.

pytest produces native JUnit XML; Pester 6.2.0 supports `JUnitXml`, `NUnitXml`/`NUnit2.5` and `NUnit3`
in the inspected installed implementation. Prefer JUnit for both pilots; Phase 2.4 must verify actual
pass/fail/skip/collection/cancellation output on both PowerShell hosts before accepting its adapter.
Native case identity includes logical group, runtime and stable test/node/data identity. Parameter
names must be deterministic, with no temporary paths or run IDs. Deliberate renames need a decision
because hosted history may treat them as different tests. Preserve native XML and mapping evidence.

Custom XML exposes one case per conformance suite/runtime or compatibility check/referee. Parity
units expose one comparison case. Do not manufacture assertion-level cases. For adapters wrapping
legacy profiles, attribute each complete returned ID once; retain missing/unattempted results as
errors/blocked, not success. No synthetic PowerShell implementation of the Python referee is shown.

| Supervisor outcome | Custom JUnit representation |
| --- | --- |
| passed | One successful case. |
| failed | `failure`, with classification/message and full diagnostic reference. |
| error / timed-out | `error`, preserving result/launch/timeout classification. |
| blocked / cancelled | `skipped` with explicit reason; blocking run failure remains in supervisor outcome. |
| approved skipped | `skipped` with decision/reason. |
| unselected | No testcase; selection/Markdown reports omission. |
| run-level planning/report/cleanup error | Separate clearly labeled `ci-infrastructure` error case when XML can still be emitted. |

Native XML is not duplicated by a custom successful group case: supervisor reports units while the
Tests tab shows actual native cases. Add a clearly labeled infrastructure case only for missing/
invalid native reports or uncovered group-level errors. If partial native results survive a timeout,
publish them with the separate timeout error; never infer unreported native passes. XML counts,
duration and state must agree with recorded source data at their respective granularity.

Runtime identity must survive JUnit `classname`/`name` (or corresponding NUnit fields) and test run
titles, so Python/7/5.1 results cannot overwrite one another. Conformance example:

```xml
<testsuite name="conformance.powershell51" tests="1" failures="0" errors="1" skipped="0">
  <testcase classname="conformance.powershell51" name="strict-ingestion" time="120.000">
    <error type="timeout" message="Unit deadline exceeded">See diagnostics/strict-ingestion.txt</error>
  </testcase>
</testsuite>
```

This is an illustrative projection, not a measured timeout. Native files publish once; custom XML
publishes separately. An expected-file manifest identifies exact run-owned XML paths/format/counts;
avoid repository-wide globs that can upload stale files. Validate the manifest and XML before
publication; zero matches are allowed only when the recorded plan legitimately expected none.

ADO's `PublishTestResults@2` supports JUnit/NUnit and presents results in the run's Tests tab. Its
missing-file/publication-failure flags are opt-in, so use explicit failure checks and prevalidate
every expected file rather than relying on finding at least one. Publish after ordinary failures,
preserve aggregate exit, and publish Markdown/detailed artifacts separately. Pipeline automated
results do not require converting every runner or managing manual Test Plans.
[Microsoft task reference](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines).

pytest documents native `--junitxml` output; choose the supported XML configuration in the pilot,
without plugins merely to produce JUnit. GitHub needs its own publication/summary adapter over the
same files and statuses; ADO-specific task behavior is not a local testing rule.
[pytest output reference](https://docs.pytest.org/en/stable/how-to/output.html#creating-junitxml-format-files).

## 7. Review Examples And Mandatory Meta-Regression

| Scenario | Planned contract outcome and regression obligation |
| --- | --- |
| Unknown changed path under a coherent checkout | Full requested profile, reason `unknown-impact`, complete eligible policy scan if precise scope unavailable; never an empty green run. |
| Duplicate group ID or unregistered native test | Planning exit 2; no child starts; catalog failure in JSON/Markdown/infrastructure XML where writable. |
| Missing PowerShell 5.1 | Its required units blocked; Python/7 independent work continues; aggregate exit 1. |
| Unit returns exit 0 with missing/malformed summary | Unit error `result-contract`; later independent units still run. |
| One assertion fails and a later unit times out | Both failures recorded in plan order, full streams retained; descendants terminated; remaining independent coverage attempted within budget. |
| Cancellation after one pass | Pass retained, active/planned units cancelled, partial native results retained; aggregate exit 130. |
| Invalid output target or unsafe link | Planning/path failure before generation or cleanup; no canonical or foreign files deleted. |
| Canonical page changes during generation | Mutation failure with path/hash evidence; dependent consumers blocked; no automatic restoration. |
| pytest collects zero tests / native framework skips required cases | Coverage error even if native exit otherwise appears successful; no unit pass. |
| Supervisor cannot write final Markdown | Test outcomes preserved; report failure forces nonzero exit; retain journal/other artifacts. |
| ADO upload fails after local success | Local record stays passed, publication record fails, hosted gate fails; no retroactive fabricated assertion. |
| Retained Primer review is pending | No fake Primer testcase; required review unresolved and readiness fails until accepted evidence exists. |

Mandatory runner/selector regression uses synthetic child processes, private registries and owned
fixtures. Cover all examples, deterministic ordering, duplicate keys, source/merge/staged/worktree
scope, rename/deletion/Unicode paths, full fallback, no-impact proof, cycles, overlapping membership,
lost streams, mismatched counts, expected skips, process-tree escape prevention, deadline headroom,
cleanup/report/publication failure and partial recovery. It must run in required local/hosted
profiles, including affected selection; never recursively launch the production full suite.

## 8. Decision Record And Remaining Gates

The maintainer accepted decisions D01-D08 together on 2026-10-03, closing the Phase 1.3 design
checkpoint. Acceptance does not implement catalog files or activate hosted policies. Revisions
must record their rationale, affected contract and maintainer review before superseding a decision.

| ID | Accepted decision and reason | Affected checkpoints |
| --- | --- | --- |
| D01 | Python supervisor; four new metadata/catalog files; existing membership stays authoritative. Avoid competing selectors and duplicate inventories. | 3.1, 3.4. |
| D02 | Explicit snapshot/scope modes; unknown impact falls back, invalid planning fails. Preserve actual-change validation independently. | 3.2, 3.6, 6.1. |
| D03 | Sequential isolated children, total unit/run deadlines, continuation and explicit blocked/cancelled outcomes. Preserve later independent evidence. | 1.4, 3.3-3.6. |
| D04 | New supervisor report v1; preserve legacy detailed/concise contracts and extraction consumer. Avoid hidden breaking changes. | 2.4, 3.5, 4.4. |
| D05 | Native pytest/Pester case results, honest custom suite/check XML, Markdown on both hosts. Keep counts and identity truthful. | 2.4, 3.5, 5.4. |
| D06 | Required review evidence distinct from automated passes; native expected skips explicitly registered. Keep unsupported/retained coverage visible. | 1.5, 4.5, 7.1. |
| D07 | Existing ledger and this decision section are durable; ignored run evidence plus confirmed evolution pointers. Avoid duplicate design stores. | Every closure, 7.2. |
| D08 | Run-owned reports, broader canonical guard and fail-closed artifact/publication verification. Prevent false green or foreign cleanup. | 2.2, 3.5, 4.3, 5.4. |

Still deliberately pending: measured budgets, exact dependency/bootstrap baselines and image support
scope (1.4); event/check-name/shard mappings, schedule host ownership and observational shadow
profiles (1.5); verified native report cases (2.4); implemented process/scope/report invariants
(3.6); three-runtime equivalence and retained reviews (4.2-4.5); hosted passing/failing publication
demonstrations and branch-policy adoption (5.4-5.5). Neither this accepted design nor a successful documentation
check satisfies those execution gates. The rollback for this pass is documentation only.
