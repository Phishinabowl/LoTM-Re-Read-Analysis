import argparse
import fnmatch
import html
import json
import posixpath
import re
import shutil
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image


PRESETS = {
    "PathwayTarotCard": {
        "operation": "crop",
        "x": 24,
        "y": 804,
        "width": 660,
        "height": 1168,
        "description": "Official EPUB pathway guide tarot-card crop, recovered from the validated Strength/Giant pilot crop.",
    },
    "PathwaySymbol": {
        "operation": "crop",
        "x": 472,
        "y": 305,
        "width": 486,
        "height": 486,
        "description": "Official EPUB pathway guide central symbol crop, recovered from the reviewed Sleepless/Darkness symbol pilot crop.",
    }
}

PRESET_ALIASES = {
    "PathwayTarotCard": "PathwayTarotCard",
    "pathwaytarotcard": "PathwayTarotCard",
    "pathway-tarot-card": "PathwayTarotCard",
    "pathway-tarot": "PathwayTarotCard",
    "tarot-card": "PathwayTarotCard",
    "PathwaySymbol": "PathwaySymbol",
    "pathwaysymbol": "PathwaySymbol",
    "pathway-symbol": "PathwaySymbol",
    "pathway-symbol-crop": "PathwaySymbol",
    "symbol": "PathwaySymbol",
}

OPERATION_ALIASES = {
    "Crop": "crop",
    "crop": "crop",
    "Extract": "extract-epub-images",
    "ExtractEpubImages": "extract-epub-images",
    "Extract-Images": "extract-epub-images",
    "List-Epub-Images": "extract-epub-images",
    "List-Images": "extract-epub-images",
    "extract": "extract-epub-images",
    "extractepubimages": "extract-epub-images",
    "extract-epub-images": "extract-epub-images",
    "extract-images": "extract-epub-images",
    "listepubimages": "extract-epub-images",
    "list-epub-images": "extract-epub-images",
    "list-images": "extract-epub-images",
}

IMAGE_TYPES = [
    "Cover",
    "FrontMatter",
    "VolumeCover",
    "EndOfVolume",
    "Pathways",
    "Characters",
    "Locations",
    "Artwork",
    "Map",
    "BackCover",
    "Other",
]


@dataclass
class EpubImage:
    image_number: int
    spine_index: int
    image_type: str
    volume: int | None
    title: str | None
    xhtml_path: str
    xhtml_file: str
    image_path: str
    image_file: str
    alt: str | None
    output_path: str | None = None


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repeatable local image operations.")
    parser.add_argument("--operation", choices=sorted(OPERATION_ALIASES), default="crop")
    parser.add_argument("--preset", choices=sorted(PRESET_ALIASES))
    parser.add_argument("--list-presets", action="store_true")
    parser.add_argument("--source-image")
    parser.add_argument("--output-image")
    parser.add_argument("--x", type=positive_int)
    parser.add_argument("--y", type=positive_int)
    parser.add_argument("--width", type=positive_int)
    parser.add_argument("--height", type=positive_int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--epub-path", default="Source/Lord of Mysteries - Book 1.epub")
    parser.add_argument("--output-dir", default=".tmp/epub-images")
    parser.add_argument("--start-image-number", type=positive_int, default=1)
    parser.add_argument("--end-image-number", type=positive_int, default=9999)
    parser.add_argument("--volume", type=int, action="append")
    parser.add_argument("--image-type", choices=IMAGE_TYPES + ["All"], action="append")
    parser.add_argument("--entry-name-pattern")
    parser.add_argument("--image-name-pattern")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def normalize_operation(operation: str) -> str:
    return OPERATION_ALIASES[operation]


def normalize_preset(preset: str | None) -> str | None:
    if preset is None:
        return None
    return PRESET_ALIASES[preset]


def list_presets() -> None:
    for name in sorted(PRESETS):
        preset = PRESETS[name]
        print(
            f"{name}: operation={preset['operation']} "
            f"x={preset['x']} y={preset['y']} "
            f"width={preset['width']} height={preset['height']} "
            f"- {preset['description']}"
        )


def resolve_crop(args: argparse.Namespace) -> tuple[str, int, int, int, int]:
    operation = args.operation
    x = args.x
    y = args.y
    width = args.width
    height = args.height

    if args.preset:
        preset = PRESETS[args.preset]
        operation = preset["operation"]
        x = preset["x"]
        y = preset["y"]
        width = preset["width"]
        height = preset["height"]

    if operation != "crop":
        raise ValueError(f"Unsupported operation: {operation}")

    if x is None or y is None or width is None or height is None:
        raise ValueError("Crop requires --x, --y, --width, and --height, or a preset that supplies them.")

    if width <= 0 or height <= 0:
        raise ValueError("Crop requires positive width and height.")

    return operation, x, y, width, height


def crop_image(source_image: Path, output_image: Path, x: int, y: int, width: int, height: int, force: bool) -> None:
    if not source_image.exists():
        raise FileNotFoundError(f"Source image not found: {source_image}")

    if output_image.exists() and not force:
        raise FileExistsError(f"Output image already exists. Use --force to overwrite: {output_image}")

    output_image.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source_image) as source:
        right = x + width
        bottom = y + height
        if right > source.width or bottom > source.height:
            raise ValueError(
                f"Crop rectangle x={x} y={y} width={width} height={height} "
                f"exceeds source size {source.width}x{source.height}."
            )

        cropped = source.crop((x, y, right, bottom))
        cropped.save(output_image)


class ImgTagParser:
    def __init__(self, xhtml: str):
        self.xhtml = xhtml

    def find(self) -> list[dict[str, str | None]]:
        tags = []
        for match in re.finditer(r"<img\b[^>]*>", self.xhtml, flags=re.IGNORECASE):
            tag = match.group(0)
            src_match = re.search(r'\bsrc\s*=\s*"([^"]+)"', tag, flags=re.IGNORECASE)
            if not src_match:
                continue
            alt_match = re.search(r'\balt\s*=\s*"([^"]*)"', tag, flags=re.IGNORECASE)
            tags.append(
                {
                    "src": html.unescape(src_match.group(1)),
                    "alt": html.unescape(alt_match.group(1)) if alt_match else None,
                }
            )
        return tags


def xhtml_title(xhtml: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", xhtml, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return html.unescape(match.group(1).strip())


def epub_relative_path(base_path: str, relative_path: str) -> str:
    base_directory = posixpath.dirname(base_path)
    return posixpath.normpath(posixpath.join(base_directory, relative_path))


def volume_from_href(href: str, title: str | None, current_volume: int | None) -> int | None:
    leaf = posixpath.basename(href)
    if re.match(r"^(side_stories.*|artwork\d*|world_map|back_cover)\.xhtml$", leaf):
        return None

    file_match = re.search(r"volume_(\d+)_", href)
    if file_match:
        return int(file_match.group(1))

    if title:
        title_match = re.search(r"^Volume\s+(\d+):", title)
        if title_match:
            return int(title_match.group(1))

    return current_volume


def image_type(href: str, title: str | None, alt: str | None) -> str:
    leaf = posixpath.basename(href)
    title = title or ""

    if leaf == "cover.xhtml":
        return "Cover"
    if leaf == "back_cover.xhtml":
        return "BackCover"
    if leaf == "world_map.xhtml":
        return "Map"
    if leaf in {"copyright.xhtml", "foreword.xhtml", "synopsis.xhtml", "table_of_contents.xhtml"}:
        return "FrontMatter"
    if re.search(r"^Volume\s+\d+:", title):
        return "VolumeCover"
    if re.search(r"end_of", leaf):
        return "EndOfVolume"
    if title == "Pathways Guide" or re.search(r"pathways", leaf):
        return "Pathways"
    if title == "Characters" or re.search(r"character|tarot", leaf):
        return "Characters"
    if title == "Locations" or re.search(r"location", leaf):
        return "Locations"
    if title in {"Image Gallery", "Artwork"} or re.search(r"image_gallery|artwork", leaf):
        return "Artwork"

    return "Other"


def selected_image(image: EpubImage, args: argparse.Namespace) -> bool:
    if image.image_number < args.start_image_number or image.image_number > args.end_image_number:
        return False

    selected_types = args.image_type or ["All"]
    if "All" not in selected_types and image.image_type not in selected_types:
        return False

    if args.volume and image.volume not in args.volume:
        return False

    if args.entry_name_pattern:
        if not (
            fnmatch.fnmatchcase(image.xhtml_path, args.entry_name_pattern)
            or fnmatch.fnmatchcase(image.xhtml_file, args.entry_name_pattern)
        ):
            return False

    if args.image_name_pattern:
        if not (
            fnmatch.fnmatchcase(image.image_path, args.image_name_pattern)
            or fnmatch.fnmatchcase(image.image_file, args.image_name_pattern)
        ):
            return False

    return True


def safe_alt(value: str | None) -> str:
    if not value or not value.strip():
        return "image"
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value)


def discover_epub_images(epub_path: Path) -> list[EpubImage]:
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB not found: {epub_path}")

    images: list[EpubImage] = []
    with zipfile.ZipFile(epub_path) as epub:
        try:
            opf_bytes = epub.read("OEBPS/content.opf")
        except KeyError as exc:
            raise FileNotFoundError("EPUB content.opf not found at OEBPS/content.opf") from exc

        root = ET.fromstring(opf_bytes)
        namespace = {"opf": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}

        if namespace:
            manifest_items = root.findall("opf:manifest/opf:item", namespace)
            spine_items = root.findall("opf:spine/opf:itemref", namespace)
        else:
            manifest_items = root.findall("manifest/item")
            spine_items = root.findall("spine/itemref")

        manifest = {item.attrib["id"]: item.attrib["href"] for item in manifest_items if "id" in item.attrib and "href" in item.attrib}

        current_volume: int | None = None
        in_side_stories = False
        image_number = 0
        spine_index = 0

        for item_ref in spine_items:
            spine_index += 1
            id_ref = item_ref.attrib.get("idref")
            if not id_ref or id_ref not in manifest:
                continue

            href = manifest[id_ref]
            if not href.startswith("Text/") or not href.endswith(".xhtml"):
                continue

            xhtml_path = f"OEBPS/{href}"
            try:
                xhtml = epub.read(xhtml_path).decode("utf-8")
            except KeyError:
                continue

            title = xhtml_title(xhtml)
            if href.startswith("Text/side_stories"):
                current_volume = None
                in_side_stories = True

            href_volume = None if in_side_stories and not re.search(r"volume_\d+_", href) else volume_from_href(href, title, current_volume)

            if re.search(r"volume_(\d+)_", href) or (title and re.search(r"^Volume\s+\d+:", title)):
                current_volume = href_volume
                in_side_stories = False

            for tag in ImgTagParser(xhtml).find():
                image_number += 1
                image_path = epub_relative_path(xhtml_path, str(tag["src"]))
                images.append(
                    EpubImage(
                        image_number=image_number,
                        spine_index=spine_index,
                        image_type=image_type(href, title, tag["alt"]),
                        volume=href_volume,
                        title=title,
                        xhtml_path=xhtml_path,
                        xhtml_file=posixpath.basename(xhtml_path),
                        image_path=image_path,
                        image_file=posixpath.basename(image_path),
                        alt=tag["alt"],
                    )
                )

    return images


def extract_epub_images(args: argparse.Namespace) -> int:
    if args.start_image_number > args.end_image_number:
        raise ValueError("start image number cannot be greater than end image number.")
    if args.start_image_number < 1 or args.end_image_number < 1:
        raise ValueError("image number filters are 1-based and must be at least 1.")

    epub_path = Path(args.epub_path)
    output_dir = Path(args.output_dir)
    images = [image for image in discover_epub_images(epub_path) if selected_image(image, args)]

    with zipfile.ZipFile(epub_path) as epub:
        for image in images:
            if args.extract:
                extension = Path(image.image_file).suffix
                filename = (
                    f"{image.image_number:04d}-spine-{image.spine_index:04d}-"
                    f"{image.image_type.lower()}-{safe_alt(image.alt)}{extension}"
                )
                destination = output_dir / filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with epub.open(image.image_path) as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target)
                except KeyError as exc:
                    raise FileNotFoundError(f"Image entry not found in EPUB: {image.image_path}") from exc
                image.output_path = str(destination.resolve())

    if args.json:
        rows = []
        for image in images:
            row = asdict(image)
            row.pop("xhtml_file", None)
            row.pop("image_file", None)
            rows.append(row)
        print(json.dumps(rows, indent=2))
    else:
        for image in images:
            volume_text = f"Vol {image.volume}" if image.volume is not None else "Vol -"
            extract_text = f" | Extracted: {image.output_path}" if image.output_path else ""
            print(
                f"Image {image.image_number} | Spine {image.spine_index} | {image.image_type} | "
                f"{volume_text} | {image.xhtml_file} | {image.image_file} | {image.title} | "
                f"Alt: {image.alt}{extract_text}"
            )

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.operation = normalize_operation(args.operation)
    args.preset = normalize_preset(args.preset)

    if args.list_presets:
        list_presets()
        return 0

    if args.operation == "extract-epub-images":
        return extract_epub_images(args)

    if not args.source_image:
        parser.error("--source-image is required unless --list-presets is used.")

    if not args.output_image:
        parser.error("--output-image is required unless --list-presets is used.")

    operation, x, y, width, height = resolve_crop(args)
    source_image = Path(args.source_image)
    output_image = Path(args.output_image)
    crop_image(source_image, output_image, x, y, width, height, args.force)

    print(
        f"Wrote {output_image} from {source_image} using {operation} "
        f"x={x} y={y} width={width} height={height}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
