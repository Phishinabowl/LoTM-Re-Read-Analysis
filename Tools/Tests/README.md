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
| PowerShell/Dependencies.Tests.ps1 | Unit | 3 | Exact module-declaration implementation |
| PowerShell/Host.Tests.ps1 | Integration | 6 | Supported host/module/readiness collaboration |
| PowerShell/QaChildren.Tests.ps1 | Integration | 8 | QA launch functions with synthetic child helpers |

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

## Framework References

- [pytest collection configuration](https://docs.pytest.org/en/stable/example/pythoncollection.html)
- [Pester configuration](https://pester.dev/docs/usage/configuration)
- [Pester discovery/run lifecycle](https://pester.dev/docs/usage/discovery-and-run)
- [Pester result object](https://pester.dev/docs/usage/result-object)
