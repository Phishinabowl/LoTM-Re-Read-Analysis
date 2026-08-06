from dataclasses import dataclass
from pathlib import Path
import re

from .project_paths import (
    PROJECT_MANIFEST_PATH,
    is_project_root,
    path_and_parents,
    resolve_project_root,
)

from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 11
PROVENANCE_MODES = {"child-directory", "fixed", "slug-prefix"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ContentRootConfig:
    id: str
    relative_path: Path
    path: Path
    provenance_mode: str
    provenance_label: str = ""


@dataclass(frozen=True)
class ResourceRootConfig:
    id: str
    relative_path: Path
    path: Path
    required: bool


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    manifest_path: Path
    schema_version: int
    project_id: str
    framework: str
    domain: str
    content_roots: tuple[ContentRootConfig, ...]
    resource_roots: tuple[ResourceRootConfig, ...]
    qa_export: Path
    visualization_python_helper: Path
    visualization_powershell_helper: Path
    visualization_render_settings: Path
    visualization_puppeteer_config: Path
    cleanup_python_helper: Path
    cleanup_powershell_helper: Path
    lookup_keys_registry: Path
    schema_packs_registry: Path
    taxonomy_registry: Path
    resources_registry: Path
    sources_registry: Path
    entities_registry: Path
    reconciliation_registry: Path
    provenance_registry: Path
    chronology_registry: Path
    occurrences_registry: Path
    interpretations_registry: Path
    hosting_registry: Path


def require_mapping(value, key: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Project manifest `{key}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Project manifest `{context}.{key}` must be a non-empty string.")
    return value.strip()


def resolve_manifest_path(
    root: Path,
    value: str,
    key: str,
    *,
    must_exist: bool,
) -> tuple[Path, Path]:
    relative_path = Path(value)
    if relative_path.is_absolute():
        raise ValueError(f"Project manifest `{key}` must be repository-relative: {value}")

    resolved_root = root.resolve()
    resolved = (resolved_root / relative_path).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"Project manifest `{key}` escapes the repository root: {value}")
    if must_exist and not resolved.exists():
        raise ValueError(f"Project manifest `{key}` path does not exist: {resolved}")
    return relative_path, resolved


def load_project_config(root: Path) -> ProjectConfig:
    resolved_root = root.resolve()
    manifest_path = resolved_root / PROJECT_MANIFEST_PATH
    data = load_yaml_file(
        manifest_path,
        "project manifest",
        expected_schema_version=SUPPORTED_SCHEMA_VERSION,
    )

    manifest = require_mapping(data, "root")
    assert_allowed_keys(
        manifest,
        {"schema_version", "project_id", "framework", "domain", "paths", "registries"},
        "Project manifest root",
    )
    schema_version = manifest.get("schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported project manifest schema_version {schema_version!r}; expected {SUPPORTED_SCHEMA_VERSION}."
        )

    project_id = require_string(manifest, "project_id", "root")
    framework = require_string(manifest, "framework", "root")
    domain = require_string(manifest, "domain", "root")
    paths = require_mapping(manifest.get("paths"), "paths")
    assert_allowed_keys(
        paths,
        {"content_roots", "resource_roots", "qa_export", "visualization", "cleanup"},
        "Project manifest `paths`",
    )

    raw_content_roots = paths.get("content_roots")
    if not isinstance(raw_content_roots, list) or not raw_content_roots:
        raise ValueError("Project manifest `paths.content_roots` must be a non-empty list.")

    content_roots: list[ContentRootConfig] = []
    configured_root_ids: set[str] = set()
    for index, raw_entry in enumerate(raw_content_roots):
        context = f"paths.content_roots[{index}]"
        entry = require_mapping(raw_entry, context)
        assert_allowed_keys(
            entry,
            {"id", "path", "provenance_mode", "provenance_label"},
            f"Project manifest `{context}`",
        )
        content_root_id = require_string(entry, "id", context)
        if not STABLE_ID_PATTERN.fullmatch(content_root_id):
            raise ValueError(
                f"Project manifest `{context}.id` must be a lowercase kebab-case stable ID: {content_root_id}"
            )
        if content_root_id in configured_root_ids:
            raise ValueError(f"Project manifest `{context}.id` duplicates content-root ID `{content_root_id}`.")
        configured_root_ids.add(content_root_id)
        path_value = require_string(entry, "path", context)
        relative_path, resolved_path = resolve_manifest_path(
            resolved_root,
            path_value,
            f"{context}.path",
            must_exist=True,
        )
        provenance_mode = require_string(entry, "provenance_mode", context)
        if provenance_mode not in PROVENANCE_MODES:
            allowed = ", ".join(sorted(PROVENANCE_MODES))
            raise ValueError(f"Project manifest `{context}.provenance_mode` must be one of: {allowed}.")
        provenance_label = str(entry.get("provenance_label", "")).strip()
        if provenance_mode == "fixed" and not provenance_label:
            raise ValueError(f"Project manifest `{context}.provenance_label` is required for fixed provenance.")
        content_roots.append(
            ContentRootConfig(
                id=content_root_id,
                relative_path=relative_path,
                path=resolved_path,
                provenance_mode=provenance_mode,
                provenance_label=provenance_label,
            )
        )

    raw_resource_roots = paths.get("resource_roots")
    if not isinstance(raw_resource_roots, list) or not raw_resource_roots:
        raise ValueError("Project manifest `paths.resource_roots` must be a non-empty list.")

    resource_roots: list[ResourceRootConfig] = []
    for index, raw_entry in enumerate(raw_resource_roots):
        context = f"paths.resource_roots[{index}]"
        entry = require_mapping(raw_entry, context)
        assert_allowed_keys(
            entry,
            {"id", "path", "required"},
            f"Project manifest `{context}`",
        )
        resource_root_id = require_string(entry, "id", context)
        if not STABLE_ID_PATTERN.fullmatch(resource_root_id):
            raise ValueError(
                f"Project manifest `{context}.id` must be a lowercase kebab-case stable ID: {resource_root_id}"
            )
        if resource_root_id in configured_root_ids:
            raise ValueError(f"Project manifest `{context}.id` duplicates configured root ID `{resource_root_id}`.")
        configured_root_ids.add(resource_root_id)
        required = entry.get("required")
        if not isinstance(required, bool):
            raise ValueError(f"Project manifest `{context}.required` must be true or false.")
        relative_path, resolved_path = resolve_manifest_path(
            resolved_root,
            require_string(entry, "path", context),
            f"{context}.path",
            must_exist=required,
        )
        resource_roots.append(
            ResourceRootConfig(
                id=resource_root_id,
                relative_path=relative_path,
                path=resolved_path,
                required=required,
            )
        )

    _, qa_export = resolve_manifest_path(
        resolved_root,
        require_string(paths, "qa_export", "paths"),
        "paths.qa_export",
        must_exist=False,
    )

    visualization = require_mapping(paths.get("visualization"), "paths.visualization")
    assert_allowed_keys(
        visualization,
        {"python_helper", "powershell_helper", "render_settings", "puppeteer_config"},
        "Project manifest `paths.visualization`",
    )
    _, visualization_python_helper = resolve_manifest_path(
        resolved_root,
        require_string(visualization, "python_helper", "paths.visualization"),
        "paths.visualization.python_helper",
        must_exist=True,
    )
    _, visualization_powershell_helper = resolve_manifest_path(
        resolved_root,
        require_string(visualization, "powershell_helper", "paths.visualization"),
        "paths.visualization.powershell_helper",
        must_exist=True,
    )
    _, visualization_render_settings = resolve_manifest_path(
        resolved_root,
        require_string(visualization, "render_settings", "paths.visualization"),
        "paths.visualization.render_settings",
        must_exist=True,
    )
    _, visualization_puppeteer_config = resolve_manifest_path(
        resolved_root,
        require_string(visualization, "puppeteer_config", "paths.visualization"),
        "paths.visualization.puppeteer_config",
        must_exist=True,
    )

    cleanup = require_mapping(paths.get("cleanup"), "paths.cleanup")
    assert_allowed_keys(
        cleanup,
        {"python_helper", "powershell_helper"},
        "Project manifest `paths.cleanup`",
    )
    _, cleanup_python_helper = resolve_manifest_path(
        resolved_root,
        require_string(cleanup, "python_helper", "paths.cleanup"),
        "paths.cleanup.python_helper",
        must_exist=True,
    )
    _, cleanup_powershell_helper = resolve_manifest_path(
        resolved_root,
        require_string(cleanup, "powershell_helper", "paths.cleanup"),
        "paths.cleanup.powershell_helper",
        must_exist=True,
    )

    registries = require_mapping(manifest.get("registries"), "registries")
    assert_allowed_keys(
        registries,
        {
            "lookup_keys",
            "schema_packs",
            "taxonomy",
            "resources",
            "sources",
            "entities",
            "reconciliation",
            "provenance",
            "chronology",
            "occurrences",
            "interpretations",
            "hosting",
        },
        "Project manifest `registries`",
    )
    _, lookup_keys_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "lookup_keys", "registries"),
        "registries.lookup_keys",
        must_exist=True,
    )
    _, schema_packs_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "schema_packs", "registries"),
        "registries.schema_packs",
        must_exist=True,
    )
    _, taxonomy_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "taxonomy", "registries"),
        "registries.taxonomy",
        must_exist=True,
    )
    _, resources_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "resources", "registries"),
        "registries.resources",
        must_exist=True,
    )
    _, sources_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "sources", "registries"),
        "registries.sources",
        must_exist=True,
    )
    _, entities_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "entities", "registries"),
        "registries.entities",
        must_exist=True,
    )
    _, reconciliation_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "reconciliation", "registries"),
        "registries.reconciliation",
        must_exist=True,
    )
    _, provenance_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "provenance", "registries"),
        "registries.provenance",
        must_exist=True,
    )
    _, chronology_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "chronology", "registries"),
        "registries.chronology",
        must_exist=True,
    )
    _, occurrences_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "occurrences", "registries"),
        "registries.occurrences",
        must_exist=True,
    )
    _, interpretations_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "interpretations", "registries"),
        "registries.interpretations",
        must_exist=True,
    )
    _, hosting_registry = resolve_manifest_path(
        resolved_root,
        require_string(registries, "hosting", "registries"),
        "registries.hosting",
        must_exist=True,
    )

    return ProjectConfig(
        root=resolved_root,
        manifest_path=manifest_path,
        schema_version=schema_version,
        project_id=project_id,
        framework=framework,
        domain=domain,
        content_roots=tuple(content_roots),
        resource_roots=tuple(resource_roots),
        qa_export=qa_export,
        visualization_python_helper=visualization_python_helper,
        visualization_powershell_helper=visualization_powershell_helper,
        visualization_render_settings=visualization_render_settings,
        visualization_puppeteer_config=visualization_puppeteer_config,
        cleanup_python_helper=cleanup_python_helper,
        cleanup_powershell_helper=cleanup_powershell_helper,
        lookup_keys_registry=lookup_keys_registry,
        schema_packs_registry=schema_packs_registry,
        taxonomy_registry=taxonomy_registry,
        resources_registry=resources_registry,
        sources_registry=sources_registry,
        entities_registry=entities_registry,
        reconciliation_registry=reconciliation_registry,
        provenance_registry=provenance_registry,
        chronology_registry=chronology_registry,
        occurrences_registry=occurrences_registry,
        interpretations_registry=interpretations_registry,
        hosting_registry=hosting_registry,
    )
