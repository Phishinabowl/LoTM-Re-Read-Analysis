# Tooling And Conformance Implementation Plan

This plan reconciles the tooling reorganization, root-detection, runtime parity,
conformance expansion, compatibility automation, static policy, CI, and framework
extraction work into one ordered checklist.

## Phase 0: Completed Foundation

- [x] Extract strict-YAML coverage into dedicated Python and PowerShell suites.
- [x] Add lookup-key suites around the pinned Unicode vectors.
- [x] Retain temporal, chronology, reconciliation, and occurrence suites.
- [x] Add the shared conformance-suite registry.
- [x] Add Python and PowerShell aggregate runners.
- [x] Add `fast` and `baseline` aggregate profiles.
- [x] Make the registry reject missing, stale, and unregistered runners.
- [x] Replace individual CI conformance commands with aggregate baseline commands.
- [x] Limit automatic CI to pull requests and pushes to `main`.
- [x] Establish Python as preferred/reference while retaining independent PowerShell compatibility.
- [x] Establish Ruff, PowerShell formatting, actionlint, and the testing methodology.

## Phase 1: Freeze The Tool Architecture

- [x] Inventory every current `Tools/` file as a runtime module, user command, conformance runner, static-policy tool, or environment probe.
- [x] Define the final `Tools/` directory map before moving files.
- [x] Define stable public command entry points and decide whether any temporary compatibility wrappers are necessary.
- [x] Record which surfaces require Python/PowerShell parity and which are intentionally runtime-specific.
- [x] Define import/module naming that will remain reusable outside LoTM.
- [x] Update the architecture and tooling docs with the migration contract before moving files.

Recommended target shape:

```text
Tools/
  Runtime/
    Python/knowledge_framework/
    PowerShell/KnowledgeFramework/
  Commands/
    QA/
    Maintenance/
    Media/
    Environment/
  Conformance/
    Suites/
  Compatibility/
  Static/
  README.md
  TOOLING_REFERENCE.md
```

`Visualization/` remains its own subsystem.

## Phase 2: Universal Project-Root Detection

- [x] Move root discovery into the shared Python and PowerShell runtime layers.
- [x] Use `Project_Config/project.yaml` as the project marker rather than `.git`.
- [x] Resolve roots in this order: explicit root, configured environment override, current-directory ancestors, executable-location ancestors, precise failure.
- [x] Ensure root discovery never changes the caller's working directory.
- [x] Adopt the shared resolver across every project-aware command and conformance runner.
- [x] Test launches from the repository root, `Tools/`, nested descendants, and an unrelated working directory.
- [x] Test valid explicit roots, invalid explicit roots, missing manifests, and ambiguous/escaping paths.
- [x] Preserve matching Python, PowerShell 7, and PowerShell 5.1 behavior.

## Phase 3: Reorganize Tools And Extract Modules

- [x] Convert reusable Python loaders into the `knowledge_framework` package.
- [x] Convert reusable PowerShell loaders into a real `KnowledgeFramework` module with `.psd1` and `.psm1` ownership.
- [x] Move QA, maintenance, media, and environment commands into their final command folders.
- [x] Move individual conformance runners under `Tools/Conformance/`.
- [x] Move formatting and annotation policy tools under `Tools/Static/`.
- [x] Update imports, module loading, manifests, documentation, and internal callers.
- [x] Update suite runner paths centrally in `Tools/Conformance/suites.json`.
- [x] Keep CI pointed at the aggregate entry points instead of adding individual commands.
- [x] Remove temporary compatibility wrappers once all tracked callers are migrated.
- [x] Verify no project-aware module assumes the old `Tools/` layout.

## Phase 4: Migration Validation

- [x] Run the aggregate baseline in Python, PowerShell 7, and PowerShell 5.1.
- [x] Compare aggregate suite inventories and semantic summaries.
- [x] Run Ruff, both PowerShell formatter checks, actionlint, and `git diff --check`.
- [x] Run Visualization validation in all three runtimes.
- [x] Run redirected Obsidian QA generation in all three runtimes.
- [x] Verify root discovery from every supported launch location.
- [x] Verify temporary-output ownership and scoped cleanup.
- [x] Record measured runtime changes from module loading.
- [x] Decide whether safe in-process PowerShell aggregation can replace child-process execution.

## Phase 5: Automate Project Compatibility

- [x] Create a durable compatibility-test registry or equivalent stable inventory.
- [x] Automate Visualization semantic comparisons.
- [x] Automate QA summary, inventory, Markdown, Mermaid, report, and snapshot comparisons.
- [x] Automate timestamp, newline, JSON-format, and redirected-path normalization.
- [x] Automate representative render and nonblank/hash validation.
- [x] Automate root-discovery and explicit-root tests.
- [x] Automate stale-output, unsafe-output, and scoped-cleanup tests.
- [x] Keep one canonical cross-runtime comparator rather than duplicating comparison logic in Python and PowerShell.
- [x] Add compatibility profiles suitable for local checks, pull requests, and full releases.

## Phase 6: Work-Annotation Enforcement

- [x] Build the work-annotation linter against `WORK_ANNOTATION_STANDARDS.md`.
- [x] Add valid and invalid annotation fixtures.
- [x] Validate allowed categories, ownership values, GitHub issue syntax, assignee syntax, and prohibited locations.
- [x] Ensure standards/reference documents do not self-trigger Todo Tree or the linter.
- [x] Decide and document whether the linter is paired or a canonical cross-runtime static-policy tool.
- [x] Add the linter to local static validation and CI.

## Phase 7: Missing Registry Conformance

Implement these in dependency order, with paired Python/PowerShell runners and shared fixtures:

- [x] Add dedicated schema-pack composition fixtures and suites.
- [x] Add taxonomy fixtures and suites.
- [x] Add resource fixtures and suites.
- [x] Add comprehensive source fixtures and suites.
- [x] Add synthetic entity fixtures and suites.
- [x] Add provenance fixtures, authority-decision vectors, and suites.
- [x] Add the full project-composition integration suite.
- [x] Add positive, malformed, boundary, ambiguity, and scale cases for each registry.
- [x] Register every new suite immediately in `suites.json`.
- [x] Add each suite to `baseline`; add it to `fast` only when its cost and diagnostic value justify it.
- [x] Require matching structured summaries across Python, PowerShell 7, and PowerShell 5.1.

## Phase 8: CI And Performance Finalization

- [x] Measure CI again after module extraction and expanded suites.
- [x] Decide whether feature branches should receive a fast profile.
- [x] Keep the full baseline and compatibility gate on pull requests, `main`, and manual dispatch.
- [x] Cache dependencies where GitHub Actions can safely do so.
- [x] Avoid treating ephemeral runner-installed tools as persistent.
- [x] Preserve stable GitHub check names for future branch protection.
- [x] Ensure adding a registered suite automatically flows into local aggregate runs and CI.
- [x] Document the final local-to-aggregate-to-CI testing hierarchy.
- [x] Run and record the post-consolidation hosted workflow after the tracked workflow commit is pushed.

### Phase 8 Measurement Snapshot - 2026-08-02

Fresh GitHub Actions workflow-dispatch run `30775535401` at commit `a843616` passed in 5m50s wall-clock:

| Job | Total | Dominant Step |
| --- | ---: | --- |
| Workflow Policy | 7s | Checkout/setup; actionlint install and validation each rounded below 1s |
| Python Validation | 1m07s | Baseline conformance 55s |
| PowerShell 7 Validation | 3m45s | Baseline conformance 2m39s |
| Windows PowerShell 5.1 Validation | 5m46s | Baseline conformance 4m36s |

Other fresh CI step costs:

- Python setup plus requirements: 4s total; pip caching is already configured and effective.
- PowerShell requirements: 15s in PowerShell 7 and 19s in Windows PowerShell 5.1.
- PowerShell formatting: 11s and 17s respectively.
- Visualization, QA smoke, and unsafe-path checks after conformance: 30s in PowerShell 7 and 25s in Windows PowerShell 5.1.
- Actionlint installation is intentionally ephemeral but currently negligible; caching it would add complexity without meaningful wall-clock benefit.

Fresh local aggregate measurements:

| Profile | Python | PowerShell 7 | Windows PowerShell 5.1 |
| --- | ---: | ---: | ---: |
| `fast` (8 suites) | 7.3s | 48.0s | 58.1s |
| `baseline` (14 suites) | 35.6s | 132.1s | 202.4s |

Fresh local compatibility measurements:

- `pull-request`: 71.958s; four checks passed and canonical outputs remained unchanged.
- `full-release`: 78.769s; five checks passed, including byte-identical three-runtime rendering.

Largest local suite costs:

- Python: source 11.43s, entity 8.11s, provenance 4.67s, reconciliation 3.73s.
- PowerShell 7: source 23.40s, lookup 19.95s, occurrence 19.48s, entity 14.28s, provenance 14.22s, reconciliation 13.33s.
- Windows PowerShell 5.1: occurrence 41.76s, source 39.77s, lookup 32.76s, reconciliation 20.78s, entity 20.25s, provenance 19.48s.

Estimated all-runtime GitHub `fast` wall-clock is roughly 2m-2m30s after current setup and smoke-test overhead. A Python-only fast branch job would likely complete in roughly 20-30s. These estimates require a temporary or adopted workflow shape for exact hosted-run measurement.

Post-consolidation manual full-release run `30777449898` at commit `e7204ee` passed all five jobs in 5m41s wall-clock:

| Job | Total | Dominant Step |
| --- | ---: | --- |
| Workflow Policy | 7s | Checkout/setup; actionlint remained negligible |
| Python Validation | 1m02s | Baseline conformance 55s |
| PowerShell 7 Validation | 2m32s | Baseline conformance 2m01s |
| Windows PowerShell 5.1 Validation | 5m16s | Baseline conformance 4m32s |
| Project Compatibility | 5m36s | Mermaid CLI installation 3m24s; full-release compatibility 1m35s |

The shared job-scoped PowerShell module path worked in both runtimes, Mermaid CLI `11.16.0` rendered three byte-identical outputs, and all canonical outputs remained protected. The nine-second wall-clock improvement understates the structural gain: duplicated consumer checks left the runtime jobs, compatibility now compares their semantics through one registry-owned gate, and PRs skip the full-release-only Mermaid setup.

## Phase 9: Extraction Readiness

- [ ] Confirm runtime modules contain no LoTM paths or vocabulary.
- [ ] Confirm narrative behavior lives in schema packs rather than the core runtime.
- [ ] Confirm LoTM configuration remains under `Project_Config/`.
- [ ] Confirm the framework can be copied without canonical LoTM content or generated outputs.
- [ ] Run the complete conformance, compatibility, static, and pressure-test baseline.
- [ ] Record the stabilized architecture in the framework evolution and extraction documentation.
