# Knowledge Platform Implementation Plan

This plan coordinates the remaining framework, schema-composition, normalized-content,
Visualization, QA, LoTM migration, analytical-projection, pack-management, and interface work.
It is an execution checklist rather than an architecture contract or historical log.

Use this document together with:

- `ARCHITECTURE.md` for component ownership and dependency boundaries;
- `Framework/framework_improvement_lifecycle.md` for every numbered framework version;
- `Framework/testing_methodology.md` for cumulative verification and pressure testing;
- `Framework/framework_evolution.md` for confirmed implementation and test history;
- `Tools/Compatibility/compatibility.json` for executable consumer-regression coverage; and
- `Tools/CI_implementation_plan.md` for the completed tooling, conformance, CI, and extraction
  foundation on which this plan depends.

## Operating Rules

- Complete phases in dependency order unless this plan explicitly allows parallel work.
- Treat implementation phases and framework versions as separate scales. A phase may contain zero,
  one, or several framework versions; version boundaries are chosen through the improvement
  lifecycle rather than predicted permanently by this roadmap.
- Treat each numbered framework-schema change as a framework version and use the full improvement
  lifecycle, including proposed tests, two-part confirmation, pressure testing, and evolution
  closure.
- Update this checklist as each subphase is confirmed. A checked item means implemented, tested,
  documented, committed, and pushed unless its wording explicitly describes a design decision.
- Add or revise permanent conformance, compatibility, and static-policy coverage as behavior moves
  into shared services. Do not create a second test inventory in this document.
- Preserve current LoTM canonical files and generated-output behavior until a phase's equivalence
  gate passes.
- Perform logical migration before physical migration. Existing files may feed a new normalized
  model before their canonical storage layout changes.
- Use previewed migration services for repository-wide physical changes. Do not perform a manual
  big-bang rewrite.
- Keep framework packs, services, and contracts free of LoTM vocabulary and paths.
- Stop at each major phase, and at migration subphases when useful, for maintainer review.

## Completion Definitions

### Logical Migration

Legacy canonical files are parsed into the new effective schema and normalized content model.
Consumers use the new services, but the canonical files may remain byte-for-byte unchanged.

### Physical Migration

Canonical page or registry storage is deliberately rewritten, split, moved, or assigned persisted
identities through a previewed and validated migration operation.

### Consumer Equivalence

For reviewed representative inputs, a migrated consumer preserves all intended information and
either matches the prior output or records an accepted, explained improvement. Output filenames,
artifact ownership, cleanup behavior, reader boundaries, provenance, and cross-runtime semantics
remain protected.

## Phase 0: Completed Foundation

- [x] Establish the reusable core and narrative schema-pack library.
- [x] Separate framework contracts, project configuration, canonical content, resources, and
  generated views.
- [x] Add strict project, pack, taxonomy, resource, source, entity, provenance, chronology,
  reconciliation, and occurrence loaders.
- [x] Establish Python and PowerShell runtime parity for framework-owned contracts.
- [x] Add aggregate conformance, compatibility, static-policy, CI, and extraction-readiness gates.
- [x] Define graph ownership under Visualization and the normalized-content boundary.
- [x] Define the local-first JSON, SQLite, DuckDB/Parquet, and optional Databricks/Delta analytical
  projection direction.
- [x] Retain current Visualization and Obsidian QA behavior as compatibility-protected consumers.

## Phase 1: Temporal And Recurrence Model Stabilization

V38 is the fixed entry point to this phase, not its completion condition. Later version numbers and
scope divisions are provisional: each preceding pressure test may split, combine, reorder, or add
work through the normal framework improvement lifecycle. Phase 2 must not begin merely because V38
passes. It begins after the retained Loki gaps have been implemented or explicitly reviewed and
deferred at the stabilization gate.

### Phase 1.1 V38 Definition

- [x] Re-enter framework improvement mode through the lifecycle document.
- [x] Recover the confirmed V37 implementation and testing state.
- [x] Define V38 around typed effect semantics and fail-closed execution.
- [x] Include the two retained V37 declaration defects and conflict-wide execution behavior.
- [x] Select required conformance, parity, compatibility, and pressure-test coverage before editing.

### Phase 1.2 V38 Implementation And Closure

- [x] Implement V38 across contracts, packs, Python, PowerShell, fixtures, and documentation.
- [x] Complete the two-part implementation confirmation with the implementation commit recorded in
  `framework_evolution.md`.
- [x] Run the cumulative V38 pressure test under `Framework/testing_methodology.md`.
- [x] Record findings, update durable methodology where needed, confirm, and push the testing record.
- [x] Verify the LoTM Visualization and QA compatibility baseline remains green.

### Phase 1.3 Aggregate And Uncertain Recurrence Cardinality

- [x] Define a bounded framework version after V38 for exact, minimum, maximum, ranged, unknown,
  and aggregate recurrence cardinality.
- [x] Represent large or source-unspecified repetition counts without inventing concrete iterations.
- [x] Permit representative concrete iterations to coexist with an aggregate execution history.
- [x] Preserve evidence, certainty, and reader/source applicability for every cardinality assertion.
- [x] Prove Loki's centuries of Loom attempts without asserting an unsupported exact total.
- [x] Replay retry, recurring medical episode, scheduled legal obligation, and scientific-trial
  scenarios so the capability remains domain-neutral.
- [x] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.4 Participation Identity And Revisited Occurrences

- [x] Define a bounded framework version that separates occurrence identity, participation identity,
  and subjective-track entry identity.
- [x] Permit one subject to participate in or encounter one concrete occurrence more than once
  without duplicating that occurrence.
- [x] Preserve role, perspective, participation status, chronology context, and subjective ordering per
  participation.
- [x] Model Loki's self-pruning occurrence once while retaining his earlier recipient participation
  and later agent participation.
- [x] Test repeated observation, review, intervention, retry inspection, and cross-domain
  participation cases.
- [ ] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.5 Chronology-Context Topology

- [ ] Define a bounded framework version for typed relations among chronology contexts without
  turning those relations into chronological precedence.
- [ ] Model relations such as outside, observes, oversees, intervenes-in, projects-into, and
  receives-from through pack-owned vocabulary and validated typed targets.
- [ ] Preserve incomparability between chronology coordinates unless an explicit mapping relates
  them.
- [ ] Connect interventions to concrete occurrences, branches, and applicability scopes without
  claiming that extratemporal means unordered.
- [ ] Prove TVA-local order, timeline oversight, and branch intervention while retaining ordinary
  chronology cycle rejection.
- [ ] Replay distributed-system control planes, simulations, archival observation, and other
  non-narrative context-topology cases.
- [ ] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.6 Timeline-Branch Lifecycle

- [ ] Define a bounded framework version for branch identity and state history.
- [ ] Support pack-owned branch states such as emerging, active, pruned, transferred, restored,
  merged, preserved, and inactive without assuming every domain uses every state.
- [ ] Represent pruning or deactivation as a provenance-backed transition rather than deletion.
- [ ] Preserve branch lineage, continuity membership, applicability, and state at a requested
  boundary.
- [ ] Model Loki's branching timelines, TVA pruning, restoration/preservation, and final replacement
  structure without collapsing branches into one chronology.
- [ ] Replay source-control branches, environment promotion, alternate histories, and scientific
  experiment branches.
- [ ] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.7 Knowledge, Skill, And Acquisition Progression

- [ ] Decide through version design whether knowledge acquisition and skill progression form one
  bounded capability or require separate versions.
- [ ] Distinguish knowledge, belief, awareness, memory, skill, proficiency, and physical state where
  the selected packs require those distinctions.
- [ ] Support continuous, sudden, external, partial, conditional, inferred, merged-memory,
  dream/prophecy, timeline-reconciliation, and practice-based acquisition mechanisms without
  forcing narrative vocabulary into core.
- [ ] Represent qualitative or bounded quantitative progression without inventing unsupported
  precision.
- [ ] Preserve retention, loss, restoration, contradiction, source evidence, and applicability
  independently from chronology.
- [ ] Model Loki's accumulated engineering understanding and retained expertise across Loom attempts.
- [ ] Replay education, credential acquisition, incident diagnosis, clinical understanding,
  investigative inference, and scientific learning scenarios.
- [ ] Complete every resulting version's lifecycle, confirmation, pressure test, and evolution
  closure.

### Phase 1.8 Temporal Stabilization Pressure Test

- [ ] Replay the complete source-grounded Loki scenario across both seasons.
- [ ] Replay the source-grounded Derrick abandoned-temple loop.
- [ ] Exercise aggregate attempts, repeated participation, extratemporal context topology, branch
  lifecycle, retained state, and expertise progression together rather than only in isolation.
- [ ] Run the complete cumulative conformance, three-runtime parity, project compatibility, and
  retained cross-industry pressure portfolio.
- [ ] Confirm that chronology remains acyclic while causal, recurrence, participation, and context
  topology use their own typed relations.
- [ ] Record every remaining limitation as supported, explicitly deferred, or outside the intended
  framework boundary.
- [ ] Update the testing methodology and candidate catalog when this phase discovers durable new
  test obligations.
- [ ] Confirm and push the final stabilization test record.

### Phase 1 Exit Gate

- [ ] No known V37/V38 semantic defect blocks higher-level schema composition.
- [ ] Uncertain/aggregate recurrence cardinality is supported or explicitly deferred.
- [ ] Repeated participation in one concrete occurrence is supported or explicitly deferred.
- [ ] Typed extratemporal chronology-context relations are supported or explicitly deferred.
- [ ] Timeline-branch lifecycle is supported or explicitly deferred.
- [ ] Knowledge and expertise progression is supported at the agreed boundary or explicitly
  separated into a later capability with maintainer approval.
- [ ] The retained Loki and Derrick scenarios pass without invented chronology cycles, occurrence
  duplication, unsupported precision, or silent state transfer.
- [ ] Framework evolution identifies the accepted next version or Phase 2 handoff.

## Phase 2: Effective Project Schema Service

### Phase 2.1 Effective-Schema Contract

- [ ] Define one domain-neutral `EffectiveProjectSchema` contract.
- [ ] Include project identity and schema versions.
- [ ] Include selected packs, dependency order, lifecycle, versions, labels, and descriptions.
- [ ] Include declared, available, deprecated, planned, enabled, and disabled capabilities.
- [ ] Include capability providers and dependency/conflict diagnostics.
- [ ] Include composed controlled-value namespaces, definitions, broader-value relationships, and
  owning packs.
- [ ] Include current content types, categories, placements, templates, graph/QA eligibility, and
  resource integration where relevant.
- [ ] Define deterministic ordering and a stable JSON serialization contract.
- [ ] Keep the exported schema generated and diagnostic rather than canonical.

### Phase 2.2 Runtime And Command Surface

- [ ] Implement matching effective-schema composition in Python and PowerShell where parity applies.
- [ ] Add a headless inspection/export command with human-readable and JSON output.
- [ ] Ensure library consumers import the service rather than shelling out to the command.
- [ ] Add positive, disabled, planned, deprecated, dependency, ambiguity, malformed, and scale tests.
- [ ] Register new permanent coverage in the aggregate conformance inventory.
- [ ] Document the API, command, output schema, and compatibility rules.

### Phase 2.3 Initial Consumer Adoption

- [ ] Make QA discover enabled content roots, content types, categories, labels, and eligibility from
  the effective schema.
- [ ] Make Visualization discover graph classes and enabled projection capabilities from the
  effective schema where current configuration permits.
- [ ] Remove replaced consumer-local category and capability allowlists.
- [ ] Preserve current page parsing and graph construction until later phases replace them.

### Phase 2 Exit Gate

- [ ] QA, Visualization, CLI, and future UI code can inspect one identical effective schema.
- [ ] Existing LoTM outputs remain compatibility-equivalent.

## Phase 3: Pack Presentation And Configuration Model

### Phase 3.1 Pack Presentation Metadata

- [ ] Define structured short and long descriptions, intended audience, use cases, examples,
  prerequisites, provided behavior, exclusions, maturity, documentation links, search keywords,
  and optional visual identifiers.
- [ ] Require friendly labels and useful descriptions for every user-selectable pack and capability.
- [ ] Backfill string-shorthand capabilities that need user-facing metadata.
- [ ] Keep presentation metadata localizable and independent of UI layout code.

### Phase 3.2 Capability Grouping

- [ ] Define stable capability groups suitable for wizard steps and editor navigation.
- [ ] Allow packs to contribute capabilities to ordered groups without duplicating capability
  ownership.
- [ ] Represent dependencies, recommendations, conflicts, and planned-only features clearly.
- [ ] Distinguish installed, selected, available, enabled, deprecated, and used-by-project states.
- [ ] Add effective-schema output for groups and presentation metadata.

### Phase 3.3 Plugin And Entitlement Boundary

- [ ] Treat declarative schema packs as versioned plugins without granting arbitrary code execution.
- [ ] Define a separate trusted extension boundary for any future executable plugin.
- [ ] Keep commercial entitlement/licensing outside portable pack semantics.
- [ ] Allow an entitlement service to control discoverability or installation without changing pack
  composition rules.

### Phase 3 Exit Gate

- [ ] A headless client can present packs and capabilities coherently without reading README prose.
- [ ] No licensing assumption leaks into reusable schema contracts.

## Phase 4: Page Modules, Fields, Defaults, And Validation Levels

### Phase 4.1 Page-Schema Contract

- [ ] Define reusable page modules independently from page instances and Markdown templates.
- [ ] Define field identity, type, cardinality, labels, help text, controlled-value source,
  applicability, ordering, and display hints.
- [ ] Compose modules through core contracts, domain packs, project profiles, content types,
  categories, and project extensions.
- [ ] Prevent page files from copying module or field definitions.
- [ ] Define deterministic composition and conflict behavior.

### Phase 4.2 Requirement Semantics

- [ ] Support `required`, `conditional`, `recommended`, `optional`, `omit-if-empty`, and `derived`
  semantics.
- [ ] Define conditional requirements against enabled capabilities, record lifecycle, other field
  values, and requested readiness level.
- [ ] Define readiness levels such as draft-valid, graph-ready, publishable, and evidence-complete.
- [ ] Ensure incomplete optional release, territory, localization, or evidence details do not block a
  useful draft record.

### Phase 4.3 Defaults And Inference

- [ ] Distinguish literal defaults, inherited context, definitional implications, suggested defaults,
  and computed derivations.
- [ ] Record value origin where persistence or explanation requires it.
- [ ] Permit overrides only where the owning rule declares them valid.
- [ ] Treat source-backed facts such as exact release dates and production details as evidence, not
  silent inference.
- [ ] Prove a Donghua example in which cultural form implies animation while optional release data
  remains absent and production assertions remain explicit.

### Phase 4.4 Template And Editor Schema

- [ ] Generate or validate templates from composed page modules without inserting empty optional
  sections into canonical pages.
- [ ] Expose form-ready schemas through `EffectiveProjectSchema`.
- [ ] Preserve human-authored prose fields separately from taxonomy/display-label conversion.

### Phase 4 Exit Gate

- [ ] A page editor can know what to require, suggest, derive, hide, and omit without hardcoded
  category forms.
- [ ] Existing LoTM templates can be described without forcing all optional modules onto every page.

## Phase 5: Normalized Content And Legacy Compatibility

### Phase 5.1 Normalized Record Contract

- [ ] Finalize normalized identities for pages and non-page content records.
- [ ] Include content type, optional category, canonical location, title, metadata, structured
  modules, relationships, evidence links, visibility, and diagnostics.
- [ ] Define normalized relationship identity, endpoints, type, state history, provenance,
  applicability, and projection metadata.
- [ ] Keep normalized records independent of Markdown/YAML physical layout.

### Phase 5.2 Legacy LoTM Adapter

- [ ] Parse current Markdown metadata, embedded structured data blocks, Relationship Seeds, and
  relevant timeline/knowledge records.
- [ ] Derive temporary stable IDs deterministically where persisted IDs do not yet exist.
- [ ] Record every compatibility-derived value and unresolved ambiguity.
- [ ] Preserve legacy source locations for migration reports and diagnostics.
- [ ] Avoid changing canonical LoTM pages during logical migration.

### Phase 5.3 Content Index

- [ ] Build one project-wide normalized content index.
- [ ] Detect duplicate identities, paths, slugs, unresolved endpoints, invalid projection sources,
  schema/module violations, and unsupported legacy constructs.
- [ ] Expose typed query services for consumers.
- [ ] Add JSON snapshots suitable for compatibility comparison without making them canonical.

### Phase 5 Exit Gate

- [ ] Current LoTM content can be represented without information loss.
- [ ] QA and Visualization no longer need to scan Markdown independently once migrated.

## Phase 6: Relationship Ownership And Projection Contract

### Phase 6.1 Canonical Relationship Model

- [ ] Make normalized structured relationships own facts, timing, confidence/state progression,
  provenance, applicability, and stable identity.
- [ ] Define universal relationship fields plus pack/category-specific extensions.
- [ ] Preserve conflicting and lower-priority evidence rather than overwriting it.
- [ ] Define inverse normalization, deduplication, supersession, and ambiguity behavior.

### Phase 6.2 Thin Projection Declarations

- [ ] Define graph projection declarations that reference canonical relationship IDs.
- [ ] Limit declarations to graph relevance, projection scope, presentation override, and explicitly
  provisional behavior.
- [ ] Preserve pending-page, semantic-hub, anonymous, and local-context use cases.
- [ ] Prevent projection declarations from becoming a second factual history.

### Phase 6.3 Legacy Seed Translation

- [ ] Translate existing Relationship Seeds and `projection_source` references into normalized
  relationships plus projection declarations.
- [ ] Report duplicate, conflicting, orphaned, or unresolvable translations.
- [ ] Retain full QA provenance during translation.
- [ ] Defer physical seed removal until category migrations are confirmed.

### Phase 6 Exit Gate

- [ ] One normalized relationship contract can explain every current QA relationship.
- [ ] No consumer needs to choose independently between seed facts and data-block facts.

## Phase 7: Visualization Consolidation

### Phase 7.1 Reusable Graph Engine

- [ ] Make Visualization consume effective-schema and normalized-content services.
- [ ] Centralize node eligibility, labels, styles, pending/stub behavior, boundary evaluation,
  relationship deduplication, progression display, and projection filtering.
- [ ] Keep presets, output destinations, and rendering separate from semantic graph construction.
- [ ] Add subject, hop-depth, category, sequence, source, work, and reader-boundary filtering hooks.

### Phase 7.2 Existing Graph Migration

- [ ] Migrate canonical repository graph presets.
- [ ] Migrate the unbounded Visualization relationship graph used by QA.
- [ ] Migrate direct-edge QA relationship graphs.
- [ ] Migrate intermediary relationship-node QA graphs.
- [ ] Preserve timing-bounded graph behavior and pending-node visibility.

### Phase 7 Exit Gate

- [ ] Visualization is the sole owner of all Mermaid graph semantics and generation.
- [ ] Canonical and redirected graph compatibility checks pass across supported runtimes.

## Phase 8: QA Exporter And Bounded Projection Migration

### Phase 8.1 QA Service Boundaries

- [ ] Make QA consume effective schema for content discovery and presentation metadata.
- [ ] Make QA consume the normalized content index for pages, data, relationships, and visibility.
- [ ] Make QA request every graph from Visualization rather than constructing Mermaid directly.
- [ ] Retain QA ownership of mirrors, anomaly reports, inventories, bounded-page requests, and
  maintainer-focused provenance presentation.

### Phase 8.2 Bounded Pages

- [ ] Generalize bounded-page machinery beyond character-specific parsing.
- [ ] Drive bounded sections and tables from composed page modules.
- [ ] Preserve anonymous, hidden, and canonical first-appearance behavior.
- [ ] Preserve medium-specific availability and reader-boundary selection.
- [ ] Keep generated prose extraction honest; do not synthesize unsupported narrative prose.

### Phase 8.3 Full-Binding And Artifact Lifecycle

- [ ] Re-evaluate the planned full-binding option against completed page-schema coverage.
- [ ] Generate all eligible bounded pages only when explicitly requested.
- [ ] Preserve stale-output cleanup, run-scoped temporary ownership, and unrelated-file safety.
- [ ] Keep generated bounded folders absent when no matching request is made.

### Phase 8 Exit Gate

- [ ] QA contains no independent graph semantics or category-specific schema duplication.
- [ ] Python, PowerShell 7, and Windows PowerShell 5.1 retain required consumer parity.

## Phase 9: LoTM Compatibility Freeze Before Physical Migration

### Phase 9.1 Representative Regression Portfolio

- [ ] Preserve the current canonical repository graphs and their semantic snapshots.
- [ ] Preserve all Obsidian mirror notes, indexes, QA reports, and graph variants.
- [ ] Preserve bounded graph and bounded-page requests at representative early, middle, and late
  reader positions.
- [ ] Retain Dunn Smith's anonymous-to-canonical reveal and Sleepless confidence progression.
- [ ] Retain Leonard Mitchell's later reveals and optional Tarot Card module behavior.
- [ ] Retain pending/provisional nodes, source-vs-seed provenance, orphan reporting, and stale-output
  cleanup.

### Phase 9.2 Equivalence Review

- [ ] Compare old and new normalized records and generated artifacts.
- [ ] Classify every difference as equivalent formatting, accepted improvement, fixed defect, or
  regression.
- [ ] Add permanent vectors for every fixed defect or newly durable behavior.
- [ ] Require maintainer approval before enabling the new consumers by default.

### Phase 9 Exit Gate

- [ ] Logical migration is complete and compatibility-protected.
- [ ] Physical LoTM migration can begin without using generated output as authority.

## Phase 10: Generalized Summary Model

### Phase 10.1 Summary Contract

- [ ] Define one reusable summary-page contract with typed targets and coverage.
- [ ] Support work segments, works, content groups, ordered series, franchises, and applicability
  scopes without duplicating source hierarchy.
- [ ] Support chapter, episode, arc, season, volume, book, series, and franchise display scopes as
  pack/project vocabulary.
- [ ] Separate hand-authored canonical summaries from generated summary projections.
- [ ] Define boundary, evidence, artwork, major-development, thread, and structured-prose modules.

### Phase 10.2 LoTM Volume Compatibility Mapping

- [ ] Map `volume-summary` logically into the generalized summary contract without rewriting its
  canonical page or template.
- [ ] Preserve the existing Volume 1 page, template, artwork, links, and graph exclusion behavior.
- [ ] Decide whether the project keeps a specialized volume profile over the generic summary type.
- [ ] Defer physical summary-page conversion to Phase 13 migration services.

### Phase 10 Exit Gate

- [ ] A summary references canonical source-model targets rather than rebuilding book/episode
  hierarchy in page data.

## Phase 11: Generated Data Projections

### Phase 11.1 Projection Metadata

- [ ] Define compiler version, project revision/digest, schema-pack versions, generation time,
  authority policy, applicability context, and reader-boundary metadata.
- [ ] Define deterministic invalidation and rebuild behavior.
- [ ] Keep every output clearly generated and noncanonical.

### Phase 11.2 JSON

- [ ] Export effective schema and normalized content for website, API, interoperability, and
  debugging consumers.
- [ ] Add deterministic snapshots and schema-version handling.

### Phase 11.3 SQLite

- [ ] Add a portable local query projection for QA, editors, and single-machine applications.
- [ ] Define normalized tables, indexes, rebuild behavior, and transaction boundaries.
- [ ] Do not treat SQLite as the canonical collaborative server.

### Phase 11.4 DuckDB And Parquet

- [ ] Add Parquet projections only when concrete analytical queries and schemas are identified.
- [ ] Use DuckDB for local columnar querying, notebooks, profiling, and analytical validation.
- [ ] Keep notebook experiments downstream of shared compiler services.
- [ ] Promote durable notebook logic into runtime modules and permanent tests.

### Phase 11.5 Optional Lakehouse Adapter

- [ ] Defer Delta/Databricks implementation until measured distributed ingestion, scale, governance,
  lineage, or multi-team requirements justify it.
- [ ] Require any lakehouse adapter to consume the same normalized contracts and preserve
  bronze/silver/gold authority semantics.

### Phase 11 Exit Gate

- [ ] Local website, editor, QA, and analytical consumers can use generated projections without
  changing canonical authority.

## Phase 12: Mutation And Migration Services

### Phase 12.1 Planning And Preview

- [ ] Add stable persisted page/content IDs.
- [ ] Build impact reports for schema changes, category renames, page moves, storage splits,
  relationship migrations, pack activation, upgrades, disabling, and removal.
- [ ] Preview canonical edits, file moves, reference changes, generated-output invalidation, and test
  impact.
- [ ] Refuse ambiguous or unsafe plans.

### Phase 12.2 Apply And Recovery

- [ ] Validate proposed state before applying changes.
- [ ] Apply canonical changes as one reviewed operation.
- [ ] Preserve operation records sufficient for diagnosis and recovery.
- [ ] Regenerate or invalidate every affected projection.
- [ ] Expose a complete Git diff for maintainer review.

### Phase 12 Exit Gate

- [ ] Physical migrations no longer depend on hand-editing repeated schema or relationship data.

## Phase 13: Physical LoTM Data Migration

Each wave must parse the legacy representation, propose the new canonical representation, compare
normalized outputs, run relevant conformance and compatibility profiles, receive maintainer review,
and retain rollback through Git. Do not remove a compatibility adapter before its entire migration
wave is confirmed.

### Phase 13.1 Pilot And Storage Decision

- [ ] Decide whether canonical prose and structured records remain embedded or become linked files.
- [ ] Define stable linking, atomic-edit, validation, and missing-sidecar behavior.
- [ ] Pilot the final layout with Dunn Smith before broad migration.
- [ ] Repeat with Old Neil and Leonard Mitchell to exercise optional and late-reveal modules.

### Phase 13.2 Character Wave

- [ ] Migrate the character template and all existing character pages.
- [ ] Migrate character relationships and projection declarations.
- [ ] Remove character-only legacy compatibility after equivalence is confirmed.

### Phase 13.3 Pathway Wave

- [ ] Complete pathway schema/template normalization, including sequences and neighboring pathways.
- [ ] Migrate existing pathway pages and graph projections.

### Phase 13.4 Remaining Glossary Waves

- [ ] Migrate factions and families.
- [ ] Migrate artifacts and items.
- [ ] Migrate locations.
- [ ] Migrate events and event subtypes such as fights.
- [ ] Migrate knowledge sources.
- [ ] Migrate concepts, deities, epochs, tarot cards, and remaining approved categories.
- [ ] Introduce future material or preparation categories only through reviewed pack/taxonomy work.

### Phase 13.5 Non-Glossary Content

- [ ] Migrate investigations.
- [ ] Physically migrate summary pages from the Phase 10 compatibility mapping.
- [ ] Migrate boards, dashboards, and navigation indexes where structured modeling adds value.

### Phase 13.6 Legacy Retirement

- [ ] Remove obsolete duplicated template/schema declarations.
- [ ] Remove migrated Relationship Seed factual duplication.
- [ ] Remove compatibility parsers only after no canonical record depends on them.
- [ ] Run the full-release and framework extraction gates.

### Phase 13 Exit Gate

- [ ] All existing LoTM canonical data uses the accepted schema/storage model.
- [ ] No information present before migration has been silently lost.

## Phase 14: Solution Profiles, Recommendations, And Add-On Lifecycle

### Phase 14.1 Solution Profiles

- [ ] Define versioned industry solutions and starter profiles separately from packs.
- [ ] Allow profiles to recommend packs, capabilities, categories, modules, graph presets, and
  project settings without inventing project facts.
- [ ] Add initial narrative profiles such as serialized fiction, shared-universe fiction, screen
  series, and fantasy worldbuilding.
- [ ] Make every recommendation previewable and optional unless required by a selected contract.

### Phase 14.2 Suggested Schemas

- [ ] Define reusable optional schemas such as magic systems without hardcoding them into all
  fantasy projects.
- [ ] Distinguish recommended, selected, enabled, and instantiated state.
- [ ] Record user-selected, inherited, suggested, and derived setting origins.

### Phase 14.3 Add-On Operations

- [ ] Discover compatible add-on packs.
- [ ] Preview dependency selection, capability activation, schema changes, and migrations.
- [ ] Activate additive capabilities without rewriting unrelated records.
- [ ] Block disabling or removing packs while project data still depends on them unless an accepted
  migration resolves that dependency.
- [ ] Prove adding shared-universe/parallel-continuity support to an existing narrative project.

### Phase 14 Exit Gate

- [ ] A project can safely gain a new capability family after creation through shared services.

## Phase 15: Framework Extraction And IT Proof Of Concept

### Phase 15.1 Extracted Framework Product

- [ ] Rehearse the expanded portable bundle including effective schema, page modules, normalized
  content, projections, and mutation services.
- [ ] Decide the physical repository/package distribution model.
- [ ] Keep LoTM as a consumer and permanent compatibility corpus.

### Phase 15.2 IT Solution And Pack

- [ ] Define an IT/operations solution profile and domain packs without narrative vocabulary.
- [ ] Model representative infrastructure, systems, applications, environments, configurations,
  evidence, incidents, changes, diagrams, and vendor references.
- [ ] Define source-priority and authority examples appropriate to operational evidence.
- [ ] Build sample content, summaries, graphs, QA, JSON, and SQLite projections.
- [ ] Use Parquet/DuckDB only where the POC has concrete analytical questions.
- [ ] Pressure-test whether any supposedly universal behavior still belongs in narrative packs.

### Phase 15 Exit Gate

- [ ] The framework supports a real non-narrative consumer without algorithm forks or LoTM leakage.

## Phase 16: Streamlit And Future Interfaces

### Phase 16.1 Read-Only Workbench

- [ ] Display effective schema, pack/capability state, validation findings, normalized records, QA
  reports, and graph previews through shared services.

### Phase 16.2 Project And Schema Wizards

- [ ] Add industry/profile selection, recommended packs, capability groups, progressive disclosure,
  dependency explanations, and impact previews.
- [ ] Keep setup and editing workflows distinct.

### Phase 16.3 Category And Page Editing

- [ ] Add schema-driven category generator/editor and page generator/editor.
- [ ] Add structured-data editing with required/optional/derived behavior.
- [ ] Add linked prose/data editing without duplicating schema definitions.
- [ ] Route every mutation through preview, validation, and migration services.

### Phase 16.4 Operational Hardening

- [ ] Add authentication, authorization, concurrency, audit, deployment, and server persistence only
  when the chosen product boundary requires them.
- [ ] Re-evaluate SQLite versus a multi-user database for collaborative deployments.
- [ ] Re-evaluate Databricks/Delta only for justified analytical or enterprise ingestion workloads.

### Phase 16 Exit Gate

- [ ] The interface is a replaceable client over tested headless services rather than the owner of
  schema or domain behavior.

## Final Completion Gate

- [ ] Effective schema composition is inspectable and deterministic.
- [ ] Packs, capabilities, modules, defaults, and recommendations are understandable and safely
  composable.
- [ ] Structured facts and graph projection declarations have unambiguous ownership.
- [ ] QA and Visualization share normalized content and one graph engine.
- [ ] Summary pages target the source model instead of duplicating it.
- [ ] LoTM is physically migrated without information loss.
- [ ] JSON, SQLite, and justified analytical projections remain rebuildable.
- [ ] Add-on packs can be installed, activated, upgraded, disabled, and removed safely.
- [ ] The extracted framework supports the IT proof of concept.
- [ ] Streamlit and future interfaces depend only on shared headless services.
