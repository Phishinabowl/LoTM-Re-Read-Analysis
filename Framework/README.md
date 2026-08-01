# Knowledge Framework

This directory contains reusable framework assets that are portable across project implementations.

- `Contracts/` documents the configuration formats and ownership boundaries enforced by framework loaders.
- `Data/` contains portable pinned runtime data used by framework contracts.
- `Packs/` contains reusable capability and vocabulary bundles.
- Future `Migrations/` content will contain versioned transformations between contract revisions.

Project-specific composition, paths, activated capabilities, taxonomy, resources, sources, and extension packs remain under `Project_Config/`.

Framework packs must not contain LoTM works, pages, source records, repository paths, or other project instances. A project selects packs through `Project_Config/schema-packs.yaml`. Selection makes capability declarations discoverable; capability lifecycle determines availability, and the project activation policy determines which available capabilities are enabled.

See `Packs/README.md` for the composable narrative pack catalog and media-axis rules. See `Contracts/lookup-key-normalization.md` for deterministic semantic lookup, `Contracts/temporal-model.md` for portable windows and precision-aware queries, `Contracts/narrative-source-registry.md` for the executable narrative source schema, and `Contracts/reconciliation-registry.md` for auditable stable-ID resolution.
