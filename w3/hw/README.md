# Checklist review - Nhóm 6
---

API: [Google Gemini API - Models](https://ai.google.dev/gemini-api/docs/models)

| Tiêu chí | Kết quả | Note |
|----------|---------|------|
| **2. Naming nhất quán** | Không đạt | Path, field JSON và model ID chưa theo một quy ước duy nhất |
| **3. Status code đúng nghĩa** | Đạt một phần | Lỗi HTTP map đúng, nhưng nội dung bị chặn an toàn được trả trong body của response thành công |

## Tiêu chí 2: Naming nhất quán
---
Checklist: lowercase, kebab-case cho path, snake_case cho query, số nhiều cho collection.

**Đạt**
- Collection dùng số nhiều, lowercase: `models/*`, `files`
- Query param đơn giản, lowercase: `key`, `alt=sse`
- Có version trong path: `/v1beta/`
- Trang models công bố quy ước đặt tên model: stable / preview / latest / experimental

**Không đạt**

1. **Động từ camelCase nằm trong path** (vi phạm "không động từ trong path" và "lowercase")
```
POST https://generativelanguage.googleapis.com/v1beta/{model=models/*}:generateContent
POST https://generativelanguage.googleapis.com/v1beta/{model=models/*}:streamGenerateContent
```

2. **Tên collection camelCase:** `cachedContents/{cachedContent}`, đáng lẽ là kebab-case (`cached-contents`)

3. **Field JSON trộn camelCase và snake_case.** Phần reference dùng camelCase, ví dụ curl của cùng trang dùng snake_case:

| Reference | Ví dụ curl |
|-----------|------------|
| `systemInstruction` | `system_instruction` |
| `toolConfig` | `tool_config` |
| `generationConfig` | `generationConfig` chứa `response_mime_type`, `response_schema` (trộn trong cùng một request) |

Giá trị enum cũng không thống nhất: `"type": "ARRAY"` ở ví dụ JSON Mode, `"type": "object"` ở ví dụ function calling. Proto JSON chấp nhận cả hai kiểu, nhưng tài liệu không chốt một dạng chuẩn.

4. **Model ID không đồng nhất**

| Vấn đề | Ví dụ |
|--------|-------|
| Vị trí `preview` khác nhau | `gemini-2.5-flash-preview-tts` và `gemini-3.1-flash-tts-preview` |
| Hậu tố ngày lúc có lúc không | `gemini-2.5-flash-native-audio-preview-12-2025` và `gemini-3.1-pro-preview` |
| Xếp loại không khớp với ID | "Gemini Omni Flash" nằm ở mục **Preview** nhưng ID `gemini-omni-1.1-flash` không có `-preview` |
| Tên hiển thị khác ID | "Nano Banana 2" tương ứng `gemini-3.1-flash-image` |
| Định dạng version khác nhau | `gemini-embedding-2-preview` và `gemini-embedding-001` |

Chính trang models ghi rõ quy ước chỉ áp dụng từ 09/2025, model ra trước đó có thể khác.

5. **Cột "Endpoint" chứa model ID**, trong khi endpoint thật là `.../models/{model}:generateContent`

6. **Vị trí version không cố định:** upload dùng `/upload/v1beta/files`, các API khác dùng `/v1beta/...`

## Tiêu chí 3: Status code đúng nghĩa
---
Checklist: mỗi response dùng code phù hợp, không trả 200 kèm lỗi trong body.

**Đạt:** với request thường, API set đúng HTTP status và trả `{"error": {"code", "message"}}`

| HTTP | Code | Nhận xét |
|------|------|----------|
| 401 | `authentication` | Thiếu hoặc sai API key |
| 403 | `permission_denied` | Có xác thực nhưng không đủ quyền (tách đúng với 401) |
| 404 | `not_found`, `model_not_found` | Đúng |
| 409 | `already_exists`, `aborted` | Đúng |
| 429 | `rate_limit_exceeded`, `quota_exceeded`, `too_many_requests` | Tách giới hạn theo phút và theo ngày |
| 402 | `payment_required` | Hết credit, ghi rõ "đừng retry" |
| 500, 501, 503, 504 | `api_error`, `unimplemented`, `service_unavailable`, `deadline_exceeded` | Đúng |

Quy tắc retry khớp với slide: retry 429, 408, 5xx; không retry 400, 402, 403.
