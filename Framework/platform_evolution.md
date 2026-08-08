# Knowledge Platform Evolution History

This document records how the reusable knowledge platform was implemented phase by phase, why each
platform boundary was introduced, which commits closed it, what compatibility evidence was retained,
and what implementation phase became safe to begin next.

`Framework/platform-implementation-plan.md` owns the ordered roadmap and completion checklist.
`Framework/framework_evolution.md` owns numbered semantic/model versions and their pressure-test
handoffs. `Framework/testing_methodology.md` owns cumulative test requirements, while
`Tools/TOOLING_REFERENCE.md` owns exact commands and the latest dated execution measurements. This
file is the confirmed platform history; it is not another plan, testing contract, or tool manual.

One platform phase may contain zero, one, or several numbered framework versions. Do not duplicate a
version's detailed model rationale here. Instead, record the platform capability that became usable,
the migrations or consumer changes performed, the implementation commits, compatibility closure,
and the accepted next platform boundary.

For a platform phase that closes through a two-part confirmation, open its historical entry with
`Closure implemented by: pending`. The first confirmation commit contains the implementation and
pending history; the second replaces that marker with the exact closure commit hash and subject.

## Platform Phase 1 - Framework Model Stabilization

Platform Phase 1 established the portable semantic kernel and tested it across narrative and
cross-industry pressure scenarios. Its detailed history belongs to the V1-V50 entries in
`Framework/framework_evolution.md`, including the chronology, recurrence, state, interpretation,
hosting, pack-isolation, and chronology-position provider work.

The V50 pressure closure recorded by `2de812a` (`Record V50 pressure-test closure`) accepted the
effective project schema as the next implementation boundary. Phase 1 therefore ended with a
pressure-tested model, strict paired configuration services, permanent conformance and compatibility
registries, aggregate runners, and an extraction rehearsal. It did not yet provide one generated
project schema to commands, QA, Visualization, or future interfaces.

## Platform Phase 2 - Effective Project Schema Service

**Implementation commits:** `18f8241` (`Define effective project schema contract`), `a514852`
(`Implement effective project schema service`), `8d0aae3` (`Add effective schema report export`),
`f5cc73d` (`Plan guarded consumer adoption`), `4e615bf` (`Lock LoTM consumer compatibility
baseline`), `6c99084` (`Adopt effective schema in consumer shadow mode`), `dd8078a` (`Migrate QA
discovery to effective schema`), `0c2de84` (`Migrate visualization discovery to effective schema`),
and `3f51250` (`Complete effective schema consumer adoption`).

**Closure implemented by:** `3f51250` (`Complete effective schema consumer adoption`)

### Phase 2.1 Effective-Schema Contract

Phase 2.1 defined `EffectiveProjectSchema` as a generated, deterministic, domain-neutral view over
one project's manifest, selected packs, capability state, controlled values, taxonomy, and resource
policy. It established that the effective schema is diagnostic output rather than canonical
configuration and that library consumers import the service instead of invoking a CLI subprocess.

The contract included project and registry versions, validated pack dependency order, provider-aware
capability lifecycle and activation, controlled-value ownership and hierarchy, content and resource
configuration, deterministic diagnostics, portable paths, and stable JSON serialization. It did not
claim ownership of page content, relationships, graph projection, or unselected framework packs.

### Phase 2.2 Runtime And Command Surface

Phase 2.2 implemented matching Python and PowerShell composition services, a paired headless command,
human-readable inspection, canonical JSON output, and confined report/file export. Permanent
effective-schema conformance covered available-disabled, planned, deprecated, multiple-provider,
dependency-failure, malformed, deterministic, unrelated-working-directory, path-safety, and
400-capability scale behavior.

The first effective schema exposed ten selected packs, 132 capabilities, 123 enabled capabilities,
nine planned capabilities, 138 controlled-value namespaces, taxonomy/resource projections, and two
deterministic deferred-category diagnostics. It created one reusable inspection boundary for CLI,
QA, Visualization, and future interfaces without migrating either consumer yet.

### Phase 2.3 Initial Consumer Adoption

Consumer adoption was deliberately staged. Phase 2.3.1 first pinned the accepted LoTM
QA/Visualization semantic summaries, complete redirected artifact inventories, hashes, bounded
requests, and canonical-output protections. Phase 2.3.2 then loaded the effective schema in-process
and compared its discovery projections against legacy consumer discovery without allowing the new
path to make output decisions.

After shadow parity held, Phase 2.3.3 made QA obtain enabled roots, content types, categories,
placements, labels, slug rules, and eligibility from the effective schema. Phase 2.3.4 migrated the
corresponding Visualization roots, categories, graph classes, slug rules, and capability state.
Markdown/YAML parsing, relationship extraction, graph construction, reader boundaries, bounded
pages, rendering, presets, destinations, filenames, and cleanup remained consumer-owned and
compatibility-equivalent.

Phase 2.3.5 removed the temporary shadow and legacy projection APIs after both consumers passed their
permanent baselines. The commands and future interfaces, QA, and Visualization could now inspect one
identical effective schema while direct legacy content parsing remained explicitly deferred to the
normalized-content migration.

### Phase 2 Compatibility Closure

All 17 registered `baseline` suites passed with matching suite inventories and canonicalized semantic
summaries in Python, PowerShell 7, and Windows PowerShell 5.1. The complete aggregate executions took
618.5 seconds combined. The focused effective-schema check produced the same 297,916-byte canonical
export, 319-line combined report, 1,621-line deduplicated report, and 126,473-byte report export in all
three runtimes while preserving malformed-root and invalid-selector failure behavior.

The 293.4-second `full-release` profile passed all seven registered checks. Visualization retained 15
nodes, 121 relationships, all five redirected refresh files, and the accepted refresh and unbounded
graph hashes. QA retained 16 notes, 121 relationships, 71 data references, and all 34 normalized
files. All twelve root launches and six unsafe-destination rejections passed. Isolated extraction
copied 236 portable files without project configuration, and all renderers produced the same
nonblank 298,269-byte SVG. Canonical Visualization and QA outputs remained unchanged, successful
temporary output was removed, and static policy plus formatting remained clean.

Phase 2 closed the consumer-adoption gate without claiming complete framework-pack discovery,
presentation-ready pack metadata, normalized page content, generalized relationships, or unified
graph generation. Pack presentation and configuration became the accepted Phase 3 boundary.

## Platform Phase 3.1 - Pack Presentation And Project Inspection

**Implementation commits:** `a8dd468` (`Define schema pack presentation contract`), `a46fbbb`
(`Implement schema pack presentation loaders`), `9fc8bba` (`Backfill schema pack catalog
metadata`), and `8160c6d` (`Add effective schema catalog inspection`).

**Closure implemented by:** `149d37b` (`Close platform pack presentation phase`)

Phase 3.1 made pack and capability configuration presentable without moving canonical ownership into
commands or interfaces. Schema-pack schema 5 adds localizable pack/capability presentation and
explicit family, role, scope, domain, and bridge classification. All 14 installed packs and 136
capability presentations now carry reviewed metadata; legacy schema-4 ingestion remains an explicit
compatibility boundary rather than being mixed into schema-5 composition.

The project-scoped effective-schema contract advances to version 2 and retains every version-1
field while adding selected-pack classification/presentation and effective/provider capability
presentation. Its paired services support exact or normalized ambiguity-safe singular pack and
capability selection. Human commands provide a concise overview, detailed composable sections, and
singular inspection; structured selectors return a filtered
`effective-project-schema-selection` envelope without changing canonical project configuration.

The closure audit identified and preserved a separate next boundary. `EffectiveProjectSchema`
describes one selected project composition and must not claim to represent unselected packs. Phase
3.2.1 therefore owns a distinct generated `FrameworkCatalog` service for deterministic installed-pack
discovery, catalog reporting, and project-state projection before capability grouping begins.

### Phase 3.1 Compatibility Closure

All 17 registered `baseline` suites passed with matching semantic summaries in Python, PowerShell
7, and Windows PowerShell 5.1. Aggregate runtimes were 51.6, 222.2, and 408.0 seconds. The
schema-pack suite validated the 14-pack/136-capability catalog, 91 malformed compositions, legacy
schema-4 compatibility, and a 64-pack rich-metadata scale composition. Effective-schema conformance
validated contract version 2, ten selected pack presentations, 132 capability presentations, three
selection cases, deterministic composition, and unchanged QA/Visualization projections.

The expanded `COMPAT-EFFECTIVE-SCHEMA` check now permanently compares complete JSON and canonical
exports, the 157-line concise overview, detailed and deduplicated reports, normalized combined
selection envelopes and file exports, invalid selectors, unsafe report paths, and malformed-root
failure envelopes in all three runtimes. The complete `full-release` profile passed all seven checks
in 469.2 seconds with canonical outputs unchanged. Visualization retained 15 nodes and 121
relationships. QA retained 16 notes, 121 relationships, 71 data references, one bounded graph, two
bounded pages, and all 34 normalized files. All 12 root launches passed, all six unsafe artifact
destinations were rejected, isolated extraction copied 239 files without LoTM configuration, and all
three renderers produced the same nonblank 298,269-byte SVG hash.

Ruff formatting and lint passed all 45 Python files. The PowerShell formatter passed all 46 files in
PowerShell 7 and Windows PowerShell 5.1 with zero drift and no over-limit lines. Work-annotation
validation passed 338 eligible files, eight annotations, and all 22 fixtures; actionlint and
`git diff --check` were clean. No implementation defect, parity defect, compatibility regression,
canonical artifact change, or extraction-boundary leak remains. Phase 3.1 is complete, and Phase
3.2.1 Framework Catalog And Discovery is the accepted next platform step.

## Platform Phase 3.1.6 - Validation Reporting Optimization

**Implementation commits:** `18b5536` (`Plan validation reporting optimization`), `860e5d6`
(`Define validation reporting contract`), `2b844c5` (`Add aggregate conformance reporting`),
`505c73e` (`Add compatibility reporting modes`), `791fffb` (`Adopt concise validation
reporting`), and `8757468` (`Close validation reporting optimization`).

**Closure implemented by:** `8757468` (`Close validation reporting optimization`)

Phase 3.1.6 is a post-closure tooling optimization before framework-catalog work. It does not reopen
the completed pack-presentation contract or reduce validation coverage. It separates concise routine
status from complete semantic diagnostics so humans, agents, and hosted logs do not need to parse
every nested passing result while detailed clients retain their established contracts.

### Phase 3.1.6.1 Baseline Measurement And Contract

Before runner changes, all measured selections passed and cleaned their successful scoped output.
Human sizes below were rendered from the captured result of the matching JSON execution rather than
rerunning an identical expensive selection solely to measure presentation.

| Run | Elapsed | Detailed JSON | Concise Human | Selected |
| --- | ---: | ---: | ---: | ---: |
| Python focused `effective-schema` | 0.913s | 1,120 bytes / 1 line | 89 bytes / 3 lines | 1 suite |
| Python `fast` | 11.242s | 3,379 bytes / 1 line | 371 bytes / 19 lines | 9 suites |
| Python `baseline` | 50.332s | 6,186 bytes / 1 line | 668 bytes / 35 lines | 17 suites |
| PowerShell 7 `baseline` | 234.746s | 6,186 bytes / 1 line | 668 bytes / 35 lines | 17 suites |
| Windows PowerShell 5.1 `baseline` | 410.422s | 6,186 bytes / 1 line | 668 bytes / 35 lines | 17 suites |
| Compatibility `local` | 271.846s | 3,005 bytes / 101 lines | 109 bytes / 4 lines | 3 checks |
| Compatibility `pull-request` | 426.265s | 5,615 bytes / 206 lines | 194 bytes / 7 lines | 6 checks |
| Compatibility `full-release` | 462.666s | 6,790 bytes / 250 lines | 211 bytes / 8 lines | 7 checks |

The three conformance baselines produced byte-identical detailed payloads. Nested passing-suite rows
accounted for 6,094 of 6,186 bytes. Compatibility's nested check records accounted for 1,996,
3,551, and 4,255 compact bytes as profiles expanded. The measured detailed success payloads were
about nine times the concise human baseline for conformance and 28-32 times the concise human
baseline for compatibility. Output reduction is therefore worthwhile, but it does not reduce the
underlying runtime of PowerShell fixtures, cross-runtime consumer checks, extraction, or rendering.

Tracked machine consumers divide into two groups. GitHub Actions currently requests complete JSON
for all three conformance runtimes and project compatibility even though its routine status role can
use a concise envelope. The isolated extraction rehearsal intentionally parses and compares complete
nested conformance summaries and must remain on detailed output. Documentation commands are human
entry points rather than parsers. No other tracked code consumes an aggregate runner's nested JSON.

`Framework/Contracts/validation-run-reporting.md` defines the accepted additive boundary: preserve
existing detailed JSON, add a versioned concise `validation-run-summary`, support confined detailed
report export, bound console failure excerpts while retaining complete diagnostics, and treat
elapsed values and run-unique retained paths as operational rather than semantic parity fields.

### Phase 3.1.6.2 Aggregate Conformance Reporting

The Python, PowerShell 7, and Windows PowerShell 5.1 aggregate conformance runners now expose
`--summary-json` / `-SummaryJson` for the concise `validation-run-summary` contract and
`--report-output` / `-ReportOutput` for a complete detailed JSON report beneath the project root.
The established `--json` / `-Json` document remains unchanged for semantic consumers. Explicit
reports are retained on success; concise and human failures automatically retain a run-scoped
report beneath `.tmp/conformance/`. Successful concise output omits nested suite summaries, while
failure rows identify every failed suite through a maximum 20-line, 4,096-byte excerpt and link to
the complete diagnostic record.

The permanent `conformance-reporting` compatibility check reuses the canonical conformance runners
and registry rather than creating a second suite inventory. Across all three runtimes it verifies
command surfaces, unchanged detailed output, concise success, explicit report export, normalized
determinism, rejection of report paths outside the project root, bounded synthetic failure excerpts,
and automatic retention of complete diagnostics. The focused check passed 13 cases in 19.244
seconds: three success cases, six repeat/determinism cases, three synthetic failures, and three
unsafe-path failures. Successful detailed reports were byte-identical at 297 bytes with SHA-256
`cc1a59485058e9f2201ea8d28ff2e0c1798e069462122cbe6feec13431c557f9`; concise success payloads
were 465-472 bytes, differing only in operational elapsed values and report paths before
normalization. The check preserved canonical project outputs and cleaned successful scoped output.

### Phase 3.1.6.3 Compatibility Reporting

The canonical Python compatibility orchestrator now implements the shared reporting contract through
`--summary-json` and `--report-output PATH`. Existing `--json` output and the registry-owned check
implementations remain unchanged. Concise results identify selected check IDs, kinds, statuses,
elapsed time, canonical-output protection, scoped-output retention, and a repository-relative report
path without embedding runtime comparisons, generated trees, hashes, or nested semantic summaries.
An explicit report may safely replace one file beneath the project root. Successful automatically
owned output is still cleaned unless `--keep-output` is selected or the report itself lives there.
Both aggregate runners now serialize concise documents in the contract-first field order defined by
`validation-run-reporting.md`; permanent checks enforce that order across all supported runtimes.

Failed checks and cleanup failures retain scoped compatibility output and automatically write the
complete detailed payload to that retained run. Human and concise failure output is limited to the
contract's 20-line, 4,096-byte excerpt and identifies both retained output and detailed report paths.
Malformed report destinations return a structured `orchestration-failure` before output creation or
check execution. Failed check attempts use `check-failure`; canonical-output and cleanup failures use
their own stable classifications.

The permanent `compatibility-reporting` check uses a private synthetic registry to exercise the same
orchestrator without recursively selecting the production compatibility profile. It passed in
29.379 seconds with public command-surface validation, one focused detailed/report case, two profile
and determinism cases, two failure-presentation cases, one unsafe-path case, and three successful
cleanup cases. The representative concise payload was 498 bytes versus 1,938 bytes for the detailed
result. The check is now the first member of `local`, `pull-request`, and `full-release`, making those
profiles contain five, eight, and nine checks respectively while preserving all prior comparisons.

### Phase 3.1.6.4 Adoption And Documentation

Routine local, agent, and hosted validation now uses concise structured summaries while writing the
complete established result to a confined detailed report. GitHub Actions retains the same baseline
suite and compatibility-profile selections, writes explicit reports beneath `.tmp/ci/`, and prints a
complete report only when the owning validation step fails. No suite, fixture, runtime, compatibility
check, canonical-output guard, or rendering boundary was removed or weakened.

The testing methodology, improvement lifecycle, project rules, extraction rehearsal, tooling
reference, command help, and runner READMEs now distinguish execution strength from presentation
verbosity. Direct detailed JSON remains intentional for semantic clients, including effective-schema
parity review and isolated extraction rehearsal. The work-annotation inventory was reviewed; no
reporting-specific deferred implementation remains, and the unrelated normalized-content migration
annotation remains valid.

Actionlint, Ruff formatting and lint, PowerShell formatting in both supported runtimes, all 22 work-
annotation fixtures, repository annotation policy, and `git diff --check` passed. Focused concise plus
report executions passed for `project-root` in Python, PowerShell 7, and Windows PowerShell 5.1; the
three detailed reports were byte-identical at 297 bytes. A focused `root-discovery` compatibility run
also passed with canonical outputs unchanged and a 1,920-byte detailed report. All four explicit
reports were removed without touching unrelated temporary content. Full three-runtime baselines and
`full-release` compatibility remain deliberately assigned to Phase 3.1.6.5 so adoption does not
duplicate the closure gate.

### Phase 3.1.6.5 Closure And Handoff

Closure review caught one semantic defect before confirmation: concise `output_kept` treated any
retained report as retained scoped output, even when compatibility had cleaned its generated tree,
and conformance populated a field that the contract marks non-applicable. The paired conformance
runners now emit `null`; compatibility mirrors the detailed result's actual scoped-output state; and
`report_path` independently records detailed-report availability. Permanent success, failure,
determinism, path-safety, cleanup, and three-runtime checks now enforce that distinction.

On the corrected exact-final tree, Ruff passed 45 Python files; the PowerShell formatter passed 46
files in PowerShell 7 and Windows PowerShell 5.1; work-annotation policy passed 340 eligible files,
eight annotations, and all 22 fixtures; and actionlint plus `git diff --check` passed. The focused
reporting checks passed, including retained deliberate-failure diagnostics without reruns. Direct
three-runtime report smoke tests produced `output_kept: null` with valid explicit report paths for
conformance and `output_kept: false` with a valid report path after successful compatibility cleanup.

All 17 `baseline` suites then passed in Python, PowerShell 7, and Windows PowerShell 5.1 in 58.3,
250.4, and 435.0 seconds. Their 6,186-byte detailed reports preserved identical suite order and one
canonicalized semantic hash. The final 9-check `full-release` profile passed in 502.6 seconds with
canonical outputs unchanged and scoped output removed. Its approximately 1,125-byte concise envelope
was materially smaller than the 8,203-byte detailed report.

Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71
data references, and all 34 normalized files. All 12 root launches passed; six unsafe destinations
were rejected while unrelated temporary content was preserved; isolated extraction copied 241
reusable files without project configuration and passed six portable suites in all three runtimes;
and every renderer produced the same nonblank 298,269-byte SVG with SHA-256
`11b9e70f735004641ab0bd348c21451d1cc2852327caa58d092dd045dfb59f73`.

Phase 3.1.6 is closed by `8757468` (`Close validation reporting optimization`). The fresh-task
handoff is finalized after the traceability commit and push so it can name the exact remote head and
verified clean status without creating a self-referential tracked document.

## Platform Phase 3.2.1 - Framework Catalog And Discovery

**Implementation commits:** `e44bf32` (`Define framework catalog contract`), `1dc52e8` (`Define
framework installation bootstrap`), and `db446da` (`Implement framework catalog discovery`).

**Closure implemented by:** `db446da` (`Implement framework catalog discovery`)

Phase 3.2.1 adds the project-independent `FrameworkCatalog` without changing the authority or
output of the project-scoped `EffectiveProjectSchema`. `Framework/framework.yaml` explicitly
selects the installed pack root and one pinned Unicode lookup registry. Paired root discovery checks
an explicit root, `KNOWLEDGE_FRAMEWORK_ROOT`, current-directory ancestry, and executable ancestry
without changing the process working directory or inferring a lookup dataset by filename.

The Python and PowerShell catalog services reuse the existing strict schema-pack parser and
validated pack/capability records. They deterministically discover immediate child directories
containing `pack.yaml`, reject malformed packs, ID mismatches, missing or incompatible
dependencies, dependency cycles, and conflicting presentation, and compile complete pack and
capability rows. Canonical pack files remain authoritative; generated catalogs and selection
envelopes are inspection output only.

Paired `inspect_framework_catalog.py` and `Get-FrameworkCatalog.ps1` commands provide a concise
summary, composable overview/pack/capability reports, exact-then-normalized combined selectors,
canonical JSON, confined JSON/report exports, structured path-safe failures, and independent
framework-root discovery. The PowerShell module now owns a shared deterministic JSON serializer
used by both catalog and effective-schema commands; catalog and effective-schema contract IDs,
records, and public commands remain distinct.

### Phase 3.2.1 Verification

Permanent `framework-installation` conformance covers 11 root vectors, strict manifest loading,
explicit selection among multiple lookup datasets, nine malformed configurations, and exact
three-runtime summaries. Permanent baseline-only `framework-catalog` conformance covers the
canonical 14 packs and 136 capabilities, deterministic repeated loading, ignored directories,
deferred/planned/deprecated discoverability, multiple providers, normalized and ambiguous
selection, eight classified malformed catalog compositions, and a generated 64-pack scale case. It
passed on the final focused run in 3.2 seconds in Python, 39.7 seconds in PowerShell 7, and 69.4
seconds in Windows PowerShell 5.1 with
byte-identical semantic summaries.

The registered `framework-catalog` compatibility check passed base and combined-selection JSON,
concise/combined/deduplicated reports, confined file exports, invalid roots and sections, unknown
selectors, outside-root rejection, and absolute-path-safe structured failures across all three
runtimes in 206.0 seconds. Base catalog JSON, selection JSON, and full reports were byte-identical.
The pre-existing `effective-schema` compatibility check passed in 167.6 seconds after shared
serializer extraction, proving its contract-version-2 JSON, selections, reports, failures, and
exports remained unchanged. Aggregate baseline, consumer, extraction, and release closure results
are recorded below.

All 19 registered `baseline` suites passed in Python, PowerShell 7, and Windows PowerShell 5.1 in
56.7, 277.9, and 474.6 seconds. Their detailed 6,796-byte reports were byte-identical and preserved
the same suite order and semantic summaries. Ruff passed the complete Tools tree; the PowerShell
formatter passed all 51 files with zero changed or over-limit lines; work-annotation validation
passed 364 eligible files, eight annotations, and all 22 fixtures; command help, registry loading,
and `git diff --check` were clean.

The final exact-tree 10-check `full-release` compatibility profile passed in 816.2 seconds with canonical
outputs unchanged and scoped output removed. The catalog retained 14 packs and 136 capabilities
with byte-identical 367,416-byte canonical JSON, 44,493-byte combined selection JSON, and
152,060-byte detailed reports. EffectiveProjectSchema retained contract version 2, ten selected
packs, 132 capabilities, 138 controlled-value namespaces, and its prior canonical hashes.
Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71
data references, one bounded graph, and two bounded pages. All 12 root launches passed; six unsafe
destinations were rejected; isolated extraction copied 266 reusable files without project
configuration and passed eight portable suites in all three runtimes; and representative rendering
remained byte-identical and nonblank.

Phase 3.2.1 is closed by `db446da` (`Implement framework catalog discovery`). Phase 3.2.2 remains
the next boundary: reconcile project/framework lookup pins, derive EffectiveProjectSchema pack
records through the catalog under exact shadow comparison, and add the explicit
`FrameworkCatalogProjectView`.

## Platform Phase 3.2.2 - Effective-Schema Catalog Integration

**Implementation commits:** `8eca229` (`Integrate effective schema with framework catalog`).

**Closure implemented by:** `8eca229` (`Integrate effective schema with framework catalog`)

Phase 3.2.2 makes the project-independent catalog the one runtime authority for installed pack
parsing while preserving `EffectiveProjectSchema` as a distinct project-scoped composition. The
project manifest's framework ID and pinned lookup registry must exactly match the installation
manifest, and each selected pack ID and configured path must resolve to the corresponding validated
catalog record. Mismatch fails closed; the service does not silently inherit, substitute, rescan,
or reparse project pack metadata.

The effective schema still owns project selection order, dependency closure, capability activation,
controlled-value composition, taxonomy, resources, and diagnostics. Its contract-version-2 JSON,
selection envelope, report surface, command names, output confinement, and QA/Visualization
projections remain unchanged. The prior direct composition remains only as a conformance shadow
oracle; supported effective-schema loading now uses catalog-retained pack objects.

An explicit `FrameworkCatalogProjectView` combines an unchanged base catalog with one completed
effective schema. It copies every installed pack and capability row under distinct project-view
record identities, preserves the source catalog record ID, and annotates selected, available,
enabled, deprecated, planned, used-by-project, and unavailable-reason state. Catalog commands attach
project context only through `--project-root` / `-ProjectRoot`; ordinary catalog inspection remains
project-independent. Project-view selectors, deterministic JSON, reports, exports, failures, and
path safety are paired across Python and PowerShell module version 0.8.0.

### Phase 3.2.2 Verification

Exact shadow comparison proved the direct and catalog-backed schema-pack registries and effective
schemas equal before the catalog path became authoritative. The canonical project view contains 14
installed packs, ten selected packs, 136 installed capabilities, 132 selected capabilities, and 123
enabled capabilities. Python and PowerShell 7 produced byte-identical 417,162-byte complete
project-view JSON with SHA-256
`63ae30eea4ccfb3c6dbe68958294166cc1458fc64a694c673194be8085386fb4`, plus byte-identical
45,156-byte selection JSON and 20,446-byte human reports. Permanent project-view conformance covers
selected and unselected records, enabled and planned state, unavailable reasons, deterministic
composition, selectors, malformed attachment, and base-catalog immutability.

All 19 registered `baseline` suites passed on the final formatted tree in Python, PowerShell 7, and
Windows PowerShell 5.1 in 55.9, 276.2, and 499.6 seconds with matching semantic summaries. Focused framework-catalog and
effective-schema compatibility passed across all three runtimes in 333.0 and 245.0 seconds;
Visualization plus QA compatibility passed in 99.3 seconds with canonical project artifacts
unchanged.

The extraction gate exposed two integration defects before closure. Its neutral consumer still used
an obsolete placeholder taxonomy document, and project-view conformance assumed LoTM-specific pack
IDs and counts. The rehearsal now creates valid empty taxonomy/resource registries, derives portable
assertions from the neutral effective schema while retaining the stricter LoTM snapshot, and passes
eight suites in all three runtimes. The direct rehearsal copied 266 files and completed in 247.8
seconds. The registered timeout increased from 240 to 360 seconds after the aggregate runner correctly
reported the stale limit; root discovery, artifact lifecycle, and extraction then passed together in
290.1 seconds.

The final ten-check `full-release` profile passed in 1,050.1 seconds. Compatibility reporting,
conformance reporting, framework catalog, effective schema, Visualization, QA, root discovery,
artifact lifecycle, isolated extraction, and rendering all passed; canonical outputs remained
unchanged and successful scoped output was removed. Phase 3.2.3, effective-schema QA publication,
is the next platform boundary.

Phase 3.2.2 is closed by `8eca229` (`Integrate effective schema with framework catalog`).

## Platform Phase 3.2.3 - Effective-Schema QA Publication

**Implementation commits:** `pending`.

**Closure implemented by:** `pending`

Phase 3.2.3 adds `effective-project-schema-report-model` version 1 as the shared semantic input for
human-facing project-schema reports. It preserves the source contract sections and adds only derived
summary counts. Python and PowerShell module version 0.9.0 provide paired report-model composers and
deterministic Markdown renderers; the existing inspection commands now consume the same model while
their canonical JSON and human-report behavior remains compatible.

Both Obsidian QA exporters render `_Generated/effective-schema.md` directly from the
`EffectiveProjectSchema` already composed for discovery and graph requests. Neither exporter invokes
an inspection command or another runtime. The report contains generated/noncanonical metadata,
project and contract identity, concise counts, ten selected packs, 132 capabilities, and two
diagnostics. It excludes the multi-thousand-line detailed report, absolute paths, timestamps, and
runtime state. Clean generation owns the file on every run, and the project baseline now protects a
complete 35-file QA inventory plus its aggregate tree hash.

### Phase 3.2.3 Verification

Focused effective-schema conformance passed with three permanent report-model cases in Python,
PowerShell 7, and Windows PowerShell 5.1. Repeated Markdown rendering was deterministic, required
metadata and sections were present, and machine-specific paths and timestamp fields were absent.
Redirected QA exports produced identical normalized 26,347-character reports in all three runtimes;
the reviewed file hash is `a05f55e3a05f4f25f90fbfa2998766e1c00acc1ba08c08d320b5ca17cf6eb220`.

Focused effective-schema plus QA compatibility passed in 301.2 seconds with canonical outputs
unchanged. All 19 registered `baseline` suites then passed in Python, PowerShell 7, and Windows
PowerShell 5.1 in 59.3, 284.0, and 514.6 seconds. Ruff and the PowerShell formatter passed the final
tree. The ten-check `full-release` profile passed in 1,017.8 seconds across compatibility reporting,
conformance reporting, framework catalog, effective schema, Visualization, QA, root discovery,
artifact lifecycle, isolated extraction, and rendering. Canonical outputs remained unchanged and
successful scoped output was removed.

Phase 3.2.3 is implemented by `pending`. Capability grouping is the next platform boundary.
