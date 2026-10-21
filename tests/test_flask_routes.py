
import pytest

from web_app.app import app, customer_queue, transaction_stack


@pytest.fixture
def client():
    app.config["TESTING"] = True

    # Очищаємо структури перед кожним тестом
    customer_queue.items.clear()
    transaction_stack.items.clear()

    with app.test_client() as test_client:
        yield test_client

    customer_queue.items.clear()
    transaction_stack.items.clear()


# =========================
# ГОЛОВНА СТОРІНКА
# =========================

def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"html" in response.data.lower()


# =========================
# HEALTH CHECK
# =========================

def test_health_route(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "ok"
    assert "message" in data


# =========================
# СОРТУВАННЯ
# =========================

@pytest.mark.parametrize("algorithm", ["bubble", "quick"])
def test_sort_route(client, algorithm):
    response = client.post(
        "/api/sort",
        json={
            "numbers": [5, 2, 4, 1],
            "algorithm": algorithm
        }
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["algorithm"] == algorithm
    assert data["original"] == [5, 2, 4, 1]
    assert data["sorted"] == [1, 2, 4, 5]


def test_sort_invalid_algorithm(client):
    response = client.post(
        "/api/sort",
        json={
            "numbers": [3, 1, 2],
            "algorithm": "unknown"
        }
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_sort_invalid_numbers(client):
    response = client.post(
        "/api/sort",
        json={
            "numbers": "3, 1, 2",
            "algorithm": "bubble"
        }
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


# =========================
# ПОШУК
# =========================

@pytest.mark.parametrize(
    ("algorithm", "expected_index"),
    [
        ("linear", 2),
        ("binary", 2),
    ]
)
def test_search_route(client, algorithm, expected_index):
    response = client.post(
        "/api/search",
        json={
            "numbers": [1, 3, 5, 7],
            "target": 5,
            "algorithm": algorithm
        }
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["algorithm"] == algorithm
    assert data["index"] == expected_index
    assert data["found"] is True


def test_search_value_not_found(client):
    response = client.post(
        "/api/search",
        json={
            "numbers": [1, 3, 5, 7],
            "target": 4,
            "algorithm": "linear"
        }
    )

    assert response.status_code == 200
    assert response.get_json()["index"] == -1
    assert response.get_json()["found"] is False


def test_binary_search_unsorted_list(client):
    response = client.post(
        "/api/search",
        json={
            "numbers": [5, 1, 3],
            "target": 3,
            "algorithm": "binary"
        }
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


# =========================
# QUEUE
# =========================

def test_queue_enqueue_and_dequeue(client):
    add_response = client.post(
        "/api/queue/enqueue",
        json={"item": "Операція A"}
    )

    assert add_response.status_code == 201
    assert add_response.is_json
    assert add_response.get_json()["size"] == 1

    second_response = client.post(
        "/api/queue/enqueue",
        json={"item": "Операція B"}
    )

    assert second_response.status_code == 201

    remove_response = client.post("/api/queue/dequeue")

    assert remove_response.status_code == 200
    assert remove_response.get_json()["removed"] == "Операція A"
    assert remove_response.get_json()["size"] == 1


def test_queue_dequeue_empty(client):
    response = client.post("/api/queue/dequeue")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_queue_rejects_empty_item(client):
    response = client.post(
        "/api/queue/enqueue",
        json={"item": "   "}
    )

    assert response.status_code == 400


# =========================
# STACK
# =========================

def test_stack_push_and_pop(client):
    add_response = client.post(
        "/api/stack/push",
        json={"item": "Транзакція A"}
    )

    assert add_response.status_code == 201
    assert add_response.is_json
    assert add_response.get_json()["size"] == 1

    second_response = client.post(
        "/api/stack/push",
        json={"item": "Транзакція B"}
    )

    assert second_response.status_code == 201

    remove_response = client.post("/api/stack/pop")

    assert remove_response.status_code == 200
    assert remove_response.get_json()["removed"] == "Транзакція B"
    assert remove_response.get_json()["size"] == 1


def test_stack_pop_empty(client):
    response = client.post("/api/stack/pop")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_stack_rejects_empty_item(client):
    response = client.post(
        "/api/stack/push",
        json={"item": "   "}
    )

    assert response.status_code == 400
