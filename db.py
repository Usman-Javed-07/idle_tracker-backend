import pymysql
from pymysql.cursors import DictCursor
from backend.config import DB_CONFIG


def get_connection():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        autocommit=True,
        cursorclass=DictCursor,
        charset="utf8mb4",
    )
