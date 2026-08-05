from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import re

from .chronology_config import ChronologyRegistry
from .project_config import ProjectConfig
from .schema_pack_config import SchemaPackRegistry
from .strict_yaml import assert_allowed_keys, load_yaml_file
from .temporal_config import TemporalWindow, normalize_effective_at, parse_temporal_window, temporal_window_match


SUPPORTED_SCHEMA_VERSION = 9
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class OccurrenceBranch:
    id: str
    label: str
    parent_branch_id: str | None
    fork_occurrence_id: str | None
    continuity_ids: tuple[str, ...]


@dataclass(frozen=True)
class BranchStateTransition:
    id: str
    label: str
    branch_id: str
    ordinal: int
    change_kind: str
    prior_state: str | None
    resulting_state: str
    activation_occurrence_id: str
    trigger_transition_id: str | None
    certainty: str


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
class RecurrenceCardinality:
    id: str
    label: str
    recurrence_id: str
    cardinality_kind: str
    minimum_count: int | None
    maximum_count: int | None
    coverage_mode: str
    representative_iteration_ids: tuple[str, ...]
    certainty: str


@dataclass(frozen=True)
class RecurrencePhase:
    id: str
    label: str
    recurrence_id: str
    start_ordinal: int
    end_ordinal: int | None


@dataclass(frozen=True)
class RecurrenceSchedule:
    id: str
    label: str
    pattern_id: str
    schedule_kind: str
    interval: int
    unit: str
    anchor_position_id: str | None
    anchor_value: str | None


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
# TODO (OWNER): Implement V46 many-to-many chronology bindings for each participation.
#   Migration target: preserve or translate the legacy singular chronology_context_id
#   field in the paired Python and PowerShell loaders.
class OccurrenceParticipation:
    id: str
    occurrence_id: str
    subject_type: str
    subject_id: str
    role: str
    perspective: str
    status: str
    chronology_context_id: str | None


@dataclass(frozen=True)
class OccurrenceTrackEntry:
    id: str
    track_id: str
    participation_id: str
    ordinal: int


@dataclass(frozen=True)
class OccurrenceTrack:
    id: str
    label: str
    kind: str
    subject_type: str
    subject_id: str
    entry_ids: tuple[str, ...]
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
    subject_type: str | None
    subject_id: str | None
    state_kind: str | None
    track_id: str | None
    comparison_value: int | None


@dataclass(frozen=True)
class ChronologyApplicabilityWindow:
    start_position_id: str | None
    end_position_id: str | None


@dataclass(frozen=True)
class RuleApplicability:
    application_level: str
    recurrence_ids: tuple[str, ...]
    phase_ids: tuple[str, ...]
    branch_ids: tuple[str, ...]
    min_iteration_ordinal: int | None
    max_iteration_ordinal: int | None
    chronology_window: ChronologyApplicabilityWindow | None
    effective_window: TemporalWindow | None


@dataclass(frozen=True)
class RecurrenceRuleEffect:
    id: str
    effect_kind: str
    target_type: str
    target_id: str


@dataclass(frozen=True)
class ResolvedRuleEffect:
    effect_kind: str
    target_type: str
    target_id: str
    repetition_policy: str
    contribution_count: int
    proposed_execution_count: int
    contributing_rule_ids: tuple[str, ...]
    contributing_effect_ids: tuple[str, ...]


@dataclass(frozen=True)
class RecurrenceRule:
    id: str
    label: str
    pattern_id: str
    rule_kind: str
    condition_logic: str
    applicability: RuleApplicability
    priority: int
    resolution_group: str
    selection_mode: str
    override_mode: str
    conditions: tuple[RecurrenceRuleCondition, ...]
    effects: tuple[RecurrenceRuleEffect, ...]


@dataclass(frozen=True)
class RuleConditionEvaluation:
    condition_id: str
    status: str
    detail: str


@dataclass(frozen=True)
class RuleEvaluationTrace:
    rule_id: str
    applicability: str
    matched: bool
    selected: bool
    disposition: str
    conditions: tuple[RuleConditionEvaluation, ...]


@dataclass(frozen=True)
class RuleEvaluation:
    status: str
    recurrence_id: str
    occurrence_id: str
    selected_rule_ids: tuple[str, ...]
    proposed_effects: tuple[ResolvedRuleEffect, ...]
    authorized_effects: tuple[ResolvedRuleEffect, ...]
    execution_disposition: str
    conflicts: tuple[str, ...]
    traces: tuple[RuleEvaluationTrace, ...]


@dataclass(frozen=True)
class StateSourceTarget:
    id: str
    target_type: str
    target_id: str
    role: str


@dataclass(frozen=True)
class StateScaleLevel:
    id: str
    ordinal: int


@dataclass(frozen=True)
class StateScale:
    id: str
    kind: str
    levels: tuple[StateScaleLevel, ...]
    minimum: int | None
    maximum: int | None
    unit: str | None


@dataclass(frozen=True)
class CapabilityValue:
    scale_id: str
    value: str | int


@dataclass(frozen=True)
class StateTransition:
    id: str
    subject_type: str
    subject_id: str
    payload_target_type: str
    payload_target_id: str
    state_kind: str
    state_profile: str
    change_kind: str
    change_profile: str
    change_shape: str
    mechanism: str
    prior_availability: str
    resulting_availability: str
    prior_attitude: str | None
    resulting_attitude: str | None
    prior_completeness: str | None
    resulting_completeness: str | None
    prior_capability: CapabilityValue | None
    resulting_capability: CapabilityValue | None
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
    chronology: ChronologyRegistry
    branches: dict[str, OccurrenceBranch]
    branch_state_transitions: tuple[BranchStateTransition, ...]
    templates: dict[str, OccurrenceTemplate]
    recurrence_patterns: dict[str, RecurrencePattern]
    recurrences: dict[str, Recurrence]
    iterations: dict[str, RecurrenceIteration]
    recurrence_cardinalities: dict[str, RecurrenceCardinality]
    phases: dict[str, RecurrencePhase]
    schedules: dict[str, RecurrenceSchedule]
    occurrences: dict[str, Occurrence]
    occurrence_participations: dict[str, OccurrenceParticipation]
    tracks: dict[str, OccurrenceTrack]
    track_entries: dict[str, OccurrenceTrackEntry]
    transitions: tuple[OccurrenceTransition, ...]
    causal_relations: tuple[CausalRelation, ...]
    outcomes: tuple[OccurrenceOutcome, ...]
    rules: tuple[RecurrenceRule, ...]
    state_scales: dict[str, StateScale]
    state_transitions: tuple[StateTransition, ...]
    carryovers: tuple[IterationCarryover, ...]
    effect_global_incompatibility_pairs: frozenset[tuple[str, str]]
    effect_same_target_incompatibility_pairs: frozenset[tuple[str, str]]
    effect_repetition_policies: dict[str, str]

    def branch_state_history(self, branch_id: str) -> tuple[BranchStateTransition, ...]:
        self._known(self.branches, branch_id, "branch")
        return tuple(item for item in self.branch_state_transitions if item.branch_id == branch_id)

    def branch_state_at(self, branch_id: str, through_ordinal: int | None = None) -> BranchStateTransition | None:
        history = self.branch_state_history(branch_id)
        if through_ordinal is None:
            return history[-1] if history else None
        if isinstance(through_ordinal, bool) or not isinstance(through_ordinal, int) or through_ordinal < 0:
            raise ValueError("Branch-state boundary ordinal must be a nonnegative integer.")
        candidates = tuple(item for item in history if item.ordinal <= through_ordinal)
        return candidates[-1] if candidates else None

    def validate_branch_continuity_targets(self, continuity_ids: set[str]) -> None:
        for branch in self.branches.values():
            unknown = set(branch.continuity_ids) - continuity_ids
            if unknown:
                raise ValueError(
                    f"branches.{branch.id}.continuity_ids references unknown continuities: {sorted(unknown)}."
                )

    def occurrences_for_iteration(self, iteration_id: str) -> tuple[Occurrence, ...]:
        self._known(self.iterations, iteration_id, "iteration")
        return tuple(item for item in self.occurrences.values() if item.iteration_id == iteration_id)

    def cardinalities_for_recurrence(self, recurrence_id: str) -> tuple[RecurrenceCardinality, ...]:
        self._known(self.recurrences, recurrence_id, "recurrence")
        return tuple(
            sorted(
                (item for item in self.recurrence_cardinalities.values() if item.recurrence_id == recurrence_id),
                key=lambda item: item.id,
            )
        )

    def occurrences_at_position(self, position_id: str) -> tuple[Occurrence, ...]:
        return tuple(
            item
            for item in self.occurrences.values()
            if any(binding.position_id == position_id for binding in item.bindings)
        )

    def participations_for_occurrence(self, occurrence_id: str) -> tuple[OccurrenceParticipation, ...]:
        self._known(self.occurrences, occurrence_id, "occurrence")
        return tuple(item for item in self.occurrence_participations.values() if item.occurrence_id == occurrence_id)

    def participations_for_subject(self, subject_type: str, subject_id: str) -> tuple[OccurrenceParticipation, ...]:
        return tuple(
            item
            for item in self.occurrence_participations.values()
            if item.subject_type == subject_type and item.subject_id == subject_id
        )

    def entries_for_occurrence_on_track(self, track_id: str, occurrence_id: str) -> tuple[OccurrenceTrackEntry, ...]:
        track = self._known(self.tracks, track_id, "track")
        self._known(self.occurrences, occurrence_id, "occurrence")
        return tuple(
            self.track_entries[entry_id]
            for entry_id in track.entry_ids
            if self.occurrence_participations[self.track_entries[entry_id].participation_id].occurrence_id
            == occurrence_id
        )

    def previous_track_entry(self, track_id: str, entry_id: str) -> OccurrenceTrackEntry | None:
        return self._adjacent_track_entry(track_id, entry_id, -1)

    def next_track_entry(self, track_id: str, entry_id: str) -> OccurrenceTrackEntry | None:
        return self._adjacent_track_entry(track_id, entry_id, 1)

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

    def phase_for_iteration(self, iteration_id: str) -> RecurrencePhase | None:
        iteration = self._known(self.iterations, iteration_id, "iteration")
        matches = [
            item
            for item in self.phases.values()
            if item.recurrence_id == iteration.recurrence_id
            and item.start_ordinal <= iteration.ordinal
            and (item.end_ordinal is None or iteration.ordinal <= item.end_ordinal)
        ]
        return matches[0] if matches else None

    def expected_schedule_value(self, schedule_id: str, iteration_ordinal: int) -> str | int:
        schedule = self._known(self.schedules, schedule_id, "recurrence schedule")
        if iteration_ordinal < 1:
            raise ValueError("Schedule iteration ordinal must be positive.")
        offset = (iteration_ordinal - 1) * schedule.interval
        if schedule.schedule_kind == "chronology-step":
            anchor = self.chronology.positions[schedule.anchor_position_id]
            system = self.chronology.coordinate_systems[anchor.coordinate_system_id]
            return anchor.value + offset if system.direction == "ascending" else anchor.value - offset
        return _add_civil_interval(schedule.anchor_value, schedule.unit, offset)

    def schedule_match(
        self,
        schedule_id: str,
        iteration_id: str,
        occurrence_id: str,
        effective_at: str | None = None,
    ) -> str:
        schedule = self._known(self.schedules, schedule_id, "recurrence schedule")
        iteration = self._known(self.iterations, iteration_id, "iteration")
        occurrence = self._known(self.occurrences, occurrence_id, "occurrence")
        if self.recurrences[iteration.recurrence_id].pattern_id != schedule.pattern_id:
            raise ValueError(f"Schedule `{schedule_id}` does not apply to iteration `{iteration_id}`.")
        expected = self.expected_schedule_value(schedule_id, iteration.ordinal)
        if schedule.schedule_kind == "civil-calendar":
            if effective_at is None:
                return "indeterminate"
            _, label = normalize_effective_at(effective_at)
            return "due" if label == expected else "off-schedule"
        anchor = self.chronology.positions[schedule.anchor_position_id]
        primary = [binding for binding in occurrence.bindings if binding.role == "primary"]
        candidates = [
            self.chronology.positions[binding.position_id]
            for binding in primary
            if self.chronology.positions[binding.position_id].coordinate_system_id == anchor.coordinate_system_id
        ]
        if not candidates:
            return "indeterminate"
        return (
            "due"
            if any(item.value == expected and item.era_id == anchor.era_id for item in candidates)
            else "off-schedule"
        )

    def evaluate_rules(
        self,
        recurrence_id: str,
        occurrence_id: str,
        *,
        effective_at: str | None = None,
    ) -> RuleEvaluation:
        return _evaluate_rules(self, recurrence_id, occurrence_id, effective_at)

    def state_transitions_for_subject(self, subject_type: str, subject_id: str) -> tuple[StateTransition, ...]:
        return tuple(
            item
            for item in self.state_transitions
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
        indices = [index for index, item in enumerate(track.occurrence_ids) if item == occurrence_id]
        if not indices:
            raise ValueError(f"Occurrence `{occurrence_id}` is not on track `{track_id}`.")
        if len(indices) > 1:
            raise ValueError(
                f"Occurrence `{occurrence_id}` appears more than once on track `{track_id}`; "
                "a participation-relative state query is required."
            )
        boundary = indices[0]
        candidates = [
            item
            for item in self.state_transitions
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
            "occurrence-branch-state-transition": {item.id: item for item in self.branch_state_transitions},
            "occurrence-template": self.templates,
            "recurrence-pattern": self.recurrence_patterns,
            "recurrence": self.recurrences,
            "recurrence-iteration": self.iterations,
            "recurrence-cardinality": self.recurrence_cardinalities,
            "recurrence-phase": self.phases,
            "recurrence-schedule": self.schedules,
            "occurrence": self.occurrences,
            "occurrence-participation": self.occurrence_participations,
            "occurrence-binding": {
                binding.id: binding for occurrence in self.occurrences.values() for binding in occurrence.bindings
            },
            "occurrence-track": self.tracks,
            "occurrence-track-entry": self.track_entries,
            "occurrence-transition": {item.id: item for item in self.transitions},
            "causal-relation": {item.id: item for item in self.causal_relations},
            "occurrence-outcome": {item.id: item for item in self.outcomes},
            "recurrence-rule": {item.id: item for item in self.rules},
            "state-scale": self.state_scales,
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
        indices = [index for index, item in enumerate(track.occurrence_ids) if item == occurrence_id]
        if not indices:
            raise ValueError(f"Occurrence `{occurrence_id}` is not on track `{track_id}`.")
        if len(indices) > 1:
            raise ValueError(
                f"Occurrence `{occurrence_id}` appears more than once on track `{track_id}`; "
                "use track-entry navigation."
            )
        index = indices[0] + offset
        if index < 0 or index >= len(track.occurrence_ids):
            return None
        return self.occurrences[track.occurrence_ids[index]]

    def _adjacent_track_entry(self, track_id: str, entry_id: str, offset: int) -> OccurrenceTrackEntry | None:
        track = self._known(self.tracks, track_id, "track")
        entry = self._known(self.track_entries, entry_id, "track entry")
        if entry.track_id != track_id:
            raise ValueError(f"Track entry `{entry_id}` does not belong to track `{track_id}`.")
        index = track.entry_ids.index(entry_id) + offset
        if index < 0 or index >= len(track.entry_ids):
            return None
        return self.track_entries[track.entry_ids[index]]

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


def _optional_nonnegative_int(item: dict, key: str, context: str) -> int | None:
    value = item.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{context}.{key} must be a nonnegative integer or null.")
    return value


def _optional_nonnegative_count(item: dict, key: str, context: str) -> int | None:
    value = item.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 9_223_372_036_854_775_807:
        raise ValueError(f"{context}.{key} must be a nonnegative signed 64-bit integer or null.")
    return value


def _signed_64_int(item: dict, key: str, context: str) -> int:
    value = item.get(key)
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < -9_223_372_036_854_775_808
        or value > 9_223_372_036_854_775_807
    ):
        raise ValueError(f"{context}.{key} must be a signed 64-bit integer.")
    return value


def _positive_int(item: dict, key: str, context: str) -> int:
    value = item.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{context}.{key} must be a positive integer.")
    return value


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
    if not packs.capability_enabled("deterministic-recurrence-rule-evaluation"):
        raise ValueError("Occurrence registry requires enabled capability `deterministic-recurrence-rule-evaluation`.")
    if not packs.capability_enabled("recurrence-schedule-modeling"):
        raise ValueError("Occurrence registry requires enabled capability `recurrence-schedule-modeling`.")
    if not packs.capability_enabled("recurrence-policy-integrity"):
        raise ValueError("Occurrence registry requires enabled capability `recurrence-policy-integrity`.")
    if not packs.capability_enabled("extensible-recurrence-policy-semantics"):
        raise ValueError("Occurrence registry requires enabled capability `extensible-recurrence-policy-semantics`.")
    if not packs.capability_enabled("civil-schedule-boundary-integrity"):
        raise ValueError("Occurrence registry requires enabled capability `civil-schedule-boundary-integrity`.")
    if not packs.capability_enabled("semantic-declaration-integrity"):
        raise ValueError("Occurrence registry requires enabled capability `semantic-declaration-integrity`.")
    if not packs.capability_enabled("deterministic-effect-resolution"):
        raise ValueError("Occurrence registry requires enabled capability `deterministic-effect-resolution`.")
    if not packs.capability_enabled("aggregate-recurrence-cardinality"):
        raise ValueError("Occurrence registry requires enabled capability `aggregate-recurrence-cardinality`.")
    if not packs.capability_enabled("occurrence-participation-identity"):
        raise ValueError("Occurrence registry requires enabled capability `occurrence-participation-identity`.")
    if not packs.capability_enabled("timeline-branch-lifecycle"):
        raise ValueError("Occurrence registry requires enabled capability `timeline-branch-lifecycle`.")
    if not packs.capability_enabled("capability-progression"):
        raise ValueError("Occurrence registry requires enabled capability `capability-progression`.")
    root = _mapping(data, "Occurrence registry root")
    assert_allowed_keys(
        root,
        {
            "schema_version",
            "branches",
            "branch_state_transitions",
            "templates",
            "recurrence_patterns",
            "recurrences",
            "iterations",
            "recurrence_cardinalities",
            "phases",
            "schedules",
            "occurrences",
            "occurrence_participations",
            "tracks",
            "track_entries",
            "transitions",
            "causal_relations",
            "outcomes",
            "rules",
            "state_scales",
            "state_transitions",
            "carryovers",
        },
        "Occurrence registry root",
    )
    if root.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported occurrence schema_version {root.get('schema_version')!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION}."
        )

    branches: dict[str, OccurrenceBranch] = {}
    for branch_id, raw in _mapping(root.get("branches"), "occurrences.branches").items():
        _stable(branch_id, "occurrence branch ID")
        context = f"branches.{branch_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "parent_branch_id", "fork_occurrence_id", "continuity_ids"}, context)
        parent_id = _optional_string(item, "parent_branch_id", context)
        fork_id = _optional_string(item, "fork_occurrence_id", context)
        if parent_id is not None:
            _stable(parent_id, f"{context}.parent_branch_id")
        if fork_id is not None:
            _stable(fork_id, f"{context}.fork_occurrence_id")
        if (parent_id is None) != (fork_id is None):
            raise ValueError(f"{context} must set both parent_branch_id and fork_occurrence_id, or neither.")
        branches[branch_id] = OccurrenceBranch(
            branch_id,
            _string(item, "label", context),
            parent_id,
            fork_id,
            _strings(item, "continuity_ids", context),
        )
    if not branches:
        raise ValueError("occurrences.branches cannot be empty.")
    for branch in branches.values():
        if branch.parent_branch_id is not None and branch.parent_branch_id not in branches:
            raise ValueError(
                f"branches.{branch.id}.parent_branch_id references unknown branch `{branch.parent_branch_id}`."
            )
    _acyclic_parent(branches, "parent_branch_id", "Branch")

    templates: dict[str, OccurrenceTemplate] = {}
    for template_id, raw in _mapping(root.get("templates"), "occurrences.templates").items():
        _stable(template_id, "occurrence template ID")
        context = f"templates.{template_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "aliases"}, context)
        kind = _string(item, "kind", context)
        _value(packs, "occurrence.template-kind", kind, f"{context}.kind")
        templates[template_id] = OccurrenceTemplate(
            template_id, _string(item, "label", context), kind, _strings(item, "aliases", context)
        )

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
            raise ValueError(
                f"recurrences.{recurrence.id}.parent_recurrence_id references unknown recurrence "
                f"`{recurrence.parent_recurrence_id}`."
            )
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
        iterations[iteration_id] = RecurrenceIteration(
            iteration_id, recurrence_id, ordinal, _optional_string(item, "parent_iteration_id", context), status
        )
    for iteration in iterations.values():
        parent_recurrence_id = recurrences[iteration.recurrence_id].parent_recurrence_id
        if parent_recurrence_id is None:
            if iteration.parent_iteration_id is not None:
                raise ValueError(
                    f"iterations.{iteration.id}.parent_iteration_id is only valid for a nested recurrence."
                )
        else:
            if iteration.parent_iteration_id not in iterations:
                raise ValueError(
                    f"iterations.{iteration.id}.parent_iteration_id must reference an iteration of "
                    f"parent recurrence `{parent_recurrence_id}`."
                )
            if iterations[iteration.parent_iteration_id].recurrence_id != parent_recurrence_id:
                raise ValueError(
                    f"iterations.{iteration.id}.parent_iteration_id must belong to parent recurrence "
                    f"`{parent_recurrence_id}`."
                )
    _validate_iteration_lifecycle(recurrences, iterations)

    recurrence_cardinalities: dict[str, RecurrenceCardinality] = {}
    cardinality_semantics: set[tuple] = set()
    for cardinality_id, raw in _mapping(
        root.get("recurrence_cardinalities"), "occurrences.recurrence_cardinalities"
    ).items():
        _stable(cardinality_id, "recurrence cardinality ID")
        context = f"recurrence_cardinalities.{cardinality_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "label",
                "recurrence_id",
                "cardinality_kind",
                "minimum_count",
                "maximum_count",
                "coverage_mode",
                "representative_iteration_ids",
                "certainty",
            },
            context,
        )
        recurrence_id = _string(item, "recurrence_id", context)
        if recurrence_id not in recurrences:
            raise ValueError(f"{context}.recurrence_id references unknown recurrence `{recurrence_id}`.")
        kind = _string(item, "cardinality_kind", context)
        coverage = _string(item, "coverage_mode", context)
        _value(packs, "occurrence.cardinality-kind", kind, f"{context}.cardinality_kind")
        _value(packs, "occurrence.cardinality-coverage", coverage, f"{context}.coverage_mode")
        minimum = _optional_nonnegative_count(item, "minimum_count", context)
        maximum = _optional_nonnegative_count(item, "maximum_count", context)
        expected_bounds = {
            "exact": minimum is not None and minimum == maximum,
            "minimum": minimum is not None and maximum is None,
            "maximum": minimum is None and maximum is not None,
            "range": minimum is not None and maximum is not None and minimum < maximum,
            "unknown": minimum is None and maximum is None,
        }
        if not expected_bounds.get(kind, False):
            raise ValueError(f"{context} bounds do not match cardinality_kind `{kind}`.")
        representative_ids = _strings(item, "representative_iteration_ids", context)
        for iteration_id in representative_ids:
            if iteration_id not in iterations or iterations[iteration_id].recurrence_id != recurrence_id:
                raise ValueError(f"{context}.representative_iteration_ids must belong to recurrence `{recurrence_id}`.")
        represented_count = len(representative_ids)
        if maximum is not None and represented_count > maximum:
            raise ValueError(f"{context} represents more concrete iterations than its maximum_count.")
        if coverage == "complete":
            if kind != "exact" or represented_count != minimum:
                raise ValueError(f"{context} complete coverage requires an exact count and full enumeration.")
        elif coverage == "representative":
            if not representative_ids:
                raise ValueError(f"{context} representative coverage requires concrete iteration IDs.")
            if kind == "exact" and represented_count == minimum:
                raise ValueError(f"{context} exact fully enumerated coverage must use `complete`.")
        elif representative_ids:
            raise ValueError(f"{context} unmaterialized coverage cannot reference concrete iterations.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        semantic_key = (recurrence_id, kind, minimum, maximum, coverage, tuple(sorted(representative_ids)), certainty)
        if semantic_key in cardinality_semantics:
            raise ValueError(f"{context} duplicates an existing semantic recurrence cardinality.")
        cardinality_semantics.add(semantic_key)
        recurrence_cardinalities[cardinality_id] = RecurrenceCardinality(
            cardinality_id,
            _string(item, "label", context),
            recurrence_id,
            kind,
            minimum,
            maximum,
            coverage,
            representative_ids,
            certainty,
        )

    phases: dict[str, RecurrencePhase] = {}
    phase_ranges: dict[str, list[tuple[int, int | None, str]]] = {}
    for phase_id, raw in _mapping(root.get("phases"), "occurrences.phases").items():
        _stable(phase_id, "recurrence phase ID")
        context = f"phases.{phase_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "recurrence_id", "start_ordinal", "end_ordinal"}, context)
        recurrence_id = _string(item, "recurrence_id", context)
        if recurrence_id not in recurrences:
            raise ValueError(f"{context}.recurrence_id references unknown recurrence `{recurrence_id}`.")
        start_ordinal = _positive_int(item, "start_ordinal", context)
        end_ordinal = _optional_nonnegative_int(item, "end_ordinal", context)
        if end_ordinal is not None and (end_ordinal < 1 or end_ordinal < start_ordinal):
            raise ValueError(f"{context}.end_ordinal must be null or at least start_ordinal.")
        for prior_start, prior_end, prior_id in phase_ranges.setdefault(recurrence_id, []):
            if _ordinal_ranges_overlap(start_ordinal, end_ordinal, prior_start, prior_end):
                raise ValueError(f"{context} overlaps recurrence phase `{prior_id}`.")
        phase_ranges[recurrence_id].append((start_ordinal, end_ordinal, phase_id))
        phases[phase_id] = RecurrencePhase(
            phase_id, _string(item, "label", context), recurrence_id, start_ordinal, end_ordinal
        )

    schedules: dict[str, RecurrenceSchedule] = {}
    for schedule_id, raw in _mapping(root.get("schedules"), "occurrences.schedules").items():
        _stable(schedule_id, "recurrence schedule ID")
        context = f"schedules.{schedule_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"label", "pattern_id", "schedule_kind", "interval", "unit", "anchor_position_id", "anchor_value"},
            context,
        )
        pattern_id = _string(item, "pattern_id", context)
        if pattern_id not in recurrence_patterns:
            raise ValueError(f"{context}.pattern_id references unknown recurrence pattern `{pattern_id}`.")
        schedule_kind = _string(item, "schedule_kind", context)
        unit = _string(item, "unit", context)
        _value(packs, "occurrence.schedule-kind", schedule_kind, f"{context}.schedule_kind")
        _value(packs, "occurrence.schedule-unit", unit, f"{context}.unit")
        interval = _positive_int(item, "interval", context)
        anchor_position_id = _optional_string(item, "anchor_position_id", context)
        anchor_value = _optional_string(item, "anchor_value", context)
        if schedule_kind == "chronology-step":
            if unit != "coordinate" or anchor_position_id not in chronology.positions or anchor_value is not None:
                raise ValueError(
                    f"{context} chronology-step schedules require unit `coordinate`, a known "
                    "anchor_position_id, and null anchor_value."
                )
            anchor = chronology.positions[anchor_position_id]
            if chronology.coordinate_systems[anchor.coordinate_system_id].kind == "era-ordinal":
                raise ValueError(f"{context} chronology-step schedules do not cross era-ordinal coordinates.")
        else:
            if unit == "coordinate" or anchor_position_id is not None or anchor_value is None:
                raise ValueError(
                    f"{context} civil-calendar schedules require a civil unit, null anchor_position_id, "
                    "and anchor_value."
                )
            _validate_civil_schedule_anchor(anchor_value, unit, context)
        schedules[schedule_id] = RecurrenceSchedule(
            schedule_id,
            _string(item, "label", context),
            pattern_id,
            schedule_kind,
            interval,
            unit,
            anchor_position_id,
            anchor_value,
        )

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
                raise ValueError(
                    f"{binding_context}.position_id references unknown chronology position `{position_id}`."
                )
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
            for right in primary_bindings[left_index + 1 :]:
                comparison = chronology.compare_positions(left.position_id, right.position_id)
                if comparison in {"before", "after"}:
                    raise ValueError(
                        f"{context}.bindings declares ordered chronology positions `{left.position_id}` and "
                        f"`{right.position_id}` as primary coordinates of one occurrence."
                    )
        occurrences[occurrence_id] = Occurrence(
            occurrence_id,
            template_id,
            _optional_string(item, "label", context),
            iteration_id,
            branch_id,
            tuple(bindings),
        )

    for branch in branches.values():
        if branch.fork_occurrence_id is not None and branch.fork_occurrence_id not in occurrences:
            raise ValueError(
                f"branches.{branch.id}.fork_occurrence_id references unknown occurrence `{branch.fork_occurrence_id}`."
            )
        if (
            branch.fork_occurrence_id is not None
            and occurrences[branch.fork_occurrence_id].branch_id != branch.parent_branch_id
        ):
            raise ValueError(
                f"branches.{branch.id}.fork_occurrence_id must belong to parent branch `{branch.parent_branch_id}`."
            )
    occurrence_branch_ids = set(branches)
    for context in chronology.contexts:
        if context.branch_id is not None and context.branch_id not in occurrence_branch_ids:
            raise ValueError(
                f"Chronology context `{context.id}` references unknown occurrence branch `{context.branch_id}`."
            )

    occurrence_participations: dict[str, OccurrenceParticipation] = {}
    participation_semantics: dict[tuple[str, str, str, str, str, str, str | None], list[str]] = {}
    chronology_context_ids = {item.id for item in chronology.contexts}
    for participation_id, raw in _mapping(
        root.get("occurrence_participations"), "occurrences.occurrence_participations"
    ).items():
        _stable(participation_id, "occurrence participation ID")
        context = f"occurrence_participations.{participation_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "occurrence_id",
                "subject_type",
                "subject_id",
                "role",
                "perspective",
                "status",
                "chronology_context_id",
            },
            context,
        )
        occurrence_id = _string(item, "occurrence_id", context)
        if occurrence_id not in occurrences:
            raise ValueError(f"{context}.occurrence_id references unknown occurrence `{occurrence_id}`.")
        subject_type = _string(item, "subject_type", context)
        subject_id = _string(item, "subject_id", context)
        _known_external_target(subject_targets, subject_type, subject_id, f"{context}.subject")
        role = _string(item, "role", context)
        _value(packs, "occurrence.participation-role", role, f"{context}.role")
        perspective = _string(item, "perspective", context)
        _value(packs, "occurrence.participation-perspective", perspective, f"{context}.perspective")
        status = _string(item, "status", context)
        _value(packs, "occurrence.participation-status", status, f"{context}.status")
        chronology_context_id = _optional_string(item, "chronology_context_id", context)
        if chronology_context_id is not None and chronology_context_id not in chronology_context_ids:
            raise ValueError(
                f"{context}.chronology_context_id references unknown chronology context `{chronology_context_id}`."
            )
        semantic_key = (
            occurrence_id,
            subject_type,
            subject_id,
            role,
            perspective,
            status,
            chronology_context_id,
        )
        participation_semantics.setdefault(semantic_key, []).append(participation_id)
        occurrence_participations[participation_id] = OccurrenceParticipation(
            participation_id,
            occurrence_id,
            subject_type,
            subject_id,
            role,
            perspective,
            status,
            chronology_context_id,
        )

    track_metadata: dict[str, tuple[str, str, str, str]] = {}
    for track_id, raw in _mapping(root.get("tracks"), "occurrences.tracks").items():
        _stable(track_id, "occurrence track ID")
        context = f"tracks.{track_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"label", "kind", "subject_type", "subject_id"}, context)
        kind = _string(item, "kind", context)
        _value(packs, "occurrence.track-kind", kind, f"{context}.kind")
        subject_type = _string(item, "subject_type", context)
        subject_id = _string(item, "subject_id", context)
        if (
            subject_targets is None
            or subject_type not in subject_targets
            or subject_id not in subject_targets[subject_type]
        ):
            raise ValueError(f"{context} references unknown subject `{subject_type}:{subject_id}`.")
        track_metadata[track_id] = (_string(item, "label", context), kind, subject_type, subject_id)

    track_entries: dict[str, OccurrenceTrackEntry] = {}
    track_ordinals: set[tuple[str, int]] = set()
    track_participations: set[tuple[str, str]] = set()
    for entry_id, raw in _mapping(root.get("track_entries"), "occurrences.track_entries").items():
        _stable(entry_id, "occurrence track-entry ID")
        context = f"track_entries.{entry_id}"
        item = _mapping(raw, context)
        assert_allowed_keys(item, {"track_id", "participation_id", "ordinal"}, context)
        track_id = _string(item, "track_id", context)
        participation_id = _string(item, "participation_id", context)
        ordinal = _positive_int(item, "ordinal", context)
        if track_id not in track_metadata:
            raise ValueError(f"{context}.track_id references unknown track `{track_id}`.")
        if participation_id not in occurrence_participations:
            raise ValueError(f"{context}.participation_id references unknown participation `{participation_id}`.")
        participation = occurrence_participations[participation_id]
        _, _, track_subject_type, track_subject_id = track_metadata[track_id]
        if (participation.subject_type, participation.subject_id) != (track_subject_type, track_subject_id):
            raise ValueError(f"{context}.participation_id subject does not match track `{track_id}`.")
        if (track_id, ordinal) in track_ordinals:
            raise ValueError(f"{context}.ordinal duplicates ordinal {ordinal} on track `{track_id}`.")
        if (track_id, participation_id) in track_participations:
            raise ValueError(f"{context}.participation_id already appears on track `{track_id}`.")
        track_ordinals.add((track_id, ordinal))
        track_participations.add((track_id, participation_id))
        track_entries[entry_id] = OccurrenceTrackEntry(entry_id, track_id, participation_id, ordinal)

    tracks: dict[str, OccurrenceTrack] = {}
    for track_id, (label, kind, subject_type, subject_id) in track_metadata.items():
        entries = sorted(
            (item for item in track_entries.values() if item.track_id == track_id),
            key=lambda item: item.ordinal,
        )
        expected_ordinals = list(range(1, len(entries) + 1))
        if [item.ordinal for item in entries] != expected_ordinals:
            raise ValueError(f"Track `{track_id}` entry ordinals must be contiguous from 1.")
        entry_ids = tuple(item.id for item in entries)
        occurrence_ids = tuple(occurrence_participations[item.participation_id].occurrence_id for item in entries)
        tracks[track_id] = OccurrenceTrack(
            track_id,
            label,
            kind,
            subject_type,
            subject_id,
            entry_ids,
            occurrence_ids,
        )
    participation_tracks: dict[str, set[str]] = {item_id: set() for item_id in occurrence_participations}
    for entry in track_entries.values():
        participation_tracks[entry.participation_id].add(entry.track_id)
    for duplicate_ids in participation_semantics.values():
        if len(duplicate_ids) < 2:
            continue
        shared_tracks = set(participation_tracks[duplicate_ids[0]])
        for participation_id in duplicate_ids[1:]:
            shared_tracks.intersection_update(participation_tracks[participation_id])
        if not shared_tracks:
            joined_ids = ", ".join(f"`{item_id}`" for item_id in duplicate_ids)
            raise ValueError(
                f"Semantic duplicate participations {joined_ids} must share a track that orders each encounter."
            )
    _validate_track_iteration_order(tracks, occurrences, iterations)

    seen_ids: set[str] = set()
    transitions: list[OccurrenceTransition] = []
    for index, raw in enumerate(_list(root.get("transitions"), "occurrences.transitions")):
        context = f"transitions[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id",
                "source_occurrence_id",
                "target_occurrence_id",
                "transition_kind",
                "transition_profile",
                "recurrence_id",
                "track_ids",
                "certainty",
            },
            context,
        )
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
        if packs.transition_profiles.get(kind) != profile:
            raise ValueError(f"{context}.transition_kind/transition_profile is not a declared typed mapping.")
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
            if track_occurrences.count(source_id) != 1 or track_occurrences.count(target_id) != 1:
                raise ValueError(
                    f"{context} endpoints must each appear exactly once on track `{track_id}`; "
                    "participation-relative transitions are not available."
                )
            if track_occurrences.index(source_id) >= track_occurrences.index(target_id):
                raise ValueError(f"{context} must advance in declared track order on `{track_id}`.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        transition = OccurrenceTransition(
            transition_id, source_id, target_id, kind, profile, recurrence_id, track_ids, certainty
        )
        _validate_transition_profile(
            transition, occurrences, iterations, recurrences, branches, chronology, recurrence_id, context
        )
        semantic_key = (source_id, target_id, kind, profile, recurrence_id, tuple(sorted(track_ids)))
        if any(
            (
                existing.source_occurrence_id,
                existing.target_occurrence_id,
                existing.transition_kind,
                existing.transition_profile,
                existing.recurrence_id,
                tuple(sorted(existing.track_ids)),
            )
            == semantic_key
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

    transition_by_id = {item.id: item for item in transitions}
    branch_state_transitions: list[BranchStateTransition] = []
    branch_state_ordinals: dict[str, set[int]] = {branch_id: set() for branch_id in branches}
    for index, raw in enumerate(_list(root.get("branch_state_transitions"), "occurrences.branch_state_transitions")):
        context = f"branch_state_transitions[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {
                "id",
                "label",
                "branch_id",
                "ordinal",
                "change_kind",
                "prior_state",
                "resulting_state",
                "activation_occurrence_id",
                "trigger_transition_id",
                "certainty",
            },
            context,
        )
        state_id = _stable(_string(item, "id", context), f"{context}.id")
        if state_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{state_id}`.")
        seen_ids.add(state_id)
        branch_id = _string(item, "branch_id", context)
        if branch_id not in branches:
            raise ValueError(f"{context}.branch_id references unknown branch `{branch_id}`.")
        ordinal = item.get("ordinal")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal <= 0:
            raise ValueError(f"{context}.ordinal must be a positive integer.")
        if ordinal in branch_state_ordinals[branch_id]:
            raise ValueError(f"{context}.ordinal duplicates ordinal {ordinal} for branch `{branch_id}`.")
        branch_state_ordinals[branch_id].add(ordinal)
        change_kind = _string(item, "change_kind", context)
        _value(packs, "occurrence.branch-change-kind", change_kind, f"{context}.change_kind")
        prior_state = _optional_string(item, "prior_state", context)
        if prior_state is not None:
            _value(packs, "occurrence.branch-state", prior_state, f"{context}.prior_state")
        resulting_state = _string(item, "resulting_state", context)
        _value(packs, "occurrence.branch-state", resulting_state, f"{context}.resulting_state")
        activation_occurrence_id = _string(item, "activation_occurrence_id", context)
        if activation_occurrence_id not in occurrences:
            raise ValueError(
                f"{context}.activation_occurrence_id references unknown occurrence `{activation_occurrence_id}`."
            )
        trigger_transition_id = _optional_string(item, "trigger_transition_id", context)
        if trigger_transition_id is not None:
            if trigger_transition_id not in transition_by_id:
                raise ValueError(
                    f"{context}.trigger_transition_id references unknown transition `{trigger_transition_id}`."
                )
            trigger = transition_by_id[trigger_transition_id]
            if activation_occurrence_id not in {trigger.source_occurrence_id, trigger.target_occurrence_id}:
                raise ValueError(f"{context}.activation_occurrence_id must be an endpoint of its trigger transition.")
            source_branch_id = occurrences[trigger.source_occurrence_id].branch_id
            target_branch_id = occurrences[trigger.target_occurrence_id].branch_id
            if trigger.transition_profile == "branch-fork" and target_branch_id != branch_id:
                raise ValueError(f"{context} branch-fork trigger must create branch `{branch_id}`.")
            if trigger.transition_profile == "branch-merge" and branch_id not in {source_branch_id, target_branch_id}:
                raise ValueError(f"{context} branch-merge trigger must involve branch `{branch_id}`.")
        if change_kind == "merge" and (
            trigger_transition_id is None
            or transition_by_id[trigger_transition_id].transition_profile != "branch-merge"
        ):
            raise ValueError(f"{context} merge change must reference a branch-merge trigger.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        branch_state_transitions.append(
            BranchStateTransition(
                state_id,
                _string(item, "label", context),
                branch_id,
                ordinal,
                change_kind,
                prior_state,
                resulting_state,
                activation_occurrence_id,
                trigger_transition_id,
                certainty,
            )
        )

    branch_state_transitions.sort(key=lambda item: (item.branch_id, item.ordinal, item.id))
    for branch_id in branches:
        history = [item for item in branch_state_transitions if item.branch_id == branch_id]
        if not history:
            continue
        if [item.ordinal for item in history] != list(range(1, len(history) + 1)):
            raise ValueError(f"Branch `{branch_id}` lifecycle ordinals must be contiguous from 1.")
        if history[0].prior_state is not None:
            raise ValueError(f"Branch `{branch_id}` first lifecycle transition must have null prior_state.")
        for previous, current in zip(history, history[1:]):
            if current.prior_state != previous.resulting_state:
                raise ValueError(
                    f"Branch `{branch_id}` lifecycle state is discontinuous between `{previous.id}` and `{current.id}`."
                )
        branch = branches[branch_id]
        if branch.parent_branch_id is not None:
            first_trigger = history[0].trigger_transition_id
            if first_trigger is None or transition_by_id[first_trigger].transition_profile != "branch-fork":
                raise ValueError(
                    f"Branch `{branch_id}` first lifecycle transition must reference its branch-fork trigger."
                )

    causal_relations: list[CausalRelation] = []
    causal_semantics: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(_list(root.get("causal_relations"), "occurrences.causal_relations")):
        context = f"causal_relations[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item, {"id", "source_occurrence_id", "relation_type", "target_occurrence_id", "certainty"}, context
        )
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
            {
                "id",
                "occurrence_id",
                "subject_type",
                "subject_id",
                "outcome_kind",
                "result_target_type",
                "result_target_id",
                "certainty",
            },
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
                result_type,
                branches,
                templates,
                recurrence_patterns,
                recurrences,
                iterations,
                occurrences,
                tracks,
                {},
                {},
                {},
                payload_targets,
                schedules=schedules,
                phases=phases,
            ):
                raise ValueError(f"{context} references unknown result target `{result_type}:{result_id}`.")
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        for prior in outcomes:
            if (
                prior.occurrence_id == occurrence_id
                and prior.subject_type == subject_type
                and prior.subject_id == subject_id
                and prior.result_target_type == result_type
                and prior.result_target_id == result_id
                and _outcomes_incompatible(packs, prior.outcome_kind, outcome_kind)
            ):
                raise ValueError(
                    f"{context}.outcome_kind `{outcome_kind}` is incompatible with "
                    f"outcome `{prior.id}` kind `{prior.outcome_kind}`."
                )
        semantic_key = (occurrence_id, subject_type, subject_id, outcome_kind, result_type, result_id)
        if semantic_key in outcome_semantics:
            raise ValueError(f"{context} duplicates an existing semantic occurrence outcome.")
        outcome_semantics.add(semantic_key)
        outcomes.append(
            OccurrenceOutcome(
                outcome_id, occurrence_id, subject_type, subject_id, outcome_kind, result_type, result_id, certainty
            )
        )

    state_scales: dict[str, StateScale] = {}
    for index, raw_scale in enumerate(_list(root.get("state_scales"), "occurrences.state_scales")):
        context = f"state_scales[{index}]"
        scale = _mapping(raw_scale, context)
        assert_allowed_keys(scale, {"id", "kind", "levels", "minimum", "maximum", "unit"}, context)
        scale_id = _stable(_string(scale, "id", context), f"{context}.id")
        if scale_id in state_scales:
            raise ValueError(f"{context}.id duplicates `{scale_id}`.")
        kind = _string(scale, "kind", context)
        _value(packs, "state.capability-scale-kind", kind, f"{context}.kind")
        raw_levels = _list(scale.get("levels"), f"{context}.levels")
        levels: list[StateScaleLevel] = []
        minimum = maximum = None
        unit = None
        if kind == "qualitative":
            if scale.get("minimum") is not None or scale.get("maximum") is not None or scale.get("unit") is not None:
                raise ValueError(f"{context} qualitative scales forbid minimum, maximum, and unit.")
            seen_level_ids: set[str] = set()
            seen_ordinals: set[int] = set()
            for level_index, raw_level in enumerate(raw_levels):
                level_context = f"{context}.levels[{level_index}]"
                level = _mapping(raw_level, level_context)
                assert_allowed_keys(level, {"id", "ordinal"}, level_context)
                level_id = _stable(_string(level, "id", level_context), f"{level_context}.id")
                ordinal = _optional_nonnegative_int(level, "ordinal", level_context)
                if ordinal is None:
                    raise ValueError(f"{level_context}.ordinal must be a nonnegative integer.")
                if level_id in seen_level_ids or ordinal in seen_ordinals:
                    raise ValueError(f"{level_context} duplicates a qualitative level ID or ordinal.")
                seen_level_ids.add(level_id)
                seen_ordinals.add(ordinal)
                levels.append(StateScaleLevel(level_id, ordinal))
            if not levels or sorted(seen_ordinals) != list(range(len(levels))):
                raise ValueError(f"{context}.levels must use contiguous ordinals beginning at zero.")
            levels.sort(key=lambda item: item.ordinal)
        else:
            if raw_levels:
                raise ValueError(f"{context} bounded-integer scales forbid qualitative levels.")
            minimum = _signed_64_int(scale, "minimum", context)
            maximum = _signed_64_int(scale, "maximum", context)
            unit = _stable(_string(scale, "unit", context), f"{context}.unit")
            if minimum >= maximum:
                raise ValueError(f"{context}.minimum must be less than maximum.")
        state_scales[scale_id] = StateScale(scale_id, kind, tuple(levels), minimum, maximum, unit)

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
            {
                "id",
                "label",
                "pattern_id",
                "rule_kind",
                "condition_logic",
                "applicability",
                "priority",
                "resolution_group",
                "selection_mode",
                "override_mode",
                "conditions",
                "effects",
            },
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
        condition_logic = _string(item, "condition_logic", context)
        selection_mode = _string(item, "selection_mode", context)
        override_mode = _string(item, "override_mode", context)
        _value(packs, "occurrence.rule-kind", rule_kind, f"{context}.rule_kind")
        _value(packs, "occurrence.rule-condition-logic", condition_logic, f"{context}.condition_logic")
        _value(packs, "occurrence.rule-selection-mode", selection_mode, f"{context}.selection_mode")
        _value(packs, "occurrence.rule-override-mode", override_mode, f"{context}.override_mode")
        priority = _optional_nonnegative_int(item, "priority", context)
        if priority is None:
            raise ValueError(f"{context}.priority must be a nonnegative integer.")
        resolution_group = _stable(_string(item, "resolution_group", context), f"{context}.resolution_group")
        applicability = _parse_rule_applicability(
            item, context, packs, chronology, pattern_id, branches, recurrences, iterations, phases
        )
        if applicability.application_level == "pattern-default" and applicability.recurrence_ids:
            raise ValueError(f"{context} pattern-default rules cannot restrict recurrence_ids.")
        if applicability.application_level == "execution-override" and not applicability.recurrence_ids:
            raise ValueError(f"{context} execution-override rules require recurrence_ids.")
        if override_mode == "replace-group" and applicability.application_level != "execution-override":
            raise ValueError(f"{context}.override_mode `replace-group` requires an execution-override rule.")
        conditions: list[RecurrenceRuleCondition] = []
        condition_semantics: set[tuple] = set()
        for condition_index, raw_condition in enumerate(_list(item.get("conditions"), f"{context}.conditions")):
            condition_context = f"{context}.conditions[{condition_index}]"
            condition = _mapping(raw_condition, condition_context)
            assert_allowed_keys(
                condition,
                {
                    "id",
                    "condition_kind",
                    "target_type",
                    "target_id",
                    "expected_value",
                    "subject_type",
                    "subject_id",
                    "state_kind",
                    "track_id",
                    "comparison_value",
                },
                condition_context,
            )
            condition_id = _stable(_string(condition, "id", condition_context), f"{condition_context}.id")
            if condition_id in nested_rule_ids:
                raise ValueError(f"{condition_context}.id duplicates `{condition_id}`.")
            nested_rule_ids.add(condition_id)
            condition_kind = _string(condition, "condition_kind", condition_context)
            _value(packs, "occurrence.rule-condition-kind", condition_kind, f"{condition_context}.condition_kind")
            target_type = _stable(
                _string(condition, "target_type", condition_context), f"{condition_context}.target_type"
            )
            target_id = _stable(_string(condition, "target_id", condition_context), f"{condition_context}.target_id")
            expected = _string(condition, "expected_value", condition_context)
            subject_type = _optional_string(condition, "subject_type", condition_context)
            subject_id = _optional_string(condition, "subject_id", condition_context)
            state_kind = _optional_string(condition, "state_kind", condition_context)
            track_id = _optional_string(condition, "track_id", condition_context)
            comparison_value = _optional_nonnegative_int(condition, "comparison_value", condition_context)
            _validate_rule_condition(
                packs,
                pattern_id,
                condition_kind,
                target_type,
                target_id,
                expected,
                subject_type,
                subject_id,
                state_kind,
                track_id,
                comparison_value,
                templates,
                recurrence_patterns,
                schedules,
                branches,
                recurrences,
                iterations,
                occurrences,
                tracks,
                outcomes,
                rule_ids,
                state_ids,
                subject_targets,
                payload_targets,
                condition_context,
            )
            condition_semantic = (
                condition_kind,
                target_type,
                target_id,
                expected,
                subject_type,
                subject_id,
                state_kind,
                track_id,
                comparison_value,
            )
            if condition_semantic in condition_semantics:
                raise ValueError(f"{condition_context} duplicates a semantic condition within its rule.")
            condition_semantics.add(condition_semantic)
            conditions.append(
                RecurrenceRuleCondition(
                    condition_id,
                    condition_kind,
                    target_type,
                    target_id,
                    expected,
                    subject_type,
                    subject_id,
                    state_kind,
                    track_id,
                    comparison_value,
                )
            )
        if not conditions:
            raise ValueError(f"{context}.conditions must be a non-empty list.")
        effects: list[RecurrenceRuleEffect] = []
        effect_semantics: set[tuple[str, str, str]] = set()
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
            if (effect_kind, target_type) not in packs.effect_target_compatibilities:
                raise ValueError(f"{effect_context}.effect_kind/target_type is not a declared typed compatibility.")
            if (rule_kind, effect_kind) not in packs.rule_effect_compatibilities:
                raise ValueError(f"{effect_context}.rule_kind/effect_kind is not a declared typed compatibility.")
            if target_id not in _target_ids(
                target_type,
                branches,
                templates,
                recurrence_patterns,
                recurrences,
                iterations,
                occurrences,
                tracks,
                {item.id: item for item in outcomes},
                rule_ids,
                state_ids,
                payload_targets,
                schedules=schedules,
            ):
                raise ValueError(f"{effect_context} references unknown target `{target_type}:{target_id}`.")
            if target_type == "recurrence-pattern":
                declared_scope = packs.effect_policies[effect_kind].recurrence_pattern_scope
                if declared_scope == "owning-pattern" and target_id != pattern_id:
                    raise ValueError(
                        f"{effect_context} effect kind `{effect_kind}` must target owning pattern `{pattern_id}`."
                    )
            effect_semantic = (effect_kind, target_type, target_id)
            if effect_semantic in effect_semantics:
                raise ValueError(f"{effect_context} duplicates a semantic effect within its rule.")
            effect_semantics.add(effect_semantic)
            effects.append(RecurrenceRuleEffect(effect_id, effect_kind, target_type, target_id))
        if not effects:
            raise ValueError(f"{context}.effects must be a non-empty list.")
        applicability_key = (
            applicability.application_level,
            tuple(sorted(applicability.recurrence_ids)),
            tuple(sorted(applicability.phase_ids)),
            tuple(sorted(applicability.branch_ids)),
            applicability.min_iteration_ordinal,
            applicability.max_iteration_ordinal,
            _chronology_window_key(applicability.chronology_window),
            _temporal_window_key(applicability.effective_window),
        )
        semantic_key = (
            pattern_id,
            rule_kind,
            condition_logic,
            applicability_key,
            priority,
            resolution_group,
            selection_mode,
            override_mode,
            tuple(
                sorted(
                    (
                        condition.condition_kind,
                        condition.target_type,
                        condition.target_id,
                        condition.expected_value,
                        condition.subject_type,
                        condition.subject_id,
                        condition.state_kind,
                        condition.track_id,
                        condition.comparison_value,
                    )
                    for condition in conditions
                )
            ),
            tuple(sorted((effect.effect_kind, effect.target_type, effect.target_id) for effect in effects)),
        )
        if semantic_key in rule_semantics:
            raise ValueError(f"{context} duplicates an existing semantic recurrence rule.")
        rule_semantics.add(semantic_key)
        rules.append(
            RecurrenceRule(
                rule_id,
                _string(item, "label", context),
                pattern_id,
                rule_kind,
                condition_logic,
                applicability,
                priority,
                resolution_group,
                selection_mode,
                override_mode,
                tuple(conditions),
                tuple(effects),
            )
        )

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
                "id",
                "subject_type",
                "subject_id",
                "payload_target_type",
                "payload_target_id",
                "state_kind",
                "change_kind",
                "change_profile",
                "change_shape",
                "mechanism",
                "prior_availability",
                "resulting_availability",
                "prior_attitude",
                "resulting_attitude",
                "prior_completeness",
                "resulting_completeness",
                "prior_capability",
                "resulting_capability",
                "activation_occurrence_id",
                "condition_rule_id",
                "track_ids",
                "source_targets",
                "certainty",
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
            payload_type,
            branches,
            templates,
            recurrence_patterns,
            recurrences,
            iterations,
            occurrences,
            tracks,
            outcome_map,
            rule_map,
            state_ids,
            payload_targets,
            schedules=schedules,
            phases=phases,
        ):
            raise ValueError(f"{context} references unknown payload `{payload_type}:{payload_id}`.")
        state_kind = _string(item, "state_kind", context)
        _value(packs, "state.state-kind", state_kind, f"{context}.state_kind")
        state_profile_id = packs.state_kind_profiles[state_kind]
        state_profile = packs.state_profiles[state_profile_id]
        change_kind = _string(item, "change_kind", context)
        _value(packs, "state.change-kind", change_kind, f"{context}.change_kind")
        change_profile = _string(item, "change_profile", context)
        _value(packs, "state.change-profile", change_profile, f"{context}.change_profile")
        if packs.state_change_profiles.get(change_kind) != change_profile:
            raise ValueError(f"{context}.change_kind/change_profile is not a declared typed mapping.")
        change_shape = _string(item, "change_shape", context)
        _value(packs, "state.change-shape", change_shape, f"{context}.change_shape")
        mechanism = _string(item, "mechanism", context)
        _value(packs, "state.mechanism", mechanism, f"{context}.mechanism")
        prior = _string(item, "prior_availability", context)
        resulting = _string(item, "resulting_availability", context)
        _value(packs, "state.availability-status", prior, f"{context}.prior_availability")
        _value(packs, "state.availability-status", resulting, f"{context}.resulting_availability")
        _validate_state_profile(change_profile, prior, resulting, context)
        prior_attitude = _optional_string(item, "prior_attitude", context)
        resulting_attitude = _optional_string(item, "resulting_attitude", context)
        _validate_state_dimension(
            state_profile.attitude,
            prior_attitude,
            resulting_attitude,
            "attitude",
            context,
        )
        if prior_attitude is not None:
            _value(packs, "state.epistemic-attitude", prior_attitude, f"{context}.prior_attitude")
            _value(packs, "state.epistemic-attitude", resulting_attitude, f"{context}.resulting_attitude")
        prior_completeness = _optional_string(item, "prior_completeness", context)
        resulting_completeness = _optional_string(item, "resulting_completeness", context)
        _validate_state_dimension(
            state_profile.completeness,
            prior_completeness,
            resulting_completeness,
            "completeness",
            context,
        )
        if prior_completeness is not None:
            _value(packs, "state.completeness", prior_completeness, f"{context}.prior_completeness")
            _value(packs, "state.completeness", resulting_completeness, f"{context}.resulting_completeness")
        prior_capability = _capability_value(item.get("prior_capability"), state_scales, f"{context}.prior_capability")
        resulting_capability = _capability_value(
            item.get("resulting_capability"), state_scales, f"{context}.resulting_capability"
        )
        _validate_state_dimension(
            state_profile.capability,
            prior_capability,
            resulting_capability,
            "capability",
            context,
        )
        if prior_capability is not None and resulting_capability is not None:
            if prior_capability.scale_id != resulting_capability.scale_id:
                raise ValueError(f"{context} prior and resulting capability must use the same scale.")
            _validate_capability_change(change_profile, prior_capability, resulting_capability, state_scales, context)
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
            if track.occurrence_ids.count(activation_id) != 1:
                raise ValueError(
                    f"{context}.activation_occurrence_id appears more than once on track `{track_id}`; "
                    "participation-relative state transitions are not available."
                )
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
                source_type,
                branches,
                templates,
                recurrence_patterns,
                recurrences,
                iterations,
                occurrences,
                tracks,
                outcome_map,
                rule_map,
                state_ids,
                payload_targets,
                schedules=schedules,
                phases=phases,
            ):
                raise ValueError(f"{source_context} references unknown target `{source_type}:{source_target_id}`.")
            role = _string(source, "role", source_context)
            _value(packs, "state.source-role", role, f"{source_context}.role")
            source_records.append(StateSourceTarget(source_id, source_type, source_target_id, role))
        certainty = _string(item, "certainty", context)
        _value(packs, "temporal.certainty", certainty, f"{context}.certainty")
        semantic_key = (
            subject_type,
            subject_id,
            payload_type,
            payload_id,
            state_kind,
            state_profile_id,
            change_kind,
            change_profile,
            change_shape,
            mechanism,
            prior,
            resulting,
            prior_attitude,
            resulting_attitude,
            prior_completeness,
            resulting_completeness,
            prior_capability,
            resulting_capability,
            activation_id,
            condition_rule_id,
            tuple(sorted(track_ids)),
        )
        if semantic_key in state_semantics:
            raise ValueError(f"{context} duplicates an existing semantic state transition.")
        state_semantics.add(semantic_key)
        states.append(
            StateTransition(
                state_id,
                subject_type,
                subject_id,
                payload_type,
                payload_id,
                state_kind,
                state_profile_id,
                change_kind,
                change_profile,
                change_shape,
                mechanism,
                prior,
                resulting,
                prior_attitude,
                resulting_attitude,
                prior_completeness,
                resulting_completeness,
                prior_capability,
                resulting_capability,
                activation_id,
                condition_rule_id,
                track_ids,
                tuple(source_records),
                certainty,
            )
        )
    state_map = {item.id: item for item in states}
    _validate_state_chains(states, tracks)

    carryovers: list[IterationCarryover] = []
    carryover_semantics: set[tuple[str, str, str, str]] = set()
    for index, raw in enumerate(_list(root.get("carryovers"), "occurrences.carryovers")):
        context = f"carryovers[{index}]"
        item = _mapping(raw, context)
        assert_allowed_keys(
            item,
            {"id", "source_iteration_id", "target_iteration_id", "track_id", "state_transition_id", "certainty"},
            context,
        )
        carryover_id = _stable(_string(item, "id", context), f"{context}.id")
        if carryover_id in seen_ids:
            raise ValueError(f"{context}.id duplicates `{carryover_id}`.")
        seen_ids.add(carryover_id)
        source_id = _string(item, "source_iteration_id", context)
        target_id = _string(item, "target_iteration_id", context)
        track_id = _string(item, "track_id", context)
        state_id = _string(item, "state_transition_id", context)
        if (
            source_id not in iterations
            or target_id not in iterations
            or track_id not in tracks
            or state_id not in state_map
        ):
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
        path,
        SUPPORTED_SCHEMA_VERSION,
        chronology,
        branches,
        tuple(branch_state_transitions),
        templates,
        recurrence_patterns,
        recurrences,
        iterations,
        recurrence_cardinalities,
        phases,
        schedules,
        occurrences,
        occurrence_participations,
        tracks,
        track_entries,
        tuple(transitions),
        tuple(causal_relations),
        tuple(outcomes),
        tuple(rules),
        state_scales,
        tuple(states),
        tuple(carryovers),
        frozenset(pair for pair, scope in packs.effect_incompatibilities.items() if scope == "global"),
        frozenset(pair for pair, scope in packs.effect_incompatibilities.items() if scope == "same-target"),
        _effect_repetition_policies(packs),
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
            raise ValueError(
                f"{context} scoped `{transition.transition_profile}` endpoints must belong to "
                f"recurrence `{recurrence_id}`."
            )
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
                for source in source_occurrence.bindings
                if source.role == "primary"
                for target in target_occurrence.bindings
                if target.role == "primary"
            }
            if "after" in comparisons:
                raise ValueError(f"{context} ordered transition contradicts exact chronology position order.")
            ordered_evidence = ordered_evidence or "before" in comparisons
            if not ordered_evidence:
                raise ValueError(
                    f"{context} ordered transition requires a forward track, iteration, or chronology order."
                )
        return

    if transition.transition_profile == "recurrence-advance":
        if source_iteration is None or target_iteration is None or recurrence_id is None:
            raise ValueError(
                f"{context} recurrence-advance transitions require recurrence-bound source and target iterations."
            )
        if (
            source_iteration.recurrence_id != recurrence_id
            or target_iteration.recurrence_id != recurrence_id
            or source_iteration.ordinal >= target_iteration.ordinal
        ):
            raise ValueError(
                f"{context} recurrence-advance transition must advance iterations in recurrence `{recurrence_id}`."
            )
        return

    if transition.transition_profile == "recurrence-exit":
        if (
            source_iteration is None
            or recurrence_id is None
            or not _recurrence_within(source_iteration.recurrence_id, recurrence_id, recurrences)
        ):
            raise ValueError(f"{context} recurrence-exit source must belong to recurrence `{recurrence_id}`.")
        if target_iteration is not None and _recurrence_within(
            target_iteration.recurrence_id, recurrence_id, recurrences
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


def _ordinal_ranges_overlap(left_start: int, left_end: int | None, right_start: int, right_end: int | None) -> bool:
    left_limit = float("inf") if left_end is None else left_end
    right_limit = float("inf") if right_end is None else right_end
    return left_start <= right_limit and right_start <= left_limit


def _validate_civil_schedule_anchor(value: str, unit: str, context: str) -> None:
    formats = {"year": "%Y", "month": "%Y-%m", "day": "%Y-%m-%d", "week": "%Y-%m-%d"}
    if unit not in formats:
        raise ValueError(f"{context}.unit `{unit}` is not valid for a civil-calendar schedule.")
    try:
        parsed = date.fromisoformat(
            value if unit in {"day", "week"} else f"{value}-01" if unit == "month" else f"{value}-01-01"
        )
    except ValueError as exc:
        raise ValueError(f"{context}.anchor_value does not match schedule unit `{unit}`: {value}") from exc
    expected = parsed.strftime(formats[unit])
    if value != expected:
        raise ValueError(f"{context}.anchor_value does not match schedule unit `{unit}`: {value}")


def _add_civil_interval(value: str, unit: str, offset: int) -> str:
    boundary_error = "Schedule projection exceeds supported civil range 0001-9999."
    if unit == "year":
        target_year = int(value) + offset
        if not 1 <= target_year <= 9999:
            raise ValueError(boundary_error)
        return f"{target_year:04d}"
    if unit == "month":
        year, month = (int(part) for part in value.split("-"))
        absolute = year * 12 + month - 1 + offset
        target_year = absolute // 12
        if not 1 <= target_year <= 9999:
            raise ValueError(boundary_error)
        return f"{target_year:04d}-{absolute % 12 + 1:02d}"
    parsed = date.fromisoformat(value)
    try:
        return (parsed + timedelta(days=offset * (7 if unit == "week" else 1))).isoformat()
    except OverflowError as exc:
        raise ValueError(boundary_error) from exc


def _outcomes_incompatible(packs: SchemaPackRegistry, left: str, right: str) -> bool:
    if left == right:
        return False
    return tuple(sorted((left, right))) in packs.outcome_incompatibilities


def _parse_rule_applicability(
    item: dict,
    context: str,
    packs: SchemaPackRegistry,
    chronology: ChronologyRegistry,
    pattern_id: str,
    branches: dict[str, OccurrenceBranch],
    recurrences: dict[str, Recurrence],
    iterations: dict[str, RecurrenceIteration],
    phases: dict[str, RecurrencePhase],
) -> RuleApplicability:
    raw = _mapping(item.get("applicability"), f"{context}.applicability")
    app_context = f"{context}.applicability"
    assert_allowed_keys(
        raw,
        {
            "application_level",
            "recurrence_ids",
            "phase_ids",
            "branch_ids",
            "min_iteration_ordinal",
            "max_iteration_ordinal",
            "chronology_window",
            "effective_window",
        },
        app_context,
    )
    application_level = _string(raw, "application_level", app_context)
    _value(packs, "occurrence.rule-application-level", application_level, f"{app_context}.application_level")
    recurrence_ids = _strings(raw, "recurrence_ids", app_context)
    phase_ids = _strings(raw, "phase_ids", app_context)
    branch_ids = _strings(raw, "branch_ids", app_context)
    for recurrence_id in recurrence_ids:
        if recurrence_id not in recurrences or recurrences[recurrence_id].pattern_id != pattern_id:
            raise ValueError(f"{app_context}.recurrence_ids references incompatible recurrence `{recurrence_id}`.")
    for phase_id in phase_ids:
        if phase_id not in phases or recurrences[phases[phase_id].recurrence_id].pattern_id != pattern_id:
            raise ValueError(f"{app_context}.phase_ids references incompatible phase `{phase_id}`.")
    for branch_id in branch_ids:
        if branch_id not in branches:
            raise ValueError(f"{app_context}.branch_ids references unknown branch `{branch_id}`.")
    minimum = _optional_nonnegative_int(raw, "min_iteration_ordinal", app_context)
    maximum = _optional_nonnegative_int(raw, "max_iteration_ordinal", app_context)
    if minimum == 0 or maximum == 0 or (minimum is not None and maximum is not None and minimum > maximum):
        raise ValueError(f"{app_context} iteration bounds must be positive and ordered.")
    chronology_window = None
    raw_window = raw.get("chronology_window")
    if raw_window is not None:
        window_context = f"{app_context}.chronology_window"
        window = _mapping(raw_window, window_context)
        assert_allowed_keys(window, {"start_position_id", "end_position_id"}, window_context)
        start = _optional_string(window, "start_position_id", window_context)
        end = _optional_string(window, "end_position_id", window_context)
        if start is None and end is None:
            raise ValueError(f"{window_context} requires at least one chronology position.")
        for position_id in (start, end):
            if position_id is not None and position_id not in chronology.positions:
                raise ValueError(f"{window_context} references unknown position `{position_id}`.")
        if start is not None and end is not None and chronology.compare_positions(start, end) == "after":
            raise ValueError(f"{window_context} is reversed.")
        chronology_window = ChronologyApplicabilityWindow(start, end)
    effective_window = parse_temporal_window(raw, "effective_window", app_context, packs)
    return RuleApplicability(
        application_level,
        recurrence_ids,
        phase_ids,
        branch_ids,
        minimum,
        maximum,
        chronology_window,
        effective_window,
    )


def _chronology_window_key(window: ChronologyApplicabilityWindow | None) -> tuple | None:
    return None if window is None else (window.start_position_id, window.end_position_id)


def _temporal_window_key(window: TemporalWindow | None) -> tuple | None:
    if window is None:
        return None

    def bound_key(bound):
        return None if bound is None else (bound.kind, bound.value, bound.precision, bound.certainty, bound.inclusive)

    return (window.kind, bound_key(window.start), bound_key(window.end))


def _validate_rule_condition(
    packs: SchemaPackRegistry,
    pattern_id: str,
    condition_kind: str,
    target_type: str,
    target_id: str,
    expected_value: str,
    subject_type: str | None,
    subject_id: str | None,
    state_kind: str | None,
    track_id: str | None,
    comparison_value: int | None,
    templates: dict[str, OccurrenceTemplate],
    recurrence_patterns: dict[str, RecurrencePattern],
    schedules: dict[str, RecurrenceSchedule],
    branches: dict[str, OccurrenceBranch],
    recurrences: dict[str, Recurrence],
    iterations: dict[str, RecurrenceIteration],
    occurrences: dict[str, Occurrence],
    tracks: dict[str, OccurrenceTrack],
    outcomes: list[OccurrenceOutcome],
    rule_ids: set[str],
    state_ids: set[str],
    subject_targets: dict[str, set[str]] | None,
    payload_targets: dict[str, set[str]] | None,
    context: str,
) -> None:
    expected_target = {
        "occurrence-reached": "occurrence-template",
        "occurrence-outcome": "occurrence-template",
        "iteration-ordinal": "recurrence-pattern",
        "schedule-due": "recurrence-schedule",
    }.get(condition_kind)
    if expected_target is not None and target_type != expected_target:
        raise ValueError(f"{context} condition `{condition_kind}` must target `{expected_target}`.")
    if target_id not in _target_ids(
        target_type,
        branches,
        templates,
        recurrence_patterns,
        recurrences,
        iterations,
        occurrences,
        tracks,
        {item.id: item for item in outcomes},
        rule_ids,
        state_ids,
        payload_targets,
        schedules=schedules,
    ):
        raise ValueError(f"{context} references unknown target `{target_type}:{target_id}`.")
    subject_fields = (subject_type, subject_id)
    if (subject_type is None) != (subject_id is None):
        raise ValueError(f"{context} must set both subject fields, or neither.")
    if subject_type is not None:
        _known_external_target(subject_targets, subject_type, subject_id, f"{context}.subject")
    if condition_kind == "occurrence-reached":
        _value(packs, "occurrence.rule-condition-value", expected_value, f"{context}.expected_value")
        if expected_value != "occurred" or any(
            value is not None for value in (*subject_fields, state_kind, track_id, comparison_value)
        ):
            raise ValueError(f"{context} occurrence-reached conditions only accept expected_value `occurred`.")
    elif condition_kind == "occurrence-outcome":
        _value(packs, "occurrence.outcome-kind", expected_value, f"{context}.expected_value")
        if subject_type is None or any(value is not None for value in (state_kind, track_id, comparison_value)):
            raise ValueError(f"{context} occurrence-outcome conditions require only a subject selector.")
    elif condition_kind == "state-availability":
        _value(packs, "state.availability-status", expected_value, f"{context}.expected_value")
        if subject_type is None or state_kind is None or track_id is None or comparison_value is not None:
            raise ValueError(f"{context} state-availability conditions require subject, state_kind, and track_id.")
        _value(packs, "state.state-kind", state_kind, f"{context}.state_kind")
        if track_id not in tracks:
            raise ValueError(f"{context}.track_id references unknown track `{track_id}`.")
        track = tracks[track_id]
        if (track.subject_type, track.subject_id) != (subject_type, subject_id):
            raise ValueError(f"{context}.track_id does not track the selected subject.")
    elif condition_kind == "iteration-ordinal":
        _value(packs, "occurrence.rule-comparison", expected_value, f"{context}.expected_value")
        if (
            comparison_value is None
            or comparison_value < 1
            or any(value is not None for value in (*subject_fields, state_kind, track_id))
        ):
            raise ValueError(f"{context} iteration-ordinal conditions require a positive comparison_value only.")
        if target_id != pattern_id:
            raise ValueError(f"{context} iteration-ordinal condition must target owning pattern `{pattern_id}`.")
    elif condition_kind == "schedule-due":
        _value(packs, "occurrence.rule-condition-value", expected_value, f"{context}.expected_value")
        if expected_value != "due" or any(
            value is not None for value in (*subject_fields, state_kind, track_id, comparison_value)
        ):
            raise ValueError(f"{context} schedule-due conditions only accept expected_value `due`.")
        if schedules[target_id].pattern_id != pattern_id:
            raise ValueError(f"{context} schedule must belong to owning pattern `{pattern_id}`.")
    else:
        raise ValueError(f"{context} uses unsupported condition kind `{condition_kind}`.")


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
        "improve": prior == resulting and resulting in {"partial", "available"},
        "degrade": prior == resulting and resulting in {"partial", "available"},
    }
    if not valid.get(profile, False):
        raise ValueError(
            f"{context} state profile `{profile}` is incompatible with availability "
            f"transition `{prior}` -> `{resulting}`."
        )


def _capability_value(value: object, scales: dict[str, StateScale], context: str) -> CapabilityValue | None:
    if value is None:
        return None
    item = _mapping(value, context)
    assert_allowed_keys(item, {"scale_id", "value"}, context)
    scale_id = _stable(_string(item, "scale_id", context), f"{context}.scale_id")
    if scale_id not in scales:
        raise ValueError(f"{context}.scale_id references unknown state scale `{scale_id}`.")
    scale = scales[scale_id]
    raw_value = item.get("value")
    if scale.kind == "qualitative":
        if not isinstance(raw_value, str) or raw_value not in {level.id for level in scale.levels}:
            raise ValueError(f"{context}.value must be a level from qualitative scale `{scale_id}`.")
        parsed_value: str | int = raw_value
    else:
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise ValueError(f"{context}.value must be an integer for bounded scale `{scale_id}`.")
        if raw_value < scale.minimum or raw_value > scale.maximum:
            raise ValueError(f"{context}.value falls outside bounded scale `{scale_id}`.")
        parsed_value = raw_value
    return CapabilityValue(scale_id, parsed_value)


def _capability_rank(value: CapabilityValue, scales: dict[str, StateScale]) -> int:
    scale = scales[value.scale_id]
    if scale.kind == "qualitative":
        return next(level.ordinal for level in scale.levels if level.id == value.value)
    return int(value.value)


def _validate_capability_change(
    profile: str,
    prior: CapabilityValue,
    resulting: CapabilityValue,
    scales: dict[str, StateScale],
    context: str,
) -> None:
    prior_rank = _capability_rank(prior, scales)
    resulting_rank = _capability_rank(resulting, scales)
    if profile == "preserve" and prior_rank != resulting_rank:
        raise ValueError(f"{context} preserve requires an unchanged capability value.")
    if profile == "improve" and resulting_rank <= prior_rank:
        raise ValueError(f"{context} improve requires an increasing capability value.")
    if profile == "degrade" and resulting_rank >= prior_rank:
        raise ValueError(f"{context} degrade requires a decreasing capability value.")


def _validate_state_dimension(
    requirement: str,
    prior: object | None,
    resulting: object | None,
    dimension: str,
    context: str,
) -> None:
    if (prior is None) != (resulting is None):
        raise ValueError(f"{context} must set both prior and resulting {dimension}, or neither.")
    present = prior is not None
    if requirement == "required" and not present:
        raise ValueError(f"{context} state profile requires prior and resulting {dimension}.")
    if requirement == "forbidden" and present:
        raise ValueError(f"{context} state profile forbids prior and resulting {dimension}.")


def _validate_state_chains(
    states: list[StateTransition],
    tracks: dict[str, OccurrenceTrack],
) -> None:
    chains: dict[tuple[str, str, str, str, str, str], list[StateTransition]] = {}
    for state in states:
        for track_id in state.track_ids:
            key = (
                track_id,
                state.subject_type,
                state.subject_id,
                state.payload_target_type,
                state.payload_target_id,
                state.state_kind,
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
            if previous.resulting_completeness != current.prior_completeness:
                raise ValueError(
                    f"State transition `{current.id}` prior completeness does not continue "
                    f"state transition `{previous.id}`."
                )
            if previous.resulting_capability != current.prior_capability:
                raise ValueError(
                    f"State transition `{current.id}` prior capability does not continue "
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
        indices[item] for item in track.occurrence_ids if occurrences[item].iteration_id == source_iteration_id
    ]
    target_indices = [
        indices[item] for item in track.occurrence_ids if occurrences[item].iteration_id == target_iteration_id
    ]
    activation_index = indices[state.activation_occurrence_id]
    if activation_index > max(source_indices):
        raise ValueError(f"{context}.state_transition_id activates after the source iteration ends.")
    chain_key = (
        state.subject_type,
        state.subject_id,
        state.payload_target_type,
        state.payload_target_id,
        state.state_kind,
    )
    for candidate in states:
        if candidate.id == state.id or track.id not in candidate.track_ids:
            continue
        candidate_key = (
            candidate.subject_type,
            candidate.subject_id,
            candidate.payload_target_type,
            candidate.payload_target_id,
            candidate.state_kind,
        )
        candidate_index = indices[candidate.activation_occurrence_id]
        if chain_key == candidate_key and activation_index < candidate_index < min(target_indices):
            raise ValueError(
                f"{context}.state_transition_id is superseded by `{candidate.id}` before the target iteration begins."
            )


def _rule_applicability_status(
    registry: OccurrenceRegistry,
    rule: RecurrenceRule,
    recurrence: Recurrence,
    iteration: RecurrenceIteration,
    occurrence: Occurrence,
    effective_at: str | None,
) -> tuple[str, str]:
    applicability = rule.applicability
    if applicability.recurrence_ids and recurrence.id not in applicability.recurrence_ids:
        return "not-applicable", "recurrence excluded"
    phase = registry.phase_for_iteration(iteration.id)
    if applicability.phase_ids and (phase is None or phase.id not in applicability.phase_ids):
        return "not-applicable", "phase excluded"
    if applicability.branch_ids and occurrence.branch_id not in applicability.branch_ids:
        return "not-applicable", "branch excluded"
    if applicability.min_iteration_ordinal is not None and iteration.ordinal < applicability.min_iteration_ordinal:
        return "not-applicable", "iteration below minimum"
    if applicability.max_iteration_ordinal is not None and iteration.ordinal > applicability.max_iteration_ordinal:
        return "not-applicable", "iteration above maximum"
    window = applicability.chronology_window
    if window is not None:
        primary = [binding.position_id for binding in occurrence.bindings if binding.role == "primary"]
        if not primary:
            return "indeterminate", "occurrence has no primary chronology binding"
        comparable = False
        inside = False
        for position_id in primary:
            start_relation = (
                registry.chronology.compare_positions(window.start_position_id, position_id)
                if window.start_position_id is not None
                else "before"
            )
            end_relation = (
                registry.chronology.compare_positions(position_id, window.end_position_id)
                if window.end_position_id is not None
                else "before"
            )
            if start_relation != "incomparable" and end_relation != "incomparable":
                comparable = True
                if start_relation in {"before", "concurrent"} and end_relation in {"before", "concurrent"}:
                    inside = True
                    break
        if not comparable:
            return "indeterminate", "chronology window is incomparable with occurrence"
        if not inside:
            return "not-applicable", "occurrence is outside chronology window"
    query, _ = normalize_effective_at(effective_at)
    if applicability.effective_window is not None and query is None:
        return "indeterminate", "effective time was not supplied"
    temporal = temporal_window_match(applicability.effective_window, query)
    if temporal is None:
        return "not-applicable", "effective time is outside window"
    if temporal == "unknown" or (isinstance(temporal, str) and temporal.startswith("indeterminate-")):
        return "indeterminate", f"effective window is {temporal}"
    return "applicable", "all applicability selectors matched"


def _evaluate_rule_condition(
    registry: OccurrenceRegistry,
    condition: RecurrenceRuleCondition,
    recurrence: Recurrence,
    iteration: RecurrenceIteration,
    occurrence: Occurrence,
    effective_at: str | None,
) -> RuleConditionEvaluation:
    kind = condition.condition_kind
    if kind == "occurrence-reached":
        matched = occurrence.template_id == condition.target_id
        detail = f"current template is `{occurrence.template_id}`"
    elif kind == "occurrence-outcome":
        matched = (
            any(
                outcome.occurrence_id == occurrence.id
                and outcome.subject_type == condition.subject_type
                and outcome.subject_id == condition.subject_id
                and outcome.outcome_kind == condition.expected_value
                for outcome in registry.outcomes
            )
            and occurrence.template_id == condition.target_id
        )
        detail = "matching subject-qualified outcome found" if matched else "matching outcome not found"
    elif kind == "state-availability":
        track = registry.tracks[condition.track_id]
        if occurrence.id not in track.occurrence_ids:
            return RuleConditionEvaluation(condition.id, "indeterminate", "occurrence is not on selected state track")
        state = registry.state_at(
            condition.track_id, occurrence.id, condition.target_type, condition.target_id, condition.state_kind
        )
        matched = state is not None and state.resulting_availability == condition.expected_value
        detail = "no state established" if state is None else f"availability is `{state.resulting_availability}`"
    elif kind == "iteration-ordinal":
        value = condition.comparison_value
        comparisons = {
            "equals": iteration.ordinal == value,
            "at-least": iteration.ordinal >= value,
            "at-most": iteration.ordinal <= value,
            "less-than": iteration.ordinal < value,
            "greater-than": iteration.ordinal > value,
        }
        matched = comparisons[condition.expected_value]
        detail = f"iteration ordinal is {iteration.ordinal}"
    elif kind == "schedule-due":
        status = registry.schedule_match(condition.target_id, iteration.id, occurrence.id, effective_at)
        if status == "indeterminate":
            return RuleConditionEvaluation(condition.id, "indeterminate", "schedule could not be evaluated")
        matched = status == "due"
        detail = f"schedule is `{status}`"
    else:
        raise ValueError(f"Unsupported recurrence condition kind `{kind}`.")
    return RuleConditionEvaluation(condition.id, "matched" if matched else "not-matched", detail)


def _effect_signature(rule: RecurrenceRule) -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted((item.effect_kind, item.target_type, item.target_id) for item in rule.effects))


def _effect_repetition_policies(packs: SchemaPackRegistry) -> dict[str, str]:
    return {effect_kind: declaration.repetition_policy for effect_kind, declaration in packs.effect_policies.items()}


def _resolve_effects(
    selected: list[RecurrenceRule], repetition_policies: dict[str, str]
) -> tuple[tuple[ResolvedRuleEffect, ...], tuple[str, ...]]:
    grouped: dict[tuple[str, str, str], list[tuple[str, RecurrenceRuleEffect]]] = {}
    for rule in sorted(selected, key=lambda item: item.id):
        for effect in rule.effects:
            grouped.setdefault((effect.effect_kind, effect.target_type, effect.target_id), []).append((rule.id, effect))
    resolved: list[ResolvedRuleEffect] = []
    conflicts: set[str] = set()
    for (effect_kind, target_type, target_id), contributions in sorted(grouped.items()):
        policy = repetition_policies[effect_kind]
        count = len(contributions)
        proposed_execution_count = count if policy == "accumulating" else 1
        if policy == "invalid" and count > 1:
            proposed_execution_count = 0
            conflicts.add(f"duplicate {effect_kind} effect on {target_type}:{target_id} is invalid")
        resolved.append(
            ResolvedRuleEffect(
                effect_kind,
                target_type,
                target_id,
                policy,
                count,
                proposed_execution_count,
                tuple(rule_id for rule_id, _ in contributions),
                tuple(effect.id for _, effect in contributions),
            )
        )
    return tuple(resolved), tuple(sorted(conflicts))


def _effect_conflicts(registry: OccurrenceRegistry, effects: tuple[ResolvedRuleEffect, ...]) -> tuple[str, ...]:
    conflicts: set[str] = set()
    kinds = sorted({item.effect_kind for item in effects})
    for index, left in enumerate(kinds):
        for right in kinds[index + 1 :]:
            pair = (left, right)
            if pair in registry.effect_global_incompatibility_pairs:
                conflicts.add(f"{left} conflicts with {right} globally")
            if pair in registry.effect_same_target_incompatibility_pairs:
                left_effects = [item for item in effects if item.effect_kind == left]
                right_effects = [item for item in effects if item.effect_kind == right]
                for left_effect in left_effects:
                    for right_effect in right_effects:
                        if (
                            left_effect.target_type == right_effect.target_type
                            and left_effect.target_id == right_effect.target_id
                        ):
                            conflicts.add(
                                f"{left} conflicts with {right} on {left_effect.target_type}:{left_effect.target_id}"
                            )
    reset_targets = {item.target_id for item in effects if item.effect_kind == "change-reset-point"}
    if len(reset_targets) > 1:
        conflicts.add("multiple change-reset-point effects select different targets")
    return tuple(sorted(conflicts))


def _evaluate_rules(
    registry: OccurrenceRegistry,
    recurrence_id: str,
    occurrence_id: str,
    effective_at: str | None,
) -> RuleEvaluation:
    recurrence = registry._known(registry.recurrences, recurrence_id, "recurrence")
    occurrence = registry._known(registry.occurrences, occurrence_id, "occurrence")
    if occurrence.iteration_id is None:
        raise ValueError(f"Occurrence `{occurrence_id}` is not part of a recurrence iteration.")
    iteration = registry.iterations[occurrence.iteration_id]
    if iteration.recurrence_id != recurrence_id:
        raise ValueError(f"Occurrence `{occurrence_id}` does not belong to recurrence `{recurrence_id}`.")

    working: dict[str, dict] = {}
    indeterminate = False
    for rule in registry.rules_for_pattern(recurrence.pattern_id):
        applicability, app_detail = _rule_applicability_status(
            registry, rule, recurrence, iteration, occurrence, effective_at
        )
        evaluations: tuple[RuleConditionEvaluation, ...] = ()
        matched = False
        disposition = app_detail
        if applicability in {"applicable", "indeterminate"}:
            evaluations = tuple(
                _evaluate_rule_condition(registry, condition, recurrence, iteration, occurrence, effective_at)
                for condition in rule.conditions
            )
            statuses = [item.status for item in evaluations]
            if rule.condition_logic == "all":
                conditions_matched = all(status == "matched" for status in statuses)
                conditions_rejected = "not-matched" in statuses
                condition_indeterminate = "indeterminate" in statuses and "not-matched" not in statuses
            else:
                conditions_matched = "matched" in statuses
                conditions_rejected = not conditions_matched and "indeterminate" not in statuses
                condition_indeterminate = not conditions_matched and "indeterminate" in statuses
            if applicability == "indeterminate":
                if conditions_rejected:
                    disposition = "conditions did not match"
                else:
                    indeterminate = True
            else:
                matched = conditions_matched
                if condition_indeterminate:
                    indeterminate = True
                    disposition = "conditions indeterminate"
                else:
                    disposition = "conditions matched" if matched else "conditions did not match"
        working[rule.id] = {
            "rule": rule,
            "applicability": applicability,
            "matched": matched,
            "selected": False,
            "disposition": disposition,
            "conditions": evaluations,
        }

    matched_rules = [item["rule"] for item in working.values() if item["matched"]]
    replaced_groups = {
        rule.resolution_group
        for rule in matched_rules
        if rule.applicability.application_level == "execution-override" and rule.override_mode == "replace-group"
    }
    candidates: list[RecurrenceRule] = []
    for rule in matched_rules:
        if rule.applicability.application_level == "pattern-default" and rule.resolution_group in replaced_groups:
            working[rule.id]["disposition"] = "suppressed by execution override"
        else:
            candidates.append(rule)

    conflicts: set[str] = set()
    selected: list[RecurrenceRule] = []
    groups: dict[str, list[RecurrenceRule]] = {}
    for rule in candidates:
        groups.setdefault(rule.resolution_group, []).append(rule)
    for group_id, members in sorted(groups.items()):
        accumulating = [rule for rule in members if rule.selection_mode == "accumulate"]
        exclusive = [rule for rule in members if rule.selection_mode == "exclusive"]
        selected.extend(accumulating)
        if exclusive:
            maximum = max(rule.priority for rule in exclusive)
            leaders = sorted((rule for rule in exclusive if rule.priority == maximum), key=lambda item: item.id)
            signatures = {_effect_signature(rule) for rule in leaders}
            if len(signatures) > 1:
                conflicts.add(f"resolution group '{group_id}' has conflicting exclusive rules at priority {maximum}")
                for rule in leaders:
                    working[rule.id]["disposition"] = "conflicting top-priority exclusive rule"
            else:
                selected.append(leaders[0])
                for rule in leaders[1:]:
                    working[rule.id]["disposition"] = f"equivalent to selected rule `{leaders[0].id}`"
            for rule in exclusive:
                if rule.priority < maximum:
                    working[rule.id]["disposition"] = "lower-priority exclusive rule"

    selected_by_id = {rule.id: rule for rule in selected}
    effects, repetition_conflicts = _resolve_effects(selected, registry.effect_repetition_policies)
    conflicts.update(repetition_conflicts)
    conflicts.update(_effect_conflicts(registry, effects))
    for rule_id in selected_by_id:
        working[rule_id]["selected"] = True
        working[rule_id]["disposition"] = "selected"
    traces = tuple(
        RuleEvaluationTrace(
            rule.id,
            working[rule.id]["applicability"],
            working[rule.id]["matched"],
            working[rule.id]["selected"],
            working[rule.id]["disposition"],
            working[rule.id]["conditions"],
        )
        for rule in sorted(registry.rules_for_pattern(recurrence.pattern_id), key=lambda item: item.id)
    )
    status = "conflict" if conflicts else "indeterminate" if indeterminate else "selected" if selected else "no-match"
    execution_disposition = {
        "conflict": "blocked-conflict",
        "selected": "authorized",
        "indeterminate": "blocked-indeterminate",
        "no-match": "not-applicable",
    }[status]
    authorized_effects = effects if execution_disposition == "authorized" else ()
    return RuleEvaluation(
        status,
        recurrence_id,
        occurrence_id,
        tuple(sorted(selected_by_id)),
        effects,
        authorized_effects,
        execution_disposition,
        tuple(sorted(conflicts)),
        traces,
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
    *,
    schedules: dict[str, RecurrenceSchedule] | None = None,
    phases: dict[str, RecurrencePhase] | None = None,
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
        "recurrence-schedule": set(schedules or {}),
        "recurrence-phase": set(phases or {}),
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
    data = load_yaml_file(
        project.occurrences_registry, "occurrence registry", expected_schema_version=SUPPORTED_SCHEMA_VERSION
    )
    return parse_occurrence_registry(
        data,
        project.occurrences_registry,
        packs,
        chronology,
        subject_targets=subject_targets,
        payload_targets=payload_targets,
    )
