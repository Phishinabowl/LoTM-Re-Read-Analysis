from dataclasses import dataclass
from pathlib import Path
from string import Formatter
import re

import yaml

from project_config import ProjectConfig
from resource_config import ResourceConfig


SUPPORTED_SOURCE_SCHEMA_VERSION = 1
LIFECYCLES = {"active", "deferred"}
SOURCE_ROLES = {"original", "adaptation", "transcript", "supplemental", "reference"}
POSITION_FIELD_TYPES = {"string", "integer", "number", "timestamp", "boolean"}
PRIORITY_ORDERS = {"ascending", "descending"}
CONFLICT_BEHAVIORS = {"flag"}
DEVIATION_OWNERS = {"adaptation-source"}
CHAPTER_NUMBERING_MODES = {"work-local", "series-global"}
VOLUME_CATALOG_STATUSES = {"verified", "pending-verification", "not-applicable"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ComparisonPolicy:
    priority_order: str
    compare_within_group_only: bool
    compare_within_work_only: bool
    cross_source_conflict: str
    adaptation_deviation_owner: str
    preserve_source_scoped_claims: bool


@dataclass(frozen=True)
class CitationFormat:
    id: str
    template: str
    required_fields: tuple[str, ...]


@dataclass(frozen=True)
class MediumConfig:
    id: str
    lifecycle: str
    label: str
    plural_label: str
    fields: dict[str, str]
    required_fields: tuple[str, ...]
    sort_fields: tuple[str, ...]
    citation_formats: tuple[CitationFormat, ...]


@dataclass(frozen=True)
class SeriesConfig:
    id: str
    lifecycle: str
    label: str
    short_label: str


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
    series_id: str
    label: str
    short_label: str
    ordinal: int
    work_type: str
    medium_id: str
    aliases: tuple[str, ...]
    chapter_numbering: str
    volume_catalog_status: str
    volumes: tuple[VolumeConfig, ...]


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
    role: str
    comparison_group: str
    priority: int
    aliases: tuple[str, ...]
    evidence_modes: tuple[str, ...]
    adapted_from_source_id: str | None
    derived_from_source_id: str | None
    resource_bindings: tuple[SourceResourceBinding, ...]


@dataclass(frozen=True)
class SourceRegistry:
    path: Path
    schema_version: int
    comparison_policy: ComparisonPolicy
    mediums: dict[str, MediumConfig]
    series: dict[str, SeriesConfig]
    works: dict[str, WorkConfig]
    work_aliases: dict[str, str]
    sources: dict[str, SourceConfig]
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


def parse_policy(raw_policy) -> ComparisonPolicy:
    context = "comparison_policy"
    policy = require_mapping(raw_policy, context)
    priority_order = require_string(policy, "priority_order", context)
    if priority_order not in PRIORITY_ORDERS:
        raise ValueError(
            f"Source registry `{context}.priority_order` must be one of: "
            f"{', '.join(sorted(PRIORITY_ORDERS))}."
        )
    cross_source_conflict = require_string(policy, "cross_source_conflict", context)
    if cross_source_conflict not in CONFLICT_BEHAVIORS:
        raise ValueError(
            f"Source registry `{context}.cross_source_conflict` must be one of: "
            f"{', '.join(sorted(CONFLICT_BEHAVIORS))}."
        )
    deviation_owner = require_string(
        policy,
        "adaptation_deviation_owner",
        context,
    )
    if deviation_owner not in DEVIATION_OWNERS:
        raise ValueError(
            f"Source registry `{context}.adaptation_deviation_owner` must be one of: "
            f"{', '.join(sorted(DEVIATION_OWNERS))}."
        )
    return ComparisonPolicy(
        priority_order=priority_order,
        compare_within_group_only=require_bool(
            policy,
            "compare_within_group_only",
            context,
        ),
        compare_within_work_only=require_bool(
            policy,
            "compare_within_work_only",
            context,
        ),
        cross_source_conflict=cross_source_conflict,
        adaptation_deviation_owner=deviation_owner,
        preserve_source_scoped_claims=require_bool(
            policy,
            "preserve_source_scoped_claims",
            context,
        ),
    )


def parse_series(series_id: str, raw_series) -> SeriesConfig:
    context = f"series.{series_id}"
    validate_id(series_id, context)
    series = require_mapping(raw_series, context)
    lifecycle = require_string(series, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        raise ValueError(
            f"Source registry `{context}.lifecycle` must be one of: "
            f"{', '.join(sorted(LIFECYCLES))}."
        )
    return SeriesConfig(
        id=series_id,
        lifecycle=lifecycle,
        label=require_string(series, "label", context),
        short_label=require_string(series, "short_label", context),
    )


def parse_work(
    work_id: str,
    raw_work,
    *,
    series: dict[str, SeriesConfig],
    mediums: dict[str, MediumConfig],
) -> WorkConfig:
    context = f"works.{work_id}"
    validate_id(work_id, context)
    work = require_mapping(raw_work, context)
    lifecycle = require_string(work, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        raise ValueError(
            f"Source registry `{context}.lifecycle` must be one of: "
            f"{', '.join(sorted(LIFECYCLES))}."
        )
    series_id = require_string(work, "series_id", context)
    if series_id not in series:
        raise ValueError(
            f"Source registry `{context}.series_id` references unknown series "
            f"`{series_id}`."
        )
    medium_id = require_string(work, "medium_id", context)
    if medium_id not in mediums:
        raise ValueError(
            f"Source registry `{context}.medium_id` references unknown medium "
            f"`{medium_id}`."
        )
    ordinal = work.get("ordinal")
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
        raise ValueError(
            f"Source registry `{context}.ordinal` must be a positive integer."
        )
    work_type = require_string(work, "work_type", context)
    validate_id(work_type, f"{context}.work_type")
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
        series_id=series_id,
        label=require_string(work, "label", context),
        short_label=require_string(work, "short_label", context),
        ordinal=ordinal,
        work_type=work_type,
        medium_id=medium_id,
        aliases=aliases,
        chapter_numbering=chapter_numbering,
        volume_catalog_status=volume_status,
        volumes=tuple(sorted_volumes),
    )


def parse_medium(medium_id: str, raw_medium) -> MediumConfig:
    context = f"mediums.{medium_id}"
    validate_id(medium_id, context)
    medium = require_mapping(raw_medium, context)
    lifecycle = require_string(medium, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        raise ValueError(
            f"Source registry `{context}.lifecycle` must be one of: "
            f"{', '.join(sorted(LIFECYCLES))}."
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
) -> SourceRegistry:
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
    comparison_policy = parse_policy(registry.get("comparison_policy"))

    raw_mediums = require_mapping(registry.get("mediums"), "mediums")
    mediums = {
        medium_id: parse_medium(medium_id, raw_medium)
        for medium_id, raw_medium in raw_mediums.items()
    }

    raw_series = require_mapping(registry.get("series"), "series")
    series = {
        series_id: parse_series(series_id, raw_series_entry)
        for series_id, raw_series_entry in raw_series.items()
    }
    raw_works = require_mapping(registry.get("works"), "works")
    works = {
        work_id: parse_work(
            work_id,
            raw_work,
            series=series,
            mediums=mediums,
        )
        for work_id, raw_work in raw_works.items()
    }
    seen_ordinals: dict[tuple[str, int], str] = {}
    work_aliases: dict[str, str] = {}
    work_ids_casefolded = {work_id.casefold() for work_id in works}
    for work in works.values():
        ordinal_key = (work.series_id, work.ordinal)
        if ordinal_key in seen_ordinals:
            raise ValueError(
                f"Source registry duplicates ordinal {work.ordinal} in series "
                f"`{work.series_id}` between `{seen_ordinals[ordinal_key]}` and "
                f"`{work.id}`."
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

    raw_sources = require_mapping(registry.get("sources"), "sources")
    sources: dict[str, SourceConfig] = {}
    aliases: dict[str, str] = {}
    for source_id, raw_source in raw_sources.items():
        context = f"sources.{source_id}"
        validate_id(source_id, context)
        source = require_mapping(raw_source, context)
        lifecycle = require_string(source, "lifecycle", context)
        if lifecycle not in LIFECYCLES:
            raise ValueError(
                f"Source registry `{context}.lifecycle` must be one of: "
                f"{', '.join(sorted(LIFECYCLES))}."
            )
        medium_id = require_string(source, "medium_id", context)
        if medium_id not in mediums:
            raise ValueError(
                f"Source registry `{context}.medium_id` references unknown medium "
                f"`{medium_id}`."
            )
        role = require_string(source, "role", context)
        if role not in SOURCE_ROLES:
            raise ValueError(
                f"Source registry `{context}.role` must be one of: "
                f"{', '.join(sorted(SOURCE_ROLES))}."
            )
        work_id = require_string(source, "work_id", context)
        if work_id not in works:
            raise ValueError(
                f"Source registry `{context}.work_id` references unknown work "
                f"`{work_id}`."
            )
        if works[work_id].medium_id != medium_id and role not in {
            "adaptation",
            "transcript",
            "supplemental",
        }:
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
        adapted_from = str(source.get("adapted_from_source_id", "")).strip() or None
        derived_from = str(source.get("derived_from_source_id", "")).strip() or None
        sources[source_id] = SourceConfig(
            id=source_id,
            lifecycle=lifecycle,
            label=require_string(source, "label", context),
            work_id=work_id,
            medium_id=medium_id,
            role=role,
            comparison_group=comparison_group,
            priority=priority,
            aliases=source_aliases,
            evidence_modes=evidence_modes,
            adapted_from_source_id=adapted_from,
            derived_from_source_id=derived_from,
            resource_bindings=bindings,
        )

    for source in sources.values():
        for relationship_name, target_id in (
            ("adapted_from_source_id", source.adapted_from_source_id),
            ("derived_from_source_id", source.derived_from_source_id),
        ):
            if target_id is None:
                continue
            if target_id not in sources:
                raise ValueError(
                    f"Source registry `sources.{source.id}.{relationship_name}` "
                    f"references unknown source `{target_id}`."
                )
            if target_id == source.id:
                raise ValueError(
                    f"Source registry `sources.{source.id}.{relationship_name}` "
                    "cannot reference itself."
                )
            target = sources[target_id]
            if target.comparison_group != source.comparison_group:
                raise ValueError(
                    f"Source registry `{source.id}` and `{target_id}` must share a "
                    "comparison group."
                )
            if target.work_id != source.work_id:
                raise ValueError(
                    f"Source registry `{source.id}` and `{target_id}` must reference "
                    "the same work."
                )
        if source.role == "adaptation" and source.adapted_from_source_id is None:
            raise ValueError(
                f"Source registry adaptation `{source.id}` requires "
                "`adapted_from_source_id`."
            )
        if source.adapted_from_source_id:
            original = sources[source.adapted_from_source_id]
            outranks_original = (
                source.priority < original.priority
                if comparison_policy.priority_order == "ascending"
                else source.priority > original.priority
            )
            if outranks_original:
                raise ValueError(
                    f"Source registry adaptation `{source.id}` cannot outrank "
                    f"`{original.id}` under the configured priority order."
                )

    def visit(source_id: str, active: set[str], complete: set[str]) -> None:
        if source_id in active:
            chain = " -> ".join((*active, source_id))
            raise ValueError(f"Source registry contains a derivation cycle: {chain}.")
        if source_id in complete:
            return
        active.add(source_id)
        source = sources[source_id]
        for target_id in (
            source.adapted_from_source_id,
            source.derived_from_source_id,
        ):
            if target_id:
                visit(target_id, active, complete)
        active.remove(source_id)
        complete.add(source_id)

    complete_sources: set[str] = set()
    for source_id in sources:
        visit(source_id, set(), complete_sources)

    return SourceRegistry(
        path=project.sources_registry,
        schema_version=schema_version,
        comparison_policy=comparison_policy,
        mediums=mediums,
        series=series,
        works=works,
        work_aliases=work_aliases,
        sources=sources,
        source_aliases=aliases,
    )
