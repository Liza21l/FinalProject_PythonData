
from pathlib import Path
import sqlite3
import pandas as pd


# 1. Шляхи до файлів
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "2019-Oct-cleaned.csv"
TEMP_DB_PATH = PROJECT_ROOT / "data" / "feature_temp.sqlite3"
OUTPUT_PATH = PROJECT_ROOT / "data" / "user_features.csv"

CHUNK_SIZE = 100_000


def main():
    if not DATA_PATH.exists():
        print(f"Файл не знайдено: {DATA_PATH}")
        return

    # Видаляємо попередню тимчасову базу,
    # щоб не додавати старі результати повторно.
    if TEMP_DB_PATH.exists():
        TEMP_DB_PATH.unlink()

    conn = sqlite3.connect(TEMP_DB_PATH)

    # Таблиця з кількістю подій кожного користувача
    conn.execute("""
        CREATE TABLE event_counts (
            user_id INTEGER,
            event_type TEXT,
            event_count INTEGER,
            PRIMARY KEY (user_id, event_type)
        )
    """)

    # Таблиця для початку й кінця кожної сесії
    conn.execute("""
        CREATE TABLE sessions (
            user_session TEXT PRIMARY KEY,
            user_id INTEGER,
            first_event TEXT,
            last_event TEXT
        )
    """)

    print("Починаємо створювати ознаки користувачів...")

    try:
        chunks = pd.read_csv(
            DATA_PATH,
            chunksize=CHUNK_SIZE
        )

        for chunk_number, df in enumerate(chunks, start=1):
            # Перетворюємо час на datetime
            df["event_time"] = pd.to_datetime(
                df["event_time"],
                errors="coerce",
                utc=True
            )

            df = df.dropna(
                subset=["event_time", "user_id", "user_session"]
            )

            # -----------------------------------
            # 1. Підрахунок подій кожного користувача
            # -----------------------------------
            counts = (
                df.groupby(["user_id", "event_type"])
                .size()
                .reset_index(name="event_count")
            )

            conn.executemany("""
                INSERT INTO event_counts
                    (user_id, event_type, event_count)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, event_type)
                DO UPDATE SET
                    event_count = event_count + excluded.event_count
            """, counts.itertuples(index=False, name=None))

            # -----------------------------------
            # 2. Знаходимо початок і кінець сесій
            # -----------------------------------
            session_data = df.groupby("user_session").agg(
                user_id=("user_id", "first"),
                first_event=("event_time", "min"),
                last_event=("event_time", "max")
            ).reset_index()

            # Записуємо дати у форматі, який розуміє SQLite
            session_data["first_event"] = (
                session_data["first_event"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            session_data["last_event"] = (
                session_data["last_event"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            conn.executemany("""
                INSERT INTO sessions
                    (user_session, user_id, first_event, last_event)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_session)
                DO UPDATE SET
                    first_event = MIN(
                        sessions.first_event,
                        excluded.first_event
                    ),
                    last_event = MAX(
                        sessions.last_event,
                        excluded.last_event
                    )
            """, session_data.itertuples(index=False, name=None))

            conn.commit()

            print(f"Оброблено частину {chunk_number}")

        # -----------------------------------
        # 3. Формуємо одну таблицю на користувача
        # -----------------------------------
        query = """
            WITH event_features AS (
                SELECT
                    user_id,

                    SUM(CASE
                        WHEN event_type = 'view'
                        THEN event_count ELSE 0
                    END) AS views,

                    SUM(CASE
                        WHEN event_type = 'cart'
                        THEN event_count ELSE 0
                    END) AS carts,

                    SUM(CASE
                        WHEN event_type = 'purchase'
                        THEN event_count ELSE 0
                    END) AS purchases,

                    SUM(CASE
                        WHEN event_type = 'remove_from_cart'
                        THEN event_count ELSE 0
                    END) AS remove_from_cart,

                    SUM(event_count) AS total_events

                FROM event_counts
                GROUP BY user_id
            ),

            session_features AS (
                SELECT
                    user_id,
                    COUNT(*) AS session_count,

                    AVG(
                        MAX(
                            0,
                            (julianday(last_event)
                            - julianday(first_event)) * 86400
                        )
                    ) AS avg_session_duration_seconds

                FROM sessions
                GROUP BY user_id
            )

            SELECT
                e.user_id,
                e.views,
                e.carts,
                e.purchases,
                e.remove_from_cart,
                e.total_events,

                COALESCE(s.session_count, 0) AS session_count,

                ROUND(
                    COALESCE(
                        s.avg_session_duration_seconds, 0
                    ),
                    2
                ) AS avg_session_duration_seconds

            FROM event_features AS e

            LEFT JOIN session_features AS s
                ON e.user_id = s.user_id

            ORDER BY e.user_id
        """

        features = pd.read_sql_query(query, conn)

        # Зберігаємо готову таблицю
        features.to_csv(OUTPUT_PATH, index=False)

        print("\nFeature Engineering завершено!")
        print(f"Кількість користувачів: {len(features)}")
        print(f"Файл з ознаками: {OUTPUT_PATH}")
        print("\nПерші 5 рядків:")
        print(features.head().to_string(index=False))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
