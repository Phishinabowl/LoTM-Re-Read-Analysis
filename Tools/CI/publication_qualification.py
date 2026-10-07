"""Manual-only, isolated publication probes; never a substitute for catalog PR coverage."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True

import bootstrap
import host_cache
import publish_hosted
from execution_reports import atomic_bytes, confined, encoded, finalize, fingerprint
from native_results import parse_junit, publication_xml
from process_supervisor import Lease, run_process
from scope import Git

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "manual-publication-qualification"


def tracked_digest(root):
    names = Git(root).read("ls-files", "-z").decode().split("\0")
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names if name}


def probe_environment(setup):
    # The guardian persists its request. Keep host/API credentials out of that evidence.
    names = ("SystemRoot", "WINDIR", "TEMP", "TMP", "HOME", "LANG", "LC_ALL", "PATH")
    return {
        **{name: os.environ[name] for name in names if name in os.environ},
        "PYTHONUTF8": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "LOTM_CI_MODULE_ROOT": setup["powershell"]["module_path"].split(os.pathsep)[0],
    }


def context(host, environment, root):
    executed = Git(root).resolve("HEAD")
    if host == "github":
        if environment["GITHUB_EVENT_NAME"] != "workflow_dispatch" or executed != environment["GITHUB_SHA"]:
            raise ValueError("Qualification requires exact manual GitHub checkout")
        from github_shadow import event_context

        value = event_context({}, environment)
    else:
        if environment["BUILD_REASON"] != "Manual":
            raise ValueError("Qualification is forbidden in policy PR execution")
        from ado_shadow import event_context

        value = event_context(environment)
        if value["executed"] != executed:
            raise ValueError("Qualification differs from exact manual Azure checkout")
    value["profile"] = PROFILE
    return value


def prepare(host):
    out = confined(ROOT, ".tmp/ci-publication-qualification")
    out.mkdir(parents=True, exist_ok=False)
    value = context(host, os.environ, ROOT)
    atomic_bytes(out, "context.json", encoded(value))
    pwsh = host_cache.runtime()
    child = subprocess.run(
        [
            sys.executable,
            str(ROOT / "Tools/CI/bootstrap.py"),
            "--python-profile",
            "development",
            "--powershell-profile",
            "development",
            "--pwsh",
            pwsh,
            "--environment-id",
            "publication-qualification",
            "--source-revision",
            value["executed"],
            "--report",
            str(out / "bootstrap.json"),
        ],
        cwd=ROOT,
        timeout=300,
        check=False,
    )
    if child.returncode:
        return child.returncode
    setup = bootstrap.read_json(out / "bootstrap.json")
    if setup["status"] != "passed":
        raise ValueError("Verified qualification runtime required")
    if host == "github":
        from github_shadow import output
    else:
        from ado_shadow import output
    output(python=setup["python"]["executable"])
    return 0


def native_command(root, runtime, failed, setup, directory):
    fixture = directory / ("test_qualification.py" if runtime == "python" else "Qualification.Tests.ps1")
    xml = directory / "native.xml"
    if runtime == "python":
        fixture.write_text("def test_publication_qualification():\n    assert 1 == " + ("2" if failed else "1") + "\n")
        return [setup["python"]["executable"], "-m", "pytest", str(fixture), "-q", "--junitxml=" + str(xml)], xml
    fixture.write_text(
        "Describe 'Publication qualification' { It 'preserves a real Pester result' { 1 | Should -Be "
        + ("2" if failed else "1")
        + " } }\n"
    )
    runner = directory / "invoke.ps1"
    runner.write_text(
        "$ErrorActionPreference = 'Stop'\nImport-Module Pester -RequiredVersion 6.2.0\n"
        "$c = New-PesterConfiguration\n$c.Run.Path = Join-Path $PSScriptRoot 'Qualification.Tests.ps1'\n"
        "$c.Run.PassThru = $true\n$c.Run.Parallel = $false\n$c.Run.Shuffle = $false\n"
        "$c.Run.Exit = $false\n$c.TestRegistry.Enabled = $false\n$c.Output.Verbosity = 'Minimal'\n"
        "$c.TestResult.Enabled = $true\n$c.TestResult.OutputFormat = 'JUnitXml'\n"
        "$c.TestResult.OutputPath = Join-Path $PSScriptRoot 'native.xml'\n"
        "$c.TestResult.OutputEncoding = 'UTF8'\n$r = Invoke-Pester -Configuration $c\n"
        "if ($r.TotalCount -ne 1 -or $r.FailedContainersCount -or $r.FailedBlocksCount) { exit 2 }\n"
        "if ($r.FailedCount) { exit 1 }\nexit 0\n",
        encoding="utf-8",
    )
    sys.path.insert(0, str(root / "Tools/Commands/Environment"))
    from powershell_process import isolated_command

    environment = probe_environment(setup)
    return isolated_command([setup["powershell"]["executable"], "-NoProfile", "-File", str(runner)], environment), xml


def probe(root, scenario, value, setup):
    from aggregate_execution import counts
    from run_ci import empty_report

    workspace = confined(root, ".tmp/ci-publication-qualification/" + scenario)
    workspace.mkdir(parents=True, exist_ok=False)
    owner = workspace / "execution" / ("run-" + uuid.uuid4().hex)
    owner.mkdir(parents=True)
    report = empty_report(PROFILE, owner.name)
    report["runtime_inventory"] = {name: setup[name] for name in ("python", "powershell")}
    report["provenance"] = {"executed_commit": value["executed"], "mode": PROFILE, "qualification_scenario": scenario}
    before = tracked_digest(root)
    rows = []
    runtimes = ("python", "powershell7") if scenario in {"assertion", "passing"} else ("python",)
    for runtime in runtimes:
        directory = owner / "units" / runtime
        directory.mkdir(parents=True)
        native = scenario in {"assertion", "passing"}
        if native:
            command, xml = native_command(root, runtime, scenario == "assertion", setup, directory)
        else:
            program = (
                "import time; print('qualification child started', flush=True); time.sleep(60)"
                if scenario == "timeout"
                else "print('qualification control passed')"
            )
            command = [setup["python"]["executable"], "-I", "-c", program]
        environment = probe_environment(setup)
        process = run_process(
            command,
            cwd=directory,
            env=environment,
            output_parent=directory,
            lease=Lease(time.monotonic() + (5 if scenario == "timeout" else 30)),
        )
        identity = ("implementation" if native else "qualification") + "/publication-" + scenario + "::" + runtime
        expected = "timed-out" if scenario == "timeout" else "exited"
        if process["status"] != expected or process["cleanup"]["verified"] is not True:
            raise ValueError("Unexpected qualification process outcome: " + json.dumps(process))
        status = "timed-out" if scenario == "timeout" else "failed" if scenario == "assertion" else "passed"
        if scenario != "timeout" and process["child_exit_code"] != (1 if scenario == "assertion" else 0):
            raise ValueError("Unexpected qualification child exit")
        reasons = ["Manual publication qualification only; not catalog coverage."]
        if scenario == "publication":
            reasons.append("Deliberately withhold staged XML after admission; the native upload task must fail.")
        if status != "passed":
            reasons.append(json.dumps(process["diagnostics"], ensure_ascii=False))
        if scenario == "missing":
            status = "error"
            reasons.append("Deliberately withhold the worker bundle; execution evidence remains in this artifact.")
        paths = [path.relative_to(owner).as_posix() for path in directory.rglob("*") if path.is_file()]
        native_counts = None
        if native:
            document, cases, observed = parse_junit(xml)
            if len(cases) != 1 or observed["failed"] != (1 if scenario == "assertion" else 0):
                raise ValueError("Unexpected native qualification inventory")
            publication_xml(
                document,
                identity,
                directory / "publication.xml",
                source_root=directory if runtime == "powershell7" else None,
            )
            paths.append((directory / "publication.xml").relative_to(owner).as_posix())
            native_counts = {
                "collected": len(cases),
                **{key: observed[key] for key in ("passed", "failed", "errors", "skipped")},
            }
        rows.append(
            {
                "id": identity,
                "owner": "implementation" if native else "qualification",
                "runtime": runtime,
                "status": status,
                "classification": None
                if status == "passed"
                else "timeout"
                if scenario == "timeout"
                else "result-contract"
                if scenario == "missing"
                else "assertion",
                "elapsed_seconds": process["seconds"],
                "reasons": reasons,
                "native_counts": native_counts,
                "artifacts": paths,
                "diagnostics": process,
                "attempts": 1,
            }
        )
        report["artifacts"].extend(fingerprint(owner, path) for path in paths)
    identities = [row["id"] for row in rows]
    report["results"] = rows
    report["selection"] = {
        "candidate_ids": identities,
        "selected_ids": identities,
        "unselected": [],
        "applied_mode": "manual-qualification",
        "fallback_reasons": [],
    }
    report["counts"] = {"candidate": len(rows), "selected": len(rows), "unselected": 0, "terminal": counts(rows)}
    report["status"], report["exit_code"] = (
        ("passed", 0) if all(row["status"] == "passed" for row in rows) else ("failed", 1)
    )
    report["failures"] = [
        {"id": row["id"], "classification": row["classification"], "excerpt": "\n".join(row["reasons"])}
        for row in rows
        if row["status"] != "passed"
    ]
    report["canonical_guard"] = {"unchanged": before == tracked_digest(root)}
    report["cleanup"] = {
        "verified": all(row["diagnostics"]["cleanup"]["verified"] for row in rows),
        "state": "processes-stopped; evidence-retained",
    }
    report["budget"] = {"elapsed_seconds": sum(row["elapsed_seconds"] for row in rows)}
    finalize(owner, report)
    if scenario != "missing":
        from github_shadow import export_bundle

        export_bundle(owner, workspace / ".tmp/ci-shadow/bundle")
    return report["exit_code"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "execute", "publish"))
    parser.add_argument("--host", choices=("github", "ado"), required=True)
    parser.add_argument("--mode", choices=("passing", "failures"), required=True)
    args = parser.parse_args()
    if args.operation == "prepare":
        return prepare(args.host)
    out = confined(ROOT, ".tmp/ci-publication-qualification")
    value = bootstrap.read_json(out / "context.json")
    if value != context(args.host, os.environ, ROOT):
        raise ValueError("Manual qualification context changed")
    scenarios = ["passing"] if args.mode == "passing" else ["assertion", "timeout", "missing", "publication"]
    if args.operation == "execute":
        setup = bootstrap.read_json(out / "bootstrap.json")
        exits = {scenario: probe(ROOT, scenario, value, setup) for scenario in scenarios}
        atomic_bytes(out, "execution.json", encoded(exits))
        return int(any(exits.values()))
    receipts, categories, failed = [], {key: [] for key in ("python", "powershell", "custom")}, False
    for scenario in scenarios:
        workspace = confined(ROOT, ".tmp/ci-publication-qualification/" + scenario)
        destination, receipt = publish_hosted.admit(workspace, value)
        try:
            publish_hosted.submit(destination, receipt, os.environ)
        except OSError as error:
            receipt.update(status="failed", error=str(error))
        if receipt["status"] == "admitted":
            for entry in receipt["xml"]:
                if scenario != "publication":
                    categories[entry["category"]].append(confined(destination, entry["path"]).as_posix())
        if scenario == "publication" and receipt["status"] == "admitted" and receipt["xml"]:
            # This owned staged copy alone is withheld. Native task must reject the exact missing input.
            target = confined(destination, receipt["xml"][0]["path"])
            target.unlink()
            receipt["deliberate_publication_fault"] = target.as_posix()
        atomic_bytes(destination, "receipt.json", encoded(receipt))
        receipts.append({"scenario": scenario, **receipt})
        failed |= receipt["status"] != "admitted"
    atomic_bytes(out, "publication.json", encoded(receipts))
    if args.host == "ado":
        from ado_shadow import output

        values = {key + "_files": "\n".join(paths) for key, paths in categories.items()}
        values.update({key + "_enabled": "true" if paths else "false" for key, paths in categories.items()})
        values["fault_file"] = next(
            (row["deliberate_publication_fault"] for row in receipts if "deliberate_publication_fault" in row), ""
        )
        output(**values)
    else:
        from github_shadow import output

        output(
            fault_file=next(
                (row["deliberate_publication_fault"] for row in receipts if "deliberate_publication_fault" in row), ""
            )
        )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
