from dataclasses import dataclass
from pathlib import Path
import re

import yaml

from project_config import ContentRootConfig, ProjectConfig, resolve_manifest_path


SUPPORTED_TAXONOMY_SCHEMA_VERSION = 2
LIFECYCLES = {"active", "deferred"}
CATEGORY_POLICIES = {"required", "optional", "forbidden"}
PATH_STRATEGIES = {"category-file", "category-subject-record", "root-file", "fixed-file"}
METADATA_TYPE_MODES = {"category", "fixed", "none"}
SLUG_MODES = {"category", "record"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class CategoryPlacement:
    content_type_id: str
    relative_folder: Path
    folder: Path
    template: Path


@dataclass(frozen=True)
class CategoryConfig:
    id: str
    lifecycle: str
    label: str
    plural_label: str
    canonical_pages_enabled: bool
    metadata_type: str = ""
    subject_slug_prefix: str = ""
    subject_slug_pattern: str = ""
    graph_class: str = ""
    placements: dict[str, CategoryPlacement] | None = None


@dataclass(frozen=True)
class ContentTypeConfig:
    id: str
    lifecycle: str
    label: str
    plural_label: str
    canonical_pages_enabled: bool
    content_root_id: str
    category_policy: str
    path_strategy: str
    metadata_type_mode: str
    slug_mode: str
    default_template: Path | None
    qa_page_enabled: bool
    graph_enabled: bool
    metadata_type: str = ""
    record_slug_prefix: str = ""
    record_slug_pattern: str = ""
    record_path: Path | None = None


@dataclass(frozen=True)
class TaxonomyConfig:
    path: Path
    schema_version: int
    categories: dict[str, CategoryConfig]
    content_types: dict[str, ContentTypeConfig]

    def reconciliation_targets(self) -> dict[str, dict[str, object]]:
        return {
            "content-type": self.content_types,
            "category": self.categories,
        }

    def reconciliation_target(self, target_type: str, target_id: str) -> object:
        targets = self.reconciliation_targets().get(target_type)
        if targets is None:
            raise ValueError(f"Unsupported taxonomy reconciliation target type `{target_type}`.")
        if target_id not in targets:
            raise ValueError(f"Unknown {target_type} `{target_id}`.")
        return targets[target_id]

    def content_roots_for_qa_pages(
        self,
        project: ProjectConfig,
    ) -> tuple[ContentRootConfig, ...]:
        enabled_ids = {
            content_type.content_root_id
            for content_type in self.content_types.values()
            if content_type.lifecycle == "active" and content_type.qa_page_enabled
        }
        return tuple(
            content_root
            for content_root in project.content_roots
            if content_root.id in enabled_ids
        )


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Taxonomy registry `{context}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Taxonomy registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def require_bool(mapping: dict, key: str, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Taxonomy registry `{context}.{key}` must be true or false.")
    return value


def validate_stable_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Taxonomy registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def validate_regex(value: str, context: str) -> None:
    try:
        re.compile(value)
    except re.error as exc:
        raise ValueError(f"Taxonomy registry `{context}` is invalid: {exc}") from exc


def resolve_folder(
    project: ProjectConfig,
    content_root_id: str,
    value: str,
    context: str,
) -> tuple[Path, Path]:
    content_roots = {content_root.id: content_root for content_root in project.content_roots}
    if content_root_id not in content_roots:
        raise ValueError(
            f"Taxonomy registry `{context}` references unknown content root "
            f"`{content_root_id}`."
        )

    relative_folder = Path(value)
    if relative_folder.is_absolute():
        raise ValueError(f"Taxonomy registry `{context}` must be relative: {value}")

    root_path = content_roots[content_root_id].path.resolve()
    folder = (root_path / relative_folder).resolve()
    if folder != root_path and root_path not in folder.parents:
        raise ValueError(
            f"Taxonomy registry `{context}` escapes content root `{content_root_id}`: {value}"
        )
    return relative_folder, folder


def resolve_template(project: ProjectConfig, value: str, context: str) -> Path:
    relative_template, _ = resolve_manifest_path(
        project.root,
        value,
        context,
        must_exist=True,
    )
    return relative_template


def parse_content_type(
    content_type_id: str,
    raw_content_type,
    *,
    project: ProjectConfig,
) -> ContentTypeConfig:
    context = f"content_types.{content_type_id}"
    validate_stable_id(content_type_id, context)
    content_type = require_mapping(raw_content_type, context)
    lifecycle = require_string(content_type, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        allowed = ", ".join(sorted(LIFECYCLES))
        raise ValueError(f"Taxonomy registry `{context}.lifecycle` must be one of: {allowed}.")

    canonical_pages_enabled = require_bool(
        content_type,
        "canonical_pages_enabled",
        context,
    )
    if lifecycle == "deferred" and canonical_pages_enabled:
        raise ValueError(
            f"Taxonomy registry `{context}` cannot enable canonical pages while deferred."
        )
    if lifecycle == "active" and not canonical_pages_enabled:
        raise ValueError(
            f"Taxonomy registry active content type `{content_type_id}` must enable "
            "canonical pages."
        )

    content_root_id = require_string(content_type, "content_root_id", context)
    validate_stable_id(content_root_id, f"{context}.content_root_id")
    root_ids = {content_root.id for content_root in project.content_roots}
    if content_root_id not in root_ids:
        raise ValueError(
            f"Taxonomy registry `{context}.content_root_id` references unknown "
            f"content root `{content_root_id}`."
        )

    category_policy = require_string(content_type, "category_policy", context)
    if category_policy not in CATEGORY_POLICIES:
        allowed = ", ".join(sorted(CATEGORY_POLICIES))
        raise ValueError(
            f"Taxonomy registry `{context}.category_policy` must be one of: {allowed}."
        )
    path_strategy = require_string(content_type, "path_strategy", context)
    if path_strategy not in PATH_STRATEGIES:
        allowed = ", ".join(sorted(PATH_STRATEGIES))
        raise ValueError(
            f"Taxonomy registry `{context}.path_strategy` must be one of: {allowed}."
        )
    metadata_type_mode = require_string(content_type, "metadata_type_mode", context)
    if metadata_type_mode not in METADATA_TYPE_MODES:
        allowed = ", ".join(sorted(METADATA_TYPE_MODES))
        raise ValueError(
            f"Taxonomy registry `{context}.metadata_type_mode` must be one of: {allowed}."
        )
    slug_mode = require_string(content_type, "slug_mode", context)
    if slug_mode not in SLUG_MODES:
        allowed = ", ".join(sorted(SLUG_MODES))
        raise ValueError(f"Taxonomy registry `{context}.slug_mode` must be one of: {allowed}.")

    if category_policy == "forbidden" and path_strategy not in {"root-file", "fixed-file"}:
        raise ValueError(
            f"Taxonomy registry `{context}` with forbidden categories must use "
            "`root-file` or `fixed-file` path strategy."
        )
    if slug_mode == "category" and category_policy == "forbidden":
        raise ValueError(
            f"Taxonomy registry `{context}` cannot use category slugs when categories "
            "are forbidden."
        )
    if metadata_type_mode == "category" and category_policy == "forbidden":
        raise ValueError(
            f"Taxonomy registry `{context}` cannot use category metadata types when "
            "categories are forbidden."
        )

    metadata_type = str(content_type.get("metadata_type", "")).strip()
    if metadata_type_mode == "fixed" and not metadata_type:
        raise ValueError(
            f"Taxonomy registry `{context}.metadata_type` is required for fixed mode."
        )

    record_slug_prefix = str(content_type.get("record_slug_prefix", "")).strip()
    record_slug_pattern = str(content_type.get("record_slug_pattern", "")).strip()
    if slug_mode == "record":
        if record_slug_prefix:
            validate_stable_id(record_slug_prefix, f"{context}.record_slug_prefix")
        if not record_slug_pattern:
            raise ValueError(
                f"Taxonomy registry `{context}.record_slug_pattern` is required for "
                "record slug mode."
            )
        validate_regex(record_slug_pattern, f"{context}.record_slug_pattern")

    default_template_value = str(content_type.get("default_template", "")).strip()
    default_template = (
        resolve_template(
            project,
            default_template_value,
            f"{context}.default_template",
        )
        if default_template_value
        else None
    )
    record_path_value = str(content_type.get("record_path", "")).strip()
    record_path = None
    if path_strategy == "fixed-file":
        if not record_path_value:
            raise ValueError(
                f"Taxonomy registry `{context}.record_path` is required for fixed-file."
            )
        relative_record, resolved_record = resolve_folder(
            project,
            content_root_id,
            record_path_value,
            f"{context}.record_path",
        )
        if not resolved_record.is_file():
            raise ValueError(
                f"Taxonomy registry `{context}.record_path` does not exist: "
                f"{resolved_record}"
            )
        record_path = relative_record
    elif record_path_value:
        raise ValueError(
            f"Taxonomy registry `{context}.record_path` is only valid for fixed-file."
        )

    return ContentTypeConfig(
        id=content_type_id,
        lifecycle=lifecycle,
        label=require_string(content_type, "label", context),
        plural_label=require_string(content_type, "plural_label", context),
        canonical_pages_enabled=canonical_pages_enabled,
        content_root_id=content_root_id,
        category_policy=category_policy,
        path_strategy=path_strategy,
        metadata_type_mode=metadata_type_mode,
        slug_mode=slug_mode,
        default_template=default_template,
        qa_page_enabled=require_bool(content_type, "qa_page_enabled", context),
        graph_enabled=require_bool(content_type, "graph_enabled", context),
        metadata_type=metadata_type,
        record_slug_prefix=record_slug_prefix,
        record_slug_pattern=record_slug_pattern,
        record_path=record_path,
    )


def parse_category(
    category_id: str,
    raw_category,
    *,
    project: ProjectConfig,
    content_types: dict[str, ContentTypeConfig],
) -> CategoryConfig:
    context = f"categories.{category_id}"
    validate_stable_id(category_id, context)
    category = require_mapping(raw_category, context)
    lifecycle = require_string(category, "lifecycle", context)
    if lifecycle not in LIFECYCLES:
        allowed = ", ".join(sorted(LIFECYCLES))
        raise ValueError(f"Taxonomy registry `{context}.lifecycle` must be one of: {allowed}.")

    canonical_pages_enabled = require_bool(
        category,
        "canonical_pages_enabled",
        context,
    )
    label = require_string(category, "label", context)
    plural_label = require_string(category, "plural_label", context)
    if lifecycle == "deferred":
        if canonical_pages_enabled:
            raise ValueError(
                f"Taxonomy registry `{context}` cannot enable canonical pages while deferred."
            )
        return CategoryConfig(
            id=category_id,
            lifecycle=lifecycle,
            label=label,
            plural_label=plural_label,
            canonical_pages_enabled=False,
        )

    if not canonical_pages_enabled:
        raise ValueError(
            f"Taxonomy registry active category `{category_id}` must enable canonical pages."
        )

    subject_slug_prefix = require_string(category, "subject_slug_prefix", context)
    validate_stable_id(subject_slug_prefix, f"{context}.subject_slug_prefix")
    subject_slug_pattern = require_string(category, "subject_slug_pattern", context)
    validate_regex(subject_slug_pattern, f"{context}.subject_slug_pattern")
    graph_class = require_string(category, "graph_class", context)
    validate_stable_id(graph_class, f"{context}.graph_class")

    raw_placements = require_mapping(category.get("placements"), f"{context}.placements")
    placements: dict[str, CategoryPlacement] = {}
    for content_type_id, raw_placement in raw_placements.items():
        placement_context = f"{context}.placements.{content_type_id}"
        if content_type_id not in content_types:
            raise ValueError(
                f"Taxonomy registry `{placement_context}` references unknown content type."
            )
        content_type = content_types[content_type_id]
        if content_type.category_policy == "forbidden":
            raise ValueError(
                f"Taxonomy registry `{placement_context}` references content type "
                "that forbids categories."
            )
        placement = require_mapping(raw_placement, placement_context)
        relative_folder, folder = resolve_folder(
            project,
            content_type.content_root_id,
            require_string(placement, "relative_folder", placement_context),
            f"{placement_context}.relative_folder",
        )
        template_value = str(placement.get("template", "")).strip()
        template = (
            resolve_template(
                project,
                template_value,
                f"{placement_context}.template",
            )
            if template_value
            else content_type.default_template
        )
        if template is None:
            raise ValueError(
                f"Taxonomy registry `{placement_context}` requires a template because "
                f"content type `{content_type_id}` has no default template."
            )
        placements[content_type_id] = CategoryPlacement(
            content_type_id=content_type_id,
            relative_folder=relative_folder,
            folder=folder,
            template=template,
        )

    required_category_types = {
        content_type.id
        for content_type in content_types.values()
        if content_type.lifecycle == "active" and content_type.category_policy == "required"
    }
    missing_required = required_category_types - set(placements)
    if missing_required:
        missing = ", ".join(sorted(missing_required))
        raise ValueError(
            f"Taxonomy registry `{context}.placements` is missing required "
            f"content type(s): {missing}."
        )

    return CategoryConfig(
        id=category_id,
        lifecycle=lifecycle,
        label=label,
        plural_label=plural_label,
        canonical_pages_enabled=True,
        metadata_type=require_string(category, "metadata_type", context),
        subject_slug_prefix=subject_slug_prefix,
        subject_slug_pattern=subject_slug_pattern,
        graph_class=graph_class,
        placements=placements,
    )


def ensure_unique(records, attribute: str, label: str) -> None:
    seen: dict[str, str] = {}
    for record in records:
        value = getattr(record, attribute)
        key = str(value).casefold()
        if key in seen:
            raise ValueError(
                f"Taxonomy registry duplicates {label} `{value}` between "
                f"`{seen[key]}` and `{record.id}`."
            )
        seen[key] = record.id


def load_taxonomy_config(project: ProjectConfig) -> TaxonomyConfig:
    try:
        data = yaml.safe_load(project.taxonomy_registry.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Unable to parse taxonomy registry {project.taxonomy_registry}: {exc}"
        ) from exc

    registry = require_mapping(data, "root")
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_TAXONOMY_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported taxonomy schema_version {schema_version!r}; "
            f"expected {SUPPORTED_TAXONOMY_SCHEMA_VERSION}."
        )

    raw_content_types = require_mapping(registry.get("content_types"), "content_types")
    content_types = {
        content_type_id: parse_content_type(
            content_type_id,
            raw_content_type,
            project=project,
        )
        for content_type_id, raw_content_type in raw_content_types.items()
    }
    fixed_record_paths = [
        content_type
        for content_type in content_types.values()
        if content_type.lifecycle == "active" and content_type.record_path is not None
    ]
    ensure_unique(fixed_record_paths, "record_path", "fixed record path")

    raw_categories = require_mapping(registry.get("categories"), "categories")
    overlapping_ids = set(raw_categories) & set(raw_content_types)
    if overlapping_ids:
        duplicates = ", ".join(sorted(overlapping_ids))
        raise ValueError(
            f"Taxonomy registry IDs cannot be both categories and content types: {duplicates}."
        )
    categories = {
        category_id: parse_category(
            category_id,
            raw_category,
            project=project,
            content_types=content_types,
        )
        for category_id, raw_category in raw_categories.items()
    }

    active_categories = [
        category
        for category in categories.values()
        if category.lifecycle == "active"
    ]
    ensure_unique(active_categories, "metadata_type", "category metadata type")
    ensure_unique(active_categories, "subject_slug_prefix", "subject slug prefix")
    ensure_unique(active_categories, "graph_class", "graph class")

    seen_placements: dict[tuple[str, str], str] = {}
    for category in active_categories:
        for content_type_id, placement in (category.placements or {}).items():
            key = (content_type_id, str(placement.relative_folder).casefold())
            if key in seen_placements:
                raise ValueError(
                    f"Taxonomy registry duplicates `{content_type_id}` folder "
                    f"`{placement.relative_folder}` between `{seen_placements[key]}` "
                    f"and `{category.id}`."
                )
            seen_placements[key] = category.id

    return TaxonomyConfig(
        path=project.taxonomy_registry,
        schema_version=schema_version,
        categories=categories,
        content_types=content_types,
    )
