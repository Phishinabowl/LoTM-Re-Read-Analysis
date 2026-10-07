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
    github_shadow = importlib.import_module("github_shadow")
    ado_shadow = importlib.import_module("ado_shadow")
    publisher = importlib.import_module("publish_hosted")
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


def hosted_bundle(root, status="passed", runtime=None, shard="", host="github"):
    owner = root / ".tmp/ci-shadow/bundle/run-hosted-fixture"
    owner.mkdir(parents=True)
    report = record(owner, status, native=runtime is not None)
    report["provenance"]["executed_commit"] = "a" * 40
    if shard:
        # Admission uses the existing finalized shard provenance contract.
        report["provenance"]["shard_source"] = {"shard": shard}
    if runtime:
        row = report["results"][0]
        row.update(id="implementation/fixture::" + runtime, runtime=runtime)
        report["selection"]["candidate_ids"] = report["selection"]["selected_ids"] = [row["id"]]
        native = b'<testsuite tests="1"><testcase classname="fixture" name="native" time="0.2"/></testsuite>\n'
        reports.atomic_bytes(owner, "units/native/publication.xml", native)
        report["artifacts"] = [reports.fingerprint(owner, "units/native/publication.xml")]
        row["artifacts"] = ["units/native/publication.xml"]
    reports.finalize(owner, report)
    context = {
        "host": host,
        "profile": "synthetic",
        "executed": "a" * 40,
        "attempt": 2,
        "run_url": "https://github.com/fixture/repository/actions/runs/123"
        if host == "github"
        else "https://dev.azure.com/DreamtechADO/project/_build/results?buildId=123",
    }
    return owner, context


@pytest.mark.parametrize("status", ["passed", "failed", "timed-out", "blocked", "cancelled"])
def test_host_publication_preserves_execution_outcome_and_exact_custom_xml(tmp_path, status):
    owner, context = hosted_bundle(tmp_path, status)
    destination, receipt = publisher.admit(tmp_path, context)
    assert receipt["status"] == "admitted"
    assert receipt["execution_exit_code"] == (0 if status == "passed" else 1)
    assert (destination / receipt["xml"][0]["path"]).read_bytes() == (owner / "custom.xml").read_bytes()
    summary = (destination / "summary.md").read_text(encoding="utf-8")
    assert "ci-shadow-aggregate-all-2" in summary
    assert "](report.json)" not in summary
    assert "No trustworthy history" in summary  # Preserve the recorded selection reason.
    assert r"\[link\](x)" in summary  # Escaped diagnostic prose is not an artifact link.
    assert receipt["markdown_submission"] == "not-submitted"


@pytest.mark.parametrize("runtime,category", [("python", "python"), ("powershell7", "powershell")])
def test_host_publication_routes_native_cases_once_without_empty_custom_duplicates(tmp_path, runtime, category):
    owner, context = hosted_bundle(tmp_path, runtime=runtime)
    destination, receipt = publisher.admit(tmp_path, context)
    assert receipt["status"] == "admitted"
    assert len(receipt["xml"]) == 1
    entry = receipt["xml"][0]
    assert entry["category"] == category and entry["counts"]["entries"] == 1
    assert (destination / entry["path"]).read_bytes() == (owner / "units/native/publication.xml").read_bytes()


def test_host_shard_summary_does_not_publish_duplicate_test_cases(tmp_path):
    _, context = hosted_bundle(tmp_path, shard="fixture")
    _, receipt = publisher.admit(tmp_path, context, "fixture")
    assert receipt["status"] == "admitted" and receipt["xml"] == []


@pytest.mark.parametrize(
    "mutation", ["missing", "corrupt", "foreign-commit", "foreign-profile", "foreign-shard", "ambiguous"]
)
def test_host_publication_rejects_missing_corrupt_or_foreign_results_with_honest_summary(tmp_path, mutation):
    owner, context = hosted_bundle(tmp_path)
    if mutation == "missing":
        (owner / "finalized.json").unlink()
    elif mutation == "corrupt":
        (owner / "custom.xml").write_text("corrupt XML")
    elif mutation == "foreign-commit":
        context["executed"] = "b" * 40
    elif mutation == "foreign-profile":
        context["profile"] = "other"
    elif mutation == "ambiguous":
        (owner.parent / "run-foreign").mkdir()
    destination, receipt = publisher.admit(tmp_path, context, "wrong" if mutation == "foreign-shard" else "")
    assert receipt["status"] == "failed" and receipt["xml"] == []
    assert "No test coverage is inferred" in (destination / "summary.md").read_text()


def test_host_publication_absent_bundle_never_invents_passing_tests(tmp_path):
    _, receipt = publisher.admit(tmp_path, {"host": "github", "run_url": "https://github.com/fixture/run"})
    assert receipt["status"] == "failed" and receipt["execution_exit_code"] is None and receipt["xml"] == []


def test_host_summary_utf8_limit_retains_explicit_complete_artifact_pointer():
    content = publisher.hosted_markdown("🐺" * publisher.SUMMARY_LIMIT, "https://github.com/fixture/run", "artifact")
    assert len(content) <= publisher.SUMMARY_LIMIT
    assert "Summary display truncated" in content.decode("utf-8")


@pytest.mark.parametrize("host", ["github", "ado"])
def test_host_summary_submission_is_not_claimed_as_server_acceptance(tmp_path, capsys, host):
    _, context = hosted_bundle(tmp_path, host=host)
    destination, receipt = publisher.admit(tmp_path, context)
    summary_file = tmp_path / "host-summary"
    publisher.submit(destination, receipt, {"GITHUB_STEP_SUMMARY": str(summary_file)})
    assert receipt["server_acceptance"] == "requires hosted task/run evidence"
    if host == "github":
        assert summary_file.read_bytes() == (destination / "summary.md").read_bytes()
    else:
        assert "##vso[task.uploadsummary]" in capsys.readouterr().out
        assert "ci-shadow-aggregate-123" in (destination / "summary.md").read_text(encoding="utf-8")


def test_host_summary_write_failure_preserves_failed_execution(tmp_path):
    _, context = hosted_bundle(tmp_path, "failed")
    destination, receipt = publisher.admit(tmp_path, context)
    with pytest.raises(OSError):
        publisher.submit(destination, receipt, {"GITHUB_STEP_SUMMARY": str(tmp_path)})
    assert receipt["execution_exit_code"] == 1 and receipt["markdown_submission"] == "not-submitted"


def test_azure_failed_bundle_export_retains_publication_diagnostics(tmp_path, monkeypatch):
    owner, context = hosted_bundle(tmp_path, host="ado")
    (owner / "custom.xml").write_text("corrupt XML")
    destination, receipt = publisher.admit(tmp_path, context)
    reports.atomic_bytes(destination, "receipt.json", reports.encoded(receipt))
    monkeypatch.setattr(github_shadow, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["ado_shadow.py", "evidence"])
    with pytest.raises(ValueError):
        ado_shadow.main()
    transported = json.loads((tmp_path / ".tmp/ci-shadow/transport/publication/receipt.json").read_text())
    assert transported["status"] == "failed" and transported["xml"] == []


@pytest.mark.parametrize("submission_failed", [False, True])
def test_host_publication_cli_keeps_execution_and_submission_status_separate(tmp_path, monkeypatch, submission_failed):
    _, context = hosted_bundle(tmp_path, "failed")
    monkeypatch.setattr(sys, "argv", ["publish_hosted.py", "--root", str(tmp_path)])
    monkeypatch.setenv("SHADOW_CONTEXT", json.dumps(context))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path if submission_failed else tmp_path / "summary"))
    assert publisher.main() == (1 if submission_failed else 0)
    receipt = json.loads((tmp_path / ".tmp/ci-shadow/publication/receipt.json").read_text(encoding="utf-8"))
    assert receipt["execution_exit_code"] == 1
    assert receipt["status"] == ("failed" if submission_failed else "admitted")


def test_host_native_tasks_publish_only_admitted_aggregate_xml_after_execution_failures():
    import yaml

    worker = yaml.safe_load((ROOT / ".azuredevops/ci-worker.yml").read_text())
    steps = worker["jobs"][0]["steps"]
    publication = next(step for step in steps if step.get("name") == "Publication")
    assert publication["condition"] == "always()" and publication["timeoutInMinutes"] == 2
    tasks = next(
        step["${{ if eq(parameters.wave, 'aggregate') }}"]
        for step in steps
        if "${{ if eq(parameters.wave, 'aggregate') }}" in step
    )
    assert len(tasks) == 3
    for task, category in zip(tasks, ["python", "powershell", "custom"], strict=True):
        assert task["task"] == "PublishTestResults@2"
        assert task["condition"] == f"and(always(), eq(variables['Publication.{category}_enabled'], 'true'))"
        inputs = task["inputs"]
        assert inputs["testResultsFiles"] == f"$(Publication.{category}_files)"
        assert inputs["testResultsFormat"] == "JUnit"
        for key in (
            "mergeTestResults",
            "failTaskOnFailedTests",
            "failTaskOnFailureToPublishResults",
            "failTaskOnMissingResultsFile",
            "publishRunAttachments",
        ):
            assert inputs[key] is True
    assert all("continueOnError" not in step for step in steps + tasks)
    github = yaml.safe_load((ROOT / ".github/workflows/ci-shadow-worker.yml").read_text())
    github_steps = github["jobs"]["execute"]["steps"]
    summary_step = next(step for step in github_steps if "publish_hosted.py" in step.get("run", ""))
    assert summary_step["if"] == "${{ always() }}" and summary_step["timeout-minutes"] == 2
    assert all("continue-on-error" not in step for step in github_steps)


@pytest.mark.parametrize("status", ["passed", "failed"])
def test_github_transfer_copies_exact_admitted_inventory_preserving_owner_and_failure(tmp_path, status):
    owner = tmp_path / "run-shadow-transfer"
    owner.mkdir()
    report = record(owner, status)
    reports.finalize(owner, report)
    (owner / "source-not-for-upload.txt").write_text("private generated source")
    destination = tmp_path / "transfer"
    github_shadow.export_bundle(owner, destination)
    copied = destination / owner.name
    manifest = reports.verify_publication(copied)
    assert manifest["execution_exit_code"] == (0 if status == "passed" else 1)
    assert not (copied / "source-not-for-upload.txt").exists()
    (copied / "custom.xml").write_text("corrupt transferred XML")
    with pytest.raises(ValueError):
        reports.verify_publication(copied)


def test_github_missing_downloads_cannot_fall_back_to_full_sequential_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(github_shadow, "validate_context", lambda *args: None)
    monkeypatch.setattr(github_shadow, "matrices", lambda *args: ({"shards": [{"id": "required"}]}, {}, {}))
    monkeypatch.setattr(controller, "execute", lambda *args: pytest.fail("Missing shards launched execution"))
    with pytest.raises(ValueError, match="every approved shard"):
        github_shadow.execute({}, None, tmp_path / "absent-downloads")


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
