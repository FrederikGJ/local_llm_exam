"""Ingest the knowledge library into a local SQLite vector store."""

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urldefrag

from rag.embeddings import DEFAULT_MODEL, DEFAULT_OLLAMA_URL, embed_texts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "viden_bibliotek"
DEFAULT_DATABASE = ROOT / ".cache" / "rag" / "knowledge.sqlite3"
CHUNK_WORDS = 180
OVERLAP_WORDS = 30
BATCH_SIZE = 16
PAGE_MARKER = re.compile(r"^\[PAGE (\d+)\][ \t]*$", re.MULTILINE)
SECTION_MARKER = re.compile(r"^\[(SECTION [^\]\n]+)\][ \t]*$", re.MULTILINE)
DOCUMENT_END = re.compile(r"\n={8,}\nEND OF (?:DOCUMENT|KNOWLEDGE BASE)\n=+\s*$")
DIVIDER = re.compile(r"^(?:={8,}|-{8,})[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    id: str
    source_file: str
    title: str
    page: int | None
    section: str | None
    source_url: str | None
    text: str

    @property
    def embedding_text(self) -> str:
        return "\n".join(part for part in (self.title, self.section, self.text) if part)


def header_value(header: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:[ \t]*([^\n]+)$", header, re.MULTILINE)
    value = match.group(1).strip() if match else ""
    return value if value and value != "-" else None


def chunk_text(text: str) -> Iterator[str]:
    words = DIVIDER.sub("", text).split()
    for start in range(0, len(words), CHUNK_WORDS - OVERLAP_WORDS):
        end = start + CHUNK_WORDS
        yield " ".join(words[start:end])
        if end >= len(words):
            break


def read_chunks(path: Path, source_dir: Path) -> Iterator[Chunk]:
    source_file = path.relative_to(source_dir).as_posix()
    text = DOCUMENT_END.sub("", path.read_text(encoding="utf-8-sig"))
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    pages = list(PAGE_MARKER.finditer(text))
    sections = [] if pages else list(SECTION_MARKER.finditer(text))
    markers = pages or sections
    header = text[:markers[0].start()] if markers else ""
    title = header_value(header, "SOURCE DOCUMENT") or header_value(header, "KNOWLEDGE BASE")
    title = title or path.stem.replace("_", " ")
    pdf_url = header_value(header, "Source URL")
    source_page = header_value(header, "Source page")

    if not markers:
        for index, content in enumerate(chunk_text(text)):
            yield Chunk(f"{source_file}:{index}", source_file, title, None, None, None, content)
        return

    for position, marker in enumerate(markers):
        end = markers[position + 1].start() if position + 1 < len(markers) else len(text)
        body = text[marker.end():end].strip()
        if body.startswith("(No extractable text on this page"):
            continue
        page = int(marker.group(1)) if pages else None
        section = marker.group(1) if sections else None
        link = pdf_url or source_page
        if pdf_url and page is not None:
            link = f"{urldefrag(pdf_url).url}#page={page}"
        for index, content in enumerate(chunk_text(body)):
            yield Chunk(f"{source_file}:{position}:{index}", source_file, title, page, section, link, content)


def write_store(database: Path, chunks: list[Chunk], vectors: list[list[float]], model: str) -> None:
    dimensions = len(vectors[0])
    if len(chunks) != len(vectors) or any(len(vector) != dimensions for vector in vectors):
        raise RuntimeError("Embedding count or dimensions changed across batches.")
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS rag_index (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                embedding_model TEXT NOT NULL,
                dimensions INTEGER NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                title TEXT NOT NULL,
                page INTEGER,
                section TEXT,
                source_url TEXT,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
        """)
        connection.execute("DELETE FROM rag_chunks")
        connection.executemany(
            "INSERT INTO rag_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                (chunk.id, chunk.source_file, chunk.title, chunk.page, chunk.section,
                 chunk.source_url, chunk.text, json.dumps(vector, separators=(",", ":")))
                for chunk, vector in zip(chunks, vectors, strict=True)
            ),
        )
        connection.execute("INSERT OR REPLACE INTO rag_index VALUES (1, ?, ?)", (model, dimensions))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="Count chunks without contacting Ollama.")
    args = parser.parse_args()

    try:
        files = sorted(args.source_dir.rglob("*.txt"))
        chunks = [chunk for path in files for chunk in read_chunks(path, args.source_dir)]
        if not chunks:
            raise RuntimeError(f"No indexable text in {args.source_dir}.")
        print(f"{len(files)} text files broken into {len(chunks)} chunks.", flush=True)
        if args.dry_run:
            return 0

        vectors: list[list[float]] = []
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            vectors.extend(embed_texts(
                [chunk.embedding_text for chunk in batch], model=args.model, base_url=args.ollama_url
            ))
            print(f"Embeddings: {len(vectors)}/{len(chunks)}", flush=True)
        write_store(args.db, chunks, vectors, args.model)
        print(f"Saved {len(chunks)} vectors to {args.db}.")
    except (OSError, RuntimeError, UnicodeError, sqlite3.Error) as error:
        print(f"Ingestion failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
