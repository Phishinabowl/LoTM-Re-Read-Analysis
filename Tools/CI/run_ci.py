"""Repository-owned full local execution and shard collection; affected execution remains disabled."""

import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import stat
import signal
import sys
import tempfile
import threading
import time
import uuid

sys.dont_write_bytecode = True

from aggregate_execution import actual_dispositions, collect_shards, counts, execute_units, outcome, persist_units
from catalog import Catalog, CatalogError
from layer_adapters import AdapterSession, guarded_manifest, format_representation
from process_supervisor import RunBudget, Lease, plain_directory, run_process
from scope import MODES, ScopeError, resolve_scope
from execution_reports import Journal, atomic_bytes, encoded, finalize, summary, excerpt


def empty_report(profile, run_id):
    return {
        "contract": "ci-execution-report",
        "contract_version": 1,
        "run_id": run_id,
        "mode": "execute",
        "profile": profile,
        "status": "failed",
        "exit_code": 2,
        "complete": True,
        "provenance": {},
        "selection": {},
        "runtime_inventory": {},
        "budget": {},
        "counts": {"candidate": 0, "selected": 0, "unselected": 0, "terminal": counts([])},
        "results": [],
        "reviews": [],
        "failures": [],
        "canonical_guard": {"unchanged": None},
        "cleanup": {"verified": True, "state": "retained"},
        "artifacts": [],
    }


def remove_scratch(owner):
    """Remove only the exact created external owner; repair read-only flags only on its own files."""
    owner = Path(owner).absolute()
    if owner.resolve() != owner or owner.is_symlink() or owner.is_junction():
        raise ValueError("External scratch owner was redirected")

    def repair(function, target, error):
        path = Path(target).absolute()
        if not isinstance(error, PermissionError) or not path.resolve().is_relative_to(owner) or path.is_symlink():
            raise error
        path.chmod(path.stat().st_mode | stat.S_IWUSR)
        function(target)

    shutil.rmtree(owner, onexc=repair)
    if owner.exists():
        raise OSError("Owned external scratch remains after cleanup")


def execute(args):
    original = plain_directory(args.root)
    parent = Path(args.output_root)
    parent = (original / parent).absolute()
    if parent == original / ".tmp" or not parent.resolve().is_relative_to(original / ".tmp"):
        raise ValueError("Execution reports require a child of owned .tmp")
    for path in (parent, *parent.parents):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Run output cannot traverse a link")
    parent.mkdir(parents=True, exist_ok=True)
    owner = parent / ("run-" + uuid.uuid4().hex)
    owner.mkdir()
    report = empty_report(args.profile, owner.name)
    journal = Journal(owner, report)
    recorded_rows, recorded_artifacts = [], []
    cancel = threading.Event()
    signals = {}
    scratch = None
    started = time.monotonic()
    try:
        for name in (signal.SIGINT, signal.SIGTERM):
            signals[name] = signal.getsignal(name)
            signal.signal(name, lambda signum, frame: cancel.set())
        scope, snapshot = resolve_scope(original, args.scope, args.base, args.source, args.executed)
        workspace = snapshot.materialize(original, owner / "source")
        Lease(started + 600).verify()
        catalog = Catalog(workspace)
        plan = catalog.plan(args.profile, "windows" if os.name == "nt" else "linux", None, args.shard_plan)
        if any(
            name not in snapshot.files
            or digest != next(row["sha256"] for row in snapshot.manifest if row["path"] == name)
            for name, digest in catalog.source_digests.items()
        ):
            raise CatalogError("Catalog does not match captured execution source")
        report["provenance"] = {
            **scope["provenance"],
            "snapshot_digest": snapshot.digest,
            "catalog_digests": catalog.source_digests,
            "host_kind": "local",
            "run_url": None,
            "actual_change_scope": scope["policy_scope"],
        }
        candidates = [row["execution_id"] for row in plan["units"]]
        execution_plan = plan
        report["reviews"] = [
            {"family": row["family"], "required": True, "status": "pending", "evidence": row["evidence"]}
            for row in plan["required_reviews"]
        ]
        report["selection"] = {
            "candidate_ids": candidates,
            "selected_ids": candidates,
            "unselected": [],
            "requested_mode": "full",
            "applied_mode": "full",
        }
        if args.shard_results:
            if not args.shard_plan or args.shard:
                raise ValueError("Collection requires a shard plan and no individual shard")
            results, sources = collect_shards(
                catalog, args.shard_plan, args.shard_results, snapshot.digest, provenance=scope["provenance"]
            )
            report["results"] = results
            report["selection"] = {
                "candidate_ids": candidates,
                "selected_ids": candidates,
                "unselected": [],
                "requested_mode": "full",
                "applied_mode": "full",
                "fallback_reasons": scope["fallback_reasons"],
                "shard_sources": {key: value["report"]["run_id"] for key, value in sources.items()},
            }
            failures = [failure for value in sources.values() for failure in value["report"]["failures"]]
            report["runtime_inventory"] = {key: value["report"]["runtime_inventory"] for key, value in sources.items()}
            report["canonical_guard"] = {"unchanged": True, "changed_paths": [], "containment_verified": True}
            # Retain source bundles/artifacts beneath this aggregate owner so every reference is locally resolvable.
            for key, value in sources.items():
                source_root = Path(value["root"])
                destination = owner / "collected" / key
                destination.mkdir(parents=True)
                for entry in value["report"]["artifacts"]:
                    source = source_root / entry["path"]
                    target = destination / entry["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    report["artifacts"].append({**entry, "path": target.relative_to(owner).as_posix()})
                for row in results:
                    if row["id"] in {item["id"] for item in value["report"]["results"]}:
                        row["artifacts"] = [
                            (destination / name).relative_to(owner).as_posix() for name in row["artifacts"]
                        ]
                        for diagnostic in row["diagnostics"].values():
                            diagnostic["files"] = {
                                name: (destination / value).relative_to(owner).as_posix()
                                for name, value in diagnostic.get("files", {}).items()
                            }
            report["cleanup"] = {"verified": True, "state": "retained", "reason": "Verified collected source evidence"}
            report["budget"] = {"elapsed_seconds": time.monotonic() - started, "collection": True}
        else:
            if args.shard and not args.shard_plan:
                raise ValueError("Shard execution requires a registered shard plan")
            if args.shard_plan and not args.shard:
                raise ValueError("Choose one registered shard or collect its complete result set")
            selected = plan["units"]
            budget_record = plan["budget"]
            if args.shard:
                shards = {row["id"]: row for row in plan["shard_plan"]["shards"]}
                if args.shard not in shards:
                    raise ValueError("Unknown registered shard")
                selected = [row for row in selected if row["execution_id"] in shards[args.shard]["units"]]
                budget_record = shards[args.shard]["budget"]
            budget = RunBudget(
                budget_record["total_seconds"] + 600,
                budget_record["termination_seconds"],
                budget_record["cleanup_seconds"],
                budget_record["finalization_seconds"],
                started=started,
            )
            execution_plan = {**plan, "units": selected}
            selected_ids = [row["execution_id"] for row in selected]
            report["selection"].update(
                selected_ids=selected_ids,
                unselected=[
                    {"id": name, "reason": "Delegated to registered shard"}
                    for name in candidates
                    if name not in selected_ids
                ],
            )
            journal.event("plan", report)
            sources = {}
            if args.source_results:
                if not args.shard_plan or not args.shard:
                    raise ValueError("Prerequisite source results require an individual registered shard")
                source_rows, source_inventory = collect_shards(
                    catalog,
                    args.shard_plan,
                    args.source_results,
                    snapshot.digest,
                    partial=True,
                    provenance=scope["provenance"],
                )
                sources = {row["id"]: row for row in source_rows}
                if set(sources) & {row["execution_id"] for row in selected}:
                    raise ValueError("Prerequisite evidence duplicates this shard's execution ownership")
                report["provenance"]["prerequisite_sources"] = [
                    value["report"]["run_id"] for value in source_inventory.values()
                ]
            output = owner / "execution"
            output.mkdir()
            # External fixtures must have unrelated ancestors. Only this exact created owner is removed.
            scratch = Path(tempfile.mkdtemp(prefix="lotm-ci-owned-")).resolve()
            if scratch.is_relative_to(original) or scratch.is_relative_to(workspace):
                raise ValueError("External scratch cannot inherit project ancestors")
            (owner / "private-scratch-owner.json").write_text(
                json.dumps({"path": str(scratch), "alias": "external-scratch"}), encoding="utf-8"
            )
            session = AdapterSession(
                workspace,
                snapshot,
                output,
                {"python": args.python, "powershell7": args.pwsh, "actionlint": args.actionlint},
                args.module_root,
                args.wheel,
                args.runtime_wheel,
                format_representation(scope["provenance"]["snapshot_kind"]),
                render_report=args.render_bootstrap_report,
            )
            for name in ("TEMP", "TMP", "TMPDIR"):
                session.env[name] = str(scratch)
            # Policy helpers require a Git worktree. Create only a private captured index;
            # original scope/snapshot provenance remains authoritative, with no synthetic commit.
            git = shutil.which("git")
            if not git:
                raise ValueError("Git prerequisite unavailable for private captured index")
            index_directory = output / "private-index"
            index_directory.mkdir()
            workspace_tmp = workspace / ".tmp"
            workspace_tmp.mkdir()
            paths_file = workspace_tmp / "captured-paths.bin"
            paths_file.write_bytes(b"\0".join(name.encode("utf-8") for name in sorted(snapshot.files)) + b"\0")
            for command in (
                [
                    git,
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "core.longpaths=true",
                    "-C",
                    str(workspace),
                    "init",
                    "--quiet",
                ],
                [
                    git,
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "core.longpaths=true",
                    "-C",
                    str(workspace),
                    "add",
                    "-f",
                    "--pathspec-from-file=" + str(paths_file),
                    "--pathspec-file-nul",
                ],
            ):
                process = run_process(
                    command,
                    cwd=workspace,
                    env=session.env,
                    output_parent=index_directory,
                    lease=Lease(time.monotonic() + 30),
                    termination=0.5,
                    cleanup=3,
                    cancel=cancel,
                )
                if (
                    process["status"] != "exited"
                    or process["child_exit_code"] != 0
                    or not process["cleanup"]["verified"]
                ):
                    report["cleanup"]["verified"] = process["cleanup"]["verified"]
                    raise ValueError("Private snapshot index could not be established")
            report["provenance"]["execution_checkout"] = "captured-source-with-private-index"
            session.preflight(selected, catalog.runtime_versions, cancel)
            context = session.context(cancel)
            if not session.containment_verified:
                report["cleanup"] = {"verified": False, "state": "failed", "external_scratch": "retained-unsafe"}
                raise ValueError("Prerequisite process containment could not be verified")
            report["runtime_inventory"] = session.inventory
            selected_ids = [row["execution_id"] for row in selected]
            report["selection"] = {
                "candidate_ids": candidates,
                "selected_ids": selected_ids,
                "unselected": [
                    {"id": name, "reason": "Delegated to registered shard"}
                    for name in candidates
                    if name not in selected_ids
                ],
                "requested_mode": "full",
                "applied_mode": "full",
                "changes": scope["changes"],
                "fallback_reasons": scope["fallback_reasons"],
            }
            journal.event("plan", report)

            def record_unit(result):
                saved = copy.deepcopy(result)
                recorded_rows.append(saved)
                entries = persist_units([saved], owner)
                recorded_artifacts.extend(entries)
                journal.event("unit-terminal", {"result": saved, "artifacts": entries})

            results, failures, guard = execute_units(
                execution_plan,
                session.execute,
                budget,
                cancel,
                lambda: guarded_manifest(workspace, snapshot),
                sources,
                observer=record_unit,
            )
            report["results"], report["canonical_guard"] = results, guard
            dispositions = actual_dispositions(
                scope, snapshot, results, context, delegated=bool(args.shard), profile_ids=set(candidates)
            )
            report["provenance"]["actual_change_scope"] = dispositions
            if context["status"] != "passed":
                failures.append(
                    {
                        "id": None,
                        "classification": "policy",
                        "excerpt": "Actual composed-context validation did not pass",
                    }
                )
            if (
                not args.shard
                and args.profile not in {"workflow-policy", "annotation-policy"}
                and any(row["status"] == "failed" for row in dispositions["dispositions"])
            ):
                failures.append(
                    {"id": None, "classification": "policy", "excerpt": "Actual change policy dispositions incomplete"}
                )
            report["results"] = recorded_rows
            report["artifacts"] = recorded_artifacts
            report["budget"] = {
                **budget_record,
                "setup_allowance_seconds": 600,
                "elapsed_seconds": time.monotonic() - started,
                "exhausted": any(row["classification"] == "budget" for row in results),
            }
            if guard["containment_verified"]:
                try:
                    remove_scratch(scratch)
                    report["cleanup"] = {
                        "verified": True,
                        "state": "retained",
                        "external_scratch": "removed",
                        "reason": "Diagnostic/source evidence retained",
                    }
                    scratch = None
                except Exception as error:
                    report["cleanup"] = {
                        "verified": False,
                        "state": "failed",
                        "external_scratch": "retained",
                        "error": str(error),
                    }
                    failures.append({"id": None, "classification": "cleanup", "excerpt": str(error)})
            else:
                report["cleanup"] = {"verified": False, "state": "failed", "external_scratch": "retained-unsafe"}
                failures.append(
                    {
                        "id": None,
                        "classification": "cleanup",
                        "excerpt": "Unverified containment; external scratch retained",
                    }
                )
            if args.shard:
                report["provenance"]["shard_source"] = catalog.expected_manifest(
                    args.shard_plan, args.shard, snapshot.digest
                )
        report["reviews"] = [
            {"family": row["family"], "required": True, "status": "pending", "evidence": row["evidence"]}
            for row in plan["required_reviews"]
        ]
        report["failures"] = failures
        report["status"], report["exit_code"] = outcome(
            report["results"], failures, cancel.is_set(), [] if args.shard else report["reviews"]
        )
        report["counts"] = {
            "candidate": len(candidates),
            "selected": len(report["results"]),
            "unselected": len(candidates) - len(report["results"]),
            "terminal": counts(report["results"]),
        }
    except Exception as error:
        if "session" in locals() and not session.containment_verified:
            report["cleanup"] = {"verified": False, "state": "failed", "external_scratch": "retained-unsafe"}
        if recorded_rows:
            report["results"] = recorded_rows
            report["artifacts"] = recorded_artifacts
            remaining = [
                row
                for row in execution_plan["units"]
                if row["execution_id"] not in {value["id"] for value in recorded_rows}
            ]

            class NoRemainingAdmission:
                def admit(self, seconds):
                    return None

            pending, _, _ = execute_units(
                {**execution_plan, "units": remaining}, lambda *args: None, NoRemainingAdmission(), cancel, lambda: None
            )
            for row in pending:
                row.update(classification="report", reasons=["Durable recording failed; later units not launched"])
            report["results"].extend(pending)
        if report["provenance"] and not report["results"]:

            class NoAdmission:
                def admit(self, seconds):
                    return None

            rows, _, _ = execute_units(execution_plan, lambda *args: None, NoAdmission(), cancel, lambda: None)
            for row in rows:
                if row["status"] != "cancelled":
                    row.update(
                        classification="prerequisite",
                        reasons=["Execution setup/evidence admission failed: " + str(error)],
                    )
            report["results"] = rows
        planning_error = isinstance(error, (ScopeError, CatalogError)) or not report["runtime_inventory"]
        report.update(
            status="cancelled" if cancel.is_set() else "failed",
            exit_code=130 if cancel.is_set() else 2 if planning_error else 1,
        )
        if report["results"]:
            report["counts"] = {
                "candidate": len(candidates),
                "selected": len(report["results"]),
                "unselected": len(candidates) - len(report["results"]),
                "terminal": counts(report["results"]),
            }
            report["failures"] = list(locals().get("failures", []))
        report["failures"].append(
            {
                "id": None,
                "classification": "scope"
                if isinstance(error, ScopeError)
                else "catalog"
                if isinstance(error, CatalogError)
                else "result-contract",
                "excerpt": str(error),
            }
        )
    finally:
        if scratch is not None:
            # Failure cleanup only follows explicit ownership; do not remove an unsafe live tree's scratch.
            if report["cleanup"].get("verified"):
                try:
                    remove_scratch(scratch)
                    report["cleanup"]["external_scratch"] = "removed"
                except OSError as error:
                    report["cleanup"] = {"verified": False, "state": "failed", "error": str(error)}
                    report["exit_code"] = 1 if report["exit_code"] == 0 else report["exit_code"]
                    report["status"] = "failed"
        for name, handler in signals.items():
            signal.signal(name, handler)
    path = owner / "report.json"
    try:
        journal.event("run-terminal", report)
        journal.close()
        finalize(owner, report)
    except Exception as error:
        journal.close()
        report.update(status="failed", exit_code=130 if cancel.is_set() else 1)
        report["failures"].append({"id": None, "classification": "report", "excerpt": str(error)})
        print("CI report finalization failed: " + str(error), file=sys.stderr)
        # This is diagnostic evidence, not a complete publication bundle; never replace foreign targets.
        report["complete"] = False
        try:
            atomic_bytes(owner, "finalization-failure.json", encoded(report))
            path = owner / "finalization-failure.json"
        except Exception as secondary:
            path = None
            print("CI failure evidence could not be written: " + str(secondary), file=sys.stderr)
    return report, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--profile", required=True)
    parser.add_argument("--scope", required=True, choices=sorted(MODES))
    parser.add_argument("--base")
    parser.add_argument("--source")
    parser.add_argument("--executed")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--pwsh")
    parser.add_argument("--module-root")
    parser.add_argument("--actionlint")
    parser.add_argument("--wheel")
    parser.add_argument("--runtime-wheel")
    parser.add_argument("--render-bootstrap-report")
    parser.add_argument("--shard-plan")
    parser.add_argument("--shard")
    parser.add_argument("--shard-result", action="append", dest="shard_results", default=[])
    parser.add_argument("--source-result", action="append", dest="source_results", default=[])
    parser.add_argument("--output-root", default=".tmp/ci-execution")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args()
    if args.json and args.summary_json:
        parser.error("Choose detailed or concise JSON")
    try:
        report, path = execute(args)
    except Exception as error:
        report, path = empty_report(args.profile, "unestablished"), None
        report["failures"] = [
            {"id": None, "classification": "report" if isinstance(error, OSError) else "scope", "excerpt": str(error)}
        ]
        if isinstance(error, OSError):
            report["exit_code"] = 1
        print("CI execution could not establish evidence: " + str(error), file=sys.stderr)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.summary_json:
        print(json.dumps(summary(report, path.name if path else None), ensure_ascii=False, indent=2))
    else:
        terminal = ", ".join(f"{value} {name}" for name, value in report["counts"]["terminal"].items() if value)
        elapsed = report["budget"].get("elapsed_seconds")
        print(
            f"CI {report['status']}: {report['counts']['selected']} units; "
            f"{terminal or 'no completed units'}; "
            + (f"{elapsed:.3f}s. " if elapsed is not None else "")
            + f"Report: {path}"
        )
        for failure in report["failures"]:
            text, truncated = excerpt(failure["excerpt"])
            print(
                f"{failure['id'] or 'run'} [{failure['classification']}]: {text}"
                + (" [excerpt truncated; see detailed evidence]" if truncated else "")
            )
    raise SystemExit(report["exit_code"])


if __name__ == "__main__":
    main()
