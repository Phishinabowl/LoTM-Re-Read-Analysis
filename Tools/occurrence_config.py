from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from chronology_config import ChronologyRegistry
from project_config import ProjectConfig
from schema_pack_config import SchemaPackRegistry
from strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_VERSION = 3
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
class RecurrencePattern:
    id: str
    label: str
    kind: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class Recurrence:
    id: str
    label: str
    pattern_id: str
    parent_recurrence_id: str | None
    status: str


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
class OccurrenceOutcome:
    id: str
    occurrence_id: str
    subject_type: str
    subject_id: str
    outcome_kind: str
    result_target_type: str | None
    result_target_id: str | None
    certainty: str


@dataclass(frozen=True)
class RecurrenceRuleCondition:
    id: str
    condition_kind: str
    target_type: str
    target_id: str
    expected_value: str


@dataclass(frozen=True)
class RecurrenceRuleEffect:
    id: str
    effect_kind: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class RecurrenceRule:
    id: str
    label: str
    pattern_id: str
    rule_kind: str
    condition_logic: str
    conditions: tuple[RecurrenceRuleCondition, ...]
    effects: tuple[RecurrenceRuleEffect, ...]


@dataclass(frozen=True)
class StateSourceTarget:
    id: str
    target_type: str
    target_id: str
    role: str


@dataclass(frozen=True)
class StateTransition:
    id: str
    subject_type: str
    subject_id: str
    payload_target_type: str
    payload_target_id: str
    state_kind: str
    change_kind: str
    change_profile: str
    mechanism: str
    prior_availability: str
    resulting_availability: str
    prior_attitude: str | None
    resulting_attitude: str | None
    completeness: str
    activation_occurrence_id: str
    condition_rule_id: str | None
    track_ids: tuple[str, ...]
    source_targets: tuple[StateSourceTarget, ...]
    certainty: str


@dataclass(frozen=True)
class IterationCarryover:
    id: str
    source_iteration_id: str
    target_iteration_id: str
    track_id: str
    state_transition_id: str
    certainty: str


@dataclass(frozen=True)
class OccurrenceRegistry:
    path: Path
    schema_version: int
    branches: dict[str, OccurrenceBranch]
    templates: dict[str, OccurrenceTemplate]
    recurrence_patterns: dict[str, RecurrencePattern]
    recurrences: dict[str, Recurrence]
    iterations: dict[str, RecurrenceIteration]
    occurrences: dict[str, Occurrence]
    tracks: dict[str, OccurrenceTrack]
    transitions: tuple[OccurrenceTransition, ...]
    causal_relations: tuple[CausalRelation, ...]
    outcomes: tuple[OccurrenceOutcome, ...]
    rules: tuple[RecurrenceRule, ...]
    state_transitions: tuple[StateTransition, ...]
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

    def outcomes_for_occurrence(self, occurrence_id: str) -> tuple[OccurrenceOutcome, ...]:
        self._known(self.occurrences, occurrence_id, "occurrence")
        return tuple(item for item in self.outcomes if item.occurrence_id == occurrence_id)

    def rules_for_pattern(self, pattern_id: str) -> tuple[RecurrenceRule, ...]:
        self._known(self.recurrence_patterns, pattern_id, "recurrence pattern")
        return tuple(item for item in self.rules if item.pattern_id == pattern_id)

    def state_transitions_for_subject(self, subject_type: str, subject_id: str) -> tuple[StateTransition, ...]:
        return tuple(
            item for item in self.state_transitions
            if item.subject_type == subject_type and item.subject_id == subject_id
        )

    def state_at(
        self,
        track_id: str,
        occurrence_id: str,
        payload_target_type: str,
        payload_target_id: str,
        state_kind: str,
    ) -> StateTransition | None:
        track = self._known(self.tracks, track_id, "track")
        if occurrence_id not in track.occurrence_ids:
            raise ValueError(f"Occurrence `{occurrence_id}` is not on track `{track_id}`.")
        boundary = track.occurrence_ids.index(occurrence_id)
        candidates = [
            item for item in self.state_transitions
            if track_id in item.track_ids
            and item.payload_target_type == payload_target_type
            and item.payload_target_id == payload_target_id
            and item.state_kind == state_kind
            and track.occurrence_ids.index(item.activation_occurrence_id) <= boundary
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda item: track.occurrence_ids.index(item.activation_occurrence_id))

    def recurrence_for_occurrence(self, occurrence_id: str) -> Recurrence | None:
        occurrence = self._known(self.occurrences, occurrence_id, "occurrence")
        if occurrence.iteration_id is None:
            return None
        return self.recurrences[self.iterations[occurrence.iteration_id].recurrence_id]

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return {
            "occurrence-branch": self.branches,
            "occurrence-template": self.templates,
            "recurrence-pattern": self.recurrence_patterns,
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
            "occurrence-outcome": {item.id: item for item in self.outcomes},
            "recurrence-rule": {item.id: item for item in self.rules},
            "state-transition": {item.id: item for item in self.state_transitions},
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
    if not packs.capability_enabled("recurrence-rule-modeling"):
        raise ValueError("Occurrence registry requires enabled capability `recurrence-rule-modeling`.")
    if not packs.capability_enabled("state-availability-acquisition"):
        raise ValueError("Occurrence registry requires enabled capability `state-availability-acquisition`.")
    root = _mapping(data, "Occurrence registry root")
    assert_allowed_keys(
        root,
        {
            "schema_version", "branches", "templates", "recurrence_patterns", "recurrences",
            "iterations", "occurrences", "tracks", "transitions", "causal_relations",
            "outcomes", "rules", "state_transitions", "carryovers",
        },
        "Occurrence registry root",
    )
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

    recurrence_patterns: dict[str, RecurrencePattern] = {}
    for pattern_id, raw in _mapping(root.get("recurrence_patterns"), "occurrences.recurrence_patterns").items():
        _stable(pattern_id, "recurrence pattern ID")
        context = f"recurrence_patterns.{pattern_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "aliases"}, context)
        kind = _string(item, "kind", context)
        _value(packs, "occurrence.recurrence-kind", kind, f"{context}.kind")
        recurrence_patterns[pattern_id] = RecurrencePattern(
            pattern_id,
            _string(item, "label", context),
            kind,
            _strings(item, "aliases", context),
        )

    recurrences: dict[str, Recurrence] = {}
    for recurrence_id, raw in _mapping(root.get("recurrences"), "occurrences.recurrences").items():
        _stable(recurrence_id, "recurrence ID")
        context = f"recurrences.{recurrence_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "pattern_id", "parent_recurrence_id", "status"}, context)
        pattern_id = _string(item, "pattern_id", context)
        if pattern_id not in recurrence_patterns:
            raise ValueError(f"{context}.pattern_id references unknown recurrence pattern `{pattern_id}`.")
        parent_id = _optional_string(item, "parent_recurrence_id", context)
        status = _string(item, "status", context)
        _value(packs, "occurrence.recurrence-status", status, f"{context}.status")
        recurrences[recurrence_id] = Recurrence(
            recurrence_id,
            _string(item, "label", context),
            pattern_id,
            parent_id,
            status,
        )
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
    _validate_iteration_lifecycle(recurrences, iterations)

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
    _validate_track_iteration_order(tracks, occurrences, iterations)

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
        if source_id == target_id:
            raise ValueError(f"{context} must connect distinct occurrence identities.")
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
        _validate_transition_profile(
            transition, occurrences, iterations, recurrences, branches, chronology, recurrence_id, context
        )
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
    causal_semantics: set[tuple[str, str, str]] = set()
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
        semantic_key = (source_id, relation_type, target_id)
        if semantic_key in causal_semantics:
            raise ValueError(f"{context} duplicates an existing semantic causal relation.")
        causal_semantics.add(semantic_key)
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        causal_relations.append(CausalRelation(relation_id, source_id, relation_type, target_id, certainty))

    outcomes: list[OccurrenceOutcome] = []
    outcome_semantics: set[tuple[str, str, str, str, str | None, str | None]] = set()
    for index, raw in enumerate(_list(root.get("outcomes"), "occurrences.outcomes")):
        context = f"outcomes[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"id", "occurrence_id", "subject_type", "subject_id", "outcome_kind", "result_target_type", "result_target_id", "certainty"},
            context,
        )
        outcome_id = _stable(_string(item, "id", context), f"{context}.id")
        if outcome_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{outcome_id}`.")
        seen_ids.add(outcome_id)
        occurrence_id = _string(item, "occurrence_id", context)
        if occurrence_id not in occurrences:
            raise ValueError(f"{context}.occurrence_id references unknown occurrence `{occurrence_id}`.")
        subject_type = _string(item, "subject_type", context)
        subject_id = _string(item, "subject_id", context)
        _known_external_target(subject_targets, subject_type, subject_id, f"{context}.subject")
        outcome_kind = _string(item, "outcome_kind", context)
        _value(packs, "occurrence.outcome-kind", outcome_kind, f"{context}.outcome_kind")
        result_type = _optional_string(item, "result_target_type", context)
        result_id = _optional_string(item, "result_target_id", context)
        if (result_type is None) != (result_id is None):
            raise ValueError(f"{context} must set both result target fields, or neither.")
        if result_type is not None:
            _stable(result_type, f"{context}.result_target_type")
            _stable(result_id, f"{context}.result_target_id")
            if result_id not in _target_ids(
                result_type, branches, templates, recurrence_patterns, recurrences, iterations,
                occurrences, tracks, {}, {}, {}, payload_targets,
            ):
                raise ValueError(f"{context} references unknown result target `{result_type}:{result_id}`.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        semantic_key = (occurrence_id, subject_type, subject_id, outcome_kind, result_type, result_id)
        if semantic_key in outcome_semantics:
            raise ValueError(f"{context} duplicates an existing semantic occurrence outcome.")
        outcome_semantics.add(semantic_key)
        outcomes.append(OccurrenceOutcome(
            outcome_id, occurrence_id, subject_type, subject_id, outcome_kind, result_type, result_id, certainty
        ))

    raw_rules = _list(root.get("rules"), "occurrences.rules")
    rule_ids = _precollect_list_ids(raw_rules, "rules")
    raw_states = _list(root.get("state_transitions"), "occurrences.state_transitions")
    state_ids = _precollect_list_ids(raw_states, "state_transitions")

    rules: list[RecurrenceRule] = []
    nested_rule_ids: set[str] = set()
    rule_semantics: set[tuple] = set()
    for index, raw in enumerate(raw_rules):
        context = f"rules[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"id", "label", "pattern_id", "rule_kind", "condition_logic", "conditions", "effects"},
            context,
        )
        rule_id = _stable(_string(item, "id", context), f"{context}.id")
        if rule_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{rule_id}`.")
        seen_ids.add(rule_id)
        pattern_id = _string(item, "pattern_id", context)
        if pattern_id not in recurrence_patterns:
            raise ValueError(f"{context}.pattern_id references unknown recurrence pattern `{pattern_id}`.")
        rule_kind = _string(item, "rule_kind", context)
        _value(packs, "occurrence.rule-kind", rule_kind, f"{context}.rule_kind")
        condition_logic = _string(item, "condition_logic", context)
        _value(packs, "occurrence.rule-condition-logic", condition_logic, f"{context}.condition_logic")
        conditions: list[RecurrenceRuleCondition] = []
        for condition_index, raw_condition in enumerate(_list(item.get("conditions"), f"{context}.conditions")):
            condition_context = f"{context}.conditions[{condition_index}]"
            condition = _mapping(raw_condition, condition_context)
            assert_allowed_keys(condition, {"id", "condition_kind", "target_type", "target_id", "expected_value"}, condition_context)
            condition_id = _stable(_string(condition, "id", condition_context), f"{condition_context}.id")
            if condition_id in nested_rule_ids:
                raise ValueError(f"{condition_context}.id duplicates `{condition_id}`.")
            nested_rule_ids.add(condition_id)
            condition_kind = _string(condition, "condition_kind", condition_context)
            _value(packs, "occurrence.rule-condition-kind", condition_kind, f"{condition_context}.condition_kind")
            target_type = _stable(_string(condition, "target_type", condition_context), f"{condition_context}.target_type")
            target_id = _stable(_string(condition, "target_id", condition_context), f"{condition_context}.target_id")
            expected = _string(condition, "expected_value", condition_context)
            _validate_rule_condition(
                packs, condition_kind, target_type, target_id, expected, templates, recurrence_patterns,
                branches, recurrences, iterations, occurrences, tracks, outcomes, rule_ids, state_ids,
                payload_targets, condition_context,
            )
            conditions.append(RecurrenceRuleCondition(condition_id, condition_kind, target_type, target_id, expected))
        if not conditions:
            raise ValueError(f"{context}.conditions must be a non-empty list.")
        effects: list[RecurrenceRuleEffect] = []
        for effect_index, raw_effect in enumerate(_list(item.get("effects"), f"{context}.effects")):
            effect_context = f"{context}.effects[{effect_index}]"
            effect = _mapping(raw_effect, effect_context)
            assert_allowed_keys(effect, {"id", "effect_kind", "target_type", "target_id"}, effect_context)
            effect_id = _stable(_string(effect, "id", effect_context), f"{effect_context}.id")
            if effect_id in nested_rule_ids:
                raise ValueError(f"{effect_context}.id duplicates `{effect_id}`.")
            nested_rule_ids.add(effect_id)
            effect_kind = _string(effect, "effect_kind", effect_context)
            _value(packs, "occurrence.rule-effect-kind", effect_kind, f"{effect_context}.effect_kind")
            target_type = _stable(_string(effect, "target_type", effect_context), f"{effect_context}.target_type")
            target_id = _stable(_string(effect, "target_id", effect_context), f"{effect_context}.target_id")
            _value(
                packs,
                "occurrence.rule-effect-kind-target-type",
                f"{effect_kind}-uses-{target_type}",
                f"{effect_context}.effect_kind/target_type",
            )
            if target_id not in _target_ids(
                target_type, branches, templates, recurrence_patterns, recurrences, iterations,
                occurrences, tracks, {item.id: item for item in outcomes}, rule_ids, state_ids, payload_targets,
            ):
                raise ValueError(f"{effect_context} references unknown target `{target_type}:{target_id}`.")
            effects.append(RecurrenceRuleEffect(effect_id, effect_kind, target_type, target_id))
        if not effects:
            raise ValueError(f"{context}.effects must be a non-empty list.")
        semantic_key = (
            pattern_id, rule_kind, condition_logic,
            tuple(sorted((item.condition_kind, item.target_type, item.target_id, item.expected_value) for item in conditions)),
            tuple(sorted((item.effect_kind, item.target_type, item.target_id) for item in effects)),
        )
        if semantic_key in rule_semantics:
            raise ValueError(f"{context} duplicates an existing semantic recurrence rule.")
        rule_semantics.add(semantic_key)
        rules.append(RecurrenceRule(
            rule_id, _string(item, "label", context), pattern_id, rule_kind,
            condition_logic, tuple(conditions), tuple(effects),
        ))

    states: list[StateTransition] = []
    state_source_ids: set[str] = set()
    state_semantics: set[tuple] = set()
    outcome_map = {item.id: item for item in outcomes}
    rule_map = {item.id: item for item in rules}
    for index, raw in enumerate(raw_states):
        context = f"state_transitions[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id", "subject_type", "subject_id", "payload_target_type", "payload_target_id",
                "state_kind", "change_kind", "change_profile", "mechanism", "prior_availability",
                "resulting_availability", "prior_attitude", "resulting_attitude", "completeness",
                "activation_occurrence_id", "condition_rule_id", "track_ids", "source_targets", "certainty",
            },
            context,
        )
        state_id = _stable(_string(item, "id", context), f"{context}.id")
        if state_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{state_id}`.")
        seen_ids.add(state_id)
        subject_type = _string(item, "subject_type", context)
        subject_id = _string(item, "subject_id", context)
        _known_external_target(subject_targets, subject_type, subject_id, f"{context}.subject")
        payload_type = _stable(_string(item, "payload_target_type", context), f"{context}.payload_target_type")
        payload_id = _stable(_string(item, "payload_target_id", context), f"{context}.payload_target_id")
        if payload_id not in _target_ids(
            payload_type, branches, templates, recurrence_patterns, recurrences, iterations,
            occurrences, tracks, outcome_map, rule_map, state_ids, payload_targets,
        ):
            raise ValueError(f"{context} references unknown payload `{payload_type}:{payload_id}`.")
        state_kind = _string(item, "state_kind", context)
        _value(packs, "state.state-kind", state_kind, f"{context}.state_kind")
        change_kind = _string(item, "change_kind", context)
        _value(packs, "state.change-kind", change_kind, f"{context}.change_kind")
        change_profile = _string(item, "change_profile", context)
        _value(packs, "state.change-profile", change_profile, f"{context}.change_profile")
        _value(packs, "state.change-kind-profile", f"{change_kind}-uses-{change_profile}", f"{context}.change_kind/change_profile")
        mechanism = _string(item, "mechanism", context)
        _value(packs, "state.mechanism", mechanism, f"{context}.mechanism")
        prior = _string(item, "prior_availability", context)
        resulting = _string(item, "resulting_availability", context)
        _value(packs, "state.availability-status", prior, f"{context}.prior_availability")
        _value(packs, "state.availability-status", resulting, f"{context}.resulting_availability")
        _validate_state_profile(change_profile, prior, resulting, context)
        prior_attitude = _optional_string(item, "prior_attitude", context)
        resulting_attitude = _optional_string(item, "resulting_attitude", context)
        if (prior_attitude is None) != (resulting_attitude is None):
            raise ValueError(f"{context} must set both epistemic attitudes, or neither.")
        if prior_attitude is not None:
            _value(packs, "state.epistemic-attitude", prior_attitude, f"{context}.prior_attitude")
            _value(packs, "state.epistemic-attitude", resulting_attitude, f"{context}.resulting_attitude")
        completeness = _string(item, "completeness", context)
        _value(packs, "state.completeness", completeness, f"{context}.completeness")
        activation_id = _string(item, "activation_occurrence_id", context)
        if activation_id not in occurrences:
            raise ValueError(f"{context}.activation_occurrence_id references unknown occurrence `{activation_id}`.")
        condition_rule_id = _optional_string(item, "condition_rule_id", context)
        if condition_rule_id is not None and condition_rule_id not in rule_map:
            raise ValueError(f"{context}.condition_rule_id references unknown rule `{condition_rule_id}`.")
        track_ids = _strings(item, "track_ids", context)
        if not track_ids:
            raise ValueError(f"{context}.track_ids must be a non-empty list.")
        for track_id in track_ids:
            if track_id not in tracks:
                raise ValueError(f"{context}.track_ids references unknown track `{track_id}`.")
            track = tracks[track_id]
            if (track.subject_type, track.subject_id) != (subject_type, subject_id):
                raise ValueError(f"{context} subject must match track `{track_id}` subject.")
            if activation_id not in track.occurrence_ids:
                raise ValueError(f"{context}.activation_occurrence_id must appear on track `{track_id}`.")
        source_records: list[StateSourceTarget] = []
        for source_index, raw_source in enumerate(_list(item.get("source_targets"), f"{context}.source_targets")):
            source_context = f"{context}.source_targets[{source_index}]"
            source = _mapping(raw_source, source_context)
            assert_allowed_keys(source, {"id", "target_type", "target_id", "role"}, source_context)
            source_id = _stable(_string(source, "id", source_context), f"{source_context}.id")
            if source_id in state_source_ids:
                raise ValueError(f"{source_context}.id duplicates `{source_id}`.")
            state_source_ids.add(source_id)
            source_type = _stable(_string(source, "target_type", source_context), f"{source_context}.target_type")
            source_target_id = _stable(_string(source, "target_id", source_context), f"{source_context}.target_id")
            if source_target_id not in _target_ids(
                source_type, branches, templates, recurrence_patterns, recurrences, iterations,
                occurrences, tracks, outcome_map, rule_map, state_ids, payload_targets,
            ):
                raise ValueError(f"{source_context} references unknown target `{source_type}:{source_target_id}`.")
            role = _string(source, "role", source_context)
            _value(packs, "state.source-role", role, f"{source_context}.role")
            source_records.append(StateSourceTarget(source_id, source_type, source_target_id, role))
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        semantic_key = (
            subject_type, subject_id, payload_type, payload_id, state_kind, change_kind, change_profile,
            mechanism, prior, resulting, prior_attitude, resulting_attitude, completeness, activation_id,
            condition_rule_id, tuple(sorted(track_ids)),
        )
        if semantic_key in state_semantics:
            raise ValueError(f"{context} duplicates an existing semantic state transition.")
        state_semantics.add(semantic_key)
        states.append(StateTransition(
            state_id, subject_type, subject_id, payload_type, payload_id, state_kind, change_kind,
            change_profile, mechanism, prior, resulting, prior_attitude, resulting_attitude,
            completeness, activation_id, condition_rule_id, track_ids, tuple(source_records), certainty,
        ))
    state_map = {item.id: item for item in states}
    _validate_state_chains(states, tracks)

    carryovers: list[IterationCarryover] = []
    carryover_semantics: set[tuple[str, str, str, str]] = set()
    for index, raw in enumerate(_list(root.get("carryovers"), "occurrences.carryovers")):
        context = f"carryovers[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"id", "source_iteration_id", "target_iteration_id", "track_id", "state_transition_id", "certainty"}, context)
        carryover_id = _stable(_string(item, "id", context), f"{context}.id")
        if carryover_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{carryover_id}`.")
        seen_ids.add(carryover_id)
        source_id = _string(item, "source_iteration_id", context)
        target_id = _string(item, "target_iteration_id", context)
        track_id = _string(item, "track_id", context)
        state_id = _string(item, "state_transition_id", context)
        if source_id not in iterations or target_id not in iterations or track_id not in tracks or state_id not in state_map:
            raise ValueError(f"{context} must reference known source/target iterations, track, and state transition.")
        source = iterations[source_id]
        target = iterations[target_id]
        if source.recurrence_id != target.recurrence_id or source.ordinal >= target.ordinal:
            raise ValueError(f"{context} must advance between iterations of the same recurrence.")
        track = tracks[track_id]
        track_iteration_ids = {occurrences[occurrence_id].iteration_id for occurrence_id in track.occurrence_ids}
        if source_id not in track_iteration_ids or target_id not in track_iteration_ids:
            raise ValueError(f"{context}.track_id must participate in both source and target iterations.")
        state = state_map[state_id]
        if track_id not in state.track_ids:
            raise ValueError(f"{context}.state_transition_id must apply to track `{track_id}`.")
        _validate_carryover_state_window(state, source_id, target_id, track, states, occurrences, context)
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        semantic_key = (source_id, target_id, track_id, state_id)
        if semantic_key in carryover_semantics:
            raise ValueError(f"{context} duplicates an existing semantic carryover.")
        carryover_semantics.add(semantic_key)
        carryovers.append(IterationCarryover(carryover_id, source_id, target_id, track_id, state_id, certainty))

    return OccurrenceRegistry(
        path, SUPPORTED_SCHEMA_VERSION, branches, templates, recurrence_patterns, recurrences,
        iterations, occurrences, tracks, tuple(transitions), tuple(causal_relations), tuple(outcomes),
        tuple(rules), tuple(states), tuple(carryovers),
    )


def _validate_transition_profile(
    transition: OccurrenceTransition,
    occurrences: dict[str, Occurrence],
    iterations: dict[str, RecurrenceIteration],
    recurrences: dict[str, Recurrence],
    branches: dict[str, OccurrenceBranch],
    chronology: ChronologyRegistry,
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
        if transition.transition_profile == "ordered":
            ordered_evidence = bool(transition.track_ids)
            if (
                source_iteration is not None
                and target_iteration is not None
                and source_iteration.recurrence_id == target_iteration.recurrence_id
            ):
                if source_iteration.ordinal > target_iteration.ordinal:
                    raise ValueError(f"{context} ordered transition moves backward across recurrence iterations.")
                ordered_evidence = ordered_evidence or source_iteration.ordinal < target_iteration.ordinal
            comparisons = {
                chronology.compare_positions(source.position_id, target.position_id)
                for source in source_occurrence.bindings if source.role == "primary"
                for target in target_occurrence.bindings if target.role == "primary"
            }
            if "after" in comparisons:
                raise ValueError(f"{context} ordered transition contradicts exact chronology position order.")
            ordered_evidence = ordered_evidence or "before" in comparisons
            if not ordered_evidence:
                raise ValueError(f"{context} ordered transition requires a forward track, iteration, or chronology order.")
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
        if (
            source_iteration is None
            or recurrence_id is None
            or not _recurrence_within(source_iteration.recurrence_id, recurrence_id, recurrences)
        ):
            raise ValueError(f"{context} recurrence-exit source must belong to recurrence `{recurrence_id}`.")
        if (
            target_iteration is not None
            and _recurrence_within(target_iteration.recurrence_id, recurrence_id, recurrences)
        ):
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


def _validate_iteration_lifecycle(
    recurrences: dict[str, Recurrence],
    iterations: dict[str, RecurrenceIteration],
) -> None:
    for recurrence_id, recurrence in recurrences.items():
        members = sorted(
            (item for item in iterations.values() if item.recurrence_id == recurrence_id),
            key=lambda item: item.ordinal,
        )
        active = [item for item in members if item.status == "active"]
        terminated = [item for item in members if item.status == "terminated"]
        if len(active) > 1:
            raise ValueError(f"Recurrence `{recurrence_id}` cannot have more than one active iteration.")
        if len(terminated) > 1:
            raise ValueError(f"Recurrence `{recurrence_id}` cannot have more than one terminated iteration.")
        if active and active[0] is not members[-1]:
            raise ValueError(f"Recurrence `{recurrence_id}` active iteration must have the highest ordinal.")
        if terminated and terminated[0] is not members[-1]:
            raise ValueError(f"Recurrence `{recurrence_id}` terminated iteration must have the highest ordinal.")
        if terminated and recurrence.status != "terminated":
            raise ValueError(f"Recurrence `{recurrence_id}` with a terminated iteration must itself be terminated.")
        if recurrence.status == "terminated" and members and members[-1].status != "terminated":
            raise ValueError(f"Terminated recurrence `{recurrence_id}` must end with a terminated iteration.")
        if recurrence.status == "completed" and (active or terminated):
            raise ValueError(f"Completed recurrence `{recurrence_id}` cannot contain active or terminated iterations.")


def _validate_track_iteration_order(
    tracks: dict[str, OccurrenceTrack],
    occurrences: dict[str, Occurrence],
    iterations: dict[str, RecurrenceIteration],
) -> None:
    for track in tracks.values():
        last_ordinal: dict[str, int] = {}
        for occurrence_id in track.occurrence_ids:
            iteration_id = occurrences[occurrence_id].iteration_id
            if iteration_id is None:
                continue
            iteration = iterations[iteration_id]
            previous = last_ordinal.get(iteration.recurrence_id)
            if previous is not None and iteration.ordinal < previous:
                raise ValueError(
                    f"Track `{track.id}` moves backward from iteration ordinal {previous} "
                    f"to {iteration.ordinal} in recurrence `{iteration.recurrence_id}`."
                )
            last_ordinal[iteration.recurrence_id] = iteration.ordinal


def _recurrence_within(
    recurrence_id: str,
    ancestor_recurrence_id: str,
    recurrences: dict[str, Recurrence],
) -> bool:
    current: str | None = recurrence_id
    while current is not None:
        if current == ancestor_recurrence_id:
            return True
        current = recurrences[current].parent_recurrence_id
    return False


def _precollect_list_ids(rows: list, context: str) -> set[str]:
    result: set[str] = set()
    for index, raw in enumerate(rows):
        item_context = f"{context}[{index}]"
        item = _mapping(raw, item_context)
        item_id = _stable(_string(item, "id", item_context), f"{item_context}.id")
        if item_id in result:
            raise ValueError(f"{item_context}.id duplicates `{item_id}`.")
        result.add(item_id)
    return result


def _known_external_target(
    targets: dict[str, set[str]] | None,
    target_type: str,
    target_id: str,
    context: str,
) -> None:
    _stable(target_type, f"{context}_type")
    _stable(target_id, f"{context}_id")
    if targets is None or target_type not in targets or target_id not in targets[target_type]:
        raise ValueError(f"{context} references unknown target `{target_type}:{target_id}`.")


def _validate_rule_condition(
    packs: SchemaPackRegistry,
    condition_kind: str,
    target_type: str,
    target_id: str,
    expected_value: str,
    templates: dict[str, OccurrenceTemplate],
    recurrence_patterns: dict[str, RecurrencePattern],
    branches: dict[str, OccurrenceBranch],
    recurrences: dict[str, Recurrence],
    iterations: dict[str, RecurrenceIteration],
    occurrences: dict[str, Occurrence],
    tracks: dict[str, OccurrenceTrack],
    outcomes: list[OccurrenceOutcome],
    rule_ids: set[str],
    state_ids: set[str],
    external_targets: dict[str, set[str]] | None,
    context: str,
) -> None:
    if condition_kind in {"occurrence-reached", "occurrence-outcome"} and target_type != "occurrence-template":
        raise ValueError(f"{context} condition `{condition_kind}` cannot target `{target_type}`.")
    if target_id not in _target_ids(
        target_type, branches, templates, recurrence_patterns, recurrences, iterations,
        occurrences, tracks, {item.id: item for item in outcomes}, rule_ids, state_ids,
        external_targets,
    ):
        raise ValueError(f"{context} references unknown target `{target_type}:{target_id}`.")
    if condition_kind == "occurrence-reached":
        _value(packs, "occurrence.rule-condition-value", expected_value, f"{context}.expected_value")
    elif condition_kind == "occurrence-outcome":
        _value(packs, "occurrence.outcome-kind", expected_value, f"{context}.expected_value")
    else:
        _value(packs, "state.availability-status", expected_value, f"{context}.expected_value")


def _validate_state_profile(profile: str, prior: str, resulting: str, context: str) -> None:
    valid = {
        "acquire": prior in {"unavailable", "latent"} and resulting in {"partial", "available"},
        "preserve": prior == resulting,
        "remove": resulting in {"unavailable", "inaccessible"},
        "restore": prior in {"unavailable", "inaccessible"} and resulting in {"partial", "available"},
        "supply": resulting in {"partial", "available"},
        "combine": resulting in {"partial", "available"},
        "derive": resulting in {"partial", "available"},
        "activate": prior in {"latent", "inaccessible"} and resulting in {"partial", "available"},
        "invalidate": resulting == "invalidated",
    }
    if not valid.get(profile, False):
        raise ValueError(
            f"{context} state profile `{profile}` is incompatible with availability "
            f"transition `{prior}` -> `{resulting}`."
        )


def _validate_state_chains(
    states: list[StateTransition],
    tracks: dict[str, OccurrenceTrack],
) -> None:
    chains: dict[tuple[str, str, str, str, str, str], list[StateTransition]] = {}
    for state in states:
        for track_id in state.track_ids:
            key = (
                track_id, state.subject_type, state.subject_id,
                state.payload_target_type, state.payload_target_id, state.state_kind,
            )
            chains.setdefault(key, []).append(state)
    for key, members in chains.items():
        track = tracks[key[0]]
        members.sort(key=lambda item: track.occurrence_ids.index(item.activation_occurrence_id))
        activation_ids = [item.activation_occurrence_id for item in members]
        if len(activation_ids) != len(set(activation_ids)):
            raise ValueError(f"State chain on track `{track.id}` has multiple transitions at one occurrence.")
        for previous, current in zip(members, members[1:]):
            if previous.resulting_availability != current.prior_availability:
                raise ValueError(
                    f"State transition `{current.id}` prior availability does not continue "
                    f"state transition `{previous.id}`."
                )
            if previous.resulting_attitude != current.prior_attitude:
                raise ValueError(
                    f"State transition `{current.id}` prior attitude does not continue "
                    f"state transition `{previous.id}`."
                )


def _validate_carryover_state_window(
    state: StateTransition,
    source_iteration_id: str,
    target_iteration_id: str,
    track: OccurrenceTrack,
    states: list[StateTransition],
    occurrences: dict[str, Occurrence],
    context: str,
) -> None:
    indices = {occurrence_id: index for index, occurrence_id in enumerate(track.occurrence_ids)}
    source_indices = [
        indices[item] for item in track.occurrence_ids
        if occurrences[item].iteration_id == source_iteration_id
    ]
    target_indices = [
        indices[item] for item in track.occurrence_ids
        if occurrences[item].iteration_id == target_iteration_id
    ]
    activation_index = indices[state.activation_occurrence_id]
    if activation_index > max(source_indices):
        raise ValueError(f"{context}.state_transition_id activates after the source iteration ends.")
    chain_key = (
        state.subject_type, state.subject_id, state.payload_target_type,
        state.payload_target_id, state.state_kind,
    )
    for candidate in states:
        if candidate.id == state.id or track.id not in candidate.track_ids:
            continue
        candidate_key = (
            candidate.subject_type, candidate.subject_id, candidate.payload_target_type,
            candidate.payload_target_id, candidate.state_kind,
        )
        candidate_index = indices[candidate.activation_occurrence_id]
        if chain_key == candidate_key and activation_index < candidate_index < min(target_indices):
            raise ValueError(
                f"{context}.state_transition_id is superseded by `{candidate.id}` before the target iteration begins."
            )


def _target_ids(
    target_type: str,
    branches: dict[str, OccurrenceBranch],
    templates: dict[str, OccurrenceTemplate],
    recurrence_patterns: dict[str, RecurrencePattern],
    recurrences: dict[str, Recurrence],
    iterations: dict[str, RecurrenceIteration],
    occurrences: dict[str, Occurrence],
    tracks: dict[str, OccurrenceTrack],
    outcomes: dict[str, OccurrenceOutcome] | set[str],
    rules: dict[str, RecurrenceRule] | set[str],
    states: dict[str, StateTransition] | set[str],
    external_targets: dict[str, set[str]] | None,
) -> set[str]:
    internal_targets = {
        "occurrence-branch": set(branches),
        "occurrence-template": set(templates),
        "recurrence-pattern": set(recurrence_patterns),
        "recurrence": set(recurrences),
        "recurrence-iteration": set(iterations),
        "occurrence": set(occurrences),
        "occurrence-track": set(tracks),
        "occurrence-outcome": set(outcomes),
        "recurrence-rule": set(rules),
        "state-transition": set(states),
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
