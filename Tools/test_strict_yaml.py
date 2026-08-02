import argparse
import json
from pathlib import Path
import tempfile

from project_config import resolve_project_root
from strict_yaml import is_rfc3339_timestamp, load_yaml_file, validate_yaml_source


INVALID_MAPPING_FIXTURES = (
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


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except ValueError:
        return
    raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run strict framework-YAML ingestion conformance tests.")
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    fixtures = root / "Framework" / "Data" / "Strict-Yaml"
    expectations = json.loads((fixtures / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("schema_version") != 1:
        raise AssertionError("Unsupported strict-YAML expectation schema.")

    mapping_keys = load_yaml_file(
        fixtures / "valid-mapping-keys.yaml", "strict YAML fixture", expected_schema_version=1
    )
    expected_keys = {"1", "true", "on", "dotted.key", "hyphen-key", "underscore_key"}
    if set(mapping_keys["mapping_keys"]) != expected_keys or not all(
        type(key) is str for key in mapping_keys["mapping_keys"]
    ):
        raise AssertionError("Canonical mapping-key fixture did not preserve string keys.")

    scalars = load_yaml_file(fixtures / "valid-scalars.yaml", "strict YAML fixture", expected_schema_version=1)
    expected_scalars = {
        "boolean_true": True,
        "boolean_false": False,
        "explicit_null": None,
        "zero": 0,
        "negative_integer": -12,
        "positive_integer": 12,
        "legacy_on": "on",
        "legacy_off": "off",
        "legacy_yes": "yes",
        "legacy_no": "no",
        "quoted_decimal": "1.5",
        "quoted_timestamp": "2026-08-02T12:34:56Z",
    }
    if {key: scalars[key] for key in expected_scalars} != expected_scalars:
        raise AssertionError("Portable scalar fixture did not retain exact values and types.")

    for name in INVALID_MAPPING_FIXTURES:
        expect_rejected(
            lambda name=name: load_yaml_file(fixtures / name, "strict YAML fixture", expected_schema_version=1),
            f"Noncanonical mapping-key fixture was accepted: {name}",
        )

    with tempfile.TemporaryDirectory(prefix="knowledge-strict-yaml-") as temp_dir:
        temp_root = Path(temp_dir)
        for case in expectations["invalid_sources"]:
            path = temp_root / f"{case['id']}.yaml"
            path.write_text(case["source"], encoding="utf-8")
            expect_rejected(
                lambda path=path: load_yaml_file(path, "strict YAML fixture", expected_schema_version=1),
                f"Nonportable YAML source was accepted: {case['id']}",
            )

        valid_bytes = (fixtures / "valid-scalars.yaml").read_bytes()
        for name, raw in (
            ("utf8-bom.yaml", b"\xef\xbb\xbf" + valid_bytes),
            ("invalid-utf8.yaml", b"schema_version: 1\nvalue: \xff\n"),
        ):
            path = temp_root / name
            path.write_bytes(raw)
            expect_rejected(
                lambda path=path: load_yaml_file(path, "strict YAML fixture", expected_schema_version=1),
                f"Byte-level YAML fixture was accepted: {name}",
            )

        budget_path = temp_root / "budget.yaml"
        budget_cases = (
            ("file-bytes", "value: 12\n", {"max_bytes": 9}),
            ("scalar-bytes", "value: \U0001f600\U0001f600\n", {"max_scalar_bytes": 7}),
            ("node-count", "value: [1, 2, 3]\n", {"max_nodes": 3}),
            ("nesting-depth", "value: [[[[0]]]]\n", {"max_depth": 3}),
        )
        for case_id, source, limits in budget_cases:
            expect_rejected(
                lambda source=source, limits=limits: validate_yaml_source(
                    source, "test registry", budget_path, **limits
                ),
                f"YAML parser budget was not enforced: {case_id}",
            )

    for codepoints in expectations["rfc3339_valid"]:
        value = "".join(chr(codepoint) for codepoint in codepoints)
        if not is_rfc3339_timestamp(value):
            raise AssertionError(f"Valid RFC 3339 timestamp was rejected: {value}")
    for codepoints in expectations["rfc3339_invalid"]:
        value = "".join(chr(codepoint) for codepoint in codepoints)
        if is_rfc3339_timestamp(value):
            raise AssertionError(f"Invalid RFC 3339 timestamp was accepted: {value}")

    summary = {
        "schema_version": 1,
        "valid_scalar_cases": len(expected_scalars),
        "invalid_mapping_key_fixtures": len(INVALID_MAPPING_FIXTURES),
        "invalid_source_cases": len(expectations["invalid_sources"]),
        "byte_cases": 2,
        "budget_cases": 4,
        "rfc3339_valid_cases": len(expectations["rfc3339_valid"]),
        "rfc3339_invalid_cases": len(expectations["rfc3339_invalid"]),
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Strict YAML conformance passed: "
            f"{summary['valid_scalar_cases']} scalar, {summary['invalid_mapping_key_fixtures']} mapping-key, "
            f"{summary['invalid_source_cases']} source, {summary['byte_cases']} byte, "
            f"{summary['budget_cases']} budget, and "
            f"{summary['rfc3339_valid_cases'] + summary['rfc3339_invalid_cases']} timestamp cases."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
