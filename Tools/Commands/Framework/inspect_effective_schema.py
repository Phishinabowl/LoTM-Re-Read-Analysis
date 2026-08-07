from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.effective_schema import (  # noqa: E402
    compose_effective_schema_selection,
    effective_schema_failure,
    effective_schema_json,
    load_effective_project_schema,
)
from knowledge_framework.lookup_key_config import load_lookup_key_config  # noqa: E402
from knowledge_framework.project_config import load_project_config, resolve_project_root  # noqa: E402


SHOW_SECTIONS = ("overview", "packs", "capabilities", "namespaces", "content", "resources", "diagnostics")
ALL_SECTIONS = ("packs", "capabilities", "namespaces", "content", "resources", "diagnostics")


def resolve_output_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Output path must remain inside the project root: {resolved}")
    return resolved


def display_value(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def human_summary(document: dict, *, include_diagnostic_rows: bool = True) -> str:
    capabilities = document["capabilities"]
    enabled = sum(row["enabled"] for row in capabilities)
    available = sum(row["available"] for row in capabilities)
    planned = sum(row["planned"] for row in capabilities)
    deprecated = sum(row["deprecated"] for row in capabilities)
    content = document["content"]
    resources = document["resources"]
    diagnostics = document["diagnostics"]
    lines = [
        f"Effective project schema: {document['project']['project_id']}",
        f"Contract: {document['contract']} v{document['contract_version']}",
        f"Framework/domain: {document['project']['framework_id']} / {document['project']['domain_id']}",
        f"Selected packs: {len(document['packs'])}",
        (
            "Capabilities: "
            f"{len(capabilities)} declared, {available} available, {enabled} enabled, "
            f"{planned} planned, {deprecated} deprecated"
        ),
        f"Controlled-value namespaces: {len(document['controlled_value_namespaces'])}",
        (
            "Content: "
            f"{len(content['roots'])} roots, {len(content['content_types'])} types, "
            f"{len(content['categories'])} categories"
        ),
        (
            "Resources: "
            f"{len(resources['roots'])} roots, {len(resources['kinds'])} kinds, "
            f"{len(resources['types'])} types"
        ),
        f"Diagnostics: {len(diagnostics)}",
    ]
    if include_diagnostic_rows:
        lines.extend(f"  [{row['severity']}] {row['code']}: {row['message']}" for row in diagnostics)
    return "\n".join(lines)


def append_presentation_entries(lines: list[str], label: str, entries: list[dict]) -> None:
    lines.append(f"  {label} ({len(entries)}):")
    if not entries:
        lines.append("    - none")
    for entry in entries:
        lines.append(f"    - {entry['id']} | {entry['label']}: {entry['description']}")


def show_overview(document: dict) -> str:
    lines = ["Pack And Capability Overview", f"Selected Packs ({len(document['packs'])})"]
    for row in document["packs"]:
        presentation = row["presentation"]
        label = presentation["label"] if presentation is not None else display_value(row["label"])
        description = (
            presentation["short_description"] if presentation is not None else display_value(row["description"])
        )
        lines.append(f"- {label} ({row['id']}): {description}")

    lines.append(f"Capabilities ({len(document['capabilities'])})")
    for row in document["capabilities"]:
        presentation = row["presentation"]
        if presentation is None:
            label = display_value(row["providers"][0]["label"])
            description = display_value(row["providers"][0]["description"])
        else:
            label = presentation["label"]
            description = presentation["description"]
        lines.append(f"- {label} ({row['id']}): {description}")
    return "\n".join(lines)


def render_pack_rows(rows: list[dict], heading: str) -> str:
    lines = [f"{heading} ({len(rows)})"]
    for row in rows:
        lines.append(
            f"- {row['id']} | lifecycle={row['lifecycle']} | kind={row['kind']} | "
            f"schema={row['schema_version']} | version={row['pack_version']}"
        )
        classification = row["classification"]
        if classification is None:
            lines.append("  classification: legacy / unavailable")
        else:
            domains = ",".join(classification["domains"]) or "none"
            joins = ",".join(classification["bridge_pack_ids"]) or "none"
            lines.append(
                f"  classification: family={classification['family']} | role={classification['role']} | "
                f"scope={classification['scope']} | domains={domains} | joins={joins}"
            )
        presentation = row["presentation"]
        if presentation is None:
            lines.append(f"  label: {display_value(row['label'])}")
            lines.append(f"  description: {display_value(row['description'])}")
        else:
            lines.append(
                f"  presentation: key={presentation['localization_key']} | "
                f"locale={presentation['default_locale']} | maturity={presentation['maturity']}"
            )
            lines.append(f"  label: {presentation['label']}")
            lines.append(f"  short description: {presentation['short_description']}")
            lines.append(f"  long description: {presentation['long_description']}")
            lines.append(f"  search keywords: {', '.join(presentation['search_keywords']) or 'none'}")
            visual = presentation["visual"]
            lines.append(
                "  visual: none"
                if visual is None
                else (
                    f"  visual: icon={display_value(visual['icon_id'])} | "
                    f"accent={display_value(visual['accent_token'])}"
                )
            )
            append_presentation_entries(lines, "intended audiences", presentation["intended_audiences"])
            append_presentation_entries(lines, "use cases", presentation["use_cases"])
            append_presentation_entries(lines, "examples", presentation["examples"])
            append_presentation_entries(lines, "prerequisites", presentation["prerequisites"])
            append_presentation_entries(lines, "provided behaviors", presentation["provided_behaviors"])
            append_presentation_entries(lines, "exclusions", presentation["exclusions"])
            lines.append(f"  documentation ({len(presentation['documentation'])}):")
            if not presentation["documentation"]:
                lines.append("    - none")
            for entry in presentation["documentation"]:
                lines.append(f"    - {entry['id']} | {entry['label']} | {entry['target_kind']}={entry['target']}")
        dependencies = row["dependencies"]
        if dependencies:
            values = ", ".join(
                f"{dependency['pack_id']}>=v{dependency['minimum_version']} "
                f"(selected v{dependency['selected_version']}, {dependency['status']})"
                for dependency in dependencies
            )
            lines.append(f"  dependencies: {values}")
        else:
            lines.append("  dependencies: none")
    return "\n".join(lines)


def show_packs(document: dict) -> str:
    return render_pack_rows(document["packs"], "Selected Packs")


def render_capability_rows(rows: list[dict], heading: str) -> str:
    lines = [f"{heading} ({len(rows)})"]
    for row in rows:
        provider_ids = ",".join(provider["pack_id"] for provider in row["providers"])
        lines.append(
            f"- {row['id']} | lifecycle={row['effective_lifecycle']} | available={display_value(row['available'])} "
            f"| enabled={display_value(row['enabled'])} | deprecated={display_value(row['deprecated'])} "
            f"| providers={provider_ids}"
        )
        presentation = row["presentation"]
        if presentation is None:
            lines.append("  presentation: legacy / unavailable")
        else:
            lines.append(f"  presentation key: {presentation['localization_key']}")
            lines.append(f"  label: {presentation['label']}")
            lines.append(f"  description: {presentation['description']}")
        for provider in row["providers"]:
            provider_presentation = provider["presentation"]
            lines.append(
                f"  - {provider['pack_id']} | lifecycle={provider['lifecycle']} | "
                f"label={display_value(provider['label'])} | description={display_value(provider['description'])}"
            )
            if provider_presentation is not None:
                lines.append(f"    presentation key: {provider_presentation['localization_key']}")
    return "\n".join(lines)


def show_capabilities(document: dict) -> str:
    return render_capability_rows(document["capabilities"], "Capabilities")


def show_namespaces(document: dict) -> str:
    namespaces = document["controlled_value_namespaces"]
    lines = [f"Controlled-Value Namespaces ({len(namespaces)})"]
    for namespace in namespaces:
        lines.append(f"- {namespace['id']} | values={len(namespace['values'])}")
        for row in namespace["values"]:
            lines.append(
                f"  - {row['id']} | owner={row['owner_pack_id']} | broader={display_value(row['broader_value_id'])} "
                f"| label={display_value(row['label'])} | description={display_value(row['description'])}"
            )
    return "\n".join(lines)


def show_content(document: dict) -> str:
    content = document["content"]
    lines = ["Content", f"Roots ({len(content['roots'])})"]
    for row in content["roots"]:
        lines.append(
            f"- {row['id']} | path={row['relative_path']} | provenance={row['provenance_mode']} "
            f"| label={display_value(row['provenance_label'])}"
        )
    lines.append(f"Content Types ({len(content['content_types'])})")
    for row in content["content_types"]:
        lines.append(
            f"- {row['id']} | lifecycle={row['lifecycle']} | root={display_value(row['content_root_id'])} "
            f"| categories={row['category_policy']} | graph={display_value(row['graph_enabled'])} "
            f"| qa={display_value(row['qa_page_enabled'])} | template={display_value(row['default_template'])}"
        )
    lines.append(f"Categories ({len(content['categories'])})")
    for row in content["categories"]:
        lines.append(
            f"- {row['id']} | lifecycle={row['lifecycle']} | graph_class={display_value(row['graph_class'])} "
            f"| placements={len(row['placements'])}"
        )
        for placement in row["placements"]:
            lines.append(
                f"  - {placement['content_type_id']} | folder={display_value(placement['relative_folder'])} "
                f"| template={display_value(placement['template'])}"
            )
    return "\n".join(lines)


def show_resources(document: dict) -> str:
    resources = document["resources"]
    lines = ["Resources", f"Roots ({len(resources['roots'])})"]
    for row in resources["roots"]:
        lines.append(f"- {row['id']} | path={row['relative_path']} | required={display_value(row['required'])}")
    lines.append(f"Kinds ({len(resources['kinds'])})")
    for row in resources["kinds"]:
        lines.append(f"- {row['id']} | label={row['label']} | plural={row['plural_label']}")
    lines.append(f"Types ({len(resources['types'])})")
    for row in resources["types"]:
        lines.append(
            f"- {row['id']} | lifecycle={row['lifecycle']} | kind={row['kind_id']} | authority={row['authority']} "
            f"| editor={display_value(row['editor_enabled'])} | placements={len(row['placements'])}"
        )
        for placement in row["placements"]:
            lines.append(
                f"  - {placement['root_id']} | path={placement['relative_path']} | tracking={placement['tracking']} "
                f"| required={display_value(placement['required'])}"
            )
    return "\n".join(lines)


def show_diagnostics(document: dict) -> str:
    lines = [f"Diagnostics ({len(document['diagnostics'])})"]
    if not document["diagnostics"]:
        lines.append("- none")
    for row in document["diagnostics"]:
        related_ids = ",".join(row["related_ids"]) or "-"
        lines.append(f"- [{row['severity']}] {row['code']} | path={display_value(row['path'])} | related={related_ids}")
        lines.append(f"  {row['message']}")
    return "\n".join(lines)


SECTION_RENDERERS = {
    "overview": show_overview,
    "packs": show_packs,
    "capabilities": show_capabilities,
    "namespaces": show_namespaces,
    "content": show_content,
    "resources": show_resources,
    "diagnostics": show_diagnostics,
}


def normalize_show_sections(values: list[str]) -> list[str]:
    selected: list[str] = []
    for value in values:
        if value not in (*SHOW_SECTIONS, "all"):
            choices = ", ".join((*SHOW_SECTIONS, "all"))
            raise ValueError(f"Unknown effective-schema section `{value}`; choose from: {choices}.")
        candidates = ALL_SECTIONS if value == "all" else (value,)
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
    return selected


def human_report(document: dict, sections: list[str], selection: dict | None = None) -> str:
    blocks = [human_summary(document, include_diagnostic_rows="diagnostics" not in sections)]
    blocks.extend(SECTION_RENDERERS[section](document) for section in sections)
    if selection is not None:
        if selection["packs"]:
            blocks.append(render_pack_rows(selection["packs"], "Pack Inspection"))
        if selection["capabilities"]:
            blocks.append(render_capability_rows(selection["capabilities"], "Capability Inspection"))
    return "\n\n".join(blocks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or export the generated EffectiveProjectSchema for a configured project."
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Project root. When omitted, searches from the current directory and script location.",
    )
    parser.add_argument("--json", action="store_true", help="Write canonical JSON to standard output.")
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Also write canonical JSON beneath the project root.",
    )
    parser.add_argument(
        "--report-output",
        metavar="PATH",
        help="Write the selected human-readable report beneath the project root.",
    )
    parser.add_argument(
        "--show",
        action="append",
        default=[],
        metavar="SECTION",
        help=(
            "Append overview, packs, capabilities, namespaces, content, resources, diagnostics, or all; "
            "repeat to combine sections."
        ),
    )
    parser.add_argument("--pack", metavar="PACK_ID", help="Inspect one selected pack by stable ID.")
    parser.add_argument(
        "--capability",
        metavar="CAPABILITY_ID",
        help="Inspect one declared capability by stable ID.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        root = resolve_project_root(args.root, executable_path=Path(__file__))
        schema = load_effective_project_schema(root)
        document = schema.to_dict()
        selection = None
        if args.pack or args.capability:
            project = load_project_config(root)
            selection = compose_effective_schema_selection(
                schema,
                load_lookup_key_config(project),
                pack_id=args.pack,
                capability_id=args.capability,
            )
        serialized = (
            effective_schema_json(schema)
            if selection is None
            else json.dumps(selection, ensure_ascii=False, indent=2) + "\n"
        )
        sections = normalize_show_sections(args.show)
        if args.output:
            output = resolve_output_path(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(serialized, encoding="utf-8", newline="\n")
        if args.report_output:
            report_output = resolve_output_path(root, args.report_output)
            report_output.parent.mkdir(parents=True, exist_ok=True)
            report_output.write_text(
                human_report(document, sections, selection) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        if args.json:
            sys.stdout.write(serialized)
        else:
            if not args.report_output:
                print(human_report(document, sections, selection))
            if args.output:
                print(f"Exported JSON: {output.relative_to(root).as_posix()}")
            if args.report_output:
                print(f"Exported report: {report_output.relative_to(root).as_posix()}")
        return 0
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        if args.json:
            sys.stdout.write(json.dumps(effective_schema_failure(error), ensure_ascii=False, indent=2) + "\n")
        else:
            print(f"Effective-schema composition failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
