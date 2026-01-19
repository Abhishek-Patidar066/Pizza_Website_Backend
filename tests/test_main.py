import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_pizza_by_name():
    response = client.get("/Order/by-name/Margherita")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Margherita"


def test_get_pizza_not_found():
    response = client.get("/Order/by-name/NonExistentPizza")
    assert response.status_code == 404


def test_get_order_by_id():
    response = client.get("/Order/by-id/1")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1


def test_place_order():
    order_data = [
        {"id": 1, "quantity": 2},
        {"id": 2, "quantity": 1},
    ]

    response = client.post("/place_order/", json=order_data)
    assert response.status_code == 200

    data = response.json()
    assert "Order_id" in data
    assert len(data["order_details"]) == 2
    assert data["total_price"] > 0
    assert isinstance(data["Order_id"], str)


def test_place_order_no_available_items():
    order_data = [{"id": 999, "quantity": 1}]

    response = client.post("/place_order/", json=order_data)
    assert response.status_code == 404


def test_place_order_partial_availability():
    order_data = [
        {"id": 1, "quantity": 1},
        {"id": 999, "quantity": 1},
    ]

    response = client.post("/place_order/", json=order_data)
    assert response.status_code == 200

    data = response.json()
    assert len(data["order_details"]) == 1
    assert data["total_price"] > 0


def test_place_order_invalid_quantity():
    order_data = [{"id": 1, "quantity": -1}]

    response = client.post("/place_order/", json=order_data)
    assert response.status_code == 422


def test_place_order_empty_order():
    response = client.post("/place_order/", json=[])
    assert response.status_code == 404


def test_add_pizza_success():
    new_pizza = {
        "id": 171,
        "name": "Margherita Extra",
        "size": "Medium",
        "price": 199.99,
        "toppings": ["cheese", "tomato"],
    }

    response = client.post("/add_pizza/", json=new_pizza)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Pizza added successfully"
    assert data["pizza"]["id"] == 171
    assert data["pizza"]["name"] == "Margherita Extra"
    assert data["pizza"]["size"] == "Medium"
    assert data["pizza"]["price"] == 199.99


def test_update_pizza_success():
    update_data = {
        "price": 12.99,
        "toppings": ["cheese", "olive"],
    }

    response = client.patch("/update_pizza/1", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["pizza"]["price"] == 12.99
    assert "olive" in data["pizza"]["toppings"]


def test_update_pizza_not_found():
    response = client.patch("/update_pizza/999", json={"price": 10})
    assert response.status_code == 404
    assert response.json()["detail"] == "Pizza not found"


def test_delete_pizzas_success():
    response = client.request(
        "DELETE",
        "/delete_pizzas",
        json={"pizza_ids": [1, 2]},
    )

    assert response.status_code == 200

    data = response.json()
    assert 1 in data["deleted"]
    assert 2 in data["deleted"]


def test_delete_pizzas_partial():
    response = client.request(
        "DELETE",
        "/delete_pizzas",
        json={"pizza_ids": [1, 999]},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["deleted"] == [1]
    assert data["not_found"] == [999]
