"""Read-only CI catalog listing and full-profile planning."""

import sys

sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path

from catalog import Catalog, CatalogError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--catalog-directory")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--profile")
    parser.add_argument("--os", choices=["windows", "linux", "macos"])
    parser.add_argument("--available-runtime", action="append")
    parser.add_argument("--shard-plan")
    args = parser.parse_args()
    try:
        catalog = Catalog(args.root, args.catalog_directory)
        if args.list:
            if args.profile or args.shard_plan:
                raise CatalogError("Listing cannot also select a profile/shard plan")
            result = {
                "contract": "ci-catalog-list",
                "contract_version": 1,
                "profiles": list(catalog.profiles),
                "units": list(catalog.units),
                "shard_plans": list(catalog.shard_plans),
                "source_digests": catalog.source_digests,
            }
        else:
            result = catalog.plan(args.profile, args.os, args.available_runtime, args.shard_plan)
        exit_code = 0
    except (CatalogError, ValueError, OSError) as error:
        result = {
            "contract": "ci-execution-plan",
            "contract_version": 1,
            "status": "error",
            "classification": "catalog",
            "error": str(error),
            "exit_code": 2,
        }
        exit_code = 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
