from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .project_config import ProjectConfig, load_project_config
from .resource_config import ResourceConfig, load_resource_config
from .schema_pack_config import SchemaPackRegistry, load_schema_pack_registry
from .taxonomy_config import TaxonomyConfig, load_taxonomy_config


CONTRACT_ID = "effective-project-schema"
CONTRACT_VERSION = 1
SEVERITY_ORDER = {"warning": 0, "info": 1}
CONSUMER_ENABLEMENT_FIELDS = {
    "qa": "qa_page_enabled",
    "visualization": "graph_enabled",
}


@dataclass(frozen=True)
class EffectiveProjectSchema:
    project: dict[str, Any]
    registry_schema_versions: tuple[dict[str, Any], ...]
    packs: tuple[dict[str, Any], ...]
    capabilities: tuple[dict[str, Any], ...]
    controlled_value_namespaces: tuple[dict[str, Any], ...]
    content: dict[str, Any]
    resources: dict[str, Any]
    diagnostics: tuple[dict[str, Any], ...]
    contract: str = CONTRACT_ID
    contract_version: int = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "contract_version": self.contract_version,
            "project": self.project,
            "registry_schema_versions": list(self.registry_schema_versions),
            "packs": list(self.packs),
            "capabilities": list(self.capabilities),
            "controlled_value_namespaces": list(self.controlled_value_namespaces),
            "content": self.content,
            "resources": self.resources,
            "diagnostics": list(self.diagnostics),
        }


def _portable_path(path: Path | str) -> str:
    return Path(path).as_posix()


def _repository_relative(path: Path | str | None, root: Path) -> str | None:
    if path is None:
        return None
    candidate = Path(path)
    resolved_root = root.resolve()
    resolved = candidate.resolve() if candidate.is_absolute() else (resolved_root / candidate).resolve()
    return resolved.relative_to(resolved_root).as_posix()


def _diagnostic(
    severity: str,
    code: str,
    message: str,
    *,
    path: str | None = None,
    related_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
        "related_ids": sorted(related_ids),
    }


def _diagnostic_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        SEVERITY_ORDER[row["severity"]],
        row["code"],
        row["path"] is not None,
        row["path"] or "",
        row["message"],
        tuple(row["related_ids"]),
    )


def compose_effective_project_schema(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    taxonomy: TaxonomyConfig,
    resources: ResourceConfig,
) -> EffectiveProjectSchema:
    diagnostics: list[dict[str, Any]] = []

    pack_rows: list[dict[str, Any]] = []
    for pack_id in packs.selection_order:
        pack = packs.packs[pack_id]
        dependency_rows = [
            {
                "pack_id": dependency.pack_id,
                "minimum_version": dependency.minimum_version,
                "selected_version": packs.packs[dependency.pack_id].pack_version,
                "status": "satisfied",
            }
            for dependency in pack.dependencies
        ]
        pack_rows.append(
            {
                "id": pack.id,
                "kind": pack.kind,
                "lifecycle": pack.lifecycle,
                "schema_version": pack.schema_version,
                "pack_version": pack.pack_version,
                "label": pack.label,
                "description": pack.description,
                "dependencies": dependency_rows,
            }
        )
        if pack.lifecycle == "deferred":
            diagnostics.append(
                _diagnostic(
                    "info",
                    "deferred-pack-selected",
                    f"Selected pack `{pack_id}` is deferred.",
                    path=f"packs.{pack_id}.lifecycle",
                    related_ids=(pack_id,),
                )
            )

    enabled = set(packs.enabled_capabilities)
    capability_rows: list[dict[str, Any]] = []
    for capability_id in sorted(packs.declared_capabilities):
        provider_ids = packs.capability_providers[capability_id]
        providers = []
        lifecycles = []
        for pack_id in provider_ids:
            definition = packs.capability_definitions[(pack_id, capability_id)]
            lifecycles.append(definition.lifecycle)
            providers.append(
                {
                    "pack_id": pack_id,
                    "lifecycle": definition.lifecycle,
                    "label": definition.label,
                    "description": definition.description,
                }
            )
        effective_lifecycle = (
            "available" if "available" in lifecycles else "deprecated" if "deprecated" in lifecycles else "planned"
        )
        is_enabled = capability_id in enabled
        capability_rows.append(
            {
                "id": capability_id,
                "declared": True,
                "effective_lifecycle": effective_lifecycle,
                "available": effective_lifecycle in {"available", "deprecated"},
                "deprecated": effective_lifecycle == "deprecated",
                "planned": effective_lifecycle == "planned",
                "enabled": is_enabled,
                "disabled": not is_enabled,
                "providers": providers,
            }
        )
        if effective_lifecycle == "deprecated" and is_enabled:
            diagnostics.append(
                _diagnostic(
                    "warning",
                    "deprecated-capability-enabled",
                    f"Deprecated capability `{capability_id}` is enabled.",
                    path="capability_activation.enabled",
                    related_ids=(capability_id, *provider_ids),
                )
            )
        if len(provider_ids) > 1:
            diagnostics.append(
                _diagnostic(
                    "info",
                    "multiple-capability-providers",
                    f"Capability `{capability_id}` has multiple selected providers.",
                    path=f"capabilities.{capability_id}.providers",
                    related_ids=(capability_id, *provider_ids),
                )
            )

    namespace_rows: list[dict[str, Any]] = []
    for namespace in sorted(packs.controlled_values):
        values = []
        for value_id in sorted(packs.controlled_values[namespace]):
            definition = packs.controlled_value_definitions[(namespace, value_id)]
            values.append(
                {
                    "id": value_id,
                    "label": definition.label,
                    "description": definition.description,
                    "broader_value_id": definition.broader_value,
                    "owner_pack_id": packs.controlled_value_owners[(namespace, value_id)],
                }
            )
        namespace_rows.append({"id": namespace, "values": values})

    content_roots = [
        {
            "id": root.id,
            "relative_path": _portable_path(root.relative_path),
            "provenance_mode": root.provenance_mode,
            "provenance_label": root.provenance_label,
        }
        for root in project.content_roots
    ]

    content_type_rows = []
    for content_type_id in sorted(taxonomy.content_types):
        item = taxonomy.content_types[content_type_id]
        content_type_rows.append(
            {
                "id": item.id,
                "lifecycle": item.lifecycle,
                "label": item.label,
                "plural_label": item.plural_label,
                "canonical_pages_enabled": item.canonical_pages_enabled,
                "content_root_id": item.content_root_id,
                "category_policy": item.category_policy,
                "path_strategy": item.path_strategy,
                "metadata_type_mode": item.metadata_type_mode,
                "slug_mode": item.slug_mode,
                "default_template": _repository_relative(item.default_template, project.root),
                "qa_page_enabled": item.qa_page_enabled,
                "graph_enabled": item.graph_enabled,
                "metadata_type": item.metadata_type,
                "record_slug_prefix": item.record_slug_prefix,
                "record_slug_pattern": item.record_slug_pattern,
                "record_path": _repository_relative(item.record_path, project.root),
            }
        )
        if item.lifecycle == "deferred":
            diagnostics.append(
                _diagnostic(
                    "info",
                    "deferred-content-type",
                    f"Content type `{item.id}` is deferred.",
                    path=f"content_types.{item.id}.lifecycle",
                    related_ids=(item.id,),
                )
            )

    category_rows = []
    for category_id in sorted(taxonomy.categories):
        item = taxonomy.categories[category_id]
        placements = [
            {
                "content_type_id": content_type_id,
                "relative_folder": _portable_path(item.placements[content_type_id].relative_folder),
                "template": _repository_relative(item.placements[content_type_id].template, project.root),
            }
            for content_type_id in sorted(item.placements or {})
        ]
        category_rows.append(
            {
                "id": item.id,
                "lifecycle": item.lifecycle,
                "label": item.label,
                "plural_label": item.plural_label,
                "canonical_pages_enabled": item.canonical_pages_enabled,
                "metadata_type": item.metadata_type,
                "subject_slug_prefix": item.subject_slug_prefix,
                "subject_slug_pattern": item.subject_slug_pattern,
                "graph_class": item.graph_class,
                "placements": placements,
            }
        )
        if item.lifecycle == "deferred":
            diagnostics.append(
                _diagnostic(
                    "info",
                    "deferred-category",
                    f"Category `{item.id}` is deferred.",
                    path=f"categories.{item.id}.lifecycle",
                    related_ids=(item.id,),
                )
            )

    resource_roots = [
        {
            "id": root.id,
            "relative_path": _portable_path(root.relative_path),
            "required": root.required,
        }
        for root in project.resource_roots
    ]
    resource_kind_rows = [
        {
            "id": resources.kinds[kind_id].id,
            "label": resources.kinds[kind_id].label,
            "plural_label": resources.kinds[kind_id].plural_label,
        }
        for kind_id in sorted(resources.kinds)
    ]
    resource_type_rows = []
    for type_id in sorted(resources.types):
        item = resources.types[type_id]
        resource_type_rows.append(
            {
                "id": item.id,
                "lifecycle": item.lifecycle,
                "label": item.label,
                "plural_label": item.plural_label,
                "kind_id": item.kind_id,
                "authority": item.authority,
                "editor_enabled": item.editor_enabled,
                "placements": [
                    {
                        "root_id": placement.root_id,
                        "relative_path": _portable_path(placement.relative_path),
                        "tracking": placement.tracking,
                        "required": placement.required,
                    }
                    for placement in item.placements
                ],
            }
        )
        if item.lifecycle == "deferred":
            diagnostics.append(
                _diagnostic(
                    "info",
                    "deferred-resource-type",
                    f"Resource type `{item.id}` is deferred.",
                    path=f"resource_types.{item.id}.lifecycle",
                    related_ids=(item.id,),
                )
            )

    return EffectiveProjectSchema(
        project={
            "project_id": project.project_id,
            "framework_id": project.framework,
            "domain_id": project.domain,
            "project_manifest_schema_version": project.schema_version,
        },
        registry_schema_versions=(
            {"registry_id": "resources", "schema_version": resources.schema_version},
            {"registry_id": "schema-packs", "schema_version": packs.schema_version},
            {"registry_id": "taxonomy", "schema_version": taxonomy.schema_version},
        ),
        packs=tuple(pack_rows),
        capabilities=tuple(capability_rows),
        controlled_value_namespaces=tuple(namespace_rows),
        content={
            "roots": content_roots,
            "content_types": content_type_rows,
            "categories": category_rows,
        },
        resources={
            "roots": resource_roots,
            "kinds": resource_kind_rows,
            "types": resource_type_rows,
        },
        diagnostics=tuple(sorted(diagnostics, key=_diagnostic_key)),
    )


def _consumer_enablement_field(consumer_id: str) -> str:
    try:
        return CONSUMER_ENABLEMENT_FIELDS[consumer_id]
    except KeyError as exc:
        supported = ", ".join(sorted(CONSUMER_ENABLEMENT_FIELDS))
        raise ValueError(
            f"Unsupported effective-schema consumer `{consumer_id}`; expected one of: {supported}."
        ) from exc


def _legacy_capability_state(packs: SchemaPackRegistry, capability_id: str) -> dict[str, Any]:
    lifecycles = [
        packs.capability_definitions[(pack_id, capability_id)].lifecycle
        for pack_id in packs.capability_providers[capability_id]
    ]
    effective_lifecycle = (
        "available" if "available" in lifecycles else "deprecated" if "deprecated" in lifecycles else "planned"
    )
    return {
        "effective_lifecycle": effective_lifecycle,
        "available": effective_lifecycle in {"available", "deprecated"},
        "enabled": capability_id in packs.enabled_capabilities,
    }


def compose_legacy_consumer_schema_projection(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    taxonomy: TaxonomyConfig,
    consumer_id: str,
) -> dict[str, Any]:
    """Project the pre-effective-schema loader results used during consumer shadow adoption."""

    enablement_field = _consumer_enablement_field(consumer_id)
    content_types = {
        content_type.id: content_type
        for content_type in taxonomy.content_types.values()
        if content_type.lifecycle == "active"
        and content_type.canonical_pages_enabled
        and getattr(content_type, enablement_field)
    }
    root_ids = {content_type.content_root_id for content_type in content_types.values()}
    roots = {
        root.id: {
            "relative_path": _portable_path(root.relative_path),
            "provenance_mode": root.provenance_mode,
            "provenance_label": root.provenance_label,
        }
        for root in project.content_roots
        if root.id in root_ids
    }
    content_type_rows = {
        content_type_id: {
            "label": item.label,
            "plural_label": item.plural_label,
            "content_root_id": item.content_root_id,
            "category_policy": item.category_policy,
            "path_strategy": item.path_strategy,
            "metadata_type_mode": item.metadata_type_mode,
            "slug_mode": item.slug_mode,
            "metadata_type": item.metadata_type,
            "record_slug_prefix": item.record_slug_prefix,
            "qa_page_enabled": item.qa_page_enabled,
            "graph_enabled": item.graph_enabled,
        }
        for content_type_id, item in sorted(content_types.items())
    }

    categories: dict[str, dict[str, Any]] = {}
    placements: dict[str, dict[str, Any]] = {}
    graph_classes: dict[str, str] = {}
    for category_id, category in sorted(taxonomy.categories.items()):
        eligible_placements = {
            content_type_id: placement
            for content_type_id, placement in (category.placements or {}).items()
            if content_type_id in content_types
        }
        if category.lifecycle != "active" or not category.canonical_pages_enabled or not eligible_placements:
            continue
        categories[category_id] = {
            "label": category.label,
            "plural_label": category.plural_label,
            "metadata_type": category.metadata_type,
            "subject_slug_prefix": category.subject_slug_prefix,
            "subject_slug_pattern": category.subject_slug_pattern,
            "graph_class": category.graph_class,
        }
        if category.graph_class:
            graph_classes[category_id] = category.graph_class
        for content_type_id, placement in sorted(eligible_placements.items()):
            placement_id = f"{category_id}|{content_type_id}"
            placements[placement_id] = {
                "category_id": category_id,
                "content_type_id": content_type_id,
                "content_root_id": content_types[content_type_id].content_root_id,
                "relative_folder": _portable_path(placement.relative_folder),
                "template": _portable_path(placement.template),
            }

    return {
        "consumer_id": consumer_id,
        "roots": dict(sorted(roots.items())),
        "content_types": content_type_rows,
        "categories": categories,
        "placements": placements,
        "graph_classes": graph_classes,
        "capability_state": {
            capability_id: _legacy_capability_state(packs, capability_id)
            for capability_id in sorted(packs.declared_capabilities)
        },
    }


def compose_effective_consumer_schema_projection(
    schema: EffectiveProjectSchema,
    consumer_id: str,
) -> dict[str, Any]:
    """Project equivalent consumer configuration from one in-memory effective schema."""

    enablement_field = _consumer_enablement_field(consumer_id)
    content_types = {
        row["id"]: row
        for row in schema.content["content_types"]
        if row["lifecycle"] == "active" and row["canonical_pages_enabled"] and row[enablement_field]
    }
    root_ids = {row["content_root_id"] for row in content_types.values()}
    roots = {
        row["id"]: {
            "relative_path": row["relative_path"],
            "provenance_mode": row["provenance_mode"],
            "provenance_label": row["provenance_label"],
        }
        for row in schema.content["roots"]
        if row["id"] in root_ids
    }
    content_type_rows = {
        content_type_id: {
            "label": row["label"],
            "plural_label": row["plural_label"],
            "content_root_id": row["content_root_id"],
            "category_policy": row["category_policy"],
            "path_strategy": row["path_strategy"],
            "metadata_type_mode": row["metadata_type_mode"],
            "slug_mode": row["slug_mode"],
            "metadata_type": row["metadata_type"],
            "record_slug_prefix": row["record_slug_prefix"],
            "qa_page_enabled": row["qa_page_enabled"],
            "graph_enabled": row["graph_enabled"],
        }
        for content_type_id, row in sorted(content_types.items())
    }

    categories: dict[str, dict[str, Any]] = {}
    placements: dict[str, dict[str, Any]] = {}
    graph_classes: dict[str, str] = {}
    for category in schema.content["categories"]:
        eligible_placements = [
            placement for placement in category["placements"] if placement["content_type_id"] in content_types
        ]
        if category["lifecycle"] != "active" or not category["canonical_pages_enabled"] or not eligible_placements:
            continue
        category_id = category["id"]
        categories[category_id] = {
            "label": category["label"],
            "plural_label": category["plural_label"],
            "metadata_type": category["metadata_type"],
            "subject_slug_prefix": category["subject_slug_prefix"],
            "subject_slug_pattern": category["subject_slug_pattern"],
            "graph_class": category["graph_class"],
        }
        if category["graph_class"]:
            graph_classes[category_id] = category["graph_class"]
        for placement in eligible_placements:
            content_type_id = placement["content_type_id"]
            placement_id = f"{category_id}|{content_type_id}"
            placements[placement_id] = {
                "category_id": category_id,
                "content_type_id": content_type_id,
                "content_root_id": content_types[content_type_id]["content_root_id"],
                "relative_folder": placement["relative_folder"],
                "template": placement["template"],
            }

    return {
        "consumer_id": consumer_id,
        "roots": dict(sorted(roots.items())),
        "content_types": content_type_rows,
        "categories": categories,
        "placements": placements,
        "graph_classes": graph_classes,
        "capability_state": {
            row["id"]: {
                "effective_lifecycle": row["effective_lifecycle"],
                "available": row["available"],
                "enabled": row["enabled"],
            }
            for row in schema.capabilities
        },
    }


def compare_consumer_schema_projections(legacy: Any, effective: Any, path: str = "") -> tuple[str, ...]:
    """Return stable path-specific differences between legacy and effective projections."""

    differences: list[str] = []
    if isinstance(legacy, dict) and isinstance(effective, dict):
        for key in sorted(set(legacy) | set(effective)):
            child_path = f"{path}.{key}" if path else str(key)
            if key not in legacy:
                differences.append(f"{child_path}: missing from legacy; effective={effective[key]!r}")
            elif key not in effective:
                differences.append(f"{child_path}: legacy={legacy[key]!r}; missing from effective schema")
            else:
                differences.extend(compare_consumer_schema_projections(legacy[key], effective[key], child_path))
        return tuple(differences)
    if legacy != effective:
        differences.append(f"{path or '<root>'}: legacy={legacy!r}; effective={effective!r}")
    return tuple(differences)


def assert_consumer_schema_shadow(
    consumer_id: str,
    legacy: dict[str, Any],
    effective: dict[str, Any],
) -> None:
    differences = compare_consumer_schema_projections(legacy, effective)
    if differences:
        details = "\n".join(f"- {difference}" for difference in differences)
        raise ValueError(f"{consumer_id} effective-schema shadow mismatch:\n{details}")


def load_effective_project_schema(root: Path) -> EffectiveProjectSchema:
    project = load_project_config(root)
    return compose_effective_project_schema(
        project,
        load_schema_pack_registry(project),
        load_taxonomy_config(project),
        load_resource_config(project),
    )


def effective_schema_json(schema: EffectiveProjectSchema, *, indent: int | None = 2) -> str:
    return json.dumps(schema.to_dict(), ensure_ascii=False, indent=indent) + "\n"


def classify_composition_error(error: Exception) -> str:
    message = str(error).lower()
    if "requires unselected pack" in message:
        return "missing-pack-dependency"
    if "must be selected after dependency" in message:
        return "pack-dependency-order"
    if "requires" in message and "version" in message and "selected version" in message:
        return "incompatible-pack-dependency"
    if "provided by both" in message or "conflict" in message:
        return "provider-or-ownership-conflict"
    if "enables capability" in message or "capability_activation" in message:
        return "invalid-capability-activation"
    if "unknown" in message or "references" in message:
        return "unknown-reference"
    return "malformed-configuration"


def effective_schema_failure(error: Exception) -> dict[str, Any]:
    return {
        "contract": "effective-project-schema-result",
        "contract_version": CONTRACT_VERSION,
        "schema": None,
        "diagnostics": [
            {
                "severity": "error",
                "code": classify_composition_error(error),
                "message": str(error),
                "path": None,
                "related_ids": [],
            }
        ],
    }
