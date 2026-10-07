"""Display-only shard labels from catalog order and dependency waves."""

import re


def shard_presentation(plan):
    shards = sorted(plan["shards"], key=lambda row: (bool(row.get("depends_on", [])), row["order"]))
    result = []
    for index, shard in enumerate(shards, 1):
        identity = shard["id"]
        if identity.startswith(("conformance-python-", "conformance-powershell7-")):
            runtime = "Python" if identity.startswith("conformance-python-") else "PowerShell 7"
            prefix = "conformance-python-" if runtime == "Python" else "conformance-powershell7-"
            batches = [row for row in shards if row["id"].startswith(prefix)]
            batch = next(number for number, row in enumerate(batches, 1) if row["id"] == identity)
            title = f"{runtime} conformance (batch {batch} of {len(batches)})"
        elif identity.startswith("native-policy-"):
            title = "Policy and implementation tests"
        elif identity.startswith(("native-infrastructure-", "infrastructure-")):
            title = "CI infrastructure"
        elif identity.startswith("compatibility-"):
            title = "Project compatibility"
        elif identity.startswith("media-"):
            title = "Media helpers"
        elif identity.startswith("parity-"):
            title = "Cross-runtime parity"
        else:
            title = re.sub(r"-\d+$", "", identity).replace("-", " ").capitalize()
        result.append({"shard": identity, "number": index, "title": title, "display_name": f"{index:02d} — {title}"})
    return result
