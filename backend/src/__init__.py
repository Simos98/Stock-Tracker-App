import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from src.cli import register_commands
from src.config import load_config
from src.extensions import db, jwt
from src.routes.auth import auth_bp
from src.routes.preferences import preferences_bp
from src.routes.reports import reports_bp
from src.routes.saved_data import saved_data_bp
from src.routes.stock import stock_bp
from src.routes.user import user_bp
from src.routes.watchlist import watchlist_bp
from src.services.alpha_vantage import AlphaVantageError, RateLimitError


def create_app(config_overrides=None):
    app = Flask(__name__, static_folder="static")
    app.config.update(load_config(config_overrides))

    CORS(app, origins=app.config["CORS_ORIGINS"])
    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(user_bp, url_prefix="/api/v1/users")
    app.register_blueprint(stock_bp, url_prefix="/api/v1/stocks")
    app.register_blueprint(watchlist_bp, url_prefix="/api/v1/watchlist")
    app.register_blueprint(preferences_bp, url_prefix="/api/v1/preferences")
    app.register_blueprint(reports_bp, url_prefix="/api/v1/reports")
    app.register_blueprint(saved_data_bp, url_prefix="/api/v1/saved-data")

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        # Keep API errors in the same {"message": ...} shape as the routes
        return jsonify(message=error.description), error.code

    @app.errorhandler(RateLimitError)
    def handle_rate_limit(error):
        app.logger.warning("Alpha Vantage rate limit: %s", error)
        return jsonify(message="Market data rate limit reached. Please try again in a minute."), 503

    @app.errorhandler(AlphaVantageError)
    def handle_market_data_error(error):
        app.logger.error("Alpha Vantage error: %s", error)
        return jsonify(message="Market data is temporarily unavailable."), 502

    register_commands(app)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        # Unknown API paths must 404 rather than fall through to the SPA
        if path.startswith("api/"):
            return jsonify(message="Resource not found"), 404

        static_dir = app.static_folder
        if path and os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        if os.path.exists(os.path.join(static_dir, "index.html")):
            # Let React Router handle client-side routes
            return send_from_directory(static_dir, "index.html")
        return jsonify(message="Frontend not built. Run `npm run build` in frontend/."), 404

    with app.app_context():
        db.create_all()

    return app
