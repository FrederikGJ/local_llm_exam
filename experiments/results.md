# Resultater · regression vs. lokal LLM + RAG

Genereres af `python experiments/compare.py`. Overskriv ikke i hånden.

Fejl = |forudsagt − faktisk|. MAE = gennemsnittet af fejlene over de 6 testcases.

| Areal | Type | Faktisk | Regression | Fejl (Regression) | LLM + RAG | Fejl (LLM + RAG) | LLM uden RAG | Fejl (LLM uden RAG) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 31 m² | genereret | 9.300 kr. | 9.178 kr. | 122 kr. | 8.400 kr. | 900 kr. | 31 kr. | 9.269 kr. |
| 60 m² | genereret | 13.600 kr. | 13.210 kr. | 390 kr. | 13.350 kr. | 250 kr. | 60 kr. | 13.540 kr. |
| 85 m² | rigtig | 14.500 kr. | 16.686 kr. | 2.186 kr. | 19.850 kr. | 5.350 kr. | 85 kr. | 14.415 kr. |
| 99 m² | genereret | 16.550 kr. | 18.633 kr. | 2.083 kr. | 19.995 kr. | 3.445 kr. | 99 kr. | 16.451 kr. |
| 117 m² | rigtig | 20.486 kr. | 21.136 kr. | 650 kr. | 18.800 kr. | 1.686 kr. | 117 kr. | 20.369 kr. |
| 141 m² | genereret | 24.900 kr. | 24.473 kr. | 427 kr. | 23.700 kr. | 1.200 kr. | 141 kr. | 24.759 kr. |
| **MAE** |  |  |  | **976 kr.** |  | **2.138 kr.** |  | **16.467 kr.** |
