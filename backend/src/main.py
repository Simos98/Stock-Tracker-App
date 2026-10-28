"""Entry point: `python -m src.main` from the backend/ directory."""

import os

from dotenv import load_dotenv

load_dotenv()

from src import create_app  # noqa: E402  (load .env before reading config)

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
