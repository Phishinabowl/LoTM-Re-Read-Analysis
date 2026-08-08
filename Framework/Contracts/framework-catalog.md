# Framework Catalog Contract

## Status And Purpose

This document defines the Phase 3.2.1 generated `FrameworkCatalog` contract. The catalog is a
project-independent, deterministic inventory of installed schema packs and their capabilities. It
exists so setup tools, documentation, editors, and later user interfaces can inspect what the
framework installation offers before a project exists or without treating one project's selected
packs as the complete framework.

The catalog is diagnostic output. Canonical `pack.yaml` files remain authoritative and the catalog
must never be edited or ingested as configuration.

## Boundary From EffectiveProjectSchema

`FrameworkCatalog` and `EffectiveProjectSchema` answer different questions:

| Contract | Question | Required inputs |
| --- | --- | --- |
| `framework-catalog` | What packs and capabilities are installed in this framework? | Framework root and canonical pack files. |
| `effective-project-schema` | What schema is effective for this validated project composition? | Project manifest, selected packs, activation, taxonomy, resources, and later project registries. |

Catalog discovery does not select packs, activate capabilities, merge controlled vocabulary into a
project schema, or claim that every installed pack can be selected together. The base catalog has no
project identity or project-state fields. Phase 3.2.2 may combine a catalog with an effective schema
only through the separate `framework-catalog-project-view` contract.

The contracts may reuse the canonical pack and capability stable IDs as references because those IDs
come from the same pack files. Their generated document identities, record meanings, serializers,
and selection-envelope IDs remain distinct. A catalog pack row means "installed pack"; an effective-
schema pack row means "pack selected into this project."

## Authority And Shared Record Model

The paired schema-pack loaders own one validated per-pack record model. Catalog and project
composition services consume that model rather than parsing pack YAML independently.

Per-pack parsing validates the pack schema, stable identity, version, lifecycle, compatibility kind,
dependencies, classification, presentation, capability declarations, controlled-value
contributions, and semantic declarations. Catalog-wide validation then checks only invariants that
are truthful across an installed inventory, including unique pack IDs and paths, dependency targets
and versions, dependency acyclicity, classification/dependency compatibility, bridge joins, and
pack/capability localization-key consistency.

Project composition retains ownership of selection order, selected dependency closure, capability
activation, merged controlled-value ownership, composed semantic declarations, and project-facing
diagnostics. Catalog loading must not call the project schema-pack registry loader as a shortcut.

## Root Resolution And Installed-Pack Discovery

Catalog loading accepts a framework repository root, not a configured project root. A valid root
contains `Framework/Packs/`. It does not require `Project_Config/project.yaml` or
`Project_Config/schema-packs.yaml`.

Installed bundled packs are immediate child directories of `Framework/Packs/` that contain exactly
one canonical `pack.yaml`. Discovery follows these rules:

- resolve the supplied root to an absolute directory for safe filesystem access, but never serialize
  that absolute path;
- enumerate immediate pack directories without recursively interpreting unrelated YAML files;
- normalize discovered relative paths to forward slashes;
- parse each pack through the shared validated per-pack loader;
- require the directory name, declared pack ID, and discovered catalog key to match exactly;
- reject duplicate IDs, duplicate resolved files, case-colliding directories, missing dependency
  targets, incompatible dependency versions, and dependency cycles;
- order catalog pack rows by ordinal stable pack ID, independent of filesystem enumeration order.

A directory without `pack.yaml` is not an installed pack and is ignored. A discovered `pack.yaml`
that is malformed fails catalog construction; discovery must not silently omit a broken installed
pack. Project-owned extension-pack discovery is deferred until an installation/extension registry
defines that root explicitly; Phase 3.2.1 does not infer arbitrary pack locations from a project.

## Catalog Document

The canonical JSON document uses this top-level order:

```json
{
  "contract": "framework-catalog",
  "contract_version": 1,
  "framework": {
    "packs_root": "Framework/Packs"
  },
  "summary": {
    "pack_count": 0,
    "capability_count": 0,
    "available_capability_count": 0,
    "deprecated_capability_count": 0,
    "planned_capability_count": 0
  },
  "packs": [],
  "capabilities": []
}
```

Every field is required. Counts are nonnegative integers derived from the emitted rows. The document
contains no project fields, activation state, timestamps, host details, or absolute paths.

### Pack Rows

Each `packs` row contains:

- `id`, the canonical pack stable ID;
- `record_id`, `framework-catalog:pack:<id>`, the generated catalog-record identity;
- `path`, the repository-relative canonical pack path;
- `schema_version`, `pack_version`, `lifecycle`, and compatibility `kind`;
- `classification` and `presentation` using the schema-pack presentation contract;
- `dependencies`, in declared order, each with `pack_id`, `minimum_version`,
  `installed_version`, and `status: satisfied`;
- `capability_ids`, in declared order;
- `controlled_value_namespaces`, ordered by ordinal namespace ID, each containing its declared values
  without merging contributions from other packs;
- `discoverability`, containing `installed: true` and `selectable`.

`selectable` is true when the pack is active and every installed dependency/version condition is
satisfied. Deferred packs remain installed and inspectable but are not selectable. Because catalog
construction fails for broken dependency installation, Phase 3.2.1 does not serialize speculative
missing-dependency states.

### Capability Rows

Each `capabilities` row contains:

- `id`, the canonical capability stable ID;
- `record_id`, `framework-catalog:capability:<id>`;
- the common validated `presentation`;
- `effective_lifecycle`, resolved as `available` when any provider declares available, otherwise
  `deprecated` when any provider declares deprecated, otherwise `planned`;
- derived `available`, `deprecated`, and `planned` booleans;
- `providers`, ordered by ordinal pack ID, each containing `pack_id`, declaration lifecycle, and the
  provider declaration's presentation.

Catalog capability rows never contain `enabled`, `disabled`, `selected`, or `used_by_project`.
Multiple providers do not imply that their packs form a valid project selection; they only describe
independent installed declarations. Conflicting provider presentation is a catalog validation error.

## Selection Contract

Singular lookup emits a separate envelope:

```json
{
  "contract": "framework-catalog-selection",
  "contract_version": 1,
  "catalog_contract_version": 1,
  "requested": {
    "pack": null,
    "capability": null
  },
  "packs": [],
  "capabilities": []
}
```

Pack and capability selectors are independent and may be combined. Each non-null selector returns
exactly one complete catalog row. Exact stable-ID matching is attempted before shared lookup-key
normalization. No match fails with the requested value and record kind. Multiple normalized matches
fail as ambiguous and report every candidate stable ID in ordinal order; the service never chooses a
winner. Selection does not change or filter the base catalog object.

## Reports And Export

Paired catalog commands provide:

- a concise default overview;
- composable detailed `packs` and `capabilities` sections;
- singular pack and capability inspection;
- canonical JSON on standard output or in a confined export file;
- a human-readable report written to a confined file.

Human spacing and terminal styling are not contract fields. Python and PowerShell render the same
semantic rows and deterministic section order. Shared selector normalization, report models, text or
Markdown rendering, JSON primitives, failure envelopes, and output-path confinement may be reused
with effective-schema inspection only where their behavior is genuinely identical.

Explicit output paths must resolve to files beneath the supplied root. The root itself and paths
outside it fail before writing. Exports use UTF-8 without a byte-order mark, LF line endings, and one
final newline. Catalog commands import their runtime service; Python and PowerShell commands never
invoke one another.

## Failure Envelope

Structured failures use `framework-catalog-result`, contract version 1, with `catalog: null` and one
stable diagnostic. Failure classification distinguishes root discovery, installed-pack discovery,
pack parsing, catalog composition, selector, and output-path errors. Diagnostics may include
repository-relative paths and stable IDs but never absolute machine paths.

## Determinism And Versioning

Catalog output is deterministic for identical canonical pack files:

- mappings use the field order defined here;
- pack, capability, provider, candidate, and summary-derived collections use their specified order;
- authored dependency, presentation-entry, documentation, keyword, capability, and controlled-value
  order is preserved where the pack contract says it communicates author intent;
- absent optional visual identity serializes as `null`;
- no generated time, current directory, user, machine, or project state enters the document.

Removing or renaming a field, changing field meaning or ordering, or changing null/empty behavior
requires a `contract_version` increment and an explicit compatibility decision. Generated snapshots
may support tests and diagnostics but never become a loader input.

## Phase 3.2.1 Conformance

Permanent paired coverage must prove canonical 14-pack discovery, complete capability presentation,
deterministic repeat loading, dependency and classification validation, deferred/planned/deprecated
discoverability, multi-provider capability handling, exact and normalized singular lookup,
ambiguity rejection, malformed root and pack failures, path confinement, generated scale behavior,
and Python/PowerShell 7/Windows PowerShell 5.1 parity. Existing effective-schema, schema-pack, QA, and
Visualization behavior remains unchanged during this phase.
