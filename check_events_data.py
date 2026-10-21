
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EVENTS_FILE = DATA_DIR / "2019-Oct-cleaned.csv"
CLUSTERS_FILE = DATA_DIR / "user_clusters.csv"

# 1. Перевіряємо структуру файлу подій
print("=== Структура файлу подій ===")

if not EVENTS_FILE.exists():
    print(f"Файл не знайдено: {EVENTS_FILE}")
    raise SystemExit

events_sample = pd.read_csv(EVENTS_FILE, nrows=5)

print("Колонки:", events_sample.columns.tolist())
print(events_sample.head(3).to_string(index=False))

required_columns = {"user_id", "product_id", "event_type"}
missing = required_columns - set(events_sample.columns)

if missing:
    print("\nНе вистачає колонок:", missing)
    raise SystemExit

# 2. Перевіряємо кількість користувачів у кластерах
print("\n=== Кластери користувачів ===")

clusters = pd.read_csv(CLUSTERS_FILE, usecols=["user_id", "cluster"])

print("Кількість користувачів:", len(clusters))
print("Кількість унікальних user_id:", clusters["user_id"].nunique())
print("\nКількість користувачів у кожному кластері:")
print(clusters["cluster"].value_counts().sort_index())

print("\nПеревірка завершена.")
