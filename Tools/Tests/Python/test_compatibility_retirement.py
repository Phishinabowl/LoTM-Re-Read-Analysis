"""Focused CI 2.4 registry, host, reporting and extraction regressions."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Tools/Compatibility"))
import run_compatibility as compatibility
import verify_framework_extraction as extraction


@pytest.fixture
def registry():
    return json.loads((ROOT / "Tools/Compatibility/compatibility.json").read_text(encoding="utf-8"))


def write_registry(tmp_path, document):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_registry_and_synthetic_reporting_keep_two_runtimes(tmp_path, registry):
    loaded = compatibility.load_registry(write_registry(tmp_path, registry))
    assert loaded["schema_version"] == 3
    assert loaded["runtimes"] == ["python", "powershell7"]
    assert len(loaded["checks"]) == 11
    generated = compatibility.create_compatibility_reporting_registry(ROOT, tmp_path)
    assert compatibility.load_registry(generated)["runtimes"] == loaded["runtimes"]


@pytest.mark.parametrize("version", [2, 3.0, True, "3", None, 99])
def test_rejects_obsolete_and_invalid_versions(tmp_path, registry, version):
    registry["schema_version"] = version
    expected = "Migrate to schema 3" if type(version) is int and version == 2 else "integer 3"
    with pytest.raises(compatibility.CompatibilityFailure, match=expected):
        compatibility.load_registry(write_registry(tmp_path, registry))


@pytest.mark.parametrize(
    "runtimes",
    [
        ["python"],
        ["powershell7", "python"],
        ["python", "powershell7", "powershell51"],
        ["python", "powershell7", "powershell7"],
        ["python", "unknown"],
        "python,powershell7",
    ],
)
def test_rejects_invalid_runtime_inventories(tmp_path, registry, runtimes):
    registry["runtimes"] = runtimes
    with pytest.raises(compatibility.CompatibilityFailure, match="runtimes must be"):
        compatibility.load_registry(write_registry(tmp_path, registry))


@pytest.mark.parametrize("field", ["checks", "profiles"])
def test_rejects_empty_catalog_surfaces(tmp_path, registry, field):
    registry[field] = [] if field == "checks" else {}
    with pytest.raises(compatibility.CompatibilityFailure, match="nonempty"):
        compatibility.load_registry(write_registry(tmp_path, registry))


@pytest.mark.parametrize(
    "text",
    [
        '{"schema_version":3,"schema_version":3}',
        '{"schema_version":3,"profiles":{"local":[],"local":[]}}',
    ],
)
def test_rejects_duplicate_json_keys(tmp_path, text):
    path = tmp_path / "duplicate.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(compatibility.CompatibilityFailure, match="Duplicate compatibility registry key"):
        compatibility.load_registry(path)


def test_old_registry_cli_fails_before_output_or_host_launch(tmp_path, registry):
    registry["schema_version"] = 2
    path = write_registry(tmp_path, registry)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "Tools/Compatibility/run_compatibility.py"),
            "--registry",
            str(path),
            "--summary-json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["selected_count"] == 0 and report["output_kept"] is False
    assert report["report_path"] is None
    assert report["failures"][0]["classification"] == "orchestration-failure"
    assert "Migrate to schema 3" in report["failures"][0]["excerpt"]


@pytest.mark.parametrize("module", [compatibility, extraction], ids=["compatibility", "extraction"])
@pytest.mark.parametrize(
    "edition,version,accepted",
    [
        ("Core", "7.4.0", True),
        ("Core", "7.6.6", True),
        ("Core", "7.3.12", False),
        ("Desktop", "5.1.19041.1", False),
        ("Desktop", "7.6.6", False),
        ("Core", "invalid", False),
    ],
)
def test_host_probe_checks_actual_edition_and_floor(monkeypatch, module, edition, version, accepted):
    looked_up = []

    def which(name):
        looked_up.append(name)
        return "fixture-pwsh"

    monkeypatch.setattr(module.shutil, "which", which)

    def probe(command, **kwargs):
        assert command[:2] == ["fixture-pwsh", "-NoProfile"]
        assert kwargs["timeout"] == 15
        return subprocess.CompletedProcess(command, 0, json.dumps({"edition": edition, "version": version}), "")

    monkeypatch.setattr(module.subprocess, "run", probe)
    invoke = lambda: (
        compatibility.find_runtime("powershell7") if module is compatibility else extraction.find_powershell_host()
    )
    if accepted:
        result = invoke()
        assert (result.executable if module is compatibility else result) == "fixture-pwsh"
    else:
        with pytest.raises(RuntimeError, match="PowerShell 7.4\\+ Core"):
            invoke()
    assert looked_up == ["pwsh"]


@pytest.mark.parametrize("module", [compatibility, extraction], ids=["compatibility", "extraction"])
@pytest.mark.parametrize("failure", ["missing", "invalid-json", "wrong-root", "nonzero", "timeout"])
def test_host_discovery_fails_actionably_without_desktop_fallback(monkeypatch, module, failure):
    monkeypatch.setattr(module.shutil, "which", lambda name: None if failure == "missing" else "fixture-pwsh")

    def probe(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 15)
        return subprocess.CompletedProcess(
            command,
            1 if failure == "nonzero" else 0,
            "[]" if failure == "wrong-root" else "invalid",
            "fixture host failure",
        )

    monkeypatch.setattr(module.subprocess, "run", probe)
    with pytest.raises(RuntimeError, match="PowerShell|runtime not found"):
        if module is compatibility:
            compatibility.find_runtime("powershell7")
        else:
            extraction.find_powershell_host()


def test_rejects_obsolete_runtime_even_without_registry(monkeypatch):
    def unexpected_lookup(name):
        raise AssertionError("Unknown host must not be discovered")

    monkeypatch.setattr(compatibility.shutil, "which", unexpected_lookup)
    assert compatibility.find_runtime("python").executable == sys.executable
    for identity in ("powershell51", "unknown"):
        with pytest.raises(compatibility.CompatibilityFailure, match="Unsupported"):
            compatibility.find_runtime(identity)
        with pytest.raises(compatibility.CompatibilityFailure, match="Unsupported"):
            compatibility.powershell_prefix(compatibility.Runtime(identity, "fixture"))


def test_portable_inventory_and_commands_remain_nine():
    assert len(extraction.PORTABLE_SUITES) == 9
    command = extraction.powershell_command("fixture-pwsh")
    assert command[:2] == ["fixture-pwsh", "-NoProfile"]
    assert "ExecutionPolicy" not in " ".join(command)
    for identity in extraction.PORTABLE_SUITES:
        assert f"'{identity}'" in command[-1]
    assert extraction.python_command().count("--suite") == 9


def portable_summary():
    return {
        "schema_version": 1,
        "profile": "selected",
        "failed": 0,
        "passed": 9,
        "suite_count": 9,
        "suites": [
            {"id": identity, "status": "passed", "summary": {"fixture": True}}
            for identity in extraction.PORTABLE_SUITES
        ],
    }


@pytest.mark.parametrize("mutation", ["schema", "omitted", "reordered", "failed", "bool-count"])
def test_extraction_cannot_pass_empty_stale_or_failed_inventory(mutation):
    summary = portable_summary()
    if mutation == "schema":
        summary["schema_version"] = True
    if mutation == "omitted":
        summary["suites"].pop()
    if mutation == "reordered":
        summary["suites"].reverse()
    if mutation == "failed":
        summary["suites"][0]["status"] = "failed"
    if mutation == "bool-count":
        summary["failed"] = False
    with pytest.raises(RuntimeError, match="all nine selected portable suites"):
        extraction.validate_portable_summary(summary)


@pytest.mark.parametrize("retain", [False, True])
@pytest.mark.parametrize("json_mode", [True, False], ids=["json", "human"])
def test_extraction_reports_cleanup_only_after_context_exit(tmp_path, monkeypatch, capsys, retain, json_mode):
    owned = tmp_path / "owned scratch"

    class OwnedDirectory:
        def __enter__(self):
            owned.mkdir()
            return str(owned)

        def __exit__(self, *args):
            if not retain:
                assert owned.resolve().is_relative_to(tmp_path.resolve())
                extraction.shutil.rmtree(owned)

    monkeypatch.setattr(extraction.tempfile, "TemporaryDirectory", lambda **kwargs: OwnedDirectory())
    monkeypatch.setattr(extraction, "parse_args", lambda: type("Args", (), {"root": tmp_path, "json": json_mode})())
    monkeypatch.setattr(extraction, "resolve_project_root", lambda *args, **kwargs: tmp_path)
    monkeypatch.setattr(extraction, "find_powershell_host", lambda: "fixture-pwsh")
    monkeypatch.setattr(extraction, "copy_framework_surface", lambda *args: 42)
    monkeypatch.setattr(extraction, "run_json", lambda *args: portable_summary())
    if retain:
        with pytest.raises(RuntimeError, match="remains after cleanup"):
            extraction.main()
        assert capsys.readouterr().out == ""
    else:
        assert extraction.main() == 0
        output = capsys.readouterr().out
        if json_mode:
            result = json.loads(output)
            assert result["runtimes"] == ["python", "powershell7"]
            assert result["schema_version"] == 1 and result["temporary_copy_removed_on_exit"] is True
        else:
            assert "two matching runtimes" in output and "three matching" not in output
        assert not owned.exists()


def test_reporting_counts_follow_completed_python_runs():
    parent = ROOT / ".tmp"
    parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="phase24-reporting-test-", dir=parent) as directory:
        output = Path(directory).resolve()
        assert output.is_relative_to(parent.resolve())
        result = compatibility.run_conformance_reporting_check(
            {"timeout_seconds": 60},
            [compatibility.Runtime("python", sys.executable)],
            ROOT,
            output,
        )
        assert result["success_cases"] == result["failure_cases"] == result["unsafe_report_path_cases"] == 1
        assert result["determinism_cases"] == 2 and result["runtimes"] == ["python"]
