"""Git scope, snapshot isolation and advisory-selection regression."""

import copy
import importlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/CI"))
    scope = importlib.import_module("scope")
    selection = importlib.import_module("selection")
    github_shadow = importlib.import_module("github_shadow")
    ado_shadow = importlib.import_module("ado_shadow")
finally:
    sys.path[:] = before


def git(root, *arguments):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    child = subprocess.run(["git", *arguments], cwd=root, env=env, capture_output=True, check=True)
    return child.stdout.decode("utf-8").strip()


def azure_fixture():
    source, base, merge = "a" * 40, "b" * 40, "c" * 40
    env = {
        "SYSTEM_COLLECTIONURI": ado_shadow.COLLECTION,
        "SYSTEM_TEAMPROJECTID": ado_shadow.PROJECT,
        "BUILD_REPOSITORY_ID": ado_shadow.REPOSITORY,
        "BUILD_REASON": "PullRequest",
        "BUILD_SOURCEVERSION": merge,
        "BUILD_BUILDID": "123",
        "SYSTEM_PULLREQUEST_PULLREQUESTID": "7",
        "SYSTEM_PULLREQUEST_SOURCECOMMITID": source,
        "SYSTEM_PULLREQUEST_SOURCEBRANCH": "refs/heads/feature",
        "SYSTEM_PULLREQUEST_TARGETBRANCH": "refs/heads/" + github_shadow.TARGET,
        "BUILD_SOURCEBRANCH": "refs/pull/7/merge",
    }
    pull = {
        "pullRequestId": 7,
        "status": "active",
        "repository": {"id": ado_shadow.REPOSITORY, "project": {"id": ado_shadow.PROJECT}},
        "sourceRefName": env["SYSTEM_PULLREQUEST_SOURCEBRANCH"],
        "targetRefName": env["SYSTEM_PULLREQUEST_TARGETBRANCH"],
        "lastMergeSourceCommit": {"commitId": source},
        "lastMergeTargetCommit": {"commitId": base},
        "lastMergeCommit": {"commitId": merge},
    }
    return env, pull


def test_azure_policy_forces_full_pr_and_preserves_immutable_metadata():
    env, pull = azure_fixture()
    env["SHADOW_PROFILE"] = "ci-infrastructure"
    result = ado_shadow.event_context(env, pull)
    assert result["profile"] == "pr-integration" and result["checkout_kind"] == "merge"
    assert result["base"] == "b" * 40 and result["source"] == "a" * 40
    assert result["executed"] == "c" * 40 and result["host"] == "ado"


@pytest.mark.parametrize(
    "reason,mode,probe",
    [
        ("PullRequest", "cohorts", "none"),
        ("Manual", "unknown", "none"),
        ("Manual", "cohorts", "failures"),
        ("PullRequest", "cohort-smoke", "none"),
    ],
)
def test_azure_cohort_experiments_are_manual_only_and_cannot_mix_with_other_probes(reason, mode, probe):
    env, pull = azure_fixture()
    env.update(BUILD_REASON=reason, SHADOW_PLACEMENT=mode, SHADOW_PUBLICATION_QUALIFICATION=probe)
    with pytest.raises(ValueError, match="placement"):
        ado_shadow.event_context(env, pull)


@pytest.mark.parametrize(
    "changes",
    [
        {"SHADOW_COHORT_QUALIFICATION": "unknown"},
        {"SHADOW_PLACEMENT": "shards"},
        {"SHADOW_PLACEMENT": "cohorts"},
        {"SHADOW_PROFILE": "ci-infrastructure"},
        {"BUILD_REASON": "PullRequest"},
        {"SHADOW_PUBLICATION_QUALIFICATION": "failures"},
        {"SHADOW_PR_NUMBER": "7", "BUILD_SOURCEVERSION": "a" * 40},
    ],
)
def test_cohort_failure_probe_cannot_enter_ordinary_full_or_pr_runs(changes):
    env, pull = azure_fixture()
    env.update(BUILD_REASON="Manual", SHADOW_PLACEMENT="cohort-smoke", SHADOW_COHORT_QUALIFICATION="launch-failure")
    env.update(changes)
    with pytest.raises(ValueError):
        ado_shadow.event_context(env, pull)


def test_cohort_failure_probe_is_captured_only_in_explicit_manual_smoke():
    env, _ = azure_fixture()
    env.update(BUILD_REASON="Manual", SHADOW_PLACEMENT="cohort-smoke", SHADOW_COHORT_QUALIFICATION="launch-failure")
    context = ado_shadow.event_context(env)
    assert context["cohort_qualification"] == "launch-failure"
    env["SHADOW_COHORT_QUALIFICATION"] = "none"
    assert "cohort_qualification" not in ado_shadow.event_context(env)


@pytest.mark.parametrize(
    "field,value",
    [
        ("SYSTEM_COLLECTIONURI", "https://example.invalid/"),
        ("SYSTEM_TEAMPROJECTID", "other"),
        ("BUILD_REPOSITORY_ID", "other"),
        ("BUILD_SOURCEVERSION", "d" * 40),
        ("SYSTEM_PULLREQUEST_SOURCECOMMITID", "d" * 40),
        ("SYSTEM_PULLREQUEST_TARGETBRANCH", "refs/heads/main"),
        ("SYSTEM_PULLREQUEST_SOURCEBRANCH", "refs/heads/other"),
        ("BUILD_SOURCEBRANCH", "refs/heads/feature"),
        ("BUILD_REASON", "IndividualCI"),
        ("SYSTEM_PULLREQUEST_PULLREQUESTID", ""),
        ("BUILD_BUILDID", "1\ncommand"),
    ],
)
def test_azure_untrusted_or_changed_execution_fails(field, value):
    env, pull = azure_fixture()
    env[field] = value
    with pytest.raises(ValueError):
        ado_shadow.event_context(env, pull)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "completed"),
        ("pullRequestId", 8),
        ("targetRefName", "refs/heads/main"),
        ("lastMergeCommit", {"commitId": "d" * 40}),
        ("forkSource", {"repository": "other"}),
    ],
)
def test_azure_api_corroboration_rejects_stale_or_foreign_pr(field, value):
    env, pull = azure_fixture()
    pull[field] = value
    with pytest.raises(ValueError):
        ado_shadow.event_context(env, pull)


def test_azure_manual_source_replay_and_unknown_base_are_distinct():
    env, pull = azure_fixture()
    env.update(
        BUILD_REASON="Manual", BUILD_SOURCEVERSION="a" * 40, SHADOW_PROFILE="pr-integration", SHADOW_PR_NUMBER="7"
    )
    context = ado_shadow.event_context(env, pull)
    assert context["checkout_kind"] == "source" and context["scope"] == "hosted-pr"
    env["SHADOW_PR_NUMBER"] = ""
    context = ado_shadow.event_context(env)
    assert context["scope"] == "hosted-commit" and context["base"] == "unavailable-manual-base"


def test_azure_missing_pr_metadata_cannot_become_green_full_fallback():
    env, _ = azure_fixture()
    with pytest.raises(ValueError, match="metadata"):
        ado_shadow.event_context(env)


def test_azure_matrix_preserves_catalog_order_union_and_deadlines():
    plan, independent, dependent = github_shadow.matrices(ROOT, {"profile": "pr-integration"})
    rows = list(ado_shadow.matrix(independent).values()) + list(ado_shadow.matrix(dependent).values())
    assert {row["shard"] for row in rows} == {row["id"] for row in plan["shards"]}
    for wave, depends in ((independent, False), (dependent, True)):
        assert [row["shard"] for row in ado_shadow.matrix(wave).values()] == [
            row["id"] for row in plan["shards"] if bool(row["depends_on"]) == depends
        ]
    assert all(row["timeout"] <= 55 for row in rows)


def test_azure_matrix_collision_fails_and_empty_wave_is_explicitly_unexecuted():
    with pytest.raises(ValueError, match="collides"):
        ado_shadow.matrix({"include": [{"shard": "a-b"}, {"shard": "a_b"}]})
    assert ado_shadow.matrix({"include": []}) == {
        "NoWork": {"shard": "__no_work__", "os": "windows-2022", "timeout": 1}
    }


def test_shard_job_titles_are_sequential_across_waves_without_renaming_execution_ids():
    plan, independent, dependent = github_shadow.matrices(ROOT, {"profile": "pr-integration"})
    rows = independent["include"] + dependent["include"]
    assert [row["display_number"] for row in rows] == list(range(1, 10))
    assert rows[2]["display_name"] == "03 — Python conformance (batch 1 of 2)"
    assert rows[3]["display_name"] == "04 — Python conformance (batch 2 of 2)"
    assert rows[4]["display_name"] == "05 — PowerShell 7 conformance (batch 1 of 2)"
    assert rows[-1]["display_name"] == "09 — Cross-runtime parity" and rows[-1]["shard"] == "parity-5"
    assert {row["shard"] for row in rows} == {row["id"] for row in plan["shards"]}
    legs = {**ado_shadow.matrix(independent), **ado_shadow.matrix(dependent)}
    assert list(legs)[0] == "Check_01_Policy_and_implementation_tests"
    assert list(legs)[-1] == "Check_09_Cross_runtime_parity"
    assert [row["display_number"] for row in legs.values()] == list(range(1, 10))


@pytest.mark.parametrize("number", [True, 0, -1, 100, "1"])
def test_azure_display_number_rejects_invalid_or_boolean_identity(number):
    with pytest.raises(ValueError, match="display identity"):
        ado_shadow.matrix({"include": [{"shard": "fixture", "display_number": number, "display_title": "Fixture"}]})


def test_azure_output_escapes_logging_controls(capsys):
    ado_shadow.output(context="data%\r\n##vso[task.complete result=Succeeded]fake")
    assert capsys.readouterr().out == (
        "##vso[task.setvariable variable=context;isOutput=true]"
        "data%AZP25%0D%0A##vso[task.complete result=Succeeded]fake\n"
    )


def test_azure_yaml_transport_keeps_policy_credentials_and_membership_bounded():
    import yaml

    class UniqueLoader(yaml.SafeLoader):
        pass

    def unique_mapping(loader, node):
        result = {}
        for key, value in node.value:
            name = loader.construct_object(key)
            assert name not in result, "Duplicate Azure YAML key: " + name
            result[name] = loader.construct_object(value)
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    pipeline = yaml.load((ROOT / ".azuredevops/ci.yml").read_text(), Loader=UniqueLoader)
    worker = yaml.load((ROOT / ".azuredevops/ci-worker.yml").read_text(), Loader=UniqueLoader)
    assert pipeline["trigger"] == "none" and pipeline["pr"] == "none"
    assert "schedules" not in pipeline
    steps = pipeline["jobs"][0]["steps"]
    context_step = next(row for row in steps if row.get("name") == "Context")
    assert context_step["env"]["SYSTEM_ACCESSTOKEN"] == "$(System.AccessToken)"
    assert sum("SYSTEM_ACCESSTOKEN" in row.get("env", {}) for row in steps) == 1
    checkouts = [row for row in steps + worker["jobs"][0]["steps"] if "checkout" in row]
    assert all(row["fetchDepth"] == 0 and row["persistCredentials"] is False for row in checkouts)
    dependent = worker["jobs"][0]["${{ if eq(parameters.wave, 'dependent') }}"]
    assert dependent["condition"] == (
        "and(not(canceled()), eq(dependencies.Plan.result, 'Succeeded'), "
        "ne(dependencies.Plan.outputs['Catalog.dependent_count'], '0'))"
    )
    assert worker["jobs"][0]["${{ if ne(parameters.wave, 'dependent') }}"]["condition"] == (
        "and(not(canceled()), eq(dependencies.Plan.result, 'Succeeded'))"
    )
    assert all("continueOnError" not in row for row in steps + worker["jobs"][0]["steps"])


@pytest.mark.integration
def test_azure_merge_scope_uses_real_multicommit_branch(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-b", "feature")
    (repo / "first.txt").write_text("first")
    commit(repo, "first")
    (repo / "second.txt").write_text("second")
    source = commit(repo, "second")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "feature", "-m", "Azure synthetic merge")
    merge = git(repo, "rev-parse", "HEAD")
    env, pull = azure_fixture()
    env.update(BUILD_SOURCEVERSION=merge, SYSTEM_PULLREQUEST_SOURCECOMMITID=source)
    pull.update(
        lastMergeSourceCommit={"commitId": source},
        lastMergeTargetCommit={"commitId": base},
        lastMergeCommit={"commitId": merge},
    )
    result = github_shadow.validate_context(repo, ado_shadow.event_context(env, pull))
    assert {row["new_path"] for row in result["changes"]} == {"first.txt", "second.txt"}


@pytest.fixture(scope="session")
def repo_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("scope-baseline")
    git(root, "init", "--initial-branch=main")
    git(root, "config", "user.name", "CI synthetic fixture")
    git(root, "config", "user.email", "ci-fixture@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "config", "core.autocrlf", "false")
    (root / ".gitignore").write_text(".tmp/\nignored/\n", encoding="utf-8")
    (root / "tracked.txt").write_bytes(b"initial\n")
    git(root, "add", "--all")
    git(root, "commit", "-m", "synthetic baseline")
    return root


@pytest.fixture
def repo(tmp_path, repo_seed):
    root = tmp_path / "repo"
    shutil.copytree(repo_seed, root)
    return root


def test_private_git_copies_do_not_share_history_configuration_or_worktree(repo, repo_seed):
    before = git(repo_seed, "rev-parse", "HEAD")
    original_config = (repo_seed / ".git/config").read_bytes()
    (repo / "tracked.txt").write_bytes(b"changed independent worktree\n")
    git(repo, "config", "user.name", "Independent fixture")
    commit(repo, "independent history")
    assert git(repo, "rev-parse", "HEAD") != before
    assert git(repo_seed, "rev-parse", "HEAD") == before
    assert (repo_seed / ".git/config").read_bytes() == original_config
    assert (repo_seed / "tracked.txt").read_bytes() == b"initial\n"
    assert git(repo_seed, "status", "--porcelain") == ""


def commit(root, message):
    git(root, "add", "--all")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def shadow_event(base, source):
    return {
        "pull_request": {
            "number": 7,
            "head": {"sha": source},
            "base": {"sha": base, "ref": github_shadow.TARGET, "repo": {"full_name": "fixture/repository"}},
        }
    }


def shadow_environment(head, name="pull_request"):
    return {
        "GITHUB_SHA": head,
        "GITHUB_EVENT_NAME": name,
        "GITHUB_REPOSITORY": "fixture/repository",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "2",
    }


def test_github_pr_context_proves_full_multicommit_scope_and_merge_execution(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-b", "feature")
    (repo / "first.txt").write_text("first")
    commit(repo, "first source")
    (repo / "tracked.txt").unlink()
    source = commit(repo, "second source deletes baseline")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "feature", "-m", "synthetic hosted merge")
    executed = git(repo, "rev-parse", "HEAD")
    context = github_shadow.event_context(shadow_event(base, source), shadow_environment(executed))
    result = github_shadow.validate_context(repo, context)
    assert context["profile"] == "pr-integration" and result["provenance"]["checkout_kind"] == "merge"
    assert result["fallback_reasons"] == []
    assert {row["new_path"] or row["old_path"] for row in result["changes"]} == {"first.txt", "tracked.txt"}
    context["executed"] = source
    with pytest.raises(ValueError, match="checkout differs"):
        github_shadow.validate_context(repo, context)


@pytest.mark.parametrize("kind", ["merge", "source"])
def test_manual_pr_replay_preserves_exact_metadata(kind):
    pull = shadow_event("a" * 40, "b" * 40)["pull_request"]
    pull["merge_commit_sha"] = "c" * 40
    event = {"inputs": {"profile": "pr-integration", "checkout_kind": kind}}
    context = github_shadow.event_context(event, shadow_environment("d" * 40, "workflow_dispatch"), pull)
    assert context["executed"] == ("b" if kind == "source" else "c") * 40
    assert context["base"] == "a" * 40 and context["source"] == "b" * 40


@pytest.mark.parametrize("mutation", ["target", "source", "event", "profile"])
def test_github_context_rejects_unapproved_metadata(mutation):
    event = shadow_event("a" * 40, "b" * 40)
    environment = shadow_environment("c" * 40)
    if mutation == "target":
        event["pull_request"]["base"]["ref"] = "main"
    elif mutation == "source":
        event["pull_request"]["head"]["sha"] = "moving-branch"
    elif mutation == "event":
        environment["GITHUB_EVENT_NAME"] = "pull_request_target"
    else:
        environment["GITHUB_EVENT_NAME"] = "workflow_dispatch"
        event = {"inputs": {"profile": "arbitrary-profile"}}
    with pytest.raises(ValueError):
        github_shadow.event_context(event, environment)


def test_github_unproven_merge_fails_instead_of_testing_unrelated_tree(repo):
    head = git(repo, "rev-parse", "HEAD")
    context = github_shadow.event_context(shadow_event(head, "b" * 40), shadow_environment(head))
    with pytest.raises(ValueError, match="parents"):
        github_shadow.validate_context(repo, context)


def test_github_matrix_is_complete_catalog_owned_and_admitted():
    plan, independent, dependent = github_shadow.matrices(ROOT, {"profile": "pr-integration"})
    rows = independent["include"] + dependent["include"]
    assert [row["shard"] for row in dependent["include"]] == ["parity-5"]
    assert {row["shard"] for row in rows} == {row["id"] for row in plan["shards"]}
    assert all(row["timeout"] <= 55 for row in rows)


def test_preparation_roles_preserve_every_admitted_shard_and_required_package_render_setup():
    plan, _, _ = github_shadow.matrices(ROOT, {"profile": "pr-integration"})
    roles = github_shadow.preparation_roles(ROOT, plan)
    assert set(roles) == {row["id"] for row in plan["shards"]}
    assert roles["native-policy-0"] == "build"
    assert roles["compatibility-6"] == "complete"
    assert all(role == "core" for shard, role in roles.items() if shard not in {"native-policy-0", "compatibility-6"})


@pytest.mark.parametrize(
    "adapter,expected",
    [
        ("installed-artifact", "build"),
        ("compatibility", "complete"),
        ("future-adapter", "complete"),
        ("pytest", "core"),
    ],
)
def test_preparation_derivation_keeps_unknown_dependencies_conservative(monkeypatch, adapter, expected):
    monkeypatch.setattr(
        github_shadow,
        "Catalog",
        lambda root: type(
            "Fixture",
            (),
            {"plan": lambda self, profile: {"units": [{"execution_id": "fixture::python", "adapter": adapter}]}},
        )(),
    )
    plan = {"profile": "fixture", "shards": [{"id": "fixture", "units": ["fixture::python"]}]}
    assert github_shadow.preparation_roles(ROOT, plan) == {"fixture": expected}


@pytest.mark.parametrize("roles", [[], {}, {"fixture": []}, {"fixture": True}, {"fixture": "collection"}])
def test_assigned_execution_role_rejects_missing_or_malformed_transport(roles):
    with pytest.raises(ValueError, match="preparation role"):
        github_shadow.assigned_payload({"preparation_roles": roles}, "fixture")


def test_unspecified_execution_preparation_retains_complete_fallback():
    assert github_shadow.assigned_payload({}, "fixture") == "complete"
    assert github_shadow.assigned_payload({}, None) == "collection"


def test_worker_rejects_transport_role_downgrade_before_reading_build_inputs(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "Tools/CI"))
    monkeypatch.setattr(github_shadow, "ROOT", tmp_path)
    monkeypatch.setattr(github_shadow, "validate_context", lambda *a: {})
    monkeypatch.setattr(
        github_shadow, "matrices", lambda *a: ({"shards": [{"id": "fixture", "depends_on": []}]}, {}, {})
    )
    monkeypatch.setattr(github_shadow, "preparation_roles", lambda *a: {"fixture": "build"})
    out = tmp_path / ".tmp/ci-cache-pilot"
    out.mkdir(parents=True)
    (out / "bootstrap.json").write_text(json.dumps({"status": "passed"}))
    (out / "pilot.json").write_text(json.dumps({"exit_code": 0, "payload_profile": "core"}))
    with pytest.raises(ValueError, match="approved execution plan"):
        github_shadow.execute({"preparation_roles": {"fixture": "core"}}, "fixture", tmp_path / ".tmp/absent")


@pytest.mark.parametrize("profile", ["pr-integration", "full-verification", "ci-infrastructure"])
def test_ado_capacity_proposal_preserves_logical_shards_dependencies_and_every_reserve(profile):
    original, _, _ = github_shadow.matrices(ROOT, {"profile": profile})
    proposal = ado_shadow.cohort_plan(ROOT, profile)
    owners = {shard: row["id"] for row in proposal["cohorts"] for shard in row["shards"]}
    assert set(owners) == {row["id"] for row in original["shards"]}
    assert sum(len(row["shards"]) for row in proposal["cohorts"]) == len(owners)
    for cohort in proposal["cohorts"]:
        rows = [row for row in original["shards"] if row["id"] in cohort["shards"]]
        assert cohort["declared_shard_seconds"] == sum(row["budget"]["total_seconds"] for row in rows)
        assert cohort["timeout_minutes"] <= 55
        assert cohort["preserved_child_setup_seconds"] == 600 * len(rows)
        assert cohort["timeout_minutes"] * 60 >= cohort["declared_shard_seconds"] + 600 * len(rows) + 300
        assert all(row["os"] == cohort["os"] for row in rows)
        assert set(cohort["depends_on"]) == {owners[value] for row in rows for value in row["depends_on"]}
    assert proposal["adopted"] is False
    assert (proposal["original_jobs"], proposal["proposed_jobs"]) == (
        (3, 3) if profile == "ci-infrastructure" else (11, 10)
    )


@pytest.mark.parametrize("shard,expected", [("infrastructure-0", "complete"), ("", "collection")])
def test_host_cache_role_uses_assigned_shard_before_bootstrap(tmp_path, monkeypatch, shard, expected):
    monkeypatch.setattr(github_shadow, "ROOT", tmp_path)
    monkeypatch.setattr(github_shadow, "validate_context", lambda *a: {})
    observed = []
    monkeypatch.setattr(
        github_shadow.host_cache,
        "cache_identity",
        lambda *a, **kw: observed.append(kw["payload_profile"]) or {"key": "fixture"},
    )
    monkeypatch.setattr(github_shadow, "output", lambda **kw: None)
    monkeypatch.setenv("SHADOW_CONTEXT", json.dumps({"host": "github"}))
    monkeypatch.setenv("SHADOW_SHARD", shard)
    monkeypatch.setattr(sys, "argv", ["github_shadow", "prepare"])
    assert github_shadow.main() == 0
    assert observed == [expected]


@pytest.mark.parametrize("payload_profile,source", [("complete", "a" * 40), ("collection", "b" * 40)])
def test_collection_rejects_wrong_role_or_source_before_reading_build_inputs(
    tmp_path, monkeypatch, payload_profile, source
):
    monkeypatch.syspath_prepend(str(ROOT / "Tools/CI"))
    monkeypatch.setattr(github_shadow, "ROOT", tmp_path)
    monkeypatch.setattr(github_shadow, "validate_context", lambda *a: {})
    monkeypatch.setattr(github_shadow, "matrices", lambda *a: ({"shards": []}, {}, {}))
    out = tmp_path / ".tmp/ci-cache-pilot"
    out.mkdir(parents=True)
    (out / "bootstrap.json").write_text(json.dumps({"status": "passed"}))
    (out / "pilot.json").write_text(
        json.dumps({"exit_code": 0, "payload_profile": payload_profile, "source_revision": source})
    )
    with pytest.raises(ValueError, match="role-specific"):
        github_shadow.execute(
            {"profile": "ci-infrastructure", "executed": "a" * 40}, None, tmp_path / ".tmp/absent-inputs"
        )


def test_github_manual_without_base_retains_full_comparison_fallback(repo):
    head = git(repo, "rev-parse", "HEAD")
    context = github_shadow.event_context({}, shadow_environment(head, "workflow_dispatch"))
    result = github_shadow.validate_context(repo, context)
    assert result["policy_scope"]["mode"] == "full" and result["fallback_reasons"]


@pytest.mark.parametrize("unsafe", ["depth", "budget"])
def test_github_transport_refuses_unadmitted_graphs(unsafe, monkeypatch):
    rows = [
        {
            "id": str(index),
            "depends_on": [str(index - 1)] if index else [],
            "os": "windows",
            "budget": {"total_seconds": 330},
        }
        for index in range(3)
    ]
    if unsafe == "budget":
        rows = rows[:1]
        rows[0]["budget"]["total_seconds"] = 3300
    plan = {"profile": "synthetic", "shards": rows}
    monkeypatch.setattr(
        github_shadow, "Catalog", lambda root: type("Fixture", (), {"shard_plans": {"fixture": plan}})()
    )
    with pytest.raises(ValueError):
        github_shadow.matrices(ROOT, {"profile": "synthetic"})


def test_github_context_cli_works_without_site_packages_and_uses_ignored_report_storage(tmp_path):
    event = tmp_path / "event.json"
    event.write_text(json.dumps(shadow_event("a" * 40, "b" * 40)))
    output = tmp_path / "outputs.txt"
    environment = {
        **os.environ,
        **shadow_environment("c" * 40),
        "GITHUB_EVENT_PATH": str(event),
        "GITHUB_OUTPUT": str(output),
    }
    child = subprocess.run(
        [sys.executable, "-I", "-S", str(ROOT / "Tools/CI/github_shadow.py"), "context"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert child.returncode == 0, child.stdout + child.stderr
    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert values["checkout"] == "c" * 40
    assert json.loads(values["context"])["profile"] == "pr-integration"


@pytest.mark.integration
@pytest.mark.parametrize("adapter", ["github", "ado", "ado-cohorts", "ado-cohort-smoke"])
def test_host_full_planning_cli_in_clean_private_checkout(tmp_path, adapter):
    root = tmp_path / "private-project"
    # Captured CI sources have a private index without HEAD; copy index-approved working bytes.
    inventory = scope.parse_inventory(scope.Git(ROOT).index(), index=True)
    for name, row in inventory.items():
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / name).read_bytes())
        destination.chmod(0o755 if row["mode"] == "100755" else 0o644)
    # Include the new adapter during pre-publication review before it enters the tracked inventory.
    shutil.copy2(ROOT / "Tools/CI/ado_shadow.py", root / "Tools/CI/ado_shadow.py")
    # New display-only helper must participate in clean-checkout proof before publication.
    shutil.copy2(ROOT / "Tools/CI/presentation.py", root / "Tools/CI/presentation.py")
    # Include registered cohort sources during review before they enter the tracked inventory.
    for name in ("Tools/CI/ado_cohort.py", "Tools/Tests/Python/test_ci_cohort.py"):
        shutil.copy2(ROOT / name, root / name)
    git(root, "init", "--initial-branch=main")
    git(root, "config", "user.name", "CI planning fixture")
    git(root, "config", "user.email", "ci-fixture@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "config", "core.autocrlf", "false")
    head = commit(root, "private planning source")
    output = tmp_path / "plan-outputs.txt"
    context = github_shadow.event_context(
        {"inputs": {"profile": "pr-integration"}}, shadow_environment(head, "workflow_dispatch")
    )
    host = "ado" if adapter.startswith("ado") else adapter
    context["host"] = host
    if adapter in {"ado-cohorts", "ado-cohort-smoke"}:
        context.update(event="Manual", placement=adapter.removeprefix("ado-"))
        if adapter == "ado-cohort-smoke":
            context["profile"] = "full-verification"
    environment = {**os.environ, "SHADOW_CONTEXT": json.dumps(context), "GITHUB_OUTPUT": str(output)}
    child = subprocess.run(
        [sys.executable, "-I", str(root / f"Tools/CI/{host}_shadow.py"), "plan"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == 0, child.stdout + child.stderr
    if adapter == "github":
        values = dict(line.split("=", 1) for line in output.read_text().splitlines())
        assert len(json.loads(values["independent"])["include"]) == 8
        assert len(json.loads(values["dependent"])["include"]) == 1
    else:
        values = dict(line.split(";isOutput=true]", 1) for line in child.stdout.splitlines())
        assert len(json.loads(values["##vso[task.setvariable variable=independent"])) == (
            1 if adapter == "ado-cohort-smoke" else 7 if adapter == "ado-cohorts" else 8
        )
        assert len(json.loads(values["##vso[task.setvariable variable=dependent"])) == 1
        if adapter == "ado-cohort-smoke":
            assert values["##vso[task.setvariable variable=dependent_count"] == "0"
            assert "NoWork" in json.loads(values["##vso[task.setvariable variable=dependent"])
    plan = json.loads((root / ".tmp/ci-shadow/plan.json").read_text())
    assert plan["scope"]["provenance"]["executed_commit"] == head
    assert plan["scope"]["policy_scope"]["mode"] == "full"
    assert git(root, "status", "--porcelain") == ""


def test_host_checkout_override_preserves_license_blob_bytes_under_crlf_machine_default(repo):
    license_file = repo / "LICENSE"
    license_file.write_bytes(b"license text\n")
    commit(repo, "synthetic LF license")
    git(repo, "config", "core.autocrlf", "true")
    license_file.unlink()
    git(repo, "checkout", "HEAD", "--", "LICENSE")
    assert license_file.read_bytes() == b"license text\r\n"
    license_file.unlink()
    environment = {
        **scope.Git(repo).environment,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.autocrlf",
        "GIT_CONFIG_VALUE_0": "false",
    }
    subprocess.run(
        ["git", "checkout", "HEAD", "--", "LICENSE"],
        cwd=repo,
        env=environment,
        capture_output=True,
        check=True,
        timeout=15,
    )
    assert license_file.read_bytes() == scope.Git(repo).read("show", "HEAD:LICENSE") == b"license text\n"


@pytest.mark.integration
def test_multicommit_mergebase_unicode_spaces_and_deletion(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-b", "feature")
    (repo / "a space é.txt").write_text("first", encoding="utf-8")
    commit(repo, "first source change")
    (repo / "tracked.txt").unlink()
    source = commit(repo, "second source change")
    report, snapshot = scope.resolve_scope(repo, "committed", base, source)
    assert report["provenance"]["merge_base"] == base
    assert report["provenance"]["executed_commit"] == source
    assert [(row["status"], row["new_path"] or row["old_path"]) for row in report["changes"]] == [
        ("A", "a space é.txt"),
        ("D", "tracked.txt"),
    ]
    assert "tracked.txt" not in snapshot.files
    assert any(row["status"] == "pending-deletion-integrity" for row in report["policy_scope"]["dispositions"])


@pytest.mark.integration
def test_staged_and_worktree_modes_preserve_different_contents(repo):
    (repo / "tracked.txt").write_text("staged", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    (repo / "tracked.txt").write_text("unstaged", encoding="utf-8")
    (repo / "new é.txt").write_text("untracked", encoding="utf-8")
    (repo / "ignored").mkdir()
    (repo / "ignored/hidden.txt").write_text("ignored")
    staged, index = scope.resolve_scope(repo, "local-staged")
    worktree, working = scope.resolve_scope(repo, "local-worktree")
    assert index.files["tracked.txt"] == b"staged" and working.files["tracked.txt"] == b"unstaged"
    assert "new é.txt" not in index.files and "new é.txt" in working.files
    assert "ignored/hidden.txt" not in working.files
    assert staged["provenance"]["snapshot_kind"] == "index"
    assert worktree["provenance"]["snapshot_kind"] == "worktree"
    assert index.digest != working.digest


@pytest.mark.integration
def test_rename_and_copy_preserve_both_paths(repo):
    base = git(repo, "rev-parse", "HEAD")
    (repo / "tracked.txt").rename(repo / "renamed space.txt")
    (repo / "copy.txt").write_bytes(b"initial\n")
    source = commit(repo, "rename and copy")
    report, _ = scope.resolve_scope(repo, "committed", base, source)
    pairs = {(row["old_path"], row["new_path"]) for row in report["changes"]}
    assert ("tracked.txt", "renamed space.txt") in pairs and ("tracked.txt", "copy.txt") in pairs
    assert {row["status"][0] for row in report["changes"]} == {"R", "C"}


@pytest.mark.integration
def test_merge_execution_records_source_impact_not_merge_tree_diff(repo):
    git(repo, "checkout", "-b", "feature")
    (repo / "source.txt").write_text("source")
    source = commit(repo, "source")
    git(repo, "checkout", "main")
    (repo / "target.txt").write_text("target")
    target = commit(repo, "target")
    git(repo, "merge", "--no-ff", "feature", "-m", "synthetic merge")
    executed = git(repo, "rev-parse", "HEAD")
    report, snapshot = scope.resolve_scope(repo, "hosted-pr", target, source, executed)
    assert report["provenance"]["checkout_kind"] == "merge"
    assert report["provenance"]["executed_commit"] == executed
    assert [row["new_path"] for row in report["changes"]] == ["source.txt"]
    assert "target.txt" in snapshot.files and not report["fallback_reasons"]


@pytest.mark.integration
def test_unknown_base_falls_back_but_unknown_source_and_dirty_checkout_block(repo):
    source = git(repo, "rev-parse", "HEAD")
    report, _ = scope.resolve_scope(repo, "committed", "missing-base", source)
    assert report["fallback_reasons"] and report["policy_scope"]["mode"] == "full"
    with pytest.raises(scope.ScopeError):
        scope.resolve_scope(repo, "committed", source, "missing-source")
    (repo / "untracked.txt").write_text("dirty")
    with pytest.raises(scope.ScopeError, match="dirty"):
        scope.resolve_scope(repo, "committed", source, source)


@pytest.mark.integration
def test_full_and_empty_local_scope_are_explicit(repo):
    empty, _ = scope.resolve_scope(repo, "local-worktree")
    full, snapshot = scope.resolve_scope(repo, "full")
    assert empty["changes"] == [] and not empty["fallback_reasons"]
    assert full["provenance"]["base_tip"] is None and full["provenance"]["merge_base"] is None
    assert full["policy_scope"]["paths"] == sorted(snapshot.files)
    with pytest.raises(scope.ScopeError):
        scope.resolve_scope(repo, "local-staged", base="HEAD")


@pytest.mark.integration
def test_snapshot_materialization_is_unique_isolated_and_verified(repo):
    report, snapshot = scope.resolve_scope(repo, "full")
    first = snapshot.materialize(repo, ".tmp/snapshots")
    second = snapshot.materialize(repo, ".tmp/snapshots")
    assert first != second and (first / "tracked.txt").read_bytes() == b"initial\n"
    (repo / "tracked.txt").write_text("later user edit")
    snapshot.verify(first)
    (first / "tracked.txt").write_text("corrupt")
    with pytest.raises(scope.ScopeError, match="drift"):
        snapshot.verify(first)
    with pytest.raises(scope.ScopeError):
        snapshot.materialize(repo, "../outside")
    assert report["execution_ready"] is False


@pytest.mark.integration
def test_shallow_history_falls_back_without_fetching(repo, tmp_path):
    base = git(repo, "rev-parse", "HEAD")
    (repo / "second.txt").write_text("second")
    commit(repo, "second")
    destination = tmp_path / "shallow"
    git(tmp_path, "clone", "--depth=1", "--no-local", repo.as_uri(), str(destination))
    report, _ = scope.resolve_scope(destination, "hosted-commit", base, "HEAD")
    assert report["fallback_reasons"] and report["provenance"]["executed_commit"]
    assert report["policy_scope"]["deletion_precision"] == "lost/not-compared"


@pytest.mark.parametrize(
    "path",
    ["../escape", "/absolute", "C:/drive", "a\\b", "a/../b", ".git/config", "a//b", ""],
    ids=["parent", "absolute", "drive", "backslash", "segment", "git-control", "empty-segment", "root"],
)
def test_unsafe_paths_rejected(path):
    with pytest.raises(scope.ScopeError):
        scope.safe_path(path)


def test_nul_parser_preserves_tabs_and_newlines_and_rejects_truncation():
    header = b":100644 100644 " + b"a" * 40 + b" " + b"b" * 40 + b" R100\0"
    rows = scope.parse_diff(header + b"old\tname\0new\nname\0")
    assert rows[0]["old_path"] == "old\tname" and rows[0]["new_path"] == "new\nname"
    for value in [header + b"old\0", header + b"old\0new", b"bad\0", header + b"old\0\xff\0"]:
        with pytest.raises(scope.ScopeError):
            scope.parse_diff(value)


def test_snapshot_rejects_windows_collisions_and_unsupported_modes():
    with pytest.raises(scope.ScopeError, match="collision"):
        scope.Snapshot({"A.txt": b"a", "a.txt": b"b"}, {"A.txt": "100644", "a.txt": "100644"}, windows=True)
    for mode in ["120000", "160000"]:
        with pytest.raises(scope.ScopeError):
            scope.Snapshot({"entry": b"bytes"}, {"entry": mode})


@pytest.mark.integration
def test_executable_mode_is_preserved_in_commit_snapshot(repo):
    base = git(repo, "rev-parse", "HEAD")
    if os.name != "nt":
        (repo / "tracked.txt").chmod(0o755)
    git(repo, "update-index", "--chmod=+x", "tracked.txt")
    git(repo, "commit", "-m", "synthetic mode change")
    report, snapshot = scope.resolve_scope(repo, "committed", base, "HEAD")
    assert snapshot.modes["tracked.txt"] == "100755"
    assert report["changes"][0]["old_mode"] == "100644"
    assert report["changes"][0]["new_mode"] == "100755"


@pytest.mark.integration
def test_index_drift_after_blob_capture_blocks(repo, monkeypatch):
    original = scope.Git.index
    count = 0

    def drift(reader):
        nonlocal count
        count += 1
        data = original(reader)
        return data if count == 1 else data + b" "

    monkeypatch.setattr(scope.Git, "index", drift)
    with pytest.raises(scope.ScopeError, match="drift"):
        scope.resolve_scope(repo, "local-staged")


def test_index_unmerged_inventory_is_not_a_safe_snapshot():
    with pytest.raises(scope.ScopeError, match="Unmerged"):
        scope.parse_inventory(b"100644 " + b"a" * 40 + b" 1\tpath\0", index=True)


@pytest.mark.integration
def test_worktree_drift_after_capture_blocks_planning(repo, monkeypatch):
    original = scope.Git.read
    changed = False

    def drift(reader, *arguments, **kwargs):
        nonlocal changed
        result = original(reader, *arguments, **kwargs)
        if arguments[0] == "diff" and not changed:
            changed = True
            (repo / "tracked.txt").write_bytes(b"changed during comparison")
        return result

    monkeypatch.setattr(scope.Git, "read", drift)
    with pytest.raises(scope.ScopeError, match="drift"):
        scope.resolve_scope(repo, "local-worktree")


@pytest.mark.integration
def test_unbounded_merge_metadata_uses_full_comparison_fallback(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-b", "feature")
    (repo / "source.txt").write_bytes(b"source")
    source = commit(repo, "source")
    git(repo, "checkout", "main")
    report, _ = scope.resolve_scope(repo, "hosted-pr", base, source)
    assert report["provenance"]["checkout_kind"] == "merge"
    assert any("cannot be bounded" in reason for reason in report["fallback_reasons"])


@pytest.mark.parametrize(
    "pattern,path,expected",
    [
        ("**/*.py", "root.py", True),
        ("Tools/**", "Tools", True),
        ("Tools/**", "Tools/a/b.py", True),
        ("Tools/*.py", "Tools/a/b.py", False),
        ("Tools/?.py", "Tools/a.py", True),
        ("tools/**", "Tools/a.py", False),
    ],
    ids=["root-globstar", "zero-segments", "nested", "segment-boundary", "question", "case"],
)
def test_glob_grammar(pattern, path, expected):
    assert selection.matches(pattern, path) is expected


@pytest.mark.parametrize("pattern", ["a[bc]", "!negation", "a/**b", "../**"])
def test_unsupported_glob_grammar_fails(pattern):
    with pytest.raises(selection.CatalogError):
        selection.matches(pattern, "a/b")


def selection_fixture():
    units = {
        "implementation/core": {"owner": "implementation", "impact_paths": ["Tools/core.py"]},
        "implementation/consumer": {"owner": "implementation", "impact_paths": ["Tools/consumer.py"]},
        "implementation/meta": {"owner": "implementation", "impact_paths": ["Tools/meta.py"]},
    }
    ids = [identity + "::python" for identity in units]
    plan = {
        "profile": "synthetic",
        "units": [{"execution_id": value, "depends_on": []} for value in ids],
        "always_run": [ids[-1]],
        "required_reviews": [],
    }
    metadata = {
        "full_selection_paths": [],
        "non_impact_paths": [],
        "dependencies": [
            {
                "source": "implementation/core",
                "consumers": ["implementation/consumer"],
                "reason": "shared implementation",
            }
        ],
    }
    report = {
        "changes": [{"status": "M", "old_path": "Tools/core.py", "new_path": "Tools/core.py"}],
        "fallback_reasons": [],
        "policy_scope": {"dispositions": [{"path": "Tools/core.py", "validated": False}]},
    }
    return plan, units, metadata, report


def test_transitive_selection_and_always_run_leave_execution_full():
    plan, units, metadata, report = selection_fixture()
    output = selection.explain(plan, units, metadata, report)
    assert output["would_select"] == output["candidate_units"]
    assert output["selection_enforced"] is False
    assert output["reasons"]["implementation/consumer::python"] == ["transitive impact: implementation/core"]
    assert output["reasons"]["implementation/meta::python"] == ["always-run obligation"]


def test_specific_selection_explains_omission_but_effective_membership_stays_full():
    plan, units, metadata, report = selection_fixture()
    metadata["dependencies"] = []
    output = selection.explain(plan, units, metadata, report)
    assert output["would_omit"] == ["implementation/consumer::python"]
    assert output["effective_execution_units"] == output["candidate_units"]


@pytest.mark.parametrize("cause", ["unknown", "shared", "unbounded", "comparison"])
def test_fallback_selects_whole_requested_profile(cause):
    plan, units, metadata, report = selection_fixture()
    if cause == "unknown":
        report["changes"][0].update(old_path="unknown.txt", new_path="unknown.txt")
    elif cause == "shared":
        metadata["full_selection_paths"] = [{"pattern": "Tools/**", "reason": "shared"}]
    elif cause == "unbounded":
        units["implementation/consumer"]["impact_paths"] = []
    else:
        report["fallback_reasons"] = ["missing comparison"]
    output = selection.explain(plan, units, metadata, report)
    assert output["fallback_reasons"] and output["would_select"] == output["candidate_units"]


def test_nonimpact_requires_reviewed_rule_and_independent_policy_completion():
    plan, units, metadata, report = selection_fixture()
    plan["always_run"] = []
    report["changes"][0].update(old_path="docs/note.md", new_path="docs/note.md")
    report["policy_scope"]["dispositions"] = [{"path": "docs/note.md", "validated": True}]
    metadata["dependencies"] = []
    metadata["non_impact_paths"] = [
        {"pattern": "docs/note.md", "reason": "inert fixture", "decision": "synthetic reviewed decision"}
    ]
    output = selection.explain(plan, units, metadata, report)
    assert output["status"] == "explained" and output["advisory_no_impact"] and output["would_select"] == []
    report["policy_scope"]["dispositions"][0]["validated"] = False
    with pytest.raises(selection.CatalogError):
        selection.explain(plan, units, metadata, report)


def test_nonimpact_conflict_cannot_hide_impact():
    plan, units, metadata, report = selection_fixture()
    metadata["non_impact_paths"] = [{"pattern": "Tools/core.py", "reason": "unsafe exemption", "decision": "synthetic"}]
    with pytest.raises(selection.CatalogError):
        selection.explain(plan, units, metadata, report)


def test_prerequisite_and_parity_closure_include_all_declared_sources():
    plan, units, metadata, report = selection_fixture()
    units["parity/pair"] = {
        "owner": "parity",
        "impact_paths": [],
        "source_units": ["implementation/core::python", "implementation/consumer::python"],
    }
    # The neutral fixture gives the comparison a bounded mapping so the closure path is tested.
    units["parity/pair"]["impact_paths"] = ["Tools/parity-only.py"]
    plan["units"].append({"execution_id": "parity/pair::referee", "depends_on": units["parity/pair"]["source_units"]})
    metadata["dependencies"] = []
    output = selection.explain(plan, units, metadata, report)
    assert "parity/pair::referee" in output["would_select"]
    assert "execution prerequisite for parity/pair::referee" in output["reasons"]["implementation/consumer::python"]


@pytest.mark.integration
@pytest.mark.parametrize("moving", ["source", "target", "checkout"])
def test_pr_metadata_drift_during_capture_cannot_be_admitted(repo, monkeypatch, moving):
    git(repo, "checkout", "-b", "feature")
    (repo / "source.txt").write_text("source")
    source = commit(repo, "source")
    git(repo, "checkout", "main")
    (repo / "target.txt").write_text("target")
    target = commit(repo, "target")
    git(repo, "merge", "--no-ff", "feature", "-m", "synthetic PR merge")
    git(repo, "update-ref", "refs/heads/target-base", target)
    executed = git(repo, "rev-parse", "HEAD")
    original = scope.Git.read
    changed = False

    def drift(self, *arguments, **options):
        nonlocal changed
        value = original(self, *arguments, **options)
        if arguments[0] == "diff" and not changed:
            changed = True
            if moving == "checkout":
                git(repo, "update-ref", "HEAD", target)
            else:
                git(
                    repo,
                    "update-ref",
                    "refs/heads/feature" if moving == "source" else "refs/heads/target-base",
                    executed,
                )
        return value

    monkeypatch.setattr(scope.Git, "read", drift)
    with pytest.raises(scope.ScopeError, match="drift"):
        scope.resolve_scope(repo, "hosted-pr", "target-base", "feature", executed)


def test_selector_reasons_order_counts_and_full_membership_are_repeatable():
    plan, units, metadata, report = selection_fixture()
    first = selection.explain(plan, units, metadata, report)
    reordered = dict(reversed(list(units.items())))
    for _ in range(3):
        again = selection.explain(plan, reordered, metadata, report)
        assert again == first
        assert len(again["would_select"]) + len(again["would_omit"]) == len(again["candidate_units"])
        assert again["effective_execution_units"] == again["candidate_units"]
