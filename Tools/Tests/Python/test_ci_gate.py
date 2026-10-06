"""Private end-to-end supervisor admission tests; never invoke the production portfolio recursively."""

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    controller = importlib.import_module("run_ci")
    scope = importlib.import_module("scope")
    processes = importlib.import_module("process_supervisor")
    reports = importlib.import_module("execution_reports")
finally:
    sys.path[:] = before


@pytest.fixture
def private_controller(tmp_path, monkeypatch):
    root = tmp_path / "private-repository"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
    (root / ".gitignore").write_text(".tmp/\n", encoding="utf-8")
    (root / "authored.md").write_bytes(b"untouched authored wording\n")
    source = scope.Snapshot({"authored.md": b"untouched authored wording\n"}, {"authored.md": "100644"})
    captured = {
        "provenance": {"mode": "local-worktree", "executed_commit": "a" * 40, "snapshot_kind": "worktree"},
        "changes": [],
        "fallback_reasons": [],
        "policy_scope": {"mode": "changed", "paths": [], "dispositions": []},
    }
    monkeypatch.setattr(controller, "resolve_scope", lambda *args: (captured, source))
    scenario = {"first": "assertion", "second": "missing", "last": "passed"}
    plan = {
        "units": [
            {
                "execution_id": "policy/" + name + "::python",
                "runtimes": ["python"],
                "adapter": "synthetic",
                "deadline_seconds": 3,
                "depends_on": [],
                "availability": "declared",
                "reasons": [],
            }
            for name in scenario
        ],
        "budget": {"total_seconds": 45, "termination_seconds": 1, "cleanup_seconds": 2, "finalization_seconds": 3},
        "required_reviews": [],
    }

    class PrivateCatalog:
        source_digests = {}
        runtime_versions = {}

        def __init__(self, workspace):
            self.workspace = workspace

        def plan(self, *args):
            return plan

    monkeypatch.setattr(controller, "Catalog", PrivateCatalog)

    class PrivateSession:
        def __init__(self, workspace, snapshot, output, *args, **kwargs):
            assert args[-1] == "Worktree"
            self.root, self.output = workspace, output
            self.env = {
                name: os.environ[name]
                for name in ("SystemRoot", "WINDIR", "TEMP", "TMP", "PATH", "HOME")
                if name in os.environ
            }
            self.inventory, self.containment_verified = {}, True

        def preflight(self, selected, versions, cancel):
            self.inventory = {"python": {"status": "verified", "version": "synthetic"}}

        def context(self, cancel):
            return {"status": "passed"}

        def execute(self, row, lease, cancel, complete):
            mode = scenario[row["execution_id"].split("/")[1].split("::")[0]]
            code = "print('{\"passed\":true}')"
            if mode == "assertion":
                code = "print('{\"passed\":false}');raise SystemExit(1)"
            elif mode == "malformed":
                code = "print('synthetic malformed summary')"
            executable = str(root / "missing-python") if mode == "missing" else sys.executable
            process = processes.run_process(
                [executable, "-I", "-B", "-c", code],
                cwd=self.root,
                env=self.env,
                output_parent=self.output,
                lease=lease,
                termination=0.15,
                cleanup=1,
                cancel=cancel,
            )
            if process["status"] != "exited":
                return {
                    "status": "error",
                    "classification": process["classification"],
                    "processes": [process],
                    "child_exit_code": process["child_exit_code"],
                    "reasons": [process.get("error", "launch failed")],
                }
            stdout = Path(process["directory"], "stdout.bin").read_text(encoding="utf-8")
            try:
                evidence = json.loads(stdout)
            except ValueError:
                return {
                    "status": "error",
                    "classification": "result-contract",
                    "processes": [process],
                    "child_exit_code": process["child_exit_code"],
                    "reasons": [stdout],
                }
            if mode == "cancel":
                cancel.set()
            return {
                "status": "passed" if evidence["passed"] else "failed",
                "classification": "assertion" if not evidence["passed"] else None,
                "processes": [process],
                "evidence": evidence,
                "child_exit_code": process["child_exit_code"],
            }

    monkeypatch.setattr(controller, "AdapterSession", PrivateSession)
    args = SimpleNamespace(
        root=str(root),
        output_root=".tmp/ci-gate",
        profile="ci-infrastructure",
        scope="local-worktree",
        base=None,
        source=None,
        executed=None,
        shard_plan=None,
        shard=None,
        shard_results=[],
        source_results=[],
        python=sys.executable,
        pwsh=None,
        module_root=None,
        actionlint=None,
        wheel=None,
        runtime_wheel=None,
        render_bootstrap_report=None,
    )
    return args, scenario, root


@pytest.mark.integration
@pytest.mark.parametrize("first,second", [("assertion", "missing"), ("malformed", "assertion"), ("cancel", "passed")])
def test_private_supervisor_continues_errors_and_records_cancellation(private_controller, first, second):
    args, scenario, root = private_controller
    scenario.update(first=first, second=second)
    report, path = controller.execute(args)
    expected = (
        ["passed", "cancelled", "cancelled"]
        if first == "cancel"
        else ["failed" if first == "assertion" else "error", "error" if second == "missing" else "failed", "passed"]
    )
    assert [row["status"] for row in report["results"]] == expected
    assert report["exit_code"] == (130 if first == "cancel" else 1)
    assert report["complete"] and report["canonical_guard"]["unchanged"] and report["cleanup"]["verified"]
    manifest = reports.verify_publication(path.parent)
    assert manifest["execution_exit_code"] == report["exit_code"]
    assert report["counts"]["selected"] == sum(report["counts"]["terminal"].values()) == 3
    if first == "cancel":
        assert all(row["attempts"] == 0 for row in report["results"][1:])
    assert (root / "authored.md").read_bytes() == b"untouched authored wording\n"


@pytest.mark.integration
def test_unit_journal_failure_keeps_actual_result_blocks_later_work_and_refuses_finalization(
    private_controller, monkeypatch
):
    args, scenario, _ = private_controller
    scenario.update(first="passed")
    original = reports.atomic_bytes

    def fail(owner, name, data, **kwargs):
        if name == "records/000004.json":
            raise OSError("synthetic unit-record failure")
        return original(owner, name, data, **kwargs)

    monkeypatch.setattr(reports, "atomic_bytes", fail)
    report, path = controller.execute(args)
    assert [row["status"] for row in report["results"]] == ["passed", "blocked", "blocked"]
    assert report["results"][0]["attempts"] == 1 and report["results"][0]["child_exit_code"] == 0
    assert report["exit_code"] == 1 and not report["complete"]
    assert path.name == "finalization-failure.json"
    assert not (path.parent / "finalized.json").exists()
    assert (path.parent / "events.jsonl").exists()


@pytest.mark.parametrize("field", ["id", "owner", "deadline_seconds", "blocking"])
def test_adapter_cannot_change_registered_metadata_and_later_units_continue(field):
    aggregate = importlib.import_module("aggregate_execution")
    import threading

    plan = {
        "units": [
            {
                "execution_id": "policy/" + name + "::python",
                "runtimes": ["python"],
                "depends_on": [],
                "deadline_seconds": 1,
                "availability": "declared",
                "reasons": [],
            }
            for name in ("first", "last")
        ]
    }

    def dispatch(row, *args):
        return {"status": "passed", field: "foreign"} if "first" in row["execution_id"] else {"status": "passed"}

    rows, failures, _ = aggregate.execute_units(
        plan, dispatch, processes.RunBudget(10, 1, 1, 1), threading.Event(), lambda: None
    )
    assert [row["status"] for row in rows] == ["error", "passed"]
    assert [row["id"] for row in rows] == [row["execution_id"] for row in plan["units"]]
    assert aggregate.outcome(rows, failures, False, []) == ("failed", 1)

    def unsafe(row, *args):
        return {"status": "passed", field: "foreign", "processes": [{"cleanup": {"verified": False}}]}

    rows, failures, guard = aggregate.execute_units(
        plan, unsafe, processes.RunBudget(10, 1, 1, 1), threading.Event(), lambda: None
    )
    assert [row["status"] for row in rows] == ["error", "blocked"]
    assert not guard["containment_verified"] and rows[1]["attempts"] == 0


def test_empty_execution_is_not_a_successful_regression_gate():
    aggregate = importlib.import_module("aggregate_execution")
    assert aggregate.outcome([], [], False, []) == ("failed", 1)
    report = controller.empty_report("ci-infrastructure", "synthetic")
    report.update(status="passed", exit_code=0, canonical_guard={"unchanged": True})
    with pytest.raises(ValueError, match="Passing record"):
        reports.validate_report(report)
