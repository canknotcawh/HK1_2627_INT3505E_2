from itertools import count
from threading import Lock

USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}

_next_id = count(3)
_lock = Lock()


def get_user(uid):
    return USERS.get(uid)


def find_by_email(email):
    target = email.strip().lower()
    for uid, user in USERS.items():
        if user["email"].lower() == target:
            return uid
    return None


def create_user(first_name, last_name, email):
    with _lock:
        uid = next(_next_id)
        USERS[uid] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }
    return uid
