from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .project_config import ProjectConfig
from .schema_pack_config import SchemaPackRegistry
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 1
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class InterpretationRelationType:
    id: str
    label: str
    inverse_type: str
    symmetric: bool
    canonical_direction: bool
    acyclic_group: str | None


@dataclass(frozen=True)
class StructuralInterpretation:
    id: str
    lifecycle: str
    label: str
    description: str | None


@dataclass(frozen=True)
class InterpretationMember:
    id: str
    interpretation_id: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class InterpretationRelation:
    id: str
    interpretation_id: str
    source_member_id: str
    relationship_type: str
    target_member_id: str


@dataclass(frozen=True)
class InterpretationComparisonSet:
    id: str
    label: str
    comparison_mode: str
    interpretation_ids: tuple[str, ...]


@dataclass(frozen=True)
class InterpretationSetDecision:
    set_id: str
    comparison_mode: str
    disposition: str
    candidate_interpretation_ids: tuple[str, ...]
    selected_interpretation_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class InterpretationStructure:
    interpretation: StructuralInterpretation
    members: tuple[InterpretationMember, ...]
    relations: tuple[InterpretationRelation, ...]


@dataclass(frozen=True)
class StructuralInterpretationRegistry:
    path: Path
    schema_version: int
    relation_types: dict[str, InterpretationRelationType]
    interpretations: dict[str, StructuralInterpretation]
    members: tuple[InterpretationMember, ...]
    relations: tuple[InterpretationRelation, ...]
    comparison_sets: dict[str, InterpretationComparisonSet]

    def members_for_interpretation(self, interpretation_id: str) -> tuple[InterpretationMember, ...]:
        self._known_interpretation(interpretation_id)
        return tuple(item for item in self.members if item.interpretation_id == interpretation_id)

    def relations_for_interpretation(self, interpretation_id: str) -> tuple[InterpretationRelation, ...]:
        self._known_interpretation(interpretation_id)
        return tuple(item for item in self.relations if item.interpretation_id == interpretation_id)

    def comparison_sets_for_interpretation(self, interpretation_id: str) -> tuple[InterpretationComparisonSet, ...]:
        self._known_interpretation(interpretation_id)
        return tuple(
            sorted(
                (item for item in self.comparison_sets.values() if interpretation_id in item.interpretation_ids),
                key=lambda item: item.id,
            )
        )

    def structure_for_interpretation(self, interpretation_id: str) -> InterpretationStructure:
        interpretation = self._known_interpretation(interpretation_id)
        return InterpretationStructure(
            interpretation,
            self.members_for_interpretation(interpretation_id),
            self.relations_for_interpretation(interpretation_id),
        )

    def comparison_set_decision(self, set_id: str) -> InterpretationSetDecision:
        comparison_set = self.comparison_sets.get(set_id)
        if comparison_set is None:
            raise ValueError(f"Unknown structural interpretation set `{set_id}`.")
        if comparison_set.comparison_mode == "compatible":
            return InterpretationSetDecision(
                set_id,
                comparison_set.comparison_mode,
                "compatible",
                comparison_set.interpretation_ids,
                (),
                "Compatible interpretations may coexist; structural membership does not select or endorse them.",
            )
        return InterpretationSetDecision(
            set_id,
            comparison_set.comparison_mode,
            "unresolved",
            comparison_set.interpretation_ids,
            (),
            "Evidence and authority resolution remain provenance-owned.",
        )

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {
            "structural-interpretation": self.interpretations,
            "structural-interpretation-member": {item.id: item for item in self.members},
            "structural-interpretation-relation": {item.id: item for item in self.relations},
            "structural-interpretation-set": self.comparison_sets,
        }

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.provenance_targets()
        if subject_type not in targets:
            raise ValueError(f"Unsupported structural interpretation provenance subject type `{subject_type}`.")
        if subject_id not in targets[subject_type]:
            raise ValueError(f"Unknown {subject_type} `{subject_id}`.")
        return targets[subject_type][subject_id]

    def validate_claim_targets(self, claim_keys: set[str]) -> None:
        for member in self.members:
            if member.target_type == "provenance-claim" and member.target_id not in claim_keys:
                raise ValueError(
                    f"Structural interpretation member `{member.id}` references unknown provenance claim "
                    f"`{member.target_id}`."
                )

    def _known_interpretation(self, interpretation_id: str) -> StructuralInterpretation:
        interpretation = self.interpretations.get(interpretation_id)
        if interpretation is None:
            raise ValueError(f"Unknown structural interpretation `{interpretation_id}`.")
        return interpretation


def _mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Structural interpretation registry `{context}` must be a mapping.")
    return value


def _list(value: object, context: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"Structural interpretation registry `{context}` must be a list.")
    return value


def _stable(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Structural interpretation registry `{context}` must be a lowercase kebab-case stable ID: {value}"
        )


def _string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Structural interpretation registry `{context}.{key}` must be a non-empty string.")
    return value.strip()


def _optional_string(mapping: dict, key: str, context: str) -> str | None:
    if key not in mapping or mapping[key] is None:
        return None
    return _string(mapping, key, context)


def _boolean(mapping: dict, key: str, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Structural interpretation registry `{context}.{key}` must be a boolean.")
    return value


def _string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    values = _list(mapping.get(key), f"{context}.{key}")
    result: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Structural interpretation registry `{context}.{key}[{index}]` must be a non-empty string."
            )
        result.append(value.strip())
    return tuple(result)


def _pack_value(packs: SchemaPackRegistry, namespace: str, value: str, context: str) -> None:
    if value not in packs.allowed_values(namespace):
        raise ValueError(
            f"Structural interpretation registry `{context}` value `{value}` is not allowed by `{namespace}`."
        )


def _canonical_relation_shape(
    relation: InterpretationRelation,
    relation_types: dict[str, InterpretationRelationType],
) -> tuple[str, str, str, str]:
    relationship_type = relation_types[relation.relationship_type]
    source_id = relation.source_member_id
    target_id = relation.target_member_id
    type_id = relation.relationship_type
    if relationship_type.symmetric:
        source_id, target_id = sorted((source_id, target_id))
    elif not relationship_type.canonical_direction:
        source_id, target_id = target_id, source_id
        type_id = relationship_type.inverse_type
    return relation.interpretation_id, source_id, type_id, target_id


def _validate_relation_types(relation_types: dict[str, InterpretationRelationType]) -> None:
    for type_id, relationship_type in relation_types.items():
        inverse = relation_types.get(relationship_type.inverse_type)
        if inverse is None:
            raise ValueError(
                f"Structural interpretation relation type `{type_id}` references unknown inverse "
                f"`{relationship_type.inverse_type}`."
            )
        if inverse.inverse_type != type_id:
            raise ValueError(f"Structural interpretation relation type `{type_id}` has a nonreciprocal inverse.")
        if relationship_type.symmetric:
            if relationship_type.inverse_type != type_id:
                raise ValueError(f"Symmetric structural interpretation relation type `{type_id}` must be self-inverse.")
            if relationship_type.canonical_direction:
                raise ValueError(
                    f"Symmetric structural interpretation relation type `{type_id}` cannot declare canonical direction."
                )
            if relationship_type.acyclic_group is not None:
                raise ValueError(
                    f"Symmetric structural interpretation relation type `{type_id}` cannot enter an acyclic group."
                )
        else:
            if inverse.symmetric:
                raise ValueError(f"Structural interpretation relation type `{type_id}` has a symmetric inverse.")
            if relationship_type.canonical_direction == inverse.canonical_direction:
                raise ValueError(
                    f"Structural interpretation inverse pair `{type_id}` and `{inverse.id}` must define exactly one "
                    "canonical direction."
                )
            if relationship_type.acyclic_group != inverse.acyclic_group:
                raise ValueError(
                    f"Structural interpretation inverse pair `{type_id}` and `{inverse.id}` must share one "
                    "acyclic group."
                )


def _validate_acyclic_relations(
    relations: tuple[InterpretationRelation, ...],
    relation_types: dict[str, InterpretationRelationType],
) -> None:
    graph: dict[tuple[str, str, str], set[str]] = {}
    for relation in relations:
        relationship_type = relation_types[relation.relationship_type]
        group = relationship_type.acyclic_group
        if group is None:
            continue
        _, source_id, _, target_id = _canonical_relation_shape(relation, relation_types)
        graph.setdefault((relation.interpretation_id, group, source_id), set()).add(target_id)

    visiting: set[tuple[str, str, str]] = set()
    visited: set[tuple[str, str, str]] = set()

    def visit(key: tuple[str, str, str]) -> None:
        if key in visiting:
            raise ValueError(
                "Structural interpretation registry contains an interpretation-local relationship cycle "
                f"in `{key[0]}` group `{key[1]}` involving `{key[2]}`."
            )
        if key in visited:
            return
        visiting.add(key)
        interpretation_id, group, _ = key
        for target_id in graph.get(key, ()):
            visit((interpretation_id, group, target_id))
        visiting.remove(key)
        visited.add(key)

    for node in tuple(graph):
        visit(node)


def _provider_targets(providers: tuple[object, ...]) -> dict[str, object]:
    targets: dict[str, object] = {}
    for provider in providers:
        method = getattr(provider, "provenance_targets", None)
        if method is None:
            raise ValueError("Structural interpretation target provider does not expose provenance_targets().")
        for target_type in method():
            if target_type in targets:
                raise ValueError(f"Structural interpretation target type `{target_type}` has multiple providers.")
            targets[target_type] = provider
    return targets


def load_interpretation_registry(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    target_providers: tuple[object, ...],
) -> StructuralInterpretationRegistry:
    if not packs.capability_enabled("structural-interpretation-modeling"):
        raise ValueError(
            "Structural interpretation registry requires enabled capability `structural-interpretation-modeling`."
        )

    data = load_yaml_file(
        project.interpretations_registry,
        "structural interpretation registry",
        expected_schema_version=SUPPORTED_SCHEMA_VERSION,
    )
    root = _mapping(data, "root")
    assert_allowed_keys(
        root,
        {"schema_version", "relation_types", "interpretations", "members", "relations", "comparison_sets"},
        "Structural interpretation registry root",
    )

    relation_types: dict[str, InterpretationRelationType] = {}
    for type_id, raw in _mapping(root.get("relation_types"), "relation_types").items():
        _stable(type_id, f"relation_types.{type_id}")
        _pack_value(packs, "interpretation.relation-type", type_id, f"relation_types.{type_id}")
        context = f"relation_types.{type_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"label", "inverse_type", "symmetric", "canonical_direction", "acyclic_group"},
            f"Structural interpretation registry `{context}`",
        )
        acyclic_group = _optional_string(item, "acyclic_group", context)
        if acyclic_group is not None:
            _stable(acyclic_group, f"{context}.acyclic_group")
        relation_types[type_id] = InterpretationRelationType(
            type_id,
            _string(item, "label", context),
            _string(item, "inverse_type", context),
            _boolean(item, "symmetric", context),
            _boolean(item, "canonical_direction", context),
            acyclic_group,
        )
    _validate_relation_types(relation_types)

    interpretations: dict[str, StructuralInterpretation] = {}
    for interpretation_id, raw in _mapping(root.get("interpretations"), "interpretations").items():
        _stable(interpretation_id, f"interpretations.{interpretation_id}")
        context = f"interpretations.{interpretation_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"lifecycle", "label", "description"},
            f"Structural interpretation registry `{context}`",
        )
        lifecycle = _string(item, "lifecycle", context)
        _pack_value(packs, "interpretation.lifecycle", lifecycle, f"{context}.lifecycle")
        interpretations[interpretation_id] = StructuralInterpretation(
            interpretation_id,
            lifecycle,
            _string(item, "label", context),
            _optional_string(item, "description", context),
        )

    providers = _provider_targets(target_providers)
    prohibited_targets = {
        "structural-interpretation",
        "structural-interpretation-member",
        "structural-interpretation-relation",
        "structural-interpretation-set",
    }
    members: list[InterpretationMember] = []
    member_ids: set[str] = set()
    semantic_members: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(_list(root.get("members"), "members")):
        context = f"members[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"id", "interpretation_id", "target_type", "target_id"},
            f"Structural interpretation registry `{context}`",
        )
        member_id = _string(item, "id", context)
        _stable(member_id, f"{context}.id")
        if member_id in member_ids:
            raise ValueError(f"Structural interpretation member ID `{member_id}` is duplicated.")
        member_ids.add(member_id)
        interpretation_id = _string(item, "interpretation_id", context)
        if interpretation_id not in interpretations:
            raise ValueError(f"{context}.interpretation_id references unknown interpretation `{interpretation_id}`.")
        target_type = _string(item, "target_type", context)
        target_id = _string(item, "target_id", context)
        if target_type in prohibited_targets:
            raise ValueError(f"{context}.target_type cannot recursively reference `{target_type}`.")
        if target_type != "provenance-claim":
            provider = providers.get(target_type)
            if provider is None:
                raise ValueError(f"{context}.target_type references unsupported target type `{target_type}`.")
            provider.provenance_target(target_type, target_id)
        shape = (interpretation_id, target_type, target_id)
        if shape in semantic_members:
            raise ValueError(
                f"Structural interpretation `{interpretation_id}` repeats target `{target_type}:{target_id}`."
            )
        semantic_members.add(shape)
        members.append(InterpretationMember(member_id, interpretation_id, target_type, target_id))

    member_map = {item.id: item for item in members}
    relations: list[InterpretationRelation] = []
    relation_ids: set[str] = set()
    semantic_relations: set[tuple[str, str, str, str]] = set()
    for index, raw in enumerate(_list(root.get("relations"), "relations")):
        context = f"relations[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"id", "interpretation_id", "source_member_id", "relationship_type", "target_member_id"},
            f"Structural interpretation registry `{context}`",
        )
        relation_id = _string(item, "id", context)
        _stable(relation_id, f"{context}.id")
        if relation_id in relation_ids:
            raise ValueError(f"Structural interpretation relation ID `{relation_id}` is duplicated.")
        relation_ids.add(relation_id)
        interpretation_id = _string(item, "interpretation_id", context)
        if interpretation_id not in interpretations:
            raise ValueError(f"{context}.interpretation_id references unknown interpretation `{interpretation_id}`.")
        source_id = _string(item, "source_member_id", context)
        target_id = _string(item, "target_member_id", context)
        if source_id == target_id:
            raise ValueError(f"Structural interpretation relation `{relation_id}` cannot relate a member to itself.")
        if source_id not in member_map or target_id not in member_map:
            raise ValueError(
                f"Structural interpretation relation `{relation_id}` references an unknown member endpoint."
            )
        if (
            member_map[source_id].interpretation_id != interpretation_id
            or member_map[target_id].interpretation_id != interpretation_id
        ):
            raise ValueError(
                f"Structural interpretation relation `{relation_id}` endpoints must belong to `{interpretation_id}`."
            )
        type_id = _string(item, "relationship_type", context)
        if type_id not in relation_types:
            raise ValueError(f"{context}.relationship_type references unknown relation type `{type_id}`.")
        relation = InterpretationRelation(relation_id, interpretation_id, source_id, type_id, target_id)
        shape = _canonical_relation_shape(relation, relation_types)
        if shape in semantic_relations:
            raise ValueError(
                f"Structural interpretation relation `{relation_id}` duplicates a relation or its inverse."
            )
        semantic_relations.add(shape)
        relations.append(relation)
    relation_tuple = tuple(relations)
    _validate_acyclic_relations(relation_tuple, relation_types)

    comparison_sets: dict[str, InterpretationComparisonSet] = {}
    semantic_sets: set[tuple[str, tuple[str, ...]]] = set()
    for set_id, raw in _mapping(root.get("comparison_sets"), "comparison_sets").items():
        _stable(set_id, f"comparison_sets.{set_id}")
        context = f"comparison_sets.{set_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"label", "comparison_mode", "interpretation_ids"},
            f"Structural interpretation registry `{context}`",
        )
        mode = _string(item, "comparison_mode", context)
        _pack_value(packs, "interpretation.comparison-mode", mode, f"{context}.comparison_mode")
        interpretation_ids = _string_list(item, "interpretation_ids", context)
        if len(interpretation_ids) < 2:
            raise ValueError(
                f"Structural interpretation comparison set `{set_id}` requires at least two interpretations."
            )
        if len(set(interpretation_ids)) != len(interpretation_ids):
            raise ValueError(f"Structural interpretation comparison set `{set_id}` repeats an interpretation.")
        unknown = [item_id for item_id in interpretation_ids if item_id not in interpretations]
        if unknown:
            raise ValueError(
                f"Structural interpretation comparison set `{set_id}` references unknown interpretations: "
                f"{', '.join(unknown)}."
            )
        shape = (mode, tuple(sorted(interpretation_ids)))
        if shape in semantic_sets:
            raise ValueError(f"Structural interpretation comparison set `{set_id}` duplicates another set.")
        semantic_sets.add(shape)
        comparison_sets[set_id] = InterpretationComparisonSet(
            set_id,
            _string(item, "label", context),
            mode,
            interpretation_ids,
        )

    return StructuralInterpretationRegistry(
        project.interpretations_registry,
        SUPPORTED_SCHEMA_VERSION,
        relation_types,
        interpretations,
        tuple(members),
        relation_tuple,
        comparison_sets,
    )
