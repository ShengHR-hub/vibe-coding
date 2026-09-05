import os
from dotenv import load_dotenv

# 加载 .env 文件（开发环境）
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('SECRET_KEY 环境变量未设置，请在 .env 或系统环境变量中配置')

    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'inkstone')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    # AI 调用配额（W1a）：每用户每分钟次数 / 每日总次数
    AI_RATE_PER_MIN = int(os.environ.get('AI_RATE_PER_MIN', 20))
    AI_DAILY_LIMIT = int(os.environ.get('AI_DAILY_LIMIT', 300))

    # OpenAI 兼容主供商（阿里云百炼/火山方舟/智谱/DeepSeek/硅基流动…）
    AI_BASE_URL = os.environ.get('AI_BASE_URL', '')
    AI_API_KEY = os.environ.get('AI_API_KEY', '')
    AI_MODEL = os.environ.get('AI_MODEL', '')
    # 兜底供应商（主供商失败自动回退）
    AI_FALLBACK_ENABLED = os.environ.get('AI_FALLBACK_ENABLED', '0')
    AI_FALLBACK_BASE_URL = os.environ.get('AI_FALLBACK_BASE_URL', '')
    AI_FALLBACK_API_KEY = os.environ.get('AI_FALLBACK_API_KEY', '')
    AI_FALLBACK_MODEL = os.environ.get('AI_FALLBACK_MODEL', '')
    # 智谱 GLM-4.7 系列 thinking：默认对 bigmodel.cn 自动 enabled，可用 disabled 关闭
    AI_THINKING = os.environ.get('AI_THINKING', '')

    if not (AI_BASE_URL and AI_API_KEY and AI_MODEL):
        raise RuntimeError('需要设置 AI_BASE_URL / AI_API_KEY / AI_MODEL（OpenAI 兼容主供商）')
