from backend.db import get_connection

def init_tables():
    sql_users = """
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(100) NOT NULL UNIQUE,
      email VARCHAR(255) NOT NULL UNIQUE,
      password_hash VARBINARY(100) NOT NULL,
      role ENUM('admin','user') NOT NULL DEFAULT 'user',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;"""
    sql_events = """
    CREATE TABLE IF NOT EXISTS activity_events (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      event_type ENUM('active','inactive') NOT NULL,
      occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      notified TINYINT(1) NOT NULL DEFAULT 0,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql_users)
    cur.execute(sql_events)
    cur.close()
    conn.close()

def insert_user(username, email, password_hash, role="user"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,%s)",
        (username, email, password_hash, role),
    )
    user_id = cur.lastrowid
    cur.close()
    conn.close()
    return user_id

def get_user_by_username_or_email(login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=%s OR email=%s LIMIT 1",
        (login, login)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def record_event(user_id, event_type):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activity_events (user_id, event_type) VALUES (%s,%s)",
        (user_id, event_type),
    )
    cur.close()
    conn.close()

def fetch_recent_events(limit=50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ae.id, ae.user_id, u.username, u.email, ae.event_type, ae.occurred_at, ae.notified
        FROM activity_events ae
        JOIN users u ON u.id = ae.user_id
        ORDER BY ae.occurred_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def fetch_unnotified_inactive_events():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ae.id, ae.user_id, u.username, u.email, ae.event_type, ae.occurred_at
        FROM activity_events ae
        JOIN users u ON u.id = ae.user_id
        WHERE ae.event_type='inactive' AND ae.notified=0
        ORDER BY ae.occurred_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def mark_event_notified(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE activity_events SET notified=1 WHERE id=%s", (event_id,))
    cur.close()
    conn.close()
