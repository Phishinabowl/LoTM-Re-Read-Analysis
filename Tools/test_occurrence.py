from __future__ import annotations

import argparse
import copy
from dataclasses import replace
import json

from chronology_config import load_chronology_registry, parse_chronology_registry
from occurrence_config import load_occurrence_registry, parse_occurrence_registry
from project_config import load_project_config, resolve_project_root
from resource_config import load_resource_config
from schema_pack_config import load_schema_pack_registry, validate_occurrence_semantic_declarations
from source_config import load_source_registry
from strict_yaml import load_yaml_file


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


def with_controlled_values(packs, additions: dict[str, tuple[str, ...]]):
    controlled_values = dict(packs.controlled_values)
    for namespace, values in additions.items():
        controlled_values[namespace] = tuple(controlled_values.get(namespace, ())) + values
    validate_occurrence_semantic_declarations(controlled_values)
    return replace(packs, controlled_values=controlled_values)


def effect_vectors(effects) -> list[list]:
    return [
        [
            effect.effect_kind,
            effect.target_type,
            effect.target_id,
            effect.repetition_policy,
            effect.contribution_count,
            effect.execution_count,
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

    root = resolve_project_root(args.root)
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
    chronology_fixture = parse_chronology_registry(
        load_yaml_file(chronology_fixture_path, "chronology fixture", expected_schema_version=1),
        chronology_fixture_path,
        packs,
        work_ids=set(),
        continuity_ids=set(),
    )
    fixture_path = fixture_root / "valid-registry.yaml"
    fixture_data = load_yaml_file(fixture_path, "occurrence fixture", expected_schema_version=4)
    fixture = parse_occurrence_registry(
        fixture_data,
        fixture_path,
        packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets={"state-record": {"protagonist-health"}},
    )
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    for iteration_id, expected in expectations["iteration_occurrences"].items():
        if ids(fixture.occurrences_for_iteration(iteration_id)) != expected:
            raise AssertionError(f"Unexpected occurrence order for iteration `{iteration_id}`.")
    for position_id, expected in expectations["position_occurrences"].items():
        if ids(fixture.occurrences_at_position(position_id)) != expected:
            raise AssertionError(f"Unexpected occurrences at position `{position_id}`.")
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
        if (
            evaluation.status != status
            or list(evaluation.selected_rule_ids) != selected
            or [effect.effect_kind for effect in evaluation.effects] != effect_kinds
            or list(evaluation.conflicts) != conflicts
        ):
            raise AssertionError(f"Unexpected rule evaluation for `{recurrence_id}` at `{occurrence_id}`: {evaluation}")
    for recurrence_id, occurrence_id, effective_at, expected in expectations["resolved_effects"]:
        evaluation = fixture.evaluate_rules(recurrence_id, occurrence_id, effective_at=effective_at)
        if effect_vectors(evaluation.effects) != expected:
            raise AssertionError(f"Unexpected resolved effects at `{occurrence_id}`: {evaluation.effects}")
    for recurrence_id, occurrence_id, effective_at, rule_id, disposition in expectations["trace_dispositions"]:
        evaluation = fixture.evaluate_rules(recurrence_id, occurrence_id, effective_at=effective_at)
        trace = next(item for item in evaluation.traces if item.rule_id == rule_id)
        if trace.disposition != disposition:
            raise AssertionError(f"Unexpected trace disposition for rule `{rule_id}`: {trace.disposition}")
    for key, expected in expectations["subject_state_transitions"].items():
        subject_type, subject_id = key.split("|", 1)
        if ids(fixture.state_transitions_for_subject(subject_type, subject_id)) != expected:
            raise AssertionError(f"Unexpected state transitions for `{key}`.")
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
                payload_targets={"state-record": {"protagonist-health"}},
            )
        except ValueError:
            continue
        raise AssertionError(f"Malformed occurrence case unexpectedly loaded: {case['name']}")

    extension_packs = with_controlled_values(
        packs,
        {
            "occurrence.rule-kind": ("pause", "signal"),
            "occurrence.rule-effect-kind": ("pause-recurrence", "signal-recurrence"),
            "occurrence.rule-effect-kind-target-type": (
                "pause-recurrence-uses-recurrence-pattern",
                "signal-recurrence-uses-recurrence-pattern",
            ),
            "occurrence.rule-kind-effect-kind": (
                "pause-uses-pause-recurrence",
                "signal-uses-signal-recurrence",
            ),
            "occurrence.rule-effect-pattern-scope": (
                "pause-recurrence-uses-owning-pattern",
                "signal-recurrence-allows-external-pattern",
            ),
            "occurrence.rule-effect-repetition-policy": (
                "pause-recurrence-uses-idempotent",
                "signal-recurrence-uses-idempotent",
            ),
            "occurrence.rule-effect-same-target-incompatibility-pair": ("advance-iteration-with-pause-recurrence",),
        },
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
        payload_targets={"state-record": {"protagonist-health"}},
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
            payload_targets={"state-record": {"protagonist-health"}},
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
        payload_targets={"state-record": {"protagonist-health"}},
    )
    external_evaluation = external_registry.evaluate_rules("outer-loop", "bell-two")
    if (
        external_evaluation.status != "selected"
        or list(external_evaluation.selected_rule_ids) != ["synthetic-signal-rule"]
        or [effect.target_id for effect in external_evaluation.effects] != ["inner-loop-pattern"]
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
        payload_targets={"state-record": {"protagonist-health"}},
    ).evaluate_rules("outer-loop", "bell-two")
    if (
        len(duplicate_evaluation.effects) != 1
        or duplicate_evaluation.effects[0].contribution_count != 2
        or duplicate_evaluation.effects[0].execution_count != 1
        or list(duplicate_evaluation.effects[0].contributing_rule_ids) != ["first-signal-rule", "second-signal-rule"]
    ):
        raise AssertionError(f"Unexpected idempotent effect resolution: {duplicate_evaluation.effects}")

    for policy, expected_status, expected_execution_count, expected_conflicts in (
        ("accumulating", "selected", 2, []),
        (
            "invalid",
            "conflict",
            0,
            ["duplicate signal-recurrence effect on recurrence-pattern:inner-loop-pattern is invalid"],
        ),
    ):
        policy_values = dict(extension_packs.controlled_values)
        policy_values["occurrence.rule-effect-repetition-policy"] = tuple(
            value
            for value in extension_packs.controlled_values["occurrence.rule-effect-repetition-policy"]
            if value != "signal-recurrence-uses-idempotent"
        ) + (f"signal-recurrence-uses-{policy}",)
        validate_occurrence_semantic_declarations(policy_values)
        policy_evaluation = parse_occurrence_registry(
            duplicate_probe,
            fixture_path,
            replace(extension_packs, controlled_values=policy_values),
            chronology_fixture,
            subject_targets={"character": {"protagonist", "observer"}},
            payload_targets={"state-record": {"protagonist-health"}},
        ).evaluate_rules("outer-loop", "bell-two")
        if (
            policy_evaluation.status != expected_status
            or policy_evaluation.effects[0].execution_count != expected_execution_count
            or list(policy_evaluation.conflicts) != expected_conflicts
        ):
            raise AssertionError(f"Unexpected `{policy}` effect resolution: {policy_evaluation}")

    scoped_probe = copy.deepcopy(fixture_data)
    scoped_probe["rules"].append(
        synthetic_rule("cross-target-pause-rule", "pause", "pause-recurrence", "inner-loop-pattern", "reset")
    )
    scoped_values = dict(extension_packs.controlled_values)
    scoped_values["occurrence.rule-effect-pattern-scope"] = tuple(
        value
        for value in extension_packs.controlled_values["occurrence.rule-effect-pattern-scope"]
        if value != "pause-recurrence-uses-owning-pattern"
    ) + ("pause-recurrence-allows-external-pattern",)
    validate_occurrence_semantic_declarations(scoped_values)
    scoped_packs = replace(extension_packs, controlled_values=scoped_values)
    scoped_evaluation = parse_occurrence_registry(
        scoped_probe,
        fixture_path,
        scoped_packs,
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets={"state-record": {"protagonist-health"}},
    ).evaluate_rules("outer-loop", "reset-two")
    if scoped_evaluation.status != "selected" or scoped_evaluation.conflicts:
        raise AssertionError(f"Cross-target same-target pair unexpectedly conflicted: {scoped_evaluation}")

    global_values = dict(scoped_values)
    global_values["occurrence.rule-effect-same-target-incompatibility-pair"] = (
        "advance-iteration-with-terminate-recurrence",
    )
    global_values["occurrence.rule-effect-global-incompatibility-pair"] = ("advance-iteration-with-pause-recurrence",)
    validate_occurrence_semantic_declarations(global_values)
    global_evaluation = parse_occurrence_registry(
        scoped_probe,
        fixture_path,
        replace(scoped_packs, controlled_values=global_values),
        chronology_fixture,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets={"state-record": {"protagonist-health"}},
    ).evaluate_rules("outer-loop", "reset-two")
    if list(global_evaluation.conflicts) != ["advance-iteration conflicts with pause-recurrence globally"]:
        raise AssertionError(f"Global incompatibility scope was not enforced: {global_evaluation}")

    declaration_failures = [
        (
            "reversed pair",
            "occurrence.rule-effect-same-target-incompatibility-pair",
            ("pause-recurrence-with-advance-iteration",),
        ),
        (
            "unknown pair",
            "occurrence.rule-effect-same-target-incompatibility-pair",
            ("advance-iteration-with-unknown-effect",),
        ),
        ("orphan scope", "occurrence.rule-effect-pattern-scope", ("unknown-effect-uses-owning-pattern",)),
        (
            "ambiguous repetition",
            "occurrence.rule-effect-repetition-policy",
            tuple(extension_packs.controlled_values["occurrence.rule-effect-repetition-policy"])
            + ("pause-recurrence-uses-accumulating",),
        ),
        (
            "missing repetition",
            "occurrence.rule-effect-repetition-policy",
            tuple(
                value
                for value in extension_packs.controlled_values["occurrence.rule-effect-repetition-policy"]
                if value != "pause-recurrence-uses-idempotent"
            ),
        ),
    ]
    for label, namespace, value in declaration_failures:
        invalid_values = dict(extension_packs.controlled_values)
        invalid_values[namespace] = value
        try:
            validate_occurrence_semantic_declarations(invalid_values)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Malformed semantic declaration unexpectedly loaded: {label}")

    duplicated_scope_values = dict(extension_packs.controlled_values)
    duplicated_scope_values["occurrence.rule-effect-global-incompatibility-pair"] = (
        "advance-iteration-with-pause-recurrence",
    )
    try:
        validate_occurrence_semantic_declarations(duplicated_scope_values)
    except ValueError:
        pass
    else:
        raise AssertionError("Effect incompatibility pair unexpectedly accepted two scopes.")

    summary = {
        "schema_version": registry.schema_version,
        "branches": len(registry.branches),
        "templates": len(registry.templates),
        "recurrence_patterns": len(registry.recurrence_patterns),
        "recurrences": len(registry.recurrences),
        "iterations": len(registry.iterations),
        "phases": len(registry.phases),
        "schedules": len(registry.schedules),
        "occurrences": len(registry.occurrences),
        "tracks": len(registry.tracks),
        "transitions": len(registry.transitions),
        "causal_relations": len(registry.causal_relations),
        "outcomes": len(registry.outcomes),
        "rules": len(registry.rules),
        "state_transitions": len(registry.state_transitions),
        "carryovers": len(registry.carryovers),
        "fixture_queries": (
            len(expectations["iteration_occurrences"])
            + len(expectations["position_occurrences"])
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
            + len(expectations["state_at"])
            + 14
        ),
        "invalid_cases": len(invalid_cases),
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
