"""Azure event/variable transport over the qualified repository shadow executor."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import github_shadow as transport

COLLECTION = "https://dev.azure.com/DreamtechADO/"
PROJECT = "66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb"
REPOSITORY = "657f741d-cf62-44d6-8b6c-08d93f471133"


def positive(value):
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]{0,8}", value):
        raise ValueError("Bounded numeric Azure identity required")
    return int(value)


def event_context(environment, pull=None):
    """Require immutable execution metadata and API corroboration for PRs."""
    if (
        environment["SYSTEM_COLLECTIONURI"] != COLLECTION
        or environment["SYSTEM_TEAMPROJECTID"] != PROJECT
        or environment["BUILD_REPOSITORY_ID"] != REPOSITORY
    ):
        raise ValueError("Azure destination differs from approved collection/project/repository")
    reason = environment["BUILD_REASON"]
    if reason not in {"PullRequest", "Manual"}:
        raise ValueError("Only policy PR and explicit manual events are adopted at 6.3")
    executed = transport.oid(environment["BUILD_SOURCEVERSION"])
    profile = "pr-integration" if reason == "PullRequest" else environment.get("SHADOW_PROFILE", "full-verification")
    if profile not in transport.PROFILES:
        raise ValueError("Unknown shadow profile")
    context = {
        "host": "ado",
        "event": reason,
        "repository": REPOSITORY,
        "profile": profile,
        "executed": executed,
        "source": executed,
        "base": "unavailable-manual-base",
        "scope": "hosted-commit",
        "checkout_kind": "source",
        "pr": None,
        "run_url": COLLECTION + PROJECT + "/_build/results?buildId=" + str(positive(environment["BUILD_BUILDID"])),
        "attempt": positive(environment.get("SYSTEM_JOBATTEMPT", "1")),
    }
    number = (
        environment.get("SYSTEM_PULLREQUEST_PULLREQUESTID")
        if reason == "PullRequest"
        else environment.get("SHADOW_PR_NUMBER")
    )
    if number:
        number = positive(number)
        if pull is None:
            raise ValueError("PR metadata is required; unknown execution cannot fall back")
        if (
            pull["pullRequestId"] != number
            or pull["status"] != "active"
            or pull["repository"]["id"] != REPOSITORY
            or pull["repository"]["project"]["id"] != PROJECT
            or pull["targetRefName"] != "refs/heads/" + transport.TARGET
            or not pull["sourceRefName"].startswith("refs/heads/")
            or pull.get("forkSource")
        ):
            raise ValueError("PR identity, status or approved repository/ref differs")
        source = transport.oid(pull["lastMergeSourceCommit"]["commitId"])
        base = transport.oid(pull["lastMergeTargetCommit"]["commitId"])
        merge = transport.oid(pull["lastMergeCommit"]["commitId"])
        if profile != "pr-integration":
            raise ValueError("PR replay requires full pr-integration")
        kind = "merge" if reason == "PullRequest" else "source"
        if executed != (merge if kind == "merge" else source):
            raise ValueError("Executed snapshot differs from corroborated PR source/merge")
        if reason == "PullRequest" and (
            environment["SYSTEM_PULLREQUEST_SOURCECOMMITID"] != source
            or environment["SYSTEM_PULLREQUEST_SOURCEBRANCH"] != pull["sourceRefName"]
            or environment["SYSTEM_PULLREQUEST_TARGETBRANCH"] != pull["targetRefName"]
            or environment["BUILD_SOURCEBRANCH"] != f"refs/pull/{number}/merge"
        ):
            raise ValueError("Policy variables and API merge metadata differ")
        context.update(source=source, base=base, scope="hosted-pr", checkout_kind=kind, pr=number)
    elif reason == "PullRequest":
        raise ValueError("Policy PR identity is missing")
    return context


def matrix(value):
    result = {}
    for row in value["include"]:
        key = re.sub(r"[^A-Za-z0-9_]", "_", row["shard"])
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,99}", key) or key in result:
            raise ValueError("Azure matrix identity is invalid or collides")
        result[key] = row
    if not result:
        # Azure requires a nonempty matrix. This transport marker is condition-skipped before
        # allocation and never represents a catalog shard, test, result or passing coverage.
        return {"NoWork": {"shard": "__no_work__", "os": "windows-2022", "timeout": 1}}
    return result


def output(**values):
    for name, value in values.items():
        if not re.fullmatch(r"[a-z_]+", name):
            raise ValueError("Invalid output variable name")
        if name in {"independent", "dependent"}:
            value = matrix(value)
        text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
        escaped = text.replace("%", "%AZP25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"##vso[task.setvariable variable={name};isOutput=true]{escaped}", flush=True)


def read_pull(environment):
    number = (
        environment.get("SYSTEM_PULLREQUEST_PULLREQUESTID")
        if environment["BUILD_REASON"] == "PullRequest"
        else environment.get("SHADOW_PR_NUMBER")
    )
    if not number:
        return None
    number = positive(number)
    # Fixed approved endpoint; never forward the token to an event-provided URL.
    request = urllib.request.Request(
        COLLECTION + PROJECT + f"/_apis/git/repositories/{REPOSITORY}/pullrequests/{number}?api-version=7.1",
        headers={"Authorization": "Bearer " + environment["SYSTEM_ACCESSTOKEN"]},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "evidence":
        out = transport.confined(transport.ROOT, ".tmp/ci-shadow/transport")
        out.mkdir(parents=True, exist_ok=False)
        bundle = transport.ROOT / ".tmp/ci-shadow/bundle"
        if bundle.exists():
            for owner in sorted(bundle.iterdir()):
                transport.export_bundle(owner, out / "bundle")
        for name in ("context.json", "tools.json", "failure.json"):
            source = transport.confined(transport.ROOT, ".tmp/ci-shadow/" + name)
            if source.is_file():
                shutil.copy2(source, out / name)
        source = transport.ROOT / ".tmp/ci-cache-pilot"
        if source.exists():
            shutil.copytree(source, out / "setup")
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "context":
        context = event_context(os.environ, read_pull(os.environ))
        transport.validate_context(transport.ROOT, context)
        output(context=context)
        return 0
    transport.output = output
    return transport.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.TimeoutExpired, StopIteration) as error:
        out = transport.ROOT / ".tmp/ci-shadow"
        out.mkdir(parents=True, exist_ok=True)
        (out / "failure.json").write_text(json.dumps({"status": "failed", "error": str(error)}), encoding="utf-8")
        print("Azure shadow failed: " + str(error), file=sys.stderr)
        raise SystemExit(1) from error
