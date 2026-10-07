# CI Runtime, Dependency And Budget Design

**CI 6.2 hosted PR shadow overlay (verified and confirmed on 2026-10-07):**
[Complete qualification](ci-testing-github-shadow.md#final-hosted-qualification-and-review) records
76/76 for source and merge at `9ff0827`, with exact coverage/native identities. Dispatch-to-completion
wall is 971s/965s (16m11s/16m05s); summed job allocation is 2448s/2434s (40m48s/40m34s). This is PR
shadow evidence, not full-verification or final hosted admission. Collection itself costs only
2.915s/2.959s while its full worker costs 148s/125s because complete dependency/render preparation
is repeated. Compatibility workers cost 648s/695s; parity also waits behind the whole independent
wave. Qualify reduced preparation and dependency-specific barriers at 6.5 without dropping units or
isolation. These single samples do not relax feedback targets, reserves or 90s/960s goals. Source and
merge replay duplication is intentional qualification overhead, not proposed routine double execution.

CI 6.1's [corrected core payload checkpoint](ci-testing-host-readiness.md#corrected-core-payload-checkpoint)
measures Python development/media and PS development bootstrap at 22.454-26.693s cold and
11.088-12.701s warm across GitHub/ADO Windows/Linux. Cache restore/save, interpreter provisioning,
checkout, queue and publication are separate. Windows Python provisioning alone costs roughly
45-52s in these samples. This does not measure complete build/render dependencies or full test
execution, and does not reduce provisional setup reserves, profile deadlines or accepted goals.

**CI 6.1 complete setup overlay (verified and confirmed on 2026-10-07):** The
[complete hosted qualification](ci-testing-host-readiness.md#complete-hosted-qualification-and-61-review)
at published `ba6047a` measures development/media, PS modules, fresh package build, locked npm/Chrome,
owned Node provisioning and real rendering. Cold/warm helper setup is GitHub Windows 68.594s/51.901s,
Linux 56.341s/19.782s; ADO Windows 79.174s/57.647s, Linux 57.252s/39.062s. Warm restores add
~6s/~4s GitHub and 10.450s/11.257s ADO (Windows/Linux); cold cache saves cost ~6s/~4s GitHub
and 26.770s/23.357s ADO. Whole cold/warm jobs are 138s/118s and 87s/43s GitHub, 181.580s/143.647s
and 108.010s/76.327s ADO. These single samples demonstrate net transport benefit, not medians or
full test execution. Interpreter provisioning remains separate, about 46-51s on Windows in these
samples; dispatch/allocation and serialized waiting are distinct from computation. Approximately
360 MB per complete platform payload makes cache transport a visible cost. Both negative controls
remain failed and fresh recovery passes; no silent repair or failed-cache save is credited as speedup.
Retain provisional setup reserves and 90s/960s goals. Profile/shard measurement and final placement
remain 6.5; no custom image/feed adoption follows from this preparation experiment.

**Status:** Phase 1.4 measurement/design checkpoint confirmed on 2026-10-05. Baseline: `c5d1d78`,
`architecture/ci-testing-modernization`, 2026-10-03. The
[accepted contracts](ci-testing-contracts.md) own orchestration semantics; their decision record
references the selections here. The [plan](ci-testing-modernization-plan.md) owns closure.
This document does not change requirements, executable catalogs, workflows or host settings.
Phase 2.5's retained-runtime refresh is confirmed on 2026-10-05; dated Phase 1.4 evidence remains below.

CI 5.1's [same-snapshot shadow comparison](ci-testing-shadow-comparison.md) is confirmed on
2026-10-06. Its failed full runs identify correction/optimization work; they do not
replace the successful Phase 2.5 reference or prove hosted throughput.

**CI 5.7 current local overlay (confirmed by the maintainer on 2026-10-06):** The
[optimization review](ci-testing-local-optimization-review.md) records Windows full 74/74 in
1,056.779s (17m37s), 36.883s / 3.37% faster than 5.5, and Windows feature 41/41 in 271.451s
(4m31s). Linux feature passes 41/41 in 266.949s (4m27s), with exact 573-file source provenance.
Complete native cohorts take 125.152s full / 125.225s feature on Windows and 105.520s on Linux.
Both feature proofs satisfy the maintainer's conditional native/full timing exceptions;
<=90s native / <=960s sequential full remain goals with measured follow-up at Phase 8.1.
Feature/hosted targets, executable ceilings, independent
processes and complete coverage are unchanged. No Windows full-native speedup is claimed.
Prepared execution includes capture/preflight/reporting and excludes acquisition. The 53.064s
full non-unit remainder includes post-unit guards and publication, so it is not all setup. Restricted
environment diagnostics do not qualify performance. Phase 6 owns cache transport/hosted measurement.

**Phase 5.8 placement gate confirmed (2026-10-06, implementation not started):** The
[Linux portability/full comparison checkpoint](ci-testing-modernization-plan.md#phase-58-linux-portability-full-comparison-and-os-placement)
must distinguish current Windows-only registration from actual dependencies, qualify proposed Linux
owners and compare equivalent complete coverage before hosted adoption. If Windows obligations remain,
measure and label the split explicitly; it is not a full Linux pass. Preserve 5.7's accepted timings,
exceptions and goals. Source/coverage equivalence and normal execution conditions precede timing;
final agent/cache/queue and placement validation remains Phase 6 on real GitHub/ADO hosts.

**5.8.1 inventory overlay (confirmed by the maintainer on 2026-10-06):** The
[Linux inventory](ci-testing-linux-portability-inventory.md) reconciles all 74 IDs: 40 exact feature
overlaps, 22 additional conformance variants, baseline parity and eleven unqualified compatibility
owners. No intrinsic Windows requirement is established for those eleven; actual QA path behavior
and absent Linux render preparation block an immediate equivalent full run. D12 media behavior
coverage is still missing from permanent registration. Its approved bounded closure preserves Windows-only
System.Drawing image coverage and changes complete portfolio accounting; do not credit added or
omitted work as faster execution. No new timing sample or relaxed budget follows from this inventory.

**5.8.2 qualification overlay (confirmed by the maintainer on 2026-10-06):**
[Focused qualification](ci-testing-linux-qualification.md) admits the eleven compatibility owners
on Linux and retains one genuinely Windows-only synthetic image group. Complete full coverage is
now 77 units (76 portable plus that required Windows obligation); feature/PR counts are 44/76.
New media groups reserve 30 seconds each, in their own admitted shard; existing unit deadlines,
2190-second shard execution ceilings and feedback goals remain. Profile safety envelopes add
90 seconds for required work, independently of feedback targets. Focused preparation/retry timings
are not new full/feature benchmarks. Phase 5.8.3 must compare identical core coverage and account
for all added media plus the Windows remainder before proposing placement or timing disposition.

**5.8.3 complete local comparison (confirmed by the maintainer on 2026-10-06):** The
[comparison record](ci-testing-os-comparison.md) measures Windows 77/77 at 1010.466s whole wall
(16m50s), with 131.930s implementation/native cost. Linux retains the same 77 IDs, passes 76 portable
units and explicitly blocks Windows image coverage: 1189.784s whole wall (19m50s), with 104.905s
qualified implementation cost. Both use identical captured bytes/modes and catalog digests, with
512 matching portable native identities, exact 42-row conformance parity, canonical guards and
verified cleanup/publication. Linux's complete report remains nonpassing; the 3.590s Windows image
unit is separately proved in the fresh full Windows reference. Its additive cost is an estimate
without standalone Windows setup, not an end-to-end split benchmark or passing aggregate.
Linux's whole invocation is 17.7% longer; conformance/compatibility outweigh faster portable native
execution and lower non-unit overhead. The accepted provisional initial full default is Windows, subject to
real hosted cache/queue/agent/throughput and placement proof in Phase 6. 90s / 960s goals remain;
the maintainer explicitly accepts the changed-coverage cost exceptions on 2026-10-06, with measured
follow-up at Phase 8.1. Acquisition and the restricted failed diagnostic are
excluded; these are single local prepared samples. Detailed component/overhead limits remain explicit.

## CI 5.1 Feedback Targets And Current Gap

**Plan sequencing revision (2026-10-06):** The agreed 5.6/5.7 extension now places coverage/scenario
consolidation and local optimization/timing acceptance before hosted adoption. References below to
Phase 8.1 follow-up retain the dated 5.5 decision; current ownership of the <=90s native / <=960s full
goals is Phase 5.7. Existing interim acceptances and measurements are preserved. Phase 8.1 reviews
post-hosted retirement and final rollout costs; it does not defer the expanded local exit gate.

CI 5.5's [acceptance review](ci-testing-acceptance-review.md) records a corrected committed passing
full profile at `ad5b71c`: 74/74 units, 434 pytest/44 Pester cases and safe cleanup, **1,210.201s
(20m10s)** outer wall time. Complete native/installed units total **120.521s**. These exceed the
unchanged 960s/90s targets; no timeout or coverage concession closes that gap. Candidate fixture
preparation and positive Pester batching are separate measurements; batching is not adopted because
whole-process timeout/failure isolation is not yet equivalent. Runtime profiling identifies repeated
lookup-registry construction. The maintainer authorized narrow runtime optimization on 2026-10-06;
final same-candidate measurements and acceptance remain open.

The Windows candidate feature profile passes 41/41 in **280.820s**, with **117.727s** of native/
installed work. Linux native-filesystem qualification takes **272.241s**, but fails schema-pack
documentation-path validation and blocks parity; it cannot certify the feature target. Its native/
installed work is **100.611s**. The narrow path repair passes focused unchanged conformance on both
OSes; a fresh aggregate proof is still required. These observations do not relax any target.

**Explicit interim native exception (2026-10-06):** The maintainer accepts final candidate native/
installed costs of **122.277s Windows / 105.911s Linux** while retaining independent processes and
coverage. The **<=90s goal is retained in Phase 8.1** for further optimization/review. No full,
feature or hosted target, timeout allowance, registration or required obligation is relaxed.
The final Linux feature run passes 41/41 in **275.151s**, with exact retained fast conformance
and verified publication/cleanup. Windows final full proof passes as recorded below.

**Explicit interim full exception (2026-10-06):** Final Windows full verification passes 74/74 in
**1,093.662s (18m14s)**, versus committed 1,210.201s: **116.539s / 9.63% faster**, with eight added
native cases and all 478 original named cases / 42 detailed conformance rows preserved. The maintainer
accepts this measured interim sequential cost. The **<=960s full goal remains in Phase 8.1**;
hosted/feature targets and executable allowances are unchanged. Final Windows feature passes 41/41
in **285.973s (4m46s)**, with verified publication/cleanup and exact fast-profile conformance.
Its separate native/installed sample is **131.242s**; the variation from the full sample remains
visible in the acceptance review and Phase 8.1 follow-up. No new hard native ceiling is inferred.

The exact committed source is `1627dfecf902287b83d683234ad2b7bca8a29aad`, with the prepared adopted
Windows runtimes/dependencies. Legacy standalone portfolios total **983.272s (16m23s)**; replacement
full shadow takes **1,179.022s (19m39s)** and reports 70 passes, three failures and one error across
74 units. Rendering also exposes unsafe global dependency resolution. These are not accepted
successful full-profile performance results. The linked comparison classifies each difference and
preserves the complete diagnostics, corpus and canonical hashes.

The original 130-case Python pilot cohort totals **11.965s** across its five current registered
groups; Pester's current 34 cases total **31.522s**, and readable-wheel verification takes **7.317s**.
The corresponding sequential cohort is **50.803s**. These observations remain within the accepted
3.5 goals (Python <=15s, Pester <=40s, installed artifact <=15s, original cohort <=60s). The 244 newer
catalog/scope/process/aggregate cases are additional obligations, not a regression of that original
130-case cohort. Their 49.389s registered cost must stay visible.

| Target accepted at CI 5.1 | CI 5.1 historical evidence and follow-up assignment |
| --- | --- |
| Complete native implementation/infrastructure plus installed artifact <=90s | Current independent native groups 92.875s plus readable install 7.317s exceed this. Batch prototypes preserve all 408 named cases in 64.032s, or 71.349s including installation, but do not yet prove equivalent isolation, family reporting or failure continuation. |
| Feature-feedback <=300s on each adopted local OS | Accepted feedback objective with all mandatory meta-regression. The earlier Windows 4.5 sample was 249.550s; no new full feature-profile or Linux cost is certified at 5.1. |
| Complete successful prepared sequential full verification <=960s (16m) | Accepted optimization target, not the current result. The 19m39s failed shadow must improve by more than native batching alone; all required semantics, consumers, source guards and diagnostics remain. |
| Hosted prepared feature <=5m; integration/full critical path <=12m, excluding queue time | Accepted Phase 6 measurement targets. GitHub parallel placement and ADO's shared slot have different critical paths. These are not current hosted observations or permission to drop obligations to meet a number. |

The new full admission remains **9,600s**, including its 210s lifecycle reserves, with the separate
600s setup allowance. This local safety ceiling is not a normal feedback target and cannot be copied
into a hosted job whose admitted allocation does not fit. Existing hosted check names/55-minute
headroom remain unchanged. Phase 6 must size validated shards/job-level budgets and setup/publication
cost, accounting for ADO serialization and repeated setup. Parallelizing jobs does not reduce summed
agent minutes, and a free single-slot ADO plan does not realize GitHub's parallel wall time.

Measured unit totals explain the present bottlenecks: **429.528s conformance** and **604.332s
compatibility** dominate the replacement. Native batching opportunities total approximately **28.843s**,
including reduced guard/supervisor boundaries, not solely interpreter startup. The catalog/schema/
extraction checks cost 164.884/122.368/117.928s respectively; no safe deletion or core-runtime saving
has been demonstrated for them. Profile repeated CLI launches, immutable composition and fixture
setup before changing those contracts. Cache downloads alone cannot remove that execution work.

Initial capture/preflight/admission is approximately 10.013s (record-timestamp estimate). Six
preparation-process records sum to 4.553s. Another 35.311s of recorded time lies outside summed units,
including that initial preparation, guards and evidence work. The 2.227s observer tail includes
cleanup/finalization/exit rather than pure Markdown rendering. These components overlap: do not add
the initial 10.013s to the 35.311s remainder. Full publication admission verifies **555 listed files /
3,526,423 bytes**; this excludes cache payloads and peak external scratch/captured source.

The initial restricted-account bootstrap check separately records full Python environment
verification **8.665s** and PS cache verification **3.083s**, with no acquisition. The Python sample
exceeds the existing <=5s reuse-verification goal; repeat the complete check under the supported
execution account after the 5.4 bootstrap corrections. The narrower aggregate Python prerequisite
probe's 0.547s is not an equivalent replacement benchmark.

The 4.6 guardian enforces a **64 MiB combined stdout/stderr monitoring threshold**, with documented
possible polling overshoot. That is not implementation of the proposed per-stream/per-unit/per-run
artifact tree/file-count quotas below. Phase 6 publication/lifecycle work must reconcile those limits
explicitly. This sample fits the proposed publication totals; it does not prove all peak quotas.

Targets are accepted at CI 5.1 confirmation; successful exact-source remeasurement remains required
before 5.5/hosted adoption. If the targets cannot be met safely, investigate further or obtain an
explicit reviewed tradeoff; do not silently raise them or lower fixture counts/deadlines. Preserve
the dated measurements below. No executable budget, catalog or workflow is changed by this update.

**Support revision (2026-10-05):** D14 accepts retirement of 5.1 through the new CI Phase 2. The
three-runtime observations below remain dated evidence, not future required coverage. The Phase 2.5
refresh below supplies completed Python/PS7 costs and accepted replacement budget design candidates.
Former CI Phases 2-7 are now 3-8; platform phase numbering is unchanged.

## Measurement Basis And Limits

Current local full-release compatibility is measured once, sequentially through the existing
11-check registry. A disposable ignored observer wraps its handlers/subprocess calls to record
durations and byte/file counts; it does not change arguments, membership, comparisons or failures.
The runner performs its existing protection/cleanup. Additional tracked-file fingerprints compare
before/after the measurement. Reporting probes intentionally launch synthetic failures, whose
acceptance remains owned by the existing checks.

The follow-up ran the existing `fast` and `baseline` conformance profiles independently in
Python, PowerShell 7 and 5.1, compared full detailed JSON, and measured static policy/startup.
The initial full profile ran sequentially; lightweight version/import probes occurred during it.
Focused distribution/render diagnostics overlap the conformance follow-up, so those diagnostic
times and overlapping follow-up timings are resource-contended observations rather than isolated
throughput benchmarks. Corrected extraction waited for follow-up completion.
These are warm local observations, not statistical percentiles or hosted-agent throughput claims.
Setup includes version-qualified module imports, runtime launch and available published annotation
job evidence. No machine dependencies are upgraded/reinstalled to manufacture a cold setup result.
Clean installation, restore misses, Linux cold execution and native pilot costs remain explicit
acceptance work in 3.1/3.4/6.4. A second complete local run is unnecessary unless a failure or budget
uncertainty needs it.

Ignored evidence directory: `.tmp/ci-phase14-20261003/`. It contains timing events, complete legacy
reports/stdout/stderr, environment import metadata, policy timings and tracked-file fingerprints.
The observation scripts are disposable measurement aids, not proposed production runners or tests.
The observer did not capture individual child exit codes in its timing rows; check acceptance and
the detailed legacy report remain the authoritative result evidence.

The initial full profile failed at the extraction timeout after eight passes; it did not attempt
distribution/render. A diagnostic TEMP override placing extraction under the repository failed
two unrelated-directory/root-discovery fixtures because their ancestors now contained a project.
That is an invalid probe environment, not evidence of an extraction semantic regression. Preserve
both failed reports; corrected extraction uses the original system-temp placement. Out-of-tree fixture ownership
must be explicit even though published report artifacts remain confined under the run directory.

### Measured Results

| Existing conformance profile | Python outer seconds | PowerShell 7 outer seconds | Windows PowerShell 5.1 outer seconds | Result |
| --- | ---: | ---: | ---: | --- |
| `fast` (10 suites each) | 13.358 | 83.925 | 193.976 | All passed; complete detailed JSON equal across runtimes. |
| `baseline` (21 suites each) | 59.773 | 318.938 | 883.505 | All passed; complete detailed JSON equal across runtimes. |

Each profile/runtime was directly executed once. Some PowerShell observations overlap focused
diagnostics as disclosed above. Do not derive hosted throughput or per-suite time from these totals.
For example, 5.1 baseline reports 882.764 seconds internally versus 883.505 outer wall seconds.

| Compatibility check | Outer seconds | Result / origin |
| --- | ---: | --- |
| compatibility-reporting | 27.303 | Passed in original full profile. |
| conformance-reporting | 19.870 | Passed in original full profile. |
| framework-catalog | 517.288 | Passed in original full profile. |
| effective-schema | 381.118 | Passed in original full profile. |
| visualization | 94.194 | Passed in original full profile. |
| qa | 147.568 | Passed in original full profile. |
| root-discovery | 6.226 | Passed in original full profile. |
| artifact-lifecycle | 72.966 | Passed in original full profile. |
| framework-extraction | 360.012 | Timed out at the registered 360-second call limit; incomplete lower-bound sample. Corrected diagnostic is recorded separately below. |
| distribution-boundary | 141.489 | Not attempted by failed full profile; separately passed focused current check, contended. |
| render | 34.703 | Not attempted by failed full profile; separately passed focused current check, contended. |

The original `full-release` failed: **1,626.897 outer seconds**, **1,626.765 reported seconds**,
eight passes, extraction timeout and two unattempted checks. Both the runner's protected-output
guard and full tracked-file fingerprints showed no changes. The registered `local`, `pull-request`
and `distribution-boundary` profiles were not independently executed; any sum of their observed
members is a derived estimate, not a completed profile result. The six `local` members sum to
**1,187.340 seconds**. Substituting the completed focused checks gives derived totals of **1,644.818
seconds** for PR, **1,707.114** for distribution-boundary and **1,821.010** for full release. These
mix separate/contended observations and the diagnostic extraction allowance; they are planning
estimates, not newly passing whole-profile results or estimates at unchanged timeout settings.

The failed extraction retained its specifically owned system-temp copy. A recovery inspection found
no Python/PowerShell process with that copy as its current directory; a scoped removal returned
OS `Access denied`, and the tree remains. No ACLs were changed or unrelated August temporary trees
removed. Evidence records actual removal as false. Parent exit and an asserted cleanup flag cannot
prove successful child-tree termination or scratch removal; adopt D13 and verify these independently.
The invalid in-repository-TEMP diagnostic failed after 13.289 seconds and is excluded from budget
calculations. The corrected extraction diagnostic passed in **378.285 outer seconds** (**376.916
reported seconds**), using only an in-memory timeout increase from 360 to 900 seconds and unchanged
system-temp placement. It copied **302 files**, passed all **nine portable suites in three matching
runtimes**, and preserved canonical outputs. The observed uniquely owned temporary copy was absent
after exit, independently verifying successful scratch removal for this passing run. The old failed
run's retained copy remains a distinct cleanup finding. Production registry/workflows are unchanged.

Static checks all passed: Ruff formatting **0.109 seconds**, Ruff validation **0.096 seconds**,
annotation policy **0.380 seconds** (22 fixtures, 387 scanned files), PowerShell formatting
**9.868 seconds** (7) and **17.482 seconds** (5.1). Empty-process launch costs were **0.025 seconds**
(Python), **0.180 seconds** (7), **0.131 seconds** (5.1); these do not represent clean bootstrap.

Warm exact-module preflight, including host launch: PowerShell 7 **1.196 seconds**, 5.1
**1.719 seconds**; Pester 6.2.0, powershell-yaml 0.4.12 and PSScriptAnalyzer 1.25.0 imported in both.
An initial 5.1 import without an execution-policy launch option failed. The successful retry uses
the existing runner's process-scoped `-ExecutionPolicy Bypass`, not a machine policy change.
actionlint 1.7.12 checked current workflows successfully in **0.087 seconds**.
Python launch plus imports of PyYAML 6.0.3, pytest 9.1.1 and Pillow 12.3.0 passed in **0.295 seconds**.
One read-only normalization/hash pass over the generated Python QA inventory took **1.042 seconds**
for **35 files**. This is a representative normalization/I/O cost, not every comparison in the run.
Original compatibility tree hashing totaled **0.162 seconds** and detailed JSON write **0.000646
seconds**. An owned 100-file, 5,700,000-byte sample passed the existing cleanup helper and verified
removal in **1.248 seconds**. The failed full run retained output, so this sample does not claim its
whole-run cleanup succeeded. Generated check artifacts reached **5,549,073 bytes** for catalog and
**105 files** for QA; captured catalog stdout totaled **6,873,145 bytes**, effective-schema stdout
**4,344,458 bytes**. Limits below cover these observed sizes with margin, not unmeasured release scale.

Published baseline annotation evidence:
[GitHub run 37131982490](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37131982490),
executed `c5d1d78115ce2f3623aeef783ac20748a8a4ab2b`: success, job **17 seconds**,
Python setup **11 seconds**, checkout **2 seconds**. Step timestamps have one-second resolution;
the annotation step completing within one recorded second is not proof of zero execution cost.
No new full workflow dispatch, ADO pipeline or policy activation was performed for this checkpoint.

## Phase 2.5 Retained-Runtime Budget Refresh (2026-10-05)

Source snapshot `19b40d8`; ignored evidence `.tmp/ci-phase25-20261005/`. The existing full-release
runner completed all 11 checks in registry order with unchanged timeouts and baselines. Its detailed
report records **601.486 seconds**, before final cleanup/report publication. The disposable observer
records **629.131 seconds**, including its post-run tracked-file audit; that audit overhead is not
treated as production setup or cleanup. Actual scoped cleanup took **1.452 seconds**, PS7 discovery
**0.495 seconds**, and detailed report writing **0.000834 seconds**. Check timings below come from
completed handler calls; no timeout override or inferred missing pass is used.

This sequential warm local sample supersedes the dated three-runtime compatibility/extraction
deadline candidates for target planning. It does not measure cold restore, hosted throughput or a
statistical percentile. Individual local/PR/distribution profiles were not independently rerun here;
their check-time sums are derived estimates from this completed full run. Phase 2.4's independently
passing six-check local profile remains separate evidence. Runtime, setup and baseline observations
are recorded in the [retained coverage proof](ci-retained-coverage-proof.md).

Completed baseline outer times are Python **60.706 seconds**, primary PS7 **327.346**, and floor
PS7.4.0 **340.172**. Their complete semantic reports equal each other and the pre-retirement reports.
The whole-profile envelope candidates become Python **150 seconds** and common supported PS7
**690 seconds** under the same rounded two-times rule, superseding the former 120/660 values.
These are placement envelopes, not individual suite deadlines. Fast-profile throughput was not
remeasured; its unchanged subset and earlier acceptance do not supply new granular allocation data.
Warm launch/import and actual policy/formatting costs are recorded in the proof. Pester timings include
temporary Desktop rejection cases and must not set steady-state native group budgets before 2.6/3.3.

| Compatibility check | Completed seconds | Proposed whole-check deadline seconds |
| --- | ---: | ---: |
| compatibility-reporting | 23.952 | 120 |
| conformance-reporting | 12.544 | 120 |
| framework-catalog | 161.299 | 330 |
| effective-schema | 118.215 | 240 |
| visualization | 34.640 | 120 |
| qa | 41.188 | 120 |
| root-discovery | 3.874 | 120 |
| artifact-lifecycle | 30.491 | 120 |
| framework-extraction | 115.870 | 390 |
| distribution-boundary | 44.007 | 120 |
| render | 15.326 | 120 |

The existing `max(120, ceil(2*T/30)*30)` rule yields 240 seconds for extraction. Retain its existing
**360-second inner call limit**, with a **390-second whole-check candidate** to allow that inner
limit plus launch/verification headroom. The completed 2.4 extraction sample (116.501 seconds) and
this full-run sample both fit the unchanged limit. The former proposed 780-second inner/810-second
outer values are historical three-runtime candidates and are superseded. No executable registry
timeout changes in 2.5; whole deadlines remain future supervisor metadata at 4.3/4.4. Other candidates
use the reviewed whole-check rule; inner limits remain per-call caps and cannot be summed or mistaken
for whole-check guarantees. Supervisor adoption must reconcile both scopes explicitly.

| Existing profile | Whole-check deadline sum | With 210-second supervisor reserves | With provisional setup/publication/host allowances |
| --- | ---: | ---: | ---: |
| local | 1,050 | 1,260 | 2,160 |
| pull-request | 1,680 | 1,890 | 2,790 |
| distribution-boundary | 1,560 | 1,770 | 2,670 |
| full-release | 1,920 | 2,130 | 3,030 |

The last column adds the existing provisional 600-second cold setup, 180-second publication and
120-second host margin. All 11 compatibility checks can provisionally fit one 2,190-second unit
allocation window under the 55-minute target; this is admission arithmetic, not an implemented shard
or a cold-host measurement. The earlier illustrative two-shard placement is superseded for sizing;
final native/source/shard/gate ownership remains 4.1/4.4/5.1/6.1. Do not add native/meta-regression
groups to this allocation without measuring and admitting them separately.

The existing 900-second hosted compatibility job is still not certified adequate: one warm pass
does not reserve declared cold setup, publication or failure headroom. Phase 2.6 should review a
**55-minute retained compatibility job allowance** against fresh host/policy state, preserving its
check identity and all current profile membership. This document changes no workflow or ADO settings.
Per-suite conformance and native-test allocations remain independent; the 120-second granular-unit
minimum still makes 21 suites exceed one 2,190-second window per runtime until measured/reviewed
catalog allocation is adopted. A short aggregate baseline does not override that admission rule.

Completed check-end artifact inventories sum to **177 files / 10,066,857 bytes**; these are snapshots
of check artifacts, not a peak-live-tree measurement or all temporary fixture bytes. Largest captured
child stdout is **752,862 bytes**, total captured child stdout **7,500,947 bytes**, largest stderr
**1,433 bytes**, and the detailed compatibility report is **9,193 bytes**. Current artifact candidates
remain adequate for these observations; native/release growth still requires measurement. The observer
records durations/stream sizes but its child exit-code field is null because the current command
result uses `exit_code`, not `returncode`; the complete owning check/report is the result authority.
The observer adds start diagnostics to its stdout capture; the final producer summary retains contract 1.

Normal-exit cleanup succeeded and the newly observed external extraction directory was absent after
exit. The original Phase 1.4 timeout-retained directory remains a separate unresolved finding; no
process-tree cancellation, failure cleanup, installation isolation or hosted result is certified here.

## Phase 2.6 Published Job Allowances And Hosted Observation (2026-10-05)

CI 2.6 applies the reviewed 2.5 envelopes to the retained workflow while retiring the dedicated
Desktop job. Exact published-snapshot manual hosted acceptance passes at `8fb0576`; these values
are configuration ceilings, not observed duration or a new source of suite membership.

| Retained job | Execution envelope seconds | Existing provisional setup/reserves/publication/host allowance | Total seconds | Checkout timeout |
| --- | ---: | ---: | ---: | ---: |
| Python Validation | 150 | 1,110 | 1,260 | 25 minutes |
| PowerShell 7 Validation | 690 | 1,110 | 1,800 | 30 minutes |
| Project Compatibility, complete portfolio | 1,920 | 1,110 | 3,030 | 55 minutes |

The 1,110-second allowance is 600 setup + 210 termination/cleanup/finalization + 180 publication +
120 host margin. It reserves headroom; it does not claim the legacy runners implement the future
supervisor or that cold setup has been measured. The 5-minute workflow-policy/annotation jobs remain
unchanged. The old 15/20/15-minute runtime/compatibility job values and Phase 2.5 warning above are
historical inputs to this reconciliation. Inner registry timeouts, all selected cases and check
identities are unchanged. Native/catalog/bootstrap and ADO adoption remain their later phases.

Successful manual [run 37363093259](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37363093259)
passes all four retained CI jobs on `8fb0576`, plus matching standalone annotation push proof.
The producer summaries verify 21 Python suites, 21 PS7 suites and all 11 full-release checks.

| Job | Producer elapsed seconds | Workflow execution step seconds | Whole job seconds | Observed acquisition/setup steps |
| --- | ---: | ---: | ---: | --- |
| Python Validation | 71.747 | 72 | 88 | Python setup 10; requirements install 1. |
| PowerShell 7 Validation | 379.596 | 381 | 416 | Modules install 10; formatting check 13. |
| Project Compatibility | 675.590 | 677 | 999 | Python setup 48; Python requirements 4; PowerShell modules 13; Node setup 6; Mermaid install 239. |

Job timers include checkout and post-job work; producer elapsed is measured inside the runner.
Workflow timestamps have whole-second resolution, so a zero-second step is not proof of zero cost.
The jobs run concurrently; do not sum their durations as developer wall-clock feedback. Compatibility
starts 21 seconds after run creation, and its whole job lasts 16 minutes 39 seconds. These are
individual hosted samples, not percentiles, clean/offline-bootstrap proof or demonstrated cache gains.
Existing Python dependency caching remains enabled; no new cache or custom agent image is adopted.
The first failed run installs Mermaid in 200 seconds versus 239 in the successful replay, illustrating
setup variability without isolating a cache effect. Failed execution timing is not comparable complete
portfolio acceptance. Pinned bootstrap/cache placement at 3.1, duplicate/setup review at 5.1/5.5 and
cold/warm host proof at 6.1/6.5 retain ownership. Faster routine feedback remains a required objective.

## Selected Version Baselines

These exact selections are accepted design baselines. CI 3.1.2 implements the coordinated local
declarations/bootstrap, confirmed with fresh cross-OS hosted acceptance on 2026-10-05. See
[bootstrap commands and observations](CI/README.md). Local machine installations remain usable.

| Component | Selected baseline / evidence |
| --- | --- |
| Python | **3.14.5**, current local runtime and existing hosted pin. Python 3.10-compatible source syntax remains a separate existing policy, not a claim that this native development environment was tested on 3.10. |
| pytest | **9.1.1**, installed; no third-party plugins initially. Native pass/fail/skip/collection/XML proof belongs to 3.3/3.4. |
| Pester | **6.2.0**, exact version-qualified import in both hosts. Never use auto-selected inbox Pester 3.4.0 or floating latest. |
| PowerShell 7 | **7.6.6**, primary exact tested host. Supported framework remains 7.4+; a separate exact 7.4.x compatibility lane/version needs evaluation before claiming floor-runtime proof. |
| Windows PowerShell | Historical observation: **5.1.19041.7725 Desktop x64**. Retired target under D14; no future bootstrap, native group or profile obligation. Existing executable requirements are removed coherently in CI Phase 2. |
| PyYAML | **6.0.3**, installed runtime dependency; replace the floating minimum only through the coordinated declaration/extraction migration. |
| Ruff | **0.16.1**, already pinned; development/policy dependency. |
| powershell-yaml | **0.4.12**, version-qualified import passed on both hosts; portable PowerShell runtime dependency. |
| PSScriptAnalyzer | **1.25.0**, version-qualified import passed on both hosts; development/policy dependency. |
| Node | **24.15.0**, local runtime; replace hosted major-only `24` during bootstrap/host adoption. |
| npm | **11.12.1**, local package manager; lockfile/install compatibility must be verified in clean setup. |
| Mermaid CLI | **11.16.0**, already declared and locally installed. |
| Puppeteer | **25.3.0**, already declared and resolved inside the local Mermaid CLI dependency tree. |
| Chrome for Testing | **150.0.7871.24**, resolved by installed Puppeteer; verify actual binary/cache/platform availability. Chrome/headless-shell are separate artifacts; do not float to a system browser. |
| actionlint | **1.7.12**, installed and current checksum-pinned Linux workflow version. Approved archive checksums for every adopted OS/architecture are required in bootstrap. |
| Pillow | **12.3.0**, locally installed; development/media dependency for required synthetic image tests. Portable framework consumers do not require it. |

pytest transitive development lock candidates are the observed `iniconfig 2.3.0`, `packaging 26.2`,
`pluggy 1.6.0`, `Pygments 2.21.0`, and Windows-only `colorama 0.4.6`. Installed pip is **26.2**;
pin it for the adopted development bootstrap after clean resolution, rather than treating whichever
pip a venv seeds as approved. Package metadata confirms pytest/Pillow require Python 3.10+, while
the selected development interpreter is 3.14.5. Different future interpreter lanes need their own
marker-aware lock evaluation, not blindly copied 3.14 transitive pins.

Direct Node version declarations alone do not lock Mermaid/Puppeteer transitive packages. Adopt an
owned `Tools/CI/Node/package.json` and committed npm lockfile using these direct versions; verify
the resolved Puppeteer/browser pair. Keep `requirements-node.txt` as the reviewed human/bootstrap
direct-version input with a consistency check, not a second competing independently edited graph.
The lockfile is generated and checked from that input. Do not install tools globally in hosted CI.

## Portable Versus Development Dependencies

The 3.1.2 declaration layout retains existing portable filenames so extraction remains bounded:

| File / surface | Proposed ownership |
| --- | --- |
| `requirements-python.txt` | Portable Python runtime: exact PyYAML; no pytest, Ruff or Pillow. |
| `requirements-python-dev.txt` | Include portable runtime plus exact pytest, Ruff and evaluated marker-aware transitive pins. |
| `requirements-python-media.txt` | Exact Pillow; installed for required synthetic-media native groups. |
| `requirements-powershell.txt` | Portable runtime: `powershell-yaml 0.4.12`, using a reviewed name/version grammar. |
| `requirements-powershell-dev.txt` | Include portable runtime plus `Pester 6.2.0` and `PSScriptAnalyzer 1.25.0`. |
| `Tools/CI/Data/runtime-versions.json` | Exact adopted interpreter/tool versions, supported host constraints and archive/checksum references; points to package declarations instead of repeating package membership. |
| `Tools/CI/Node/` | Owned rendering package manifest/lock, installed only for declared render obligations. |

PowerShell requirements use two whitespace-separated fields, module name and exact version; optional
comments and a confined `-r <relative-file>` include grammar apply to development lists. Unknown
syntax, duplicate conflicting versions, include cycles, escaping paths or floating constraints fail.
CI 3.1.2 replaces the Save-Module workflow loops with a repository-owned exact installer and updates
environment helpers/regressions together, using `Save-Module -RequiredVersion` and version-qualified
imports. Name-only/floating declarations are rejected rather than accidentally installed as module names.

Python includes must be confined and the supported pip grammar explicit. Evaluate wheel availability
and verified hashes for adopted Windows/Linux platforms during clean bootstrap; a full hash lock
must contain every platform/marker dependency it claims. Do not invent hashes or assert a complete
lock from a global `pip list` observation.

Extraction currently copies the two existing runtime declarations, `pyproject.toml`, Framework,
Runtime and Conformance. Existing shared suites require neither pytest/Pester nor Ruff/PSScriptAnalyzer;
the inspected runtime/conformance tree contains no imports of those development tools. Keep native
tests/CI/media/render assets outside extraction. Update portable requirement parsing/validation
where needed, then prove a clean neutral extraction with runtime-only dependencies and the current
nine portable suites. Copying Ruff config does not make Ruff a runtime dependency.

EPUB/image tests become **required PR implementation coverage**, per maintainer instruction on
2026-10-03. Use synthetic owned EPUBs/tiny images, deterministic fixtures and bounded output. Include
Pillow in relevant Python test setup; unsupported or missing required native dependencies fail
preflight, not silently skip. Test PowerShell counterparts in their supported Windows hosts. No
local copyrighted EPUB/artwork directory is a CI prerequisite. Actual operations/assertions are
implemented and compared in the native pilot/integration phases, not claimed from package discovery.

## Budget Rules And Hosted Constraints

The rules/reserves below remain applicable. The original Phase 1.4 numerical compatibility/extraction
and baseline candidates are dated design evidence, superseded by the Phase 2.5 refresh above.

For a measured unit with local warm time `T`, propose outer deadline
`max(120, ceil(2*T/30)*30)` seconds. It covers startup, every nested subprocess, comparisons and
artifact verification. This two-times allowance is an initial design margin, not a measured p95.
Use the larger observed supported-runtime time for a common deadline, or explicit variant values.
Existing inner subprocess/parser/browser limits remain independently enforced.

Proposed whole-check deadlines from completed samples: reporting **120 seconds** each, catalog
**1,050**, effective-schema **780**, Visualization **210**, QA **300**, root-discovery **120**,
artifact-lifecycle **150**, distribution-boundary **300**, rendering **120**. Distribution/render
use the contended samples conservatively. These are design candidates, not changed registry values.
Whole baseline-profile envelope candidates are Python **120**, PowerShell 7 **660**; fast candidates
are **120**, **180**. The former 5.1 envelopes (baseline **1,770**, fast **390**) remain historical
planning values and are excluded from target profiles under D14. These are profile envelopes for
placement, not deadlines to duplicate on every individual suite. Actual per-suite metadata must be
measured and the admitted total reconciled before adopting the granular supervisor.

A timed-out sample is a lower bound, not a completed runtime measurement; it cannot justify a
two-times deadline calculated from the cutoff alone. Completed extraction supports a proposed
**780-second inner call limit** and **810-second whole-unit deadline**, adding 30 seconds beyond
the rounded two-times allowance for launch/verification. The diagnostic's 900 seconds is evidence
allowance, not the proposed adopted limit. Coordinate the registered 360-second inner limit and
new supervisor metadata in 4.3/4.4; increasing only an outer supervisor deadline cannot cure the
inner timeout. This original candidate was based on the nine-suite/three-runtime measurement;
D14 requires fresh two-runtime sizing at 2.5 before adoption. Preserve all nine suites and require
explicit regression/compatibility evidence; no registry value changes in this measurement pass.

Native test groups have no measurements yet. Their deadlines must be measured at 3.3/3.4 before
executable catalog acceptance. Baseline conformance totals can supply conservative bounds during
planning, but are not measured individual suite times. Tightening requires actual suite/group data;
do not label total profile time as every unit's normal cost.

Profile supervisor budgets must fit the sum of selected unit deadlines plus explicit **30-second
termination**, **60-second cleanup**, and **120-second finalization** reserves. Startup/setup is a
separate phase; admission checks cannot authorize a profile whose declared worst-case allocation
cannot fit its launch window. Reserve headroom before launching children. Budget exhaustion blocks
remaining units and fails the gate; it never converts them to optional skips.

Hosted placement must separately allow checkout/bootstrap/cache misses and **180 seconds for
publication**, followed by **120 seconds of host margin**. Cold bootstrap allowance is initially
**600 seconds**, explicitly provisional until measured on clean hosts. Prefer a **55-minute job
target**, below ADO's current free hosted **60-minute hard ceiling**. A shard's maximum admitted
unit-deadline sum is therefore `3300 - 600 - 210 - 180 - 120 = 2190 seconds` with these allowances.
If a single unit exceeds that window, split its architecture only after equivalent coverage proof
or select an explicitly reviewed suitable agent/entitlement; increasing YAML beyond the platform
ceiling does not fix it. Do not purchase capacity or configure agents in this checkpoint.

The existing compatibility job allows **900 seconds including setup**. Historical full release took
1,504.3 seconds before setup; current whole-check measurements make the mismatch actionable. Do not
fix it by dropping render, extraction, negative cases or required retained runtime variants. D14 is
a reviewed support retirement, not a timeout workaround or optional runtime skip. Phase 1.5 must map the
measured execution units into repository-owned shard profiles; YAML references those profiles.
Preserve `Project Compatibility` and other required-check identities through reviewed aggregation.
Legacy/replacement shadow overhead needs additional explicit capacity or separate runs, not hidden
inside the steady-state budget. Main/manual/full local execution spans all required shards.

The [Phase 1.5 host/integration design](ci-testing-host-integration-design.md#4-shards-budgets-and-aggregate-check-identity)
maps illustrative compatibility placement, explains the granular conformance minimum and proposed
strict shard/gate manifests, and assigns final sizing to 2.5/3.1/5.1. Its old-deadline examples are
not approved executable partitions or fresh two-runtime measurements. YAML cannot own that inventory.

ADO entitlement/agent readiness was inspected in 1.1: one free hosted slot, 1,800 minutes/month,
60-minute private job limit, and no registered self-hosted agents. Do not assume simultaneous shards;
one slot serializes jobs and affects total feedback latency. Recheck tenant settings before rollout.
The official [Microsoft-hosted agent documentation](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted)
confirms the free private-project duration/monthly limits. Schedule/event duplication and monthly
usage estimates belong to 1.5/7.3, using measured agent-minutes rather than local wall time alone.

## Isolation, Cache And Offline Execution

Local owned bootstrap state lives under ignored `.local/ci/`; ephemeral tests/reports stay in
`.tmp/ci/<run-id>/`. Hosted tool state uses the adapter's declared agent temporary/cache roots.
Do not alter AllUsers installations, user profiles or global npm tools. Reuse the user's current
machine setup for diagnosis, but certify gated execution against its declared isolated environment.

Use a per-interpreter venv; disable user-site imports and set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` unless
an explicitly pinned plugin is registered. Initial pytest needs no plugins for JUnit. Use
`-NoProfile`, a run-owned PowerShell module location and exact imports; retain necessary system
modules while excluding competing user/module roots. The historical process-scoped Desktop launch
handling is retired with that host at Phase 2; retained launchers still respect actual host policy.
Plugin isolation is supported by the
[pytest documentation](https://docs.pytest.org/en/stable/how-to/plugins.html).

Existing maintenance/Visualization cleanup scans cache directories recursively beneath its project
root, including ignored paths. Keep persistent bootstrap state outside the executed snapshot;
snapshot capture excludes `.local`, `.tmp`, venvs, module stores and Node/browser caches. Prove that
cleanup leaves shared bootstrap state intact in 3.1/4.6. A direct repository-root consumer run must
not accidentally traverse or remove a newly populated tool store. Do not change QA/Visualization
semantics to accommodate bootstrap without an explicit compatibility-reviewed change.

| Cache | Key / invalidation and hit verification |
| --- | --- |
| Python downloads | Cache schema, OS/architecture, exact Python, pip and complete declaration/hash-lock digests; recreate venv and verify installed versions/imports. Cache package payloads rather than moving a venv between agents. |
| PowerShell packages | Cache schema, OS/architecture, module declaration/include digests and checksum policy; verify module version/content and import in each exact host. No fallback to an older matching-name module. |
| Node packages | Cache schema, OS/architecture, exact Node/npm and package-lock digest; use `npm ci` in an owned prefix and verify the resolved dependency tree. Cache hits do not replace installation integrity checks. |
| Browser binaries | OS/architecture, exact Puppeteer/browser revision and download integrity; verify executable existence/version and headless smoke render. Distinguish Chrome from headless-shell. |
| actionlint/runtime archives | Exact version, platform/architecture and approved checksum; validate archive before extraction/use. |

Set `PUPPETEER_CACHE_DIR` explicitly for bootstrap and execution. Puppeteer documents this setting;
its default home cache cannot be assumed present on a new agent.
[Puppeteer configuration](https://pptr.dev/api/puppeteer.configuration).
Cache restore keys may reuse package-download stores, but no broad restore may certify installed
runtime/module/browser state. Corrupt/incomplete hits invalidate and fail preflight or trigger an
explicit bootstrap repair; test invocation never repairs by downloading dependencies.

After successful bootstrap, standard implementation/conformance/compatibility execution must use
the available tools/fixtures without external package downloads. Local loopback browser automation
is permitted. Network/API policy checks declare their separate needs; no credentials are embedded
in cache keys, fixtures or reports. Prove package-cache miss/hit and offline test execution in 3.1;
the installed-machine measurements here do not certify cold/offline reproducibility.

## Artifact Limits, Retention And Missing Tools

Proposed starting limits: **16 MiB per stdout/stderr stream**, **64 MiB per unit artifact tree**,
**256 MiB per run**, **10,000 files per run**. Evidence measurements must fit these with margin;
native pilots/release fixtures can revise them through the decision record. Continue draining
streams safely on overflow; retain available bytes/truncation metadata, fail the evidence contract
and terminate only the owned offending tree when safe execution requires it. Human excerpts remain
20 lines/4,096 UTF-8 bytes. Limits never justify silently losing later failure records.

Clean automatic fixtures/process scratch after each unit; retain reports until publication completes.
Local successful evidence: **7 days**; failed/cancelled evidence: **14 days** or explicitly kept.
Deletion is explicit owned retention cleanup, never automatic deletion of arbitrary `.tmp` trees.
GitHub artifact proposal: **14 days**; ADO uses the existing **30-day run retention** until host
design reviews actual artifact retention/permissions. Do not promise local evidence URLs survive
that policy or change tenant retention from this document. Cache lifetime is separate from reports.

Required missing/wrong/unimportable tools, an unavailable browser, conflicting versions, corrupted
caches or unfulfilled OS/host requirements produce actionable preflight errors and block their
units. Independent available units continue. Full fallback cannot remove those obligations; no
installation during tests, silent dependency floating, or success based on `Get-Module -ListAvailable`
alone. Clean-host archive availability and permission limits remain rollout evidence gates.

## Acceptance And Remaining Evidence

Phase 1.4 acceptance covers measured costs, exact candidate baselines, dependency separation, conservative
budget allocation, cache isolation and report limits. Native group budgets, complete transitive/hash
locks, lower supported PowerShell-floor proof, cold/offline setup and hosted throughput are explicitly
pending the implementation/host checkpoints above. These pending proofs do not authorize a new green
pipeline, retire current coverage or change required checks. Confirmation closes this design
checkpoint on 2026-10-05 with final local measurements and their limitations recorded. Adoption,
two-runtime remeasurement at 2.5 and later execution proofs remain required before changing gates.

Documentation verification for the original 2026-10-03 measurement pass: all **47 relative links**
across its five affected documents resolve;
annotation validation passes **22 fixtures / 387 files**; `git diff --check` passes. Final tracked
fingerprints differ only for the four intentionally edited existing documents; the new design is
untracked pending confirmation. Canonical/executable/dependency/workflow tracked files are unchanged.
