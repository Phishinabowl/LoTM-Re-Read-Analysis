from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .occurrence_config import OccurrenceRegistry
from .project_config import ProjectConfig
from .schema_pack_config import SchemaPackRegistry
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 2
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class HostCarrier:
    id: str
    lifecycle: str
    carrier_kind: str
    label: str
    lifecycle_track_id: str
    activated_at_entry_id: str
    terminated_at_entry_id: str | None


@dataclass(frozen=True)
class HostedIdentityOccupancy:
    id: str
    subject_type: str
    subject_id: str
    carrier_id: str
    role: str
    activated_at_entry_id: str
    terminated_at_entry_id: str | None


@dataclass(frozen=True)
class HostedIdentityTransition:
    id: str
    transition_kind: str
    source_occupancy_id: str
    target_occupancy_id: str
    occurrence_id: str
    source_entry_id: str
    target_entry_id: str
    identity_relationship_type: str | None
    identity_relationship_id: str | None


@dataclass(frozen=True)
class HostCarrierBinding:
    id: str
    child_carrier_id: str
    parent_carrier_id: str
    binding_kind: str
    child_activated_at_entry_id: str
    parent_activated_at_entry_id: str
    child_terminated_at_entry_id: str | None
    parent_terminated_at_entry_id: str | None


@dataclass(frozen=True)
class HostCarrierPath:
    carrier_id: str
    binding_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReachableHostedIdentityOccupancy:
    occupancy: HostedIdentityOccupancy
    carrier_path: HostCarrierPath


@dataclass(frozen=True)
class HostedIdentityRegistry:
    path: Path
    schema_version: int
    enabled: bool
    carriers: dict[str, HostCarrier]
    occupancies: dict[str, HostedIdentityOccupancy]
    transitions: dict[str, HostedIdentityTransition]
    bindings: dict[str, HostCarrierBinding]
    occurrences: OccurrenceRegistry

    def occupancies_for_carrier(self, carrier_id: str) -> tuple[HostedIdentityOccupancy, ...]:
        self._known(self.carriers, carrier_id, "host carrier")
        return tuple(item for item in self.occupancies.values() if item.carrier_id == carrier_id)

    def occupancies_for_subject(self, subject_type: str, subject_id: str) -> tuple[HostedIdentityOccupancy, ...]:
        matches = tuple(
            item
            for item in self.occupancies.values()
            if item.subject_type == subject_type and item.subject_id == subject_id
        )
        if not matches:
            raise ValueError(f"Unknown hosted identity subject `{subject_type}:{subject_id}`.")
        return matches

    def carrier_active_at(self, carrier_id: str, entry_id: str) -> bool:
        carrier = self._known(self.carriers, carrier_id, "host carrier")
        boundary = self._entry_index(carrier.lifecycle_track_id, entry_id)
        activated = self._entry_index(carrier.lifecycle_track_id, carrier.activated_at_entry_id)
        if boundary < activated:
            return False
        if carrier.terminated_at_entry_id is None:
            return True
        return boundary < self._entry_index(carrier.lifecycle_track_id, carrier.terminated_at_entry_id)

    def occupancies_at(self, carrier_id: str, entry_id: str) -> tuple[HostedIdentityOccupancy, ...]:
        carrier = self._known(self.carriers, carrier_id, "host carrier")
        boundary = self._entry_index(carrier.lifecycle_track_id, entry_id)
        if not self.carrier_active_at(carrier_id, entry_id):
            return ()
        matches = []
        for item in self.occupancies_for_carrier(carrier_id):
            activated = self._entry_index(carrier.lifecycle_track_id, item.activated_at_entry_id)
            terminated = (
                self._entry_index(carrier.lifecycle_track_id, item.terminated_at_entry_id)
                if item.terminated_at_entry_id is not None
                else None
            )
            if activated <= boundary and (terminated is None or boundary < terminated):
                matches.append(item)
        return tuple(sorted(matches, key=lambda item: item.id))

    def controllers_at(self, carrier_id: str, entry_id: str) -> tuple[HostedIdentityOccupancy, ...]:
        return tuple(item for item in self.occupancies_at(carrier_id, entry_id) if item.role == "controlling")

    def bindings_for_child(self, carrier_id: str) -> tuple[HostCarrierBinding, ...]:
        self._known(self.carriers, carrier_id, "host carrier")
        return tuple(item for item in self.bindings.values() if item.child_carrier_id == carrier_id)

    def bindings_for_parent(self, carrier_id: str) -> tuple[HostCarrierBinding, ...]:
        self._known(self.carriers, carrier_id, "host carrier")
        return tuple(item for item in self.bindings.values() if item.parent_carrier_id == carrier_id)

    def binding_active_at(self, binding_id: str, boundary_entries: dict[str, str]) -> bool:
        binding = self._known(self.bindings, binding_id, "host carrier binding")
        child = self.carriers[binding.child_carrier_id]
        parent = self.carriers[binding.parent_carrier_id]
        return self._interval_active_at(
            child.lifecycle_track_id,
            binding.child_activated_at_entry_id,
            binding.child_terminated_at_entry_id,
            boundary_entries,
        ) and self._interval_active_at(
            parent.lifecycle_track_id,
            binding.parent_activated_at_entry_id,
            binding.parent_terminated_at_entry_id,
            boundary_entries,
        )

    def parents_at(self, carrier_id: str, boundary_entries: dict[str, str]) -> tuple[HostCarrierBinding, ...]:
        return tuple(
            item for item in self.bindings_for_child(carrier_id) if self.binding_active_at(item.id, boundary_entries)
        )

    def children_at(self, carrier_id: str, boundary_entries: dict[str, str]) -> tuple[HostCarrierBinding, ...]:
        return tuple(
            item for item in self.bindings_for_parent(carrier_id) if self.binding_active_at(item.id, boundary_entries)
        )

    def ancestors_at(self, carrier_id: str, boundary_entries: dict[str, str]) -> tuple[HostCarrierPath, ...]:
        return self._carrier_paths_at(carrier_id, boundary_entries, toward_parents=True)

    def descendants_at(self, carrier_id: str, boundary_entries: dict[str, str]) -> tuple[HostCarrierPath, ...]:
        return self._carrier_paths_at(carrier_id, boundary_entries, toward_parents=False)

    def reachable_occupancies_at(
        self, carrier_id: str, boundary_entries: dict[str, str]
    ) -> tuple[ReachableHostedIdentityOccupancy, ...]:
        self._known(self.carriers, carrier_id, "host carrier")
        paths = (HostCarrierPath(carrier_id, ()),) + self.descendants_at(carrier_id, boundary_entries)
        result = []
        for path in paths:
            carrier = self.carriers[path.carrier_id]
            entry_id = self._boundary_entry(boundary_entries, carrier.lifecycle_track_id)
            for occupancy in self.occupancies_at(path.carrier_id, entry_id):
                result.append(ReachableHostedIdentityOccupancy(occupancy, path))
        return tuple(
            sorted(
                result,
                key=lambda item: (len(item.carrier_path.binding_ids), item.carrier_path.binding_ids, item.occupancy.id),
            )
        )

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        if not self.enabled:
            return {}
        return {
            "host-carrier": self.carriers,
            "hosted-identity-occupancy": self.occupancies,
            "hosted-identity-transition": self.transitions,
            "host-carrier-binding": self.bindings,
        }

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.provenance_targets().get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported hosted-identity provenance subject type `{subject_type}`.")
        return self._known(targets, subject_id, subject_type)

    def reconciliation_targets(self) -> dict[str, dict[str, object]]:
        if not self.enabled:
            return {}
        return {"host-carrier": self.carriers}

    def reconciliation_provider(self) -> dict[str, object]:
        aliases = {"host-carrier": {}} if self.enabled else {}
        return {"provider_id": "hosting", "targets": self.reconciliation_targets(), "aliases": aliases}

    def _entry_index(self, track_id: str, entry_id: str) -> int:
        track = self._known(self.occurrences.tracks, track_id, "occurrence track")
        entry = self._known(self.occurrences.track_entries, entry_id, "occurrence track entry")
        if entry.track_id != track_id:
            raise ValueError(f"Track entry `{entry_id}` does not belong to track `{track_id}`.")
        return track.entry_ids.index(entry_id)

    def _boundary_entry(self, boundary_entries: dict[str, str], track_id: str) -> str:
        if not isinstance(boundary_entries, dict):
            raise ValueError("Host carrier boundary entries must be a mapping from track ID to entry ID.")
        entry_id = boundary_entries.get(track_id)
        if not isinstance(entry_id, str) or not entry_id.strip():
            raise ValueError(f"Host carrier boundary entries are missing lifecycle track `{track_id}`.")
        self._entry_index(track_id, entry_id)
        return entry_id

    def _interval_active_at(
        self,
        track_id: str,
        activated_at_entry_id: str,
        terminated_at_entry_id: str | None,
        boundary_entries: dict[str, str],
    ) -> bool:
        boundary = self._entry_index(track_id, self._boundary_entry(boundary_entries, track_id))
        activated = self._entry_index(track_id, activated_at_entry_id)
        if boundary < activated:
            return False
        return terminated_at_entry_id is None or boundary < self._entry_index(track_id, terminated_at_entry_id)

    def _carrier_paths_at(
        self, carrier_id: str, boundary_entries: dict[str, str], *, toward_parents: bool
    ) -> tuple[HostCarrierPath, ...]:
        self._known(self.carriers, carrier_id, "host carrier")
        result: list[HostCarrierPath] = []

        def visit(current_id: str, binding_ids: tuple[str, ...]) -> None:
            candidates = (
                self.parents_at(current_id, boundary_entries)
                if toward_parents
                else self.children_at(current_id, boundary_entries)
            )
            for binding in candidates:
                next_id = binding.parent_carrier_id if toward_parents else binding.child_carrier_id
                next_path = binding_ids + (binding.id,)
                result.append(HostCarrierPath(next_id, next_path))
                visit(next_id, next_path)

        visit(carrier_id, ())
        return tuple(sorted(result, key=lambda item: (len(item.binding_ids), item.carrier_id, item.binding_ids)))

    @staticmethod
    def _known(items: dict[str, object], item_id: str, kind: str):
        if item_id not in items:
            raise ValueError(f"Unknown {kind} `{item_id}`.")
        return items[item_id]


def _mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Hosted identity registry `{context}` must be a mapping.")
    return value


def _list(value: object, context: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"Hosted identity registry `{context}` must be a list.")
    return value


def _string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Hosted identity registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def _optional_string(mapping: dict, key: str, context: str) -> str | None:
    if key not in mapping or mapping[key] is None:
        return None
    return _string(mapping, key, context)


def _stable(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Hosted identity registry `{context}` must be a lowercase kebab-case stable ID: {value}")


def _pack_value(packs: SchemaPackRegistry, namespace: str, value: str, context: str) -> None:
    if value not in packs.allowed_values(namespace):
        raise ValueError(f"Hosted identity registry `{context}` value `{value}` is not allowed by `{namespace}`.")


def _provider_maps(providers: tuple[object, ...], method_name: str, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for provider in providers:
        method = getattr(provider, method_name, None)
        if method is None:
            raise ValueError(f"Hosted identity {label} provider does not expose {method_name}().")
        for target_type in method():
            if target_type in result:
                raise ValueError(f"Hosted identity {label} type `{target_type}` has multiple providers.")
            result[target_type] = provider
    return result


def _entry_index(occurrences: OccurrenceRegistry, track_id: str, entry_id: str, context: str) -> int:
    track = occurrences.tracks.get(track_id)
    if track is None:
        raise ValueError(f"{context} references unknown lifecycle track `{track_id}`.")
    entry = occurrences.track_entries.get(entry_id)
    if entry is None:
        raise ValueError(f"{context} references unknown track entry `{entry_id}`.")
    if entry.track_id != track_id:
        raise ValueError(f"{context} track entry `{entry_id}` does not belong to `{track_id}`.")
    return track.entry_ids.index(entry_id)


def _entry_occurrence_id(occurrences: OccurrenceRegistry, entry_id: str) -> str:
    entry = occurrences.track_entries[entry_id]
    return occurrences.occurrence_participations[entry.participation_id].occurrence_id


def _assert_binding_acyclic(bindings: dict[str, HostCarrierBinding]) -> None:
    parents: dict[str, list[str]] = {}
    for binding in bindings.values():
        parents.setdefault(binding.child_carrier_id, []).append(binding.parent_carrier_id)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(carrier_id: str) -> None:
        if carrier_id in visiting:
            raise ValueError(f"Host carrier bindings contain a cycle through `{carrier_id}`.")
        if carrier_id in visited:
            return
        visiting.add(carrier_id)
        for parent_id in sorted(parents.get(carrier_id, ())):
            visit(parent_id)
        visiting.remove(carrier_id)
        visited.add(carrier_id)

    for child_id in sorted(parents):
        visit(child_id)


def load_hosted_identity_registry(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    occurrences: OccurrenceRegistry,
    identity_providers: tuple[object, ...],
) -> HostedIdentityRegistry:
    data = load_yaml_file(
        project.hosting_registry,
        "hosted identity registry",
        expected_schema_version=SUPPORTED_SCHEMA_VERSION,
    )
    root = _mapping(data, "root")
    assert_allowed_keys(
        root,
        {"schema_version", "carriers", "bindings", "occupancies", "transitions"},
        "Hosted identity registry root",
    )

    carrier_rows = _mapping(root.get("carriers"), "carriers")
    binding_rows = _list(root.get("bindings"), "bindings")
    occupancy_rows = _list(root.get("occupancies"), "occupancies")
    transition_rows = _list(root.get("transitions"), "transitions")
    enabled = packs.capability_enabled("hosted-identity-embodiment")
    if not enabled:
        if carrier_rows or binding_rows or occupancy_rows or transition_rows:
            raise ValueError("Hosted identity records require enabled capability `hosted-identity-embodiment`.")
        return HostedIdentityRegistry(
            project.hosting_registry,
            SUPPORTED_SCHEMA_VERSION,
            False,
            {},
            {},
            {},
            {},
            occurrences,
        )

    identity_targets = _provider_maps(identity_providers, "identity_targets", "identity-target")
    provenance_targets = _provider_maps(identity_providers, "provenance_targets", "relationship-target")

    carriers: dict[str, HostCarrier] = {}
    for carrier_id, raw in carrier_rows.items():
        _stable(carrier_id, f"carriers.{carrier_id}")
        context = f"carriers.{carrier_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "lifecycle",
                "carrier_kind",
                "label",
                "lifecycle_track_id",
                "activated_at_entry_id",
                "terminated_at_entry_id",
            },
            f"Hosted identity registry `{context}`",
        )
        lifecycle = _string(item, "lifecycle", context)
        carrier_kind = _string(item, "carrier_kind", context)
        _pack_value(packs, "hosting.record-lifecycle", lifecycle, f"{context}.lifecycle")
        _pack_value(packs, "hosting.carrier-kind", carrier_kind, f"{context}.carrier_kind")
        track_id = _string(item, "lifecycle_track_id", context)
        activated_id = _string(item, "activated_at_entry_id", context)
        terminated_id = _optional_string(item, "terminated_at_entry_id", context)
        activated = _entry_index(occurrences, track_id, activated_id, context)
        if terminated_id is not None and _entry_index(occurrences, track_id, terminated_id, context) <= activated:
            raise ValueError(f"{context}.terminated_at_entry_id must follow activation on the lifecycle track.")
        carriers[carrier_id] = HostCarrier(
            carrier_id,
            lifecycle,
            carrier_kind,
            _string(item, "label", context),
            track_id,
            activated_id,
            terminated_id,
        )

    bindings: dict[str, HostCarrierBinding] = {}
    semantic_bindings: set[tuple[str, str, str, int, int, int | None, int | None]] = set()
    for index, raw in enumerate(binding_rows):
        context = f"bindings[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id",
                "child_carrier_id",
                "parent_carrier_id",
                "binding_kind",
                "child_activated_at_entry_id",
                "parent_activated_at_entry_id",
                "child_terminated_at_entry_id",
                "parent_terminated_at_entry_id",
            },
            f"Hosted identity registry `{context}`",
        )
        binding_id = _string(item, "id", context)
        _stable(binding_id, f"{context}.id")
        if binding_id in bindings:
            raise ValueError(f"Host carrier binding ID `{binding_id}` is duplicated.")
        child_id = _string(item, "child_carrier_id", context)
        parent_id = _string(item, "parent_carrier_id", context)
        if child_id == parent_id or child_id not in carriers or parent_id not in carriers:
            raise ValueError(f"{context} must reference two distinct known carrier endpoints.")
        kind = _string(item, "binding_kind", context)
        _pack_value(packs, "hosting.binding-kind", kind, f"{context}.binding_kind")
        child = carriers[child_id]
        parent = carriers[parent_id]
        child_activated_id = _string(item, "child_activated_at_entry_id", context)
        parent_activated_id = _string(item, "parent_activated_at_entry_id", context)
        child_terminated_id = _optional_string(item, "child_terminated_at_entry_id", context)
        parent_terminated_id = _optional_string(item, "parent_terminated_at_entry_id", context)
        if (child_terminated_id is None) != (parent_terminated_id is None):
            raise ValueError(f"{context} child and parent termination boundaries must be supplied together.")
        child_activated = _entry_index(
            occurrences, child.lifecycle_track_id, child_activated_id, f"{context}.child_activated_at_entry_id"
        )
        parent_activated = _entry_index(
            occurrences, parent.lifecycle_track_id, parent_activated_id, f"{context}.parent_activated_at_entry_id"
        )
        child_terminated = (
            _entry_index(
                occurrences,
                child.lifecycle_track_id,
                child_terminated_id,
                f"{context}.child_terminated_at_entry_id",
            )
            if child_terminated_id is not None
            else None
        )
        parent_terminated = (
            _entry_index(
                occurrences,
                parent.lifecycle_track_id,
                parent_terminated_id,
                f"{context}.parent_terminated_at_entry_id",
            )
            if parent_terminated_id is not None
            else None
        )
        if _entry_occurrence_id(occurrences, child_activated_id) != _entry_occurrence_id(
            occurrences, parent_activated_id
        ):
            raise ValueError(f"{context} activation boundaries must resolve to one occurrence.")
        if child_terminated_id is not None and _entry_occurrence_id(
            occurrences, child_terminated_id
        ) != _entry_occurrence_id(occurrences, parent_terminated_id):
            raise ValueError(f"{context} termination boundaries must resolve to one occurrence.")
        if child_terminated is not None and child_terminated <= child_activated:
            raise ValueError(f"{context} child termination must follow activation.")
        if parent_terminated is not None and parent_terminated <= parent_activated:
            raise ValueError(f"{context} parent termination must follow activation.")
        for carrier, activated, terminated in (
            (child, child_activated, child_terminated),
            (parent, parent_activated, parent_terminated),
        ):
            carrier_start = _entry_index(
                occurrences,
                carrier.lifecycle_track_id,
                carrier.activated_at_entry_id,
                f"carriers.{carrier.id}",
            )
            carrier_end = (
                _entry_index(
                    occurrences,
                    carrier.lifecycle_track_id,
                    carrier.terminated_at_entry_id,
                    f"carriers.{carrier.id}",
                )
                if carrier.terminated_at_entry_id is not None
                else None
            )
            if activated < carrier_start or (carrier_end is not None and activated >= carrier_end):
                raise ValueError(f"{context} activates outside carrier `{carrier.id}` lifecycle.")
            if carrier_end is not None and (terminated is None or terminated > carrier_end):
                raise ValueError(f"{context} extends beyond carrier `{carrier.id}` lifecycle.")
        shape = (
            child_id,
            parent_id,
            kind,
            child_activated,
            parent_activated,
            child_terminated,
            parent_terminated,
        )
        if shape in semantic_bindings:
            raise ValueError(f"Host carrier binding `{binding_id}` duplicates another binding.")
        semantic_bindings.add(shape)
        bindings[binding_id] = HostCarrierBinding(
            binding_id,
            child_id,
            parent_id,
            kind,
            child_activated_id,
            parent_activated_id,
            child_terminated_id,
            parent_terminated_id,
        )
    _assert_binding_acyclic(bindings)

    occupancies: dict[str, HostedIdentityOccupancy] = {}
    semantic_occupancies: set[tuple[str, str, str, str, int, int | None]] = set()
    for index, raw in enumerate(occupancy_rows):
        context = f"occupancies[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id",
                "subject_type",
                "subject_id",
                "carrier_id",
                "role",
                "activated_at_entry_id",
                "terminated_at_entry_id",
            },
            f"Hosted identity registry `{context}`",
        )
        occupancy_id = _string(item, "id", context)
        _stable(occupancy_id, f"{context}.id")
        if occupancy_id in occupancies:
            raise ValueError(f"Hosted identity occupancy ID `{occupancy_id}` is duplicated.")
        subject_type = _string(item, "subject_type", context)
        subject_id = _string(item, "subject_id", context)
        provider = identity_targets.get(subject_type)
        if provider is None:
            raise ValueError(f"{context}.subject_type references unsupported identity type `{subject_type}`.")
        provider.identity_target(subject_type, subject_id)
        carrier_id = _string(item, "carrier_id", context)
        if carrier_id not in carriers:
            raise ValueError(f"{context}.carrier_id references unknown carrier `{carrier_id}`.")
        carrier = carriers[carrier_id]
        role = _string(item, "role", context)
        _pack_value(packs, "hosting.occupancy-role", role, f"{context}.role")
        activated_id = _string(item, "activated_at_entry_id", context)
        terminated_id = _optional_string(item, "terminated_at_entry_id", context)
        activated = _entry_index(occurrences, carrier.lifecycle_track_id, activated_id, context)
        terminated = (
            _entry_index(occurrences, carrier.lifecycle_track_id, terminated_id, context)
            if terminated_id is not None
            else None
        )
        carrier_start = _entry_index(
            occurrences, carrier.lifecycle_track_id, carrier.activated_at_entry_id, f"carriers.{carrier_id}"
        )
        carrier_end = (
            _entry_index(
                occurrences, carrier.lifecycle_track_id, carrier.terminated_at_entry_id, f"carriers.{carrier_id}"
            )
            if carrier.terminated_at_entry_id is not None
            else None
        )
        if activated < carrier_start or (carrier_end is not None and activated >= carrier_end):
            raise ValueError(f"{context} activates outside carrier `{carrier_id}` lifecycle.")
        if terminated is not None and terminated <= activated:
            raise ValueError(f"{context}.terminated_at_entry_id must follow activation.")
        if carrier_end is not None and (terminated is None or terminated > carrier_end):
            raise ValueError(f"{context} extends beyond carrier `{carrier_id}` lifecycle.")
        shape = (subject_type, subject_id, carrier_id, role, activated, terminated)
        if shape in semantic_occupancies:
            raise ValueError(f"Hosted identity occupancy `{occupancy_id}` duplicates another occupancy.")
        semantic_occupancies.add(shape)
        occupancies[occupancy_id] = HostedIdentityOccupancy(
            occupancy_id, subject_type, subject_id, carrier_id, role, activated_id, terminated_id
        )

    transitions: dict[str, HostedIdentityTransition] = {}
    semantic_transitions: set[tuple[str, str, str, str]] = set()
    for index, raw in enumerate(transition_rows):
        context = f"transitions[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id",
                "transition_kind",
                "source_occupancy_id",
                "target_occupancy_id",
                "occurrence_id",
                "source_entry_id",
                "target_entry_id",
                "identity_relationship_type",
                "identity_relationship_id",
            },
            f"Hosted identity registry `{context}`",
        )
        transition_id = _string(item, "id", context)
        _stable(transition_id, f"{context}.id")
        if transition_id in transitions:
            raise ValueError(f"Hosted identity transition ID `{transition_id}` is duplicated.")
        kind = _string(item, "transition_kind", context)
        _pack_value(packs, "hosting.transition-kind", kind, f"{context}.transition_kind")
        source_id = _string(item, "source_occupancy_id", context)
        target_id = _string(item, "target_occupancy_id", context)
        if source_id == target_id or source_id not in occupancies or target_id not in occupancies:
            raise ValueError(f"{context} must reference two distinct known occupancy endpoints.")
        source = occupancies[source_id]
        target = occupancies[target_id]
        occurrence_id = _string(item, "occurrence_id", context)
        if occurrence_id not in occurrences.occurrences:
            raise ValueError(f"{context}.occurrence_id references unknown occurrence `{occurrence_id}`.")
        source_entry_id = _string(item, "source_entry_id", context)
        target_entry_id = _string(item, "target_entry_id", context)
        source_carrier = carriers[source.carrier_id]
        target_carrier = carriers[target.carrier_id]
        _entry_index(occurrences, source_carrier.lifecycle_track_id, source_entry_id, context)
        _entry_index(occurrences, target_carrier.lifecycle_track_id, target_entry_id, context)
        source_entry = occurrences.track_entries[source_entry_id]
        target_entry = occurrences.track_entries[target_entry_id]
        source_occurrence = occurrences.occurrence_participations[source_entry.participation_id].occurrence_id
        target_occurrence = occurrences.occurrence_participations[target_entry.participation_id].occurrence_id
        if source_occurrence != occurrence_id or target_occurrence != occurrence_id:
            raise ValueError(f"{context} boundary entries must resolve to occurrence `{occurrence_id}`.")
        if target.activated_at_entry_id != target_entry_id:
            raise ValueError(f"{context}.target_entry_id must activate the target occupancy.")
        relationship_type = _optional_string(item, "identity_relationship_type", context)
        relationship_id = _optional_string(item, "identity_relationship_id", context)
        if (relationship_type is None) != (relationship_id is None):
            raise ValueError(f"{context} identity relationship type and ID must be supplied together.")
        same_subject = (source.subject_type, source.subject_id) == (target.subject_type, target.subject_id)
        if kind == "move":
            if (
                not same_subject
                or source.carrier_id == target.carrier_id
                or relationship_type is not None
                or source.terminated_at_entry_id != source_entry_id
            ):
                raise ValueError(f"{context} move requires one unchanged subject crossing distinct carriers.")
        elif kind == "copy":
            if same_subject or source.carrier_id == target.carrier_id or relationship_type is None:
                raise ValueError(f"{context} copy requires distinct subjects, carriers, and an identity relationship.")
            _pack_value(
                packs,
                "hosting.identity-relationship-target-type",
                relationship_type,
                f"{context}.identity_relationship_type",
            )
            provider = provenance_targets.get(relationship_type)
            if provider is None:
                raise ValueError(f"{context} references unsupported identity relationship type `{relationship_type}`.")
            provider.provenance_target(relationship_type, relationship_id)
            source_activated = _entry_index(
                occurrences, source_carrier.lifecycle_track_id, source.activated_at_entry_id, context
            )
            source_terminated = (
                _entry_index(occurrences, source_carrier.lifecycle_track_id, source.terminated_at_entry_id, context)
                if source.terminated_at_entry_id is not None
                else None
            )
            source_boundary = _entry_index(occurrences, source_carrier.lifecycle_track_id, source_entry_id, context)
            if source_boundary < source_activated or (
                source_terminated is not None and source_boundary >= source_terminated
            ):
                raise ValueError(f"{context} copy source is not active at its boundary entry.")
        elif kind == "control-handoff":
            if source.carrier_id != target.carrier_id or source.role != "controlling" or target.role != "controlling":
                raise ValueError(f"{context} control handoff requires controlling occupancies on one carrier.")
            if same_subject or relationship_type is not None or source.terminated_at_entry_id != source_entry_id:
                raise ValueError(f"{context} control handoff requires distinct subjects and no identity assertion.")
        else:
            raise ValueError(f"Unsupported hosted identity transition kind `{kind}`.")
        shape = (kind, source_id, target_id, occurrence_id)
        if shape in semantic_transitions:
            raise ValueError(f"Hosted identity transition `{transition_id}` duplicates another transition.")
        semantic_transitions.add(shape)
        transitions[transition_id] = HostedIdentityTransition(
            transition_id,
            kind,
            source_id,
            target_id,
            occurrence_id,
            source_entry_id,
            target_entry_id,
            relationship_type,
            relationship_id,
        )

    return HostedIdentityRegistry(
        project.hosting_registry,
        SUPPORTED_SCHEMA_VERSION,
        True,
        carriers,
        occupancies,
        transitions,
        bindings,
        occurrences,
    )
