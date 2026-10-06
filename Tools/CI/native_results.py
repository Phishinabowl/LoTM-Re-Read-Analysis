"""Reconcile native JUnit/phase evidence without manufacturing native test cases."""

import math
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_junit(path):
    content = Path(path).read_bytes()
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("Native XML declarations/entities are not accepted")
    root = ET.fromstring(content)
    if root.tag not in ("testsuites", "testsuite"):
        raise ValueError("Expected native JUnit testsuite(s)")
    cases = []
    for item in root.iter("testcase"):
        duration = float(item.get("time", "0"))
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("Invalid native case duration")
        kinds = [name for name in ("failure", "error", "skipped") if item.find(name) is not None]
        if len(kinds) > 1:
            raise ValueError("Ambiguous native case outcome")
        cases.append(
            {
                "classname": item.get("classname", ""),
                "name": item.get("name", ""),
                "outcome": kinds[0] if kinds else "passed",
                "duration": duration,
            }
        )
    counts = {
        key: sum(row["outcome"] == value for row in cases)
        for key, value in [("passed", "passed"), ("failed", "failure"), ("errors", "error"), ("skipped", "skipped")]
    }
    counts["entries"] = len(cases)
    return root, cases, counts


def validate_phase(runtime, child_exit, phase):
    expected = "pytest" if runtime == "python" else "pester"
    if phase.get("framework") != expected or phase.get("exit_code") != child_exit:
        raise ValueError("Native framework/exit evidence does not match child process")
    for name in ("collected", "excluded"):
        value = phase.get(name, 0)
        if type(value) is not int or value < 0:
            raise ValueError("Invalid native inventory count")
    if "collected" not in phase or not isinstance(phase.get("reports"), list):
        raise ValueError("Native inventory/phase evidence unavailable")
    identities = set()
    for row in phase["reports"]:
        key = (row["id"], row.get("phase"))
        if not row["id"] or key in identities:
            raise ValueError("Missing or duplicate native phase identity")
        identities.add(key)
    if runtime == "powershell7" and len(identities) != phase["collected"]:
        raise ValueError("Native selected identity count does not match inventory")


def classify(runtime, child_exit, phase, counts):
    if child_exit == 130 or phase.get("interrupted"):
        return "cancelled", "cancellation", 130
    if phase.get("collection_errors") or (runtime == "python" and child_exit in (3, 4)):
        return "error", "collection", 1
    if runtime == "python":
        failing = [row for row in phase.get("reports", []) if row["outcome"] == "failed"]
        if any(row["phase"] == "teardown" for row in failing):
            return "error", "cleanup", 1
        if any(row["phase"] == "setup" for row in failing):
            return "error", "prerequisite", 1
    elif phase.get("cleanup_failed"):
        return "error", "cleanup", 1
    elif phase.get("prerequisite_failed"):
        return "error", "prerequisite", 1
    elif phase.get("failed_containers"):
        return "error", "collection" if phase.get("discovery_failed") else "prerequisite", 1
    if phase.get("collected", 0) == 0 or counts["skipped"] or any(row.get("xfail") for row in phase.get("reports", [])):
        return "error", "result-contract", 1
    if child_exit or counts["failed"] or counts["errors"]:
        return "failed", "assertion", 1
    if counts["entries"] != phase["collected"]:
        return "error", "result-contract", 1
    return "passed", None, 0


def publication_xml(root, identity, destination, source_root=None):
    # Preserve raw XML separately; prefix only existing cases, never add successful group cases.
    for item in root.iter("testcase"):
        original = item.get("classname", "")
        if source_root is not None:
            original = Path(original).resolve().relative_to(Path(source_root).resolve()).as_posix()
        if not original.startswith(identity + "."):
            item.set("classname", identity + "." + original)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
