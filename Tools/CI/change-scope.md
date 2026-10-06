# Git Scope And Explain-Only Impact Selection

CI 4.2 is confirmed on 2026-10-05. `scope.py` resolves comparison/provenance and captures
source bytes; `selection.py` explains impact; `explain_ci.py` connects them to the validated catalog.
Only Git reads run. No test runner, dependency installation, fetch or hosted activation occurs.
All profiles still have full effective execution membership and execution_ready false.

```powershell
# $python is the prepared development interpreter.
& $python Tools/CI/explain_ci.py --profile feature-feedback --scope local-worktree
& $python Tools/CI/explain_ci.py --profile pr-integration --scope full
& $python Tools/CI/explain_ci.py --profile pr-integration --scope local-staged --snapshot-output-root .tmp/ci/sources
# A clean checkout is required for committed/hosted modes.
& $python Tools/CI/explain_ci.py --profile pr-integration --scope committed --base origin/main --source HEAD --snapshot-output-root .tmp/ci/sources
```

## Explicit Modes And Provenance

| Mode | Comparison | Captured content / constraints |
| --- | --- | --- |
| committed | Resolved base/source merge base to complete source tip | Actual checkout must equal source and be clean; index, unstaged and untracked source changes are rejected. |
| hosted-pr | Actual target/source merge base to source tip | Executed checkout HEAD is recorded separately. Source checkout or exact two-parent target/source merge metadata is bounded; other identified merge content forces full fallback. |
| hosted-commit | Explicit base/source merge base to source | Actual executed HEAD must equal source; no invented parent/base. |
| local-staged | HEAD versus index | Index blob bytes/modes only; later unstaged and untracked files do not enter capture. Unmerged index or index drift blocks. |
| local-worktree | HEAD versus combined staged/unstaged tracked changes and nonignored untracked files | Current bytes/modes, including tracked deletions; index/untracked/content drift blocks. |
| full | No comparison or merge base | Captured worktree inventory; full eligible policy surface, with lost/not-compared deletion precision explicit. No fabricated empty changed-file proof. |

Scope is mandatory. Local/full modes reject committed ref parameters instead of silently mixing
sources. Resolved base tip, source tip, merge base, executed commit, checkout kind, snapshot kind,
index digest and SHA256 content-manifest digest are recorded. A PR source-impact list is explicitly
not the merge-tree diff; the snapshot contains the actual executed merge tree, including target-only
files. Ref/HEAD changes during resolution fail. Shallow/missing/unbounded comparison metadata falls
back to full only after the executed source snapshot is identified and captured coherently.

Unavailable source/HEAD, nonrepository roots, dirty committed/hosted checkout, unreadable source,
unmerged index, unsupported snapshot object, unsafe path or drift blocks with exit 2. No fetch is
attempted. A host may acquire missing history through its later bounded adapter; this resolver
records lost precision rather than calling unavailable history an empty successful diff.

## Git And Path Boundaries

Git commands use argument arrays, no shell expansion, optional locking disabled, no interactive
prompts, disabled fsmonitor/untracked-cache helpers and explicit no-ext-diff/no-textconv. Commits are
resolved with --verify/--end-of-options. Raw diffs and tree/index/untracked inventories are NUL-delimited;
paths are not whitespace-split. Rename/copy detection preserves both paths. Add/modify/delete/type
and executable-mode changes retain raw status/mode evidence. UTF8 decoding is strict; spaces, Unicode,
case, tabs and newlines survive parsing. Git metadata/control paths, parent segments, absolute/drive/
UNC/backslash paths and root destinations are rejected. Windows case collisions block capture.

Comparison path/status data that cannot be trusted produces full fallback on a known safe snapshot.
Current gitlinks/submodules or symlinks cannot produce a supported executable snapshot and block;
historical gitlink impact on an otherwise regular source snapshot is unbounded/full. Internal links
are also deliberately unsupported here, avoiding platform privilege-dependent materialization.
These are conservative supported-source boundaries, not proof that arbitrary Git configuration is
a security sandbox. Git reads have 30s call limits; process-tree ownership remains 4.3.

Glob grammar is case-sensitive literal segments, * and ? within a segment, and whole-segment **
for zero or more segments. Brackets, negation, regex and partial-segment globstar fail catalog/selection
validation. No semantic lookup-key normalization is applied to paths.

## Captured Snapshots And Catalog Authority

Commit/index capture reads immutable Git blobs with size admission before payload acquisition.
Worktree capture reads regular files, checks repeated content/index/untracked inventories and retains
POSIX executable modes. Per-file 32 MiB / total 256 MiB snapshot allowances fail closed; changing
these supported limits requires review and cannot silently omit large source files.

`resolve_scope(...)` returns a ci-change-scope v1 report and Snapshot object containing actual bytes,
modes and deterministic path/mode/SHA256/size manifest. Default worktree explanation writes no files.
`Snapshot.materialize(repository, parent)` requires explicitly supplied, Git-ignored owned .tmp storage,
creates a unique snapshot directory, writes only captured files and verifies exact inventory/content/
link containment. Repeated capture never overwrites an older generation or canonical source.
Snapshots do not contain .git, global dependencies or a guessed environment. Source bytes are frozen
in the captured copy; this is not an ACL-based immutability guarantee. Future execution must verify
the capture again and direct writes to owned output (4.3/4.4).

CLI index/commit modes require --snapshot-output-root so the catalog is loaded from the captured
source, not from different working-tree registration. Materialized source verification follows planning.
Worktree modes without materialization verify catalog inputs against captured bytes and recheck source/
index/HEAD after explanation. Catalog errors remain hard failures; comparison fallback cannot repair
invalid registration or substitute another revision's catalog. Planning code provenance and captured
catalog/entry digests remain separate from proof that any tests executed.

## Advisory Selection And Actual-File Policy

ci-impact-explanation v1 includes full candidates, would_select/would_omit, per-unit reasons,
per-path impact/disposition, fallback reasons and scope/provenance. effective_execution_units always
equals the full candidate list and selection_enforced is false. Status remains explained; a synthetic
reviewed no-test-impact case can set advisory_no_impact but cannot activate a no-impact hosted run.
CI 4.6/Phase 7 owns execution selection adoption.

Shared full-selection paths, unbounded candidate mapping, unknown/unmapped paths, incomplete history
and unsupported comparison statuses select the entire requested profile. Otherwise both old/new paths
are matched, transitive impact reaches a fixed point, prerequisites are added, affected comparisons
retain complete source runtime sets, and always-run groups remain selected. Ordering stays the validated
plan order. Runtime/OS requirements are not removed by a smaller advisory subset.

Policy scope is independent: every changed path retains pending-validation or pending-deletion-integrity
status. On full fallback the whole captured eligible surface is pending and deletion precision is lost.
An impact omission never labels a repository file validated. Actual validators/context/deletion integrity
remain 4.4. Unknown docs are not exempt. Current production metadata adopts no non-impact rules;
affirmative reviewed rules, no conflicting impact, independently completed policy dispositions, no
required reviews and no always-run units are necessary even for advisory no-impact eligibility.

Current broad mappings deliberately make normal feature/PR changes choose full coverage. This
checkpoint proves the mechanism using bounded synthetic mappings, not a promised reduction in this
repository's current workload. ci-scope is registered and always-run beside ci-catalog in native profiles.
Its additional 120s allowance brings the initial native/policy shard to 2160s, within the unchanged
2190s window. This is maximum admission arithmetic, not expected run time or a new hosted job.

## Evidence And Remaining Gates

Forty-two regressions (30 unit / 12 integration) cover real private Git histories, multicommit scope,
Unicode/spaces, rename/copy, source/merge provenance, deletion, staged/worktree distinction, mode changes,
ignored/untracked files, shallow history, missing refs, unsafe paths, case collisions, NUL/tab/newline
parsing, index/worktree drift, unique verified copies and selector fallback/dependency/parity/no-impact
boundaries. No production full-suite recursion or live external repository mutation occurs.
Windows/WSL native aggregates pass 230 pytest cases; unchanged PS evidence is retained.
Final local aggregate samples are 27.205s Windows / 7.233s WSL, including process startup.
This increased Git/meta-regression workload exceeds the earlier prepared Python feedback goal on
Windows; retain the goal and review fixture/Git/catalog costs at 5.1 rather than raising timeouts.

Ignored .tmp/ci-phase42/ retains aggregate reports and this checkout's local-worktree/full/materialized
explanations: advisory fallback remains full and matching captured catalog authority is verified.
Linux executable-mode proof caught a fixture that updated the index flag without changing the physical
file; it now sets both on POSIX. Worktree capture retains physical POSIX modes. Independent fixture
bytes use explicit LF, preserving rather than accidentally normalizing platform-specific contents.

Whole-run/process deadlines and descendant cleanup remain 4.3; execution adapters/policy validation
remain 4.4; durable aggregate evidence/retention remain 4.5; mandatory supervision/selector gate remains
4.6. No hosted YAML, required check, canonical content or semantic membership is changed here.

Documentation checks resolve 77 relative links/anchors; annotation policy passes 22 fixtures / 442
files without findings, Ruff checks pass and git diff --check passes. Runtime evidence uses private
fixtures and ignored local reports; no full legacy compatibility portfolio was redundantly rerun.
