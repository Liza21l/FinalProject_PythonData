from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FEATURES_PATH = PROJECT_ROOT / "data" / "user_features.csv"
CLUSTERS_PATH = PROJECT_ROOT / "data" / "user_clusters.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "pca_clusters.png"

RANDOM_STATE = 42
SAMPLE_SIZE = 5_000

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
    print("Завантажуємо дані користувачів...")

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Не знайдено файл: {FEATURES_PATH}"
        )

    if not CLUSTERS_PATH.exists():
        raise FileNotFoundError(
            f"Не знайдено файл: {CLUSTERS_PATH}"
        )

    features_df = pd.read_csv(FEATURES_PATH)
    clusters_df = pd.read_csv(
        CLUSTERS_PATH,
        usecols=["user_id", "cluster"]
    )

    missing_columns = (
        set(FEATURE_COLUMNS + ["user_id"])
        - set(features_df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"У user_features.csv немає колонок: "
            f"{missing_columns}"
        )

    if features_df["user_id"].duplicated().any():
        raise ValueError(
            "У user_features.csv знайдено повторні user_id."
        )

    if clusters_df["user_id"].duplicated().any():
        raise ValueError(
            "У user_clusters.csv знайдено повторні user_id."
        )

    print("Об'єднуємо ознаки з результатами кластеризації...")

    df = features_df.merge(
        clusters_df,
        on="user_id",
        how="inner",
        validate="one_to_one"
    )

    if df.empty:
        raise ValueError(
            "Не вдалося зіставити користувачів і кластери."
        )

    print(f"Зіставлено користувачів: {len(df):,}")

    sample_size = min(SAMPLE_SIZE, len(df))

    sample_df = df.sample(
        n=sample_size,
        random_state=RANDOM_STATE
    ).copy()

    X = sample_df[FEATURE_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce"
    )

    X = X.replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    valid_rows = X.notna().all(axis=1)

    X = X.loc[valid_rows]
    sample_df = sample_df.loc[valid_rows]

    if len(X) < 2:
        raise ValueError(
            "Недостатньо коректних рядків для PCA."
        )

    print(f"Розмір вибірки: {len(X):,}")
    print("Масштабуємо ознаки...")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Виконуємо PCA...")

    pca = PCA(n_components=2)

    coordinates = pca.fit_transform(X_scaled)

    plot_df = pd.DataFrame(
        coordinates,
        columns=["PC1", "PC2"],
        index=sample_df.index
    )

    plot_df["cluster"] = sample_df["cluster"].values

    explained_variance = (
        pca.explained_variance_ratio_.sum() * 100
    )

    print(
        "Інформація, збережена двома компонентами PCA: "
        f"{explained_variance:.2f}%"
    )

    print("Створюємо графік...")

    plt.figure(figsize=(11, 7))

    for cluster_id in sorted(plot_df["cluster"].unique()):
        cluster_data = plot_df[
            plot_df["cluster"] == cluster_id
        ]

        plt.scatter(
            cluster_data["PC1"],
            cluster_data["PC2"],
            label=f"Cluster {cluster_id}",
            alpha=0.55,
            s=15
        )

    plt.title("Customer Segmentation: PCA Visualization")
    plt.xlabel("Principal Component 1")
    plt.ylabel("Principal Component 2")

    plt.legend(title="User clusters")
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(OUTPUT_PATH, dpi=160)
    plt.close()

    print("\nPCA-візуалізацію створено!")
    print(f"Графік збережено: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
