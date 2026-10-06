"""Private report lifecycle fixtures; never run the production portfolio recursively."""

import copy
import importlib
import json
import os
from pathlib import Path
import sys
import subprocess
import threading
import time
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    reports = importlib.import_module("execution_reports")
    controller = importlib.import_module("run_ci")
    aggregate = importlib.import_module("aggregate_execution")
finally:
    sys.path[:] = before


def record(owner, status="passed", native=False):
    report = controller.empty_report("synthetic", owner.name)
    row = {
        "id": "conformance/fixture::python",
        "owner": "conformance",
        "runtime": "python",
        "status": status,
        "classification": None if status == "passed" else "synthetic",
        "elapsed_seconds": 1.25,
        "reasons": ["special <&|` [link](x) 🐺"],
        "native_counts": None,
        "artifacts": [],
        "diagnostics": {},
        "attempts": 1,
    }
    if native:
        row.update(
            id="implementation/fixture::python",
            owner="implementation",
            native_counts={"collected": 1, "passed": 1, "failed": 0, "errors": 0, "skipped": 0},
        )
    report["results"] = [row]
    report["selection"] = {
        "candidate_ids": [row["id"]],
        "selected_ids": [row["id"]],
        "unselected": [],
        "applied_mode": "full",
        "fallback_reasons": ["No trustworthy history"],
    }
    report["counts"] = {"candidate": 1, "selected": 1, "unselected": 0, "terminal": aggregate.counts([row])}
    report["status"], report["exit_code"] = ("passed", 0) if status == "passed" else ("failed", 1)
    report["canonical_guard"] = {"unchanged": True}
    report["budget"] = {"elapsed_seconds": 1.25}
    return report


@pytest.mark.parametrize("data", ['{"status":"passed","status":"failed"}', '{"duration":NaN}', '{"duration":Infinity}'])
def test_json_admission_rejects_duplicate_and_nonfinite_values(data):
    with pytest.raises(ValueError):
        reports.decode_json(data)


@pytest.mark.parametrize(
    "status,tag",
    [
        ("passed", None),
        ("failed", "failure"),
        ("error", "error"),
        ("timed-out", "error"),
        ("cancelled", "skipped"),
        ("blocked", "skipped"),
        ("skipped", "skipped"),
    ],
)
def test_custom_outcomes_preserve_granularity_and_xml_escaping(tmp_path, status, tag):
    report = record(tmp_path, status)
    report["results"][0]["reasons"].append("illegal control\x01 retained only in detailed JSON")
    root = ET.fromstring(reports.custom_xml(report, set()))
    assert len(list(root.iter("testcase"))) == 1
    case = root.find("testcase")
    assert case.get("classname") == "conformance.python"
    assert (case.find(tag) is not None) if tag else len(case) == 0
    assert case.get("time") == "1.250000"


def test_native_cases_publish_once_without_successful_group_case(tmp_path):
    owner = tmp_path / "run-native"
    owner.mkdir()
    report = record(owner, native=True)
    native = (
        b'<testsuite tests="1"><testcase classname="fixture.python" name="parameter[wolf]" time="0.2"/></testsuite>\n'
    )
    reports.atomic_bytes(owner, "units/native/publication.xml", native)
    report["artifacts"] = [reports.fingerprint(owner, "units/native/publication.xml")]
    report["results"][0]["artifacts"] = ["units/native/publication.xml"]
    manifest = reports.finalize(owner, report)
    assert manifest == reports.verify_publication(owner)
    assert manifest["xml"][0]["counts"]["entries"] == 1
    assert manifest["xml"][1]["counts"]["entries"] == 0
    assert (owner / "units/native/publication.xml").read_bytes() == native


@pytest.mark.parametrize(
    "mutation", ["missing", "changed", "duplicate", "foreign-id", "xml-count", "omitted-file", "omitted-xml"]
)
def test_publication_admission_rejects_stale_missing_foreign_or_duplicate_evidence(tmp_path, mutation):
    owner = tmp_path / "run-fixture"
    owner.mkdir()
    reports.finalize(owner, record(owner))
    path = owner / "publication-manifest.json"
    manifest = json.loads(path.read_text())
    if mutation == "missing":
        (owner / "custom.xml").unlink()
    elif mutation == "changed":
        (owner / "custom.xml").write_text("foreign XML")
    else:
        if mutation == "duplicate":
            manifest["files"].append(manifest["files"][0])
        elif mutation == "foreign-id":
            manifest["run_id"] = "run-foreign"
        elif mutation == "omitted-file":
            manifest["files"] = [entry for entry in manifest["files"] if entry["path"] != "summary.md"]
        elif mutation == "omitted-xml":
            manifest["xml"] = []
        else:
            manifest["xml"][0]["counts"]["passed"] += 1
        path.write_bytes(reports.encoded(manifest))
        (owner / "finalized.json").write_bytes(
            reports.encoded({"run_id": owner.name, "manifest": reports.fingerprint(owner, "publication-manifest.json")})
        )
    with pytest.raises(ValueError):
        reports.verify_publication(owner)


@pytest.mark.parametrize("name", ["../sibling.txt", "/outside.txt", "C:/outside.txt", "link\\file.txt", ""])
def test_atomic_reports_reject_unconfined_paths(tmp_path, name):
    with pytest.raises(ValueError):
        reports.atomic_bytes(tmp_path, name, b"foreign")


def test_atomic_reports_reject_foreign_overwrites_and_hardlinks(tmp_path):
    target = tmp_path / "report.json"
    target.write_bytes(b"user-owned")
    with pytest.raises(ValueError):
        reports.atomic_bytes(tmp_path, "report.json", b"changed")
    assert target.read_bytes() == b"user-owned"
    os.link(target, tmp_path / "alias.json")
    with pytest.raises(ValueError):
        reports.atomic_bytes(tmp_path, "report.json", b"changed", replace=True)


def test_linked_report_directory_is_rejected(tmp_path):
    (tmp_path / "foreign").mkdir()
    try:
        (tmp_path / "linked").symlink_to(tmp_path / "foreign", target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation unavailable; junction proof remains Windows integration")
    with pytest.raises(ValueError):
        reports.atomic_bytes(tmp_path, "linked/report.json", b"changed")


def test_projection_failure_never_admits_completion_and_retains_prior_evidence(tmp_path, monkeypatch):
    report = record(tmp_path)
    original = reports.atomic_bytes

    def fail(owner, name, data, **kwargs):
        if name == "summary.md":
            raise OSError("synthetic disk failure")
        return original(owner, name, data, **kwargs)

    monkeypatch.setattr(reports, "atomic_bytes", fail)
    with pytest.raises(OSError, match="disk failure"):
        reports.finalize(tmp_path, report)
    assert (tmp_path / "summary.json").exists()
    assert not (tmp_path / "finalized.json").exists()
    assert report["results"][0]["status"] == "passed"


def test_markdown_summary_full_json_and_utf8_agree_without_unbounded_excerpts(tmp_path):
    owner = tmp_path / "run-fixture"
    owner.mkdir()
    report = record(owner, "failed")
    report["failures"] = [{"id": None, "classification": "report", "excerpt": "🐺<&\r\n" * 1000}]
    reports.finalize(owner, report)
    detailed = json.loads((owner / "report.json").read_text(encoding="utf-8"))
    summary = json.loads((owner / "summary.json").read_text(encoding="utf-8"))
    assert len(detailed["failures"][0]["excerpt"]) > 4096
    assert summary["failures"][0]["excerpt_truncated"]
    assert len(summary["failures"][0]["excerpt"].encode()) <= 4096
    assert summary["counts"] == detailed["counts"]
    markdown = (owner / "summary.md").read_text(encoding="utf-8")
    assert "No trustworthy history" in markdown and "&lt;&amp;" in markdown
    for name in ("report.json", "summary.json", "summary.md", "custom.xml", "publication-manifest.json"):
        data = (owner / name).read_bytes()
        assert data.endswith(b"\n") and b"\r\n" not in data and not data.startswith(b"\xef\xbb\xbf")


def test_recovery_retains_terminal_units_and_marks_unreported_coverage(tmp_path):
    source, destination = tmp_path / "run-source", tmp_path / "run-recovered"
    source.mkdir()
    report = record(source)
    row = copy.deepcopy(report["results"][0])
    report["results"] = []
    report["selection"]["selected_ids"].append("conformance/later::python")
    report["selection"]["candidate_ids"].append("conformance/later::python")
    report["counts"]["candidate"] = 2
    journal = reports.Journal(source, report)
    journal.event("plan", report)
    journal.event("unit-terminal", {"result": row, "artifacts": []})
    journal.close()
    with (source / "events.jsonl").open("ab") as stream:
        stream.write(b'{"sequence":4')
    result = reports.recover(source, destination)
    assert [row["status"] for row in result["results"]] == ["passed", "blocked"]
    assert result["results"][1]["child_exit_code"] is None
    assert result["results"][1]["deadline_seconds"] is None
    assert result["exit_code"] == 1 and not result["complete"]
    assert not result["cleanup"]["verified"] and result["canonical_guard"]["unchanged"] is None
    assert reports.verify_publication(destination)["complete"] is False
    assert (source / "events.jsonl").exists()


@pytest.mark.parametrize("mutation", ["sequence", "record", "duplicate-unit"])
def test_recovery_rejects_corrupt_journal(tmp_path, mutation):
    source = tmp_path / "run-source"
    source.mkdir()
    report = record(source)
    row = copy.deepcopy(report["results"][0])
    report["results"] = []
    journal = reports.Journal(source, report)
    journal.event("unit-terminal", {"result": row, "artifacts": []})
    if mutation == "duplicate-unit":
        journal.event("unit-terminal", {"result": row, "artifacts": []})
    journal.close()
    if mutation == "record":
        (source / "records/000002.json").write_text("changed")
    elif mutation == "sequence":
        lines = (source / "events.jsonl").read_text().splitlines()
        changed = json.loads(lines[1])
        changed["sequence"] = 10
        (source / "events.jsonl").write_text(lines[0] + "\n" + json.dumps(changed) + "\n")
    with pytest.raises(ValueError):
        reports.recover(source, tmp_path / "run-recovered")


def test_unit_observer_records_cancellation_and_preserves_completed_evidence():
    seen, cancel = [], threading.Event()

    class Budget:
        def admit(self, seconds):
            class Lease:
                def verify(self):
                    pass

            return Lease()

    plan = {
        "units": [
            {
                "execution_id": "conformance/" + name + "::python",
                "runtimes": ["python"],
                "deadline_seconds": 2,
                "depends_on": [],
                "availability": "declared",
                "reasons": [],
            }
            for name in ("first", "later")
        ]
    }

    def dispatch(*args):
        cancel.set()
        return {"status": "passed", "classification": None}

    rows, _, _ = aggregate.execute_units(
        plan, dispatch, Budget(), cancel, lambda: None, observer=lambda row: seen.append(copy.deepcopy(row))
    )
    assert [row["status"] for row in seen] == ["passed", "cancelled"]
    assert rows == seen and rows[1]["attempts"] == 0


@pytest.mark.parametrize("status", ["timed-out", "cancelled"])
def test_partial_native_cases_remain_real_without_invented_selected_counts(tmp_path, status):
    report = record(tmp_path, status)
    row = report["results"][0]
    row.update(owner="implementation", id="implementation/fixture::python")
    report["selection"].update(candidate_ids=[row["id"]], selected_ids=[row["id"]])
    source = tmp_path / "partial.xml"
    source.write_bytes(b'<testsuite><testcase name="observed" classname="fixture"/></testsuite>')
    row["retained_native"] = {"native.xml": str(source)}
    report["artifacts"] = aggregate.persist_units([row], tmp_path)
    manifest = reports.finalize(tmp_path, report)
    assert manifest["xml"][0]["partial"] is True
    assert manifest["xml"][0]["counts"]["entries"] == 1
    assert row["native_counts"] is None
    assert manifest["xml"][1]["counts"]["errors" if status == "timed-out" else "skipped"] == 1


@pytest.mark.integration
def test_hard_killed_writer_recovers_fsynced_plan_without_claiming_cleanup(tmp_path):
    source = tmp_path / "run-source"
    source.mkdir()
    report = record(source)
    report["results"] = []
    (tmp_path / "input.json").write_bytes(reports.encoded(report))
    code = (
        "import sys,json,pathlib,time;sys.path.insert(0,sys.argv[1]);from execution_reports import Journal;"
        "root=pathlib.Path(sys.argv[2]);value=json.loads(pathlib.Path(sys.argv[3]).read_text());"
        "journal=Journal(root,value);journal.event('plan',value);(root/'ready').write_text('ready');time.sleep(30)"
    )
    child = subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", code, str(ROOT / "Tools/CI"), str(source), str(tmp_path / "input.json")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not (source / "ready").exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert (source / "ready").exists()
        child.kill()
        child.communicate(timeout=5)
        report = reports.recover(source, tmp_path / "run-recovery")
        assert report["results"][0]["status"] == "blocked"
        assert report["results"][0]["attempts"] == 0
        assert report["cleanup"]["verified"] is False
        assert report["exit_code"] == 1 and report["complete"] is False
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=5)


def test_concurrent_run_owners_have_separate_exact_manifests(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    def run(index):
        owner = tmp_path / ("run-" + str(index))
        owner.mkdir()
        reports.finalize(owner, record(owner))
        return reports.verify_publication(owner)["run_id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, range(2))) == ["run-0", "run-1"]


@pytest.mark.parametrize("mutation", ["counts", "unknown", "native-missing", "guard", "unit-artifact"])
def test_finalization_rejects_contradictory_record_without_rewriting_results(tmp_path, mutation):
    report = record(tmp_path)
    if mutation == "counts":
        report["counts"]["selected"] = 2
    elif mutation == "unknown":
        report["foreign"] = True
    elif mutation == "native-missing":
        report["results"][0]["native_counts"] = {"passed": 1}
    elif mutation == "guard":
        report["canonical_guard"]["unchanged"] = None
    else:
        report["results"][0]["artifacts"] = ["missing.log"]
    with pytest.raises(ValueError):
        reports.finalize(tmp_path, report)
    assert report["results"][0]["status"] == "passed"
    assert not (tmp_path / "finalized.json").exists()
