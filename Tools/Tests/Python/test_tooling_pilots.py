"""CI 3.3 pilots: tooling behavior; existing shared fixtures keep semantic authority."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load_tool(relative, name):
    before = sys.path[:]
    try:
        spec = importlib.util.spec_from_file_location(name, ROOT / relative)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = before


annotations = load_tool("Tools/Static/lint_work_annotations.py", "native_annotation_pilot")
compatibility = load_tool("Tools/Compatibility/run_compatibility.py", "native_normalization_pilot")
paths = load_tool("Tools/Runtime/Python/knowledge_framework/project_paths.py", "native_root_pilot")


@pytest.fixture
def policy():
    return annotations.load_policy(annotations.POLICY_PATH)


def test_git_inventory_preserves_nul_delimited_unicode_and_spaces(tmp_path, monkeypatch):
    def git(command, **kwargs):
        assert command == ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        assert kwargs["cwd"] == tmp_path
        return subprocess.CompletedProcess(command, 0, "a file.py\0unicodé.ps1\0".encode(), b"")

    monkeypatch.setattr(annotations.subprocess, "run", git)
    assert annotations.repository_inventory(tmp_path) == [tmp_path / "a file.py", tmp_path / "unicodé.ps1"]


def test_git_discovery_failure_is_not_empty_passing_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(
        annotations.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 128, b"", b"fixture Git failure"),
    )
    with pytest.raises(annotations.AnnotationPolicyFailure, match="fixture Git failure"):
        annotations.repository_inventory(tmp_path)


def test_requested_discovery_is_sorted_unique_and_rejects_missing_or_escaping_paths(tmp_path, monkeypatch):
    directory = tmp_path / "tools"
    directory.mkdir()
    files = [directory / name for name in ("b.py", "a.py")]
    for file in files:
        file.write_text("pass\n")
    monkeypatch.setattr(annotations, "repository_inventory", lambda root: files)
    assert annotations.requested_inventory(tmp_path, ["tools", "tools/a.py"]) == sorted(files)
    for value, message in [("missing.py", "does not exist"), ("../outside.py", "remain inside")]:
        with pytest.raises(annotations.AnnotationPolicyFailure, match=message):
            annotations.requested_inventory(tmp_path, [value])


def test_scan_excludes_policy_fixture_paths_and_reports_utf8_and_size_failures(tmp_path, monkeypatch, policy):
    from dataclasses import replace

    files = []
    for name, content in [
        ("Tools/Static/Fixtures/Work-Annotations/cache.py", b"# fixture ignored\n"),
        ("bad.py", b"\xff"),
        ("large.py", b"x" * 100),
    ]:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        files.append(file)
    monkeypatch.setattr(annotations, "repository_inventory", lambda root: files)
    checked, count, findings = annotations.scan_repository(tmp_path, replace(policy, maximum_file_bytes=32), [])
    assert checked == count == 0
    assert [row.code for row in findings] == ["unreadable-text", "file-size-limit"]
    assert [row.path for row in findings] == ["bad.py", "large.py"]


@pytest.mark.integration
@pytest.mark.parametrize("case", ["fixtures", "escaping-path", "invalid-policy"])
def test_annotation_cli_reports_fixture_success_and_invocation_failures(tmp_path, case):
    manifest = tmp_path / "Project_Config/project.yaml"
    manifest.parent.mkdir()
    manifest.write_text("schema_version: 1\n")
    command = [sys.executable, str(ROOT / "Tools/Static/lint_work_annotations.py"), "--root", str(tmp_path), "--json"]
    if case == "fixtures":
        command.append("--fixtures-only")
    elif case == "escaping-path":
        command.extend(["--path", "../outside.py"])
    else:
        invalid = tmp_path / "invalid-policy.json"
        document = json.loads(annotations.POLICY_PATH.read_text())
        document["schema_version"] = 99
        invalid.write_text(json.dumps(document))
        command.extend(["--policy", str(invalid), "--fixtures-only"])
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert result.stdout, result.stderr
    report = json.loads(result.stdout)
    assert result.returncode == (0 if case == "fixtures" else 1)
    assert report["status"] == ("passed" if case == "fixtures" else "failed")
    if case == "fixtures":
        assert report["fixture_cases"] == report["fixture_passed"] == 22
        assert report["files_checked"] == report["finding_count"] == 0
    else:
        assert ("remain inside" if case == "escaping-path" else "schema_version") in report["error"]


def test_normalization_changes_generated_fields_only_and_preserves_list_order(tmp_path):
    output = tmp_path / "output"
    first = {
        "generated_at": "first",
        "items": ["second", "first"],
        "authored": "time matters",
        "path": (output / "a.md").as_posix(),
    }
    second = {
        "path": (output / "a.md").as_posix(),
        "authored": "time matters",
        "items": ["second", "first"],
        "generated_at": "second",
    }
    expected = {
        "authored": "time matters",
        "generated_at": "<generated-at>",
        "items": ["second", "first"],
        "path": "<compat-output>/a.md",
    }
    assert compatibility.normalize_value(first, [output]) == compatibility.normalize_value(second, [output]) == expected
    changed = {**second, "authored": "changed content"}
    assert compatibility.normalize_value(changed, [output]) != expected
    assert first["generated_at"] == "first"


def test_json_and_binary_normalization_detect_real_content_changes(tmp_path):
    file = tmp_path / "result.json"
    file.write_bytes(b'\xef\xbb\xbf{"b":2,"a":1}')
    digest = compatibility.normalized_file_sha256(file, [])
    file.write_text('{"a":1,"b":2}\n')
    assert compatibility.normalized_file_sha256(file, []) == digest
    file.write_text('{"a":1,"b":3}')
    assert compatibility.normalized_file_sha256(file, []) != digest
    binary = tmp_path / "image.png"
    binary.write_bytes(b"\x00\xff")
    before = compatibility.normalized_file_sha256(binary, [])
    binary.write_bytes(b"\x00\xfe")
    assert compatibility.normalized_file_sha256(binary, []) != before


def test_tree_comparison_rejects_missing_and_changed_artifacts(tmp_path):
    roots = {name: tmp_path / name for name in ("python", "powershell7")}
    for root in roots.values():
        root.mkdir()
        (root / "page.md").write_text("same content\n")
    assert compatibility.compare_trees(roots)["normalized_match_count"] == 1
    (roots["powershell7"] / "page.md").write_text("changed content\n")
    with pytest.raises(compatibility.CompatibilityFailure):
        compatibility.compare_trees(roots)
    (roots["powershell7"] / "page.md").unlink()
    with pytest.raises(compatibility.CompatibilityFailure):
        compatibility.compare_trees(roots)


def test_root_api_explicit_precedence_and_failure_never_fall_back(tmp_path):
    explicit = tmp_path / "explicit"
    other = tmp_path / "other"
    for root in (explicit, other):
        (root / "Project_Config").mkdir(parents=True)
        (root / "Project_Config/project.yaml").write_text("schema_version: 1\n")
    cwd = Path.cwd()
    assert (
        paths.resolve_project_root(
            explicit, environment={"KNOWLEDGE_PROJECT_ROOT": str(other)}, current_directory=other
        )
        == explicit
    )
    with pytest.raises(RuntimeError, match="explicit root.*missing required manifest"):
        paths.resolve_project_root(
            tmp_path / "missing", environment={"KNOWLEDGE_PROJECT_ROOT": str(other)}, current_directory=other
        )
    assert Path.cwd() == cwd


def test_root_api_rejects_relative_environment_even_with_valid_current_root(tmp_path):
    (tmp_path / "Project_Config").mkdir()
    (tmp_path / "Project_Config/project.yaml").write_text("schema_version: 1\n")
    with pytest.raises(RuntimeError, match="must be an absolute path"):
        paths.resolve_project_root(environment={"KNOWLEDGE_PROJECT_ROOT": "relative"}, current_directory=tmp_path)
