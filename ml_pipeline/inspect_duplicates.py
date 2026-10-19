
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "2019-Oct-cleaned.csv"
DB_PATH = PROJECT_ROOT / "data" / "duplicate_inspection.sqlite3"

CHUNK_SIZE = 100_000


def main():
    if not DATA_PATH.exists():
        print(f"Файл не знайдено: {DATA_PATH}")
        return

    # Видаляємо тимчасову базу від попереднього запуску
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE seen_rows (
            row_hash INTEGER PRIMARY KEY,
            row_data TEXT NOT NULL
        )
    """)

    total_duplicates = 0

    try:
        for chunk_number, chunk in enumerate(
            pd.read_csv(
                DATA_PATH,
                chunksize=CHUNK_SIZE,
                dtype=str,
                keep_default_na=False
            ),
            start=1
        ):
            hashes = pd.util.hash_pandas_object(
                chunk,
                index=False
            ).to_numpy()

            for row_position, hash_value in enumerate(hashes):
                row_hash = int(hash_value)

                if row_hash >= 2**63:
                    row_hash -= 2**64

                row = chunk.iloc[row_position]

                # Серіалізуємо повний рядок для точного порівняння
                row_data = row.to_json(force_ascii=False)

                existing = connection.execute(
                    """
                    SELECT row_data
                    FROM seen_rows
                    WHERE row_hash = ?
                    """,
                    (row_hash,)
                ).fetchone()

                if existing is not None:
                    previous_data = existing[0]

                    if previous_data == row_data:
                        total_duplicates += 1

                        print(
                            f"\nЗнайдено точний повторний рядок "
                            f"(частина {chunk_number}):"
                        )
                        print(row.to_string())
                        print("-" * 50)

                    else:
                        print(
                            "\nУвага: однаковий хеш, але дані різні. "
                            "Це можлива колізія хешу."
                        )

                else:
                    connection.execute(
                        """
                        INSERT INTO seen_rows (row_hash, row_data)
                        VALUES (?, ?)
                        """,
                        (row_hash, row_data)
                    )

            connection.commit()

            print(
                f"Перевірено частину {chunk_number}. "
                f"Точних повторів наразі: {total_duplicates}"
            )

        print("\n=== РЕЗУЛЬТАТ ПЕРЕВІРКИ ===")
        print(f"Точних повторних рядків: {total_duplicates}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
