"""Explicitly install and verify a reviewed wheel; never invoked implicitly by pytest."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import bootstrap
from package_artifact import inspect_wheel

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIRECTORIES = ("Framework/Packs", "Framework/Data/Strict-Yaml", "Framework/Data/Framework-Catalog")
FIXTURE_FILES = (
    "Framework/framework.yaml",
    "Framework/capability-roadmap.yaml",
    "Framework/platform-implementation-plan.md",
    "Framework/Data/unicode-lookup-16.0.0.json",
    "Framework/Data/lookup-key-regression-vectors.json",
)


def clean_environment():
    environment = bootstrap.clean_environment()
    for name in ("KNOWLEDGE_FRAMEWORK_ROOT", "KNOWLEDGE_PROJECT_ROOT"):
        environment.pop(name, None)
    return environment


def prepare_consumer(target):
    for name in FIXTURE_DIRECTORIES:
        shutil.copytree(ROOT / name, target / name)
    for name in FIXTURE_FILES:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    # Reuse the existing synthetic extraction consumer, not the canonical LoTM project manifest.
    spec = importlib.util.spec_from_file_location(
        "extraction_fixture", ROOT / "Tools/Compatibility/neutral_consumer.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.write_neutral_consumer(target)
    files = sorted(path for path in target.rglob("*") if path.is_file())
    return {path.relative_to(target).as_posix(): bootstrap.digest(path) for path in files}


def verify(wheel, installer, report, runtime_wheel=None):
    start = time.perf_counter()
    metadata, files = bootstrap.package_metadata()
    contract = inspect_wheel(wheel, ROOT, bootstrap.source_version(), files, metadata["project"])
    versions = bootstrap.read_json(bootstrap.DATA / "runtime-versions.json")
    pins, identity, lock = bootstrap.python_plan("runtime", False, versions)
    if runtime_wheel is None:
        payload_cache = bootstrap.owned_path(ROOT / ".local/ci-cache/python" / bootstrap.key_for(identity))
        # Verification uses already acquired payloads only, including their committed published digests.
        bootstrap.acquire_wheels(pins, payload_cache, lock, offline=True, check=True)
        yaml_wheel = payload_cache / bootstrap.wheel_for(lock["packages"]["pyyaml"])["filename"]
    else:
        yaml_wheel = Path(runtime_wheel).resolve()
        row = bootstrap.wheel_for(lock["packages"]["pyyaml"])
        if yaml_wheel.name != row["filename"] or bootstrap.digest(yaml_wheel) != row["sha256"]:
            raise ValueError("Explicit runtime wheel does not match the committed platform lock")
    contract["yaml_version"] = pins["pyyaml"]
    contract["python_version"] = versions["python"]
    interpreter = json.loads(
        bootstrap.run(
            [
                installer,
                "-I",
                "-c",
                "import sys,importlib.metadata as m,json;"
                "print(json.dumps({'python':'.'.join(map(str,sys.version_info[:3])),'pip':m.version('pip')}))",
            ]
        )
    )
    if interpreter != {"python": versions["python"], "pip": versions["pip"]}:
        raise ValueError("Installer must use the adopted interpreter and exact pip")
    results = []
    temporary_path = None
    environment = clean_environment()
    try:
        with tempfile.TemporaryDirectory(prefix="knowledge-installed-package-") as temporary:
            owner = Path(temporary).resolve()
            temporary_path = owner
            if owner.is_relative_to(ROOT.resolve()):
                raise ValueError("Installed-package verification must execute outside the checkout")
            prefix = owner / "environment"
            # No global/user packages, pip/build tools or editable links in the runtime environment.
            bootstrap.run([installer, "-I", "-m", "venv", "--without-pip", prefix], cwd=owner, environment=environment)
            executable = prefix / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            probe = owner / "probe.py"
            shutil.copy2(ROOT / "Tools/CI/installed_package_probe.py", probe)
            contract_file = owner / "contract.json"
            contract_file.write_text(json.dumps(contract), encoding="utf-8")
            neutral = owner / "consumer"
            neutral.mkdir()
            fixture_inputs = prepare_consumer(neutral)

            def execute(name, command, *, expected_error=None):
                began = time.perf_counter()
                result = subprocess.run(
                    [str(value) for value in command],
                    cwd=owner,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                passed = (
                    result.returncode == 0
                    if expected_error is None
                    else result.returncode != 0 and expected_error in result.stderr
                )
                row = {
                    "id": name,
                    "passed": passed,
                    "exit_code": result.returncode,
                    "seconds": time.perf_counter() - began,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
                results.append(row)
                if not passed:
                    raise RuntimeError(f"Installed verification failed: {name}\n{result.stdout}\n{result.stderr}")
                return result.stdout

            probe_command = [executable, "-I", probe, "--contract", contract_file, "--identity-only"]
            execute("missing-installation", probe_command, expected_error="No module named 'knowledge_framework'")
            install = [
                installer,
                "-I",
                "-m",
                "pip",
                "--python",
                prefix,
                "--isolated",
                "install",
                "--no-index",
                "--no-deps",
            ]
            execute("install-wheel-only", install + [wheel])
            execute("missing-runtime-dependency", probe_command, expected_error="No module named 'yaml'")
            execute("install-declared-runtime", install + [yaml_wheel])
            installed = json.loads(
                execute(
                    "installed-neutral-semantics",
                    [executable, "-I", probe, "--contract", contract_file, "--root", neutral],
                )
            )
            wrong_version = {**contract, "version": "99.0.0"}
            contract_file.write_text(json.dumps(wrong_version), encoding="utf-8")
            execute("incompatible-package-version", probe_command, expected_error="Installed package version mismatch")
            contract_file.write_text(json.dumps({**contract, "yaml_version": "99.0.0"}), encoding="utf-8")
            execute(
                "incompatible-runtime-version",
                probe_command,
                expected_error="Installed runtime dependency version mismatch",
            )
            contract_file.write_text(json.dumps(contract), encoding="utf-8")
            package_file = Path(installed["origin"])
            original = package_file.read_bytes()
            package_file.write_bytes(original + b"\n# altered installed content\n")
            try:
                execute("altered-installed-code", probe_command, expected_error="Installed module differs from wheel")
            finally:
                package_file.write_bytes(original)
            execute("installed-pip-check", [installer, "-I", "-m", "pip", "--python", prefix, "--isolated", "check"])
            # An inherited source path/root cannot turn a missing installation into a pass.
            empty_prefix = owner / "empty-environment"
            bootstrap.run(
                [installer, "-I", "-m", "venv", "--without-pip", empty_prefix], cwd=owner, environment=environment
            )
            empty_python = empty_prefix / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            environment["PYTHONPATH"] = str(ROOT / "Tools/Runtime/Python")
            environment["KNOWLEDGE_PROJECT_ROOT"] = str(ROOT)
            execute(
                "source-path-cannot-satisfy-missing-installation",
                [empty_python, "-I", probe, "--contract", contract_file, "--identity-only"],
                expected_error="No module named 'knowledge_framework'",
            )
            result = {
                "schema_version": 1,
                "status": "passed",
                "wheel": str(wheel),
                "wheel_sha256": bootstrap.digest(wheel),
                "artifact": contract,
                "installed": installed,
                "fixtures": fixture_inputs,
                "checks": results,
            }
    except Exception as error:
        result = {"schema_version": 1, "status": "failed", "error": str(error), "checks": results}
    result.update(
        seconds=time.perf_counter() - start,
        temporary_directory=str(temporary_path) if temporary_path else None,
        cleanup_complete=temporary_path is not None and not temporary_path.exists(),
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["status"] != "passed":
        raise RuntimeError(result["error"])
    print(
        f"Installed package verification passed: {len(contract['members'])} wheel members, "
        f"{len(results)} installation checks ({result['seconds']:.3f}s). Report: {report}"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-and-verify", action="store_true", required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--installer-python", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--runtime-wheel", type=Path, help="Explicit already acquired locked PyYAML wheel for captured execution."
    )
    args = parser.parse_args()
    report = args.report.resolve()
    if not report.is_relative_to((ROOT / ".tmp").resolve()) or not (ROOT / ".tmp").resolve().is_relative_to(
        ROOT.resolve()
    ):
        parser.error("Report must stay inside the checkout owned .tmp directory")
    verify(args.wheel.resolve(), args.installer_python.resolve(), report, args.runtime_wheel)


if __name__ == "__main__":
    main()
