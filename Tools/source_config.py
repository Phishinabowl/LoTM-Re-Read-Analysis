from dataclasses import dataclass
from pathlib import Path
from string import Formatter
import re

import yaml

from project_config import ProjectConfig
from resource_config import ResourceConfig
from schema_pack_config import SchemaPackRegistry, load_schema_pack_registry


SUPPORTED_SOURCE_SCHEMA_VERSION = 3
LIFECYCLES = {"active", "deferred"}
POSITION_FIELD_TYPES = {"string", "integer", "number", "timestamp", "boolean"}
PRIORITY_ORDERS = {"ascending", "descending"}
CONFLICT_BEHAVIORS = {"flag"}
DEVIATION_OWNERS = {"derivative-work"}
CHAPTER_NUMBERING_MODES = {"work-local", "series-global", "not-applicable"}
VOLUME_CATALOG_STATUSES = {"verified", "pending-verification", "not-applicable"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class RelationshipTypeConfig:
    id: str
    label: str
    inverse_type: str
    symmetric: bool


@dataclass(frozen=True)
class WorkGroupTypeConfig:
    id: str
    label: str
    ordered: bool


@dataclass(frozen=True)
class WorkGroupConfig:
    id: str
    lifecycle: str
    label: str
    short_label: str
    group_type: str
    parent_group_id: str | None


@dataclass(frozen=True)
class ContinuityConfig:
    id: str
    lifecycle: str
    label: str
    short_label: str
    continuity_type: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ContinuityRelationship:
    id: str
    source_continuity_id: str
    relationship_type: str
    target_continuity_id: str
    status: str


@dataclass(frozen=True)
class AuthorityProfile:
    id: str
    lifecycle: str
    label: str
    continuity_order: tuple[str, ...]
    accepted_membership_statuses: tuple[str, ...]
    source_priority_order: str
    comparison_work_relationship_types: tuple[str, ...]
    cross_source_conflict: str
    derivative_deviation_owner: str
    preserve_source_scoped_claims: bool


@dataclass(frozen=True)
class CitationFormat:
    id: str
    template: str
    required_fields: tuple[str, ...]


@dataclass(frozen=True)
class RegistryValueConfig:
    id: str
    label: str


@dataclass(frozen=True)
class CulturalFormConfig:
    id: str
    label: str
    modality_id: str


@dataclass(frozen=True)
class MediumConfig:
    id: str
    lifecycle: str
    label: str
    plural_label: str
    modality_ids: tuple[str, ...]
    cultural_form_ids: tuple[str, ...]
    fields: dict[str, str]
    required_fields: tuple[str, ...]
    sort_fields: tuple[str, ...]
    citation_formats: tuple[CitationFormat, ...]


@dataclass(frozen=True)
class WorkGroupMembership:
    group_id: str
    role: str
    ordinal: int | None


@dataclass(frozen=True)
class ContinuityMembership:
    continuity_id: str
    status: str


@dataclass(frozen=True)
class VolumeConfig:
    id: str
    number: int
    label: str
    chapter_start: int
    chapter_end: int


@dataclass(frozen=True)
class WorkConfig:
    id: str
    lifecycle: str
    label: str
    short_label: str
    work_type: str
    medium_id: str
    release_form_id: str
    work_status: str
    aliases: tuple[str, ...]
    group_memberships: tuple[WorkGroupMembership, ...]
    continuity_memberships: tuple[ContinuityMembership, ...]
    chapter_numbering: str
    volume_catalog_status: str
    volumes: tuple[VolumeConfig, ...]


@dataclass(frozen=True)
class WorkRelationship:
    id: str
    source_work_id: str
    relationship_type: str
    target_work_id: str
    continuity_ids: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class SegmentConfig:
    id: str
    work_id: str
    parent_segment_id: str | None
    segment_type: str
    label: str
    ordinal: int | None


@dataclass(frozen=True)
class OrderingEntry:
    target_type: str
    target_id: str
    ordinal: int


@dataclass(frozen=True)
class OrderingScheme:
    id: str
    label: str
    ordering_type: str
    entries: tuple[OrderingEntry, ...]


@dataclass(frozen=True)
class AdaptationMapping:
    id: str
    source_work_id: str
    target_work_id: str
    source_segment_ids: tuple[str, ...]
    target_segment_ids: tuple[str, ...]
    mapping_type: str
    status: str


@dataclass(frozen=True)
class SourceResourceBinding:
    resource_type_id: str
    root_id: str
    relative_path: Path
    path: Path
    required: bool


@dataclass(frozen=True)
class SourceConfig:
    id: str
    lifecycle: str
    label: str
    work_id: str
    medium_id: str
    container_format_ids: tuple[str, ...]
    role: str
    comparison_group: str
    priority: int
    aliases: tuple[str, ...]
    evidence_modes: tuple[str, ...]
    resource_bindings: tuple[SourceResourceBinding, ...]


@dataclass(frozen=True)
class SourceRelationship:
    id: str
    source_source_id: str
    relationship_type: str
    target_source_id: str


@dataclass(frozen=True)
class SourceRegistry:
    path: Path
    schema_version: int
    default_authority_profile_id: str
    media_modalities: dict[str, RegistryValueConfig]
    cultural_forms: dict[str, CulturalFormConfig]
    release_forms: dict[str, RegistryValueConfig]
    container_formats: dict[str, RegistryValueConfig]
    mediums: dict[str, MediumConfig]
    work_group_types: dict[str, WorkGroupTypeConfig]
    work_groups: dict[str, WorkGroupConfig]
    continuities: dict[str, ContinuityConfig]
    continuity_relationship_types: dict[str, RelationshipTypeConfig]
    continuity_relationships: tuple[ContinuityRelationship, ...]
    authority_profiles: dict[str, AuthorityProfile]
    work_relationship_types: dict[str, RelationshipTypeConfig]
    works: dict[str, WorkConfig]
    segments: dict[str, SegmentConfig]
    ordering_schemes: dict[str, OrderingScheme]
    work_relationships: tuple[WorkRelationship, ...]
    adaptation_mappings: tuple[AdaptationMapping, ...]
    work_aliases: dict[str, str]
    source_relationship_types: dict[str, RelationshipTypeConfig]
    sources: dict[str, SourceConfig]
    source_relationships: tuple[SourceRelationship, ...]
    source_aliases: dict[str, str]

    def resolve_source_id(self, value: str) -> str | None:
        normalized = value.strip().casefold()
        if normalized in {source_id.casefold() for source_id in self.sources}:
            return next(
                source_id
                for source_id in self.sources
                if source_id.casefold() == normalized
            )
        return self.source_aliases.get(normalized)

    def resolve_work_id(self, value: str) -> str | None:
        normalized = value.strip().casefold()
        for work_id in self.works:
            if work_id.casefold() == normalized:
                return work_id
        return self.work_aliases.get(normalized)


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Source registry `{context}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Source registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def require_bool(mapping: dict, key: str, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Source registry `{context}.{key}` must be true or false.")
    return value


def require_string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"Source registry `{context}.{key}` must be a list of strings.")
    return tuple(item.strip() for item in value)


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Source registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def validate_field_id(value: str, context: str) -> None:
    if not FIELD_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Source registry `{context}` must be a lowercase snake_case field ID: {value}"
        )


def validate_pack_values(
    schema_packs: SchemaPackRegistry,
    namespace: str,
    values,
    context: str,
) -> None:
    allowed = set(schema_packs.allowed_values(namespace))
    if not allowed:
        raise ValueError(
            f"Selected schema packs do not provide controlled namespace "
            f"`{namespace}` required by `{context}`."
        )
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(
            f"Source registry `{context}` uses value(s) not provided by the selected "
            f"schema packs in `{namespace}`: {', '.join(sorted(unknown))}."
        )


def parse_lifecycle(mapping: dict, context: str) -> str:
    lifecycle = require_string(mapping, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        raise ValueError(
            f"Source registry `{context}.lifecycle` must be one of: "
            f"{', '.join(sorted(LIFECYCLES))}."
        )
    return lifecycle


def parse_labeled_registry(raw_value, context: str) -> dict[str, RegistryValueConfig]:
    raw_registry = require_mapping(raw_value, context)
    parsed: dict[str, RegistryValueConfig] = {}
    for value_id, raw_definition in raw_registry.items():
        value_context = f"{context}.{value_id}"
        validate_id(value_id, value_context)
        definition = require_mapping(raw_definition, value_context)
        parsed[value_id] = RegistryValueConfig(
            id=value_id,
            label=require_string(definition, "label", value_context),
        )
    if not parsed:
        raise ValueError(f"Source registry `{context}` must not be empty.")
    return parsed


def parse_relationship_types(raw_value, context: str) -> dict[str, RelationshipTypeConfig]:
    raw_types = require_mapping(raw_value, context)
    parsed: dict[str, RelationshipTypeConfig] = {}
    for type_id, raw_type in raw_types.items():
        type_context = f"{context}.{type_id}"
        validate_id(type_id, type_context)
        value = require_mapping(raw_type, type_context)
        inverse_type = require_string(value, "inverse_type", type_context)
        validate_id(inverse_type, f"{type_context}.inverse_type")
        parsed[type_id] = RelationshipTypeConfig(
            id=type_id,
            label=require_string(value, "label", type_context),
            inverse_type=inverse_type,
            symmetric=require_bool(value, "symmetric", type_context),
        )
    for relation_type in parsed.values():
        inverse = parsed.get(relation_type.inverse_type)
        if inverse is None:
            raise ValueError(
                f"Source registry `{context}.{relation_type.id}.inverse_type` "
                f"references unknown type `{relation_type.inverse_type}`."
            )
        if inverse.inverse_type != relation_type.id:
            raise ValueError(
                f"Source registry relationship types `{relation_type.id}` and "
                f"`{inverse.id}` do not define reciprocal inverses."
            )
        if relation_type.symmetric != (relation_type.id == relation_type.inverse_type):
            raise ValueError(
                f"Source registry relationship type `{relation_type.id}` has "
                "inconsistent symmetric and inverse settings."
            )
    return parsed


def parse_work(
    work_id: str,
    raw_work,
    *,
    work_groups: dict[str, WorkGroupConfig],
    work_group_types: dict[str, WorkGroupTypeConfig],
    continuities: dict[str, ContinuityConfig],
    mediums: dict[str, MediumConfig],
    release_forms: dict[str, RegistryValueConfig],
    membership_statuses: set[str],
) -> WorkConfig:
    context = f"works.{work_id}"
    validate_id(work_id, context)
    work = require_mapping(raw_work, context)
    lifecycle = parse_lifecycle(work, context)
    medium_id = require_string(work, "medium_id", context)
    if medium_id not in mediums:
        raise ValueError(
            f"Source registry `{context}.medium_id` references unknown medium "
            f"`{medium_id}`."
        )
    work_type = require_string(work, "work_type", context)
    validate_id(work_type, f"{context}.work_type")
    release_form_id = require_string(work, "release_form_id", context)
    if release_form_id not in release_forms:
        raise ValueError(
            f"Source registry `{context}.release_form_id` references unknown release "
            f"form `{release_form_id}`."
        )
    work_status = require_string(work, "work_status", context)
    validate_id(work_status, f"{context}.work_status")
    chapter_numbering = require_string(work, "chapter_numbering", context)
    if chapter_numbering not in CHAPTER_NUMBERING_MODES:
        raise ValueError(
            f"Source registry `{context}.chapter_numbering` must be one of: "
            f"{', '.join(sorted(CHAPTER_NUMBERING_MODES))}."
        )
    volume_status = require_string(work, "volume_catalog_status", context)
    if volume_status not in VOLUME_CATALOG_STATUSES:
        raise ValueError(
            f"Source registry `{context}.volume_catalog_status` must be one of: "
            f"{', '.join(sorted(VOLUME_CATALOG_STATUSES))}."
        )
    aliases = require_string_list(work, "aliases", context)
    for alias in aliases:
        validate_id(alias, f"{context}.aliases")
    raw_group_memberships = work.get("group_memberships")
    if not isinstance(raw_group_memberships, list) or not raw_group_memberships:
        raise ValueError(
            f"Source registry `{context}.group_memberships` must be a non-empty list."
        )
    group_memberships: list[WorkGroupMembership] = []
    seen_groups: set[str] = set()
    for index, raw_membership in enumerate(raw_group_memberships):
        membership_context = f"{context}.group_memberships[{index}]"
        membership = require_mapping(raw_membership, membership_context)
        group_id = require_string(membership, "group_id", membership_context)
        if group_id not in work_groups:
            raise ValueError(
                f"Source registry `{membership_context}.group_id` references "
                f"unknown work group `{group_id}`."
            )
        if group_id in seen_groups:
            raise ValueError(
                f"Source registry `{context}` repeats work group `{group_id}`."
            )
        seen_groups.add(group_id)
        role = require_string(membership, "role", membership_context)
        validate_id(role, f"{membership_context}.role")
        ordinal = membership.get("ordinal")
        ordered = work_group_types[work_groups[group_id].group_type].ordered
        if ordered:
            if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
                raise ValueError(
                    f"Source registry `{membership_context}.ordinal` must be a "
                    "positive integer for an ordered work group."
                )
        elif ordinal is not None:
            raise ValueError(
                f"Source registry `{membership_context}.ordinal` is only valid for "
                "ordered work groups."
            )
        group_memberships.append(WorkGroupMembership(group_id, role, ordinal))

    raw_continuity_memberships = work.get("continuity_memberships")
    if not isinstance(raw_continuity_memberships, list) or not raw_continuity_memberships:
        raise ValueError(
            f"Source registry `{context}.continuity_memberships` must be a "
            "non-empty list."
        )
    continuity_memberships: list[ContinuityMembership] = []
    seen_continuities: set[str] = set()
    for index, raw_membership in enumerate(raw_continuity_memberships):
        membership_context = f"{context}.continuity_memberships[{index}]"
        membership = require_mapping(raw_membership, membership_context)
        continuity_id = require_string(membership, "continuity_id", membership_context)
        if continuity_id not in continuities:
            raise ValueError(
                f"Source registry `{membership_context}.continuity_id` references "
                f"unknown continuity `{continuity_id}`."
            )
        if continuity_id in seen_continuities:
            raise ValueError(
                f"Source registry `{context}` repeats continuity `{continuity_id}`."
            )
        seen_continuities.add(continuity_id)
        status = require_string(membership, "status", membership_context)
        if status not in membership_statuses:
            raise ValueError(
                f"Source registry `{membership_context}.status` must be one of: "
                f"{', '.join(sorted(membership_statuses))}."
            )
        continuity_memberships.append(ContinuityMembership(continuity_id, status))

    if "volumes" not in work or not isinstance(work.get("volumes"), list):
        raise ValueError(f"Source registry `{context}.volumes` must be a list.")
    raw_volumes = work["volumes"]
    if volume_status == "verified" and not raw_volumes:
        raise ValueError(
            f"Source registry verified work `{work_id}` requires volume records."
        )
    volumes: list[VolumeConfig] = []
    volume_ids: set[str] = set()
    volume_numbers: set[int] = set()
    for index, raw_volume in enumerate(raw_volumes):
        volume_context = f"{context}.volumes[{index}]"
        volume = require_mapping(raw_volume, volume_context)
        volume_id = require_string(volume, "id", volume_context)
        validate_id(volume_id, f"{volume_context}.id")
        if volume_id in volume_ids:
            raise ValueError(
                f"Source registry `{volume_context}.id` duplicates `{volume_id}`."
            )
        volume_ids.add(volume_id)
        number = volume.get("number")
        chapter_start = volume.get("chapter_start")
        chapter_end = volume.get("chapter_end")
        for field_name, value in (
            ("number", number),
            ("chapter_start", chapter_start),
            ("chapter_end", chapter_end),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(
                    f"Source registry `{volume_context}.{field_name}` must be a "
                    "positive integer."
                )
        if number in volume_numbers:
            raise ValueError(
                f"Source registry `{context}` duplicates volume number {number}."
            )
        volume_numbers.add(number)
        if chapter_end < chapter_start:
            raise ValueError(
                f"Source registry `{volume_context}` chapter range is reversed."
            )
        volumes.append(
            VolumeConfig(
                id=volume_id,
                number=number,
                label=require_string(volume, "label", volume_context),
                chapter_start=chapter_start,
                chapter_end=chapter_end,
            )
        )
    sorted_volumes = sorted(volumes, key=lambda volume: volume.number)
    if volume_status == "verified":
        for expected_number, volume in enumerate(sorted_volumes, start=1):
            if volume.number != expected_number:
                raise ValueError(
                    f"Source registry `{context}` verified volume numbers must be "
                    "contiguous from 1."
                )
        for previous, current in zip(sorted_volumes, sorted_volumes[1:]):
            if current.chapter_start != previous.chapter_end + 1:
                raise ValueError(
                    f"Source registry `{context}` verified chapter ranges must be "
                    "contiguous and non-overlapping."
                )
    return WorkConfig(
        id=work_id,
        lifecycle=lifecycle,
        label=require_string(work, "label", context),
        short_label=require_string(work, "short_label", context),
        work_type=work_type,
        medium_id=medium_id,
        release_form_id=release_form_id,
        work_status=work_status,
        aliases=aliases,
        group_memberships=tuple(group_memberships),
        continuity_memberships=tuple(continuity_memberships),
        chapter_numbering=chapter_numbering,
        volume_catalog_status=volume_status,
        volumes=tuple(sorted_volumes),
    )


def parse_medium(
    medium_id: str,
    raw_medium,
    *,
    media_modalities: dict[str, RegistryValueConfig],
    cultural_forms: dict[str, CulturalFormConfig],
) -> MediumConfig:
    context = f"mediums.{medium_id}"
    validate_id(medium_id, context)
    medium = require_mapping(raw_medium, context)
    lifecycle = require_string(medium, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        raise ValueError(
            f"Source registry `{context}.lifecycle` must be one of: "
            f"{', '.join(sorted(LIFECYCLES))}."
        )
    modality_ids = require_string_list(medium, "modality_ids", context)
    if not modality_ids:
        raise ValueError(
            f"Source registry `{context}.modality_ids` must not be empty."
        )
    unknown_modalities = set(modality_ids) - set(media_modalities)
    if unknown_modalities:
        raise ValueError(
            f"Source registry `{context}.modality_ids` references unknown media "
            f"modalities: {', '.join(sorted(unknown_modalities))}."
        )
    cultural_form_ids = require_string_list(medium, "cultural_form_ids", context)
    unknown_cultural_forms = set(cultural_form_ids) - set(cultural_forms)
    if unknown_cultural_forms:
        raise ValueError(
            f"Source registry `{context}.cultural_form_ids` references unknown "
            f"cultural forms: {', '.join(sorted(unknown_cultural_forms))}."
        )
    incompatible_forms = [
        cultural_form_id
        for cultural_form_id in cultural_form_ids
        if cultural_forms[cultural_form_id].modality_id not in modality_ids
    ]
    if incompatible_forms:
        raise ValueError(
            f"Source registry `{context}.cultural_form_ids` contains forms whose "
            f"modalities are absent from `modality_ids`: "
            f"{', '.join(sorted(incompatible_forms))}."
        )
    position = require_mapping(medium.get("position"), f"{context}.position")
    raw_fields = require_mapping(position.get("fields"), f"{context}.position.fields")
    fields: dict[str, str] = {}
    for field_id, field_type in raw_fields.items():
        validate_field_id(field_id, f"{context}.position.fields.{field_id}")
        if field_type not in POSITION_FIELD_TYPES:
            raise ValueError(
                f"Source registry `{context}.position.fields.{field_id}` must be one of: "
                f"{', '.join(sorted(POSITION_FIELD_TYPES))}."
            )
        fields[field_id] = field_type
    required_fields = require_string_list(
        position,
        "required_fields",
        f"{context}.position",
    )
    sort_fields = require_string_list(position, "sort_fields", f"{context}.position")
    for list_name, values in (
        ("required_fields", required_fields),
        ("sort_fields", sort_fields),
    ):
        unknown = set(values) - set(fields)
        if unknown:
            raise ValueError(
                f"Source registry `{context}.position.{list_name}` references unknown "
                f"field(s): {', '.join(sorted(unknown))}."
            )

    raw_formats = position.get("citation_formats")
    if not isinstance(raw_formats, list) or not raw_formats:
        raise ValueError(
            f"Source registry `{context}.position.citation_formats` must be a "
            "non-empty list."
        )
    citation_formats: list[CitationFormat] = []
    seen_format_ids: set[str] = set()
    for index, raw_format in enumerate(raw_formats):
        format_context = f"{context}.position.citation_formats[{index}]"
        citation = require_mapping(raw_format, format_context)
        format_id = require_string(citation, "id", format_context)
        validate_id(format_id, f"{format_context}.id")
        if format_id in seen_format_ids:
            raise ValueError(
                f"Source registry `{format_context}.id` duplicates `{format_id}`."
            )
        seen_format_ids.add(format_id)
        template = require_string(citation, "template", format_context)
        citation_required = require_string_list(
            citation,
            "required_fields",
            format_context,
        )
        placeholders = {
            field_name
            for _, field_name, _, _ in Formatter().parse(template)
            if field_name is not None
        }
        if placeholders != set(citation_required):
            raise ValueError(
                f"Source registry `{format_context}` template placeholders must match "
                "`required_fields`."
            )
        unknown = placeholders - set(fields)
        if unknown:
            raise ValueError(
                f"Source registry `{format_context}.template` references unknown "
                f"field(s): {', '.join(sorted(unknown))}."
            )
        citation_formats.append(
            CitationFormat(
                id=format_id,
                template=template,
                required_fields=citation_required,
            )
        )

    return MediumConfig(
        id=medium_id,
        lifecycle=lifecycle,
        label=require_string(medium, "label", context),
        plural_label=require_string(medium, "plural_label", context),
        modality_ids=modality_ids,
        cultural_form_ids=cultural_form_ids,
        fields=fields,
        required_fields=required_fields,
        sort_fields=sort_fields,
        citation_formats=tuple(citation_formats),
    )


def resolve_resource_binding(
    project: ProjectConfig,
    resources: ResourceConfig,
    binding: dict,
    context: str,
) -> SourceResourceBinding:
    resource_type_id = require_string(binding, "resource_type_id", context)
    validate_id(resource_type_id, f"{context}.resource_type_id")
    if resource_type_id not in resources.types:
        raise ValueError(
            f"Source registry `{context}.resource_type_id` references unknown resource "
            f"type `{resource_type_id}`."
        )
    root_id = require_string(binding, "root_id", context)
    validate_id(root_id, f"{context}.root_id")
    roots = {root.id: root for root in project.resource_roots}
    if root_id not in roots:
        raise ValueError(
            f"Source registry `{context}.root_id` references unknown resource root "
            f"`{root_id}`."
        )
    allowed_placements = tuple(
        placement
        for placement in resources.types[resource_type_id].placements
        if placement.root_id == root_id
    )
    allowed_roots = {placement.root_id for placement in allowed_placements}
    if root_id not in allowed_roots:
        raise ValueError(
            f"Source registry `{context}` binds resource type `{resource_type_id}` "
            f"outside its configured roots: {root_id}."
        )
    relative_path_value = require_string(binding, "relative_path", context)
    relative_path = Path(relative_path_value)
    if relative_path.is_absolute():
        raise ValueError(
            f"Source registry `{context}.relative_path` must be relative: "
            f"{relative_path_value}"
        )
    root_path = roots[root_id].path.resolve()
    path = (root_path / relative_path).resolve()
    if path != root_path and root_path not in path.parents:
        raise ValueError(
            f"Source registry `{context}.relative_path` escapes resource root "
            f"`{root_id}`: {relative_path_value}"
        )
    if not any(
        path == placement.path.resolve() or placement.path.resolve() in path.parents
        for placement in allowed_placements
    ):
        raise ValueError(
            f"Source registry `{context}` path is outside every configured "
            f"`{resource_type_id}` placement beneath `{root_id}`: {relative_path_value}"
        )
    required = require_bool(binding, "required", context)
    if required and not path.exists():
        raise ValueError(f"Source registry `{context}` path does not exist: {path}")
    return SourceResourceBinding(
        resource_type_id=resource_type_id,
        root_id=root_id,
        relative_path=relative_path,
        path=path,
        required=required,
    )


def load_source_registry(
    project: ProjectConfig,
    resources: ResourceConfig,
    schema_packs: SchemaPackRegistry | None = None,
) -> SourceRegistry:
    if schema_packs is None:
        schema_packs = load_schema_pack_registry(project)
    allowed_source_roles = set(
        schema_packs.allowed_values("source.source-role")
    )
    if not allowed_source_roles:
        raise ValueError(
            "Selected schema packs do not provide controlled namespace "
            "`source.source-role` required by `sources.*.role`."
        )
    membership_statuses = set(
        schema_packs.allowed_values("source.membership-status")
    )
    if not membership_statuses:
        raise ValueError(
            "Selected schema packs do not provide controlled namespace "
            "`source.membership-status` required by continuity memberships and "
            "relationship statuses."
        )
    try:
        data = yaml.safe_load(project.sources_registry.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Unable to parse source registry {project.sources_registry}: {exc}"
        ) from exc
    registry = require_mapping(data, "root")
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_SOURCE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported source schema_version {schema_version!r}; "
            f"expected {SUPPORTED_SOURCE_SCHEMA_VERSION}."
        )
    media_modalities = parse_labeled_registry(
        registry.get("media_modalities"), "media_modalities"
    )
    validate_pack_values(
        schema_packs,
        "source.media-modality",
        media_modalities,
        "media_modalities",
    )
    raw_cultural_forms = require_mapping(
        registry.get("cultural_forms"), "cultural_forms"
    )
    cultural_forms: dict[str, CulturalFormConfig] = {}
    for cultural_form_id, raw_cultural_form in raw_cultural_forms.items():
        context = f"cultural_forms.{cultural_form_id}"
        validate_id(cultural_form_id, context)
        cultural_form = require_mapping(raw_cultural_form, context)
        modality_id = require_string(cultural_form, "modality_id", context)
        if modality_id not in media_modalities:
            raise ValueError(
                f"Source registry `{context}.modality_id` references unknown media "
                f"modality `{modality_id}`."
            )
        cultural_forms[cultural_form_id] = CulturalFormConfig(
            id=cultural_form_id,
            label=require_string(cultural_form, "label", context),
            modality_id=modality_id,
        )
    validate_pack_values(
        schema_packs,
        "source.cultural-form",
        cultural_forms,
        "cultural_forms",
    )
    release_forms = parse_labeled_registry(
        registry.get("release_forms"), "release_forms"
    )
    validate_pack_values(
        schema_packs,
        "source.release-form",
        release_forms,
        "release_forms",
    )
    container_formats = parse_labeled_registry(
        registry.get("container_formats"), "container_formats"
    )
    validate_pack_values(
        schema_packs,
        "source.container-format",
        container_formats,
        "container_formats",
    )
    raw_mediums = require_mapping(registry.get("mediums"), "mediums")
    mediums = {
        medium_id: parse_medium(
            medium_id,
            raw_medium,
            media_modalities=media_modalities,
            cultural_forms=cultural_forms,
        )
        for medium_id, raw_medium in raw_mediums.items()
    }
    validate_pack_values(
        schema_packs, "source.medium", mediums, "mediums"
    )

    raw_group_types = require_mapping(
        registry.get("work_group_types"), "work_group_types"
    )
    work_group_types: dict[str, WorkGroupTypeConfig] = {}
    for type_id, raw_type in raw_group_types.items():
        context = f"work_group_types.{type_id}"
        validate_id(type_id, context)
        value = require_mapping(raw_type, context)
        work_group_types[type_id] = WorkGroupTypeConfig(
            id=type_id,
            label=require_string(value, "label", context),
            ordered=require_bool(value, "ordered", context),
        )
    validate_pack_values(
        schema_packs,
        "source.work-group-type",
        work_group_types,
        "work_group_types",
    )

    raw_groups = require_mapping(registry.get("work_groups"), "work_groups")
    work_groups: dict[str, WorkGroupConfig] = {}
    for group_id, raw_group in raw_groups.items():
        context = f"work_groups.{group_id}"
        validate_id(group_id, context)
        group = require_mapping(raw_group, context)
        group_type = require_string(group, "group_type", context)
        if group_type not in work_group_types:
            raise ValueError(
                f"Source registry `{context}.group_type` references unknown work "
                f"group type `{group_type}`."
            )
        parent_group_id = str(group.get("parent_group_id", "")).strip() or None
        work_groups[group_id] = WorkGroupConfig(
            id=group_id,
            lifecycle=parse_lifecycle(group, context),
            label=require_string(group, "label", context),
            short_label=require_string(group, "short_label", context),
            group_type=group_type,
            parent_group_id=parent_group_id,
        )
    for group in work_groups.values():
        if group.parent_group_id is None:
            continue
        if group.parent_group_id not in work_groups:
            raise ValueError(
                f"Source registry `work_groups.{group.id}.parent_group_id` references "
                f"unknown work group `{group.parent_group_id}`."
            )
        if group.parent_group_id == group.id:
            raise ValueError(f"Source registry work group `{group.id}` cannot parent itself.")
    complete_groups: set[str] = set()

    def visit_group(group_id: str, active: set[str]) -> None:
        if group_id in active:
            raise ValueError(
                f"Source registry contains a work-group parent cycle involving "
                f"`{group_id}`."
            )
        if group_id in complete_groups:
            return
        active.add(group_id)
        parent = work_groups[group_id].parent_group_id
        if parent:
            visit_group(parent, active)
        active.remove(group_id)
        complete_groups.add(group_id)

    for group_id in work_groups:
        visit_group(group_id, set())

    raw_continuities = require_mapping(registry.get("continuities"), "continuities")
    continuities: dict[str, ContinuityConfig] = {}
    continuity_aliases: set[str] = set()
    continuity_ids_casefolded = {
        continuity_id.casefold() for continuity_id in raw_continuities
    }
    for continuity_id, raw_continuity in raw_continuities.items():
        context = f"continuities.{continuity_id}"
        validate_id(continuity_id, context)
        continuity = require_mapping(raw_continuity, context)
        continuity_type = require_string(continuity, "continuity_type", context)
        validate_id(continuity_type, f"{context}.continuity_type")
        aliases = require_string_list(continuity, "aliases", context)
        for alias in aliases:
            validate_id(alias, f"{context}.aliases")
            alias_key = alias.casefold()
            if alias_key in continuity_aliases or alias_key in continuity_ids_casefolded:
                raise ValueError(
                    f"Source registry continuity alias `{alias}` is duplicated or "
                    "collides with a continuity ID."
                )
            continuity_aliases.add(alias_key)
        continuities[continuity_id] = ContinuityConfig(
            id=continuity_id,
            lifecycle=parse_lifecycle(continuity, context),
            label=require_string(continuity, "label", context),
            short_label=require_string(continuity, "short_label", context),
            continuity_type=continuity_type,
            aliases=aliases,
        )
    validate_pack_values(
        schema_packs,
        "source.continuity-type",
        (continuity.continuity_type for continuity in continuities.values()),
        "continuities.*.continuity_type",
    )

    continuity_relationship_types = parse_relationship_types(
        registry.get("continuity_relationship_types"),
        "continuity_relationship_types",
    )
    work_relationship_types = parse_relationship_types(
        registry.get("work_relationship_types"), "work_relationship_types"
    )
    source_relationship_types = parse_relationship_types(
        registry.get("source_relationship_types"), "source_relationship_types"
    )
    validate_pack_values(
        schema_packs,
        "source.continuity-relationship-type",
        continuity_relationship_types,
        "continuity_relationship_types",
    )
    validate_pack_values(
        schema_packs,
        "source.work-relationship-type",
        work_relationship_types,
        "work_relationship_types",
    )
    validate_pack_values(
        schema_packs,
        "source.source-relationship-type",
        source_relationship_types,
        "source_relationship_types",
    )

    raw_continuity_relationships = registry.get("continuity_relationships")
    if not isinstance(raw_continuity_relationships, list):
        raise ValueError(
            "Source registry `continuity_relationships` must be a list."
        )
    continuity_relationships: list[ContinuityRelationship] = []
    seen_relationship_ids: set[str] = set()
    for index, raw_relationship in enumerate(raw_continuity_relationships):
        context = f"continuity_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_relationship_ids:
            raise ValueError(
                f"Source registry relationship ID `{relationship_id}` is duplicated."
            )
        seen_relationship_ids.add(relationship_id)
        source_id = require_string(
            relationship, "source_continuity_id", context
        )
        target_id = require_string(
            relationship, "target_continuity_id", context
        )
        relationship_type = require_string(
            relationship, "relationship_type", context
        )
        if source_id not in continuities or target_id not in continuities:
            raise ValueError(
                f"Source registry `{context}` references an unknown continuity."
            )
        if source_id == target_id:
            raise ValueError(
                f"Source registry `{context}` cannot relate a continuity to itself."
            )
        if relationship_type not in continuity_relationship_types:
            raise ValueError(
                f"Source registry `{context}.relationship_type` references unknown "
                f"type `{relationship_type}`."
            )
        status = require_string(relationship, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Source registry `{context}.status` must be one of: "
                f"{', '.join(sorted(membership_statuses))}."
            )
        continuity_relationships.append(
            ContinuityRelationship(
                relationship_id, source_id, relationship_type, target_id, status
            )
        )

    raw_authority_profiles = require_mapping(
        registry.get("authority_profiles"), "authority_profiles"
    )
    authority_profiles: dict[str, AuthorityProfile] = {}
    for profile_id, raw_profile in raw_authority_profiles.items():
        context = f"authority_profiles.{profile_id}"
        validate_id(profile_id, context)
        profile = require_mapping(raw_profile, context)
        continuity_order = require_string_list(profile, "continuity_order", context)
        if len(set(continuity_order)) != len(continuity_order):
            raise ValueError(
                f"Source registry `{context}.continuity_order` contains duplicates."
            )
        unknown_continuities = set(continuity_order) - set(continuities)
        if unknown_continuities:
            raise ValueError(
                f"Source registry `{context}.continuity_order` references unknown "
                f"continuities: {', '.join(sorted(unknown_continuities))}."
            )
        accepted_statuses = require_string_list(
            profile, "accepted_membership_statuses", context
        )
        unknown_statuses = set(accepted_statuses) - membership_statuses
        if unknown_statuses:
            raise ValueError(
                f"Source registry `{context}.accepted_membership_statuses` contains "
                f"unknown values: {', '.join(sorted(unknown_statuses))}."
            )
        priority_order = require_string(profile, "source_priority_order", context)
        if priority_order not in PRIORITY_ORDERS:
            raise ValueError(
                f"Source registry `{context}.source_priority_order` must be one of: "
                f"{', '.join(sorted(PRIORITY_ORDERS))}."
            )
        comparison_types = require_string_list(
            profile, "comparison_work_relationship_types", context
        )
        unknown_types = set(comparison_types) - set(work_relationship_types)
        if unknown_types:
            raise ValueError(
                f"Source registry `{context}.comparison_work_relationship_types` "
                f"references unknown types: {', '.join(sorted(unknown_types))}."
            )
        conflict = require_string(profile, "cross_source_conflict", context)
        if conflict not in CONFLICT_BEHAVIORS:
            raise ValueError(
                f"Source registry `{context}.cross_source_conflict` must be one of: "
                f"{', '.join(sorted(CONFLICT_BEHAVIORS))}."
            )
        deviation_owner = require_string(
            profile, "derivative_deviation_owner", context
        )
        if deviation_owner not in DEVIATION_OWNERS:
            raise ValueError(
                f"Source registry `{context}.derivative_deviation_owner` must be one "
                f"of: {', '.join(sorted(DEVIATION_OWNERS))}."
            )
        authority_profiles[profile_id] = AuthorityProfile(
            id=profile_id,
            lifecycle=parse_lifecycle(profile, context),
            label=require_string(profile, "label", context),
            continuity_order=continuity_order,
            accepted_membership_statuses=accepted_statuses,
            source_priority_order=priority_order,
            comparison_work_relationship_types=comparison_types,
            cross_source_conflict=conflict,
            derivative_deviation_owner=deviation_owner,
            preserve_source_scoped_claims=require_bool(
                profile, "preserve_source_scoped_claims", context
            ),
        )
    default_authority_profile_id = require_string(
        registry, "default_authority_profile_id", "root"
    )
    if default_authority_profile_id not in authority_profiles:
        raise ValueError(
            "Source registry `default_authority_profile_id` references unknown "
            f"authority profile `{default_authority_profile_id}`."
        )

    raw_works = require_mapping(registry.get("works"), "works")
    works = {
        work_id: parse_work(
            work_id,
            raw_work,
            work_groups=work_groups,
            work_group_types=work_group_types,
            continuities=continuities,
            mediums=mediums,
            release_forms=release_forms,
            membership_statuses=membership_statuses,
        )
        for work_id, raw_work in raw_works.items()
    }
    validate_pack_values(
        schema_packs,
        "source.work-type",
        (work.work_type for work in works.values()),
        "works.*.work_type",
    )
    validate_pack_values(
        schema_packs,
        "source.work-lifecycle-status",
        (work.work_status for work in works.values()),
        "works.*.work_status",
    )
    seen_ordinals: dict[tuple[str, int], str] = {}
    work_aliases: dict[str, str] = {}
    work_ids_casefolded = {work_id.casefold() for work_id in works}
    for work in works.values():
        for membership in work.group_memberships:
            if membership.ordinal is not None:
                ordinal_key = (membership.group_id, membership.ordinal)
                if ordinal_key in seen_ordinals:
                    raise ValueError(
                        f"Source registry duplicates ordinal {membership.ordinal} in "
                        f"work group `{membership.group_id}` between "
                        f"`{seen_ordinals[ordinal_key]}` and `{work.id}`."
                    )
                seen_ordinals[ordinal_key] = work.id
        for alias in work.aliases:
            alias_key = alias.casefold()
            if alias_key in work_aliases or alias_key in work_ids_casefolded:
                raise ValueError(
                    f"Source registry work alias `{alias}` is duplicated or collides "
                    "with a work ID."
                )
            work_aliases[alias_key] = work.id

    raw_segments = require_mapping(registry.get("segments"), "segments")
    segments: dict[str, SegmentConfig] = {}
    for segment_id, raw_segment in raw_segments.items():
        context = f"segments.{segment_id}"
        validate_id(segment_id, context)
        segment = require_mapping(raw_segment, context)
        work_id = require_string(segment, "work_id", context)
        if work_id not in works:
            raise ValueError(
                f"Source registry `{context}.work_id` references unknown work "
                f"`{work_id}`."
            )
        parent_segment_id = str(segment.get("parent_segment_id", "")).strip() or None
        segment_type = require_string(segment, "segment_type", context)
        validate_id(segment_type, f"{context}.segment_type")
        ordinal = segment.get("ordinal")
        if ordinal is not None and (
            isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1
        ):
            raise ValueError(
                f"Source registry `{context}.ordinal` must be a positive integer "
                "when present."
            )
        segments[segment_id] = SegmentConfig(
            id=segment_id,
            work_id=work_id,
            parent_segment_id=parent_segment_id,
            segment_type=segment_type,
            label=require_string(segment, "label", context),
            ordinal=ordinal,
        )
    if segments:
        validate_pack_values(
            schema_packs,
            "source.segment-type",
            (segment.segment_type for segment in segments.values()),
            "segments.*.segment_type",
        )
    for segment in segments.values():
        if segment.parent_segment_id is None:
            continue
        parent = segments.get(segment.parent_segment_id)
        if parent is None:
            raise ValueError(
                f"Source registry `segments.{segment.id}.parent_segment_id` references "
                f"unknown segment `{segment.parent_segment_id}`."
            )
        if parent.id == segment.id:
            raise ValueError(f"Source registry segment `{segment.id}` cannot parent itself.")
        if parent.work_id != segment.work_id:
            raise ValueError(
                f"Source registry segment `{segment.id}` and its parent must belong "
                "to the same work."
            )
    complete_segments: set[str] = set()

    def visit_segment(segment_id: str, active: set[str]) -> None:
        if segment_id in active:
            raise ValueError(
                f"Source registry contains a segment-parent cycle involving "
                f"`{segment_id}`."
            )
        if segment_id in complete_segments:
            return
        active.add(segment_id)
        parent = segments[segment_id].parent_segment_id
        if parent:
            visit_segment(parent, active)
        active.remove(segment_id)
        complete_segments.add(segment_id)

    for segment_id in segments:
        visit_segment(segment_id, set())

    raw_ordering_schemes = require_mapping(
        registry.get("ordering_schemes"), "ordering_schemes"
    )
    ordering_schemes: dict[str, OrderingScheme] = {}
    for scheme_id, raw_scheme in raw_ordering_schemes.items():
        context = f"ordering_schemes.{scheme_id}"
        validate_id(scheme_id, context)
        scheme = require_mapping(raw_scheme, context)
        ordering_type = require_string(scheme, "ordering_type", context)
        validate_id(ordering_type, f"{context}.ordering_type")
        raw_entries = scheme.get("entries")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError(
                f"Source registry `{context}.entries` must be a non-empty list."
            )
        entries: list[OrderingEntry] = []
        seen_targets: set[tuple[str, str]] = set()
        seen_ordinals: set[int] = set()
        for index, raw_entry in enumerate(raw_entries):
            entry_context = f"{context}.entries[{index}]"
            entry = require_mapping(raw_entry, entry_context)
            target_type = require_string(entry, "target_type", entry_context)
            if target_type not in {"work", "segment"}:
                raise ValueError(
                    f"Source registry `{entry_context}.target_type` must be `work` "
                    "or `segment`."
                )
            target_id = require_string(entry, "target_id", entry_context)
            targets = works if target_type == "work" else segments
            if target_id not in targets:
                raise ValueError(
                    f"Source registry `{entry_context}.target_id` references unknown "
                    f"{target_type} `{target_id}`."
                )
            ordinal = entry.get("ordinal")
            if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
                raise ValueError(
                    f"Source registry `{entry_context}.ordinal` must be a positive integer."
                )
            target_key = (target_type, target_id)
            if target_key in seen_targets or ordinal in seen_ordinals:
                raise ValueError(
                    f"Source registry `{context}.entries` repeats a target or ordinal."
                )
            seen_targets.add(target_key)
            seen_ordinals.add(ordinal)
            entries.append(OrderingEntry(target_type, target_id, ordinal))
        ordering_schemes[scheme_id] = OrderingScheme(
            id=scheme_id,
            label=require_string(scheme, "label", context),
            ordering_type=ordering_type,
            entries=tuple(sorted(entries, key=lambda entry: entry.ordinal)),
        )
    if ordering_schemes:
        validate_pack_values(
            schema_packs,
            "source.ordering-type",
            (scheme.ordering_type for scheme in ordering_schemes.values()),
            "ordering_schemes.*.ordering_type",
        )

    raw_work_relationships = registry.get("work_relationships")
    if not isinstance(raw_work_relationships, list):
        raise ValueError("Source registry `work_relationships` must be a list.")
    work_relationships: list[WorkRelationship] = []
    for index, raw_relationship in enumerate(raw_work_relationships):
        context = f"work_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_relationship_ids:
            raise ValueError(
                f"Source registry relationship ID `{relationship_id}` is duplicated."
            )
        seen_relationship_ids.add(relationship_id)
        source_id = require_string(relationship, "source_work_id", context)
        target_id = require_string(relationship, "target_work_id", context)
        relationship_type = require_string(
            relationship, "relationship_type", context
        )
        if source_id not in works or target_id not in works:
            raise ValueError(f"Source registry `{context}` references an unknown work.")
        if source_id == target_id:
            raise ValueError(
                f"Source registry `{context}` cannot relate a work to itself."
            )
        if relationship_type not in work_relationship_types:
            raise ValueError(
                f"Source registry `{context}.relationship_type` references unknown "
                f"type `{relationship_type}`."
            )
        continuity_ids = require_string_list(
            relationship, "continuity_ids", context
        )
        unknown_continuities = set(continuity_ids) - set(continuities)
        if unknown_continuities:
            raise ValueError(
                f"Source registry `{context}.continuity_ids` references unknown "
                f"continuities: {', '.join(sorted(unknown_continuities))}."
            )
        status = require_string(relationship, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Source registry `{context}.status` must be one of: "
                f"{', '.join(sorted(membership_statuses))}."
            )
        work_relationships.append(
            WorkRelationship(
                relationship_id,
                source_id,
                relationship_type,
                target_id,
                continuity_ids,
                status,
            )
        )

    raw_adaptation_mappings = registry.get("adaptation_mappings")
    if not isinstance(raw_adaptation_mappings, list):
        raise ValueError("Source registry `adaptation_mappings` must be a list.")
    adaptation_mappings: list[AdaptationMapping] = []
    seen_adaptation_mapping_ids: set[str] = set()
    for index, raw_mapping in enumerate(raw_adaptation_mappings):
        context = f"adaptation_mappings[{index}]"
        mapping = require_mapping(raw_mapping, context)
        mapping_id = require_string(mapping, "id", context)
        validate_id(mapping_id, f"{context}.id")
        if mapping_id in seen_adaptation_mapping_ids:
            raise ValueError(
                f"Source registry adaptation mapping ID `{mapping_id}` is duplicated."
            )
        seen_adaptation_mapping_ids.add(mapping_id)
        source_work_id = require_string(mapping, "source_work_id", context)
        target_work_id = require_string(mapping, "target_work_id", context)
        if source_work_id not in works or target_work_id not in works:
            raise ValueError(
                f"Source registry `{context}` references an unknown work."
            )
        source_segment_ids = require_string_list(
            mapping, "source_segment_ids", context
        )
        target_segment_ids = require_string_list(
            mapping, "target_segment_ids", context
        )
        for field_name, segment_ids, work_id in (
            ("source_segment_ids", source_segment_ids, source_work_id),
            ("target_segment_ids", target_segment_ids, target_work_id),
        ):
            for segment_id in segment_ids:
                if segment_id not in segments:
                    raise ValueError(
                        f"Source registry `{context}.{field_name}` references unknown "
                        f"segment `{segment_id}`."
                    )
                if segments[segment_id].work_id != work_id:
                    raise ValueError(
                        f"Source registry `{context}.{field_name}` segment "
                        f"`{segment_id}` belongs to a different work."
                    )
        mapping_type = require_string(mapping, "mapping_type", context)
        status = require_string(mapping, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Source registry `{context}.status` must be one of: "
                f"{', '.join(sorted(membership_statuses))}."
            )
        adaptation_mappings.append(
            AdaptationMapping(
                id=mapping_id,
                source_work_id=source_work_id,
                target_work_id=target_work_id,
                source_segment_ids=source_segment_ids,
                target_segment_ids=target_segment_ids,
                mapping_type=mapping_type,
                status=status,
            )
        )
    if adaptation_mappings:
        validate_pack_values(
            schema_packs,
            "source.adaptation-mapping-type",
            (mapping.mapping_type for mapping in adaptation_mappings),
            "adaptation_mappings.*.mapping_type",
        )

    raw_sources = require_mapping(registry.get("sources"), "sources")
    sources: dict[str, SourceConfig] = {}
    aliases: dict[str, str] = {}
    for source_id, raw_source in raw_sources.items():
        context = f"sources.{source_id}"
        validate_id(source_id, context)
        source = require_mapping(raw_source, context)
        lifecycle = parse_lifecycle(source, context)
        medium_id = require_string(source, "medium_id", context)
        if medium_id not in mediums:
            raise ValueError(
                f"Source registry `{context}.medium_id` references unknown medium "
                f"`{medium_id}`."
            )
        container_format_ids = require_string_list(
            source, "container_format_ids", context
        )
        if not container_format_ids:
            raise ValueError(
                f"Source registry `{context}.container_format_ids` must not be empty."
            )
        unknown_container_formats = set(container_format_ids) - set(container_formats)
        if unknown_container_formats:
            raise ValueError(
                f"Source registry `{context}.container_format_ids` references unknown "
                f"container formats: {', '.join(sorted(unknown_container_formats))}."
            )
        role = require_string(source, "role", context)
        if role not in allowed_source_roles:
            raise ValueError(
                f"Source registry `{context}.role` must be one of: "
                f"{', '.join(sorted(allowed_source_roles))}."
            )
        work_id = require_string(source, "work_id", context)
        if work_id not in works:
            raise ValueError(
                f"Source registry `{context}.work_id` references unknown work "
                f"`{work_id}`."
            )
        if works[work_id].medium_id != medium_id and role not in {"supplemental", "reference", "extract"}:
            raise ValueError(
                f"Source registry `{context}` medium does not match work `{work_id}`."
            )
        comparison_group = require_string(source, "comparison_group", context)
        validate_id(comparison_group, f"{context}.comparison_group")
        priority = source.get("priority")
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            raise ValueError(
                f"Source registry `{context}.priority` must be a positive integer."
            )
        source_aliases = require_string_list(source, "aliases", context)
        for alias in source_aliases:
            validate_id(alias, f"{context}.aliases")
            alias_key = alias.casefold()
            if alias_key in aliases or alias_key in {
                existing_id.casefold() for existing_id in raw_sources
            }:
                raise ValueError(
                    f"Source registry alias `{alias}` is duplicated or collides with "
                    "a source ID."
                )
            aliases[alias_key] = source_id
        evidence_modes = require_string_list(source, "evidence_modes", context)
        for evidence_mode in evidence_modes:
            validate_id(evidence_mode, f"{context}.evidence_modes")
        raw_bindings = source.get("resource_bindings")
        if not isinstance(raw_bindings, list):
            raise ValueError(
                f"Source registry `{context}.resource_bindings` must be a list."
            )
        bindings = tuple(
            resolve_resource_binding(
                project,
                resources,
                require_mapping(raw_binding, f"{context}.resource_bindings[{index}]"),
                f"{context}.resource_bindings[{index}]",
            )
            for index, raw_binding in enumerate(raw_bindings)
        )
        sources[source_id] = SourceConfig(
            id=source_id,
            lifecycle=lifecycle,
            label=require_string(source, "label", context),
            work_id=work_id,
            medium_id=medium_id,
            container_format_ids=container_format_ids,
            role=role,
            comparison_group=comparison_group,
            priority=priority,
            aliases=source_aliases,
            evidence_modes=evidence_modes,
            resource_bindings=bindings,
        )
    validate_pack_values(
        schema_packs,
        "source.source-role",
        (source.role for source in sources.values()),
        "sources.*.role",
    )

    raw_source_relationships = registry.get("source_relationships")
    if not isinstance(raw_source_relationships, list):
        raise ValueError("Source registry `source_relationships` must be a list.")
    source_relationships: list[SourceRelationship] = []
    for index, raw_relationship in enumerate(raw_source_relationships):
        context = f"source_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_relationship_ids:
            raise ValueError(
                f"Source registry relationship ID `{relationship_id}` is duplicated."
            )
        seen_relationship_ids.add(relationship_id)
        source_id = require_string(relationship, "source_source_id", context)
        target_id = require_string(relationship, "target_source_id", context)
        relationship_type = require_string(
            relationship, "relationship_type", context
        )
        if source_id not in sources or target_id not in sources:
            raise ValueError(
                f"Source registry `{context}` references an unknown source."
            )
        if source_id == target_id:
            raise ValueError(
                f"Source registry `{context}` cannot relate a source to itself."
            )
        if relationship_type not in source_relationship_types:
            raise ValueError(
                f"Source registry `{context}.relationship_type` references unknown "
                f"type `{relationship_type}`."
            )
        source_relationships.append(
            SourceRelationship(
                relationship_id, source_id, relationship_type, target_id
            )
        )

    return SourceRegistry(
        path=project.sources_registry,
        schema_version=schema_version,
        default_authority_profile_id=default_authority_profile_id,
        media_modalities=media_modalities,
        cultural_forms=cultural_forms,
        release_forms=release_forms,
        container_formats=container_formats,
        mediums=mediums,
        work_group_types=work_group_types,
        work_groups=work_groups,
        continuities=continuities,
        continuity_relationship_types=continuity_relationship_types,
        continuity_relationships=tuple(continuity_relationships),
        authority_profiles=authority_profiles,
        work_relationship_types=work_relationship_types,
        works=works,
        segments=segments,
        ordering_schemes=ordering_schemes,
        work_relationships=tuple(work_relationships),
        adaptation_mappings=tuple(adaptation_mappings),
        work_aliases=work_aliases,
        source_relationship_types=source_relationship_types,
        sources=sources,
        source_relationships=tuple(source_relationships),
        source_aliases=aliases,
    )
