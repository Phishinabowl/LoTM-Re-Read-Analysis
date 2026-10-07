# CI 6.4 Hosted Markdown And Test Publication

**Status:** First implementation increment is confirmed and dual-published as `117a457`. GitHub's
first full run publishes complete failure evidence; Azure run 48 passes all 76 units and publishes
652 verified server cases. Azure summary attachment acceptance remains open. Scoped readiness
correction, explicit named Azure summary attachments, native-case diagnostic display and manual
qualification transport are prepared locally, uncommitted for review.
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
`GITHUB_STEP_SUMMARY`; the prepared Azure transport uses explicitly named `task.addattachment`
commands with type `Distributedtask.Core.Summary`. Publication steps have a two-minute timeout.
Provenance, selection/fallback, unit/native counts, durations, guard/cleanup, retained review/skipped
coverage and bounded failures remain visible. Passing display omits the long artifact inventory;
the original summary, manifest, JSON, native XML and complete child diagnostics remain in the artifact.

Hosted summaries link to the actual run and name the artifact to download. Relative file links become
explicit artifact paths rather than broken browser links; escaped diagnostic prose is preserved.
Display is bounded to 900 KiB with an explicit truncation notice, below GitHub's per-step limit.
Azure stages publication diagnostics before strict bundle export, so corrupt evidence cannot hide
its admission failure. No automatic interrupted-run recovery or cleanup claim is introduced.

GitHub summaries appear on the Actions run reached through a PR check's **Details** link. This adds no
PR comment or write permission. Azure's documented summary attachment location is the run's
Extensions view; the actual tenant UI still needs the maintainer walkthrough. Successful submission
tasks are distinct from independently verified server attachments and rendered views.

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
14.18s. The 23 new publisher cases remain inside the existing `ci-execution` group. Ruff check/format,
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

## First Hosted Execution And Scoped Recovery

At exact source `117a4574a5e22d9cd76e31ad0eab59a5eb921061`,
[GitHub shadow 37600129773](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37600129773)
collects all 76 units: 75 pass and one native process group fails. All ten worker summary steps succeed,
including failed shard and aggregate; the workflow remains failed. The admitted aggregate preserves
**534 pytest cases (one failed), 60 Pester cases and 58 custom cases**, exact XML and a publication
receipt retaining execution exit 1. Canonical/source guard and cleanup are verified. Original
[GitHub CI 37600129800](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37600129800)
and annotation policy pass. This is real failure-transport evidence, not successful profile acceptance.

The failing existing process test used a 0.8-second lease to prove forced termination. Hosted cold
launch consumed that lease before the target started, correctly returning `blocked`, not `timed-out`.
The prepared test correction requests cancellation only after the child publishes readiness with its
signal handler installed, then proves forced termination and process disappearance. Dedicated timeout
tests retain whole-lifetime deadline coverage. No supervisor behavior or production deadline is changed.
The adjacent graceful-exit fixture's identical 0.5-second startup assumption uses the same readiness
helper; its graceful/forced and keyboard-interruption assertions remain covered, without adding cases.
The initial hosted summary exposes only the native group's generic `failed` excerpt. The prepared
publisher improvement adds actual failed native case names and bounded message/stack excerpts directly
to hosted Markdown, preserving raw XML bytes and complete diagnostics in the artifact.

Optional policy 4 dispatches [Azure run 48](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=48)
at merge `4debafd1082ceab4f2656236717935e0a067301a`, same source/framework target. Completed native
policy/infrastructure and all remaining shards pass: **76/76**, complete admitted aggregate,
unchanged canonical/source guard and verified cleanup. Azure's actual completed test runs **2, 4, 6**
contain **534 pytest, 60 Pester and 58 custom cases**, all passed. Independent API comparison matches
every compound identity (automated test storage/class plus name) to original JUnit, with no duplication.
Displayed titles retain testcase names; runtime/group prefixes are preserved in automated test storage,
and runtime categories have separate test runs. These are server results, not inferred upload counts.

Queue-to-finish is **53m43s**, including native result publication. This remains unacceptable as a
steady-state baseline and does not relax 6.5's priority timing gate. All summary submission tasks
succeed, but exact Build and Distributed Task attachment APIs still return no summary attachments.
Thus Azure Markdown server/UI acceptance remains open. The prepared transport uses the documented
explicit `task.addattachment` command and distinct safe names, including multiple probes within one
task record; live verification must establish acceptance rather than claiming the alias's missing
attachments are already fixed. The older documentation build 47 is cancelled, without success credit.

## Bounded Manual Qualification Increment

[`publication_qualification.py`](CI/publication_qualification.py) owns four deliberately isolated
failure probes and a passing recovery control. They are selected through the existing shadow
workflow/pipeline's new optional `publication_qualification` parameter (`none`, `passing`, `failures`).
The default is `none`; GitHub PR and Azure policy PR execution retain the entire catalog profile even
if qualification inputs are supplied. A qualification job requires manual execution and corroborates
the exact checkout against host metadata. No new pipeline resource, policy, required check or schedule
is introduced. Private fixture membership is owned by the helper, never the host YAML or PR catalog.

| Probe | Concrete evidence |
| --- | --- |
| Assertion | One real pytest assertion and one real Pester 6.2.0 assertion fail, retaining their original native stack traces and group/runtime identities. |
| Timeout | An owned Python child sleeps beyond a five-second lease; process supervision proves timeout and cleanup, and custom XML records an error. |
| Missing result | The fixture's complete execution evidence is retained but its exported worker bundle is deliberately withheld; admission fails with no invented published cases. |
| Publication failure | A passing control's admitted staged XML copy is withheld; the actual native Azure result task or GitHub upload action must reject its exact missing input. Original execution evidence stays intact. |
| Recovery | Real pytest and Pester controls both pass with original native XML and no duplicate successful custom case. |

`failures` produces an intentionally failed qualification run; successful diagnostic upload must not
make it green. Its native Azure test runs are explicitly titled `QUALIFICATION`. `passing` is a separate
green recovery run. All fixture code and captured streams live in ignored owned scratch; none enters
normal native discovery or adds a permanent story/scenario family. Process requests use a small
environment allowlist so host/API credentials are not persisted in guardian evidence.

The manual jobs provision pinned Python development and PowerShell development dependencies only,
with no rendering/browser/media setup. Job ceiling is 12 minutes, bootstrap timeout five minutes,
assertion/control leases 30 seconds, timeout lease five seconds, and owned termination/cleanup reserves
remain enforced. Expected fixture failures do not prevent later probes or diagnostic upload. An
unexpected launch/cleanup failure blocks acceptance and is not reclassified as an expected fault.

Local working-tree proof runs real pytest/Pester passing and failing controls, observes exactly one
case per runtime with the expected exit, and verifies tracked-source guard and process cleanup. This
is distinct from hosted acceptance. Permanent helper meta-regressions stay in the existing
`ci-execution` group; they require no PowerShell installation in Python's routine regression lane.
Publish this prepared increment only after confirmation, preserve the current Azure run's evidence,
then qualify both manual modes on both hosts and requalify successful current-source PR publication.

Final follow-up verification passes **210 focused cases per OS** (Windows 40.53s; Linux 25.24s),
including both readiness-based termination fixtures. Eleven additional cases versus the first
publication increment cover manual qualification, native failure display and safe distinct attachment
names within existing registered groups. Real local pytest/Pester controls pass/fail as intended,
with stable published Pester identities and verified source/process guards. Ruff, actionlint,
annotation policy (22/22 fixtures; eight annotations in 493 files), relative document links and
diff hygiene pass. No complete local portfolio rerun or additional full source replay is substituted
for the pending hosted qualification.

**Rollback:** Restore preceding worker templates and remove the new publication invocation. Preserve
original bundles, failed receipts and optional policies; no catalog or execution contract rollback
is required for this presentation increment.
