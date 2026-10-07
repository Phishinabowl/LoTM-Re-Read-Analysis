"""Cohort placement keeps independent child execution and original publication contracts."""

import argparse
import copy
import importlib
import json
import signal
import shutil
import subprocess
import os
import sys
from pathlib import Path
import threading
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    record = importlib.import_module("Tools.Tests.Python.test_ci_reports").record
    cohort = importlib.import_module("ado_cohort")
    publisher = importlib.import_module("publish_hosted")
    reports = importlib.import_module("execution_reports")
finally:
    sys.path[:] = before


@pytest.fixture
def experiment(tmp_path, monkeypatch):
    monkeypatch.setattr(cohort.transport, "ROOT", tmp_path)
    context = {
        "host": "ado",
        "profile": "synthetic",
        "executed": "a" * 40,
        "run_url": "https://dev.azure.com/DreamtechADO/project/_build/results?buildId=123",
    }
    group = {
        "id": "cohort-0",
        "os": "windows",
        "shards": ["first", "second"],
        "preparation": "core",
        "declared_shard_seconds": 60,
        "preserved_child_setup_seconds": 1200,
    }
    plan = {"id": "fixture-plan", "shards": [{"id": name, "budget": {"total_seconds": 30}} for name in group["shards"]]}
    monkeypatch.setattr(cohort, "admitted_cohort", lambda *a: (copy.deepcopy(group), copy.deepcopy(plan)))
    monkeypatch.setattr(
        cohort.transport,
        "execution_arguments",
        lambda context, shard, inputs, **kw: argparse.Namespace(
            python=sys.executable, root=str(tmp_path), shard=shard, output_root=kw["output_root"]
        ),
    )
    script = tmp_path / "fixture_worker.py"
    script.write_text(
        "import json, pathlib, sys\n"
        f"sys.path.insert(0, {str(ROOT / 'Tools/CI')!r})\n"
        "from execution_reports import finalize\n"
        "value=lambda flag: sys.argv[sys.argv.index(flag)+1]\n"
        "root=pathlib.Path(value('--root')); shard=value('--shard')\n"
        "template=json.loads((root/('template-'+shard+'.json')).read_text())\n"
        "mode=template.pop('fixture_mode')\n"
        "if mode=='crash': raise SystemExit(2)\n"
        "owner=root/value('--output-root')/template['run_id']; owner.mkdir(parents=True)\n"
        "finalize(owner, template)\n"
        "if mode=='tamper': (owner/'report.json').write_text('corrupt')\n"
        "print('child diagnostic '+shard, flush=True)\n"
        "raise SystemExit(2 if mode=='misexit' else template['exit_code'])\n",
        encoding="utf-8",
    )
    original = cohort.child_command
    monkeypatch.setattr(cohort, "child_command", lambda args: [args.python, str(script)] + original(args)[2:])

    def write(name, mode):
        owner = tmp_path / ("run-fixture-" + name)
        report = record(owner, "failed" if mode == "failed" else "passed")
        report["profile"] = context["profile"]
        report["provenance"].update(
            executed_commit=context["executed"], shard_source={"shard": name, "shard_plan": plan["id"]}
        )
        report["fixture_mode"] = mode
        (tmp_path / ("template-" + name + ".json")).write_text(json.dumps(report), encoding="utf-8")

    return tmp_path, context, write


@pytest.mark.integration
@pytest.mark.parametrize("first", ["passed", "failed", "crash", "tamper", "misexit"])
def test_owned_children_continue_after_failure_with_exact_original_bundles(experiment, first):
    root, context, write = experiment
    write("first", first)
    write("second", "passed")
    result, stage = cohort.run_cohort(root, context, "cohort-0", root / ".tmp/absent")
    assert [row["shard"] for row in result["shards"]] == ["first", "second"]
    assert result["shards"][1]["status"] == "passed"
    assert result["exit_code"] == (0 if first == "passed" else 1)
    assert result["adopted"] is False
    paths = sorted(stage.rglob("shard-result.json"))
    assert len(paths) == (2 if first in {"passed", "failed"} else 1)
    for path in paths:
        manifest = reports.verify_publication(path.parent)
        assert manifest["execution_exit_code"] == (1 if first == "failed" and "first" in path.parts else 0)
    receipts = list(stage.rglob("receipt.json"))
    assert all(json.loads(path.read_text())["xml"] == [] for path in receipts)  # Aggregate alone publishes cases.
    assert len(list(stage.rglob("stdout.bin"))) == 2
    assert "child diagnostic second" in next((stage / "processes/second").glob("stdout.bin")).read_text()
    assert not any(path.name == "source" for path in stage.rglob("*"))
    with pytest.raises(FileExistsError):
        cohort.run_cohort(root, context, "cohort-0", root / ".tmp/absent")


@pytest.mark.integration
def test_manual_launch_fault_runs_real_child_then_continues_without_invented_coverage(experiment, monkeypatch):
    root, context, write = experiment
    context.update(event="Manual", placement="cohort-smoke", profile="full-verification", pr=None)
    context["cohort_qualification"] = "launch-failure"
    monkeypatch.setattr(
        cohort.ado_shadow, "validate_placement", lambda *args: [{"id": "cohort-0", "shards": ["first", "second"]}]
    )
    write("first", "passed")
    write("second", "passed")
    result, stage = cohort.run_cohort(root, context, "cohort-0", root / ".tmp/absent")
    first, second = result["shards"]
    assert result["status"] == "failed" and result["exit_code"] == 1
    assert result["qualification"] == {"scenario": "launch-failure", "shard": "first"}
    assert first["process"]["child_exit_code"] == 2 and first["process"]["cleanup"]["verified"]
    assert "run_id" not in first
    assert second["status"] == "passed", second
    assert not (stage / "first/bundle").exists()
    assert len(list(stage.rglob("shard-result.json"))) == 1
    assert "Deliberate cohort qualification" in (stage / "processes/first/stdout.bin").read_text()


def test_cancelled_cohort_never_launches_or_invents_later_coverage(experiment):
    root, context, _ = experiment
    cancel = threading.Event()
    cancel.set()
    handlers = {name: signal.getsignal(name) for name in (signal.SIGINT, signal.SIGTERM)}
    result, stage = cohort.run_cohort(root, context, "cohort-0", root / ".tmp/absent", cancel=cancel)
    assert result["exit_code"] == 130 and result["status"] == "cancelled"
    assert all(row["status"] == "cancelled" and "process" not in row for row in result["shards"])
    assert list(stage.rglob("shard-result.json")) == []
    assert handlers == {name: signal.getsignal(name) for name in handlers}


@pytest.mark.integration
def test_inflight_cancellation_terminates_owned_child_and_stops_later_shards(experiment, monkeypatch):
    root, context, _ = experiment
    ready = root / "ready"
    cancel = threading.Event()
    script = f"import pathlib,time; pathlib.Path({str(ready)!r}).write_text('ready'); time.sleep(300)"
    monkeypatch.setattr(cohort, "child_command", lambda args: [args.python, "-c", script])

    def cancel_when_ready():
        deadline = time.monotonic() + 15
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        cancel.set()

    watcher = threading.Thread(target=cancel_when_ready)
    watcher.start()
    try:
        result, stage = cohort.run_cohort(root, context, "cohort-0", root / ".tmp/absent", cancel=cancel)
    finally:
        watcher.join(16)
    assert ready.exists() and not watcher.is_alive()
    assert result["exit_code"] == 130 and result["status"] == "cancelled"
    assert result["shards"][0]["process"]["cleanup"]["verified"] is True
    assert result["shards"][1]["status"] == "cancelled" and "process" not in result["shards"][1]
    assert list(stage.rglob("shard-result.json")) == []


def test_cohort_children_receive_explicit_environment_without_host_credentials(monkeypatch):
    for name in (
        "SYSTEM_ACCESSTOKEN",
        "GITHUB_TOKEN",
        "PYTHONPATH",
        "PYTHONHOME",
        "SHADOW_CONTEXT",
        "NPM_CONFIG_TOKEN",
    ):
        monkeypatch.setenv(name, "synthetic-sentinel")
    environment = cohort.child_environment()
    assert "synthetic-sentinel" not in environment.values()
    assert environment["GIT_TERMINAL_PROMPT"] == "0" and environment["PYTHONNOUSERSITE"] == "1"


@pytest.mark.parametrize("cause", ["timeout", "cancel", "cleanup"])
def test_owned_process_lifecycle_faults_preserve_honest_exit_and_later_admission(experiment, monkeypatch, cause):
    root, context, write = experiment
    write("second", "passed")
    original = cohort.run_process
    invoked = []

    def process(command, **options):
        invoked.append(command)
        if len(invoked) > 1:
            return original(command, **options)
        directory = options["output_parent"] / "process-synthetic"
        directory.mkdir()
        if cause == "cancel":
            options["cancel"].set()
        return {
            "directory": str(directory),
            "status": "cancelled" if cause == "cancel" else "timed-out",
            "child_exit_code": None,
            "cleanup": {"verified": cause != "cleanup"},
        }

    monkeypatch.setattr(cohort, "run_process", process)
    result, stage = cohort.run_cohort(root, context, "cohort-0", root / ".tmp/absent")
    assert result["exit_code"] == (130 if cause == "cancel" else 1)
    assert result["shards"][0]["status"] in {"timed-out", "cancelled"}
    assert result["shards"][1]["status"] == ("cancelled" if cause == "cancel" else "passed")
    assert len(list(stage.rglob("shard-result.json"))) == (0 if cause == "cancel" else 1)


def test_original_allowance_is_not_shortened_to_fit_a_cohort(experiment, monkeypatch):
    root, context, _ = experiment
    for scenario in ("initial", "preflight"):
        private = root / scenario
        private.mkdir()
        monkeypatch.setattr(cohort.transport, "ROOT", private)
        group = {
            "id": "cohort-0",
            "shards": ["first"],
            "preparation": "core",
            "declared_shard_seconds": 1 if scenario == "initial" else 200,
            "preserved_child_setup_seconds": 600,
        }
        plan = {"id": "fixture-plan", "shards": [{"id": "first", "budget": {"total_seconds": 200}}]}
        monkeypatch.setattr(cohort, "admitted_cohort", lambda *a: (group, plan))
        clock = [0]
        monkeypatch.setattr(cohort.time, "monotonic", lambda: clock[0])

        def preflight(*args, **kwargs):
            clock[0] = 100
            return argparse.Namespace()

        monkeypatch.setattr(cohort.transport, "execution_arguments", preflight)
        result, stage = cohort.run_cohort(private, context, "cohort-0", private / ".tmp/absent")
        assert result["exit_code"] == 1 and result["shards"][0]["status"] == "blocked"
        assert list(stage.rglob("shard-result.json")) == []


@pytest.mark.parametrize("bad", ["../escape", ".tmp/foreign", ".tmp/ci-shadow/cohorts/../escape"])
def test_publication_owner_cannot_escape_reviewed_cohort_scratch(tmp_path, bad):
    with pytest.raises(ValueError):
        publisher.admit(tmp_path, {"host": "ado"}, "fixture", worker_owner=bad)


def test_shared_preparation_cannot_downgrade_a_complete_shard(tmp_path, monkeypatch):
    monkeypatch.setattr(cohort.transport, "ROOT", tmp_path)
    monkeypatch.setattr(cohort.transport, "validate_context", lambda *a: {})
    monkeypatch.setattr(
        cohort.transport, "matrices", lambda *a: ({"shards": [{"id": "fixture", "depends_on": []}]}, {}, {})
    )
    monkeypatch.setattr(cohort.transport.bootstrap, "read_json", lambda *a: {})
    with pytest.raises(ValueError, match="downgrade"):
        cohort.transport.execution_arguments({}, "fixture", tmp_path / ".tmp/absent", preparation="core")


@pytest.mark.parametrize("mutation", ["identity", "os", "roles", "source"])
def test_cohort_admission_rejects_unknown_placement_host_role_map_and_source(monkeypatch, mutation):
    plan, _, _ = cohort.transport.matrices(ROOT, {"profile": "full-verification"})
    proposal = cohort.ado_shadow.cohort_plan(ROOT, "full-verification")
    row = next(row for row in proposal["cohorts"] if row["os"] == cohort.platform.system().lower())
    context = {
        "host": "ado",
        "profile": "full-verification",
        "preparation_roles": cohort.transport.preparation_roles(ROOT, plan),
    }
    monkeypatch.setattr(cohort.transport, "validate_context", lambda *a: {})
    if mutation == "source":

        def reject(*_):
            raise ValueError("Synthetic source mismatch")

        monkeypatch.setattr(cohort.transport, "validate_context", reject)
    elif mutation == "os":
        monkeypatch.setattr(cohort.platform, "system", lambda: "Unknown")
    elif mutation == "roles":
        context["preparation_roles"] = {}
    with pytest.raises(ValueError):
        cohort.admitted_cohort(ROOT, context, "cohort-999" if mutation == "identity" else row["id"])


@pytest.mark.parametrize(
    "required,shared",
    [("core", "core"), ("core", "build"), ("core", "complete"), ("build", "build"), ("complete", "complete")],
)
def test_shared_role_retains_required_receipts_and_explicit_child_inputs(tmp_path, monkeypatch, required, shared):
    monkeypatch.setattr(cohort.transport, "ROOT", tmp_path)
    monkeypatch.setattr(cohort.transport, "validate_context", lambda *a: {})
    monkeypatch.setattr(cohort.transport, "preparation_roles", lambda *a: {"fixture": required})
    monkeypatch.setattr(
        cohort.transport,
        "matrices",
        lambda *a: ({"id": "fixture-plan", "shards": [{"id": "fixture", "depends_on": []}]}, {}, {}),
    )
    setup = {
        "status": "passed",
        "python": {"key": "fixture", "executable": sys.executable},
        "powershell": {"module_path": "fixture", "executable": "fixture"},
    }
    documents = {
        "bootstrap.json": setup,
        "pilot.json": {"exit_code": 0, "payload_profile": shared, "source_revision": "a" * 40},
        "build.json": {"status": "passed", "package": {"wheel": "fixture.whl"}},
        "python-wheel-lock.json": {"packages": {"pyyaml": {}}},
        "tools.json": {"actionlint": None},
    }
    monkeypatch.setattr(cohort.transport.bootstrap, "read_json", lambda path: documents[Path(path).name])
    monkeypatch.setattr(
        cohort.transport.bootstrap, "wheel_for", lambda *a: {"filename": "yaml.whl", "sha256": "verified"}
    )
    monkeypatch.setattr(cohort.transport.bootstrap, "digest", lambda *a: "verified")
    context = {
        "preparation_roles": {"fixture": required},
        "executed": "a" * 40,
        "profile": "fixture",
        "scope": "hosted-commit",
        "base": None,
        "source": "a" * 40,
        "host": "ado",
        "run_url": "fixture",
    }
    args = cohort.transport.execution_arguments(
        context,
        "fixture",
        tmp_path / ".tmp/absent",
        preparation=shared,
        output_root=".tmp/ci-shadow/cohorts/cohort-0/shards/fixture/execution",
    )
    assert args.python == sys.executable and args.wheel == (None if shared == "core" else "fixture.whl")
    assert args.shard == "fixture" and args.shard_results == []
    command = cohort.child_command(args)
    assert command[command.index("--output-root") + 1] == args.output_root
    assert command[command.index("--shard") + 1] == "fixture"


@pytest.mark.parametrize("mode", ["cohorts", "cohort-smoke"])
def test_manual_matrices_preserve_roles_coverage_order_and_capture_placement(mode):
    context, plan, independent, dependent = cohort.ado_shadow.cohort_matrices(
        ROOT, {"host": "ado", "event": "Manual", "placement": mode, "profile": "full-verification"}
    )
    rows = independent["include"] + dependent["include"]
    assert [row["display_number"] for row in rows] == list(range(1, len(rows) + 1))
    assert len(rows) == (8 if mode == "cohorts" else 1)
    assert all(row["timeout"] <= 55 for row in rows)
    selected = cohort.ado_shadow.validate_placement(ROOT, context)
    for row in rows:
        group = next(group for group in selected if group["id"] == row["cohort"])
        assert context["preparation_roles"][row["setup_shard"]] == group["preparation"]
        assert row["display_title"] and not row["display_title"].endswith("-1")
        for shard in group["shards"]:
            assert publisher.shard_artifact(ROOT, context, shard) == "ci-shadow-" + group["id"]
    if mode == "cohorts":
        assert {shard for group in selected for shard in group["shards"]} == {row["id"] for row in plan["shards"]}
    else:
        with pytest.raises(ValueError, match="Partial"):
            cohort.validate_collection(ROOT, context, ROOT / ".tmp/no-results")
    damaged = copy.deepcopy(context)
    damaged["cohort_placement"]["cohorts"][0]["preparation"] = "core"
    with pytest.raises(ValueError, match="Captured"):
        cohort.ado_shadow.validate_placement(ROOT, damaged)


@pytest.fixture
def collected(tmp_path, monkeypatch):
    context = {
        "host": "ado",
        "event": "Manual",
        "placement": "cohorts",
        "profile": "synthetic",
        "executed": "a" * 40,
        "run_url": "https://dev.azure.com/DreamtechADO/project/_build/results?buildId=123",
    }
    group = {
        "id": "cohort-0",
        "shards": ["first", "second"],
        "preparation": "core",
        "os": "windows",
        "declared_shard_seconds": 60,
        "preserved_child_setup_seconds": 1200,
    }
    plan = {
        "id": "fixture-plan",
        "shards": [{"id": name, "order": number, "depends_on": []} for number, name in enumerate(group["shards"])],
    }
    monkeypatch.setattr(cohort.ado_shadow, "validate_placement", lambda *a: [group])
    monkeypatch.setattr(cohort.transport, "matrices", lambda *a: (plan, {}, {}))
    stage = tmp_path / ".tmp/ci-shadow/cohorts/cohort-0/transport"
    entries = []
    for name in group["shards"]:
        owner = stage / name / "bundle" / ("run-fixture-" + name)
        owner.mkdir(parents=True)
        report = record(owner, "failed" if name == "first" else "passed")
        report["provenance"].update(
            executed_commit=context["executed"], shard_source={"shard": name, "shard_plan": plan["id"]}
        )
        reports.finalize(owner, report)
        entries.append(
            {
                "shard": name,
                "run_id": report["run_id"],
                "status": report["status"],
                "exit_code": report["exit_code"],
                "process": {"status": "exited", "child_exit_code": report["exit_code"], "cleanup": {"verified": True}},
            }
        )
    result = {
        "contract": "ci-ado-cohort-experiment",
        "contract_version": 1,
        "adopted": False,
        "executed_commit": context["executed"],
        "profile": context["profile"],
        "cohort": {**group, "shard_plan": plan["id"]},
        "shards": entries,
        "exit_code": 1,
        "status": "failed",
    }
    reports.atomic_bytes(stage, "cohort-result.json", reports.encoded(result))
    return tmp_path, context, stage, result


def test_collection_admits_original_failed_and_passing_shards_without_changing_outcomes(collected):
    root, context, stage, _ = collected
    owners = cohort.validate_collection(root, context, stage)
    assert len(owners) == 2
    assert [reports.verify_publication(owner)["execution_exit_code"] for owner in owners] == [1, 0]


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "extra-bundle",
        "profile",
        "commit",
        "budget",
        "shards",
        "exit",
        "cleanup",
        "escape",
        "status",
        "manifest",
        "qualification",
    ],
)
def test_collection_rejects_incomplete_foreign_or_inconsistent_cohort_evidence(collected, mutation):
    root, context, stage, result = collected
    receipt = stage / "cohort-result.json"
    if mutation == "missing":
        receipt.unlink()
    elif mutation == "duplicate":
        (stage / "duplicate").mkdir()
        shutil.copy2(receipt, stage / "duplicate/cohort-result.json")
    elif mutation == "extra-bundle":
        shutil.copytree(stage / "first/bundle", stage / "stray/bundle")
    elif mutation == "manifest":
        (stage / "first/bundle/run-fixture-first/publication-manifest.json").unlink()
    else:
        if mutation == "profile":
            result["profile"] = "foreign"
        elif mutation == "commit":
            result["executed_commit"] = "b" * 40
        elif mutation == "budget":
            result["cohort"]["preserved_child_setup_seconds"] = 0
        elif mutation == "shards":
            result["shards"].pop()
        elif mutation == "exit":
            result["shards"][0]["exit_code"] = 0
        elif mutation == "cleanup":
            result["shards"][0]["process"]["cleanup"]["verified"] = False
        elif mutation == "escape":
            result["shards"][0]["run_id"] = "../escape"
        elif mutation == "status":
            result["status"] = "passed"
        elif mutation == "qualification":
            result["qualification"] = {"scenario": "launch-failure", "shard": "first"}
        receipt.write_bytes(reports.encoded(result))
    with pytest.raises((ValueError, OSError, KeyError)):
        cohort.validate_collection(root, context, stage)


def test_smoke_summary_marks_partial_coverage_and_never_uploads_test_cases(collected, capsys):
    root, context, stage, _ = collected
    context["placement"] = "cohort-smoke"
    assert cohort.publish_summary(root, context, "cohort-0") == 0
    text = (stage / "summary.md").read_text(encoding="utf-8")
    assert "Partial qualification only" in text and "failed" in text
    assert "01. First" in text and "02. Second" in text
    output = capsys.readouterr().out
    assert "task.addattachment" in output and "testresults" not in output.lower()


def test_launch_failure_summary_preserves_missing_coverage_diagnostic_and_later_results(collected, capsys):
    root, context, stage, result = collected
    context.update(event="Manual", placement="cohort-smoke", profile="full-verification", pr=None)
    context["cohort_qualification"] = "launch-failure"
    # Keep the captured fixture source profile; admission failure must not hide readable later evidence.
    for owner in stage.glob("*/bundle/run-*"):
        report = reports.decode_json((owner / "report.json").read_text(encoding="utf-8"))
        report["profile"] = context["profile"]
        shutil.rmtree(owner)
        owner.mkdir()
        reports.finalize(owner, report)
    first = result["shards"][0]
    shutil.rmtree(stage / "first")
    first.pop("run_id")
    first.update(reason="Cohort child produced missing or ambiguous run evidence")
    first["process"]["child_exit_code"] = 2
    result["profile"] = context["profile"]
    result["qualification"] = {"scenario": "launch-failure", "shard": "first"}
    reports.atomic_bytes(stage, "cohort-result.json", reports.encoded(result), replace=True)
    assert cohort.publish_summary(root, context, "cohort-0") == 1
    text = (stage / "summary.md").read_text(encoding="utf-8")
    assert "Partial qualification only" in text and "Deliberate qualification fault" in text
    assert "Missing finalized shard evidence: first" in text
    assert "Child process: exited; exit: 2" in text
    assert "no passing coverage is inferred" in text and "CI execution: passed" in text
    assert "testresults" not in capsys.readouterr().out.lower()


def test_bare_diagnostic_staging_retains_setup_without_promoting_it_to_coverage(tmp_path):
    source = tmp_path / ".tmp/ci-cache-pilot"
    source.mkdir(parents=True)
    (source / "failure.json").write_text('{"error":"synthetic acquisition failure"}')
    stage = cohort.diagnostics(tmp_path, {"host": "ado"}, "cohort-0")
    assert (stage / "setup/failure.json").is_file()
    assert not list(stage.rglob("shard-result.json"))
    with pytest.raises(ValueError):
        cohort.diagnostics(tmp_path, {}, "../escape")


@pytest.mark.integration
def test_cohort_diagnostic_cli_works_without_site_packages_after_setup_failure(tmp_path):
    directory = tmp_path / "Tools/CI"
    directory.mkdir(parents=True)
    for source in (ROOT / "Tools/CI").glob("*.py"):
        shutil.copy2(source, directory / source.name)
    runtime = tmp_path / "Tools/Commands/Environment"
    runtime.mkdir(parents=True)
    for source in (ROOT / "Tools/Commands/Environment").glob("*.py"):
        shutil.copy2(source, runtime / source.name)
    failure = tmp_path / ".tmp/ci-cache-pilot"
    failure.mkdir(parents=True)
    (failure / "failure.json").write_text('{"error":"controlled setup failure"}', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(directory / "ado_cohort.py"), "--cohort", "cohort-0", "--diagnostics"],
        env={**os.environ, "SHADOW_CONTEXT": json.dumps({"host": "ado"})},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / ".tmp/ci-shadow/cohorts/cohort-0/transport/setup/failure.json").is_file()
