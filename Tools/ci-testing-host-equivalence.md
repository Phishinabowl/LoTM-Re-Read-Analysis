# Hosted Equivalence And Cost Qualification

## Status And Scope

Phase 6.5 starts from confirmed Phase 6.4 closeout `2f150d6`. The
[modernization plan](ci-testing-modernization-plan.md#phase-65-host-equivalence-and-policy-adoption-review)
owns acceptance. GitHub PR 3 and Azure PR 19 remain paused; no required check, policy, event,
suite membership, conformance fixture or canonical content is changed by this first increment.
The Python patch checkpoint is confirmed and dual-published as `b07f942`. The checkout-byte correction
and first collection-role optimization are subsequently confirmed and dual-published as `87fd18e`.
Corrected build inputs match published bytes on both hosts/OSs, both reduced aggregates preserve
460 cases, and current-source failure publication is independently verified. The maintainer confirms
these two qualified checkpoints and their evidence on 2026-10-07; wider optimization/equivalence/
policy-adoption gates remain open.

## Python Patch Candidate

The reviewed candidate is **CPython 3.14.8**, the current stable 3.14 maintenance/security release
reported by the [official release page](https://www.python.org/downloads/release/python-3148/)
(release date September 30, 2026). Its notes include SSL, archive extraction, decompression,
credential-scheme handling and bundled-library corrections. This is a patch checkpoint within
the already accepted Python 3.14+ eligibility, not a 3.15 migration or a free-threaded lane.

The official Windows install manager verifies its release index signature and extracts the exact
candidate with `py install --target=.local/ci-tools/python-3.14.8 3.14.8`. This creates no global
registration or shortcuts and preserves the existing 3.14.5 installation. The isolated Linux
candidate uses the existing standalone-runtime approach, now release `20261003`:

- Archive: `cpython-3.14.8+20261003-x86_64-unknown-linux-gnu-install_only.tar.gz`.
- Publisher: [Astral Python standalone release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261003).
- Verified SHA256: `371b6c281bbb09b29279e9e3a2996bab4ae2ea03cca52bf869f8bd89286b0ae8`.
- New owner: `/home/matt/lotm-ci-workspaces/phase-6.5/python-3.14.8`; no existing owner is replaced.

The live Actions Python registry contains stable, ordinary x64 3.14.8 payloads for Windows and
Ubuntu 24.04. Registry presence is acquisition eligibility, not hosted execution proof.
The candidate diff updates both runtime/lock interpreter labels and every GitHub/Azure workflow
pin together. Existing package versions, wheel URLs/digests, `Requires-Python >=3.14`, py310 source
syntax policy, package 0.1.0 and PowerShell/Pester versions remain unchanged. Runtime identity
changes invalidate version-specific Python environments and hosted payload keys automatically;
PowerShell dependency receipts retain their unchanged graph identity.

The native adapter's old hard-coded `(3, 14, 5)` probe is replaced by the authoritative
`Data/runtime-versions.json` pin. Two real integration cases prove accepted-version execution and
nonzero prerequisite rejection of a mismatched interpreter, with no invented test counts.
These belong to the existing registered native-results group; no new suite or pressure family is added.

## Local Evidence

| Check | Windows | Linux |
| --- | --- | --- |
| Fresh development/media environment with locked dependencies | Passed, 23.997s | Passed, 134.491s |
| Complete existing Python implementation suite before adapter correction | 574 passed, 91.22s | 574 passed, 82.52s |
| Native adapter group after correction, including two new integration cases | 35 passed, 4.45s | 35 passed, 6.40s |
| Verified wheel build with unchanged build pins | Passed, 18.970s | Passed, 127.192s |
| Outside-checkout installed consumer, 28 wheel members / 10 checks | Passed, 7.393s | Passed, 25.486s |
| Existing Pester portfolio through candidate controller | 60 passed, 28.171s | 58 portable cases passed, 30.268s |
| Existing language-neutral baseline fixtures through Python | 21 suites passed, 64.733s | 21 suites passed, 87.417s |

Linux explicitly excludes the Windows-only two-case image group; it is covered in the Windows run.
These are qualification samples, not new whole-profile timing baselines. Linux environments/builds
were prepared on the Windows-mounted checkout; their setup timings cannot establish native Linux
hosted performance. Existing 3.14.5 environments and all dated evidence remain available.
Linux Pester's initial missing `/usr/bin/pwsh` and omitted owned-module-root launches failed honestly
before cases were credited; correction uses the existing WSL PowerShell/module receipts and
process-local paths, without another runtime/module installation. Original diagnostics remain retained.

Ruff and GitHub actionlint pass. Evidence, exact candidate registry metadata, native XML, environment
receipts and installed-consumer records are retained under ignored `.tmp/ci-phase65`.
All 21 baseline suites pass per OS. Final static/diff review passes before publication; these
results do not substitute for cross-runtime parity or full project/host equivalence gates.

## Existing ADO Cost Decomposition

Run 54 is a functional, shared-slot full PR sample on the old baseline, not an uncontended or accepted
steady-state cost. Its eleven jobs sum to **3097.523s (51m38s)**. Independently summing native task
intervals gives:

| Task category | Occurrences | Summed seconds |
| --- | ---: | ---: |
| Exact Python acquisition | 11 | 564.930 |
| Worker environment preparation | 10 | 579.680 |
| Repository execution and aggregate collection | 10 | 1478.647 |
| Payload cache restoration | 10 | 129.330 |
| Payload post-job cache work | 10 | 15.130 |
| Checkout | 11 | 87.810 |

These categories do not exhaust job time; planning, wrappers, publication, initialization and
finalization remain separately accountable. Queue/allocation gaps and overlapping experiments must
not be mislabeled as execution or removed from wall-time reporting. The single hosted slot makes
summed repeated preparation consequential, even when GitHub runs independent jobs concurrently.
The audit source is retained `.tmp/ci-phase64/ado54-final-timeline.json`; its derived cost record is
`.tmp/ci-phase65/ado54-cost-audit.json`.

Every existing worker, including infrastructure and aggregate collection, currently requests the
complete build/render payload and actionlint. That confirmed duplication motivates the next
increment: derive preparation from the approved plan and assigned role, while preserving
preflight, necessary package/runtime payloads, source protection and complete admission. Test
isolation and full profile membership remain mandatory. ADO consolidation and narrower barriers
must preserve every approved unit exactly once and independent continuation after failure;
job reduction alone is not evidence of stronger or equivalent coverage.

## Hosted Patch Qualification At b07f942

Confirmation publishes all nineteen reviewed files as `b07f9428b43a11b2e71f645f31384e89475b3cc1`.
Local HEAD, upstream and both fetched remote branch tips agree, with a clean tree before the next
increment. Both PRs remain paused. Annotation run 37657000281 and the automatic core cache pilot
37657000390 pass. No automatic full PR run is triggered.

Complete cold and warm pilots pass on Windows and Linux:

- GitHub [cold 37657056851](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37657056851)
  and [warm 37657516265](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37657516265).
- Azure [cold 57](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=57)
  and [warm 58](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=58).

Independent receipt audit verifies all eight jobs' exact published source, 3.14.8 interpreters,
unchanged dependencies, 7.6.6 PowerShell, package 0.1.0 builds, pinned browser and real SVG labels,
and requested cache miss/hit disposition. Each OS's warm key equals its cold key. The 23 Python
runtime source-input hashes match across all eight jobs. Pilot artifacts retain build receipts/logs,
not downloadable wheel bytes; this audit does not claim independent rehashing of hosted wheel archives.

| Host / OS | Cold setup | Warm setup | Cold job | Warm job | Cold / warm Python acquisition |
| --- | ---: | ---: | ---: | ---: | ---: |
| GitHub / Windows | 82.045s | 55.035s | 162s | 84s | 59s / 0s |
| GitHub / Linux | 67.385s | 33.960s | 100s | 51s | 1s / 0s |
| Azure / Windows | 77.986s | 59.793s | 168.723s | 107.057s | 43.210s / 0.317s |
| Azure / Linux | 54.630s | 39.195s | 91.257s | 88.403s | 10.123s / 10.783s |

Helper setup excludes native cache transport and Python acquisition. Job intervals exclude waiting
for another allocation. These are single samples on distinct hosted allocations, not percentiles;
variation in agent interpreter availability cannot be attributed to the dependency payload cache.

The audit also detects **different Windows/Linux `pyproject.toml` and `LICENSE` input hashes**:
pilot checkouts inherit Windows CRLF conversion. Successful local wheel checks validate each
checkout's own bytes, so green jobs alone do not prove cross-host build-input equivalence.
The prepared correction applies the existing shadow-worker `core.autocrlf=false` process setting
before checkout in both pilots. Existing synthetic real-Git regression covers that setting; corrected
hosted pilot input comparison remains required. Original pilot outcomes remain honest dependency/
build-execution proof, not final package-input equivalence or whole-profile acceptance.

Evidence is retained under `.tmp/ci-phase65`: original cold/warm artifacts, native task timelines,
`patch-pilot-audit.json` and `patch-timing-audit.json`. Python 3.14.5 rollback remains available.

## Prepared Collection-Role Optimization

The aggregate worker now requests a distinct `collection` payload containing only runtime Python
dependencies (`pip` and PyYAML). It neither acquires PowerShell/actionlint/Node nor builds the wheel
or prepares/qualifies rendering. Cache identity distinguishes this role from `complete` and `core`.
Execution workers keep complete preparation unchanged in this increment.

Both host workers explicitly propagate their assigned shard during preparation. A missing shard
denotes collection, not a smaller test selection. Before execution/collection, the transport requires
a successful receipt with the expected role and exact execution commit; execution additionally
requires the original successful build and PowerShell receipts. Collection still admits every
approved shard exactly once with existing provenance, manifest, XML, cleanup and failure checks.
No catalog IDs, suite membership, unit deadlines, check names or policy conditions change.

Final focused bootstrap/scope regression contains **128 cases per OS**, covering role-separated keys,
forbidden collection tool acquisition, assigned-shard propagation and wrong-role/foreign-source
receipt rejection. Fresh production collection bootstraps pass in private owners on both OSs:
Windows 12.457s, Linux 85.850s on the Windows-mounted checkout. Both install only pip/PyYAML and
produce no build/render/Node or PowerShell receipt. These setup samples are not hosted performance proof.

The final real Windows infrastructure shard passes all five checks and **460 native cases** in
96.837s. The runtime-only collector admits its complete bundle in **4.562s**, preserving those same
460 cases and verified source protection/cleanup. An initial accidental use of the bare candidate
controller fails on missing YAML without crediting coverage; the verified runtime controller succeeds.
A Linux attempt to admit that local Windows worktree bundle correctly rejects its different snapshot
digest: mounted Unix worktree mode capture differs from Windows index mode capture. That experiment
does not establish cross-OS local-worktree interchangeability or justify relaxing provenance.
Current hosted aggregate placement remains Windows; Linux reduced preparation and focused tests
are qualified, while full Linux collection would require its own coherent source/manifest proof.

These eight implementation/test/workflow files plus the two evidence/plan updates are uncommitted
pending confirmation. Publication must then prove corrected pilot build-input hashes and the
reduced aggregate's ordinary success/failure publication on both hosts. Further execution-role
preparation, ADO consolidation, barriers and runtime acquisition remain explicit later increments.

## Published Collection And Checkout Qualification

The maintainer confirms the ten-file follow-up, published as
`87fd18e6c4a3548871ba10fe6be9d3263c5abe32`. All four local/upstream/remote branch references agree,
with a clean tree before this evidence update. Both PRs remain paused. These experiments are exact
manual branch snapshots, not fresh PR merge/target equivalence.

Corrected complete pilots pass on GitHub
[37661226324](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37661226324) and Azure
[59](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=59),
on Windows and Linux. Independent comparison against the exact published GitHub file bytes verifies
all four jobs' `pyproject.toml` and `LICENSE` hashes. Exact 3.14.8 dependency/bootstrap/package build
and real render qualification pass; no rollback to 3.14.5 is required for this patch checkpoint.
The previous cold/warm cache proof remains retained; the byte correction does not change dependency
pins or cache-hit verification. Final whole-profile equivalence and policy adoption remain separate.

Bounded infrastructure profiles pass on GitHub
[37661228573](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37661228573) and Azure
[60](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=60).
Each preserves five approved checks and **460 passing native cases**, with complete 67-file manifest
validation, unchanged sources and verified cleanup. Aggregate artifacts contain only runtime
bootstrap/pilot receipts; no PowerShell, Node, wheel-build or render receipt is present. Azure's 460
server case identities/outcomes match original XML exactly; its one **4196-byte** combined report
matches the admitted artifact. GitHub's admitted report is **2042 bytes**, with the actual artifact link.

| Host / role | Preparation | Whole job |
| --- | ---: | ---: |
| GitHub execution, complete payload | 67.297s | 262s |
| GitHub aggregate, runtime-only payload | 7.041s | 74s |
| Azure execution, complete payload | 76.741s | 268.113s |
| Azure aggregate, runtime-only payload | 7.485s | 63.630s |

These same-source role samples show removal of unused aggregate provisioning. Different jobs have
different work and allocations; they are not controlled whole-pipeline speedup percentages or
accepted final latency baselines. Preparation excludes native transport/acquisition. Azure run 60
shares the slot with pilot 59: queue-to-finish is 12m14s, while start-to-finish is 9m22s; neither is
an uncontended native/full feedback benchmark. Execution jobs still prepare the complete payload.

Existing bounded failure controls are replayed at the corrected source on GitHub
[37662167069](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37662167069) and Azure
[61](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=61).
Both remain intentionally failed after assertion failures, an owned child timeout, missing-result
admission and deliberate publication loss. Original execution exits, complete manifests, source
protection, cleanup and failure excerpts are independently verified. Azure stores exactly three
failed native cases (pytest/Pester/custom), with identities/outcomes and nonempty error messages
matching originals. Its four diagnostic Markdown attachments match admitted bytes exactly; missing
coverage produces no invented case. These probe jobs verify current-source failure transport and
runtime behavior; they do not run the production reduced aggregate or substitute for portfolio coverage.

Original artifacts, server bytes and native timing records remain under ignored `.tmp/ci-phase65`
and `.tmp/ci-phase64/ado60-server` / `ado61-server`. Wider execution-role preparation, ADO cohort
consolidation, narrower barriers, acquisition warnings/credentials, PR/event equivalence, final
timing review and policy adoption remain open. No check name, policy, selection mode or timing goal
is relaxed by this increment. The local default/editor selection is not silently changed: use the
verified 3.14.8 environment from its bootstrap receipt; existing 3.14.5 installations remain retained.

## Execution Preparation And Read-Only Azure Placement Proposal

The maintainer confirms publication of this increment on 2026-10-07. It is dual-published as
`6b8452c18fe922a352c7314b32c61bda96ae45f0`; HEAD, upstream and both remote branch references agree.
Preparation now derives from adapters in the approved repository catalog and assigned shard:

| Role | Required payload | Current assignment |
| --- | --- | --- |
| `core` | Python development/media dependencies and PowerShell development modules | Implementation, conformance, parity and media shards |
| `build` | Core payload plus the installed-package wheel build | Native policy/package shard |
| `complete` | Core, wheel build, owned Node/browser/render payload and real renderer qualification | Project compatibility; unknown adapters conservatively retain this role |
| `collection` | Runtime Python, pip and PyYAML only | Aggregate admission and publication |

The plan emits the role map into host context; workers recompute it before execution and reject
transport downgrades. Unspecified legacy execution retains complete setup. Cache identities separate
all four roles. Both pilot parameter lists accept `build` for bounded hosted qualification.
Test/profile membership, isolation, original shard IDs, runtime versions, OS placement, timeout
reserves and result admission remain unchanged. Python implementation shards retain PowerShell and
media dependencies because their implementation tests exercise those helpers.

Final bootstrap/scope regression passes 143 cases per OS: Windows 32.12s and WSL 39.51s.
Ruff and actionlint pass. Fresh production recipes in private copied-source owners prove:

| Local recipe | Windows setup | WSL setup |
| --- | ---: | ---: |
| Core, without build/render receipts | 42.723s | 157.169s |
| Build, package 0.1.0 wheel without render receipts | 55.206s | 290.372s |

These are local acquisition/environment measurements, not hosted speedup claims. WSL owners sit
on the Windows-mounted filesystem. The first Windows build attempt encountered sandbox network
restrictions; the authorized network retry passes in the same inspected owner, with failed logs
retained. Python remains exactly 3.14.8 and PowerShell 7.6.6.
The real Windows `ci-infrastructure` profile using the core receipt's interpreter/modules passes
all five checks and 475 cases in 108.998s, with canonical/source protection and cleanup verified.
The extra 15 cases relative to run 60 are preparation/placement regression, not added semantic
conformance families. Original finalized evidence remains under ignored `.tmp/ci-phase65`.

`ado_shadow.py placement <approved-profile>` provides a deterministic, read-only capacity proposal.
It does not alter execution matrices. Full/PR profiles now propose eight execution cohorts plus Plan
and Aggregate. The initial nine-job proposal is superseded by the allowance correction below:
ten physical jobs versus eleven today, preserving all nine logical shards.
Only shards with the same OS and prerequisite signature may share a cohort. Every original shard
budget/reserve remains included. Each child retains its 600-second snapshot/setup allowance;
180 seconds transport and 120 seconds publication/wrapper remain allocated per cohort. Admission
stays within 55 minutes. The proposed shared Windows core cohort contains infrastructure and the
small PowerShell conformance tail; media remains separate. Python conformance remains on Linux.
The two Linux shards cannot fit together
under the retained admission ceiling. Infrastructure-only remains three physical jobs.

No cohort is adopted, and no job-count reduction is credited as measured performance improvement.
Before activation, qualify shared preparation, independent continuation/cancellation, per-shard
finalized bundles, partial-failure diagnostics, artifact routing, exact aggregate coverage and
catalog-ordered report sections. Keep individual shard execution and the complete-preparation
baseline available as rollback. The bounded hosted preparation proof below qualifies this increment;
full/event/policy qualification remains open and both PRs remain paused.

### Hosted Preparation Qualification At 6b8452c

Both bounded `ci-infrastructure` runs pass five checks and 475 cases at the exact published source:
[GitHub 37682136133](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37682136133)
and [Azure 62](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=62).
Their native case identities match the local core reference exactly. Both original 67-file finalized
manifests verify, with source protection and cleanup preserved. Workers receive the catalog role map
and actually provision `core`; aggregates provision `collection`. GitHub's current-attempt artifact
link verifies, and Azure's server stores precisely the 475 original passing cases in test run 42.
Azure stores one 4,203-byte Markdown report matching admitted artifact bytes exactly.

| Bounded job | Preparation seconds | Whole job seconds |
| --- | ---: | ---: |
| GitHub core execution | 23.186 | 183.000 |
| GitHub collection | 7.142 | 74.000 |
| Azure core execution | 25.123 | 246.370 |
| Azure collection | 7.781 | 60.140 |

Earlier complete-prepared infrastructure samples measured 67.297s on GitHub and 76.741s on Azure.
The present receipts prove removal of build/render work with 15 additional preparation/placement
regressions retained; these are measured samples rather than a controlled total-pipeline speedup
percentage. Azure 62 takes 9m52.679s queue-to-finish and 9m44.497s start-to-finish, sharing its hosted
slot with cold pilot 63. Queue/wave waits do not become test execution time or an accepted full-run
performance baseline.

Build-only cold/warm qualification passes on both hosts and OSs:
[GitHub cold 37682147008](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37682147008),
[GitHub warm 37682390304](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37682390304),
[Azure cold 63](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=63)
and [Azure warm 64](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=64).

| Build recipe | Cold setup seconds | Warm setup seconds |
| --- | ---: | ---: |
| GitHub Windows | 35.082 | 20.764 |
| GitHub Linux | 29.637 | 12.023 |
| Azure Windows | 50.759 | 20.990 |
| Azure Linux | 31.644 | 17.880 |

All eight jobs retain Python 3.14.8, PowerShell 7.6.6 and package 0.1.0. Each warm receipt proves
an exact hit on its corresponding cold key; no floating/fallback runtime is used. Published LICENSE
and pyproject input hashes match across all builds, with clean source labels. Build-only receipts
contain bootstrap/build steps and no Node/render qualification. Pilot artifacts retain build receipts,
not the wheel archives themselves; this is not an independent hosted wheel-byte comparison.
The push-triggered [core pilot 37682073311](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37682073311)
also passes both OSs without build/render inputs, as does the separate annotation check.

Original receipts, aggregate/shard artifacts, Azure server bytes and timing audits remain in ignored
`.tmp/ci-phase65` and `.tmp/ci-phase64/ado62-server`. This is manual branch preparation qualification,
not full conformance/compatibility portfolio or fresh PR/event proof. Installed-package execution
under the derived build role remains part of subsequent broader worker qualification. No cohort,
required-check change, selective execution or policy adoption is activated. GitHub PR 3 remains
closed and Azure PR 19 abandoned. Existing failure/cancellation contracts, complete-preparation
rollback and timing goals remain intact; acquisition warnings and narrower barriers remain open.

### Cohort Executor Backend Review Checkpoint

The maintainer confirms the hosted preparation evidence update, dual-published as `b592236` on
2026-10-07, with four-reference parity verified. The next backend increment is locally prepared
and remains uncommitted pending review; no Azure YAML, policy, PR state or active matrix changes.

`ado_cohort.py` recomputes approved placement and source/OS/role admission, then delegates each
original shard to `run_ci.py` in an independently owned child. Shared preparation may cover a
higher role but cannot downgrade the shard's requirements. Existing single-worker admission is
factored into the same argument builder; its default execution and publication paths remain intact.
Children receive an explicit environment without host credentials or arbitrary project injection.
Parent cancellation uses the qualified process supervisor, stops later launches and returns 130.
Test failure, crash, corrupt evidence, exit mismatch and owned timeout retain failure status while
later independent children continue. A child cannot launch unless its complete original allowance
fits; later blocked/cancelled work produces no invented passing coverage.

Every admitted shard retains its original finalized manifest, JSON/XML, failure diagnostics and
private publication receipt. Cohort transport stages exactly one original bundle per admitted
shard plus complete bounded supervisor captures, never the captured source trees. Shard receipts
do not upload native test cases; aggregate-only publication remains authoritative. Experimental
receipts explicitly record `adopted: false` and reject reuse of an existing owner.

Review exposed a missing term in the preliminary packing calculation: `run_ci` admits each shard
with its declared budget **plus 600 seconds**, including snapshot/setup. The corrected proposal
preserves 600 seconds for every child, rather than treating all setup headroom as shared. Full/PR
placement therefore proposes eight execution cohorts plus Plan/Aggregate, or **11 → 10 jobs**.
The shared infrastructure/PowerShell-tail cohort reserves 1,170 shard seconds, 1,200 child setup
seconds and 300 transport/publication/wrapper seconds: 2,670 seconds, rounded up to 45 minutes.
The media shard no longer fits that cohort within the unchanged 55-minute admission ceiling.
This correction changes only the read-only proposal; no hosted runtime limit was shortened.

Broader focused catalog, scope, reporting and cohort regression passes **321 cases per OS**:
Windows 63.80s and WSL 105.50s. The 25 new cohort cases are registered in the existing CI scope
group, preserving logical suite IDs and its 120-second unit deadline. Real owned-child fixtures
prove continuation and exact failed/successful bundle admission; a readiness-based live cancellation
fixture proves child cleanup and stops later work. Ruff and diff checks pass. The real Windows
`ci-infrastructure` reference passes five checks and **500 cases in 108.597s**, with source protection,
cleanup and finalized publication verified. Its evidence is retained under ignored
`.tmp/ci-phase65/cohort-backend-reference`; this is local runner/registration proof, not an executed
production cohort or an adopted hosted grouping. No timing goal is relaxed.
The final admission guard rechecks the full child allowance after preflight and never clips its
lease to remaining cohort time. All 25 cohort cases pass again after that guard: Windows 7.87s /
WSL 45.50s, including initial/preflight budget refusal without launching a child.

Next, wire a manual opt-in Azure experiment while keeping ordinary shard placement available.
Qualify shared setup once, cohort artifact routing, exact collector/receipt inventory, partial
failures and recovery, aggregate-only native cases, combined report links/order, and sequential
friendly cohort job titles. Run the actual approved shared cohort and compare original shard
identities/outcomes and timings before normal placement can change. Reopen the same PRs only for
the later fresh event/policy gate. Retain individual workers and complete preparation for rollback.

### Manual Azure Wiring Review Checkpoint

The maintainer confirms the nine-file backend checkpoint, dual-published as
`11651feb93e8a6ac8e5c3aca7fe4a01a0726687f` on 2026-10-07, with four-reference parity verified.
The next wiring increment is locally prepared and remains uncommitted pending confirmation.

Pipeline 3 gains an explicit `placement` parameter:

| Mode | Execution and acceptance boundary |
| --- | --- |
| `shards` (default) | Existing individual workers and aggregate; ordinary/PR behavior retained |
| `cohorts` | Manual full-profile experiment: eight execution cohorts plus Plan/Aggregate; every original logical shard remains required |
| `cohort-smoke` | Manual bounded qualification of the one approved shared independent cohort, using the full-verification source catalog; no full-profile aggregate |

Both experimental modes require a Manual event and cannot mix with publication probes. Smoke
requires the full-verification source catalog, captures its exact approved placement/roles and
executes only the infrastructure/PowerShell-tail cohort. The two actual logical shards retain
independent owned children and reports. Its combined Markdown explicitly marks partial qualification.
No smoke-native Test Results upload is performed: native cases remain aggregate-only, and smoke
cannot satisfy full-profile collection/publication. A green smoke run is not full-portfolio proof.

Full experiments receive deterministic, sequential friendly cohort job labels in execution-wave
order. Shared preparation uses a catalog-derived member with the cohort's maximum required role;
it is provisioned once. Cohort artifacts retain the original per-shard bundles, diagnostics and
setup receipts. Full collection recomputes captured placement and requires every cohort receipt
and original shard exactly once. Missing/duplicate/foreign inventory, changed budgets, inconsistent
exit/status, bad cleanup, escaped ownership and lost manifests are rejected before collection.
Genuine failed and passing finalized shards remain independently admissible, preserving their
original outcomes. Combined aggregate sections retain logical shard order and link to the owning
cohort artifact; ordinary shard links remain unchanged.

The opt-in worker downloads only the current run's cohort artifacts; the aggregate chooses the
matching cohort/shard artifact pattern. The unchanged task's documented
[artifact matching contract](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/download-pipeline-artifact-v2?view=azure-pipelines)
supports the bounded pattern and per-artifact download directories. No credentials are propagated
to cohort children, no pipeline/policy/schedule is activated, and both PRs stay paused.

Final focused cohort/scope/report regression passes **262 cases per OS**: Windows 61.91s and
WSL 162.92s. These include real clean-checkout planning CLIs for both new modes, original
failed/passing receipt admission, deliberate collector mutations, artifact routes and partial-report
submission. Bare `-I -S` diagnostics preserve a setup failure without site packages; that probe
identified and fixed the cohort CLI's missing explicit colocated import path. Original policy
PR and default shard paths remain covered. Ruff, Azure YAML parsing, existing actionlint and diff
checks pass. Local YAML parsing is not Azure template compilation or live UI acceptance.

After publication, preview the actual Azure templates, then run bounded `cohort-smoke` qualification
at the exact published source before a full experiment. Verify shared setup occurs once, both
original shard identities/outcomes, complete failure diagnostics, exact stored Markdown and timings.
Keep deliberate failure/recovery and full cohort aggregate/native/report equality as distinct
remaining gates. No hosted runs are queued by this local increment; normal placement and timing
goals remain unchanged. Rollback is the default `shards` mode and retained individual worker template.

### Bounded Hosted Cohort Qualification At 8138f9d

The maintainer confirms opt-in publication and bounded hosted qualification on 2026-10-07.
The eleven-file checkpoint is dual-published as `8138f9d40940c745c4e123dd1ad5ebc8286a45d9`,
with HEAD/upstream/GitHub/Azure parity verified. The separate annotation push check passes.
Azure template previews succeed for all three modes at that exact source, without agent allocation.
The expanded smoke graph contains Plan and the two execution-wave definitions, with no Aggregate
or native upload tasks; runtime planning sets the empty dependent count to zero, skipping allocation.
Both full graphs retain Aggregate and its three fatal-on-missing native upload tasks.

[Azure smoke run 65](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=65)
passes Plan and one shared execution job, titled
`CI Check_01_CI_infrastructure_PowerShell_7_conformance_batch_2_of_2`. The captured source,
manual placement, approved shard inventory and role map match independently recomputed catalogs.
Both owned child processes exit successfully, and their finalized manifests, original reports,
source protection and cleanup verify. No captured source tree or duplicate shard bundle enters
the cohort transport artifact.

| Original logical shard | Checks | Recorded pytest cases | Execution seconds | Manifest files |
| --- | ---: | ---: | ---: | ---: |
| CI infrastructure | 4 | 489 | 150.793 | 62 |
| PowerShell conformance, batch 2 | 3 | — | 53.723 | 28 |

The three conformance suites retain their original language-neutral/custom outcome contracts;
they are not converted to Pester or counted as pytest cases. Shared core preparation executes
exactly once in 24.027s, with an actual payload cache miss, Python 3.14.8 and PowerShell 7.6.6.
No wheel build, Node or rendering recipe is provisioned. The cohort executor takes 210.995s;
its whole agent job takes 317.627s. Plan takes 78.480s. Pipeline start-to-finish is 434.238s
(7m14.238s), and queue-to-finish is 442.913s (7m22.913s). These are bounded qualification costs,
not full-portfolio timings or a controlled comparison against earlier runs.

Repeated native Python acquisition remains visible: Plan's `UsePythonVersion` takes 45.220s and
the cohort worker's takes 46.143s. The acquisition/warning optimization gate remains open;
payload caching does not imply the interpreter acquisition is cached across fresh agents.

Azure stores exactly one 15,820-byte `ci-cohort-qualification-8e73bd64.md` attachment, identical
to the original staged Markdown. It explicitly marks partial qualification and includes both
original logical shard sections. Server test-run/case inventory is empty as designed: smoke is not
the full aggregate and does not upload native cases. API acceptance and exact-byte admission pass;
the maintainer's copied tenant report confirms the partial boundary and both result blocks.
The maintainer accepts this bounded evidence and requests collapsible coverage-detail lists
in the next increment. The copied text does not independently prove heading/table appearance;
the lengthy delegated-unit lists remain a readability improvement, not a coverage failure.

Original previews, timeline, cohort artifact and audit helpers remain under ignored `.tmp/ci-phase65`,
with exact stored server bytes in `.tmp/ci-phase64/ado65-server`. Default shard placement remains
active. GitHub PR 3 is still closed and Azure PR 19 abandoned; no policy/check/schedule changed.
Deliberate cohort failure/recovery, full cohort collector/native/report equality, full timings,
interpreter acquisition, fresh PR/event equivalence and adoption remain separate open gates.

## Remaining Qualification And Rollback

### Coverage Detail Readability Follow-Up

The maintainer requests collapsible coverage-detail lists after accepting run 65's bounded
qualification. The next local increment wraps nonempty unselected coverage in a closed details
section with a check count, retaining every original ID and selection reason. Required reviews
and failure diagnostics stay visible. Empty coverage does not add an empty section; original
report evidence is not mutated. Hosted rendering of this follow-up remains unqualified until
the increment is confirmed and included in a subsequent bounded publication experiment.
Focused report/cohort regressions pass all 146 cases on Windows (25.74s) and Linux (122.07s),
including preserved reasons, visible reviews/failures, balanced closed sections and unchanged
input evidence. Ruff checks and formatting pass. No new hosted run is queued for this local pass.

### Bounded Cohort Failure And Recovery Follow-Up

The next local increment adds an explicit `cohort_qualification: launch-failure` manual parameter,
defaulting to `none`. Admission requires Azure Manual, `cohort-smoke`, the full-verification source
catalog and no PR replay; ordinary shards, full cohorts, policy PRs, unknown faults and mixed
publication probes cannot admit it. The first original child exits with code 2 before producing
results. The executor retains its bounded process capture and verified cleanup, records missing
coverage honestly, continues the later original shard and returns failure. No canonical source
or fixture is corrupted, no native cases are invented or uploaded, and original child deadlines
and preparation roles remain unchanged. The summary labels the deliberate fault and exposes the
missing shard's process status/exit and admission diagnostic alongside actual later results.

After confirmation/publication, preview and queue a bounded smoke at the exact new source with
the fault enabled. Require an intentionally failed execution job/run, a real passing second shard,
retained first-child exit/capture/cleanup, no first-shard finalized results, one exact-byte partial
summary and zero server native cases. Then queue matching smoke at that same source with the fault
disabled; require both original shards and manifests, successful execution and complete bounded
report admission. Observe collapsible coverage and visible diagnostics in the tenant report.
Keep PRs paused and ordinary `shards` placement active. Neither probe closes full cohort collection,
native-report equality, portfolio timing, interpreter acquisition or final event/policy adoption.

The nine-file local increment, including the previously reviewed report cleanup, passes all 275
focused report/cohort/scope cases on Windows (63.56s) and Linux (163.62s). Ruff checks/formatting
and diff checks pass. The new cases exercise a real isolated exit-2 child and later-shard execution,
fault admission bounds, missing-result human diagnostics and qualification receipt mismatch.
A local readability preview generated from run 65's original reports preserves both coverage lists
under closed details sections in original shard order. Changes remain uncommitted; no hosted probe
or runtime/policy adoption is claimed from this local proof.

### Hosted Failure/Recovery Publication At 21eacc0

The maintainer confirms the nine-file increment and bounded hosted qualification on 2026-10-07.
It is dual-published as `21eacc0ef1226735bfc88517a70ea1987d2a706c`; HEAD/upstream/GitHub/Azure
parity and clean status verify. GitHub annotation run `37698920575` passes. Azure read-only previews
compile both exact-source smoke modes with Plan and execution waves, no full Aggregate/native uploads,
and the intended fault/default context. GitHub PR 3 remains closed and Azure PR 19 abandoned.

[Azure deliberate failure run 66](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=66)
finishes failed as required. Independent artifact audit verifies the first child exits with code 2,
retains its deliberate-fault output and verified cleanup, and produces no finalized shard bundle.
Complete admission rejects the missing evidence. The second original shard nevertheless passes all
three PowerShell conformance checks in 52.260s, with its original 28-file manifest, report, source
protection and verified cleanup intact. Cohort execution takes 56.545s; shared core preparation runs
once in 30.448s with an actual cache miss. No native case is invented or uploaded.

Azure stores one 8,531-byte partial report, identical to the admitted summary. It exposes first-child
exit/missing-coverage diagnostics and actual later results, with one closed 74-check coverage section.
The maintainer confirms in the tenant UI that coverage starts collapsed, expands correctly, and the
deliberate failure diagnostic remains visible. Plan takes 78.633s and the worker 126.383s;
pipeline duration is 222.546s, queue-to-finish 229.637s (3m49.637s). The two native Python acquisition
tasks measure 48.907s and 0.300s; these samples do not establish a guaranteed acquisition cost.

[Azure matching recovery run 67](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=67)
passes at the same commit with the fault absent. Independent audit admits both original shard
receipts and manifests: four infrastructure checks with 502/502 pytest cases in 138.721s (62 files),
plus three PowerShell conformance checks in 43.793s (28 files). Both owned processes exit zero;
source protection, containment and cleanup verify. Cohort execution is 188.813s and shared core
preparation executes once in 24.924s with another actual cache miss. Native server inventory remains
empty, as required for smoke qualification. Azure stores one 15,922-byte report, identical to the
admitted summary, with both coverage lists in closed expandable sections and original shard order.
The tenant interaction is confirmed through run 66; run 67's bytes and structure are API-verified.

Plan takes 35.337s and the worker 255.080s; pipeline duration is 312.363s, queue-to-finish 317.867s
(5m17.867s). The two Python acquisition tasks take 0.307s and 0.310s. Preserve these measured
differences from earlier runs without attributing them to a new acquisition implementation or
guaranteeing future warm behavior. Run 66's cache post-job log records no save activity, and run 67
reports another miss for the same payload key. Recovery is passing cold-payload evidence, not a
claimed warm-payload acceptance.

The bounded failure/continuation, same-source recovery and collapsible-report gates are now proved.
Original previews, timelines and cohort artifacts remain under ignored `.tmp/ci-phase65`, with
exact server attachments under `.tmp/ci-phase64/ado66-server` and `ado67-server`; the independent
failure/recovery and timing audit helpers retain the compared source and inventories. Neither
bounded run establishes full-profile coverage or closes the remaining 6.5 timing, full-collector,
native-report equality, interpreter acquisition or fresh event/policy adoption gates. No full run
is queued, ordinary shard placement remains active, and both PRs remain paused.

### Same-Source Infrastructure Aggregate Comparison At 2af597d

The maintainer confirms the failure/recovery evidence, dual-published as
`2af597dae315bb8505ad4ecdde6d0b155eb6fd13` on 2026-10-07, with HEAD/upstream/GitHub/Azure
parity and clean status verified. GitHub annotation run `37702182378` passes. Continue 6.5 with
the existing complete `ci-infrastructure` profile to qualify real cohort collection and native
publication at bounded cost. Its five Python implementation checks occupy one original logical
shard, `infrastructure-0`, and three allocated jobs in either mode. Empty dependent execution is
condition-skipped. This is not a complete LoTM portfolio or a job-consolidation timing benchmark.

Read-only Azure previews compile ordinary and cohort graphs at the same exact source. Both retain
aggregate-only native upload tasks with fatal missing/publication failures, the appropriate original
shard/cohort download patterns and fault controls disabled. No runtime, policy, check or default
placement changes accompany the experiment; GitHub PR 3 stays closed and Azure PR 19 abandoned.

[Azure ordinary reference run 68](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=68)
passes all five checks and publishes exactly 537 passed cases in one pytest test run (server run 44).
Independent audit reconciles every published identity/outcome with original admitted native XML;
staged XML bytes match the finalized aggregate sources. The aggregate manifest has 67 files;
source protection and verified cleanup remain intact. Azure stores one exact-byte 4,201-byte combined
report with the original shard in order and the correct ordinary artifact reference.

Core preparation is an actual warm payload hit at 11.773s. Collection uses only Python runtime
dependencies (pip/PyYAML), with an actual cold collection payload and setup at 7.981s; original
collection takes 1.908s. No PowerShell, wheel build, Node or renderer is provisioned in Aggregate.
Plan takes 80.017s, worker 248.153s, Aggregate 106.853s; pipeline duration is 484.913s and
queue-to-finish 491.786s (8m11.786s). Three native Python acquisition tasks cost 45.693s, 44.163s
and 44.283s, confirming that the near-instant sample from run 67 is not a dependable acquisition
baseline. Keep that warning/authentication/acquisition optimization gate open.

[Azure matching cohort run 69](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=69)
passes at the same source with fault controls disabled. Independent cohort admission verifies the
complete original logical shard, its owned process exit zero, verified cleanup and preserved budget.
The original worker and both collected aggregates have the same five ordered unit outcomes and
537 native case identities/outcomes. Each transport preserves its own original native XML
byte-for-byte into collection; cross-run duration fields are not required to match. Azure publishes
exactly those 537 passed cases in one pytest test run (server run 46), with no shard-level duplicate
upload. The 67-file aggregate manifest verifies, as do source protection and cleanup. One stored
4,187-byte combined report matches admitted bytes, retains original shard order and correctly
references `ci-shadow-cohort-0` rather than the ordinary shard artifact.

Core preparation is an actual warm hit at 12.339s; the isolated original execution takes about
151.60s and its cohort wrapper about 156.14s. Collection is an actual warm hit with setup at
7.422s and original collection at 1.754s. Both aggregates retain the collection-only Python
environment and no PowerShell/build/Node/render preparation.

| Same-source mode | Plan seconds | Worker seconds | Aggregate seconds | Pipeline seconds | Queue-to-finish seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary shards, run 68 | 80.017 | 248.153 | 106.853 | 484.913 | 491.786 |
| Cohorts, run 69 | 80.580 | 215.903 | 69.103 | 409.049 | 414.198 |

Run 69's three native Python acquisition steps take 43.253s, 0.290s and 0.330s. Its faster wall
time (6m54.198s) is not credited to job consolidation: this profile uses three jobs in both modes,
and host acquisition variability contributes substantially. Native execution is about 149.97s in
the ordinary reference versus 151.60s in the cohort child. No timing goal or setup ceiling is waived.

The bounded complete infrastructure profile now proves actual cohort collection, aggregate-only
pytest publication, original XML preservation and correct ordered report routing. Original previews,
worker/aggregate artifacts, timelines and comparison helpers remain under ignored `.tmp/ci-phase65`,
with exact server cases/attachments under `.tmp/ci-phase64/ado68-server` and `ado69-server`.
Full multi-cohort/multi-runtime coverage, nonempty dependency waves, portfolio timings, pinned
interpreter acquisition and fresh event/policy adoption remain separate open gates. Both PRs stay
paused and ordinary placement remains the active default; no full portfolio run is queued.

The patch and aggregate-preparation checkpoints are confirmed on 2026-10-07. Continue with deliberate
manual optimization runs while PRs remain paused; branch qualification is not fresh PR merge proof.
The adopted exact Python baseline is now 3.14.8, with retained 3.14.5 rollback evidence. Setup failure
cannot silently select another version.

Review the two `UsePythonVersion@0` warnings during the acquisition increment. Its documented
`githubToken` input concerns registry download limits, while exact-pin acquisition must survive
host-image patch replacement. No personal credential is added to YAML, no existing authentication
is repurposed, and no host-managed secret is created by this checkpoint. A repository-owned
hash-pinned acquisition alternative must be reviewed and measured before replacing native setup.

The infrastructure comparison evidence is confirmed and dual-published as `8ada9f7` on 2026-10-07.
The next [pinned Python acquisition proposal](ci-python-acquisition-design.md) is a design-review
checkpoint. Run 68's slow worker log and read-only upstream source show substantial Windows
installation/pip-refresh work after the archive transfer; the exact-pin warning is emitted even
when the interpreter is already cached. The proposal separates warning/authentication disposition
from a completed-interpreter cache experiment, retains native rollback and requires trusted seal,
fixed-prefix, cold/warm, corruption/recovery and original test-publication proof before adoption.
No installer is executed locally, no runtime archive is downloaded, no secret is created and no
new hosted run is queued by this source/proposal pass. Both PRs remain paused; 6.5 stays open.

The maintainer approves the acquisition pilot design, dual-published as `571a488` on 2026-10-07
with HEAD/upstream/GitHub/Azure parity. Its first local implementation adds a read-only PS7 admission
library and registers its Pester fixtures in the existing dependency group. Exact cache identities,
external-seal inventory verification, conservative link/owner/type checks and probe-checked receipts
do not execute or restore cached runtimes; handoff and save flags remain false. The original native
adapter admits all 52 registered dependency cases per OS (47 new, five existing), zero skips/errors;
Windows takes 6.152s and Linux 16.516s. Catalog/clean-private planning proof passes 89 cases per OS,
and formatter/lint/annotation/diff checks pass. Runtime archive inspection, mutable-file/fixed-prefix
qualification, repeatable real seals, hosted cache restoration and failure/recovery measurements
remain open. No workflow, timeout, profile/shard membership, secret or machine runtime changes.
The implementation/evidence is uncommitted; see the acquisition design for exact local boundaries.

That admission increment is subsequently confirmed and dual-published as `8719f8d`, with all four
branch refs matching. Read-only downloaded-byte inspection verifies both exact upstream asset sizes
and SHA-256 values. Windows supplies an installer rather than a completed runtime; Linux supplies a
prefix-bound tree with 5,996 bytecode files and eight relative links. Neither installer/executable is
run. Repeated hosted capture and an explicit generated-file/pip/alias/mode contract remain required
before trusted seals or restoration are adopted. Detailed findings are in the acquisition design;
this inspection queues no hosted jobs and changes no default, machine installation or paused PR.

The next reviewed candidate prepares a separate manual-only raw-capture YAML and guarded PS7
collector: two independent jobs per OS, exact authoritative Python pin, no cache save/restore and
no full portfolio. Raw retention omits nothing; Unix modes and the exact Windows native alias are
inspection evidence only. The strict admission path remains unchanged. All 63 registered dependency
cases pass per OS, zero skips/errors; YAML structure parses locally. Temporary definition creation,
Azure preview and actual native provenance/repeated-capture comparison await publication approval.
The acquisition design records the exact bounds and intentionally unverified receipt fields.

The capture candidate is confirmed and dual-published as `5ab075c`; temporary Azure pipeline 4 is
registered without automatic execution and its preview matches the four bounded manual jobs.
Run 70 uses that exact source. Native setup succeeds, but three capture jobs reject an unqualified
native-output handoff before inventory; failure receipts publish correctly. The run is canceled,
with its fourth job canceled and no admitted capture/seal/cache operations. A scoped correction
names/qualifies the producer output and adds early unresolved-output rejection plus platform-aware
exact-prefix comparison. All 69 registered native cases pass per OS. This new diff is uncommitted;
retry qualification and actual repeated inventories remain open. See the acquisition design for
source references, run timing and precise outcome disposition.

The handoff correction is subsequently confirmed/published as `b5378a1`, with four-ref parity.
The published-source preview passes and run 71 succeeds for all four capture jobs (4m07.377s
queue-to-finish). Independently recomputed inventory digests and source/contract checks pass.
Windows captures have 5,088 entries each with 408 differing pip-generated files; Linux has 9,789
entries each with 571 differing bytecode files. Raw trees are not repeatable trusted seals.
The first Windows job selects preinstalled Python from a newer image while the other three native
tasks download the inspected release; this is not a controlled same-image cold/cold Windows proof.
A documented in-memory projection retains identical entries per OS after source-backed-bytecode,
complete native-base-pip and exact alias normalization. No runtime is changed or restored by that
analysis. Candidate construction, execution, ensurepip/locked bootstrap, mode-aware external seals,
cold/warm/corruption/recovery and default adoption remain open. Three evidence docs are uncommitted;
see the acquisition design for full counts, timings, provenance limits and the proposed next gate.

The capture findings/design are confirmed and dual-published as `38fddb3`. A subsequent local
candidate builder now materializes only private fixture owners, preserves the native source and
retained source/ensurepip inputs, records omissions, normalizes the exact Windows alias and hashes
Linux file/directory/root modes under strict schema 3. Copy/source verification and incomplete
failure receipts pass; no candidate runtime is executed or restored. All 84 registered dependency
cases pass through native admission on both OSs with zero skips/errors. Actual capture-record
projections match per OS; Windows preserves 120 preexisting empty cache directories beyond the
exploratory projection. Hosted candidate execution, locked bootstrap, external seal/restore wiring,
corruption/recovery and benefit measurement remain open. Five files are uncommitted for review;
no new hosted jobs, defaults or PR state changes. Details are in the acquisition design.

The private builder is confirmed/published as `c743f42`. The next candidate adds a default-off mode
to pipeline 4 and a native-supervised verifier/probe/locked-bootstrap driver, retaining four bounded
manual jobs and uploading diagnostic receipts rather than runtime binaries. Complete mode-aware
payload checks and actual core-library ownership precede qualification; success cannot admit a
cache or fixed-prefix restore. The bootstrap's no-base-bytecode path is explicit/source-only and
ordinary behavior stays unchanged. All 53 focused pytest and 84 Pester cases pass per OS; real fresh
runtime-profile bootstrap succeeds locally on both OSs. The custom WSL static-SSL build is correctly
rejected by the Actions-specific file-backed-module probe; positive Linux candidate proof is hosted
and still open. Azure's candidate override preview passes without allocation. This increment is
confirmed and published as `b5d04bb`, with four-ref parity and a passing committed-source preview.
Run 72's first Windows copy passes base/core-library ownership and fresh locked bootstrap, but its
post-bootstrap inventory correctly rejects newly generated `Lib/__pycache__`. CPython ensurepip's
nested interpreter preserves isolation but drops `-B`; the no-bytecode environment is ignored under
isolation. Child cleanup is verified, qualification remains failed and no trust/save/handoff is
admitted. The remaining three jobs are cancelled; queue-to-finish is 3m06.900s. No Linux candidate
execution or repeated-copy success is claimed.

The scoped opt-in correction runs the retained bundled pip wheel directly under isolated `-B`,
then performs the existing locked install/check. Ordinary behavior remains unchanged. All 55 focused
pytest cases pass per OS, including the upstream nested-flag reproduction and actual fresh offline
bundled-wheel bootstrap. A complete private copy of the existing Windows runtime also passes all
three real owned children and fresh locked bootstrap (11.757s), with candidate/source fingerprints
unchanged and trust/restore/save/handoff withheld. This is local correction proof, not hosted Linux
or provider-repeatability evidence. The maintainer confirms and dual-publishes this correction as
`1f7b1b3`, with four-ref parity and passing committed-source preview.

Corrected manual run 73 succeeds in all four jobs at that exact commit, queue-to-finish 7m37.665s.
All copied bases and fresh environments pass real module/core-library ownership, locked pip 26.2/
PyYAML 6.0.3 and unchanged-payload/source verification; all twelve owned children exit zero with
verified cleanup. Windows independent inventories match completely. Linux execution also passes,
but repeatability is blocked by 3,029 mode differences only: image `20261004.327.1` preinstalls the
native tree at 0777, while image `20260927.320.1` downloads the same pinned release with 0644/0755.
Retained bytes, paths/types/links match. The independent seal audit explicitly exits 1 for that
Linux mismatch; pipeline success does not imply cache/trusted-seal/restore/handoff acceptance.

Read-only comparison against the rehashed pinned tar archive confirms all 3,029 downloaded modes
match release metadata. The next recommended design checkpoint reviews archive-derived canonical
permissions and fail-closed provenance/type/mode rules before changing normalization. Current native
mode preservation remains in force; no seal or cache backend is adopted. The maintainer confirms
that direction/outcome checkpoint, dual-published as `d9f7298` with four-ref parity.

The next concrete policy independently derives the complete retained reference from the pinned tar
bytes plus three exact installer-added aliases and removal of `setup.sh`. All 2,813 retained regular
file hashes match both real Linux captures. The 3,040-entry external reference reproduces the original
mode-aware digest; all 3,029 modes match the downloaded variant. The proposal accepts only exact
reference modes or observed 0777 with matching bytes/types/paths/links, reducing permissions only in
a fresh private owner. Root/source preservation, strict external reference identity, explicit Linux
v2 normalization, receipt stamping and failure/meta-regression gates precede hosted retry.

The concrete policy is confirmed and dual-published as `68470c2`, with four-ref parity. Its first
implementation checkpoint prepares the reproducible Python deriver, exact repository release
specification/full reference, LF byte-stability rule and strict PS7 admission reader. Both OSs
regenerate the same 703,313-byte reference and digest from the real pinned archive. Existing v1
builder/driver, production adapter and manual pipeline behavior remain unchanged.

All 69 focused Python and 105 registered Pester cases pass per OS with zero errors/skips. Final
Pester group costs are 11.082s Windows/20.528s Linux; the initial 71.420s WSL sample exposed redundant
per-row filesystem stats, removed without weakening actual owner or metadata validation. Tests retain
deadline/cancellation, typed identity, complete paths/links/modes, duplicate/malformed/corrupt inputs,
read-only derivation and fresh-owned-output refusal. No new group, deadline, host run or cache is added.

The maintainer confirms the reference foundation, published as `1e9dd30` with four-ref parity.
The next explicit Linux v2 builder/driver increment is implemented locally: exact external reference
matching, restricted permission reductions, private-only copying, source-root preservation and
schema-2 mode/reference provenance. The Python receiver independently binds external declarations
and typed inventory before any executable launch. Raw/Windows v1/ordinary defaults remain unchanged.

All 87 focused Python and 124 registered Pester cases pass per OS with zero errors/skips; final
Pester costs are 13.023s Windows/22.535s Linux. Actual Linux fixtures prove copying, reduction,
source/root preservation, cancellation/partial refusal and root-mutation detection; Windows cases
verify the host restriction. Real captured Linux inventories now normalize identically at 3,040
entries and the reviewed digest, reducing 3,029 modes/zero respectively. Their native root mode was
not captured, so that data-only comparison explicitly uses a synthetic root and does not close
actual hosted root/execution qualification.

The maintainer confirms this increment, dual-published as `f5705d3` with four-ref parity. The actual
committed-source preview passes. Manual run 74 succeeds in all four jobs at exact `f5705d3`, with
queue-to-finish 7m38.869s. All four older-image agents download the pinned provider release; Windows
v1 paired inventories match and Linux v2 paired inventories match the external mode-aware reference.
Real native Linux roots are 0777, copied as 0755 and verified unchanged in their original locations.
Retained modes already match the archive, so entry reductions are zero. All twelve owned children
exit zero with cleanup verified; copied bases and fresh locked environments pass actual module/core/
prefix ownership and unchanged-payload checks.

The independent full artifact audit exits zero, including reference stamps, complete inventory bytes/
modes, actual roots, reduction records, native source identity and no runtime-binary uploads. All final
PS source checks are corroborated. Fresh execution covers only downloaded retained modes; historical
run-73 captured projection plus synthetic real copy tests cover the all-0777 file variant, as explicitly
allowed by the bounded plan. Do not claim that variant was freshly scheduled or any owned cache hit.

The maintainer confirms this result checkpoint, published as `8652baa` with four-ref parity. The next
increment prepares a complete Windows external reference from the audited native pair, alongside the
existing archive-derived Linux reference, common strict platform reading and separate mode-aware
schema-2 cache-plan/staging-admission helpers. Exact provider archive/reference/inventory identity,
normalization and fixed prefix bind the cache key; current source revision is separate. A verified
staging hit cannot grant restoration, execution or handoff. No cache task, destination write or new
hosted run is introduced.

All 94 focused Python and 140 registered Pester cases pass per OS with zero errors/skips. Final group
costs are 13.951s Windows/25.874s Linux; plan keys and 742,725 Windows reference bytes reproduce
identically across metadata-test hosts. Tests exercise real staged fixtures, corrupt/missing/extra/
mode-altered bytes, metadata/key/schema/promoted-state refusal and bounded cancellation. Windows
reference provenance is qualified native output plus the independent service audit, not installed
bytes extracted from its installer archive. Linux derivation/proofs remain unchanged.

The maintainer confirms the ten-file checkpoint, published as `c9be93a` with four-ref parity.
Next qualify actual hosted prefix/absent-target
ownership, no-overwrite leases and complete copy/probe/receipt behavior. Current v1 cache scaffold
stays unadopted until lifecycle replacement coverage permits retirement; it cannot admit v2 plans.
Restore/save benefit, fault/recovery and ordinary handoffs remain open. See the acquisition design
for complete boundaries/rollback. Phase 6.5 and paused PRs remain unchanged; no new hosted run is queued.

The following private-copy increment adds fresh target/external receipt ownership, read-only exact
tools-root/prefix checks and nonexecuting immutable file/link/mode copying. Existing occupied or linked
owners are preserved; an incomplete lease/target cannot be reused. Private copying expressly refuses
the declared native owner. Cancellation/timeout/I/O failure and source mutation remain incomplete,
without execution/restoration/handoff/save promotion. Tests use only synthetic private fixtures on
Windows/WSL; no installed runtime, tool-cache registration or agent prefix is modified. The maintainer
confirms the five-file increment, published as `af91478` with four-ref parity. The actual guarded
hosted driver, fixed-prefix writes/probes, warm cache economics and
ordinary role/profile handoffs remain later qualification gates, not claims of this private proof.
Final registered Pester group results are 152/152 on each OS, zero errors/skips, in 14.699s Windows
and 25.370s Linux within the unchanged 120-second deadline. Twelve added cases cover private copying
and ownership/failure refusal; scoped static policy/22 fixtures, formatting and all 66 documentation
links pass. No Python implementation changes require repeating its prior focused verification.

The next eight-file increment implements a disconnected manual Azure restoration driver, fresh
version-level ownership lease, exact-prefix copying and an explicit restored Python qualification
entry. Full external seals precede executable launch and are rechecked after the existing bounded
base/environment probes and fresh locked bootstrap. Completed evidence requires all three child
exit/cleanup proofs, immutable payload and no premature cache/handoff/save promotion. Actual local
entry refuses on Windows/WSL before output creation; successful restoration tests use private
simulated roots and Python entry tests virtualize owner paths without launching an interpreter.
Real fixed-prefix execution/outer job cancellation/artifact behavior are not yet hosted proof.
No pipeline YAML/cache task, registration or ordinary handoff changes occur. This source checkpoint
awaits review; next wire a bounded opt-in manual pilot with explicit native route for occupied image
prefixes, then measure real restoration and cold/warm cost/fault/recovery. Phase 6.5 stays open.
Verification passes 103 focused pytest cases per OS (5.48s Windows/7.86s Linux) and 176 registered
Pester cases per OS (15.881s Windows/27.754s Linux), zero errors/skips. Ruff/PowerShell formatting,
five-file annotation policy/all 22 fixtures, 67 doc links and diff checks pass. These are local protocol/
ownership checks, not warm-cache performance or real fixed-prefix hosted proof.

After patch disposition, qualify role-specific preparation, ADO job consolidation and dependency
barriers separately. Measure cold/warm setup, actual workload, publication and queue time; compare
complete local/hosted portfolio identity and failure/cancellation behavior. Restore the same PRs
before fresh PR/event equivalence and policy adoption. Original checks remain until their accepted
replacement gate. The accepted 90-second native and 16-minute sequential goals are not relaxed.

Rollback is the retained 3.14.5 runtime/pin/lock/workflow baseline at `2f150d6`, plus its original
environment and hosted evidence. Restore the complete candidate pin increment together if hosted
qualification fails; retain failed candidate diagnostics and record its disposition. Do not downgrade
or remove machine runtimes, overwrite existing environment owners, or mix interpreter labels with
different authoritative pins.
