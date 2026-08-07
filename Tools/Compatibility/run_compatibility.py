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
    "effective-schema",
    "framework-extraction",
    "qa",
    "render",
    "root-discovery",
    "visualization",
}
CHECK_KEYS = {
    "artifact-lifecycle": {"id", "kind", "timeout_seconds"},
    "effective-schema": {"id", "kind", "timeout_seconds"},
    "framework-extraction": {"id", "kind", "timeout_seconds"},
    "qa": {"id", "kind", "timeout_seconds", "bounded_graphs", "bounded_pages"},
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
    "visualization": {"id", "kind", "timeout_seconds"},
}
GENERATED_KEYS = {"generated_at", "generatedAt"}
MACHINE_ID = re.compile(r"^[a-z][a-z0-9-]*$")
TEXT_EXTENSIONS = {".json", ".md", ".mmd", ".txt", ".yaml", ".yml"}


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
        require_string_list(check, "bounded_graphs")
        require_string_list(check, "bounded_pages")
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
    parser.add_argument("--json", action="store_true", help="Emit a structured JSON summary.")
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
    if registry.get("schema_version") != 1:
        raise CompatibilityFailure("Compatibility registry schema_version must be integer 1.")
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
    return {
        "status": "passed",
        "nodes": int(match.group(1)) if match else None,
        "relationships": int(match.group(2)) if match else None,
        "refresh": refresh_comparison,
        "unbounded_graph_match": True,
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
    return {
        "status": "passed",
        "summary": summaries["python"],
        "files": comparison,
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


def run_effective_schema_check(
    check: dict[str, Any], runtimes: list[Runtime], root: Path, output_root: Path
) -> dict[str, Any]:
    python_script = root / "Tools" / "Commands" / "Framework" / "inspect_effective_schema.py"
    powershell_script = root / "Tools" / "Commands" / "Framework" / "Get-EffectiveProjectSchema.ps1"
    documents: dict[str, dict[str, Any]] = {}
    export_bytes: dict[str, bytes] = {}
    human_reports: dict[str, dict[str, str]] = {}
    failure_codes: dict[str, str] = {}
    selection_failures: dict[str, str] = {}
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
        selection_failures[runtime.id] = invalid_show_result.stderr.strip()

    reference_runtime = runtimes[0].id
    reference = documents[reference_runtime]
    for runtime_id, document in documents.items():
        if document != reference:
            raise CompatibilityFailure(f"Effective-schema output differs between {reference_runtime} and {runtime_id}.")
    if len(set(export_bytes.values())) != 1:
        raise CompatibilityFailure("Canonical effective-schema export bytes differ between runtimes.")
    for case_id in human_reports[reference_runtime]:
        outputs = {reports[case_id] for reports in human_reports.values()}
        if len(outputs) != 1:
            raise CompatibilityFailure(f"Effective-schema human inspection case `{case_id}` differs between runtimes.")
    if len(set(failure_codes.values())) != 1:
        raise CompatibilityFailure(f"Effective-schema failure codes differ by runtime: {failure_codes}")
    if len(set(selection_failures.values())) != 1:
        raise CompatibilityFailure(f"Effective-schema selector failures differ by runtime: {selection_failures}")
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
        "human_sections": ["packs", "capabilities"],
        "human_report_lines": len(human_reports[reference_runtime]["combined"].splitlines()),
        "human_all_report_lines": len(human_reports[reference_runtime]["all-deduplicated"].splitlines()),
        "invalid_selector_cases": 1,
        "failure_code": next(iter(failure_codes.values())),
        "elapsed_seconds": elapsed,
    }


CHECK_HANDLERS = {
    "artifact-lifecycle": run_artifact_lifecycle_check,
    "effective-schema": run_effective_schema_check,
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


def main() -> int:
    args = parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
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
    output_root.mkdir(parents=True, exist_ok=False)
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    failure: Exception | None = None
    before: dict[str, str] | None = None
    canonical_unchanged = False
    try:
        before = sha256_tree(protected_paths(root))
        for check in checks:
            check_root = output_root / check["id"]
            check_root.mkdir(parents=True, exist_ok=True)
            result = CHECK_HANDLERS[check["kind"]](check, runtimes, root, check_root)
            results.append({"id": check["id"], "kind": check["kind"], **result})
    except Exception as exc:  # preserve scoped output for the failure summary before cleanup
        failure = exc
    if before is not None:
        after = sha256_tree(protected_paths(root))
        canonical_unchanged = before == after
        if not canonical_unchanged and failure is None:
            failure = CompatibilityFailure("Compatibility run modified protected canonical outputs.")
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
    if not args.keep_output and failure is None:
        cleanup_output(root, output_root)
        payload["output_root"] = None
        payload["output_kept"] = False
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"Compatibility {payload['status']}: {len(results)}/{len(checks)} checks in {payload['elapsed_seconds']}s"
        )
        for result in results:
            print(f"- {result['id']}: {result['status']}")
        if failure:
            print(f"Error: {failure}", file=sys.stderr)
            print(f"Output retained: {output_root}", file=sys.stderr)
    return 1 if failure else 0


def cli() -> int:
    try:
        return main()
    except CompatibilityFailure as exc:
        if "--json" in sys.argv:
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
