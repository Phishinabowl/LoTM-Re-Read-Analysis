# CI 5.5 Coverage And Performance Acceptance Review

**Status:** Final local proof and CI 5.5 are confirmed by the maintainer on 2026-10-06.
Interim native/full timing exceptions are explicitly accepted; hosted adoption remains Phase 6.

**Subsequent plan extension (2026-10-06):** This confirmed 5.5 record remains the baseline. New
5.6/5.7 checkpoints now require scenario consolidation and current local optimization/timing
acceptance before Phase 6. The 90-second native / 16-minute full goals previously assigned here
to Phase 8.1 move to 5.7; dated measurements and accepted interim exceptions are not revoked.

The [modernization plan](ci-testing-modernization-plan.md) owns closure. This review neither retires
legacy checks nor activates GitHub/ADO authority. On 2026-10-06 the maintainer authorized narrowly
profiled runtime optimization with parity/consumer proof. Candidate changes include the Linux
documentation-path correction and lookup preparation improvements below. Final acceptance remains open.

## Corrected Committed Full Profile

Commit `ad5b71cea7ee4c8ac04dc98ea5bf88dcda131bdf` passes the public `full-verification` profile:
**74/74 units**, exit zero, 434 pytest cases and 44 Pester cases, all 42 paired baseline obligations,
11 compatibility checks, retained-result parity, actual repository policy/composition and installed
artifact verification. Canonical/source guards and containment pass; external scratch is removed.
Prepared outer execution is **1,210.201 seconds (20 minutes 10 seconds)**, against the accepted
960-second full target. Complete native/installed unit time is **120.521 seconds**, against 90 seconds.
This corrected successful record supersedes no historical measurement or fixture expectation.

The complete committed bundle is retained under ignored `.tmp/ci-phase55/full-baseline/`.
It is a passing local full profile, not hosted evidence or automatic acceptance of release review families.

## Safe CI Changes And Candidate Disposition

Catalog/scope tests prepare baseline templates once, then physically copy fresh files, registry
objects and independent Git metadata for each case. No hardlinks, shared mutable working trees,
assertion deletion or test-directory sweep are used. Two added regressions mutate a copy and prove
its template's data/history/configuration stays unchanged. All 115 affected cases pass; one combined
focused sample is 25.93 seconds versus about 30.90 seconds of original registered group time.
Different invocation boundaries mean this is a candidate observation, not an accepted full-run saving.

A registered Pester regression proves independent script scopes and later-container execution after
intentional discovery, setup, assertion and cleanup failures. It runs private synthetic containers,
not the production portfolio recursively. Existing runtime-API group ownership includes this file;
all six PowerShell groups remain independently supervised and all five mandatory Python
infrastructure groups remain unconditional.

The manual combined-Pester trial passes 45 cases in **23.976 seconds**, including that new regression.
Positive named-case and container-failure evidence alone cannot establish equivalence to six separate
processes after whole-process timeout/cancellation or arbitrary process-global contamination.
**Combined execution is not adopted**; no group, family or required check identity is removed.

Python catalog profiling attributes repeated owner-module compilation and path resolution to much of
constructor cost. A separate PowerShell lookup-loader probe measures identical 354,177-byte registries
at four paths: 4.111 seconds cold, then 2.774/2.808/2.787 seconds; the existing same-path cache hit is
0.000903 seconds. This identifies a concrete validation/setup hotspot. It does not prove a safe
cross-path cache or faster parser, and no runtime cache or parser change follows without the scope/design
review and full parity/consumer proof. Native startup batching alone cannot close the full-profile gap.

### Authorized Lookup Preparation Improvements

The loader retains one private template for exactly equal previously validated decoded registry text.
New paths are still read; changed text uses the original parser and all original validation. Successful
loads receive independent hashtables, nested arrays and trim sets, with their own diagnostic path.
Neither a returned first configuration nor a later clone can mutate the template. Failed reads,
malformed JSON, invalid scalars and invalid counts never seed a cache entry. The pre-existing same-path
cache behavior is preserved. There is no shared disk cache, hash-only reuse or parser replacement.

Four new runtime-API Pester cases prove mutation isolation, actual identical-text reuse, failed-read/
parse recovery, changed valid data and retained scalar/count rejection. All six runtime-API cases
pass through the repository native adapter on Windows. An exploratory direct `Invoke-Pester` call
failed because its default registry plugin lacked sandbox registry access; that is not passing
evidence. The repository configuration disables that unused plugin and supplies admitted results.

The repeated-new-path probe falls from about 2.8 seconds to **0.024/0.016/0.036 seconds**. A separate
alternating fresh-table probe identifies collection construction cost: `New-Object` takes **4.353s
initially / 2.977s subsequently**, versus **1.663s / 1.594s** for direct constructors. The lookup
implementation's seven constructors now instantiate the same .NET classes directly. The probe
overlaps the earlier captured full run, so it is profiling evidence, not an isolated aggregate budget
certification. Final aggregate results must correspond to both preparation changes together.

The Windows candidate `feature-feedback` profile passes **41/41 units** in **280.820 seconds
(4 minutes 41 seconds)**, within the 300-second target. Its native/installed units total
**117.727 seconds**, still above 90 seconds. This source overlay includes the fixture changes
and registered Pester regression (436 pytest/45 Pester); it predates the supervisor correction
below and does not substitute for final full-profile proof. Its 358-file publication bundle verifies.

Linux qualification exposed a process-state race: a `/proc` scan could report no active group
member before `Popen` had obtained the root's exit status. The PS7 prerequisite emitted passing
version/module evidence but was correctly rejected because its process result had a null exit
code. The corrected supervisor keeps the root active until its owned wait status is available.
A deterministic regression forces the empty-scan/live-root condition; all **43** process tests
pass independently on Windows and WSL. The real Linux prerequisite retry now records exit zero.
The failed Linux run is retained as failure evidence, not a passing timing sample.

A mounted-source run was gracefully cancelled with verified cleanup; its filesystem overhead
does not qualify native Linux performance. Qualification uses a fresh physical source copy on
WSL's Linux filesystem, with private Git metadata and explicitly recorded primary-overlay
provenance. No primary history or canonical source is changed.

The supervisor-corrected Linux feature run completes in **272.241 seconds**, with **39 passed,
one failed and parity blocked**; its 357-file publication bundle verifies. Native/installed units
total **100.611 seconds**. This failed run is not certified feature performance despite finishing
within 300 seconds. It exposes the PowerShell counterpart of the Python portability defect fixed
in Phase 2: native Linux `IsPathRooted` accepts `C:/outside.md`. Documentation validation now also
rejects explicit Windows absolute-drive syntax and normalized rooted paths. The existing fixture
and all 117 invalid-composition cases remain unchanged. Focused complete schema-pack results pass
on both Windows and Linux and exactly match the committed Windows result. No mixed-run aggregate
pass is assembled from the repair. Qualification was still pending at that point; the final
local acceptance record below supplies the later complete proof.

Feature-profile and further native measurements remain separate evidence. Unmet targets require
further safe optimization or an explicit reviewed tradeoff; timeout headroom and warm caches do not
satisfy performance acceptance. Hosted feature/full targets stay assigned to Phase 6. The existing
ShellCheck/pyflakes hosted-policy boundary remains explicitly open there.

## Every Stable Family Reconciled

The methodology's **71** current stable IDs remain: **37** executable/policy/parity families map to
passing committed results; **34** scenario/pressure families retain maintainer review. The matrix is
an evidence mapping, not another registration catalog or a claim that story-specific probes ran.
Historical Desktop support retirement remains the accepted Phase 2 policy; active parity is Python/PS7.
No generated count or successful primitive suite silently satisfies a retained scenario/pressure family.

| Stable family | Current verified obligation or retained boundary |
| --- | --- |
| `CONF-FRAMEWORK-INSTALLATION` | `conformance/framework-installation::python`, `conformance/framework-installation::powershell7` |
| `CONF-FRAMEWORK-CATALOG` | `conformance/framework-catalog::python`, `conformance/framework-catalog::powershell7` |
| `CONF-CAPABILITY-ROADMAP` | `conformance/capability-roadmap::python`, `conformance/capability-roadmap::powershell7` |
| `CONF-EFFECTIVE-SCHEMA` | `conformance/effective-schema::python`, `conformance/effective-schema::powershell7` |
| `CONF-PROJECT-COMPOSITION` | `conformance/project-composition::python`, `conformance/project-composition::powershell7` |
| `CONF-LOOKUP` | `conformance/lookup-key::python`, `conformance/lookup-key::powershell7` |
| `CONF-STRICT-INGESTION` | `conformance/strict-ingestion::python`, `conformance/strict-ingestion::powershell7` |
| `CONF-TEMPORAL` | `conformance/temporal::python`, `conformance/temporal::powershell7` |
| `CONF-CHRONOLOGY` | `conformance/chronology::python`, `conformance/chronology::powershell7` |
| `CONF-RECONCILIATION` | `conformance/reconciliation::python`, `conformance/reconciliation::powershell7` |
| `CONF-OCCURRENCE` | `conformance/occurrence::python`, `conformance/occurrence::powershell7` |
| `CONF-INTERPRETATION` | `conformance/interpretation::python`, `conformance/interpretation::powershell7` |
| `CONF-HOSTING` | `conformance/hosting::python`, `conformance/hosting::powershell7` |
| `CONF-PROJECT-ROOT` | `conformance/project-root::python`, `conformance/project-root::powershell7` |
| `CONF-PACK-COMPOSITION` | `conformance/schema-pack::python`, `conformance/schema-pack::powershell7` |
| `CONF-DISTRIBUTION-BOUNDARY` | `conformance/distribution-boundary::python`, `conformance/distribution-boundary::powershell7` |
| `CONF-TAXONOMY` | `conformance/taxonomy::python`, `conformance/taxonomy::powershell7` |
| `CONF-RESOURCE` | `conformance/resource::python`, `conformance/resource::powershell7` |
| `CONF-SOURCE` | `conformance/source::python`, `conformance/source::powershell7` |
| `CONF-ENTITY` | `conformance/entity::python`, `conformance/entity::powershell7` |
| `CONF-PROVENANCE` | `conformance/provenance::python`, `conformance/provenance::powershell7` |
| `STATIC-POWERSHELL` | `policy/powershell-format::powershell7` |
| `STATIC-PYTHON` | `policy/ruff::python` |
| `STATIC-WORK-ANNOTATIONS` | `policy/work-annotations::python` |
| `STATIC-GITHUB-ACTIONS` | `policy/actionlint::python` |
| `PARITY-SUPPORTED-RUNTIMES` | `parity/conformance-baseline::referee` |
| `PARITY-STRUCTURED-OUTPUT` | `compatibility/conformance-reporting::referee`, `compatibility/compatibility-reporting::referee` |
| `PARITY-COMMAND-SURFACE` | `compatibility/framework-catalog::referee`, `compatibility/effective-schema::referee`, `compatibility/conformance-reporting::referee`, `compatibility/compatibility-reporting::referee` |
| `COMPAT-FRAMEWORK-CATALOG` | `compatibility/framework-catalog::referee` |
| `COMPAT-EFFECTIVE-SCHEMA` | `compatibility/effective-schema::referee` |
| `COMPAT-VISUALIZATION` | `compatibility/visualization::referee` |
| `COMPAT-QA` | `compatibility/qa::referee` |
| `COMPAT-RENDER` | `compatibility/render::referee` |
| `COMPAT-ROOT-DISCOVERY` | `compatibility/root-discovery::referee` |
| `COMPAT-ARTIFACT-LIFECYCLE` | `compatibility/artifact-lifecycle::referee` |
| `COMPAT-FRAMEWORK-EXTRACTION` | `compatibility/framework-extraction::referee` |
| `COMPAT-VALIDATION-REPORTING` | `compatibility/compatibility-reporting::referee`, `compatibility/conformance-reporting::referee` |
| `SCENARIO-DERRICK` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-LOKI` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-PRIMER` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-ARRIVAL` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-MEMENTO` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-DOCTOR-WHO` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-WESTWORLD` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-PARODY-DERIVATION` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-CONTINUITY-IDENTITY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-MARVEL-SHARED-UNIVERSE` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-DC-CONTINUITY-REWRITES` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-COLLABORATIVE-CANON` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-VERSIONED-RULESETS` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-LIVE-SERVICE-NARRATIVE` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-RECONSTRUCTED-MEDIA` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-SERIALIZED-ADAPTATION` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `SCENARIO-TEXTUAL-TRADITION` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-CROSS-DOMAIN` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-ADVERSARIAL` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-SCALE` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-LAYER-PORTABILITY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-WORK-CONTINUITY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-MEDIA-DISTRIBUTION` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-EVIDENCE-AUTHORITY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-RULESET-POLICY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-ENTITY-IDENTITY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-TEMPORAL-TOPOLOGY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-RECURRENCE-STATE` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-EPISTEMIC-STATE` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-CAPABILITY-STATE` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-TEMPORAL-COMPOSITION` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-STRUCTURAL-INTERPRETATION` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-PARTICIPANT-CHRONOLOGY` | Retained maintainer review; supporting primitive coverage does not close this family. |
| `PRESSURE-HOSTED-IDENTITY` | Retained maintainer review; supporting primitive coverage does not close this family. |

## Final Local Acceptance Record

The final captured Windows candidate passes **74/74 units** in **1,093.662 seconds (18m14s)**,
**116.539 seconds / 9.63% faster** than the committed 1,210.201-second reference. All **478 original
native cases remain**, eight cases are added (437 pytest/49 Pester total), all **42** detailed
conformance rows match exactly, and the **556-file** publication bundle verifies. All eleven consumer
checks pass, including canonical projections, extraction, distribution and pinned rendering.
Source protection and containment verify; external scratch is removed. This is local-worktree
candidate evidence, not committed or hosted acceptance.

On 2026-10-06 the maintainer explicitly accepts **18m14s as an interim sequential full cost**.
The **<=960s (16m) full goal remains in Phase 8.1**, alongside the native goal below. Hosted targets
and executable budgets are unchanged. No fixture, family, check or guard is removed to meet a number.

The final Linux feature candidate passes **41/41 units in 275.151s (4m35s)**. Its 20 fast-conformance
rows exactly match retained full-baseline rows, all 437 pytest/49 Pester cases pass, its 358-file
publication verifies, containment/source protection verify and external scratch is removed. This
sample overlaps the earlier Windows intermediate run; it is an observed passing cost under that
load, not a precision claim about isolated Linux throughput. No Linux full-release proof is claimed.

Two intermediate Windows trials were terminated deliberately: one for the overlong fixture line,
and one after its 42 conformance/native obligations passed because the constructor change superseded
that capture. Neither is a full pass or timing acceptance record. Their durable partial evidence
remains; guardian cleanup verifies and recorded external scratch is removed.

On 2026-10-06 the maintainer explicitly accepts the measured interim complete native/installed
costs of **122.277s Windows / 105.911s Linux**, retaining independent process isolation. The
**<=90s goal remains assigned to Phase 8.1**. The separate final Windows feature sample records
**131.242s** for the same complete native/installed cohort; this observed variation stays visible.
The full interim exception is recorded above; feature/hosted targets and executable budgets
remain unchanged. These are reviewed interim timing exceptions, not removal of coverage or adoption
of the unsafe positive-only batch prototype.

Final Windows feature verification passes **41/41 units in 285.973s (4m46s)**, within the unchanged
300-second target. Its 20 detailed fast-conformance rows exactly match final full results, all
437 pytest/49 Pester cases pass, its 358-file publication verifies and external scratch is removed.
Windows full and feature measurements run sequentially without overlapping benchmarks.

The current candidate inventory is 437 pytest/49 Pester cases, including three new Python isolation/
supervisor regressions, one Pester container regression and four lookup preparation regressions. Windows/Linux focused process tests,
schema-pack equivalence, Ruff lint/format, owning PowerShell formatting, annotation policy (22/22
fixtures, 465 files) and `git diff --check` pass. The first full-profile section is specifically the
committed reference; this final acceptance record qualifies the captured candidate implementation.

Complete original gates remain available. The maintainer confirms this checkpoint and authorizes
focused branch publication on 2026-10-06. No required check identity or legacy runner is retired. Phase 6 owns exact
committed hosted evidence, optional hosted-policy integrations and platform publication/activation.
The subsequent plan extension assigns the retained 90-second native and 16-minute sequential full
optimization goals to 5.7 before hosting; Phase 8.1 owns retirement after verified hosted equivalence.
