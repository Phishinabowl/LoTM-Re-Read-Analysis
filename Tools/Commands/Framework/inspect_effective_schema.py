from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.effective_schema import (  # noqa: E402
    effective_schema_failure,
    effective_schema_json,
    load_effective_project_schema,
)
from knowledge_framework.project_config import resolve_project_root  # noqa: E402


SHOW_SECTIONS = ("packs", "capabilities", "namespaces", "content", "resources", "diagnostics")


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


def show_packs(document: dict) -> str:
    lines = [f"Selected Packs ({len(document['packs'])})"]
    for row in document["packs"]:
        lines.append(
            f"- {row['id']} | lifecycle={row['lifecycle']} | kind={row['kind']} | "
            f"schema={row['schema_version']} | version={row['pack_version']}"
        )
        lines.append(f"  label: {display_value(row['label'])}")
        lines.append(f"  description: {display_value(row['description'])}")
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


def show_capabilities(document: dict) -> str:
    lines = [f"Capabilities ({len(document['capabilities'])})"]
    for row in document["capabilities"]:
        provider_ids = ",".join(provider["pack_id"] for provider in row["providers"])
        lines.append(
            f"- {row['id']} | lifecycle={row['effective_lifecycle']} | available={display_value(row['available'])} "
            f"| enabled={display_value(row['enabled'])} | deprecated={display_value(row['deprecated'])} "
            f"| providers={provider_ids}"
        )
        for provider in row["providers"]:
            lines.append(
                f"  - {provider['pack_id']} | lifecycle={provider['lifecycle']} | "
                f"label={display_value(provider['label'])} | description={display_value(provider['description'])}"
            )
    return "\n".join(lines)


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
        candidates = SHOW_SECTIONS if value == "all" else (value,)
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
    return selected


def human_report(document: dict, sections: list[str]) -> str:
    blocks = [human_summary(document, include_diagnostic_rows="diagnostics" not in sections)]
    blocks.extend(SECTION_RENDERERS[section](document) for section in sections)
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
        "--show",
        action="append",
        default=[],
        metavar="SECTION",
        help=(
            "Append packs, capabilities, namespaces, content, resources, diagnostics, or all; "
            "repeat to combine sections."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        root = resolve_project_root(args.root, executable_path=Path(__file__))
        schema = load_effective_project_schema(root)
        document = schema.to_dict()
        serialized = effective_schema_json(schema)
        if args.output:
            output = resolve_output_path(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(serialized, encoding="utf-8", newline="\n")
        if args.json:
            sys.stdout.write(serialized)
        else:
            print(human_report(document, normalize_show_sections(args.show)))
            if args.output:
                print(f"Exported JSON: {output.relative_to(root).as_posix()}")
        return 0
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        if args.json:
            sys.stdout.write(json.dumps(effective_schema_failure(error), ensure_ascii=False, indent=2) + "\n")
        else:
            print(f"Effective-schema composition failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
