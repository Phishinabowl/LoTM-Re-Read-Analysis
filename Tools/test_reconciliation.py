import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile

import yaml

from entity_config import load_entity_registry
from project_config import load_project_config
from reconciliation_config import load_reconciliation_registry
from resource_config import load_resource_config
from schema_pack_config import load_schema_pack_registry
from source_config import load_source_registry
from strict_yaml import load_yaml_file, validate_yaml_source
from taxonomy_config import load_taxonomy_config


FIXTURE_TARGETS = {
    "category": ("current-category", "history-source", "reversed-source"),
    "content-type": ("current-content-type",),
}


def build_context(root: Path):
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    taxonomy = load_taxonomy_config(project)
    resources = load_resource_config(project)
    sources = load_source_registry(project, resources, packs)
    entities = load_entity_registry(project, taxonomy, sources, packs)
    providers = []
    for provider in (
        taxonomy.reconciliation_provider(),
        resources.reconciliation_provider(),
        sources.reconciliation_provider(),
        entities.reconciliation_provider(),
    ):
        providers.append(
            {
                "provider_id": provider["provider_id"],
                "targets": {
                    target_type: dict(records)
                    for target_type, records in provider["targets"].items()
                },
                "aliases": {
                    target_type: dict(records)
                    for target_type, records in provider["aliases"].items()
                },
            }
        )
    taxonomy_provider = providers[0]
    for target_type, target_ids in FIXTURE_TARGETS.items():
        for target_id in target_ids:
            taxonomy_provider["targets"][target_type][target_id] = {"id": target_id}
    taxonomy_provider["aliases"]["category"] = {"old-alias": "current-category"}
    return project, packs, tuple(providers)


def normalized_resolution(resolution) -> dict:
    endpoint = lambda item: f"{item.target_type}:{item.target_id}"
    return {
        "target_type": resolution.requested_type,
        "target_id": resolution.requested_id,
        "outcome": resolution.outcome,
        "canonical": [endpoint(item) for item in resolution.canonical_targets],
        "branches": [
            [
                branch.outcome,
                endpoint(branch.canonical_target) if branch.canonical_target else None,
                list(branch.reconciliation_ids),
            ]
            for branch in resolution.branches
        ],
    }


def load_at(project, packs, providers, path: Path):
    return load_reconciliation_registry(
        replace(project, reconciliation_registry=path), providers, packs
    )


def deep_registry(depth: int) -> dict:
    records = []
    for index in range(depth):
        source_id = f"deep-{index:04d}"
        target_id = f"deep-{index + 1:04d}" if index + 1 < depth else "current-category"
        records.append(
            {
                "id": f"deep-record-{index:04d}",
                "source_type": "category",
                "source_id": source_id,
                "source_state": "tombstone",
                "source_label_mode": "omitted",
                "operation": "redirect",
                "targets": [{"target_type": "category", "target_id": target_id}],
                "reason": "renamed",
                "status": "active",
                "audit": {"mode": "repository-history"},
            }
        )
    return {
        "schema_version": 4,
        "resolution": {
            "max_branches": 65536,
            "max_records": max(depth + 1, 100000),
            "max_targets_per_record": 4096,
            "max_resolution_steps": max(depth + 1, 250000),
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run stable-identity reconciliation conformance tests.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--deep-chain", type=int, default=1500)
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = args.root.resolve()
    fixtures = root / "Framework" / "Data" / "Reconciliation"
    strict_yaml_fixtures = root / "Framework" / "Data" / "Strict-Yaml"
    project, packs, providers = build_context(root)

    mapping_keys = load_yaml_file(
        strict_yaml_fixtures / "valid-mapping-keys.yaml",
        "strict YAML fixture",
        expected_schema_version=1,
    )
    expected_keys = {
        "1", "true", "on", "dotted.key", "hyphen-key", "underscore_key"
    }
    if set(mapping_keys["mapping_keys"]) != expected_keys or not all(
        type(key) is str for key in mapping_keys["mapping_keys"]
    ):
        raise AssertionError("Canonical mapping-key fixture did not preserve string keys.")
    mapping_key_fixture_names = (
        "invalid-boolean-key.yaml",
        "invalid-integer-key.yaml",
        "invalid-empty-key.yaml",
        "invalid-uppercase-key.yaml",
        "invalid-case-collision.yaml",
        "invalid-unicode-key.yaml",
        "invalid-punctuation-key.yaml",
        "invalid-complex-key.yaml",
        "invalid-duplicate-key.yaml",
    )
    for name in mapping_key_fixture_names:
        try:
            load_yaml_file(strict_yaml_fixtures / name, "strict YAML fixture")
        except ValueError:
            pass
        else:
            raise AssertionError(f"Noncanonical mapping-key fixture was accepted: {name}")

    registry = load_at(project, packs, providers, fixtures / "valid-v4.yaml")
    scalar_registry = load_at(project, packs, providers, fixtures / "valid-scalar-parity.yaml")
    if scalar_registry.records[0].source_label != "on":
        raise AssertionError("Legacy YAML Boolean word did not remain a string.")
    expected = json.loads((fixtures / "expectations.json").read_text(encoding="utf-8"))
    actual = [
        normalized_resolution(registry.resolve(case["target_type"], case["target_id"]))
        for case in expected["resolutions"]
    ]
    if actual != expected["resolutions"]:
        raise AssertionError("Reconciliation resolution vectors did not match expectations.")

    for name in (
        "invalid-operation-reason.yaml",
        "invalid-alias-conflict.yaml",
        "invalid-audit.yaml",
        "invalid-reclassify.yaml",
        "invalid-active-cycle.yaml",
        "invalid-unknown-terminal.yaml",
        "invalid-source-state.yaml",
        "invalid-label-mode.yaml",
        "invalid-supersession-cycle.yaml",
        "invalid-duplicate-key.yaml",
        "invalid-schema-string.yaml",
        "invalid-unknown-field.yaml",
        "invalid-timestamp-case.yaml",
        "invalid-timestamp-offset.yaml",
        "invalid-resolution-type.yaml",
        "invalid-resolution-field.yaml",
        "invalid-schema-decimal.yaml",
        "invalid-record-field.yaml",
        "invalid-target-field.yaml",
        "invalid-audit-field.yaml",
        "invalid-present-retire.yaml",
        "invalid-uppercase-controlled-value.yaml",
        "invalid-schema-explicit-tag.yaml",
        "invalid-schema-hex.yaml",
        "invalid-schema-plus.yaml",
        "invalid-schema-leading-zero.yaml",
        "invalid-merge-key.yaml",
        "invalid-timestamp-hour.yaml",
        "invalid-timestamp-zone-minute.yaml",
        "invalid-present-merge.yaml",
        "invalid-record-limit.yaml",
        "invalid-target-limit.yaml",
        "invalid-document-marker.yaml",
        "invalid-unquoted-timestamp.yaml",
        "invalid-leading-zero-limit.yaml",
        "invalid-trailing-decimal.yaml",
        "invalid-negative-trailing-decimal.yaml",
        "invalid-trailing-decimal-exponent.yaml",
        "invalid-tilde-null.yaml",
        "invalid-empty-null.yaml",
    ):
        try:
            load_at(project, packs, providers, fixtures / name)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Malformed reconciliation fixture was accepted: {name}")

    limited = load_at(project, packs, providers, fixtures / "branch-limit.yaml")
    try:
        limited.resolve("category", "branch-limit-source")
    except ValueError:
        pass
    else:
        raise AssertionError("Reconciliation branch limit did not stop expansion.")

    step_limited = load_at(project, packs, providers, fixtures / "resolution-step-limit.yaml")
    try:
        step_limited.resolve("category", "step-limit-a")
    except ValueError:
        pass
    else:
        raise AssertionError("Reconciliation step limit did not stop traversal.")

    with tempfile.TemporaryDirectory(prefix="knowledge-reconciliation-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_bytes = (fixtures / "valid-v4.yaml").read_bytes()
        for name, raw in (
            ("invalid-utf8.yaml", b"schema_version: 4\ninvalid: \xff\n"),
            ("utf8-bom.yaml", b"\xef\xbb\xbf" + valid_bytes),
        ):
            malformed_path = temp_root / name
            malformed_path.write_bytes(raw)
            try:
                load_at(project, packs, providers, malformed_path)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Byte-level YAML fixture was accepted: {name}")

        budget_path = temp_root / "budget.yaml"
        try:
            validate_yaml_source(
                "value: \U0001f600\U0001f600\n",
                "test registry",
                budget_path,
                max_scalar_bytes=7,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("UTF-8 scalar-byte budget did not reject two emoji.")
        try:
            validate_yaml_source(
                "value: 12\n", "test registry", budget_path, max_bytes=9
            )
        except ValueError:
            pass
        else:
            raise AssertionError("UTF-8 file-byte budget was not enforced.")

        path = Path(temp_dir) / "deep-chain.yaml"
        path.write_text(yaml.safe_dump(deep_registry(args.deep_chain), sort_keys=False), encoding="utf-8")
        deep = load_at(project, packs, providers, path)
        result = deep.resolve("category", "deep-0000")
        if result.outcome != "redirected" or len(result.reconciliation_ids) != args.deep_chain:
            raise AssertionError("Deep reconciliation chain did not resolve completely.")

    summary = {
        "schema_version": 4,
        "resolution_vectors": len(actual),
        "malformed_reconciliation_fixtures": 40,
        "malformed_mapping_key_fixtures": 9,
        "byte_scalar_key_parity": True,
        "branch_limit_checked": True,
        "step_limit_checked": True,
        "deep_chain_hops": args.deep_chain,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"Reconciliation conformance passed: {summary['resolution_vectors']} vectors, "
            f"{summary['malformed_reconciliation_fixtures']} malformed reconciliation fixtures, "
            f"{summary['malformed_mapping_key_fixtures']} malformed mapping-key fixtures, "
            f"byte/scalar/key parity, branch and step limits, {summary['deep_chain_hops']}-hop chain."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
