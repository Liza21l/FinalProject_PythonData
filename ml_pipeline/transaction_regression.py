
from pathlib import Path

import joblib
import pandas as pd

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "ml_pipeline" / "saved_models"

FEATURES_FILE = DATA_DIR / "user_features.csv"
TARGET_FILE = DATA_DIR / "user_purchase_totals.csv"
REPORT_FILE = DATA_DIR / "transaction_regression_report.txt"
MODEL_FILE = MODEL_DIR / "transaction_regression.joblib"


def main():
    print("Завантажуємо ознаки користувачів...")
    features = pd.read_csv(FEATURES_FILE)

    print("Завантажуємо суми покупок...")
    targets = pd.read_csv(TARGET_FILE)

    # Об'єднуємо ознаки та цільову змінну за user_id.
    # Inner join залишає користувачів, які мають покупки.
    data = features.merge(
        targets,
        on="user_id",
        how="inner",
        validate="one_to_one",
    )

    feature_columns = [
        "views",
        "carts",
        "purchases",
        "remove_from_cart",
        "total_events",
        "session_count",
        "avg_session_duration_seconds",
    ]

    data = data.dropna(
        subset=feature_columns + ["total_purchase_amount"]
    )

    X = data[feature_columns]
    y = data["total_purchase_amount"]

    print(f"Користувачів у вибірці: {len(data):,}")
    print(f"Ознак для моделі: {len(feature_columns)}")

    # Відокремлюємо дані для перевірки моделі.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    # Проста базова модель для порівняння.
    baseline = DummyRegressor(strategy="mean")
    baseline.fit(X_train, y_train)
    baseline_predictions = baseline.predict(X_test)

    # Навчаємо Random Forest для регресії.
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    print("Навчаємо RandomForestRegressor...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    # Метрики базової моделі.
    baseline_r2 = r2_score(y_test, baseline_predictions)
    baseline_mae = mean_absolute_error(
        y_test,
        baseline_predictions,
    )

    # Метрики Random Forest.
    model_r2 = r2_score(y_test, predictions)
    model_mae = mean_absolute_error(y_test, predictions)

    print("\n=== РЕЗУЛЬТАТИ РЕГРЕСІЇ ===")
    print(
        f"Baseline R²: {baseline_r2:.4f} | "
        f"Baseline MAE: {baseline_mae:.2f}"
    )
    print(
        f"Random Forest R²: {model_r2:.4f} | "
        f"Random Forest MAE: {model_mae:.2f}"
    )

    print("\n=== ПРИКЛАДИ ПРОГНОЗІВ ===")
    examples = pd.DataFrame({
        "actual_amount": y_test.iloc[:10].values,
        "predicted_amount": predictions[:10].round(2),
    })
    print(examples.to_string(index=False))

    # Зберігаємо звіт.
    report = [
        "ЗВІТ: РЕГРЕСІЯ СУМИ ПОКУПОК КОРИСТУВАЧА",
        "=" * 45,
        f"Користувачів у вибірці: {len(data)}",
        f"Навчальна вибірка: {len(X_train)}",
        f"Тестова вибірка: {len(X_test)}",
        f"Кількість ознак: {len(feature_columns)}",
        "",
        "Baseline:",
        f"R² = {baseline_r2:.4f}",
        f"MAE = {baseline_mae:.2f}",
        "",
        "Random Forest Regressor:",
        f"R² = {model_r2:.4f}",
        f"MAE = {model_mae:.2f}",
        "",
        "Ознаки:",
        ", ".join(feature_columns),
        "",
        "Цільова змінна: total_purchase_amount",
        "Оцінка стосується користувачів, які здійснили покупки.",
        "Ознаки та суми належать до одного періоду, тому це не",
        "прогноз майбутніх витрат.",
    ]

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)

    print(f"\nЗвіт збережено: {REPORT_FILE}")
    print(f"Модель збережено: {MODEL_FILE}")


if __name__ == "__main__":
    main()
