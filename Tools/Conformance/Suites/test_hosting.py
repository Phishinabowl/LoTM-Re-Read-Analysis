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
from knowledge_framework.interpretation_config import load_interpretation_registry  # noqa: E402
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


PACK_PATHS = {
    "core": "Framework/Packs/core/pack.yaml",
    "hosting-foundation": "Framework/Packs/hosting-foundation/pack.yaml",
    "narrative-media": "Framework/Packs/narrative-media/pack.yaml",
    "hosting-narrative": "Framework/Packs/hosting-narrative/pack.yaml",
    "hosting-simulation": "Framework/Packs/hosting-simulation/pack.yaml",
    "hosting-compute": "Framework/Packs/hosting-compute/pack.yaml",
}


def load_pack_variant(project, path: Path, selected: tuple[str, ...], enabled: tuple[str, ...]):
    document = {
        "schema_version": 2,
        "selected_packs": [{"pack_id": pack_id, "path": PACK_PATHS[pack_id]} for pack_id in selected],
        "capability_activation": {"default": "disabled", "enabled": list(enabled)},
    }
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return load_schema_pack_registry(replace(project, schema_packs_registry=path))


def assert_pack_isolation(project, temp_root: Path):
    variants = {
        "core": {
            "selected": ("core",),
            "enabled": (),
            "carriers": (),
            "bindings": (),
        },
        "foundation": {
            "selected": ("core", "hosting-foundation"),
            "enabled": ("hosted-identity-embodiment",),
            "hosting_enabled": True,
            "carriers": (),
            "bindings": ("installed-in", "contained-in", "attached-to"),
        },
        "foundation-disabled": {
            "selected": ("core", "hosting-foundation"),
            "enabled": (),
            "hosting_enabled": False,
            "carriers": (),
            "bindings": ("installed-in", "contained-in", "attached-to"),
        },
        "narrative": {
            "selected": ("core", "hosting-foundation", "narrative-media", "hosting-narrative"),
            "enabled": ("hosted-identity-embodiment",),
            "carriers": ("physical-body", "vessel"),
            "bindings": ("installed-in", "contained-in", "attached-to"),
        },
        "simulation": {
            "selected": ("core", "hosting-foundation", "hosting-simulation"),
            "enabled": ("hosted-identity-embodiment",),
            "carriers": ("control-unit", "avatar"),
            "bindings": ("installed-in", "contained-in", "attached-to", "projected-through"),
        },
        "compute": {
            "selected": ("core", "hosting-foundation", "hosting-compute"),
            "enabled": ("hosted-identity-embodiment",),
            "carriers": ("runtime", "container", "virtual-host"),
            "bindings": ("installed-in", "contained-in", "attached-to", "executes-in"),
        },
        "combined": {
            "selected": (
                "core",
                "hosting-foundation",
                "narrative-media",
                "hosting-narrative",
                "hosting-simulation",
                "hosting-compute",
            ),
            "enabled": ("hosted-identity-embodiment",),
            "carriers": (
                "physical-body",
                "vessel",
                "control-unit",
                "avatar",
                "runtime",
                "container",
                "virtual-host",
            ),
            "bindings": (
                "installed-in",
                "contained-in",
                "attached-to",
                "projected-through",
                "executes-in",
            ),
        },
    }
    loaded = {}
    for variant_id, expected in variants.items():
        packs = load_pack_variant(
            project,
            temp_root / f"packs-{variant_id}.json",
            expected["selected"],
            expected["enabled"],
        )
        if packs.allowed_values("hosting.carrier-kind") != expected["carriers"]:
            raise AssertionError(f"Hosting carrier vocabulary leaked in `{variant_id}` composition.")
        if packs.allowed_values("hosting.binding-kind") != expected["bindings"]:
            raise AssertionError(f"Hosting binding vocabulary leaked in `{variant_id}` composition.")
        expected_hosting = expected.get("hosting_enabled", variant_id != "core")
        if packs.capability_enabled("hosted-identity-embodiment") != expected_hosting:
            raise AssertionError(f"Hosted identity capability activation changed in `{variant_id}` composition.")
        loaded[variant_id] = packs
    return loaded


def load_combined_fixture_packs(project, path: Path):
    document = load_yaml_file(project.schema_packs_registry, "schema-pack registry", expected_schema_version=2)
    document["selected_packs"].extend(
        [
            {"pack_id": "hosting-simulation", "path": PACK_PATHS["hosting-simulation"]},
            {"pack_id": "hosting-compute", "path": PACK_PATHS["hosting-compute"]},
        ]
    )
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return load_schema_pack_registry(replace(project, schema_packs_registry=path))


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


def assert_composed_ownership(project, packs, occurrences, hosting, root: Path) -> int:
    fixture_project = replace(
        project,
        interpretations_registry=root / "Framework" / "Data" / "Interpretations" / "composed-registry.json",
    )
    interpretations = load_interpretation_registry(
        fixture_project,
        packs,
        (occurrences, occurrences.chronology, hosting),
    )
    decision = interpretations.comparison_set_decision("order-alternatives")
    if decision.disposition != "unresolved" or decision.selected_interpretation_ids:
        raise AssertionError("Competing composed structures no longer remain unresolved.")

    branch_state = occurrences.branch_state_at("changed-outcome", 3)
    if branch_state is None or branch_state.resulting_state != "pruned":
        raise AssertionError("Composed branch-lifecycle lookup changed.")

    cardinality_kinds = {item.cardinality_kind for item in occurrences.cardinalities_for_recurrence("inner-loop")}
    if cardinality_kinds != {"minimum", "maximum", "range", "unknown"}:
        raise AssertionError("Composed aggregate-recurrence cardinalities changed.")

    causal = next(item for item in occurrences.causal_relations if item.id == "next-wake-enables-reset")
    if causal.source_occurrence_id != "wake-two" or causal.target_occurrence_id != "reset-one":
        raise AssertionError("Backward causal knowledge relation changed.")

    recipient_bindings = occurrences.chronology_bindings_for_participation("protagonist-self-intervention-recipient")
    agent_bindings = occurrences.chronology_bindings_for_participation("protagonist-self-intervention-agent")
    if {item.chronology_context_id for item in recipient_bindings} != {None, "recipient-context"} or {
        item.chronology_context_id for item in agent_bindings
    } != {None, "agent-context"}:
        raise AssertionError("Composed participant-relative chronology bindings changed.")

    belief = occurrences.state_at(
        "protagonist-experience",
        "restored-main",
        "occurrence-template",
        "bell",
        "belief",
    )
    if belief is None or belief.resulting_attitude != "accepts-false":
        raise AssertionError("Composed unreliable-belief revision changed.")

    skill = occurrences.state_at(
        "protagonist-experience",
        "restored-main",
        "occurrence-template",
        "bell",
        "skill",
    )
    if skill is None or skill.resulting_capability is None or skill.resulting_capability.value != "practiced":
        raise AssertionError("Composed state progression changed.")

    reachable = hosting.reachable_occupancies_at(
        "body-b",
        {"protagonist-experience": "protagonist-entry-10", "observer-experience": "observer-entry-07"},
    )
    if not any(
        item.occupancy.id == "alpha-control-unit" and item.carrier_path.binding_ids == ("control-unit-body-b",)
        for item in reachable
    ):
        raise AssertionError("Composed hosted-identity reachability changed.")
    return 8


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
    provider = FixtureProvider()

    with tempfile.TemporaryDirectory(prefix="hosting-conformance-") as temporary:
        temp_root = Path(temporary)
        pack_variants = assert_pack_isolation(project, temp_root)
        if len(pack_variants) != expectations["pack_compositions"]:
            raise AssertionError("Hosted identity pack-composition count changed.")
        packs = load_combined_fixture_packs(project, temp_root / "packs-fixture.json")
        occurrences = fixture_occurrences(root, packs)
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
        composed_assertions = assert_composed_ownership(project, packs, occurrences, registry, root)
        if composed_assertions != expectations["composed_assertions"]:
            raise AssertionError("Hosted identity composed-ownership assertion count changed.")
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

        empty = {"schema_version": 2, "carriers": {}, "bindings": [], "occupancies": [], "transitions": []}
        path.write_text(json.dumps(empty, indent=2) + "\n", encoding="utf-8")
        disabled_registry = load_fixture(project, pack_variants["core"], occurrences, provider, path)
        if (
            disabled_registry.registered
            or disabled_registry.enabled
            or disabled_registry.provenance_targets()
            or disabled_registry.reconciliation_targets()
        ):
            raise AssertionError("Disabled empty hosting registry exposed active providers.")

        selected_disabled_registry = load_fixture(
            project, pack_variants["foundation-disabled"], occurrences, provider, path
        )
        expected_provenance_types = {
            "host-carrier",
            "host-carrier-binding",
            "hosted-identity-occupancy",
            "hosted-identity-transition",
        }
        if (
            not selected_disabled_registry.registered
            or selected_disabled_registry.enabled
            or set(selected_disabled_registry.provenance_targets()) != expected_provenance_types
            or set(selected_disabled_registry.reconciliation_targets()) != {"host-carrier"}
            or any(selected_disabled_registry.provenance_targets().values())
            or any(selected_disabled_registry.reconciliation_targets().values())
        ):
            raise AssertionError("Selected disabled hosting did not expose empty typed providers.")

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
        "composed_assertions": composed_assertions,
        "invalid_configurations": invalid_configurations,
        "invalid_queries": invalid_queries,
        "pack_compositions": len(pack_variants),
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
