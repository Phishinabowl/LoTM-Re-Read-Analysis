# CI 5.7 Local Optimization And Timing Acceptance

**Status:** Implemented, locally verified and confirmed by the maintainer on 2026-10-06.
Both feature profiles pass, satisfying the reviewed conditional timing disposition. The
[modernization plan](ci-testing-modernization-plan.md) owns confirmation. Hosted adoption has not started.

## Baseline, Scope And Retained Coverage

The confirmed [5.5 acceptance record](ci-testing-acceptance-review.md) supplies the comparison:
1,093.662s sequential full, 285.973s Windows feature, 275.151s Linux feature, and complete native
cohorts of 122.277s Windows full / 131.242s Windows feature / 105.911s Linux feature.
The [5.6 consolidation](ci-testing-pressure-consolidation.md) organized review requirements without
removing executable work. Its two catalog regressions account for the increase from 486 to 488
native cases; they are not a performance concession.

The adopted implementation changes only configuration collection construction and source-byte
comparison. YAML validation and schema-pack validation instantiate the same .NET List/HashSet
types directly, retaining the original ordinal or ordinal-ignore-case comparer. No parser, limit,
validation branch, decoded-YAML cache, returned schema or command contract changes.

The canonical guard reads every protected file and compares its bytes directly with the captured
bytes, avoiding two SHA-256 computations per comparison. Snapshot/provenance/publication digests
remain SHA-256. Inventory, link/junction containment and executable-mode checks remain intact;
no timestamp/size cache substitutes for content. An existing regression now also changes content
without changing file length and restores timestamps, proving that metadata cannot hide mutation.

No native group is combined, no process is shared between groups, and no fixture, executable case,
review question, suite or required check is removed. Timeouts, cancellation, independent failure
continuation, admission limits, selection policy and hosted workflows are unchanged. Active accounting
remains 74 full units, 42 conformance obligations, eleven consumers, 54 methodology families and
17 unresolved semantic pressure reviews. Implementation inventory remains 439 pytest / 49 Pester.

## Final Measurements And Evidence

These are prepared local executions, including normal capture/preflight/reporting overhead. They
exclude dependency acquisition. Complete profiles run sequentially, without overlapping benchmarks.
Linux uses its native filesystem; Windows-mounted source timings do not substitute for Linux proof.

| Profile / cohort | 5.5 reference | 5.7 candidate | Disposition |
| --- | ---: | ---: | --- |
| Windows sequential full | 1,093.662s | 1,056.779s (17m37s) | 74/74 pass; remaining 96.779s gap to 960s retained |
| Windows feature | 285.973s | 271.451s (4m31s) | 41/41 pass; within 300s |
| Linux feature | 275.151s | 266.949s (4m27s) | 41/41 pass; within 300s |
| Windows full native | 122.277s | 125.152s | 90s goal remains unmet |
| Windows feature native | 131.242s | 125.225s | Same complete cohort; variation remains visible |
| Linux feature native | 105.911s | 105.520s | Remaining 15.520s gap to 90s retained |

Full verification is 36.883s / 3.37% faster than the retained 5.5 sample. Windows feature is
14.522s / 5.08% faster. These are observed whole-profile differences, not precision attribution
to individual edits. No Windows full-native improvement is claimed. The earlier Linux reference
overlapped an intermediate Windows run, so comparisons retain that measurement limitation.

Final full owner costs are policy 14.505s, native/installed implementation 125.152s, conformance
367.251s, parity 0.266s and compatibility 496.541s. The remaining 53.064s is non-unit overhead,
including capture, prerequisite validation, post-unit guards and publication; it is not all setup.
Unit clocks also include their pre-dispatch guard and adapter work, not only framework assertion time.

All 486 prior named native cases remain, with the two 5.6 cases added. All 42 full detailed
conformance rows match 5.5 exactly, all eleven consumers pass, and the 556-file full publication
verifies. Both feature profiles match all 20 retained fast rows, preserve all 488 current native
cases and verify their 358-file publications. Linux's 8.202s lower feature observation retains the
reference's overlapping-load limitation; no isolated Linux speedup percentage is certified.
307 protected runtime/fixture/contract/pack/project files remain byte-identical to 5.5 in the qualified
captures; the only intentional runtime implementation differences are the two collection-construction
files. These counts precede acceptance-documentation edits, including the module release note.
Each run additionally guards every captured source byte and verifies containment and external scratch removal. Existing
LoTM Visualization/QA golden expectations remain unchanged.

## Exact Source And Reproduction Boundaries

Windows full and feature capture the same 573-file working candidate over
`9c4250372de238fc5bfd71d6a69a664d7aa66753`, with snapshot digest
`450091d1ff9e289b95274581acef50b5a8edbae520b75912d9f4e773cdc1c6de`.
Linux uses a physical copy with independent synthetic Git metadata. A complete inventory audit
proves no missing, extra or changed files and the same snapshot digest before final qualification.
The final Linux execution report independently records that same digest, passes all 41 units and
verifies publication, canonical protection, containment and external scratch removal.
The synthetic Git HEAD is not the primary publication HEAD. No primary history/configuration is changed.
Evidence documentation follows these captures; executable/fixture bytes remain the qualified candidate.

Ignored `.tmp/ci-phase57/` retains commands, complete reports, JUnit, Markdown, stdout/stderr,
publication inventories, audits and profiling probes. `full-certified` and `feature-windows`
are the Windows qualification owners; `feature-proof-certified` in the recorded native Linux
workspace owns final Linux qualification. The existing [aggregate recipes](CI/aggregate-execution.md)
remain authoritative. Use the complete prepared development interpreter and its verified modules,
actionlint, framework wheel and platform-appropriate PyYAML wheel. Full also requires the admitted
render-bootstrap report. A same-version build-only environment is insufficient for CI execution.

Diagnostic failures remain separate: an incorrectly passed PowerShell array failed suite selection
before execution; the corrected invocation passed four affected suites. A restricted Windows context
had excessive render validation cost, an unreadable wheel and two formatter discrepancies. The
controller was stopped, guardian EOF cleanup verified, owned processes were absent and external
scratch was removed in its creating context. Recovery retains a failed, incomplete report.
The formatter normalized only the two edited runtime files before qualified execution.

The render store contains 30,530 dependency files and 308 browser files. A separate unrestricted
integrity/containment probe takes 7.174s / 6.847s for dependency content/paths; the restricted run
is not a certified timing sample. Cache integrity checks remain mandatory. Initial Linux selection
used a build-only environment without PyYAML and failed before tests. A later passing 571-file run
was rejected for final provenance because its synthetic index omitted `Source/.order` and
`Source/README.md`; both were already copied. Restoring those two private index entries proves the
complete 573-file digest. Neither diagnostic supplies a mixed-run aggregate pass.

## Reviewed Timing Disposition And Follow-Up

On 2026-10-06 the maintainer accepts explicit pre-hosted native/full timing exceptions conditional
on both feature profiles passing. Final Windows 271.451s / Linux 266.949s feature proof and exact-source
audits satisfy that condition. The measured native cohorts remain 125.152s Windows full / 125.225s
Windows feature / 105.520s Linux feature. The 90s native and 960s sequential full goals remain; no timeout,
required coverage, feature target or hosted target is relaxed. The maintainer confirms this checkpoint
on 2026-10-06. Phase 6 owns exact committed hosted evidence, cache transport, placement and critical-path
measurements; this local record does not activate a pipeline or close unresolved pressure reviews.

The subsequent [Phase 5.8 plan addition](ci-testing-modernization-plan.md#phase-58-linux-portability-full-comparison-and-os-placement),
confirmed by the maintainer on 2026-10-06, adds local Linux portability/full comparison and a reviewed provisional OS
matrix before Phase 6. Its implementation is unstarted. This preserves the 5.7 evidence and accepted
timing disposition; current Windows-only compatibility registration is not proof of an inherent OS
dependency. A genuinely required Windows remainder must remain explicit in any split comparison.

Phase 8.1 must revisit the measured hotspots: framework-catalog CLI compatibility (136.439s),
effective-schema CLI compatibility (100.368s), extraction (77.315s), native aggregate regressions
(21.219s), catalog regressions (17.489s), scope regressions (11.378s), and repeated startup/private
fixture preparation. Profile before changing boundaries. Any batching needs timeout/restart and
process-global contamination proof; downloads, integrity skipping, case deletion or larger timeout
ceilings cannot satisfy a feedback goal. Reconcile local/hosted wall time and resource costs, then
meet the goals or obtain a final explicit disposition before integration.

Rollback restores the four implementation/test files together to `9c42503` and requalifies affected
profiles. Preserve the 5.5/5.6 evidence and semantic mappings. No old runner/check has been retired.

Final static verification passes Ruff and the owning PowerShell formatter, annotation policy
(22/22 fixtures, 468 files, eight valid annotations), all 105 checked documentation links and
`git diff --check`. The four final implementation/test files exactly match the qualified captures;
only evidence/documentation changes follow qualification. No extra full rerun is required for those edits.
