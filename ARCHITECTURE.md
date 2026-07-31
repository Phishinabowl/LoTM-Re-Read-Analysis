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

`Project_Config/project.yaml` is the bootstrap manifest. It identifies the project, locates canonical content roots, and declares tool-integration paths. As supporting registries are added, the manifest will locate them without absorbing their domain definitions.

`Tools/project_config.py` and `Tools/Project-Config.ps1` are the matching manifest-loader implementations. They locate and validate project configuration; they do not own domain taxonomy.

### Taxonomy Registry

The planned `Project_Config/taxonomy.yaml` owns:

- stable category IDs;
- category labels, folders, slug prefixes, and graph classes;
- controlled relationship types and reciprocal behavior;
- strict field-scoped enums and their aliases;
- confidence or precedence orderings that affect generic projection behavior;
- explicitly extensible domain vocabularies.

The registry must distinguish strict enums, extensible vocabularies, aliases, and free descriptive fields. There must not be one global `status`, `type`, or `confidence` allowlist when those names serve different model contexts.

### Source Registry

The planned `Project_Config/sources.yaml` owns:

- stable source and medium IDs;
- source priority;
- original-versus-adaptation relationships;
- source-specific labels and reference conventions;
- conflict, deviation, and unresolved-difference policy.

Source priority must guide comparison and deviation reporting without erasing independently modeled disclosure timelines.

### Visualization Configuration

Visualization settings and presets define graph views, boundaries, filtering choices, validation, rendering, and destinations. They do not redefine canonical categories or relationships.

## Component Ownership

| Component | Owns | Must Not Own |
| --- | --- | --- |
| Project configuration loaders | Root detection, manifest parsing, safe path resolution, registry discovery | Domain categories, graph semantics, page mutation |
| Taxonomy and source registry loaders | Registry parsing, schema validation, aliases, controlled-value lookup | Canonical page content, graph serialization |
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
- taxonomy and source registries;
- category schemas and templates;
- canonical content and evidence;
- domain-specific graph presets or presentation overrides.

The framework must not assume names such as `Glossary_Threads`, `Characters`, `Pathways`, `novel`, or `donghua`. LoTM and IT repositories should configure those concepts independently while using the same services.

## Transition Sequence

The current extraction plan is:

1. **Project boundary:** manifest, root detection, configurable content roots, and tool paths.
2. **Model boundary:** architecture contract, taxonomy registry, source registry, shared registry loaders, warning-only validation, and normalized content index.
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
