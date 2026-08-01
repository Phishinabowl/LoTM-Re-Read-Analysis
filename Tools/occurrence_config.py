from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from chronology_config import ChronologyRegistry
from project_config import ProjectConfig
from schema_pack_config import SchemaPackRegistry
from strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 2
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class OccurrenceBranch:
    id: str
    label: str
    parent_branch_id: str | None
    fork_occurrence_id: str | None


@dataclass(frozen=True)
class OccurrenceTemplate:
    id: str
    label: str
    kind: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class Recurrence:
    id: str
    label: str
    kind: str
    parent_recurrence_id: str | None


@dataclass(frozen=True)
class RecurrenceIteration:
    id: str
    recurrence_id: str
    ordinal: int
    parent_iteration_id: str | None
    status: str


@dataclass(frozen=True)
class OccurrenceBinding:
    id: str
    position_id: str
    role: str


@dataclass(frozen=True)
class Occurrence:
    id: str
    template_id: str
    label: str | None
    iteration_id: str | None
    branch_id: str
    bindings: tuple[OccurrenceBinding, ...]


@dataclass(frozen=True)
class OccurrenceTrack:
    id: str
    label: str
    kind: str
    subject_type: str
    subject_id: str
    occurrence_ids: tuple[str, ...]


@dataclass(frozen=True)
class OccurrenceTransition:
    id: str
    source_occurrence_id: str
    target_occurrence_id: str
    transition_kind: str
    transition_profile: str
    recurrence_id: str | None
    track_ids: tuple[str, ...]
    certainty: str


@dataclass(frozen=True)
class CausalRelation:
    id: str
    source_occurrence_id: str
    relation_type: str
    target_occurrence_id: str
    certainty: str


@dataclass(frozen=True)
class IterationCarryover:
    id: str
    source_iteration_id: str
    target_iteration_id: str
    track_id: str
    carryover_kind: str
    payload_target_type: str
    payload_target_id: str
    certainty: str


@dataclass(frozen=True)
class OccurrenceRegistry:
    path: Path
    schema_version: int
    branches: dict[str, OccurrenceBranch]
    templates: dict[str, OccurrenceTemplate]
    recurrences: dict[str, Recurrence]
    iterations: dict[str, RecurrenceIteration]
    occurrences: dict[str, Occurrence]
    tracks: dict[str, OccurrenceTrack]
    transitions: tuple[OccurrenceTransition, ...]
    causal_relations: tuple[CausalRelation, ...]
    carryovers: tuple[IterationCarryover, ...]

    def occurrences_for_iteration(self, iteration_id: str) -> tuple[Occurrence, ...]:
        self._known(self.iterations, iteration_id, "iteration")
        return tuple(item for item in self.occurrences.values() if item.iteration_id == iteration_id)

    def occurrences_at_position(self, position_id: str) -> tuple[Occurrence, ...]:
        return tuple(
            item
            for item in self.occurrences.values()
            if any(binding.position_id == position_id for binding in item.bindings)
        )

    def occurrences_for_iteration_on_track(self, iteration_id: str, track_id: str) -> tuple[Occurrence, ...]:
        self._known(self.iterations, iteration_id, "iteration")
        track = self._known(self.tracks, track_id, "track")
        return tuple(
            self.occurrences[occurrence_id]
            for occurrence_id in track.occurrence_ids
            if self.occurrences[occurrence_id].iteration_id == iteration_id
        )

    def previous_before_iteration(self, track_id: str, iteration_id: str) -> Occurrence | None:
        occurrences = self.occurrences_for_iteration_on_track(iteration_id, track_id)
        if not occurrences:
            return None
        return self.previous_on_track(track_id, occurrences[0].id)

    def next_after_iteration(self, track_id: str, iteration_id: str) -> Occurrence | None:
        occurrences = self.occurrences_for_iteration_on_track(iteration_id, track_id)
        if not occurrences:
            return None
        return self.next_on_track(track_id, occurrences[-1].id)

    def previous_on_track(self, track_id: str, occurrence_id: str) -> Occurrence | None:
        return self._adjacent_on_track(track_id, occurrence_id, -1)

    def next_on_track(self, track_id: str, occurrence_id: str) -> Occurrence | None:
        return self._adjacent_on_track(track_id, occurrence_id, 1)

    def carryovers_into(self, iteration_id: str) -> tuple[IterationCarryover, ...]:
        self._known(self.iterations, iteration_id, "iteration")
        return tuple(item for item in self.carryovers if item.target_iteration_id == iteration_id)

    def recurrence_for_occurrence(self, occurrence_id: str) -> Recurrence | None:
        occurrence = self._known(self.occurrences, occurrence_id, "occurrence")
        if occurrence.iteration_id is None:
            return None
        return self.recurrences[self.iterations[occurrence.iteration_id].recurrence_id]

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {
            "occurrence-branch": self.branches,
            "occurrence-template": self.templates,
            "recurrence": self.recurrences,
            "recurrence-iteration": self.iterations,
            "occurrence": self.occurrences,
            "occurrence-binding": {
                binding.id: binding
                for occurrence in self.occurrences.values()
                for binding in occurrence.bindings
            },
            "occurrence-track": self.tracks,
            "occurrence-transition": {item.id: item for item in self.transitions},
            "causal-relation": {item.id: item for item in self.causal_relations},
            "iteration-carryover": {item.id: item for item in self.carryovers},
        }

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        targets = self.provenance_targets().get(subject_type)
        if targets is None:
            raise ValueError(f"Unsupported occurrence-registry subject type `{subject_type}`.")
        return self._known(targets, subject_id, subject_type)

    def _adjacent_on_track(self, track_id: str, occurrence_id: str, offset: int) -> Occurrence | None:
        track = self._known(self.tracks, track_id, "track")
        if occurrence_id not in track.occurrence_ids:
            raise ValueError(f"Occurrence `{occurrence_id}` is not on track `{track_id}`.")
        index = track.occurrence_ids.index(occurrence_id) + offset
        if index < 0 or index >= len(track.occurrence_ids):
            return None
        return self.occurrences[track.occurrence_ids[index]]

    @staticmethod
    def _known(items: dict[str, object], item_id: str, kind: str):
        if item_id not in items:
            raise ValueError(f"Unknown {kind} `{item_id}`.")
        return items[item_id]


def _mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a mapping.")
    return value


def _list(value: object, context: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{context} must be a list.")
    return value


def _string(item: dict, key: str, context: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string.")
    return value.strip()


def _optional_string(item: dict, key: str, context: str) -> str | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string or null.")
    return value.strip()


def _strings(item: dict, key: str, context: str) -> tuple[str, ...]:
    values = _list(item.get(key), f"{context}.{key}")
    result = tuple(value.strip() for value in values if isinstance(value, str) and value.strip())
    if len(result) != len(values) or len(set(result)) != len(result):
        raise ValueError(f"{context}.{key} must contain unique non-empty strings.")
    return result


def _stable(value: str, context: str) -> str:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{context} must be a lowercase kebab-case stable ID: {value}")
    return value


def _value(packs: SchemaPackRegistry, namespace: str, value: str, context: str) -> None:
    if value not in packs.allowed_values(namespace):
        raise ValueError(f"{context} uses `{value}`, which is not provided in `{namespace}`.")


def _acyclic_parent(items: dict[str, object], parent_attribute: str, kind: str) -> None:
    for item_id, item in items.items():
        seen: set[str] = set()
        current = item_id
        while current is not None:
            if current in seen:
                raise ValueError(f"{kind} parent cycle includes `{current}`.")
            seen.add(current)
            current = getattr(items[current], parent_attribute)


def parse_occurrence_registry(
    data: object,
    path: Path,
    packs: SchemaPackRegistry,
    chronology: ChronologyRegistry,
    *,
    subject_targets: dict[str, set[str]] | None = None,
    payload_targets: dict[str, set[str]] | None = None,
) -> OccurrenceRegistry:
    if not packs.capability_enabled("occurrence-recurrence-modeling"):
        raise ValueError("Occurrence registry requires enabled capability `occurrence-recurrence-modeling`.")
    root = _mapping(data, "Occurrence registry root")
    assert_allowed_keys(root, {"schema_version", "branches", "templates", "recurrences", "iterations", "occurrences", "tracks", "transitions", "causal_relations", "carryovers"}, "Occurrence registry root")
    if root.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"Unsupported occurrence schema_version {root.get('schema_version')!r}; expected {SUPPORTED_SCHEMA_VERSION}.")

    branches: dict[str, OccurrenceBranch] = {}
    for branch_id, raw in _mapping(root.get("branches"), "occurrences.branches").items():
        _stable(branch_id, "occurrence branch ID")
        context = f"branches.{branch_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "parent_branch_id", "fork_occurrence_id"}, context)
        parent_id = _optional_string(item, "parent_branch_id", context)
        fork_id = _optional_string(item, "fork_occurrence_id", context)
        if parent_id is not None:
            _stable(parent_id, f"{context}.parent_branch_id")
        if fork_id is not None:
            _stable(fork_id, f"{context}.fork_occurrence_id")
        if (parent_id is None) != (fork_id is None):
            raise ValueError(f"{context} must set both parent_branch_id and fork_occurrence_id, or neither.")
        branches[branch_id] = OccurrenceBranch(branch_id, _string(item, "label", context), parent_id, fork_id)
    if not branches:
        raise ValueError("occurrences.branches cannot be empty.")
    for branch in branches.values():
        if branch.parent_branch_id is not None and branch.parent_branch_id not in branches:
            raise ValueError(f"branches.{branch.id}.parent_branch_id references unknown branch `{branch.parent_branch_id}`.")
    _acyclic_parent(branches, "parent_branch_id", "Branch")

    templates: dict[str, OccurrenceTemplate] = {}
    for template_id, raw in _mapping(root.get("templates"), "occurrences.templates").items():
        _stable(template_id, "occurrence template ID")
        context = f"templates.{template_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "aliases"}, context)
        kind = _string(item, "kind", context)
        _value(packs, "occurrence.template-kind", kind, f"{context}.kind")
        templates[template_id] = OccurrenceTemplate(template_id, _string(item, "label", context), kind, _strings(item, "aliases", context))

    recurrences: dict[str, Recurrence] = {}
    for recurrence_id, raw in _mapping(root.get("recurrences"), "occurrences.recurrences").items():
        _stable(recurrence_id, "recurrence ID")
        context = f"recurrences.{recurrence_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "parent_recurrence_id"}, context)
        kind = _string(item, "kind", context)
        _value(packs, "occurrence.recurrence-kind", kind, f"{context}.kind")
        parent_id = _optional_string(item, "parent_recurrence_id", context)
        recurrences[recurrence_id] = Recurrence(recurrence_id, _string(item, "label", context), kind, parent_id)
    for recurrence in recurrences.values():
        if recurrence.parent_recurrence_id is not None and recurrence.parent_recurrence_id not in recurrences:
            raise ValueError(f"recurrences.{recurrence.id}.parent_recurrence_id references unknown recurrence `{recurrence.parent_recurrence_id}`.")
    _acyclic_parent(recurrences, "parent_recurrence_id", "Recurrence")

    iterations: dict[str, RecurrenceIteration] = {}
    ordinals: set[tuple[str, int]] = set()
    for iteration_id, raw in _mapping(root.get("iterations"), "occurrences.iterations").items():
        _stable(iteration_id, "recurrence iteration ID")
        context = f"iterations.{iteration_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"recurrence_id", "ordinal", "parent_iteration_id", "status"}, context)
        recurrence_id = _string(item, "recurrence_id", context)
        if recurrence_id not in recurrences:
            raise ValueError(f"{context}.recurrence_id references unknown recurrence `{recurrence_id}`.")
        ordinal = item.get("ordinal")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
            raise ValueError(f"{context}.ordinal must be a positive integer.")
        if (recurrence_id, ordinal) in ordinals:
            raise ValueError(f"{context}.ordinal duplicates ordinal {ordinal} in `{recurrence_id}`.")
        ordinals.add((recurrence_id, ordinal))
        status = _string(item, "status", context)
        _value(packs, "occurrence.iteration-status", status, f"{context}.status")
        iterations[iteration_id] = RecurrenceIteration(iteration_id, recurrence_id, ordinal, _optional_string(item, "parent_iteration_id", context), status)
    for iteration in iterations.values():
        parent_recurrence_id = recurrences[iteration.recurrence_id].parent_recurrence_id
        if parent_recurrence_id is None:
            if iteration.parent_iteration_id is not None:
                raise ValueError(f"iterations.{iteration.id}.parent_iteration_id is only valid for a nested recurrence.")
        else:
            if iteration.parent_iteration_id not in iterations:
                raise ValueError(f"iterations.{iteration.id}.parent_iteration_id must reference an iteration of parent recurrence `{parent_recurrence_id}`.")
            if iterations[iteration.parent_iteration_id].recurrence_id != parent_recurrence_id:
                raise ValueError(f"iterations.{iteration.id}.parent_iteration_id must belong to parent recurrence `{parent_recurrence_id}`.")

    occurrences: dict[str, Occurrence] = {}
    binding_ids: set[str] = set()
    for occurrence_id, raw in _mapping(root.get("occurrences"), "occurrences.occurrences").items():
        _stable(occurrence_id, "occurrence ID")
        context = f"occurrences.{occurrence_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"template_id", "label", "iteration_id", "branch_id", "bindings"}, context)
        template_id = _string(item, "template_id", context)
        branch_id = _string(item, "branch_id", context)
        iteration_id = _optional_string(item, "iteration_id", context)
        if template_id not in templates:
            raise ValueError(f"{context}.template_id references unknown template `{template_id}`.")
        if branch_id not in branches:
            raise ValueError(f"{context}.branch_id references unknown branch `{branch_id}`.")
        if iteration_id is not None and iteration_id not in iterations:
            raise ValueError(f"{context}.iteration_id references unknown iteration `{iteration_id}`.")
        bindings: list[OccurrenceBinding] = []
        for index, raw_binding in enumerate(_list(item.get("bindings"), f"{context}.bindings")):
            binding_context = f"{context}.bindings[{index}]"
            binding = _mapping(raw_binding, binding_context)
            assert_allowed_keys(binding, {"id", "position_id", "role"}, binding_context)
            binding_id = _stable(_string(binding, "id", binding_context), f"{binding_context}.id")
            if binding_id in binding_ids:
                raise ValueError(f"{binding_context}.id duplicates `{binding_id}`.")
            binding_ids.add(binding_id)
            position_id = _string(binding, "position_id", binding_context)
            if position_id not in chronology.positions:
                raise ValueError(f"{binding_context}.position_id references unknown chronology position `{position_id}`.")
            role = _string(binding, "role", binding_context)
            _value(packs, "occurrence.binding-role", role, f"{binding_context}.role")
            bindings.append(OccurrenceBinding(binding_id, position_id, role))
        semantic_bindings: set[tuple[str, str]] = set()
        for binding in bindings:
            semantic_key = (binding.position_id, binding.role)
            if semantic_key in semantic_bindings:
                raise ValueError(f"{context}.bindings duplicates `{binding.role}` binding to `{binding.position_id}`.")
            semantic_bindings.add(semantic_key)
        primary_bindings = [binding for binding in bindings if binding.role == "primary"]
        for left_index, left in enumerate(primary_bindings):
            for right in primary_bindings[left_index + 1:]:
                comparison = chronology.compare_positions(left.position_id, right.position_id)
                if comparison in {"before", "after"}:
                    raise ValueError(
                        f"{context}.bindings declares ordered chronology positions `{left.position_id}` and "
                        f"`{right.position_id}` as primary coordinates of one occurrence."
                    )
        occurrences[occurrence_id] = Occurrence(occurrence_id, template_id, _optional_string(item, "label", context), iteration_id, branch_id, tuple(bindings))

    for branch in branches.values():
        if branch.fork_occurrence_id is not None and branch.fork_occurrence_id not in occurrences:
            raise ValueError(f"branches.{branch.id}.fork_occurrence_id references unknown occurrence `{branch.fork_occurrence_id}`.")
        if (
            branch.fork_occurrence_id is not None
            and occurrences[branch.fork_occurrence_id].branch_id != branch.parent_branch_id
        ):
            raise ValueError(f"branches.{branch.id}.fork_occurrence_id must belong to parent branch `{branch.parent_branch_id}`.")
    occurrence_branch_ids = set(branches)
    for context in chronology.narrative_contexts:
        if context.branch_id is not None and context.branch_id not in occurrence_branch_ids:
            raise ValueError(f"Chronology context `{context.id}` references unknown occurrence branch `{context.branch_id}`.")

    tracks: dict[str, OccurrenceTrack] = {}
    for track_id, raw in _mapping(root.get("tracks"), "occurrences.tracks").items():
        _stable(track_id, "occurrence track ID")
        context = f"tracks.{track_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "subject_type", "subject_id", "occurrence_ids"}, context)
        kind = _string(item, "kind", context)
        _value(packs, "occurrence.track-kind", kind, f"{context}.kind")
        subject_type = _string(item, "subject_type", context)
        subject_id = _string(item, "subject_id", context)
        if subject_targets is None or subject_type not in subject_targets or subject_id not in subject_targets[subject_type]:
            raise ValueError(f"{context} references unknown subject `{subject_type}:{subject_id}`.")
        occurrence_ids = _strings(item, "occurrence_ids", context)
        unknown = set(occurrence_ids) - set(occurrences)
        if unknown:
            raise ValueError(f"{context}.occurrence_ids references unknown occurrences: {', '.join(sorted(unknown))}.")
        tracks[track_id] = OccurrenceTrack(track_id, _string(item, "label", context), kind, subject_type, subject_id, occurrence_ids)

    seen_ids: set[str] = set()
    transitions: list[OccurrenceTransition] = []
    for index, raw in enumerate(_list(root.get("transitions"), "occurrences.transitions")):
        context = f"transitions[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"id", "source_occurrence_id", "target_occurrence_id", "transition_kind", "transition_profile", "recurrence_id", "track_ids", "certainty"}, context)
        transition_id = _stable(_string(item, "id", context), f"{context}.id")
        if transition_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{transition_id}`.")
        seen_ids.add(transition_id)
        source_id = _string(item, "source_occurrence_id", context)
        target_id = _string(item, "target_occurrence_id", context)
        if source_id not in occurrences or target_id not in occurrences:
            raise ValueError(f"{context} must reference known source and target occurrences.")
        kind = _string(item, "transition_kind", context)
        _value(packs, "occurrence.transition-kind", kind, f"{context}.transition_kind")
        profile = _string(item, "transition_profile", context)
        _value(packs, "occurrence.transition-profile", profile, f"{context}.transition_profile")
        _value(
            packs,
            "occurrence.transition-kind-profile",
            f"{kind}-uses-{profile}",
            f"{context}.transition_kind/transition_profile",
        )
        recurrence_id = _optional_string(item, "recurrence_id", context)
        if recurrence_id is not None and recurrence_id not in recurrences:
            raise ValueError(f"{context}.recurrence_id references unknown recurrence `{recurrence_id}`.")
        track_ids = _strings(item, "track_ids", context)
        if set(track_ids) - set(tracks):
            raise ValueError(f"{context}.track_ids references unknown tracks.")
        for track_id in track_ids:
            track_occurrences = tracks[track_id].occurrence_ids
            if source_id not in track_occurrences or target_id not in track_occurrences:
                raise ValueError(f"{context} endpoints must both appear on track `{track_id}`.")
            if track_occurrences.index(source_id) >= track_occurrences.index(target_id):
                raise ValueError(f"{context} must advance in declared track order on `{track_id}`.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        transition = OccurrenceTransition(transition_id, source_id, target_id, kind, profile, recurrence_id, track_ids, certainty)
        _validate_transition_profile(transition, occurrences, iterations, branches, recurrence_id, context)
        semantic_key = (source_id, target_id, kind, profile, recurrence_id, tuple(sorted(track_ids)))
        if any(
            (existing.source_occurrence_id, existing.target_occurrence_id, existing.transition_kind,
             existing.transition_profile, existing.recurrence_id, tuple(sorted(existing.track_ids))) == semantic_key
            for existing in transitions
        ):
            raise ValueError(f"{context} duplicates an existing semantic transition.")
        transitions.append(transition)

    fork_transitions: dict[str, list[OccurrenceTransition]] = {branch_id: [] for branch_id in branches}
    for transition in transitions:
        if transition.transition_profile != "branch-fork":
            continue
        target_branch_id = occurrences[transition.target_occurrence_id].branch_id
        fork_transitions[target_branch_id].append(transition)
    for branch in branches.values():
        if branch.parent_branch_id is None:
            continue
        matches = fork_transitions[branch.id]
        if len(matches) != 1:
            raise ValueError(f"branches.{branch.id} must have exactly one matching branch-fork transition.")

    causal_relations: list[CausalRelation] = []
    for index, raw in enumerate(_list(root.get("causal_relations"), "occurrences.causal_relations")):
        context = f"causal_relations[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"id", "source_occurrence_id", "relation_type", "target_occurrence_id", "certainty"}, context)
        relation_id = _stable(_string(item, "id", context), f"{context}.id")
        if relation_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{relation_id}`.")
        seen_ids.add(relation_id)
        source_id = _string(item, "source_occurrence_id", context)
        target_id = _string(item, "target_occurrence_id", context)
        if source_id not in occurrences or target_id not in occurrences:
            raise ValueError(f"{context} must reference known source and target occurrences.")
        relation_type = _string(item, "relation_type", context)
        _value(packs, "occurrence.causal-relation-type", relation_type, f"{context}.relation_type")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        causal_relations.append(CausalRelation(relation_id, source_id, relation_type, target_id, certainty))

    carryovers: list[IterationCarryover] = []
    for index, raw in enumerate(_list(root.get("carryovers"), "occurrences.carryovers")):
        context = f"carryovers[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"id", "source_iteration_id", "target_iteration_id", "track_id", "carryover_kind", "payload_target_type", "payload_target_id", "certainty"}, context)
        carryover_id = _stable(_string(item, "id", context), f"{context}.id")
        if carryover_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{carryover_id}`.")
        seen_ids.add(carryover_id)
        source_id = _string(item, "source_iteration_id", context)
        target_id = _string(item, "target_iteration_id", context)
        track_id = _string(item, "track_id", context)
        if source_id not in iterations or target_id not in iterations or track_id not in tracks:
            raise ValueError(f"{context} must reference known source/target iterations and track.")
        source = iterations[source_id]
        target = iterations[target_id]
        if source.recurrence_id != target.recurrence_id or source.ordinal >= target.ordinal:
            raise ValueError(f"{context} must advance between iterations of the same recurrence.")
        track_iteration_ids = {
            occurrences[occurrence_id].iteration_id
            for occurrence_id in tracks[track_id].occurrence_ids
        }
        if source_id not in track_iteration_ids or target_id not in track_iteration_ids:
            raise ValueError(f"{context}.track_id must participate in both source and target iterations.")
        kind = _string(item, "carryover_kind", context)
        _value(packs, "occurrence.carryover-kind", kind, f"{context}.carryover_kind")
        payload_type = _string(item, "payload_target_type", context)
        payload_id = _string(item, "payload_target_id", context)
        _stable(payload_type, f"{context}.payload_target_type")
        _stable(payload_id, f"{context}.payload_target_id")
        known_payload_targets = _payload_target_ids(
            payload_type, branches, templates, recurrences, iterations, occurrences, tracks, payload_targets
        )
        if payload_id not in known_payload_targets:
            raise ValueError(f"{context} references unknown payload target `{payload_type}:{payload_id}`.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        semantic_key = (source_id, target_id, track_id, kind, payload_type, payload_id)
        if any(
            (existing.source_iteration_id, existing.target_iteration_id, existing.track_id, existing.carryover_kind,
             existing.payload_target_type, existing.payload_target_id) == semantic_key
            for existing in carryovers
        ):
            raise ValueError(f"{context} duplicates an existing semantic carryover.")
        carryovers.append(IterationCarryover(carryover_id, source_id, target_id, track_id, kind, payload_type, payload_id, certainty))

    return OccurrenceRegistry(path, SUPPORTED_SCHEMA_VERSION, branches, templates, recurrences, iterations, occurrences, tracks, tuple(transitions), tuple(causal_relations), tuple(carryovers))


def _validate_transition_profile(
    transition: OccurrenceTransition,
    occurrences: dict[str, Occurrence],
    iterations: dict[str, RecurrenceIteration],
    branches: dict[str, OccurrenceBranch],
    recurrence_id: str | None,
    context: str,
) -> None:
    source_occurrence = occurrences[transition.source_occurrence_id]
    target_occurrence = occurrences[transition.target_occurrence_id]
    source_iteration = iterations.get(source_occurrence.iteration_id) if source_occurrence.iteration_id else None
    target_iteration = iterations.get(target_occurrence.iteration_id) if target_occurrence.iteration_id else None

    if transition.transition_profile in {"ordered", "jump"}:
        if recurrence_id is not None and (
            source_iteration is None
            or target_iteration is None
            or source_iteration.recurrence_id != recurrence_id
            or target_iteration.recurrence_id != recurrence_id
        ):
            raise ValueError(f"{context} scoped `{transition.transition_profile}` endpoints must belong to recurrence `{recurrence_id}`.")
        return

    if transition.transition_profile == "recurrence-advance":
        if source_iteration is None or target_iteration is None or recurrence_id is None:
            raise ValueError(f"{context} recurrence-advance transitions require recurrence-bound source and target iterations.")
        if (
            source_iteration.recurrence_id != recurrence_id
            or target_iteration.recurrence_id != recurrence_id
            or source_iteration.ordinal >= target_iteration.ordinal
        ):
            raise ValueError(f"{context} recurrence-advance transition must advance iterations in recurrence `{recurrence_id}`.")
        return

    if transition.transition_profile == "recurrence-exit":
        if source_iteration is None or recurrence_id is None or source_iteration.recurrence_id != recurrence_id:
            raise ValueError(f"{context} recurrence-exit source must belong to recurrence `{recurrence_id}`.")
        if target_iteration is not None and target_iteration.recurrence_id == recurrence_id:
            raise ValueError(f"{context} recurrence-exit target must leave recurrence `{recurrence_id}`.")
        return

    if transition.transition_profile == "branch-fork":
        _validate_optional_transition_recurrence_scope(
            transition, source_iteration, target_iteration, recurrence_id, context
        )
        target_branch = branches[target_occurrence.branch_id]
        if (
            target_branch.parent_branch_id is None
            or target_branch.parent_branch_id != source_occurrence.branch_id
            or target_branch.fork_occurrence_id != source_occurrence.id
        ):
            raise ValueError(f"{context} branch-fork endpoints do not match the target branch lineage.")
        return

    if transition.transition_profile == "branch-merge":
        _validate_optional_transition_recurrence_scope(
            transition, source_iteration, target_iteration, recurrence_id, context
        )
        if source_occurrence.branch_id == target_occurrence.branch_id:
            raise ValueError(f"{context} branch-merge endpoints must belong to different branches.")
        return

    raise ValueError(f"{context} uses unsupported transition profile `{transition.transition_profile}`.")


def _validate_optional_transition_recurrence_scope(
    transition: OccurrenceTransition,
    source_iteration: RecurrenceIteration | None,
    target_iteration: RecurrenceIteration | None,
    recurrence_id: str | None,
    context: str,
) -> None:
    if recurrence_id is not None and (
        source_iteration is None
        or target_iteration is None
        or source_iteration.recurrence_id != recurrence_id
        or target_iteration.recurrence_id != recurrence_id
    ):
        raise ValueError(
            f"{context} scoped `{transition.transition_profile}` endpoints must belong to recurrence `{recurrence_id}`."
        )


def _payload_target_ids(
    target_type: str,
    branches: dict[str, OccurrenceBranch],
    templates: dict[str, OccurrenceTemplate],
    recurrences: dict[str, Recurrence],
    iterations: dict[str, RecurrenceIteration],
    occurrences: dict[str, Occurrence],
    tracks: dict[str, OccurrenceTrack],
    external_targets: dict[str, set[str]] | None,
) -> set[str]:
    internal_targets = {
        "occurrence-branch": set(branches),
        "occurrence-template": set(templates),
        "recurrence": set(recurrences),
        "recurrence-iteration": set(iterations),
        "occurrence": set(occurrences),
        "occurrence-track": set(tracks),
    }
    if target_type in internal_targets:
        return internal_targets[target_type]
    if external_targets is not None and target_type in external_targets:
        return external_targets[target_type]
    return set()


def load_occurrence_registry(
    project: ProjectConfig,
    packs: SchemaPackRegistry,
    chronology: ChronologyRegistry,
    *,
    subject_targets: dict[str, set[str]] | None = None,
    payload_targets: dict[str, set[str]] | None = None,
) -> OccurrenceRegistry:
    data = load_yaml_file(project.occurrences_registry, "occurrence registry", expected_schema_version=SUPPORTED_SCHEMA_VERSION)
    return parse_occurrence_registry(
        data, project.occurrences_registry, packs, chronology,
        subject_targets=subject_targets, payload_targets=payload_targets,
    )
