from __future__ import annotations

import argparse
import copy
import json

from chronology_config import load_chronology_registry, parse_chronology_registry
from occurrence_config import load_occurrence_registry, parse_occurrence_registry
from project_config import load_project_config, resolve_project_root
from resource_config import load_resource_config
from schema_pack_config import load_schema_pack_registry
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate occurrence and recurrence registry behavior and cross-runtime fixtures.")
    parser.add_argument("--root", help="Repository root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()

    root = resolve_project_root(args.root)
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    resources = load_resource_config(project)
    sources = load_source_registry(project, resources, packs)
    chronology = load_chronology_registry(project, packs, work_ids=set(sources.works), continuity_ids=set(sources.continuities))
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
    fixture_data = load_yaml_file(fixture_path, "occurrence fixture", expected_schema_version=3)
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
        if (previous.id if previous else None) != expected_previous or (following.id if following else None) != expected_next:
            raise AssertionError(f"Unexpected track boundaries for `{iteration_id}` on `{track_id}`.")
    for track_id, occurrence_id, expected_previous, expected_next in expectations["track_neighbors"]:
        previous = fixture.previous_on_track(track_id, occurrence_id)
        following = fixture.next_on_track(track_id, occurrence_id)
        if (previous.id if previous else None) != expected_previous or (following.id if following else None) != expected_next:
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
                invalid, fixture_path, packs, chronology_fixture,
                subject_targets={"character": {"protagonist", "observer"}},
                payload_targets={"state-record": {"protagonist-health"}},
            )
        except ValueError:
            continue
        raise AssertionError(f"Malformed occurrence case unexpectedly loaded: {case['name']}")

    summary = {
        "schema_version": registry.schema_version,
        "branches": len(registry.branches),
        "templates": len(registry.templates),
        "recurrence_patterns": len(registry.recurrence_patterns),
        "recurrences": len(registry.recurrences),
        "iterations": len(registry.iterations),
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
            + len(expectations["subject_state_transitions"])
            + len(expectations["state_at"])
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
