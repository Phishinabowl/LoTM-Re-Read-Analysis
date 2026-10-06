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
finally:
    sys.path[:] = before


def git(root, *arguments):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    child = subprocess.run(["git", *arguments], cwd=root, env=env, capture_output=True, check=True)
    return child.stdout.decode("utf-8").strip()


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
