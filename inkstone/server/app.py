from flask import Flask, send_from_directory, send_file, request, abort
from flask_cors import CORS
from config import Config
import os
from utils.logger import setup_logger, log_request

# Allowed static file extensions (prevent serving .py, .sh, etc.)
_STATIC_ALLOWED = {'.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.map', '.json'}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # 配置日志
    setup_logger(app)

    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    CORS(app, supports_credentials=True, origins=[o.strip() for o in cors_origins])

    from routes import register_blueprints
    register_blueprints(app)

    # 请求后钩子：记录日志 + 安全头
    @app.after_request
    def after_request_log(response):
        try:
            log_request(app, request, response)
        except Exception:
            pass
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    @app.route('/api/health')
    def health():
        return {'code': 0, 'data': 'ok', 'msg': 'success'}

    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        # Only allow image files from uploads
        ext = os.path.splitext(filename)[1].lower()
        if ext not in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
            abort(404)
        resp = send_from_directory(upload_dir, filename)
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        return resp

    # Vue History 模式：所有非 API / 非 uploads 的路径返回 index.html
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'client', 'dist')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_vue(path):
        # 如果是 API 或 uploads 路径，不处理（由上面的路由处理）
        if path.startswith('api/') or path.startswith('uploads/'):
            return {'code': 404, 'msg': '接口不存在'}, 404
        # 如果是静态文件（js/css/图片等），返回文件
        file_path = os.path.join(static_dir, path)
        if path and os.path.isfile(file_path):
            ext = os.path.splitext(path)[1].lower()
            if ext not in _STATIC_ALLOWED:
                abort(404)
            return send_file(file_path)
        # 否则返回 index.html（Vue 路由处理）
        index_path = os.path.join(static_dir, 'index.html')
        if os.path.isfile(index_path):
            return send_file(index_path)
        return {'code': 404, 'msg': '前端未构建，请先运行 npm run build'}, 404

    return app


if __name__ == '__main__':
    app = create_app()
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, port=5000)
