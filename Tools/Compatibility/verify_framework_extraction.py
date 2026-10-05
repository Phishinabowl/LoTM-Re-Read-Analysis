#!/usr/bin/env python3
"""Rehearse a standalone framework copy against a neutral consumer project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


RUNTIME_ROOT = Path(__file__).resolve().parents[1] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.project_paths import resolve_project_root  # noqa: E402


# VERIFY (OWNER): Revisit this allowlist whenever a new portable framework surface is introduced.
COPY_DIRECTORIES = (
    Path("Framework"),
    Path("Tools/Runtime"),
    Path("Tools/Conformance"),
)
COPY_FILES = (
    Path("pyproject.toml"),
    Path("requirements-python.txt"),
    Path("requirements-powershell.txt"),
)
FORBIDDEN_TOP_LEVEL = (
    "Artwork",
    "Boards",
    "Glossary_Threads",
    "Investigations",
    "Obsidian_Export",
    "Source",
    "Testing",
    "Visualization",
    "Volumes",
)
PORTABLE_SUITES = (
    "project-root",
    "framework-installation",
    "framework-catalog",
    "capability-roadmap",
    "strict-ingestion",
    "lookup-key",
    "schema-pack",
    "temporal",
    "interpretation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Source project root; auto-detected when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    return parser.parse_args()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def copy_framework_surface(source_root: Path, target_root: Path) -> int:
    copied_files = 0
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
    for relative in COPY_DIRECTORIES:
        source = source_root / relative
        target = target_root / relative
        shutil.copytree(source, target, ignore=ignore)
        copied_files += sum(1 for path in target.rglob("*") if path.is_file())
    for relative in COPY_FILES:
        shutil.copy2(source_root / relative, target_root / relative)
        copied_files += 1
    return copied_files


def write_neutral_consumer(target_root: Path) -> None:
    for relative in (
        "Content",
        "Project_Config",
        "Tools/Extraction-Stubs",
    ):
        (target_root / relative).mkdir(parents=True, exist_ok=True)

    write_text(target_root / "Tools/Extraction-Stubs/helper.py", "# Neutral extraction helper stub.\n")
    write_text(target_root / "Tools/Extraction-Stubs/Helper.ps1", "# Neutral extraction helper stub.\n")
    write_text(target_root / "Tools/Extraction-Stubs/settings.json", "{}\n")

    write_text(
        target_root / "Project_Config/project.yaml",
        """schema_version: 11
project_id: extraction-smoke
framework: knowledge-model
domain: neutral

paths:
  content_roots:
    - id: content
      path: Content
      provenance_mode: fixed
      provenance_label: content
  resource_roots:
    - id: framework
      path: Framework
      required: true
    - id: tools
      path: Tools
      required: true
    - id: project-config
      path: Project_Config
      required: true
  qa_export: QA_Output
  visualization:
    python_helper: Tools/Extraction-Stubs/helper.py
    powershell_helper: Tools/Extraction-Stubs/Helper.ps1
    render_settings: Tools/Extraction-Stubs/settings.json
    puppeteer_config: Tools/Extraction-Stubs/settings.json
  cleanup:
    python_helper: Tools/Extraction-Stubs/helper.py
    powershell_helper: Tools/Extraction-Stubs/Helper.ps1

registries:
  lookup_keys: Framework/Data/unicode-lookup-16.0.0.json
  schema_packs: Project_Config/schema-packs.yaml
  taxonomy: Project_Config/taxonomy.yaml
  resources: Project_Config/resources.yaml
  sources: Project_Config/sources.yaml
  entities: Project_Config/entities.yaml
  reconciliation: Project_Config/reconciliation.yaml
  provenance: Project_Config/provenance.yaml
  chronology: Project_Config/chronology.yaml
  occurrences: Project_Config/occurrences.yaml
  interpretations: Project_Config/interpretations.yaml
  hosting: Project_Config/hosting.yaml
""",
    )
    write_text(
        target_root / "Project_Config/schema-packs.yaml",
        """schema_version: 2
selected_packs:
  - pack_id: core
    path: Framework/Packs/core/pack.yaml
capability_activation:
  default: disabled
  enabled:
    - structural-interpretation-modeling
""",
    )
    write_text(
        target_root / "Project_Config/taxonomy.yaml",
        """schema_version: 2
content_types: {}
categories: {}
""",
    )
    write_text(
        target_root / "Project_Config/resources.yaml",
        """schema_version: 1
resource_kinds: {}
resource_types: {}
""",
    )
    for name in (
        "sources",
        "entities",
        "reconciliation",
        "provenance",
        "chronology",
        "occurrences",
        "interpretations",
        "hosting",
    ):
        write_text(target_root / f"Project_Config/{name}.yaml", "schema_version: 1\n")


def assert_copy_boundary(target_root: Path) -> None:
    leaked = [name for name in FORBIDDEN_TOP_LEVEL if (target_root / name).exists()]
    if leaked:
        raise RuntimeError(f"Extraction copy contains forbidden project surfaces: {', '.join(leaked)}")
    if (target_root / "Project_Config/project.yaml").read_text(encoding="utf-8").find("extraction-smoke") < 0:
        raise RuntimeError("Extraction rehearsal did not create the neutral consumer manifest.")


def run_json(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        raise RuntimeError(f"Extraction command failed ({completed.returncode}): {' '.join(command)}\n{output}")
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"Extraction command produced no structured output: {' '.join(command)}")
    try:
        result = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Extraction command did not end with JSON: {' '.join(command)}") from exc
    if not isinstance(result, dict):
        raise RuntimeError(f"Extraction command returned a non-object summary: {' '.join(command)}")
    return result


def python_command() -> list[str]:
    command = [sys.executable, "Tools/Conformance/run_conformance.py"]
    for suite in PORTABLE_SUITES:
        command.extend(("--suite", suite))
    command.append("--json")
    return command


def powershell_command(host: str) -> list[str]:
    suite_literals = ",".join(f"'{suite}'" for suite in PORTABLE_SUITES)
    invocation = f"& 'Tools/Conformance/Run-Conformance.ps1' -Suite @({suite_literals}) -Json"
    command = [host, "-NoProfile"]
    command.extend(("-Command", invocation))
    return command


def find_powershell_host() -> str:
    host = shutil.which("pwsh")
    if host is None:
        raise RuntimeError(
            "Required extraction-test runtime is unavailable: powershell7. Install PowerShell 7.4+ Core."
        )
    try:
        probe = subprocess.run(
            [
                host,
                "-NoProfile",
                "-Command",
                "@{edition=$PSVersionTable.PSEdition;version=$PSVersionTable.PSVersion.ToString()}"
                " | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        if probe.returncode != 0:
            raise RuntimeError(
                f"Extraction PowerShell host probe failed ({probe.returncode}) at {host}: "
                f"{probe.stdout.strip()} {probe.stderr.strip()}. Use PowerShell 7.4+ Core."
            )
        result = json.loads(probe.stdout)
        version = str(result.get("version", ""))
        supported = (
            result.get("edition") == "Core"
            and re.fullmatch(r"\d+\.\d+(?:\.\d+){0,2}", version)
            and tuple(int(part) for part in version.split(".")[:2]) >= (7, 4)
        )
    except (OSError, subprocess.TimeoutExpired, ValueError, AttributeError) as exc:
        raise RuntimeError(
            f"Unable to verify extraction PowerShell host {host}: {exc}. Use PowerShell 7.4+ Core."
        ) from exc
    if not supported:
        raise RuntimeError(f"Unsupported extraction PowerShell host at {host}: {result!r}. Use PowerShell 7.4+ Core.")
    return host


def normalized_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "failed": summary.get("failed"),
        "passed": summary.get("passed"),
        "profile": summary.get("profile"),
        "schema_version": summary.get("schema_version"),
        "suite_count": summary.get("suite_count"),
        "suites": summary.get("suites"),
    }


def validate_portable_summary(summary: dict[str, Any]) -> None:
    suites = summary.get("suites")
    if (
        type(summary.get("schema_version")) is not int
        or summary["schema_version"] != 1
        or type(summary.get("failed")) is not int
        or summary["failed"] != 0
        or type(summary.get("passed")) is not int
        or summary["passed"] != len(PORTABLE_SUITES)
        or type(summary.get("suite_count")) is not int
        or summary["suite_count"] != len(PORTABLE_SUITES)
        or summary.get("profile") != "selected"
        or not isinstance(suites, list)
        or any(not isinstance(row, dict) or row.get("status") != "passed" for row in suites)
        or [row.get("id") for row in suites] != list(PORTABLE_SUITES)
    ):
        raise RuntimeError(
            "Extraction summary must report all nine selected portable suites passed in order (schema 1)."
        )


def main() -> int:
    args = parse_args()
    source_root = resolve_project_root(args.root, executable_path=__file__)
    powershell_host = find_powershell_host()
    with tempfile.TemporaryDirectory(prefix="knowledge-framework-extraction-") as temp_directory:
        target_root = Path(temp_directory) / "extracted-framework"
        target_root.mkdir()
        copied_files = copy_framework_surface(source_root, target_root)
        write_neutral_consumer(target_root)
        assert_copy_boundary(target_root)

        summaries: dict[str, dict[str, Any]] = {"python": run_json(python_command(), target_root)}
        summaries["powershell7"] = run_json(powershell_command(powershell_host), target_root)

        for result in summaries.values():
            validate_portable_summary(result)
        expected = normalized_summary(summaries["python"])
        for runtime in ("powershell7",):
            if normalized_summary(summaries[runtime]) != expected:
                raise RuntimeError(f"Extracted framework conformance differs between Python and {runtime}.")

        summary = {
            "schema_version": 1,
            "status": "passed",
            "copied_files": copied_files,
            "copied_directories": [path.as_posix() for path in COPY_DIRECTORIES],
            "copied_project_config": False,
            "forbidden_surfaces_absent": len(FORBIDDEN_TOP_LEVEL),
            "neutral_project_id": "extraction-smoke",
            "runtimes": list(summaries),
            "portable_suites": list(PORTABLE_SUITES),
            "temporary_copy_removed_on_exit": True,
        }
    if Path(temp_directory).exists():
        raise RuntimeError(f"Extraction temporary copy remains after cleanup: {temp_directory}")
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Framework extraction rehearsal passed: "
            f"{copied_files} reusable files, {len(PORTABLE_SUITES)} portable suites, "
            "and two matching runtimes."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
