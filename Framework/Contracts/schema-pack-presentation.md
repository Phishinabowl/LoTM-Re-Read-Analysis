# Schema-Pack Presentation And Classification Contract

## Purpose

Schema packs need enough structured metadata for command-line inspection, setup wizards, editors,
documentation catalogs, and future plugin discovery without requiring those consumers to parse
README prose or infer architecture from a pack ID. Presentation metadata describes a pack to a
person. Classification metadata describes where the pack belongs architecturally. Neither changes
capability ownership, dependency resolution, activation, or entitlement.

This contract is domain-neutral. It defines portable records and validation behavior, not a fixed
catalog of industries, wizard screens, icons, colors, or commercial tiers.

## Authority Boundaries

- `pack_kind` remains the compatibility-facing validation class used by existing composition.
- `classification` is the architectural classification used by catalogs and configuration tools.
- `presentation` owns default human-facing text and stable localization keys.
- `dependencies` remain the executable pack prerequisites.
- capability lifecycle and activation remain authoritative for availability and behavior.
- entitlement, installation state, UI layout, and project usage are outside this contract.

Presentation text must never activate a capability, satisfy a dependency, grant authority, or alter
validation. A renderer may choose how to display the records but must not reinterpret them.

## Pack Classification

Each pack declares one `classification` mapping:

```yaml
classification:
  family: hosting
  role: bridge
  scope: cross-domain
  domains: [hosting, narrative]
  bridge_pack_ids: [hosting-foundation, narrative-media]
```

### Family

`family` is an extensible stable ID used to cluster related packs. It is not a closed framework
allowlist. Projects and future industries may introduce families such as `hosting`, `narrative`,
`preservation`, `operations`, or `clinical` without changing the core loader.

Family is descriptive, not authoritative. Pack ownership, dependency, and bridge validation must
not be inferred from a shared prefix or family value.

### Role

`role` is one of:

- `foundation`: reusable primitives on which other packs build;
- `domain`: the principal semantic model for a domain;
- `bridge`: explicit integration between otherwise separate foundations or domains;
- `extension`: optional behavior or vocabulary added to an existing foundation or domain.

Role is independent of `pack_kind`. A compatibility `domain` pack may be architecturally an
`extension`, and a compatibility `extension` pack may be a `bridge`.

### Scope And Domains

`scope` is one of:

- `domain-neutral`: reusable without adopting domain-facing semantics;
- `domain-specific`: intentionally contributes semantics for one or more declared domains;
- `cross-domain`: intentionally connects two or more declared domains.

`domains` is an ordinally unique list of stable IDs:

- a `domain-neutral` pack must declare an empty list;
- a `domain-specific` pack must declare at least one domain;
- a `cross-domain` pack must declare at least two domains.

All vocabulary exported by a domain-specific or cross-domain pack is interpreted within its declared
scope. A pack classified as domain-neutral must not export domain-facing vocabulary. Loaders enforce
the structural declaration and dependency closure; conformance fixtures and catalog review enforce
the semantic truth of that declaration. IDs and folder names are never accepted as proof.

### Bridge Joins

`bridge_pack_ids` is required and non-empty only when `role` is `bridge`:

- every ID must be a selected direct dependency;
- every joined pack must be classified as a `foundation` or `domain`;
- the bridge must list every foundation or domain it intentionally joins;
- a bridge must use `cross-domain` scope;
- the union of joined-pack domains and any domain-neutral foundation context must explain the
  bridge's declared domains.

Non-bridge packs must not declare bridge joins. Composition fails closed for missing, repeated,
unknown, unselected, or structurally incompatible joins.

### Dependency Scope

A domain-neutral pack may depend only on domain-neutral packs. A domain-specific pack may depend on
domain-neutral packs and packs whose declared domains are compatible with its own. Cross-domain
integration must be explicit through a bridge instead of being inferred from dependency names.

## Pack Presentation

Each user-selectable pack declares one `presentation` mapping. It is a content model, not a screen
layout:

```yaml
presentation:
  localization_key: pack.hosting-narrative
  default_locale: en
  label: Narrative Hosting Bridge
  short_description: Connects hosted identity with narrative embodiment.
  long_description: >-
    Adds physical-body and vessel vocabulary while preserving the separation between identity,
    carrier, occupancy, and narrative entity semantics.
  maturity: preview
  intended_audiences:
    - id: narrative-modeler
      label: Narrative modelers
      description: People modeling identity across bodies, vessels, or incarnations.
  use_cases:
    - id: embodied-identity
      label: Model embodied identity
      description: Connect a narrative entity to physical carriers without merging their identity.
  examples:
    - id: body-transfer
      label: Body transfer
      description: Track one identity moving between separately identified bodies.
  prerequisites:
    - id: hosting-and-narrative-foundations
      label: Hosting and narrative foundations
      description: Requires both joined packs to be selected at compatible versions.
  provided_behaviors:
    - id: narrative-carrier-vocabulary
      label: Narrative carrier vocabulary
      description: Supplies physical-body and vessel carrier kinds.
  exclusions:
    - id: identity-inference
      label: No identity inference
      description: Shared carriers do not prove entity equivalence or continuity.
  documentation:
    - id: pack-catalog
      label: Schema Pack Catalog
      target_kind: repository-path
      target: Framework/Packs/README.md
  search_keywords: [body, embodiment, hosting, identity, vessel]
```

### Localizable Text

`localization_key` is a stable dotted key unique across the pack catalog. The default English fields
remain available in portable pack files so headless clients always have useful text. A future
localization catalog may replace display text by combining the localization key with field and entry
IDs; it must not rewrite pack IDs or semantic records.

`default_locale` uses a canonical language tag and currently must be `en`. Supporting additional
locale catalogs is a later interface concern and does not require changing the pack contract.

Pack presentation requires:

- `label`;
- `short_description` suitable for a compact catalog row;
- `long_description` suitable for a detail view;
- `maturity`;
- non-empty `intended_audiences`, `use_cases`, `provided_behaviors`, and `exclusions` lists;
- `examples`, `prerequisites`, `documentation`, and `search_keywords` lists, which may be empty when
  their absence is intentional.

`maturity` is one of `experimental`, `preview`, `stable`, or `legacy`. Maturity communicates support
expectations; it does not replace pack lifecycle or capability lifecycle.

Audience, use-case, example, prerequisite, behavior, and exclusion entries use stable `id`, `label`,
and `description` fields. IDs must be unique within their list. Documentation entries use stable
`id` and `label` plus either a repository-relative path or an HTTPS URL identified by `target_kind`.
Repository paths must remain inside the project root. Loaders do not fetch external documentation.

`search_keywords` are non-empty strings normalized only for duplicate detection. Their original
human-readable spelling is preserved and output order is deterministic.

### Optional Visual Identity

An optional `visual` mapping may contain renderer-independent stable IDs such as `icon_id` and
`accent_token`. It must not contain inline SVG, binary data, CSS, absolute paths, or assumptions
about a particular UI toolkit. Absence means the client uses its own neutral default.

## Capability Presentation

Every user-selectable capability uses a mapped declaration rather than string shorthand:

```yaml
- id: hosted-identity-embodiment
  lifecycle: available
  presentation:
    localization_key: capability.hosted-identity-embodiment
    label: Hosted Identity Embodiment
    description: Model carriers, occupancy, control, and transitions without inferring identity.
```

The capability ID, lifecycle, providers, dependencies, availability, activation, and project usage
remain semantic fields outside presentation. Capability presentation requires a globally stable
localization key, friendly label, and useful description. Multiple providers of the same capability
must use the same localization key and semantically equivalent default text; composition rejects
conflicting presentation.

## Human-Facing Inspection Model

Singular inspection is a filtered view over `EffectiveProjectSchema`, not a second schema authority.
A pack inspection record contains:

- stable ID, schema version, pack version, lifecycle, and compatibility `pack_kind`;
- classification and presentation;
- resolved dependencies and bridge joins;
- provided capabilities and controlled-value contributions.

A capability inspection record contains:

- stable ID and presentation;
- effective lifecycle, availability, activation, and deprecation state;
- provider packs and each provider's declaration;
- dependencies, recommendations, conflicts, groups, and project usage when later phases add them.

CLI selectors may render these records for humans or emit deterministic JSON, but spacing, headings,
and terminal styling are not part of this contract. Unknown IDs fail with exact stable-ID context.
If normalization would match multiple IDs, selection fails as ambiguous rather than choosing one.

## Composition And Determinism

- Pack and capability localization keys must be globally unique within a composed schema.
- Stable IDs, classification lists, presentation entry lists, documentation entries, and keywords
  preserve declared order where it communicates author intent.
- Registry summaries and lookup indexes use ordinal stable-ID order.
- Optional fields serialize explicitly according to the effective-schema contract; clients must not
  invent missing visual identity.
- Presentation-only changes may change inspection output but must not change capability activation,
  controlled values, page discovery, QA relationships, graph projection, or canonical content.

## Versioning And Migration

The implementation of this contract advances schema-pack files to schema version 5. Existing
top-level pack `label` and `description` values migrate into `presentation.label` and
`presentation.short_description`; authored long descriptions must add useful detail rather than
repeat the short text. Runtime objects may retain read-only label and description accessors during
consumer migration, but schema-5 pack files have one presentation authority.

String-shorthand capability declarations are not valid in schema 5. The catalog migration must
backfill every capability with lifecycle and presentation metadata before singular capability
inspection is enabled.

## Conformance Requirements

Paired Python and PowerShell suites must prove:

- exact classification and presentation parity;
- all role, scope, domain, dependency, and bridge invariants;
- required metadata and unique localization keys;
- malformed entry, keyword, documentation target, visual identifier, and path rejection;
- equivalent multi-provider capability presentation;
- rejection of conflicting provider presentation;
- deterministic composition and singular lookup;
- generated scale behavior with rich metadata;
- unchanged semantic composition when only presentation text changes;
- full QA and Visualization compatibility after catalog migration.
