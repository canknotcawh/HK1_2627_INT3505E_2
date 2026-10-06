# app.py — bài 1: GET /books, POST /books
from flask import Flask, jsonify, make_response, request
app = Flask(__name__)
BOOKS = []
_next_id = 1
# ─── GET /books —— trả danh sách
@app.get("/books")
def list_books():
	return jsonify({
		"data": BOOKS,
		"total": len(BOOKS)
	}), 200
# ─── POST /books —— tạo mới
@app.post("/books")
def create_book():
	global _next_id #create_book() cần thay đổi biến toàn cục _next_id, nên phải khai báo global
	if not request.is_json: #kiểm tra xem request có phải là JSON hay không, nếu không thì trả về lỗi 415
		return jsonify(error="expected JSON"), 415
	p = request.get_json(silent=True) or {} #lấy dữ liệu JSON từ request, nếu không có thì trả về dict rỗng
	t = (p.get("title") or "").strip() #lấy title + author từ dữ liệu JSON, nếu không có thì trả về chuỗi rỗng, sau đó loại bỏ khoảng trắng đầu và cuối
	a = (p.get("author") or "").strip() 
	if not t or not a: #nếu title hoặc author rỗng thì trả về lỗi 422
		return jsonify(error="title and author required"), 422
	book = {"id": _next_id, "title": t, "author": a} #tạo một dict book với id, title và author
	BOOKS.append(book) #thêm book vào danh sách BOOKS
	_next_id += 1
	resp = make_response(jsonify(book), 201) #tạo response với dữ liệu book và status code 201
	resp.headers["Location"] = f"/books/{book['id']}" #thêm header Location vào response, trỏ đến URL của book vừa tạo
	return resp

if __name__ == "__main__":
	app.run(host="127.0.0.1", port=5000, debug=True)
