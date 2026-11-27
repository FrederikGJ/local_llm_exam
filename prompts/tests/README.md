# Test af 4T-systemprompten

`run_prompt_tests.py` stiller to lokale modeller et relevant spørgsmål og et spørgsmål uden for emnet. Systemprompten er `prompts/system_prompt.txt`. Et håndplukket uddrag fra `viden_bibliotek/` sendes med som kilde, fordi retrieval ikke er bygget endnu.

Kræver Python 3.10 eller nyere og en kørende Ollama på `http://localhost:11434` med begge modeller hentet. Kør fra projektroden:

```powershell
ollama pull qwen:0.5b-chat-v1.5-q2_K
ollama pull qwen3:4b
python prompts/tests/run_prompt_tests.py
```

Svarene skrives ud, når alle modeller har svaret. `qwen3:4b` kan tage flere minutter pr. svar på CPU.
