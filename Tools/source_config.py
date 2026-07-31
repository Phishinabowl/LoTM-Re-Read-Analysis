from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Formatter
import re

import yaml

from project_config import ProjectConfig
from resource_config import ResourceConfig
from schema_pack_config import SchemaPackRegistry, load_schema_pack_registry


SUPPORTED_SOURCE_SCHEMA_VERSION = 8
LIFECYCLES = {"active", "deferred"}
POSITION_FIELD_TYPES = {"string", "integer", "number", "timestamp", "boolean"}
PRIORITY_ORDERS = {"ascending", "descending"}
CONFLICT_BEHAVIORS = {"flag"}
DEVIATION_OWNERS = {"derivative-work"}
CHAPTER_NUMBERING_MODES = {"work-local", "series-global", "not-applicable"}
VOLUME_CATALOG_STATUSES = {"verified", "pending-verification", "not-applicable"}
ORDERING_MODES = {"total", "partial"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
FIELD_PATH_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(?:(?:\.[a-z][a-z0-9_]*)|(?:\[[0-9]+\]))*$"
)
LANGUAGE_TAG_PATTERN = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


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
    parent_work_id: str | None
    work_type: str
    medium_id: str
    release_form_id: str
    work_status: str
    aliases: tuple[str, ...]
    localized_titles: tuple["LocalizedTitle", ...]
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
    aliases: tuple[str, ...]
    localized_titles: tuple["LocalizedTitle", ...]
    ordinal: int | None


@dataclass(frozen=True)
class ContentGroupMember:
    id: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class ContentGroup:
    id: str
    lifecycle: str
    label: str
    group_type: str
    members: tuple[ContentGroupMember, ...]
    parent_group_ids: tuple[str, ...]
    ordering_scheme_id: str | None
    localized_titles: tuple["LocalizedTitle", ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class NumberingEntry:
    target_id: str
    display_number: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class NumberingScheme:
    id: str
    lifecycle: str
    label: str
    target_type: str
    scope_type: str
    scope_id: str | None
    entries: tuple[NumberingEntry, ...]


@dataclass(frozen=True)
class OrderingEntry:
    id: str
    target_type: str
    target_id: str
    ordinal: int | None
    after_entry_ids: tuple[str, ...]


@dataclass(frozen=True)
class OrderingScheme:
    id: str
    label: str
    ordering_type: str
    ordering_mode: str
    entries: tuple[OrderingEntry, ...]


@dataclass(frozen=True)
class AdaptationBasisInput:
    work_id: str
    segment_ids: tuple[str, ...]
    basis_role: str


@dataclass(frozen=True)
class AdaptationMapping:
    id: str
    basis_inputs: tuple[AdaptationBasisInput, ...]
    target_work_id: str
    target_segment_ids: tuple[str, ...]
    mapping_type: str
    status: str


@dataclass(frozen=True)
class LocalizedTitle:
    id: str
    language_tag: str
    territory_ids: tuple[str, ...]
    title: str
    title_type: str
    status: str
    is_primary: bool
    romanization_scheme: str | None
    valid_window: "TemporalWindow | None"


@dataclass(frozen=True)
class TemporalWindow:
    start: str | None
    end: str | None
    precision: str
    certainty: str
    timezone: str | None


@dataclass(frozen=True)
class TerritoryConfig:
    id: str
    lifecycle: str
    label: str
    territory_type: str
    parent_territory_id: str | None
    codes: dict[str, str]


@dataclass(frozen=True)
class PlatformConfig:
    id: str
    lifecycle: str
    label: str
    platform_type: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ManifestationConfig:
    id: str
    lifecycle: str
    label: str
    work_id: str
    segment_ids: tuple[str, ...]
    manifestation_type: str
    language_tags: tuple[str, ...]
    territory_ids: tuple[str, ...]
    container_format_ids: tuple[str, ...]
    localized_titles: tuple[LocalizedTitle, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ManifestationRelationship:
    id: str
    source_manifestation_id: str
    relationship_type: str
    target_manifestation_id: str
    status: str


@dataclass(frozen=True)
class ManifestationSegmentMapping:
    id: str
    source_manifestation_id: str
    source_segment_ids: tuple[str, ...]
    target_manifestation_id: str
    target_segment_ids: tuple[str, ...]
    mapping_type: str
    status: str


@dataclass(frozen=True)
class ReleaseComponent:
    id: str
    lifecycle: str
    label: str
    manifestation_id: str | None
    component_type: str
    segment_ids: tuple[str, ...]
    language_tag: str | None


@dataclass(frozen=True)
class ReleaseComponentRelationship:
    id: str
    source_component_id: str
    relationship_type: str
    target_component_id: str


@dataclass(frozen=True)
class ReleasePackage:
    id: str
    lifecycle: str
    label: str
    package_type: str
    manifestation_ids: tuple[str, ...]
    segment_ids: tuple[str, ...]
    release_component_ids: tuple[str, ...]
    container_format_ids: tuple[str, ...]
    localized_titles: tuple[LocalizedTitle, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseEvent:
    id: str
    lifecycle: str
    label: str
    subject_type: str
    subject_id: str
    segment_ids: tuple[str, ...]
    release_event_type: str
    release_window: TemporalWindow | None
    territory_ids: tuple[str, ...]
    platform_ids: tuple[str, ...]
    availability_status: str
    release_run_id: str | None


@dataclass(frozen=True)
class ReleaseRunException:
    exception_type: str
    segment_id: str
    release_window: TemporalWindow | None
    interval_count: int | None


@dataclass(frozen=True)
class ReleaseRunPhase:
    id: str
    segment_ids: tuple[str, ...]
    first_release_window: TemporalWindow
    cadence_unit: str
    cadence_interval: int
    batch_size: int


@dataclass(frozen=True)
class ReleaseRun:
    id: str
    lifecycle: str
    label: str
    subject_type: str
    subject_id: str
    segment_ids: tuple[str, ...]
    ordering_scheme_id: str
    release_event_type: str
    phases: tuple[ReleaseRunPhase, ...]
    territory_ids: tuple[str, ...]
    platform_ids: tuple[str, ...]
    availability_status: str
    exceptions: tuple[ReleaseRunException, ...]


@dataclass(frozen=True)
class CatalogPlacement:
    id: str
    lifecycle: str
    label: str
    platform_id: str
    placement_type: str
    parent_placement_id: str | None
    target_type: str
    target_id: str
    ordinal: int | None
    provider_key: str | None
    localized_titles: tuple[LocalizedTitle, ...]


@dataclass(frozen=True)
class PlatformOffering:
    id: str
    lifecycle: str
    label: str
    platform_id: str
    subject_type: str
    subject_id: str
    segment_ids: tuple[str, ...]
    release_event_id: str | None
    offering_type: str
    availability_status: str
    territory_ids: tuple[str, ...]
    language_tags: tuple[str, ...]
    availability_window: TemporalWindow | None
    catalog_placement_ids: tuple[str, ...]


@dataclass(frozen=True)
class IdentifierScheme:
    id: str
    lifecycle: str
    label: str
    target_types: tuple[str, ...]
    case_sensitive: bool


@dataclass(frozen=True)
class ExternalIdentifier:
    id: str
    scheme_id: str
    target_type: str
    target_id: str
    value: str
    territory_ids: tuple[str, ...]
    language_tag: str | None
    status: str


@dataclass(frozen=True)
class SourceResourceBinding:
    resource_type_id: str
    root_id: str
    relative_path: Path
    path: Path
    required: bool


@dataclass(frozen=True)
class SourceCoverage:
    id: str
    target_type: str
    target_id: str
    coverage_type: str
    position_ranges: tuple["CoveragePositionRange", ...]


@dataclass(frozen=True)
class CoveragePositionRange:
    id: str
    start: dict[str, object]
    end: dict[str, object]


@dataclass(frozen=True)
class SourceObservation:
    id: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class SourceConfig:
    id: str
    lifecycle: str
    label: str
    work_ids: tuple[str, ...]
    manifestation_id: str | None
    release_package_id: str | None
    release_event_id: str | None
    release_component_ids: tuple[str, ...]
    platform_offering_id: str | None
    medium_id: str
    container_format_ids: tuple[str, ...]
    role: str
    comparison_group: str
    priority: int
    aliases: tuple[str, ...]
    evidence_modes: tuple[str, ...]
    observations: tuple[SourceObservation, ...]
    coverage: tuple[SourceCoverage, ...]
    resource_bindings: tuple[SourceResourceBinding, ...]


@dataclass(frozen=True)
class SourceRelationship:
    id: str
    source_source_id: str
    relationship_type: str
    target_source_id: str


@dataclass(frozen=True)
class ProvenanceEvidenceLink:
    source_id: str
    evidence_role: str
    locator: dict[str, object]


@dataclass(frozen=True)
class ProvenanceAssertion:
    id: str
    subject_type: str
    subject_id: str
    field_path: str | None
    asserted_value: object
    assertion_status: str
    observed_at: TemporalWindow | None
    effective_window: TemporalWindow | None
    evidence_links: tuple[ProvenanceEvidenceLink, ...]


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
    content_groups: dict[str, ContentGroup]
    numbering_schemes: dict[str, NumberingScheme]
    ordering_schemes: dict[str, OrderingScheme]
    work_relationships: tuple[WorkRelationship, ...]
    adaptation_mappings: tuple[AdaptationMapping, ...]
    territories: dict[str, TerritoryConfig]
    platforms: dict[str, PlatformConfig]
    manifestation_relationship_types: dict[str, RelationshipTypeConfig]
    manifestations: dict[str, ManifestationConfig]
    manifestation_relationships: tuple[ManifestationRelationship, ...]
    manifestation_segment_mappings: tuple[ManifestationSegmentMapping, ...]
    release_components: dict[str, ReleaseComponent]
    release_component_relationship_types: dict[str, RelationshipTypeConfig]
    release_component_relationships: tuple[ReleaseComponentRelationship, ...]
    release_packages: dict[str, ReleasePackage]
    release_runs: dict[str, ReleaseRun]
    release_events: dict[str, ReleaseEvent]
    catalog_placements: dict[str, CatalogPlacement]
    platform_offerings: dict[str, PlatformOffering]
    work_aliases: dict[str, str]
    source_relationship_types: dict[str, RelationshipTypeConfig]
    sources: dict[str, SourceConfig]
    source_relationships: tuple[SourceRelationship, ...]
    provenance_assertions: tuple[ProvenanceAssertion, ...]
    source_aliases: dict[str, str]
    identifier_schemes: dict[str, IdentifierScheme]
    external_identifiers: tuple[ExternalIdentifier, ...]

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


def optional_string(mapping: dict, key: str, context: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Source registry `{context}.{key}` must be a non-empty string when present."
        )
    return value.strip()


def validate_language_tag(value: str, context: str) -> None:
    if not LANGUAGE_TAG_PATTERN.fullmatch(value):
        raise ValueError(
            f"Source registry `{context}` must be a BCP-47-style language tag: {value}"
        )


def parse_localized_titles(
    mapping: dict,
    context: str,
    schema_packs: SchemaPackRegistry,
) -> tuple[LocalizedTitle, ...]:
    raw_titles = mapping.get("localized_titles", [])
    if not isinstance(raw_titles, list):
        raise ValueError(
            f"Source registry `{context}.localized_titles` must be a list."
        )
    titles: list[LocalizedTitle] = []
    seen_ids: set[str] = set()
    seen_scopes: set[tuple[str, tuple[str, ...], str, str | None]] = set()
    for index, raw_title in enumerate(raw_titles):
        title_context = f"{context}.localized_titles[{index}]"
        value = require_mapping(raw_title, title_context)
        title_id = require_string(value, "id", title_context)
        validate_id(title_id, f"{title_context}.id")
        if title_id in seen_ids:
            raise ValueError(
                f"Source registry `{context}.localized_titles` repeats ID `{title_id}`."
            )
        seen_ids.add(title_id)
        language_tag = require_string(value, "language_tag", title_context)
        validate_language_tag(language_tag, f"{title_context}.language_tag")
        territory_ids = require_string_list(value, "territory_ids", title_context)
        title_type = require_string(value, "title_type", title_context)
        validate_pack_values(
            schema_packs,
            "source.localized-title-type",
            (title_type,),
            f"{title_context}.title_type",
        )
        status = require_string(value, "status", title_context)
        validate_pack_values(
            schema_packs,
            "source.localized-title-status",
            (status,),
            f"{title_context}.status",
        )
        romanization_scheme = optional_string(
            value, "romanization_scheme", title_context
        )
        scope = (
            language_tag.casefold(),
            tuple(sorted(territory_ids)),
            title_type,
            romanization_scheme,
        )
        if scope in seen_scopes:
            raise ValueError(
                f"Source registry `{context}.localized_titles` repeats a locale scope."
            )
        seen_scopes.add(scope)
        titles.append(
            LocalizedTitle(
                id=title_id,
                language_tag=language_tag,
                territory_ids=territory_ids,
                title=require_string(value, "title", title_context),
                title_type=title_type,
                status=status,
                is_primary=require_bool(value, "is_primary", title_context),
                romanization_scheme=romanization_scheme,
                valid_window=parse_temporal_window(
                    value, "valid_window", title_context, schema_packs
                ),
            )
        )
    return tuple(titles)


def parse_temporal_window(
    mapping: dict,
    key: str,
    context: str,
    schema_packs: SchemaPackRegistry,
) -> TemporalWindow | None:
    raw_window = mapping.get(key)
    if raw_window is None:
        return None
    window_context = f"{context}.{key}"
    window = require_mapping(raw_window, window_context)
    precision = require_string(window, "precision", window_context)
    certainty = require_string(window, "certainty", window_context)
    validate_pack_values(
        schema_packs,
        "source.temporal-precision",
        (precision,),
        f"{window_context}.precision",
    )
    validate_pack_values(
        schema_packs,
        "source.temporal-certainty",
        (certainty,),
        f"{window_context}.certainty",
    )
    start = optional_string(window, "start", window_context)
    end = optional_string(window, "end", window_context)
    timezone = optional_string(window, "timezone", window_context)
    if precision == "unknown":
        if start is not None or end is not None or timezone is not None:
            raise ValueError(
                f"Source registry `{window_context}` with unknown precision cannot "
                "declare start, end, or timezone."
            )
    elif start is None:
        raise ValueError(
            f"Source registry `{window_context}.start` is required unless precision "
            "is `unknown`."
        )

    def validate_value(value: str | None, field_name: str) -> None:
        if value is None:
            return
        try:
            if precision == "year":
                if not re.fullmatch(r"\d{4}", value):
                    raise ValueError
            elif precision == "month":
                datetime.strptime(value, "%Y-%m")
            elif precision == "date":
                datetime.strptime(value, "%Y-%m-%d")
            elif precision == "datetime":
                datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                f"Source registry `{window_context}.{field_name}` does not match "
                f"precision `{precision}`: {value}"
            ) from exc

    validate_value(start, "start")
    validate_value(end, "end")
    if timezone is not None and precision != "datetime":
        raise ValueError(
            f"Source registry `{window_context}.timezone` is only valid for datetime "
            "precision."
        )
    return TemporalWindow(start, end, precision, certainty, timezone)


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Source registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def validate_position_values(
    values: dict[str, object],
    fields: dict[str, str],
    context: str,
) -> None:
    for field_id, value in values.items():
        field_type = fields[field_id]
        valid = False
        if field_type in {"string", "timestamp"}:
            valid = isinstance(value, str) and bool(value.strip())
        elif field_type == "integer":
            valid = isinstance(value, int) and not isinstance(value, bool)
        elif field_type == "number":
            valid = isinstance(value, (int, float)) and not isinstance(value, bool)
        elif field_type == "boolean":
            valid = isinstance(value, bool)
        if not valid:
            raise ValueError(
                f"Source registry `{context}.{field_id}` must match position "
                f"field type `{field_type}`."
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
    schema_packs: SchemaPackRegistry,
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
        parent_work_id=optional_string(work, "parent_work_id", context),
        work_type=work_type,
        medium_id=medium_id,
        release_form_id=release_form_id,
        work_status=work_status,
        aliases=aliases,
        localized_titles=parse_localized_titles(work, context, schema_packs),
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
            schema_packs=schema_packs,
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
        if work.parent_work_id is not None:
            if work.parent_work_id not in works:
                raise ValueError(
                    f"Source registry `works.{work.id}.parent_work_id` references "
                    f"unknown work `{work.parent_work_id}`."
                )
            if work.parent_work_id == work.id:
                raise ValueError(f"Source registry work `{work.id}` cannot parent itself.")
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

    complete_works: set[str] = set()

    def visit_work(work_id: str, active: set[str]) -> None:
        if work_id in active:
            raise ValueError(
                f"Source registry contains a work-parent cycle involving `{work_id}`."
            )
        if work_id in complete_works:
            return
        active.add(work_id)
        parent = works[work_id].parent_work_id
        if parent:
            visit_work(parent, active)
        active.remove(work_id)
        complete_works.add(work_id)

    for work_id in works:
        visit_work(work_id, set())

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
        parent_segment_id = optional_string(segment, "parent_segment_id", context)
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
            aliases=require_string_list(segment, "aliases", context),
            localized_titles=parse_localized_titles(segment, context, schema_packs),
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

    segment_aliases_by_work: dict[str, set[str]] = {}
    for segment in segments.values():
        aliases = segment_aliases_by_work.setdefault(segment.work_id, set())
        work_segment_ids = {
            item.id.casefold()
            for item in segments.values()
            if item.work_id == segment.work_id
        }
        for alias in segment.aliases:
            validate_id(alias, f"segments.{segment.id}.aliases")
            normalized = alias.casefold()
            if normalized in aliases or normalized in work_segment_ids:
                raise ValueError(
                    f"Source registry segment alias `{alias}` is duplicated or "
                    f"collides inside work `{segment.work_id}`."
                )
            aliases.add(normalized)

    raw_numbering_schemes = require_mapping(
        registry.get("numbering_schemes"), "numbering_schemes"
    )
    numbering_schemes: dict[str, NumberingScheme] = {}
    for scheme_id, raw_scheme in raw_numbering_schemes.items():
        context = f"numbering_schemes.{scheme_id}"
        validate_id(scheme_id, context)
        scheme = require_mapping(raw_scheme, context)
        target_type = require_string(scheme, "target_type", context)
        scope_type = require_string(scheme, "scope_type", context)
        validate_pack_values(
            schema_packs,
            "source.numbering-target-type",
            (target_type,),
            f"{context}.target_type",
        )
        validate_pack_values(
            schema_packs,
            "source.numbering-scope-type",
            (scope_type,),
            f"{context}.scope_type",
        )
        scope_id = optional_string(scheme, "scope_id", context)
        if scope_type == "none" and scope_id is not None:
            raise ValueError(
                f"Source registry `{context}.scope_id` must be omitted for none scope."
            )
        if scope_type == "work":
            if scope_id not in works:
                raise ValueError(
                    f"Source registry `{context}.scope_id` references unknown work "
                    f"`{scope_id}`."
                )
            if target_type != "segment":
                raise ValueError(
                    f"Source registry `{context}` work scope requires segment targets."
                )
        if scope_type == "work-group":
            if scope_id not in work_groups:
                raise ValueError(
                    f"Source registry `{context}.scope_id` references unknown work "
                    f"group `{scope_id}`."
                )
            if target_type != "work":
                raise ValueError(
                    f"Source registry `{context}` work-group scope requires work "
                    "targets."
                )
        raw_entries = scheme.get("entries")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError(
                f"Source registry `{context}.entries` must be a non-empty list."
            )
        entries: list[NumberingEntry] = []
        seen_targets: set[str] = set()
        seen_numbers: set[str] = set()
        targets = works if target_type == "work" else segments
        for index, raw_entry in enumerate(raw_entries):
            entry_context = f"{context}.entries[{index}]"
            entry = require_mapping(raw_entry, entry_context)
            target_id = require_string(entry, "target_id", entry_context)
            if target_id not in targets:
                raise ValueError(
                    f"Source registry `{entry_context}.target_id` references unknown "
                    f"{target_type} `{target_id}`."
                )
            if scope_type == "work" and segments[target_id].work_id != scope_id:
                raise ValueError(
                    f"Source registry `{entry_context}` target falls outside work "
                    f"scope `{scope_id}`."
                )
            if scope_type == "work-group" and not any(
                membership.group_id == scope_id
                for membership in works[target_id].group_memberships
            ):
                raise ValueError(
                    f"Source registry `{entry_context}` target falls outside work "
                    f"group scope `{scope_id}`."
                )
            display_number = require_string(
                entry, "display_number", entry_context
            )
            aliases = require_string_list(entry, "aliases", entry_context)
            number_keys = {display_number.casefold(), *(a.casefold() for a in aliases)}
            if target_id in seen_targets or seen_numbers.intersection(number_keys):
                raise ValueError(
                    f"Source registry `{context}.entries` repeats a target or number."
                )
            seen_targets.add(target_id)
            seen_numbers.update(number_keys)
            entries.append(NumberingEntry(target_id, display_number, aliases))
        numbering_schemes[scheme_id] = NumberingScheme(
            id=scheme_id,
            lifecycle=parse_lifecycle(scheme, context),
            label=require_string(scheme, "label", context),
            target_type=target_type,
            scope_type=scope_type,
            scope_id=scope_id,
            entries=tuple(entries),
        )

    raw_content_groups = require_mapping(
        registry.get("content_groups"), "content_groups"
    )
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
        ordering_mode = require_string(scheme, "ordering_mode", context)
        if ordering_mode not in ORDERING_MODES:
            raise ValueError(
                f"Source registry `{context}.ordering_mode` must be one of: "
                f"{', '.join(sorted(ORDERING_MODES))}."
            )
        raw_entries = scheme.get("entries")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError(
                f"Source registry `{context}.entries` must be a non-empty list."
            )
        entries: list[OrderingEntry] = []
        seen_entry_ids: set[str] = set()
        seen_targets: set[tuple[str, str]] = set()
        seen_ordinals: set[int] = set()
        for index, raw_entry in enumerate(raw_entries):
            entry_context = f"{context}.entries[{index}]"
            entry = require_mapping(raw_entry, entry_context)
            entry_id = require_string(entry, "id", entry_context)
            validate_id(entry_id, f"{entry_context}.id")
            if entry_id in seen_entry_ids:
                raise ValueError(
                    f"Source registry `{context}.entries` repeats entry ID `{entry_id}`."
                )
            seen_entry_ids.add(entry_id)
            target_type = require_string(entry, "target_type", entry_context)
            if target_type not in {"work", "segment", "content-group"}:
                raise ValueError(
                    f"Source registry `{entry_context}.target_type` must be `work` "
                    "`segment`, or `content-group`."
                )
            target_id = require_string(entry, "target_id", entry_context)
            targets = (
                works
                if target_type == "work"
                else segments
                if target_type == "segment"
                else raw_content_groups
            )
            if target_id not in targets:
                raise ValueError(
                    f"Source registry `{entry_context}.target_id` references unknown "
                    f"{target_type} `{target_id}`."
                )
            ordinal = entry.get("ordinal")
            after_entry_ids = require_string_list(
                entry, "after_entry_ids", entry_context
            )
            for predecessor_id in after_entry_ids:
                validate_id(
                    predecessor_id, f"{entry_context}.after_entry_ids"
                )
            if ordering_mode == "total":
                if (
                    isinstance(ordinal, bool)
                    or not isinstance(ordinal, int)
                    or ordinal < 1
                ):
                    raise ValueError(
                        f"Source registry `{entry_context}.ordinal` must be a "
                        "positive integer for total ordering."
                    )
                if after_entry_ids:
                    raise ValueError(
                        f"Source registry `{entry_context}.after_entry_ids` must be "
                        "empty for total ordering."
                    )
            elif ordinal is not None:
                raise ValueError(
                    f"Source registry `{entry_context}.ordinal` must be omitted for "
                    "partial ordering."
                )
            target_key = (target_type, target_id)
            if target_key in seen_targets or (
                ordinal is not None and ordinal in seen_ordinals
            ):
                raise ValueError(
                    f"Source registry `{context}.entries` repeats a target or ordinal."
                )
            seen_targets.add(target_key)
            if ordinal is not None:
                seen_ordinals.add(ordinal)
            entries.append(
                OrderingEntry(
                    entry_id, target_type, target_id, ordinal, after_entry_ids
                )
            )
        if ordering_mode == "partial":
            entry_ids = {entry.id for entry in entries}
            for entry in entries:
                unknown = set(entry.after_entry_ids) - entry_ids
                if unknown:
                    raise ValueError(
                        f"Source registry `{context}` entry `{entry.id}` references "
                        f"unknown predecessors: {', '.join(sorted(unknown))}."
                    )
                if entry.id in entry.after_entry_ids:
                    raise ValueError(
                        f"Source registry `{context}` entry `{entry.id}` cannot "
                        "follow itself."
                    )
            complete_entries: set[str] = set()

            def visit_ordering_entry(entry_id: str, active: set[str]) -> None:
                if entry_id in active:
                    raise ValueError(
                        f"Source registry `{context}` contains a partial-order cycle "
                        f"involving `{entry_id}`."
                    )
                if entry_id in complete_entries:
                    return
                active.add(entry_id)
                entry = next(item for item in entries if item.id == entry_id)
                for predecessor_id in entry.after_entry_ids:
                    visit_ordering_entry(predecessor_id, active)
                active.remove(entry_id)
                complete_entries.add(entry_id)

            for entry in entries:
                visit_ordering_entry(entry.id, set())
        ordering_schemes[scheme_id] = OrderingScheme(
            id=scheme_id,
            label=require_string(scheme, "label", context),
            ordering_type=ordering_type,
            ordering_mode=ordering_mode,
            entries=tuple(
                sorted(entries, key=lambda entry: entry.ordinal or 0)
                if ordering_mode == "total"
                else entries
            ),
        )
    if ordering_schemes:
        validate_pack_values(
            schema_packs,
            "source.ordering-type",
            (scheme.ordering_type for scheme in ordering_schemes.values()),
            "ordering_schemes.*.ordering_type",
        )

    content_groups: dict[str, ContentGroup] = {}
    content_group_aliases: set[str] = set()
    for group_id, raw_group in raw_content_groups.items():
        context = f"content_groups.{group_id}"
        validate_id(group_id, context)
        group = require_mapping(raw_group, context)
        raw_members = group.get("members")
        if not isinstance(raw_members, list) or not raw_members:
            raise ValueError(
                f"Source registry `{context}.members` must be a non-empty list."
            )
        members: list[ContentGroupMember] = []
        seen_member_ids: set[str] = set()
        seen_members: set[tuple[str, str]] = set()
        for index, raw_member in enumerate(raw_members):
            member_context = f"{context}.members[{index}]"
            member = require_mapping(raw_member, member_context)
            member_id = require_string(member, "id", member_context)
            validate_id(member_id, f"{member_context}.id")
            if member_id in seen_member_ids:
                raise ValueError(
                    f"Source registry `{context}.members` repeats ID `{member_id}`."
                )
            seen_member_ids.add(member_id)
            target_type = require_string(
                member, "target_type", member_context
            )
            target_id = require_string(member, "target_id", member_context)
            target_registries = {
                "work": works,
                "segment": segments,
                "content-group": raw_content_groups,
            }
            if target_type not in target_registries:
                raise ValueError(
                    f"Source registry `{member_context}.target_type` must be "
                    "`work`, `segment`, or `content-group`."
                )
            if target_id not in target_registries[target_type]:
                raise ValueError(
                    f"Source registry `{member_context}.target_id` references "
                    f"unknown {target_type} `{target_id}`."
                )
            member_key = (target_type, target_id)
            if member_key in seen_members:
                raise ValueError(
                    f"Source registry `{context}.members` contains duplicates."
                )
            seen_members.add(member_key)
            members.append(ContentGroupMember(member_id, target_type, target_id))
        parent_group_ids = require_string_list(
            group, "parent_group_ids", context
        )
        if group_id in parent_group_ids or len(set(parent_group_ids)) != len(
            parent_group_ids
        ):
            raise ValueError(
                f"Source registry `{context}.parent_group_ids` contains a self "
                "reference or duplicate."
            )
        ordering_scheme_id = optional_string(
            group, "ordering_scheme_id", context
        )
        if ordering_scheme_id is not None:
            if ordering_scheme_id not in ordering_schemes:
                raise ValueError(
                    f"Source registry `{context}.ordering_scheme_id` references "
                    f"unknown ordering scheme `{ordering_scheme_id}`."
                )
            ordered_targets = {
                (entry.target_type, entry.target_id)
                for entry in ordering_schemes[ordering_scheme_id].entries
            }
            if ordered_targets != seen_members:
                raise ValueError(
                    f"Source registry `{context}.ordering_scheme_id` must order "
                    "exactly the group's members."
                )
        aliases = require_string_list(group, "aliases", context)
        for alias in aliases:
            validate_id(alias, f"{context}.aliases")
            normalized = alias.casefold()
            if normalized in content_group_aliases or normalized in {
                value.casefold() for value in raw_content_groups
            }:
                raise ValueError(
                    f"Source registry content-group alias `{alias}` is duplicated "
                    "or collides with a group ID."
                )
            content_group_aliases.add(normalized)
        content_groups[group_id] = ContentGroup(
            id=group_id,
            lifecycle=parse_lifecycle(group, context),
            label=require_string(group, "label", context),
            group_type=require_string(group, "group_type", context),
            members=tuple(members),
            parent_group_ids=parent_group_ids,
            ordering_scheme_id=ordering_scheme_id,
            localized_titles=parse_localized_titles(group, context, schema_packs),
            aliases=aliases,
        )
    if content_groups:
        validate_pack_values(
            schema_packs,
            "source.content-group-type",
            (group.group_type for group in content_groups.values()),
            "content_groups.*.group_type",
        )
    for group in content_groups.values():
        unknown_parents = set(group.parent_group_ids) - set(content_groups)
        if unknown_parents:
            raise ValueError(
                f"Source registry `content_groups.{group.id}.parent_group_ids` "
                f"references unknown groups: {', '.join(sorted(unknown_parents))}."
            )
    complete_content_groups: set[str] = set()

    def visit_content_group(group_id: str, active: set[str]) -> None:
        if group_id in active:
            raise ValueError(
                f"Source registry contains a content-group cycle involving "
                f"`{group_id}`."
            )
        if group_id in complete_content_groups:
            return
        active.add(group_id)
        for parent_id in content_groups[group_id].parent_group_ids:
            visit_content_group(parent_id, active)
        for member in content_groups[group_id].members:
            if member.target_type == "content-group":
                visit_content_group(member.target_id, active)
        active.remove(group_id)
        complete_content_groups.add(group_id)

    for group_id in content_groups:
        visit_content_group(group_id, set())

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
        target_work_id = require_string(mapping, "target_work_id", context)
        if target_work_id not in works:
            raise ValueError(
                f"Source registry `{context}.target_work_id` references an unknown work."
            )
        target_segment_ids = require_string_list(
            mapping, "target_segment_ids", context
        )
        for segment_id in target_segment_ids:
            if (
                segment_id not in segments
                or segments[segment_id].work_id != target_work_id
            ):
                raise ValueError(
                    f"Source registry `{context}.target_segment_ids` references "
                    f"segment `{segment_id}` outside target work `{target_work_id}`."
                )
        raw_basis_inputs = mapping.get("basis_inputs")
        if not isinstance(raw_basis_inputs, list) or not raw_basis_inputs:
            raise ValueError(
                f"Source registry `{context}.basis_inputs` must be a non-empty list."
            )
        basis_inputs: list[AdaptationBasisInput] = []
        seen_basis_works: set[str] = set()
        for basis_index, raw_basis in enumerate(raw_basis_inputs):
            basis_context = f"{context}.basis_inputs[{basis_index}]"
            basis = require_mapping(raw_basis, basis_context)
            work_id = require_string(basis, "work_id", basis_context)
            if work_id not in works:
                raise ValueError(
                    f"Source registry `{basis_context}.work_id` references unknown "
                    f"work `{work_id}`."
                )
            if work_id == target_work_id or work_id in seen_basis_works:
                raise ValueError(
                    f"Source registry `{context}.basis_inputs` repeats a work or "
                    "uses the target as its own basis."
                )
            seen_basis_works.add(work_id)
            segment_ids = require_string_list(
                basis, "segment_ids", basis_context
            )
            for segment_id in segment_ids:
                if (
                    segment_id not in segments
                    or segments[segment_id].work_id != work_id
                ):
                    raise ValueError(
                        f"Source registry `{basis_context}.segment_ids` references "
                        f"segment `{segment_id}` outside work `{work_id}`."
                    )
            basis_inputs.append(
                AdaptationBasisInput(
                    work_id=work_id,
                    segment_ids=segment_ids,
                    basis_role=require_string(basis, "basis_role", basis_context),
                )
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
                basis_inputs=tuple(basis_inputs),
                target_work_id=target_work_id,
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
        validate_pack_values(
            schema_packs,
            "source.adaptation-basis-role",
            (
                basis.basis_role
                for mapping in adaptation_mappings
                for basis in mapping.basis_inputs
            ),
            "adaptation_mappings.*.basis_inputs.*.basis_role",
        )

    raw_territories = require_mapping(registry.get("territories"), "territories")
    territories: dict[str, TerritoryConfig] = {}
    for territory_id, raw_territory in raw_territories.items():
        context = f"territories.{territory_id}"
        validate_id(territory_id, context)
        territory = require_mapping(raw_territory, context)
        raw_codes = require_mapping(territory.get("codes"), f"{context}.codes")
        codes: dict[str, str] = {}
        for scheme_id, code in raw_codes.items():
            validate_id(scheme_id, f"{context}.codes")
            if not isinstance(code, str) or not code.strip():
                raise ValueError(
                    f"Source registry `{context}.codes.{scheme_id}` must be a "
                    "non-empty string."
                )
            codes[scheme_id] = code.strip()
        territories[territory_id] = TerritoryConfig(
            id=territory_id,
            lifecycle=parse_lifecycle(territory, context),
            label=require_string(territory, "label", context),
            territory_type=require_string(territory, "territory_type", context),
            parent_territory_id=optional_string(
                territory, "parent_territory_id", context
            ),
            codes=codes,
        )
    if territories:
        validate_pack_values(
            schema_packs,
            "source.territory-type",
            (territory.territory_type for territory in territories.values()),
            "territories.*.territory_type",
        )
    for territory in territories.values():
        if territory.parent_territory_id is not None:
            if territory.parent_territory_id not in territories:
                raise ValueError(
                    f"Source registry `territories.{territory.id}` references unknown "
                    f"parent `{territory.parent_territory_id}`."
                )
            if territory.parent_territory_id == territory.id:
                raise ValueError(
                    f"Source registry territory `{territory.id}` cannot parent itself."
                )
    for territory_id in territories:
        seen_territories: set[str] = set()
        current_id: str | None = territory_id
        while current_id is not None:
            if current_id in seen_territories:
                raise ValueError(
                    f"Source registry contains a territory cycle involving "
                    f"`{current_id}`."
                )
            seen_territories.add(current_id)
            current_id = territories[current_id].parent_territory_id
    seen_territory_codes: set[tuple[str, str]] = set()
    for territory in territories.values():
        for scheme_id, code in territory.codes.items():
            key = (scheme_id, code.casefold())
            if key in seen_territory_codes:
                raise ValueError(
                    f"Source registry repeats territory code `{scheme_id}:{code}`."
                )
            seen_territory_codes.add(key)

    for owner_context, localized_titles in (
        *((f"works.{work.id}", work.localized_titles) for work in works.values()),
        *(
            (f"segments.{segment.id}", segment.localized_titles)
            for segment in segments.values()
        ),
        *(
            (f"content_groups.{group.id}", group.localized_titles)
            for group in content_groups.values()
        ),
    ):
        for localized_title in localized_titles:
            unknown_territories = set(localized_title.territory_ids) - set(territories)
            if unknown_territories:
                raise ValueError(
                    f"Source registry `{owner_context}.localized_titles` references "
                    f"unknown territories: {', '.join(sorted(unknown_territories))}."
                )

    raw_platforms = require_mapping(registry.get("platforms"), "platforms")
    platforms: dict[str, PlatformConfig] = {}
    platform_aliases: set[str] = set()
    for platform_id, raw_platform in raw_platforms.items():
        context = f"platforms.{platform_id}"
        validate_id(platform_id, context)
        platform = require_mapping(raw_platform, context)
        platform_type = require_string(platform, "platform_type", context)
        aliases = require_string_list(platform, "aliases", context)
        for alias in aliases:
            validate_id(alias, f"{context}.aliases")
            normalized = alias.casefold()
            if normalized in platform_aliases or normalized in {
                value.casefold() for value in raw_platforms
            }:
                raise ValueError(
                    f"Source registry platform alias `{alias}` is duplicated or "
                    "collides with a platform ID."
                )
            platform_aliases.add(normalized)
        platforms[platform_id] = PlatformConfig(
            id=platform_id,
            lifecycle=parse_lifecycle(platform, context),
            label=require_string(platform, "label", context),
            platform_type=platform_type,
            aliases=aliases,
        )
    if platforms:
        validate_pack_values(
            schema_packs,
            "source.platform-type",
            (platform.platform_type for platform in platforms.values()),
            "platforms.*.platform_type",
        )

    manifestation_relationship_types = parse_relationship_types(
        registry.get("manifestation_relationship_types"),
        "manifestation_relationship_types",
    )
    if manifestation_relationship_types:
        validate_pack_values(
            schema_packs,
            "source.manifestation-relationship-type",
            manifestation_relationship_types,
            "manifestation_relationship_types",
        )

    raw_manifestations = require_mapping(
        registry.get("manifestations"), "manifestations"
    )
    manifestations: dict[str, ManifestationConfig] = {}
    manifestation_aliases: set[str] = set()
    for manifestation_id, raw_manifestation in raw_manifestations.items():
        context = f"manifestations.{manifestation_id}"
        validate_id(manifestation_id, context)
        manifestation = require_mapping(raw_manifestation, context)
        work_id = require_string(manifestation, "work_id", context)
        if work_id not in works:
            raise ValueError(
                f"Source registry `{context}.work_id` references unknown work "
                f"`{work_id}`."
            )
        segment_ids = require_string_list(
            manifestation, "segment_ids", context
        )
        for segment_id in segment_ids:
            if (
                segment_id not in segments
                or segments[segment_id].work_id != work_id
            ):
                raise ValueError(
                    f"Source registry `{context}.segment_ids` references segment "
                    f"`{segment_id}` outside work `{work_id}`."
                )
        manifestation_type = require_string(
            manifestation, "manifestation_type", context
        )
        container_format_ids = require_string_list(
            manifestation, "container_format_ids", context
        )
        unknown_formats = set(container_format_ids) - set(container_formats)
        if unknown_formats:
            raise ValueError(
                f"Source registry `{context}.container_format_ids` references unknown "
                f"formats: {', '.join(sorted(unknown_formats))}."
            )
        aliases = require_string_list(manifestation, "aliases", context)
        for alias in aliases:
            validate_id(alias, f"{context}.aliases")
            normalized = alias.casefold()
            if normalized in manifestation_aliases or normalized in {
                value.casefold() for value in raw_manifestations
            }:
                raise ValueError(
                    f"Source registry manifestation alias `{alias}` is duplicated or "
                    "collides with a manifestation ID."
                )
            manifestation_aliases.add(normalized)
        language_tags = require_string_list(
            manifestation, "language_tags", context
        )
        for language_tag in language_tags:
            validate_language_tag(language_tag, f"{context}.language_tags")
        territory_ids = require_string_list(
            manifestation, "territory_ids", context
        )
        unknown_territories = set(territory_ids) - set(territories)
        if unknown_territories:
            raise ValueError(
                f"Source registry `{context}.territory_ids` references unknown "
                f"territories: {', '.join(sorted(unknown_territories))}."
            )
        localized_titles = parse_localized_titles(
            manifestation, context, schema_packs
        )
        for localized_title in localized_titles:
            unknown_territories = set(localized_title.territory_ids) - set(territories)
            if unknown_territories:
                raise ValueError(
                    f"Source registry `{context}.localized_titles` references unknown "
                    f"territories: {', '.join(sorted(unknown_territories))}."
                )
        manifestations[manifestation_id] = ManifestationConfig(
            id=manifestation_id,
            lifecycle=parse_lifecycle(manifestation, context),
            label=require_string(manifestation, "label", context),
            work_id=work_id,
            segment_ids=segment_ids,
            manifestation_type=manifestation_type,
            language_tags=language_tags,
            territory_ids=territory_ids,
            container_format_ids=container_format_ids,
            localized_titles=localized_titles,
            aliases=aliases,
        )
    if manifestations:
        validate_pack_values(
            schema_packs,
            "source.manifestation-type",
            (
                manifestation.manifestation_type
                for manifestation in manifestations.values()
            ),
            "manifestations.*.manifestation_type",
        )

    raw_manifestation_relationships = registry.get("manifestation_relationships")
    if not isinstance(raw_manifestation_relationships, list):
        raise ValueError(
            "Source registry `manifestation_relationships` must be a list."
        )
    manifestation_relationships: list[ManifestationRelationship] = []
    seen_manifestation_relationship_ids: set[str] = set()
    for index, raw_relationship in enumerate(raw_manifestation_relationships):
        context = f"manifestation_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_manifestation_relationship_ids:
            raise ValueError(
                f"Source registry manifestation relationship ID `{relationship_id}` "
                "is duplicated."
            )
        seen_manifestation_relationship_ids.add(relationship_id)
        source_id = require_string(
            relationship, "source_manifestation_id", context
        )
        target_id = require_string(
            relationship, "target_manifestation_id", context
        )
        relationship_type = require_string(
            relationship, "relationship_type", context
        )
        if source_id not in manifestations or target_id not in manifestations:
            raise ValueError(
                f"Source registry `{context}` references an unknown manifestation."
            )
        if source_id == target_id:
            raise ValueError(
                f"Source registry `{context}` cannot relate a manifestation to itself."
            )
        if relationship_type not in manifestation_relationship_types:
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
        manifestation_relationships.append(
            ManifestationRelationship(
                relationship_id, source_id, relationship_type, target_id, status
            )
        )

    raw_manifestation_segment_mappings = registry.get(
        "manifestation_segment_mappings"
    )
    if not isinstance(raw_manifestation_segment_mappings, list):
        raise ValueError(
            "Source registry `manifestation_segment_mappings` must be a list."
        )
    manifestation_segment_mappings: list[ManifestationSegmentMapping] = []
    seen_manifestation_mapping_ids: set[str] = set()
    related_manifestation_pairs = {
        frozenset(
            (
                relationship.source_manifestation_id,
                relationship.target_manifestation_id,
            )
        )
        for relationship in manifestation_relationships
    }
    for index, raw_mapping in enumerate(raw_manifestation_segment_mappings):
        context = f"manifestation_segment_mappings[{index}]"
        mapping = require_mapping(raw_mapping, context)
        mapping_id = require_string(mapping, "id", context)
        validate_id(mapping_id, f"{context}.id")
        if mapping_id in seen_manifestation_mapping_ids:
            raise ValueError(
                f"Source registry manifestation segment mapping ID `{mapping_id}` "
                "is duplicated."
            )
        seen_manifestation_mapping_ids.add(mapping_id)
        source_id = require_string(
            mapping, "source_manifestation_id", context
        )
        target_id = require_string(
            mapping, "target_manifestation_id", context
        )
        if source_id not in manifestations or target_id not in manifestations:
            raise ValueError(
                f"Source registry `{context}` references an unknown manifestation."
            )
        if source_id == target_id:
            raise ValueError(
                f"Source registry `{context}` cannot map a manifestation to itself."
            )
        if manifestations[source_id].work_id != manifestations[target_id].work_id:
            raise ValueError(
                f"Source registry `{context}` must map manifestations of the same "
                "work."
            )
        if frozenset((source_id, target_id)) not in related_manifestation_pairs:
            raise ValueError(
                f"Source registry `{context}` requires a manifestation relationship "
                "between its source and target."
            )
        source_segment_ids = require_string_list(
            mapping, "source_segment_ids", context
        )
        target_segment_ids = require_string_list(
            mapping, "target_segment_ids", context
        )
        work_id = manifestations[source_id].work_id
        for field_name, values, manifestation_id in (
            ("source_segment_ids", source_segment_ids, source_id),
            ("target_segment_ids", target_segment_ids, target_id),
        ):
            for segment_id in values:
                if (
                    segment_id not in segments
                    or segments[segment_id].work_id != work_id
                    or (
                        manifestations[manifestation_id].segment_ids
                        and segment_id
                        not in manifestations[manifestation_id].segment_ids
                    )
                ):
                    raise ValueError(
                        f"Source registry `{context}.{field_name}` references segment "
                        f"`{segment_id}` outside manifestation scope."
                    )
        mapping_type = require_string(mapping, "mapping_type", context)
        if mapping_type == "omitted":
            valid_shape = bool(source_segment_ids) and not target_segment_ids
        elif mapping_type == "added":
            valid_shape = not source_segment_ids and bool(target_segment_ids)
        else:
            valid_shape = bool(source_segment_ids) and bool(target_segment_ids)
        if not valid_shape:
            raise ValueError(
                f"Source registry `{context}` has segment lists incompatible with "
                f"mapping type `{mapping_type}`."
            )
        status = require_string(mapping, "status", context)
        if status not in membership_statuses:
            raise ValueError(
                f"Source registry `{context}.status` must be one of: "
                f"{', '.join(sorted(membership_statuses))}."
            )
        manifestation_segment_mappings.append(
            ManifestationSegmentMapping(
                mapping_id,
                source_id,
                source_segment_ids,
                target_id,
                target_segment_ids,
                mapping_type,
                status,
            )
        )
    if manifestation_segment_mappings:
        validate_pack_values(
            schema_packs,
            "source.manifestation-segment-mapping-type",
            (
                mapping.mapping_type
                for mapping in manifestation_segment_mappings
            ),
            "manifestation_segment_mappings.*.mapping_type",
        )

    raw_release_components = require_mapping(
        registry.get("release_components"), "release_components"
    )
    release_components: dict[str, ReleaseComponent] = {}
    for component_id, raw_component in raw_release_components.items():
        context = f"release_components.{component_id}"
        validate_id(component_id, context)
        component = require_mapping(raw_component, context)
        manifestation_id = optional_string(
            component, "manifestation_id", context
        )
        if manifestation_id is not None and manifestation_id not in manifestations:
            raise ValueError(
                f"Source registry `{context}.manifestation_id` references unknown "
                f"manifestation `{manifestation_id}`."
        )
        segment_ids = require_string_list(component, "segment_ids", context)
        for segment_id in segment_ids:
            if segment_id not in segments:
                raise ValueError(
                    f"Source registry `{context}.segment_ids` references segment "
                    f"`{segment_id}`."
                )
            if manifestation_id is not None:
                manifestation = manifestations[manifestation_id]
                if (
                    segments[segment_id].work_id != manifestation.work_id
                    or (
                        manifestation.segment_ids
                        and segment_id not in manifestation.segment_ids
                    )
                ):
                    raise ValueError(
                        f"Source registry `{context}.segment_ids` references segment "
                        f"`{segment_id}` outside manifestation scope."
                    )
        language_tag = optional_string(component, "language_tag", context)
        if language_tag is not None:
            validate_language_tag(language_tag, f"{context}.language_tag")
        release_components[component_id] = ReleaseComponent(
            id=component_id,
            lifecycle=parse_lifecycle(component, context),
            label=require_string(component, "label", context),
            manifestation_id=manifestation_id,
            component_type=require_string(component, "component_type", context),
            segment_ids=segment_ids,
            language_tag=language_tag,
        )
    if release_components:
        validate_pack_values(
            schema_packs,
            "source.release-component-type",
            (component.component_type for component in release_components.values()),
            "release_components.*.component_type",
        )

    release_component_relationship_types = parse_relationship_types(
        registry.get("release_component_relationship_types"),
        "release_component_relationship_types",
    )
    if release_component_relationship_types:
        validate_pack_values(
            schema_packs,
            "source.release-component-relationship-type",
            release_component_relationship_types,
            "release_component_relationship_types",
        )
    raw_component_relationships = registry.get(
        "release_component_relationships"
    )
    if not isinstance(raw_component_relationships, list):
        raise ValueError(
            "Source registry `release_component_relationships` must be a list."
        )
    release_component_relationships: list[ReleaseComponentRelationship] = []
    seen_component_relationship_ids: set[str] = set()
    for index, raw_relationship in enumerate(raw_component_relationships):
        context = f"release_component_relationships[{index}]"
        relationship = require_mapping(raw_relationship, context)
        relationship_id = require_string(relationship, "id", context)
        validate_id(relationship_id, f"{context}.id")
        if relationship_id in seen_component_relationship_ids:
            raise ValueError(
                f"Source registry release-component relationship ID "
                f"`{relationship_id}` is duplicated."
            )
        seen_component_relationship_ids.add(relationship_id)
        source_component_id = require_string(
            relationship, "source_component_id", context
        )
        target_component_id = require_string(
            relationship, "target_component_id", context
        )
        if (
            source_component_id not in release_components
            or target_component_id not in release_components
        ):
            raise ValueError(
                f"Source registry `{context}` references an unknown release "
                "component."
            )
        if source_component_id == target_component_id:
            raise ValueError(
                f"Source registry `{context}` cannot relate a component to itself."
            )
        relationship_type = require_string(
            relationship, "relationship_type", context
        )
        if relationship_type not in release_component_relationship_types:
            raise ValueError(
                f"Source registry `{context}.relationship_type` references unknown "
                f"type `{relationship_type}`."
            )
        release_component_relationships.append(
            ReleaseComponentRelationship(
                relationship_id,
                source_component_id,
                relationship_type,
                target_component_id,
            )
        )

    raw_release_packages = require_mapping(
        registry.get("release_packages"), "release_packages"
    )
    release_packages: dict[str, ReleasePackage] = {}
    release_package_aliases: set[str] = set()
    for package_id, raw_package in raw_release_packages.items():
        context = f"release_packages.{package_id}"
        validate_id(package_id, context)
        package = require_mapping(raw_package, context)
        manifestation_ids = require_string_list(
            package, "manifestation_ids", context
        )
        unknown_manifestations = set(manifestation_ids) - set(manifestations)
        if unknown_manifestations:
            raise ValueError(
                f"Source registry `{context}.manifestation_ids` references unknown "
                f"manifestations: {', '.join(sorted(unknown_manifestations))}."
            )
        segment_ids = require_string_list(package, "segment_ids", context)
        for segment_id in segment_ids:
            if segment_id not in segments:
                raise ValueError(
                    f"Source registry `{context}.segment_ids` references unknown "
                    f"segment `{segment_id}`."
                )
        component_ids = require_string_list(
            package, "release_component_ids", context
        )
        component_manifestation_ids: set[str] = set()
        for component_id in component_ids:
            if component_id not in release_components:
                raise ValueError(
                    f"Source registry `{context}.release_component_ids` references "
                    f"unknown component `{component_id}`."
                )
            component_manifestation_id = release_components[
                component_id
            ].manifestation_id
            if component_manifestation_id is not None:
                component_manifestation_ids.add(component_manifestation_id)
            if (
                manifestation_ids
                and component_manifestation_id is not None
                and component_manifestation_id not in manifestation_ids
            ):
                raise ValueError(
                    f"Source registry `{context}` component `{component_id}` belongs "
                    "to a manifestation outside the package."
                )
        effective_manifestation_ids = set(manifestation_ids) | component_manifestation_ids
        package_work_ids = {
            manifestations[manifestation_id].work_id
            for manifestation_id in effective_manifestation_ids
        }
        for segment_id in segment_ids:
            if package_work_ids and segments[segment_id].work_id not in package_work_ids:
                raise ValueError(
                    f"Source registry `{context}.segment_ids` references segment "
                    f"`{segment_id}` outside the package manifestations."
                )
        if not manifestation_ids and not segment_ids and not component_ids:
            raise ValueError(
                f"Source registry `{context}` must contain a manifestation, segment, "
                "or release component."
            )
        container_format_ids = require_string_list(
            package, "container_format_ids", context
        )
        unknown_formats = set(container_format_ids) - set(container_formats)
        if unknown_formats:
            raise ValueError(
                f"Source registry `{context}.container_format_ids` references unknown "
                f"formats: {', '.join(sorted(unknown_formats))}."
            )
        aliases = require_string_list(package, "aliases", context)
        for alias in aliases:
            validate_id(alias, f"{context}.aliases")
            normalized = alias.casefold()
            if normalized in release_package_aliases or normalized in {
                value.casefold() for value in raw_release_packages
            }:
                raise ValueError(
                    f"Source registry release-package alias `{alias}` is duplicated "
                    "or collides with a package ID."
                )
            release_package_aliases.add(normalized)
        localized_titles = parse_localized_titles(package, context, schema_packs)
        for localized_title in localized_titles:
            unknown_territories = set(localized_title.territory_ids) - set(territories)
            if unknown_territories:
                raise ValueError(
                    f"Source registry `{context}.localized_titles` references unknown "
                    f"territories: {', '.join(sorted(unknown_territories))}."
                )
        release_packages[package_id] = ReleasePackage(
            id=package_id,
            lifecycle=parse_lifecycle(package, context),
            label=require_string(package, "label", context),
            package_type=require_string(package, "package_type", context),
            manifestation_ids=manifestation_ids,
            segment_ids=segment_ids,
            release_component_ids=component_ids,
            container_format_ids=container_format_ids,
            localized_titles=localized_titles,
            aliases=aliases,
        )
    if release_packages:
        validate_pack_values(
            schema_packs,
            "source.release-package-type",
            (package.package_type for package in release_packages.values()),
            "release_packages.*.package_type",
        )

    packages_by_component: dict[str, set[str]] = {
        component_id: set() for component_id in release_components
    }
    for package in release_packages.values():
        for component_id in package.release_component_ids:
            packages_by_component[component_id].add(package.id)
    for component in release_components.values():
        if (
            component.manifestation_id is None
            and not packages_by_component[component.id]
        ):
            raise ValueError(
                f"Source registry release component `{component.id}` has no "
                "manifestation and is not included in a release package."
            )
        for package_id in packages_by_component[component.id]:
            package = release_packages[package_id]
            package_work_ids = {
                manifestations[manifestation_id].work_id
                for manifestation_id in package.manifestation_ids
            } | {
                segments[segment_id].work_id
                for segment_id in package.segment_ids
            }
            if component.manifestation_id is not None:
                package_work_ids.add(
                    manifestations[component.manifestation_id].work_id
                )
            component_work_ids = {
                segments[segment_id].work_id
                for segment_id in component.segment_ids
            }
            if package_work_ids and not component_work_ids.issubset(
                package_work_ids
            ):
                raise ValueError(
                    f"Source registry release component `{component.id}` has segment "
                    f"scope outside package `{package_id}`."
                )

    def release_package_work_ids(package_id: str) -> set[str]:
        package = release_packages[package_id]
        work_ids = {
            manifestations[manifestation_id].work_id
            for manifestation_id in package.manifestation_ids
        }
        work_ids.update(
            segments[segment_id].work_id for segment_id in package.segment_ids
        )
        for component_id in package.release_component_ids:
            component = release_components[component_id]
            if component.manifestation_id is not None:
                work_ids.add(
                    manifestations[component.manifestation_id].work_id
                )
            work_ids.update(
                segments[segment_id].work_id
                for segment_id in component.segment_ids
            )
        return work_ids

    def validate_distribution_scope(
        subject_type: str,
        subject_id: str,
        segment_ids: tuple[str, ...],
        context: str,
    ) -> None:
        validate_pack_values(
            schema_packs,
            "source.distribution-subject-type",
            (subject_type,),
            f"{context}.subject_type",
        )
        if subject_type == "manifestation":
            if subject_id not in manifestations:
                raise ValueError(
                    f"Source registry `{context}.subject_id` references unknown "
                    f"manifestation `{subject_id}`."
                )
            subject = manifestations[subject_id]
            for segment_id in segment_ids:
                if (
                    segment_id not in segments
                    or segments[segment_id].work_id != subject.work_id
                    or (
                        subject.segment_ids
                        and segment_id not in subject.segment_ids
                    )
                ):
                    raise ValueError(
                        f"Source registry `{context}.segment_ids` references segment "
                        f"`{segment_id}` outside manifestation scope."
                    )
            return
        if subject_id not in release_packages:
            raise ValueError(
                f"Source registry `{context}.subject_id` references unknown release "
                f"package `{subject_id}`."
            )
        package = release_packages[subject_id]
        package_work_ids = release_package_work_ids(subject_id)
        package_segment_ids = set(package.segment_ids)
        for segment_id in segment_ids:
            if segment_id not in segments:
                raise ValueError(
                    f"Source registry `{context}.segment_ids` references unknown "
                    f"segment `{segment_id}`."
                )
            if package_segment_ids:
                valid = segment_id in package_segment_ids
            else:
                valid = segments[segment_id].work_id in package_work_ids
            if not valid:
                raise ValueError(
                    f"Source registry `{context}.segment_ids` references segment "
                    f"`{segment_id}` outside release-package scope."
                )

    raw_release_runs = require_mapping(
        registry.get("release_runs"), "release_runs"
    )
    release_runs: dict[str, ReleaseRun] = {}
    for run_id, raw_run in raw_release_runs.items():
        context = f"release_runs.{run_id}"
        validate_id(run_id, context)
        run = require_mapping(raw_run, context)
        subject_type = require_string(run, "subject_type", context)
        subject_id = require_string(run, "subject_id", context)
        segment_ids = require_string_list(run, "segment_ids", context)
        if not segment_ids or len(set(segment_ids)) != len(segment_ids):
            raise ValueError(
                f"Source registry `{context}.segment_ids` must be a non-empty "
                "duplicate-free list."
            )
        validate_distribution_scope(
            subject_type, subject_id, segment_ids, context
        )
        ordering_scheme_id = require_string(
            run, "ordering_scheme_id", context
        )
        if ordering_scheme_id not in ordering_schemes:
            raise ValueError(
                f"Source registry `{context}.ordering_scheme_id` references unknown "
                f"ordering scheme `{ordering_scheme_id}`."
            )
        ordering = ordering_schemes[ordering_scheme_id]
        ordered_segment_ids = {
            entry.target_id
            for entry in ordering.entries
            if entry.target_type == "segment"
        }
        if (
            ordering.ordering_mode != "total"
            or len(ordered_segment_ids) != len(ordering.entries)
            or ordered_segment_ids != set(segment_ids)
        ):
            raise ValueError(
                f"Source registry `{context}.ordering_scheme_id` must be a total "
                "ordering of exactly the run's segments."
            )
        raw_phases = run.get("phases")
        if not isinstance(raw_phases, list) or not raw_phases:
            raise ValueError(
                f"Source registry `{context}.phases` must be a non-empty list."
            )
        phases: list[ReleaseRunPhase] = []
        seen_phase_ids: set[str] = set()
        flattened_phase_segments: list[str] = []
        for index, raw_phase in enumerate(raw_phases):
            phase_context = f"{context}.phases[{index}]"
            phase = require_mapping(raw_phase, phase_context)
            phase_id = require_string(phase, "id", phase_context)
            validate_id(phase_id, f"{phase_context}.id")
            if phase_id in seen_phase_ids:
                raise ValueError(
                    f"Source registry `{context}.phases` repeats phase ID "
                    f"`{phase_id}`."
                )
            seen_phase_ids.add(phase_id)
            phase_segment_ids = require_string_list(
                phase, "segment_ids", phase_context
            )
            if not phase_segment_ids:
                raise ValueError(
                    f"Source registry `{phase_context}.segment_ids` must not be "
                    "empty."
                )
            flattened_phase_segments.extend(phase_segment_ids)
            first_release_window = parse_temporal_window(
                phase, "first_release_window", phase_context, schema_packs
            )
            if first_release_window is None:
                raise ValueError(
                    f"Source registry `{phase_context}.first_release_window` is "
                    "required."
                )
            cadence = require_mapping(
                phase.get("cadence"), f"{phase_context}.cadence"
            )
            cadence_unit = require_string(
                cadence, "unit", f"{phase_context}.cadence"
            )
            cadence_interval = cadence.get("interval")
            if (
                isinstance(cadence_interval, bool)
                or not isinstance(cadence_interval, int)
                or cadence_interval < 1
            ):
                raise ValueError(
                    f"Source registry `{phase_context}.cadence.interval` must be "
                    "a positive integer."
                )
            validate_pack_values(
                schema_packs,
                "source.release-run-cadence-unit",
                (cadence_unit,),
                f"{phase_context}.cadence.unit",
            )
            batch_size = phase.get("batch_size")
            if (
                isinstance(batch_size, bool)
                or not isinstance(batch_size, int)
                or batch_size < 1
                or batch_size > len(phase_segment_ids)
            ):
                raise ValueError(
                    f"Source registry `{phase_context}.batch_size` must be between "
                    "1 and the number of phase segments."
                )
            phases.append(
                ReleaseRunPhase(
                    phase_id,
                    phase_segment_ids,
                    first_release_window,
                    cadence_unit,
                    cadence_interval,
                    batch_size,
                )
            )
        ordered_run_segments = tuple(
            entry.target_id for entry in ordering.entries
        )
        if tuple(flattened_phase_segments) != ordered_run_segments:
            raise ValueError(
                f"Source registry `{context}.phases` must partition the run's "
                "segments exactly in ordering-scheme order."
            )
        territory_ids = require_string_list(run, "territory_ids", context)
        unknown_territories = set(territory_ids) - set(territories)
        if unknown_territories:
            raise ValueError(
                f"Source registry `{context}.territory_ids` references unknown "
                f"territories: {', '.join(sorted(unknown_territories))}."
            )
        platform_ids = require_string_list(run, "platform_ids", context)
        unknown_platforms = set(platform_ids) - set(platforms)
        if unknown_platforms:
            raise ValueError(
                f"Source registry `{context}.platform_ids` references unknown "
                f"platforms: {', '.join(sorted(unknown_platforms))}."
            )
        raw_exceptions = run.get("exceptions")
        if not isinstance(raw_exceptions, list):
            raise ValueError(
                f"Source registry `{context}.exceptions` must be a list."
            )
        exceptions: list[ReleaseRunException] = []
        seen_exceptions: set[tuple[str, str]] = set()
        for index, raw_exception in enumerate(raw_exceptions):
            exception_context = f"{context}.exceptions[{index}]"
            exception = require_mapping(raw_exception, exception_context)
            exception_type = require_string(
                exception, "exception_type", exception_context
            )
            validate_pack_values(
                schema_packs,
                "source.release-run-exception-type",
                (exception_type,),
                f"{exception_context}.exception_type",
            )
            segment_id = require_string(
                exception, "segment_id", exception_context
            )
            if segment_id not in segment_ids:
                raise ValueError(
                    f"Source registry `{exception_context}.segment_id` falls outside "
                    "the release run."
                )
            if (exception_type, segment_id) in seen_exceptions:
                raise ValueError(
                    f"Source registry `{context}.exceptions` repeats an exception."
                )
            seen_exceptions.add((exception_type, segment_id))
            release_window = parse_temporal_window(
                exception,
                "release_window",
                exception_context,
                schema_packs,
            )
            interval_count = exception.get("interval_count")
            if interval_count is not None and (
                isinstance(interval_count, bool)
                or not isinstance(interval_count, int)
                or interval_count < 1
            ):
                raise ValueError(
                    f"Source registry `{exception_context}.interval_count` must be "
                    "a positive integer when present."
                )
            if exception_type == "rescheduled":
                valid_shape = release_window is not None and interval_count is None
            elif exception_type == "pause":
                valid_shape = release_window is None and interval_count is not None
            else:
                valid_shape = release_window is None and interval_count is None
            if not valid_shape:
                raise ValueError(
                    f"Source registry `{exception_context}` fields are incompatible "
                    f"with exception type `{exception_type}`."
                )
            exceptions.append(
                ReleaseRunException(
                    exception_type,
                    segment_id,
                    release_window,
                    interval_count,
                )
            )
        release_runs[run_id] = ReleaseRun(
            id=run_id,
            lifecycle=parse_lifecycle(run, context),
            label=require_string(run, "label", context),
            subject_type=subject_type,
            subject_id=subject_id,
            segment_ids=segment_ids,
            ordering_scheme_id=ordering_scheme_id,
            release_event_type=require_string(
                run, "release_event_type", context
            ),
            phases=tuple(phases),
            territory_ids=territory_ids,
            platform_ids=platform_ids,
            availability_status=require_string(
                run, "availability_status", context
            ),
            exceptions=tuple(exceptions),
        )
    if release_runs:
        validate_pack_values(
            schema_packs,
            "source.release-event-type",
            (run.release_event_type for run in release_runs.values()),
            "release_runs.*.release_event_type",
        )
        validate_pack_values(
            schema_packs,
            "source.availability-status",
            (run.availability_status for run in release_runs.values()),
            "release_runs.*.availability_status",
        )

    raw_release_events = require_mapping(
        registry.get("release_events"), "release_events"
    )
    release_events: dict[str, ReleaseEvent] = {}
    for event_id, raw_event in raw_release_events.items():
        context = f"release_events.{event_id}"
        validate_id(event_id, context)
        event = require_mapping(raw_event, context)
        subject_type = require_string(event, "subject_type", context)
        subject_id = require_string(event, "subject_id", context)
        segment_ids = require_string_list(event, "segment_ids", context)
        validate_distribution_scope(
            subject_type, subject_id, segment_ids, context
        )
        platform_ids = require_string_list(event, "platform_ids", context)
        unknown_platforms = set(platform_ids) - set(platforms)
        if unknown_platforms:
            raise ValueError(
                f"Source registry `{context}.platform_ids` references unknown "
                f"platforms: {', '.join(sorted(unknown_platforms))}."
            )
        territory_ids = require_string_list(event, "territory_ids", context)
        unknown_territories = set(territory_ids) - set(territories)
        if unknown_territories:
            raise ValueError(
                f"Source registry `{context}.territory_ids` references unknown "
                f"territories: {', '.join(sorted(unknown_territories))}."
            )
        release_run_id = optional_string(event, "release_run_id", context)
        if release_run_id is not None:
            if release_run_id not in release_runs:
                raise ValueError(
                    f"Source registry `{context}.release_run_id` references unknown "
                    f"release run `{release_run_id}`."
                )
            release_run = release_runs[release_run_id]
            if (
                release_run.subject_type != subject_type
                or release_run.subject_id != subject_id
                or not set(segment_ids).issubset(release_run.segment_ids)
                or (
                    release_run.platform_ids
                    and not set(platform_ids).issubset(release_run.platform_ids)
                )
                or (
                    release_run.territory_ids
                    and not set(territory_ids).issubset(
                        release_run.territory_ids
                    )
                )
            ):
                raise ValueError(
                    f"Source registry `{context}` falls outside its release run."
                )
        release_events[event_id] = ReleaseEvent(
            id=event_id,
            lifecycle=parse_lifecycle(event, context),
            label=require_string(event, "label", context),
            subject_type=subject_type,
            subject_id=subject_id,
            segment_ids=segment_ids,
            release_event_type=require_string(
                event, "release_event_type", context
            ),
            release_window=parse_temporal_window(
                event, "release_window", context, schema_packs
            ),
            territory_ids=territory_ids,
            platform_ids=platform_ids,
            availability_status=require_string(
                event, "availability_status", context
            ),
            release_run_id=release_run_id,
        )
    if release_events:
        validate_pack_values(
            schema_packs,
            "source.release-event-type",
            (event.release_event_type for event in release_events.values()),
            "release_events.*.release_event_type",
        )
        validate_pack_values(
            schema_packs,
            "source.availability-status",
            (event.availability_status for event in release_events.values()),
            "release_events.*.availability_status",
        )

    raw_catalog_placements = require_mapping(
        registry.get("catalog_placements"), "catalog_placements"
    )
    catalog_placements: dict[str, CatalogPlacement] = {}
    for placement_id, raw_placement in raw_catalog_placements.items():
        context = f"catalog_placements.{placement_id}"
        validate_id(placement_id, context)
        placement = require_mapping(raw_placement, context)
        platform_id = require_string(placement, "platform_id", context)
        if platform_id not in platforms:
            raise ValueError(
                f"Source registry `{context}.platform_id` references unknown platform "
                f"`{platform_id}`."
            )
        target_type = require_string(placement, "target_type", context)
        target_id = require_string(placement, "target_id", context)
        validate_pack_values(
            schema_packs,
            "source.catalog-target-type",
            (target_type,),
            f"{context}.target_type",
        )
        catalog_targets = {
            "work": works,
            "segment": segments,
            "content-group": content_groups,
            "manifestation": manifestations,
            "release-package": release_packages,
        }
        if target_id not in catalog_targets[target_type]:
            raise ValueError(
                f"Source registry `{context}.target_id` references unknown "
                f"{target_type} `{target_id}`."
            )
        ordinal = placement.get("ordinal")
        if ordinal is not None and (
            isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1
        ):
            raise ValueError(
                f"Source registry `{context}.ordinal` must be a positive integer "
                "when present."
            )
        localized_titles = parse_localized_titles(
            placement, context, schema_packs
        )
        for localized_title in localized_titles:
            unknown_territories = set(localized_title.territory_ids) - set(
                territories
            )
            if unknown_territories:
                raise ValueError(
                    f"Source registry `{context}.localized_titles` references "
                    f"unknown territories: "
                    f"{', '.join(sorted(unknown_territories))}."
                )
        catalog_placements[placement_id] = CatalogPlacement(
            id=placement_id,
            lifecycle=parse_lifecycle(placement, context),
            label=require_string(placement, "label", context),
            platform_id=platform_id,
            placement_type=require_string(placement, "placement_type", context),
            parent_placement_id=optional_string(
                placement, "parent_placement_id", context
            ),
            target_type=target_type,
            target_id=target_id,
            ordinal=ordinal,
            provider_key=optional_string(placement, "provider_key", context),
            localized_titles=localized_titles,
        )
    for placement in catalog_placements.values():
        parent_id = placement.parent_placement_id
        if parent_id is not None:
            if parent_id not in catalog_placements:
                raise ValueError(
                    f"Source registry `catalog_placements.{placement.id}` references "
                    f"unknown parent `{parent_id}`."
                )
            if parent_id == placement.id:
                raise ValueError(
                    f"Source registry catalog placement `{placement.id}` cannot "
                    "parent itself."
                )
            if catalog_placements[parent_id].platform_id != placement.platform_id:
                raise ValueError(
                    f"Source registry catalog placement `{placement.id}` and its "
                    "parent must belong to the same platform."
                )
    complete_placements: set[str] = set()

    def visit_placement(placement_id: str, active: set[str]) -> None:
        if placement_id in active:
            raise ValueError(
                f"Source registry contains a catalog-placement cycle involving "
                f"`{placement_id}`."
            )
        if placement_id in complete_placements:
            return
        active.add(placement_id)
        parent = catalog_placements[placement_id].parent_placement_id
        if parent:
            visit_placement(parent, active)
        active.remove(placement_id)
        complete_placements.add(placement_id)

    for placement_id in catalog_placements:
        visit_placement(placement_id, set())
    if catalog_placements:
        validate_pack_values(
            schema_packs,
            "source.catalog-placement-type",
            (placement.placement_type for placement in catalog_placements.values()),
            "catalog_placements.*.placement_type",
        )

    raw_platform_offerings = require_mapping(
        registry.get("platform_offerings"), "platform_offerings"
    )
    platform_offerings: dict[str, PlatformOffering] = {}
    for offering_id, raw_offering in raw_platform_offerings.items():
        context = f"platform_offerings.{offering_id}"
        validate_id(offering_id, context)
        offering = require_mapping(raw_offering, context)
        platform_id = require_string(offering, "platform_id", context)
        subject_type = require_string(offering, "subject_type", context)
        subject_id = require_string(offering, "subject_id", context)
        segment_ids = require_string_list(offering, "segment_ids", context)
        validate_distribution_scope(
            subject_type, subject_id, segment_ids, context
        )
        release_event_id = optional_string(
            offering, "release_event_id", context
        )
        if platform_id not in platforms:
            raise ValueError(
                f"Source registry `{context}.platform_id` references unknown platform "
                f"`{platform_id}`."
            )
        if release_event_id is not None:
            if release_event_id not in release_events:
                raise ValueError(
                    f"Source registry `{context}.release_event_id` references unknown "
                    f"release event `{release_event_id}`."
                )
            event = release_events[release_event_id]
            if (
                event.subject_type != subject_type
                or event.subject_id != subject_id
                or platform_id not in event.platform_ids
                or (
                    event.segment_ids
                    and not set(segment_ids).issubset(event.segment_ids)
                )
            ):
                raise ValueError(
                    f"Source registry `{context}` release event does not match its "
                    "subject, segment scope, and platform."
                )
        placement_ids = require_string_list(
            offering, "catalog_placement_ids", context
        )
        for placement_id in placement_ids:
            if (
                placement_id not in catalog_placements
                or catalog_placements[placement_id].platform_id != platform_id
            ):
                raise ValueError(
                    f"Source registry `{context}.catalog_placement_ids` references "
                    f"placement `{placement_id}` outside platform `{platform_id}`."
                )
        territory_ids = require_string_list(offering, "territory_ids", context)
        unknown_territories = set(territory_ids) - set(territories)
        if unknown_territories:
            raise ValueError(
                f"Source registry `{context}.territory_ids` references unknown "
                f"territories: {', '.join(sorted(unknown_territories))}."
            )
        language_tags = require_string_list(offering, "language_tags", context)
        for language_tag in language_tags:
            validate_language_tag(language_tag, f"{context}.language_tags")
        platform_offerings[offering_id] = PlatformOffering(
            id=offering_id,
            lifecycle=parse_lifecycle(offering, context),
            label=require_string(offering, "label", context),
            platform_id=platform_id,
            subject_type=subject_type,
            subject_id=subject_id,
            segment_ids=segment_ids,
            release_event_id=release_event_id,
            offering_type=require_string(offering, "offering_type", context),
            availability_status=require_string(
                offering, "availability_status", context
            ),
            territory_ids=territory_ids,
            language_tags=language_tags,
            availability_window=parse_temporal_window(
                offering, "availability_window", context, schema_packs
            ),
            catalog_placement_ids=placement_ids,
        )
    if platform_offerings:
        validate_pack_values(
            schema_packs,
            "source.platform-offering-type",
            (offering.offering_type for offering in platform_offerings.values()),
            "platform_offerings.*.offering_type",
        )
        validate_pack_values(
            schema_packs,
            "source.availability-status",
            (offering.availability_status for offering in platform_offerings.values()),
            "platform_offerings.*.availability_status",
        )

    raw_identifier_schemes = require_mapping(
        registry.get("identifier_schemes"), "identifier_schemes"
    )
    identifier_schemes: dict[str, IdentifierScheme] = {}
    for scheme_id, raw_scheme in raw_identifier_schemes.items():
        context = f"identifier_schemes.{scheme_id}"
        validate_id(scheme_id, context)
        scheme = require_mapping(raw_scheme, context)
        target_types = require_string_list(scheme, "target_types", context)
        if not target_types:
            raise ValueError(
                f"Source registry `{context}.target_types` must not be empty."
            )
        validate_pack_values(
            schema_packs,
            "source.identifier-target-type",
            target_types,
            f"{context}.target_types",
        )
        identifier_schemes[scheme_id] = IdentifierScheme(
            id=scheme_id,
            lifecycle=parse_lifecycle(scheme, context),
            label=require_string(scheme, "label", context),
            target_types=target_types,
            case_sensitive=require_bool(scheme, "case_sensitive", context),
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
        work_ids = require_string_list(source, "work_ids", context)
        if not work_ids or len(set(work_ids)) != len(work_ids):
            raise ValueError(
                f"Source registry `{context}.work_ids` must be a non-empty "
                "duplicate-free list."
            )
        unknown_works = set(work_ids) - set(works)
        if unknown_works:
            raise ValueError(
                f"Source registry `{context}.work_ids` references unknown works: "
                f"{', '.join(sorted(unknown_works))}."
            )
        manifestation_id = optional_string(source, "manifestation_id", context)
        if manifestation_id is not None:
            if manifestation_id not in manifestations:
                raise ValueError(
                    f"Source registry `{context}.manifestation_id` references unknown "
                    f"manifestation `{manifestation_id}`."
                )
            if manifestations[manifestation_id].work_id not in work_ids:
                raise ValueError(
                    f"Source registry `{context}` manifestation belongs to a "
                    "work outside the source scope."
                )
        release_package_id = optional_string(
            source, "release_package_id", context
        )
        if release_package_id is not None:
            if release_package_id not in release_packages:
                raise ValueError(
                    f"Source registry `{context}.release_package_id` references "
                    f"unknown release package `{release_package_id}`."
                )
            package = release_packages[release_package_id]
            package_manifestation_ids = set(package.manifestation_ids) | {
                release_components[component_id].manifestation_id
                for component_id in package.release_component_ids
                if release_components[component_id].manifestation_id is not None
            }
            if manifestation_id is not None and manifestation_id not in package_manifestation_ids:
                raise ValueError(
                    f"Source registry `{context}` manifestation is not contained by "
                    "its release package."
                )
            package_work_ids = release_package_work_ids(release_package_id)
            if package_work_ids and not set(work_ids).issubset(package_work_ids):
                raise ValueError(
                    f"Source registry `{context}.work_ids` extends beyond its "
                    "release package."
                )
        release_event_id = optional_string(source, "release_event_id", context)
        if release_event_id is not None:
            if release_event_id not in release_events:
                raise ValueError(
                    f"Source registry `{context}.release_event_id` references unknown "
                    f"release event `{release_event_id}`."
                )
            event = release_events[release_event_id]
            expected_subject = (
                ("release-package", release_package_id)
                if release_package_id is not None
                else ("manifestation", manifestation_id)
            )
            if (event.subject_type, event.subject_id) != expected_subject:
                raise ValueError(
                    f"Source registry `{context}` release event does not belong to "
                    "its manifestation or package."
                )
        release_component_ids = require_string_list(
            source, "release_component_ids", context
        )
        for component_id in release_component_ids:
            if component_id not in release_components:
                raise ValueError(
                    f"Source registry `{context}.release_component_ids` references "
                    f"unknown component `{component_id}`."
                )
            component_manifestation_id = release_components[
                component_id
            ].manifestation_id
            component_matches = component_manifestation_id == manifestation_id
            if release_package_id is not None:
                component_matches = component_matches or component_id in (
                    release_packages[release_package_id].release_component_ids
                )
            if not component_matches:
                raise ValueError(
                    f"Source registry `{context}` component `{component_id}` does not "
                    "belong to its manifestation or package."
                )
            component_work_ids = {
                segments[segment_id].work_id
                for segment_id in release_components[component_id].segment_ids
            }
            if component_manifestation_id is not None:
                component_work_ids.add(
                    manifestations[component_manifestation_id].work_id
                )
            if component_work_ids and not component_work_ids.intersection(work_ids):
                raise ValueError(
                    f"Source registry `{context}` component `{component_id}` falls "
                    "outside the source work scope."
                )
        platform_offering_id = optional_string(
            source, "platform_offering_id", context
        )
        if platform_offering_id is not None:
            if platform_offering_id not in platform_offerings:
                raise ValueError(
                    f"Source registry `{context}.platform_offering_id` references "
                    f"unknown offering `{platform_offering_id}`."
                )
            offering = platform_offerings[platform_offering_id]
            expected_subject = (
                ("release-package", release_package_id)
                if release_package_id is not None
                else ("manifestation", manifestation_id)
            )
            if (offering.subject_type, offering.subject_id) != expected_subject:
                raise ValueError(
                    f"Source registry `{context}` platform offering does not belong "
                    "to its manifestation or package."
                )
        incompatible_work_ids = {
            work_id
            for work_id in work_ids
            if works[work_id].medium_id != medium_id
        }
        if incompatible_work_ids and role not in {
            "supplemental",
            "reference",
            "extract",
        }:
            raise ValueError(
                f"Source registry `{context}` medium does not match works: "
                f"{', '.join(sorted(incompatible_work_ids))}."
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
        observation_targets = {
            "manifestation": manifestations,
            "release-package": release_packages,
            "release-event": release_events,
            "release-component": release_components,
            "platform-offering": platform_offerings,
        }
        raw_observations = source.get("observations")
        if not isinstance(raw_observations, list):
            raise ValueError(
                f"Source registry `{context}.observations` must be a list."
            )
        observations: list[SourceObservation] = []
        seen_observation_ids: set[str] = set()
        seen_observation_targets: set[tuple[str, str]] = set()
        for index, raw_observation in enumerate(raw_observations):
            observation_context = f"{context}.observations[{index}]"
            observation = require_mapping(raw_observation, observation_context)
            observation_id = require_string(
                observation, "id", observation_context
            )
            validate_id(observation_id, f"{observation_context}.id")
            target_type = require_string(
                observation, "target_type", observation_context
            )
            target_id = require_string(
                observation, "target_id", observation_context
            )
            if observation_id in seen_observation_ids:
                raise ValueError(
                    f"Source registry `{context}.observations` repeats ID "
                    f"`{observation_id}`."
                )
            if (
                target_type not in observation_targets
                or target_id not in observation_targets[target_type]
            ):
                raise ValueError(
                    f"Source registry `{observation_context}` references unknown "
                    f"{target_type} `{target_id}`."
                )
            if (target_type, target_id) in seen_observation_targets:
                raise ValueError(
                    f"Source registry `{context}.observations` repeats a target."
                )
            seen_observation_ids.add(observation_id)
            seen_observation_targets.add((target_type, target_id))
            observations.append(
                SourceObservation(observation_id, target_type, target_id)
            )
        raw_coverage = source.get("coverage")
        if not isinstance(raw_coverage, list):
            raise ValueError(
                f"Source registry `{context}.coverage` must be a list."
            )
        coverage: list[SourceCoverage] = []
        seen_coverage_ids: set[str] = set()
        seen_coverage: set[tuple[str, str]] = set()
        coverage_targets = {
            "work": works,
            "segment": segments,
            "content-group": content_groups,
            "manifestation": manifestations,
            "release-component": release_components,
            "release-package": release_packages,
        }

        def coverage_work_ids(target_type: str, target_id: str) -> set[str]:
            if target_type == "work":
                return {target_id}
            if target_type == "segment":
                return {segments[target_id].work_id}
            if target_type == "content-group":
                result: set[str] = set()
                for member in content_groups[target_id].members:
                    if member.target_type == "work":
                        result.add(member.target_id)
                    elif member.target_type == "segment":
                        result.add(segments[member.target_id].work_id)
                    else:
                        result.update(
                            coverage_work_ids("content-group", member.target_id)
                        )
                return result
            if target_type == "manifestation":
                return {manifestations[target_id].work_id}
            if target_type == "release-package":
                return release_package_work_ids(target_id)
            component = release_components[target_id]
            result = {
                segments[segment_id].work_id
                for segment_id in component.segment_ids
            }
            if component.manifestation_id is not None:
                result.add(
                    manifestations[component.manifestation_id].work_id
                )
            return result

        for observation in observations:
            if observation.target_type == "release-event":
                observed = release_events[observation.target_id]
                observed_work_ids = (
                    {manifestations[observed.subject_id].work_id}
                    if observed.subject_type == "manifestation"
                    else release_package_work_ids(observed.subject_id)
                )
            elif observation.target_type == "platform-offering":
                observed = platform_offerings[observation.target_id]
                observed_work_ids = (
                    {manifestations[observed.subject_id].work_id}
                    if observed.subject_type == "manifestation"
                    else release_package_work_ids(observed.subject_id)
                )
            else:
                observed_work_ids = coverage_work_ids(
                    observation.target_type, observation.target_id
                )
            if observed_work_ids and not observed_work_ids.issubset(work_ids):
                raise ValueError(
                    f"Source registry `{context}.observations` includes material "
                    "outside the source work scope."
                )

        for index, raw_coverage_entry in enumerate(raw_coverage):
            coverage_context = f"{context}.coverage[{index}]"
            coverage_entry = require_mapping(
                raw_coverage_entry, coverage_context
            )
            coverage_id = require_string(
                coverage_entry, "id", coverage_context
            )
            validate_id(coverage_id, f"{coverage_context}.id")
            if coverage_id in seen_coverage_ids:
                raise ValueError(
                    f"Source registry `{context}.coverage` repeats ID "
                    f"`{coverage_id}`."
                )
            seen_coverage_ids.add(coverage_id)
            target_type = require_string(
                coverage_entry, "target_type", coverage_context
            )
            validate_pack_values(
                schema_packs,
                "source.coverage-target-type",
                (target_type,),
                f"{coverage_context}.target_type",
            )
            target_id = require_string(
                coverage_entry, "target_id", coverage_context
            )
            if (
                target_type not in coverage_targets
                or target_id not in coverage_targets[target_type]
            ):
                raise ValueError(
                    f"Source registry `{coverage_context}.target_id` references "
                    f"unknown {target_type} `{target_id}`."
                )
            coverage_type = require_string(
                coverage_entry, "coverage_type", coverage_context
            )
            validate_pack_values(
                schema_packs,
                "source.coverage-type",
                (coverage_type,),
                f"{coverage_context}.coverage_type",
            )
            key = (target_type, target_id)
            if key in seen_coverage:
                raise ValueError(
                    f"Source registry `{context}.coverage` repeats a target."
                )
            seen_coverage.add(key)
            target_work_ids = coverage_work_ids(target_type, target_id)
            if target_work_ids and not target_work_ids.issubset(work_ids):
                raise ValueError(
                    f"Source registry `{coverage_context}` extends beyond the "
                    "source work scope."
                )
            raw_ranges = coverage_entry.get("position_ranges")
            if not isinstance(raw_ranges, list):
                raise ValueError(
                    f"Source registry `{coverage_context}.position_ranges` must "
                    "be a list."
                )
            position_ranges: list[CoveragePositionRange] = []
            seen_range_ids: set[str] = set()
            medium_fields = mediums[medium_id].fields
            for range_index, raw_range in enumerate(raw_ranges):
                range_context = (
                    f"{coverage_context}.position_ranges[{range_index}]"
                )
                position_range = require_mapping(raw_range, range_context)
                range_id = require_string(position_range, "id", range_context)
                validate_id(range_id, f"{range_context}.id")
                if range_id in seen_range_ids:
                    raise ValueError(
                        f"Source registry `{coverage_context}.position_ranges` "
                        f"repeats ID `{range_id}`."
                    )
                seen_range_ids.add(range_id)
                start = require_mapping(
                    position_range.get("start"), f"{range_context}.start"
                )
                end = require_mapping(
                    position_range.get("end"), f"{range_context}.end"
                )
                if not start or set(start) != set(end):
                    raise ValueError(
                        f"Source registry `{range_context}` start/end fields must "
                        "be non-empty and identical."
                    )
                unknown_fields = set(start) - set(medium_fields)
                if unknown_fields:
                    raise ValueError(
                        f"Source registry `{range_context}` references unknown "
                        f"position fields: {', '.join(sorted(unknown_fields))}."
                    )
                validate_position_values(start, medium_fields, f"{range_context}.start")
                validate_position_values(end, medium_fields, f"{range_context}.end")
                position_ranges.append(
                    CoveragePositionRange(range_id, dict(start), dict(end))
                )
            coverage.append(
                SourceCoverage(
                    coverage_id,
                    target_type,
                    target_id,
                    coverage_type,
                    tuple(position_ranges),
                )
            )
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
            work_ids=work_ids,
            manifestation_id=manifestation_id,
            release_package_id=release_package_id,
            release_event_id=release_event_id,
            release_component_ids=release_component_ids,
            platform_offering_id=platform_offering_id,
            medium_id=medium_id,
            container_format_ids=container_format_ids,
            role=role,
            comparison_group=comparison_group,
            priority=priority,
            aliases=source_aliases,
            evidence_modes=evidence_modes,
            observations=tuple(observations),
            coverage=tuple(coverage),
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

    nested_provenance_targets = {
        "content-group-member": [
            member
            for group in content_groups.values()
            for member in group.members
        ],
        "localized-title": [
            title
            for owner in (
                *works.values(),
                *segments.values(),
                *content_groups.values(),
                *manifestations.values(),
                *release_packages.values(),
                *catalog_placements.values(),
            )
            for title in owner.localized_titles
        ],
        "release-run-phase": [
            phase for run in release_runs.values() for phase in run.phases
        ],
        "source-coverage": [
            coverage
            for source in sources.values()
            for coverage in source.coverage
        ],
    }
    for nested_type, nested_records in nested_provenance_targets.items():
        nested_ids = [record.id for record in nested_records]
        if len(nested_ids) != len(set(nested_ids)):
            raise ValueError(
                f"Source registry {nested_type} IDs must be unique across owners."
            )

    provenance_targets = {
        "work": works,
        "segment": segments,
        "content-group": content_groups,
        "work-relationship": {
            item.id: item for item in work_relationships
        },
        "adaptation-mapping": {
            item.id: item for item in adaptation_mappings
        },
        "manifestation": manifestations,
        "manifestation-relationship": {
            item.id: item for item in manifestation_relationships
        },
        "manifestation-segment-mapping": {
            item.id: item for item in manifestation_segment_mappings
        },
        "release-component": release_components,
        "release-component-relationship": {
            item.id: item for item in release_component_relationships
        },
        "release-package": release_packages,
        "release-run": release_runs,
        "release-event": release_events,
        "catalog-placement": catalog_placements,
        "platform-offering": platform_offerings,
        "source": sources,
        "source-relationship": {
            item.id: item for item in source_relationships
        },
        **{
            nested_type: {record.id: record for record in nested_records}
            for nested_type, nested_records in nested_provenance_targets.items()
        },
    }
    raw_provenance_assertions = registry.get("provenance_assertions")
    if not isinstance(raw_provenance_assertions, list):
        raise ValueError(
            "Source registry `provenance_assertions` must be a list."
        )
    provenance_assertions: list[ProvenanceAssertion] = []
    seen_provenance_ids: set[str] = set()
    for index, raw_assertion in enumerate(raw_provenance_assertions):
        context = f"provenance_assertions[{index}]"
        assertion = require_mapping(raw_assertion, context)
        assertion_id = require_string(assertion, "id", context)
        validate_id(assertion_id, f"{context}.id")
        if assertion_id in seen_provenance_ids:
            raise ValueError(
                f"Source registry provenance assertion ID `{assertion_id}` is "
                "duplicated."
            )
        seen_provenance_ids.add(assertion_id)
        subject_type = require_string(assertion, "subject_type", context)
        validate_pack_values(
            schema_packs,
            "provenance.subject-type",
            (subject_type,),
            f"{context}.subject_type",
        )
        subject_id = require_string(assertion, "subject_id", context)
        if (
            subject_type not in provenance_targets
            or subject_id not in provenance_targets[subject_type]
        ):
            raise ValueError(
                f"Source registry `{context}.subject_id` references unknown "
                f"{subject_type} `{subject_id}`."
            )
        field_path = optional_string(assertion, "field_path", context)
        if field_path is not None and not FIELD_PATH_PATTERN.fullmatch(
            field_path
        ):
            raise ValueError(
                f"Source registry `{context}.field_path` must be a dotted/indexed "
                "machine field path."
            )
        if "asserted_value" not in assertion:
            raise ValueError(
                f"Source registry `{context}.asserted_value` is required, "
                "including when the asserted value is null."
            )
        asserted_value = assertion["asserted_value"]
        assertion_status = require_string(
            assertion, "assertion_status", context
        )
        validate_pack_values(
            schema_packs,
            "provenance.assertion-status",
            (assertion_status,),
            f"{context}.assertion_status",
        )
        observed_at = parse_temporal_window(
            assertion, "observed_at", context, schema_packs
        )
        effective_window = parse_temporal_window(
            assertion, "effective_window", context, schema_packs
        )
        raw_evidence_links = assertion.get("evidence_links")
        if not isinstance(raw_evidence_links, list) or not raw_evidence_links:
            raise ValueError(
                f"Source registry `{context}.evidence_links` must be a non-empty "
                "list."
            )
        evidence_links: list[ProvenanceEvidenceLink] = []
        seen_evidence_sources: set[str] = set()
        for evidence_index, raw_link in enumerate(raw_evidence_links):
            evidence_context = (
                f"{context}.evidence_links[{evidence_index}]"
            )
            link = require_mapping(raw_link, evidence_context)
            evidence_source_id = require_string(
                link, "source_id", evidence_context
            )
            if evidence_source_id not in sources:
                raise ValueError(
                    f"Source registry `{evidence_context}.source_id` references "
                    f"unknown source `{evidence_source_id}`."
                )
            if evidence_source_id in seen_evidence_sources:
                raise ValueError(
                    f"Source registry `{context}.evidence_links` repeats source "
                    f"`{evidence_source_id}`."
                )
            seen_evidence_sources.add(evidence_source_id)
            evidence_role = require_string(
                link, "evidence_role", evidence_context
            )
            validate_pack_values(
                schema_packs,
                "provenance.evidence-role",
                (evidence_role,),
                f"{evidence_context}.evidence_role",
            )
            locator = require_mapping(
                link.get("locator"), f"{evidence_context}.locator"
            )
            if not locator:
                raise ValueError(
                    f"Source registry `{evidence_context}.locator` must not be "
                    "empty."
                )
            source_medium = mediums[sources[evidence_source_id].medium_id]
            unknown_locator_fields = set(locator) - set(source_medium.fields)
            if unknown_locator_fields:
                raise ValueError(
                    f"Source registry `{evidence_context}.locator` references "
                    f"unknown source-position fields: "
                    f"{', '.join(sorted(unknown_locator_fields))}."
                )
            validate_position_values(
                locator,
                source_medium.fields,
                f"{evidence_context}.locator",
            )
            evidence_links.append(
                ProvenanceEvidenceLink(
                    evidence_source_id, evidence_role, dict(locator)
                )
            )
        evidence_roles = {link.evidence_role for link in evidence_links}
        if assertion_status in {"verified", "inferred"} and "supports" not in evidence_roles:
            raise ValueError(
                f"Source registry `{context}` status `{assertion_status}` requires "
                "supporting evidence."
            )
        if assertion_status == "disputed" and not {
            "supports",
            "contradicts",
        }.issubset(evidence_roles):
            raise ValueError(
                f"Source registry `{context}` disputed status requires supporting "
                "and contradicting evidence."
            )
        provenance_assertions.append(
            ProvenanceAssertion(
                assertion_id,
                subject_type,
                subject_id,
                field_path,
                asserted_value,
                assertion_status,
                observed_at,
                effective_window,
                tuple(evidence_links),
            )
        )

    raw_external_identifiers = registry.get("external_identifiers")
    if not isinstance(raw_external_identifiers, list):
        raise ValueError(
            "Source registry `external_identifiers` must be a list."
        )
    external_identifiers: list[ExternalIdentifier] = []
    seen_external_identifier_ids: set[str] = set()
    seen_scheme_values: set[tuple[str, str]] = set()
    identifier_targets = {
        "work": works,
        "segment": segments,
        "content-group": content_groups,
        "manifestation": manifestations,
        "release-package": release_packages,
        "release-run": release_runs,
        "release-event": release_events,
        "platform": platforms,
        "catalog-placement": catalog_placements,
        "source": sources,
    }
    for index, raw_identifier in enumerate(raw_external_identifiers):
        context = f"external_identifiers[{index}]"
        identifier = require_mapping(raw_identifier, context)
        identifier_id = require_string(identifier, "id", context)
        validate_id(identifier_id, f"{context}.id")
        if identifier_id in seen_external_identifier_ids:
            raise ValueError(
                f"Source registry external identifier ID `{identifier_id}` is "
                "duplicated."
            )
        seen_external_identifier_ids.add(identifier_id)
        scheme_id = require_string(identifier, "scheme_id", context)
        if scheme_id not in identifier_schemes:
            raise ValueError(
                f"Source registry `{context}.scheme_id` references unknown scheme "
                f"`{scheme_id}`."
            )
        target_type = require_string(identifier, "target_type", context)
        if target_type not in identifier_schemes[scheme_id].target_types:
            raise ValueError(
                f"Source registry `{context}.target_type` is not allowed by "
                f"identifier scheme `{scheme_id}`."
            )
        target_id = require_string(identifier, "target_id", context)
        if target_id not in identifier_targets[target_type]:
            raise ValueError(
                f"Source registry `{context}.target_id` references unknown "
                f"{target_type} `{target_id}`."
            )
        value = require_string(identifier, "value", context)
        normalized_value = (
            value
            if identifier_schemes[scheme_id].case_sensitive
            else value.casefold()
        )
        scheme_value = (scheme_id, normalized_value)
        if scheme_value in seen_scheme_values:
            raise ValueError(
                f"Source registry repeats value `{value}` in identifier scheme "
                f"`{scheme_id}`."
            )
        seen_scheme_values.add(scheme_value)
        territory_ids = require_string_list(
            identifier, "territory_ids", context
        )
        unknown_territories = set(territory_ids) - set(territories)
        if unknown_territories:
            raise ValueError(
                f"Source registry `{context}.territory_ids` references unknown "
                f"territories: {', '.join(sorted(unknown_territories))}."
            )
        language_tag = optional_string(identifier, "language_tag", context)
        if language_tag is not None:
            validate_language_tag(language_tag, f"{context}.language_tag")
        status = require_string(identifier, "status", context)
        validate_pack_values(
            schema_packs,
            "source.identifier-status",
            (status,),
            f"{context}.status",
        )
        external_identifiers.append(
            ExternalIdentifier(
                id=identifier_id,
                scheme_id=scheme_id,
                target_type=target_type,
                target_id=target_id,
                value=value,
                territory_ids=territory_ids,
                language_tag=language_tag,
                status=status,
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
        content_groups=content_groups,
        numbering_schemes=numbering_schemes,
        ordering_schemes=ordering_schemes,
        work_relationships=tuple(work_relationships),
        adaptation_mappings=tuple(adaptation_mappings),
        territories=territories,
        platforms=platforms,
        manifestation_relationship_types=manifestation_relationship_types,
        manifestations=manifestations,
        manifestation_relationships=tuple(manifestation_relationships),
        manifestation_segment_mappings=tuple(
            manifestation_segment_mappings
        ),
        release_components=release_components,
        release_component_relationship_types=(
            release_component_relationship_types
        ),
        release_component_relationships=tuple(
            release_component_relationships
        ),
        release_packages=release_packages,
        release_runs=release_runs,
        release_events=release_events,
        catalog_placements=catalog_placements,
        platform_offerings=platform_offerings,
        work_aliases=work_aliases,
        source_relationship_types=source_relationship_types,
        sources=sources,
        source_relationships=tuple(source_relationships),
        provenance_assertions=tuple(provenance_assertions),
        source_aliases=aliases,
        identifier_schemes=identifier_schemes,
        external_identifiers=tuple(external_identifiers),
    )
