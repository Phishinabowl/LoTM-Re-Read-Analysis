"""Single native group adapter; catalog supervision and process-tree control remain Phase 4."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

import bootstrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Commands/Environment"))
from powershell_process import isolated_command  # noqa: E402
from native_results import classify, parse_junit, publication_xml, validate_phase

ROOT = Path(__file__).resolve().parents[2]


def owned_output(value):
    path = Path(value).resolve()
    owner = (ROOT / ".tmp").resolve()
    if not owner.is_relative_to(ROOT.resolve()) or not path.is_relative_to(owner):
        raise ValueError("Native output must stay beneath owned checkout .tmp storage")
    return path


def execute(args):
    identity = args.group + "." + args.runtime
    native_root = ROOT / "Tools/Tests" / ("Python" if args.runtime == "python" else "PowerShell")
    suffix = ".py" if args.runtime == "python" else ".Tests.ps1"
    paths = (
        [Path(value).resolve() for value in args.path]
        if args.path
        else sorted(native_root.glob("test_*.py" if args.runtime == "python" else "*.Tests.ps1"))
    )
    if not paths or any(
        not path.is_file() or not path.is_relative_to(native_root.resolve()) or not path.name.endswith(suffix)
        for path in paths
    ):
        raise ValueError("Native selection must contain existing files confined to its runtime test root")
    destination = owned_output(args.output_root)
    destination.mkdir(parents=True, exist_ok=True)
    run_dir = destination / ("run-" + uuid.uuid4().hex)
    run_dir.mkdir()
    owned_output(run_dir)
    xml = run_dir / "native.xml"
    phase_file = run_dir / "native-phases.json"
    env = bootstrap.clean_environment()
    for name in ("KNOWLEDGE_PROJECT_ROOT", "KNOWLEDGE_FRAMEWORK_ROOT", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(name, None)
    result = {
        "contract": "native-test-run",
        "contract_version": 1,
        "identity": identity,
        "runtime": args.runtime,
        "paths": [path.relative_to(ROOT).as_posix() for path in paths],
        "status": "error",
        "classification": "prerequisite",
        "exit_code": 1,
        "child_exit_code": None,
        "native_counts": None,
        "artifacts": {"stdout": "stdout.log", "stderr": "stderr.log"},
        "run_directory": str(run_dir),
    }
    start = time.perf_counter()
    stdout = stderr = ""
    try:
        if args.runtime == "python":
            version = bootstrap.read_json(bootstrap.DATA / "runtime-versions.json")["python"]
            probe = subprocess.run(
                [
                    args.executable,
                    "-I",
                    "-c",
                    "import sys,pytest;assert sys.version.split()[0]==sys.argv[1];assert pytest.__version__=='9.1.1'",
                    version,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if probe.returncode:
                raise RuntimeError("Exact Python/pytest prerequisite unavailable\n" + probe.stdout + probe.stderr)
            env["PYTHONPATH"] = str(ROOT / "Tools/CI")
            env["NATIVE_PHASE_REPORT"] = str(phase_file)
            command = [
                args.executable,
                "-m",
                "pytest",
                "-p",
                "native_pytest_observer",
                "--junitxml=" + str(xml),
                "--junit-prefix=" + identity,
                "-q",
                "-o",
                "junit_logging=all",
                *map(str, paths),
            ]
            if args.filter:
                command += ["-k", args.filter]
        else:
            request = run_dir / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "paths": list(map(str, paths)),
                        "xml": str(xml),
                        "phase": str(phase_file),
                        "identity": identity,
                        "filter": args.filter,
                    }
                ),
                encoding="utf-8",
            )
            command = [
                args.executable,
                "-NoProfile",
                "-File",
                str(ROOT / "Tools/CI/Invoke-NativePester.ps1"),
                "-Request",
                str(request),
            ]
        result["classification"] = "launch"
        child = subprocess.run(
            isolated_command(command, env) if args.runtime == "powershell7" else command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout,
        )
        stdout, stderr = child.stdout, child.stderr
        result["child_exit_code"] = child.returncode
        result["classification"] = "result-contract"
        phase = json.loads(phase_file.read_text(encoding="utf-8-sig")) if phase_file.is_file() else {}
        if child.returncode == 130 or phase.get("interrupted"):
            result.update(status="cancelled", classification="cancellation", exit_code=130)
        elif not phase:
            result["classification"] = (
                "prerequisite" if args.runtime == "powershell7" and "Pester" in stderr else "result-contract"
            )
            raise RuntimeError("Native phase report unavailable; framework output retained")
        else:
            validate_phase(args.runtime, child.returncode, phase)
            tree, cases, counts = parse_junit(xml)
            result["native_counts"] = {"collected": phase["collected"], **counts}
            result["phase_evidence"] = phase
            publication_xml(tree, identity, run_dir / "junit.xml", ROOT if args.runtime == "powershell7" else None)
            result["status"], result["classification"], result["exit_code"] = classify(
                args.runtime, child.returncode, phase, counts
            )
            result["artifacts"].update(
                native_xml="native.xml", publication_xml="junit.xml", native_phases="native-phases.json"
            )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        stdout = stdout.decode("utf-8", errors="replace") if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode("utf-8", errors="replace") if isinstance(stderr, bytes) else stderr
        result.update(status="timed-out", classification="timeout", exit_code=1, error=str(error))
    except KeyboardInterrupt:
        result.update(status="cancelled", classification="cancellation", exit_code=130)
    except Exception as error:
        result["error"] = str(error)
        stderr += "\n" + str(error)
    result["seconds"] = time.perf_counter() - start
    for name, path in [("native_xml", xml), ("native_phases", phase_file)]:
        if path.is_file():
            result["artifacts"][name] = path.name
    try:
        (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    except OSError as error:
        result.update(status="error", classification="report", exit_code=1, error=str(error))
        print("Native result finalization failed: " + str(error), file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=["python", "powershell7"], required=True)
    parser.add_argument("--executable", required=True)
    parser.add_argument("--group", default="native-pilot")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--filter")
    parser.add_argument("--output-root", default=".tmp/native-tests")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if not re.fullmatch("[a-z][a-z0-9-]*", args.group) or not 0 < args.timeout <= 3600:
        parser.error("Require a stable group ID and timeout between 0 and 3600 seconds")
    try:
        result = execute(args)
    except Exception as error:
        result = {
            "contract": "native-test-run",
            "contract_version": 1,
            "status": "error",
            "classification": "scope",
            "exit_code": 2,
            "error": str(error),
        }
    print(json.dumps(result, indent=2))
    raise SystemExit(result["exit_code"])


if __name__ == "__main__":
    main()
