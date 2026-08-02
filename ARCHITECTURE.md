# Knowledge Model Architecture Contract

## Status

This document is the authoritative architecture and component-ownership contract for the repository and for the reusable knowledge-model framework being extracted from it.

It describes both the required target architecture and the boundaries that new work must follow during migration. When current code does not yet match this contract, treat the mismatch as transition debt to remove, not as precedent for additional duplication.

LoTM-specific authoring, evidence, taxonomy, and spoiler-modeling rules remain in [PROJECT_RULES.md](PROJECT_RULES.md). Framework iterations enter through [Framework/framework_improvement_lifecycle.md](Framework/framework_improvement_lifecycle.md); cumulative testing and retained coverage live in [Framework/testing_methodology.md](Framework/testing_methodology.md); and [Framework/framework_evolution.md](Framework/framework_evolution.md) remains the historical implementation, pressure-test, and next-version handoff log. Tool switches and current implementation details remain in [Tools/TOOLING_REFERENCE.md](Tools/TOOLING_REFERENCE.md).

## Architectural Goals

The system must:

- support multiple knowledge domains without hardcoding LoTM folder names, page types, sources, or relationship vocabularies into framework code;
- preserve human-readable canonical articles alongside structured, machine-readable state;
- generate reader-safe projections without making generated outputs canonical;
- expose the same model, validation, visualization, and mutation behavior to command-line tools, QA workflows, future websites, and editor interfaces;
- support controlled repository-wide migrations such as category, folder, slug, or schema changes;
- preserve Python-preferred tooling with behaviorally compatible PowerShell fallbacks where repository policy requires them.

Paired executable commands that emit a human-readable validation or conformance summary must also expose `--json` and `-Json` forms with the same semantic fields. Library-only loaders do not need command switches. File-producing tools may use durable structured output files instead, but that contract must be explicit rather than an accidental omission.

## Core Principles

### Configuration Owns Domain Meaning

Framework code performs generic operations. Project configuration defines domain categories, controlled vocabularies, sources, paths, and presentation mappings.

Adding an IT category such as `server`, or renaming a LoTM category label, must not require editing graph algorithms, QA algorithms, or UI code.

### Stable Identity Is Separate From Presentation

Stable category and page identifiers are permanent machine identities. Display labels, plural labels, folders, filenames, slugs, colors, and icons are mutable presentation or storage properties.

A label or folder rename must not silently create a new category. A page-title or slug rename must not silently create a new subject.

Existing pages do not yet persist all planned stable IDs. Until that migration occurs, current slugs remain provisional identity keys and must be changed only through reviewed repository migrations.

### Generated Views Are Compiled Outputs

Generated Mermaid, rendered images, Obsidian mirrors, QA reports, bounded pages, indexes, and future website projections are compiled views. They are never independent sources of truth.

Fix durable errors in canonical configuration, content, structured data, evidence records, or relationships, then regenerate the affected views.

### Shared Services Precede Interfaces

Command-line tools, Streamlit, and future websites are clients of shared framework services. They may collect input, display previews, and choose output destinations, but they must not implement competing taxonomy, validation, graph, or migration rules.

### Tool Runtime And Command Architecture

Reusable model behavior and executable command behavior must be physically separate. The target `Tools/` layout is:

```text
Tools/
  Runtime/
    Python/
      knowledge_framework/
    PowerShell/
      KnowledgeFramework/
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

`Visualization/` remains a separate subsystem because it owns graph semantics, projections, rendering, and graph-specific configuration rather than general command support. Framework fixtures remain under `Framework/Data/`; project configuration remains under `Project_Config/`.

The Python runtime is a real `knowledge_framework` package. Its module names remain descriptive and domain-neutral, including `project_paths`, `strict_yaml`, `project_config`, `lookup_key_config`, `schema_pack_config`, `taxonomy_config`, `resource_config`, `temporal_config`, `source_config`, `chronology_config`, `entity_config`, `reconciliation_config`, `occurrence_config`, and `provenance_config`. Commands bootstrap the repository package root and import these modules by package-qualified name; they do not add a flat script directory to `sys.path` or import sibling command files.

The package and PowerShell module preserve this dependency direction:

```text
project_paths
strict_yaml
project_config -> project_paths, strict_yaml
lookup_key_config -> project_config
schema_pack_config -> project_config, strict_yaml
taxonomy_config -> project_config, strict_yaml
resource_config -> project_config, strict_yaml
temporal_config -> schema_pack_config, strict_yaml
source_config -> lookup_key_config, project_config, resource_config,
                 schema_pack_config, strict_yaml, temporal_config
chronology_config -> project_config, schema_pack_config, strict_yaml
entity_config -> lookup_key_config, project_config, schema_pack_config,
                 source_config, taxonomy_config, strict_yaml
reconciliation_config -> project_config, schema_pack_config, strict_yaml
occurrence_config -> chronology_config, project_config, schema_pack_config,
                     strict_yaml, temporal_config
provenance_config -> chronology_config, entity_config, occurrence_config,
                     project_config, reconciliation_config, schema_pack_config,
                     source_config, strict_yaml, temporal_config
```

Provider objects may flow into higher services without adding reverse imports. A lower layer must not import a higher layer merely to construct project composition; the future project-composition service owns that orchestration.

The PowerShell runtime is one manifest-backed `KnowledgeFramework` module with `KnowledgeFramework.psd1`, `KnowledgeFramework.psm1`, and internal implementation scripts. The manifest explicitly exports supported functions; commands and conformance runners import the module and do not dot-source a chain of peer scripts. Both PowerShell 7 and Windows PowerShell 5.1 remain supported until a separately reviewed compatibility decision changes that contract.

`project_paths` owns dependency-light project discovery and safe repository-relative path primitives. `project_config` owns manifest parsing and validation on top of those primitives. Project discovery uses `Project_Config/project.yaml`, never `.git`, and resolves in this order: an explicit root, the `KNOWLEDGE_PROJECT_ROOT` environment override, current-directory ancestors, executable-location ancestors, then a precise failure. Discovery must not change the caller's working directory.

The following surfaces require independent Python and PowerShell behavior parity:

- reusable configuration, identity, temporal, chronology, occurrence, and provenance runtime services;
- durable user commands for QA export, cleanup, EPUB/media search, and image operations;
- permanent conformance suites and their aggregate runners; and
- Visualization commands and generated semantic outputs.

Parity means equivalent semantics, validation boundaries, root selection, help, structured summaries, exit behavior, and documented side effects. It does not require identical source layout or implementation technique. Python commands call Python runtime services, and PowerShell commands call PowerShell runtime services; neither implementation silently delegates its domain behavior to the other.

Environment probes, parser-native formatters, Ruff, the future work-annotation linter, and the future cross-runtime compatibility comparator are intentionally single-runtime or canonical orchestration tools. They validate runtimes rather than offering a domain-feature fallback. A cross-runtime comparator may launch all supported runtimes because comparison is its explicit responsibility. Any new exception to parity must be documented here and in `Tools/TOOLING_REFERENCE.md`.

The post-migration command paths are the stable public CLI entry points. This pre-release repository will perform one atomic path migration: tracked callers, CI, documentation, module imports, and conformance registry paths move together. Old root-level script paths do not receive permanent wrappers, because that would recreate the flat directory and duplicate command inventory. A temporary wrapper is permitted only for a specifically identified external dependency, must warn about deprecation, and must have a recorded removal checkpoint.

The migration order is fixed:

1. implement and validate shared project discovery;
2. create the Python package and PowerShell module without changing command behavior;
3. move individual conformance runners and update only their centralized `suites.json` runner paths;
4. move user commands, environment probes, and static tools while updating tracked callers and documentation;
5. run static, three-runtime aggregate, root-discovery, Visualization, QA, render, and artifact-lifecycle validation;
6. remove obsolete root-level implementations or approved temporary wrappers; and
7. add missing registry suites only after final runtime and conformance paths are stable.

## Source-of-Truth Layers

The repository uses these authority layers:

1. **Project configuration** identifies the project and defines domain and tool contracts.
2. **Canonical content** owns human-readable articles, structured state, relationships, and reader-position modeling.
3. **Evidence and investigation records** support, qualify, and trace canonical claims.
4. **Generated views** compile the preceding layers for QA, navigation, visualization, publishing, or bounded-reader presentation.

Within canonical pages, the visible article and structured page data are two synchronized representations of the same modeled subject. Neither may drift silently from the other. A future separation into linked Markdown and structured-data files may change their storage layout without changing this authority model.

## Configuration Contracts

### Project Manifest

`Project_Config/project.yaml` is the bootstrap manifest. It identifies the project, assigns stable IDs to modeled content and resource roots, locates supporting registries, and declares tool-integration paths without absorbing domain definitions.

`Tools/project_config.py` and `Tools/Project-Config.ps1` are the matching manifest-loader implementations. They locate and validate project configuration and registry paths, including the pinned lookup-key data registry; they do not own domain taxonomy.

### Lookup-Key Registry

`Framework/Data/unicode-lookup-16.0.0.json` is portable framework data selected by the project manifest. `Tools/lookup_key_config.py` and `Tools/Lookup-Key-Config.ps1` implement the same pinned trim, NFC, full default case-fold, and NFC algorithm without inheriting the host runtime's Unicode version or locale rules. Human-facing aliases and explicitly case-insensitive semantic values use the resulting key with ordinal comparison. Stable IDs, schema keys, filesystem paths, and standards-specific language tags retain their own validators. See `Framework/Contracts/lookup-key-normalization.md`.

### Schema Packs

`Framework/` contains portable framework assets. `Framework/Contracts/` owns versioned configuration-shape contracts as they stabilize, while `Framework/Packs/` owns bundled reusable capability and vocabulary packs. `Project_Config/` remains the project-instance composition layer.

`Project_Config/schema-packs.yaml` selects reusable schema packs in dependency order and activates project capabilities. Each selected pack is a portable contract stored separately from project-instance data:

- `Framework/Packs/core/pack.yaml` declares domain-neutral platform capabilities and evidence-source vocabulary;
- `Framework/Packs/narrative-media/pack.yaml` depends on `core` and contributes the narrative foundation;
- publishing, screen/audio, adaptation, distribution, shared-universe, interactive, preservation, and production/rights companion packs add orthogonal domain capabilities without forcing them into every narrative project;
- future implementations may replace `narrative-media` with packs such as `it-operations`, `legal-matter`, or `medical-knowledge`, or compose compatible packs.

A capability has separate declaration, lifecycle, availability, and project-activation states. String capability entries are shorthand for lifecycle `available`; mapped entries may be `planned`, `available`, or `deprecated`. Planned capabilities remain discoverable to roadmap tooling but cannot be enabled. Available capabilities may be enabled by `capability_activation.enabled`; deprecated capabilities remain activatable for compatibility or migration but should not be recommended for new projects. The activation default must remain `disabled`. An unavailable or unenabled capability is omitted by tools, validators, projections, and interfaces unless project configuration explicitly references its contract, in which case validation must report the invalid reference. Missing or incompatible declared pack dependencies are always errors.

A schema pack may contribute capabilities and controlled values. Narrative media uses orthogonal axes: medium profiles own reader-position behavior; modalities describe prose, sequential art, animation, live action, audio, still image, or interaction; cultural forms preserve anime, Donghua, manga, manhwa, manhua, and webtoon identity; release forms describe creative packaging; and container formats describe concrete evidence artifacts. Narrative sources may contain embedded visual assets regardless of whether the container is an EPUB, comic release, scan, or another supported format. Official EPUB artwork is therefore an illustration carried by an EPUB source, not a compound medium. The source record owns evidence provenance, the extracted image is a visual resource, and promotion into a tracked page-ready asset remains a separate project action. Reusable packs do not instantiate LoTM works, categories, pages, paths, source records, or project-specific vocabulary. A project-owned extension pack may contribute local terminology while project registries instantiate actual records. Interface wizards should generate or edit those layers from pack contracts rather than embedding industry or organization assumptions in UI code.

`Tools/schema_pack_config.py` and `Tools/Schema-Pack-Config.ps1` are the matching schema-pack loaders. They validate pack identity, version, kind, lifecycle, repository-safe paths, dependency selection and order, capability availability and activation, controlled-value namespaces, and unambiguous ownership. Source-registry loaders consume the aggregate pack contract and reject medium, work, continuity, relationship, or source-role vocabulary not supplied by a selected pack.

The initial pack boundary is deliberately narrow. It proves executable ownership for source-model vocabulary before taxonomy fields, page modules, graph projections, and editor forms are migrated into the same pack mechanism.

### Taxonomy Registry

`Project_Config/taxonomy.yaml` is the machine-readable taxonomy registry. Its current category and content-type records own:

- stable category IDs;
- stable content-type IDs and their distinction from subject categories;
- lifecycle and canonical-page enablement;
- content-type roots, category policy, path strategy, metadata behavior, record-slug rules, default templates, QA-page eligibility, and graph eligibility;
- category labels, metadata types, subject-slug rules, graph classes, and per-content-type folder/template placements;

The following sections remain planned extensions of this registry:

- controlled relationship types and reciprocal behavior;
- strict field-scoped enums and their aliases;
- confidence or precedence orderings that affect generic projection behavior;
- explicitly extensible domain vocabularies.

`Tools/taxonomy_config.py` and `Tools/Taxonomy-Config.ps1` are the matching registry loaders. They validate registry structure, stable IDs, content-root and content-type references, category/content-type compatibility, safe relative folders, slug expressions, templates, and uniqueness constraints. Domain clients should consume their normalized records instead of adding new category allowlists.

The registry must distinguish strict enums, extensible vocabularies, aliases, and free descriptive fields. There must not be one global `status`, `type`, or `confidence` allowlist when those names serve different model contexts.

Content type and subject category are orthogonal:

- a Dunn Smith article is `content_type_id: glossary-page` plus `category_id: character`;
- a Dunn Smith source review is `content_type_id: investigation-record` plus `category_id: character`;
- a Volume Summary is `content_type_id: volume-summary` with categories forbidden.

A content type defines the record contract, root, path strategy, optional default template, QA-page behavior, and graph eligibility. A category defines the subject family, subject slug, display/metadata identity, graph class, and its placement under eligible content types. Aggregating records such as Volume Summaries, analyst boards, the project dashboard, and the navigation index therefore do not appear in the category editor or become subject graph nodes merely because they are canonical records.

### Resource Registry

`Project_Config/resources.yaml` is the machine-readable registry for repository resources that support, configure, generate, or provide evidence for content without being authored content records themselves. It owns:

- stable resource-kind and resource-type IDs;
- resource lifecycle, authority role, and editor eligibility;
- placement beneath manifest-configured resource roots;
- tracked, ignored, or mixed storage behavior;
- whether a placement must exist in a valid checkout.

Examples include framework contracts and packs, visual assets, local source material, executable tools, project configuration, generated visualizations, QA exports, design records, application state, and temporary artifacts. These are intentionally not taxonomy content types. The distinction lets an IT implementation map the same contracts to diagrams, vendor documentation, logs, automation, configuration, generated topology views, and local working state.

`Tools/resource_config.py` and `Tools/Resource-Config.ps1` are the matching registry loaders. They validate stable IDs, resource-root and kind references, controlled lifecycle/authority/tracking values, safe relative placements, required paths, and placement uniqueness.

### Source Registry

`Project_Config/sources.yaml` schema version 18 owns:

- stable source and medium-profile IDs plus instantiated modality, cultural-form, release-form, and container-format facets;
- stable franchise/collection/adaptation-program groups, creative works, structural work segments, recursively nested content groups with stable member identities and controlled participation roles, continuities, and per-work volume identities;
- named numbering schemes plus independent total or partial publication, release, story, production, or recommended ordering schemes;
- segment-aware, multi-input adaptation mappings with explicit source-basis roles that preserve source and derivative claims;
- manifestations for whole works or selected segments, including editions, translations, cuts, recuts, remasters, builds, and explicit segment-level version mappings;
- manifestation- or package-scoped components, typed component lineage, commercial packages, phased release runs, and concrete events for tracks, bundled material, staggered segments, and launches;
- hierarchical territories plus platforms, localized direct-target provider catalog placements, stable and temporally scoped localized-title variants, segment-scoped offerings, BCP-47-style languages, and structured availability windows;
- external identifier schemes and values for works, segments, releases, platforms, catalog records, and evidence sources;
- medium-specific position fields, explicit canonical-work scope fields, optional pack-owned volume-catalog or segment-ordering structural validators, sort order, and citation formats;
- authority profiles, comparison groups, general source priority, hierarchical claim namespaces and evidence modes, precedence-resolved claim-specific authority rules, explainable authority decisions, and multi-source comparisons;
- typed work relationships such as sequel, spinoff, side story, adaptation, remake, retelling, parody, crossover, containment, compilation, and inspiration;
- reusable provenance-addressable applicability scopes plus explainable decisions that discover structurally containing targets, inherited territories, effective time, explicit precedence, tied winners, and indeterminate timing;
- scope-backed work relationships, continuity assertions, and work-production contexts that keep narrow applicability, canon state, production origin, authorization, rights basis, and commerciality independent from creative lineage;
- typed source relationships such as edition, translation, transcript, subtitle track, dub, scan, extract, and package membership;
- composite evidence-source work scope, permitted locator media, repeatable typed release observations, stable medium- and evidence-mode-scoped coverage entries with semantically work-scoped position ranges, source aliases, controlled evidence modes, and bindings to registered resources;
- conflict, deviation, and unresolved-difference policy.

Reader positions are work-scoped before they are volume- or chapter-scoped. This prevents chapter 100 in one book from colliding with chapter 100 in a sequel and permits filtering or sorting by franchise, collection, continuity, work, volume, and local chapter. Work aliases may provide familiar labels while canonical work IDs remain stable.

Current graph and bounded-page implementations predate the work registry and remain implicitly scoped to `lotm-1`. Their migration to the normalized content index must add an explicit work selector before those interfaces are used for COI or cross-book output; do not infer a work from a chapter number.

Creative-work identity, manifestation identity, distribution, and evidence lineage are separate. `lotm-donghua-season-1` is an adaptation work in its own continuity; its streaming manifestation is a particular version of that work; a release event or platform offering records where that manifestation appeared; `lotm-donghua-release` is the evidence source observing it; and the English subtitles are both a release component and an evidence source. A transcript, edition, or scan never becomes the adaptation merely because it supplies evidence about it.

Transformative lineage is also separate from production and rights. A parody is its own creative work related by `parody-of`, optionally in a parody continuity and with detailed adaptation mappings to its basis works. Reused footage or replacement dialogue does not reduce that work to a manifestation or dub. Likewise, `fan-production`, commerciality, authorization, and rights basis do not imply one another. A web-hosted fan parody and a commercial theatrical parody can therefore share the same lineage type while retaining different production contexts and platform records. Authorization and legal-basis values are source-backed claims, never automatic consequences of the parody classification.

Applicability is a reusable axis. A whole-work scope may coexist with a higher-precedence segment, relationship, mapping, manifestation, component, package, or claim scope. Exact target/territory/precedence scopes cannot overlap in effective time. The paired loaders discover applicable scopes through explicit structural containment, territory ancestry, and inclusive effective-time matching, then return all matches, the tied highest-precedence winner set, match reasons, and indeterminate unknown-time scopes. Containment never flows sideways merely because two targets share a work. Omitted territory and time inputs conservatively exclude narrower territory- or time-bound scopes; empty territory remains an unspecified broad default rather than a worldwide assertion. Equal winning precedence is an ambiguity to report, not an invitation to guess. Work relationships may use a scope only when it resolves entirely inside their source work. Production contexts retain their owning `work_id` and use a scope to identify the exact material, relationship, territory, and time to which the context applies.

Provider catalog presentation is not canonical hierarchy. A streaming service may label material as a season, part, volume, or collection differently from the creative structure. Preserve that label in a catalog placement unless the unit independently qualifies as a work. Partial ordering schemes preserve concurrent or unresolved release branches without forcing arbitrary ordinals.

An adaptation program is a heterogeneous work group. It may contain television seasons, skipped-content specials, character specials, films, or other release forms in one adaptation continuity. Named ordering schemes preserve release order separately from story, publication, production, or recommended order. Each member remains an independent work with its own evidence sources, spoiler timeline, and relationship to the work or works it adapts.

Priority is interpreted inside a comparison group under a selected authority profile. General numeric priority remains the fallback, while claim-authority rules can rank matching source IDs, roles, media, or the evidence mode actually named by a locator differently for controlled claim namespaces. Broader claim and evidence-mode rules are inherited by narrower values, and explicit precedence selects the winner, allowing reusable defaults plus deliberate exceptions without hidden specificity behavior. Authority consumers can retrieve the source, locator mode, rank, winning rule and precedence, matched namespace, separate namespace/mode inheritance flags, and fallback state. Multi-source comparison reports a winner, tie, or incomparable set; claim evaluation groups assertions by stable `claim_key` and distinguishes one winner, corroborating ties, conflicting top-ranked values, and incomparable evidence groups. The current adaptation-comparison profile gives the novels first authority for canonical content, official artwork first authority for visual design, novel text first authority for dialogue, subtitles first authority for localization, and the official Donghua release first authority for release metadata. A disagreement therefore becomes a claim-aware comparison finding attached to the appropriate derivative or evidence layer; it does not rewrite the novel work or another continuity. Source-scoped claims and each medium's disclosure timeline remain independently valid.

The resource registry says where source material lives and how that storage is governed. The source registry identifies creative works and evidence sources and defines their separate semantic relationships.

`Tools/source_config.py` and `Tools/Source-Config.ps1` are the matching source-registry loaders. They validate media-facet compatibility, release and container forms, work/group/segment nesting, recursively nested content groups and member roles, reusable target/territory/time applicability scopes, semantic applicability decisions and precedence, scoped work relationships and continuity, temporal windows, numbering and orderings, continuities, authority profiles, works and memberships, production/right contexts, volume ranges, adaptation mappings, manifestations and version mappings, components and lineage, release packages/runs/events, territories, platform catalogs/offerings, identifiers, source observations, coverage, position schemas, aliases, priorities, comparison groups, resource bindings, and stable provenance-target lookup. Domain clients should use these normalized records and decision/comparison APIs rather than hardcoding domain values.

### Entity Registry

`Project_Config/entities.yaml` schema version 4 instantiates optional continuity-independent conceptual entities, continuity-bound incarnations, and continuity-specific identity phases when the selected schema packs enable the matching capabilities. The registry owns stable entity/incarnation/phase IDs, primary and additional taxonomy-category memberships, ambiguity-preserving labels and aliases, semantically directed and optionally acyclic entity relationships, continuity memberships, applicability-scope-backed incarnation and phase bindings, normalized incarnation relationships, and acyclic same-subject phase succession. It does not own pages, portrayals, manifestations, releases, ordinary state changes, or mistaken-ID reconciliation. A phase requires persistent identity; clones, simulations, temporal duplicates, fusions, mantle holders, and successors remain separate subjects unless identity persistence is explicitly established.

`Tools/entity_config.py` and `Tools/Entity-Config.ps1` are the matching entity-registry loaders. They consume the normalized taxonomy, selected-pack, and source registries; validate every cross-registry reference and controlled value; and expose ambiguity-safe lookup, identity-subject/target, entity-incarnation, phase, binding, relationship, reconciliation-target, and provenance-target APIs. Identity and reconciliation targeting are deliberately narrower than provenance targeting. Entity-registry records are stable provenance addresses, but evidence locators and assertions remain centralized in the provenance service. The LoTM registry intentionally begins empty until a real identity distinction warrants records. See `Framework/Contracts/narrative-entity-registry.md` and `Framework/Contracts/identity-target-provider.md`.

### Stable-ID Reconciliation

`Project_Config/reconciliation.yaml` schema version 4 owns auditable redirects, merges, splits, retirements, reclassifications, and tombstones across stable-record providers. `Tools/reconciliation_config.py` and `Tools/Reconciliation-Config.ps1` compose exact pack-controlled providers from taxonomy, resources, sources, and entities; validate closed record shapes, provider alias ownership, source existence, operation/reason compatibility, operation cardinality, same-type behavior except explicit reclassification, redirect-only compatibility for present sources, tombstone-backed active retirement, privacy-aware source-label retention, strict audit timestamps, historical supersession, terminal targets, and acyclic active resolution. Memoized iterative resolution returns canonical, redirected, ambiguous, or retired outcomes with both convenience summaries and branch-specific traversal provenance, subject to project-owned record, target-fan-out, branch, and traversal-step safety bounds. Reconciliation records are themselves provenance-addressable.

Resolution is read-only. It does not rename folders or files, rewrite page/YAML references, mutate aliases, or update generated graph IDs. The later migration service consumes reconciliation decisions through previewed, validated, reversible repository operations. Every split stays ambiguous even when its branches converge or all retire, and a tombstone reserves a historical ID against both record reuse and alias ownership.

### Provenance Registry

`Project_Config/provenance.yaml` schema version 3 owns factual assertions and claim-supersession chains independently of the registries whose records they describe. `Tools/provenance_config.py` and `Tools/Provenance-Config.ps1` compose typed provenance-target providers from source, entity, and reconciliation registries, reject unsupported or missing subjects, resolve semantic field paths, validate evidence locators against source work, coverage, and segment bounds, and evaluate claims through source-owned authority profiles. Subject registries own their records; they do not own evidence assertions about themselves.

### Temporal Kernel

`Tools/temporal_config.py` and `Tools/Temporal-Config.ps1` own the shared domain-neutral civil-time parser, precision-aware query model, and comparison behavior used by source and provenance registries. Core pack vocabulary controls interval/unknown windows, known/unknown bounds, year/month/date/datetime precision, and per-bound certainty. Intervals may be open at either end and independently inclusive or exclusive; open and unknown bounds are distinct. Canonical datetimes use at most six fractional digits, reject RFC 3339's unknown local offset form `-00:00`, and must normalize safely into years `0001` through `9999`. Exclusive bounds outside those extrema are empty and invalid. Unknown, announced, approximate, uncertain, and partial-intersection results remain explicit instead of being coerced into exact dates. See `Framework/Contracts/temporal-model.md`.

### Chronology Registry

`Project_Config/chronology.yaml` schema version 1 instantiates project-defined chronology coordinate systems, ordered eras, positions, spans, explicit order relations, cross-system anchors/equivalences, and optional narrative contexts. `Tools/chronology_config.py` and `Tools/Chronology-Config.ps1` enforce the same closed shapes, pack-owned vocabulary, integer domains, zero policies, era-local direction, relative origins, nonempty spans, coherent exact ordering, comparison behavior, and work/continuity references.

The core `chronology-coordinate-systems` capability is domain-neutral. The narrative-media `narrative-chronology` capability contributes story, backstory, flashback, flashforward, time-travel, and alternate-timeline roles. LoTM Epoch labels and ordering live in project configuration. Story chronology, causal order, publication/release order, and reader disclosure remain separate; incomparable coordinate systems remain incomparable without an explicit relationship or mapping. See `Framework/Contracts/chronology-registry.md`.

`Project_Config/occurrences.yaml` schema version 2 composes chronology into stable branch, occurrence-template, recurrence, iteration, occurrence, position-binding, perspective-track, transition, causal-relation, and carryover records. `Tools/occurrence_config.py` and `Tools/Occurrence-Config.ps1` enforce acyclic branch and recurrence topology, unique ordered iterations, valid nested recurrence, coherent primary chronology bindings, pack-registered transition kind/profile pairs, forward track order, branch-fork lineage, payload-bearing carryover, and typed provenance targets. Their query services resolve iteration contents, iteration contents in track order, track boundaries, repeated occurrences at one coordinate, ordinary track neighbors, carryover, and occurrence recurrence identity. Causal cycles are allowed because causal edges never enter chronology comparison.

Core owns domain-neutral occurrence and recurrence mechanics. Narrative media specializes them with time loops, subjective experience, loop reset/escape, and retained memory, knowledge, physical state, or awareness. The LoTM registry activates only its `main` branch until verified project data requires concrete occurrences. See `Framework/Contracts/occurrence-recurrence-registry.md`.

The required load order is project manifest, selected packs and foundational registries, source registry, chronology registry with composed work/continuity targets, entity and other subject providers, occurrence registry with chronology and subject targets, reconciliation registry, then provenance registry. Cross-registry validation is deferred to composition layers so source, chronology, occurrence, and entity loaders do not depend on one another through evidence claims or historical IDs. A new provenance-addressable registry must expose a typed target-provider API and pack-owned `provenance.subject-type` values rather than implementing another assertion parser.

### Strict Configuration Ingestion

Framework registry loaders share `Tools/strict_yaml.py` and `Tools/Strict-Yaml.ps1`. Invalid or BOM-prefixed UTF-8, non-string or noncanonical mapping keys, duplicate keys, noncanonical value scalars, implicit nulls, tags, anchors, aliases, merge keys, document markers, coerced schema-version values, unknown keys in closed registry shapes, runtime-dependent timestamp interpretations, and byte/parser-budget overruns are configuration errors rather than values to normalize silently. Canonical mapping keys are lowercase machine identifiers validated before runtime-native dictionaries are built; labels and external text remain values. Registry IDs and controlled values are case-sensitive. This strict boundary covers the project manifest and framework registries; page-embedded YAML remains a transitional content-ingestion concern until the normalized content-index contract replaces it. See `Framework/Contracts/strict-configuration-ingestion.md`.

Publication-run records, live-performance productions/events, crossover events, branching narrative state, preservation/access state, textual witnesses, editorial assembly, contributor credits, and detailed party-/asset-/instrument-scoped rights grants and restrictions remain planned capabilities. Pack ownership is established, but project data must not instantiate them until paired executable contracts are implemented.

### Visualization Configuration

Visualization settings and presets define graph views, boundaries, filtering choices, validation, rendering, and destinations. They do not redefine canonical categories or relationships.

## Component Ownership

| Component | Owns | Must Not Own |
| --- | --- | --- |
| Project configuration loaders | Root detection, manifest parsing, safe content/resource path resolution, registry discovery | Domain categories, graph semantics, page mutation |
| Schema-pack loaders | Pack selection, dependency/version validation, capabilities, controlled-value ownership | Project-instance works, pages, paths, or sources |
| Lookup-key loader | Pinned runtime-independent Unicode normalization for semantic aliases and case-insensitive values | Fuzzy matching, stable-ID rewriting, path or language-tag normalization |
| Taxonomy, resource, source, chronology, occurrence, entity, and reconciliation registry loaders | Registry parsing, schema validation, aliases, cross-registry references, pack-controlled value lookup, chronology comparison, occurrence queries, read-only stable-ID resolution | Canonical page content, graph serialization, repository mutation |
| Content index | Canonical-content discovery and normalized records | Domain constants duplicated from registries, presentation-specific graph decisions |
| Validation service | Schema, taxonomy, reference, provenance, and consistency findings | Silent canonical rewrites |
| Repository mutation service | Planned canonical edits, moves, reference updates, validation, rollback data | UI presentation, independent domain rules |
| Visualization engine | All graph projection, filtering, deduplication, styling, validation, Mermaid generation, and optional rendering | Canonical truth, fixed output lifecycle |
| QA exporter | QA orchestration, Obsidian mirrors, non-graph reports, requested graph presets, ignored output destinations | Independent graph construction, styling, or relationship projection |
| CLI tools | Argument parsing, service invocation, result reporting | Duplicate business logic |
| Streamlit and future websites | Forms, previews, navigation, service orchestration, presentation | Direct unvalidated repository mutation or competing graph/model rules |

## Visualization Boundary

Visualization owns all graph semantics and generation, regardless of where an artifact is written or whether it is tracked by Git.

The same visualization engine may produce:

- tracked canonical Mermaid sources under `Visualization/graphs/`;
- tracked rendered artifacts under `Visualization/rendered/`;
- ignored QA graphs under `Obsidian_Export/_Generated/`;
- temporary validation outputs under `.tmp/`;
- future interactive graph projections for Streamlit or a website.

The caller chooses the preset, reader boundary, filters, and output destination. Output lifecycle does not determine algorithm ownership.

The QA exporter may parse QA-only evidence and request QA graph presets, but it must pass normalized records to Visualization rather than maintain its own Mermaid builders, type styling, deduplication, or edge-projection rules.

Current direct QA generation of `QA-relationship-graph.mmd` and `QA-relationship-node-graph.mmd` predates this contract. Moving those generation paths into the reusable visualization engine is required Phase 3 migration work. Their files remain ignored QA outputs in `Obsidian_Export/`.

## Normalized Content Boundary

All consumers should eventually operate on one normalized content-record contract rather than independently scan Markdown and reinterpret YAML.

A normalized page record should expose at least:

```yaml
page_id: lotm.character.dunn-smith
category_id: character
slug: character-dunn-smith
canonical_file: Glossary_Threads/Characters/character-dunn-smith.md
title: Dunn Smith
metadata: {}
data_blocks: {}
relationships: []
```

During migration, the content index may derive missing stable IDs from existing slugs. Derived IDs are compatibility behavior, not permission to couple future identity permanently to filenames.

Non-category records should use the same normalized boundary while leaving `category_id` empty and declaring their content type, for example `record_kind: summary` and `content_type_id: volume-summary`.

## Mutation and Migration Contract

Repository-wide changes such as category-folder renames, slug-prefix changes, page moves, and schema migrations must be planned operations.

A mutation workflow must:

1. build an impact report;
2. identify affected canonical files, references, templates, configuration, presets, and generated outputs;
3. preview file moves and structured changes;
4. validate the proposed state before finalizing;
5. apply canonical changes as one reviewed operation;
6. regenerate or invalidate affected compiled views;
7. expose the resulting Git diff;
8. preserve enough operation data to recover when validation fails.

Changing only a category label is not the same operation as changing its stable ID, folder, or slug prefix. Editors must present those consequences separately.

Generated outputs must never be reverse-migrated into canonical data.

## Interface Contract

Streamlit is a planned interface, not an architecture layer. Its category generator/editor, page generator/editor, structured-data editor, QA dashboard, and graph preview must call shared services.

The same operations must remain available headlessly so automation and other interfaces are not dependent on Streamlit.

Category and page forms should eventually be schema-driven. Interface code may customize layout and usability, but field meaning and validation belong to project schemas and registries.

## Framework Extraction Boundary

The reusable framework should contain:

- manifest and registry contracts;
- configuration loaders;
- the core schema pack and schema-pack loader contract;
- optional reusable domain-pack library entries without project instances;
- normalized content indexing;
- validation services;
- repository mutation and migration services;
- visualization engine and generic graph presets;
- CLI contracts;
- configuration and page-schema support.

A domain implementation should contain:

- its project manifest;
- selected-pack registry and any project-owned extension packs;
- taxonomy, resource, source, and optional entity/incarnation registries;
- category and non-category content-type schemas and templates;
- canonical content and evidence;
- domain-specific graph presets or presentation overrides.

The framework must not assume names such as `Glossary_Threads`, `Characters`, `Pathways`, `novel`, or `donghua`. LoTM and IT repositories should configure those concepts independently while using the same services.

## Transition Sequence

The current extraction plan is:

1. **Project boundary:** manifest, root detection, configurable content/resource roots, and tool paths.
2. **Model boundary:** architecture contract, schema-pack boundary, taxonomy registry, resource registry, source registry, shared registry loaders, warning-only validation, and normalized content index.
3. **Visualization boundary:** reusable graph engine, configurable graph presets, and migration of all QA graph construction into Visualization.
4. **Framework extraction:** copy the domain-neutral contracts and services into a reusable framework repository.
5. **IT proof of concept:** define IT taxonomy, evidence priorities, schemas, sample content, and graphs without changing framework algorithms.
6. **Mutation services:** stable persisted page IDs, schema-driven creation/editing, migration planning, and linked structured-data evolution.
7. **Streamlit interface:** category, page, YAML/data, migration, QA, and graph workflows over shared services.

## Current Non-Goals

This contract does not immediately:

- split embedded YAML from Markdown pages;
- assign persisted stable IDs to every existing page;
- move ignored QA artifacts into tracked visualization folders;
- make Streamlit a dependency;
- convert every descriptive field into a controlled enum;
- require a single physical repository for the framework, LoTM domain, and IT domain.

Those changes must follow the service and migration boundaries above.
