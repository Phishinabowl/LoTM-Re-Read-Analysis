from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .occurrence_config import OccurrenceRegistry
from .project_config import ProjectConfig
from .schema_pack_config import SchemaPackRegistry
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 1
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
class HostedIdentityRegistry:
    path: Path
    schema_version: int
    carriers: dict[str, HostCarrier]
    occupancies: dict[str, HostedIdentityOccupancy]
    transitions: dict[str, HostedIdentityTransition]
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

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {
            "host-carrier": self.carriers,
            "hosted-identity-occupancy": self.occupancies,
            "hosted-identity-transition": self.transitions,
        }

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.provenance_targets().get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported hosted-identity provenance subject type `{subject_type}`.")
        return self._known(targets, subject_id, subject_type)

    def reconciliation_targets(self) -> dict[str, dict[str, object]]:
        return {"host-carrier": self.carriers}

    def reconciliation_provider(self) -> dict[str, object]:
        return {"provider_id": "hosting", "targets": self.reconciliation_targets(), "aliases": {"host-carrier": {}}}

    def _entry_index(self, track_id: str, entry_id: str) -> int:
        track = self._known(self.occurrences.tracks, track_id, "occurrence track")
        entry = self._known(self.occurrences.track_entries, entry_id, "occurrence track entry")
        if entry.track_id != track_id:
            raise ValueError(f"Track entry `{entry_id}` does not belong to track `{track_id}`.")
        return track.entry_ids.index(entry_id)

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


def load_hosted_identity_registry(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    occurrences: OccurrenceRegistry,
    identity_providers: tuple[object, ...],
) -> HostedIdentityRegistry:
    if not packs.capability_enabled("hosted-identity-embodiment"):
        raise ValueError("Hosted identity registry requires enabled capability `hosted-identity-embodiment`.")

    data = load_yaml_file(
        project.hosting_registry,
        "hosted identity registry",
        expected_schema_version=SUPPORTED_SCHEMA_VERSION,
    )
    root = _mapping(data, "root")
    assert_allowed_keys(
        root, {"schema_version", "carriers", "occupancies", "transitions"}, "Hosted identity registry root"
    )

    identity_targets = _provider_maps(identity_providers, "identity_targets", "identity-target")
    provenance_targets = _provider_maps(identity_providers, "provenance_targets", "relationship-target")

    carriers: dict[str, HostCarrier] = {}
    for carrier_id, raw in _mapping(root.get("carriers"), "carriers").items():
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

    occupancies: dict[str, HostedIdentityOccupancy] = {}
    semantic_occupancies: set[tuple[str, str, str, str, int, int | None]] = set()
    for index, raw in enumerate(_list(root.get("occupancies"), "occupancies")):
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
    for index, raw in enumerate(_list(root.get("transitions"), "transitions")):
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
        carriers,
        occupancies,
        transitions,
        occurrences,
    )
