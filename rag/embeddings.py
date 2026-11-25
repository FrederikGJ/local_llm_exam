"""Client for Ollama's local embedding API."""

import json
import math
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEFAULT_MODEL = "bge-m3"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


def embed_texts(texts: list[str], *, model: str, base_url: str) -> list[list[float]]:
    """Return one vector per input, in input order."""
    if not texts:
        return []

    request = Request(
        f"{base_url.rstrip('/')}/api/embed",
        data=json.dumps({"model": model, "input": texts, "truncate": False}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            payload = json.load(response)
    except HTTPError as error:
        detail = error.read(1024).decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {error.code} for {model}: {detail}") from error
    except (OSError, HTTPException) as error:
        raise RuntimeError(f"Could not reach Ollama at {base_url}: {error}") from error
    except ValueError as error:
        raise RuntimeError("Ollama returned an unreadable JSON response.") from error

    vectors = payload.get("embeddings") if isinstance(payload, dict) else None
    if not isinstance(vectors, list) or len(vectors) != len(texts):
        raise RuntimeError("Ollama did not return one embedding per input.")

    dimensions = None
    for vector in vectors:
        if not isinstance(vector, list) or not vector:
            raise RuntimeError("Ollama returned an empty or invalid vector.")
        if dimensions is None:
            dimensions = len(vector)
        if len(vector) != dimensions or not all(
            type(value) in (float, int) and math.isfinite(value) for value in vector
        ):
            raise RuntimeError("Ollama returned vectors with invalid values or dimensions.")
    return vectors
