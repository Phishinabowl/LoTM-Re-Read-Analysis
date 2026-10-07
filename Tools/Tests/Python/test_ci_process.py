"""Synthetic owned trees, whole-lifetime budgets and caller-loss cleanup; no production suite recursion."""

import importlib
import json
import os
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
    processes = importlib.import_module("process_supervisor")
    windows_backend = importlib.import_module("windows_process")
finally:
    sys.path[:] = before


def env():
    names = ("SystemRoot", "WINDIR", "TEMP", "TMP", "HOME", "LANG")
    return {**{name: os.environ[name] for name in names if name in os.environ}, "CI_SYNTHETIC": "yes"}


def execute(tmp_path, code, timeout=5, cancel=None, arguments=None):
    return processes.run_process(
        [sys.executable, "-c", code, *(arguments or [])],
        cwd=tmp_path,
        env=env(),
        output_parent=tmp_path,
        lease=processes.Lease(time.monotonic() + timeout),
        termination=0.15,
        cleanup=1,
        cancel=cancel,
    )


def wait_file(path, timeout=5):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.is_file() and path.stat().st_size:
            if path.suffix == ".json":
                try:
                    json.loads(path.read_text())
                except (ValueError, OSError):
                    time.sleep(0.01)
                    continue
            return
        time.sleep(0.01)
    pytest.fail("Synthetic process did not publish readiness: " + str(path))


def alive(pid):
    if os.name == "nt":
        import ctypes

        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        api.OpenProcess.restype = ctypes.c_void_p
        api.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = api.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return api.WaitForSingleObject(handle, 0) == 258
        finally:
            api.CloseHandle(handle)
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] not in ("Z", "X")
    except FileNotFoundError:
        return False


def test_live_posix_root_is_active_even_when_proc_group_scan_has_no_members(monkeypatch):
    tree = processes.PosixTree.__new__(processes.PosixTree)
    tree.pid = 123
    tree.child = type("Child", (), {"returncode": None, "poll": lambda self: None})()
    monkeypatch.setattr(Path, "glob", lambda *args: [])
    assert tree.active() is True


def tree_code(tmp_path, root_exit=False):
    leaf = (
        "import os,time; from pathlib import Path; Path('grandchild.pid').write_text(str(os.getpid())); time.sleep(20)"
    )
    child = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(leaf) + "]); time.sleep(20)"
    return (
        "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',"
        + repr(child)
        + "]); "
        + ("time.sleep(.3)" if root_exit else "time.sleep(20)")
    )


@pytest.mark.parametrize("value", [0, -1, True, float("inf"), float("nan"), "1"])
def test_budget_rejects_invalid_numbers(value):
    with pytest.raises(ValueError):
        processes.RunBudget(value, 1, 1, 1)


def test_run_reserves_admission_nested_lease_and_verification(monkeypatch):
    tick = [100.0]
    monkeypatch.setattr(processes.time, "monotonic", lambda: tick[0])
    budget = processes.RunBudget(20, 2, 3, 4)
    assert budget.execution_deadline == 111
    assert budget.admit(12) is None
    lease = budget.admit(10)
    assert lease.deadline == 110 and lease.nested(50).deadline == 110
    assert lease.nested(2).deadline == 102
    tick[0] = 110
    with pytest.raises(TimeoutError):
        lease.verify()
    assert budget.admit(2) is None and budget.deadline - tick[0] == 10


def test_reserves_cannot_consume_whole_run():
    with pytest.raises(ValueError):
        processes.RunBudget(3, 1, 1, 1)


@pytest.mark.parametrize("arguments", [[], "echo test", ["python", "-c", "pass"], [sys.executable, "\0"]])
def test_no_shell_or_ambiguous_executable(tmp_path, arguments):
    with pytest.raises(ValueError):
        processes.run_process(
            arguments, cwd=tmp_path, env=env(), output_parent=tmp_path, lease=processes.Lease(time.monotonic() + 1)
        )


@pytest.mark.parametrize("values", [{}, {"a=b": "x"}, {"ok": 1}, {"ok": "\0"}])
def test_explicit_environment_validation(values):
    with pytest.raises(ValueError):
        processes.environment(values)


def test_expired_and_precancelled_do_not_launch(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Unexpected launch"))
    cancel = threading.Event()
    cancel.set()
    result = execute(tmp_path, "pass", cancel=cancel)
    assert result["status"] == "cancelled" and result["cleanup"]["verified"]
    result = execute(tmp_path, "pass", timeout=-1)
    assert result["status"] == "blocked" and result["classification"] == "budget"


def test_empty_tree_never_signals_recycled_process_group():
    class Empty:
        def active(self):
            return False

        def graceful(self):
            pytest.fail("Signalled an empty tree")

    assert processes.stop_tree(Empty(), 0.1, 0.1) == {"graceful": "not-needed", "forced": False, "verified": True}


def test_unverified_cleanup_cannot_pass():
    class Stuck:
        def active(self):
            return True

        def graceful(self):
            return "unsupported-no-shared-console"

        def force(self):
            pass

    assert processes.stop_tree(Stuck(), 0.01, 0.01)["verified"] is False


@pytest.mark.parametrize("remains_stuck", [False, True])
def test_guardian_fallback_waits_share_cleanup_deadline(monkeypatch, remains_stuck):
    tick = [100.0]
    waits = []
    events = []
    monkeypatch.setattr(processes.time, "monotonic", lambda: tick[0])

    class Guardian:
        def terminate(self):
            events.append("terminate")

        def kill(self):
            events.append("kill")

        def wait(self, timeout):
            waits.append(timeout)
            tick[0] += timeout
            if len(waits) == 1 or remains_stuck:
                raise subprocess.TimeoutExpired("synthetic guardian", timeout)
            return 1

    assert processes.stop_guardian(Guardian(), 101) is (not remains_stuck)
    assert waits == [0.5, 0.5] and tick[0] == 101 and events == ["terminate", "kill"]


def test_guardian_launch_failure_is_recorded(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("synthetic guardian launch failure")

    monkeypatch.setattr(subprocess, "Popen", unavailable)
    result = execute(tmp_path, "pass")
    assert result["status"] == "error" and result["classification"] == "launch"
    assert result["cleanup"]["verified"] and "synthetic" in result["error"]


def test_ownership_preflight_failure_never_executes_target(tmp_path, monkeypatch):
    with (tmp_path / "out").open("wb") as stdout, (tmp_path / "err").open("wb") as stderr:
        if os.name == "nt":
            before = sys.path[:]
            try:
                sys.path.insert(0, str(ROOT / "Tools/CI"))
                backend = importlib.import_module("windows_process")
            finally:
                sys.path[:] = before
            original = backend.WindowsTree.check
            calls = [0]

            def failed_limit(value):
                calls[0] += 1
                if calls[0] == 2:
                    raise OSError("synthetic job limit failure")
                return original(value)

            monkeypatch.setattr(backend.WindowsTree, "check", staticmethod(failed_limit))
            with pytest.raises(OSError, match="synthetic"):
                backend.WindowsTree(
                    [sys.executable, "-c", "from pathlib import Path; Path('escaped').touch()"],
                    tmp_path,
                    env(),
                    stdout,
                    stderr,
                )
        else:

            class FailedLibc:
                def prctl(self, *args):
                    return -1

            monkeypatch.setattr(processes.ctypes, "CDLL", lambda *args, **kwargs: FailedLibc())
            monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Executed without ownership"))
            with pytest.raises(OSError, match="subreaper"):
                processes.PosixTree([sys.executable], tmp_path, env(), stdout, stderr)
    assert (tmp_path / "out").read_bytes() == b""
    assert not (tmp_path / "escaped").exists()


def test_output_redirection_links_are_rejected(tmp_path):
    link = tmp_path / "link"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        # Windows without symlink privilege: inspect rejection with an explicit synthetic path probe.
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(Path, "is_symlink", lambda value: value == link)
            with pytest.raises(ValueError, match="links"):
                processes.plain_directory(link)
    else:
        with pytest.raises(ValueError, match="links"):
            processes.plain_directory(link)


@pytest.mark.parametrize("failure", ["unverified", "force-error", "close-error"])
def test_guardian_cleanup_failure_is_retained(tmp_path, monkeypatch, failure):
    class SyntheticTree:
        pid = 12345
        closed = False

        def __init__(self, *args):
            pass

        def active(self):
            return True

        def poll(self):
            return None

        def graceful(self):
            return "unsupported-no-shared-console"

        def force(self):
            if failure == "force-error":
                raise OSError("synthetic force error")

        def close(self):
            SyntheticTree.closed = True
            if failure == "close-error":
                raise OSError("synthetic close error")

    if os.name == "nt":
        monkeypatch.setattr(windows_backend, "WindowsTree", SyntheticTree)
    else:
        monkeypatch.setattr(processes, "PosixTree", SyntheticTree)
    request = {
        "directory": str(tmp_path),
        "arguments": [sys.executable],
        "cwd": str(tmp_path),
        "environment": env(),
        "deadline": time.monotonic() + 0.02,
        "termination": 0.01,
        "cleanup": 0.01,
    }
    processes.supervise_owned(request, threading.Event(), [None])
    result = json.loads((tmp_path / "process.json").read_text())
    assert result["status"] == "error" and result["classification"] == "cleanup"
    assert result["cleanup"]["verified"] is False and SyntheticTree.closed


@pytest.mark.integration
def test_exact_arguments_environment_cwd_and_nonzero_exit(tmp_path, monkeypatch):
    monkeypatch.setenv("FOREIGN_PROCESS_MARKER", "must-not-inherit")
    arguments = ["space value", 'quote"value', "tail\\", "雪", "$(not a shell);&"]
    code = (
        "import json,os,sys; print(json.dumps([sys.argv[1:],os.getenv('CI_SYNTHETIC'),os.getcwd(),"
        "os.getenv('FOREIGN_PROCESS_MARKER')])); sys.exit(7)"
    )
    result = execute(tmp_path, code, arguments=arguments)
    assert result["status"] == "exited" and result["child_exit_code"] == 7 and result["cleanup"]["verified"]
    data = json.loads((Path(result["directory"]) / "stdout.bin").read_text())
    assert data == [arguments, "yes", str(tmp_path), None]


@pytest.mark.integration
def test_noisy_binary_streams_are_complete_and_presentation_bounded(tmp_path):
    code = "import os; [(os.write(1,b'a'*8192),os.write(2,b'b'*8192)) for _ in range(64)]; os.write(2,b'\\xffEND')"
    result = execute(tmp_path, code)
    assert result["status"] == "exited" and result["child_exit_code"] == 0
    assert result["diagnostics"]["stdout.bin"]["bytes"] == 524288
    assert result["diagnostics"]["stderr.bin"]["bytes"] == 524292
    assert result["diagnostics"]["stderr.bin"]["truncated"]
    assert result["diagnostics"]["stderr.bin"]["tail"].endswith("\ufffdEND")


def test_capture_accounting_measures_bytes_without_touching_shared_cursor(tmp_path):
    with (tmp_path / "out").open("w+b", buffering=0) as out, (tmp_path / "err").open("w+b", buffering=0) as err:
        out.write(b"stdout bytes")
        err.write(b"stderr")
        out.seek(2)
        err.seek(1)
        assert processes.captured_bytes(out, err) == 18
        assert out.tell() == 2 and err.tell() == 1


@pytest.mark.integration
def test_incremental_native_output_retains_every_structured_byte(tmp_path):
    expected = json.dumps([{"id": index, "text": "x" * 120} for index in range(3000)]).encode()
    code = """
import ctypes,json,os,time
data=json.dumps([{'id':i,'text':'x'*120} for i in range(3000)]).encode()
if os.name=='nt':
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.GetStdHandle.argtypes=[ctypes.c_ulong]
    api.GetStdHandle.restype=ctypes.c_void_p
    api.WriteFile.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_ulong),ctypes.c_void_p]
    handle=api.GetStdHandle(0xfffffff5)
for start in range(0,len(data),256):
    chunk=data[start:start+256]
    if os.name=='nt':
        count=ctypes.c_ulong()
        assert api.WriteFile(handle,chunk,len(chunk),ctypes.byref(count),None) and count.value==len(chunk)
    else:
        assert os.write(1,chunk)==len(chunk)
    time.sleep(.0001)
"""
    result = execute(tmp_path, code, timeout=8)
    captured = (Path(result["directory"]) / "stdout.bin").read_bytes()
    assert result["status"] == "exited" and result["child_exit_code"] == 0, result
    assert captured == expected
    assert len(json.loads(captured)) == 3000
    assert result["capture"]["observed_bytes"] == len(expected)


@pytest.mark.integration
@pytest.mark.parametrize("root_exit", [False, True])
def test_timeout_includes_grandchildren_even_after_root_exit(tmp_path, root_exit):
    result = execute(tmp_path, tree_code(tmp_path, root_exit), timeout=1.2)
    assert result["status"] == "timed-out" and result["cleanup"]["verified"], result
    assert result["seconds"] < 4
    assert not alive(int((tmp_path / "grandchild.pid").read_text()))


@pytest.mark.integration
def test_cancellation_preserves_foreign_child_and_later_recovery(tmp_path):
    foreign = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(20)"],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    cancel = threading.Event()

    def cancel_ready():
        wait_file(tmp_path / "grandchild.pid")
        cancel.set()

    trigger = threading.Thread(target=cancel_ready)
    trigger.start()
    try:
        result = execute(tmp_path, tree_code(tmp_path), cancel=cancel)
        assert result["status"] == "cancelled" and result["cleanup"]["verified"], result
        assert not alive(int((tmp_path / "grandchild.pid").read_text()))
        assert foreign.poll() is None
        recovery = execute(tmp_path, "print('recovered')")
        assert recovery["status"] == "exited" and recovery["child_exit_code"] == 0
        assert recovery["directory"] != result["directory"]
        assert (Path(result["directory"]) / "process.json").exists()
    finally:
        trigger.join(timeout=5)
        foreign.terminate()
        foreign.wait(timeout=3)


@pytest.mark.integration
def test_missing_executable_is_launch_error_and_outputs_retained(tmp_path):
    result = processes.run_process(
        [str(tmp_path / "missing-executable")],
        cwd=tmp_path,
        env=env(),
        output_parent=tmp_path,
        lease=processes.Lease(time.monotonic() + 5),
        termination=0.1,
        cleanup=1,
    )
    assert result["status"] == "error" and result["classification"] == "launch", result
    assert result["cleanup"]["verified"] and "error" in result


@pytest.mark.integration
def test_hard_caller_termination_releases_tree_and_retains_record(tmp_path):
    script = tmp_path / "caller.py"
    script.write_text(
        "import sys,time\nsys.path.insert(0," + repr(str(ROOT / "Tools/CI")) + ")\n"
        "from process_supervisor import run_process,Lease\n"
        "run_process("
        + repr([sys.executable, "-c", tree_code(tmp_path)])
        + ",cwd="
        + repr(str(tmp_path))
        + ",env="
        + repr(env())
        + ",output_parent="
        + repr(str(tmp_path))
        + ",lease=Lease(time.monotonic()+15),termination=.1,cleanup=1)\n",
        encoding="utf-8",
    )
    caller = subprocess.Popen(
        [sys.executable, str(script)], creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )
    try:
        wait_file(tmp_path / "grandchild.pid")
        pid = int((tmp_path / "grandchild.pid").read_text())
        caller.kill()
        caller.wait(timeout=3)
        directory = next(tmp_path.glob("process-*"))
        wait_file(directory / "process.json")
        record = json.loads((directory / "process.json").read_text())
        assert record["status"] == "cancelled" and record["reason"] == "caller-disappeared"
        assert record["cleanup"]["verified"] and not alive(pid)
    finally:
        if caller.poll() is None:
            caller.kill()
            caller.wait(timeout=3)


@pytest.mark.integration
def test_platform_graceful_and_forced_termination(tmp_path):
    code = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready',flush=True); time.sleep(20)"
    result = execute(tmp_path, code, timeout=0.8)
    assert result["status"] == "timed-out" and result["cleanup"]["verified"] and result["cleanup"]["forced"]
    assert result["cleanup"]["graceful"] == (
        "unsupported-no-shared-console" if os.name == "nt" else "SIGTERM-process-group"
    )


@pytest.mark.integration
def test_supported_graceful_exit_and_keyboard_interrupt(tmp_path, monkeypatch):
    result = execute(tmp_path, "import time; print('ready',flush=True); time.sleep(20)", timeout=0.5)
    assert result["status"] == "timed-out" and result["cleanup"]["verified"]
    assert result["cleanup"]["forced"] is (os.name == "nt")
    original_sleep = processes.time.sleep
    first = [True]

    def interrupt_once(value):
        if first[0]:
            first[0] = False
            raise KeyboardInterrupt
        original_sleep(value)

    monkeypatch.setattr(processes.time, "sleep", interrupt_once)
    result = execute(tmp_path, "import time; time.sleep(20)")
    assert result["status"] == "cancelled" and result["cleanup"]["verified"], result


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_capture_limit_rejects_invalid_threshold_before_launch(tmp_path, limit):
    with pytest.raises(ValueError, match="Capture threshold"):
        processes.run_process(
            [sys.executable, "-c", "pass"],
            cwd=tmp_path,
            env=env(),
            output_parent=tmp_path,
            lease=processes.Lease(time.monotonic() + 1),
            capture_limit_bytes=limit,
        )


@pytest.mark.integration
@pytest.mark.parametrize("stream", [1, 2])
def test_output_threshold_retains_diagnostics_terminates_owned_child_and_recovers(tmp_path, stream):
    code = f"import os,time;os.write({stream},b'complete diagnostic '*4096);time.sleep(10)"
    result = processes.run_process(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env(),
        output_parent=tmp_path,
        lease=processes.Lease(time.monotonic() + 3),
        termination=0.15,
        cleanup=1,
        capture_limit_bytes=32768,
    )
    assert result["status"] == "error" and result["classification"] == "evidence-limit", result
    assert result["cleanup"]["verified"] and result["capture"]["exceeded"]
    assert result["diagnostics"]["stdout.bin" if stream == 1 else "stderr.bin"]["bytes"] > 32768
    assert execute(tmp_path, "print('later independent child')")["status"] == "exited"
