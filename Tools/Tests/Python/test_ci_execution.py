"""Private aggregate, adapter and shard fixtures; never recursively run the production portfolio."""

import copy
import importlib
import json
import stat
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    aggregate = importlib.import_module("aggregate_execution")
    adapters = importlib.import_module("layer_adapters")
    processes = importlib.import_module("process_supervisor")
    scopes = importlib.import_module("scope")
    worker = importlib.import_module("adapter_worker")
    controller = importlib.import_module("run_ci")
    sys.path.insert(0, str(ROOT / "Tools/Conformance"))
    conformance = importlib.import_module("run_conformance")
    sys.path.insert(0, str(ROOT / "Tools/Compatibility"))
    compatibility = importlib.import_module("run_compatibility")
finally:
    sys.path[:] = before


def plan():
    return {
        "units": [
            {
                "execution_id": "implementation/" + name + "::python",
                "adapter": "pytest",
                "entry": [],
                "runtimes": ["python"],
                "os": ["windows", "linux"],
                "deadline_seconds": 2,
                "depends_on": dependencies,
                "availability": "declared",
                "reasons": [],
            }
            for name, dependencies in [("alpha", []), ("beta", []), ("dependent", ["implementation/alpha::python"])]
        ]
    }


def budget():
    return processes.RunBudget(20, 1, 1, 1)


def test_independent_failures_continue_and_prerequisite_blocks_without_attempt():
    launches = []

    def dispatch(row, *args):
        launches.append(row["execution_id"])
        return {"status": "failed" if "alpha" in row["execution_id"] else "passed", "classification": "assertion"}

    rows, failures, guard = aggregate.execute_units(plan(), dispatch, budget(), threading.Event(), lambda: None)
    assert launches == ["implementation/alpha::python", "implementation/beta::python"]
    assert [row["status"] for row in rows] == ["failed", "passed", "blocked"]
    assert rows[-1]["attempts"] == 0 and rows[-1]["native_counts"] is None
    assert len(failures) == 2 and guard["unchanged"]


@pytest.mark.parametrize("failure", ["exception", "timeout", "cleanup", "mutation", "cancel"])
def test_unsafe_and_cancelled_states_are_explicit(failure):
    cancel = threading.Event()
    calls = []

    def dispatch(row, *args):
        calls.append(row["execution_id"])
        if failure == "exception":
            raise ValueError("synthetic malformed result")
        if failure == "timeout":
            raise TimeoutError("synthetic whole unit timeout")
        if failure == "cancel":
            cancel.set()
            return {"status": "cancelled", "classification": "cancellation"}
        if failure == "cleanup":
            return {"status": "error", "classification": "cleanup", "processes": [{"cleanup": {"verified": False}}]}
        return {"status": "passed"}

    def guard():
        if failure == "mutation" and calls:
            raise ValueError("captured authored source mutated")

    rows, failures, state = aggregate.execute_units(plan(), dispatch, budget(), cancel, guard)
    assert len(rows) == 3 and all(row["status"] in aggregate.STATES for row in rows)
    if failure in {"mutation", "cleanup"}:
        assert len(calls) == 1 and rows[1]["status"] == "blocked"
    if failure == "mutation":
        assert rows[0]["status"] == "passed" and state["unchanged"] is False
    if failure == "cancel":
        assert aggregate.outcome(rows, failures, True, [])[1] == 130
        assert all(row["status"] == "cancelled" for row in rows)
    else:
        assert aggregate.outcome(rows, failures, False, [])[1] == 1


def test_budget_blocking_does_not_invent_test_coverage():
    tiny = processes.RunBudget(3.1, 1, 1, 1)
    rows, _, _ = aggregate.execute_units(
        plan(), lambda *args: pytest.fail("Unexpected launch"), tiny, threading.Event(), lambda: None
    )
    assert [row["status"] for row in rows] == ["blocked"] * 3
    assert rows[0]["classification"] == "budget" and all(row["attempts"] == 0 for row in rows)


def test_pending_review_and_independent_failure_exit_precedence():
    assert aggregate.outcome([], [], False, [{"status": "pending"}]) == ("failed", 1)
    assert aggregate.outcome([], [{"classification": "assertion"}], True, []) == ("cancelled", 130)
    assert aggregate.outcome([{"status": "cancelled"}], [], False, []) == ("cancelled", 130)


def test_run_origin_includes_setup_and_cannot_extend_deadline(monkeypatch):
    monkeypatch.setattr(processes.time, "monotonic", lambda: 100)
    value = processes.RunBudget(20, 1, 1, 1, started=90)
    assert value.deadline == 110 and value.execution_deadline == 107
    with pytest.raises(ValueError):
        processes.RunBudget(20, 1, 1, 1, started=101)


@pytest.mark.parametrize("deadline", ["expired", "bounded", "nonfinite"])
def test_compatibility_nested_deadline_preserves_partial_diagnostics(monkeypatch, tmp_path, deadline):
    value = (
        time.monotonic() - 1
        if deadline == "expired"
        else float("inf")
        if deadline == "nonfinite"
        else time.monotonic() + 5
    )
    monkeypatch.setenv("LOTM_CI_UNIT_DEADLINE", str(value))

    def hung(command, **kwargs):
        assert 0 < kwargs["timeout"] <= 3
        raise subprocess.TimeoutExpired(command, kwargs["timeout"], output=b"partial stdout", stderr=b"partial stderr")

    monkeypatch.setattr(compatibility.subprocess, "run", hung)
    with pytest.raises(compatibility.CompatibilityFailure) as caught:
        compatibility.run_command(compatibility.Runtime("python", sys.executable), [sys.executable], tmp_path, 60)
    if deadline == "bounded":
        assert "partial stdout" in str(caught.value) and "partial stderr" in str(caught.value)


@pytest.mark.parametrize(
    "left,right", [(True, 1), (1, 1.0), (["a", "b"], ["b", "a"]), ({"a": None}, {}), ({"a": 0}, {"a": False})]
)
def test_parity_preserves_semantic_types_order_and_fields(left, right):
    assert adapters.typed_equal(left, right) is False


def detailed():
    return {
        "schema_version": 1,
        "profile": "selected",
        "suite_count": 1,
        "passed": 1,
        "failed": 0,
        "suites": [{"id": "alpha", "status": "passed", "summary": {"cases": 2}}],
    }


@pytest.mark.parametrize("change", ["empty", "identity", "bool", "count", "missing-summary", "wrong-schema"])
def test_conformance_result_cannot_pass_false_inventory(change):
    value = detailed()
    if change == "empty":
        value["suites"] = []
    if change == "identity":
        value["suites"][0]["id"] = "beta"
    if change == "bool":
        value["passed"] = True
    if change == "count":
        value["suite_count"] = 2
    if change == "missing-summary":
        del value["suites"][0]["summary"]
    if change == "wrong-schema":
        value["schema_version"] = True
    with pytest.raises(ValueError):
        adapters.conformance_result(value, "alpha")


def test_conformance_child_deadline_is_owned_by_runner(monkeypatch, tmp_path):
    def hung(command, **kwargs):
        assert kwargs["timeout"] == 0.5
        raise subprocess.TimeoutExpired(command, 0.5, output=b"retained stdout", stderr=b"retained stderr")

    monkeypatch.setattr(conformance.subprocess, "run", hung)
    result = conformance.run_suite(tmp_path, {"id": "alpha", "python_path": tmp_path / "child.py"}, 0.5)
    assert result["status"] == "failed" and "deadline" in result["error"]
    assert "retained stdout" in result["error"] and "retained stderr" in result["error"]


def test_compatibility_owner_continues_and_stops_after_canonical_mutation(tmp_path, monkeypatch):
    protected = tmp_path / "authored.md"
    protected.write_text("unchanged")
    monkeypatch.setattr(compatibility, "protected_paths", lambda root: [protected])
    before = compatibility.sha256_tree([protected])
    calls = []

    def failed(*args):
        calls.append("failed")
        raise compatibility.CompatibilityFailure("synthetic assertion")

    def good(*args):
        calls.append("good")
        return {"status": "passed"}

    monkeypatch.setitem(compatibility.CHECK_HANDLERS, "alpha", failed)
    monkeypatch.setitem(compatibility.CHECK_HANDLERS, "beta", good)
    checks = [{"id": "alpha", "kind": "alpha"}, {"id": "beta", "kind": "beta"}]
    rows, failures, safe = compatibility.execute_checks(checks, [], tmp_path, tmp_path, before)
    assert [row["status"] for row in rows] == ["failed", "passed"] and calls == ["failed", "good"] and safe
    assert failures[0]["id"] == "alpha"

    def mutate(*args):
        protected.write_text("changed")
        return {"status": "passed"}

    monkeypatch.setitem(compatibility.CHECK_HANDLERS, "alpha", mutate)
    rows, failures, safe = compatibility.execute_checks(checks, [], tmp_path, tmp_path, before)
    assert [row["status"] for row in rows] == ["passed", "blocked"] and not safe
    assert failures[-1]["classification"] == "canonical-output-change"


def test_captured_bytes_and_additional_authored_files_are_guarded(tmp_path):
    snapshot = scopes.Snapshot({"authored.md": b"original"}, {"authored.md": "100644"})
    (tmp_path / "authored.md").write_bytes(b"original")
    assert adapters.guarded_manifest(tmp_path, snapshot) == snapshot.digest
    (tmp_path / ".tmp").mkdir()
    (tmp_path / ".tmp/log.bin").write_bytes(b"owned output")
    assert adapters.guarded_manifest(tmp_path, snapshot) == snapshot.digest
    (tmp_path / "additional.md").write_text("unexpected authoring")
    with pytest.raises(ValueError, match="Protected"):
        adapters.guarded_manifest(tmp_path, snapshot)


def test_cleanup_removes_only_owned_readonly_git_fixture(tmp_path):
    owner = tmp_path / "owned"
    owner.mkdir()
    target = owner / "git-object"
    target.write_bytes(b"owned read-only fixture")
    target.chmod(stat.S_IRUSR)
    foreign = tmp_path / "unrelated"
    foreign.write_bytes(b"preserved")
    controller.remove_scratch(owner)
    assert not owner.exists() and foreign.read_bytes() == b"preserved"


def test_adapter_contract_failure_retains_process_diagnostics(tmp_path, monkeypatch):
    session = adapters.AdapterSession(tmp_path, None, tmp_path, {"python": sys.executable})
    process = {"directory": "owned-diagnostic", "child_exit_code": 0, "cleanup": {"verified": True}}

    def malformed(*args):
        session.active_processes = [process]
        raise ValueError("synthetic malformed JSON after successful process")

    monkeypatch.setattr(session, "execute_layer", malformed)
    result = session.execute({}, processes.Lease(time.monotonic() + 1), threading.Event(), {})
    assert result["status"] == "error" and result["classification"] == "result-contract"
    assert result["processes"] == [process] and result["child_exit_code"] == 0


def test_prerequisite_source_rows_enable_shard_dependencies_without_duplicate_execution():
    required = plan()["units"][-1]
    completed = {"implementation/alpha::python": {"status": "passed", "evidence": {"synthetic": True}}}
    called = []

    def dispatch(row, lease, cancel, sources):
        called.append(row["execution_id"])
        assert sources["implementation/alpha::python"]["evidence"] == {"synthetic": True}
        return {"status": "passed"}

    rows, failures, _ = aggregate.execute_units(
        {"units": [required]}, dispatch, budget(), threading.Event(), lambda: None, completed
    )
    assert rows[0]["status"] == "passed" and called == [required["execution_id"]] and not failures


def test_actual_scope_keeps_deletion_and_composed_context_separate_from_test_impact():
    snapshot = scopes.Snapshot({"changed.py": b"pass"}, {"changed.py": "100644"})
    scope = {"policy_scope": {"paths": ["changed.py", "deleted.md"], "mode": "changed", "deletion_precision": True}}
    results = [{"id": name, "status": "passed"} for name in ["policy/ruff::python", "policy/work-annotations::python"]]
    report = aggregate.actual_dispositions(scope, snapshot, results, {"status": "passed"})
    assert [row["status"] for row in report["dispositions"]] == ["validated", "validated"]
    assert report["dispositions"][1]["exists"] is False and report["dispositions"][1]["deletion_integrity"]
    assert (
        aggregate.actual_dispositions(scope, snapshot, results, {"status": "failed"})["dispositions"][0]["status"]
        == "failed"
    )


def test_explicit_annotation_inventory_does_not_fall_back_to_git(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "Tools/Static"))
    policy_module = importlib.import_module("lint_work_annotations")
    policy = policy_module.load_policy(ROOT / "Tools/Static/work-annotations.json")
    source = tmp_path / "changed.py"
    source.write_text("print('synthetic')\n")
    monkeypatch.setattr(policy_module, "repository_inventory", lambda *args: pytest.fail("Read another Git inventory"))
    assert policy_module.scan_paths(tmp_path, policy, [source]) == (1, 0, [])


@pytest.mark.integration
def test_real_owned_failure_then_success_keeps_complete_diagnostics(tmp_path):
    snapshot = scopes.Snapshot({"owned.txt": b"source"}, {"owned.txt": "100644"})
    (tmp_path / "owned.txt").write_bytes(b"source")
    session = adapters.AdapterSession(tmp_path, snapshot, tmp_path, {"python": sys.executable})

    def dispatch(row, lease, cancel, completed):
        script = (
            "import sys; print('full retained failure'); sys.exit(1)"
            if "alpha" in row["execution_id"]
            else "print('later ran')"
        )
        result = session.launch([sys.executable, "-c", script], tmp_path, lease, cancel)
        return {
            "status": "passed" if result["child_exit_code"] == 0 else "failed",
            "classification": "assertion",
            "child_exit_code": result["child_exit_code"],
            "processes": [result],
        }

    rows, failures, _ = aggregate.execute_units(plan(), dispatch, budget(), threading.Event(), lambda: None)
    assert [row["status"] for row in rows] == ["failed", "passed", "blocked"]
    assert Path(rows[0]["processes"][0]["directory"], "stdout.bin").read_text().strip() == "full retained failure"
    assert Path(rows[1]["processes"][0]["directory"], "stdout.bin").read_text().strip() == "later ran"


@pytest.mark.parametrize(
    "change", ["valid", "missing", "duplicate", "snapshot", "artifact", "false-native", "foreign-unit"]
)
def test_shard_collection_rejects_incomplete_or_false_evidence(tmp_path, change):
    source = {"units": ["policy/ruff::python"], "shard": "one", "profile": "synthetic"}

    class Catalog:
        source_digests = {"input": "digest"}
        profiles = {"synthetic": {"execution": ["policy/ruff::python"]}}
        shard_plans = {"plan": {"profile": "synthetic"}}
        units = {"policy/ruff": {"owner": "policy", "adapter": "ruff", "deadline_seconds": 2}}

        def validate_manifests(self, plan_id, sources, digest):
            if sources != [source]:
                raise ValueError("missing/duplicate/foreign source")

    (tmp_path / "owned").mkdir()
    process_path = tmp_path / "owned/process.json"
    process_path.write_text(json.dumps({"status": "exited", "child_exit_code": 0, "cleanup": {"verified": True}}))
    entry = aggregate.artifact(process_path, tmp_path, "policy/ruff::python")
    row = {
        "id": "policy/ruff::python",
        "owner": "policy",
        "runtime": "python",
        "blocking": True,
        "deadline_seconds": 2,
        "status": "passed",
        "child_exit_code": 0,
        "native_counts": None,
        "artifacts": [entry["path"]],
    }
    report = controller.empty_report("synthetic", "owned")
    report.update(
        profile="synthetic",
        status="passed",
        exit_code=0,
        provenance={"snapshot_digest": "snapshot", "catalog_digests": Catalog.source_digests},
        results=[row],
        artifacts=[entry],
        counts={"terminal": aggregate.counts([row])},
        canonical_guard={"unchanged": True},
        cleanup={"verified": True},
    )
    path = tmp_path / "bundle.json"
    value = {"contract": "ci-shard-result", "contract_version": 1, "source": source, "report": report}
    if change == "snapshot":
        report["provenance"]["snapshot_digest"] = "wrong"
    if change == "artifact":
        process_path.write_text("altered")
    if change == "false-native":
        row["native_counts"] = {"passed": 1}
    if change == "foreign-unit":
        row["id"] = "policy/other::python"
    path.write_text(json.dumps(value))
    bundles = [] if change == "missing" else [path, path] if change == "duplicate" else [path]
    if change == "valid":
        rows, _ = aggregate.collect_shards(Catalog(), "plan", bundles, "snapshot")
        assert rows == [row]
        return
    with pytest.raises((ValueError, KeyError)):
        aggregate.collect_shards(Catalog(), "plan", bundles, "snapshot")
