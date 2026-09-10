from flask import Flask, jsonify

app = Flask(__name__)
ORDERS = {}  # giả lập DB

# DELETE /orders/<id>
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)
    # 404 — không tìm thấy
    if order is None:
        return {"error": "not found"}, 404
    # 409 — business rule
    if order["status"] in ("shipped", "delivered"):
        return {"error": "cannot delete"}, 409
    ORDERS.pop(order_id, None)
    # 204 — success, no body
    return "", 204

if __name__ == "__main__":
	app.run(host="127.0.0.1", port=5000, debug=True)