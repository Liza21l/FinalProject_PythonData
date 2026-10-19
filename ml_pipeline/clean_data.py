
from pathlib import Path
import pandas as pd


# 1. Знаходимо папку проєкту
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 2. Шляхи до файлів
DATA_PATH = PROJECT_ROOT / "data" / "2019-Oct.csv"
CLEANED_PATH = PROJECT_ROOT / "data" / "2019-Oct-cleaned.csv"
REPORT_PATH = PROJECT_ROOT / "data" / "cleaning_report.txt"



def main():
    # Перевіряємо наявність оригінального файлу
    if not DATA_PATH.exists():
        print(f"Файл не знайдено: {DATA_PATH}")
        return

    total_rows = 0
    removed_duplicates = 0
    removed_bad_dates = 0
    removed_bad_prices = 0
    filled_category = 0
    filled_brand = 0

    print("Починаємо очищення датасету...")

    # Читаємо CSV частинами
    chunks = pd.read_csv(
        DATA_PATH,
        chunksize= 100000
    )

    # Обробляємо кожну частину
    for chunk_number, df in enumerate(chunks):

        original_rows = len(df)
        total_rows += original_rows

        # 1. Видаляємо дублікати всередині поточної частини
        before = len(df)
        df = df.drop_duplicates()
        removed_duplicates += before - len(df)

        # 2. Перетворюємо дату на datetime
        df["event_time"] = pd.to_datetime(
            df["event_time"],
            errors="coerce",
            utc=True
        )

        # Видаляємо рядки з некоректною датою
        before = len(df)
        df = df.dropna(subset=["event_time"])
        removed_bad_dates += before - len(df)

        # 3. Перевіряємо ціну
        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        # Видаляємо порожні, некоректні та від'ємні ціни
        before = len(df)
        df = df[
            df["price"].notna()
            & (df["price"] >= 0)
        ]
        removed_bad_prices += before - len(df)

        # 4. Заповнюємо пропуски в категорії
        filled_category += df["category_code"].isna().sum()
        df["category_code"] = df["category_code"].fillna("Unknown")

        # 5. Заповнюємо пропуски в бренді
        filled_brand += df["brand"].isna().sum()
        df["brand"] = df["brand"].fillna("Unknown")

        # 6. Записуємо очищену частину в новий CSV
        # Для першої частини створюємо файл,
        # наступні частини додаємо в кінець.
        df.to_csv(
            CLEANED_PATH,
            index=False,
            mode="w" if chunk_number == 0 else "a",
            header=(chunk_number == 0)
        )

        print(
            f"Оброблено частину {chunk_number + 1}: "
            f"{original_rows} рядків"
        )

    # 7. Створюємо звіт
    with open(REPORT_PATH, "w", encoding="utf-8") as report:
        report.write("=== ЗВІТ ПРО ОЧИЩЕННЯ ===\n")
        report.write(f"Оброблено рядків: {total_rows}\n")
        report.write(
            f"Видалено дублікатів у межах частин: "
            f"{removed_duplicates}\n"
        )
        report.write(f"Видалено рядків з некоректною датою: {removed_bad_dates}\n")
        report.write(f"Видалено рядків з некоректною ціною: {removed_bad_prices}\n")
        report.write(f"Заповнено пропусків category_code: {filled_category}\n")
        report.write(f"Заповнено пропусків brand: {filled_brand}\n")

    print("\nОчищення завершено!")
    print(f"Новий CSV: {CLEANED_PATH}")
    print(f"Звіт: {REPORT_PATH}")


if __name__ == "__main__":
    main()
