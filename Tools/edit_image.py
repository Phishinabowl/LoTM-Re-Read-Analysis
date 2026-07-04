import argparse
from pathlib import Path

from PIL import Image


PRESETS = {
    "PathwayTarotCard": {
        "operation": "crop",
        "x": 24,
        "y": 804,
        "width": 660,
        "height": 1168,
        "description": "Official EPUB pathway guide tarot-card crop, recovered from the validated Strength/Giant pilot crop.",
    }
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repeatable local image operations.")
    parser.add_argument("--operation", choices=["crop"], default="crop")
    parser.add_argument("--preset", choices=sorted(PRESETS))
    parser.add_argument("--list-presets", action="store_true")
    parser.add_argument("--source-image")
    parser.add_argument("--output-image")
    parser.add_argument("--x", type=positive_int)
    parser.add_argument("--y", type=positive_int)
    parser.add_argument("--width", type=positive_int)
    parser.add_argument("--height", type=positive_int)
    parser.add_argument("--force", action="store_true")
    return parser


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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_presets:
        list_presets()
        return 0

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
