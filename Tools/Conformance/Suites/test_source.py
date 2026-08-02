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
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402
from knowledge_framework.source_config import (  # noqa: E402
    compare_positions,
    load_source_registry,
    validate_source_position,
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


def load_fixture(project, schema_packs, root: Path):
    fixture = fixture_project(project, root)
    resources = load_resource_config(fixture)
    return load_source_registry(fixture, resources, schema_packs)


def assert_counts(registry, expected: dict) -> None:
    direct_fields = (
        "media_modalities",
        "mediums",
        "work_groups",
        "continuities",
        "authority_profiles",
        "works",
        "segments",
        "content_groups",
        "numbering_schemes",
        "ordering_schemes",
        "work_relationships",
        "adaptation_mappings",
        "territories",
        "applicability_scopes",
        "work_production_contexts",
        "manifestations",
        "release_components",
        "release_packages",
        "release_runs",
        "release_events",
        "catalog_placements",
        "platform_offerings",
        "sources",
        "external_identifiers",
    )
    for field in direct_fields:
        if len(getattr(registry, field)) != expected[field]:
            raise AssertionError(f"Source fixture `{field}` count changed.")
    coverage_count = sum(len(source.coverage) for source in registry.sources.values())
    observation_count = sum(len(source.observations) for source in registry.sources.values())
    if coverage_count != expected["coverage_entries"]:
        raise AssertionError("Source fixture coverage count changed.")
    if observation_count != expected["observations"]:
        raise AssertionError("Source fixture observation count changed.")
    if len(registry.reconciliation_targets()) != expected["reconciliation_target_types"]:
        raise AssertionError("Source reconciliation target-type count changed.")
    if len(registry.provenance_targets()) != expected["provenance_target_types"]:
        raise AssertionError("Source provenance target-type count changed.")


def assert_services(registry) -> None:
    if registry.resolve_work_id("ORIGINAL-WORK") != "primary-work":
        raise AssertionError("Source work-alias resolution changed.")
    if registry.resolve_source_id("SCREEN-SOURCE") != "adaptation-source":
        raise AssertionError("Evidence source-alias resolution changed.")
    if registry.resolve_work_id("missing-work") is not None:
        raise AssertionError("Unknown work alias unexpectedly resolved.")
    if registry.reconciliation_target("work", "primary-work") is not registry.works["primary-work"]:
        raise AssertionError("Source reconciliation lookup changed.")
    if (
        registry.provenance_target("coverage-position-range", "primary-chapters-one-two").id
        != "primary-chapters-one-two"
    ):
        raise AssertionError("Nested source provenance lookup changed.")
    highest = registry.highest_precedence_scopes(("adaptation-work-scope", "chapter-one-region-scope"))
    if tuple(item.id for item in highest) != ("chapter-one-region-scope",):
        raise AssertionError("Applicability precedence selection changed.")

    adaptation = registry.applicability_decision("segment", "adaptation-episode-one")
    if adaptation.winning_scope_ids != ("adaptation-work-scope",) or adaptation.matches[0].target_match != "contained":
        raise AssertionError("Contained work-scope applicability changed.")
    chapter = registry.applicability_decision(
        "segment",
        "primary-chapter-one",
        territory_id="sample-region",
        effective_at="2025-02-01T00:00:00Z",
    )
    if chapter.winning_scope_ids != ("chapter-one-region-scope",) or chapter.matches[0].target_match != "exact":
        raise AssertionError("Territorial segment applicability changed.")
    before = registry.applicability_decision(
        "segment",
        "primary-chapter-one",
        territory_id="sample-region",
        effective_at="2024-12-31T00:00:00Z",
    )
    if before.winning_scope_ids:
        raise AssertionError("Applicability accepted a scope before its effective window.")

    primary = registry.authority_decision("comparison-profile", "dialogue", "primary-source", "canonical-text")
    if primary.rank != 1 or primary.winning_rule_id != "primary-dialogue-rule" or primary.inherited:
        raise AssertionError("Exact source authority rule selection changed.")
    adaptation_authority = registry.authority_decision(
        "comparison-profile", "dialogue", "adaptation-source", "animation-visual"
    )
    if (
        adaptation_authority.rank != 2
        or adaptation_authority.winning_rule_id != "adaptation-content-rule"
        or not adaptation_authority.claim_namespace_inherited
    ):
        raise AssertionError("Claim-namespace authority inheritance changed.")
    mode_authority = registry.authority_decision(
        "comparison-profile", "canonical-content", "primary-source", "canonical-text"
    )
    if mode_authority.winning_rule_id != "primary-text-mode-rule" or not mode_authority.evidence_mode_inherited:
        raise AssertionError("Evidence-mode authority inheritance changed.")
    fallback = registry.authority_decision("comparison-profile", "publication-metadata", "primary-source")
    if fallback.rank != 1 or not fallback.priority_fallback:
        raise AssertionError("Source-priority authority fallback changed.")
    comparison = registry.compare_authority(
        "comparison-profile",
        "dialogue",
        (
            ("primary-claim", "primary-source", "canonical-text"),
            ("adaptation-claim", "adaptation-source", "animation-visual"),
        ),
    )
    if comparison.outcome != "winner" or comparison.winning_candidate_ids != ("primary-claim",):
        raise AssertionError("Multi-source authority comparison changed.")

    novel_start = {"work": "primary-work", "volume": 1, "chapter": 1}
    novel_end = {"work": "primary-work", "volume": 1, "chapter": 2}
    validate_source_position(
        novel_start,
        registry.mediums["novel"],
        registry.sources["primary-source"].work_ids,
        registry.works,
        registry.segments,
        registry.ordering_schemes,
        "fixture novel position",
    )
    if compare_positions(novel_start, novel_end, registry.mediums["novel"]) != -1:
        raise AssertionError("Novel position ordering changed.")
    anime_start = {
        "work": "adaptation-work",
        "segment": "adaptation-episode-one",
        "ordering_scheme": "adaptation-release-order",
        "episode": 1,
    }
    anime_end = {
        "work": "adaptation-work",
        "segment": "adaptation-episode-two",
        "ordering_scheme": "adaptation-release-order",
        "episode": 2,
    }
    validate_source_position(
        anime_start,
        registry.mediums["anime"],
        registry.sources["adaptation-source"].work_ids,
        registry.works,
        registry.segments,
        registry.ordering_schemes,
        "fixture anime position",
    )
    if (
        compare_positions(
            anime_start,
            anime_end,
            registry.mediums["anime"],
            registry.ordering_schemes,
        )
        != -1
    ):
        raise AssertionError("Ordering-backed position comparison changed.")


def assert_invalid_queries(registry) -> int:
    actions = (
        lambda: registry.reconciliation_target("unknown", "primary-work"),
        lambda: registry.reconciliation_target("work", "unknown"),
        lambda: registry.provenance_target("unknown", "primary-work"),
        lambda: registry.provenance_target("work", "unknown"),
        lambda: registry.highest_precedence_scopes(()),
        lambda: registry.highest_precedence_scopes(("unknown",)),
        lambda: registry.applicability_decision("unknown", "primary-work"),
        lambda: registry.applicability_decision("work", "unknown"),
        lambda: registry.applicability_decision("work", "primary-work", territory_id="unknown"),
        lambda: registry.authority_decision("unknown", "dialogue", "primary-source"),
        lambda: registry.authority_decision("comparison-profile", "dialogue", "unknown"),
        lambda: registry.authority_decision("comparison-profile", "unknown", "primary-source"),
        lambda: registry.authority_decision("comparison-profile", "dialogue", "primary-source", "animation-visual"),
        lambda: registry.compare_authority("comparison-profile", "dialogue", ()),
        lambda: registry.compare_authority(
            "comparison-profile",
            "dialogue",
            (
                ("duplicate", "primary-source", None),
                ("duplicate", "adaptation-source", None),
            ),
        ),
    )
    for index, action in enumerate(actions):
        expect_rejected(action, f"Invalid source service query was accepted: {index}")
    return len(actions)


def add_scale_sources(document: dict, count: int) -> None:
    for index in range(count):
        source_id = f"scale-source-{index:03d}"
        document["sources"][source_id] = {
            "lifecycle": "active",
            "label": f"Scale Source {index:03d}",
            "work_ids": ["primary-work"],
            "manifestation_id": "primary-edition",
            "release_component_ids": [],
            "medium_id": "novel",
            "locator_medium_ids": ["novel"],
            "container_format_ids": ["epub"],
            "role": "primary-edition",
            "comparison_group": "scale-group",
            "priority": index + 1,
            "aliases": [],
            "evidence_modes": ["canonical-text"],
            "observations": [],
            "coverage": [],
            "resource_bindings": [],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run source-registry conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    schema_packs = load_schema_pack_registry(project)
    canonical_resources = load_resource_config(project)
    canonical = load_source_registry(project, canonical_resources, schema_packs)
    fixture_root = root / "Framework" / "Data" / "Sources"
    base_root = fixture_root / "base"
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported source conformance expectation schema.")
    base_document = json.loads((base_root / "registry.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="knowledge-source-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_root = temp_root / "valid"
        shutil.copytree(base_root, valid_root)
        fixture_registry = load_fixture(project, schema_packs, valid_root)
        assert_counts(fixture_registry, expectations["valid_counts"])
        assert_services(fixture_registry)
        invalid_query_count = assert_invalid_queries(fixture_registry)
        if invalid_query_count != expectations["invalid_query_cases"]:
            raise AssertionError("Source invalid-query expectation count changed.")

        for case in expectations["invalid_cases"]:
            case_root = temp_root / case["id"]
            shutil.copytree(base_root, case_root)
            document = copy.deepcopy(base_document)
            for operation in case["operations"]:
                apply_operation(document, operation, case_root)
            write_json(case_root / "registry.json", document)
            expect_rejected(
                lambda case_root=case_root: load_fixture(project, schema_packs, case_root),
                f"Malformed source configuration was accepted: {case['id']}",
            )

        scale_root = temp_root / "scale"
        shutil.copytree(base_root, scale_root)
        scale_document = copy.deepcopy(base_document)
        scale_count = expectations["scale_additional_sources"]
        add_scale_sources(scale_document, scale_count)
        write_json(scale_root / "registry.json", scale_document)
        scale_registry = load_fixture(project, schema_packs, scale_root)
        if len(scale_registry.sources) != len(fixture_registry.sources) + scale_count:
            raise AssertionError("Source scale composition count changed.")

    summary = {
        "schema_version": 1,
        "canonical_works": len(canonical.works),
        "canonical_sources": len(canonical.sources),
        "fixture_works": len(fixture_registry.works),
        "fixture_sources": len(fixture_registry.sources),
        "fixture_provenance_target_types": len(fixture_registry.provenance_targets()),
        "invalid_configuration_cases": len(expectations["invalid_cases"]),
        "invalid_query_cases": invalid_query_count,
        "scale_additional_sources": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Source conformance passed: "
            f"{summary['canonical_works']} canonical works, "
            f"{summary['canonical_sources']} canonical sources, "
            f"{summary['invalid_configuration_cases']} malformed configurations, and "
            f"{summary['scale_additional_sources']} additional scale sources."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
