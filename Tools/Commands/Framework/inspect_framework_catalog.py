from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


RUNTIME_ROOT = Path(__file__).resolve().parents[2] / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.framework_catalog import (  # noqa: E402
    compose_framework_catalog_selection,
    framework_catalog_failure,
    framework_catalog_json,
    load_framework_catalog,
)
from knowledge_framework.framework_paths import resolve_framework_root  # noqa: E402


SHOW_SECTIONS = ("overview", "packs", "capabilities")
ALL_SECTIONS = ("packs", "capabilities")


def resolve_output_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved == root or root not in resolved.parents:
        raise ValueError(f"Output path must resolve to a file beneath the framework root: {resolved}")
    return resolved


def display_value(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def human_summary(document: dict) -> str:
    summary = document["summary"]
    framework = document["framework"]
    return "\n".join(
        [
            f"Framework catalog: {framework['id']}",
            f"Contract: {document['contract']} v{document['contract_version']}",
            f"Manifest: {framework['manifest_path']}",
            f"Pack root: {framework['packs_root']}",
            f"Lookup registry: {framework['lookup_registry']} ({framework['unicode_version']})",
            f"Installed packs: {summary['pack_count']}",
            (
                "Capabilities: "
                f"{summary['capability_count']} declared, "
                f"{summary['available_capability_count']} available, "
                f"{summary['planned_capability_count']} planned, "
                f"{summary['deprecated_capability_count']} deprecated"
            ),
        ]
    )


def show_overview(document: dict) -> str:
    lines = [f"Installed Packs ({len(document['packs'])})"]
    for row in document["packs"]:
        presentation = row["presentation"]
        label = row["id"] if presentation is None else presentation["label"]
        description = "-" if presentation is None else presentation["short_description"]
        selectable = display_value(row["discoverability"]["selectable"])
        lines.append(f"- {label} ({row['id']}) | lifecycle={row['lifecycle']} | selectable={selectable}: {description}")
    return "\n".join(lines)


def append_presentation_entries(lines: list[str], label: str, entries: list[dict]) -> None:
    lines.append(f"  {label} ({len(entries)}):")
    if not entries:
        lines.append("    - none")
    for entry in entries:
        lines.append(f"    - {entry['id']} | {entry['label']}: {entry['description']}")


def render_pack_rows(rows: list[dict], heading: str) -> str:
    lines = [f"{heading} ({len(rows)})"]
    for row in rows:
        lines.append(
            f"- {row['id']} | lifecycle={row['lifecycle']} | kind={row['kind']} | "
            f"schema={row['schema_version']} | version={row['pack_version']} | "
            f"selectable={display_value(row['discoverability']['selectable'])}"
        )
        lines.append(f"  path: {row['path']}")
        classification = row["classification"]
        if classification is None:
            lines.append("  classification: legacy / unavailable")
        else:
            domains = ",".join(classification["domains"]) or "none"
            bridges = ",".join(classification["bridge_pack_ids"]) or "none"
            lines.append(
                f"  classification: family={classification['family']} | role={classification['role']} | "
                f"scope={classification['scope']} | domains={domains} | bridges={bridges}"
            )
        presentation = row["presentation"]
        if presentation is None:
            lines.append("  presentation: unavailable")
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
        lines.append(f"  dependencies ({len(row['dependencies'])}):")
        if not row["dependencies"]:
            lines.append("    - none")
        for dependency in row["dependencies"]:
            lines.append(
                f"    - {dependency['pack_id']} | minimum={dependency['minimum_version']} | "
                f"installed={dependency['installed_version']} | status={dependency['status']}"
            )
        lines.append(f"  capabilities ({len(row['capability_ids'])}):")
        lines.extend(f"    - {value}" for value in row["capability_ids"])
        lines.append(f"  controlled-value namespaces ({len(row['controlled_value_namespaces'])}):")
        if not row["controlled_value_namespaces"]:
            lines.append("    - none")
        for namespace in row["controlled_value_namespaces"]:
            lines.append(f"    - {namespace['id']} ({len(namespace['values'])})")
            for value in namespace["values"]:
                lines.append(
                    f"      - {value['id']} | broader={display_value(value['broader_value'])} | "
                    f"label={display_value(value['label'])} | description={display_value(value['description'])}"
                )
    return "\n".join(lines)


def show_packs(document: dict) -> str:
    return render_pack_rows(document["packs"], "Packs")


def render_capability_rows(rows: list[dict], heading: str) -> str:
    lines = [f"{heading} ({len(rows)})"]
    for row in rows:
        presentation = row["presentation"]
        label = row["id"] if presentation is None else presentation["label"]
        description = "-" if presentation is None else presentation["description"]
        lines.append(
            f"- {row['id']} | lifecycle={row['effective_lifecycle']} | "
            f"available={display_value(row['available'])} | deprecated={display_value(row['deprecated'])} | "
            f"planned={display_value(row['planned'])}"
        )
        lines.append(f"  label: {label}")
        lines.append(f"  description: {description}")
        if presentation is not None:
            lines.append(f"  presentation key: {presentation['localization_key']}")
        lines.append(f"  providers ({len(row['providers'])}):")
        for provider in row["providers"]:
            provider_presentation = provider["presentation"]
            provider_label = provider["pack_id"] if provider_presentation is None else provider_presentation["label"]
            lines.append(f"    - {provider['pack_id']} | lifecycle={provider['lifecycle']} | label={provider_label}")
    return "\n".join(lines)


def show_capabilities(document: dict) -> str:
    return render_capability_rows(document["capabilities"], "Capabilities")


SECTION_RENDERERS = {
    "overview": show_overview,
    "packs": show_packs,
    "capabilities": show_capabilities,
}


def normalize_show_sections(values: list[str]) -> list[str]:
    selected: list[str] = []
    for value in values:
        if value not in (*SHOW_SECTIONS, "all"):
            choices = ", ".join((*SHOW_SECTIONS, "all"))
            raise ValueError(f"Unknown framework-catalog section `{value}`; choose from: {choices}.")
        candidates = ALL_SECTIONS if value == "all" else (value,)
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
    return selected


def human_report(document: dict, sections: list[str], selection: dict | None = None) -> str:
    blocks = [human_summary(document)]
    blocks.extend(SECTION_RENDERERS[section](document) for section in sections)
    if selection is not None:
        if selection["packs"]:
            blocks.append(render_pack_rows(selection["packs"], "Pack Inspection"))
        if selection["capabilities"]:
            blocks.append(render_capability_rows(selection["capabilities"], "Capability Inspection"))
    return "\n\n".join(blocks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or export the generated project-independent FrameworkCatalog."
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Framework repository root. When omitted, searches from the current directory and script location.",
    )
    parser.add_argument("--json", action="store_true", help="Write canonical JSON to standard output.")
    parser.add_argument("--output", metavar="PATH", help="Also write canonical JSON beneath the framework root.")
    parser.add_argument(
        "--report-output",
        metavar="PATH",
        help="Write the selected human-readable report beneath the framework root.",
    )
    parser.add_argument(
        "--show",
        action="append",
        default=[],
        metavar="SECTION",
        help="Append overview, packs, capabilities, or all; repeat to combine sections.",
    )
    parser.add_argument("--pack", metavar="PACK_ID", help="Inspect one installed pack by stable ID.")
    parser.add_argument("--capability", metavar="CAPABILITY_ID", help="Inspect one capability by stable ID.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    classification = "root-discovery"
    root: Path | None = None
    try:
        root = resolve_framework_root(args.root, executable_path=Path(__file__))
        classification = "catalog-composition"
        catalog = load_framework_catalog(root)
        document = catalog.to_dict()
        selection = None
        if args.pack or args.capability:
            classification = "selector"
            selection = compose_framework_catalog_selection(
                catalog,
                pack_id=args.pack,
                capability_id=args.capability,
            )
        classification = "catalog-composition"
        serialized = (
            framework_catalog_json(catalog)
            if selection is None
            else json.dumps(selection, ensure_ascii=False, indent=2) + "\n"
        )
        sections = normalize_show_sections(args.show)
        if args.output:
            classification = "output-path"
            output = resolve_output_path(root, args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(serialized, encoding="utf-8", newline="\n")
        if args.report_output:
            classification = "output-path"
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
        classification = getattr(error, "classification", classification)
        if args.json:
            if classification == "root-discovery":
                message = "Framework root discovery failed."
            elif classification == "output-path":
                message = "Framework catalog output path is invalid."
            else:
                message = str(error)
                if root is not None:
                    message = message.replace(str(root), ".")
            sys.stdout.write(
                json.dumps(
                    framework_catalog_failure(error, classification, message=message),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            )
        else:
            print(f"Framework-catalog composition failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
