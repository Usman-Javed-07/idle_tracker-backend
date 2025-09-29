from backend.db import get_connection

def init_tables():
    # safe to call on every start
    conn = get_connection(); cur = conn.cursor()
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
    cur.close(); conn.close()

# --- Users
def insert_user(username, name, department, email, password_hash,
                role="user", shift_start_time="09:00:00", shift_duration_seconds=32400):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, name, department, email, password_hash, role,
                           shift_start_time, shift_duration_seconds)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (username, name, department, email, password_hash, role, shift_start_time, shift_duration_seconds))
    uid = cur.lastrowid
    cur.close(); conn.close()
    return uid

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

def list_users():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT id, username, name, department, email, status, shift_start_time, shift_duration_seconds FROM users ORDER BY name")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def update_user_status(user_id, status):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE users SET status=%s, last_status_change=NOW() WHERE id=%s", (status, user_id))
    cur.close(); conn.close()

# --- Events
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

def fetch_user_inactive_history(user_id, limit=200):
    conn = get_connection(); cur = conn.cursor()
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
