import base64
import json
import pytest
from app import create_app, ORDERS, encode_cursor


@pytest.fixture
def client():
    return create_app().test_client()


def walk(client, qs, limit=7):
    """Follow next_cursor until exhausted; return all items in order."""
    items, url, pages = [], f"/orders?limit={limit}&{qs}", 0
    while url:
        body = client.get(url).get_json()
        items += body["data"]
        pages += 1
        cur = body["page"]["next_cursor"]
        url = f"/orders?limit={limit}&{qs}&cursor={cur}" if cur else None
        assert pages < 100
    return items


def test_default_response_shape(client):
    body = client.get("/orders").get_json()
    assert len(body["data"]) == 10
    assert set(body["page"]) == {"limit", "has_more", "next_cursor"}
    assert body["page"]["has_more"] is True


def test_limit(client):
    assert len(client.get("/orders?limit=5").get_json()["data"]) == 5


@pytest.mark.parametrize("qs", ["limit=0", "limit=101", "limit=x", "limit=-1"])
def test_bad_limit(client, qs):
    assert client.get(f"/orders?{qs}").status_code == 400


def test_filter_status(client):
    data = client.get("/orders?status=paid&limit=100").get_json()["data"]
    assert data and all(o["status"] == "paid" for o in data)
    assert len(data) == sum(o["status"] == "paid" for o in ORDERS)


def test_filter_customer_and_status(client):
    data = client.get("/orders?status=paid&customer_id=2&limit=100").get_json()["data"]
    assert all(o["status"] == "paid" and o["customer_id"] == 2 for o in data)


def test_bad_filter_values(client):
    assert client.get("/orders?status=nope").status_code == 400
    assert client.get("/orders?customer_id=abc").status_code == 400


def test_sparse_fields(client):
    data = client.get("/orders?fields=id,total").get_json()["data"]
    assert all(set(o) == {"id", "total"} for o in data)


def test_unknown_field_is_400(client):
    assert client.get("/orders?fields=id,password").status_code == 400


# ---- cursor ----

def test_walk_covers_everything_once(client):
    items = walk(client, "")
    assert [o["id"] for o in items] == [o["id"] for o in ORDERS]


@pytest.mark.parametrize("sort", ["total", "-total", "created_at", "-created_at", "-id"])
def test_walk_with_sort_has_no_gaps_or_duplicates(client, sort):
    items = walk(client, f"sort={sort}")
    ids = [o["id"] for o in items]
    assert len(ids) == len(set(ids)) == len(ORDERS)
    field, desc = sort.lstrip("-"), sort.startswith("-")
    keys = [(o[field], o["id"]) for o in items]
    assert keys == sorted(keys, reverse=desc)


def test_walk_with_filter_and_sort(client):
    items = walk(client, "status=paid&sort=-total", limit=3)
    expected = sorted((o for o in ORDERS if o["status"] == "paid"),
                      key=lambda o: (o["total"], o["id"]), reverse=True)
    assert [o["id"] for o in items] == [o["id"] for o in expected]


def test_last_page_has_no_cursor(client):
    body = client.get("/orders?limit=100").get_json()
    assert body["page"]["has_more"] is False and body["page"]["next_cursor"] is None


def test_sparse_fields_do_not_break_cursor(client):
    items = walk(client, "fields=id&sort=-total")
    assert len(items) == len(ORDERS) and all(set(o) == {"id"} for o in items)


@pytest.mark.parametrize("cursor", [
    "garbage",
    "!!!",
    base64.urlsafe_b64encode(b"not json").decode(),
    base64.urlsafe_b64encode(b'[1,2,3]').decode(),
    base64.urlsafe_b64encode(json.dumps({"v": 1}).encode()).decode(),
    encode_cursor({"v": 1, "id": "x", "q": "abc"}),
])
def test_bad_cursor_is_400(client, cursor):
    r = client.get(f"/orders?cursor={cursor}")
    assert r.status_code == 400
    assert r.mimetype == "application/problem+json"
    assert "Traceback" not in r.get_data(as_text=True)


def test_cursor_reused_with_different_sort_or_filter_is_400(client):
    cur = client.get("/orders?sort=total&limit=3").get_json()["page"]["next_cursor"]
    assert client.get(f"/orders?sort=-total&cursor={cur}").status_code == 400
    assert client.get(f"/orders?sort=total&status=paid&cursor={cur}").status_code == 400
    assert client.get(f"/orders?sort=total&cursor={cur}").status_code == 200


def test_invalid_sort_is_400(client):
    for s in ("customer_id", "--total", "total-", "status"):
        assert client.get(f"/orders?sort={s}").status_code == 400