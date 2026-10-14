from pathlib import Path

import yaml
from flask import Flask, jsonify, request

app = Flask(__name__)
SPEC_PATH = Path(__file__).with_name("petstore.yaml")
PETS = {}
NEXT_ID = 1


def error(status, message):
    return jsonify({"code": status, "message": message}), status


@app.before_request
def require_api_key():
    # The OpenAPI spec defines the header name, but not a fixed key value.
    if request.path in {"/docs", "/openapi.json"}:
        return None
    if not request.headers.get("X-API-Key", "").strip():
        return error(401, "Missing or invalid API key")


@app.get("/openapi.json")
def openapi_json():
    return jsonify(yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8")))


@app.get("/docs")
def docs():
    return '''<!doctype html>
<html><head><title>Petstore API docs</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></head>
<body><div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:'/openapi.json',dom_id:'#swagger-ui'});</script></body></html>'''


def parse_pet_id(raw_id):
    try:
        pet_id = int(raw_id)
    except (TypeError, ValueError):
        return None
    return pet_id if pet_id > 0 else None


def validate_pet(data):
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    unknown = set(data) - {"name", "tag"}
    if unknown:
        return f"Unknown field(s): {', '.join(sorted(unknown))}"
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return "name is required and must be a non-empty string"
    if "tag" in data and not isinstance(data["tag"], str):
        return "tag must be a string"
    return None


@app.get("/pets")
def list_pets():
    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return error(400, "limit must be an integer")
    if not 1 <= limit <= 100:
        return error(400, "limit must be between 1 and 100")

    tag = request.args.get("tag")
    pets = sorted(PETS.values(), key=lambda pet: pet["id"])
    if tag is not None:
        pets = [pet for pet in pets if pet.get("tag") == tag]
    return jsonify({"pets": pets[:limit]})


@app.post("/pets")
def create_pet():
    global NEXT_ID
    data = request.get_json(silent=True)
    if data is None:
        return error(400, "Request body must be valid JSON")
    problem = validate_pet(data)
    if problem:
        return error(400, problem)

    pet = {"id": NEXT_ID, "name": data["name"].strip()}
    if "tag" in data:
        pet["tag"] = data["tag"]
    PETS[NEXT_ID] = pet
    NEXT_ID += 1
    return jsonify(pet), 201


@app.get("/pets/<pet_id>")
def get_pet(pet_id):
    parsed_id = parse_pet_id(pet_id)
    if parsed_id is None:
        return error(400, "petId must be a positive integer")
    pet = PETS.get(parsed_id)
    if pet is None:
        return error(404, "Pet not found")
    return jsonify(pet)


@app.put("/pets/<pet_id>")
def update_pet(pet_id):
    parsed_id = parse_pet_id(pet_id)
    if parsed_id is None:
        return error(400, "petId must be a positive integer")
    if parsed_id not in PETS:
        return error(404, "Pet not found")

    data = request.get_json(silent=True)
    if data is None:
        return error(400, "Request body must be valid JSON")
    problem = validate_pet(data)
    if problem:
        return error(400, problem)

    pet = {"id": parsed_id, "name": data["name"].strip()}
    if "tag" in data:
        pet["tag"] = data["tag"]
    PETS[parsed_id] = pet
    return jsonify(pet)


@app.delete("/pets/<pet_id>")
def delete_pet(pet_id):
    parsed_id = parse_pet_id(pet_id)
    if parsed_id is None:
        return error(400, "petId must be a positive integer")
    if parsed_id not in PETS:
        return error(404, "Pet not found")
    del PETS[parsed_id]
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
