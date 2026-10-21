
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

files = [
    DATA_DIR / "user_clusters.csv",
    DATA_DIR / "user_features.csv",
    DATA_DIR / "product_scores.csv",
    DATA_DIR / "cluster_product_scores.csv",
]

for file_path in files:
    print(f"\n{'=' * 60}")
    print(f"Файл: {file_path.name}")

    if not file_path.exists():
        print("Файл не знайдено!")
        continue

    df = pd.read_csv(file_path, nrows=5)

    print("Колонки:", df.columns.tolist())
    print(df.head(3).to_string(index=False))

# Окрема повна перевірка рекомендацій за кластерами
recommendations_file = DATA_DIR / "cluster_product_scores.csv"

if recommendations_file.exists():
    recommendations = pd.read_csv(recommendations_file)

    print("\n" + "=" * 60)
    print("КІЛЬКІСТЬ РЕКОМЕНДАЦІЙ ЗА КЛАСТЕРАМИ")

    print(recommendations.groupby("cluster").size())

    print("\nСТАТИСТИКА ПЕРЕГЛЯДІВ")

    print(
        recommendations.groupby("cluster")["views"]
        .agg(["count", "min", "max", "mean"])
    )

    print("\nУСІ РЕКОМЕНДАЦІЇ")

    print(
        recommendations[
            [
                "cluster",
                "product_id",
                "views",
                "purchases",
                "purchase_to_view_ratio"
            ]
        ].to_string(index=False)
    )
