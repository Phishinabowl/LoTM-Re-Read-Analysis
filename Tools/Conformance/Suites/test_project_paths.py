"""Conformance vectors for dependency-light project-root discovery."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


TOOLS_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = TOOLS_ROOT / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.project_paths import resolve_project_root


def create_project(root: Path) -> Path:
    (root / "Project_Config").mkdir(parents=True)
    (root / "Project_Config" / "project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    return root.resolve()


def assert_rejected(action, expected_text: str) -> None:
    try:
        action()
    except RuntimeError as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"Expected error containing {expected_text!r}, got: {exc}") from exc
        return
    raise AssertionError(f"Expected rejection containing {expected_text!r}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    actual_root = resolve_project_root(args.root, executable_path=__file__)
    original_cwd = Path.cwd()
    temp_root = Path(tempfile.mkdtemp(prefix="knowledge-project-root-"))
    vectors = 0

    try:
        project_a = create_project(temp_root / "project-a")
        project_b = create_project(temp_root / "project-b")
        nested_a = project_a / "one" / "two"
        nested_a.mkdir(parents=True)
        nested_b = project_b / "nested"
        nested_b.mkdir()
        executable_b = nested_b / "command.py"
        executable_b.write_text("# fixture\n", encoding="utf-8")
        unrelated = temp_root / "unrelated"
        unrelated.mkdir()
        unrelated_executable = unrelated / "command.py"
        unrelated_executable.write_text("# fixture\n", encoding="utf-8")
        git_only = temp_root / "git-only"
        (git_only / ".git").mkdir(parents=True)

        assert resolve_project_root(actual_root, environment={"KNOWLEDGE_PROJECT_ROOT": str(project_b)}) == actual_root
        vectors += 1
        assert resolve_project_root(environment={"KNOWLEDGE_PROJECT_ROOT": str(project_b)}) == project_b
        vectors += 1
        assert_rejected(
            lambda: resolve_project_root(environment={"KNOWLEDGE_PROJECT_ROOT": str(unrelated)}),
            "missing required manifest",
        )
        vectors += 1
        assert_rejected(
            lambda: resolve_project_root(environment={"KNOWLEDGE_PROJECT_ROOT": "relative/project"}),
            "must be an absolute path",
        )
        vectors += 1
        assert resolve_project_root(current_directory=nested_a, environment={}) == project_a
        vectors += 1
        assert (
            resolve_project_root(
                executable_path=executable_b,
                current_directory=unrelated,
                environment={},
            )
            == project_b
        )
        vectors += 1
        assert (
            resolve_project_root(
                executable_path=executable_b,
                current_directory=nested_a,
                environment={},
            )
            == project_a
        )
        vectors += 1
        assert (
            resolve_project_root(
                executable_path=executable_b,
                current_directory=nested_a,
                environment={"KNOWLEDGE_PROJECT_ROOT": str(project_b)},
            )
            == project_b
        )
        vectors += 1
        assert_rejected(
            lambda: resolve_project_root(
                executable_path=unrelated_executable,
                current_directory=git_only,
                environment={},
            ),
            "Could not auto-detect",
        )
        vectors += 1
        assert_rejected(
            lambda: resolve_project_root(
                executable_path=unrelated_executable,
                current_directory=unrelated,
                environment={},
            ),
            "Expected manifest: Project_Config/project.yaml",
        )
        vectors += 1
        assert Path.cwd() == original_cwd
        vectors += 1
    finally:
        shutil.rmtree(temp_root)

    summary = {
        "environment_variable": "KNOWLEDGE_PROJECT_ROOT",
        "marker": "Project_Config/project.yaml",
        "schema_version": 1,
        "vectors": vectors,
        "working_directory_preserved": Path.cwd() == original_cwd,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Project-root conformance passed: {vectors} vectors; working directory preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
