# CI 5.1 Same-Snapshot Shadow Comparison

**Status:** CI 5.1 comparison confirmed by the maintainer on 2026-10-06. The
[modernization plan](ci-testing-modernization-plan.md#phase-51-same-snapshot-shadow-comparison)
owns acceptance. This comparison does not retire checks, activate hosted profiles or change
required-check identities. Phase 5.2-5.5 retain their distinct acceptance obligations.

## Source And Measurement Boundary

Both execution paths use committed source `1627dfecf902287b83d683234ad2b7bca8a29aad`, the accepted
CI 4.6 checkpoint. An ignored disposable checkout uses that commit and its original objects;
its clean index is verified before execution. Initial archive line-ending differences were
resolved only in the disposable checkout. No global Git trust setting was changed.
The replacement records snapshot digest
`74570f388408cee9fd6ae2baad26f32286bd49947ca21d08c8685e41ae6e8298` and captured catalog digests.

The legacy reference means the current owning standalone commands for accepted post-retirement
Phase 2 coverage, executed against this same source. It does not mean reverting implementation
files to Phase 2 or reinstating Windows PowerShell 5.1. The replacement is the repository-owned
`modernization-shadow` profile, with complete membership and no human-review waiver invented by
this measurement. Required release reviews remain owned by the later release-readiness gate.

Runs are sequential on this Windows machine, using prepared CPython 3.14.5, PowerShell 7.6.6,
Pester 6.2.0 and the pinned development/media dependencies. Owned modules, wheels and Mermaid/
Chrome resources are explicit. Nothing is installed or downloaded during test execution.
Rendering uses Node 24.15.0, npm 11.12.1, Mermaid CLI from the owned lock and Chrome 150.0.7871.24.
These are single warm local observations, not hosted throughput or statistical percentiles.

Ignored `.tmp/ci-phase51/` owns invocation timings, full diagnostic streams, setup observations
and disposable observers. `paired-source/.tmp/phase51/` owns legacy detailed JSON;
`normal-source/.tmp/phase51/new/run-b753a6d71b0e426a9256e6530c8172b7/` owns the replacement bundle.
Observer scripts are not permanent suite registration. Both disposable checkouts reference the
same original commit. The normal-account checkout avoids the trust failure described below.

## Coverage Accounting

| Boundary | Legacy reference | Replacement full profile |
| --- | --- | --- |
| Static policy | Ruff lint/format, PowerShell formatter, annotations, actionlint | Four registered policy units over captured source. |
| Shared conformance | All 21 suites in Python and all 21 in PS7 | The same 42 suite/runtime obligations and owning fixtures. |
| Cross-runtime parity | Compare retained complete baseline documents | One referee compares retained typed semantic summaries without rerunning suites. |
| Project compatibility | All 11 `full-release` checks | The same 11 owning check families, each supervised independently. |
| Implementation tests | Not part of the legacy hosted portfolios | 15 native groups plus one installed-wheel group; an additional boundary. |
| CI infrastructure | Prior checkpoints provide negative-path evidence | Mandatory native-results, catalog, scope, process and aggregate/report regressions. |

The replacement has **74 units: 4 policy, 16 implementation, 42 conformance, 1 parity and
11 compatibility**. A unit is an execution boundary, not a native test case. Raw pytest/Pester
case counts cannot be substituted for shared fixture inventory or compatibility obligations.
Synthetic media remains required implementation coverage. Extraction and installed-wheel checks
remain separate: a copied neutral framework and an installed Python distribution prove different
consumer contracts.

## Preflight Differences

The unmodified bootstrap's render check fails because npm receives the same null-file path as
both user and global configuration. npm rejects this as duplicate configuration loading. The
measurement observer uses two distinct empty owned configuration files; this is a disclosed
measurement workaround, not a source fix or evidence that unmodified bootstrap passes.
The initial restricted check records Python environment verification at **8.665s** and PS module
reuse at **3.083s**, without acquisition. Python exceeds the earlier <=5s verification goal in
this account/sample; normal-account whole-environment verification remains a remeasurement item,
not a saving inferred from the aggregate's narrower 0.547s Python preflight.

After that workaround, dependency and browser content receipts passed, but the restricted account's
headless browser smoke timed out. Normal process permissions passed the same pinned browser smoke.
The retry reused the completed dependency-content audit and rechecked browser contents/version;
its duration is not a fresh complete render environment verification benchmark.

The aggregate adapter excludes inherited Puppeteer settings and has no explicit render-environment
admission. The legacy render invocation also demonstrated a separate integration defect: Mermaid's
launch looked for `chrome-headless-shell`, which the adopted Chrome-only bootstrap deliberately
omits. Bootstrap's successful full-Chrome smoke does not prove Mermaid uses that browser. Explicit
verified executable/configuration propagation is required; downloading another browser to hide the
configuration mismatch is not the proposed remedy.

The first replacement invocation rejected the sandbox account's checkout ownership with exit 2,
zero selected units and a complete diagnostic report. Its Git isolation deliberately does not
trust the observer's inherited safe-directory setting. A second clean disposable checkout was
created by the normal execution account; it references the same accepted commit. Global Git trust
and primary repository ownership remain unchanged.

The initial legacy full profile attempted all 11 checks: eight passed; Visualization, QA and render
failed. The Visualization/QA failures arise in normalization, not a changed canonical baseline.
`normalize_string` takes the first `.tmp` component when constructing a repository-relative output
alias. Nested ignored checkouts therefore leave the actual generated relative paths unnormalized.
A disclosed in-memory nearest-owned-`.tmp` diagnostic matches **all five Visualization refresh
files and all 35 QA files** to the unchanged golden hashes. It changes no source, fixture or baseline
and is diagnostic proof, not adoption of a new normalization implementation.

The replacement formatter reports all 70 PowerShell files changed in its captured Git-blob source.
The legacy physical checkout passes: Git stores LF-normalized blobs while `.gitattributes` requests
CRLF worktree files, and the formatter compares its CRLF output with the input representation.
Resolve that boundary without rewriting guarded source bytes or weakening real formatting checks.

Installed-wheel execution cannot read the original wheel under the normal account: its owner-only
ACL belongs to the sandbox build account. This is an environment limitation, distinct from package
correctness. The child retains the PermissionError, but the adapter's missing-report classification
does not surface that root cause directly. A readable byte-identical disposable wheel can support a
focused diagnostic; no broadening of the original ACL or successful full-profile claim follows.

Actionlint's optional ShellCheck/pyflakes integration is disabled by the aggregate adapter, as
documented in [aggregate execution](CI/aggregate-execution.md). Neither helper is available in this
local reference. Local equality therefore cannot certify equivalence to their possible presence on
the legacy hosted image. Phase 6 must make that behavior explicit and preserve or separately review
the actual hosted coverage before adopting the replacement check.

## Complete Results And Cost

| Execution | Observed seconds | Result |
| --- | ---: | --- |
| Legacy static checks combined | 12.832 | All pass; Ruff lint/format, annotations, PS formatting and actionlint. |
| Legacy Python baseline | 61.839 | 21/21 pass. |
| Legacy PS7 baseline | 329.612 | 21/21 pass; complete document equals Python's. |
| Legacy full-release compatibility | 578.989 outer / 578.299 reported | Eight pass, three fail; all 11 attempted; canonical outputs unchanged. |
| Legacy paths summed, sequential | 983.272 | **16m23s**; this includes a failed render, not successful pinned-browser full acceptance. |
| Replacement modernization-shadow | 1,179.022 outer / 1,176.794 recorded | **19m39s**; 74/74 terminal, 70 passed, three failed, one error; exit 1. |

Replacement unit timing sums are **13.790s policy**, **93.536s implementation** (including the
early failed installed-artifact attempt), **78.922s Python conformance**, **350.607s PS7 conformance**,
**0.297s retained-result parity**, and **604.332s compatibility**. The remaining **35.311s** inside
the recorded run covers capture/admission, guards, persistence and other controller work; do not
call it all process startup. An additional **2.227s** separates the recorded budget cut from observer
completion, including cleanup/finalization/controller exit; it is not a pure Markdown benchmark.

The initial source/preflight/admission interval is approximately **10.013s**, estimated from the
immutable initial/first-unit record creation times minus the first unit's measured duration.
Its six supervised preparation processes total **4.553s**: private-index initialization/staging,
Python/PS/actionlint preflight and actual composed-context validation. No acquisition occurs.
The full portfolio records **80 supervised launches**; each has a guardian and target, and nested
conformance/compatibility calls add further processes. Empty-interpreter five-sample medians are
**0.029s Python / 0.201s PS7**. Startup alone does not explain the long consumer checks.

The comparison is approximately **195.750s slower** for the replacement in this observation.
Added native coverage accounts for **92.875s** of registered unit time, with further supervision,
per-suite invocation, evidence and differing rendering execution. This is not an achieved CI
speedup. The failed legacy render and unreadable replacement wheel prevent treating the timing
delta as an accepted successful steady-state cost. See the [runtime budget](ci-testing-runtime-budget.md)
for targets and acceptance limits.

All **42 detailed conformance suite rows** match exactly, including IDs, statuses, typed summaries,
ordered values, invalid-case and scale counts. The parity referee passes without additional runs.
All **374 pytest / 34 Pester** cases pass with zero required skips. All nine automatically passing
replacement compatibility checks attempt their owning contracts; eight are also passing legacy checks.
Both paths preserve the canonical-output guard. Replacement source containment/cleanup are verified,
and its exactly owned external scratch is removed. No selected unit is omitted or silently skipped.

| Expected failure / exit boundary | Retained comparison evidence |
| --- | --- |
| Invalid semantic inputs and generated scale boundaries | All 42 typed suite summaries match, including invalid-case/decision/scale counts; owning fixtures still enforce expected rejection. |
| Public CLI reporting, invalid selectors and unsafe export paths | Eight mutually passing compatibility checks retain the same failure/cleanup/determinism cases, failure codes and export hashes; only explicitly measured sizes/times differ. |
| Malformed native/aggregate evidence, empty/required-skip coverage, incorrect metadata | The mandatory 277-case infrastructure cohort passes; native result, catalog, selector and aggregate/report tests retain their negative assertions. This includes the 33 existing native-result cases, not 277 new cases. |
| Timeout, cancellation, descendants, partial streams and unsafe cleanup | Registered process/native/report regressions pass; this full portfolio itself has no timeout/cancellation and therefore is not a new real LoTM cancellation drill. Later consumer/release gates remain. |
| Independent failures do not suppress later checks | Legacy attempts all 11 despite three failures; replacement finishes all 74 despite formatter, wheel and consumer failures. Both return 1; the original untrusted source returns 2 with zero selected units. |
| Complete failure evidence versus readable presentation | Publication/JSON/XML/Markdown admission passes for a failed run. Raw owner failures survive, but generic human reasons remain a diagnosed adapter gap. |

## Difference Classification And Closure

| Difference | Classification | Evidence and owning closure |
| --- | --- | --- |
| Per-unit reports, native XML, custom JUnit, Markdown, journal, publication manifest | Intended reporting improvement | Verified complete failed bundle: 555 listed files / 3,526,423 bytes, 74 terminal units. These are publication bytes, not peak scratch/source/cache size. |
| Reporter `concise_bytes` / `detailed_bytes` and recorded elapsed values | Intended operational measurement variation | Recursive comparison finds only these fields in the eight mutually passing checks; artifact-lifecycle matches entirely. No general hash/order/ID normalization is permitted. |
| PS formatter passes physical checkout but fails all 70 captured files | Implementation defect at representation boundary | All 70 raw captured files equal LF-normalized legacy checkout bytes. Correct the adapter boundary at 5.2 without rewriting guarded source or hiding whitespace defects. |
| Visualization/QA fail in both nested checkouts; failure tree hashes differ by run path | Existing implementation defect exposed by isolation | Semantic checks pass before golden path-hash checks. Nearest-owned-`.tmp` diagnostic matches the unchanged five/35-file baselines. Correct and regress normalization at 5.3. |
| Legacy render fails with owned cache; replacement render passes | Implementation defect / unsafe environmental dependency | Owned setup lacks the requested headless-shell. With Puppeteer overrides absent, the owned package's default resolver finds an existing headless-shell in the user's global `.cache/puppeteer`, outside the adopted receipt. This resolver probe preserves normal Windows account variables; it is not a direct child-process trace. Wire admitted full-Chrome executable/configuration at 5.4. |
| npm rejects identical user/global null config files | Implementation defect | First unmodified render bootstrap fails; two distinct empty observer config files permit verification. Fix and regress bootstrap at 5.4. |
| Restricted browser smoke and first replacement Git trust failure | Environment limitations, correctly nonpassing | Normal-owned checkout and normal process execution resolve admission; exit 2/zero units was preserved. No global trust/ACL override. |
| Original installed wheel denied by owner-only ACL | Environment limitation plus prerequisite-reporting gap | Readable copies match exact SHA256; focused installed verifier passes in 7.317s. Original ACL unchanged. Preflight/classification correction belongs to 5.4. |
| Formatter/compatibility human failure reasons say only `failed`; wheel says missing report | Implementation diagnostic gap | Full owner JSON and both streams survive, but root causes need bounded promotion into human/Markdown failure text. Correct alongside 5.2-5.4 adapters. |
| Optional actionlint integrations absent locally and disabled by adapter | Unresolved hosted-policy contract boundary | Explicit Phase 6 verification/adoption decision; do not silently approve a coverage reduction from local equality. |

The focused rendering diagnostic sets `PUPPETEER_EXECUTABLE_PATH` to the verified owned full-Chrome
binary and passes both runtime renders in **13.146s**, with unchanged canonical outputs. That
matches the passing replacement render's SVG hashes and dimensions, demonstrating a narrow
configuration remedy. It neither changes the complete run's result nor
certifies the current aggregate's render admission. Bootstrap smoke, Mermaid rendering and browser
cache provenance remain separate obligations.

The original failed reporter/normalization/wheel records remain available. All mutually passing
compatibility case counts, semantic summaries, selectors, rejection cases, export hashes and
distribution/extraction inventory agree after identifying the explicitly measured operational fields.
No unexplained comparison difference remains; failed obligations still block Phase 5 acceptance.

## Slimming Candidates And Rollback

| Candidate / boundary | Measured opportunity | Remaining coverage and required failure comparison | Disposition / rollback |
| --- | --- | --- | --- |
| Batch Python native launches over the exact approved entry list | 61.354s registered versus 47.030s combined: 14.324s difference. | All 374 cases/terminal outcomes match after removing only the declared run-group prefix; file/class/case identity retained. Collection errors, later-file continuation, state leakage, mandatory family accounting and timeouts are not proved equivalent by a green batch. | Candidate only; retain nine independent groups and 277 mandatory cases until accepted proof. Restore original group/catalog/shard placement if a prototype loses coverage/isolation. |
| Batch PS native launches over six approved files | 31.522s registered versus 17.003s combined: 14.519s difference. | All 34 cases and outcomes match; no fixtures excluded. Need discovery/BeforeAll/assertion failure, cancellation and later-file continuation proof, source guards and exact per-family reporting. | Candidate only; retain six groups. Rollback is the current approved entry/group mapping and independent processes. |
| Reuse conformance results for parity | Current referee 0.297s; source baselines cost 429.528s in replacement. | Already compares retained 42 results, including typed summaries/order/counts; rejected corrupt/incomplete source evidence remains mandatory regression coverage. | Already implemented; never add a second baseline solely to compute parity. Preserve original standalone commands for diagnostics/rollback. The 429.528s is avoided hypothetical duplicate work, not a newly measured speedup. |
| Retire legacy/replacement hosted shadow duplication | This comparison's legacy path costs 983.272s. | Keep authoritative shared conformance and all 11 consumers; retire only superseded orchestration after complete local/hosted equivalence. Current failures prohibit removal. | 8.1 review only. Preserve existing workflow/check identities and standalone recipes for rollback. |
| Move repeated consumer setup/selector logic to native tests or cache immutable composition | Largest new checks: catalog 164.884s, schema 122.368s, extraction 117.928s. | These prove public CLI/export/negative/packaging contracts that helper tests cannot replace. Profile actual command/parsing work; require exact retained scenarios, failures, fingerprints and cache invalidation before changing execution. | Investigation only; **zero demonstrated saving** and no approved deletion. Restore owning CLI scenarios on any discrepancy. |
| Remove the annotation fixture-only CLI case, installed-wheel checks or extraction as apparent duplicates | No removal benchmark; startup medians do not establish safe savings. | Actual-file policy, public CLI reporting, installed distribution and neutral copied-framework consumers have different boundaries. | Retain. Repeated scenario names are insufficient removal evidence. |

Native batching differences include fewer supervisor/guard/report boundaries, not merely interpreter
startup. They are upper bounds for a design that retains current safety and logical family evidence.
Do not replace mandatory catalog membership with an arbitrary test-directory sweep. Deliberate
failure fixtures remain excluded from normal registration.

The initial Python batch used a shared system pytest TEMP tree denied to this account: 240 setup
errors, not an equivalent run or saving. Its preserved diagnostic is excluded from performance
acceptance. The corrected sample uses fresh unrelated external scratch, passes all 374 cases and
verifies scratch removal. Changing run-group XML prefixes is explicitly accounted for; comparing
only totals would have missed that identity difference.

## Acceptance Boundary

CI 5.1's inventory/comparison/classification/measurement checkpoint is confirmed. The full replacement
is **not accepted green**: the three failures, one environment error and unsafe rendering dependency
must be resolved and rerun at their owning checkpoints before 5.5/hosted adoption. The current
coverage and executable catalogs are unchanged; no test or original check is retired here.
Budget ceilings remain safety limits. The following phases must prove meaningful feedback improvement,
not simply increase timeout allowances or publish the existing slower run.

Verification of this documentation increment includes the complete publication-manifest admission,
explicit annotation validation of all four changed/new documents and all 22 policy fixtures, relative
link checks and Git whitespace/diff review. Primary tracked changes are confined to those documents;
canonical pages/templates/Seeds, QA/Visualization sources, fixtures, dependencies, tests, registries
and workflows remain unchanged. Maintainer confirmation authorizes focused commit/publication of
this comparison record and its plan/ledger/budget updates.
