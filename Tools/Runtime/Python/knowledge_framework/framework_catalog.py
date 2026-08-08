"""Project-independent framework pack and capability catalog services."""

from __future__ import annotations

from dataclasses import dataclass
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
CONTRACT_VERSION = 1
SELECTION_CONTRACT_ID = "framework-catalog-selection"
SELECTION_CONTRACT_VERSION = 1
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
    capabilities: tuple[dict[str, Any], ...]
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
            },
            "summary": {
                "pack_count": len(self.packs),
                "capability_count": len(self.capabilities),
                "available_capability_count": sum(row["available"] for row in self.capabilities),
                "deprecated_capability_count": sum(row["deprecated"] for row in self.capabilities),
                "planned_capability_count": sum(row["planned"] for row in self.capabilities),
            },
            "packs": list(self.packs),
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
                "controlled_value_namespaces": _controlled_value_namespaces(pack),
                "discoverability": {"installed": True, "selectable": pack.lifecycle == "active"},
            }
        )
    return tuple(rows)


def _compose_capability_rows(packs: dict[str, SchemaPackConfig]) -> tuple[dict[str, Any], ...]:
    providers: dict[str, list[tuple[str, Any]]] = {}
    for pack_id in sorted(packs):
        pack = packs[pack_id]
        for capability_id in pack.capabilities:
            providers.setdefault(capability_id, []).append((pack_id, pack.capability_definitions[capability_id]))

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
                "providers": [
                    {
                        "pack_id": pack_id,
                        "lifecycle": definition.lifecycle,
                        "presentation": _capability_presentation(definition.presentation),
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
    return FrameworkCatalog(
        config=config,
        pack_configs=packs,
        packs=_compose_pack_rows(config, packs),
        capabilities=_compose_capability_rows(packs),
    )


def framework_catalog_json(catalog: FrameworkCatalog, *, indent: int | None = 2) -> str:
    return json.dumps(catalog.to_dict(), ensure_ascii=False, indent=indent) + "\n"


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


def compose_framework_catalog_selection(
    catalog: FrameworkCatalog,
    *,
    pack_id: str | None = None,
    capability_id: str | None = None,
) -> dict[str, Any]:
    if pack_id is None and capability_id is None:
        raise ValueError("Framework-catalog selection requires a pack or capability ID.")
    return {
        "contract": SELECTION_CONTRACT_ID,
        "contract_version": SELECTION_CONTRACT_VERSION,
        "catalog_contract_version": catalog.contract_version,
        "requested": {"pack": pack_id, "capability": capability_id},
        "packs": [] if pack_id is None else [_resolve_catalog_row(catalog.packs, pack_id, "pack", catalog)],
        "capabilities": (
            []
            if capability_id is None
            else [_resolve_catalog_row(catalog.capabilities, capability_id, "capability", catalog)]
        ),
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
