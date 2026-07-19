"""日志配置模块"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(app):
    """配置 Flask 应用的日志系统"""

    # 日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 文件日志（轮转，每个文件最大 10MB，保留 5 个备份）
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'inkstone.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 错误日志单独文件
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # 配置 app logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)

    # 记录启动日志
    app.logger.info('墨池 Inkstone 服务启动')

    return app.logger


def log_request(app, request, response=None, error=None):
    """记录请求日志"""
    user_id = request.session.get('user_id') if hasattr(request, 'session') else None
    user_info = f'user:{user_id}' if user_id else 'anonymous'

    if error:
        app.logger.error(
            f'{request.method} {request.path} | {user_info} | ERROR: {error}'
        )
    else:
        status = response.status_code if response else 'N/A'
        app.logger.info(
            f'{request.method} {request.path} | {user_info} | {status}'
        )


def log_user_action(app, user_id, action, detail=''):
    """记录用户操作日志"""
    app.logger.info(f'USER_ACTION | user:{user_id} | {action} | {detail}')


def log_ai_call(app, user_id, endpoint, success=True, error=None):
    """记录 AI 调用日志"""
    if success:
        app.logger.info(f'AI_CALL | user:{user_id} | {endpoint} | SUCCESS')
    else:
        app.logger.error(f'AI_CALL | user:{user_id} | {endpoint} | ERROR: {error}')
