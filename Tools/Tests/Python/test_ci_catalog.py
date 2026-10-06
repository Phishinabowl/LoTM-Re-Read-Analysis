"""Catalog ownership, closed contracts, deterministic plans and fail-closed admission."""

import copy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    catalogs = importlib.import_module("catalog")
finally:
    sys.path[:] = before


@pytest.fixture
def private_catalog(tmp_path):
    # Private source/registry tree. Nothing changes real registration or canonical sources.
    root = tmp_path / "repo"
    data = root / "Tools/CI/Data"
    data.mkdir(parents=True)
    for filename in catalogs.FILES.values():
        shutil.copy2(ROOT / "Tools/CI/Data" / filename, data / filename)
    for owner, filename in [("Conformance", "suites.json"), ("Compatibility", "compatibility.json")]:
        directory = root / "Tools" / owner
        directory.mkdir(parents=True)
        shutil.copy2(ROOT / "Tools" / owner / filename, directory / filename)
        script = "run_conformance.py" if owner == "Conformance" else "run_compatibility.py"
        shutil.copy2(ROOT / "Tools" / owner / script, directory / script)
    shutil.copytree(
        ROOT / "Tools/Runtime/Python",
        root / "Tools/Runtime/Python",
        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
    )
    documents = {key: json.loads((data / name).read_text()) for key, name in catalogs.FILES.items()}
    records = documents["policy"]["validators"] + documents["implementation"]["groups"]
    entries = [entry for row in records for entry in row["entry"]]
    registry = json.loads((root / "Tools/Conformance/suites.json").read_text())
    entries += [row[key] for row in registry["suites"] for key in ("python", "powershell")]
    entries += ["Tools/Tests/PowerShell/Fixtures/NativeResultCases.Tests.ps1"]
    for entry in entries:
        path = root / entry
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    fixtures = [
        item
        for row in records + documents["metadata"]["external_units"] + documents["metadata"]["comparisons"]
        for item in row["fixtures"]
    ]
    for fixture in fixtures:
        path = root / fixture
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if (ROOT / fixture).is_dir():
            path.mkdir(exist_ok=True)
        else:
            path.write_text("", encoding="utf-8")
    methodology = root / "Framework/testing_methodology.md"
    methodology.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "Framework/testing_methodology.md", methodology)
    shutil.copy2(ROOT / "Tools/CI/Data/runtime-versions.json", data / "runtime-versions.json")
    for script in (
        "catalog.py",
        "plan_ci.py",
        "scope.py",
        "selection.py",
        "explain_ci.py",
        "process_supervisor.py",
        "windows_process.py",
        "run_ci.py",
        "aggregate_execution.py",
        "layer_adapters.py",
        "adapter_worker.py",
        "Invoke-CiAdapter.ps1",
    ):
        shutil.copy2(ROOT / "Tools/CI" / script, root / "Tools/CI" / script)
    return root, data, documents


def write_documents(data, documents):
    for key, name in catalogs.FILES.items():
        (data / name).write_text(json.dumps(documents[key]), encoding="utf-8")


def test_real_planning_is_deterministic_without_launch_or_membership_copy(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("Planning launched a process"))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Planning launched a process"))
    catalog = catalogs.Catalog(ROOT)
    first = catalog.plan("pr-integration", "windows", ["python", "powershell7"], "pr-integration-initial")
    assert first == catalog.plan("pr-integration", "windows", ["python", "powershell7"], "pr-integration-initial")
    assert not first["execution_ready"] and first["runtime_assumptions_verified"] is False
    assert len([row for row in first["units"] if row["execution_id"].startswith("conformance/")]) == 42
    assert len([row for row in first["units"] if row["execution_id"].startswith("compatibility/")]) == 10
    assert first["rollout_blockers"]
    assert all(row["availability"] == "declared" for row in first["units"])


def test_private_tree_has_equivalent_plan_ids(private_catalog):
    root, _, _ = private_catalog
    actual = catalogs.Catalog(root).plan("implementation-pilot")
    expected = catalogs.Catalog(ROOT).plan("implementation-pilot")
    assert [row["execution_id"] for row in actual["units"]] == [row["execution_id"] for row in expected["units"]]


def test_unavailable_required_coverage_is_visible_not_omitted():
    plan = catalogs.Catalog(ROOT).plan("pr-integration", "linux", ["python"])
    blocked = {row["execution_id"] for row in plan["units"] if row["availability"] == "blocked"}
    assert "implementation/powershell-host::powershell7" in blocked
    assert "compatibility/qa::referee" in blocked
    assert len(plan["units"]) == len(catalogs.Catalog(ROOT).plan("pr-integration")["units"])


@pytest.mark.parametrize(
    "mutation",
    [
        "extra-root",
        "missing-root",
        "boolean-version",
        "duplicate-order",
        "unknown-adapter",
        "wrong-runtime",
        "wrong-contract",
        "argument-injection",
        "escaping-entry",
        "missing-entry",
        "double-owned",
        "skip-exemption",
        "empty-exemption",
        "missing-fixture",
        "unsafe-impact",
        "unknown-dependency",
        "cycle",
    ],
    ids=lambda value: value,
)
def test_invalid_registration_is_hard_failure(private_catalog, mutation):
    root, data, docs = private_catalog
    document = docs["implementation"]
    row = document["groups"][0]
    if mutation == "extra-root":
        document["extra"] = 1
    elif mutation == "missing-root":
        del document["discovery"]
    elif mutation == "boolean-version":
        document["schema_version"] = True
    elif mutation == "duplicate-order":
        document["groups"][1]["order"] = row["order"]
    elif mutation == "unknown-adapter":
        row["adapter"] = "shell-eval"
    elif mutation == "wrong-runtime":
        row["runtimes"] = ["powershell51"]
    elif mutation == "wrong-contract":
        row["result_contract"] = "invented"
    elif mutation == "argument-injection":
        row["arguments"] = ["--output-root", "../outside"]
    elif mutation == "escaping-entry":
        row["entry"] = ["../outside.py"]
    elif mutation == "missing-entry":
        row["entry"] = ["Tools/Tests/Python/test_missing.py"]
    elif mutation == "double-owned":
        document["groups"][1]["entry"] = row["entry"]
    elif mutation == "skip-exemption":
        row["allowed_skips"] = ["anything"]
    elif mutation == "empty-exemption":
        row["empty_policy"] = "allow-no-applicable-files"
    elif mutation == "missing-fixture":
        row["fixtures"] = ["missing-data"]
    elif mutation == "unsafe-impact":
        row["impact_paths"] = ["../**"]
    elif mutation == "unknown-dependency":
        row["depends_on"] = ["implementation/missing"]
    else:
        row["depends_on"] = ["implementation/" + row["id"]]
    write_documents(data, docs)
    with pytest.raises(catalogs.CatalogError):
        catalogs.Catalog(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "unregistered",
        "stale-exclusion",
        "extra-metadata",
        "missing-metadata",
        "bad-parity-normalization",
        "partial-parity",
        "bad-impact-edge",
        "non-impact-exemption",
    ],
    ids=lambda value: value,
)
def test_discovery_external_and_parity_fail_closed(private_catalog, mutation):
    root, data, docs = private_catalog
    metadata = docs["metadata"]
    if mutation == "unregistered":
        (root / "Tools/Tests/Python/test_extra.py").write_text("")
    elif mutation == "stale-exclusion":
        docs["implementation"]["discovery"][1]["exclude"][0]["path"] = "Tools/Tests/PowerShell/missing.Tests.ps1"
    elif mutation == "extra-metadata":
        metadata["external_units"].append(copy.deepcopy(metadata["external_units"][0]))
    elif mutation == "missing-metadata":
        metadata["external_units"].pop()
    elif mutation == "bad-parity-normalization":
        metadata["comparisons"][0]["normalization"] = "erase-errors"
    elif mutation == "partial-parity":
        metadata["comparisons"][0]["source_reference"]["runtimes"] = ["python"]
    elif mutation == "bad-impact-edge":
        metadata["dependencies"][0]["consumers"] = ["unknown/unit"]
    else:
        metadata["non_impact_paths"] = [{"pattern": "Tools/**", "reason": "unsafe", "decision": "none"}]
    write_documents(data, docs)
    with pytest.raises(catalogs.CatalogError):
        catalogs.Catalog(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-reference",
        "unknown-profile",
        "both-source-fields",
        "nonblocking",
        "missing-always",
        "affected",
        "profile-budget",
        "missing-unit",
        "duplicate-placement",
        "shard-os",
        "shard-budget",
        "shard-cycle",
        "missing-source-edge",
        "gate-missing-source",
        "gate-foreign-unit",
        "gate-duplicate-name",
        "gate-budget",
        "partial-aggregate",
    ],
    ids=lambda value: value,
)
def test_profile_and_shard_admission_is_not_weakened(private_catalog, mutation):
    root, data, docs = private_catalog
    profile = next(row for row in docs["profiles"]["profiles"] if row["id"] == "pr-integration")
    shard = next(row for row in docs["profiles"]["shard_plans"] if row["profile"] == profile["id"])
    if mutation == "duplicate-reference":
        profile["references"].append(copy.deepcopy(profile["references"][0]))
    elif mutation == "unknown-profile":
        profile["references"][-2]["profile"] = "unknown"
    elif mutation == "both-source-fields":
        profile["references"][0]["profile"] = "invented"
    elif mutation == "nonblocking":
        profile["references"][0]["blocking"] = False
    elif mutation == "missing-always":
        profile["always_run"] = ["implementation/missing::python"]
    elif mutation == "affected":
        profile["selection"] = "affected"
    elif mutation == "profile-budget":
        profile["budget"]["total_seconds"] = 211
    elif mutation == "missing-unit":
        shard["shards"][0]["units"].pop()
    elif mutation == "duplicate-placement":
        shard["shards"][1]["units"].append(shard["shards"][0]["units"][0])
    elif mutation == "shard-os":
        next(row for row in shard["shards"] if row["id"].startswith("compatibility"))["os"] = "linux"
    elif mutation == "shard-budget":
        shard["shards"][0]["budget"]["total_seconds"] = 211
    elif mutation == "shard-cycle":
        shard["shards"][0]["depends_on"] = [shard["shards"][0]["id"]]
    elif mutation == "missing-source-edge":
        next(row for row in shard["shards"] if row["id"].startswith("parity"))["depends_on"] = []
    elif mutation == "gate-missing-source":
        shard["gates"][0]["source_shards"] = []
    elif mutation == "gate-foreign-unit":
        shard["gates"][0]["units"].append("policy/missing::python")
    elif mutation == "gate-duplicate-name":
        shard["gates"][1]["check_name"] = shard["gates"][0]["check_name"]
    elif mutation == "gate-budget":
        shard["gates"][0]["budget"]["total_seconds"] = 211
    else:
        shard["gates"][-1]["units"].pop()
    write_documents(data, docs)
    with pytest.raises(catalogs.CatalogError):
        catalogs.Catalog(root)


def test_duplicate_json_keys_are_rejected(private_catalog):
    root, data, _ = private_catalog
    (data / "policy-validators.json").write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(catalogs.CatalogError, match="Duplicate JSON key"):
        catalogs.Catalog(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "foreign-profile",
        "wrong-snapshot",
        "stale-source",
        "missing-unit",
        "unknown-shard",
        "boolean-version",
    ],
    ids=lambda value: value,
)
def test_source_manifest_union_and_provenance(private_catalog, mutation):
    root, _, _ = private_catalog
    catalog = catalogs.Catalog(root)
    plan_id = "pr-integration-initial"
    shards = catalog.shard_plans[plan_id]["shards"]
    manifests = [catalog.expected_manifest(plan_id, row["id"], "a" * 64) for row in shards]
    projections = catalog.validate_manifests(plan_id, manifests, "a" * 64)
    assert projections[-1]["gate"] == "aggregate"
    if mutation == "missing":
        manifests.pop()
    elif mutation == "duplicate":
        manifests.append(copy.deepcopy(manifests[0]))
    elif mutation == "foreign-profile":
        manifests[0]["profile"] = "full-verification"
    elif mutation == "wrong-snapshot":
        manifests[0]["snapshot_digest"] = "b" * 64
    elif mutation == "stale-source":
        manifests[0]["source_digests"] = {}
    elif mutation == "missing-unit":
        manifests[0]["units"].pop()
    elif mutation == "unknown-shard":
        manifests[0]["shard"] = "unknown"
    else:
        manifests[0]["contract_version"] = True
    with pytest.raises(catalogs.CatalogError):
        catalog.validate_manifests(plan_id, manifests, "a" * 64)


def test_returned_plan_mutation_does_not_change_catalog():
    catalog = catalogs.Catalog(ROOT)
    expected = catalog.plan("implementation-pilot")
    changed = catalog.plan("implementation-pilot")
    changed["units"][0]["entry"].clear()
    changed["source_digests"].clear()
    assert catalog.plan("implementation-pilot") == expected


def test_stale_source_after_planning_is_rejected(private_catalog):
    root, _, _ = private_catalog
    catalog = catalogs.Catalog(root)
    (root / "Tools/CI/plan_ci.py").write_text("# changed source\n")
    with pytest.raises(catalogs.CatalogError, match="Source changed"):
        catalog.expected_manifest("pr-integration-initial", "native-policy-0", "a" * 64)


def test_invalid_external_registry_has_catalog_classification(private_catalog):
    root, _, _ = private_catalog
    path = root / "Tools/Compatibility/compatibility.json"
    registry = json.loads(path.read_text())
    registry["runtimes"].append("powershell51")
    path.write_text(json.dumps(registry))
    with pytest.raises(catalogs.CatalogError, match="obsolete"):
        catalogs.Catalog(root)
