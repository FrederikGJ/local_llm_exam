"""Train a linear regression on the train rows in dataset.csv and predict the test rows.

The split column in dataset.csv is the only source of the train/test split, so the
LLM + RAG experiment (experiments/experiment_rag/) uses exactly the same test cases.
"""

import csv
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

DATA_DIR = Path(__file__).resolve().parent
DATASET = DATA_DIR / "dataset.csv"
PREDICTIONS = DATA_DIR / "predictions_regression.csv"


def main() -> None:
    with DATASET.open(encoding="utf-8", newline="") as dataset:
        rows = list(csv.DictReader(dataset))

    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] == "test"]

    X_train = [[float(row["area_m2"])] for row in train]
    y_train = [float(row["monthly_rent_dkk"]) for row in train]
    X_test = [[float(row["area_m2"])] for row in test]
    y_test = [float(row["monthly_rent_dkk"]) for row in test]

    print(f"Træning: {len(X_train)} rækker")
    print(f"Test: {len(X_test)} rækker")

    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    print(f"Model: husleje = {model.intercept_:,.2f} + {model.coef_[0]:,.2f} * areal")

    for (x,), actual, predicted in zip(X_test, y_test, predictions):
        print(f"X = {x:g} | Faktisk: {actual:,.2f} | Forudsagt: {predicted:,.2f}")

    mae = mean_absolute_error(y_test, predictions)
    print(f"MAE: {mae:,.2f}")

    with PREDICTIONS.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["area_m2", "predicted_rent_dkk"])
        for (x,), predicted in zip(X_test, predictions):
            writer.writerow([f"{x:g}", round(float(predicted))])
    print(f"Forudsigelser gemt i {PREDICTIONS.relative_to(DATA_DIR.parents[1])}")


if __name__ == "__main__":
    main()
