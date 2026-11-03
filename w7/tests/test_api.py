from sqlalchemy import event
from product_api.extensions import db


def add_product(client, sku="KB-001", name="Keyboard", stock=10):
    return client.post("/api/v1/products", json={
        "sku": sku, "name": name, "price_cents": 1000, "qty_in_stock": stock,
    })


def test_post_product_and_defaults(client):
    response = client.post("/api/v1/products", json={
        "sku": "KB-001", "name": "Keyboard", "price_cents": 1000,
    })
    assert response.status_code == 201
    assert response.json["qty_in_stock"] == 0


def test_product_validation_returns_422(client):
    for payload in (
        {"sku": "x", "name": "Keyboard", "price_cents": 100},
        {"sku": "KB-1", "name": "   ", "price_cents": 100},
        {"sku": "KB-1", "name": "Keyboard", "price_cents": -1},
        {"sku": "KB-1", "name": "Keyboard", "price_cents": "100"},
    ):
        assert client.post("/api/v1/products", json=payload).status_code == 422


def test_duplicate_sku_conflict(client):
    assert add_product(client).status_code == 201
    response = add_product(client)
    assert response.status_code == 409
    assert response.json["error"] == "conflict"


def test_product_get_and_pagination(client):
    add_product(client)
    response = client.get("/api/v1/products?page=1&size=20")
    assert response.status_code == 200
    assert response.json["total"] == 1
    assert response.json["items"][0]["sku"] == "KB-001"
    assert client.get("/api/v1/products?page=0").status_code == 422
    assert client.get("/api/v1/products/999").status_code == 404


def test_reserve_patch_and_soft_delete(client):
    product_id = add_product(client, stock=3).json["id"]
    assert client.post(f"/api/v1/products/{product_id}/reserve", json={"qty": 2}).json["qty_in_stock"] == 1
    assert client.post(f"/api/v1/products/{product_id}/reserve", json={"qty": 2}).status_code == 409
    assert client.patch(f"/api/v1/products/{product_id}", json={"price_cents": 1200}).json["price_cents"] == 1200
    assert client.patch(f"/api/v1/products/{product_id}", json={}).status_code == 422
    assert client.delete(f"/api/v1/products/{product_id}").status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").status_code == 404
    assert client.get("/api/v1/products").json["total"] == 0


def test_order_has_multiple_order_items_and_snapshots_price(client):
    first = add_product(client, "KB-001", "Keyboard", 5).json["id"]
    second = add_product(client, "MS-001", "Mouse", 5).json["id"]
    response = client.post("/api/v1/orders", json={"items": [
        {"product_id": first, "quantity": 1},
        {"product_id": second, "quantity": 2},
    ]})
    assert response.status_code == 201
    assert len(response.json["items"]) == 2
    assert {item["product_id"] for item in response.json["items"]} == {first, second}
    assert client.get(f"/api/v1/products/{first}").json["qty_in_stock"] == 4
    assert client.get(f"/api/v1/products/{second}").json["qty_in_stock"] == 3


def test_order_rejects_bad_items_and_insufficient_stock(client):
    product_id = add_product(client, stock=1).json["id"]
    assert client.post("/api/v1/orders", json={"items": [{"product_id": product_id, "quantity": 2}]}).status_code == 409
    assert client.post("/api/v1/orders", json={"items": [{"product_id": product_id, "quantity": True}]}).status_code == 422
    assert client.post("/api/v1/orders", json={"items": []}).status_code == 422


def test_get_orders_eager_loading_has_bounded_select_count(app, client):
    product_ids = [
        add_product(client, f"SKU-{index:03}", f"Product {index}").json["id"]
        for index in range(1, 4)
    ]
    for product_id in product_ids:
        response = client.post("/api/v1/orders", json={"items": [{"product_id": product_id, "quantity": 1}]})
        assert response.status_code == 201

    statements = []
    with app.app_context():
        engine = db.engine
        def count_selects(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)
        event.listen(engine, "before_cursor_execute", count_selects)
        try:
            response = client.get("/api/v1/orders")
        finally:
            event.remove(engine, "before_cursor_execute", count_selects)

    assert response.status_code == 200
    assert len(response.json["items"]) == 3
    assert all(len(order["items"]) == 1 for order in response.json["items"])
    # One SELECT for orders, one for all order_items, one for all referenced products.
    assert len(statements) <= 3, f"N+1 suspected: {len(statements)} SELECTs"


def test_health_and_readiness_are_separate(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/ready").status_code == 200
