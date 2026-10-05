"""Explicit maintenance: resolve published wheel digests for the exact adopted declarations."""

import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Tools/Commands/Environment"))
from dependency_requirements import read_requirements  # noqa: E402


def main():
    data = ROOT / "Tools/CI/Data"
    versions = json.loads((data / "runtime-versions.json").read_text())
    pins = {}
    for file in versions["python_declarations"].values():
        for platform in ("win32", "linux"):
            current, _ = read_requirements(ROOT / file, ROOT, platform=platform)
            for name, version in current.items():
                if name in pins and pins[name] != version:
                    raise ValueError(f"Conflicting version authorities: {name}")
                pins[name] = version
    if pins["pip"] != versions["pip"]:
        raise ValueError("pip declaration and baseline disagree")
    packages = {}
    for name, version in sorted(pins.items()):
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as response:
            metadata = json.load(response)
        files = []
        for row in metadata["urls"]:
            filename = row["filename"]
            if row["packagetype"] != "bdist_wheel" or row["yanked"]:
                continue
            supported_platform = filename.endswith(("-any.whl", "-win_amd64.whl")) or (
                "manylinux" in filename and filename.endswith("x86_64.whl")
            )
            supported_abi = "-py3-" in filename or "-py2.py3-" in filename or "-cp314-cp314-" in filename
            if supported_platform and supported_abi:
                files.append({"filename": filename, "sha256": row["digests"]["sha256"], "url": row["url"]})
        if not files:
            raise ValueError(f"No supported published wheel for {name} {version}")
        packages[name] = {
            "version": version,
            "requires_python": metadata["info"]["requires_python"],
            "requires_dist": metadata["info"]["requires_dist"] or [],
            "files": sorted(files, key=lambda row: row["filename"]),
        }
    lock = {
        "schema_version": 1,
        "interpreter": "CPython " + versions["python"],
        "platforms": ["windows-x86_64", "linux-x86_64-glibc"],
        "packages": packages,
    }
    (data / "python-wheel-lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Reviewed exact declarations resolved to {len(packages)} pinned package records. Inspect the lock diff.")


if __name__ == "__main__":
    main()
