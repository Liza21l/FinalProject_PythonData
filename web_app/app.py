import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from web_app.models import db, Operation
from web_app.algorithms import (
    bubble_sort,
    quick_sort,
    linear_search,
    binary_search
)


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


if __name__ == "__main__":
    app.run(debug=True)