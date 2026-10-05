# CI Phase 2.5 Retained Coverage Proof

**Status:** Phase 2.5 confirmed on 2026-10-05, verification source `19b40d86f6716322e8579b456588de835a929961`,
`architecture/ci-testing-modernization`, 2026-10-05. The [plan](ci-testing-modernization-plan.md)
owns acceptance; the [ledger](ci-testing-coverage-ledger.md) preserves the pre-retirement coverage
inventory. This evidence does not register tests, activate hosts or complete Phase 2.6.

## Evidence And Reproduction

Ignored `.tmp/ci-phase25-20261005/` owns full compatibility JSON, diagnostic streams/timing events,
three baseline reports, focused native XML, synthetic-media observations and preservation evidence.
The disposable measurement scripts are observation aids, not permanent runners or test registration.
The full compatibility observer wraps existing handlers without changing membership, arguments,
timeouts, comparisons or failure behavior. Its diagnostics accompany the final concise producer
summary; detailed schema 1 and concise contract 1 remain authoritative.

```powershell
python Tools\Compatibility\run_compatibility.py --profile full-release --summary-json --report-output .tmp/ci/<run-id>/compatibility.json
python Tools\Conformance\run_conformance.py --profile baseline --summary-json --report-output .tmp/ci/<run-id>/python-baseline.json
pwsh -NoProfile -File Tools\Conformance\Run-Conformance.ps1 -Profile baseline -SummaryJson -ReportOutput .tmp/ci/<run-id>/ps7-baseline.json
python -m ruff format --check .
python -m ruff check .
python Tools\Static\lint_work_annotations.py --json
pwsh -NoProfile -File Tools\Static\Format-PowerShell.ps1 -Json
actionlint
python -m pytest Tools\Tests\Python\test_compatibility_retirement.py -q --junitxml=.tmp/ci/<run-id>/pytest.xml
```

Choose a unique ignored run ID. The actual floor run uses the checksum-verified portable PS7.4.0
from Phase 2.2; it changes no installation or machine PATH. Pester invocations import exact 6.2.0,
run `Tools/Tests/PowerShell`, enable NUnit XML in the owned directory and return aggregate failure
through `Run.Exit`. These direct native invocations still include temporary retirement proof until
2.6; they are not future catalog membership. pytest disables automatic third-party plugin loading.
No dependencies are installed or upgraded during this checkpoint.

## Completed Observations

| Execution | Observed seconds | Result |
| --- | ---: | --- |
| Python 3.14.5 baseline | 60.706 | All 21 suites pass. |
| PS7 7.6.6 baseline | 327.346 | All 21 suites pass. |
| PS7 7.4.0 baseline | 340.172 | All 21 suites pass. |
| Full-release compatibility | 601.486 reported | All 11 checks pass in order, including extraction/distribution/render. |
| pytest 9.1.1 | 2.892 outer | All 52 cases pass, with JUnit XML. |
| Pester 6.2.0 on primary | 12.298 outer | All 18 cases pass, with NUnit XML. |
| Pester 6.2.0 on floor | 13.605 outer | All 18 cases pass, with NUnit XML. |

The three complete baseline documents are exactly equal, and exactly equal to Phase 1.4's original
Python and PS7 baseline documents. All native XML counts show zero failures/errors/skips; Pester totals
include the four temporary Desktop cases per host. Their timing is retirement proof, not a future
steady-state native group measurement. Later pilots must measure the permanent groups after 2.6.

Static checks pass: Ruff format 0.113 seconds, Ruff validation 0.104, annotations 0.411 (22 fixtures /
395 files), PS7 formatting 9.920 (58 sources, no changes/long lines), actionlint 0.325. Warm startup is
0.029 seconds for Python and 0.194 for PS7; launch plus Python imports is 0.263 and exact PS7 module
imports 0.977. Imports verify PyYAML 6.0.3, pytest 9.1.1, Pillow 12.3.0, Pester 6.2.0,
powershell-yaml 0.4.12 and PSScriptAnalyzer 1.25.0. None of these is a cold bootstrap measurement.

The full observer's 629.131-second elapsed value includes post-run fingerprint auditing; its report's
601.486 seconds excludes final cleanup/publication. The [budget refresh](ci-testing-runtime-budget.md)
records measured cleanup/reporting separately and preserves the limits of both observations. Baseline,
media, native and full compatibility work ran sequentially; only lightweight read-only inspection and
documentation work overlapped. No concurrent rendering/conformance workload was used for timing.

Before/after audit freezes 491 tracked files and 47 protected canonical/generated baseline files.
The full run changed none; subsequent tracked changes are confined to the five review documents.
The new proof document adds no executable membership. All source, fixtures, registries, baselines,
requirements, workflows and canonical content remain unchanged. All 28 original Phase 1.4 JSON records
are preserved. The observed new external extraction path was absent after exit, as was full-run scoped
output. Normal-exit proof is independently observed, not inferred from a report's cleanup flag.
All 46 relative document links resolve; annotation policy and `git diff --check` pass after the final
documentation edits. Original Phase 1.4 measurement and numeric-budget blocks remain verbatim.

## Old Coverage To Retained Proof

Each paired suite below retains its source/fixture bytes and baseline membership. Complete detailed
JSON is compared, including negative cases, decisions and scale counts; independent green exits
alone do not establish parity. The ten-suite fast profile remains an unchanged subset, with its
earlier focused execution evidence preserved; no fresh fast-profile timing is claimed here.

| Existing paired suite | Retained proof / disposition |
| --- | --- |
| project-root | Complete 21-suite baseline in Python/PS7; only Desktop execution retired. |
| framework-installation | Same baseline and fixture assertions; only Desktop execution retired. |
| framework-catalog | Same baseline, negative/scale cases and full compatibility check. |
| capability-roadmap | Same baseline and roadmap/transition assertions. |
| strict-ingestion | Same baseline and byte/key/parser-budget assertions. |
| lookup-key | Same baseline and Unicode/collision assertions. |
| schema-pack | Same baseline and composition/typed-collision/scale assertions. |
| distribution-boundary | Same baseline plus full compatibility check; inert metadata semantics retained. |
| taxonomy | Same baseline and classification/scale assertions. |
| resource | Same baseline and resource/scale assertions. |
| effective-schema | Same baseline plus full compatibility CLI/export/report check. |
| source | Same baseline and identity/coverage/rejection assertions. |
| entity | Same baseline and identity/reference/scale assertions. |
| provenance | Same baseline and resolution/authority/rejection assertions. |
| temporal | Same baseline and coordinate/window/decision assertions. |
| chronology | Same baseline and ordering/topology/scale assertions. |
| reconciliation | Same baseline and ambiguity/deep-chain/termination assertions. |
| occurrence | Same baseline and recurrence/state/participation/scale assertions. |
| hosting | Same baseline and carrier/occupancy/composition/scale assertions. |
| interpretation | Same baseline and candidate-structure/comparison/scale assertions. |
| project-composition | Same baseline and enabled/disabled/provider-closure assertions. |

| Existing compatibility check | Retained full-release proof / intentional change |
| --- | --- |
| compatibility-reporting | Existing fixed success/failure/confinement/cleanup cases unchanged; synthetic registry now schema 3. |
| conformance-reporting | Detailed/concise/failure/report-byte proof retained; actual runtime-dependent counts are 2/4/2/2. |
| framework-catalog | Full catalog/project view, human/JSON/exports/selectors/failures retained in Python/PS7. |
| effective-schema | Schema, selection, human/QA reports, exports and invalid inputs retained in Python/PS7. |
| visualization | Bounded/unbounded projections and normalized inventory/hash oracle unchanged. |
| qa | Accepted 35-file inventory per runtime, bounded requests and content/hash oracle unchanged. |
| root-discovery | Existing four-location root-suite matrix retained in both runtimes; not every adapter. |
| artifact-lifecycle | Existing Python mutation/stale removal and paired rejection/dry-run proof retained; G04 remains open. |
| framework-extraction | Same copy boundaries, neutral consumer and nine selected portable suites; matching Python/PS7 results and observed normal-exit removal. |
| distribution-boundary | Independent paired inert-provider/portable-output comparison retained. |
| render | Existing output-size/required-label checks retained in both runtimes with installed rendering dependencies. |

All four compatibility profile memberships and check timeouts remain byte-for-byte unchanged from
2.4. The full-release run attempts every check; local/PR/distribution coverage is a subset argument,
not fabricated independent profile execution. The nine extraction IDs remain project-root,
framework-installation, framework-catalog, capability-roadmap, strict-ingestion, lookup-key,
schema-pack, temporal and interpretation. The measured copy has 304 reusable files and excludes
LoTM configuration/content and CI implementation tests; nine forbidden surfaces remain absent.

Static Python, PowerShell, annotation and workflow policy remain separate checks. Structured output
and command-surface parity remain owned by the paired suites/compatibility referee. All 71 methodology
families remain mapped in the original ledger. Retained pressure/review families are not converted
into new automatic passes; their existing obligations and G01-G15 implementation deferrals remain.
The dedicated hosted Desktop job is deliberately pending 2.6, not marked green by local proof.

## Temporary 5.1 Acceptance Proof And Permanent Tests

The following four `Host.Tests.ps1` cases are temporary migration proof. They issue 16 actual
Desktop child launches per Pester host invocation, using only process-scoped execution-policy handling
so machine policy does not mask rejection. They are not an ongoing supported-runtime comparison.

| Temporary case | Actual Desktop launches | Phase 2.6 disposition |
| --- | ---: | --- |
| returns structured Desktop readiness without importing framework services | 1 | Remove from regular execution; preserve acceptance evidence. |
| preserves concise failure reporting and writes no report on Desktop | 1 | Same; retain synthetic policy/report regressions. |
| rejects native manifest import and direct psm1 import on Desktop | 2 | Same; preserve supported manifest/import coverage. |
| rejects every public startup path on Desktop before root discovery or generation | 12 | Same; preserve supported startup/child coverage. |

The retained resolver case also uses the installed Desktop executable as an alternate existing file.
At 2.6 replace that input with a harmless fixture file and remove shared Desktop path setup. Keep
the six host cases and eight QA-child cases as ongoing implementation coverage. Their edition/version
policy vectors must remain synthetic; every permanent test must run without installed 5.1.
All 52 Python regressions remain useful registry/discovery/reporting/extraction tests: Desktop/version
strings are mock inputs, not real 5.1 launches. Their Python-only reporting cardinality proof runs Python.
If any historical migration harness is retained, invoke it only explicitly on demand outside normal
native roots/catalogs/profiles/hosted gates. No tests are moved or removed by this classification.

Synthetic media rehearsal creates an owned EPUB and an 8-by-8 RGB image; no local book/artwork is
read. Python and PS7 primary/floor find the same two text hits and produce the expected 3-by-4 crop
with exact pixels. PS7 rejects overwriting without Force and preserves the existing output bytes;
source bytes are unchanged and fixture scratch is absent after context exit. This Windows proof does
not claim Linux System.Drawing support. Permanent native media cases/required PR admission remain Phase 3.

## Retained Limitations And Rollback

The Phase 1.4 timeout-retained extraction directory still exists; its original evidence stays intact.
Successful new normal-exit cleanup does not prove timeout/cancellation cleanup or descendant ownership.
Compatibility remains fail-fast with per-call timeouts; conformance still lacks per-suite deadlines.
The [budget refresh](ci-testing-runtime-budget.md) replaces sizing candidates, not runner supervision.
Cold/offline bootstrap, isolated dependencies, native catalog/report adapters and live hosted evidence
remain later gates. PSScriptAnalyzer 1.25.0 needs 7.4.6, so formatter proof uses the primary host while
7.4.0 proves the framework runtime floor. The existing unimplemented manifest export remains a separate
finding; no export or API repair is folded into retirement.

Phase 2.5 changes only evidence/planning documents. Roll back those changes together;
keep raw historical evidence and accepted 2.2-2.4 implementations. No canonical refresh, registry
timeout change, workflow activation, machine uninstall or Git history rewrite is involved.
