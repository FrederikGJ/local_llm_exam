# Sammenligningsøvelse · lineær regression vs. lokal LLM + RAG

Et lille eksperiment ved siden af applikationen. Begge metoder skal forudsige den annoncerede månedlige husleje i København ud fra lejlighedens areal i m². De får de samme 6 testinput, og de bliver målt mod de samme faktiske værdier.

| Mappe | Indhold |
| --- | --- |
| [`regression/`](regression/) | Datasættet, split, lineær regression (script og notebook). |
| [`experiment_rag/`](experiment_rag/) | Lokal LLM + RAG over træningsrækkerne (script og notebook) og retrieval-loggen. |
| `compare.py` | Samler de gemte forudsigelser i [`results.md`](results.md). |

## Data og split

`regression/dataset.csv` har 300 rækker: 10 rigtige BoligPortal-annoncer og 290 genererede rækker. Input er `area_m2`, og target er `monthly_rent_dkk`. Kolonnen `split` er den eneste kilde til delingen: 294 træningsrækker og 6 testrækker. Testrækkerne er de to rigtige testannoncer (85 og 117 m²) og fire genererede rækker (31, 60, 99 og 141 m²). Detaljer står i [`regression/README.md`](regression/README.md).

Hvad hver metode får:

- **Regression:** træner på de 294 træningsrækker og forudsiger de 6 testarealer.
- **LLM + RAG:** RAG-samlingen indeholder kun de 294 træningsrækker. For hver testcase hentes de 5 mest lignende eksempler med embeddings og cosine similarity. LLM'en får eksemplerne og testarealet som tekst. Den kalder ikke regressionsmodellen. Se [`experiment_rag/README.md`](experiment_rag/README.md) og [`experiment_rag/retrieval_log.md`](experiment_rag/retrieval_log.md).
- **LLM uden RAG:** samme LLM og systemprompt, men kun testarealet. Den er med for at vise, hvad retrieval ændrer.

Ingen af metoderne ser testlejen. Den bruges kun til at beregne fejlen.

## Kør

Fra projektroden med `.venv` aktiveret (se [`regression/README.md`](regression/README.md#kør)) og Ollama startet med `rag-llm` og `bge-m3` (se [`ollama/README.md`](../ollama/README.md)):

```bash
python experiments/regression/train_linear_regression.py
python -m experiments.experiment_rag.llm_rag_predict
python experiments/compare.py
```

## Resultater

Målt 25. november 2026 med `rag-llm` = `qwen:0.5b-chat-v1.5-q2_K`, `bge-m3`, top-5, `temperature 0` og `seed 42`. To kørsler gav samme tal. Fejl = |forudsagt − faktisk|, og MAE er gennemsnittet af fejlene over de 6 testcases.

| Areal | Type | Faktisk | Regression | Fejl | LLM + RAG | Fejl | LLM uden RAG | Fejl |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 31 m² | genereret | 9.300 kr. | 9.178 kr. | 122 kr. | 8.400 kr. | 900 kr. | 31 kr. | 9.269 kr. |
| 60 m² | genereret | 13.600 kr. | 13.210 kr. | 390 kr. | 13.350 kr. | 250 kr. | 60 kr. | 13.540 kr. |
| 85 m² | rigtig | 14.500 kr. | 16.686 kr. | 2.186 kr. | 19.850 kr. | 5.350 kr. | 85 kr. | 14.415 kr. |
| 99 m² | genereret | 16.550 kr. | 18.633 kr. | 2.083 kr. | 19.995 kr. | 3.445 kr. | 99 kr. | 16.451 kr. |
| 117 m² | rigtig | 20.486 kr. | 21.136 kr. | 650 kr. | 18.800 kr. | 1.686 kr. | 117 kr. | 20.369 kr. |
| 141 m² | genereret | 24.900 kr. | 24.473 kr. | 427 kr. | 23.700 kr. | 1.200 kr. | 141 kr. | 24.759 kr. |
| **MAE** | | | | **976 kr.** | | **2.138 kr.** | | **16.467 kr.** |

Tabellen er kopieret fra `results.md`. Kør `compare.py` igen, og opdatér den her, hvis data, model eller prompt ændres.

## Diskussion

**Regressionen vinder.** MAE er 976 kr. mod 2.138 kr. for LLM + RAG. Regressionen bruger alle 294 træningsrækker til at finde én linje (ca. 139 kr. pr. m² + 4.868 kr.) og interpolerer jævnt mellem dem. Data er næsten lineært, fordi de genererede rækker ser ud til at være lavet ud fra en lineær sammenhæng. Det giver regressionen en fordel. Begge metoder rammer for højt på den rigtige annonce på 85 m², som ligger under den generelle linje.

**LLM'en regner ikke. Den kopierer.** I alle 6 testcases svarede LLM + RAG med præcis lejen fra ét af de hentede eksempler. Fem gange var det eksempel #1, og én gang #5. Modellen interpolerer ikke mellem eksemplerne. Den virker som et opslag i det, retrieval finder. Kvaliteten afhænger derfor helt af retrieval.

**Retrieval sammenligner tekst og ikke tal.** Embeddingmodellen ser "85 m²" som tekst. For 85 m² hentede den også 35 og 155 m². For 99 m² hentede den 49 m² to gange, og for 60 m² hentede den 156 m² to gange. Når samme areal fandtes i træningsdata (31, 60 og 141 m²), lå det øverst. Ved 60 og 141 m² kopierede LLM'en det og fik en fejl på 250 og 1.200 kr. Ved 60 m² var LLM + RAG endda bedre end regressionen (250 mod 390 kr.). Ved 85 m² var top-1 et eksempel på 88 m² med høj leje, og fejlen blev 5.350 kr. Grafen "Hvad blev hentet?" i notebooken viser det.

**RAG hjalp tydeligt.** Uden RAG svarede modellen med arealet som husleje (85 m² → 85 kr.), og MAE blev 16.467 kr. Med RAG fik den en realistisk skala og rigtige eksempler at vælge imellem. Her kan vi demonstrere, hvordan retrieval påvirker svaret.

**Hvornår er en specialiseret model bedre?** Når input er tal med en stabil sammenhæng, og man har træningsdata. Regressionen er præcis, kan forklares med to tal, giver samme svar hver gang og tager mikrosekunder. Et LLM-kald tager sekunder. En LLM + RAG giver mere mening, når input er ustruktureret tekst, fx en annoncebeskrivelse, når svaret skal forklares i naturligt sprog, eller når der kun er få eksempler og meget baggrundsviden.

**Begrænsninger.** Kun 6 testcases, så MAE er usikker. 290 af 300 rækker er genererede, og metoden er ikke dokumenteret endnu. LLM'en er en meget lille model (0,5B parametre, 2-bit). Vi har kun prøvet én prompt og ét input (areal). Beliggenhed, antal værelser og stand er ikke med.

**Mulige forbedringer.** Hent eksempler efter areal (fx de nærmeste arealer eller et filter på metadata) i stedet for kun tekstlighed. Prøv en større model, fx `qwen3.5:2b`, og lad den ræsonnere før tallet. Saml flere rigtige annoncer.
