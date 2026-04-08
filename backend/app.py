#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from backend.config import SECRET_KEY, DEBUG, CORS_ORIGINS
from backend.database import init_db

def create_app():
    """Create and configure Flask application"""
    import os
    from flask import send_from_directory, send_file

    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

    app = Flask(__name__, static_folder=None)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = DEBUG

    # CORS только для разработки без pywebview
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database and create tables
    init_db()

    # Register blueprints
    from backend.routes import profiles, years, months, update
    app.register_blueprint(profiles.bp)
    app.register_blueprint(years.bp)
    app.register_blueprint(months.bp)
    app.register_blueprint(update.bp)

    def _no_cache(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Serve frontend
    @app.route('/')
    def index():
        return _no_cache(send_file(os.path.join(frontend_dir, 'index.html')))

    @app.route('/<path:path>')
    def static_files(path):
        return _no_cache(send_from_directory(frontend_dir, path))

    return app

if __name__ == '__main__':
    from backend.config import HOST, PORT
    app = create_app()
    print("\n✓ База данных инициализирована")
    print(f"✓ Сервер запущен на http://{HOST}:{PORT}\n")
    app.run(host=HOST, port=PORT, debug=DEBUG)
