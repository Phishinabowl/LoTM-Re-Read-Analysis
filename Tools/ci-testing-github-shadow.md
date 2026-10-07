# CI 6.2 Thin GitHub Shadow Adapter

**Status:** Implemented locally; hosted publication and PR/source/merge proof remain open.
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
