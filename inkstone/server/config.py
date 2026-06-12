import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'inkstone-secret-key-2026')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '123456')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'inkstone')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MIMO_API_KEY = os.environ.get('MIMO_API_KEY', 'tp-c6o130njwoqih2djnj3yufm9rmbpljgqxygsc5v9o9pze2ho')
    MIMO_BASE_URL = os.environ.get('MIMO_BASE_URL', 'https://token-plan-cn.xiaomimimo.com/anthropic')
    MIMO_MODEL = os.environ.get('MIMO_MODEL', 'mimo-v2.5')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
