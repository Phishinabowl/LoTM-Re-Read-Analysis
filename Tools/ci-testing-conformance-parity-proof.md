# CI 5.2 Conformance And Formatter Representation Proof

**Status:** Implemented, verified locally and confirmed by the maintainer on 2026-10-06.
The [modernization plan](ci-testing-modernization-plan.md#phase-52-complete-cross-runtime-conformance-and-parity)
owns acceptance. This closes the 5.1 formatter discrepancy, not the remaining consumer/render/wheel
gates or the Phase 5 full acceptance gate.

## Formatter Boundary

`Format-PowerShell.ps1` now accepts `-SourceRepresentation Worktree|GitBlob`. Worktree remains the
default: ordinary checks/fixes retain physical CRLF expectations. GitBlob compares the computed
CRLF formatter result in LF form, requires LF-normalized input and forbids `-Fix`. The parser,
token/semicolon preservation, whitespace and long-line checks remain active. Neither representation
changes captured files during a check; existing JSON result fields remain unchanged.

The controller chooses from captured provenance: commit/hosted and index snapshots use GitBlob;
local-worktree/full snapshots use Worktree. Unknown kinds fail closed. The fixed PowerShell worker
receives the explicit representation; older direct worker requests default to Worktree. Snapshot
materialization and byte guards are unchanged. The fix does not convert every captured file to CRLF
or weaken ordinary worktree policy.

The real formatter adapter passes all **70 captured PowerShell sources**, where 5.1 had reported
all 70 changed. New tests cover LF acceptance, retained physical CRLF requirements, genuine bad
spacing/separators, multiline literal preservation, nonnormalized input, parsing failure and
forbidden blob fixes. Six CLI cases also compare before/after fixture bytes.

## Parity Contract

The production referee now validates retained source status, expected suite ID, schema/count
consistency and error-free success shape before comparing summaries. Its source inventory must
contain both retained runtimes for each registered suite. IDs/errors cannot be hidden by otherwise
matching summaries. Different operational profile labels do not change semantics; all fields
inside summaries remain subject to exact typed comparison, including ordered arrays.

Negative adapter tests change suite ID, count, decision, order, error, status and JSON number type;
they also exercise failed source records and a missing runtime. Semantic mismatches fail; invalid
source evidence errors. The unchanged successful fixture with a different profile label passes.
Existing selector/parity closure, shard/report and private-controller regressions remain active.

## Evidence And Reproduction

Ignored `.tmp/ci-phase52/` retains focused JUnit/native XML, both streams, Linux observations and
the complete baseline observer's provenance, progress, results and individual supervised processes.
Observation helpers are not permanent catalog membership or replacements for public runners.

The baseline starts from committed `0cb6a8b9e0b5ea26d3adc0e7de944051b9ad53ae` plus seven explicit
working code/test overlays. Each overlay's computed blob is checked against Git's actual filtered
`hash-object` result. Its frozen snapshot digest is
`580e8a493553ba4568b6dc36739bd3f84acdcb833e65e83f9b2352e4f02c851d`.
This is documented working-change proof, not a claim that the uncommitted implementation was already
in HEAD. The final two additional negative tests and documentation followed capture; production
runtime/adapter code and all conformance inputs remained unchanged during/after the baseline.

The observer selects **44 existing catalog obligations**: the PowerShell formatter, all 21 baseline
suites in each runtime, and their production parity referee. It uses the production adapters,
aggregate execution, leases and source guards. It does not claim complete execution of the
74-unit full-verification profile or publish an invented passing full-profile bundle.

| Verification | Result |
| --- | --- |
| Windows baseline/formatter/parity | 44/44 pass in 472.154s; all 42 detailed suite rows exactly match the retained 5.1 reference. |
| Complete cross-runtime inventory | Exactly the registry's ordered 21 baseline IDs in each runtime; canonical referee passes without rerunning sources. |
| Focused public owner selection | `project-root` only in Python/PS7; one suite each, detailed row equals its baseline row. |
| Windows Python focused adapter/controller/report regression | 105 cases pass: 62 initial, two added source-failure cases, 41 reporting cases; no whole-cohort rerun to add the final two tests. |
| Windows Pester formatter | 17 cases pass, including six real child CLI scenarios. |
| Linux focused Python | The same 64 adapter/controller cases pass across the initial and two-case follow-up observations. |
| Linux Pester formatter | The same 17 cases pass using pinned PS7.6.6/Pester6.2.0. |
| Preservation and cleanup | Full frozen source guard passes with no changed paths; process containment verified; exact external baseline/focused/Linux scratch owners removed. |

Windows and Linux use their prepared Python 3.14.5 and PS7.6.6 tools, exact analyzer 1.25.0 and
Pester 6.2.0; no dependency acquisition or Desktop process occurs. Linux focused tests overlap
part of the Windows validation, so the 472.154s is correctness evidence, not an isolated throughput
benchmark or performance improvement claim. Linux's complete LoTM portfolio and the PS7 floor
are not newly certified by this focused proof.

The initial Python controller fixture omitted the real resolver's `snapshot_kind` field; its four
failures were retained, the fixture was corrected and it now asserts Worktree routing. A preparation
observer also used a nonexistent catalog `owner` key before executing tests; its empty private scratch
was removed. After the passing full baseline, the observer removed TEMP too early for its final
standalone selector probe. That failure is preserved; fresh unrelated owned TEMP passes both selector
checks. None required rerunning the full baseline or relaxing production validation.

Direct formatter recipes are in [Tooling Reference](TOOLING_REFERENCE.md#check-recipe).
Captured routing and parity behavior are in [aggregate execution](CI/aggregate-execution.md).
Public conformance commands retain their existing switches:

```powershell
& $python Tools/Conformance/run_conformance.py --profile baseline --json
& $pwsh -NoProfile -File Tools/Conformance/Run-Conformance.ps1 -Profile baseline -Json
& $python Tools/Conformance/run_conformance.py --suite project-root --json
& $pwsh -NoProfile -File Tools/Conformance/Run-Conformance.ps1 -Suite project-root -Json
```

Use pinned prepared executables and owned modules; retain full detailed results for comparison.
Normal `run_ci.py` execution routes representations automatically from scope. Full-profile/shard
recipes remain authoritative; this observer's 44-unit subset is a checkpoint proof only.

## Remaining Gates

No suite, fixture expectation, semantic family, baseline, required check name, runtime support
boundary, dependency or workflow changes here. The existing test groups discover the additional
cases; no new test group is registered. Current catalog case inventory is **390 Python / 44 Pester**,
with **293 mandatory Python infrastructure cases** (CI execution grows from 89 to 105).
Those are inventory counts; the focused observations above do not claim an additional full-native run.

The 5.1 historical report remains unchanged. This record supplies the formatter correction and
complete current semantic-parity proof. Nested output normalization and bounded failure summaries
remain 5.3; npm/browser/wheel admission and release reproduction remain 5.4. Final 5.5/full/hosted
acceptance and performance optimization remain gated. Maintainer confirmation on 2026-10-06
authorizes the focused CI 5.2 commit and dual-remote publication.

Final scoped validation passes: Ruff lint/format on all four changed Python files; physical formatting
on all three changed PowerShell files; annotation policy's 22 fixtures across 461 eligible files;
84 relative documentation links; Git whitespace/diff review. No canonical or unrelated tracked change
is present. Temporary evidence is retained under ignored owners for review.
