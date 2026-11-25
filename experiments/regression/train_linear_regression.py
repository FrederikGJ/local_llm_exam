import csv
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

DATA_DIR = Path(__file__).resolve().parent


def main() -> None:
    with (DATA_DIR / "dataset.csv").open(encoding="utf-8", newline="") as dataset:
        rows = list(csv.DictReader(dataset))

    X = [[float(row["area_m2"])] for row in rows]
    y = [float(row["monthly_rent_dkk"]) for row in rows]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    print(f"Træning: {len(X_train)} rækker")
    print(f"Test: {len(X_test)} rækker")

    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    for (x,), actual, predicted in zip(X_test, y_test, predictions):
        print(f"X = {x:g} | Faktisk: {actual:,.2f} | Forudsagt: {predicted:,.2f}")

    mae = mean_absolute_error(y_test, predictions)
    print(f"MAE: {mae:,.2f}")


if __name__ == "__main__":
    main()
