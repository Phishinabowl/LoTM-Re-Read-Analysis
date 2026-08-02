from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


TOOLS_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON_ROOT = TOOLS_ROOT / "Runtime" / "Python"
if str(RUNTIME_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PYTHON_ROOT))

from knowledge_framework.project_paths import resolve_project_root  # noqa: E402


REGISTRY_PATH = Path("Tools") / "Conformance" / "suites.json"
ROOT_KEYS = {"schema_version", "profiles", "suites", "discovery"}
SUITE_KEYS = {"id", "python", "powershell", "tags"}
DISCOVERY_KEYS = {"directory", "pattern", "exclude"}
STABLE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def require_mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Conformance registry `{context}` must be a mapping.")
    return value


def require_string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Conformance registry `{context}` must be a non-empty string.")
    return value.strip()


def require_string_list(value: object, context: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"Conformance registry `{context}` must be a string list.")
    return value


def require_keys(mapping: dict, allowed: set[str], context: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise ValueError(f"Conformance registry `{context}` has unsupported fields: {sorted(unknown)}")


def resolve_registered_path(root: Path, value: object, context: str) -> tuple[str, Path]:
    relative = Path(require_string(value, context))
    if relative.is_absolute():
        raise ValueError(f"Conformance registry `{context}` must be repository-relative.")
    resolved = (root / relative).resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError(f"Conformance registry `{context}` escapes the project root.")
    if not resolved.is_file():
        raise ValueError(f"Conformance runner does not exist: {relative.as_posix()}")
    return relative.as_posix(), resolved


def load_registry(root: Path) -> tuple[dict, dict[str, dict]]:
    path = root / REGISTRY_PATH
    registry = require_mapping(json.loads(path.read_text(encoding="utf-8")), "root")
    require_keys(registry, ROOT_KEYS, "root")
    if registry.get("schema_version") != 1:
        raise ValueError("Unsupported conformance registry schema_version.")

    raw_suites = registry.get("suites")
    if not isinstance(raw_suites, list) or not raw_suites:
        raise ValueError("Conformance registry `suites` must be a non-empty list.")
    suites: dict[str, dict] = {}
    runtime_paths = {"python": set(), "powershell": set()}
    for index, value in enumerate(raw_suites):
        suite = require_mapping(value, f"suites[{index}]")
        require_keys(suite, SUITE_KEYS, f"suites[{index}]")
        suite_id = require_string(suite.get("id"), f"suites[{index}].id")
        if not STABLE_ID.fullmatch(suite_id) or suite_id in suites:
            raise ValueError(f"Invalid or duplicate conformance suite ID: {suite_id}")
        normalized = {"id": suite_id, "tags": require_string_list(suite.get("tags"), f"{suite_id}.tags")}
        if len(normalized["tags"]) != len(set(normalized["tags"])):
            raise ValueError(f"Conformance suite `{suite_id}` contains duplicate tags.")
        for runtime in ("python", "powershell"):
            relative, resolved = resolve_registered_path(root, suite.get(runtime), f"{suite_id}.{runtime}")
            if relative in runtime_paths[runtime]:
                raise ValueError(f"Duplicate {runtime} conformance runner: {relative}")
            runtime_paths[runtime].add(relative)
            normalized[runtime] = relative
            normalized[f"{runtime}_path"] = resolved
        suites[suite_id] = normalized

    profiles = require_mapping(registry.get("profiles"), "profiles")
    for profile_id, suite_ids in profiles.items():
        if not STABLE_ID.fullmatch(profile_id):
            raise ValueError(f"Invalid conformance profile ID: {profile_id}")
        members = require_string_list(suite_ids, f"profiles.{profile_id}")
        if not members or len(members) != len(set(members)):
            raise ValueError(f"Conformance profile `{profile_id}` must contain unique suites.")
        unknown = set(members) - set(suites)
        if unknown:
            raise ValueError(f"Conformance profile `{profile_id}` references unknown suites: {sorted(unknown)}")

    validate_discovery(root, registry.get("discovery"), runtime_paths)
    return registry, suites


def validate_discovery(root: Path, value: object, runtime_paths: dict[str, set[str]]) -> None:
    discovery = require_mapping(value, "discovery")
    require_keys(discovery, {"python", "powershell"}, "discovery")
    for runtime in ("python", "powershell"):
        rules = discovery.get(runtime)
        if not isinstance(rules, list) or not rules:
            raise ValueError(f"Conformance registry `discovery.{runtime}` must be a non-empty list.")
        discovered: set[str] = set()
        excluded: set[str] = set()
        for index, value_rule in enumerate(rules):
            rule = require_mapping(value_rule, f"discovery.{runtime}[{index}]")
            require_keys(rule, DISCOVERY_KEYS, f"discovery.{runtime}[{index}]")
            directory = Path(require_string(rule.get("directory"), f"discovery.{runtime}[{index}].directory"))
            pattern = require_string(rule.get("pattern"), f"discovery.{runtime}[{index}].pattern")
            excluded.update(require_string_list(rule.get("exclude"), f"discovery.{runtime}[{index}].exclude"))
            source_dir = (root / directory).resolve()
            if root != source_dir and root not in source_dir.parents:
                raise ValueError(f"Conformance discovery directory escapes the project root: {directory}")
            discovered.update(path.relative_to(root).as_posix() for path in source_dir.glob(pattern) if path.is_file())
        unregistered = discovered - excluded - runtime_paths[runtime]
        stale_exclusions = excluded - discovered
        if unregistered:
            raise ValueError(f"Unregistered {runtime} conformance runners: {sorted(unregistered)}")
        if stale_exclusions:
            raise ValueError(f"Stale {runtime} conformance exclusions: {sorted(stale_exclusions)}")


def select_suites(args, registry: dict, suites: dict[str, dict]) -> tuple[str, list[dict]]:
    if args.suite:
        suite_ids = list(dict.fromkeys(args.suite))
        unknown = set(suite_ids) - set(suites)
        if unknown:
            raise ValueError(f"Unknown conformance suite(s): {sorted(unknown)}")
        return "selected", [suites[suite_id] for suite_id in suite_ids]
    profiles = registry["profiles"]
    if args.profile not in profiles:
        raise ValueError(f"Unknown conformance profile `{args.profile}`; choose from {sorted(profiles)}")
    return args.profile, [suites[suite_id] for suite_id in profiles[args.profile]]


def parse_child_summary(stdout: str, suite_id: str) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Conformance suite `{suite_id}` emitted no JSON summary.")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise ValueError(f"Conformance suite `{suite_id}` summary must be a JSON object.")
    return value


def run_suite(root: Path, suite: dict) -> dict:
    command = [sys.executable, str(suite["python_path"]), "--root", str(root), "--json"]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8", check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return {"id": suite["id"], "status": "failed", "error": detail or "Runner exited without output."}
    try:
        summary = parse_child_summary(completed.stdout, suite["id"])
    except (ValueError, json.JSONDecodeError) as exc:
        return {"id": suite["id"], "status": "failed", "error": str(exc)}
    return {"id": suite["id"], "status": "passed", "summary": summary}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run registered Python framework conformance suites.")
    parser.add_argument("--root", help="Project root; auto-detected when omitted.")
    parser.add_argument("--profile", default="baseline", help="Registered profile to run (default: baseline).")
    parser.add_argument("--suite", action="append", help="Run one registered suite; repeat for multiple suites.")
    parser.add_argument("--list", action="store_true", help="List registered profiles and suites without running them.")
    parser.add_argument("--json", action="store_true", help="Emit a stable JSON summary.")
    args = parser.parse_args()

    root = resolve_project_root(args.root, executable_path=__file__)
    registry, suites = load_registry(root)
    if args.list:
        listing = {"schema_version": 1, "profiles": registry["profiles"], "suites": list(suites)}
        print(
            json.dumps(listing, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(listing, indent=2)
        )
        return 0

    profile, selected = select_suites(args, registry, suites)
    results = []
    for suite in selected:
        if not args.json:
            print(f"RUN: {suite['id']}")
        result = run_suite(root, suite)
        results.append(result)
        if not args.json:
            print(f"{result['status'].upper()}: {suite['id']}")

    failed = sum(result["status"] == "failed" for result in results)
    summary = {
        "schema_version": 1,
        "profile": profile,
        "suite_count": len(results),
        "passed": len(results) - failed,
        "failed": failed,
        "suites": results,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Conformance {profile}: {summary['passed']} passed, {summary['failed']} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
