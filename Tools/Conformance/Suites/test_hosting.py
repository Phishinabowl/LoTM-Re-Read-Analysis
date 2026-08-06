from __future__ import annotations

import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.chronology_config import parse_chronology_registry  # noqa: E402
from knowledge_framework.hosting_config import load_hosted_identity_registry  # noqa: E402
from knowledge_framework.occurrence_config import parse_occurrence_registry  # noqa: E402
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402
from knowledge_framework.strict_yaml import load_yaml_file  # noqa: E402


class FixtureProvider:
    def __init__(self) -> None:
        self.identities = {
            "entity": {
                "alpha": {"id": "alpha"},
                "beta": {"id": "beta"},
                "delta": {"id": "delta"},
                "epsilon": {"id": "epsilon"},
            },
            "entity-incarnation": {"gamma-incarnation": {"id": "gamma-incarnation"}},
            "identity-phase": {"beta-phase": {"id": "beta-phase"}},
        }
        self.relationships = {
            "entity-relationship": {"beta-derived-from-alpha": {"id": "beta-derived-from-alpha"}},
            "incarnation-relationship": {},
            "identity-phase-relationship": {},
        }

    def identity_targets(self):
        return self.identities

    def identity_target(self, target_type: str, target_id: str):
        if target_type not in self.identities or target_id not in self.identities[target_type]:
            raise ValueError(f"Unknown fixture identity `{target_type}:{target_id}`.")
        return self.identities[target_type][target_id]

    def provenance_targets(self):
        return self.relationships

    def provenance_target(self, target_type: str, target_id: str):
        if target_type not in self.relationships or target_id not in self.relationships[target_type]:
            raise ValueError(f"Unknown fixture relationship `{target_type}:{target_id}`.")
        return self.relationships[target_type][target_id]


def set_path(data: object, path: list[object], value: object, operation: str) -> None:
    current = data
    for part in path[:-1]:
        current = current[part]
    final = path[-1]
    if operation == "set":
        current[final] = value
    elif operation == "append":
        current[final].append(value)
    elif operation == "remove":
        if isinstance(current, list):
            current.pop(final)
        else:
            current.pop(final)
    else:
        raise ValueError(f"Unknown fixture operation `{operation}`.")


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except (KeyError, TypeError, ValueError):
        return
    raise AssertionError(message)


def fixture_occurrences(root: Path, packs):
    chronology_path = root / "Framework" / "Data" / "Chronology" / "valid-registry.yaml"
    chronology_data = load_yaml_file(chronology_path, "chronology fixture", expected_schema_version=2)
    chronology_data["contexts"] = [
        {
            "id": "recipient-context",
            "label": "Recipient Context",
            "coordinate_system_id": "mission-day",
            "role": "story",
            "continuity_ids": [],
            "work_ids": ["fixture-work"],
            "branch_id": "main",
        },
        {
            "id": "agent-context",
            "label": "Agent Context",
            "coordinate_system_id": "control-step",
            "role": "time-travel-origin",
            "continuity_ids": [],
            "work_ids": ["fixture-work"],
            "branch_id": "main",
        },
    ]
    chronology_data["context_relations"] = []
    chronology = parse_chronology_registry(
        chronology_data,
        chronology_path,
        packs,
        work_ids={"fixture-work"},
        continuity_ids=set(),
    )
    occurrence_path = root / "Framework" / "Data" / "Occurrence" / "valid-registry.yaml"
    occurrence_data = load_yaml_file(occurrence_path, "occurrence fixture", expected_schema_version=10)
    return parse_occurrence_registry(
        occurrence_data,
        occurrence_path,
        packs,
        chronology,
        subject_targets={"character": {"protagonist", "observer"}},
        payload_targets={
            "state-record": {"protagonist-health"},
            "credential-record": {"protagonist-qualification"},
        },
    )


def load_fixture(project, packs, occurrences, provider, path: Path):
    fixture_project = replace(project, hosting_registry=path)
    return load_hosted_identity_registry(fixture_project, packs, occurrences, (provider,))


def assert_services(registry) -> int:
    if [item.id for item in registry.occupancies_for_carrier("body-a")] != [
        "alpha-controller",
        "beta-controller",
        "gamma-body-a",
    ]:
        raise AssertionError("Carrier occupancy query changed.")
    if [item.id for item in registry.occupancies_for_subject("entity", "alpha")] != [
        "alpha-controller",
        "alpha-control-unit",
        "alpha-runtime-source",
        "alpha-controller-body-b",
    ]:
        raise AssertionError("Subject occupancy query changed.")
    if [item.id for item in registry.controllers_at("body-a", "protagonist-entry-04")] != ["alpha-controller"]:
        raise AssertionError("Controller lookup before handoff changed.")
    if [item.id for item in registry.controllers_at("body-a", "protagonist-entry-05")] != ["beta-controller"]:
        raise AssertionError("Controller lookup at handoff changed.")
    if [item.id for item in registry.occupancies_at("body-b", "protagonist-entry-10")] != [
        "alpha-controller-body-b",
        "beta-copy-body-b",
        "delta-dormant-body-b",
        "epsilon-controller-body-b",
        "gamma-body-b",
    ]:
        raise AssertionError("Co-resident occupancy lookup changed.")
    if [item.id for item in registry.controllers_at("body-b", "protagonist-entry-10")] != [
        "alpha-controller-body-b",
        "epsilon-controller-body-b",
    ]:
        raise AssertionError("Co-control lookup changed.")
    if registry.occupancies["delta-dormant-body-b"].role != "dormant":
        raise AssertionError("Dormant co-residence changed.")
    if not registry.carrier_active_at("body-a", "protagonist-entry-13"):
        raise AssertionError("Carrier unexpectedly inactive before termination.")
    if registry.carrier_active_at("body-a", "protagonist-entry-14"):
        raise AssertionError("Carrier unexpectedly active at exclusive termination boundary.")
    if registry.provenance_target("hosted-identity-transition", "alpha-copy-to-beta").transition_kind != "copy":
        raise AssertionError("Hosted identity provenance lookup changed.")
    if tuple(registry.reconciliation_targets()) != ("host-carrier",):
        raise AssertionError("Hosted identity reconciliation target boundary changed.")
    boundary_05 = {
        "protagonist-experience": "protagonist-entry-05",
        "observer-experience": "observer-entry-04",
    }
    boundary_10 = {
        "protagonist-experience": "protagonist-entry-10",
        "observer-experience": "observer-entry-07",
    }
    if [item.id for item in registry.bindings_for_child("control-unit-a")] != [
        "control-unit-body-a",
        "control-unit-body-b",
    ]:
        raise AssertionError("Direct child binding query changed.")
    if [item.id for item in registry.parents_at("control-unit-a", boundary_05)] != ["control-unit-body-a"]:
        raise AssertionError("Control-unit parent before movement changed.")
    if [item.id for item in registry.parents_at("control-unit-a", boundary_10)] != ["control-unit-body-b"]:
        raise AssertionError("Control-unit parent at movement boundary changed.")
    if [(item.carrier_id, item.binding_ids) for item in registry.ancestors_at("runtime-a", boundary_10)] != [
        ("observer-host-a", ("runtime-observer-host",)),
        ("process-a", ("runtime-process",)),
        ("container-a", ("runtime-process", "process-container")),
        ("virtual-machine-a", ("runtime-process", "process-container", "container-virtual-machine")),
    ]:
        raise AssertionError("Transitive ancestor query changed.")
    if not registry.binding_active_at("runtime-observer-host", boundary_05):
        raise AssertionError("Cross-track paired binding boundary changed.")
    if [(item.carrier_id, item.binding_ids) for item in registry.descendants_at("virtual-machine-a", boundary_10)] != [
        ("container-a", ("container-virtual-machine",)),
        ("process-a", ("container-virtual-machine", "process-container")),
        ("runtime-a", ("container-virtual-machine", "process-container", "runtime-process")),
    ]:
        raise AssertionError("Transitive descendant query changed.")
    reachable_runtime = registry.reachable_occupancies_at("virtual-machine-a", boundary_10)
    if [(item.occupancy.id, item.carrier_path.carrier_id) for item in reachable_runtime] != [
        ("alpha-runtime-source", "runtime-a")
    ]:
        raise AssertionError("Reachable occupancy query changed.")
    if registry.occupancies_for_carrier("virtual-machine-a"):
        raise AssertionError("Indirect occupancy was promoted to direct occupancy.")
    reachable_body = registry.reachable_occupancies_at("body-b", boundary_10)
    if not any(
        item.occupancy.id == "alpha-control-unit" and item.carrier_path.binding_ids == ("control-unit-body-b",)
        for item in reachable_body
    ):
        raise AssertionError("Identity did not remain reachable through the moved control unit.")
    if registry.occupancies["alpha-control-unit"].carrier_id != "control-unit-a":
        raise AssertionError("Control-unit movement falsely moved its direct identity occupancy.")
    if registry.provenance_target("host-carrier-binding", "control-unit-body-b").binding_kind != "installed-in":
        raise AssertionError("Host carrier binding provenance lookup changed.")
    return 22


def assert_invalid_queries(registry) -> int:
    actions = (
        lambda: registry.occupancies_for_carrier("missing"),
        lambda: registry.occupancies_for_subject("entity", "missing"),
        lambda: registry.carrier_active_at("body-a", "missing"),
        lambda: registry.carrier_active_at("body-a", "observer-entry-01"),
        lambda: registry.occupancies_at("missing", "protagonist-entry-01"),
        lambda: registry.provenance_target("missing", "body-a"),
        lambda: registry.provenance_target("host-carrier", "missing"),
        lambda: registry.bindings_for_child("missing"),
        lambda: registry.bindings_for_parent("missing"),
        lambda: registry.binding_active_at("missing", {"protagonist-experience": "protagonist-entry-01"}),
        lambda: registry.binding_active_at("control-unit-body-a", {}),
        lambda: registry.parents_at("control-unit-a", {"protagonist-experience": "observer-entry-01"}),
        lambda: registry.reachable_occupancies_at("missing", {"protagonist-experience": "protagonist-entry-01"}),
        lambda: registry.provenance_target("host-carrier-binding", "missing"),
    )
    for action in actions:
        expect_rejected(action, "Hosted identity invalid query unexpectedly succeeded.")
    return len(actions)


def assert_scale(project, packs, occurrences, provider, base: dict, path: Path) -> tuple[int, int, int]:
    scale = copy.deepcopy(base)
    scale["carriers"] = {}
    scale["occupancies"] = []
    scale["transitions"] = []
    scale["bindings"] = []
    for index in range(128):
        carrier_id = f"scale-carrier-{index:03d}"
        scale["carriers"][carrier_id] = {
            "lifecycle": "active",
            "carrier_kind": "runtime",
            "label": f"Scale Carrier {index:03d}",
            "lifecycle_track_id": "protagonist-experience",
            "activated_at_entry_id": "protagonist-entry-01",
            "terminated_at_entry_id": None,
        }
        scale["occupancies"].append(
            {
                "id": f"scale-occupancy-{index:03d}",
                "subject_type": "entity",
                "subject_id": "alpha",
                "carrier_id": carrier_id,
                "role": "active",
                "activated_at_entry_id": "protagonist-entry-01",
                "terminated_at_entry_id": None,
            }
        )
        if index:
            scale["bindings"].append(
                {
                    "id": f"scale-binding-{index:03d}",
                    "child_carrier_id": carrier_id,
                    "parent_carrier_id": f"scale-carrier-{index - 1:03d}",
                    "binding_kind": "contained-in",
                    "child_activated_at_entry_id": "protagonist-entry-01",
                    "parent_activated_at_entry_id": "protagonist-entry-01",
                    "child_terminated_at_entry_id": None,
                    "parent_terminated_at_entry_id": None,
                }
            )
    path.write_text(json.dumps(scale, indent=2) + "\n", encoding="utf-8")
    registry = load_fixture(project, packs, occurrences, provider, path)
    boundary = {"protagonist-experience": "protagonist-entry-10"}
    if len(registry.ancestors_at("scale-carrier-127", boundary)) != 127:
        raise AssertionError("Hosted identity binding scale traversal changed.")
    return len(registry.carriers), len(registry.occupancies), len(registry.bindings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate hosted identity and embodiment registry conformance.")
    parser.add_argument("--root", help="Explicit project root.")
    parser.add_argument("--json", action="store_true", help="Emit a compact JSON summary.")
    args = parser.parse_args()

    root = resolve_project_root(args.root, executable_path=Path(__file__))
    fixture_root = root / "Framework" / "Data" / "Hosting"
    base = json.loads((fixture_root / "base" / "registry.json").read_text(encoding="utf-8"))
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    occurrences = fixture_occurrences(root, packs)
    provider = FixtureProvider()

    with tempfile.TemporaryDirectory(prefix="hosting-conformance-") as temporary:
        path = Path(temporary) / "registry.json"
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        registry = load_fixture(project, packs, occurrences, provider, path)
        counts = {
            "carriers": len(registry.carriers),
            "occupancies": len(registry.occupancies),
            "transitions": len(registry.transitions),
            "bindings": len(registry.bindings),
            "provenance_target_types": len(registry.provenance_targets()),
            "reconciliation_target_types": len(registry.reconciliation_targets()),
        }
        if counts != expectations["counts"]:
            raise AssertionError("Hosted identity fixture counts changed.")
        service_assertions = assert_services(registry)
        invalid_queries = assert_invalid_queries(registry)
        if invalid_queries != expectations["invalid_queries"]:
            raise AssertionError("Hosted identity invalid-query count changed.")

        invalid_configurations = 0
        for case in expectations["invalid_cases"]:
            candidate = copy.deepcopy(base)
            for operation in case["operations"]:
                set_path(candidate, operation["path"], operation.get("value"), operation["op"])
            path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
            expect_rejected(
                lambda: load_fixture(project, packs, occurrences, provider, path),
                f"Hosted identity invalid case `{case['id']}` unexpectedly succeeded.",
            )
            invalid_configurations += 1

        disabled_packs = replace(
            packs,
            enabled_capabilities=frozenset(
                item for item in packs.enabled_capabilities if item != "hosted-identity-embodiment"
            ),
        )
        path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        expect_rejected(
            lambda: load_fixture(project, disabled_packs, occurrences, provider, path),
            "Disabled hosted identity capability unexpectedly loaded.",
        )
        invalid_configurations += 1

        duplicate_provider = FixtureProvider()
        expect_rejected(
            lambda: load_hosted_identity_registry(
                replace(project, hosting_registry=path), packs, occurrences, (provider, duplicate_provider)
            ),
            "Duplicate hosted identity provider unexpectedly loaded.",
        )
        invalid_configurations += 1
        scale_carriers, scale_occupancies, scale_bindings = assert_scale(
            project, packs, occurrences, provider, base, path
        )

    summary = {
        "schema_version": registry.schema_version,
        "counts": counts,
        "service_assertions": service_assertions,
        "invalid_configurations": invalid_configurations,
        "invalid_queries": invalid_queries,
        "scale_carriers": scale_carriers,
        "scale_occupancies": scale_occupancies,
        "scale_bindings": scale_bindings,
    }
    if args.json:
        print(json.dumps(summary, separators=(",", ":"), sort_keys=True))
    else:
        print("Hosted identity conformance passed.")
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
