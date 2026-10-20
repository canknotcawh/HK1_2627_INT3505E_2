import base64
import json
from flask import Blueprint, jsonify, request
from sqlalchemy import and_, or_
from . import db
from .models import Book

api = Blueprint("api", __name__, url_prefix="/api/v1")
SORTABLE = {"id": Book.id, "title": Book.title, "price_vnd": Book.price_vnd,
            "stock": Book.stock, "genre": Book.genre, "created_at": Book.created_at}


def parse_sort(raw, strategy):
    parts = (raw or "id:asc").split(",")
    parsed = []
    for part in parts:
        bits = part.strip().split(":")
        key = bits[0]
        direction = bits[1].lower() if len(bits) == 2 else "asc"
        if len(bits) > 2 or key not in SORTABLE or direction not in ("asc", "desc"):
            raise ValueError("sort phải gồm các khóa hợp lệ, ví dụ title:asc,price_vnd:desc")
        parsed.append((key, direction))
    if strategy == "cursor" and (not parsed or parsed[-1][0] != "id"):
        parsed.append(("id", "asc"))
    return parsed


def encode_cursor(values):
    raw = json.dumps(values, separators=(",", ":"), default=str).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(token):
    try:
        return json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
    except Exception as exc:
        raise ValueError("cursor không hợp lệ") from exc


def after_clause(sort, values):
    if not isinstance(values, list) or len(values) != len(sort):
        raise ValueError("cursor không khớp với sort hiện tại")
    normalized = []
    for (key, _), value in zip(sort, values):
        try:
            if key in ("id", "price_vnd", "stock"):
                value = int(value)
            elif key == "created_at":
                from datetime import datetime
                value = datetime.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("cursor chứa giá trị không hợp lệ") from exc
        normalized.append(value)
    alternatives = []
    for i, (key, direction) in enumerate(sort):
        equal_prefix = [SORTABLE[sort[j][0]] == normalized[j] for j in range(i)]
        col = SORTABLE[key]
        val = normalized[i]
        cmp = col > val if direction == "asc" else col < val
        alternatives.append(and_(*(equal_prefix + [cmp])))
    return or_(*alternatives)


@api.get("/books")
def list_books():
    strategy = request.args.get("strategy", "offset").lower()
    if strategy not in ("offset", "cursor"):
        return jsonify(error="strategy phải là offset hoặc cursor"), 400
    try:
        sort = parse_sort(request.args.get("sort"), strategy)
        query = Book.query
        if request.args.get("genre"):
            query = query.filter(Book.genre.ilike(request.args["genre"].strip()))
        for key, direction in sort:
            col = SORTABLE[key]
            query = query.order_by(col.asc() if direction == "asc" else col.desc())
        if strategy == "offset":
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))
            if page < 1 or not 1 <= per_page <= 100:
                raise ValueError("page >= 1 và per_page trong khoảng 1..100")
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify(data=[b.to_dict() for b in pagination.items], pagination={
                "strategy": "offset", "page": page, "per_page": per_page,
                "total": pagination.total, "pages": pagination.pages,
                "has_next": pagination.has_next, "has_prev": pagination.has_prev})
        limit = int(request.args.get("limit", 10))
        if not 1 <= limit <= 100:
            raise ValueError("limit trong khoảng 1..100")
        cursor = request.args.get("cursor")
        if cursor:
            query = query.filter(after_clause(sort, decode_cursor(cursor)))
        rows = query.limit(limit + 1).all()
        has_next = len(rows) > limit
        rows = rows[:limit]
        next_cursor = None
        if has_next and rows:
            last = rows[-1]
            values = [getattr(last, key).isoformat() if key == "created_at" else getattr(last, key) for key, _ in sort]
            next_cursor = encode_cursor(values)
        return jsonify(data=[b.to_dict() for b in rows], pagination={
            "strategy": "cursor", "limit": limit, "has_next": has_next, "next_cursor": next_cursor})
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400


@api.get("/books/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    return (jsonify(data=book.to_dict()), 200) if book else (jsonify(error="not_found"), 404)


@api.post("/books")
def create_book():
    body = request.get_json(silent=True) or {}
    required = ("title", "isbn", "price_vnd", "stock", "genre", "category_id")
    if any(k not in body for k in required):
        return jsonify(error="missing_required_fields", required=list(required)), 400
    book = Book(**{k: body[k] for k in required})
    db.session.add(book)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(error="invalid_book_or_duplicate_isbn"), 400
    return jsonify(data=book.to_dict()), 201


@api.patch("/books/<int:book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify(error="not_found"), 404
    body = request.get_json(silent=True) or {}
    for key in ("title", "isbn", "price_vnd", "stock", "genre", "category_id"):
        if key in body:
            setattr(book, key, body[key])
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(error="invalid_book_or_duplicate_isbn"), 400
    return jsonify(data=book.to_dict())


@api.delete("/books/<int:book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify(error="not_found"), 404
    db.session.delete(book)
    db.session.commit()
    return "", 204
