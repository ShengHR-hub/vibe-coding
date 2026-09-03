import logging
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
from config import Config

logger = logging.getLogger(__name__)

# 连接池：延迟初始化，避免 import 时 MySQL 不可用导致崩溃
_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = PooledDB(
            creator=pymysql,
            mincached=2,
            maxcached=20,
            maxconnections=50,
            blocking=True,
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            cursorclass=DictCursor,
            autocommit=False,
            charset='utf8mb4',
        )
    return _pool


def get_conn():
    return _get_pool().connection()


def query(sql, params=None, one=False):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if one:
                return cur.fetchone()
            return cur.fetchall()
    except Exception as e:
        logger.error(f'Query failed: {e} | SQL: {sql}')
        raise
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        conn.rollback()
        logger.error(f'Execute failed: {e} | SQL: {sql}')
        raise
    finally:
        conn.close()


def execute_many(operations):
    """Execute multiple SQL operations in a single transaction.

    Args:
        operations: list of (sql, params) tuples
    Returns:
        list of lastrowid for each operation
    """
    conn = get_conn()
    try:
        results = []
        with conn.cursor() as cur:
            for sql, params in operations:
                cur.execute(sql, params)
                results.append(cur.lastrowid)
        conn.commit()
        return results
    except Exception as e:
        conn.rollback()
        logger.error(f'Transaction failed: {e}')
        raise
    finally:
        conn.close()
