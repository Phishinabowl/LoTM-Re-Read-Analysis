"""Plan-ordered aggregate execution and strict shard evidence admission; publication is separate."""

import copy
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

from catalog import CatalogError
from layer_adapters import read_json, conformance_result, compatibility_result, typed_equal
from native_results import parse_junit, validate_phase, classify

STATES = ("passed", "failed", "error", "timed-out", "cancelled", "blocked", "skipped")
LAYERS = {
    "policy": "static-policy",
    "implementation": "implementation-tests",
    "conformance": "language-neutral-conformance",
    "compatibility": "project-compatibility",
    "parity": "cross-runtime-parity",
}


def execute_units(plan, dispatch, budget, cancel, guard, sources=None, observer=None):
    results, failures, complete = [], [], dict(sources or {})
    safe, contained, changed = True, True, []
    for row in plan["units"]:
        identity = row["execution_id"]
        owner, runtime = identity.split("::")[0].split("/")[0], identity.split("::")[1]
        result = {
            "id": identity,
            "owner": owner,
            "layer": LAYERS[owner],
            "runtime": runtime,
            "participating_runtimes": row["runtimes"],
            "blocking": True,
            "status": "blocked",
            "classification": "prerequisite",
            "child_exit_code": None,
            "elapsed_seconds": 0,
            "deadline_seconds": row["deadline_seconds"],
            "attempts": 0,
            "native_counts": None,
            "reasons": [],
            "diagnostics": {},
            "artifacts": [],
        }
        dependencies = [
            name for name in row["depends_on"] if name not in complete or complete[name]["status"] != "passed"
        ]
        lease = None
        if cancel.is_set():
            result.update(status="cancelled", classification="cancellation", reasons=["Run cancellation requested"])
        elif not safe:
            result.update(classification="canonical-mutation", reasons=["Shared source or containment became unsafe"])
        elif dependencies:
            result["reasons"] = ["Required prerequisite did not pass: " + name for name in dependencies]
        elif row["availability"] == "blocked":
            result["reasons"] = row["reasons"]
        elif (lease := budget.admit(row["deadline_seconds"])) is None:
            result.update(
                classification="budget", reasons=["Whole unit allowance cannot fit before lifecycle reserves"]
            )
        else:
            started = time.monotonic()
            try:
                guard()
                result["attempts"] = 1
                outcome = dispatch(row, lease, cancel, complete)
                if outcome.get("status") not in STATES:
                    raise ValueError("Adapter did not supply a terminal unit state")
                result.update(outcome)
                if result["status"] == "blocked":
                    result["attempts"] = 0
                if result["status"] not in {"cancelled", "timed-out", "blocked"}:
                    lease.verify()
            except TimeoutError as error:
                result.update(status="timed-out", classification="timeout", reasons=[str(error)])
            except Exception as error:
                result.update(status="error", classification="result-contract", reasons=[str(error)])
            result["elapsed_seconds"] = time.monotonic() - started
            for process in result.get("processes", []):
                if not process["cleanup"]["verified"]:
                    safe = False
                    contained = False
                    failures.append(
                        {"id": identity, "classification": "cleanup", "excerpt": "Owned tree cleanup unverified"}
                    )
            try:
                guard()
            except Exception as error:
                safe = False
                changed.append(str(error))
                failures.append({"id": identity, "classification": "canonical-mutation", "excerpt": str(error)})
        if result["status"] != "passed":
            failures.append(
                {
                    "id": identity,
                    "classification": result["classification"],
                    "excerpt": "\n".join(result.get("reasons", [])) or result["status"],
                }
            )
        if result["status"] == "cancelled":
            cancel.set()
        complete[identity] = result
        results.append(result)
        if observer is not None:
            observer(result)
    return results, failures, {"unchanged": not changed, "changed_paths": changed, "containment_verified": contained}


def counts(results):
    return {state: sum(row["status"] == state for row in results) for state in STATES}


def outcome(results, failures, cancelled, reviews):
    if cancelled or any(row["status"] == "cancelled" for row in results):
        return "cancelled", 130
    if (
        failures
        or any(row["status"] != "passed" for row in results)
        or any(row["status"] != "accepted" for row in reviews)
    ):
        return "failed", 1
    return "passed", 0


def artifact(path, owner, producer, required=True):
    path, owner = Path(path), Path(owner).resolve()
    resolved = path.resolve()
    for parent in path.parents:
        if parent == owner.parent:
            break
        if parent.is_symlink() or parent.is_junction():
            raise ValueError("Artifact traverses a link")
    if path.is_symlink() or path.is_junction() or not resolved.is_relative_to(owner) or not path.is_file():
        raise ValueError("Artifact escapes run ownership or is missing")
    data = path.read_bytes()
    return {
        "path": resolved.relative_to(owner).as_posix(),
        "media_type": "application/json"
        if path.suffix == ".json"
        else "application/xml"
        if path.suffix == ".xml"
        else "application/octet-stream",
        "producer": producer,
        "required": required,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "state": "complete",
    }


def persist_units(results, owner):
    """Retain stable adapter inputs alongside raw process streams; final atomic lifecycle belongs to 4.5."""
    manifests = []
    for row in results:
        directory = owner / "units" / row["id"].replace("/", "-").replace("::", "-")
        directory.mkdir(parents=True, exist_ok=True)
        evidence = row.pop("evidence", None)
        from execution_reports import atomic_bytes, encoded, xml_bytes

        if evidence is not None:
            detail = directory / "detail.json"
            atomic_bytes(owner, detail.relative_to(owner).as_posix(), encoded(evidence))
            row["artifacts"].append(detail.relative_to(owner).as_posix())
            manifests.append(artifact(detail, owner, row["id"]))
            if row["native_counts"] is not None:
                for source, name in [
                    ("native.xml", "native.xml"),
                    ("native-phases.json", "phase.json"),
                    ("junit.xml", "publication.xml"),
                ]:
                    target = directory / name
                    content = (Path(evidence["run_directory"]) / source).read_bytes()
                    if name == "publication.xml":
                        content = xml_bytes(parse_junit(Path(evidence["run_directory"]) / source)[0])
                    atomic_bytes(
                        owner,
                        target.relative_to(owner).as_posix(),
                        content,
                    )
                    row["artifacts"].append(target.relative_to(owner).as_posix())
                    manifests.append(artifact(target, owner, row["id"]))
        retained = row.pop("retained_native", {})
        for name, source in retained.items():
            target = directory / ("partial-" + name if row["native_counts"] is None else "child-" + name)
            atomic_bytes(owner, target.relative_to(owner).as_posix(), Path(source).read_bytes())
            row["artifacts"].append(target.relative_to(owner).as_posix())
            manifests.append(artifact(target, owner, row["id"]))
            if name == "native.xml" and row["native_counts"] is None:
                try:
                    tree, _, _ = parse_junit(target)
                    for case in tree.iter("testcase"):
                        # Interrupted raw XML may contain machine-specific PS source paths.
                        original = case.get("classname", "").replace("\\", "/")
                        if "Tools/Tests/" in original:
                            original = "Tools/Tests/" + original.split("Tools/Tests/", 1)[1]
                        case.set("classname", row["id"].replace("::", ".") + "." + original)
                    publication = directory / "publication.xml"
                    atomic_bytes(owner, publication.relative_to(owner).as_posix(), xml_bytes(tree))
                    row["artifacts"].append(publication.relative_to(owner).as_posix())
                    manifests.append(artifact(publication, owner, row["id"]))
                except (ValueError, ET.ParseError) as error:
                    # Invalid/incomplete raw XML remains a diagnostic, never an upload candidate.
                    row["diagnostics"]["partial-native"] = {"error": str(error)}
        for index, process in enumerate(row.pop("processes", [])):
            source = Path(process["directory"])
            diagnostics = {}
            for name in ("stdout.bin", "stderr.bin", "guardian.bin", "process.json"):
                path = source / name
                if path.exists():
                    relative = path.relative_to(owner).as_posix()
                    row["artifacts"].append(relative)
                    manifests.append(artifact(path, owner, row["id"]))
                    diagnostics[name] = relative
            row["diagnostics"][str(index)] = {
                "files": diagnostics,
                "capture": process.get("diagnostics", {}),
                "cleanup": process["cleanup"],
            }
    return manifests


def actual_dispositions(scope, snapshot, results, context, delegated=False, profile_ids=None):
    """Actual current files are covered by full static scans independently of regression impact selection."""
    outcomes = {row["id"]: row["status"] for row in results}
    paths = scope["policy_scope"]["paths"] if scope["policy_scope"]["mode"] == "changed" else sorted(snapshot.files)
    rows = []
    for path in paths:
        suffix = Path(path).suffix.lower()
        required = []
        if suffix in {".py", ".pyi"}:
            required.append("policy/ruff::python")
        if suffix in {".ps1", ".psm1", ".psd1"}:
            required.append("policy/powershell-format::powershell7")
        if path.startswith(".github/workflows/") and suffix in {".yml", ".yaml"}:
            required.append("policy/actionlint::python")
        # The annotation policy itself decides eligible extensions/exclusions/prohibited surfaces.
        required.append("policy/work-annotations::python")
        missing = [identity for identity in required if outcomes.get(identity) != "passed"]
        outside = profile_ids is not None and any(identity not in profile_ids for identity in missing)
        rows.append(
            {
                "path": path,
                "exists": path in snapshot.files,
                "validators": required,
                "status": "outside-profile"
                if outside and context["status"] == "passed"
                else "delegated"
                if delegated and missing
                else "failed"
                if missing or context["status"] != "passed"
                else "validated",
                "deletion_integrity": "current catalog and composed configuration references"
                if path not in snapshot.files
                else None,
            }
        )
    return {
        "mode": scope["policy_scope"]["mode"],
        "deletion_precision": scope["policy_scope"]["deletion_precision"],
        "context": {key: value for key, value in context.items() if key != "process"},
        "dispositions": rows,
        "authority": (
            "current registered static policies and actual composed context; authored logical schema remains deferred"
        ),
    }


def collect_shards(catalog, plan_id, bundles, snapshot_digest, partial=False, provenance=None):
    """A successful artifact upload alone never satisfies source provenance, coverage or native truth."""
    documents = [(Path(path), read_json(path)) for path in bundles]
    if partial:
        seen = set()
        for _, document in documents:
            source = document["source"]
            expected = catalog.expected_manifest(plan_id, source["shard"], snapshot_digest)
            if source != expected or source["shard"] in seen:
                raise CatalogError("Wrong/duplicate prerequisite shard source")
            seen.add(source["shard"])
    else:
        catalog.validate_manifests(plan_id, [document["source"] for _, document in documents], snapshot_digest)
    rows, artifacts, inventory = {}, [], {}
    semantic_evidence = {}
    for path, document in documents:
        from execution_reports import verify_publication

        try:
            admitted = verify_publication(path.parent)
            if path.name != "shard-result.json" or not admitted["complete"]:
                raise ValueError("Shard requires its finalized publication bundle")
        except (OSError, ValueError, KeyError) as error:
            raise CatalogError("Shard report publication was not finalized: " + str(error)) from error
        if (
            set(document) != {"contract", "contract_version", "source", "report"}
            or document["contract"] != "ci-shard-result"
            or type(document["contract_version"]) is not int
            or document["contract_version"] != 1
        ):
            raise CatalogError("Invalid shard result envelope")
        report = document["report"]
        if provenance is not None:
            keys = ("mode", "base_tip", "source_tip", "merge_base", "executed_commit", "checkout_kind", "snapshot_kind")
            if any(report["provenance"].get(key) != provenance.get(key) for key in keys):
                raise CatalogError("Shard source/merge/scope provenance differs from this collection")
        if (
            report.get("contract") != "ci-execution-report"
            or type(report.get("contract_version")) is not int
            or report["contract_version"] != 1
            or report.get("complete") is not True
        ):
            raise CatalogError("Incomplete/wrong shard execution report")
        if (
            report["profile"] != document["source"]["profile"]
            or report["provenance"]["snapshot_digest"] != snapshot_digest
            or report["provenance"]["catalog_digests"] != catalog.source_digests
        ):
            raise CatalogError("Foreign shard execution tree/profile/catalog")
        if [row["id"] for row in report["results"]] != document["source"]["units"]:
            raise CatalogError("Wrong/omitted/reordered shard result inventory")
        known = {}
        for entry in report["artifacts"]:
            from scope import safe_path

            safe_path(entry["path"])
            actual = artifact(path.parent / entry["path"], path.parent, entry["producer"], entry["required"])
            if actual != entry or entry["path"] in known:
                raise CatalogError("Stale/duplicate/foreign artifact evidence")
            known[entry["path"]] = entry
        for row in report["results"]:
            if row["status"] not in STATES or row["id"] in rows or any(name not in known for name in row["artifacts"]):
                raise CatalogError("Invalid terminal state or missing/duplicate unit evidence")
            details = [name for name in row["artifacts"] if name.endswith("/detail.json")]
            evidence = read_json(path.parent / details[0]) if details else None
            descriptor = catalog.units[row["id"].split("::")[0]]
            if (
                row["owner"] != descriptor["owner"]
                or row["runtime"] != row["id"].split("::")[1]
                or row["blocking"] is not True
                or row["deadline_seconds"] != descriptor["deadline_seconds"]
            ):
                raise CatalogError("Shard unit metadata differs from approved catalog")
            if row["child_exit_code"] is not None and type(row["child_exit_code"]) is not int:
                raise CatalogError("Noninteger child exit code")
            if (
                descriptor["adapter"] in {"pytest", "pester"}
                and row["status"] == "passed"
                and row["native_counts"] is None
            ):
                raise CatalogError("Passing native shard omitted case counts")
            if descriptor["adapter"] not in {"pytest", "pester"} and row["native_counts"] is not None:
                raise CatalogError("Custom shard invented native assertion counts")
            if row["status"] == "passed":
                process_records = [name for name in row["artifacts"] if name.endswith("/process.json")]
                if row["owner"] != "parity" and (row["child_exit_code"] != 0 or not process_records):
                    raise CatalogError("Passing shard lacks owned successful process evidence")
                for name in process_records:
                    process = read_json(path.parent / name)
                    if (
                        process.get("status") != "exited"
                        or process.get("child_exit_code") != 0
                        or process["cleanup"]["verified"] is not True
                    ):
                        raise CatalogError("Process evidence contradicts passing shard")
                if row["owner"] == "conformance":
                    if not conformance_result(evidence, row["id"].split("/")[1].split("::")[0])[0]:
                        raise CatalogError("Conformance evidence does not pass")
                if row["owner"] == "compatibility":
                    if not compatibility_result(evidence, row["id"].split("/")[1].split("::")[0]):
                        raise CatalogError("Compatibility evidence does not pass")
                if row["native_counts"] is not None:
                    expected_identity = row["id"].split("/")[1].split("::")[0] + "." + row["runtime"]
                    if (
                        evidence.get("contract") != "native-test-run"
                        or evidence.get("identity") != expected_identity
                        or evidence.get("paths") != descriptor["entry"]
                    ):
                        raise CatalogError("Native shard belongs to another approved group/input")
                    xml = [name for name in row["artifacts"] if name.endswith("/native.xml")]
                    phase_paths = [name for name in row["artifacts"] if name.endswith("/phase.json")]
                    if len(xml) != 1 or len(phase_paths) != 1:
                        raise CatalogError("Native shard lacks actual case/phase evidence")
                    _, _, native = parse_junit(path.parent / xml[0])
                    phase = read_json(path.parent / phase_paths[0])
                    validate_phase(row["runtime"], evidence["child_exit_code"], phase)
                    if (
                        row["native_counts"] != {"collected": phase["collected"], **native}
                        or classify(row["runtime"], evidence["child_exit_code"], phase, native)[0] != "passed"
                    ):
                        raise CatalogError("Native shard coverage/counts are false")
            rows[row["id"]] = copy.deepcopy(row)
            semantic_evidence[row["id"]] = evidence
        if (
            report["counts"]["terminal"] != counts(report["results"])
            or report["canonical_guard"]["unchanged"] is not True
            or report["cleanup"]["verified"] is not True
        ):
            raise CatalogError("False shard counts/guard/cleanup evidence")
        if any(type(value) is not int or value < 0 for value in report["counts"]["terminal"].values()):
            raise CatalogError("Invalid shard terminal counts")
        expected_status, expected_exit = outcome(
            report["results"], report["failures"], report["status"] == "cancelled", []
        )
        if (
            report["status"] != expected_status
            or type(report["exit_code"]) is not int
            or report["exit_code"] != expected_exit
        ):
            raise CatalogError("Shard aggregate outcome contradicts recorded failures/coverage")
        inventory[document["source"]["shard"]] = {"root": str(path.parent), "report": report}
        artifacts.extend(report["artifacts"])
    plan = catalog.shard_plans[plan_id]
    order = catalog.profiles[plan["profile"]]["execution"]
    if not partial and set(order) != set(rows):
        raise CatalogError("Shard partition incomplete")
    for identity, row in rows.items():
        descriptor = catalog.units[identity.split("::")[0]]
        if row["owner"] == "parity" and row["status"] == "passed":
            pairs = {}
            for source in descriptor["source_units"]:
                if rows[source]["status"] != "passed":
                    raise CatalogError("Passing parity has failed/blocked source coverage")
                summary = semantic_evidence[source]["suites"][0]["summary"]
                pairs.setdefault(source.split("::")[0], {})[source.split("::")[1]] = summary
            if not pairs or any(
                set(pair) != {"python", "powershell7"} or not typed_equal(pair["python"], pair["powershell7"])
                for pair in pairs.values()
            ):
                raise CatalogError("Passing shard parity contradicts semantic source evidence")
    if partial:
        for name in rows:
            rows[name]["evidence"] = semantic_evidence[name]
    return [rows[name] for name in order if name in rows], inventory
