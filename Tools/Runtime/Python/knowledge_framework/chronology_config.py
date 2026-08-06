from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from .project_config import ProjectConfig
from .schema_pack_config import SchemaPackRegistry
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 2
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class CoordinateSystem:
    id: str
    label: str
    kind: str
    value_domain: str
    direction: str
    zero_policy: str
    aliases: tuple[str, ...]
    origin_position_id: str | None


@dataclass(frozen=True)
class ChronologyEra:
    id: str
    coordinate_system_id: str
    label: str
    ordinal: int
    aliases: tuple[str, ...]
    direction: str


@dataclass(frozen=True)
class ChronologyPosition:
    id: str
    coordinate_system_id: str
    value: int
    era_id: str | None
    label: str | None
    certainty: str


@dataclass(frozen=True)
class ChronologySpan:
    id: str
    coordinate_system_id: str
    start_position_id: str | None
    end_position_id: str | None
    start_inclusive: bool
    end_inclusive: bool
    certainty: str


@dataclass(frozen=True)
class ChronologyRelation:
    id: str
    source_position_id: str
    relation_type: str
    target_position_id: str
    certainty: str


@dataclass(frozen=True)
class ChronologyMapping:
    id: str
    source_position_id: str
    mapping_kind: str
    target_position_id: str
    certainty: str


@dataclass(frozen=True)
class ChronologyContext:
    id: str
    label: str
    coordinate_system_id: str
    role: str
    continuity_ids: tuple[str, ...]
    work_ids: tuple[str, ...]
    branch_id: str | None


@dataclass(frozen=True)
class ChronologyContextRelationBinding:
    id: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class ChronologyContextRelation:
    id: str
    source_context_id: str
    relation_type: str
    target_context_id: str
    certainty: str
    bindings: tuple[ChronologyContextRelationBinding, ...]


@dataclass(frozen=True)
class ChronologyRegistry:
    path: Path
    schema_version: int
    coordinate_systems: dict[str, CoordinateSystem]
    eras: dict[str, ChronologyEra]
    positions: dict[str, ChronologyPosition]
    spans: tuple[ChronologySpan, ...]
    relations: tuple[ChronologyRelation, ...]
    mappings: tuple[ChronologyMapping, ...]
    contexts: tuple[ChronologyContext, ...]
    context_relations: tuple[ChronologyContextRelation, ...]
    equivalence_classes: dict[str, str] = field(default_factory=dict)
    order_edges: dict[str, frozenset[str]] = field(default_factory=dict)

    def context_relations_from(
        self, context_id: str, relation_type: str | None = None
    ) -> tuple[ChronologyContextRelation, ...]:
        self._require_context(context_id)
        return tuple(
            relation
            for relation in self.context_relations
            if relation.source_context_id == context_id
            and (relation_type is None or relation.relation_type == relation_type)
        )

    def context_relations_to(
        self, context_id: str, relation_type: str | None = None
    ) -> tuple[ChronologyContextRelation, ...]:
        self._require_context(context_id)
        return tuple(
            relation
            for relation in self.context_relations
            if relation.target_context_id == context_id
            and (relation_type is None or relation.relation_type == relation_type)
        )

    def validate_context_relation_targets(self, targets: dict[str, set[str]]) -> None:
        for relation in self.context_relations:
            for binding in relation.bindings:
                if binding.target_type not in targets or binding.target_id not in targets[binding.target_type]:
                    raise ValueError(
                        f"Chronology context relation binding `{binding.id}` references unknown target "
                        f"`{binding.target_type}:{binding.target_id}`."
                    )

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {
            "chronology-position": self.positions,
            "chronology-context": {item.id: item for item in self.contexts},
            "chronology-context-relation": {item.id: item for item in self.context_relations},
            "chronology-context-relation-binding": {
                binding.id: binding for relation in self.context_relations for binding in relation.bindings
            },
        }

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.provenance_targets()
        if subject_type not in targets:
            raise ValueError(f"Unsupported chronology provenance subject type `{subject_type}`.")
        if subject_id not in targets[subject_type]:
            raise ValueError(f"Unknown {subject_type} `{subject_id}`.")
        return targets[subject_type][subject_id]

    def _require_context(self, context_id: str) -> None:
        if context_id not in {item.id for item in self.contexts}:
            raise ValueError(f"Unknown chronology context `{context_id}`.")

    def compare_positions(self, left_id: str, right_id: str) -> str:
        if left_id not in self.positions:
            raise ValueError(f"Unknown chronology position `{left_id}`.")
        if right_id not in self.positions:
            raise ValueError(f"Unknown chronology position `{right_id}`.")
        if left_id == right_id:
            return "concurrent"
        if self.equivalence_classes:
            left_class = self.equivalence_classes[left_id]
            right_class = self.equivalence_classes[right_id]
            if left_class == right_class:
                return "concurrent"
            if self._class_reaches(left_class, right_class):
                return "before"
            if self._class_reaches(right_class, left_class):
                return "after"
            return "incomparable"
        left = self.positions[left_id]
        right = self.positions[right_id]
        if left.coordinate_system_id == right.coordinate_system_id:
            system = self.coordinate_systems[left.coordinate_system_id]
            if left.era_id is not None and right.era_id is not None:
                left_era = self.eras[left.era_id]
                right_era = self.eras[right.era_id]
                if left_era.ordinal != right_era.ordinal:
                    return "before" if left_era.ordinal < right_era.ordinal else "after"
                direction = left_era.direction
            else:
                direction = system.direction
            if left.value == right.value:
                return "concurrent"
            before = left.value < right.value
            if direction == "descending":
                before = not before
            return "before" if before else "after"
        if self._is_relative_origin_pair(left, right):
            return "concurrent"
        for mapping in self.mappings:
            endpoints = {mapping.source_position_id, mapping.target_position_id}
            if (
                endpoints == {left_id, right_id}
                and mapping.mapping_kind == "equivalent"
                and mapping.certainty == "exact"
            ):
                return "concurrent"
        for relation in self.relations:
            if relation.certainty != "exact":
                continue
            if relation.source_position_id == left_id and relation.target_position_id == right_id:
                return relation.relation_type
            if relation.source_position_id == right_id and relation.target_position_id == left_id:
                return _inverse_relation(relation.relation_type)
        return "incomparable"

    def _class_reaches(self, source_class: str, target_class: str) -> bool:
        pending = list(self.order_edges.get(source_class, ()))
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current == target_class:
                return True
            if current in seen:
                continue
            seen.add(current)
            pending.extend(self.order_edges.get(current, ()))
        return False

    def _is_relative_origin_pair(self, left: ChronologyPosition, right: ChronologyPosition) -> bool:
        for relative, candidate_origin in ((left, right), (right, left)):
            system = self.coordinate_systems[relative.coordinate_system_id]
            if (
                system.kind == "relative"
                and relative.value == 0
                and system.origin_position_id == candidate_origin.id
                and relative.certainty == "exact"
                and candidate_origin.certainty == "exact"
            ):
                return True
        return False


def _require_mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a mapping.")
    return value


def _require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string.")
    return value.strip()


def _optional_string(mapping: dict, key: str, context: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string or null.")
    return value.strip()


def _string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{context}.{key} must be a list.")
    result = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(result) != len(value) or len(set(result)) != len(result):
        raise ValueError(f"{context}.{key} must contain unique non-empty strings.")
    return result


def _stable_id(value: str, context: str) -> str:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{context} must be a lowercase kebab-case stable ID: {value}")
    return value


def _pack_value(packs: SchemaPackRegistry, namespace: str, value: str, context: str) -> None:
    allowed = packs.allowed_values(namespace)
    if not allowed or value not in allowed:
        raise ValueError(f"{context} uses `{value}`, which is not provided in `{namespace}`.")


def _require_capability(packs: SchemaPackRegistry, capability: str) -> None:
    if not packs.capability_enabled(capability):
        raise ValueError(f"Chronology registry requires enabled capability `{capability}`.")


def _inverse_relation(value: str) -> str:
    return {"before": "after", "after": "before"}.get(value, value)


def _intrinsic_comparison(
    left: ChronologyPosition,
    right: ChronologyPosition,
    coordinate_systems: dict[str, CoordinateSystem],
    eras: dict[str, ChronologyEra],
) -> str:
    if left.coordinate_system_id != right.coordinate_system_id:
        return "incomparable"
    system = coordinate_systems[left.coordinate_system_id]
    if left.era_id is not None and right.era_id is not None:
        left_era = eras[left.era_id]
        right_era = eras[right.era_id]
        if left_era.ordinal != right_era.ordinal:
            return "before" if left_era.ordinal < right_era.ordinal else "after"
        direction = left_era.direction
    else:
        direction = system.direction
    if left.value == right.value:
        return "concurrent"
    before = left.value < right.value
    if direction == "descending":
        before = not before
    return "before" if before else "after"


def parse_chronology_registry(
    data: object,
    path: Path,
    packs: SchemaPackRegistry,
    *,
    work_ids: set[str] | None = None,
    continuity_ids: set[str] | None = None,
) -> ChronologyRegistry:
    _require_capability(packs, "chronology-coordinate-systems")
    root = _require_mapping(data, "Chronology registry root")
    assert_allowed_keys(
        root,
        {
            "schema_version",
            "coordinate_systems",
            "eras",
            "positions",
            "spans",
            "relations",
            "mappings",
            "contexts",
            "context_relations",
        },
        "Chronology registry root",
    )
    if root.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported chronology schema_version {root.get('schema_version')!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION}."
        )

    coordinate_systems: dict[str, CoordinateSystem] = {}
    raw_systems = _require_mapping(root.get("coordinate_systems"), "chronology.coordinate_systems")
    if not raw_systems:
        raise ValueError("chronology.coordinate_systems cannot be empty.")
    for system_id, raw in raw_systems.items():
        _stable_id(system_id, "chronology coordinate-system ID")
        context = f"coordinate_systems.{system_id}"
        item = _require_mapping(raw, context)
        assert_allowed_keys(
            item,
            {"label", "kind", "value_domain", "direction", "zero_policy", "aliases", "origin_position_id"},
            context,
        )
        kind = _require_string(item, "kind", context)
        value_domain = _require_string(item, "value_domain", context)
        direction = _require_string(item, "direction", context)
        zero_policy = _require_string(item, "zero_policy", context)
        _pack_value(packs, "chronology.coordinate-kind", kind, f"{context}.kind")
        _pack_value(packs, "chronology.value-domain", value_domain, f"{context}.value_domain")
        _pack_value(packs, "chronology.direction", direction, f"{context}.direction")
        _pack_value(packs, "chronology.zero-policy", zero_policy, f"{context}.zero_policy")
        origin = _optional_string(item, "origin_position_id", context)
        if origin is not None:
            _stable_id(origin, f"{context}.origin_position_id")
        if kind == "relative" and origin is None:
            raise ValueError(f"{context}.origin_position_id is required for relative coordinates.")
        if kind != "relative" and origin is not None:
            raise ValueError(f"{context}.origin_position_id is only valid for relative coordinates.")
        if zero_policy == "absent" and value_domain != "positive-integer":
            raise ValueError(f"{context} with absent zero must use positive-integer values.")
        coordinate_systems[system_id] = CoordinateSystem(
            system_id,
            _require_string(item, "label", context),
            kind,
            value_domain,
            direction,
            zero_policy,
            _string_list(item, "aliases", context),
            origin,
        )

    eras: dict[str, ChronologyEra] = {}
    era_ordinals: set[tuple[str, int]] = set()
    for era_id, raw in _require_mapping(root.get("eras"), "chronology.eras").items():
        _stable_id(era_id, "chronology era ID")
        context = f"eras.{era_id}"
        item = _require_mapping(raw, context)
        assert_allowed_keys(item, {"coordinate_system_id", "label", "ordinal", "aliases", "direction"}, context)
        system_id = _require_string(item, "coordinate_system_id", context)
        if system_id not in coordinate_systems:
            raise ValueError(f"{context}.coordinate_system_id references unknown coordinate system `{system_id}`.")
        if coordinate_systems[system_id].kind != "era-ordinal":
            raise ValueError(f"{context} can only belong to an era-ordinal coordinate system.")
        ordinal = item.get("ordinal")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
            raise ValueError(f"{context}.ordinal must be a positive integer.")
        if (system_id, ordinal) in era_ordinals:
            raise ValueError(f"{context}.ordinal duplicates ordinal {ordinal} in `{system_id}`.")
        era_ordinals.add((system_id, ordinal))
        direction = _optional_string(item, "direction", context) or coordinate_systems[system_id].direction
        _pack_value(packs, "chronology.direction", direction, f"{context}.direction")
        eras[era_id] = ChronologyEra(
            era_id,
            system_id,
            _require_string(item, "label", context),
            ordinal,
            _string_list(item, "aliases", context),
            direction,
        )

    positions: dict[str, ChronologyPosition] = {}
    occupied_coordinates: set[tuple[str, str | None, int]] = set()
    for position_id, raw in _require_mapping(root.get("positions"), "chronology.positions").items():
        _stable_id(position_id, "chronology position ID")
        context = f"positions.{position_id}"
        item = _require_mapping(raw, context)
        assert_allowed_keys(item, {"coordinate_system_id", "value", "era_id", "label", "certainty"}, context)
        system_id = _require_string(item, "coordinate_system_id", context)
        if system_id not in coordinate_systems:
            raise ValueError(f"{context}.coordinate_system_id references unknown coordinate system `{system_id}`.")
        system = coordinate_systems[system_id]
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{context}.value must be an integer.")
        if system.value_domain == "nonnegative-integer" and value < 0:
            raise ValueError(f"{context}.value must be nonnegative.")
        if system.value_domain == "positive-integer" and value < 1:
            raise ValueError(f"{context}.value must be positive.")
        if system.zero_policy == "absent" and value == 0:
            raise ValueError(f"{context}.value cannot use zero in `{system_id}`.")
        era_id = _optional_string(item, "era_id", context)
        if system.kind == "era-ordinal":
            if era_id is None or era_id not in eras or eras[era_id].coordinate_system_id != system_id:
                raise ValueError(f"{context}.era_id must reference an era in `{system_id}`.")
        elif era_id is not None:
            raise ValueError(f"{context}.era_id is only valid for era-ordinal coordinates.")
        coordinate = (system_id, era_id, value)
        if coordinate in occupied_coordinates:
            raise ValueError(f"{context} duplicates an existing coordinate.")
        occupied_coordinates.add(coordinate)
        certainty = _require_string(item, "certainty", context)
        _pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        positions[position_id] = ChronologyPosition(
            position_id, system_id, value, era_id, _optional_string(item, "label", context), certainty
        )

    for system in coordinate_systems.values():
        if system.origin_position_id is not None:
            if system.origin_position_id not in positions:
                raise ValueError(
                    f"coordinate_systems.{system.id}.origin_position_id references unknown position "
                    f"`{system.origin_position_id}`."
                )
            if positions[system.origin_position_id].coordinate_system_id == system.id:
                raise ValueError(
                    f"coordinate_systems.{system.id}.origin_position_id must use another coordinate system."
                )
    origin_edges = {
        system.id: positions[system.origin_position_id].coordinate_system_id
        for system in coordinate_systems.values()
        if system.origin_position_id is not None
    }
    for system_id in origin_edges:
        seen: set[str] = set()
        current = system_id
        while current in origin_edges:
            if current in seen:
                raise ValueError(f"Chronology relative-origin cycle includes coordinate system `{current}`.")
            seen.add(current)
            current = origin_edges[current]

    spans: list[ChronologySpan] = []
    raw_spans = root.get("spans", [])
    if not isinstance(raw_spans, list):
        raise ValueError("chronology.spans must be a list.")
    seen_span_ids: set[str] = set()
    for index, raw in enumerate(raw_spans):
        context = f"spans[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id",
                "coordinate_system_id",
                "start_position_id",
                "end_position_id",
                "start_inclusive",
                "end_inclusive",
                "certainty",
            },
            context,
        )
        span_id = _stable_id(_require_string(item, "id", context), f"{context}.id")
        if span_id in seen_span_ids:
            raise ValueError(f"{context}.id duplicates `{span_id}`.")
        seen_span_ids.add(span_id)
        system_id = _require_string(item, "coordinate_system_id", context)
        if system_id not in coordinate_systems:
            raise ValueError(f"{context}.coordinate_system_id references unknown coordinate system `{system_id}`.")
        start_id = _optional_string(item, "start_position_id", context)
        end_id = _optional_string(item, "end_position_id", context)
        if start_id is None and end_id is None:
            raise ValueError(f"{context} requires at least one endpoint.")
        for key, position_id in (("start_position_id", start_id), ("end_position_id", end_id)):
            if position_id is not None and (
                position_id not in positions or positions[position_id].coordinate_system_id != system_id
            ):
                raise ValueError(f"{context}.{key} must reference a position in `{system_id}`.")
        start_inclusive = item.get("start_inclusive")
        end_inclusive = item.get("end_inclusive")
        if type(start_inclusive) is not bool or type(end_inclusive) is not bool:
            raise ValueError(f"{context} inclusivity fields must be true or false.")
        certainty = _require_string(item, "certainty", context)
        _pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        if start_id is not None and end_id is not None:
            probe = ChronologyRegistry(
                path, SUPPORTED_SCHEMA_VERSION, coordinate_systems, eras, positions, (), (), (), (), ()
            )
            ordering = probe.compare_positions(start_id, end_id)
            if ordering == "after" or (ordering == "concurrent" and not (start_inclusive and end_inclusive)):
                raise ValueError(f"{context} has an empty or reversed span.")
        spans.append(ChronologySpan(span_id, system_id, start_id, end_id, start_inclusive, end_inclusive, certainty))

    relations: list[ChronologyRelation] = []
    seen_record_ids: set[str] = set()
    for index, raw in enumerate(root.get("relations", [])):
        context = f"relations[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(
            item, {"id", "source_position_id", "relation_type", "target_position_id", "certainty"}, context
        )
        relation_id = _stable_id(_require_string(item, "id", context), f"{context}.id")
        if relation_id in seen_record_ids:
            raise ValueError(f"{context}.id duplicates `{relation_id}`.")
        seen_record_ids.add(relation_id)
        source_id = _require_string(item, "source_position_id", context)
        target_id = _require_string(item, "target_position_id", context)
        if source_id not in positions or target_id not in positions or source_id == target_id:
            raise ValueError(f"{context} must reference two distinct known positions.")
        relation_type = _require_string(item, "relation_type", context)
        certainty = _require_string(item, "certainty", context)
        _pack_value(packs, "chronology.relation-type", relation_type, f"{context}.relation_type")
        _pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        relations.append(ChronologyRelation(relation_id, source_id, relation_type, target_id, certainty))

    mappings: list[ChronologyMapping] = []
    for index, raw in enumerate(root.get("mappings", [])):
        context = f"mappings[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(
            item, {"id", "source_position_id", "mapping_kind", "target_position_id", "certainty"}, context
        )
        mapping_id = _stable_id(_require_string(item, "id", context), f"{context}.id")
        if mapping_id in seen_record_ids:
            raise ValueError(f"{context}.id duplicates `{mapping_id}`.")
        seen_record_ids.add(mapping_id)
        source_id = _require_string(item, "source_position_id", context)
        target_id = _require_string(item, "target_position_id", context)
        if source_id not in positions or target_id not in positions or source_id == target_id:
            raise ValueError(f"{context} must reference two distinct known positions.")
        if positions[source_id].coordinate_system_id == positions[target_id].coordinate_system_id:
            raise ValueError(f"{context} must map positions in different coordinate systems.")
        mapping_kind = _require_string(item, "mapping_kind", context)
        certainty = _require_string(item, "certainty", context)
        _pack_value(packs, "chronology.mapping-kind", mapping_kind, f"{context}.mapping_kind")
        _pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        mappings.append(ChronologyMapping(mapping_id, source_id, mapping_kind, target_id, certainty))

    contexts: list[ChronologyContext] = []
    raw_contexts = root.get("contexts", [])
    if not isinstance(raw_contexts, list):
        raise ValueError("chronology.contexts must be a list.")
    if raw_contexts:
        _require_capability(packs, "chronology-contexts")
    seen_context_ids: set[str] = set()
    for index, raw in enumerate(raw_contexts):
        context = f"contexts[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(
            item, {"id", "label", "coordinate_system_id", "role", "continuity_ids", "work_ids", "branch_id"}, context
        )
        context_id = _stable_id(_require_string(item, "id", context), f"{context}.id")
        if context_id in seen_context_ids:
            raise ValueError(f"{context}.id duplicates `{context_id}`.")
        seen_context_ids.add(context_id)
        system_id = _require_string(item, "coordinate_system_id", context)
        if system_id not in coordinate_systems:
            raise ValueError(f"{context}.coordinate_system_id references unknown coordinate system `{system_id}`.")
        role = _require_string(item, "role", context)
        _pack_value(packs, "chronology.context-role", role, f"{context}.role")
        context_work_ids = _string_list(item, "work_ids", context)
        context_continuity_ids = _string_list(item, "continuity_ids", context)
        if (context_work_ids or context_continuity_ids) and (work_ids is None or continuity_ids is None):
            raise ValueError("Chronology contexts with project targets require composed work and continuity targets.")
        unknown_works = set(context_work_ids) - work_ids if work_ids is not None else set()
        unknown_continuities = set(context_continuity_ids) - continuity_ids if continuity_ids is not None else set()
        if unknown_works:
            raise ValueError(f"{context}.work_ids references unknown works: {', '.join(sorted(unknown_works))}.")
        if unknown_continuities:
            raise ValueError(
                f"{context}.continuity_ids references unknown continuities: {', '.join(sorted(unknown_continuities))}."
            )
        branch_id = _optional_string(item, "branch_id", context)
        if branch_id is not None:
            _stable_id(branch_id, f"{context}.branch_id")
        contexts.append(
            ChronologyContext(
                context_id,
                _require_string(item, "label", context),
                system_id,
                role,
                context_continuity_ids,
                context_work_ids,
                branch_id,
            )
        )

    context_relations: list[ChronologyContextRelation] = []
    raw_context_relations = root.get("context_relations", [])
    if not isinstance(raw_context_relations, list):
        raise ValueError("chronology.context_relations must be a list.")
    if raw_context_relations:
        _require_capability(packs, "chronology-context-topology")
    seen_context_relation_ids: set[str] = set()
    seen_context_relation_semantics: set[tuple[str, str, str]] = set()
    seen_context_binding_ids: set[str] = set()
    for index, raw in enumerate(raw_context_relations):
        context = f"context_relations[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(
            item,
            {"id", "source_context_id", "relation_type", "target_context_id", "certainty", "bindings"},
            context,
        )
        relation_id = _stable_id(_require_string(item, "id", context), f"{context}.id")
        if relation_id in seen_context_relation_ids:
            raise ValueError(f"{context}.id duplicates `{relation_id}`.")
        seen_context_relation_ids.add(relation_id)
        source_context_id = _require_string(item, "source_context_id", context)
        target_context_id = _require_string(item, "target_context_id", context)
        if source_context_id not in seen_context_ids or target_context_id not in seen_context_ids:
            raise ValueError(f"{context} must reference two known chronology contexts.")
        if source_context_id == target_context_id:
            raise ValueError(f"{context} cannot relate a chronology context to itself.")
        relation_type = _require_string(item, "relation_type", context)
        _pack_value(packs, "chronology.context-relation-type", relation_type, f"{context}.relation_type")
        semantic_key = (source_context_id, relation_type, target_context_id)
        if semantic_key in seen_context_relation_semantics:
            raise ValueError(f"{context} duplicates an existing context relation.")
        seen_context_relation_semantics.add(semantic_key)
        certainty = _require_string(item, "certainty", context)
        _pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        raw_bindings = item.get("bindings", [])
        if not isinstance(raw_bindings, list):
            raise ValueError(f"{context}.bindings must be a list.")
        bindings: list[ChronologyContextRelationBinding] = []
        seen_binding_semantics: set[tuple[str, str]] = set()
        for binding_index, raw_binding in enumerate(raw_bindings):
            binding_context = f"{context}.bindings[{binding_index}]"
            binding = _require_mapping(raw_binding, binding_context)
            assert_allowed_keys(binding, {"id", "target_type", "target_id"}, binding_context)
            binding_id = _stable_id(_require_string(binding, "id", binding_context), f"{binding_context}.id")
            if binding_id in seen_context_binding_ids:
                raise ValueError(f"{binding_context}.id duplicates `{binding_id}`.")
            seen_context_binding_ids.add(binding_id)
            target_type = _require_string(binding, "target_type", binding_context)
            target_id = _stable_id(
                _require_string(binding, "target_id", binding_context), f"{binding_context}.target_id"
            )
            _pack_value(packs, "chronology.context-binding-target-type", target_type, f"{binding_context}.target_type")
            binding_semantic = (target_type, target_id)
            if binding_semantic in seen_binding_semantics:
                raise ValueError(f"{binding_context} duplicates target `{target_type}:{target_id}`.")
            seen_binding_semantics.add(binding_semantic)
            bindings.append(ChronologyContextRelationBinding(binding_id, target_type, target_id))
        context_relations.append(
            ChronologyContextRelation(
                relation_id,
                source_context_id,
                relation_type,
                target_context_id,
                certainty,
                tuple(bindings),
            )
        )

    parent = {position_id: position_id for position_id in positions}

    def find(position_id: str) -> str:
        current = position_id
        while parent[current] != current:
            current = parent[current]
        root_id = current
        current = position_id
        while parent[current] != current:
            next_id = parent[current]
            parent[current] = root_id
            current = next_id
        return root_id

    def union(left_id: str, right_id: str) -> None:
        left_root = find(left_id)
        right_root = find(right_id)
        if left_root == right_root:
            return
        canonical, other = sorted((left_root, right_root))
        parent[other] = canonical

    for system in coordinate_systems.values():
        if system.kind != "relative" or system.origin_position_id is None:
            continue
        origin = positions[system.origin_position_id]
        for position in positions.values():
            if (
                position.coordinate_system_id == system.id
                and position.value == 0
                and position.certainty == "exact"
                and origin.certainty == "exact"
            ):
                union(position.id, origin.id)
    for mapping in mappings:
        if mapping.mapping_kind == "equivalent" and mapping.certainty == "exact":
            union(mapping.source_position_id, mapping.target_position_id)
    for relation in relations:
        if relation.relation_type == "concurrent" and relation.certainty == "exact":
            union(relation.source_position_id, relation.target_position_id)

    equivalence_classes = {position_id: find(position_id) for position_id in positions}
    exact_pairs: set[tuple[str, str]] = set()
    order_edges: dict[str, set[str]] = {}
    exact_incomparables: list[tuple[str, str, str]] = []

    def add_order_edge(source_id: str, target_id: str, context: str) -> None:
        source_class = equivalence_classes[source_id]
        target_class = equivalence_classes[target_id]
        if source_class == target_class:
            raise ValueError(f"{context} contradicts exact equivalence between `{source_id}` and `{target_id}`.")
        order_edges.setdefault(source_class, set()).add(target_class)

    positions_by_system: dict[str, list[ChronologyPosition]] = {}
    for position in positions.values():
        positions_by_system.setdefault(position.coordinate_system_id, []).append(position)
    for system_positions in positions_by_system.values():
        for index, left in enumerate(system_positions):
            for right in system_positions[index + 1 :]:
                comparison = _intrinsic_comparison(left, right, coordinate_systems, eras)
                if comparison == "before":
                    add_order_edge(left.id, right.id, "Intrinsic chronology")
                elif comparison == "after":
                    add_order_edge(right.id, left.id, "Intrinsic chronology")

    for relation in relations:
        left = positions[relation.source_position_id]
        right = positions[relation.target_position_id]
        if relation.certainty != "exact":
            continue
        pair = tuple(sorted((left.id, right.id)))
        if pair in exact_pairs:
            raise ValueError(
                f"Chronology relation `{relation.id}` duplicates an exact relation between `{pair[0]}` and `{pair[1]}`."
            )
        exact_pairs.add(pair)
        if relation.relation_type == "before":
            add_order_edge(left.id, right.id, f"Chronology relation `{relation.id}`")
        elif relation.relation_type == "after":
            add_order_edge(right.id, left.id, f"Chronology relation `{relation.id}`")
        elif relation.relation_type == "incomparable":
            exact_incomparables.append((left.id, right.id, relation.id))

    order_nodes = set(order_edges)
    for targets in order_edges.values():
        order_nodes.update(targets)
    indegree = {position_id: 0 for position_id in order_nodes}
    for targets in order_edges.values():
        for target_id in targets:
            indegree[target_id] += 1
    ready = sorted(position_id for position_id, degree in indegree.items() if degree == 0)
    processed = 0
    while ready:
        position_id = ready.pop()
        processed += 1
        for target_id in order_edges.get(position_id, ()):
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                ready.append(target_id)
    if processed != len(order_nodes):
        raise ValueError("Combined exact chronology contains a before/after cycle.")

    frozen_edges = {source_id: frozenset(target_ids) for source_id, target_ids in order_edges.items()}
    registry = ChronologyRegistry(
        path,
        SUPPORTED_SCHEMA_VERSION,
        coordinate_systems,
        eras,
        positions,
        tuple(spans),
        tuple(relations),
        tuple(mappings),
        tuple(contexts),
        tuple(context_relations),
        equivalence_classes,
        frozen_edges,
    )
    for left_id, right_id, relation_id in exact_incomparables:
        if registry.compare_positions(left_id, right_id) != "incomparable":
            raise ValueError(f"Chronology relation `{relation_id}` contradicts derived exact order.")
    return registry


def load_chronology_registry(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    *,
    work_ids: set[str] | None = None,
    continuity_ids: set[str] | None = None,
) -> ChronologyRegistry:
    data = load_yaml_file(
        project.chronology_registry, "chronology registry", expected_schema_version=SUPPORTED_SCHEMA_VERSION
    )
    return parse_chronology_registry(
        data, project.chronology_registry, packs, work_ids=work_ids, continuity_ids=continuity_ids
    )
