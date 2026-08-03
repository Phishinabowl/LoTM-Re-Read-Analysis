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

- [x] Confirm runtime modules contain no LoTM paths or vocabulary.
- [x] Confirm narrative behavior lives in schema packs rather than the core runtime.
- [x] Confirm LoTM configuration remains under `Project_Config/`.
- [x] Confirm the framework can be copied without canonical LoTM content or generated outputs.
- [x] Run the complete conformance, compatibility, static, and pressure-test baseline.
- [x] Record the stabilized architecture in the framework evolution and extraction documentation.

### Phase 9.1 Runtime Boundary Audit - 2026-08-02

The audit covered all 30 maintained files under `Tools/Runtime/`: the 15-module Python
`knowledge_framework` package and the matching 15-file PowerShell `KnowledgeFramework` module. Neither runtime contains LoTM project IDs, titles, entities, user or machine paths, canonical content-folder names, source-file defaults, or generated graph and QA artifact names.

`Project_Config/project.yaml` is the one fixed discovery path in both implementations. It is the framework's generic bootstrap-manifest convention, not a LoTM path. Content roots, resource roots, registry paths, QA output, visualization helpers, render configuration, and cleanup helpers are resolved from that manifest. LoTM-specific defaults that remain in command adapters, such as the local EPUB utilities, are outside the reusable runtime boundary and are not included in this portability claim.

### Phase 9.2 Pack Ownership Audit - 2026-08-02

The composed LoTM project selects one core pack and seven narrative domain packs. Of 945 composed controlled values, core owns 281 portable chronology, occurrence, state, provenance, reconciliation, and generic evidence-artifact values; the narrative packs own the remaining 664 domain values. Every `narrative.*` and `identity.*` value is domain-pack owned. Core's 18 `source.*` values are limited to a provenance-claim applicability target plus generic reference, transcript, translation, localization, scan, extract, edition, and package-membership evidence roles and relationships. Media, cultural form, work, segment, continuity, adaptation, manifestation, release, distribution, production, and shared-universe vocabularies remain outside core.

Runtime code owns deterministic ingestion, structural invariants, query mechanics, and evaluator implementations; schema packs declaratively own capability availability, controlled vocabulary, extension policy, structural-strategy selection, and semantic compatibility declarations. Packs therefore extend behavior through validated declarations rather than arbitrary executable code. The narrative source loader is an optional domain service within the reusable runtime package, while chronology, recurrence, state, provenance, and reconciliation kernels remain domain-neutral and accept narrative additions only through composed pack values.

Targeted `schema-pack`, `source`, `chronology`, and `occurrence` conformance passed with matching structured summaries in Python, PowerShell 7, and Windows PowerShell 5.1. The corpus includes 43 malformed pack compositions, 65 malformed source configurations, 15 invalid source queries, 13 malformed chronology fixtures, 67 malformed occurrence registries, and extension-defined occurrence semantics that alter validated behavior without an engine edit.

### Phase 9.3 Project Configuration Audit - 2026-08-02

All LoTM semantic project configuration remains in the eleven files under `Project_Config/`: the bootstrap manifest, pack selection and activation, taxonomy, resources, sources, entities, reconciliation, provenance, chronology, occurrences, and the composition baseline. The manifest is the sole registry locator, and no duplicate or shadow project registry was found elsewhere in the repository.

This boundary does not classify every project-specific file as configuration. Canonical Markdown and embedded page data remain authored content; `Visualization/data/refresh-snapshot.json` is generated regression evidence; and compatibility, static-policy, formatter, render, editor, and CI settings configure repository tooling rather than instantiate the LoTM world model. Reusable framework packs and synthetic fixtures contain no LoTM project IDs, titles, entities, or canonical paths. General narrative terms such as `donghua` remain correctly owned by reusable narrative packs.

The full project-composition suite passed with matching summaries in Python, PowerShell 7, and Windows PowerShell 5.1: 8 selected packs, 114 enabled and 9 disabled capabilities, 24 reconciliation target types, 53 provenance subject types, two deterministic composition passes, and seven rejected invalid compositions.

### Phase 9.4 Isolated Extraction Rehearsal - 2026-08-02

`Tools/Compatibility/verify_framework_extraction.py` now performs a repeatable standalone-copy rehearsal. It copies only `Framework/`, `Tools/Runtime/`, `Tools/Conformance/`, the Python and PowerShell dependency declarations, and the Python formatter policy into a unique operating-system temporary directory. It does not copy the LoTM `Project_Config/`; instead it generates a neutral core-only `extraction-smoke` consumer manifest and disposable registry placeholders.

The verifier rejects nine canonical or generated project surfaces, runs project-root, strict-ingestion, lookup-key, schema-pack, and temporal conformance from inside the copied tree, compares structured summaries across Python, PowerShell 7, and Windows PowerShell 5.1, and removes the temporary tree on exit. The first rehearsal copied 202 reusable files and passed all five suites in all three runtimes with no LoTM configuration, canonical content, source material, QA export, visualization state, or generated output present.

The permanent `framework-extraction` compatibility check is included in `pull-request` and `full-release` profiles. It remains outside `local` so the three-runtime isolated copy does not slow the rapid Visualization/QA implementation loop.

### Phase 9.5 Complete Stabilization Baseline - 2026-08-02

The complete static gate passed: actionlint accepted all workflows; Ruff reported all 38 Python files formatted and lint-clean; the work-annotation linter checked 304 files and all 22 fixtures with zero findings; and the PowerShell formatter found 39 clean files, zero changes, and zero over-limit lines in both PowerShell 7 and Windows PowerShell 5.1.

All 14 registered baseline conformance suites passed in Python, PowerShell 7, and Windows PowerShell 5.1 with matching semantic summaries. This includes the complete canonical and synthetic project, ingestion, lookup, pack, taxonomy, resource, source, entity, provenance, temporal, chronology, reconciliation, occurrence, and composition coverage; all malformed and invalid-query corpora; the 1,500-hop reconciliation chain and configured limits; and the registered 64-, 128-, and project-oracle scale cases.

The `full-release` compatibility profile passed all six checks in 148.044 seconds. Visualization remained at 15 nodes and 121 relationships; 34 QA files and their 16-note, 121-relationship, 71-data-reference summary matched across runtimes; all 12 root-launch combinations passed; stale and scoped artifacts were removed while unrelated content was preserved; six unsafe destinations were rejected; the 202-file isolated framework copy passed; and each runtime rendered the same nonblank 298,269-byte SVG with SHA-256 `11b9e70f735004641ab0bd348c21451d1cc2852327caa58d092dd045dfb59f73`. Canonical outputs remained unchanged and compatibility output was cleaned.

The retained pressure portfolio was reviewed under `Framework/testing_methodology.md`. `PRESSURE-LAYER-PORTABILITY` received new executable evidence from the neutral core-only copy. The work/continuity, media/distribution, evidence/authority, entity/identity, temporal/topology, recurrence/state, Derrick, and Loki conclusions remain supported by unchanged green model suites and the V37 record. Adversarial malformed input, unsafe output, ambiguity, cycle, limit, and scale probes all remained green. Conceptual narrative and synthetic IT/operations, medical, legal/compliance, investigative, and scientific replays found no new ownership leak or extraction defect. They do not claim that a non-narrative pack or IT proof of concept already exists.

The replay preserved the V38 recommendation. Empty-vocabulary orphan effect declarations, delimiter-composed effect semantics, and conflict-wide fail-closed execution remain known next-version work; uncertain recurrence cardinality, repeated participation, extratemporal relations, branch lifecycle, and deeper knowledge-acquisition semantics remain later staged capabilities rather than Phase 9 regressions.

### Phase 9.6 Stabilized Extraction Record - 2026-08-02

`Framework/extraction_readiness.md` now separates the proven portable kernel from the eventual complete framework product. It records the exact copy allowlist, project-owned configuration/content boundary, nine enforced exclusions, verification commands, measured baseline, pressure-test conclusion, and known remaining architecture stages. `ARCHITECTURE.md` and `Framework/README.md` point to that status record.

Phase 9 therefore closes the CI implementation plan with an extraction-ready framework foundation: reusable contracts, packs, paired runtimes, conformance, and dependency policy can be copied and validated without LoTM instances. It does not prematurely mark Visualization consolidation, a separate physical repository, an IT pack/POC, mutation services, or the Streamlit interface complete.
