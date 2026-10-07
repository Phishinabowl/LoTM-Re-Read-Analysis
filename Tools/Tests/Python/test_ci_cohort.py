"""Cohort placement keeps independent child execution and original publication contracts."""

import argparse
import copy
import importlib
import json
import signal
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
