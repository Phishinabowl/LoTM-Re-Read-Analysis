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

from knowledge_framework.interpretation_config import load_interpretation_registry  # noqa: E402
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402


class FixtureProvider:
    def __init__(self, targets: dict[str, tuple[str, ...]]):
        self.targets = {
            target_type: {target_id: {"id": target_id} for target_id in ids} for target_type, ids in targets.items()
        }

    def provenance_targets(self) -> dict[str, dict[str, object]]:
        return self.targets

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        if subject_type not in self.targets or subject_id not in self.targets[subject_type]:
            raise ValueError(f"Unknown fixture target `{subject_type}:{subject_id}`.")
        return self.targets[subject_type][subject_id]


def fixture_providers() -> tuple[FixtureProvider, ...]:
    return (
        FixtureProvider({"occurrence": ("first-occurrence", "second-occurrence")}),
        FixtureProvider({"entity": ("observer-entity",)}),
        FixtureProvider({"chronology-position": ("shared-position",)}),
    )


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except (KeyError, TypeError, ValueError):
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
    value = copy.deepcopy(operation.get("value"))
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
        raise AssertionError(f"Unknown fixture operation `{operation['op']}`.")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def load_fixture(project, packs, providers, root: Path):
    fixture_project = replace(project, interpretations_registry=root / "registry.json")
    return load_interpretation_registry(fixture_project, packs, providers)


def assert_counts(registry, expected: dict) -> None:
    for field in ("relation_types", "interpretations", "members", "relations", "comparison_sets"):
        if len(getattr(registry, field)) != expected[field]:
            raise AssertionError(f"Structural interpretation fixture `{field}` count changed.")
    if len(registry.provenance_targets()) != expected["provenance_target_types"]:
        raise AssertionError("Structural interpretation provenance target-type count changed.")


def assert_services(registry, claim_keys: set[str]) -> None:
    registry.validate_claim_targets(claim_keys)
    structure = registry.structure_for_interpretation("forward-reconstruction")
    if tuple(item.id for item in structure.members) != ("forward-first", "forward-second", "forward-claim"):
        raise AssertionError("Structural interpretation member query changed.")
    if tuple(item.id for item in structure.relations) != ("forward-order", "forward-claim-cause"):
        raise AssertionError("Structural interpretation relation query changed.")
    if tuple(item.id for item in registry.comparison_sets_for_interpretation("forward-reconstruction")) != (
        "order-alternatives",
        "research-candidates",
    ):
        raise AssertionError("Structural interpretation comparison-set query changed.")
    unresolved = registry.comparison_set_decision("order-alternatives")
    if unresolved.disposition != "unresolved" or unresolved.selected_interpretation_ids:
        raise AssertionError("Mutually exclusive interpretation set no longer remains unresolved.")
    compatible = registry.comparison_set_decision("compatible-contexts")
    if compatible.disposition != "compatible" or compatible.selected_interpretation_ids:
        raise AssertionError("Compatible interpretation decision changed.")
    target = registry.provenance_target("structural-interpretation-relation", "forward-order")
    if target.relationship_type != "precedes":
        raise AssertionError("Structural interpretation provenance lookup changed.")


def assert_invalid_queries(registry) -> int:
    actions = (
        lambda: registry.members_for_interpretation("unknown"),
        lambda: registry.relations_for_interpretation("unknown"),
        lambda: registry.comparison_sets_for_interpretation("unknown"),
        lambda: registry.structure_for_interpretation("unknown"),
        lambda: registry.comparison_set_decision("unknown"),
        lambda: registry.provenance_target("unknown", "forward-reconstruction"),
        lambda: registry.provenance_target("structural-interpretation", "unknown"),
        lambda: registry.validate_claim_targets(set()),
    )
    for action in actions:
        expect_rejected(action, "Structural interpretation invalid query unexpectedly succeeded.")
    return len(actions)


def assert_scale(project, packs, providers, base: dict, root: Path) -> tuple[int, int]:
    scale = copy.deepcopy(base)
    scale["interpretations"] = {
        "scale-reconstruction": {
            "lifecycle": "active",
            "label": "Scale Reconstruction",
            "description": None,
        }
    }
    scale["members"] = []
    scale["relations"] = []
    scale["comparison_sets"] = {}
    provider = FixtureProvider({"occurrence": tuple(f"scale-occurrence-{index:03d}" for index in range(128))})
    for index in range(128):
        scale["members"].append(
            {
                "id": f"scale-member-{index:03d}",
                "interpretation_id": "scale-reconstruction",
                "target_type": "occurrence",
                "target_id": f"scale-occurrence-{index:03d}",
            }
        )
        if index:
            scale["relations"].append(
                {
                    "id": f"scale-relation-{index:03d}",
                    "interpretation_id": "scale-reconstruction",
                    "source_member_id": f"scale-member-{index - 1:03d}",
                    "relationship_type": "precedes",
                    "target_member_id": f"scale-member-{index:03d}",
                }
            )
    write_json(root / "registry.json", scale)
    registry = load_fixture(project, packs, (provider,), root)
    return len(registry.members), len(registry.relations)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate structural interpretation registry conformance.")
    parser.add_argument("--root", help="Explicit project root.")
    parser.add_argument("--json", action="store_true", help="Emit a compact JSON summary.")
    args = parser.parse_args()

    root = resolve_project_root(explicit_root=args.root, executable_path=Path(__file__))
    fixture_root = root / "Framework" / "Data" / "Interpretations"
    base = json.loads((fixture_root / "base" / "registry.json").read_text(encoding="utf-8"))
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    providers = fixture_providers()
    claim_keys = set(expectations["claim_keys"])

    with tempfile.TemporaryDirectory(prefix="interpretation-conformance-") as temporary:
        temporary_root = Path(temporary)
        write_json(temporary_root / "registry.json", base)
        registry = load_fixture(project, packs, providers, temporary_root)
        assert_counts(registry, expectations["counts"])
        assert_services(registry, claim_keys)
        invalid_queries = assert_invalid_queries(registry)
        if invalid_queries != expectations["invalid_queries"]:
            raise AssertionError("Structural interpretation invalid-query count changed.")

        invalid_configurations = 0
        for case in expectations["invalid_cases"]:
            if case.get("post_load") == "unknown-claim":
                expect_rejected(
                    lambda: registry.validate_claim_targets(set()),
                    f"Structural interpretation invalid case `{case['id']}` unexpectedly succeeded.",
                )
            else:
                candidate = copy.deepcopy(base)
                for operation in case.get("operations", []):
                    apply_operation(candidate, operation)
                write_json(temporary_root / "registry.json", candidate)
                expect_rejected(
                    lambda: load_fixture(project, packs, providers, temporary_root),
                    f"Structural interpretation invalid case `{case['id']}` unexpectedly succeeded.",
                )
            invalid_configurations += 1

        disabled_packs = replace(
            packs,
            enabled_capabilities=frozenset(
                item for item in packs.enabled_capabilities if item != "structural-interpretation-modeling"
            ),
        )
        write_json(temporary_root / "registry.json", base)
        expect_rejected(
            lambda: load_fixture(project, disabled_packs, providers, temporary_root),
            "Disabled structural interpretation capability unexpectedly loaded.",
        )
        invalid_configurations += 1

        duplicate_provider = FixtureProvider({"occurrence": ("other-occurrence",)})
        expect_rejected(
            lambda: load_fixture(project, packs, providers + (duplicate_provider,), temporary_root),
            "Duplicate structural interpretation target provider unexpectedly loaded.",
        )
        invalid_configurations += 1

        scale_members, scale_relations = assert_scale(project, packs, providers, base, temporary_root)

    summary = {
        "schema_version": registry.schema_version,
        "counts": expectations["counts"],
        "invalid_configurations": invalid_configurations,
        "invalid_queries": invalid_queries,
        "scale_members": scale_members,
        "scale_relations": scale_relations,
    }
    if args.json:
        print(json.dumps(summary, separators=(",", ":"), sort_keys=True))
    else:
        print("Structural interpretation conformance passed.")
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
