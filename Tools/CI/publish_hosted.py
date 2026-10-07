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

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_LIMIT = 900 * 1024  # Below GitHub's 1 MiB per-step summary limit, including our notice.


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
        content = confined(owner, "summary.md").read_text(encoding="utf-8")
        content = content.split("\n## Artifacts\n", 1)[0] + native_failures(owner, manifest)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--shard", default=os.environ.get("SHADOW_SHARD", ""))
    args = parser.parse_args()
    context = decode_json(os.environ["SHADOW_CONTEXT"])
    destination, receipt = admit(Path(args.root).absolute(), context, args.shard)
    try:
        submit(destination, receipt, os.environ)
    except (OSError, KeyError) as error:
        receipt.update(status="failed", error="Markdown submission failed: " + str(error))
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
