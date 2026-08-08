"""Conformance vectors for project-independent framework catalog services."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
import tempfile


TOOLS_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = TOOLS_ROOT / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.framework_catalog import (  # noqa: E402
    compose_framework_catalog_project_view,
    compose_framework_catalog_project_view_selection,
    compose_framework_catalog_selection,
    framework_catalog_json,
    framework_catalog_project_view_json,
    load_framework_catalog,
)
from knowledge_framework.effective_schema import load_effective_project_schema  # noqa: E402
from knowledge_framework.framework_paths import resolve_framework_root  # noqa: E402


FIXTURE_PACKS = ("fixture-core", "fixture-domain", "fixture-extension")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    return parser


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=True, indent=2) + "\n")


def assert_rejected(action, expected_text: str, expected_classification: str | None = None) -> None:
    try:
        action()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"Expected error containing {expected_text!r}, got: {exc}") from exc
        if expected_classification is not None and getattr(exc, "classification", None) != expected_classification:
            raise AssertionError(
                f"Expected classification {expected_classification!r}, got {getattr(exc, 'classification', None)!r}."
            ) from exc
        return
    raise AssertionError(f"Expected rejection containing {expected_text!r}.")


def prepare_root(source_root: Path, target_root: Path) -> Path:
    framework = target_root / "Framework"
    data = framework / "Data"
    packs = framework / "Packs"
    data.mkdir(parents=True)
    packs.mkdir()
    shutil.copy2(source_root / "Framework" / "Data" / "unicode-lookup-16.0.0.json", data)
    write_text(
        framework / "framework.yaml",
        "schema_version: 1\n"
        "framework_id: fixture-framework\n"
        "paths:\n"
        "  packs: Packs\n"
        "registries:\n"
        "  lookup_keys: Data/unicode-lookup-16.0.0.json\n",
    )
    source_packs = source_root / "Framework" / "Data" / "Schema-Packs" / "base" / "packs"
    for pack_id in FIXTURE_PACKS:
        target = packs / pack_id / "pack.yaml"
        target.parent.mkdir()
        shutil.copy2(source_packs / f"{pack_id}.json", target)
    (packs / "ignored-directory").mkdir()
    write_text(packs / "ignored-directory" / "README.md", "No pack manifest.\n")
    return target_root.resolve()


def mutate_pack(root: Path, pack_id: str, action) -> None:
    path = root / "Framework" / "Packs" / pack_id / "pack.yaml"
    document = json.loads(path.read_text(encoding="utf-8"))
    action(document)
    write_json(path, document)


def scale_pack(index: int) -> dict:
    pack_id = f"scale-pack-{index:03d}"
    capability_id = f"scale-capability-{index:03d}"
    return {
        "schema_version": 5,
        "pack_id": pack_id,
        "pack_version": 1,
        "lifecycle": "active",
        "pack_kind": "extension",
        "classification": {
            "family": "scale",
            "role": "extension",
            "scope": "domain-neutral",
            "domains": [],
            "bridge_pack_ids": [],
        },
        "presentation": {
            "localization_key": f"pack.{pack_id}",
            "default_locale": "en",
            "label": f"Scale Pack {index:03d}",
            "short_description": "Generated catalog scale fixture.",
            "long_description": "Exercises deterministic installed-pack catalog behavior at scale.",
            "maturity": "experimental",
            "intended_audiences": [{"id": "tester", "label": "Tester", "description": "Runs catalog scale tests."}],
            "use_cases": [{"id": "scale", "label": "Scale", "description": "Exercises catalog scale."}],
            "examples": [],
            "prerequisites": [],
            "provided_behaviors": [{"id": "catalog", "label": "Catalog", "description": "Provides one catalog row."}],
            "exclusions": [{"id": "project", "label": "No project", "description": "Contains no project data."}],
            "documentation": [],
            "search_keywords": ["catalog", "scale"],
        },
        "dependencies": [],
        "capabilities": [
            {
                "id": capability_id,
                "lifecycle": "available",
                "presentation": {
                    "localization_key": f"capability.{capability_id}",
                    "label": f"Scale Capability {index:03d}",
                    "description": "Generated catalog scale capability.",
                },
            }
        ],
        "controlled_values": {f"scale.value-{index:03d}": [f"value-{index:03d}"]},
    }


def main() -> int:
    args = build_parser().parse_args()
    root = resolve_framework_root(args.root, executable_path=__file__)
    expectations = json.loads(
        (root / "Framework" / "Data" / "Framework-Catalog" / "expectations.json").read_text(encoding="utf-8")
    )
    temp_root = Path(tempfile.mkdtemp(prefix="knowledge-framework-catalog-"))
    invalid_cases = 0

    try:
        canonical = load_framework_catalog(root)
        canonical_document = canonical.to_dict()
        summary = canonical_document["summary"]
        assert summary["pack_count"] == expectations["canonical_pack_count"]
        assert summary["capability_count"] == expectations["canonical_capability_count"]
        assert summary["available_capability_count"] == expectations["canonical_available_capability_count"]
        assert summary["planned_capability_count"] == expectations["canonical_planned_capability_count"]
        assert summary["deprecated_capability_count"] == expectations["canonical_deprecated_capability_count"]
        assert framework_catalog_json(canonical) == framework_catalog_json(load_framework_catalog(root))

        effective_schema = load_effective_project_schema(root)
        catalog_before_view = framework_catalog_json(canonical)
        project_view = compose_framework_catalog_project_view(canonical, effective_schema)
        assert project_view["contract"] == "framework-catalog-project-view"
        if effective_schema.project["project_id"] == "lotm-analysis":
            assert project_view["summary"] == expectations["project_view_summary"]
        assert project_view["summary"]["pack_count"] == len(canonical.packs)
        assert project_view["summary"]["selected_pack_count"] == len(effective_schema.packs)
        assert project_view["summary"]["capability_count"] == len(canonical.capabilities)
        assert project_view["summary"]["selected_capability_count"] == len(effective_schema.capabilities)
        assert project_view["summary"]["enabled_capability_count"] == sum(
            row["enabled"] for row in effective_schema.capabilities
        )
        assert framework_catalog_project_view_json(project_view) == framework_catalog_project_view_json(
            compose_framework_catalog_project_view(canonical, effective_schema)
        )
        assert framework_catalog_json(canonical) == catalog_before_view
        selected_pack_id = effective_schema.packs[0]["id"]
        selected_pack = next(row for row in project_view["packs"] if row["id"] == selected_pack_id)
        unselected_pack = next(row for row in project_view["packs"] if not row["project_state"]["selected"])
        enabled_capability_id = next(row["id"] for row in effective_schema.capabilities if row["enabled"])
        enabled_capability = next(row for row in project_view["capabilities"] if row["id"] == enabled_capability_id)
        planned_capability = next(row for row in project_view["capabilities"] if row["project_state"]["planned"])
        assert selected_pack["project_state"]["selected"] and selected_pack["project_state"]["used_by_project"]
        assert not unselected_pack["project_state"]["selected"] and unselected_pack["project_state"]["available"]
        assert enabled_capability["project_state"]["enabled"]
        planned_selected = planned_capability["id"] in {row["id"] for row in effective_schema.capabilities}
        assert planned_capability["project_state"] == {
            "selected": planned_selected,
            "available": False,
            "enabled": False,
            "deprecated": False,
            "planned": True,
            "used_by_project": False,
            "unavailable_reason": "capability-lifecycle-planned",
        }
        project_selection = compose_framework_catalog_project_view_selection(
            canonical,
            project_view,
            pack_id=selected_pack_id.upper(),
            capability_id=enabled_capability_id.upper(),
        )
        assert project_selection["contract"] == "framework-catalog-project-view-selection"
        assert [row["id"] for row in project_selection["packs"]] == [selected_pack_id]
        assert [row["id"] for row in project_selection["capabilities"]] == [enabled_capability_id]
        assert_rejected(
            lambda: compose_framework_catalog_project_view(
                canonical,
                replace(
                    effective_schema,
                    project={**effective_schema.project, "framework_id": "wrong-framework"},
                ),
            ),
            "does not match catalog framework",
        )
        assert_rejected(
            lambda: compose_framework_catalog_project_view(
                canonical,
                replace(
                    effective_schema,
                    packs=(*effective_schema.packs, {**effective_schema.packs[0], "id": "missing-pack"}),
                ),
            ),
            "absent from the framework catalog",
        )

        selection = compose_framework_catalog_selection(
            canonical,
            pack_id="NARRATIVE-MEDIA",
            capability_id="NARRATIVE-TIME-LOOPS",
        )
        assert [row["id"] for row in selection["packs"]] == ["narrative-media"]
        assert [row["id"] for row in selection["capabilities"]] == ["narrative-time-loops"]
        assert_rejected(
            lambda: compose_framework_catalog_selection(canonical, pack_id="unknown-pack"),
            "Unknown framework-catalog pack ID",
        )

        ambiguous = replace(
            canonical,
            packs=(
                {"id": "ambiguous-pack", "record_id": "one"},
                {"id": "AMBIGUOUS-PACK", "record_id": "two"},
            ),
        )
        assert_rejected(
            lambda: compose_framework_catalog_selection(ambiguous, pack_id="Ambiguous-Pack"),
            "Ambiguous framework-catalog pack ID",
        )

        fixture_root = prepare_root(root, temp_root / "fixture")
        fixture = load_framework_catalog(fixture_root).to_dict()
        assert fixture["summary"]["pack_count"] == expectations["fixture_pack_count"]
        assert fixture["summary"]["capability_count"] == expectations["fixture_capability_count"]
        extension = next(row for row in fixture["packs"] if row["id"] == "fixture-extension")
        assert extension["discoverability"] == {"installed": True, "selectable": False}
        shared = next(row for row in fixture["capabilities"] if row["id"] == "shared-capability")
        assert [row["pack_id"] for row in shared["providers"]] == ["fixture-core", "fixture-domain"]
        assert shared["effective_lifecycle"] == "available"
        planned = next(row for row in fixture["capabilities"] if row["id"] == "planned-capability")
        deprecated = next(row for row in fixture["capabilities"] if row["id"] == "deprecated-capability")
        assert planned["planned"] and not planned["available"]
        assert deprecated["deprecated"] and not deprecated["available"]

        missing_root = prepare_root(root, temp_root / "missing-dependency")
        mutate_pack(
            missing_root,
            "fixture-domain",
            lambda value: value.__setitem__("dependencies", [{"pack_id": "missing-pack", "minimum_version": 1}]),
        )
        assert_rejected(
            lambda: load_framework_catalog(missing_root),
            "requires missing pack",
            "catalog-composition",
        )
        invalid_cases += 1

        version_root = prepare_root(root, temp_root / "dependency-version")
        mutate_pack(
            version_root,
            "fixture-domain",
            lambda value: value.__setitem__("dependencies", [{"pack_id": "fixture-core", "minimum_version": 99}]),
        )
        assert_rejected(
            lambda: load_framework_catalog(version_root),
            "version 99 or newer",
            "catalog-composition",
        )
        invalid_cases += 1

        cycle_root = prepare_root(root, temp_root / "dependency-cycle")
        mutate_pack(
            cycle_root,
            "fixture-core",
            lambda value: value.__setitem__("dependencies", [{"pack_id": "fixture-domain", "minimum_version": 1}]),
        )
        assert_rejected(
            lambda: load_framework_catalog(cycle_root),
            "dependency graph contains a cycle",
            "catalog-composition",
        )
        invalid_cases += 1

        mismatch_root = prepare_root(root, temp_root / "directory-mismatch")
        source = mismatch_root / "Framework" / "Packs" / "fixture-core"
        target = mismatch_root / "Framework" / "Packs" / "wrong-name"
        source.rename(target)
        assert_rejected(lambda: load_framework_catalog(mismatch_root), "wrong-name", "pack-parsing")
        invalid_cases += 1

        malformed_root = prepare_root(root, temp_root / "malformed-pack")
        mutate_pack(
            malformed_root,
            "fixture-core",
            lambda value: value.__setitem__("unknown_catalog_field", True),
        )
        assert_rejected(
            lambda: load_framework_catalog(malformed_root),
            "unsupported field",
            "pack-parsing",
        )
        invalid_cases += 1

        discovery_root = prepare_root(root, temp_root / "invalid-directory")
        source = discovery_root / "Framework" / "Packs" / "fixture-core"
        source.rename(discovery_root / "Framework" / "Packs" / "Invalid_Directory")
        assert_rejected(
            lambda: load_framework_catalog(discovery_root),
            "lowercase kebab-case",
            "installed-pack-discovery",
        )
        invalid_cases += 1

        manifest_root = prepare_root(root, temp_root / "invalid-manifest")
        write_text(manifest_root / "Framework" / "framework.yaml", "schema_version: 1\nunknown: true\n")
        assert_rejected(
            lambda: load_framework_catalog(manifest_root),
            "unsupported field",
            "installation-manifest",
        )
        invalid_cases += 1

        lookup_root = prepare_root(root, temp_root / "invalid-lookup")
        write_text(
            lookup_root / "Framework" / "Data" / "unicode-lookup-16.0.0.json",
            '{"schema_version": 1, "unknown": true}\n',
        )
        assert_rejected(
            lambda: load_framework_catalog(lookup_root),
            "Lookup-key registry",
            "lookup-registry",
        )
        invalid_cases += 1

        scale_root = prepare_root(root, temp_root / "scale")
        shutil.rmtree(scale_root / "Framework" / "Packs")
        packs_root = scale_root / "Framework" / "Packs"
        for index in range(expectations["scale_pack_count"]):
            write_json(packs_root / f"scale-pack-{index:03d}" / "pack.yaml", scale_pack(index))
        scale = load_framework_catalog(scale_root).to_dict()
        assert scale["summary"]["pack_count"] == expectations["scale_pack_count"]
        assert scale["summary"]["capability_count"] == expectations["scale_pack_count"]
    finally:
        shutil.rmtree(temp_root)

    if invalid_cases != expectations["invalid_cases"]:
        raise AssertionError(f"Expected {expectations['invalid_cases']} invalid cases, got {invalid_cases}.")

    result = {
        "ambiguity_cases": 1,
        "canonical_capability_count": expectations["canonical_capability_count"],
        "canonical_pack_count": expectations["canonical_pack_count"],
        "fixture_capability_count": expectations["fixture_capability_count"],
        "fixture_pack_count": expectations["fixture_pack_count"],
        "invalid_cases": invalid_cases,
        "project_view_cases": 8,
        "scale_pack_count": expectations["scale_pack_count"],
        "selection_cases": 3,
    }
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Framework-catalog conformance passed: "
            f"{result['canonical_pack_count']} canonical packs, "
            f"{result['canonical_capability_count']} canonical capabilities, "
            f"{invalid_cases} invalid cases, {result['scale_pack_count']} scale packs."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
