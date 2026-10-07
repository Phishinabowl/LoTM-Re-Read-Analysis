"""Admit existing run evidence for host summaries and aggregate-only test publication."""

import argparse
import hashlib
import html
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

sys.dont_write_bytecode = True

from execution_reports import (
    atomic_bytes,
    confined,
    decode_json,
    encoded,
    excerpt,
    fingerprint,
    markdown_text,
    verify_publication,
)
from native_results import parse_junit
from presentation import shard_presentation

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_LIMIT = 900 * 1024  # Below GitHub's 1 MiB per-step summary limit, including our notice.


def check_name(identity):
    name = identity.split("/", 1)[-1].split("::", 1)[0]
    name = name.removeprefix("python-").removeprefix("powershell-")
    acronyms = {"ci": "CI", "qa": "QA", "api": "API", "epub": "EPUB"}
    return " ".join(acronyms.get(word, word.capitalize()) for word in name.split("-"))


def human_value(value):
    if value is None:
        return "Not recorded"
    if type(value) is bool:
        return "Yes" if value else "No"
    if isinstance(value, dict):
        return "; ".join(key.replace("_", " ") + ": " + human_value(item) for key, item in value.items())
    if isinstance(value, list):
        return "; ".join(human_value(item) for item in value) or "None"
    return str(value)


def readable_report(report):
    """Human hosted projection; original JSON/XML/Markdown remain immutable evidence."""
    selection, counts = report["selection"], report["counts"]
    guard, cleanup = report["canonical_guard"], report["cleanup"]

    def flag(value, positive, negative):
        return positive if value is True else negative if value is False else "Not recorded"

    def duration(value):
        return f"{value:.3f} s" if type(value) in (int, float) else "Not recorded"

    terminal = "; ".join(f"{value} {key}" for key, value in counts["terminal"].items() if value)
    lines = [
        "# CI execution: " + markdown_text(report["status"]),
        "",
        "**Profile:** " + markdown_text(report["profile"]),
        "",
        f"**Checks:** {terminal or 'None completed'}. "
        f"{counts['selected']} selected; {counts['unselected']} not selected.",
        "",
        "**Selection:** " + markdown_text(selection.get("applied_mode", "unknown")) + " profile.",
    ]
    native_rows = [row["native_counts"] for row in report["results"] if row["native_counts"] is not None]
    if native_rows:
        totals = {
            key: sum(row[key] for row in native_rows) for key in ("passed", "collected", "failed", "errors", "skipped")
        }
        lines += [
            "",
            f"**Recorded native tests:** {totals['passed']} / {totals['collected']} passed; "
            f"{totals['failed']} failed, {totals['errors']} errors, {totals['skipped']} skipped.",
        ]
    reasons = selection.get("fallback_reasons", [])
    if reasons:
        lines += ["", "**Selection reasons:**", ""]
        for reason in reasons:
            if isinstance(reason, str) and reason.startswith("comparison unavailable:"):
                lines += [
                    "- Changed-file comparison was unavailable.",
                    "",
                    "<details>",
                    "<summary>Selection diagnostic</summary>",
                    "",
                    markdown_text(reason),
                    "",
                    "</details>",
                ]
            else:
                lines += ["- " + markdown_text(reason)]
    else:
        lines += ["", "**Selection fallback:** None recorded."]
    collected = report["budget"].get("collection") is True
    label = "Aggregate collection time" if collected else "Execution time for this shard/run"
    lines += ["", f"**{label}:** {duration(report['budget'].get('elapsed_seconds'))}."]
    if collected:
        lines += [
            "",
            "Collection combines completed results; this is not the whole pipeline duration.",
            "",
            "**Sum of check durations:** " + duration(sum(row["elapsed_seconds"] for row in report["results"])) + ". "
            "Excludes agent queues, job environment setup and publication; may include overlapping work.",
        ]
    lines += [
        "",
        "**Canonical/source files:** " + flag(guard.get("unchanged"), "Unchanged", "Changes detected") + ".",
        "",
        "**Process cleanup:** " + flag(cleanup.get("verified"), "Verified", "Not verified") + ".",
    ]
    if "containment_verified" in guard:
        lines += ["", "**Containment:** " + flag(guard["containment_verified"], "Verified", "Not verified") + "."]
    if cleanup.get("external_scratch"):
        lines += ["", "**Temporary execution files:** " + markdown_text(cleanup["external_scratch"]) + "."]
    if cleanup.get("reason"):
        lines += ["", "**Evidence retention:** " + markdown_text(cleanup["reason"]) + "."]
    if guard.get("changed_paths"):
        lines += ["", "**Changed protected paths:**", ""]
        lines += ["- " + markdown_text(path) for path in guard["changed_paths"]]
    lines += [
        "",
        "## Results",
        "",
        "| Check | Runtime | Result | Duration | Native tests (passed / collected) | Notes |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in report["results"]:
        native = row["native_counts"]
        cases = "—" if native is None else f"{native['passed']} / {native['collected']}"
        runtime = {"python": "Python", "powershell7": "PowerShell 7"}.get(row["runtime"], row["runtime"])
        lines.append(
            f"| {markdown_text(check_name(row['id']))} | {markdown_text(runtime)} | "
            f"{markdown_text(row['status'])} | {duration(row['elapsed_seconds'])} | {cases} | "
            f"{markdown_text('; '.join(row['reasons']))} |"
        )
    for title, rows in (
        ("Unselected coverage", selection.get("unselected", [])),
        ("Retained reviews", report["reviews"]),
    ):
        if rows:
            lines += ["", "## " + title, ""]
            for row in rows:
                fields = row.items() if isinstance(row, dict) else [("Detail", row)]
                lines += [
                    "- "
                    + "; ".join(
                        markdown_text(key.replace("_", " ")) + ": " + markdown_text(human_value(value))
                        for key, value in fields
                    )
                ]
    if report["failures"]:
        lines += ["", "## Failures", ""]
        for failure in report["failures"]:
            text, truncated = excerpt(failure["excerpt"])
            lines += ["- " + markdown_text(f"{failure['id'] or 'run'} [{failure['classification']}]: {text}")]
            if truncated:
                lines += ["  Complete diagnostic retained in report.json."]
    lines += [
        "",
        "<details>",
        "<summary>Run provenance and stable check IDs</summary>",
        "",
        "Execution commit: " + markdown_text(report["provenance"].get("executed_commit", "unknown")),
        "",
        "Scope: " + markdown_text(report["provenance"].get("mode", "unknown")),
        "",
        "Run: " + markdown_text(report["run_id"]),
        "",
    ]
    lines += ["- " + markdown_text(row["id"]) for row in report["results"]]
    lines += [
        "",
        "</details>",
        "",
        "[Detailed JSON](report.json) · [Publication inventory](publication-manifest.json)",
        "",
    ]
    return "\n".join(lines)


def native_failures(owner, manifest):
    lines = []
    for entry in manifest["xml"]:
        if entry["identity"] == "ci-custom" or not (entry["counts"]["failed"] or entry["counts"]["errors"]):
            continue
        document, _, _ = parse_junit(confined(owner, entry["path"]))
        for case in document.iter("testcase"):
            node = next((item for item in case if item.tag in {"failure", "error"}), None)
            if node is None:
                continue
            if not lines:
                lines.extend(["\n## Native case failures\n", ""])
            text, truncated = excerpt(node.get("message", "") + "\n" + (node.text or ""))
            lines.extend(
                [
                    "- " + markdown_text(entry["identity"] + " / " + case.get("name", "unknown")),
                    "  " + markdown_text(text),
                    "  Complete native XML in artifact: <code>" + html.escape(entry["path"]) + "</code>.",
                    "  Diagnostic display truncated." if truncated else "",
                ]
            )
    return "\n".join(lines)


def hosted_markdown(content, run_url, artifact):
    # File links work inside the downloaded bundle, not inside either host's summary page.
    content = content.split("\n## Artifacts\n", 1)[0]
    content += "\n\n## Detailed artifacts\n\nComplete file inventory and diagnostics remain in the downloaded bundle.\n"
    for label, path in (("Detailed JSON", "report.json"), ("Publication inventory", "publication-manifest.json")):
        content = content.replace(f"[{label}]({path})", f"{label} (<code>{path}</code> in artifact)")
    header = f"[Hosted run and artifacts]({run_url}) · Download artifact `{artifact}`.\n\n"
    notice = "\n\nSummary display truncated; complete Markdown, JSON and diagnostics remain in the artifact.\n"
    data = (header + content).encode("utf-8")
    if len(data) > SUMMARY_LIMIT:
        data = data[: SUMMARY_LIMIT - len(notice.encode())].decode("utf-8", errors="ignore").encode() + notice.encode()
    return data


def admit(root, context, shard=""):
    """Stage exact admitted XML; never regenerate cases, scan raw XML, or alter execution outcomes."""
    destination = confined(root, ".tmp/ci-shadow/publication")
    destination.mkdir(parents=True, exist_ok=False)
    receipt = {
        "contract": "ci-host-publication",
        "contract_version": 1,
        "status": "failed",
        "host": context["host"],
        "shard": shard or None,
        "execution_exit_code": None,
        "xml": [],
        "markdown_submission": "not-submitted",
        "server_acceptance": "requires hosted task/run evidence",
    }
    try:
        host = context["host"]
        url = context["run_url"]
        prefix = "https://github.com/" if host == "github" else "https://dev.azure.com/DreamtechADO/"
        if host not in {"github", "ado"} or not url.startswith(prefix) or any(char in url for char in "\r\n()[]"):
            raise ValueError("Invalid hosted publication destination")
        if shard and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", shard):
            raise ValueError("Invalid publication shard identity")
        bundle = confined(root, ".tmp/ci-shadow/bundle")
        owners = list(bundle.iterdir()) if bundle.exists() else []
        if len(owners) != 1:
            raise ValueError("Publication requires exactly one current worker bundle; results missing or ambiguous")
        owner = confined(bundle, owners[0].name)
        manifest = verify_publication(owner)
        report = decode_json(confined(owner, "report.json").read_text(encoding="utf-8"))
        provenance = report["provenance"]
        if (
            report["profile"] != context["profile"]
            or provenance.get("executed_commit") != context["executed"]
            or provenance.get("shard_source", {}).get("shard", "") != shard
        ):
            raise ValueError("Publication profile/commit/shard differs from current execution")
        receipt.update(
            run_id=owner.name,
            execution_exit_code=manifest["execution_exit_code"],
            complete=manifest["complete"],
            manifest=fingerprint(owner, "publication-manifest.json"),
            summary_label=provenance.get("qualification_scenario", shard or "aggregate"),
        )
        if host == "github":
            artifact = f"ci-shadow-{'shard-' + shard if shard else 'aggregate-all'}-{context['attempt']}"
        else:
            build = parse_qs(urlsplit(url).query)["buildId"][0]
            if not re.fullmatch(r"[1-9][0-9]{0,8}", build):
                raise ValueError("Invalid Azure build identity")
            artifact = "ci-shadow-shard-" + shard if shard else "ci-shadow-aggregate-" + build
        content = readable_report(report) + native_failures(owner, manifest)
        atomic_bytes(destination, "summary.md", hosted_markdown(content, url, artifact))
        # Only the collected aggregate supplies test cases. Shard summaries never duplicate them.
        if not shard:
            for index, entry in enumerate(manifest["xml"]):
                identity = entry["identity"]
                if identity == "ci-custom":
                    category = "custom"
                elif identity.endswith("::python"):
                    category = "python"
                elif identity.endswith("::powershell7"):
                    category = "powershell"
                else:
                    raise ValueError("Unsupported XML runtime identity")
                if entry["counts"]["entries"] == 0:
                    continue
                target = f"xml/{category}-{index:04d}.xml"
                atomic_bytes(destination, target, confined(owner, entry["path"]).read_bytes())
                receipt["xml"].append(
                    {
                        **entry,
                        "source_path": entry["path"],
                        "path": target,
                        "category": category,
                        "staged_file": fingerprint(destination, target),
                    }
                )
        verify_publication(owner)
        receipt["status"] = "admitted"
    except (OSError, ValueError, KeyError, TypeError) as error:
        receipt["error"] = str(error)
        receipt["xml"] = []  # Partially staged bytes are diagnostic only, never task inputs.
        text = (
            "# CI publication failed\n\n"
            + html.escape(str(error))
            + "\n\nNo test coverage is inferred. Inspect worker logs and retained diagnostics.\n"
        )
        atomic_bytes(destination, "summary.md", text.encode("utf-8"), replace=(destination / "summary.md").exists())
    return destination, receipt


def submit(destination, receipt, environment):
    content = confined(destination, "summary.md").read_bytes()
    if receipt["host"] == "github":
        with open(environment["GITHUB_STEP_SUMMARY"], "ab") as stream:
            stream.write(content)
        receipt["markdown_submission"] = "written-to-host-summary-file"
    else:
        path = str(confined(destination, "summary.md"))
        escaped = path.replace("%", "%AZP25").replace("\r", "%0D").replace("\n", "%0A")
        label = receipt.get("summary_label", "publication-failure")
        if not isinstance(label, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", label):
            label = "publication-failure"
        suffix = hashlib.sha256(str(destination).encode("utf-8")).hexdigest()[:8]
        name = f"ci-{label}-{suffix}.md"
        # Name each attachment explicitly; multiple qualification summaries share one task record.
        print(f"##vso[task.addattachment type=Distributedtask.Core.Summary;name={name};]" + escaped, flush=True)
        receipt["summary_attachment_name"] = name
        receipt["markdown_submission"] = "logging-command-emitted"


def ordered_azure_summary(root, context, destination, receipt, plan):
    """Compose verified evidence in catalog order; Azure attachment order is not controllable."""
    downloads = confined(root, ".tmp/ci-shadow/downloads")
    paths = list(downloads.rglob("shard-result.json")) if downloads.exists() else []
    owners = {}
    for path in paths:
        owner = confined(downloads, path.parent.relative_to(downloads).as_posix())
        manifest = verify_publication(owner)
        envelope = decode_json(confined(owner, "shard-result.json").read_text(encoding="utf-8"))
        report = decode_json(confined(owner, "report.json").read_text(encoding="utf-8"))
        source = envelope["source"]
        identity = source["shard"]
        if (
            identity in owners
            or source["shard_plan"] != plan["id"]
            or source["profile"] != context["profile"]
            or report["profile"] != context["profile"]
            or report["provenance"]["executed_commit"] != context["executed"]
            or envelope["report"] != report
        ):
            raise ValueError("Ordered summary received duplicate or foreign shard evidence")
        owners[identity] = (owner, manifest, report)
    shards = shard_presentation(plan)
    expected = {row["shard"] for row in shards}
    if set(owners) - expected or (receipt["status"] == "admitted" and set(owners) != expected):
        raise ValueError("Ordered summary shard inventory differs from admitted aggregate")
    if receipt["status"] == "admitted":
        bundle = next(confined(root, ".tmp/ci-shadow/bundle").iterdir())
        aggregate = decode_json(confined(bundle, "report.json").read_text(encoding="utf-8"))
        if aggregate["selection"]["shard_sources"] != {key: value[2]["run_id"] for key, value in owners.items()}:
            raise ValueError("Ordered summary differs from collected shard owners")
    text = confined(destination, "summary.md").read_text(encoding="utf-8")
    text += "\n\n# Shard reports in execution-wave order\n\n"
    text += (
        "Aggregate above; expand a shard below. Catalog order is retained within each wave; "
        "dependent work follows independent work.\n"
    )
    for index, shard in enumerate(shards, 1):
        identity = shard["shard"]
        text += f"\n<details>\n<summary>{index:02d}. {html.escape(shard['title'])}</summary>\n\n"
        if identity in owners:
            owner, manifest, report = owners[identity]
            content = readable_report(report) + native_failures(owner, manifest)
            text += hosted_markdown(content, context["run_url"], "ci-shadow-shard-" + identity).decode("utf-8")
        else:
            text += "Shard evidence unavailable; no execution or passing coverage is inferred.\n"
        text += "\n</details>\n"
    data = text.encode("utf-8")
    if len(data) > SUMMARY_LIMIT:
        # Never cut a details element or silently omit a failed shard's bounded diagnostics.
        raise ValueError("Combined Azure summary exceeds the hosted display allowance; inspect retained artifacts")
    atomic_bytes(destination, "summary.md", data, replace=True)
    receipt["summary_label"] = "report"
    receipt["ordered_shards"] = [row["shard"] for row in shards]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--shard", default=os.environ.get("SHADOW_SHARD", ""))
    args = parser.parse_args()
    context = decode_json(os.environ["SHADOW_CONTEXT"])
    # Failed-job retries reuse Plan outputs, but artifact uploads belong to the current attempt.
    if context["host"] == "github" and "GITHUB_RUN_ATTEMPT" in os.environ:
        attempt = os.environ["GITHUB_RUN_ATTEMPT"]
        if not re.fullmatch(r"[1-9][0-9]{0,8}", attempt):
            raise ValueError("Invalid current GitHub run attempt")
        context["attempt"] = int(attempt)
    destination, receipt = admit(Path(args.root).absolute(), context, args.shard)
    try:
        if context["host"] == "ado":
            if args.shard:
                receipt["markdown_submission"] = "retained-in-shard-artifact"
            else:
                if receipt["status"] == "admitted":
                    from catalog import Catalog

                    plans = [
                        row
                        for row in Catalog(Path(args.root).absolute()).shard_plans.values()
                        if row["profile"] == context["profile"]
                    ]
                    if len(plans) != 1:
                        raise ValueError("Exactly one approved Azure report plan required")
                    ordered_azure_summary(Path(args.root).absolute(), context, destination, receipt, plans[0])
                submit(destination, receipt, os.environ)
        else:
            submit(destination, receipt, os.environ)
    except (OSError, KeyError, ValueError, TypeError) as error:
        receipt.update(status="failed", error="Markdown submission failed: " + str(error))
        if context["host"] == "ado" and not args.shard:
            try:
                # Retain a visible failure diagnostic even if composition rejects downloaded evidence.
                original = confined(destination, "summary.md").read_bytes()
                diagnostic = ("# CI report composition failed\n\n" + markdown_text(str(error)) + "\n\n").encode()
                atomic_bytes(destination, "summary.md", diagnostic + original, replace=True)
                receipt["summary_label"] = "report-failure"
                submit(destination, receipt, os.environ)
            except (OSError, KeyError, ValueError) as submission_error:
                receipt["error"] += "; diagnostic submission failed: " + str(submission_error)
    if receipt["host"] == "ado":
        from ado_shadow import output

        values = {}
        for category in ("python", "powershell", "custom"):
            paths = [
                confined(destination, row["path"]).as_posix() for row in receipt["xml"] if row["category"] == category
            ]
            values[category + "_files"] = "\n".join(paths) if receipt["status"] == "admitted" else ""
            values[category + "_enabled"] = "true" if values[category + "_files"] else "false"
        output(**values)
    atomic_bytes(destination, "receipt.json", encoded(receipt))
    print(f"Hosted publication {receipt['status']}; execution exit {receipt['execution_exit_code']}", flush=True)
    if receipt["status"] != "admitted":
        print(receipt.get("error", "Publication failed"), file=sys.stderr)
        return 1
    # This verifies/submits evidence; the earlier execution step retains its own exit code.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
