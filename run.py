import logging

from dotenv import load_dotenv

# Load .env before importing the app, since Config reads environment variables at import time.
load_dotenv()

from app import create_app  # noqa: E402
from app.database.db import init_db  # noqa: E402
from app.database.seed import load_owid_csv  # noqa: E402

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        init_db()
        load_owid_csv()
    logging.getLogger("app").info("Server starting", extra={"url": "http://127.0.0.1:5000"})
    app.run(debug=app.config["DEBUG"])
