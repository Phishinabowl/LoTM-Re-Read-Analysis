"""Manual Windows agent qualification using existing runners and owned process fixtures."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bootstrap
from execution_reports import atomic_bytes, encoded, verify_publication
import publication_qualification as publication
from scope import Git
from catalog import Catalog

ROOT = Path(__file__).resolve().parents[2]


def command(arguments, directory, name, environment, timeout):
    start = time.perf_counter()
    with (
        (directory / (name + ".stdout.log")).open("wb") as stdout,
        (directory / (name + ".stderr.log")).open("wb") as stderr,
    ):
        result = subprocess.run(
            arguments, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, timeout=timeout, check=False
        )
    return {"exit_code": result.returncode, "seconds": time.perf_counter() - start}


def execute(mode, setup, output, source, scope="hosted-commit"):
    if setup["status"] != "passed" or Git(ROOT).resolve("HEAD") != source:
        raise ValueError("Passing bootstrap and exact source required")
    if scope == "hosted-commit" and Git(ROOT).read("status", "--porcelain=v1", "-z", "--untracked-files=all"):
        raise ValueError("Hosted qualification requires a clean exact-source checkout")
    if output.exists() or not output.resolve().is_relative_to(ROOT / ".tmp"):
        raise ValueError("Pilot output must be a new owned .tmp child")
    output.mkdir(parents=True)
    environment = publication.probe_environment(setup)
    # The real runner invokes Git; preserve Windows home metadata, not host/API credentials.
    environment.update(
        {name: os.environ[name] for name in ("USERPROFILE", "HOMEDRIVE", "HOMEPATH") if name in os.environ}
    )
    environment["PSModulePath"] = setup["powershell"]["module_path"]
    python = setup["python"]["executable"]
    pwsh = setup["powershell"]["executable"]
    record = {"mode": mode, "source": source, "validation_scope": scope, "full_profile_acceptance": False, "steps": {}}
    before = publication.tracked_digest(ROOT)
    if mode == "workload":
        arguments = [
            python,
            str(ROOT / "Tools/CI/run_ci.py"),
            "--profile",
            "ci-infrastructure",
            "--scope",
            scope,
            "--host-kind",
            "ado" if scope == "hosted-commit" else "local",
            "--python",
            python,
            "--pwsh",
            pwsh,
            "--module-root",
            setup["powershell"]["module_path"].split(os.pathsep)[0],
            "--output-root",
            str(output / "infrastructure"),
            "--json",
        ]
        if scope == "hosted-commit":
            arguments.extend(["--base", Git(ROOT).resolve(source + "^"), "--source", source, "--executed", source])
        record["steps"]["infrastructure"] = command(arguments, output, "infrastructure", environment, 1320)
        owners = list((output / "infrastructure").glob("run-*"))
        if len(owners) != 1:
            raise ValueError("Expected one infrastructure owner")
        verify_publication(owners[0])
        result = bootstrap.read_json(owners[0] / "report.json")
        expected = [row["execution_id"] for row in Catalog(ROOT).plan("ci-infrastructure", "windows", None)["units"]]
        if result["selection"].get("selected_ids") != expected or [row["id"] for row in result["results"]] != expected:
            raise ValueError("Workload differs from the registered infrastructure profile")
        record["infrastructure"] = {
            "status": result["status"],
            "counts": result["counts"],
            "cleanup": result["cleanup"],
            "canonical_guard": result["canonical_guard"],
        }
        print("##vso[task.uploadsummary]" + str(owners[0] / "summary.md"), flush=True)
        arguments = [
            pwsh,
            "-NoProfile",
            "-File",
            str(ROOT / "Tools/Conformance/Run-Conformance.ps1"),
            "-Suite",
            "project-root",
            "-ReportOutput",
            str(output / "powershell-project-root.json"),
            "-TimeoutSeconds",
            "120",
        ]
        record["steps"]["powershell-project-root"] = command(
            arguments, output, "powershell-project-root", environment, 180
        )
        record["powershell_conformance"] = bootstrap.read_json(output / "powershell-project-root.json")
        if (
            record["powershell_conformance"]["suite_count"] != 1
            or record["powershell_conformance"]["suites"][0]["id"] != "project-root"
        ):
            raise ValueError("Supplemental conformance differs from the registered project-root suite")
        code = int(any(row["exit_code"] for row in record["steps"].values()))
    elif mode == "failure":
        # Keep the existing publication probe's canonical owners and native assertion failures.
        for scenario in ("assertion", "passing"):
            record["steps"][scenario] = {"exit_code": publication.probe(ROOT, scenario, {"executed": source}, setup)}
        if record["steps"]["assertion"]["exit_code"] != 1 or record["steps"]["passing"]["exit_code"] != 0:
            raise ValueError("Expected assertion failure followed by independent passing recovery")
        record["expected_failure_observed"] = True
        record["later_recovery_passed"] = True
        code = 1  # Deliberate failure must remain red in ADO.
    else:
        spec = importlib.util.spec_from_file_location(
            "km_owned_process_fixture", ROOT / "Tools/Tests/Python/test_ci_process.py"
        )
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
        cancelled = threading.Event()
        for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
            if hasattr(signal, name):
                signal.signal(getattr(signal, name), lambda *_: cancelled.set())
        atomic_bytes(
            output,
            "cancel-ready.json",
            encoded({"source": source, "owned_fixture": "test_ci_process.tree_code", "hold_seconds": 300}),
        )
        print(
            "KM cancellation fixture starting; wait for grandchild.pid before requesting ADO cancellation.", flush=True
        )
        result = fixture.execute(output, fixture.tree_code(output, lifetime=300), timeout=330, cancel=cancelled)
        record["process"] = result
        code = 130 if result["status"] == "cancelled" else 1
    record["canonical_source_unchanged"] = before == publication.tracked_digest(ROOT)
    if not record["canonical_source_unchanged"]:
        code = 1
    record["exit_code"] = code
    atomic_bytes(output, "qualification.json", encoded(record))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("workload", "failure", "cancel"), required=True)
    parser.add_argument("--bootstrap-report", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    if (
        os.environ.get("BUILD_REASON") != "Manual"
        or os.environ.get("BUILD_SOURCEBRANCH") != "refs/heads/architecture/ci-testing-modernization"
        or os.environ.get("BUILD_SOURCEVERSION") != args.source
    ):
        raise ValueError("Pilot requires exact manually dispatched modernization source")
    return execute(args.mode, bootstrap.read_json(args.bootstrap_report), args.output_root.resolve(), args.source)


if __name__ == "__main__":
    raise SystemExit(main())
