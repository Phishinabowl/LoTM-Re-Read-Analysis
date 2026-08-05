from __future__ import annotations

import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.chronology_config import load_chronology_registry, parse_chronology_registry
from knowledge_framework.occurrence_config import load_occurrence_registry, parse_occurrence_registry
from knowledge_framework.project_config import load_project_config, resolve_project_root
from knowledge_framework.resource_config import load_resource_config
from knowledge_framework.schema_pack_config import EffectPolicyDeclaration, load_schema_pack_registry
from knowledge_framework.source_config import load_source_registry
from knowledge_framework.strict_yaml import load_yaml_file


def set_path(data: object, path: str, value: object) -> None:
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    final = parts[-1]
    if isinstance(current, list):
        current[int(final)] = value
    else:
        current[final] = value


def ids(items) -> list[str]:
    return [item.id for item in items]


def with_semantic_extension(
    packs,
    additions: dict[str, tuple[str, ...]],
    target_compatibilities: tuple[tuple[str, str], ...],
    rule_compatibilities: tuple[tuple[str, str], ...],
    policies: tuple[EffectPolicyDeclaration, ...],
    incompatibilities: dict[tuple[str, str], str],
):
    controlled_values = dict(packs.controlled_values)
    for namespace, values in additions.items():
        controlled_values[namespace] = tuple(controlled_values.get(namespace, ())) + values
    effect_policies = dict(packs.effect_policies)
    effect_policies.update({policy.effect_kind: policy for policy in policies})
    effect_incompatibilities = dict(packs.effect_incompatibilities)
    effect_incompatibilities.update(incompatibilities)
    return replace(
        packs,
        controlled_values=controlled_values,
        effect_target_compatibilities=packs.effect_target_compatibilities.union(target_compatibilities),
        rule_effect_compatibilities=packs.rule_effect_compatibilities.union(rule_compatibilities),
        effect_policies=effect_policies,
        effect_incompatibilities=effect_incompatibilities,
    )


def effect_vectors(effects) -> list[list]:
    return [
        [
            effect.effect_kind,
            effect.target_type,
            effect.target_id,
            effect.repetition_policy,
            effect.contribution_count,
            effect.proposed_execution_count,
            list(effect.contributing_rule_ids),
            list(effect.contributing_effect_ids),
        ]
        for effect in effects
    ]


def synthetic_rule(
    rule_id: str,
    rule_kind: str,
    effect_kind: str,
    target_id: str,
    occurrence_template: str,
) -> dict:
    return {
        "id": rule_id,
        "label": f"Synthetic {effect_kind} extension",
        "pattern_id": "outer-loop-pattern",
        "rule_kind": rule_kind,
        "condition_logic": "all",
        "applicability": {
            "application_level": "pattern-default",
            "recurrence_ids": [],
            "phase_ids": [],
            "branch_ids": [],
            "min_iteration_ordinal": 2,
            "max_iteration_ordinal": 2,
            "chronology_window": None,
            "effective_window": None,
        },
        "priority": 10,
        "resolution_group": f"synthetic-{effect_kind}",
        "selection_mode": "accumulate",
        "override_mode": "inherit",
        "conditions": [
            {
                "id": f"{rule_id}-condition",
                "condition_kind": "occurrence-reached",
                "target_type": "occurrence-template",
                "target_id": occurrence_template,
                "expected_value": "occurred",
                "subject_type": None,
                "subject_id": None,
                "state_kind": None,
                "track_id": None,
                "comparison_value": None,
            }
        ],
        "effects": [
            {
                "id": f"{rule_id}-effect",
                "effect_kind": effect_kind,
                "target_type": "recurrence-pattern",
                "target_id": target_id,
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate occurrence and recurrence registry behavior and cross-runtime fixtures."
    )
    parser.add_argument("--root", help="Repository root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()

    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    resources = load_resource_config(project)
    sources = load_source_registry(project, resources, packs)
    chronology = load_chronology_registry(
        project, packs, work_ids=set(sources.works), continuity_ids=set(sources.continuities)
    )
    registry = load_occurrence_registry(project, packs, chronology)

    fixture_root = root / "Framework" / "Data" / "Occurrence"
    chronology_fixture_path = root / "Framework" / "Data" / "Chronology" / "valid-registry.yaml"
    chronology_fixture_data = load_yaml_file(chronology_fixture_path, "chronology fixture", expected_schema_version=2)
    chronology_fixture_data["contexts"] = [
        {
            "id": "recipient-context",
            "label": "Recipient Context",
            "coordinate_system_id": "civil-year",
            "role": "story",
            "continuity_ids": [],
            "work_ids": ["fixture-work"],
            "branch_id": "main",
        },
        {
            "id": "agent-context",
            "label": "Agent Context",
            "coordinate_system_id": "civil-year",
            "role": "time-travel-origin",
            "continuity_ids": [],
            "work_ids": ["fixture-work"],
            "branch_id": "main",
        },
    ]
    chronology_fixture_data["context_relations"] = []
    chronology_fixture = parse_chronology_registry(
        chronology_fixture_data,
        chronology_fixture_path,
        packs,
        work_ids={"fixture-work"},
        continuity_ids=set(),
    )
    fixture_path = fixture_root / "valid-registry.yaml"
    fixture_data = load_yaml_file(fixture_path, "occurrence fixture", expected_schema_version=9)
    payload_targets = {
        "state-record": {"protagonist-health"},
        "credential-record": {"protagonist-qualification"},
    }
    fixture = parse_occurrence_registry(
        fixture_data,
        fixture_path,
        packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    )
    fixture.validate_branch_continuity_targets({"fixture-continuity"})
    try:
        fixture.validate_branch_continuity_targets(set())
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown branch continuity membership unexpectedly validated.")
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    for branch_id, expected in expectations["branch_state_histories"].items():
        if ids(fixture.branch_state_history(branch_id)) != expected:
            raise AssertionError(f"Unexpected branch-state history for `{branch_id}`.")
    for branch_id, boundary, expected in expectations["branch_state_at"]:
        state = fixture.branch_state_at(branch_id, boundary)
        if (state.id if state else None) != expected:
            raise AssertionError(f"Unexpected branch state for `{branch_id}` at ordinal {boundary}.")
    try:
        fixture.branch_state_history("missing-branch")
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown branch-state history query unexpectedly succeeded.")
    try:
        fixture.branch_state_at("main", -1)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative branch-state boundary unexpectedly succeeded.")
    for iteration_id, expected in expectations["iteration_occurrences"].items():
        if ids(fixture.occurrences_for_iteration(iteration_id)) != expected:
            raise AssertionError(f"Unexpected occurrence order for iteration `{iteration_id}`.")
    for recurrence_id, expected in expectations["recurrence_cardinalities"].items():
        if ids(fixture.cardinalities_for_recurrence(recurrence_id)) != expected:
            raise AssertionError(f"Unexpected cardinalities for recurrence `{recurrence_id}`.")
    for position_id, expected in expectations["position_occurrences"].items():
        if ids(fixture.occurrences_at_position(position_id)) != expected:
            raise AssertionError(f"Unexpected occurrences at position `{position_id}`.")
    for occurrence_id, expected in expectations["occurrence_participations"].items():
        if ids(fixture.participations_for_occurrence(occurrence_id)) != expected:
            raise AssertionError(f"Unexpected participations for occurrence `{occurrence_id}`.")
    for key, expected in expectations["subject_participations"].items():
        subject_type, subject_id = key.split("|", 1)
        if ids(fixture.participations_for_subject(subject_type, subject_id)) != expected:
            raise AssertionError(f"Unexpected participations for subject `{key}`.")
    for key, expected in expectations["track_occurrence_entries"].items():
        track_id, occurrence_id = key.split("|", 1)
        if ids(fixture.entries_for_occurrence_on_track(track_id, occurrence_id)) != expected:
            raise AssertionError(f"Unexpected entries for `{occurrence_id}` on `{track_id}`.")
    for track_id, entry_id, expected_previous, expected_next in expectations["track_entry_neighbors"]:
        previous = fixture.previous_track_entry(track_id, entry_id)
        following = fixture.next_track_entry(track_id, entry_id)
        if (previous.id if previous else None) != expected_previous or (
            following.id if following else None
        ) != expected_next:
            raise AssertionError(f"Unexpected track-entry neighbors for `{entry_id}`.")
    for track_id, occurrence_id, expected_error in expectations["ambiguous_occurrence_neighbors"]:
        try:
            fixture.previous_on_track(track_id, occurrence_id)
        except ValueError as exc:
            if str(exc) != expected_error:
                raise AssertionError(f"Unexpected ambiguous occurrence error: {exc}") from exc
        else:
            raise AssertionError(f"Ambiguous occurrence `{occurrence_id}` unexpectedly resolved on `{track_id}`.")
    for key, expected in expectations["iteration_track_occurrences"].items():
        iteration_id, track_id = key.split("|", 1)
        if ids(fixture.occurrences_for_iteration_on_track(iteration_id, track_id)) != expected:
            raise AssertionError(f"Unexpected track occurrence order for `{iteration_id}` on `{track_id}`.")
    for track_id, iteration_id, expected_previous, expected_next in expectations["track_iteration_boundaries"]:
        previous = fixture.previous_before_iteration(track_id, iteration_id)
        following = fixture.next_after_iteration(track_id, iteration_id)
        if (previous.id if previous else None) != expected_previous or (
            following.id if following else None
        ) != expected_next:
            raise AssertionError(f"Unexpected track boundaries for `{iteration_id}` on `{track_id}`.")
    for track_id, occurrence_id, expected_previous, expected_next in expectations["track_neighbors"]:
        previous = fixture.previous_on_track(track_id, occurrence_id)
        following = fixture.next_on_track(track_id, occurrence_id)
        if (previous.id if previous else None) != expected_previous or (
            following.id if following else None
        ) != expected_next:
            raise AssertionError(f"Unexpected neighbors for `{occurrence_id}` on `{track_id}`.")
    for iteration_id, expected in expectations["carryovers_into"].items():
        if ids(fixture.carryovers_into(iteration_id)) != expected:
            raise AssertionError(f"Unexpected carryover into iteration `{iteration_id}`.")
    for occurrence_id, expected in expectations["occurrence_recurrences"].items():
        recurrence = fixture.recurrence_for_occurrence(occurrence_id)
        if (recurrence.id if recurrence else None) != expected:
            raise AssertionError(f"Unexpected recurrence for occurrence `{occurrence_id}`.")
    for occurrence_id, expected in expectations["occurrence_outcomes"].items():
        if ids(fixture.outcomes_for_occurrence(occurrence_id)) != expected:
            raise AssertionError(f"Unexpected outcomes for occurrence `{occurrence_id}`.")
    for pattern_id, expected in expectations["pattern_rules"].items():
        if ids(fixture.rules_for_pattern(pattern_id)) != expected:
            raise AssertionError(f"Unexpected rules for recurrence pattern `{pattern_id}`.")
    for iteration_id, expected in expectations["iteration_phases"].items():
        phase = fixture.phase_for_iteration(iteration_id)
        if (phase.id if phase else None) != expected:
            raise AssertionError(f"Unexpected recurrence phase for `{iteration_id}`.")
    for schedule_id, ordinal, expected in expectations["schedule_values"]:
        if fixture.expected_schedule_value(schedule_id, ordinal) != expected:
            raise AssertionError(f"Unexpected schedule value for `{schedule_id}` ordinal {ordinal}.")
    for schedule_id, ordinal, expected_error in expectations["schedule_errors"]:
        try:
            fixture.expected_schedule_value(schedule_id, ordinal)
        except ValueError as exc:
            if str(exc) != expected_error:
                raise AssertionError(f"Unexpected schedule error for `{schedule_id}`: {exc}") from exc
        else:
            raise AssertionError(f"Schedule `{schedule_id}` ordinal {ordinal} unexpectedly projected.")
    for schedule_id, iteration_id, occurrence_id, effective_at, expected in expectations["schedule_matches"]:
        if fixture.schedule_match(schedule_id, iteration_id, occurrence_id, effective_at) != expected:
            raise AssertionError(f"Unexpected schedule match for `{schedule_id}` at `{occurrence_id}`.")
    for recurrence_id, occurrence_id, effective_at, status, selected, effect_kinds, conflicts in expectations[
        "rule_evaluations"
    ]:
        evaluation = fixture.evaluate_rules(recurrence_id, occurrence_id, effective_at=effective_at)
        if hasattr(evaluation, "effects"):
            raise AssertionError("Unsafe legacy rule-evaluation `effects` alias remains available.")
        if (
            evaluation.status != status
            or list(evaluation.selected_rule_ids) != selected
            or [effect.effect_kind for effect in evaluation.proposed_effects] != effect_kinds
            or [effect.effect_kind for effect in evaluation.authorized_effects]
            != (effect_kinds if status == "selected" else [])
            or evaluation.execution_disposition
            != {
                "selected": "authorized",
                "conflict": "blocked-conflict",
                "indeterminate": "blocked-indeterminate",
                "no-match": "not-applicable",
            }[status]
            or list(evaluation.conflicts) != conflicts
        ):
            raise AssertionError(f"Unexpected rule evaluation for `{recurrence_id}` at `{occurrence_id}`: {evaluation}")
    for recurrence_id, occurrence_id, effective_at, expected in expectations["resolved_effects"]:
        evaluation = fixture.evaluate_rules(recurrence_id, occurrence_id, effective_at=effective_at)
        if effect_vectors(evaluation.proposed_effects) != expected:
            raise AssertionError(f"Unexpected proposed effects at `{occurrence_id}`: {evaluation.proposed_effects}")
    for recurrence_id, occurrence_id, effective_at, rule_id, disposition in expectations["trace_dispositions"]:
        evaluation = fixture.evaluate_rules(recurrence_id, occurrence_id, effective_at=effective_at)
        trace = next(item for item in evaluation.traces if item.rule_id == rule_id)
        if trace.disposition != disposition:
            raise AssertionError(f"Unexpected trace disposition for rule `{rule_id}`: {trace.disposition}")
    for key, expected in expectations["subject_state_transitions"].items():
        subject_type, subject_id = key.split("|", 1)
        if ids(fixture.state_transitions_for_subject(subject_type, subject_id)) != expected:
            raise AssertionError(f"Unexpected state transitions for `{key}`.")
    for scale_id, expected in expectations["state_scales"].items():
        scale = fixture.state_scales[scale_id]
        actual = [
            scale.kind,
            [level.id for level in scale.levels],
            scale.minimum,
            scale.maximum,
            scale.unit,
        ]
        if actual != expected:
            raise AssertionError(f"Unexpected state scale `{scale_id}`: {actual}")
    state_transitions = {transition.id: transition for transition in fixture.state_transitions}
    for transition_id, expected in expectations["state_snapshots"].items():
        transition = state_transitions[transition_id]
        actual = [
            transition.state_profile,
            transition.change_shape,
            transition.prior_availability,
            transition.resulting_availability,
            transition.prior_completeness,
            transition.resulting_completeness,
            transition.prior_attitude,
            transition.resulting_attitude,
            (
                f"{transition.prior_capability.scale_id}:{transition.prior_capability.value}"
                if transition.prior_capability
                else None
            ),
            (
                f"{transition.resulting_capability.scale_id}:{transition.resulting_capability.value}"
                if transition.resulting_capability
                else None
            ),
        ]
        if actual != expected:
            raise AssertionError(f"Unexpected state snapshot for `{transition_id}`: {actual}")
    for track_id, occurrence_id, payload_type, payload_id, state_kind, expected in expectations["state_at"]:
        state = fixture.state_at(track_id, occurrence_id, payload_type, payload_id, state_kind)
        if (state.id if state else None) != expected:
            raise AssertionError(f"Unexpected state at `{occurrence_id}` on `{track_id}`.")

    invalid_cases = json.loads((fixture_root / "invalid-cases.json").read_text(encoding="utf-8"))
    for case in invalid_cases:
        invalid = copy.deepcopy(fixture_data)
        for change in case["changes"]:
            set_path(invalid, change["path"], change["value"])
        try:
            parse_occurrence_registry(
                invalid,
                fixture_path,
                packs,
                chronology_fixture,
                subject_targets={"character": {"protagonist", "observer"}},
                payload_targets={
                    "state-record": {"protagonist-health"},
                    "credential-record": {"protagonist-qualification"},
                },
            )
        except ValueError:
            continue
        raise AssertionError(f"Malformed occurrence case unexpectedly loaded: {case['name']}")

    scale_count = 128
    scale_probe = copy.deepcopy(fixture_data)
    scale_probe["tracks"]["scale-observer-experience"] = {
        "label": "Scale Observer Experience",
        "kind": "observation",
        "subject_type": "character",
        "subject_id": "observer",
    }
    for index in range(scale_count):
        cardinality_id = f"scale-cardinality-{index:03d}"
        scale_probe["recurrence_cardinalities"][cardinality_id] = {
            "label": f"Scale cardinality {index:03d}",
            "recurrence_id": "inner-loop",
            "cardinality_kind": "minimum",
            "minimum_count": 1000 + index,
            "maximum_count": None,
            "coverage_mode": "unmaterialized",
            "representative_iteration_ids": [],
            "certainty": "uncertain",
        }
        occurrence_id = f"scale-occurrence-{index:03d}"
        participation_id = f"scale-participation-{index:03d}"
        entry_id = f"scale-entry-{index:03d}"
        scale_probe["occurrences"][occurrence_id] = {
            "template_id": "intervention",
            "label": f"Scale occurrence {index:03d}",
            "iteration_id": None,
            "branch_id": "main",
            "bindings": [],
        }
        scale_probe["occurrence_participations"][participation_id] = {
            "occurrence_id": occurrence_id,
            "subject_type": "character",
            "subject_id": "observer",
            "role": "reviewer",
            "perspective": "reconstructed",
            "status": "completed",
            "chronology_context_id": None,
        }
        scale_probe["track_entries"][entry_id] = {
            "track_id": "scale-observer-experience",
            "participation_id": participation_id,
            "ordinal": index + 1,
        }
        scale_probe["branch_state_transitions"].append(
            {
                "id": f"scale-branch-state-{index:03d}",
                "label": f"Scale branch state {index:03d}",
                "branch_id": "main",
                "ordinal": index + 3,
                "change_kind": "preserve",
                "prior_state": "preserved",
                "resulting_state": "preserved",
                "activation_occurrence_id": "restored-main",
                "trigger_transition_id": None,
                "certainty": "exact",
            }
        )
    scale_registry = parse_occurrence_registry(
        scale_probe,
        fixture_path,
        packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    )
    if len(scale_registry.cardinalities_for_recurrence("inner-loop")) != 5 + scale_count:
        raise AssertionError("Generated recurrence-cardinality scale probe did not retain every record.")
    if (
        len(scale_registry.participations_for_subject("character", "observer")) != 7 + scale_count
        or len(scale_registry.tracks["scale-observer-experience"].entry_ids) != scale_count
    ):
        raise AssertionError("Generated occurrence-participation scale probe did not retain every record.")
    if len(scale_registry.branch_state_history("main")) != 2 + scale_count:
        raise AssertionError("Generated branch-state scale probe did not retain every record.")

    mixed_indeterminate_probe = copy.deepcopy(fixture_data)
    mixed_rule = copy.deepcopy(mixed_indeterminate_probe["rules"][0])
    mixed_rule["id"] = "indeterminate-reset-rule"
    mixed_rule["label"] = "Indeterminate reset policy"
    mixed_rule["resolution_group"] = "indeterminate-control"
    mixed_rule["applicability"]["effective_window"] = copy.deepcopy(
        fixture_data["rules"][3]["applicability"]["effective_window"]
    )
    mixed_rule["conditions"][0]["id"] = "indeterminate-reset-reached"
    mixed_rule["conditions"][1]["id"] = "indeterminate-reset-ordinal"
    mixed_rule["effects"][0]["id"] = "indeterminate-reset-advances"
    mixed_indeterminate_probe["rules"].append(mixed_rule)
    mixed_indeterminate_evaluation = parse_occurrence_registry(
        mixed_indeterminate_probe,
        fixture_path,
        packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    ).evaluate_rules("outer-loop", "reset-one")
    if (
        mixed_indeterminate_evaluation.status != "indeterminate"
        or mixed_indeterminate_evaluation.execution_disposition != "blocked-indeterminate"
        or list(mixed_indeterminate_evaluation.selected_rule_ids) != ["outer-reset-rule"]
        or [effect.effect_kind for effect in mixed_indeterminate_evaluation.proposed_effects] != ["advance-iteration"]
        or mixed_indeterminate_evaluation.authorized_effects
    ):
        raise AssertionError(
            f"Mixed selected/indeterminate evaluation did not fail closed: {mixed_indeterminate_evaluation}"
        )

    extension_packs = with_semantic_extension(
        packs,
        {
            "occurrence.rule-kind": ("pause", "signal"),
            "occurrence.rule-effect-kind": ("pause-recurrence", "signal-recurrence"),
        },
        (
            ("pause-recurrence", "recurrence-pattern"),
            ("signal-recurrence", "recurrence-pattern"),
        ),
        (("pause", "pause-recurrence"), ("signal", "signal-recurrence")),
        (
            EffectPolicyDeclaration("pause-recurrence", "idempotent", "owning-pattern"),
            EffectPolicyDeclaration("signal-recurrence", "idempotent", "external-pattern"),
        ),
        {tuple(sorted(("advance-iteration", "pause-recurrence"))): "same-target"},
    )
    owning_probe = copy.deepcopy(fixture_data)
    owning_probe["rules"].append(
        synthetic_rule("synthetic-pause-rule", "pause", "pause-recurrence", "outer-loop-pattern", "reset")
    )
    owning_registry = parse_occurrence_registry(
        owning_probe,
        fixture_path,
        extension_packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    )
    owning_evaluation = owning_registry.evaluate_rules("outer-loop", "reset-two")
    if (
        owning_evaluation.status != "conflict"
        or list(owning_evaluation.selected_rule_ids) != ["outer-reset-rule", "synthetic-pause-rule"]
        or list(owning_evaluation.conflicts)
        != ["advance-iteration conflicts with pause-recurrence on recurrence-pattern:outer-loop-pattern"]
    ):
        raise AssertionError(f"Unexpected owning-pattern extension evaluation: {owning_evaluation}")

    foreign_owning_probe = copy.deepcopy(owning_probe)
    foreign_owning_probe["rules"][-1]["effects"][0]["target_id"] = "inner-loop-pattern"
    try:
        parse_occurrence_registry(
            foreign_owning_probe,
            fixture_path,
            extension_packs,
            chronology_fixture,
            subject_targets={"character": {"protagonist", "observer"}},
            payload_targets=payload_targets,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Owning-pattern extension unexpectedly accepted a foreign pattern target.")

    external_probe = copy.deepcopy(fixture_data)
    external_probe["rules"].append(
        synthetic_rule("synthetic-signal-rule", "signal", "signal-recurrence", "inner-loop-pattern", "bell")
    )
    external_registry = parse_occurrence_registry(
        external_probe,
        fixture_path,
        extension_packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    )
    external_evaluation = external_registry.evaluate_rules("outer-loop", "bell-two")
    if (
        external_evaluation.status != "selected"
        or list(external_evaluation.selected_rule_ids) != ["synthetic-signal-rule"]
        or [effect.target_id for effect in external_evaluation.authorized_effects] != ["inner-loop-pattern"]
    ):
        raise AssertionError(f"Unexpected external-pattern extension evaluation: {external_evaluation}")

    duplicate_probe = copy.deepcopy(fixture_data)
    first_signal = synthetic_rule("first-signal-rule", "signal", "signal-recurrence", "inner-loop-pattern", "bell")
    second_signal = synthetic_rule("second-signal-rule", "signal", "signal-recurrence", "inner-loop-pattern", "bell")
    first_signal["resolution_group"] = "first-signal-group"
    second_signal["resolution_group"] = "second-signal-group"
    duplicate_probe["rules"].extend((first_signal, second_signal))
    duplicate_evaluation = parse_occurrence_registry(
        duplicate_probe,
        fixture_path,
        extension_packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    ).evaluate_rules("outer-loop", "bell-two")
    if (
        len(duplicate_evaluation.authorized_effects) != 1
        or duplicate_evaluation.authorized_effects[0].contribution_count != 2
        or duplicate_evaluation.authorized_effects[0].proposed_execution_count != 1
        or list(duplicate_evaluation.authorized_effects[0].contributing_rule_ids)
        != ["first-signal-rule", "second-signal-rule"]
    ):
        raise AssertionError(f"Unexpected idempotent effect resolution: {duplicate_evaluation}")

    for policy, expected_status, expected_execution_count, expected_conflicts in (
        ("accumulating", "selected", 2, []),
        (
            "invalid",
            "conflict",
            0,
            ["duplicate signal-recurrence effect on recurrence-pattern:inner-loop-pattern is invalid"],
        ),
    ):
        policies = dict(extension_packs.effect_policies)
        policies["signal-recurrence"] = EffectPolicyDeclaration("signal-recurrence", policy, "external-pattern")
        policy_evaluation = parse_occurrence_registry(
            duplicate_probe,
            fixture_path,
            replace(extension_packs, effect_policies=policies),
            chronology_fixture,
            subject_targets={"character": {"protagonist", "observer"}},
            payload_targets=payload_targets,
        ).evaluate_rules("outer-loop", "bell-two")
        if (
            policy_evaluation.status != expected_status
            or policy_evaluation.proposed_effects[0].proposed_execution_count != expected_execution_count
            or bool(policy_evaluation.authorized_effects) != (expected_status == "selected")
            or list(policy_evaluation.conflicts) != expected_conflicts
        ):
            raise AssertionError(f"Unexpected `{policy}` effect resolution: {policy_evaluation}")

    scoped_probe = copy.deepcopy(fixture_data)
    scoped_probe["rules"].append(
        synthetic_rule("cross-target-pause-rule", "pause", "pause-recurrence", "inner-loop-pattern", "reset")
    )
    scoped_policies = dict(extension_packs.effect_policies)
    scoped_policies["pause-recurrence"] = EffectPolicyDeclaration("pause-recurrence", "idempotent", "external-pattern")
    scoped_packs = replace(extension_packs, effect_policies=scoped_policies)
    scoped_evaluation = parse_occurrence_registry(
        scoped_probe,
        fixture_path,
        scoped_packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    ).evaluate_rules("outer-loop", "reset-two")
    if scoped_evaluation.status != "selected" or scoped_evaluation.conflicts:
        raise AssertionError(f"Cross-target same-target pair unexpectedly conflicted: {scoped_evaluation}")

    global_incompatibilities = dict(scoped_packs.effect_incompatibilities)
    global_incompatibilities[tuple(sorted(("advance-iteration", "pause-recurrence")))] = "global"
    global_evaluation = parse_occurrence_registry(
        scoped_probe,
        fixture_path,
        replace(scoped_packs, effect_incompatibilities=global_incompatibilities),
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets=payload_targets,
    ).evaluate_rules("outer-loop", "reset-two")
    if (
        list(global_evaluation.conflicts) != ["advance-iteration conflicts with pause-recurrence globally"]
        or global_evaluation.execution_disposition != "blocked-conflict"
        or global_evaluation.authorized_effects
        or len(global_evaluation.proposed_effects) != 2
    ):
        raise AssertionError(f"Global incompatibility scope was not enforced: {global_evaluation}")

    summary = {
        "schema_version": registry.schema_version,
        "branches": len(registry.branches),
        "branch_state_transitions": len(registry.branch_state_transitions),
        "templates": len(registry.templates),
        "recurrence_patterns": len(registry.recurrence_patterns),
        "recurrences": len(registry.recurrences),
        "iterations": len(registry.iterations),
        "recurrence_cardinalities": len(registry.recurrence_cardinalities),
        "phases": len(registry.phases),
        "schedules": len(registry.schedules),
        "occurrences": len(registry.occurrences),
        "occurrence_participations": len(registry.occurrence_participations),
        "tracks": len(registry.tracks),
        "track_entries": len(registry.track_entries),
        "transitions": len(registry.transitions),
        "causal_relations": len(registry.causal_relations),
        "outcomes": len(registry.outcomes),
        "rules": len(registry.rules),
        "state_scales": len(registry.state_scales),
        "state_transitions": len(registry.state_transitions),
        "carryovers": len(registry.carryovers),
        "fixture_queries": (
            len(expectations["iteration_occurrences"])
            + len(expectations["branch_state_histories"])
            + len(expectations["branch_state_at"])
            + len(expectations["recurrence_cardinalities"])
            + len(expectations["position_occurrences"])
            + len(expectations["occurrence_participations"])
            + len(expectations["subject_participations"])
            + len(expectations["track_occurrence_entries"])
            + len(expectations["track_entry_neighbors"]) * 2
            + len(expectations["ambiguous_occurrence_neighbors"])
            + len(expectations["iteration_track_occurrences"])
            + len(expectations["track_iteration_boundaries"]) * 2
            + len(expectations["track_neighbors"]) * 2
            + len(expectations["carryovers_into"])
            + len(expectations["occurrence_recurrences"])
            + len(expectations["occurrence_outcomes"])
            + len(expectations["pattern_rules"])
            + len(expectations["iteration_phases"])
            + len(expectations["schedule_values"])
            + len(expectations["schedule_errors"])
            + len(expectations["schedule_matches"])
            + len(expectations["rule_evaluations"])
            + len(expectations["resolved_effects"])
            + len(expectations["trace_dispositions"])
            + len(expectations["subject_state_transitions"])
            + len(expectations["state_scales"])
            + len(expectations["state_snapshots"])
            + len(expectations["state_at"])
            + 18
        ),
        "invalid_cases": len(invalid_cases),
        "scale_cardinalities": scale_count,
        "scale_participations": scale_count,
        "scale_branch_state_transitions": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Occurrence validation passed: "
            f"schema {summary['schema_version']}, {summary['branches']} project branch, "
            f"{summary['fixture_queries']} fixture queries, and {summary['invalid_cases']} malformed cases."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
