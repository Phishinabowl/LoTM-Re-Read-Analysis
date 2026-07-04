#!/usr/bin/env python3
"""Clean disposable local tool caches from this repository."""

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


def clean_cache_dirs(paths: list[Path]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for path in paths:
        shutil.rmtree(path)
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
    args = parser.parse_args()

    repo_root = get_repo_root()
    targets = find_cache_dirs(repo_root)

    if args.delete:
        results = clean_cache_dirs(targets)
    else:
        results = [{"path": str(path), "status": "would_delete"} for path in targets]

    output = {
        "repo_root": str(repo_root),
        "delete": args.delete,
        "allowed_directory_names": sorted(CACHE_DIR_NAMES),
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
