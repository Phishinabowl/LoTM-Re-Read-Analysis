# Knowledge Model Architecture Contract

## Status

This document is the authoritative architecture and component-ownership contract for the repository and for the reusable knowledge-model framework being extracted from it.

It describes both the required target architecture and the boundaries that new work must follow during migration. When current code does not yet match this contract, treat the mismatch as transition debt to remove, not as precedent for additional duplication.

LoTM-specific authoring, evidence, taxonomy, and spoiler-modeling rules remain in [PROJECT_RULES.md](PROJECT_RULES.md). Tool switches and current implementation details remain in [Tools/TOOLING_REFERENCE.md](Tools/TOOLING_REFERENCE.md).

## Architectural Goals

The system must:

- support multiple knowledge domains without hardcoding LoTM folder names, page types, sources, or relationship vocabularies into framework code;
- preserve human-readable canonical articles alongside structured, machine-readable state;
- generate reader-safe projections without making generated outputs canonical;
- expose the same model, validation, visualization, and mutation behavior to command-line tools, QA workflows, future websites, and editor interfaces;
- support controlled repository-wide migrations such as category, folder, slug, or schema changes;
- preserve Python-preferred tooling with behaviorally compatible PowerShell fallbacks where repository policy requires them.

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

`Tools/project_config.py` and `Tools/Project-Config.ps1` are the matching manifest-loader implementations. They locate and validate project configuration and registry paths; they do not own domain taxonomy.

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

Examples include visual assets, local source material, executable tools, project configuration, generated visualizations, QA exports, design records, application state, and temporary artifacts. These are intentionally not taxonomy content types. The distinction lets an IT implementation map the same contracts to diagrams, vendor documentation, logs, automation, configuration, generated topology views, and local working state.

`Tools/resource_config.py` and `Tools/Resource-Config.ps1` are the matching registry loaders. They validate stable IDs, resource-root and kind references, controlled lifecycle/authority/tracking values, safe relative placements, required paths, and placement uniqueness.

### Source Registry

The planned `Project_Config/sources.yaml` owns:

- stable source and medium IDs;
- source priority;
- original-versus-adaptation relationships;
- source-specific labels and reference conventions;
- conflict, deviation, and unresolved-difference policy.

Source priority must guide comparison and deviation reporting without erasing independently modeled disclosure timelines.

The resource registry says where source material lives and how that storage is governed. The source registry will identify the evidence sources themselves and define their semantic priority and derivation relationships.

### Visualization Configuration

Visualization settings and presets define graph views, boundaries, filtering choices, validation, rendering, and destinations. They do not redefine canonical categories or relationships.

## Component Ownership

| Component | Owns | Must Not Own |
| --- | --- | --- |
| Project configuration loaders | Root detection, manifest parsing, safe content/resource path resolution, registry discovery | Domain categories, graph semantics, page mutation |
| Taxonomy, resource, and source registry loaders | Registry parsing, schema validation, aliases, controlled-value lookup | Canonical page content, graph serialization |
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
- normalized content indexing;
- validation services;
- repository mutation and migration services;
- visualization engine and generic graph presets;
- CLI contracts;
- configuration and page-schema support.

A domain implementation should contain:

- its project manifest;
- taxonomy, resource, and source registries;
- category and non-category content-type schemas and templates;
- canonical content and evidence;
- domain-specific graph presets or presentation overrides.

The framework must not assume names such as `Glossary_Threads`, `Characters`, `Pathways`, `novel`, or `donghua`. LoTM and IT repositories should configure those concepts independently while using the same services.

## Transition Sequence

The current extraction plan is:

1. **Project boundary:** manifest, root detection, configurable content/resource roots, and tool paths.
2. **Model boundary:** architecture contract, taxonomy registry, resource registry, source registry, shared registry loaders, warning-only validation, and normalized content index.
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
