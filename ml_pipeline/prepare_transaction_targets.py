
from pathlib import Path

import pandas as pd


# Шляхи до файлів
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "2019-Oct-cleaned.csv"
OUTPUT_FILE = DATA_DIR / "user_purchase_totals.csv"

CHUNK_SIZE = 1_000_000


def main():
    print("Починаємо підготовку сум покупок...")

    # Зберігатимемо підсумки кожної частини файлу
    partial_totals = []

    total_rows = 0
    purchase_rows = 0

    # Читаємо великий CSV частинами, щоб не завантажувати
    # усі 5,9 ГБ у пам'ять одночасно
    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_FILE,
            usecols=["event_type", "price", "user_id"],
            chunksize=CHUNK_SIZE,
        ),
        start=1,
    ):
        total_rows += len(chunk)

        # Залишаємо лише події покупок
        purchases = chunk.loc[
            chunk["event_type"] == "purchase",
            ["user_id", "price"],
        ].copy()

        # Перетворюємо ціну на число
        purchases["price"] = pd.to_numeric(
            purchases["price"],
            errors="coerce",
        )

        # Прибираємо рядки без користувача або коректної ціни
        purchases = purchases.dropna(
            subset=["user_id", "price"]
        )

        purchase_rows += len(purchases)

        # Рахуємо суму покупок кожного користувача в цій частині
        chunk_totals = (
            purchases.groupby("user_id", as_index=False)["price"]
            .sum()
            .rename(columns={"price": "total_purchase_amount"})
        )

        partial_totals.append(chunk_totals)

        print(
            f"Частина {chunk_number}: "
            f"оброблено рядків {total_rows:,}"
        )

    if not partial_totals:
        raise ValueError("Не знайдено даних для обробки.")

    # Об'єднуємо підсумки різних частин.
    # Один користувач міг зустрітися в кількох частинах.
    totals = pd.concat(partial_totals, ignore_index=True)

    totals = (
        totals.groupby("user_id", as_index=False)[
            "total_purchase_amount"
        ]
        .sum()
    )

    totals["total_purchase_amount"] = (
        totals["total_purchase_amount"].round(2)
    )

    totals.to_csv(OUTPUT_FILE, index=False)

    print("\n=== РЕЗУЛЬТАТ ===")
    print(f"Оброблено всього рядків: {total_rows:,}")
    print(f"Рядків покупок із коректною ціною: {purchase_rows:,}")
    print(f"Користувачів із покупками: {len(totals):,}")
    print(f"Сума всіх покупок: {totals['total_purchase_amount'].sum():,.2f}")
    print(f"Файл збережено: {OUTPUT_FILE}")

    print("\nПерші рядки:")
    print(totals.head())


if __name__ == "__main__":
    main()
