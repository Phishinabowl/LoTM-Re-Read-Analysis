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
from knowledge_framework.project_config import load_project_config, resolve_project_root
from knowledge_framework.resource_config import load_resource_config
from knowledge_framework.schema_pack_config import load_schema_pack_registry
from knowledge_framework.source_config import load_source_registry
from knowledge_framework.strict_yaml import load_yaml_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate chronology registry behavior and cross-runtime fixtures.")
    parser.add_argument("--root", help="Repository root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()

    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    resources = load_resource_config(project)
    sources = load_source_registry(project, resources, packs)
    registry = load_chronology_registry(
        project,
        packs,
        work_ids=set(sources.works),
        continuity_ids=set(sources.continuities),
    )

    fixture_root = root / "Framework" / "Data" / "Chronology"
    fixture_data = load_yaml_file(
        fixture_root / "valid-registry.yaml",
        "chronology fixture",
        expected_schema_version=2,
    )
    fixture = parse_chronology_registry(
        fixture_data,
        fixture_root / "valid-registry.yaml",
        packs,
        work_ids=set(),
        continuity_ids=set(),
    )
    context_only_fixture = parse_chronology_registry(
        fixture_data,
        fixture_root / "valid-registry.yaml",
        packs,
    )
    if len(context_only_fixture.contexts) != len(fixture.contexts):
        raise AssertionError("Context-only chronology loading changed when optional project targets were omitted.")
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    for left, right, expected in expectations["comparisons"]:
        actual = fixture.compare_positions(left, right)
        if actual != expected:
            raise AssertionError(f"Chronology comparison {left}/{right}: expected {expected}, got {actual}")

    for context_id, relation_type, expected_ids in expectations["context_queries"]["from"]:
        actual_ids = [item.id for item in fixture.context_relations_from(context_id, relation_type)]
        if actual_ids != expected_ids:
            raise AssertionError(
                f"Outgoing context relations for {context_id}/{relation_type}: "
                f"expected {expected_ids}, got {actual_ids}"
            )
    for context_id, relation_type, expected_ids in expectations["context_queries"]["to"]:
        actual_ids = [item.id for item in fixture.context_relations_to(context_id, relation_type)]
        if actual_ids != expected_ids:
            raise AssertionError(
                f"Incoming context relations for {context_id}/{relation_type}: "
                f"expected {expected_ids}, got {actual_ids}"
            )
    fixture.validate_context_relation_targets(
        {target_type: set(target_ids) for target_type, target_ids in expectations["context_targets"].items()}
    )
    try:
        fixture.validate_context_relation_targets(
            {target_type: set() for target_type in expectations["context_targets"]}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown chronology context relation binding target unexpectedly validated.")
    disabled_topology_packs = replace(
        packs,
        enabled_capabilities=tuple(
            capability for capability in packs.enabled_capabilities if capability != "chronology-context-topology"
        ),
    )
    try:
        parse_chronology_registry(
            fixture_data,
            fixture_root / "valid-registry.yaml",
            disabled_topology_packs,
            work_ids=set(),
            continuity_ids=set(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Chronology context topology loaded without its capability.")
    provenance_targets = fixture.provenance_targets()
    if {key: len(value) for key, value in provenance_targets.items()} != {
        "chronology-context": 4,
        "chronology-context-relation": 7,
        "chronology-context-relation-binding": 3,
    }:
        raise AssertionError("Chronology provenance target counts did not match the V41 fixture.")

    scale_count = 128
    scale_data = copy.deepcopy(fixture_data)
    scale_data["contexts"] = list(scale_data["contexts"])
    scale_data["context_relations"] = list(scale_data["context_relations"])
    for index in range(scale_count):
        scale_data["contexts"].append(
            {
                "id": f"scale-context-{index}",
                "label": f"Scale Context {index}",
                "coordinate_system_id": "control-step",
                "role": "operational",
                "continuity_ids": [],
                "work_ids": [],
                "branch_id": None,
            }
        )
        scale_data["context_relations"].append(
            {
                "id": f"scale-relation-{index}",
                "source_context_id": f"scale-context-{index}",
                "relation_type": "observes",
                "target_context_id": f"scale-context-{(index + 1) % scale_count}",
                "certainty": "exact",
                "bindings": [],
            }
        )
    scale_fixture = parse_chronology_registry(
        scale_data,
        fixture_root / "generated-scale-registry.yaml",
        packs,
        work_ids=set(),
        continuity_ids=set(),
    )
    if len(scale_fixture.context_relations) != len(fixture.context_relations) + scale_count:
        raise AssertionError("Chronology context topology scale extension did not retain every generated relation.")

    invalid_paths = sorted(fixture_root.glob("invalid-*.yaml"))
    for path in invalid_paths:
        try:
            data = load_yaml_file(path, "invalid chronology fixture", expected_schema_version=2)
            parse_chronology_registry(data, path, packs, work_ids=set(), continuity_ids=set())
        except ValueError:
            continue
        raise AssertionError(f"Malformed chronology fixture unexpectedly loaded: {path.name}")

    summary = {
        "schema_version": registry.schema_version,
        "coordinate_systems": len(registry.coordinate_systems),
        "eras": len(registry.eras),
        "positions": len(registry.positions),
        "spans": len(registry.spans),
        "relations": len(registry.relations),
        "mappings": len(registry.mappings),
        "contexts": len(registry.contexts),
        "context_relations": len(registry.context_relations),
        "fixture_context_queries": sum(len(items) for items in expectations["context_queries"].values()),
        "fixture_comparisons": len(expectations["comparisons"]),
        "invalid_fixtures": len(invalid_paths),
        "scale_context_relations": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Chronology validation passed: "
            f"schema {summary['schema_version']}, {summary['coordinate_systems']} project coordinate system, "
            f"{summary['eras']} eras, {summary['contexts']} context, {summary['context_relations']} context relations, "
            f"{summary['fixture_comparisons']} comparisons, {summary['fixture_context_queries']} topology queries, "
            f"and {summary['invalid_fixtures']} malformed fixtures."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
