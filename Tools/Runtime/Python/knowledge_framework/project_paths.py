"""Dependency-light project-root discovery and repository path primitives."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import sys


PROJECT_MANIFEST_PATH = Path("Project_Config") / "project.yaml"
PROJECT_ROOT_ENVIRONMENT_VARIABLE = "KNOWLEDGE_PROJECT_ROOT"


def is_project_root(path: str | Path) -> bool:
    candidate = Path(path)
    return candidate.is_dir() and (candidate / PROJECT_MANIFEST_PATH).is_file()


def path_and_parents(path: str | Path):
    resolved = Path(path).resolve()
    yield resolved
    yield from resolved.parents


def _validated_root(value: str | Path, source: str, *, require_absolute: bool = False) -> Path:
    candidate = Path(value).expanduser()
    if require_absolute and not candidate.is_absolute():
        raise RuntimeError(f"{source} must be an absolute path: {candidate}")
    resolved = candidate.resolve()
    if not is_project_root(resolved):
        raise RuntimeError(
            f"Project root from {source} is missing required manifest {PROJECT_MANIFEST_PATH.as_posix()}: {resolved}"
        )
    return resolved


def _executable_search_start(executable_path: str | Path | None) -> Path | None:
    value = executable_path
    if value is None and sys.argv and sys.argv[0] not in {"", "-c", "-m"}:
        value = sys.argv[0]
    if value is None:
        return None
    candidate = Path(value).expanduser().resolve()
    if candidate.is_file():
        return candidate.parent
    return candidate


def resolve_project_root(
    explicit_root: str | Path | None = None,
    *,
    executable_path: str | Path | None = None,
    current_directory: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path:
    """Resolve a project root without changing the process working directory."""

    if explicit_root is not None and str(explicit_root).strip():
        return _validated_root(explicit_root, "explicit root")

    environment_values = os.environ if environment is None else environment
    environment_root = environment_values.get(PROJECT_ROOT_ENVIRONMENT_VARIABLE, "").strip()
    if environment_root:
        return _validated_root(
            environment_root,
            f"environment variable {PROJECT_ROOT_ENVIRONMENT_VARIABLE}",
            require_absolute=True,
        )

    search_starts: list[tuple[str, Path]] = [
        ("current directory", Path.cwd() if current_directory is None else Path(current_directory)),
    ]
    executable_start = _executable_search_start(executable_path)
    if executable_start is not None:
        search_starts.append(("executable location", executable_start))

    checked: set[Path] = set()
    for _, start in search_starts:
        for candidate in path_and_parents(start):
            if candidate in checked:
                continue
            checked.add(candidate)
            if is_project_root(candidate):
                return candidate

    starts = ", ".join(f"{label}={Path(path).resolve()}" for label, path in search_starts)
    raise RuntimeError(
        f"Could not auto-detect the project root from {starts}. "
        f"Expected manifest: {PROJECT_MANIFEST_PATH.as_posix()}. "
        "Pass the root explicitly or set KNOWLEDGE_PROJECT_ROOT to an absolute project path."
    )
