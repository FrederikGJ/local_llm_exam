# LLM-13 · Lejebolig

Vi estimerer den annoncerede månedlige husleje i kroner ud fra lejlighedens areal i m². Den enkelte annonce er en observation.

Vi valgte de første ti annoncer på [BoligPortals liste over lejligheder i København](https://www.boligportal.dk/lejligheder/k%C3%B8benhavn/) ved opslag 23. november 2026. CSV-filen indeholder linket til hver annonce. Lejen er den annoncerede månedlige husleje. Særskilt aconto, depositum og forudbetalt husleje indgår ikke. Annoncer kan udløbe. Dette øvelsesdatasæt på ti annoncer beskriver et lille udsnit af markedet.

Notebooken læser `dataset.csv` og deler de ti rækker med `train_test_split` i otte træningsrækker og to testrækker. Modellen trænes med `X_train` og `y_train`. Derefter forudsiger den på `X_test` og måler den gennemsnitlige absolutte fejl (MAE) med `y_test`. Grafen viser modellen og testresultaterne.

## Kør i Jupyter Notebook

Pak zippen ud i projektroden. Åbn Anaconda Prompt i samme mappe. Opret miljøet første gang.

```bat
conda create -n llm-exam-regression python=3.12 scikit-learn=1.8 notebook matplotlib
conda activate llm-exam-regression
jupyter notebook experiments/regression/linear_regression.ipynb
```

Hvis miljøet allerede er oprettet, kan du aktivere det og køre `conda install notebook matplotlib`, hvis pakkerne mangler. Kør notebookens celler fra toppen med **Shift+Enter**. Behold `dataset.csv` ved siden af notebooken.

Kør eventuelt scriptet med `python experiments/regression/train_linear_regression.py`.
