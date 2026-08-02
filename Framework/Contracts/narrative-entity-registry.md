# Narrative Entity Registry Contract

## Purpose

`Project_Config/entities.yaml` instantiates conceptual subjects, continuity-bound realizations, and persistent-identity phases for projects that enable the `entity-incarnations` and `entity-identity-phases` capabilities from `narrative-shared-universe`.

An **entity** is a continuity-independent conceptual subject. An **incarnation** is one realization of that subject whose identity is bounded by a continuity. An **identity phase** is an addressable continuity-specific epoch during which that entity or incarnation retains identity. An **entity relationship** connects distinct conceptual subjects without pretending that successors, mantle holders, clones, namesakes, instances, or composite inspirations are alternate realizations of one subject. These distinctions support adaptations, reboots, alternate universes, branches, transformations, and crossovers without forcing every page, portrayal, or state change to become a separate subject.

## Boundaries

Create a separate incarnation only when continuity incompatibility matters to claims, relationships, chronology, or projection. Do not create an incarnation merely for:

- a disguise, alias, title, role, age, pathway/ability state, or other change inside one continuity;
- an actor, voice actor, performance, visual design, translation, or localized name;
- an edition, cut, release, manifestation, evidence source, or platform offering;
- a page, investigation, graph node, or generated view.

Those concerns remain owned by page data, taxonomy, source/manifestation records, production records, or presentation layers. A single incarnation may list additional continuity memberships when it crosses into another continuity without becoming a different realization.

Create an identity phase only when persistent identity and the phase itself both matter to claims, chronology, relationships, or projection. Regenerations, reincarnations, restorations, and ontological transformations may qualify when identity persistence is explicitly established. Ordinary aging, disguises, titles, roles, power changes, injuries, employment, and other state changes remain page or domain data. A clone, simulation, temporal duplicate, fusion, mantle holder, or successor is not a phase merely because it resembles or derives from another subject; model it as a separate entity, incarnation, or relationship unless persistent identity is established.

## Registry Shape

Schema version 4 contains:

- `entities`: stable IDs with lifecycle, one `primary_category_id`, one or more taxonomy `category_ids`, label, and aliases;
- `entity_relationship_types`: project-instantiated, pack-constrained relationship definitions with reciprocal inverse, symmetry, canonical-direction, and optional acyclic-group declarations;
- `entity_relationships`: stable typed edges between conceptual entities, optionally qualified by an applicability scope and semantic `basis_roles` for derivation, inspiration, or composite construction;
- `incarnations`: stable IDs with an owning entity, label/aliases, one primary continuity, and one or more status-bearing continuity memberships;
- `incarnation_bindings`: stable records connecting an incarnation to an existing source-registry `applicability_scope_id` with a pack-owned binding type and membership status;
- `incarnation_relationship_types`: project-instantiated, pack-constrained relationship definitions with reciprocal inverse, symmetry, canonical-direction, and optional acyclic-group declarations;
- `incarnation_relationships`: stable typed edges between incarnation records, optionally qualified by an applicability scope;
- `identity_phases`: stable, labeled, alias-aware phases with one identity subject, continuity, and pack-owned phase type;
- `identity_phase_bindings`: stable records connecting a phase to material through an existing applicability scope;
- `identity_phase_relationship_types`: project-instantiated, pack-constrained inverse relationship definitions; and
- `identity_phase_relationships`: stable ordering edges between phases of the same subject and continuity.

All IDs and acyclic-group IDs use lowercase kebab case. Every entity category must exist in the taxonomy registry, and the primary category must be one of that entity's category memberships. Continuities and applicability scopes must exist in the source registry. Membership and relationship statuses come from `source.membership-status`; binding, relationship, and basis-role values come from the selected shared-universe pack.

Labels and aliases are search names, not unique identifiers. Multiple distinct entities, incarnations, or phases may legitimately share a name. Exact stable-ID lookup always wins. Plural resolution returns every matching stable ID; singular resolution returns a unique match, returns no value when there is no match, and raises an explicit ambiguity error when several records share the name. An alias still cannot impersonate another record's stable ID.

## Entity Relationship Semantics

Use entity relationships for same-continuity or conceptual distinctions such as succession, namesakes, legacy, mantle holding, cloning, faction splintering, derivation, composites, inspiration, or class/instance identity. Store one direction of an inverse pair; `A successor-to B` and `B has-successor A` are the same fact and cannot coexist as duplicate records. Every asymmetric inverse pair declares exactly one `canonical_direction: true`; symmetric types are self-inverse and canonical. Canonicalization follows that semantic declaration rather than relationship-ID sorting.

An inverse pair may share an `acyclic_group` when cycles are semantically invalid. The loaders normalize every edge into its canonical direction and reject cycles within each group. Unscoped edges act as global defaults and participate in every scoped cycle check; edges from two different explicit scopes are not combined with one another. Succession, cloning, splintering, derivation/composition, class-instance hierarchy, incarnation branching, reboot lineage, and incarnation derivation are acyclic. Inspiration and other relationships that can legitimately be mutual remain outside acyclic groups.

`basis_roles` may appear only on `derived-from`, `composite-of`, or `inspired-by` records. They identify which semantic dimensions came from a basis entity, such as identity, name, appearance, personality, history, abilities, relationships, or narrative function. They do not assign unsupported numeric contribution weights.

## Binding Semantics

Bindings qualify where an incarnation is primary, appears, or crosses into material already described by a reusable applicability scope. The scope remains owned and semantically resolved by the source registry. A binding does not duplicate the scope target, territory, effective time, or precedence.

Continuity membership and material applicability are different facts. An incarnation can belong to a continuity without appearing in every work in that continuity, and a crossover appearance can bind to narrow material without changing the incarnation's primary continuity.

## Identity Phase Semantics

A phase names either an `entity` or `entity-incarnation` through the identity-subject provider API and always names one registered continuity. An incarnation-owned phase must use one of that incarnation's continuity memberships. Entity ownership allows a project to model phases without inventing a default incarnation when no continuity split otherwise exists.

Phase bindings reuse source-owned applicability scopes and classify the phase as primary or appearing in that material. A phase scope must resolve to one or more canonical works and every resolved work must belong to the phase continuity. Bindings do not copy source targets, territory, effective time, or precedence. Phase ordering is explicit rather than inferred from labels, IDs, publication order, or overlapping scopes. `succeeds` and `precedes` are reciprocal views of one fact; endpoints must retain one subject and continuity, inverse duplicates are invalid, and the canonical succession graph is acyclic. Overlapping scope or time coverage is not rejected by itself because nonlinear disclosure and unresolved chronology may coexist.

## Provenance And Pages

Entity, entity-relationship, entity-incarnation, incarnation-binding, incarnation-relationship, identity-phase, identity-phase-binding, and identity-phase-relationship IDs are stable provenance-addressable records. The paired loaders expose typed lookup APIs consumed by the standalone provenance registry. Entities, incarnations, and identity phases also participate in the narrower reconciliation-target provider API. Do not treat every provenance target as an identity, and do not duplicate identity history, locator, evidence, assertion, or claim-supersession logic inside `entities.yaml`.

Canonical pages do not yet store entity or incarnation IDs. That migration must use the shared mutation service and preserve page slugs as presentation/storage identifiers rather than silently treating a rename as a new conceptual entity. Until then, an empty project entity registry is valid and preferable to speculative incarnation splits.

## Planned Adjacent Contracts

Domain-neutral stable-ID reconciliation is executable through `Project_Config/reconciliation.yaml`. It consumes the entity identity-target provider alongside other stable-record providers rather than overloading aliases or deleting historical IDs. Do not use phases, incarnations, or aliases to approximate redirects, merges, splits, retirements, or tombstones.

## Loader Contract

`Tools/Runtime/Python/knowledge_framework/entity_config.py` and `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` must remain behaviorally equivalent. They validate schema version, capability activation, stable IDs, category memberships and primary-category selection, entity and continuity references, applicability-scope bindings, controlled values and basis-role placement, alias-to-ID conflicts, phase subject/continuity compatibility, inverse/canonical relationship definitions, acyclic groups, endpoint existence, self-relationships, and duplicate or inverse-duplicate bindings/relationships. They expose plural ambiguity-preserving name resolution and strict singular resolution for entities, incarnations, and phases; subject-to-phase, phase-to-binding, and phase-to-relationship queries; typed identity-target lookup; and expanded provenance targets.
