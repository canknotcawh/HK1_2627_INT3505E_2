import logging
import pytest
from app import create_app

REQUIRED = {"type", "title", "detail", "status", "instance"}


@pytest.fixture
def client():
    return create_app().test_client()


def check_problem(resp, status):
    assert resp.status_code == status
    assert resp.mimetype == "application/problem+json"
    body = resp.get_json()
    assert REQUIRED <= body.keys()
    assert body["status"] == status
    return body


def test_resource_not_found(client):
    r = client.get("/resources/999")
    body = check_problem(r, 404)
    assert body["instance"] == "/resources/999"
    assert "Traceback" not in r.get_data(as_text=True)


@pytest.mark.parametrize("accept", [None, "application/json", "*/*", "text/html"])
def test_problem_json_regardless_of_accept(client, accept):
    headers = {"Accept": accept} if accept else {}
    check_problem(client.get("/resources/999", headers=headers), 404)


def test_validation_error_has_extension(client):
    body = check_problem(client.post("/resources", json={}), 422)
    assert body["errors"][0]["field"] == "name"


def test_http_exception_fallback_404_route(client):
    body = check_problem(client.get("/no/such/route"), 404)
    assert body["instance"] == "/no/such/route"


def test_http_exception_fallback_405_keeps_allow_header(client):
    r = client.delete("/resources/1")
    check_problem(r, 405)
    assert "GET" in r.headers["Allow"]


def test_unhandled_exception_is_neutral_and_logged(client, caplog):
    with caplog.at_level(logging.ERROR, logger="api"):
        r = client.get("/boom")
    body = check_problem(r, 500)
    text = r.get_data(as_text=True)
    assert "secret" not in text and "db.py" not in text and "Traceback" not in text
    assert body["error_id"] in caplog.text
    assert "RuntimeError" in caplog.text and "secret" in caplog.text