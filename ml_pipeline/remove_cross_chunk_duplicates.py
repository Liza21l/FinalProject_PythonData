from pathlib import Path
import os
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "2019-Oct-cleaned.csv"
TEMP_PATH = PROJECT_ROOT / "data" / "2019-Oct-cleaned-temp.csv"

CHUNK_SIZE = 100_000

TARGET_ROW = {
    "event_time": "2019-10-22 18:26:15+00:00",
    "event_type": "cart",
    "product_id": "1004750",
    "category_id": "2053013555631882655",
    "category_code": "electronics.smartphone",
    "brand": "samsung",
    "price": "195.49",
    "user_id": "523756557",
    "user_session": "7f5c488b-ccc6-4655-97a2-56f137afcb97",
}


def main():
    if not DATA_PATH.exists():
        print(f"Файл не знайдено: {DATA_PATH}")
        return

    if TEMP_PATH.exists():
        TEMP_PATH.unlink()

    total_rows = 0
    matching_rows = 0
    removed_rows = 0
    first_chunk = True

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
            total_rows += len(chunk)

            if first_chunk:
                missing_columns = set(TARGET_ROW) - set(chunk.columns)

                if missing_columns:
                    raise ValueError(
                        f"Не знайдено колонки: {missing_columns}"
                    )

            mask = pd.Series(True, index=chunk.index)

            for column, value in TARGET_ROW.items():
                mask &= chunk[column] == value

            indexes = list(chunk.index[mask])
            matching_rows += len(indexes)

            # Перший збіг зберігаємо.
            # Усі наступні збіги видаляємо.
            rows_to_drop = []

            for index in indexes:
                if matching_rows - len(indexes) > 0 or rows_to_drop:
                    rows_to_drop.append(index)
                else:
                    rows_to_drop.append(index)
                    break

            # Якщо це перший збіг у файлі, зберігаємо його.
            # Якщо попередній збіг був раніше, видаляємо поточний.
            if matching_rows - len(indexes) > 0:
                rows_to_drop = indexes
            else:
                rows_to_drop = indexes[1:]

            if rows_to_drop:
                chunk = chunk.drop(index=rows_to_drop)
                removed_rows += len(rows_to_drop)

            chunk.to_csv(
                TEMP_PATH,
                mode="w" if first_chunk else "a",
                index=False,
                header=first_chunk
            )

            first_chunk = False

            print(
                f"Частина {chunk_number}: "
                f"перевірено {total_rows:,} рядків; "
                f"видалено {removed_rows} дублікатів"
            )

        print("\n=== ПІДСУМОК ===")
        print(f"Перевірено рядків: {total_rows:,}")
        print(f"Знайдено цільових записів: {matching_rows}")
        print(f"Видалено дублікатів: {removed_rows}")

        if matching_rows != 2 or removed_rows != 1:
            print(
                "\nПеревірка не пройдена. "
                "Початковий файл залишено без змін."
            )
            print(f"Тимчасовий файл: {TEMP_PATH}")
            return

        os.replace(TEMP_PATH, DATA_PATH)

        print("\nУспішно! Видалено один дублікат.")
        print(f"Оновлений файл: {DATA_PATH}")

    except Exception as error:
        print(f"\nПомилка: {error}")
        print("Початковий файл не замінено.")


if __name__ == "__main__":
    main()