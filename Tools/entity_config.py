from dataclasses import dataclass
from pathlib import Path
import re

from lookup_key_config import LookupKeyConfig, load_lookup_key_config
from project_config import ProjectConfig
from schema_pack_config import SchemaPackRegistry, load_schema_pack_registry
from source_config import SourceRegistry
from taxonomy_config import TaxonomyConfig
from strict_yaml import load_yaml_file


SUPPORTED_ENTITY_SCHEMA_VERSION = 4
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
    canonical_direction: bool
    acyclic_group: str | None


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
    canonical_direction: bool
    acyclic_group: str | None


@dataclass(frozen=True)
class IncarnationRelationship:
    id: str
    source_incarnation_id: str
    relationship_type: str
    target_incarnation_id: str
    status: str
    applicability_scope_id: str | None


@dataclass(frozen=True)
class IdentityPhase:
    id: str
    lifecycle: str
    subject_type: str
    subject_id: str
    continuity_id: str
    phase_type: str
    label: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class IdentityPhaseBinding:
    id: str
    identity_phase_id: str
    applicability_scope_id: str
    binding_type: str
    status: str


@dataclass(frozen=True)
class IdentityPhaseRelationshipType:
    id: str
    label: str
    inverse_type: str
    symmetric: bool
    canonical_direction: bool
    acyclic_group: str | None


@dataclass(frozen=True)
class IdentityPhaseRelationship:
    id: str
    source_identity_phase_id: str
    relationship_type: str
    target_identity_phase_id: str
    status: str


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
    identity_phases: dict[str, IdentityPhase]
    identity_phase_bindings: tuple[IdentityPhaseBinding, ...]
    identity_phase_relationship_types: dict[str, IdentityPhaseRelationshipType]
    identity_phase_relationships: tuple[IdentityPhaseRelationship, ...]
    lookup_keys: LookupKeyConfig
    entity_aliases: dict[str, tuple[str, ...]]
    incarnation_aliases: dict[str, tuple[str, ...]]
    identity_phase_aliases: dict[str, tuple[str, ...]]

    def resolve_entity_ids(self, value: str) -> tuple[str, ...]:
        normalized = self.lookup_keys.normalize(value)
        for entity_id in self.entities:
            if self.lookup_keys.normalize(entity_id) == normalized:
                return (entity_id,)
        return self.entity_aliases.get(normalized, ())

    def resolve_entity_id(self, value: str) -> str | None:
        matches = self.resolve_entity_ids(value)
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous entity name `{value}` matches: {', '.join(matches)}."
            )
        return matches[0] if matches else None

    def resolve_incarnation_ids(self, value: str) -> tuple[str, ...]:
        normalized = self.lookup_keys.normalize(value)
        for incarnation_id in self.incarnations:
            if self.lookup_keys.normalize(incarnation_id) == normalized:
                return (incarnation_id,)
        return self.incarnation_aliases.get(normalized, ())

    def resolve_incarnation_id(self, value: str) -> str | None:
        matches = self.resolve_incarnation_ids(value)
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous incarnation name `{value}` matches: {', '.join(matches)}."
            )
        return matches[0] if matches else None

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

    def phases_for_subject(
        self, subject_type: str, subject_id: str
    ) -> tuple[IdentityPhase, ...]:
        targets = self.identity_subject_targets().get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported identity subject type `{subject_type}`.")
        if subject_id not in targets:
            raise ValueError(f"Unknown {subject_type} `{subject_id}`.")
        return tuple(
            phase
            for phase in self.identity_phases.values()
            if phase.subject_type == subject_type and phase.subject_id == subject_id
        )

    def bindings_for_identity_phase(
        self, identity_phase_id: str
    ) -> tuple[IdentityPhaseBinding, ...]:
        if identity_phase_id not in self.identity_phases:
            raise ValueError(f"Unknown identity-phase `{identity_phase_id}`.")
        return tuple(
            binding
            for binding in self.identity_phase_bindings
            if binding.identity_phase_id == identity_phase_id
        )

    def relationships_for_identity_phase(
        self, identity_phase_id: str
    ) -> tuple[IdentityPhaseRelationship, ...]:
        if identity_phase_id not in self.identity_phases:
            raise ValueError(f"Unknown identity-phase `{identity_phase_id}`.")
        return tuple(
            relationship
            for relationship in self.identity_phase_relationships
            if identity_phase_id
            in (
                relationship.source_identity_phase_id,
                relationship.target_identity_phase_id,
            )
        )

    def resolve_identity_phase_ids(self, value: str) -> tuple[str, ...]:
        normalized = self.lookup_keys.normalize(value)
        for phase_id in self.identity_phases:
            if self.lookup_keys.normalize(phase_id) == normalized:
                return (phase_id,)
        return self.identity_phase_aliases.get(normalized, ())

    def resolve_identity_phase_id(self, value: str) -> str | None:
        matches = self.resolve_identity_phase_ids(value)
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous identity-phase name `{value}` matches: {', '.join(matches)}."
            )
        return matches[0] if matches else None

    def identity_subject_targets(self) -> dict[str, dict[str, object]]:
        return {
            "entity": self.entities,
            "entity-incarnation": self.incarnations,
        }

    def identity_subject_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.identity_subject_targets().get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported identity subject type `{subject_type}`.")
        if subject_id not in targets:
            raise ValueError(f"Unknown {subject_type} `{subject_id}`.")
        return targets[subject_id]

    def identity_targets(self) -> dict[str, dict[str, object]]:
        return {
            **self.identity_subject_targets(),
            "identity-phase": self.identity_phases,
        }

    def identity_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.identity_targets().get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported identity target type `{subject_type}`.")
        if subject_id not in targets:
            raise ValueError(f"Unknown {subject_type} `{subject_id}`.")
        return targets[subject_id]

    def reconciliation_targets(self) -> dict[str, dict[str, object]]:
        return self.identity_targets()

    def reconciliation_provider(self) -> dict[str, object]:
        return {
            "provider_id": "entity",
            "targets": self.reconciliation_targets(),
            "aliases": {
                "entity": dict(self.entity_aliases),
                "entity-incarnation": dict(self.incarnation_aliases),
                "identity-phase": dict(self.identity_phase_aliases),
            },
        }

    def reconciliation_target(self, target_type: str, target_id: str) -> object:
        return self.identity_target(target_type, target_id)

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {
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
            "identity-phase": self.identity_phases,
            "identity-phase-binding": {
                binding.id: binding for binding in self.identity_phase_bindings
            },
            "identity-phase-relationship": {
                relationship.id: relationship
                for relationship in self.identity_phase_relationships
            },
        }

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.provenance_targets().get(subject_type)
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
    if len(set(values)) != len(values):
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


def build_aliases(
    records: dict[str, EntityConfig | IncarnationConfig | IdentityPhase],
    label: str,
    lookup_keys: LookupKeyConfig,
) -> dict[str, tuple[str, ...]]:
    aliases: dict[str, list[str]] = {}
    ids = {lookup_keys.normalize(record_id): record_id for record_id in records}
    for record in records.values():
        record_alias_keys: set[str] = set()
        for alias in record.aliases:
            alias_key = lookup_keys.normalize(alias)
            if alias_key in record_alias_keys:
                raise ValueError(
                    f"Entity registry {label} `{record.id}` contains duplicate aliases."
                )
            record_alias_keys.add(alias_key)
        for alias in (record.label, *record.aliases):
            normalized = lookup_keys.normalize(alias)
            if normalized in ids and ids[normalized] != record.id:
                raise ValueError(
                    f"Entity registry {label} alias `{alias}` conflicts with ID `{ids[normalized]}`."
                )
            owners = aliases.setdefault(normalized, [])
            if record.id not in owners:
                owners.append(record.id)
    return {alias: tuple(owners) for alias, owners in aliases.items()}


def validate_relationship_type_inverses(
    relationship_types: dict[
        str,
        EntityRelationshipType
        | IncarnationRelationshipType
        | IdentityPhaseRelationshipType,
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
        if relationship_type.symmetric:
            if not relationship_type.canonical_direction:
                raise ValueError(
                    f"Entity registry {label} symmetric relationship type "
                    f"`{relationship_type.id}` must be its canonical direction."
                )
            if relationship_type.acyclic_group is not None:
                raise ValueError(
                    f"Entity registry {label} symmetric relationship type "
                    f"`{relationship_type.id}` cannot declare an acyclic group."
                )
        else:
            if relationship_type.canonical_direction == inverse.canonical_direction:
                raise ValueError(
                    f"Entity registry {label} relationship types "
                    f"`{relationship_type.id}` and `{inverse.id}` must declare "
                    "exactly one canonical direction."
                )
            if relationship_type.acyclic_group != inverse.acyclic_group:
                raise ValueError(
                    f"Entity registry {label} relationship types "
                    f"`{relationship_type.id}` and `{inverse.id}` must use the "
                    "same acyclic group."
                )


def canonical_relationship_shape(
    source_id: str,
    type_id: str,
    target_id: str,
    scope_id: str | None,
    relationship_types: dict[
        str,
        EntityRelationshipType
        | IncarnationRelationshipType
        | IdentityPhaseRelationshipType,
    ],
) -> tuple[str, str, str, str | None]:
    relationship_type = relationship_types[type_id]
    if relationship_type.symmetric:
        return min(source_id, target_id), type_id, max(source_id, target_id), scope_id
    if relationship_type.canonical_direction:
        return source_id, type_id, target_id, scope_id
    return target_id, relationship_type.inverse_type, source_id, scope_id


def validate_acyclic_relationships(
    relationships: list[
        EntityRelationship | IncarnationRelationship | IdentityPhaseRelationship
    ],
    relationship_types: dict[
        str,
        EntityRelationshipType
        | IncarnationRelationshipType
        | IdentityPhaseRelationshipType,
    ],
    label: str,
) -> None:
    normalized: list[tuple[str, str, str, str | None]] = []
    for relationship in relationships:
        source_id = (
            getattr(relationship, "source_entity_id", None)
            or getattr(relationship, "source_incarnation_id", None)
            or getattr(relationship, "source_identity_phase_id")
        )
        target_id = (
            getattr(relationship, "target_entity_id", None)
            or getattr(relationship, "target_incarnation_id", None)
            or getattr(relationship, "target_identity_phase_id")
        )
        relationship_type = relationship_types[relationship.relationship_type]
        if relationship_type.acyclic_group is None:
            continue
        canonical = canonical_relationship_shape(
            source_id,
            relationship.relationship_type,
            target_id,
            getattr(relationship, "applicability_scope_id", None),
            relationship_types,
        )
        normalized.append(
            (relationship_type.acyclic_group, canonical[0], canonical[2], canonical[3])
        )

    for group in sorted({entry[0] for entry in normalized}):
        group_edges = [entry for entry in normalized if entry[0] == group]
        scope_ids = sorted({entry[3] for entry in group_edges if entry[3] is not None})
        for scope_id in (None, *scope_ids):
            edges = [
                (source_id, target_id)
                for _, source_id, target_id, edge_scope_id in group_edges
                if edge_scope_id is None or edge_scope_id == scope_id
            ]
            adjacency: dict[str, set[str]] = {}
            indegree: dict[str, int] = {}
            for source_id, target_id in edges:
                indegree.setdefault(source_id, 0)
                indegree.setdefault(target_id, 0)
                targets = adjacency.setdefault(source_id, set())
                if target_id not in targets:
                    targets.add(target_id)
                    indegree[target_id] += 1
            queue = [node_id for node_id, degree in indegree.items() if degree == 0]
            processed = 0
            while queue:
                node_id = queue.pop()
                processed += 1
                for target_id in adjacency.get(node_id, ()):
                    indegree[target_id] -= 1
                    if indegree[target_id] == 0:
                        queue.append(target_id)
            if processed != len(indegree):
                scope_label = scope_id or "unscoped relationships"
                raise ValueError(
                    f"Entity registry contains a cycle among {label} relationships "
                    f"in acyclic group `{group}` for `{scope_label}`."
                )


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
    lookup_keys = load_lookup_key_config(project)

    data = load_yaml_file(project.entities_registry, "entity registry", expected_schema_version=SUPPORTED_ENTITY_SCHEMA_VERSION)
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
        acyclic_group = optional_string(
            relationship_type, "acyclic_group", context
        )
        if acyclic_group is not None:
            validate_id(acyclic_group, f"{context}.acyclic_group")
        entity_relationship_types[type_id] = EntityRelationshipType(
            id=type_id,
            label=require_string(relationship_type, "label", context),
            inverse_type=require_string(relationship_type, "inverse_type", context),
            symmetric=require_bool(relationship_type, "symmetric", context),
            canonical_direction=require_bool(
                relationship_type, "canonical_direction", context
            ),
            acyclic_group=acyclic_group,
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
    validate_acyclic_relationships(
        entity_relationships, entity_relationship_types, "entity"
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
        acyclic_group = optional_string(
            relationship_type, "acyclic_group", context
        )
        if acyclic_group is not None:
            validate_id(acyclic_group, f"{context}.acyclic_group")
        relationship_types[type_id] = IncarnationRelationshipType(
            id=type_id,
            label=require_string(relationship_type, "label", context),
            inverse_type=require_string(relationship_type, "inverse_type", context),
            symmetric=require_bool(relationship_type, "symmetric", context),
            canonical_direction=require_bool(
                relationship_type, "canonical_direction", context
            ),
            acyclic_group=acyclic_group,
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
        shape = canonical_relationship_shape(
            source_id,
            type_id,
            target_id,
            scope_id,
            relationship_types,
        )
        if shape in seen_relationship_shapes:
            raise ValueError(
                f"Entity registry `{context}` duplicates an incarnation relationship or its inverse."
            )
        seen_relationship_shapes.add(shape)
        relationships.append(
            IncarnationRelationship(
                relationship_id, source_id, type_id, target_id, status, scope_id
            )
        )
    validate_acyclic_relationships(
        relationships, relationship_types, "incarnation"
    )

    if not schema_packs.capability_enabled("entity-identity-phases"):
        raise ValueError(
            "Entity registry schema 4 requires enabled schema capability "
            "`entity-identity-phases`."
        )

    identity_phases: dict[str, IdentityPhase] = {}
    raw_identity_phases = require_mapping(
        registry.get("identity_phases"), "identity_phases"
    )
    identity_subject_targets: dict[str, dict[str, object]] = {
        "entity": entities,
        "entity-incarnation": incarnations,
    }
    for phase_id, raw_phase in raw_identity_phases.items():
        validate_id(phase_id, f"identity_phases.{phase_id}")
        context = f"identity_phases.{phase_id}"
        phase = require_mapping(raw_phase, context)
        lifecycle = require_string(phase, "lifecycle", context)
        validate_lifecycle(lifecycle, f"{context}.lifecycle")
        subject_type = require_string(phase, "subject_type", context)
        validate_pack_value(
            schema_packs,
            "identity.phase-subject-type",
            subject_type,
            f"{context}.subject_type",
        )
        if subject_type not in identity_subject_targets:
            raise ValueError(
                f"Entity registry `{context}.subject_type` has no installed identity provider."
            )
        subject_id = require_string(phase, "subject_id", context)
        if subject_id not in identity_subject_targets[subject_type]:
            raise ValueError(
                f"Entity registry `{context}.subject_id` references unknown "
                f"{subject_type} `{subject_id}`."
            )
        continuity_id = require_string(phase, "continuity_id", context)
        if continuity_id not in sources.continuities:
            raise ValueError(
                f"Entity registry `{context}.continuity_id` references unknown "
                f"continuity `{continuity_id}`."
            )
        if subject_type == "entity-incarnation":
            membership_ids = {
                membership.continuity_id
                for membership in incarnations[subject_id].continuity_memberships
            }
            if continuity_id not in membership_ids:
                raise ValueError(
                    f"Entity registry `{context}.continuity_id` is not a continuity "
                    f"membership of incarnation `{subject_id}`."
                )
        phase_type = require_string(phase, "phase_type", context)
        validate_pack_value(
            schema_packs,
            "identity.phase-type",
            phase_type,
            f"{context}.phase_type",
        )
        identity_phases[phase_id] = IdentityPhase(
            id=phase_id,
            lifecycle=lifecycle,
            subject_type=subject_type,
            subject_id=subject_id,
            continuity_id=continuity_id,
            phase_type=phase_type,
            label=require_string(phase, "label", context),
            aliases=string_list(phase, "aliases", context),
        )

    phase_bindings: list[IdentityPhaseBinding] = []
    seen_phase_binding_ids: set[str] = set()
    seen_phase_binding_shapes: set[tuple[str, str, str]] = set()
    for index, raw_binding in enumerate(
        require_list(
            registry.get("identity_phase_bindings"), "identity_phase_bindings"
        )
    ):
        context = f"identity_phase_bindings[{index}]"
        binding = require_mapping(raw_binding, context)
        binding_id = require_string(binding, "id", context)
        validate_id(binding_id, f"{context}.id")
        if binding_id in seen_phase_binding_ids:
            raise ValueError(
                f"Entity registry repeats identity-phase binding ID `{binding_id}`."
            )
        seen_phase_binding_ids.add(binding_id)
        phase_id = require_string(binding, "identity_phase_id", context)
        if phase_id not in identity_phases:
            raise ValueError(
                f"Entity registry `{context}.identity_phase_id` references unknown "
                f"identity phase `{phase_id}`."
            )
        scope_id = require_string(binding, "applicability_scope_id", context)
        if scope_id not in sources.applicability_scopes:
            raise ValueError(
                f"Entity registry `{context}.applicability_scope_id` references "
                f"unknown scope `{scope_id}`."
            )
        scope = sources.applicability_scopes[scope_id]
        work_ids = sources.target_work_ids(scope.target_type, scope.target_id)
        if not work_ids:
            raise ValueError(
                f"Entity registry `{context}.applicability_scope_id` must resolve "
                "to source material with a canonical work."
            )
        phase_continuity_id = identity_phases[phase_id].continuity_id
        if any(
            phase_continuity_id
            not in {
                membership.continuity_id
                for membership in sources.works[work_id].continuity_memberships
            }
            for work_id in work_ids
        ):
            raise ValueError(
                f"Entity registry `{context}.applicability_scope_id` resolves "
                f"outside phase continuity `{phase_continuity_id}`."
            )
        binding_type = require_string(binding, "binding_type", context)
        validate_pack_value(
            schema_packs,
            "identity.phase-binding-type",
            binding_type,
            f"{context}.binding_type",
        )
        status = require_string(binding, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Entity registry `{context}.status` value `{status}` is not "
                "supplied by selected schema packs."
            )
        shape = (phase_id, scope_id, binding_type)
        if shape in seen_phase_binding_shapes:
            raise ValueError(
                f"Entity registry `{context}` duplicates an identity-phase binding."
            )
        seen_phase_binding_shapes.add(shape)
        phase_bindings.append(
            IdentityPhaseBinding(
                binding_id, phase_id, scope_id, binding_type, status
            )
        )

    phase_relationship_types: dict[str, IdentityPhaseRelationshipType] = {}
    for type_id, raw_type in require_mapping(
        registry.get("identity_phase_relationship_types"),
        "identity_phase_relationship_types",
    ).items():
        context = f"identity_phase_relationship_types.{type_id}"
        validate_id(type_id, context)
        validate_pack_value(
            schema_packs, "identity.phase-relationship-type", type_id, context
        )
        relationship_type = require_mapping(raw_type, context)
        acyclic_group = optional_string(
            relationship_type, "acyclic_group", context
        )
        if acyclic_group is not None:
            validate_id(acyclic_group, f"{context}.acyclic_group")
        phase_relationship_types[type_id] = IdentityPhaseRelationshipType(
            id=type_id,
            label=require_string(relationship_type, "label", context),
            inverse_type=require_string(
                relationship_type, "inverse_type", context
            ),
            symmetric=require_bool(relationship_type, "symmetric", context),
            canonical_direction=require_bool(
                relationship_type, "canonical_direction", context
            ),
            acyclic_group=acyclic_group,
        )
    validate_relationship_type_inverses(
        phase_relationship_types, "identity-phase"
    )

    phase_relationships: list[IdentityPhaseRelationship] = []
    seen_phase_relationship_ids: set[str] = set()
    seen_phase_relationship_shapes: set[tuple[str, str, str, str | None]] = set()
    for index, raw_relationship in enumerate(
        require_list(
            registry.get("identity_phase_relationships"),
            "identity_phase_relationships",
        )
    ):
        context = f"identity_phase_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_phase_relationship_ids:
            raise ValueError(
                f"Entity registry repeats identity-phase relationship ID "
                f"`{relationship_id}`."
            )
        seen_phase_relationship_ids.add(relationship_id)
        source_id = require_string(
            relationship, "source_identity_phase_id", context
        )
        target_id = require_string(
            relationship, "target_identity_phase_id", context
        )
        if source_id not in identity_phases or target_id not in identity_phases:
            raise ValueError(
                f"Entity registry `{context}` references an unknown identity-phase endpoint."
            )
        if source_id == target_id:
            raise ValueError(
                f"Entity registry `{context}` cannot relate an identity phase to itself."
            )
        source_phase = identity_phases[source_id]
        target_phase = identity_phases[target_id]
        if (
            source_phase.subject_type,
            source_phase.subject_id,
            source_phase.continuity_id,
        ) != (
            target_phase.subject_type,
            target_phase.subject_id,
            target_phase.continuity_id,
        ):
            raise ValueError(
                f"Entity registry `{context}` must relate phases of the same "
                "identity subject and continuity."
            )
        type_id = require_string(relationship, "relationship_type", context)
        if type_id not in phase_relationship_types:
            raise ValueError(
                f"Entity registry `{context}.relationship_type` references "
                f"unknown type `{type_id}`."
            )
        status = require_string(relationship, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Entity registry `{context}.status` value `{status}` is not "
                "supplied by selected schema packs."
            )
        shape = canonical_relationship_shape(
            source_id, type_id, target_id, None, phase_relationship_types
        )
        if shape in seen_phase_relationship_shapes:
            raise ValueError(
                f"Entity registry `{context}` duplicates an identity-phase "
                "relationship or its inverse."
            )
        seen_phase_relationship_shapes.add(shape)
        phase_relationships.append(
            IdentityPhaseRelationship(
                relationship_id, source_id, type_id, target_id, status
            )
        )
    validate_acyclic_relationships(
        phase_relationships, phase_relationship_types, "identity-phase"
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
        identity_phases=identity_phases,
        identity_phase_bindings=tuple(phase_bindings),
        identity_phase_relationship_types=phase_relationship_types,
        identity_phase_relationships=tuple(phase_relationships),
        lookup_keys=lookup_keys,
        entity_aliases=build_aliases(entities, "entity", lookup_keys),
        incarnation_aliases=build_aliases(incarnations, "incarnation", lookup_keys),
        identity_phase_aliases=build_aliases(
            identity_phases, "identity phase", lookup_keys
        ),
    )
