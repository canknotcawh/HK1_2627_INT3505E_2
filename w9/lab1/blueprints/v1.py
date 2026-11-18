from datetime import datetime, timezone
from email.utils import format_datetime

from flask import Blueprint, request

from .users_data import get_user

bp = Blueprint("v1", __name__)

@bp.route("/users/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u:
        return {"error": "nf"}, 404
    return {
        "id": uid,
        "full_name": f"{u['first_name']} {u['last_name']}",
        "email": u["email"],
    }

