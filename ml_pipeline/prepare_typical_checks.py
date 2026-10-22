
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "2019-Oct-cleaned.csv"
DB_FILE = DATA_DIR / "typical_checks.sqlite3"
OUTPUT_FILE = DATA_DIR / "user_typical_checks.csv"

CHUNK_SIZE = 500_000


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Не знайдено файл: {INPUT_FILE}")

    if DB_FILE.exists():
        print(
            "Знайдено попередню базу типових чеків. "
            "Видали її вручну, якщо хочеш почати обробку з нуля."
        )
        raise FileExistsError(DB_FILE)

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE sessions (
                user_id INTEGER NOT NULL,
                user_session TEXT NOT NULL,
                session_amount REAL NOT NULL,
                PRIMARY KEY (user_id, user_session)
            )
        """)

        total_rows = 0

        for number, chunk in enumerate(
            pd.read_csv(
                INPUT_FILE,
                usecols=[
                    "event_type",
                    "price",
                    "user_id",
                    "user_session",
                ],
                chunksize=CHUNK_SIZE,
            ),
            start=1,
        ):
            total_rows += len(chunk)

            purchases = chunk.loc[
                chunk["event_type"] == "purchase",
                ["user_id", "user_session", "price"],
            ].copy()

            purchases["price"] = pd.to_numeric(
                purchases["price"], errors="coerce"
            )

            purchases = purchases.dropna(
                subset=["user_id", "user_session", "price"]
            )

            # Сума покупок за кожною сесією в поточній частині.
            session_totals = (
                purchases.groupby(
                    ["user_id", "user_session"],
                    as_index=False,
                )["price"]
                .sum()
            )

            # UPSERT об'єднує частини, якщо одна сесія
            # трапилася в декількох частинах CSV.
            conn.executemany(
                """
                INSERT INTO sessions (
                    user_id, user_session, session_amount
                )
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, user_session)
                DO UPDATE SET
                    session_amount =
                        session_amount + excluded.session_amount
                """,
                session_totals.itertuples(index=False, name=None),
            )

            conn.commit()
            print(f"Оброблено рядків: {total_rows:,}")

        print("Обчислюємо типовий чек кожного користувача...")

        checks = pd.read_sql_query(
            """
            SELECT
                user_id,
                AVG(session_amount) AS typical_check,
                COUNT(*) AS purchase_sessions
            FROM sessions
            GROUP BY user_id
            """,
            conn,
        )

    checks["typical_check"] = checks["typical_check"].round(2)
    checks.to_csv(OUTPUT_FILE, index=False)

    print("\n=== РЕЗУЛЬТАТ ===")
    print(f"Користувачів: {len(checks):,}")
    print(f"Файл: {OUTPUT_FILE}")
    print(checks.head().to_string(index=False))


if __name__ == "__main__":
    main()
