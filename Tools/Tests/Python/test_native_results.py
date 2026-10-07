"""Native report truth, publication identity and adapter failure boundaries."""

import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    results = importlib.import_module("native_results")
    adapter = importlib.import_module("run_native_tests")
finally:
    sys.path[:] = before


def evidence(**changes):
    return {"framework": "pytest", "exit_code": 0, "collected": 1, "reports": [], **changes}


@pytest.mark.integration
@pytest.mark.parametrize("matching", [True, False])
def test_native_adapter_enforces_authoritative_python_patch(matching, monkeypatch):
    if not matching:
        monkeypatch.setattr(adapter.bootstrap, "read_json", lambda path: {"python": "0.0.0"})
    (ROOT / ".tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-version-", dir=ROOT / ".tmp") as owner:
        args = argparse.Namespace(
            runtime="python",
            executable=sys.executable,
            group="version-proof",
            path=[str(ROOT / "Tools/Tests/Python/test_bootstrap.py")],
            output_root=owner,
            filter="pure_runtime_lock_has_no_development_or_media_dependencies",
            timeout=30,
        )
        report = adapter.execute(args)
        if matching:
            assert report["status"] == "passed", report
            assert report["native_counts"]["collected"] == 1
        else:
            assert report["classification"] == "prerequisite" and report["exit_code"] == 1
            assert report["native_counts"] is None


def counts(**changes):
    return {"entries": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0, **changes}


def test_publication_preserves_raw_cases_and_unicode_diagnostics(tmp_path):
    raw = tmp_path / "raw.xml"
    original = (
        '<testsuite><testcase classname="source" name="é &amp; case" time="0.125">'
        "<failure>bad &lt;&amp;&gt; é</failure></testcase></testsuite>"
    )
    raw.write_text(original, encoding="utf-8")
    tree, rows, native = results.parse_junit(raw)
    target = tmp_path / "publish.xml"
    results.publication_xml(tree, "group.python", target)
    published, mapped, same_counts = results.parse_junit(target)
    assert raw.read_text(encoding="utf-8") == original
    assert len(rows) == len(mapped) == 1
    assert mapped[0]["classname"] == "group.python.source"
    assert mapped[0]["name"] == "é & case"
    assert mapped[0]["duration"] == 0.125
    assert published.find("testcase/failure").text == "bad <&> é"
    assert same_counts == native


@pytest.mark.parametrize(
    "content",
    [
        "<broken",
        "<other/>",
        '<!DOCTYPE testsuite [<!ENTITY x "unsafe">]><testsuite/>',
        '<testsuite><testcase time="NaN"/></testsuite>',
        '<testsuite><testcase time="-1"/></testsuite>',
        "<testsuite><testcase><failure/><skipped/></testcase></testsuite>",
    ],
    ids=["malformed", "root", "entity", "nonfinite", "negative", "ambiguous"],
)
def test_invalid_native_xml_is_rejected(tmp_path, content):
    path = tmp_path / "native.xml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises((ValueError, results.ET.ParseError)):
        results.parse_junit(path)


@pytest.mark.parametrize(
    "runtime,exit_code,phase,native,classification",
    [
        ("python", 1, evidence(exit_code=1), counts(failed=1), "assertion"),
        ("python", 2, evidence(exit_code=2, collection_errors=[{"diagnostic": "bad"}]), counts(), "collection"),
        ("python", 0, evidence(collected=0), counts(entries=0), "result-contract"),
        ("powershell7", 0, evidence(excluded=5), counts(skipped=1), "result-contract"),
        ("python", 0, evidence(reports=[{"xfail": True, "outcome": "skipped"}]), counts(), "result-contract"),
        ("python", 1, evidence(reports=[{"phase": "teardown", "outcome": "failed"}]), counts(errors=1), "cleanup"),
        ("python", 1, evidence(reports=[{"phase": "setup", "outcome": "failed"}]), counts(errors=1), "prerequisite"),
        ("powershell7", 1, evidence(prerequisite_failed=True), counts(), "prerequisite"),
        ("powershell7", 1, evidence(cleanup_failed=True), counts(), "cleanup"),
        ("python", 130, evidence(), counts(), "cancellation"),
        ("python", 0, evidence(collected=2), counts(), "result-contract"),
        ("python", 0, evidence(), counts(entries=2, passed=2), "result-contract"),
    ],
    ids=[
        "assertion",
        "collection",
        "empty",
        "skip",
        "xfail",
        "teardown",
        "setup",
        "pester-setup",
        "pester-cleanup",
        "cancel",
        "missing-case",
        "extra-case",
    ],
)
def test_failures_never_become_passes(runtime, exit_code, phase, native, classification):
    status, actual, aggregate_exit = results.classify(runtime, exit_code, phase, native)
    assert status != "passed"
    assert actual == classification
    assert aggregate_exit == (130 if classification == "cancellation" else 1)


def test_framework_inventory_is_separate_from_xml_entries():
    # pytest emits call and teardown failures as two XML entries for one collected identity.
    assert results.classify("python", 0, evidence(), counts()) == ("passed", None, 0)
    assert (
        results.classify(
            "python",
            1,
            evidence(reports=[{"phase": "teardown", "outcome": "failed"}]),
            counts(entries=2, failed=1, errors=1),
        )[1]
        == "cleanup"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"framework": "pester"},
        {"exit_code": 1},
        {"collected": -1},
        {"collected": True},
        {"reports": None},
        {"reports": [{"id": "a", "phase": "call"}, {"id": "a", "phase": "call"}]},
    ],
    ids=["framework", "exit", "negative", "boolean", "missing-report", "duplicate"],
)
def test_inconsistent_phase_evidence_is_rejected(changes):
    with pytest.raises(ValueError):
        results.validate_phase("python", 0, evidence(**changes))


def test_output_rejects_sibling_and_external_paths(tmp_path):
    for path in [tmp_path, ROOT / ".tmp-sibling", ROOT / "Tools"]:
        with pytest.raises(ValueError, match="owned checkout"):
            adapter.owned_output(path)


def test_pester_publication_removes_machine_root_without_adding_cases(tmp_path):
    source = tmp_path / "Tools/Tests/PowerShell/Owned.Tests.ps1"
    root = results.ET.Element("testsuite")
    results.ET.SubElement(root, "testcase", classname=str(source), name="owned & é", time="0.1")
    destination = tmp_path / "junit.xml"
    results.publication_xml(root, "group.powershell7", destination, tmp_path)
    _, cases, native = results.parse_junit(destination)
    assert cases[0]["classname"] == "group.powershell7.Tools/Tests/PowerShell/Owned.Tests.ps1"
    assert cases[0]["name"] == "owned & é" and native["entries"] == 1


def test_adapter_retains_framework_exit_and_rejects_missing_or_unpublishable_xml(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    source = tmp_path / "Tools/Tests/Python/test_owned.py"
    source.parent.mkdir(parents=True)
    source.write_text("", encoding="utf-8")
    args = argparse.Namespace(
        runtime="python",
        executable="synthetic",
        group="fixture",
        path=[str(source)],
        output_root=str(tmp_path / ".tmp/results"),
        filter=None,
        timeout=10,
    )
    launches = 0

    def child(command, **kwargs):
        nonlocal launches
        if "-I" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        launches += 1
        phase = Path(kwargs["env"]["NATIVE_PHASE_REPORT"])
        phase.write_text(json.dumps(evidence(exit_code=1 if launches == 1 else 0)), encoding="utf-8")
        if launches == 1:
            phase.with_name("native.xml").write_text(
                '<testsuite><testcase name="owned"><failure>actual diagnostic</failure></testcase></testsuite>',
                encoding="utf-8",
            )
        elif launches == 3:
            phase.with_name("native.xml").write_text(
                '<testsuite><testcase name="owned"/></testsuite>', encoding="utf-8"
            )
        return subprocess.CompletedProcess(command, 1 if launches == 1 else 0, "stdout é", "stderr é")

    monkeypatch.setattr(adapter.subprocess, "run", child)
    first = adapter.execute(args)
    second = adapter.execute(args)
    assert first["classification"] == "assertion" and first["child_exit_code"] == 1
    assert second["classification"] == "result-contract" and second["exit_code"] == 1
    assert first["run_directory"] != second["run_directory"]
    assert Path(first["run_directory"], "native.xml").is_file()
    assert Path(first["run_directory"], "stdout.log").read_text(encoding="utf-8") == "stdout é"
    assert Path(first["run_directory"], "stderr.log").read_text(encoding="utf-8") == "stderr é"

    def unpublishable(*args, **kwargs):
        raise ValueError("Synthetic native publication failure")

    monkeypatch.setattr(adapter, "publication_xml", unpublishable)
    third = adapter.execute(args)
    assert third["child_exit_code"] == 0 and third["exit_code"] == 1
    assert third["classification"] == "result-contract" and third["status"] == "error"


def test_missing_dependency_is_reported_without_installing(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    source = tmp_path / "Tools/Tests/Python/test_owned.py"
    source.parent.mkdir(parents=True)
    source.write_text("", encoding="utf-8")
    args = argparse.Namespace(
        runtime="python",
        executable="synthetic",
        group="fixture",
        path=[str(source)],
        output_root=str(tmp_path / ".tmp/results"),
        filter=None,
        timeout=10,
    )
    commands = []

    def child(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 1, "", "No module named pytest")

    monkeypatch.setattr(adapter.subprocess, "run", child)
    report = adapter.execute(args)
    assert len(commands) == 1 and "-I" in commands[0]
    assert report["classification"] == "prerequisite" and report["exit_code"] == 1
    assert report["native_counts"] is None


def test_finalization_failure_is_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    source = tmp_path / "Tools/Tests/Python/test_owned.py"
    source.parent.mkdir(parents=True)
    source.write_text("", encoding="utf-8")
    args = argparse.Namespace(
        runtime="python",
        executable="missing",
        group="fixture",
        path=[str(source)],
        output_root=str(tmp_path / ".tmp/results"),
        filter=None,
        timeout=10,
    )
    monkeypatch.setattr(
        adapter.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 1, "", "missing pytest")
    )
    write = Path.write_text

    def denied(path, *args, **kwargs):
        if path.name == "result.json":
            raise OSError("synthetic report write failure")
        return write(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", denied)
    report = adapter.execute(args)
    assert report["classification"] == "report" and report["exit_code"] == 1


def test_timeout_retains_partial_streams_without_inventing_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    source = tmp_path / "Tools/Tests/PowerShell/Owned.Tests.ps1"
    source.parent.mkdir(parents=True)
    source.write_text("", encoding="utf-8")
    args = argparse.Namespace(
        runtime="powershell7",
        executable="synthetic",
        group="fixture",
        path=[str(source)],
        output_root=str(tmp_path / ".tmp/results"),
        filter=None,
        timeout=0.1,
    )

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 0.1, output="partial é".encode(), stderr=b"partial failure")

    monkeypatch.setattr(adapter.subprocess, "run", timeout)
    report = adapter.execute(args)
    assert report["classification"] == "timeout" and report["exit_code"] == 1
    assert report["native_counts"] is None and report["child_exit_code"] is None
    assert Path(report["run_directory"], "stdout.log").read_text(encoding="utf-8") == "partial é"
    assert Path(report["run_directory"], "stderr.log").read_text(encoding="utf-8") == "partial failure"


def test_external_test_selection_is_rejected_before_launch(tmp_path, monkeypatch):
    source = tmp_path / "test_outside.py"
    source.write_text("", encoding="utf-8")
    args = argparse.Namespace(
        runtime="python",
        executable="unused",
        group="fixture",
        path=[str(source)],
        output_root=str(ROOT / ".tmp/results"),
        filter=None,
        timeout=10,
    )
    monkeypatch.setattr(
        adapter.subprocess, "run", lambda *args, **kwargs: pytest.fail("Invalid selection launched a child")
    )
    with pytest.raises(ValueError, match="runtime test root"):
        adapter.execute(args)
