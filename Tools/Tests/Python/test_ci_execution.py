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
    bootstrap = importlib.import_module("bootstrap")
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


@pytest.mark.parametrize("kind,expected", [("commit", "GitBlob"), ("index", "GitBlob"), ("worktree", "Worktree")])
def test_formatter_representation_is_bound_to_snapshot_provenance(kind, expected):
    assert adapters.format_representation(kind) == expected


def test_unknown_formatter_representation_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="representation"):
        adapters.format_representation("unknown")
    with pytest.raises(ValueError, match="representation"):
        adapters.AdapterSession(tmp_path, None, tmp_path, {}, source_representation="unknown")


@pytest.mark.parametrize("representation", ["GitBlob", "Worktree"])
def test_formatter_request_preserves_declared_representation(tmp_path, monkeypatch, representation):
    snapshot = scopes.Snapshot({"sample.ps1": b"$value = 1\n"}, {"sample.ps1": "100644"})
    session = adapters.AdapterSession(
        tmp_path,
        snapshot,
        tmp_path,
        {"python": sys.executable, "powershell7": sys.executable},
        source_representation=representation,
    )
    session.readiness = {"powershell7": True}

    def launch(command, directory, lease, cancel):
        request = json.loads((directory / "request.json").read_text())
        assert request["paths"] == ["sample.ps1"] and request["source_representation"] == representation
        (directory / "stdout.bin").write_text(json.dumps({"ready": True, "files_checked": 1}))
        return {"directory": str(directory), "status": "exited", "child_exit_code": 0, "cleanup": {"verified": True}}

    monkeypatch.setattr(session, "launch", launch)
    result = session.execute_layer(
        {"adapter": "powershell-format", "execution_id": "policy/powershell-format::powershell7"},
        processes.Lease(time.monotonic() + 5),
        threading.Event(),
        {},
    )
    assert result["status"] == "passed"


@pytest.mark.parametrize(
    "change",
    ["none", "id", "count", "decision", "order", "error", "status", "type", "source-status", "missing-runtime"],
)
def test_real_parity_adapter_rejects_semantic_and_source_failures(tmp_path, change):
    left = detailed()
    left["suites"][0]["summary"].update(decision="accepted", ordered=["first", "second"])
    right = copy.deepcopy(left)
    right["profile"] = "different-operational-profile"
    summary = right["suites"][0]["summary"]
    if change == "id":
        right["suites"][0]["id"] = "beta"
    elif change == "count":
        summary["cases"] = 3
    elif change == "decision":
        summary["decision"] = "rejected"
    elif change == "order":
        summary["ordered"].reverse()
    elif change == "error":
        right["suites"][0]["error"] = "unexpected semantic failure"
    elif change == "status":
        right["suites"][0]["status"] = "failed"
        right.update(passed=0, failed=1)
    elif change == "type":
        summary["cases"] = 2.0
    dependencies = ["conformance/alpha::python", "conformance/alpha::powershell7"]
    completed = {name: {"status": "passed", "evidence": value} for name, value in zip(dependencies, [left, right])}
    if change == "source-status":
        completed[dependencies[1]]["status"] = "failed"
    elif change == "missing-runtime":
        dependencies = dependencies[:1]
    session = adapters.AdapterSession(tmp_path, None, tmp_path, {})
    row = {"adapter": "parity", "execution_id": "parity/synthetic::referee", "depends_on": dependencies}
    if change in {"id", "error", "status", "source-status", "missing-runtime"}:
        with pytest.raises(ValueError):
            session.execute_layer(row, processes.Lease(time.monotonic() + 5), threading.Event(), completed)
    else:
        result = session.execute_layer(row, processes.Lease(time.monotonic() + 5), threading.Event(), completed)
        assert result["status"] == ("passed" if change == "none" else "failed")
        assert result["evidence"]["sources"] == dependencies


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


def test_compatibility_owner_records_multiple_failures_and_preserves_unrelated_artifacts(tmp_path, monkeypatch):
    protected = tmp_path / "authored.md"
    protected.write_bytes(b"authored wording stays intact")
    sentinel = tmp_path / "unrelated.txt"
    sentinel.write_bytes(b"keep unrelated artifact")
    monkeypatch.setattr(compatibility, "protected_paths", lambda root: [protected])
    before = compatibility.sha256_tree([protected])

    def failed(check, *args):
        raise compatibility.CompatibilityFailure("specific failure " + check["id"])

    monkeypatch.setitem(compatibility.CHECK_HANDLERS, "failed-fixture", failed)
    monkeypatch.setitem(compatibility.CHECK_HANDLERS, "passed-fixture", lambda *args: {"status": "passed"})
    checks = [
        {"id": "first", "kind": "failed-fixture"},
        {"id": "second", "kind": "failed-fixture"},
        {"id": "later", "kind": "passed-fixture"},
    ]
    rows, failures, safe = compatibility.execute_checks(checks, [], tmp_path, tmp_path / "output", before)
    assert [row["status"] for row in rows] == ["failed", "failed", "passed"] and safe
    assert [failure["error"] for failure in failures] == ["specific failure first", "specific failure second"]
    assert protected.read_bytes() == b"authored wording stays intact"
    assert sentinel.read_bytes() == b"keep unrelated artifact"


@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.parametrize("separator", ["/", "\\"])
def test_normalization_uses_nearest_output_owner_and_preserves_content(tmp_path, depth, separator):
    root = tmp_path
    for _ in range(depth):
        root = root / ".tmp" / "isolated-source"
    output = root / ".tmp" / "compatibility-qa" / "qa" / "python"
    relative = ".tmp/compatibility-qa/qa/python"
    absolute = str(output).replace("\\", "/")
    text = f"Authored words; ordered A then B.\n{absolute}/page.md\n{relative}/page.md\n"
    text = text.replace("/", separator)
    normalized = compatibility.normalize_string(text, [output])
    assert normalized == (
        "Authored words; ordered A then B.\n<compat-output>"
        + separator
        + "page.md\n<compat-output>"
        + separator
        + "page.md\n"
    )
    values = compatibility.normalize_value({"items": ["second", "first"], "prose": text}, [output])
    assert values["items"] == ["second", "first"] and values["prose"] == normalized


@pytest.mark.parametrize("adapter", ["compatibility", "conformance"])
@pytest.mark.parametrize("long", [False, True])
def test_owner_error_promotion_is_bounded_and_retains_full_evidence(adapter, long):
    error = "Unsafe output: <authored>|preserve.\r\n" + ("detail\n" * 1000 if long else "specific mismatch")
    document = {"checks" if adapter == "compatibility" else "suites": [{"status": "failed", "error": error}]}
    before = copy.deepcopy(document)
    reasons = adapters.owning_failure_reasons(document, adapter)
    assert reasons and "Unsafe output" in reasons[0] and "\r" not in reasons[0]
    assert len(reasons[0].encode("utf-8")) < 4200
    assert ("Truncated" in reasons[0]) is long
    assert document == before


def test_owner_error_promotion_prefers_check_detail_with_envelope_fallback():
    assert adapters.owning_failure_reasons({"checks": [], "error": "cleanup failed"}, "compatibility") == [
        "cleanup failed"
    ]
    assert adapters.owning_failure_reasons({"checks": [{"status": "passed"}]}, "compatibility") == []


def test_formatter_failure_promotes_counts_and_paths_without_losing_full_owner_rows():
    document = {
        "files_changed": 70,
        "long_lines": 1,
        "files": [
            {"path": f"file-{index}.ps1", "changed": True, "long_lines": [{"line": 5, "length": 201}]}
            for index in range(70)
        ],
    }
    before = copy.deepcopy(document)
    reasons = adapters.owning_failure_reasons(document, "powershell-format")
    assert "70 changed files; 1 long lines" in reasons[0] and "file-0.ps1" in reasons[0]
    assert "Truncated" in reasons[0] and len(reasons[0].encode("utf-8")) < 4200
    assert document == before


@pytest.mark.parametrize("input_kind", ["missing", "denied"])
def test_unreadable_wheel_blocks_before_verifier_launch(tmp_path, monkeypatch, input_kind):
    wheel = tmp_path / "framework.whl"
    runtime = tmp_path / "runtime.whl"
    runtime.write_bytes(b"runtime")
    if input_kind == "denied":
        wheel.write_bytes(b"framework")
        original = Path.open

        def denied(path, *args, **kwargs):
            if path == wheel:
                raise PermissionError("synthetic unreadable original ACL")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", denied)
    session = adapters.AdapterSession(
        tmp_path, scopes.Snapshot({}, {}), tmp_path, {"python": sys.executable}, wheel=wheel, runtime_wheel=runtime
    )
    session.readiness = {"python": True}
    monkeypatch.setattr(session, "launch", lambda *args: pytest.fail("Unreadable input launched verifier"))
    result = session.execute(
        {"adapter": "installed-artifact", "execution_id": "implementation/python-installed-runtime::python"},
        processes.Lease(time.monotonic() + 5),
        threading.Event(),
        {},
    )
    assert result["status"] == "blocked" and result["classification"] == "prerequisite"
    assert "Unreadable framework wheel input" in result["reasons"][0] and str(wheel) in result["reasons"][0]


def test_owned_child_environment_keeps_windows_system_locations_without_global_browser_override(tmp_path, monkeypatch):
    monkeypatch.setenv("SystemDrive", "Z:")
    monkeypatch.setenv("ProgramData", "Z:/ProgramData")
    monkeypatch.setenv("PUPPETEER_EXECUTABLE_PATH", "global-browser")
    session = adapters.AdapterSession(tmp_path, None, tmp_path, {})
    assert session.env["SystemDrive"] == "Z:" and session.env["ProgramData"] == "Z:/ProgramData"
    assert "PUPPETEER_EXECUTABLE_PATH" not in session.env


@pytest.mark.parametrize(
    "change",
    ["none", "missing", "report", "key", "outside", "lock", "dependency", "browser", "config", "resolver", "version"],
)
def test_render_admission_rejects_stale_or_global_inputs(tmp_path, monkeypatch, change):
    versions = json.loads((ROOT / "Tools/CI/Data/runtime-versions.json").read_text())
    manifest = json.loads((ROOT / "Tools/CI/Node/package.json").read_text())
    lock = (ROOT / "Tools/CI/Node/package-lock.json").read_bytes()
    identity = {
        "schema": 2,
        "os": sys.platform,
        "architecture": __import__("platform").machine(),
        "node": versions["node"],
        "npm": versions["npm"],
        "browser": "chrome",
        "browser_version": versions["chrome"],
        "lock": __import__("hashlib").sha256(lock).hexdigest(),
    }
    key = bootstrap.key_for(identity)
    owner = tmp_path / ".local/ci-environments/render" / key / "synthetic"
    cache = tmp_path / ".local/ci-cache/browsers" / key
    modules = owner / "node_modules"
    modules.mkdir(parents=True)
    cache.mkdir(parents=True)
    (modules / "package.txt").write_bytes(b"pinned dependency")
    (owner / "package.json").write_text(json.dumps(manifest))
    (owner / "package-lock.json").write_bytes(lock)
    (owner / ".puppeteerrc.cjs").write_text(bootstrap.render_configuration())
    browser = cache / "chrome.exe"
    browser.write_bytes(b"pinned browser")
    (owner / "content-sha256.json").write_text(json.dumps(bootstrap.tree_manifest(modules)))
    (cache / "content-sha256.json").write_text(json.dumps(bootstrap.tree_manifest(cache)))
    mmdc = modules / ".bin" / ("mmdc.cmd" if sys.platform == "win32" else "mmdc")
    mmdc.parent.mkdir()
    mmdc.write_bytes(b"owned launcher")
    (owner / "content-sha256.json").write_text(json.dumps(bootstrap.tree_manifest(modules)))
    report = tmp_path / "bootstrap.json"
    report.write_text(
        json.dumps(
            {
                "status": "passed",
                "render": {
                    "environment": str(owner),
                    "browser_cache": str(cache),
                    "key": key,
                    "node": sys.executable,
                    "path": str(browser),
                    "mmdc": str(mmdc),
                    "browser": "Chrome/" + versions["chrome"],
                },
            }
        )
    )
    if change == "report":
        report.write_text('{"status":"failed"}')
    elif change == "lock":
        (owner / "package-lock.json").write_text("changed")
    elif change == "dependency":
        (modules / "package.txt").write_text("changed")
    elif change == "browser":
        browser.write_text("changed")
    elif change == "config":
        (owner / ".puppeteerrc.cjs").write_text("global fallback")
    elif change in {"key", "outside"}:
        value = json.loads(report.read_text())
        value["render"]["key" if change == "key" else "browser_cache"] = (
            "0" * 24 if change == "key" else str(tmp_path / "unowned-cache")
        )
        report.write_text(json.dumps(value))

    def probe(command, **kwargs):
        environment = kwargs["env"]
        assert environment["PUPPETEER_EXECUTABLE_PATH"] == str(browser)
        assert environment["PUPPETEER_SKIP_DOWNLOAD"] == "true"
        directory = kwargs["output_parent"] / "process"
        directory.mkdir()
        (directory / "stdout.bin").write_text(
            json.dumps(
                {
                    "status": "passed",
                    "version": "v" + ("wrong" if change == "version" else versions["node"]),
                    "browser": "Chrome/" + versions["chrome"],
                    "puppeteer": manifest["dependencies"]["puppeteer"],
                    "path": str(tmp_path / "global-browser") if change == "resolver" else str(browser),
                }
            )
        )
        return {"directory": str(directory), "status": "exited", "child_exit_code": 0, "cleanup": {"verified": True}}

    monkeypatch.setattr(adapters, "run_process", probe)
    session = adapters.AdapterSession(ROOT, None, tmp_path, {}, render_report=None if change == "missing" else report)
    session.preflight_render(versions)
    assert session.readiness["render"] is (change == "none")
    if change != "none":
        assert session.inventory["render"]["error"]


@pytest.mark.parametrize("adapter,runtime", [("compatibility", "referee"), ("conformance", "python")])
def test_real_adapter_promotes_failure_into_aggregate_and_markdown(tmp_path, monkeypatch, adapter, runtime):
    error = "Golden inventory mismatch: <preserve>|specific owner error"
    document = {
        "schema_version": 1,
        "passed": 0,
        "failed": 1,
        "error": error,
    }
    if adapter == "compatibility":
        document.update(
            requested_checks=["alpha"],
            canonical_outputs_unchanged=True,
            status="failed",
            checks=[{"id": "alpha", "status": "failed", "error": error}],
        )
    else:
        document.update(suite_count=1, suites=[{"id": "alpha", "status": "failed", "error": error}])
    session = adapters.AdapterSession(tmp_path, scopes.Snapshot({}, {}), tmp_path, {"python": sys.executable})
    session.readiness = {"python": True, "powershell7": True}

    def launch(command, directory, lease, cancel):
        (directory / "stdout.bin").write_text(json.dumps(document))
        return {"directory": str(directory), "status": "exited", "child_exit_code": 1, "cleanup": {"verified": True}}

    monkeypatch.setattr(session, "launch", launch)
    row = {
        **plan()["units"][0],
        "execution_id": f"{adapter}/alpha::{runtime}",
        "adapter": adapter,
        "runtimes": ["python", "powershell7"] if adapter == "compatibility" else ["python"],
        "deadline_seconds": 5,
    }
    results, failures, guard = aggregate.execute_units(
        {"units": [row]}, session.execute, budget(), threading.Event(), lambda: None
    )
    assert results[0]["status"] == "failed" and results[0]["evidence"] == document
    assert failures[0]["excerpt"] == error
    report = controller.empty_report("synthetic", "private-owner")
    report.update(results=results, failures=failures, canonical_guard=guard)
    markdown = sys.modules["execution_reports"].markdown(report)
    assert "Golden inventory mismatch" in markdown and "&lt;preserve&gt;" in markdown
    assert "\\|specific owner error" in markdown


@pytest.mark.parametrize("mode", ["deadline", "cancel"])
@pytest.mark.parametrize("logical_id", ["alpha", "render", "framework-extraction"])
def test_compatibility_adapter_contains_real_nested_child_on_interruption(tmp_path, mode, logical_id):
    runner = tmp_path / "Tools/Compatibility/run_compatibility.py"
    runner.parent.mkdir(parents=True)
    ready = tmp_path / "nested-ready"
    sentinel = tmp_path / "unrelated.txt"
    sentinel.write_bytes(b"keep unrelated artifact")
    child = "import time; from pathlib import Path; Path('nested-ready').write_text('ready'); time.sleep(30)"
    runner.write_text(
        "import sys,json\nfrom pathlib import Path\n"
        f"sys.path.insert(0, {str(ROOT / 'Tools/Compatibility')!r})\n"
        "import run_compatibility as owner\n"
        "identity=sys.argv[sys.argv.index('--check')+1]\n"
        "try:\n"
        "    owner.run_command(owner.Runtime('python',sys.executable), "
        f"[sys.executable,'-c',{child!r}], Path.cwd(), 60)\n"
        "except owner.CompatibilityFailure as error:\n"
        "    print(json.dumps({'schema_version':1,'requested_checks':[identity],'canonical_outputs_unchanged':True,"
        "'status':'failed','passed':0,'failed':1,'checks':[{'id':identity,'status':'failed','error':str(error)}]}),flush=True)\n"
        "    sys.exit(1)\n"
    )
    session = adapters.AdapterSession(tmp_path, scopes.Snapshot({}, {}), tmp_path, {"python": sys.executable})
    session.readiness = {"python": True, "powershell7": True, "render": True}
    cancel = threading.Event()
    stop = threading.Event()

    def cancellation():
        while not stop.wait(0.01):
            if ready.exists():
                cancel.set()
                return

    thread = threading.Thread(target=cancellation)
    if mode == "cancel":
        thread.start()
    try:
        result = session.execute(
            {"adapter": "compatibility", "execution_id": f"compatibility/{logical_id}::referee"},
            processes.Lease(time.monotonic() + (5 if mode == "deadline" else 10)),
            cancel,
            {},
        )
    finally:
        stop.set()
        if mode == "cancel":
            thread.join(timeout=1)
    assert ready.exists(), "The nested child must actually start before testing interruption"
    assert result["status"] == ("failed" if mode == "deadline" else "cancelled")
    if mode == "deadline":
        assert "nested command deadline exceeded" in result["reasons"][0]
    assert result["processes"][0]["cleanup"]["verified"] and session.containment_verified
    assert sentinel.read_bytes() == b"keep unrelated artifact"


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
    native_root = tmp_path / ".tmp/native-synthetic"
    (native_root / "run-one").mkdir(parents=True)
    (native_root / "run-two").mkdir()
    result = session.execute(
        {"adapter": "pytest", "execution_id": "implementation/synthetic::python"},
        processes.Lease(time.monotonic() + 1),
        threading.Event(),
        {},
    )
    assert result["processes"] == [process]
    assert result["status"] == "error" and "Unexpected native run owner" in result["reasons"][-1]


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
        "classification": None,
        "elapsed_seconds": 0,
        "reasons": [],
        "diagnostics": {},
    }
    report = controller.empty_report("synthetic", tmp_path.name)
    report.update(
        profile="synthetic",
        status="passed",
        exit_code=0,
        provenance={"snapshot_digest": "snapshot", "catalog_digests": Catalog.source_digests, "shard_source": source},
        results=[row],
        artifacts=[entry],
        counts={"candidate": 1, "selected": 1, "unselected": 0, "terminal": aggregate.counts([row])},
        selection={"candidate_ids": [row["id"]], "selected_ids": [row["id"]], "unselected": []},
        canonical_guard={"unchanged": True},
        cleanup={"verified": True},
    )
    from execution_reports import finalize

    finalize(tmp_path, report)
    path = tmp_path / "shard-result.json"
    value = {"contract": "ci-shard-result", "contract_version": 1, "source": source, "report": report}
    if change == "snapshot":
        report["provenance"]["snapshot_digest"] = "wrong"
    if change == "artifact":
        process_path.write_text("altered")
    if change == "false-native":
        row["native_counts"] = {"passed": 1}
    if change == "foreign-unit":
        row["id"] = "policy/other::python"
    if change != "valid":
        path.write_text(json.dumps(value))
    bundles = [] if change == "missing" else [path, path] if change == "duplicate" else [path]
    if change == "valid":
        rows, _ = aggregate.collect_shards(Catalog(), "plan", bundles, "snapshot")
        assert rows == [row]
        return
    with pytest.raises((ValueError, KeyError)):
        aggregate.collect_shards(Catalog(), "plan", bundles, "snapshot")
