# CI Catalogs And Read-Only Planning

CI 4.1 is confirmed on 2026-10-05. `catalog.py` validates registration and produces
plans; `plan_ci.py` exposes listing/planning only. Neither executes a suite, probes a host, installs
dependencies, selects affected tests or publishes results. Existing workflows/checks remain active.

Inventory/timing tables below record the confirmed 4.1 checkpoint. CI 4.2 subsequently registers
ci-scope as a fourteenth implementation group and always-run obligation; its current 52-unit
inventory, additional allowance and explain-only behavior are documented in [Git scope](change-scope.md).

```powershell
# Use the prepared development Python executable recorded by bootstrap.
& $python Tools/CI/plan_ci.py --list
& $python Tools/CI/plan_ci.py --profile pr-integration
& $python Tools/CI/plan_ci.py --profile pr-integration --shard-plan pr-integration-initial
& $python Tools/CI/plan_ci.py --profile pr-integration --os linux --available-runtime python
```

Default root is the checkout containing the command, independent of cwd. `--root` names an explicit
source tree; an alternate `--catalog-directory` must remain beneath it (relative paths use that root).
The last command retains all required units and marks missing PS7/Windows obligations blocked.
`--available-runtime` is an explicit planning assumption, not verified readiness or a runtime substitute.
Absent assumptions produce `unverified` availability. Valid inspection exits 0 with `planned` status,
even with blocked coverage; invalid registration/invocation exits 2 with catalog diagnostics. A valid
plan is not a passing execution. Every current plan has `execution_ready: false` and rollout blockers.

## Registration And Source Ownership

Four UTF8 JSON schema-1 catalogs live in `Data/`:

| Catalog | Current authority |
| --- | --- |
| policy-validators.json | Four validators: Ruff, PS formatting, annotation policy and pinned actionlint. Script/configuration entry points are explicit; actionlint's input is the adopted version declaration and workflow fixture directory. |
| implementation-tests.json | Thirteen groups: six pytest files, six Pester files and the explicit installed-artifact verification route. One owner per entry; deliberate failure fixtures are excluded with CI 3.4 provenance. |
| coverage-metadata.json | Execution/impact/fixture metadata for all 21 existing conformance suites and 11 compatibility checks; two planned fast/baseline parity comparisons. It does not own existing suite/check membership. |
| execution-profiles.json | Eight accepted profiles, ordered references, budgets, always-run catalog regression, retained reviews, initial shard placements and result gates. |

Existing owners' strict Python registry loaders supply current conformance/compatibility membership,
paths, ordering, discovery and profile expansion. Duplicate JSON keys are additionally rejected before
those loaders run. No conformance/compatibility profile member list is copied into the new profiles.
Shard/gate expanded IDs are explicit placement projections checked against live owner expansion;
a changed source profile invalidates stale placement. External metadata must cover every registered
unit; unknown, duplicate or missing execution metadata fails. Impact paths conservatively cover current
runtime/configuration/content/consumer directories; unbounded impact is explicit, not no-impact proof.

The installed-artifact adapter is a reviewed implementation clarification of the accepted CI 3.1 route,
with result ID `installed-package-v1`. It points to verify_installed_package.py; planning never installs
a wheel or invents pytest collection for that route. Ruff/actionlint entries are declared configuration
inputs to fixed adapters, rather than shell commands. Adapter argument/result execution belongs to 4.4.

Records have closed shapes and exact types, including integer/boolean distinctions. Unknown IDs,
adapters, result contracts, runtimes/OS, path escapes, missing inputs, multiply owned resolved files,
unregistered discovery, stale exclusions, duplicate order and dependency cycles are hard errors.
Native files must resolve inside their declared native roots. Catalog arguments and allowed skips
remain explicit empty lists; no invocation override, empty-collection exemption, non-impact exemption
or affected selection has been adopted. Those future capabilities need their owning proof/review.

Order is reference order, owning catalog/registry order and runtime order, then stable prerequisite
sorting. Dependencies require all declared variants in the profile closure; comparisons require
complete Python/PS7 sources. Grouping never auto-registers discovered files. Current gating profiles
must include all approved native groups and four policies; broad integration profiles additionally
retain all baseline semantics and parity. CI catalog regression is always-run for native profiles.

## Profiles And Initial Admission

| Profile | Expanded units | Initial shards | Sum of unit deadline allowances, seconds |
| --- | ---: | ---: | ---: |
| workflow-policy | 1 | 1 | 120 |
| annotation-policy | 1 | 1 | 120 |
| feature-feedback | 38 | 4 | 4560 |
| pr-integration | 70 | 7 | 9000 |
| full-verification | 71 | 7 | 9120 |
| release-readiness | 71 | 7 | 9120 |
| implementation-pilot | 40 | 5 | 5130 |
| modernization-shadow | 71 | 7 | 9120 |

These sums are conservative worst-case admission allowances, **not expected run durations** or new
hosted jobs. Each initial native/policy/conformance/parity unit reserves 120 seconds; compatibility
uses the confirmed two-runtime 2.5 allocations (120/330/240/390 seconds as applicable). Baseline
aggregate times are not relabeled as individual-suite measurements. Per-unit deadline sum must fit
the profile launch window after 30s termination, 60s cleanup and 120s finalization reserves.

Each shard has the same reserve keys, at most 2190 seconds of unit allocation, and must fit 3300
seconds with the separate provisional 600s setup, 180s publication and 120s host margin. The native/
policy shard reserves 2040 execution seconds; each conformance runtime is split into 18/3-suite
chunks, compatibility gets its own shard, and parity waits for the source conformance shards.
Phase 5.1/6.5 must remeasure/review grouping and setup duplication before activating placement.
The catalog does not turn seven initial shards into a claim that seven hosted jobs are optimal.

Validate exact disjoint unit union, OS compatibility, shard cycles, cross-shard prerequisite edges,
in-shard prerequisite order and canonical result ordering. Gates project existing unit results once
without re-executing them; their source-shard sets must exactly match projected producers. Aggregate
gate covers the complete closure; duplicate check names, partial aggregate coverage and insufficient
gate budgets fail. Existing check labels are retained (Workflow Policy, Work Annotation Policy,
Python Validation, PowerShell 7 Validation, Project Compatibility where applicable). `CI Aggregate
(<profile>)` is an additional planned label only; hosted required-check adoption remains 6.5/8.4.

Full/release profiles visibly retain later process, policy, report, synthetic media and complete
parity acceptance blockers. No placeholder nonexistent test file is treated as approved coverage.
Release readiness also lists all 34 current retained PRESSURE/SCENARIO families from the methodology
with null evidence; an empty or incomplete review list is rejected. Inspection does not satisfy them.

## Source Manifests And Plan Evidence

`ci-execution-plan` v1 contains ordered expanded units, per-runtime entry points, fixture/impact paths,
dependency identities, whole-unit deadlines, result IDs, budgets, runtime/dependency prerequisites,
availability assumptions, retained reviews, selected shard plan, source digests and rollout blockers.
No timestamps/PIDs or child results are fabricated. Returned values are independent copies.
`ci-catalog-list` v1 lists approved logical units, profiles and shard plans with source digests.

`Catalog.expected_manifest(plan_id, shard_id, snapshot_digest)` creates the expected
`ci-shard-source` v1 input envelope: contract/version, plan/profile/shard IDs, ordered execution IDs,
source digests and a required 64-digit captured snapshot digest. Catalogs, owner registries, planning
code and registered entry bytes are hashed. Inputs changing after planning fail before manifest use.
`validate_manifests` rejects missing/duplicate/foreign/stale sources, wrong snapshot, wrong unit order/
inventory and mismatched digests; successful validation returns gate projections without executing.
Manifest values cannot mutate the catalog through returned references.

Snapshot capture/provenance authority is 4.2; these envelope tests use inert synthetic digest values.
Actual result/artifact manifests, their completeness/digests and gate execution belong to 4.4/4.5.
This is not signed artifact authentication, proof that children executed, or the aggregate supervisor
JSON contract. No report files are created by list/plan; controller stdout can be retained explicitly
under an owned ignored destination by the caller.

## Local Evidence And Remaining Work

Ignored `.tmp/ci-phase41/` retains Windows/WSL audit proof: repeated eight-profile plans agree,
all 51 logical units remain visible, and planning rejects process/network/non-evidence file writes.
Catalog validation/planning takes about 0.35s Windows / 0.15s WSL in these local samples.
Fifty-eight permanent pytest regressions use private source/registry trees, inert entries and exact
mutations rather than production full-suite recursion. Native aggregates pass 188 pytest cases on
Windows/WSL; WSL also passes unchanged 32 Pester cases. Existing Windows Pester evidence remains
valid because this checkpoint changes no PowerShell implementation or tests.

The expanded Windows pytest aggregate took 18.046s, above the 3.5 15s feedback goal for the earlier
130-case cohort; the final WSL sample took 5.545s. Record the increased workload and investigate private-fixture/
catalog costs at 5.1 instead of silently raising the goal or interpreting the timeout as expected
duration. The current native cohort still fits the combined 60s planning goal using earlier installed
artifact/Pester samples; those sums are estimates, not a new simultaneously measured full run.

Next is 4.2 Git scope and explain-only affected selection. No new workflow/pipeline, branch protection,
check retirement, canonical migration, dependency acquisition or test execution supervisor is adopted
here. Plans remain full and locally inspectable while later capabilities are implemented.
