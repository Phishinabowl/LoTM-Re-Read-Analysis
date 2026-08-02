# Framework Testing Methodology

## Purpose

This document is the authoritative cumulative testing methodology for the reusable knowledge framework and its current project integrations. It defines what must be tested, when each test layer runs, how parity and generated artifacts are compared, and how results enter permanent project history.

The broader version workflow is governed by `Framework/framework_improvement_lifecycle.md`. Enter framework improvement mode there, then return to this document at version design, implementation verification, pressure testing, and testing-methodology review checkpoints.

Testing grows with the framework. A later version inherits every still-applicable earlier test family and pressure scenario. Do not silently omit a retained test, weaken an expectation, or replace a difficult case with an easier one. Revise or retire coverage only through an explicit methodology change that records why the old expectation no longer represents the contract.

The methodology was formalized after V37. Git history owns its revision history; it does not have an independent schema version. Stable test-family IDs provide durable references from evolution entries, commits, future automation, and extracted projects.

## Document Ownership

| Artifact | Owns |
| --- | --- |
| `Framework/framework_improvement_lifecycle.md` | End-to-end version workflow, required checkpoints, two-part implementation confirmation, and closure gates. |
| `Framework/testing_methodology.md` | Pressure-test candidate selection and retention, test lifecycle, required layers, stable test-family IDs, impact rules, comparison standards, and result classification. |
| `Tools/TOOLING_REFERENCE.md` | Exact commands, switches, current output shapes, tool-specific parity recipes, expected runtime-only differences, and dated execution records. |
| `Framework/framework_evolution.md` | Historical results, defects, capability gaps, architectural conclusions, implementing commits, and next-version recommendations. |
| `PROJECT_RULES.md` | The short mandatory policy requiring this methodology and blocking advancement when required tests fail. |
| `Framework/Data/` and paired test tools | Permanent executable fixtures, expected results, malformed cases, scale vectors, and runtime assertions. |

Do not duplicate full command recipes here. Do not turn the evolution log into the testing contract. Do not treat a dated tooling audit as a substitute for retained methodology.

## Core Principles

1. **Cumulative coverage:** every version inherits all applicable retained tests.
2. **No silent retirement:** removing, renaming, narrowing, or materially changing a test requires a reason in this document and a corresponding evolution note.
3. **Defects become regression tests:** a deterministic defect fixed in code must receive a permanent positive or negative vector before the fix is considered complete.
4. **Parity is behavioral:** Python, PowerShell 7, and Windows PowerShell 5.1 must agree on accepted data, rejected data, decisions, structured summaries, and generated semantics where paired runtimes exist.
5. **Pressure tests challenge assumptions:** they are not limited to expected success and must distinguish implementation defects from missing capabilities.
6. **Compatibility consumers matter:** registry conformance alone does not prove that QA, visualization, bounded projection, or future editors still work.
7. **Canonical outputs are protected:** regression tests use redirected ignored destinations unless the maintainer separately confirms a canonical refresh.
8. **Evidence remains explicit:** source-grounded scenarios identify their evidence basis; synthetic cases are labeled synthetic and must not be presented as project facts.

## Pressure-Test Candidate Catalog

This catalog provides durable candidates for conceptual and source-grounded pressure testing across industries. It preserves the broad portfolio used during V1-V37 and gives future maintainers a starting point without requiring chat history.

Named works and real-world domains are **test prompts**, not automatic evidence. Verify source details when a conclusion depends on exact events, release history, legal status, clinical behavior, or technical implementation. Otherwise label the probe conceptual or synthetic.

### Narrative Media Candidates

| Candidate | Particularly Useful For |
| --- | --- |
| *Lord of Mysteries*, *Circle of Inevitability*, and the Donghua adaptation | Multi-book series identity, chapter/volume scoping, novel-versus-adaptation authority, reader disclosure, cultural form versus container, specials/films/seasons, source provenance, fictional Epochs, and the source-grounded Derrick recurrence scenario. |
| *Star Wars* and *Spaceballs* | Franchise groups, films/series/books/comics/games, continuities and canon policy, prequels/sequels/spinoffs, BBY/ABY chronology, adaptation/derivation, and parody without inferring rights or officiality. |
| *Star Trek* | Multiple series and films, reboots and parallel timelines, crossovers, recasts, stardates, alternate continuities, and one conceptual entity across continuity-bound incarnations. |
| Tolkien's legendarium | Named Ages, event-relative chronology, posthumous publications, editions and compilations, adaptations, overlapping textual traditions, and differences among work, manifestation, and evidence source. |
| Marvel/DC and other long-running Western comics | Reboots, retcons, branching universes, crossovers, mantle and legacy succession, clones, composites, alternate counterparts, issue/collection order, and ambiguous entity identity. Marvel's *Loki* additionally retains the TVA, branching timelines, repeated Loom attempts, bootstrap causality, and extratemporal-context pressure scenario. |
| *Dragon Ball*, *Dragon Ball Z*, and *Dragon Ball Z Abridged* | Series/work lineage, adaptation relationships, transformative parody, segment correspondence, production context, and strict separation of derivation from authorization, commerciality, officiality, or legal status. |
| *One Piece* | Very long serialization, manga/anime correspondence, chapters versus episodes, specials/films, recap or compilation material, release order versus story order, and reader-position scaling. |
| *Solo Leveling* | Web-novel/novel, manhwa, anime, translation, localization, cultural-form, manifestation, and cross-medium adaptation distinctions. |
| Gundam | Shared branding across distinct continuities, Universal Century chronology, alternate settings, series/OVA/film forms, compilation releases, and entity or technology counterparts. |
| Time-loop and time-travel portfolio | *Groundhog Day*, *Edge of Tomorrow*, *Re:Zero*, *Steins;Gate*, *Dark*, *Primer*, *Tenet*, *Russian Doll*, *Palm Springs*, and *Outer Wilds* test fixed or changing resets, nested recurrence, staggered awareness, subjective order, branching, partial escape, and retained/lost/restored state. |
| Rotating serialized-media sample | Choose an additional anime, Donghua, manga, manhua, manhwa, webtoon, streaming series, comic, game, or prose serial with an irregular release/adaptation structure so the catalog does not overfit only the named franchises. |

### Cross-Industry Candidates

| Industry | Candidate Scenarios |
| --- | --- |
| IT and operations | Deployment retries and rollback, scheduled jobs, maintenance windows, incident timelines, distributed process observations, environment or branch promotion, configuration restoration, cache hydration, credential acquisition, duplicate actions, retry exhaustion, changing checkpoints, and cleanup/output ownership. |
| Medical and clinical | Recurring episodes or visits, uncertain or reduced-precision dates, diagnosis revision, clinical-state availability, treatment and medication schedules, duplicate administration prevention, delayed/restored evidence, conflicting observations, and provenance-separated belief versus verified state. Use synthetic data unless governed real data is explicitly supplied. |
| Legal and compliance | Effective dates, licenses, territory-scoped rules, recurring filing/reporting obligations, grace periods, competing authorities, corroborating or conflicting evidence, claim supersession, retention duties, audit history, and one action required by multiple independent rules. Do not infer legal conclusions from lineage or metadata. |
| Law enforcement and investigations | DNA, video, audio, photographs, documents, system logs, physical evidence, and first-hand witness accounts with source-specific authority, chain of custody, observation versus claim, contradiction/corroboration, uncertainty, supersession, and scoped applicability. Use synthetic cases unless authorized case data is provided. |
| Science and research | Repeated trials, experimental runs, instrument observations, sample identity, protocol versions, failed/repeated attempts, causal hypotheses, competing measurements, provenance, reproducibility, and partial or incomparable ordering. |

### Candidate Selection Rules

- Start from the version's affected pressure-matrix IDs, then choose candidates because they stress those semantics, not merely because they are familiar.
- For a narrow version, include at least one ordinary case, one irregular case, and one adversarial boundary from every materially affected matrix.
- Run a broad catalog replay when a version changes a foundational abstraction, promotes behavior into core, alters pack boundaries, begins a new architectural era, or prepares extraction into another industry.
- `PRESSURE-CROSS-DOMAIN` must include narrative, IT/operations, medical, and legal/compliance probes. Add law-enforcement/investigative or scientific probes when evidence authority, provenance, recurrence, chronology, or identity is affected.
- Rotate candidates over time. Do not repeatedly use one franchise or one retry scenario as proof of generality.
- Record the selected candidates, whether each was conceptual, synthetic, repository-grounded, or externally source-grounded, and which test-family IDs it exercised.

## Stable Test Families

### Permanent Conformance

`Tools/Conformance/suites.json` is the executable inventory for paired permanent runners. The Python and PowerShell aggregate commands validate that registry, reject discovered but unregistered conformance scripts, and execute named profiles with stable structured summaries. Register every new permanent runner before claiming it is part of the baseline; a standalone script is not permanent coverage until the aggregate inventory owns it.

| ID | Current Purpose | Permanent Surface |
| --- | --- | --- |
| `CONF-PROJECT-COMPOSITION` | Load the canonical manifest, selected packs, activated capabilities, taxonomy, resources, sources, entities, reconciliation, provenance, chronology, and occurrences in dependency order; verify provider closure, expected schema/count summaries, and clean absence of disabled capabilities. | Paired configuration loaders, canonical `Project_Config/`, composed-loader assertions, and the current integrated registry baseline recorded in `Tools/TOOLING_REFERENCE.md`. |
| `CONF-LOOKUP` | Verify pinned Unicode normalization, equivalent/distinct and exact-output lookup vectors, ordinal comparison, malformed registry/input rejection, alias ambiguity, and the boundary between human lookup keys and exact machine IDs. | `Tools/Conformance/Suites/test_lookup_key.py`, `Tools/Conformance/Suites/Test-Lookup-Key.ps1`, `Framework/Data/unicode-lookup-16.0.0.json`, `Framework/Data/lookup-key-regression-vectors.json`, and `Framework/Data/Lookup-Key/`. |
| `CONF-STRICT-INGESTION` | Reject nonportable YAML, malformed mapping keys/scalars, duplicate keys, invalid bytes and timestamps, and parser-budget violations while preserving the portable scalar subset. | `Tools/Conformance/Suites/test_strict_yaml.py`, `Tools/Conformance/Suites/Test-Strict-Yaml.ps1`, shared strict loaders, and `Framework/Data/Strict-Yaml/`. |
| `CONF-TEMPORAL` | Verify precision-aware civil-time parsing, matching, overlap, certainty, bounds, and supported range behavior. | `Tools/Conformance/Suites/test_temporal.py`, `Tools/Conformance/Suites/Test-Temporal.ps1`, and `Framework/Data/Temporal/`. |
| `CONF-CHRONOLOGY` | Verify coordinate systems, exact/partial ordering, spans, mappings, cycles, eras, and cross-context comparison. | `Tools/Conformance/Suites/test_chronology.py`, `Tools/Conformance/Suites/Test-Chronology.ps1`, and `Framework/Data/Chronology/`. |
| `CONF-RECONCILIATION` | Verify stable-ID redirects, merges, splits, retirements, reclassification, ambiguity, limits, deep chains, and strict ingestion. | `Tools/Conformance/Suites/test_reconciliation.py`, `Tools/Conformance/Suites/Test-Reconciliation.ps1`, and `Framework/Data/Reconciliation/`. |
| `CONF-OCCURRENCE` | Verify occurrence identity, recurrence topology, tracks, transitions, causality, outcomes, schedules, rules, state acquisition, carryover, semantic declarations, resolution, and conflicts. | `Tools/Conformance/Suites/test_occurrence.py`, `Tools/Conformance/Suites/Test-Occurrence.ps1`, and `Framework/Data/Occurrence/`. |
| `CONF-PROJECT-ROOT` | Verify marker-based project discovery, precedence, invalid overrides, unrelated launch locations, `.git` rejection, precise failure, and working-directory preservation. | `Tools/Conformance/Suites/test_project_paths.py`, `Tools/Conformance/Suites/Test-Project-Paths.ps1`, and the shared runtime project-path services. |
| `CONF-PACK-COMPOSITION` | Verify capability lifecycle, dependency order and version boundaries, activation, multiple providers, controlled-value ownership and hierarchy, occurrence semantic closure, malformed composition, and scale. | `Tools/Conformance/Suites/test_schema_pack.py`, `Tools/Conformance/Suites/Test-Schema-Pack.ps1`, and `Framework/Data/Schema-Packs/`. |
| `STATIC-POWERSHELL` | Discover and check every tracked or nonignored untracked PowerShell source in the Git worktree with the repository formatter in PowerShell 7 and Windows PowerShell 5.1; require successful parsing, token-preserving normalization, CRLF, UTF-8 without BOM, no optional statement terminators or trailing whitespace, and no line above the configured limit. | `Tools/Static/Format-PowerShell.ps1`, `Tools/Static/powershell-format-settings.psd1`, `.gitattributes`, and all repository `.ps1`, `.psm1`, and `.psd1` sources. |
| `STATIC-PYTHON` | Discover and check every tracked or nonignored untracked Python source with Ruff; require canonical formatting, Python 3.10-compatible parsing, LF, UTF-8 without BOM, and no line above 120 characters. Markdown code fences and Gitignored local/generated files remain outside the default source policy. | `pyproject.toml`, `.gitattributes`, `requirements-python.txt`, and all repository `.py` and `.pyi` sources. |
| `STATIC-WORK-ANNOTATIONS` | Run the permanent valid/invalid annotation fixtures, then scan every tracked or nonignored untracked eligible surface; validate tags, local/GitHub ownership, tracking syntax, issue and assignee URLs, ASCII/punctuation, self-exclusions, and prohibited locations. | `WORK_ANNOTATION_STANDARDS.md`, `Tools/Static/work-annotations.json`, `Tools/Static/Fixtures/Work-Annotations/cases.json`, `.vscode/settings.json`, and `Tools/Static/lint_work_annotations.py`. |
| `STATIC-GITHUB-ACTIONS` | Validate every tracked GitHub Actions workflow with actionlint, immutable third-party action SHAs, explicit least-privilege permissions, bounded timeouts, and stable human-readable check names suitable for repository rules. | `.github/workflows/*.yml`, a local official actionlint executable, and the checksum-pinned actionlint installer in `.github/workflows/ci.yml`. |

### Runtime Parity

| ID | Requirement |
| --- | --- |
| `PARITY-THREE-RUNTIME` | Run every affected paired conformance or compatibility surface in Python, PowerShell 7, and Windows PowerShell 5.1. Compare semantics after only documented non-semantic normalization. |
| `PARITY-STRUCTURED-OUTPUT` | Paired summary commands must expose matching `--json` / `-Json` fields and values. File-producing tools must expose a documented structured artifact contract instead of an ambiguous generic summary. |
| `PARITY-COMMAND-SURFACE` | Paired commands must expose equivalent help, switch/parameter meaning, defaults, validation boundaries, exit behavior, root selection, preferred/fallback delegation, and documented side effects. Help must not accidentally execute the command. |

### Project Compatibility

`Tools/Compatibility/compatibility.json` is the executable check and profile inventory, and `Tools/Compatibility/run_compatibility.py` is the canonical cross-runtime orchestrator. The registry owns representative inputs and profile membership; this methodology owns when those profiles are required and what each stable compatibility family means. Do not duplicate individual runtime commands in CI once the aggregate compatibility profile is adopted there.

| ID | Requirement |
| --- | --- |
| `COMPAT-VISUALIZATION` | Validate existing and freshly generated configured views, exercise unbounded and bounded graph projection, and compare Mermaid plus semantic snapshots. |
| `COMPAT-QA` | Generate redirected Obsidian QA mirrors with representative bounded graphs and pages; compare summaries, file inventories, stable Markdown/Mermaid outputs, reports, and snapshot semantics. |
| `COMPAT-RENDER` | Render at least one redirected representative graph through all supported runtimes and verify successful, nonempty, semantically equivalent output. |
| `COMPAT-ROOT-DISCOVERY` | Verify manifest-based project-root discovery from the repository root, `Tools/`, a nested descendant, and an unrelated working directory. Exercise explicit root, `KNOWLEDGE_PROJECT_ROOT`, current-directory precedence, executable fallback, invalid/missing manifests, and unchanged caller location across affected commands. |
| `COMPAT-ARTIFACT-LIFECYCLE` | Verify redirected output ownership, safe creation beneath fresh multi-level parent paths, rejection of repository-root and outside-repository destinations, stale generated-folder removal, run-scoped temporary cleanup, preservation of unrelated temporary files, and protection of canonical outputs. |

### Retained Pressure Scenarios

| ID | Purpose And Non-Negotiable Questions |
| --- | --- |
| `SCENARIO-DERRICK` | Source-grounded delayed-awareness loop. Can the model distinguish repeated occurrences, what happened in a chosen iteration, what Derrick knew immediately before it, Colin's different knowledge state, reset versus termination, and recurrence exit without a chronology cycle? |
| `SCENARIO-LOKI` | Source-grounded temporal-topology stress case. Can the model separate TVA-local order, timeline branches, repeated Loom attempts, retained learning, bootstrap causality, final termination, and known unsupported aggregate/repeated-participation/extratemporal/branch-lifecycle needs? |
| `PRESSURE-CROSS-DOMAIN` | Replay new primitives against at least narrative, IT/operations, medical, and legal/compliance cases so a narrative convenience is not mistaken for a universal contract. |
| `PRESSURE-ADVERSARIAL` | Attack empty, minimal, contradictory, delimiter-colliding, boundary, ambiguous, unknown, cyclic, oversized, and cross-namespace inputs beyond the permanent happy path. |
| `PRESSURE-SCALE` | Exercise current safety limits and representative deep/wide structures where algorithmic changes could affect termination, memory, recursion, or runtime parity. |

The scenario IDs are stable even when their concrete probes improve. Update the scenario description and permanent fixtures when a version makes a stronger question executable. Preserve older expectations that remain meaningful.

### Retained Historical Pressure Matrices

The following matrices preserve the broad architectural pressure tests that drove V1-V37. They are more specific than `PRESSURE-CROSS-DOMAIN`: that family checks reuse outside the originating domain, while these families check that the model still answers the structural questions that caused earlier versions to exist.

| ID | Retained Questions |
| --- | --- |
| `PRESSURE-LAYER-PORTABILITY` | Does ownership remain correctly split among domain-neutral core, reusable domain packs, project composition, project instances, canonical content, and compiled consumers? Do absent capabilities remain disabled without errors? Can the same framework be composed for narrative, IT/operations, medical, and legal/compliance projects without importing LoTM vocabulary or paths? |
| `PRESSURE-WORK-CONTINUITY` | Can the model distinguish franchises, ordered series, collections, adaptation programs, continuities, branches, sequels, prequels, spinoffs, side stories, crossovers, remakes, retellings, compilations, inspirations, parodies, and other derivative relationships without inferring canon, authorization, officiality, commerciality, or legal status? Can mappings operate below whole-work level? |
| `PRESSURE-MEDIA-DISTRIBUTION` | Are modality, cultural form, creative/release form, manifestation, container, release component, package, run, event, platform, territory, offering, identifier, localized title, segment grouping, numbering, and ordering independent? Do irregular issues, chapters, episodes, cours, split seasons, compilations, editions, translations, dubs, cuts, builds, bundles, and staggered releases remain representable without conflating identity or order? |
| `PRESSURE-EVIDENCE-AUTHORITY` | Can observations, source scope, channel-bounded coverage, exact locators, stable claims, claim namespaces, evidence modes, authority profiles, candidate sets, corroboration, contradiction, incomparability, applicability, territory/time qualification, precedence ties, supersession, and provenance-addressable field paths remain distinct and explainable? Does source priority stay scoped rather than becoming one global truth ranking? |
| `PRESSURE-ENTITY-IDENTITY` | Can conceptual entities, continuity-bound incarnations, persistent identity phases, aliases, ambiguous names, categories, typed relationships, relationship bases, and stable-ID reconciliation remain distinct? Test reboots, alternate counterparts, recasts, regenerations, clones, composites, mantle or legacy succession, splinters, class/instance relations, merges, splits, retirement, reclassification, and exclusions for ordinary roles, disguises, costumes, portrayals, designs, manifestations, and graph nodes. |
| `PRESSURE-TEMPORAL-TOPOLOGY` | Can civil time, reduced precision, open or unknown bounds, fictional eras, negative or far-future coordinates, year-zero policies, descending counters, event-relative dating, multiple axes, mappings, partial/incomparable order, story/publication/release/disclosure order, flashbacks, time travel, and branching timelines remain separate? Chronology cycles must still fail while causal or recurrence cycles use their own services. |
| `PRESSURE-RECURRENCE-STATE` | Can distinct repeated occurrences share coordinates without sharing identity; can fixed/changing reset points, nested loops, staggered awareness, retained/lost/restored state, partial escape, branch transitions, recurrence rules, schedules, outcomes, and deterministic effect resolution be represented without chronology cycles or accidental state transfer? Pressure knowledge acquisition through continuous, sudden, external, partial, conditional, inferred, merged-memory, dream/prophecy, and timeline-reconciliation cases without pretending unsupported epistemic semantics exist. Replay narrative and non-narrative recurrence, not only one loop story. |

### Historical Coverage Index

This index records where the earlier pressure rounds were retained after the methodology was formalized. It is a coverage map, not a replacement for the detailed findings in `Framework/framework_evolution.md`.

| Historical Rounds | Retained Coverage |
| --- | --- |
| Extraction foundation | `CONF-PROJECT-COMPOSITION`, `CONF-PACK-COMPOSITION`, `PRESSURE-LAYER-PORTABILITY`, project compatibility, and command/root/artifact lifecycle checks. |
| V1-V2: series, franchise, continuity, lineage, authority profiles | `PRESSURE-WORK-CONTINUITY`, `PRESSURE-EVIDENCE-AUTHORITY`, and the multi-work/mixed-media candidates. |
| V3-V7: composable media, manifestations, distribution, ordering, groups, and first assertion provenance | `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-MEDIA-DISTRIBUTION`, `PRESSURE-WORK-CONTINUITY`, and `PRESSURE-EVIDENCE-AUTHORITY`. |
| V8-V15: observations, claim-aware authority, structural positions, candidate evaluation, parody, scoped state, and applicability resolution | `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-WORK-CONTINUITY`, `PRESSURE-MEDIA-DISTRIBUTION`, `CONF-TEMPORAL`, and the derivative/parody candidates. |
| V16-V23: entities, relationships, identity hardening, lookup, cross-registry provenance, phases, and reconciliation | `PRESSURE-ENTITY-IDENTITY`, `CONF-LOOKUP`, `CONF-RECONCILIATION`, `CONF-PROJECT-COMPOSITION`, and `PRESSURE-EVIDENCE-AUTHORITY`. |
| V24-V27: strict YAML, canonical syntax, byte preflight, and mapping keys | `CONF-STRICT-INGESTION`, `PARITY-THREE-RUNTIME`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-SCALE`. |
| V28-V30: civil time, query boundaries, chronology axes, mappings, and closure | `CONF-TEMPORAL`, `CONF-CHRONOLOGY`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-CROSS-DOMAIN`, and the temporal-coordinate candidates. |
| V31-V37: occurrences, recurrences, transitions, state acquisition, policy, schedules, extension semantics, and effect resolution | `CONF-OCCURRENCE`, `PRESSURE-RECURRENCE-STATE`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-CROSS-DOMAIN`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-SCALE`. |

When a historical finding appears not to fit one of these retained families, revise this methodology before running or closing the next version. Do not assume that a missing row means the old test is obsolete.

### Retained Project Compatibility Portfolio

These project-level probes preserve the QA, visualization, launcher, and cleanup behaviors that were temporarily omitted during later framework iterations before the compatibility gate was formalized:

- Launch a normal Obsidian QA export from the repository root, `Tools/`, a nested descendant, and an unrelated working directory, proving manifest-based root discovery and equivalent summaries without changing caller location.
- Generate a redirected bounded graph and bounded character pages at an early reader boundary. Retain Dunn Smith's hidden/anonymous/canonical reveal transition and pathway-status progression as the primary current boundary regression; include Leonard Mitchell when later-reveal or optional-module behavior is affected.
- Rerun without bounded requests and verify stale bounded graphs/pages are removed and no empty optional output folder remains.
- Compare Python, PowerShell 7, and Windows PowerShell 5.1 QA file inventories, stable Markdown/Mermaid output, reports, and semantic snapshots after only documented normalization.
- Validate both tracked and freshly generated configured Visualization views; exercise unbounded and bounded projection; verify expected node/relationship counts and zero class/layout issues.
- Render at least one redirected graph in all supported runtimes and verify nonempty semantic equivalence without refreshing canonical outputs.
- Exercise help and structured-summary modes without triggering generation, then compare paired switch meaning, defaults, validation boundaries, and exit behavior.
- Verify automatic and explicit cleanup remove only artifacts owned by the run or requested scope, preserve unrelated `.tmp/` content, remove stale generated subtrees, and leave canonical outputs untouched.

The executable inventory, sample boundaries, and profile composition belong in `Tools/Compatibility/compatibility.json`; exact switches, expected counts, normalization, and the latest measured baseline belong in `Tools/TOOLING_REFERENCE.md`. If representative project data changes, replace a probe deliberately and record why; do not silently stop testing the behavior it represented.

## Testing Within The Version Lifecycle

The numbered steps below are the testing portion of the circular process in `Framework/framework_improvement_lifecycle.md`. They do not replace its orientation, evolution-entry, confirmation, or handoff requirements.

### 1. Classify Impact

Before testing, identify every changed contract, loader, pack, registry, fixture, generated consumer, launcher, and documentation surface. Use the impact matrix below to select additional tests. The required framework-version baseline still runs even when the immediate change appears narrow.

### 2. Add Or Update Permanent Tests

Implementation must add permanent vectors for its promised behavior and for every deterministic defect it repairs. Positive cases prove accepted behavior; malformed cases prove rejection boundaries; decision vectors prove exact outcomes and traces. Update both runtime implementations before claiming parity.

### 3. Run Implementation Conformance

Run the aggregate `baseline` profile in Python, PowerShell 7, and Windows PowerShell 5.1, not only the newly edited suite. Exercise permanent families that do not yet own standalone registered runners through their documented integrated checks. Run the three-runtime parity families for every paired surface. Compare aggregate structured summaries, suite summaries, and exact expected errors where the contract defines them. The `fast` profile is useful during implementation but cannot close this step.

### 4. Run Project Compatibility Gate

Run the compatibility `local` profile during implementation. Run `pull-request` before PR readiness, and run `full-release` before a framework version is implementation-complete. These profiles cumulatively exercise `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, and `COMPAT-RENDER` according to the executable registry. Use focused `--check` selections only for diagnosis; they do not replace the required profile. Exact switches, current representative inputs, normalization, and the latest measured baseline live in `Tools/TOOLING_REFERENCE.md` and `Tools/Compatibility/compatibility.json`.

### 5. Confirm Implementation

Once implementation conformance and compatibility pass, use the lifecycle document's two-part confirmation sequence. Commit the implementation separately from the evolution-document reference update. The version entry records the implementation commit, proposed testing, proposed candidates, permanent counts, compatibility result, and any accepted limitation that existed before pressure testing.

### 6. Run Post-Version Pressure Testing

Run `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, applicable retained scenarios, and `PRESSURE-SCALE` when algorithmic risk warrants it. Pressure testing may use temporary probes, but reproducible defects must be promoted into permanent fixtures when fixed.

### 7. Record And Decide

Replace `Testing After Vn` placeholders with executed coverage, results, defects, capability gaps, deferred concerns, and the next-version recommendation. A shared defect across runtimes is still a defect; parity only proves consistent behavior. Do not begin the next version while an unclassified failure remains.

Review implementation-local annotations under `WORK_ANNOTATION_STANDARDS.md` before closing the test round. A test failure, accepted limitation, or missing permanent vector cannot remain only in Todo Tree. Route it to the evolution record, this methodology, an executable suite, or an explicitly requested GitHub Issue according to ownership; retain a source annotation only when its exact location remains useful.

## Required Framework-Version Baseline

Every framework evolution version must run:

- `STATIC-POWERSHELL` in PowerShell 7 and Windows PowerShell 5.1;
- `STATIC-PYTHON` through both Ruff format-check and line-length-check commands;
- `STATIC-WORK-ANNOTATIONS` through its fixture-backed repository scan;
- the aggregate conformance `baseline` profile in Python, PowerShell 7, and Windows PowerShell 5.1, with matching registered suite inventory and semantic summaries;
- `CONF-PROJECT-COMPOSITION` and `CONF-LOOKUP`;
- `CONF-TEMPORAL`;
- `CONF-CHRONOLOGY`;
- `CONF-RECONCILIATION`;
- `CONF-OCCURRENCE`;
- dedicated `CONF-STRICT-INGESTION` and `CONF-PACK-COMPOSITION` coverage;
- `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, and `PARITY-COMMAND-SURFACE` for affected paired commands;
- `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, and `COMPAT-ARTIFACT-LIFECYCLE`;
- every retained pressure scenario materially affected by the version; and
- `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and every materially affected historical pressure matrix after implementation confirmation.

`PRESSURE-SCALE` is required when the version changes traversal, recursion, graph closure, sorting/grouping, cardinality, parser budgets, resolution limits, or other complexity-sensitive behavior.

## Change-Impact Matrix

| Change | Additional Required Coverage |
| --- | --- |
| Manifest, composition order, project roots, capability activation, or registry discovery | `CONF-PROJECT-COMPOSITION`, `CONF-PACK-COMPOSITION`, `PRESSURE-LAYER-PORTABILITY`, downstream consumers, and full runtime parity. |
| Unicode lookup, aliases, human-facing identifiers, or exact-ID boundaries | `CONF-LOOKUP`, ambiguous/plural and strict/singular lookup, alias-to-ID collisions, pinned Unicode vectors, ordinal comparison, and every consuming registry. |
| Strict ingestion or mapping/scalar parsing | Every registry loader, `CONF-STRICT-INGESTION`, all permanent conformance suites, parser budgets, and full runtime parity. |
| Pack schema, capabilities, dependencies, or controlled values | `CONF-PACK-COMPOSITION`, every consuming registry, malformed composition, project activation, and compatibility consumers. |
| Work, continuity, adaptation, derivative lineage, production, or rights semantics | `PRESSURE-WORK-CONTINUITY`, `PRESSURE-LAYER-PORTABILITY`, affected source/provenance loaders, and representative mixed-media plus parody probes. |
| Media, manifestation, segment, numbering, ordering, release, distribution, territory, platform, or identifier semantics | `PRESSURE-MEDIA-DISTRIBUTION`, `PRESSURE-WORK-CONTINUITY`, structural position validation, source coverage, and irregular-release probes. |
| Evidence source, observation, coverage, locator, authority, applicability, claim, or provenance semantics | `PRESSURE-EVIDENCE-AUTHORITY`, `CONF-PROJECT-COMPOSITION`, affected target providers, precedence/tie/indeterminate cases, and cross-domain evidence probes. |
| Entity, incarnation, identity phase, alias, typed relationship, or reconciliation semantics | `PRESSURE-ENTITY-IDENTITY`, `CONF-LOOKUP`, `CONF-RECONCILIATION`, provenance target resolution, ambiguity/cycle cases, and mixed-continuity probes. |
| Registry schema or loader | Its permanent suite, every downstream composed loader/provider, provenance targeting when applicable, malformed migration cases, and full runtime parity. |
| Temporal or chronology semantics | Both temporal and chronology suites, `PRESSURE-TEMPORAL-TOPOLOGY`, plus every source, occurrence, schedule, applicability, and bounded-projection consumer affected. |
| Occurrence, recurrence, state, or effect semantics | `CONF-OCCURRENCE`, `PRESSURE-RECURRENCE-STATE`, Derrick and Loki scenarios, cross-domain pressure, provenance targets, and project compatibility. |
| QA or bounded-page projection | `COMPAT-QA`, representative hidden/anonymous/canonical boundaries, generated-file cleanup, and Python/PowerShell file parity. |
| Visualization projection, filtering, graph schema, or rendering | `COMPAT-VISUALIZATION`, `COMPAT-RENDER`, QA-delegated visualization outputs, configured no-render refresh, and semantic snapshots. |
| Manifest discovery, path configuration, launcher behavior, or CLI switches | `COMPAT-ROOT-DISCOVERY`, `PARITY-COMMAND-SURFACE`, help output, explicit-root behavior, output safety, and both preferred/fallback launch positions. |
| Generated-output cleanup, temporary paths, or output ownership | `COMPAT-ARTIFACT-LIFECYCLE`, stale-output replacement/removal, run-scoped cleanup, unrelated-file preservation, and canonical-output protection. |
| PowerShell implementation, new PowerShell source location, formatting policy, formatter settings, or line-ending policy | `STATIC-POWERSHELL` in PowerShell 7 and Windows PowerShell 5.1, repository-wide discovery including a temporary nonignored out-of-tree probe when discovery changes, affected runtime conformance, `git diff --check`, and a review of manually wrapped expressions for semantic equivalence. |
| Python implementation, new Python source location, Ruff configuration, dependency, or line-ending policy | `STATIC-PYTHON`, repository-wide discovery including a temporary nonignored out-of-tree probe when discovery changes, affected runtime conformance, `git diff --check`, and a review of manually split semantic strings or expressions. |
| Work-annotation standard, policy registry, linter, fixture, eligible/prohibited path, or Todo Tree configuration | `STATIC-WORK-ANNOTATIONS`, fixture-only conformance, full repository discovery, focused valid/prohibited temporary probes when discovery changes, Todo Tree self-exclusion review, Ruff, and `git diff --check`. |
| GitHub Actions workflow, action pin, job/check name, permissions, trigger, runner, or repository-rule requirement | `STATIC-GITHUB-ACTIONS`, local command equivalence for changed steps, immutable-pin verification against the official action repository, and one observed GitHub-hosted run before treating the policy as green. |
| Documentation or methodology-only change | Link/path review and `git diff --check`. Run affected executable suites when the edit changes a runtime contract, expected result, command, or claim about current behavior. A historical coverage reclassification may cite the latest recorded green baseline without rerunning unchanged code, but it must identify that baseline and must not present an unexecuted test as a pass. |

When uncertain, run the broader set and record why.

## Comparison Standards

### Exact Comparison

Use exact comparison for stable IDs, accepted/rejected case counts, decision statuses, conflict text where contractually pinned, structured summary fields, generated Mermaid semantics, stable Markdown content, and deterministic contributor order.

### Semantic Comparison

Normalize only documented non-semantic differences:

- generated timestamps;
- redirected runtime-specific root paths;
- UTF-8 BOM and newline representation where both readers accept them;
- JSON whitespace and property formatting; and
- renderer-internal byte differences when visual dimensions, content, and nonblank output are the actual contract.

Never normalize labels, IDs, relationship keys, ordering that is contractually deterministic, counts, decisions, visibility boundaries, or omitted/extra files merely to make parity pass.

### Generated Artifact Safety

Write compatibility and pressure outputs beneath a uniquely scoped ignored `.tmp/` directory. Never point a test settings file at canonical `Visualization/` outputs or the normal `Obsidian_Export/` destination. File-producing tools must reject the repository root itself and outside-repository destinations before destructive cleanup, while still creating safe missing parent directories beneath the repository. After comparison, invoke the cleanup helper with the exact scoped temporary path so unrelated temporary work remains untouched.

## Result Classification

| Classification | Meaning | Required Action |
| --- | --- | --- |
| `pass` | Behavior matches the current contract in every required runtime. | Record meaningful counts and scenarios. |
| `implementation-defect` | Implemented behavior violates the intended current-version contract. | Block advancement, repair, and add permanent regression coverage. |
| `parity-defect` | Runtime implementations disagree. | Block advancement and repair the divergent implementation or shared fixture. |
| `compatibility-regression` | A project consumer breaks despite framework conformance. | Block advancement unless an explicit reviewed contract migration updates the consumer. |
| `missing-capability` | The current contract consistently lacks a required representation or service. | Record the boundary and evaluate it for the next version. |
| `accepted-contract-change` | Expected output changed intentionally under a reviewed contract migration. | Update fixtures, consumers, methodology if needed, and evolution history. |
| `deferred` | A real need is acknowledged but deliberately outside the immediate version. | Preserve it in evolution history and retained scenarios; do not fabricate support. |

## Retention And Revision Rules

- Add a new stable test-family ID only for a durable class of coverage, not every individual assertion.
- Never reuse a retired ID for different semantics.
- Retire a family only when its owning capability is removed or fully subsumed; identify the replacement ID and reason here.
- When a scenario becomes executable, preserve its earlier conceptual question and add permanent fixtures for the newly testable behavior.
- When a test expectation changes, state whether the old behavior was a defect or an accepted contract change.
- Review this methodology during every framework version and update it whenever the new version creates a test layer, consumer, risk class, comparison rule, or retained scenario.
- Review this methodology again during post-version pressure testing. A durable testing discovery must enter this document before the evolution round is closed.
- Review the pressure-test candidate catalog during version design and again after pressure testing.
- Add a candidate when it exposes a reusable structural pattern not represented clearly by the current catalog, materially improves industry coverage, or repeatedly proves useful across versions. Prefer expanding an existing candidate row when the new example exercises the same pattern.
- Do not add every title, incident, case, or synthetic fixture. One-off examples remain in the evolution result unless retaining them would help a future maintainer choose a meaningfully different test.
- Every added or revised candidate must state what it is particularly useful for and whether exact use normally requires source verification, synthetic data, governed data, or another evidence constraint.
- Replace or retire a candidate only through an explicit methodology edit and evolution note that preserves the structural behavior the old candidate represented.
- Keep dated execution details in `Tools/TOOLING_REFERENCE.md` and version-specific results in `Framework/framework_evolution.md`; this document remains cumulative policy.

## Evolution Log Record Shape

Each version entry should be able to answer:

- Which stable test families ran?
- What permanent counts changed, and why?
- Did all required runtimes agree?
- Did project compatibility consumers remain green?
- Which source-grounded and cross-domain scenarios were replayed?
- Which historical pressure matrices and representative portfolio probes were replayed?
- Which candidate-catalog entries were selected, how was each evidence basis classified, and did testing add, refine, replace, or deliberately decline to promote a candidate?
- What defects were repaired during implementation?
- What defects, missing capabilities, or deferred concerns did pressure testing expose?
- Which new coverage must be retained by the next version?

A concise reference such as `Passed: CONF-*, PARITY-*, COMPAT-*; pressure: SCENARIO-DERRICK, SCENARIO-LOKI, PRESSURE-ADVERSARIAL, PRESSURE-CROSS-DOMAIN` is sufficient when the surrounding entry records concrete counts and findings.

## Future Automation

Stable test-family IDs are intended to support a later machine-readable test profile and unified runner. Do not create that registry or orchestration layer until the framework extraction boundary and paired-runtime ownership are stable enough to avoid another drifting implementation pair. Until then, this methodology is authoritative and `Tools/TOOLING_REFERENCE.md` remains the command source.
