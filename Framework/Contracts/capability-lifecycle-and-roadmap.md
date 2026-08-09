# Capability Lifecycle And Roadmap Contract

## Status And Purpose

This contract defines the capability-lifecycle authority boundary and the Phase 3.4.2 executable
delivery-traceability registry. It centralizes meanings that were previously spread across pack,
catalog, effective-schema, and planning documents. Catalog and effective-schema projections remain
deferred to Phase 3.4.3.

Schema packs remain authoritative for portable capability declarations. A separate framework-level
capability-roadmap registry describes delivery planning for declared `planned` capabilities.
The registry is development and diagnostic metadata: it cannot create a capability, change its
lifecycle, satisfy a dependency, select a pack, activate behavior, or authorize project records.

## Authority Layers

| Authority | Owns | Must Not Own |
| --- | --- | --- |
| Canonical `pack.yaml` | Capability identity, provider ownership, lifecycle, presentation, groups, relationships, controlled values, and portable semantics. | Delivery phase, accepted deferral, implementation evidence, project selection, or activation. |
| Capability-roadmap registry | Delivery target or accepted deferral, rationale, platform prerequisites, and promotion evidence for declared planned capabilities. | Capability identity or lifecycle, pack dependency satisfaction, project state, or runtime authorization. |
| `FrameworkCatalog` | Project-independent installed pack and capability inventory plus later joined roadmap diagnostics. | Project selection, activation, or roadmap authority. |
| `EffectiveProjectSchema` | Selected-pack capability composition and project activation, plus later selected-capability roadmap diagnostics. | Unselected capability inventory or independent roadmap parsing. |
| `FrameworkCatalogProjectView` | Full installed catalog annotated with one effective project's selection and availability state. | A third capability or roadmap model. |
| Framework evolution history | Confirmed implementation and verification history. | Current capability lifecycle or current roadmap disposition. |

Generated catalog, project-view, and effective-schema documents remain diagnostic projections. They
must consume the validated pack and roadmap authorities rather than becoming configuration inputs.

## Capability Lifecycle

Capability lifecycle is provider-authored portable state. It is not project activation,
implementation health, entitlement, installation, selection, usage, or roadmap disposition.

| Lifecycle | Meaning | Activation And Data Rule |
| --- | --- | --- |
| `planned` | The capability has stable identity, provider ownership, presentation, and enough reviewed semantics to be discoverable, but its executable contract is not yet available. | It is unavailable and cannot be enabled. Canonical project records must not depend on it. |
| `available` | The capability has an executable contract and supported runtime behavior satisfying the promotion gate. | A project selecting a provider pack may enable it. Omission from activation keeps it disabled. |
| `deprecated` | The capability remains executable for compatibility or migration but is no longer recommended for new use. | It remains activatable where required by existing projects and should emit an explainable warning. |

A **roadmap candidate** is not a lifecycle state. It has not yet earned a canonical pack declaration,
is absent from catalog and effective-schema capability records, and remains planning prose until its
identity, ownership, semantics, and declaration are reviewed.

### Valid Transitions

| From | To | Rule |
| --- | --- | --- |
| Roadmap candidate | `planned` | Add a reviewed canonical pack declaration and current roadmap entry together. |
| `planned` | `available` | Complete the promotion gate and change pack lifecycle, roadmap state, evidence, tests, and documentation atomically. |
| `planned` | Removed declaration | Permit only a documented withdrawal or replacement decision; never reuse the stable ID for different semantics. |
| `available` | `deprecated` | Preserve executable compatibility while recording replacement or migration guidance when applicable. |
| `deprecated` | `available` | Permit only an explicit reviewed rescission that proves the capability again satisfies the current promotion gate. |
| `deprecated` | Removed declaration | Require a compatibility decision and migration or proof that no supported project depends on it. |

An `available` capability must not regress to `planned`: doing so would make previously valid project
records and activation invalid. A `planned` capability cannot become `deprecated` because it was
never executable. Direct `available` removal is prohibited except through a separately documented
emergency compatibility decision. Renaming or repurposing a stable capability ID is not a lifecycle
transition and remains invalid.

For capabilities with multiple providers, provider declarations retain their own lifecycle. The
existing effective-lifecycle precedence remains `available`, then `deprecated`, then `planned`.
Roadmap traceability attaches to the stable capability ID, while provider-specific implementation
evidence must retain the provider pack ID. A provider transition must not falsely claim that every
other provider changed state.

## Dependency Classes

Three dependency classes remain independent:

1. **Technical pack dependencies** are portable declarations in `pack.yaml`. They govern installed
   compatibility and selected-pack composition through stable pack IDs and minimum versions.
2. **Platform implementation prerequisites** are delivery-order facts in the capability roadmap,
   such as requiring a registry, service, migration boundary, or editor contract before promotion.
3. **Domain-capability delivery dependencies** relate planned capabilities or implementation phases
   without making one pack a technical dependency of another.

Only technical pack dependencies can satisfy pack composition. Roadmap dependencies cannot select a
pack, satisfy a missing minimum version, activate a capability, or make project data valid. A valid
accepted deferral in one domain does not block unrelated packs, projects, or industries.

## Capability-Roadmap Registry Boundary

Phase 3.4.2 implements a strict framework-level registry with stable registry identity
`capability-roadmap`. `Framework/framework.yaml` must explicitly select its repository-relative
path. Loaders must not hardcode its filename, search for a plausible file, infer it from
`platform-implementation-plan.md`, or require `Project_Config/`.

The registry contains:

- a supported integer schema version and exact registry ID;
- stable delivery-target records that identify implementation phases without parsing display
  headings from Markdown;
- one current traceability entry for every capability whose effective installed lifecycle is
  `planned`;
- a disposition of either scheduled delivery or accepted deferral;
- a delivery-target reference or deferral identity and rationale, as required by disposition;
- explicit platform-prerequisite references that remain separate from pack dependencies; and
- optional typed implementation evidence used to evaluate promotion readiness without authoring a
  self-asserted `ready` boolean.

The roadmap is a current-state registry, not the historical log. Confirmed prior implementation and
verification remain in framework or platform evolution. Promotion updates the pack declaration and
roadmap atomically; historical evidence remains recoverable from the confirmed evolution record and
Git history.

### Canonical Shape

`Framework/capability-roadmap.yaml` is schema version 1. Its root is closed to
`schema_version`, `registry_id`, `delivery_targets`, and `capabilities`.

- Delivery targets are keyed by stable ID and contain exactly `kind`, `label`, `plan_path`, and
  `plan_anchor`. The only current target kind is `platform-phase`.
- Capability entries are keyed by exact catalog capability ID. `scheduled` entries require one
  `delivery_target_id`; `accepted-deferral` entries instead require `deferral_id` and
  `review_trigger`.
- Every entry requires a rationale plus explicit lists for platform prerequisites,
  domain-capability delivery dependencies, and typed implementation evidence.
- Evidence kinds are `compatibility`, `conformance`, `contract`, `documentation`, `extraction`, or
  `runtime`. Provider-scoped evidence must name a pack that declares the capability.
- The current registry maps all 13 effective installed `planned` capabilities to eight Phase 12 or
  Phase 17 delivery targets.

`Framework/framework.yaml` schema 2 requires `registries.capability_roadmap`. Framework manifest
schema 1 remains loadable for legacy isolated installations, but roadmap services reject it because
it does not select a registry.

### Identity And Ordering

Capability references use exact canonical stable IDs from installed pack declarations. Registry and
delivery-target IDs use the repository's lowercase machine-ID rules. Semantic lookup normalization
may support human inspection, but it must not establish identity, repair case drift, or choose among
ambiguous records.

Serialized delivery targets and capability entries use ordinal stable-ID order. Authored evidence
order may be preserved only where the executable registry contract declares that order meaningful.
Paths use confined framework-relative forward-slash form. No timestamp, absolute path, current
directory, user, machine, or Git working state enters canonical registry identity.

### Failure Behavior

The strict paired loaders reject at least:

- unsupported schema versions, wrong registry identity, unknown or duplicate keys, and nonportable
  YAML;
- duplicate or noncanonical stable IDs and ambiguous normalized selectors;
- unknown capability, provider-pack, delivery-target, or prerequisite references;
- a declared planned capability with no roadmap entry;
- a roadmap entry for an undeclared capability or an incompatible lifecycle/disposition pair;
- scheduled work without a delivery target and accepted deferral without an identity and rationale;
- dependency cycles, self-dependencies, invalid paths, and contradictory duplicate evidence; and
- any attempt to author capability lifecycle, project activation, entitlement, executable code, or
  technical pack-dependency satisfaction in roadmap metadata.

Malformed selected roadmap configuration fails roadmap-aware inspection and projection explicitly;
consumers must not silently omit entries or fall back to planning prose. A valid accepted deferral is
not a failure and does not make the capability available.

## Projection Boundary

Phase 3.4.3 will add projections without changing authority:

- `FrameworkCatalog` may join traceability for every installed planned capability;
- `FrameworkCatalogProjectView` may add the same traceability beside project state; and
- `EffectiveProjectSchema` may include traceability only for capabilities declared by selected
  packs, with an explicit unavailable reason for selected planned capabilities.

Unselected capabilities remain absent from `EffectiveProjectSchema`. Roadmap metadata cannot change
catalog identity, effective lifecycle precedence, selected dependency closure, controlled values,
or activation. Any serialized field addition follows the owning contract's versioning and
compatibility rules.

## Promotion Readiness

Phase 3.4.4 will make promotion criteria executable. At minimum, promotion requires a reviewed
contract, supported runtime implementation, matching runtime parity where applicable, permanent
positive/malformed/boundary/ambiguity/scale coverage, documentation, extraction review,
compatibility analysis, and required consumer regression results.

Roadmap evidence supports that decision but never authorizes it by itself. The lifecycle changes to
`available` only in the reviewed implementation change that makes the capability usable.
