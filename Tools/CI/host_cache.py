"""CI 6.1 payload-cache pilot; no profile adoption or test membership authority."""

import argparse
import hashlib
import json
import math
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
import xml.etree.ElementTree as ET
import zipfile

import bootstrap

ROOT = Path(__file__).resolve().parents[2]
INPUTS = (
    "Tools/CI/Data/runtime-versions.json",
    "Tools/CI/Data/python-wheel-lock.json",
    "Tools/CI/bootstrap.py",
    "Tools/CI/host_cache.py",
    "Tools/CI/github_shadow.py",
    "Tools/Commands/Environment/powershell_process.py",
    "Tools/Commands/Environment/Invoke-OwnedPowerShell.ps1",
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
NODE_ARCHIVES = {
    "win32": ("node-v24.15.0-win-x64.zip", "cc5149eabd53779ce1e7bdc5401643622d0c7e6800ade18928a767e940bb0e62"),
    "linux": ("node-v24.15.0-linux-x64.tar.gz", "44836872d9aec49f1e6b52a9a922872db9a2b02d235a616a5681b6a85fec8d89"),
}


def cache_identity(root, namespace, system=None, architecture=None, payload_profile="core"):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", namespace):
        raise ValueError("Cache namespace must be a bounded lowercase label")
    system = system or sys.platform
    architecture = (architecture or platform.machine()).lower()
    if system not in ARCHIVES or architecture not in {"amd64", "x86_64"}:
        raise ValueError("Cache pilot supports Windows/Linux x64 only")
    if payload_profile not in {"core", "complete"}:
        raise ValueError("Unknown payload profile")
    inputs = sorted(set(INPUTS) | {p.name for p in root.glob("requirements-*.txt")})
    hashes = {}
    for name in inputs:
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Cache input escapes source: " + name)
        hashes[name] = bootstrap.digest(path)
    identity = {"schema_version": 1, "os": system, "architecture": "x64", "profile": payload_profile, "inputs": hashes}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {**identity, "namespace": namespace, "key": f"lotm-payload-v1-{system}-x64-{namespace}-{digest}"}


def acquire_archive(name, expected, url, offline):
    archive = bootstrap.owned_path(ROOT / ".local/ci-cache/tool-archives" / name)
    if archive.exists():
        if bootstrap.digest(archive) != expected:
            raise ValueError("Cached runtime archive digest mismatch")
        return archive
    if offline:
        raise ValueError("Runtime archive unavailable offline: " + name)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as response, archive.open("xb") as destination:
        shutil.copyfileobj(response, destination)
    if bootstrap.digest(archive) != expected:
        raise ValueError("Runtime archive digest mismatch")
    return archive


def runtime(offline=False):
    """Use exact existing PS or acquire a hash-pinned portable copy, never a machine install."""
    version = bootstrap.read_json(ROOT / "Tools/CI/Data/runtime-versions.json")["powershell"]
    if version != "7.6.6":
        raise ValueError("Review portable release hashes when changing the adopted PS runtime")
    host = shutil.which("pwsh")
    command = ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]
    if host and bootstrap.run([host, *command], timeout=30).strip() == version:
        return str(Path(host).resolve())
    name, expected = ARCHIVES[sys.platform]
    owner = bootstrap.owned_path(ROOT / ".local/ci-tools/powershell-7.6.6")
    if owner.exists():
        raise ValueError("Existing portable runtime owner requires inspection; no implicit replacement")
    archive = acquire_archive(
        name, expected, f"https://github.com/PowerShell/PowerShell/releases/download/v{version}/{name}", offline
    )
    owner.mkdir(parents=True)
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


def node_runtime(offline):
    versions = bootstrap.read_json(ROOT / "Tools/CI/Data/runtime-versions.json")
    if (versions["node"], versions["npm"]) != ("24.15.0", "11.12.1"):
        raise ValueError("Review Node archive pins when changing adopted Node/npm")
    # Always materialize the verified archive; warmed payloads remain usable when agent Node changes.
    name, expected = NODE_ARCHIVES[sys.platform]
    archive = acquire_archive(name, expected, "https://nodejs.org/dist/v24.15.0/" + name, offline)
    owner = bootstrap.owned_path(ROOT / ".local/ci-tools/node-24.15.0")
    package = owner / name.removesuffix(".tar.gz").removesuffix(".zip")
    receipt = owner / "content-sha256.json"
    if owner.exists():
        if not receipt.is_file() or bootstrap.read_json(receipt) != {
            "archive_sha256": expected,
            "files": bootstrap.tree_manifest(package),
        }:
            raise ValueError("Existing owned Node provenance/content differs; no implicit repair")
    else:
        owner.mkdir(parents=True)
        if sys.platform == "win32":
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(owner)
        else:
            with tarfile.open(archive) as bundle:
                bundle.extractall(owner, filter="data")
        receipt.write_text(
            json.dumps({"archive_sha256": expected, "files": bootstrap.tree_manifest(package)}), encoding="utf-8"
        )
    directory = package if sys.platform == "win32" else package / "bin"
    return str(directory)


def inject_fault(fault):
    """Mutate only a restored ephemeral hosted payload; never repair or upload it."""
    if fault == "none":
        return
    if fault not in {"wheel", "module-receipt"}:
        raise ValueError("Unknown cache fault")
    if os.environ.get("LOTM_CI_CACHE_PILOT") != "hosted":
        raise ValueError("Fault controls require the explicitly marked ephemeral hosted pilot")
    versions = bootstrap.read_json(ROOT / "Tools/CI/Data/runtime-versions.json")
    if fault == "wheel":
        _, identity, lock = bootstrap.python_plan("development", True, versions)
        row = bootstrap.wheel_for(lock["packages"]["pyyaml"])
        target = ROOT / ".local/ci-cache/python" / bootstrap.key_for(identity) / row["filename"]
    else:
        inputs = {name: bootstrap.digest(ROOT / name) for name in versions["powershell_declarations"].values()}
        key = bootstrap.key_for({"schema": 1, "os": sys.platform, "architecture": platform.machine(), "inputs": inputs})
        target = ROOT / ".local/ci-cache/powershell" / key / "content-sha256.json"
    target = bootstrap.owned_path(target)
    if not target.is_file():
        raise ValueError("Fault target missing from restored payload")
    if fault == "wheel":
        target.write_bytes(b"deliberately corrupt hosted cache fixture")
    else:
        target.unlink()


def qualify_render(out):
    """Real CLI smoke and agent prerequisites, using only the verified render environment."""
    report = bootstrap.read_json(out / "render.json")
    if report["status"] != "passed":
        raise ValueError("Verified render bootstrap required before CLI qualification")
    render = report["render"]
    evidence = {"node": render["node"], "browser": render["browser"], "platform": sys.platform}
    if sys.platform == "linux":
        libraries = bootstrap.run(["ldd", render["path"]], timeout=30)
        if "not found" in libraries:
            raise ValueError("Chrome agent shared libraries missing:\n" + libraries)
        font = bootstrap.run(["fc-match", "Arial"], timeout=30).strip()
        if "Liberation Sans" not in font and "Arial" not in font:
            raise ValueError("Expected Arial-compatible agent font unavailable: " + font)
        evidence.update(libraries=libraries, font=font)
    else:
        font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arial.ttf"
        if not font.is_file():
            raise ValueError("Expected Windows Arial font unavailable")
        evidence["font"] = str(font)
    source = out / "render-smoke.mmd"
    svg = out / "render-smoke.svg"
    source.write_text('flowchart LR\n  A["Pinned source"] --> B["Cache verified"]\n', encoding="utf-8")
    config = out / "render-config.json"
    config.write_text(
        json.dumps({"executablePath": render["path"], "args": ["--no-sandbox"] if sys.platform == "linux" else []}),
        encoding="utf-8",
    )
    environment = bootstrap.clean_environment()
    environment["PATH"] = str(Path(render["node"]).parent) + os.pathsep + environment["PATH"]
    bootstrap.run(
        [render["mmdc"], "-i", source, "-o", svg, "-p", config, "--quiet"], environment=environment, timeout=60
    )
    text = svg.read_text(encoding="utf-8")
    if len(text) > 200000 or any(label not in text for label in ("Pinned source", "Cache verified")):
        raise ValueError("Rendered synthetic labels absent or output exceeds smoke allowance")
    document = ET.fromstring(text)
    geometry = document.attrib.get("viewBox", "").split()
    if len(geometry) != 4 or any(not math.isfinite(float(value)) or float(value) <= 0 for value in geometry[2:]):
        raise ValueError("Rendered synthetic diagram geometry invalid")
    evidence.update(
        svg_sha256=bootstrap.digest(svg),
        source_sha256=bootstrap.digest(source),
        view_box=geometry,
        labels_verified=True,
    )
    (out / "render-qualification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "bootstrap"))
    parser.add_argument("--namespace", default="pilot-1")
    parser.add_argument("--host", choices=("local", "github", "ado"), default="local")
    parser.add_argument("--cache-hit", choices=("true", "false"), default="false")
    parser.add_argument("--expect", choices=("auto", "hit", "miss"), default="auto")
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--payload-profile", choices=("core", "complete"), default="core")
    parser.add_argument("--fault", choices=("none", "wheel", "module-receipt"), default="none")
    parser.add_argument("--environment-id", default="host-pilot-fresh")
    parser.add_argument("--source-modified", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
        parser.error("Full source revision required")
    out = (ROOT / ".tmp/ci-cache-pilot").resolve()
    if not out.is_relative_to(ROOT.resolve()):
        raise ValueError("Pilot report destination escapes repository")
    out.mkdir(parents=True, exist_ok=True)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.environment_id):
        parser.error("Bounded environment ID required")
    identity = cache_identity(ROOT, args.namespace, payload_profile=args.payload_profile)
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
    if args.fault != "none" and (args.host == "local" or not hit):
        raise ValueError("Fault experiment requires an actual restored hosted cache hit")
    if list((ROOT / ".local/ci-environments/python").glob("*/" + args.environment_id)):
        raise ValueError("Pilot requires a fresh environment; existing pilot owner is not reused or removed")
    started = time.perf_counter()
    deadline = time.monotonic() + 900
    os.environ["LOTM_CI_UNIT_DEADLINE"] = str(min(float(os.environ.get("LOTM_CI_UNIT_DEADLINE", deadline)), deadline))
    pwsh = runtime(hit)
    inject_fault(args.fault)
    base = [
        sys.executable,
        str(ROOT / "Tools/CI/bootstrap.py"),
        "--environment-id",
        args.environment_id,
        "--source-revision",
        args.source_revision,
    ]
    if hit:
        base.append("--offline")
    if args.source_modified:
        base.append("--source-modified")
    commands = [
        (
            "bootstrap",
            [
                "--media",
                "--powershell-profile",
                "development",
                "--pwsh",
                pwsh,
            ],
        )
    ]
    if args.payload_profile == "complete":
        node_started = time.perf_counter()
        directory = node_runtime(hit)
        os.environ["PATH"] = directory + os.pathsep + os.environ["PATH"]
        (out / "node.json").write_text(
            json.dumps({"directory": directory, "seconds": time.perf_counter() - node_started}), encoding="utf-8"
        )
        commands.extend(
            [
                ("build", ["--package-mode", "wheel", "--build-only"]),
                ("render", ["--python-profile", "none", "--render"]),
            ]
        )
    steps = []
    for name, arguments in commands:
        step_start = time.perf_counter()
        timeout = min(720, float(os.environ["LOTM_CI_UNIT_DEADLINE"]) - time.monotonic() - 2)
        if timeout <= 0:
            raise ValueError("Pilot whole-setup deadline exhausted")
        try:
            result = subprocess.run(
                base + arguments + ["--report", str(out / (name + ".json"))],
                cwd=ROOT,
                env=bootstrap.clean_environment(),
                timeout=timeout,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as error:
            diagnostic = ""
            for output in (error.stdout, error.stderr):
                diagnostic += output.decode("utf-8", errors="replace") if isinstance(output, bytes) else output or ""
            (out / (name + ".log")).write_text(diagnostic, encoding="utf-8")
            raise
        (out / (name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        print(result.stdout + result.stderr, flush=True)
        steps.append({"id": name, "exit_code": result.returncode, "seconds": time.perf_counter() - step_start})
    exit_code = 1 if any(step["exit_code"] for step in steps) else 0
    if args.payload_profile == "complete" and next(step for step in steps if step["id"] == "render")["exit_code"] == 0:
        step_start = time.perf_counter()
        try:
            qualify_render(out)
            steps.append({"id": "render-smoke", "exit_code": 0, "seconds": time.perf_counter() - step_start})
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            (out / "render-qualification-failure.json").write_text(json.dumps({"error": str(error)}), encoding="utf-8")
            steps.append({"id": "render-smoke", "exit_code": 1, "seconds": time.perf_counter() - step_start})
            print(str(error), file=sys.stderr)
            exit_code = 1
    evidence = {
        "schema_version": 1,
        "host": args.host,
        "source_revision": args.source_revision,
        "key": identity["key"],
        "host_cache_hit": hit,
        "expected": args.expect,
        "exit_code": exit_code,
        "steps": steps,
        "payload_profile": args.payload_profile,
        "fault": args.fault,
        "setup_seconds": time.perf_counter() - started,
        "transport_timing": "Read restore/save task durations from the hosted run; excluded here",
        "scope": "Repository bootstrap payloads; profiles/testing authority unchanged",
    }
    (out / "pilot.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return exit_code


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
