# Owned Process Lifecycle (CI 4.3)

CI 4.3 is confirmed on 2026-10-05. `process_supervisor.py` supplies the local process
primitive, lifecycle budget admission and synthetic regression coverage. Existing runners and hosted
workflows retain their execution behavior. Layer adapters/aggregate execution belong to 4.4;
durable report publication belongs to 4.5. No catalog profile is execution-ready yet.

## API And Ownership

CI 4.6 adds a [mandatory regression gate](regression-gate.md) and a 64 MiB combined stdout/stderr
monitoring threshold. Exceeding it yields evidence-limit, owned-tree termination and retained bytes;
it is not a hard filesystem quota and may overshoot during a write/poll/termination interval.
Small-threshold fixtures prove each stream and subsequent independent recovery. The optional
primitive argument capture_limit_bytes exists for fixtures; catalog/CLI overrides are not adopted.

`run_process(arguments, cwd=..., env=..., output_parent=..., lease=..., termination=..., cleanup=...,
cancel=...)` requires an argument list with an absolute executable, existing explicit directories,
an explicit environment dictionary and an admitted finite monotonic `Lease`. No shell, runtime
installation or executable search is performed. Directories cannot traverse symlinks/junctions.
The caller must own the output parent; the primitive creates a unique `process-<uuid>` child and
never removes previous or unrelated destinations. Production adapter admission will confine this
parent to its run-owned storage. Tests use pytest-owned temporary parents.

The caller starts a separate Python guardian using its current interpreter in isolated mode. Only
the caller owns the guardian's stdin writer. A cancellation message, Ctrl+C or pipe EOF interrupts
the owned tree. EOF also detects a hard-killed caller. The target gets null stdin and does not inherit
the control pipe. The explicit environment reaches both guardian and target; arguments/environment
travel through the private pipe, rather than a persisted invocation file. Windows launches are hidden.

| Host | Concrete mechanism | Stop and independent verification |
| --- | --- | --- |
| Windows 10+/Server 2016+ | Unnamed Job Object with kill-on-last-handle-close and no breakaway permission; atomic `PROC_THREAD_ATTRIBUTE_JOB_LIST` creation and explicit standard-handle list. Ownership failure cannot start an uncontained target. | No shared console is assumed, so graceful console signaling is explicitly unsupported. TerminateJobObject forces the owned tree. Verify job active count, root exit and retained member process handles, checking membership before retaining handles. Closing the guardian's private job handle is an additional crash safeguard. |
| Linux (including WSL) | `start_new_session=True` establishes the root process group; guardian becomes a child subreaper before launch. `/proc` verifies live group membership; exited adopted descendants are reaped. | SIGTERM to the group, bounded grace period, then SIGKILL if needed. Verify no live group members remain. Zombies cannot execute/write and are distinguished from live members. |

An empty tree is never signaled by its old PID/group ID. Windows member handles preserve process
identity; membership is checked before accepting an opened handle. Later unrelated children and
their artifacts survive. A root exit alone does not finish a unit while its group/job has live descendants.

Linux process groups contain ordinary inherited descendants, not programs that deliberately detach
into a new session/group. This primitive is for approved repository tools, not a security sandbox.
Adapters needing stronger containment or tools that detach must block until their ownership route is
proved; no PID-name search or broad host cleanup substitutes for ownership. Other POSIX platforms
currently fail preflight rather than claiming an unverified backend.

Mechanisms follow [Microsoft's job-object contract](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[atomic job/handle attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)
and [Python's process-session API](https://docs.python.org/3/library/subprocess.html).

## Budgets And Cancellation

`RunBudget(total, termination, cleanup, finalization)` uses a monotonic clock. All values must be
finite and positive; reserves must leave an execution window. `admit(unit_seconds)` returns a lease
only when the whole unit allowance fits before termination/cleanup/finalization reserves. A later
unit without an allowance is blocked, not silently shortened or counted as executed.

`Lease.nested(seconds)` clamps an inner deadline to its parent's deadline. A unit lease begins before
guardian startup and covers its root and descendants. `Lease.verify()` must also be used by the owning
adapter after parsing/verification; these operations cannot restart the unit clock. The process
primitive records late caller collection as timeout. Adapter result work, run cancellation propagation
to planned units and aggregate exits are connected in 4.4, not inferred from this API.

On timeout/cancellation, graceful termination where supported and forced cleanup have separate bounds.
A final exceptional guardian watchdog reserves part of the existing cleanup window for bounded
guardian termination/kill waits, without restarting the clock. Cancellation tightens that window to
termination/cleanup reserves from the cancellation request. Missing records or unverified cleanup
produce errors; report publication retains its own reserve.
No successful upload can convert a timeout or cleanup failure into success.

The guardian handles SIGINT/SIGTERM and pipe EOF. A hard-killed caller is tested on both OSes.
Hard-killing the Linux guardian itself, deliberately escaping its group, host shutdown and disk failure
cannot guarantee completed cleanup/report publication. A Windows guardian kill closes its last job
handle, but cannot promise a final report. The caller reports missing/unverified evidence as an error;
4.5 owns recovery/publication proof. No host-wide process cleanup is attempted.

## Diagnostics And Process Results

Target stdout/stderr go directly to separate binary files, avoiding pipe backpressure and reader-thread
deadlocks. Every byte written to those handles remains in `stdout.bin`/`stderr.bin`; there is no silent
output truncation. This is not a disk-quota guarantee. `guardian.bin` retains guardian diagnostics.
Routine presentation contains byte counts and at most a 2048-byte tail per stream with replacement
decoding for malformed UTF-8. Failure analysis uses the complete files.

`ownership.json` records guardian/root PIDs and backend after ownership. `process.json` records the
guardian's terminal process result; the returned record additionally covers caller collection timing,
directory and bounded diagnostics. These local files are retained even when the caller disappears.
They are not yet atomic authenticated aggregate manifests or the final reporting contract.

The envelope is `ci-owned-process` v1. States are `exited`, `timed-out`, `cancelled`, `blocked` or
`error`; original child exit is preserved when known, otherwise null. `exited` means a process tree
finished, including a nonzero child exit. It never claims tests passed or asserts coverage. Launch,
timeout, cancellation, budget and cleanup classifications remain distinct; cleanup includes graceful
route, whether force was needed and verified termination. Failure to launch the guardian starts no tree.

## Local Verification And Registration

```powershell
# Use the development interpreter recorded by bootstrap; no dependency acquisition here.
& $python -m pytest Tools/Tests/Python/test_ci_process.py -q
& $python Tools/CI/plan_ci.py --profile pr-integration --shard-plan pr-integration-initial
```

The `ci-process` group is the fifteenth implementation group / fifty-third logical unit. It runs
after ci-scope, has a 30-second deadline and is always-run in native profiles. Source manifests
include both supervisor and Windows backend. Initial native/policy allocation becomes 2190 seconds,
using the existing ceiling without increasing it; its lifecycle total is 2400 seconds. Further
registration needs placement/deadline review rather than silently raising the host ceiling.

Thirty-six regressions (27 unit / 9 integration) cover safe arguments/environment/cwd, run reserves,
nested deadlines and result verification, pre-cancellation/budget blocking, ownership/launch errors,
cleanup failure, binary noisy output, hung roots/grandchildren, root exit before descendants,
cancellation/Ctrl+C, hard caller termination, unrelated-process preservation, retained artifacts,
graceful/forced routes and recovery. Private fixtures launch only synthetic Python children. No live
LoTM validation, rendering, conformance migration or recursive full-suite launch occurs inside them.

Windows/WSL native totals and timings are recorded in the [coverage ledger](../ci-testing-coverage-ledger.md).
Later gates still own real runner integration, canonical/snapshot guards, complete adapter results,
incremental/atomic reporting and hosted lifecycle verification.
