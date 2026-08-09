"""Conformance vectors for project-independent capability-roadmap loading."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile


TOOLS_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = TOOLS_ROOT / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.capability_roadmap import (  # noqa: E402
    load_capability_roadmap,
    load_capability_roadmap_file,
)
from knowledge_framework.framework_config import load_framework_config  # noqa: E402
from knowledge_framework.framework_paths import resolve_framework_root  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    return parser


def assert_rejected(action, expected_text: str) -> None:
    try:
        action()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"Expected error containing {expected_text!r}, got: {exc}") from exc
        return
    raise AssertionError(f"Expected rejection containing {expected_text!r}.")


def main() -> int:
    args = build_parser().parse_args()
    root = resolve_framework_root(args.root, executable_path=__file__)
    fixture_root = root / "Framework" / "Data" / "Capability-Roadmap"
    catalog = json.loads((fixture_root / "catalog.json").read_text(encoding="utf-8"))
    valid = json.loads((fixture_root / "valid-roadmap.json").read_text(encoding="utf-8"))
    config = load_framework_config(root)
    invalid_cases = 0

    with tempfile.TemporaryDirectory(prefix="knowledge-capability-roadmap-") as temp:
        temp_root = Path(temp)

        def load_document(document: dict):
            path = temp_root / "roadmap.json"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
            return load_capability_roadmap_file(path, framework_config=config, catalog=catalog)

        model = load_document(valid)
        normalized = model.to_dict()
        assert normalized == load_document(valid).to_dict()
        assert [row["capability_id"] for row in normalized["capabilities"]] == [
            "deferred-capability",
            "scheduled-capability",
        ]
        assert normalized["capabilities"][0]["disposition"] == "accepted-deferral"
        assert normalized["capabilities"][1]["delivery_target_id"] == "platform-phase-alpha"

        cases: list[tuple[str, object, str]] = [
            (
                "unknown-root-field",
                lambda row: row.update({"unexpected": True}),
                "unsupported field",
            ),
            (
                "wrong-registry-id",
                lambda row: row.update({"registry_id": "other-roadmap"}),
                "must be `capability-roadmap`",
            ),
            (
                "unknown-target-kind",
                lambda row: row["delivery_targets"]["platform-phase-alpha"].update({"kind": "milestone"}),
                "must be one of",
            ),
            (
                "unknown-capability",
                lambda row: row["capabilities"].update(
                    {"unknown-capability": deepcopy(row["capabilities"]["scheduled-capability"])}
                ),
                "unknown capability ID",
            ),
            (
                "missing-planned-capability",
                lambda row: row["capabilities"].pop("deferred-capability"),
                "missing planned capability",
            ),
            (
                "non-planned-capability",
                lambda row: row["capabilities"].update(
                    {"available-capability": deepcopy(row["capabilities"]["scheduled-capability"])}
                ),
                "non-planned capability",
            ),
            (
                "unknown-delivery-target",
                lambda row: row["capabilities"]["scheduled-capability"].update(
                    {"delivery_target_id": "platform-phase-missing"}
                ),
                "unknown delivery target",
            ),
            (
                "invalid-disposition",
                lambda row: row["capabilities"]["scheduled-capability"].update({"disposition": "maybe"}),
                "must be one of",
            ),
            (
                "malformed-deferral",
                lambda row: row["capabilities"]["deferred-capability"].pop("review_trigger"),
                "review_trigger",
            ),
            (
                "unknown-prerequisite",
                lambda row: row["capabilities"]["scheduled-capability"].update(
                    {"platform_prerequisite_ids": ["platform-phase-missing"]}
                ),
                "unknown delivery target",
            ),
            (
                "self-target-prerequisite",
                lambda row: row["capabilities"]["scheduled-capability"].update(
                    {"platform_prerequisite_ids": ["platform-phase-alpha"]}
                ),
                "own delivery target",
            ),
            (
                "unknown-domain-dependency",
                lambda row: row["capabilities"]["scheduled-capability"].update(
                    {"domain_capability_dependency_ids": ["unknown-capability"]}
                ),
                "unknown capability",
            ),
            (
                "self-domain-dependency",
                lambda row: row["capabilities"]["scheduled-capability"].update(
                    {"domain_capability_dependency_ids": ["scheduled-capability"]}
                ),
                "cannot depend on itself",
            ),
            (
                "domain-dependency-cycle",
                lambda row: row["capabilities"]["deferred-capability"].update(
                    {"domain_capability_dependency_ids": ["scheduled-capability"]}
                ),
                "contain a cycle",
            ),
            (
                "duplicate-list-value",
                lambda row: row["capabilities"]["scheduled-capability"].update(
                    {"domain_capability_dependency_ids": ["deferred-capability", "deferred-capability"]}
                ),
                "duplicate values",
            ),
            (
                "invalid-plan-path",
                lambda row: row["delivery_targets"]["platform-phase-alpha"].update(
                    {"plan_path": "../platform-implementation-plan.md"}
                ),
                "confined framework-relative path",
            ),
            (
                "unknown-evidence-kind",
                lambda row: row["capabilities"]["scheduled-capability"]["implementation_evidence"][0].update(
                    {"kind": "wish"}
                ),
                "must be one of",
            ),
            (
                "wrong-evidence-provider",
                lambda row: row["capabilities"]["scheduled-capability"]["implementation_evidence"][0].update(
                    {"provider_pack_id": "fixture-core"}
                ),
                "is not a provider",
            ),
        ]
        for _, mutate, expected in cases:
            document = deepcopy(valid)
            mutate(document)
            assert_rejected(lambda document=document: load_document(document), expected)
            invalid_cases += 1

        duplicate_path = temp_root / "duplicate.yaml"
        duplicate_path.write_text(
            "schema_version: 1\nregistry_id: capability-roadmap\nregistry_id: duplicate\n",
            encoding="utf-8",
            newline="\n",
        )
        assert_rejected(
            lambda: load_capability_roadmap_file(duplicate_path, framework_config=config, catalog=catalog),
            "duplicate mapping key",
        )
        invalid_cases += 1

        scale_catalog = {"contract": "framework-catalog", "capabilities": []}
        scale_document = deepcopy(valid)
        scale_document["capabilities"] = {}
        for index in range(128):
            capability_id = f"scale-capability-{index:03d}"
            scale_catalog["capabilities"].append(
                {"id": capability_id, "planned": True, "providers": [{"pack_id": "fixture-domain"}]}
            )
            scale_document["capabilities"][capability_id] = {
                "disposition": "scheduled",
                "delivery_target_id": "platform-phase-alpha",
                "rationale": "Generated scale mapping.",
                "platform_prerequisite_ids": [],
                "domain_capability_dependency_ids": [],
                "implementation_evidence": [],
            }
        path = temp_root / "scale.json"
        path.write_text(json.dumps(scale_document), encoding="utf-8")
        scale = load_capability_roadmap_file(path, framework_config=config, catalog=scale_catalog)
        assert len(scale.capabilities) == 128

    canonical = load_capability_roadmap(root)
    assert len(canonical.delivery_targets) == 8
    assert len(canonical.capabilities) == 13
    summary = {
        "canonical_capabilities": len(canonical.capabilities),
        "canonical_delivery_targets": len(canonical.delivery_targets),
        "invalid_cases": invalid_cases,
        "neutral_capabilities": len(model.capabilities),
        "scale_capabilities": 128,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Capability-roadmap conformance passed: "
            f"{len(canonical.capabilities)} canonical mappings, {invalid_cases} invalid cases, "
            "128 scale mappings."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
