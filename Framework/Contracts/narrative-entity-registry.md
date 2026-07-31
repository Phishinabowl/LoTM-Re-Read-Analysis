# Narrative Entity Registry Contract

## Purpose

`Project_Config/entities.yaml` instantiates conceptual subjects and their continuity-bound realizations for projects that enable the `entity-incarnations` capability from `narrative-shared-universe`.

An **entity** is a continuity-independent conceptual subject. An **incarnation** is one realization of that subject whose identity is bounded by a continuity. An **entity relationship** connects distinct conceptual subjects without pretending that successors, mantle holders, clones, namesakes, instances, or composite inspirations are alternate realizations of one subject. These distinctions support adaptations, reboots, alternate universes, branches, and crossovers without forcing every page, portrayal, or state change to become a separate subject.

## Boundaries

Create a separate incarnation only when continuity incompatibility matters to claims, relationships, chronology, or projection. Do not create an incarnation merely for:

- a disguise, alias, title, role, age, pathway/ability state, or other change inside one continuity;
- an actor, voice actor, performance, visual design, translation, or localized name;
- an edition, cut, release, manifestation, evidence source, or platform offering;
- a page, investigation, graph node, or generated view.

Those concerns remain owned by page data, taxonomy, source/manifestation records, production records, or presentation layers. A single incarnation may list additional continuity memberships when it crosses into another continuity without becoming a different realization.

## Registry Shape

Schema version 2 contains:

- `entities`: stable IDs with lifecycle, one `primary_category_id`, one or more taxonomy `category_ids`, label, and aliases;
- `entity_relationship_types`: project-instantiated, pack-constrained relationship definitions with reciprocal inverse and symmetry declarations;
- `entity_relationships`: stable typed edges between conceptual entities, optionally qualified by an applicability scope and semantic `basis_roles` for derivation, inspiration, or composite construction;
- `incarnations`: stable IDs with an owning entity, label/aliases, one primary continuity, and one or more status-bearing continuity memberships;
- `incarnation_bindings`: stable records connecting an incarnation to an existing source-registry `applicability_scope_id` with a pack-owned binding type and membership status;
- `incarnation_relationship_types`: project-instantiated, pack-constrained relationship definitions with reciprocal inverse and symmetry declarations;
- `incarnation_relationships`: stable typed edges between incarnation records, optionally qualified by an applicability scope.

All IDs use lowercase kebab case. Every entity category must exist in the taxonomy registry, and the primary category must be one of that entity's category memberships. Continuities and applicability scopes must exist in the source registry. Membership and relationship statuses come from `source.membership-status`; binding, relationship, and basis-role values come from the selected shared-universe pack.

## Entity Relationship Semantics

Use entity relationships for same-continuity or conceptual distinctions such as succession, namesakes, legacy, mantle holding, cloning, faction splintering, derivation, composites, inspiration, or class/instance identity. Store one direction of an inverse pair; `A successor-to B` and `B has-successor A` are the same fact and cannot coexist as duplicate records.

`basis_roles` may appear only on `derived-from`, `composite-of`, or `inspired-by` records. They identify which semantic dimensions came from a basis entity, such as identity, name, appearance, personality, history, abilities, relationships, or narrative function. They do not assign unsupported numeric contribution weights.

## Binding Semantics

Bindings qualify where an incarnation is primary, appears, or crosses into material already described by a reusable applicability scope. The scope remains owned and semantically resolved by the source registry. A binding does not duplicate the scope target, territory, effective time, or precedence.

Continuity membership and material applicability are different facts. An incarnation can belong to a continuity without appearing in every work in that continuity, and a crossover appearance can bind to narrow material without changing the incarnation's primary continuity.

## Provenance And Pages

Entity, entity-relationship, incarnation, binding, and incarnation-relationship IDs are stable provenance-addressable records. The paired loaders expose typed lookup APIs so a future central provenance service can validate assertions across registries. Source-registry assertions do not yet accept these cross-registry targets; do not duplicate locator or evidence logic inside `entities.yaml`.

Canonical pages do not yet store entity or incarnation IDs. That migration must use the shared mutation service and preserve page slugs as presentation/storage identifiers rather than silently treating a rename as a new conceptual entity. Until then, an empty project entity registry is valid and preferable to speculative incarnation splits.

## Planned Adjacent Contracts

`entity-identity-phases` remains planned for addressable same-continuity phases such as regenerations, temporal duplicates, simulations, and ontologically distinct transformations. `entity-identity-reconciliation` remains planned for auditable merges, redirects, mistaken duplicates, and superseded stable IDs. Do not misuse incarnations or aliases to approximate either contract.

## Loader Contract

`Tools/entity_config.py` and `Tools/Entity-Config.ps1` must remain behaviorally equivalent. They validate schema version, capability activation, stable IDs, category memberships and primary-category selection, entity and continuity references, applicability-scope bindings, controlled values and basis-role placement, alias uniqueness, inverse relationship definitions, endpoint existence, self-relationships, and duplicate or inverse-duplicate bindings/relationships.
