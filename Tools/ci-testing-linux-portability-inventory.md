# CI 5.8.1 Linux Portability And Dependency Inventory

**Status:** Read-only executable inventory and bounded qualification proposal on 2026-10-06,
confirmed by the maintainer on 2026-10-06. Inspected clean checkout: `1179913f55c3d1bc0da8f49b29a426b33c159466`,
`architecture/ci-testing-modernization`. The [plan](ci-testing-modernization-plan.md) owns closure.
No executable, registry, dependency, workflow, canonical content or baseline is changed here;
no compatibility suite or timed full run is launched. Documentation and ignored inspection records
are the only writes. The accepted [5.7 evidence](ci-testing-local-optimization-review.md) remains intact.

## Confirmed Admission And Evidence Boundary

[Catalog loading](CI/catalog.py) assigns all compatibility descriptors `os: [windows]` at external
owner import. [Coverage metadata](CI/Data/coverage-metadata.json) has no OS field and its closed
schema rejects adding one today. The [compatibility registry](Compatibility/compatibility.json)
owns eleven ordered checks and profiles, without OS eligibility. Its runner finds Python and PS7,
uses `pwsh -NoProfile`, and has no blanket Windows execution gate. Thus current catalog restriction
does not establish an inherent dependency for any of the eleven checks.

The complete current Windows reference is **74 units**: four policies, nine pytest groups, six
Pester groups, one installed-artifact unit, 42 conformance variants, one full-baseline parity unit
and eleven compatibility checks. All 74 IDs and Windows/Linux plans were reconciled read-only
against the 5.7 report; eleven compatibility units are blocked on Linux by registration.

The existing 41-unit Linux feature proof contains **40 identical full-profile IDs** plus
`parity/conformance-fast::referee`. Full uses `parity/conformance-baseline::referee` instead.
Remaining full qualification is therefore **22 conformance variants + baseline parity + eleven
compatibility checks**. A passing fast comparator is not full-baseline parity. The registry declares
the remaining conformance variants portable; it does not supply current full Linux execution proof.

## Eleven Compatibility Owners And Their Nested Work

All rows below passed on Windows at 5.7. Linux classifications are inventory conclusions/proposals,
not newly passing checks. The implementation authority is [run_compatibility.py](Compatibility/run_compatibility.py).

| Check | Actual nested execution and retained comparison | Linux qualification finding |
| --- | --- | --- |
| `compatibility-reporting` | Child compatibility runner, both root-discovery runtimes/locations, detailed/concise/human/error modes, unsafe reports, cleanup and bounded diagnostics | Portable candidate. Its synthetic failing render has a missing input and must fail before browser invocation; it is not real render proof or a Chrome prerequisite. Preserve deterministic envelopes and exact stdout/report bytes where asserted. |
| `conformance-reporting` | Both aggregate runners and project-root suite, private malformed project/helper, help discovery, deterministic concise results, explicit/automatic failure reports, outside-root denial | Portable candidate with existing root primitives. Preserve schema/count/type checks, report-path semantics and narrowly declared timing/owner aliases. |
| `framework-catalog` | Both framework CLI commands; catalog, selection, provider filters, project attachment/views, human/JSON exports, invalid selectors and unsafe reports | Portable candidate backed by primitive conformance, not CLI qualification. Within-host Python/PS7 JSON/report bytes and diagnostics must still match. Check path/encoding/case behavior without broadly normalizing errors. |
| `effective-schema` | Both effective-schema CLI commands; catalog/schema, filtered selections, report sections, exports, invalid selectors and outside-root reports | Portable candidate. Preserve diagnostic codes, canonical bytes, selectors and ordered values; project-dependent text/path output needs exact checks. |
| `visualization` | Both `Validate`, `Refresh -SkipRender` and unbounded relationship graph; normalized five-file golden refresh, semantic counts and graph digest | No browser required for this check. PS broken-link discovery excludes `.git`/`Source` with backslash-only patterns and formats diagnostic paths with backslashes; Python uses native separators. Qualify exclusion and diagnostic parity before changing golden expectations. |
| `qa` | Both QA exporters, bounded graphs/pages, settings redirect and nested refresh with `-SkipRender`; normalized 35-file golden tree and structured counts | Confirmed PS relative-path defect; see probe below. Its nested PS host already uses the verified current Core executable. Preserve exact generated tree, authored source wording and source/content-root identities. |
| `root-discovery` | Project-path suites in both runtimes from repo, Tools, nested Contracts and unrelated location: eight launches | Portable candidate; the constituent suites are in existing Linux feature proof. The owning eight-launch check remains unqualified. Preserve explicit/environment/cwd precedence and negative path grammar. |
| `artifact-lifecycle` | Python QA generation/regeneration and stale cleanup, both-runtime unsafe QA rejection and cleanup dry runs, Python scoped deletion plus unrelated sentinel | Depends on QA path qualification. Current positive destructive mutation owner is Python; do not invent PS destructive equivalence or drop rejection/dry-run controls. Cache scans must remain isolated from shared bootstrap stores. |
| `framework-extraction` | Separate temporary copy of Framework/Runtime/Conformance + reviewed files; neutral project; nine portable suites in both runtimes; forbidden-surface and cleanup checks | Portable candidate; no LoTM pages, real media or rendering required. Qualify complete copied inventory, dependency inheritance, temp cleanup and eighteen ordered suite results, not just a copy-only rehearsal. |
| `distribution-boundary` | Both aggregate runners select the distribution suite; exact returned summary and provider-inert/unchanged-output controls | Portable candidate; it is not in the fast feature cohort. Retain missing-provider and byte-preservation behavior; do not count duplicate fixture use as redundant consumer coverage. |
| `render` | Both Visualization Render entry points call pinned mmdc/Puppeteer/full Chrome for representative SVG; nonblank/size/labels/dimensions checks and reported output hashes | Linux-native toolchain is not prepared. Helpers are not statically Windows-gated. Qualify dependencies, fonts, launch/cleanup and both helpers. Current owner requires within-host dimensions, reports hash equality, but does not require byte-identical SVG across OSes. |

### Concrete Path Findings

PS QA `ConvertTo-RelativePath` constructs a backslash-terminated base URI and is called
for source and content-relative paths. Evaluating only that existing AST function against existing
Linux paths returns `phase57-native-source/README.md` instead of `README.md`. The source is not
portable at this point; adding Linux to an OS list would not fix it. Proposed correction uses
filesystem-relative paths and forward-slash serialization, with Windows byte/output proof.

PS Visualization `Get-BrokenMarkdownLinks` uses backslash-only directory exclusions. It runs during
refresh, including QA refresh checks. Python exclusions use `os.sep`; its diagnostic combines a
literal `.\\` prefix with a native relative path, while PS forces backslashes. Qualification must
cover both directory filtering and diagnostic representation. Source-pattern inspection alone does
not prove the complete golden refresh currently fails; that belongs to 5.8.2.

Root/output helpers also use ordinal-ignore-case comparisons in places. Preserve legitimate Windows
case behavior while qualifying case-sensitive Linux sibling paths, absolute-drive/UNC rejection,
Unicode/spaces, symlinks and existing-ancestor containment. Do not assume every backslash in a PS
script is a defect: PS Join-Path supports many existing portable inputs already proved by the fast suites.

## Required Tools, Platform Requirements And Preparation

| Surface | Adopted dependency / current proof | Linux preparation or qualification boundary |
| --- | --- | --- |
| Python runtime and package | CPython 3.14.5, pip 26.2, PyYAML 6.0.3; Python package 0.1.0 | Prepared development interpreter already exists; use Linux x86-64 locked PyYAML, not a Windows wheel or build-only interpreter. Installed verification uses `bin/python`, a fresh outside-checkout venv, no-index/no-deps installation and neutral fixture/origin/hash/poisoned-source checks. |
| Native Python/policy/media | pytest 9.1.1, Ruff 0.16.1, Pillow 12.3.0 and complete locked dev graph | Existing feature verifies imported versions/content. Colorama is Windows-conditional. Pillow installation is not proof that image/EPUB helpers were exercised. Build-only payloads remain separate. |
| PS runtime/development | Core 7.6.6, runtime floor 7.4.0, powershell-yaml 0.4.12, Pester 6.2.0, PSScriptAnalyzer 1.25.0 | Owned Linux host/modules already qualified by feature proof. Analyzer requires 7.4.6+, so use adopted development host, not the floor for formatting. Keep exact module imports, no user-profile roots, and current nested host inheritance. |
| Static/Git policy | actionlint 1.7.12, Git, actual-change annotation/composition context, formatter representation | All four policies and actual-context preflight are already in feature proof. Actionlint's optional ShellCheck/pyflakes hosted integrations remain Phase 6; this inventory neither drops them nor counts them as proved. |
| Native render runtime | Node 24.15.0, npm 11.12.1 | Read-only WSL inventory finds no native Node on PATH or under the owned runtime directory. `npm` resolves to a Windows-mounted installation; that is not admitted native Linux setup. Prepare native runtimes explicitly and verify versions before bootstrap. |
| Render packages/browser | Mermaid CLI 11.16.0, Puppeteer 25.3.0, full Chrome 150.0.7871.24; committed npm lock | No owned Linux render environment/browser cache found in the existing native workspace. Bootstrap is OS/architecture/version/lock keyed, uses npm ci and explicit Chrome acquisition, skips Firefox/headless-shell, and sets `installDeps:false`. Obtain a Linux receipt; Windows caches/receipts cannot certify it. |
| Chrome system runtime | Native ELF dependencies, NSS/X11/GTK/font libraries as required by the acquired browser; fonts and Ubuntu launch environment | Inspect actual browser linkage and readable fonts, use the upstream [requirements](https://pptr.dev/guides/system-requirements) and [troubleshooting](https://pptr.dev/troubleshooting), then verify a real headless launch. No package installation or OS-policy change occurs here. Missing packages or machine-level changes need explicit handling at preparation. |

Observed WSL is Ubuntu 24.04.5 LTS x86-64 on WSL2. This is one local Linux environment, not a claim
about every distro or a hosted agent. Existing Puppeteer configs already supply no-sandbox flags;
do not silently add broader host security changes. Both helpers must receive the admitted browser
through the existing owner environment rather than substituting a system/Windows browser or direct mmdc.
Browser/font-dependent dimensions may differ across OSes; preserve current within-host requirements
and report the difference before adopting any new cross-OS comparator.

## Genuine Windows Surface And Previously Accepted Coverage Gap

[Edit-Image.ps1](Commands/Media/Edit-Image.ps1) performs crop operations with System.Drawing Image,
Bitmap and Graphics. This is a genuine Windows boundary on modern .NET; the Unix switch was removed
in .NET 7 ([Microsoft](https://learn.microsoft.com/en-us/dotnet/core/compatibility/core-libraries/7.0/system-drawing)).
The helper is not invoked by any current registered full unit. Its existence therefore does not
make today's eleven compatibility checks inherently Windows-only.

However, [D12](ci-testing-contracts.md) already requires synthetic EPUB/image implementation tests
in PR coverage. Current permanent test entries have no EPUB/image-helper behavior tests. Earlier
Phase 2 media rehearsals and having Pillow installed do not close that requirement; G03 and the pilot
review retained it. This inventory exposes the outstanding registration/behavior gap rather than
claiming the 74-unit reference contains it.

Recommended bounded closure at 5.8.2: portable Python EPUB/image synthetic fixtures, PS EPUB
qualification using its actual compression/XML behavior, and a small Windows-only PS crop test lane.
Use synthetic files, not local books/artwork. Retain current helper support; no image-library rewrite
or retirement is proposed. Add genuine behavior regressions to approved registration and update all
profile/impact/coverage counts. If Windows-required media is added, the complete required portfolio
will be larger than the historical 74 units and cannot honestly be called a wholly Linux full run.
Compare the same original 74 core obligations on both OSes where qualified, then account for added
media and any Windows remainder separately in the complete split portfolio. New costs require the
5.8.3 disposition; the 5.7 exception is not automatic acceptance of changed coverage.

## Bounded 5.8.2 Proposal And Decisions For Review

1. Preserve the confirmed 5.7 commit, all 74 IDs, fixtures, golden data, deadlines and check names.
   Prepare a complete native Linux copy from authoritative bytes/modes and verify its complete digest
   before launching anything; force known tracked-under-ignored files into any synthetic index.
2. Prepare native Node/npm/Chrome explicitly in owned locations. Inspect system prerequisites and
   qualify bootstrap integrity/ownership, real headless launch and helper invocation. Request a
   concrete machine-level change only if it is actually necessary; do not install during tests.
3. Fix only demonstrated QA/Visualization path behavior and resulting narrow consumer portability
   defects. Add focused Unicode/path/exclusion/case/containment regressions and prove Windows behavior
   and existing golden outputs unchanged. Different text, schema or render semantics require review.
4. Replace the CI loader's blanket compatibility OS default with explicit per-unit `os` declarations
   in coverage metadata. Recommend metadata **schema 2**, with required nonempty, duplicate-free,
   known Windows/Linux lists for all external descriptors, strict type/unknown-field/version rejection,
   and unchanged ownership/order. Other catalog schema versions and conformance/compatibility registry
   versions stay unchanged. This is the confirmed D24 design refinement of D22; it is not implemented.
   OS metadata represents CI eligibility; standalone custom owners keep their independent commands.
5. Test missing/duplicate/unknown OS values, unsupported version/type, truthful Linux blockage,
   Windows admission, incompatible shard placement and exactly preserved full membership. Qualify
   candidates through owned supervised execution and complete result/report/cleanup admission;
   permanent support is not established merely by a successful planning/listing command.
6. Close the existing D12 synthetic-media gap with explicit runtime/OS registration. Preserve the
   distinction between portable core comparison and all required PR/full coverage. Review updated
   counts and required Windows assignment rather than silently bypassing a blocked native group.
7. Qualify ten non-render owners, remaining conformance variants and full parity; real rendering
   follows admitted Linux preparation. Use focused evidence during repairs; run final complete
   comparison only after the candidate is stable. Reuse unaffected Windows 5.7 proof; requalify
   affected Windows behavior and perform a fresh complete reference where executable changes require it.

The maintainer confirmed the D24 metadata-schema-2 design and bounded D12 gap closure/Windows-media
placement on 2026-10-06. Phase 5.8.2 implementation remains unstarted. If Chrome requires unavailable system dependencies,
a broad product/runtime redesign is needed, or existing goldens cannot be preserved, bring back that
specific decision. Nothing here approves changing canonical content, retiring helpers, changing
required checks or assuming hosted performance. The plan's split-platform fallback remains available.

## Comparison, Isolation And Rollback Rules

Use current `typed_equal` for exact conformance types/keys/ordered arrays. Compatibility owner
normalization removes declared generated time and owned-output aliases, normalizes text newlines
and JSON key order, and hashes binary content. Do not add blanket stripping of paths, slashes,
errors, IDs, counts, authored text or missing outputs to force parity. CLI canonical JSON/export
bytes remain exact between runtimes where the owner asserts them. Cross-OS observations must
distinguish semantic differences from already permitted operational fields explicitly.

Owned Linux execution uses process groups, parent EOF cancellation, descendant wait/reaping and
source/publication guards; it is not the Windows Job Object containment implementation. Retain
independent continuation, whole-unit/nested deadlines and cleanup verification. Detached descendants,
hard host kills and unverified cleanup remain explicit failures/boundaries. Keep temp/consumer
fixtures outside shared bootstrap caches; dry-run/cleanup checks must not traverse live tool stores.
No 5.8.1 probe changes project sources or launches a suite/browser.

Rollback for this checkpoint is documentation only. For the proposed implementation, revert changed
OS admission/metadata and path/bootstrap code together to the 5.7 reference, restore prior profile
assignments, and retain approved media obligations rather than losing them with an unrelated rollback.
Retain failed/superseded evidence; no aggregate pass is assembled from different captures.

Ignored `.tmp/ci-phase581/inventory.json` records every current full ID, adapter, entry, OS declaration,
reference cost and feature-overlap status. This is read-only evidence, not another test registry.
The URI AST probe evaluates only an existing pure path helper against existing files; it is not
consumer golden/output qualification. No newly passing Linux full or compatibility result is claimed.

Verification for this documentary checkpoint: all 74 matrix IDs match catalog order, the 40 exact
feature overlaps and separate fast parity reconcile, all 111 local documentation links resolve,
annotation policy passes 22/22 fixtures across 469 files with eight valid annotations, and
`git diff --check` passes. The worktree diff contains only this inventory and four CI documentation
updates; no executable/dependency/catalog/workflow or canonical file is edited.

## Complete Current 74-Unit Mapping

The following table is generated from the read-only catalog inspection. `Feature` means the exact
ID is in existing Linux feature proof; `Qualify` means additional current full proof is required.
Every row proposes retaining Windows support and attempting Linux qualification. Compatibility
eligibility remains Windows-only until its owning implementation/admission proof. Added D12 media
obligations are not hidden inside this historical 74-row matrix.

| Execution ID | Existing Linux evidence / required action |
| --- | --- |
| `policy/ruff::python` | Feature; retain and requalify if affected |
| `policy/work-annotations::python` | Feature; retain and requalify if affected |
| `policy/actionlint::python` | Feature; retain and requalify if affected |
| `policy/powershell-format::powershell7` | Feature; retain and requalify if affected |
| `implementation/python-bootstrap::python` | Feature; retain and requalify if affected |
| `implementation/python-compatibility-implementation::python` | Feature; retain and requalify if affected |
| `implementation/python-package-artifact::python` | Feature; retain and requalify if affected |
| `implementation/python-tooling-pilots::python` | Feature; retain and requalify if affected |
| `implementation/python-native-results::python` | Feature; retain and requalify if affected |
| `implementation/ci-catalog::python` | Feature; retain and requalify if affected |
| `implementation/python-installed-runtime::python` | Feature; retain and requalify if affected |
| `implementation/ci-scope::python` | Feature; retain and requalify if affected |
| `implementation/ci-process::python` | Feature; retain and requalify if affected |
| `implementation/ci-execution::python` | Feature; retain and requalify if affected |
| `implementation/powershell-conformance-implementation::powershell7` | Feature; retain and requalify if affected |
| `implementation/powershell-dependencies::powershell7` | Feature; retain and requalify if affected |
| `implementation/powershell-formatting-implementation::powershell7` | Feature; retain and requalify if affected |
| `implementation/powershell-host::powershell7` | Feature; retain and requalify if affected |
| `implementation/powershell-qa-children::powershell7` | Feature; retain and requalify if affected |
| `implementation/powershell-runtime-api::powershell7` | Feature; retain and requalify if affected |
| `conformance/project-root::python` | Feature; retain and requalify if affected |
| `conformance/project-root::powershell7` | Feature; retain and requalify if affected |
| `conformance/framework-installation::python` | Feature; retain and requalify if affected |
| `conformance/framework-installation::powershell7` | Feature; retain and requalify if affected |
| `conformance/framework-catalog::python` | Qualify remaining baseline variant |
| `conformance/framework-catalog::powershell7` | Qualify remaining baseline variant |
| `conformance/capability-roadmap::python` | Qualify remaining baseline variant |
| `conformance/capability-roadmap::powershell7` | Qualify remaining baseline variant |
| `conformance/strict-ingestion::python` | Feature; retain and requalify if affected |
| `conformance/strict-ingestion::powershell7` | Feature; retain and requalify if affected |
| `conformance/lookup-key::python` | Feature; retain and requalify if affected |
| `conformance/lookup-key::powershell7` | Feature; retain and requalify if affected |
| `conformance/schema-pack::python` | Feature; retain and requalify if affected |
| `conformance/schema-pack::powershell7` | Feature; retain and requalify if affected |
| `conformance/distribution-boundary::python` | Qualify remaining baseline variant |
| `conformance/distribution-boundary::powershell7` | Qualify remaining baseline variant |
| `conformance/taxonomy::python` | Feature; retain and requalify if affected |
| `conformance/taxonomy::powershell7` | Feature; retain and requalify if affected |
| `conformance/resource::python` | Feature; retain and requalify if affected |
| `conformance/resource::powershell7` | Feature; retain and requalify if affected |
| `conformance/effective-schema::python` | Feature; retain and requalify if affected |
| `conformance/effective-schema::powershell7` | Feature; retain and requalify if affected |
| `conformance/source::python` | Qualify remaining baseline variant |
| `conformance/source::powershell7` | Qualify remaining baseline variant |
| `conformance/entity::python` | Qualify remaining baseline variant |
| `conformance/entity::powershell7` | Qualify remaining baseline variant |
| `conformance/provenance::python` | Qualify remaining baseline variant |
| `conformance/provenance::powershell7` | Qualify remaining baseline variant |
| `conformance/temporal::python` | Feature; retain and requalify if affected |
| `conformance/temporal::powershell7` | Feature; retain and requalify if affected |
| `conformance/chronology::python` | Feature; retain and requalify if affected |
| `conformance/chronology::powershell7` | Feature; retain and requalify if affected |
| `conformance/reconciliation::python` | Qualify remaining baseline variant |
| `conformance/reconciliation::powershell7` | Qualify remaining baseline variant |
| `conformance/occurrence::python` | Qualify remaining baseline variant |
| `conformance/occurrence::powershell7` | Qualify remaining baseline variant |
| `conformance/hosting::python` | Qualify remaining baseline variant |
| `conformance/hosting::powershell7` | Qualify remaining baseline variant |
| `conformance/interpretation::python` | Qualify remaining baseline variant |
| `conformance/interpretation::powershell7` | Qualify remaining baseline variant |
| `conformance/project-composition::python` | Qualify remaining baseline variant |
| `conformance/project-composition::powershell7` | Qualify remaining baseline variant |
| `parity/conformance-baseline::referee` | Qualify full 42-row parity; fast parity is separate |
| `compatibility/compatibility-reporting::referee` | Qualify owner + OS admission |
| `compatibility/conformance-reporting::referee` | Qualify owner + OS admission |
| `compatibility/framework-catalog::referee` | Qualify owner + OS admission |
| `compatibility/effective-schema::referee` | Qualify owner + OS admission |
| `compatibility/visualization::referee` | Qualify owner + OS admission |
| `compatibility/qa::referee` | Qualify owner + OS admission |
| `compatibility/root-discovery::referee` | Qualify owner + OS admission |
| `compatibility/artifact-lifecycle::referee` | Qualify owner + OS admission |
| `compatibility/framework-extraction::referee` | Qualify owner + OS admission |
| `compatibility/distribution-boundary::referee` | Qualify owner + OS admission |
| `compatibility/render::referee` | Qualify owner + OS admission |
