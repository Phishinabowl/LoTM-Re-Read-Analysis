"""Conformance vectors for the optional distribution and entitlement boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


TOOLS_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = TOOLS_ROOT / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.effective_schema import effective_schema_json, load_effective_project_schema  # noqa: E402
from knowledge_framework.framework_catalog import framework_catalog_json, load_framework_catalog  # noqa: E402
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402


REQUIRED_PACK_REJECTIONS = {
    "registry-unselected-dependency",
    "pack-executable-entrypoint",
    "pack-install-hooks",
    "pack-embedded-credentials",
    "pack-commercial-offerings",
    "pack-entitlements",
}
FORBIDDEN_OUTPUT_KEYS = {
    "account_id",
    "acquirable",
    "commercial_offerings",
    "entitled",
    "entitlement_provider",
    "entitlements",
    "grants",
    "offering_catalog",
    "post_install_enforcement",
    "price",
    "pricing",
    "product_tier",
    "sku",
    "subscription_id",
    "tenant_id",
    "token",
}
PROJECT_INJECTION_CASES = {
    "account_id": "fixture-account",
    "commercial_offerings": ["premium"],
    "entitlements": ["paid"],
    "pricing": {"amount": "999.00"},
    "post_install_enforcement": "disable",
}
PROJECT_DIRECTORIES = (
    "Artwork",
    "Tools",
    "Visualization",
    "Visualization/graphs",
    "Visualization/rendered",
)
PROJECT_CONTENT_DIRECTORIES = ("Boards", "Glossary_Threads", "Investigations", "Volumes")
PROJECT_FILES = (
    "Tools/Commands/Maintenance/clean_temp_files.py",
    "Tools/Commands/Maintenance/Clean-TempFiles.ps1",
    "Visualization/visualize.py",
    "Visualization/visualize.ps1",
    "Visualization/config/render-settings.json",
    "Visualization/config/puppeteer-config.json",
    "Visualization/data/refresh-snapshot.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    return parser.parse_args()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="ascii", newline="\n")


def prepare_project(source_root: Path, target_root: Path) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
    shutil.copytree(source_root / "Framework", target_root / "Framework", ignore=ignore)
    shutil.copytree(source_root / "Project_Config", target_root / "Project_Config", ignore=ignore)
    for source in source_root.glob("*.md"):
        shutil.copy2(source, target_root / source.name)
    for relative in PROJECT_CONTENT_DIRECTORIES:
        shutil.copytree(source_root / relative, target_root / relative, ignore=ignore)
    for relative in PROJECT_DIRECTORIES:
        (target_root / relative).mkdir(parents=True, exist_ok=True)
    for relative in PROJECT_FILES:
        path = target_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n" if path.suffix == ".json" else "# Boundary fixture.\n", encoding="ascii")


def project_composition_summary(source_root: Path, project_root: Path) -> dict:
    command = [
        sys.executable,
        str(source_root / "Tools" / "Conformance" / "Suites" / "test_project_composition.py"),
        "--root",
        str(project_root),
        "--json",
    ]
    completed = subprocess.run(
        command,
        cwd=source_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise AssertionError(f"Project-composition boundary probe failed: {detail}")
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("Project-composition boundary probe emitted no JSON summary.")
    document = json.loads(lines[-1])
    if not isinstance(document, dict):
        raise AssertionError("Project-composition boundary probe returned a non-object summary.")
    return document


def semantic_outputs(source_root: Path, project_root: Path) -> dict[str, object]:
    return {
        "catalog": json.loads(framework_catalog_json(load_framework_catalog(project_root))),
        "effective_schema": json.loads(effective_schema_json(load_effective_project_schema(project_root))),
        "project_composition": project_composition_summary(source_root, project_root),
    }


def collect_forbidden_keys(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_OUTPUT_KEYS:
                findings.append(child_path)
            findings.extend(collect_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(collect_forbidden_keys(child, f"{path}[{index}]"))
    return findings


def expect_project_injection_rejected(project_root: Path, key: str, value: object) -> None:
    manifest = project_root / "Project_Config" / "project.yaml"
    original = manifest.read_text(encoding="utf-8")
    try:
        serialized = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        manifest.write_text(original + f"\n{key}: {serialized}\n", encoding="utf-8", newline="\n")
        try:
            load_project_config(project_root)
        except (KeyError, TypeError, ValueError):
            return
        raise AssertionError(f"Portable project manifest accepted commercial field: {key}")
    finally:
        manifest.write_text(original, encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    expectations = json.loads(
        (root / "Framework" / "Data" / "Schema-Packs" / "expectations.json").read_text(encoding="utf-8")
    )
    rejection_ids = {case["id"] for case in expectations["invalid_cases"]}
    missing_rejections = REQUIRED_PACK_REJECTIONS - rejection_ids
    if missing_rejections:
        raise AssertionError(f"Required schema-pack boundary rejections are missing: {sorted(missing_rejections)}")

    fixture = json.loads(
        (root / "Framework" / "Data" / "Distribution-Boundary" / "adversarial-external-metadata.json").read_text(
            encoding="utf-8"
        )
    )
    with tempfile.TemporaryDirectory(prefix="knowledge-distribution-boundary-") as temp_directory:
        project_root = Path(temp_directory) / "project"
        prepare_project(root, project_root)
        baseline = semantic_outputs(root, project_root)
        forbidden_findings = collect_forbidden_keys(baseline)
        if forbidden_findings:
            raise AssertionError(f"Commercial fields leaked into portable outputs: {forbidden_findings}")

        sidecar_paths = (
            project_root / "Framework" / "Distribution" / "offerings.json",
            project_root / "Project_Config" / "entitlements.json",
            project_root / "Framework" / "Packs" / "narrative-media" / "entitlement.json",
            project_root / "Framework" / "Packs" / "remote-premium" / "offering.json",
        )
        for path in sidecar_paths:
            write_json(path, fixture)

        with_external_metadata = semantic_outputs(root, project_root)
        if with_external_metadata != baseline:
            raise AssertionError("External commercial metadata changed portable composition outputs.")
        for key, value in PROJECT_INJECTION_CASES.items():
            expect_project_injection_rejected(project_root, key, value)

    summary = {
        "schema_version": 1,
        "pack_rejection_vectors": len(REQUIRED_PACK_REJECTIONS),
        "project_injection_cases": len(PROJECT_INJECTION_CASES),
        "external_metadata_locations": len(sidecar_paths),
        "semantic_surfaces": len(baseline),
        "provider_failure_inert": True,
        "portable_outputs_unchanged": True,
        "forbidden_output_keys": len(FORBIDDEN_OUTPUT_KEYS),
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Distribution-boundary conformance passed: "
            f"{summary['semantic_surfaces']} semantic surfaces, "
            f"{summary['external_metadata_locations']} inert metadata locations, and "
            f"{summary['project_injection_cases']} rejected project injections."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
