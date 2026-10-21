
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

files = [
    DATA_DIR / "user_clusters.csv",
    DATA_DIR / "user_features.csv",
    DATA_DIR / "product_scores.csv",
]

for file_path in files:
    print(f"\n{'=' * 50}")
    print(f"Файл: {file_path.name}")

    if not file_path.exists():
        print("Файл не знайдено!")
        continue

    df = pd.read_csv(file_path, nrows=5)

    print("Колонки:", df.columns.tolist())
    print(df.head(3).to_string(index=False))
