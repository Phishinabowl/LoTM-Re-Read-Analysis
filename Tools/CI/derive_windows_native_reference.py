"""Freeze paired qualified Windows inventories; no installer execution or automatic checksum update."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "Tools/CI/Data/python-windows-native-reference-spec.json"


def derive(archive, first, second, spec, *, timeout=60):
    deadline = time.monotonic() + timeout

    def budget():
        if time.monotonic() >= deadline:
            raise TimeoutError("Windows reference derivation deadline exhausted")

    budget()
    archive = Path(archive)
    if not archive.is_file() or archive.is_symlink() or archive.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("Plain bounded pinned archive required")
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != spec["identity"]["archive_sha256"]:
        raise ValueError("Pinned Windows provider archive differs")
    inventories, revisions, captures = [], [], []
    for owner in (Path(first), Path(second)):

        def read(name):
            budget()
            path = owner / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError("Plain bounded qualified evidence required")
            return json.loads(path.read_text(encoding="utf-8-sig"))

        capture, candidate, qualification = map(
            read, ("capture.json", "candidate.json", "candidate-qualification.json")
        )
        if (
            capture.get("os") != "windows"
            or capture.get("image_family") != "windows-2022"
            or capture.get("architecture") != "x64"
            or capture.get("requested_python") != spec["identity"]["python"]
            or type(candidate.get("schema_version")) is not int
            or candidate.get("schema_version") != 1
            or candidate.get("normalization") != "native-core-v1"
            or candidate.get("status") != "candidate-complete"
            or qualification.get("status") != "qualification-passed"
            or not isinstance(capture.get("executed_commit"), str)
            or not re.fullmatch("[0-9a-f]{40}", capture["executed_commit"])
            or capture.get("executed_commit") != qualification.get("executed_commit")
            or candidate.get("source_sha256") != capture["inventory"]["sha256"]
            or any(
                qualification.get(key) is not True
                for key in ("runtime_probe_verified", "environment_verified", "payload_unchanged")
            )
            or len(qualification.get("processes", [])) != 3
            or any(
                p.get("child_exit_code") != 0 or p.get("cleanup", {}).get("verified") is not True
                for p in qualification["processes"]
            )
        ):
            raise ValueError("Paired qualified Windows source evidence required")
        inventory = candidate["inventory"]
        frame = {key: inventory[key] for key in ("root_unix_mode", "entries")}
        digest = hashlib.sha256(json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        if (
            type(inventory["schema_version"]) is not int
            or inventory["schema_version"] != 3
            or inventory["root_unix_mode"] is not None
            or digest != spec["expected_inventory_sha256"]
            or inventory["sha256"] != digest
        ):
            raise ValueError("Reviewed Windows mode-aware inventory differs")
        inventories.append(inventory)
        revisions.append(capture["executed_commit"])
        captures.append(capture.get("capture_id"))
    if (
        inventories[0] != inventories[1]
        or revisions[0] != revisions[1]
        or captures != ["1", "2"]
        or Path(first).resolve() == Path(second).resolve()
    ):
        raise ValueError("Distinct same-source inventory pair required")
    budget()
    return {
        "contract": "ci-python-windows-native-reference",
        "schema_version": 1,
        "identity": spec["identity"],
        "inventory": inventories[0],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    result = derive(args.archive, args.first, args.second, spec)
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    digest = hashlib.sha256(encoded).hexdigest()
    if digest != spec["reference_sha256"]:
        raise ValueError("Output differs from reviewed reference bytes; no automatic checksum update")
    output = args.output.absolute()
    if ".." in output.parts or not output.is_relative_to(ROOT) or output.exists() or output.is_symlink():
        raise ValueError("Fresh repository-owned output required")
    for parent in output.parents:
        if parent == ROOT:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("Linked output parent refused")
    with output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"status": "derived", "entries": len(result["inventory"]["entries"]), "reference_sha256": digest}))


if __name__ == "__main__":
    main()
