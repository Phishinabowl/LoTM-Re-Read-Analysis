"""Child probe: only the installed runtime may satisfy imports; fixtures remain external."""

import argparse
import hashlib
import importlib
from importlib import metadata
import json
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rejected(action, text):
    try:
        action()
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        require(text in str(error), f"Wrong failure classification: {error}")
        return
    raise ValueError("Expected external-root/data rejection: " + text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--identity-only", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text())
    prefix = Path(sys.prefix).resolve()
    require(sys.prefix != sys.base_prefix, "Installed verification requires an isolated environment")
    require(
        ".".join(map(str, sys.version_info[:3])) == contract["python_version"], "Installed interpreter version mismatch"
    )
    import knowledge_framework as framework
    import yaml

    distribution = metadata.distribution("knowledge-framework")
    require(distribution.version == contract["version"] == framework.__version__, "Installed package version mismatch")
    require(metadata.version("PyYAML") == contract["yaml_version"], "Installed runtime dependency version mismatch")
    require(Path(yaml.__file__).resolve().is_relative_to(prefix), "Dependency import escaped isolated environment")
    metadata_file = distribution.locate_file(f"knowledge_framework-{contract['version']}.dist-info/METADATA")
    require(
        hashlib.sha256(Path(metadata_file).read_bytes()).hexdigest() == contract["metadata_sha256"],
        "Installed metadata differs from wheel",
    )
    for relative, expected in contract["runtime_sha256"].items():
        module_name = relative.removesuffix(".py").replace("/", ".")
        if module_name.endswith(".__init__"):
            module_name = module_name.removesuffix(".__init__")
        module = importlib.import_module(module_name)
        origin = Path(module.__file__).resolve()
        require(origin.is_relative_to(prefix), "Framework import escaped isolated environment: " + str(origin))
        require(
            origin.relative_to(Path(framework.__file__).parent.parent.resolve()).as_posix() == relative,
            "Unexpected module location",
        )
        require(
            hashlib.sha256(origin.read_bytes()).hexdigest() == expected,
            "Installed module differs from wheel: " + relative,
        )
    license_file = distribution.locate_file(f"knowledge_framework-{contract['version']}.dist-info/licenses/LICENSE")
    require(
        hashlib.sha256(Path(license_file).read_bytes()).hexdigest() == contract["license_sha256"],
        "Installed license differs from wheel",
    )
    result = {
        "version": distribution.version,
        "origin": framework.__file__,
        "runtime_modules": len(contract["runtime_sha256"]),
    }
    if not args.identity_only:
        root = args.root.resolve()
        require(framework.resolve_framework_root(root) == root, "Explicit framework root changed")
        require(framework.resolve_project_root(root) == root, "Explicit project root changed")
        catalog = framework.load_framework_catalog(root)
        expectations = json.loads((root / "Framework/Data/Framework-Catalog/expectations.json").read_text())
        summary = catalog.to_dict()["summary"]
        for key in (
            "pack_count",
            "capability_count",
            "capability_group_count",
            "available_capability_count",
            "planned_capability_count",
        ):
            require(summary[key] == expectations["canonical_" + key], "Retained catalog expectation differs: " + key)
        schema = framework.load_effective_project_schema(root)
        require(schema.project["project_id"] == "extraction-smoke", "Neutral consumer identity changed")
        require([row["id"] for row in schema.packs] == ["core"], "Neutral consumer selection changed")
        require(
            framework.effective_schema_json(schema)
            == framework.effective_schema_json(framework.load_effective_project_schema(root)),
            "Composition is not deterministic",
        )
        require(
            framework.compose_effective_schema_report_model(schema)["summary"]["selected_packs"] == 1,
            "Report composition differs",
        )
        from knowledge_framework.lookup_key_config import load_lookup_key_config
        from knowledge_framework.project_config import load_project_config
        from knowledge_framework.strict_yaml import load_yaml_file

        lookup = load_lookup_key_config(load_project_config(root))
        vectors = json.loads((root / "Framework/Data/lookup-key-regression-vectors.json").read_text())
        text = lambda points: "".join(map(chr, points))
        count = 0
        for case in vectors["equivalent"]:
            require(
                lookup.normalize(text(case["left"])) == lookup.normalize(text(case["right"])),
                "Equivalent lookup vector failed: " + case["id"],
            )
            count += 1
        for case in vectors["distinct"]:
            require(
                lookup.normalize(text(case["left"])) != lookup.normalize(text(case["right"])),
                "Distinct lookup vector failed: " + case["id"],
            )
            count += 1
        for case in vectors["normalized"]:
            require(
                list(map(ord, lookup.normalize(text(case["input"])))) == case["expected"],
                "Normalized lookup vector failed: " + case["id"],
            )
            count += 1
        strict = root / "Framework/Data/Strict-Yaml"
        keys = load_yaml_file(strict / "valid-mapping-keys.yaml", "installed YAML fixture", expected_schema_version=1)
        require(
            set(keys["mapping_keys"]) == {"1", "true", "on", "dotted.key", "hyphen-key", "underscore_key"},
            "Mapping key fixture changed",
        )
        invalid = json.loads((strict / "expectations.json").read_text())["invalid_sources"]
        for case in invalid:
            file = root / "invalid-source.yaml"
            file.write_text(case["source"], encoding="utf-8")
            rejected(lambda: load_yaml_file(file, "installed YAML fixture", expected_schema_version=1), "")
        missing = Path.cwd() / "missing-root"
        for resolver in (framework.resolve_framework_root, framework.resolve_project_root):
            rejected(lambda resolver=resolver: resolver(missing, environment={}), "missing required manifest")
            rejected(
                lambda resolver=resolver: resolver(
                    current_directory=Path.cwd(), executable_path=Path.cwd() / "probe.py", environment={}
                ),
                "Could not auto-detect",
            )
        rejected(lambda: framework.load_effective_project_schema(missing), "manifest")
        data_file = root / "Framework/Data/unicode-lookup-16.0.0.json"
        saved = data_file.read_bytes()
        data_file.unlink()
        try:
            rejected(lambda: framework.load_framework_catalog(root), "lookup")
        finally:
            data_file.write_bytes(saved)
        result.update(
            lookup_vectors=count,
            strict_invalid_sources=len(invalid),
            catalog_summary=summary,
            project_id=schema.project["project_id"],
            external_failure_checks=6,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
