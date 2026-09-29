from datetime import datetime, timezone
from flask import Flask, Blueprint, jsonify, request, url_for

api = Blueprint("api", __name__, url_prefix="/api/v1")

POSTS = {}
_next_id = 1
MAX_LIMIT = 50
SORT_FIELDS = {"id", "created_at", "title"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def error(status, message):
    return jsonify({"error": message}), status


def validate(data, partial=False):
    if not isinstance(data, dict):
        return "body must be a JSON object"
    for field in ("title", "body"):
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return f"{field} must be a non-empty string"
        elif not partial:
            return f"{field} is required"
    if "author_id" in data and not isinstance(data["author_id"], int):
        return "author_id must be an integer"
    if not partial and "author_id" not in data:
        return "author_id is required"
    tags = data.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        return "tags must be a list of strings"
    return None


@api.get("/posts")
def list_posts():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return error(400, "page and limit must be integers")
    if page < 1 or not 1 <= limit <= MAX_LIMIT:
        return error(400, f"page >= 1 and 1 <= limit <= {MAX_LIMIT}")

    items = list(POSTS.values())
    tag = request.args.get("tag")
    if tag:
        items = [p for p in items if tag in p["tags"]]
    author = request.args.get("author_id")
    if author:
        if not author.isdigit():
            return error(400, "author_id must be an integer")
        items = [p for p in items if p["author_id"] == int(author)]

    sort = request.args.get("sort", "-created_at")
    field = sort.lstrip("-")
    if field not in SORT_FIELDS:
        return error(400, f"sort must be one of {sorted(SORT_FIELDS)}")
    items.sort(key=lambda p: (p[field], p["id"]), reverse=sort.startswith("-"))

    total = len(items)
    start = (page - 1) * limit
    data = items[start:start + limit]
    meta = {"page": page, "limit": limit, "total": total}
    resp = jsonify({"data": data, "meta": meta})
    links = []
    if start + limit < total:
        links.append(f'<{url_for("api.list_posts", page=page + 1, limit=limit)}>; rel="next"')
    if page > 1:
        links.append(f'<{url_for("api.list_posts", page=page - 1, limit=limit)}>; rel="prev"')
    if links:
        resp.headers["Link"] = ", ".join(links)
    return resp


@api.post("/posts")
def create_post():
    global _next_id
    data = request.get_json(silent=True)
    msg = validate(data)
    if msg:
        return error(422, msg)
    post = {
        "id": _next_id,
        "title": data["title"].strip(),
        "body": data["body"],
        "author_id": data["author_id"],
        "tags": sorted(set(data.get("tags", []))),
        "created_at": now(),
        "updated_at": now(),
    }
    POSTS[_next_id] = post
    _next_id += 1
    resp = jsonify(post)
    resp.status_code = 201
    resp.headers["Location"] = url_for("api.get_post", post_id=post["id"])
    return resp


@api.get("/posts/<int:post_id>")
def get_post(post_id):
    post = POSTS.get(post_id)
    return jsonify(post) if post else error(404, "post not found")


@api.put("/posts/<int:post_id>")
def replace_post(post_id):
    post = POSTS.get(post_id)
    if not post:
        return error(404, "post not found")
    data = request.get_json(silent=True)
    msg = validate(data)
    if msg:
        return error(422, msg)
    post.update(title=data["title"].strip(), body=data["body"],
                author_id=data["author_id"],
                tags=sorted(set(data.get("tags", []))), updated_at=now())
    return jsonify(post)


@api.patch("/posts/<int:post_id>")
def update_post(post_id):
    post = POSTS.get(post_id)
    if not post:
        return error(404, "post not found")
    data = request.get_json(silent=True)
    msg = validate(data, partial=True)
    if msg:
        return error(422, msg)
    for key in ("title", "body", "author_id"):
        if key in data:
            post[key] = data[key]
    if "tags" in data:
        post["tags"] = sorted(set(data["tags"]))
    post["updated_at"] = now()
    return jsonify(post)


@api.delete("/posts/<int:post_id>")
def delete_post(post_id):
    if POSTS.pop(post_id, None) is None:
        return error(404, "post not found")
    return "", 204


def create_app():
    app = Flask(__name__)
    app.register_blueprint(api)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)