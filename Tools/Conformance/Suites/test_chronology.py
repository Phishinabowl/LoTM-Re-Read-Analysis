from __future__ import annotations

import argparse
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
        expected_schema_version=1,
    )
    fixture = parse_chronology_registry(
        fixture_data,
        fixture_root / "valid-registry.yaml",
        packs,
        work_ids=set(),
        continuity_ids=set(),
    )
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    for left, right, expected in expectations["comparisons"]:
        actual = fixture.compare_positions(left, right)
        if actual != expected:
            raise AssertionError(f"Chronology comparison {left}/{right}: expected {expected}, got {actual}")

    invalid_paths = sorted(fixture_root.glob("invalid-*.yaml"))
    for path in invalid_paths:
        try:
            data = load_yaml_file(path, "invalid chronology fixture", expected_schema_version=1)
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
        "narrative_contexts": len(registry.narrative_contexts),
        "fixture_comparisons": len(expectations["comparisons"]),
        "invalid_fixtures": len(invalid_paths),
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Chronology validation passed: "
            f"schema {summary['schema_version']}, {summary['coordinate_systems']} project coordinate system, "
            f"{summary['eras']} eras, {summary['narrative_contexts']} narrative context, "
            f"{summary['fixture_comparisons']} comparisons, and {summary['invalid_fixtures']} malformed fixtures."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
