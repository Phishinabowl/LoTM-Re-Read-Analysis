# CI Dual-Host And Integration Design

**Status:** Phase 1.5 design confirmed on 2026-10-05, based on `0e89480`, inspected 2026-10-05.
The maintainer accepted D15-D18, including GitHub weekly verification at Sunday 09:00 UTC and ADO
full runs on demand. The design below remains unimplemented. No workflow, pipeline, policy, catalog or runtime is
implemented/activated here. [Contracts](ci-testing-contracts.md) own execution/report semantics;
the [plan](ci-testing-modernization-plan.md) owns gates, and the [ledger](ci-testing-coverage-ledger.md)
owns coverage. [Budgets](ci-testing-runtime-budget.md) retain the dated measurement baseline.

## 1. Confirmed Host And Transport State

| Surface | Read-only evidence on 2026-10-05 |
| --- | --- |
| GitHub | Public `Phishinabowl/LoTM-Re-Read-Analysis`, default `main`; rulesets empty; main/framework branches report unprotected. |
| Azure Repos | Organization `DreamtechADO`; private project/repository `LoTM Inspired KM Platform`; repository enabled, default `refs/heads/main`. |
| ADO project/repository identity | Project `66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb`; repository `657f741d-cf62-44d6-8b6c-08d93f471133`. These identify the inspected destination, not credentials. |
| ADO execution/policy | Pipeline and repository-policy inventories empty; no ADO YAML in the checkout. A working pipeline/agent launch remains unproved. |
| Publication | `origin` fetches GitHub and has two intentional push URLs; `ado` fetches Azure Repos independently. HEAD/upstream/tracking tips and live modernization tips agree. |
| Capacity/retention | Phase 1.1 inspected one shared free private hosted slot, 1,800 minutes/month, 60-minute job ceiling, no self-hosted agents; artifacts/runs 30 days, PR runs 10 days. These older entitlement/retention observations must be refreshed before adoption. |

Live `git ls-remote` returned identical tips on both hosts:

| Ref | Commit |
| --- | --- |
| `main` | `608e48939ec352876ae919213a236592f46d982c` |
| `architecture/framework-extraction-foundation` | `c4b79326e8dde5420f61d318f4f541e752b6030a` |
| `architecture/ci-testing-modernization` | `0e89480f0f30cae0c6d9fb5370a319e6c1714a8e` |

Current GitHub `ci.yml` runs on PRs, main pushes and manual dispatch; it still includes 5.1 until
CI Phase 2. Non-main pushes run the separate annotation workflow. There is no schedule. Full CI
still has unconditional superseded-run cancellation, repeated setup, and no Markdown/XML/artifact
publication. These are current behavior, not evidence of the target below being installed.

## 2. Merge Authority, Synchronization And Credentials

GitHub is the sole merge authority. The modernization GitHub PR targets the framework branch;
the matching ADO PR is validation evidence against the same target, with no independent merge.
Normal confirmed publication remains exactly `git push origin HEAD`; never add an `ado` push,
mirror all refs, or force synchronization. Verify both results, refresh tracking refs and compare
HEAD/upstream/origin/ado. A partial push is a publication failure until diagnosed; do not overwrite
a divergent destination or run a second broad push to hide the discrepancy.

After an authorized GitHub merge, synchronize that accepted target commit to Azure Repos with an
explicit target-ref publication, outside the ordinary current-branch rule. Inspect destination
ancestry first and obtain the already-required scoped publication authorization. ADO does not
create another merge commit. Record source/target tips, run URLs and parity; divergent history blocks
integration closure. No automatic merge, write-back mirror service or credentialed CI push is planned.

Policy adoption must preserve this transport. Verify that proposed ADO target policies permit the
reviewed direct synchronization of GitHub-accepted history; optional validation is not an assumption
of push permission. If enforcement blocks that path, stop adoption and review the policy/transport
design. Do not automatically bypass policies, grant new write permissions or independently merge in
ADO to regain parity. This is a 6.3/6.5 activation gate, not an unresolved need to create another history.

Local transport uses existing credential-manager/CLI authentication outside tracked files. Hosted
checkout and metadata inspection use host-provided narrowly scoped read credentials; publication
uses only necessary artifact/test-result permissions. No tokens, credential profiles or credential-bearing
URLs enter child test environments, fixtures, caches or reports. Tests run offline after bootstrap;
no service connection or Azure subscription deployment is needed for repository testing.

GitHub and ADO PR merge commits can have different IDs despite identical source/target histories.
Cross-host equivalence requires matching source and target commits, profiles, catalog/dependency
digests and execution tree content; record each actual merge ID. Do not require the two hosts to
manufacture the same merge hash, or accept equal source tips as proof of equal execution trees.

## 3. Repository Profiles And Event Mapping

These are accepted design names for the future execution-profiles catalog. They do not introduce
a second membership list: each expands references to owning registries/catalogs with the contract's
strict rules. Shared profile coverage is validated by unit identities; profiles do not recursively
reference other execution profiles or duplicate owner membership.

| Profile | Required coverage / scope |
| --- | --- |
| `workflow-policy` | Registered workflow/configuration policy and approved tooling checks; whole applicable surface. |
| `annotation-policy` | Existing annotation policy, including its permanent fixtures; whole eligible surface. |
| `feature-feedback` | Static/actual-change policy, implementation/meta-regression and fast Python/PS7 conformance. Initially full within this profile; affected selection only after Phase 7 proof, with full-profile fallback. |
| `pr-integration` | All implementation/meta-regression groups, actual-change validation, all 21 baseline suites in both retained runtimes and complete parity; compatibility PR profile plus distribution-boundary. Synthetic media is required. |
| `full-verification` | Full eligible policy validation, all native/meta-regression and baseline/parity coverage, compatibility full-release (all 11 checks, including render), and registered retained executable pressure obligations. |
| `release-readiness` | Full verification plus applicable methodology-required human review evidence. Automated results cannot satisfy conceptual pressure review or promote unsupported families. |
| `implementation-pilot` | Approved Phase 3 groups with existing conformance/compatibility as the reference; no unimplemented supervisor dependency. |
| `modernization-shadow` | Replacement execution compared with the post-retirement legacy reference through separately named nonrequired host jobs. Required owner references retain their failure semantics; findings block adoption. |

Profile admission, registration completeness and the required-review family list are repository
decisions. Ordinary automated integration is distinct from lifecycle/release readiness: when a
methodology checkpoint requires a human review, that readiness obligation stays blocking there.
No ordinary PR obtains fictitious passes for all conceptual scenarios, and no required review is
silently dropped because its evidence is not automated.

| Event | GitHub | ADO | Scope / rollout boundary |
| --- | --- | --- | --- |
| Non-main feature push | Annotation check plus feature feedback after rollout. | Feature feedback after rollout; native results/Markdown. | Execute pushed source commit; explicit base for precise changes, otherwise full applicable policy/profile. |
| PR into framework/main | Full `pr-integration`; proposed explicit opened/reopened/synchronize/ready-for-review/edited-base handling, including draft evidence. | Target-branch build-validation policy dispatches full `pr-integration`. | Execute verified merge snapshot; source impact is merge-base-to-source, not just latest commit. |
| Main push | Full `full-verification`. | Full `full-verification` after synchronized GitHub history arrives. | No affected filtering; test exact committed source. Main/release evidence is retained. |
| Manual | Named allowlisted profile; default `full-verification`, explicit branch/ref. | Same profile choices and explicit ref. | Full by default; precise comparison only with an explicit validated base. |
| Weekly | Selected owner: full `full-verification` on main, Sunday 09:00 UTC. | No steady-state weekly run; full runs on demand. | Both hosts demonstrate scheduled dispatch during rollout before removing the temporary ADO schedule. |

Framework PRs and named manual runs supply pre-main evidence. Do not enable periodic feature-branch
verification or claim GitHub's scheduler can test an arbitrary framework branch. Main event adoption
becomes relevant only as reviewed history reaches main; current events remain active during shadow.
New ADO pipeline proposal: `LoTM Platform CI`, YAML `.azuredevops/ci.yml`; create it only in Phase 6.
GitHub retains its two existing workflow paths. Native host adapters pass scope and profile names;
YAML never defines fixture membership, impact rules or validation semantics.

Shadow jobs preserve native/supervisor exits and complete diagnostics; do not apply blanket YAML
continue-on-error to hide a required owner failure. The optional/nonblocking boundary is host adoption,
while existing required reference gates stay authoritative. `passed-with-findings` remains limited to
explicitly approved observational references permitted by the existing contract, not a general shadow
success override. Separate reference/replacement runs carry distinct run identities and match snapshots.

### PR Provenance And Scope

GitHub PRs use event base/source SHAs and the verified checkout merge ID/tree. ADO records
`Build.SourceVersion`, `System.PullRequest.SourceCommitId`, target/source refs and PR identity;
resolve the target commit from verified execution metadata/merge ancestry, with API corroboration
where needed. Do not invent a `System.PullRequest.TargetCommitId` variable or compare against a
moving target tip fetched later. Verify actual parent/source relationships and tree content; parent
position alone is not a universal inference rule. Changed target/base/metadata races require full
comparison fallback or a planning failure when the executed snapshot cannot be trusted.

Both adapters provision complete Git objects/history, then use the repository scope resolver.
Missing comparison evidence can fall back to full eligible policy/full requested profile on a known
coherent snapshot; unidentified/mismatched execution cannot. Report lost deletion/history precision
instead of silently using one commit. Host provenance checks belong to 4.2/6.2/6.3 regression and pilots.
The official sources describe [GitHub PR merge refs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request),
[Azure Repos policy-driven PR builds](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#pr-triggers)
and [ADO build/PR variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops).

### Duplicate Runs, Cancellation And Schedule

Initially keep push feedback even when a PR is open; the feature profile is cheaper than integration.
Do not suppress required PR work based on an unreliable cross-host PR lookup. GitHub and ADO both
run PR/main evidence intentionally; that dual-host cost is the learning/equivalence requirement.
Measure overlap before further optimization at 7.2. Annotation currently also runs within Python
validation: keep one owner per profile and separate non-main push visibility, rather than blindly
adding another PR annotation job or demanding a push-only check on a merge ref.

Cancel superseded feature/PR runs within that host, branch/PR, target and profile; never cross-cancel
main, manual release or scheduled evidence. Keep those runs queued/serial when necessary. ADO CI
batching may combine source pushes while PR auto-cancellation needs separate verified settings.
Every cancelled run reports partial/blocked coverage where publication survives; queue batching,
host cancellation and child-process cancellation are different contracts. No host-independent API
cancellation service is required. Current GitHub blanket cancellation is changed only during adoption.

The selected steady-state owner is GitHub; accepted Sunday 09:00 UTC is 05:00 Eastern in daylight
time and 04:00 in standard time. Scheduling is best effort. The public GitHub repository's scheduled
workflows can be disabled after inactivity and run on the default branch; inspect actual dispatch
and report absence explicitly. GitHub notes potential delays/drops at busy times, including the hour.
Keep the accepted time; move it only through a recorded schedule decision.
[GitHub schedule reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

ADO's temporary schedule pilot declares its ref and forces execution even with unchanged content;
inspect UI schedule overrides and actual queued runs. Remove the pilot schedule after demonstration
and verify no duplicate steady-state schedule remains. A missing schedule execution is unverified,
not a passing run. No monitoring automation is created here.
[Azure scheduling reference](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/scheduled-triggers?view=azure-devops).

## 4. Shards, Budgets And Aggregate Check Identity

A shard is an approved portion of a repository profile assigned to one hosted job. A shard plan
records exact expanded units, owning references, dependency edges, budgets and expected evidence;
the union must equal the requested full profile with no duplicate execution identity. Distinct
extraction/rejection/reporting exercises remain separate even when they call similar tools.
YAML consumes a validated repository shard plan; it cannot quietly repartition or omit units.
The proposed `shard_plans` addition in the contracts records placement and result-gate inputs in
the existing execution-profiles catalog. It is not another membership registry or a new fifth catalog.

Sequential child execution remains the supervisor rule inside each shard. Any independent host-job
overlap must prove isolated checkout/scratch and dependencies before adoption; otherwise serialize
the jobs. ADO's inspected single slot already serializes allocation. Results always render in global
plan order, irrespective of completion order; comparison/aggregation waits for all required sources.

Use the accepted 55-minute target, 600-second provisional cold setup, 210-second supervisor reserves,
180-second publication and 120-second host margin: admitted unit deadlines total at most **2,190
seconds per shard**. Native costs, exact shard counts and cold allowances require measurement in
2.5/3.1/5.1; publish no unmeasured numerical savings. A normal short run does not justify admitting
a declared worst-case allocation beyond the host ceiling.

At the current 120-second minimum per granular unit, 21 conformance units reserve at least 2,520
seconds per runtime. That cannot fit one 2,190-second window before native groups. Provisionally
plan multiple conformance shards for each runtime; measure actual setup/group deadlines before
fixing the layout. The earlier 120/660-second aggregate envelopes are placement observations, not
permission to pretend every individual suite can inherit the aggregate's deadline or hide its cases.
Fewer shards require a measured/reviewed allocation change, not weaker or missing coverage.

The following is the preserved Phase 1.5 illustration using dated pre-retirement deadline candidates:

| Candidate shard | Owning check IDs | Deadline sum |
| --- | --- | ---: |
| Compatibility A | compatibility-reporting, conformance-reporting, framework-catalog, visualization, qa, root-discovery, artifact-lifecycle | 2,070 seconds |
| Compatibility B | effective-schema, framework-extraction, distribution-boundary, render | 2,010 seconds; 1,890 for PR without render |

This partitions all 11 checks; it is historical illustrative design, not an executable second registry.
Phase 2.5's [budget refresh](ci-testing-runtime-budget.md#phase-25-retained-runtime-budget-refresh-2026-10-05)
supersedes these sizing candidates: the complete retained portfolio proposes a 1,920-second deadline
sum, fitting one 2,190-second allocation window. With the existing allowances, total admission is
3,030 seconds under the 55-minute target. One compatibility shard is therefore a provisional option;
native/meta tests and source baseline work are not included in that sum. No shard manifest or hosted
partition is implemented by this evidence. Preserve owning order; enforce final measured placement
through profiles/metadata at 4.1/4.4. Source baseline/native/policy work
has separately admitted shards. Parity/aggregation needs its own measured budget and source manifests.
Legacy fail-fast runners must expose owning check boundaries/continued failures before a wrapper
can claim later coverage; this remains required in 4.4.

Retain GitHub integration identities `Workflow Policy`, `Python Validation`, `PowerShell 7 Validation`
and `Project Compatibility`. Retain non-main `Work Annotation Policy`; it is not a required PR check
unless an explicit reviewed PR event gives it genuine execution. CI Phase 2.6 retires the 5.1 check.
Use clearly named nonrequired worker/shadow jobs; retained check names become stable aggregate jobs
where needed, always evaluated after ordinary child failures. No workflow-level path skip leaves a
required context pending; no synthetic green replacement reports omitted coverage.

Python/PS7 aggregates require exact source-unit inventories, outcomes and artifacts. Project
Compatibility additionally performs complete baseline parity and confirms the requested compatibility
portfolio. Build a comparison view of returned suite results, preserving original files; do not
fabricate a legacy full-run report or say one runner executed a profile that was assembled from shards.
Aggregate records must match commit/tree, profile, plan/catalog/dependency digests and runtime versions.
Missing, stale, duplicate, wrong-snapshot or malformed artifacts fail, even if every available job is
green. Cancelled/skipped required shards cannot satisfy the union. Host finalization loss remains explicit.

Local reproduction resolves the same profile and all shard plans against one snapshot, runs them
in deterministic order and produces a run-set aggregate with the same coverage/status rules. Local
full execution does not require hosted artifact services or YAML. Exact command surfaces are implemented
and documented in Phase 4; none of these profile names is a current invocation recipe.

Capacity planning uses summed measured agent-job minutes, including repeated cold/cache setup,
shadow reference runs, cancelled work and intentional dual-host events. Queue latency is separate
from consumed agent time. With N feature pushes, P PR validations, M main updates and U on-demand
full runs, estimate ADO use as `N*feature_minutes + P*pr_minutes + M*full_minutes + U*full_minutes`
plus pilot/shadow/cancellation overhead. Refresh remaining organization allowance; other projects
share it. If admission/capacity fails, keep evidence unverified and defer activation or review capacity;
do not purchase agents or reduce PR coverage implicitly. Quantified cost/cadence approval belongs to 7.4.

## 5. Shadow Adoption, Policy Gates And Learning

| Stage | Authority / action | Required evidence / rollback |
| --- | --- | --- |
| Phase 2 | Retire only 5.1; existing retained runners/workflows remain authoritative. | All retained semantics/report counts/cleanup, fresh budgets, hosted retained checks; revert focused retirement together if needed. |
| Phase 3 | Bootstrap/layout/native pilots against existing retained coverage. | Clean/offline/exact-host setup; independently runnable pytest/Pester, required synthetic media, failure/collection/XML proof. Keep existing checks. |
| Phases 4-5 | Implement strict catalogs/scope/process/results; full local shadow comparison. | Mandatory synthetic meta-regression plus all 21/11/nine-suite boundaries, canonical guards and retained human reviews. No hosted authority change. |
| Phase 6 | Add nonrequired replacement evidence and the ADO pipeline/optional validation policy. | Same source/target/tree proof; passing/failing/timeout/missing/publication scenarios, Tests tab and Markdown, verified agent/cost/retention. Restore original GitHub invocation; disable only new ADO triggers/policies. |
| Phase 7 | Enable conservative feature selection, main/manual events and selected schedule. | Explain-only comparisons first; full PR/reference remains. Verify duplication, cancellation, fallbacks and monthly use before rollout acceptance. |
| Phase 8 | Integrate reviewed overhaul into the framework branch, synchronize accepted history and verify afterward. | Exact-final host/local evidence and explicit merge authorization; retain rollback commits/settings. Platform Phase 4.1 review stays independent. |

Do not add required GitHub contexts until real jobs have published the proposed names and failed
correctly on a negative control. Initially keep current protection state while comparing shadows;
at 6.5 propose required retained PR checks for framework/main using exact observed contexts, with
fresh settings and maintainer adoption review. ADO build validation starts optional/nonblocking on
the framework target, expires/revalidates when target changes, and never authorizes ADO merging.
Later policy changes need their existing explicit activation authorization; this document does not grant it.
Before enabling policies, prove their interaction with target synchronization on the approved test
scope and keep recorded prior settings. No extra reviewer-count, access-control or merge policy is
introduced merely to demonstrate automated build validation. Policy controls do not redefine suite scope.

Before each ADO action explain: project/repo identify code; pipeline selects YAML/ref; an agent runs
each job; tasks invoke repository commands and publish artifacts; build validation queues a PR merge
build; Tests displays native/custom XML while Markdown explains profile selection, omissions and
failures. Local reproduction is the same repository profile without host publishing. Demonstrate an
intentional failed case and where to find its diagnostics, not just screenshots of a green pipeline.

## 6. Scenario Ledger Review, Deferrals And Entry Gates

The ledger already maps all 71 stable methodology families, 21 suites, 11 checks, runtime files and
14 command filenames. Membership stays there/in owning registries; no family is retired here except
the reviewed host support boundary D14. The following groups dispose of every current G01-G14 gap:

| Gaps / uncertainty | Classification, owner and required checkpoint |
| --- | --- |
| G01/G02/G03: implementation/media/formatter/meta-regression coverage | Accepted implementation work: native owners at 3.3; supervisor/selector at 4.6; integration at 5.1/5.3. Mandatory PR coverage; no count-only adoption. |
| G04/G05: lifecycle and incomplete canonical protection | Accepted implementation work: fixture/guard owners at 3.2/5.3; block coverage retirement at 8.1 until proved. |
| G06/G14: exact dependencies/extraction/5.1 support | Accepted coordinated migration at 2.1-2.6 and 3.1/5.4. Two-runtime closure precedes native pilots. Unsupported external consumers are not an open transition requirement per maintainer. |
| G07: native/custom XML and retained conceptual review | Reporting owners at 3.4/4.5/6.4; methodology review at 5.5/readiness. No fabricated assertion/story cases or implicit automation of unsupported families. |
| G08/G10/G13: timeout, cleanup, normalization and fixture ancestry | Known observed defects/limitations, not design blockers with named delivery: retirement proof/measurement at 2.5; process/report owners at 4.3-4.6 and 5.3/5.4. Failed cleanup/report evidence blocks its execution acceptance. |
| G09/G11: full parity and conservative dependencies | Comparison/scope owners at 4.2/5.2 and 7.1; PR stays full. Shared/unknown paths cannot become no-impact. |
| G12: duplicated annotation/check identity and host policy | Host owners at 2.6/6.2-6.5, event proof at 7.2. Preserve genuine check contexts and stage policy changes. |
| Exact PS7 floor, clean/hash locks, Linux/media limitations | Named proof gates at 2.2/3.1/3.3/5.4. Primary observed host 7.6.6; 7.4+ support is not already tested at its floor. Keep Windows/API obligations explicit. |
| Final shard count, native/cold timing and monthly usage | Deferred numerical acceptance to 2.5/3.1/5.1/6.5/7.4. Admission proof precedes activation; preliminary partitions are not production authority. |
| Agent launches, schedule delivery, cancellation/publication/retention | Deferred live evidence to 6.1/6.4/6.5/7.3. Empty pipelines/queue entitlement do not prove running agents or durable upload. |
| ADO policy compatibility with direct GitHub-history synchronization | Host policy/transport proof at 6.3/6.5 before enforcement. Stop activation if blocked; no automatic bypass or second merge history. |

Mandatory negative controls cover missing/wrong execution commits, incomplete history, changed target,
unknown paths, missing host, invalid/duplicate registration, empty collection/unexpected skips,
assertion plus later timeout, escaped descendants, scratch/report/publication failure, wrong shard
union, stale artifacts, prohibited parity normalization, shadow findings and absent required review.
The existing contracts own exact outcomes and runner tests; adapters add event/manifest regression,
not a second semantic runner. Every scenario needs observed evidence at its owning checkpoint.

Phase 1 exit review accepted this design and all gap dispositions on 2026-10-05. No new
unclassified omission, consumer break or canonical migration is proposed. Phase 2 is limited to the
reviewed retirement inventory; Phase 3 pilots cover representative implementation boundaries and
required media without building the Phase 4 supervisor early. Full Python/PS7 dual implementation
remains the current policy. Deferred runtime/host proofs do not claim those phases are complete.

Confirmation closes only Phase 1.5/Phase 1 design and publishes documents. It does not start
retirement, native adoption, create PRs/pipelines, change branch policies or enable schedules.

Documentation verification on 2026-10-05: 56 relative links/anchors resolve across the six affected
documents; all 41 CI subphases remain sequential; two JSON examples and one XML example parse.
The methodology's 71 stable family IDs remain mapped, every G01-G14 disposition is present, and
the illustrative partition matches all 11 registered compatibility IDs without duplication. Budget
arithmetic passes. Annotation policy passes 22 fixtures / 388 files and `git diff --check` passes.
These checks validate design consistency, not runtime/host equivalence or final shard performance.
