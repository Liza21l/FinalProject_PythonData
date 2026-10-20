from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "user_clusters.csv"
MODEL_DIR = PROJECT_ROOT / "ml_pipeline" / "saved_models"
MODEL_PATH = MODEL_DIR / "random_forest_model.joblib"
REPORT_PATH = PROJECT_ROOT / "data" / "random_forest_report.txt"

RANDOM_STATE = 42

# Ознаки, за якими модель оцінюватиме активність.
# total_events не включаємо, бо саме на його основі
# визначатимемо high_engagement.
FEATURE_COLUMNS = [
    "views",
    "carts",
    "purchases",
    "remove_from_cart",
    "session_count",
    "avg_session_duration_seconds",
    "cluster",
]


def main():
    print("Завантажуємо дані...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Файл не знайдено: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print(f"Кількість користувачів: {len(df):,}")

    required_columns = set(FEATURE_COLUMNS + ["total_events"])
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"У файлі немає колонок: {missing_columns}"
        )

    # Перевіряємо числові значення.
    for column in FEATURE_COLUMNS + ["total_events"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    df = df.dropna(
        subset=FEATURE_COLUMNS + ["total_events"]
    ).copy()

    if df.empty:
        raise ValueError("Після очищення не залишилося даних.")

    # Визначаємо високу активність за медіаною.
    median_events = df["total_events"].median()

    df["high_engagement"] = (
        df["total_events"] > median_events
    ).astype(int)

    print(f"Медіана total_events: {median_events}")
    print("\nРозподіл цільової змінної:")
    print(df["high_engagement"].value_counts().sort_index())

    X = df[FEATURE_COLUMNS]
    y = df["high_engagement"]

    if y.nunique() < 2:
        raise ValueError(
            "Цільова змінна має лише один клас. "
            "Навчити класифікатор неможливо."
        )

    print("\nРозділяємо дані на навчальну та тестову вибірки...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(f"Навчальна вибірка: {len(X_train):,}")
    print(f"Тестова вибірка: {len(X_test):,}")

    # Для GridSearchCV використовуємо підвибірку,
    # щоб не запускати дорогий пошук на мільйонах рядків.
    grid_sample_size = min(100_000, len(X_train))

    X_grid = X_train.sample(
        n=grid_sample_size,
        random_state=RANDOM_STATE
    )

    y_grid = y_train.loc[X_grid.index]

    print(
        f"\nРозмір вибірки для GridSearchCV: "
        f"{len(X_grid):,}"
    )

    # Невелика сітка параметрів.
    # Кожна комбінація перевіряється за допомогою крос-валідації.
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [10, 20],
        "min_samples_split": [2, 5],
    }

    base_model = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced"
    )

    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        scoring="f1",
        cv=3,
        n_jobs=-1,
        verbose=1
    )

    print("\nЗапускаємо GridSearchCV...")

    grid_search.fit(X_grid, y_grid)

    print("\nНайкращі параметри:")
    print(grid_search.best_params_)

    print(f"Найкращий F1 під час CV: {grid_search.best_score_:.4f}")

    # Навчаємо фінальну модель на всій навчальній вибірці
    # з найкращими параметрами.
    print("\nНавчаємо фінальну модель...")

    best_model = RandomForestClassifier(
        **grid_search.best_params_,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced"
    )

    best_model.fit(X_train, y_train)

    print("\nОцінюємо модель на тестовій вибірці...")

    y_pred = best_model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(
        y_test, y_pred, zero_division=0
    )
    recall = recall_score(
        y_test, y_pred, zero_division=0
    )
    f1 = f1_score(
        y_test, y_pred, zero_division=0
    )

    report = classification_report(
        y_test,
        y_pred,
        zero_division=0
    )

    matrix = confusion_matrix(y_test, y_pred)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(best_model, MODEL_PATH)

    report_text = f"""
RANDOM FOREST — РЕЗУЛЬТАТИ

Кількість користувачів: {len(df)}
Медіана total_events: {median_events}

Найкращі параметри:
{grid_search.best_params_}

Найкращий F1 під час GridSearchCV:
{grid_search.best_score_:.4f}

Метрики на тестовій вибірці:
Accuracy:  {accuracy:.4f}
Precision: {precision:.4f}
Recall:    {recall:.4f}
F1-score:  {f1:.4f}

Матриця помилок:
{matrix}

Classification report:
{report}
"""

    REPORT_PATH.write_text(
        report_text,
        encoding="utf-8"
    )

    print(report_text)

    print(f"\nМодель збережено: {MODEL_PATH}")
    print(f"Звіт збережено: {REPORT_PATH}")


if __name__ == "__main__":
    main()