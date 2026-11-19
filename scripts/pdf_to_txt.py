#!/usr/bin/env python3
"""Udtræk tekst fra PDF-filerne i viden_pdf/ til .txt-filer i viden_bibliotek/.

Hver .txt-fil får en header med titel, udgiver (styrelse/myndighed) og kildelinks
fra scripts/pdf_sources.json, og teksten deles op med [PAGE N]-markører, så RAG'en
kan henvise til den præcise side (fx <Source URL>#page=N).

Kørsel (fra repo-roden):
    python scripts/pdf_to_txt.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = REPO_ROOT / "viden_pdf"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "viden_bibliotek"
# Lives in scripts/ (not viden_pdf/, which is gitignored) so the metadata is versioned.
SOURCES_FILE = Path(__file__).resolve().parent / "pdf_sources.json"
OUTPUT_PREFIX = "pdf_"
SEPARATOR = "=" * 80

# Dehyphenate words split across lines; ligatures and special whitespace are
# deliberately NOT preserved, so "ﬂ" becomes "fl" etc.
TEXT_FLAGS = pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_MEDIABOX_CLIP

# A line starting like this begins a new list item instead of continuing a paragraph.
LIST_ITEM_RE = re.compile(r"^(?:[•●▪◦■►→✓*]|\d{1,2}[.)])\s")
# A line ending in a URL cut after "/" or "-" continues without a space on the next line.
BROKEN_URL_RE = re.compile(r"(?:https?://|www\.|\w\.(?:dk|com|eu|org)/)\S*[/-]$")
# Navigation buttons (arrows) in interactive PDFs carry no content.
NAV_ONLY_RE = re.compile(r"^[←→↑↓\s]+$")


def load_sources() -> dict[str, dict[str, str]]:
    if not SOURCES_FILE.exists():
        print(f"ADVARSEL: {SOURCES_FILE} findes ikke - kildeinfo bliver tom.", file=sys.stderr)
        return {}
    with SOURCES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def output_name(pdf_path: Path) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "_", pdf_path.stem.lower()).strip("_")
    return f"{OUTPUT_PREFIX}{slug}.txt"


def clean_block(text: str) -> str:
    """Join the hard-wrapped lines of one text block into paragraphs/list items."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\xad\n", "").replace("\xad", "")  # soft hyphens

    items: list[str] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue
        if items and not LIST_ITEM_RE.match(line):
            joiner = "" if BROKEN_URL_RE.search(items[-1]) else " "
            items[-1] = f"{items[-1]}{joiner}{line}"
        else:
            items.append(line)
    text = "\n".join(items)
    return "" if NAV_ONLY_RE.match(text) else text


def page_text(page: pymupdf.Page) -> str:
    blocks = page.get_text("blocks", flags=TEXT_FLAGS)  # content-stream order keeps columns intact
    paragraphs = [clean_block(b[4]) for b in blocks if b[6] == 0]
    return "\n\n".join(p for p in paragraphs if p)


def build_header(pdf_path: Path, meta: dict[str, str], page_count: int) -> str:
    source_url = meta.get("source_url") or "-"
    page_hint = (
        f"Link to a page with {source_url}#page=N."
        if source_url != "-"
        else "No direct PDF link - use the source page."
    )
    lines = [
        SEPARATOR,
        f"SOURCE DOCUMENT: {meta.get('title') or pdf_path.stem}",
        f"Publisher: {meta.get('publisher') or 'unknown'}",
        f"Published: {meta.get('published') or 'unknown'}",
        f"Source URL: {source_url}",
        f"Source page: {meta.get('source_page') or '-'}",
        f"Original file: {pdf_path.parent.name}/{pdf_path.name}",
        f"Pages: {page_count}",
        f"Page markers: [PAGE N] = page N in the original PDF. {page_hint}",
        SEPARATOR,
    ]
    return "\n".join(lines)


def convert(pdf_path: Path, meta: dict[str, str], output_dir: Path) -> tuple[Path, int, list[int]]:
    with pymupdf.open(pdf_path) as doc:
        if not meta.get("title") and doc.metadata.get("title"):
            meta = {**meta, "title": doc.metadata["title"]}

        parts = [build_header(pdf_path, meta, doc.page_count)]
        empty_pages: list[int] = []
        for number, page in enumerate(doc, start=1):
            text = page_text(page)
            if not text:
                empty_pages.append(number)
                text = "(No extractable text on this page - probably only images.)"
            parts.append(f"[PAGE {number}]\n{text}")
        parts.append(f"{SEPARATOR}\nEND OF DOCUMENT\n{SEPARATOR}")

        out_path = output_dir / output_name(pdf_path)
        out_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        return out_path, doc.page_count, empty_pages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR, help="mappe med PDF-filer")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="mappe til .txt-filer")
    args = parser.parse_args()

    pdf_paths = sorted(args.input_dir.glob("*.pdf"))
    if not pdf_paths:
        print(f"Ingen PDF-filer i {args.input_dir}", file=sys.stderr)
        return 1

    sources = load_sources()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_paths:
        meta = sources.get(pdf_path.name)
        if meta is None:
            print(f"ADVARSEL: {pdf_path.name} mangler i {SOURCES_FILE.name} (titel/udgiver/link).", file=sys.stderr)
            meta = {}
        out_path, pages, empty = convert(pdf_path, meta, args.output_dir)
        note = f" (sider uden tekst: {empty})" if empty else ""
        print(f"{pdf_path.name} -> {out_path.parent.name}/{out_path.name}: {pages} sider{note}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
