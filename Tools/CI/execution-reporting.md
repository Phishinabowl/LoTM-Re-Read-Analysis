# Execution Reports And Artifact Lifecycle (CI 4.5)

CI 4.5 is confirmed by the maintainer on 2026-10-06. The explicit local runner records one result model and derives
detailed JSON, concise JSON, Markdown and JUnit from it. Existing standalone conformance/compatibility
detailed JSON and validation-run-summary v1 remain unchanged. Hosted summary/upload tasks and
publication receipts remain Phase 6.4; local publication admission is available now.

## Files And Authority

Each invocation allocates a fresh run owner under the approved repository `.tmp` output parent.
No existing run is overwritten. Files are UTF-8 without BOM, LF and a final newline; original raw
native XML, phase reports and child streams remain separate artifacts in their original encoding.

| File | Meaning |
| --- | --- |
| `events.jsonl`, `records/*.json` | Sequenced run/plan/unit/terminal events pointing to atomic, hash-bound records. Each unit's diagnostic artifacts are retained before its terminal event is flushed. |
| `report.json` | Detailed ci-execution-report v1; complete means intact final recording, not successful tests. |
| `summary.json` | ci-execution-summary v1: bounded failure excerpts, unit/native counts, guard/cleanup, duration and detailed-report location. This is a separate contract from legacy validation-run-summary v1. |
| `summary.md` | Common human view: provenance, selection/fallback, unselected/blocked coverage, durations, native counts, retained reviews, guards, cleanup, every failure and artifact links. |
| `custom.xml` | JUnit cases for registered custom units and clearly labeled infrastructure errors/reviews. |
| `units/*/publication.xml` | Existing native cases with stable group/runtime identities, without a duplicate successful group testcase. Raw XML and phase evidence remain available. |
| `publication-manifest.json` | Exact file lengths/digests and JUnit file identities/counts; no repository-wide upload glob. |
| `finalized.json` | Last atomic completion marker, binding the manifest. Its absence means publication has not been admitted. |
| `finalization-failure.json` | Best-effort detailed failure record when projections/manifest finalization fail. This is diagnostic evidence, not a completed publication bundle. |

Atomic writes use an exclusive temporary file, flush/fsync and same-directory atomic no-clobber
installation. Existing foreign files, hardlinked replacement targets, outside paths, symlinks and
junctions are rejected. Concurrent invocations have different owners. Original assertion outcomes
never change because a later projection fails; the aggregate gains a report failure and exits nonzero.
Failure to write any evidence still emits stderr and returns nonzero. No successful upload can
override the execution exit recorded in the manifest.

## Commands

Normal [local execution](aggregate-execution.md#local-commands) now produces all projections.
`--json` selects detailed stdout; `--summary-json` selects the new concise contract, with identical
execution membership. Normal output includes status/counts and bounded failures with the evidence path.

```powershell
# Verify every expected file and XML count before a later hosted publication step.
& $python Tools/CI/report_ci.py --run $runDirectory

# After the original supervisor has stopped: recover into a new sibling owner; exit is 1.
& $python Tools/CI/report_ci.py --run $interruptedRunDirectory --recover
```

Both commands require a run beneath this repository's `.tmp`; `--root` supports an explicit repository.
Verification returns zero for an intact evidence bundle even when its tests failed, allowing failure
artifacts to be uploaded. The host must separately preserve `execution_exit_code` and fail on upload
failure. Recovery is evidence inspection, not test resumption, process termination or scratch cleanup.

## Native And Custom XML

Custom statuses map passed to a successful case, failed to failure, error/timed-out to error,
blocked/cancelled/skipped to skipped with explicit reasons. Selected blocked work still makes the
supervisor fail; the Tests tab's skipped count cannot establish a passing gate. Unselected work gets
no testcase and remains visible in selection/Markdown. Run-level errors have ci-infrastructure cases.
Retained required reviews remain explicit skipped review cases until their acceptance gate.

Each conformance suite/runtime, compatibility referee check, parity comparison or policy unit is
one custom case. No assertion counts are invented. Native successful/assertion-failed groups publish
their actual pytest/Pester cases once. Group-level timeout, cancellation or contract errors get
separate infrastructure evidence. Syntactically valid partial native XML may publish only observed
cases, with `partial: true`; unknowable selected native counts remain null. Invalid partial XML is
retained diagnostically and excluded from the XML upload list. XML controls are replaced only in the
XML presentation; complete original diagnostics remain in JSON/streams.

JUnit is the adopted interoperable format for GitHub/ADO and does not require a second NUnit copy.
This checkpoint activates no hosted workflow or check-name change. Host adapters must use the exact
manifest paths, publish after ordinary failures, and independently report publication failures.

## Interrupted Runs And Recovery

Events flush after each atomically persisted record. Recovery validates sequence numbers, record
digests, selected unit ownership and artifact digests; a final torn journal line is ignored. Earlier
corruption, duplicate/foreign units or changed artifacts fail admission. Completed results survive;
units without durable terminal evidence become blocked with zero known attempts. Recovery keeps
unknown child exit/deadline/runtime participation null rather than reconstructing unrecorded metadata.
It always
records complete false, failed exit 1, unknown source guard and unverified cleanup, even if all durable
unit results passed. It does not claim how far an interrupted child actually ran.

A hard supervisor/OS/host kill can prevent final events, projections, cleanup or upload. The journal
only proves bytes already flushed before that interruption. Whole-machine power loss durability is
not claimed. Recover only after the original owner is no longer writing; no automatic deletion or
live-owner takeover is implemented. A recovered bundle remains partial and cannot satisfy a required
execution/shard gate. Success/failure evidence is retained until an explicit later retention policy
removes its exact owner; this checkpoint adds no broad cleanup command.

## Verification

Private regression fixtures exercise status mapping, native nonduplication, partial native timeout/
cancellation, deterministic counts, UTF-8/newlines/escaping, bounded presentation with complete JSON,
concurrent owners, corrupt/stale/missing/foreign evidence, failed projections, unconfined/linked paths,
and interrupted recovery. A real isolated Python writer is killed after its journal flush and recovered
without inventing termination/cleanup proof. Runtime and profile evidence is recorded in the
[coverage ledger](../ci-testing-coverage-ledger.md) and [implementation plan](../ci-testing-modernization-plan.md).
