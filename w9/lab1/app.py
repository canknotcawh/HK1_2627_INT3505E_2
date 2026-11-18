"""Lab 1 - URI Path Versioning: User API v1 -> v2 với Flask Blueprint."""

from pathlib import Path

import yaml
from flask import Flask, jsonify

from blueprints.v1 import bp as v1_bp
from blueprints.v2 import bp as v2_bp

SPEC_PATH = Path(__file__).with_name("openapi.yaml")


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.register_blueprint(v1_bp, url_prefix="/api/v1")
    app.register_blueprint(v2_bp, url_prefix="/api/v2")

    @app.get("/openapi.json")
    def openapi_json():
        return jsonify(yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8")))

    @app.get("/docs")
    def docs():
        return """<!doctype html><html><head><title>User API v1 / v2</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"></head>
<body><div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:'/openapi.json', dom_id:'#swagger-ui'});</script>
</body></html>"""

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
