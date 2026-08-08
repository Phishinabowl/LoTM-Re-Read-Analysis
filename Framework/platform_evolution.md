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

**Implementation commits:** pending

**Closure implemented by:** pending

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
