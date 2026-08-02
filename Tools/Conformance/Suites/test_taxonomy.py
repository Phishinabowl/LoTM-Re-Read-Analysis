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
    ContentRootConfig,
    load_project_config,
    resolve_project_root,
)
from knowledge_framework.taxonomy_config import load_taxonomy_config  # noqa: E402


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
    content_roots = (
        ContentRootConfig(
            id="articles",
            relative_path=Path("content/articles"),
            path=root / "content" / "articles",
            provenance_mode="fixed",
            provenance_label="article",
        ),
        ContentRootConfig(
            id="records",
            relative_path=Path("content/records"),
            path=root / "content" / "records",
            provenance_mode="fixed",
            provenance_label="record",
        ),
    )
    return replace(
        project,
        root=root,
        taxonomy_registry=root / "registry.json",
        content_roots=content_roots,
    )


def assert_valid_fixture(registry, project, expected: dict) -> None:
    if len(registry.content_types) != expected["content_types"]:
        raise AssertionError("Taxonomy fixture content-type count changed.")
    if len(registry.categories) != expected["categories"]:
        raise AssertionError("Taxonomy fixture category count changed.")
    if (
        sum(category.lifecycle == "active" for category in registry.categories.values())
        != expected["active_categories"]
    ):
        raise AssertionError("Taxonomy fixture active-category count changed.")
    qa_roots = [root.id for root in registry.content_roots_for_qa_pages(project)]
    if qa_roots != expected["qa_root_ids"]:
        raise AssertionError("Taxonomy QA content-root selection changed.")
    alpha = registry.categories["subject-alpha"]
    if list(alpha.placements or {}) != expected["subject_alpha_placements"]:
        raise AssertionError("Taxonomy category placement order changed.")
    alpha_page = (alpha.placements or {})["subject-page"]
    if str(alpha_page.relative_folder).replace("\\", "/") != expected["subject_alpha_page_folder"]:
        raise AssertionError("Taxonomy relative placement changed.")
    if str(alpha_page.template).replace("\\", "/") != expected["subject_alpha_page_template"]:
        raise AssertionError("Taxonomy placement template selection changed.")
    fixed = registry.content_types["fixed-index"]
    if str(fixed.record_path).replace("\\", "/") != expected["fixed_record_path"]:
        raise AssertionError("Taxonomy fixed record path changed.")
    provider = registry.reconciliation_provider()
    if provider["provider_id"] != "taxonomy" or list(provider["targets"]) != expected["reconciliation_target_types"]:
        raise AssertionError("Taxonomy reconciliation provider changed.")
    if registry.reconciliation_target("category", "subject-alpha") is not alpha:
        raise AssertionError("Taxonomy reconciliation category lookup changed.")
    if registry.reconciliation_target("content-type", "subject-page") is not registry.content_types["subject-page"]:
        raise AssertionError("Taxonomy reconciliation content-type lookup changed.")


def write_scale_fixture(root: Path, base_document: dict, category_count: int) -> None:
    content_type = copy.deepcopy(base_document["content_types"]["subject-page"])
    categories = {}
    for index in range(category_count):
        category_id = f"scale-subject-{index:03d}"
        prefix = f"scale-{index:03d}"
        categories[category_id] = {
            "lifecycle": "active",
            "label": f"Scale Subject {index:03d}",
            "plural_label": f"Scale Subjects {index:03d}",
            "canonical_pages_enabled": True,
            "metadata_type": f"Scale Subject {index:03d}",
            "subject_slug_prefix": prefix,
            "subject_slug_pattern": f"^{prefix}-[a-z0-9][a-z0-9-]*$",
            "graph_class": f"scale-class-{index:03d}",
            "placements": {"subject-page": {"relative_folder": f"Scale-{index:03d}"}},
        }
    write_json(
        root / "registry.json",
        {"schema_version": 2, "content_types": {"subject-page": content_type}, "categories": categories},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run taxonomy configuration conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    canonical = load_taxonomy_config(project)
    fixture_root = root / "Framework" / "Data" / "Taxonomy"
    base_root = fixture_root / "base"
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported taxonomy conformance expectation schema.")
    base_document = json.loads((base_root / "registry.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="knowledge-taxonomy-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_root = temp_root / "valid"
        shutil.copytree(base_root, valid_root)
        valid_project = fixture_project(project, valid_root)
        fixture_registry = load_taxonomy_config(valid_project)
        assert_valid_fixture(fixture_registry, valid_project, expectations["valid"])
        expect_rejected(
            lambda: fixture_registry.reconciliation_target("unknown", "subject-alpha"),
            "Unsupported taxonomy reconciliation target type was accepted.",
        )
        expect_rejected(
            lambda: fixture_registry.reconciliation_target("category", "unknown"),
            "Unknown taxonomy reconciliation target was accepted.",
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
                lambda case_project=case_project: load_taxonomy_config(case_project),
                f"Malformed taxonomy configuration was accepted: {case['id']}",
            )

        scale_root = temp_root / "scale"
        shutil.copytree(base_root, scale_root)
        scale_count = expectations["scale_category_count"]
        write_scale_fixture(scale_root, base_document, scale_count)
        scale_project = fixture_project(project, scale_root)
        scale_registry = load_taxonomy_config(scale_project)
        if len(scale_registry.content_types) != 1 or len(scale_registry.categories) != scale_count:
            raise AssertionError("Taxonomy scale composition counts changed.")

    summary = {
        "schema_version": 1,
        "canonical_content_types": len(canonical.content_types),
        "canonical_categories": len(canonical.categories),
        "fixture_content_types": len(fixture_registry.content_types),
        "fixture_categories": len(fixture_registry.categories),
        "fixture_active_categories": sum(
            category.lifecycle == "active" for category in fixture_registry.categories.values()
        ),
        "invalid_configuration_cases": len(expectations["invalid_cases"]),
        "invalid_query_cases": expectations["invalid_query_cases"],
        "scale_category_count": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Taxonomy conformance passed: "
            f"{summary['canonical_content_types']} canonical content types, "
            f"{summary['canonical_categories']} canonical categories, "
            f"{summary['invalid_configuration_cases']} malformed configurations, and "
            f"{summary['scale_category_count']} scale categories."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
