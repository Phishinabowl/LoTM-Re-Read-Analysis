"""Conservative impact explanation. Execution membership always remains full."""

from functools import lru_cache
import re

from catalog import CatalogError
from scope import safe_path


def matches(pattern, path):
    safe_path(path)
    if not isinstance(pattern, str) or not pattern or any(char in pattern for char in "[]!\\:"):
        raise CatalogError("Unsupported impact glob grammar")
    segments = pattern.split("/")
    if any(part in ("", ".", "..") or ("**" in part and part != "**") for part in segments):
        raise CatalogError("Unsupported impact glob segments")
    parts = path.split("/")

    @lru_cache(None)
    def visit(left, right):
        if left == len(segments):
            return right == len(parts)
        if segments[left] == "**":
            return visit(left + 1, right) or (right < len(parts) and visit(left, right + 1))
        expression = "".join(
            "[^/]*" if char == "*" else "[^/]" if char == "?" else re.escape(char) for char in segments[left]
        )
        return right < len(parts) and re.fullmatch(expression, parts[right]) is not None and visit(left + 1, right + 1)

    return visit(0, 0)


def explain(plan, units, metadata, scope):
    candidates = [row["execution_id"] for row in plan["units"]]
    logical = {value.split("::")[0] for value in candidates}
    reasons = {value: [] for value in candidates}
    selected = set()
    fallback = list(scope["fallback_reasons"])
    rows = []
    for change in scope["changes"]:
        for path in dict.fromkeys(path for path in [change["old_path"], change["new_path"]] if path):
            impact = {
                identity
                for identity in logical
                if any(matches(pattern, path) for pattern in units[identity]["impact_paths"])
            }
            shared = [rule["reason"] for rule in metadata["full_selection_paths"] if matches(rule["pattern"], path)]
            exemptions = [rule for rule in metadata["non_impact_paths"] if matches(rule["pattern"], path)]
            if exemptions and (impact or shared):
                raise CatalogError("Conflicting impact/non-impact rules")
            if shared:
                fallback += ["shared infrastructure/content: " + path + " (" + "; ".join(shared) + ")"]
            elif not impact and not exemptions:
                fallback += ["unknown/incomplete impact mapping: " + path]
            rows.append(
                {
                    "path": path,
                    "impact_units": sorted(impact),
                    "shared_reasons": shared,
                    "non_impact_decisions": [rule["decision"] for rule in exemptions],
                    "policy_validation": "still required independently",
                }
            )
            for value in candidates:
                if value.split("::")[0] in impact:
                    selected.add(value)
                    reasons[value].append("changed path: " + path)
    if scope["changes"] and any(not units[identity]["impact_paths"] for identity in logical):
        fallback.append("unbounded candidate impact mapping")
    if fallback:
        selected = set(candidates)
        for value in candidates:
            reasons[value].append("conservative full-profile fallback")
    else:
        for value in plan["always_run"]:
            selected.add(value)
            reasons[value].append("always-run obligation")
        changed = True
        while changed:
            before = set(selected)
            selected_logical = {value.split("::")[0] for value in selected}
            for edge in metadata["dependencies"]:
                source_active = (
                    edge["source"] in selected_logical
                    if edge["source"] in units
                    else any(matches(edge["source"], row["path"]) for row in rows)
                )
                if source_active:
                    for value in candidates:
                        if value.split("::")[0] in edge["consumers"] and value not in selected:
                            selected.add(value)
                            reasons[value].append("transitive impact: " + edge["source"])
            for value in candidates:
                if value in selected:
                    for prerequisite in plan["units"][candidates.index(value)]["depends_on"]:
                        if prerequisite not in selected:
                            selected.add(prerequisite)
                            reasons[prerequisite].append("execution prerequisite for " + value)
                if units[value.split("::")[0]]["owner"] == "parity" and any(
                    source in selected for source in units[value.split("::")[0]]["source_units"]
                ):
                    if value not in selected:
                        selected.add(value)
                        reasons[value].append("complete parity runtime set")
            changed = selected != before
    dispositions = scope.get("policy_scope", {}).get("dispositions", [])
    policy_complete = {row["path"] for row in dispositions if row.get("validated") is True} >= {
        row["path"] for row in rows
    }
    no_impact = (
        not selected
        and not plan["required_reviews"]
        and not plan["always_run"]
        and all(row["non_impact_decisions"] for row in rows)
        and not fallback
        and policy_complete
    )
    if not selected and not no_impact:
        raise CatalogError("Zero selection cannot satisfy required policy/review obligations")
    return {
        "contract": "ci-impact-explanation",
        "contract_version": 1,
        "status": "explained",
        "advisory_no_impact": no_impact,
        "scope": scope,
        "profile": plan["profile"],
        "candidate_units": candidates,
        "would_select": [value for value in candidates if value in selected],
        "would_omit": [value for value in candidates if value not in selected],
        "reasons": reasons,
        "changed_path_dispositions": rows,
        "fallback_reasons": list(dict.fromkeys(fallback)),
        "effective_execution_units": candidates,
        "selection_enforced": False,
        "execution_ready": False,
    }
