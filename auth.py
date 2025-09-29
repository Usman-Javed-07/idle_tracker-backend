import bcrypt
from backend.models import insert_user, get_user_by_username_or_email

def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())

def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed)

def admin_create_user(username, name, department, email, password, shift_start_time="09:00:00"):
    if get_user_by_username_or_email(username) or get_user_by_username_or_email(email):
        raise ValueError("Username or email already exists.")
    pwd_hash = hash_password(password)
    return insert_user(username, name, department, email, pwd_hash, role="user",
                       shift_start_time=shift_start_time, shift_duration_seconds=32400)

def login(login_text: str, password: str):
    user = get_user_by_username_or_email(login_text)
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None
