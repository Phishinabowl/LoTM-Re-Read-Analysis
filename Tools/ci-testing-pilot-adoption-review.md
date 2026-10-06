# CI 3.5 Pilot Equivalence And Adoption Review

**Status:** Confirmed on 2026-10-05, closing CI 3.5 and the Phase 3 local exit gate.
Inspected source baseline: `bda40eb9787437f27f9c9b9e7d20c1463d9afdcf`.
The [modernization plan](ci-testing-modernization-plan.md#phase-35-pilot-equivalence-and-adoption-review)
owns acceptance; the [coverage ledger](ci-testing-coverage-ledger.md) owns gap dispositions.
This review approves candidates for later registration, not executable membership or hosted activation.

## Coverage Decision

Adopt the existing native foundations and pilots as supplementary implementation coverage for
Phase 4 registration. **No retained runner, fixture family, policy check or hosted gate can be retired
on this evidence.** The pilots test implementation contracts; the 21 paired conformance suites and
11 compatibility checks retain semantic/project authority. Their runtime list is Python/PS7 under
the already confirmed Phase 2 support policy. PS5.1 retirement is not reopened here.

The matrix below compares specific behaviors, not unlike counts. “Additional” means the native
case proves a failure boundary beyond an existing real-content check. “Partial overlap” means
both routes remain until broader equivalence/adoption proof identifies one owner for each obligation.
No row claims native tests replace the full legacy family. Test file paths are relative to
`Tools/Tests/`; actual assertions and fixture inputs are inspected at the source baseline above.

| Scenario | Retained authority / current proof | Native positive and deliberate negative proof | Disposition / remaining boundary |
| --- | --- | --- | --- |
| Annotation grammar | Static policy's 22 authored fixtures and actual repository scan | Python/test_tooling_pilots.py CLI invokes the same 22 fixtures; invalid policy and escaping path return JSON/exit 1 | Partial overlap; keep one authored oracle, preserve actual-file validation. Consolidate repeated fixture execution at 5.1 only after equivalent CLI evidence. |
| Annotation inventory/I/O | Repository scan discovers real files through Git | NUL-delimited spaces/Unicode, sorted/unique selection, failed Git, absent/escaping paths, invalid UTF8 and byte limit | Additional implementation coverage; mocks prove argument/error handling, not Git scope resolution. |
| Formatter meaningful tokens | Static formatter checks actual tracked/nonignored sources | PowerShell/Formatter.Tests.ps1 uses real exact analyzer for separators/comments/strings/idempotence; parse errors and mocked corrupt formatter output are rejected | Additional; keep actual-file formatting. Native corruption mock is labeled, not a claim about real analyzer corruption. |
| Formatter discovery | Static tool's actual repository inventory | Mocked Git exit/inventory, deleted/duplicate sources and explicit missing/unsupported paths | Additional; no complete changed-file policy validation or rename/deletion scope proof yet. |
| Conformance catalog/order | Existing paired runners load suites.json and run its selected semantic suites | PowerShell/ConformanceRunner.Tests.ps1 rejects duplicate IDs, unregistered files, stale exclusions and invalid selection; checks declared order with inert private runners | Partial overlap; semantic execution remains in paired suites. Python registry regressions remain in the existing foundation file. |
| Conformance JSON/excerpts | Compatibility conformance-reporting exercises public help, commands, failure reports and both runtimes | Pester helper tests retain counts/failed IDs, UTF8 excerpt bounds, complete Unicode JSON and basic destination rejection | Partial overlap; helper calls do not replace subprocess parity, public switches or legacy report link/case safety. |
| Compatibility normalization | Real QA/Visualization baselines and cross-runtime comparisons | Python/test_tooling_pilots.py preserves authored content/list order, removes generated-only fields, and rejects changed/missing JSON/binary artifacts | Additional independent implementation boundary; real LoTM baselines remain unchanged. |
| Root precedence/rejection | Project-root conformance, root-discovery and neutral extraction | Python/PowerShell root API tests prefer explicit roots and reject invalid/relative overrides without fallback | Partial overlap; two source API edges do not prove every adapter/cwd or installed origin. |
| Host/dependency readiness | Module manifest, readiness commands and retained supported-runtime launches | Host.Tests.ps1 / Dependencies.Tests.ps1 plus Python registry/extraction tests reject unsupported inventories, broken modules and unsafe/floating declarations | Supplementary permanent supported-host proof; retired-host inputs are inert rejection fixtures, not live 5.1 runs. |
| QA helper delegation/lifecycle | Real compatibility QA inventory/hashes, artifact-lifecycle rejection/dry-run routes | QaChildren.Tests.ps1 verifies three child argument/cwd/host routes, failure handling, real owned cache deletion and stale bounded-output removal | Additional; synthetic child tests do not replace real rendered pages or complete PowerShell destructive parity/canonical protection. |
| Bootstrap/cache | Explicit 3.1.2 cold/fresh-offline/check builds and hosted acquisition proof | test_bootstrap.py rejects missing/corrupt payloads, unsafe includes, graph conflicts and inherited path/browser overrides without implicit downloads | New implementation layer; receipt/hash checks remain alongside explicit installation proof. |
| Package content/installed origin | Nine-suite copy-based neutral extraction remains active | test_package_artifact.py rejects wrong metadata/content/RECORD; verify_installed_package.py proves fresh isolated import/dependencies and ten positive/negative installation checks | New artifact boundary; source/extraction and installed-wheel routes have distinct obligations. No universal reproducible-build claim. |
| Native result/exit truth | Legacy detailed JSON/concise v1 reporting remains public | test_native_results.py and explicit native fixtures reject assertion/collection/setup/teardown, zero/filter, required skip/xfail/XPASS, missing dependencies/XML, inconsistent exits/counts and publication/write failures | New native-report layer; raw XML, case diagnostics, counts and both streams survive. Full aggregate/custom XML/publication belongs to 4.5/6.4. |
| Cancellation/timeout/cleanup | Existing per-call timeout/extraction cleanup evidence | Native pytest interrupt, controlled Pester exit 130, partial-stream timeout and post-context cleanup checks | Partial; no descendant ownership, Ctrl+C guarantee or whole-run deadline equivalence. Mandatory 4.3/4.6 process proof remains. |

These comparisons retain failure-detecting assertions for the two genuine 3.3 fixes (annotation's
missing sys import and formatter line-ending idempotence) and the 3.4 publication-failure exit fix.
Tests use independent expected values or existing authored fixtures; they do not regenerate oracles
from production output. Native framework failure fixtures remain excluded from normal/editor discovery.

## Diagnostics, Isolation And Cost

Legacy semantic/reporting checks retain detailed JSON, concise v1 summaries and runtime comparison.
Native adapters add actual JUnit case evidence and separate framework/aggregate exits; they do not
invent per-fixture native granularity for custom suites. Passing controller output is structured JSON;
concise human/Markdown aggregation is still 4.5. Pester's captured pipeline output is in phase evidence,
pytest case captures are in XML, and child stdout/stderr have separate logs.

Per-file fresh-process independence and discovery were proved at 3.2; 3.3 adds independently runnable
pilot files. TestDrive/tmp_path own native fixture writes and restore environment/import/module state.
The installed-wheel route runs outside the checkout in a fresh owned environment. Native adapters
use fresh output generations and resolved path confinement. This is not a general security sandbox,
complete canonical guard or process-tree ownership guarantee. Phase 4 must connect those guarantees
before adopting supervisor-managed execution. Canonical prose, structured content and baseline hashes
have not changed during this pilot work.

| Measured local route, including process startup | Windows seconds | WSL seconds | Evidence |
| --- | ---: | ---: | --- |
| 3.3 representative Python file (12 cases) | 0.975 | 0.609 | .tmp/ci-phase33/*-proof.json |
| 3.3 Formatter / ConformanceRunner / RuntimeApi individual files | 3.387 / 2.415 / 2.563 | 4.282 / 3.584 / 3.426 | Same; exact analyzer is active for formatter |
| 3.4 adapter Python aggregate (130 cases) | 4.995 | 2.260 | .tmp/ci-phase34/*-python-aggregate.json |
| 3.4 adapter Pester aggregate (32 cases) | 12.071 | 23.305 | .tmp/ci-phase34/*-powershell7-aggregate.json |
| 3.1.3 installed-artifact verification (ten checks) | 7.456 | 3.822 | .tmp/ci-phase313/windows.json and linux.json |

These are dated samples of different checkpoints, not simultaneous full-profile runs or percentiles.
Their sums (approximately 24.5s Windows / 29.4s WSL for the current aggregates plus installed checks)
are planning estimates for that cohort, excluding bootstrap/build/static/conformance/project checks.
No per-file run should also repeat the same aggregate in routine coverage; independent file proof
belongs to diagnostics or explicit isolation regression. Keep group placement measurable at 4.1/5.1.

**Accepted feedback goals:** already prepared native Python aggregate <=15s, native
Pester aggregate <=40s, installed-artifact verification <=15s, and the current cohort sequentially
<=60s on each adopted local OS. Measure controller wall time, record test/launch counts and investigate
regressions against a comparable sample. These are feedback goals, not silently lowered failure
timeouts. The current adapter default remains 120s; Phase 4 admits whole-unit/run deadlines separately.
Reconcile the complete PR/full portfolio at 5.1, then measure hosted cold/warm behavior at 6.1/6.5.

Windows bootstrap evidence gives 1.302s for an existing Python environment verification and 21.105s
for a fresh offline Python environment from verified payloads (3.1.2 samples, rounded).
Accepted corresponding local goals are <=5s verification and <=45s fresh offline preparation.
Separate an already prepared environment from payload restoration/reinstallation: they are different
cache states. PowerShell module reuse and combined hosted setup need separate measurements; no
combined warm-setup saving is asserted from Python alone. The failed cold-all attempt is not an
accepted cold baseline. Fresh hosted bootstrap proof took 2m55s Windows / 2m00s Linux for an entire
verification job, not dependency installation alone. Existing provisional 600s cold allowance remains
until clean-host measurements replace it; see [runtime budget](ci-testing-runtime-budget.md).

Rendering is not in this routine native cohort. The recorded Chrome/npm cold and fresh-offline
samples (~248s/~246s) versus verified reuse (~8s) show why payload caching alone must not be
advertised as an installed-environment speedup. Retained compatibility's hosted 999s whole-job
sample includes 239s Mermaid installation; the 55-minute job timeout is headroom, not normal duration.
No full CI speedup is established by the native targets. Keep setup/duplication optimization with
5.1/5.5/6.1 and affected selection explain-only until Phase 7.

## Local Reproduction And Registration Candidates

[Native commands/artifacts](Tests/README.md#ci-34-native-results-and-failure-contracts) provide
both aggregate invocations and explicit failure recipes. To run only the representative tooling pilots:

```powershell
# $python and process-scoped PSModulePath come from the prepared bootstrap report.
& $python Tools/CI/run_native_tests.py --runtime python --executable $python --group python-tooling-pilots --path Tools/Tests/Python/test_tooling_pilots.py
& $python Tools/CI/run_native_tests.py --runtime powershell7 --executable pwsh --group powershell-formatting-implementation --path Tools/Tests/PowerShell/Formatter.Tests.ps1
& $python Tools/CI/run_native_tests.py --runtime powershell7 --executable pwsh --group powershell-conformance-implementation --path Tools/Tests/PowerShell/ConformanceRunner.Tests.ps1
& $python Tools/CI/run_native_tests.py --runtime powershell7 --executable pwsh --group powershell-runtime-api --path Tools/Tests/PowerShell/RuntimeApi.Tests.ps1
```

Retained commands remain independently executable (these run real checks and may take longer):

```powershell
& $python Tools/Static/lint_work_annotations.py --json
./Tools/Static/Format-PowerShell.ps1
& $python Tools/Conformance/run_conformance.py --profile baseline --summary-json --report-output .tmp/ci-review/python-conformance.json
./Tools/Conformance/Run-Conformance.ps1 -Profile baseline -SummaryJson -ReportOutput .tmp/ci-review/powershell-conformance.json
& $python Tools/Compatibility/run_compatibility.py --check conformance-reporting --json --output-root .tmp/ci-review/compatibility
```

[Installed-artifact commands](CI/README.md#installed-artifact-verification-ci-313) explicitly build
and verify a wheel; they must not be hidden in pytest setup or confuse source tests with installed proof.
Linux uses its prepared Linux interpreter, pwsh and module cache with the same repository-owned entry
points. The WSL snapshot is a test copy, not another publication checkout. Existing workflow YAML
still runs retained gates; native steady-state host membership is not activated by these commands.

Register current bootstrap/dependency, supported-host/compatibility, QA-child, package-artifact,
installed-runtime, tooling-pilot, formatting, conformance-helper, runtime-API and native-result
candidates through 4.1. Assign one owning group per test file and avoid executing aggregates plus
their constituent groups as duplicate coverage. Source/package verification remains a distinct route.
Required runtime/OS, dependencies, fixtures, impact edges and timeout/report contracts must be explicit.

Next mandatory implementation groups follow actual Phase 4 APIs: catalog/plan validation (4.1),
Git scope and conservative selection (4.2), process ownership/budget/cancellation (4.3), layer adapters
and independent aggregate failure (4.4), projections/finalization/lifecycle (4.5), reconciled as the
nonrecursive meta-regression gate (4.6). Their tests use private catalogs and synthetic children,
not recursive full-suite execution. Media/adapter/lifecycle gaps, complete 21-suite parity and neutral
extraction expansion retain 5.1-5.4 ownership; synthetic media remains required PR coverage.

## Phase 3 Exit And Rollback

The already confirmed 3.1 package/installed proof, 3.2 discovery/isolation, 3.3 pilots and 3.4 failure
matrix satisfy the Phase 3 local foundation gates. This checkpoint inspects that evidence without
rerunning unchanged long compatibility portfolios. Reviewed gap closures are partial except the
initial package foundation: G15's local package contract/installed proof is implemented, while
registration/host adoption/extraction expansion remain explicit follow-ups. G01/G02/G03/G07/G10
remain open for their wider scope; G04/G05/G08/G09/G11/G12/G13 are not closed by native case counts.

Rollback leaves original suites/checks, fixtures, detailed JSON and standalone commands available.
No legacy replacement switch has been activated. Revert focused native/package adoption if needed;
do not reintroduce PS5.1 or discard canonical content as an incidental rollback. Later retirement
requires a scenario-complete old/new comparison, real negative detection, required-OS diagnostics,
measured cost, local invocation, unchanged check/protection intent and a separately accepted rollback.

Documentation/evidence review resolves 52 relative links/anchors across this review, plan, ledger
and test README. Annotation policy passes 22 fixtures / 433 files without findings; diff checks pass.
Ignored `.tmp/ci-phase35/review.json` records inspected native/package/extraction status and timing
samples, retained registry counts and proposed goals. These checks inspect accepted historical
runtime evidence; no new full-suite timing, hosted result or replacement equivalence is invented.
