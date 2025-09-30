# backend/models.py
import os, uuid, datetime as dt
from backend.db import get_connection
from backend.config import (
    MEDIA_ROOT, MEDIA_SCREENSHOTS_DIR, MEDIA_RECORDINGS_DIR, MEDIA_BASE_URL
)

# -----------------------------
# Helpers
# -----------------------------
def _has_column(table: str, column: str) -> bool:
    """Return True if `table`.`column` exists."""
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
    ok = cur.fetchone() is not None
    cur.close(); conn.close()
    return ok

def _ensure_media_dirs():
    os.makedirs(MEDIA_SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(MEDIA_RECORDINGS_DIR, exist_ok=True)

def _now_stamp():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

# -----------------------------
# Schema / Migrations
# -----------------------------
def init_tables():
    conn = get_connection(); cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(100) NOT NULL UNIQUE,
      name VARCHAR(150) NOT NULL,
      department VARCHAR(150) NOT NULL,
      email VARCHAR(255) NOT NULL UNIQUE,
      password_hash VARBINARY(100) NOT NULL,
      role ENUM('admin','user') NOT NULL DEFAULT 'user',
      shift_start_time TIME NOT NULL DEFAULT '09:00:00',
      shift_duration_seconds INT NOT NULL DEFAULT 32400,
      status ENUM('off','shift_start','active','inactive') NOT NULL DEFAULT 'off',
      last_status_change TIMESTAMP NULL DEFAULT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;""")
    # Add missing shift_end_time (migration)
    if not _has_column("users", "shift_end_time"):
        cur.execute("ALTER TABLE users ADD COLUMN shift_end_time TIME NOT NULL DEFAULT '18:00:00'")

    # ACTIVITY EVENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_events (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      event_type ENUM('shift_start','active','inactive') NOT NULL,
      occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      notified TINYINT(1) NOT NULL DEFAULT 0,
      active_duration_seconds INT NULL,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;""")

    # SCREENSHOTS (URL-based; keep compatible with earlier blob schema)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS screenshots (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      event_id BIGINT NULL,
      taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      mime VARCHAR(64) NOT NULL DEFAULT 'image/png',
      url TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (event_id) REFERENCES activity_events(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""")
    if not _has_column("screenshots", "url"):
        cur.execute("ALTER TABLE screenshots ADD COLUMN url TEXT")

    # RECORDINGS (URL-based; keep compatible with earlier blob schema)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS screen_recordings (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      event_id BIGINT NULL,
      recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      duration_seconds INT NOT NULL,
      mime VARCHAR(64) NOT NULL DEFAULT 'video/mp4',
      url TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (event_id) REFERENCES activity_events(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""")
    if not _has_column("screen_recordings", "url"):
        cur.execute("ALTER TABLE screen_recordings ADD COLUMN url TEXT")

    # OVERTIME
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_overtimes (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      ot_date DATE NOT NULL,
      overtime_seconds INT NOT NULL DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uniq_user_date (user_id, ot_date),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;""")

    cur.close(); conn.close()

# -----------------------------
# Users
# -----------------------------
def insert_user(username, name, department, email, password_hash,
                role="user",
                shift_start_time="09:00:00",
                shift_end_time="18:00:00",
                shift_duration_seconds=32400):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, name, department, email, password_hash, role,
                           shift_start_time, shift_end_time, shift_duration_seconds)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (username, name, department, email, password_hash, role,
          shift_start_time, shift_end_time, shift_duration_seconds))
    uid = cur.lastrowid
    cur.close(); conn.close()
    return uid

def admin_update_user(user_id, **fields):
    if not fields: return
    cols, vals = [], []
    for k, v in fields.items():
        if v is None: continue
        cols.append(f"{k}=%s"); vals.append(v)
    if not cols: return
    q = "UPDATE users SET " + ", ".join(cols) + " WHERE id=%s"
    vals.append(user_id)
    conn = get_connection(); cur = conn.cursor()
    cur.execute(q, tuple(vals)); conn.commit(); cur.close(); conn.close()

def admin_delete_user(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit(); cur.close(); conn.close()

def get_user_by_username_or_email(login):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s OR email=%s LIMIT 1", (login, login))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def list_users(search=None):
    conn = get_connection(); cur = conn.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("""
          SELECT id, username, name, department, email, status,
                 shift_start_time, shift_end_time, shift_duration_seconds
          FROM users
          WHERE username LIKE %s OR name LIKE %s OR department LIKE %s
          ORDER BY name
        """, (like, like, like))
    else:
        cur.execute("""
          SELECT id, username, name, department, email, status,
                 shift_start_time, shift_end_time, shift_duration_seconds
          FROM users ORDER BY name
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def update_user_status(user_id, status):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE users SET status=%s, last_status_change=NOW() WHERE id=%s", (status, user_id))
    cur.close(); conn.close()

# -----------------------------
# Events
# -----------------------------
def record_event(user_id, event_type, active_duration_seconds=None, notified=0):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO activity_events (user_id, event_type, active_duration_seconds, notified)
        VALUES (%s,%s,%s,%s)
    """, (user_id, event_type, active_duration_seconds, notified))
    eid = cur.lastrowid
    cur.close(); conn.close()
    return eid

def fetch_unnotified_inactive_events():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT ae.id, ae.user_id, u.username, u.email, u.name, u.department,
               ae.event_type, ae.occurred_at, ae.active_duration_seconds
        FROM activity_events ae
        JOIN users u ON u.id = ae.user_id
        WHERE ae.event_type='inactive' AND ae.notified=0
        ORDER BY ae.occurred_at DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def mark_event_notified(event_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE activity_events SET notified=1 WHERE id=%s", (event_id,))
    cur.close(); conn.close()

def fetch_user_inactive_history(user_id, start_date=None, end_date=None, limit=300):
    conn = get_connection(); cur = conn.cursor()
    if start_date and end_date:
        cur.execute("""
            SELECT ae.id, u.username, u.email, ae.event_type, ae.occurred_at, ae.notified,
                   ae.active_duration_seconds
            FROM activity_events ae
            JOIN users u ON u.id = ae.user_id
            WHERE ae.user_id=%s AND ae.event_type='inactive'
              AND DATE(ae.occurred_at) BETWEEN %s AND %s
            ORDER BY ae.occurred_at DESC
            LIMIT %s
        """, (user_id, start_date, end_date, limit))
    else:
        cur.execute("""
            SELECT ae.id, u.username, u.email, ae.event_type, ae.occurred_at, ae.notified,
                   ae.active_duration_seconds
            FROM activity_events ae
            JOIN users u ON u.id = ae.user_id
            WHERE ae.user_id=%s AND ae.event_type='inactive'
            ORDER BY ae.occurred_at DESC
            LIMIT %s
        """, (user_id, limit))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# -----------------------------
# Overtime
# -----------------------------
def insert_overtime(user_id, ot_date, seconds):
    """
    Add to a user's overtime for a given date (upsert accumulation).
    """
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
      INSERT INTO user_overtimes (user_id, ot_date, overtime_seconds)
      VALUES (%s,%s,%s)
      ON DUPLICATE KEY UPDATE overtime_seconds=overtime_seconds+VALUES(overtime_seconds)
    """, (user_id, ot_date, seconds))
    conn.commit(); cur.close(); conn.close()

# -----------------------------
# Media (URL-based)
# -----------------------------
def insert_screenshot_url(user_id, image_bytes, event_id=None, mime="image/png"):
    """
    Save PNG to disk and record URL in DB.
    """
    _ensure_media_dirs()
    name = f"{_now_stamp()}_{uuid.uuid4().hex}.png"
    relpath = os.path.join("screenshots", name)
    abspath = os.path.join(MEDIA_ROOT, relpath)
    with open(abspath, "wb") as f:
        f.write(image_bytes)
    url = f"{MEDIA_BASE_URL}/{relpath.replace(os.sep, '/')}"
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO screenshots (user_id, event_id, url, mime)
        VALUES (%s,%s,%s,%s)
    """, (user_id, event_id, url, mime))
    sid = cur.lastrowid
    cur.close(); conn.close()
    return sid, url

def insert_recording_url(user_id, video_bytes, duration_seconds, event_id=None, mime="video/mp4"):
    """
    Save MP4 to disk and record URL in DB.
    """
    _ensure_media_dirs()
    name = f"{_now_stamp()}_{uuid.uuid4().hex}.mp4"
    relpath = os.path.join("recordings", name)
    abspath = os.path.join(MEDIA_ROOT, relpath)
    with open(abspath, "wb") as f:
        f.write(video_bytes)
    url = f"{MEDIA_BASE_URL}/{relpath.replace(os.sep, '/')}"
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO screen_recordings (user_id, event_id, duration_seconds, url, mime)
        VALUES (%s,%s,%s,%s,%s)
    """, (user_id, event_id, duration_seconds, url, mime))
    rid = cur.lastrowid
    cur.close(); conn.close()
    return rid, url

def fetch_screenshots_for_user(user_id, limit=50):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
      SELECT id, user_id, event_id, taken_at, mime, url
      FROM screenshots WHERE user_id=%s ORDER BY taken_at DESC LIMIT %s
    """, (user_id, limit))
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

def fetch_recordings_for_user(user_id, limit=20):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
      SELECT id, user_id, event_id, recorded_at, duration_seconds, mime, url
      FROM screen_recordings WHERE user_id=%s ORDER BY recorded_at DESC LIMIT %s
    """, (user_id, limit))
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows

# -----------------------------
# Admin emails (fan-out)
# -----------------------------
def list_admin_emails():
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT email FROM users WHERE role='admin' AND email IS NOT NULL AND email <> ''")
        rows = cur.fetchall()
        emails = []
        for r in rows:
            if isinstance(r, dict):
                em = r.get("email")
            else:
                em = r[0] if len(r) > 0 else None
            if em:
                emails.append(em)
        return emails
    finally:
        cur.close(); conn.close()
