"""Run-owned atomic evidence, deterministic projections and fail-closed publication admission."""

import copy
import hashlib
import html
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import uuid
import xml.etree.ElementTree as ET

from native_results import parse_junit


def decode_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate report key: " + key)
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite report value: " + value)

    return json.loads(data, object_pairs_hook=unique, parse_constant=invalid)


def confined(owner, name):
    owner = Path(owner).absolute()
    original = name
    name = PurePosixPath(name)
    if name.is_absolute() or any(part in {"..", "."} for part in name.parts) or "\\" in str(name) or ":" in str(name):
        raise ValueError("Unsafe report path")
    path = owner / str(name)
    if not name.parts or path == owner or str(name) != original:
        raise ValueError("Report requires a file path")
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError("Report path traverses a link")
        if part == owner:
            break
    if owner.resolve() != owner or not path.resolve().is_relative_to(owner):
        raise ValueError("Report escapes run ownership")
    return path


def atomic_bytes(owner, name, content, replace=False):
    path = confined(owner, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and (not replace or not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError("Report refuses an existing foreign or linked target")
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # Atomic no-clobber admission even when another writer creates the target meanwhile.
            os.link(temporary, path)
            temporary.unlink()
    finally:
        temporary.unlink(missing_ok=True)
    return path


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def fingerprint(owner, name, producer="report"):
    path = confined(owner, name)
    if not path.is_file():
        raise ValueError("Missing run artifact: " + name)
    data = path.read_bytes()
    return {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "producer": producer}


def verify_files(owner, entries):
    names = set()
    for entry in entries:
        if entry["path"] in names:
            raise ValueError("Duplicate artifact path")
        names.add(entry["path"])
        actual = fingerprint(owner, entry["path"])
        if type(entry["bytes"]) is not int or any(actual[key] != entry[key] for key in ("bytes", "sha256")):
            raise ValueError("Stale or changed artifact: " + entry["path"])


def journal_records(owner, partial=False):
    lines = confined(owner, "events.jsonl").read_bytes().splitlines(keepends=True)
    records, units_started, terminal = [], False, False
    for index, line in enumerate(lines):
        if not line.endswith(b"\n"):
            if partial and index == len(lines) - 1:
                break
            raise ValueError("Incomplete finalized journal")
        event = decode_json(line)
        if (
            set(event) != {"sequence", "kind", "record"}
            or type(event["sequence"]) is not int
            or event["sequence"] != index + 1
            or event["record"]["path"] != f"records/{index + 1:06d}.json"
        ):
            raise ValueError("Journal sequence/record mismatch")
        kind = event["kind"]
        if (
            terminal
            or kind not in {"run-start", "plan", "unit-terminal", "run-terminal"}
            or (index == 0 and kind != "run-start")
            or (index > 0 and kind == "run-start")
            or (units_started and kind == "plan")
        ):
            raise ValueError("Unknown or misplaced journal transition")
        units_started = units_started or kind == "unit-terminal"
        terminal = kind == "run-terminal"
        verify_files(owner, [event["record"]])
        payload = decode_json(confined(owner, event["record"]["path"]).read_text(encoding="utf-8"))
        records.append((event, payload))
    if not records or (not partial and not terminal):
        raise ValueError("Missing durable run/terminal journal record")
    return records


class Journal:
    """One writer per unique owner; fsync each event after its atomic record is durable."""

    def __init__(self, owner, initial):
        self.owner, self.sequence = Path(owner), 0
        self.stream = confined(owner, "events.jsonl").open("xb")
        self.event("run-start", initial)

    def event(self, kind, payload):
        self.sequence += 1
        record = "records/" + f"{self.sequence:06d}.json"
        atomic_bytes(self.owner, record, encoded(payload))
        event = {
            "sequence": self.sequence,
            "kind": kind,
            "record": fingerprint(self.owner, record),
        }
        self.stream.write((json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def excerpt(value):
    full = str(value).replace("\r\n", "\n").replace("\r", "\n")
    limited = "\n".join(full.split("\n")[:20]).encode("utf-8")[:4096].decode("utf-8", errors="ignore")
    return limited, limited != full


def markdown_text(value):
    value = html.escape(str(value), quote=True)
    return re.sub(r"([\\`*_{\[\]|])", r"\\\1", value).replace("\r", "").replace("\n", "<br>")


def summary(report, report_path="report.json"):
    failures = []
    for row in report["failures"]:
        text, truncated = excerpt(row["excerpt"])
        failures.append(
            {"id": row["id"], "classification": row["classification"], "excerpt": text, "excerpt_truncated": truncated}
        )
    return {
        "contract": "ci-execution-summary",
        "contract_version": 1,
        "run_id": report["run_id"],
        "profile": report["profile"],
        "status": report["status"],
        "exit_code": report["exit_code"],
        "complete": report["complete"],
        "counts": report["counts"],
        "elapsed_seconds": report["budget"].get("elapsed_seconds"),
        "canonical_outputs_unchanged": report["canonical_guard"].get("unchanged"),
        "cleanup_verified": report["cleanup"].get("verified"),
        "report_path": report_path,
        "results": [{key: row[key] for key in ("id", "status", "native_counts")} for row in report["results"]],
        "failures": failures,
    }


def markdown(report):
    selection = report["selection"]
    lines = [
        "# CI execution: " + markdown_text(report["status"]),
        "",
        f"Profile: {markdown_text(report['profile'])}. Run: {markdown_text(report['run_id'])}.",
        "",
        "Execution commit: " + markdown_text(report["provenance"].get("executed_commit", "unknown")),
        "Scope: " + markdown_text(report["provenance"].get("mode", "unknown")),
        "Selection: " + markdown_text(selection.get("applied_mode", "unknown")),
        "Fallback reasons: " + markdown_text(selection.get("fallback_reasons", [])),
        "",
        f"Units: {report['counts']['selected']} selected; {report['counts']['unselected']} unselected. "
        f"Duration: {report['budget'].get('elapsed_seconds', 'unknown')} seconds.",
        "",
        "Canonical/source guard: " + markdown_text(report["canonical_guard"]),
        "Cleanup: " + markdown_text(report["cleanup"]),
        "",
        "[Detailed JSON](report.json) · [Publication inventory](publication-manifest.json)",
        "",
        "| Unit | Status | Seconds | Native cases (passed / collected) | Reasons |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in report["results"]:
        native = row["native_counts"]
        count = "—" if native is None else f"{native['passed']} / {native['collected']}"
        lines.append(
            f"| {markdown_text(row['id'])} | {row['status']} | {row['elapsed_seconds']:.3f} | "
            f"{count} | {markdown_text('; '.join(row['reasons']))} |"
        )
    for title, rows in [
        ("Unselected coverage", selection.get("unselected", [])),
        ("Retained reviews", report["reviews"]),
    ]:
        if rows:
            lines.extend(["", "## " + title, ""])
            lines.extend("- " + markdown_text(row) for row in rows)
    if report["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in report["failures"]:
            text, truncated = excerpt(failure["excerpt"])
            lines.extend(
                [
                    "- " + markdown_text(f"{failure['id'] or 'run'} [{failure['classification']}]: {text}"),
                    "  Full diagnostic retained in report.json." if truncated else "",
                ]
            )
    lines.extend(["", "## Artifacts", ""])
    for entry in report["artifacts"]:
        from urllib.parse import quote

        lines.append(f"- [{markdown_text(entry['path'])}]({quote(entry['path'], safe='/')})")
    return "\n".join(lines) + "\n"


def xml_bytes(root):
    # XML 1.0 cannot represent control characters; replace them only in this presentation.
    for item in root.iter():
        for key, value in item.attrib.items():
            item.set(key, xml_text(value))
        if item.text:
            item.text = xml_text(item.text)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def xml_text(value):
    return "".join(
        char
        if char in "\t\n\r"
        or 0x20 <= ord(char) <= 0xD7FF
        or 0xE000 <= ord(char) <= 0xFFFD
        or 0x10000 <= ord(char) <= 0x10FFFF
        else "\ufffd"
        for char in str(value).replace("\r\n", "\n").replace("\r", "\n")
    )


def custom_xml(report, native_ids):
    suite = ET.Element("testsuite", name="ci-custom")
    for row in report["results"]:
        if row["id"] in native_ids and row["native_counts"] is not None and row["status"] in {"passed", "failed"}:
            continue
        native_group = row["owner"] == "implementation" and (
            row["native_counts"] is not None or row["status"] != "passed"
        )
        case = ET.SubElement(
            suite,
            "testcase",
            classname=("ci-infrastructure." if native_group else "") + row["owner"] + "." + row["runtime"],
            name=row["id"].split("::")[0],
            time=f"{row['elapsed_seconds']:.6f}",
        )
        status = row["status"]
        tag = {
            "failed": "failure",
            "error": "error",
            "timed-out": "error",
            "blocked": "skipped",
            "cancelled": "skipped",
            "skipped": "skipped",
        }.get(status)
        if tag:
            node = ET.SubElement(case, tag, type=row["classification"] or status, message="; ".join(row["reasons"]))
            node.text = "\n".join(row["reasons"]) + "\nDiagnostics: " + ", ".join(row["artifacts"])
    for index, failure in enumerate(report["failures"]):
        if failure["id"] is not None:
            continue
        case = ET.SubElement(
            suite,
            "testcase",
            classname="ci-infrastructure",
            name=failure["classification"] + "." + str(index),
            time="0",
        )
        ET.SubElement(
            case, "error", type=failure["classification"], message=excerpt(failure["excerpt"])[0]
        ).text = failure["excerpt"]
    for review in report["reviews"]:
        if review["required"] and review["status"] != "accepted":
            case = ET.SubElement(
                suite, "testcase", classname="ci-infrastructure.review", name=review["family"], time="0"
            )
            ET.SubElement(case, "skipped", message="Required maintainer review remains " + review["status"])
    cases = list(suite)
    for name, tag in [("tests", None), ("failures", "failure"), ("errors", "error"), ("skipped", "skipped")]:
        suite.set(name, str(len(cases) if tag is None else sum(case.find(tag) is not None for case in cases)))
    suite.set("time", f"{sum(float(case.get('time')) for case in cases):.6f}")
    return xml_bytes(suite)


def validate_report(report):
    if set(report) != set(
        "contract contract_version run_id mode profile status exit_code complete provenance selection "
        "runtime_inventory budget counts results reviews failures canonical_guard cleanup artifacts".split()
    ):
        raise ValueError("Unknown or missing execution report fields")
    if (
        report["contract"] != "ci-execution-report"
        or type(report["contract_version"]) is not int
        or report["contract_version"] != 1
    ):
        raise ValueError("Unsupported execution report contract")
    selected = report["selection"].get("selected_ids", [])
    identities = [row["id"] for row in report["results"]]
    if identities != selected or len(set(identities)) != len(identities):
        raise ValueError("Recorded selected/result inventory differs")
    if report["counts"]["selected"] != len(identities):
        raise ValueError("Recorded result count differs")
    candidates = report["selection"].get("candidate_ids", [])
    unselected = report["selection"].get("unselected", [])
    if (
        len(set(candidates)) != len(candidates)
        or report["counts"]["candidate"] != len(candidates)
        or report["counts"]["unselected"] != len(unselected)
        or set(selected) & {row["id"] for row in unselected}
        or set(selected) | {row["id"] for row in unselected} != set(candidates)
    ):
        raise ValueError("Selection coverage accounting differs")
    for row in report["results"]:
        if (
            row["status"] not in report["counts"]["terminal"]
            or not math.isfinite(row["elapsed_seconds"])
            or row["elapsed_seconds"] < 0
        ):
            raise ValueError("Invalid terminal record")
    for state, count in report["counts"]["terminal"].items():
        if type(count) is not int or count != sum(row["status"] == state for row in report["results"]):
            raise ValueError("Terminal counts differ")
    known = {entry["path"] for entry in report["artifacts"]}
    if any(name not in known for row in report["results"] for name in row["artifacts"]):
        raise ValueError("Unit references missing artifact")
    if report["status"] == "passed" and (
        not identities
        or report["exit_code"] != 0
        or not report["complete"]
        or report["failures"]
        or any(row["status"] != "passed" for row in report["results"])
        or report["cleanup"].get("verified") is not True
        or report["canonical_guard"].get("unchanged") is not True
    ):
        raise ValueError("Passing record contradicts required evidence")


def native_inventory(owner, report):
    native_ids, xml_entries = set(), []
    for row in report["results"]:
        candidates = [name for name in row["artifacts"] if name.endswith("/publication.xml")]
        if len(candidates) > 1:
            raise ValueError("Duplicate native publication XML")
        if candidates:
            name = candidates[0]
            _, _, native_counts = parse_junit(confined(owner, name))
            if row["native_counts"] is not None and any(
                native_counts[key] != row["native_counts"][key] for key in ("passed", "failed", "errors", "skipped")
            ):
                raise ValueError("Native XML disagrees with recorded cases")
            native_ids.add(row["id"])
            xml_entries.append(
                {
                    "path": name,
                    "format": "JUnit",
                    "identity": row["id"],
                    "counts": native_counts,
                    "partial": row["native_counts"] is None,
                }
            )
        elif row["native_counts"] is not None:
            raise ValueError("Recorded native inventory lacks publication XML")
    return native_ids, xml_entries


def finalize(owner, report):
    """No completion marker is admitted until every expected projection and artifact verifies."""
    validate_report(report)
    verify_files(owner, report["artifacts"])
    native_ids, xml_entries = native_inventory(owner, report)
    atomic_bytes(owner, "custom.xml", custom_xml(report, native_ids))
    _, _, custom_counts = parse_junit(confined(owner, "custom.xml"))
    xml_entries.append({"path": "custom.xml", "format": "JUnit", "identity": "ci-custom", "counts": custom_counts})
    atomic_bytes(owner, "summary.json", encoded(summary(report)))
    atomic_bytes(owner, "summary.md", markdown(report).encode("utf-8"))
    atomic_bytes(owner, "report.json", encoded(report))
    files = list(report["artifacts"]) + [
        fingerprint(owner, name) for name in ("report.json", "summary.json", "summary.md", "custom.xml")
    ]
    journal_path = confined(owner, "events.jsonl")
    if journal_path.exists():
        records = journal_records(owner)
        events = [event for event, _ in records]
        if records[-1][1] != report:
            raise ValueError("Terminal journal differs from finalized report")
        files.append(fingerprint(owner, "events.jsonl"))
        files.extend(event["record"] for event in events)
    if "shard_source" in report["provenance"]:
        atomic_bytes(
            owner,
            "shard-result.json",
            encoded(
                {
                    "contract": "ci-shard-result",
                    "contract_version": 1,
                    "source": report["provenance"]["shard_source"],
                    "report": report,
                }
            ),
        )
        files.append(fingerprint(owner, "shard-result.json"))
    manifest = {
        "contract": "ci-publication-manifest",
        "contract_version": 1,
        "run_id": report["run_id"],
        "execution_status": report["status"],
        "execution_exit_code": report["exit_code"],
        "complete": report["complete"],
        "files": files,
        "xml": xml_entries,
    }
    atomic_bytes(owner, "publication-manifest.json", encoded(manifest))
    verify_files(owner, files)
    atomic_bytes(
        owner,
        "finalized.json",
        encoded({"run_id": report["run_id"], "manifest": fingerprint(owner, "publication-manifest.json")}),
    )
    return manifest


def verify_publication(owner):
    """Return exact XML paths; uploading any one file is not sufficient proof of a complete run."""
    marker = decode_json(confined(owner, "finalized.json").read_text(encoding="utf-8"))
    verify_files(owner, [marker["manifest"]])
    manifest = decode_json(confined(owner, "publication-manifest.json").read_text(encoding="utf-8"))
    if (
        manifest["contract"] != "ci-publication-manifest"
        or manifest["contract_version"] != 1
        or marker["run_id"] != manifest["run_id"]
        or manifest["run_id"] != Path(owner).name
    ):
        raise ValueError("Foreign publication manifest")
    verify_files(owner, manifest["files"])
    report = decode_json(confined(owner, "report.json").read_text(encoding="utf-8"))
    validate_report(report)
    if (
        manifest["execution_status"] != report["status"]
        or manifest["execution_exit_code"] != report["exit_code"]
        or manifest["complete"] != report["complete"]
        or manifest["run_id"] != report["run_id"]
    ):
        raise ValueError("Publication contradicts execution record")
    if decode_json(confined(owner, "summary.json").read_text(encoding="utf-8")) != summary(report):
        raise ValueError("Concise projection contradicts execution record")
    inventory = {row["path"] for row in manifest["files"]}
    expected = {entry["path"] for entry in report["artifacts"]} | {
        "report.json",
        "summary.json",
        "summary.md",
        "custom.xml",
    }
    if "shard_source" in report["provenance"]:
        expected.add("shard-result.json")
    if confined(owner, "events.jsonl").exists():
        records = journal_records(owner)
        events = [event for event, _ in records]
        if records[-1][1] != report:
            raise ValueError("Terminal journal differs from published report")
        expected.add("events.jsonl")
        expected.update(event["record"]["path"] for event in events)
    if inventory != expected:
        raise ValueError("Publication omitted or added unexpected artifacts")
    native_ids, expected_xml = native_inventory(owner, report)
    expected_xml.append(
        {
            "path": "custom.xml",
            "format": "JUnit",
            "identity": "ci-custom",
            "counts": parse_junit(confined(owner, "custom.xml"))[2],
        }
    )
    if manifest["xml"] != expected_xml or confined(owner, "custom.xml").read_bytes() != custom_xml(report, native_ids):
        raise ValueError("XML projection omitted or contradicted recorded units")
    if confined(owner, "summary.md").read_bytes() != markdown(report).encode("utf-8"):
        raise ValueError("Markdown projection contradicts execution record")
    names = [entry["path"] for entry in manifest["xml"]]
    if len(set(names)) != len(names) or not names or any(name not in inventory for name in names):
        raise ValueError("Missing or duplicate XML inventory")
    for entry in manifest["xml"]:
        _, _, counts = parse_junit(confined(owner, entry["path"]))
        if entry["format"] != "JUnit" or counts != entry["counts"]:
            raise ValueError("Publication XML count mismatch")
    return manifest


def recover(source, destination):
    """Recover durable completed records into a new owner, never claim process cleanup or final success."""
    source, destination = Path(source), Path(destination)
    report, artifacts, rows, selected = None, [], [], []
    for event, payload in journal_records(source, partial=True):
        if event["kind"] in {"run-start", "plan", "run-terminal"}:
            report = payload
            selected = report["selection"].get("selected_ids", [])
        elif event["kind"] == "unit-terminal":
            row = payload["result"]
            if row["id"] not in selected or row["id"] in {value["id"] for value in rows}:
                raise ValueError("Foreign or duplicate recovered unit")
            verify_files(source, payload["artifacts"])
            artifacts.extend(payload["artifacts"])
            rows.append(row)
    if report is None:
        raise ValueError("No durable run start")
    if destination.exists() or destination.parent.absolute() != source.parent.absolute():
        raise ValueError("Recovery requires a fresh owner")
    if report["artifacts"]:
        artifacts = report["artifacts"]
        verify_files(source, artifacts)
    destination.mkdir()
    for entry in artifacts:
        atomic_bytes(destination, entry["path"], confined(source, entry["path"]).read_bytes())
    report = copy.deepcopy(report)
    # Terminal event is authoritative when present; otherwise retain completed units only.
    if not report["results"]:
        report["results"] = rows
    established = {row["id"] for row in report["results"]}
    for identity in selected:
        if identity not in established:
            report["results"].append(
                {
                    "id": identity,
                    "owner": identity.split("/")[0],
                    "runtime": identity.split("::")[1],
                    "layer": {
                        "policy": "static-policy",
                        "implementation": "implementation-tests",
                        "conformance": "language-neutral-conformance",
                        "compatibility": "project-compatibility",
                        "parity": "cross-runtime-parity",
                    }[identity.split("/")[0]],
                    "participating_runtimes": None,
                    "blocking": True,
                    "child_exit_code": None,
                    "deadline_seconds": None,
                    "status": "blocked",
                    "classification": "interrupted",
                    "native_counts": None,
                    "elapsed_seconds": 0,
                    "attempts": 0,
                    "reasons": ["No durable terminal evidence"],
                    "artifacts": [],
                    "diagnostics": {},
                }
            )
    report["results"].sort(key=lambda row: selected.index(row["id"]))
    report.update(run_id=destination.name, complete=False, status="failed", exit_code=1)
    report["provenance"]["recovered_from"] = source.name
    report["artifacts"] = artifacts
    report["cleanup"] = {
        "verified": False,
        "state": "unknown",
        "reason": "Interrupted owner; no process cleanup inferred",
    }
    report["canonical_guard"] = {"unchanged": None, "containment_verified": False}
    report["failures"].append(
        {
            "id": None,
            "classification": "interrupted",
            "excerpt": "Recovered partial evidence; original finalization/termination is unverified",
        }
    )
    report["counts"]["selected"] = len(report["results"])
    report["counts"]["candidate"] = len(report["selection"].get("candidate_ids", []))
    report["counts"]["unselected"] = len(report["selection"].get("unselected", []))
    report["counts"]["terminal"] = {
        state: sum(row["status"] == state for row in report["results"]) for state in report["counts"]["terminal"]
    }
    finalize(destination, report)
    return report
