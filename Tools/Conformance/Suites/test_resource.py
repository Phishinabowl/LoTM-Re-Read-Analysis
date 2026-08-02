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

from knowledge_framework.project_config import (  # noqa: E402
    ResourceRootConfig,
    load_project_config,
    resolve_project_root,
)
from knowledge_framework.resource_config import load_resource_config  # noqa: E402


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


def apply_operation(document: object, operation: dict, case_root: Path) -> None:
    parent, final = parent_at(document, operation["path"])
    value = (
        str((case_root.parent / "outside").resolve())
        if operation.get("value_source") == "absolute-path"
        else copy.deepcopy(operation.get("value"))
    )
    if operation["op"] == "set":
        parent[final] = value  # type: ignore[index]
    elif operation["op"] == "append":
        target = parent[final]  # type: ignore[index]
        if not isinstance(target, list):
            raise AssertionError("Fixture append target must be a list.")
        target.append(value)
    elif operation["op"] == "remove":
        if isinstance(parent, list):
            parent.pop(final)
        else:
            del parent[final]  # type: ignore[index]
    else:
        raise AssertionError(f"Unknown fixture mutation operation: {operation['op']}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def fixture_project(project, root: Path):
    resource_roots = tuple(
        ResourceRootConfig(
            id=root_id,
            relative_path=Path(relative_path),
            path=root / relative_path,
            required=False,
        )
        for root_id, relative_path in (
            ("documents", "documents"),
            ("evidence-store", "evidence"),
            ("generated", "generated"),
            ("workspace", "workspace"),
        )
    )
    return replace(
        project,
        root=root,
        resources_registry=root / "registry.json",
        resource_roots=resource_roots,
    )


def assert_valid_fixture(registry, expected: dict) -> None:
    if len(registry.kinds) != expected["resource_kinds"]:
        raise AssertionError("Resource fixture kind count changed.")
    if len(registry.types) != expected["resource_types"]:
        raise AssertionError("Resource fixture type count changed.")
    active_count = sum(item.lifecycle == "active" for item in registry.types.values())
    if active_count != expected["active_resource_types"]:
        raise AssertionError("Resource fixture active-type count changed.")
    authorities = sorted({item.authority for item in registry.types.values()})
    if authorities != sorted(expected["authority_values"]):
        raise AssertionError("Resource fixture authority coverage changed.")
    tracking = sorted({placement.tracking for item in registry.types.values() for placement in item.placements})
    if tracking != sorted(expected["tracking_values"]):
        raise AssertionError("Resource fixture tracking coverage changed.")
    generated_roots = [placement.root_id for placement in registry.types["generated-preview"].placements]
    if generated_roots != expected["generated_preview_roots"]:
        raise AssertionError("Resource multi-placement order changed.")
    if len(registry.types["future-export"].placements) != expected["deferred_placement_count"]:
        raise AssertionError("Deferred resource placement behavior changed.")
    required_path = registry.types["canonical-document"].placements[0].path
    if not required_path.exists():
        raise AssertionError("Required resource placement did not resolve to the fixture tree.")
    provider = registry.reconciliation_provider()
    if provider["provider_id"] != "resource":
        raise AssertionError("Resource reconciliation provider ID changed.")
    if list(provider["targets"]) != expected["reconciliation_target_types"]:
        raise AssertionError("Resource reconciliation target order changed.")
    if registry.reconciliation_target("resource-kind", "document") is not registry.kinds["document"]:
        raise AssertionError("Resource-kind reconciliation lookup changed.")
    if (
        registry.reconciliation_target("resource-type", "canonical-document")
        is not registry.types["canonical-document"]
    ):
        raise AssertionError("Resource-type reconciliation lookup changed.")


def write_scale_fixture(root: Path, type_count: int) -> None:
    resource_types = {}
    for index in range(type_count):
        type_id = f"scale-resource-{index:03d}"
        resource_types[type_id] = {
            "lifecycle": "active",
            "label": f"Scale Resource {index:03d}",
            "plural_label": f"Scale Resources {index:03d}",
            "kind_id": "scale-kind",
            "authority": "supporting",
            "editor_enabled": False,
            "placements": [
                {
                    "root_id": "generated",
                    "relative_path": f"scale/{index:03d}",
                    "tracking": "ignored",
                    "required": False,
                }
            ],
        }
    write_json(
        root / "registry.json",
        {
            "schema_version": 1,
            "resource_kinds": {"scale-kind": {"label": "Scale Kind", "plural_label": "Scale Kinds"}},
            "resource_types": resource_types,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run resource-registry conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    canonical = load_resource_config(project)
    fixture_root = root / "Framework" / "Data" / "Resources"
    base_root = fixture_root / "base"
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported resource conformance expectation schema.")
    base_document = json.loads((base_root / "registry.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="knowledge-resource-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_root = temp_root / "valid"
        shutil.copytree(base_root, valid_root)
        fixture_registry = load_resource_config(fixture_project(project, valid_root))
        assert_valid_fixture(fixture_registry, expectations["valid"])
        expect_rejected(
            lambda: fixture_registry.reconciliation_target("unknown", "document"),
            "Unsupported resource reconciliation target type was accepted.",
        )
        expect_rejected(
            lambda: fixture_registry.reconciliation_target("resource-kind", "unknown"),
            "Unknown resource reconciliation target was accepted.",
        )

        for case in expectations["invalid_cases"]:
            case_root = temp_root / case["id"]
            shutil.copytree(base_root, case_root)
            document = copy.deepcopy(base_document)
            for operation in case["operations"]:
                apply_operation(document, operation, case_root)
            write_json(case_root / "registry.json", document)
            case_project = fixture_project(project, case_root)
            expect_rejected(
                lambda case_project=case_project: load_resource_config(case_project),
                f"Malformed resource configuration was accepted: {case['id']}",
            )

        scale_root = temp_root / "scale"
        scale_root.mkdir()
        scale_count = expectations["scale_resource_type_count"]
        write_scale_fixture(scale_root, scale_count)
        scale_registry = load_resource_config(fixture_project(project, scale_root))
        if len(scale_registry.kinds) != 1 or len(scale_registry.types) != scale_count:
            raise AssertionError("Resource scale composition counts changed.")

    summary = {
        "schema_version": 1,
        "canonical_resource_kinds": len(canonical.kinds),
        "canonical_resource_types": len(canonical.types),
        "fixture_resource_kinds": len(fixture_registry.kinds),
        "fixture_resource_types": len(fixture_registry.types),
        "fixture_active_resource_types": sum(item.lifecycle == "active" for item in fixture_registry.types.values()),
        "invalid_configuration_cases": len(expectations["invalid_cases"]),
        "invalid_query_cases": expectations["invalid_query_cases"],
        "scale_resource_type_count": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Resource conformance passed: "
            f"{summary['canonical_resource_kinds']} canonical kinds, "
            f"{summary['canonical_resource_types']} canonical types, "
            f"{summary['invalid_configuration_cases']} malformed configurations, and "
            f"{summary['scale_resource_type_count']} scale resource types."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
