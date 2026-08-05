from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import json
from pathlib import Path
import sys


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.chronology_config import load_chronology_registry  # noqa: E402
from knowledge_framework.entity_config import load_entity_registry  # noqa: E402
from knowledge_framework.interpretation_config import load_interpretation_registry  # noqa: E402
from knowledge_framework.lookup_key_config import load_lookup_key_config  # noqa: E402
from knowledge_framework.occurrence_config import load_occurrence_registry  # noqa: E402
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402
from knowledge_framework.provenance_config import load_provenance_registry  # noqa: E402
from knowledge_framework.reconciliation_config import load_reconciliation_registry  # noqa: E402
from knowledge_framework.resource_config import load_resource_config  # noqa: E402
from knowledge_framework.schema_pack_config import load_schema_pack_registry  # noqa: E402
from knowledge_framework.source_config import load_source_registry  # noqa: E402
from knowledge_framework.taxonomy_config import load_taxonomy_config  # noqa: E402


SOURCE_COUNT_FIELDS = (
    "media_modalities",
    "cultural_forms",
    "release_forms",
    "container_formats",
    "mediums",
    "work_groups",
    "continuities",
    "authority_profiles",
    "work_relationship_types",
    "works",
    "segments",
    "content_groups",
    "ordering_schemes",
    "numbering_schemes",
    "work_relationships",
    "adaptation_mappings",
    "territories",
    "applicability_scopes",
    "manifestations",
    "release_components",
    "release_packages",
    "release_runs",
    "release_events",
    "catalog_placements",
    "platform_offerings",
    "sources",
)
CHRONOLOGY_COUNT_FIELDS = (
    "coordinate_systems",
    "eras",
    "contexts",
    "context_relations",
    "positions",
    "spans",
    "relations",
    "mappings",
)
ENTITY_COUNT_FIELDS = (
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
OCCURRENCE_COUNT_FIELDS = (
    "branches",
    "branch_state_transitions",
    "templates",
    "recurrence_patterns",
    "recurrences",
    "recurrence_cardinalities",
    "iterations",
    "phases",
    "schedules",
    "occurrences",
    "occurrence_participations",
    "tracks",
    "track_entries",
    "transitions",
    "causal_relations",
    "outcomes",
    "rules",
    "state_scales",
    "state_transitions",
    "carryovers",
)


@dataclass(frozen=True)
class Composition:
    project: object
    lookup: object
    packs: object
    taxonomy: object
    resources: object
    sources: object
    chronology: object
    entities: object
    occurrences: object
    interpretations: object
    providers: tuple[dict[str, object], ...]
    reconciliation: object
    provenance: object


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except (KeyError, TypeError, ValueError):
        return
    raise AssertionError(message)


def load_composition(root: Path) -> Composition:
    project = load_project_config(root)
    lookup = load_lookup_key_config(project)
    packs = load_schema_pack_registry(project)
    taxonomy = load_taxonomy_config(project)
    resources = load_resource_config(project)
    sources = load_source_registry(project, resources, packs)
    chronology = load_chronology_registry(
        project,
        packs,
        work_ids=set(sources.works),
        continuity_ids=set(sources.continuities),
    )
    entities = load_entity_registry(project, taxonomy, sources, packs)
    occurrences = load_occurrence_registry(project, packs, chronology)
    occurrences.validate_branch_continuity_targets(set(sources.continuities))
    chronology.validate_context_relation_targets(
        {
            "occurrence": set(occurrences.occurrences),
            "occurrence-branch": set(occurrences.branches),
            "applicability-scope": set(sources.applicability_scopes),
        }
    )
    providers = (
        taxonomy.reconciliation_provider(),
        resources.reconciliation_provider(),
        sources.reconciliation_provider(),
        entities.reconciliation_provider(),
    )
    reconciliation = load_reconciliation_registry(project, providers, packs)
    interpretations = load_interpretation_registry(
        project,
        packs,
        (sources, entities, reconciliation, chronology, occurrences),
    )
    provenance = load_provenance_registry(
        project,
        sources,
        entities,
        reconciliation,
        packs,
        occurrences,
        interpretations,
    )
    return Composition(
        project,
        lookup,
        packs,
        taxonomy,
        resources,
        sources,
        chronology,
        entities,
        occurrences,
        interpretations,
        providers,
        reconciliation,
        provenance,
    )


def count_fields(registry, fields: tuple[str, ...]) -> dict[str, int]:
    return {field: len(getattr(registry, field)) for field in fields}


def summarize(composition: Composition) -> dict:
    project = composition.project
    packs = composition.packs
    reconciliation = composition.reconciliation
    provenance_types = (
        set(composition.sources.provenance_targets())
        | set(composition.entities.provenance_targets())
        | set(reconciliation.provenance_targets())
        | set(composition.chronology.provenance_targets())
        | set(composition.occurrences.provenance_targets())
        | set(composition.interpretations.provenance_targets())
        | {"claim-supersession"}
    )
    return {
        "project": {
            "project_id": project.project_id,
            "framework": project.framework,
            "domain": project.domain,
            "content_root_ids": [item.id for item in project.content_roots],
            "resource_root_ids": [item.id for item in project.resource_roots],
        },
        "schemas": {
            "project": project.schema_version,
            "lookup": composition.lookup.schema_version,
            "packs": packs.schema_version,
            "taxonomy": composition.taxonomy.schema_version,
            "resources": composition.resources.schema_version,
            "sources": composition.sources.schema_version,
            "chronology": composition.chronology.schema_version,
            "entities": composition.entities.schema_version,
            "occurrences": composition.occurrences.schema_version,
            "interpretations": composition.interpretations.schema_version,
            "reconciliation": reconciliation.schema_version,
            "provenance": composition.provenance.schema_version,
        },
        "packs": {
            "selection_order": list(packs.selection_order),
            "versions": {pack_id: packs.packs[pack_id].pack_version for pack_id in packs.selection_order},
            "declared_capabilities": len(packs.declared_capabilities),
            "available_capabilities": len(packs.available_capabilities),
            "enabled_capabilities": len(packs.enabled_capabilities),
            "disabled_capability_ids": sorted(set(packs.declared_capabilities) - set(packs.enabled_capabilities)),
            "controlled_value_namespaces": len(packs.controlled_values),
            "controlled_values": sum(len(values) for values in packs.controlled_values.values()),
            "semantic_declarations": {
                "transition_profiles": len(packs.transition_profiles),
                "outcome_incompatibilities": len(packs.outcome_incompatibilities),
                "effect_target_compatibilities": len(packs.effect_target_compatibilities),
                "rule_effect_compatibilities": len(packs.rule_effect_compatibilities),
                "effect_policies": len(packs.effect_policies),
                "effect_incompatibilities": len(packs.effect_incompatibilities),
                "state_change_profiles": len(packs.state_change_profiles),
                "state_profiles": len(packs.state_profiles),
                "state_kind_profiles": len(packs.state_kind_profiles),
            },
        },
        "counts": {
            "taxonomy": {
                "categories": len(composition.taxonomy.categories),
                "content_types": len(composition.taxonomy.content_types),
            },
            "resources": {
                "kinds": len(composition.resources.kinds),
                "types": len(composition.resources.types),
            },
            "sources": count_fields(composition.sources, SOURCE_COUNT_FIELDS),
            "chronology": count_fields(composition.chronology, CHRONOLOGY_COUNT_FIELDS),
            "entities": count_fields(composition.entities, ENTITY_COUNT_FIELDS),
            "occurrences": count_fields(composition.occurrences, OCCURRENCE_COUNT_FIELDS),
            "interpretations": {
                "relation_types": len(composition.interpretations.relation_types),
                "interpretations": len(composition.interpretations.interpretations),
                "members": len(composition.interpretations.members),
                "relations": len(composition.interpretations.relations),
                "comparison_sets": len(composition.interpretations.comparison_sets),
            },
            "reconciliation": {
                "target_types": len(reconciliation.targets),
                "records": len(reconciliation.records),
                "aliases": sum(len(aliases) for aliases in reconciliation.aliases.values()),
            },
            "provenance": {
                "assertions": len(composition.provenance.assertions),
                "claim_supersessions": len(composition.provenance.claim_supersessions),
            },
        },
        "providers": {
            "reconciliation_target_types": sum(len(provider["targets"]) for provider in composition.providers),
            "source_provenance_types": len(composition.sources.provenance_targets()),
            "entity_provenance_types": len(composition.entities.provenance_targets()),
            "reconciliation_provenance_types": len(reconciliation.provenance_targets()),
            "chronology_provenance_types": len(composition.chronology.provenance_targets()),
            "occurrence_provenance_types": len(composition.occurrences.provenance_targets()),
            "interpretation_provenance_types": len(composition.interpretations.provenance_targets()),
            "total_provenance_subject_types": len(provenance_types),
        },
    }


def assert_wiring(composition: Composition) -> None:
    project = composition.project
    path_pairs = (
        (composition.lookup.path, project.lookup_keys_registry),
        (composition.packs.path, project.schema_packs_registry),
        (composition.taxonomy.path, project.taxonomy_registry),
        (composition.resources.path, project.resources_registry),
        (composition.sources.path, project.sources_registry),
        (composition.chronology.path, project.chronology_registry),
        (composition.entities.path, project.entities_registry),
        (composition.occurrences.path, project.occurrences_registry),
        (composition.interpretations.path, project.interpretations_registry),
        (composition.reconciliation.path, project.reconciliation_registry),
        (composition.provenance.path, project.provenance_registry),
    )
    if any(actual.resolve() != expected.resolve() for actual, expected in path_pairs):
        raise AssertionError("A composed registry did not retain its manifest-owned path.")
    if composition.occurrences.chronology is not composition.chronology:
        raise AssertionError("Occurrence composition did not retain the loaded chronology instance.")
    if composition.provenance.sources is not composition.sources:
        raise AssertionError("Provenance composition did not retain the loaded source instance.")
    if composition.provenance.entities is not composition.entities:
        raise AssertionError("Provenance composition did not retain the loaded entity instance.")
    if composition.provenance.reconciliations is not composition.reconciliation:
        raise AssertionError("Provenance composition did not retain the loaded reconciliation instance.")
    if composition.provenance.chronology is not composition.chronology:
        raise AssertionError("Provenance composition did not retain the loaded chronology instance.")
    if composition.provenance.occurrences is not composition.occurrences:
        raise AssertionError("Provenance composition did not retain the loaded occurrence instance.")
    if composition.provenance.interpretations is not composition.interpretations:
        raise AssertionError("Provenance composition did not retain the loaded interpretation instance.")


def assert_provider_closure(composition: Composition) -> None:
    reconciliation_types = {target_type for provider in composition.providers for target_type in provider["targets"]}
    allowed_reconciliation = set(composition.packs.allowed_values("reconciliation.target-type"))
    if (
        reconciliation_types != allowed_reconciliation
        or set(composition.reconciliation.targets) != reconciliation_types
    ):
        raise AssertionError("Reconciliation provider closure changed.")
    provenance_types = (
        set(composition.sources.provenance_targets())
        | set(composition.entities.provenance_targets())
        | set(composition.reconciliation.provenance_targets())
        | set(composition.chronology.provenance_targets())
        | set(composition.occurrences.provenance_targets())
        | set(composition.interpretations.provenance_targets())
        | {"claim-supersession"}
    )
    if provenance_types != set(composition.packs.allowed_values("provenance.subject-type")):
        raise AssertionError("Provenance provider closure changed.")


def without_capability(packs, capability: str):
    return replace(packs, enabled_capabilities=tuple(item for item in packs.enabled_capabilities if item != capability))


def with_provenance_types(packs, values: tuple[str, ...]):
    controlled_values = dict(packs.controlled_values)
    controlled_values["provenance.subject-type"] = values
    return replace(packs, controlled_values=controlled_values)


def assert_invalid_compositions(composition: Composition) -> int:
    project = composition.project
    providers = composition.providers
    packs = composition.packs
    provenance_types = packs.allowed_values("provenance.subject-type")
    actions = (
        lambda: load_reconciliation_registry(project, providers[:-1], packs),
        lambda: load_reconciliation_registry(project, providers + (providers[0],), packs),
        lambda: load_provenance_registry(
            project,
            composition.sources,
            composition.entities,
            composition.reconciliation,
            with_provenance_types(packs, provenance_types + ("unprovided-subject",)),
            composition.occurrences,
            composition.interpretations,
        ),
        lambda: load_provenance_registry(
            project,
            composition.sources,
            composition.entities,
            composition.reconciliation,
            with_provenance_types(packs, tuple(item for item in provenance_types if item != "entity")),
            composition.occurrences,
            composition.interpretations,
        ),
        lambda: load_entity_registry(
            project,
            composition.taxonomy,
            composition.sources,
            without_capability(packs, "entity-incarnations"),
        ),
        lambda: load_occurrence_registry(
            project,
            without_capability(packs, "occurrence-recurrence-modeling"),
            composition.chronology,
        ),
        lambda: load_occurrence_registry(
            project,
            without_capability(packs, "occurrence-participation-identity"),
            composition.chronology,
        ),
        lambda: load_occurrence_registry(
            project,
            without_capability(packs, "timeline-branch-lifecycle"),
            composition.chronology,
        ),
        lambda: load_occurrence_registry(
            project,
            without_capability(packs, "capability-progression"),
            composition.chronology,
        ),
        lambda: load_chronology_registry(
            project,
            without_capability(packs, "chronology-contexts"),
            work_ids=set(composition.sources.works),
            continuity_ids=set(composition.sources.continuities),
        ),
        lambda: load_reconciliation_registry(
            project,
            providers,
            without_capability(packs, "stable-identity-reconciliation"),
        ),
        lambda: load_interpretation_registry(
            project,
            without_capability(packs, "structural-interpretation-modeling"),
            (
                composition.sources,
                composition.entities,
                composition.reconciliation,
                composition.chronology,
                composition.occurrences,
            ),
        ),
    )
    for index, action in enumerate(actions):
        expect_rejected(action, f"Invalid project composition was accepted: {index}")
    return len(actions)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full project-composition conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    baseline_path = root / "Project_Config" / "composition-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baseline.get("schema_version") != 1:
        raise AssertionError("Unsupported project-composition baseline schema.")

    expected_summary = {key: baseline[key] for key in ("project", "schemas", "packs", "counts", "providers")}
    pass_count = baseline["composition_passes"]
    summaries = []
    for _ in range(pass_count):
        composition = load_composition(root)
        assert_wiring(composition)
        assert_provider_closure(composition)
        summary = summarize(composition)
        if summary != expected_summary:
            raise AssertionError("Canonical project composition differs from its reviewed baseline.")
        summaries.append(summary)
    if any(summary != summaries[0] for summary in summaries[1:]):
        raise AssertionError("Repeated project composition produced process-state drift.")

    invalid_count = assert_invalid_compositions(composition)
    if invalid_count != baseline["invalid_composition_cases"]:
        raise AssertionError("Project-composition invalid-case count changed.")

    output = {
        "schema_version": 1,
        "project_id": composition.project.project_id,
        "composition_passes": pass_count,
        "selected_packs": len(composition.packs.packs),
        "enabled_capabilities": len(composition.packs.enabled_capabilities),
        "disabled_capabilities": len(baseline["packs"]["disabled_capability_ids"]),
        "reconciliation_target_types": len(composition.reconciliation.targets),
        "provenance_subject_types": baseline["providers"]["total_provenance_subject_types"],
        "invalid_composition_cases": invalid_count,
    }
    if args.json:
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Project composition conformance passed: "
            f"{pass_count} complete loads, {output['selected_packs']} packs, "
            f"{output['reconciliation_target_types']} reconciliation target types, and "
            f"{invalid_count} rejected invalid compositions."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
