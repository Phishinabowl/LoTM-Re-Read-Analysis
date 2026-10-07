# CI 6.3 Native Azure Pipelines Shadow Adapter

**Status:** Initial adapter published as `0284a36`; pipeline 3 is created. The first hosted smoke
exposed an empty-wave condition defect, and concurrent GitHub qualification exposed shared output
capture corruption. Scoped corrections are locally verified and awaiting publication confirmation.
Actual complete hosted qualification remains open. Entry is confirmed 6.2 at `7cd016e`; no ADO PR
or framework-target policy has been created yet.
The [modernization plan](ci-testing-modernization-plan.md#phase-63-native-azure-pipelines-adapter)
owns acceptance. [Host integration design](ci-testing-host-integration-design.md) owns merge/event
boundaries; its initial inventories are historical, not a description of today's installed pipelines.

## Host Boundaries And Inspected State

The project `LoTM Inspired KM Platform` contains Azure Repos and Azure Pipelines. Its repository
stores the mirrored history. A pipeline definition selects YAML and a default branch; the YAML
allocates jobs to hosted agents. Each task provisions dependencies, invokes repository commands or
transfers artifacts. An agent is the temporary machine running a job, not a persistent development
environment. Locally the same catalog/profile executes without agent allocation or hosted transport.

Initial read-only Azure CLI inspection on 2026-10-07 confirmed project
`66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb`, repository
`657f741d-cf62-44d6-8b6c-08d93f471133`, existing pipeline 2 `LoTM CI Cache Pilot`, and hosted queue
39 / pool 9 `Azure Pipelines`. Framework-target policy inventory was empty. Authorized creation later
established pipeline 3 `LoTM Platform CI` on the modernization branch using that queue; exact template
preview and real planning/worker allocation are observed. The previously
inspected single shared private hosted slot serializes work; remaining monthly allowance is unknown.

Azure Repos PR validation is dispatched by a target-branch build policy, not YAML `pr:`. Proposed
pipeline `LoTM Platform CI` uses [.azuredevops/ci.yml](../.azuredevops/ci.yml) and the shared
[worker template](../.azuredevops/ci-worker.yml). Push and schedule triggers remain disabled.
Proposed framework-target validation is enabled, automatic, **optional/nonblocking**, with no path
filter, target-change revalidation and no independent merge authority. Do not enable required policy,
auto-complete, additional reviewer/security settings or schedules in this checkpoint.

GitHub remains the sole merge authority. The corresponding ADO PR is validation evidence only.
Record the exact optional policy settings and preserve the prior empty inventory. Policy/transport
interaction must be reviewed before enforcement at 6.5; no direct target push or permission bypass
is performed merely to manufacture that evidence. Normal publication remains `git push origin HEAD`.

## Repository Ownership And Execution

[ado_shadow.py](CI/ado_shadow.py) normalizes Azure metadata and logging commands, delegating to the
6.2-qualified [shared shadow executor](CI/github_shadow.py). Catalogs, scope resolution, process
supervision, parity and publication admission remain the same local authorities. Host-specific cache
namespaces and report host/run URL distinguish Azure from GitHub without changing suite membership.
Cache identity includes both adapter implementations; modified helper bytes invalidate prior payloads.

PR context requires the approved collection/project/repository and framework target, an active same-
repository PR, exact source/base/merge IDs from the fixed read-only PR API, and agreement with actual
policy variables. Actual checkout must equal the executed SHA; merge parents must match the immutable
source/target pair. A moving target tip is never substituted. API/build disagreement fails planning,
rather than assigning a green full-suite fallback to unknown execution provenance. Known manual
source without comparison evidence retains the existing full eligible policy fallback.

Manual profiles are allowlisted: `full-verification` (default), `pr-integration`, `ci-infrastructure`.
An explicit numeric `pr_number` supports source replay only when the queued exact source version
matches active PR metadata and the full `pr-integration` profile is requested. Policy PR builds force
`pr-integration` regardless of a manual profile parameter. No source checkout override or moving-ref
resolution is hidden inside the worker.

Planning provisions pinned Python 3.14.5 and a fresh verified runtime environment before importing
catalog dependencies. Workers use the verified development interpreter, complete immutable payload
and fresh environments; PowerShell 7.6.6/Pester 6.2.0 and exact tool receipts retain 6.1/6.2 ownership.
Checkout fetches complete history, persists no credentials and preserves unspecified Git text bytes
with process-scoped `core.autocrlf=false`. Only context discovery receives `System.AccessToken`, and
the API endpoint is fixed; the token is not forwarded to worker tests or written into artifacts.

The Azure matrix adapts approved catalog rows without adding membership. Wave order is deterministic;
aggregate order remains global catalog order. Independent failures do not suppress later independent
jobs or the dependent/collection attempts. Required missing/failed source evidence remains a failure.
Every row is admitted below 55 minutes; the initial Azure worker host ceiling is 55 minutes, with
tighter repository child deadlines unchanged, five-minute planning and two-minute cancellation grace.
The infrastructure profile has no dependent wave: a condition-skipped `NoWork` matrix marker avoids
an empty Azure matrix. It allocates no worker, executes no test and contributes no passing result.
The guard must use upstream planning output count, available before matrix expansion; matrix
variables are unavailable at job-condition evaluation. The initial matrix-variable guard incorrectly
allocated the marker. The corrected skip remains a real hosted retry gate.

Native Azure tasks provision Python, restore exact payload caches and transfer current-run pipeline
artifacts. Download patterns admit only shard artifacts, excluding planning diagnostics. Admitted
bundles retain original run directory names and verified manifests. A separate bounded transport
directory includes only admitted bundles and explicit setup/context/tool/failure diagnostics, not
captured private source workspaces. Ordinary failure publication does not override execution status.
Markdown is retained inside bundles; visible Markdown and Tests-tab wiring belong to 6.4.

## Qualification And Rollback

Local regression extends existing `ci-scope`, not a new duplicate harness. Coverage exercises foreign
destinations, missing/stale PR evidence, metadata/merge drift, unsupported events, complete real
multicommit Git scope, manual source replay/fallback, logging escape, matrix collision/order/deadlines,
empty-wave omission, credential/checkout YAML boundaries and complete clean-private-checkout planning
CLIs for both hosts. Focused scope/report/bootstrap tests and repository formatting/policy checks must
pass on Windows/Linux before publication. These checks do not prove Azure's template engine or agents.

Local results on 2026-10-07: the focused scope/report/bootstrap cohort passes **161 cases per OS**;
after the final empty-wave and host-label adjustments, all **87 scope cases** pass again on Windows
(25.06s) and Linux (12.35s). Ruff check/format, unchanged GitHub actionlint, annotation policy
(22/22 fixtures, 487 files, eight annotations) and `git diff --check` pass. No Pester implementation
or semantic fixture is changed; the existing PowerShell/reference evidence remains intact. Nine files
formed the initial review increment. These were local checks; subsequent hosted evidence follows.

### Initial Publication And Scoped Recovery

Initial adapter `0284a36334d0930ea4b9267132b24b25cc39c3ec` is published with verified GitHub/ADO parity.
Pipeline 3 was created without an initial automatic run; exact-source Azure template preview passes.
The REST preview rejects an explicitly submitted empty `pr_number` string; omitting the parameter
uses its accepted YAML default. No runtime change or false success is inferred from that request error.

[Smoke run 43](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=43)
executes exact source `0284a36`. Planning passes and records five infrastructure units and honest
full-policy fallback because the manual smoke has no explicit comparison base. Cold complete payload
provisioning passes in 322.290s. The real infrastructure shard passes **5/5** in 93.184s with admitted
publication hashes, source guard and verified cleanup. Its snapshot is
`beeb881683755c95199533c7f58996f6a5b03b7c43746661830a08f39c189b38`.
However, Azure evaluates job conditions before matrix variables exist: `NoWork` was allocated,
invalidating the intended empty-wave skip. The build was cancelled and is terminal `canceled`; no
complete aggregate or green smoke acceptance is credited. Downloaded shard evidence remains intact.

Concurrent [GitHub shadow 37581977348](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37581977348)
exposes corrupt formatter stdout JSON, despite formatter child exit zero. The native/policy shard
correctly remains failed; the original [reference CI 37581977060](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37581977060)
passes unchanged. The malformed raw stream and failure classification are retained. A bounded Windows
PowerShell JSON reproduction corrupts **8/10** streams under the original supervisor and **0/10**
after changing capture accounting from shared output cursor queries to physical file-size inspection.
Permanent regressions verify displaced cursor accounting and every byte of incremental native JSON
output. Capture thresholds, deadlines, cleanup and strict result parsing are retained.

The Azure correction guards the dependency wave using `Catalog.dependent_count`, not an unavailable
matrix variable. YAML regression also rejects duplicate keys instead of silently discarding conditions.
Final scoped scope/process/report tests pass **176 cases per OS** (37.24s Windows / 18.86s Linux).
Real owned-module Windows formatter recovery passes all 74 files with strict, complete JSON capture.
Ruff check/format and annotation policy (22/22 fixtures, 488 files, eight annotations) pass. These
corrections are uncommitted pending confirmation; real corrected Azure expansion/skip/collection,
complete PR scope and source/merge qualification still require hosted retry. Evidence is retained in
ignored `.tmp/ci-phase63`; no fixture, native Pester case or required coverage is retired.

After confirmed correction publication: preview and retry the existing named pipeline's
`ci-infrastructure` smoke, proving the empty dependent wave is actually skipped before allocation.
Record
actual queue, task/runtime/cache/transport results. Then create a validation-only ADO PR targeting the
framework branch and stage the optional build policy, preserving all settings and rollback IDs.
Qualify actual merge execution with complete `pr-integration` and explicit source provenance/replay;
audit run artifacts against exact catalog coverage and source/tree identities. Keep failed attempts
and missed coverage visible. PR drafts do not supply automatic policy-dispatch proof; inspect actual
dispatch rather than assuming it from successful PR creation.

Do not close 6.3 from local checks, small smoke coverage or a successful artifact upload. Actual
complete PR scope/coverage, coherent source/merge identities and host equivalence remain required.
ADO may serialize all allocations; report summed agent minutes and queue delay separately from
wall time. Final placement/cost adoption remains 6.5; controlled failure/publication tests remain 6.4.

Rollback disables only the newly introduced optional policy/pipeline dispatch, preserving cache pilot,
GitHub checks, catalogs, canonical sources and mirrored Git history. The ADO PR stays unmerged; no
resource deletion, independent merge or automatic target synchronization is implied.

Official references: [policy-driven PR builds](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#pr-triggers),
[build policies](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops),
[job/matrix ownership](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops),
[immutable PR merge metadata](https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-request?view=azure-devops-rest-7.1).
