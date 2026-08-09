"""Project-independent framework pack and capability catalog services."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .framework_config import FrameworkConfig, load_framework_config
from .schema_pack_config import (
    STABLE_ID_PATTERN,
    CapabilityPresentation,
    PackClassification,
    PackPresentation,
    SchemaPackConfig,
    _validate_pack_presentation_composition,
    load_pack,
)


CONTRACT_ID = "framework-catalog"
CONTRACT_VERSION = 3
SELECTION_CONTRACT_ID = "framework-catalog-selection"
SELECTION_CONTRACT_VERSION = 3
PROJECT_VIEW_CONTRACT_ID = "framework-catalog-project-view"
PROJECT_VIEW_CONTRACT_VERSION = 3
PROJECT_VIEW_SELECTION_CONTRACT_ID = "framework-catalog-project-view-selection"
PROJECT_VIEW_SELECTION_CONTRACT_VERSION = 3
CAPABILITY_LIFECYCLE_PRECEDENCE = ("available", "deprecated", "planned")


class FrameworkCatalogError(ValueError):
    def __init__(self, classification: str, message: str):
        super().__init__(message)
        self.classification = classification


@dataclass(frozen=True)
class FrameworkCatalog:
    config: FrameworkConfig
    pack_configs: dict[str, SchemaPackConfig]
    packs: tuple[dict[str, Any], ...]
    capability_groups: tuple[dict[str, Any], ...]
    capabilities: tuple[dict[str, Any], ...]
    capability_roadmap: Any | None = None
    contract: str = CONTRACT_ID
    contract_version: int = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "contract_version": self.contract_version,
            "framework": {
                "id": self.config.framework_id,
                "manifest_path": _relative_path(self.config.manifest_path, self.config.root),
                "packs_root": _relative_path(self.config.packs_root, self.config.root),
                "lookup_registry": _relative_path(self.config.lookup_keys_registry, self.config.root),
                "lookup_algorithm": self.config.lookup_keys.algorithm,
                "unicode_version": self.config.lookup_keys.unicode_version,
                "capability_roadmap_registry": (
                    None
                    if self.config.capability_roadmap_registry is None
                    else _relative_path(self.config.capability_roadmap_registry, self.config.root)
                ),
                "capability_roadmap_schema_version": (
                    None if self.capability_roadmap is None else self.capability_roadmap.schema_version
                ),
            },
            "summary": {
                "pack_count": len(self.packs),
                "capability_group_count": len(self.capability_groups),
                "capability_count": len(self.capabilities),
                "available_capability_count": sum(row["available"] for row in self.capabilities),
                "deprecated_capability_count": sum(row["deprecated"] for row in self.capabilities),
                "planned_capability_count": sum(row["planned"] for row in self.capabilities),
                "scheduled_capability_count": sum(
                    row["delivery_traceability"] is not None
                    and row["delivery_traceability"]["disposition"] == "scheduled"
                    for row in self.capabilities
                ),
                "deferred_capability_count": sum(
                    row["delivery_traceability"] is not None
                    and row["delivery_traceability"]["disposition"] == "accepted-deferral"
                    for row in self.capabilities
                ),
            },
            "packs": list(self.packs),
            "capability_groups": list(self.capability_groups),
            "capabilities": list(self.capabilities),
        }


def _relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _presentation_entry(entry: Any) -> dict[str, str]:
    return {"id": entry.id, "label": entry.label, "description": entry.description}


def _pack_classification(value: PackClassification | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "family": value.family,
        "role": value.role,
        "scope": value.scope,
        "domains": list(value.domains),
        "bridge_pack_ids": list(value.bridge_pack_ids),
    }


def _pack_presentation(value: PackPresentation | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "localization_key": value.localization_key,
        "default_locale": value.default_locale,
        "label": value.label,
        "short_description": value.short_description,
        "long_description": value.long_description,
        "maturity": value.maturity,
        "intended_audiences": [_presentation_entry(entry) for entry in value.intended_audiences],
        "use_cases": [_presentation_entry(entry) for entry in value.use_cases],
        "examples": [_presentation_entry(entry) for entry in value.examples],
        "prerequisites": [_presentation_entry(entry) for entry in value.prerequisites],
        "provided_behaviors": [_presentation_entry(entry) for entry in value.provided_behaviors],
        "exclusions": [_presentation_entry(entry) for entry in value.exclusions],
        "documentation": [
            {
                "id": entry.id,
                "label": entry.label,
                "target_kind": entry.target_kind,
                "target": entry.target,
            }
            for entry in value.documentation
        ],
        "search_keywords": list(value.search_keywords),
        "visual": (
            None
            if value.visual is None
            else {"icon_id": value.visual.icon_id, "accent_token": value.visual.accent_token}
        ),
    }


def _capability_presentation(value: CapabilityPresentation | None) -> dict[str, str] | None:
    if value is None:
        return None
    return {
        "localization_key": value.localization_key,
        "label": value.label,
        "description": value.description,
    }


def _capability_relationships(value: Any) -> dict[str, list[str]]:
    return {
        "requires": list(value.requires),
        "recommends": list(value.recommends),
        "conflicts_with": list(value.conflicts_with),
    }


def _controlled_value_namespaces(pack: SchemaPackConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for namespace in sorted(pack.controlled_values):
        definitions = pack.controlled_value_definitions[namespace]
        rows.append(
            {
                "id": namespace,
                "values": [
                    {
                        "id": value_id,
                        "label": definitions[value_id].label,
                        "description": definitions[value_id].description,
                        "broader_value": definitions[value_id].broader_value,
                    }
                    for value_id in pack.controlled_values[namespace]
                ],
            }
        )
    return rows


def _validate_dependencies(packs: dict[str, SchemaPackConfig]) -> None:
    for pack_id in sorted(packs):
        pack = packs[pack_id]
        for dependency in pack.dependencies:
            installed = packs.get(dependency.pack_id)
            if installed is None:
                raise ValueError(f"Installed schema pack `{pack_id}` requires missing pack `{dependency.pack_id}`.")
            if installed.pack_version < dependency.minimum_version:
                raise ValueError(
                    f"Installed schema pack `{pack_id}` requires `{dependency.pack_id}` version "
                    f"{dependency.minimum_version} or newer; installed version is {installed.pack_version}."
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(pack_id: str, path: tuple[str, ...]) -> None:
        if pack_id in visiting:
            cycle_start = path.index(pack_id)
            cycle = (*path[cycle_start:], pack_id)
            raise ValueError(f"Installed schema-pack dependency graph contains a cycle: {' -> '.join(cycle)}.")
        if pack_id in visited:
            return
        visiting.add(pack_id)
        for dependency in sorted(packs[pack_id].dependencies, key=lambda item: item.pack_id):
            visit(dependency.pack_id, (*path, pack_id))
        visiting.remove(pack_id)
        visited.add(pack_id)

    for pack_id in sorted(packs):
        visit(pack_id, ())


def _discover_pack_configs(config: FrameworkConfig) -> dict[str, SchemaPackConfig]:
    candidates: list[tuple[str, Path]] = []
    directory_keys: dict[str, str] = {}
    resolved_files: dict[Path, str] = {}
    try:
        for directory in config.packs_root.iterdir():
            if not directory.is_dir():
                continue
            pack_path = directory / "pack.yaml"
            if not pack_path.is_file():
                continue
            pack_id = directory.name
            if not STABLE_ID_PATTERN.fullmatch(pack_id):
                raise ValueError(f"Installed schema-pack directory must be a lowercase kebab-case stable ID: {pack_id}")
            directory_key = pack_id.casefold()
            prior_directory = directory_keys.get(directory_key)
            if prior_directory is not None:
                raise ValueError(f"Installed schema-pack directories collide by case: {prior_directory}, {pack_id}.")
            directory_keys[directory_key] = pack_id
            resolved_file = pack_path.resolve()
            prior_file = resolved_files.get(resolved_file)
            if prior_file is not None:
                raise ValueError(
                    f"Installed schema packs `{prior_file}` and `{pack_id}` resolve to the same pack file."
                )
            resolved_files[resolved_file] = pack_id
            candidates.append((pack_id, pack_path))
    except (OSError, ValueError) as exc:
        raise FrameworkCatalogError("installed-pack-discovery", str(exc)) from exc

    packs: dict[str, SchemaPackConfig] = {}
    for pack_id, path in sorted(candidates):
        try:
            packs[pack_id] = load_pack(path, pack_id)
        except (OSError, TypeError, ValueError) as exc:
            raise FrameworkCatalogError("pack-parsing", str(exc)) from exc
    try:
        _validate_dependencies(packs)
        _validate_pack_presentation_composition(packs, sorted(packs))
    except (TypeError, ValueError) as exc:
        raise FrameworkCatalogError("catalog-composition", str(exc)) from exc
    return packs


def _compose_pack_rows(config: FrameworkConfig, packs: dict[str, SchemaPackConfig]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for pack_id in sorted(packs):
        pack = packs[pack_id]
        rows.append(
            {
                "id": pack.id,
                "record_id": f"framework-catalog:pack:{pack.id}",
                "path": _relative_path(pack.path, config.root),
                "schema_version": pack.schema_version,
                "pack_version": pack.pack_version,
                "lifecycle": pack.lifecycle,
                "kind": pack.kind,
                "classification": _pack_classification(pack.classification),
                "presentation": _pack_presentation(pack.presentation),
                "dependencies": [
                    {
                        "pack_id": dependency.pack_id,
                        "minimum_version": dependency.minimum_version,
                        "installed_version": packs[dependency.pack_id].pack_version,
                        "status": "satisfied",
                    }
                    for dependency in pack.dependencies
                ],
                "capability_ids": list(pack.capabilities),
                "capability_group_ids": [group.id for group in pack.capability_groups],
                "capability_group_contribution_ids": [
                    membership.group_id for membership in pack.capability_group_memberships
                ],
                "controlled_value_namespaces": _controlled_value_namespaces(pack),
                "discoverability": {"installed": True, "selectable": pack.lifecycle == "active"},
            }
        )
    return tuple(rows)


def _compose_capability_group_rows(packs: dict[str, SchemaPackConfig]) -> tuple[dict[str, Any], ...]:
    definitions: dict[str, tuple[str, Any]] = {}
    contributions: dict[str, list[dict[str, Any]]] = {}
    for pack_id in sorted(packs):
        pack = packs[pack_id]
        for group in pack.capability_groups:
            definitions[group.id] = (pack_id, group)
        for membership in pack.capability_group_memberships:
            contributions.setdefault(membership.group_id, []).append(
                {
                    "provider_pack_id": pack_id,
                    "order": membership.order,
                    "capability_ids": list(membership.capability_ids),
                }
            )

    rows: list[dict[str, Any]] = []
    for group_id, (owner_pack_id, definition) in sorted(
        definitions.items(), key=lambda item: (item[1][1].order, item[0])
    ):
        group_contributions = sorted(
            contributions.get(group_id, []),
            key=lambda row: (row["order"], row["provider_pack_id"]),
        )
        capability_ids = list(
            dict.fromkeys(
                capability_id
                for contribution in group_contributions
                for capability_id in contribution["capability_ids"]
            )
        )
        rows.append(
            {
                "id": group_id,
                "record_id": f"framework-catalog:capability-group:{group_id}",
                "order": definition.order,
                "presentation": _capability_presentation(definition.presentation),
                "owner_pack_id": owner_pack_id,
                "contributions": group_contributions,
                "capability_ids": capability_ids,
            }
        )
    return tuple(rows)


def _compose_capability_rows(
    packs: dict[str, SchemaPackConfig],
    delivery_traceability: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], ...]:
    delivery_traceability = delivery_traceability or {}
    providers: dict[str, list[tuple[str, Any]]] = {}
    capability_groups: dict[str, list[str]] = {}
    for pack_id in sorted(packs):
        pack = packs[pack_id]
        for capability_id in pack.capabilities:
            providers.setdefault(capability_id, []).append((pack_id, pack.capability_definitions[capability_id]))
        for membership in pack.capability_group_memberships:
            for capability_id in membership.capability_ids:
                groups = capability_groups.setdefault(capability_id, [])
                if membership.group_id not in groups:
                    groups.append(membership.group_id)

    rows: list[dict[str, Any]] = []
    for capability_id in sorted(providers):
        definitions = providers[capability_id]
        lifecycles = {definition.lifecycle for _, definition in definitions}
        effective_lifecycle = next(item for item in CAPABILITY_LIFECYCLE_PRECEDENCE if item in lifecycles)
        presentation = definitions[0][1].presentation
        rows.append(
            {
                "id": capability_id,
                "record_id": f"framework-catalog:capability:{capability_id}",
                "presentation": _capability_presentation(presentation),
                "effective_lifecycle": effective_lifecycle,
                "available": effective_lifecycle == "available",
                "deprecated": effective_lifecycle == "deprecated",
                "planned": effective_lifecycle == "planned",
                "delivery_traceability": deepcopy(delivery_traceability.get(capability_id)),
                "group_ids": capability_groups.get(capability_id, []),
                "relationships": _capability_relationships(definitions[0][1].relationships),
                "providers": [
                    {
                        "pack_id": pack_id,
                        "lifecycle": definition.lifecycle,
                        "presentation": _capability_presentation(definition.presentation),
                        "pack_dependencies": [dependency.pack_id for dependency in packs[pack_id].dependencies],
                        "controlled_value_namespace_ids": sorted(packs[pack_id].controlled_values),
                    }
                    for pack_id, definition in definitions
                ],
            }
        )
    return tuple(rows)


def load_framework_catalog(root: Path) -> FrameworkCatalog:
    try:
        config = load_framework_config(root)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        classification = "lookup-registry" if "lookup-key registry" in str(exc).casefold() else "installation-manifest"
        raise FrameworkCatalogError(classification, str(exc)) from exc
    packs = _discover_pack_configs(config)
    base_catalog = FrameworkCatalog(
        config=config,
        pack_configs=packs,
        packs=_compose_pack_rows(config, packs),
        capability_groups=_compose_capability_group_rows(packs),
        capabilities=_compose_capability_rows(packs),
    )
    if config.capability_roadmap_registry is None:
        return base_catalog
    try:
        from .capability_roadmap import (
            compose_capability_delivery_traceability,
            load_capability_roadmap_file,
        )

        roadmap = load_capability_roadmap_file(
            config.capability_roadmap_registry,
            framework_config=config,
            catalog=base_catalog,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise FrameworkCatalogError("catalog-composition", str(exc)) from exc
    return FrameworkCatalog(
        config=config,
        pack_configs=packs,
        packs=base_catalog.packs,
        capability_groups=base_catalog.capability_groups,
        capabilities=_compose_capability_rows(packs, compose_capability_delivery_traceability(roadmap)),
        capability_roadmap=roadmap,
    )


def framework_catalog_json(catalog: FrameworkCatalog, *, indent: int | None = 2) -> str:
    return json.dumps(catalog.to_dict(), ensure_ascii=False, indent=indent) + "\n"


def compose_framework_catalog_project_view(
    catalog: FrameworkCatalog,
    effective_schema: object,
) -> dict[str, Any]:
    schema = effective_schema.to_dict() if hasattr(effective_schema, "to_dict") else effective_schema
    if not isinstance(schema, dict) or schema.get("contract") != "effective-project-schema":
        raise TypeError("Framework catalog project view requires a validated EffectiveProjectSchema.")
    project = schema["project"]
    if project["framework_id"] != catalog.config.framework_id:
        raise ValueError(
            f"Project framework `{project['framework_id']}` does not match catalog framework "
            f"`{catalog.config.framework_id}`."
        )

    selected_packs = {row["id"]: row for row in schema["packs"]}
    selected_groups = {row["id"]: row for row in schema.get("capability_groups", [])}
    selected_capabilities = {row["id"]: row for row in schema["capabilities"]}
    catalog_pack_ids = {row["id"] for row in catalog.packs}
    catalog_group_ids = {row["id"] for row in catalog.capability_groups}
    catalog_capability_ids = {row["id"] for row in catalog.capabilities}
    missing_packs = sorted(set(selected_packs) - catalog_pack_ids)
    missing_groups = sorted(set(selected_groups) - catalog_group_ids)
    missing_capabilities = sorted(set(selected_capabilities) - catalog_capability_ids)
    if missing_packs:
        raise ValueError(
            "Effective schema selects pack(s) absent from the framework catalog: " + ", ".join(missing_packs) + "."
        )
    if missing_capabilities:
        raise ValueError(
            "Effective schema declares capability or capabilities absent from the framework catalog: "
            + ", ".join(missing_capabilities)
            + "."
        )
    if missing_groups:
        raise ValueError(
            "Effective schema includes capability group(s) absent from the framework catalog: "
            + ", ".join(missing_groups)
            + "."
        )

    pack_rows: list[dict[str, Any]] = []
    for catalog_row in catalog.packs:
        row = deepcopy(catalog_row)
        selected = catalog_row["id"] in selected_packs
        row["catalog_record_id"] = row["record_id"]
        row["record_id"] = f"framework-catalog-project-view:pack:{row['id']}"
        row["project_state"] = {
            "selected": selected,
            "available": bool(catalog_row["discoverability"]["selectable"]),
            "enabled": selected,
            "deprecated": False,
            "planned": catalog_row["lifecycle"] == "deferred",
            "used_by_project": selected,
            "unavailable_reason": (None if catalog_row["discoverability"]["selectable"] else "pack-lifecycle-deferred"),
        }
        pack_rows.append(row)

    group_rows: list[dict[str, Any]] = []
    for catalog_row in catalog.capability_groups:
        row = deepcopy(catalog_row)
        effective_row = selected_groups.get(catalog_row["id"])
        selected_capability_rows = [
            selected_capabilities[capability_id]
            for capability_id in catalog_row["capability_ids"]
            if capability_id in selected_capabilities
        ]
        row["catalog_record_id"] = row["record_id"]
        row["record_id"] = f"framework-catalog-project-view:capability-group:{row['id']}"
        row["project_state"] = {
            "selected": effective_row is not None,
            "available": any(capability["available"] for capability in selected_capability_rows),
            "enabled": any(capability["enabled"] for capability in selected_capability_rows),
            "deprecated": bool(selected_capability_rows)
            and all(capability["deprecated"] for capability in selected_capability_rows),
            "planned": bool(selected_capability_rows)
            and all(capability["planned"] for capability in selected_capability_rows),
            "used_by_project": any(capability["enabled"] for capability in selected_capability_rows),
            "unavailable_reason": (
                None
                if any(capability["available"] for capability in selected_capability_rows)
                else "no-selected-available-capabilities"
            ),
        }
        group_rows.append(row)

    capability_rows: list[dict[str, Any]] = []
    for catalog_row in catalog.capabilities:
        row = deepcopy(catalog_row)
        effective_row = selected_capabilities.get(catalog_row["id"])
        selected = effective_row is not None
        enabled = bool(effective_row and effective_row["enabled"])
        row["catalog_record_id"] = row["record_id"]
        row["record_id"] = f"framework-catalog-project-view:capability:{row['id']}"
        row["project_state"] = {
            "selected": selected,
            "available": bool(effective_row["available"] if selected else catalog_row["available"]),
            "enabled": enabled,
            "deprecated": bool(effective_row["deprecated"] if selected else catalog_row["deprecated"]),
            "planned": bool(effective_row["planned"] if selected else catalog_row["planned"]),
            "used_by_project": enabled,
            "unavailable_reason": (
                effective_row["unavailable_reason"]
                if selected
                else ("capability-lifecycle-planned" if catalog_row["planned"] else None)
            ),
        }
        capability_rows.append(row)

    return {
        "contract": PROJECT_VIEW_CONTRACT_ID,
        "contract_version": PROJECT_VIEW_CONTRACT_VERSION,
        "catalog_contract_version": catalog.contract_version,
        "effective_schema_contract_version": schema["contract_version"],
        "project": {
            "project_id": project["project_id"],
            "framework_id": project["framework_id"],
            "domain_id": project["domain_id"],
        },
        "summary": {
            "pack_count": len(pack_rows),
            "selected_pack_count": sum(row["project_state"]["selected"] for row in pack_rows),
            "available_pack_count": sum(row["project_state"]["available"] for row in pack_rows),
            "capability_count": len(capability_rows),
            "capability_group_count": len(group_rows),
            "selected_capability_group_count": sum(row["project_state"]["selected"] for row in group_rows),
            "enabled_capability_group_count": sum(row["project_state"]["enabled"] for row in group_rows),
            "selected_capability_count": sum(row["project_state"]["selected"] for row in capability_rows),
            "enabled_capability_count": sum(row["project_state"]["enabled"] for row in capability_rows),
            "available_capability_count": sum(row["project_state"]["available"] for row in capability_rows),
            "deprecated_capability_count": sum(row["project_state"]["deprecated"] for row in capability_rows),
            "planned_capability_count": sum(row["project_state"]["planned"] for row in capability_rows),
        },
        "packs": pack_rows,
        "capability_groups": group_rows,
        "capabilities": capability_rows,
    }


def framework_catalog_project_view_json(view: dict[str, Any], *, indent: int | None = 2) -> str:
    return json.dumps(view, ensure_ascii=False, indent=indent) + "\n"


def _resolve_catalog_row(
    rows: tuple[dict[str, Any], ...],
    value: str,
    record_name: str,
    catalog: FrameworkCatalog,
) -> dict[str, Any]:
    exact = [row for row in rows if row["id"] == value]
    if exact:
        return exact[0]
    normalized = catalog.config.lookup_keys.normalize(value)
    matches = [row for row in rows if catalog.config.lookup_keys.normalize(row["id"]) == normalized]
    if not matches:
        raise ValueError(f"Unknown framework-catalog {record_name} ID `{value}`.")
    if len(matches) > 1:
        match_ids = ", ".join(row["id"] for row in matches)
        raise ValueError(f"Ambiguous framework-catalog {record_name} ID `{value}`; matches: {match_ids}.")
    return matches[0]


def _filter_catalog_capabilities(
    rows: list[dict[str, Any]],
    *,
    provider_pack_ids: tuple[str, ...],
    lifecycles: tuple[str, ...],
    availability: tuple[str, ...],
    activation: tuple[str, ...],
    usage: tuple[str, ...],
    project_view: bool,
) -> list[dict[str, Any]]:
    allowed_lifecycles = {"available", "deprecated", "planned"}
    allowed_availability = {"available", "unavailable"}
    allowed_activation = {"enabled", "disabled"}
    allowed_usage = {"used", "unused"}
    for values, allowed, label in (
        (lifecycles, allowed_lifecycles, "lifecycle"),
        (availability, allowed_availability, "availability"),
        (activation, allowed_activation, "activation"),
        (usage, allowed_usage, "project usage"),
    ):
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Unknown capability {label} filter(s): {', '.join(sorted(unknown))}.")
    if not project_view and (activation or usage):
        raise ValueError("Capability activation and project-usage filters require a catalog project view.")

    filtered = rows
    if provider_pack_ids:
        providers = set(provider_pack_ids)
        filtered = [
            row for row in filtered if providers.intersection(provider["pack_id"] for provider in row["providers"])
        ]
    if lifecycles:
        filtered = [row for row in filtered if row["effective_lifecycle"] in set(lifecycles)]
    if availability:
        requested = set(availability)
        filtered = [row for row in filtered if ("available" if row["available"] else "unavailable") in requested]
    if activation:
        requested = set(activation)
        filtered = [
            row for row in filtered if ("enabled" if row["project_state"]["enabled"] else "disabled") in requested
        ]
    if usage:
        requested = set(usage)
        filtered = [
            row for row in filtered if ("used" if row["project_state"]["used_by_project"] else "unused") in requested
        ]
    return filtered


def compose_framework_catalog_selection(
    catalog: FrameworkCatalog,
    *,
    pack_id: str | None = None,
    group_id: str | None = None,
    capability_id: str | None = None,
    provider_pack_ids: tuple[str, ...] = (),
    lifecycles: tuple[str, ...] = (),
    availability: tuple[str, ...] = (),
    activation: tuple[str, ...] = (),
    usage: tuple[str, ...] = (),
) -> dict[str, Any]:
    if not any((pack_id, group_id, capability_id, provider_pack_ids, lifecycles, availability, activation, usage)):
        raise ValueError("Framework-catalog selection requires an ID or capability filter.")
    selected_groups = (
        []
        if group_id is None
        else [_resolve_catalog_row(catalog.capability_groups, group_id, "capability group", catalog)]
    )
    normalized_provider_ids = [
        _resolve_catalog_row(catalog.packs, value, "pack", catalog)["id"] for value in provider_pack_ids
    ]
    capability_query_requested = any(
        (group_id, capability_id, provider_pack_ids, lifecycles, availability, activation, usage)
    )
    capabilities = list(catalog.capabilities) if capability_query_requested else []
    if capability_id is not None:
        capabilities = [_resolve_catalog_row(catalog.capabilities, capability_id, "capability", catalog)]
    if selected_groups:
        group_capabilities = set(selected_groups[0]["capability_ids"])
        capabilities = [row for row in capabilities if row["id"] in group_capabilities]
    capabilities = _filter_catalog_capabilities(
        capabilities,
        provider_pack_ids=tuple(normalized_provider_ids),
        lifecycles=lifecycles,
        availability=availability,
        activation=activation,
        usage=usage,
        project_view=False,
    )
    if group_id is None and any((provider_pack_ids, lifecycles, availability, activation, usage, capability_id)):
        capability_ids = {row["id"] for row in capabilities}
        selected_groups = [
            row for row in catalog.capability_groups if capability_ids.intersection(row["capability_ids"])
        ]
    return {
        "contract": SELECTION_CONTRACT_ID,
        "contract_version": SELECTION_CONTRACT_VERSION,
        "catalog_contract_version": catalog.contract_version,
        "requested": {
            "pack": pack_id,
            "capability_group": group_id,
            "capability": capability_id,
            "filters": {
                "provider_pack_ids": normalized_provider_ids,
                "lifecycles": list(lifecycles),
                "availability": list(availability),
                "activation": list(activation),
                "usage": list(usage),
            },
        },
        "packs": [] if pack_id is None else [_resolve_catalog_row(catalog.packs, pack_id, "pack", catalog)],
        "capability_groups": selected_groups,
        "capabilities": capabilities,
    }


def compose_framework_catalog_project_view_selection(
    catalog: FrameworkCatalog,
    view: dict[str, Any],
    *,
    pack_id: str | None = None,
    group_id: str | None = None,
    capability_id: str | None = None,
    provider_pack_ids: tuple[str, ...] = (),
    lifecycles: tuple[str, ...] = (),
    availability: tuple[str, ...] = (),
    activation: tuple[str, ...] = (),
    usage: tuple[str, ...] = (),
) -> dict[str, Any]:
    if view.get("contract") != PROJECT_VIEW_CONTRACT_ID:
        raise TypeError("Project-view selection requires a FrameworkCatalogProjectView.")
    if not any((pack_id, group_id, capability_id, provider_pack_ids, lifecycles, availability, activation, usage)):
        raise ValueError("Framework-catalog project-view selection requires an ID or capability filter.")
    selected_groups = (
        []
        if group_id is None
        else [_resolve_catalog_row(tuple(view["capability_groups"]), group_id, "capability group", catalog)]
    )
    normalized_provider_ids = [
        _resolve_catalog_row(tuple(view["packs"]), value, "pack", catalog)["id"] for value in provider_pack_ids
    ]
    capability_query_requested = any(
        (group_id, capability_id, provider_pack_ids, lifecycles, availability, activation, usage)
    )
    capabilities = list(view["capabilities"]) if capability_query_requested else []
    if capability_id is not None:
        capabilities = [_resolve_catalog_row(tuple(view["capabilities"]), capability_id, "capability", catalog)]
    if selected_groups:
        group_capabilities = set(selected_groups[0]["capability_ids"])
        capabilities = [row for row in capabilities if row["id"] in group_capabilities]
    capabilities = _filter_catalog_capabilities(
        capabilities,
        provider_pack_ids=tuple(normalized_provider_ids),
        lifecycles=lifecycles,
        availability=availability,
        activation=activation,
        usage=usage,
        project_view=True,
    )
    if group_id is None and any((provider_pack_ids, lifecycles, availability, activation, usage, capability_id)):
        capability_ids = {row["id"] for row in capabilities}
        selected_groups = [
            row for row in view["capability_groups"] if capability_ids.intersection(row["capability_ids"])
        ]
    return {
        "contract": PROJECT_VIEW_SELECTION_CONTRACT_ID,
        "contract_version": PROJECT_VIEW_SELECTION_CONTRACT_VERSION,
        "project_view_contract_version": view["contract_version"],
        "requested": {
            "pack": pack_id,
            "capability_group": group_id,
            "capability": capability_id,
            "filters": {
                "provider_pack_ids": normalized_provider_ids,
                "lifecycles": list(lifecycles),
                "availability": list(availability),
                "activation": list(activation),
                "usage": list(usage),
            },
        },
        "packs": ([] if pack_id is None else [_resolve_catalog_row(tuple(view["packs"]), pack_id, "pack", catalog)]),
        "capability_groups": selected_groups,
        "capabilities": capabilities,
    }


def framework_catalog_failure(
    error: Exception,
    classification: str = "catalog-composition",
    *,
    message: str | None = None,
) -> dict[str, Any]:
    return {
        "contract": "framework-catalog-result",
        "contract_version": 1,
        "status": "failed",
        "catalog": None,
        "diagnostic": {"classification": classification, "message": str(error) if message is None else message},
    }
