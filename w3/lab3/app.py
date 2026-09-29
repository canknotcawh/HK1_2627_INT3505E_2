import base64
import binascii
import hashlib
import json
import logging
import random
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger("api")

STATUSES = ("pending", "paid", "shipped", "cancelled")
SORT_FIELDS = ("id", "total", "created_at")
ALL_FIELDS = ("id", "customer_id", "status", "total", "created_at")
DEFAULT_LIMIT = 10
MAX_LIMIT = 100


class BadRequest(Exception):
    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


def seed_orders(n=60):
    rnd = random.Random(42)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    orders = []
    for i in range(1, n + 1):
        orders.append({
            "id": i,
            "customer_id": rnd.randint(1, 5),
            "status": rnd.choice(STATUSES),
            # totals are drawn from a small set so ties are common
            "total": rnd.choice([10, 20, 30, 40, 50, 75, 100]),
            "created_at": (base + timedelta(hours=i // 3)).isoformat(),
        })
    return orders


ORDERS = seed_orders()


def encode_cursor(payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(token):
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        payload = json.loads(raw)
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise BadRequest("cursor is malformed")
    if not isinstance(payload, dict) or not {"v", "id", "q"} <= payload.keys():
        raise BadRequest("cursor is malformed")
    if not isinstance(payload["id"], int) or not isinstance(payload["q"], str):
        raise BadRequest("cursor is malformed")
    return payload


def query_fingerprint(status, customer_id, sort):
    text = f"{status}|{customer_id}|{sort}"
    return hashlib.sha1(text.encode()).hexdigest()[:8]


def parse_limit(raw):
    if raw is None:
        return DEFAULT_LIMIT
    if not raw.isdigit() or not 1 <= int(raw) <= MAX_LIMIT:
        raise BadRequest(f"limit must be an integer between 1 and {MAX_LIMIT}")
    return int(raw)


def parse_sort(raw):
    field = raw.lstrip("-")
    if field not in SORT_FIELDS or raw.count("-") > 1 or (raw.count("-") and not raw.startswith("-")):
        raise BadRequest(f"sort must be one of {list(SORT_FIELDS)}, optionally prefixed with '-'")
    return field, raw.startswith("-")


def parse_fields(raw):
    if raw is None:
        return None
    fields = [f for f in raw.split(",") if f]
    unknown = [f for f in fields if f not in ALL_FIELDS]
    if not fields or unknown:
        raise BadRequest(f"unknown fields {unknown}; allowed: {list(ALL_FIELDS)}" if unknown
                         else "fields must not be empty")
    return fields


def list_orders():
    args = request.args
    limit = parse_limit(args.get("limit"))
    sort = args.get("sort", "id")
    field, desc = parse_sort(sort)
    fields = parse_fields(args.get("fields"))

    status = args.get("status")
    if status is not None and status not in STATUSES:
        raise BadRequest(f"status must be one of {list(STATUSES)}")
    customer_id = args.get("customer_id")
    if customer_id is not None and not customer_id.isdigit():
        raise BadRequest("customer_id must be an integer")

    items = ORDERS
    if status:
        items = [o for o in items if o["status"] == status]
    if customer_id:
        items = [o for o in items if o["customer_id"] == int(customer_id)]

    # (sort value, id) is a total order, so keyset pagination is stable even with ties
    items = sorted(items, key=lambda o: (o[field], o["id"]), reverse=desc)

    fingerprint = query_fingerprint(status, customer_id, sort)
    token = args.get("cursor")
    if token:
        cur = decode_cursor(token)
        if cur["q"] != fingerprint:
            raise BadRequest("cursor does not match the current filter/sort")
        last = (cur["v"], cur["id"])
        try:
            if desc:
                items = [o for o in items if (o[field], o["id"]) < last]
            else:
                items = [o for o in items if (o[field], o["id"]) > last]
        except TypeError:
            raise BadRequest("cursor is malformed")

    page = items[:limit]
    has_more = len(items) > limit
    next_cursor = None
    if has_more:
        tail = page[-1]
        next_cursor = encode_cursor({"v": tail[field], "id": tail["id"], "q": fingerprint})

    if fields:
        page = [{k: o[k] for k in fields} for o in page]
    return jsonify({"data": page, "page": {"limit": limit, "has_more": has_more,
                                           "next_cursor": next_cursor}})


def problem(status, title, detail):
    resp = jsonify({"type": "about:blank", "title": title, "status": status,
                    "detail": detail, "instance": request.path})
    resp.status_code = status
    resp.headers["Content-Type"] = "application/problem+json"
    return resp


def create_app():
    app = Flask(__name__)
    app.add_url_rule("/orders", "list_orders", list_orders, methods=["GET"])

    @app.errorhandler(BadRequest)
    def on_bad_request(err):
        return problem(400, "Bad Request", err.detail)

    @app.errorhandler(HTTPException)
    def on_http(err):
        return problem(err.code, err.name, err.description)

    @app.errorhandler(Exception)
    def on_unexpected(err):
        log.exception("unhandled error on %s", request.path)
        return problem(500, "Internal Server Error", "An unexpected error occurred.")

    return app


if __name__ == "__main__":
    create_app().run(port=5000)