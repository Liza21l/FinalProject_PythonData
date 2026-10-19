
import sqlite3
from pathlib import Path

import pandas as pd


# 1. Визначаємо шляхи до файлів
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "2019-Oct-cleaned.csv"
DB_PATH = PROJECT_ROOT / "data" / "duplicate_check.sqlite3"
REPORT_PATH = PROJECT_ROOT / "data" / "duplicate_check_report.txt"

CHUNK_SIZE = 100_000


def main():
    # Перевіряємо, чи існує очищений CSV
    if not DATA_PATH.exists():
        print(f"Помилка: файл не знайдено: {DATA_PATH}")
        return

    # Видаляємо тимчасову базу від попередньої перевірки
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Створюємо SQLite-базу для збереження хешів
    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE seen_hashes (
            row_hash INTEGER PRIMARY KEY
        )
    """)

    total_rows = 0
    duplicate_rows = 0

    print("Починаємо перевірку дублікатів...")
    print("Перевірка великого файлу може тривати довго.")

    try:
        # 2. Читаємо CSV частинами
        for chunk_number, chunk in enumerate(
            pd.read_csv(
                DATA_PATH,
                chunksize=CHUNK_SIZE,
                dtype=str,
                keep_default_na=False
            ),
            start=1
        ):
            # 3. Створюємо хеш кожного рядка
            hashes = pd.util.hash_pandas_object(
                chunk,
                index=False
            ).to_numpy()

            values = []

            for value in hashes:
                number = int(value)

                # Перетворюємо число у формат SQLite INTEGER
                if number >= 2**63:
                    number -= 2**64

                values.append((number,))

            # 4. Додаємо лише хеші, яких ще немає в базі
            changes_before = connection.total_changes

            connection.executemany(
                """
                INSERT OR IGNORE INTO seen_hashes (row_hash)
                VALUES (?)
                """,
                values
            )

            unique_added = (
                connection.total_changes - changes_before
            )

            # Різниця показує кількість повторних хешів
            duplicates_in_chunk = len(chunk) - unique_added

            total_rows += len(chunk)
            duplicate_rows += duplicates_in_chunk

            connection.commit()

            print(
                f"Частина {chunk_number}: "
                f"оброблено рядків: {total_rows:,}; "
                f"дублікатів знайдено: {duplicate_rows:,}"
            )

        # 5. Формуємо підсумковий звіт
        unique_rows = total_rows - duplicate_rows

        report = (
            "=== ПЕРЕВІРКА ДУБЛІКАТІВ ===\n"
            f"Перевірено рядків: {total_rows}\n"
            f"Унікальних рядків за хешем: {unique_rows}\n"
            f"Знайдено дублікатів: {duplicate_rows}\n"
        )

        REPORT_PATH.write_text(report, encoding="utf-8")

        print("\n" + report)
        print(f"Звіт збережено у файлі: {REPORT_PATH}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
