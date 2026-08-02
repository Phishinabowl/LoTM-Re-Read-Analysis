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

from knowledge_framework.entity_config import load_entity_registry  # noqa: E402
from knowledge_framework.project_config import (  # noqa: E402
    ContentRootConfig,
    ResourceRootConfig,
    load_project_config,
    resolve_project_root,
)
from knowledge_framework.resource_config import load_resource_config  # noqa: E402
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402
from knowledge_framework.source_config import load_source_registry  # noqa: E402
from knowledge_framework.taxonomy_config import load_taxonomy_config  # noqa: E402


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
        raise AssertionError(f"Unknown fixture mutation operation: {operation['op']}")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def taxonomy_fixture_project(project, root: Path):
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


def source_fixture_project(project, root: Path):
    resource_root = ResourceRootConfig(
        id="source-files",
        relative_path=Path("source-files"),
        path=root / "source-files",
        required=True,
    )
    return replace(
        project,
        root=root,
        resources_registry=root / "resources.json",
        sources_registry=root / "registry.json",
        resource_roots=(resource_root,),
    )


def load_fixture(project, taxonomy, sources, schema_packs, root: Path):
    fixture_project = replace(project, entities_registry=root / "registry.json")
    return load_entity_registry(fixture_project, taxonomy, sources, schema_packs)


def assert_counts(registry, expected: dict) -> None:
    fields = (
        "entities",
        "entity_relationship_types",
        "entity_relationships",
        "incarnations",
        "incarnation_bindings",
        "incarnation_relationship_types",
        "incarnation_relationships",
        "identity_phases",
        "identity_phase_bindings",
        "identity_phase_relationship_types",
        "identity_phase_relationships",
    )
    for field in fields:
        if len(getattr(registry, field)) != expected[field]:
            raise AssertionError(f"Entity fixture `{field}` count changed.")
    if len(registry.reconciliation_targets()) != expected["reconciliation_target_types"]:
        raise AssertionError("Entity reconciliation target-type count changed.")
    if len(registry.provenance_targets()) != expected["provenance_target_types"]:
        raise AssertionError("Entity provenance target-type count changed.")


def assert_services(registry) -> None:
    if registry.resolve_entity_id("FIRST-CONCEPT") != "alpha-concept":
        raise AssertionError("Entity alias resolution changed.")
    if registry.resolve_entity_ids("shared-subject") != ("alpha-concept", "beta-concept"):
        raise AssertionError("Ambiguous entity resolution changed.")
    if registry.resolve_incarnation_ids("shared-incarnation") != ("alpha-primary", "beta-primary"):
        raise AssertionError("Ambiguous incarnation resolution changed.")
    if registry.resolve_identity_phase_ids("shared-phase") != (
        "alpha-primary-early",
        "beta-concept-phase",
    ):
        raise AssertionError("Ambiguous identity-phase resolution changed.")
    if registry.resolve_entity_id("missing-entity") is not None:
        raise AssertionError("Unknown entity alias unexpectedly resolved.")
    if tuple(item.id for item in registry.incarnations_for_entity("alpha-concept")) != (
        "alpha-primary",
        "alpha-adaptation",
    ):
        raise AssertionError("Entity-to-incarnation query changed.")
    if tuple(item.id for item in registry.relationships_for_entity("alpha-concept")) != (
        "beta-succeeds-alpha",
        "gamma-inspired-by-alpha",
    ):
        raise AssertionError("Entity relationship query changed.")
    if tuple(item.id for item in registry.bindings_for_incarnation("alpha-primary")) != ("alpha-primary-binding",):
        raise AssertionError("Incarnation binding query changed.")
    if tuple(item.id for item in registry.relationships_for_incarnation("alpha-primary")) != (
        "alpha-continuity-counterparts",
    ):
        raise AssertionError("Incarnation relationship query changed.")
    if tuple(item.id for item in registry.phases_for_subject("entity-incarnation", "alpha-primary")) != (
        "alpha-primary-early",
        "alpha-primary-late",
    ):
        raise AssertionError("Incarnation identity-phase query changed.")
    if tuple(item.id for item in registry.phases_for_subject("entity", "beta-concept")) != ("beta-concept-phase",):
        raise AssertionError("Entity identity-phase query changed.")
    if tuple(item.id for item in registry.bindings_for_identity_phase("alpha-primary-early")) != (
        "alpha-early-binding",
    ):
        raise AssertionError("Identity-phase binding query changed.")
    if tuple(item.id for item in registry.relationships_for_identity_phase("alpha-primary-early")) != (
        "alpha-late-succeeds-early",
    ):
        raise AssertionError("Identity-phase relationship query changed.")
    if registry.identity_subject_target("entity", "alpha-concept") is not registry.entities["alpha-concept"]:
        raise AssertionError("Identity subject lookup changed.")
    if (
        registry.identity_target("identity-phase", "alpha-primary-early")
        is not registry.identity_phases["alpha-primary-early"]
    ):
        raise AssertionError("Identity target lookup changed.")
    provider = registry.reconciliation_provider()
    if provider["provider_id"] != "entity" or tuple(provider["targets"]) != (
        "entity",
        "entity-incarnation",
        "identity-phase",
    ):
        raise AssertionError("Entity reconciliation provider changed.")
    relationship = registry.provenance_target("entity-relationship", "gamma-inspired-by-alpha")
    if relationship.basis_roles != ("identity", "appearance"):
        raise AssertionError("Entity provenance relationship lookup changed.")


def assert_invalid_queries(registry) -> int:
    actions = (
        lambda: registry.resolve_entity_id("shared-subject"),
        lambda: registry.resolve_incarnation_id("shared-incarnation"),
        lambda: registry.resolve_identity_phase_id("shared-phase"),
        lambda: registry.incarnations_for_entity("unknown"),
        lambda: registry.relationships_for_entity("unknown"),
        lambda: registry.bindings_for_incarnation("unknown"),
        lambda: registry.relationships_for_incarnation("unknown"),
        lambda: registry.phases_for_subject("unknown", "alpha-concept"),
        lambda: registry.phases_for_subject("entity", "unknown"),
        lambda: registry.bindings_for_identity_phase("unknown"),
        lambda: registry.relationships_for_identity_phase("unknown"),
        lambda: registry.identity_subject_target("unknown", "alpha-concept"),
        lambda: registry.identity_subject_target("entity", "unknown"),
        lambda: registry.identity_target("unknown", "alpha-concept"),
        lambda: registry.provenance_target("unknown", "alpha-concept"),
    )
    for index, action in enumerate(actions):
        expect_rejected(action, f"Invalid entity service query was accepted: {index}")
    return len(actions)


def add_scale_entities(document: dict, count: int) -> None:
    for index in range(count):
        entity_id = f"scale-entity-{index:03d}"
        document["entities"][entity_id] = {
            "lifecycle": "active",
            "primary_category_id": "subject-alpha",
            "category_ids": ["subject-alpha"],
            "label": f"Scale Entity {index:03d}",
            "aliases": [],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run entity-registry conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    schema_packs = load_schema_pack_registry(project)
    canonical_taxonomy = load_taxonomy_config(project)
    canonical_resources = load_resource_config(project)
    canonical_sources = load_source_registry(project, canonical_resources, schema_packs)
    canonical = load_entity_registry(project, canonical_taxonomy, canonical_sources, schema_packs)

    taxonomy_root = root / "Framework" / "Data" / "Taxonomy" / "base"
    taxonomy = load_taxonomy_config(taxonomy_fixture_project(project, taxonomy_root))
    source_root = root / "Framework" / "Data" / "Sources" / "base"
    source_project = source_fixture_project(project, source_root)
    resources = load_resource_config(source_project)
    sources = load_source_registry(source_project, resources, schema_packs)

    fixture_root = root / "Framework" / "Data" / "Entities"
    base_root = fixture_root / "base"
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported entity conformance expectation schema.")
    base_document = json.loads((base_root / "registry.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="knowledge-entity-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_root = temp_root / "valid"
        shutil.copytree(base_root, valid_root)
        fixture_registry = load_fixture(project, taxonomy, sources, schema_packs, valid_root)
        assert_counts(fixture_registry, expectations["valid_counts"])
        assert_services(fixture_registry)
        invalid_query_count = assert_invalid_queries(fixture_registry)
        if invalid_query_count != expectations["invalid_query_cases"]:
            raise AssertionError("Entity invalid-query expectation count changed.")

        for case in expectations["invalid_cases"]:
            case_root = temp_root / case["id"]
            shutil.copytree(base_root, case_root)
            document = copy.deepcopy(base_document)
            for operation in case["operations"]:
                apply_operation(document, operation)
            write_json(case_root / "registry.json", document)
            expect_rejected(
                lambda case_root=case_root: load_fixture(
                    project,
                    taxonomy,
                    sources,
                    schema_packs,
                    case_root,
                ),
                f"Malformed entity configuration was accepted: {case['id']}",
            )

        scale_root = temp_root / "scale"
        shutil.copytree(base_root, scale_root)
        scale_document = copy.deepcopy(base_document)
        scale_count = expectations["scale_additional_entities"]
        add_scale_entities(scale_document, scale_count)
        write_json(scale_root / "registry.json", scale_document)
        scale_registry = load_fixture(project, taxonomy, sources, schema_packs, scale_root)
        if len(scale_registry.entities) != len(fixture_registry.entities) + scale_count:
            raise AssertionError("Entity scale composition count changed.")

    summary = {
        "schema_version": 1,
        "canonical_entities": len(canonical.entities),
        "canonical_incarnations": len(canonical.incarnations),
        "canonical_identity_phases": len(canonical.identity_phases),
        "fixture_entities": len(fixture_registry.entities),
        "fixture_incarnations": len(fixture_registry.incarnations),
        "fixture_identity_phases": len(fixture_registry.identity_phases),
        "fixture_provenance_target_types": len(fixture_registry.provenance_targets()),
        "invalid_configuration_cases": len(expectations["invalid_cases"]),
        "invalid_query_cases": invalid_query_count,
        "scale_additional_entities": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Entity conformance passed: "
            f"{summary['fixture_entities']} fixture entities, "
            f"{summary['fixture_incarnations']} incarnations, "
            f"{summary['invalid_configuration_cases']} malformed configurations, and "
            f"{summary['scale_additional_entities']} additional scale entities."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
