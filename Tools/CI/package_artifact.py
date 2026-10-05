"""Inspect a runtime wheel against reviewed source, metadata and RECORD boundaries."""

import base64
import csv
from email.parser import BytesParser
import hashlib
import io
from pathlib import Path
import re
import zipfile


def dependency_identity(value):
    # The accepted package has one simple bound; compare ordering independently of setuptools.
    match = re.fullmatch(r"([A-Za-z0-9_.-]+)(.*)", value.replace(" ", ""))
    if match is None:
        raise ValueError("Invalid runtime dependency metadata")
    return match[1].lower().replace("_", "-"), tuple(sorted(match[2].split(",")))


def inspect_wheel(wheel, root, version, files, project):
    root = Path(root)
    info = f"knowledge_framework-{version}.dist-info"
    source = root / "Tools/Runtime/Python/knowledge_framework"
    expected = {"knowledge_framework/" + name: (source / name).read_bytes() for name in files}
    expected[info + "/licenses/LICENSE"] = (root / "LICENSE").read_bytes()
    auxiliary = {info + "/" + name for name in ("METADATA", "WHEEL", "top_level.txt", "RECORD")}
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate wheel members")
        if set(names) != set(expected) | auxiliary:
            raise ValueError(f"Wheel member boundary differs: {sorted(set(names) ^ (set(expected) | auxiliary))}")
        contents = {name: archive.read(name) for name in names}
    for name, value in expected.items():
        if contents[name] != value:
            raise ValueError("Wheel source/license content differs: " + name)
    metadata = BytesParser().parsebytes(contents[info + "/METADATA"])
    for field, value in {
        "Name": "knowledge-framework",
        "Version": version,
        "Requires-Python": project["requires-python"],
    }.items():
        if metadata.get_all(field) != [value]:
            raise ValueError("Wheel metadata differs: " + field)
    requirements = metadata.get_all("Requires-Dist", [])
    if sorted(map(dependency_identity, requirements)) != sorted(map(dependency_identity, project["dependencies"])):
        raise ValueError("Unexpected wheel runtime dependencies")
    if metadata.get_all("Provides-Extra") or metadata.get_all("License-File") != ["LICENSE"]:
        raise ValueError("Unexpected package extras/license declaration")
    wheel_metadata = BytesParser().parsebytes(contents[info + "/WHEEL"])
    if wheel_metadata.get_all("Tag") != ["py3-none-any"] or wheel_metadata.get("Root-Is-Purelib") != "true":
        raise ValueError("Unexpected binary wheel/platform tag")
    if contents[info + "/top_level.txt"].decode().strip() != "knowledge_framework":
        raise ValueError("Unexpected top-level package")
    records = list(csv.reader(io.StringIO(contents[info + "/RECORD"].decode())))
    if len(records) != len(names) or any(len(row) != 3 for row in records) or {row[0] for row in records} != set(names):
        raise ValueError("Wheel RECORD membership differs")
    for name, encoded, size in records:
        if name == info + "/RECORD":
            if encoded or size:
                raise ValueError("RECORD must not hash itself")
        else:
            digest = base64.urlsafe_b64encode(hashlib.sha256(contents[name]).digest()).rstrip(b"=").decode()
            if encoded != "sha256=" + digest or size != str(len(contents[name])):
                raise ValueError("Wheel RECORD digest/size differs: " + name)
    return {
        "version": version,
        "members": sorted(names),
        "runtime_sha256": {
            name: hashlib.sha256(value).hexdigest()
            for name, value in expected.items()
            if name.startswith("knowledge_framework/")
        },
        "metadata_sha256": hashlib.sha256(contents[info + "/METADATA"]).hexdigest(),
        "license_sha256": hashlib.sha256(contents[info + "/licenses/LICENSE"]).hexdigest(),
        "dependencies": requirements,
    }
