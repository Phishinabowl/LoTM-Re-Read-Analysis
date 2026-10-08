"""Explicit read-only release-reference derivation; never extracts or executes an installer."""

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "Tools/CI/Data/python-linux-release-reference-spec.json"


def derive(archive, specification, *, timeout=60):
    if not math.isfinite(timeout) or timeout <= 0:
        raise TimeoutError("Release-reference derivation deadline exhausted")
    deadline = time.monotonic() + timeout

    def budget():
        if time.monotonic() >= deadline:
            raise TimeoutError("Release-reference derivation deadline exhausted")

    identity = specification["identity"]
    archive = Path(archive)
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("Plain pinned archive required")
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != identity["archive_sha256"]:
        raise ValueError("Pinned archive hash differs")
    rows, members = {}, {}
    with tarfile.open(archive, "r:gz") as stream:
        for member in stream:
            budget()
            path = member.name.removeprefix("./")
            if path == ".":
                if not member.isdir() or member.mode != 0o755:
                    raise ValueError("Expected release root mode")
                continue
            if (
                len(rows) >= 200000
                or member.size > 256 * 1024 * 1024
                or member.size < 0
                or member.sparse is not None
                or path in rows
                or not path
                or PurePosixPath(path).is_absolute()
                or any(part in ("", ".", "..") for part in path.split("/"))
                or re.search(r"[\\:\x00-\x1f]", path)
                or not (member.isfile() or member.isdir() or member.issym())
            ):
                raise ValueError("Unsafe, duplicate or unbounded archive member")
            kind = "file" if member.isfile() else "directory" if member.isdir() else "symlink"
            row = {"path": path, "kind": kind}
            if kind == "file":
                row["bytes"] = member.size
            if kind == "symlink":
                row["target"] = member.linkname
            else:
                if not 0 <= member.mode <= 0o777:
                    raise ValueError("Privileged archive mode")
                row["unix_mode"] = member.mode
            rows[path], members[path] = row, member
        library = "lib/python3.14"
        package = library + "/site-packages/pip"
        distributions = [
            path
            for path, row in rows.items()
            if row["kind"] == "directory"
            and re.fullmatch(re.escape(library) + r"/site-packages/pip-[0-9]+\.[0-9]+(?:\.[0-9]+)?\.dist-info", path)
        ]
        if len(distributions) != 1 or any(
            rows.get(path, {}).get("kind") != "file"
            for path in (package + "/__init__.py", distributions[0] + "/RECORD")
        ):
            raise ValueError("One complete release base-pip distribution required")
        if rows.get("setup.sh", {}).get("kind") != "file":
            raise ValueError("Reviewed installer script missing")
        omitted = set()
        for path, row in rows.items():
            budget()
            if (
                path == "setup.sh"
                or any(path == prefix or path.startswith(prefix + "/") for prefix in (package, distributions[0]))
                or path in ("bin/pip", "bin/pip3", "bin/pip3.14")
            ):
                omitted.add(path)
            elif row["kind"] == "file":
                match = re.fullmatch(
                    re.escape(library) + r"(?:/.*)?/__pycache__/([^/]+)\.cpython-314(?:\.opt-[12])?\.pyc", path
                )
                if match:
                    source = path.rsplit("/__pycache__/", 1)[0] + "/" + match[1] + ".py"
                    if rows.get(source, {}).get("kind") == "file":
                        omitted.add(path)
        for path, row in rows.items():
            budget()
            if path not in omitted and row["kind"] == "directory" and path.endswith("/__pycache__"):
                children = [name for name in rows if name.startswith(path + "/")]
                if children and all(name in omitted for name in children):
                    omitted.add(path)
        retained = {path: row for path, row in rows.items() if path not in omitted}
        for path, row in retained.items():
            budget()
            if row["kind"] != "symlink" and row["unix_mode"] not in (0o644, 0o755):
                raise ValueError("Unqualified retained release mode")
            if row["kind"] == "directory" and row["unix_mode"] != 0o755:
                raise ValueError("Unqualified release directory mode")
            if row["kind"] == "file":
                with stream.extractfile(members[path]) as data:
                    digest = hashlib.file_digest(data, "sha256").hexdigest()
                retained[path] = {
                    "path": path,
                    "kind": "file",
                    "bytes": row["bytes"],
                    "sha256": digest,
                    "unix_mode": row["unix_mode"],
                }
        aliases = {"bin/python": "python3.14", "bin/python314": "python3.14", "python": "./bin/python3.14"}
        for path, target in aliases.items():
            if path in retained:
                raise ValueError("Reviewed installer alias already supplied by archive")
            retained[path] = {"path": path, "kind": "symlink", "target": target}
        for path, row in retained.items():
            if row["kind"] == "symlink":
                target = row["target"]
                if (
                    PurePosixPath(target).is_absolute()
                    or ".." in target.split("/")
                    or re.search(r"[\\:\x00-\x1f]", target)
                    or retained.get(str(PurePosixPath(path).parent / target), {}).get("kind") != "file"
                ):
                    raise ValueError("Relative direct retained file link required")
        entries = [retained[path] for path in sorted(retained, key=lambda path: path.encode("utf-16-be"))]
        frame = {"root_unix_mode": 0o755, "entries": entries}
        digest = hashlib.sha256(json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        if digest != specification["expected_inventory_sha256"]:
            raise ValueError("Derived inventory differs from reviewed expected digest")
        budget()
        with archive.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != identity["archive_sha256"]:
                raise ValueError("Pinned archive changed during derivation")
        budget()
        return {
            "contract": "ci-python-linux-release-reference",
            "schema_version": 1,
            "identity": identity,
            "inventory": {"schema_version": 3, **frame, "sha256": digest},
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    specification = json.loads(SPEC.read_text(encoding="utf-8"))
    result = derive(args.archive, specification)
    encoded = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    if digest != specification["reference_sha256"]:
        raise ValueError("Reference bytes differ from reviewed file digest; no automatic update")
    output = args.output.absolute()
    if ".." in output.parts or not output.is_relative_to(ROOT) or output.exists() or output.is_symlink():
        raise ValueError("Fresh repository-owned output required")
    parent = output.parent
    while parent != ROOT:
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("Linked output owner refused")
        parent = parent.parent
    with output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"status": "derived", "entries": len(result["inventory"]["entries"]), "reference_sha256": digest}))


if __name__ == "__main__":
    main()
