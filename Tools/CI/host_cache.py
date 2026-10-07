"""CI 6.1 payload-cache pilot; no profile adoption or test membership authority."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile

import bootstrap

ROOT = Path(__file__).resolve().parents[2]
INPUTS = (
    "Tools/CI/Data/runtime-versions.json",
    "Tools/CI/Data/python-wheel-lock.json",
    "Tools/CI/bootstrap.py",
    "Tools/CI/host_cache.py",
    "Tools/CI/Install-PowerShellRequirements.ps1",
    "Tools/CI/Probe-PowerShellModules.ps1",
    "Tools/Commands/Environment/dependency_requirements.py",
    "Tools/Commands/Environment/Private/Requirements.ps1",
    "Tools/CI/Node/package.json",
    "Tools/CI/Node/package-lock.json",
    "pyproject.toml",
)
ARCHIVES = {
    "win32": ("PowerShell-7.6.6-win-x64.zip", "02fe458be20493fbdf43f61ea20610b811ee6c738ab1676c61b9cfcd1a33c860"),
    "linux": ("powershell-7.6.6-linux-x64.tar.gz", "ddbc4a2d113bbd46d283cfedcbcd117a70caefd7673f41f2b4e0000badf103bc"),
}


def cache_identity(root, namespace, system=None, architecture=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", namespace):
        raise ValueError("Cache namespace must be a bounded lowercase label")
    system = system or sys.platform
    architecture = (architecture or platform.machine()).lower()
    if system not in ARCHIVES or architecture not in {"amd64", "x86_64"}:
        raise ValueError("Cache pilot supports Windows/Linux x64 only")
    inputs = sorted(set(INPUTS) | {p.name for p in root.glob("requirements-*.txt")})
    hashes = {}
    for name in inputs:
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Cache input escapes source: " + name)
        hashes[name] = bootstrap.digest(path)
    identity = {"schema_version": 1, "os": system, "architecture": "x64", "inputs": hashes}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {**identity, "namespace": namespace, "key": f"lotm-payload-v1-{system}-x64-{namespace}-{digest}"}


def runtime():
    """Use exact existing PS or acquire a hash-pinned portable copy, never a machine install."""
    version = bootstrap.read_json(ROOT / "Tools/CI/Data/runtime-versions.json")["powershell"]
    if version != "7.6.6":
        raise ValueError("Review portable release hashes when changing the adopted PS runtime")
    host = shutil.which("pwsh")
    command = ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]
    if host and bootstrap.run([host, *command], timeout=30).strip() == version:
        return host
    name, expected = ARCHIVES[sys.platform]
    owner = bootstrap.owned_path(ROOT / ".local/ci-tools/powershell-7.6.6")
    if owner.exists():
        raise ValueError("Existing portable runtime owner requires inspection; no implicit replacement")
    owner.mkdir(parents=True)
    archive = owner / name
    with (
        urllib.request.urlopen(
            f"https://github.com/PowerShell/PowerShell/releases/download/v{version}/{name}", timeout=120
        ) as response,
        archive.open("xb") as destination,
    ):
        shutil.copyfileobj(response, destination)
    if bootstrap.digest(archive) != expected:
        raise ValueError("Portable PowerShell archive digest mismatch")
    if sys.platform == "win32":
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(owner / "files")
        host = owner / "files/pwsh.exe"
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(owner / "files", filter="data")
        host = owner / "files/pwsh"
        host.chmod(0o755)
    if bootstrap.run([host, *command], timeout=30).strip() != version:
        raise ValueError("Portable PowerShell version mismatch")
    return str(host)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "bootstrap"))
    parser.add_argument("--namespace", default="pilot-1")
    parser.add_argument("--host", choices=("local", "github", "ado"), default="local")
    parser.add_argument("--cache-hit", choices=("true", "false"), default="false")
    parser.add_argument("--expect", choices=("auto", "hit", "miss"), default="auto")
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
        parser.error("Full source revision required")
    out = (ROOT / ".tmp/ci-cache-pilot").resolve()
    if not out.is_relative_to(ROOT.resolve()):
        raise ValueError("Pilot report destination escapes repository")
    out.mkdir(parents=True, exist_ok=True)
    identity = cache_identity(ROOT, args.namespace)
    (out / "identity.json").write_text(json.dumps(identity, indent=2), encoding="utf-8")
    if args.operation == "prepare":
        bootstrap.owned_path(ROOT / ".local/ci-cache").mkdir(parents=True, exist_ok=True)
        if args.host == "github":
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
                stream.write("key=" + identity["key"] + "\n")
        elif args.host == "ado":
            print("##vso[task.setvariable variable=payloadCacheKey]" + identity["key"])
        print("Payload key: " + identity["key"])
        return 0
    hit = args.cache_hit == "true"
    if (args.expect == "hit" and not hit) or (args.expect == "miss" and hit):
        raise ValueError("Observed host cache status does not match the requested experiment")
    if list((ROOT / ".local/ci-environments/python").glob("*/host-pilot-fresh")):
        raise ValueError("Pilot requires a fresh environment; existing pilot owner is not reused or removed")
    started = time.perf_counter()
    pwsh = runtime()
    command = [
        sys.executable,
        str(ROOT / "Tools/CI/bootstrap.py"),
        "--media",
        "--powershell-profile",
        "development",
        "--pwsh",
        pwsh,
        "--environment-id",
        "host-pilot-fresh",
        "--source-revision",
        args.source_revision,
        "--report",
        str(out / "bootstrap.json"),
    ]
    if hit:
        command.append("--offline")
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=bootstrap.clean_environment(),
        timeout=720,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (out / "bootstrap.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    evidence = {
        "schema_version": 1,
        "host": args.host,
        "source_revision": args.source_revision,
        "key": identity["key"],
        "host_cache_hit": hit,
        "expected": args.expect,
        "exit_code": result.returncode,
        "setup_seconds": time.perf_counter() - started,
        "transport_timing": "Read restore/save task durations from the hosted run; excluded here",
        "scope": "Python development/media wheels and PowerShell development modules",
    }
    (out / "pilot.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(result.stdout + result.stderr)
    return result.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        failure = (ROOT / ".tmp/ci-cache-pilot/failure.json").resolve()
        if failure.is_relative_to(ROOT.resolve()):
            failure.parent.mkdir(parents=True, exist_ok=True)
            failure.write_text(json.dumps({"status": "failed", "error": str(error)}, indent=2), encoding="utf-8")
        print(f"Cache pilot failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
