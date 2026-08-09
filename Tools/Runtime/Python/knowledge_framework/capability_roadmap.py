"""Strict project-independent capability-roadmap loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .framework_config import FrameworkConfig, load_framework_config
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 1
REGISTRY_ID = "capability-roadmap"
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:/")
DELIVERY_TARGET_KINDS = {"platform-phase"}
DISPOSITIONS = {"scheduled", "accepted-deferral"}
EVIDENCE_KINDS = {"compatibility", "conformance", "contract", "documentation", "extraction", "runtime"}


@dataclass(frozen=True)
class DeliveryTarget:
    id: str
    kind: str
    label: str
    plan_path: str
    plan_anchor: str


@dataclass(frozen=True)
class ImplementationEvidence:
    kind: str
    reference: str
    provider_pack_id: str | None


@dataclass(frozen=True)
class CapabilityTraceability:
    capability_id: str
    disposition: str
    delivery_target_id: str | None
    deferral_id: str | None
    rationale: str
    review_trigger: str | None
    platform_prerequisite_ids: tuple[str, ...]
    domain_capability_dependency_ids: tuple[str, ...]
    implementation_evidence: tuple[ImplementationEvidence, ...]


@dataclass(frozen=True)
class CapabilityRoadmap:
    config: FrameworkConfig
    registry_path: Path
    schema_version: int
    registry_id: str
    delivery_targets: tuple[DeliveryTarget, ...]
    capabilities: tuple[CapabilityTraceability, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "registry_id": self.registry_id,
            "delivery_targets": [
                {
                    "id": row.id,
                    "kind": row.kind,
                    "label": row.label,
                    "plan_path": row.plan_path,
                    "plan_anchor": row.plan_anchor,
                }
                for row in self.delivery_targets
            ],
            "capabilities": [
                {
                    "capability_id": row.capability_id,
                    "disposition": row.disposition,
                    "delivery_target_id": row.delivery_target_id,
                    "deferral_id": row.deferral_id,
                    "rationale": row.rationale,
                    "review_trigger": row.review_trigger,
                    "platform_prerequisite_ids": list(row.platform_prerequisite_ids),
                    "domain_capability_dependency_ids": list(row.domain_capability_dependency_ids),
                    "implementation_evidence": [
                        {
                            "kind": evidence.kind,
                            "reference": evidence.reference,
                            "provider_pack_id": evidence.provider_pack_id,
                        }
                        for evidence in row.implementation_evidence
                    ],
                }
                for row in self.capabilities
            ],
        }


def _require_mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Capability roadmap `{context}` must be a mapping.")
    return value


def _require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Capability roadmap `{context}.{key}` must be a non-empty string.")
    return value.strip()


def _require_stable_id(value: str, context: str) -> str:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Capability roadmap `{context}` must be a lowercase kebab-case stable ID: {value}")
    return value


def _require_string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Capability roadmap `{context}.{key}` must be a list of non-empty strings.")
    normalized = tuple(item.strip() for item in value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"Capability roadmap `{context}.{key}` contains duplicate values.")
    return tuple(sorted(normalized))


def _resolve_plan_path(framework_directory: Path, value: str, context: str) -> str:
    if "\\" in value:
        raise ValueError(f"Capability roadmap `{context}` must use forward slashes: {value}")
    segments = value.split("/")
    posix_path = PurePosixPath(value)
    if (
        posix_path.is_absolute()
        or WINDOWS_ABSOLUTE_PATTERN.match(value)
        or value.startswith("//")
        or any(segment in {"", ".", ".."} for segment in segments)
    ):
        raise ValueError(f"Capability roadmap `{context}` must be a confined framework-relative path: {value}")
    root = framework_directory.resolve()
    resolved = (root / Path(*segments)).resolve()
    if root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"Capability roadmap `{context}` file does not exist beneath Framework: {value}")
    return PurePosixPath(*segments).as_posix()


def _catalog_document(catalog: object) -> dict[str, Any]:
    document = catalog.to_dict() if hasattr(catalog, "to_dict") else catalog
    if not isinstance(document, dict) or document.get("contract") != "framework-catalog":
        raise TypeError("Capability roadmap validation requires a validated FrameworkCatalog.")
    return document


def _assert_acyclic(dependencies: dict[str, tuple[str, ...]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(capability_id: str) -> None:
        if capability_id in visited:
            return
        if capability_id in visiting:
            raise ValueError(
                f"Capability roadmap domain-capability delivery dependencies contain a cycle at `{capability_id}`."
            )
        visiting.add(capability_id)
        for dependency_id in dependencies.get(capability_id, ()):
            if dependency_id in dependencies:
                visit(dependency_id)
        visiting.remove(capability_id)
        visited.add(capability_id)

    for capability_id in sorted(dependencies):
        visit(capability_id)


def load_capability_roadmap_file(
    path: Path,
    *,
    framework_config: FrameworkConfig,
    catalog: object,
) -> CapabilityRoadmap:
    data = load_yaml_file(path, "capability roadmap", expected_schema_version=SUPPORTED_SCHEMA_VERSION)
    root = _require_mapping(data, "root")
    assert_allowed_keys(
        root,
        {"schema_version", "registry_id", "delivery_targets", "capabilities"},
        "Capability roadmap root",
    )
    registry_id = _require_stable_id(_require_string(root, "registry_id", "root"), "root.registry_id")
    if registry_id != REGISTRY_ID:
        raise ValueError(f"Capability roadmap `root.registry_id` must be `{REGISTRY_ID}`: {registry_id}")

    target_mapping = _require_mapping(root.get("delivery_targets"), "delivery_targets")
    targets: dict[str, DeliveryTarget] = {}
    for target_id in sorted(target_mapping):
        _require_stable_id(target_id, f"delivery_targets.{target_id}")
        context = f"delivery_targets.{target_id}"
        target = _require_mapping(target_mapping[target_id], context)
        assert_allowed_keys(target, {"kind", "label", "plan_path", "plan_anchor"}, f"Capability roadmap `{context}`")
        kind = _require_string(target, "kind", context)
        if kind not in DELIVERY_TARGET_KINDS:
            raise ValueError(
                f"Capability roadmap `{context}.kind` must be one of: {', '.join(sorted(DELIVERY_TARGET_KINDS))}."
            )
        targets[target_id] = DeliveryTarget(
            id=target_id,
            kind=kind,
            label=_require_string(target, "label", context),
            plan_path=_resolve_plan_path(
                framework_config.framework_directory,
                _require_string(target, "plan_path", context),
                f"{context}.plan_path",
            ),
            plan_anchor=_require_stable_id(
                _require_string(target, "plan_anchor", context),
                f"{context}.plan_anchor",
            ),
        )

    catalog_document = _catalog_document(catalog)
    catalog_capabilities = {row["id"]: row for row in catalog_document["capabilities"]}
    planned_ids = {capability_id for capability_id, row in catalog_capabilities.items() if row["planned"]}
    capability_mapping = _require_mapping(root.get("capabilities"), "capabilities")
    authored_ids = set(capability_mapping)
    missing = sorted(planned_ids - authored_ids)
    stale = sorted(authored_ids - planned_ids)
    if missing:
        raise ValueError("Capability roadmap is missing planned capability mapping(s): " + ", ".join(missing) + ".")
    if stale:
        unknown = [capability_id for capability_id in stale if capability_id not in catalog_capabilities]
        if unknown:
            raise ValueError("Capability roadmap references unknown capability ID(s): " + ", ".join(unknown) + ".")
        raise ValueError("Capability roadmap contains non-planned capability mapping(s): " + ", ".join(stale) + ".")

    capabilities: dict[str, CapabilityTraceability] = {}
    dependency_graph: dict[str, tuple[str, ...]] = {}
    for capability_id in sorted(capability_mapping):
        _require_stable_id(capability_id, f"capabilities.{capability_id}")
        context = f"capabilities.{capability_id}"
        entry = _require_mapping(capability_mapping[capability_id], context)
        common_keys = {
            "disposition",
            "rationale",
            "platform_prerequisite_ids",
            "domain_capability_dependency_ids",
            "implementation_evidence",
        }
        disposition = _require_string(entry, "disposition", context)
        if disposition not in DISPOSITIONS:
            raise ValueError(
                f"Capability roadmap `{context}.disposition` must be one of: {', '.join(sorted(DISPOSITIONS))}."
            )
        if disposition == "scheduled":
            assert_allowed_keys(entry, common_keys | {"delivery_target_id"}, f"Capability roadmap `{context}`")
            delivery_target_id = _require_stable_id(
                _require_string(entry, "delivery_target_id", context),
                f"{context}.delivery_target_id",
            )
            if delivery_target_id not in targets:
                raise ValueError(
                    f"Capability roadmap `{context}.delivery_target_id` references unknown delivery target: "
                    f"{delivery_target_id}"
                )
            deferral_id = None
            review_trigger = None
        else:
            assert_allowed_keys(
                entry,
                common_keys | {"deferral_id", "review_trigger"},
                f"Capability roadmap `{context}`",
            )
            delivery_target_id = None
            deferral_id = _require_stable_id(
                _require_string(entry, "deferral_id", context),
                f"{context}.deferral_id",
            )
            review_trigger = _require_string(entry, "review_trigger", context)

        prerequisites = _require_string_list(entry, "platform_prerequisite_ids", context)
        for prerequisite_id in prerequisites:
            _require_stable_id(prerequisite_id, f"{context}.platform_prerequisite_ids")
            if prerequisite_id not in targets:
                raise ValueError(
                    f"Capability roadmap `{context}.platform_prerequisite_ids` references unknown delivery target: "
                    f"{prerequisite_id}"
                )
            if prerequisite_id == delivery_target_id:
                raise ValueError(f"Capability roadmap `{context}` cannot depend on its own delivery target.")

        dependencies = _require_string_list(entry, "domain_capability_dependency_ids", context)
        for dependency_id in dependencies:
            _require_stable_id(dependency_id, f"{context}.domain_capability_dependency_ids")
            if dependency_id not in catalog_capabilities:
                raise ValueError(
                    f"Capability roadmap `{context}.domain_capability_dependency_ids` references unknown capability: "
                    f"{dependency_id}"
                )
            if dependency_id == capability_id:
                raise ValueError(f"Capability roadmap `{context}` cannot depend on itself.")

        evidence_rows = entry.get("implementation_evidence")
        if not isinstance(evidence_rows, list):
            raise ValueError(f"Capability roadmap `{context}.implementation_evidence` must be a list.")
        provider_ids = {provider["pack_id"] for provider in catalog_capabilities[capability_id]["providers"]}
        evidence: list[ImplementationEvidence] = []
        evidence_keys: set[tuple[str, str, str | None]] = set()
        for index, evidence_value in enumerate(evidence_rows):
            evidence_context = f"{context}.implementation_evidence[{index}]"
            evidence_row = _require_mapping(evidence_value, evidence_context)
            assert_allowed_keys(
                evidence_row,
                {"kind", "reference", "provider_pack_id"},
                f"Capability roadmap `{evidence_context}`",
            )
            evidence_kind = _require_string(evidence_row, "kind", evidence_context)
            if evidence_kind not in EVIDENCE_KINDS:
                raise ValueError(
                    f"Capability roadmap `{evidence_context}.kind` must be one of: "
                    + ", ".join(sorted(EVIDENCE_KINDS))
                    + "."
                )
            reference = _require_string(evidence_row, "reference", evidence_context)
            provider_pack_id = evidence_row.get("provider_pack_id")
            if provider_pack_id is not None:
                if not isinstance(provider_pack_id, str) or not provider_pack_id.strip():
                    raise ValueError(
                        f"Capability roadmap `{evidence_context}.provider_pack_id` must be a non-empty string."
                    )
                provider_pack_id = _require_stable_id(
                    provider_pack_id.strip(),
                    f"{evidence_context}.provider_pack_id",
                )
                if provider_pack_id not in provider_ids:
                    raise ValueError(
                        f"Capability roadmap `{evidence_context}.provider_pack_id` is not a provider of "
                        f"`{capability_id}`: {provider_pack_id}"
                    )
            evidence_key = (evidence_kind, reference, provider_pack_id)
            if evidence_key in evidence_keys:
                raise ValueError(f"Capability roadmap `{context}.implementation_evidence` contains duplicates.")
            evidence_keys.add(evidence_key)
            evidence.append(ImplementationEvidence(evidence_kind, reference, provider_pack_id))

        capabilities[capability_id] = CapabilityTraceability(
            capability_id=capability_id,
            disposition=disposition,
            delivery_target_id=delivery_target_id,
            deferral_id=deferral_id,
            rationale=_require_string(entry, "rationale", context),
            review_trigger=review_trigger,
            platform_prerequisite_ids=prerequisites,
            domain_capability_dependency_ids=dependencies,
            implementation_evidence=tuple(evidence),
        )
        dependency_graph[capability_id] = dependencies

    _assert_acyclic(dependency_graph)
    return CapabilityRoadmap(
        config=framework_config,
        registry_path=path.resolve(),
        schema_version=SUPPORTED_SCHEMA_VERSION,
        registry_id=registry_id,
        delivery_targets=tuple(targets[target_id] for target_id in sorted(targets)),
        capabilities=tuple(capabilities[capability_id] for capability_id in sorted(capabilities)),
    )


def load_capability_roadmap(root: Path, *, catalog: object | None = None) -> CapabilityRoadmap:
    if catalog is None:
        from .framework_catalog import load_framework_catalog

        catalog = load_framework_catalog(root)
    config = catalog.config if hasattr(catalog, "config") else load_framework_config(root)
    if config.capability_roadmap_registry is None:
        raise ValueError("Framework manifest schema 2 with `registries.capability_roadmap` is required.")
    return load_capability_roadmap_file(
        config.capability_roadmap_registry,
        framework_config=config,
        catalog=catalog,
    )
