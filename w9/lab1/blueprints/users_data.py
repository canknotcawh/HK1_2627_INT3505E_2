"""Nguồn dữ liệu duy nhất (single source of truth) dùng chung cho v1 và v2."""

from itertools import count
from threading import Lock

USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}

_next_id = count(3)
_lock = Lock()


def get_user(uid):
    """Trả về bản ghi gốc (first_name/last_name) hoặc None."""
    return USERS.get(uid)


def find_by_email(email):
    """Trả về id của user có email trùng (không phân biệt hoa thường)."""
    target = email.strip().lower()
    for uid, user in USERS.items():
        if user["email"].lower() == target:
            return uid
    return None


def create_user(first_name, last_name, email):
    """Thêm user mới và trả về id vừa cấp."""
    with _lock:
        uid = next(_next_id)
        USERS[uid] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }
    return uid
