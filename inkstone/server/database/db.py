import pymysql
from pymysql.cursors import DictCursor
from config import Config


def get_conn():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        port=Config.MYSQL_PORT,
        cursorclass=DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )


def query(sql, params=None, one=False):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if one:
                return cur.fetchone()
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
