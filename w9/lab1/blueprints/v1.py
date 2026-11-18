from datetime import datetime, timezone
from email.utils import format_datetime

from flask import Blueprint, request

from .users_data import get_user

bp = Blueprint("v1", __name__)

# v1 không nhận thêm tính năng mới từ thời điểm này.
DEPRECATED_AT = datetime(2026, 12, 1, tzinfo=timezone.utc)
# Sau ngày này client phải chuyển sang v2 vì v1 sẽ ngừng phục vụ.
SUNSET_AT = datetime(2027, 6, 30, tzinfo=timezone.utc)


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


@bp.after_request
def mark_deprecated(response):
    """Mọi response của v1 đều báo cho client biết phiên bản sắp bị thay thế."""
    response.headers["Deprecation"] = f"@{int(DEPRECATED_AT.timestamp())}"
    response.headers["Sunset"] = format_datetime(SUNSET_AT, usegmt=True)

    uid = (request.view_args or {}).get("uid")
    successor = f"/api/v2/users/{uid}" if uid else "/api/v2/users"
    response.headers["Link"] = f'<{successor}>; rel="successor-version"'
    return response
