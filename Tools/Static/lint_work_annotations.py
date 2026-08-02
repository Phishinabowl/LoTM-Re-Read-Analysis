#!/usr/bin/env python3
"""Validate implementation-local work annotations and their repository placement."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(__file__).resolve().parents[1] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.project_paths import resolve_project_root  # noqa: E402


POLICY_PATH = Path(__file__).with_name("work-annotations.json")
FIXTURE_PATH = Path(__file__).parent / "Fixtures" / "Work-Annotations" / "cases.json"
MACHINE_ID = re.compile(r"^[a-z][a-z0-9-]*$")
FULL_ANNOTATION = re.compile(r"^(?P<tag>[A-Z][A-Z0-9_-]*) \((?P<owner>[^()]*)\): (?P<body>.*)$")
GITHUB_TRACKING = re.compile(r"^GH #(?P<number>[1-9][0-9]*) - (?P<description>.+)$")
GITHUB_HANDLE = re.compile(r"^@[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
ISSUE_URL = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/issues/(?P<number>[1-9][0-9]*)$"
)
ASSIGNEE_URL = re.compile(r"^https://github\.com/(?P<handle>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)$")


class AnnotationPolicyFailure(RuntimeError):
    """Raised when policy configuration or invocation is invalid."""


@dataclass(frozen=True)
class Policy:
    tags: tuple[str, ...]
    local_owners: tuple[str, ...]
    scannable_extensions: frozenset[str]
    excluded_paths: tuple[str, ...]
    prohibited_paths: tuple[str, ...]
    maximum_file_bytes: int


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int
    message: str
    annotation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "annotation": self.annotation,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Project root; auto-detected when omitted.")
    parser.add_argument("--policy", default=str(POLICY_PATH), help="Annotation policy registry path.")
    parser.add_argument("--fixtures", default=str(FIXTURE_PATH), help="Fixture registry path.")
    parser.add_argument("--fixtures-only", action="store_true", help="Run fixture conformance without scanning files.")
    parser.add_argument(
        "--path", action="append", default=[], help="Scan one repository file or directory; repeatable."
    )
    parser.add_argument("--json", action="store_true", help="Emit a structured JSON summary.")
    return parser.parse_args()


def resolve_config_path(value: str, root: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def require_string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise AnnotationPolicyFailure(f"Policy {key} must be a nonempty string list.")
    if len(value) != len(set(value)):
        raise AnnotationPolicyFailure(f"Policy {key} must not contain duplicates.")
    return value


def normalize_registry_path(value: str, key: str) -> str:
    normalized = value.replace("\\", "/").strip("/")
    path = Path(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise AnnotationPolicyFailure(f"Policy {key} contains an unsafe repository-relative path: {value}")
    return normalized


def load_policy(path: Path) -> Policy:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnnotationPolicyFailure(f"Unable to load annotation policy {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AnnotationPolicyFailure("Annotation policy root must be an object.")
    expected = {
        "schema_version",
        "tags",
        "local_owners",
        "scannable_extensions",
        "excluded_paths",
        "prohibited_paths",
        "maximum_file_bytes",
    }
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown or missing:
        raise AnnotationPolicyFailure(
            f"Annotation policy keys differ: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    if data["schema_version"] != 1:
        raise AnnotationPolicyFailure("Annotation policy schema_version must be integer 1.")
    tags = require_string_list(data, "tags")
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_-]*", tag) for tag in tags):
        raise AnnotationPolicyFailure("Annotation tags must be uppercase machine tokens.")
    owners = require_string_list(data, "local_owners")
    if owners != ["OWNER", "UNASSIGNED"]:
        raise AnnotationPolicyFailure("Annotation local_owners must be OWNER, UNASSIGNED in order.")
    extensions = require_string_list(data, "scannable_extensions")
    if any(not item.startswith(".") or item != item.lower() for item in extensions):
        raise AnnotationPolicyFailure("Scannable extensions must be lowercase dot-prefixed values.")
    excluded = tuple(
        normalize_registry_path(item, "excluded_paths") for item in require_string_list(data, "excluded_paths")
    )
    prohibited = tuple(
        normalize_registry_path(item, "prohibited_paths") for item in require_string_list(data, "prohibited_paths")
    )
    overlaps = [
        (excluded_path, prohibited_path)
        for excluded_path in excluded
        for prohibited_path in prohibited
        if path_is_within(excluded_path, (prohibited_path,)) or path_is_within(prohibited_path, (excluded_path,))
    ]
    if overlaps:
        raise AnnotationPolicyFailure(f"Excluded and prohibited annotation paths must not overlap: {overlaps}")
    maximum = data["maximum_file_bytes"]
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0:
        raise AnnotationPolicyFailure("Annotation maximum_file_bytes must be a positive integer.")
    return Policy(tuple(tags), tuple(owners), frozenset(extensions), excluded, prohibited, maximum)


def path_is_within(path: str, prefixes: tuple[str, ...]) -> bool:
    folded = path.replace("\\", "/").strip("/").casefold()
    for prefix in prefixes:
        candidate = prefix.casefold()
        if folded == candidate or folded.startswith(candidate + "/"):
            return True
    return False


def repository_inventory(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        details = completed.stderr.decode("utf-8", errors="replace").strip()
        raise AnnotationPolicyFailure(f"Unable to discover repository files through Git: {details}")
    paths = completed.stdout.decode("utf-8", errors="strict").split("\0")
    return [root / path for path in paths if path]


def requested_inventory(root: Path, values: list[str]) -> list[Path]:
    requested: list[Path] = []
    for value in values:
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if path != root and root not in path.parents:
            raise AnnotationPolicyFailure(f"Requested scan path must remain inside the project root: {path}")
        if not path.exists():
            raise AnnotationPolicyFailure(f"Requested scan path does not exist: {path}")
        requested.append(path)
    selected: set[Path] = set()
    for candidate in repository_inventory(root):
        resolved = candidate.resolve()
        if any(resolved == path or (path.is_dir() and path in resolved.parents) for path in requested):
            selected.add(resolved)
    return sorted(selected)


def markdown_visible_lines(lines: list[str]) -> list[bool]:
    visible: list[bool] = []
    fence: str | None = None
    for line in lines:
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else "~~~" if stripped.startswith("~~~") else None
        if marker:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            visible.append(False)
            continue
        visible.append(fence is None)
    return visible


def comment_content(line: str, extension: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if extension in {".md", ".txt"}:
        if stripped.startswith("<!--"):
            stripped = stripped[4:].strip()
            if stripped.endswith("-->"):
                stripped = stripped[:-3].rstrip()
        return stripped
    markers = ["//"] if extension in {".js", ".jsx", ".ts", ".tsx"} else ["#"]
    if extension in {".cfg", ".conf", ".ini"}:
        markers.append(";")
    positions = [line.find(marker) for marker in markers if line.find(marker) >= 0]
    if not positions:
        return None
    position = min(positions)
    marker_length = 2 if line[position : position + 2] == "//" else 1
    return line[position + marker_length :].strip()


def add_finding(
    findings: list[Finding],
    code: str,
    path: str,
    line: int,
    message: str,
    annotation: str,
) -> None:
    findings.append(Finding(code, path, line, message, annotation))


def description_findings(
    findings: list[Finding],
    path: str,
    line: int,
    description: str,
    annotation: str,
) -> None:
    if not description:
        add_finding(findings, "empty-description", path, line, "Annotation description must not be empty.", annotation)
        return
    if not description.isascii():
        add_finding(findings, "non-ascii-annotation", path, line, "Annotation text must use ASCII.", annotation)
    if description[-1] not in ".?!":
        add_finding(
            findings,
            "description-punctuation",
            path,
            line,
            "Annotation description must end with terminal punctuation.",
            annotation,
        )


def continuation_fields(lines: list[str], index: int, extension: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for offset in (1, 2):
        if index + offset >= len(lines):
            break
        content = comment_content(lines[index + offset], extension)
        if content is None:
            break
        content = content.strip()
        if content.startswith("Issue: "):
            fields["issue"] = content.removeprefix("Issue: ").strip()
        elif content.startswith("Assignee: "):
            fields["assignee"] = content.removeprefix("Assignee: ").strip()
        else:
            break
    return fields


def validate_github_tracking(
    findings: list[Finding],
    path: str,
    line_number: int,
    owner: str,
    issue_number: str,
    description: str,
    annotation: str,
    fields: dict[str, str],
) -> None:
    handle: str | None = None
    if owner == "OWNER":
        add_finding(
            findings,
            "github-issue-owner",
            path,
            line_number,
            "A linked GitHub issue must use UNASSIGNED or its assigned public handle.",
            annotation,
        )
    elif owner == "UNASSIGNED":
        pass
    elif not GITHUB_HANDLE.fullmatch(owner):
        add_finding(
            findings,
            "invalid-github-handle",
            path,
            line_number,
            "GitHub owner must be an @-prefixed public handle.",
            annotation,
        )
    else:
        handle = owner[1:]
    description_findings(findings, path, line_number, description, annotation)
    issue_url = fields.get("issue")
    if issue_url is None:
        add_finding(
            findings,
            "missing-issue-url",
            path,
            line_number,
            "A GitHub-linked annotation requires an immediate Issue URL continuation.",
            annotation,
        )
    else:
        match = ISSUE_URL.fullmatch(issue_url)
        if not match or match.group("number") != issue_number:
            add_finding(
                findings,
                "issue-url-mismatch",
                path,
                line_number,
                "Issue URL must be a full GitHub issue URL with the same issue number.",
                annotation,
            )
    assignee_url = fields.get("assignee")
    if owner == "UNASSIGNED":
        if assignee_url is not None:
            add_finding(
                findings,
                "unexpected-assignee-url",
                path,
                line_number,
                "An UNASSIGNED GitHub issue must omit the Assignee continuation.",
                annotation,
            )
    elif handle is not None:
        if assignee_url is None:
            add_finding(
                findings,
                "missing-assignee-url",
                path,
                line_number,
                "An assigned GitHub issue requires an immediate Assignee profile continuation.",
                annotation,
            )
        else:
            match = ASSIGNEE_URL.fullmatch(assignee_url)
            if not match or match.group("handle").casefold() != handle.casefold():
                add_finding(
                    findings,
                    "assignee-url-mismatch",
                    path,
                    line_number,
                    "Assignee URL must match the annotation's public GitHub handle.",
                    annotation,
                )


def validate_text(path: str, text: str, policy: Policy) -> tuple[int, list[Finding]]:
    extension = Path(path).suffix.lower()
    lines = text.splitlines()
    visible = markdown_visible_lines(lines) if extension == ".md" else [True] * len(lines)
    prohibited = path_is_within(path, policy.prohibited_paths)
    findings: list[Finding] = []
    annotations = 0
    for index, source_line in enumerate(lines):
        if not visible[index]:
            continue
        content = comment_content(source_line, extension)
        if content is None:
            continue
        known_start = next((tag for tag in policy.tags if re.match(rf"^{re.escape(tag)}(?:\s|\(|:)", content)), None)
        full = FULL_ANNOTATION.fullmatch(content)
        if full is None:
            if known_start is not None:
                annotations += 1
                add_finding(
                    findings,
                    "malformed-format",
                    path,
                    index + 1,
                    "Annotation must use TAG (OWNER): concise explanation.",
                    content,
                )
            continue
        annotations += 1
        tag = full.group("tag")
        owner = full.group("owner")
        body = full.group("body")
        if tag not in policy.tags:
            add_finding(
                findings,
                "unsupported-tag",
                path,
                index + 1,
                f"Unsupported annotation tag: {tag}.",
                content,
            )
            continue
        if prohibited:
            add_finding(
                findings,
                "prohibited-location",
                path,
                index + 1,
                "Work annotations are prohibited in this reader-facing, generated, source, or artwork location.",
                content,
            )
            continue
        github = GITHUB_TRACKING.fullmatch(body)
        if github:
            validate_github_tracking(
                findings,
                path,
                index + 1,
                owner,
                github.group("number"),
                github.group("description"),
                content,
                continuation_fields(lines, index, extension),
            )
            continue
        if owner.startswith("@"):
            code = "invalid-github-handle" if not GITHUB_HANDLE.fullmatch(owner) else "github-owner-without-issue"
            message = (
                "GitHub owner must be a valid @-prefixed public handle."
                if code == "invalid-github-handle"
                else "A GitHub handle may appear only on an annotation linked to an existing issue."
            )
            add_finding(findings, code, path, index + 1, message, content)
        elif owner not in policy.local_owners:
            add_finding(
                findings,
                "invalid-owner",
                path,
                index + 1,
                "Local annotation owner must be OWNER or UNASSIGNED.",
                content,
            )
        if body.startswith("[GH-PENDING] - "):
            description = body.removeprefix("[GH-PENDING] - ")
        elif body.startswith("GH") or body.startswith("[GH"):
            add_finding(
                findings,
                "malformed-github-tracking",
                path,
                index + 1,
                "GitHub tracking must use [GH-PENDING] - or GH #number - syntax.",
                content,
            )
            description = body
        else:
            description = body
        description_findings(findings, path, index + 1, description, content)
    return annotations, findings


def load_fixture_data(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnnotationPolicyFailure(f"Unable to load annotation fixtures {path}: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"schema_version", "cases"} or data["schema_version"] != 1:
        raise AnnotationPolicyFailure("Annotation fixture registry must use the closed schema_version 1 shape.")
    cases = data["cases"]
    if not isinstance(cases, list) or not cases:
        raise AnnotationPolicyFailure("Annotation fixture cases must be a nonempty list.")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "path", "text", "expected_codes"}:
            raise AnnotationPolicyFailure("Each annotation fixture must use the closed case shape.")
        case_id = case["id"]
        if not isinstance(case_id, str) or not MACHINE_ID.fullmatch(case_id) or case_id in ids:
            raise AnnotationPolicyFailure(f"Invalid or duplicate annotation fixture id: {case_id}")
        ids.add(case_id)
        if not isinstance(case["path"], str) or not isinstance(case["text"], str):
            raise AnnotationPolicyFailure(f"Annotation fixture {case_id} requires string path and text values.")
        expected = case["expected_codes"]
        if not isinstance(expected, list) or not all(
            isinstance(code, str) and MACHINE_ID.fullmatch(code) for code in expected
        ):
            raise AnnotationPolicyFailure(f"Annotation fixture {case_id} expected_codes must be machine IDs.")
        if len(expected) != len(set(expected)):
            raise AnnotationPolicyFailure(f"Annotation fixture {case_id} contains duplicate expected codes.")
    return cases


def run_fixtures(path: Path, policy: Policy) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for case in load_fixture_data(path):
        _, findings = validate_text(case["path"], case["text"], policy)
        actual = sorted(finding.code for finding in findings)
        expected = sorted(case["expected_codes"])
        result = {"id": case["id"], "status": "passed" if actual == expected else "failed"}
        results.append(result)
        if actual != expected:
            failures.append({"id": case["id"], "expected_codes": expected, "actual_codes": actual})
    return results, failures


def scan_repository(root: Path, policy: Policy, requested: list[str]) -> tuple[int, int, list[Finding]]:
    inventory = requested_inventory(root, requested) if requested else repository_inventory(root)
    files_checked = 0
    annotations = 0
    findings: list[Finding] = []
    for path in inventory:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if path_is_within(relative, policy.excluded_paths) or path.suffix.lower() not in policy.scannable_extensions:
            continue
        try:
            if path.stat().st_size > policy.maximum_file_bytes:
                add_finding(
                    findings,
                    "file-size-limit",
                    relative,
                    0,
                    f"Eligible annotation surface exceeds {policy.maximum_file_bytes} bytes.",
                    "",
                )
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            add_finding(
                findings,
                "unreadable-text",
                relative,
                0,
                f"Unable to read eligible annotation surface as UTF-8: {exc}",
                "",
            )
            continue
        files_checked += 1
        file_annotations, file_findings = validate_text(relative, text, policy)
        annotations += file_annotations
        findings.extend(file_findings)
    return files_checked, annotations, findings


def render_human(payload: dict[str, Any]) -> None:
    print(
        f"Work annotations {payload['status']}: {payload['annotations']} annotations in "
        f"{payload['files_checked']} files; fixtures {payload['fixture_passed']}/{payload['fixture_cases']}."
    )
    for finding in payload["findings"]:
        location = f"{finding['path']}:{finding['line']}" if finding["line"] else finding["path"]
        print(f"- {location} [{finding['code']}] {finding['message']}")
    for failure in payload["fixture_failures"]:
        print(f"- fixture {failure['id']}: expected {failure['expected_codes']}, received {failure['actual_codes']}")


def main() -> int:
    args = parse_args()
    root = resolve_project_root(args.root, executable_path=__file__)
    policy = load_policy(resolve_config_path(args.policy, root))
    fixture_results, fixture_failures = run_fixtures(resolve_config_path(args.fixtures, root), policy)
    if args.fixtures_only:
        files_checked, annotations, findings = 0, 0, []
    else:
        files_checked, annotations, findings = scan_repository(root, policy, args.path)
    failed = bool(fixture_failures or findings)
    payload = {
        "schema_version": 1,
        "status": "failed" if failed else "passed",
        "files_checked": files_checked,
        "annotations": annotations,
        "finding_count": len(findings),
        "fixture_cases": len(fixture_results),
        "fixture_passed": sum(result["status"] == "passed" for result in fixture_results),
        "fixture_failures": fixture_failures,
        "findings": [finding.as_dict() for finding in findings],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        render_human(payload)
    return 1 if failed else 0


def cli() -> int:
    try:
        return main()
    except RuntimeError as exc:
        if "--json" in sys.argv:
            print(json.dumps({"schema_version": 1, "status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"Work annotations failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
