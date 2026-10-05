# CI Testing Coverage And Consumer Dependency Ledger

Phase 1.2 inspection baseline: `268ac9d7930377d3ba789e64978fbb1bf3635ea0`, on
`architecture/ci-testing-modernization`, inspected 2026-10-03. This document records current
coverage, consumer dependencies, and proposed implementation-test ownership. It does not register
tests or certify a new run. Phase 1.3 will review its durable location and the executable contracts.

The [modernization plan](ci-testing-modernization-plan.md) owns delivery checkpoints.
[Testing Methodology](../Framework/testing_methodology.md) owns cumulative requirements and stable
coverage-family IDs. [Conformance registry](Conformance/suites.json) and
[compatibility registry](Compatibility/compatibility.json) remain executable membership authorities.
[Tooling Reference](TOOLING_REFERENCE.md) owns detailed command/API documentation.
[Validation reporting](../Framework/Contracts/validation-run-reporting.md) owns existing report semantics.
Changes to those authorities require review; this inventory cannot silently override them.

**Evidence labels:** Current means inspected executable behavior; retained means documented required
pressure or review without an equivalent registered executable family; proposed means future work.
Ownership below means a repository component and delivery checkpoint, not a newly assigned person.
There is no independent pytest or Pester implementation-test catalog in this baseline.

## Current Conformance Ownership

All 21 registered suites have Python and PowerShell implementations. The PowerShell implementation
runs in both PowerShell 7 and Windows PowerShell 5.1. The registry defines `fast` (10) and `baseline`
(21), ordered membership, source paths, and discovery. This table is explanatory, not a second list
for execution. Fixture paths below are relative to `Framework/Data/` unless stated otherwise.
Suite filenames reside in `Tools/Conformance/Suites/`; the registry supplies their exact spelling.

| Stable family | Registry ID / paired executable stems | Fixture owner and present scope |
| --- | --- | --- |
| `CONF-PROJECT-ROOT` | `project-root`: `test_project_paths.py`, `Test-Project-Paths.ps1` | Synthetic temporary projects; manifest, explicit/environment/cwd/executable discovery, failures and caller location. |
| `CONF-FRAMEWORK-INSTALLATION` | `framework-installation`: `test_framework_installation.py`, `Test-Framework-Installation.ps1` | `Framework-Installation`; isolated installation/attachment and synthetic roots. |
| `CONF-FRAMEWORK-CATALOG` | `framework-catalog`: `test_framework_catalog.py`, `Test-Framework-Catalog.ps1` | `Framework-Catalog`, `Schema-Packs`; catalog structure, invalid packs and generated scale cases. |
| `CONF-CAPABILITY-ROADMAP` | `capability-roadmap`: `test_capability_roadmap.py`, `Test-Capability-Roadmap.ps1` | `Capability-Roadmap`; valid catalog/roadmap and malformed or inconsistent relationships. |
| `CONF-STRICT-INGESTION` | `strict-ingestion`: `test_strict_yaml.py`, `Test-Strict-Yaml.ps1` | `Strict-Yaml`; accepted/rejected YAML, byte/syntax/key boundaries and parser limits. |
| `CONF-LOOKUP` | `lookup-key`: `test_lookup_key.py`, `Test-Lookup-Key.ps1` | `Lookup-Key`, Unicode 16.0.0 table and regression vectors; normalization, collisions and boundaries. |
| `CONF-PACK-COMPOSITION` | `schema-pack`: `test_schema_pack.py`, `Test-Schema-Pack.ps1` | `Schema-Packs`; ordering, closure, isolation, delimiter collisions, invalid composition and generated scale. |
| `CONF-DISTRIBUTION-BOUNDARY` | `distribution-boundary`: `test_distribution_boundary.py`, `Test-Distribution-Boundary.ps1` | `Distribution-Boundary`, `Schema-Packs`; inert external metadata, unchanged portable outputs and forbidden semantic additions. |
| `CONF-TAXONOMY` | `taxonomy`: `test_taxonomy.py`, `Test-Taxonomy.ps1` | `Taxonomy`; valid/invalid classification, references and generated scale. |
| `CONF-RESOURCE` | `resource`: `test_resource.py`, `Test-Resource.ps1` | `Resources`; valid/invalid resource configuration and generated scale. |
| `CONF-EFFECTIVE-SCHEMA` | `effective-schema`: `test_effective_schema.py`, `Test-Effective-Schema.ps1` | `Effective-Schema` plus composition inputs; complete schema, selectors, invalid classification, report/QA projection and generated scale. |
| `CONF-SOURCE` | `source`: `test_source.py`, `Test-Source.ps1` | `Sources`; source identity, coverage, references and malformed input. |
| `CONF-ENTITY` | `entity`: `test_entity.py`, `Test-Entity.ps1` | `Entities`, `Taxonomy`, `Sources`; entity identity, relationships and invalid references. |
| `CONF-PROVENANCE` | `provenance`: `test_provenance.py`, `Test-Provenance.ps1` | `Provenance` and composed target registries; target paths, evidence resolution, rejection and provider closure. |
| `CONF-TEMPORAL` | `temporal`: `test_temporal.py`, `Test-Temporal.ps1` | `Temporal`; coordinates, precision, bounds, query decisions and invalid time values. |
| `CONF-CHRONOLOGY` | `chronology`: `test_chronology.py`, `Test-Chronology.ps1` | `Chronology`; positions, bindings, topology, ordering/closure and generated scale. |
| `CONF-RECONCILIATION` | `reconciliation`: `test_reconciliation.py`, `Test-Reconciliation.ps1` | `Reconciliation`, strict ingestion dependencies; resolution, ambiguity, cycles and deep chains. |
| `CONF-OCCURRENCE` | `occurrence`: `test_occurrence.py`, `Test-Occurrence.ps1` | `Occurrence`, `Chronology`; recurrence/state/participation/extension decisions, invalid cases and scale. |
| `CONF-HOSTING` | `hosting`: `test_hosting.py`, `Test-Hosting.ps1` | `Hosting`, occurrence/chronology/interpretation inputs; carrier topology, occupancy, pack isolation and scale. |
| `CONF-INTERPRETATION` | `interpretation`: `test_interpretation.py`, `Test-Interpretation.ps1` | `Interpretations`; shared records, candidate structures, composed references and scale. |
| `CONF-PROJECT-COMPOSITION` | `project-composition`: `test_project_composition.py`, `Test-Project-Composition.ps1` | `Project_Config/composition-baseline.json` and configured registries; composed counts, provider closure and capability-disabled cases. |

The suites already contain substantial negative, exact-decision, ambiguity and generated scale
coverage. Native test migration must inventory assertions before deciding what to replace. It must
not claim these classes are missing merely because they are embedded in custom suite scripts.

## Current Compatibility, Static And Parity Ownership

Compatibility is a single Python cross-runtime referee in `Compatibility/run_compatibility.py`.
Its 11 registry checks dispatch to `run_<kind>_check` handlers (hyphens become underscores).
Registered timeouts bound individual subprocess calls; they are not whole-check deadlines.
Profiles are `local` (6), `pull-request` (9), `distribution-boundary` (8), `full-release` (11).

| Existing family | Check ID | Current proof and important boundary |
| --- | --- | --- |
| `COMPAT-VALIDATION-REPORTING` | `compatibility-reporting` | Python referee self-tests through a private nonrecursive registry: success/failure, JSON/report envelopes, confinement and retained evidence. |
| `COMPAT-VALIDATION-REPORTING` | `conformance-reporting` | Three-runtime aggregate help, concise/detailed reports, failures, excerpt limits, confinement and report cleanup. These are reporting probes, not an exhaustive supervisor regression suite. |
| `COMPAT-FRAMEWORK-CATALOG` | `framework-catalog` | Three-runtime full catalog/project view, exports, human reports, selectors, compound filters and representative failures. |
| `COMPAT-EFFECTIVE-SCHEMA` | `effective-schema` | Three-runtime schema, selection envelopes, human/QA reports, exports and representative invalid inputs. |
| `COMPAT-VISUALIZATION` | `visualization` | Three-runtime configured/bounded/unbounded projections, Mermaid and normalized snapshot/file hashes against `Baselines/lotm-consumers.json`. |
| `COMPAT-QA` | `qa` | Three-runtime redirected QA, bounded page/graph outputs, effective-schema report, reviewed 35-file inventory and hashes from the same baseline. |
| `COMPAT-ROOT-DISCOVERY` | `root-discovery` | Launches the project-root conformance suite from root, Tools, nested and unrelated cwd in three runtimes. Does not launch every production command from each position. |
| `COMPAT-ARTIFACT-LIFECYCLE` | `artifact-lifecycle` | Python QA rerun/stale removal and destructive cleanup; three-runtime unsafe destination rejection and cleanup dry-run comparison. PowerShell destructive behavior is not equivalently exercised. |
| `COMPAT-FRAMEWORK-EXTRACTION` | `framework-extraction` | Python extraction referee; isolated neutral consumer runs nine portable suites in three runtimes and compares detailed summaries. |
| `CONF-DISTRIBUTION-BOUNDARY`, parity families | `distribution-boundary` | Executes paired distribution suite in three runtimes and compares inert-provider/portable-output results. Present in distribution/full profiles, absent from PR profile. |
| `COMPAT-RENDER` | `render` | Three-runtime redirected representative graph rendering, output-size/label checks. Full-release profile; external rendering dependencies apply. |

| Family | Current executable/policy owner | Proposed regression owner |
| --- | --- | --- |
| `STATIC-PYTHON` | Ruff, `pyproject.toml`, `.gitattributes`, Python dependency declaration; repository formatting/line-length checks | pytest regression only for repository-owned discovery/adapters; Ruff semantics remain upstream. |
| `STATIC-POWERSHELL` | `Static/Format-PowerShell.ps1`, `powershell-format-settings.psd1`, Git inventory and parser/token preservation in both hosts | Pester formatting fixtures: discovery, encodings, token preservation, limits, check/fix and diagnostics. |
| `STATIC-WORK-ANNOTATIONS` | `Static/lint_work_annotations.py`, policy JSON, `Fixtures/Work-Annotations/cases.json` (22 cases), standards/Todo Tree exclusions | Retain fixture conformance; pytest filesystem/Git discovery, policy errors, CLI and report regressions. |
| `STATIC-GITHUB-ACTIONS` | actionlint and checksum-pinned installer in `.github/workflows/ci.yml`; workflow pins, permissions, timeouts/check names | Repository policy tests for owned rules; retain actionlint locally and hosted. Future ADO policy needs an explicit contract. |
| `PARITY-THREE-RUNTIME` | Paired conformance and Python compatibility referee | Explicit cross-runtime comparison owner; three independent green baseline jobs alone do not compare all suite summaries. |
| `PARITY-STRUCTURED-OUTPUT` | Compatibility reporting/command checks, semantic baseline normalization, extraction comparison | Preserve detailed/concise/artifact contracts; regression tests for only permitted normalization. |
| `PARITY-COMMAND-SURFACE` | Reporting help probes and catalog/schema/consumer command checks | Adapter integration tests plus parity checks for currently unexercised defaults, switches and failures. |

Current GitHub CI has workflow policy, Python static/baseline, PowerShell 7 static/baseline,
Windows PowerShell 5.1 static/baseline, and compatibility jobs. Work annotations run in the Python
job and a separate workflow. ADO has repository parity but no pipeline in this baseline. Preserve
existing check identities and duplicate gate behavior until Phase 1.5 defines migration impact.

## Proposed Implementation-Test Ownership

Python owns pytest unit/integration tests; PowerShell owns Pester **6.2.0** unit/integration tests in
the adopted PS7 host. D14 retires 5.1 through CI Phase 2; the current three-runtime inventory above
remains the inspected pre-retirement baseline. Shared fixtures and paired conformance retain authority.
Native tests should add implementation failure modes and isolate defects without copying the whole
neutral assertion set. The Phase 3 pilot and later regression phases must prove coverage alongside
existing runners before retirement. Exact dependency separation belongs to Phases 1.4/3.1.

There are **22 Python package files**, **20 PowerShell private scripts**, and the PowerShell root
module/manifest. Python names below are under `Runtime/Python/knowledge_framework/`; PowerShell
private files are under `Runtime/PowerShell/KnowledgeFramework/Private/`.

| Python file(s) | PowerShell implementation | Proposed native ownership and existing semantic owner |
| --- | --- | --- |
| `__init__.py` | `KnowledgeFramework.psm1`, `KnowledgeFramework.psd1` in module root | Import/export contracts, fresh-process import, supported host, no unexpected side effects; installation suite. |
| `framework_paths.py`, `project_paths.py` | Root-resolution functions in root module | Filesystem/error/env restoration and caller-location isolation; installation/project-root suites. |
| `strict_yaml.py` | `Strict-Yaml.ps1` | Parser adapter, byte/I/O failures and dependency errors; strict-ingestion suite. |
| Serialization helpers distributed through Python modules | `Serialization.ps1` | JSON/YAML serialization, encoding, deterministic ordering and write failures; reporting/structured parity. |
| `framework_config.py`, `project_config.py` | `Framework-Config.ps1`, `Project-Config.ps1` | Loader/cache/path/error handling and malformed manifests; installation/composition. |
| `lookup_key_config.py` | `Lookup-Key-Config.ps1` | Lookup implementation and table loading failures; lookup-key. |
| `schema_pack_config.py` | `Schema-Pack-Config.ps1` | Discovery, merge/provider boundaries, dependency failure and I/O; schema-pack/distribution. |
| `framework_catalog.py`, `capability_roadmap.py` | `Framework-Catalog.ps1`, `Capability-Roadmap.ps1` | Catalog/roadmap construction, selective imports, adapters and report failures; corresponding suites. |
| `taxonomy_config.py`, `resource_config.py` | `Taxonomy-Config.ps1`, `Resource-Config.ps1` | Registry loading, path/errors and internal traversal; taxonomy/resource. |
| `effective_schema.py` | `Effective-Project-Schema.ps1` | Composition service, selection/report serialization and consumer seams; effective-schema/composition. |
| `source_config.py`, `entity_config.py` | `Source-Config.ps1`, `Entity-Config.ps1` | Loader/reference implementation and missing-provider failures; source/entity. |
| `temporal_config.py`, `chronology_config.py` | `Temporal-Config.ps1`, `Chronology-Config.ps1` | Parsing/query/traversal implementation and limits; temporal/chronology. |
| `reconciliation_config.py` | `Reconciliation-Config.ps1` | Resolution internals, chain/cycle/error handling; reconciliation. |
| `occurrence_config.py` | `Occurrence-Config.ps1` | State/effect/participation internals and closure failures; occurrence. |
| `interpretation_config.py` | `Interpretation-Config.ps1` | Candidate isolation/provider failures; interpretation. |
| `hosting_config.py` | `Hosting-Config.ps1` | Carrier traversal/occupancy implementation and provider failures; hosting. |
| `provenance_config.py` | `Provenance-Config.ps1` | Target routing/resolution and implementation exceptions; provenance/composition. |

Every Pester file must establish its own discovery/setup dependencies. Do not depend on another
test file's top-level execution or ordering to supply helper functions. Child-process isolation and
environment restoration must be tested separately from successful semantic results.

### Command Adapter Consumers

| Current command files | Current coverage / proposed pytest and Pester integration owner |
| --- | --- |
| `Commands/Framework/inspect_framework_catalog.py`, `Get-FrameworkCatalog.ps1` | Catalog compatibility; extend parsing/help/default/root and report-write failure matrices. |
| `Commands/Framework/inspect_effective_schema.py`, `Get-EffectiveProjectSchema.ps1` | Effective-schema compatibility; same adapter matrix plus project-only selection boundaries. |
| `Commands/QA/obsidian_qa_export.py`, `Obsidian-QA-Export.ps1` | QA/lifecycle compatibility; redirected generation, stale removal, cleanup and canonical guard tests. |
| `Commands/Maintenance/clean_temp_files.py`, `Clean-TempFiles.ps1` | Lifecycle dry-run parity/Python deletion; add owned temporary fixtures for both PowerShell destructive paths. |
| `Commands/Media/search_epub.py`, `Search-Epub.ps1` | Documented helper; no registered dedicated integration check. Add synthetic owned EPUBs for filters, aliases, boundaries and malformed archives; do not require copyrighted local source books. |
| `Commands/Media/edit_image.py`, `Edit-Image.ps1` | Documented helper; no registered dedicated integration check. Add owned tiny-image/archive fixtures, operation/preset/output safety and dependency/platform cases. Decide supported image semantics before claiming pixel parity. |
| `Commands/Environment/Test-Python.ps1`, `Test-PowerShell.ps1` | Availability probes, not exact dependency-version certification. Pester: discovery, absent tools, requirement parsing and truthful status. |
| `../Visualization/visualize.py`, `../Visualization/visualize.ps1` | Visualization/render compatibility; native tests for argument aliases, settings, errors and process boundaries. Retain current location during CI work. |
| `Conformance/run_conformance.py`, `Run-Conformance.ps1` | Existing registry/reporting probes; pytest/Pester registry validation, process/error/timeout contracts and CLI integration. |
| `Compatibility/run_compatibility.py`, `verify_framework_extraction.py` | Python referee/extraction checks; pytest dispatch, failure continuation, deadlines, normalization, copy policy and actual cleanup verification. |
| `Static/lint_work_annotations.py`, `Format-PowerShell.ps1` | Existing policy execution; native implementation regression as above. |

Exact switch maps stay in Tooling Reference. Trace root/help/JSON/report switches; catalog/schema
selection/filter/export switches; QA bounded/stub/clean switches; cleanup delete/tmp switches;
EPUB chapter/volume/entry/query/context/count/regex aliases; image crop/preset/extract/force switches;
and Visualization mode/input/output/graph/settings/no-render aliases. File-producing Visualization
has structured artifacts; it does not expose a universal generic `--json` summary.

## Retained Scenario And Pressure Ownership

The following stable families are methodology requirements. The inspected executable suite set does
not supply named source-grounded story probes equivalent to all these requirements. Primitive
coverage below is supporting evidence, not a declaration that an entire narrative matrix passed.
Framework maintainer review owns concrete probe selection and unsupported findings. Reproducible
defects should become permanent fixtures. Phase 1.3 must preserve retained/pending states; later
pressure profiles need explicit registration, budgets and evidence rather than automatic pass marks.

| Retained scenario | Supporting executable owner(s); retained review focus |
| --- | --- |
| `SCENARIO-DERRICK` | occurrence, chronology, provenance; awareness, iterations, reset/exit. |
| `SCENARIO-LOKI` | occurrence, chronology, provenance, project-composition; branches, recurrence, knowledge versus capability. |
| `SCENARIO-PRIMER` | interpretation, chronology, provenance; unresolved competing reconstructions. |
| `SCENARIO-ARRIVAL` | occurrence, chronology, temporal; backward causality and participant order. |
| `SCENARIO-MEMENTO` | interpretation, occurrence, provenance; presentation/experience/evidence separation. |
| `SCENARIO-DOCTOR-WHO` | occurrence, chronology, entity; participant-relative chronology and identity. |
| `SCENARIO-WESTWORLD` | hosting, entity, occurrence, provenance; carriers, copies, occupancy and divergence. |
| `SCENARIO-PARODY-DERIVATION` | schema-pack, distribution-boundary, source; derivation without inferred rights/canon. |
| `SCENARIO-CONTINUITY-IDENTITY` | entity, reconciliation, hosting; identity across continuities and embodiments. |
| `SCENARIO-MARVEL-SHARED-UNIVERSE` | entity, chronology, source; shared continuity, identity and publication structure. |
| `SCENARIO-DC-CONTINUITY-REWRITES` | entity, reconciliation, chronology; rewritten history without erased identity. |
| `SCENARIO-COLLABORATIVE-CANON` | source, provenance; stewardship versus factual authority. |
| `SCENARIO-VERSIONED-RULESETS` | schema-pack, source, provenance; normative policy; unsupported capabilities remain explicit. |
| `SCENARIO-LIVE-SERVICE-NARRATIVE` | occurrence, source, chronology; collective/live state and replay. |
| `SCENARIO-RECONSTRUCTED-MEDIA` | source, provenance, interpretation; reconstruction and preservation. |
| `SCENARIO-SERIALIZED-ADAPTATION` | source, schema-pack, chronology; adaptation and irregular release structure. |
| `SCENARIO-TEXTUAL-TRADITION` | source, provenance, interpretation; versions, evidence and stewardship. |

| Retained pressure family | Supporting executable owner(s); retained review boundary |
| --- | --- |
| `PRESSURE-CROSS-DOMAIN` | All relevant semantic suites and extraction; actual narrative/IT/medical/legal probes remain required. |
| `PRESSURE-ADVERSARIAL` | All relevant suite negative cases; add change-specific contradictory/ambiguous/collision probes. |
| `PRESSURE-SCALE` | Generated suite scale/limit cases; change-specific deep/wide complexity and termination measurements. |
| `PRESSURE-LAYER-PORTABILITY` | installation, schema-pack, project-composition, extraction; core/pack/project ownership. |
| `PRESSURE-WORK-CONTINUITY` | schema-pack, source, entity; derivative/continuity and rights/canon distinctions. |
| `PRESSURE-MEDIA-DISTRIBUTION` | source, distribution-boundary, chronology; manifestation/release/platform/order distinctions. |
| `PRESSURE-EVIDENCE-AUTHORITY` | source, provenance, interpretation; scoped authority, ties and indeterminate findings. |
| `PRESSURE-RULESET-POLICY` | schema-pack, source, provenance; ruleset semantics may remain unsupported. |
| `PRESSURE-ENTITY-IDENTITY` | lookup-key, entity, reconciliation, hosting; mixed-continuity/identity probes. |
| `PRESSURE-TEMPORAL-TOPOLOGY` | temporal, chronology, occurrence; chronology versus causality/topology. |
| `PRESSURE-RECURRENCE-STATE` | occurrence, chronology, provenance; recurrence, cardinality and state carryover. |
| `PRESSURE-EPISTEMIC-STATE` | occurrence, schema-pack, provenance; understanding/access/belief boundaries. |
| `PRESSURE-CAPABILITY-STATE` | occurrence, schema-pack, provenance; proficiency versus credentials and knowledge. |
| `PRESSURE-TEMPORAL-COMPOSITION` | occurrence, chronology, provenance, project-composition; integrated narrative/non-narrative replay. |
| `PRESSURE-STRUCTURAL-INTERPRETATION` | interpretation, provenance, chronology; unresolved hypotheses and canonical isolation. |
| `PRESSURE-PARTICIPANT-CHRONOLOGY` | occurrence, chronology; multi-clock and repeated-participation boundaries. |
| `PRESSURE-HOSTED-IDENTITY` | hosting, entity, occurrence, reconciliation; physical/virtual carriers and indirect occupancy. |

## Consumer Contracts And Migration Constraints

| Current public consumer | Confirmed dependency / required migration protection |
| --- | --- |
| Suite selection/discovery | `suites.json` schema 1, paired paths, ordered profiles, `test_*.py`/`Test-*.ps1` discovery and exclusions. Both runners reject invalid registry/path/discovery states. New pytest filenames must not accidentally become unregistered conformance suites. |
| Compatibility selection | Registry schema 2, three runtimes, ordered profiles/check kinds/timeouts; Python dispatch. New catalog references must not duplicate membership authority. |
| Aggregate CLI | Conformance repeated `--suite` deduplicates preserving first order; compatibility repeated `--check` rejects duplicates. Preserve or explicitly version this difference. List/help/report combinations have validation rules. |
| Detailed JSON | Conformance schema 1 includes ordered suite summaries/errors; compatibility detailed schema 1 differs from its registry version. Extraction and reporting probes consume complete nested objects. Do not substitute concise JSON. |
| Concise v1 | `validation-run-summary`, contract-first field ordering, selected/result/failure counts, elapsed time, canonical status, report retention/path. Failure excerpts bound to 20 lines/4096 UTF-8 bytes. Keep native report projections outside these existing envelopes until reviewed. |
| Report files | Detailed UTF-8 without BOM, LF/final newline, root-confined explicit paths and owned automatic reports. Reporting probes normalize only permitted duration/path differences; preserve exact decision/error meaning and failure evidence. |
| Baselines | `Compatibility/Baselines/lotm-consumers.json` semantic/file/tree hashes; `Project_Config/composition-baseline.json` composed oracle. Only documented generated timestamp/operational metadata normalization is allowed. Regeneration requires semantic review. |
| Extraction copy policy | `verify_framework_extraction.py` copies `Framework`, `Tools/Runtime`, `Tools/Conformance`, `pyproject.toml`, Python/PowerShell requirements. Does not copy Commands, Compatibility, Static, future CI infrastructure or Node requirements. Dependency splits must update this consumer deliberately. |
| Extraction portable selection | Explicit nine: project-root, framework-installation, framework-catalog, capability-roadmap, strict-ingestion, lookup-key, schema-pack, temporal, interpretation. This is not the complete 21-suite baseline. Neutral consumer is synthesized; LoTM configuration/content is excluded. |
| Environment/root discovery | `KNOWLEDGE_PROJECT_ROOT`, `KNOWLEDGE_FRAMEWORK_ROOT`; explicit/env/cwd/executable behavior, invalid overrides and caller location. Compatibility sets `PYTHONUTF8=1`; hosted module discovery uses `PSModulePath` and an owned runner temporary module path. |
| Dependency declarations | Python: PyYAML minimum and pinned Ruff; PowerShell: unpinned YAML/PSScriptAnalyzer; Node: pinned rendering packages. Pester/pytest are locally available but not yet integrated into repository declarations/catalogs. Image Python imports Pillow without a matching current requirements entry. |
| Availability probes | Environment commands discover executables/modules/imports; they do not certify all exact version constraints. Version-qualified requirements/imports need regression coverage before changing their parsing assumptions. |
| Hosted consumers | GitHub YAML currently owns installation/job dispatch and summaries. Preserve required check names while moving execution semantics into locally reproducible owners. ADO Tests XML and Markdown need projections of the same truthful result state; non-native suites remain identifiable custom tests. |
| Canonical protection | Compatibility snapshots configured settings/report/snapshot/graph/render paths and existing QA export. It is not a whole-tree guard for authored pages, templates, Relationship Seeds and all configuration. New mutation tests must use owned temporary fixtures plus a broader explicit guard. |

Compatibility currently stops after a check exception. It does not attempt every later check or
provide a complete supervisor skipped/cancelled result model. Timeouts are per subprocess, so
multiple launches can exceed a registry timeout in aggregate. These behaviors cannot be treated as
the target supervisor contract. Likewise the extraction summary's cleanup declaration is not an
independent regression assertion observing the temporary directory after context exit.

## Current Transitive Dependencies And Conservative Selection

Python import inspection supplies a minimum graph, not a complete dependency proof: data paths,
dynamic/local imports, manifests and command settings add edges. PowerShell imports all 20 private
scripts through its root module. Filename-level matching alone cannot justify skipping consumers.

| Implemented dependency area | Present downstream consumers | Proposed safe selection until bounded |
| --- | --- | --- |
| Root/package/module loading, strict YAML, project/framework config | Registry loaders, semantic suites, commands, extraction; PowerShell module imports | Complete implementation/conformance/compatibility coverage for foundational changes. |
| Schema packs, lookup, taxonomy/resources, framework catalog/roadmap | Effective schema, project composition, source/entity and composed services; QA/Visualization | Full coverage where provider/composition impact is uncertain; catalog/roadmap have local import edges in both directions. |
| Temporal/chronology | Occurrence, source, provenance, interpretation/hosting through composed references, bounded projections | Full semantic/parity and downstream project compatibility unless a validated graph proves narrower impact. |
| Occurrence/interpretation/hosting/reconciliation/entity/source | Provenance routing and project-composition consumers; semantic fixtures share registries | Include dependent suites and composed/project consumers; unresolved target/provider edges force full selection. |
| Effective schema and configured projections | QA, Visualization, compatibility baselines, generated reports | Include both consumers, parity, lifecycle and relevant rendering; retain canonical guards. |
| Registries, runner/report logic, extraction, dependency/bootstrap, shared CI infrastructure | Every registered family and its reporting/local/hosted consumers | Complete relevant suite/profile set; no no-impact decision from docs or extension matching alone. |
| Shared fixture directories/expectations/normalization | Multiple suites and cross-runtime oracles | Follow explicit fixture edges; absent mapping means full fallback. |
| Policy/config/workflows | Static tools and hosted gates; workflow changes may alter all execution | Policy regression plus existing checks; changed host/runtime semantics require full profile evidence. |
| Unknown, deleted, renamed, external or indeterminate paths / missing Git comparison evidence | Impact cannot be safely resolved | Explainable full-profile fallback; do not infer future storage paths. |

No affected selector is implemented by this document. Phase 1.3 must define the meaning of full
selection by requested profile, required host capability and expensive/manual retained coverage;
an unavailable runtime or retained human review must remain visible rather than count as a pass.

## Gap And Checkpoint Ledger

| Gap | Current limitation / proposed owner | Delivery checkpoint |
| --- | --- | --- |
| G01 | No native implementation registration or complete runner/selector meta-regression catalog; add pytest/Pester tests without replacing shared fixtures. | Phases 3.3, 4.1-4.6. |
| G02 | Formatter lacks a dedicated permanent fixture harness; annotation fixtures do not exhaust Git/discovery/I/O/report regressions. | Phases 3.3, 4.4, 4.6, 5.1. |
| G03 | Root-discovery matrix exercises the root suite, not every adapter; media/environment adapter boundaries have no dedicated registered tests. | Phases 3.3, 5.1, 5.3; required synthetic media PR scope accepted in D12. |
| G04 | Lifecycle destructive mutation/stale removal exercised in Python; PowerShell gets rejection/dry-run evidence. | Phases 3.3, 5.3 before retirement in 8.1. |
| G05 | Current protected paths do not guard the complete canonical page/template/Relationship Seeds boundary. | Phases 1.3, 3.2, 5.3. |
| G06 | Availability checks and extraction copies constrain dependency splitting/pinning; Phase 1.4 proposes exact portable/dev/media declarations. Pillow scope is accepted, declaration/clean install proof remains pending. | Phases 1.4, 3.1, 5.4; see runtime/dependency/budget design and D12. |
| G07 | Custom reports have no native XML test projection; retained pressure families have no automatic per-story pass evidence. | Phases 1.3, 4.5, 6.4; retained review at 5.5. |
| G08 | Per-call timeouts and fail-fast compatibility do not guarantee whole-check budgets, cancellation or continued coverage. Phase 1.4 full release failed at the 360-second extraction limit after eight passes; later checks were unattempted. | Phases 1.4, 4.3, 4.4, 4.6; measured evidence in runtime/dependency/budget design. |
| G09 | Three green runtime jobs do not compare all 21 nested suite outputs; extraction compares only nine. | Phases 1.3, 5.2, 5.4. |
| G10 | Baseline/report normalization and temporary extraction cleanup need implementation-level regression proof. | Phases 3.3, 4.5, 5.3, 5.4. |
| G11 | Shared modules/data/provider relationships make simplistic affected selection unsafe. | Phases 1.3, 4.2, 4.6, 7.1. |
| G12 | Annotation duplicate gates/check-name dependencies and future ADO policy/report publication need staged migration evidence. | Phases 1.5, 6.2-6.5. |
| G13 | Extraction/root fixtures require unrelated ancestors; overriding TEMP under the repository invalidates that probe. A timeout retained owned external scratch despite parent exit; actual cleanup needs independent verification. | Phases 3.2, 4.3, 4.6, 5.4; D13 and Phase 1.4 evidence. |
| G14 | Accepted 5.1 retirement requires coordinated module/preflight, QA child-host, registry/extraction/report-count and hosted-check migration. Preserve all 21 suites, 11 check families and nine extraction suites; prove Python/PS7 semantics before retiring the host gate. | Phases 2.1-2.6; D14; budgets refreshed at 2.5. |

### Runtime Retirement Inventory (2026-10-05)

The read-only consumer audit found no feature uniquely requiring Desktop/5.1 and no registered
external consumer. The maintainer additionally confirms nobody else has a copy of the project.
Current GitHub main/framework branches reported `protected: false`; ADO pipeline inventory was empty.
Refresh protections/policies before check retirement; these observations do not authorize activation.

| Actual consumer / declaration | Required migration / proof |
| --- | --- |
| `Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` | Current minimum 5.1 and Desktop/Core declaration become the reviewed PS7 minimum/Core support; preserve exports and reject unsupported hosts. |
| `Commands/Environment/Test-PowerShell.ps1`, conformance launch boundaries | Readiness validates actual host/edition; retained suites use the approved PS7 executable; verify early unsupported-host failures. |
| `Commands/QA/Obsidian-QA-Export.ps1` | Three hardcoded `powershell` children perform refresh, bounded graphs and cache cleanup even under a PS7 parent. Migrate resolved hosts and prove unchanged outputs/side effects. |
| `Compatibility/compatibility.json`, `run_compatibility.py` | Strict runtime list, discovery and synthetic reporting registry require all three hosts today. Coordinate two-runtime acceptance and derive runtime-dependent reporting case counts truthfully. |
| `Compatibility/verify_framework_extraction.py` | Independent three-host discovery must become Python/PS7; preserve neutral consumer, all nine suites, copy boundary and actual removal proof. |
| `.github/workflows/ci.yml` | Retire the dedicated 5.1 job only after retained proof and fresh policy inspection; preserve retained gates/events and nested compatibility coverage. |
| Active help/docs/contracts/platform gates | Replace current `powershell` recipes/support promises through coordinated support adoption; retain historical test evidence. No file extension or helper path rename is needed. |
| `Commands/Media/Edit-Image.ps1`, `Search-Epub.ps1` | System.Drawing/compression use needs retained Windows/PS7 fixture proof. Host retirement does not automatically promise Linux media support or remove Windows CI. |

This inventory updates planned ownership only. No executable/support metadata, active framework
contract, workflow, dependency declaration or canonical content is changed by the planning pass.

For each implementation increment, preserve positive cases, malformed/minimal inputs, boundary and
ambiguity decisions, exact errors, scale/termination, report success/failure, cleanup, canonical
protection and applicable parity. Mark unsupported or retained review explicitly. Coverage can be
retired only after parallel old/new evidence proves equivalence or improvement and the rollback
point remains usable. This ledger inventories ownership; it does not authorize those retirements.

The maintainer reviewed and confirmed this mapping and gap list on 2026-10-03, closing Phase 1.2.
Phase 1.3 owns concrete catalog/result/selection contracts; Phase 1.4 supplies measurements rather than extrapolating
timings from this static inspection. Existing executable registries and workflows remain unchanged.

### Documentation Verification

The inspection pass checked that all 71 stable methodology families, all 21 registered suite IDs
and paired filenames, all 11 check IDs, all 22 Python package filenames, all 20 PowerShell private
filenames, and all 14 command filenames appear in this ledger. Relative links in this ledger, the
plan and Tools README resolve. Annotation validation passed all 22 fixtures and scanned 385 files
with no findings. These are inventory/documentation checks, not fresh conformance or compatibility
execution evidence. Phase 1.4 will measure those executions separately.
