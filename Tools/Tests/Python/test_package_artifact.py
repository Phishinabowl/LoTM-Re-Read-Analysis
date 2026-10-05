"""Permanent wheel-boundary regressions; these tests never install packages or download tools."""

import base64
import csv
import hashlib
import io
from pathlib import Path
import sys
import subprocess
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Tools/CI"))
import bootstrap  # noqa: E402
from package_artifact import inspect_wheel  # noqa: E402


@pytest.fixture
def contract():
    metadata, files = bootstrap.package_metadata()
    return metadata["project"], files, bootstrap.source_version()


def wheel_contents(contract):
    project, files, version = contract
    info = f"knowledge_framework-{version}.dist-info"
    members = {
        "knowledge_framework/" + name: (ROOT / "Tools/Runtime/Python/knowledge_framework" / name).read_bytes()
        for name in files
    }
    members.update(
        {
            info + "/METADATA": (
                f"Metadata-Version: 2.4\nName: knowledge-framework\nVersion: {version}\n"
                f"Requires-Python: {project['requires-python']}\n"
                "Requires-Dist: PyYAML<7,>=6.0.3\nLicense-File: LICENSE\n\n"
            ).encode(),
            info + "/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            info + "/top_level.txt": b"knowledge_framework\n",
            info + "/licenses/LICENSE": (ROOT / "LICENSE").read_bytes(),
        }
    )
    return info, members


def write_wheel(path, info, members, *, corrupt_record=False, duplicate=False):
    rows = []
    for name, value in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=").decode()
        rows.append([name, "sha256=" + digest, str(len(value))])
    rows.append([info + "/RECORD", "", ""])
    if corrupt_record:
        rows[0][1] = "sha256=wrong"
    stream = io.StringIO()
    csv.writer(stream).writerows(rows)
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in members.items():
            archive.writestr(name, value)
        archive.writestr(info + "/RECORD", stream.getvalue())
        if duplicate:
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr(info + "/METADATA", members[info + "/METADATA"])


def test_exact_runtime_wheel_and_license_are_accepted(tmp_path, contract):
    info, members = wheel_contents(contract)
    wheel = tmp_path / "runtime.whl"
    write_wheel(wheel, info, members)
    project, files, version = contract
    result = inspect_wheel(wheel, ROOT, version, files, project)
    assert len(result["members"]) == len(files) + 5
    assert set(result["runtime_sha256"]) == {"knowledge_framework/" + name for name in files}


def test_neutral_fixture_builder_needs_no_runtime_or_yaml_installation(tmp_path):
    helper = ROOT / "Tools/Compatibility/neutral_consumer.py"
    code = (
        "import importlib.util,pathlib,sys;"
        "spec=importlib.util.spec_from_file_location('neutral_fixture',sys.argv[1]);"
        "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);"
        "module.write_neutral_consumer(pathlib.Path(sys.argv[2]))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-c", code, str(helper), str(tmp_path)], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr
    assert "project_id: extraction-smoke" in (tmp_path / "Project_Config/project.yaml").read_text()
    assert not (tmp_path / "Tools/Runtime").exists()


@pytest.mark.parametrize(
    "unexpected",
    [
        "Project_Config/project.yaml",
        "Framework/framework.yaml",
        "Volumes/page.md",
        "Tools/Tests/test.py",
        ".env",
        "../secret",
    ],
)
def test_external_content_and_path_escape_members_are_rejected(tmp_path, contract, unexpected):
    info, members = wheel_contents(contract)
    members[unexpected] = b"forbidden"
    wheel = tmp_path / "runtime.whl"
    write_wheel(wheel, info, members)
    project, files, version = contract
    with pytest.raises(ValueError, match="member boundary"):
        inspect_wheel(wheel, ROOT, version, files, project)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-runtime",
        "changed-runtime",
        "changed-license",
        "wrong-version",
        "unexpected-dependency",
        "wrong-python",
        "extra",
        "binary-tag",
        "bad-record",
        "duplicate",
    ],
)
def test_corrupt_or_incompatible_artifacts_fail_closed(tmp_path, contract, mutation):
    info, members = wheel_contents(contract)
    if mutation == "missing-runtime":
        del members["knowledge_framework/project_paths.py"]
    elif mutation == "changed-runtime":
        members["knowledge_framework/project_paths.py"] += b"\n# changed\n"
    elif mutation == "changed-license":
        members[info + "/licenses/LICENSE"] = b"wrong license"
    elif mutation == "wrong-version":
        members[info + "/METADATA"] = members[info + "/METADATA"].replace(
            f"Version: {contract[2]}".encode(), b"Version: 99.0.0"
        )
    elif mutation == "unexpected-dependency":
        members[info + "/METADATA"] += b"Requires-Dist: pytest>=9\n"
        # Add it to the header block, rather than an ignored metadata body.
        members[info + "/METADATA"] = members[info + "/METADATA"].replace(b"\n\n", b"\n")
    elif mutation == "wrong-python":
        members[info + "/METADATA"] = members[info + "/METADATA"].replace(b">=3.14", b">=3.10")
    elif mutation == "extra":
        members[info + "/METADATA"] = members[info + "/METADATA"].replace(b"\n\n", b"\nProvides-Extra: media\n\n")
    elif mutation == "binary-tag":
        members[info + "/WHEEL"] = members[info + "/WHEEL"].replace(b"py3-none-any", b"cp314-cp314-win_amd64")
    wheel = tmp_path / "runtime.whl"
    write_wheel(wheel, info, members, corrupt_record=mutation == "bad-record", duplicate=mutation == "duplicate")
    project, files, version = contract
    with pytest.raises(ValueError):
        inspect_wheel(wheel, ROOT, version, files, project)
