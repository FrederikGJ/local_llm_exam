# Sammenligningsøvelse: lineær regression mod lokal LLM + RAG

Et lille eksperiment ved siden af applikationen. Spørgsmålet er, om en lokal sprogmodel med retrieval kan forudsige husleje lige så godt som en specialiseret model. Begge metoder estimerer den annoncerede månedlige husleje for en lejlighed i København ud fra arealet i m², og de måles på de samme seks testcases.

**Kort fortalt.** Lineær regression vinder klart med en MAE på 976 kr. mod 2.138 kr. for LLM + RAG. Sprogmodellen regner ikke selv, men gentager lejen fra ét af de hentede eksempler, så resultatet står og falder med retrieval.

| Sti | Indhold |
|:---|:---|
| [`regression/`](regression/) | Datasættet, det faste split og den lineære regression (script og notebook) |
| [`experiment_rag/`](experiment_rag/) | Lokal LLM + RAG (script og notebook) og retrieval-loggen |
| [`compare.py`](compare.py) | Samler forudsigelserne i [`results.md`](results.md) |

## Design

Datasættet [`regression/dataset.csv`](regression/dataset.csv) har 300 lejligheder: 10 rigtige BoligPortal-annoncer og 290 genererede rækker. Kolonnen `split` deler det i 294 træningsrækker og 6 testrækker, nemlig to rigtige annoncer (85 og 117 m²) og fire genererede (31, 60, 99 og 141 m²). Detaljerne står i [`regression/README.md`](regression/README.md).

Tre metoder får de samme testarealer. **Regressionen** tilpasses de 294 træningsrækker. **LLM + RAG** får testarealet og de fem mest lignende træningsrækker som tekst, hentet med `bge-m3`-embeddings og cosine similarity. Den kalder ikke regressionsmodellen. **LLM uden RAG** får kun testarealet og viser, hvad retrieval tilfører. Ingen af metoderne ser testlejen, som kun bruges til at beregne fejlen. Prompt og retrieval er beskrevet i [`experiment_rag/README.md`](experiment_rag/README.md).

## Resultater

Målt 25. november 2026 med `rag-llm` (`qwen:0.5b-chat-v1.5-q2_K`), `bge-m3`, top-5, `temperature 0` og `seed 42`. To kørsler gav samme tal. Fejlen er |forudsagt − faktisk|, og MAE er gennemsnittet over de seks testcases.

**Månedlig husleje i kr.** Absolut fejl i parentes. Fed er mindste fejl i rækken, og \* markerer en rigtig annonce.

| Testcase | Faktisk | Regression | LLM + RAG | LLM uden RAG |
|:---|---:|---:|---:|---:|
| 31 m² | 9.300 | **9.178 (122)** | 8.400 (900) | 31 (9.269) |
| 60 m² | 13.600 | 13.210 (390) | **13.350 (250)** | 60 (13.540) |
| 85 m²\* | 14.500 | **16.686 (2.186)** | 19.850 (5.350) | 85 (14.415) |
| 99 m² | 16.550 | **18.633 (2.083)** | 19.995 (3.445) | 99 (16.451) |
| 117 m²\* | 20.486 | **21.136 (650)** | 18.800 (1.686) | 117 (20.369) |
| 141 m² | 24.900 | **24.473 (427)** | 23.700 (1.200) | 141 (24.759) |
| **MAE** | | **976** | 2.138 | 16.467 |

Tallene stammer fra [`results.md`](results.md), som `compare.py` genererer. Opdatér tabellen her, hvis data, model eller prompt ændres.

## Diskussion

**Regressionen udjævner, LLM'en kopierer.** Regressionen finder én linje gennem alle 294 træningsrækker (ca. 139 kr. pr. m² plus 4.868 kr.) og udjævner dermed støjen i de enkelte annoncer. LLM + RAG svarede i alle seks testcases med præcis lejen fra ét af de hentede eksempler, fem gange eksempel #1. Den interpolerer ikke, men arver hele støjen fra det eksempel, den vælger. At de genererede rækker ser ud til at følge en lineær sammenhæng, giver regressionen en ekstra fordel.

**Retrieval sammenligner tekst, ikke tal.** Embeddingmodellen læser »85 m²« som tekst. For 85 m² blev derfor også 35 og 155 m² hentet, og for 60 m² to eksempler på 156 m². Når det præcise areal fandtes i træningsdata, lå det øverst, og ved 60 m² slog LLM + RAG faktisk regressionen (250 mod 390 kr.). Ved 85 m² var top-1 derimod et dyrt eksempel på 88 m², og fejlen blev 5.350 kr. Figur 1 i [`experiment_rag/llm_rag.ipynb`](experiment_rag/llm_rag.ipynb) viser mønsteret.

**RAG er stadig afgørende.** Uden eksempler svarede modellen med arealet som husleje (85 m² → 85 kr.) og fik en MAE på 16.467 kr. Retrieval giver den skalaen og noget konkret at vælge imellem.

**Hvornår hvad?** Ved numerisk input med en stabil sammenhæng er en specialiseret model at foretrække. Den er mere præcis, kan forklares med to tal og svarer på mikrosekunder frem for sekunder. LLM + RAG giver mere mening ved ustruktureret input som annoncetekster, når svaret skal forklares i naturligt sprog, eller når der er få eksempler, men meget baggrundsviden.

**Begrænsninger og næste skridt.** Seks testcases giver en usikker MAE, 290 af 300 rækker er genererede med en endnu udokumenteret metode, og LLM'en er meget lille (0,5B parametre, 2-bit). Kun én prompt og ét input er afprøvet, så beliggenhed, værelser og stand indgår ikke. De oplagte forbedringer er at hente eksempler efter afstand i areal frem for tekstlighed, at prøve en større model som `qwen3.5:2b` med ræsonnement før tallet og at samle flere rigtige annoncer.

## Kør

Fra projektroden med `.venv` aktiveret (se [`regression/README.md`](regression/README.md#kør)) og Ollama startet med `rag-llm` og `bge-m3` (se [`ollama/README.md`](../ollama/README.md)):

```bash
python experiments/regression/train_linear_regression.py   # → regression/predictions_regression.csv
python -m experiments.experiment_rag.llm_rag_predict        # → experiment_rag/predictions_llm.csv og retrieval_log.md
python experiments/compare.py                               # → results.md
```

De to notebooks, [`regression/linear_regression.ipynb`](regression/linear_regression.ipynb) og [`experiment_rag/llm_rag.ipynb`](experiment_rag/llm_rag.ipynb), gennemgår de samme trin med tabeller og figurer.
