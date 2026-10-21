
from pathlib import Path

import joblib
import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "user_clusters.csv"
MODEL_PATH = (
    PROJECT_ROOT
    / "ml_pipeline"
    / "saved_models"
    / "random_forest_model.joblib"
)

RANDOM_STATE = 42

FEATURE_COLUMNS = [
    "session_count",
    "avg_session_duration_seconds",
]


def main():
    print("Завантажуємо дані...")

    df = pd.read_csv(DATA_PATH)

    df["total_events"] = pd.to_numeric(
        df["total_events"], errors="coerce"
    )

    for column in FEATURE_COLUMNS:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    df = df.replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    df = df.dropna(
        subset=FEATURE_COLUMNS + ["total_events"]
    ).copy()

    median_events = df["total_events"].median()

    df["high_engagement"] = (
        df["total_events"] > median_events
    ).astype(int)

    X = df[FEATURE_COLUMNS]
    y = df["high_engagement"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(f"Навчальна вибірка: {len(X_train):,}")
    print(f"Тестова вибірка: {len(X_test):,}")

    # 1. Базова модель: завжди прогнозує найчастіший клас.
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_train, y_train)

    baseline_predictions = baseline.predict(X_test)

    # 2. Завантажуємо вже навчену модель Random Forest.
    model = joblib.load(MODEL_PATH)
    rf_predictions = model.predict(X_test)

    # 3. Порівнюємо результати.
    models = {
        "Baseline": baseline_predictions,
        "Random Forest": rf_predictions,
    }

    print("\n=== ПОРІВНЯННЯ МОДЕЛЕЙ ===")

    results = []

    for name, predictions in models.items():
        results.append({
            "Модель": name,
            "Accuracy": accuracy_score(y_test, predictions),
            "Precision": precision_score(
                y_test, predictions, zero_division=0
            ),
            "Recall": recall_score(
                y_test, predictions, zero_division=0
            ),
            "F1-score": f1_score(
                y_test, predictions, zero_division=0
            ),
        })

    results_df = pd.DataFrame(results)

    print(results_df.to_string(
        index=False,
        formatters={
            "Accuracy": "{:.4f}".format,
            "Precision": "{:.4f}".format,
            "Recall": "{:.4f}".format,
            "F1-score": "{:.4f}".format,
        }
    ))

    print("\nПорівняння завершено!")


if __name__ == "__main__":
    main()
