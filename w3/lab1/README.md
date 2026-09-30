# Resources

| Resource | Ghi chú |
|---|---|
| users | Tài khoản người dùng |
| profile | Hồ sơ, 1-1 với user |
| posts | Bài viết, N-1 với user |
| comments | Bình luận, N-1 post |
| tags | Thẻ, quan hệ N-N với posts |
| follows | Mô hình hóa thành sub-collection following/followers |

# Phân loại

| Loại | Đường dẫn |
|---|---|
| Collection | `/users`, `/posts`, `/tags` |
| Item | `/users/{user_id}`, `/posts/{post_id}`, `/tags/{slug}`, `/comments/{comment_id}` |
| Singleton sub-resource | `/users/{user_id}/profile` |
| Sub-collection | `/posts/{post_id}/comments`, `/posts/{post_id}/tags`, `/users/{user_id}/posts`, `/users/{user_id}/followers`, `/users/{user_id}/following` |
| Item của sub-collection | `/users/{user_id}/following/{target_id}` |

# Sơ đồ cây endpoint

```
/api/v1
├── /users
│   ├── GET, POST
│   └── /{user_id}
│       ├── GET, PATCH, DELETE
│       ├── /profile                GET, PUT
│       ├── /posts                  GET
│       ├── /followers              GET
│       └── /following              GET
│           └── /{target_id}        PUT (follow), DELETE (unfollow)
├── /posts
│   ├── GET, POST
│   └── /{post_id}
│       ├── GET, PUT, PATCH, DELETE
│       ├── /comments               GET, POST
│       └── /tags                   GET
│           └── /{slug}             PUT (attach), DELETE (detach)
├── /comments
│   └── /{comment_id}               GET, PATCH, DELETE
└── /tags
    ├── GET
    └── /{slug}
        ├── GET
        └── /posts                  GET
```

## Version segment

Chỉ tăng major khi có breaking change; thay đổi/thêm field, endpoint giữ nguyên v1.

## Triển khai

app.py