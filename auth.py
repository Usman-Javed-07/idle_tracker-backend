import bcrypt
from datetime import datetime, timedelta

from backend.models import insert_user, get_user_by_username_or_email

# ---------- password helpers ----------


def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())


def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed)

# ---------- shift helpers ----------


def _as_dt(hms: str) -> datetime:
    t = datetime.strptime(hms, "%H:%M:%S").time()
    return datetime(2000, 1, 1, t.hour, t.minute, t.second)


def _duration_seconds(shift_start_time: str, shift_end_time: str) -> int:
    """Seconds between start and end on a 24h clock. If end <= start, roll to next day."""
    start_dt = _as_dt(shift_start_time)
    end_dt = _as_dt(shift_end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return int((end_dt - start_dt).total_seconds())

# ---------- admin create/login ----------


def admin_create_user(
    username: str,
    name: str,
    department: str,
    email: str,
    password: str,
    *,
    shift_start_time: str = "09:00:00",
    shift_end_time: str = "18:00:00",
):
    """
    Create a user with explicit shift start & end.
    Computes shift_duration_seconds from start/end.
    """
    if get_user_by_username_or_email(username) or get_user_by_username_or_email(email):
        raise ValueError("Username or email already exists.")

    pwd_hash = hash_password(password)
    duration = _duration_seconds(shift_start_time, shift_end_time)

    # NOTE: insert_user must accept shift_end_time and shift_duration_seconds.
    return insert_user(
        username,
        name,
        department,
        email,
        pwd_hash,
        role="user",
        shift_start_time=shift_start_time,
        shift_end_time=shift_end_time,
        shift_duration_seconds=duration,
    )


def login(login_text: str, password: str):
    user = get_user_by_username_or_email(login_text)
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None
