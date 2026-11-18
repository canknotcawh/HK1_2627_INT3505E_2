from flask import Blueprint, jsonify, request, url_for

from .users_data import create_user, find_by_email, get_user

bp = Blueprint("v2", __name__)

EMAIL_MAX_LENGTH = 254


def render(uid):
    u = get_user(uid)
    return {
        "id": uid,
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"],
    }


def validate(data):
    if not isinstance(data, dict):
        return "body must be a JSON object"
    for field in ("first_name", "last_name"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"{field} is required and must be a non-empty string"
    email = data.get("email")
    if not isinstance(email, str) or not email.strip():
        return "email is required and must be a non-empty string"
    email = email.strip()
    if len(email) > EMAIL_MAX_LENGTH:
        return f"email must be at most {EMAIL_MAX_LENGTH} characters"
    local, _, domain = email.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        return "email must look like local@domain.tld"
    return None


@bp.route("/users/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u:
        return {"error": "nf"}, 404
    return {
        "id": uid,
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"],
    }


@bp.route("/users", methods=["POST"])
def create():
    data = request.get_json(silent=True)
    problem = validate(data)
    if problem:
        return {"error": "invalid", "message": problem}, 422

    email = data["email"].strip()
    if find_by_email(email) is not None:
        return {"error": "conflict", "message": "email already exists"}, 409

    uid = create_user(data["first_name"].strip(), data["last_name"].strip(), email)
    response = jsonify(render(uid))
    response.status_code = 201
    response.headers["Location"] = url_for("v2.get", uid=uid)
    return response
