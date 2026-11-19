# scripts

Hjælpescripts til projektet.

## pdf_to_txt.py

Trækker teksten ud af PDF'erne i `viden_pdf/` og gemmer dem som `viden_bibliotek/pdf_<navn>.txt`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/pdf_to_txt.py
```

- Titel, udgiver (styrelse) og kildelinks hentes fra `scripts/pdf_sources.json`. Når du lægger en ny PDF ind, så tilføj den også dér.
- Teksten deles op med `[PAGE N]`, hvor N er sidenummeret i den originale PDF. Et kildelink til en bestemt side bliver så `<Source URL>#page=N`.
