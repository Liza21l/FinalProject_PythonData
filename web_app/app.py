import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from web_app.models import db, Operation
from web_app.algorithms import (
    bubble_sort,
    quick_sort,
    linear_search,
    binary_search
)
from web_app.recommendations import get_recommendations
from web_app.models import db, Operation
from web_app.structures import Queue, Stack
import pandas as pd
from functools import lru_cache

# Шляхи до папок проєкту
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "operations.db"


# Створення Flask-застосунку
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Створюємо чергу та стек для вебзастосунку
customer_queue = Queue()
transaction_stack = Stack()

# Налаштування бази даних
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{DATABASE_PATH.as_posix()}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Підключення SQLAlchemy
db.init_app(app)


# Створення таблиць у базі даних
with app.app_context():
    db.create_all()


# Функція для запису операції в базу даних
def log_operation(operation_type, details):
    operation = Operation(
        operation_type=operation_type,
        details=details
    )

    db.session.add(operation)
    db.session.commit()


# Головна сторінка
@app.route("/")
def index():
    return render_template("index.html")


# Перевірка роботи сервера
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Flask Backend працює!"
    })


# Отримання історії операцій
@app.route("/api/operations", methods=["GET"])
def get_operations():
    operations = (
        db.session.query(Operation)
        .order_by(Operation.created_at.desc())
        .limit(50)
        .all()
    )

    return jsonify([
        operation.to_dict()
        for operation in operations
    ])


# API для сортування списку
@app.route("/api/sort", methods=["POST"])
def sort_numbers():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Очікується JSON-об'єкт."
        }), 400

    numbers = data.get("numbers")
    algorithm = data.get("algorithm")

    if not isinstance(numbers, list):
        return jsonify({
            "error": "Поле numbers має бути списком."
        }), 400

    # Перевіряємо, що список містить числа
    if any(
        isinstance(number, bool)
        or not isinstance(number, (int, float))
        for number in numbers
    ):
        return jsonify({
            "error": "Список повинен містити лише числа."
        }), 400

    algorithms = {
        "bubble": bubble_sort,
        "quick": quick_sort
    }

    if algorithm not in algorithms:
        return jsonify({
            "error": "Вибери bubble або quick."
        }), 400

    sorted_numbers = algorithms[algorithm](numbers)

    log_operation(
        f"sort:{algorithm}",
        json.dumps({
            "input": numbers,
            "output": sorted_numbers
        })
    )

    return jsonify({
        "algorithm": algorithm,
        "original": numbers,
        "sorted": sorted_numbers
    })


# API для пошуку числа
@app.route("/api/search", methods=["POST"])
def search_number():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Очікується JSON-об'єкт."
        }), 400

    numbers = data.get("numbers")
    target = data.get("target")
    algorithm = data.get("algorithm")

    if not isinstance(numbers, list) or not numbers:
        return jsonify({
            "error": "numbers має бути непорожнім списком."
        }), 400

    if any(
        isinstance(number, bool)
        or not isinstance(number, (int, float))
        for number in numbers
    ):
        return jsonify({
            "error": "Список повинен містити лише числа."
        }), 400

    if (
        isinstance(target, bool)
        or not isinstance(target, (int, float))
    ):
        return jsonify({
            "error": "target має бути числом."
        }), 400

    if algorithm == "linear":
        index = linear_search(numbers, target)

    elif algorithm == "binary":
        if numbers != sorted(numbers):
            return jsonify({
                "error": (
                    "Для binary search список має бути "
                    "відсортований за зростанням."
                )
            }), 400

        index = binary_search(numbers, target)

    else:
        return jsonify({
            "error": "Вибери linear або binary."
        }), 400

    log_operation(
        f"search:{algorithm}",
        json.dumps({
            "numbers": numbers,
            "target": target,
            "index": index
        })
    )

    return jsonify({
        "algorithm": algorithm,
        "target": target,
        "index": index,
        "found": index != -1
    })

@app.route("/api/recommendations", methods=["GET"])
def recommendations_route():
    try:
        cluster_param = request.args.get("cluster")
        cluster = None

        if cluster_param is not None:
            try:
                cluster = int(cluster_param)
            except ValueError:
                return jsonify({
                    "error": "Параметр cluster має бути цілим числом."
                }), 400

            if cluster < 0:
                return jsonify({
                    "error": "Номер кластера не може бути від'ємним."
                }), 400

        recommendations = get_recommendations(
            limit=10,
            max_per_category=2,
            cluster=cluster
        )

        return jsonify({
            "count": len(recommendations),
            "cluster": cluster,
            "recommendations": recommendations
        }), 200

    except (FileNotFoundError, OSError, ValueError) as error:
        return jsonify({"error": str(error)}), 500

# Отримання поточного стану черги
@app.route("/api/queue", methods=["GET"])
def get_queue():
    return jsonify({
        "items": list(customer_queue.items),
        "size": customer_queue.size()
    })

# Додавання елемента до черги
@app.route("/api/queue/enqueue", methods=["POST"])
def enqueue_item():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Очікується JSON-об'єкт."
        }), 400

    item = data.get("item")

    if not isinstance(item, str) or not item.strip():
        return jsonify({
            "error": "Поле item має містити непорожній текст."
        }), 400

    item = item.strip()
    customer_queue.enqueue(item)

    log_operation(
        "queue:enqueue",
        json.dumps({"item": item}, ensure_ascii=False)
    )

    return jsonify({
        "message": "Елемент додано до черги.",
        "items": list(customer_queue.items),
        "size": customer_queue.size()
    }), 201

# Видалення першого елемента з черги
@app.route("/api/queue/dequeue", methods=["POST"])
def dequeue_item():
    if customer_queue.is_empty():
        return jsonify({
            "error": "Черга порожня."
        }), 400

    item = customer_queue.dequeue()

    log_operation(
        "queue:dequeue",
        json.dumps({"item": item}, ensure_ascii=False)
    )

    return jsonify({
        "message": "Елемент видалено з черги.",
        "removed": item,
        "items": list(customer_queue.items),
        "size": customer_queue.size()
    })

# Отримання поточного стану стека
@app.route("/api/stack", methods=["GET"])
def get_stack():
    return jsonify({
        "items": list(transaction_stack.items),
        "size": transaction_stack.size()
    })

# Додавання елемента до стека
@app.route("/api/stack/push", methods=["POST"])
def push_item():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Очікується JSON-об'єкт."
        }), 400

    item = data.get("item")

    if not isinstance(item, str) or not item.strip():
        return jsonify({
            "error": "Поле item має містити непорожній текст."
        }), 400

    item = item.strip()
    transaction_stack.push(item)

    log_operation(
        "stack:push",
        json.dumps({"item": item}, ensure_ascii=False)
    )

    return jsonify({
        "message": "Елемент додано до стека.",
        "items": list(transaction_stack.items),
        "size": transaction_stack.size()
    }), 201

# Видалення верхнього елемента зі стека
@app.route("/api/stack/pop", methods=["POST"])
def pop_item():
    if transaction_stack.is_empty():
        return jsonify({
            "error": "Стек порожній."
        }), 400

    item = transaction_stack.pop()

    log_operation(
        "stack:pop",
        json.dumps({"item": item}, ensure_ascii=False)
    )

    return jsonify({
        "message": "Елемент видалено зі стека.",
        "removed": item,
        "items": list(transaction_stack.items),
        "size": transaction_stack.size()
    })
@lru_cache(maxsize=1)
def calculate_dashboard_stats():
    features_path = DATA_DIR / "user_features.csv"
    clusters_path = DATA_DIR / "user_clusters.csv"
    scores_path = DATA_DIR / "product_scores.csv"

    if not all(path.exists() for path in [
        features_path, clusters_path, scores_path
    ]):
        raise FileNotFoundError(
            "Не знайдено один або декілька файлів статистики."
        )

    # Загальна статистика користувачів
    totals = {
        "users": 0,
        "views": 0,
        "carts": 0,
        "purchases": 0
    }

    for chunk in pd.read_csv(features_path, chunksize=100_000):
        totals["users"] += len(chunk)

        for column in ("views", "carts", "purchases"):
            if column in chunk.columns:
                totals[column] += int(chunk[column].sum())

    # Кількість користувачів у кожному кластері
    cluster_counts = {}

    for chunk in pd.read_csv(clusters_path, chunksize=100_000):
        cluster_column = next(
            (
                col for col in ("cluster", "cluster_label", "Cluster")
                if col in chunk.columns
            ),
            None
        )

        if cluster_column is None:
            raise ValueError(
                "Не знайдено колонку кластера у user_clusters.csv."
            )

        counts = chunk[cluster_column].value_counts()

        for cluster, count in counts.items():
            key = str(cluster)
            cluster_counts[key] = (
                cluster_counts.get(key, 0) + int(count)
            )

    # Кількість товарів у каталозі рекомендацій
    products = sum(
        1 for _ in open(scores_path, encoding="utf-8")
    ) - 1

    return {
        **totals,
        "products": max(products, 0),
        "clusters": cluster_counts
    }


@app.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    try:
        return jsonify(calculate_dashboard_stats())
    except (OSError, ValueError, KeyError) as error:
        app.logger.exception("Не вдалося розрахувати статистику Dashboard")
        return jsonify({"error": str(error)}), 500


@app.route("/api/pca-visualization")
def pca_visualization():
    html_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "pca_clusters.html"
    )

    if not html_path.exists():
        return jsonify({
            "error": "PCA-візуалізацію ще не створено."
        }), 404

    return send_file(
        html_path,
        mimetype="text/html"
    )

if __name__ == "__main__":
    app.run(debug=True)