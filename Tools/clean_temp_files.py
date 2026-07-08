#!/usr/bin/env python3
"""Clean disposable local tool caches and opted-in temp artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
}

TMP_DIR_NAME = ".tmp"


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_within_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.resolve().relative_to(repo_root)
        return True
    except ValueError:
        return False


def find_cache_dirs(repo_root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_dir() or path.name not in CACHE_DIR_NAMES:
            continue
        resolved = path.resolve()
        if is_within_repo(resolved, repo_root):
            matches.append(resolved)
    return sorted(matches, key=lambda item: str(item).lower())


def find_tmp_artifacts(repo_root: Path) -> list[Path]:
    tmp_root = (repo_root / TMP_DIR_NAME).resolve()
    if not tmp_root.exists() or not tmp_root.is_dir():
        return []
    if not is_within_repo(tmp_root, repo_root):
        return []
    return sorted(tmp_root.iterdir(), key=lambda item: str(item).lower())


def resolve_existing_path(repo_root: Path, path_value: str) -> Path | None:
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        return None
    return path.resolve()


def is_within_tmp(path: Path, repo_root: Path) -> bool:
    tmp_root = (repo_root / TMP_DIR_NAME).resolve()
    try:
        path.resolve().relative_to(tmp_root)
        return path.resolve() != tmp_root
    except ValueError:
        return False


def find_scoped_tmp_artifacts(repo_root: Path, path_values: list[str]) -> list[Path]:
    matches: list[Path] = []
    seen: set[Path] = set()
    for path_value in path_values:
        resolved = resolve_existing_path(repo_root, path_value)
        if resolved is None or not is_within_repo(resolved, repo_root) or not is_within_tmp(resolved, repo_root):
            continue
        if resolved not in seen:
            matches.append(resolved)
            seen.add(resolved)
    return sorted(matches, key=lambda item: str(item).lower())


def clean_cache_dirs(paths: list[Path]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        results.append({"path": str(path), "status": "deleted"})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove allowlisted Python/tool cache directories under this repository."
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete matching cache directories. Without this flag, the script only lists matches.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output.",
    )
    parser.add_argument(
        "--include-tmp",
        action="store_true",
        help="Also include direct children of the repository .tmp directory.",
    )
    parser.add_argument(
        "--tmp-path",
        action="append",
        default=[],
        help=(
            "Include an exact path under repository .tmp. Repeat for multiple scoped paths. "
            "This is intended for automatic cleanup of artifacts created by the current run."
        ),
    )
    args = parser.parse_args()

    repo_root = get_repo_root()
    cache_targets = find_cache_dirs(repo_root)
    tmp_targets = find_tmp_artifacts(repo_root) if args.include_tmp else []
    scoped_tmp_targets = find_scoped_tmp_artifacts(repo_root, args.tmp_path)
    targets = cache_targets + tmp_targets + scoped_tmp_targets

    if args.delete:
        results = clean_cache_dirs(targets)
    else:
        results = [{"path": str(path), "status": "would_delete"} for path in targets]

    output = {
        "repo_root": str(repo_root),
        "delete": args.delete,
        "allowed_directory_names": sorted(CACHE_DIR_NAMES),
        "include_tmp": args.include_tmp,
        "tmp_root": str(repo_root / TMP_DIR_NAME),
        "cache_count": len(cache_targets),
        "tmp_count": len(tmp_targets),
        "scoped_tmp_count": len(scoped_tmp_targets),
        "count": len(results),
        "results": results,
    }

    if args.json:
        print(json.dumps(output, indent=2))
        return 0

    action = "Deleted" if args.delete else "Would delete"
    if not results:
        print("No allowlisted cache directories found.")
        return 0

    for result in results:
        print(f"{action}: {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
