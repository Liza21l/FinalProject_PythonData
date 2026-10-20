import sqlite3
from pathlib import Path

import pandas as pd


# Шляхи до файлів
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CLEANED_FILE = DATA_DIR / "2019-Oct-cleaned.csv"
TEMP_DB = DATA_DIR / "product_stats.sqlite3"
OUTPUT_FILE = DATA_DIR / "product_scores.csv"

CHUNK_SIZE = 100_000


def build_product_catalog():
    """
    Обробляє очищений CSV частинами,
    підраховує статистику товарів
    і зберігає її у SQLite.
    """

    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Не знайдено файл: {CLEANED_FILE}"
        )

    if TEMP_DB.exists():
        TEMP_DB.unlink()

    connection = sqlite3.connect(TEMP_DB)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE product_stats (
                product_id INTEGER PRIMARY KEY,
                views INTEGER NOT NULL DEFAULT 0,
                carts INTEGER NOT NULL DEFAULT 0,
                purchases INTEGER NOT NULL DEFAULT 0,
                removed_from_cart INTEGER NOT NULL DEFAULT 0,
                price_sum REAL NOT NULL DEFAULT 0,
                price_count INTEGER NOT NULL DEFAULT 0,
                category_code TEXT NOT NULL DEFAULT 'Unknown',
                brand TEXT NOT NULL DEFAULT 'Unknown'
            )
        """)

        connection.commit()

        processed_rows = 0

        for chunk_number, chunk in enumerate(
            pd.read_csv(
                CLEANED_FILE,
                usecols=[
                    "event_type",
                    "product_id",
                    "category_code",
                    "brand",
                    "price"
                ],
                chunksize=CHUNK_SIZE
            ),
            start=1
        ):

            processed_rows += len(chunk)

            # Кількість кожного типу подій для кожного товару
            chunk["views"] = (
                chunk["event_type"] == "view"
            ).astype(int)

            chunk["carts"] = (
                chunk["event_type"] == "cart"
            ).astype(int)

            chunk["purchases"] = (
                chunk["event_type"] == "purchase"
            ).astype(int)

            chunk["removed_from_cart"] = (
                chunk["event_type"] == "remove_from_cart"
            ).astype(int)

            # Підготовка даних для групування
            chunk["price"] = pd.to_numeric(
                chunk["price"],
                errors="coerce"
            )

            # Підрахунок статистики для кожного товару
            grouped = chunk.groupby("product_id").agg(
                views=("views", "sum"),
                carts=("carts", "sum"),
                purchases=("purchases", "sum"),
                removed_from_cart=("removed_from_cart", "sum"),
                price_sum=("price", "sum"),
                price_count=("price", "count"),
                category_code=("category_code", "first"),
                brand=("brand", "first")
            )

            records = []

            for product_id, row in grouped.iterrows():
                records.append((
                    int(product_id),
                    int(row["views"]),
                    int(row["carts"]),
                    int(row["purchases"]),
                    int(row["removed_from_cart"]),
                    float(row["price_sum"]),
                    int(row["price_count"]),
                    str(row["category_code"]),
                    str(row["brand"])
                ))

            # Додаємо статистику до SQLite.
            # Якщо товар уже є, додаємо нові лічильники.
            cursor.executemany("""
                INSERT INTO product_stats (
                    product_id,
                    views,
                    carts,
                    purchases,
                    removed_from_cart,
                    price_sum,
                    price_count,
                    category_code,
                    brand
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(product_id) DO UPDATE SET
                    views = views + excluded.views,
                    carts = carts + excluded.carts,
                    purchases = purchases + excluded.purchases,
                    removed_from_cart =
                        removed_from_cart + excluded.removed_from_cart,
                    price_sum = price_sum + excluded.price_sum,
                    price_count = price_count + excluded.price_count,

                    category_code = CASE
                        WHEN product_stats.category_code = 'Unknown'
                        THEN excluded.category_code
                        ELSE product_stats.category_code
                    END,

                    brand = CASE
                        WHEN product_stats.brand = 'Unknown'
                        THEN excluded.brand
                        ELSE product_stats.brand
                    END
            """, records)

            connection.commit()

            print(
                f"Оброблено частину {chunk_number}. "
                f"Рядків: {processed_rows:,}"
            )

        # Переносимо підсумкову статистику у DataFrame
        products = pd.read_sql_query(
            "SELECT * FROM product_stats",
            connection
        )

    finally:
        connection.close()

    # Розрахунок середньої ціни
    products["average_price"] = (
        products["price_sum"]
        / products["price_count"].replace(0, pd.NA)
    )

    products["average_price"] = (
        products["average_price"].fillna(0)
    )

    # Розрахунок оцінки популярності
    products["score"] = (
        products["views"] * 1
        + products["carts"] * 3
        + products["purchases"] * 5
        - products["removed_from_cart"] * 2
    )

    # Спочатку рекомендуємо товари з найвищою оцінкою
    products = products.sort_values(
        by="score",
        ascending=False
    )

    # Зберігаємо каталог товарів з оцінками
    products.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nКаталог товарів створено!")
    print(f"Кількість товарів: {len(products):,}")
    print(f"Файл результатів: {OUTPUT_FILE}")


def greedy_recommendations(
    products,
    limit=10,
    max_per_category=2
):
    """
    Жадібно вибирає популярні товари,
    намагаючись урізноманітнити категорії.
    """

    if limit <= 0:
        return products.head(0).copy()

    selected = []
    category_counts = {}

    # Проходимо товари від найвищої оцінки до найнижчої
    for _, product in products.iterrows():

        category = product["category_code"]

        current_count = category_counts.get(category, 0)

        if current_count >= max_per_category:
            continue

        selected.append(product)

        category_counts[category] = current_count + 1

        if len(selected) == limit:
            break

    # Якщо категорій недостатньо, доповнюємо список
    # найкращими ще не вибраними товарами.
    if len(selected) < limit:

        selected_ids = {
            product["product_id"]
            for product in selected
        }

        for _, product in products.iterrows():

            if product["product_id"] in selected_ids:
                continue

            selected.append(product)

            if len(selected) == limit:
                break

    if not selected:
        return products.head(0).copy()

    return pd.DataFrame(selected).reset_index(drop=True)


def main():
    # Формуємо каталог, якщо його ще немає
    if not OUTPUT_FILE.exists():
        build_product_catalog()

    products = pd.read_csv(OUTPUT_FILE)

    recommendations = greedy_recommendations(
        products,
        limit=10,
        max_per_category=2
    )

    print("\n=== GREEDY RECOMMENDATIONS ===")

    print(
        recommendations[
            [
                "product_id",
                "category_code",
                "brand",
                "average_price",
                "score"
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()