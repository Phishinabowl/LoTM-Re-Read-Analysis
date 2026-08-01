from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from project_config import ProjectConfig
from schema_pack_config import SchemaPackRegistry
from strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 1
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
class NarrativeChronologyContext:
    id: str
    label: str
    coordinate_system_id: str
    role: str
    continuity_ids: tuple[str, ...]
    work_ids: tuple[str, ...]
    branch_id: str | None


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
    narrative_contexts: tuple[NarrativeChronologyContext, ...]

    def compare_positions(self, left_id: str, right_id: str) -> str:
        if left_id not in self.positions:
            raise ValueError(f"Unknown chronology position `{left_id}`.")
        if right_id not in self.positions:
            raise ValueError(f"Unknown chronology position `{right_id}`.")
        if left_id == right_id:
            return "concurrent"
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
        {"schema_version", "coordinate_systems", "eras", "positions", "spans", "relations", "mappings", "narrative_contexts"},
        "Chronology registry root",
    )
    if root.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"Unsupported chronology schema_version {root.get('schema_version')!r}; expected {SUPPORTED_SCHEMA_VERSION}.")

    coordinate_systems: dict[str, CoordinateSystem] = {}
    raw_systems = _require_mapping(root.get("coordinate_systems"), "chronology.coordinate_systems")
    if not raw_systems:
        raise ValueError("chronology.coordinate_systems cannot be empty.")
    for system_id, raw in raw_systems.items():
        _stable_id(system_id, "chronology coordinate-system ID")
        context = f"coordinate_systems.{system_id}"
        item = _require_mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "value_domain", "direction", "zero_policy", "aliases", "origin_position_id"}, context)
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
            system_id, _require_string(item, "label", context), kind, value_domain,
            direction, zero_policy, _string_list(item, "aliases", context), origin,
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
        eras[era_id] = ChronologyEra(era_id, system_id, _require_string(item, "label", context), ordinal, _string_list(item, "aliases", context), direction)

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
        positions[position_id] = ChronologyPosition(position_id, system_id, value, era_id, _optional_string(item, "label", context), certainty)

    for system in coordinate_systems.values():
        if system.origin_position_id is not None:
            if system.origin_position_id not in positions:
                raise ValueError(f"coordinate_systems.{system.id}.origin_position_id references unknown position `{system.origin_position_id}`.")
            if positions[system.origin_position_id].coordinate_system_id == system.id:
                raise ValueError(f"coordinate_systems.{system.id}.origin_position_id must use another coordinate system.")
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
        assert_allowed_keys(item, {"id", "coordinate_system_id", "start_position_id", "end_position_id", "start_inclusive", "end_inclusive", "certainty"}, context)
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
            if position_id is not None and (position_id not in positions or positions[position_id].coordinate_system_id != system_id):
                raise ValueError(f"{context}.{key} must reference a position in `{system_id}`.")
        start_inclusive = item.get("start_inclusive")
        end_inclusive = item.get("end_inclusive")
        if type(start_inclusive) is not bool or type(end_inclusive) is not bool:
            raise ValueError(f"{context} inclusivity fields must be true or false.")
        certainty = _require_string(item, "certainty", context)
        _pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        if start_id is not None and end_id is not None:
            probe = ChronologyRegistry(path, SUPPORTED_SCHEMA_VERSION, coordinate_systems, eras, positions, (), (), (), ())
            ordering = probe.compare_positions(start_id, end_id)
            if ordering == "after" or (ordering == "concurrent" and not (start_inclusive and end_inclusive)):
                raise ValueError(f"{context} has an empty or reversed span.")
        spans.append(ChronologySpan(span_id, system_id, start_id, end_id, start_inclusive, end_inclusive, certainty))

    relations: list[ChronologyRelation] = []
    seen_record_ids: set[str] = set()
    for index, raw in enumerate(root.get("relations", [])):
        context = f"relations[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(item, {"id", "source_position_id", "relation_type", "target_position_id", "certainty"}, context)
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
        assert_allowed_keys(item, {"id", "source_position_id", "mapping_kind", "target_position_id", "certainty"}, context)
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

    contexts: list[NarrativeChronologyContext] = []
    raw_contexts = root.get("narrative_contexts", [])
    if not isinstance(raw_contexts, list):
        raise ValueError("chronology.narrative_contexts must be a list.")
    if raw_contexts:
        _require_capability(packs, "narrative-chronology")
    seen_context_ids: set[str] = set()
    for index, raw in enumerate(raw_contexts):
        context = f"narrative_contexts[{index}]"
        item = _require_mapping(raw, context)
        assert_allowed_keys(item, {"id", "label", "coordinate_system_id", "role", "continuity_ids", "work_ids", "branch_id"}, context)
        context_id = _stable_id(_require_string(item, "id", context), f"{context}.id")
        if context_id in seen_context_ids:
            raise ValueError(f"{context}.id duplicates `{context_id}`.")
        seen_context_ids.add(context_id)
        system_id = _require_string(item, "coordinate_system_id", context)
        if system_id not in coordinate_systems:
            raise ValueError(f"{context}.coordinate_system_id references unknown coordinate system `{system_id}`.")
        role = _require_string(item, "role", context)
        _pack_value(packs, "narrative.chronology-role", role, f"{context}.role")
        context_work_ids = _string_list(item, "work_ids", context)
        context_continuity_ids = _string_list(item, "continuity_ids", context)
        if not context_work_ids and not context_continuity_ids:
            raise ValueError(f"{context} must name at least one work or continuity.")
        if work_ids is None or continuity_ids is None:
            raise ValueError("Narrative chronology contexts require composed work and continuity targets.")
        unknown_works = set(context_work_ids) - work_ids
        unknown_continuities = set(context_continuity_ids) - continuity_ids
        if unknown_works:
            raise ValueError(f"{context}.work_ids references unknown works: {', '.join(sorted(unknown_works))}.")
        if unknown_continuities:
            raise ValueError(f"{context}.continuity_ids references unknown continuities: {', '.join(sorted(unknown_continuities))}.")
        branch_id = _optional_string(item, "branch_id", context)
        if branch_id is not None:
            _stable_id(branch_id, f"{context}.branch_id")
        contexts.append(NarrativeChronologyContext(context_id, _require_string(item, "label", context), system_id, role, context_continuity_ids, context_work_ids, branch_id))

    registry = ChronologyRegistry(path, SUPPORTED_SCHEMA_VERSION, coordinate_systems, eras, positions, tuple(spans), tuple(relations), tuple(mappings), tuple(contexts))
    coordinate_registry = ChronologyRegistry(path, SUPPORTED_SCHEMA_VERSION, coordinate_systems, eras, positions, tuple(spans), (), tuple(mappings), tuple(contexts))
    exact_pairs: set[tuple[str, str]] = set()
    order_edges: dict[str, set[str]] = {}
    for relation in relations:
        left = positions[relation.source_position_id]
        right = positions[relation.target_position_id]
        if relation.certainty != "exact":
            continue
        pair = tuple(sorted((left.id, right.id)))
        if pair in exact_pairs:
            raise ValueError(f"Chronology relation `{relation.id}` duplicates an exact relation between `{pair[0]}` and `{pair[1]}`.")
        exact_pairs.add(pair)
        computed = coordinate_registry.compare_positions(left.id, right.id)
        if computed != "incomparable" and relation.relation_type != computed:
            raise ValueError(f"Chronology relation `{relation.id}` contradicts ordered coordinates: declared {relation.relation_type}, computed {computed}.")
        if relation.relation_type == "before":
            order_edges.setdefault(left.id, set()).add(right.id)
        elif relation.relation_type == "after":
            order_edges.setdefault(right.id, set()).add(left.id)

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
        raise ValueError("Exact chronology relations contain a before/after cycle.")
    return registry


def load_chronology_registry(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    *,
    work_ids: set[str] | None = None,
    continuity_ids: set[str] | None = None,
) -> ChronologyRegistry:
    data = load_yaml_file(project.chronology_registry, "chronology registry", expected_schema_version=SUPPORTED_SCHEMA_VERSION)
    return parse_chronology_registry(data, project.chronology_registry, packs, work_ids=work_ids, continuity_ids=continuity_ids)
