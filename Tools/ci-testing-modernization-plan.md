# CI And Testing Modernization Implementation Plan

**Status:** Expanded documentation draft for maintainer review. No modernization implementation or
hosted rollout is complete. Creating this plan does not authorize its execution.

**Working branch:** `architecture/ci-testing-modernization`, created from
`architecture/framework-extraction-foundation` at `c4b7932`.

**Integration target:** A GitHub pull request into `architecture/framework-extraction-foundation`.
Merge only after the modernization acceptance gates pass; resume platform work there afterward.

## Purpose And Placement

Modernize repository-owned testing and CI before Platform Phase 4.2 adds more field and page-schema
contracts. The interlude follows the existing Phase 4.1 discovery work without claiming its pending
maintainer review is complete. CI closure and Phase 4.1 review are independent prerequisites for
Phase 4.2. Existing platform phase numbers and discovery finding IDs remain unchanged.

Support direct local execution, GitHub Actions, and Azure Pipelines through the same authoritative
catalogs, fixtures, profiles, runners, and result contracts. Publish concise Markdown summaries in
both hosts and native automated test results in Azure DevOps (ADO).

Use this plan with:

- [Platform Implementation Plan](../Framework/platform-implementation-plan.md) for sequencing.
- [Architecture](../ARCHITECTURE.md) for current component and runtime boundaries.
- [Testing Methodology](../Framework/testing_methodology.md) for cumulative coverage and retention.
- [Validation Run Reporting](../Framework/Contracts/validation-run-reporting.md) for existing reports.
- [Framework Improvement Lifecycle](../Framework/framework_improvement_lifecycle.md) for any
  numbered semantic/model version introduced by subsequent work.
- [Tooling Reference](TOOLING_REFERENCE.md) for implemented commands and output contracts.
- [Completed Tooling Plan](CI_implementation_plan.md) for the earlier foundation and dated evidence.
- [Platform Evolution](../Framework/platform_evolution.md) for confirmed closure history.

This plan owns modernization execution and acceptance. It is not a second executable test inventory
or a replacement for the testing methodology. Proposed paths and command surfaces below remain
design candidates until Phase 1 review; do not describe them as implemented.

## Operating Rules

- Work in focused increments. Leave edits uncommitted until explicit confirmation; publish through
  the agreed Git workflow. This first pass changes documentation only.
- Keep canonical LoTM pages, templates, Relationship Seeds, project data, QA behavior, and
  Visualization behavior unchanged. Generate test artifacts only in isolated owned destinations.
- Preserve authored prose independently from structured state. CI must not resolve Phase 4.1
  conflicts, select a future canonical storage layout, or promote discovery IDs into schema IDs.
- Preserve existing public conformance/compatibility entry points and detailed JSON contracts.
- Run legacy and replacement coverage together until equivalent or stronger coverage is evidenced.
  Retire coverage only through an explicit methodology decision and historical record.
- Keep EVR inspection read-only. Adapt portable patterns; do not copy its Exchange, DevMenu,
  corporate approval, annotation enforcement, or Windows-only assumptions into this platform.
- A phase checkbox means implemented, verified, documented, committed, and pushed unless it
  explicitly describes a design decision. All implementation items start unchecked.
- Use subphase checkpoints to record evidence and resolve blockers; they are not additional
  permission requests for work already authorized. Pause for maintainer review at major phase gates
  and when a material design, coverage, or publication decision is still unresolved.
- Do not turn this draft into authorization for external
  repository creation, remote configuration, pipeline activation, or branch-policy changes.

## Checked-Out Baseline And Known Gaps

The read-only assessment used LoTM `c4b7932` and EVR `3f36556`. Recheck versions, catalogs, Git state,
and host settings before implementation; these observations are not live tenant configuration.

| Surface | Confirmed baseline |
| --- | --- |
| Conformance | 21 paired suites; 10 in `fast`, all 21 in `baseline`; validated registry and discovery. |
| Compatibility | 11 checks; `local` has 6, `pull-request` 9, `distribution-boundary` 8, `full-release` 11. |
| Implementation frameworks | No repository pytest or Pester registration/configuration yet. |
| Static checks | Ruff with `E501`, parser/token-aware PowerShell formatting, actionlint, annotation policy with 22 fixtures. |
| Reporting | Detailed JSON and concise `validation-run-summary` v1; retained failure reports. |
| GitHub | PR, `main`, manual full CI; non-main push annotation workflow; no schedule. |
| ADO | Not established for this repository; organization/project/repository and policies need inspection. |

Current authorities are [suites.json](Conformance/suites.json),
[compatibility.json](Compatibility/compatibility.json),
[CI workflow](../.github/workflows/ci.yml), and
[annotation workflow](../.github/workflows/work-annotations.yml).

Confirmed gaps to address:

- Conformance has child isolation and aggregate failures but no per-suite timeout.
- Compatibility has subprocess timeouts but no total check deadline and stops at the first failure.
- Hosted baseline jobs do not compare all 21 runtime summaries; existing reporting and extraction
  checks compare narrower inventories.
- Earlier failed steps suppress later checks within a job. Detailed reports have no artifact upload
  or hosted Markdown/XML publication, and Python conformance can lose one diagnostic stream.
- PyYAML and PowerShell dependencies are not all exactly pinned; PowerShell 7 follows the host image.
- Shared dependency setup is repeated in YAML. There is no governed affected-test selector.
- PR compatibility omits the distribution-boundary check, although baseline conformance covers it.
- Phase 3 history records full-release compatibility at 1,504.3 seconds locally, exceeding the
  configured 900-second GitHub job allowance before setup. This is a budget risk, not a claim of
  an observed hosted timeout. Measure fresh profiles before choosing new deadlines.

EVR demonstrates separate policy/regression catalogs, ordered child execution, process ownership,
impact reasons, aggregate failures, and Markdown reporting. Its Pester migration remains planned.
Its unmatched paths produce `NoImpact`; its orchestrator meta-regression exists but is not a hosted
harness catalog member. Adopt stricter unknown-path handling and explicit hosted meta-regression.

## Target Ownership And Execution Model

| Layer | Owns |
| --- | --- |
| Static formatting and policy | Source inspection through Ruff, formatter, annotations, actionlint; no source execution or automatic fixes in CI. |
| Actual-change validation | Complete selected file validation and required composed context; one explicit change scope. |
| Python implementation tests | pytest unit/integration coverage for Python implementations, commands, validators, runners, selectors, and normalization. |
| PowerShell implementation tests | Pester **6.2.0** unit/integration coverage in Windows PowerShell 5.1 and PowerShell 7.4+. |
| Language-neutral conformance | Existing paired suites and shared fixtures proving portable contract semantics. |
| Cross-runtime parity | Matching inventories, accepted/rejected behavior, semantic summaries, errors, and serialization. |
| LoTM end-to-end compatibility | Reviewed project baselines, bounded QA/Visualization, extraction, and artifact lifecycle. |
| Expensive verification | Release/render and retained executable scale/pressure profiles; conceptual pressure review remains human/methodology owned. |
| Hosted orchestration | Provision agents, pass event scope, call repository profiles, publish results, and preserve aggregate exit status. |

### Catalogs And Supervisor

Use one Python-owned supervisor and selector, consistent with the canonical Python compatibility
referee. Independent PowerShell domain behavior and conformance must not delegate their semantics
to Python. Any convenience PowerShell launcher forwards arguments rather than owning another selector.
Document this intentional orchestration exception in the architecture when implemented.

Retain conformance and compatibility inventories in their existing registries. Proposed new
`Tools/CI/` catalogs own policy validators, implementation-test groups, and execution profiles.
Profiles reference owning inventories; they do not copy suite membership. Resolve exact filenames
and schema versions in Phase 1. Discovery detects missing registration; it does not approve tests.

Each approved unit needs stable ID, purpose, deterministic order, runtime/OS requirements, entry
point and arguments, fixture/impact metadata, total deadline, blocking policy, and output adapter.
Validate unknown fields/IDs, duplicates, path containment, missing files, stale exclusions, profile
coverage, and required runtime variants. Invalid executable catalogs fail; they cannot become an
empty successful run. Use safe argument arrays rather than shell command strings.

Plan execution before launching children. Expose a read-only list/selection plan with profile,
requested/selected/omitted IDs, change scope, reasons, deadlines, and runtime requirements.

### Change Scope And Conservative Selection

Separate policy scope from test selection. A changed registry may require complete project
composition; checking only its syntax is insufficient. Deletions participate in impact and integrity
checks even when no file remains to validate.

Use the complete PR merge-base comparison and preserve additions, deletions, and both rename paths
with NUL-delimited Git output. Define explicit local committed, staged, unstaged, and untracked modes;
never silently conflate a committed snapshot with working files. Record resolved refs and merge base.
Hosted adapters must also identify the actual source/merge commit being executed.

Initially optimize local/feature-branch feedback only. PR baseline and compatibility coverage stay
full during migration. Use current implemented paths, including transitive dependencies. Shared
ingestion/composition infrastructure, runners, catalogs, reporting contracts, dependencies, and host
configuration changes select broad coverage. An unknown path, unsupported status, missing history,
or incomplete impact metadata selects the complete applicable profile with a recorded reason.

Zero selected tests require every changed path to have an approved non-impact explanation. Distinguish
unselected coverage from native framework skipped tests. Fallback never silently enables an expensive
profile outside the requested profile, and selection never weakens lifecycle closure requirements.

### Runtime, Isolation, And Failure Behavior

Pin Pester exactly **6.2.0** and use version-qualified imports. Verify PowerShell 5.1 and 7.4+.
Choose and pin pytest, its necessary plugins, Python, and supporting dependency baselines after
compatibility evaluation; never automatically float to the newest release. Separate bootstrap from
execution. Required missing/incorrect dependencies fail preflight without silent runtime substitution.

Use isolated child processes with owned temporary directories and bounded stdout/stderr capture.
Implement tested Windows Job Object and POSIX process-group adapters. Total unit deadlines cover all
nested subprocesses; enforce a run budget with cleanup/reporting headroom. Stop only owned process
trees on timeout/cancellation. Keep execution sequential initially; add parallelism only with measured
benefit and proved isolation, while preserving deterministic result order.

Continue independent units after assertion, launch, discovery, or timeout failures. Unsafe shared
state/canonical mutation stops dependent work and reports why. Cancellation stops new launches,
terminates owned children, preserves partial evidence, and cannot report success. Missing required
results, unexpected empty collection, and unexpected skipped required coverage are failures.

### Reporting Across Local, GitHub, And ADO

Produce all reporting projections from the same recorded execution results:

- Concise human status and bounded failure excerpts.
- Versioned supervisor JSON with selection, provenance, per-unit status/duration/exit/deadline,
  omitted coverage, runtime versions, artifact locations, canonical protection, and cleanup outcomes.
- Markdown as the front door in GitHub and ADO: overall result, coverage/reasons, failures, durations,
  safety outcomes, and links to native tests and detailed diagnostics.
- Native pytest JUnit and Pester JUnit/NUnit results. Give runtime variants distinct stable identities.
- Honest XML adapters for custom conformance/compatibility checks, initially one result per
  suite/runtime or check. Do not invent assertion-level counts that runners do not expose.
- Complete JSON, stdout/stderr, comparisons, and failure artifacts, with measured retention/size policy.

Preserve detailed JSON and concise v1 for current clients, including extraction. Add a supervisor
contract rather than silently reinterpret them. Allow only documented normalization; protect IDs,
decisions, visibility, ordering, and file inventories. Reporting mode must not alter coverage.
Use run-owned ignored destinations, incremental evidence and atomic finalization; preserve partial
results after timeout/cancellation. A hard host termination may prevent final publication; document
that boundary rather than promising complete reports in all circumstances.

## GitHub And Azure DevOps Model

GitHub remains the initial authoritative merge location. Azure Repos receives the same commit
history as a synchronized copy; ADO PRs initially provide validation/learning evidence. Do not create
two independently merged histories or merge the modernization into `main` before its framework PR.
Resolve remote names, ref mappings, credentials, synchronization method, and permissions before
changing Git configuration. Verify intended branch commit parity after each synchronization; avoid
destructive mirror/force pushes. Keep credentials outside tracked files.

Use native GitHub Actions and Azure Pipelines orchestration over the same repository profiles.
GitHub PR events and Azure Repos target-branch build-validation policies have different trigger
mechanics; normalize their scope in adapters rather than duplicate selection semantics in YAML.
Both hosts must validate the modernization PR against the framework target branch.

Publish ADO XML with `PublishTestResults@2` after ordinary test failures, preserving aggregate failure
and detecting unexpectedly missing/publishing-failed results. Publish Markdown and detailed artifacts
in both hosts. XML improves ADO's Tests tab without replacing reports or converting custom runners
into pytest/Pester. Keep automated pipeline results distinct from separately managed manual Test Plans.

Before each ADO setup step, explain its purpose, configuration, local equivalent, and verification.
Demonstrate both a passing run and a deliberately failing test, including how to find diagnostics.
Inspect actual tenant access, agent availability/parallelism, costs, retention, and branch policies;
do not assume corporate settings or EVR permissions apply here.

### Target Event Matrix

| Event | Repository-owned coverage |
| --- | --- |
| Feature push | Annotations, static policy, affected implementation tests, fast conformance; conservative profile fallback. |
| PR | Full implementation/meta-regression, all three baseline runtimes, full baseline parity, PR compatibility including distribution-boundary. |
| `main` | Full integration plus separately budgeted blocking release/render verification. |
| Manual | Explicit named profile, default full; documented reproduction/scope options. |
| Weekly schedule | Full unfiltered verification, release/render, retained executable scale coverage. |

Preserve current events during shadow adoption. Measure feature-push costs and duplicate PR/push
runs before enabling expanded triggers. Prefer cancel-in-progress for superseded feature/PR runs;
retain main/release evidence. Choose schedule ownership between hosts to avoid accidental duplicated
expensive runs while proving scheduled execution on each host during rollout.

Preserve existing GitHub check names: `Workflow Policy`, `Python Validation`,
`PowerShell 7 Validation`, `Windows PowerShell 5.1 Validation`, `Project Compatibility`, and
`Work Annotation Policy`. Inspect actual protections before adding/renaming requirements. Do not
skip required workflows with path filters; repository selection explains coverage within completed checks.
Separate expensive job placement without masking failure in the integration result.

## Phased Implementation

Use `Phase 1`, `Phase 1.1`, `Phase 1.2`, and the same decimal structure throughout. These numbers
belong to this CI plan, not to the platform implementation plan. Cross-document references must name
the CI plan explicitly. Subphases define reviewable work units rather than predicting commit counts.

### Checkpoint And Evidence Discipline

For each subphase, record the scope, baseline commit, changed files, executed commands/profiles,
runtime/dependency versions, expected and observed outcomes, report/artifact locations, unresolved
findings, and the next checkpoint. Record hosted run URLs and actual executed commit IDs when
available. Distinguish a measured pass, expected synthetic failure, environment limitation,
accepted deferral, and work not executed. Do not prewrite successful closure evidence.

The coverage ledger records stable behavior/scenario references and their executable owners; it
does not copy executable profile membership out of catalogs. The decision record captures rationale,
affected contracts, and review outcome. Resolve their durable locations in Phase 1.3 and use pointers
from this plan rather than adding another evolving evidence store here.

At each checkpoint, inspect the intended diff, run checks appropriate to the change, review retained
reports, preserve unrelated changes, and update the ledger. Broader checks are required when shared
behavior changes or a phase gate demands them. Committing/pushing still requires explicit user
authorization. Do not mark an implementation checkbox complete from a local test alone.

| Phase | Prerequisite | Main acceptance evidence |
| --- | --- | --- |
| 1 | Accepted planning scope | Coverage ledger, measurements, reviewed contracts and decisions. |
| 2 | Phase 1 design gate | Pinned framework pilots and legacy/replacement scenario comparisons. |
| 3 | Phase 2 pilot gate | Catalog, scope, process, reporting, and selector meta-regression. |
| 4 | Phase 3 execution gate | Full local equivalence, cross-runtime parity, unchanged LoTM baselines. |
| 5 | Phase 4 local gate | Observed GitHub/ADO runs, native tests, Markdown, and host scope proof. |
| 6 | Phase 5 hosted gate | Explain-only selection evidence, event matrix, costs, and safe fallback. |
| 7 | Phase 6 rollout gate | Accepted retirement, exact-final validation, integration and handoff. |

Read-only ADO readiness inspection and publication design can occur in Phase 1. Live host setup
belongs to Phase 5. Begin implementation tests for new Phase 3 APIs alongside those APIs; Phase 2
pilots must use existing surfaces and must not depend on unimplemented selectors. Do not begin the
next major phase while a blocking gate is unresolved.

## Phase 1: Baseline, Coverage, And Design Contracts

### Phase 1.1 Repository And Host Orientation

- [ ] Review this expanded plan and record the accepted scope before implementation starts.
- [ ] Recheck branch/base commit, worktree changes, current catalogs, public entry points, source
  instructions, runtime/dependency availability, and current phase boundaries.
- [ ] Inspect actual GitHub checks/protections, triggers, permissions, caches, and artifact behavior;
  record unknown host settings rather than inferring them from YAML.
- [ ] Identify ADO organization/project/repository candidates, access, agents, parallel-job availability,
  retention, and costs without creating resources or changing policies.

**Checkpoint:** Current-state inventory distinguishes checkout facts, historical evidence, and host unknowns.

### Phase 1.2 Coverage And Consumer Dependency Ledger

- [ ] Map all existing suites, checks, static validators, reporting probes, and retained pressure families
  to their current executable owners and required runtimes.
- [ ] Inventory Python and PowerShell runtime modules and command adapters; assign implementation-test
  ownership and identify missing unit/integration coverage without duplicating shared conformance.
- [ ] Map positive, malformed, boundary, ambiguity, exact decision/error, scale, reporting, cleanup,
  canonical protection, and parity scenarios to proposed coverage or explicit retained ownership.
- [ ] Trace consumers of CLI switches, detailed JSON, concise v1, baselines, extraction copy lists,
  fixture discovery, environment variables, and dependency declarations before proposing changes.
- [ ] Identify transitive dependencies using current implemented paths; document areas where impact
  cannot be safely bounded and must select full coverage.

**Checkpoint:** Every existing coverage family and public consumer has an owner; gaps remain visible.

### Phase 1.3 Contracts, Catalog Boundaries, And Result Semantics

- [ ] Set catalog filenames/schema versions, stable IDs/order, discovery rules, runtime requirements,
  profile references, extension rules, and strict validation behavior.
- [ ] Specify committed versus local change-scope modes, merge/source execution semantics, safe path
  handling, conservative fallback, and evidence required for a no-impact decision.
- [ ] Specify execution/result states, blocking policy, prerequisite failures, skipped/unselected
  coverage, empty collection, cancellation, partial runs, aggregate exit codes, and report failures.
- [ ] Specify supervisor JSON, Markdown/XML projections, stable test identities, native/custom
  granularity, normalization rules, path confinement, and compatibility with existing consumers.
- [ ] Nominate authoritative ledger, decision-record, and execution-evidence locations; set how
  accepted design revisions and phase closure enter methodology, tooling reference, and evolution.

**Checkpoint:** Review concrete contract shapes and failure examples before implementing the supervisor.

### Phase 1.4 Measurements, Dependencies, And Budget Design

- [ ] Measure current local profiles by runtime, including setup, launch, normalization, rendering,
  extraction, and cleanup costs. Refresh hosted evidence when publication is authorized.
- [ ] Reconcile the existing full-release/job timeout mismatch; define total unit/run budgets and
  termination/reporting headroom without weakening the selected coverage.
- [ ] Select exact Python, pytest/plugins, PowerShell, and supporting dependency baselines; keep
  Pester fixed at 6.2.0 and document supported 5.1/7.4+ variants.
- [ ] Separate portable runtime/conformance requirements from test/dev/bootstrap dependencies where
  appropriate; account for extraction copies and available offline execution after bootstrap.
- [ ] Set cache keys/invalidation, runtime verification, owned module paths, artifact limits, retention,
  and missing-tool behavior; record any environment constraints requiring a different agent.

**Checkpoint:** Budgets and dependency decisions have measured or explicitly pending evidence.

### Phase 1.5 Dual-Host And Integration Design Review

- [ ] Record ADO destination, GitHub merge authority, remotes/ref mappings, synchronization sequence,
  divergence handling, and credential ownership; do not establish two independent merge histories.
- [ ] Set host event-to-profile mapping, PR target/source semantics, schedule time/ownership, duplicate
  run policy, check-name preservation, and safe staged branch-policy adoption.
- [ ] Review the full scenario ledger and unresolved decisions; distinguish blockers from accepted
  deferrals with owners and later checkpoints.
- [ ] Accept the implementation boundaries and Phase 2 pilot scope; retain original runners and gates.

### Phase 1 Exit Gate

- [ ] Reviewed contracts, ledger, budgets, dependency strategy, and host design are sufficient to implement.
- [ ] No unclassified coverage omission, public-consumer break, or Phase 4 canonical change is planned.

**Rollback:** Keep existing runners/workflows authoritative and revise design documents only.

## Phase 2: Pester And pytest Foundations And Pilots

### Phase 2.1 Pinned Bootstrap And Runtime Preflight

- [ ] Implement explicit bootstrap/dependency declarations and verify installed versions/paths.
- [ ] Use version-qualified Pester 6.2.0 imports; verify 5.1 and the adopted 7.4+ runtime baseline.
- [ ] Keep test invocation free of automatic installation; detect missing, legacy, wrong, and unusable
  dependencies with actionable failures.
- [ ] Test clean setup, repeat setup, changed dependency/cache state, and portable conformance after
  separating runtime and test requirements.

**Checkpoint:** Installation and execution are independently reproducible; no silent version substitution.

### Phase 2.2 Test Layout, Discovery, Fixtures, And Lifecycle

- [ ] Configure exact pytest roots and Pester files/tags; avoid collecting command-style conformance.
- [ ] Define unit/integration categories, stable identities, fixture ownership, setup/teardown,
  temporary output, environment restoration, and module import isolation.
- [ ] Prove individual files can run without cross-file setup side effects and discovery never contacts
  services or mutates canonical content.
- [ ] Define catalog registration expectations for new tests, including empty collection and stale files.

**Checkpoint:** A selected file/group and the pilot aggregate discover the intended same test identities.

### Phase 2.3 Representative Python And PowerShell Pilots

- [ ] Add fixture-driven pytest coverage for annotation discovery/CLI, existing registry validation,
  compatibility normalization, and representative Python API behavior selected by the ledger.
- [ ] Add Pester coverage for formatter discovery/token preservation, existing aggregate/report
  boundaries, and representative PowerShell API behavior in both supported runtimes.
- [ ] Use narrow importable helpers where needed; review any helper extraction separately and preserve
  public CLI behavior rather than introducing a broad runtime refactor.
- [ ] Exercise positive and negative scenarios with useful case names and exact assertions where
  defined; label mocks/synthetic fixtures and preserve shared-fixture authority.

**Checkpoint:** Pilots prove implementation behavior and complement independently runnable conformance.

### Phase 2.4 Native Results And Framework Failure Contracts

- [ ] Emit pytest JUnit and Pester native JUnit/NUnit results with distinct runtime identities.
- [ ] Prove assertion/discovery failures, no tests, wrong filters, missing dependencies, unexpected
  required skips, and fixture teardown failures return classified nonzero outcomes.
- [ ] Preserve case diagnostics, durations, native counts, and both output streams; verify structured
  adapters do not invent test granularity or mask framework exits.
- [ ] Check report encoding, XML escaping, unsafe paths, repeat execution, and stale-result avoidance.

**Checkpoint:** Results can be inspected locally and parsed without relying on hosted publication.

### Phase 2.5 Pilot Equivalence And Adoption Review

- [ ] Compare legacy and pilot coverage scenario by scenario, including deliberate failure detection,
  diagnostics, isolation, runtime cost, and local invocation.
- [ ] Update the coverage ledger and exact command documentation; keep original coverage active.
- [ ] Record limitations and choose the next implementation-test groups as Phase 3 APIs are added.

### Phase 2 Exit Gate

- [ ] Pilots pass in required runtimes and demonstrate useful diagnostics without weaker coverage.
- [ ] No harness is retired or host gate reduced on the strength of pilot test counts alone.

**Rollback:** Disable pilot profile references while retaining original execution and permanent fixtures.

## Phase 3: Catalogs, Supervisor, And Mandatory Meta-Regression

### Phase 3.1 Strict Catalogs And Execution Planning

- [ ] Implement owning catalogs and profile references without copying existing suite membership.
- [ ] Validate closed shapes, duplicates, unknown IDs, missing/stale files, runtime variants,
  containment, ordering, fixture ownership, and registration completeness.
- [ ] Produce deterministic read-only list/plan output, including required prerequisites and budgets.
- [ ] Test invalid catalogs as hard failures; unavailable approved coverage remains visible.

**Checkpoint:** Repeated planning selects the same ordered units; no children run during inspection.

### Phase 3.2 Change-Scope Resolver And Explain-Only Selector

- [ ] Implement NUL-delimited multi-commit merge-base scope, rename source/destination, deletions,
  explicit local modes, resolved refs, and executed source/merge provenance.
- [ ] Implement approved impact rules and conservative full-profile fallback for unknown/unsupported
  scope, missing history, unsafe paths, and incomplete metadata.
- [ ] Test spaces/Unicode/tabs and platform path rules, case distinctions, type/status changes,
  staged/unstaged/untracked input, empty scope, shallow history, and unavailable base/head.
- [ ] Prove shared infrastructure/transitive dependencies broaden selection and every no-impact
  decision has affirmative rules. Keep selection explain-only until Phase 6.

**Checkpoint:** Fixture-backed plans explain each selected/omitted unit and distinguish invalid catalogs
from safely recoverable selection uncertainty.

### Phase 3.3 Process Ownership, Deadlines, And Cancellation

- [ ] Implement tested Windows Job Object and POSIX process-group ownership using safe argument arrays.
- [ ] Drain stdout/stderr without deadlock, retain complete diagnostics to owned files, and bound
  routine presentation without discarding failure evidence.
- [ ] Enforce total unit/nested-child/run budgets, graceful termination where supported, bounded
  forced cleanup, and reserved report-publication time.
- [ ] Test grandchildren, hung/noisy children, launch/ownership failure, timeout, cancellation,
  parent termination, unrelated-process preservation, and later successful recovery.

**Checkpoint:** Synthetic process trees stop within budget; unrelated processes and outputs survive.

### Phase 3.4 Layer Adapters And Aggregate Execution

- [ ] Add adapters for static policy, actual-change validators, pytest, Pester, existing conformance,
  parity, and compatibility using their supported public contracts.
- [ ] Separate actual-file validation scope from tooling regression selection; include necessary
  composed context and deletion integrity checks.
- [ ] Address conformance child deadlines and compatibility first-failure behavior at their owning
  runner boundaries; a supervisor wrapper alone must not claim later internal checks ran.
- [ ] Continue independent failures, classify dependency-blocked/unexecuted units, stop unsafe shared
  state, and calculate aggregate status independently of publication success.
- [ ] Preserve standalone commands, detailed JSON consumers, expected errors, and semantic ownership.

**Checkpoint:** Deliberate formatter/test/compatibility failures leave later independent evidence visible.

### Phase 3.5 Unified JSON, Markdown, XML, And Artifact Lifecycle

- [ ] Implement projections from one recorded result model, retaining detailed JSON and concise v1.
- [ ] Render selection, skipped/unexecuted coverage, durations, failures, canonical protection,
  cleanup, and diagnostic links in readable Markdown.
- [ ] Adapt custom suites/checks to honest XML units while preserving native pytest/Pester cases.
- [ ] Test incremental evidence/atomic finalization, UTF-8/newlines/XML escaping, concurrent run names,
  confined paths, unsafe overwrite targets, stale evidence, and cleanup/publication failures.
- [ ] Verify cancellation/timeout partial reports and document the hard-host-kill boundary.

**Checkpoint:** Human, JSON, Markdown, and XML results agree; artifacts belong to one isolated run.

### Phase 3.6 Mandatory Runner And Selector Regression Gate

- [ ] Register catalog/scope/selector/process/report regression in mandatory local and hosted profiles.
- [ ] Use synthetic children and private registries to test the supervisor without recursively invoking
  the production full suite.
- [ ] Cover multiple failures, missing children, malformed summaries, discovery errors, empty/skipped
  coverage, launch errors, output limits, timeouts, cancellation, cleanup failures, and recovery.
- [ ] Prove selection reasons/order/counts and aggregate exit status remain deterministic.

### Phase 3 Exit Gate

- [ ] Meta-regression proves the concrete execution and failure contracts in supported OS/runtime variants.
- [ ] Existing runners remain usable and no reported result implies coverage that did not execute.

**Rollback:** Disable supervisor adoption; preserve original standalone execution and added regression fixtures.

## Phase 4: Full Local Equivalence And Compatibility Proof

### Phase 4.1 Same-Snapshot Shadow Comparison

- [ ] Run old and new full profiles on the same committed snapshot and dependency baseline.
- [ ] Compare ledger scenarios, inventories, runtimes, expected failure detection, and exit behavior.
- [ ] Classify every difference as intended reporting improvement, implementation defect, environment
  limitation, or separately reviewed contract change; block unexplained differences.
- [ ] Measure new setup/launch/execution/report costs and revise budgets with evidence.

**Checkpoint:** A comparison record identifies equivalent retained coverage and any remaining blockers.

### Phase 4.2 Complete Cross-Runtime Conformance And Parity

- [ ] Run all registered baseline suites in Python, PowerShell 7, and Windows PowerShell 5.1.
- [ ] Compare exact selected inventories and semantic summaries through the canonical comparator.
- [ ] Validate allowed operational normalization; inject a changed ID/count/decision/order/error to
  prove prohibited semantic differences fail.
- [ ] Exercise focused selection and full aggregation without changing shared-fixture expectations.

**Checkpoint:** Full baseline parity is executable, not inferred from independent green runtime jobs.

### Phase 4.3 LoTM Consumers, Safety, And Distribution Boundaries

- [ ] Run existing compatibility portfolios with distribution-boundary added to PR integration coverage.
- [ ] Preserve accepted QA/Visualization summaries, normalized inventories/hashes, bounded reader
  visibility, authored-content protection, filenames, and lifecycle semantics.
- [ ] Exercise root discovery, unsafe paths, stale output, scoped cleanup, protected-output changes,
  multiple failures, and compatibility deadline/cancellation behavior.
- [ ] Inspect retained failure output and prove unrelated artifacts survive; do not refresh baselines
  to hide a migration regression.

**Checkpoint:** Project semantics and canonical bytes remain unchanged, with complete consumer evidence.

### Phase 4.4 Extraction, Release, And Local Reproduction

- [ ] Rehearse the portable extraction bundle with the revised requirements/copy lists and no LoTM
  canonical content or new unapproved CI/runtime coupling.
- [ ] Run rendering and retained executable scale/pressure coverage using redirected outputs.
- [ ] Verify deadlines cover extraction/render descendants and successful cleanup preserves ownership.
- [ ] Document exact bootstrap/profile commands from Windows and unrelated working directories;
  Linux reports unavailable 5.1 coverage explicitly rather than claiming a full equivalent pass.

**Checkpoint:** Portable conformance survives modernization and hosted profiles have direct local recipes.

### Phase 4.5 Coverage And Safety Acceptance Review

- [ ] Reconcile every legacy ledger row against current executable evidence and unresolved limitations.
- [ ] Review reports/artifacts and verify new implementation tests cover affected modules/commands,
  rather than concentrating all test effort on the supervisor.
- [ ] Accept the local equivalence record before changing hosted authority; keep original gates available.

### Phase 4 Exit Gate

- [ ] Equivalent or stronger full coverage, unchanged LoTM baselines, complete parity, and safe output
  lifecycle are proved locally; environment limitations are explicit and do not masquerade as passes.

**Rollback:** Retain legacy invocation as reference and repair discrepancies before hosted adoption.

## Phase 5: GitHub And ADO Shadow Adoption And Learning

### Phase 5.1 Repository Synchronization And Host Readiness

- [ ] Publish the branch only after Git confirmation; establish approved ADO resources and remotes
  through the reviewed synchronization contract without destructive mirror/force pushes.
- [ ] Verify framework and modernization branch commit parity, ref mapping, authentication scope,
  divergence detection, and recovery after a partial synchronization failure.
- [ ] Recheck agents, runtimes, job capacity, costs, permissions, and protections before activation.
- [ ] Open an authorized draft GitHub PR into the framework branch when needed for shadow PR runs;
  use an ADO validation PR against the matching framework branch, without independent ADO merging.

**Checkpoint:** Both hosts test traceable identical source history; publication and merge authority are clear.

### Phase 5.2 Thin GitHub Actions Adapter

- [ ] Bootstrap pinned dependencies, verify runtime versions, pass event scope, and invoke repository
  profiles with no YAML-owned suite membership or validation semantics.
- [ ] Preserve existing check names and full required coverage; use nonrequired shadow jobs while
  comparing new orchestration against original checks.
- [ ] Validate workflow policy, immutable action pins, read-only permissions, cache invalidation,
  job budgets, cancellation behavior, and complete-history requirements.
- [ ] Prove PR source/merge execution and full multi-commit scope at the framework target branch.

**Checkpoint:** Observed GitHub evidence matches local profile behavior and identifies the executed commit.

### Phase 5.3 Native Azure Pipelines Adapter

- [ ] Explain project/repository/pipeline/agent/job/task boundaries and their local equivalents before setup.
- [ ] Configure pipeline YAML that bootstraps the same dependencies and invokes the same repository profiles.
- [ ] Configure Azure Repos framework-target build-validation policy in a staged/nonblocking form
  first; explain why Azure Repos PR validation is policy-driven rather than YAML `pr:` driven.
- [ ] Normalize actual ADO target/source/merge refs and prove complete branch scope; keep required
  suite decisions outside Azure YAML and branch-policy path filters.

**Checkpoint:** ADO runs reproduce the same semantic profile and source provenance as GitHub/local runs.

### Phase 5.4 Markdown, Tests Tab, And Detailed Publication

- [ ] Publish Markdown in both hosts and native pytest/Pester/custom XML with `PublishTestResults@2`
  in ADO after ordinary test failures; retain run-specific JSON and diagnostic artifacts.
- [ ] Verify stable names distinguish runtime variants, honest counts, skipped/unexecuted coverage,
  durations, failed cases, stack traces, and custom-suite details.
- [ ] Demonstrate passing, assertion-failed, timed-out, missing-result, and publication-failed runs;
  prove successful report upload cannot erase an execution failure.
- [ ] Walk through ADO logs, Tests tab, Markdown, diagnostics, and artifacts with the maintainer;
  explain automated results versus manual Test Plans and note actual cancellation limitations.

**Checkpoint:** The maintainer can diagnose an intentional failure from each host without rerunning blindly.

### Phase 5.5 Host Equivalence And Policy Adoption Review

- [ ] Compare run/profile/suite identities, scenario outcomes, executed commits, dependency versions,
  normalization, and report contents between both hosts and local reference runs.
- [ ] Record observed timings, cache behavior, artifact retention, permissions, cancellation, and agent limits.
- [ ] Review real required-check/build-validation configuration before making shadow jobs authoritative;
  do not remove old gates until equivalent or stronger hosted coverage is accepted.
- [ ] Keep rollback settings and original workflows available; record activation decisions and run URLs.

### Phase 5 Exit Gate

- [ ] Both hosts have observed success/failure evidence, usable native/Markdown reports, accurate PR
  scope, and safe staged policy adoption; local proof alone does not close this gate.

**Rollback:** Restore previous GitHub invocation; leave new ADO pipelines nonrequired and disable only
newly introduced policies/triggers through reviewed changes. Preserve shared Git history.

## Phase 6: Conservative Selection And Event Rollout

### Phase 6.1 Explain-Only Selection Against Full References

- [ ] Run selectors alongside full local and hosted reference profiles without reducing execution.
- [ ] Exercise representative current paths and deliberate shared/transitive changes, deletions,
  renames, dependency/catalog/report edits, and unknown paths.
- [ ] Compare reasons and selected coverage against the ledger; inspect missed-impact opportunities
  even when the unchanged full suite happens to pass.
- [ ] Verify no-impact rules, missing-history fallback, deterministic order, and selection provenance.

**Checkpoint:** Reviewed selection scenarios demonstrate conservative dependency mapping, not merely green runs.

### Phase 6.2 Local And Feature-Branch Selection Enablement

- [ ] Enable affected implementation tests and fast conformance for local/feature profiles with
  complete applicable-profile fallback and an explicit full-run override.
- [ ] Measure feature-push cost and open-PR duplicate runs; apply reviewed event deduplication without
  suppressing required checks or changing the source snapshot tested.
- [ ] Verify documentation-only/approved no-impact reports complete visibly with honest coverage status.
- [ ] Retain full PR implementation/meta-regression, conformance/parity, and project compatibility.

**Checkpoint:** Selection saves work only where its evidence permits; required integration coverage stays full.

### Phase 6.3 Main, Manual, And Scheduled Profiles

- [ ] Enable full integration and separately budgeted blocking release/render verification for `main`.
- [ ] Enable named manual profiles with default full execution and documented reproduction options.
- [ ] Demonstrate weekly full unfiltered release/render and retained executable scale coverage on both
  hosts, then apply agreed schedule ownership/time/retention to avoid accidental duplicate expense.
- [ ] Verify superseded feature/PR cancellation, retained main/release evidence, schedule branch/ref,
  and eventual applicability after the framework work merges to `main`.

**Checkpoint:** Every event maps to a documented locally runnable profile and produces accountable evidence.

### Phase 6.4 Failure, Cost, And Fallback Rollout Review

- [ ] Rehearse unavailable history, dependency/runtime drift, canceled jobs, partial publication, and
  selector failure under the enabled event model.
- [ ] Confirm full fallback, blocked required coverage, and aggregate failure remain visible.
- [ ] Review costs/budgets and update actual event behavior in the methodology/tooling documentation.
- [ ] Accept event rollout without authorizing any future reduction of full PR/lifecycle gates.

### Phase 6 Exit Gate

- [ ] Explainable selection, full fallback, complete required checks, and event cost/retention ownership
  are demonstrated in both host adapters.

**Rollback:** Force full profiles and disable only new optional triggers/schedules; retain mandatory gates.

## Phase 7: Selective Retirement, Integration, And Framework Handoff

### Phase 7.1 Retirement Proposal And Coverage Review

- [ ] Name each superseded harness/adapter and map its scenarios to verified replacements.
- [ ] Review direct invocation, failure diagnostics, runtime variants, cleanup, and reporting—not just counts.
- [ ] Retain useful custom conformance/end-to-end runners and shared fixtures; record accepted coverage
  revisions in methodology and evolution before deleting superseded implementation.
- [ ] Check every caller, catalog, extraction list, command recipe, and rollback dependency affected by removal.

**Checkpoint:** Only explicitly accepted replacements retire; no orphaned consumer or silently lost scenario.

### Phase 7.2 Documentation And Operational Handoff

- [ ] Update architecture, testing methodology, tooling reference, extraction/dependency guidance,
  profile commands, registration procedure, troubleshooting, and rollback instructions.
- [ ] Document how to add a test/check, choose its owning layer, declare impact, validate registration,
  reproduce a hosted failure, and inspect all result surfaces.
- [ ] Preserve dated historical measurements; record current costs, host settings, limitations,
  accepted deferrals, and authoritative evidence links without publishing secrets.
- [ ] Review the complete ledger against final implementation and resolve stale planning references.

**Checkpoint:** A fresh maintainer can reproduce, extend, and diagnose the architecture from repository docs.

### Phase 7.3 Exact-Final Verification And PR Readiness

- [ ] Run full local baseline/parity/implementation/meta-regression, static policy, compatibility,
  extraction, rendering, and retained executable pressure coverage on the final proposed snapshot.
- [ ] Observe matching final GitHub/ADO integration/release evidence after the latest executable changes.
- [ ] Verify unchanged canonical content/configuration/baselines, safe temporary cleanup, mirror parity,
  required checks, native results, Markdown, and complete diagnostics.
- [ ] Refresh the authorized modernization PR or open it if absent; target the framework branch,
  review upstream advancement, and rerun affected/full gates after any bring-forward changes.

**Checkpoint:** Final PR evidence belongs to the exact reviewed commits, with no outstanding blocker.

### Phase 7.4 Reviewed Merge And Post-Integration Verification

- [ ] Merge only with explicit publication authorization and accepted gates; synchronize GitHub's
  accepted framework history to ADO through the reviewed workflow.
- [ ] Verify post-integration profile results and actual required policy/check behavior before removing
  shadow configuration or describing the rollout as complete.
- [ ] Record confirmed commits, run URLs, coverage revisions, measurements, exclusions, rollback
  points, and handoff in platform evolution using its normal closure sequence.

**Checkpoint:** The framework branch contains the accepted modernization and both hosts reflect that history.

### Phase 7.5 Return To Platform Work

- [ ] Close the CI interlude checklist without marking Phase 4.1 findings reviewed.
- [ ] Independently complete the pending Phase 4.1 maintainer disposition gate before Phase 4.2.
- [ ] Resume platform work with the new test-registration/verification procedure and preserved
  logical-schema/canonical-content boundaries.

### Phase 7 Exit Gate

- [ ] The reviewed overhaul is integrated and verified, accepted retirements are recorded, the
  repository/host documentation is current, and the platform handoff is explicit.

**Rollback:** Revert focused adoption commits through normal review and restore the retained execution
path. Do not rewrite shared history, force synchronization, or reset canonical content.

## Remaining Setup And Review Details

The agreed direction includes dual hosts, GitHub merge authority initially, Pester 6.2.0, pytest,
retained shared conformance, Markdown plus native results, full PR gates, distribution-boundary
integration coverage, and a separate modernization branch/PR into the framework branch.

Phase 1 still needs concrete ADO organization/project/repository, access and agent availability,
remote/synchronization mechanics, exact dependency versions beyond Pester, runtime baselines,
measured budgets, schedule time/host ownership, artifact retention, and actual protection settings.
These are setup/design refinements, not completed tenant configuration. Explain ADO concepts at
their owning phase and record decisions in their authoritative contract or command documentation.

## Official References

- [Pester 6.2.0 package](https://www.powershellgallery.com/packages/Pester/6.2.0)
- [Pester 6 runtime and configuration migration](https://pester.dev/docs/migrations/v5-to-v6)
- [Pester native test results](https://pester.dev/docs/usage/test-results)
- [pytest output and JUnit reporting](https://docs.pytest.org/en/stable/how-to/output.html)
- [Azure Pipelines test-result publication](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines)
- [Azure Repos pipeline triggers and PR validation](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)
- [Azure Repos branch policies](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops)
