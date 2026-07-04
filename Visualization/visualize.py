#!/usr/bin/env python
"""Unified visualization workflow for Mermaid graph generation and rendering."""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import shutil
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]


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
    name = re.sub(r"^(artifact|character|concept|event|faction|location|pathway)-", "", Path(slug).stem)
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


def read_glossary_nodes() -> dict[str, str]:
    nodes: dict[str, str] = {}
    root = resolve_repo_path("Glossary_Threads")
    for file_path in sorted(root.rglob("*.md")):
        if file_path.name == "TEMPLATE.md":
            continue
        slug = file_path.stem
        node_id = convert_slug_to_node_id(slug)
        label = None
        for line in read_text(file_path).splitlines():
            match = re.match(r"^#\s+(.+)$", line)
            if match:
                label = match.group(1).strip()
                break
        nodes[node_id] = label or convert_slug_to_fallback_label(slug)
    return nodes


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
                current = {"source": match.group(1).strip(), "target": "", "relationship_type": "", "chapter": "", "status": "", "confidence": ""}
                continue
            if current is None:
                continue
            if match := re.match(r"^\s+target:\s*(.+?)\s*$", line):
                current["target"] = match.group(1).strip()
            elif match := re.match(r"^\s+relationship_type:\s*(.+?)\s*$", line):
                current["relationship_type"] = match.group(1).strip()
            elif not current["chapter"] and (match := re.match(r"^\s+chapter:\s*(.+?)\s*$", line)):
                current["chapter"] = match.group(1).strip()
            elif match := re.match(r"^\s+status:\s*(.+?)\s*$", line):
                current["status"] = match.group(1).strip()
            elif match := re.match(r"^\s+confidence:\s*(.+?)\s*$", line):
                current["confidence"] = match.group(1).strip()

        if in_section and in_code and current is not None:
            relationships.append(current)

    return [
        relationship
        for relationship in relationships
        if relationship["source"].strip() and relationship["target"].strip() and relationship["relationship_type"].strip()
    ]


def format_relationship_label(relationship: dict[str, str], timing_spoiler_free: bool) -> str:
    parts = [relationship["relationship_type"]]
    if not timing_spoiler_free and relationship.get("chapter"):
        parts.append(f"ch{relationship['chapter']}")
    if relationship.get("status") and relationship["status"] != "active":
        parts.append(relationship["status"])
    if relationship.get("confidence") and relationship["confidence"] != "confirmed":
        parts.append(relationship["confidence"])
    return " ".join(parts)


def format_relationship_node_label(relationship: dict[str, str], timing_spoiler_free: bool) -> str:
    return format_relationship_label(relationship, timing_spoiler_free).replace(" ", "<br/>", 1) if False else "<br/>".join(
        part.replace('"', r"\"") for part in format_relationship_label(relationship, timing_spoiler_free).split(" ")
    )


def write_mermaid_graph(graph_path: Path, nodes: dict[str, str], relationships: list[dict[str, str]], timing_spoiler_free: bool) -> None:
    for relationship in relationships:
        source = convert_slug_to_node_id(relationship["source"])
        target = convert_slug_to_node_id(relationship["target"])
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
        "  classDef event fill:#fff1f2,stroke:#e11d48,stroke-width:2px,color:#1f2937",
        "  classDef faction fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#1f2937",
        "  classDef location fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1f2937",
        "  classDef pathway fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#1f2937",
        "  classDef relationship fill:#f7f2e9,stroke:#c69245,stroke-width:1.5px,color:#1f2937",
        "",
    ]
    for node_id in sorted(nodes):
        class_name = node_id.split("_")[0]
        if class_name in {"artifact", "character", "concept", "event", "faction", "location", "pathway"}:
            lines.append(f"  class {node_id} {class_name}")

    lines.append("")
    seen_edges: set[str] = set()
    edges: list[dict[str, str]] = []
    for relationship in relationships:
        source = convert_slug_to_node_id(relationship["source"])
        target = convert_slug_to_node_id(relationship["target"])
        label = format_relationship_label(relationship, timing_spoiler_free)
        key = f"{source}|{label}|{target}"
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": source, "target": target, "label": label, "nodeLabel": format_relationship_node_label(relationship, timing_spoiler_free)})

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
    for view in views:
        graph_path = resolve_repo_path(view["input"])
        timing_spoiler_free = "timing-spoiler-free" in view["input"]
        write_mermaid_graph(graph_path, dict(nodes), relationships, timing_spoiler_free)


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
            pending.append(match.group(1).strip())
    return pending


def get_broken_markdown_links() -> list[str]:
    broken: list[str] = []
    for file_path in sorted(REPO_ROOT.rglob("*.md")):
        full_name = str(file_path)
        if f"{os.sep}.git{os.sep}" in full_name or f"{os.sep}Source{os.sep}" in full_name:
            continue
        text = read_text(file_path)
        for match in re.finditer(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
            target = match.group(1).strip().strip("<>")
            if re.match(r"^(https?:|mailto:)", target):
                continue
            target_path = file_path.parent / unquote(target)
            if not target_path.exists():
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

    primary_graph = resolve_repo_path(settings["views"][0]["input"])
    stats = get_graph_stats(primary_graph)
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
        "nodes": stats["NodeIds"],
        "relationships": [
            {key: relationship[key] for key in ["source", "target", "label", "key", "endpointKey"]}
            for relationship in stats["Relationships"]
        ],
        "views": [view["name"] for view in settings["views"]],
        "rendered_files": rendered_files,
        "broken_links": broken_links,
        "orphan_nodes": stats["OrphanNodes"],
        "pending_nodes": pending_nodes,
    }

    def previous_count(key: str) -> int:
        return 0 if previous_snapshot is None else len(previous_snapshot.get(key) or [])

    node_diff = compare_string_set((previous_snapshot or {}).get("nodes") or [], snapshot["nodes"])
    relationship_diff = compare_string_set(
        [relationship["key"] for relationship in (previous_snapshot or {}).get("relationships") or []],
        [relationship["key"] for relationship in snapshot["relationships"]],
    )
    duplicate_relationships = get_duplicate_relationships(snapshot["relationships"])
    changed_relationships = [] if previous_snapshot is None else get_changed_relationships(previous_snapshot.get("relationships") or [], snapshot["relationships"])
    validation_issue_count = len(broken_links) + len(stats["OrphanNodes"]) + len(duplicate_relationships) + len(relationship_diff["Removed"])

    report = [
        f"Last Updated: {timestamp}",
        "",
        "### Summary",
        "",
        "| Metric | Count | Delta |",
        "| --- | ---: | ---: |",
        f"| Nodes | {len(snapshot['nodes'])} | {format_snapshot_delta(previous_snapshot, previous_count('nodes'), len(snapshot['nodes']))} |",
        f"| Relationships | {len(snapshot['relationships'])} | {format_snapshot_delta(previous_snapshot, previous_count('relationships'), len(snapshot['relationships']))} |",
        f"| Views Updated | {len(settings['views'])} | {format_snapshot_delta(previous_snapshot, previous_count('views'), len(snapshot['views']))} |",
        f"| Rendered Files | {len(rendered_files)} | {format_snapshot_delta(previous_snapshot, previous_count('rendered_files'), len(rendered_files))} |",
        f"| Broken Links | {len(broken_links)} | {format_snapshot_delta(previous_snapshot, previous_count('broken_links'), len(broken_links))} |",
        f"| Orphan Nodes | {len(stats['OrphanNodes'])} | {format_snapshot_delta(previous_snapshot, previous_count('orphan_nodes'), len(stats['OrphanNodes']))} |",
        f"| Pending Nodes | {len(pending_nodes)} | {format_snapshot_delta(previous_snapshot, previous_count('pending_nodes'), len(pending_nodes))} |",
        f"| Validation Issues | {validation_issue_count} | n/a |",
        "",
        "### Semantic Changes",
        "",
        f"- Added nodes: {len(node_diff['Added'])}",
        f"- Removed nodes: {len(node_diff['Removed'])}",
        f"- Added relationships: {len(relationship_diff['Added'])}",
        f"- Removed relationships: {len(relationship_diff['Removed'])}",
        f"- Changed relationship labels: {len(changed_relationships)}",
        f"- Duplicate relationships: {len(duplicate_relationships)}",
        "",
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
        f"- Orphan nodes: {len(stats['OrphanNodes'])}",
        f"- Duplicate relationships: {len(duplicate_relationships)}",
        f"- Removed relationships: {len(relationship_diff['Removed'])}",
        f"- Changed relationship labels: {len(changed_relationships)}",
        f"- Pending graph nodes: {len(pending_nodes)}",
    ]

    for title, items in [
        ("Added Nodes", node_diff["Added"]),
        ("Removed Nodes", node_diff["Removed"]),
        ("Added Relationships", relationship_diff["Added"]),
        ("Removed Relationships", relationship_diff["Removed"]),
        ("Duplicate Relationships", duplicate_relationships),
        ("Orphan Nodes", stats["OrphanNodes"]),
        ("Broken Links", broken_links),
        ("Pending Nodes", pending_nodes),
    ]:
        if items:
            report += ["", f"#### {title}", ""]
            report += [f"- `{item}`" if title != "Broken Links" else f"- {item}" for item in items]

    if changed_relationships:
        report += ["", "#### Changed Relationship Labels", ""]
        for relationship in changed_relationships:
            report.append(f"- `{relationship['source']}` -> `{relationship['target']}` changed from `{relationship['previous']}` to `{relationship['current']}`")

    update_report_section(report_path, report)
    write_text(snapshot_path, json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print(f"Visualization refresh tracker updated in {settings['reportPath']}")


def invoke_render_mode(settings: dict[str, Any], puppeteer_config: Path, input_path: str | None, output_paths: list[str] | None) -> None:
    if not input_path:
        raise RuntimeError("Render mode requires --input-path.")

    input_full_path = resolve_repo_path(input_path)
    if not input_full_path.exists():
        raise RuntimeError(f"Input Mermaid file not found: {input_path}")

    if not output_paths:
        base_name = input_full_path.stem
        output_paths = [f"Visualization/rendered/{base_name}.svg", f"Visualization/rendered/{base_name}.png"]

    for output_path in output_paths:
        invoke_mermaid_render(input_full_path, resolve_repo_path(output_path), settings, puppeteer_config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and render repository Mermaid visualizations.")
    parser.add_argument("--mode", choices=["Refresh", "Render"], default="Refresh")
    parser.add_argument("--input-path")
    parser.add_argument("--output-path", action="append", dest="output_paths")
    parser.add_argument("--settings-path", default="Visualization/config/render-settings.json")
    parser.add_argument("--skip-render", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.chdir(REPO_ROOT)
    settings_path = resolve_repo_path(args.settings_path)
    settings = json.loads(read_text(settings_path))
    puppeteer_config = resolve_repo_path(settings["puppeteerConfig"])

    if args.mode == "Render":
        invoke_render_mode(settings, puppeteer_config, args.input_path, args.output_paths)
    else:
        invoke_refresh_mode(settings, puppeteer_config, args.skip_render)


if __name__ == "__main__":
    main()
