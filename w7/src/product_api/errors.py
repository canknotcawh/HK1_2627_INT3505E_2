from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException
class ApiError(Exception):
    status=500; code="internal_error"
    def __init__(self, detail=""): self.detail=detail
class NotFound(ApiError): status=404; code="not_found"
class Conflict(ApiError): status=409; code="conflict"
def register_errors(app):
    @app.errorhandler(ApiError)
    def api_error(e): return jsonify(error=e.code, detail=e.detail), e.status
    @app.errorhandler(ValidationError)
    def validation(e): return jsonify(error="validation_error", detail=e.messages), 422
    @app.errorhandler(HTTPException)
    def http(e): return jsonify(error=(e.name or "http_error").lower().replace(" ","_"), detail=e.description), e.code
    @app.errorhandler(Exception)
    def unexpected(e):
        app.logger.exception("unhandled")
        return jsonify(error="internal_error", detail="Unexpected server error"), 500
