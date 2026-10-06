# Mandatory Infrastructure Regression Gate (CI 4.6)

CI 4.6 is confirmed by the maintainer on 2026-10-06. The [implementation catalog](Data/implementation-tests.json)
registers tests; [execution profiles](Data/execution-profiles.json) select mandatory execution.
The focused ci-infrastructure profile tests infrastructure without recursively invoking the real
conformance/compatibility portfolio. GitHub/ADO activation remains Phase 6.

## Membership And Reproduction

| Registered group | Cases | Contract coverage |
| --- | ---: | --- |
| python-native-results | 33 | Discovery/phase/exit/XML reconciliation, empty/skipped coverage, dependency/report failures and partial streams. |
| ci-catalog | 67 | Closed registration/discovery, mandatory family/OS membership, ordering, shard union/gates/source manifests and retained check identities. |
| ci-scope | 46 | Private Git histories, snapshots, rename/deletion, drift/fallback, selection reasons and parity closure. |
| ci-process | 42 | Explicit launch/environment, owned descendants, timeout/cancellation/caller loss, cleanup and capture thresholds. |
| ci-execution | 89 | Aggregate/adapter outcomes, reports/publication/recovery and private end-to-end supervisor failures. |

CI 5.2 adds 16 representation/parity regressions to the existing ci-execution group (now 105 cases)
and ten cases to the existing Pester formatter file. Current mandatory inventory is 293 Python
cases; all Python groups total 390 and PowerShell groups total 44. The table above is the dated
CI 4.6 baseline, not a second registration authority. [CI 5.2 proof](../ci-testing-conformance-parity-proof.md)
records focused execution and complete semantic conformance separately from those inventory counts.

CI 5.3 adds 17 consumer/diagnostic/interruption regressions to the same ci-execution group (now 122).
Current mandatory inventory is 310 Python cases, all Python groups total 407 and PowerShell remains
44. The [consumer/safety proof](../ci-testing-consumer-safety-proof.md) separates final focused native
execution from the registered real consumer portfolio and its remaining release/full gates.

CI 5.4 adds 18 cases to ci-execution (now 140), five to bootstrap, three to compatibility implementation
and one to package artifacts. Current Python inventory is 434, mandatory infrastructure is 328 and
PowerShell remains 44. [Release reproduction proof](../ci-testing-release-reproduction-proof.md)
distinguishes native negative paths from actual acquired wheel/browser and copied-framework execution.

CI 5.5 adds isolated fixture/process/container coverage and four lookup-preparation regressions;
its confirmed full record has 437 pytest / 49 Pester cases, including 331 mandatory infrastructure cases.
CI 5.6 adds two catalog-admission regressions (ci-catalog 70; mandatory infrastructure 333; declared
Python inventory 439). These protect inactive historical aliases and omitted semantic reviews.
The [consolidation review](../ci-testing-pressure-consolidation.md) distinguishes focused current
CI evidence from the unchanged 5.5 domain baseline; final full/timing requalification remains 5.7.

At CI 4.6 these five groups contained 277 pytest cases. Reporting/gate tests join the existing ci-execution
group. All implementation-bearing profiles must retain all five always-run groups. Every
test_ci_*.py entry must belong to a mandatory group; these groups support Windows and Linux.
Removing a family, moving reporting coverage to an optional group or declaring one OS fails
catalog admission. Policy-only profiles stay separate policy checks.

```powershell
# Use the exact prepared development/media Python executable recorded by bootstrap.
& $python Tools/CI/run_ci.py --profile ci-infrastructure --scope local-worktree `
    --python $python --summary-json

& $python Tools/CI/plan_ci.py --profile ci-infrastructure --os linux
```

The focused profile uses [captured-source execution](aggregate-execution.md), actual composition,
source guards, isolated processes, aggregate exits and [atomic reports](execution-reporting.md).
It needs prepared Python; it does not acquire PowerShell/actionlint. PowerShell implementation tests
remain independently required by the full profiles.

Admission is 510 execution seconds plus 210 lifecycle reserve, with the existing separate 600-second
setup allowance. Its initial shard plan has one Windows placement and the catalog-only identity
CI Infrastructure Regression. Local Linux execution uses the same profile. Hosted placement/matrices
and required-check policy remain Phase 6. Existing shard allocations and check names are retained.

## Permanent Failure Coverage

| Scenario | Concrete regression owner |
| --- | --- |
| Multiple failures and continued coverage | test_ci_execution.py/test_ci_gate.py: assertion plus missing child, or malformed summary plus assertion, followed by a passing child. |
| Launch, discovery and malformed native results | test_ci_process.py/test_native_results.py/test_ci_gate.py; no native count inferred from process exit. |
| Empty/skipped or false coverage | Native phase/XML classifier and empty aggregate/publication rejection. |
| Wrong adapter metadata | test_ci_gate.py: ID, owner, deadline or blocking override fails while later independent work continues. |
| Output, timeout, cancellation and cleanup | Real owned trees in test_ci_process.py; native partial/report projections remain covered at 4.5. |
| Recording/finalization failure and recovery | test_ci_gate.py injects a unit-record failure: actual completed result survives, later work blocks, broken sequence prevents a completion marker. test_ci_reports.py retains killed-writer and corrupt/stale/foreign evidence controls. |
| Selection reasons, order and counts | test_ci_scope.py repeats explanation across dictionary insertion order; effective execution stays full. |
| Wrong/omitted/duplicate shards and artifacts | test_ci_catalog.py/test_ci_execution.py: exact partitions, source/catalog/snapshot identity and publication evidence. |
| PR/ref races | test_ci_scope.py advances source, target or checkout refs during capture in private histories; drift fails admission. Immutable SHA/merge and unbounded-parent fallback cases remain intact. |
| Existing aggregate identities | test_ci_catalog.py verifies Workflow Policy, Python Validation, PowerShell 7 Validation and Project Compatibility names. |

Public primitives are tested with private registries and synthetic children, including an end-to-end
run_ci.execute fixture. Real host event/API freshness and GitHub/ADO metadata wiring remain Phase 6;
local ref-race fixtures do not claim live hosted proof.

## Execution Corrections

Guardian capture now has a 64 MiB combined stdout/stderr monitoring threshold per process. Crossing
it stops the owned tree, records evidence-limit/cleanup, retains captured bytes and permits later
independent work. This is a monitored threshold, not a strict filesystem quota: a write/poll interval
or termination output can overshoot it. Streams are not silently truncated. Tests use small thresholds;
production uses the fixed default without catalog/CLI overrides or larger execution deadlines.

Adapters cannot change approved unit metadata; empty execution cannot pass. Finalization/publication
verify journal sequence, record identity, transition order and exact terminal-report agreement.
Recovery may ignore only a torn final journal line. Failed unit recording cannot be hidden behind
successful projections. Private Git index commands enable core.longpaths per invocation for deep
Windows owned paths without changing user/global Git configuration. Authored content and domain
conformance/compatibility fixtures remain unchanged.

## Rollout Boundary

Supported-OS/retained-runtime evidence is recorded in the [coverage ledger](../ci-testing-coverage-ledger.md)
and [plan](../ci-testing-modernization-plan.md). This checkpoint changes no workflow YAML, schedule,
branch protection or merge authority. Phase 5 owns full same-snapshot equivalence/performance;
Phase 6 owns hosted execution/publication. Rollback can stop using the supervisor/profile while
retaining original standalone runners and these regression fixtures.
