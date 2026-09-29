import pytest
import app as blog


@pytest.fixture
def client():
    blog.POSTS.clear()
    blog._next_id = 1
    return blog.create_app().test_client()


def make(client, **kw):
    body = {"title": "Hello", "body": "text", "author_id": 1, "tags": []}
    body.update(kw)
    return client.post("/api/v1/posts", json=body)


def test_create_returns_201_and_location(client):
    r = make(client, tags=["flask", "flask", "api"])
    assert r.status_code == 201
    assert r.headers["Location"] == "/api/v1/posts/1"
    assert r.get_json()["tags"] == ["api", "flask"]


def test_create_validation(client):
    assert client.post("/api/v1/posts", json={"title": ""}).status_code == 422
    assert client.post("/api/v1/posts", data="x").status_code == 422


def test_get_put_patch_delete(client):
    make(client)
    assert client.get("/api/v1/posts/1").status_code == 200
    r = client.put("/api/v1/posts/1", json={"title": "New", "body": "b", "author_id": 2})
    assert r.get_json()["title"] == "New"
    r = client.patch("/api/v1/posts/1", json={"body": "patched"})
    assert r.get_json()["body"] == "patched" and r.get_json()["title"] == "New"
    assert client.delete("/api/v1/posts/1").status_code == 204
    assert client.get("/api/v1/posts/1").status_code == 404
    assert client.delete("/api/v1/posts/1").status_code == 404


def test_list_filter_and_paging(client):
    for i in range(5):
        make(client, title=f"p{i}", author_id=1 + i % 2, tags=["a"] if i < 3 else [])
    r = client.get("/api/v1/posts?limit=2&sort=id")
    body = r.get_json()
    assert [p["id"] for p in body["data"]] == [1, 2]
    assert body["meta"]["total"] == 5
    assert 'rel="next"' in r.headers["Link"]
    assert client.get("/api/v1/posts?tag=a").get_json()["meta"]["total"] == 3
    assert client.get("/api/v1/posts?author_id=2").get_json()["meta"]["total"] == 2


@pytest.mark.parametrize("qs", ["limit=0", "limit=999", "page=x", "sort=body", "author_id=x"])
def test_list_bad_params(client, qs):
    assert client.get(f"/api/v1/posts?{qs}").status_code == 400