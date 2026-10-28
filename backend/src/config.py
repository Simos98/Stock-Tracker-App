import os
from datetime import timedelta


def load_config(overrides=None):
    """Build the Flask config from environment variables, then apply overrides (used by tests)."""
    debug = os.environ.get("FLASK_DEBUG") == "1"
    config = {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY"),
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(hours=1),
        "JWT_REFRESH_TOKEN_EXPIRES": timedelta(days=30),
        # Relative SQLite paths resolve inside backend/instance/
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL") or "sqlite:///finance_companion.db",
        "ALPHAVANTAGE_API_KEY": os.environ.get("ALPHAVANTAGE_API_KEY"),
        "CORS_ORIGINS": (os.environ.get("CORS_ORIGINS") or "http://localhost:5173").split(","),
    }
    config.update(overrides or {})

    for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
        if not config[name]:
            if not debug:
                raise RuntimeError(f"{name} must be set (see backend/.env.example)")
            config[name] = f"dev-only-{name.lower()}-do-not-use-in-production"
    return config
