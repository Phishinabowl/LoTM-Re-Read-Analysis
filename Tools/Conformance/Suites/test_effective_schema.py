from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import sys
import tempfile


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import knowledge_framework  # noqa: E402
from knowledge_framework.effective_schema import (  # noqa: E402
    compose_effective_schema_selection,
    compose_effective_project_schema,
    compose_effective_consumer_schema_projection,
    effective_schema_failure,
    effective_schema_json,
    load_effective_project_schema,
)
from knowledge_framework.framework_catalog import load_framework_catalog  # noqa: E402
from knowledge_framework.lookup_key_config import load_lookup_key_config  # noqa: E402
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402
from knowledge_framework.resource_config import load_resource_config  # noqa: E402
from knowledge_framework.schema_pack_config import (  # noqa: E402
    CapabilityConfig,
    load_schema_pack_registry,
    load_schema_pack_registry_from_catalog,
)
from knowledge_framework.taxonomy_config import load_taxonomy_config  # noqa: E402


TOP_LEVEL_KEYS = [
    "contract",
    "contract_version",
    "project",
    "registry_schema_versions",
    "packs",
    "capabilities",
    "controlled_value_namespaces",
    "content",
    "resources",
    "diagnostics",
]


def summary(document: dict, scale_capabilities: int) -> dict:
    capabilities = document["capabilities"]
    return {
        "schema_version": 1,
        "contract": document["contract"],
        "contract_version": document["contract_version"],
        "project_id": document["project"]["project_id"],
        "packs": len(document["packs"]),
        "active_packs": sum(row["lifecycle"] == "active" for row in document["packs"]),
        "pack_presentations": sum(row["presentation"] is not None for row in document["packs"]),
        "capabilities": len(capabilities),
        "available_capabilities": sum(row["available"] for row in capabilities),
        "enabled_capabilities": sum(row["enabled"] for row in capabilities),
        "planned_capabilities": sum(row["planned"] for row in capabilities),
        "deprecated_capabilities": sum(row["deprecated"] for row in capabilities),
        "capability_presentations": sum(row["presentation"] is not None for row in capabilities),
        "controlled_value_namespaces": len(document["controlled_value_namespaces"]),
        "content_roots": len(document["content"]["roots"]),
        "content_types": len(document["content"]["content_types"]),
        "categories": len(document["content"]["categories"]),
        "resource_roots": len(document["resources"]["roots"]),
        "resource_kinds": len(document["resources"]["kinds"]),
        "resource_types": len(document["resources"]["types"]),
        "diagnostic_codes": [row["code"] for row in document["diagnostics"]],
        "scale_capabilities": scale_capabilities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EffectiveProjectSchema conformance checks.")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=Path(__file__))

    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    catalog = load_framework_catalog(root)
    catalog_packs = load_schema_pack_registry_from_catalog(project, catalog)
    if packs != catalog_packs:
        raise AssertionError("Catalog-backed schema-pack composition differs from the direct shadow path.")
    taxonomy = load_taxonomy_config(project)
    resources = load_resource_config(project)
    schema = compose_effective_project_schema(project, packs, taxonomy, resources)
    catalog_schema = compose_effective_project_schema(project, catalog_packs, taxonomy, resources)
    if effective_schema_json(schema) != effective_schema_json(catalog_schema):
        raise AssertionError("Catalog-backed effective schema differs from the direct shadow composition.")
    if effective_schema_json(load_effective_project_schema(root)) != effective_schema_json(catalog_schema):
        raise AssertionError("Effective-schema loading did not use the catalog-backed composition.")
    try:
        load_schema_pack_registry_from_catalog(replace(project, framework="wrong-framework"), catalog)
    except ValueError as error:
        if "does not match installed framework" not in str(error):
            raise
    else:
        raise AssertionError("Catalog-backed composition accepted a mismatched framework ID.")
    try:
        load_schema_pack_registry_from_catalog(
            replace(project, lookup_keys_registry=project.manifest_path),
            catalog,
        )
    except ValueError as error:
        if "does not match the framework installation" not in str(error):
            raise
    else:
        raise AssertionError("Catalog-backed composition accepted a mismatched lookup-key registry.")
    document = schema.to_dict()

    if list(document) != TOP_LEVEL_KEYS:
        raise AssertionError("Effective schema top-level property order changed.")
    if document["registry_schema_versions"] != sorted(
        document["registry_schema_versions"], key=lambda row: row["registry_id"]
    ):
        raise AssertionError("Effective schema registry versions are not ordered by registry ID.")
    for key in ("capabilities", "controlled_value_namespaces"):
        ids = [row["id"] for row in document[key]]
        if ids != sorted(ids):
            raise AssertionError(f"Effective schema {key} are not ordered by stable ID.")
    if any(row["lifecycle"] != "active" for row in document["packs"]):
        raise AssertionError("Effective schema did not preserve selected pack lifecycle.")
    if any(row["classification"] is None or row["presentation"] is None for row in document["packs"]):
        raise AssertionError("Effective schema lost selected-pack classification or presentation.")
    if any(row["presentation"] is None for row in document["capabilities"]):
        raise AssertionError("Effective schema lost capability presentation.")
    if any(row["presentation"]["visual"] is not None for row in document["packs"]):
        raise AssertionError("Effective schema invented optional pack visual metadata.")
    if str(root.resolve()) in effective_schema_json(schema):
        raise AssertionError("Effective schema leaked an absolute project path.")
    if effective_schema_json(schema) != effective_schema_json(
        compose_effective_project_schema(project, packs, taxonomy, resources)
    ):
        raise AssertionError("Repeated effective-schema composition was not byte deterministic.")
    original_directory = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="effective-schema-cwd-") as temp_directory:
        try:
            os.chdir(temp_directory)
            alternate_directory_json = effective_schema_json(
                compose_effective_project_schema(project, packs, taxonomy, resources)
            )
        finally:
            os.chdir(original_directory)
    if alternate_directory_json != effective_schema_json(schema):
        raise AssertionError("Effective-schema composition changed with the process working directory.")

    lookup_keys = load_lookup_key_config(project)
    selection = compose_effective_schema_selection(
        schema,
        lookup_keys,
        pack_id="Narrative-Media",
        capability_id="Narrative-Time-Loops",
    )
    if (
        selection["source_contract_version"] != document["contract_version"]
        or [row["id"] for row in selection["packs"]] != ["narrative-media"]
        or [row["id"] for row in selection["capabilities"]] != ["narrative-time-loops"]
    ):
        raise AssertionError("Effective-schema normalized singular selection changed.")
    try:
        compose_effective_schema_selection(schema, lookup_keys, pack_id="missing-pack")
    except ValueError:
        pass
    else:
        raise AssertionError("Effective-schema selection accepted an unknown pack ID.")
    ambiguous_schema = replace(
        schema,
        packs=(*schema.packs, {**schema.packs[0], "id": schema.packs[0]["id"].upper()}),
    )
    try:
        compose_effective_schema_selection(ambiguous_schema, lookup_keys, pack_id=schema.packs[0]["id"].title())
    except ValueError:
        pass
    else:
        raise AssertionError("Effective-schema selection accepted an ambiguous normalized pack ID.")

    consumer_ids = ("qa", "visualization")
    consumer_projections = {
        consumer_id: compose_effective_consumer_schema_projection(schema, consumer_id) for consumer_id in consumer_ids
    }
    retired_consumer_apis = (
        "assert_consumer_schema_shadow",
        "compare_consumer_schema_projections",
        "compose_legacy_consumer_schema_projection",
    )
    if any(hasattr(knowledge_framework, name) for name in retired_consumer_apis):
        raise AssertionError("Retired effective-schema shadow APIs remain publicly exported.")

    qa_projection = consumer_projections["qa"]
    if set(qa_projection["roots"]) != {"glossary", "volumes"}:
        raise AssertionError("Effective QA discovery roots changed.")
    character = qa_projection["categories"].get("character", {})
    if character.get("label") != "Character" or character.get("plural_label") != "Characters":
        raise AssertionError("Effective QA category labels changed.")
    if qa_projection["placements"]["character|glossary-page"]["relative_folder"] != "Characters":
        raise AssertionError("Effective QA category placement changed.")
    volume = qa_projection["records"].get("volume summary", {})
    if (
        volume.get("content_type_id") != "volume-summary"
        or volume.get("export_folder") != "Volumes"
        or volume.get("slug_prefix") != "volume"
        or not re.fullmatch(volume.get("slug_pattern", ""), "volume-01-clown")
    ):
        raise AssertionError("Effective QA fixed-record slug configuration changed.")
    if re.fullmatch(volume["slug_pattern"], "volume-1"):
        raise AssertionError("Effective QA fixed-record slug matching accepted a non-page volume identifier.")

    visualization_projection = consumer_projections["visualization"]
    if set(visualization_projection["roots"]) != {"glossary"}:
        raise AssertionError("Effective Visualization discovery roots changed.")
    if set(visualization_projection["content_types"]) != {"glossary-page"}:
        raise AssertionError("Effective Visualization content types changed.")
    tarot_card = visualization_projection["records"].get("tarot card", {})
    if (
        tarot_card.get("relative_folder") != "Tarot_Cards"
        or tarot_card.get("slug_prefix") != "tarot-card"
        or tarot_card.get("graph_class") != "tarot"
        or not re.fullmatch(tarot_card.get("slug_pattern", ""), "tarot-card-the-star")
    ):
        raise AssertionError("Effective Visualization record discovery changed.")
    required_visualization_capabilities = {
        "graph-projection",
        "reader-disclosure",
        "spoiler-bounding",
        "visibility-policy",
    }
    enabled_visualization_capabilities = {
        capability_id
        for capability_id, state in visualization_projection["capability_state"].items()
        if state["available"] and state["enabled"]
    }
    if not required_visualization_capabilities <= enabled_visualization_capabilities:
        raise AssertionError("Effective Visualization projection capabilities changed.")

    capability_by_id = {row["id"]: row for row in document["capabilities"]}
    planned_id = next(row["id"] for row in document["capabilities"] if row["planned"])
    if capability_by_id[planned_id]["available"] or not capability_by_id[planned_id]["disabled"]:
        raise AssertionError("Planned capability state is inconsistent.")

    disabled_id = next(row["id"] for row in document["capabilities"] if row["enabled"])
    disabled_packs = replace(
        packs,
        enabled_capabilities=tuple(item for item in packs.enabled_capabilities if item != disabled_id),
    )
    disabled_document = compose_effective_project_schema(project, disabled_packs, taxonomy, resources).to_dict()
    disabled_row = next(row for row in disabled_document["capabilities"] if row["id"] == disabled_id)
    if not disabled_row["available"] or disabled_row["enabled"] or not disabled_row["disabled"]:
        raise AssertionError("Available-but-disabled capability state is inconsistent.")

    provider_id = packs.capability_providers[disabled_id][0]
    deprecated_definitions = dict(packs.capability_definitions)
    base_definition = deprecated_definitions[(provider_id, disabled_id)]
    deprecated_definitions[(provider_id, disabled_id)] = replace(base_definition, lifecycle="deprecated")
    deprecated_packs = replace(packs, capability_definitions=deprecated_definitions)
    deprecated_document = compose_effective_project_schema(project, deprecated_packs, taxonomy, resources).to_dict()
    deprecated_row = next(row for row in deprecated_document["capabilities"] if row["id"] == disabled_id)
    if not deprecated_row["deprecated"] or not deprecated_row["enabled"]:
        raise AssertionError("Deprecated enabled capability did not retain activation state.")
    if "deprecated-capability-enabled" not in {row["code"] for row in deprecated_document["diagnostics"]}:
        raise AssertionError("Deprecated enabled capability did not emit its diagnostic.")

    second_provider = next(pack_id for pack_id in packs.selection_order if pack_id != provider_id)
    multiple_providers = dict(packs.capability_providers)
    multiple_providers[disabled_id] = (provider_id, second_provider)
    multiple_definitions = dict(packs.capability_definitions)
    multiple_definitions[(second_provider, disabled_id)] = CapabilityConfig(
        id=disabled_id,
        lifecycle="planned",
        label="Synthetic secondary provider",
        description=None,
    )
    ambiguous_packs = replace(
        packs,
        capability_providers=multiple_providers,
        capability_definitions=multiple_definitions,
    )
    ambiguous_document = compose_effective_project_schema(project, ambiguous_packs, taxonomy, resources).to_dict()
    ambiguous_row = next(row for row in ambiguous_document["capabilities"] if row["id"] == disabled_id)
    if len(ambiguous_row["providers"]) != 2 or ambiguous_row["effective_lifecycle"] != "available":
        raise AssertionError("Multiple-provider lifecycle resolution is inconsistent.")
    if "multiple-capability-providers" not in {row["code"] for row in ambiguous_document["diagnostics"]}:
        raise AssertionError("Multiple capability providers did not emit their diagnostic.")

    scale_count = 400
    scale_ids = tuple(f"scale-capability-{index:03d}" for index in range(scale_count))
    scale_providers = dict(packs.capability_providers)
    scale_definitions = dict(packs.capability_definitions)
    for capability_id in scale_ids:
        scale_providers[capability_id] = (provider_id,)
        scale_definitions[(provider_id, capability_id)] = CapabilityConfig(
            id=capability_id,
            lifecycle="available",
            label=None,
            description=None,
        )
    scale_packs = replace(
        packs,
        declared_capabilities=(*packs.declared_capabilities, *scale_ids),
        available_capabilities=(*packs.available_capabilities, *scale_ids),
        capability_providers=scale_providers,
        capability_definitions=scale_definitions,
    )
    scale_document = compose_effective_project_schema(project, scale_packs, taxonomy, resources).to_dict()
    if len(scale_document["capabilities"]) != len(document["capabilities"]) + scale_count:
        raise AssertionError("Effective schema scale composition lost capabilities.")

    failure = effective_schema_failure(ValueError("Schema pack `child` requires unselected pack `base`."))
    if failure["schema"] is not None or failure["diagnostics"][0]["code"] != "missing-pack-dependency":
        raise AssertionError("Effective schema failure classification changed.")

    expected_path = root / "Framework" / "Data" / "Effective-Schema" / "expected-summary.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = summary(document, scale_count)
    if actual != expected:
        raise AssertionError(f"Effective schema summary changed:\nexpected={expected}\nactual={actual}")

    result = {
        "schema_version": 1,
        "status": "passed",
        "summary": actual,
        "deterministic_passes": 3,
        "synthetic_states": 4,
        "selection_cases": 3,
        "failure_cases": 1,
        "consumer_projection_modes": len(consumer_ids),
        "retired_consumer_apis": len(retired_consumer_apis),
        "qa_discovery_content_types": len(qa_projection["content_types"]),
        "qa_discovery_categories": len(qa_projection["categories"]),
        "qa_discovery_placements": len(qa_projection["placements"]),
        "qa_discovery_records": len(qa_projection["records"]),
        "visualization_discovery_content_types": len(visualization_projection["content_types"]),
        "visualization_discovery_categories": len(visualization_projection["categories"]),
        "visualization_discovery_records": len(visualization_projection["records"]),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(
            "Effective-schema conformance passed: "
            f"{actual['packs']} packs, {actual['capabilities']} capabilities, "
            f"{actual['controlled_value_namespaces']} namespaces, and {scale_count} scale capabilities."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
