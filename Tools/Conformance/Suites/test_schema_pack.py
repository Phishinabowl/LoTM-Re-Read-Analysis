from __future__ import annotations

import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
import tempfile


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402


TARGET_PATHS = {
    "registry": Path("registry.json"),
    "fixture-core": Path("packs/fixture-core.json"),
    "fixture-domain": Path("packs/fixture-domain.json"),
    "fixture-extension": Path("packs/fixture-extension.json"),
}


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except (TypeError, ValueError):
        return
    raise AssertionError(message)


def parent_at(document: object, path: list[object]) -> tuple[object, object]:
    if not path:
        raise AssertionError("Fixture mutation path cannot be empty.")
    current = document
    for segment in path[:-1]:
        current = current[segment]  # type: ignore[index]
    return current, path[-1]


def apply_operation(document: object, operation: dict) -> None:
    parent, final = parent_at(document, operation["path"])
    if operation["op"] == "set":
        parent[final] = copy.deepcopy(operation["value"])  # type: ignore[index]
    elif operation["op"] == "append":
        target = parent[final]  # type: ignore[index]
        if not isinstance(target, list):
            raise AssertionError("Fixture append target must be a list.")
        target.append(copy.deepcopy(operation["value"]))
    elif operation["op"] == "remove":
        if isinstance(parent, list):
            parent.pop(final)
        else:
            del parent[final]  # type: ignore[index]
    else:
        raise AssertionError(f"Unknown fixture mutation operation: {operation['op']}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def assert_valid_fixture(registry, expected: dict) -> None:
    if list(registry.selection_order) != expected["selection_order"]:
        raise AssertionError("Schema-pack fixture selection order changed.")
    if len(registry.declared_capabilities) != expected["declared_capabilities"]:
        raise AssertionError("Schema-pack declared capability count changed.")
    if len(registry.available_capabilities) != expected["available_capabilities"]:
        raise AssertionError("Schema-pack available capability count changed.")
    if len(registry.enabled_capabilities) != expected["enabled_capabilities"]:
        raise AssertionError("Schema-pack enabled capability count changed.")
    if list(registry.capability_providers["shared-capability"]) != expected["shared_capability_providers"]:
        raise AssertionError("Schema-pack multiple-provider composition changed.")
    if list(registry.allowed_values("fixture.kind")) != expected["kind_values"]:
        raise AssertionError("Schema-pack cross-pack controlled-value order changed.")
    if list(registry.allowed_values("fixture.mode")) != expected["mode_values"]:
        raise AssertionError("Schema-pack extension values changed.")
    if registry.owner_of("fixture.kind", "domain-kind") != expected["domain_kind_owner"]:
        raise AssertionError("Schema-pack controlled-value ownership changed.")
    definition = registry.definition_of("fixture.kind", "domain-kind")
    if definition is None or definition.broader_value != expected["domain_kind_broader"]:
        raise AssertionError("Schema-pack cross-pack broader-value resolution changed.")
    if registry.capability_available("planned-capability"):
        raise AssertionError("Planned schema-pack capability became available.")
    if registry.capability_enabled("planned-capability"):
        raise AssertionError("Planned schema-pack capability became enabled.")
    if not registry.capability_available("deprecated-capability"):
        raise AssertionError("Deprecated schema-pack capability lost compatibility availability.")
    semantic = expected["semantic_declarations"]
    for field, expected_count in semantic.items():
        if len(getattr(registry, field)) != expected_count:
            raise AssertionError(f"Schema-pack typed semantic count changed for `{field}`.")


def write_scale_fixture(root: Path, pack_count: int) -> Path:
    packs_dir = root / "packs"
    packs_dir.mkdir(parents=True)
    selections = []
    enabled = []
    for index in range(pack_count):
        pack_id = "scale-core" if index == 0 else f"scale-pack-{index:03d}"
        capability = f"scale-capability-{index:03d}"
        value = f"scale-value-{index:03d}"
        transition_kind = f"scale-transition-{index:03d}"
        transition_profile = f"scale-profile-{index:03d}"
        filename = f"{pack_id}.json"
        selections.append({"pack_id": pack_id, "path": f"packs/{filename}"})
        enabled.append(capability)
        pack = {
            "schema_version": 4,
            "pack_id": pack_id,
            "pack_version": 1,
            "lifecycle": "active",
            "pack_kind": "core" if index == 0 else "extension",
            "label": f"Scale Pack {index:03d}",
            "description": "Generated schema-pack scale fixture.",
            "dependencies": [] if index == 0 else [{"pack_id": "scale-core", "minimum_version": 1}],
            "capabilities": [capability],
            "controlled_values": {
                "scale.value": [value],
                "occurrence.transition-kind": [transition_kind],
                "occurrence.transition-profile": [transition_profile],
            },
            "semantic_declarations": {
                "occurrence": {
                    "transition_profiles": [
                        {
                            "transition_kind": transition_kind,
                            "transition_profile": transition_profile,
                        }
                    ]
                }
            },
        }
        write_json(packs_dir / filename, pack)
    registry_path = root / "registry.json"
    write_json(
        registry_path,
        {
            "schema_version": 2,
            "selected_packs": selections,
            "capability_activation": {"default": "disabled", "enabled": enabled},
        },
    )
    return registry_path


def assert_typed_delimiter_collision(project, base_root: Path, temp_root: Path) -> int:
    collision_root = temp_root / "delimiter-collision"
    shutil.copytree(base_root, collision_root)
    core_path = collision_root / "packs" / "fixture-core.json"
    core = json.loads(core_path.read_text(encoding="utf-8"))
    effect_kinds = ["a", "a-with-b", "b-with-c", "c"]
    core["controlled_values"]["occurrence.rule-effect-kind"].extend(effect_kinds)
    semantics = core["semantic_declarations"]["occurrence"]
    semantics["effect_target_compatibilities"].extend(
        {"effect_kind": effect_kind, "target_type": "subject"} for effect_kind in effect_kinds
    )
    semantics["rule_effect_compatibilities"].extend(
        {"rule_kind": "add", "effect_kind": effect_kind} for effect_kind in effect_kinds
    )
    semantics["effect_policies"].extend(
        {"effect_kind": effect_kind, "repetition_policy": "idempotent"} for effect_kind in effect_kinds
    )
    semantics["effect_incompatibilities"].extend(
        (
            {"members": ["a", "b-with-c"], "scope": "global"},
            {"members": ["a-with-b", "c"], "scope": "same-target"},
        )
    )
    write_json(core_path, core)
    collision_project = replace(
        project,
        root=collision_root,
        schema_packs_registry=collision_root / "registry.json",
    )
    registry = load_schema_pack_registry(collision_project)
    expected = {
        ("a", "b-with-c"): "global",
        ("a-with-b", "c"): "same-target",
    }
    actual = {pair: registry.effect_incompatibilities[pair] for pair in expected}
    if actual != expected:
        raise AssertionError("Typed delimiter-collision declarations did not remain distinct.")
    return len(expected)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run schema-pack composition conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    canonical = load_schema_pack_registry(project)
    fixture_root = root / "Framework" / "Data" / "Schema-Packs"
    base_root = fixture_root / "base"
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported schema-pack conformance expectation schema.")

    with tempfile.TemporaryDirectory(prefix="knowledge-schema-pack-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_root = temp_root / "valid"
        shutil.copytree(base_root, valid_root)
        valid_project = replace(project, root=valid_root, schema_packs_registry=valid_root / "registry.json")
        fixture_registry = load_schema_pack_registry(valid_project)
        assert_valid_fixture(fixture_registry, expectations["valid"])
        typed_collision_pairs = assert_typed_delimiter_collision(project, base_root, temp_root)

        for case in expectations["invalid_cases"]:
            case_root = temp_root / case["id"]
            shutil.copytree(base_root, case_root)
            target_path = case_root / TARGET_PATHS[case["target"]]
            document = json.loads(target_path.read_text(encoding="utf-8"))
            for operation in case["operations"]:
                apply_operation(document, operation)
            write_json(target_path, document)
            case_project = replace(project, root=case_root, schema_packs_registry=case_root / "registry.json")
            expect_rejected(
                lambda case_project=case_project: load_schema_pack_registry(case_project),
                f"Malformed schema-pack composition was accepted: {case['id']}",
            )

        scale_root = temp_root / "scale"
        scale_count = expectations["scale_pack_count"]
        scale_project = replace(
            project,
            root=scale_root,
            schema_packs_registry=write_scale_fixture(scale_root, scale_count),
        )
        scale_registry = load_schema_pack_registry(scale_project)
        if not (
            len(scale_registry.selection_order)
            == len(scale_registry.declared_capabilities)
            == len(scale_registry.enabled_capabilities)
            == len(scale_registry.allowed_values("scale.value"))
            == len(scale_registry.transition_profiles)
            == scale_count
        ):
            raise AssertionError("Schema-pack scale composition counts changed.")

    summary = {
        "schema_version": 1,
        "canonical_selected_packs": len(canonical.selection_order),
        "fixture_selected_packs": len(fixture_registry.selection_order),
        "fixture_declared_capabilities": len(fixture_registry.declared_capabilities),
        "fixture_available_capabilities": len(fixture_registry.available_capabilities),
        "fixture_enabled_capabilities": len(fixture_registry.enabled_capabilities),
        "fixture_controlled_values": sum(len(values) for values in fixture_registry.controlled_values.values()),
        "invalid_composition_cases": len(expectations["invalid_cases"]),
        "scale_pack_count": scale_count,
        "scale_typed_declarations": len(scale_registry.transition_profiles),
        "typed_collision_pairs": typed_collision_pairs,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Schema-pack conformance passed: "
            f"{summary['canonical_selected_packs']} canonical packs, "
            f"{summary['fixture_selected_packs']} synthetic packs, "
            f"{summary['invalid_composition_cases']} malformed compositions, and "
            f"{summary['scale_pack_count']} scale packs."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
