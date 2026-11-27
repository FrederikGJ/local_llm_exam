# Lokal LLM (Ollama i Docker)

Kører Ollama i Docker. Som standard bruges den mindste Qwen-model, vi kunne finde: `qwen:0.5b-chat-v1.5-q2_K` (~300 MB). Den er bevidst dårlig, men kører på en hvilken som helst laptop uden GPU.

## Start

```bash
cd ollama
cp .env.example .env        # valgfrit - uden .env bruges standardværdierne
docker compose up -d
docker compose logs -f model-init   # vent på "Klar: rag-llm -> ..."
```

Ollama kører på `http://localhost:11434`. RAG-appen skal altid kalde modellen **`rag-llm`**. Det er et alias, der peger på `OLLAMA_MODEL` med `temperature` og `num_ctx` fra `.env`.

`model-init` henter også embeddingmodellen `EMBED_MODEL` (standard `bge-m3`, ~1,2 GB), som `rag/ingest.py` og `experiments/experiment_rag/` bruger. Første gang tager det et par minutter.

Test:
```bash
curl http://localhost:11434/api/chat -d '{"model":"rag-llm","messages":[{"role":"user","content":"Hvad er et CPR-nummer?"}],"stream":false}'
```

## Skift model

1. Ret `OLLAMA_MODEL` i `.env` til en model fra [ollama.com/library](https://ollama.com/library).
2. Kør `docker compose up -d`. Så hentes den nye model, og `rag-llm` peger på den.

Eksempler:

| Maskine | `OLLAMA_MODEL` | Størrelse |
|---|---|---|
| Laptop uden GPU (standard) | `qwen:0.5b-chat-v1.5-q2_K` | ~0,3 GB |
| Laptop, lidt bedre svar | `qwen3.5:2b` | ~3 GB |
| GPU med 8-12 GB VRAM | `qwen3.5:9b` | ~7 GB |
| Stor GPU med 24 GB+ VRAM | `qwen3.8:27b` | ~18 GB |

Gamle modeller fylder på disken. Se dem med `docker compose exec ollama ollama list`, og slet med `docker compose exec ollama ollama rm <model>`.

## Med NVIDIA GPU

Kræver NVIDIA-driver og [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
docker compose exec ollama ollama ps   # PROCESSOR skal vise "100% GPU"
```

## Stop

`docker compose down` stopper containerne. Modellerne bliver liggende i volumen `ollama_data`. Brug `docker compose down -v` for også at slette dem.
