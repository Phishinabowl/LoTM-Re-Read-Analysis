"""Strict project-independent capability-roadmap loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .framework_config import FrameworkConfig, load_framework_config
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 2
REGISTRY_ID = "capability-roadmap"
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:/")
DELIVERY_TARGET_KINDS = {"platform-phase"}
DISPOSITIONS = {"scheduled", "accepted-deferral"}
EVIDENCE_CRITERIA = {
    "compatibility-impact",
    "conformance-ambiguity",
    "conformance-boundary",
    "conformance-malformed",
    "conformance-positive",
    "conformance-scale",
    "consumer-regression",
    "contract",
    "documentation",
    "emergency-decision",
    "evolution",
    "extraction-review",
    "migration-guidance",
    "runtime-parity",
    "runtime-support",
}
CAPABILITY_LIFECYCLES = {"available", "deprecated", "planned"}
TRANSITION_TYPES = {
    ("planned", "available"): "promotion",
    ("planned", None): "withdrawal",
    ("available", "deprecated"): "deprecation",
    ("deprecated", "available"): "rescission",
    ("deprecated", None): "removal",
    ("available", None): "emergency-removal",
}
PROMOTION_CRITERIA = {
    "compatibility-impact",
    "conformance-ambiguity",
    "conformance-boundary",
    "conformance-malformed",
    "conformance-positive",
    "conformance-scale",
    "consumer-regression",
    "contract",
    "documentation",
    "evolution",
    "extraction-review",
    "runtime-support",
}
TRANSITION_CRITERIA = {
    "promotion": PROMOTION_CRITERIA,
    "rescission": PROMOTION_CRITERIA,
    "withdrawal": {"compatibility-impact", "documentation", "evolution"},
    "deprecation": {
        "compatibility-impact",
        "consumer-regression",
        "documentation",
        "evolution",
        "migration-guidance",
    },
    "removal": {
        "compatibility-impact",
        "consumer-regression",
        "documentation",
        "evolution",
        "extraction-review",
        "migration-guidance",
    },
    "emergency-removal": {
        "compatibility-impact",
        "consumer-regression",
        "documentation",
        "emergency-decision",
        "evolution",
        "extraction-review",
        "migration-guidance",
    },
    "material-reshape": {
        "compatibility-impact",
        "conformance-boundary",
        "conformance-malformed",
        "conformance-positive",
        "consumer-regression",
        "contract",
        "documentation",
        "evolution",
        "extraction-review",
    },
}
PROVIDER_SCOPED_CRITERIA = {
    "conformance-ambiguity",
    "conformance-boundary",
    "conformance-malformed",
    "conformance-positive",
    "conformance-scale",
    "contract",
    "runtime-parity",
    "runtime-support",
}


@dataclass(frozen=True)
class DeliveryTarget:
    id: str
    kind: str
    label: str
    plan_path: str
    plan_anchor: str


@dataclass(frozen=True)
class ImplementationEvidence:
    criterion: str
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
                            "criterion": evidence.criterion,
                            "reference": evidence.reference,
                            "provider_pack_id": evidence.provider_pack_id,
                        }
                        for evidence in row.implementation_evidence
                    ],
                }
                for row in self.capabilities
            ],
        }


def compose_capability_delivery_traceability(roadmap: CapabilityRoadmap) -> dict[str, dict[str, Any]]:
    """Project validated roadmap rows into capability-owned diagnostic metadata."""

    targets = {row.id: row for row in roadmap.delivery_targets}
    projections: dict[str, dict[str, Any]] = {}
    for row in roadmap.capabilities:
        target = targets.get(row.delivery_target_id) if row.delivery_target_id is not None else None
        projections[row.capability_id] = {
            "disposition": row.disposition,
            "delivery_target": (
                None
                if target is None
                else {
                    "id": target.id,
                    "kind": target.kind,
                    "label": target.label,
                    "plan_path": target.plan_path,
                    "plan_anchor": target.plan_anchor,
                }
            ),
            "deferral": (
                None if row.deferral_id is None else {"id": row.deferral_id, "review_trigger": row.review_trigger}
            ),
            "rationale": row.rationale,
            "platform_prerequisite_ids": list(row.platform_prerequisite_ids),
            "domain_capability_dependency_ids": list(row.domain_capability_dependency_ids),
            "implementation_evidence": [
                {
                    "criterion": evidence.criterion,
                    "reference": evidence.reference,
                    "provider_pack_id": evidence.provider_pack_id,
                }
                for evidence in row.implementation_evidence
            ],
        }
    return projections


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
                {"criterion", "reference", "provider_pack_id"},
                f"Capability roadmap `{evidence_context}`",
            )
            evidence_criterion = _require_string(evidence_row, "criterion", evidence_context)
            if evidence_criterion not in EVIDENCE_CRITERIA:
                raise ValueError(
                    f"Capability roadmap `{evidence_context}.criterion` must be one of: "
                    + ", ".join(sorted(EVIDENCE_CRITERIA))
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
            if evidence_criterion in PROVIDER_SCOPED_CRITERIA and provider_pack_id is None:
                raise ValueError(
                    f"Capability roadmap `{evidence_context}.provider_pack_id` is required for "
                    f"criterion `{evidence_criterion}`."
                )
            evidence_key = (evidence_criterion, reference, provider_pack_id)
            if evidence_key in evidence_keys:
                raise ValueError(f"Capability roadmap `{context}.implementation_evidence` contains duplicates.")
            evidence_keys.add(evidence_key)
            evidence.append(ImplementationEvidence(evidence_criterion, reference, provider_pack_id))

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


def evaluate_capability_lifecycle_transition(
    *,
    capability_id: str,
    provider_pack_id: str,
    before_lifecycle: str,
    after_lifecycle: str | None,
    decision: dict[str, Any],
    known_capability_ids: set[str] | frozenset[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Evaluate governance evidence without mutating authoritative pack lifecycle."""

    capability_id = _require_stable_id(capability_id, "transition.capability_id")
    provider_pack_id = _require_stable_id(provider_pack_id, "transition.provider_pack_id")
    if before_lifecycle not in CAPABILITY_LIFECYCLES:
        raise ValueError(f"Capability lifecycle transition has unknown before lifecycle: {before_lifecycle}")
    if after_lifecycle is not None and after_lifecycle not in CAPABILITY_LIFECYCLES:
        raise ValueError(f"Capability lifecycle transition has unknown after lifecycle: {after_lifecycle}")
    if not isinstance(decision, dict):
        raise TypeError("Capability lifecycle transition decision must be a mapping.")
    assert_allowed_keys(
        decision,
        {
            "transition",
            "rationale",
            "replacement_capability_id",
            "roadmap_after_present",
            "roadmap_before_present",
            "runtime_behavior_changed",
            "runtime_parity_required",
            "evidence",
        },
        "Capability lifecycle transition decision",
    )

    expected_transition = (
        "material-reshape"
        if before_lifecycle == after_lifecycle
        else TRANSITION_TYPES.get((before_lifecycle, after_lifecycle))
    )
    transition = _require_string(decision, "transition", "transition")
    if expected_transition is None or transition != expected_transition:
        raise ValueError(
            "Capability lifecycle transition is invalid: "
            f"{before_lifecycle} -> {after_lifecycle or 'removed'} as `{transition}`."
        )
    _require_string(decision, "rationale", "transition")

    roadmap_before_present = decision.get("roadmap_before_present")
    roadmap_after_present = decision.get("roadmap_after_present")
    if not isinstance(roadmap_before_present, bool) or not isinstance(roadmap_after_present, bool):
        raise ValueError(
            "Capability lifecycle transition `roadmap_before_present` and `roadmap_after_present` must be booleans."
        )
    if roadmap_before_present != (before_lifecycle == "planned"):
        raise ValueError("Capability lifecycle transition before state has roadmap/lifecycle drift.")
    if roadmap_after_present != (after_lifecycle == "planned"):
        raise ValueError("Capability lifecycle transition after state has roadmap/lifecycle drift.")

    runtime_behavior_changed = decision.get("runtime_behavior_changed")
    runtime_parity_required = decision.get("runtime_parity_required")
    if not isinstance(runtime_behavior_changed, bool) or not isinstance(runtime_parity_required, bool):
        raise ValueError(
            "Capability lifecycle transition `runtime_behavior_changed` and `runtime_parity_required` must be booleans."
        )
    if transition in {"promotion", "rescission"} and not runtime_behavior_changed:
        raise ValueError(f"Capability lifecycle `{transition}` must declare changed runtime behavior.")
    if runtime_parity_required and not runtime_behavior_changed:
        raise ValueError("Capability lifecycle transition cannot require parity without runtime impact.")

    replacement_id = decision.get("replacement_capability_id")
    if replacement_id is not None:
        if not isinstance(replacement_id, str) or not replacement_id.strip():
            raise ValueError("Capability lifecycle transition replacement must be a stable capability ID or null.")
        replacement_id = _require_stable_id(replacement_id.strip(), "transition.replacement_capability_id")
        if replacement_id == capability_id:
            raise ValueError("Capability lifecycle transition cannot replace a capability with itself.")
        known_ids = set(known_capability_ids)
        if replacement_id not in known_ids:
            raise ValueError(f"Capability lifecycle transition references unknown replacement: {replacement_id}")

    evidence_rows = decision.get("evidence")
    if not isinstance(evidence_rows, list):
        raise ValueError("Capability lifecycle transition `evidence` must be a list.")
    present: set[str] = set()
    seen: set[tuple[str, str, str | None]] = set()
    for index, value in enumerate(evidence_rows):
        context = f"transition.evidence[{index}]"
        row = _require_mapping(value, context)
        assert_allowed_keys(row, {"criterion", "reference", "provider_pack_id"}, context)
        criterion = _require_string(row, "criterion", context)
        if criterion not in EVIDENCE_CRITERIA:
            raise ValueError(
                f"Capability lifecycle transition `{context}.criterion` must be one of: "
                + ", ".join(sorted(EVIDENCE_CRITERIA))
                + "."
            )
        reference = _require_string(row, "reference", context)
        evidence_provider = row.get("provider_pack_id")
        if evidence_provider is not None:
            if not isinstance(evidence_provider, str) or not evidence_provider.strip():
                raise ValueError(f"Capability lifecycle transition `{context}.provider_pack_id` is invalid.")
            evidence_provider = _require_stable_id(evidence_provider.strip(), f"{context}.provider_pack_id")
        if criterion in PROVIDER_SCOPED_CRITERIA and evidence_provider != provider_pack_id:
            raise ValueError(
                f"Capability lifecycle transition criterion `{criterion}` must name provider `{provider_pack_id}`."
            )
        key = (criterion, reference, evidence_provider)
        if key in seen:
            raise ValueError("Capability lifecycle transition evidence contains duplicates.")
        seen.add(key)
        present.add(criterion)

    required = set(TRANSITION_CRITERIA[transition])
    if runtime_behavior_changed:
        required.add("runtime-support")
    if runtime_parity_required:
        required.add("runtime-parity")
    missing = sorted(required - present)
    return {
        "capability_id": capability_id,
        "provider_pack_id": provider_pack_id,
        "transition": transition,
        "before_lifecycle": before_lifecycle,
        "after_lifecycle": after_lifecycle,
        "replacement_capability_id": replacement_id,
        "roadmap_before_present": roadmap_before_present,
        "roadmap_after_present": roadmap_after_present,
        "runtime_behavior_changed": runtime_behavior_changed,
        "runtime_parity_required": runtime_parity_required,
        "required_criteria": sorted(required),
        "present_criteria": sorted(present),
        "missing_criteria": missing,
        "ready": not missing,
    }


def load_capability_roadmap(root: Path, *, catalog: object | None = None) -> CapabilityRoadmap:
    if catalog is None:
        from .framework_catalog import load_framework_catalog

        catalog = load_framework_catalog(root)
        attached = getattr(catalog, "capability_roadmap", None)
        if attached is not None:
            return attached
    config = catalog.config if hasattr(catalog, "config") else load_framework_config(root)
    if config.capability_roadmap_registry is None:
        raise ValueError("Framework manifest schema 2 with `registries.capability_roadmap` is required.")
    return load_capability_roadmap_file(
        config.capability_roadmap_registry,
        framework_config=config,
        catalog=catalog,
    )
