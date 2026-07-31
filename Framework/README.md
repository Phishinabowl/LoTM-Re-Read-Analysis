# Knowledge Framework

This directory contains reusable framework assets that are portable across project implementations.

- `Contracts/` documents the configuration formats and ownership boundaries enforced by framework loaders.
- `Packs/` contains reusable capability and vocabulary bundles.
- Future `Migrations/` content will contain versioned transformations between contract revisions.

Project-specific composition, paths, activated capabilities, taxonomy, resources, sources, and extension packs remain under `Project_Config/`.

Framework packs must not contain LoTM works, pages, source records, repository paths, or other project instances. A project selects packs through `Project_Config/schema-packs.yaml`; selecting a pack makes its capabilities available, while the project activation policy determines which available capabilities are enabled.
