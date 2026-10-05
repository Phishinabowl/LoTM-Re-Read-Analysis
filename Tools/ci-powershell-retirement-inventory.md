# PowerShell Host Retirement: Support Contract And Migration Inventory

**Status:** CI Phase 2.1 confirmed on 2026-10-05, source snapshot `be54319f99b798e4432f55f2af00d21dda30d276`,
`architecture/ci-testing-modernization`, 2026-10-05. D14 already approves 5.1 retirement; this
checkpoint applies the documentary support contract and records its implementation/version boundaries.
It does not change executables, dependency declarations, registries or hosted configuration.

## Support Boundary And Transition

Supported platform implementations are Python and **PowerShell 7.4+ Core**. The observed primary
development host is **7.6.6**; that observation does not prove the 7.4 floor or a clean install.
Pester remains **6.2.0**. Desktop/Windows PowerShell 5.1 and Core versions below 7.4 are outside
the supported contract; no feature is delegated to Python merely to satisfy this policy.
Independent Python/PS7 behavior, all semantic fixtures, root/visibility/validation rules, exports
and public CLI paths remain required. Windows APIs still require explicitly supported OS coverage.

Phase 2.2 now implements the 0.14.0 module's 7.4/Core boundary, preflight and public startup guards
confirmed on 2026-10-05. Phase 2.3's three QA children use that resolved host, confirmed on 2026-10-05.
Phase 2.4 implements schema-3 Python/PS7 registries, verified host discovery, dynamic reporting counts
and two-runtime extraction, confirmed on 2026-10-05. Current hosted CI still has a 5.1 job, pending 2.6. This is a
temporary migration obligation, not
an ongoing support promise. Implement enforcement at 2.2, children at 2.3, registry/extraction at
2.4, retained proof at 2.5 and hosted retirement at 2.6. Complete local retained coverage is confirmed
at 2.5 on 2026-10-05; hosted closure remains 2.6. Standalone compatibility/extraction no longer require 5.1.

Active documented PowerShell recipes use `pwsh`; a machine with only Python can use Python tools,
and a PowerShell-only machine needs supported PS7 and applicable dependencies. Do not redirect an
unsupported invocation to another host or implementation silently. Never uninstall the OS shell or
alter machine execution policy as part of retirement. Explicit process launch policy is owned by 2.2.

## Frozen Evidence And Coverage Mapping

Ignored `.tmp/ci-phase21-20261005/frozen-snapshot.json` records hashes of all **485 tracked files**
at entry and **28 Phase 1.4 JSON evidence files**. The original measurements under
`.tmp/ci-phase14-20261003/` stay unchanged, including the failed 360-second extraction, corrected
378.285-second diagnostic and cleanup finding. Git commit history provides the durable source
snapshot; these hashes are local audit evidence, not another canonical baseline.

The active methodology family **PARITY-SUPPORTED-RUNTIMES** replaces **PARITY-THREE-RUNTIME**
one-for-one. Retired ID references in historical evidence map to the same retained semantic
obligation with Desktop host coverage deliberately removed. Do not register the old ID as another
required test, double-count the alias or rewrite past execution results. There remain **71 active
methodology families**, all **21 paired conformance suites**, **11 compatibility check families**
and **nine extraction suites**. The retired ID is historical metadata, not a 72nd active family.

Historical evolution logs, completed platform phases, dated tooling checks, extraction stabilization
evidence and Phase 1.4 measurements retain their original three-runtime results. Authored LoTM pages,
templates, Relationship Seeds, project data, fixture bytes and QA/Visualization baselines are untouched.
Operational helper recipes can change executable spelling without changing their narrative/domain content.

## Executable Migration Inventory

Paths below are repository-relative and describe the frozen Phase 2.1 inventory. Phase owners refer
to the accepted CI plan; no row is completed by documenting it. Preserve focused commits and record
actual verification at adoption. Phase 2.2 progress and findings are recorded in the plan and below.

| Consumer / location | Exact obligation | Owner / verification gate |
| --- | --- | --- |
| `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` | Current `ModuleVersion 0.13.0`, `PowerShellVersion 5.1`, Desktop/Core. Plan 0.14.0 with minimum 7.4/Core only; preserve all exports. | 2.2: supported import plus deliberate unsupported import, unchanged export inventory. |
| Runtime module entry/private scripts | Keep the independent implementation and existing loader/semantic APIs. No blanket conversion to newer syntax/APIs or removal of compatibility-safe constructs. | 2.2/2.5: all 21 suites and consumer parity; no private implementation churn. |
| `Tools/Commands/Environment/Test-PowerShell.ps1` | Host readiness before module import; actual edition/version and unsupported-host diagnostics. Module discovery alone cannot mean ready. | 2.2: Core floor/current, Desktop, older Core, missing/import-failed module and structured/human exit evidence. |
| `Tools/Commands/Environment/Test-Python.ps1`, Framework/QA/Media/Maintenance `.ps1` entry points, `Visualization/visualize.ps1` | Keep paths/arguments and imports; unsupported PowerShell fails clearly before generation. No Python subprocess replacement for domain behavior. | 2.2/2.5: startup, help where supported, JSON/human errors, canonical guard; required OS fixtures. |
| `Tools/Static/Format-PowerShell.ps1` | Correction from 2.2 inspection: already imports the framework module for project discovery. Add a dependency-free early host guard; retain its existing discovery dependency without adding domain validation. | 2.2: unsupported early failure, retained parser/token/discovery/encoding policy. |
| `Tools/Conformance/Run-Conformance.ps1` | Module import occurs before orchestration. Preserve reporting-mode failure semantics on unsupported host; approved children inherit the resolved supported executable. | 2.2: List/help/summary/report failure boundaries, no suite launch under unsupported host. |
| `Tools/Conformance/Suites/Test-Distribution-Boundary.ps1` | Existing current-process child executable plus Desktop launch branch. Preserve source/fixture roots and child comparison while removing Desktop obligation. | 2.2/2.5: retained distribution/composition probes, missing/wrong executable and no hidden Desktop child. |
| `Tools/Commands/QA/Obsidian-QA-Export.ps1`: Write-RepoRefreshCheck, Write-BoundedGraphs, Invoke-DisposableCacheCleanup | Exactly three executable `powershell` calls; migrate to resolved approved PS7 while preserving arguments/cwd/side effects and isolated process boundaries. | 2.3: recorded child identity, redirected refresh/bounded/cleanup success and failure; baseline hashes unchanged. |
| QA direct invocation and `Project_Config/project.yaml` helper paths | Keep existing visualization/cleanup helper file paths; host choice does not justify manifest/schema/data changes. | 2.3: direct QaRelationship call and configured path validation. |
| `Tools/Compatibility/compatibility.json` and run_compatibility.py load_registry/find_runtime/powershell_prefix | Schema 2 requires exact Python/PS7/5.1 order; runtime discovery and launch handling must move together to schema 3 Python/PS7. | 2.4: current/new/old/unknown/duplicate runtime/version fixtures and all existing profile/check membership. |
| run_compatibility.py create_compatibility_reporting_registry | Synthetic registry repeats schema 2 and the three-runtime list; it must migrate with the owning validator. | 2.4: positive/negative reporting and cleanup fixtures still execute, rather than fail accidentally at registry parsing. |
| run_compatibility.py run_conformance_reporting_check | Hardcoded success/failure/unsafe counts of 3 and determinism 6 come from runtime multiplicity. Derive these from actual executions; unrelated fixed cleanup/scenario counts remain unchanged. | 2.4: expected two-runtime counts 2/2/2 and determinism 4, complete failure reports and truthful omitted inventory. |
| `Tools/Compatibility/verify_framework_extraction.py` | Independently requires both PowerShell hosts; remove Desktop discovery/comparison, preserve Python/PS7 and all nine suites plus neutral-copy boundaries. | 2.4/2.5: exact portable summaries, no project leakage, actual post-exit removal; never trust an early cleanup declaration alone. |
| `.github/workflows/ci.yml` | Dedicated Windows PowerShell 5.1 job, shell/setup/report paths; compatibility still invokes nested hosts. Retire only after retained proof and refreshed protection/budget checks. | 2.6: actual retained check identities, event/coverage evidence and unchanged source authority. |
| `Tools/Commands/Media/Edit-Image.ps1`, Search-Epub.ps1 | System.Drawing and compression assemblies remain implementation dependencies; host retirement is not proof of portable media APIs. | 2.2/2.5: owned synthetic Windows/PS7 images/EPUBs; permanent required native PR groups at 3.3. |
| Future CI profiles/metadata/Pester adapters | Approved runtime IDs are Python/PS7; reject obsolete runtime declarations. No 5.1 optional skip or fake successful result. | 4.1/4.4/4.6: exact registration/variant/OS coverage and negative controls. |

## Documentary Consumers And Historical Exceptions

The active architecture, project policy, methodology and affected framework contract runtime clauses
adopt Python/PS7. Root bootstrap/specification, Tools and Visualization guides and operational media
recipes use the PS7 launcher. Framework data READMEs retain their fixture semantics and counts.
The active future platform parity gate changes to retained runtimes; completed platform gates do not.

`Tools/TOOLING_REFERENCE.md` distinguishes supported recipes/policy from current pre-migration
implementation. Its current CI and compatibility implementation descriptions stay explicitly three-host
until 2.4/2.6 updates them. Last-check paragraphs and historical measurements are preserved.
`Framework/extraction_readiness.md` updates the support gate above Stabilization Evidence; the dated
evidence below that heading is preserved verbatim. `Framework/platform_evolution.md`,
`Framework/framework_evolution.md`, completed `Tools/CI_implementation_plan.md`, read-only discovery
inventories and authored investigations keep historical references/commands; they are not new launchers.
Phase 2.1 changed no `.ps1` files. Phase 2.2 updates source help strings to `pwsh` alongside startup
guards; QA's actual three executable child calls remain unchanged until 2.3.

## Accepted Version And Public Result Decisions

These accepted planned implementation versions make the breaking host boundary explicit; they do not
advance domain/model versions or falsely mark an unimplemented schema as live.

| Surface | Frozen 2.1 baseline / planned adoption | Meaning / obsolete-input behavior |
| --- | --- | --- |
| KnowledgeFramework module | 0.13.0 / **0.14.0** at 2.2 | Pre-1.0 support change recorded in module release notes. PS7.4+ Core only; old hosts fail before semantic/generation work. No export/API/data rewrite. |
| Compatibility registry | schema 2 / **schema 3** at 2.4 | Same root/check/profile shapes, reviewed ordered runtime list becomes Python/PS7. Reject old schema 2 rather than silently rewriting or executing its Desktop obligation; explain migration. Synthetic registries migrate too. |
| Conformance registry | schema **1 unchanged** | Language-neutral paired filenames and all 21 suite/profile/discovery memberships unchanged. PowerShell host support is not another suite inventory. |
| Detailed conformance/compatibility and concise validation-run-summary | detailed schema **1**, concise contract **1 unchanged** | Fields/meaning/order preserved. Runtime arrays/maps and runtime-dependent counts report actual executions; cardinality changes are intentional and documented, not fabricated compatibility. Historical reports remain interpretable. |
| Extraction summary | schema **1 unchanged** | Same copy/suite/result fields; runtimes become Python/PS7 and text stops claiming three hosts. copied_files is measured, not an immutable expected count. Actual removal proof stays separate. |
| PowerShell environment probe | Currently unversioned JSON; retain its existing fields | Plan ready = supported host plus usable declared modules, with additive host_supported/minimum_powershell_version diagnostics. Document this readiness refinement and verify consumer/CLI behavior at 2.2; no wholesale shared-report contract is invented. |
| Framework/project/pack/fixture/oracle schemas | **Unchanged** | Runtime support changes no persisted knowledge schema or Unicode/temporal/visibility semantics. No V51 model version is introduced by this CI work. |

Post-retirement compatibility runtime identity remains `powershell7`; do not rename it to a specific
patch ID or collapse it with Python. Preserve native result identity and record actual host versions.
Same-shaped reports remain v1 because fields retain their meaning; consumers assuming a fixed runtime
cardinality must migrate with 2.4 and get permanent tests. If implementation needs incompatible
field changes, stop and review a separate report-contract revision rather than stretching this decision.

The release-notes Markdown under the module is an allowlisted reusable runtime document and will be
copied by extraction's existing Runtime directory rule. Record that documentary copied-file change;
do not assert the old 302-file diagnostic count still describes a new bundle or expand COPY_FILES to CI assets.

## Acceptance And Next Checkpoint

**Phase 2.5 temporary-test classification, confirmed 2026-10-05:** Four `Host.Tests.ps1` cases actually launch Desktop:
structured readiness, concise/no-report failure, native manifest/direct psm1 import rejection, and
all public startup/conformance-mode rejection. Together they launch 16 Desktop children per Pester
host invocation. Their purpose is retirement acceptance; remove them from regular execution at 2.6
before Phase 3 catalog admission, preserving recorded evidence. If a migration harness is retained,
it is explicitly on demand and outside steady-state profiles/catalogs/hosted gates.
The alternate-executable assertion in the retained resolver test also depends on the installed
Desktop path; replace it with a harmless existing fixture file at 2.6 and remove the shared Desktop
path setup. Retain six host tests, eight QA-child tests and all 52 Python regressions, including
synthetic edition/version values, mocked probes and obsolete-declaration rejection. Those permanent
policy tests must not require or launch 5.1. This classification does not yet move or delete tests.

**Phase 2.4 confirmed 2026-10-05:** Registry and synthetic registry are schema 3, ordered
Python/PS7; obsolete schema 2 receives a migration error. Both independent discovery paths verify
Core/minimum 7.4 before work. Reporting counts are derived from completed executions; fixed
compatibility scenario counts and report/extraction schema 1 remain unchanged. Extraction requires
all nine portable results and checks scratch absence before emitting success. The plan owns pytest,
CLI/report evidence and preserved inventories. Full portfolio, budget and timeout/process ownership
proof remain separately owned by 2.5 and later checkpoints.

**Phase 2.3 confirmed 2026-10-05:** The three QA child launches use the current approved PS7
executable; direct visualization and helper paths remain unchanged. Eight child regressions and
accepted QA/Visualization content baselines pass on PS7.6.6 and 7.4.0. Cleanup failure suppression,
inherited cwd and the known timeout-leftover finding are preserved rather than reported fixed.
The plan owns exact hashes, normal-exit cleanup proof, process sampling limits and confirmation status.

**Phase 2.2 confirmed 2026-10-05:** Host guards, module 0.14.0, usable-dependency readiness and
conformance child resolution are implemented with focused Pester 6.2.0 regressions. The plan owns
verification evidence and confirmation status. Actual 7.4.0/7.6.6 Windows runtime/media checks remain
distinct from future clean bootstrap, full retained coverage and complete host retirement. Existing
module exports match the baseline (309 actual functions); a pre-existing unimplemented manifest
declaration is recorded without broadening this change. PSScriptAnalyzer 1.25.0 requires 7.4.6 and
is correctly reported unusable on the runtime floor 7.4.0. No dependency or host installation is changed.

The maintainer confirmed this inventory, documentary support adoption and version choices as Phase 2.1
on 2026-10-05. Evidence here
is static inventory, preserved snapshots and documentation consistency, not runtime retirement proof.
Every implementation consumer has a named owner/checkpoint; baseline and canonical protection remain
requirements. Phase 2.2 host enforcement and module adoption are confirmed; Phase 2.3 is next. Remaining
2.3-2.6 work does not become complete through this checkpoint. Phase 2.1 rollback is documentary;
Phase 2.2's coordinated executable/test/documentation rollback is specified in the plan.

Verification on 2026-10-05: 171 relative links resolve across 33 edited tracked documents and two new
documents. All 71 active families remain mapped, with 21 paired suites, 11 compatibility families and
nine extraction suites unchanged. All 58 protected history blocks and 28 Phase 1.4 JSON evidence
files are preserved. Tracked hashes prove only the planned Markdown changes; executable/module/
registry/fixture/canonical bytes remain unchanged. Annotation policy passes 22 fixtures / 390 files;
`git diff --check` passes. These checks do not certify unsupported-host rejection or retired-host-free
execution; those are deliberately deferred to the owning implementation gates above.
