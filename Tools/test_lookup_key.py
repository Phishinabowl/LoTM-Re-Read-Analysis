import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile

from lookup_key_config import load_lookup_key_config
from project_config import load_project_config


def from_codepoints(values: list[int]) -> str:
    return "".join(chr(value) for value in values)


def to_codepoints(value: str) -> list[int]:
    return [ord(character) for character in value]


def mutate_registry(canonical: dict, case_id: str) -> dict:
    registry = copy.deepcopy(canonical)
    if case_id == "unknown-root-field":
        registry["unexpected"] = True
    elif case_id == "schema-version-string":
        registry["schema_version"] = "1"
    elif case_id == "unsupported-algorithm":
        registry["algorithm"] = "runtime-default"
    elif case_id == "trim-not-array":
        registry["trim_codepoints"] = "32"
    elif case_id == "trim-surrogate":
        registry["trim_codepoints"] = [0xD800]
    elif case_id == "case-folding-invalid-key":
        registry["case_folding"] = {"D800": [97]}
    elif case_id == "case-folding-empty-sequence":
        registry["case_folding"] = {"0041": []}
    elif case_id == "case-folding-noninteger-sequence":
        registry["case_folding"] = {"0041": ["97"]}
    elif case_id == "combining-class-zero":
        registry["canonical_combining_class"] = {"0300": 0}
    elif case_id == "composition-malformed-key":
        registry["canonical_composition"] = {"0041": 65}
    elif case_id == "composition-surrogate-target":
        registry["canonical_composition"] = {"0041+0300": 0xD800}
    elif case_id == "declared-count-mismatch":
        registry["counts"]["case_folding"] += 1
    else:
        raise AssertionError(f"Unknown lookup-key mutation case: {case_id}")
    return registry


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except (TypeError, ValueError):
        return
    raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pinned lookup-key normalization conformance tests.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = args.root.resolve()
    data_dir = root / "Framework" / "Data"
    project = load_project_config(root)
    config = load_lookup_key_config(project)
    vectors = json.loads((data_dir / "lookup-key-regression-vectors.json").read_text(encoding="utf-8"))
    invalid = json.loads((data_dir / "Lookup-Key" / "invalid-cases.json").read_text(encoding="utf-8"))
    if vectors.get("schema_version") != 1 or vectors.get("algorithm") != config.algorithm:
        raise AssertionError("Lookup-key vector schema or algorithm does not match the loaded registry.")
    if invalid.get("schema_version") != 1:
        raise AssertionError("Unsupported malformed lookup-key fixture schema.")

    for case in vectors["equivalent"]:
        if config.normalize(from_codepoints(case["left"])) != config.normalize(from_codepoints(case["right"])):
            raise AssertionError(f"Equivalent lookup-key vector remained distinct: {case['id']}")
    for case in vectors["distinct"]:
        if config.normalize(from_codepoints(case["left"])) == config.normalize(from_codepoints(case["right"])):
            raise AssertionError(f"Distinct lookup-key vector collided: {case['id']}")
    for case in vectors["normalized"]:
        actual = to_codepoints(config.normalize(from_codepoints(case["input"])))
        if actual != case["expected"]:
            raise AssertionError(f"Lookup-key normalized output differed: {case['id']}")

    expect_rejected(lambda: config.normalize(123), "Non-string lookup-key input was accepted.")
    expect_rejected(lambda: config.normalize("\ud800"), "Unpaired-surrogate lookup-key input was accepted.")

    canonical = json.loads(project.lookup_keys_registry.read_text(encoding="ascii"))
    with tempfile.TemporaryDirectory(prefix="knowledge-lookup-key-") as temp_dir:
        temp_root = Path(temp_dir)
        for case in invalid["cases"]:
            path = temp_root / f"{case['id']}.json"
            if case["id"] == "malformed-json":
                path.write_text('{"schema_version": 1,', encoding="ascii")
            else:
                path.write_text(
                    json.dumps(mutate_registry(canonical, case["id"]), ensure_ascii=True, separators=(",", ":")),
                    encoding="ascii",
                )
            test_project = replace(project, lookup_keys_registry=path)
            expect_rejected(
                lambda test_project=test_project: load_lookup_key_config(test_project),
                f"Malformed lookup-key registry was accepted: {case['id']}",
            )

    summary = {
        "schema_version": 1,
        "unicode_version": config.unicode_version,
        "equivalent_vectors": len(vectors["equivalent"]),
        "distinct_vectors": len(vectors["distinct"]),
        "normalized_vectors": len(vectors["normalized"]),
        "invalid_registry_cases": len(invalid["cases"]),
        "invalid_input_cases": 2,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Lookup-key conformance passed: "
            f"Unicode {summary['unicode_version']}, {summary['equivalent_vectors']} equivalent, "
            f"{summary['distinct_vectors']} distinct, {summary['normalized_vectors']} exact-output, "
            f"{summary['invalid_registry_cases']} malformed-registry, and "
            f"{summary['invalid_input_cases']} invalid-input cases."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
