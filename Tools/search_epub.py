import argparse
import fnmatch
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath


ENTRY_TYPES = ["Chapters", "SideStories", "Appendices", "Artwork", "FrontMatter", "Other", "All"]


def configure_output_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Document:
    path: str
    file_name: str
    entry_type: str
    volume: int | None
    chapter: int | None
    title: str | None
    order: int
    sort_chapter: int
    lines: list[str]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the local Lord of Mysteries EPUB.")
    parser.add_argument("--epub-path", default="Source/Lord of Mysteries - Book 1.epub")
    parser.add_argument("--start-chapter", type=positive_int, default=1)
    parser.add_argument("--end-chapter", type=positive_int, default=9999)
    parser.add_argument("--volume", type=int, action="append")
    parser.add_argument("--entry-type", choices=ENTRY_TYPES, action="append", default=None)
    parser.add_argument("--entry-name-pattern")
    parser.add_argument("--pattern", "--query", "--text", "--search")
    parser.add_argument("--context-lines", type=non_negative_int, default=0)
    parser.add_argument("--max-hits-per-chapter", type=non_negative_int, default=50)
    parser.add_argument("--counts-only", "--counts", action="store_true")
    parser.add_argument("--term-summary", "--summary-only", "--summary", action="store_true")
    parser.add_argument("--include-line-match-counts", action="store_true")
    parser.add_argument("--regex-pattern", action="store_true")
    parser.add_argument("--case-sensitive", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-entries", action="store_true")
    return parser


def convert_xhtml_to_lines(xhtml: str) -> list[str]:
    plain = re.sub(r"<[^>]+>", "\n", xhtml)
    plain = html.unescape(plain)
    return [line.strip() for line in plain.split("\n") if line.strip()]


def make_regex(terms: list[str], use_regex: bool, match_case: bool) -> re.Pattern[str]:
    parts = terms if use_regex else [re.escape(term) for term in terms]
    flags = 0 if match_case else re.IGNORECASE
    return re.compile("|".join(parts), flags)


def make_single_regex(term: str, use_regex: bool, match_case: bool) -> re.Pattern[str]:
    return make_regex([term], use_regex, match_case)


def format_snippet(text: str, max_length: int = 260) -> str:
    snippet = re.sub(r"\s+", " ", text)
    if len(snippet) > max_length:
        return snippet[:max_length] + "..."
    return snippet


def matched_terms(text: str, terms: list[str], use_regex: bool, match_case: bool) -> list[str]:
    return [term for term in terms if make_single_regex(term, use_regex, match_case).search(text)]


def term_match_counts(text: str, terms: list[str], use_regex: bool, match_case: bool) -> dict[str, int]:
    counts: dict[str, int] = {}
    for term in terms:
        count = len(make_single_regex(term, use_regex, match_case).findall(text))
        if count > 0:
            counts[term] = count
    return counts


def get_entry_title(lines: list[str], chapter: int | None) -> str | None:
    if not lines:
        return None
    if chapter is not None:
        for line in lines:
            if re.search(r"^Chapter\s+\d+(:|\b)", line):
                return line
    return lines[0]


def entry_metadata(path: str, lines: list[str], order: int) -> Document:
    chapter = None
    for line in lines:
        match = re.search(r"^Chapter\s+(\d+)(:|\b)", line)
        if match:
            chapter = int(match.group(1))
            break

    volume = None
    file_match = re.search(r"^OEBPS/Text/volume_(\d+)_", path)
    if file_match:
        volume = int(file_match.group(1))

    leaf_name = PurePosixPath(path).name
    if leaf_name.startswith("side_stories"):
        entry_type = "SideStories"
    elif chapter is not None and volume is not None:
        entry_type = "Chapters"
    elif re.search(r"^(character|pathways|location)\d+\.xhtml$", leaf_name):
        entry_type = "Appendices"
    elif re.search(r"^(artwork\d*|cover|back_cover)\.xhtml$", leaf_name):
        entry_type = "Artwork"
    elif re.search(r"^(copyright|foreword)\.xhtml$", leaf_name):
        entry_type = "FrontMatter"
    else:
        entry_type = "Other"

    sort_chapter = chapter if chapter is not None else 100000 + order
    return Document(
        path=path,
        file_name=leaf_name,
        entry_type=entry_type,
        volume=volume,
        chapter=chapter,
        title=get_entry_title(lines, chapter),
        order=order,
        sort_chapter=sort_chapter,
        lines=lines,
    )


def get_epub_entries(epub_path: str) -> list[Document]:
    documents: list[Document] = []
    with zipfile.ZipFile(epub_path) as epub:
        order = 0
        for info in epub.infolist():
            if not info.filename.startswith("OEBPS/Text/") or not info.filename.endswith(".xhtml"):
                continue
            xhtml = epub.read(info.filename).decode("utf-8")
            documents.append(entry_metadata(info.filename, convert_xhtml_to_lines(xhtml), order))
            order += 1
    return documents


def selected_entry(document: Document, args: argparse.Namespace) -> bool:
    entry_types = args.entry_type or ["Chapters"]
    selected_types = [entry_type for entry_type in ENTRY_TYPES if entry_type != "All"] if "All" in entry_types else entry_types
    if document.entry_type not in selected_types:
        return False

    if args.volume and document.volume not in args.volume:
        return False

    if document.chapter is not None and (document.chapter < args.start_chapter or document.chapter > args.end_chapter):
        return False

    if args.entry_name_pattern:
        if not (
            fnmatch.fnmatchcase(document.path, args.entry_name_pattern)
            or fnmatch.fnmatchcase(document.file_name, args.entry_name_pattern)
        ):
            return False

    return True


def document_label(document: Document) -> str:
    if document.chapter is not None:
        if document.entry_type != "Chapters":
            return f"{document.entry_type} Ch {document.chapter}"
        if document.volume is not None:
            return f"Ch {document.chapter} (Vol {document.volume})"
        return f"Ch {document.chapter}"
    return f"{document.entry_type}: {document.file_name}"


def document_json(document: Document) -> dict[str, object]:
    return {
        "entry_type": document.entry_type,
        "volume": document.volume,
        "chapter": document.chapter,
        "title": document.title,
        "source_path": document.path,
    }


def split_terms(pattern: str, regex_pattern: bool) -> list[str]:
    if regex_pattern:
        return [pattern]
    return [term.strip() for term in pattern.split("|") if term.strip()]


def term_summary_rows(documents: list[Document], terms: list[str], use_regex: bool, match_case: bool) -> list[dict[str, int | str]]:
    volume_numbers = sorted({document.volume for document in documents if document.volume is not None})
    rows: list[dict[str, int | str]] = []

    for term in terms:
        term_regex = make_single_regex(term, use_regex, match_case)
        row: dict[str, int | str] = {"term": term, "total": 0}
        for volume_number in volume_numbers:
            row[f"vol_{volume_number}"] = 0
        row["no_volume"] = 0

        for document in documents:
            count = sum(len(term_regex.findall(line)) for line in document.lines)
            if count <= 0:
                continue
            row["total"] = int(row["total"]) + count
            if document.volume is None:
                row["no_volume"] = int(row["no_volume"]) + count
            else:
                key = f"vol_{document.volume}"
                row[key] = int(row[key]) + count
        rows.append(row)

    return rows


def format_term_summary_table(rows: list[dict[str, int | str]]) -> list[str]:
    if not rows:
        return []
    properties = list(rows[0].keys())
    widths = {}
    for prop in properties:
        widths[prop] = max(len(prop), *(len(str(row[prop])) for row in rows))

    header = " | ".join(prop.ljust(widths[prop]) for prop in properties)
    separator = "-|-".join("-" * widths[prop] for prop in properties)
    lines = [header, separator]
    for row in rows:
        parts = []
        for prop in properties:
            value = str(row[prop])
            parts.append(value.ljust(widths[prop]) if prop == "term" else value.rjust(widths[prop]))
        lines.append(" | ".join(parts))
    return lines


def count_terms(lines: list[str], terms: list[str], use_regex: bool, match_case: bool) -> dict[str, int]:
    counts: dict[str, int] = {}
    for term in terms:
        term_regex = make_single_regex(term, use_regex, match_case)
        count = sum(len(term_regex.findall(line)) for line in lines)
        if count > 0:
            counts[term] = count
    return counts


def search_documents(documents: list[Document], terms: list[str], args: argparse.Namespace) -> list[object] | None:
    search_regex = make_regex(terms, args.regex_pattern, args.case_sensitive)
    json_results: list[object] = []

    for document in documents:
        lines = document.lines
        hit_indexes = [index for index, line in enumerate(lines) if search_regex.search(line)]
        if not hit_indexes:
            continue

        term_counts = count_terms(lines, terms, args.regex_pattern, args.case_sensitive)

        if args.counts_only:
            if args.json:
                for key, count in term_counts.items():
                    result = document_json(document)
                    result.update({"term": key, "count": count})
                    json_results.append(result)
                continue
            count_parts = [f"{key}={count}" for key, count in term_counts.items()]
            print(f"{document_label(document)}: {'; '.join(count_parts)}")
            continue

        if not args.json:
            print()
            print(f"=== {document_label(document)}: {document.title} ===")
            print(document.path)

        printed = 0
        for hit_index in hit_indexes:
            if printed >= args.max_hits_per_chapter:
                if not args.json:
                    print(f"... hit limit reached for {document_label(document)} ({args.max_hits_per_chapter} shown of {len(hit_indexes)})")
                break

            if args.context_lines <= 0:
                if args.json:
                    for matched_term in matched_terms(lines[hit_index], terms, args.regex_pattern, args.case_sensitive):
                        hit: dict[str, object] = document_json(document)
                        hit.update(
                            {
                                "term": matched_term,
                                "line": hit_index + 1,
                                "line_index": hit_index,
                                "snippet": format_snippet(lines[hit_index]),
                            }
                        )
                        if args.include_line_match_counts:
                            hit["line_term_counts"] = term_match_counts(lines[hit_index], terms, args.regex_pattern, args.case_sensitive)
                        json_results.append(hit)
                else:
                    print(f"[{hit_index}] {format_snippet(lines[hit_index])}")
            else:
                start = max(0, hit_index - args.context_lines)
                end = min(len(lines) - 1, hit_index + args.context_lines)
                if args.json:
                    context = [
                        {"line": context_index + 1, "line_index": context_index, "snippet": format_snippet(lines[context_index])}
                        for context_index in range(start, end + 1)
                    ]
                    for matched_term in matched_terms(lines[hit_index], terms, args.regex_pattern, args.case_sensitive):
                        hit = document_json(document)
                        hit.update(
                            {
                                "term": matched_term,
                                "line": hit_index + 1,
                                "line_index": hit_index,
                                "snippet": format_snippet(lines[hit_index]),
                                "context": context,
                            }
                        )
                        if args.include_line_match_counts:
                            hit["line_term_counts"] = term_match_counts(lines[hit_index], terms, args.regex_pattern, args.case_sensitive)
                        json_results.append(hit)
                else:
                    for context_index in range(start, end + 1):
                        print(f"[{context_index}] {format_snippet(lines[context_index])}")
                    print("--")

            printed += 1

    return json_results if args.json else None


def main() -> int:
    configure_output_encoding()
    parser = build_parser()
    args = parser.parse_args()

    if not args.list_entries and not args.pattern:
        parser.error('provide --pattern. For literal multi-term searches, separate terms with "|". Use --list-entries to inspect EPUB entries without a search pattern.')

    if args.list_entries and args.term_summary:
        parser.error("--term-summary cannot be combined with --list-entries.")

    if args.start_chapter > args.end_chapter:
        parser.error("--start-chapter cannot be greater than --end-chapter.")

    try:
        documents = sorted(
            [document for document in get_epub_entries(args.epub_path) if selected_entry(document, args)],
            key=lambda document: (document.sort_chapter, document.order),
        )
    except FileNotFoundError:
        parser.error(f"EPUB not found: {args.epub_path}")
    except zipfile.BadZipFile:
        parser.error(f"EPUB is not a valid zip archive: {args.epub_path}")

    json_results: list[object] = []
    terms: list[str] = []
    if not args.list_entries:
        terms = split_terms(args.pattern, args.regex_pattern)

    if args.term_summary:
        rows = term_summary_rows(documents, terms, args.regex_pattern, args.case_sensitive)
        if args.json:
            json_results.extend(rows)
        else:
            for line in format_term_summary_table(rows):
                print(line)
    elif args.list_entries:
        if args.json:
            json_results.extend(document_json(document) for document in documents)
        else:
            for document in documents:
                volume_text = f"Vol {document.volume}" if document.volume is not None else "Vol -"
                chapter_text = f"Ch {document.chapter}" if document.chapter is not None else "Ch -"
                print(f"{document.entry_type} | {volume_text} | {chapter_text} | {document.file_name} | {document.title}")
    else:
        results = search_documents(documents, terms, args)
        if results is not None:
            json_results.extend(results)

    if args.json:
        print(json.dumps(json_results, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
