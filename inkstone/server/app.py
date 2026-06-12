from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    from routes import register_blueprints
    register_blueprints(app)

    @app.route('/api/health')
    def health():
        return {'code': 0, 'data': 'ok', 'msg': 'success'}

    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(upload_dir, filename)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
