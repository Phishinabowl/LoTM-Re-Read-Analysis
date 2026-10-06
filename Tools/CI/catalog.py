"""Strict CI catalog loading and deterministic planning; never launches children."""

import copy
import hashlib
import json
from pathlib import Path
import re

ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
RUNTIMES = ["python", "powershell7"]
REGRESSION_UNITS = (
    "implementation/python-native-results::python",
    "implementation/ci-catalog::python",
    "implementation/ci-scope::python",
    "implementation/ci-process::python",
    "implementation/ci-execution::python",
)
OPERATING_SYSTEMS = {"windows", "linux", "macos"}
BUDGET_KEYS = {"total_seconds", "termination_seconds", "cleanup_seconds", "finalization_seconds"}
RECORD_KEYS = set(
    (
        "id description order adapter runtimes os entry arguments fixtures impact_paths depends_on "
        "deadline_seconds result_contract empty_policy allowed_skips"
    ).split()
)
EXTERNAL_KEYS = set("unit fixtures impact_paths deadline_seconds depends_on result_contract".split())
REFERENCE_KEYS = {"owner", "profile", "ids", "runtimes", "blocking"}
ADAPTERS = {
    "ruff": ("python", "ruff-v1"),
    "powershell-format": ("powershell7", "powershell-format-v1"),
    "work-annotations": ("python", "work-annotations-v1"),
    "actionlint": ("python", "actionlint-v1"),
    "pytest": ("python", "native-test-run-v1"),
    "pester": ("powershell7", "native-test-run-v1"),
    "installed-artifact": ("python", "installed-package-v1"),
}
FILES = {
    "policy": "policy-validators.json",
    "implementation": "implementation-tests.json",
    "profiles": "execution-profiles.json",
    "metadata": "coverage-metadata.json",
}


class CatalogError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CatalogError(message)


def closed(value, keys, context):
    require(isinstance(value, dict) and set(value) == keys, f"{context}: require exact fields {sorted(keys)}")


def integer(value, minimum, context):
    require(type(value) is int and value >= minimum, f"{context}: require integer >= {minimum}")


def text(value, context):
    require(isinstance(value, str) and bool(value.strip()), f"{context}: require nonempty text")


def strings(value, context, nonempty=False):
    require(isinstance(value, list), f"{context}: require list")
    if nonempty:
        require(bool(value), f"{context}: require nonempty list")
    for item in value:
        text(item, context)
    require(len(value) == len(set(value)), f"{context}: duplicate values")


def machine(value):
    require(isinstance(value, str) and ID.fullmatch(value), f"Invalid machine ID: {value}")


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CatalogError(f"Cannot read catalog {path}: {error}") from error


def path_value(value, pattern=False):
    text(value, "path")
    require("\\" not in value and not value.startswith("/") and ":" not in value, f"Unsafe relative path: {value}")
    require(all(part not in ("", "..") for part in value.split("/")), f"Unsafe relative path: {value}")
    if not pattern:
        require(not any(char in value for char in "*?[]"), f"Literal path required: {value}")
    else:
        require(not any(char in value for char in "[]!"), "Unsupported impact/discovery glob grammar")
        require(
            all("**" not in part or part == "**" for part in value.split("/")), "Globstar must occupy a whole segment"
        )


def owned_path(root, value, file=False):
    path_value(value)
    target = (root / value).resolve()
    require(target.is_relative_to(root), f"Path escapes root: {value}")
    require(target.is_file() if file else target.exists(), f"Missing registered path: {value}")
    return target


def patterns(values, context):
    strings(values, context)
    for value in values:
        path_value(value, pattern=True)


def ordered(records, context):
    require(isinstance(records, list) and bool(records), f"{context}: empty records")
    ids, orders = set(), set()
    for record in records:
        require(isinstance(record, dict), f"{context}: require record")
        machine(record.get("id"))
        integer(record.get("order"), 0, context)
        require(record["id"] not in ids and record["order"] not in orders, f"{context}: duplicate ID/order")
        ids.add(record["id"])
        orders.add(record["order"])
    return sorted(records, key=lambda row: row["order"])


def budget(value):
    closed(value, BUDGET_KEYS, "budget")
    for key, number in value.items():
        integer(number, 1, key)
    reserves = sum(value[key] for key in BUDGET_KEYS - {"total_seconds"})
    require(value["total_seconds"] > reserves, "Budget leaves no launch window")
    return value["total_seconds"] - reserves


def topological(items, edges):
    require(set(edges) == set(items), "Dependency inventory mismatch")
    for dependencies in edges.values():
        require(set(dependencies) <= set(items), "Unknown dependency")
    result = []
    remaining = list(items)
    while remaining:
        ready = next((item for item in remaining if set(edges[item]) <= set(result)), None)
        require(ready is not None, "Dependency cycle")
        result.append(ready)
        remaining.remove(ready)
    return result


def discovery(root, records, entries):
    require(isinstance(records, list) and bool(records), "Discovery must be nonempty")
    discovered, excluded = set(), set()
    for record in records:
        closed(record, {"directory", "pattern", "exclude"}, "discovery")
        directory = owned_path(root, record["directory"])
        require(directory.is_dir(), "Discovery directory required")
        path_value(record["pattern"], pattern=True)
        found = set()
        for path in directory.glob(record["pattern"]):
            if path.is_file():
                require(path.resolve().is_relative_to(root), "Discovery link escape")
                found.add(path.relative_to(root).as_posix())
        require(not discovered.intersection(found), "Overlapping discovery rules")
        discovered.update(found)
        require(isinstance(record["exclude"], list), "Invalid discovery exclusions")
        for exclusion in record["exclude"]:
            closed(exclusion, {"path", "reason", "decision"}, "exclusion")
            text(exclusion["reason"], "exclusion reason")
            text(exclusion["decision"], "exclusion decision")
            require(exclusion["path"] in found and exclusion["path"] not in excluded, "Stale/duplicate exclusion")
            excluded.add(exclusion["path"])
    require(
        discovered - excluded == entries,
        f"Discovery registration mismatch: {sorted((discovered - excluded) ^ entries)}",
    )


def external_fields(root, row):
    strings(row["fixtures"], "fixtures")
    for fixture in row["fixtures"]:
        owned_path(root, fixture)
    patterns(row["impact_paths"], "impact paths")
    strings(row["depends_on"], "dependencies")
    integer(row["deadline_seconds"], 1, "deadline")


class Catalog:
    def __init__(self, root, directory=None):
        self.root = Path(root).resolve()
        directory = self.root / Path(directory) if directory else self.root / "Tools/CI/Data"
        require(directory.resolve().is_relative_to(self.root), "Catalog directory escapes root")
        self.documents = {key: read_json(directory / name) for key, name in FILES.items()}
        self.sources = {key: directory / name for key, name in FILES.items()}
        self.units = {}
        self.owner_profiles = {}
        self.profiles = {}
        self.shard_plans = {}
        try:
            self._owned_catalog("policy", "validators")
            self._owned_catalog("implementation", "groups")
            self._external_catalogs()
            self._metadata()
            self._profiles()
            self._shards()
        except (TypeError, KeyError, AttributeError, ValueError, RuntimeError, OSError) as error:
            raise CatalogError(str(error)) from error
        for identity, row in self.units.items():
            for index, entry in enumerate(row["entry"]):
                self.sources[f"entry-{identity}-{index}"] = self.root / entry
        self.sources["catalog-code"] = self.root / "Tools/CI/catalog.py"
        self.sources["planner-code"] = self.root / "Tools/CI/plan_ci.py"
        if "implementation/ci-scope" in self.units:
            for script in ("scope.py", "selection.py", "explain_ci.py"):
                self.sources["scope-code-" + script] = self.root / "Tools/CI" / script
        if "implementation/ci-process" in self.units:
            for script in ("process_supervisor.py", "windows_process.py"):
                self.sources["process-code-" + script] = self.root / "Tools/CI" / script
        if "implementation/ci-execution" in self.units:
            for script in (
                "run_ci.py",
                "aggregate_execution.py",
                "layer_adapters.py",
                "adapter_worker.py",
                "Invoke-CiAdapter.ps1",
                "execution_reports.py",
                "report_ci.py",
            ):
                self.sources["execution-code-" + script] = self.root / "Tools/CI" / script
        self.source_digests = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.sources.values(), key=lambda value: value.relative_to(self.root).as_posix())
        }
        self.runtime_versions = read_json(self.root / "Tools/CI/Data/runtime-versions.json")

    def _owned_catalog(self, owner, key):
        document = self.documents[owner]
        closed(document, {"schema_version", key, "discovery"}, owner)
        require(
            type(document["schema_version"]) is int and document["schema_version"] == 1, "Unsupported catalog version"
        )
        entries = set()
        resolved_entries = set()
        for row in ordered(document[key], owner):
            closed(row, RECORD_KEYS, owner)
            text(row["description"], "description")
            require(row["adapter"] in ADAPTERS, "Unknown adapter")
            runtime, contract = ADAPTERS[row["adapter"]]
            require(
                row["runtimes"] == [runtime] and row["result_contract"] == contract, "Adapter runtime/result mismatch"
            )
            require(
                row["adapter"]
                in (
                    {"pytest", "pester", "installed-artifact"}
                    if owner == "implementation"
                    else {"ruff", "powershell-format", "work-annotations", "actionlint"}
                ),
                "Wrong adapter owner",
            )
            strings(row["os"], "OS", True)
            require(set(row["os"]) <= OPERATING_SYSTEMS, "Unknown OS")
            strings(row["entry"], "entries", True)
            require(
                row["adapter"] in ("pytest", "pester") or len(row["entry"]) == 1, "Validator entry must be singular"
            )
            for entry in row["entry"]:
                target = owned_path(self.root, entry, file=True)
                require(target not in resolved_entries, "Multiply owned resolved entry")
                resolved_entries.add(target)
                require(entry not in entries, "Multiply owned entry")
                if row["adapter"] in ("pytest", "pester"):
                    prefix = "Tools/Tests/Python/" if runtime == "python" else "Tools/Tests/PowerShell/"
                    require(
                        entry.startswith(prefix) and entry.endswith(".py" if runtime == "python" else ".Tests.ps1"),
                        "Wrong native file/root",
                    )
                    require(target.is_relative_to(self.root / prefix), "Native file resolves outside native root")
                entries.add(entry)
            require(row["arguments"] == [], "Initial adapters accept no catalog argument overrides")
            require(row["empty_policy"] == "fail" and row["allowed_skips"] == [], "No empty/skip exemption adopted")
            external_fields(self.root, row)
            self.units[f"{owner}/{row['id']}"] = {**row, "owner": owner}
        discovery(self.root, document["discovery"], entries)

    def _external_catalogs(self):
        # Load the existing owners' strict validators without executing domain suites.
        import importlib.util
        import sys

        for owner, path, loader, key in [
            ("conformance", "Tools/Conformance/run_conformance.py", "load_registry", "suites"),
            ("compatibility", "Tools/Compatibility/run_compatibility.py", "load_registry", "checks"),
        ]:
            before = sys.path[:]
            bytecode = sys.dont_write_bytecode
            try:
                sys.dont_write_bytecode = True
                spec = importlib.util.spec_from_file_location("ci_catalog_" + owner, self.root / path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                registry_path = (
                    self.root
                    / f"Tools/{owner.title()}/"
                    / ("suites.json" if owner == "conformance" else "compatibility.json")
                )
                original = read_json(registry_path)
                require(type(original.get("schema_version")) is int, "Boolean external version rejected")
                registry = (
                    getattr(module, loader)(self.root)
                    if owner == "conformance"
                    else getattr(module, loader)(registry_path)
                )
                if owner == "conformance":
                    registry = registry[0]
            finally:
                sys.path[:] = before
                sys.dont_write_bytecode = bytecode
            self.sources[owner] = registry_path
            self.owner_profiles[owner] = registry["profiles"]
            for index, row in enumerate(registry[key]):
                unit = f"{owner}/{row['id']}"
                self.units[unit] = {
                    "id": row["id"],
                    "owner": owner,
                    "order": index,
                    "description": unit,
                    "adapter": owner,
                    "runtimes": RUNTIMES if owner == "conformance" else ["referee"],
                    "participants": RUNTIMES if owner == "compatibility" else [],
                    "os": ["windows", "linux"] if owner == "conformance" else ["windows"],
                    "entry": [row["python"], row["powershell"]] if owner == "conformance" else [path],
                }

    def reference(self, row):
        closed(row, REFERENCE_KEYS, "reference")
        require(row["owner"] in ("policy", "implementation", "conformance", "compatibility", "parity"), "Unknown owner")
        require(row["blocking"] is True, "Required coverage cannot become observational")
        require((row["profile"] is None) != (row["ids"] is None), "Require exactly profile or IDs")
        if row["profile"] is not None:
            require(
                row["owner"] in self.owner_profiles and row["profile"] in self.owner_profiles[row["owner"]],
                "Unknown owner profile",
            )
            ids = self.owner_profiles[row["owner"]][row["profile"]]
        else:
            strings(row["ids"], "reference IDs", True)
            ids = row["ids"]
            require(all(f"{row['owner']}/{identity}" in self.units for identity in ids), "Unknown reference ID")
            ids = sorted(ids, key=lambda identity: self.units[f"{row['owner']}/{identity}"]["order"])
        strings(row["runtimes"], "reference runtimes", True)
        require(set(row["runtimes"]) <= set(RUNTIMES), "Unsupported reference runtime")
        result = []
        for identity in ids:
            unit = f"{row['owner']}/{identity}"
            require(unit in self.units, f"Unknown unit: {unit}")
            descriptor = self.units[unit]
            if row["owner"] in ("compatibility", "parity"):
                require(row["runtimes"] == descriptor["participants"], "Incomplete referee runtime set")
                result.append(unit + "::referee")
            else:
                require(set(row["runtimes"]) <= set(descriptor["runtimes"]), "Unavailable runtime variant")
                result.extend(unit + "::" + runtime for runtime in RUNTIMES if runtime in row["runtimes"])
        return result

    def _metadata(self):
        document = self.documents["metadata"]
        closed(
            document,
            {
                "schema_version",
                "external_units",
                "comparisons",
                "dependencies",
                "full_selection_paths",
                "non_impact_paths",
            },
            "metadata",
        )
        require(
            type(document["schema_version"]) is int and document["schema_version"] == 1, "Unsupported metadata version"
        )
        require(isinstance(document["external_units"], list), "External metadata list required")
        expected = {key for key, row in self.units.items() if row["owner"] in self.owner_profiles}
        seen = set()
        for row in document["external_units"]:
            closed(row, EXTERNAL_KEYS, "external metadata")
            require(row["unit"] in expected and row["unit"] not in seen, "Unknown/duplicate external metadata")
            require(
                row["result_contract"]
                == (
                    "conformance-detailed-v1" if row["unit"].startswith("conformance/") else "compatibility-detailed-v3"
                ),
                "External result contract mismatch",
            )
            external_fields(self.root, row)
            self.units[row["unit"]].update(row)
            seen.add(row["unit"])
        require(seen == expected, "Missing execution metadata")
        for row in ordered(document["comparisons"], "comparisons"):
            closed(
                row,
                EXTERNAL_KEYS | {"id", "description", "order", "source_reference", "runtimes", "normalization"},
                "comparison",
            )
            require(row["unit"] == "parity/" + row["id"] and row["unit"] not in self.units, "Invalid parity identity")
            require(
                row["runtimes"] == RUNTIMES
                and row["normalization"] == "conformance-semantic-v1"
                and row["result_contract"] == "parity-v1",
                "Unsupported parity contract",
            )
            text(row["description"], "comparison description")
            external_fields(self.root, row)
            require(row["source_reference"]["owner"] == "conformance", "Parity source owner unsupported")
            sources = self.reference(row["source_reference"])
            require(row["source_reference"]["runtimes"] == row["runtimes"], "Parity source runtime mismatch")
            self.units[row["unit"]] = {
                **row,
                "owner": "parity",
                "adapter": "parity",
                "participants": row["runtimes"],
                "runtimes": ["referee"],
                "os": ["windows", "linux"],
                "entry": [],
                "source_units": sources,
            }
        for key, keys in [
            ("full_selection_paths", {"pattern", "reason"}),
            ("non_impact_paths", {"pattern", "reason", "decision"}),
        ]:
            require(isinstance(document[key], list), "Invalid path rules")
            seen_patterns = set()
            for rule in document[key]:
                closed(rule, keys, "path rule")
                path_value(rule["pattern"], pattern=True)
                require(rule["pattern"] not in seen_patterns, "Duplicate path rule")
                seen_patterns.add(rule["pattern"])
                for field in keys - {"pattern"}:
                    text(rule[field], field)
        # No non-impact exemption is adopted until selector proof. Reject ambiguous exemptions now.
        require(document["non_impact_paths"] == [], "Non-impact rules require later selector adoption")
        shared = {row["pattern"] for row in document["full_selection_paths"]}
        impact_edges = {unit: [] for unit in self.units}
        require(isinstance(document["dependencies"], list), "Invalid impact dependencies")
        seen_sources = set()
        for edge in document["dependencies"]:
            closed(edge, {"source", "consumers", "reason"}, "impact edge")
            require(edge["source"] in self.units or edge["source"] in shared, "Unknown impact source")
            require(edge["source"] not in seen_sources, "Duplicate impact source")
            seen_sources.add(edge["source"])
            text(edge["reason"], "impact reason")
            strings(edge["consumers"], "impact consumers", True)
            require(set(edge["consumers"]) <= set(self.units), "Unknown impact consumer")
            if edge["source"] in self.units:
                impact_edges[edge["source"]] = edge["consumers"]
        topological(list(self.units), impact_edges)
        execution_edges = {unit: row["depends_on"] for unit, row in self.units.items()}
        for unit, row in self.units.items():
            if row["owner"] == "parity":
                execution_edges[unit] = list(
                    dict.fromkeys(execution_edges[unit] + [value.split("::")[0] for value in row["source_units"]])
                )
        topological(list(self.units), execution_edges)

    def _profiles(self):
        document = self.documents["profiles"]
        require(
            all(identity.split("::")[0] in self.units for identity in REGRESSION_UNITS),
            "Mandatory infrastructure regression registration missing",
        )
        for identity in REGRESSION_UNITS:
            unit = self.units[identity.split("::")[0]]
            require(
                unit["adapter"] == "pytest"
                and unit["runtimes"] == ["python"]
                and {"windows", "linux"} <= set(unit["os"]),
                "Mandatory regression must support Windows/Linux Python",
            )
        mandatory_entries = {
            name for identity in REGRESSION_UNITS for name in self.units[identity.split("::")[0]]["entry"]
        }
        require(
            all(
                path.relative_to(self.root).as_posix() in mandatory_entries
                for path in (self.root / "Tools/Tests/Python").glob("test_ci_*.py")
            ),
            "CI regression entry belongs to a nonmandatory group",
        )
        closed(document, {"schema_version", "runtime_order", "profiles", "shard_plans"}, "profiles catalog")
        require(
            type(document["schema_version"]) is int
            and document["schema_version"] == 1
            and document["runtime_order"] == RUNTIMES,
            "Invalid profile version/runtime order",
        )
        require(isinstance(document["profiles"], list) and document["profiles"], "Profiles required")
        methodology = (self.root / "Framework/testing_methodology.md").read_text(encoding="utf-8")
        families = set(re.findall(r"^\| `(PRESSURE-[A-Z0-9-]+|SCENARIO-[A-Z0-9-]+)`", methodology, re.M))
        for profile in document["profiles"]:
            closed(
                profile,
                set("id description references always_run selection execution_policy budget required_reviews".split()),
                "profile",
            )
            machine(profile["id"])
            require(profile["id"] not in self.profiles, "Duplicate profile ID")
            text(profile["description"], "profile description")
            require(profile["selection"] == "full", "Affected selection not adopted")
            closed(
                profile["execution_policy"],
                {"continue_independent", "parallelism", "canonical_guard", "environment"},
                "execution policy",
            )
            require(
                profile["execution_policy"]
                == {
                    "continue_independent": True,
                    "parallelism": 1,
                    "canonical_guard": "canonical-v1",
                    "environment": "owned-v1",
                },
                "Unsupported execution policy",
            )
            require(type(profile["execution_policy"]["parallelism"]) is int, "Boolean parallelism rejected")
            require(isinstance(profile["references"], list) and profile["references"], "Profile references required")
            execution = [unit for reference in profile["references"] for unit in self.reference(reference)]
            require(len(execution) == len(set(execution)), "Duplicate expanded references")
            edges = {identity: [] for identity in execution}
            for identity in execution:
                row = self.units[identity.split("::")[0]]
                for dependency in row["depends_on"]:
                    required = [dependency + "::" + runtime for runtime in self.units[dependency]["runtimes"]]
                    require(set(required) <= set(execution), "Prerequisite missing from profile closure")
                    edges[identity].extend(required)
                if row["owner"] == "parity":
                    require(set(row["source_units"]) <= set(execution), "Parity source missing from profile")
                    edges[identity].extend(row["source_units"])
            execution = topological(execution, edges)
            strings(profile["always_run"], "always-run", True)
            require(set(profile["always_run"]) <= set(execution), "Unknown always-run obligation")
            if any(unit.startswith("implementation/") for unit in execution):
                require(
                    set(REGRESSION_UNITS) <= set(profile["always_run"]),
                    "Catalog/scope/process/aggregate/native regression must always run",
                )
            allocation = sum(self.units[unit.split("::")[0]]["deadline_seconds"] for unit in execution)
            window = budget(profile["budget"])
            require(allocation <= window, f"Profile {profile['id']}: deadline allocation {allocation} exceeds {window}")
            require(isinstance(profile["required_reviews"], list), "Invalid review inventory")
            seen = set()
            for review in profile["required_reviews"]:
                closed(review, {"family", "blocking", "evidence"}, "required review")
                require(
                    review["family"] not in seen and review["family"] in families,
                    "Unknown/duplicate methodology review",
                )
                seen.add(review["family"])
                require(
                    review["blocking"] is True and review["evidence"] is None,
                    "Reviewed evidence adoption not implemented",
                )
            self.profiles[profile["id"]] = {**profile, "execution": execution, "dependencies": edges}
            if profile["id"] == "release-readiness":
                require(seen == families and bool(seen), "Release readiness omits retained methodology review")
            if profile["id"] in {
                "feature-feedback",
                "pr-integration",
                "full-verification",
                "release-readiness",
                "modernization-shadow",
            }:
                native = {
                    key + "::" + runtime
                    for key, unit in self.units.items()
                    if unit["owner"] == "implementation"
                    for runtime in unit["runtimes"]
                }
                require(native <= set(execution), "Gating profile omits approved implementation group")
                require(
                    {
                        "policy/ruff::python",
                        "policy/powershell-format::powershell7",
                        "policy/work-annotations::python",
                        "policy/actionlint::python",
                    }
                    <= set(execution),
                    "Gating profile omits required policy",
                )
            if profile["id"] in {"pr-integration", "full-verification", "release-readiness", "modernization-shadow"}:
                require(
                    set(
                        self.reference(
                            {
                                "owner": "conformance",
                                "profile": "baseline",
                                "ids": None,
                                "runtimes": RUNTIMES,
                                "blocking": True,
                            }
                        )
                    )
                    <= set(execution),
                    "Gating profile omits baseline semantics",
                )
                require(any(unit.startswith("parity/") for unit in execution), "Gating profile omits parity")

        require(
            "ci-infrastructure" in self.profiles
            and self.profiles["ci-infrastructure"]["execution"] == list(REGRESSION_UNITS),
            "Focused infrastructure profile must contain the exact mandatory regression set",
        )

    def _shards(self):
        plans = self.documents["profiles"]["shard_plans"]
        require(isinstance(plans, list) and plans, "Shard plans required")
        for plan in plans:
            closed(plan, {"id", "profile", "shards", "gates", "aggregate_gate"}, "shard plan")
            machine(plan["id"])
            require(
                plan["id"] not in self.shard_plans and plan["profile"] in self.profiles, "Unknown/duplicate shard plan"
            )
            profile = self.profiles[plan["profile"]]
            shards = ordered(plan["shards"], "shards")
            placements, by_id, edges = {}, {}, {}
            for shard in shards:
                closed(shard, {"id", "order", "units", "depends_on", "os", "budget"}, "shard")
                strings(shard["units"], "shard units", True)
                require(
                    shard["units"] == [unit for unit in profile["execution"] if unit in shard["units"]],
                    "Shard must preserve canonical result order",
                )
                strings(shard["depends_on"], "shard dependencies")
                require(shard["os"] in OPERATING_SYSTEMS, "Unsupported shard OS")
                require(set(shard["units"]) <= set(profile["execution"]), "Foreign shard units")
                allocation = 0
                for unit in shard["units"]:
                    require(unit not in placements, "Duplicate shard placement")
                    row = self.units[unit.split("::")[0]]
                    require(shard["os"] in row["os"], "Incompatible shard OS")
                    placements[unit] = shard["id"]
                    allocation += row["deadline_seconds"]
                window = budget(shard["budget"])
                require(allocation <= window and allocation <= 2190, "Shard admission exceeds execution window")
                require(
                    shard["budget"]["total_seconds"] + 600 + 180 + 120 <= 3300, "Shard exceeds provisional host ceiling"
                )
                by_id[shard["id"]] = shard
                edges[shard["id"]] = shard["depends_on"]
            require(set(placements) == set(profile["execution"]), "Incomplete shard union")
            topological(list(by_id), edges)

            def ancestors(identity):
                result = set()
                pending = list(edges[identity])
                while pending:
                    value = pending.pop()
                    if value not in result:
                        result.add(value)
                        pending.extend(edges[value])
                return result

            for unit, prerequisites in profile["dependencies"].items():
                owner = placements[unit]
                for dependency in prerequisites:
                    source = placements[dependency]
                    require(
                        source in ancestors(owner)
                        if source != owner
                        else by_id[owner]["units"].index(dependency) < by_id[owner]["units"].index(unit),
                        "Shard dependency/order mismatch",
                    )
            require(isinstance(plan["gates"], list) and plan["gates"], "Gates required")
            gates, names = {}, set()
            for gate in plan["gates"]:
                closed(gate, {"id", "check_name", "units", "source_shards", "budget"}, "gate")
                machine(gate["id"])
                text(gate["check_name"], "check name")
                require(gate["id"] not in gates and gate["check_name"] not in names, "Duplicate gate identity/name")
                strings(gate["units"], "gate units", True)
                require(
                    gate["units"] == [unit for unit in profile["execution"] if unit in gate["units"]],
                    "Gate must preserve canonical result order",
                )
                strings(gate["source_shards"], "source shards", True)
                require(set(gate["source_shards"]) <= set(by_id), "Unknown gate source shard")
                require(set(gate["units"]) <= set(profile["execution"]), "Foreign gate unit")
                require(
                    {placements[unit] for unit in gate["units"]} == set(gate["source_shards"]),
                    "Gate source projection mismatch",
                )
                require(
                    budget(gate["budget"]) >= 120 and gate["budget"]["total_seconds"] + 900 <= 3300,
                    "Gate budget not admitted",
                )
                gates[gate["id"]] = gate
                names.add(gate["check_name"])
            require(
                plan["aggregate_gate"] in gates
                and set(gates[plan["aggregate_gate"]]["units"]) == set(profile["execution"]),
                "Aggregate gate must cover complete profile",
            )
            self.shard_plans[plan["id"]] = copy.deepcopy(plan)

    def plan(self, profile_id, os_name=None, available=None, shard_plan=None):
        require(profile_id in self.profiles, "Unknown execution profile")
        require(os_name is None or os_name in OPERATING_SYSTEMS, "Unknown requested OS")
        require(available is None or set(available) <= set(RUNTIMES), "Unsupported available runtime")
        if available is not None:
            strings(available, "available runtime assumptions")
        profile = self.profiles[profile_id]
        rows = []
        for identity in profile["execution"]:
            logical, runtime = identity.split("::")
            unit = self.units[logical]
            required = unit.get("participants", []) if runtime == "referee" else [runtime]
            reasons = []
            if os_name is not None and os_name not in unit["os"]:
                reasons.append("required OS unavailable")
            if available is not None and not set(required) <= set(available):
                reasons.append("required runtime unavailable")
            rows.append(
                {
                    "execution_id": identity,
                    "adapter": unit["adapter"],
                    "entry": [unit["entry"][RUNTIMES.index(runtime)]]
                    if unit["owner"] == "conformance"
                    else unit["entry"],
                    "fixtures": unit["fixtures"],
                    "impact_paths": unit["impact_paths"],
                    "unbounded_impact": not bool(unit["impact_paths"]),
                    "result_contract": unit["result_contract"],
                    "runtimes": required,
                    "os": unit["os"],
                    "deadline_seconds": unit["deadline_seconds"],
                    "depends_on": profile["dependencies"][identity],
                    "availability": "blocked" if reasons else "unverified" if available is None else "declared",
                    "reasons": reasons,
                }
            )
        selected_shard = None
        if shard_plan:
            require(
                shard_plan in self.shard_plans and self.shard_plans[shard_plan]["profile"] == profile_id,
                "Wrong shard plan/profile",
            )
            selected_shard = self.shard_plans[shard_plan]
        return copy.deepcopy(
            {
                "contract": "ci-execution-plan",
                "contract_version": 1,
                "status": "planned",
                "profile": profile_id,
                "selection": "full",
                "source_digests": self.source_digests,
                "runtime_assumptions_verified": False,
                "prerequisites": {
                    "runtime_versions": self.runtime_versions,
                    "native_dependencies": {"pytest": "9.1.1", "Pester": "6.2.0"},
                    "verification": "Required execution preflight; no imports/probes/installations during planning",
                },
                "budget": profile["budget"],
                "deadline_sum_seconds": sum(row["deadline_seconds"] for row in rows),
                "always_run": profile["always_run"],
                "required_reviews": profile["required_reviews"],
                "units": rows,
                "shard_plan": selected_shard,
                "execution_ready": False,
                "rollout_blockers": [
                    "Phase 4.4 local execution exists; hosted adoption remains gated",
                    "Phase 4.5 local reports exist; hosted publication remains gated",
                ]
                + (
                    ["Phase 5 required synthetic media and complete parity proof"]
                    if profile_id
                    in {"pr-integration", "full-verification", "release-readiness", "modernization-shadow"}
                    else []
                ),
            }
        )

    def expected_manifest(self, plan_id, shard_id, snapshot_digest):
        current = {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.sources.values()
        }
        require(current == self.source_digests, "Source changed since planning")
        require(plan_id in self.shard_plans, "Unknown shard plan")
        require(
            isinstance(snapshot_digest, str) and re.fullmatch("[0-9a-f]{64}", snapshot_digest),
            "Captured snapshot digest required",
        )
        plan = self.shard_plans[plan_id]
        shards = {row["id"]: row for row in plan["shards"]}
        require(shard_id in shards, "Unknown manifest shard")
        return copy.deepcopy(
            {
                "contract": "ci-shard-source",
                "contract_version": 1,
                "shard_plan": plan_id,
                "profile": plan["profile"],
                "shard": shard_id,
                "snapshot_digest": snapshot_digest,
                "source_digests": self.source_digests,
                "units": shards[shard_id]["units"],
            }
        )

    def validate_manifests(self, plan_id, manifests, snapshot_digest):
        require(plan_id in self.shard_plans and isinstance(manifests, list), "Invalid source manifest inventory")
        plan = self.shard_plans[plan_id]
        seen = set()
        for manifest in manifests:
            closed(
                manifest,
                {
                    "contract",
                    "contract_version",
                    "shard_plan",
                    "profile",
                    "shard",
                    "snapshot_digest",
                    "source_digests",
                    "units",
                },
                "source manifest",
            )
            require(type(manifest["contract_version"]) is int, "Boolean manifest version rejected")
            require(manifest["shard"] not in seen, "Duplicate source manifest")
            expected = self.expected_manifest(plan_id, manifest["shard"], snapshot_digest)
            require(manifest == expected, "Stale/foreign/incomplete source manifest")
            seen.add(manifest["shard"])
        require(seen == {row["id"] for row in plan["shards"]}, "Missing source manifests")
        return copy.deepcopy(
            [
                {"gate": gate["id"], "units": gate["units"], "source_shards": gate["source_shards"]}
                for gate in plan["gates"]
            ]
        )
