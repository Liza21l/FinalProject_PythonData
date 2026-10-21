from pathlib import Path

import pandas as pd

from ml_pipeline.greedy_recommendations import greedy_recommendations


BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = BASE_DIR / "data" / "product_scores.csv"


def get_recommendations(limit=10, max_per_category=2):
    if not PRODUCTS_FILE.exists():
        raise FileNotFoundError(
            f"Не знайдено каталог товарів: {PRODUCTS_FILE}"
        )

    products = pd.read_csv(PRODUCTS_FILE)

    recommendations = greedy_recommendations(
        products,
        limit=limit,
        max_per_category=max_per_category
    )

    # Замінюємо NaN на None, щоб JSON формувався коректно.
    recommendations = recommendations.astype(object).where(
        pd.notna(recommendations),
        None
    )

    return recommendations[
        [
            "product_id",
            "category_code",
            "brand",
            "average_price",
            "score"
        ]
    ].to_dict(orient="records")