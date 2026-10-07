"""Experimental Azure placement executor; logical shard contracts remain authoritative."""

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import threading
import time

import ado_shadow
import github_shadow as transport
from execution_reports import atomic_bytes, confined, decode_json, encoded, verify_publication
from process_supervisor import Lease, run_process
from publish_hosted import admit


def admitted_cohort(root, context, identity):
    if context.get("host") != "ado" or context.get("profile") not in transport.PROFILES:
        raise ValueError("Cohort requires an approved Azure profile")
    transport.validate_context(root, context)
    proposal = ado_shadow.cohort_plan(root, context["profile"])
    rows = [row for row in proposal["cohorts"] if row["id"] == identity]
    if len(rows) != 1 or rows[0]["os"] != platform.system().lower():
        raise ValueError("Unknown cohort or incompatible execution OS")
    plan, _, _ = transport.matrices(root, context)
    if context.get("preparation_roles") != transport.preparation_roles(root, plan):
        raise ValueError("Cohort requires the exact catalog preparation map")
    return rows[0], plan


def child_command(args):
    command = [args.python, str(Path(args.root) / "Tools/CI/run_ci.py"), "--summary-json"]
    for key, value in vars(args).items():
        if value is None:
            continue
        if isinstance(value, list):
            flag = {"source_results": "--source-result", "shard_results": "--shard-result"}[key]
            for item in value:
                command.extend([flag, str(item)])
        else:
            command.extend(["--" + key.replace("_", "-"), str(value)])
    return command


def child_environment():
    """Match adapter isolation: host tokens and arbitrary project environment do not reach children."""
    names = ("SystemRoot", "SystemDrive", "ProgramData", "WINDIR", "TEMP", "TMP", "HOME", "LANG", "PATH", "PATHEXT")
    environment = {name: os.environ[name] for name in names if name in os.environ}
    environment.update(
        PYTHONUTF8="1",
        PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PIP_NO_INDEX="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
    )
    return environment


def stage_shard(root, context, cohort, shard, worker, stage, process):
    """Only one finalized original bundle enters transport; never upload captured source trees."""
    runs = list(confined(root, worker + "/execution").glob("run-*"))
    if len(runs) != 1:
        raise ValueError("Cohort child produced missing or ambiguous run evidence")
    owner = runs[0]
    manifest = verify_publication(owner)
    envelope = decode_json(confined(owner, "shard-result.json").read_text(encoding="utf-8"))
    report = decode_json(confined(owner, "report.json").read_text(encoding="utf-8"))
    if (
        envelope["source"]["shard"] != shard
        or envelope["source"]["shard_plan"] != cohort["shard_plan"]
        or envelope["report"] != report
        or report["provenance"].get("executed_commit") != context["executed"]
        or report["profile"] != context["profile"]
        or process["status"] != "exited"
        or process["child_exit_code"] != manifest["execution_exit_code"]
        or not process["cleanup"]["verified"]
    ):
        raise ValueError("Cohort child process and finalized shard evidence disagree")
    transport.export_bundle(owner, confined(root, worker + "/bundle"))
    destination, receipt = admit(
        root, context, shard, worker_owner=worker, artifact_override="ci-shadow-" + cohort["id"]
    )
    atomic_bytes(destination, "receipt.json", encoded(receipt))
    if receipt["status"] != "admitted":
        raise ValueError("Cohort shard publication admission failed: " + receipt.get("error", "unknown"))
    if manifest["execution_exit_code"] != report["exit_code"]:
        raise ValueError("Cohort child exit differs from its finalized manifest")
    # The stage contains no second copy of shard-result.json under captured execution/source paths.
    target = stage / shard
    target.mkdir()
    transport.export_bundle(owner, target / "bundle")
    shutil.copytree(destination, target / "publication")
    return {"run_id": report["run_id"], "status": report["status"], "exit_code": report["exit_code"]}


def run_cohort(root, context, identity, inputs, *, cancel=None):
    root = Path(root).absolute()
    if root != transport.ROOT:
        raise ValueError("Cohort execution requires the configured repository owner")
    cohort, plan = admitted_cohort(root, context, identity)
    cohort = {**cohort, "shard_plan": plan["id"]}
    prefix = ".tmp/ci-shadow/cohorts/" + cohort["id"]
    owner = confined(root, prefix)
    owner.mkdir(parents=True, exist_ok=False)
    stage = owner / "transport"
    stage.mkdir()
    processes = owner / "processes"
    processes.mkdir()
    cancellation = cancel if cancel is not None else threading.Event()
    handlers = {}
    if threading.current_thread() is threading.main_thread():
        for name in (signal.SIGINT, signal.SIGTERM):
            handlers[name] = signal.signal(name, lambda *_: cancellation.set())
    started = time.monotonic()
    deadline = started + cohort["declared_shard_seconds"] + cohort["preserved_child_setup_seconds"] + 120
    result = {
        "contract": "ci-ado-cohort-experiment",
        "contract_version": 1,
        "adopted": False,
        "cohort": cohort,
        "executed_commit": context["executed"],
        "profile": context["profile"],
        "shards": [],
    }
    budgets = {row["id"]: row["budget"]["total_seconds"] for row in plan["shards"]}
    try:
        for shard in cohort["shards"]:
            row = {"shard": shard, "status": "error", "exit_code": 1}
            worker = prefix + "/shards/" + shard
            try:
                if cancellation.is_set():
                    row.update(status="cancelled", exit_code=130)
                elif time.monotonic() + budgets[shard] + 600 + 30 > deadline:
                    row.update(status="blocked", reason="Cohort cannot admit the complete original shard allowance")
                else:
                    args = transport.execution_arguments(
                        context, shard, inputs, preparation=cohort["preparation"], output_root=worker + "/execution"
                    )
                    child_deadline = time.monotonic() + budgets[shard] + 600 + 30
                    if child_deadline > deadline:
                        row["status"] = "blocked"
                        raise ValueError("Cohort preflight consumed the remaining complete child allowance")
                    environment = child_environment()
                    process = run_process(
                        child_command(args),
                        cwd=root,
                        env=environment,
                        output_parent=processes,
                        lease=Lease(child_deadline),
                        cancel=cancellation,
                    )
                    row["process"] = process
                    if process["status"] != "exited":
                        row["status"] = process["status"]
                    # Retain complete bounded supervisor capture independently of result admission.
                    atomic_bytes(stage, "process-" + shard + ".json", encoded(process))
                    capture = confined(processes, Path(process["directory"]).relative_to(processes).as_posix())
                    captures = stage / "processes" / shard
                    captures.mkdir(parents=True)
                    for name in ("stdout.bin", "stderr.bin", "guardian.bin", "process.json", "ownership.json"):
                        source = confined(capture, name)
                        if source.is_file():
                            shutil.copy2(source, captures / name)
                    row.update(stage_shard(root, context, cohort, shard, worker, stage, process))
            except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
                row["reason"] = str(error)
                if cancellation.is_set():
                    row.update(status="cancelled", exit_code=130)
            result["shards"].append(row)
            atomic_bytes(owner, "cohort-progress.json", encoded(result), replace=True)
    finally:
        for name, handler in handlers.items():
            signal.signal(name, handler)
    result["elapsed_seconds"] = time.monotonic() - started
    result["exit_code"] = 130 if cancellation.is_set() else int(any(row["exit_code"] for row in result["shards"]))
    result["status"] = "cancelled" if cancellation.is_set() else "failed" if result["exit_code"] else "passed"
    atomic_bytes(owner, "cohort-result.json", encoded(result))
    atomic_bytes(stage, "cohort-result.json", encoded(result))
    return result, stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--inputs", default=".tmp/ci-shadow/downloads")
    args = parser.parse_args()
    context = json.loads(os.environ["SHADOW_CONTEXT"])
    if context.get("host") != "ado":
        raise ValueError("Experimental cohort CLI requires Azure context")
    result, stage = run_cohort(transport.ROOT, context, args.cohort, args.inputs)
    print(json.dumps({"status": result["status"], "shards": len(result["shards"]), "transport": str(stage)}))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
