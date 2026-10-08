"""Manual hosted private/restored qualification; external cache seals are admitted by the PS driver."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootstrap
from process_supervisor import Lease, plain_directory, run_process

ROOT = Path(__file__).resolve().parents[2]

PROBE = r"""
import ctypes, importlib.util, json, pathlib, platform, ssl, sqlite3, struct, sys, sysconfig
import venv, ensurepip, _ssl, _sqlite3
prefix, base, executable, version, mode = sys.argv[1:]
prefix, base, executable = map(lambda p:pathlib.Path(p).resolve(), (prefix, base, executable))
assert sys.version.split()[0] == version
assert sys.implementation.name == 'cpython' and not sysconfig.get_config_var('Py_GIL_DISABLED')
assert platform.machine().lower() in ('amd64', 'x86_64')
assert struct.calcsize('P') == 8 and sysconfig.get_platform().endswith(('amd64', 'x86_64'))
assert sys.flags.isolated and sys.flags.dont_write_bytecode
assert pathlib.Path(sys.prefix).resolve() == prefix and pathlib.Path(sys.base_prefix).resolve() == base
assert pathlib.Path(sys.executable).resolve() == executable
modules = (ssl, sqlite3, venv, ensurepip, _ssl, _sqlite3)
for module in modules:
    assert getattr(module, '__file__', None), 'Expected file-backed qualification module: ' + module.__name__
origins = {m.__name__:str(pathlib.Path(m.__file__).resolve()) for m in modules}
assert all(pathlib.Path(p).is_relative_to(base) for p in origins.values())
sqlite3.connect(':memory:').execute('select 1').fetchone()
if mode == 'base':
    assert importlib.util.find_spec('pip') is None
if sys.platform == 'win32':
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    kernel.GetModuleHandleW.argtypes = (ctypes.c_wchar_p,)
    kernel.GetModuleFileNameW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong)
    handle = kernel.GetModuleHandleW('python314.dll')
    assert handle
    buffer = ctypes.create_unicode_buffer(32768)
    count = kernel.GetModuleFileNameW(handle, buffer, len(buffer))
    assert 0 < count < len(buffer)
    core = [str(pathlib.Path(buffer.value).resolve())]
else:
    maps = pathlib.Path('/proc/self/maps').read_text().splitlines()
    core = sorted({line.split(maxsplit=5)[-1].strip() for line in maps
                   if 'libpython3.14.so' in line and len(line.split(maxsplit=5)) == 6})
assert core and all(pathlib.Path(p).resolve().is_relative_to(base) for p in core)
print(json.dumps({'version':version, 'prefix':str(prefix), 'base_prefix':str(base), 'executable':str(executable),
                  'origins':origins, 'core_library':core, 'isolated':True, 'no_bytecode':True, 'mode':mode}))
"""


def load_linux_release_reference(check_budget=lambda: None):
    """Read only repository-owned declarations; a runtime receipt cannot replace this reference."""
    data = plain_directory(ROOT / "Tools/CI/Data")

    def read(name):
        check_budget()
        path = data / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 2 * 1024 * 1024:
            raise ValueError("Plain bounded repository reference required")
        encoded = path.read_bytes()
        if len(encoded) > 2 * 1024 * 1024:
            raise ValueError("Reference size limit exceeded")

        def unique(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("Duplicate repository reference JSON key")
                value[key] = item
            return value

        result = json.loads(encoded.decode("utf-8"), object_pairs_hook=unique)
        check_budget()
        return result, hashlib.sha256(encoded).hexdigest()

    def fields(value, names):
        if not isinstance(value, dict) or set(value) != set(names):
            raise ValueError("Exact repository reference fields required")

    versions = bootstrap.read_json(data / "runtime-versions.json")
    if (
        not isinstance(versions, dict)
        or not isinstance(versions.get("python"), str)
        or not re.fullmatch(r"3\.14\.[0-9]+", versions["python"])
    ):
        raise ValueError("Exact adopted Python pin required")
    version = versions["python"]
    spec, _ = read("python-linux-release-reference-spec.json")
    fields(spec, ("schema_version", "reference_file", "reference_sha256", "expected_inventory_sha256", "identity"))
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("Release reference specification revision differs")
    identity = spec["identity"]
    fields(
        identity,
        (
            "normalization",
            "provider",
            "provider_build",
            "python",
            "implementation",
            "gil",
            "image_family",
            "architecture",
            "asset",
            "archive_sha256",
        ),
    )
    expected = {
        "normalization": "native-core-v2-linux-release-modes",
        "provider": "actions/python-versions",
        "python": version,
        "implementation": "cpython",
        "gil": "enabled",
        "image_family": "ubuntu-24.04",
        "architecture": "x64",
        "asset": f"python-{version}-linux-24.04-x64.tar.gz",
    }
    if (
        any(not isinstance(value, str) for value in identity.values())
        or any(identity[key] != value for key, value in expected.items())
        or not re.fullmatch(re.escape(version) + "-[0-9]+", identity["provider_build"])
        or not re.fullmatch("[0-9a-f]{64}", identity["archive_sha256"])
        or spec["reference_file"] != f"python-linux-{version}-reference.json"
    ):
        raise ValueError("Pinned repository release identity differs")
    for key in ("reference_sha256", "expected_inventory_sha256"):
        if not isinstance(spec[key], str) or not re.fullmatch("[0-9a-f]{64}", spec[key]):
            raise ValueError("Typed release reference digest required")
    reference, digest = read(spec["reference_file"])
    fields(reference, ("contract", "schema_version", "identity", "inventory"))
    if (
        digest != spec["reference_sha256"]
        or reference["contract"] != "ci-python-linux-release-reference"
        or type(reference["schema_version"]) is not int
        or reference["schema_version"] != 1
        or reference["identity"] != identity
    ):
        raise ValueError("Repository release reference bytes or identity differ")
    inventory = reference["inventory"]
    fields(inventory, ("schema_version", "root_unix_mode", "entries", "sha256"))
    frame = {"root_unix_mode": inventory["root_unix_mode"], "entries": inventory["entries"]}
    if (
        type(inventory["schema_version"]) is not int
        or inventory["schema_version"] != 3
        or type(inventory["root_unix_mode"]) is not int
        or inventory["root_unix_mode"] != 0o755
        or inventory["sha256"] != spec["expected_inventory_sha256"]
        or hashlib.sha256(json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        != inventory["sha256"]
    ):
        raise ValueError("Repository release inventory differs")
    check_budget()
    return {"identity": identity, "sha256": digest, "inventory_sha256": inventory["sha256"]}, inventory


def validate_release_binding(receipt, inventory, check_budget=lambda: None):
    reference, expected_inventory = load_linux_release_reference(check_budget)
    if receipt.get("reference") != reference or json.dumps(
        inventory, sort_keys=True, separators=(",", ":")
    ) != json.dumps(expected_inventory, sort_keys=True, separators=(",", ":")):
        raise ValueError("Candidate must match the external repository reference")
    if type(receipt.get("source_root_mode")) is not int or receipt["source_root_mode"] not in (0o755, 0o777):
        raise ValueError("Qualified native source-root mode required")
    changes = receipt.get("mode_changes")
    if not isinstance(changes, list) or len(changes) > len(inventory["entries"]):
        raise ValueError("Bounded mode-change evidence required")
    modes = {row["path"]: row.get("unix_mode") for row in inventory["entries"]}
    previous = None
    for change in changes:
        check_budget()
        if (
            not isinstance(change, dict)
            or set(change) != {"path", "from", "to"}
            or not isinstance(change["path"], str)
            or change["path"] not in modes
            or type(change["from"]) is not int
            or change["from"] != 0o777
            or type(change["to"]) is not int
            or change["to"] not in (0o644, 0o755)
            or change["to"] != modes[change["path"]]
            or (previous is not None and previous.encode("utf-16-be") >= change["path"].encode("utf-16-be"))
        ):
            raise ValueError("Exact ordinal qualified mode-change evidence required")
        previous = change["path"]


def validate_payload(candidate, receipt, *, lease=None, cancellation=None):
    """Verify the complete mode-aware copy before execution; receipt is not a cache trust anchor."""
    candidate = plain_directory(candidate)

    def check_budget():
        if lease is not None:
            lease.verify()
        if cancellation is not None and cancellation.is_set():
            raise TimeoutError("Candidate verification cancelled")

    check_budget()
    if (
        receipt.get("contract") != "ci-python-runtime-candidate"
        or receipt.get("status") != "candidate-complete"
        or type(receipt.get("schema_version")) is not int
        or receipt["schema_version"] not in (1, 2)
    ):
        raise ValueError("Completed fresh candidate receipt required")
    v2 = receipt["schema_version"] == 2
    expected_normalization = "native-core-v2-linux-release-modes" if v2 else "native-core-v1"
    if receipt.get("normalization") != expected_normalization or any(
        receipt.get(key) is not False for key in ("trusted_seal", "handoff_admitted", "saved", "runtime_probe_verified")
    ):
        raise ValueError("Qualification must not promote a candidate to trusted cache admission")
    inventory = receipt["inventory"]
    if v2:
        if sys.platform != "linux":
            raise ValueError("Release-mode qualification is Linux-only")
        validate_release_binding(receipt, inventory, check_budget)
    if type(inventory["schema_version"]) is not int or inventory["schema_version"] != 3:
        raise ValueError("Strict mode-aware candidate inventory required")
    entries = inventory["entries"]
    if (
        not isinstance(entries, list)
        or not entries
        or len(entries) > 200000
        or not re.fullmatch("[0-9a-f]{64}", inventory["sha256"])
    ):
        raise ValueError("Bounded complete candidate inventory required")
    for row in entries:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("path"), str)
            or row.get("kind") not in ("file", "directory", "symlink")
        ):
            raise ValueError("Typed candidate inventory entries required")
        if row["kind"] == "file" and (
            type(row.get("bytes")) is not int
            or not 0 <= row["bytes"] <= 256 * 1024 * 1024
            or not re.fullmatch("[0-9a-f]{64}", row.get("sha256", ""))
        ):
            raise ValueError("Typed bounded file metadata required")
        if (
            sys.platform == "linux"
            and row["kind"] != "symlink"
            and (type(row.get("unix_mode")) is not int or not 0 <= row["unix_mode"] <= 4095)
        ):
            raise ValueError("Typed Unix mode metadata required")
    frame = {"root_unix_mode": inventory["root_unix_mode"], "entries": entries}
    encoded = json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != inventory["sha256"]:
        raise ValueError("Candidate inventory digest differs from its receipt")
    paths = [row["path"] for row in entries]
    if len(set(paths)) != len(paths) or paths != sorted(paths, key=lambda p: p.encode("utf-16-be")):
        raise ValueError("Candidate inventory paths must be unique and ordinal")
    expected = dict(zip(paths, entries, strict=True))
    seen = set()
    root_mode = stat.S_IMODE(candidate.stat().st_mode) if sys.platform == "linux" else None
    if root_mode != inventory["root_unix_mode"]:
        raise ValueError("Candidate root mode differs")
    for directory, directories, files in os.walk(candidate, followlinks=False):
        for name in directories + files:
            check_budget()
            path = Path(directory) / name
            if hasattr(path, "is_junction") and path.is_junction():
                raise ValueError("Candidate junctions are not qualified")
            relative = path.relative_to(candidate).as_posix()
            if (
                relative not in expected
                or any(p in ("", ".", "..") for p in relative.split("/"))
                or re.search(r"[\\:\x00-\x1f]", relative)
            ):
                raise ValueError("Unexpected or unsafe candidate path: " + relative)
            row = expected[relative]
            info = path.lstat()
            if path.is_symlink():
                if path.is_dir() or row["kind"] != "symlink" or os.readlink(path).replace("\\", "/") != row["target"]:
                    raise ValueError("Candidate link differs: " + relative)
                target = path.parent / row["target"]
                if (
                    PurePosixPath(row["target"]).is_absolute()
                    or re.search(r"[\\:\x00-\x1f]", row["target"])
                    or target.is_symlink()
                ):
                    raise ValueError("Candidate link is not a relative direct file")
                resolved = target.resolve(strict=True)
                if not resolved.is_relative_to(candidate) or not resolved.is_file():
                    raise ValueError("Candidate link escapes or lacks its target")
            elif stat.S_ISDIR(info.st_mode):
                if row["kind"] != "directory":
                    raise ValueError("Candidate directory differs")
            elif stat.S_ISREG(info.st_mode):
                if row["kind"] != "file" or info.st_nlink > 1 or info.st_size != row["bytes"]:
                    raise ValueError("Candidate file metadata differs")
                with path.open("rb") as stream:
                    opened = os.fstat(stream.fileno())
                    if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        raise ValueError("Candidate file changed before hashing")
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                after = path.lstat()
                if digest != row["sha256"] or (after.st_ino, after.st_size, after.st_mtime_ns) != (
                    info.st_ino,
                    info.st_size,
                    info.st_mtime_ns,
                ):
                    raise ValueError("Candidate file bytes differ: " + relative)
            else:
                raise ValueError("Nonregular candidate node")
            if sys.platform == "linux" and not path.is_symlink() and stat.S_IMODE(info.st_mode) != row["unix_mode"]:
                raise ValueError("Candidate Unix mode differs: " + relative)
            seen.add(relative)
    if seen != set(expected):
        raise ValueError("Candidate inventory files are missing")
    check_budget()
    return candidate


def child_environment(candidate, values=None):
    allowed = {
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "PROGRAMDATA",
        "WINDIR",
        "TEMP",
        "TMP",
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_ARCHITEW6432",
    }
    values = os.environ if values is None else values
    env = {key: value for key, value in values.items() if key.upper() in allowed}
    env.update(PYTHONUTF8="1", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    if sys.platform == "linux":
        env["LD_LIBRARY_PATH"] = str(candidate / "lib")
    return env


class QualificationProcessError(RuntimeError):
    def __init__(self, result):
        self.result = result
        super().__init__("Candidate child failed: " + json.dumps(result, ensure_ascii=False))


def step(command, output, env, lease, cancellation):
    result = run_process(command, cwd=ROOT, env=env, output_parent=output, lease=lease, cancel=cancellation)
    if result["status"] != "exited" or result["child_exit_code"] != 0 or not result["cleanup"]["verified"]:
        raise QualificationProcessError(result)
    return result, Path(result["directory"]) / "stdout.bin"


def admit_probe(value, prefix, base, executable, version, mode):
    if (
        not isinstance(value, dict)
        or value.get("version") != version
        or value.get("mode") != mode
        or any(value.get(name) is not True for name in ("isolated", "no_bytecode"))
    ):
        raise ValueError("Candidate probe contract differs")
    for name, expected in (("prefix", prefix), ("base_prefix", base), ("executable", executable)):
        if Path(value.get(name, "")).resolve() != Path(expected).resolve():
            raise ValueError("Candidate probe ownership differs")
    origins = value.get("origins", {})
    core = value.get("core_library", [])
    if (
        not isinstance(origins, dict)
        or set(origins) != {"ssl", "sqlite3", "venv", "ensurepip", "_ssl", "_sqlite3"}
        or not isinstance(core, list)
        or not core
    ):
        raise ValueError("Candidate core-library and module evidence is incomplete")
    if any(
        not isinstance(p, str) or not Path(p).resolve().is_relative_to(Path(base).resolve())
        for p in [*origins.values(), *core]
    ):
        raise ValueError("Candidate module/core library escaped its owner")
    return value


def qualify(candidate, receipt, output, revision, identity):
    candidate = plain_directory(candidate)
    output = plain_directory(output)
    processes = output / "qualification-processes"
    processes.mkdir(exist_ok=False)
    versions = bootstrap.read_json(bootstrap.DATA / "runtime-versions.json")
    executable = candidate / ("python.exe" if sys.platform == "win32" else "bin/python3.14")
    env = child_environment(candidate)
    cancel = threading.Event()
    handlers = {}
    if threading.current_thread() is threading.main_thread():
        for name in (signal.SIGINT, signal.SIGTERM):
            handlers[name] = signal.signal(name, lambda *_: cancel.set())
    lease = Lease(time.monotonic() + 600)
    report = {
        "contract": "ci-python-candidate-qualification",
        "schema_version": 1,
        "executed_commit": revision,
        "status": "failed",
        "runtime_probe_verified": False,
        "reference_verified": False,
        "environment_verified": False,
        "provider_build_verified": False,
        "trusted_seal": False,
        "restoration_verified": False,
        "handoff_admitted": False,
        "saved": False,
        "processes": [],
    }
    try:
        validate_payload(candidate, receipt, lease=lease, cancellation=cancel)
        report["normalization"] = receipt["normalization"]
        if receipt["schema_version"] == 2:
            report.update(
                reference_verified=True,
                reference=receipt["reference"],
                source_root_mode=receipt["source_root_mode"],
                mode_changes=len(receipt["mode_changes"]),
            )
        arguments = [
            str(executable),
            "-I",
            "-B",
            "-c",
            PROBE,
            str(candidate),
            str(candidate),
            str(executable),
            versions["python"],
            "base",
        ]
        result, stdout = step(arguments, processes, env, lease.nested(60), cancel)
        report["processes"].append(result)
        report["base_probe"] = admit_probe(
            json.loads(stdout.read_text(encoding="utf-8")), candidate, candidate, executable, versions["python"], "base"
        )
        report["runtime_probe_verified"] = True
        validate_payload(candidate, receipt, lease=lease, cancellation=cancel)
        bootstrap_report = output / "candidate-bootstrap.json"
        env["LOTM_CI_UNIT_DEADLINE"] = str(lease.deadline)
        command = [
            str(executable),
            "-I",
            "-B",
            str(ROOT / "Tools/CI/bootstrap.py"),
            "--python-profile",
            "runtime",
            "--package-mode",
            "source",
            "--no-base-bytecode",
            "--environment-id",
            identity,
            "--source-revision",
            revision,
            "--report",
            str(bootstrap_report),
            "--json",
        ]
        result, _ = step(command, processes, env, lease.nested(360), cancel)
        report["processes"].append(result)
        built = bootstrap.read_json(bootstrap_report)
        if built["status"] != "passed" or built["python"]["environment_created"] is not True:
            raise ValueError("Fresh locked project bootstrap proof required")
        environment_exe = Path(built["python"]["executable"])
        environment_prefix = Path(built["python"]["prefix"])
        if not environment_prefix.resolve().is_relative_to((ROOT / ".local/ci-environments").resolve()):
            raise ValueError("Project environment escaped its owner")
        validate_payload(candidate, receipt, lease=lease, cancellation=cancel)
        command = [
            str(environment_exe),
            "-I",
            "-B",
            "-c",
            PROBE,
            str(environment_prefix),
            str(candidate),
            str(environment_exe),
            versions["python"],
            "environment",
        ]
        result, stdout = step(command, processes, env, lease.nested(60), cancel)
        report["processes"].append(result)
        report["environment_probe"] = admit_probe(
            json.loads(stdout.read_text(encoding="utf-8")),
            environment_prefix,
            candidate,
            environment_exe,
            versions["python"],
            "environment",
        )
        report["bootstrap"] = built
        report["environment_verified"] = True
        validate_payload(candidate, receipt, lease=lease, cancellation=cancel)
        report.update(status="qualification-passed", payload_unchanged=True)
    except (OSError, ValueError, RuntimeError, TimeoutError) as error:
        report["error"] = str(error)
        failed_process = error.result if isinstance(error, QualificationProcessError) else None
        if failed_process is not None:
            report["failed_process"] = failed_process
        if cancel.is_set() or (failed_process or {}).get("status") == "cancelled":
            report["status"] = "cancelled"
        elif isinstance(error, TimeoutError) or (failed_process or {}).get("status") in ("timed-out", "blocked"):
            report["status"] = "timed-out"
        try:
            validate_payload(candidate, receipt, lease=Lease(time.monotonic() + 20))
            report["payload_unchanged"] = True
        except (OSError, ValueError, TimeoutError):
            report["payload_unchanged"] = False
    finally:
        report["exit_code"] = {"qualification-passed": 0, "cancelled": 130, "timed-out": 124}.get(report["status"], 1)
        for name, handler in handlers.items():
            signal.signal(name, handler)
        (output / "candidate-qualification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--restored", action="store_true", help="Guarded owned-prefix restoration pilot only")
    args = parser.parse_args()
    if (
        os.environ.get("TF_BUILD") != "True"
        or os.environ.get("BUILD_REASON") != "Manual"
        or (
            os.environ.get("LOTM_RUNTIME_RESTORE") != "hosted-restore-qualification-only"
            if args.restored
            else os.environ.get("CAPTURE_MODE") != "candidate"
        )
    ):
        raise ValueError("Candidate execution requires the explicit manual hosted pilot")
    if Path(os.environ["BUILD_SOURCESDIRECTORY"]).resolve() != ROOT or not re.fullmatch(
        "[0-9a-f]{40}", os.environ["BUILD_SOURCEVERSION"]
    ):
        raise ValueError("Hosted checkout/source ownership differs")
    candidate = plain_directory(args.candidate)
    output = plain_directory(args.output)
    if args.restored:
        versions = bootstrap.read_json(bootstrap.DATA / "runtime-versions.json")
        tools = plain_directory(Path(os.environ["AGENT_TOOLSDIRECTORY"]))
        fixed = Path("C:/hostedtoolcache/windows" if sys.platform == "win32" else "/opt/hostedtoolcache")
        image = "windows-2022" if sys.platform == "win32" else "ubuntu-24.04"
        if (
            sys.platform not in ("win32", "linux")
            or tools != fixed
            or os.environ.get("RESTORE_IMAGE") != image
            or not re.fullmatch("[1-9][0-9]*", os.environ.get("BUILD_BUILDID", ""))
            or candidate != tools / "Python" / versions["python"] / "x64"
            or output != ROOT / ".tmp/ci-runtime-restore"
        ):
            raise ValueError("Restored runtime requires the declared native prefix and diagnostic owner")
    elif (
        not candidate.is_relative_to(ROOT / ".tmp/ci-runtime-candidates") or output != ROOT / ".tmp/ci-runtime-capture"
    ):
        raise ValueError("Hosted candidate/output owner differs")
    receipt_path = args.receipt.resolve()
    if receipt_path != output / "candidate.json" or args.receipt.is_symlink():
        raise ValueError("Hosted candidate receipt owner differs")
    identity = (
        "runtime-restored-" + os.environ["BUILD_BUILDID"]
        if args.restored
        else "runtime-candidate-" + os.environ["BUILD_BUILDID"] + "-" + os.environ["CAPTURE_ID"]
    )
    result = qualify(candidate, bootstrap.read_json(receipt_path), output, os.environ["BUILD_SOURCEVERSION"], identity)
    print("Candidate qualification: " + result["status"])
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
