from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PRODUCTS_FILE = DATA_DIR / "cluster_product_scores.csv"
CHECKS_FILE = DATA_DIR / "user_typical_checks.csv"


def get_recommendations(
    limit=10,
    max_per_category=2,
    cluster=None,
    user_id=None,
    max_price=None,
    use_typical_check=False,
):
    """Повертає рекомендації з урахуванням кластера та бюджету."""

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
        "purchase_to_view_ratio",
    }

    missing_columns = required_columns - set(products.columns)

    if missing_columns:
        raise ValueError(
            f"У файлі бракує колонок: {sorted(missing_columns)}"
        )

    typical_check = None

    # Знаходимо типовий чек вибраного користувача.
    if use_typical_check:
        if user_id is None:
            raise ValueError(
                "Для використання типового чека передай user_id."
            )

        if not CHECKS_FILE.exists():
            raise FileNotFoundError(
                f"Не знайдено файл типових чеків: {CHECKS_FILE}"
            )

        checks = pd.read_csv(
            CHECKS_FILE,
            usecols=["user_id", "typical_check"],
        )

        user_check = checks.loc[
            checks["user_id"] == int(user_id),
            "typical_check",
        ]

        if user_check.empty:
            raise ValueError(
                f"Для користувача {user_id} типовий чек не знайдено."
            )

        typical_check = float(user_check.iloc[0])

        # Якщо max_price не передали, типовий чек стає лімітом.
        if max_price is None:
            max_price = typical_check

    # Вибираємо товари потрібного кластера.
    if cluster is not None:
        products = products[
            products["cluster"] == cluster
        ].copy()

        if products.empty:
            raise ValueError(
                f"Для кластера {cluster} немає рекомендацій."
            )
    else:
        products = products.sort_values(
            ["purchase_to_view_ratio", "views", "purchases"],
            ascending=[False, False, False],
        )

        products = products.drop_duplicates(
            subset=["product_id"]
        )

    # Залишаємо товари з достатньою кількістю переглядів.
    products = products[
        products["views"] >= 10
    ].copy()

    # Застосовуємо ціновий фільтр.
    if max_price is not None:
        if max_price < 0:
            raise ValueError("max_price не може бути від'ємним.")

        products = products[
            products["average_price"].notna()
            & (products["average_price"] <= max_price)
        ].copy()

    products = products.sort_values(
        ["purchase_to_view_ratio", "views", "purchases"],
        ascending=[False, False, False],
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
            "purchases": int(product["purchases"]),
        })

        category_counts[category] += 1

        if len(recommendations) >= limit:
            break

    return recommendations
