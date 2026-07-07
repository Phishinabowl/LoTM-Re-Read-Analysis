import argparse
import datetime as dt
import importlib.util
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


TYPE_FOLDERS = {
    "artifact": "Artifacts",
    "character": "Characters",
    "concept": "Concepts",
    "event": "Events",
    "faction": "Factions",
    "item": "Items",
    "location": "Locations",
    "pathway": "Pathways",
    "uniqueness": "Uniquenesses",
    "volume summary": "Volumes",
}

RECIPROCAL_TYPES = {
    "superior": "subordinate",
    "subordinate": "superior",
    "mentor": "student",
    "student": "mentor",
    "investigates": "investigated-by",
    "investigated-by": "investigates",
}

SLUG_PREFIXES = (
    "artifact",
    "character",
    "concept",
    "deity",
    "event",
    "faction",
    "item",
    "location",
    "pathway",
    "tarot-card",
    "uniqueness",
)

SLUG_RE = re.compile(
    r"\b(?:"
    + "|".join(re.escape(prefix) for prefix in SLUG_PREFIXES)
    + r")-[a-z0-9][a-z0-9-]*\b"
)

DATA_REFERENCE_KEYS = {
    "",
    "artifact",
    "character",
    "concept",
    "concept_index",
    "dedicated_article",
    "entity",
    "event",
    "faction",
    "item",
    "file",
    "location",
    "pathway",
    "related_ats_formula",
    "related_deity",
    "source",
    "target",
}


@dataclass
class Relationship:
    source: str = ""
    target: str = ""
    relationship_type: str = ""
    status: str = ""
    confidence: str = ""
    notes: str = ""
    source_file: str = ""
    start_medium: str = ""
    start_volume: str = ""
    start_chapter: str = ""
    projection_source: str = ""


@dataclass(frozen=True)
class AvailabilityEntry:
    medium: str = ""
    volume: str = ""
    chapter: str = ""
    season: str = ""
    episode: str = ""
    release_order: str = ""
    status: str = ""
    confidence: str = ""
    graph_visibility: str = ""
    adaptation_relationship: str = ""


@dataclass(frozen=True)
class DataProjection:
    source_slug: str
    projection_source: str
    availability: tuple[AvailabilityEntry, ...]


@dataclass(frozen=True)
class DataReference:
    source: str
    target: str
    source_file: str
    yaml_block: str
    context_key: str = ""


@dataclass
class CanonicalNote:
    slug: str
    title: str
    source_path: Path
    relative_source: str
    metadata: dict[str, str]
    relationships: list[Relationship] = field(default_factory=list)
    data_references: list[DataReference] = field(default_factory=list)
    data_projections: dict[str, DataProjection] = field(default_factory=dict)

    @property
    def type_name(self) -> str:
        return self.metadata.get("type", "Unknown")

    @property
    def export_folder(self) -> str:
        return TYPE_FOLDERS.get(self.type_name.lower(), "Other")

    @property
    def export_file_stem(self) -> str:
        return safe_file_stem(self.title)


def configure_output_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an Obsidian QA mirror from metadata, data blocks, and Relationship Seeds."
    )
    parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    parser.add_argument("--output-dir", default="Obsidian_Export", help="Generated export directory.")
    parser.add_argument("--include-stubs", action="store_true", help="Include pages whose metadata status is Stub.")
    parser.add_argument("--clean", action="store_true", help="Delete the output directory before regenerating it.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of human-readable text.")
    return parser


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def normalize_rel_path(path: Path) -> str:
    return path.as_posix()


def slug_to_title(slug: str) -> str:
    cleaned = re.sub(r"^(?:" + "|".join(re.escape(p) for p in SLUG_PREFIXES) + r")-", "", slug)
    return " ".join(part.capitalize() for part in cleaned.split("-") if part)


def safe_file_stem(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
    return cleaned or "Untitled"


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or fallback
    return fallback


def extract_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in extract_section(text, "Metadata").splitlines():
        if not line.strip() or line.lstrip().startswith("-") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if key and value:
            metadata[key] = value
    return metadata


def strip_scalar(value: str) -> str:
    value = value.strip()
    if value in {"", "null", "Null", "NULL"}:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def fenced_yaml_blocks(text: str) -> list[tuple[str, str]]:
    blocks = []
    for index, match in enumerate(re.finditer(r"```yaml\s*(.*?)```", text, re.DOTALL), start=1):
        blocks.append((f"yaml-block-{index}", match.group(1).strip()))
    return blocks


def extract_relationship_yaml(text: str) -> str:
    section = extract_section(text, "Relationship Seeds")
    if not section:
        return ""
    match = re.search(r"```yaml\s*(.*?)```", section, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_relationships(block: str, source_file: str) -> list[Relationship]:
    relationships: list[Relationship] = []
    current: dict[str, str] | None = None
    nested_key = ""

    for raw_line in block.splitlines():
        if not raw_line.strip() or raw_line.strip() == "relationships:":
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if line.startswith("- "):
            if current:
                relationships.append(make_relationship(current, source_file))
            current = {}
            nested_key = ""
            line = line[2:].strip()
            if not line:
                continue

        if current is None or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = strip_scalar(value)

        if indent <= 4:
            nested_key = key if value == "" else ""
            if value:
                current[key] = value
        elif nested_key:
            current[f"{nested_key}_{key}"] = value
        else:
            current[key] = value

    if current:
        relationships.append(make_relationship(current, source_file))
    return [rel for rel in relationships if rel.source or rel.target]


def make_relationship(data: dict[str, str], source_file: str) -> Relationship:
    return Relationship(
        source=data.get("source", ""),
        target=data.get("target", ""),
        relationship_type=data.get("relationship_type", ""),
        status=data.get("status", ""),
        confidence=data.get("confidence", ""),
        notes=data.get("notes", ""),
        source_file=source_file,
        start_medium=data.get("start_medium", ""),
        start_volume=data.get("start_volume", ""),
        start_chapter=data.get("start_chapter", ""),
        projection_source=data.get("projection_source", ""),
    )


def parse_inline_mapping(value: str) -> dict[str, str]:
    value = strip_scalar(value)
    if not value.startswith("{") or not value.endswith("}"):
        return {}
    result: dict[str, str] = {}
    inner = value[1:-1].strip()
    if not inner:
        return result
    for part in inner.split(","):
        if ":" not in part:
            continue
        key, item_value = part.split(":", 1)
        result[key.strip()] = strip_scalar(item_value)
    return result


def slugify_projection_value(value: str) -> str:
    value = strip_scalar(value).strip()
    if not value:
        return ""
    if SLUG_RE.fullmatch(value):
        return value
    value = re.sub(r"[/\\]+", " ", value)
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return value


def projection_keys_for_row(row: dict[str, str]) -> set[str]:
    keys: set[str] = set()
    for key in ["target", "ability", "event", "pathway", "organization", "item", "label", "field", "entity", "uniqueness"]:
        value = row.get(key, "")
        if not value:
            continue
        slug_value = slugify_projection_value(value)
        if slug_value:
            keys.add(slug_value)
            for prefix in SLUG_PREFIXES:
                keys.add(f"{prefix}-{slug_value}")
    return keys


def make_availability_entry(data: dict[str, str]) -> AvailabilityEntry:
    return AvailabilityEntry(
        medium=data.get("medium", ""),
        volume=data.get("from_volume", "") or data.get("volume", ""),
        chapter=data.get("from_chapter", "") or data.get("chapter", ""),
        season=data.get("from_season", "") or data.get("season", ""),
        episode=data.get("from_episode", "") or data.get("episode", ""),
        release_order=data.get("from_release_order", "") or data.get("release_order", ""),
        status=data.get("status", "") or data.get("possession_status", "") or data.get("outcome_status", ""),
        confidence=data.get("confidence", ""),
        graph_visibility=data.get("graph_visibility", ""),
        adaptation_relationship=data.get("adaptation_relationship", ""),
    )


def parse_data_projections(text: str, note_slug: str) -> dict[str, DataProjection]:
    projections: dict[str, DataProjection] = {}
    relationship_block = extract_relationship_yaml(text)

    for _, block in fenced_yaml_blocks(text):
        if relationship_block and block == relationship_block:
            continue

        root_key = ""
        section_key = ""
        row: dict[str, str] | None = None
        availability: list[AvailabilityEntry] = []
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
                    projection = DataProjection(note_slug, projection_source, tuple(availability))
                    projections[f"{note_slug}|{projection_source}"] = projection
                    projections.setdefault(projection_source, projection)
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
                root_key = key.strip() if strip_scalar(value) == "" else ""
                section_key = ""
                continue

            if root_key and indent == 2 and not line.startswith("- "):
                finish_row()
                key, value = line.split(":", 1)
                section_key = key.strip() if strip_scalar(value) == "" else ""
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
            value = strip_scalar(value)

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
                key = key.lstrip("-").strip()
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


def slug_candidates_from_yaml_value(value: str) -> set[str]:
    value = strip_scalar(value).strip()
    if not value or value.startswith("{") or value.startswith("["):
        return set()

    if SLUG_RE.fullmatch(value):
        return {value}

    path_match = re.search(r"(?:^|/|\\)(" + SLUG_RE.pattern[2:-2] + r")\.md$", value)
    if path_match:
        return {path_match.group(1)}

    return set()


def parse_data_references(text: str, note_slug: str, source_file: str) -> list[DataReference]:
    refs: set[DataReference] = set()
    relationship_block = extract_relationship_yaml(text)
    for block_name, block in fenced_yaml_blocks(text):
        if relationship_block and block == relationship_block:
            continue
        for raw_line in block.splitlines():
            line = raw_line.strip()
            key = ""
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lstrip("-").strip()
                candidates = slug_candidates_from_yaml_value(value)
            elif line.startswith("- "):
                candidates = slug_candidates_from_yaml_value(line[2:])
            else:
                candidates = set()

            if key not in DATA_REFERENCE_KEYS:
                continue

            for slug in candidates:
                if slug != note_slug:
                    refs.add(DataReference(note_slug, slug, source_file, block_name, key))
    return sorted(refs, key=lambda ref: (ref.target, ref.yaml_block, ref.context_key))


def discover_notes(
    root: Path, include_stubs: bool
) -> tuple[dict[str, CanonicalNote], list[Relationship], list[DataReference], dict[str, DataProjection]]:
    notes: dict[str, CanonicalNote] = {}
    relationships: list[Relationship] = []
    data_references: list[DataReference] = []
    data_projections: dict[str, DataProjection] = {}

    for search_root in [root / "Glossary_Threads", root / "Volumes"]:
        if not search_root.exists():
            continue
        for path in sorted(search_root.rglob("*.md")):
            if path.name.upper() == "TEMPLATE.MD":
                continue
            text = read_text(path)
            metadata = parse_metadata(text)
            if metadata.get("status", "").lower() == "stub" and not include_stubs:
                continue
            if not metadata.get("type"):
                continue

            relative_source = normalize_rel_path(path.relative_to(root))
            note = CanonicalNote(
                slug=path.stem,
                title=first_heading(text, slug_to_title(path.stem)),
                source_path=path,
                relative_source=relative_source,
                metadata=metadata,
            )
            note.relationships = parse_relationships(extract_relationship_yaml(text), relative_source)
            note.data_references = parse_data_references(text, note.slug, relative_source)
            note.data_projections = parse_data_projections(text, note.slug)
            notes[note.slug] = note
            relationships.extend(note.relationships)
            data_references.extend(note.data_references)
            data_projections.update(note.data_projections)

    return notes, relationships, data_references, data_projections


def wiki_link(slug: str, notes: dict[str, CanonicalNote]) -> str:
    if slug in notes:
        note = notes[slug]
        return f"[[{note.export_folder}/{note.export_file_stem}|{note.title}]]"
    return f"[[{slug_to_title(slug)}]]"


def table_wiki_link(slug: str, notes: dict[str, CanonicalNote]) -> str:
    if slug in notes:
        note = notes[slug]
        return f"[[{note.export_folder}/{note.export_file_stem}|{note.title}]]"
    return f"[[{slug_to_title(slug)}]]"


def source_link(source_file: str) -> str:
    source_without_suffix = source_file[:-3] if source_file.endswith(".md") else source_file
    return f"[[{source_without_suffix}|{source_file}]]"


def table_source_link(source_file: str) -> str:
    source_without_suffix = source_file[:-3] if source_file.endswith(".md") else source_file
    return f"[[{source_without_suffix}]]"


def yaml_quote(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def mermaid_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def mermaid_node_id(slug: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", slug)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"node_{cleaned}"
    return cleaned


def mermaid_node_title(slug: str, notes: dict[str, CanonicalNote]) -> str:
    return notes[slug].title if slug in notes else slug_to_title(slug)


def edge_line(rel: Relationship, notes: dict[str, CanonicalNote], incoming: bool = False) -> str:
    subject = wiki_link(rel.source if incoming else rel.target, notes)
    field_name = f"incoming-{rel.relationship_type or 'relationship'}" if incoming else rel.relationship_type or "relationship"
    details = []
    if rel.status:
        details.append(f"status: {rel.status}")
    if rel.confidence:
        details.append(f"confidence: {rel.confidence}")
    if rel.start_medium or rel.start_volume or rel.start_chapter:
        details.append("start: " + " ".join(x for x in [rel.start_medium, rel.start_volume, rel.start_chapter] if x))
    return f"- {field_name}:: {subject}" + (f" ({'; '.join(details)})" if details else "")


def data_ref_line(ref: DataReference, notes: dict[str, CanonicalNote], incoming: bool = False) -> str:
    subject = wiki_link(ref.source if incoming else ref.target, notes)
    key = ref.context_key or "yaml-reference"
    return f"- {key}:: {subject} ({ref.yaml_block}; {source_link(ref.source_file)})"


def render_note(
    note: CanonicalNote,
    notes: dict[str, CanonicalNote],
    relationships: list[Relationship],
    data_references: list[DataReference],
) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    outgoing = [rel for rel in relationships if rel.source == note.slug]
    incoming = [rel for rel in relationships if rel.target == note.slug and rel.source != note.slug]
    outgoing_refs = [ref for ref in data_references if ref.source == note.slug]
    incoming_refs = [ref for ref in data_references if ref.target == note.slug and ref.source != note.slug]

    lines = [
        "---",
        f"source_file: {yaml_quote(note.relative_source)}",
        f"source_slug: {yaml_quote(note.slug)}",
        f"type: {yaml_quote(note.type_name.lower())}",
        f"status: {yaml_quote(note.metadata.get('status', ''))}",
        f"reader_boundary: {yaml_quote(note.metadata.get('reader_knowledge_boundary', ''))}",
        f"spoiler_boundary: {yaml_quote(note.metadata.get('spoiler_boundary', ''))}",
        "generated: true",
        f"generated_at: {yaml_quote(generated_at)}",
        "---",
        "",
        f"# {note.title}",
        "",
        "## Canonical Source",
        "",
        f"- {source_link(note.relative_source)}",
        "",
        "## Metadata Mirror",
        "",
    ]
    for key in ["type", "status", "reader_knowledge_boundary", "spoiler_boundary", "confidence_level", "tags"]:
        if key in note.metadata:
            lines.append(f"- {key.replace('_', ' ').title()}:: {note.metadata[key]}")

    lines.extend(["", "## Outgoing Relationship Seeds", ""])
    lines.extend(edge_line(rel, notes) for rel in outgoing)
    if not outgoing:
        lines.append("- None generated.")

    lines.extend(["", "## Incoming Relationship Seeds", ""])
    lines.extend(edge_line(rel, notes, incoming=True) for rel in incoming)
    if not incoming:
        lines.append("- None generated.")

    lines.extend(["", "## Data Block References", ""])
    lines.extend(data_ref_line(ref, notes) for ref in outgoing_refs)
    if not outgoing_refs:
        lines.append("- None generated.")

    lines.extend(["", "## Incoming Data Block References", ""])
    lines.extend(data_ref_line(ref, notes, incoming=True) for ref in incoming_refs)
    if not incoming_refs:
        lines.append("- None generated.")

    lines.extend(["", "## Seed Evidence", ""])
    for rel in outgoing + incoming:
        lines.append(f"- `{rel.source}` --{rel.relationship_type or 'relationship'}--> `{rel.target}` from {source_link(rel.source_file)}")
    if not outgoing and not incoming:
        lines.append("- No Relationship Seeds mention this note.")

    lines.append("")
    return "\n".join(lines)


def render_labeled_relationship_graph(relationships: list[Relationship], notes: dict[str, CanonicalNote]) -> str:
    grouped: dict[tuple[str, str, str], list[Relationship]] = {}
    for rel in relationships:
        if not rel.source or not rel.target:
            continue
        key = (rel.source, rel.relationship_type or "relationship", rel.target)
        grouped.setdefault(key, []).append(rel)

    used_slugs = sorted({slug for source, _, target in grouped for slug in (source, target)})
    lines = [
        "%% QA Relationship Graph",
        "%% Generated from Relationship Seeds as a QA-only Mermaid view.",
        "%% Duplicate seed edges are collapsed and marked with counts.",
        "%% Unknown nodes are Relationship Seed slugs that do not currently resolve to generated mirror notes.",
        "graph LR",
    ]

    for slug in used_slugs:
        node_id = mermaid_node_id(slug)
        title = mermaid_escape(mermaid_node_title(slug, notes))
        lines.append(f'  {node_id}["{title}"]')

    lines.append("")
    for source, relationship_type, target in sorted(grouped):
        duplicate_count = len(grouped[(source, relationship_type, target)])
        label = relationship_type
        if duplicate_count > 1:
            label = f"{label} x{duplicate_count}"
        lines.append(f'  {mermaid_node_id(source)} -->|"{mermaid_escape(label)}"| {mermaid_node_id(target)}')

    lines.extend(qa_graph_class_definitions())
    append_qa_graph_class_assignments(lines, used_slugs, notes)

    lines.append("")
    return "\n".join(lines)


def render_relationship_node_graph(
    relationships: list[Relationship], notes: dict[str, CanonicalNote], data_projections: dict[str, DataProjection]
) -> str:
    grouped: dict[tuple[str, str, str], list[Relationship]] = {}
    for rel in relationships:
        if not rel.source or not rel.target:
            continue
        key = (rel.source, rel.relationship_type or "relationship", rel.target)
        grouped.setdefault(key, []).append(rel)

    used_slugs = sorted({slug for source, _, target in grouped for slug in (source, target)})
    lines = [
        "%% QA Relationship Node Graph",
        "%% Generated from Relationship Seeds as a QA-only Mermaid view with relationship nodes.",
        "%% Duplicate seed edges are collapsed into relationship nodes and marked with counts.",
        "%% Unknown nodes are Relationship Seed slugs that do not currently resolve to generated mirror notes.",
        "graph LR",
    ]

    for slug in used_slugs:
        node_id = mermaid_node_id(slug)
        title = mermaid_escape(mermaid_node_title(slug, notes))
        lines.append(f'  {node_id}["{title}"]')

    lines.append("")
    grouped_items = sorted(grouped)
    for index, (source, relationship_type, target) in enumerate(grouped_items, start=1):
        group = grouped[(source, relationship_type, target)]
        duplicate_count = len(group)
        label_lines = [f"{relationship_type} x{duplicate_count}" if duplicate_count > 1 else relationship_type]
        source_lines = relationship_source_lines(group, data_projections)
        if source_lines:
            label_lines.extend(source_lines)
        if duplicate_count > 1:
            fallback_lines = relationship_provenance_lines(group, data_projections)
            for fallback_line in fallback_lines:
                if fallback_line not in label_lines:
                    label_lines.append(fallback_line)
        label = "<br/>".join(label_lines)
        relationship_node_id = f"rel_{index:03d}"
        lines.append(f'  {relationship_node_id}["{mermaid_escape(label)}"]')
        lines.append(f"  {mermaid_node_id(source)} --> {relationship_node_id}")
        lines.append(f"  {relationship_node_id} --> {mermaid_node_id(target)}")

    lines.extend(qa_graph_class_definitions(include_relationship=True))
    append_qa_graph_class_assignments(lines, used_slugs, notes)
    for index in range(1, len(grouped_items) + 1):
        lines.append(f"  class rel_{index:03d} relationship")

    lines.append("")
    return "\n".join(lines)


def relationship_source_lines(
    relationships: list[Relationship], data_projections: dict[str, DataProjection]
) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for rel in sorted(relationships, key=lambda item: (source_domain_label(item.source_file), item.source_file)):
        line = relationship_source_line(rel, data_projections)
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def relationship_source_line(rel: Relationship, data_projections: dict[str, DataProjection]) -> str:
    domain = source_domain_label(rel.source_file)
    if rel.projection_source:
        projection = data_projections.get(f"{rel.source}|{rel.projection_source}") or data_projections.get(rel.projection_source)
        if projection:
            history = format_availability_history(projection.availability)
            if history:
                return f"{domain} data {history}"

    seed_parts = [domain, "seed"]
    if rel.start_medium:
        seed_parts.append(rel.start_medium)
    if rel.start_chapter:
        seed_parts.append(f"ch{rel.start_chapter}")
    if rel.confidence:
        seed_parts.append(rel.confidence)
    if rel.status and rel.status != "active":
        seed_parts.append(rel.status)
    return " ".join(seed_parts)


def format_availability_history(entries: tuple[AvailabilityEntry, ...]) -> str:
    by_medium: dict[str, list[str]] = {}
    for entry in entries:
        entry_text = format_availability_entry(entry)
        if not entry_text:
            continue
        medium = entry.medium or "unknown"
        by_medium.setdefault(medium, [])
        if entry_text not in by_medium[medium]:
            by_medium[medium].append(entry_text)

    lines: list[str] = []
    for medium in sorted(by_medium):
        lines.append(f"{medium} {' -> '.join(by_medium[medium])}")
    return "; ".join(lines)


def format_availability_entry(entry: AvailabilityEntry) -> str:
    timing_parts: list[str] = []
    if entry.medium == "novel" and entry.chapter:
        timing_parts.append(f"ch{entry.chapter}")
    elif entry.medium == "donghua":
        has_real_position = any(
            value and value != "TBD" for value in [entry.season, entry.episode, entry.release_order]
        )
        if not has_real_position:
            return ""
        if entry.season and entry.season != "TBD":
            timing_parts.append(f"s{entry.season}")
        if entry.episode and entry.episode != "TBD":
            timing_parts.append(f"e{entry.episode}")
        if entry.release_order and entry.release_order != "TBD":
            timing_parts.append(f"r{entry.release_order}")
    elif entry.medium:
        timing_parts.append(entry.medium)
    if not timing_parts:
        return ""
    if entry.confidence and entry.confidence != "TBD":
        timing_parts.append(entry.confidence)
    elif entry.status and entry.status != "TBD":
        timing_parts.append(entry.status)
    if entry.graph_visibility and entry.graph_visibility != "full":
        timing_parts.append(entry.graph_visibility)
    if entry.adaptation_relationship and entry.adaptation_relationship != "pending":
        timing_parts.append(entry.adaptation_relationship)
    return " ".join(timing_parts)


def relationship_provenance_lines(
    relationships: list[Relationship], data_projections: dict[str, DataProjection] | None = None
) -> list[str]:
    lines: list[str] = []
    for rel in sorted(relationships, key=lambda item: (source_domain_label(item.source_file), item.confidence, item.start_chapter, item.source_file)):
        if data_projections:
            line = relationship_source_line(rel, data_projections)
            if line:
                lines.append(line)
                continue
        parts = [source_domain_label(rel.source_file), "seed"]
        if rel.start_medium:
            parts.append(rel.start_medium)
        if rel.confidence:
            parts.append(rel.confidence)
        if rel.start_chapter:
            parts.append(f"ch{rel.start_chapter}")
        if rel.status and rel.status != "active":
            parts.append(rel.status)
        lines.append(" ".join(parts))
    return lines


def source_domain_label(source_file: str) -> str:
    parts = Path(source_file).parts
    if "Glossary_Threads" in parts:
        index = parts.index("Glossary_Threads")
        if index + 1 < len(parts):
            return singular_domain(parts[index + 1])
    if parts and parts[0] == "Volumes":
        return "volume"
    stem = Path(source_file).stem
    for prefix in SLUG_PREFIXES:
        if stem.startswith(f"{prefix}-"):
            return prefix.replace("tarot-card", "tarot")
    return "source"


def singular_domain(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    mapping = {
        "artifacts": "artifact",
        "characters": "character",
        "concepts": "concept",
        "deities": "deity",
        "events": "event",
        "factions": "faction",
        "items": "item",
        "locations": "location",
        "pathways": "pathway",
        "tarot-cards": "tarot",
        "uniquenesses": "uniqueness",
        "volumes": "volume",
    }
    return mapping.get(normalized, normalized.rstrip("s") or "source")


def qa_graph_class_definitions(include_relationship: bool = False) -> list[str]:
    lines = [
        "",
        "  classDef character fill:#dbeafe,stroke:#2563eb,color:#111827",
        "  classDef faction fill:#fee2e2,stroke:#dc2626,color:#111827",
        "  classDef artifact fill:#fef3c7,stroke:#d97706,color:#111827",
        "  classDef concept fill:#ede9fe,stroke:#7c3aed,color:#111827",
        "  classDef pathway fill:#dcfce7,stroke:#16a34a,color:#111827",
        "  classDef location fill:#ffedd5,stroke:#ea580c,color:#111827",
        "  classDef event fill:#fce7f3,stroke:#db2777,color:#111827",
        "  classDef item fill:#ecfccb,stroke:#65a30d,color:#111827",
        "  classDef volume fill:#e5e7eb,stroke:#6b7280,color:#111827",
        "  classDef unknown fill:#f8fafc,stroke:#64748b,stroke-dasharray: 4 3,color:#111827",
    ]
    if include_relationship:
        lines.append("  classDef relationship fill:#f8fafc,stroke:#475569,stroke-width:1.5px,color:#111827")
    return lines


def append_qa_graph_class_assignments(lines: list[str], used_slugs: list[str], notes: dict[str, CanonicalNote]) -> None:
    class_map = {
        "Character": "character",
        "Faction": "faction",
        "Artifact": "artifact",
        "Concept": "concept",
        "Pathway": "pathway",
        "Location": "location",
        "Event": "event",
        "Item": "item",
        "Volume Summary": "volume",
    }
    for slug in used_slugs:
        class_name = class_map.get(notes[slug].type_name, "unknown") if slug in notes else "unknown"
        lines.append(f"  class {mermaid_node_id(slug)} {class_name}")


def write_visualization_relationship_graph(root: Path, output_path: Path) -> None:
    visualize_path = root / "Visualization" / "visualize.py"
    if not visualize_path.exists():
        raise RuntimeError(f"Visualization helper not found: {visualize_path}")

    module_name = "_lotm_visualization_for_obsidian_qa"
    spec = importlib.util.spec_from_file_location(module_name, visualize_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load visualization helper: {visualize_path}")

    visualize = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = visualize
    spec.loader.exec_module(visualize)

    node_data = visualize.read_glossary_nodes()
    nodes = {node_id: data["label"] for node_id, data in node_data.items()}
    relationships = visualize.read_relationship_seeds()
    data_projections = visualize.read_data_projections()
    filtered_relationships = visualize.filter_relationships_for_boundary(
        relationships,
        None,
        set(nodes),
        set(nodes),
        data_projections,
        False,
    )
    pending_node_ids = {node_id for node_id, data in node_data.items() if data.get("status") == "pending"}
    pending_endpoint_node_ids = visualize.get_missing_relationship_endpoints(filtered_relationships, set(nodes))
    visualize.write_mermaid_graph(
        output_path,
        dict(nodes),
        filtered_relationships,
        False,
        set(nodes),
        pending_node_ids,
        pending_endpoint_node_ids,
        include_confirmed_confidence=True,
    )


def render_relationship_index(relationships: list[Relationship], notes: dict[str, CanonicalNote]) -> str:
    lines = [
        "# Relationship Index",
        "",
        "Generated from Relationship Seeds. Canonical notes remain the source of truth.",
        "",
        "| Source | Relationship | Target | Status | Confidence | Seed File |",
        "|---|---|---|---|---|---|",
    ]
    for rel in sorted(relationships, key=lambda item: (item.source, item.relationship_type, item.target)):
        lines.append(
            "| "
            + " | ".join(
                [
                    table_wiki_link(rel.source, notes),
                    rel.relationship_type or "",
                    table_wiki_link(rel.target, notes),
                    rel.status or "",
                    rel.confidence or "",
                    table_source_link(rel.source_file),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_data_reference_index(data_references: list[DataReference], notes: dict[str, CanonicalNote]) -> str:
    lines = [
        "# Data Block Reference Index",
        "",
        "Generated from non-Relationship-Seed YAML data blocks. These are references, not typed graph edges.",
        "",
        "| Source | Context | Target | YAML Block | File |",
        "|---|---|---|---|---|",
    ]
    for ref in sorted(data_references, key=lambda item: (item.source, item.target, item.context_key)):
        lines.append(
            "| "
            + " | ".join(
                [
                    table_wiki_link(ref.source, notes),
                    ref.context_key or "",
                    table_wiki_link(ref.target, notes),
                    ref.yaml_block,
                    table_source_link(ref.source_file),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def analyze_orphans(
    notes: dict[str, CanonicalNote],
    relationships: list[Relationship],
    data_references: list[DataReference],
) -> dict[str, list[str]]:
    known = set(notes)
    rel_sources = {rel.source for rel in relationships if rel.source}
    rel_targets = {rel.target for rel in relationships if rel.target}
    data_targets = {ref.target for ref in data_references if ref.target}
    all_sources = rel_sources | {ref.source for ref in data_references if ref.source}
    all_targets = rel_targets | data_targets
    return {
        "unknown_relationship_sources": sorted(rel_sources - known),
        "unknown_relationship_targets": sorted(rel_targets - known),
        "unknown_data_targets": sorted(data_targets - known),
        "notes_without_any_edges_or_refs": sorted(known - all_sources - all_targets),
        "notes_without_outgoing_relationships": sorted(known - rel_sources),
    }


def render_orphan_report(
    notes: dict[str, CanonicalNote],
    relationships: list[Relationship],
    data_references: list[DataReference],
) -> str:
    data = analyze_orphans(notes, relationships, data_references)
    headings = [
        ("Unknown Relationship Sources", "unknown_relationship_sources"),
        ("Unknown Relationship Targets", "unknown_relationship_targets"),
        ("Unknown Data Block Targets", "unknown_data_targets"),
        ("Canonical Notes With No Edges Or Data References", "notes_without_any_edges_or_refs"),
        ("Canonical Notes With No Outgoing Relationship Seeds", "notes_without_outgoing_relationships"),
    ]
    lines = ["# Orphan Report", "", "Unknown entries do not currently resolve to a generated canonical mirror note.", ""]
    for heading, key in headings:
        lines.extend([f"## {heading}", ""])
        values = data[key]
        lines.extend(f"- {wiki_link(value, notes)} (`{value}`)" for value in values) if values else lines.append("- None.")
        lines.append("")
    return "\n".join(lines)


def analyze_suspicious_edges(relationships: list[Relationship], notes: dict[str, CanonicalNote]) -> dict[str, list]:
    loops = [rel for rel in relationships if rel.source and rel.source == rel.target]
    seen: dict[tuple[str, str, str], list[Relationship]] = {}
    for rel in relationships:
        seen.setdefault((rel.source, rel.relationship_type, rel.target), []).append(rel)
    duplicates = [items for items in seen.values() if len(items) > 1]
    edge_types = {(rel.source, rel.relationship_type, rel.target) for rel in relationships}
    missing_reciprocals = [
        rel
        for rel in relationships
        if rel.relationship_type in RECIPROCAL_TYPES
        and (rel.target, RECIPROCAL_TYPES[rel.relationship_type], rel.source) not in edge_types
    ]
    same_type_known_edges = [
        rel
        for rel in relationships
        if rel.source in notes and rel.target in notes and notes[rel.source].type_name == notes[rel.target].type_name
    ]
    return {
        "self_loops": loops,
        "duplicate_edges": duplicates,
        "missing_reciprocals": missing_reciprocals,
        "same_type_known_edges": same_type_known_edges,
    }


def render_suspicious_edges(notes: dict[str, CanonicalNote], relationships: list[Relationship]) -> str:
    data = analyze_suspicious_edges(relationships, notes)
    lines = ["# Suspicious Edges", "", "These are lint-style prompts for human review, not automatic errors.", ""]

    lines.extend(["## Self Loops", ""])
    lines.extend(
        f"- {wiki_link(rel.source, notes)} {rel.relationship_type or 'relationship'} -> {wiki_link(rel.target, notes)}"
        for rel in data["self_loops"]
    ) if data["self_loops"] else lines.append("- None.")

    lines.extend(["", "## Duplicate Edges", ""])
    if data["duplicate_edges"]:
        for group in data["duplicate_edges"]:
            rel = group[0]
            files = ", ".join(sorted({item.source_file for item in group}))
            lines.append(f"- {wiki_link(rel.source, notes)} {rel.relationship_type} -> {wiki_link(rel.target, notes)} appears {len(group)} times. Sources: {files}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Expected Reciprocals Missing", ""])
    lines.extend(
        f"- {wiki_link(rel.source, notes)} {rel.relationship_type} -> {wiki_link(rel.target, notes)}; expected `{RECIPROCAL_TYPES[rel.relationship_type]}` back."
        for rel in data["missing_reciprocals"]
    ) if data["missing_reciprocals"] else lines.append("- None.")

    lines.extend(["", "## Same-Type Known Edges", ""])
    lines.extend(
        f"- {wiki_link(rel.source, notes)} {rel.relationship_type} -> {wiki_link(rel.target, notes)} (`{notes[rel.source].type_name}` to `{notes[rel.target].type_name}`)"
        for rel in data["same_type_known_edges"]
    ) if data["same_type_known_edges"] else lines.append("- None.")

    lines.append("")
    return "\n".join(lines)


def ensure_safe_output(root: Path, output_dir: Path) -> Path:
    resolved_root = root.resolve()
    resolved_output = output_dir.resolve()
    if resolved_root != resolved_output and resolved_root not in resolved_output.parents:
        raise ValueError(f"Output directory must stay inside the repository root: {output_dir}")
    return resolved_output


def write_export(
    root: Path,
    output_dir: Path,
    clean: bool,
    notes: dict[str, CanonicalNote],
    relationships: list[Relationship],
    data_references: list[DataReference],
    data_projections: dict[str, DataProjection],
) -> None:
    output_dir = ensure_safe_output(root, output_dir)
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for folder in sorted(set(TYPE_FOLDERS.values()) | {"Other", "_Generated"}):
        (output_dir / folder).mkdir(parents=True, exist_ok=True)

    for note in notes.values():
        (output_dir / note.export_folder / f"{note.export_file_stem}.md").write_text(
            render_note(note, notes, relationships, data_references),
            encoding="utf-8",
        )

    generated_dir = output_dir / "_Generated"
    (generated_dir / "relationship-index.md").write_text(render_relationship_index(relationships, notes), encoding="utf-8")
    (generated_dir / "QA-relationship-graph.mmd").write_text(
        render_labeled_relationship_graph(relationships, notes),
        encoding="utf-8",
    )
    (generated_dir / "QA-relationship-node-graph.mmd").write_text(
        render_relationship_node_graph(relationships, notes, data_projections),
        encoding="utf-8",
    )
    write_visualization_relationship_graph(root, generated_dir / "visualization-relationship-graph.mmd")
    (generated_dir / "data-reference-index.md").write_text(render_data_reference_index(data_references, notes), encoding="utf-8")
    (generated_dir / "orphan-report.md").write_text(render_orphan_report(notes, relationships, data_references), encoding="utf-8")
    (generated_dir / "suspicious-edges.md").write_text(render_suspicious_edges(notes, relationships), encoding="utf-8")


def clean_disposable_caches(root: Path) -> None:
    try:
        clean_path = root / "Tools" / "clean_temp_files.py"
        spec = importlib.util.spec_from_file_location("_lotm_clean_temp_files", clean_path)
        if spec is None or spec.loader is None:
            return
        cleaner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cleaner)
        cleaner.clean_cache_dirs(cleaner.find_cache_dirs(root))
    except Exception:
        return


def main() -> int:
    configure_output_encoding()
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    output_dir = (root / args.output_dir).resolve()

    notes, relationships, data_references, data_projections = discover_notes(root, args.include_stubs)
    write_export(root, output_dir, args.clean, notes, relationships, data_references, data_projections)

    orphan_data = analyze_orphans(notes, relationships, data_references)
    suspicious_data = analyze_suspicious_edges(relationships, notes)
    summary = {
        "notes": len(notes),
        "relationships": len(relationships),
        "data_references": len(data_references),
        "output_dir": str(output_dir),
        "unknown_relationship_sources": len(orphan_data["unknown_relationship_sources"]),
        "unknown_relationship_targets": len(orphan_data["unknown_relationship_targets"]),
        "unknown_data_targets": len(orphan_data["unknown_data_targets"]),
        "self_loops": len(suspicious_data["self_loops"]),
        "duplicate_edge_groups": len(suspicious_data["duplicate_edges"]),
        "missing_reciprocals": len(suspicious_data["missing_reciprocals"]),
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Generated {summary['notes']} Obsidian QA notes.")
        print(f"Relationship Seeds: {summary['relationships']}; data block references: {summary['data_references']}.")
        print(f"Output: {summary['output_dir']}")
        print(
            "QA: "
            f"{summary['unknown_relationship_sources']} unknown relationship sources, "
            f"{summary['unknown_relationship_targets']} unknown relationship targets, "
            f"{summary['unknown_data_targets']} unknown data targets, "
            f"{summary['self_loops']} self loops, "
            f"{summary['duplicate_edge_groups']} duplicate edge groups, "
            f"{summary['missing_reciprocals']} missing expected reciprocals."
        )
    clean_disposable_caches(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
