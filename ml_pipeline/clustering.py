from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "user_features.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "user_clusters.csv"
MODEL_DIR = PROJECT_ROOT / "ml_pipeline" / "saved_models"

ELBOW_PATH = PROJECT_ROOT / "data" / "elbow_method.png"

RANDOM_STATE = 42
SAMPLE_SIZE = 100_000
MAX_CLUSTERS = 10

FEATURE_COLUMNS = [
    "views",
    "carts",
    "purchases",
    "remove_from_cart",
    "total_events",
    "session_count",
    "avg_session_duration_seconds",
]


def main():
    print("Завантажуємо дані...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Файл не знайдено: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print(f"Кількість користувачів: {len(df):,}")

    # Перевіряємо наявність необхідних колонок.
    missing_columns = set(FEATURE_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Не знайдено колонки: {missing_columns}"
        )

    # Перевіряємо числові дані.
    X = df[FEATURE_COLUMNS].copy()

    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([float("inf"), float("-inf")], float("nan"))

    if X.isna().any().any():
        raise ValueError(
            "Знайдено пропущені або некоректні значення. "
            "Потрібно перевірити user_features.csv."
        )

    if len(X) < 2:
        raise ValueError(
            "Для кластеризації потрібно щонайменше 2 користувачі."
        )

    print("\nМасштабуємо ознаки за допомогою StandardScaler...")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Для Elbow Method використовуємо випадкову вибірку.
    sample_size = min(SAMPLE_SIZE, len(X_scaled))

    sample_df = pd.DataFrame(X_scaled).sample(
        n=sample_size,
        random_state=RANDOM_STATE
    )

    X_sample = sample_df.to_numpy()

    print(
        f"Розмір вибірки для Elbow Method: "
        f"{len(X_sample):,}"
    )

    # Elbow Method.
    print("\nВиконуємо Elbow Method...")

    inertias = []

    cluster_range = range(1, MAX_CLUSTERS + 1)

    for k in cluster_range:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=10
        )

        model.fit(X_sample)

        inertias.append(model.inertia_)

        print(
            f"K = {k}: inertia = {model.inertia_:.2f}"
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 5))
    plt.plot(
        list(cluster_range),
        inertias,
        marker="o"
    )

    plt.title("Elbow Method")
    plt.xlabel("Number of clusters (K)")
    plt.ylabel("Inertia")
    plt.xticks(list(cluster_range))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(ELBOW_PATH, dpi=150)
    plt.close()

    print(f"\nГрафік збережено: {ELBOW_PATH}")

    print(
        "\nВідкрий графік elbow_method.png "
        "і подивись, де крива починає вирівнюватися."
    )

    # Тимчасове автоматичне значення.
    # Після перегляду графіка його можна змінити.
    optimal_k = 5

    print(
        f"\nНавчаємо фінальний KMeans з K = {optimal_k}..."
    )

    kmeans = KMeans(
        n_clusters=optimal_k,
        random_state=RANDOM_STATE,
        n_init=10
    )

    df["cluster"] = kmeans.fit_predict(X_scaled)

    # Зберігаємо дані з номерами кластерів.
    df.to_csv(OUTPUT_PATH, index=False)

    # Зберігаємо моделі та параметри масштабування.
    joblib.dump(
        scaler,
        MODEL_DIR / "kmeans_scaler.joblib"
    )

    joblib.dump(
        kmeans,
        MODEL_DIR / "kmeans_model.joblib"
    )

    # Підсумкова статистика.
    print("\n=== РОЗПОДІЛ КОРИСТУВАЧІВ ЗА КЛАСТЕРАМИ ===")

    print(
        df["cluster"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\n=== СЕРЕДНІ ПОКАЗНИКИ КЛАСТЕРІВ ===")

    print(
        df.groupby("cluster")[FEATURE_COLUMNS]
        .mean()
        .round(2)
        .to_string()
    )

    print("\nKMeans завершено!")
    print(f"Результат: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()