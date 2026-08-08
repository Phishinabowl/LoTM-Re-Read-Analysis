#!/usr/bin/env python3
"""Run registry-driven cross-runtime project compatibility checks."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(__file__).resolve().parents[1] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.project_config import load_project_config  # noqa: E402
from knowledge_framework.project_paths import resolve_project_root  # noqa: E402


REGISTRY_PATH = Path(__file__).with_name("compatibility.json")
# TODO (OWNER): Register normalized-content compatibility as that consumer boundary lands.
ALLOWED_CHECK_KINDS = {
    "artifact-lifecycle",
    "compatibility-reporting",
    "conformance-reporting",
    "effective-schema",
    "framework-catalog",
    "framework-extraction",
    "qa",
    "render",
    "root-discovery",
    "visualization",
}
CHECK_KEYS = {
    "artifact-lifecycle": {"id", "kind", "timeout_seconds"},
    "compatibility-reporting": {"id", "kind", "timeout_seconds"},
    "conformance-reporting": {"id", "kind", "timeout_seconds"},
    "effective-schema": {"id", "kind", "timeout_seconds"},
    "framework-catalog": {"id", "kind", "timeout_seconds"},
    "framework-extraction": {"id", "kind", "timeout_seconds"},
    "qa": {"id", "kind", "timeout_seconds", "baseline", "bounded_graphs", "bounded_pages"},
    "render": {
        "id",
        "kind",
        "timeout_seconds",
        "input",
        "output_format",
        "minimum_bytes",
        "required_labels",
    },
    "root-discovery": {"id", "kind", "timeout_seconds", "launch_locations"},
    "visualization": {"id", "kind", "timeout_seconds", "baseline"},
}
GENERATED_KEYS = {"generated_at", "generatedAt"}
MACHINE_ID = re.compile(r"^[a-z][a-z0-9-]*$")
TEXT_EXTENSIONS = {".json", ".md", ".mmd", ".txt", ".yaml", ".yml"}
FAILURE_EXCERPT_LINES = 20
FAILURE_EXCERPT_BYTES = 4096


@dataclass(frozen=True)
class Runtime:
    id: str
    executable: str


@dataclass(frozen=True)
class CommandResult:
    runtime: str
    command: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float


class CompatibilityFailure(RuntimeError):
    """Raised when a compatibility contract is violated."""


def require_string_list(check: dict[str, Any], key: str, *, nonempty: bool = True) -> list[str]:
    value = check.get(key)
    if (
        not isinstance(value, list)
        or (nonempty and not value)
        or not all(isinstance(item, str) and item for item in value)
    ):
        qualifier = "nonempty " if nonempty else ""
        raise CompatibilityFailure(f"Compatibility check {check['id']} requires a {qualifier}string list: {key}")
    if len(value) != len(set(value)):
        raise CompatibilityFailure(f"Compatibility check {check['id']} contains duplicate {key} entries.")
    return value


def validate_relative_path(check: dict[str, Any], key: str) -> None:
    value = check.get(key)
    if not isinstance(value, str) or not value:
        raise CompatibilityFailure(f"Compatibility check {check['id']} requires a string path: {key}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise CompatibilityFailure(f"Compatibility check {check['id']} requires a safe repository-relative {key}.")


def validate_check(check: dict[str, Any]) -> None:
    kind = check.get("kind")
    if kind not in ALLOWED_CHECK_KINDS:
        raise CompatibilityFailure(f"Unsupported compatibility check kind: {kind}")
    unknown = set(check) - CHECK_KEYS[kind]
    if unknown:
        raise CompatibilityFailure(f"Compatibility check {check['id']} has unknown keys: {sorted(unknown)}")
    if not isinstance(check.get("timeout_seconds"), int) or isinstance(check["timeout_seconds"], bool):
        raise CompatibilityFailure(f"Compatibility check {check['id']} requires an integer timeout_seconds.")
    if check["timeout_seconds"] <= 0:
        raise CompatibilityFailure(f"Compatibility check {check['id']} requires a positive timeout_seconds.")
    if kind == "qa":
        validate_relative_path(check, "baseline")
        require_string_list(check, "bounded_graphs")
        require_string_list(check, "bounded_pages")
    elif kind == "visualization":
        validate_relative_path(check, "baseline")
    elif kind == "root-discovery":
        launch_locations = require_string_list(check, "launch_locations")
        expected = ["repo-root", "tools", "nested", "unrelated"]
        if launch_locations != expected:
            raise CompatibilityFailure(
                f"Compatibility check {check['id']} launch_locations must be exactly {expected} in order."
            )
    elif kind == "render":
        validate_relative_path(check, "input")
        if check.get("output_format") != "svg":
            raise CompatibilityFailure(f"Compatibility check {check['id']} output_format must be svg.")
        minimum_bytes = check.get("minimum_bytes")
        if not isinstance(minimum_bytes, int) or isinstance(minimum_bytes, bool) or minimum_bytes <= 0:
            raise CompatibilityFailure(f"Compatibility check {check['id']} requires a positive integer minimum_bytes.")
        require_string_list(check, "required_labels")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Project root; auto-detected when omitted.")
    parser.add_argument("--registry", default=str(REGISTRY_PATH), help="Compatibility registry path.")
    parser.add_argument("--profile", default="local", help="Registered compatibility profile.")
    parser.add_argument("--check", action="append", default=[], help="Run only a registered check; repeatable.")
    parser.add_argument("--list", action="store_true", help="List registered profiles and checks.")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="Emit the complete structured JSON result.")
    output_group.add_argument(
        "--summary-json",
        action="store_true",
        help="Emit a concise validation-run-summary without nested check details.",
    )
    parser.add_argument(
        "--report-output",
        metavar="PATH",
        help="Write the complete structured JSON result to a file beneath the project root.",
    )
    parser.add_argument("--keep-output", action="store_true", help="Keep the scoped .tmp output for inspection.")
    parser.add_argument("--output-root", help="Explicit ignored output root beneath repository .tmp.")
    return parser.parse_args()


def load_registry(path: Path) -> dict[str, Any]:
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityFailure(f"Unable to load compatibility registry {path}: {exc}") from exc
    if not isinstance(registry, dict):
        raise CompatibilityFailure("Compatibility registry root must be an object.")
    allowed = {"schema_version", "runtimes", "profiles", "checks"}
    unknown = set(registry) - allowed
    if unknown:
        raise CompatibilityFailure(f"Unknown compatibility registry keys: {sorted(unknown)}")
    if registry.get("schema_version") != 2:
        raise CompatibilityFailure("Compatibility registry schema_version must be integer 2.")
    runtimes = registry.get("runtimes")
    if runtimes != ["python", "powershell7", "powershell51"]:
        raise CompatibilityFailure("Compatibility runtimes must be python, powershell7, powershell51 in order.")
    checks = registry.get("checks")
    profiles = registry.get("profiles")
    if not isinstance(checks, list) or not isinstance(profiles, dict):
        raise CompatibilityFailure("Compatibility checks must be a list and profiles must be an object.")
    check_ids: set[str] = set()
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("id"), str) or not MACHINE_ID.fullmatch(check["id"]):
            raise CompatibilityFailure("Each compatibility check requires a lowercase machine id.")
        if check["id"] in check_ids:
            raise CompatibilityFailure(f"Duplicate compatibility check id: {check['id']}")
        validate_check(check)
        check_ids.add(check["id"])
    for profile, selected in profiles.items():
        if not isinstance(profile, str) or not MACHINE_ID.fullmatch(profile):
            raise CompatibilityFailure("Every compatibility profile requires a lowercase machine id.")
        if not isinstance(selected, list) or not selected or not all(isinstance(item, str) for item in selected):
            raise CompatibilityFailure("Every compatibility profile requires a nonempty check-id list.")
        missing = set(selected) - check_ids
        if missing:
            raise CompatibilityFailure(f"Profile {profile} references unknown checks: {sorted(missing)}")
        if len(selected) != len(set(selected)):
            raise CompatibilityFailure(f"Profile {profile} contains duplicate check ids.")
    return registry


def resolve_registry_path(value: str, root: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def resolve_output_root(value: str | None, root: Path) -> Path:
    tmp_root = (root / ".tmp").resolve()
    if value:
        output = Path(value)
        if not output.is_absolute():
            output = root / output
        output = output.resolve()
    else:
        output = tmp_root / "compatibility" / f"run-{int(time.time())}-{os.getpid()}"
    if output == tmp_root or tmp_root not in output.parents:
        raise CompatibilityFailure(f"Compatibility output must be a child of {tmp_root}: {output}")
    return output


def resolve_report_output(value: str, root: Path) -> Path:
    candidate = Path(value)
    output = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if output == root or root not in output.parents:
        raise CompatibilityFailure(f"Compatibility report output must be a file beneath the project root: {output}")
    if output.exists() and not output.is_file():
        raise CompatibilityFailure(f"Compatibility report output must be a file path: {output}")
    return output


def find_runtime(runtime_id: str) -> Runtime:
    if runtime_id == "python":
        return Runtime(runtime_id, sys.executable)
    command = "pwsh" if runtime_id == "powershell7" else "powershell"
    executable = shutil.which(command)
    if not executable:
        raise CompatibilityFailure(f"Required runtime not found on PATH: {command}")
    return Runtime(runtime_id, executable)


def run_command(
    runtime: Runtime,
    command: list[str],
    cwd: Path,
    timeout: int,
    *,
    expect_success: bool = True,
) -> CommandResult:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    result = CommandResult(
        runtime=runtime.id,
        command=command,
        cwd=str(cwd),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=round(time.perf_counter() - started, 3),
    )
    if expect_success and result.exit_code != 0:
        details = (result.stdout + "\n" + result.stderr).strip()
        raise CompatibilityFailure(f"{runtime.id} command failed ({result.exit_code}): {' '.join(command)}\n{details}")
    if not expect_success and result.exit_code == 0:
        raise CompatibilityFailure(f"{runtime.id} command unexpectedly succeeded: {' '.join(command)}")
    return result


def powershell_prefix(runtime: Runtime) -> list[str]:
    prefix = [runtime.executable, "-NoProfile"]
    if runtime.id == "powershell51":
        prefix.extend(["-ExecutionPolicy", "Bypass"])
    return prefix


def python_or_powershell_command(
    runtime: Runtime,
    python_script: Path,
    powershell_script: Path,
    python_args: list[str],
    powershell_args: list[str],
) -> list[str]:
    if runtime.id == "python":
        return [runtime.executable, str(python_script), *python_args]
    return [*powershell_prefix(runtime), "-File", str(powershell_script), *powershell_args]


def parse_json_output(text: str) -> Any:
    decoder = json.JSONDecoder()
    candidates: list[Any] = []
    for index, character in enumerate(text):
        if character not in "[{":
            continue
        try:
            value, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if not text[index + end :].strip():
            return value
        candidates.append(value)
    if not candidates:
        raise CompatibilityFailure(f"Command did not emit parseable JSON: {text[-1000:]}")
    return candidates[-1]


def normalize_string(value: str, output_roots: list[Path]) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    for output_root in sorted(output_roots, key=lambda item: len(str(item)), reverse=True):
        variants = {
            str(output_root),
            str(output_root).replace("\\", "/"),
            os.path.relpath(output_root, output_root.parents[2]).replace("\\", "/")
            if len(output_root.parents) > 2
            else str(output_root),
        }
        parts = output_root.resolve().parts
        if ".tmp" in parts:
            tmp_index = parts.index(".tmp")
            tmp_relative = str(Path(*parts[tmp_index:]))
            variants.update({tmp_relative, tmp_relative.replace("\\", "/")})
        for variant in sorted(variants, key=len, reverse=True):
            normalized = normalized.replace(variant, "<compat-output>")
            normalized = normalized.replace(variant.replace("/", "\\"), "<compat-output>")
    normalized = re.sub(r"(?m)^generated_at: \".*\"$", 'generated_at: "<generated-at>"', normalized)
    normalized = re.sub(r"(?m)^Last Updated: .*$", "Last Updated: <generated-at>", normalized)
    return normalized


def normalize_value(value: Any, output_roots: list[Path], property_name: str | None = None) -> Any:
    if property_name in GENERATED_KEYS:
        return "<generated-at>"
    if isinstance(value, dict):
        return {key: normalize_value(value[key], output_roots, key) for key in sorted(value)}
    if isinstance(value, list):
        return [normalize_value(item, output_roots) for item in value]
    if isinstance(value, str):
        return normalize_string(value, output_roots)
    return value


def normalized_file(path: Path, output_roots: list[Path]) -> str:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        return json.dumps(
            normalize_value(value, output_roots), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    return normalize_string(text, output_roots)


def normalized_file_sha256(path: Path, output_roots: list[Path]) -> str:
    return hashlib.sha256(normalized_file(path, output_roots).encode("utf-8")).hexdigest()


def normalized_tree_manifest(root: Path, output_roots: list[Path]) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): normalized_file_sha256(path, output_roots)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def normalized_tree_sha256(manifest: dict[str, str]) -> str:
    serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_hash_manifest(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise CompatibilityFailure(f"Consumer baseline requires a nonempty file-hash mapping: {label}")
    for relative_path, digest in value.items():
        if not isinstance(relative_path, str) or not relative_path:
            raise CompatibilityFailure(f"Consumer baseline contains an invalid file path: {label}")
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts or "\\" in relative_path:
            raise CompatibilityFailure(f"Consumer baseline contains an unsafe portable path: {relative_path}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CompatibilityFailure(f"Consumer baseline contains an invalid SHA-256 for {relative_path}.")
    return value


def load_consumer_baseline(check: dict[str, Any], root: Path, section: str) -> dict[str, Any]:
    path = resolve_registry_path(check["baseline"], root)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityFailure(f"Unable to load consumer baseline {path}: {exc}") from exc
    expected_keys = {"schema_version", "normalization_version", "project_id", "visualization", "qa"}
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise CompatibilityFailure(f"Consumer baseline has an invalid root shape: {path}")
    if document["schema_version"] != 1 or document["normalization_version"] != 1:
        raise CompatibilityFailure(f"Consumer baseline uses an unsupported schema or normalization version: {path}")
    project = load_project_config(root)
    if document["project_id"] != project.project_id:
        raise CompatibilityFailure(
            f"Consumer baseline project_id `{document['project_id']}` does not match `{project.project_id}`."
        )
    value = document.get(section)
    if not isinstance(value, dict):
        raise CompatibilityFailure(f"Consumer baseline requires an object section: {section}")
    return value


def assert_semantic_baseline(label: str, actual: dict[str, Any], expected: Any) -> None:
    if not isinstance(expected, dict) or actual != expected:
        raise CompatibilityFailure(f"{label} semantic baseline changed: expected {expected}, actual {actual}")


def assert_tree_baseline(
    label: str,
    actual: dict[str, str],
    expected: Any,
    expected_tree_sha256: Any,
) -> str:
    expected_manifest = validate_hash_manifest(expected, f"{label}.files")
    missing = sorted(set(expected_manifest) - set(actual))
    unexpected = sorted(set(actual) - set(expected_manifest))
    changed = sorted(path for path in set(actual) & set(expected_manifest) if actual[path] != expected_manifest[path])
    actual_tree_sha256 = normalized_tree_sha256(actual)
    if not isinstance(expected_tree_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_tree_sha256):
        raise CompatibilityFailure(f"Consumer baseline contains an invalid tree SHA-256: {label}")
    if missing or unexpected or changed or actual_tree_sha256 != expected_tree_sha256:
        raise CompatibilityFailure(
            f"{label} content baseline changed: missing={missing}, unexpected={unexpected}, changed={changed}, "
            f"expected_tree_sha256={expected_tree_sha256}, actual_tree_sha256={actual_tree_sha256}"
        )
    return actual_tree_sha256


def tree_inventory(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def compare_trees(roots: dict[str, Path]) -> dict[str, Any]:
    inventories = {runtime: tree_inventory(root) for runtime, root in roots.items()}
    reference = inventories["python"]
    if any(inventory != reference for inventory in inventories.values()):
        raise CompatibilityFailure(f"Generated file inventories differ: {inventories}")
    output_roots = list(roots.values())
    mismatches: list[str] = []
    for relative in reference:
        values = {runtime: normalized_file(root / relative, output_roots) for runtime, root in roots.items()}
        if len(set(values.values())) != 1:
            mismatches.append(relative)
    if mismatches:
        raise CompatibilityFailure(f"Normalized generated files differ: {mismatches}")
    return {"file_count": len(reference), "normalized_match_count": len(reference), "mismatches": []}


def sha256_tree(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        if path.is_file():
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.is_dir():
            for child in sorted(item for item in path.rglob("*") if item.is_file()):
                hashes[str(child)] = hashlib.sha256(child.read_bytes()).hexdigest()
    return hashes


def visualization_commands(runtime: Runtime, root: Path, mode: str, arguments: list[str]) -> list[str]:
    python_script = root / "Visualization" / "visualize.py"
    powershell_script = root / "Visualization" / "visualize.ps1"
    python_mode = {"QaRelationship": "qa-relationship"}.get(mode, mode)
    return python_or_powershell_command(
        runtime,
        python_script,
        powershell_script,
        ["--mode", python_mode, *arguments],
        ["-Mode", mode, *arguments],
    )


def write_redirected_settings(root: Path, destination: Path) -> Path:
    source = root / "Visualization" / "config" / "render-settings.json"
    settings = json.loads(source.read_text(encoding="utf-8"))
    relative_root = destination.relative_to(root).as_posix()
    settings["reportPath"] = f"{relative_root}/refresh-report.md"
    settings["snapshotPath"] = f"{relative_root}/refresh-snapshot.json"
    for index, view in enumerate(settings["views"], start=1):
        view["input"] = f"{relative_root}/view-{index}.mmd"
        view["outputs"] = [f"{relative_root}/rendered/view-{index}.svg", f"{relative_root}/rendered/view-{index}.png"]
    path = destination / "render-settings.json"
    destination.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return path


def run_visualization_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    timeout = check["timeout_seconds"]
    baseline = load_consumer_baseline(check, root, "visualization")
    validate_outputs: dict[str, str] = {}
    refresh_roots: dict[str, Path] = {}
    unbounded_paths: dict[str, Path] = {}
    elapsed: dict[str, float] = {}
    for runtime in runtimes:
        runtime_root = output_root / runtime.id
        settings_path = write_redirected_settings(root, runtime_root / "refresh")
        validate = run_command(
            runtime,
            visualization_commands(runtime, root, "Validate", []),
            output_root,
            timeout,
        )
        validate_outputs[runtime.id] = normalize_string(validate.stdout, [output_root])
        refresh_args = (
            ["--settings-path", str(settings_path), "--skip-render"]
            if runtime.id == "python"
            else ["-SettingsPath", str(settings_path), "-SkipRender"]
        )
        refresh = run_command(
            runtime,
            visualization_commands(runtime, root, "Refresh", refresh_args),
            output_root,
            timeout,
        )
        graph_path = runtime_root / "unbounded-relationship.mmd"
        graph_args = (
            ["--graph-path", str(graph_path), "--include-confirmed-confidence"]
            if runtime.id == "python"
            else ["-GraphPath", str(graph_path), "-IncludeConfirmedConfidence"]
        )
        unbounded = run_command(
            runtime,
            visualization_commands(runtime, root, "QaRelationship", graph_args),
            output_root,
            timeout,
        )
        elapsed[runtime.id] = round(validate.elapsed_seconds + refresh.elapsed_seconds + unbounded.elapsed_seconds, 3)
        refresh_roots[runtime.id] = runtime_root / "refresh"
        unbounded_paths[runtime.id] = graph_path
    if len(set(validate_outputs.values())) != 1:
        raise CompatibilityFailure("Visualization Validate output differs across runtimes.")
    refresh_comparison = compare_trees(refresh_roots)
    unbounded_values = {
        runtime: normalized_file(path, list(unbounded_paths.values())) for runtime, path in unbounded_paths.items()
    }
    if len(set(unbounded_values.values())) != 1:
        raise CompatibilityFailure("Unbounded Visualization Mermaid output differs across runtimes.")
    match = re.search(r"Source parse: nodes=(\d+) relationships=(\d+)", next(iter(validate_outputs.values())))
    semantic_summary = {
        "nodes": int(match.group(1)) if match else None,
        "relationships": int(match.group(2)) if match else None,
    }
    assert_semantic_baseline("Visualization", semantic_summary, baseline.get("semantic_summary"))
    refresh_output_roots = list(refresh_roots.values())
    refresh_manifest = normalized_tree_manifest(refresh_roots["python"], refresh_output_roots)
    refresh_tree_sha256 = assert_tree_baseline(
        "Visualization refresh",
        refresh_manifest,
        baseline.get("refresh_files"),
        baseline.get("refresh_tree_sha256"),
    )
    unbounded_sha256 = normalized_file_sha256(unbounded_paths["python"], list(unbounded_paths.values()))
    expected_unbounded_sha256 = baseline.get("unbounded_relationship_sha256")
    if unbounded_sha256 != expected_unbounded_sha256:
        raise CompatibilityFailure(
            "Visualization unbounded relationship baseline changed: "
            f"expected {expected_unbounded_sha256}, actual {unbounded_sha256}"
        )
    return {
        "status": "passed",
        **semantic_summary,
        "refresh": refresh_comparison,
        "refresh_tree_sha256": refresh_tree_sha256,
        "unbounded_graph_match": True,
        "unbounded_relationship_sha256": unbounded_sha256,
        "elapsed_seconds": elapsed,
    }


def qa_command(
    runtime: Runtime,
    root: Path,
    output_dir: Path,
    bounded_graphs: list[str],
    bounded_pages: list[str],
) -> list[str]:
    python_args = ["--clean", "--output-dir", str(output_dir), "--json"]
    powershell_args = ["-Clean", "-OutputDir", str(output_dir), "-Json"]
    for spec in bounded_graphs:
        python_args.extend(["--bounded-graph", spec])
    if bounded_graphs:
        powershell_args.extend(["-BoundedGraph", ";".join(bounded_graphs)])
    for spec in bounded_pages:
        python_args.extend(["--bounded-page", spec])
    if bounded_pages:
        powershell_args.extend(["-BoundedPage", ";".join(bounded_pages)])
    return python_or_powershell_command(
        runtime,
        root / "Tools" / "Commands" / "QA" / "obsidian_qa_export.py",
        root / "Tools" / "Commands" / "QA" / "Obsidian-QA-Export.ps1",
        python_args,
        powershell_args,
    )


def run_qa_check(check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path) -> dict[str, Any]:
    baseline = load_consumer_baseline(check, root, "qa")
    roots = {runtime.id: output_root / runtime.id for runtime in runtimes}
    summaries: dict[str, Any] = {}
    elapsed: dict[str, float] = {}
    for runtime in runtimes:
        result = run_command(
            runtime,
            qa_command(
                runtime,
                root,
                roots[runtime.id],
                check.get("bounded_graphs", []),
                check.get("bounded_pages", []),
            ),
            output_root,
            check["timeout_seconds"],
        )
        summary = parse_json_output(result.stdout)
        summary.pop("output_dir", None)
        summaries[runtime.id] = summary
        elapsed[runtime.id] = result.elapsed_seconds
    canonical = {runtime: json.dumps(value, sort_keys=True) for runtime, value in summaries.items()}
    if len(set(canonical.values())) != 1:
        raise CompatibilityFailure(f"QA structured summaries differ: {summaries}")
    comparison = compare_trees(roots)
    semantic_summary = summaries["python"]
    assert_semantic_baseline("QA", semantic_summary, baseline.get("semantic_summary"))
    output_roots = list(roots.values())
    file_manifest = normalized_tree_manifest(roots["python"], output_roots)
    tree_sha256 = assert_tree_baseline(
        "QA export",
        file_manifest,
        baseline.get("files"),
        baseline.get("tree_sha256"),
    )
    return {
        "status": "passed",
        "summary": semantic_summary,
        "files": comparison,
        "tree_sha256": tree_sha256,
        "elapsed_seconds": elapsed,
    }


def root_suite_command(runtime: Runtime, root: Path) -> list[str]:
    return python_or_powershell_command(
        runtime,
        root / "Tools" / "Conformance" / "Suites" / "test_project_paths.py",
        root / "Tools" / "Conformance" / "Suites" / "Test-Project-Paths.ps1",
        ["--json"],
        ["-Json"],
    )


def compatibility_child_command(
    root: Path,
    registry_path: Path,
    output_root: Path,
    *,
    check_id: str | None = None,
    profile: str | None = None,
    output_mode: str | None = None,
    report_output: Path | None = None,
    keep_output: bool = False,
) -> list[str]:
    command = [
        sys.executable,
        str(root / "Tools" / "Compatibility" / "run_compatibility.py"),
        "--root",
        str(root),
        "--registry",
        str(registry_path),
        "--output-root",
        str(output_root),
    ]
    if check_id is not None:
        command.extend(["--check", check_id])
    elif profile is not None:
        command.extend(["--profile", profile])
    if output_mode == "detailed":
        command.append("--json")
    elif output_mode == "concise":
        command.append("--summary-json")
    if report_output is not None:
        command.extend(["--report-output", str(report_output)])
    if keep_output:
        command.append("--keep-output")
    return command


def create_compatibility_reporting_registry(root: Path, destination: Path) -> Path:
    registry_path = destination / "reporting-registry.json"
    registry = {
        "schema_version": 2,
        "runtimes": ["python", "powershell7", "powershell51"],
        "profiles": {
            "reporting": ["reporting-root-discovery"],
            "failing": ["reporting-failing-render"],
        },
        "checks": [
            {
                "id": "reporting-root-discovery",
                "kind": "root-discovery",
                "timeout_seconds": 30,
                "launch_locations": ["repo-root", "tools", "nested", "unrelated"],
            },
            {
                "id": "reporting-failing-render",
                "kind": "render",
                "timeout_seconds": 30,
                "input": ".tmp/compatibility-reporting-missing-input.mmd",
                "output_format": "svg",
                "minimum_bytes": 1,
                "required_labels": ["never-rendered"],
            },
        ],
    }
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8", newline="\n")
    return registry_path


def validate_concise_compatibility_summary(document: Any, *, expected_status: str) -> None:
    if not isinstance(document, dict):
        raise CompatibilityFailure("Compatibility concise output must be a JSON object.")
    expected_fields = [
        "contract",
        "contract_version",
        "runner",
        "status",
        "profile",
        "requested_ids",
        "selected_count",
        "passed",
        "failed",
        "elapsed_seconds",
        "canonical_outputs_unchanged",
        "output_kept",
        "report_path",
        "results",
        "failures",
    ]
    if list(document) != expected_fields:
        raise CompatibilityFailure(f"Compatibility concise fields differ: {sorted(document)}")
    if (
        document["contract"] != "validation-run-summary"
        or document["contract_version"] != 1
        or document["runner"] != "project-compatibility"
        or document["status"] != expected_status
    ):
        raise CompatibilityFailure(f"Invalid compatibility concise identity/status: {document}")
    if document["elapsed_seconds"] is not None and (
        not isinstance(document["elapsed_seconds"], (int, float)) or document["elapsed_seconds"] < 0
    ):
        raise CompatibilityFailure("Compatibility concise elapsed_seconds must be null or nonnegative.")
    if not isinstance(document["output_kept"], bool):
        raise CompatibilityFailure("Compatibility concise output_kept must be boolean.")
    if len(document["requested_ids"]) != document["selected_count"]:
        raise CompatibilityFailure("Compatibility concise selection counts are inconsistent.")
    for result in document["results"]:
        if set(result) != {"id", "kind", "status"}:
            raise CompatibilityFailure(f"Invalid concise compatibility result row: {result}")


def normalized_compatibility_summary(document: dict[str, Any]) -> str:
    normalized = copy.deepcopy(document)
    normalized["elapsed_seconds"] = 0
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def run_compatibility_reporting_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    del runtimes
    registry_path = create_compatibility_reporting_registry(root, output_root)
    report_root = output_root / "reports"
    help_result = run_command(
        Runtime("python", sys.executable),
        [sys.executable, str(root / "Tools" / "Compatibility" / "run_compatibility.py"), "--help"],
        root,
        check["timeout_seconds"],
    )
    if any(token not in help_result.stdout for token in ("--summary-json", "--report-output")):
        raise CompatibilityFailure("Compatibility help lacks reporting switches.")

    detailed_output = output_root / "runs" / "detailed"
    detailed_report = report_root / "detailed.json"
    detailed_result = run_command(
        Runtime("python", sys.executable),
        compatibility_child_command(
            root,
            registry_path,
            detailed_output,
            check_id="reporting-root-discovery",
            output_mode="detailed",
            report_output=detailed_report,
        ),
        root,
        check["timeout_seconds"],
    )
    detailed_document = parse_json_output(detailed_result.stdout)
    expected_detailed_fields = {
        "schema_version",
        "profile",
        "requested_checks",
        "status",
        "passed",
        "failed",
        "elapsed_seconds",
        "canonical_outputs_unchanged",
        "output_root",
        "output_kept",
        "checks",
    }
    if set(detailed_document) != expected_detailed_fields or detailed_document["status"] != "passed":
        raise CompatibilityFailure("Detailed compatibility output changed shape or failed.")
    if detailed_report.read_bytes() != detailed_result.stdout.encode("utf-8"):
        raise CompatibilityFailure("Detailed compatibility report differs from detailed stdout bytes.")
    if detailed_output.exists():
        raise CompatibilityFailure("Successful focused compatibility output was not cleaned.")

    concise_report = report_root / "concise.json"
    concise_documents = []
    for index in range(2):
        run_root = output_root / "runs" / f"concise-{index + 1}"
        concise_result = run_command(
            Runtime("python", sys.executable),
            compatibility_child_command(
                root,
                registry_path,
                run_root,
                profile="reporting",
                output_mode="concise",
                report_output=concise_report,
            ),
            root,
            check["timeout_seconds"],
        )
        document = parse_json_output(concise_result.stdout)
        validate_concise_compatibility_summary(document, expected_status="passed")
        if (
            document["profile"] != "reporting"
            or document["requested_ids"] != ["reporting-root-discovery"]
            or document["output_kept"] is not False
            or not document["report_path"]
            or run_root.exists()
        ):
            raise CompatibilityFailure("Compatibility concise profile/report cleanup semantics differ.")
        concise_documents.append(document)
    if len({normalized_compatibility_summary(document) for document in concise_documents}) != 1:
        raise CompatibilityFailure("Compatibility concise output is nondeterministic.")
    concise_detail = parse_json_output(concise_report.read_text(encoding="utf-8"))
    if (
        concise_detail["status"] != "passed"
        or len(concise_detail["checks"]) != 1
        or concise_documents[-1]["output_kept"] != concise_detail["output_kept"]
    ):
        raise CompatibilityFailure("Compatibility concise detailed report is incomplete.")

    unsafe_report = root.parent / f"compatibility-reporting-unsafe-{os.getpid()}.json"
    unsafe_output = output_root / "runs" / "unsafe"
    if unsafe_report.exists():
        raise CompatibilityFailure(f"Unsafe compatibility probe already exists: {unsafe_report}")
    unsafe_result = run_command(
        Runtime("python", sys.executable),
        compatibility_child_command(
            root,
            registry_path,
            unsafe_output,
            profile="reporting",
            output_mode="concise",
            report_output=unsafe_report,
        ),
        root,
        check["timeout_seconds"],
        expect_success=False,
    )
    unsafe_document = parse_json_output(unsafe_result.stdout)
    validate_concise_compatibility_summary(unsafe_document, expected_status="failed")
    if (
        unsafe_document["failures"][0].get("classification") != "orchestration-failure"
        or unsafe_report.exists()
        or unsafe_output.exists()
    ):
        raise CompatibilityFailure("Unsafe compatibility report path was not rejected before execution.")

    failure_output = output_root / "runs" / "failure"
    failure_result = run_command(
        Runtime("python", sys.executable),
        compatibility_child_command(
            root,
            registry_path,
            failure_output,
            check_id="reporting-failing-render",
            output_mode="concise",
        ),
        root,
        check["timeout_seconds"],
        expect_success=False,
    )
    failure_document = parse_json_output(failure_result.stdout)
    validate_concise_compatibility_summary(failure_document, expected_status="failed")
    if (
        failure_document["failures"][0].get("classification") != "check-failure"
        or failure_document["failures"][0].get("id") != "reporting-failing-render"
        or not failure_document["output_kept"]
        or not failure_document["report_path"]
    ):
        raise CompatibilityFailure("Failed compatibility reporting envelope lacks retained diagnostics.")
    retained_report = root / failure_document["report_path"]
    if not retained_report.is_file() or failure_output not in retained_report.parents:
        raise CompatibilityFailure("Failed compatibility detailed report was not retained with scoped output.")
    retained_detail = parse_json_output(retained_report.read_text(encoding="utf-8"))
    if (
        retained_detail["status"] != "failed"
        or not retained_detail.get("error")
        or failure_document["output_kept"] != retained_detail["output_kept"]
    ):
        raise CompatibilityFailure("Failed compatibility detailed report lacks complete diagnostics.")

    human_failure_output = output_root / "runs" / "human-failure"
    human_failure_result = run_command(
        Runtime("python", sys.executable),
        compatibility_child_command(
            root,
            registry_path,
            human_failure_output,
            check_id="reporting-failing-render",
        ),
        root,
        check["timeout_seconds"],
        expect_success=False,
    )
    if (
        "Output retained:" not in human_failure_result.stderr
        or "Detailed report:" not in human_failure_result.stderr
        or not (human_failure_output / "report.json").is_file()
    ):
        raise CompatibilityFailure("Human compatibility failure did not identify retained diagnostics.")

    long_error = "\n".join(f"synthetic compatibility failure line {index:02d}" for index in range(1, 31))
    excerpt, truncated = bounded_failure_excerpt(long_error)
    if not truncated or len(excerpt.splitlines()) > 20 or len(excerpt.encode("utf-8")) > 4096:
        raise CompatibilityFailure("Compatibility failure excerpt violates the reporting budget.")

    return {
        "status": "passed",
        "contract": "validation-run-summary",
        "contract_version": 1,
        "focused_cases": 1,
        "profile_cases": 2,
        "determinism_cases": 2,
        "failure_cases": 2,
        "unsafe_report_path_cases": 1,
        "cleanup_cases": 3,
        "detailed_bytes": len(detailed_result.stdout.encode("utf-8")),
        "concise_bytes": len(json.dumps(concise_documents[-1], separators=(",", ":")).encode("utf-8")),
        "elapsed_seconds": round(
            detailed_result.elapsed_seconds + sum(document["elapsed_seconds"] for document in concise_documents),
            3,
        ),
    }


def aggregate_conformance_command(
    runtime: Runtime,
    project_root: Path,
    *,
    suite_id: str,
    output_mode: str | None = None,
    report_output: Path | None = None,
) -> list[str]:
    python_args = ["--root", str(project_root), "--suite", suite_id]
    powershell_args = ["-Root", str(project_root), "-Suite", suite_id]
    if output_mode == "detailed":
        python_args.append("--json")
        powershell_args.append("-Json")
    elif output_mode == "concise":
        python_args.append("--summary-json")
        powershell_args.append("-SummaryJson")
    if report_output is not None:
        python_args.extend(["--report-output", str(report_output)])
        powershell_args.extend(["-ReportOutput", str(report_output)])
    return python_or_powershell_command(
        runtime,
        project_root / "Tools" / "Conformance" / "run_conformance.py",
        project_root / "Tools" / "Conformance" / "Run-Conformance.ps1",
        python_args,
        powershell_args,
    )


def powershell_conformance_parameter_command(runtime: Runtime, root: Path) -> list[str]:
    script_path = str(root / "Tools" / "Conformance" / "Run-Conformance.ps1").replace("'", "''")
    expression = f"(Get-Command '{script_path}').Parameters.Keys | Sort-Object"
    return [*powershell_prefix(runtime), "-Command", expression]


def create_failing_conformance_project(root: Path, destination: Path) -> Path:
    project_root = destination / "failing-project"
    (project_root / "Project_Config").mkdir(parents=True)
    (project_root / "Project_Config" / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    shutil.copytree(root / "Tools" / "Runtime", project_root / "Tools" / "Runtime")
    conformance_root = project_root / "Tools" / "Conformance"
    fixture_root = conformance_root / "Fixtures"
    fixture_root.mkdir(parents=True)
    shutil.copy2(root / "Tools" / "Conformance" / "run_conformance.py", conformance_root)
    shutil.copy2(root / "Tools" / "Conformance" / "Run-Conformance.ps1", conformance_root)
    (fixture_root / "fail_suite.py").write_text(
        """import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--root")
parser.add_argument("--json", action="store_true")
parser.parse_args()
print("\\n".join(f"synthetic failure line {index:02d}" for index in range(1, 31)), file=sys.stderr)
raise SystemExit(7)
""",
        encoding="utf-8",
        newline="\n",
    )
    (fixture_root / "Fail-Suite.ps1").write_text(
        """param(
    [string]$Root,
    [switch]$Json
)
1..30 | ForEach-Object {
    Write-Output "synthetic failure line $($_.ToString('00'))"
}
exit 7
""",
        encoding="utf-8",
        newline="\n",
    )
    registry = {
        "schema_version": 1,
        "profiles": {"fast": ["fixture-failure"], "baseline": ["fixture-failure"]},
        "suites": [
            {
                "id": "fixture-failure",
                "python": "Tools/Conformance/Fixtures/fail_suite.py",
                "powershell": "Tools/Conformance/Fixtures/Fail-Suite.ps1",
                "tags": ["fixture"],
            }
        ],
        "discovery": {
            "python": [
                {
                    "directory": "Tools/Conformance/Fixtures",
                    "pattern": "*_suite.py",
                    "exclude": [],
                }
            ],
            "powershell": [
                {
                    "directory": "Tools/Conformance/Fixtures",
                    "pattern": "*-Suite.ps1",
                    "exclude": [],
                }
            ],
        },
    }
    (conformance_root / "suites.json").write_text(
        json.dumps(registry, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project_root


def validate_concise_conformance_summary(document: Any, *, expected_status: str) -> None:
    if not isinstance(document, dict):
        raise CompatibilityFailure("Conformance concise output must be a JSON object.")
    expected_fields = [
        "contract",
        "contract_version",
        "runner",
        "status",
        "profile",
        "requested_ids",
        "selected_count",
        "passed",
        "failed",
        "elapsed_seconds",
        "canonical_outputs_unchanged",
        "output_kept",
        "report_path",
        "results",
        "failures",
    ]
    if list(document) != expected_fields:
        raise CompatibilityFailure(f"Conformance concise fields differ: {sorted(document)}")
    if (
        document["contract"] != "validation-run-summary"
        or document["contract_version"] != 1
        or document["runner"] != "framework-conformance"
        or document["status"] != expected_status
        or document["canonical_outputs_unchanged"] is not None
        or document["output_kept"] is not None
    ):
        raise CompatibilityFailure(f"Invalid conformance concise identity/status: {document}")
    if document["elapsed_seconds"] is not None and (
        not isinstance(document["elapsed_seconds"], (int, float)) or document["elapsed_seconds"] < 0
    ):
        raise CompatibilityFailure("Conformance concise elapsed_seconds must be null or nonnegative.")
    if (
        len(document["requested_ids"]) != document["selected_count"]
        or len(document["results"]) != document["selected_count"]
    ):
        raise CompatibilityFailure("Conformance concise selection counts are inconsistent.")
    for result in document["results"]:
        if set(result) != {"id", "kind", "status"} or result["kind"] is not None:
            raise CompatibilityFailure(f"Invalid concise conformance result row: {result}")
        if "summary" in result:
            raise CompatibilityFailure("Concise conformance output leaked a nested suite summary.")


def normalized_concise_summary(document: dict[str, Any]) -> str:
    normalized = copy.deepcopy(document)
    normalized["elapsed_seconds"] = 0
    normalized["report_path"] = "REPORT" if normalized["report_path"] is not None else None
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def run_conformance_reporting_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    failing_root = create_failing_conformance_project(root, output_root)
    detailed_documents: dict[str, Any] = {}
    concise_documents: dict[str, Any] = {}
    report_bytes: dict[str, bytes] = {}
    concise_sizes: dict[str, int] = {}
    detailed_sizes: dict[str, int] = {}
    elapsed: dict[str, float] = {}
    failure_report_sizes: dict[str, int] = {}

    for runtime in runtimes:
        help_command = (
            [runtime.executable, str(root / "Tools" / "Conformance" / "run_conformance.py"), "--help"]
            if runtime.id == "python"
            else powershell_conformance_parameter_command(runtime, root)
        )
        help_result = run_command(runtime, help_command, root, check["timeout_seconds"])
        help_text = help_result.stdout + help_result.stderr
        required_help = (
            ["--summary-json", "--report-output"] if runtime.id == "python" else ["SummaryJson", "ReportOutput"]
        )
        if any(token not in help_text for token in required_help):
            raise CompatibilityFailure(f"{runtime.id} conformance help lacks reporting switches.")

        detailed_result = run_command(
            runtime,
            aggregate_conformance_command(runtime, root, suite_id="project-root", output_mode="detailed"),
            root,
            check["timeout_seconds"],
        )
        detailed_document = parse_json_output(detailed_result.stdout)
        detailed_documents[runtime.id] = detailed_document
        detailed_sizes[runtime.id] = len(detailed_result.stdout.encode("utf-8"))

        report_path = output_root / runtime.id / "success-report.json"
        concise_result = run_command(
            runtime,
            aggregate_conformance_command(
                runtime,
                root,
                suite_id="project-root",
                output_mode="concise",
                report_output=report_path,
            ),
            root,
            check["timeout_seconds"],
        )
        concise_document = parse_json_output(concise_result.stdout)
        validate_concise_conformance_summary(concise_document, expected_status="passed")
        if concise_document["output_kept"] is not None or not concise_document["report_path"]:
            raise CompatibilityFailure(f"{runtime.id} did not expose its explicit detailed report.")
        concise_documents[runtime.id] = concise_document
        concise_sizes[runtime.id] = len(concise_result.stdout.encode("utf-8"))
        elapsed[runtime.id] = round(detailed_result.elapsed_seconds + concise_result.elapsed_seconds, 3)
        report_bytes[runtime.id] = report_path.read_bytes()
        if parse_json_output(report_bytes[runtime.id].decode("utf-8")) != detailed_document:
            raise CompatibilityFailure(f"{runtime.id} detailed report differs from detailed stdout semantics.")

        deterministic_results = []
        for _ in range(2):
            result = run_command(
                runtime,
                aggregate_conformance_command(runtime, root, suite_id="project-root", output_mode="concise"),
                root,
                check["timeout_seconds"],
            )
            document = parse_json_output(result.stdout)
            validate_concise_conformance_summary(document, expected_status="passed")
            deterministic_results.append(normalized_concise_summary(document))
        if len(set(deterministic_results)) != 1:
            raise CompatibilityFailure(f"{runtime.id} concise conformance output is nondeterministic.")

        outside_report = root.parent / f"validation-reporting-unsafe-{os.getpid()}-{runtime.id}.json"
        if outside_report.exists():
            raise CompatibilityFailure(f"Unsafe conformance probe already exists: {outside_report}")
        unsafe_result = run_command(
            runtime,
            aggregate_conformance_command(
                runtime,
                root,
                suite_id="project-root",
                output_mode="concise",
                report_output=outside_report,
            ),
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        unsafe_document = parse_json_output(unsafe_result.stdout)
        validate_concise_conformance_summary(unsafe_document, expected_status="failed")
        if (
            outside_report.exists()
            or "RUN:" in unsafe_result.stdout
            or unsafe_document["failures"][0].get("classification") != "orchestration-failure"
        ):
            raise CompatibilityFailure(f"{runtime.id} unsafe report validation occurred after suite execution.")

        failure_result = run_command(
            runtime,
            aggregate_conformance_command(
                runtime,
                failing_root,
                suite_id="fixture-failure",
                output_mode="concise",
            ),
            failing_root,
            check["timeout_seconds"],
            expect_success=False,
        )
        failure_document = parse_json_output(failure_result.stdout)
        validate_concise_conformance_summary(failure_document, expected_status="failed")
        if failure_document["output_kept"] is not None or not failure_document["report_path"]:
            raise CompatibilityFailure(f"{runtime.id} failed conformance did not retain its detailed report.")
        failure_row = failure_document["failures"][0]
        if (
            failure_row.get("classification") != "suite-failure"
            or not failure_row.get("excerpt_truncated")
            or len(failure_row.get("excerpt", "").splitlines()) > 20
            or len(failure_row.get("excerpt", "").encode("utf-8")) > 4096
        ):
            raise CompatibilityFailure(f"{runtime.id} failure excerpt violates the reporting budget.")
        failure_report = (failing_root / failure_document["report_path"]).resolve()
        if failing_root not in failure_report.parents or not failure_report.is_file():
            raise CompatibilityFailure(f"{runtime.id} retained failure report is missing or unsafe.")
        failure_detail = parse_json_output(failure_report.read_text(encoding="utf-8"))
        if "synthetic failure line 30" not in failure_detail["suites"][0]["error"]:
            raise CompatibilityFailure(f"{runtime.id} retained failure report truncated full diagnostics.")
        failure_report_sizes[runtime.id] = failure_report.stat().st_size

    reference_runtime = runtimes[0].id
    if len({json.dumps(value, sort_keys=True) for value in detailed_documents.values()}) != 1:
        raise CompatibilityFailure("Detailed conformance JSON differs across runtimes.")
    if len({normalized_concise_summary(value) for value in concise_documents.values()}) != 1:
        raise CompatibilityFailure("Concise conformance summaries differ across runtimes.")
    if len(set(report_bytes.values())) != 1:
        raise CompatibilityFailure("Detailed conformance report bytes differ across runtimes.")

    return {
        "status": "passed",
        "contract": "validation-run-summary",
        "contract_version": 1,
        "runtimes": [runtime.id for runtime in runtimes],
        "success_cases": 3,
        "determinism_cases": 6,
        "failure_cases": 3,
        "unsafe_report_path_cases": 3,
        "detailed_bytes": detailed_sizes[reference_runtime],
        "concise_bytes": concise_sizes,
        "report_bytes": len(report_bytes[reference_runtime]),
        "report_sha256": hashlib.sha256(report_bytes[reference_runtime]).hexdigest(),
        "failure_report_bytes": failure_report_sizes,
        "elapsed_seconds": elapsed,
    }


def run_root_discovery_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    locations = {
        "repo-root": root,
        "tools": root / "Tools",
        "nested": root / "Framework" / "Contracts",
        "unrelated": output_root.parent,
    }
    selected = check.get("launch_locations", [])
    results: list[dict[str, Any]] = []
    canonical: set[str] = set()
    for runtime in runtimes:
        for location in selected:
            result = run_command(
                runtime,
                root_suite_command(runtime, root),
                locations[location],
                check["timeout_seconds"],
            )
            summary = parse_json_output(result.stdout)
            canonical.add(json.dumps(summary, sort_keys=True))
            results.append(
                {
                    "runtime": runtime.id,
                    "location": location,
                    "elapsed_seconds": result.elapsed_seconds,
                }
            )
    if len(canonical) != 1:
        raise CompatibilityFailure("Project-root summaries differ across runtimes or launch locations.")
    return {"status": "passed", "launch_count": len(results), "launches": results}


def cleanup_command(runtime: Runtime, root: Path, tmp_path: Path, delete: bool) -> list[str]:
    relative = tmp_path.relative_to(root).as_posix()
    python_args = ["--tmp-path", relative, "--json"]
    powershell_args = ["-TmpPath", relative, "-Json"]
    if delete:
        python_args.append("--delete")
        powershell_args.append("-Delete")
    return python_or_powershell_command(
        runtime,
        root / "Tools" / "Commands" / "Maintenance" / "clean_temp_files.py",
        root / "Tools" / "Commands" / "Maintenance" / "Clean-TempFiles.ps1",
        python_args,
        powershell_args,
    )


def unsafe_qa_command(runtime: Runtime, root: Path, destination: str) -> list[str]:
    return python_or_powershell_command(
        runtime,
        root / "Tools" / "Commands" / "QA" / "obsidian_qa_export.py",
        root / "Tools" / "Commands" / "QA" / "Obsidian-QA-Export.ps1",
        ["--output-dir", destination, "--json"],
        ["-OutputDir", destination, "-Json"],
    )


def run_artifact_lifecycle_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    lifecycle_root = output_root / "owned" / "deep" / "qa"
    sentinel = output_root / "preserve-me.txt"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("preserve", encoding="utf-8")
    python = runtimes[0]
    run_command(
        python,
        qa_command(
            python,
            root,
            lifecycle_root,
            ["name=chapter-32,medium=novel,maxVolume=1,maxChapter=32"],
            ["slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=32"],
        ),
        output_root,
        check["timeout_seconds"],
    )
    stale = lifecycle_root / "_Generated" / "bounded-pages" / "stale.txt"
    stale.write_text("stale", encoding="utf-8")
    run_command(
        python,
        qa_command(python, root, lifecycle_root, [], []),
        output_root,
        check["timeout_seconds"],
    )
    stale_removed = not stale.exists()
    optional_folders_absent = (
        not (lifecycle_root / "_Generated" / "bounded-pages").exists()
        and not (lifecycle_root / "_Generated" / "bounded-graphs").exists()
    )
    rejected = 0
    for runtime in runtimes:
        for destination in (".", "../compatibility-output-escape"):
            run_command(
                runtime,
                unsafe_qa_command(runtime, root, destination),
                root,
                check["timeout_seconds"],
                expect_success=False,
            )
            rejected += 1
    dry_summaries: dict[str, Any] = {}
    for runtime in runtimes:
        result = run_command(
            runtime,
            cleanup_command(runtime, root, lifecycle_root, False),
            output_root,
            check["timeout_seconds"],
        )
        summary = parse_json_output(result.stdout)
        dry_summaries[runtime.id] = {
            "delete": summary["delete"],
            "scoped_tmp_count": summary["scoped_tmp_count"],
            "target_status": summary["results"][-1]["status"],
        }
    if len({json.dumps(value, sort_keys=True) for value in dry_summaries.values()}) != 1:
        raise CompatibilityFailure(f"Cleanup dry-run summaries differ: {dry_summaries}")
    run_command(
        python,
        cleanup_command(python, root, lifecycle_root, True),
        output_root,
        check["timeout_seconds"],
    )
    scoped_removed = not lifecycle_root.exists()
    sentinel_preserved = sentinel.exists()
    if not all((stale_removed, optional_folders_absent, scoped_removed, sentinel_preserved)):
        raise CompatibilityFailure("Artifact lifecycle cleanup or preservation invariant failed.")
    return {
        "status": "passed",
        "stale_removed": stale_removed,
        "optional_folders_absent": optional_folders_absent,
        "unsafe_destinations_rejected": rejected,
        "cleanup_dry_run_match": True,
        "scoped_removed": scoped_removed,
        "unrelated_preserved": sentinel_preserved,
    }


def run_render_check(check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path) -> dict[str, Any]:
    source = root / check["input"]
    records: list[dict[str, Any]] = []
    dimensions: set[tuple[str | None, str | None, str | None]] = set()
    for runtime in runtimes:
        destination = output_root / runtime.id / f"representative.{check['output_format']}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        args = (
            ["--input-path", str(source), "--output-path", str(destination)]
            if runtime.id == "python"
            else ["-InputPath", str(source), "-OutputPath", str(destination)]
        )
        result = run_command(
            runtime,
            visualization_commands(runtime, root, "Render", args),
            output_root,
            check["timeout_seconds"],
        )
        data = destination.read_bytes()
        text = data.decode("utf-8", errors="replace")
        if len(data) < check["minimum_bytes"] or "<svg" not in text:
            raise CompatibilityFailure(f"Rendered output is missing or blank for {runtime.id}: {destination}")
        missing_labels = [label for label in check.get("required_labels", []) if label not in text]
        if missing_labels:
            raise CompatibilityFailure(f"Rendered output for {runtime.id} lacks labels: {missing_labels}")
        width = re.search(r'<svg[^>]*\bwidth="([^"]+)"', text)
        height = re.search(r'<svg[^>]*\bheight="([^"]+)"', text)
        view_box = re.search(r'<svg[^>]*\bviewBox="([^"]+)"', text)
        dimension = (
            width.group(1) if width else None,
            height.group(1) if height else None,
            view_box.group(1) if view_box else None,
        )
        dimensions.add(dimension)
        records.append(
            {
                "runtime": runtime.id,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "dimensions": dimension,
                "elapsed_seconds": result.elapsed_seconds,
            }
        )
    if len(dimensions) != 1:
        raise CompatibilityFailure(f"Rendered dimensions differ across runtimes: {records}")
    return {
        "status": "passed",
        "outputs": records,
        "hash_match": len({record["sha256"] for record in records}) == 1,
        "nonblank": True,
        "semantic_dimensions_match": True,
    }


def run_framework_extraction_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    del output_root
    python_runtime = next(runtime for runtime in runtimes if runtime.id == "python")
    result = run_command(
        python_runtime,
        [
            python_runtime.executable,
            str(root / "Tools" / "Compatibility" / "verify_framework_extraction.py"),
            "--root",
            str(root),
            "--json",
        ],
        root,
        check["timeout_seconds"],
    )
    summary = parse_json_output(result.stdout)
    if not isinstance(summary, dict) or summary.get("status") != "passed":
        raise CompatibilityFailure(f"Framework extraction rehearsal returned an invalid summary: {summary!r}")
    return {
        "status": "passed",
        "copied_files": summary.get("copied_files"),
        "copied_project_config": summary.get("copied_project_config"),
        "forbidden_surfaces_absent": summary.get("forbidden_surfaces_absent"),
        "neutral_project_id": summary.get("neutral_project_id"),
        "portable_suites": summary.get("portable_suites"),
        "runtimes": summary.get("runtimes"),
        "elapsed_seconds": result.elapsed_seconds,
    }


def run_framework_catalog_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    python_script = root / "Tools" / "Commands" / "Framework" / "inspect_framework_catalog.py"
    powershell_script = root / "Tools" / "Commands" / "Framework" / "Get-FrameworkCatalog.ps1"
    documents: dict[str, dict[str, Any]] = {}
    export_bytes: dict[str, bytes] = {}
    report_export_bytes: dict[str, bytes] = {}
    selection_documents: dict[str, dict[str, Any]] = {}
    selection_export_bytes: dict[str, bytes] = {}
    project_view_documents: dict[str, dict[str, Any]] = {}
    project_view_export_bytes: dict[str, bytes] = {}
    project_view_reports: dict[str, str] = {}
    project_view_report_bytes: dict[str, bytes] = {}
    project_view_selections: dict[str, dict[str, Any]] = {}
    project_attachment_failures: dict[str, str] = {}
    human_reports: dict[str, dict[str, str]] = {}
    failure_classifications: dict[str, str] = {}
    invalid_show_failures: dict[str, str] = {}
    singular_selection_failures: dict[str, str] = {}
    unsafe_report_failures: dict[str, str] = {}
    elapsed: dict[str, float] = {}

    for runtime in runtimes:
        command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--json"],
            ["-Root", str(root), "-Json"],
        )
        result = run_command(runtime, command, root, check["timeout_seconds"])
        document = parse_json_output(result.stdout)
        if not isinstance(document, dict) or document.get("contract") != "framework-catalog":
            raise CompatibilityFailure(f"{runtime.id} returned an invalid framework catalog: {document!r}")
        documents[runtime.id] = document
        elapsed[runtime.id] = result.elapsed_seconds

        human_reports[runtime.id] = {}
        human_cases = {
            "overview": (
                ["--root", str(root), "--show", "overview"],
                ["-Root", str(root), "-Show", "overview"],
            ),
            "combined": (
                ["--root", str(root), "--show", "packs", "--show", "capabilities"],
                ["-Root", str(root), "-Show", "packs,capabilities"],
            ),
            "all-deduplicated": (
                ["--root", str(root), "--show", "packs", "--show", "all", "--show", "packs"],
                ["-Root", str(root), "-Show", "packs,all,packs"],
            ),
        }
        for case_id, (python_args, powershell_args) in human_cases.items():
            human_command = python_or_powershell_command(
                runtime,
                python_script,
                powershell_script,
                python_args,
                powershell_args,
            )
            human_result = run_command(runtime, human_command, root, check["timeout_seconds"])
            human_reports[runtime.id][case_id] = human_result.stdout.replace("\r\n", "\n")

        report_export_path = output_root / f"{runtime.id}.txt"
        report_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--show",
                "packs",
                "--show",
                "all",
                "--show",
                "packs",
                "--report-output",
                str(report_export_path),
            ],
            [
                "-Root",
                str(root),
                "-Show",
                "packs,all,packs",
                "-ReportOutput",
                str(report_export_path),
            ],
        )
        report_result = run_command(runtime, report_export_command, root, check["timeout_seconds"])
        expected_confirmation = f"Exported report: {report_export_path.relative_to(root).as_posix()}\n"
        if report_result.stdout.replace("\r\n", "\n") != expected_confirmation:
            raise CompatibilityFailure(f"{runtime.id} returned an invalid framework-catalog report confirmation.")
        report_export_bytes[runtime.id] = report_export_path.read_bytes()
        if report_export_bytes[runtime.id].decode("utf-8") != human_reports[runtime.id]["all-deduplicated"]:
            raise CompatibilityFailure(f"{runtime.id} framework-catalog report export differs from human output.")

        export_path = output_root / f"{runtime.id}.json"
        export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--output", str(export_path)],
            ["-Root", str(root), "-Output", str(export_path)],
        )
        run_command(runtime, export_command, root, check["timeout_seconds"])
        exported = json.loads(export_path.read_text(encoding="utf-8-sig"))
        if exported != document:
            raise CompatibilityFailure(f"{runtime.id} framework-catalog export differs from JSON output.")
        export_bytes[runtime.id] = export_path.read_bytes()

        selection_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--pack",
                "Narrative-Media",
                "--capability",
                "Narrative-Time-Loops",
                "--json",
            ],
            [
                "-Root",
                str(root),
                "-Pack",
                "Narrative-Media",
                "-Capability",
                "Narrative-Time-Loops",
                "-Json",
            ],
        )
        selection_result = run_command(runtime, selection_command, root, check["timeout_seconds"])
        selection = parse_json_output(selection_result.stdout)
        if (
            not isinstance(selection, dict)
            or selection.get("contract") != "framework-catalog-selection"
            or [row.get("id") for row in selection.get("packs", [])] != ["narrative-media"]
            or [row.get("id") for row in selection.get("capabilities", [])] != ["narrative-time-loops"]
        ):
            raise CompatibilityFailure(f"{runtime.id} returned an invalid catalog selection: {selection!r}")
        selection_documents[runtime.id] = selection

        selection_export_path = output_root / f"{runtime.id}-selection.json"
        selection_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--pack",
                "Narrative-Media",
                "--capability",
                "Narrative-Time-Loops",
                "--output",
                str(selection_export_path),
            ],
            [
                "-Root",
                str(root),
                "-Pack",
                "Narrative-Media",
                "-Capability",
                "Narrative-Time-Loops",
                "-Output",
                str(selection_export_path),
            ],
        )
        run_command(runtime, selection_export_command, root, check["timeout_seconds"])
        exported_selection = json.loads(selection_export_path.read_text(encoding="utf-8-sig"))
        if exported_selection != selection:
            raise CompatibilityFailure(f"{runtime.id} catalog selection export differs from JSON output.")
        selection_export_bytes[runtime.id] = selection_export_path.read_bytes()

        project_view_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--project-root", str(root), "--json"],
            ["-Root", str(root), "-ProjectRoot", str(root), "-Json"],
        )
        project_view_result = run_command(runtime, project_view_command, root, check["timeout_seconds"])
        project_view = parse_json_output(project_view_result.stdout)
        if (
            not isinstance(project_view, dict)
            or project_view.get("contract") != "framework-catalog-project-view"
            or project_view.get("summary", {}).get("selected_pack_count") != 10
            or project_view.get("summary", {}).get("enabled_capability_count") != 123
        ):
            raise CompatibilityFailure(f"{runtime.id} returned an invalid catalog project view: {project_view!r}")
        project_view_documents[runtime.id] = project_view

        project_view_export_path = output_root / f"{runtime.id}-project-view.json"
        project_view_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--project-root",
                str(root),
                "--output",
                str(project_view_export_path),
            ],
            [
                "-Root",
                str(root),
                "-ProjectRoot",
                str(root),
                "-Output",
                str(project_view_export_path),
            ],
        )
        run_command(runtime, project_view_export_command, root, check["timeout_seconds"])
        exported_project_view = json.loads(project_view_export_path.read_text(encoding="utf-8-sig"))
        if exported_project_view != project_view:
            raise CompatibilityFailure(f"{runtime.id} catalog project-view export differs from JSON output.")
        project_view_export_bytes[runtime.id] = project_view_export_path.read_bytes()

        project_view_report_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--project-root", str(root), "--show", "overview"],
            ["-Root", str(root), "-ProjectRoot", str(root), "-Show", "overview"],
        )
        project_view_report_result = run_command(
            runtime,
            project_view_report_command,
            root,
            check["timeout_seconds"],
        )
        project_view_reports[runtime.id] = project_view_report_result.stdout.replace("\r\n", "\n")
        project_view_report_path = output_root / f"{runtime.id}-project-view.txt"
        project_view_report_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--project-root",
                str(root),
                "--show",
                "overview",
                "--report-output",
                str(project_view_report_path),
            ],
            [
                "-Root",
                str(root),
                "-ProjectRoot",
                str(root),
                "-Show",
                "overview",
                "-ReportOutput",
                str(project_view_report_path),
            ],
        )
        run_command(runtime, project_view_report_export_command, root, check["timeout_seconds"])
        project_view_report_bytes[runtime.id] = project_view_report_path.read_bytes()
        if project_view_report_bytes[runtime.id].decode("utf-8") != project_view_reports[runtime.id]:
            raise CompatibilityFailure(f"{runtime.id} catalog project-view report export differs from human output.")

        project_view_selection_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--project-root",
                str(root),
                "--pack",
                "Narrative-Media",
                "--capability",
                "Narrative-Time-Loops",
                "--json",
            ],
            [
                "-Root",
                str(root),
                "-ProjectRoot",
                str(root),
                "-Pack",
                "Narrative-Media",
                "-Capability",
                "Narrative-Time-Loops",
                "-Json",
            ],
        )
        project_view_selection_result = run_command(
            runtime,
            project_view_selection_command,
            root,
            check["timeout_seconds"],
        )
        project_view_selection = parse_json_output(project_view_selection_result.stdout)
        if (
            not isinstance(project_view_selection, dict)
            or project_view_selection.get("contract") != "framework-catalog-project-view-selection"
            or [row.get("id") for row in project_view_selection.get("packs", [])] != ["narrative-media"]
            or [row.get("id") for row in project_view_selection.get("capabilities", [])] != ["narrative-time-loops"]
        ):
            raise CompatibilityFailure(
                f"{runtime.id} returned an invalid catalog project-view selection: {project_view_selection!r}"
            )
        project_view_selections[runtime.id] = project_view_selection

        missing_project_root = output_root / "missing-project-root"
        project_attachment_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--project-root", str(missing_project_root), "--json"],
            ["-Root", str(root), "-ProjectRoot", str(missing_project_root), "-Json"],
        )
        project_attachment_result = run_command(
            runtime,
            project_attachment_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        project_attachment_failure = parse_json_output(project_attachment_result.stdout)
        if (
            not isinstance(project_attachment_failure, dict)
            or project_attachment_failure.get("contract") != "framework-catalog-result"
            or project_attachment_failure.get("diagnostic", {}).get("classification") != "project-attachment"
        ):
            raise CompatibilityFailure(
                f"{runtime.id} returned an invalid project-attachment failure: {project_attachment_failure!r}"
            )
        project_attachment_failures[runtime.id] = project_attachment_failure["diagnostic"]["classification"]

        invalid_root = output_root / "missing-framework-root"
        failure_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(invalid_root), "--json"],
            ["-Root", str(invalid_root), "-Json"],
        )
        failure_result = run_command(
            runtime,
            failure_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        failure = parse_json_output(failure_result.stdout)
        if (
            not isinstance(failure, dict)
            or failure.get("contract") != "framework-catalog-result"
            or failure.get("catalog") is not None
            or failure.get("status") != "failed"
            or not isinstance(failure.get("diagnostic"), dict)
        ):
            raise CompatibilityFailure(f"{runtime.id} returned an invalid catalog failure envelope: {failure!r}")
        if str(root.parent).casefold() in json.dumps(failure).casefold():
            raise CompatibilityFailure(f"{runtime.id} leaked an absolute path in a catalog failure.")
        failure_classifications[runtime.id] = failure["diagnostic"].get("classification")

        invalid_show_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--show", "not-a-section"],
            ["-Root", str(root), "-Show", "not-a-section"],
        )
        invalid_show_result = run_command(
            runtime,
            invalid_show_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        invalid_show_failures[runtime.id] = invalid_show_result.stderr.strip()

        unknown_pack_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--pack", "missing-pack"],
            ["-Root", str(root), "-Pack", "missing-pack"],
        )
        unknown_pack_result = run_command(
            runtime,
            unknown_pack_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        singular_selection_failures[runtime.id] = unknown_pack_result.stderr.strip()

        unsafe_report_path = root.parent / ".framework-catalog-report-outside.txt"
        unsafe_report_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--report-output", str(unsafe_report_path)],
            ["-Root", str(root), "-ReportOutput", str(unsafe_report_path)],
        )
        unsafe_report_result = run_command(
            runtime,
            unsafe_report_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        if unsafe_report_path.exists():
            raise CompatibilityFailure(f"{runtime.id} created a catalog report outside the framework root.")
        unsafe_report_failures[runtime.id] = unsafe_report_result.stderr.strip()

    reference_runtime = runtimes[0].id
    reference = documents[reference_runtime]
    for runtime_id, document in documents.items():
        if document != reference:
            raise CompatibilityFailure(f"Framework catalog differs between {reference_runtime} and {runtime_id}.")
    if len(set(export_bytes.values())) != 1:
        raise CompatibilityFailure("Canonical framework-catalog export bytes differ between runtimes.")
    if len(set(report_export_bytes.values())) != 1:
        raise CompatibilityFailure("Framework-catalog human report bytes differ between runtimes.")
    for runtime_id, selection in selection_documents.items():
        if selection != selection_documents[reference_runtime]:
            raise CompatibilityFailure(
                f"Framework-catalog selection differs between {reference_runtime} and {runtime_id}."
            )
    if len(set(selection_export_bytes.values())) != 1:
        raise CompatibilityFailure("Framework-catalog selection export bytes differ between runtimes.")
    for runtime_id, project_view in project_view_documents.items():
        if project_view != project_view_documents[reference_runtime]:
            raise CompatibilityFailure(
                f"Framework-catalog project view differs between {reference_runtime} and {runtime_id}."
            )
    if len(set(project_view_export_bytes.values())) != 1:
        raise CompatibilityFailure("Framework-catalog project-view export bytes differ between runtimes.")
    if len(set(project_view_reports.values())) != 1 or len(set(project_view_report_bytes.values())) != 1:
        raise CompatibilityFailure("Framework-catalog project-view reports differ between runtimes.")
    for runtime_id, project_view_selection in project_view_selections.items():
        if project_view_selection != project_view_selections[reference_runtime]:
            raise CompatibilityFailure(
                f"Framework-catalog project-view selection differs between {reference_runtime} and {runtime_id}."
            )
    if len(set(project_attachment_failures.values())) != 1:
        raise CompatibilityFailure(
            f"Framework-catalog project-attachment failures differ: {project_attachment_failures}"
        )
    for case_id in human_reports[reference_runtime]:
        outputs = {reports[case_id] for reports in human_reports.values()}
        if len(outputs) != 1:
            raise CompatibilityFailure(f"Framework-catalog human case `{case_id}` differs between runtimes.")
    if len(set(failure_classifications.values())) != 1:
        raise CompatibilityFailure(f"Framework-catalog failure classes differ: {failure_classifications}")
    if len(set(invalid_show_failures.values())) != 1:
        raise CompatibilityFailure(f"Framework-catalog show failures differ: {invalid_show_failures}")
    if len(set(singular_selection_failures.values())) != 1:
        raise CompatibilityFailure(f"Framework-catalog selector failures differ: {singular_selection_failures}")
    if len(set(unsafe_report_failures.values())) != 1:
        raise CompatibilityFailure(f"Framework-catalog unsafe-path failures differ: {unsafe_report_failures}")

    canonical_export = export_bytes[reference_runtime]
    return {
        "status": "passed",
        "contract_version": reference["contract_version"],
        "packs": len(reference["packs"]),
        "capabilities": len(reference["capabilities"]),
        "canonical_export_bytes": len(canonical_export),
        "canonical_export_sha256": hashlib.sha256(canonical_export).hexdigest(),
        "human_report_export_bytes": len(report_export_bytes[reference_runtime]),
        "human_report_export_sha256": hashlib.sha256(report_export_bytes[reference_runtime]).hexdigest(),
        "human_sections": ["packs", "capabilities"],
        "selection_contract_version": selection_documents[reference_runtime]["contract_version"],
        "selection_export_bytes": len(selection_export_bytes[reference_runtime]),
        "selection_export_sha256": hashlib.sha256(selection_export_bytes[reference_runtime]).hexdigest(),
        "project_view_contract_version": project_view_documents[reference_runtime]["contract_version"],
        "project_view_export_bytes": len(project_view_export_bytes[reference_runtime]),
        "project_view_export_sha256": hashlib.sha256(project_view_export_bytes[reference_runtime]).hexdigest(),
        "project_view_report_bytes": len(project_view_report_bytes[reference_runtime]),
        "project_view_selection_contract_version": project_view_selections[reference_runtime]["contract_version"],
        "project_attachment_cases": 1,
        "invalid_selector_cases": 2,
        "unsafe_report_path_cases": 1,
        "failure_classification": next(iter(failure_classifications.values())),
        "elapsed_seconds": elapsed,
    }


def run_effective_schema_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    python_script = root / "Tools" / "Commands" / "Framework" / "inspect_effective_schema.py"
    powershell_script = root / "Tools" / "Commands" / "Framework" / "Get-EffectiveProjectSchema.ps1"
    documents: dict[str, dict[str, Any]] = {}
    export_bytes: dict[str, bytes] = {}
    report_export_bytes: dict[str, bytes] = {}
    overview_export_bytes: dict[str, bytes] = {}
    selection_documents: dict[str, dict[str, Any]] = {}
    selection_export_bytes: dict[str, bytes] = {}
    human_reports: dict[str, dict[str, str]] = {}
    failure_codes: dict[str, str] = {}
    invalid_show_failures: dict[str, str] = {}
    singular_selection_failures: dict[str, str] = {}
    unsafe_report_failures: dict[str, str] = {}
    elapsed: dict[str, float] = {}

    for runtime in runtimes:
        command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--json"],
            ["-Root", str(root), "-Json"],
        )
        result = run_command(runtime, command, root, check["timeout_seconds"])
        document = parse_json_output(result.stdout)
        if not isinstance(document, dict) or document.get("contract") != "effective-project-schema":
            raise CompatibilityFailure(f"{runtime.id} returned an invalid effective schema: {document!r}")
        documents[runtime.id] = document
        elapsed[runtime.id] = result.elapsed_seconds

        human_reports[runtime.id] = {}
        human_cases = {
            "overview": (
                ["--root", str(root), "--show", "overview"],
                ["-Root", str(root), "-Show", "overview"],
            ),
            "combined": (
                ["--root", str(root), "--show", "packs", "--show", "capabilities"],
                ["-Root", str(root), "-Show", "packs,capabilities"],
            ),
            "all-deduplicated": (
                ["--root", str(root), "--show", "packs", "--show", "all", "--show", "packs"],
                ["-Root", str(root), "-Show", "packs,all,packs"],
            ),
        }
        for case_id, (python_args, powershell_args) in human_cases.items():
            human_command = python_or_powershell_command(
                runtime,
                python_script,
                powershell_script,
                python_args,
                powershell_args,
            )
            human_result = run_command(runtime, human_command, root, check["timeout_seconds"])
            human_reports[runtime.id][case_id] = human_result.stdout.replace("\r\n", "\n")

        report_export_path = output_root / f"{runtime.id}.txt"
        report_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--show",
                "packs",
                "--show",
                "all",
                "--show",
                "packs",
                "--report-output",
                str(report_export_path),
            ],
            [
                "-Root",
                str(root),
                "-Show",
                "packs,all,packs",
                "-ReportOutput",
                str(report_export_path),
            ],
        )
        report_export_result = run_command(runtime, report_export_command, root, check["timeout_seconds"])
        expected_confirmation = f"Exported report: {report_export_path.relative_to(root).as_posix()}\n"
        if report_export_result.stdout.replace("\r\n", "\n") != expected_confirmation:
            raise CompatibilityFailure(f"{runtime.id} returned an invalid report-export confirmation.")
        report_export_bytes[runtime.id] = report_export_path.read_bytes()
        if report_export_bytes[runtime.id].decode("utf-8") != human_reports[runtime.id]["all-deduplicated"]:
            raise CompatibilityFailure(f"{runtime.id} report export differs from its human command output.")

        overview_export_path = output_root / f"{runtime.id}-overview.txt"
        overview_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--show", "overview", "--report-output", str(overview_export_path)],
            ["-Root", str(root), "-Show", "overview", "-ReportOutput", str(overview_export_path)],
        )
        overview_export_result = run_command(runtime, overview_export_command, root, check["timeout_seconds"])
        expected_overview_confirmation = f"Exported report: {overview_export_path.relative_to(root).as_posix()}\n"
        if overview_export_result.stdout.replace("\r\n", "\n") != expected_overview_confirmation:
            raise CompatibilityFailure(f"{runtime.id} returned an invalid overview-export confirmation.")
        overview_export_bytes[runtime.id] = overview_export_path.read_bytes()
        if overview_export_bytes[runtime.id].decode("utf-8") != human_reports[runtime.id]["overview"]:
            raise CompatibilityFailure(f"{runtime.id} overview export differs from its human command output.")

        export_path = output_root / f"{runtime.id}.json"
        export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--output", str(export_path)],
            ["-Root", str(root), "-Output", str(export_path)],
        )
        run_command(runtime, export_command, root, check["timeout_seconds"])
        exported = json.loads(export_path.read_text(encoding="utf-8-sig"))
        if exported != document:
            raise CompatibilityFailure(f"{runtime.id} file export differs from its JSON command output.")
        export_bytes[runtime.id] = export_path.read_bytes()

        selection_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--pack",
                "Narrative-Media",
                "--capability",
                "Narrative-Time-Loops",
                "--json",
            ],
            [
                "-Root",
                str(root),
                "-Pack",
                "Narrative-Media",
                "-Capability",
                "Narrative-Time-Loops",
                "-Json",
            ],
        )
        selection_result = run_command(runtime, selection_command, root, check["timeout_seconds"])
        selection_document = parse_json_output(selection_result.stdout)
        if (
            not isinstance(selection_document, dict)
            or selection_document.get("contract") != "effective-project-schema-selection"
            or [row.get("id") for row in selection_document.get("packs", [])] != ["narrative-media"]
            or [row.get("id") for row in selection_document.get("capabilities", [])] != ["narrative-time-loops"]
        ):
            raise CompatibilityFailure(
                f"{runtime.id} returned an invalid effective-schema selection: {selection_document!r}"
            )
        selection_documents[runtime.id] = selection_document

        selection_export_path = output_root / f"{runtime.id}-selection.json"
        selection_export_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            [
                "--root",
                str(root),
                "--pack",
                "Narrative-Media",
                "--capability",
                "Narrative-Time-Loops",
                "--output",
                str(selection_export_path),
            ],
            [
                "-Root",
                str(root),
                "-Pack",
                "Narrative-Media",
                "-Capability",
                "Narrative-Time-Loops",
                "-Output",
                str(selection_export_path),
            ],
        )
        run_command(runtime, selection_export_command, root, check["timeout_seconds"])
        exported_selection = json.loads(selection_export_path.read_text(encoding="utf-8-sig"))
        if exported_selection != selection_document:
            raise CompatibilityFailure(f"{runtime.id} selection export differs from its JSON command output.")
        selection_export_bytes[runtime.id] = selection_export_path.read_bytes()

        invalid_root = output_root / "missing-project-root"
        failure_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(invalid_root), "--json"],
            ["-Root", str(invalid_root), "-Json"],
        )
        failure_result = run_command(
            runtime,
            failure_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        failure = parse_json_output(failure_result.stdout)
        if (
            not isinstance(failure, dict)
            or failure.get("schema") is not None
            or not isinstance(failure.get("diagnostics"), list)
            or len(failure["diagnostics"]) != 1
            or failure["diagnostics"][0].get("severity") != "error"
        ):
            raise CompatibilityFailure(f"{runtime.id} returned an invalid failure envelope: {failure!r}")
        failure_codes[runtime.id] = failure["diagnostics"][0]["code"]

        invalid_show_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--show", "not-a-section"],
            ["-Root", str(root), "-Show", "not-a-section"],
        )
        invalid_show_result = run_command(
            runtime,
            invalid_show_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        invalid_show_failures[runtime.id] = invalid_show_result.stderr.strip()

        unknown_pack_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--pack", "missing-pack"],
            ["-Root", str(root), "-Pack", "missing-pack"],
        )
        unknown_pack_result = run_command(
            runtime,
            unknown_pack_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        singular_selection_failures[runtime.id] = unknown_pack_result.stderr.strip()

        unsafe_report_path = root.parent / ".effective-schema-report-outside.txt"
        unsafe_report_command = python_or_powershell_command(
            runtime,
            python_script,
            powershell_script,
            ["--root", str(root), "--report-output", str(unsafe_report_path)],
            ["-Root", str(root), "-ReportOutput", str(unsafe_report_path)],
        )
        unsafe_report_result = run_command(
            runtime,
            unsafe_report_command,
            root,
            check["timeout_seconds"],
            expect_success=False,
        )
        if unsafe_report_path.exists():
            raise CompatibilityFailure(f"{runtime.id} created an unsafe report export outside the project root.")
        unsafe_report_failures[runtime.id] = unsafe_report_result.stderr.strip()

    reference_runtime = runtimes[0].id
    reference = documents[reference_runtime]
    for runtime_id, document in documents.items():
        if document != reference:
            raise CompatibilityFailure(f"Effective-schema output differs between {reference_runtime} and {runtime_id}.")
    if len(set(export_bytes.values())) != 1:
        raise CompatibilityFailure("Canonical effective-schema export bytes differ between runtimes.")
    if len(set(report_export_bytes.values())) != 1:
        raise CompatibilityFailure("Effective-schema human report export bytes differ between runtimes.")
    if len(set(overview_export_bytes.values())) != 1:
        raise CompatibilityFailure("Effective-schema overview export bytes differ between runtimes.")
    for runtime_id, selection_document in selection_documents.items():
        if selection_document != selection_documents[reference_runtime]:
            raise CompatibilityFailure(
                f"Effective-schema selection differs between {reference_runtime} and {runtime_id}."
            )
    if len(set(selection_export_bytes.values())) != 1:
        raise CompatibilityFailure("Effective-schema selection export bytes differ between runtimes.")
    for case_id in human_reports[reference_runtime]:
        outputs = {reports[case_id] for reports in human_reports.values()}
        if len(outputs) != 1:
            raise CompatibilityFailure(f"Effective-schema human inspection case `{case_id}` differs between runtimes.")
    if len(set(failure_codes.values())) != 1:
        raise CompatibilityFailure(f"Effective-schema failure codes differ by runtime: {failure_codes}")
    if len(set(invalid_show_failures.values())) != 1:
        raise CompatibilityFailure(f"Effective-schema show failures differ by runtime: {invalid_show_failures}")
    if len(set(singular_selection_failures.values())) != 1:
        raise CompatibilityFailure(
            f"Effective-schema singular selector failures differ by runtime: {singular_selection_failures}"
        )
    if len(set(unsafe_report_failures.values())) != 1:
        raise CompatibilityFailure(
            f"Effective-schema unsafe report failures differ by runtime: {unsafe_report_failures}"
        )
    canonical_export = export_bytes[reference_runtime]

    return {
        "status": "passed",
        "contract_version": reference["contract_version"],
        "packs": len(reference["packs"]),
        "capabilities": len(reference["capabilities"]),
        "controlled_value_namespaces": len(reference["controlled_value_namespaces"]),
        "diagnostics": len(reference["diagnostics"]),
        "canonical_export_bytes": len(canonical_export),
        "canonical_export_sha256": hashlib.sha256(canonical_export).hexdigest(),
        "human_report_export_bytes": len(report_export_bytes[reference_runtime]),
        "human_report_export_sha256": hashlib.sha256(report_export_bytes[reference_runtime]).hexdigest(),
        "overview_report_bytes": len(overview_export_bytes[reference_runtime]),
        "overview_report_sha256": hashlib.sha256(overview_export_bytes[reference_runtime]).hexdigest(),
        "overview_report_lines": len(human_reports[reference_runtime]["overview"].splitlines()),
        "human_sections": ["packs", "capabilities"],
        "human_report_lines": len(human_reports[reference_runtime]["combined"].splitlines()),
        "human_all_report_lines": len(human_reports[reference_runtime]["all-deduplicated"].splitlines()),
        "selection_contract_version": selection_documents[reference_runtime]["contract_version"],
        "selection_export_bytes": len(selection_export_bytes[reference_runtime]),
        "selection_export_sha256": hashlib.sha256(selection_export_bytes[reference_runtime]).hexdigest(),
        "invalid_selector_cases": 2,
        "unsafe_report_path_cases": 1,
        "failure_code": next(iter(failure_codes.values())),
        "elapsed_seconds": elapsed,
    }


CHECK_HANDLERS = {
    "artifact-lifecycle": run_artifact_lifecycle_check,
    "compatibility-reporting": run_compatibility_reporting_check,
    "conformance-reporting": run_conformance_reporting_check,
    "effective-schema": run_effective_schema_check,
    "framework-catalog": run_framework_catalog_check,
    "framework-extraction": run_framework_extraction_check,
    "qa": run_qa_check,
    "render": run_render_check,
    "root-discovery": run_root_discovery_check,
    "visualization": run_visualization_check,
}


def protected_paths(root: Path) -> list[Path]:
    project = load_project_config(root)
    settings = json.loads(project.visualization_render_settings.read_text(encoding="utf-8"))
    paths = [
        project.visualization_render_settings,
        root / settings["reportPath"],
        root / settings["snapshotPath"],
    ]
    for view in settings["views"]:
        paths.append(root / view["input"])
        paths.extend(root / output for output in view.get("outputs", []))
    if project.qa_export.exists():
        paths.append(project.qa_export)
    return paths


def select_checks(registry: dict[str, Any], profile: str, requested: list[str]) -> list[dict[str, Any]]:
    checks = {check["id"]: check for check in registry["checks"]}
    if requested:
        if len(requested) != len(set(requested)):
            raise CompatibilityFailure("Requested compatibility checks must not contain duplicates.")
        missing = set(requested) - set(checks)
        if missing:
            raise CompatibilityFailure(f"Unknown requested compatibility checks: {sorted(missing)}")
        selected_ids = requested
    else:
        if profile not in registry["profiles"]:
            raise CompatibilityFailure(f"Unknown compatibility profile: {profile}")
        selected_ids = registry["profiles"][profile]
    return [checks[check_id] for check_id in selected_ids]


def list_registry(registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": registry["schema_version"],
        "profiles": registry["profiles"],
        "checks": [{"id": check["id"], "kind": check["kind"]} for check in registry["checks"]],
    }


def cleanup_output(root: Path, output_root: Path) -> None:
    command = [
        sys.executable,
        "-B",
        str(root / "Tools" / "Commands" / "Maintenance" / "clean_temp_files.py"),
        "--tmp-path",
        output_root.relative_to(root).as_posix(),
        "--delete",
        "--json",
    ]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8", check=False)
    if completed.returncode != 0:
        raise CompatibilityFailure(f"Compatibility cleanup failed: {completed.stdout}\n{completed.stderr}")


def write_detailed_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def bounded_failure_excerpt(value: object) -> tuple[str, bool]:
    normalized = str(value or "Runner exited without output.").replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    truncated = len(lines) > FAILURE_EXCERPT_LINES
    excerpt = "\n".join(lines[:FAILURE_EXCERPT_LINES])
    encoded = excerpt.encode("utf-8")
    if len(encoded) > FAILURE_EXCERPT_BYTES:
        truncated = True
        encoded = encoded[:FAILURE_EXCERPT_BYTES]
        while True:
            try:
                excerpt = encoded.decode("utf-8")
                break
            except UnicodeDecodeError as error:
                encoded = encoded[: error.start]
    return excerpt, truncated


def concise_compatibility_summary(
    payload: dict[str, Any],
    *,
    report_path: str | None,
    failed_check: dict[str, Any] | None,
    failure_classification: str | None,
) -> dict[str, Any]:
    results = [{"id": result["id"], "kind": result["kind"], "status": result["status"]} for result in payload["checks"]]
    failures = []
    if "error" in payload:
        failed_id = failed_check["id"] if failed_check is not None else None
        if failed_check is not None and not any(result["id"] == failed_id for result in results):
            results.append({"id": failed_id, "kind": failed_check["kind"], "status": "failed"})
        excerpt, truncated = bounded_failure_excerpt(payload["error"])
        failures.append(
            {
                "id": failed_id,
                "classification": failure_classification or "orchestration-failure",
                "excerpt": excerpt,
                "excerpt_truncated": truncated,
            }
        )
    return {
        "contract": "validation-run-summary",
        "contract_version": 1,
        "runner": "project-compatibility",
        "status": payload["status"],
        "profile": payload["profile"],
        "requested_ids": payload["requested_checks"],
        "selected_count": len(payload["requested_checks"]),
        "passed": payload["passed"],
        "failed": payload["failed"],
        "elapsed_seconds": payload["elapsed_seconds"],
        "canonical_outputs_unchanged": payload["canonical_outputs_unchanged"],
        "output_kept": payload["output_kept"],
        "report_path": report_path,
        "results": results,
        "failures": failures,
    }


def concise_compatibility_orchestration_failure(error: Exception) -> dict[str, Any]:
    excerpt, truncated = bounded_failure_excerpt(error)
    return {
        "contract": "validation-run-summary",
        "contract_version": 1,
        "runner": "project-compatibility",
        "status": "failed",
        "profile": None,
        "requested_ids": [],
        "selected_count": 0,
        "passed": 0,
        "failed": 1,
        "elapsed_seconds": None,
        "canonical_outputs_unchanged": None,
        "output_kept": False,
        "report_path": None,
        "results": [],
        "failures": [
            {
                "id": None,
                "classification": "orchestration-failure",
                "excerpt": excerpt,
                "excerpt_truncated": truncated,
            }
        ],
    }


def main() -> int:
    args = parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    if args.list and (args.summary_json or args.report_output):
        raise CompatibilityFailure("--list cannot be combined with --summary-json or --report-output.")
    report_output = resolve_report_output(args.report_output, root) if args.report_output else None
    registry_path = resolve_registry_path(args.registry, root)
    registry = load_registry(registry_path)
    if args.list:
        payload = list_registry(registry)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("Compatibility profiles:")
            for profile, check_ids in payload["profiles"].items():
                print(f"- {profile}: {', '.join(check_ids)}")
            print("Compatibility checks:")
            for check in payload["checks"]:
                print(f"- {check['id']} ({check['kind']})")
        return 0
    checks = select_checks(registry, args.profile, args.check)
    runtimes = [find_runtime(runtime_id) for runtime_id in registry["runtimes"]]
    output_root = resolve_output_root(args.output_root, root)
    if report_output == output_root:
        raise CompatibilityFailure("Compatibility report output cannot be the scoped output directory itself.")
    output_root.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    failure: Exception | None = None
    failed_check: dict[str, Any] | None = None
    failure_classification: str | None = None
    before: dict[str, str] | None = None
    canonical_unchanged = False
    try:
        before = sha256_tree(protected_paths(root))
        for check in checks:
            failed_check = check
            check_root = output_root / check["id"]
            check_root.mkdir(parents=True, exist_ok=True)
            result = CHECK_HANDLERS[check["kind"]](check, runtimes, root, check_root)
            results.append({"id": check["id"], "kind": check["kind"], **result})
            failed_check = None
    except Exception as exc:  # preserve scoped output for the failure summary before cleanup
        failure = exc
        failure_classification = "check-failure" if failed_check is not None else "orchestration-failure"
    if before is not None:
        after = sha256_tree(protected_paths(root))
        canonical_unchanged = before == after
        if not canonical_unchanged and failure is None:
            failure = CompatibilityFailure("Compatibility run modified protected canonical outputs.")
            failure_classification = "canonical-output-change"
    payload = {
        "schema_version": 1,
        "profile": args.profile if not args.check else None,
        "requested_checks": [check["id"] for check in checks],
        "status": "failed" if failure else "passed",
        "passed": len(results),
        "failed": 1 if failure else 0,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "canonical_outputs_unchanged": canonical_unchanged,
        "output_root": str(output_root),
        "output_kept": args.keep_output or failure is not None,
        "checks": results,
    }
    if failure:
        payload["error"] = str(failure)
    report_inside_output = report_output is not None and (
        report_output == output_root or output_root in report_output.parents
    )
    if report_inside_output:
        payload["output_kept"] = True
    if not args.keep_output and failure is None and not report_inside_output:
        try:
            cleanup_output(root, output_root)
            payload["output_root"] = None
            payload["output_kept"] = False
        except Exception as exc:
            failure = exc
            failure_classification = "cleanup-failure"
            payload["status"] = "failed"
            payload["failed"] = 1
            payload["output_kept"] = True
            payload["error"] = str(exc)
    if failure is not None and report_output is None:
        report_output = output_root / "report.json"
    if report_output is not None:
        write_detailed_report(report_output, payload)
    report_relative = report_output.relative_to(root).as_posix() if report_output is not None else None
    if args.json:
        print(json.dumps(payload, indent=2))
    elif args.summary_json:
        print(
            json.dumps(
                concise_compatibility_summary(
                    payload,
                    report_path=report_relative,
                    failed_check=failed_check,
                    failure_classification=failure_classification,
                ),
                separators=(",", ":"),
            )
        )
    else:
        print(
            f"Compatibility {payload['status']}: {len(results)}/{len(checks)} checks in {payload['elapsed_seconds']}s"
        )
        for result in results:
            print(f"- {result['id']}: {result['status']}")
        if failure:
            excerpt, truncated = bounded_failure_excerpt(failure)
            print(f"Error: {excerpt}", file=sys.stderr)
            if truncated:
                print("Error excerpt truncated; see the detailed report.", file=sys.stderr)
            print(f"Output retained: {output_root}", file=sys.stderr)
            print(f"Detailed report: {report_relative}", file=sys.stderr)
    return 1 if failure else 0


def cli() -> int:
    try:
        return main()
    except CompatibilityFailure as exc:
        if "--summary-json" in sys.argv:
            print(json.dumps(concise_compatibility_orchestration_failure(exc), separators=(",", ":")))
        elif "--json" in sys.argv:
            print(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "failed",
                        "passed": 0,
                        "failed": 1,
                        "canonical_outputs_unchanged": None,
                        "output_root": None,
                        "output_kept": False,
                        "checks": [],
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(f"Compatibility failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
