# CI 6.4 Hosted Markdown And Test Publication

**Status:** Implementation increments are confirmed and dual-published as `117a457` and `849b8a6`.
Bounded failure and recovery controls are qualified on both hosts. Azure failure run 50 stores four
exact-byte Markdown attachments and three independently verified failed cases; recovery 51 stores
one exact-byte summary and two passing native cases. Current-source GitHub and Azure PR qualification
both pass 76/76 units and 663 unique cases. Azure run 49 stores ten Markdown attachments and exact
aggregate-only native results. The maintainer confirms Tests and Markdown are both visible in the
actual tenant UI for failure run 50. The published 6.4 implementation has complete qualification
evidence. The subsequently requested combined Azure report is confirmed and dual-published as
`5513fa7`; its actual hosted presentation is still unqualified. A reproduced interpreter-handoff
correction is prepared locally and remains uncommitted for review.
First-source Azure run 48 passes all 76 units and publishes 652 verified server cases. Entry is
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

At the qualified `849b8a6` checkpoint, every worker publishes its summary after ordinary test failures. GitHub uses
`GITHUB_STEP_SUMMARY`; the Azure transport uses explicitly named `task.addattachment`
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

## Confirmed Follow-Up And Bounded Hosted Evidence

Maintainer confirmation publishes the ten-file follow-up as
`849b8a6f05ee53881fca2df89f5b9ba3e58179cf`. GitHub and Azure branch references agree with HEAD;
the push uses only the established dual-destination `origin` workflow. No additional policy,
required check, catalog member or canonical content changes.

[GitHub failure qualification 37610082285](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37610082285)
executes all four probes. Assertion and timeout execution exits are 1; missing exported evidence
fails admission; the actual upload action rejects the deliberately missing publication input.
The job remains failed after successful diagnostic artifact upload. All four summaries are written
to the host summary file, including the missing-result diagnostic; exact original manifests, source
guards and process cleanup are independently verified. Native failure display includes real pytest
and Pester assertion details. No missing or deliberately withheld publication case is credited.

[GitHub recovery 37610361502](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37610361502)
passes its real pytest and Pester controls. Both manual runs skip normal plan/shard/aggregate jobs;
these controls are qualification evidence, not substitutes for PR coverage.

[Azure failure qualification 50](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=50)
finishes intentionally failed in 3m05s queue-to-finish, with 2m26s execution. Exact server test runs
8, 10 and 12 contain one failed pytest assertion, one failed Pester assertion and one failed timeout
case. Their compound storage/name identities and outcomes exactly match original admitted XML;
all have error messages, and native assertion stack traces remain available. Native result tasks
fail on those cases, the separate task fails on its exact missing publication input, and the final
diagnostic artifact upload still succeeds. Missing results create no fabricated test case.

Both Build and Distributed Task attachment APIs report **four** Azure summary attachments with
distinct names. Downloaded server bytes match all four admitted summaries exactly: assertion,
timeout, missing-result diagnostic and passing execution preceding deliberate publication loss.
This establishes actual server acceptance of the explicit named transport. It does not claim the
old alias's missing attachments have been retrospectively recovered or establish rendered UI
appearance by itself. In the walkthrough, the maintainer explicitly confirms both Tests and
Markdown are visible in the actual Azure UI. Tests supplies individual cases, durations and failure
details; Markdown supplies scope and overall results; task logs and the artifact preserve complete
JSON/XML and child diagnostics. Automated build results remain separate from manual Test Plans.
Ordinary child timeout is publishable, while host cancellation or agent loss may interrupt upload.

[Azure recovery 51](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=51)
passes its real pytest and Pester controls. Server test runs 14 and 16 contain exactly two passing
cases matching original XML identities; no custom successful case duplicates them. The server's
single Markdown attachment exactly matches the admitted summary bytes. Original manifests, tracked
source guard and process cleanup are independently verified. Execution takes 2m08s, with 4m52s
queued beforehand (7m00s queue-to-finish); queue delay is distinct from test/setup cost.

[Current-source GitHub PR shadow 37610038443](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37610038443)
passes all nine execution shards and its aggregate at merge `f463edf9103445914e3f9bb9327b88d3bd4907fe`,
source `849b8a6`, unchanged framework target. Independent manifest/XML verification proves **76/76
units and 545 pytest + 60 Pester + 58 custom = 663 unique passing cases**, with no failure, error,
skip or duplicated case. Complete publication, exact source provenance, canonical/source guard and
process cleanup pass. All ten worker summary steps succeed, and the admitted aggregate preserves
execution exit 0. The corrected infrastructure shard passes all four groups (392 pytest cases,
including 45 process cases). Existing required GitHub CI 37610037777 and annotation policy
37610031973 pass.

[Azure policy run 49](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=49)
completes successfully at merge `5f5fdcd2c6f14abc54787794594d4678efb8194e`, same source and target.
All eleven jobs succeed, including nine execution shards and aggregate. Independent complete-manifest
and original XML verification proves **76/76 units and 663 unique passing cases**, with canonical/source
guard and cleanup verified. Actual server test runs **18, 20 and 22** contain exactly **545 pytest,
60 Pester and 58 custom cases**; every compound storage/name identity and outcome matches original XML.
Selected unit identities and framework target agree with the successful GitHub reference; each host's
distinct merge commit is retained rather than pretending the commits are identical.

All ten summary tasks and three aggregate-only native result tasks succeed. Both attachment APIs
report ten named summaries, whose actual stored Markdown is downloaded; the aggregate's 6402 bytes
match the admitted summary exactly. Together with bounded failure/recovery and the maintainer's UI
walkthrough, this completes the 6.4 qualification evidence. Checklist closure awaits final confirmation.

Queue-to-finish is **56m53s**; summed job execution is **49m37s**, including provisioning and publication.
Azure's single hosted slot interleaves manual runs 50/51 with run 49, so its elapsed time is not an
uncontended performance baseline. Preserve job/queue costs separately for the unchanged 6.5 timing
gate; this long runtime is not accepted as steady-state operation. The aggregate summary's 3.267-second
duration is the collection operation, not the full pipeline duration or summed testcase execution.

Final follow-up verification passes **210 focused cases per OS** (Windows 40.53s; Linux 25.24s),
including both readiness-based termination fixtures. Eleven additional cases versus the first
publication increment cover manual qualification, native failure display and safe distinct attachment
names within existing registered groups. Real local pytest/Pester controls pass/fail as intended,
with stable published Pester identities and verified source/process guards. Ruff, actionlint,
annotation policy (22/22 fixtures; eight annotations in 493 files), relative document links and
diff hygiene pass. No complete local portfolio rerun or additional full source replay is substituted
for the completed hosted qualification. The closeout adds documentation only; no new runtime suite
execution is needed for these evidence edits. Phase 6.5 and selective event activation remain unstarted.

## Ordered Azure Report Refinement

The maintainer requests predictable Extensions ordering and selects one combined report after review
of Azure's documented attachment command, which exposes name/type but no display-order property.
Do not claim numbered separate attachment titles establish sorting. This local refinement composes
the aggregate first, followed by expandable `<details>` sections in the repository catalog's explicit
shard order. Display numbers indicate reading order, not execution/completion order. Actual Azure
rendering of these sections remains a hosted acceptance check; deterministic content order does not
by itself prove the tenant supports the expand/collapse presentation.

Normal Azure shard workers retain their admitted summary in the individual shard artifact and emit
no summary attachment. The aggregate publishes the single combined report. GitHub's existing worker
summaries and manual qualification probes are unchanged. Every included shard requires verified final
publication, matching profile/commit/plan and original report envelope. Duplicate, corrupt, foreign or
unknown evidence is rejected; an admitted aggregate requires the exact collected shard-owner inventory.
Failed aggregate admission emits its honest failure diagnostic without loading the full catalog;
individual shard evidence stays in artifacts. Composition rejection still attempts a visible
diagnostic attachment and returns failure. No missing
coverage is invented, no native XML is regenerated and test publication remains aggregate-only.

The combined display must fit the existing 900 KiB allowance; oversized composition fails visibly
rather than cutting an expandable section or silently hiding failure diagnostics. Original evidence
and individual reports remain in artifacts. A hard cancellation/agent loss can still interrupt final
publication; artifact/log retention does not imply that the aggregate ran successfully.

Local report regressions pass **89 cases per OS** (Windows 13.84s; Linux 10.12s), including ordering,
failure/missing evidence, duplicate/foreign/corrupt rejection, display bounds, Azure-only shard retention
and visible composition-failure diagnostics. Read-only replay of run 49's nine actual shard bundles
produces **104914 bytes**, with all nine sections in catalog order and all 19 admitted XML files
preserved. Ruff and diff hygiene pass. No fresh hosted acceptance or additional full portfolio run is
claimed for this unpublished refinement. After confirmation, use a bounded Azure profile to qualify
the single attachment and rendering, and observe the next ordinary PR aggregate for the complete
nine-section presentation; preserve run 49 as the accepted preceding publication evidence.

**Publication and interpreter correction:** Confirmation publishes the four-file increment as
`5513fa7316bed71cf80ff027f1826384da2f784d`, with a clean tree and exact four-reference parity.
Azure bounded infrastructure qualification 53 and automatic PR run 52 are queued on this source.
Before acceptance, a local `python -S` reproduction exposes that full catalog construction imports
the compatibility/runtime owners and requires PyYAML. The existing Azure publisher step invokes the
bare setup interpreter rather than the verified development environment. Runs 52/53 are cancelled
to avoid consuming hosted minutes on an unqualified source; no successful qualification is credited.

The prepared correction passes `Bootstrap.python` into the publication task, uses that existing
verified executable when available, and retains bare-Python diagnostic fallback after setup failure.
Shard-only artifact retention does not load the full catalog; failed aggregate admission can emit
its summary with no site packages. A real `-S` CLI regression proves the latter, and workflow coverage
checks the prepared-interpreter handoff. **91 report cases pass per OS** (Windows 11.37s; Linux 10.06s).
The correction is uncommitted, awaiting confirmation before retrying bounded Azure publication and
the actual Extensions rendering check. Original run 49 and the bounded failure/recovery evidence
remain intact; GitHub publication has no new catalog dependency.

**Rollback:** Restore preceding worker templates and remove the new publication invocation. Preserve
original bundles, failed receipts and optional policies; no catalog or execution contract rollback
is required for this presentation increment.
