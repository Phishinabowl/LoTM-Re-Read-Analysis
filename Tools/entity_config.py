from dataclasses import dataclass
from pathlib import Path
import re

import yaml

from project_config import ProjectConfig
from schema_pack_config import SchemaPackRegistry, load_schema_pack_registry
from source_config import SourceRegistry
from taxonomy_config import TaxonomyConfig


SUPPORTED_ENTITY_SCHEMA_VERSION = 2
LIFECYCLES = {"active", "deferred"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class EntityConfig:
    id: str
    lifecycle: str
    primary_category_id: str
    category_ids: tuple[str, ...]
    label: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class EntityRelationshipType:
    id: str
    label: str
    inverse_type: str
    symmetric: bool


@dataclass(frozen=True)
class EntityRelationship:
    id: str
    source_entity_id: str
    relationship_type: str
    target_entity_id: str
    status: str
    applicability_scope_id: str | None
    basis_roles: tuple[str, ...]


@dataclass(frozen=True)
class IncarnationContinuityMembership:
    continuity_id: str
    status: str


@dataclass(frozen=True)
class IncarnationConfig:
    id: str
    lifecycle: str
    entity_id: str
    label: str
    aliases: tuple[str, ...]
    primary_continuity_id: str
    continuity_memberships: tuple[IncarnationContinuityMembership, ...]


@dataclass(frozen=True)
class IncarnationBinding:
    id: str
    incarnation_id: str
    applicability_scope_id: str
    binding_type: str
    status: str


@dataclass(frozen=True)
class IncarnationRelationshipType:
    id: str
    label: str
    inverse_type: str
    symmetric: bool


@dataclass(frozen=True)
class IncarnationRelationship:
    id: str
    source_incarnation_id: str
    relationship_type: str
    target_incarnation_id: str
    status: str
    applicability_scope_id: str | None


@dataclass(frozen=True)
class EntityRegistry:
    path: Path
    schema_version: int
    entities: dict[str, EntityConfig]
    entity_relationship_types: dict[str, EntityRelationshipType]
    entity_relationships: tuple[EntityRelationship, ...]
    incarnations: dict[str, IncarnationConfig]
    incarnation_bindings: tuple[IncarnationBinding, ...]
    incarnation_relationship_types: dict[str, IncarnationRelationshipType]
    incarnation_relationships: tuple[IncarnationRelationship, ...]
    entity_aliases: dict[str, str]
    incarnation_aliases: dict[str, str]

    def resolve_entity_id(self, value: str) -> str | None:
        normalized = value.strip().casefold()
        for entity_id in self.entities:
            if entity_id.casefold() == normalized:
                return entity_id
        return self.entity_aliases.get(normalized)

    def resolve_incarnation_id(self, value: str) -> str | None:
        normalized = value.strip().casefold()
        for incarnation_id in self.incarnations:
            if incarnation_id.casefold() == normalized:
                return incarnation_id
        return self.incarnation_aliases.get(normalized)

    def incarnations_for_entity(self, entity_id: str) -> tuple[IncarnationConfig, ...]:
        if entity_id not in self.entities:
            raise ValueError(f"Unknown entity `{entity_id}`.")
        return tuple(
            incarnation
            for incarnation in self.incarnations.values()
            if incarnation.entity_id == entity_id
        )

    def relationships_for_entity(
        self, entity_id: str
    ) -> tuple[EntityRelationship, ...]:
        if entity_id not in self.entities:
            raise ValueError(f"Unknown entity `{entity_id}`.")
        return tuple(
            relationship
            for relationship in self.entity_relationships
            if entity_id
            in (relationship.source_entity_id, relationship.target_entity_id)
        )

    def bindings_for_incarnation(self, incarnation_id: str) -> tuple[IncarnationBinding, ...]:
        if incarnation_id not in self.incarnations:
            raise ValueError(f"Unknown incarnation `{incarnation_id}`.")
        return tuple(
            binding
            for binding in self.incarnation_bindings
            if binding.incarnation_id == incarnation_id
        )

    def relationships_for_incarnation(
        self, incarnation_id: str
    ) -> tuple[IncarnationRelationship, ...]:
        if incarnation_id not in self.incarnations:
            raise ValueError(f"Unknown incarnation `{incarnation_id}`.")
        return tuple(
            relationship
            for relationship in self.incarnation_relationships
            if incarnation_id
            in (
                relationship.source_incarnation_id,
                relationship.target_incarnation_id,
            )
        )

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        target_maps = {
            "entity": self.entities,
            "entity-relationship": {
                relationship.id: relationship
                for relationship in self.entity_relationships
            },
            "entity-incarnation": self.incarnations,
            "incarnation-binding": {
                binding.id: binding for binding in self.incarnation_bindings
            },
            "incarnation-relationship": {
                relationship.id: relationship
                for relationship in self.incarnation_relationships
            },
        }
        targets = target_maps.get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported entity-registry subject type `{subject_type}`.")
        if subject_id not in targets:
            raise ValueError(f"Unknown {subject_type} `{subject_id}`.")
        return targets[subject_id]


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Entity registry `{context}` must be a mapping.")
    return value


def require_list(value, context: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"Entity registry `{context}` must be a list.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Entity registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def optional_string(mapping: dict, key: str, context: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Entity registry `{context}.{key}` must be a non-empty string or null.")
    return value.strip()


def require_bool(mapping: dict, key: str, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Entity registry `{context}.{key}` must be true or false.")
    return value


def string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    raw = require_list(mapping.get(key), f"{context}.{key}")
    values: list[str] = []
    for index, value in enumerate(raw):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Entity registry `{context}.{key}[{index}]` must be a non-empty string."
            )
        values.append(value.strip())
    if len({value.casefold() for value in values}) != len(values):
        raise ValueError(f"Entity registry `{context}.{key}` contains duplicate values.")
    return tuple(values)


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Entity registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def validate_lifecycle(value: str, context: str) -> None:
    if value not in LIFECYCLES:
        raise ValueError(
            f"Entity registry `{context}` must be one of: {', '.join(sorted(LIFECYCLES))}."
        )


def validate_pack_value(
    packs: SchemaPackRegistry, namespace: str, value: str, context: str
) -> None:
    allowed = packs.allowed_values(namespace)
    if not allowed:
        raise ValueError(
            f"Selected schema packs do not provide controlled namespace `{namespace}`."
        )
    if value not in allowed:
        raise ValueError(
            f"Entity registry `{context}` value `{value}` is not supplied by selected schema packs."
        )


def build_aliases(records: dict[str, EntityConfig | IncarnationConfig], label: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    ids = {record_id.casefold(): record_id for record_id in records}
    for record in records.values():
        for alias in (record.label, *record.aliases):
            normalized = alias.casefold()
            if normalized in ids and ids[normalized] != record.id:
                raise ValueError(
                    f"Entity registry {label} alias `{alias}` conflicts with ID `{ids[normalized]}`."
                )
            owner = aliases.get(normalized)
            if owner is not None and owner != record.id:
                raise ValueError(
                    f"Entity registry {label} alias `{alias}` is shared by `{owner}` and `{record.id}`."
                )
            aliases[normalized] = record.id
    return aliases


def validate_relationship_type_inverses(
    relationship_types: dict[
        str, EntityRelationshipType | IncarnationRelationshipType
    ],
    label: str,
) -> None:
    for relationship_type in relationship_types.values():
        if relationship_type.inverse_type not in relationship_types:
            raise ValueError(
                f"Entity registry {label} relationship type "
                f"`{relationship_type.id}` references unknown inverse "
                f"`{relationship_type.inverse_type}`."
            )
        inverse = relationship_types[relationship_type.inverse_type]
        if inverse.inverse_type != relationship_type.id:
            raise ValueError(
                f"Entity registry {label} relationship types "
                f"`{relationship_type.id}` and `{inverse.id}` are not "
                "reciprocal inverses."
            )
        if relationship_type.symmetric != (
            relationship_type.id == relationship_type.inverse_type
        ):
            raise ValueError(
                f"Entity registry {label} relationship type "
                f"`{relationship_type.id}` has inconsistent symmetric and "
                "inverse settings."
            )


def canonical_relationship_shape(
    source_id: str,
    type_id: str,
    target_id: str,
    scope_id: str | None,
    relationship_types: dict[str, EntityRelationshipType],
) -> tuple[str, str, str, str | None]:
    relationship_type = relationship_types[type_id]
    if relationship_type.symmetric:
        return min(source_id, target_id), type_id, max(source_id, target_id), scope_id
    canonical_type = min(type_id, relationship_type.inverse_type)
    if type_id == canonical_type:
        return source_id, canonical_type, target_id, scope_id
    return target_id, canonical_type, source_id, scope_id


def load_entity_registry(
    project: ProjectConfig,
    taxonomy: TaxonomyConfig,
    sources: SourceRegistry,
    schema_packs: SchemaPackRegistry | None = None,
) -> EntityRegistry:
    if schema_packs is None:
        schema_packs = load_schema_pack_registry(project)
    if not schema_packs.capability_enabled("entity-incarnations"):
        raise ValueError(
            "Entity registry requires enabled schema capability `entity-incarnations`."
        )

    try:
        data = yaml.safe_load(project.entities_registry.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Unable to parse entity registry {project.entities_registry}: {exc}"
        ) from exc
    registry = require_mapping(data, "root")
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_ENTITY_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported entity schema_version {schema_version!r}; "
            f"expected {SUPPORTED_ENTITY_SCHEMA_VERSION}."
        )

    entities: dict[str, EntityConfig] = {}
    for entity_id, raw_entity in require_mapping(registry.get("entities"), "entities").items():
        validate_id(entity_id, f"entities.{entity_id}")
        context = f"entities.{entity_id}"
        entity = require_mapping(raw_entity, context)
        lifecycle = require_string(entity, "lifecycle", context)
        validate_lifecycle(lifecycle, f"{context}.lifecycle")
        primary_category_id = require_string(
            entity, "primary_category_id", context
        )
        category_ids = string_list(entity, "category_ids", context)
        if not category_ids:
            raise ValueError(
                f"Entity registry `{context}.category_ids` cannot be empty."
            )
        unknown_categories = set(category_ids) - set(taxonomy.categories)
        if unknown_categories:
            raise ValueError(
                f"Entity registry `{context}.category_ids` references unknown categories: "
                + ", ".join(sorted(unknown_categories))
                + "."
            )
        if primary_category_id not in category_ids:
            raise ValueError(
                f"Entity registry `{context}.primary_category_id` must appear in category_ids."
            )
        entities[entity_id] = EntityConfig(
            id=entity_id,
            lifecycle=lifecycle,
            primary_category_id=primary_category_id,
            category_ids=category_ids,
            label=require_string(entity, "label", context),
            aliases=string_list(entity, "aliases", context),
        )

    membership_statuses = set(schema_packs.allowed_values("source.membership-status"))
    if not membership_statuses:
        raise ValueError(
            "Selected schema packs do not provide controlled namespace `source.membership-status`."
        )

    entity_relationship_types: dict[str, EntityRelationshipType] = {}
    raw_entity_types = require_mapping(
        registry.get("entity_relationship_types"), "entity_relationship_types"
    )
    for type_id, raw_type in raw_entity_types.items():
        context = f"entity_relationship_types.{type_id}"
        validate_id(type_id, context)
        validate_pack_value(
            schema_packs, "narrative.entity-relationship-type", type_id, context
        )
        relationship_type = require_mapping(raw_type, context)
        entity_relationship_types[type_id] = EntityRelationshipType(
            id=type_id,
            label=require_string(relationship_type, "label", context),
            inverse_type=require_string(relationship_type, "inverse_type", context),
            symmetric=require_bool(relationship_type, "symmetric", context),
        )
    validate_relationship_type_inverses(
        entity_relationship_types, "entity"
    )

    entity_relationships: list[EntityRelationship] = []
    seen_entity_relationship_ids: set[str] = set()
    seen_entity_relationship_shapes: set[tuple[str, str, str, str | None]] = set()
    lineage_role_types = {"derived-from", "composite-of", "inspired-by"}
    for index, raw_relationship in enumerate(
        require_list(registry.get("entity_relationships"), "entity_relationships")
    ):
        context = f"entity_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_entity_relationship_ids:
            raise ValueError(
                f"Entity registry repeats entity relationship ID `{relationship_id}`."
            )
        seen_entity_relationship_ids.add(relationship_id)
        source_id = require_string(relationship, "source_entity_id", context)
        target_id = require_string(relationship, "target_entity_id", context)
        if source_id not in entities or target_id not in entities:
            raise ValueError(
                f"Entity registry `{context}` references an unknown entity endpoint."
            )
        if source_id == target_id:
            raise ValueError(
                f"Entity registry `{context}` cannot relate an entity to itself."
            )
        type_id = require_string(relationship, "relationship_type", context)
        if type_id not in entity_relationship_types:
            raise ValueError(
                f"Entity registry `{context}.relationship_type` references unknown type `{type_id}`."
            )
        status = require_string(relationship, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Entity registry `{context}.status` value `{status}` is not supplied by selected schema packs."
            )
        scope_id = optional_string(relationship, "applicability_scope_id", context)
        if scope_id is not None and scope_id not in sources.applicability_scopes:
            raise ValueError(
                f"Entity registry `{context}.applicability_scope_id` references unknown scope `{scope_id}`."
            )
        basis_roles = (
            string_list(relationship, "basis_roles", context)
            if "basis_roles" in relationship
            else ()
        )
        for basis_role in basis_roles:
            validate_pack_value(
                schema_packs,
                "narrative.entity-relationship-basis-role",
                basis_role,
                f"{context}.basis_roles",
            )
        if basis_roles and type_id not in lineage_role_types:
            raise ValueError(
                f"Entity registry `{context}.basis_roles` is only valid for "
                "derived-from, composite-of, or inspired-by relationships."
            )
        shape = canonical_relationship_shape(
            source_id,
            type_id,
            target_id,
            scope_id,
            entity_relationship_types,
        )
        if shape in seen_entity_relationship_shapes:
            raise ValueError(
                f"Entity registry `{context}` duplicates an entity relationship or its inverse."
            )
        seen_entity_relationship_shapes.add(shape)
        entity_relationships.append(
            EntityRelationship(
                relationship_id,
                source_id,
                type_id,
                target_id,
                status,
                scope_id,
                basis_roles,
            )
        )

    incarnations: dict[str, IncarnationConfig] = {}
    raw_incarnations = require_mapping(registry.get("incarnations"), "incarnations")
    for incarnation_id, raw_incarnation in raw_incarnations.items():
        validate_id(incarnation_id, f"incarnations.{incarnation_id}")
        context = f"incarnations.{incarnation_id}"
        incarnation = require_mapping(raw_incarnation, context)
        lifecycle = require_string(incarnation, "lifecycle", context)
        validate_lifecycle(lifecycle, f"{context}.lifecycle")
        entity_id = require_string(incarnation, "entity_id", context)
        if entity_id not in entities:
            raise ValueError(
                f"Entity registry `{context}.entity_id` references unknown entity `{entity_id}`."
            )
        primary_continuity_id = require_string(
            incarnation, "primary_continuity_id", context
        )
        if primary_continuity_id not in sources.continuities:
            raise ValueError(
                f"Entity registry `{context}.primary_continuity_id` references unknown continuity `{primary_continuity_id}`."
            )
        memberships: list[IncarnationContinuityMembership] = []
        seen_continuities: set[str] = set()
        for index, raw_membership in enumerate(
            require_list(incarnation.get("continuity_memberships"), f"{context}.continuity_memberships")
        ):
            membership_context = f"{context}.continuity_memberships[{index}]"
            membership = require_mapping(raw_membership, membership_context)
            continuity_id = require_string(membership, "continuity_id", membership_context)
            if continuity_id not in sources.continuities:
                raise ValueError(
                    f"Entity registry `{membership_context}.continuity_id` references unknown continuity `{continuity_id}`."
                )
            if continuity_id in seen_continuities:
                raise ValueError(
                    f"Entity registry `{context}.continuity_memberships` repeats `{continuity_id}`."
                )
            seen_continuities.add(continuity_id)
            status = require_string(membership, "status", membership_context)
            if status not in membership_statuses:
                raise ValueError(
                    f"Entity registry `{membership_context}.status` value `{status}` is not supplied by selected schema packs."
                )
            memberships.append(IncarnationContinuityMembership(continuity_id, status))
        if not memberships:
            raise ValueError(f"Entity registry `{context}.continuity_memberships` cannot be empty.")
        if primary_continuity_id not in seen_continuities:
            raise ValueError(
                f"Entity registry `{context}.primary_continuity_id` must appear in continuity_memberships."
            )
        incarnations[incarnation_id] = IncarnationConfig(
            id=incarnation_id,
            lifecycle=lifecycle,
            entity_id=entity_id,
            label=require_string(incarnation, "label", context),
            aliases=string_list(incarnation, "aliases", context),
            primary_continuity_id=primary_continuity_id,
            continuity_memberships=tuple(memberships),
        )

    bindings: list[IncarnationBinding] = []
    seen_binding_ids: set[str] = set()
    seen_binding_shapes: set[tuple[str, str, str]] = set()
    for index, raw_binding in enumerate(
        require_list(registry.get("incarnation_bindings"), "incarnation_bindings")
    ):
        context = f"incarnation_bindings[{index}]"
        binding = require_mapping(raw_binding, context)
        binding_id = require_string(binding, "id", context)
        validate_id(binding_id, f"{context}.id")
        if binding_id in seen_binding_ids:
            raise ValueError(f"Entity registry repeats binding ID `{binding_id}`.")
        seen_binding_ids.add(binding_id)
        incarnation_id = require_string(binding, "incarnation_id", context)
        if incarnation_id not in incarnations:
            raise ValueError(
                f"Entity registry `{context}.incarnation_id` references unknown incarnation `{incarnation_id}`."
            )
        scope_id = require_string(binding, "applicability_scope_id", context)
        if scope_id not in sources.applicability_scopes:
            raise ValueError(
                f"Entity registry `{context}.applicability_scope_id` references unknown scope `{scope_id}`."
            )
        binding_type = require_string(binding, "binding_type", context)
        validate_pack_value(
            schema_packs, "narrative.incarnation-binding-type", binding_type, f"{context}.binding_type"
        )
        status = require_string(binding, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Entity registry `{context}.status` value `{status}` is not supplied by selected schema packs."
            )
        shape = (incarnation_id, scope_id, binding_type)
        if shape in seen_binding_shapes:
            raise ValueError(f"Entity registry `{context}` duplicates an incarnation binding.")
        seen_binding_shapes.add(shape)
        bindings.append(IncarnationBinding(binding_id, incarnation_id, scope_id, binding_type, status))

    relationship_types: dict[str, IncarnationRelationshipType] = {}
    raw_types = require_mapping(
        registry.get("incarnation_relationship_types"), "incarnation_relationship_types"
    )
    for type_id, raw_type in raw_types.items():
        context = f"incarnation_relationship_types.{type_id}"
        validate_id(type_id, context)
        validate_pack_value(
            schema_packs, "narrative.incarnation-relationship-type", type_id, context
        )
        relationship_type = require_mapping(raw_type, context)
        relationship_types[type_id] = IncarnationRelationshipType(
            id=type_id,
            label=require_string(relationship_type, "label", context),
            inverse_type=require_string(relationship_type, "inverse_type", context),
            symmetric=require_bool(relationship_type, "symmetric", context),
        )
    validate_relationship_type_inverses(relationship_types, "incarnation")

    relationships: list[IncarnationRelationship] = []
    seen_relationship_ids: set[str] = set()
    seen_relationship_shapes: set[tuple[str, str, str, str | None]] = set()
    for index, raw_relationship in enumerate(
        require_list(registry.get("incarnation_relationships"), "incarnation_relationships")
    ):
        context = f"incarnation_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_relationship_ids:
            raise ValueError(f"Entity registry repeats relationship ID `{relationship_id}`.")
        seen_relationship_ids.add(relationship_id)
        source_id = require_string(relationship, "source_incarnation_id", context)
        target_id = require_string(relationship, "target_incarnation_id", context)
        if source_id not in incarnations or target_id not in incarnations:
            raise ValueError(
                f"Entity registry `{context}` references an unknown incarnation endpoint."
            )
        if source_id == target_id:
            raise ValueError(f"Entity registry `{context}` cannot relate an incarnation to itself.")
        type_id = require_string(relationship, "relationship_type", context)
        if type_id not in relationship_types:
            raise ValueError(
                f"Entity registry `{context}.relationship_type` references unknown type `{type_id}`."
            )
        status = require_string(relationship, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Entity registry `{context}.status` value `{status}` is not supplied by selected schema packs."
            )
        scope_id = optional_string(relationship, "applicability_scope_id", context)
        if scope_id is not None and scope_id not in sources.applicability_scopes:
            raise ValueError(
                f"Entity registry `{context}.applicability_scope_id` references unknown scope `{scope_id}`."
            )
        relationship_type = relationship_types[type_id]
        shape = (
            min(source_id, target_id) if relationship_type.symmetric else source_id,
            type_id,
            max(source_id, target_id) if relationship_type.symmetric else target_id,
            scope_id,
        )
        if shape in seen_relationship_shapes:
            raise ValueError(f"Entity registry `{context}` duplicates an incarnation relationship.")
        seen_relationship_shapes.add(shape)
        relationships.append(
            IncarnationRelationship(
                relationship_id, source_id, type_id, target_id, status, scope_id
            )
        )

    return EntityRegistry(
        path=project.entities_registry,
        schema_version=schema_version,
        entities=entities,
        entity_relationship_types=entity_relationship_types,
        entity_relationships=tuple(entity_relationships),
        incarnations=incarnations,
        incarnation_bindings=tuple(bindings),
        incarnation_relationship_types=relationship_types,
        incarnation_relationships=tuple(relationships),
        entity_aliases=build_aliases(entities, "entity"),
        incarnation_aliases=build_aliases(incarnations, "incarnation"),
    )
