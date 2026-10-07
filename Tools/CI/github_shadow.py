"""Thin GitHub shadow transport over authoritative local profiles and shard collection."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bootstrap
import host_cache
from catalog import Catalog
from execution_reports import verify_publication, confined
from scope import Git, resolve_scope

ROOT = Path(__file__).resolve().parents[2]
TARGET = "architecture/framework-extraction-foundation"
PROFILES = {"pr-integration", "full-verification", "ci-infrastructure"}
ACTIONLINT = {
    "win32": (
        "actionlint_1.7.12_windows_amd64.zip",
        "6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9",
    ),
    "linux": (
        "actionlint_1.7.12_linux_amd64.tar.gz",
        "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8",
    ),
}


def oid(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Exact 40-character execution identity required")
    return value


def event_context(event, environment, pull=None):
    """Normalize bounded event metadata; no suite/path selection or moving-ref inference."""
    name = environment["GITHUB_EVENT_NAME"]
    repository = environment["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid repository identity")
    executed = oid(environment["GITHUB_SHA"])
    kind = "merge"
    if name == "pull_request":
        pull = event["pull_request"]
        profile = "pr-integration"
    elif name == "workflow_dispatch":
        inputs = event.get("inputs", {})
        kind = inputs.get("checkout_kind", "merge")
        profile = inputs.get("profile", "full-verification")
        if pull is not None:
            if profile != "pr-integration":
                raise ValueError("Explicit PR replay requires full pr-integration")
            executed = oid(pull["head"]["sha"] if kind == "source" else pull["merge_commit_sha"])
    else:
        raise ValueError("Only PR and explicit manual shadow events are adopted at 6.2")
    if profile not in PROFILES or kind not in {"source", "merge"}:
        raise ValueError("Unknown shadow profile or checkout kind")
    context = {
        "host": "github",
        "event": name,
        "repository": repository,
        "profile": profile,
        "executed": executed,
        "source": executed,
        "base": "unavailable-manual-base",
        "scope": "hosted-commit",
        "checkout_kind": "source",
        "pr": None,
    }
    if pull is not None:
        if pull["base"]["ref"] != TARGET or pull["base"]["repo"]["full_name"] != repository:
            raise ValueError("PR target does not match the approved framework repository/ref")
        number = pull["number"]
        if type(number) is not int or number <= 0:
            raise ValueError("Invalid PR identity")
        context.update(
            base=oid(pull["base"]["sha"]),
            source=oid(pull["head"]["sha"]),
            scope="hosted-pr",
            checkout_kind=kind,
            pr=number,
        )
        if kind == "source" and executed != context["source"]:
            raise ValueError("Source replay must execute the exact PR head")
    context["run_url"] = "https://github.com/" + repository + "/actions/runs/" + str(int(environment["GITHUB_RUN_ID"]))
    context["attempt"] = int(environment["GITHUB_RUN_ATTEMPT"])
    return context


def validate_context(root, context):
    git = Git(root)
    if git.resolve("HEAD") != oid(context["executed"]):
        raise ValueError("Actual checkout differs from the event execution identity")
    if context["scope"] == "hosted-pr" and context["checkout_kind"] == "merge":
        parents = git.read("show", "-s", "--format=%P", context["executed"]).decode().strip().split()
        if len(parents) != 2 or set(parents) != {context["base"], context["source"]}:
            raise ValueError("PR execution cannot be proven against exact target/source parents")
    return resolve_scope(root, context["scope"], context["base"], context["source"], context["executed"])[0]


def matrices(root, context):
    catalog = Catalog(root)
    plans = [row for row in catalog.shard_plans.values() if row["profile"] == context["profile"]]
    if len(plans) != 1:
        raise ValueError("Exactly one approved shard plan required")
    plan = plans[0]
    shards = {row["id"]: row for row in plan["shards"]}
    independent, dependent = [], []
    for row in plan["shards"]:
        if any(shards[name]["depends_on"] for name in row["depends_on"]):
            raise ValueError("Shadow transport supports one dependency wave; deeper plans need reviewed orchestration")
        minutes = math.ceil((row["budget"]["total_seconds"] + 600 + 180 + 120) / 60)
        if minutes > 55 or row["os"] not in {"windows", "linux"}:
            raise ValueError("Shard cannot be admitted on approved hosted capacity")
        entry = {
            "shard": row["id"],
            "os": "windows-2022" if row["os"] == "windows" else "ubuntu-24.04",
            "timeout": minutes,
        }
        (dependent if row["depends_on"] else independent).append(entry)
    return plan, {"include": independent}, {"include": dependent}


def output(**values):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
        for name, value in values.items():
            text = json.dumps(value, separators=(",", ":")) if not isinstance(value, str) else value
            if "\n" in text or "\r" in text:
                raise ValueError("Multiline transport output rejected")
            stream.write(name + "=" + text + "\n")


def actionlint(offline):
    if bootstrap.read_json(ROOT / "Tools/CI/Data/runtime-versions.json")["actionlint"] != "1.7.12":
        raise ValueError("Review actionlint archive hashes when changing the adopted version")
    name, digest = ACTIONLINT[sys.platform]
    archive = host_cache.acquire_archive(
        name, digest, "https://github.com/rhysd/actionlint/releases/download/v1.7.12/" + name, offline
    )
    owner = bootstrap.owned_path(ROOT / ".local/ci-tools/actionlint-1.7.12")
    if owner.exists():
        raise ValueError("Fresh hosted actionlint owner required")
    owner.mkdir(parents=True)
    executable = owner / ("actionlint.exe" if os.name == "nt" else "actionlint")
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as package:
            executable.write_bytes(package.read(executable.name))
    else:
        with tarfile.open(archive) as package:
            member = package.extractfile("actionlint")
            if member is None:
                raise ValueError("Pinned actionlint archive lacks executable")
            executable.write_bytes(member.read())
        executable.chmod(0o755)
    if bootstrap.run([executable, "--version"]).splitlines()[0] != "1.7.12":
        raise ValueError("Pinned actionlint version differs")
    return str(executable)


def bundles(root):
    root = Path(root)
    if not root.exists():
        return []
    if root.is_symlink() or root.is_junction() or not root.resolve().is_relative_to(ROOT / ".tmp"):
        raise ValueError("Downloaded evidence must be confined to repository .tmp")
    return sorted(root.rglob("shard-result.json"))


def export_bundle(owner, destination):
    manifest = verify_publication(owner)
    destination = destination / owner.name
    destination.mkdir(parents=True, exist_ok=False)
    for name in [*(row["path"] for row in manifest["files"]), "publication-manifest.json", "finalized.json"]:
        source = confined(owner, name)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    verify_publication(destination)


def execute(context, shard, inputs):
    import run_ci

    validate_context(ROOT, context)
    plan, _, _ = matrices(ROOT, context)
    available = bundles(inputs)
    if shard:
        row = next(row for row in plan["shards"] if row["id"] == shard)
        dependency_ids = set(row["depends_on"])
        selected = [path for path in available if bootstrap.read_json(path)["source"]["shard"] in dependency_ids]
        if {bootstrap.read_json(path)["source"]["shard"] for path in selected} != dependency_ids:
            raise ValueError("Missing prerequisite shard evidence")
    else:
        selected = available
        expected = {row["id"] for row in plan["shards"]}
        identities = [bootstrap.read_json(path)["source"]["shard"] for path in selected]
        if len(identities) != len(expected) or set(identities) != expected:
            raise ValueError("Collection requires every approved shard exactly once; no sequential fallback")
    setup = bootstrap.read_json(ROOT / ".tmp/ci-cache-pilot/bootstrap.json")
    build = bootstrap.read_json(ROOT / ".tmp/ci-cache-pilot/build.json")
    if setup["status"] != "passed" or build["status"] != "passed":
        raise ValueError("Verified dependency/build setup required")
    # Paths are taken from authoritative bootstrap receipts, never from workflow guesses.
    modules = setup["powershell"]["module_path"].split(os.pathsep)[0]
    lock = bootstrap.read_json(ROOT / "Tools/CI/Data/python-wheel-lock.json")
    payload = bootstrap.wheel_for(lock["packages"]["pyyaml"])
    runtime_wheel = ROOT / ".local/ci-cache/python" / setup["python"]["key"] / payload["filename"]
    if bootstrap.digest(runtime_wheel) != payload["sha256"]:
        raise ValueError("Explicit runtime wheel differs from captured lock")
    args = argparse.Namespace(
        root=str(ROOT),
        profile=context["profile"],
        scope=context["scope"],
        base=context["base"],
        source=context["source"],
        executed=context["executed"],
        python=setup["python"]["executable"],
        pwsh=setup["powershell"]["executable"],
        module_root=modules,
        actionlint=bootstrap.read_json(ROOT / ".tmp/ci-shadow/tools.json")["actionlint"],
        wheel=build["package"]["wheel"],
        runtime_wheel=str(runtime_wheel),
        render_bootstrap_report=str(ROOT / ".tmp/ci-cache-pilot/render.json"),
        shard_plan=plan["id"],
        shard=shard,
        source_results=list(map(str, selected)) if shard else [],
        shard_results=list(map(str, selected)) if not shard else [],
        output_root=".tmp/ci-shadow/execution",
        host_kind=context.get("host", "github"),
        run_url=context["run_url"],
    )
    report, path = run_ci.execute(args)
    if path is None:
        raise ValueError("Execution did not produce a report")
    owner = path.parent
    export_bundle(owner, ROOT / ".tmp/ci-shadow/bundle")
    print(
        f"{context.get('host', 'github')} shadow {report['status']}: "
        f"{report['counts']['selected']} selected; report {path}",
        flush=True,
    )
    for failure in report["failures"]:
        print(f"{failure['id']}: {failure['excerpt']}", flush=True)
    return report["exit_code"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("context", "plan-bootstrap", "plan", "prepare", "bootstrap", "execute", "collect")
    )
    parser.add_argument("--shard")
    parser.add_argument("--inputs", default=".tmp/ci-shadow/downloads")
    args = parser.parse_args()
    out = confined(ROOT, ".tmp/ci-shadow")
    out.mkdir(parents=True, exist_ok=True)
    if args.operation == "context":
        event = bootstrap.read_json(os.environ["GITHUB_EVENT_PATH"])
        number = event.get("inputs", {}).get("pr_number", "")
        pull = None
        if number:
            if not re.fullmatch(r"[1-9][0-9]{0,8}", number):
                raise ValueError("Bounded numeric PR identity required")
            repository = os.environ["GITHUB_REPOSITORY"]
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
                raise ValueError("Invalid repository identity")
            request = urllib.request.Request(
                f"https://api.github.com/repos/{repository}/pulls/{number}",
                headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                pull = json.load(response)
            if pull["state"] != "open":
                raise ValueError("PR replay requires an open PR")
        context = event_context(event, os.environ, pull)
        output(context=context, checkout=context["executed"])
        return 0
    context = json.loads(os.environ["SHADOW_CONTEXT"])
    if args.operation == "plan-bootstrap":
        validate_context(ROOT, context)
        deadline = time.monotonic() + 150
        environment = {**os.environ, "LOTM_CI_UNIT_DEADLINE": str(deadline)}
        report_path = out / "planning-bootstrap.json"
        command = [
            sys.executable,
            str(ROOT / "Tools/CI/bootstrap.py"),
            "--python-profile",
            "runtime",
            "--environment-id",
            context["host"] + "-shadow-plan",
            "--source-revision",
            context["executed"],
            "--report",
            str(report_path),
        ]
        child = subprocess.run(command, cwd=ROOT, env=environment, timeout=150, check=False)
        if child.returncode:
            return child.returncode
        setup = bootstrap.read_json(report_path)
        if setup["status"] != "passed":
            raise ValueError("Planning runtime bootstrap did not pass")
        output(python=setup["python"]["executable"])
        return 0
    if args.operation == "plan":
        scope = validate_context(ROOT, context)
        plan, independent, dependent = matrices(ROOT, context)
        (out / "plan.json").write_text(json.dumps({"context": context, "scope": scope, "shard_plan": plan}, indent=2))
        output(independent=independent, dependent=dependent, dependent_count=str(len(dependent["include"])))
        return 0
    if args.operation == "prepare":
        validate_context(ROOT, context)
        identity = host_cache.cache_identity(ROOT, context["host"] + "-shadow-1", payload_profile="complete")
        (out / "context.json").write_text(json.dumps(context, indent=2))
        output(key=identity["key"])
        return 0
    if args.operation == "bootstrap":
        hit = os.environ.get("CACHE_HIT") == "true"
        deadline = time.monotonic() + 600
        os.environ["LOTM_CI_UNIT_DEADLINE"] = str(deadline)
        tool = actionlint(hit)
        environment = {**os.environ, "LOTM_CI_UNIT_DEADLINE": str(deadline)}
        # The complete payload remains the measured immutable transport unit during shadow rollout.
        command = [
            sys.executable,
            "Tools/CI/host_cache.py",
            "bootstrap",
            "--host",
            context["host"],
            "--namespace",
            context["host"] + "-shadow-1",
            "--source-revision",
            context["executed"],
            "--cache-hit",
            "true" if hit else "false",
            "--payload-profile",
            "complete",
        ]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Preparation deadline exhausted during tool acquisition")
        child = subprocess.run(command, cwd=ROOT, env=environment, timeout=remaining, check=False)
        if child.returncode:
            return child.returncode
        (out / "tools.json").write_text(json.dumps({"actionlint": tool, "setup_deadline_seconds": 600}, indent=2))
        setup = bootstrap.read_json(ROOT / ".tmp/ci-cache-pilot/bootstrap.json")
        output(python=setup["python"]["executable"])
        return 0
    return execute(context, args.shard if args.operation == "execute" else None, ROOT / args.inputs)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, StopIteration) as error:
        out = ROOT / ".tmp/ci-shadow"
        out.mkdir(parents=True, exist_ok=True)
        (out / "failure.json").write_text(json.dumps({"status": "failed", "error": str(error)}, indent=2))
        print("GitHub shadow failed: " + str(error), file=sys.stderr)
        raise SystemExit(1) from error
