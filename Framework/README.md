# Knowledge Framework

This directory contains reusable framework assets that are portable across project implementations.

- `Contracts/` documents the configuration formats and ownership boundaries enforced by framework loaders.
- `Data/` contains portable pinned runtime data used by framework contracts.
- `Packs/` contains reusable capability and vocabulary bundles.
- `framework.yaml` is the project-independent installation bootstrap that explicitly selects the
  pack root and pinned lookup registry used by framework catalog discovery.
- `framework_improvement_lifecycle.md` defines the end-to-end version iteration, confirmation, testing, historical closure, and handoff workflow.
- `testing_methodology.md` defines the cross-industry pressure-test candidate catalog plus cumulative conformance, runtime-parity, compatibility, pressure-scenario, comparison, and test-retention requirements.
- `framework_evolution.md` records the historical implementation and pressure-test results that drove each framework version.
- `platform_evolution.md` records confirmed platform-phase implementation, migration, compatibility closure, and handoff history without duplicating numbered framework-version pressure records.
- `extraction_readiness.md` records the proven portable bundle, project-owned boundary, extraction rehearsal, stabilization evidence, and limits of the current readiness claim.
- `analytical-projection-architecture.md` defines the downstream JSON, SQLite, Parquet, notebook, medallion, and optional Databricks/Delta path without changing canonical authority.
- `platform-implementation-plan.md` is the phased execution checklist for effective schema composition, normalized content, consumer migration, LoTM physical migration, projections, add-on packs, the IT proof of concept, interfaces, and the ordered deferred-capability program. It also records capability candidates that are not yet pack declarations.
- Future `Migrations/` content will contain versioned transformations between contract revisions.

Platform Phases 1 through 3.2.3 are complete. The generated project-independent `FrameworkCatalog`
inventories all installed packs while each project's `EffectiveProjectSchema` selects validated
catalog records and adds activation, taxonomy, resources, and diagnostics. Explicit project
attachment produces a separate `FrameworkCatalogProjectView` without mutating either source.
The shared effective-schema report model also publishes a deterministic noncanonical Markdown view
through Obsidian QA. Capability grouping and later interface work remain subsequent boundaries.

Project-specific composition, paths, activated capabilities, taxonomy, resources, sources, and extension packs remain under `Project_Config/`. See `Contracts/framework-installation.md` for the bootstrap boundary; it does not replace a project manifest or select project packs.

Framework packs must not contain LoTM works, pages, source records, repository paths, or other project instances. A project selects packs through `Project_Config/schema-packs.yaml`. Selection makes capability declarations discoverable; capability lifecycle determines availability, and the project activation policy determines which available capabilities are enabled.

Enter framework improvement mode through `framework_improvement_lifecycle.md`, then use `testing_methodology.md` at its required testing checkpoints. See `Packs/README.md` for the composable narrative pack catalog and media-axis rules. See `Contracts/framework-catalog.md` for the generated project-independent installed-pack inventory, `Contracts/effective-project-schema.md` for the generated project-schema inspection boundary, `Contracts/lookup-key-normalization.md` for deterministic semantic lookup, `Contracts/temporal-model.md` for portable civil-time windows, `Contracts/chronology-registry.md` for non-civil coordinate systems and narrative chronology contexts, `Contracts/occurrence-recurrence-registry.md` for distinct happenings, iterations, transitions, and participant tracks, `Contracts/structural-interpretation-registry.md` for competing candidate structures that do not mutate canonical graphs, `Contracts/narrative-source-registry.md` for the executable narrative source schema, and `Contracts/reconciliation-registry.md` for auditable stable-ID resolution.
