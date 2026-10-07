"""Synthetic media behavior; no real EPUB, artwork or canonical content is read."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[3]
before = sys.path[:]
try:
    spec = importlib.util.spec_from_file_location("native_media_images", ROOT / "Tools/Commands/Media/edit_image.py")
    images = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = images
    spec.loader.exec_module(images)
finally:
    sys.path[:] = before


@pytest.mark.integration
def test_epub_cli_searches_unicode_literal_terms_and_filters_chapters(tmp_path):
    epub = tmp_path / "synthetic book.epub"
    with zipfile.ZipFile(epub, "w") as archive:
        archive.writestr(
            "OEBPS/Text/volume_1_chapter_1.xhtml",
            "<html><body><h1>Chapter 1: Fixture</h1><p>café A+B</p></body></html>",
        )
        archive.writestr(
            "OEBPS/Text/volume_1_chapter_2.xhtml", "<html><body><h1>Chapter 2: Fixture</h1><p>café</p></body></html>"
        )
    command = [
        sys.executable,
        str(ROOT / "Tools/Commands/Media/search_epub.py"),
        "--root",
        str(ROOT),
        "--epub-path",
        str(epub),
        "--pattern",
        "café|A+B",
        "--end-chapter",
        "1",
        "--json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stderr
    rows = json.loads(result.stdout)
    assert {row["term"] for row in rows} == {"café", "A+B"}
    assert {row["chapter"] for row in rows} == {1}


@pytest.mark.integration
def test_epub_cli_rejects_bad_zip_without_mutating_input(tmp_path):
    epub = tmp_path / "broken.epub"
    epub.write_bytes(b"not a zip")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "Tools/Commands/Media/search_epub.py"),
            "--root",
            str(ROOT),
            "--epub-path",
            str(epub),
            "--pattern",
            "fixture",
        ],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert b"not a valid zip" in result.stderr
    assert epub.read_bytes() == b"not a zip"


def test_crop_pixels_dimensions_and_overwrite_protection(tmp_path):
    source, output = tmp_path / "source.png", tmp_path / "crop.png"
    image = Image.new("RGB", (4, 3), "blue")
    image.putpixel((1, 1), (255, 0, 0))
    image.save(source)
    original = source.read_bytes()
    images.crop_image(source, output, 1, 1, 2, 1, False)
    with Image.open(output) as cropped:
        assert cropped.size == (2, 1)
        assert [cropped.getpixel((x, 0)) for x in range(2)] == [(255, 0, 0), (0, 0, 255)]
    saved = output.read_bytes()
    with pytest.raises(FileExistsError):
        images.crop_image(source, output, 0, 0, 1, 1, False)
    assert output.read_bytes() == saved
    images.crop_image(source, output, 0, 0, 1, 1, True)
    with Image.open(output) as cropped:
        assert cropped.size == (1, 1)
    assert source.read_bytes() == original


def test_crop_rejects_out_of_bounds_without_output(tmp_path):
    source, output = tmp_path / "source.png", tmp_path / "crop.png"
    Image.new("RGB", (2, 2), "blue").save(source)
    with pytest.raises(ValueError, match="exceeds source size"):
        images.crop_image(source, output, 1, 1, 2, 2, False)
    assert not output.exists()
