# Artwork

This folder tracks official EPUB artwork metadata and any narrowly selected page-ready assets.

Bulk extracted artwork and derivative working crops are local staging assets, like the source EPUB and subtitles. Keep them out of Git:

- `Artwork/extracted/`
- `Artwork/tarot-cards/`

Use [official-epub-image-map.md](official-epub-image-map.md) to preserve source order, local staging paths, classifications, and planned article mappings without uploading the full extracted asset set.

When a page actually embeds an image and the maintainer has intentionally selected it for repository use, copy only that specific page-ready asset into a tracked location such as `Artwork/page-assets/` and link the article to that selected file. Do not bulk-promote extracted images or crop sets.
