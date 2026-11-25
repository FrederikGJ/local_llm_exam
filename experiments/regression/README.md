# Lejebolig · lineær regression

Første halvdel af sammenligningsøvelsen. Hele øvelsen, resultaterne og diskussionen står i [`../README.md`](../README.md).

Vi estimerer den annoncerede månedlige husleje i kroner ud fra lejlighedens areal i m². En række er én lejlighed.

## Data

`dataset.csv` har 300 rækker.

| Kolonne | Indhold |
| --- | --- |
| `area_m2` | **Input.** Areal i m² (26–156). |
| `monthly_rent_dkk` | **Target.** Annonceret månedlig husleje i kr. |
| `source_url` | Link til annoncen. Kun for rigtige rækker. |
| `data_type` | `real` (rigtig annonce) eller `synthetic` (genereret). |
| `split` | `train` eller `test`. |

**10 rigtige annoncer.** De første ti annoncer på [BoligPortals liste over lejligheder i København](https://www.boligportal.dk/lejligheder/k%C3%B8benhavn/) ved opslag 23. november 2026. Lejen er den annoncerede månedlige husleje. Særskilt aconto, depositum og forudbetalt husleje indgår ikke. Annoncer kan udløbe.

**290 genererede rækker.** De er lavet for at få flere datapunkter end ti. Opgaven tillader at generere data.

### Sådan er de genererede rækker lavet

> **TODO (Mahdi):** Læg generatorscriptet i denne mappe, eller beskriv metoden her, så rækkerne kan genskabes.

Det kan vi se i selve data:

- Arealerne ligger mellem 26 og 156 m², samme spænd som de rigtige annoncer.
- Alle lejer er rundet til hele 50 kr.
- Hældningen er næsten den samme. En lineær tilpasning giver ca. 137 kr./m² for de 10 rigtige og ca. 139 kr./m² for de 290 genererede.
- De genererede rækker spreder sig ca. 1.400 kr. (standardafvigelse) omkring deres egen linje.

Det ligner en lineær sammenhæng fundet ud fra de rigtige annoncer plus tilfældig støj. Så er datasættet næsten lineært fra starten, og det giver lineær regression en fordel. Det er en begrænsning, vi bør nævne i synopsen.

## Train/test-split

Kolonnen `split` er den eneste kilde til delingen. Scriptet og notebooken læser den, og LLM + RAG-delen bruger den samme kolonne. Så får begge metoder de samme testinput, og testlejen bruges kun til at måle fejlen.

- **294 træningsrækker.**
- **6 testrækker:** de to rigtige testannoncer (85 og 117 m²) og fire genererede rækker på 31, 60, 99 og 141 m². De fire er valgt blandt de oprindelige testrækker som dem tættest på 30, 60, 100 og 140 m², så testen dækker hele arealspændet.

Oprindeligt var 60 rækker markeret som test. Opgaven siger, at "one or a few well-chosen test cases are sufficient" og "a small table of results". Derfor er de øvrige 54 flyttet til træning.

## Kør

Fra projektroden. Opret `.venv` første gang:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r experiments/requirements.txt
```

Script:

```bash
python experiments/regression/train_linear_regression.py
```

Det udskriver modellen, forudsigelserne og MAE og gemmer forudsigelserne i `predictions_regression.csv`. Filen bruges af `experiments/compare.py`.

Notebook:

```bash
jupyter notebook experiments/regression/linear_regression.ipynb
```

Kør cellerne fra toppen med **Shift+Enter**. Notebooken giver samme tal som scriptet, plus en tabel og en graf.

## Resultat

Modellen er `husleje ≈ 4.868 + 139,04 × areal`. MAE på de 6 testcases er 976 kr. Tabellen med alle tre metoder står i [`../README.md`](../README.md#resultater).
