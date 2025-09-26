import os

# For simplicity, hardcode; or load from env (os.getenv)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),   # XAMPP default
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),    # XAMPP often empty by default
    "database": os.getenv("DB_NAME", "idle_tracker_db"),
}

# Single admin bootstrap (used once if missing)
ADMIN_BOOTSTRAP = {
    "username": os.getenv("ADMIN_USERNAME", "admin"),
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "password": os.getenv("ADMIN_PASSWORD", "admin123"),
}
