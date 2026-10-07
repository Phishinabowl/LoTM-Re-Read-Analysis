"""Experimental Azure placement executor; logical shard contracts remain authoritative."""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import sys
import threading
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ado_shadow
import github_shadow as transport
from execution_reports import atomic_bytes, confined, decode_json, encoded, verify_publication
from process_supervisor import Lease, run_process
from publish_hosted import admit, hosted_markdown, readable_report, native_failures, submit


def admitted_cohort(root, context, identity):
    if context.get("host") != "ado" or context.get("profile") not in transport.PROFILES:
        raise ValueError("Cohort requires an approved Azure profile")
    transport.validate_context(root, context)
    proposal = ado_shadow.cohort_plan(root, context["profile"])
    if context.get("placement"):
        allowed = ado_shadow.validate_placement(root, context)
        if identity not in {row["id"] for row in allowed}:
            raise ValueError("Cohort is outside the captured manual experiment")
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


def validate_result(root, context, stage, result, expected):
    plan, _, _ = transport.matrices(root, context)
    if (
        result.get("contract") != "ci-ado-cohort-experiment"
        or result.get("contract_version") != 1
        or result.get("adopted") is not False
        or result.get("executed_commit") != context["executed"]
        or result.get("profile") != context["profile"]
        or result.get("cohort") != {**expected, "shard_plan": plan["id"]}
        or [row["shard"] for row in result["shards"]] != expected["shards"]
    ):
        raise ValueError("Cohort receipt differs from captured source and logical inventory")
    owners = []
    for row in result["shards"]:
        owner = confined(stage, row["shard"] + "/bundle/" + row["run_id"])
        manifest = verify_publication(owner)
        report = decode_json(confined(owner, "report.json").read_text(encoding="utf-8"))
        source = decode_json(confined(owner, "shard-result.json").read_text(encoding="utf-8"))["source"]
        process = row["process"]
        if (
            source["shard"] != row["shard"]
            or source["shard_plan"] != plan["id"]
            or report["profile"] != context["profile"]
            or report["provenance"].get("executed_commit") != context["executed"]
            or report["run_id"] != row["run_id"]
            or report["status"] != row["status"]
            or manifest["execution_exit_code"] != row["exit_code"]
            or process["status"] != "exited"
            or process["child_exit_code"] != row["exit_code"]
            or process["cleanup"]["verified"] is not True
        ):
            raise ValueError("Cohort receipt disagrees with original shard evidence")
        owners.append(owner)
    exit_code = int(any(row["exit_code"] for row in result["shards"]))
    if result.get("exit_code") != exit_code or result.get("status") != ("failed" if exit_code else "passed"):
        raise ValueError("Cohort aggregate exit or lifecycle status is inconsistent")
    if set(stage.rglob("shard-result.json")) != {owner / "shard-result.json" for owner in owners}:
        raise ValueError("Cohort transport contains duplicate or unregistered shard evidence")
    return owners


def validate_collection(root, context, inputs):
    if context.get("placement") == "cohort-smoke":
        raise ValueError("Partial cohort smoke cannot satisfy full-profile collection")
    rows = ado_shadow.validate_placement(root, context)
    inputs = confined(root, Path(inputs).absolute().relative_to(Path(root).absolute()).as_posix())
    receipts = list(inputs.rglob("cohort-result.json")) if inputs.exists() else []
    expected = {row["id"]: row for row in rows}
    seen, owners = set(), []
    for path in receipts:
        result = decode_json(path.read_text(encoding="utf-8"))
        identity = result["cohort"]["id"]
        if identity not in expected or identity in seen:
            raise ValueError("Duplicate or foreign cohort receipt")
        seen.add(identity)
        owners.extend(validate_result(root, context, path.parent, result, expected[identity]))
    if seen != set(expected) or set(inputs.rglob("shard-result.json")) != {
        owner / "shard-result.json" for owner in owners
    }:
        raise ValueError("Cohort collection requires every original cohort and logical shard exactly once")
    return owners


def diagnostics(root, context, identity):
    if not re.fullmatch(r"cohort-[0-9]{1,3}", identity):
        raise ValueError("Invalid cohort diagnostic owner")
    stage = confined(root, ".tmp/ci-shadow/cohorts/" + identity + "/transport")
    stage.mkdir(parents=True, exist_ok=True)
    atomic_bytes(stage, "context.json", encoded(context))
    for name in ("tools.json", "failure.json"):
        source = confined(root, ".tmp/ci-shadow/" + name)
        if source.is_file():
            shutil.copy2(source, stage / name)
    source = confined(root, ".tmp/ci-cache-pilot")
    if source.is_dir():
        shutil.copytree(source, stage / "setup")
    return stage


def publish_summary(root, context, identity):
    rows = ado_shadow.validate_placement(root, context)
    expected = next(row for row in rows if row["id"] == identity)
    stage = confined(root, ".tmp/ci-shadow/cohorts/" + identity + "/transport")
    result = decode_json(confined(stage, "cohort-result.json").read_text(encoding="utf-8"))
    error = None
    try:
        validate_result(root, context, stage, result, expected)
    except (OSError, ValueError, KeyError, TypeError) as exception:
        error = str(exception)
    text = "# CI cohort qualification: " + ("failed" if error else result["status"]) + "\n\n"
    text += "**Partial qualification only. This does not satisfy full-profile coverage.**\n\n"
    text += "Shared preparation; original shards remain independently executed and reported.\n\n"
    if error:
        from execution_reports import markdown_text

        text += "Admission diagnostic: " + markdown_text(error) + "\n\n"
    plan, _, _ = transport.matrices(root, context)
    titles = {row["shard"]: row["title"] for row in transport.shard_presentation(plan)}
    for number, shard in enumerate(expected["shards"], 1):
        text += f"## {number:02d}. {titles[shard]}\n\n"
        owners = list((stage / shard / "bundle").glob("run-*"))
        if len(owners) == 1:
            manifest = verify_publication(owners[0])
            report = decode_json((owners[0] / "report.json").read_text(encoding="utf-8"))
            if (
                report["provenance"].get("executed_commit") != context["executed"]
                or report["profile"] != context["profile"]
            ):
                raise ValueError("Foreign shard cannot be rendered in cohort qualification")
            text += readable_report(report) + native_failures(owners[0], manifest)
        else:
            text += "Finalized shard evidence unavailable; no passing coverage is inferred.\n\n"
    atomic_bytes(stage, "summary.md", hosted_markdown(text, context["run_url"], "ci-shadow-" + identity))
    receipt = {"host": "ado", "summary_label": "cohort-qualification", "markdown_submission": "not-submitted"}
    if context["placement"] == "cohort-smoke":
        submit(stage, receipt, os.environ)
    atomic_bytes(stage, "summary-receipt.json", encoded(receipt))
    return int(error is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--inputs", default=".tmp/ci-shadow/downloads")
    parser.add_argument("--diagnostics", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    context = json.loads(os.environ["SHADOW_CONTEXT"])
    if context.get("host") != "ado":
        raise ValueError("Experimental cohort CLI requires Azure context")
    if args.diagnostics:
        diagnostics(transport.ROOT, context, args.cohort)
        return 0
    if args.publish:
        return publish_summary(transport.ROOT, context, args.cohort)
    result, stage = run_cohort(transport.ROOT, context, args.cohort, args.inputs)
    print(json.dumps({"status": result["status"], "shards": len(result["shards"]), "transport": str(stage)}))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
