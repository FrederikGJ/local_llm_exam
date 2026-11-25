# Retrieval-log · LLM + RAG

Genereres af `python -m experiments.experiment_rag.llm_rag_predict`. Overskriv ikke i hånden.

- LLM: `rag-llm` (temperature 0, seed 42, svar tvunget til JSON med ét heltal)
- Embeddingmodel: `bge-m3` · top-k: 5 · cosine similarity
- RAG-samling: 294 træningsrækker fra `dataset.csv` i `.cache/rag/rent_examples.sqlite3`. Ingen testrækker.

## Systemprompt med RAG

> You are an experienced rental valuer for the Copenhagen apartment market. Estimate the advertised monthly rent in Danish kroner (DKK) for one apartment from its floor area. Rent means the advertised monthly rent without utilities (aconto) and without deposit. Be precise and factual and do not explain your answer. A program reads your reply and compares it with other estimates, so reply only with JSON in the form {"monthly_rent_dkk": <integer>}. Base your estimate on the reference examples from the training data.

Uden RAG bruges samme systemprompt uden den sidste sætning, og brugerprompten er kun `Apartment to estimate: <areal> m². What is the monthly rent in DKK?`

## Testcase: 85 m²

Søgetekst: `Apartment in Copenhagen, 85 m². Monthly rent:`

| # | Cosine | Hentet tekst | Type | Kilde |
|---:|---:|---|---|---|
| 1 | 0.9070 | Apartment in Copenhagen, 88 m². Monthly rent: 19850 DKK. | genereret | `dataset.csv:234` |
| 2 | 0.8768 | Apartment in Copenhagen, 35 m². Monthly rent: 9100 DKK. | genereret | `dataset.csv:206` |
| 3 | 0.8730 | Apartment in Copenhagen, 83 m². Monthly rent: 15250 DKK. | genereret | `dataset.csv:95` |
| 4 | 0.8712 | Apartment in Copenhagen, 155 m². Monthly rent: 25850 DKK. | genereret | `dataset.csv:86` |
| 5 | 0.8710 | Apartment in Copenhagen, 83 m². Monthly rent: 15800 DKK. | genereret | `dataset.csv:27` |

Gennemsnitlig arealafstand mellem testcase og hentede eksempler: 25.4 m².

Brugerprompt med RAG:

```text
Reference examples (training data):
- Apartment in Copenhagen, 88 m². Monthly rent: 19850 DKK.
- Apartment in Copenhagen, 35 m². Monthly rent: 9100 DKK.
- Apartment in Copenhagen, 83 m². Monthly rent: 15250 DKK.
- Apartment in Copenhagen, 155 m². Monthly rent: 25850 DKK.
- Apartment in Copenhagen, 83 m². Monthly rent: 15800 DKK.

Apartment to estimate: 85 m². What is the monthly rent in DKK?
```

- Svar med RAG: `{"monthly_rent_dkk": 19850 }` → **19.850 kr.**
- Svar uden RAG: `{"monthly_rent_dkk": 85}` → **85 kr.**

## Testcase: 117 m²

Søgetekst: `Apartment in Copenhagen, 117 m². Monthly rent:`

| # | Cosine | Hentet tekst | Type | Kilde |
|---:|---:|---|---|---|
| 1 | 0.8799 | Apartment in Copenhagen, 115 m². Monthly rent: 18800 DKK. | genereret | `dataset.csv:107` |
| 2 | 0.8784 | Apartment in Copenhagen, 115 m². Monthly rent: 21000 DKK. | genereret | `dataset.csv:158` |
| 3 | 0.8732 | Apartment in Copenhagen, 116 m². Monthly rent: 21150 DKK. | genereret | `dataset.csv:162` |
| 4 | 0.8726 | Apartment in Copenhagen, 113 m². Monthly rent: 20000 DKK. | genereret | `dataset.csv:81` |
| 5 | 0.8712 | Apartment in Copenhagen, 111 m². Monthly rent: 19150 DKK. | genereret | `dataset.csv:109` |

Gennemsnitlig arealafstand mellem testcase og hentede eksempler: 3.0 m².

Brugerprompt med RAG:

```text
Reference examples (training data):
- Apartment in Copenhagen, 115 m². Monthly rent: 18800 DKK.
- Apartment in Copenhagen, 115 m². Monthly rent: 21000 DKK.
- Apartment in Copenhagen, 116 m². Monthly rent: 21150 DKK.
- Apartment in Copenhagen, 113 m². Monthly rent: 20000 DKK.
- Apartment in Copenhagen, 111 m². Monthly rent: 19150 DKK.

Apartment to estimate: 117 m². What is the monthly rent in DKK?
```

- Svar med RAG: `{"monthly_rent_dkk": 18800 }` → **18.800 kr.**
- Svar uden RAG: `{"monthly_rent_dkk": 117}` → **117 kr.**

## Testcase: 99 m²

Søgetekst: `Apartment in Copenhagen, 99 m². Monthly rent:`

| # | Cosine | Hentet tekst | Type | Kilde |
|---:|---:|---|---|---|
| 1 | 0.8824 | Apartment in Copenhagen, 89 m². Monthly rent: 19995 DKK. | rigtig | [annonce](https://www.boligportal.dk/lejligheder/k%C3%B8benhavn/89m2-3-vaer-id-5692241) |
| 2 | 0.8796 | Apartment in Copenhagen, 49 m². Monthly rent: 9600 DKK. | genereret | `dataset.csv:31` |
| 3 | 0.8745 | Apartment in Copenhagen, 49 m². Monthly rent: 10850 DKK. | genereret | `dataset.csv:70` |
| 4 | 0.8730 | Apartment in Copenhagen, 100 m². Monthly rent: 16700 DKK. | genereret | `dataset.csv:286` |
| 5 | 0.8721 | Apartment in Copenhagen, 98 m². Monthly rent: 18900 DKK. | genereret | `dataset.csv:125` |

Gennemsnitlig arealafstand mellem testcase og hentede eksempler: 22.4 m².

Brugerprompt med RAG:

```text
Reference examples (training data):
- Apartment in Copenhagen, 89 m². Monthly rent: 19995 DKK.
- Apartment in Copenhagen, 49 m². Monthly rent: 9600 DKK.
- Apartment in Copenhagen, 49 m². Monthly rent: 10850 DKK.
- Apartment in Copenhagen, 100 m². Monthly rent: 16700 DKK.
- Apartment in Copenhagen, 98 m². Monthly rent: 18900 DKK.

Apartment to estimate: 99 m². What is the monthly rent in DKK?
```

- Svar med RAG: `{"monthly_rent_dkk": 19995}` → **19.995 kr.**
- Svar uden RAG: `{"monthly_rent_dkk": 99 }` → **99 kr.**

## Testcase: 141 m²

Søgetekst: `Apartment in Copenhagen, 141 m². Monthly rent:`

| # | Cosine | Hentet tekst | Type | Kilde |
|---:|---:|---|---|---|
| 1 | 0.9357 | Apartment in Copenhagen, 141 m². Monthly rent: 23700 DKK. | genereret | `dataset.csv:122` |
| 2 | 0.8837 | Apartment in Copenhagen, 142 m². Monthly rent: 22550 DKK. | genereret | `dataset.csv:149` |
| 3 | 0.8828 | Apartment in Copenhagen, 140 m². Monthly rent: 27100 DKK. | genereret | `dataset.csv:272` |
| 4 | 0.8812 | Apartment in Copenhagen, 142 m². Monthly rent: 24800 DKK. | genereret | `dataset.csv:288` |
| 5 | 0.8797 | Apartment in Copenhagen, 41 m². Monthly rent: 10700 DKK. | genereret | `dataset.csv:48` |

Gennemsnitlig arealafstand mellem testcase og hentede eksempler: 20.6 m².

Brugerprompt med RAG:

```text
Reference examples (training data):
- Apartment in Copenhagen, 141 m². Monthly rent: 23700 DKK.
- Apartment in Copenhagen, 142 m². Monthly rent: 22550 DKK.
- Apartment in Copenhagen, 140 m². Monthly rent: 27100 DKK.
- Apartment in Copenhagen, 142 m². Monthly rent: 24800 DKK.
- Apartment in Copenhagen, 41 m². Monthly rent: 10700 DKK.

Apartment to estimate: 141 m². What is the monthly rent in DKK?
```

- Svar med RAG: `{"monthly_rent_dkk": 23700 }` → **23.700 kr.**
- Svar uden RAG: `{"monthly_rent_dkk": 141}` → **141 kr.**

## Testcase: 60 m²

Søgetekst: `Apartment in Copenhagen, 60 m². Monthly rent:`

| # | Cosine | Hentet tekst | Type | Kilde |
|---:|---:|---|---|---|
| 1 | 0.9318 | Apartment in Copenhagen, 60 m². Monthly rent: 13350 DKK. | genereret | `dataset.csv:186` |
| 2 | 0.8693 | Apartment in Copenhagen, 156 m². Monthly rent: 26000 DKK. | genereret | `dataset.csv:261` |
| 3 | 0.8656 | Apartment in Copenhagen, 62 m². Monthly rent: 16200 DKK. | genereret | `dataset.csv:63` |
| 4 | 0.8649 | Apartment in Copenhagen, 61 m². Monthly rent: 13450 DKK. | genereret | `dataset.csv:64` |
| 5 | 0.8648 | Apartment in Copenhagen, 156 m². Monthly rent: 26012 DKK. | rigtig | [annonce](https://www.boligportal.dk/lejligheder/k%C3%B8benhavn/156m2-5-vaer-id-5692489) |

Gennemsnitlig arealafstand mellem testcase og hentede eksempler: 39.0 m².

Brugerprompt med RAG:

```text
Reference examples (training data):
- Apartment in Copenhagen, 60 m². Monthly rent: 13350 DKK.
- Apartment in Copenhagen, 156 m². Monthly rent: 26000 DKK.
- Apartment in Copenhagen, 62 m². Monthly rent: 16200 DKK.
- Apartment in Copenhagen, 61 m². Monthly rent: 13450 DKK.
- Apartment in Copenhagen, 156 m². Monthly rent: 26012 DKK.

Apartment to estimate: 60 m². What is the monthly rent in DKK?
```

- Svar med RAG: `{"monthly_rent_dkk": 13350 }` → **13.350 kr.**
- Svar uden RAG: `{"monthly_rent_dkk": 60}` → **60 kr.**

## Testcase: 31 m²

Søgetekst: `Apartment in Copenhagen, 31 m². Monthly rent:`

| # | Cosine | Hentet tekst | Type | Kilde |
|---:|---:|---|---|---|
| 1 | 0.9218 | Apartment in Copenhagen, 31 m². Monthly rent: 8550 DKK. | genereret | `dataset.csv:170` |
| 2 | 0.8794 | Apartment in Copenhagen, 29 m². Monthly rent: 6800 DKK. | genereret | `dataset.csv:225` |
| 3 | 0.8734 | Apartment in Copenhagen, 29 m². Monthly rent: 7700 DKK. | genereret | `dataset.csv:224` |
| 4 | 0.8676 | Apartment in Copenhagen, 32 m². Monthly rent: 12050 DKK. | genereret | `dataset.csv:130` |
| 5 | 0.8644 | Apartment in Copenhagen, 30 m². Monthly rent: 8400 DKK. | genereret | `dataset.csv:91` |

Gennemsnitlig arealafstand mellem testcase og hentede eksempler: 1.2 m².

Brugerprompt med RAG:

```text
Reference examples (training data):
- Apartment in Copenhagen, 31 m². Monthly rent: 8550 DKK.
- Apartment in Copenhagen, 29 m². Monthly rent: 6800 DKK.
- Apartment in Copenhagen, 29 m². Monthly rent: 7700 DKK.
- Apartment in Copenhagen, 32 m². Monthly rent: 12050 DKK.
- Apartment in Copenhagen, 30 m². Monthly rent: 8400 DKK.

Apartment to estimate: 31 m². What is the monthly rent in DKK?
```

- Svar med RAG: `{"monthly_rent_dkk": 8400 }` → **8.400 kr.**
- Svar uden RAG: `{"monthly_rent_dkk": 31}` → **31 kr.**
