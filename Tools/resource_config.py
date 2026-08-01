from dataclasses import dataclass
from pathlib import Path
import re

from project_config import ProjectConfig
from strict_yaml import load_yaml_file


SUPPORTED_RESOURCE_SCHEMA_VERSION = 1
LIFECYCLES = {"active", "deferred"}
AUTHORITIES = {"canonical", "supporting", "evidence", "operational", "generated", "temporary"}
TRACKING_MODES = {"tracked", "ignored", "mixed"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ResourceKindConfig:
    id: str
    label: str
    plural_label: str


@dataclass(frozen=True)
class ResourcePlacement:
    root_id: str
    relative_path: Path
    path: Path
    tracking: str
    required: bool


@dataclass(frozen=True)
class ResourceTypeConfig:
    id: str
    lifecycle: str
    label: str
    plural_label: str
    kind_id: str
    authority: str
    editor_enabled: bool
    placements: tuple[ResourcePlacement, ...]


@dataclass(frozen=True)
class ResourceConfig:
    path: Path
    schema_version: int
    kinds: dict[str, ResourceKindConfig]
    types: dict[str, ResourceTypeConfig]

    def reconciliation_targets(self) -> dict[str, dict[str, object]]:
        return {
            "resource-kind": self.kinds,
            "resource-type": self.types,
        }

    def reconciliation_provider(self) -> dict[str, object]:
        return {
            "provider_id": "resource",
            "targets": self.reconciliation_targets(),
            "aliases": {},
        }

    def reconciliation_target(self, target_type: str, target_id: str) -> object:
        targets = self.reconciliation_targets().get(target_type)
        if targets is None:
            raise ValueError(f"Unsupported resource reconciliation target type `{target_type}`.")
        if target_id not in targets:
            raise ValueError(f"Unknown {target_type} `{target_id}`.")
        return targets[target_id]


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Resource registry `{context}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Resource registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def require_bool(mapping: dict, key: str, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Resource registry `{context}.{key}` must be true or false.")
    return value


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Resource registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def resolve_placement(
    project: ProjectConfig,
    root_id: str,
    value: str,
    context: str,
    *,
    required: bool,
) -> tuple[Path, Path]:
    roots = {root.id: root for root in project.resource_roots}
    if root_id not in roots:
        raise ValueError(
            f"Resource registry `{context}` references unknown resource root `{root_id}`."
        )
    relative_path = Path(value)
    if relative_path.is_absolute():
        raise ValueError(f"Resource registry `{context}` must be relative: {value}")
    root_path = roots[root_id].path.resolve()
    path = (root_path / relative_path).resolve()
    if path != root_path and root_path not in path.parents:
        raise ValueError(
            f"Resource registry `{context}` escapes resource root `{root_id}`: {value}"
        )
    if required and not path.exists():
        raise ValueError(f"Resource registry `{context}` path does not exist: {path}")
    return relative_path, path


def load_resource_config(project: ProjectConfig) -> ResourceConfig:
    data = load_yaml_file(project.resources_registry, "resource registry", expected_schema_version=SUPPORTED_RESOURCE_SCHEMA_VERSION)

    registry = require_mapping(data, "root")
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_RESOURCE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported resource schema_version {schema_version!r}; "
            f"expected {SUPPORTED_RESOURCE_SCHEMA_VERSION}."
        )

    raw_kinds = require_mapping(registry.get("resource_kinds"), "resource_kinds")
    kinds: dict[str, ResourceKindConfig] = {}
    for kind_id, raw_kind in raw_kinds.items():
        context = f"resource_kinds.{kind_id}"
        validate_id(kind_id, context)
        kind = require_mapping(raw_kind, context)
        kinds[kind_id] = ResourceKindConfig(
            id=kind_id,
            label=require_string(kind, "label", context),
            plural_label=require_string(kind, "plural_label", context),
        )

    raw_types = require_mapping(registry.get("resource_types"), "resource_types")
    types: dict[str, ResourceTypeConfig] = {}
    seen_placements: dict[tuple[str, str], str] = {}
    for type_id, raw_type in raw_types.items():
        context = f"resource_types.{type_id}"
        validate_id(type_id, context)
        resource_type = require_mapping(raw_type, context)
        lifecycle = require_string(resource_type, "lifecycle", context)
        if lifecycle not in LIFECYCLES:
            raise ValueError(
                f"Resource registry `{context}.lifecycle` must be one of: "
                f"{', '.join(sorted(LIFECYCLES))}."
            )
        kind_id = require_string(resource_type, "kind_id", context)
        if kind_id not in kinds:
            raise ValueError(
                f"Resource registry `{context}.kind_id` references unknown kind `{kind_id}`."
            )
        authority = require_string(resource_type, "authority", context)
        if authority not in AUTHORITIES:
            raise ValueError(
                f"Resource registry `{context}.authority` must be one of: "
                f"{', '.join(sorted(AUTHORITIES))}."
            )
        raw_placements = resource_type.get("placements")
        if not isinstance(raw_placements, list) or (lifecycle == "active" and not raw_placements):
            raise ValueError(
                f"Resource registry `{context}.placements` must be a non-empty list "
                "for active resource types."
            )
        placements: list[ResourcePlacement] = []
        for index, raw_placement in enumerate(raw_placements or []):
            placement_context = f"{context}.placements[{index}]"
            placement = require_mapping(raw_placement, placement_context)
            root_id = require_string(placement, "root_id", placement_context)
            validate_id(root_id, f"{placement_context}.root_id")
            tracking = require_string(placement, "tracking", placement_context)
            if tracking not in TRACKING_MODES:
                raise ValueError(
                    f"Resource registry `{placement_context}.tracking` must be one of: "
                    f"{', '.join(sorted(TRACKING_MODES))}."
                )
            required = require_bool(placement, "required", placement_context)
            relative_path, path = resolve_placement(
                project,
                root_id,
                require_string(placement, "relative_path", placement_context),
                f"{placement_context}.relative_path",
                required=required,
            )
            placement_key = (root_id, str(relative_path).casefold())
            if placement_key in seen_placements:
                raise ValueError(
                    f"Resource registry duplicates placement `{root_id}/{relative_path}` "
                    f"between `{seen_placements[placement_key]}` and `{type_id}`."
                )
            seen_placements[placement_key] = type_id
            placements.append(
                ResourcePlacement(
                    root_id=root_id,
                    relative_path=relative_path,
                    path=path,
                    tracking=tracking,
                    required=required,
                )
            )
        types[type_id] = ResourceTypeConfig(
            id=type_id,
            lifecycle=lifecycle,
            label=require_string(resource_type, "label", context),
            plural_label=require_string(resource_type, "plural_label", context),
            kind_id=kind_id,
            authority=authority,
            editor_enabled=require_bool(resource_type, "editor_enabled", context),
            placements=tuple(placements),
        )

    return ResourceConfig(
        path=project.resources_registry,
        schema_version=schema_version,
        kinds=kinds,
        types=types,
    )
