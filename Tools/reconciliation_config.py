from dataclasses import dataclass
from pathlib import Path
import re

import yaml

from project_config import ProjectConfig
from schema_pack_config import SchemaPackRegistry, load_schema_pack_registry


SUPPORTED_RECONCILIATION_SCHEMA_VERSION = 1
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ReconciliationEndpoint:
    target_type: str
    target_id: str


@dataclass(frozen=True)
class ReconciliationRecord:
    id: str
    source_type: str
    source_id: str
    source_state: str
    source_label: str
    operation: str
    targets: tuple[ReconciliationEndpoint, ...]
    reason: str
    status: str
    superseded_by_id: str | None


@dataclass(frozen=True)
class ReconciliationResolution:
    outcome: str
    requested_type: str
    requested_id: str
    canonical_targets: tuple[ReconciliationEndpoint, ...]
    reconciliation_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationRegistry:
    path: Path
    schema_version: int
    records: tuple[ReconciliationRecord, ...]
    targets: dict[str, dict[str, object]]

    def reconciliation_target(self, target_type: str, target_id: str) -> object:
        records = self.targets.get(target_type)
        if records is None:
            raise ValueError(f"Unsupported reconciliation target type `{target_type}`.")
        if target_id not in records:
            raise ValueError(f"Unknown current {target_type} `{target_id}`.")
        return records[target_id]

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {"reconciliation-record": {record.id: record for record in self.records}}

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        if subject_type != "reconciliation-record":
            raise ValueError(f"Unsupported reconciliation provenance subject type `{subject_type}`.")
        records = self.provenance_targets()[subject_type]
        if subject_id not in records:
            raise ValueError(f"Unknown reconciliation-record `{subject_id}`.")
        return records[subject_id]

    def resolve(self, target_type: str, target_id: str) -> ReconciliationResolution:
        if target_type not in self.targets:
            raise ValueError(f"Unsupported reconciliation target type `{target_type}`.")
        active = {
            (record.source_type, record.source_id): record
            for record in self.records
            if record.status == "active"
        }
        requested = ReconciliationEndpoint(target_type, target_id)
        if (target_type, target_id) not in active:
            if target_id not in self.targets[target_type]:
                raise ValueError(f"Unknown current or historical {target_type} `{target_id}`.")
            return ReconciliationResolution(
                "canonical", target_type, target_id, (requested,), ()
            )

        paths: list[str] = []

        def walk(endpoint: ReconciliationEndpoint) -> tuple[ReconciliationEndpoint, ...]:
            record = active.get((endpoint.target_type, endpoint.target_id))
            if record is None:
                return (endpoint,)
            paths.append(record.id)
            if record.operation == "retire":
                return ()
            resolved: list[ReconciliationEndpoint] = []
            for target in record.targets:
                for item in walk(target):
                    if item not in resolved:
                        resolved.append(item)
            return tuple(resolved)

        canonical = walk(requested)
        first = active[(target_type, target_id)]
        outcome = (
            "retired" if not canonical else
            "ambiguous" if first.operation == "split" or len(canonical) > 1 else
            "redirected"
        )
        return ReconciliationResolution(
            outcome, target_type, target_id, canonical, tuple(dict.fromkeys(paths))
        )


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Reconciliation registry `{context}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Reconciliation registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def optional_string(mapping: dict, key: str, context: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Reconciliation registry `{context}.{key}` must be null or a non-empty string.")
    return value.strip()


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Reconciliation registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def validate_pack_value(
    schema_packs: SchemaPackRegistry, namespace: str, value: str, context: str
) -> None:
    if value not in schema_packs.allowed_values(namespace):
        raise ValueError(
            f"Reconciliation registry `{context}` uses unregistered {namespace} value `{value}`."
        )


def load_reconciliation_registry(
    project: ProjectConfig,
    providers: tuple[dict[str, dict[str, object]], ...],
    schema_packs: SchemaPackRegistry | None = None,
) -> ReconciliationRegistry:
    if schema_packs is None:
        schema_packs = load_schema_pack_registry(project)
    if not schema_packs.capability_enabled("stable-identity-reconciliation"):
        raise ValueError("Capability `stable-identity-reconciliation` must be enabled.")

    targets: dict[str, dict[str, object]] = {}
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            raise ValueError(
                f"Reconciliation provider {index} must be a mapping of target types to stable-record maps."
            )
        invalid_maps = [key for key, value in provider.items() if not isinstance(value, dict)]
        if invalid_maps:
            raise ValueError(
                "Reconciliation providers must expose stable-record mappings for: "
                + ", ".join(sorted(invalid_maps))
                + "."
            )
        overlap = set(targets) & set(provider)
        if overlap:
            raise ValueError(
                "Reconciliation target types have multiple providers: "
                + ", ".join(sorted(overlap))
                + "."
            )
        targets.update(provider)
    allowed_target_types = set(schema_packs.allowed_values("reconciliation.target-type"))
    provided_target_types = set(targets)
    missing = allowed_target_types - provided_target_types
    extra = provided_target_types - allowed_target_types
    if missing or extra:
        details = []
        if missing:
            details.append("missing providers: " + ", ".join(sorted(missing)))
        if extra:
            details.append("unregistered providers: " + ", ".join(sorted(extra)))
        raise ValueError("Reconciliation target-provider mismatch (" + "; ".join(details) + ").")

    try:
        data = yaml.safe_load(project.reconciliation_registry.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Unable to parse reconciliation registry {project.reconciliation_registry}: {exc}"
        ) from exc
    registry = require_mapping(data, "root")
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_RECONCILIATION_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported reconciliation schema_version {schema_version!r}; "
            f"expected {SUPPORTED_RECONCILIATION_SCHEMA_VERSION}."
        )
    raw_records = registry.get("records")
    if not isinstance(raw_records, list):
        raise ValueError("Reconciliation registry `records` must be a list.")

    records: list[ReconciliationRecord] = []
    record_ids: set[str] = set()
    active_sources: set[tuple[str, str]] = set()
    for index, raw_record in enumerate(raw_records):
        context = f"records[{index}]"
        item = require_mapping(raw_record, context)
        record_id = require_string(item, "id", context)
        validate_id(record_id, f"{context}.id")
        if record_id in record_ids:
            raise ValueError(f"Reconciliation record ID `{record_id}` is duplicated.")
        record_ids.add(record_id)
        source_type = require_string(item, "source_type", context)
        validate_pack_value(schema_packs, "reconciliation.target-type", source_type, f"{context}.source_type")
        source_id = require_string(item, "source_id", context)
        validate_id(source_id, f"{context}.source_id")
        source_state = require_string(item, "source_state", context)
        validate_pack_value(schema_packs, "reconciliation.source-state", source_state, f"{context}.source_state")
        source_label = require_string(item, "source_label", context)
        operation = require_string(item, "operation", context)
        validate_pack_value(schema_packs, "reconciliation.operation", operation, f"{context}.operation")
        reason = require_string(item, "reason", context)
        validate_pack_value(schema_packs, "reconciliation.reason", reason, f"{context}.reason")
        status = require_string(item, "status", context)
        validate_pack_value(schema_packs, "reconciliation.status", status, f"{context}.status")
        superseded_by_id = optional_string(item, "superseded_by_id", context)
        if superseded_by_id is not None:
            validate_id(superseded_by_id, f"{context}.superseded_by_id")

        raw_targets = item.get("targets")
        if not isinstance(raw_targets, list):
            raise ValueError(f"Reconciliation registry `{context}.targets` must be a list.")
        endpoints: list[ReconciliationEndpoint] = []
        seen_endpoints: set[tuple[str, str]] = set()
        for target_index, raw_target in enumerate(raw_targets):
            target_context = f"{context}.targets[{target_index}]"
            target = require_mapping(raw_target, target_context)
            target_type = require_string(target, "target_type", target_context)
            validate_pack_value(schema_packs, "reconciliation.target-type", target_type, f"{target_context}.target_type")
            target_id = require_string(target, "target_id", target_context)
            validate_id(target_id, f"{target_context}.target_id")
            if target_type != source_type:
                raise ValueError(f"Reconciliation registry `{target_context}` must preserve target type `{source_type}`.")
            key = (target_type, target_id)
            if key == (source_type, source_id):
                raise ValueError(f"Reconciliation registry `{target_context}` cannot target its own source.")
            if key in seen_endpoints:
                raise ValueError(f"Reconciliation registry `{context}.targets` repeats `{target_type}:{target_id}`.")
            seen_endpoints.add(key)
            endpoints.append(ReconciliationEndpoint(target_type, target_id))

        expected = 0 if operation == "retire" else 2 if operation == "split" else 1
        if (operation == "split" and len(endpoints) < expected) or (
            operation != "split" and len(endpoints) != expected
        ):
            requirement = "at least two" if operation == "split" else str(expected)
            raise ValueError(f"Reconciliation registry `{context}.targets` requires {requirement} target(s) for `{operation}`.")
        source_exists = source_id in targets[source_type]
        if (source_state == "present") != source_exists:
            expectation = "exist" if source_state == "present" else "be absent"
            raise ValueError(f"Reconciliation registry `{context}` source must {expectation} for source_state `{source_state}`.")
        if status == "active":
            if superseded_by_id is not None:
                raise ValueError(f"Reconciliation registry active `{record_id}` cannot have superseded_by_id.")
            source_key = (source_type, source_id)
            if source_key in active_sources:
                raise ValueError(f"Reconciliation source `{source_type}:{source_id}` has multiple active records.")
            active_sources.add(source_key)
        elif status == "superseded":
            if superseded_by_id is None:
                raise ValueError(f"Reconciliation registry superseded `{record_id}` requires superseded_by_id.")
        else:
            if superseded_by_id is not None:
                raise ValueError(f"Reconciliation registry reversed `{record_id}` cannot have superseded_by_id.")
            if source_state != "present":
                raise ValueError(f"Reconciliation registry reversed `{record_id}` requires a present source.")
        records.append(ReconciliationRecord(
            record_id, source_type, source_id, source_state, source_label,
            operation, tuple(endpoints), reason, status, superseded_by_id
        ))

    by_id = {record.id: record for record in records}
    for record in records:
        if record.superseded_by_id is not None:
            successor = by_id.get(record.superseded_by_id)
            if successor is None:
                raise ValueError(f"Reconciliation record `{record.id}` references unknown superseded_by_id `{record.superseded_by_id}`.")
            if (successor.source_type, successor.source_id) != (record.source_type, record.source_id):
                raise ValueError(f"Reconciliation record `{record.id}` supersession must retain the same source.")

    active = {(record.source_type, record.source_id): record for record in records if record.status == "active"}
    for record in active.values():
        for endpoint in record.targets:
            if endpoint.target_id not in targets[endpoint.target_type] and (
                endpoint.target_type, endpoint.target_id
            ) not in active:
                raise ValueError(f"Reconciliation record `{record.id}` targets unknown current or historical `{endpoint.target_type}:{endpoint.target_id}`.")

    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()
    def visit(key: tuple[str, str]) -> None:
        if key in visiting:
            raise ValueError(f"Reconciliation active resolution graph contains a cycle at `{key[0]}:{key[1]}`.")
        if key in visited or key not in active:
            return
        visiting.add(key)
        for endpoint in active[key].targets:
            visit((endpoint.target_type, endpoint.target_id))
        visiting.remove(key)
        visited.add(key)
    for key in active:
        visit(key)

    for record in records:
        seen: set[str] = set()
        current = record
        while current.superseded_by_id is not None:
            if current.id in seen:
                raise ValueError(f"Reconciliation supersession chain contains a cycle at `{current.id}`.")
            seen.add(current.id)
            current = by_id[current.superseded_by_id]
        if record.status == "superseded" and current.status != "active":
            raise ValueError(f"Reconciliation superseded record `{record.id}` must lead to an active record.")

    return ReconciliationRegistry(
        project.reconciliation_registry,
        schema_version,
        tuple(records),
        targets,
    )
