"""Strict framework installation manifest loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from .framework_paths import FRAMEWORK_MANIFEST_PATH
from .lookup_key_config import LookupKeyConfig, load_lookup_key_registry
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_FRAMEWORK_SCHEMA_VERSION = 1
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:/")


@dataclass(frozen=True)
class FrameworkConfig:
    root: Path
    framework_directory: Path
    manifest_path: Path
    schema_version: int
    framework_id: str
    packs_relative_path: str
    packs_root: Path
    lookup_keys_relative_path: str
    lookup_keys_registry: Path
    lookup_keys: LookupKeyConfig


def _require_mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Framework manifest `{context}` must be a mapping.")
    return value


def _require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Framework manifest `{context}.{key}` must be a non-empty string.")
    return value.strip()


def _resolve_framework_path(
    framework_directory: Path,
    value: str,
    key: str,
    *,
    require_directory: bool,
) -> Path:
    if "\\" in value:
        raise ValueError(f"Framework manifest `{key}` must use forward slashes: {value}")
    segments = value.split("/")
    posix_path = PurePosixPath(value)
    if (
        posix_path.is_absolute()
        or WINDOWS_ABSOLUTE_PATTERN.match(value)
        or value.startswith("//")
        or any(segment in {"", ".", ".."} for segment in segments)
    ):
        raise ValueError(f"Framework manifest `{key}` must be a confined relative path: {value}")

    resolved_root = framework_directory.resolve()
    resolved = (resolved_root / Path(*segments)).resolve()
    if resolved_root not in resolved.parents:
        raise ValueError(f"Framework manifest `{key}` escapes the Framework directory: {value}")
    if require_directory:
        if not resolved.is_dir():
            raise ValueError(f"Framework manifest `{key}` directory does not exist: {value}")
    elif not resolved.is_file():
        raise ValueError(f"Framework manifest `{key}` file does not exist: {value}")
    return resolved


def load_framework_config(root: Path) -> FrameworkConfig:
    resolved_root = root.resolve()
    manifest_path = resolved_root / FRAMEWORK_MANIFEST_PATH
    data = load_yaml_file(
        manifest_path,
        "framework manifest",
        expected_schema_version=SUPPORTED_FRAMEWORK_SCHEMA_VERSION,
    )
    manifest = _require_mapping(data, "root")
    assert_allowed_keys(
        manifest,
        {"schema_version", "framework_id", "paths", "registries"},
        "Framework manifest root",
    )

    framework_id = _require_string(manifest, "framework_id", "root")
    if not STABLE_ID_PATTERN.fullmatch(framework_id):
        raise ValueError(
            f"Framework manifest `root.framework_id` must be a lowercase kebab-case stable ID: {framework_id}"
        )

    paths = _require_mapping(manifest.get("paths"), "paths")
    assert_allowed_keys(paths, {"packs"}, "Framework manifest `paths`")
    registries = _require_mapping(manifest.get("registries"), "registries")
    assert_allowed_keys(registries, {"lookup_keys"}, "Framework manifest `registries`")

    packs_relative_path = _require_string(paths, "packs", "paths")
    lookup_relative_path = _require_string(registries, "lookup_keys", "registries")
    framework_directory = manifest_path.parent
    packs_root = _resolve_framework_path(
        framework_directory,
        packs_relative_path,
        "paths.packs",
        require_directory=True,
    )
    lookup_registry = _resolve_framework_path(
        framework_directory,
        lookup_relative_path,
        "registries.lookup_keys",
        require_directory=False,
    )

    return FrameworkConfig(
        root=resolved_root,
        framework_directory=framework_directory,
        manifest_path=manifest_path,
        schema_version=SUPPORTED_FRAMEWORK_SCHEMA_VERSION,
        framework_id=framework_id,
        packs_relative_path=packs_relative_path,
        packs_root=packs_root,
        lookup_keys_relative_path=lookup_relative_path,
        lookup_keys_registry=lookup_registry,
        lookup_keys=load_lookup_key_registry(lookup_registry),
    )
