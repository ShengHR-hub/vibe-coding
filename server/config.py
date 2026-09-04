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

    # AI 供应商（多 Provider，2026-09）：mimo（默认，保留原行为）| openai
    AI_PROVIDER = (os.environ.get('AI_PROVIDER', 'mimo') or 'mimo').strip().lower()
    # OpenAI 兼容主供商（阿里云百炼/火山方舟/智谱/DeepSeek/硅基流动…）
    AI_BASE_URL = os.environ.get('AI_BASE_URL', '')
    AI_API_KEY = os.environ.get('AI_API_KEY', '')
    AI_MODEL = os.environ.get('AI_MODEL', '')
    # 兜底供应商（主供商失败自动回退）
    AI_FALLBACK_ENABLED = os.environ.get('AI_FALLBACK_ENABLED', '0')
    AI_FALLBACK_BASE_URL = os.environ.get('AI_FALLBACK_BASE_URL', '')
    AI_FALLBACK_API_KEY = os.environ.get('AI_FALLBACK_API_KEY', '')
    AI_FALLBACK_MODEL = os.environ.get('AI_FALLBACK_MODEL', '')

    # MiMo（原厂商，Anthropic 风格）
    MIMO_API_KEY = os.environ.get('MIMO_API_KEY', '')
    MIMO_BASE_URL = os.environ.get('MIMO_BASE_URL', 'https://token-plan-cn.xiaomimimo.com/anthropic')
    MIMO_MODEL = os.environ.get('MIMO_MODEL', 'mimo-v2.5')

    if AI_PROVIDER == 'mimo' and not MIMO_API_KEY:
        raise RuntimeError('MIMO_API_KEY 环境变量未设置（或改用 AI_PROVIDER=openai + AI_API_KEY）')
    if AI_PROVIDER == 'openai' and not (AI_BASE_URL and AI_API_KEY and AI_MODEL):
        raise RuntimeError('AI_PROVIDER=openai 需要设置 AI_BASE_URL / AI_API_KEY / AI_MODEL')
