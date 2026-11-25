# Lejebolig · lokal LLM + RAG

Anden halvdel af sammenligningsøvelsen. Den lokale LLM forudsiger husleje ud fra areal for de samme 6 testcases som regressionen. Resultater og diskussion står i [`../README.md`](../README.md).

## Hvad LLM'en har adgang til

| Del | Indhold |
| --- | --- |
| RAG-samling | De 294 træningsrækker fra `../regression/dataset.csv`, én kort tekst pr. række, fx `Apartment in Copenhagen, 88 m². Monthly rent: 19850 DKK.` Ingen testrækker. |
| Lager | `.cache/rag/rent_examples.sqlite3`. Samme tabeller som `rag.ingest` (`rag_index`, `rag_chunks`), men en separat fil, så eksemplerne ikke blandes med vidensbiblioteket. |
| Embeddings | `bge-m3` via Ollama, samme klient som `rag.ingest` (`rag.embeddings.embed_texts`). |
| Retrieval | Søgeteksten `Apartment in Copenhagen, <areal> m². Monthly rent:` embeddes. Alle 294 eksempler rangeres efter cosine similarity, og top 5 kommer med i prompten. |
| LLM | `rag-llm` (som standard `qwen:0.5b-chat-v1.5-q2_K`). `temperature 0` og `seed 42`, så kørslen kan gentages. |
| Svarformat | Ollamas structured output (`format` med et JSON-schema) tvinger svaret til `{"monthly_rent_dkk": <heltal>}`. |
| Uden RAG | Samme LLM og systemprompt, men uden eksempler. Bruges til at se, hvad retrieval ændrer. |

`load_dataset()` i `llm_rag_predict.py` returnerer kun arealet fra testrækkerne. Testlejen indlæses først i `compare.py` og i notebookens trin 5, når fejlen skal måles. LLM'en får kun tekst. Den kalder ikke regressionsmodellen og kører ingen kode.

`retrieval_log.md` viser for hver testcase de hentede eksempler med cosine-score, den fulde prompt og LLM'ens rå svar.

## Prompt og 4T

Systemprompten står i `SYSTEM_PROMPT` i `llm_rag_predict.py`:

| T | I prompten |
| --- | --- |
| Traits | "an experienced rental valuer for the Copenhagen apartment market" |
| Task | Estimér den annoncerede månedlige husleje ud fra arealet, uden aconto og depositum. Med RAG: brug eksemplerne fra træningsdata. |
| Tone | Præcis og saglig, ingen forklaring. |
| Target | Et program læser svaret og sammenligner det med andre estimater, så svaret skal være JSON. |

Prompterne er på engelsk. I en hurtig prøve før JSON-tvangen svarede modellen på dansk med tekst uden tal, mens den på engelsk gav tal.

## Kør

Ollama skal køre med `rag-llm` og `bge-m3`. `docker compose up -d` i `ollama/` henter begge (se [`ollama/README.md`](../../ollama/README.md)). Python-miljøet er beskrevet i [`../regression/README.md`](../regression/README.md#kør).

Script fra projektroden:

```bash
python -m experiments.experiment_rag.llm_rag_predict
```

Det bygger RAG-samlingen, spørger LLM'en med og uden RAG og gemmer `predictions_llm.csv` og `retrieval_log.md`. Brug `--llm` til en anden model, `-k` til et andet antal eksempler og `--ollama-url` ved en anden port.

Notebook med de samme trin, tabeller og grafer:

```bash
jupyter notebook experiments/experiment_rag/llm_rag.ipynb
```

Kør `python experiments/regression/train_linear_regression.py` først, hvis `../regression/predictions_regression.csv` mangler. Notebookens sidste trin sammenligner med den.
