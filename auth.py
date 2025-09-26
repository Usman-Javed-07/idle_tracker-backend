import bcrypt
from backend.models import insert_user, get_user_by_username_or_email

def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())

def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed)

def signup(username: str, email: str, password: str, role: str = "user"):
    if get_user_by_username_or_email(username) or get_user_by_username_or_email(email):
        raise ValueError("Username or email already exists.")
    pwd_hash = hash_password(password)
    return insert_user(username, email, pwd_hash, role)

def login(login_text: str, password: str):
    user = get_user_by_username_or_email(login_text)
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None
