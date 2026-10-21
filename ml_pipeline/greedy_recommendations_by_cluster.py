
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

EVENTS_FILE = DATA_DIR / "2019-Oct-cleaned.csv"
CLUSTERS_FILE = DATA_DIR / "user_clusters.csv"
PRODUCTS_FILE = DATA_DIR / "product_scores.csv"

TEMP_DB = DATA_DIR / "cluster_product_stats.sqlite3"
OUTPUT_FILE = DATA_DIR / "cluster_product_scores.csv"

CHUNK_SIZE = 100_000
TOP_N = 10


def build_cluster_recommendations():
    """Рахуємо топ товарів окремо для кожного кластера."""

    for file_path in [EVENTS_FILE, CLUSTERS_FILE, PRODUCTS_FILE]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Не знайдено файл: {file_path}"
            )

    # 1. Завантажуємо відповідність user_id -> cluster
    print("Завантажуємо кластери користувачів...")

    clusters = pd.read_csv(
        CLUSTERS_FILE,
        usecols=["user_id", "cluster"]
    )

    clusters["user_id"] = pd.to_numeric(
        clusters["user_id"], errors="coerce"
    )
    clusters = clusters.dropna(subset=["user_id"])
    clusters["user_id"] = clusters["user_id"].astype("int64")

    user_to_cluster = clusters.drop_duplicates(
        "user_id"
    ).set_index("user_id")["cluster"]

    print(f"Завантажено користувачів: {len(user_to_cluster):,}")

    # 2. Створюємо окрему тимчасову базу даних.
    # Старий product_scores.csv не змінюємо.
    if TEMP_DB.exists():
        TEMP_DB.unlink()

    connection = sqlite3.connect(TEMP_DB)

    connection.execute("""
        CREATE TABLE cluster_product_stats (
            cluster INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            views INTEGER NOT NULL DEFAULT 0,
            purchases INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (cluster, product_id)
        )
    """)

    # 3. Обробляємо великий CSV частинами
    print("\nОбробляємо події...")

    total_rows = 0
    matched_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            EVENTS_FILE,
            usecols=["user_id", "product_id", "event_type"],
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):
        total_rows += len(chunk)

        # Для цієї метрики потрібні перегляди та покупки
        chunk = chunk[
            chunk["event_type"].isin(["view", "purchase"])
        ].copy()

        chunk["user_id"] = pd.to_numeric(
            chunk["user_id"], errors="coerce"
        )
        chunk["product_id"] = pd.to_numeric(
            chunk["product_id"], errors="coerce"
        )

        chunk = chunk.dropna(
            subset=["user_id", "product_id"]
        )

        chunk["user_id"] = chunk["user_id"].astype("int64")
        chunk["product_id"] = chunk["product_id"].astype("int64")

        # Призначаємо кожній події кластер її користувача
        chunk["cluster"] = chunk["user_id"].map(user_to_cluster)

        chunk = chunk.dropna(subset=["cluster"])

        if chunk.empty:
            continue

        matched_rows += len(chunk)

        chunk["is_view"] = (
            chunk["event_type"] == "view"
        ).astype("int64")

        chunk["is_purchase"] = (
            chunk["event_type"] == "purchase"
        ).astype("int64")

        # Агрегуємо події для кожної пари кластер + товар
        grouped = (
            chunk.groupby(
                ["cluster", "product_id"],
                as_index=False
            )
            .agg(
                views=("is_view", "sum"),
                purchases=("is_purchase", "sum")
            )
        )

        records = [
            (
                int(row.cluster),
                int(row.product_id),
                int(row.views),
                int(row.purchases)
            )
            for row in grouped.itertuples(index=False)
        ]

        # Додаємо статистику поточного фрагмента до бази
        connection.executemany("""
            INSERT INTO cluster_product_stats
                (cluster, product_id, views, purchases)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cluster, product_id)
            DO UPDATE SET
                views = views + excluded.views,
                purchases = purchases + excluded.purchases
        """, records)

        connection.commit()

        print(
            f"Оброблено частин: {chunk_number} | "
            f"рядків у файлі: {total_rows:,}"
        )

    print(f"\nПодій, що відповідають відомим кластерам: {matched_rows:,}")

    # 4. Завантажуємо агреговану статистику
    stats = pd.read_sql_query(
        """
        SELECT cluster, product_id, views, purchases
        FROM cluster_product_stats
        WHERE views > 0
        """,
        connection
    )

    connection.close()

    if stats.empty:
        raise ValueError(
            "Не знайдено товарів із переглядами у відомих кластерах."
        )

    # 5. Рахуємо purchase-to-view ratio
    stats["purchase_to_view_ratio"] = (
        stats["purchases"] / stats["views"]
    )

    # 6. Додаємо назви категорій, бренди та ціни
    print("\nДодаємо інформацію про товари...")

    products = pd.read_csv(
        PRODUCTS_FILE,
        usecols=[
            "product_id",
            "category_code",
            "brand",
            "average_price"
        ]
    )

    products["product_id"] = pd.to_numeric(
        products["product_id"], errors="coerce"
    )
    products = products.dropna(subset=["product_id"])
    products["product_id"] = products["product_id"].astype("int64")

    stats = stats.merge(
        products.drop_duplicates("product_id"),
        on="product_id",
        how="left"
    )

    # 7. Сортуємо товари всередині кожного кластера
    # Спочатку конверсія, потім кількість переглядів
    stats = stats.sort_values(
        by=[
            "cluster",
            "purchase_to_view_ratio",
            "views",
            "purchases"
        ],
        ascending=[True, False, False, False]
    )

    # Беремо топ-10 окремо для кожного кластера
    recommendations = (
        stats.groupby("cluster", group_keys=False)
        .head(TOP_N)
        .copy()
    )

    # Зберігаємо результат у новий файл
    recommendations.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nРекомендації успішно сформовано!")
    print(f"Файл: {OUTPUT_FILE}")
    print(f"Кількість рекомендацій: {len(recommendations)}")
    print("\nКількість товарів у кожному кластері:")
    print(recommendations.groupby("cluster").size())

    print("\nТоп товарів:")
    print(
        recommendations[
            [
                "cluster",
                "product_id",
                "category_code",
                "brand",
                "views",
                "purchases",
                "purchase_to_view_ratio"
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    build_cluster_recommendations()
