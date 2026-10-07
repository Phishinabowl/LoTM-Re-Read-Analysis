"""Owned process primitive; real layer adapters and aggregate publication are later gates."""

import ctypes
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import uuid

CAPTURE_LIMIT_BYTES = 64 * 1024 * 1024


def seconds(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("Budget seconds must be finite and positive")
    return value


@dataclass(frozen=True)
class Lease:
    """Absolute monotonic deadline shared by startup, nested execution and adapter verification."""

    deadline: float

    def __post_init__(self):
        if (
            isinstance(self.deadline, bool)
            or not isinstance(self.deadline, (int, float))
            or not math.isfinite(self.deadline)
        ):
            raise ValueError("Finite monotonic deadline required")

    def remaining(self):
        return max(0, self.deadline - time.monotonic())

    def nested(self, timeout):
        return Lease(min(self.deadline, time.monotonic() + seconds(timeout)))

    def verify(self):
        if not self.remaining():
            raise TimeoutError("Whole-unit deadline exhausted, including result verification")


class RunBudget:
    def __init__(self, total, termination, cleanup, finalization, *, started=None):
        self.total = seconds(total)
        self.termination = seconds(termination)
        self.cleanup = seconds(cleanup)
        self.finalization = seconds(finalization)
        reserve = self.termination + self.cleanup + self.finalization
        if reserve >= self.total:
            raise ValueError("Run budget cannot admit execution after lifecycle reserves")
        now = time.monotonic()
        if started is not None and (
            not isinstance(started, (int, float))
            or isinstance(started, bool)
            or not math.isfinite(started)
            or started > now
        ):
            raise ValueError("Run origin must be a finite monotonic timestamp no later than now")
        self.deadline = (now if started is None else started) + self.total
        self.execution_deadline = self.deadline - reserve

    def admit(self, timeout):
        timeout = seconds(timeout)
        # Do not launch a unit unless its complete allowance fits before lifecycle reserves.
        if time.monotonic() + timeout > self.execution_deadline:
            return None
        return Lease(time.monotonic() + timeout)


def plain_directory(value):
    path = Path(value).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Owned process paths cannot traverse links or junctions")
    if not path.is_dir():
        raise ValueError("Process directory must already exist")
    return path.resolve()


def environment(values):
    if not isinstance(values, dict) or not values:
        raise ValueError("Explicit environment allowlist required")
    for key, value in values.items():
        if not isinstance(key, str) or not key or any(char in key for char in "=\0"):
            raise ValueError("Invalid environment key")
        if not isinstance(value, str) or "\0" in value:
            raise ValueError("Invalid environment value")
    if os.name == "nt" and len({key.upper() for key in values}) != len(values):
        raise ValueError("Case-colliding Windows environment keys")
    return dict(values)


def excerpt(path, limit=2048):
    """Bound presentation only. Diagnostic files retain every byte written by the child."""
    with open(path, "rb") as stream:
        stream.seek(0, os.SEEK_END)
        length = stream.tell()
        stream.seek(max(0, length - limit))
        return {"bytes": length, "tail": stream.read().decode("utf-8", errors="replace"), "truncated": length > limit}


class PosixTree:
    def __init__(self, arguments, cwd, env, stdout, stderr):
        if not sys.platform.startswith("linux"):
            raise OSError("Verified POSIX ownership currently requires Linux /proc")
        # Adopt orphaned descendants so completed grandchildren can be reaped independently of host init.
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "Cannot establish Linux child subreaper")
        self.child = subprocess.Popen(
            arguments,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
            close_fds=True,
        )
        self.pid = self.child.pid

    def poll(self):
        return self.child.poll()

    def active(self):
        self.poll()
        # A /proc scan can miss a live root during exit or process-group transitions.
        # Popen owns the root wait status; never publish an exit before it is available.
        if self.child.returncode is None:
            return True
        if self.child.returncode is not None:
            while True:
                try:
                    if os.waitpid(-1, os.WNOHANG)[0] == 0:
                        break
                except ChildProcessError:
                    break
        # Zombie processes cannot execute or write; /proc distinguishes them from live descendants.
        for path in Path("/proc").glob("[0-9]*/stat"):
            try:
                parts = path.read_text().rsplit(")", 1)[1].split()
                if int(parts[2]) == self.pid and parts[0] not in ("Z", "X"):
                    return True
            except (FileNotFoundError, ProcessLookupError):
                continue
        return False

    def graceful(self):
        try:
            os.killpg(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return "SIGTERM-process-group"

    def force(self):
        try:
            os.killpg(self.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def close(self):
        self.poll()


def stop_tree(tree, termination, cleanup):
    if not tree.active():
        return {"graceful": "not-needed", "forced": False, "verified": True}
    graceful = tree.graceful()
    end = time.monotonic() + (termination if graceful != "unsupported-no-shared-console" else 0)
    while tree.active() and time.monotonic() < end:
        time.sleep(0.01)
    forced = tree.active()
    if forced:
        tree.force()
    end = time.monotonic() + cleanup
    while tree.active() and time.monotonic() < end:
        time.sleep(0.01)
    return {"graceful": graceful, "forced": forced, "verified": not tree.active()}


def stop_guardian(child, deadline):
    """Exceptional fallback shares the existing cleanup reserve instead of restarting a timeout."""
    child.terminate()
    remaining = max(0, deadline - time.monotonic())
    try:
        child.wait(timeout=remaining / 2)
        return True
    except subprocess.TimeoutExpired:
        child.kill()
    try:
        child.wait(timeout=max(0, deadline - time.monotonic()))
        return True
    except subprocess.TimeoutExpired:
        return False


def guardian():
    """Private child endpoint. EOF means the owning caller disappeared; control is never inherited."""
    request = json.loads(sys.stdin.readline())
    directory = Path(request["directory"])
    cancellation = threading.Event()
    reason = [None]

    def control():
        line = sys.stdin.readline()
        reason[0] = "caller-cancellation" if line else "caller-disappeared"
        cancellation.set()

    threading.Thread(target=control, daemon=True).start()

    def interrupted(signum, frame):
        reason[0] = "guardian-signal"
        cancellation.set()

    for name in (signal.SIGINT, signal.SIGTERM):
        signal.signal(name, interrupted)
    supervise_owned(request, cancellation, reason)


def captured_bytes(*streams):
    """Inspect file size without querying or changing a child-shared output cursor."""
    return sum(os.fstat(stream.fileno()).st_size for stream in streams)


def supervise_owned(request, cancellation, reason):
    """Guardian implementation separated from its control endpoint for deterministic failure tests."""
    directory = Path(request["directory"])
    tree = None
    record = {
        "contract": "ci-owned-process",
        "contract_version": 1,
        "status": "error",
        "classification": "launch",
        "child_exit_code": None,
        "cleanup": {"verified": True},
        "ownership": "windows-job" if os.name == "nt" else "linux-process-group",
    }
    started = time.monotonic()
    capture_limit = request.get("capture_limit_bytes", CAPTURE_LIMIT_BYTES)
    try:
        with (
            (directory / "stdout.bin").open("xb", buffering=0) as stdout,
            (directory / "stderr.bin").open("xb", buffering=0) as stderr,
        ):
            if cancellation.is_set() or time.monotonic() >= request["deadline"]:
                record.update(
                    status="cancelled" if cancellation.is_set() else "timed-out",
                    classification="cancellation" if cancellation.is_set() else "timeout",
                )
            else:
                if os.name == "nt":
                    from windows_process import WindowsTree

                    tree = WindowsTree(request["arguments"], request["cwd"], request["environment"], stdout, stderr)
                else:
                    tree = PosixTree(request["arguments"], request["cwd"], request["environment"], stdout, stderr)
                (directory / "ownership.json").write_text(
                    json.dumps({"guardian_pid": os.getpid(), "root_pid": tree.pid, "ownership": record["ownership"]}),
                    encoding="utf-8",
                )
                while tree.active() and not cancellation.is_set() and time.monotonic() < request["deadline"]:
                    if captured_bytes(stdout, stderr) > capture_limit:
                        break
                    time.sleep(0.01)
                code = tree.poll()
                captured = captured_bytes(stdout, stderr)
                record["capture"] = {
                    "limit_bytes": capture_limit,
                    "observed_bytes": captured,
                    "exceeded": captured > capture_limit,
                }
                if captured > capture_limit:
                    record.update(
                        status="error",
                        classification="evidence-limit",
                        reason="Combined stdout/stderr capture threshold exceeded",
                    )
                elif cancellation.is_set():
                    record.update(status="cancelled", classification="cancellation", reason=reason[0])
                elif time.monotonic() >= request["deadline"]:
                    record.update(status="timed-out", classification="timeout")
                else:
                    record.update(status="exited", classification=None)
                # Native assertions/coverage are deliberately not inferred from the process exit.
                record["child_exit_code"] = code
                record["cleanup"] = stop_tree(tree, request["termination"], request["cleanup"])
                captured = captured_bytes(stdout, stderr)
                record["capture"].update(observed_bytes=captured, exceeded=captured > capture_limit)
                if captured > capture_limit:
                    record.update(status="error", classification="evidence-limit")
                if record["child_exit_code"] is None:
                    record["child_exit_code"] = tree.poll()
                if not record["cleanup"]["verified"]:
                    record.update(status="error", classification="cleanup")
    except BaseException as error:
        record.update(status="error", error=f"{type(error).__name__}: {error}")
        if tree is not None:
            record["classification"] = "cleanup"
            try:
                record["cleanup"] = stop_tree(tree, request["termination"], request["cleanup"])
            except BaseException as cleanup_error:
                record["cleanup"] = {"verified": False, "error": str(cleanup_error)}
    finally:
        if tree is not None:
            try:
                tree.close()
            except BaseException as error:
                record.update(status="error", classification="cleanup", error=str(error))
                record["cleanup"]["verified"] = False
    record["seconds"] = time.monotonic() - started
    (directory / "process.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def run_process(
    arguments,
    *,
    cwd,
    env,
    output_parent,
    lease,
    termination=1,
    cleanup=2,
    cancel=None,
    capture_limit_bytes=CAPTURE_LIMIT_BYTES,
):
    """Launch one explicitly owned command; retain outputs; return honest process-only status."""
    started = time.monotonic()
    if not isinstance(lease, Lease) or not math.isfinite(lease.deadline):
        raise ValueError("Finite admitted lease required")
    seconds(termination)
    seconds(cleanup)
    if type(capture_limit_bytes) is not int or capture_limit_bytes <= 0:
        raise ValueError("Capture threshold must be a positive integer byte count")
    if (
        not isinstance(arguments, list)
        or not arguments
        or any(not isinstance(value, str) or "\0" in value for value in arguments)
        or not Path(arguments[0]).is_absolute()
    ):
        raise ValueError("Explicit absolute executable and argument array required")
    cwd, parent, env = plain_directory(cwd), plain_directory(output_parent), environment(env)
    directory = parent / ("process-" + uuid.uuid4().hex)
    directory.mkdir()
    base = {
        "contract": "ci-owned-process",
        "contract_version": 1,
        "directory": str(directory),
        "child_exit_code": None,
        "cleanup": {"verified": True},
    }
    if (cancel is not None and cancel.is_set()) or not lease.remaining():
        return {
            **base,
            "status": "cancelled" if lease.remaining() else "blocked",
            "classification": "cancellation" if lease.remaining() else "budget",
            "seconds": 0,
        }
    request = {
        "arguments": arguments,
        "cwd": str(cwd),
        "environment": env,
        "directory": str(directory),
        "deadline": lease.deadline,
        "termination": termination,
        "cleanup": cleanup,
        "capture_limit_bytes": capture_limit_bytes,
    }
    # Only the caller holds the guardian's stdin writer. Target handles cannot inherit it.
    with (directory / "guardian.bin").open("xb") as diagnostic:
        try:
            child = subprocess.Popen(
                [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--guardian"],
                stdin=subprocess.PIPE,
                stdout=diagnostic,
                stderr=diagnostic,
                close_fds=True,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except OSError as error:
            return {
                **base,
                "status": "error",
                "classification": "launch",
                "error": str(error),
                "seconds": time.monotonic() - started,
            }
        requested = False
        lifecycle_deadline = lease.deadline + termination + cleanup
        try:
            child.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
            child.stdin.flush()
            while child.poll() is None:
                if (cancel is not None and cancel.is_set()) and not requested:
                    child.stdin.write(b"cancel\n")
                    child.stdin.flush()
                    requested = True
                    lifecycle_deadline = min(lifecycle_deadline, time.monotonic() + termination + cleanup)
                if time.monotonic() >= lifecycle_deadline - min(0.5, cleanup / 2):
                    # Exceptional stuck guardian: never describe unverified POSIX cleanup as successful.
                    stop_guardian(child, lifecycle_deadline)
                    break
                time.sleep(0.01)
        except (KeyboardInterrupt, BrokenPipeError):
            requested = True
            child.stdin.close()
            lifecycle_deadline = min(lifecycle_deadline, time.monotonic() + termination + cleanup)
            try:
                child.wait(timeout=max(0, lifecycle_deadline - time.monotonic() - min(0.5, cleanup / 2)))
            except subprocess.TimeoutExpired:
                stop_guardian(child, lifecycle_deadline)
        finally:
            if not child.stdin.closed:
                child.stdin.close()
    result_path = directory / "process.json"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result.update(directory=str(directory), seconds=time.monotonic() - started)
    else:
        result = {
            **base,
            "status": "error",
            "classification": "launch",
            "seconds": time.monotonic() - started,
            "error": "Guardian failed without a complete process record",
            "cleanup": {"verified": False},
        }
    if requested and result["status"] == "exited":
        result.update(status="cancelled", classification="cancellation")
    elif result["status"] == "exited" and not lease.remaining():
        result.update(status="timed-out", classification="timeout", reason="caller collection exceeded unit deadline")
    result["diagnostics"] = {
        name: excerpt(directory / name)
        for name in ("stdout.bin", "stderr.bin", "guardian.bin")
        if (directory / name).is_file()
    }
    return result


if __name__ == "__main__":
    if sys.argv[1:] != ["--guardian"]:
        raise SystemExit("Private process guardian; use run_process from the repository supervisor")
    # -I does not put the script directory on sys.path. Load only the colocated backend.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    guardian()
