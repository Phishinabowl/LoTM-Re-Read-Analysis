"""Resolve explicit Git scope and explain advisory impact without launching tests."""

import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import json
from pathlib import Path

from catalog import Catalog, CatalogError
from scope import MODES, Git, ScopeError, require, resolve_scope, worktree_snapshot
from selection import explain


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--profile", required=True)
    parser.add_argument("--scope", choices=sorted(MODES), required=True)
    parser.add_argument("--base")
    parser.add_argument("--source")
    parser.add_argument("--executed")
    parser.add_argument("--snapshot-output-root")
    args = parser.parse_args()
    try:
        scope, snapshot = resolve_scope(args.root, args.scope, args.base, args.source, args.executed)
        destination = None
        if args.snapshot_output_root:
            destination = snapshot.materialize(args.root, args.snapshot_output_root)
            scope.update(materialized=True, snapshot_directory=str(destination))
        elif args.scope in {"committed", "hosted-pr", "hosted-commit", "local-staged"}:
            raise ScopeError(
                "Index/commit planning requires explicit snapshot materialization for matching catalog authority"
            )
        catalog = Catalog(destination or args.root)
        for name, digest in catalog.source_digests.items():
            require(
                name in snapshot.files and hashlib.sha256(snapshot.files[name]).hexdigest() == digest,
                "Catalog input differs from captured snapshot: " + name,
            )
        plan = catalog.plan(args.profile)
        result = explain(plan, catalog.units, catalog.documents["metadata"], scope)
        if destination:
            snapshot.verify(destination)
        else:
            current, index_digest, _ = worktree_snapshot(Git(args.root), windows=sys.platform == "win32")
            require(
                current.digest == snapshot.digest and index_digest == scope["provenance"]["index_digest"],
                "Source drift during catalog/impact planning",
            )
            require(
                Git(args.root).resolve("HEAD") == scope["provenance"]["executed_commit"],
                "HEAD drift during catalog/impact planning",
            )
        result["source_digests"] = catalog.source_digests
        code = 0
    except (ScopeError, CatalogError, OSError, ValueError) as error:
        result = {
            "contract": "ci-impact-explanation",
            "contract_version": 1,
            "status": "error",
            "classification": "scope" if isinstance(error, ScopeError) else "catalog",
            "error": str(error),
            "exit_code": 2,
            "execution_ready": False,
        }
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
