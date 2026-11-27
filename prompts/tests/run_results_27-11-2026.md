# Testresultater 27-11-2026

Kørt med `run_prompt_tests.py` mod `prompts/system_prompt.txt`. Kilden er CPR-uddraget fra Workindenmarks "Welcome to Denmark". Ollama kørte lokalt på CPU.

| Test | `qwen:0.5b-chat-v1.5-q2_K` (standard) | `qwen3:4b` |
| --- | --- | --- |
| `legit`: What is a CPR number and how do I get one? | Forkert. Opfinder, at CPR-nummeret hænger sammen med patientens sygehistorie. Ingen kildehenvisning, og svaret gentager sig selv til sidst. | Korrekt. Bruger kun kilden, nummererede trin, forklarer Borgerservice og har `Sources:` til sidst. Trin 1–3 mangler `[Source 1]`. |
| `offtopic`: Who won the US midterm elections? | Forkert. Ignorerer fallback-reglen og finder på et svar (kalder 3. november 2020 for midtvejsvalg). | Korrekt. Kun fallback-sætningen. |

**Konklusion:** Prompten virker, når modellen er stor nok. Standardmodellen følger hverken 4T'erne eller fallback-reglen og hallucinerer. `qwen3:4b` er tænkende og tager flere minutter pr. svar på CPU.
