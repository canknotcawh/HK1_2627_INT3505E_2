from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import yaml
from flask import Flask, jsonify, request

app = Flask(__name__)
SPEC_PATH = Path(__file__).with_name("openapi.yaml")
TASKS = {}
STATUSES = {"todo", "in_progress", "done"}
PRIORITIES = {"low", "medium", "high"}


def error(code, message, status):
    return jsonify({"code": code, "message": message}), status


def validate_fields(data, *, creating=False):
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    allowed = {"title", "status", "priority", "dueDate", "assigneeId"}
    unknown = set(data) - allowed
    if unknown:
        return f"Unknown field(s): {', '.join(sorted(unknown))}"
    if creating and not isinstance(data.get("title"), str):
        return "title is required and must be a string"
    if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip() or len(data["title"]) > 200):
        return "title must contain 1-200 characters"
    if "status" in data and data["status"] not in STATUSES:
        return "status must be todo, in_progress, or done"
    if "priority" in data and data["priority"] not in PRIORITIES:
        return "priority must be low, medium, or high"
    if "dueDate" in data and data["dueDate"] is not None:
        try:
            date.fromisoformat(data["dueDate"])
        except (TypeError, ValueError):
            return "dueDate must use YYYY-MM-DD format or be null"
    if "assigneeId" in data and data["assigneeId"] is not None:
        try:
            UUID(data["assigneeId"])
        except (TypeError, ValueError, AttributeError):
            return "assigneeId must be a UUID or null"
    return None


@app.before_request
def require_bearer_token():
    if request.path in {"/docs", "/openapi.json"}:
        return None
    if not request.headers.get("Authorization", "").startswith("Bearer "):
        return error("unauthorized", "Provide a bearer token", 401)
    return None


@app.get("/openapi.json")
def openapi_json():
    return jsonify(yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8")))


@app.get("/docs")
def docs():
    return '''<!doctype html><html><head><title>Tasks API docs</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></head>
<body><div id="swagger-ui"></div><script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:'/openapi.json',dom_id:'#swagger-ui'});</script></body></html>'''


@app.get("/v1/tasks")
def list_tasks():
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(100, max(1, int(request.args.get("pageSize", 20))))
    except ValueError:
        return error("bad_request", "page and pageSize must be integers", 400)
    status = request.args.get("status")
    if status and status not in STATUSES:
        return error("validation_error", "Invalid status filter", 422)
    items = sorted(TASKS.values(), key=lambda item: item["createdAt"])
    if status:
        items = [item for item in items if item["status"] == status]
    start = (page - 1) * page_size
    return jsonify({"items": items[start:start + page_size], "page": page,
                    "pageSize": page_size, "totalItems": len(items)})


@app.post("/v1/tasks")
def create_task():
    data = request.get_json(silent=True)
    if data is None:
        return error("bad_request", "Request body must be valid JSON", 400)
    problem = validate_fields(data, creating=True)
    if problem:
        return error("validation_error", problem, 422)
    task_id = str(uuid4())
    task = {"id": task_id, "title": data["title"].strip(),
            "status": data.get("status", "todo"), "priority": data.get("priority", "medium"),
            "dueDate": data.get("dueDate"), "assigneeId": data.get("assigneeId"),
            "createdAt": datetime.now(timezone.utc).isoformat()}
    TASKS[task_id] = task
    return jsonify(task), 201


def find_task(task_id):
    try:
        normalized = str(UUID(task_id))
    except ValueError:
        return None, error("not_found", "Task not found", 404)
    task = TASKS.get(normalized)
    return (task, None) if task else (None, error("not_found", "Task not found", 404))


@app.get("/v1/tasks/<task_id>")
def get_task(task_id):
    task, failure = find_task(task_id)
    return failure or jsonify(task)


@app.patch("/v1/tasks/<task_id>")
def patch_task(task_id):
    task, failure = find_task(task_id)
    if failure:
        return failure
    data = request.get_json(silent=True)
    if data is None:
        return error("bad_request", "Request body must be valid JSON", 400)
    problem = validate_fields(data)
    if problem:
        return error("validation_error", problem, 422)
    if not data:
        return error("validation_error", "At least one field is required", 422)
    task.update(data)
    return jsonify(task)


@app.delete("/v1/tasks/<task_id>")
def delete_task(task_id):
    task, failure = find_task(task_id)
    if failure:
        return failure
    del TASKS[task["id"]]
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
