def test_offset_pagination(client):
    response = client.get("/api/v1/books?strategy=offset&page=1&per_page=2")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["has_next"] is True


def test_cursor_pagination_is_contiguous(client):
    first = client.get("/api/v1/books?strategy=cursor&limit=2&sort=title:asc,id:asc").get_json()
    token = first["pagination"]["next_cursor"]
    second = client.get(f"/api/v1/books?strategy=cursor&limit=2&sort=title:asc,id:asc&cursor={token}").get_json()
    assert [b["title"] for b in first["data"]] == ["API Design", "Blue Mountain"]
    assert [b["title"] for b in second["data"]] == ["The River"]
    assert first["data"][-1]["id"] != second["data"][0]["id"]


def test_genre_filter_and_multi_sort(client):
    response = client.get("/api/v1/books?genre=fiction&sort=price_vnd:desc,title:asc")
    assert [b["price_vnd"] for b in response.get_json()["data"]] == [160000, 120000]


def test_bad_sort_rejected(client):
    response = client.get("/api/v1/books?sort=secret:asc")
    assert response.status_code == 400


def test_invalid_strategy_rejected(client):
    assert client.get("/api/v1/books?strategy=unknown").status_code == 400


def test_book_crud(client):
    payload = {"title": "Test", "isbn": "9780000000099", "price_vnd": 100, "stock": 1, "genre": "fiction", "category_id": 1}
    created = client.post("/api/v1/books", json=payload)
    assert created.status_code == 201
    book_id = created.get_json()["data"]["id"]
    assert client.patch(f"/api/v1/books/{book_id}", json={"stock": 4}).get_json()["data"]["stock"] == 4
    assert client.delete(f"/api/v1/books/{book_id}").status_code == 204
