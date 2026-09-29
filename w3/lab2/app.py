from flask import Flask, jsonify, request
from problem import register_error_handlers, NotFound, ValidationFailed

RESOURCES = {1: {"id": 1, "name": "alpha"}, 2: {"id": 2, "name": "beta"}}


def create_app():
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/resources/<int:resource_id>")
    def get_resource(resource_id):
        item = RESOURCES.get(resource_id)
        if item is None:
            raise NotFound(f"Resource {resource_id} does not exist.")
        return jsonify(item)

    @app.post("/resources")
    def create_resource():
        data = request.get_json(silent=True) or {}
        if not data.get("name"):
            raise ValidationFailed("Request body is invalid.",
                                   errors=[{"field": "name", "message": "required"}])
        return jsonify(data), 201

    @app.get("/boom")
    def boom():
        raise RuntimeError("db password=secret at /srv/app/db.py line 42")

    return app


if __name__ == "__main__":
    create_app().run(debug=False)