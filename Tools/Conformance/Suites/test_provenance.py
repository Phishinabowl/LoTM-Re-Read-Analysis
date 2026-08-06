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

from knowledge_framework.chronology_config import (  # noqa: E402
    load_chronology_registry,
    parse_chronology_registry,
)
from knowledge_framework.entity_config import load_entity_registry  # noqa: E402
from knowledge_framework.interpretation_config import load_interpretation_registry  # noqa: E402
from knowledge_framework.hosting_config import load_hosted_identity_registry  # noqa: E402
from knowledge_framework.occurrence_config import (  # noqa: E402
    load_occurrence_registry,
    parse_occurrence_registry,
)
from knowledge_framework.project_config import (  # noqa: E402
    ContentRootConfig,
    ResourceRootConfig,
    load_project_config,
    resolve_project_root,
)
from knowledge_framework.provenance_config import load_provenance_registry  # noqa: E402
from knowledge_framework.reconciliation_config import load_reconciliation_registry  # noqa: E402
from knowledge_framework.resource_config import load_resource_config  # noqa: E402
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402
from knowledge_framework.source_config import load_source_registry  # noqa: E402
from knowledge_framework.taxonomy_config import load_taxonomy_config  # noqa: E402
from knowledge_framework.strict_yaml import load_yaml_file  # noqa: E402


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
        ContentRootConfig("articles", Path("content/articles"), root / "content" / "articles", "fixed", "article"),
        ContentRootConfig("records", Path("content/records"), root / "content" / "records", "fixed", "record"),
    )
    return replace(project, root=root, taxonomy_registry=root / "registry.json", content_roots=content_roots)


def source_fixture_project(project, root: Path):
    resource_root = ResourceRootConfig("source-files", Path("source-files"), root / "source-files", True)
    return replace(
        project,
        root=root,
        resources_registry=root / "resources.json",
        sources_registry=root / "registry.json",
        resource_roots=(resource_root,),
    )


def extend_source_document(document: dict) -> None:
    primary = document["sources"]["primary-source"]
    for source_id, label, comparison_group in (
        ("corroborating-source", "Corroborating Source", "sample-narrative"),
        ("incomparable-source", "Incomparable Source", "external-comparison"),
    ):
        source = copy.deepcopy(primary)
        source["label"] = label
        source["aliases"] = []
        source["observations"] = []
        source["coverage"] = []
        source["resource_bindings"] = []
        source["comparison_group"] = comparison_group
        document["sources"][source_id] = source
    document["applicability_scopes"].extend(
        [
            {
                "id": "reported-alpha-name-scope",
                "target_type": "provenance-claim",
                "target_id": "reported-alpha-name",
                "territory_ids": [],
                "precedence": 20,
            },
            {
                "id": "confirmed-alpha-name-scope",
                "target_type": "provenance-claim",
                "target_id": "confirmed-alpha-name",
                "territory_ids": [],
                "precedence": 10,
            },
            {
                "id": "inner-loop-cardinality-scope",
                "target_type": "provenance-claim",
                "target_id": "inner-loop-minimum-cardinality",
                "territory_ids": [],
                "effective_window": {
                    "kind": "interval",
                    "start": {
                        "kind": "known",
                        "value": "2025-01-01",
                        "precision": "date",
                        "certainty": "exact",
                        "inclusive": True,
                    },
                },
                "precedence": 30,
            },
        ]
    )


def load_fixture(project, sources, entities, reconciliations, packs, occurrences, interpretations, hosting, path: Path):
    fixture_project = replace(project, provenance_registry=path)
    return load_provenance_registry(
        fixture_project,
        sources,
        entities,
        reconciliations,
        packs,
        occurrences,
        interpretations,
        hosting,
    )


def assert_counts(registry, expected: dict) -> None:
    links = [link for assertion in registry.assertions for link in assertion.evidence_links]
    locators = [locator for link in links for locator in link.locators]
    claim_keys = {assertion.claim_key for assertion in registry.assertions}
    actual = {
        "assertions": len(registry.assertions),
        "claim_supersessions": len(registry.claim_supersessions),
        "claim_keys": len(claim_keys),
        "evidence_links": len(links),
        "locators": len(locators),
    }
    if actual != expected:
        raise AssertionError(f"Provenance fixture counts changed: {actual!r}")


def assert_authority_vectors(registry, vectors: list[dict]) -> None:
    for expected in vectors:
        actual = registry.evaluate_claim_authority("comparison-profile", expected["claim_key"])
        normalized = {
            "claim_key": actual.claim_key,
            "outcome": actual.outcome,
            "best_rank": actual.best_rank,
            "winning_assertion_ids": list(actual.winning_assertion_ids),
        }
        if normalized != expected:
            raise AssertionError(f"Authority vector changed: {normalized!r}")
        for item in actual.decisions:
            if item.decision.source_id not in registry.sources.sources:
                raise AssertionError("Authority decision lost its source identity.")
            if item.decision.rank < 0:
                raise AssertionError("Authority decision produced a negative rank.")


def assert_services(registry) -> None:
    if tuple(item.id for item in registry.assertions_for_claim("authority-winner")) != (
        "winner-primary",
        "winner-adaptation",
    ):
        raise AssertionError("Claim assertion lookup changed.")
    if registry.provenance_target("entity", "alpha-concept") is not registry.entities.entities["alpha-concept"]:
        raise AssertionError("Cross-registry provenance target lookup changed.")
    supersession = registry.provenance_target("claim-supersession", "confirmed-name-supersedes-reported-name")
    if supersession.source_claim_key != "confirmed-alpha-name":
        raise AssertionError("Claim-supersession target lookup changed.")
    cardinality = registry.provenance_target("recurrence-cardinality", "inner-minimum-count")
    if cardinality.minimum_count != 1:
        raise AssertionError("Recurrence-cardinality provenance target lookup changed.")
    participation = registry.provenance_target("occurrence-participation", "protagonist-self-intervention-agent")
    if participation.role != "agent":
        raise AssertionError("Occurrence-participation provenance target lookup changed.")
    track_entry = registry.provenance_target("occurrence-track-entry", "protagonist-entry-14")
    if track_entry.participation_id != participation.id or track_entry.ordinal != 14:
        raise AssertionError("Occurrence-track-entry provenance target lookup changed.")
    chronology_binding = registry.provenance_target(
        "occurrence-participation-chronology-binding", "agent-personal-binding"
    )
    if chronology_binding.target_id != participation.id or chronology_binding.chronology_context_id != "agent-context":
        raise AssertionError("Participation chronology-binding provenance target lookup changed.")
    state = registry.provenance_target("state-transition", "protagonist-completes-inner-step-knowledge")
    if state.state_profile != "epistemic-access" or state.resulting_completeness != "complete":
        raise AssertionError("Epistemic state-transition provenance target lookup changed.")
    exact = registry.applicability_decision("provenance-claim", "reported-alpha-name")
    if exact.winning_scope_ids != ("reported-alpha-name-scope",) or exact.highest_precedence != 20:
        raise AssertionError("Provenance-claim applicability resolution changed.")
    delegated = registry.applicability_decision("work", "adaptation-work")
    if delegated.winning_scope_ids != ("adaptation-work-scope",):
        raise AssertionError("Delegated source applicability resolution changed.")
    cardinality_scope = registry.applicability_decision(
        "provenance-claim", "inner-loop-minimum-cardinality", effective_at="2025-02-01"
    )
    if (
        cardinality_scope.winning_scope_ids != ("inner-loop-cardinality-scope",)
        or cardinality_scope.highest_precedence != 30
    ):
        raise AssertionError("Recurrence-cardinality claim applicability resolution changed.")


def assert_invalid_queries(registry) -> int:
    actions = (
        lambda: registry.provenance_target("unknown", "alpha-concept"),
        lambda: registry.provenance_target("entity", "unknown"),
        lambda: registry.evaluate_claim_authority("comparison-profile", "unknown-claim"),
        lambda: registry.evaluate_claim_authority("comparison-profile", "context-only-claim"),
        lambda: registry.applicability_decision("provenance-claim", "unknown-claim"),
    )
    for index, action in enumerate(actions):
        expect_rejected(action, f"Invalid provenance service query was accepted: {index}")
    return len(actions)


def add_scale_assertions(document: dict, count: int) -> None:
    for index in range(count):
        document["assertions"].append(
            {
                "id": f"scale-assertion-{index:03d}",
                "claim_key": f"scale-claim-{index:03d}",
                "subject_type": "entity",
                "subject_id": "alpha-concept",
                "claim_namespace": "canonical-content",
                "field_path": "label",
                "asserted_value": f"Scale Value {index:03d}",
                "assertion_status": "verified",
                "evidence_links": [
                    {
                        "source_id": "primary-source",
                        "evidence_role": "supports",
                        "locators": [
                            {
                                "id": f"scale-locator-{index:03d}",
                                "medium_id": "novel",
                                "evidence_mode": "canonical-text",
                                "locator_type": "point",
                                "position": {"work": "primary-work", "volume": 1, "chapter": 1},
                            }
                        ],
                    }
                ],
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run provenance-registry conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)

    canonical_taxonomy = load_taxonomy_config(project)
    canonical_resources = load_resource_config(project)
    canonical_sources = load_source_registry(project, canonical_resources, packs)
    canonical_entities = load_entity_registry(project, canonical_taxonomy, canonical_sources, packs)
    chronology = load_chronology_registry(
        project, packs, work_ids=set(canonical_sources.works), continuity_ids=set(canonical_sources.continuities)
    )
    occurrences = load_occurrence_registry(project, packs, chronology)
    canonical_hosting = load_hosted_identity_registry(project, packs, occurrences, (canonical_entities,))
    canonical_providers = (
        canonical_taxonomy.reconciliation_provider(),
        canonical_resources.reconciliation_provider(),
        canonical_sources.reconciliation_provider(),
        canonical_entities.reconciliation_provider(),
        canonical_hosting.reconciliation_provider(),
    )
    reconciliations = load_reconciliation_registry(project, canonical_providers, packs)
    canonical = load_provenance_registry(
        project, canonical_sources, canonical_entities, reconciliations, packs, occurrences, hosting=canonical_hosting
    )
    chronology_context_target = canonical.provenance_target("chronology-context", "lotm-novel-main-story-chronology")
    if chronology_context_target.id != "lotm-novel-main-story-chronology":
        raise AssertionError("Chronology-context provenance dispatch returned the wrong target.")

    fixture_root = root / "Framework" / "Data" / "Provenance"
    base_document = json.loads((fixture_root / "base" / "registry.json").read_text(encoding="utf-8"))
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported provenance conformance expectation schema.")

    with tempfile.TemporaryDirectory(prefix="knowledge-provenance-") as temp_dir:
        temp_root = Path(temp_dir)
        source_root = temp_root / "sources"
        shutil.copytree(root / "Framework" / "Data" / "Sources" / "base", source_root)
        source_document = json.loads((source_root / "registry.json").read_text(encoding="utf-8"))
        extend_source_document(source_document)
        write_json(source_root / "registry.json", source_document)
        source_project = source_fixture_project(project, source_root)
        resources = load_resource_config(source_project)
        sources = load_source_registry(source_project, resources, packs)

        taxonomy_root = root / "Framework" / "Data" / "Taxonomy" / "base"
        taxonomy = load_taxonomy_config(taxonomy_fixture_project(project, taxonomy_root))
        entity_project = replace(
            project, entities_registry=root / "Framework" / "Data" / "Entities" / "base" / "registry.json"
        )
        entities = load_entity_registry(entity_project, taxonomy, sources, packs)

        chronology_fixture_path = root / "Framework" / "Data" / "Chronology" / "valid-registry.yaml"
        chronology_fixture_data = load_yaml_file(
            chronology_fixture_path, "chronology fixture", expected_schema_version=2
        )
        chronology_fixture_data["contexts"] = [
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
        chronology_fixture_data["context_relations"] = []
        chronology_fixture = parse_chronology_registry(
            chronology_fixture_data,
            chronology_fixture_path,
            packs,
            work_ids={"fixture-work"},
            continuity_ids=set(),
        )
        occurrence_fixture_path = root / "Framework" / "Data" / "Occurrence" / "valid-registry.yaml"
        fixture_occurrences = parse_occurrence_registry(
            load_yaml_file(occurrence_fixture_path, "occurrence fixture", expected_schema_version=10),
            occurrence_fixture_path,
            packs,
            chronology_fixture,
            subject_targets={"character": {"protagonist", "observer"}},
            payload_targets={
                "state-record": {"protagonist-health"},
                "credential-record": {"protagonist-qualification"},
            },
        )
        hosting_document = json.loads(
            (root / "Framework" / "Data" / "Hosting" / "base" / "registry.json").read_text(encoding="utf-8")
        )
        hosting_document["occupancies"] = []
        hosting_document["transitions"] = []
        hosting_path = temp_root / "hosting.json"
        write_json(hosting_path, hosting_document)
        hosting_project = replace(project, hosting_registry=hosting_path)
        fixture_hosting = load_hosted_identity_registry(hosting_project, packs, fixture_occurrences, (entities,))

        interpretation_document = load_yaml_file(
            project.interpretations_registry,
            "structural interpretation registry",
            expected_schema_version=1,
        )
        interpretation_document["interpretations"] = {
            "candidate-structure": {
                "lifecycle": "active",
                "label": "Candidate Structure",
                "description": "A provenance composition probe.",
            }
        }
        interpretation_document["members"] = [
            {
                "id": "candidate-entity",
                "interpretation_id": "candidate-structure",
                "target_type": "entity",
                "target_id": "alpha-concept",
            },
            {
                "id": "candidate-claim",
                "interpretation_id": "candidate-structure",
                "target_type": "provenance-claim",
                "target_id": "forward-structure-label",
            },
        ]
        interpretation_path = temp_root / "interpretations.json"
        write_json(interpretation_path, interpretation_document)
        interpretation_project = replace(project, interpretations_registry=interpretation_path)
        interpretations = load_interpretation_registry(
            interpretation_project,
            packs,
            (sources, entities, reconciliations, chronology_fixture, fixture_occurrences, fixture_hosting),
        )

        interpretation_assertion = copy.deepcopy(base_document["assertions"][0])
        interpretation_assertion.update(
            {
                "id": "interpretation-support",
                "claim_key": "forward-structure-label",
                "subject_type": "structural-interpretation",
                "subject_id": "candidate-structure",
                "claim_namespace": "structural-interpretation",
                "field_path": "label",
                "asserted_value": "Candidate Structure",
            }
        )
        interpretation_assertion["evidence_links"][0]["locators"][0]["id"] = "interpretation-support-locator"
        base_document["assertions"].append(interpretation_assertion)

        binding_assertion = copy.deepcopy(base_document["assertions"][0])
        binding_assertion.update(
            {
                "id": "carrier-binding-kind-support",
                "claim_key": "control-unit-body-b-binding-kind",
                "subject_type": "host-carrier-binding",
                "subject_id": "control-unit-body-b",
                "claim_namespace": "canonical-content",
                "field_path": "binding_kind",
                "asserted_value": "installed-in",
            }
        )
        binding_assertion["evidence_links"][0]["locators"][0]["id"] = "carrier-binding-kind-support-locator"
        base_document["assertions"].append(binding_assertion)

        valid_path = temp_root / "valid.json"
        write_json(valid_path, base_document)
        registry = load_fixture(
            project,
            sources,
            entities,
            reconciliations,
            packs,
            fixture_occurrences,
            interpretations,
            fixture_hosting,
            valid_path,
        )
        if (
            registry.provenance_target("structural-interpretation", "candidate-structure").label
            != "Candidate Structure"
        ):
            raise AssertionError("Structural interpretation provenance dispatch returned the wrong target.")
        binding_target = registry.provenance_target("host-carrier-binding", "control-unit-body-b")
        if binding_target.binding_kind != "installed-in":
            raise AssertionError("Host-carrier-binding provenance dispatch returned the wrong target.")
        assert_counts(registry, expectations["valid_counts"])
        assert_authority_vectors(registry, expectations["authority_vectors"])
        assert_services(registry)
        invalid_query_count = assert_invalid_queries(registry)
        if invalid_query_count != expectations["invalid_query_cases"]:
            raise AssertionError("Provenance invalid-query expectation count changed.")

        for case in expectations["invalid_cases"]:
            document = copy.deepcopy(base_document)
            for operation in case["operations"]:
                apply_operation(document, operation)
            case_path = temp_root / f"{case['id']}.json"
            write_json(case_path, document)
            expect_rejected(
                lambda case_path=case_path: load_fixture(
                    project,
                    sources,
                    entities,
                    reconciliations,
                    packs,
                    fixture_occurrences,
                    interpretations,
                    fixture_hosting,
                    case_path,
                ),
                f"Malformed provenance configuration was accepted: {case['id']}",
            )

        scale_document = copy.deepcopy(base_document)
        scale_count = expectations["scale_additional_assertions"]
        add_scale_assertions(scale_document, scale_count)
        scale_path = temp_root / "scale.json"
        write_json(scale_path, scale_document)
        scale_registry = load_fixture(
            project,
            sources,
            entities,
            reconciliations,
            packs,
            fixture_occurrences,
            interpretations,
            fixture_hosting,
            scale_path,
        )
        if len(scale_registry.assertions) != len(registry.assertions) + scale_count:
            raise AssertionError("Provenance scale composition count changed.")

    summary = {
        "schema_version": 1,
        "canonical_assertions": len(canonical.assertions),
        "canonical_claim_supersessions": len(canonical.claim_supersessions),
        "fixture_assertions": len(registry.assertions),
        "fixture_claim_supersessions": len(registry.claim_supersessions),
        "authority_vector_cases": len(expectations["authority_vectors"]),
        "invalid_configuration_cases": len(expectations["invalid_cases"]),
        "invalid_query_cases": invalid_query_count,
        "scale_additional_assertions": scale_count,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Provenance conformance passed: "
            f"{summary['fixture_assertions']} fixture assertions, "
            f"{summary['authority_vector_cases']} authority vectors, "
            f"{summary['invalid_configuration_cases']} malformed configurations, and "
            f"{summary['scale_additional_assertions']} additional scale assertions."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
