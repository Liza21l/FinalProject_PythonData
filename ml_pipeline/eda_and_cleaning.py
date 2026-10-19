from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "2019-Oct.csv"

REPORT_PATH = PROJECT_ROOT / "data" / "eda_report.txt"

def main():
    if not DATA_PATH.exists():
        print(f"Data file not found at {DATA_PATH}. Please ensure the data file is present.")
        return
    print(f"Завантажуємо частину датасету...")

    df = pd.read_csv(DATA_PATH, nrows=1000)

    # Зберігаємо результати у текстовий звіт
    with open(REPORT_PATH, "w", encoding="utf-8") as report:
        def show(message=""):
            print(message)
            report.write(str(message) + "\n")


        show("\n=== 1. РОЗМІР ДАТАСЕТУ ===")
        show(f"Рядків: {df.shape[0]}")
        show(f"Стовпців: {df.shape[1]}")

        show("\n=== 2. Назва колонок ===")
        for col in df.columns:
            show(col)

        show("\n=== 3. Типи даних ===")
        show(df.dtypes.to_string())

        show("\n=== 4. Перші 5 рядків датасету ===")
        show(df.head().to_string(index=False))

        show("\n=== 5. Пропущені значення ===")
        missing = df.isna().sum()
        show(missing.to_string())

        show("\n=== 6. Відсоток пропусків ===")
        missing_percent = (df.isna().mean() * 100).round(2)
        show(missing_percent.to_string())

        show("\n=== 7. Дублікати ===")
        duplicates = df.duplicated().sum()
        show(f"Кількість дублікатів: {duplicates}")

        show("\n=== 8. Типи подій ===")
        event_types = df['event_type'].value_counts()
        show(event_types.to_string())

        show("\n=== 9. Статистика цін ===")
        price_stats = df['price'].describe()
        show(price_stats.to_string())

        # Перетворюємо час на тип datetime
        df['event_time'] = pd.to_datetime(df['event_time'], errors='coerce', utc=True)

        show("\n=== 10. ДІАПАЗОН ДАТ У ВИБІРЦІ ===")
        show(f"Перша дата: {df['event_time'].min()}")
        show(f"Остання дата: {df['event_time'].max()}")

        show("\n===  11. Використання пам'яті ===")
        memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
        show(f"Використання пам'яті: {memory_mb:.2f} MB")

    print(f"Звіт з EDA збережено у {REPORT_PATH}")

if __name__ == "__main__":
    main()