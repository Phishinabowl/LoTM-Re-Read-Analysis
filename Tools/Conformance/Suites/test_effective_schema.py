from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.effective_schema import (  # noqa: E402
    compose_effective_project_schema,
    effective_schema_failure,
    effective_schema_json,
)
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402
from knowledge_framework.resource_config import load_resource_config  # noqa: E402
from knowledge_framework.schema_pack_config import (  # noqa: E402
    CapabilityConfig,
    load_schema_pack_registry,
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
        "capabilities": len(capabilities),
        "available_capabilities": sum(row["available"] for row in capabilities),
        "enabled_capabilities": sum(row["enabled"] for row in capabilities),
        "planned_capabilities": sum(row["planned"] for row in capabilities),
        "deprecated_capabilities": sum(row["deprecated"] for row in capabilities),
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
    taxonomy = load_taxonomy_config(project)
    resources = load_resource_config(project)
    schema = compose_effective_project_schema(project, packs, taxonomy, resources)
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
    if str(root.resolve()) in effective_schema_json(schema):
        raise AssertionError("Effective schema leaked an absolute project path.")
    if effective_schema_json(schema) != effective_schema_json(
        compose_effective_project_schema(project, packs, taxonomy, resources)
    ):
        raise AssertionError("Repeated effective-schema composition was not byte deterministic.")

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
        "deterministic_passes": 2,
        "synthetic_states": 4,
        "failure_cases": 1,
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
