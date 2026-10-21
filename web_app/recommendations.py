
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = BASE_DIR / "data" / "cluster_product_scores.csv"


def get_recommendations(
    limit=10,
    max_per_category=2,
    cluster=None
):
    """Повертає рекомендації для конкретного кластера або загальний топ."""

    if not PRODUCTS_FILE.exists():
        raise FileNotFoundError(
            f"Не знайдено каталог рекомендацій: {PRODUCTS_FILE}"
        )

    products = pd.read_csv(PRODUCTS_FILE)

    required_columns = {
        "cluster",
        "product_id",
        "category_code",
        "brand",
        "average_price",
        "views",
        "purchases",
        "purchase_to_view_ratio"
    }

    missing_columns = required_columns - set(products.columns)

    if missing_columns:
        raise ValueError(
            f"У файлі бракує колонок: {sorted(missing_columns)}"
        )

    # Якщо кластер передано, залишаємо тільки його товари.
    if cluster is not None:
        products = products[
            products["cluster"] == cluster
        ].copy()

        if products.empty:
            raise ValueError(
                f"Для кластера {cluster} немає рекомендацій."
            )
    else:
        # Без вибраного кластера залишаємо найкращий запис
        # для кожного товару, щоб не дублювати його.
        products = products.sort_values(
            ["purchase_to_view_ratio", "views", "purchases"],
            ascending=[False, False, False]
        )

        products = products.drop_duplicates(
            subset=["product_id"]
        )

    # Прибираємо товари з недостатньою кількістю переглядів.
    products = products[products["views"] >= 10].copy()

    products = products.sort_values(
        ["purchase_to_view_ratio", "views", "purchases"],
        ascending=[False, False, False]
    )

    recommendations = []
    category_counts = {}

    for _, product in products.iterrows():
        category = product["category_code"]

        if pd.isna(category):
            category = "Unknown"

        category_counts.setdefault(category, 0)

        if category_counts[category] >= max_per_category:
            continue

        recommendations.append({
            "cluster": int(product["cluster"]),
            "product_id": int(product["product_id"]),
            "category_code": (
                None if pd.isna(product["category_code"])
                else product["category_code"]
            ),
            "brand": (
                None if pd.isna(product["brand"])
                else product["brand"]
            ),
            "average_price": (
                None if pd.isna(product["average_price"])
                else float(product["average_price"])
            ),
            "score": float(product["purchase_to_view_ratio"]),
            "views": int(product["views"]),
            "purchases": int(product["purchases"])
        })

        category_counts[category] += 1

        if len(recommendations) >= limit:
            break

    return recommendations
