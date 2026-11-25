"""Predict monthly rent with the local LLM + RAG, using only the training rows as RAG material.

1. Read experiments/regression/dataset.csv. The train rows become the RAG collection.
   From the test rows only the area is read. Their rent never reaches the LLM.
2. Embed the train rows and save them in a separate SQLite store with the same format as
   rag.ingest (.cache/rag/rent_examples.sqlite3). It is kept apart from the knowledge index.
3. For each test area: embed the question, rank the stored rows by cosine similarity, take top-k.
4. Ask the local LLM with the retrieved examples (LLM + RAG) and without them (LLM alone).
   The LLM only sees text. It never calls the regression model or runs any code.
5. Save predictions_llm.csv and retrieval_log.md (what was retrieved and what the LLM answered).

Run from the project root:  python -m experiments.experiment_rag.llm_rag_predict
"""

import argparse
import csv
import json
import math
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from rag.embeddings import DEFAULT_MODEL as DEFAULT_EMBED_MODEL
from rag.embeddings import DEFAULT_OLLAMA_URL, embed_texts
from rag.ingest import ROOT, Chunk, write_store

HERE = Path(__file__).resolve().parent
DATASET = ROOT / "experiments" / "regression" / "dataset.csv"
DEFAULT_DATABASE = ROOT / ".cache" / "rag" / "rent_examples.sqlite3"
PREDICTIONS = HERE / "predictions_llm.csv"
RETRIEVAL_LOG = HERE / "retrieval_log.md"
DEFAULT_LLM = "rag-llm"
DEFAULT_TOP_K = 5
BATCH_SIZE = 32

# 4T's: Traits (who the model is), Task (what to do), Tone (how), Target (who reads the answer).
SYSTEM_PROMPT = (
    "You are an experienced rental valuer for the Copenhagen apartment market. "  # Traits
    "Estimate the advertised monthly rent in Danish kroner (DKK) for one apartment from its "
    "floor area. Rent means the advertised monthly rent without utilities (aconto) and "
    "without deposit. "  # Task
    "Be precise and factual and do not explain your answer. "  # Tone
    "A program reads your reply and compares it with other estimates, so reply only with "
    'JSON in the form {"monthly_rent_dkk": <integer>}.'  # Target
)
RAG_INSTRUCTION = "Base your estimate on the reference examples from the training data."

# Ollama structured output: forces the reply to be JSON with one integer.
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"monthly_rent_dkk": {"type": "integer"}},
    "required": ["monthly_rent_dkk"],
}


def shown(path: Path) -> str:
    """Path relative to the project root when possible, for messages and the log."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def example_text(area: str, rent: str) -> str:
    return f"Apartment in Copenhagen, {area} m². Monthly rent: {rent} DKK."


def query_text(area: str) -> str:
    return f"Apartment in Copenhagen, {area} m². Monthly rent:"


def load_dataset() -> tuple[list[dict[str, str]], list[str]]:
    """Return the train rows and the test areas. Test rents are deliberately not returned."""
    with DATASET.open(encoding="utf-8", newline="") as dataset:
        rows = list(csv.DictReader(dataset))
    for line, row in enumerate(rows, start=2):
        row["id"] = f"dataset.csv:{line}"
    train = [row for row in rows if row["split"] == "train"]
    test_areas = [row["area_m2"] for row in rows if row["split"] == "test"]
    return train, test_areas


def build_collection(train: list[dict[str, str]], db: Path, model: str, url: str) -> None:
    chunks = [
        Chunk(
            id=row["id"],
            source_file=DATASET.relative_to(ROOT).as_posix(),
            title="Rental apartments in Copenhagen (training data)",
            page=None,
            section=row["data_type"],
            source_url=row["source_url"] or None,
            text=example_text(row["area_m2"], row["monthly_rent_dkk"]),
        )
        for row in train
    ]
    vectors: list[list[float]] = []
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        vectors.extend(embed_texts([chunk.text for chunk in batch], model=model, base_url=url))
    write_store(db, chunks, vectors, model)
    print(f"RAG-samling: {len(chunks)} træningsrækker gemt i {shown(db)}", flush=True)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def retrieve(db: Path, query: str, k: int, url: str) -> list[tuple[float, str, str]]:
    """Return the top-k stored rows as (similarity, id, text)."""
    with closing(sqlite3.connect(db)) as connection:
        model, = connection.execute("SELECT embedding_model FROM rag_index").fetchone()
        stored = connection.execute("SELECT id, text, embedding FROM rag_chunks").fetchall()
    query_vector, = embed_texts([query], model=model, base_url=url)
    scored = [
        (cosine(query_vector, json.loads(embedding)), chunk_id, text)
        for chunk_id, text, embedding in stored
    ]
    return sorted(scored, key=lambda hit: hit[0], reverse=True)[:k]


def ask_llm(user_prompt: str, system_prompt: str, model: str, url: str) -> tuple[int, str]:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": ANSWER_SCHEMA,
        "options": {"temperature": 0, "seed": 42},
    }
    request = Request(
        f"{url.rstrip('/')}/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=300) as response:
            answer = json.load(response)["message"]["content"]
    except HTTPError as error:
        detail = error.read(1024).decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {error.code} for {model}: {detail}") from error
    except OSError as error:
        raise RuntimeError(f"Could not reach Ollama at {url}: {error}") from error
    try:
        return int(json.loads(answer)["monthly_rent_dkk"]), answer
    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"Could not read a rent from the LLM reply: {answer!r}") from error


def rag_prompt(area: str, hits: list[tuple[float, str, str]]) -> str:
    examples = "\n".join(f"- {text}" for _, _, text in hits)
    return (
        f"Reference examples (training data):\n{examples}\n\n"
        f"Apartment to estimate: {area} m². What is the monthly rent in DKK?"
    )


def kroner(amount: int) -> str:
    return f"{amount:,} kr.".replace(",", ".")


def plain_prompt(area: str) -> str:
    return f"Apartment to estimate: {area} m². What is the monthly rent in DKK?"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--llm", default=DEFAULT_LLM, help="Chat model (default: rag-llm).")
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("-k", "--top-k", type=int, default=DEFAULT_TOP_K)
    args = parser.parse_args()

    train, test_areas = load_dataset()
    train_by_id = {row["id"]: row for row in train}
    rag_system = f"{SYSTEM_PROMPT} {RAG_INSTRUCTION}"
    try:
        build_collection(train, args.db, args.embed_model, args.ollama_url)
        results = []
        for area in test_areas:
            hits = retrieve(args.db, query_text(area), args.top_k, args.ollama_url)
            prompt = rag_prompt(area, hits)
            with_rag, rag_answer = ask_llm(prompt, rag_system, args.llm, args.ollama_url)
            without_rag, plain_answer = ask_llm(plain_prompt(area), SYSTEM_PROMPT, args.llm, args.ollama_url)
            print(f"{area} m²: LLM+RAG {kroner(with_rag)} | LLM uden RAG {kroner(without_rag)}", flush=True)
            results.append((area, hits, prompt, with_rag, rag_answer, without_rag, plain_answer))
    except (OSError, RuntimeError, sqlite3.Error) as error:
        print(f"Fejl: {error}", file=sys.stderr)
        return 1

    with PREDICTIONS.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["area_m2", "llm_rag_rent_dkk", "llm_no_rag_rent_dkk"])
        writer.writerows((area, with_rag, without_rag) for area, _, _, with_rag, _, without_rag, _ in results)

    log = [
        "# Retrieval-log · LLM + RAG",
        "",
        "Genereres af `python -m experiments.experiment_rag.llm_rag_predict`. Overskriv ikke i hånden.",
        "",
        f"- LLM: `{args.llm}` (temperature 0, seed 42, svar tvunget til JSON med ét heltal)",
        f"- Embeddingmodel: `{args.embed_model}` · top-k: {args.top_k} · cosine similarity",
        f"- RAG-samling: {len(train)} træningsrækker fra `dataset.csv` i `{shown(args.db)}`."
        " Ingen testrækker.",
        "",
        "## Systemprompt med RAG",
        "",
        f"> {rag_system}",
        "",
        "Uden RAG bruges samme systemprompt uden den sidste sætning, og brugerprompten er kun"
        f" `{plain_prompt('<areal>')}`",
    ]
    for area, hits, prompt, with_rag, rag_answer, without_rag, plain_answer in results:
        hit_rows = [train_by_id[chunk_id] for _, chunk_id, _ in hits]
        distance = sum(abs(float(row["area_m2"]) - float(area)) for row in hit_rows) / len(hit_rows)
        log += [
            "",
            f"## Testcase: {area} m²",
            "",
            f"Søgetekst: `{query_text(area)}`",
            "",
            "| # | Cosine | Hentet tekst | Type | Kilde |",
            "|---:|---:|---|---|---|",
        ]
        for rank, ((similarity, chunk_id, text), row) in enumerate(zip(hits, hit_rows), start=1):
            kind = "rigtig" if row["data_type"] == "real" else "genereret"
            source = f"[annonce]({row['source_url']})" if row["source_url"] else f"`{chunk_id}`"
            log.append(f"| {rank} | {similarity:.4f} | {text} | {kind} | {source} |")
        log += [
            "",
            f"Gennemsnitlig arealafstand mellem testcase og hentede eksempler: {distance:.1f} m².",
            "",
            "Brugerprompt med RAG:",
            "",
            "```text",
            prompt,
            "```",
            "",
            f"- Svar med RAG: `{rag_answer.strip()}` → **{kroner(with_rag)}**",
            f"- Svar uden RAG: `{plain_answer.strip()}` → **{kroner(without_rag)}**",
        ]
    RETRIEVAL_LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"Gemt: {shown(PREDICTIONS)} og {shown(RETRIEVAL_LOG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
