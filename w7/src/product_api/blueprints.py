from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from .extensions import db
from .models import Product, Order, OrderItem
from .schemas import ProductIn, ProductOut, ProductPatch, ReserveIn
from .errors import NotFound, Conflict

products = Blueprint("products", __name__, url_prefix="/api/v1/products")
orders = Blueprint("orders", __name__, url_prefix="/api/v1/orders")
health = Blueprint("health", __name__)


def active(pid):
    product = db.session.get(Product, pid)
    if product is None or product.archived:
        raise NotFound("product not found")
    return product


def _json_body():
    if not request.is_json:
        raise ValidationError({"body": "Content-Type must be application/json"})
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError({"body": "JSON body must be an object"})
    return data


@products.get("")
def list_products():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 20))
    except (TypeError, ValueError):
        raise ValidationError({"query": "page and size must be integers"})
    if page < 1 or size < 1 or size > 100:
        raise ValidationError({"query": "page must be >= 1 and size must be between 1 and 100"})
    filt = Product.archived.is_(False)
    total = db.session.scalar(db.select(func.count()).select_from(Product).where(filt)) or 0
    rows = db.session.execute(
        db.select(Product).where(filt).order_by(Product.id).offset((page - 1) * size).limit(size)
    ).scalars().all()
    return jsonify(items=ProductOut(many=True).dump(rows), page=page, size=size, total=total)


@products.get("/<int:pid>")
def get_product(pid):
    return jsonify(ProductOut().dump(active(pid)))


@products.post("")
def create_product():
    product = Product(**ProductIn().load(_json_body()))
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("sku already exists")
    return jsonify(ProductOut().dump(product)), 201


@products.post("/<int:pid>/reserve")
def reserve(pid):
    data = ReserveIn().load(_json_body())
    product = active(pid)
    # Conditional UPDATE makes reservation atomic and prevents overselling under concurrency.
    result = db.session.execute(
        update(Product)
        .where(Product.id == pid, Product.archived.is_(False), Product.qty_in_stock >= data["qty"])
        .values(qty_in_stock=Product.qty_in_stock - data["qty"])
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise Conflict(f"insufficient stock; available quantity may have changed")
    db.session.commit()
    db.session.refresh(product)
    return jsonify(ProductOut().dump(product))


@products.patch("/<int:pid>")
def patch(pid):
    data = ProductPatch().load(_json_body(), partial=True)
    if not data:
        raise ValidationError({"body": "provide at least one supported field"})
    product = active(pid)
    for key, value in data.items():
        setattr(product, key, value)
    db.session.commit()
    return jsonify(ProductOut().dump(product))


@products.delete("/<int:pid>")
def delete(pid):
    product = active(pid)
    product.archived = True
    db.session.commit()
    return "", 204


def order_data(order):
    return {
        "id": order.id,
        "status": order.status,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price_cents": item.unit_price_cents,
                "product": ProductOut().dump(item.product),
            }
            for item in order.items
        ],
    }


@orders.post("")
def create_order():
    data = _json_body()
    items = data.get("items")
    if set(data) != {"items"} or not isinstance(items, list) or not items:
        raise ValidationError({"items": "provide a non-empty items list"})
    normalized = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != {"product_id", "quantity"}:
            raise ValidationError({"items": {index: "each item requires only product_id and quantity"}})
        product_id, quantity = item["product_id"], item["quantity"]
        if type(product_id) is not int or product_id < 1 or type(quantity) is not int or quantity < 1:
            raise ValidationError({"items": {index: "product_id and quantity must be positive integers"}})
        normalized.append((product_id, quantity))
    ids = [product_id for product_id, _ in normalized]
    if len(set(ids)) != len(ids):
        raise ValidationError({"items": "duplicate product_id; combine quantities into one item"})

    try:
        # Lock product rows where supported (PostgreSQL); stock is still checked in a
        # conditional UPDATE to remain safe against concurrent order creation.
        products_by_id = {
            product.id: product
            for product in db.session.execute(
                db.select(Product).where(Product.id.in_(ids), Product.archived.is_(False)).with_for_update()
            ).scalars()
        }
        if len(products_by_id) != len(ids):
            raise NotFound("one or more products not found")
        order = Order()
        db.session.add(order)
        for product_id, quantity in normalized:
            product = products_by_id[product_id]
            changed = db.session.execute(
                update(Product)
                .where(Product.id == product_id, Product.archived.is_(False), Product.qty_in_stock >= quantity)
                .values(qty_in_stock=Product.qty_in_stock - quantity)
            )
            if changed.rowcount != 1:
                raise Conflict(f"insufficient stock for product {product_id}")
            order.items.append(
                OrderItem(product=product, quantity=quantity, unit_price_cents=product.price_cents)
            )
        db.session.commit()
    except (NotFound, Conflict, IntegrityError):
        db.session.rollback()
        raise
    db.session.refresh(order)
    # Load relationships before serialization, avoiding implicit lazy-load surprises.
    order = db.session.execute(
        db.select(Order).where(Order.id == order.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    ).scalar_one()
    return jsonify(order_data(order)), 201


@orders.get("")
def list_orders():
    stmt = db.select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product)
    ).order_by(Order.id.desc())
    rows = db.session.execute(stmt).scalars().all()
    return jsonify(items=[order_data(order) for order in rows], total=len(rows))


@orders.get("/<int:oid>")
def get_order(oid):
    stmt = db.select(Order).where(Order.id == oid).options(
        selectinload(Order.items).selectinload(OrderItem.product)
    )
    order = db.session.execute(stmt).scalar_one_or_none()
    if order is None:
        raise NotFound("order not found")
    return jsonify(order_data(order))


@health.get("/healthz")
def liveness():
    return jsonify(status="ok"), 200


@health.get("/ready")
def readiness():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok", checks={"db": "ok"}), 200
    except Exception:
        db.session.rollback()
        return jsonify(status="degraded", checks={"db": "err"}), 503
