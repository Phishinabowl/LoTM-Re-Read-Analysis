#!/usr/bin/env python
"""Unified visualization workflow for Mermaid graph generation and rendering."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]

SLUG_PREFIXES = (
    "artifact",
    "character",
    "concept",
    "deity",
    "event",
    "faction",
    "item",
    "source",
    "location",
    "pathway",
    "tarot-card",
    "uniqueness",
)

SLUG_RE = re.compile(r"\b(?:" + "|".join(re.escape(prefix) for prefix in SLUG_PREFIXES) + r")-[a-z0-9][a-z0-9-]*\b")


@dataclass
class RenderSize:
    width: int
    height: int
    node_count: int
    edge_count: int
    complexity: int
    scale_steps: int
    max_fan_out: int
    fan_out_steps: int


def resolve_repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def setting(settings: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    value: Any = settings
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def get_mermaid_render_size(graph_path: Path, settings: dict[str, Any]) -> RenderSize:
    width = int(settings["width"])
    height = int(settings["height"])
    auto_size = settings.get("autoSize") or {}

    if not auto_size.get("enabled"):
        return RenderSize(width, height, 0, 0, 0, 0, 0, 0)

    node_ids: set[str] = set()
    edge_count = 0
    outgoing_counts: dict[str, int] = defaultdict(int)
    incoming_counts: dict[str, int] = defaultdict(int)

    for line in read_text(graph_path).splitlines():
        for match in re.finditer(r'(^|[\s])([A-Za-z0-9_]+)\s*(?:\["|\(|\{|\>)', line):
            node_ids.add(match.group(2))

        if re.search(r"\s-->|--\>|-.->|==>", line):
            edge_count += 1

        edge_match = re.match(r"^\s*([A-Za-z0-9_]+)\s*(?:-->|--\>|-.->|==>)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)", line)
        if edge_match:
            source, target = edge_match.group(1), edge_match.group(2)
            node_ids.update([source, target])
            outgoing_counts[source] += 1
            incoming_counts[target] += 1

    node_count = len(node_ids)
    complexity = node_count + edge_count
    unit = float(auto_size.get("complexityUnit") or 40.0)
    scale_steps = max(0, math.ceil(math.sqrt(complexity / unit)) - 1)

    width_step = int(auto_size.get("widthStep") or 1200)
    height_step = int(auto_size.get("heightStep") or 600)
    max_width = int(auto_size.get("maxWidth") or width)
    max_height = int(auto_size.get("maxHeight") or height)
    fan_out_threshold = int(auto_size.get("fanOutThreshold") or 6)
    fan_out_width_step = int(auto_size.get("fanOutWidthStep") or 900)

    max_fan_out = max([0, *outgoing_counts.values(), *incoming_counts.values()])
    fan_out_steps = max(0, math.ceil((max_fan_out - fan_out_threshold) / fan_out_threshold)) if fan_out_threshold > 0 else 0

    width = min(max_width, width + (scale_steps * width_step) + (fan_out_steps * fan_out_width_step))
    height = min(max_height, height + (scale_steps * height_step))
    return RenderSize(width, height, node_count, edge_count, complexity, scale_steps, max_fan_out, fan_out_steps)


def get_mermaid_class_validation(graph_path: Path, settings: dict[str, Any]) -> list[str]:
    declared_nodes: set[str] = set()
    used_nodes: set[str] = set()
    class_assignments: dict[str, set[str]] = defaultdict(set)
    class_defs: set[str] = set()
    issues: list[str] = []

    for line in read_text(graph_path).splitlines():
        match = re.match(r"^\s*classDef\s+([A-Za-z0-9_-]+)", line)
        if match:
            class_defs.add(match.group(1))
            continue

        match = re.match(r"^\s*class\s+(.+?)\s+([A-Za-z0-9_-]+)\s*;?\s*$", line)
        if match:
            class_name = match.group(2)
            for node_id in match.group(1).split(","):
                node_id = node_id.strip()
                if node_id:
                    class_assignments[node_id].add(class_name)
            continue

        for match in re.finditer(r'(^|[\s])([A-Za-z0-9_]+)\s*(?:\["|\(|\{|\>)', line):
            declared_nodes.add(match.group(2))
            used_nodes.add(match.group(2))

        for match in re.finditer(r"([A-Za-z0-9_]+)\s*(?:-->|--\>|-.->|==>)", line):
            used_nodes.add(match.group(1))

        for match in re.finditer(r"(?:-->|--\>|-.->|==>)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)", line):
            used_nodes.add(match.group(1))

    validation_settings = settings.get("classValidation") or {}
    graph_uses_classes = bool(class_defs or class_assignments)
    require_coverage = graph_uses_classes and validation_settings.get("requireClassesWhenGraphUsesClasses", True)

    if require_coverage:
        for node_id in sorted(used_nodes):
            if node_id not in class_assignments:
                issues.append(f"Node `{node_id}` is used but has no explicit class assignment.")

    for node_id in sorted(class_assignments):
        if node_id not in used_nodes and node_id not in declared_nodes:
            issues.append(f"Class assignment references missing node `{node_id}`.")
        for class_name in class_assignments[node_id]:
            if class_defs and class_name not in class_defs:
                issues.append(f"Node `{node_id}` uses undefined class `{class_name}`.")

    for rule in validation_settings.get("semanticPatterns") or []:
        class_name = rule.get("className")
        for node_id in sorted(used_nodes):
            if any(re.search(pattern, node_id) for pattern in rule.get("patterns") or []):
                if node_id not in class_assignments or class_name not in class_assignments[node_id]:
                    issues.append(f"Node `{node_id}` matches semantic class `{class_name}` but is not assigned to that class.")

    return issues


def assert_mermaid_class_validation(graph_path: Path, settings: dict[str, Any]) -> None:
    class_validation = settings.get("classValidation")
    if class_validation is not None and not class_validation.get("enabled", True):
        return

    issues = get_mermaid_class_validation(graph_path, settings)
    if issues:
        raise RuntimeError(f"Mermaid class validation failed for {graph_path}\n- " + "\n- ".join(issues))


def get_mermaid_layout_validation(graph_path: Path, settings: dict[str, Any]) -> list[str]:
    class_assignments: dict[str, set[str]] = defaultdict(set)
    class_defs: set[str] = set()
    node_labels: dict[str, str] = {}
    edges: list[dict[str, str]] = []
    subgraph_count = 0
    issues: list[str] = []

    for line in read_text(graph_path).splitlines():
        match = re.match(r"^\s*classDef\s+([A-Za-z0-9_-]+)", line)
        if match:
            class_defs.add(match.group(1))
            continue

        match = re.match(r"^\s*class\s+(.+?)\s+([A-Za-z0-9_-]+)\s*;?\s*$", line)
        if match:
            class_name = match.group(2)
            for node_id in match.group(1).split(","):
                node_id = node_id.strip()
                if node_id:
                    class_assignments[node_id].add(class_name)
            continue

        if re.match(r"^\s*subgraph\s+", line):
            subgraph_count += 1

        for match in re.finditer(r'(^|[\s])([A-Za-z0-9_]+)\s*\["([^"]+)"\]', line):
            node_labels[match.group(2)] = re.sub(r"\s+", " ", match.group(3).replace("<br/>", " ")).strip()

        edge_match = re.match(r"^\s*([A-Za-z0-9_]+)\s*(?:-->|--\>|-.->|==>)\s*(?:\|[^|]*\|\s*)?([A-Za-z0-9_]+)", line)
        if edge_match:
            edges.append({"Source": edge_match.group(1), "Target": edge_match.group(2)})

    layout_settings = settings.get("layoutValidation") or {}
    section_classes = layout_settings.get("sectionClassNames") or ["group"]
    cross_section_target_classes = layout_settings.get("crossSectionTargetClasses") or ["holder", "sequence"]
    duplicate_label_ignore_classes = layout_settings.get("duplicateLabelIgnoreClasses") or ["relationship"]
    proxy_node_patterns = layout_settings.get("proxyNodeIdPatterns") or [r"(^|_)ref(erence)?$", r"(^|_)proxy$", "_ref_", "_proxy_"]
    proxy_label_patterns = layout_settings.get("proxyLabelPatterns") or ["reference", "proxy", "see ", "reconstruction", "summary"]
    dense_graph_settings = layout_settings.get("denseGraphValidation")
    ordered_series_settings = layout_settings.get("orderedSeriesValidation")

    def has_any_class(node_id: str, class_names: list[str]) -> bool:
        return any(class_name in class_assignments.get(node_id, set()) for class_name in class_names)

    if dense_graph_settings and dense_graph_settings.get("enabled"):
        graph_node_ids = set(node_labels)
        for edge in edges:
            graph_node_ids.update([edge["Source"], edge["Target"]])

        min_node_count = int(dense_graph_settings.get("minNodeCount") or 20)
        if len(graph_node_ids) >= min_node_count:
            if dense_graph_settings.get("requireClassDefinitions") and not class_defs:
                issues.append(
                    f"Dense graph has {len(graph_node_ids)} nodes but no `classDef` styling. Use styled node classes so readers can distinguish groups, entities, relationships, evidence, uncertainty, and other semantic roles."
                )

            max_subgraph_count = int(dense_graph_settings.get("maxSubgraphCount", 4))
            if subgraph_count > max_subgraph_count:
                issues.append(
                    f"Dense graph uses {subgraph_count} Mermaid subgraph clusters. Dense knowledge maps should usually use styled group nodes and a connected semantic spine; reserve subgraph clusters for a few large regions or explicitly requested cluster views."
                )

            adjacency: dict[str, set[str]] = {node_id: set() for node_id in graph_node_ids}
            for edge in edges:
                adjacency.setdefault(edge["Source"], set()).add(edge["Target"])
                adjacency.setdefault(edge["Target"], set()).add(edge["Source"])

            visited: set[str] = set()
            component_count = 0
            for node_id in sorted(graph_node_ids):
                if node_id in visited:
                    continue
                component_count += 1
                queue: deque[str] = deque([node_id])
                visited.add(node_id)
                while queue:
                    current = queue.popleft()
                    for neighbor in adjacency.get(current, set()):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

            max_disconnected = int(dense_graph_settings.get("maxDisconnectedComponents", 2))
            if component_count > max_disconnected:
                issues.append(
                    f"Dense graph has {component_count} disconnected components. Dense knowledge maps should usually have a connected semantic spine, such as root -> group -> entity -> detail, unless the user explicitly requests separate disconnected diagrams."
                )

    labels_by_text: dict[str, list[str]] = defaultdict(list)
    for node_id, label in sorted(node_labels.items()):
        if has_any_class(node_id, duplicate_label_ignore_classes):
            continue
        if label:
            labels_by_text[label].append(node_id)

    for label, node_ids in sorted(labels_by_text.items()):
        unique_node_ids = sorted(set(node_ids))
        if len(unique_node_ids) > 1:
            issues.append(f"Duplicate visual label `{label}` appears on multiple node IDs: {', '.join(unique_node_ids)}. Use one canonical node or label local references/proxies explicitly.")

    for node_id, label in sorted(node_labels.items()):
        if not any(re.search(pattern, node_id) for pattern in proxy_node_patterns):
            continue
        if not any(re.search(pattern, label) for pattern in proxy_label_patterns):
            issues.append(f"Proxy/reference-like node `{node_id}` must label itself as a reference, proxy, reconstruction, summary, or `see ...` node. Current label: `{label}`.")

    for edge in edges:
        if not has_any_class(edge["Source"], section_classes):
            continue
        if not has_any_class(edge["Target"], cross_section_target_classes):
            continue
        other_incoming = [
            candidate
            for candidate in edges
            if candidate["Target"] == edge["Target"]
            and candidate["Source"] != edge["Source"]
            and not has_any_class(candidate["Source"], section_classes)
        ]
        if other_incoming:
            owners = ", ".join(sorted({candidate["Source"] for candidate in other_incoming}))
            issues.append(f"Section node `{edge['Source']}` links directly to `{edge['Target']}`, but `{edge['Target']}` already has non-section incoming owner(s): {owners}. Use a local reference/proxy node inside the section instead.")

    if ordered_series_settings and ordered_series_settings.get("enabled"):
        max_direct_children = int(ordered_series_settings.get("maxDirectChildren") or 2)
        child_label_patterns = ordered_series_settings.get("childLabelPatterns") or [
            r"^Seq\s*[0-9]",
            r"^Sequence\s*[0-9]",
            r"^Ch(?:apter)?\s*[0-9]",
            r"^Episode\s*[0-9]",
            r"^Step\s*[0-9]",
            r"^Phase\s*[0-9]",
            r"^Stage\s*[0-9]",
            r"^Rank\s*[0-9]",
            r"^Level\s*[0-9]",
        ]
        edges_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
        for edge in edges:
            edges_by_source[edge["Source"]].append(edge)
        for source, source_edges in edges_by_source.items():
            ordered_children = sorted(
                {
                    edge["Target"]
                    for edge in source_edges
                    if edge["Target"] in node_labels and any(re.search(pattern, node_labels[edge["Target"]]) for pattern in child_label_patterns)
                }
            )
            if len(ordered_children) > max_direct_children:
                issues.append(
                    f"Node `{source}` has {len(ordered_children)} direct ordered-series children: {', '.join(ordered_children)}. Ordered ladders, timelines, ranks, phases, chapters, steps, and sequences should usually chain child-to-child or use intermediate grouping nodes instead of wide sibling fan-out."
                )

    return issues


def assert_mermaid_layout_validation(graph_path: Path, settings: dict[str, Any]) -> None:
    layout_validation = settings.get("layoutValidation")
    if layout_validation is not None and not layout_validation.get("enabled", True):
        return

    issues = get_mermaid_layout_validation(graph_path, settings)
    if issues:
        raise RuntimeError(f"Mermaid layout validation failed for {graph_path}\n- " + "\n- ".join(issues))


def invoke_mermaid_render(input_path: Path, output_path: Path, settings: dict[str, Any], puppeteer_config: Path) -> None:
    assert_mermaid_class_validation(input_path, settings)
    assert_mermaid_layout_validation(input_path, settings)
    render_size = get_mermaid_render_size(input_path, settings)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mermaid_cli = shutil.which("mmdc") or shutil.which("mmdc.cmd") or shutil.which("mmdc.ps1")
    if not mermaid_cli:
        raise RuntimeError("Mermaid CLI executable not found on PATH: mmdc")

    command = [
        mermaid_cli,
        "-p",
        str(puppeteer_config),
        "-i",
        str(input_path),
        "-o",
        str(output_path),
        "-b",
        str(settings["background"]),
        "-w",
        str(render_size.width),
        "-H",
        str(render_size.height),
    ]
    if output_path.suffix.lower() == ".png":
        command += ["-s", str(settings["pngScale"])]

    print(
        "Rendering {0} -> {1} ({2}x{3}, nodes={4}, edges={5}, maxFanOut={6})".format(
            input_path,
            output_path,
            render_size.width,
            render_size.height,
            render_size.node_count,
            render_size.edge_count,
            render_size.max_fan_out,
        ),
        flush=True,
    )
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def convert_slug_to_node_id(slug: str) -> str:
    return Path(slug).stem.replace("-", "_")


def convert_slug_to_fallback_label(slug: str) -> str:
    name = re.sub(r"^(artifact|character|concept|deity|epoch|event|faction|family|item|source|location|mystery|pathway|tarot-card|timeline|uniqueness)-", "", Path(slug).stem)
    parts = [part for part in name.split("-") if part]
    label_parts = []
    for part in parts:
        if part.isdigit():
            label_parts.append(part)
        elif re.match(r"^[0-9]+_[0-9]+$", part):
            label_parts.append(part.replace("_", "-"))
        else:
            label_parts.append(part[:1].upper() + part[1:])
    return " ".join(label_parts)


def convert_node_id_to_fallback_label(node_id: str) -> str:
    return convert_slug_to_fallback_label(node_id.replace("_", "-"))


def read_glossary_nodes() -> dict[str, dict[str, str]]:
    nodes: dict[str, dict[str, str]] = {}
    root = resolve_repo_path("Glossary_Threads")
    for file_path in sorted(root.rglob("*.md")):
        if file_path.name == "TEMPLATE.md":
            continue
        slug = file_path.stem
        node_id = convert_slug_to_node_id(slug)
        label = None
        subject_visible_from = ""
        status = ""
        for line in read_text(file_path).splitlines():
            match = re.match(r"^#\s+(.+)$", line)
            if match:
                label = match.group(1).strip()
            if match := re.match(r"^Subject Visible From:\s*(.+?)\s*$", line):
                subject_visible_from = match.group(1).strip()
            if match := re.match(r"^Status:\s*(.+?)\s*$", line):
                status = match.group(1).strip().lower()
            if label and subject_visible_from and status:
                break
        nodes[node_id] = {
            "label": label or convert_slug_to_fallback_label(slug),
            "subject_visible_from": subject_visible_from,
            "status": status,
        }
    return nodes


def read_first_appearance_graph_displays() -> dict[str, list[dict[str, str]]]:
    displays: dict[str, list[dict[str, str]]] = defaultdict(list)
    root = resolve_repo_path("Glossary_Threads")
    display_index = 1
    for file_path in sorted(root.rglob("*.md")):
        if file_path.name == "TEMPLATE.md":
            continue
        note_slug = file_path.stem
        canonical_node_id = convert_slug_to_node_id(note_slug)
        text = read_text(file_path)
        relationship_block = extract_relationship_yaml(text)

        for block in fenced_yaml_blocks(text):
            if relationship_block and block == relationship_block:
                continue

            root_key = ""
            section_key = ""
            row: dict[str, str] | None = None
            graph_display: dict[str, str] = {}
            context = ""

            def finish_row() -> None:
                nonlocal row, graph_display, display_index, context
                if row is None:
                    return
                behavior = graph_display.get("behavior", "")
                label = graph_display.get("label", "")
                if behavior == "anonymized-node" and label:
                    medium = graph_display.get("visible_from_medium") or row.get("position_medium") or row.get("medium", "")
                    volume = graph_display.get("visible_from_volume") or row.get("position_volume", "")
                    chapter = graph_display.get("visible_from_chapter") or row.get("position_chapter", "")
                    season = graph_display.get("visible_from_season") or row.get("position_season", "")
                    episode = graph_display.get("visible_from_episode") or row.get("position_episode", "")
                    release_order = graph_display.get("visible_from_release_order") or row.get("position_release_order", "")
                    displays[canonical_node_id].append(
                        {
                            "node_id": f"anon_{display_index:03d}",
                            "canonical_node_id": canonical_node_id,
                            "label": label,
                            "behavior": behavior,
                            "medium": medium,
                            "volume": volume,
                            "chapter": chapter,
                            "season": season,
                            "episode": episode,
                            "release_order": release_order,
                            "resolves_medium": graph_display.get("resolves_to_canonical_at_medium", ""),
                            "resolves_volume": graph_display.get("resolves_to_canonical_at_volume", ""),
                            "resolves_chapter": graph_display.get("resolves_to_canonical_at_chapter", ""),
                            "resolves_season": graph_display.get("resolves_to_canonical_at_season", ""),
                            "resolves_episode": graph_display.get("resolves_to_canonical_at_episode", ""),
                            "resolves_release_order": graph_display.get("resolves_to_canonical_at_release_order", ""),
                        }
                    )
                    display_index += 1
                row = None
                graph_display = {}
                context = ""

            for raw_line in block.splitlines():
                if not raw_line.strip() or ":" not in raw_line:
                    continue
                indent = len(raw_line) - len(raw_line.lstrip(" "))
                line = raw_line.strip()

                if indent == 0 and not line.startswith("- "):
                    finish_row()
                    key, value = line.split(":", 1)
                    root_key = key.strip() if strip_yaml_scalar(value) == "" else ""
                    section_key = ""
                    continue

                if root_key and indent == 2 and not line.startswith("- "):
                    finish_row()
                    key, value = line.split(":", 1)
                    section_key = key.strip() if strip_yaml_scalar(value) == "" else ""
                    continue

                if root_key and section_key == "first_appearance_beats" and indent == 4 and line.startswith("- "):
                    finish_row()
                    row = {}
                    graph_display = {}
                    context = ""
                    line = line[2:].strip()
                    if ":" not in line:
                        continue

                if row is None or section_key != "first_appearance_beats":
                    continue

                key, value = line.split(":", 1)
                key = key.strip().lstrip("-").strip()
                value = strip_yaml_scalar(value)

                if indent == 4:
                    row[key] = value
                    context = ""
                elif indent == 6:
                    if key in {"position", "graph_display"}:
                        context = key
                        if key == "position":
                            for inline_key, inline_value in parse_inline_mapping(value).items():
                                row[f"position_{inline_key}"] = inline_value
                        continue
                    row[key] = value
                    context = ""
                elif indent >= 8:
                    if context == "position":
                        row[f"position_{key}"] = value
                    elif context == "graph_display":
                        if key in {"visible_from", "resolves_to_canonical_at"}:
                            for inline_key, inline_value in parse_inline_mapping(value).items():
                                graph_display[f"{key}_{inline_key}"] = inline_value
                        else:
                            graph_display[key] = value

            finish_row()

    return displays


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if value in {"", "null", "Null", "NULL"}:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_inline_mapping(value: str) -> dict[str, str]:
    value = strip_yaml_scalar(value)
    if not value.startswith("{") or not value.endswith("}"):
        return {}
    result: dict[str, str] = {}
    for part in value[1:-1].split(","):
        if ":" not in part:
            continue
        key, item_value = part.split(":", 1)
        result[key.strip()] = strip_yaml_scalar(item_value)
    return result


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def fenced_yaml_blocks(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"```yaml\s*(.*?)```", text, re.DOTALL)]


def extract_relationship_yaml(text: str) -> str:
    section = extract_section(text, "Relationship Seeds")
    match = re.search(r"```yaml\s*(.*?)```", section, re.DOTALL)
    return match.group(1).strip() if match else ""


def projection_slug(value: str) -> str:
    value = strip_yaml_scalar(value)
    if not value:
        return ""
    if SLUG_RE.fullmatch(value):
        return value
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def projection_keys_for_row(row: dict[str, str]) -> set[str]:
    keys: set[str] = set()
    for key in [
        "target",
        "ability",
        "event",
        "pathway",
        "organization",
        "item",
        "source_unit_id",
        "batch_id",
        "fragment_id",
        "label",
        "field",
        "entity",
        "uniqueness",
    ]:
        value = row.get(key, "")
        if not value:
            continue
        slug = projection_slug(value)
        if not slug:
            continue
        keys.add(slug)
        for prefix in SLUG_PREFIXES:
            keys.add(f"{prefix}-{slug}")
    return keys


def make_availability_entry(data: dict[str, str]) -> dict[str, str]:
    return {
        "medium": data.get("medium", ""),
        "volume": data.get("from_volume", "") or data.get("volume", ""),
        "chapter": data.get("from_chapter", "") or data.get("chapter", ""),
        "season": data.get("from_season", "") or data.get("season", ""),
        "episode": data.get("from_episode", "") or data.get("episode", ""),
        "release_order": data.get("from_release_order", "") or data.get("release_order", ""),
        "status": data.get("status", "") or data.get("possession_status", "") or data.get("outcome_status", ""),
        "confidence": data.get("confidence", ""),
        "graph_visibility": data.get("graph_visibility", ""),
        "display_source_label": data.get("display_source_label", ""),
        "display_target_label": data.get("display_target_label", ""),
        "display_relationship_type": data.get("display_relationship_type", ""),
    }


def read_data_projections() -> dict[str, list[dict[str, str]]]:
    projections: dict[str, list[dict[str, str]]] = {}
    root = resolve_repo_path("Glossary_Threads")
    for file_path in sorted(root.rglob("*.md")):
        if file_path.name == "TEMPLATE.md":
            continue
        note_slug = file_path.stem
        text = read_text(file_path)
        relationship_block = extract_relationship_yaml(text)
        for block in fenced_yaml_blocks(text):
            if relationship_block and block == relationship_block:
                continue

            root_key = ""
            section_key = ""
            row: dict[str, str] | None = None
            availability: list[dict[str, str]] = []
            availability_item: dict[str, str] | None = None
            in_availability = False
            in_from = False

            def finish_availability_item() -> None:
                nonlocal availability_item
                if availability_item is not None:
                    availability.append(make_availability_entry(availability_item))
                    availability_item = None

            def finish_row() -> None:
                nonlocal row, availability, availability_item, in_availability, in_from
                if row is None:
                    return
                finish_availability_item()
                if root_key and section_key and availability:
                    for key in projection_keys_for_row(row):
                        projection_source = f"{root_key}.{section_key}[{key}]"
                        projections[f"{note_slug}|{projection_source}"] = list(availability)
                        projections.setdefault(projection_source, list(availability))
                row = None
                availability = []
                availability_item = None
                in_availability = False
                in_from = False

            for raw_line in block.splitlines():
                if not raw_line.strip() or ":" not in raw_line:
                    continue
                indent = len(raw_line) - len(raw_line.lstrip(" "))
                line = raw_line.strip()

                if indent == 0 and not line.startswith("- "):
                    finish_row()
                    key, value = line.split(":", 1)
                    root_key = key.strip() if strip_yaml_scalar(value) == "" else ""
                    section_key = ""
                    continue

                if root_key and indent == 2 and not line.startswith("- "):
                    finish_row()
                    key, value = line.split(":", 1)
                    section_key = key.strip() if strip_yaml_scalar(value) == "" else ""
                    continue

                if root_key and section_key and indent == 4 and line.startswith("- "):
                    finish_row()
                    row = {}
                    line = line[2:].strip()
                    if ":" not in line:
                        continue

                if row is None:
                    continue

                key, value = line.split(":", 1)
                key = key.strip().lstrip("-").strip()
                value = strip_yaml_scalar(value)

                if indent == 4:
                    row[key] = value
                    in_availability = False
                    in_from = False
                elif indent == 6 and key != "availability" and not in_availability:
                    row[key] = value
                elif indent == 6 and key == "availability":
                    finish_availability_item()
                    in_availability = True
                    in_from = False
                elif indent == 8 and line.startswith("- "):
                    finish_availability_item()
                    availability_item = {}
                    if key:
                        availability_item[key] = value
                    in_availability = True
                    in_from = False
                elif in_availability and availability_item is not None:
                    if key == "from":
                        availability_item.update({f"from_{k}": v for k, v in parse_inline_mapping(value).items()})
                        in_from = True
                    elif in_from and indent >= 12:
                        availability_item[f"from_{key}"] = value
                    else:
                        availability_item[key] = value
                        in_from = False

            finish_row()
    return projections


def read_relationship_seeds() -> list[dict[str, str]]:
    relationships: list[dict[str, str]] = []
    root = resolve_repo_path("Glossary_Threads")
    for file_path in sorted(root.rglob("*.md")):
        if file_path.name == "TEMPLATE.md":
            continue

        in_section = False
        in_code = False
        current: dict[str, str] | None = None
        for line in read_text(file_path).splitlines():
            if line == "## Relationship Seeds":
                in_section = True
                continue
            if in_section and not in_code and re.match(r"^##\s+", line):
                break
            if not in_section:
                continue
            if re.match(r"^```", line):
                if in_code and current is not None:
                    relationships.append(current)
                    current = None
                in_code = not in_code
                continue
            if not in_code:
                continue

            match = re.match(r"^\s*-\s+source:\s*(.+?)\s*$", line)
            if match:
                if current is not None:
                    relationships.append(current)
                current = {
                    "source": match.group(1).strip(),
                    "target": "",
                    "relationship_type": "",
                    "medium": "",
                    "volume": "",
                    "chapter": "",
                    "status": "",
                    "confidence": "",
                    "projection_source": "",
                    "projection_scope": "",
                    "history_label": "",
                }
                continue
            if current is None:
                continue
            if match := re.match(r"^\s+target:\s*(.+?)\s*$", line):
                current["target"] = match.group(1).strip()
            elif match := re.match(r"^\s+relationship_type:\s*(.+?)\s*$", line):
                current["relationship_type"] = match.group(1).strip()
            elif not current["medium"] and (match := re.match(r"^\s+medium:\s*(.+?)\s*$", line)):
                current["medium"] = match.group(1).strip()
            elif not current["volume"] and (match := re.match(r"^\s+volume:\s*(.+?)\s*$", line)):
                current["volume"] = match.group(1).strip()
            elif not current["chapter"] and (match := re.match(r"^\s+chapter:\s*(.+?)\s*$", line)):
                current["chapter"] = match.group(1).strip()
            elif match := re.match(r"^\s+status:\s*(.+?)\s*$", line):
                current["status"] = match.group(1).strip()
            elif match := re.match(r"^\s+confidence:\s*(.+?)\s*$", line):
                current["confidence"] = match.group(1).strip()
            elif match := re.match(r"^\s+projection_source:\s*(.+?)\s*$", line):
                current["projection_source"] = match.group(1).strip()
            elif match := re.match(r"^\s+projection_scope:\s*(.+?)\s*$", line):
                current["projection_scope"] = match.group(1).strip()

        if in_section and in_code and current is not None:
            relationships.append(current)

    return [
        relationship
        for relationship in relationships
        if relationship["source"].strip() and relationship["target"].strip() and relationship["relationship_type"].strip()
    ]


def parse_boundary_number(value: str) -> int | None:
    value = str(value).strip()
    if value.isdigit():
        return int(value)
    return None


def parse_subject_visible_from(value: str) -> dict[str, int | str | None]:
    match = re.search(r"\bNovel\s+V(?:ol(?:ume)?)?\s*(\d+)\s+Ch(?:apter)?\s*(\d+)\b", value, re.I)
    if not match:
        return {"medium": "", "volume": None, "chapter": None}
    return {"medium": "novel", "volume": int(match.group(1)), "chapter": int(match.group(2))}


def position_is_visible(medium: str, volume: str | int | None, chapter: str | int | None, boundary: dict[str, Any]) -> bool:
    boundary_medium = str(boundary.get("medium") or "").strip().lower()
    if boundary_medium and str(medium or "").strip().lower() != boundary_medium:
        return False

    volume_number = parse_boundary_number(str(volume or ""))
    chapter_number = parse_boundary_number(str(chapter or ""))
    max_volume = boundary.get("maxVolume")
    max_chapter = boundary.get("maxChapter")

    if volume_number is None or chapter_number is None:
        return bool(boundary.get("includeUnknownPositions", False))
    if max_volume is not None and volume_number > int(max_volume):
        return False
    if max_volume is not None and max_chapter is not None and volume_number == int(max_volume) and chapter_number > int(max_chapter):
        return False
    return True


def filter_nodes_for_boundary(nodes: dict[str, dict[str, str]], boundary: dict[str, Any] | None) -> dict[str, str]:
    if not boundary:
        return {node_id: node["label"] for node_id, node in nodes.items()}

    filtered: dict[str, str] = {}
    for node_id, node in nodes.items():
        visible_from = node.get("subject_visible_from", "")
        if not visible_from:
            if boundary.get("includeUnknownSubjects", False):
                filtered[node_id] = node["label"]
            continue
        parsed = parse_subject_visible_from(visible_from)
        if position_is_visible(str(parsed["medium"]), parsed["volume"], parsed["chapter"], boundary):
            filtered[node_id] = node["label"]
    return filtered


def node_is_visible_at_boundary(node: dict[str, str], boundary: dict[str, Any] | None) -> bool:
    if not boundary:
        return True
    visible_from = node.get("subject_visible_from", "")
    if not visible_from:
        return bool(boundary.get("includeUnknownSubjects", False))
    parsed = parse_subject_visible_from(visible_from)
    return position_is_visible(str(parsed["medium"]), parsed["volume"], parsed["chapter"], boundary)


def graph_display_is_visible(display: dict[str, str], boundary: dict[str, Any] | None) -> bool:
    if not boundary:
        return False
    if not position_is_visible(display.get("medium", ""), display.get("volume", ""), display.get("chapter", ""), boundary):
        return False
    resolves_medium = display.get("resolves_medium", "")
    if resolves_medium and position_is_visible(resolves_medium, display.get("resolves_volume", ""), display.get("resolves_chapter", ""), boundary):
        return False
    return True


def get_anonymized_node_displays(
    nodes: dict[str, dict[str, str]],
    boundary: dict[str, Any] | None,
    first_appearance_displays: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str], dict[str, str]]:
    if not boundary:
        return {}, {}

    display_nodes: dict[str, str] = {}
    node_aliases: dict[str, str] = {}
    for canonical_node_id, displays in first_appearance_displays.items():
        node = nodes.get(canonical_node_id)
        if node and node_is_visible_at_boundary(node, boundary):
            continue
        visible_displays = [display for display in displays if graph_display_is_visible(display, boundary)]
        if not visible_displays:
            continue
        display = visible_displays[-1]
        display_nodes[display["node_id"]] = display["label"]
        node_aliases[canonical_node_id] = display["node_id"]
    return display_nodes, node_aliases


def availability_is_pinned(entry: dict[str, str]) -> bool:
    if entry.get("medium") == "novel":
        return bool(parse_boundary_number(entry.get("volume", "")) and parse_boundary_number(entry.get("chapter", "")))
    if entry.get("medium") == "donghua":
        return any(entry.get(key) and entry.get(key) != "TBD" for key in ["season", "episode", "release_order"])
    return False


def availability_entry_is_visible(entry: dict[str, str], boundary: dict[str, Any] | None) -> bool:
    if not availability_is_pinned(entry):
        return False
    if boundary and not position_is_visible(entry.get("medium", ""), entry.get("volume", ""), entry.get("chapter", ""), boundary):
        return False
    if entry.get("graph_visibility") == "hidden":
        return False
    return True


def format_availability_entry(entry: dict[str, str], timing_spoiler_free: bool) -> str:
    parts: list[str] = []
    if not timing_spoiler_free:
        if entry.get("medium") == "novel" and entry.get("chapter"):
            parts.append(f"ch{entry['chapter']}")
        elif entry.get("medium") == "donghua":
            if entry.get("season") and entry["season"] != "TBD":
                parts.append(f"s{entry['season']}")
            if entry.get("episode") and entry["episode"] != "TBD":
                parts.append(f"e{entry['episode']}")
    if entry.get("confidence") and entry["confidence"] != "confirmed":
        parts.append(entry["confidence"])
    elif entry.get("confidence") == "confirmed":
        parts.append("confirmed")
    elif entry.get("status") and entry["status"] not in {"active", "current-at-boundary"}:
        parts.append(entry["status"])
    return " ".join(parts)


def format_availability_history(entries: list[dict[str, str]], timing_spoiler_free: bool) -> str:
    visible_entries = [entry for entry in entries if availability_entry_is_visible(entry, None)]
    if not visible_entries:
        return ""
    by_medium: dict[str, list[str]] = defaultdict(list)
    for entry in visible_entries:
        if entry.get("medium") == "donghua" and not any(entry.get(key) and entry.get(key) != "TBD" for key in ["season", "episode", "release_order"]):
            continue
        line = format_availability_entry(entry, timing_spoiler_free)
        if line and line not in by_medium[entry.get("medium", "unknown")]:
            by_medium[entry.get("medium", "unknown")].append(line)
    lines = []
    for medium in sorted(by_medium):
        prefix = medium if not timing_spoiler_free else ""
        history = " -> ".join(by_medium[medium])
        lines.append(f"{prefix} {history}".strip())
    return "; ".join(lines)


def choose_current_availability(entries: list[dict[str, str]], boundary: dict[str, Any] | None) -> dict[str, str] | None:
    visible_entries = [entry for entry in entries if availability_entry_is_visible(entry, boundary)]
    if not visible_entries:
        return None
    return visible_entries[-1]


def relationship_strength(relationship: dict[str, str]) -> tuple[int, int, int, int]:
    has_projection = 1 if relationship.get("projection_source") else 0
    has_history = 1 if relationship.get("history_label") else 0
    canonical = 1 if relationship.get("projection_scope") == "canonical" else 0
    confidence_rank = {"confirmed": 3, "strong-evidence": 2, "strong-inference": 2, "clue": 1}.get(relationship.get("confidence", ""), 0)
    return (has_history, has_projection, canonical, confidence_rank)


def filter_relationships_for_boundary(
    relationships: list[dict[str, str]],
    boundary: dict[str, Any] | None,
    visible_node_ids: set[str] | None = None,
    known_node_ids: set[str] | None = None,
    data_projections: dict[str, list[dict[str, str]]] | None = None,
    timing_spoiler_free: bool = False,
    node_aliases: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    data_projections = data_projections or {}
    node_aliases = node_aliases or {}
    visible_node_ids = visible_node_ids or set()
    known_node_ids = known_node_ids or set()
    selected: dict[tuple[str, str, str], dict[str, str]] = {}

    for relationship in relationships:
        source_node = convert_slug_to_node_id(relationship["source"])
        target_node = convert_slug_to_node_id(relationship["target"])
        if visible_node_ids:
            hidden_known_endpoint = any(
                node_id not in visible_node_ids and node_id in known_node_ids and node_id not in node_aliases
                for node_id in [source_node, target_node]
            )
            if hidden_known_endpoint:
                continue

        rendered = dict(relationship)
        rendered["render_source_node"] = node_aliases.get(source_node, source_node)
        rendered["render_target_node"] = node_aliases.get(target_node, target_node)
        projection_source = relationship.get("projection_source", "")
        namespaced_projection_source = f"{relationship.get('source', '')}|{projection_source}"
        availability = data_projections.get(namespaced_projection_source) or data_projections.get(projection_source, [])
        if availability:
            current = choose_current_availability(availability, boundary)
            if current is None:
                continue
            rendered["medium"] = current.get("medium", rendered.get("medium", ""))
            rendered["volume"] = current.get("volume", rendered.get("volume", ""))
            rendered["chapter"] = current.get("chapter", rendered.get("chapter", ""))
            rendered["status"] = current.get("status", rendered.get("status", ""))
            rendered["confidence"] = current.get("confidence", rendered.get("confidence", ""))
            rendered["history_label"] = format_availability_history(
                [entry for entry in availability if availability_entry_is_visible(entry, boundary)],
                timing_spoiler_free,
            )
        elif boundary and not position_is_visible(rendered.get("medium", ""), rendered.get("volume", ""), rendered.get("chapter", ""), boundary):
            continue

        key = (rendered["render_source_node"], rendered["relationship_type"], rendered["render_target_node"])
        previous = selected.get(key)
        if previous is None or relationship_strength(rendered) > relationship_strength(previous):
            selected[key] = rendered

    return [selected[key] for key in sorted(selected)]


def get_missing_relationship_endpoints(relationships: list[dict[str, str]], known_node_ids: set[str]) -> set[str]:
    missing: set[str] = set()
    for relationship in relationships:
        for key in ["source", "target"]:
            node_id = convert_slug_to_node_id(relationship[key])
            if node_id not in known_node_ids:
                missing.add(node_id)
    return missing


def format_relationship_label(
    relationship: dict[str, str],
    timing_spoiler_free: bool,
    include_confirmed_confidence: bool = False,
) -> str:
    parts = [relationship["relationship_type"]]
    if relationship.get("history_label"):
        parts.append(relationship["history_label"])
        return " ".join(parts)
    if not timing_spoiler_free and relationship.get("chapter"):
        parts.append(f"ch{relationship['chapter']}")
    if relationship.get("status") and relationship["status"] != "active":
        parts.append(relationship["status"])
    if relationship.get("confidence") and (include_confirmed_confidence or relationship["confidence"] != "confirmed"):
        parts.append(relationship["confidence"])
    return " ".join(parts)


def format_relationship_node_label(
    relationship: dict[str, str],
    timing_spoiler_free: bool,
    include_confirmed_confidence: bool = False,
) -> str:
    if relationship.get("history_label"):
        parts = [relationship["relationship_type"], relationship["history_label"]]
        return "<br/>".join(part.replace('"', r"\"") for part in parts)
    return format_relationship_label(relationship, timing_spoiler_free, include_confirmed_confidence).replace(" ", "<br/>", 1) if False else "<br/>".join(
        part.replace('"', r"\"") for part in format_relationship_label(relationship, timing_spoiler_free, include_confirmed_confidence).split(" ")
    )


def write_mermaid_graph(
    graph_path: Path,
    nodes: dict[str, str],
    relationships: list[dict[str, str]],
    timing_spoiler_free: bool,
    known_node_ids: set[str] | None = None,
    pending_node_ids: set[str] | None = None,
    pending_endpoint_node_ids: set[str] | None = None,
    include_confirmed_confidence: bool = False,
) -> None:
    known = set(nodes) if known_node_ids is None else set(known_node_ids) | set(nodes)
    pending_node_ids = pending_node_ids or set()
    pending_endpoint_node_ids = pending_endpoint_node_ids or set()
    missing_endpoint_nodes: set[str] = set()
    for relationship in relationships:
        source = relationship.get("render_source_node") or convert_slug_to_node_id(relationship["source"])
        target = relationship.get("render_target_node") or convert_slug_to_node_id(relationship["target"])
        if source not in known:
            missing_endpoint_nodes.add(source)
        if target not in known:
            missing_endpoint_nodes.add(target)
        nodes.setdefault(source, convert_node_id_to_fallback_label(source))
        nodes.setdefault(target, convert_node_id_to_fallback_label(target))

    lines = ["graph TD"]
    for node_id in sorted(nodes):
        label = nodes[node_id].replace('"', r"\"")
        lines.append(f'  {node_id}["{label}"]')

    lines += [
        "",
        "  classDef artifact fill:#f3ead7,stroke:#b7791f,stroke-width:2px,color:#1f2937",
        "  classDef character fill:#ecebff,stroke:#7c5cff,stroke-width:2px,color:#1f2937",
        "  classDef concept fill:#e8f5f0,stroke:#2f855a,stroke-width:2px,color:#1f2937",
        "  classDef deity fill:#fae8ff,stroke:#c026d3,stroke-width:2px,color:#1f2937",
        "  classDef epoch fill:#ede9fe,stroke:#6d28d9,stroke-width:2px,color:#1f2937",
        "  classDef event fill:#fff1f2,stroke:#e11d48,stroke-width:2px,color:#1f2937",
        "  classDef faction fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#1f2937",
        "  classDef family fill:#fce7f3,stroke:#be185d,stroke-width:2px,color:#1f2937",
        "  classDef item fill:#ecfccb,stroke:#65a30d,stroke-width:2px,color:#1f2937",
        "  classDef source fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#1f2937",
        "  classDef location fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1f2937",
        "  classDef mystery fill:#e5e7eb,stroke:#4b5563,stroke-width:2px,color:#1f2937",
        "  classDef pathway fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#1f2937",
        "  classDef tarot fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#1f2937",
        "  classDef timeline fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1f2937",
        "  classDef uniqueness fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#1f2937",
        "  classDef missingEndpoint fill:#f8fafc,stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3,color:#1f2937",
        "  classDef pendingNode stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3",
        "  classDef pendingEndpoint fill:#f8fafc,stroke:#64748b,stroke-width:2px,stroke-dasharray:4 3,color:#1f2937",
        "  classDef anonymizedNode fill:#f8fafc,stroke:#475569,stroke-width:2px,stroke-dasharray:6 3,color:#1f2937",
        "  classDef relationship fill:#f7f2e9,stroke:#c69245,stroke-width:1.5px,color:#1f2937",
        "",
    ]
    for node_id in sorted(nodes):
        if re.match(r"^anon_[0-9]+$", node_id):
            lines.append(f"  class {node_id} anonymizedNode")
            continue
        if node_id in missing_endpoint_nodes:
            class_name = "pendingEndpoint" if node_id in pending_endpoint_node_ids else "missingEndpoint"
            lines.append(f"  class {node_id} {class_name}")
            continue
        class_name = node_id.split("_")[0]
        if class_name in {
            "artifact",
            "character",
            "concept",
            "deity",
            "epoch",
            "event",
            "faction",
            "family",
            "item",
            "source",
            "location",
            "mystery",
            "pathway",
            "tarot",
            "timeline",
            "uniqueness",
        }:
            lines.append(f"  class {node_id} {class_name}")
        if node_id in pending_node_ids:
            lines.append(f"  class {node_id} pendingNode")

    lines.append("")
    seen_edges: set[str] = set()
    edges: list[dict[str, str]] = []
    for relationship in relationships:
        source = relationship.get("render_source_node") or convert_slug_to_node_id(relationship["source"])
        target = relationship.get("render_target_node") or convert_slug_to_node_id(relationship["target"])
        label = format_relationship_label(relationship, timing_spoiler_free, include_confirmed_confidence)
        key = f"{source}|{label}|{target}"
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": source, "target": target, "label": label, "nodeLabel": format_relationship_node_label(relationship, timing_spoiler_free, include_confirmed_confidence)})

    for index, edge in enumerate(sorted(edges, key=lambda item: (item["source"], item["target"], item["label"])), start=1):
        relationship_id = f"rel_{index:03d}"
        lines.append(f'  {relationship_id}["{edge["nodeLabel"]}"]')
        lines.append(f"  class {relationship_id} relationship")
        lines.append(f'  {edge["source"]} --> {relationship_id}')
        lines.append(f'  {relationship_id} --> {edge["target"]}')

    write_text(graph_path, "\n".join(lines) + "\n")


def update_mermaid_graphs(views: list[dict[str, Any]]) -> None:
    nodes = read_glossary_nodes()
    relationships = read_relationship_seeds()
    data_projections = read_data_projections()
    first_appearance_displays = read_first_appearance_graph_displays()
    pending_node_ids = {node_id for node_id, node in nodes.items() if node.get("status") == "pending"}
    for view in views:
        graph_path = resolve_repo_path(view["input"])
        timing_spoiler_free = "timing-spoiler-free" in view["input"]
        boundary = view.get("readerBoundary")
        view_nodes = filter_nodes_for_boundary(nodes, boundary)
        anonymized_nodes, node_aliases = get_anonymized_node_displays(nodes, boundary, first_appearance_displays)
        view_nodes.update(anonymized_nodes)
        view_relationships = filter_relationships_for_boundary(
            relationships,
            boundary,
            set(view_nodes),
            set(nodes),
            data_projections,
            timing_spoiler_free,
            node_aliases,
        )
        pending_endpoint_node_ids = get_missing_relationship_endpoints(view_relationships, set(nodes))
        write_mermaid_graph(
            graph_path,
            dict(view_nodes),
            view_relationships,
            timing_spoiler_free,
            set(nodes),
            pending_node_ids & set(view_nodes),
            pending_endpoint_node_ids,
        )


def get_graph_stats(graph_path: Path) -> dict[str, Any]:
    nodes: set[str] = set()
    linked: set[str] = set()
    edges: list[dict[str, str]] = []
    relationship_labels: dict[str, str] = {}
    relationship_sources: dict[str, str] = {}
    relationship_targets: dict[str, str] = {}

    for line in read_text(graph_path).splitlines():
        if match := re.match(r'^\s+([A-Za-z0-9_]+)\["(.+)"\]', line):
            node_id, label = match.group(1), match.group(2)
            if re.match(r"^rel_[0-9]+$", node_id):
                relationship_labels[node_id] = re.sub(r"\s+", " ", label.replace("<br/>", " ").replace(r"\"", '"')).strip()
            else:
                nodes.add(node_id)
            continue

        if match := re.match(r"^\s+([A-Za-z0-9_]+)\s+-->\|([^|]+)\|\s+([A-Za-z0-9_]+)", line):
            source, label, target = match.group(1), match.group(2).strip(), match.group(3)
            edges.append({"source": source, "target": target, "label": label, "key": f"{source}|{label}|{target}", "endpointKey": f"{source}|{target}"})
            linked.update([source, target])
            continue

        if match := re.match(r"^\s+([A-Za-z0-9_]+)\s+-->\s+(rel_[0-9]+)", line):
            relationship_sources[match.group(2)] = match.group(1)
            continue

        if match := re.match(r"^\s+(rel_[0-9]+)\s+-->\s+([A-Za-z0-9_]+)", line):
            relationship_targets[match.group(1)] = match.group(2)
            continue

    for relationship_id, label in relationship_labels.items():
        if relationship_id not in relationship_sources or relationship_id not in relationship_targets:
            continue
        source = relationship_sources[relationship_id]
        target = relationship_targets[relationship_id]
        edges.append({"source": source, "target": target, "label": label, "key": f"{source}|{label}|{target}", "endpointKey": f"{source}|{target}"})
        linked.update([source, target])

    return {"NodeIds": sorted(nodes), "Relationships": sorted(edges, key=lambda item: item["key"]), "OrphanNodes": sorted(nodes - linked)}


def read_previous_snapshot(snapshot_path: Path) -> dict[str, Any] | None:
    if not snapshot_path.exists():
        return None
    return json.loads(read_text(snapshot_path))


def compare_string_set(previous: list[str], current: list[str]) -> dict[str, list[str]]:
    previous_set = {item for item in previous if item and item.strip()}
    current_set = {item for item in current if item and item.strip()}
    return {"Added": sorted(current_set - previous_set), "Removed": sorted(previous_set - current_set)}


def get_duplicate_relationships(relationships: list[dict[str, str]]) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for relationship in relationships:
        counts[relationship["key"]] += 1
    return sorted(f"{key} x{count}" for key, count in counts.items() if count > 1)


def get_changed_relationships(previous_relationships: list[dict[str, str]], current_relationships: list[dict[str, str]]) -> list[dict[str, str]]:
    previous_by_endpoint: dict[str, set[str]] = defaultdict(set)
    current_by_endpoint: dict[str, set[str]] = defaultdict(set)
    for relationship in previous_relationships:
        previous_by_endpoint[relationship["endpointKey"]].add(relationship["label"])
    for relationship in current_relationships:
        current_by_endpoint[relationship["endpointKey"]].add(relationship["label"])

    changes: list[dict[str, str]] = []
    for endpoint, current_labels in current_by_endpoint.items():
        if endpoint not in previous_by_endpoint:
            continue
        previous_labels = sorted(previous_by_endpoint[endpoint])
        current_labels_sorted = sorted(current_labels)
        if previous_labels != current_labels_sorted:
            source, target = endpoint.split("|", 1)
            changes.append({"source": source, "target": target, "previous": "; ".join(previous_labels), "current": "; ".join(current_labels_sorted)})
    return sorted(changes, key=lambda item: (item["source"], item["target"]))


def get_pending_graph_nodes() -> list[str]:
    state_path = resolve_repo_path("CURRENT_STATE.md")
    pending: list[str] = []
    in_section = False
    for line in read_text(state_path).splitlines():
        if line == "### Deferred Graph Nodes":
            in_section = True
            continue
        if in_section and re.match(r"^###\s+", line):
            break
        if in_section and (match := re.match(r"^-\s+(.+)$", line)):
            pending.append(match.group(1).strip().replace("](Investigations/", "](../Investigations/"))
    return pending


def get_broken_markdown_links() -> list[str]:
    broken: list[str] = []
    for file_path in sorted(REPO_ROOT.rglob("*.md")):
        full_name = str(file_path)
        if f"{os.sep}.git{os.sep}" in full_name or f"{os.sep}Source{os.sep}" in full_name or file_path.name == "TEMPLATE.md":
            continue
        text = read_text(file_path)
        for match in re.finditer(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
            target = match.group(1).strip().strip("<>")
            if re.match(r"^(https?:|mailto:)", target):
                continue
            target_path = file_path.parent / unquote(target)
            if not target_path.exists():
                try:
                    relative_target = target_path.resolve().relative_to(REPO_ROOT)
                    if relative_target.parts and relative_target.parts[0] == "Glossary_Threads":
                        continue
                except ValueError:
                    pass
                broken.append(f".\\{file_path.relative_to(REPO_ROOT)} -> {target}")
    return broken


def format_snapshot_delta(previous_snapshot: dict[str, Any] | None, previous_value: int, current_value: int) -> str:
    if previous_snapshot is None:
        return "n/a"
    delta = current_value - previous_value
    return f"+{delta}" if delta > 0 else str(delta)


def update_report_section(report_path: Path, report_lines: list[str]) -> None:
    start_marker = "<!-- VISUALIZATION-REFRESH-REPORT:START -->"
    end_marker = "<!-- VISUALIZATION-REFRESH-REPORT:END -->"
    replacement = "\n".join([start_marker, *report_lines, end_marker]) + "\n"

    if not report_path.exists():
        write_text(report_path, replacement)
        return

    content = read_text(report_path)
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if pattern.search(content):
        write_text(report_path, pattern.sub(lambda _: replacement.rstrip("\n"), content))
    else:
        write_text(report_path, content.rstrip() + "\n\n" + replacement)


def invoke_refresh_mode(settings: dict[str, Any], puppeteer_config: Path, skip_render: bool) -> None:
    update_mermaid_graphs(settings["views"])

    if not skip_render:
        for view in settings["views"]:
            for output in view["outputs"]:
                invoke_mermaid_render(resolve_repo_path(view["input"]), resolve_repo_path(output), settings, puppeteer_config)

    view_stats: list[dict[str, Any]] = []
    for view in settings["views"]:
        graph_stats = get_graph_stats(resolve_repo_path(view["input"]))
        view_stats.append(
            {
                "name": view["name"],
                "input": view["input"],
                "nodes": graph_stats["NodeIds"],
                "relationships": [
                    {key: relationship[key] for key in ["source", "target", "label", "key", "endpointKey"]}
                    for relationship in graph_stats["Relationships"]
                ],
                "orphan_nodes": graph_stats["OrphanNodes"],
            }
        )

    primary_view = view_stats[0]
    pending_nodes = get_pending_graph_nodes()
    broken_links = get_broken_markdown_links()
    rendered_files = [output for view in settings["views"] for output in view["outputs"] if resolve_repo_path(output).exists()]

    report_path = resolve_repo_path(settings["reportPath"])
    snapshot_path = resolve_repo_path(settings["snapshotPath"])
    previous_snapshot = read_previous_snapshot(snapshot_path)
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    timestamp = timestamp[:-2] + ":" + timestamp[-2:]

    snapshot = {
        "generated_at": timestamp,
        "nodes": primary_view["nodes"],
        "relationships": primary_view["relationships"],
        "views": [view["name"] for view in settings["views"]],
        "view_stats": view_stats,
        "rendered_files": rendered_files,
        "broken_links": broken_links,
        "orphan_nodes": primary_view["orphan_nodes"],
        "pending_nodes": pending_nodes,
    }

    def previous_count(key: str) -> int:
        return 0 if previous_snapshot is None else len(previous_snapshot.get(key) or [])

    previous_view_stats = {view.get("input") or view.get("name"): view for view in (previous_snapshot or {}).get("view_stats") or []}

    def previous_for_view(view: dict[str, Any], index: int) -> dict[str, Any]:
        previous_view = previous_view_stats.get(view["input"]) or previous_view_stats.get(view["name"])
        if previous_view is not None:
            return previous_view
        if index == 0 and previous_snapshot is not None:
            return {
                "nodes": previous_snapshot.get("nodes") or [],
                "relationships": previous_snapshot.get("relationships") or [],
                "orphan_nodes": previous_snapshot.get("orphan_nodes") or [],
            }
        return {"nodes": [], "relationships": [], "orphan_nodes": []}

    view_reports: list[dict[str, Any]] = []
    for index, view in enumerate(view_stats):
        previous_view = previous_for_view(view, index)
        node_diff = compare_string_set(previous_view.get("nodes") or [], view["nodes"])
        relationship_diff = compare_string_set(
            [relationship["key"] for relationship in previous_view.get("relationships") or []],
            [relationship["key"] for relationship in view["relationships"]],
        )
        duplicate_relationships = get_duplicate_relationships(view["relationships"])
        changed_relationships = [] if previous_snapshot is None else get_changed_relationships(previous_view.get("relationships") or [], view["relationships"])
        view_reports.append(
            {
                "view": view,
                "previous": previous_view,
                "node_diff": node_diff,
                "relationship_diff": relationship_diff,
                "duplicate_relationships": duplicate_relationships,
                "changed_relationships": changed_relationships,
            }
        )

    validation_issue_count = len(broken_links)
    for view_report in view_reports:
        validation_issue_count += len(view_report["view"]["orphan_nodes"])
        validation_issue_count += len(view_report["duplicate_relationships"])
        validation_issue_count += len(view_report["relationship_diff"]["Removed"])

    report = [
        f"Last Updated: {timestamp}",
        "",
        "### Summary",
        "",
        "| Metric | Count | Delta |",
        "| --- | ---: | ---: |",
        f"| Views Updated | {len(settings['views'])} | {format_snapshot_delta(previous_snapshot, previous_count('views'), len(snapshot['views']))} |",
        f"| Rendered Files | {len(rendered_files)} | {format_snapshot_delta(previous_snapshot, previous_count('rendered_files'), len(rendered_files))} |",
        f"| Broken Links | {len(broken_links)} | {format_snapshot_delta(previous_snapshot, previous_count('broken_links'), len(broken_links))} |",
        f"| Pending Nodes | {len(pending_nodes)} | {format_snapshot_delta(previous_snapshot, previous_count('pending_nodes'), len(pending_nodes))} |",
        f"| Validation Issues | {validation_issue_count} | n/a |",
        "",
        "### View Summary",
        "",
        "| View | Nodes | Delta | Relationships | Delta | Orphan Nodes |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for view_report in view_reports:
        view = view_report["view"]
        previous_view = view_report["previous"]
        report.append(
            f"| {view['name']} | {len(view['nodes'])} | {format_snapshot_delta(previous_snapshot, len(previous_view.get('nodes') or []), len(view['nodes']))} | "
            f"{len(view['relationships'])} | {format_snapshot_delta(previous_snapshot, len(previous_view.get('relationships') or []), len(view['relationships']))} | "
            f"{len(view['orphan_nodes'])} |"
        )

    report += [
        "",
        "### Semantic Changes",
        "",
    ]
    for view_report in view_reports:
        view = view_report["view"]
        node_diff = view_report["node_diff"]
        relationship_diff = view_report["relationship_diff"]
        changed_relationships = view_report["changed_relationships"]
        duplicate_relationships = view_report["duplicate_relationships"]
        report += [
            f"#### {view['name']}",
            "",
            f"- Added nodes: {len(node_diff['Added'])}",
            f"- Removed nodes: {len(node_diff['Removed'])}",
            f"- Added relationships: {len(relationship_diff['Added'])}",
            f"- Removed relationships: {len(relationship_diff['Removed'])}",
            f"- Changed relationship labels: {len(changed_relationships)}",
            f"- Duplicate relationships: {len(duplicate_relationships)}",
            "",
        ]

    report += [
        "### Views",
        "",
    ]
    report += [f"- {view['name']}: `{view['input']}`" for view in settings["views"]]
    report += ["", "### Rendered Outputs", ""]
    for rendered_file in rendered_files:
        report.append(f"- `{rendered_file}` ({resolve_repo_path(rendered_file).stat().st_size} bytes)")
    report += [
        "",
        "### Hygiene",
        "",
        f"- Broken links: {len(broken_links)}",
        f"- Orphan nodes: {sum(len(view_report['view']['orphan_nodes']) for view_report in view_reports)}",
        f"- Duplicate relationships: {sum(len(view_report['duplicate_relationships']) for view_report in view_reports)}",
        f"- Removed relationships: {sum(len(view_report['relationship_diff']['Removed']) for view_report in view_reports)}",
        f"- Changed relationship labels: {sum(len(view_report['changed_relationships']) for view_report in view_reports)}",
        f"- Pending graph nodes: {len(pending_nodes)}",
    ]

    for view_report in view_reports:
        view = view_report["view"]
        for title, items in [
            ("Added Nodes", view_report["node_diff"]["Added"]),
            ("Removed Nodes", view_report["node_diff"]["Removed"]),
            ("Added Relationships", view_report["relationship_diff"]["Added"]),
            ("Removed Relationships", view_report["relationship_diff"]["Removed"]),
            ("Duplicate Relationships", view_report["duplicate_relationships"]),
            ("Orphan Nodes", view["orphan_nodes"]),
        ]:
            if items:
                report += ["", f"#### {view['name']} - {title}", ""]
                report += [f"- `{item}`" for item in items]

        if view_report["changed_relationships"]:
            report += ["", f"#### {view['name']} - Changed Relationship Labels", ""]
            for relationship in view_report["changed_relationships"]:
                report.append(f"- `{relationship['source']}` -> `{relationship['target']}` changed from `{relationship['previous']}` to `{relationship['current']}`")

    for title, items in [("Broken Links", broken_links), ("Pending Nodes", pending_nodes)]:
        if items:
            report += ["", f"#### {title}", ""]
            report += [f"- {item}" if title == "Broken Links" else f"- `{item}`" for item in items]

    update_report_section(report_path, report)
    write_text(snapshot_path, json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print(f"Visualization refresh tracker updated in {settings['reportPath']}")


def invoke_render_mode(settings: dict[str, Any], puppeteer_config: Path, input_path: str | None, output_paths: list[str] | None) -> None:
    if not input_path:
        raise RuntimeError("Render mode requires --input-path. Aliases: --input, --graph.")

    input_full_path = resolve_repo_path(input_path)
    if not input_full_path.exists():
        raise RuntimeError(f"Input Mermaid file not found: {input_path}")

    if not output_paths:
        base_name = input_full_path.stem
        output_paths = [f"Visualization/rendered/{base_name}.svg", f"Visualization/rendered/{base_name}.png"]

    for output_path in output_paths:
        invoke_mermaid_render(input_full_path, resolve_repo_path(output_path), settings, puppeteer_config)


def load_visualization_settings(settings_path: str | Path = "Visualization/config/render-settings.json") -> dict[str, Any]:
    return json.loads(read_text(resolve_repo_path(settings_path)))


def invoke_validate_mode(settings: dict[str, Any]) -> None:
    nodes = read_glossary_nodes()
    relationships = read_relationship_seeds()
    data_projections = read_data_projections()
    first_appearance_displays = read_first_appearance_graph_displays()
    pending_node_ids = {node_id for node_id, node in nodes.items() if node.get("status") == "pending"}
    print(f"Source parse: nodes={len(nodes)} relationships={len(relationships)}")

    issues: list[str] = []
    for view in settings["views"]:
        graph_path = resolve_repo_path(view["input"])
        if not graph_path.exists():
            issues.append(f"Configured graph is missing: {view['input']}")
            continue
        class_issues = get_mermaid_class_validation(graph_path, settings)
        layout_issues = get_mermaid_layout_validation(graph_path, settings)
        print(f"Existing graph: {view['input']} class_issues={len(class_issues)} layout_issues={len(layout_issues)}")
        issues.extend(f"{view['input']}: {issue}" for issue in [*class_issues, *layout_issues])

    with tempfile.TemporaryDirectory(prefix="lotm-visualization-validate-") as temp_dir:
        temp_root = Path(temp_dir)
        for view in settings["views"]:
            temp_graph = temp_root / Path(view["input"]).name
            timing_spoiler_free = "timing-spoiler-free" in view["input"]
            boundary = view.get("readerBoundary")
            view_nodes = filter_nodes_for_boundary(nodes, boundary)
            anonymized_nodes, node_aliases = get_anonymized_node_displays(nodes, boundary, first_appearance_displays)
            view_nodes.update(anonymized_nodes)
            view_relationships = filter_relationships_for_boundary(
                relationships,
                boundary,
                set(view_nodes),
                set(nodes),
                data_projections,
                timing_spoiler_free,
                node_aliases,
            )
            pending_endpoint_node_ids = get_missing_relationship_endpoints(view_relationships, set(nodes))
            write_mermaid_graph(
                temp_graph,
                dict(view_nodes),
                view_relationships,
                timing_spoiler_free,
                set(nodes),
                pending_node_ids & set(view_nodes),
                pending_endpoint_node_ids,
            )
            class_issues = get_mermaid_class_validation(temp_graph, settings)
            layout_issues = get_mermaid_layout_validation(temp_graph, settings)
            print(f"Generated graph: {view['input']} class_issues={len(class_issues)} layout_issues={len(layout_issues)}")
            issues.extend(f"generated {view['input']}: {issue}" for issue in [*class_issues, *layout_issues])

    if issues:
        raise RuntimeError("Visualization validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))

    print("Visualization validation passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and render repository Mermaid visualizations.")
    parser.add_argument(
        "--mode",
        choices=[
            "refresh",
            "render",
            "validate",
            "check",
            "test",
            "update",
            "generate",
            "manual-render",
            "pure-render",
            "Refresh",
            "Render",
            "Validate",
            "Check",
            "Test",
            "Update",
            "Generate",
            "Manual-Render",
            "Pure-Render",
        ],
        default="Refresh",
    )
    parser.add_argument("--input-path", "--input", "--graph", dest="input_path")
    parser.add_argument("--output-path", "--output", "--out", action="append", dest="output_paths")
    parser.add_argument("--settings-path", "--settings", default="Visualization/config/render-settings.json")
    parser.add_argument("--skip-render", "--no-render", action="store_true")
    args = parser.parse_args()
    args.mode = args.mode.lower()
    if args.mode in {"update", "generate"}:
        args.mode = "refresh"
    elif args.mode in {"manual-render", "pure-render"}:
        args.mode = "render"
    elif args.mode in {"check", "test"}:
        args.mode = "validate"
    return args


def clean_disposable_caches() -> None:
    try:
        clean_path = REPO_ROOT / "Tools" / "clean_temp_files.py"
        spec = importlib.util.spec_from_file_location("_lotm_clean_temp_files", clean_path)
        if spec is None or spec.loader is None:
            return
        cleaner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cleaner)
        cleaner.clean_cache_dirs(cleaner.find_cache_dirs(REPO_ROOT))
    except Exception:
        return


def main() -> None:
    args = parse_args()
    os.chdir(REPO_ROOT)
    settings = load_visualization_settings(args.settings_path)
    puppeteer_config = resolve_repo_path(settings["puppeteerConfig"])

    try:
        if args.mode == "render":
            invoke_render_mode(settings, puppeteer_config, args.input_path, args.output_paths)
        elif args.mode == "validate":
            invoke_validate_mode(settings)
        else:
            invoke_refresh_mode(settings, puppeteer_config, args.skip_render)
    finally:
        clean_disposable_caches()


if __name__ == "__main__":
    main()
