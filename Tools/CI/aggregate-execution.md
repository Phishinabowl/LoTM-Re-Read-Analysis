# Local Aggregate Execution And Shard Evidence (CI 4.4)

CI 4.4 is confirmed by the maintainer on 2026-10-06. `run_ci.py` connects captured Git scope, owning
catalogs, process supervision and layer adapters. Explicit local execution is available; existing
hosted workflows/check names remain unchanged. CI 4.5 adds [local reporting](execution-reporting.md).
Planning still advertises rollout blockers: hosted publication, mandatory hosted meta-regression/adoption and complete equivalence
(4.6/Phase 5 onward). This checkpoint is not the completed hosted migration.

## Local Commands

Use explicit verified paths recorded by bootstrap, including its module root and acquired wheels.
Execution never installs dependencies, downloads tools or repairs an environment.

Profiles selecting rendering also require `--render-bootstrap-report` pointing to a passing current
bootstrap report. Admission rechecks owned content receipts, captured pins/configuration and actual
Node/full-Chrome resolution before propagating the exact executable and owned Mermaid PATH.
Missing/unreadable wheel inputs block installed-artifact execution with prerequisite diagnostics.
See the [release reproduction proof](../ci-testing-release-reproduction-proof.md) for exact preparation
recipes, input ownership and OS limits; feature-only profiles do not require render preparation.

```powershell
# Variables are executable/module/artifact paths from your bootstrap reports.
& $python Tools/CI/run_ci.py --profile feature-feedback --scope local-worktree `
    --pwsh $pwsh --module-root $modules --actionlint $actionlint `
    --wheel $wheel --runtime-wheel $yamlWheel

& $python Tools/CI/run_ci.py --profile feature-feedback --scope local-staged `
    --pwsh $pwsh --module-root $modules --actionlint $actionlint `
    --wheel $wheel --runtime-wheel $yamlWheel --json

# One registered shard; the saved shard-result.json is its transferable input to collection.
& $python Tools/CI/run_ci.py --profile feature-feedback --scope committed `
    --base $base --source $source --shard-plan feature-feedback-initial `
    --shard native-policy-0 --pwsh $pwsh --module-root $modules --actionlint $actionlint `
    --wheel $wheel --runtime-wheel $yamlWheel

# Supply every required source shard to collection; repeat --shard-result.
& $python Tools/CI/run_ci.py --profile feature-feedback --scope committed `
    --base $base --source $source --shard-plan feature-feedback-initial `
    --shard-result $nativeBundle --shard-result $infrastructureBundle `
    --shard-result $pythonConformanceBundle --shard-result $powershellConformanceBundle `
    --shard-result $parityBundle
```

`--root` defaults to the command's repository. All six scope modes retain the [4.2 rules](change-scope.md).
`--output-root` must be a child of ignored repository `.tmp`; every invocation allocates a unique
owner. Index/commit/worktree execution always materializes the captured source and loads its catalog.
Full membership is enforced; there is no affected-selection or arbitrary unit/argument override.
`--json` emits the complete local record; normal output shows terminal counts and failure reasons.

A shard needing prior results accepts repeatable `--source-result` bundles. They must be approved
other shards from the same profile/plan, source snapshot and catalog; they cannot duplicate this
shard's ownership. Dependencies use verified prior results, including raw native/semantic artifacts.
Final collection needs every shard, irrespective of whether earlier shards failed. A transferred
bundle retains its relative artifact tree beside shard-result.json; a JSON file alone is insufficient.

## Source, Policy And Isolation

The execution source is an owned captured copy, not the working checkout. A private Git index is
initialized only in that copy so existing formatter/Git discovery contracts remain usable. It has
no synthetic commit and does not replace original source/merge/index provenance. Actual scope,
snapshot digest and captured catalog digests remain the authority.

All captured source files are guarded before/after units, including authored pages, templates,
Relationship Seeds, configuration and canonical projections. Addition/deletion/content/mode drift
fails the run and blocks later shared-source work; source is never automatically restored. Only
the copy's owned `.tmp`, `.local` and private `.git` areas are generated destinations. Ruff caches
stay under `.tmp`; isolated fixture probes and guardians explicitly disable source bytecode writes.

Actual changed paths/deletions are recorded separately from implementation/conformance selection.
Current static policies scan the complete captured surface conservatively; their results provide
coverage for changed-file dispositions without narrowing test membership. Actual project/framework
pack, catalog, taxonomy/resource and provider composition is loaded from the captured configuration,
not inferred from synthetic conformance fixtures. Deleted registrations/references fail catalog or
composed-context admission. Lost historical deletion precision remains visible on full fallback.

The current deletion check covers registered/catalog/configuration references. It does not claim
future authored-page logical-schema/link validation, whose Phase 4.1 inventory still needs maintainer
review. Narrow workflow/annotation profiles label other policy obligations outside-profile; shard
obligations not executed there remain delegated. A full gating profile cannot pass incomplete actual
policy dispositions. Missing source/catalog authority never becomes an empty success.

External fixture scratch has unrelated ancestors, an explicit private ownership record and a stable
public alias. Only its exact created owner is removed after verified process termination. Read-only
Git fixture flags may be cleared on owned files during removal; foreign ACLs/trees are never changed.
Cleanup failure remains a run failure and preserves the owner for diagnosis.

## Adapters And Outcomes

| Layer | Execution and evidence authority |
| --- | --- |
| Static policy | Explicit captured paths through pinned Ruff lint/format, existing PowerShell formatter, annotation policy functions/fixtures and actionlint. Optional shellcheck/pyflakes integrations are disabled: they are not adopted repository dependencies; hosted policy equivalence remains a Phase 5/6 gate. |
| Actual context | Existing effective-project composition API over real captured project/framework data; separate run-level policy dispositions. |
| pytest/Pester | Existing native adapter, phase observer, raw XML and publication XML. Reconcile framework/process exit, identity, phase inventory and case counts; absent/malformed/unexpected coverage is an error. |
| Language-neutral conformance | Existing owning registry and selected-suite runner; exact one-suite detailed JSON and original semantic summary. Per-suite child deadlines are explicit in both standalone runners. |
| Parity | Compare retained conformance semantic summaries without rerunning sources. Types, keys and ordered arrays remain exact; no broad normalization removes semantic fields. |
| Compatibility | Owning registry selects individual checks, preserving detailed JSON and expected-error contracts. Portfolio mode continues independent check failures, records failed/blocked checks, and stops after protected state changes. Inherited aggregate deadlines clamp nested calls and retain timeout diagnostics. |
| Installed artifact | Existing reviewed-wheel verifier; explicit locked PyYAML wheel supports copied-source execution without hidden cache/network fallback. Wheel content/metadata and dependency digest checks remain authoritative. |

CI 5.2 distinguishes the formatter's input representation explicitly. Commit/hosted and staged-index
captures use `GitBlob`: computed formatter CRLF output is compared in Git's LF representation without
writing captured bytes. Local-worktree/full captures use `Worktree`, preserving the existing physical
CRLF check. Blob fixes and non-LF blob input are rejected; unknown snapshot kinds fail closed. Existing
formatter JSON fields and default direct invocation remain unchanged.

The parity adapter also validates each retained source's passed status, expected suite ID, schema/counts
and error-free success shape before comparing summaries. Different operational profile labels do not
change equivalence; no field inside a semantic summary is removed or normalized. Changed decisions,
counts, JSON types and array order fail; missing runtime or malformed/error evidence is an error.

CI 5.3 preserves owning-check JSON while promoting failed conformance/compatibility error text into
bounded aggregate reasons. Formatter failures also expose counts and affected paths. Full owner JSON
and streams remain retained; the existing human/Markdown projections receive specific reasons.
Consumer output normalization uses the nearest output-owning `.tmp`, supporting current nested
execution checkouts without changing canonical consumer baselines.

Preflight checks exact adopted Python/PS7/actionlint and required native dependency versions, selected
environment import origins, installed Python RECORD content and owned PowerShell cache receipts.
Runtime/module absence blocks affected obligations while independent available units may continue.
Runtime labels/digests are recorded; execution does not float versions or install missing packages.

`RunBudget` binds the original invocation clock, including the existing 600-second setup allowance;
unit/nested leases preserve termination/cleanup/finalization reserves. Independent assertion/policy
failures permit later attempts. Failed execution prerequisites block dependents; loss of source or
containment stops later launches. Every established selected ID has one terminal result, including
unexecuted/blocked/cancelled units, with zero attempts and unknown native counts where appropriate.
Native errors retain raw process diagnostics even when result parsing fails.

Aggregate exits are 0 for satisfied obligations, 1 for execution/coverage/review/cleanup/report failure,
2 for invalid invocation/planning/source evidence, and 130 for cancellation. Earlier failures remain
visible when cancellation takes precedence. Required review families stay pending until their owning
acceptance gate; no automated passing result invents maintainer approval.

## Collection And Reporting Boundary

Local JSON is `ci-execution-report` v1. Units retain original exits, native counts, detailed adapter
artifacts and complete stdout/stderr; bounded diagnostic tails are presentation only. Artifact records
contain relative paths, producer, bytes and SHA-256. This is the initial local recording/collection
implementation. CI 4.5 extends it with atomic journaling/recovery and Markdown/XML projections.

`ci-shard-result` v1 binds a report to the existing `ci-shard-source` manifest. Collection verifies
exact catalog/profile/shard/snapshot identity, partition membership/order, terminal counts, source
guards, cleanup and required artifact bytes/digests. Passing custom/native/parity results require
actual matching owned-process and domain/native evidence. Missing, stale, duplicated, foreign or
contradictory evidence fails even if an artifact upload succeeded. Source artifacts are copied under
the aggregate owner; future hosted workflows will use this same admission model.

The initial native/policy shard is now 1920 seconds of execution plus 210 lifecycle reserve. A new
native-infrastructure-1 shard owns catalog/scope/process/aggregate regression: 390 execution seconds
plus 210 reserve. Existing check identities remain intact with updated source-shard projections;
neither shard exceeds the unchanged 2190 execution / 3300 host ceiling. No workflow YAML is activated.

Local incremental events, interrupted recovery, confined publication admission and Markdown/custom XML
are implemented at CI 4.5. Actual hosted publication and complete host/event/shadow adoption remain later gates.
Evidence and measured costs are recorded in the [coverage ledger](../ci-testing-coverage-ledger.md).
