# CI 6.2 Thin GitHub Shadow Adapter

**Status:** Published as `407107b`; draft GitHub PR 3 is open. Hosted PR/source/merge proof remains open.
Entry is confirmed 6.1 at `1b2911f`. This checkpoint does not replace existing CI or close Phase 6.
The [modernization plan](ci-testing-modernization-plan.md#phase-62-thin-github-actions-adapter)
owns acceptance; [host integration design](ci-testing-host-integration-design.md) owns event/merge
policy. GitHub remains the authoritative merge location; no protection change is introduced.

## Repository Authority And Host Transport

[Shadow workflow](../.github/workflows/ci-shadow.yml) and its
[reusable worker](../.github/workflows/ci-shadow-worker.yml) invoke
[repository adapter](CI/github_shadow.py). `Catalog` selects the unique approved shard plan and
derives its OS, independent/dependent waves and timeout from the current catalogs. YAML has no
unit/suite list or path-based coverage selection. All requested profile units remain required.
The current graph has one dependency wave: parity consumes the four conformance source shards.
Before catalog construction, the planning job explicitly bootstraps a fresh pinned runtime-only
Python environment: catalog validators import the framework's YAML implementation. This setup
has a 150-second deadline inside the five-minute planning job and is separately measured; it is
not a global pip install or an assumption about packages preinstalled in the agent image.
Deeper dependencies fail admission until orchestration is reviewed; they are not silently skipped.
Collection requires every approved shard exactly once, even after ordinary worker failures.
Missing downloads cannot fall back to accidentally executing the whole profile again.

PR events target the framework branch and select full `pr-integration`. Explicit manual runs
allow `full-verification`, `pr-integration` or `ci-infrastructure`; default is full verification.
Feature/main/schedule event adoption and supersession cancellation remain Phase 7. No workflow-level
path filtering, `pull_request_target`, elevated token, blanket continue-on-error or required-check
replacement is added. Existing `CI` and `Work Annotation Policy` jobs retain their names and behavior.

Normal PR execution uses the event's exact merge checkout, base and source SHAs. Explicit manual PR
replay accepts a bounded numeric open PR ID, retrieves current metadata using read-only GitHub API
access, and selects exact source or merge execution. The approved target repository/ref must match.
Actual HEAD must match execution; a merge must have the exact target/source parent set. Metadata
races/unproven execution fail. Scope then uses the existing merge-base-to-source resolver, including
all commits and deletions; unavailable comparison for a coherent manual snapshot remains visible
full fallback. Manual input does not redefine comparison or suite semantics.
[GitHub event documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).

Checkout uses complete history and no persisted credentials. All external actions are immutable
commit pins. The new download action adopts v4 commit `d3f86a106a0bac45b974a628896c90dbdf5c8093`;
downloads are limited to this run's shard artifact names. Existing exact Python/action pins are
retained. Read-only `contents` and `pull-requests` permissions cover checkout/manual metadata;
there is no token in payload caches or report bundles.

## Preparation, Isolation And Budgets

The 6.1-qualified complete payload is the initial shared immutable transport unit, using a new
shadow namespace and automatically keyed helper/lock/runtime bytes. Each worker prepares fresh
development/media Python, PS modules, build-only wheel and locked rendering. Complete preparation
on every worker avoids admitting partially populated caches under the same identity; it knowingly
repeats setup not needed by every shard. Measure this cost at 6.5 before splitting transport into
separately qualified payloads. Do not count cache reuse as test success or claim these shadows are
the optimized final placement.

Actionlint 1.7.12 is acquired as an official x64 archive with checked SHA256, extracted to owned
user storage and version-probed. Its archive is included in cache transport. A warm hit runs offline
and cannot repair corrupt or missing payloads. No machine installation or internal feed is introduced.
[Official actionlint release/checksums](https://github.com/rhysd/actionlint/releases/tag/v1.7.12).

Workers receive 600 seconds for preparation, their catalog shard's execution/lifecycle budget,
180 seconds for publication and 120 seconds host margin. The derived timeout is rounded up to
minutes and cannot exceed 55. Collection reserves 21 minutes for setup, its 330-second gate and
publication/margin. Preparation has an inherited monotonic deadline; supervisor unit/process budgets
remain authoritative. Host cancellation skips new dependent launches; controlled cancellation,
partial recovery and publication acceptance still require their Phase 6.4 experiments. No passing
cancellation result is inferred from static workflow conditions.

Production PS script children use
[owned launcher](Commands/Environment/Invoke-OwnedPowerShell.ps1) and
[argument transport](Commands/Environment/powershell_process.py). The launcher resets the module
path after startup to the explicit supervisor-selected owner plus PS builtin modules. It carries
named parameters as data and preserves original nonzero exits. Aggregate preflight/formatter,
native Pester, conformance suite children and compatibility script children share this isolation;
standalone commands without the explicit CI owner retain their prior behavior. Exact-version/module
receipt and owned-origin preflight checks remain. No global module is removed or rewritten.

## Evidence And Local Reproduction

The adapter delegates execution/collection to `run_ci.execute`, with explicit paths from bootstrap
reports and GitHub host/run provenance. It copies only the existing admitted publication inventory
into a transfer bundle, preserving the original run-directory name, detailed reports, journals,
native/custom evidence and byte hashes. Generated captured sources and private scratch ownership
are excluded. Each worker uploads its admitted bundle and setup/failure diagnostics after ordinary
failure; collection still verifies exact source/catalog/profile/partition and content through the
existing collector. Upload success never overrides a failed supervisor exit.

The adapter does not yet publish Step Summary/native tests or issue hosted publication receipts.
Those are Phase 6.4, where deliberate failed/missing/stale/publication/cancellation experiments must
prove both visibility and outcome. This transport supplies their required complete evidence.

Local reproduction uses the same [aggregate commands](CI/aggregate-execution.md#local-commands):
prepare pinned dependencies explicitly, resolve `hosted-pr` with exact recorded base/source/executed
SHAs, execute every catalog shard with prerequisite bundles, then collect all source bundles.
No GitHub artifact service or workflow execution is required locally. Manual replay requires the
exact recorded objects; replacing an unavailable merge with another tree is not equivalent proof.

## Verification And Remaining Hosted Gate

The first automatic [shadow run 37574526788](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37574526788)
fails at context setup before any tests launch: the adapter mistakenly used `.local`-only bootstrap
path admission for `.tmp/ci-shadow`. The scoped correction uses the existing confined report-path
authority, retaining link/escape checks. A real `-I -S` bare-interpreter CLI regression covers the
host's pre-bootstrap context step and verifies bounded outputs without installed packages. The failed
run remains historical evidence; production coverage is not credited for its skipped workers.

The [next run 37574903443](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37574903443)
passes context admission but fails catalog construction because the bare interpreter lacks PyYAML.
The scoped correction adds explicit runtime bootstrap before catalog planning and uses its verified
interpreter. A clean private-checkout planning CLI regression exercises actual scope resolution,
owning validators and the complete eight-independent/one-dependent matrix, without launching tests.
Neither failed attempt satisfies execution coverage; both remain preserved.
Workers likewise invoke execution/collection through the verified development interpreter returned
by bootstrap, rather than the host's base Python. Catalog validation and aggregate execution share
their declared prerequisites; prepared environments are explicit paths, not implicit activation.

At `84c7de7`, [run 37575809880](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37575809880)
completes all nine shards and collection: 72/76 units pass, four fail, none are skipped/blocked,
and the aggregate remains red with verified source guards/cleanup. All four conformance source
shards and parity pass; media and infrastructure pass. Original reference CI also passes all four
retained check identities in [run 37575809655](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37575809655).
This is observed continuation and failure preservation, not passing shadow acceptance.

Two native failures identify Windows LICENSE checkout CRLF versus captured Git-blob LF and an
absent launcher location in extracted synthetic conformance functions. Two compatibility failures
identify the same missing launcher in reporting/extraction fixtures. The scoped correction sets
`core.autocrlf=false` through per-job Git environment configuration before checkout, retaining
explicit `.gitattributes` rules and exact wheel-content comparison. No repository/user Git setting,
canonical file or wheel verifier is changed. A real Git regression proves CRLF defaults produce
different bytes, then the job override produces exact license blob bytes.

The supervisor passes the confined source launcher explicitly; wrapped children propagate it into
their descendants. Both script and existing inline PowerShell commands use the selected module owner,
including extraction verification. Neutral/extracted frameworks do not acquire CI directories or
another portability dependency. Synthetic child timeout coverage retains the five-second wall bound
and twenty-second sleeper but uses a two-second deadline, allowing cold PS startup to emit its
required diagnostic. Production deadlines and coverage identities are unchanged.

Corrected local scope regression passes 62 cases on both OSs. The real native adapter passes all
eight conformance-runner cases on Windows/Linux; five dependency cases verify script/inline owned
imports and exact exits. Windows execution/compatibility/package regressions pass 164 cases.
Real conformance-reporting and framework-extraction checks pass with explicit owned modules,
unchanged canonical outputs and verified fixture cleanup. Actual hosted retry/source replay remains
necessary; these local corrections do not turn the retained red run into a pass.

Final scope/bootstrap/report regression passes 133 cases on Windows and Linux. The earlier broader
execution/report/native-result/compatibility cohort passes 219 cases; its report additions are
covered by the final focused cohort. Five Pester dependency cases pass on both OSs, including real
child isolation, literal argument preservation, exit 7 and successful handling of an expected nested
native failure. Synthetic Git metadata proves multi-commit
deletion scope, source/merge replay, wrong execution/target rejection, catalog-owned matrices and
full comparison fallback. Transfer regression verifies exact inventory, failure preservation and
corrupt transferred evidence rejection. Existing groups own these cases; no new semantic family
or permanent group is registered.

The real local `ci-infrastructure` profile passes all five units in 84.545s using its captured
worktree snapshot. This is bounded local runner proof, not a hosted/full-profile timing. Final
repository Ruff lint/format, actionlint across all workflows, changed PowerShell formatting,
annotation policy (22/22 fixtures, 484 files, zero findings) and `git diff --check` pass. The new
Windows actionlint provisioner acquires the official archive, verifies its digest and probes 1.7.12.
Linux archive/host provisioning is still part of live shadow qualification, not inferred from WSL tests.

Before closure, publish the reviewed adapter, open the authorized draft GitHub PR into the framework
branch, and record passing live automatic merge and explicit source replay. Verify actual scope covers
more than the latest commit, all expected shards/gates execute, pinned setup/import origins qualify,
ordinary failures do not suppress independent work and original required contexts remain intact.
Retain exact source/tree/catalog identities and real job/setup/transport durations. Final admission
and placement remain 6.5; do not infer them from local tests or 6.1 preparation timing.

**Rollback:** Disable/remove only the new shadow adapters and optional draft PR; preserve existing CI,
required identities, canonical sources, verified caches and the published 6.1 evidence. No merge or
protection adoption is authorized by this checkpoint.
