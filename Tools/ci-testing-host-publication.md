# CI 6.4 Hosted Markdown And Test Publication

**Status:** First implementation increment is prepared locally, uncommitted for maintainer review.
Hosted Markdown/Tests acceptance and deliberate hosted failure experiments remain open. Entry is
confirmed 6.3 at `cc93c8d`; the [modernization plan](ci-testing-modernization-plan.md#phase-64-markdown-tests-tab-and-detailed-publication)
owns acceptance. No required check, branch policy, event or timing goal is changed.

## Authority And Failure Behavior

[`publish_hosted.py`](CI/publish_hosted.py) consumes the current worker's single exported run bundle.
It verifies the final marker, manifest, file hashes, projections and XML counts, then corroborates
profile, executed commit and shard identity against host context. It does not run tests, add catalog
members, scan raw XML or manufacture a successful group case. Missing, corrupt, ambiguous or foreign
evidence fails admission and produces a diagnostic summary with no inferred coverage. Failed execution
bundles remain publishable, preserving their nonzero execution exit.

A fresh `.tmp/ci-shadow/publication` owner holds hosted `summary.md`, exact-byte XML copies and
`receipt.json`. Receipts distinguish execution outcome, admission and Markdown submission. Writing a
GitHub summary file or emitting an Azure logging command does not prove server acceptance; actual
task logs, summary attachments and test-result API evidence must establish that after publication.
Successful uploads cannot erase the preceding execution failure. Publisher, artifact and native-result
upload errors also fail the job; no `continueOnError` or outcome-reset step is added.

## Markdown And Artifacts

Every worker publishes its execution summary after ordinary test failures. GitHub uses
`GITHUB_STEP_SUMMARY`; Azure uses `task.uploadsummary`. Publication steps have a two-minute timeout.
Provenance, selection/fallback, unit/native counts, durations, guard/cleanup, retained review/skipped
coverage and bounded failures remain visible. Passing display omits the long artifact inventory;
the original summary, manifest, JSON, native XML and complete child diagnostics remain in the artifact.

Hosted summaries link to the actual run and name the artifact to download. Relative file links become
explicit artifact paths rather than broken browser links; escaped diagnostic prose is preserved.
Display is bounded to 900 KiB with an explicit truncation notice, below GitHub's per-step limit.
Azure stages publication diagnostics before strict bundle export, so corrupt evidence cannot hide
its admission failure. No automatic interrupted-run recovery or cleanup claim is introduced.

GitHub summaries appear on the Actions run reached through a PR check's **Details** link. This adds no
PR comment or write permission. Azure Markdown appears in the run summary. These live locations still
need verification for this increment.

## Azure Tests Tab And Counts

Only the collected aggregate publishes test cases, avoiding shard/aggregate duplication. Exact
manifest-listed XML is partitioned into three native `PublishTestResults@2` tasks:

| Test run | Case authority |
| --- | --- |
| pytest | Actual Python cases with existing implementation-group/runtime identity prefixes. |
| Pester PS7 | Actual Pester cases with existing implementation-group/runtime identity prefixes. |
| Custom suites and infrastructure | One case per custom execution unit, plus explicitly recorded infrastructure errors and unresolved required reviews. |

Safe numbered XML copies are passed as exact newline-separated paths, without a repository-wide glob.
Each task merges its category, attaches the original XML and fails on failed tests, missing expected
files or failure to publish. Empty categories are omitted, not replaced with passing runs. Admission
failure fails the publisher and disables all native tasks. Blocked/cancelled work may appear skipped
in JUnit while still failing the execution gate. Unselected work has no invented testcase.

The three complete 6.3 reference bundles each contain **511 pytest + 60 Pester + 58 custom = 629
published cases** across 76 execution units. These historical replay counts do not predict the new
source's test count. Publisher regressions belong to the existing registered `ci-execution` group;
no semantic family or suite registration is added. Native stack traces and durations retain their
original XML bytes. Summed testcase duration is distinct from pipeline wall time and setup/queue cost.

The Tests tab contains automated build results. Azure Test Plans is separate manual/exploratory test
management; this phase creates no manual plan or paid resource. On a qualified run, start in Summary
for scope/status, open Tests for a failed case and stack trace, then open task logs or download the
named artifact for complete JSON and raw diagnostics. Actual hosted results and the maintainer
walkthrough remain acceptance requirements.

## Verification And Remaining Hosted Gate

Private fixtures cover passing, assertion-failed, timed-out, blocked and cancelled outcomes; native
routing/nonduplication; missing/corrupt/foreign evidence; summary write failure; UTF-8 limits;
submission versus acceptance; and Azure diagnostic retention after failed bundle export. Workflow
regressions verify aggregate-only tasks, exact outputs and failure-sensitive publication settings.

Final focused report/scope verification passes **154 cases on each OS**: Windows 26.23s and Linux
14.18s. The 25 new publisher cases remain inside the existing `ci-execution` group. Ruff check/format,
actionlint and annotation policy pass (22/22 fixtures; eight annotations in 490 eligible files).

Ignored `.tmp/ci-phase64` retains read-only publication replays of admitted 6.3 GitHub success/failure,
Azure merge/source and infrastructure smoke bundles. XML bytes/counts and original exits match
exactly. These do not rerun tests or establish hosted UI/server acceptance. Full passing display
shrinks from roughly 140 KiB with inventory to about 6.4 KiB; complete inventories stay in artifacts.
The smoke's four observed pytest XML files publish without inventing Pester/custom cases.

After confirmed publication, qualify actual successful PR aggregates on both hosts, verifying summary
attachments, native case identities/counts, failure stack traces and admitted artifacts. Use bounded
manual qualification to demonstrate assertion failure, repository child timeout, missing results and
publication failure on both hosts. Clearly label deliberate probes as qualification evidence; never
substitute them for catalog coverage or required PR success. Prefer small probes over repeated full
PR runs, isolate owned scratch, and retain failed run URLs/diagnostics.

Ordinary child timeout with a final report is publishable. Host cancellation, agent loss or a hard
deadline may stop publication despite `always()`; no cancellation upload/cleanup guarantee is claimed.
Unknown participation stays explicit. Uploading diagnostics alone cannot satisfy missing aggregate
execution. The optional Azure policy can queue a full run after each push; account for the single
slot and the already-running 6.3 documentation build before scheduling experiments. Avoid unnecessary
source replays. Phase 6.5 retains priority optimization: approximately 51-minute Azure PR timing is
unacceptable as the final operating baseline.

## Primary Host References

- [Azure result publication](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines)
  documents JUnit, explicit paths, task failure controls, attachments and the Tests tab.
- [Azure logging commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands?view=azure-devops)
  documents Markdown summary attachment.
- [GitHub workflow commands](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions)
  documents job summaries and the display limit.

**Rollback:** Restore preceding worker templates and remove the new publication invocation. Preserve
original bundles, failed receipts and optional policies; no catalog or execution contract rollback
is required for this presentation increment.
