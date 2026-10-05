"""Read-only Python readiness. Exact dependency metadata and imports must both work."""

import argparse
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys

from dependency_requirements import IMPORT_NAMES, read_requirements


def inspect(root, requirements):
    results = []
    supported = sys.version_info >= (3, 14)
    try:
        pins, _ = read_requirements(requirements, root)
        for name, version in pins.items():
            module_name = IMPORT_NAMES.get(name, name.replace("-", "_"))
            row = {"package": name, "module": module_name, "expected_version": version, "available": False}
            try:
                installed = importlib.metadata.version(name)
                row["installed_version"] = installed
                if installed != version:
                    raise ValueError(f"Expected {name} {version}, found {installed}")
                module = importlib.import_module(module_name)
                row.update(
                    available=True, import_origin=str(getattr(module, "__file__", "")), detail="Version/import OK"
                )
            except Exception as error:
                row["detail"] = str(error)
            results.append(row)
        ready = supported and all(row["available"] for row in results)
        message = (
            "Python interpreter and exact dependencies are usable."
            if ready
            else "Python 3.14+ and exact usable dependencies required."
        )
    except (ValueError, OSError) as error:
        ready, message = False, str(error)
    return {
        "ready": ready,
        "interpreter_supported": supported,
        "version": sys.version.split()[0],
        "executable": sys.executable,
        "requirements_path": str(Path(requirements).resolve()),
        "requirements_available": ready,
        "requirements": results,
        "message": message,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.root, args.requirements)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
