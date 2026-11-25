# LLM-5 · Klargør tekst til RAG

Ingestion læser `.txt`-filerne i `viden_bibliotek/`, deler dem op og gemmer tekst, kildeoplysninger og embeddings i en lokal SQLite-database. Start fra projektroden i PowerShell. Scriptet bruger Python 3.10 eller nyere og standardbiblioteket.

## Tjek dokumenter og chunks

```powershell
python -m rag.ingest --dry-run
```

PDF-udtrækkene deles først ved `[PAGE N]`. Den generelle guide deles ved `[SECTION …]`. Derefter deles hvert afsnit eller hver side i højst 180 ord med 30 ords overlap. Det hjælper med at bevare konteksten omkring et skel mellem to chunks. Et chunk har aldrig tekst fra to PDF-sider.

## Byg indekset

Start Ollama, og hent den flersprogede embeddingmodel én gang. Spørgsmål kan være på engelsk, og kildeteksterne kan være på dansk eller engelsk.

```powershell
ollama pull bge-m3
python -m rag.ingest
```

Hvis du allerede har startet projektets Ollama-container via `ollama_setup`, kan du bruge `docker exec ollama ollama pull bge-m3` i stedet for den første kommando. Standardadressen er `http://localhost:11434`. Angiv `--ollama-url` ved en anden port.

Databasen ligger i `.cache/rag/knowledge.sqlite3`. Den genereres lokalt og er dækket af repoets eksisterende Git-ignore for `.cache/`. Ved en ny kørsel erstatter scriptet indekset i én SQLite-transaktion, efter at alle embeddings er hentet.

## Data til LLM-7

| Tabel | Felter |
| --- | --- |
| `rag_index` | `embedding_model` og `dimensions` til valg og kontrol af søgevektoren. |
| `rag_chunks` | `id`, `source_file`, `title`, `page`, `section`, `source_url`, `text` og `embedding`. `embedding` er en JSON-liste af tal. |

Brug `rag.embeddings.embed_texts` med modellen fra `rag_index` til at embedde søgespørgsmålet, og læs de gemte vektorer med `json.loads`. Det giver LLM-7 det nødvendige input til cosine similarity og top-k.

`source_url` peger på PDF-siden, når konverteringen har et direkte PDF-link. Ellers bruges den registrerede kildewebside, hvis den findes. `source_file`, `page` og `section` følger altid den tilgængelige lokation i tekstkilden.
