# Security Audit

## Scope

Review các endpoint:

- `POST /auth/login`
- `POST /auth/refresh`
- `GET /posts/{id}`

Mục tiêu là xác định các vị trí có thể làm lộ thông tin xác thực, dữ liệu cá nhân hoặc nội dung bài đăng.

## 1. Password bị ghi vào log

**Nguy cơ:** Request body của `/auth/login` có thể chứa mật khẩu người dùng. Ghi toàn bộ body vào application log, reverse-proxy log hoặc hệ thống giám sát có thể làm lộ thông tin xác thực.

**Giảm thiểu:**
- Không log password hoặc toàn bộ request body của endpoint đăng nhập.
- Hạn chế quyền truy cập log và đặt thời hạn lưu trữ phù hợp.
- Dùng password hashing chuyên dụng như Argon2id hoặc bcrypt khi lưu mật khẩu.

## 2. User enumeration qua lỗi đăng nhập

**Nguy cơ:** Trả thông báo khác nhau như "username không tồn tại" và "password sai" giúp kẻ tấn công xác định tài khoản hợp lệ.

**Giảm thiểu:**
- Trả cùng thông báo chung: `Invalid username or password`.
- Tránh chênh lệch thời gian xử lý quá rõ rệt giữa các trường hợp.
- Giới hạn số lần đăng nhập và theo dõi hành vi bất thường.

## 3. Access token hoặc refresh token bị lộ

**Nguy cơ:** Token xuất hiện trong log, URL, analytics, crash report hoặc bị đánh cắp từ nơi lưu trữ phía client. Ai có token còn hiệu lực có thể sử dụng quyền của người dùng.

**Giảm thiểu:**
- Không truyền token trong URL hoặc ghi token nguyên bản vào log.
- Dùng HTTPS.
- Lưu token an toàn; cân nhắc cookie `HttpOnly`, `Secure`, `SameSite` tùy kiến trúc client.
- Access token nên có thời hạn ngắn; refresh token cần rotation và cơ chế thu hồi.
- Nếu dùng cookie tự động gửi theo request, đánh giá và phòng chống CSRF.

## 4. Thiếu kiểm tra quyền truy cập bài đăng (IDOR/BOLA)

**Nguy cơ:** Người dùng thay `{id}` trong `/posts/{id}` để đọc bài đăng của người khác, kể cả bài chỉ dành cho follower hoặc bài riêng tư.

**Giảm thiểu:**
- Kiểm tra quyền ở tầng server cho từng bài đăng.
- Không coi việc biết ID hoặc dùng ID khó đoán là cơ chế phân quyền.
- Kiểm tra quyền sở hữu, trạng thái visibility và quan hệ follower trước khi trả dữ liệu.
- Trả `404` thống nhất khi bài không tồn tại hoặc người gọi không được phép biết đến nó, nếu chính sách bảo mật yêu cầu tránh lộ sự tồn tại.

## 5. Rò rỉ dữ liệu qua response bài đăng

**Nguy cơ:** API trả thừa trường nội bộ như email, số điện thoại, IP, moderation notes, access flags hoặc dữ liệu chưa được phép công khai.

**Giảm thiểu:**
- Dùng response DTO/serializer theo allowlist.
- Chỉ trả các trường được định nghĩa trong schema.
- Kiểm thử response với tài khoản và quyền khác nhau.
- Không serialize trực tiếp toàn bộ database entity.

## 6. Brute-force và credential stuffing

**Nguy cơ:** Kẻ tấn công thử nhiều mật khẩu hoặc tái sử dụng thông tin đăng nhập bị rò rỉ qua `/auth/login`; endpoint refresh cũng có thể bị lạm dụng.

**Giảm thiểu:**
- Rate limit theo IP và tài khoản với ngưỡng hợp lý.
- Theo dõi đăng nhập thất bại và hành vi bất thường.
- Cân nhắc CAPTCHA hoặc bước xác minh bổ sung khi có dấu hiệu lạm dụng.
- Trả `429 Too Many Requests` khi vượt giới hạn.

## 7. Refresh-token replay

**Nguy cơ:** Nếu refresh token bị đánh cắp và có thể dùng nhiều lần, kẻ tấn công có thể tiếp tục tạo access token mới.

**Giảm thiểu:**
- Rotation mỗi lần refresh thành công.
- Vô hiệu hóa refresh token cũ.
- Phát hiện token đã bị dùng lại và thu hồi phiên/token family theo chính sách.
- Không ghi refresh token nguyên bản vào log.

## 8. Rò rỉ thông tin nội bộ qua lỗi server

**Nguy cơ:** Stack trace, câu SQL, đường dẫn file, tên bảng hoặc chi tiết hạ tầng xuất hiện trong response `500`.

**Giảm thiểu:**
- Trả thông báo lỗi chung và mã lỗi ổn định.
- Ghi chi tiết kỹ thuật vào log nội bộ có kiểm soát truy cập.
- Không gửi stack trace hoặc secret cho client.

## 9. Cache nhầm dữ liệu riêng tư

**Nguy cơ:** Response của `/posts/{id}` chứa bài riêng tư nhưng bị cache dùng chung, dẫn đến người dùng khác nhận được dữ liệu đó.

**Giảm thiểu:**
- Cấu hình cache phù hợp với dữ liệu cá nhân và phân quyền.
- Với nội dung nhạy cảm, cân nhắc `Cache-Control: private, no-store`.
- Đảm bảo cache key không làm lẫn response giữa các người dùng.
- Kiểm thử cả đường đi qua CDN và reverse proxy.

## 10. Scope và cấu hình CORS không an toàn

**Nguy cơ:** API chấp nhận scope quá rộng hoặc cấu hình CORS cho phép origin không đáng tin cậy, làm tăng khả năng truy cập trái phép trong một số mô hình client.

**Giảm thiểu:**
- Chỉ cấp scope tối thiểu cần thiết; `GET /posts/{id}` yêu cầu `posts:read`.
- Kiểm tra chữ ký, issuer, audience và expiration của JWT.
- Chỉ cho phép các origin cần thiết; không kết hợp credentialed requests với wildcard origin.
- CORS không thay thế xác thực hoặc kiểm tra quyền phía server.

