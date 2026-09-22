# app.py 
from flask import Flask, jsonify, make_response, request
app = Flask(__name__)
BOOKS = []
_next_id = 1
# ─── GET /books/<id> ─── cache 60s
@app.get("/books/<int:bid>")
def fetch(bid): 
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==bid), None) #tìm quyển có id tương ứng
    if i is None: return jsonify(error="not found"), 404 #nếu không tìm thấy
    resp = make_response(jsonify(BOOKS[i]), 200) #tạo response với dữ liệu cuốn sách và status code 200
    resp.headers["Cache-Control"]="max-age=60"; return resp #thêm header Cache-Control vào response, cho phép cache trong 60 giây
# ─── PUT ─── thay toàn bộ, title+author bắt buộc
@app.put("/books/<int:bid>")
def put(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==bid), None) #tìm quyển có id tương ứng
    if i is None: return jsonify(error="not found"), 404 #nếu không tìm thấy
    p = request.get_json(silent=True) or {} #lấy dữ liệu JSON từ request, nếu không có thì trả về dict rỗng
    t,a = p.get("title"), p.get("author") #lấy title + author từ dữ liệu JSON
    if not t or not a: return jsonify(error="need title+author"), 422 #nếu title hoặc author rỗng thì trả về lỗi 422
    BOOKS[i]={"id":bid,"title":t.strip(),"author":a.strip(), #tạo một dict book với id, title và author, loại bỏ khoảng trắng đầu và cuối
    "isbn":p.get("isbn"),"price":p.get("price")} #thêm isbn và price nếu có
    return jsonify(BOOKS[i]), 200
# ─── PATCH ─── chỉ cập nhật field có trong body
@app.patch("/books/<int:bid>")
def patch(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==bid), None) #tìm quyển có id tương ứng
    if i is None: return jsonify(error="not found"), 404 #nếu không tìm thấy
    p = request.get_json(silent=True) or {} #lấy dữ liệu JSON từ request, nếu không có thì trả về dict rỗng
    if p.get("price", 0) < 0:
        return jsonify(error="price must be positive"), 422 #nếu price âm thì trả về lỗi 422
    for k in"title author isbn price".split():
        if k in p: BOOKS[i][k] = p[k] #nếu key có trong dữ liệu JSON thì cập nhật giá trị của key đó trong dict book
    return jsonify(BOOKS[i]), 200
# ─── DELETE ─── idempotent, trả 204
@app.delete("/books/<int:bid>")
def delete(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==bid), None) #tìm quyển có id tương ứng
    if i is None: return jsonify(error="not found"), 404 #nếu không tìm thấy
    BOOKS.pop(i) #xóa quyển sách khỏi danh sách BOOKS
    return jsonify(), 204