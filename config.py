import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "idle_tracker_db"),
}

# One admin
ADMIN_BOOTSTRAP = {
    "username": os.getenv("ADMIN_USERNAME", "admin"),
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "password": os.getenv("ADMIN_PASSWORD", "admin123"),
    "name": os.getenv("ADMIN_NAME", "System Admin"),
    "department": os.getenv("ADMIN_DEPT", "IT"),
    "shift_start_time": os.getenv("ADMIN_SHIFT", "09:00:00"),
}

# Email – fill these with your SMTP/app-password
SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("SMTP_USER", "your_email@gmail.com"),
    "password": os.getenv("SMTP_PASS", "your_app_password"),
    "from_addr": os.getenv("SMTP_FROM", "your_email@gmail.com"),
    "use_tls": True,
}


# Where media files are written on disk
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(os.getcwd(), "media"))
MEDIA_SCREENSHOTS_DIR = os.path.join(MEDIA_ROOT, "screenshots")
MEDIA_RECORDINGS_DIR = os.path.join(MEDIA_ROOT, "recordings")

# Public URL base for the Flask static server below
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "http://127.0.0.1:5000/media")
