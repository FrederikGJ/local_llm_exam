"""Compare linear regression and the local LLM + RAG on the same test cases.

Reads the actual rents from the test rows in regression/dataset.csv and the saved predictions
from regression/predictions_regression.csv and experiment_rag/predictions_llm.csv.
Prints a results table with absolute errors and MAE, and saves it as results.md.

Run from the project root after the two experiments:  python experiments/compare.py
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def kroner(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", ".") + " kr."


def main() -> None:
    test = [row for row in read_csv(HERE / "regression" / "dataset.csv") if row["split"] == "test"]
    regression = read_csv(HERE / "regression" / "predictions_regression.csv")
    llm = read_csv(HERE / "experiment_rag" / "predictions_llm.csv")
    if not (len(test) == len(regression) == len(llm)) or any(
        actual["area_m2"] != reg["area_m2"] or actual["area_m2"] != llm_row["area_m2"]
        for actual, reg, llm_row in zip(test, regression, llm)
    ):
        raise SystemExit("Testrækkerne passer ikke sammen. Kør begge eksperimenter igen.")

    methods = {
        "Regression": [float(row["predicted_rent_dkk"]) for row in regression],
        "LLM + RAG": [float(row["llm_rag_rent_dkk"]) for row in llm],
        "LLM uden RAG": [float(row["llm_no_rag_rent_dkk"]) for row in llm],
    }
    actuals = [float(row["monthly_rent_dkk"]) for row in test]

    header = "| Areal | Type | Faktisk | " + " | ".join(
        f"{name} | Fejl ({name})" for name in methods
    ) + " |"
    lines = [header, "|---:|---|---:|" + "---:|---:|" * len(methods)]
    order = sorted(range(len(test)), key=lambda index: float(test[index]["area_m2"]))
    for index in order:
        row = test[index]
        kind = "rigtig" if row["data_type"] == "real" else "genereret"
        cells = [f"{row['area_m2']} m²", kind, kroner(actuals[index])]
        for predictions in methods.values():
            cells += [kroner(predictions[index]), kroner(abs(predictions[index] - actuals[index]))]
        lines.append("| " + " | ".join(cells) + " |")

    mae_cells = ["**MAE**", "", ""]
    for predictions in methods.values():
        mae = sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(actuals)
        mae_cells += ["", f"**{kroner(mae)}**"]
    lines.append("| " + " | ".join(mae_cells) + " |")

    table = "\n".join(lines)
    print(table)
    RESULTS.write_text(
        "# Resultater · regression vs. lokal LLM + RAG\n\n"
        "Genereres af `python experiments/compare.py`. Overskriv ikke i hånden.\n\n"
        f"Fejl = |forudsagt − faktisk|. MAE = gennemsnittet af fejlene over de {len(test)} testcases.\n\n"
        f"{table}\n",
        encoding="utf-8",
    )
    print(f"\nGemt i {RESULTS.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
