# Narrative Entity Registry Contract

## Purpose

`Project_Config/entities.yaml` instantiates conceptual subjects and their continuity-bound realizations for projects that enable the `entity-incarnations` capability from `narrative-shared-universe`.

An **entity** is a continuity-independent conceptual subject. An **incarnation** is one realization of that subject whose identity is bounded by a continuity. This distinction supports adaptations, reboots, alternate universes, branches, and crossovers without forcing every page, portrayal, or state change to become a separate subject.

## Boundaries

Create a separate incarnation only when continuity incompatibility matters to claims, relationships, chronology, or projection. Do not create an incarnation merely for:

- a disguise, alias, title, role, age, pathway/ability state, or other change inside one continuity;
- an actor, voice actor, performance, visual design, translation, or localized name;
- an edition, cut, release, manifestation, evidence source, or platform offering;
- a page, investigation, graph node, or generated view.

Those concerns remain owned by page data, taxonomy, source/manifestation records, production records, or presentation layers. A single incarnation may list additional continuity memberships when it crosses into another continuity without becoming a different realization.

## Registry Shape

Schema version 1 contains:

- `entities`: stable IDs with lifecycle, taxonomy `category_id`, label, and aliases;
- `incarnations`: stable IDs with an owning entity, label/aliases, one primary continuity, and one or more status-bearing continuity memberships;
- `incarnation_bindings`: stable records connecting an incarnation to an existing source-registry `applicability_scope_id` with a pack-owned binding type and membership status;
- `incarnation_relationship_types`: project-instantiated, pack-constrained relationship definitions with reciprocal inverse and symmetry declarations;
- `incarnation_relationships`: stable typed edges between incarnation records, optionally qualified by an applicability scope.

All IDs use lowercase kebab case. Entity categories must exist in the taxonomy registry. Continuities and applicability scopes must exist in the source registry. Membership and relationship statuses come from `source.membership-status`; binding and relationship types come from the selected shared-universe pack.

## Binding Semantics

Bindings qualify where an incarnation is primary, appears, or crosses into material already described by a reusable applicability scope. The scope remains owned and semantically resolved by the source registry. A binding does not duplicate the scope target, territory, effective time, or precedence.

Continuity membership and material applicability are different facts. An incarnation can belong to a continuity without appearing in every work in that continuity, and a crossover appearance can bind to narrow material without changing the incarnation's primary continuity.

## Provenance And Pages

Entity, incarnation, binding, and relationship IDs are stable provenance-addressable records. The paired loaders expose typed lookup APIs so a future central provenance service can validate assertions across registries. Source-registry assertions do not yet accept these cross-registry targets; do not duplicate locator or evidence logic inside `entities.yaml`.

Canonical pages do not yet store entity or incarnation IDs. That migration must use the shared mutation service and preserve page slugs as presentation/storage identifiers rather than silently treating a rename as a new conceptual entity. Until then, an empty project entity registry is valid and preferable to speculative incarnation splits.

## Loader Contract

`Tools/entity_config.py` and `Tools/Entity-Config.ps1` must remain behaviorally equivalent. They validate schema version, capability activation, stable IDs, category and entity references, continuity membership, applicability-scope bindings, controlled values, alias uniqueness, inverse relationship definitions, endpoint existence, self-relationships, and duplicate bindings or relationships.
