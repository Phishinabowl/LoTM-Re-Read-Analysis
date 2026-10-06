# Native Test Layout, Discovery And Lifecycle

CI 3.2 defines native implementation-test discovery. Language-neutral conformance remains owned
by `Tools/Conformance/suites.json` and compatibility by its existing registry. Tests below do not
approve new conformance membership or replace retained semantic fixtures.

## Roots And Commands

`pyproject.toml` confines default pytest collection to `Tools/Tests/Python/test_*.py`, using
`test_*` functions and `Test*` classes. Strict configuration/markers, importlib import mode,
disabled third-party plugin autoload, strict xfail and disabled cacheprovider are explicit.
Use the already bootstrapped development interpreter; invocation never installs dependencies.

```powershell
python -m pytest --collect-only -q
python -m pytest -q
python -m pytest Tools/Tests/Python/test_bootstrap.py -q
python -m pytest -m integration -q
```

Explicit pytest CLI paths can override default discovery roots. The native conftest rejects items
outside its root when participating in collection. The later catalog launcher must validate every
requested path before invoking pytest; these defaults are not a security sandbox or catalog.

PowerShell uses exact Pester 6.2.0 through `PowerShell/PesterConfiguration.ps1`. It selects only
native `.Tests.ps1` files, sorts/deduplicates paths, validates explicit selections, disables
parallel/shuffled execution, confines Pester's container-hook root and disables unused TestRegistry.
Core 7.4+ is required; PS7.6.6 is the adopted development baseline. No module installation occurs.

```powershell
$configuration = & ./Tools/Tests/PowerShell/PesterConfiguration.ps1 -Discover
$result = Invoke-Pester -Configuration $configuration
$selected = @($result.Tests | Where-Object ShouldRun)
if ($selected.Count -eq 0 -or $result.FailedContainersCount -gt 0) { throw 'Native discovery failed or selected no tests.' }

$configuration = & ./Tools/Tests/PowerShell/PesterConfiguration.ps1 -Path Tools/Tests/PowerShell/Host.Tests.ps1
$result = Invoke-Pester -Configuration $configuration
if ($result.FailedCount -gt 0 -or $result.FailedContainersCount -gt 0 -or @($result.Tests | Where-Object ShouldRun).Count -eq 0) { throw 'Native tests failed or selected no tests.' }
```

Use `-Tag Unit` or `-Tag Integration` for category selection. Pester `TotalCount` includes excluded
tests; use selected `ShouldRun` identities when checking filters, empty selections and equivalence.
The configuration creates a Pester configuration object, not the Phase 4 aggregate orchestrator.

## VS Code Discovery

Tracked `.vscode/settings.json` enables pytest, disables unittest, restricts pytest arguments to
`Tools/Tests/Python` and restricts the Pester adapter glob to `Tools/Tests/PowerShell/*.Tests.ps1`.
The ignored local `.code-workspace` mirrors these settings because the installed Pester adapter
reads workspace-level configuration without a folder resource. Dependency caches are not test roots.
The local workspace may name the prepared development interpreter as its initial default; committed
settings must not contain a machine-specific interpreter path or a particular bootstrap cache key.

If VS Code already selected an interpreter, use **Python: Select Interpreter**, then **Enter
interpreter path**, selecting the development executable recorded by bootstrap. Changing
`python.defaultInterpreterPath` does not replace an existing selection. Reload the window or refresh
test discovery afterward. Editor discovery uses the Python extension's explicitly loaded pytest
adapter plugin; disabled automatic third-party plugin discovery does not block that explicit plugin.
The Testing panel is a development view, not suite membership authority or hosted acceptance.

## Current Files And Categories

| File | Category | Current identities | Ownership |
| --- | --- | --- | --- |
| Python/test_bootstrap.py | unit | 15 | Dependency grammar/cache/bootstrap implementation |
| Python/test_compatibility_retirement.py | unit/integration | 51 unit, 1 integration | Current registry/report/host/extraction implementation; inert legacy-host inputs are retained rejection cases |
| Python/test_package_artifact.py | unit | 18 | Wheel boundary and pure synthetic-consumer helper |
| Python/test_tooling_pilots.py | unit/integration | 9 unit, 3 integration | Annotation discovery/CLI, normalization and root API implementation |
| Python/test_native_results.py | unit | 33 | Native XML/phase truth, publication identity, adapter scope, timeout and finalization |
| Python/test_ci_catalog.py | unit | 58 | Private source/catalog trees, discovery/closure, deterministic planning, shard/gate admission and manifests |
| Python/test_ci_scope.py | unit/integration | 30 unit, 12 integration | Real private Git histories, snapshot/rename/mode/drift contracts and advisory selector closure |
| PowerShell/ConformanceRunner.Tests.ps1 | Unit | 6 | Conformance registry/selection/report helpers with inert synthetic runners |
| PowerShell/Dependencies.Tests.ps1 | Unit | 3 | Exact module-declaration implementation |
| PowerShell/Formatter.Tests.ps1 | Unit/Integration | 3 Unit, 4 Integration | Mocked Git/explicit-file discovery and real exact-version analyzer |
| PowerShell/Host.Tests.ps1 | Integration | 6 | Supported host/module/readiness collaboration |
| PowerShell/QaChildren.Tests.ps1 | Integration | 8 | QA launch functions with synthetic child helpers |
| PowerShell/RuntimeApi.Tests.ps1 | Integration | 2 | Source-module root precedence/rejection with neutral manifests |

Python's collection hook adds `unit` only when no category is declared, rejects overlapping
categories and sorts stable node IDs. Mark integration explicitly for real command/module
collaboration. Pester category tags are declared on owning Describe blocks and inherited by tests.
Helpers used only to prove one implementation's isolation may run in a subprocess without becoming
end-to-end project tests. Synthetic launch helpers never generate canonical LoTM output.

Pytest case identity is the repository-relative path plus node/function and explicit parameter ID.
Pester identity is repository-relative file plus expanded Describe/Context/It path. Exclude PID,
temporary paths, timestamps and Pester-generated GUIDs. New parameterized cases need stable IDs;
identities must be unique and unchanged between individual and aggregate discovery.

## Fixture And State Ownership

- Runtime/source implementation tests use explicit, temporary source import paths and restore them
  immediately after collection imports. Imported helpers must be the intended source implementation;
  installed-wheel verification remains its separate isolated child route.
- Python fixtures are function-scoped by default. Use `tmp_path`, context-managed temporary owners
  and `monkeypatch`; do not depend on a previously collected/executed file. The autouse fixture restores
  cwd, environment and `sys.path` after each case, including failures. It does not undo arbitrary
  object mutation: module/function patches belong to monkeypatch or an explicit finally block.
- Pester executable setup stays in BeforeAll/BeforeEach, teardown in AfterEach/AfterAll. Discovery
  bodies declare tests/data only; no child launches, package setup, service calls or canonical writes.
  TestDrive owns synthetic output. QA restores its environment variables; host tests remove their
  newly imported framework module and restore any prior framework module imports.
- TestRegistry is disabled because no current test owns registry fixtures. Adding registry coverage
  requires an explicit fixture/lifecycle decision, not enabling machine mutations for all tests.
- Shared language-neutral files remain read-only external fixtures. Mutations apply to owned copies.
  Source fixtures must never be silently replaced by data generated from the implementation under test.
- Each native file must run in a fresh process with only its declared dependencies. Later Phase 4
  process isolation/cancellation is authoritative; direct same-process runs are development conveniences.

## Registration And Failure Expectations

Directory discovery inventories candidate native files; it does not approve catalog membership.
Phases 3.3-3.5/4.1 assign group IDs, owners, entry paths, runtime/category, PR/full scope, fixture and
dependency inputs, impact paths and timeout/report contracts. The future catalog must reject stale,
missing, escaping, duplicate or unapproved entries, and reconcile discovered files with registration.
An intended nonempty group discovering zero tests is a failure; an explicitly unselected group is
reported separately. Pytest exit 5/collection errors and Pester failed containers/zero selected
`ShouldRun` tests cannot become passing coverage. No automatic fallback from an empty explicit
selection to the whole suite. Changed-file selection's conservative fallback belongs to Phase 4.

CI 3.2 local proof is preserved under ignored `.tmp/ci-phase32/`: default/individual discovery has
the same 85 pytest and 17 Pester identities on Windows/WSL; every file and both aggregates pass.
Python discovery used an audit guard rejecting network/DNS, child processes and file writes except
the explicit evidence JSON/null output device (capture disabled, bytecode disabled). Pester discovery
uses SkipRun; source inspection confirms only declaration bodies execute during current discovery.
Fresh Pester child-host proof verifies file independence and framework-module restoration. Empty,
escaping and stale Pester file selections fail. These observations validate current files, not a
general isolation/security guarantee for arbitrary future tests. No new semantic cases or registry
memberships were added. CI 3.2 is confirmed on 2026-10-05. VS Code discovery also confirms all
85 Python cases using the selected isolated development interpreter; the maintainer confirmed
that scoped Pester discovery removed the cached dependency test and cleared its pending state.

## CI 3.3 Pilot Scope And Evidence

CI 3.3 is confirmed on 2026-10-05: 12 pytest/15 Pester cases supplement the retained
foundation, giving 97/32 aggregate cases. Existing registry validation is retained rather than
duplicated. Annotation CLI integration reuses the 22 existing policy fixtures as one CLI/report
route, not a competing oracle. New writes use tmp_path/TestDrive; Git is mocked with argument/exit
assertions, registry runners are inert synthetic files and source API roots contain neutral manifests.
No service calls, canonical exports or dependency installation occur during these tests.

Support/Get-ToolFunctionBlock.ps1 is a test-only AST adapter loading actual function definitions
without command startup. The formatter uses real PSScriptAnalyzer 1.25.0; only the corruption-output
boundary is mocked. No production helper extraction or runtime refactor was required. New files
pass independently and all native cases pass on Windows/WSL. Observed aggregate process times are
Python 4.292s/2.057s and Pester 12.254s/23.208s, including startup; local samples, not hosted percentiles.
The formatter pilot needs the development host (PS7.6.6 adopted; analyzer requires Core 7.4.6+),
not the runtime-only 7.4.0 lane. Evidence/logs/native XML are ignored `.tmp/ci-phase33/`.

The pilots caught two genuine defects before their narrow fixes: annotation JSON error handling
referenced sys without importing it, and single-line formatting could switch LF/CRLF on its second
pass. The missing import is added; final formatting follows the existing CRLF policy. Invalid policy
and escaping CLI requests now return JSON failure/exit 1 instead of NameError. Both failure-detecting
assertions remain. No policy grammar, runtime/schema behavior, fixtures or suite membership changed.
Full static formatting passes 67 sources unchanged; annotation policy passes 22 fixtures without findings.

Proposed PR/full native groups are python-tooling-pilots, powershell-formatting-implementation,
powershell-conformance-implementation and powershell-runtime-api; formal registration belongs to 4.1.
G01/G02/G03/G10 receive partial implementation proof. Media/every-adapter coverage, exhaustive runner
supervision and broader report encoding/path/case/link safety remain later gates. Native failure
contracts and equivalence/adoption review are 3.4/3.5. No existing coverage is retired here.

## CI 3.4 Native Results And Failure Contracts

CI 3.4 is confirmed on 2026-10-05. The single-group adapter is
`Tools/CI/run_native_tests.py`; it invokes exact pytest 9.1.1 on CPython 3.14.5 or exact
Pester 6.2.0 on the selected supported PS7 host. It never installs missing dependencies.
Use the development executable and process-scoped module path recorded by bootstrap:

```powershell
$bootstrap = Get-Content .tmp/ci/bootstrap.json -Raw | ConvertFrom-Json
$python = $bootstrap.python.executable
$env:PSModulePath = $bootstrap.powershell.module_path
& $python Tools/CI/run_native_tests.py --runtime python --executable $python --group python-native
& $python Tools/CI/run_native_tests.py --runtime powershell7 --executable pwsh --group powershell-native
```

`--path` may repeat for existing files confined to that runtime's native test root; omitted paths
select the current sorted root files. `--filter` passes a pytest keyword expression or Pester
FullName pattern. An explicit empty result fails; it never broadens selection. This is local
development discovery, not approved catalog membership or affected-test selection.
`--timeout` is a positive child timeout (default 120 seconds, maximum 3600); the Python prerequisite
probe has a separate 15-second timeout. Phase 4 owns admission, whole-run budgets and process trees.

Each invocation creates a new `run-<uuid>` beneath `--output-root` (default `.tmp/native-tests`).
The adapter resolves links and confines output to the checkout's owned `.tmp`; absolute, relative,
sibling and escaping inputs are checked before launch. UUIDs identify artifact generations, not
native tests. Retained files are `native.xml`, publication `junit.xml`, `native-phases.json`, both
child stream logs, and `result.json` where produced. Missing XML/phase evidence cannot pass or reuse
an older generation. The complete structured result is also written to controller stdout.

The local JSON contract is `native-test-run`, version 1: identity, runtime, selected paths,
status/classification, aggregate and original child exits, duration, native counts, phase evidence,
run directory and available artifact names. Unknown counts/exits remain null. This is one native
group's result, not the later `ci-execution-report` supervisor contract. Exit 0 means passed;
1 means a blocking execution/result/report failure, 2 a rejected invocation/scope, and 130 cancellation.
Framework exits remain separate: for example pytest's empty-selection exit 5 becomes aggregate 1.

Both frameworks emit native **JUnit**, one of the reviewed JUnit/NUnit alternatives. Raw XML stays
unchanged. Publication XML prefixes existing case classnames with `<group>.<runtime>`; Pester's
absolute source classnames become repository-relative paths. It never adds a successful group case
or converts custom suites into invented native tests. Case names, diagnostics, durations and native
XML entries are retained. Actual selected inventory comes from pytest session/Pester ShouldRun
evidence. XML entries are counted separately because an assertion plus teardown error can yield two
entries for one pytest test. Pester excludes unselected tests from the selected inventory.

The explicitly loaded pytest observer retains setup/call/teardown outcomes and collection errors.
Pester retains selected identities, per-test errors and captured pipeline output, plus failed
container/block diagnostics. Child stdout and stderr stay separate; pytest captured case output is
also in its native XML. Discovery, setup, teardown, assertion, unexpected required skips/xfail,
strict XPASS, zero tests, wrong filters, unavailable dependencies and malformed/missing/inconsistent
result evidence all fail. Strict XPASS uses assertion classification; xfail/skips use result-contract.
Pester hook phases use actual error stack frames and owning native test AST extents.

`Fixtures/native_result_cases.py` and `Fixtures/NativeResultCases.Tests.ps1` deliberately fail only
when explicitly invoked; normal/editor root discovery excludes them. For example:

```powershell
$env:NATIVE_FAILURE_CASE = 'teardown'
try {
    & $python Tools/CI/run_native_tests.py --runtime python --executable $python --path Tools/Tests/Python/Fixtures/native_result_cases.py
    & $python Tools/CI/run_native_tests.py --runtime powershell7 --executable pwsh --path Tools/Tests/PowerShell/Fixtures/NativeResultCases.Tests.ps1
} finally { Remove-Item Env:NATIVE_FAILURE_CASE }
```

Local Windows/WSL proof under ignored `.tmp/ci-phase34/` covers 10 pytest/9 Pester deliberate
scenarios, plus real bare-environment pytest rejection. Both normal aggregates pass 130 pytest and
32 Pester cases, including the 33 permanent report/adapter unit regressions. XML escaping and Unicode,
both streams, native/publication case parity, stale avoidance and a Linux symlink escape are checked.
Cancellation proof is pytest KeyboardInterrupt and a controlled Pester child exit 130; it does not
certify Ctrl+C handling or descendant termination. Timeout tests preserve partial streams and unknown
counts; Phase 4 still owns process-tree cancellation/cleanup and exhaustive supervisor regressions.
No custom conformance fixtures, legacy coverage, workflow/check names or hosted publication change.

## CI 3.5 Adoption Boundary

The [pilot adoption review](../ci-testing-pilot-adoption-review.md) records scenario-level comparisons,
local feedback targets, exact representative/retained invocations and Phase 4 registration candidates.
It is confirmed on 2026-10-05. Native tests supplement existing semantic and actual-file checks;
no legacy family is retired. Catalog registration must avoid executing a native aggregate and its
constituent groups twice in routine coverage. Independent file proof remains an isolation/diagnostic
route. Prepared native timing targets exclude setup and the retained compatibility portfolio.

## CI 4.1 Catalog Registration

[Catalog planning](../CI/catalog-planning.md) is confirmed on 2026-10-05. Native discovery is now
reconciled with explicit owning groups; the deliberate Pester result fixture has a reasoned exclusion.
One installed-artifact group owns the separate explicit verification route. Catalog meta-regression
is always-run in native profiles, using private trees and inert entries without full-suite recursion.
Native execution still uses the 3.4 development adapter; catalog planning never invokes it. Scope
selection, supervision, complete reports and hosted adoption remain later checkpoints.

## CI 4.2 Scope And Selector Regression

[Git scope](../CI/change-scope.md) is confirmed on 2026-10-05. Its 42 cases supplement the 4.1
catalog gate; ci-scope is registered and always-run in native profiles. Git integration fixtures use
only owned temporary repositories, synthetic identities/content and standalone argument-array Git
commands, without fetching/publication or changing the real checkout. Snapshots use exact bytes/modes,
not source-generated semantic expectations. Narrow selection remains advisory; full execution and
pending actual-file policy obligations stay visible. Current native aggregate is 230 pytest cases.

## Framework References

- [pytest collection configuration](https://docs.pytest.org/en/stable/example/pythoncollection.html)
- [Pester configuration](https://pester.dev/docs/usage/configuration)
- [Pester discovery/run lifecycle](https://pester.dev/docs/usage/discovery-and-run)
- [Pester result object](https://pester.dev/docs/usage/result-object)
