import logging
import uuid
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger("api")
PROBLEM_JSON = "application/problem+json"
TYPE_BASE = "https://api.example.com/problems/"


class ProblemError(Exception):
    def __init__(self, status, title, detail=None, type_slug="about:blank", **extra):
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_slug = type_slug
        self.extra = extra


class NotFound(ProblemError):
    def __init__(self, detail=None):
        super().__init__(404, "Resource Not Found", detail, "not-found")


class ValidationFailed(ProblemError):
    def __init__(self, detail=None, errors=None):
        extra = {"errors": errors} if errors else {}
        super().__init__(422, "Validation Failed", detail, "validation-error", **extra)


def problem_response(status, title, detail, type_slug="about:blank", **extra):
    type_uri = type_slug if type_slug == "about:blank" else TYPE_BASE + type_slug
    body = {
        "type": type_uri,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path,
        **extra,
    }
    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = PROBLEM_JSON
    return resp


def register_error_handlers(app):
    @app.errorhandler(ProblemError)
    def handle_problem(err):
        return problem_response(err.status, err.title, err.detail, err.type_slug, **err.extra)

    @app.errorhandler(HTTPException)
    def handle_http(err):
        resp = problem_response(err.code, err.name, err.description)
        for key, value in (err.get_headers() or []):
            if key.lower() not in ("content-type", "content-length"):
                resp.headers[key] = value
        return resp

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        error_id = uuid.uuid4().hex[:12]
        log.exception("unhandled exception error_id=%s path=%s", error_id, request.path)
        return problem_response(
            500,
            "Internal Server Error",
            "An unexpected error occurred. Quote the error_id when contacting support.",
            error_id=error_id,
        )