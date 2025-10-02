# bootstrap_admin.py
import sys
from backend.models import init_tables, insert_user, get_user_by_username_or_email
from backend.config import ADMIN_BOOTSTRAP
from backend.auth import hash_password, _duration_seconds
import os

# add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_admin():
    # Check if admin exists by username or email
    existing = get_user_by_username_or_email(ADMIN_BOOTSTRAP["username"]) or \
               get_user_by_username_or_email(ADMIN_BOOTSTRAP["email"])

    if existing:
        print(f"✅ Admin already exists: {existing['username']} (id={existing['id']})")
        return existing["id"]

    # Hash password
    pwd_hash = hash_password(ADMIN_BOOTSTRAP["password"])

    # Compute shift duration
    shift_start = ADMIN_BOOTSTRAP.get("shift_start_time", "09:00:00")
    shift_end = "18:00:00"  # fixed end, or make configurable
    duration = _duration_seconds(shift_start, shift_end)

    # Insert admin user
    uid = insert_user(
        username=ADMIN_BOOTSTRAP["username"],
        name=ADMIN_BOOTSTRAP["name"],
        department=ADMIN_BOOTSTRAP["department"],
        email=ADMIN_BOOTSTRAP["email"],
        password_hash=pwd_hash,
        role="admin",
        shift_start_time=shift_start,
        shift_end_time=shift_end,
        shift_duration_seconds=duration,
    )

    print(f"🎉 Admin created successfully with id={uid}, username={ADMIN_BOOTSTRAP['username']}")
    return uid


if __name__ == "__main__":
    try:
        print("🔄 Initializing tables...")
        init_tables()
        ensure_admin()
    except Exception as e:
        print("❌ Error while bootstrapping admin:", e)
        sys.exit(1)
