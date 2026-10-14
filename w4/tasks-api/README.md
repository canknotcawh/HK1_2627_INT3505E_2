# Tasks API

Bài tập OpenAPI 3.0.3: API quản lý task nội bộ với năm operation: `GET /tasks`, `POST /tasks`, `GET /tasks/{taskId}`, `PATCH /tasks/{taskId}`, và `DELETE /tasks/{taskId}`.

## Chạy local

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- Swagger UI: http://localhost:5000/docs
- OpenAPI JSON: http://localhost:5000/openapi.json
- API base URL: http://localhost:5000/v1

API demo yêu cầu header `Authorization: Bearer <token>` cho các endpoint task. Đây là kiểm tra sự hiện diện của bearer token để minh họa contract; chưa xác minh JWT thật. Dữ liệu lưu trong bộ nhớ và mất khi tiến trình khởi động lại.

## Dùng thử

Swagger UI có thể gửi request sau khi điền bất kỳ giá trị bearer token nào vào nút **Authorize**.

```bash
curl -X POST http://localhost:5000/v1/tasks \
  -H "Authorization: Bearer demo" -H "Content-Type: application/json" \
  -d '{"title":"Hoàn thành bài API","priority":"high","dueDate":"2026-11-15"}'
```

## Hai quyết định thiết kế

1. **PATCH thay vì PUT:** bài tập yêu cầu chỉnh sửa một phần task, nên `PATCH` chỉ gửi các trường cần đổi. Schema từ chối body rỗng và field không được hỗ trợ.
2. **UUID và bearer auth:** UUID làm định danh opaque cho task/assignee; bearer auth mô tả cách truyền JWT thống nhất. Bản demo chỉ kiểm tra header có dạng Bearer, chưa xác thực chữ ký/token.

Các lựa chọn bổ sung: dùng status `todo | in_progress | done`, priority `low | medium | high`; `DELETE` thành công trả `204` không có body; danh sách phân trang bằng `page` và `pageSize`.

## Kiểm tra đặc tả

- Swagger Editor: mở https://editor.swagger.io/ và nạp `openapi.yaml` để kiểm tra cú pháp và OpenAPI 3.0.3.
- Spectral: `npx @stoplight/spectral-cli lint openapi.yaml --ruleset .spectral.yaml`.
- ReDoc: `npx @redocly/cli lint openapi.yaml` và `npx @redocly/cli preview-docs openapi.yaml`.

Screenshot yêu cầu: mở `/docs`, thử **POST /tasks** với body mẫu ở trên, sau đó thử **GET /tasks** và chụp màn hình kết quả `201` cùng task vừa tạo. UI dùng Swagger UI CDN nên cần kết nối Internet.
